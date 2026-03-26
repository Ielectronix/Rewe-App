import flet as ft

def main(page: ft.Page):
    page.title = "LIMS / REWE App"
    page.theme_mode = ft.ThemeMode.DARK
    # Zentriert alles schön für das Handy-Display
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Icon(name=ft.icons.PHONELINK_SETUP, color="blue", size=60),
        ft.Text("LIMS Mobile System", size=32, weight="bold"),
        ft.Text("Status: APK Build erfolgreich", size=16, italic=True, color="grey"),
        ft.Divider(height=30),
        ft.ElevatedButton(
            "PDF Scanner starten", 
            icon=ft.icons.DOCUMENT_SCANNER,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        ),
        ft.TextButton("Einstellungen", icon=ft.icons.SETTINGS)
    )

if __name__ == "__main__":
    # Für die APK brauchen wir kein 'port' oder 'host'
    ft.app(target=main)