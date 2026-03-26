import flet as ft

def main(page: ft.Page):
    page.title = "LIMS Startbildschirm"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def handle_result(e: ft.FilePickerResultEvent):
        if e.files:
            status_text.value = f"✅ Geladen: {e.files[0].name}"
            status_text.color = ft.Colors.GREEN
        else:
            status_text.value = "❌ Auswahl abgebrochen"
            status_text.color = ft.Colors.RED
        page.update()

    pick_files_dialog = ft.FilePicker(on_result=handle_result)
    page.overlay.append(pick_files_dialog)

    status_text = ft.Text("Keine Vorlage gewählt", color=ft.Colors.GREY_400)

    page.add(
        ft.Text("LIMS / REWE App", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.ElevatedButton(
            "📂 PDF-Vorlage suchen",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: pick_files_dialog.pick_files(allowed_extensions=["pdf"])
        ),
        ft.Padding(content=status_text, padding=ft.padding.only(top=20))
    )

ft.app(target=main) # Ganz wichtig: Nur so für die Handy-App!