import flet as ft
import traceback
import json
import os
import datetime
import shutil

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
        except: pass
        page.update()

    try:
        import pypdf
        from pypdf.generic import DictionaryObject, NameObject, ArrayObject

        # --- DATEI-MANAGEMENT ---
        SPEICHER_DATEI = "meine_monitoring_daten.json"
        BENUTZER_DATEI = "benutzer_daten.json"

        def lade_maerkte():
            if os.path.exists(SPEICHER_DATEI):
                with open(SPEICHER_DATEI, "r", encoding="utf-8") as d: return json.load(d)
            return []

        def speichere_maerkte(liste):
            with open(SPEICHER_DATEI, "w", encoding="utf-8") as d: json.dump(liste, d)

        def lade_benutzer():
            if os.path.exists(BENUTZER_DATEI):
                with open(BENUTZER_DATEI, "r", encoding="utf-8") as d:
                    daten = json.load(d)
                    return daten.get("vorname", ""), daten.get("zuname", "")
            return "", ""

        def speichere_benutzer(v, z):
            with open(BENUTZER_DATEI, "w", encoding="utf-8") as d: json.dump({"vorname": v, "zuname": z}, d)

        def nav_leiste():
            return ft.Container(bgcolor="#001100", padding=10, border_radius=10, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[ft.ElevatedButton("Märkte", on_click=lambda e: zeige_dashboard(), bgcolor="#004400", color="white"), ft.ElevatedButton("Senden", on_click=lambda e: zeige_postausgang(), bgcolor="#004400", color="white"), ft.ElevatedButton("Archiv", on_click=lambda e: zeige_archiv(), bgcolor="#004400", color="white")]))

        # --- SEITEN-LOGIK ---

        def zeige_startbildschirm():
            ansicht.controls.clear()
            header = ft.Text(spans=[ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=45)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=45))], text_align=ft.TextAlign.CENTER)
            v, z = lade_benutzer()
            
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", label_style=ft.TextStyle(color="white"), text_size=10, border_color="white", text_align=ft.TextAlign.CENTER)
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", label_style=ft.TextStyle(color="white"), text_size=10, border_color="white", text_align=ft.TextAlign.CENTER)
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value); zeige_dashboard()
            ansicht.controls.extend([ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(height=40), ft.Row([ft.ElevatedButton("Neuen Tag starten", on_click=start_klick, bgcolor="red", color="white", width=250, height=60)], alignment=ft.MainAxisAlignment.CENTER)])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Divider(color="transparent"))
            ansicht.controls.append(ft.Row([ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white")], alignment=ft.MainAxisAlignment.CENTER))
            if not maerkte:
                ansicht.controls.append(ft.Row([ft.Text("Noch keine Märkte angelegt.", color="grey", size=16)], alignment=ft.MainAxisAlignment.CENTER))
            else:
                def loesche_t(i): maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                for index, markt in enumerate(maerkte):
                    adr = markt.get("adresse", "").strip() or "Unbenannter Markt"
                    buchstabe = chr(65 + index) if index < 26 else str(index)
                    ansicht.controls.append(ft.Row([ft.ElevatedButton(f"Tour {buchstabe}: {adr}", on_click=lambda e, i=index: zeige_maske(i), expand=True, height=50, bgcolor="#005500", color="white"), ft.ElevatedButton("🗑️", on_click=lambda e, i=index: loesche_t(i), bgcolor="red", color="white", height=50, width=65)]))
            ansicht.controls.append(ft.Divider(color="white"))
            ansicht.controls.append(ft.Row([ft.ElevatedButton("Tour voranlegen", on_click=lambda e: zeige_maske(None), bgcolor="red", color="white", height=50)], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        def zeige_maske(markt_index):
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            v, z = lade_benutzer()
            heute = datetime.datetime.now()
            if markt_index is None:
                aktuelle_daten = {"adresse": "", "marktnummer": "", "auftragsnummer": "", "mitarbeiter_name": f"{v} {z}".strip(), "auftraggeber": "03509 - REWE Hackfleischmonitoring", "typ_probenahme": "Standard", "bemerkung": "", "tag": f"{heute.day:02d}", "monat": f"{heute.month:02d}", "jahr": str(heute.year)}
                titel = "Neue Tour anlegen"
            else:
                aktuelle_daten = maerkte[markt_index]
                titel = "Tour bearbeiten"

            stil_tf_gelb_10 = ft.TextStyle(color="yellow", size=10)
            stil_tf_gelb_12 = ft.TextStyle(color="yellow", size=12) # Neue Größe 12
            stil_label_weiss = ft.TextStyle(color="white")
            stil_label_rot_fett = ft.TextStyle(color="red", size=10, weight="bold")

            # Marktnummer & Auftragsnummer jetzt in Größe 12
            adr_in = ft.TextField(label="Adresse Markt", value=aktuelle_daten.get("adresse"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white", text_size=10)
            nr_in = ft.TextField(label="Marktnummer", value=aktuelle_daten.get("marktnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", text_size=12)
            auft_in = ft.TextField(label="Auftragsnummer", value=aktuelle_daten.get("auftragsnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", text_size=12)
            name_in = ft.TextField(label="Name Probenehmer", value=aktuelle_daten.get("mitarbeiter_name"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white", text_size=10)

            # --- BEMERKUNGS-WEICHE ---
            # Das Label heißt jetzt direkt "Zusätzliche Bemerkung" und sitzt auf dem Rahmen
            bem_in = ft.TextField(label="Zusätzliche Bemerkung", value=aktuelle_daten.get("bemerkung"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white", text_size=10, expand=1, visible=True)
            vor_dd = ft.Dropdown(label="Zusätzliche Bemerkung ▼", color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_rot_fett, expand=1, options=[ft.dropdown.Option("keine Fertiggerichte"), ft.dropdown.Option("keine Convinience heute"), ft.dropdown.Option("keine HFM heute"), ft.dropdown.Option("keine Convinience generell")], visible=False)

            def aktiviere_manuell(e):
                bem_in.visible = True; vor_dd.visible = False
                btn_manuell.bgcolor = "red"; btn_vorlage.bgcolor = "grey"
                page.update()

            def aktiviere_vorlage(e):
                bem_in.visible = False; vor_dd.visible = True
                btn_manuell.bgcolor = "grey"; btn_vorlage.bgcolor = "red"
                page.update()

            # Verkleinerte Buttons über ft.ButtonStyle (Kleine Schrift, wenig Padding)
            btn_manuell = ft.ElevatedButton("✍️ Selbst schreiben", on_click=aktiviere_manuell, bgcolor="red", color="white", height=30, style=ft.ButtonStyle(padding=5, text_style=ft.TextStyle(size=10)))
            btn_vorlage = ft.ElevatedButton("📋 Vorlage", on_click=aktiviere_vorlage, bgcolor="grey", color="white", height=30, style=ft.ButtonStyle(padding=5, text_style=ft.TextStyle(size=10)))

            # Buttons Links und Rechts ausgerichtet
            weiche_reihe = ft.Row([btn_manuell, btn_vorlage], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            bemerkungs_container = ft.Row([bem_in, vor_dd])

            ag_dd = ft.Dropdown(label="Auftraggeber ▼", value=aktuelle_daten.get("auftraggeber"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_rot_fett, options=[ft.dropdown.Option("03509 - REWE Hackfleischmonitoring"), ft.dropdown.Option("3001767 - REWE Dortmund (Hackfleischmonitoring)")])
            typ_dd = ft.Dropdown(label="Typ der Probenahme ▼", value=aktuelle_daten.get("typ_probenahme"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_rot_fett, options=[ft.dropdown.Option("Standard"), ft.dropdown.Option("Nachkontrolle"), ft.dropdown.Option("Mehrwöchig")])
            
            t_dd = ft.Dropdown(value=aktuelle_daten.get("tag"), width=90, color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_rot_fett, options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 32)])
            m_dd = ft.Dropdown(value=aktuelle_daten.get("monat"), width=90, color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_rot_fett, options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)])
            j_dd = ft.Dropdown(value=aktuelle_daten.get("jahr"), width=110, color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_rot_fett, options=[ft.dropdown.Option(str(i)) for i in range(heute.year - 1, heute.year + 2)])

            def pdf_speichern(e):
                try:
                    e.control.text = "Lädt..."; e.control.bgcolor = "blue"; page.update()
                    text_fuer_pdf = bem_in.value if bem_in.visible else vor_dd.value
                    ausg = os.path.join("assets", "stammdaten_fertig.pdf")
                    reader = pypdf.PdfReader(os.path.join("assets", "stammdaten.pdf"))
                    writer = pypdf.PdfWriter(clone_from=reader)
                    if "/AcroForm" not in writer.root_object: writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
                    if "/Fields" not in writer.root_object["/AcroForm"]: writer.root_object["/AcroForm"].update({NameObject("/Fields"): ArrayObject()})
                    f_map = {"tf_0000_00_ZS-001870": adr_in.value, "tf_0000_00_ZS-1408": nr_in.value, "tf_0000_00_ZS-002000": auft_in.value, "cal_templateLaborderprobenahmeDatum": f"{t_dd.value}.{m_dd.value}.{j_dd.value}", "dd_0000_00_ZS-002314": name_in.value, "dd_0000_00_ZS-1566": ag_dd.value, "dd_0000_00_ZS-002315": typ_dd.value, "dd_0000_00_ZS-001796": text_fuer_pdf}
                    writer.update_page_form_field_values(writer.pages[0], f_map)
                    with open(ausg, "wb") as f: writer.write(f)
                    e.control.text = "ERFOLG!"; e.control.bgcolor = "green"; page.update()
                except PermissionError:
                    page.overlay.append(ft.SnackBar(content=ft.Text("❌ Datei ist offen! Bitte stammdaten_fertig.pdf schließen.", color="white"), bgcolor="red", open=True))
                    e.control.text = "PDF offen!"; e.control.bgcolor = "red"; page.update()
                except Exception as ex: zeige_fehler(ex)

            save_btn = ft.ElevatedButton("Speichern", bgcolor="blue", color="white", height=35, style=ft.ButtonStyle(padding=2, text_style=ft.TextStyle(size=10, weight="bold")), expand=True)
            def save_klick(e):
                text_fuer_json = bem_in.value if bem_in.visible else vor_dd.value
                d = {"adresse": adr_in.value, "marktnummer": nr_in.value, "auftragsnummer": auft_in.value, "mitarbeiter_name": name_in.value, "auftraggeber": ag_dd.value, "typ_probenahme": typ_dd.value, "bemerkung": text_fuer_json, "tag": t_dd.value, "monat": m_dd.value, "jahr": j_dd.value}
                if markt_index is None: maerkte.append(d)
                else: maerkte[markt_index] = d
                speichere_maerkte(maerkte); save_btn.bgcolor = "green"; save_btn.text = "Gespeichert!"; page.update()
            save_btn.on_click = save_klick

            # AKTIONEN: In einer Zeile nebeneinander, mit expand=True quetschen sie sich automatisch passend!
            btn_touren = ft.ElevatedButton("Zu Touren", on_click=lambda e: zeige_dashboard(), bgcolor="#004400", color="white", height=35, style=ft.ButtonStyle(padding=2, text_style=ft.TextStyle(size=10, weight="bold")), expand=True)
            btn_pdf = ft.ElevatedButton("PDF eintragen", on_click=pdf_speichern, bgcolor="blue", color="white", height=35, style=ft.ButtonStyle(padding=2, text_style=ft.TextStyle(size=10, weight="bold")), expand=True)
            
            aktions_buttons = ft.Row([save_btn, btn_touren, btn_pdf], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=5)

            ansicht.controls.extend([
                ft.Row([ft.ElevatedButton("STAMMDATEN", bgcolor="red", color="white"), ft.ElevatedButton("1.HFM", bgcolor="grey", color="white")], scroll=ft.ScrollMode.HIDDEN),
                ft.Divider(color="white"), ft.Text(titel, size=20, weight="bold", color="white"),
                adr_in, nr_in, 
                ft.Text("Etikettennummer eingeben: XX-XXXXXX", color="red", size=10, weight="bold"),
                auft_in, ag_dd, name_in, typ_dd,
                weiche_reihe,
                bemerkungs_container,
                ft.Column([ft.Text("Datum der Probenahme", color="white", weight="bold"), ft.Row([t_dd, m_dd, j_dd])]),
                ft.Container(height=20),
                aktions_buttons
            ])
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear(); ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
            p_list = [f for f in os.listdir("assets") if f.endswith(".pdf") and f != "stammdaten.pdf"] if os.path.exists("assets") else []
            for pdf in p_list:
                def dl(e, d=pdf):
                    try:
                        z = "/storage/emulated/0/Download" if os.path.exists("/storage/emulated/0/Download") else os.path.join(os.path.expanduser("~"), "Downloads")
                        shutil.copyfile(os.path.join("assets", d), os.path.join(z, d))
                        s = ft.SnackBar(content=ft.Text(f"✅ {d} gespeichert!", color="white"), bgcolor="green", open=True)
                        page.overlay.append(s); e.control.text = "✅"; e.control.bgcolor = "green"; page.update()
                    except Exception as ex: zeige_fehler(ex)
                def rm(e, d=pdf): os.remove(os.path.join("assets", d)); zeige_postausgang()
                ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=10, content=ft.Row([ft.Text(pdf, color="white", size=10, expand=True), ft.ElevatedButton("💾", on_click=dl, bgcolor="blue"), ft.ElevatedButton("🗑️", on_click=rm, bgcolor="red")])))
            page.update()

        def zeige_archiv(): ansicht.controls.clear(); ansicht.controls.append(nav_leiste()); page.update()
        zeige_startbildschirm()
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": ft.app(target=main, assets_dir="assets")