import flet as ft
import traceback

def main(page: ft.Page):
    # 1. Grund-Setup
    page.title = "Rewe Monitoring"
    page.bgcolor = "#003300"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # 2. Speicher-Helfer (Das App-Gedächtnis)
    def lade_maerkte():
        return page.client_storage.get("meine_maerkte") or []

    def speichere_maerkte(maerkte_liste):
        page.client_storage.set("meine_maerkte", maerkte_liste)

    # 3. Navigation (Die Leiste unten)
    def tab_gewechselt(e):
        index = e.control.selected_index
        if index == 0:
            zeige_dashboard()
        elif index == 1:
            zeige_postausgang()
        elif index == 2:
            zeige_archiv()

    page.navigation_bar = ft.NavigationBar(
        bgcolor="#001100",
        selected_index=0,
        on_change=tab_gewechselt,
        destinations=[
            ft.NavigationDestination(icon=ft.icons.ASSIGNMENT, label="Märkte"),
            ft.NavigationDestination(icon=ft.icons.OUTBOX, label="Postausgang"),
            ft.NavigationDestination(icon=ft.icons.HISTORY, label="Archiv"),
        ]
    )
    # Erstmal unsichtbar machen, bis man auf "Neuen Tag starten" drückt
    page.navigation_bar.visible = False

    # ---------------- DIE VERSCHIEDENEN SEITEN ----------------

    # SEITE: Der Startbildschirm
    def zeige_startbildschirm():
        page.clean()
        page.navigation_bar.visible = False
        
        header = ft.Text(
            spans=[
                ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=45)),
                ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=45)),
            ], text_align=ft.TextAlign.CENTER
        )
        
        def start_klick(e):
            page.navigation_bar.visible = True
            zeige_dashboard()

        page.add(
            ft.Container(height=50),
            ft.Row([header], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=30),
            ft.Icon(ft.icons.ASSIGNMENT_TURNED_IN, size=100, color="white"),
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton(
                    "Neuen Tag starten", 
                    on_click=start_klick, 
                    bgcolor="red", 
                    color="white",
                    width=250,
                    height=60,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), text_style=ft.TextStyle(size=20, weight="bold"))
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        )
        page.update()

    # SEITE 1: Dashboard (Märkte voranlegen)
    def zeige_dashboard():
        page.clean()
        page.navigation_bar.selected_index = 0
        maerkte = lade_maerkte()

        page.add(ft.Text("Meine heutigen Märkte", size=25, weight="bold", color="white"))
        
        if not maerkte:
            page.add(ft.Text("Noch keine Märkte für heute geplant. Leg direkt los!", color="grey", size=16))
        else:
            for index, markt in enumerate(maerkte):
                page.add(
                    ft.ElevatedButton(
                        f"🏪 {markt['name']} ({markt['ort']})", 
                        on_click=lambda e, i=index: zeige_maske(i),
                        width=300, height=50, bgcolor="#005500", color="white"
                    )
                )

        page.add(
            ft.Divider(color="white"),
            ft.ElevatedButton("+ Neuen Markt voranlegen", on_click=lambda e: zeige_maske(None), bgcolor="red", color="white", height=50)
        )
        page.update()

    # UNTERSEITE: Eingabe-Maske (Vorbereitung / Bearbeitung)
    def zeige_maske(markt_index):
        page.clean()
        page.navigation_bar.visible = False # Navi verstecken beim Tippen
        maerkte = lade_maerkte()
        
        if markt_index is None:
            aktuelle_daten = {"name": "", "rewe_id": "", "ort": ""}
            titel = "Neuen Markt anlegen"
        else:
            aktuelle_daten = maerkte[markt_index]
            titel = "Markt-Daten bearbeiten"

        name_input = ft.TextField(label="Filialname / Bezeichner", value=aktuelle_daten["name"], color="white", border_color="white")
        id_input = ft.TextField(label="REWE-ID (z.B. 12345)", value=aktuelle_daten["rewe_id"], color="white", border_color="white")
        ort_input = ft.TextField(label="Ort", value=aktuelle_daten["ort"], color="white", border_color="white")

        def speichere_klick(e):
            neue_daten = {"name": name_input.value, "rewe_id": id_input.value, "ort": ort_input.value}
            if markt_index is None:
                maerkte.append(neue_daten)
            else:
                maerkte[markt_index] = neue_daten
                
            speichere_maerkte(maerkte)
            page.navigation_bar.visible = True
            zeige_dashboard()

        def zurueck_klick(e):
            page.navigation_bar.visible = True
            zeige_dashboard()

        button_reihe = [
            ft.ElevatedButton("Speichern", on_click=speichere_klick, bgcolor="green", color="white"),
            ft.TextButton("Zurück", on_click=zurueck_klick, icon=ft.icons.ARROW_BACK, icon_color="white")
        ]

        if markt_index is not None:
            def loeschen_klick(e):
                maerkte.pop(markt_index)
                speichere_maerkte(maerkte)
                page.navigation_bar.visible = True
                zeige_dashboard()
                
            button_reihe.append(ft.IconButton(icon=ft.icons.DELETE_FOREVER, icon_color="red", on_click=loeschen_klick))

        page.add(
            ft.Text(titel, size=25, weight="bold", color="white"),
            ft.Divider(color="transparent"),
            name_input, id_input, ort_input,
            ft.Container(height=20),
            ft.Row(button_reihe)
        )
        page.update()

    # SEITE 2: Postausgang
    def zeige_postausgang():
        page.clean()
        page.navigation_bar.selected_index = 1

        def datei_teilen(e):
            # Platzhalter für die spätere OneDrive-Integration
            page.add(ft.Text("PDF wird im Hintergrundordner gespeichert...", color="green"))
            page.update()

        page.add(
            ft.Text("Postausgang", size=25, weight="bold", color="white"),
            ft.Text("Hier landen die fertigen PDFs. (Upload-Funktion in Arbeit)", color="grey"),
            ft.Divider(color="white"),
            
            ft.ListTile(
                leading=ft.Icon(ft.icons.PICTURE_AS_PDF, color="red"),
                title=ft.Text("Test_Protokoll.pdf", color="white"),
                subtitle=ft.Text("Heute generiert - Bereit", color="grey"),
                trailing=ft.IconButton(ft.icons.CLOUD_UPLOAD, icon_color="blue", on_click=datei_teilen)
            )
        )
        page.update()

    # SEITE 3: Archiv
    def zeige_archiv():
        page.clean()
        page.navigation_bar.selected_index = 2
        
        page.add(
            ft.Text("Archiv (Letzte 7 Tage)", size=25, weight="bold", color="white"),
            ft.Text("Tippe auf das gelbe Stift-Symbol, um alte Daten nachträglich zu ändern.", color="grey"),
            ft.Divider(color="white"),
            
            ft.ListTile(
                leading=ft.Icon(ft.icons.HISTORY, color="green"),
                title=ft.Text("Rewe Musterstadt", color="white"),
                subtitle=ft.Text("Abgeschlossen", color="grey"),
                trailing=ft.IconButton(ft.icons.EDIT, icon_color="yellow")
            )
        )
        page.update()

    # ---- NOTFALL-BILDSCHIRM ----
    def show_error_screen(error: Exception):
        page.clean()
        page.bgcolor = "black"
        page.navigation_bar.visible = False
        error_details = traceback.format_exc()
        page.add(
            ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red", size=60),
            ft.Text("SYSTEM-ABSTURZ", color="red", size=25, weight="bold"),
            ft.Text(error_details, color="yellow", size=12, selectable=True)
        )
        page.update()

    # ---- START-CHECK ----
    try:
        import pypdf
        zeige_startbildschirm()
    except Exception as e:
        show_error_screen(e)

if __name__ == "__main__":
    ft.app(target=main)