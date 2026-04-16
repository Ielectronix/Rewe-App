import flet as ft
import traceback

def main(page: ft.Page):
    # Einfache Einstellungen, die immer funktionieren
    page.bgcolor = "#003300"
    page.title = "REWE Monitoring"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Haupt-Container
    ansicht = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    # Wir laden die anderen Dateien (formular, etc.) nur, wenn sie da sind
    try:
        from datenverwaltung import lade_benutzer, speichere_benutzer
        from formular import zeige_maske_ui
        
        # Das Teilen-Modul (Das brauchen wir für den Senden-Button!)
        share = ft.Share()
        page.overlay.append(share)

        def start_klick(e):
            # Wir gehen einfach direkt zum Dashboard/Formular
            # Wenn die Rechte im System fehlen, merken wir das erst beim Speichern
            zeige_dashboard()

        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(ft.Text("DASHBOARD", size=30, color="white"))
            # Hier kommt dein normaler Code wieder rein...
            page.update()

        # Start-Bildschirm
        ansicht.controls.extend([
            ft.Text("REWE MONITORING", size=32, weight="bold", color="red"),
            ft.ElevatedButton("Neuen Tag starten", on_click=start_klick, bgcolor="white", color="black")
        ])
        
    except Exception as e:
        ansicht.controls.append(ft.Text(f"Fehler beim Laden: {e}", color="yellow"))

    page.update()

if __name__ == "__main__":
    ft.app(target=main)