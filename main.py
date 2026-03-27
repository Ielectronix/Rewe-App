import flet as ft
import traceback
import json
import os
import datetime

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

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
        # DATEI-TRESORE
        # =========================================================
        SPEICHER_DATEI = "meine_monitoring_daten.json"
        BENUTZER_DATEI = "benutzer_daten.json"

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

        def lade_benutzer():
            try:
                if os.path.exists(BENUTZER_DATEI):
                    with open(BENUTZER_DATEI, "r", encoding="utf-8") as datei:
                        daten = json.load(datei)
                        return daten.get("vorname", ""), daten.get("zuname", "")
                return "", ""
            except:
                return "", ""

        def speichere_benutzer(vorname, zuname):
            try:
                with open(BENUTZER_DATEI, "w", encoding="utf-8") as datei:
                    json.dump({"vorname": vorname, "zuname": zuname}, datei)
            except:
                pass

        # =========================================================
        # HAUPT-NAVIGATION
        # =========================================================
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
                
                # STARTSEITE: Label normal, Text Größe 10
                label_stil_normal = ft.TextStyle(color="white")
                text_stil_10 = ft.TextStyle(color="white", size=10)
                gespeicherter_vorname, gespeicherter_zuname = lade_benutzer()
                
                vorname_input = ft.TextField(
                    label="Vorname",
                    value=gespeicherter_vorname, 
                    color="white", text_style=text_stil_10, label_style=label_stil_normal, 
                    border_color="white", cursor_color="white",
                    text_align=ft.TextAlign.CENTER,
                    text_size=10
                )
                
                zuname_input = ft.TextField(
                    label="Nachname",
                    value=gespeicherter_zuname, 
                    color="white", text_style=text_stil_10, label_style=label_stil_normal, 
                    border_color="white", cursor_color="white",
                    text_align=ft.TextAlign.CENTER,
                    text_size=10
                )

                def start_klick(e):
                    speichere_benutzer(vorname_input.value, zuname_input.value)
                    zeige_dashboard()
                
                ansicht.controls.append(ft.Container(height=50))
                ansicht.controls.append(ft.Row([header], alignment=ft.MainAxisAlignment.CENTER))
                ansicht.controls.append(ft.Container(height=40)) 
                
                eingabe_spalte = ft.Column(
                    controls=[vorname_input, zuname_input],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
                ansicht.controls.append(eingabe_spalte)
                
                ansicht.controls.append(ft.Container(height=40)) 
                
                ansicht.controls.append(
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
                ansicht.controls.clear()
                maerkte = lade_maerkte()

                ansicht.controls.append(nav_leiste())
                ansicht.controls.append(ft.Divider(color="transparent"))
                ansicht.controls.append(ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white"))
                
                if not maerkte:
                    ansicht.controls.append(ft.Text("Noch keine Märkte angelegt. Leg direkt los!", color="grey", size=16))
                else:
                    def loesche_tour_direkt(index_zum_loeschen):
                        maerkte.pop(index_zum_loeschen)
                        speichere_maerkte(maerkte)
                        zeige_dashboard()

                    for index, markt in enumerate(maerkte):
                        anzeige_name = markt.get("adresse", "")
                        if anzeige_name == "":
                            anzeige_name = "Unbenannter Markt"

                        ansicht.controls.append(
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        f"Tour: {anzeige_name}", 
                                        on_click=lambda e, i=index: zeige_maske(i),
                                        expand=True, height=50, bgcolor="#005500", color="white"
                                    ),
                                    ft.ElevatedButton(
                                        "🗑️", 
                                        on_click=lambda e, i=index: loesche_tour_direkt(i),
                                        bgcolor="red", color="white", height=50, width=65
                                    )
                                ]
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
        # 4. DIE TOUR-MASKE 
        # =========================================================
        def zeige_maske(markt_index):
            try:
                ansicht.controls.clear()
                maerkte = lade_maerkte()
                
                gespeicherter_vorname, gespeicherter_zuname = lade_benutzer()
                voller_name = f"{gespeicherter_vorname} {gespeicherter_zuname}".strip()
                
                heute = datetime.datetime.now()
                aktueller_tag = f"{heute.day:02d}"
                aktueller_monat = f"{heute.month:02d}"
                aktuelles_jahr = str(heute.year)
                
                tag_wert = aktueller_tag
                monat_wert = aktueller_monat
                jahr_wert = aktuelles_jahr
                
                if markt_index is None:
                    aktuelle_daten = {
                        "adresse": "", 
                        "marktnummer": "", 
                        "auftragsnummer": "", 
                        "mitarbeiter_name": voller_name,
                        "auftraggeber": "03509 - REWE Hackfleischmonitoring"
                    }
                    titel = "Neue Tour anlegen"
                else:
                    aktuelle_daten = maerkte[markt_index]
                    titel = "Tour bearbeiten"
                    
                    gespeichertes_datum = aktuelle_daten.get("datum", "")
                    if gespeichertes_datum:
                        teile = gespeichertes_datum.split(".")
                        if len(teile) == 3 and teile[0].isdigit() and teile[1].isdigit() and teile[2].isdigit():
                            tag_wert = f"{int(teile[0]):02d}"
                            monat_wert = f"{int(teile[1]):02d}"
                            jahr_wert = str(int(teile[2]))

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

                # =========================================================
                # STILE: Labels wieder groß, Text 10, Dropdown 9
                # =========================================================
                label_stil_normal = ft.TextStyle(color="white") # Keine Größe = Standard/Normalgroß
                text_stil_10 = ft.TextStyle(color="white", size=10)
                text_stil_9 = ft.TextStyle(color="white", size=9)
                
                # Hier ist der weiße Schatten (Rand) um den roten Dropdown-Text
                weisser_rand_effekt = ft.Shadow(blur_radius=3, color="white", offset=ft.Offset(0, 0))
                roter_stil_label = ft.TextStyle(color="red", size=9, weight="bold", shadow=weisser_rand_effekt)

                adresse_input = ft.TextField(
                    label="Adresse Markt", value=aktuelle_daten.get("adresse", ""), 
                    color="white", text_style=text_stil_10, label_style=label_stil_normal, 
                    border_color="white", cursor_color="white", text_size=10
                )
                marktnummer_input = ft.TextField(
                    label="Marktnummer", value=aktuelle_daten.get("marktnummer", ""), 
                    color="white", text_style=text_stil_10, label_style=label_stil_normal, 
                    border_color="white", cursor_color="white", text_size=10
                )
                
                auftragsnummer_hinweis = ft.Text(
                    "Etikettennummer eingeben: XX-XXXXXX", 
                    color="red", 
                    size=12, # Hinweis in lesbarer Größe
                    weight="bold"
                )
                
                auftrag_input = ft.TextField(
                    label="Auftragsnummer", value=aktuelle_daten.get("auftragsnummer", ""), 
                    color="white", text_style=text_stil_10, label_style=label_stil_normal, 
                    border_color="white", cursor_color="white", text_size=10
                )
                
                name_input = ft.TextField(
                    label="Name", value=aktuelle_daten.get("mitarbeiter_name", voller_name), 
                    color="white", text_style=text_stil_10, label_style=label_stil_normal, 
                    border_color="white", cursor_cursor="white", text_size=10
                )

                # =========================================================
                # AUFTRAGGEBER-DROPDOWN
                # =========================================================
                auftraggeber_dd = ft.Dropdown(
                    label="Auftraggeber (Hier auswählen ▼)", 
                    value=aktuelle_daten.get("auftraggeber", "03509 - REWE Hackfleischmonitoring"),
                    color="white", border_color="white", text_style=text_stil_9, 
                    label_style=roter_stil_label, # Roter Text, Größe 9, weißer Rand!
                    text_size=9,
                    options=[
                        ft.dropdown.Option(
                            key="03509 - REWE Hackfleischmonitoring", 
                            text="03509 - REWE Hackfleischmonitoring"
                        ),
                        ft.dropdown.Option(
                            key="3001767 - REWE Dortmund (Hackfleischmonitoring)", 
                            text="3001767 - REWE Dortmund (Hackfleischmonitoring)"
                        )
                    ]
                )

                # =========================================================
                # DATUMSWÄHLER (Eingabe: 10, Labels: Normal)
                # =========================================================
                tag_dd = ft.Dropdown(
                    label="Tag", value=tag_wert, width=90, 
                    color="white", border_color="white", text_style=text_stil_10, label_style=label_stil_normal,
                    text_size=10, content_padding=10, 
                    options=[ft.dropdown.Option(key=f"{i:02d}", text=f"{i:02d}") for i in range(1, 32)]
                )
                monat_dd = ft.Dropdown(
                    label="Monat", value=monat_wert, width=90, 
                    color="white", border_color="white", text_style=text_stil_10, label_style=label_stil_normal,
                    text_size=10, content_padding=10, 
                    options=[ft.dropdown.Option(key=f"{i:02d}", text=f"{i:02d}") for i in range(1, 13)]
                )
                jahr_dd = ft.Dropdown(
                    label="Jahr", value=jahr_wert, width=110, 
                    color="white", border_color="white", text_style=text_stil_10, label_style=label_stil_normal,
                    text_size=10, content_padding=10, 
                    options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(heute.year - 1, heute.year + 5)]
                )

                datum_zeile = ft.Column(
                    controls=[
                        ft.Text("Datum der Probenahme", color="white", weight="bold", size=16), # Normale, gut lesbare Größe
                        ft.Row([tag_dd, monat_dd, jahr_dd])
                    ]
                )

                def speichere_klick(e):
                    zusammengesetztes_datum = f"{tag_dd.value}.{monat_dd.value}.{jahr_dd.value}"
                    
                    neue_daten = {
                        "adresse": adresse_input.value,
                        "marktnummer": marktnummer_input.value,
                        "datum": zusammengesetztes_datum,
                        "auftragsnummer": auftrag_input.value,
                        "mitarbeiter_name": name_input.value,
                        "auftraggeber": auftraggeber_dd.value 
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

                ansicht.controls.append(untermenue)
                ansicht.controls.append(ft.Divider(color="white"))
                ansicht.controls.append(ft.Text(titel, size=20, weight="bold", color="white"))
                ansicht.controls.append(adresse_input)
                ansicht.controls.append(marktnummer_input)
                ansicht.controls.append(auftragsnummer_hinweis) 
                ansicht.controls.append(auftrag_input)
                ansicht.controls.append(auftraggeber_dd) 
                ansicht.controls.append(name_input)
                ansicht.controls.append(datum_zeile) 
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