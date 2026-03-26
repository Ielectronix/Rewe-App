import flet as ft
import traceback

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # =========================================================
    # DER ZENTRALE FEHLER-FÄNGER FÜR ALLES
    # =========================================================
    def zeige_fehler(e):
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

    try:
        import pypdf

        # 2. Speicher-Helfer
        def lade_maerkte():
            return page.client_storage.get("meine_maerkte") or []

        def speichere_maerkte(maerkte_liste):
            page.client_storage.set("meine_maerkte", maerkte_liste)

        # 3. KUGELSICHERE NAVIGATION (Einfache ElevatedButtons)
        def nav_leiste():
            return ft.Container(
                bgcolor="#001100",
                padding=10,
                border_radius=10,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        ft.ElevatedButton("Märkte", on_click=lambda e: zeige_dashboard(), bgcolor="#004400", color="white"),
                        ft.ElevatedButton("Senden", on_click=lambda e: zeige_postausgang(), bgcolor="#004400", color="white"),
                        ft.ElevatedButton("Archiv", on_click=lambda e: zeige_archiv(), bgcolor="#004400", color="white"),
                    ]
                )
            )

        # ---------------- DIE VERSCHIEDENEN SEITEN ----------------

        def zeige_startbildschirm():
            try:
                page.clean()
                page.bgcolor = "#003300"
                
                header = ft.Text(
                    spans=[
                        ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=45)),
                        ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=45)),
                    ], text_align=ft.TextAlign.CENTER
                )
                
                def start_klick(e):
                    zeige_dashboard()

                page.add(
                    ft.Container(height=50),
                    ft.Row([header], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=30),
                    ft.Text("Protokollierung", size=20, color="white", weight="bold", text_align=ft.TextAlign.CENTER),
                    ft.Container(height=30),
                    ft.Row([
                        ft.ElevatedButton(
                            "Neuen Tag starten", 
                            on_click=start_klick, 
                            bgcolor="red", 
                            color="white",
                            width=250,
                            height=60
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER)
                )
                page.update()
            except Exception as e:
                zeige_fehler(e)

        def zeige_dashboard():
            try:
                page.clean()
                page.bgcolor = "#003300"
                maerkte = lade_maerkte()

                page.add(nav_leiste())
                page.add(ft.Divider(color="transparent"))
                
                page.add(ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white"))
                
                if not maerkte:
                    page.add(ft.Text("Noch keine Märkte angelegt. Leg direkt los!", color="grey", size=16))
                else:
                    for index, markt in enumerate(maerkte):
                        # Falls noch ein altes Format gespeichert ist, fangen wir das hier ab!
                        anzeige_name = markt.get("adresse", "")
                        if anzeige_name == "":
                            anzeige_name = "Unbenannter Markt"

                        page.add(
                            ft.ElevatedButton(
                                f"Tour: {anzeige_name}", 
                                on_click=lambda e, i=index: zeige_maske(i),
                                width=300, height=50, bgcolor="#005500", color="white"
                            )
                        )

                page.add(
                    ft.Divider(color="white"),
                    ft.Row([ft.ElevatedButton("Tour voranlegen", on_click=lambda e: zeige_maske(None), bgcolor="red", color="white", height=50)], alignment=ft.MainAxisAlignment.CENTER)
                )
                page.update()
            except Exception as e:
                zeige_fehler(e)

        def zeige_maske(markt_index):
            try:
                page.clean()
                page.bgcolor = "#003300"
                maerkte = lade_maerkte()
                
                if markt_index is None:
                    aktuelle_daten = {"adresse": "", "marktnummer": "", "datum": "", "auftragsnummer": ""}
                else:
                    aktuelle_daten = maerkte[markt_index]

                untermenue = ft.Row(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.ElevatedButton("STAMMDATEN", bgcolor="red", color="white"),
                        ft.ElevatedButton("MESSWERTE (Bald)", bgcolor="grey", color="white", disabled=True),
                    ]
                )

                adresse_input = ft.TextField(label="1. Adresse Markt", value=aktuelle_daten.get("adresse", ""), color="white", border_color="white")
                marktnummer_input = ft.TextField(label="2. Marktnummer", value=aktuelle_daten.get("marktnummer", ""), color="white", border_color="white")
                datum_input = ft.TextField(label="3. Datum der Probenahme", value=aktuelle_daten.get("datum", ""), color="white", border_color="white")
                auftrag_input = ft.TextField(label="4. Auftragsnummer", value=aktuelle_daten.get("auftragsnummer", ""), color="white", border_color="white")

                def speichere_klick(e):
                    neue_daten = {
                        "adresse": adresse_input.value,
                        "marktnummer": marktnummer_input.value,
                        "datum": datum_input.value,
                        "auftragsnummer": auftrag_input.value
                    }
                    if markt_index is None:
                        maerkte.append(neue_daten)
                    else:
                        maerkte[markt_index] = neue_daten
                        
                    speichere_maerkte(maerkte)
                    zeige_dashboard()

                def zurueck_klick(e):
                    zeige_dashboard()

                button_reihe = [
                    ft.ElevatedButton("Speichern", on_click=speichere_klick, bgcolor="green", color="white"),
                    ft.ElevatedButton("Zurück", on_click=zurueck_klick, bgcolor="grey", color="white")
                ]

                if markt_index is not None:
                    def loeschen_klick(e):
                        maerkte.pop(markt_index)
                        speichere_maerkte(maerkte)
                        zeige_dashboard()
                    button_reihe.append(ft.ElevatedButton("Löschen", bgcolor="red", color="white", on_click=loeschen_klick))

                page.add(
                    untermenue,
                    ft.Divider(color="white"),
                    adresse_input, 
                    marktnummer_input, 
                    datum_input,
                    auftrag_input,
                    ft.Container(height=20),
                    ft.Row(button_reihe)
                )
                page.update()
            except Exception as e:
                zeige_fehler(e)

        def zeige_postausgang():
            try:
                page.clean()
                page.bgcolor = "#003300"
                page.add(nav_leiste())
                page.add(ft.Divider(color="transparent"))
                
                page.add(
                    ft.Text("Postausgang", size=25, weight="bold", color="white"),
                    ft.Text("Hier landen die fertigen PDFs.", color="grey"),
                    ft.Divider(color="white"),
                    
                    ft.ListTile(
                        leading=ft.Text("P", size=30, color="red"),
                        title=ft.Text("Protokoll.pdf", color="white"),
                        subtitle=ft.Text("Heute generiert - Bereit", color="grey")
                    )
                )
                page.update()
            except Exception as e:
                zeige_fehler(e)

        def zeige_archiv():
            try:
                page.clean()
                page.bgcolor = "#003300"
                page.add(nav_leiste())
                page.add(ft.Divider(color="transparent"))
                
                page.add(
                    ft.Text("Archiv", size=25, weight="bold", color="white"),
                    ft.Text("Tippe auf 'Bearbeiten', um Daten nachträglich zu ändern.", color="grey"),
                    ft.Divider(color="white"),
                    
                    ft.ListTile(
                        leading=ft.Text("A", size=30, color="green"),
                        title=ft.Text("Beispiel Filiale", color="white"),
                        subtitle=ft.Text("Abgeschlossen", color="grey"),
                        trailing=ft.ElevatedButton("Bearbeiten", bgcolor="grey", color="white")
                    )
                )
                page.update()
            except Exception as e:
                zeige_fehler(e)

        # START DER APP!
        zeige_startbildschirm()

    except Exception as e:
        zeige_fehler(e)

if __name__ == "__main__":
    ft.app(target=main)