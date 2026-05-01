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
    # Zentrierung auf der ganzen Seite aktivieren
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ft.SafeArea(ansicht))

    # --- DER ABSOLUTE SHARE-SCHUTZ ---
    share_module = None
    if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
        try:
            # Wir laden Share NUR auf dem Handy
            share_module = ft.Share()
            page.overlay.append(share_module)
        except:
            pass

    def zeige_fehler(e):
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=24, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow"))
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # Navigation oben (Dunkel)
        def nav_btn(text, on_click):
            return ft.ElevatedButton(
                text, on_click=on_click, bgcolor="#1a1a1a", color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), padding=15)
            )

        # DEIN WUNSCH-DESIGN: Farbrand-Buttons
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
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", border_color="white", width=300, text_align="center")
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", border_color="white", width=300, text_align="center")
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()
            ansicht.controls.extend([
                ft.Text("REWE Monitoring", color="white", weight="bold", size=28),
                v_in, z_in,
                action_btn("🚀 Tag starten", start_klick, "#F44336")
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=20, weight="bold", color="white"))
            
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren.", color="white54"))
            else:
                for index, markt in enumerate(maerkte):
                    mnr = (markt.get("marktnummer") or "Unbenannt")
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    # Karten mit festem Maß (Breite 350) gegen den grauen Bereich
                    ansicht.controls.append(
                        ft.Container(
                            bgcolor="#002200", padding=15, border_radius=15, width=350,
                            content=ft.Row([
                                ft.Text(f"{mnr}", color="white", weight="bold", size=16),
                                ft.Row([
                                    action_btn("✏️", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#2196F3"),
                                    action_btn("🗑️", loesche_t, "#F44336")
                                ], spacing=5)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
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
            ansicht.controls.append(ft.Text("Postausgang", size=20, weight="bold", color="white"))
            pdfs_gefunden = False
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                for f in os.listdir(base):
                    if f.lower().endswith(".pdf"):
                        pdfs_gefunden = True
                        pfad = os.path.join(base, f)
                        async def teilen(e, p=pfad):
                            if share_module: await share_module.share_files([ft.ShareFile.from_path(p)])
                        ansicht.controls.append(
                            ft.Container(bgcolor="#002200", padding=10, border_radius=15, width=350,
                                content=ft.Row([ft.Text(f[:15], color="white", size=12), action_btn("📤", teilen, "#2196F3")], alignment="spaceBetween")
                            )
                        )
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte.", color="white54"))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv", size=20, weight="bold", color="white"))
            email = ft.TextField(value="registration-mibi.ber@tentamus.com", read_only=True, color="white", border="none", text_align="center", width=350)
            ansicht.controls.append(ft.Container(bgcolor="#1a1a1a", padding=15, border_radius=15, width=350, content=ft.Column([ft.Text("E-MAIL KOPIEREN:", color="orange", weight="bold"), email], horizontal_alignment="center")))
            page.update()

        zeige_startbildschirm()
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")
