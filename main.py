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
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=30, weight="bold"))
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
        VORLAGEN_DATEI = "tour_vorlagen.json"

        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold"),
                on_click=on_click,
                bgcolor=bgcolor,
                color=color,
                expand=expand,
                height=height,
                width=width
            )

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

        def lade_vorlagen():
            if os.path.exists(VORLAGEN_DATEI):
                with open(VORLAGEN_DATEI, "r", encoding="utf-8") as d: return json.load(d)
            return {}

        def speichere_vorlagen(daten):
            with open(VORLAGEN_DATEI, "w", encoding="utf-8") as d: json.dump(daten, d)

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=10, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("Touren", lambda e: zeige_dashboard(), "#004400", "white"),
                    sicherer_button("Senden", lambda e: zeige_postausgang(), "#004400", "white"),
                    sicherer_button("Archiv", lambda e: zeige_archiv(), "#004400", "white")
                ])
            )

        def zeige_startbildschirm():
            ansicht.controls.clear()
            header = ft.Text(spans=[ft.TextSpan("Rewe ", ft.TextStyle(color="red", weight="bold", size=45)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=45))], text_align=ft.TextAlign.CENTER)
            v, z = lade_benutzer()
            
            stil_label_weiss = ft.TextStyle(color="white")
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value); zeige_dashboard()
                
            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            
            ansicht.controls.extend([
                ft.Container(height=50), 
                ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), 
                ft.Container(height=40), 
                ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER), 
                ft.Container(height=40), 
                ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)
            ])
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
                for index, markt in enumerate(maerkte):
                    adr = markt.get("adresse", "").strip() or "Unbenannter Markt"
                    buchstabe = chr(65 + index) if index < 26 else str(index)
                    def loesche_t(e, i=index): maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    btn_tour = sicherer_button(f"Tour {buchstabe}: {adr}", lambda e, i=index: zeige_maske(i), "#005500", "white", expand=True, height=50)
                    btn_del = sicherer_button("🗑️", loesche_t, "red", "white", height=50, width=65)
                    ansicht.controls.append(ft.Row([btn_tour, btn_del]))
                    
            ansicht.controls.append(ft.Divider(color="white"))
            btn_neu = sicherer_button("Tour voranlegen", lambda e: zeige_maske(None), "red", "white", height=50)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        def zeige_maske(markt_index):
            try:
                ansicht.controls.clear()
                maerkte = lade_maerkte()
                v, z = lade_benutzer()
                
                if markt_index is None:
                    aktuelle_daten = {"adresse": "", "marktnummer": "", "auftragsnummer": "", "mitarbeiter_name": f"{v} {z}".strip(), "auftraggeber": "03509 - REWE Hackfleischmonitoring", "typ_probenahme": "Standard", "bemerkung": ""}
                    titel = "Neue Tour anlegen"
                else:
                    aktuelle_daten = maerkte[markt_index]
                    titel = "Tour bearbeiten"

                stil_tf_gelb_10 = ft.TextStyle(color="yellow", size=10)
                stil_tf_gelb_12 = ft.TextStyle(color="yellow", size=12)
                stil_label_weiss = ft.TextStyle(color="white")
                stil_cb_weiss = ft.TextStyle(color="white", size=10)

                def erstelle_combo(label_text, wert, optionen, groesse=10, ausdehnbar=False):
                    combo = ft.TextField(label=label_text, value=wert, color="yellow", text_style=ft.TextStyle(size=groesse), label_style=stil_label_weiss, border_color="white", expand=ausdehnbar, content_padding=10)
                    items = []
                    for opt in optionen:
                        def erstelle_klick(txt):
                            def klick(e):
                                combo.value = txt
                                combo.update()
                            return klick
                        items.append(ft.PopupMenuItem(content=ft.Text(opt), on_click=erstelle_klick(opt)))
                    pb = ft.PopupMenuButton(items=items, icon="arrow_drop_down", icon_color="white")
                    combo.suffix = pb 
                    return combo

                # --- 1. STAMMDATEN FELDER ---
                adr_in = ft.TextField(label="Adresse Markt", value=aktuelle_daten.get("adresse"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white")
                nr_in = ft.TextField(label="Marktnummer", value=aktuelle_daten.get("marktnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white")
                auft_in = ft.TextField(label="Auftragsnummer", value=aktuelle_daten.get("auftragsnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white")
                name_in = ft.TextField(label="Name Probenehmer", value=aktuelle_daten.get("mitarbeiter_name"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white")
                bem_in = ft.TextField(label="Zusätzliche Bemerkung", value=aktuelle_daten.get("bemerkung"), color="yellow", text_style=stil_tf_gelb_10, label_style=stil_label_weiss, border_color="white")
                
                ag_dd = erstelle_combo("Auftraggeber", aktuelle_daten.get("auftraggeber", ""), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund (Hackfleischmonitoring)"])
                typ_dd = erstelle_combo("Typ der Probenahme", aktuelle_daten.get("typ_probenahme", "Standard"), ["Standard", "Nachkontrolle", "Mehrwöchig"])

                lims_warnung = ft.Text("⚠️ HINWEIS: Aktivierungs-Haken fehlt!", color="red", weight="bold", visible=False)
                lims_override_cb = ft.Checkbox(label="Trotzdem speichern", visible=False, label_style=stil_cb_weiss, fill_color="red", check_color="white")

                def pruefe_lims_warnung(e=None):
                    tw_hat_daten = bool((tw_zeit_in.value or "").strip() or (tw_temp_in.value or "").strip())
                    se_hat_daten = bool((se_zeit_in.value or "").strip() or (se_temp_in.value or "").strip())
                    
                    tw_braucht_warnung = tw_hat_daten and not tw_kalt_cb.value
                    se_braucht_warnung = se_hat_daten and not se_kalt_cb.value
                    
                    lims_warnung.visible = tw_braucht_warnung or se_braucht_warnung
                    lims_override_cb.visible = tw_braucht_warnung or se_braucht_warnung
                    
                    if not (tw_braucht_warnung or se_braucht_warnung):
                        lims_override_cb.value = False
                    page.update()

                def format_zeit(e):
                    val = e.control.value or ""
                    zahlen = "".join([c for c in val if c.isdigit()])[:4]
                    neu_wert = zahlen[:2] + ":" + zahlen[2:] if len(zahlen) >= 3 else zahlen
                    if e.control.value != neu_wert:
                        e.control.value = neu_wert
                        e.control.update()
                    pruefe_lims_warnung()

                def format_temp_blur(e):
                    val = (e.control.value or "").strip().replace(" °C", "").replace("°C", "").strip()
                    e.control.value = val + " °C" if val else ""
                    e.control.update()
                    pruefe_lims_warnung()

                # --- 2. TRINKWASSER FELDER ---
                tw_kalt_cb = ft.Checkbox(label="Trinkwasser kalt", value=aktuelle_daten.get("tw_kalt", False), on_change=pruefe_lims_warnung, label_style=stil_label_weiss, fill_color="yellow", check_color="black")
                tw_zeit_in = ft.TextField(label="Probenahmezeit", value=aktuelle_daten.get("tw_zeit"), border_color="white", color="yellow", label_style=stil_label_weiss, on_change=format_zeit)
                tw_temp_in = ft.TextField(label="Temp Probenahme", value=aktuelle_daten.get("tw_temp"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur)
                tw_tempkonst_in = ft.TextField(label="Temp Konstante", value=aktuelle_daten.get("tw_tempkonst"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur)
                
                tw_desinf_dd = erstelle_combo("Desinfektion", aktuelle_daten.get("tw_desinf", "Abflammen"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
                tw_zapf_dd = erstelle_combo("Zapfstelle", aktuelle_daten.get("tw_zapf", "Spülbecken"), ["Spülbecken", "Handwaschbecken"])
                tw_zapf_sonst_dd = erstelle_combo("Sonstiges Zapfstelle", aktuelle_daten.get("tw_zapf_sonst", ""), ["Schlaucharmatur", "Schlauchbrause", "Schlauch mit Brause"])
                tw_inaktiv_dd = erstelle_combo("Inaktivierung", aktuelle_daten.get("tw_inaktiv", "Na-Thiosulfat"), ["Na-Thiosulfat"])
                
                tw_kurz1_dd = erstelle_combo("Farbe", aktuelle_daten.get("tw_kurz1", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], ausdehnbar=True)
                tw_kurz2_dd = erstelle_combo("Trübung", aktuelle_daten.get("tw_kurz2", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], ausdehnbar=True)
                tw_kurz3_dd = erstelle_combo("Bodensatz", aktuelle_daten.get("tw_kurz3", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], ausdehnbar=True)
                tw_kurz4_dd = erstelle_combo("Geruch", aktuelle_daten.get("tw_kurz4", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], ausdehnbar=True)
                
                tw_zweck_dd = erstelle_combo("Zweck", aktuelle_daten.get("tw_zweck", "Zweck B"), ["Zweck A", "Zweck B", "Zweck C"])
                tw_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("tw_verpackung", "500ml Kunststoff-Flasche mit Natriumthiosulfat"), ["500ml Kunststoff-Flasche mit Natriumthiosulfat"])
                tw_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("tw_entnahmeort", "Metzgerei"), ["Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke", "Salatbar", "Convenience Küche"])
                tw_bemerkung_dd = erstelle_combo("TW Bemerkung", aktuelle_daten.get("tw_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                cb_pn = ft.Checkbox(label="PN-Hahn", value=aktuelle_daten.get("tw_cb_pn", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_zwei = ft.Checkbox(label="Zweigriff", value=aktuelle_daten.get("tw_cb_zwei", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_sensor = ft.Checkbox(label="Sensor", value=aktuelle_daten.get("tw_cb_sensor", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_knie = ft.Checkbox(label="Knie", value=aktuelle_daten.get("tw_cb_knie", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_ein = ft.Checkbox(label="Einhebel", value=aktuelle_daten.get("tw_cb_ein", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_ein_g = ft.Checkbox(label="Eingriff", value=aktuelle_daten.get("tw_cb_ein_g", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_eck = ft.Checkbox(label="Eckventil", value=aktuelle_daten.get("tw_cb_eck", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                
                cb_auff_ja = ft.Checkbox(label="ja", value=aktuelle_daten.get("cb_auff_ja", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_nein = ft.Checkbox(label="nein", value=aktuelle_daten.get("cb_auff_nein", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_perl = ft.Checkbox(label="Perlator nicht entfernbar", value=aktuelle_daten.get("cb_auff_perl", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_verkalk = ft.Checkbox(label="Starke Verkalkung", value=aktuelle_daten.get("cb_auff_verkalk", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_verbrueh = ft.Checkbox(label="Armatur mit Verbrühschutz", value=aktuelle_daten.get("cb_auff_verbrueh", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_durchlauf = ft.Checkbox(label="Durchlauferhitzer", value=aktuelle_daten.get("cb_auff_durchlauf", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_unterbau = ft.Checkbox(label="Unterbauspeicher [L]", value=aktuelle_daten.get("cb_auff_unterbau", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                
                tw_unterbau_l_in = ft.TextField(value=aktuelle_daten.get("tw_unterbau_l"), width=50, height=35, content_padding=5, text_size=10, color="yellow")
                
                cb_auff_eck_zu = ft.Checkbox(label="Eckventil warm/kalt geschlossen", value=aktuelle_daten.get("cb_auff_eck_zu", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_nichtmoeglich = ft.Checkbox(label="nicht möglich", value=aktuelle_daten.get("cb_auff_nichtmoeglich", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_dusche = ft.Checkbox(label="Entnahme aus der Dusche", value=aktuelle_daten.get("cb_auff_dusche", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_handbrause = ft.Checkbox(label="Handbrause", value=aktuelle_daten.get("cb_auff_handbrause", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_sonst = ft.Checkbox(label="Sonstiges", value=aktuelle_daten.get("cb_auff_sonst", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                
                tw_auff_sonstiges_in = ft.TextField(label="Auffälligkeiten (Sonstiges)", value=aktuelle_daten.get("tw_auff_sonstiges"), color="yellow", label_style=stil_label_weiss)
                tw_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("tw_inhalt", "ca. 500 ml"), color="yellow", label_style=stil_label_weiss)

                # --- 3. SCHERBENEIS FELDER ---
                se_kalt_cb = ft.Checkbox(label="Scherbeneis Eigenkontrolle", value=aktuelle_daten.get("se_kalt", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                se_zeit_in = ft.TextField(label="Probenahmezeit", value=aktuelle_daten.get("se_zeit"), border_color="white", color="yellow", label_style=stil_label_weiss, on_change=format_zeit)
                se_zapf_dd = erstelle_combo("Zapfstelle (Eis)", aktuelle_daten.get("se_zapf", "Eismaschine"), ["Eismaschine"])
                
                se_cb_eiswanne = ft.Checkbox(label="Eiswanne/Schöpfprobe", value=aktuelle_daten.get("se_cb_eiswanne", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                se_cb_fallprobe = ft.Checkbox(label="Fallprobe", value=aktuelle_daten.get("se_cb_fallprobe", True), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                se_tech_sonst_in = ft.TextField(label="Sonstiges (Technik)", value=aktuelle_daten.get("se_tech_sonst"), color="yellow", label_style=stil_label_weiss)

                se_desinf_dd = erstelle_combo("Art der Desinfektion", aktuelle_daten.get("se_desinf", "ohne Desinfektion"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
                se_cb_ozon = ft.Checkbox(label="Ozonsterilisator", value=aktuelle_daten.get("se_cb_ozon", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                se_auff_sonst_in = ft.TextField(label="Sonstiges (Auffälligkeiten)", value=aktuelle_daten.get("se_auff_sonst"), color="yellow", label_style=stil_label_weiss)
                
                se_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("se_inhalt", "ca. 1000ml"), color="yellow", label_style=stil_label_weiss)
                se_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("se_verpackung", "steriler Probenbeutel"), ["steriler Probenbeutel"])
                se_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("se_entnahmeort", "Fischabteilung-Eismaschine"), ["Fischabteilung-Eismaschine", "Metzgerei", "Produktionsraum"])
                se_temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get("se_temp"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur)
                se_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("se_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])


                # --- 4. VORLAGEN LOGIK ---
                alle_vorlagen = lade_vorlagen()
                vorlagen_status = ft.Text("", weight="bold") 
                
                vl_dd = ft.Dropdown(options=[ft.dropdown.Option(k) for k in alle_vorlagen.keys()], expand=1)
                
                def lade_v(e):
                    if not vl_dd.value: return
                    v = alle_vorlagen.get(vl_dd.value, {})
                    
                    adr_in.value = ""; nr_in.value = ""; auft_in.value = ""
                    tw_kalt_cb.value = False; tw_zeit_in.value = ""; tw_temp_in.value = ""; tw_tempkonst_in.value = ""
                    se_kalt_cb.value = False; se_zeit_in.value = ""; se_temp_in.value = ""
                    
                    for cb in [cb_pn, cb_zwei, cb_sensor, cb_knie, cb_ein, cb_ein_g, cb_eck, cb_auff_ja, cb_auff_nein, cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf, cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich, cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst, se_cb_eiswanne, se_cb_ozon]: cb.value = False
                    tw_unterbau_l_in.value = ""; tw_auff_sonstiges_in.value = ""; se_tech_sonst_in.value = ""; se_auff_sonst_in.value = ""
                    
                    se_cb_fallprobe.value = True

                    if "name_in" in v: name_in.value = v["name_in"]
                    if "ag_dd" in v: ag_dd.value = v["ag_dd"]
                    if "typ_dd" in v: typ_dd.value = v["typ_dd"]
                    if "bem_in" in v: bem_in.value = v["bem_in"]
                    
                    if "tw_desinf_dd" in v: tw_desinf_dd.value = v["tw_desinf_dd"]
                    if "tw_zapf_dd" in v: tw_zapf_dd.value = v["tw_zapf_dd"]
                    if "tw_zapf_sonst_dd" in v: tw_zapf_sonst_dd.value = v["tw_zapf_sonst_dd"]
                    if "tw_inaktiv_dd" in v: tw_inaktiv_dd.value = v["tw_inaktiv_dd"]
                    if "tw_kurz1_dd" in v: tw_kurz1_dd.value = v["tw_kurz1_dd"]
                    if "tw_kurz2_dd" in v: tw_kurz2_dd.value = v["tw_kurz2_dd"]
                    if "tw_kurz3_dd" in v: tw_kurz3_dd.value = v["tw_kurz3_dd"]
                    if "tw_kurz4_dd" in v: tw_kurz4_dd.value = v["tw_kurz4_dd"]
                    if "tw_zweck_dd" in v: tw_zweck_dd.value = v["tw_zweck_dd"]
                    if "tw_inhalt_in" in v: tw_inhalt_in.value = v["tw_inhalt_in"]
                    if "tw_verpackung_dd" in v: tw_verpackung_dd.value = v["tw_verpackung_dd"]
                    if "tw_entnahmeort_dd" in v: tw_entnahmeort_dd.value = v["tw_entnahmeort_dd"]
                    if "tw_bemerkung_dd" in v: tw_bemerkung_dd.value = v["tw_bemerkung_dd"]

                    if "se_zapf_dd" in v: se_zapf_dd.value = v["se_zapf_dd"]
                    if "se_desinf_dd" in v: se_desinf_dd.value = v["se_desinf_dd"]
                    if "se_inhalt_in" in v: se_inhalt_in.value = v["se_inhalt_in"]
                    if "se_verpackung_dd" in v: se_verpackung_dd.value = v["se_verpackung_dd"]
                    if "se_entnahmeort_dd" in v: se_entnahmeort_dd.value = v["se_entnahmeort_dd"]
                    if "se_bemerkung_dd" in v: se_bemerkung_dd.value = v["se_bemerkung_dd"]
                    
                    vorlagen_status.value = f"✅ '{vl_dd.value}' geladen!"
                    vorlagen_status.color = "green"
                    pruefe_lims_warnung()
                    page.update()

                vl_load_btn = sicherer_button("Laden", lade_v, "blue", "white")
                vl_name_in = ft.TextField(label="Name für neue Vorlage", expand=1, label_style=stil_label_weiss)
                
                def del_v(e):
                    if vl_dd.value in alle_vorlagen:
                        del alle_vorlagen[vl_dd.value]
                        speichere_vorlagen(alle_vorlagen)
                        vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                        vorlagen_status.value = f"🗑️ Gelöscht!"
                        vorlagen_status.color = "red"
                        vl_dd.value = None
                        page.update()

                vl_del_btn = sicherer_button("🗑️", del_v, "red", "white")
                
                def save_v(e):
                    if not vl_name_in.value: return
                    
                    d_v = {
                        "name_in": name_in.value, "ag_dd": ag_dd.value, "typ_dd": typ_dd.value, "bem_in": bem_in.value,
                        "tw_desinf_dd": tw_desinf_dd.value, "tw_zapf_dd": tw_zapf_dd.value, "tw_zapf_sonst_dd": tw_zapf_sonst_dd.value,
                        "tw_inaktiv_dd": tw_inaktiv_dd.value, "tw_kurz1_dd": tw_kurz1_dd.value, "tw_kurz2_dd": tw_kurz2_dd.value,
                        "tw_kurz3_dd": tw_kurz3_dd.value, "tw_kurz4_dd": tw_kurz4_dd.value, "tw_zweck_dd": tw_zweck_dd.value, 
                        "tw_inhalt_in": tw_inhalt_in.value, "tw_verpackung_dd": tw_verpackung_dd.value, 
                        "tw_entnahmeort_dd": tw_entnahmeort_dd.value, "tw_bemerkung_dd": tw_bemerkung_dd.value,
                        "se_zapf_dd": se_zapf_dd.value, "se_desinf_dd": se_desinf_dd.value, "se_inhalt_in": se_inhalt_in.value,
                        "se_verpackung_dd": se_verpackung_dd.value, "se_entnahmeort_dd": se_entnahmeort_dd.value, "se_bemerkung_dd": se_bemerkung_dd.value
                    }
                    alle_vorlagen[vl_name_in.value] = d_v
                    speichere_vorlagen(alle_vorlagen)
                    vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                    vorlagen_status.value = f"✅ Gespeichert!"
                    vorlagen_status.color = "orange"
                    vl_name_in.value = ""
                    page.update()

                vl_save_btn = sicherer_button("⭐ Speichern", save_v, "orange", "black")
                
                vorlagen_container = ft.Container(
                    bgcolor="#002200", padding=15, border_radius=10,
                    content=ft.Column([
                        ft.Row([ft.Text("📋 Globale Tour-Vorlagen", color="white", weight="bold", size=16), vorlagen_status]),
                        vl_dd,
                        ft.Row([vl_del_btn, vl_load_btn], alignment=ft.MainAxisAlignment.END),
                        ft.Divider(color="white24"),
                        vl_name_in,
                        ft.Row([vl_save_btn], alignment=ft.MainAxisAlignment.END)
                    ], spacing=10)
                )

                # --- ZUSAMMENBAU DES LAYOUTS ---
                def cb_row(links, rechts):
                    return ft.Row([ft.Container(links, expand=1), ft.Container(rechts, expand=1)], vertical_alignment=ft.CrossAxisAlignment.CENTER)

                stamm_col = ft.Column([adr_in, nr_in, auft_in, ag_dd, name_in, typ_dd, bem_in], visible=True)
                
                tw_col = ft.Column([
                    tw_kalt_cb,
                    tw_zeit_in, tw_temp_in, tw_tempkonst_in, tw_desinf_dd, tw_zapf_dd, tw_zapf_sonst_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Probenahmetechnik / Art der Zapfstelle:", color="white", weight="bold"),
                    cb_row(cb_pn, cb_ein), cb_row(cb_zwei, cb_ein_g), cb_row(cb_sensor, cb_eck), cb_knie,
                    ft.Divider(color="white24"),
                    ft.Text("Sensorik & Auffälligkeiten", color="white", size=16, weight="bold"),
                    tw_inaktiv_dd,
                    ft.Text("Kurzsensorik:", color="white", weight="bold"),
                    ft.Row([tw_kurz1_dd, tw_kurz2_dd]), ft.Row([tw_kurz3_dd, tw_kurz4_dd]),
                    ft.Text("Auffälligkeiten:", color="white", weight="bold"),
                    cb_row(cb_auff_ja, cb_auff_nein), cb_row(cb_auff_perl, cb_auff_verkalk), cb_row(cb_auff_verbrueh, cb_auff_durchlauf),
                    cb_row(ft.Row([cb_auff_unterbau, tw_unterbau_l_in], spacing=0), cb_auff_eck_zu),
                    cb_row(cb_auff_nichtmoeglich, cb_auff_dusche), cb_row(cb_auff_handbrause, cb_auff_sonst),
                    tw_auff_sonstiges_in,
                    ft.Divider(color="white24"),
                    ft.Text("Probenahmedetails", color="white", size=16, weight="bold"),
                    tw_zweck_dd, tw_inhalt_in, tw_verpackung_dd, tw_entnahmeort_dd, tw_bemerkung_dd
                ], visible=False)

                se_col = ft.Column([
                    se_kalt_cb,
                    se_zeit_in, se_zapf_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Probenahmetechnik / Art der Zapfstelle:", color="white", weight="bold"),
                    cb_row(se_cb_eiswanne, se_cb_fallprobe),
                    se_tech_sonst_in,
                    ft.Divider(color="white24"),
                    se_desinf_dd,
                    ft.Text("Auffälligkeiten:", color="white", weight="bold"),
                    se_cb_ozon, se_auff_sonst_in,
                    ft.Divider(color="white24"),
                    se_inhalt_in, se_verpackung_dd, se_entnahmeort_dd, se_temp_in, se_bemerkung_dd
                ], visible=False)

                # --- 5. NEU: HFM UNTERMENÜ & PLATZHALTER ---
                hfm_hack_col = ft.Column([ft.Text("Hier kommen später die Felder für: Hackfleisch gemischt", color="yellow")], visible=True)
                hfm_mett_col = ft.Column([ft.Text("Hier kommen später die Felder für: Gewürztes Schweinemett", color="yellow")], visible=False)
                hfm_fz_schwein_col = ft.Column([ft.Text("Hier kommen später die Felder für: Fleischzubereitung Schwein", color="yellow")], visible=False)
                hfm_fz_gefluegel_col = ft.Column([ft.Text("Hier kommen später die Felder für: Fleischzubereitung Geflügel", color="yellow")], visible=False)
                hfm_bio_col = ft.Column([ft.Text("Hier kommen später die Felder für: Biohackfleisch", color="yellow")], visible=False)

                def switch_hfm_tab(tab_name):
                    hfm_hack_col.visible = (tab_name == "hack")
                    hfm_mett_col.visible = (tab_name == "mett")
                    hfm_fz_schwein_col.visible = (tab_name == "schwein")
                    hfm_fz_gefluegel_col.visible = (tab_name == "gefluegel")
                    hfm_bio_col.visible = (tab_name == "bio")
                    
                    btn_hfm_hack.bgcolor = "red" if tab_name == "hack" else "grey"
                    btn_hfm_mett.bgcolor = "red" if tab_name == "mett" else "grey"
                    btn_hfm_fz_schwein.bgcolor = "red" if tab_name == "schwein" else "grey"
                    btn_hfm_fz_gefluegel.bgcolor = "red" if tab_name == "gefluegel" else "grey"
                    btn_hfm_bio.bgcolor = "red" if tab_name == "bio" else "grey"
                    page.update()

                btn_hfm_hack = sicherer_button("Hack gemischt", lambda e: switch_hfm_tab("hack"), "red", "white")
                btn_hfm_mett = sicherer_button("Mett", lambda e: switch_hfm_tab("mett"), "grey", "white")
                btn_hfm_fz_schwein = sicherer_button("FZ Schwein", lambda e: switch_hfm_tab("schwein"), "grey", "white")
                btn_hfm_fz_gefluegel = sicherer_button("FZ Geflügel", lambda e: switch_hfm_tab("gefluegel"), "grey", "white")
                btn_hfm_bio = sicherer_button("Bio-Hack", lambda e: switch_hfm_tab("bio"), "grey", "white")

                hfm_col = ft.Column([
                    ft.Row([btn_hfm_hack, btn_hfm_mett, btn_hfm_fz_schwein, btn_hfm_fz_gefluegel, btn_hfm_bio], scroll=ft.ScrollMode.AUTO),
                    ft.Divider(color="white24"),
                    hfm_hack_col, hfm_mett_col, hfm_fz_schwein_col, hfm_fz_gefluegel_col, hfm_bio_col
                ], visible=False)

                # --- HAUPT-REITER SCHALTUNGEN ---
                def switch_tab_stamm(e):
                    stamm_col.visible = True; tw_col.visible = False; se_col.visible = False; hfm_col.visible = False
                    btn_stamm.bgcolor = "red"; btn_tw.bgcolor = "grey"; btn_se.bgcolor = "grey"; btn_hfm.bgcolor = "grey"
                    page.update()
                    
                def switch_tab_tw(e):
                    stamm_col.visible = False; tw_col.visible = True; se_col.visible = False; hfm_col.visible = False
                    btn_stamm.bgcolor = "grey"; btn_tw.bgcolor = "red"; btn_se.bgcolor = "grey"; btn_hfm.bgcolor = "grey"
                    page.update()

                def switch_tab_se(e):
                    stamm_col.visible = False; tw_col.visible = False; se_col.visible = True; hfm_col.visible = False
                    btn_stamm.bgcolor = "grey"; btn_tw.bgcolor = "grey"; btn_se.bgcolor = "red"; btn_hfm.bgcolor = "grey"
                    page.update()

                def switch_tab_hfm(e):
                    stamm_col.visible = False; tw_col.visible = False; se_col.visible = False; hfm_col.visible = True
                    btn_stamm.bgcolor = "grey"; btn_tw.bgcolor = "grey"; btn_se.bgcolor = "grey"; btn_hfm.bgcolor = "red"
                    page.update()

                btn_stamm = sicherer_button("STAMMDATEN", switch_tab_stamm, "red", "white")
                btn_tw = sicherer_button("TRINKWASSER", switch_tab_tw, "grey", "white")
                btn_se = sicherer_button("SCHERBENEIS", switch_tab_se, "grey", "white")
                btn_hfm = sicherer_button("HFM", switch_tab_hfm, "grey", "white")

                fehler_text = ft.Text("", color="red", weight="bold", visible=False)
                status_text = ft.Text("", color="yellow", weight="bold", size=16)

                def hole_aktuelle_daten():
                    return {
                        "adresse": adr_in.value, "marktnummer": nr_in.value, "auftragsnummer": auft_in.value, 
                        "mitarbeiter_name": name_in.value, "auftraggeber": ag_dd.value, "typ_probenahme": typ_dd.value, "bemerkung": bem_in.value,
                        
                        "tw_kalt": tw_kalt_cb.value, "tw_lims_override": lims_override_cb.value, "tw_zeit": tw_zeit_in.value, 
                        "tw_temp": tw_temp_in.value, "tw_desinf": tw_desinf_dd.value, "tw_zapf": tw_zapf_dd.value,
                        "tw_cb_pn": cb_pn.value, "tw_cb_zwei": cb_zwei.value, "tw_cb_sensor": cb_sensor.value, "tw_cb_knie": cb_knie.value, 
                        "tw_cb_ein": cb_ein.value, "tw_cb_ein_g": cb_ein_g.value, "tw_cb_eck": cb_eck.value, "tw_zapf_sonst": tw_zapf_sonst_dd.value,
                        "tw_inaktiv": tw_inaktiv_dd.value, "tw_kurz1": tw_kurz1_dd.value, "tw_kurz2": tw_kurz2_dd.value, 
                        "tw_kurz3": tw_kurz3_dd.value, "tw_kurz4": tw_kurz4_dd.value, "cb_auff_ja": cb_auff_ja.value, 
                        "cb_auff_nein": cb_auff_nein.value, "cb_auff_perl": cb_auff_perl.value, "cb_auff_verkalk": cb_auff_verkalk.value, 
                        "cb_auff_verbrueh": cb_auff_verbrueh.value, "cb_auff_durchlauf": cb_auff_durchlauf.value,
                        "cb_auff_unterbau": cb_auff_unterbau.value, "tw_unterbau_l": tw_unterbau_l_in.value, "cb_auff_eck_zu": cb_auff_eck_zu.value, 
                        "cb_auff_nichtmoeglich": cb_auff_nichtmoeglich.value, "cb_auff_dusche": cb_auff_dusche.value, 
                        "cb_auff_handbrause": cb_auff_handbrause.value, "cb_auff_sonst": cb_auff_sonst.value, "tw_auff_sonstiges": tw_auff_sonstiges_in.value,
                        "tw_zweck": tw_zweck_dd.value, "tw_inhalt": tw_inhalt_in.value, "tw_verpackung": tw_verpackung_dd.value, 
                        "tw_entnahmeort": tw_entnahmeort_dd.value, "tw_tempkonst": tw_tempkonst_in.value, "tw_bemerkung": tw_bemerkung_dd.value,

                        "se_kalt": se_kalt_cb.value, "se_zeit": se_zeit_in.value, "se_zapf": se_zapf_dd.value,
                        "se_cb_eiswanne": se_cb_eiswanne.value, "se_cb_fallprobe": se_cb_fallprobe.value, "se_tech_sonst": se_tech_sonst_in.value,
                        "se_desinf": se_desinf_dd.value, "se_cb_ozon": se_cb_ozon.value, "se_auff_sonst": se_auff_sonst_in.value,
                        "se_inhalt": se_inhalt_in.value, "se_verpackung": se_verpackung_dd.value, "se_entnahmeort": se_entnahmeort_dd.value,
                        "se_temp": se_temp_in.value, "se_bemerkung": se_bemerkung_dd.value
                    }

                def nur_speichern(e):
                    if not nr_in.value or not auft_in.value:
                        switch_tab_stamm(None)
                        fehler_text.value="⚠️ MARKTNUMMER UND AUFTRAGSNUMMER FEHLEN!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return

                    try:
                        fehler_text.visible = False
                        status_text.value = "⏳ Speichere in Touren-Liste..."
                        status_text.color = "yellow"
                        page.update()

                        maerkte = lade_maerkte()
                        d = hole_aktuelle_daten()
                        if markt_index is None: maerkte.append(d)
                        else: maerkte[markt_index] = d
                        speichere_maerkte(maerkte)

                        status_text.value = "✅ Tour gespeichert!"
                        status_text.color = "orange"
                        page.update()
                    except Exception as ex: 
                        status_text.value = "❌ Fehler"
                        status_text.color = "red"
                        zeige_fehler(ex)

                def save_final(e):
                    if not nr_in.value or not auft_in.value:
                        switch_tab_stamm(None)
                        fehler_text.value="⚠️ MARKTNUMMER UND AUFTRAGSNUMMER FEHLEN!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return
                    
                    hat_tw_daten = bool((tw_zeit_in.value or "").strip() or (tw_temp_in.value or "").strip())
                    hat_se_daten = bool((se_zeit_in.value or "").strip() or (se_temp_in.value or "").strip())
                    
                    if hat_tw_daten and not tw_kalt_cb.value and not lims_override_cb.value:
                        switch_tab_tw(None)
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI TRINKWASSER FEHLT!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return

                    if hat_se_daten and not se_kalt_cb.value and not lims_override_cb.value:
                        switch_tab_se(None)
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI SCHERBENEIS FEHLT!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return

                    try:
                        fehler_text.visible = False
                        status_text.value = "⏳ Speichere und erstelle PDF..."
                        status_text.color = "yellow"
                        page.update()

                        maerkte = lade_maerkte()
                        d = hole_aktuelle_daten()
                        if markt_index is None: maerkte.append(d)
                        else: maerkte[markt_index] = d
                        speichere_maerkte(maerkte)

                        temp_dir, final_dir, heute_ordner = get_rewe_paths()
                        s_markt = "".join([c for c in nr_in.value if c.isalnum()])
                        final_ausg = os.path.join(final_dir, f"REWE_{s_markt}_{datetime.datetime.now().strftime('%d%m%y')}.pdf")
                        
                        writer = pypdf.PdfWriter()
                        writer.append(pypdf.PdfReader(os.path.join("assets", "stammdaten.pdf")))
                        writer.append(pypdf.PdfReader(os.path.join("assets", "trinkwasser.pdf")))
                        writer.append(pypdf.PdfReader(os.path.join("assets", "scherbeneis.pdf")))
                        
                        def cb_val(val): return "/Yes" if val else "/Off"
                            
                        tw_sonst_text = tw_auff_sonstiges_in.value or ""
                        if cb_auff_unterbau.value and (tw_unterbau_l_in.value or "").strip(): 
                            tw_sonst_text += f" (L: {tw_unterbau_l_in.value})"
                        
                        f_map = {
                            "tf_0000_00_ZS-001870": adr_in.value, "tf_0000_00_ZS-1408": nr_in.value, "tf_0000_00_ZS-002000": auft_in.value, 
                            "cal_templateLaborderprobenahmeDatum": datetime.datetime.now().strftime('%d.%m.%Y'), 
                            "dd_0000_00_ZS-002314": name_in.value, "dd_0000_00_ZS-1566": ag_dd.value, 
                            "dd_0000_00_ZS-002315": typ_dd.value, "dd_0000_00_ZS-001796": bem_in.value
                        }
                        
                        if tw_kalt_cb.value:
                            f_map.update({
                                "cb_0001_00": cb_val(tw_kalt_cb.value), "tf_0001_00_probenahmeUhrzeit": tw_zeit_in.value, 
                                "tf_0001_00_ZS-1441": tw_temp_in.value, "tf_0001_00_PE_ZS-1514": tw_tempkonst_in.value, 
                                "dd_0001_00_PE_ZS-002255": tw_desinf_dd.value, "dd_0001_00_PE_ZS-002318": tw_zapf_dd.value, 
                                "cb_0001_00_PE_ZS-002304_PN-Hahn": cb_val(cb_pn.value), "cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur": cb_val(cb_ein.value), 
                                "cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur": cb_val(cb_zwei.value), "cb_0001_00_PE_ZS-002304_ Eingriff-Armmatur": cb_val(cb_ein_g.value), 
                                "cb_0001_00_PE_ZS-002304_ Sensor-Armatur": cb_val(cb_sensor.value), "cb_0001_00_PE_ZS-002304_ Eckventil": cb_val(cb_eck.value), 
                                "cb_0001_00_PE_ZS-002304_ Armatur mit Kniebestätigung": cb_val(cb_knie.value), "cb_0001_00_PE_ZS-002304_Sonstiges": tw_zapf_sonst_dd.value, 
                                "dd_0001_00_PE_ZS-001948": tw_inaktiv_dd.value, "dd_0001_00_PE_ZS-002305_Farbe": tw_kurz1_dd.value, 
                                "dd_0001_00_PE_ZS-002305_ Trübung": tw_kurz2_dd.value, "dd_0001_00_PE_ZS-002305_ Bodensatz": tw_kurz3_dd.value, 
                                "dd_0001_00_PE_ZS-002305_ Geruch": tw_kurz4_dd.value, "cb_0001_00_PE_ZS-1268_ja": cb_val(cb_auff_ja.value), 
                                "cb_0001_00_PE_ZS-1268_ nein": cb_val(cb_auff_nein.value), "cb_0001_00_PE_ZS-1268_ Perlator nicht entfernbar": cb_val(cb_auff_perl.value), 
                                "cb_0001_00_PE_ZS-1268_ Starke Verkalkung": cb_val(cb_auff_verkalk.value), "cb_0001_00_PE_ZS-1268_ Armatur mit Verbrühschutz": cb_val(cb_auff_verbrueh.value), 
                                "cb_0001_00_PE_ZS-1268_ Durchlauferhitzer": cb_val(cb_auff_durchlauf.value), "cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]": cb_val(cb_auff_unterbau.value), 
                                "cb_0001_00_PE_ZS-1268_ Eckventil warm/kalt geschlossen": cb_val(cb_auff_eck_zu.value), "cb_0001_00_PE_ZS-1268_ nicht möglich": cb_val(cb_auff_nichtmoeglich.value), 
                                "cb_0001_00_PE_ZS-1268_ Entnahme aus der Dusche": cb_val(cb_auff_dusche.value), "cb_0001_00_PE_ZS-1268_ Handbrause": cb_val(cb_auff_handbrause.value), 
                                "cb_0001_00_PE_ZS-1268_ Sonstiges": cb_val(bool(tw_sonst_text)), "cb_0001_00_PE_ZS-1268_Sonstiges": tw_sonst_text, 
                                "dd_0001_00_PE_ZS-002317": tw_zweck_dd.value, "tf_0001_00_ZS-1215": tw_inhalt_in.value, 
                                "dd_0001_00_ZS-001798": tw_verpackung_dd.value, "dd_0001_00_ZS-001799": tw_entnahmeort_dd.value, "dd_0001_00_ZS-001796": tw_bemerkung_dd.value
                            })

                        if se_kalt_cb.value:
                            f_map.update({
                                "cb_0002_00": cb_val(se_kalt_cb.value),
                                "tf_0002_00_probenahmeUhrzeit": se_zeit_in.value,
                                "dd_0002_00_PE_ZS-002319": se_zapf_dd.value,
                                "cb_0002_00_PE_ZS-002304_Eiswanne": cb_val(se_cb_eiswanne.value),
                                "cb_0002_00_PE_ZS-002304_ Fallprobe": cb_val(se_cb_fallprobe.value),
                                "cb_0002_00_PE_ZS-002304_Sonstiges": se_tech_sonst_in.value,
                                "dd_0002_00_PE_ZS-002255": se_desinf_dd.value,
                                "cb_0002_00_PE_ZS-1268_Ozonsterilisator": cb_val(se_cb_ozon.value),
                                "cb_0002_00_PE_ZS-1268_Sonstiges": se_auff_sonst_in.value,
                                "tf_0002_00_ZS-1215": se_inhalt_in.value,
                                "dd_0002_00_ZS-001798": se_verpackung_dd.value,
                                "dd_0002_00_ZS-001799": se_entnahmeort_dd.value,
                                "tf_0002_00_ZS-1441": se_temp_in.value,
                                "dd_0002_00_ZS-001796": se_bemerkung_dd.value
                            })
                            
                        if "/AcroForm" not in writer.root_object: 
                            writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
                            
                        if "/Fields" not in writer.root_object["/AcroForm"]: 
                            writer.root_object["/AcroForm"].update({NameObject("/Fields"): ArrayObject()})
                            
                        for p in writer.pages: 
                            writer.update_page_form_field_values(p, f_map)
                            
                        with open(final_ausg, "wb") as f: 
                            writer.write(f)
                            
                        status_text.value = "✅ PDF erfolgreich erstellt!"
                        status_text.color = "green"
                        page.update()
                        
                    except Exception as ex: 
                        status_text.value = "❌ Fehler"
                        status_text.color = "red"
                        zeige_fehler(ex)

                btn_zurueck = sicherer_button("🔙 Zurück", lambda e: zeige_dashboard(), "#004400", "white", expand=True)
                btn_speichern = sicherer_button("💾 Nur Speichern", nur_speichern, "orange", "black", expand=True)
                btn_final = sicherer_button("📄 Bericht erstellen (PDF)", save_final, "blue", "white", expand=True, height=50)

                ansicht.controls.extend([
                    ft.Row([btn_stamm, btn_tw, btn_se, btn_hfm], scroll=ft.ScrollMode.AUTO),
                    lims_warnung,
                    lims_override_cb,
                    vorlagen_container,
                    ft.Divider(color="white"),
                    ft.Text(titel, size=20, weight="bold", color="white"),
                    stamm_col, tw_col, se_col, hfm_col,
                    ft.Container(height=20),
                    fehler_text,
                    status_text,
                    ft.Row([btn_zurueck, btn_speichern]),
                    ft.Row([btn_final])
                ])
                page.update()
                
            except Exception as intern_e:
                zeige_fehler(intern_e)

        def zeige_postausgang():
            ansicht.controls.clear(); ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
            temp_dir, final_dir, heute_ordner = get_rewe_paths()
            ansicht.controls.append(ft.Text(spans=[ft.TextSpan("Die Berichte für heute liegen im Ordner:\n", ft.TextStyle(color="red", size=12)), ft.TextSpan(f"Downloads / REWE / {heute_ordner} /\n\n", ft.TextStyle(color="red", size=14, weight="bold")), ft.TextSpan("TIPP: Um einen Bericht zu ändern, bearbeite einfach die Tour und klicke neu auf 'Bericht erstellen'. Der alte Bericht wird automatisch überschrieben!", ft.TextStyle(color="red", size=12))]))
            ansicht.controls.append(ft.Container(height=10))
            p_list = [f for f in os.listdir(final_dir) if f.endswith(".pdf")] if os.path.exists(final_dir) else []
            if not p_list: ansicht.controls.append(ft.Text("Noch keine Berichte für heute erstellt.", color="grey", size=14))
            for pdf in p_list:
                def rm(e, d=pdf): os.remove(os.path.join(final_dir, d)); zeige_postausgang()
                ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=10, content=ft.Row([ft.Text(pdf, color="white", size=10, expand=True), sicherer_button("🗑️", rm, "red", "white")])))
            page.update()

        def zeige_archiv(): ansicht.controls.clear(); ansicht.controls.append(nav_leiste()); page.update()
        zeige_startbildschirm()
        
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": ft.app(target=main, assets_dir="assets")