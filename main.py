import flet as ft
import traceback

def main(page: ft.Page):
    # =========================================================
    # DAS ABSOLUTE SICHERHEITSNETZ
    # =========================================================
    try:
        page.title = "Rewe Monitoring System"
        page.bgcolor = "#003300" # Dunkelgrün
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 20

        # PDF-Werkzeug laden (lassen wir zur Sicherheit mal drin)
        import pypdf

        # 2. Speicher-Helfer
        def lade_maerkte():
            return page.client_storage.get("meine_maerkte") or []

        def speichere_maerkte(maerkte_liste):
            page.client_storage.set("meine_maerkte", maerkte_liste)

        # 3. UNSERE TEXT-BASIERTE NAVIGATION (Sicherer als Emojis!)
        def nav_leiste():
            return ft.Container(
                bgcolor="#001100",
                padding=10,
                border_radius=10,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        # Alle Emojis und Icons wurden entfernt
                        ft.TextButton("Märkte", on_click=lambda e: zeige_dashboard(), style=ft.ButtonStyle(color="white")),
                        ft.TextButton("Postausgang", on_click=lambda e: zeige_postausgang(), style=ft.ButtonStyle(color="white")),
                        ft.TextButton("Archiv", on_click=lambda e: zeige_archiv(), style=ft.ButtonStyle(color="white")),
                    ]
                )
            )

        # ---------------- DIE VERSCHIEDENEN SEITEN ----------------

        def zeige_startbildschirm():
            page.clean()
            
            header = ft.Text(
                spans=[
                    ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=45)),
                    ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=45)),
                ], text_align=ft.TextAlign.CENTER
            )
            
            def start_klick(e):
                zeige_dashboard()

            # BEHOBEN: Der große grüne Haken wurde entfernt
            page.add(
                ft.Container(height=50),
                ft.Row([header], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=30),
                
                # Wir fügen hier stattdessen einen beschreibenden Text hinzu
                ft.Text("Protokollierung", size=20, color="white", weight="bold", text_align=ft.TextAlign.CENTER),
                
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
            maerkte = lade_maerkte()

            # Navigation wird ganz oben als "Tab-Leiste" eingefügt
            page.add(nav_leiste())
            page.add(ft.Divider(color="transparent"))
            
            page.add(ft.Text("Meine heutigen Märkte", size=25, weight="bold", color="white"))
            
            if not maerkte:
                page.add(ft.Text("Noch keine Märkte für heute geplant. Leg direkt los!", color="grey", size=16))
            else:
                for index, markt in enumerate(maerkte):
                    # Button für bestehenden Markt
                    page.add(
                        ft.ElevatedButton(
                            f"Filiale: {markt['name']} ({markt['ort']})", 
                            on_click=lambda e, i=index: zeige_maske(i),
                            width=300, height=50, bgcolor="#005500", color="white"
                        )
                    )

            # BEHOBEN: Emoji aus dem Button entfernt
            page.add(
                ft.Divider(color="white"),
                ft.Row([ft.ElevatedButton("Markt anlegen", on_click=lambda e: zeige_maske(None), bgcolor="red", color="white", height=50)], alignment=ft.MainAxisAlignment.CENTER)
            )
            page.update()

        def zeige_maske(markt_index):
            page.clean()
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
                zeige_dashboard()

            def zurueck_klick(e):
                zeige_dashboard()

            # BEHOBEN: Emojis aus den Buttons entfernt
            button_reihe = [
                ft.ElevatedButton("Speichern", on_click=speichere_klick, bgcolor="green", color="white"),
                ft.TextButton("Zurück", on_click=zurueck_klick, style=ft.ButtonStyle(color="white"))
            ]

            if markt_index is not None:
                def loeschen_klick(e):
                    maerkte.pop(markt_index)
                    speichere_maerkte(maerkte)
                    zeige_dashboard()
                    
                # BEHOBEN: Emoji aus dem Button entfernt
                button_reihe.append(ft.ElevatedButton("Löschen", bgcolor="red", color="white", on_click=loeschen_klick))

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
            page.add(nav_leiste())
            page.add(ft.Divider(color="transparent"))
            
            page.add(
                ft.Text("Postausgang", size=25, weight="bold", color="white"),
                ft.Text("Hier landen die fertigen PDFs.", color="grey"),
                ft.Divider(color="white"),
                
                ft.ListTile(
                    leading=ft.Text("P", size=30, color="red"), # Platzhalter statt Emoji
                    title=ft.Text("Protokoll.pdf", color="white"),
                    subtitle=ft.Text("Heute generiert - Bereit", color="grey")
                )
            )
            page.update()

        def zeige_archiv():
            page.clean()
            page.add(nav_leiste())
            page.add(ft.Divider(color="transparent"))
            
            page.add(
                ft.Text("Archiv", size=25, weight="bold", color="white"),
                ft.Text("Tippe auf 'Bearbeiten', um Daten nachträglich zu ändern.", color="grey"),
                ft.Divider(color="white"),
                
                ft.ListTile(
                    leading=ft.Text("A", size=30, color="green"), # Platzhalter statt Emoji
                    title=ft.Text("Beispiel Filiale", color="white"),
                    subtitle=ft.Text("Abgeschlossen", color="grey"),
                    # BEHOBEN: Emoji entfernt
                    trailing=ft.TextButton("Bearbeiten")
                )
            )
            page.update()

        # START DER APP!
        zeige_startbildschirm()

    except Exception as e:
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