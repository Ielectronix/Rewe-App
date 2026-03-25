import flet as ft
import os
from datetime import datetime

def main(page: ft.Page):
    page.title = "Bilacon LIMS-App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = "adaptive"

    # --- SPEICHER-LOGIK ---
    vorlagen_pfad = page.client_storage.get("vorlagen_pfad")

    # --- FILEPICKER SETUP ---
    def on_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            page.client_storage.set("vorlagen_pfad", e.path)
            status_pfad.value = f"✅ Ordner verknüpft: {e.path}"
            status_pfad.color = ft.colors.GREEN
        else:
            status_pfad.value = "❌ Auswahl abgebrochen"
            status_pfad.color = ft.colors.RED
        page.update()

    file_picker = ft.FilePicker(on_result=on_directory_result)
    page.overlay.append(file_picker)
    status_pfad = ft.Text(f"Aktueller Pfad: {vorlagen_pfad if vorlagen_pfad else 'Nicht gewählt'}")

    # --- NAVIGATIONSLOGIK ---
    def route_change(route):
        page.views.clear()
        
        # LOGIN (Startseite)
        if page.route == "/":
            page.views.append(
                ft.View("/", [
                    ft.AppBar(title=ft.Text("Bilacon Login"), bgcolor=ft.colors.SURFACE_VARIANT),
                    ft.Icon(ft.icons.LOCK_PERSON, size=100, color=ft.colors.BLUE),
                    ft.TextField(label="Mitarbeiter-Kürzel"),
                    ft.ElevatedButton("Anmelden", on_click=lambda _: page.go("/dashboard")),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

        # DASHBOARD
        elif page.route == "/dashboard":
            page.views.append(
                ft.View("/dashboard", [
                    ft.AppBar(title=ft.Text("Hauptmenü"), bgcolor=ft.colors.BLUE_50),
                    ft.Text("Willkommen!", size=25, weight="bold"),
                    ft.ElevatedButton("Tour starten", icon=ft.icons.PLAY_ARROW, on_click=lambda _: page.go("/tour")),
                    ft.ElevatedButton("Einstellungen", icon=ft.icons.SETTINGS, on_click=lambda _: page.go("/settings")),
                ])
            )

        # EINSTELLUNGEN
        elif page.route == "/settings":
            page.views.append(
                ft.View("/settings", [
                    ft.AppBar(title=ft.Text("Einstellungen")),
                    ft.Text("OneDrive Vorlagen-Pfad", weight="bold"),
                    status_pfad,
                    ft.ElevatedButton("Ordner wählen", icon=ft.icons.FOLDER, on_click=lambda _: file_picker.get_directory_path()),
                    ft.ElevatedButton("Zurück zum Menü", on_click=lambda _: page.go("/dashboard")),
                ])
            )

        page.update()

    page.on_route_change = route_change
    page.go(page.route)

# --- DIESER TEIL IST JETZT DER SCHLÜSSEL ---
if __name__ == "__main__":
    # Wir sagen Flet hier direkt: Hoste die App im Netzwerk auf Port 8550
    ft.app(target=main, view=None, port=8550, host="0.0.0.0")
