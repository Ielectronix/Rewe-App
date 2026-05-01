import flet as ft
import traceback
import os
import datetime
import urllib.parse
import shutil

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#001a00"
    page.padding = 15
    page.scroll = "auto"

    ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ft.SafeArea(ansicht))

    share = ft.Share()
    if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
        page.overlay.append(share)

    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=24, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow"))
        try: ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=10))
        except: pass
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # Dunkle, solide Buttons für die Hauptnavigation oben
        def nav_btn(text, on_click):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold"),
                on_click=on_click, bgcolor="#1a1a1a", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), padding=15)
            )

        # DEIN WUNSCH-DESIGN: Dunkler Hintergrund, leuchtender Farbrand und leuchtender Text!
        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold"),
                on_click=on_click, bgcolor="#111111", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=25), 
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                    side=ft.BorderSide(width=2, color=farbe) # <-- Der magische Farbrand!
                )
            )

        def nav_leiste():
            return ft.Row(
                wrap=True, alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    nav_btn("🚚 Touren", lambda e: zeige_dashboard()),
                    nav_btn("📤 Senden", lambda e: zeige_postausgang()),
                    nav_btn("🗄️ Archiv", lambda e: zeige_archiv())
                ]
            )

        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", border_color="white", width=300, text_align=ft.TextAlign.CENTER)
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", border_color="white", width=300, text_align=ft.TextAlign.CENTER)
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()
                
            ansicht.controls.extend([
                ft.Container(height=30),
                ft.Text("REWE Monitoring", color="white", weight="bold", size=28, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                v_in, z_in,
                ft.Container(height=20),
                action_btn("🚀 Neuen Tag starten", start_klick, "#F44336") # Roter Rand
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=20, weight="bold", color="white", text_align=ft.TextAlign.CENTER))
            
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren angelegt.", color="white54"))
            else:
                for index, markt in enumerate(maerkte):
                    adr = (markt.get("adresse") or "").strip()
                    mnr = (markt.get("marktnummer") or "").strip()
                    anzeige_text = f"{mnr} - {adr}" if mnr and adr else (mnr or adr or "Unbenannte Tour")
                    
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    ansicht.controls.append(
                        ft.Container(
                            bgcolor="#002200", padding=15, border_radius=15, width=400,
                            content=ft.Row([
                                ft.Text(f"Tour {chr(65+index)}:\n{anzeige_text}", color="white", weight="bold", width=160),
                                action_btn("✏️", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#2196F3"), # Blauer Rand
                                action_btn("🗑️", loesche_t, "#F44336") # Roter Rand
                            ], wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
                    
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(action_btn("➕ Neue Tour anlegen", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "#2196F3"))
            page.update()

        def get_erweiterte_bases():
            try: bases = get_all_rewe_bases()
            except: bases = []
            extra_paths = ["/storage/emulated/0/Download/Rewe_Monitoring", "/storage/emulated/0/Download", "/storage/emulated/0/Downloads", "/storage/emulated/0/Documents/Rewe_Monitoring"]
            for p in extra_paths:
                if p not in bases: bases.append(p)
            return bases

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="white", text_align=ft.TextAlign.CENTER))
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
                        ansicht.controls.append(ft.Text(f"Berichte in:\n{ordner}", color="red", size=12, text_align=ft.TextAlign.CENTER))
                        for pdf in p_list:
                            pdf_komplett = os.path.join(ordner, pdf) 
                            
                            async def teilen_klick(e, pfad=pdf_komplett):
                                if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
                                    await share.share_files([ft.ShareFile.from_path(pfad)], text="Hier ist der neue REWE-Prüfbericht.")
                                else: print(f"Teilen am PC nicht möglich.")
                                    
                            def rm_klick(e, pfad=pdf_komplett):
                                if os.path.exists(pfad): os.remove(pfad)
                                zeige_postausgang()
                            
                            ansicht.controls.append(
                                ft.Container(
                                    bgcolor="#002200", padding=15, border_radius=15, width=400,
                                    content=ft.Row([
                                        ft.Text(pdf, color="white", size=12, width=160), 
                                        action_btn("📤", teilen_klick, "#2196F3"),
                                        action_btn("🗑️", rm_klick, "#F44336")
                                    ], wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                                )
                            )
                except PermissionError: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Noch keine Berichte für heute erstellt.", color="white54"))
            page.update()

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
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=20, weight="bold", color="white", text_align=ft.TextAlign.CENTER))
            bereinige_archiv()
            email_feld = ft.TextField(value="registration-mibi.ber@tentamus.com", read_only=True, color="white", border=ft.InputBorder.NONE, content_padding=0, text_align=ft.TextAlign.CENTER)
            ansicht.controls.append(ft.Container(bgcolor="#1a1a1a", padding=15, border_radius=15, width=400, content=ft.Column([ft.Text("MANUELLER E-MAIL VERSAND:", color="orange", weight="bold"), email_feld, ft.Text("Betreff: REWE + Marktnummer", color="yellow")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)))
            
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
                        ansicht.controls.append(ft.Text(f"{ordner}", color="yellow", weight="bold"))
                        for pdf in p_list:
                            pdfs_gefunden = True
                            def mail_senden(e, d=pdf):
                                betreff = urllib.parse.quote(f"REWE Monitoring Bericht: {d}")
                                body = urllib.parse.quote("Hallo,\n\nbitte den Bericht im Anhang finden.\n\nViele Grüße")
                                page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={betreff}&body={body}")
                            ansicht.controls.append(ft.Container(bgcolor="#002200", padding=15, border_radius=15, width=400, content=ft.Row([ft.Text(pdf, color="white", size=12, width=180), action_btn("📧 Mail", mail_senden, "#2196F3")], wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)))
                        ansicht.controls.append(ft.Divider(color="white24"))
                except PermissionError: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="white54"))
            page.update()

        zeige_startbildschirm()

    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")
