import flet as ft
import traceback

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300"
    page.scroll = ft.ScrollMode.AUTO
    ansicht = ft.Column(expand=True)
    page.add(ansicht)
    
    # BERECHTIGUNG ANFORDERN
    def check_permissions(e=None):
        page.request_permission(ft.PermissionType.WRITE_EXTERNAL_STORAGE)
        page.request_permission(ft.PermissionType.MANAGE_EXTERNAL_STORAGE)
        page.update()

    try:
        from datenverwaltung import lade_maerkte
        from formular import zeige_maske_ui
        
        def zeige_dashboard():
            ansicht.controls.clear()
            
            # HIER IST DER FIX: Text-Emojis statt ft.icons!
            ansicht.controls.append(ft.Row([
                ft.Text("Meine Touren", size=25, weight="bold", color="white"),
                ft.ElevatedButton("🔓 Rechte prüfen", color="orange", bgcolor="#111111", on_click=check_permissions)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
            
            for i, m in enumerate(lade_maerkte()):
                ansicht.controls.append(ft.ListTile(
                    title=ft.Text(f"{m.get('marktnummer', '???')} - {m.get('adresse', 'Unbekannt')}", color="white"),
                    on_click=lambda e, idx=i: zeige_maske_ui(page, ansicht, zeige_dashboard, idx)
                ))
                
            # HIER IST DER FIX: Text-Emoji "➕" statt ft.icons.ADD!
            ansicht.controls.append(ft.ElevatedButton("➕ Neue Tour", on_click=lambda _: zeige_maske_ui(page, ansicht, zeige_dashboard, None)))
            page.update()

        page.on_connect = check_permissions
        zeige_dashboard()
        
    except Exception as e:
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text("⚠️ SYSTEM-ABSTURZ!", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(f"Fehler: {str(e)}", color="yellow", size=20))
        ansicht.controls.append(ft.Text("Details für den Programmierer:", color="white", weight="bold"))
        ansicht.controls.append(ft.Text(traceback.format_exc(), color="white54", size=12))
        page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")