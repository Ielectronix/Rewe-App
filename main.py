import flet as ft
import traceback

def main(page: ft.Page):
    # =========================================================
    # DAS ABSOLUTE SICHERHEITSNETZ
    # =========================================================
    try:
        # 1. Grund-Setup
        page.title = "Rewe Monitoring"
        page.bgcolor = "#003300"
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 20

        # PDF-Werkzeug laden
        import pypdf

        # 2. Speicher-Helfer
        def lade_maerkte():
            return page.client_storage.get("meine_maerkte") or []

        def speichere_maerkte(maerkte_liste):
            page.client_storage.set("meine_maerkte", maerkte_liste)

        # 3. Navigation
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
                ft.NavigationBarDestination(icon="list", label="Märkte"),
                ft.NavigationBarDestination(icon="upload", label="Postausgang"),
                ft.NavigationBarDestination(icon="archive", label="Archiv"),
            ]
        )
        page.navigation_bar.visible = False

        # ---------------- DIE VERSCHIEDENEN SEITEN ----------------

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
                # Korrektur: Kein "name=" mehr!
                ft.Icon("check_circle", size=100, color="white"),
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

        def zeige_maske(markt_index):
            page.clean()
            page.navigation_bar.visible = False
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
                ft.TextButton("Zurück", on_click=zurueck_klick, icon="arrow_back", icon_color="white")
            ]

            if markt_index is not None:
                def loeschen_klick(e):
                    maerkte.pop(markt_index)
                    speichere_maerkte(maerkte)
                    page.navigation_bar.visible = True
                    zeige_dashboard()
                    
                button_reihe.append(ft.IconButton(icon="delete_forever", icon_color="red", on_click=loeschen_klick))

            page.add(
                ft.Text(titel, size=25, weight="bold", color="white"),
                ft.Divider(color="transparent"),
                name_input, id_input, ort_input,
                ft.Container(height=20),
                ft.Row(button_reihe)
            )
            page.update()

        def zeige_postausgang():
            page.clean()
            page.navigation_bar.selected_index = 1

            page.add(
                ft.Text("Postausgang", size=25, weight="bold", color="white"),
                ft.Text("Hier landen die fertigen PDFs.", color="grey"),
                ft.Divider(color="white"),
                
                ft.ListTile(
                    # Korrektur: Kein "name=" mehr!
                    leading=ft.Icon("picture_as_pdf", color="red"),
                    title=ft.Text("Test_Protokoll.pdf", color="white"),
                    subtitle=ft.Text("Heute generiert - Bereit", color="grey")
                )
            )
            page.update()

        def zeige_archiv():
            page.clean()
            page.navigation_bar.selected_index = 2
            
            page.add(
                ft.Text("Archiv (Letzte 7 Tage)", size=25, weight="bold", color="white"),
                ft.Text("Tippe auf das gelbe Stift-Symbol, um alte Daten nachträglich zu ändern.", color="grey"),
                ft.Divider(color="white"),
                
                ft.ListTile(
                    # Korrektur: Kein "name=" mehr!
                    leading=ft.Icon("archive", color="green"),
                    title=ft.Text("Rewe Musterstadt", color="white"),
                    subtitle=ft.Text("Abgeschlossen", color="grey"),
                    trailing=ft.IconButton(icon="edit", icon_color="yellow")
                )
            )
            page.update()

        # START DER APP!
        zeige_startbildschirm()

    except Exception as e:
        # ABSOLUTER NOTFALL-BILDSCHIRM
        page.clean()
        page.bgcolor = "black"
        page.add(
            ft.Text("FEHLER GEFUNDEN:", color="red", size=30, weight="bold"),
            ft.Text(str(e), color="yellow", size=20)
        )
        try:
            page.add(ft.Text(traceback.format_exc(), color="white", size=12))
        except:
            pass
        page.update()

if __name__ == "__main__":
    ft.app(target=main)