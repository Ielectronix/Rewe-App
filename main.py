import flet as ft
import traceback

def main(page: ft.Page):
    # 1. Grundzustand herstellen 
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = ft.padding.only(left=10, top=55, right=10, bottom=10)
    page.scroll = ft.ScrollMode.AUTO

    # DEN FEHLER BEHOBEN: Wir hängen das Teilen-Modul NICHT mehr an den Bildschirm an!
    # Das verhindert den roten "Unknown control"-Balken.
    share = ft.Share()

    # Haupt-Container
    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    page.add(ansicht)

    # Einfache Fehleranzeige
    def zeige_fehler(e):
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text(f"Systemfehler: {e}", color="yellow", size=16))
        page.update()

    try:
        # Import deiner eigenen Dateien
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from formular import zeige_maske_ui

        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold"),
                on_click=on_click, bgcolor=bgcolor, color=color, 
                expand=expand, height=height, width=width
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
            v_in = ft.TextField(label="Vorname", value=v)
            z_in = ft.TextField(label="Nachname", value=z)
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()

            ansicht.controls.extend([
                ft.Container(height=30),
                
                # --- HIER IST DEIN NEUES DESIGN ---
                ft.Row([
                    ft.Text("REWE", size=30, weight="bold", color="red"),
                    ft.Text("MONITORING", size=30, weight="bold", color="white")
                ], alignment=ft.MainAxisAlignment.CENTER),
                # ----------------------------------
                
                ft.Container(height=30),
                v_in, z_in,
                ft.Container(height=30),
                ft.Row([sicherer_button("TAG STARTEN", start_klick, "red", "white", height=60, width=250)], alignment=ft.MainAxisAlignment.CENTER)
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Meine Touren", size=20, weight="bold", color="white"))
            
            maerkte = lade_maerkte()
            for index, markt in enumerate(maerkte):
                btn = sicherer_button(f"Tour: {markt.get('marktnummer')}", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500")
                ansicht.controls.append(btn)
            
            btn_neu = sicherer_button("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red")
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Senden", size=25, color="white"))
            
            async def teilen_klick(e):
                pass

            ansicht.controls.append(sicherer_button("📤 PDF TEILEN", teilen_klick, "blue", height=60))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv", size=25, color="white"))
            page.update()

        # Start
        zeige_startbildschirm()

    except Exception as e:
        zeige_fehler(e)

if __name__ == "__main__":
    ft.app(target=main)