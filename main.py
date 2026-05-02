import flet as ft
import traceback
import os
import datetime
import urllib.parse
import shutil

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#001a00"
    page.padding = 20
    page.scroll = "auto"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ft.SafeArea(ansicht))

    share_obj = ft.Share() if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS] else None

    def zeige_fehler(e):
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text(f"FEHLER: {str(e)}", color="red"))
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def nav_btn(text, on_click):
            return ft.ElevatedButton(
                text, on_click=on_click, bgcolor="#1a1a1a", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10)
            )

        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold"),
                on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=25), 
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                    side=ft.BorderSide(width=2, color=farbe)
                )
            )

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(emoji, size=16),
                on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    padding=0,
                    side=ft.BorderSide(width=2, color=farbe)
                ),
                width=45, height=45
            )

        # FIX: Exakt gedrittelte Reihe, kein Quetschen mehr!
        def nav_leiste():
            return ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Container(content=nav_btn("🚚 Touren", lambda e: zeige_dashboard()), expand=1),
                    ft.Container(content=nav_btn("📤 Senden", lambda e: zeige_postausgang()), expand=1),
                    ft.Container(content=nav_btn("🗄️ Archiv", lambda e: zeige_archiv()), expand=1)
                ]
            )

        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            # FIX: Schriftfarbe explizit auf gelb gezwungen
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", text_style=ft.TextStyle(color="yellow"), label_style=ft.TextStyle(color="white54"), border_color="white", width=300, text_align="center")
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", text_style=ft.TextStyle(color="yellow"), label_style=ft.TextStyle(color="white54"), border_color="white", width=300, text_align="center")
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()
                
            ansicht.controls.extend([
                ft.Container(height=30),
                ft.Text("REWE Monitoring", color="white", weight="bold", size=28),
                ft.Container(height=10),
                v_in, z_in,
                ft.Container(height=10),
                action_btn("🚀 Tag starten", start_klick, "#F44336")
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=20, weight="bold", color="white"))
            
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren angelegt.", color="white54"))
            else:
                for index, markt in enumerate(maerkte):
                    anzeige_text = markt.get("adresse")
                    if not anzeige_text or str(anzeige_text).strip() == "":
                        anzeige_text = markt.get("marktnummer") or "Unbenannte Tour"
                        
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    ansicht.controls.append(
                        ft.Container(
                            bgcolor="#002200", padding=15, border_radius=15, width=380,
                            content=ft.Row([
                                ft.Text(f"{anzeige_text}", color="white", weight="bold", size=12, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                small_btn("✏️", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#2196F3"),
                                small_btn("🗑️", loesche_t, "#F44336")
                            ], alignment="spaceBetween")
                        )
                    )
            ansicht.controls.append(action_btn("➕ Neue Tour anlegen", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "#2196F3"))
            page.update()

        def get_erweiterte_bases():
            try: return get_all_rewe_bases() + ["/storage/emulated/0/Download/Rewe_Monitoring"]
            except: return []

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="white"))
            
            heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
            pdfs_gefunden = False
            such_ordner = []
            for base in get_erweiterte_bases():
                such_ordner.append(os.path.join(base, heute_ordner))
                such_ordner.append(base)
            
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    for f in os.listdir(ordner):
                        if f.lower().endswith(".pdf"):
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            
                            async def teilen_jetzt(e, p=pfad):
                                if share_obj: await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                                else: print("Share geht auf dem PC nicht.")

                            def rm(e, p=pfad):
                                if os.path.exists(p): os.remove(p)
                                zeige_postausgang()

                            ansicht.controls.append(
                                ft.Container(
                                    bgcolor="#002200", padding=15, border_radius=15, width=380,
                                    content=ft.Row([
                                        ft.Text(f[:18], color="white", size=12, expand=True),
                                        action_btn("📤 Senden", teilen_jetzt, "#2196F3"),
                                        small_btn("🗑️", rm, "#F44336")
                                    ])
                                )
                            )
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte zum Senden.", color="white54"))
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
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=20, weight="bold", color="white"))
            bereinige_archiv()
            email_val = "registration-mibi.ber@tentamus.com"
            ansicht.controls.append(ft.Container(bgcolor="#1a1a1a", padding=20, border_radius=15, content=ft.Column([ft.Text("E-MAIL KOPIEREN:", color="#FF9800", weight="bold"), ft.Text(email_val, color="white")], horizontal_alignment="center")))
            
            pdfs_gefunden = False
            such_ordner = []
            for base in get_erweiterte_bases():
                if os.path.exists(base):
                    such_ordner.append(base)
                    try:
                        for o in os.listdir(base):
                            p = os.path.join(base, o)
                            if os.path.isdir(p) and o != "temp": such_ordner.append(p)
                    except: pass
            
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    p_list = [f for f in os.listdir(ordner) if f.lower().endswith(".pdf")]
                    if p_list:
                        ansicht.controls.append(ft.Text(f"{ordner}", color="yellow", weight="bold", size=12))
                        for f in p_list:
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            
                            async def teilen_archiv(e, p=pfad):
                                if share_obj: await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                                else: print("Share geht auf dem PC nicht.")

                            ansicht.controls.append(
                                ft.Container(
                                    bgcolor="#002200", padding=15, border_radius=15, width=380, 
                                    content=ft.Row([
                                        ft.Text(f[:18], color="white", size=12, expand=True), 
                                        action_btn("📤 Senden", teilen_archiv, "#2196F3")
                                    ])
                                )
                            )
                        ansicht.controls.append(ft.Divider(color="white24"))
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="white54"))
            page.update()

        zeige_startbildschirm()

    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main)