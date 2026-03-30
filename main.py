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

        # Hilfs-Funktion für sichere Buttons
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
                ft.Row([v_in], alignment=ft.MainAxisAlignment.CENTER), 
                ft.Row([z_in], alignment=ft.MainAxisAlignment.CENTER), 
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
                heute_str = datetime.datetime.now().strftime('%d.%m.%Y')
                
                if markt_index is None:
                    aktuelle_daten = {"datum": heute_str, "adresse": "", "marktnummer": "", "auftragsnummer": "", "mitarbeiter_name": f"{v} {z}".strip(), "auftraggeber": "03509 - REWE Hackfleischmonitoring", "typ_probenahme": "Standard", "bemerkung": ""}
                    titel = "Neue Tour anlegen"
                else:
                    aktuelle_daten = maerkte[markt_index]
                    titel = "Tour bearbeiten"

                stil_tf_gelb_12 = ft.TextStyle(color="yellow", size=12)
                stil_label_weiss = ft.TextStyle(color="white")
                stil_cb_weiss = ft.TextStyle(color="white", size=12)

                tage_opts = [""] + [f"{i:02d}" for i in range(1, 32)]
                mon_opts = [""] + [f"{i:02d}" for i in range(1, 13)]
                jahr_opts = [""] + [str(i) for i in range(2024, 2035)]
                
                charge_opts_s = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Schweinehackfleisch"]
                charge_opts_r = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Rinderhackfleisch"]
                entnahmeort_opts = ["Fischabteilung", "Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke"]
                verpackung_opts = ["steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel u. etikett", "Pappschale mit Kunststofffolie umwickelt", "tiefgezogene Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie umwickelt", "SB-Kunststoffverpackung"]

                def parse_datum(datum_str, def_t="", def_m="", def_j=""):
                    if not datum_str: return def_t, def_m, def_j
                    parts = datum_str.split(".")
                    if len(parts) == 3: return parts[0], parts[1], parts[2]
                    return def_t, def_m, def_j

                def get_date_str(t, m, j):
                    t = t.strip() if t else ""
                    m = m.strip() if m else ""
                    j = j.strip() if j else ""
                    if not t and not m and not j: return ""
                    return f"{t}.{m}.{j}"

                # Standard ausdehnbar=True zwingt alle Dropdowns auf volle Breite!
                def erstelle_combo(label_text, wert, optionen, groesse=12, ausdehnbar=True, on_change_func=None):
                    def on_txt_change(e):
                        if on_change_func: on_change_func(e)
                        
                    combo = ft.TextField(
                        label=label_text, value=wert, color="yellow", 
                        text_style=ft.TextStyle(size=groesse, color="yellow"), label_style=stil_label_weiss, 
                        border_color="white", expand=ausdehnbar, content_padding=10, 
                        on_change=on_txt_change
                    )
                    items = []
                    for opt in optionen:
                        def erstelle_klick(txt):
                            def klick(e):
                                combo.value = txt
                                combo.update()
                                if on_change_func: on_change_func(e)
                            return klick
                        items.append(ft.PopupMenuItem(content=ft.Text(opt), on_click=erstelle_klick(opt)))
                    pb = ft.PopupMenuButton(items=items, icon="arrow_drop_down", icon_color="white")
                    combo.suffix = pb 
                    return combo

                # --- 1. STAMMDATEN FELDER ---
                d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                tag_dd = erstelle_combo("Tag", d_tag, tage_opts, ausdehnbar=1)
                mon_dd = erstelle_combo("Mon", d_mon, mon_opts, ausdehnbar=1)
                jahr_dd = erstelle_combo("Jahr", d_jahr, jahr_opts, ausdehnbar=2) # Jahr bekommt doppelt Platz

                datum_row = ft.Column([
                    ft.Text("Datum der Probenahme", color="white", weight="bold"),
                    ft.Row([tag_dd, mon_dd, jahr_dd])
                ])

                # expand=True bei JEDEM Textfeld hinzugefügt, für den Dehnungs-Zwang!
                adr_in = ft.TextField(label="Adresse Markt", value=aktuelle_daten.get("adresse"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                nr_in = ft.TextField(label="Marktnummer", value=aktuelle_daten.get("marktnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                auft_in = ft.TextField(label="Auftragsnummer", value=aktuelle_daten.get("auftragsnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                name_in = ft.TextField(label="Name Probenehmer", value=aktuelle_daten.get("mitarbeiter_name"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                bem_in = ft.TextField(label="Zusätzliche Bemerkung", value=aktuelle_daten.get("bemerkung"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                
                ag_dd = erstelle_combo("Auftraggeber", aktuelle_daten.get("auftraggeber", ""), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund (Hackfleischmonitoring)"])
                typ_dd = erstelle_combo("Typ der Probenahme", aktuelle_daten.get("typ_probenahme", "Standard"), ["Standard", "Nachkontrolle", "Mehrwöchig"])

                lims_warnung = ft.Text("⚠️ HINWEIS: Aktivierungs-Haken fehlt!", color="red", weight="bold", visible=False)
                lims_override_cb = ft.Checkbox(label="Trotzdem speichern", visible=False, label_style=stil_cb_weiss, fill_color="red", check_color="white")

                def pruefe_lims_warnung(e=None):
                    tw_hat_daten = bool((tw_zeit_in.value or "").strip() or (tw_temp_in.value or "").strip())
                    se_hat_daten = bool((se_zeit_in.value or "").strip() or (se_temp_in.value or "").strip())
                    hfm_hack_hat_daten = bool((hfm_hack_temp_in.value or "").strip() or (hfm_hack_mhd_s_tag_dd.value or "").strip() or (hfm_hack_mhd_r_tag_dd.value or "").strip())
                    hfm_mett_hat_daten = bool((hfm_mett_temp_in.value or "").strip() or (hfm_mett_mhd_tag_dd.value or "").strip())
                    hfm_fzs_hat_daten = bool((hfm_fzs_temp_in.value or "").strip() or (hfm_fzs_mhd_tag_dd.value or "").strip() or (hfm_fzs_produkt_in.value or "").strip())
                    hfm_fzg_hat_daten = bool((hfm_fzg_temp_in.value or "").strip() or (hfm_fzg_mhd_tag_dd.value or "").strip() or (hfm_fzg_produkt_in.value or "").strip())
                    
                    tw_braucht_warnung = tw_hat_daten and not tw_kalt_cb.value
                    se_braucht_warnung = se_hat_daten and not se_kalt_cb.value
                    hfm_hack_braucht_warnung = hfm_hack_hat_daten and not hfm_hack_cb.value
                    hfm_mett_braucht_warnung = hfm_mett_hat_daten and not hfm_mett_cb.value
                    hfm_fzs_braucht_warnung = hfm_fzs_hat_daten and not hfm_fzs_cb.value
                    hfm_fzg_braucht_warnung = hfm_fzg_hat_daten and not hfm_fzg_cb.value
                    
                    braucht_warnung = any([tw_braucht_warnung, se_braucht_warnung, hfm_hack_braucht_warnung, hfm_mett_braucht_warnung, hfm_fzs_braucht_warnung, hfm_fzg_braucht_warnung])
                    
                    lims_warnung.visible = braucht_warnung
                    lims_override_cb.visible = braucht_warnung
                    
                    if not braucht_warnung:
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
                tw_zeit_in = ft.TextField(label="Probenahmezeit", value=aktuelle_daten.get("tw_zeit"), border_color="white", color="yellow", label_style=stil_label_weiss, on_change=format_zeit, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                tw_temp_in = ft.TextField(label="Temp Probenahme", value=aktuelle_daten.get("tw_temp"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                tw_tempkonst_in = ft.TextField(label="Temp Konstante", value=aktuelle_daten.get("tw_tempkonst"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                tw_desinf_dd = erstelle_combo("Desinfektion", aktuelle_daten.get("tw_desinf", "Abflammen"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
                tw_zapf_dd = erstelle_combo("Zapfstelle", aktuelle_daten.get("tw_zapf", "Spülbecken"), ["Spülbecken", "Handwaschbecken"])
                tw_zapf_sonst_dd = erstelle_combo("Sonstiges Zapfstelle", aktuelle_daten.get("tw_zapf_sonst", ""), ["Schlaucharmatur", "Schlauchbrause", "Schlauch mit Brause"])
                tw_inaktiv_dd = erstelle_combo("Inaktivierung", aktuelle_daten.get("tw_inaktiv", "Na-Thiosulfat"), ["Na-Thiosulfat"])
                
                tw_kurz1_dd = erstelle_combo("Farbe", aktuelle_daten.get("tw_kurz1", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
                tw_kurz2_dd = erstelle_combo("Trübung", aktuelle_daten.get("tw_kurz2", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
                tw_kurz3_dd = erstelle_combo("Bodensatz", aktuelle_daten.get("tw_kurz3", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
                tw_kurz4_dd = erstelle_combo("Geruch", aktuelle_daten.get("tw_kurz4", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
                
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
                
                tw_unterbau_l_in = ft.TextField(value=aktuelle_daten.get("tw_unterbau_l"), expand=True, height=40, content_padding=10, text_size=12, color="yellow", border_color="white")
                
                cb_auff_eck_zu = ft.Checkbox(label="Eckventil warm/kalt geschlossen", value=aktuelle_daten.get("cb_auff_eck_zu", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_nichtmoeglich = ft.Checkbox(label="nicht möglich", value=aktuelle_daten.get("cb_auff_nichtmoeglich", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_dusche = ft.Checkbox(label="Entnahme aus der Dusche", value=aktuelle_daten.get("cb_auff_dusche", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_handbrause = ft.Checkbox(label="Handbrause", value=aktuelle_daten.get("cb_auff_handbrause", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                cb_auff_sonst = ft.Checkbox(label="Sonstiges", value=aktuelle_daten.get("cb_auff_sonst", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                
                tw_auff_sonstiges_in = ft.TextField(label="Auffälligkeiten (Sonstiges)", value=aktuelle_daten.get("tw_auff_sonstiges"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                tw_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("tw_inhalt", "ca. 500 ml"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12, expand=True)

                # --- 3. SCHERBENEIS FELDER ---
                se_kalt_cb = ft.Checkbox(label="Scherbeneis Eigenkontrolle", value=aktuelle_daten.get("se_kalt", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                se_zeit_in = ft.TextField(label="Probenahmezeit", value=aktuelle_daten.get("se_zeit"), border_color="white", color="yellow", label_style=stil_label_weiss, on_change=format_zeit, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                se_zapf_dd = erstelle_combo("Zapfstelle (Eis)", aktuelle_daten.get("se_zapf", "Eismaschine"), ["Eismaschine"])
                
                se_cb_eiswanne = ft.Checkbox(label="Eiswanne/Schöpfprobe", value=aktuelle_daten.get("se_cb_eiswanne", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                se_cb_fallprobe = ft.Checkbox(label="Fallprobe", value=aktuelle_daten.get("se_cb_fallprobe", True), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                se_tech_sonst_in = ft.TextField(label="Sonstiges (Technik)", value=aktuelle_daten.get("se_tech_sonst"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12, expand=True)

                se_desinf_dd = erstelle_combo("Art der Desinfektion", aktuelle_daten.get("se_desinf", "ohne Desinfektion"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
                se_cb_ozon = ft.Checkbox(label="Ozonsterilisator", value=aktuelle_daten.get("se_cb_ozon", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                se_auff_sonst_in = ft.TextField(label="Sonstiges (Auffälligkeiten)", value=aktuelle_daten.get("se_auff_sonst"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                se_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("se_inhalt", "ca. 1000ml"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                se_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("se_verpackung", "steriler Probenbeutel"), ["steriler Probenbeutel"])
                se_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("se_entnahmeort", "Fischabteilung-Eismaschine"), ["Fischabteilung-Eismaschine", "Metzgerei", "Produktionsraum"])
                se_temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get("se_temp"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                se_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("se_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 4. HFM - HACKFLEISCH GEMISCHT ---
                hfm_hack_cb = ft.Checkbox(label="Hackfleisch gemischt", value=aktuelle_daten.get("hfm_hack_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_hack_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_hack_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_h_t, hfm_h_m, hfm_h_j = parse_datum(aktuelle_daten.get("hfm_hack_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_hack_herst_tag_dd = erstelle_combo("Tag", hfm_h_t, tage_opts, ausdehnbar=1)
                hfm_hack_herst_mon_dd = erstelle_combo("Mon", hfm_h_m, mon_opts, ausdehnbar=1)
                hfm_hack_herst_jahr_dd = erstelle_combo("Jahr", hfm_h_j, jahr_opts, ausdehnbar=2)

                mhd_s_t, mhd_s_m, mhd_s_j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_schwein", ""))
                hfm_hack_mhd_s_tag_dd = erstelle_combo("Tag", mhd_s_t, tage_opts, ausdehnbar=1, on_change_func=pruefe_lims_warnung)
                hfm_hack_mhd_s_mon_dd = erstelle_combo("Mon", mhd_s_m, mon_opts, ausdehnbar=1)
                hfm_hack_mhd_s_jahr_dd = erstelle_combo("Jahr", mhd_s_j, jahr_opts, ausdehnbar=2)

                mhd_r_t, mhd_r_m, mhd_r_j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_rind", ""))
                hfm_hack_mhd_r_tag_dd = erstelle_combo("Tag", mhd_r_t, tage_opts, ausdehnbar=1, on_change_func=pruefe_lims_warnung)
                hfm_hack_mhd_r_mon_dd = erstelle_combo("Mon", mhd_r_m, mon_opts, ausdehnbar=1)
                hfm_hack_mhd_r_jahr_dd = erstelle_combo("Jahr", mhd_r_j, jahr_opts, ausdehnbar=2)

                hfm_hack_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_hack_inhalt", "jeweils ca. 200 g"), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_hack_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_hack_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_hack_lief_schwein_in = ft.TextField(label="Lieferant (Schwein)", value=aktuelle_daten.get("hfm_hack_lief_schwein", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_hack_lief_rind_in = ft.TextField(label="Lieferant (Rind)", value=aktuelle_daten.get("hfm_hack_lief_rind", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                hfm_hack_charge_schwein_dd = erstelle_combo("Charge Schwein", aktuelle_daten.get("hfm_hack_charge_schwein", "Bitte eingeben"), charge_opts_s)
                hfm_hack_charge_rind_dd = erstelle_combo("Charge Rind", aktuelle_daten.get("hfm_hack_charge_rind", "Bitte eingeben"), charge_opts_r)
                
                hfm_hack_temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get("hfm_hack_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_hack_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_hack_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 5. HFM - GEWÜRZTES SCHWEINEMETT ---
                hfm_mett_cb = ft.Checkbox(label="Gewürztes Schweinemett", value=aktuelle_daten.get("hfm_mett_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_mett_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_mett_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_m_t, hfm_m_m, hfm_m_j = parse_datum(aktuelle_daten.get("hfm_mett_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_mett_herst_tag_dd = erstelle_combo("Tag", hfm_m_t, tage_opts, ausdehnbar=1)
                hfm_mett_herst_mon_dd = erstelle_combo("Mon", hfm_m_m, mon_opts, ausdehnbar=1)
                hfm_mett_herst_jahr_dd = erstelle_combo("Jahr", hfm_m_j, jahr_opts, ausdehnbar=2)

                mhd_mett_t, mhd_mett_m, mhd_mett_j = parse_datum(aktuelle_daten.get("hfm_mett_mhd", ""))
                hfm_mett_mhd_tag_dd = erstelle_combo("Tag", mhd_mett_t, tage_opts, ausdehnbar=1, on_change_func=pruefe_lims_warnung)
                hfm_mett_mhd_mon_dd = erstelle_combo("Mon", mhd_mett_m, mon_opts, ausdehnbar=1)
                hfm_mett_mhd_jahr_dd = erstelle_combo("Jahr", mhd_mett_j, jahr_opts, ausdehnbar=2)

                hfm_mett_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_mett_inhalt", "ca. 200 g"), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_mett_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_mett_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_mett_lief_in = ft.TextField(label="Lieferant Rohware", value=aktuelle_daten.get("hfm_mett_lief", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_mett_charge_dd = erstelle_combo("Charge Rohware", aktuelle_daten.get("hfm_mett_charge", "Bitte eingeben"), charge_opts_s)
                
                hfm_mett_temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get("hfm_mett_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_mett_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_mett_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 6. HFM - FZ SCHWEIN ---
                hfm_fzs_cb = ft.Checkbox(label="Fleischzubereitung Schwein", value=aktuelle_daten.get("hfm_fzs_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_fzs_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_fzs_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_fzs_produkt_in = ft.TextField(label="Produkt", hint_text="z. B. Schweine Nacken", value=aktuelle_daten.get("hfm_fzs_produkt", ""), color="yellow", label_style=stil_label_weiss, border_color="white", on_change=pruefe_lims_warnung, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzs_marinade_in = ft.TextField(label="Marinade", value=aktuelle_daten.get("hfm_fzs_marinade", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                hfm_fzs_h_t, hfm_fzs_h_m, hfm_fzs_h_j = parse_datum(aktuelle_daten.get("hfm_fzs_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_fzs_herst_tag_dd = erstelle_combo("Tag", hfm_fzs_h_t, tage_opts, ausdehnbar=1)
                hfm_fzs_herst_mon_dd = erstelle_combo("Mon", hfm_fzs_h_m, mon_opts, ausdehnbar=1)
                hfm_fzs_herst_jahr_dd = erstelle_combo("Jahr", hfm_fzs_h_j, jahr_opts, ausdehnbar=2)

                mhd_fzs_t, mhd_fzs_m, mhd_fzs_j = parse_datum(aktuelle_daten.get("hfm_fzs_mhd", ""))
                hfm_fzs_mhd_tag_dd = erstelle_combo("Tag", mhd_fzs_t, tage_opts, ausdehnbar=1, on_change_func=pruefe_lims_warnung)
                hfm_fzs_mhd_mon_dd = erstelle_combo("Mon", mhd_fzs_m, mon_opts, ausdehnbar=1)
                hfm_fzs_mhd_jahr_dd = erstelle_combo("Jahr", mhd_fzs_j, jahr_opts, ausdehnbar=2)

                hfm_fzs_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_fzs_inhalt", "ca. 200 g"), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzs_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_fzs_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_fzs_lief_in = ft.TextField(label="Lieferant Rohware", value=aktuelle_daten.get("hfm_fzs_lief", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzs_charge_dd = erstelle_combo("Charge Rohware", aktuelle_daten.get("hfm_fzs_charge", "Bitte eingeben"), charge_opts_s)
                
                hfm_fzs_temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get("hfm_fzs_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzs_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_fzs_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 7. HFM - FZ GEFLÜGEL ---
                hfm_fzg_cb = ft.Checkbox(label="Fleischzubereitung Geflügel", value=aktuelle_daten.get("hfm_fzg_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_fzg_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_fzg_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_fzg_produkt_in = ft.TextField(label="Produkt", hint_text="z. B. Hähnchenbrust", value=aktuelle_daten.get("hfm_fzg_produkt", ""), color="yellow", label_style=stil_label_weiss, border_color="white", on_change=pruefe_lims_warnung, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzg_marinade_in = ft.TextField(label="Marinade", value=aktuelle_daten.get("hfm_fzg_marinade", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                hfm_fzg_h_t, hfm_fzg_h_m, hfm_fzg_h_j = parse_datum(aktuelle_daten.get("hfm_fzg_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_fzg_herst_tag_dd = erstelle_combo("Tag", hfm_fzg_h_t, tage_opts, ausdehnbar=1)
                hfm_fzg_herst_mon_dd = erstelle_combo("Mon", hfm_fzg_h_m, mon_opts, ausdehnbar=1)
                hfm_fzg_herst_jahr_dd = erstelle_combo("Jahr", hfm_fzg_h_j, jahr_opts, ausdehnbar=2)

                mhd_fzg_t, mhd_fzg_m, mhd_fzg_j = parse_datum(aktuelle_daten.get("hfm_fzg_mhd", ""))
                hfm_fzg_mhd_tag_dd = erstelle_combo("Tag", mhd_fzg_t, tage_opts, ausdehnbar=1, on_change_func=pruefe_lims_warnung)
                hfm_fzg_mhd_mon_dd = erstelle_combo("Mon", mhd_fzg_m, mon_opts, ausdehnbar=1)
                hfm_fzg_mhd_jahr_dd = erstelle_combo("Jahr", mhd_fzg_j, jahr_opts, ausdehnbar=2)

                hfm_fzg_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_fzg_inhalt", "ca. 200 g"), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzg_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_fzg_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_fzg_lief_in = ft.TextField(label="Lieferant Rohware", value=aktuelle_daten.get("hfm_fzg_lief", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzg_charge_dd = erstelle_combo("Charge Rohware", aktuelle_daten.get("hfm_fzg_charge", "Bitte eingeben"), ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Geflügel"])
                
                hfm_fzg_temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get("hfm_fzg_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzg_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_fzg_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                hfm_bio_col = ft.Column([ft.Text("Felder für: Biohackfleisch", color="yellow")], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                def switch_hfm_tab(tab_name):
                    hfm_hack_col.visible = (tab_name == "hack")
                    hfm_mett_col.visible = (tab_name == "mett")
                    hfm_fzs_col.visible = (tab_name == "schwein")
                    hfm_fzg_col.visible = (tab_name == "gefluegel")
                    hfm_bio_col.visible = (tab_name == "bio")
                    
                    btn_hfm_hack.bgcolor = "red" if tab_name == "hack" else "blue"
                    btn_hfm_mett.bgcolor = "red" if tab_name == "mett" else "blue"
                    btn_hfm_fz_schwein.bgcolor = "red" if tab_name == "schwein" else "blue"
                    btn_hfm_fz_gefluegel.bgcolor = "red" if tab_name == "gefluegel" else "blue"
                    btn_hfm_bio.bgcolor = "red" if tab_name == "bio" else "blue"
                    page.update()

                btn_hfm_hack = sicherer_button("Hack gemischt", lambda e: switch_hfm_tab("hack"), "red", "white")
                btn_hfm_mett = sicherer_button("Mett", lambda e: switch_hfm_tab("mett"), "blue", "white")
                btn_hfm_fz_schwein = sicherer_button("FZ Schwein", lambda e: switch_hfm_tab("schwein"), "blue", "white")
                btn_hfm_fz_gefluegel = sicherer_button("FZ Geflügel", lambda e: switch_hfm_tab("gefluegel"), "blue", "white")
                btn_hfm_bio = sicherer_button("Bio-Hack", lambda e: switch_hfm_tab("bio"), "blue", "white")

                hfm_col = ft.Column([
                    ft.Row([btn_hfm_hack, btn_hfm_mett, btn_hfm_fz_schwein, btn_hfm_fz_gefluegel, btn_hfm_bio], scroll=ft.ScrollMode.AUTO),
                    ft.Divider(color="white24"),
                    hfm_hack_col, hfm_mett_col, hfm_fzs_col, hfm_fzg_col, hfm_bio_col
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                # --- HAUPT-REITER SCHALTUNGEN ---
                def switch_tab_stamm(e):
                    stamm_col.visible = True; tw_col.visible = False; se_col.visible = False; hfm_col.visible = False
                    btn_stamm.bgcolor = "red"; btn_tw.bgcolor = "blue"; btn_se.bgcolor = "blue"; btn_hfm.bgcolor = "blue"
                    page.update()
                    
                def switch_tab_tw(e):
                    stamm_col.visible = False; tw_col.visible = True; se_col.visible = False; hfm_col.visible = False
                    btn_stamm.bgcolor = "blue"; btn_tw.bgcolor = "red"; btn_se.bgcolor = "blue"; btn_hfm.bgcolor = "blue"
                    page.update()

                def switch_tab_se(e):
                    stamm_col.visible = False; tw_col.visible = False; se_col.visible = True; hfm_col.visible = False
                    btn_stamm.bgcolor = "blue"; btn_tw.bgcolor = "blue"; btn_se.bgcolor = "red"; btn_hfm.bgcolor = "blue"
                    page.update()

                def switch_tab_hfm(e):
                    stamm_col.visible = False; tw_col.visible = False; se_col.visible = False; hfm_col.visible = True
                    btn_stamm.bgcolor = "blue"; btn_tw.bgcolor = "blue"; btn_se.bgcolor = "blue"; btn_hfm.bgcolor = "red"
                    page.update()

                # Blaue Hauptreiter, rot wenn aktiv
                btn_stamm = sicherer_button("STAMMDATEN", switch_tab_stamm, "red", "white")
                btn_tw = sicherer_button("TRINKWASSER", switch_tab_tw, "blue", "white")
                btn_se = sicherer_button("SCHERBENEIS", switch_tab_se, "blue", "white")
                btn_hfm = sicherer_button("HFM", switch_tab_hfm, "blue", "white")

                fehler_text = ft.Text("", color="red", weight="bold", visible=False)
                status_text = ft.Text("", color="yellow", weight="bold", size=16)

                def hole_aktuelle_daten():
                    return {
                        "datum": f"{tag_dd.value}.{mon_dd.value}.{jahr_dd.value}", "adresse": adr_in.value, "marktnummer": nr_in.value, "auftragsnummer": auft_in.value, 
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
                        "se_temp": se_temp_in.value, "se_bemerkung": se_bemerkung_dd.value,

                        "hfm_hack_cb": hfm_hack_cb.value, "hfm_hack_entnahmeort": hfm_hack_entnahmeort_dd.value,
                        "hfm_hack_herstelldatum": get_date_str(hfm_hack_herst_tag_dd.value, hfm_hack_herst_mon_dd.value, hfm_hack_herst_jahr_dd.value), 
                        "hfm_hack_inhalt": hfm_hack_inhalt_in.value, "hfm_hack_verpackung": hfm_hack_verpackung_dd.value, 
                        "hfm_hack_lief_schwein": hfm_hack_lief_schwein_in.value, "hfm_hack_lief_rind": hfm_hack_lief_rind_in.value, 
                        "hfm_hack_mhd_schwein": get_date_str(hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value),
                        "hfm_hack_mhd_rind": get_date_str(hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value), 
                        "hfm_hack_charge_schwein": hfm_hack_charge_schwein_dd.value, "hfm_hack_charge_rind": hfm_hack_charge_rind_dd.value, 
                        "hfm_hack_temp": hfm_hack_temp_in.value, "hfm_hack_bemerkung": hfm_hack_bemerkung_dd.value,

                        "hfm_mett_cb": hfm_mett_cb.value, "hfm_mett_entnahmeort": hfm_mett_entnahmeort_dd.value,
                        "hfm_mett_herstelldatum": get_date_str(hfm_mett_herst_tag_dd.value, hfm_mett_herst_mon_dd.value, hfm_mett_herst_jahr_dd.value),
                        "hfm_mett_inhalt": hfm_mett_inhalt_in.value, "hfm_mett_verpackung": hfm_mett_verpackung_dd.value,
                        "hfm_mett_lief": hfm_mett_lief_in.value, 
                        "hfm_mett_mhd": get_date_str(hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value),
                        "hfm_mett_charge": hfm_mett_charge_dd.value, "hfm_mett_temp": hfm_mett_temp_in.value,
                        "hfm_mett_bemerkung": hfm_mett_bemerkung_dd.value,

                        "hfm_fzs_cb": hfm_fzs_cb.value, "hfm_fzs_entnahmeort": hfm_fzs_entnahmeort_dd.value,
                        "hfm_fzs_produkt": hfm_fzs_produkt_in.value, "hfm_fzs_marinade": hfm_fzs_marinade_in.value,
                        "hfm_fzs_herstelldatum": get_date_str(hfm_fzs_herst_tag_dd.value, hfm_fzs_herst_mon_dd.value, hfm_fzs_herst_jahr_dd.value),
                        "hfm_fzs_inhalt": hfm_fzs_inhalt_in.value, "hfm_fzs_verpackung": hfm_fzs_verpackung_dd.value,
                        "hfm_fzs_lief": hfm_fzs_lief_in.value, 
                        "hfm_fzs_mhd": get_date_str(hfm_fzs_mhd_tag_dd.value, hfm_fzs_mhd_mon_dd.value, hfm_fzs_mhd_jahr_dd.value),
                        "hfm_fzs_charge": hfm_fzs_charge_dd.value, "hfm_fzs_temp": hfm_fzs_temp_in.value,
                        "hfm_fzs_bemerkung": hfm_fzs_bemerkung_dd.value,

                        "hfm_fzg_cb": hfm_fzg_cb.value, "hfm_fzg_entnahmeort": hfm_fzg_entnahmeort_dd.value,
                        "hfm_fzg_produkt": hfm_fzg_produkt_in.value, "hfm_fzg_marinade": hfm_fzg_marinade_in.value,
                        "hfm_fzg_herstelldatum": get_date_str(hfm_fzg_herst_tag_dd.value, hfm_fzg_herst_mon_dd.value, hfm_fzg_herst_jahr_dd.value),
                        "hfm_fzg_inhalt": hfm_fzg_inhalt_in.value, "hfm_fzg_verpackung": hfm_fzg_verpackung_dd.value,
                        "hfm_fzg_lief": hfm_fzg_lief_in.value, 
                        "hfm_fzg_mhd": get_date_str(hfm_fzg_mhd_tag_dd.value, hfm_fzg_mhd_mon_dd.value, hfm_fzg_mhd_jahr_dd.value),
                        "hfm_fzg_charge": hfm_fzg_charge_dd.value, "hfm_fzg_temp": hfm_fzg_temp_in.value,
                        "hfm_fzg_bemerkung": hfm_fzg_bemerkung_dd.value
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
                    hat_hfm_hack = bool((hfm_hack_temp_in.value or "").strip() or (hfm_hack_mhd_s_tag_dd.value or "").strip() or (hfm_hack_mhd_r_tag_dd.value or "").strip())
                    hat_hfm_mett = bool((hfm_mett_temp_in.value or "").strip() or (hfm_mett_mhd_tag_dd.value or "").strip())
                    hat_hfm_fzs = bool((hfm_fzs_temp_in.value or "").strip() or (hfm_fzs_mhd_tag_dd.value or "").strip() or (hfm_fzs_produkt_in.value or "").strip())
                    hat_hfm_fzg = bool((hfm_fzg_temp_in.value or "").strip() or (hfm_fzg_mhd_tag_dd.value or "").strip() or (hfm_fzg_produkt_in.value or "").strip())
                    
                    # 1. Haken vergessen Warnung (LIMS-Override)
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
                        
                    if hat_hfm_hack and not hfm_hack_cb.value and not lims_override_cb.value:
                        switch_tab_hfm(None)
                        switch_hfm_tab("hack")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI HACKFLEISCH GEMISCHT FEHLT!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return

                    if hat_hfm_mett and not hfm_mett_cb.value and not lims_override_cb.value:
                        switch_tab_hfm(None)
                        switch_hfm_tab("mett")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI SCHWEINEMETT FEHLT!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return

                    if hat_hfm_fzs and not hfm_fzs_cb.value and not lims_override_cb.value:
                        switch_tab_hfm(None)
                        switch_hfm_tab("schwein")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI FZ SCHWEIN FEHLT!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return

                    if hat_hfm_fzg and not hfm_fzg_cb.value and not lims_override_cb.value:
                        switch_tab_hfm(None)
                        switch_hfm_tab("gefluegel")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI FZ GEFLÜGEL FEHLT!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return

                    # 2. PFLICHTFELD WARNUNG (Uhrzeit, Temperatur, MHD)
                    fehlende_pflicht = []
                    if tw_kalt_cb.value:
                        if not tw_zeit_in.value.strip(): fehlende_pflicht.append("TW: Uhrzeit")
                        if not tw_temp_in.value.strip(): fehlende_pflicht.append("TW: Temperatur")
                    if se_kalt_cb.value:
                        if not se_zeit_in.value.strip(): fehlende_pflicht.append("Eis: Uhrzeit")
                        if not se_temp_in.value.strip(): fehlende_pflicht.append("Eis: Temperatur")
                    if hfm_hack_cb.value:
                        if not hfm_hack_temp_in.value.strip(): fehlende_pflicht.append("Hack: Temperatur")
                        if not hfm_hack_mhd_s_tag_dd.value.strip() and not hfm_hack_mhd_r_tag_dd.value.strip():
                            fehlende_pflicht.append("Hack: MHD (Schwein oder Rind)")
                    if hfm_mett_cb.value:
                        if not hfm_mett_temp_in.value.strip(): fehlende_pflicht.append("Mett: Temperatur")
                        if not hfm_mett_mhd_tag_dd.value.strip() or not hfm_mett_mhd_mon_dd.value.strip() or not hfm_mett_mhd_jahr_dd.value.strip():
                            fehlende_pflicht.append("Mett: MHD")
                    if hfm_fzs_cb.value:
                        if not hfm_fzs_temp_in.value.strip(): fehlende_pflicht.append("FZ Schwein: Temperatur")
                        if not hfm_fzs_mhd_tag_dd.value.strip() or not hfm_fzs_mhd_mon_dd.value.strip() or not hfm_fzs_mhd_jahr_dd.value.strip():
                            fehlende_pflicht.append("FZ Schwein: MHD")
                    if hfm_fzg_cb.value:
                        if not hfm_fzg_temp_in.value.strip(): fehlende_pflicht.append("FZ Geflügel: Temperatur")
                        if not hfm_fzg_mhd_tag_dd.value.strip() or not hfm_fzg_mhd_mon_dd.value.strip() or not hfm_fzg_mhd_jahr_dd.value.strip():
                            fehlende_pflicht.append("FZ Geflügel: MHD")
                            
                    if fehlende_pflicht:
                        fehler_text.value = f"⚠️ PFLICHTFELDER FEHLEN:\n{', '.join(fehlende_pflicht)}"
                        fehler_text.visible = True; status_text.value = ""
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
                        writer.append(pypdf.PdfReader(os.path.join("assets", "hackfleisch_gemischt.pdf")))
                        writer.append(pypdf.PdfReader(os.path.join("assets", "schweinemett.pdf")))
                        writer.append(pypdf.PdfReader(os.path.join("assets", "fz_schwein.pdf")))
                        writer.append(pypdf.PdfReader(os.path.join("assets", "fz_huhn.pdf")))
                        
                        def cb_val(val): return "/Yes" if val else "/Off"
                            
                        tw_sonst_text = tw_auff_sonstiges_in.value or ""
                        if cb_auff_unterbau.value and (tw_unterbau_l_in.value or "").strip(): 
                            tw_sonst_text += f" (L: {tw_unterbau_l_in.value})"
                        
                        f_map = {
                            "tf_0000_00_ZS-001870": adr_in.value, "tf_0000_00_ZS-1408": nr_in.value, "tf_0000_00_ZS-002000": auft_in.value, 
                            "cal_templateLaborderprobenahmeDatum": f"{tag_dd.value}.{mon_dd.value}.{jahr_dd.value}", 
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
                                "cb_0002_00": cb_val(se_kalt_cb.value), "tf_0002_00_probenahmeUhrzeit": se_zeit_in.value, 
                                "dd_0002_00_PE_ZS-002319": se_zapf_dd.value, "cb_0002_00_PE_ZS-002304_Eiswanne": cb_val(se_cb_eiswanne.value), 
                                "cb_0002_00_PE_ZS-002304_ Fallprobe": cb_val(se_cb_fallprobe.value), "cb_0002_00_PE_ZS-002304_Sonstiges": se_tech_sonst_in.value, 
                                "dd_0002_00_PE_ZS-002255": se_desinf_dd.value, "cb_0002_00_PE_ZS-1268_Ozonsterilisator": cb_val(se_cb_ozon.value), 
                                "cb_0002_00_PE_ZS-1268_Sonstiges": se_auff_sonst_in.value, "tf_0002_00_ZS-1215": se_inhalt_in.value, 
                                "dd_0002_00_ZS-001798": se_verpackung_dd.value, "dd_0002_00_ZS-001799": se_entnahmeort_dd.value, 
                                "tf_0002_00_ZS-1441": se_temp_in.value, "dd_0002_00_ZS-001796": se_bemerkung_dd.value
                            })

                        if hfm_hack_cb.value:
                            f_map.update({
                                "cb_0004_00": cb_val(hfm_hack_cb.value),
                                "tf_0004_00": "Hackfleisch gemischt",
                                "dd_0004_00_ZS-001799": hfm_hack_entnahmeort_dd.value,
                                "cal_0004_00_ZS-001810": get_date_str(hfm_hack_herst_tag_dd.value, hfm_hack_herst_mon_dd.value, hfm_hack_herst_jahr_dd.value),
                                "tf_0004_00_ZS-1215": hfm_hack_inhalt_in.value,
                                "dd_0004_00_ZS-001798": hfm_hack_verpackung_dd.value,
                                "tf_0004_00_ZS-1209_Schweinefleisch: XXX": hfm_hack_lief_schwein_in.value,
                                "tf_0004_00_ZS-1209_Rindfleisch: XXX": hfm_hack_lief_rind_in.value,
                                "tf_0004_00_ZS-001835_Schweinefleisch: XXX": get_date_str(hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value),
                                "tf_0004_00_ZS-001835_Rindfleisch: XXX": get_date_str(hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value),
                                "tf_0004_00_ZS-002081_Schweinefleisch: XXX": hfm_hack_charge_schwein_dd.value,
                                "tf_0004_00_ZS-002081_Rindfleisch: XXX": hfm_hack_charge_rind_dd.value,
                                "tf_0004_00_ZS-1441": hfm_hack_temp_in.value,
                                "dd_0004_00_ZS-001796": hfm_hack_bemerkung_dd.value
                            })

                        if hfm_mett_cb.value:
                            f_map.update({
                                "cb_0006_00": cb_val(hfm_mett_cb.value),
                                "tf_0006_00": "gewürztes Schweinemett",
                                "dd_0006_00_ZS-001799": hfm_mett_entnahmeort_dd.value,
                                "cal_0006_00_ZS-001810": get_date_str(hfm_mett_herst_tag_dd.value, hfm_mett_herst_mon_dd.value, hfm_mett_herst_jahr_dd.value),
                                "tf_0006_00_ZS-1215": hfm_mett_inhalt_in.value,
                                "dd_0006_00_ZS-001798": hfm_mett_verpackung_dd.value,
                                "tf_0006_00_ZS-1209": hfm_mett_lief_in.value,
                                "tf_0006_00_ZS-001835": get_date_str(hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value),
                                "tf_0006_00_ZS-002081": hfm_mett_charge_dd.value,
                                "tf_0006_00_ZS-1441": hfm_mett_temp_in.value,
                                "dd_0006_00_ZS-001796": hfm_mett_bemerkung_dd.value
                            })

                        if hfm_fzs_cb.value:
                            prod_s = hfm_fzs_produkt_in.value.strip()
                            mar_s = hfm_fzs_marinade_in.value.strip()
                            if prod_s and mar_s:
                                prod_mar_str_s = f"{prod_s} / {mar_s}"
                            else:
                                prod_mar_str_s = prod_s or mar_s

                            f_map.update({
                                "cb_0008_00": cb_val(hfm_fzs_cb.value),
                                "tf_0008_00": "Fleischzubereitung Schwein",
                                "tf_0008_00_ Produkt \"Marinade\"": prod_mar_str_s,
                                "dd_0008_00_ZS-001799": hfm_fzs_entnahmeort_dd.value,
                                "cal_0008_00_ZS-001810": get_date_str(hfm_fzs_herst_tag_dd.value, hfm_fzs_herst_mon_dd.value, hfm_fzs_herst_jahr_dd.value),
                                "tf_0008_00_ZS-1215": hfm_fzs_inhalt_in.value,
                                "dd_0008_00_ZS-001798": hfm_fzs_verpackung_dd.value,
                                "tf_0008_00_ZS-1209": hfm_fzs_lief_in.value,
                                "tf_0008_00_ZS-001835": get_date_str(hfm_fzs_mhd_tag_dd.value, hfm_fzs_mhd_mon_dd.value, hfm_fzs_mhd_jahr_dd.value),
                                "tf_0008_00_ZS-002081": hfm_fzs_charge_dd.value,
                                "tf_0008_00_ZS-1441": hfm_fzs_temp_in.value,
                                "dd_0008_00_ZS-001796": hfm_fzs_bemerkung_dd.value
                            })

                        if hfm_fzg_cb.value:
                            prod_g = hfm_fzg_produkt_in.value.strip()
                            mar_g = hfm_fzg_marinade_in.value.strip()
                            if prod_g and mar_g:
                                prod_mar_str_g = f"{prod_g} / {mar_g}"
                            else:
                                prod_mar_str_g = prod_g or mar_g

                            f_map.update({
                                "cb_0007_00": cb_val(hfm_fzg_cb.value),
                                "tf_0007_00": "Fleischzubereitung Geflügel",
                                "tf_0007_00_ Produkt \"Marinade\"": prod_mar_str_g,
                                "dd_0007_00_ZS-001799": hfm_fzg_entnahmeort_dd.value,
                                "cal_0007_00_ZS-001810": get_date_str(hfm_fzg_herst_tag_dd.value, hfm_fzg_herst_mon_dd.value, hfm_fzg_herst_jahr_dd.value),
                                "tf_0007_00_ZS-1215": hfm_fzg_inhalt_in.value,
                                "dd_0007_00_ZS-001798": hfm_fzg_verpackung_dd.value,
                                "tf_0007_00_ZS-1209": hfm_fzg_lief_in.value,
                                "tf_0007_00_ZS-001835": get_date_str(hfm_fzg_mhd_tag_dd.value, hfm_fzg_mhd_mon_dd.value, hfm_fzg_mhd_jahr_dd.value),
                                "tf_0007_00_ZS-002081": hfm_fzg_charge_dd.value,
                                "tf_0007_00_ZS-1441": hfm_fzg_temp_in.value,
                                "dd_0007_00_ZS-001796": hfm_fzg_bemerkung_dd.value
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

                btn_zurueck = sicherer_button("🔙 Touren", lambda e: zeige_dashboard(), "red", "white", expand=True, height=45)
                btn_speichern = sicherer_button("💾 Speichern", nur_speichern, "orange", "black", expand=True, height=45)
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