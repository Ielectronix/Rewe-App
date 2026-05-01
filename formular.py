import flet as ft
import datetime
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, lade_vorlagen, speichere_vorlagen
from pdf_generator import erstelle_bericht

def zeige_maske_ui(page: ft.Page, ansicht: ft.Column, nav_leiste, zeige_dashboard, zeige_fehler, markt_index):
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

        # --- FIX FÜR DEN BUTTON (Roter schwarzer Error-Screen ist weg!) ---
        def sicherer_button(text, on_click, bgcolor="blue", color="white", height=None, width=None):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold", text_align=ft.TextAlign.CENTER),
                on_click=on_click, bgcolor=bgcolor, color=color, height=height, width=width,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=10)
            )

        stil_tf_gelb_12 = ft.TextStyle(color="yellow", size=12)
        stil_label_weiss = ft.TextStyle(color="white")
        stil_cb_weiss = ft.TextStyle(color="white", size=12)
        stil_hint_weiss = ft.TextStyle(color="white54", size=12)

        tage_opts = [""] + [f"{i:02d}" for i in range(1, 32)]
        mon_opts = [""] + [f"{i:02d}" for i in range(1, 13)]
        jahr_opts = [""] + [str(i) for i in range(2024, 2035)]
        
        charge_opts_s = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "", "Kein Schweinehackfleisch"]
        charge_opts_r = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "", "Kein Rinderhackfleisch"]
        charge_opts_g = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "", "Kein Geflügel"]
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

        # --- KEIN EXPAND BEI DROPDOWNS ---
        def erstelle_combo(label_text, wert, optionen, groesse=12, breite=None, on_change_func=None):
            def on_txt_change(e):
                if on_change_func: on_change_func(e)
            
            combo = ft.TextField(label=label_text, value=wert, hint_text="Bitte eingeben", color="yellow", text_style=ft.TextStyle(size=groesse, color="yellow"), label_style=stil_label_weiss, border_color="white", dense=True, content_padding=10, width=breite, on_change=on_txt_change)
            
            items = []
            for opt in optionen:
                def erstelle_klick(txt):
                    def klick(e):
                        combo.value = txt; combo.update()
                        if on_change_func: on_change_func(e)
                    return klick
                items.append(ft.PopupMenuItem(content=ft.Text(opt), on_click=erstelle_klick(opt)))
            pb = ft.PopupMenuButton(items=items, content=ft.Text("▼", color="white"))
            combo.suffix = pb 
            return combo

        def hat_charge_wert(val):
            return bool(val and val != "")

        # ==========================================
        # ELEMENTE IM SPEICHER ERSTELLEN
        # ==========================================
        
        # --- 1. STAMMDATEN ---
        d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
        tag_dd = erstelle_combo("Tag", d_tag, tage_opts, breite=80)
        mon_dd = erstelle_combo("Mon", d_mon, mon_opts, breite=80)
        jahr_dd = erstelle_combo("Jahr", d_jahr, jahr_opts, breite=100)
        adr_in = ft.TextField(label="Adresse Markt", value=aktuelle_daten.get("adresse"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10)
        nr_in = ft.TextField(label="Marktnummer", value=aktuelle_daten.get("marktnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10)
        auft_in = ft.TextField(label="Auftragsnummer", hint_text="Etikettenummer: XX-XXXXXXX", hint_style=stil_hint_weiss, value=aktuelle_daten.get("auftragsnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10)
        name_in = ft.TextField(label="Name Probenehmer", value=aktuelle_daten.get("mitarbeiter_name"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10)
        bem_in = ft.TextField(label="Zusätzliche Bemerkung", value=aktuelle_daten.get("bemerkung"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10)
        ag_dd = erstelle_combo("Auftraggeber", aktuelle_daten.get("auftraggeber", ""), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund (Hackfleischmonitoring)"])
        typ_dd = erstelle_combo("Typ der Probenahme", aktuelle_daten.get("typ_probenahme", "Standard"), ["Standard", "Nachkontrolle", "Mehrwöchig"])

        lims_warnung = ft.Text("⚠️ HINWEIS: Aktivierungs-Haken fehlt!", color="red", weight="bold", visible=False)
        lims_override_cb = ft.Checkbox(label="Trotzdem speichern", visible=False, label_style=stil_cb_weiss, fill_color="red", check_color="white")

        def pruefe_lims_warnung(e=None):
            # ... Warnungslogik ...
            lims_warnung.visible = False # Kann später detailliert implementiert werden
            page.update()

        def format_zeit(e):
            val = e.control.value or ""
            zahlen = "".join([c for c in val if c.isdigit()])[:4]
            neu_wert = zahlen[:2] + ":" + zahlen[2:] if len(zahlen) >= 3 else zahlen
            if e.control.value != neu_wert:
                e.control.value = neu_wert
                e.control.update()

        def format_temp_blur(e):
            val = (e.control.value or "").strip().replace(" °C", "").replace("°C", "").strip()
            e.control.value = val + " °C" if val else ""
            e.control.update()

        def format_gramm_blur(e):
            val = (e.control.value or "").strip()
            if val and not val.lower().endswith("g") and not val.lower().endswith("ml"):
                e.control.value = val + " g"
                e.control.update()

        # --- 2. TRINKWASSER ---
        tw_kalt_cb = ft.Checkbox(label="Trinkwasser kalt", value=aktuelle_daten.get("tw_kalt", False), label_style=stil_label_weiss, fill_color="yellow", check_color="black")
        tw_zeit_in = ft.TextField(label="Probenahmezeit", value=aktuelle_daten.get("tw_zeit"), border_color="white", color="yellow", label_style=stil_label_weiss, on_change=format_zeit, content_padding=10, text_style=stil_tf_gelb_12)
        tw_temp_in = ft.TextField(label="Temp Probenahme", value=aktuelle_daten.get("tw_temp"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12)
        tw_tempkonst_in = ft.TextField(label="Temp Konstante", value=aktuelle_daten.get("tw_tempkonst"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12)
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
        tw_bemerkung_dd = erstelle_combo("TW Bemerkung", aktuelle_daten.get("tw_bemerkung_2", ""), ["", "Keine Besonderheiten"])
        cb_pn = ft.Checkbox(label="PN-Hahn", value=aktuelle_daten.get("tw_cb_pn", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_zwei = ft.Checkbox(label="Zweigriff", value=aktuelle_daten.get("tw_cb_zwei", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_sensor = ft.Checkbox(label="Sensor", value=aktuelle_daten.get("tw_cb_sensor", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_knie = ft.Checkbox(label="Knie", value=aktuelle_daten.get("tw_cb_knie", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_ein = ft.Checkbox(label="Einhebel", value=aktuelle_daten.get("tw_cb_ein", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_ein_g = ft.Checkbox(label="Eingriff", value=aktuelle_daten.get("tw_cb_ein_g", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_eck = ft.Checkbox(label="Eckventil", value=aktuelle_daten.get("tw_cb_eck", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_ja = ft.Checkbox(label="ja", value=aktuelle_daten.get("tw_auff_ja", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_nein = ft.Checkbox(label="nein", value=aktuelle_daten.get("tw_auff_nein", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_perl = ft.Checkbox(label="Perlator nicht entfernbar", value=aktuelle_daten.get("tw_auff_perlator", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_verkalk = ft.Checkbox(label="Starke Verkalkung", value=aktuelle_daten.get("tw_auff_kalk", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_verbrueh = ft.Checkbox(label="Armatur mit Verbrühschutz", value=aktuelle_daten.get("tw_auff_verbrueh", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_durchlauf = ft.Checkbox(label="Durchlauferhitzer", value=aktuelle_daten.get("tw_auff_durchlauf", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_unterbau = ft.Checkbox(label="Unterbauspeicher", value=aktuelle_daten.get("tw_auff_unterbau", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_eck_zu = ft.Checkbox(label="Eckventil warm/kalt geschlossen", value=aktuelle_daten.get("tw_auff_eckventil", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_nichtmoeglich = ft.Checkbox(label="nicht möglich", value=aktuelle_daten.get("tw_auff_unmoeglich", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_dusche = ft.Checkbox(label="Entnahme aus der Dusche", value=aktuelle_daten.get("tw_auff_dusche", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_handbrause = ft.Checkbox(label="Handbrause", value=aktuelle_daten.get("tw_auff_handbrause", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        cb_auff_sonst = ft.Checkbox(label="Sonstiges", value=aktuelle_daten.get("tw_auff_sonstiges", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        tw_auff_sonstiges_in = ft.TextField(label="Auffälligkeiten (Sonstiges)", value=aktuelle_daten.get("tw_auff_sonst_text"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12)
        tw_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("tw_inhalt", "ca. 500 ml"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12)
        
        # --- 3. SCHERBENEIS FELDER ---
        se_kalt_cb = ft.Checkbox(label="Scherbeneis Eigenkontrolle", value=aktuelle_daten.get("se_kalt", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
        se_zeit_in = ft.TextField(label="Probenahmezeit", value=aktuelle_daten.get("se_zeit"), border_color="white", color="yellow", label_style=stil_label_weiss, on_change=format_zeit, content_padding=10, text_style=stil_tf_gelb_12)
        se_zapf_dd = erstelle_combo("Zapfstelle (Eis)", aktuelle_daten.get("se_zapf", "Eismaschine"), ["Eismaschine"])
        se_cb_eiswanne = ft.Checkbox(label="Eiswanne/Schöpfprobe", value=aktuelle_daten.get("se_cb_eiswanne", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        se_cb_fallprobe = ft.Checkbox(label="Fallprobe", value=aktuelle_daten.get("se_cb_fallprobe", True), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        se_tech_sonst_in = ft.TextField(label="Sonstiges (Technik)", value=aktuelle_daten.get("se_tech_sonst"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12)
        se_desinf_dd = erstelle_combo("Art der Desinfektion", aktuelle_daten.get("se_desinf", "ohne Desinfektion"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
        se_cb_ozon = ft.Checkbox(label="Ozonsterilisator", value=aktuelle_daten.get("se_cb_ozon", False), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
        se_auff_sonst_in = ft.TextField(label="Sonstiges (Auffälligkeiten)", value=aktuelle_daten.get("se_auff_sonst"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12)
        se_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("se_inhalt", "ca. 1000ml"), color="yellow", label_style=stil_label_weiss, content_padding=10, text_style=stil_tf_gelb_12)
        se_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("se_verpackung", "steriler Probenbeutel"), ["steriler Probenbeutel"])
        se_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("se_entnahmeort", "Fischabteilung-Eismaschine"), ["Fischabteilung-Eismaschine", "Metzgerei", "Produktionsraum"])
        se_temp_in = ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get("se_temp"), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12)
        se_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("se_bemerkung", ""), ["", "Keine Besonderheiten"])

        # --- OKZ SCHERBENEIS ---
        se_okz_cb = ft.Checkbox(label="Abklatschproben Scherbeneis", value=aktuelle_daten.get("se_abklatsch_cb", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
        se_okz_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("se_abklatsch_bemerkung", ""), ["", "Keine Besonderheiten"])
        se_okz_status_opts = ["R+D", "R", "P", "-"]
        se_okz_objekt_opts = ["Eiswanne innen rechts", "Eiswanne innen links", "Auswurfrohr", "Eisschaufel", "Eiswanne", "Eismaschine innen", "Klappe/Deckel", "Sonstiges"]
        se_okz_ort_opts = ["Fischabteilung", "Metzgerei", "Produktionsbereich", "Kühlraum"]
        se_okz_defaults = {1: {"obj": "Eiswanne innen rechts", "abk": True, "tup": True}, 2: {"obj": "Eiswanne innen links", "abk": True, "tup": True}, 3: {"obj": "Auswurfrohr", "abk": True, "tup": True}}
        se_okz_controls = {}
        for i in range(1, 4):
            idx = f"{i:02d}"
            se_okz_controls[idx] = {
                "status": erstelle_combo("Status", aktuelle_daten.get(f"0003_status_{idx}", "R+D"), se_okz_status_opts, breite=100),
                "objekt": erstelle_combo("Objekt", aktuelle_daten.get(f"0003_objekt_{idx}", se_okz_defaults[i]["obj"]), se_okz_objekt_opts, breite=200),
                "ort": erstelle_combo("Probenahmeort", aktuelle_daten.get(f"0003_ort_{idx}", ""), se_okz_ort_opts),
                "abklatsch": ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"0003_abklatsch_{idx}", se_okz_defaults[i]["abk"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black"),
                "tupfer": ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"0003_tupfer_{idx}", se_okz_defaults[i]["tup"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            }

        # --- 4. HFM Hack ---
        hfm_hack_cb = ft.Checkbox(label="Hackfleisch gemischt", value=aktuelle_daten.get("hfm_hack_cb", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
        hfm_hack_entnahmeort_dd = erstelle_combo("Entnahmeort", aktuelle_daten.get("hfm_hack_entnahmeort", "Kühlraum"), entnahmeort_opts)
        hfm_h_t, hfm_h_m, hfm_h_j = parse_datum(aktuelle_daten.get("hfm_hack_herstelldatum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
        hfm_hack_herst_tag_dd = erstelle_combo("Tag", hfm_h_t, tage_opts, breite=80)
        hfm_hack_herst_mon_dd = erstelle_combo("Mon", hfm_h_m, mon_opts, breite=80)
        hfm_hack_herst_jahr_dd = erstelle_combo("Jahr", hfm_h_j, jahr_opts, breite=100)
        mhd_s_t, mhd_s_m, mhd_s_j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_schwein", ""))
        hfm_hack_mhd_s_tag_dd = erstelle_combo("Tag", mhd_s_t, tage_opts, breite=80)
        hfm_hack_mhd_s_mon_dd = erstelle_combo("Mon", mhd_s_m, mon_opts, breite=80)
        hfm_hack_mhd_s_jahr_dd = erstelle_combo("Jahr", mhd_s_j, jahr_opts, breite=100)
        mhd_r_t, mhd_r_m, mhd_r_j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_rind", ""))
        hfm_hack_mhd_r_tag_dd = erstelle_combo("Tag", mhd_r_t, tage_opts, breite=80)
        hfm_hack_mhd_r_mon_dd = erstelle_combo("Mon", mhd_r_m, mon_opts, breite=80)
        hfm_hack_mhd_r_jahr_dd = erstelle_combo("Jahr", mhd_r_j, jahr_opts, breite=100)
        hfm_hack_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("hfm_hack_inhalt", "jeweils ca. 200 g"), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, on_blur=format_gramm_blur)
        hfm_hack_verpackung_dd = erstelle_combo("Verpackung", aktuelle_daten.get("hfm_hack_verpackung", "steriler Probenbeutel"), verpackung_opts)
        hfm_hack_lief_schwein_in = ft.TextField(label="Lieferant (Schwein)", value=aktuelle_daten.get("hfm_hack_lief_schwein", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12)
        hfm_hack_lief_rind_in = ft.TextField(label="Lieferant (Rind)", value=aktuelle_daten.get("hfm_hack_lief_rind", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12)
        hfm_hack_charge_schwein_dd = erstelle_combo("Charge Schwein", aktuelle_daten.get("hfm_hack_charge_schwein", ""), charge_opts_s)
        hfm_hack_charge_rind_dd = erstelle_combo("Charge Rind", aktuelle_daten.get("hfm_hack_charge_rind", ""), charge_opts_r)
        hfm_hack_temp_in = ft.TextField(label="Probenahmetemperatur", hint_text="(Soll Schwein/Rind: <+7°C)", hint_style=stil_hint_weiss, value=aktuelle_daten.get("hfm_hack_temp", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12)
        hfm_hack_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_hack_bemerkung", ""), ["", "Keine Besonderheiten"])

        # --- OKZ HFM ---
        hfm_okz_cb = ft.Checkbox(label="Abklatschproben HFM", value=aktuelle_daten.get("hfm_abklatsch_cb", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
        hfm_okz_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("hfm_abklatsch_bemerkung", ""), ["", "Keine Besonderheiten"])
        okz_status_opts = ["R+D", "R", "P", "-"]
        okz_objekt_opts = ["Fleischwolf-Auflage", "Fleischwolf-Lochscheibe", "Fleischwolf-Auswurf", "Fleischwolf-Spirale", "Wand am Fleischwolf", "Hackstecher", "Schaufel", "Thekenschale", "Messer", "Schneidebrett", "Auflage Knochensäge", "Tisch", "Flesichwanne", "Kühlhausgriff", "Schüssel", "Seifenspender"]
        okz_ort_opts = ["Kühlraum", "Produktionsbereich", "Theke"]
        okz_defaults = {1: {"obj": "Fleischwolf-Auflage", "abk": True, "tup": False}, 2: {"obj": "Fleischwolf-Auswurf", "abk": True, "tup": True}, 3: {"obj": "Thekenschale", "abk": True, "tup": False}, 4: {"obj": "Hackstecher", "abk": True, "tup": True}, 5: {"obj": "Messer", "abk": True, "tup": False}, 6: {"obj": "Schneidebrett", "abk": True, "tup": False}, 7: {"obj": "Wand am Fleischwolf", "abk": True, "tup": True}, 8: {"obj": "", "abk": False, "tup": False}, 9: {"obj": "", "abk": False, "tup": False}, 10: {"obj": "", "abk": False, "tup": False}}
        okz_controls = {}
        for i in range(1, 11):
            idx = f"{i:02d}"
            okz_controls[idx] = {
                "status": erstelle_combo("Status", aktuelle_daten.get(f"0010_status_{idx}", "R+D"), okz_status_opts, breite=100),
                "objekt": erstelle_combo("Objekt", aktuelle_daten.get(f"0010_objekt_{idx}", okz_defaults[i]["obj"]), okz_objekt_opts, breite=200),
                "ort": erstelle_combo("Probenahmeort", aktuelle_daten.get(f"0010_ort_{idx}", ""), okz_ort_opts),
                "abklatsch": ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"0010_abklatsch_{idx}", okz_defaults[i]["abk"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black"),
                "tupfer": ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"0010_tupfer_{idx}", okz_defaults[i]["tup"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            }

        # --- Convenience ---
        og_cb = ft.Checkbox(label="Obst-/Gemüse Convenience", value=aktuelle_daten.get("og_cb", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
        og_ort_opts = ["Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Kühlraum", "SB-Theke", "Salatbar", "Saftpresse"]
        og_verpackung_opts = ["SB-Kunststoffverpackung", "SB-Styroporverpackung", "Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie", "steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel"]
        og_controls = {}
        for i in range(1, 6):
            idx = f"{i:02d}"
            h_t_val, h_m_val, h_j_val = parse_datum(aktuelle_daten.get(f"og_herst_{idx}", ""), "", "", "")
            v_t_val, v_m_val, v_j_val = parse_datum(aktuelle_daten.get(f"og_verb_{idx}", ""), "", "", "")
            og_controls[i] = {
                "name": ft.TextField(label=f"Name Teilprobe {i}", value=aktuelle_daten.get(f"og_name_{idx}", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12),
                "ort": erstelle_combo("Entnahmeort", aktuelle_daten.get(f"og_ort_{idx}", ""), og_ort_opts),
                "h_t": erstelle_combo("Tag", h_t_val, tage_opts, breite=80), "h_m": erstelle_combo("Mon", h_m_val, mon_opts, breite=80), "h_j": erstelle_combo("Jahr", h_j_val, jahr_opts, breite=100),
                "v_t": erstelle_combo("Tag", v_t_val, tage_opts, breite=80), "v_m": erstelle_combo("Mon", v_m_val, mon_opts, breite=80), "v_j": erstelle_combo("Jahr", v_j_val, jahr_opts, breite=100),
                "inhalt": ft.TextField(label="Inhalt", value=aktuelle_daten.get(f"og_inhalt_{idx}", ""), hint_text="bitte Grammzahl angeben", hint_style=stil_hint_weiss, color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12, on_blur=format_gramm_blur),
                "verpackung": erstelle_combo("Verpackung", aktuelle_daten.get(f"og_verp_{idx}", ""), og_verpackung_opts),
                "temp": ft.TextField(label="Probenahmetemperatur", value=aktuelle_daten.get(f"og_temp_{idx}", ""), border_color="white", color="yellow", label_style=stil_label_weiss, on_blur=format_temp_blur, content_padding=10, text_style=stil_tf_gelb_12)
            }

        # --- OKZ Convenience ---
        og_okz_cb = ft.Checkbox(label="Abklatschproben Convenience", value=aktuelle_daten.get("og_abklatsch_cb", False), label_style=ft.TextStyle(color="white", size=16, weight="bold"), fill_color="yellow", check_color="black")
        og_okz_bemerkung_dd = erstelle_combo("Bemerkungen", aktuelle_daten.get("og_abklatsch_bemerkung_1", ""), ["", "Keine Besonderheiten"])
        og_okz_anmerkung_in = ft.TextField(label="Anmerkung", value=aktuelle_daten.get("og_abklatsch_bemerkung_2", ""), color="yellow", label_style=stil_label_weiss, border_color="white", content_padding=10, text_style=stil_tf_gelb_12)
        og_okz_status_opts = ["R+D", "R", "P", "-"]
        og_okz_objekt_opts = ["Schneidebrett", "Messer", "Saftpresse Auffanggitter", "Saftpresse Rückwand", "Saftpresse Auslass", "Waagenauflage", "Schüssel", "Löffel", "GN-Behälter"]
        og_okz_ort_opts = ["Kühlraum", "Produktionsbereich", "Theke"]
        og_okz_defaults = {1: {"obj": "Schneidebrett", "abk": True, "tup": True}, 2: {"obj": "Messer", "abk": True, "tup": True}, 3: {"obj": "Waagenauflage", "abk": True, "tup": False}, 4: {"obj": "Schüssel", "abk": True, "tup": False}, 5: {"obj": "Löffel", "abk": True, "tup": False}}
        og_okz_controls = {}
        for i in range(1, 6):
            idx = f"{i:02d}"
            og_okz_controls[idx] = {
                "status": erstelle_combo("Status", aktuelle_daten.get(f"0011_status_{idx}", "R+D"), og_okz_status_opts, breite=100),
                "objekt": erstelle_combo("Objekt", aktuelle_daten.get(f"0011_objekt_{idx}", og_okz_defaults[i]["obj"]), og_okz_objekt_opts, breite=200),
                "ort": erstelle_combo("Probenahmeort", aktuelle_daten.get(f"0011_ort_{idx}", ""), og_okz_ort_opts),
                "abklatsch": ft.Checkbox(label="Abklatsch", value=aktuelle_daten.get(f"0011_abklatsch_{idx}", og_okz_defaults[i]["abk"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black"),
                "tupfer": ft.Checkbox(label="Tupfer", value=aktuelle_daten.get(f"0011_tupfer_{idx}", og_okz_defaults[i]["tup"]), label_style=stil_cb_weiss, fill_color="yellow", check_color="black")
            }

        # ==========================================
        # DAS NEUE "CLEAR & LOAD" SYSTEM
        # ==========================================
        tab_content = ft.Column(spacing=15)
        fehler_text = ft.Text("", color="red", weight="bold", visible=False)
        status_text = ft.Text("", color="yellow", weight="bold", size=16)

        # Die Sub-Tab Container für HFM, Eis und Convenience
        sub_tab_content = ft.Column(spacing=15)

        def switch_tab(tab_name):
            tab_content.controls.clear()
            sub_tab_content.controls.clear()
            
            # Button Farben zurücksetzen
            btn_stamm.bgcolor = "red" if tab_name == "stamm" else "blue"
            btn_tw.bgcolor = "red" if tab_name == "tw" else "blue"
            btn_se.bgcolor = "red" if tab_name == "se" else "blue"
            btn_hfm.bgcolor = "red" if tab_name == "hfm" else "blue"
            btn_og.bgcolor = "red" if tab_name == "og" else "blue"

            if tab_name == "stamm":
                tab_content.controls.extend([
                    datum_row, adr_in, nr_in, auft_in, ag_dd, name_in, typ_dd, bem_in
                ])

            elif tab_name == "tw":
                tab_content.controls.extend([
                    ft.Divider(height=10, color="transparent"),
                    ft.Text("Trinkwasser-Check", size=20, weight="bold"),
                    tw_kalt_cb, tw_zeit_in, tw_temp_in, tw_tempkonst_in,
                    ft.Divider(color="white24"),
                    ft.Text("Probenahme / Zapfstelle:", color="white", weight="bold"),
                    tw_entnahmeort_dd, tw_zapf_dd, tw_zapf_sonst_dd, tw_desinf_dd,
                    ft.Row([cb_pn, cb_zwei, cb_sensor, cb_knie], wrap=True),
                    ft.Row([cb_ein, cb_ein_g, cb_eck], wrap=True),
                    ft.Divider(color="white24"),
                    ft.Text("Sensorik & Analytik:", color="white", weight="bold"),
                    tw_inaktiv_dd, tw_kurz1_dd, tw_kurz2_dd, tw_kurz3_dd, tw_kurz4_dd,
                    ft.Divider(color="white24"),
                    ft.Text("Auffälligkeiten:", color="white", weight="bold"),
                    ft.Row([cb_auff_ja, cb_auff_nein], wrap=True),
                    cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf,
                    cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich, 
                    cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst,
                    tw_auff_sonstiges_in,
                    ft.Divider(color="white24"),
                    tw_zweck_dd, tw_inhalt_in, tw_verpackung_dd, tw_bemerkung_dd
                ])

            elif tab_name == "se":
                # Sub-Navigation Eis
                btn_se_eis = sicherer_button("❄️ Eis", lambda e: switch_subtab_se("eis"), "red", "white")
                btn_se_okz = sicherer_button("🔬 OKZ", lambda e: switch_subtab_se("okz"), "blue", "white")
                tab_content.controls.append(ft.Row([btn_se_eis, btn_se_okz], wrap=True))
                tab_content.controls.append(ft.Divider(color="white24"))
                tab_content.controls.append(sub_tab_content)
                
                def switch_subtab_se(sub):
                    sub_tab_content.controls.clear()
                    btn_se_eis.bgcolor = "red" if sub == "eis" else "blue"
                    btn_se_okz.bgcolor = "red" if sub == "okz" else "blue"
                    if sub == "eis":
                        sub_tab_content.controls.extend([
                            se_kalt_cb, se_zeit_in, se_zapf_dd, ft.Divider(color="white24"),
                            ft.Text("Probenahmetechnik / Art der Zapfstelle:", color="white", weight="bold"),
                            ft.Row([se_cb_eiswanne, se_cb_fallprobe], wrap=True), se_tech_sonst_in, ft.Divider(color="white24"),
                            se_desinf_dd, ft.Text("Auffälligkeiten:", color="white", weight="bold"),
                            se_cb_ozon, se_auff_sonst_in, ft.Divider(color="white24"),
                            se_inhalt_in, se_verpackung_dd, se_entnahmeort_dd, se_temp_in, se_bemerkung_dd
                        ])
                    elif sub == "okz":
                        sub_tab_content.controls.extend([
                            ft.Text("⚠️ Bitte darauf achten: Haken setzen oder entfernen!", color="orange", weight="bold"),
                            se_okz_cb, ft.Divider(color="white24")
                        ])
                        for i in range(1, 4):
                            idx = f"{i:02d}"; c = se_okz_controls[idx]
                            sub_tab_content.controls.extend([
                                ft.Text(f"Probe {i}", color="yellow", weight="bold", size=14),
                                ft.Row([c["status"], c["objekt"]], wrap=True),
                                c["ort"],
                                ft.Row([c["abklatsch"], c["tupfer"]], wrap=True),
                                ft.Divider(color="white24")
                            ])
                        sub_tab_content.controls.append(se_okz_bemerkung_dd)
                    page.update()
                switch_subtab_se("eis")

            elif tab_name == "hfm":
                btn_hfm_hack = sicherer_button("🥩 Hack", lambda e: switch_subtab_hfm("hack"), "red", "white")
                btn_hfm_mett = sicherer_button("🍖 Mett", lambda e: switch_subtab_hfm("mett"), "blue", "white")
                btn_hfm_okz = sicherer_button("🔬 OKZ", lambda e: switch_subtab_hfm("okz"), "blue", "white")
                tab_content.controls.append(ft.Row([btn_hfm_hack, btn_hfm_mett, btn_hfm_okz], wrap=True)) # Verkürzt für's Testen
                tab_content.controls.append(ft.Divider(color="white24"))
                tab_content.controls.append(sub_tab_content)

                def switch_subtab_hfm(sub):
                    sub_tab_content.controls.clear()
                    btn_hfm_hack.bgcolor = "red" if sub == "hack" else "blue"
                    btn_hfm_mett.bgcolor = "red" if sub == "mett" else "blue"
                    btn_hfm_okz.bgcolor = "red" if sub == "okz" else "blue"
                    
                    if sub == "hack":
                        sub_tab_content.controls.extend([
                            hfm_hack_cb, hfm_hack_entnahmeort_dd, ft.Divider(color="white24"),
                            ft.Text("Herstellungsdatum:", color="white", weight="bold"),
                            ft.Row([hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd], wrap=True),
                            hfm_hack_inhalt_in, hfm_hack_verpackung_dd, ft.Divider(color="white24"),
                            ft.Text("Lieferant:", color="white", weight="bold"),
                            hfm_hack_lief_schwein_in, hfm_hack_lief_rind_in, ft.Divider(color="white24"),
                            ft.Text("MHD-Rohware (Schweinefleisch):", color="yellow", weight="bold", size=12),
                            ft.Row([hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_s_jahr_dd], wrap=True),
                            ft.Text("MHD-Rohware (Rindfleisch):", color="yellow", weight="bold", size=12),
                            ft.Row([hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, hfm_hack_mhd_r_jahr_dd], wrap=True),
                            ft.Divider(color="white24"),
                            ft.Text("Charge Rohware:", color="white", weight="bold"),
                            hfm_hack_charge_schwein_dd, hfm_hack_charge_rind_dd, ft.Divider(color="white24"),
                            hfm_hack_temp_in, hfm_hack_bemerkung_dd
                        ])
                    elif sub == "mett":
                        sub_tab_content.controls.extend([
                            hfm_mett_cb, hfm_mett_entnahmeort_dd, ft.Divider(color="white24"),
                            ft.Text("Herstellungsdatum:", color="white", weight="bold"),
                            ft.Row([hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd], wrap=True),
                            hfm_mett_inhalt_in, hfm_mett_verpackung_dd, ft.Divider(color="white24"),
                            hfm_mett_lief_in, ft.Divider(color="white24"),
                            ft.Text("MHD-Rohware:", color="white", weight="bold"),
                            ft.Row([hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, hfm_mett_mhd_jahr_dd], wrap=True),
                            ft.Divider(color="white24"),
                            hfm_mett_charge_dd, ft.Divider(color="white24"),
                            hfm_mett_temp_in, hfm_mett_bemerkung_dd
                        ])
                    elif sub == "okz":
                        sub_tab_content.controls.extend([
                            ft.Text("⚠️ Bitte darauf achten: Haken setzen oder entfernen!", color="orange", weight="bold"),
                            hfm_okz_cb, ft.Divider(color="white24")
                        ])
                        for i in range(1, 11):
                            idx = f"{i:02d}"; c = okz_controls[idx]
                            sub_tab_content.controls.extend([
                                ft.Text(f"Probe {i}", color="yellow", weight="bold", size=14),
                                ft.Row([c["status"], c["objekt"]], wrap=True),
                                c["ort"],
                                ft.Row([c["abklatsch"], c["tupfer"]], wrap=True),
                                ft.Divider(color="white24")
                            ])
                        sub_tab_content.controls.append(hfm_okz_bemerkung_dd)
                    page.update()
                switch_subtab_hfm("hack")

            elif tab_name == "og":
                btn_og_teil = sicherer_button("🥗 Convenience", lambda e: switch_subtab_og("teil"), "red", "white")
                btn_og_okz = sicherer_button("🔬 OKZ", lambda e: switch_subtab_og("okz"), "blue", "white")
                tab_content.controls.append(ft.Row([btn_og_teil, btn_og_okz], wrap=True))
                tab_content.controls.append(ft.Divider(color="white24"))
                tab_content.controls.append(sub_tab_content)

                def switch_subtab_og(sub):
                    sub_tab_content.controls.clear()
                    btn_og_teil.bgcolor = "red" if sub == "teil" else "blue"
                    btn_og_okz.bgcolor = "red" if sub == "okz" else "blue"
                    if sub == "teil":
                        sub_tab_content.controls.append(og_cb)
                        sub_tab_content.controls.append(ft.Divider(color="white24"))
                        for i in range(1, 6):
                            c = og_controls[i]
                            sub_tab_content.controls.extend([
                                ft.Text(f"Teilprobe {i}", color="yellow", weight="bold", size=14),
                                c["name"], c["ort"],
                                ft.Text("Herstellungsdatum:", color="white", size=12),
                                ft.Row([c["h_t"], c["h_m"], c["h_j"]], wrap=True),
                                ft.Text("Verbrauchsdatum:", color="white", size=12),
                                ft.Row([c["v_t"], c["v_m"], c["v_j"]], wrap=True),
                                c["inhalt"], c["verpackung"], c["temp"],
                                ft.Divider(color="white24")
                            ])
                    elif sub == "okz":
                        sub_tab_content.controls.extend([
                            ft.Text("⚠️ Bitte darauf achten: Haken setzen oder entfernen!", color="orange", weight="bold"),
                            og_okz_cb, ft.Divider(color="white24")
                        ])
                        for i in range(1, 6):
                            idx = f"{i:02d}"; c = og_okz_controls[idx]
                            if i == 2: sub_tab_content.controls.append(ft.Text("💡 Info: Bei Saftpresse bitte hier auswählen.", color="white54", italic=True, size=12))
                            sub_tab_content.controls.extend([
                                ft.Text(f"Probe {i}", color="yellow", weight="bold", size=14),
                                ft.Row([c["status"], c["objekt"]], wrap=True),
                                c["ort"],
                                ft.Row([c["abklatsch"], c["tupfer"]], wrap=True),
                                ft.Divider(color="white24")
                            ])
                        sub_tab_content.controls.extend([
                            ft.Text("💡 Wichtig: Wird die Saftpresse beprobt, muss zwingend auch das Messer aufgenommen werden!", color="orange", weight="bold"),
                            og_okz_bemerkung_dd, og_okz_anmerkung_in
                        ])
                    page.update()
                switch_subtab_og("teil")
            
            page.update()

        # HAUPT-BUTTONS
        btn_stamm = sicherer_button("📋 Stammdaten", lambda e: switch_tab("stamm"), "red", "white")
        btn_tw = sicherer_button("💧 Trinkwasser", lambda e: switch_tab("tw"), "blue", "white")
        btn_se = sicherer_button("❄️ Scherbeneis", lambda e: switch_tab("se"), "blue", "white")
        btn_hfm = sicherer_button("🥩 HFM", lambda e: switch_tab("hfm"), "blue", "white")
        btn_og = sicherer_button("🥗 Convenience", lambda e: switch_tab("og"), "blue", "white")

        def hole_aktuelle_daten():
            def safe_date(t, m, j):
                val = get_date_str(t, m, j)
                return "" if val == ".." else val

            d = {
                "datum": f"{tag_dd.value}.{mon_dd.value}.{jahr_dd.value}", "adresse": adr_in.value, "marktnummer": nr_in.value, "auftragsnummer": auft_in.value, 
                "mitarbeiter_name": name_in.value, "auftraggeber": ag_dd.value, "typ_probenahme": typ_dd.value, "bemerkung": bem_in.value,
                "tw_kalt": tw_kalt_cb.value, "tw_lims_override": lims_override_cb.value, "tw_zeit": tw_zeit_in.value, 
                "tw_temp": tw_temp_in.value, "tw_desinf": tw_desinf_dd.value, "tw_zapf": tw_zapf_dd.value,
                "tw_cb_pn": cb_pn.value, "tw_cb_zwei": cb_zwei.value, "tw_cb_sensor": cb_sensor.value, "tw_cb_knie": cb_knie.value, 
                "tw_cb_ein": cb_ein.value, "tw_cb_ein_g": cb_ein_g.value, "tw_cb_eck": cb_eck.value, "tw_zapf_sonst": tw_zapf_sonst_dd.value,
                "tw_inaktiv": tw_inaktiv_dd.value, "tw_kurz1": tw_kurz1_dd.value, "tw_kurz2": tw_kurz2_dd.value, 
                "tw_kurz3": tw_kurz3_dd.value, "tw_kurz4": tw_kurz4_dd.value, 
                "tw_auff_ja": cb_auff_ja.value, "tw_auff_nein": cb_auff_nein.value, 
                "tw_auff_perlator": cb_auff_perl.value, "tw_auff_kalk": cb_auff_verkalk.value, 
                "tw_auff_verbrueh": cb_auff_verbrueh.value, "tw_auff_durchlauf": cb_auff_durchlauf.value,
                "tw_auff_eckventil": cb_auff_eck_zu.value, "tw_auff_unterbau": cb_auff_unterbau.value, 
                "tw_auff_unmoeglich": cb_auff_nichtmoeglich.value, "tw_auff_dusche": cb_auff_dusche.value, 
                "tw_auff_handbrause": cb_auff_handbrause.value, "tw_auff_sonstiges": cb_auff_sonst.value, 
                "tw_auff_sonst_text": tw_auff_sonstiges_in.value,
                "tw_zweck": tw_zweck_dd.value, "tw_inhalt": tw_inhalt_in.value, "tw_verpackung": tw_verpackung_dd.value, 
                "tw_entnahmeort": tw_entnahmeort_dd.value, "tw_tempkonst": tw_tempkonst_in.value, "tw_bemerkung_2": tw_bemerkung_dd.value,
                
                "se_kalt": se_kalt_cb.value, "se_zeit": se_zeit_in.value, "se_zapf": se_zapf_dd.value,
                "se_cb_eiswanne": se_cb_eiswanne.value, "se_cb_fallprobe": se_cb_fallprobe.value, "se_tech_sonst": se_tech_sonst_in.value,
                "se_desinf": se_desinf_dd.value, "se_cb_ozon": se_cb_ozon.value, "se_auff_sonst": se_auff_sonst_in.value,
                "se_inhalt": se_inhalt_in.value, "se_verpackung": se_verpackung_dd.value, "se_entnahmeort": se_entnahmeort_dd.value,
                "se_temp": se_temp_in.value, "se_bemerkung": se_bemerkung_dd.value,
                "se_abklatsch_cb": se_okz_cb.value, "se_abklatsch_bemerkung": se_okz_bemerkung_dd.value,
                
                "hfm_hack_cb": hfm_hack_cb.value, "hfm_hack_entnahmeort": hfm_hack_entnahmeort_dd.value,
                "hfm_hack_herstelldatum": safe_date(hfm_hack_herst_tag_dd.value, hfm_hack_herst_mon_dd.value, hfm_hack_herst_jahr_dd.value), 
                "hfm_hack_inhalt": hfm_hack_inhalt_in.value, "hfm_hack_verpackung": hfm_hack_verpackung_dd.value, 
                "hfm_hack_lief_schwein": hfm_hack_lief_schwein_in.value, "hfm_hack_lief_rind": hfm_hack_lief_rind_in.value, 
                "hfm_hack_mhd_schwein": safe_date(hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value),
                "hfm_hack_mhd_rind": safe_date(hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value), 
                "hfm_hack_charge_schwein": hfm_hack_charge_schwein_dd.value, "hfm_hack_charge_rind": hfm_hack_charge_rind_dd.value, 
                "hfm_hack_temp": hfm_hack_temp_in.value, "hfm_hack_bemerkung": hfm_hack_bemerkung_dd.value,
                
                "hfm_mett_cb": hfm_mett_cb.value, "hfm_mett_entnahmeort": hfm_mett_entnahmeort_dd.value,
                "hfm_mett_herstelldatum": safe_date(hfm_mett_herst_tag_dd.value, hfm_mett_herst_mon_dd.value, hfm_mett_herst_jahr_dd.value),
                "hfm_mett_inhalt": hfm_mett_inhalt_in.value, "hfm_mett_verpackung": hfm_mett_verpackung_dd.value,
                "hfm_mett_lief": hfm_mett_lief_in.value, 
                "hfm_mett_mhd": safe_date(hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value),
                "hfm_mett_charge": hfm_mett_charge_dd.value, "hfm_mett_temp": hfm_mett_temp_in.value,
                "hfm_mett_bemerkung": hfm_mett_bemerkung_dd.value,
                
                "hfm_abklatsch_cb": hfm_okz_cb.value, "hfm_abklatsch_bemerkung": hfm_okz_bemerkung_dd.value,
                "og_cb": og_cb.value, 
                "og_abklatsch_cb": og_okz_cb.value, "og_abklatsch_bemerkung_1": og_okz_bemerkung_dd.value,
                "og_abklatsch_bemerkung_2": og_okz_anmerkung_in.value
            }
            
            for idx_str, ctrls in se_okz_controls.items():
                d[f"0003_status_{idx_str}"] = ctrls["status"].value
                d[f"0003_objekt_{idx_str}"] = ctrls["objekt"].value
                d[f"0003_ort_{idx_str}"] = ctrls["ort"].value
                d[f"0003_abklatsch_{idx_str}"] = ctrls["abklatsch"].value
                d[f"0003_tupfer_{idx_str}"] = ctrls["tupfer"].value
                
            for idx_str, ctrls in okz_controls.items():
                d[f"0010_status_{idx_str}"] = ctrls["status"].value
                d[f"0010_objekt_{idx_str}"] = ctrls["objekt"].value
                d[f"0010_ort_{idx_str}"] = ctrls["ort"].value
                d[f"0010_abklatsch_{idx_str}"] = ctrls["abklatsch"].value
                d[f"0010_tupfer_{idx_str}"] = ctrls["tupfer"].value
                
            for i in range(1, 6):
                idx = f"{i:02d}"; ctrls = og_controls[i]
                d[f"og_name_{idx}"] = ctrls["name"].value
                d[f"og_ort_{idx}"] = ctrls["ort"].value
                d[f"og_herst_{idx}"] = safe_date(ctrls["h_t"].value, ctrls["h_m"].value, ctrls["h_j"].value)
                d[f"og_verb_{idx}"] = safe_date(ctrls["v_t"].value, ctrls["v_m"].value, ctrls["v_j"].value)
                d[f"og_inhalt_{idx}"] = ctrls["inhalt"].value
                d[f"og_verp_{idx}"] = ctrls["verpackung"].value
                d[f"og_temp_{idx}"] = ctrls["temp"].value
                
            for idx_str, ctrls in og_okz_controls.items():
                d[f"0011_status_{idx_str}"] = ctrls["status"].value
                d[f"0011_objekt_{idx_str}"] = ctrls["objekt"].value
                d[f"0011_ort_{idx_str}"] = ctrls["ort"].value
                d[f"0011_abklatsch_{idx_str}"] = ctrls["abklatsch"].value
                d[f"0011_tupfer_{idx_str}"] = ctrls["tupfer"].value
                
            return d

        def nur_speichern(e):
            if not (nr_in.value or "").strip():
                switch_tab("stamm")
                fehler_text.value="⚠️ MARKTNUMMER FEHLT! (Wird als Name für die Tour benötigt)"
                fehler_text.visible=True; status_text.value=""; page.update(); return
            try:
                fehler_text.visible = False
                status_text.value = "⏳ Speichere Tour..."
                status_text.color = "yellow"; page.update()
                maerkte = lade_maerkte()
                d = hole_aktuelle_daten()
                tour_aktualisiert = False
                for i, tour in enumerate(maerkte):
                    if tour.get("marktnummer") == nr_in.value:
                        maerkte[i] = d
                        tour_aktualisiert = True
                        break
                if not tour_aktualisiert: maerkte.append(d)
                speichere_maerkte(maerkte)
                status_text.value = "✅ Tour erfolgreich gespeichert!"; status_text.color = "orange"; page.update()
            except Exception as ex: 
                status_text.value = "❌ Fehler"; status_text.color = "red"; zeige_fehler(ex)
        
        def save_final(e):
            if not (nr_in.value or "").strip() or not (auft_in.value or "").strip() or not (adr_in.value or "").strip() or not (name_in.value or "").strip():
                switch_tab("stamm")
                fehler_text.value="⚠️ PFLICHTFELDER FEHLEN: Adresse, Probenehmer, Markt- und Auftragsnummer!"
                fehler_text.visible=True; status_text.value=""; page.update(); return
            try:
                fehler_text.visible = False
                status_text.value = "⏳ Speichere und erstelle PDF..."
                status_text.color = "yellow"; page.update()
                maerkte = lade_maerkte()
                d = hole_aktuelle_daten()
                if markt_index is None: maerkte.append(d)
                else: maerkte[markt_index] = d
                speichere_maerkte(maerkte)
                try:
                    saved_path = erstelle_bericht(d)
                    status_text.value = f"✅ PDF erstellt!\nGespeichert in:\n{saved_path}"
                    status_text.color = "green"
                except Exception as ex:
                    status_text.value = ""
                    fehler_text.value = f"⚠️ SPEICHER-FEHLER: {str(ex)}"
                    fehler_text.visible = True
                page.update()
            except Exception as ex: 
                status_text.value = "❌ Fehler"; status_text.color = "red"; zeige_fehler(ex)

        alle_vorlagen = lade_vorlagen()
        vorlagen_status = ft.Text("", weight="bold") 
        vl_dd = ft.Dropdown(options=[ft.dropdown.Option(k) for k in alle_vorlagen.keys()], hint_text="⬇️ Hier Vorlage auswählen...", dense=True, content_padding=10, color="yellow", text_style=ft.TextStyle(color="yellow", weight="bold", size=14), border_color="white")
        vl_name_in = ft.TextField(label="Name für neue Vorlage", color="yellow", text_style=ft.TextStyle(size=12, color="yellow"), label_style=stil_label_weiss, border_color="white", dense=True, content_padding=10)
        
        def lade_v(e):
            if not vl_dd.value: return
            v = alle_vorlagen.get(vl_dd.value, {})
            # (Die Werte werden hier reingeladen, stark gekürzt für Übersicht)
            if "name_in" in v: name_in.value = v["name_in"]
            if "ag_dd" in v: ag_dd.value = v["ag_dd"]
            if "typ_dd" in v: typ_dd.value = v["typ_dd"]
            if "bem_in" in v: bem_in.value = v["bem_in"]
            vorlagen_status.value = f"✅ '{vl_dd.value}' geladen!"
            vorlagen_status.color = "green"
            page.update()

        def del_v(e):
            if vl_dd.value in alle_vorlagen:
                del alle_vorlagen[vl_dd.value]
                speichere_vorlagen(alle_vorlagen)
                vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                vorlagen_status.value = f"🗑️ Gelöscht!"
                vorlagen_status.color = "red"
                vl_dd.value = None
                page.update()
        
        def save_v(e):
            if not (vl_name_in.value or "").strip(): return
            d_v = {"name_in": name_in.value, "ag_dd": ag_dd.value, "typ_dd": typ_dd.value, "bem_in": bem_in.value}
            alle_vorlagen[vl_name_in.value] = d_v
            speichere_vorlagen(alle_vorlagen)
            vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
            vorlagen_status.value = f"✅ Vorlage gespeichert!"
            vorlagen_status.color = "orange"
            vl_name_in.value = ""
            page.update()

        vl_load_btn = sicherer_button("Laden", lade_v, "blue", "white")
        vl_del_btn = sicherer_button("🗑️", del_v, "red", "white")
        vl_save_btn = sicherer_button("Speichern", save_v, "orange", "black")
        
        vorlagen_container = ft.Container(
            bgcolor="#002200", padding=10, border_radius=10,
            content=ft.Column([
                ft.Row([ft.Text("📋 Vorlagen", color="white", weight="bold", size=14), vorlagen_status]),
                vl_dd,
                ft.Row([vl_load_btn, vl_del_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color="white24"),
                vl_name_in,
                ft.Row([vl_save_btn], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=5)
        )

        btn_zurueck = sicherer_button("🚚 Touren", lambda e: zeige_dashboard(), "red", "white")
        btn_speichern = sicherer_button("💾 Speichern", nur_speichern, "orange", "black")
        btn_final = sicherer_button("📄 Bericht", save_final, "blue", "white")

        # --- ZUSAMMENBAU DES HAUPT-LAYOUTS ---
        ansicht.controls.extend([
            ft.Row([btn_stamm, btn_tw, btn_se, btn_hfm, btn_og], wrap=True, alignment=ft.MainAxisAlignment.CENTER),
            lims_warnung, lims_override_cb, vorlagen_container,
            ft.Divider(color="white"),
            ft.Text(titel, size=20, weight="bold", color="white"),
            tab_content, # <--- HIER PASSIERT DIE MAGIE! Nur der aktive Tab wird hier reingeladen!
            ft.Container(height=20),
            fehler_text, status_text,
            ft.Row([btn_zurueck, btn_speichern], wrap=True, alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([btn_final], wrap=True, alignment=ft.MainAxisAlignment.CENTER)
        ])
        
        # Startzustand: Lade Stammdaten
        switch_tab("stamm")
        
    except Exception as intern_e:
        if zeige_fehler: zeige_fehler(intern_e)
