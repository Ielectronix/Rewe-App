import flet as ft
import os
import traceback

def main(page: ft.Page):
    # --- GRUND-EINSTELLUNGEN (Sofort laden!) ---
    page.title = "REWE Monitoring"
    page.bgcolor = "#003300"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Wir definieren die Werkzeuge, aber fassen sie noch nicht an!
    ph = ft.PermissionHandler()
    share = ft.Share()
    page.overlay.extend([ph, share])

    # Das ist unser Haupt-Container
    container = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(container)

    def zeige_fehler(msg):
        container.controls.append(ft.Text(f"FEHLER: {msg}", color="red"))
        page.update()

    def check_rights(e):
        try:
            # Das öffnet die EINSTELLUNGEN der App direkt
            # Hier müssen die Mitarbeiter die 3 Punkte drücken
            ph.open_app_settings()
        except Exception as ex:
            zeige_fehler(str(ex))

    # --- UI AUFBAU ---
    container.controls.extend([
        ft.Text("REWE Monitoring", size=32, weight="bold", color="red"),
        ft.Text("SYSTEM-CHECK", size=20, color="white"),
        ft.Container(height=20),
        ft.Text("Falls das Speichern nicht geht:", color="yellow"),
        ft.ElevatedButton(
            "1. Berechtigungen freischalten", 
            icon=ft.icons.SETTINGS, 
            on_click=check_rights,
            bgcolor="orange",
            color="black"
        ),
        ft.Container(height=20),
        ft.ElevatedButton(
            "2. App starten", 
            on_click=lambda _: starte_app_logik(), 
            bgcolor="green", 
            color="white",
            height=50,
            width=200
        )
    ])

    def starte_app_logik():
        # Hier kommt dein eigentlicher Code rein (Dashboard etc.)
        container.controls.clear()
        container.controls.append(ft.Text("App läuft! Viel Erfolg.", color="green", size=20))
        # Hier rufst du dein zeige_dashboard() auf
        page.update()

    page.update()

if __name__ == "__main__":
    ft.app(target=main)