import flet as ft
import traceback

def main(page: ft.Page):
    page.bgcolor = "#003300"
    page.title = "REWE Debug Mode"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # WICHTIG: Das Werkzeug vorbereiten
    ph = ft.PermissionHandler()
    page.overlay.append(ph)

    # Ein Textfeld für Fehlermeldungen (damit wir sehen, was passiert!)
    info_text = ft.Text("Bitte auf den Button drücken", color="white")

    def button_klick(e):
        info_text.value = "Button wurde gedrückt... versuche Einstellungen zu öffnen..."
        info_text.color = "yellow"
        page.update()
        
        try:
            # Versuch 1: App-Einstellungen direkt öffnen
            ph.open_app_settings()
        except Exception as ex:
            # Falls das fehlschlägt, zeigen wir den Fehler hier an!
            info_text.value = f"FEHLER: {str(ex)}"
            info_text.color = "red"
            page.update()

    btn = ft.ElevatedButton(
        "ZUGRIFF FREISCHALTEN", 
        on_click=button_klick,
        bgcolor="white",
        color="black",
        width=250,
        height=60
    )

    page.add(
        ft.Text("REWE MONITORING", size=30, weight="bold", color="red"),
        ft.Container(height=20),
        info_text,
        ft.Container(height=10),
        btn
    )

if __name__ == "__main__":
    ft.app(target=main)