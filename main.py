import flet as ft
import traceback

def main(page: ft.Page):
    # 1. SOFORT die Seite grün machen (Kein weißer Bildschirm möglich!)
    page.bgcolor = "#003300"
    page.title = "REWE Monitoring"
    page.update() 

    try:
        # 2. Werkzeuge ganz vorsichtig vorbereiten
        # Wir nutzen hier nur die Standard-Sachen, um Abstürze zu vermeiden
        share = ft.Share()
        page.overlay.append(share)
        page.update()

        # 3. Den Inhalt bauen
        ansicht = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
        page.add(ansicht)

        def start_klick(e):
            # Hier laden wir später deine Dashboard-Logik
            ansicht.controls.clear()
            ansicht.controls.append(ft.Text("Lade Dashboard...", color="white"))
            page.update()

        # 4. UI anzeigen
        ansicht.controls.extend([
            ft.Text("REWE MONITORING", size=32, weight="bold", color="red"),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Neuen Tag starten", 
                on_click=start_klick,
                bgcolor="white",
                color="black",
                width=250,
                height=50
            )
        ])
        page.update()

    except Exception as e:
        # Falls DOCH etwas schief geht, zeigen wir es auf dem Schirm!
        page.add(ft.Text(f"Start-Fehler: {str(e)}", color="yellow"))
        page.add(ft.Text(traceback.format_exc(), color="white", size=10))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)