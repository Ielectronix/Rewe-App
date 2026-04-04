import flet as ft
from datenverwaltung import lade_maerkte, lade_benutzer
from formular import zeige_maske_ui

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Fordert Android-Berechtigungen direkt über die Seite an
    def check_permissions(e=None):
        page.request_permission(ft.PermissionType.WRITE_EXTERNAL_STORAGE)
        page.request_permission(ft.PermissionType.MANAGE_EXTERNAL_STORAGE)
        page.update()

    ansicht = ft.Column(expand=True)
    page.add(ansicht)

    def zeige_dashboard():
        ansicht.controls.clear()
        ansicht.controls.append(ft.Row([
            ft.Text("Meine Touren", size=25, weight="bold"),
            ft.IconButton(icon=ft.icons.LOCK_OPEN, icon_color="orange", on_click=check_permissions)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        for i, m in enumerate(lade_maerkte()):
            ansicht.controls.append(ft.ListTile(
                title=ft.Text(f"{m.get('marktnummer')} - {m.get('adresse')}", color="white"),
                on_click=lambda e, idx=i: zeige_maske_ui(page, ansicht, zeige_dashboard, idx)
            ))
        
        ansicht.controls.append(ft.ElevatedButton("Neue Tour", icon=ft.icons.ADD, on_click=lambda _: zeige_maske_ui(page, ansicht, zeige_dashboard, None)))
        page.update()

    # App Start: Erst Rechte fragen, dann Dashboard
    page.on_connect = check_permissions
    zeige_dashboard()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")