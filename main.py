import flet as ft
import traceback # Das ist unser "Flugschreiber" für genaue Zeilennummern

def main(page: ft.Page):
    # Wenn die Fehlermeldung lang wird, können wir jetzt scrollen!
    page.scroll = ft.ScrollMode.AUTO 
    
    try:
        # 1. Grunddesign setzen
        page.title = "Rewe Monitoring"
        page.bgcolor = "#003300"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.padding = 20

        # 2. Testen, ob das PDF-Werkzeug der Übeltäter ist
        import pypdf

        # 3. UI Elemente bauen
        header = ft.Text(
            spans=[
                ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=40)),
                ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=40)),
            ],
            text_align=ft.TextAlign.CENTER
        )
        
        user_input = ft.TextField(label="Benutzername", text_align=ft.TextAlign.CENTER, color="white", border_color="white")
        pass_input = ft.TextField(label="Passwort", password=True, text_align=ft.TextAlign.CENTER, color="white", border_color="white")
        
        def dummy_login(e):
            try:
                page.add(ft.Text("Login erfolgreich! Keine Fehler gefunden.", color="green", size=20))
                page.update()
            except Exception as ex:
                show_error_screen(page, ex)

        # 4. Alles auf den Bildschirm packen
        page.add(
            header,
            ft.Text("App erfolgreich geladen!", color="white70"),
            ft.Divider(color="transparent"),
            user_input,
            pass_input,
            ft.ElevatedButton("Einloggen", on_click=dummy_login, bgcolor="red", color="white")
        )

    except Exception as e:
        # WENN HIER IRGENDWAS SCHIEFGEHT, STARTET DER NOTFALL-BILDSCHIRM
        show_error_screen(page, e)

def show_error_screen(page: ft.Page, error: Exception):
    # Bildschirm leeren und auf "Alarm" schalten
    page.clean()
    page.bgcolor = "black"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    
    # Den genauen Fehlertext holen (inklusive Zeilennummer!)
    error_details = traceback.format_exc()
    
    page.add(
        ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red", size=60),
        ft.Text("SYSTEM-ABSTURZ", color="red", size=25, weight="bold"),
        ft.Text("Bitte mach einen Screenshot von diesem Text:", color="white", size=16),
        ft.Divider(color="white"),
        # Dieser Text zeigt uns jedes Detail des Fehlers:
        ft.Text(error_details, color="yellow", size=12, selectable=True)
    )
    page.update()

if __name__ == "__main__":
    ft.app(target=main)