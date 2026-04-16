import flet as ft
import os

def main(page: ft.Page):
    page.bgcolor = "#003300"
    page.title = "REWE Monitoring"
    
    # Die Werkzeuge laden
    ph = ft.PermissionHandler()
    share = ft.Share()
    page.overlay.extend([ph, share])

    ansicht = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    def start_klick(e):
        # Wir prüfen, ob wir schon schreiben dürfen
        # Falls nicht, schicken wir den User DIREKT in das richtige Menü
        try:
            # Dieser Befehl öffnet bei Android direkt die Seite "Vollzugriff auf Dateien"
            # oder die App-Info, damit man nicht suchen muss!
            ph.open_app_settings() 
            
            # Kurze Info für den Mitarbeiter
            status_text.value = "Bitte 'Alle Dateien verwalten' aktivieren und dann zurückkehren."
            status_text.color = "yellow"
            page.update()
        except:
            pass

    # Der Button, den du auf dem Foto siehst
    btn_start = ft.ElevatedButton(
        "Berechtigung freischalten", 
        on_click=start_klick,
        bgcolor="white",
        color="black",
        width=250,
        height=50
    )

    status_text = ft.Text("Schritt 1: Zugriff erlauben", color="white")

    def zeige_start():
        ansicht.controls.clear()
        ansicht.controls.extend([
            ft.Text("REWE MONITORING", size=32, weight="bold", color="red"),
            ft.Container(height=20),
            status_text,
            btn_start,
            ft.Container(height=20),
            ft.Text("Info: Ohne Vollzugriff kann kein PDF\nim Download-Ordner gespeichert werden.", 
                    size=12, color="white70", text_align=ft.TextAlign.CENTER)
        ])
        page.update()

    zeige_start()

if __name__ == "__main__":
    ft.app(target=main)