import flet as ft
import traceback
import json
import os
import datetime
import shutil

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO
    
    try:
        page.window.icon = "icon.png"
    except: pass

    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
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
        try: ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=12))
        except: pass
        page.update()

    try:
        import pypdf
        from pypdf.generic import DictionaryObject, NameObject, ArrayObject, BooleanObject

        SPEICHER_DATEI = "meine_monitoring_daten.json"
        BENUTZER_DATEI = "benutzer_daten.json"
        VORLAGEN_DATEI = "tour_vorlagen.json"

        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", size=12),
                on_click=on_click, bgcolor=bgcolor, color=color,
                expand=expand, height=height, width=width,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=5)
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
                    daten = json.load(d); return daten.get("vorname", ""), daten.get("zuname", "")
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
            v, z = lade_benutzer()
            stil_hint_weiss = ft.TextStyle(color="white54", size=12)
            
            v_in = ft.TextField(label="Vorname", hint_text="Dein Vorname", hint_style=stil_hint_weiss, value=v, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, width=300)
            z_in = ft.TextField(label="Nachname", hint_text="Dein Nachname", hint_style=stil_hint_weiss, value=z, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, width=300)
            
            btn_start = sicherer_button("Neuen Tag starten", lambda e: (speichere_benutzer(v_in.value, z_in.value), zeige_dashboard()), "red", "white", height=60, width=250)
            
            header = ft.Text(spans=[
                ft.TextSpan("REWE ", ft.TextStyle(color="red", weight="bold", size=32)),
                ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=32))
            ], text_align=ft.TextAlign.CENTER)

            ansicht.controls.extend([
                ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), 
                ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=40), ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)
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
                    adr = (markt.get("adresse") or "").strip() or "Unbenannter Markt"
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
                stil_hint_weiss = ft.TextStyle(color="white54", size=12)

                tage_opts = [""] + [f"{i:02d}" for i in range(1, 32)]
                mon_opts = [""] + [f"{i:02d}" for i in range(1, 13)]
                jahr_opts = [""] + [str(i) for i in range(2024, 2035)]
                
                charge_opts_s = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Schweinehackfleisch"]
                charge_opts_r = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Rinderhackfleisch"]
                charge_opts_g = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Geflügel"]
                entnahmeort_opts = ["Fischabteilung", "Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke"]
                verpackung_opts = ["steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel u. etikett", "Pappschale mit Kunststofffolie umwickelt", "tiefgezogene Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie umwickelt", "SB-Kunststoffverpackung"]

                def parse_datum(datum_str, def_t="", def_m="", def_j=""):
                    if not datum_str: return def_t, def_m, def_j
                    parts = datum_str.split(".")
                    if len(parts) == 3: return parts[0], parts[1], parts[2]
                    return def_t, def_m, def_j

                def get_date_str(t, m, j):
                    t = (t or "").strip(); m = (m or "").strip(); j = (j or "").strip()
                    if not t and not m and not j: return ""
                    return f"{t}.{m}.{j}"

                def erstelle_combo(label_text, wert, optionen, groesse=12, ausdehnbar=1, breite=None, on_change_func=None):
                    def on_txt_change(e):
                        if on_change_func: on_change_func(e)
                    combo = ft.TextField(
                        label=label_text, value=wert, color="yellow", 
                        text_style=ft.TextStyle(size=groesse, color="yellow"), label_style=stil_label_weiss, 
                        border_color="white", expand=ausdehnbar if breite is None else False, width=breite, content_padding=5, 
                        on_change=on_txt_change
                    )
                    items = []
                    for opt in optionen:
                        def erstelle_klick(txt):
                            def klick(e):
                                combo.value = txt; combo.update()
                                if on_change_func: on_change_func(e)
                            return klick
                        items.append(ft.PopupMenuItem(content=ft.Text(opt), on_click=erstelle_klick(opt)))
                    pb = ft.PopupMenuButton(items=items, icon="arrow_drop_down", icon_color="white")
                    combo.suffix = pb 
                    return combo

                def hat_charge_wert(val):
                    return bool(val and val != "Bitte eingeben")

                def cb_row(links, rechts):
                    return ft.Row([ft.Container(links, expand=1), ft.Container(rechts, expand=1)], vertical_alignment=ft.CrossAxisAlignment.CENTER)

                # --- 1. STAMMDATEN FELDER ---
                d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                tag_dd = erstelle_combo("Tag", d_tag, tage_opts, breite=95)
                mon_dd = erstelle_combo("Mon", d_mon, mon_opts, breite=95)
                jahr_dd = erstelle_combo("Jahr", d_jahr, jahr_opts, ausdehnbar=True)

                datum_row = ft.Column([
                    ft.Text("Datum der Probenahme", color="white", weight="bold"),
                    ft.Row([tag_dd, mon_dd, jahr_dd])
                ])

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
                    
                    se_okz_hat_daten = False
                    for i in range(1, 4):
                        if (se_okz_controls[i]["ort"].value or "").strip(): se_okz_hat_daten = True

                    hfm_hack_hat_daten = bool((hfm_hack_temp_in.value or "").strip() or (hfm_hack_mhd_s_tag_dd.value or "").strip() or (hfm_hack_mhd_r_tag_dd.value or "").strip() or hat_charge_wert(hfm_hack_charge_schwein_dd.value) or hat_charge_wert(hfm_hack_charge_rind_dd.value))
                    hfm_mett_hat_daten = bool((hfm_mett_temp_in.value or "").strip() or (hfm_mett_mhd_tag_dd.value or "").strip() or hat_charge_wert(hfm_mett_charge_dd.value))
                    hfm_fzs_hat_daten = bool((hfm_fzs_temp_in.value or "").strip() or (hfm_fzs_mhd_tag_dd.value or "").strip() or hat_charge_wert(hfm_fzs_charge_dd.value))
                    hfm_fzg_hat_daten = bool((hfm_fzg_temp_in.value or "").strip() or (hfm_fzg_mhd_tag_dd.value or "").strip() or hat_charge_wert(hfm_fzg_charge_dd.value))
                    hfm_bio_hat_daten = bool((hfm_bio_temp_in.value or "").strip() or (hfm_bio_mhd_s_tag_dd.value or "").strip() or (hfm_bio_mhd_r_tag_dd.value or "").strip() or hat_charge_wert(hfm_bio_charge_schwein_dd.value) or hat_charge_wert(hfm_bio_charge_rind_dd.value))
                    
                    og_hat_daten = False
                    for i in range(1, 6):
                        if (og_controls[i]["name"].value or "").strip() or (og_controls[i]["temp"].value or "").strip() or (og_controls[i]["v_t"].value or "").strip():
                            og_hat_daten = True
                    
                    tw_braucht_warnung = tw_hat_daten and not tw_kalt_cb.value
                    se_braucht_warnung = se_hat_daten and not se_kalt_cb.value
                    se_okz_braucht_warnung = se_okz_hat_daten and not se_okz_cb.value
                    hfm_hack_braucht_warnung = hfm_hack_hat_daten and not hfm_hack_cb.value
                    hfm_mett_braucht_warnung = hfm_mett_hat_daten and not hfm_mett_cb.value
                    hfm_fzs_braucht_warnung = hfm_fzs_hat_daten and not hfm_fzs_cb.value
                    hfm_fzg_braucht_warnung = hfm_fzg_hat_daten and not hfm_fzg_cb.value
                    hfm_bio_braucht_warnung = hfm_bio_hat_daten and not hfm_bio_cb.value
                    og_braucht_warnung = og_hat_daten and not og_cb.value
                    
                    braucht_warnung = any([tw_braucht_warnung, se_braucht_warnung, se_okz_braucht_warnung, hfm_hack_braucht_warnung, hfm_mett_braucht_warnung, hfm_fzs_braucht_warnung, hfm_fzg_braucht_warnung, hfm_bio_braucht_warnung, og_braucht_warnung])
                    
                    lims_warnung.visible = braucht_warnung
                    lims_override_cb.visible = braucht_warnung
                    if not braucht_warnung: lims_override_cb.value = False
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

                def format_gramm_blur(e):
                    val = (e.control.value or "").strip()
                    if val and not val.lower().endswith("g") and not val.lower().endswith("ml"):
                        e.control.value = val + " g"
                        e.control.update()

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
                cb_auff_unterbau = ft.Checkbox(label="Unterbauspeicher", value=aktuelle_daten.get("cb_auff_unterbau", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
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

                # --- 3b. SCHERBENEIS - OKZ ---
                se_okz_cb = ft.Checkbox(label="Abklatschproben Scherbeneis", value=aktuelle_daten.get("se_okz_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                se_okz_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("se_okz_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])
                
                se_okz_status_opts = ["R+D", "R", "P", "-"]
                se_okz_objekt_opts = ["Eiswanne innen rechts", "Eiswanne innen links", "Auswurfrohr", "Eisschaufel", "Eiswanne", "Eismaschine innen", "Klappe/Deckel", "Sonstiges"]
                se_okz_ort_opts = ["Fischabteilung", "Metzgerei", "Produktionsbereich", "Kühlraum"]
                
                se_okz_defaults = {
                    1: {"obj": "Eiswanne innen rechts", "abk": True, "tup": True},
                    2: {"obj": "Eiswanne innen links", "abk": True, "tup": True},
                    3: {"obj": "Auswurfrohr", "abk": True, "tup": True}
                }
                
                se_okz_controls = {}
                se_okz_felder = []
                
                for i in range(1, 4):
                    idx = f"{i:02d}"
                    s_dd = erstelle_combo("Status", aktuelle_daten.get(f"se_okz_status_{idx}", "R+D"), se_okz_status_opts)
                    obj_dd = erstelle_combo("Objekt", aktuelle_daten.get(f"se_okz_objekt_{idx}", se_okz_defaults[i]["obj"]), se_okz_objekt_opts)
                    ort_dd = erstelle_combo("Probenahmeort", aktuelle_daten.get(f"se_okz_ort_{idx}", ""), se_okz_ort_opts, on_change_func=pruefe_lims_warnung)
                    abk_cb = ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"se_okz_abklatsch_{idx}", se_okz_defaults[i]["abk"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    tup_cb = ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"se_okz_tupfer_{idx}", se_okz_defaults[i]["tup"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    
                    se_okz_controls[i] = {"status": s_dd, "objekt": obj_dd, "ort": ort_dd, "abklatsch": abk_cb, "tupfer": tup_cb}
                    se_okz_felder.append(ft.Text(f"Probe {i}", color="yellow", weight="bold", size=14))
                    se_okz_felder.append(ft.Row([s_dd, obj_dd]))
                    se_okz_felder.append(ft.Row([ort_dd]))
                    se_okz_felder.append(ft.Row([abk_cb, tup_cb], alignment=ft.MainAxisAlignment.SPACE_AROUND))
                    se_okz_felder.append(ft.Divider(color="white24"))

                # --- 4. HFM - HACKFLEISCH GEMISCHT ---
                hfm_hack_cb = ft.Checkbox(label="Hackfleisch gemischt", value=aktuelle_daten.get("hfm_hack_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_hack_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_hack_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_h_t, hfm_h_m, hfm_h_j = parse_datum(aktuelle_daten.get("hfm_hack_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_hack_herst_tag_dd = erstelle_combo("Tag", hfm_h_t, tage_opts, ausdehnbar=3)
                hfm_hack_herst_mon_dd = erstelle_combo("Mon", hfm_h_m, mon_opts, ausdehnbar=3)
                hfm_hack_herst_jahr_dd = erstelle_combo("Jahr", hfm_h_j, jahr_opts, ausdehnbar=4)

                mhd_s_t, mhd_s_m, mhd_s_j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_schwein", ""))
                hfm_hack_mhd_s_tag_dd = erstelle_combo("Tag", mhd_s_t, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                hfm_hack_mhd_s_mon_dd = erstelle_combo("Mon", mhd_s_m, mon_opts, ausdehnbar=3)
                hfm_hack_mhd_s_jahr_dd = erstelle_combo("Jahr", mhd_s_j, jahr_opts, ausdehnbar=4)

                mhd_r_t, mhd_r_m, mhd_r_j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_rind", ""))
                hfm_hack_mhd_r_tag_dd = erstelle_combo("Tag", mhd_r_t, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                hfm_hack_mhd_r_mon_dd = erstelle_combo("Mon", mhd_r_m, mon_opts, ausdehnbar=3)
                hfm_hack_mhd_r_jahr_dd = erstelle_combo("Jahr", mhd_r_j, jahr_opts, ausdehnbar=4)

                hfm_hack_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_hack_inhalt", "jeweils ca. 200 g"), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True, on_blur=format_gramm_blur)
                hfm_hack_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_hack_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_hack_lief_schwein_in = ft.TextField(label="Lieferant (Schwein)", value=aktuelle_daten.get("hfm_hack_lief_schwein", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_hack_lief_rind_in = ft.TextField(label="Lieferant (Rind)", value=aktuelle_daten.get("hfm_hack_lief_rind", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                hfm_hack_charge_schwein_dd = erstelle_combo("Charge Schwein", aktuelle_daten.get("hfm_hack_charge_schwein", "Bitte eingeben"), charge_opts_s, on_change_func=pruefe_lims_warnung)
                hfm_hack_charge_rind_dd = erstelle_combo("Charge Rind", aktuelle_daten.get("hfm_hack_charge_rind", "Bitte eingeben"), charge_opts_r, on_change_func=pruefe_lims_warnung)
                
                hfm_hack_temp_in = ft.TextField(label="Probenahmetemperatur", hint_text="(Soll Schwein/Rind: <+7°C)", hint_style=stil_hint_weiss, value=aktuelle_daten.get("hfm_hack_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_hack_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_hack_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 5. HFM - GEWÜRZTES SCHWEINEMETT ---
                hfm_mett_cb = ft.Checkbox(label="Gewürztes Schweinemett", value=aktuelle_daten.get("hfm_mett_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_mett_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_mett_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_m_t, hfm_m_m, hfm_m_j = parse_datum(aktuelle_daten.get("hfm_mett_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_mett_herst_tag_dd = erstelle_combo("Tag", hfm_m_t, tage_opts, ausdehnbar=3)
                hfm_mett_herst_mon_dd = erstelle_combo("Mon", hfm_m_m, mon_opts, ausdehnbar=3)
                hfm_mett_herst_jahr_dd = erstelle_combo("Jahr", hfm_m_j, jahr_opts, ausdehnbar=4)

                mhd_mett_t, mhd_mett_m, mhd_mett_j = parse_datum(aktuelle_daten.get("hfm_mett_mhd", ""))
                hfm_mett_mhd_tag_dd = erstelle_combo("Tag", mhd_mett_t, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                hfm_mett_mhd_mon_dd = erstelle_combo("Mon", mhd_mett_m, mon_opts, ausdehnbar=3)
                hfm_mett_mhd_jahr_dd = erstelle_combo("Jahr", mhd_mett_j, jahr_opts, ausdehnbar=4)

                hfm_mett_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_mett_inhalt", "ca. 200 g"), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True, on_blur=format_gramm_blur)
                hfm_mett_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_mett_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_mett_lief_in = ft.TextField(label="Lieferant Rohware", value=aktuelle_daten.get("hfm_mett_lief", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_mett_charge_dd = erstelle_combo("Charge Rohware", aktuelle_daten.get("hfm_mett_charge", "Bitte eingeben"), charge_opts_s, on_change_func=pruefe_lims_warnung)
                
                hfm_mett_temp_in = ft.TextField(label="Probenahmetemperatur", hint_text="(Soll Schwein: <+7°C)", hint_style=stil_hint_weiss, value=aktuelle_daten.get("hfm_mett_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_mett_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_mett_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 6. HFM - FZ SCHWEIN ---
                hfm_fzs_cb = ft.Checkbox(label="Fleischzubereitung Schwein", value=aktuelle_daten.get("hfm_fzs_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_fzs_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_fzs_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_fzs_produkt_in = ft.TextField(label="Produkt", hint_text="z. B. Schweine Nacken", hint_style=ft.TextStyle(color="white", size=12), value=aktuelle_daten.get("hfm_fzs_produkt", ""), color="yellow", label_style=stil_label_weiss, border_color="white", on_change=pruefe_lims_warnung, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzs_marinade_in = ft.TextField(label="Marinade", value=aktuelle_daten.get("hfm_fzs_marinade", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                hfm_fzs_h_t, hfm_fzs_h_m, hfm_fzs_h_j = parse_datum(aktuelle_daten.get("hfm_fzs_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_fzs_herst_tag_dd = erstelle_combo("Tag", hfm_fzs_h_t, tage_opts, ausdehnbar=3)
                hfm_fzs_herst_mon_dd = erstelle_combo("Mon", hfm_fzs_h_m, mon_opts, ausdehnbar=3)
                hfm_fzs_herst_jahr_dd = erstelle_combo("Jahr", hfm_fzs_h_j, jahr_opts, ausdehnbar=4)

                mhd_fzs_t, mhd_fzs_m, mhd_fzs_j = parse_datum(aktuelle_daten.get("hfm_fzs_mhd", ""))
                hfm_fzs_mhd_tag_dd = erstelle_combo("Tag", mhd_fzs_t, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                hfm_fzs_mhd_mon_dd = erstelle_combo("Mon", mhd_fzs_m, mon_opts, ausdehnbar=3)
                hfm_fzs_mhd_jahr_dd = erstelle_combo("Jahr", mhd_fzs_j, jahr_opts, ausdehnbar=4)

                hfm_fzs_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_fzs_inhalt", "ca. 200 g"), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True, on_blur=format_gramm_blur)
                hfm_fzs_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_fzs_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_fzs_lief_in = ft.TextField(label="Lieferant Rohware", value=aktuelle_daten.get("hfm_fzs_lief", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzs_charge_dd = erstelle_combo("Charge Rohware", aktuelle_daten.get("hfm_fzs_charge", "Bitte eingeben"), charge_opts_s, on_change_func=pruefe_lims_warnung)
                
                hfm_fzs_temp_in = ft.TextField(label="Probenahmetemperatur", hint_text="(Soll Schwein: <+7°C)", hint_style=stil_hint_weiss, value=aktuelle_daten.get("hfm_fzs_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzs_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_fzs_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 7. HFM - FZ GEFLÜGEL ---
                hfm_fzg_cb = ft.Checkbox(label="Fleischzubereitung Geflügel", value=aktuelle_daten.get("hfm_fzg_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_fzg_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_fzg_entnahmeort", "Kühlraum"), entnahmeort_opts)
                
                hfm_fzg_produkt_in = ft.TextField(label="Produkt", hint_text="z. B. Hähnchenbrust", hint_style=ft.TextStyle(color="white", size=12), value=aktuelle_daten.get("hfm_fzg_produkt", ""), color="yellow", label_style=stil_label_weiss, border_color="white", on_change=pruefe_lims_warnung, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzg_marinade_in = ft.TextField(label="Marinade", value=aktuelle_daten.get("hfm_fzg_marinade", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                hfm_fzg_h_t, hfm_fzg_h_m, hfm_fzg_h_j = parse_datum(aktuelle_daten.get("hfm_fzg_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_fzg_herst_tag_dd = erstelle_combo("Tag", hfm_fzg_h_t, tage_opts, ausdehnbar=3)
                hfm_fzg_herst_mon_dd = erstelle_combo("Mon", hfm_fzg_h_m, mon_opts, ausdehnbar=3)
                hfm_fzg_herst_jahr_dd = erstelle_combo("Jahr", hfm_fzg_h_j, jahr_opts, ausdehnbar=4)

                mhd_fzg_t, mhd_fzg_m, mhd_fzg_j = parse_datum(aktuelle_daten.get("hfm_fzg_mhd", ""))
                hfm_fzg_mhd_tag_dd = erstelle_combo("Tag", mhd_fzg_t, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                hfm_fzg_mhd_mon_dd = erstelle_combo("Mon", mhd_fzg_m, mon_opts, ausdehnbar=3)
                hfm_fzg_mhd_jahr_dd = erstelle_combo("Jahr", mhd_fzg_j, jahr_opts, ausdehnbar=4)

                hfm_fzg_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_fzg_inhalt", "ca. 200 g"), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True, on_blur=format_gramm_blur)
                hfm_fzg_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_fzg_verpackung", "steriler Probenbeutel"), verpackung_opts)
                
                hfm_fzg_lief_in = ft.TextField(label="Lieferant Rohware", value=aktuelle_daten.get("hfm_fzg_lief", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzg_charge_dd = erstelle_combo("Charge Rohware", aktuelle_daten.get("hfm_fzg_charge", "Bitte eingeben"), charge_opts_g, on_change_func=pruefe_lims_warnung)
                
                hfm_fzg_temp_in = ft.TextField(label="Probenahmetemperatur", hint_text="(Soll Geflügel: <+4°C)", hint_style=stil_hint_weiss, value=aktuelle_daten.get("hfm_fzg_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_fzg_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_fzg_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 8. HFM - BIO HACK ---
                hfm_bio_cb = ft.Checkbox(label="Bio-Hackfleisch", value=aktuelle_daten.get("hfm_bio_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_bio_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_bio_entnahmeort", "Produktionsraum"), entnahmeort_opts)
                
                hfm_b_t, hfm_b_m, hfm_b_j = parse_datum(aktuelle_daten.get("hfm_bio_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                hfm_bio_herst_tag_dd = erstelle_combo("Tag", hfm_b_t, tage_opts, ausdehnbar=3)
                hfm_bio_herst_mon_dd = erstelle_combo("Mon", hfm_b_m, mon_opts, ausdehnbar=3)
                hfm_bio_herst_jahr_dd = erstelle_combo("Jahr", hfm_b_j, jahr_opts, ausdehnbar=4)

                mhd_b_s_t, mhd_b_s_m, mhd_b_s_j = parse_datum(aktuelle_daten.get("hfm_bio_mhd_schwein", ""))
                hfm_bio_mhd_s_tag_dd = erstelle_combo("Tag", mhd_b_s_t, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                hfm_bio_mhd_s_mon_dd = erstelle_combo("Mon", mhd_b_s_m, mon_opts, ausdehnbar=3)
                hfm_bio_mhd_s_jahr_dd = erstelle_combo("Jahr", mhd_b_s_j, jahr_opts, ausdehnbar=4)

                mhd_b_r_t, mhd_b_r_m, mhd_b_r_j = parse_datum(aktuelle_daten.get("hfm_bio_mhd_rind", ""))
                hfm_bio_mhd_r_tag_dd = erstelle_combo("Tag", mhd_b_r_t, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                hfm_bio_mhd_r_mon_dd = erstelle_combo("Mon", mhd_b_r_m, mon_opts, ausdehnbar=3)
                hfm_bio_mhd_r_jahr_dd = erstelle_combo("Jahr", mhd_b_r_j, jahr_opts, ausdehnbar=4)

                hfm_bio_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_bio_inhalt", "jeweils ca. 200 g"), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True, on_blur=format_gramm_blur)
                hfm_bio_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_bio_verpackung", "steriler Probenbecher"), verpackung_opts)
                
                hfm_bio_lief_schwein_in = ft.TextField(label="Lieferant (Schwein)", value=aktuelle_daten.get("hfm_bio_lief_schwein", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_bio_lief_rind_in = ft.TextField(label="Lieferant (Rind)", value=aktuelle_daten.get("hfm_bio_lief_rind", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                hfm_bio_charge_schwein_dd = erstelle_combo("Charge Schwein", aktuelle_daten.get("hfm_bio_charge_schwein", "Bitte eingeben"), charge_opts_s, on_change_func=pruefe_lims_warnung)
                hfm_bio_charge_rind_dd = erstelle_combo("Charge Rind", aktuelle_daten.get("hfm_bio_charge_rind", "Bitte eingeben"), charge_opts_r, on_change_func=pruefe_lims_warnung)
                
                hfm_bio_temp_in = ft.TextField(label="Probenahmetemperatur", hint_text="(Soll Schwein/Rind: <+7°C)", hint_style=stil_hint_weiss, value=aktuelle_daten.get("hfm_bio_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                hfm_bio_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_bio_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])

                # --- 9. HFM - OKZ ---
                hfm_okz_cb = ft.Checkbox(label="Abklatschproben HFM", value=aktuelle_daten.get("hfm_okz_cb", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                hfm_okz_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_okz_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])
                
                okz_status_opts = ["R+D", "R", "P", "-"]
                okz_objekt_opts = ["Fleischwolf-Auflage", "Fleischwolf-Lochscheibe", "Fleischwolf-Auswurf", "Fleischwolf-Spirale", "Wand am Fleischwolf", "Hackstecher", "Schaufel", "Thekenschale", "Messer", "Schneidebrett", "Auflage Knochensäge", "Tisch", "Flesichwanne", "Kühlhausgriff", "Schüssel", "Seifenspender"]
                okz_ort_opts = ["Kühlraum", "Produktionsbereich", "Theke"]
                
                okz_defaults = {
                    1: {"obj": "Fleischwolf-Auflage", "abk": True, "tup": False},
                    2: {"obj": "Fleischwolf-Auswurf", "abk": True, "tup": True},
                    3: {"obj": "Thekenschale", "abk": True, "tup": False},
                    4: {"obj": "Hackstecher", "abk": True, "tup": True},
                    5: {"obj": "Messer", "abk": True, "tup": False},
                    6: {"obj": "Schneidebrett", "abk": True, "tup": False},
                    7: {"obj": "Wand am Fleischwolf", "abk": True, "tup": True},
                    8: {"obj": "", "abk": False, "tup": False},
                    9: {"obj": "", "abk": False, "tup": False},
                    10: {"obj": "", "abk": False, "tup": False}
                }

                okz_controls = {}
                okz_felder = []
                
                for i in range(1, 11):
                    idx = f"{i:02d}"
                    s_dd = erstelle_combo("Status", aktuelle_daten.get(f"okz_status_{idx}", "R+D"), okz_status_opts)
                    obj_dd = erstelle_combo("Objekt", aktuelle_daten.get(f"okz_objekt_{idx}", okz_defaults[i]["obj"]), okz_objekt_opts)
                    ort_dd = erstelle_combo("Probenahmeort", aktuelle_daten.get(f"okz_ort_{idx}", ""), okz_ort_opts)
                    abk_cb = ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"okz_abklatsch_{idx}", okz_defaults[i]["abk"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    tup_cb = ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"okz_tupfer_{idx}", okz_defaults[i]["tup"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    okz_controls[idx] = {"status": s_dd, "objekt": obj_dd, "ort": ort_dd, "abklatsch": abk_cb, "tupfer": tup_cb}
                    okz_felder.append(ft.Text(f"Probe {i}", color="yellow", weight="bold", size=14))
                    okz_felder.append(ft.Row([s_dd, obj_dd]))
                    okz_felder.append(ft.Row([ort_dd]))
                    okz_felder.append(ft.Row([abk_cb, tup_cb], alignment=ft.MainAxisAlignment.SPACE_AROUND))
                    okz_felder.append(ft.Divider(color="white24"))

                # --- 10. OG (OBST/GEMÜSE) UNTERMENÜ ---
                og_ort_opts = ["Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Kühlraum", "SB-Theke", "Salatbar", "Saftpresse"]
                og_verpackung_opts = ["SB-Kunststoffverpackung", "SB-Styroporverpackung", "Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie", "steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel"]
                
                og_cb = ft.Checkbox(label="Obst-/Gemüse Convenience", value=aktuelle_daten.get("og_cb", False), on_change=pruefe_lims_warnung, label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                
                og_controls = {}
                og_felder = []
                
                for i in range(1, 6):
                    idx = f"{i:02d}"
                    og_name_in = ft.TextField(label=f"Name Teilprobe {i}", value=aktuelle_daten.get(f"og_name_{idx}", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True, on_change=pruefe_lims_warnung)
                    ort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get(f"og_ort_{idx}", ""), og_ort_opts)
                    h_t_val, h_m_val, h_j_val = parse_datum(aktuelle_daten.get(f"og_herst_{idx}", ""), "", "", "")
                    h_t = erstelle_combo("Tag", h_t_val, tage_opts, ausdehnbar=3)
                    h_m = erstelle_combo("Mon", h_m_val, mon_opts, ausdehnbar=3)
                    h_j = erstelle_combo("Jahr", h_j_val, jahr_opts, ausdehnbar=4)
                    v_t_val, v_m_val, v_j_val = parse_datum(aktuelle_daten.get(f"og_verb_{idx}", ""), "", "", "")
                    v_t = erstelle_combo("Tag", v_t_val, tage_opts, ausdehnbar=3, on_change_func=pruefe_lims_warnung)
                    v_m = erstelle_combo("Mon", v_m_val, mon_opts, ausdehnbar=3)
                    v_j = erstelle_combo("Jahr", v_j_val, jahr_opts, ausdehnbar=4)
                    inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get(f"og_inhalt_{idx}", ""), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True, on_blur=format_gramm_blur)
                    verp_dd = erstelle_combo("Verpackung", aktuelle_daten.get(f"og_verp_{idx}", ""), og_verpackung_opts)
                    temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get(f"og_temp_{idx}", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                    og_controls[i] = {"name": og_name_in, "ort": ort_dd, "h_t": h_t, "h_m": h_m, "h_j": h_j, "v_t": v_t, "v_m": v_m, "v_j": v_j, "inhalt": inhalt_in, "verpackung": verp_dd, "temp": temp_in}
                    og_felder.append(ft.Text(f"Teilprobe {i}", color="yellow", weight="bold", size=14))
                    og_felder.append(og_name_in)
                    og_felder.append(ort_dd)
                    og_felder.append(ft.Text("Herstellungsdatum:", color="white", size=12))
                    og_felder.append(ft.Row([h_t, h_m, h_j]))
                    og_felder.append(ft.Text("Verbrauchsdatum:", color="white", size=12))
                    og_felder.append(ft.Row([v_t, v_m, v_j]))
                    og_felder.append(inhalt_in)
                    og_felder.append(verp_dd)
                    og_felder.append(temp_in)
                    og_felder.append(ft.Divider(color="white24"))

                # --- 11. OG - OKZ ---
                og_okz_cb = ft.Checkbox(label="Abklatschproben OG", value=aktuelle_daten.get("og_okz_cb", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
                og_okz_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("og_okz_bemerkung", "Bitte eingeben"), ["Bitte eingeben", "Keine Besonderheiten"])
                og_okz_anmerkung_in = ft.TextField(label="Anmerkung", value=aktuelle_daten.get("og_okz_anmerkung", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, expand=True)
                
                og_okz_status_opts = ["R+D", "R", "P", "-"]
                og_okz_objekt_opts = ["Schneidebrett", "Messer", "Saftpresse Auffanggitter", "Saftpresse Rückwand", "Saftpresse Auslass", "Waagenauflage", "Schüssel", "Löffel", "GN-Behälter"]
                og_okz_ort_opts = ["Kühlraum", "Produktionsbereich", "Theke"]
                
                og_okz_defaults = {
                    1: {"obj": "Schneidebrett", "abk": True, "tup": True},
                    2: {"obj": "Messer", "abk": True, "tup": True},
                    3: {"obj": "Waagenauflage", "abk": True, "tup": False},
                    4: {"obj": "Schüssel", "abk": True, "tup": False},
                    5: {"obj": "Löffel", "abk": True, "tup": False}
                }
                
                og_okz_controls = {}
                og_okz_felder = []
                
                for i in range(1, 6):
                    idx = f"{i:02d}"
                    if i == 2: og_okz_felder.append(ft.Text("💡 Info: Bei Saftpresse bitte hier auswählen.", color="white54", italic=True, size=12))
                    s_dd = erstelle_combo("Status", aktuelle_daten.get(f"og_okz_status_{idx}", "R+D"), og_okz_status_opts)
                    obj_dd = erstelle_combo("Objekt", aktuelle_daten.get(f"og_okz_objekt_{idx}", og_okz_defaults[i]["obj"]), og_okz_objekt_opts)
                    ort_dd = erstelle_combo("Probenahmeort", aktuelle_daten.get(f"og_okz_ort_{idx}", ""), og_okz_ort_opts)
                    abk_cb = ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"og_okz_abklatsch_{idx}", og_okz_defaults[i]["abk"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    tup_cb = ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"og_okz_tupfer_{idx}", og_okz_defaults[i]["tup"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    og_okz_controls[idx] = {"status": s_dd, "objekt": obj_dd, "ort": ort_dd, "abklatsch": abk_cb, "tupfer": tup_cb}
                    og_okz_felder.append(ft.Text(f"Probe {i}", color="yellow", weight="bold", size=14))
                    og_okz_felder.append(ft.Row([s_dd, obj_dd]))
                    og_okz_felder.append(ft.Row([ort_dd]))
                    og_okz_felder.append(ft.Row([abk_cb, tup_cb], alignment=ft.MainAxisAlignment.SPACE_AROUND))
                    og_okz_felder.append(ft.Divider(color="white24"))

                # --- 12. VORLAGEN LOGIK ---
                alle_vorlagen = lade_vorlagen()
                vorlagen_status = ft.Text("", weight="bold") 
                
                vl_dd = ft.Dropdown(options=[ft.dropdown.Option(k) for k in alle_vorlagen.keys()], expand=True, dense=True, content_padding=10)
                
                def lade_v(e):
                    if not vl_dd.value: return
                    v = alle_vorlagen.get(vl_dd.value, {})
                    
                    try:
                        h_t, h_m, h_j = heute_str.split(".")
                        tag_dd.value = h_t; mon_dd.value = h_m; jahr_dd.value = h_j
                        hfm_hack_herst_tag_dd.value = h_t; hfm_hack_herst_mon_dd.value = h_m; hfm_hack_herst_jahr_dd.value = h_j
                        hfm_mett_herst_tag_dd.value = h_t; hfm_mett_herst_mon_dd.value = h_m; hfm_mett_herst_jahr_dd.value = h_j
                        hfm_fzs_herst_tag_dd.value = h_t; hfm_fzs_herst_mon_dd.value = h_m; hfm_fzs_herst_jahr_dd.value = h_j
                        hfm_fzg_herst_tag_dd.value = h_t; hfm_fzg_herst_mon_dd.value = h_m; hfm_fzg_herst_jahr_dd.value = h_j
                        hfm_bio_herst_tag_dd.value = h_t; hfm_bio_herst_mon_dd.value = h_m; hfm_bio_herst_jahr_dd.value = h_j
                    except: pass
                    
                    adr_in.value = ""; nr_in.value = ""; auft_in.value = ""
                    tw_kalt_cb.value = False; tw_zeit_in.value = ""; tw_temp_in.value = ""; tw_tempkonst_in.value = ""
                    se_kalt_cb.value = False; se_zeit_in.value = ""; se_temp_in.value = ""
                    
                    hfm_hack_cb.value = False; hfm_hack_temp_in.value = ""
                    hfm_hack_lief_schwein_in.value = ""; hfm_hack_lief_rind_in.value = ""
                    hfm_hack_mhd_s_tag_dd.value = ""; hfm_hack_mhd_s_mon_dd.value = ""; hfm_hack_mhd_s_jahr_dd.value = ""
                    hfm_hack_mhd_r_tag_dd.value = ""; hfm_hack_mhd_r_mon_dd.value = ""; hfm_hack_mhd_r_jahr_dd.value = ""

                    hfm_mett_cb.value = False; hfm_mett_temp_in.value = ""; hfm_mett_lief_in.value = ""
                    hfm_mett_mhd_tag_dd.value = ""; hfm_mett_mhd_mon_dd.value = ""; hfm_mett_mhd_jahr_dd.value = ""

                    hfm_fzs_cb.value = False; hfm_fzs_temp_in.value = ""; hfm_fzs_lief_in.value = ""; hfm_fzs_produkt_in.value = ""; hfm_fzs_marinade_in.value = ""
                    hfm_fzs_mhd_tag_dd.value = ""; hfm_fzs_mhd_mon_dd.value = ""; hfm_fzs_mhd_jahr_dd.value = ""

                    hfm_fzg_cb.value = False; hfm_fzg_temp_in.value = ""; hfm_fzg_lief_in.value = ""; hfm_fzg_produkt_in.value = ""; hfm_fzg_marinade_in.value = ""
                    hfm_fzg_mhd_tag_dd.value = ""; hfm_fzg_mhd_mon_dd.value = ""; hfm_fzg_mhd_jahr_dd.value = ""

                    hfm_bio_cb.value = False; hfm_bio_temp_in.value = ""; hfm_bio_lief_schwein_in.value = ""; hfm_bio_lief_rind_in.value = ""
                    hfm_bio_mhd_s_tag_dd.value = ""; hfm_bio_mhd_s_mon_dd.value = ""; hfm_bio_mhd_s_jahr_dd.value = ""
                    hfm_bio_mhd_r_tag_dd.value = ""; hfm_bio_mhd_r_mon_dd.value = ""; hfm_bio_mhd_r_jahr_dd.value = ""
                    
                    se_okz_cb.value = False; se_okz_bemerkung_dd.value = "Bitte eingeben"
                    for i in range(1, 4):
                        ctrls = se_okz_controls[i]
                        ctrls["status"].value = "R+D"
                        ctrls["objekt"].value = se_okz_defaults[i]["obj"]
                        ctrls["ort"].value = ""
                        ctrls["abklatsch"].value = se_okz_defaults[i]["abk"]
                        ctrls["tupfer"].value = se_okz_defaults[i]["tup"]

                    hfm_okz_cb.value = False; hfm_okz_bemerkung_dd.value = "Bitte eingeben"
                    for idx_str, ctrls in okz_controls.items():
                        i = int(idx_str)
                        ctrls["status"].value = "R+D"
                        ctrls["objekt"].value = okz_defaults[i]["obj"]
                        ctrls["ort"].value = ""
                        ctrls["abklatsch"].value = okz_defaults[i]["abk"]
                        ctrls["tupfer"].value = okz_defaults[i]["tup"]
                        
                    og_cb.value = False
                    for i in range(1, 6):
                        ctrls = og_controls[i]
                        ctrls["name"].value = ""; ctrls["ort"].value = ""
                        ctrls["h_t"].value = ""; ctrls["h_m"].value = ""; ctrls["h_j"].value = ""
                        ctrls["v_t"].value = ""; ctrls["v_m"].value = ""; ctrls["v_j"].value = ""
                        ctrls["inhalt"].value = ""; ctrls["verpackung"].value = ""; ctrls["temp"].value = ""

                    og_okz_cb.value = False; og_okz_bemerkung_dd.value = "Bitte eingeben"; og_okz_anmerkung_in.value = ""
                    for idx_str, ctrls in og_okz_controls.items():
                        i = int(idx_str)
                        ctrls["status"].value = "R+D"
                        ctrls["objekt"].value = og_okz_defaults[i]["obj"]
                        ctrls["ort"].value = ""
                        ctrls["abklatsch"].value = og_okz_defaults[i]["abk"]
                        ctrls["tupfer"].value = og_okz_defaults[i]["tup"]
                    
                    for cb in [cb_pn, cb_zwei, cb_sensor, cb_knie, cb_ein, cb_ein_g, cb_eck, cb_auff_ja, cb_auff_nein, cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf, cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich, cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst, se_cb_eiswanne, se_cb_ozon]: cb.value = False
                    tw_auff_sonstiges_in.value = ""; se_tech_sonst_in.value = ""; se_auff_sonst_in.value = ""
                    
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

                    if "hfm_hack_entnahmeort" in v: hfm_hack_entnahmeort_dd.value = v["hfm_hack_entnahmeort"]
                    if "hfm_hack_inhalt" in v: hfm_hack_inhalt_in.value = v["hfm_hack_inhalt"]
                    if "hfm_hack_verpackung" in v: hfm_hack_verpackung_dd.value = v["hfm_hack_verpackung"]
                    if "hfm_hack_charge_schwein" in v: hfm_hack_charge_schwein_dd.value = v["hfm_hack_charge_schwein"]
                    if "hfm_hack_charge_rind" in v: hfm_hack_charge_rind_dd.value = v["hfm_hack_charge_rind"]
                    if "hfm_hack_bemerkung" in v: hfm_hack_bemerkung_dd.value = v["hfm_hack_bemerkung"]
                    if "hfm_hack_lief_schwein" in v: hfm_hack_lief_schwein_in.value = v["hfm_hack_lief_schwein"]
                    if "hfm_hack_lief_rind" in v: hfm_hack_lief_rind_in.value = v["hfm_hack_lief_rind"]

                    if "hfm_mett_entnahmeort" in v: hfm_mett_entnahmeort_dd.value = v["hfm_mett_entnahmeort"]
                    if "hfm_mett_inhalt" in v: hfm_mett_inhalt_in.value = v["hfm_mett_inhalt"]
                    if "hfm_mett_verpackung" in v: hfm_mett_verpackung_dd.value = v["hfm_mett_verpackung"]
                    if "hfm_mett_charge" in v: hfm_mett_charge_dd.value = v["hfm_mett_charge"]
                    if "hfm_mett_bemerkung" in v: hfm_mett_bemerkung_dd.value = v["hfm_mett_bemerkung"]
                    if "hfm_mett_lief" in v: hfm_mett_lief_in.value = v["hfm_mett_lief"]

                    if "hfm_fzs_entnahmeort" in v: hfm_fzs_entnahmeort_dd.value = v["hfm_fzs_entnahmeort"]
                    if "hfm_fzs_produkt" in v: hfm_fzs_produkt_in.value = v["hfm_fzs_produkt"]
                    if "hfm_fzs_marinade" in v: hfm_fzs_marinade_in.value = v["hfm_fzs_marinade"]
                    if "hfm_fzs_inhalt" in v: hfm_fzs_inhalt_in.value = v["hfm_fzs_inhalt"]
                    if "hfm_fzs_verpackung" in v: hfm_fzs_verpackung_dd.value = v["hfm_fzs_verpackung"]
                    if "hfm_fzs_charge" in v: hfm_fzs_charge_dd.value = v["hfm_fzs_charge"]
                    if "hfm_fzs_bemerkung" in v: hfm_fzs_bemerkung_dd.value = v["hfm_fzs_bemerkung"]
                    if "hfm_fzs_lief" in v: hfm_fzs_lief_in.value = v["hfm_fzs_lief"]

                    if "hfm_fzg_entnahmeort" in v: hfm_fzg_entnahmeort_dd.value = v["hfm_fzg_entnahmeort"]
                    if "hfm_fzg_produkt" in v: hfm_fzg_produkt_in.value = v["hfm_fzg_produkt"]
                    if "hfm_fzg_marinade" in v: hfm_fzg_marinade_in.value = v["hfm_fzg_marinade"]
                    if "hfm_fzg_inhalt" in v: hfm_fzg_inhalt_in.value = v["hfm_fzg_inhalt"]
                    if "hfm_fzg_verpackung" in v: hfm_fzg_verpackung_dd.value = v["hfm_fzg_verpackung"]
                    if "hfm_fzg_charge" in v: hfm_fzg_charge_dd.value = v["hfm_fzg_charge"]
                    if "hfm_fzg_bemerkung" in v: hfm_fzg_bemerkung_dd.value = v["hfm_fzg_bemerkung"]
                    if "hfm_fzg_lief" in v: hfm_fzg_lief_in.value = v["hfm_fzg_lief"]

                    if "hfm_bio_entnahmeort" in v: hfm_bio_entnahmeort_dd.value = v["hfm_bio_entnahmeort"]
                    if "hfm_bio_inhalt" in v: hfm_bio_inhalt_in.value = v["hfm_bio_inhalt"]
                    if "hfm_bio_verpackung" in v: hfm_bio_verpackung_dd.value = v["hfm_bio_verpackung"]
                    if "hfm_bio_charge_schwein" in v: hfm_bio_charge_schwein_dd.value = v["hfm_bio_charge_schwein"]
                    if "hfm_bio_charge_rind" in v: hfm_bio_charge_rind_dd.value = v["hfm_bio_charge_rind"]
                    if "hfm_bio_bemerkung" in v: hfm_bio_bemerkung_dd.value = v["hfm_bio_bemerkung"]
                    if "hfm_bio_lief_schwein" in v: hfm_bio_lief_schwein_in.value = v["hfm_bio_lief_schwein"]
                    if "hfm_bio_lief_rind" in v: hfm_bio_lief_rind_in.value = v["hfm_bio_lief_rind"]
                    
                    if "se_okz_bemerkung" in v: se_okz_bemerkung_dd.value = v["se_okz_bemerkung"]
                    for i in range(1, 4):
                        idx = f"{i:02d}"
                        ctrls = se_okz_controls[i]
                        if f"se_okz_status_{idx}" in v: ctrls["status"].value = v[f"se_okz_status_{idx}"]
                        if f"se_okz_objekt_{idx}" in v: ctrls["objekt"].value = v[f"se_okz_objekt_{idx}"]
                        if f"se_okz_ort_{idx}" in v: ctrls["ort"].value = v[f"se_okz_ort_{idx}"]
                        if f"se_okz_abklatsch_{idx}" in v: ctrls["abklatsch"].value = v[f"se_okz_abklatsch_{idx}"]
                        if f"se_okz_tupfer_{idx}" in v: ctrls["tupfer"].value = v[f"se_okz_tupfer_{idx}"]

                    if "hfm_okz_bemerkung" in v: hfm_okz_bemerkung_dd.value = v["hfm_okz_bemerkung"]
                    for idx_str, ctrls in okz_controls.items():
                        if f"okz_status_{idx_str}" in v: ctrls["status"].value = v[f"okz_status_{idx_str}"]
                        if f"okz_objekt_{idx_str}" in v: ctrls["objekt"].value = v[f"okz_objekt_{idx_str}"]
                        if f"okz_ort_{idx_str}" in v: ctrls["ort"].value = v[f"okz_ort_{idx_str}"]
                        if f"okz_abklatsch_{idx_str}" in v: ctrls["abklatsch"].value = v[f"okz_abklatsch_{idx_str}"]
                        if f"okz_tupfer_{idx_str}" in v: ctrls["tupfer"].value = v[f"okz_tupfer_{idx_str}"]
                        
                    for i in range(1, 6):
                        ctrls = og_controls[i]
                        idx = f"{i:02d}"
                        if f"og_name_{idx}" in v: ctrls["name"].value = v[f"og_name_{idx}"]
                        if f"og_ort_{idx}" in v: ctrls["ort"].value = v[f"og_ort_{idx}"]
                        if f"og_inhalt_{idx}" in v: ctrls["inhalt"].value = v[f"og_inhalt_{idx}"]
                        if f"og_verp_{idx}" in v: ctrls["verpackung"].value = v[f"og_verp_{idx}"]

                    if "og_okz_bemerkung" in v: og_okz_bemerkung_dd.value = v["og_okz_bemerkung"]
                    if "og_okz_anmerkung" in v: og_okz_anmerkung_in.value = v["og_okz_anmerkung"]
                    for idx_str, ctrls in og_okz_controls.items():
                        if f"og_okz_status_{idx_str}" in v: ctrls["status"].value = v[f"og_okz_status_{idx_str}"]
                        if f"og_okz_objekt_{idx_str}" in v: ctrls["objekt"].value = v[f"og_okz_objekt_{idx_str}"]
                        if f"og_okz_ort_{idx_str}" in v: ctrls["ort"].value = v[f"og_okz_ort_{idx_str}"]
                        if f"og_okz_abklatsch_{idx_str}" in v: ctrls["abklatsch"].value = v[f"og_okz_abklatsch_{idx_str}"]
                        if f"og_okz_tupfer_{idx_str}" in v: ctrls["tupfer"].value = v[f"og_okz_tupfer_{idx_str}"]
                    
                    vorlagen_status.value = f"✅ '{vl_dd.value}' geladen!"
                    vorlagen_status.color = "green"
                    pruefe_lims_warnung()
                    page.update()

                vl_load_btn = sicherer_button("Laden 📥", lade_v, "blue", "white", width=90, height=40)
                vl_name_in = ft.TextField(label="Name für neue Vorlage", expand=True, color="yellow", text_style=ft.TextStyle(size=12, color="yellow"), label_style=stil_label_weiss, border_color="white", dense=True, content_padding=10)
                
                def del_v(e):
                    if vl_dd.value in alle_vorlagen:
                        del alle_vorlagen[vl_dd.value]
                        speichere_vorlagen(alle_vorlagen)
                        vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                        vorlagen_status.value = f"🗑️ Gelöscht!"
                        vorlagen_status.color = "red"
                        vl_dd.value = None
                        page.update()

                vl_del_btn = sicherer_button("Löschen 🗑️", del_v, "red", "white", width=100, height=40)
                
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
                        "se_verpackung_dd": se_verpackung_dd.value, "se_entnahmeort_dd": se_entnahmeort_dd.value, "se_bemerkung_dd": se_bemerkung_dd.value,
                        
                        "hfm_hack_entnahmeort": hfm_hack_entnahmeort_dd.value, "hfm_hack_inhalt": hfm_hack_inhalt_in.value,
                        "hfm_hack_verpackung": hfm_hack_verpackung_dd.value, "hfm_hack_charge_schwein": hfm_hack_charge_schwein_dd.value,
                        "hfm_hack_charge_rind": hfm_hack_charge_rind_dd.value, "hfm_hack_bemerkung": hfm_hack_bemerkung_dd.value,
                        "hfm_hack_lief_schwein": hfm_hack_lief_schwein_in.value, "hfm_hack_lief_rind": hfm_hack_lief_rind_in.value,
                        
                        "hfm_mett_entnahmeort": hfm_mett_entnahmeort_dd.value, "hfm_mett_inhalt": hfm_mett_inhalt_in.value,
                        "hfm_mett_verpackung": hfm_mett_verpackung_dd.value, "hfm_mett_lief": hfm_mett_lief_in.value,
                        "hfm_mett_charge": hfm_mett_charge_dd.value, "hfm_mett_bemerkung": hfm_mett_bemerkung_dd.value,
                        
                        "hfm_fzs_entnahmeort": hfm_fzs_entnahmeort_dd.value, "hfm_fzs_produkt": hfm_fzs_produkt_in.value,
                        "hfm_fzs_marinade": hfm_fzs_marinade_in.value, "hfm_fzs_inhalt": hfm_fzs_inhalt_in.value,
                        "hfm_fzs_verpackung": hfm_fzs_verpackung_dd.value, "hfm_fzs_lief": hfm_fzs_lief_in.value,
                        "hfm_fzs_charge": hfm_fzs_charge_dd.value, "hfm_fzs_bemerkung": hfm_fzs_bemerkung_dd.value,

                        "hfm_fzg_entnahmeort": hfm_fzg_entnahmeort_dd.value, "hfm_fzg_produkt": hfm_fzg_produkt_in.value,
                        "hfm_fzg_marinade": hfm_fzg_marinade_in.value, "hfm_fzg_inhalt": hfm_fzg_inhalt_in.value,
                        "hfm_fzg_verpackung": hfm_fzg_verpackung_dd.value, "hfm_fzg_lief": hfm_fzg_lief_in.value,
                        "hfm_fzg_charge": hfm_fzg_charge_dd.value, "hfm_fzg_bemerkung": hfm_fzg_bemerkung_dd.value,

                        "hfm_bio_entnahmeort": hfm_bio_entnahmeort_dd.value, "hfm_bio_inhalt": hfm_bio_inhalt_in.value,
                        "hfm_bio_verpackung": hfm_bio_verpackung_dd.value,
                        "hfm_bio_lief_schwein": hfm_bio_lief_schwein_in.value, "hfm_bio_lief_rind": hfm_bio_lief_rind_in.value,
                        
                        "hfm_okz_bemerkung": hfm_okz_bemerkung_dd.value,
                        "og_okz_bemerkung": og_okz_bemerkung_dd.value,
                        "og_okz_anmerkung": og_okz_anmerkung_in.value,
                        
                        "se_okz_bemerkung": se_okz_bemerkung_dd.value
                    }
                    
                    for i in range(1, 4):
                        idx = f"{i:02d}"
                        ctrls = se_okz_controls[i]
                        d_v[f"se_okz_status_{idx}"] = ctrls["status"].value
                        d_v[f"se_okz_objekt_{idx}"] = ctrls["objekt"].value
                        d_v[f"se_okz_ort_{idx}"] = ctrls["ort"].value
                        d_v[f"se_okz_abklatsch_{idx}"] = ctrls["abklatsch"].value
                        d_v[f"se_okz_tupfer_{idx}"] = ctrls["tupfer"].value
                    
                    for idx_str, ctrls in okz_controls.items():
                        d_v[f"okz_status_{idx_str}"] = ctrls["status"].value
                        d_v[f"okz_objekt_{idx_str}"] = ctrls["objekt"].value
                        d_v[f"okz_ort_{idx_str}"] = ctrls["ort"].value
                        d_v[f"okz_abklatsch_{idx_str}"] = ctrls["abklatsch"].value
                        d_v[f"okz_tupfer_{idx_str}"] = ctrls["tupfer"].value
                        
                    for i in range(1, 6):
                        idx = f"{i:02d}"
                        ctrls = og_controls[i]
                        d_v[f"og_name_{idx}"] = ctrls["name"].value
                        d_v[f"og_ort_{idx}"] = ctrls["ort"].value
                        d_v[f"og_inhalt_{idx}"] = ctrls["inhalt"].value
                        d_v[f"og_verp_{idx}"] = ctrls["verpackung"].value

                    for idx_str, ctrls in og_okz_controls.items():
                        d_v[f"og_okz_status_{idx_str}"] = ctrls["status"].value
                        d_v[f"og_okz_objekt_{idx_str}"] = ctrls["objekt"].value
                        d_v[f"og_okz_ort_{idx_str}"] = ctrls["ort"].value
                        d_v[f"og_okz_abklatsch_{idx_str}"] = ctrls["abklatsch"].value
                        d_v[f"og_okz_tupfer_{idx_str}"] = ctrls["tupfer"].value

                    alle_vorlagen[vl_name_in.value] = d_v
                    speichere_vorlagen(alle_vorlagen)
                    vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                    vorlagen_status.value = f"✅ Vorlage '{vl_name_in.value}' gespeichert!"
                    vorlagen_status.color = "orange"
                    vl_name_in.value = ""

                    # ALLE TAGES-FELDER AUTOMATISCH LEEREN!
                    adr_in.value = ""; nr_in.value = ""; auft_in.value = ""
                    try:
                        h_t, h_m, h_j = heute_str.split(".")
                        tag_dd.value = h_t; mon_dd.value = h_m; jahr_dd.value = h_j
                        hfm_hack_herst_tag_dd.value = h_t; hfm_hack_herst_mon_dd.value = h_m; hfm_hack_herst_jahr_dd.value = h_j
                        hfm_mett_herst_tag_dd.value = h_t; hfm_mett_herst_mon_dd.value = h_m; hfm_mett_herst_jahr_dd.value = h_j
                        hfm_fzs_herst_tag_dd.value = h_t; hfm_fzs_herst_mon_dd.value = h_m; hfm_fzs_herst_jahr_dd.value = h_j
                        hfm_fzg_herst_tag_dd.value = h_t; hfm_fzg_herst_mon_dd.value = h_m; hfm_fzg_herst_jahr_dd.value = h_j
                        hfm_bio_herst_tag_dd.value = h_t; hfm_bio_herst_mon_dd.value = h_m; hfm_bio_herst_jahr_dd.value = h_j
                    except: pass
                    
                    tw_zeit_in.value = ""; tw_temp_in.value = ""; tw_tempkonst_in.value = ""
                    se_zeit_in.value = ""; se_temp_in.value = ""
                    hfm_hack_temp_in.value = ""; hfm_mett_temp_in.value = ""; hfm_fzs_temp_in.value = ""; hfm_fzg_temp_in.value = ""; hfm_bio_temp_in.value = ""
                    
                    hfm_hack_mhd_s_tag_dd.value = ""; hfm_hack_mhd_s_mon_dd.value = ""; hfm_hack_mhd_s_jahr_dd.value = ""
                    hfm_hack_mhd_r_tag_dd.value = ""; hfm_hack_mhd_r_mon_dd.value = ""; hfm_hack_mhd_r_jahr_dd.value = ""
                    hfm_mett_mhd_tag_dd.value = ""; hfm_mett_mhd_mon_dd.value = ""; hfm_mett_mhd_jahr_dd.value = ""
                    hfm_fzs_mhd_tag_dd.value = ""; hfm_fzs_mhd_mon_dd.value = ""; hfm_fzs_mhd_jahr_dd.value = ""
                    hfm_fzg_mhd_tag_dd.value = ""; hfm_fzg_mhd_mon_dd.value = ""; hfm_fzg_mhd_jahr_dd.value = ""
                    hfm_bio_mhd_s_tag_dd.value = ""; hfm_bio_mhd_s_mon_dd.value = ""; hfm_bio_mhd_s_jahr_dd.value = ""
                    hfm_bio_mhd_r_tag_dd.value = ""; hfm_bio_mhd_r_mon_dd.value = ""; hfm_bio_mhd_r_jahr_dd.value = ""

                    hfm_hack_charge_schwein_dd.value = "Bitte eingeben"; hfm_hack_charge_rind_dd.value = "Bitte eingeben"
                    hfm_mett_charge_dd.value = "Bitte eingeben"
                    hfm_fzs_charge_dd.value = "Bitte eingeben"; hfm_fzg_charge_dd.value = "Bitte eingeben"
                    hfm_bio_charge_schwein_dd.value = "Bitte eingeben"; hfm_bio_charge_rind_dd.value = "Bitte eingeben"
                    
                    for i in range(1, 4):
                        ctrls = se_okz_controls[i]
                        ctrls["status"].value = "R+D"
                        ctrls["objekt"].value = se_okz_defaults[i]["obj"]
                        ctrls["ort"].value = ""
                        ctrls["abklatsch"].value = se_okz_defaults[i]["abk"]
                        ctrls["tupfer"].value = se_okz_defaults[i]["tup"]
                    
                    for idx_str, ctrls in okz_controls.items():
                        i = int(idx_str)
                        ctrls["status"].value = "R+D"
                        ctrls["objekt"].value = okz_defaults[i]["obj"]
                        ctrls["ort"].value = ""
                        ctrls["abklatsch"].value = okz_defaults[i]["abk"]
                        ctrls["tupfer"].value = okz_defaults[i]["tup"]

                    for i in range(1, 6):
                        ctrls = og_controls[i]
                        ctrls["name"].value = ""; ctrls["ort"].value = ""
                        ctrls["h_t"].value = ""; ctrls["h_m"].value = ""; ctrls["h_j"].value = ""
                        ctrls["v_t"].value = ""; ctrls["v_m"].value = ""; ctrls["v_j"].value = ""
                        ctrls["inhalt"].value = ""; ctrls["verpackung"].value = ""; ctrls["temp"].value = ""

                    og_okz_cb.value = False; og_okz_bemerkung_dd.value = "Bitte eingeben"; og_okz_anmerkung_in.value = ""
                    for idx_str, ctrls in og_okz_controls.items():
                        i = int(idx_str)
                        ctrls["status"].value = "R+D"
                        ctrls["objekt"].value = og_okz_defaults[i]["obj"]
                        ctrls["ort"].value = ""
                        ctrls["abklatsch"].value = og_okz_defaults[i]["abk"]
                        ctrls["tupfer"].value = og_okz_defaults[i]["tup"]
                    
                    page.update()

                vl_save_btn = sicherer_button("Speichern 💾", save_v, "orange", "black", width=110, height=40)
                
                # KOMPAKTE VORLAGEN BOX
                vorlagen_container = ft.Container(
                    bgcolor="#002200", padding=10, border_radius=10,
                    content=ft.Column([
                        ft.Row([ft.Text("📋 Vorlagen", color="white", weight="bold", size=14), vorlagen_status]),
                        ft.Row([vl_dd, vl_load_btn, vl_del_btn]),
                        ft.Row([vl_name_in, vl_save_btn])
                    ], spacing=5)
                )

                # --- ZUSAMMENBAU DES LAYOUTS ---
                stamm_col = ft.Column([datum_row, adr_in, nr_in, auft_in, ag_dd, name_in, typ_dd, bem_in], visible=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
                
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
                    tw_kurz1_dd, tw_kurz2_dd, tw_kurz3_dd, tw_kurz4_dd,
                    ft.Text("Auffälligkeiten:", color="white", weight="bold"),
                    cb_row(cb_auff_ja, cb_auff_nein),
                    cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf,
                    cb_auff_eck_zu, cb_auff_nichtmoeglich, cb_auff_dusche, cb_auff_handbrause,
                    cb_auff_sonst,
                    cb_auff_unterbau,
                    tw_auff_sonstiges_in,
                    ft.Divider(color="white24"),
                    ft.Text("Probenahmedetails", color="white", size=16, weight="bold"),
                    tw_zweck_dd, tw_inhalt_in, tw_verpackung_dd, tw_entnahmeort_dd, tw_bemerkung_dd
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                se_eis_col = ft.Column([
                    se_kalt_cb, se_zeit_in, se_zapf_dd, ft.Divider(color="white24"),
                    ft.Text("Probenahmetechnik / Art der Zapfstelle:", color="white", weight="bold"),
                    cb_row(se_cb_eiswanne, se_cb_fallprobe), se_tech_sonst_in, ft.Divider(color="white24"),
                    se_desinf_dd, ft.Text("Auffälligkeiten:", color="white", weight="bold"),
                    se_cb_ozon, se_auff_sonst_in, ft.Divider(color="white24"),
                    se_inhalt_in, se_verpackung_dd, se_entnahmeort_dd, se_temp_in, se_bemerkung_dd
                ], visible=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                se_okz_col = ft.Column([
                    ft.Text("⚠️ Bitte darauf achten: Haken setzen oder entfernen!", color="orange", weight="bold"),
                    se_okz_cb, ft.Divider(color="white24"), *se_okz_felder, se_okz_bemerkung_dd
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                def switch_se_tab(tab_name):
                    se_eis_col.visible = (tab_name == "eis")
                    se_okz_col.visible = (tab_name == "okz")
                    btn_se_eis.bgcolor = "red" if tab_name == "eis" else "blue"
                    btn_se_okz.bgcolor = "red" if tab_name == "okz" else "blue"
                    page.update()

                btn_se_eis = sicherer_button("Eis", lambda e: switch_se_tab("eis"), "red", "white")
                btn_se_okz = sicherer_button("OKZ", lambda e: switch_se_tab("okz"), "blue", "white")

                se_main_col = ft.Column([
                    ft.Row([btn_se_eis, btn_se_okz], scroll=ft.ScrollMode.AUTO),
                    ft.Divider(color="white24"),
                    se_eis_col, se_okz_col
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


                # --- HFM UNTERMENÜ ---
                hfm_hack_col = ft.Column([
                    hfm_hack_cb,
                    hfm_hack_entnahmeort_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Herstellungsdatum:", color="white", weight="bold"),
                    ft.Row([hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd]),
                    hfm_hack_inhalt_in,
                    hfm_hack_verpackung_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Lieferant:", color="white", weight="bold"),
                    hfm_hack_lief_schwein_in, hfm_hack_lief_rind_in,
                    ft.Divider(color="white24"),
                    ft.Text("MHD-Rohware (Schweinefleisch):", color="yellow", weight="bold", size=12),
                    ft.Row([hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_s_jahr_dd]),
                    ft.Text("MHD-Rohware (Rindfleisch):", color="yellow", weight="bold", size=12),
                    ft.Row([hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, hfm_hack_mhd_r_jahr_dd]),
                    ft.Divider(color="white24"),
                    ft.Text("Charge Rohware:", color="white", weight="bold"),
                    hfm_hack_charge_schwein_dd, hfm_hack_charge_rind_dd,
                    ft.Divider(color="white24"),
                    hfm_hack_temp_in,
                    hfm_hack_bemerkung_dd
                ], visible=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                hfm_mett_col = ft.Column([
                    hfm_mett_cb,
                    hfm_mett_entnahmeort_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Herstellungsdatum:", color="white", weight="bold"),
                    ft.Row([hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd]),
                    hfm_mett_inhalt_in,
                    hfm_mett_verpackung_dd,
                    ft.Divider(color="white24"),
                    hfm_mett_lief_in,
                    ft.Divider(color="white24"),
                    ft.Text("MHD-Rohware:", color="white", weight="bold"),
                    ft.Row([hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, hfm_mett_mhd_jahr_dd]),
                    ft.Divider(color="white24"),
                    hfm_mett_charge_dd,
                    ft.Divider(color="white24"),
                    hfm_mett_temp_in,
                    hfm_mett_bemerkung_dd
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                hfm_fzs_col = ft.Column([
                    hfm_fzs_cb,
                    hfm_fzs_entnahmeort_dd,
                    hfm_fzs_produkt_in, hfm_fzs_marinade_in,
                    ft.Divider(color="white24"),
                    ft.Text("Herstellungsdatum:", color="white", weight="bold"),
                    ft.Row([hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_herst_jahr_dd]),
                    hfm_fzs_inhalt_in,
                    hfm_fzs_verpackung_dd,
                    ft.Divider(color="white24"),
                    hfm_fzs_lief_in,
                    ft.Divider(color="white24"),
                    ft.Text("MHD-Rohware:", color="white", weight="bold"),
                    ft.Row([hfm_fzs_mhd_tag_dd, hfm_fzs_mhd_mon_dd, hfm_fzs_mhd_jahr_dd]),
                    ft.Divider(color="white24"),
                    hfm_fzs_charge_dd,
                    ft.Divider(color="white24"),
                    hfm_fzs_temp_in,
                    hfm_fzs_bemerkung_dd
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                hfm_fzg_col = ft.Column([
                    hfm_fzg_cb,
                    hfm_fzg_entnahmeort_dd,
                    hfm_fzg_produkt_in, hfm_fzg_marinade_in,
                    ft.Divider(color="white24"),
                    ft.Text("Herstellungsdatum:", color="white", weight="bold"),
                    ft.Row([hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_herst_jahr_dd]),
                    hfm_fzg_inhalt_in,
                    hfm_fzg_verpackung_dd,
                    ft.Divider(color="white24"),
                    hfm_fzg_lief_in,
                    ft.Divider(color="white24"),
                    ft.Text("MHD-Rohware:", color="white", weight="bold"),
                    ft.Row([hfm_fzg_mhd_tag_dd, hfm_fzg_mhd_mon_dd, hfm_fzg_mhd_jahr_dd]),
                    ft.Divider(color="white24"),
                    hfm_fzg_charge_dd,
                    ft.Divider(color="white24"),
                    hfm_fzg_temp_in,
                    hfm_fzg_bemerkung_dd
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                hfm_bio_col = ft.Column([
                    hfm_bio_cb,
                    hfm_bio_entnahmeort_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Herstellungsdatum:", color="white", weight="bold"),
                    ft.Row([hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_herst_jahr_dd]),
                    hfm_bio_inhalt_in,
                    hfm_bio_verpackung_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Lieferant:", color="white", weight="bold"),
                    hfm_bio_lief_schwein_in, hfm_bio_lief_rind_in,
                    ft.Divider(color="white24"),
                    ft.Text("MHD-Rohware (Schweinefleisch):", color="yellow", weight="bold", size=12),
                    ft.Row([hfm_bio_mhd_s_tag_dd, hfm_bio_mhd_s_mon_dd, hfm_bio_mhd_s_jahr_dd]),
                    ft.Text("MHD-Rohware (Rindfleisch):", color="yellow", weight="bold", size=12),
                    ft.Row([hfm_bio_mhd_r_tag_dd, hfm_bio_mhd_r_mon_dd, hfm_bio_mhd_r_jahr_dd]),
                    ft.Divider(color="white24"),
                    ft.Text("Charge Rohware:", color="white", weight="bold"),
                    hfm_bio_charge_schwein_dd, hfm_bio_charge_rind_dd,
                    ft.Divider(color="white24"),
                    hfm_bio_temp_in,
                    hfm_bio_bemerkung_dd
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                hfm_okz_col = ft.Column([
                    ft.Text("💡 Tipp: Lege eine Vorlage für Dich an mit den jeweiligen Entnahmeorten.", color="white54", italic=True, size=12),
                    ft.Text("⚠️ Bitte darauf achten: Haken setzen oder entfernen!", color="orange", weight="bold"),
                    hfm_okz_cb, ft.Divider(color="white24"), *okz_felder, hfm_okz_bemerkung_dd
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                def switch_hfm_tab(tab_name):
                    hfm_hack_col.visible = (tab_name == "hack")
                    hfm_mett_col.visible = (tab_name == "mett")
                    hfm_fzs_col.visible = (tab_name == "schwein")
                    hfm_fzg_col.visible = (tab_name == "gefluegel")
                    hfm_bio_col.visible = (tab_name == "bio")
                    hfm_okz_col.visible = (tab_name == "okz")
                    
                    btn_hfm_hack.bgcolor = "red" if tab_name == "hack" else "blue"
                    btn_hfm_mett.bgcolor = "red" if tab_name == "mett" else "blue"
                    btn_hfm_fz_schwein.bgcolor = "red" if tab_name == "schwein" else "blue"
                    btn_hfm_fz_gefluegel.bgcolor = "red" if tab_name == "gefluegel" else "blue"
                    btn_hfm_bio.bgcolor = "red" if tab_name == "bio" else "blue"
                    btn_hfm_okz.bgcolor = "red" if tab_name == "okz" else "blue"
                    page.update()

                btn_hfm_hack = sicherer_button("Hack gemischt", lambda e: switch_hfm_tab("hack"), "red", "white")
                btn_hfm_mett = sicherer_button("Mett", lambda e: switch_hfm_tab("mett"), "blue", "white")
                btn_hfm_fz_schwein = sicherer_button("FZ Schwein", lambda e: switch_hfm_tab("schwein"), "blue", "white")
                btn_hfm_fz_gefluegel = sicherer_button("FZ Geflügel", lambda e: switch_hfm_tab("gefluegel"), "blue", "white")
                btn_hfm_bio = sicherer_button("Bio-Hack", lambda e: switch_hfm_tab("bio"), "blue", "white")
                btn_hfm_okz = sicherer_button("OKZ", lambda e: switch_hfm_tab("okz"), "blue", "white")

                hfm_main_col = ft.Column([
                    ft.Row([btn_hfm_hack, btn_hfm_mett, btn_hfm_fz_schwein, btn_hfm_fz_gefluegel, btn_hfm_bio, btn_hfm_okz], scroll=ft.ScrollMode.AUTO),
                    ft.Divider(color="white24"),
                    hfm_hack_col, hfm_mett_col, hfm_fzs_col, hfm_fzg_col, hfm_bio_col, hfm_okz_col
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                og_teil_col = ft.Column([
                    og_cb, ft.Divider(color="white24"), *og_felder
                ], visible=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                og_okz_col = ft.Column([
                    ft.Text("⚠️ Bitte darauf achten: Haken setzen oder entfernen!", color="orange", weight="bold"),
                    og_okz_cb, 
                    ft.Divider(color="white24"), 
                    *og_okz_felder, 
                    ft.Text("💡 Wichtig: Wird die Saftpresse beprobt, muss zwingend auch das Messer aufgenommen werden!", color="orange", weight="bold"),
                    og_okz_bemerkung_dd,
                    og_okz_anmerkung_in
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                def switch_og_tab(tab_name):
                    og_teil_col.visible = (tab_name == "teil")
                    og_okz_col.visible = (tab_name == "okz")
                    btn_og_teil.bgcolor = "red" if tab_name == "teil" else "blue"
                    btn_og_okz.bgcolor = "red" if tab_name == "okz" else "blue"
                    page.update()

                btn_og_teil = sicherer_button("Convenience", lambda e: switch_og_tab("teil"), "red", "white")
                btn_og_okz = sicherer_button("OKZ", lambda e: switch_og_tab("okz"), "blue", "white")

                og_main_col = ft.Column([
                    ft.Row([btn_og_teil, btn_og_okz], scroll=ft.ScrollMode.AUTO),
                    ft.Divider(color="white24"),
                    og_teil_col, og_okz_col
                ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

                # --- HAUPT-REITER SCHALTUNGEN ---
                def switch_tab_stamm(e):
                    stamm_col.visible = True; tw_col.visible = False; se_main_col.visible = False; hfm_main_col.visible = False; og_main_col.visible = False
                    btn_stamm.bgcolor = "red"; btn_tw.bgcolor = "blue"; btn_se.bgcolor = "blue"; btn_hfm.bgcolor = "blue"; btn_og.bgcolor = "blue"
                    page.update()
                    
                def switch_tab_tw(e):
                    stamm_col.visible = False; tw_col.visible = True; se_main_col.visible = False; hfm_main_col.visible = False; og_main_col.visible = False
                    btn_stamm.bgcolor = "blue"; btn_tw.bgcolor = "red"; btn_se.bgcolor = "blue"; btn_hfm.bgcolor = "blue"; btn_og.bgcolor = "blue"
                    page.update()

                def switch_tab_se(e):
                    stamm_col.visible = False; tw_col.visible = False; se_main_col.visible = True; hfm_main_col.visible = False; og_main_col.visible = False
                    btn_stamm.bgcolor = "blue"; btn_tw.bgcolor = "blue"; btn_se.bgcolor = "red"; btn_hfm.bgcolor = "blue"; btn_og.bgcolor = "blue"
                    page.update()

                def switch_tab_hfm(e):
                    stamm_col.visible = False; tw_col.visible = False; se_main_col.visible = False; hfm_main_col.visible = True; og_main_col.visible = False
                    btn_stamm.bgcolor = "blue"; btn_tw.bgcolor = "blue"; btn_se.bgcolor = "blue"; btn_hfm.bgcolor = "red"; btn_og.bgcolor = "blue"
                    page.update()
                    
                def switch_tab_og(e):
                    stamm_col.visible = False; tw_col.visible = False; se_main_col.visible = False; hfm_main_col.visible = False; og_main_col.visible = True
                    btn_stamm.bgcolor = "blue"; btn_tw.bgcolor = "blue"; btn_se.bgcolor = "blue"; btn_hfm.bgcolor = "blue"; btn_og.bgcolor = "red"
                    page.update()

                btn_stamm = sicherer_button("STAMMDATEN", switch_tab_stamm, "red", "white")
                btn_tw = sicherer_button("TRINKWASSER", switch_tab_tw, "blue", "white")
                btn_se = sicherer_button("SCHERBENEIS", switch_tab_se, "blue", "white")
                btn_hfm = sicherer_button("HFM", switch_tab_hfm, "blue", "white")
                btn_og = sicherer_button("OG", switch_tab_og, "blue", "white")

                fehler_text = ft.Text("", color="red", weight="bold", visible=False)
                status_text = ft.Text("", color="yellow", weight="bold", size=16)

                def hole_aktuelle_daten():
                    d = {
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
                        "cb_auff_unterbau": cb_auff_unterbau.value, "cb_auff_eck_zu": cb_auff_eck_zu.value, 
                        "cb_auff_nichtmoeglich": cb_auff_nichtmoeglich.value, "cb_auff_dusche": cb_auff_dusche.value, 
                        "cb_auff_handbrause": cb_auff_handbrause.value, "cb_auff_sonst": cb_auff_sonst.value, "tw_auff_sonstiges": tw_auff_sonstiges_in.value,
                        "tw_zweck": tw_zweck_dd.value, "tw_inhalt": tw_inhalt_in.value, "tw_verpackung": tw_verpackung_dd.value, 
                        "tw_entnahmeort": tw_entnahmeort_dd.value, "tw_tempkonst": tw_tempkonst_in.value, "tw_bemerkung": tw_bemerkung_dd.value,

                        "se_kalt": se_kalt_cb.value, "se_zeit": se_zeit_in.value, "se_zapf": se_zapf_dd.value,
                        "se_cb_eiswanne": se_cb_eiswanne.value, "se_cb_fallprobe": se_cb_fallprobe.value, "se_tech_sonst": se_tech_sonst_in.value,
                        "se_desinf": se_desinf_dd.value, "se_cb_ozon": se_cb_ozon.value, "se_auff_sonst": se_auff_sonst_in.value,
                        "se_inhalt": se_inhalt_in.value, "se_verpackung": se_verpackung_dd.value, "se_entnahmeort": se_entnahmeort_dd.value,
                        "se_temp": se_temp_in.value, "se_bemerkung": se_bemerkung_dd.value,
                        
                        "se_okz_cb": se_okz_cb.value, "se_okz_bemerkung": se_okz_bemerkung_dd.value,

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
                        "hfm_fzg_bemerkung": hfm_fzg_bemerkung_dd.value,

                        "hfm_bio_cb": hfm_bio_cb.value, "hfm_bio_entnahmeort": hfm_bio_entnahmeort_dd.value,
                        "hfm_bio_herstelldatum": get_date_str(hfm_bio_herst_tag_dd.value, hfm_bio_herst_mon_dd.value, hfm_bio_herst_jahr_dd.value),
                        "hfm_bio_inhalt": hfm_bio_inhalt_in.value, "hfm_bio_verpackung": hfm_bio_verpackung_dd.value,
                        "hfm_bio_lief_schwein": hfm_bio_lief_schwein_in.value, "hfm_bio_lief_rind": hfm_bio_lief_rind_in.value,
                        "hfm_bio_mhd_schwein": get_date_str(hfm_bio_mhd_s_tag_dd.value, hfm_bio_mhd_s_mon_dd.value, hfm_bio_mhd_s_jahr_dd.value),
                        "hfm_bio_mhd_rind": get_date_str(hfm_bio_mhd_r_tag_dd.value, hfm_bio_mhd_r_mon_dd.value, hfm_bio_mhd_r_jahr_dd.value),
                        "hfm_bio_charge_schwein": hfm_bio_charge_schwein_dd.value, "hfm_bio_charge_rind": hfm_bio_charge_rind_dd.value,
                        "hfm_bio_temp": hfm_bio_temp_in.value, "hfm_bio_bemerkung": hfm_bio_bemerkung_dd.value,
                        
                        "hfm_okz_cb": hfm_okz_cb.value, "hfm_okz_bemerkung": hfm_okz_bemerkung_dd.value,
                        "og_cb": og_cb.value,
                        "og_okz_cb": og_okz_cb.value,
                        "og_okz_bemerkung": og_okz_bemerkung_dd.value,
                        "og_okz_anmerkung": og_okz_anmerkung_in.value
                    }
                    
                    for i in range(1, 4):
                        idx = f"{i:02d}"
                        ctrls = se_okz_controls[i]
                        d[f"se_okz_status_{idx}"] = ctrls["status"].value
                        d[f"se_okz_objekt_{idx}"] = ctrls["objekt"].value
                        d[f"se_okz_ort_{idx}"] = ctrls["ort"].value
                        d[f"se_okz_abklatsch_{idx}"] = ctrls["abklatsch"].value
                        d[f"se_okz_tupfer_{idx}"] = ctrls["tupfer"].value
                        
                    for idx_str, ctrls in okz_controls.items():
                        d[f"okz_status_{idx_str}"] = ctrls["status"].value
                        d[f"okz_objekt_{idx_str}"] = ctrls["objekt"].value
                        d[f"okz_ort_{idx_str}"] = ctrls["ort"].value
                        d[f"okz_abklatsch_{idx_str}"] = ctrls["abklatsch"].value
                        d[f"okz_tupfer_{idx_str}"] = ctrls["tupfer"].value

                    for i in range(1, 6):
                        idx = f"{i:02d}"
                        ctrls = og_controls[i]
                        d[f"og_name_{idx}"] = ctrls["name"].value
                        d[f"og_ort_{idx}"] = ctrls["ort"].value
                        d[f"og_herst_{idx}"] = get_date_str(ctrls["h_t"].value, ctrls["h_m"].value, ctrls["h_j"].value)
                        d[f"og_verb_{idx}"] = get_date_str(ctrls["v_t"].value, ctrls["v_m"].value, ctrls["v_j"].value)
                        d[f"og_inhalt_{idx}"] = ctrls["inhalt"].value
                        d[f"og_verp_{idx}"] = ctrls["verpackung"].value
                        d[f"og_temp_{idx}"] = ctrls["temp"].value
                        
                    for idx_str, ctrls in og_okz_controls.items():
                        d[f"og_okz_status_{idx_str}"] = ctrls["status"].value
                        d[f"og_okz_objekt_{idx_str}"] = ctrls["objekt"].value
                        d[f"og_okz_ort_{idx_str}"] = ctrls["ort"].value
                        d[f"og_okz_abklatsch_{idx_str}"] = ctrls["abklatsch"].value
                        d[f"og_okz_tupfer_{idx_str}"] = ctrls["tupfer"].value
                        
                    return d

                def nur_speichern(e):
                    if not (nr_in.value or "").strip() or not (auft_in.value or "").strip():
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
                    if not (nr_in.value or "").strip() or not (auft_in.value or "").strip():
                        switch_tab_stamm(None)
                        fehler_text.value="⚠️ MARKTNUMMER UND AUFTRAGSNUMMER FEHLEN!"
                        fehler_text.visible=True; status_text.value=""
                        page.update(); return
                    
                    tw_hat_daten = bool((tw_zeit_in.value or "").strip() or (tw_temp_in.value or "").strip())
                    se_hat_daten = bool((se_zeit_in.value or "").strip() or (se_temp_in.value or "").strip())
                    
                    se_okz_hat_daten = False
                    for i in range(1, 4):
                        if (se_okz_controls[i]["ort"].value or "").strip(): se_okz_hat_daten = True

                    hfm_hack_hat_daten = bool((hfm_hack_temp_in.value or "").strip() or (hfm_hack_mhd_s_tag_dd.value or "").strip() or (hfm_hack_mhd_r_tag_dd.value or "").strip() or hat_charge_wert(hfm_hack_charge_schwein_dd.value) or hat_charge_wert(hfm_hack_charge_rind_dd.value))
                    hfm_mett_hat_daten = bool((hfm_mett_temp_in.value or "").strip() or (hfm_mett_mhd_tag_dd.value or "").strip() or hat_charge_wert(hfm_mett_charge_dd.value))
                    hfm_fzs_hat_daten = bool((hfm_fzs_temp_in.value or "").strip() or (hfm_fzs_mhd_tag_dd.value or "").strip() or hat_charge_wert(hfm_fzs_charge_dd.value))
                    hfm_fzg_hat_daten = bool((hfm_fzg_temp_in.value or "").strip() or (hfm_fzg_mhd_tag_dd.value or "").strip() or hat_charge_wert(hfm_fzg_charge_dd.value))
                    hfm_bio_hat_daten = bool((hfm_bio_temp_in.value or "").strip() or (hfm_bio_mhd_s_tag_dd.value or "").strip() or (hfm_bio_mhd_r_tag_dd.value or "").strip() or hat_charge_wert(hfm_bio_charge_schwein_dd.value) or hat_charge_wert(hfm_bio_charge_rind_dd.value))
                    
                    og_hat_daten = False
                    for i in range(1, 6):
                        if (og_controls[i]["name"].value or "").strip() or (og_controls[i]["temp"].value or "").strip() or (og_controls[i]["v_t"].value or "").strip():
                            og_hat_daten = True
                    
                    # 1. Haken vergessen Warnung (LIMS-Override)
                    if tw_hat_daten and not tw_kalt_cb.value and not lims_override_cb.value:
                        switch_tab_tw(None)
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI TRINKWASSER FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if se_hat_daten and not se_kalt_cb.value and not lims_override_cb.value:
                        switch_tab_se(None)
                        switch_se_tab("eis")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI SCHERBENEIS FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if se_okz_hat_daten and not se_okz_cb.value and not lims_override_cb.value:
                        switch_tab_se(None)
                        switch_se_tab("okz")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI SCHERBENEIS OKZ FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if hfm_hack_hat_daten and not hfm_hack_cb.value and not lims_override_cb.value:
                        switch_tab_hfm("hack")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI HACKFLEISCH GEMISCHT FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if hfm_mett_hat_daten and not hfm_mett_cb.value and not lims_override_cb.value:
                        switch_tab_hfm("mett")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI SCHWEINEMETT FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if hfm_fzs_hat_daten and not hfm_fzs_cb.value and not lims_override_cb.value:
                        switch_tab_hfm("schwein")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI FZ SCHWEIN FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if hfm_fzg_hat_daten and not hfm_fzg_cb.value and not lims_override_cb.value:
                        switch_tab_hfm("gefluegel")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI FZ GEFLÜGEL FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if hfm_bio_hat_daten and not hfm_bio_cb.value and not lims_override_cb.value:
                        switch_tab_hfm("bio")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI BIO-HACK FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return
                    if og_hat_daten and not og_cb.value and not lims_override_cb.value:
                        switch_tab_og("teil")
                        fehler_text.value="⚠️ AKTIVIERUNGS-HAKEN BEI OG FEHLT!"
                        fehler_text.visible=True; status_text.value=""; page.update(); return

                    # 2. PFLICHTFELD WARNUNG (Uhrzeit, Temperatur, MHD, Charge)
                    fehlende_pflicht = []
                    if tw_kalt_cb.value:
                        if not (tw_zeit_in.value or "").strip(): fehlende_pflicht.append("TW: Uhrzeit")
                        if not (tw_temp_in.value or "").strip(): fehlende_pflicht.append("TW: Temperatur")
                    if se_kalt_cb.value:
                        if not (se_zeit_in.value or "").strip(): fehlende_pflicht.append("Eis: Uhrzeit")
                        if not (se_temp_in.value or "").strip(): fehlende_pflicht.append("Eis: Temperatur")
                    if hfm_hack_cb.value:
                        if not (hfm_hack_temp_in.value or "").strip(): fehlende_pflicht.append("Hack: Temperatur")
                        if not (hfm_hack_mhd_s_tag_dd.value or "").strip() and not (hfm_hack_mhd_r_tag_dd.value or "").strip(): fehlende_pflicht.append("Hack: MHD")
                        if not hat_charge_wert(hfm_hack_charge_schwein_dd.value) and not hat_charge_wert(hfm_hack_charge_rind_dd.value): fehlende_pflicht.append("Hack: Charge")
                    if hfm_mett_cb.value:
                        if not (hfm_mett_temp_in.value or "").strip(): fehlende_pflicht.append("Mett: Temperatur")
                        if not (hfm_mett_mhd_tag_dd.value or "").strip(): fehlende_pflicht.append("Mett: MHD")
                        if not hat_charge_wert(hfm_mett_charge_dd.value): fehlende_pflicht.append("Mett: Charge")
                    if hfm_fzs_cb.value:
                        if not (hfm_fzs_temp_in.value or "").strip(): fehlende_pflicht.append("FZS: Temperatur")
                        if not (hfm_fzs_mhd_tag_dd.value or "").strip(): fehlende_pflicht.append("FZS: MHD")
                        if not hat_charge_wert(hfm_fzs_charge_dd.value): fehlende_pflicht.append("FZS: Charge")
                    if hfm_fzg_cb.value:
                        if not (hfm_fzg_temp_in.value or "").strip(): fehlende_pflicht.append("FZG: Temperatur")
                        if not (hfm_fzg_mhd_tag_dd.value or "").strip(): fehlende_pflicht.append("FZG: MHD")
                        if not hat_charge_wert(hfm_fzg_charge_dd.value): fehlende_pflicht.append("FZG: Charge")
                    if hfm_bio_cb.value:
                        if not (hfm_bio_temp_in.value or "").strip(): fehlende_pflicht.append("Bio: Temperatur")
                        if not (hfm_bio_mhd_s_tag_dd.value or "").strip() and not (hfm_bio_mhd_r_tag_dd.value or "").strip(): fehlende_pflicht.append("Bio: MHD")
                        if not hat_charge_wert(hfm_bio_charge_schwein_dd.value) and not hat_charge_wert(hfm_bio_charge_rind_dd.value): fehlende_pflicht.append("Bio: Charge")
                    if og_cb.value:
                        og_ok = False
                        for i in range(1, 6):
                            if (og_controls[i]["temp"].value or "").strip() and (og_controls[i]["v_t"].value or "").strip(): og_ok = True
                        if not og_ok: fehlende_pflicht.append("OG: Mind. 1x Temp & Verbrauchsdatum")
                            
                    if fehlende_pflicht:
                        fehler_text.value = f"⚠️ PFLICHTFELDER FEHLEN:\n{', '.join(fehlende_pflicht)}"
                        fehler_text.visible = True; status_text.value = ""
                        page.update(); return

                    try:
                        fehler_text.visible = False
                        status_text.value = "⏳ Speichere und erstelle PDF..."
                        status_text.color = "yellow"
                        page.update()

                        # Datei-Check!
                        pdf_dateien = [
                            "stammdaten.pdf", "trinkwasser.pdf", "scherbeneis.pdf", "okz-se.pdf",
                            "hackfleisch_gemischt.pdf", "schweinemett.pdf", "fz_schwein.pdf", 
                            "fz_huhn.pdf", "bio.pdf", "okz-hfm.pdf", "og.pdf", "okz-og.pdf"
                        ]
                        fehlende_pdfs = [p for p in pdf_dateien if not os.path.exists(os.path.join("assets", p))]
                        
                        if fehlende_pdfs:
                            fehler_text.value = f"⚠️ FEHLENDE PDF-VORLAGEN IM ASSETS-ORDNER:\n{', '.join(fehlende_pdfs)}"
                            fehler_text.visible = True
                            status_text.value = ""
                            page.update()
                            return

                        maerkte = lade_maerkte()
                        d = hole_aktuelle_daten()
                        if markt_index is None: maerkte.append(d)
                        else: maerkte[markt_index] = d
                        speichere_maerkte(maerkte)

                        temp_dir, final_dir, heute_ordner = get_rewe_paths()
                        s_markt = "".join([c for c in nr_in.value if c.isalnum()])
                        final_ausg = os.path.join(final_dir, f"REWE_{s_markt}_{datetime.datetime.now().strftime('%d%m%y')}.pdf")
                        
                        writer = pypdf.PdfWriter()
                        for pdf_datei in pdf_dateien:
                            writer.append(pypdf.PdfReader(os.path.join("assets", pdf_datei)))
                        
                        def cb_val(val): return BooleanObject(True) if val else BooleanObject(False)
                            
                        tw_sonst_text = tw_auff_sonstiges_in.value or ""
                        
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

                        if se_okz_cb.value:
                            f_map.update({
                                "cb_0003_00": cb_val(se_okz_cb.value), "tf_0003_00": "Abklatschproben Scherbeneis",
                                "dd_0003_00_ZS-001796": se_okz_bemerkung_dd.value
                            })
                            for i in range(1, 4):
                                idx = f"{i:02d}"
                                ctrls = se_okz_controls[i]
                                f_map[f"dd_0003_{idx}_ZS-001880"] = ctrls["status"].value
                                f_map[f"dd_0003_{idx}_ZS-1419"] = ctrls["objekt"].value
                                f_map[f"dd_0003_{idx}_ZS-001792"] = ctrls["ort"].value
                                f_map[f"cb_0003_{idx}_ZS-002294"] = cb_val(ctrls["abklatsch"].value)
                                f_map[f"cb_0003_{idx}_ZS-002295"] = cb_val(ctrls["tupfer"].value)

                        if hfm_hack_cb.value:
                            f_map.update({
                                "cb_0004_00": cb_val(hfm_hack_cb.value), "tf_0004_00": "Hackfleisch gemischt",
                                "dd_0004_00_ZS-001799": hfm_hack_entnahmeort_dd.value,
                                "cal_0004_00_ZS-001810": get_date_str(hfm_hack_herst_tag_dd.value, hfm_hack_herst_mon_dd.value, hfm_hack_herst_jahr_dd.value),
                                "tf_0004_00_ZS-1215": hfm_hack_inhalt_in.value, "dd_0004_00_ZS-001798": hfm_hack_verpackung_dd.value,
                                "tf_0004_00_ZS-1209_Schweinefleisch: XXX": hfm_hack_lief_schwein_in.value,
                                "tf_0004_00_ZS-1209_Rindfleisch: XXX": hfm_hack_lief_rind_in.value,
                                "tf_0004_00_ZS-001835_Schweinefleisch: XXX": get_date_str(hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value),
                                "tf_0004_00_ZS-001835_Rindfleisch: XXX": get_date_str(hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value),
                                "tf_0004_00_ZS-002081_Schweinefleisch: XXX": hfm_hack_charge_schwein_dd.value,
                                "tf_0004_00_ZS-002081_Rindfleisch: XXX": hfm_hack_charge_rind_dd.value,
                                "tf_0004_00_ZS-1441": hfm_hack_temp_in.value, "dd_0004_00_ZS-001796": hfm_hack_bemerkung_dd.value
                            })

                        if hfm_mett_cb.value:
                            f_map.update({
                                "cb_0006_00": cb_val(hfm_mett_cb.value), "tf_0006_00": "gewürztes Schweinemett",
                                "dd_0006_00_ZS-001799": hfm_mett_entnahmeort_dd.value,
                                "cal_0006_00_ZS-001810": get_date_str(hfm_mett_herst_tag_dd.value, hfm_mett_herst_mon_dd.value, hfm_mett_herst_jahr_dd.value),
                                "tf_0006_00_ZS-1215": hfm_mett_inhalt_in.value, "dd_0006_00_ZS-001798": hfm_mett_verpackung_dd.value,
                                "tf_0006_00_ZS-1209": hfm_mett_lief_in.value,
                                "tf_0006_00_ZS-001835": get_date_str(hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value),
                                "tf_0006_00_ZS-002081": hfm_mett_charge_dd.value, "tf_0006_00_ZS-1441": hfm_mett_temp_in.value,
                                "dd_0006_00_ZS-001796": hfm_mett_bemerkung_dd.value
                            })

                        if hfm_fzs_cb.value:
                            prod_s = (hfm_fzs_produkt_in.value or "").strip(); mar_s = (hfm_fzs_marinade_in.value or "").strip()
                            prod_mar_str_s = f"{prod_s} / {mar_s}" if (prod_s and mar_s) else (prod_s or mar_s)
                            f_map.update({
                                "cb_0008_00": cb_val(hfm_fzs_cb.value), "tf_0008_00": "Fleischzubereitung Schwein",
                                "tf_0008_00_ Produkt \"Marinade\"": prod_mar_str_s, "dd_0008_00_ZS-001799": hfm_fzs_entnahmeort_dd.value,
                                "cal_0008_00_ZS-001810": get_date_str(hfm_fzs_herst_tag_dd.value, hfm_fzs_herst_mon_dd.value, hfm_fzs_herst_jahr_dd.value),
                                "tf_0008_00_ZS-1215": hfm_fzs_inhalt_in.value, "dd_0008_00_ZS-001798": hfm_fzs_verpackung_dd.value,
                                "tf_0008_00_ZS-1209": hfm_fzs_lief_in.value,
                                "tf_0008_00_ZS-001835": get_date_str(hfm_fzs_mhd_tag_dd.value, hfm_fzs_mhd_mon_dd.value, hfm_fzs_mhd_jahr_dd.value),
                                "tf_0008_00_ZS-002081": hfm_fzs_charge_dd.value, "tf_0008_00_ZS-1441": hfm_fzs_temp_in.value,
                                "dd_0008_00_ZS-001796": hfm_fzs_bemerkung_dd.value
                            })

                        if hfm_fzg_cb.value:
                            prod_g = (hfm_fzg_produkt_in.value or "").strip(); mar_g = (hfm_fzg_marinade_in.value or "").strip()
                            prod_mar_str_g = f"{prod_g} / {mar_g}" if (prod_g and mar_g) else (prod_g or mar_g)
                            f_map.update({
                                "cb_0007_00": cb_val(hfm_fzg_cb.value), "tf_0007_00": "Fleischzubereitung Geflügel",
                                "tf_0007_00_ Produkt \"Marinade\"": prod_mar_str_g, "dd_0007_00_ZS-001799": hfm_fzg_entnahmeort_dd.value,
                                "cal_0007_00_ZS-001810": get_date_str(hfm_fzg_herst_tag_dd.value, hfm_fzg_herst_mon_dd.value, hfm_fzg_herst_jahr_dd.value),
                                "tf_0007_00_ZS-1215": hfm_fzg_inhalt_in.value, "dd_0007_00_ZS-001798": hfm_fzg_verpackung_dd.value,
                                "tf_0007_00_ZS-1209": hfm_fzg_lief_in.value,
                                "tf_0007_00_ZS-001835": get_date_str(hfm_fzg_mhd_tag_dd.value, hfm_fzg_mhd_mon_dd.value, hfm_fzg_mhd_jahr_dd.value),
                                "tf_0007_00_ZS-002081": hfm_fzg_charge_dd.value, "tf_0007_00_ZS-1441": hfm_fzg_temp_in.value,
                                "dd_0007_00_ZS-001796": hfm_fzg_bemerkung_dd.value
                            })

                        if hfm_bio_cb.value:
                            f_map.update({
                                "cb_0005_00": cb_val(hfm_bio_cb.value), "tf_0005_00": "Biohackfleisch",
                                "dd_0005_00_ZS-001799": hfm_bio_entnahmeort_dd.value,
                                "cal_0005_00_ZS-001810": get_date_str(hfm_bio_herst_tag_dd.value, hfm_bio_herst_mon_dd.value, hfm_bio_herst_jahr_dd.value),
                                "tf_0005_00_ZS-1215": hfm_bio_inhalt_in.value, "dd_0005_00_ZS-001798": hfm_bio_verpackung_dd.value,
                                "tf_0005_00_ZS-1209_Schweinefleisch: XXX": hfm_bio_lief_schwein_in.value,
                                "tf_0005_00_ZS-1209_Rindfleisch: XXX": hfm_bio_lief_rind_in.value,
                                "tf_0005_00_ZS-001835_Schweinefleisch: XXX": get_date_str(hfm_bio_mhd_s_tag_dd.value, hfm_bio_mhd_s_mon_dd.value, hfm_bio_mhd_s_jahr_dd.value),
                                "tf_0005_00_ZS-001835_Rindfleisch: XXX": get_date_str(hfm_bio_mhd_r_tag_dd.value, hfm_bio_mhd_r_mon_dd.value, hfm_bio_mhd_r_jahr_dd.value),
                                "tf_0005_00_ZS-002081_Schweinefleisch: XXX": hfm_bio_charge_schwein_dd.value,
                                "tf_0005_00_ZS-002081_Rindfleisch: XXX": hfm_bio_charge_rind_dd.value,
                                "tf_0005_00_ZS-1441": hfm_bio_temp_in.value, "dd_0005_00_ZS-001796": hfm_bio_bemerkung_dd.value
                            })

                        if hfm_okz_cb.value:
                            f_map.update({
                                "cb_0010_00": cb_val(hfm_okz_cb.value), "tf_0010_00": "Abklatschproben HFM",
                                "dd_0010_00_ZS-001796": hfm_okz_bemerkung_dd.value
                            })
                            for i in range(1, 11):
                                idx = f"{i:02d}"
                                ctrls = okz_controls[idx]
                                f_map[f"dd_0010_{idx}_ZS-001880"] = ctrls["status"].value
                                f_map[f"dd_0010_{idx}_ZS-1419"] = ctrls["objekt"].value
                                f_map[f"dd_0010_{idx}_ZS-001792"] = ctrls["ort"].value
                                f_map[f"cb_0010_{idx}_ZS-002294"] = cb_val(ctrls["abklatsch"].value)
                                f_map[f"cb_0010_{idx}_ZS-002295"] = cb_val(ctrls["tupfer"].value)
                                
                        if og_cb.value:
                            f_map.update({
                                "cb_0009_00": cb_val(og_cb.value), "tf_0009_00": "Obst-/Gemüse Convenience"
                            })
                            for i in range(1, 6):
                                idx = f"{i:02d}"
                                ctrls = og_controls[i]
                                f_map[f"tf_0009_00_ Teilprobe {i}:"] = ctrls["name"].value
                                f_map[f"dd_0009_{idx}_ZS-001799"] = ctrls["ort"].value
                                f_map[f"cal_0009_{idx}_ZS-001810"] = get_date_str(ctrls["h_t"].value, ctrls["h_m"].value, ctrls["h_j"].value)
                                f_map[f"tf_0009_{idx}_ZS-1527"] = get_date_str(ctrls["v_t"].value, ctrls["v_m"].value, ctrls["v_j"].value)
                                f_map[f"tf_0009_{idx}_ZS-1215"] = ctrls["inhalt"].value
                                f_map[f"dd_0009_{idx}_ZS-001798"] = ctrls["verpackung"].value
                                f_map[f"tf_0009_{idx}_ZS-1441"] = ctrls["temp"].value
                                
                        if og_okz_cb.value:
                            f_map.update({
                                "cb_0011_00": cb_val(og_okz_cb.value), "tf_0011_00": "Obst-Gemüse Abklatschproben",
                                "dd_0011_00_ZS-001796": og_okz_bemerkung_dd.value,
                                "Anmerkung": og_okz_anmerkung_in.value
                            })
                            for i in range(1, 6):
                                idx = f"{i:02d}"
                                ctrls = og_okz_controls[idx]
                                f_map[f"dd_0011_{idx}_ZS-001880"] = ctrls["status"].value
                                f_map[f"dd_0011_{idx}_ZS-1419"] = ctrls["objekt"].value
                                f_map[f"dd_0011_{idx}_ZS-001792"] = ctrls["ort"].value
                                f_map[f"cb_0011_{idx}_ZS-002294"] = cb_val(ctrls["abklatsch"].value)
                                f_map[f"cb_0011_{idx}_ZS-002295"] = cb_val(ctrls["tupfer"].value)
                            
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
                btn_speichern = sicherer_button("💾 Tour speichern", nur_speichern, "orange", "black", expand=True, height=45)
                btn_final = sicherer_button("📄 Bericht erstellen (PDF)", save_final, "blue", "white", expand=True, height=50)

                ansicht.controls.extend([
                    ft.Row([btn_stamm, btn_tw, btn_se, btn_hfm, btn_og], scroll=ft.ScrollMode.AUTO),
                    lims_warnung,
                    lims_override_cb,
                    vorlagen_container,
                    ft.Divider(color="white"),
                    ft.Text(titel, size=20, weight="bold", color="white"),
                    stamm_col, tw_col, se_main_col, hfm_main_col, og_main_col,
                    ft.Container(height=20),
                    fehler_text,
                    status_text,
                    ft.Row([btn_zurueck, btn_speichern]),
                    ft.Row([btn_final])
                ])
                page.update()
                
            except Exception as intern_e:
                zeige_fehler(intern_e)

        def bereinige_archiv():
            base_dl = "/storage/emulated/0/Download" if os.path.exists("/storage/emulated/0/Download") else os.path.join(os.path.expanduser("~"), "Downloads")
            rewe_dir = os.path.join(base_dl, "REWE")
            if not os.path.exists(rewe_dir): return
            
            heute = datetime.datetime.now()
            for ordner in os.listdir(rewe_dir):
                ordner_pfad = os.path.join(rewe_dir, ordner)
                if os.path.isdir(ordner_pfad) and ordner != "temp":
                    try:
                        ordner_datum = datetime.datetime.strptime(ordner, '%Y-%m-%d')
                        alter = (heute - ordner_datum).days
                        if alter > 7:
                            shutil.rmtree(ordner_pfad)
                    except: pass

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=25, weight="bold", color="white"))
            
            bereinige_archiv()
            
            base_dl = "/storage/emulated/0/Download" if os.path.exists("/storage/emulated/0/Download") else os.path.join(os.path.expanduser("~"), "Downloads")
            rewe_dir = os.path.join(base_dl, "REWE")
            
            pdfs_gefunden = False
            if os.path.exists(rewe_dir):
                ordner_liste = sorted([o for o in os.listdir(rewe_dir) if os.path.isdir(os.path.join(rewe_dir, o)) and o != "temp"], reverse=True)
                for ordner in ordner_liste:
                    ordner_pfad = os.path.join(rewe_dir, ordner)
                    p_list = [f for f in os.listdir(ordner_pfad) if f.endswith(".pdf")]
                    
                    if p_list:
                        ansicht.controls.append(ft.Text(ordner, color="yellow", weight="bold", size=16))
                        for pdf in p_list:
                            pdfs_gefunden = True
                            
                            def mail_senden(e, d=pdf):
                                page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject=REWE Monitoring Bericht: {d}&body=Bitte den Bericht im Anhang manuell anfuegen.")
                                
                            ansicht.controls.append(
                                ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                                    content=ft.Row([
                                        ft.Text(pdf, color="white", size=12, expand=True), 
                                        sicherer_button("📧 Mail versenden", mail_senden, "blue", "white")
                                    ])
                                )
                            )
                        ansicht.controls.append(ft.Divider(color="white24"))
                        
            if not pdfs_gefunden:
                ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="grey", size=14))
                
            page.update()
            
        def zeige_postausgang():
            ansicht.controls.clear(); ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
            temp_dir, final_dir, heute_ordner = get_rewe_paths()
            
            def oeffne_ordner(e):
                try: page.launch_url(f"file://{final_dir}")
                except: pass
                
            ansicht.controls.append(
                ft.Row([
                    ft.Text("Die Berichte für heute liegen im Ordner:", color="red", size=12, expand=True),
                    sicherer_button("📂 Ordner öffnen", oeffne_ordner, "blue", "white")
                ])
            )
            ansicht.controls.append(ft.Text(f"Downloads / REWE / {heute_ordner} /\n", color="red", size=14, weight="bold"))
            ansicht.controls.append(ft.Text("TIPP: Gehe ins Archiv, um Berichte per Mail zu versenden!", color="red", size=12))
            ansicht.controls.append(ft.Container(height=10))
            
            p_list = [f for f in os.listdir(final_dir) if f.endswith(".pdf")] if os.path.exists(final_dir) else []
            if not p_list: ansicht.controls.append(ft.Text("Noch keine Berichte für heute erstellt.", color="grey", size=14))
            for pdf in p_list:
                def rm(e, d=pdf): os.remove(os.path.join(final_dir, d)); zeige_postausgang()
                def oeffne(e, d=pdf): 
                    try: page.launch_url(f"file://{os.path.join(final_dir, d)}")
                    except: pass
                    
                ansicht.controls.append(
                    ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                        content=ft.Row([
                            ft.Text(pdf, color="white", size=10, expand=True),
                            sicherer_button("📄 Öffnen", oeffne, "blue", "white"),
                            sicherer_button("🗑️", rm, "red", "white")
                        ])
                    )
                )
            page.update()

        zeige_startbildschirm()
        
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": ft.app(target=main, assets_dir="assets")
