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

    def get_rewe_paths():
        base_dl = "/storage/emulated/0/Download" if os.path.exists("/storage/emulated/0/Download") else os.path.join(os.path.expanduser("~"), "Downloads")
        rewe_dir = os.path.join(base_dl, "REWE")
        temp_dir = os.path.join(rewe_dir, "temp")
        heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
        final_dir = os.path.join(rewe_dir, heute_ordner)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_dir, exist_ok=True)
        return temp_dir, final_dir, heute_ordner

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

        SPEICHER_DATEI = "meine_monitoring_daten.json"
        BENUTZER_DATEI = "benutzer_daten.json"
        FAVORITEN_DATEI = "meine_favoriten.json"

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

        def lade_favoriten():
            if os.path.exists(FAVORITEN_DATEI):
                with open(FAVORITEN_DATEI, "r", encoding="utf-8") as d: return json.load(d)
            return {}

        def speichere_favoriten(daten):
            with open(FAVORITEN_DATEI, "w", encoding="utf-8") as d: json.dump(daten, d)

        def nav_leiste():
            return ft.Container(bgcolor="#001100", padding=10, border_radius=10, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[ft.ElevatedButton("Touren", on_click=lambda e: zeige_dashboard(), bgcolor="#004400", color="white"), ft.ElevatedButton("Senden", on_click=lambda e: zeige_postausgang(), bgcolor="#004400", color="white"), ft.ElevatedButton("Archiv", on_click=lambda e: zeige_archiv(), bgcolor="#004400", color="white")]))

        def zeige_startbildschirm():
            ansicht.controls.clear()
            header = ft.Text(spans=[ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=45)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=45))], text_align=ft.TextAlign.CENTER)
            v, z = lade_benutzer()
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", label_style=ft.TextStyle(color="white"), text_size=12, border_color="white", text_align=ft.TextAlign.CENTER)
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", label_style=ft.TextStyle(color="white"), text_size=12, border_color="white", text_align=ft.TextAlign.CENTER)
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value); zeige_dashboard()
            ansicht.controls.extend([ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.STRETCH), ft.Container(height=40), ft.Row([ft.ElevatedButton("Neuen Tag starten", on_click=start_klick, bgcolor="red", color="white", width=250, height=60)], alignment=ft.MainAxisAlignment.CENTER)])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Divider(color="transparent"))
            ansicht.controls.append(ft.Row([ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white")], alignment=ft.MainAxisAlignment.CENTER))
            if not maerkte:
                ansicht.controls.append(ft.Row([ft.Text("Noch keine Touren angelegt.", color="grey", size=16)], alignment=ft.MainAxisAlignment.CENTER))
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
            favs = lade_favoriten() # Lade Vorlage
            v, z = lade_benutzer()
            
            if markt_index is None:
                # Neue Tour -> Statische Daten aus Favoriten, dynamische Daten strikt LEER!
                aktuelle_daten = {
                    "adresse": "", "marktnummer": "", "auftragsnummer": "", "bemerkung": "",
                    "mitarbeiter_name": favs.get("mitarbeiter_name", f"{v} {z}".strip()), 
                    "auftraggeber": favs.get("auftraggeber", "03509 - REWE Hackfleischmonitoring"), 
                    "typ_probenahme": favs.get("typ_probenahme", "Standard"), 
                    "tw_zeit": "", "tw_temp": "", "tw_tempkonst": "", "tw_unterbau_l": "", "tw_auff_sonstiges": ""
                }
                for key, val in favs.items():
                    if (key.startswith("tw_") or key.startswith("cb_")) and key not in ["tw_zeit", "tw_temp", "tw_tempkonst", "tw_unterbau_l", "tw_auff_sonstiges", "tw_lims_override"]:
                        aktuelle_daten[key] = val
                titel = "Neue Tour anlegen"
            else:
                aktuelle_daten = maerkte[markt_index]
                titel = "Tour bearbeiten"

            stil_tf_gelb_10 = ft.TextStyle(color="yellow", size=10)
            stil_tf_gelb_12 = ft.TextStyle(color="yellow", size=12)
            stil_label_weiss = ft.TextStyle(color="white")
            stil_cb_weiss = ft.TextStyle(color="white", size=10)

            btn_tab_stamm = ft.ElevatedButton("STAMMDATEN", bgcolor="red", color="white")
            btn_tab_tw = ft.ElevatedButton("TRINKWASSER", bgcolor="grey", color="white")

            def wechsle_zu_stamm(e=None):
                stammdaten_spalte.visible = True; trinkwasser_spalte.visible = False
                btn_tab_stamm.bgcolor = "red"; btn_tab_tw.bgcolor = "grey"; page.update()

            def wechsle_zu_tw(e=None):
                stammdaten_spalte.visible = False; trinkwasser_spalte.visible = True
                btn_tab_stamm.bgcolor = "grey"; btn_tab_tw.bgcolor = "red"; page.update()

            btn_tab_stamm.on_click = wechsle_zu_stamm
            btn_tab_tw.on_click = wechsle_zu_tw

            # ==========================================
            # STAMMDATEN Felder
            # ==========================================
            adr_in = ft.TextField(label="Adresse Markt", value=aktuelle_daten.get("adresse"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white", text_size=10)
            nr_in = ft.TextField(label="Marktnummer", value=aktuelle_daten.get("marktnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", text_size=12)
            auft_in = ft.TextField(label="Auftragsnummer", hint_text="Etikettennummer: XX-XXXXXX", hint_style=ft.TextStyle(color="white54", size=10), value=aktuelle_daten.get("auftragsnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", text_size=12)
            name_in = ft.TextField(label="Name Probenehmer", value=aktuelle_daten.get("mitarbeiter_name"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white", text_size=10)
            
            bem_in = ft.TextField(label="Zusätzliche Bemerkung", value=aktuelle_daten.get("bemerkung"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white", text_size=10, expand=1, visible=True)
            vor_dd = ft.Dropdown(label="Zusätzliche Bemerkung ▼", color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, expand=1, options=[ft.dropdown.Option("keine Fertiggerichte"), ft.dropdown.Option("keine Convinience heute"), ft.dropdown.Option("keine HFM heute"), ft.dropdown.Option("keine Convinience generell")], visible=False)

            def aktiviere_manuell(e):
                bem_in.visible = True; vor_dd.visible = False; page.update()
            def aktiviere_vorlage(e):
                bem_in.visible = False; vor_dd.visible = True; page.update()

            btn_manuell = ft.ElevatedButton("✍️ Selbst schreiben", on_click=aktiviere_manuell, bgcolor="red", color="white", height=30, style=ft.ButtonStyle(padding=5, text_style=ft.TextStyle(size=10)))
            btn_vorlage = ft.ElevatedButton("📋 Vorlage", on_click=aktiviere_vorlage, bgcolor="grey", color="white", height=30, style=ft.ButtonStyle(padding=5, text_style=ft.TextStyle(size=10)))
            weiche_reihe = ft.Row([btn_manuell, btn_vorlage], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
            ag_dd = ft.Dropdown(label="Auftraggeber ▼", value=aktuelle_daten.get("auftraggeber"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("03509 - REWE Hackfleischmonitoring"), ft.dropdown.Option("3001767 - REWE Dortmund (Hackfleischmonitoring)")])
            typ_dd = ft.Dropdown(label="Typ der Probenahme ▼", value=aktuelle_daten.get("typ_probenahme"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("Standard"), ft.dropdown.Option("Nachkontrolle"), ft.dropdown.Option("Mehrwöchig")])
            
            stammdaten_spalte = ft.Column([adr_in, nr_in, auft_in, ag_dd, name_in, typ_dd, weiche_reihe, bem_in, vor_dd], horizontal_alignment=ft.CrossAxisAlignment.STRETCH, visible=True)

            # ==========================================
            # TRINKWASSER Felder & WÄCHTER
            # ==========================================
            tw_lims_warnung = ft.Text("⚠️ HINWEIS: Daten eingetragen, aber der Aktivierungs-Haken oben fehlt!", color="red", size=14, weight="bold", visible=False)
            tw_lims_override_cb = ft.Checkbox(label="Trotzdem ohne Aktivierung speichern", value=aktuelle_daten.get("tw_lims_override", False), label_style=ft.TextStyle(color="red", size=12, weight="bold"), fill_color="red", check_color="white", visible=False)

            def pruefe_lims_warnung(e=None):
                zeit_val = (tw_zeit_in.value or "").strip()
                temp_val = (tw_temp_in.value or "").strip()
                hat_daten = bool(zeit_val or temp_val)
                braucht_warnung = hat_daten and not tw_kalt_cb.value
                tw_lims_warnung.visible = braucht_warnung
                tw_lims_override_cb.visible = braucht_warnung
                if not braucht_warnung: tw_lims_override_cb.value = False 
                page.update()

            def format_zeit(e):
                val = e.control.value or ""
                zahlen = "".join([c for c in val if c.isdigit()])[:4]
                if len(zahlen) >= 3: e.control.value = zahlen[:2] + ":" + zahlen[2:]
                else: e.control.value = zahlen
                e.control.update(); pruefe_lims_warnung()

            def format_temp_blur(e):
                val = (e.control.value or "").strip().replace(" °C", "").replace("°C", "")
                if val: e.control.value = val + " °C"
                e.control.update(); pruefe_lims_warnung()

            # --- SEITE 2 FELDER ---
            tw_kalt_cb = ft.Checkbox(label="Trinkwasser kalt", value=aktuelle_daten.get("tw_kalt", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black", on_change=pruefe_lims_warnung)
            tw_zeit_in = ft.TextField(label="Probenahmezeit", value=aktuelle_daten.get("tw_zeit"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", on_change=format_zeit)
            tw_temp_in = ft.TextField(label="Probenahmetemperatur (nur Zahl tippen)", value=aktuelle_daten.get("tw_temp"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", on_blur=format_temp_blur)
            tw_desinf_dd = ft.Dropdown(label="Art der Desinfektion ▼", value=aktuelle_daten.get("tw_desinf", "Abflammen"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("Abflammen"), ft.dropdown.Option("Alkohol")])
            tw_zapf_dd = ft.Dropdown(label="Zapfstelle (TW) ▼", value=aktuelle_daten.get("tw_zapf", "Spülbecken"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("Spülbecken"), ft.dropdown.Option("Handwaschbecken")])
            
            cb_pn = ft.Checkbox(label="PN-Hahn", value=aktuelle_daten.get("tw_cb_pn", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_zwei = ft.Checkbox(label="Zweigriff-Mischarmatur", value=aktuelle_daten.get("tw_cb_zwei", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_sensor = ft.Checkbox(label="Sensor-Armatur", value=aktuelle_daten.get("tw_cb_sensor", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_knie = ft.Checkbox(label="Armatur mit Kniebestätigung", value=aktuelle_daten.get("tw_cb_knie", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_ein = ft.Checkbox(label="Einhebel-Mischarmatur", value=aktuelle_daten.get("tw_cb_ein", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_ein_g = ft.Checkbox(label="Eingriff-Armatur", value=aktuelle_daten.get("tw_cb_ein_g", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_eck = ft.Checkbox(label="Eckventil", value=aktuelle_daten.get("tw_cb_eck", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            tw_zapf_sonst_dd = ft.Dropdown(label="Sonstiges Zapfstelle ▼", value=aktuelle_daten.get("tw_zapf_sonst"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("Bitte wählen...")])

            # --- SEITE 3 FELDER ---
            tw_inaktiv_dd = ft.Dropdown(label="Inaktivierungsmittel ▼", value=aktuelle_daten.get("tw_inaktiv", "Na-Thiosulfat"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("Na-Thiosulfat")])
            kurz_opts = [ft.dropdown.Option("1 - nicht wahrnehmbar"), ft.dropdown.Option("2 - wahrnehmbar")]
            tw_kurz1_dd = ft.Dropdown(value=aktuelle_daten.get("tw_kurz1", "1 - nicht wahrnehmbar"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, text_size=10, expand=1, options=kurz_opts)
            tw_kurz2_dd = ft.Dropdown(value=aktuelle_daten.get("tw_kurz2", "1 - nicht wahrnehmbar"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, text_size=10, expand=1, options=kurz_opts)
            tw_kurz3_dd = ft.Dropdown(value=aktuelle_daten.get("tw_kurz3", "1 - nicht wahrnehmbar"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, text_size=10, expand=1, options=kurz_opts)
            tw_kurz4_dd = ft.Dropdown(value=aktuelle_daten.get("tw_kurz4", "1 - nicht wahrnehmbar"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, text_size=10, expand=1, options=kurz_opts)

            cb_auff_ja = ft.Checkbox(label="ja", value=aktuelle_daten.get("cb_auff_ja", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_nein = ft.Checkbox(label="nein", value=aktuelle_daten.get("cb_auff_nein", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_perl = ft.Checkbox(label="Perlator nicht entfernbar", value=aktuelle_daten.get("cb_auff_perl", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_verkalk = ft.Checkbox(label="Starke Verkalkung", value=aktuelle_daten.get("cb_auff_verkalk", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_verbrueh = ft.Checkbox(label="Armatur mit Verbrühschutz", value=aktuelle_daten.get("cb_auff_verbrueh", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_durchlauf = ft.Checkbox(label="Durchlauferhitzer", value=aktuelle_daten.get("cb_auff_durchlauf", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_unterbau = ft.Checkbox(label="Unterbauspeicher [L]", value=aktuelle_daten.get("cb_auff_unterbau", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            tw_unterbau_l_in = ft.TextField(value=aktuelle_daten.get("tw_unterbau_l"), width=50, height=35, color="yellow", text_style=stil_tf_gelb_10, border_color="white", content_padding=5)
            cb_auff_eck_zu = ft.Checkbox(label="Eckventil warm/kalt geschlossen", value=aktuelle_daten.get("cb_auff_eck_zu", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_nichtmoeglich = ft.Checkbox(label="nicht möglich", value=aktuelle_daten.get("cb_auff_nichtmoeglich", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_dusche = ft.Checkbox(label="Entnahme aus der Dusche", value=aktuelle_daten.get("cb_auff_dusche", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_handbrause = ft.Checkbox(label="Handbrause", value=aktuelle_daten.get("cb_auff_handbrause", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            cb_auff_sonst = ft.Checkbox(label="Sonstiges", value=aktuelle_daten.get("cb_auff_sonst", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            tw_auff_sonstiges_in = ft.TextField(label="Sonstiges (Auffälligkeiten)", value=aktuelle_daten.get("tw_auff_sonstiges"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white", text_size=10, multiline=True)

            # --- SEITE 4 FELDER ---
            tw_zweck_dd = ft.Dropdown(label="Zweck der PN ▼", value=aktuelle_daten.get("tw_zweck", "DIN EN ISO 19458 Zweck B"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("DIN EN ISO 19458 Zweck B"), ft.dropdown.Option("Zweck A"), ft.dropdown.Option("Zweck C")])
            tw_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("tw_inhalt", "ca. 500 ml"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", text_size=12)
            tw_verpackung_dd = ft.Dropdown(label="Verpackung ▼", value=aktuelle_daten.get("tw_verpackung", "500ml Kunststoff-Flasche mit Natriumthiosulfat"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("500ml Kunststoff-Flasche mit Natriumthiosulfat")])
            tw_entnahmeort_dd = ft.Dropdown(label="Entnahmeort ▼", value=aktuelle_daten.get("tw_entnahmeort", "Metzgerei"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("Metzgerei"), ft.dropdown.Option("Käsetheke"), ft.dropdown.Option("Fischtheke")])
            tw_tempkonst_in = ft.TextField(label="Temperaturkonstante (nur Zahl tippen)", value=aktuelle_daten.get("tw_tempkonst"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", on_blur=format_temp_blur)
            tw_bemerkung_dd = ft.Dropdown(label="Bemerkungen für Trinkwasser ▼", value=aktuelle_daten.get("tw_bemerkung", "Bitte eingeben"), color="yellow", border_color="white", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, options=[ft.dropdown.Option("Bitte eingeben"), ft.dropdown.Option("Keine Besonderheiten")])

            trinkwasser_spalte = ft.Column([
                tw_kalt_cb, tw_lims_warnung, tw_lims_override_cb, tw_zeit_in, tw_temp_in, tw_desinf_dd, tw_zapf_dd,
                ft.Text("Probenahmetechnik / Art der Zapfstelle:", color="white", weight="bold"),
                ft.Row([ft.Column([cb_pn, cb_zwei, cb_sensor, cb_knie], expand=1), ft.Column([cb_ein, cb_ein_g, cb_eck, ft.Container(height=30)], expand=1)], alignment=ft.MainAxisAlignment.START),
                tw_zapf_sonst_dd, ft.Divider(color="white"), ft.Text("Sensorik & Auffälligkeiten", color="white", size=16, weight="bold"), tw_inaktiv_dd,
                ft.Text("Kurzsensorik:", color="white", weight="bold"), ft.Row([tw_kurz1_dd, tw_kurz2_dd]), ft.Row([tw_kurz3_dd, tw_kurz4_dd]),
                ft.Text("Auffälligkeiten:", color="white", weight="bold"),
                ft.Row([ft.Column([cb_auff_ja, cb_auff_perl, cb_auff_verbrueh, ft.Row([cb_auff_unterbau, tw_unterbau_l_in]), cb_auff_nichtmoeglich, cb_auff_handbrause], expand=1), ft.Column([cb_auff_nein, cb_auff_verkalk, cb_auff_durchlauf, cb_auff_eck_zu, cb_auff_dusche, cb_auff_sonst], expand=1)], alignment=ft.MainAxisAlignment.START),
                tw_auff_sonstiges_in, ft.Divider(color="white"), ft.Text("Probenahmedetails", color="white", size=16, weight="bold"),
                tw_zweck_dd, tw_inhalt_in, tw_verpackung_dd, tw_entnahmeort_dd, tw_tempkonst_in, tw_bemerkung_dd
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH, visible=False)
            
            pruefe_lims_warnung()

            # ==========================================
            # BUTTON-LOGIK
            # ==========================================
            fehler_text = ft.Text("", color="red", size=14, weight="bold", visible=False)

            def check_pflichtfelder():
                if not (nr_in.value or "").strip() or not (auft_in.value or "").strip():
                    wechsle_zu_stamm(); fehler_text.value = "⚠️ FEHLER: Bitte Marktnummer und Auftragsnummer eingeben!"; fehler_text.visible = True; page.update(); return False
                if bool((tw_zeit_in.value or "").strip() or (tw_temp_in.value or "").strip()) and not tw_kalt_cb.value and not tw_lims_override_cb.value:
                    wechsle_zu_tw(); fehler_text.value = "⚠️ FEHLER: Bitte Aktivierungs-Haken setzen oder Ausnahme bestätigen!"; fehler_text.visible = True; page.update(); return False
                fehler_text.visible = False; return True

            def hole_aktuelle_masken_daten():
                return {
                    "adresse": adr_in.value, "marktnummer": nr_in.value, "auftragsnummer": auft_in.value, "mitarbeiter_name": name_in.value, "auftraggeber": ag_dd.value, "typ_probenahme": typ_dd.value, "bemerkung": (bem_in.value if bem_in.visible else vor_dd.value),
                    "tw_kalt": tw_kalt_cb.value, "tw_lims_override": tw_lims_override_cb.value, "tw_zeit": tw_zeit_in.value, "tw_temp": tw_temp_in.value, "tw_desinf": tw_desinf_dd.value, "tw_zapf": tw_zapf_dd.value,
                    "tw_cb_pn": cb_pn.value, "tw_cb_zwei": cb_zwei.value, "tw_cb_sensor": cb_sensor.value, "tw_cb_knie": cb_knie.value, "tw_cb_ein": cb_ein.value, "tw_cb_ein_g": cb_ein_g.value, "tw_cb_eck": cb_eck.value, "tw_zapf_sonst": tw_zapf_sonst_dd.value,
                    "tw_inaktiv": tw_inaktiv_dd.value, "tw_kurz1": tw_kurz1_dd.value, "tw_kurz2": tw_kurz2_dd.value, "tw_kurz3": tw_kurz3_dd.value, "tw_kurz4": tw_kurz4_dd.value,
                    "cb_auff_ja": cb_auff_ja.value, "cb_auff_nein": cb_auff_nein.value, "cb_auff_perl": cb_auff_perl.value, "cb_auff_verkalk": cb_auff_verkalk.value, "cb_auff_verbrueh": cb_auff_verbrueh.value, "cb_auff_durchlauf": cb_auff_durchlauf.value,
                    "cb_auff_unterbau": cb_auff_unterbau.value, "tw_unterbau_l": tw_unterbau_l_in.value, "cb_auff_eck_zu": cb_auff_eck_zu.value, "cb_auff_nichtmoeglich": cb_auff_nichtmoeglich.value, "cb_auff_dusche": cb_auff_dusche.value, "cb_auff_handbrause": cb_auff_handbrause.value, "cb_auff_sonst": cb_auff_sonst.value, "tw_auff_sonstiges": tw_auff_sonstiges_in.value,
                    "tw_zweck": tw_zweck_dd.value, "tw_inhalt": tw_inhalt_in.value, "tw_verpackung": tw_verpackung_dd.value, "tw_entnahmeort": tw_entnahmeort_dd.value, "tw_tempkonst": tw_tempkonst_in.value, "tw_bemerkung": tw_bemerkung_dd.value
                }

            def fav_speichern_klick(e):
                d = hole_aktuelle_masken_daten()
                # DIE SCHWARZE LISTE: Alles, was hier steht, wird IGNORIERT!
                ignore = ["adresse", "marktnummer", "auftragsnummer", "bemerkung", "tw_zeit", "tw_temp", "tw_tempkonst", "tw_lims_override", "tw_unterbau_l", "tw_auff_sonstiges"]
                fav_daten = {k: v for k, v in d.items() if k not in ignore}
                speichere_favoriten(fav_daten)
                e.control.text = "✅ Favorit gemerkt!"; e.control.bgcolor = "orange"; page.update()

            def save_klick(e):
                if not check_pflichtfelder(): return 
                d = hole_aktuelle_masken_daten()
                if markt_index is None: maerkte.append(d)
                else: maerkte[markt_index] = d
                speichere_maerkte(maerkte); e.control.bgcolor = "green"; e.control.text = "✅ Gespeichert!"; page.update()

            def pdf_speichern_klick(e):
                if not check_pflichtfelder(): return 
                try:
                    e.control.text = "Lädt..."; page.update()
                    d = hole_aktuelle_masken_daten()
                    temp_dir, final_dir, heute_ordner = get_rewe_paths()
                    sicherer_markt = "".join([c for c in (nr_in.value or "") if c.isalnum()])
                    heute = datetime.datetime.now()
                    final_ausg = os.path.join(final_dir, f"REWE_{sicherer_markt}_{heute.strftime('%d%m%y')}.pdf")
                    wird_akt = os.path.exists(final_ausg)
                    
                    reader = pypdf.PdfReader(os.path.join("assets", "stammdaten.pdf"))
                    writer = pypdf.PdfWriter(clone_from=reader)
                    f_map = {"tf_0000_00_ZS-001870": d["adresse"], "tf_0000_00_ZS-1408": d["marktnummer"], "tf_0000_00_ZS-002000": d["auftragsnummer"], "cal_templateLaborderprobenahmeDatum": heute.strftime("%d.%m.%Y"), "dd_0000_00_ZS-002314": d["mitarbeiter_name"], "dd_0000_00_ZS-1566": d["auftraggeber"], "dd_0000_00_ZS-002315": d["typ_probenahme"], "dd_0000_00_ZS-001796": d["bemerkung"]}
                    if "/AcroForm" not in writer.root_object: writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
                    writer.update_page_form_field_values(writer.pages[0], f_map)
                    with open(final_ausg, "wb") as f: writer.write(f)
                    e.control.text = "✅ AKTUALISIERT!" if wird_akt else "✅ ERFOLG!"; e.control.bgcolor = "green"; page.update()
                except Exception as ex: zeige_fehler(ex)

            # --- UI ZUSAMMENBAU ---
            btn_fav = ft.ElevatedButton("⭐ Als Favorit merken", on_click=fav_speichern_klick, bgcolor="orange", color="black", height=35, expand=True)
            save_btn = ft.ElevatedButton("Speichern", on_click=save_klick, bgcolor="blue", color="white", height=35, expand=True)
            btn_touren = ft.ElevatedButton("Zu Touren", on_click=lambda e: zeige_dashboard(), bgcolor="#004400", color="white", height=35, expand=True)
            btn_pdf = ft.ElevatedButton("Bericht erstellen", on_click=pdf_speichern_klick, bgcolor="blue", color="white", height=35, expand=True)
            
            ansicht.controls.extend([
                ft.Row([btn_tab_stamm, btn_tab_tw], scroll=ft.ScrollMode.HIDDEN),
                ft.Divider(color="white"), ft.Text(titel, size=20, weight="bold", color="white"),
                stammdaten_spalte, trinkwasser_spalte,
                ft.Container(height=20),
                fehler_text,
                ft.Row([save_btn, btn_touren, btn_pdf], spacing=5),
                ft.Row([btn_fav]) 
            ])
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear(); ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
            temp_dir, final_dir, heute_ordner = get_rewe_paths()
            ansicht.controls.append(ft.Text(spans=[ft.TextSpan("Berichte liegen in: ", ft.TextStyle(color="red")), ft.TextSpan(f"Downloads/REWE/{heute_ordner}/", ft.TextStyle(color="red", weight="bold"))]))
            p_list = [f for f in os.listdir(final_dir) if f.endswith(".pdf")] if os.path.exists(final_dir) else []
            for pdf in p_list:
                def rm(e, d=pdf): os.remove(os.path.join(final_dir, d)); zeige_postausgang()
                ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=10, content=ft.Row([ft.Text(pdf, color="white", size=10, expand=True), ft.ElevatedButton("🗑️", on_click=rm, bgcolor="red")])))
            page.update()

        def zeige_archiv(): ansicht.controls.clear(); ansicht.controls.append(nav_leiste()); page.update()
        zeige_startbildschirm()
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": ft.app(target=main, assets_dir="assets")