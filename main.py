import flet as ft
import sys
import traceback

# --- NOTFALL-LOGGING (Fängt Fehler ab, bevor die App startet) ---
error_message = None
try:
    import os
    from datetime import datetime
    # Hier vermuten wir den Fehler (z.B. pypdf nicht installiert)
    import pypdf
    from pdf_helper import stamm_daten_pdf_erstellen
except Exception:
    # Speichert den kompletten Fehler-Text
    error_message = traceback.format_exc()

def main(page: ft.Page):
    page.title = "Bilacon LIMS-App - Rettungsmodus"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT

    # FALLS EIN FEHLER BEIM LADEN PASSIERT IST:
    if error_message:
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.REPORT_GMAILERRORRED_ROUNDED, color="red", size=50),
                    ft.Text("START-FEHLER ERKANNT", size=20, weight="bold", color="red"),
                    ft.Text("Die App konnte nicht laden. Wahrscheinlich fehlt eine Bibliothek (z.B. pypdf) oder eine Datei."),
                    ft.Divider(),
                    ft.Text("TECHNISCHE DETAILS (Bitte kopieren):", weight="bold"),
                    ft.Container(
                        content=ft.Text(error_message, font_family="monospace", size=12, selectable=True),
                        bgcolor="#f0f0f0",
                        padding=10,
                        border_radius=5
                    ),
                    ft.ElevatedButton("Seite neu laden", on_click=lambda _: page.update())
                ]),
                padding=20
            )
        )
        page.update()
        return

    # --- WENN ALLES OK IST, ZEIGE DAS DASHBOARD ---
    # (Hier kommt der Rest deines normalen Codes hin...)
    page.add(ft.Text("✅ App erfolgreich geladen!", size=25, color="green"))
    page.add(ft.ElevatedButton("Zum Dashboard", on_click=lambda _: page.go("/dashboard")))
    
    # ... Rest der App (wie in der letzten Nachricht)
    page.update()

# WICHTIG: Das hier muss ganz unten stehen
if __name__ == "__main__":
    ft.app(target=main)