import flet as ft
import os

def main(page: ft.Page):
    page.title = "REWE Monitoring"
    page.bgcolor = "#003300"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Module vorbereiten
    ph = ft.PermissionHandler()
    share = ft.Share()
    page.overlay.extend([ph, share])

    # Funktion, um die Systemeinstellungen direkt zu öffnen
    def oeffne_einstellungen(e):
        # Das schickt den Nutzer direkt in das App-Info Menü
        ph.open_app_settings()

    # Die Ansicht
    status_text = ft.Text("Prüfe Berechtigungen...", color="white")
    
    # Button, der nur erscheint, wenn der Zugriff blockiert ist
    settings_btn = ft.ElevatedButton(
        "System-Einstellungen öffnen", 
        icon=ft.icons.SETTINGS,
        on_click=oeffne_einstellungen,
        visible=False,
        bgcolor="orange",
        color="black"
    )

    def check_initial_perms():
        # Wir prüfen nur leise, ob wir schreiben dürfen
        # Falls nicht, zeigen wir den Button für die Einstellungen
        if page.platform == ft.PagePlatform.ANDROID:
            status_text.value = "Hinweis: Vollzugriff auf Speicher wird benötigt."
            settings_btn.visible = True
            page.update()

    # UI Aufbau
    page.add(
        ft.Column([
            ft.Container(height=50),
            ft.Row([ft.Text("REWE ", size=32, color="red", weight="bold"), 
                    ft.Text("Monitoring", size=32, color="white", weight="bold")], 
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([settings_btn], alignment=ft.MainAxisAlignment.CENTER),
            ft.ElevatedButton("Tag starten", on_click=lambda _: page.update(), bgcolor="red", color="white")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # Nach dem Laden kurz prüfen
    page.on_connect = lambda _: check_initial_perms()
    page.update()

if __name__ == "__main__":
    ft.app(target=main)