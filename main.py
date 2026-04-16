import flet as ft
import traceback
import os
import datetime
import shutil
import urllib.parse

def main(page: ft.Page):
    # --- AUTOMATISCHES RECHTE-POPUP FÜR MITARBEITER ---
    ph = page.get_permission_handler()
    ph.request_permission(ft.PermissionType.STORAGE)
    
    # ... hier geht dein normaler Code weiter ...
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.padding = ft.padding.only(left=10, top=55, right=10, bottom=10)
    page.scroll = ft.ScrollMode.AUTO

    def check_permissions(e=None):
        page.request_permission(ft.PermissionType.WRITE_EXTERNAL_STORAGE)
        page.request_permission(ft.PermissionType.MANAGE_EXTERNAL_STORAGE)
    
    try: page.window.icon = "icon.png"
    except: pass

    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    page.add(ansicht)

    # --- TEILEN-MODUL FÜR ANDROID (Versteckt den roten Kasten am PC) ---
    share = ft.Share()

    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=20))
        try: ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=12))
        except: pass
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            align_txt = ft.TextAlign.LEFT if (expand and not height) else ft.TextAlign.CENTER
            # Emoji-Buttons (Teilen & Löschen) bekommen eine größere Schrift
            text_size = 18 if text in ["🗑️", "📤"] else 12 
            txt_obj = ft.Text(text, weight="bold", size=text_size, text_align=align_txt)
            
            inhalt = []
            if expand and not height: 
                inhalt.append(ft.Container(content=txt_obj, expand=True, padding=ft.padding.only(left=5)))
            else: 
                inhalt.append(txt_obj)
                
            align_row = ft.MainAxisAlignment.START if (expand and text and not height) else ft.MainAxisAlignment.CENTER
            return ft.ElevatedButton(
                content=ft.Row(inhalt, alignment=align_row, spacing=0),
                on_click=on_click, bgcolor=bgcolor, color=color, expand=expand, height=height, width=width,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=10, vertical=10))
            )

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=10, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("🚚 Touren", lambda e: zeige_dashboard(), "#004400", "white", expand=True, height=50),
                    sicherer_button("📤 Senden", lambda e: zeige_postausgang(), "#004400", "white", expand=True, height=50),
                    sicherer_button("🗄️ Archiv", lambda e: zeige_archiv(), "#004400", "white", expand=True, height=50)
                ])
            )

        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            stil_label_weiss = ft.TextStyle(color="white")
            stil_hint_weiss = ft.TextStyle(color="white54", size=12)
            v_in = ft.TextField(label="Vorname", hint_text="Dein Vorname", hint_style=stil_hint_weiss, value=v, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            z_in = ft.TextField(label="Nachname", hint_text="Dein Nachname", hint_style=stil_hint_weiss, value=z, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()
            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            header = ft.Text(spans=[ft.TextSpan("REWE ", ft.TextStyle(color="red", weight="bold", size=32)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=32))], text_align=ft.TextAlign.CENTER)
            ansicht.controls.extend([ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(height=40), ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Divider(color="transparent"))
            ansicht.controls.append(ft.Row([ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
            
            if not maerkte:
                ansicht.controls.append(ft.Row([ft.Text("Noch keine Touren angelegt.", color="grey", size=16)], alignment=ft.MainAxisAlignment.CENTER))
            else:
                for index, markt in enumerate(maerkte):
                    adr = (markt.get("adresse") or "").strip()
                    mnr = (markt.get("marktnummer") or "").strip()
                    anzeige_text = f"{mnr} - {adr}" if mnr and adr else (mnr or adr or "Unbenannte Tour")
                    buchstabe = chr(65 + index) if index < 26 else str(index)
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    btn_tour = sicherer_button(f"🚚 Tour {buchstabe}: {anzeige_text}", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500", "white", expand=True, height=None)
                    btn_del = sicherer_button("🗑️", loesche_t, "red", "white", height=50, width=60)
                    ansicht.controls.append(ft.Row([btn_tour, btn_del], vertical_alignment=ft.CrossAxisAlignment.CENTER))
                    
            ansicht.controls.append(ft.Divider(color="white"))
            btn_neu = sicherer_button("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", "white", height=50, width=200)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        def get_erweiterte_bases():
            try: bases = get_all_rewe_bases()
            except: bases = []
            extra_paths = ["/storage/emulated/0/Download/Rewe_Monitoring", "/storage/emulated/0/Download", "/storage/emulated/0/Downloads", "/storage/emulated/0/Documents/Rewe_Monitoring"]
            for p in extra_paths:
                if p not in bases: bases.append(p)
            return bases

        def bereinige_archiv():
            heute = datetime.datetime.now()
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                try:
                    for ordner in os.listdir(base):
                        ordner_pfad = os.path.join(base, ordner)
                        if os.path.isdir(ordner_pfad) and ordner != "temp":
                            try:
                                ordner_datum = datetime.datetime.strptime(ordner, '%Y-%m-%d')
                                if (heute - ordner_datum).days > 7: shutil.rmtree(ordner_pfad)
                            except: pass
                except PermissionError: pass

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=25, weight="bold", color="white"))
            bereinige_archiv()
            email_feld = ft.TextField(value="registration-mibi.ber@tentamus.com", read_only=True, color="white", selection_color="yellow", border=ft.InputBorder.NONE, content_padding=0, text_style=ft.TextStyle(size=14, weight="bold"))
            ansicht.controls.append(ft.Container(bgcolor="#330000", padding=10, border_radius=10, content=ft.Column([ft.Text("MANUELLER E-MAIL VERSAND:", color="orange", weight="bold"), ft.Text("Empfänger:", color="orange", size=14, weight="bold"), email_feld, ft.Text("Betreff: REWE + Marktnummer", color="yellow", size=14, weight="bold", selectable=True), ft.Text("1. E-Mail-Adresse gedrückt halten, um sie zu kopieren.\n2. In Mail-App einfügen.\n3. PDF-Datei über Büroklammer-Symbol anhängen.", color="white", size=12)])))
            
            pdfs_gefunden = False
            such_ordner = []
            for base in get_erweiterte_bases():
                such_ordner.append(base)
                if os.path.exists(base):
                    try:
                        for o in os.listdir(base):
                            p = os.path.join(base, o)
                            if os.path.isdir(p) and o != "temp": such_ordner.append(p)
                    except: pass
            
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    p_list = []
                    for f in os.listdir(ordner):
                        if f.lower().endswith(".pdf") and ("rewe" in f.lower() or ordner.split("/")[-1].startswith("202")): p_list.append(f)
                    if p_list:
                        ansicht.controls.append(ft.Text(f"{ordner}", color="yellow", weight="bold", size=16))
                        for pdf in p_list:
                            pdfs_gefunden = True
                            def mail_senden(e, d=pdf):
                                betreff = urllib.parse.quote(f"REWE Monitoring Bericht: {d}")
                                body = urllib.parse.quote("Hallo,\n\nbitte den Bericht im Anhang finden. (WICHTIG: Die PDF-Datei muss noch manuell angehängt werden!)\n\nViele Grüße")
                                page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={betreff}&body={body}")
                            ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=10, content=ft.Row([ft.Text(pdf, color="white", size=12, expand=True, selectable=True), sicherer_button("📧 Mail", mail_senden, "blue", "white")])))
                        ansicht.controls.append(ft.Divider(color="white24"))
                except PermissionError: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="grey", size=14))
            page.update()
            
        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=25, weight="bold", color="white"))
            heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
            heute_str_de = datetime.datetime.now().strftime('%d.%m.%Y')
            pdfs_gefunden = False
            such_ordner = []
            for base in get_erweiterte_bases():
                such_ordner.append(os.path.join(base, heute_ordner))
                such_ordner.append(base)
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    p_list = []
                    for f in os.listdir(ordner):
                        if f.lower().endswith(".pdf"):
                            if ordner.endswith(heute_ordner): p_list.append(f)
                            elif "rewe" in f.lower() and (heute_str_de in f or heute_ordner in f): p_list.append(f)
                    if p_list:
                        pdfs_gefunden = True
                        ansicht.controls.append(ft.Container(bgcolor="#330000", padding=10, border_radius=10, content=ft.Column([ft.Text("Berichte für heute liegen in:", color="red", size=12), ft.Text(f"{ordner}", color="red", size=12, weight="bold", selectable=True)])))
                        
                        for pdf in p_list:
                            pdf_komplett = os.path.join(ordner, pdf) 
                            
                            # WICHTIG: pfad=pdf_komplett und name=pdf "binden" die Werte fest an DIESEN einen Button.
                            async def teilen_klick(e, pfad=pdf_komplett):
                                if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
                                    await share.share_files([ft.ShareFile.from_path(pfad)], text="Hier ist der neue REWE-Prüfbericht.")
                                else:
                                    print(f"Teilen am PC nicht möglich. PDF-Pfad wäre: {pfad}")
                                    
                            def rm_klick(e, pfad=pdf_komplett):
                                if os.path.exists(pfad):
                                    os.remove(pfad)
                                zeige_postausgang()
                            
                            # Sicherer Emoji-Button (Stürzt garantiert nicht ab!)
                            btn_share = sicherer_button("📤", teilen_klick, "blue", "white", width=50)
                            btn_del = sicherer_button("🗑️", rm_klick, "red", "white", width=50)
                            
                            ansicht.controls.append(
                                ft.Container(
                                    bgcolor="#002200", 
                                    padding=10, 
                                    border_radius=10, 
                                    content=ft.Row([
                                        ft.Text(pdf, color="white", size=10, expand=True), 
                                        btn_share, 
                                        btn_del
                                    ])
                                )
                            )
                except PermissionError: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Noch keine Berichte für heute erstellt.", color="grey", size=14))
            page.update()

        page.on_connect = check_permissions
        zeige_startbildschirm()
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")
