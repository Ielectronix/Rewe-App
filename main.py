import flet as ft
import traceback
import json
import os
import datetime
import shutil
import urllib.parse
 
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
        heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
        primary_base = "/storage/emulated/0/Download"
        fallback_base = "/storage/emulated/0/Android/media"
        desktop_base = os.path.join(os.path.expanduser("~"), "Downloads")
 
        if os.path.exists(primary_base):
            rewe_dir = os.path.join(primary_base, "REWE")
            try:
                os.makedirs(rewe_dir, exist_ok=True)
                test_file = os.path.join(rewe_dir, ".test_write")
                with open(test_file, "w") as f: f.write("ok")
                os.remove(test_file)
                display_pfad = "Downloads / REWE"
            except (PermissionError, OSError):
                rewe_dir = os.path.join(fallback_base, "REWE")
                os.makedirs(rewe_dir, exist_ok=True)
                display_pfad = "Android / media / REWE"
        elif os.path.exists(fallback_base):
            rewe_dir = os.path.join(fallback_base, "REWE")
            os.makedirs(rewe_dir, exist_ok=True)
            display_pfad = "Android / media / REWE"
        else:
            rewe_dir = os.path.join(desktop_base, "REWE")
            display_pfad = "Downloads / REWE"
 
        temp_dir = os.path.join(rewe_dir, "temp")
        final_dir = os.path.join(rewe_dir, heute_ordner)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_dir, exist_ok=True)
        return temp_dir, final_dir, heute_ordner, display_pfad
 
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
            stil_label_weiss = ft.TextStyle(color="white")
            stil_hint_weiss = ft.TextStyle(color="white", size=12)
            
            v_in = ft.TextField(label="Vorname", hint_text="Dein Vorname", hint_style=stil_hint_weiss, value=v, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            z_in = ft.TextField(label="Nachname", hint_text="Dein Nachname", hint_style=stil_hint_weiss, value=z, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value); zeige_dashboard()
                
            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            header = ft.Text(spans=[ft.TextSpan("REWE ", ft.TextStyle(color="red", weight="bold", size=32)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=32))], text_align=ft.TextAlign.CENTER)
            ansicht.controls.extend([ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(height=40), ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)])
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
                    t = (t or "").strip()
                    m = (m or "").strip()
                    j = (j or "").strip()
                    if not t and not m and not j: return ""
                    return f"{t}.{m}.{j}"
                def erstelle_combo(label_text, wert, optionen, groesse=12, ausdehnbar=1, on_change_func=None):
                    def on_txt_change(e):
                        if on_change_func: on_change_func(e)
                    combo = ft.TextField(
                        label=label_text, value=wert, color="yellow", 
                        text_style=ft.TextStyle(size=groesse, color="yellow"), label_style=stil_label_weiss, 
                        border_color="white", expand=ausdehnbar, content_padding=5, 
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
 
                def hat_charge_wert(val): return bool(val and val != "Bitte eingeben")
                def cb_row(links, rechts): return ft.Row([ft.Container(links, expand=1), ft.Container(rechts, expand=1)], vertical_alignment=ft.CrossAxisAlignment.CENTER)
 
                # --- 1. STAMMDATEN FELDER ---
                d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                tag_dd = erstelle_combo("Tag", d_tag, tage_opts, ausdehnbar=3)
                mon_dd = erstelle_combo("Mon", d_mon, mon_opts, ausdehnbar=3)
                jahr_dd = erstelle_combo("Jahr", d_jahr, jahr_opts, ausdehnbar=4)
 
                datum_row = ft.Column([ft.Text("Datum der Probenahme", color="white", weight="bold"), ft.Row([tag_dd, mon_dd, jahr_dd])])
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
                    lims_warnung.visible = braucht_warnung; lims_override_cb.visible = braucht_warnung
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
                
                cb_auff_unterbau = ft.Checkbox(label="Unterbauspeicher [L]", value=aktuelle_daten.get("cb_auff_unterbau", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                tw_unterbau_l_in = ft.TextField(value=aktuelle_daten.get("tw_unterbau_l"), hint_text="Literangabe", hint_style=ft.TextStyle(color="white", size=12), expand=True, height=45, content_padding=10, text_style=stil_tf_gelb_12, color="yellow", border_color="white")
                
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
                    def_obj = se_okz_defaults[i]["obj"]
                    def_abk = se_okz_defaults[i]["abk"]
                    def_tup = se_okz_defaults[i]["tup"]
                    
                    s_dd = erstelle_combo("Status", aktuelle_daten.get(f"se_okz_status_{idx}", "R+D"), se_okz_status_opts)
                    obj_dd = erstelle_combo("Objekt", aktuelle_daten.get(f"se_okz_objekt_{idx}", def_obj), se_okz_objekt_opts)
                    ort_dd = erstelle_combo("Probenahmeort", aktuelle_daten.get(f"se_okz_ort_{idx}", ""), se_okz_ort_opts, on_change_func=pruefe_lims_warnung)
                    
                    abk_cb = ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"se_okz_abklatsch_{idx}", def_abk), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    tup_cb = ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"se_okz_tupfer_{idx}", def_tup), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    
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
                    def_obj = okz_defaults[i]["obj"]
                    def_abk = okz_defaults[i]["abk"]
                    def_tup = okz_defaults[i]["tup"]
                    
                    s_dd = erstelle_combo("Status", aktuelle_daten.get(f"okz_status_{idx}", "R+D"), okz_status_opts)
                    obj_dd = erstelle_combo("Objekt", aktuelle_daten.get(f"okz_objekt_{idx}", def_obj), okz_objekt_opts)
                    ort_dd = erstelle_combo("Probenahmeort", aktuelle_daten.get(f"okz_ort_{idx}", ""), okz_ort_opts)
                    
                    abk_cb = ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"okz_abklatsch_{idx}", def_abk), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    tup_cb = ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"okz_tupfer_{idx}", def_tup), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    
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
                    
                    og_controls[i] = {
                        "name": og_name_in, "ort": ort_dd,
                        "h_t": h_t, "h_m": h_m, "h_j": h_j,
                        "v_t": v_t, "v_m": v_m, "v_j": v_j,
                        "inhalt": inhalt_in, "verpackung": verp_dd, "temp": temp_in
                    }
                    
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
                    def_obj = og_okz_defaults[i]["obj"]
                    def_abk = og_okz_defaults[i]["abk"]
                    def_tup = og_okz_defaults[i]["tup"]
                    
                    if i == 2:
                        og_okz_felder.append(ft.Text("💡 Info: Bei Saftpresse bitte hier auswählen.", color="white54", italic=True, size=12))
 
                    s_dd = erstelle_combo("Status", aktuelle_daten.get(f"og_okz_status_{idx}", "R+D"), og_okz_status_opts)
                    obj_dd = erstelle_combo("Objekt", aktuelle_daten.get(f"og_okz_objekt_{idx}", def_obj), og_okz_objekt_opts)
                    ort_dd = erstelle_combo("Probenahmeort", aktuelle_daten.get(f"og_okz_ort_{idx}", ""), og_okz_ort_opts)
                    
                    abk_cb = ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"og_okz_abklatsch_{idx}", def_abk), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    tup_cb = ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"og_okz_tupfer_{idx}", def_tup), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
                    
                    og_okz_controls[idx] = {"status": s_dd, "objekt": obj_dd, "ort": ort_dd, "abklatsch": abk_cb, "tupfer": tup_cb}
                    
                    og_okz_felder.append(ft.Text(f"Probe {i}", color="yellow", weight="bold", size=14))
                    og_okz_felder.append(ft.Row([s_dd, obj_dd]))
                    og_okz_felder.append(ft.Row([ort_dd]))
                    og_okz_felder.append(ft.Row([abk_cb, tup_cb], alignment=ft.MainAxisAlignment.SPACE_AROUND))
                    og_okz_felder.append(ft.Divider(color="white24"))
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
 
                btn_zurueck = sicherer_button("🔙 Touren", lambda e: zeige_dashboard(), "red", "white", expand=True, height=45)
                btn_speichern = sicherer_button("💾 Tour speichern", nur_speichern, "orange", "black", expand=True, height=45)
                btn_final = sicherer_button("📄 Bericht erstellen (PDF)", save_final, "blue", "white", expand=True, height=50)
 
                _, _, _, ui_pfad = get_rewe_paths()
                info_pfad_text = ft.Text(f"ℹ️ PDFs werden automatisch gespeichert unter:\n{ui_pfad}", color="white54", size=12, italic=True, text_align=ft.TextAlign.CENTER)

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
                    ft.Row([info_pfad_text], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([btn_final])
                ])
                page.update()
                
            except Exception as intern_e:
                zeige_fehler(intern_e)
 
    def bereinige_archiv():
        temp_dir, _, _, _ = get_rewe_paths()
        rewe_dir = os.path.dirname(temp_dir)
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
        
        temp_dir, _, _, display_pfad = get_rewe_paths()
        rewe_dir = os.path.dirname(temp_dir)
        
        def copy_path(e, p):
            page.set_clipboard(p)
            page.show_snack_bar(ft.SnackBar(content=ft.Text("Pfad kopiert! Jetzt in Dateien-App einfügen."), bgcolor="orange"))

        ansicht.controls.append(ft.Container(bgcolor="#222200", padding=10, border_radius=10, content=ft.Column([
            ft.Text("SPEICHERORT FINDEN:", color="orange", weight="bold"),
            ft.Text("Suche diesen Pfad in deiner 'Dateien'-App:", color="white", size=12),
            ft.Text(display_pfad, color="yellow", size=12, weight="bold"),
            sicherer_button("📋 Pfad kopieren", lambda e: copy_path(None, display_pfad), "orange", "black")
        ])))

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
                            subject = urllib.parse.quote(f"REWE Monitoring Bericht: {d}")
                            body = urllib.parse.quote("Bitte den Bericht im Anhang manuell anfuegen.")
                            page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={subject}&body={body}")
                            
                        ansicht.controls.append(
                            ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                                content=ft.Row([
                                    ft.Text(pdf, color="white", size=12, expand=True), 
                                    sicherer_button("📧 Mail vorbereiten", mail_senden, "blue", "white")
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
        temp_dir, final_dir, heute_ordner, display_pfad = get_rewe_paths()
        
        def copy_path(e):
            page.set_clipboard(final_dir)
            page.show_snack_bar(ft.SnackBar(content=ft.Text("Pfad kopiert! Jetzt in Dateien-App einfügen."), bgcolor="blue"))

        ansicht.controls.append(ft.Container(bgcolor="#330000", padding=10, border_radius=10, content=ft.Column([
            ft.Text("DATEIEN VERSENDEN - ANLEITUNG:", color="red", weight="bold"),
            ft.Text("Da Android das direkte Öffnen blockiert, bitte so vorgehen:", color="white", size=12),
            ft.Text("1. Diesen Button drücken:", color="white", size=12),
            sicherer_button("📋 Pfad kopieren", copy_path, "blue", "white"),
            ft.Text("2. Handy-App 'Dateien' öffnen.\n3. Pfad oben in Suche einfügen.\n4. PDFs auswählen und per Mail senden.", color="white", size=12)
        ])))
        
        ansicht.controls.append(ft.Text(f"Aktueller Ordner:\n{display_pfad} / {heute_ordner}", color="yellow", size=12))
        ansicht.controls.append(ft.Container(height=10))
        
        p_list = [f for f in os.listdir(final_dir) if f.endswith(".pdf")] if os.path.exists(final_dir) else []
        if not p_list: ansicht.controls.append(ft.Text("Noch keine Berichte für heute erstellt.", color="grey", size=14))
        for pdf in p_list:
            def rm(e, d=pdf): os.remove(os.path.join(final_dir, d)); zeige_postausgang()
            ansicht.controls.append(
                ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                    content=ft.Row([
                        ft.Text(pdf, color="white", size=10, expand=True),
                        sicherer_button("🗑️", rm, "red", "white")
                    ])
                )
            )
        page.update()
 
    zeige_startbildschirm()
        
if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")