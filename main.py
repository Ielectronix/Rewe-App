import flet as ft
import traceback
import os

def main(page: ft.Page):
    # 1. Sofortige Grund-Ansicht
    page.bgcolor = "#003300"
    page.title = "REWE App Debug"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # Ein einfacher Text, der IMMER kommen muss
    debug_text = ft.Text("App gestartet... lade Module...", color="white", size=16)
    page.add(debug_text)
    page.update()

    try:
        # Wir testen die Importe einzeln
        debug_text.value = "Lade Datenverwaltung..."
        page.update()
        import datenverwaltung
        
        debug_text.value = "Lade PDF-Generator..."
        page.update()
        import pdf_generator
        
        debug_text.value = "Lade Formular..."
        page.update()
        import formular

        # Wenn wir hier ankommen, löschen wir den Debug-Text und zeigen den Start-Button
        page.controls.clear()
        
        def starte_tag(e):
            # Hier rufen wir die Rechte ab, wenn man drückt
            ph = ft.PermissionHandler()
            page.overlay.append(ph)
            page.update()
            try:
                ph.request_permission(ft.PermissionType.STORAGE)
            except:
                pass
            # Hier zeigst du dein normales Menü
            page.add(ft.Text("Erfolg! Dashboard wird geladen...", color="green"))
            page.update()

        page.add(
            ft.Text("REWE MONITORING", size=30, weight="bold", color="red"),
            ft.ElevatedButton("Neuen Tag starten", on_click=starte_tag, bgcolor="white", color="black")
        )
        page.update()

    except Exception as e:
        # Wenn es knallt, zeigt uns die App jetzt den Fehler auf dem grünen Schirm!
        fehler_stack = traceback.format_exc()
        page.add(
            ft.Text("LADEFEHLER:", color="red", weight="bold", size=20),
            ft.Text(str(e), color="yellow", size=14),
            ft.Text(fehler_stack, color="white", size=10, selectable=True)
        )
        page.update()

if __name__ == "__main__":
    ft.app(target=main)