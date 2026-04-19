import flet as ft
import traceback
import os
import datetime
import shutil
import urllib.parse

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#002200" 
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = ft.padding.only(left=15, top=55, right=15, bottom=15)
    page.scroll = ft.ScrollMode.AUTO

    def check_permissions(e=None):
        try:
            page.request_permission(ft.PermissionType.WRITE_EXTERNAL_STORAGE)
            page.request_permission(ft.PermissionType.MANAGE_EXTERNAL_STORAGE)
        except:
            pass
    
    try: page.window.icon = "icon.png"
    except: pass

    # GRAUER KASTEN BEHOBEN: expand=True wurde entfernt!
    ansicht = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=25, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=16))
        try: ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=10))
        except: pass
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # BUTTON-FEHLER BEHOBEN: Wieder der saubere Flet-Standard! Nichts ragt mehr über.
        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            return ft.ElevatedButton(
                text=text,
                on_click=on_click, 
                bgcolor=bgcolor, 
                color=color, 
                expand=expand, 
                height=height, 
                width=width,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=5
                )
            )

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=15, 
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
            
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()
                
            btn_start = sicherer_button("TAG STARTEN", start_klick, "red", "white", height=60, width=250)
            
            # STARTBILDSCHIRM ZENTRIERT!
            ansicht.controls.extend([
                ft.Container(height=40),
                ft.Row([
                    ft.Text("REWE", size=32, weight="bold", color="red"),
                    ft.Text("MONITORING", size=32, weight="bold", color="white")
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=40),
                ft.Row([v_in], alignment=ft.MainAxisAlignment.CENTER), 
                ft.Row([z_in], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=40),
                ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(ft.Row([ft.Text("Meine heutigen Touren", size=22, weight="bold", color="white")], alignment=ft.MainAxisAlignment.START))
            
            if not maerkte:
                ansicht.controls.append(ft.Container(height=20))
                ansicht.controls.append(ft.Row([ft.Text("Noch keine Touren angelegt.", color="grey", size=16)], alignment=ft.MainAxisAlignment.CENTER))
            else:
                for index, markt in enumerate(maerkte):
                    adr = (markt.get("adresse") or "").strip()
                    mnr = (markt.get("marktnummer") or "").strip()
                    anzeige_text = f"{mnr} - {adr}" # Auf eine Zeile angepasst für bessere Ansicht
                    buchstabe = chr(65 + index) if index < 26 else str(index)
                    
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    btn_tour = sicherer_button(f"🚚 Tour {buchstabe}:\n{anzeige_text}", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500", "white", expand=True)
                    
                    # Rote Mülltonne als sauberes Icon!
                    btn_del = ft.IconButton(icon=ft.icons.DELETE, icon_color="white", bgcolor="red", on_click=loesche_t)
                    
                    ansicht.controls.append(ft.Row([btn_tour, btn_del], vertical_alignment=ft.CrossAxisAlignment.CENTER))
                    
            ansicht.controls.append(ft.Divider(color="transparent"))
            btn_neu = sicherer_button("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", "white", height=50, width=200)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        def get_erweiterte_bases():
            try: bases = get_all_rewe_bases()
            except: bases = []
            extra_paths = ["/storage/emulated/0/Download/Rewe_Monitoring", "/storage/emulated/0/Download", "/storage/emulated/0/Documents/Rewe_Monitoring"]
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
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=22, weight="bold", color="white"))
            bereinige_archiv()
            
            email_feld = ft.TextField(value="registration-mibi.ber@tentamus.com", read_only=True, color="white", border=ft.InputBorder.NONE, content_padding=0, text_style=ft.TextStyle(size=14, weight="bold"), text_align=ft.TextAlign.CENTER)
            ansicht.controls.append(
                ft.Container(bgcolor="#330000", padding=10, border_radius=10, content=ft.Column([
                    ft.Text("📧 ZIEL-ADRESSE:", color="orange", weight="bold"), 
                    email_feld, 
                    ft.Text("1. Adresse gedrückt halten & kopieren.\n2. Auf das blaue Teilen-Icon drücken.\n3. PDF über die Büroklammer anhängen.", color="white", size=12)
                ]))
            )
            
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
                        ansicht.controls.append(ft.Text(f"{ordner}", color="yellow", weight="bold", size=14))
                        for pdf in p_list:
                            pdfs_gefunden = True
                            
                            def mail_klick_archiv(e, d=pdf):
                                betreff = urllib.parse.quote(f"REWE Monitoring Bericht: {d}")
                                page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={betreff}")

                            # HIER IST WIEDER DAS BLAUE TEILEN-ICON
                            btn_teilen = ft.IconButton(icon=ft.icons.SHARE, icon_color="white", bgcolor="blue", on_click=mail_klick_archiv)

                            ansicht.controls.append(
                                ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                                    content=ft.Row([
                                        ft.Text(pdf, color="white", size=12, expand=True, selectable=True), 
                                        btn_teilen
                                    ])
                                )
                            )
                        ansicht.controls.append(ft.Divider(color="white24"))
                except PermissionError: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Container(padding=20, content=ft.Text("Keine Berichte im Archiv.", color="grey", size=14)))
            page.update()
            
        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(ft.Row([ft.Text("Postausgang (Heute)", size=22, weight="bold", color="white")], alignment=ft.MainAxisAlignment.START))
            heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
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
                        if f.lower().endswith(".pdf") and (heute_ordner in f or ordner.endswith(heute_ordner)): p_list.append(f)
                    if p_list:
                        pdfs_gefunden = True
                        ansicht.controls.append(ft.Container(bgcolor="#330000", padding=10, border_radius=10, content=ft.Column([ft.Text("Berichte für heute liegen in:", color="red", size=12), ft.Text(f"{ordner}", color="red", size=12, weight="bold", selectable=True)])))
                        
                        for pdf in p_list:
                            pdf_komplett = os.path.join(ordner, pdf) 
                                    
                            def rm_klick(e, pfad=pdf_komplett):
                                if os.path.exists(pfad): os.remove(pfad)
                                zeige_postausgang()
                            
                            def mail_klick_post(e, d=pdf):
                                betreff = urllib.parse.quote(f"REWE Monitoring Bericht: {d}")
                                page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={betreff}")

                            # HIER SIND DIE BLAUEN UND ROTEN ICONS FÜR TEILEN & LÖSCHEN
                            btn_teilen = ft.IconButton(icon=ft.icons.SHARE, icon_color="white", bgcolor="blue", on_click=mail_klick_post)
                            btn_del = ft.IconButton(icon=ft.icons.DELETE, icon_color="white", bgcolor="red", on_click=rm_klick)

                            ansicht.controls.append(
                                ft.Container(bgcolor="#003300", padding=10, border_radius=10, 
                                    content=ft.Row([
                                        ft.Text(pdf, color="white", size=12, expand=True, weight="bold"), 
                                        btn_teilen,
                                        btn_del
                                    ])
                                )
                            )
                except PermissionError: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Container(padding=20, content=ft.Text("Noch keine Berichte für heute erstellt.", color="grey", size=14)))
            page.update()

        page.on_connect = check_permissions
        zeige_startbildschirm()
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")