import flet as ft

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Navigation oben
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.REORDER),
        leading_width=40,
        title=ft.Text("Rewe Monitoring"),
        center_title=False,
        bgcolor=ft.colors.RED, # Dein rotes Design-Element
        actions=[
            ft.IconButton(ft.icons.SETTINGS),
        ],
    )

    def change_tab(e):
        # Hier steuern wir später, was passiert wenn man oben klickt
        index = e.control.selected_index
        if index == 0:
            show_login()
        elif index == 1:
            show_maske()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.LOCK, label="Login"),
            ft.NavigationDestination(icon=ft.icons.EDIT_NOTE, label="Maske"),
            ft.NavigationDestination(icon=ft.icons.PICTURE_AS_PDF, label="PDF Helfer"),
        ],
        on_change=change_tab,
        bgcolor="#002200"
    )

    def show_login():
        page.clean()
        page.add(
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Login", size=30, color="white"),
                    ft.TextField(label="User", text_align=ft.TextAlign.CENTER, width=300),
                    ft.TextField(label="Pass", password=True, text_align=ft.TextAlign.CENTER, width=300),
                    ft.ElevatedButton("Starten", bgcolor="red", color="white")
                ]
            )
        )

    def show_maske():
        page.clean()
        page.add(
            ft.Text("PDF Maske & Zuweisung", size=25, color="white"),
            ft.Text("Hier werden die IDs aus dem PDF automatisch gefüllt.", color="white70"),
            ft.ElevatedButton("Original PDF hochladen", icon=ft.icons.UPLOAD_FILE),
            ft.Divider(),
            ft.TextField(label="Messwert 1 (ID: REWE_01)", width=300),
            ft.ElevatedButton("PDF Generieren", icon=ft.icons.DOWNLOAD, bgcolor="red", color="white")
        )

    # Starte mit dem Login
    show_login()

if __name__ == "__main__":
    ft.app(target=main)