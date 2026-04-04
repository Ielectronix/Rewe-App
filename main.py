import flet as ft
import traceback

def main(page: ft.Page):
    # Basis-Setup
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300"
    page.scroll = ft.ScrollMode.AUTO
    
    ansicht = ft.Column(expand=True)
    page.add(ansicht)
    
    # ---------------------------------------------------------
    # DER FEHLER-SCANNER: Fängt alle Abstürze beim Start ab!
    # ---------------------------------------------------------
    try:
        from datenverwaltung import lade_maerkte, lade_benutzer
        from formular import zeige_maske_ui
        
        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(ft.Text("Meine Touren", size=25, weight="bold", color="white"))
            
            maerkte = lade_maerkte()
            for i, m in enumerate(maerkte):
                ansicht.controls.append(ft.ListTile(
                    title=ft.Text(f"{m.get('marktnummer', '???')} - {m.get('adresse', 'Unbekannt')}", color="white"),
                    on_click=lambda e, idx=i: zeige_maske_ui(page, ansicht, zeige_dashboard, idx)
                ))
            ansicht.controls.append(ft.ElevatedButton("Neue Tour", icon=ft.icons.ADD, on_click=lambda _: zeige_maske_ui(page, ansicht, zeige_dashboard, None)))
            page.update()

        # Versuche das Dashboard zu laden
        zeige_dashboard()
        
    except Exception as e:
        # Falls irgendwas schiefgeht, zeige den roten Fehler-Bildschirm!
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text("⚠️ SYSTEM-ABSTURZ!", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(f"Fehler: {str(e)}", color="yellow", size=20))
        ansicht.controls.append(ft.Text("Details für den Programmierer:", color="white", weight="bold"))
        ansicht.controls.append(ft.Text(traceback.format_exc(), color="white54", size=12))
        page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")