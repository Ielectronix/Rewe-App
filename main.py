import flet as ft
import traceback
import os

def main(page: ft.Page):
    # --- GRUND-SETUP ---
    page.bgcolor = "#003300"
    page.title = "REWE Monitoring"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # Module für später im Hintergrund bereitstellen
    ph = ft.PermissionHandler()
    share = ft.Share()
    page.overlay.extend([ph, share])

    # Haupt-Container
    ansicht = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    # --- DIE LOGIK FÜR DEN BUTTON ---
    def start_klick(e):
        # 1. Visuelles Feedback: Button zeigt, dass er arbeitet
        btn_start.disabled = True
        btn_start.text = "Lade Dashboard..."
        page.update()

        # 2. Versuch der Rechte-Abfrage (ohne die App zu blockieren)
        try:
            ph.request_permission(ft.PermissionType.STORAGE)
        except:
            pass # Falls Android blockt, ignorieren wir es hier einfach

        # 3. WEITER GEHT'S: Wir laden jetzt dein echtes Menü!
        # Hier rufen wir jetzt deine Dashboard-Funktion auf
        zeige_dashboard()

    # --- DEIN ECHTES DASHBOARD (Hier kommt dein Menü rein) ---
    def zeige_dashboard():
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text("MEINE TOUREN", size=25, weight="bold", color="white"))
        
        # Beispiel-Tour-Button (Hier kannst du deine echte Touren-Schleife einbauen)
        ansicht.controls.append(
            ft.Container(
                bgcolor="#005500",
                padding=10,
                border_radius=10,
                content=ft.Text("🚚 Tour A: REWE Markt 123", color="white")
            )
        )
        
        ansicht.controls.append(
            ft.ElevatedButton("Zurück zum Start", on_click=lambda _: zeige_start())
        )
        page.update()

    # --- DER STARTBILDSCHIRM (Das, was du auf dem Foto siehst) ---
    def zeige_start():
        ansicht.controls.clear()
        ansicht.controls.extend([
            ft.Text("REWE MONITORING", size=32, weight="bold", color="red"),
            ft.Container(height=20),
            btn_start
        ])
        page.update()

    # Den Button einmal global definieren
    btn_start = ft.ElevatedButton(
        "Neuen Tag starten", 
        on_click=start_klick, 
        bgcolor="white", 
        color="black",
        width=250,
        height=50
    )

    # App mit dem Startbildschirm öffnen
    zeige_start()

if __name__ == "__main__":
    ft.app(target=main)