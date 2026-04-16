import flet as ft
import traceback
import os
import datetime
import shutil
import urllib.parse

def main(page: ft.Page):
    # --- 1. MODULE IM HINTERGRUND LADEN (Verhindert roten Balken) ---
    ph = ft.PermissionHandler()
    share = ft.Share()
    # WICHTIG: Overlay benutzen, nicht page.add!
    page.overlay.extend([ph, share])
    
    # --- 2. GRUND-EINSTELLUNGEN ---
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" # Das REWE-Grün
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = ft.padding.only(left=10, top=55, right=10, bottom=10)
    page.scroll = ft.ScrollMode.AUTO

    # Container für die verschiedenen Ansichten
    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    page.add(ansicht)

    # --- FEHLER-ANZEIGE ---
    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=20))
        try:
            ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=12))
        except:
            pass
        page.update()

    try:
        # Importe deiner anderen Dateien
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # --- HILFSFUNKTION FÜR BUTTONS ---
        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            text_size = 18 if text in ["🗑️", "📤"] else 12 
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", size=text_size),
                on_click=on_click, bgcolor=bgcolor, color=color, 
                expand=expand, height=height, width=width,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )

        # --- NAVIGATION ---
        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=10, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("🚚 Touren", lambda e: zeige_dashboard(), "#004400", "white", expand=True, height=50),
                    sicherer_button("📤 Senden", lambda e: zeige_postausgang(), "#004400", "white", expand=True, height=50),
                    sicherer_button("🗄️ Archiv", lambda e: zeige_archiv(), "#004400", "white", expand=True, height=50)
                ])
            )

        # --- STARTBILDSCHIRM ---
        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", border_color="white")
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", border_color="white")
            
            def start_klick(e):
                # Beim Start versuchen wir die Rechte zu holen
                try:
                    ph.request_permission(ft.PermissionType.STORAGE)
                except:
                    pass
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()

            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            
            ansicht.controls.extend([
                ft.Container(height=50),
                ft.Row([ft.Text("REWE MONITORING", size=32, weight="bold", color="red")], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=40),
                v_in, z_in,
                ft.Container(height=20),
                ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)
            ])
            page.update()

        # --- DASHBOARD (TOUREN-LISTE) ---
        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white"))
            
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren angelegt.", color="grey"))
            else:
                for index, markt in enumerate(maerkte):
                    mnr = markt.get("marktnummer", "Unbenannt")
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    btn_tour = sicherer_button(f"🚚 Tour: {mnr}", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500", "white", expand=True)
                    btn_del = sicherer_button("🗑️", loesche_t, "red", "white", width=60)
                    ansicht.controls.append(ft.Row([btn_tour, btn_del]))
            
            btn_neu = sicherer_button("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", "white", height=50, width=200)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        # --- POSTAUSGANG (SENDEN-FUNKTION) ---
        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Senden", size=25, weight="bold", color="white"))
            
            # Hier nur ein Beispiel, wie das Teilen aufgerufen wird:
            async def teilen_test(e):
                # Beispiel: Wenn du eine Datei hättest:
                # await share.share_files([ft.ShareFile.from_path("/pfad/zu/deiner.pdf")])
                await share.share_files(None, text="Test-Nachricht aus der REWE App")

            ansicht.controls.append(sicherer_button("📤 Test Senden", teilen_test, "blue"))
            page.update()

        # --- ARCHIV ---
        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv", size=25, weight="bold", color="white"))
            ansicht.controls.append(ft.Text("Hier liegen die PDFs der letzten 7 Tage.", color="grey"))
            page.update()

        # App mit Startbildschirm starten
        zeige_startbildschirm()

    except Exception as e:
        zeige_fehler(e)

if __name__ == "__main__":
    ft.app(target=main)