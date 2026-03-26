import flet as ft
import traceback
import json
import os
import datetime # NEU: Für das automatische Datum

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # =========================================================
    # KALENDER-WERKZEUG (Unsichtbar im Hintergrund laden)
    # =========================================================
    page.date_picker = ft.DatePicker()
    page.overlay.append(page.date_picker)

    # =========================================================
    # DER CONTAINER-TRICK
    # =========================================================
    ansicht = ft.Column(expand=True)
    page.add(ansicht)

    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("FEHLER GEFUNDEN:", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=20))
        try:
            ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=12))
        except:
            pass
        page.update()

    try:
        import pypdf

        # =========================================================
        # DATEI-TRESOR
        # =========================================================
        SPEICHER_DATEI = "meine_monitoring_daten.json"

        def lade_maerkte():
            try:
                if os.path.exists(SPEICHER_DATEI):
                    with open(SPEICHER_DATEI, "r", encoding="utf-8") as datei:
                        return json.load(datei)
                return []
            except Exception as e:
                return []

        def speichere_maerkte(maerkte_liste):
            try:
                with open(SPEICHER_DATEI, "w", encoding="utf-8") as datei:
                    json.dump(maerkte_liste, datei)
            except:
                pass

        # 3. HAUPT-NAVIGATION
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
                ansicht.controls.clear()
                
                header = ft.Text(
                    spans=[
                        ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=45)),
                        ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=45)),
                    ], text_align=ft.TextAlign.CENTER
                )
                
                ansicht.controls.append(ft.Container(height=50))
                ansicht.controls.append(ft.Row([header], alignment=ft.MainAxisAlignment.CENTER))
                ansicht.controls.append(ft.Container(height=60)) 
                
                ansicht.controls.append(
                    ft.Row([
                        ft.ElevatedButton(
                            "Neuen Tag starten", 
                            on_click=lambda e: zeige_dashboard(), 
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
                ansicht.controls.clear()
                maerkte = lade_maerkte()

                ansicht.controls.append(nav_leiste())
                ansicht.controls.append(ft.Divider(color="transparent"))
                ansicht.controls.append(ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white"))
                
                if not maerkte:
                    ansicht.controls.append(ft.Text("Noch keine Märkte angelegt. Leg direkt los!", color="grey", size=16))
                else:
                    for index, markt in enumerate(maerkte):
                        anzeige_name = markt.get("adresse", "")
                        if anzeige_name == "":
                            anzeige_name = "Unbenannter Markt"

                        ansicht.controls.append(
                            ft.ElevatedButton(
                                f"Tour: {anzeige_name}", 
                                on_click=lambda e, i=index: zeige_maske(i),
                                width=300, height=50, bgcolor="#005500", color="white"
                            )
                        )

                ansicht.controls.append(ft.Divider(color="white"))
                ansicht.controls.append(
                    ft.Row([ft.ElevatedButton("Tour voranlegen", on_click=lambda e: zeige_maske(None), bgcolor="red", color="white", height=50)], alignment=ft.MainAxisAlignment.CENTER)
                )
                page.update()
            except Exception as e:
                zeige_fehler(e)

        # =========================================================
        # 4. DIE TOUR-MASKE (Stammdaten)
        # =========================================================
        def zeige_maske(markt_index):
            try:
                ansicht.controls.clear()
                maerkte = lade_maerkte()
                
                # Wir holen uns das exakte heutige Datum
                heute_str = datetime.datetime.now().strftime("%d.%m.%Y")
                
                if markt_index is None:
                    # BEHOBEN: Setzt beim Neu-Anlegen automatisch das heutige Datum ein!
                    aktuelle_daten = {"adresse": "", "marktnummer": "", "datum": heute_str, "auftragsnummer": ""}
                    titel = "Neue Tour anlegen"
                else:
                    aktuelle_daten = maerkte[markt_index]
                    # Falls alte Daten kein Datum haben, füllen wir es auf
                    if not aktuelle_daten.get("datum"):
                        aktuelle_daten["datum"] = heute_str
                    titel = "Tour bearbeiten"

                # --- BEHOBEN: HIDDEN lässt das Menü scrollen, ohne die hässliche Linie zu zeigen! ---
                untermenue = ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    scroll=ft.ScrollMode.HIDDEN, 
                    controls=[
                        ft.ElevatedButton("STAMMDATEN", bgcolor="red", color="white"),
                        ft.ElevatedButton("1.HFM", bgcolor="grey", color="white"),
                        ft.ElevatedButton("OKZ -HFM", bgcolor="grey", color="white"),
                        ft.ElevatedButton("3. OG", bgcolor="grey", color="white"),
                        ft.ElevatedButton("4. OKZ-OG", bgcolor="grey", color="white"),
                        ft.ElevatedButton("5. TW", bgcolor="grey", color="white"),
                        ft.ElevatedButton("6. Scherbeneis", bgcolor="grey", color="white"),
                    ]
                )

                # --- BEHOBEN: Text-Styling ist jetzt absolut auf "Weiß" gezwungen ---
                weisser_stil = ft.TextStyle(color="white")

                adresse_input = ft.TextField(
                    label="1. Adresse Markt", value=aktuelle_daten.get("adresse", ""), 
                    color="white", text_style=weisser_stil, label_style=weisser_stil, border_color="white", cursor_color="white"
                )
                marktnummer_input = ft.TextField(
                    label="2. Marktnummer", value=aktuelle_daten.get("marktnummer", ""), 
                    color="white", text_style=weisser_stil, label_style=weisser_stil, border_color="white", cursor_color="white"
                )
                auftrag_input = ft.TextField(
                    label="4. Auftragsnummer", value=aktuelle_daten.get("auftragsnummer", ""), 
                    color="white", text_style=weisser_stil, label_style=weisser_stil, border_color="white", cursor_color="white"
                )

                # --- DER NEUE KALENDER (Date Picker) ---
                datum_input = ft.TextField(
                    label="3. Datum der Probenahme", value=aktuelle_daten.get("datum", ""), 
                    color="white", text_style=weisser_stil, label_style=weisser_stil, border_color="white", 
                    expand=True # Macht das Feld so breit wie möglich
                )
                
                def datum_gewaehlt(e):
                    if page.date_picker.value:
                        # Schreibt das ausgewählte Datum im Format TT.MM.JJJJ in das Textfeld
                        datum_input.value = page.date_picker.value.strftime("%d.%m.%Y")
                        page.update()

                page.date_picker.on_change = datum_gewaehlt

                # Ein kleiner Button neben dem Feld, der den Kalender öffnet
                datum_zeile = ft.Row([
                    datum_input,
                    ft.ElevatedButton("📅", on_click=lambda e: page.date_picker.pick_date(), bgcolor="grey", color="white")
                ])

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

                button_reihe = [
                    ft.ElevatedButton("Speichern", on_click=speichere_klick, bgcolor="green", color="white"),
                    ft.ElevatedButton("Zurück", on_click=lambda e: zeige_dashboard(), bgcolor="grey", color="white")
                ]

                if markt_index is not None:
                    def loeschen_klick(e):
                        maerkte.pop(markt_index)
                        speichere_maerkte(maerkte)
                        zeige_dashboard()
                    button_reihe.append(ft.ElevatedButton("Löschen", bgcolor="red", color="white", on_click=loeschen_klick))

                ansicht.controls.append(untermenue)
                ansicht.controls.append(ft.Divider(color="white"))
                ansicht.controls.append(ft.Text(titel, size=20, weight="bold", color="white"))
                ansicht.controls.append(adresse_input)
                ansicht.controls.append(marktnummer_input)
                ansicht.controls.append(datum_zeile) # Die Zeile mit dem Feld und dem Kalender-Button
                ansicht.controls.append(auftrag_input)
                ansicht.controls.append(ft.Container(height=20))
                ansicht.controls.append(ft.Row(button_reihe))
                page.update()
            except Exception as e:
                zeige_fehler(e)

        # ---------------- RESTLICHE SEITEN ----------------

        def zeige_postausgang():
            try:
                ansicht.controls.clear()
                ansicht.controls.append(nav_leiste())
                ansicht.controls.append(ft.Divider(color="transparent"))
                
                ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
                ansicht.controls.append(ft.Text("Hier landen die fertigen PDFs.", color="grey"))
                ansicht.controls.append(ft.Divider(color="white"))
                
                ansicht.controls.append(
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
                ansicht.controls.clear()
                ansicht.controls.append(nav_leiste())
                ansicht.controls.append(ft.Divider(color="transparent"))
                
                ansicht.controls.append(ft.Text("Archiv", size=25, weight="bold", color="white"))
                ansicht.controls.append(ft.Text("Tippe auf 'Bearbeiten', um Daten nachträglich zu ändern.", color="grey"))
                ansicht.controls.append(ft.Divider(color="white"))
                
                ansicht.controls.append(
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