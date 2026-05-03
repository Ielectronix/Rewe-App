import flet as ft
import datetime
import json
import os
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer
from pdf_generator import erstelle_bericht

def lade_vorlagen_lokal():
    try:
        if os.path.exists("tour_vorlagen.json"):
            with open("tour_vorlagen.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {}

def speichere_vorlagen_lokal(daten):
    try:
        with open("tour_vorlagen.json", "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=4)
    except: pass

def zeige_maske_ui(page: ft.Page, ansicht: ft.Column, nav_leiste, zeige_dashboard, zeige_fehler, markt_index):
    try:
        ansicht.controls.clear()
        ansicht.horizontal_alignment = ft.CrossAxisAlignment.CENTER 
        
        fehler_text = ft.Text("", color="red", weight="bold", visible=False, size=14)
        status_text = ft.Text("", color="yellow", weight="bold", size=16, text_align="center")

        maerkte = lade_maerkte()
        v, z = lade_benutzer()
        heute_str = datetime.datetime.now().strftime('%d.%m.%Y')
        
        if markt_index is None:
            aktuelle_daten = {"datum": heute_str, "mitarbeiter_name": f"{v} {z}".strip()}
            titel = "Neue Tour"
        else:
            aktuelle_daten = maerkte[markt_index]
            titel = f"Tour: {aktuelle_daten.get('marktnummer', 'Bearbeiten')}"

        def tf(label, val, hint="", w=320, oc=None, ob=None):
            return ft.TextField(label=label, value=val or "", hint_text=hint, hint_style=ft.TextStyle(color="white54", size=12), color="yellow", text_style=ft.TextStyle(size=12, color="yellow"), label_style=ft.TextStyle(color="white"), border_color="white", content_padding=10, width=w, on_change=oc, on_blur=ob)

        def cb(label, val, oc=None, bold=False):
            return ft.Checkbox(label=label, value=bool(val), on_change=oc, label_style=ft.TextStyle(color="white", size=16 if bold else 12, weight="bold" if bold else "normal"), fill_color="yellow", check_color="black")

        def combo(label, val, opts, w=320, oc=None):
            def intern_oc(e):
                if oc: oc(e)
            echter_wert = val if val else (opts[0] if opts else "")
            c = ft.TextField(label=label, value=echter_wert, color="yellow", text_style=ft.TextStyle(size=12, color="yellow"), label_style=ft.TextStyle(color="white"), border_color="white", dense=True, content_padding=10, width=w, on_change=intern_oc)
            items = [ft.PopupMenuItem(content=ft.Text(o), on_click=lambda e, opt=o: (setattr(c, 'value', opt), c.update(), intern_oc(e))) for o in opts]
            c.suffix = ft.PopupMenuButton(items=items, content=ft.Text("▼", color="white"))
            return c
            
        def action_btn_form(text, oc, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold"),
                on_click=oc, bgcolor="#0b1a0b", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10), 
                    padding=ft.padding.symmetric(vertical=15, horizontal=20),
                    side=ft.BorderSide(width=2, color=farbe)
                )
            )

        def emoji_btn(text, oc, farbe):
            return ft.ElevatedButton(
                text, on_click=oc, bgcolor="#1a1a1a", color=farbe,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10, side=ft.BorderSide(width=1.5, color=farbe))
            )

        def parse_datum(d, dt="", dm="", dj=""):
            if not d: return dt, dm, dj
            p = d.split(".")
            return (p[0], p[1], p[2]) if len(p)==3 else (dt, dm, dj)

        def get_date_str(t, m, j):
            t, m, j = (t or "").strip(), (m or "").strip(), (j or "").strip()
            return f"{t}.{m}.{j}" if (t or m or j) else ""

        def format_zeit(e):
            val = e.control.value or ""
            zahlen = "".join([c for c in val if c.isdigit()])[:4]
            neu = zahlen[:2] + ":" + zahlen[2:] if len(zahlen) >= 3 else zahlen
            if e.control.value != neu: e.control.value = neu; e.control.update()

        def format_temp(e):
            val = (e.control.value or "").strip().replace(" °C", "").replace("°C", "").strip()
            e.control.value = val + " °C" if val else ""; e.control.update()

        def format_gramm(e):
            val = (e.control.value or "").strip()
            if val and not val.lower().endswith("g") and not val.lower().endswith("ml"):
                e.control.value = val + " g"; e.control.update()

        htoday, mtoday, jtoday = heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2]
        def get_herst(key):
            val = str(aktuelle_daten.get(key, "")).strip()
            if not val or len(val.split(".")) != 3 or val == "..":
                return htoday, mtoday, jtoday
            return val.split(".")[0], val.split(".")[1], val.split(".")[2]

        tage_opts = [""] + [f"{i:02d}" for i in range(1, 32)]
        mon_opts = [""] + [f"{i:02d}" for i in range(1, 13)]
        jahr_opts = [""] + [str(i) for i in range(2024, 2035)]
        c_opts_s = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "", "Kein Schweinehackfleisch"]
        c_opts_r = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "", "Kein Rinderhackfleisch"]
        c_opts_g = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "", "Kein Geflügel"]
        ort_opts = ["Fischabteilung", "Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke"]
        verp_opts = ["steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel u. etikett", "Pappschale mit Kunststofffolie umwickelt", "tiefgezogene Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie umwickelt", "SB-Kunststoffverpackung"]

        lims_override_cb = cb("Trotzdem speichern", False)

        d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
        tag_dd, mon_dd, jahr_dd = combo("Tag", d_tag, tage_opts, 90), combo("Mon", d_mon, mon_opts, 90), combo("Jahr", d_jahr, jahr_opts, 120)
        datum_row = ft.Column([ft.Text("Datum der Probenahme", color="white", weight="bold"), ft.Row([tag_dd, mon_dd, jahr_dd], wrap=True)])
        
        adr_in = tf("Adresse Markt", aktuelle_daten.get("adresse", ""))
        nr_in = tf("Marktnummer", aktuelle_daten.get("marktnummer", ""))
        auft_in = tf("Auftragsnummer", aktuelle_daten.get("auftragsnummer", ""), "Etikettenummer: XX-XXXXXXX")
        name_in = tf("Name Probenehmer", aktuelle_daten.get("mitarbeiter_name", ""))
        bem_in = tf("Zusätzliche Bemerkung", aktuelle_daten.get("bemerkung", ""))
        ag_dd = combo("Auftraggeber", aktuelle_daten.get("auftraggeber"), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund (Hackfleischmonitoring)"])
        typ_dd = combo("Typ der Probenahme", aktuelle_daten.get("typ_probenahme"), ["Standard", "Nachkontrolle", "Mehrwöchig"])

        tw_kalt_cb = cb("Trinkwasser kalt", aktuelle_daten.get("tw_kalt", False), bold=True)
        tw_zeit_in, tw_temp_in, tw_tempkonst_in = tf("Probenahmezeit", aktuelle_daten.get("tw_zeit", "")), tf("Temp Probenahme", aktuelle_daten.get("tw_temp", "")), tf("Temp Konstante", aktuelle_daten.get("tw_tempkonst", ""))
        tw_desinf_dd, tw_zapf_dd = combo("Desinfektion", aktuelle_daten.get("tw_desinf"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"]), combo("Zapfstelle", aktuelle_daten.get("tw_zapf"), ["Spülbecken", "Handwaschbecken"])
        tw_zapf_sonst_dd, tw_inaktiv_dd = combo("Sonstiges Zapfstelle", aktuelle_daten.get("tw_zapf_sonst", ""), ["Schlaucharmatur", "Schlauchbrause", "Schlauch mit Brause"]), combo("Inaktivierung", aktuelle_daten.get("tw_inaktiv"), ["Na-Thiosulfat"])
        tw_kurz1_dd, tw_kurz2_dd = combo("Farbe", aktuelle_daten.get("tw_kurz1"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"]), combo("Trübung", aktuelle_daten.get("tw_kurz2"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
        tw_kurz3_dd, tw_kurz4_dd = combo("Bodensatz", aktuelle_daten.get("tw_kurz3"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"]), combo("Geruch", aktuelle_daten.get("tw_kurz4"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
        tw_zweck_dd, tw_verpackung_dd = combo("Zweck", aktuelle_daten.get("tw_zweck"), ["Zweck A", "Zweck B", "Zweck C"]), combo("Verpackung", aktuelle_daten.get("tw_verpackung"), ["500ml Kunststoff-Flasche mit Natriumthiosulfat"])
        tw_entnahmeort_dd, tw_bemerkung_dd = combo("Entnahmeort", aktuelle_daten.get("tw_entnahmeort"), ort_opts), combo("TW Bemerkung", aktuelle_daten.get("tw_bemerkung_2", ""), ["", "Keine Besonderheiten"])
        cb_pn, cb_zwei, cb_sensor, cb_knie = cb("PN-Hahn", aktuelle_daten.get("tw_cb_pn", False)), cb("Zweigriff", aktuelle_daten.get("tw_cb_zwei", False)), cb("Sensor", aktuelle_daten.get("tw_cb_sensor", False)), cb("Knie", aktuelle_daten.get("tw_cb_knie", False))
        cb_ein, cb_ein_g, cb_eck = cb("Einhebel", aktuelle_daten.get("tw_cb_ein", False)), cb("Eingriff", aktuelle_daten.get("tw_cb_ein_g", False)), cb("Eckventil", aktuelle_daten.get("tw_cb_eck", False))
        cb_auff_ja, cb_auff_nein, cb_auff_perl = cb("ja", aktuelle_daten.get("tw_auff_ja", False)), cb("nein", aktuelle_daten.get("tw_auff_nein", False)), cb("Perlator nicht entfernbar", aktuelle_daten.get("tw_auff_perlator", False))
        cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf = cb("Starke Verkalkung", aktuelle_daten.get("tw_auff_kalk", False)), cb("Armatur mit Verbrühschutz", aktuelle_daten.get("tw_auff_verbrueh", False)), cb("Durchlauferhitzer", aktuelle_daten.get("tw_auff_durchlauf", False))
        cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich = cb("Unterbauspeicher", aktuelle_daten.get("tw_auff_unterbau", False)), cb("Eckventil warm/kalt geschlossen", aktuelle_daten.get("tw_auff_eckventil", False)), cb("nicht möglich", aktuelle_daten.get("tw_auff_unmoeglich", False))
        cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst = cb("Entnahme Dusche", aktuelle_daten.get("tw_auff_dusche", False)), cb("Handbrause", aktuelle_daten.get("tw_auff_handbrause", False)), cb("Sonstiges", aktuelle_daten.get("tw_auff_sonstiges", False))
        tw_auff_sonstiges_in, tw_inhalt_in = tf("Auffälligkeiten (Sonstiges)", aktuelle_daten.get("tw_auff_sonst_text", "")), tf("Inhalt", aktuelle_daten.get("tw_inhalt", ""))

        se_kalt_cb = cb("Scherbeneis Eigenkontrolle", aktuelle_daten.get("se_kalt", False), bold=True)
        se_zeit_in, se_zapf_dd = tf("Probenahmezeit", aktuelle_daten.get("se_zeit", "")), combo("Zapfstelle (Eis)", aktuelle_daten.get("se_zapf"), ["Eismaschine"])
        se_cb_eiswanne, se_cb_fallprobe = cb("Eiswanne/Schöpfprobe", aktuelle_daten.get("se_cb_eiswanne", False)), cb("Fallprobe", aktuelle_daten.get("se_cb_fallprobe", True))
        se_tech_sonst_in, se_desinf_dd = tf("Sonstiges (Technik)", aktuelle_daten.get("se_tech_sonst", "")), combo("Art der Desinfektion", aktuelle_daten.get("se_desinf"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
        se_cb_ozon, se_auff_sonst_in = cb("Ozonsterilisator", aktuelle_daten.get("se_cb_ozon", False)), tf("Sonstiges (Auffälligkeiten)", aktuelle_daten.get("se_auff_sonst", ""))
        se_inhalt_in, se_verpackung_dd = tf("Inhalt", aktuelle_daten.get("se_inhalt", "")), combo("Verpackung", aktuelle_daten.get("se_verpackung"), ["steriler Probenbeutel"])
        se_entnahmeort_dd, se_temp_in = combo("Entnahmeort", aktuelle_daten.get("se_entnahmeort"), ["Fischabteilung-Eismaschine", "Metzgerei", "Produktionsraum"]), tf("Probenahmetemperatur", aktuelle_daten.get("se_temp", ""))
        se_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("se_bemerkung", ""), ["", "Keine Besonderheiten"])

        se_okz_cb = cb("Abklatschproben Scherbeneis", aktuelle_daten.get("se_abklatsch_cb", False), bold=True)
        se_okz_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("se_abklatsch_bemerkung", ""), ["", "Keine Besonderheiten"])
        se_okz_opts = ["", "Eiswanne innen rechts", "Eiswanne innen links", "Auswurfrohr", "Eisschaufel", "Eiswanne", "Eismaschine innen", "Klappe/Deckel", "Sonstiges"]
        se_okz_def = {1: "Eiswanne innen rechts", 2: "Eiswanne innen links", 3: "Auswurfrohr"}
        se_okz_controls = {}
        for i in range(1, 4):
            idx = f"{i:02d}"
            se_okz_controls[idx] = {"status": combo("Status", aktuelle_daten.get(f"0003_status_{idx}"), ["R+D", "R", "P", "-"], 100), "objekt": combo("Objekt", aktuelle_daten.get(f"0003_objekt_{idx}") or se_okz_def[i], se_okz_opts, 200), "ort": combo("Probenahmeort", aktuelle_daten.get(f"0003_ort_{idx}", ""), ["Fischabteilung", "Metzgerei", "Produktionsbereich", "Kühlraum"]), "abklatsch": cb("Abklatsch", aktuelle_daten.get(f"0003_abklatsch_{idx}", True)), "tupfer": cb("Tupfer", aktuelle_daten.get(f"0003_tupfer_{idx}", True))}

        hfm_hack_cb = cb("Hackfleisch gemischt", aktuelle_daten.get("hfm_hack_cb", False), bold=True)
        hfm_hack_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_hack_entnahmeort"), ort_opts)
        t, m, j = get_herst("hfm_hack_herstelldatum")
        hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        t, m, j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_schwein", ""))
        hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_s_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        t, m, j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_rind", ""))
        hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, hfm_hack_mhd_r_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        hfm_hack_inhalt_in = tf("Inhalt", aktuelle_daten.get("hfm_hack_inhalt", ""))
        hfm_hack_verpackung_dd = combo("Verpackung", aktuelle_daten.get("hfm_hack_verpackung"), verp_opts)
        hfm_hack_lief_schwein_in, hfm_hack_lief_rind_in = tf("Lieferant (Schwein)", aktuelle_daten.get("hfm_hack_lief_schwein", "")), tf("Lieferant (Rind)", aktuelle_daten.get("hfm_hack_lief_rind", ""))
        hfm_hack_charge_schwein_dd, hfm_hack_charge_rind_dd = combo("Charge Schwein", aktuelle_daten.get("hfm_hack_charge_schwein", ""), c_opts_s), combo("Charge Rind", aktuelle_daten.get("hfm_hack_charge_rind", ""), c_opts_r)
        hfm_hack_temp_in, hfm_hack_bemerkung_dd = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_hack_temp", "")), combo("Bemerkungen", aktuelle_daten.get("hfm_hack_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_mett_cb = cb("Gewürztes Schweinemett", aktuelle_daten.get("hfm_mett_cb", False), bold=True)
        hfm_mett_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_mett_entnahmeort"), ort_opts)
        t, m, j = get_herst("hfm_mett_herstelldatum")
        hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        t, m, j = parse_datum(aktuelle_daten.get("hfm_mett_mhd", ""))
        hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, hfm_mett_mhd_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        hfm_mett_inhalt_in, hfm_mett_verpackung_dd = tf("Inhalt", aktuelle_daten.get("hfm_mett_inhalt", "")), combo("Verpackung", aktuelle_daten.get("hfm_mett_verpackung"), verp_opts)
        hfm_mett_lief_in, hfm_mett_charge_dd = tf("Lieferant Rohware", aktuelle_daten.get("hfm_mett_lief", "")), combo("Charge Rohware", aktuelle_daten.get("hfm_mett_charge", ""), c_opts_s)
        hfm_mett_temp_in, hfm_mett_bemerkung_dd = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_mett_temp", "")), combo("Bemerkungen", aktuelle_daten.get("hfm_mett_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_fzs_cb = cb("Fleischzubereitung Schwein", aktuelle_daten.get("hfm_fzs_cb", False), bold=True)
        hfm_fzs_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_fzs_entnahmeort"), ort_opts)
        hfm_fzs_produkt_in, hfm_fzs_marinade_in = tf("Produkt", aktuelle_daten.get("hfm_fzs_produkt", "")), tf("Marinade", aktuelle_daten.get("hfm_fzs_marinade", ""))
        t, m, j = get_herst("hfm_fzs_herstelldatum")
        hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_herst_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        t, m, j = parse_datum(aktuelle_daten.get("hfm_fzs_mhd", ""))
        hfm_fzs_mhd_tag_dd, hfm_fzs_mhd_mon_dd, hfm_fzs_mhd_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        hfm_fzs_inhalt_in, hfm_fzs_verpackung_dd = tf("Inhalt", aktuelle_daten.get("hfm_fzs_inhalt", "")), combo("Verpackung", aktuelle_daten.get("hfm_fzs_verpackung"), verp_opts)
        hfm_fzs_lief_in, hfm_fzs_charge_dd = tf("Lieferant Rohware", aktuelle_daten.get("hfm_fzs_lief", "")), combo("Charge Rohware", aktuelle_daten.get("hfm_fzs_charge", ""), c_opts_s)
        hfm_fzs_temp_in, hfm_fzs_bemerkung_dd = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_fzs_temp", "")), combo("Bemerkungen", aktuelle_daten.get("hfm_fzs_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_fzg_cb = cb("Fleischzubereitung Geflügel", aktuelle_daten.get("hfm_fzg_cb", False), bold=True)
        hfm_fzg_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_fzg_entnahmeort"), ort_opts)
        hfm_fzg_produkt_in, hfm_fzg_marinade_in = tf("Produkt", aktuelle_daten.get("hfm_fzg_produkt", "")), tf("Marinade", aktuelle_daten.get("hfm_fzg_marinade", ""))
        t, m, j = get_herst("hfm_fzg_herstelldatum")
        hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_herst_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        t, m, j = parse_datum(aktuelle_daten.get("hfm_fzg_mhd", ""))
        hfm_fzg_mhd_tag_dd, hfm_fzg_mhd_mon_dd, hfm_fzg_mhd_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        hfm_fzg_inhalt_in, hfm_fzg_verpackung_dd = tf("Inhalt", aktuelle_daten.get("hfm_fzg_inhalt", "")), combo("Verpackung", aktuelle_daten.get("hfm_fzg_verpackung"), verp_opts)
        hfm_fzg_lief_in, hfm_fzg_charge_dd = tf("Lieferant Rohware", aktuelle_daten.get("hfm_fzg_lief", "")), combo("Charge Rohware", aktuelle_daten.get("hfm_fzg_charge", ""), c_opts_g)
        hfm_fzg_temp_in, hfm_fzg_bemerkung_dd = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_fzg_temp", "")), combo("Bemerkungen", aktuelle_daten.get("hfm_fzg_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_bio_cb = cb("Bio-Hackfleisch", aktuelle_daten.get("hfm_bio_cb", False), bold=True)
        hfm_bio_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_bio_entnahmeort"), ort_opts)
        t, m, j = get_herst("hfm_bio_herstelldatum")
        hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_herst_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        t, m, j = parse_datum(aktuelle_daten.get("hfm_bio_mhd_schwein", ""))
        hfm_bio_mhd_s_tag_dd, hfm_bio_mhd_s_mon_dd, hfm_bio_mhd_s_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        t, m, j = parse_datum(aktuelle_daten.get("hfm_bio_mhd_rind", ""))
        hfm_bio_mhd_r_tag_dd, hfm_bio_mhd_r_mon_dd, hfm_bio_mhd_r_jahr_dd = combo("Tag", t, tage_opts, 90), combo("Mon", m, mon_opts, 90), combo("Jahr", j, jahr_opts, 120)
        hfm_bio_inhalt_in, hfm_bio_verpackung_dd = tf("Inhalt", aktuelle_daten.get("hfm_bio_inhalt", "")), combo("Verpackung", aktuelle_daten.get("hfm_bio_verpackung"), verp_opts)
        hfm_bio_lief_schwein_in, hfm_bio_lief_rind_in = tf("Lieferant (Schwein)", aktuelle_daten.get("hfm_bio_lief_schwein", "")), tf("Lieferant (Rind)", aktuelle_daten.get("hfm_bio_lief_rind", ""))
        hfm_bio_charge_schwein_dd, hfm_bio_charge_rind_dd = combo("Charge Schwein", aktuelle_daten.get("hfm_bio_charge_schwein", ""), c_opts_s), combo("Charge Rind", aktuelle_daten.get("hfm_bio_charge_rind", ""), c_opts_r)
        hfm_bio_temp_in, hfm_bio_bemerkung_dd = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_bio_temp", "")), combo("Bemerkungen", aktuelle_daten.get("hfm_bio_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_okz_cb = cb("Abklatschproben HFM", aktuelle_daten.get("hfm_abklatsch_cb", False), bold=True)
        hfm_okz_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("hfm_abklatsch_bemerkung", ""), ["", "Keine Besonderheiten"])
        okz_obj_opts = ["", "Fleischwolf-Auflage", "Fleischwolf-Lochscheibe", "Fleischwolf-Auswurf", "Fleischwolf-Spirale", "Wand am Fleischwolf", "Hackstecher", "Schaufel", "Thekenschale", "Messer", "Schneidebrett", "Auflage Knochensäge", "Tisch", "Flesichwanne", "Kühlhausgriff", "Schüssel", "Seifenspender"]
        okz_def = {1: {"o": "Fleischwolf-Auflage", "a": True, "t": False}, 2: {"o": "Fleischwolf-Auswurf", "a": True, "t": True}, 3: {"o": "Thekenschale", "a": True, "t": False}, 4: {"o": "Hackstecher", "a": True, "t": True}, 5: {"o": "Messer", "a": True, "t": False}, 6: {"o": "Schneidebrett", "a": True, "t": False}, 7: {"o": "Wand am Fleischwolf", "a": True, "t": True}, 8: {"o": "", "a": False, "t": False}, 9: {"o": "", "a": False, "t": False}, 10: {"o": "", "a": False, "t": False}}
        okz_controls = {}
        for i in range(1, 11):
            idx = f"{i:02d}"
            okz_controls[idx] = {"status": combo("Status", aktuelle_daten.get(f"0010_status_{idx}"), ["R+D", "R", "P", "-"], 100), "objekt": combo("Objekt", aktuelle_daten.get(f"0010_objekt_{idx}") or okz_def[i]["o"], okz_obj_opts, 200), "ort": combo("Probenahmeort", aktuelle_daten.get(f"0010_ort_{idx}", ""), ["Kühlraum", "Produktionsbereich", "Theke"]), "abklatsch": cb("Abklatsch", aktuelle_daten.get(f"0010_abklatsch_{idx}", okz_def[i]["a"])), "tupfer": cb("Tupfer", aktuelle_daten.get(f"0010_tupfer_{idx}", okz_def[i]["t"]))}

        # --- 5. CONVENIENCE / PROBEN ---
        og_cb = cb("Obst-/Gemüse Convenience", aktuelle_daten.get("og_cb", False), bold=True)
        og_controls = {}
        for i in range(1, 6):
            idx = f"{i:02d}"
            ht, hm, hj = parse_datum(aktuelle_daten.get(f"og_herst_{idx}", ""))
            vt, vm, vj = parse_datum(aktuelle_daten.get(f"og_verb_{idx}", ""))
            og_controls[i] = {
                "name": tf(f"Name Teilprobe {i}", aktuelle_daten.get(f"og_name_{idx}", "")),
                "ort": combo("Entnahmeort", aktuelle_daten.get(f"og_ort_{idx}", ""), ["Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Kühlraum", "SB-Theke", "Salatbar", "Saftpresse"]),
                "h_t": combo("Tag", ht, tage_opts, 90), "h_m": combo("Mon", hm, mon_opts, 90), "h_j": combo("Jahr", hj, jahr_opts, 120),
                "v_t": combo("Tag", vt, tage_opts, 90), "v_m": combo("Mon", vm, mon_opts, 90), "v_j": combo("Jahr", vj, jahr_opts, 120),
                "inhalt": tf("Inhalt", aktuelle_daten.get(f"og_inhalt_{idx}", ""), "Grammzahl", ob=format_gramm),
                "verpackung": combo("Verpackung", aktuelle_daten.get(f"og_verp_{idx}", ""), verp_opts),
                "temp": tf("Probenahmetemperatur", aktuelle_daten.get(f"og_temp_{idx}", ""), ob=format_temp)
            }

        og_okz_cb = cb("Abklatschproben Convenience", aktuelle_daten.get("og_abklatsch_cb", False), bold=True)
        og_okz_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("og_abklatsch_bemerkung_1", ""), ["", "Keine Besonderheiten"])
        og_okz_anmerkung_in = tf("Anmerkung", aktuelle_daten.get("og_abklatsch_bemerkung_2", ""))
        
        og_okz_opts = ["", "Schneidebrett", "Messer", "Saftpresse Auffanggitter", "Saftpresse Rückwand", "Saftpresse Auslass", "Waagenauflage", "Schüssel", "Löffel", "GN-Behälter"]
        og_okz_def = {1: {"o": "Schneidebrett", "a": True, "t": True}, 2: {"o": "Messer", "a": True, "t": True}, 3: {"o": "Waagenauflage", "a": True, "t": False}, 4: {"o": "Schüssel", "a": True, "t": False}, 5: {"o": "Löffel", "a": True, "t": False}}
        og_okz_controls = {}
        for i in range(1, 6):
            idx = f"{i:02d}"
            og_okz_controls[idx] = {"status": combo("Status", aktuelle_daten.get(f"0011_status_{idx}"), ["R+D", "R", "P", "-"], 100), "objekt": combo("Objekt", aktuelle_daten.get(f"0011_objekt_{idx}") or og_okz_def[i]["o"], og_okz_opts, 200), "ort": combo("Probenahmeort", aktuelle_daten.get(f"0011_ort_{idx}", ""), ["Kühlraum", "Produktionsbereich", "Theke"]), "abklatsch": cb("Abklatsch", aktuelle_daten.get(f"0011_abklatsch_{idx}", og_okz_def[i]["a"])), "tupfer": cb("Tupfer", aktuelle_daten.get(f"0011_tupfer_{idx}", og_okz_def[i]["t"]))}

        # ==========================================
        # VORLAGEN LOGIK (AUFKLAPPBAR)
        # ==========================================
        alle_vorlagen = lade_vorlagen_lokal()
        vorlagen_status = ft.Text("", weight="bold", size=12) 
        vl_dd = ft.Dropdown(options=[ft.dropdown.Option(k) for k in alle_vorlagen.keys()], hint_text="Vorlage wählen...", dense=True, content_padding=10, color="yellow", text_style=ft.TextStyle(color="yellow", size=12), border_color="white", width=200)
        vl_name_in = tf("Als neue Vorlage speichern", "", w=200)

        def lade_v(e):
            if not vl_dd.value: return
            v = alle_vorlagen.get(vl_dd.value, {})
            if "name_in" in v: name_in.value = v["name_in"]
            if "ag_dd" in v: ag_dd.value = v["ag_dd"]
            if "typ_dd" in v: typ_dd.value = v["typ_dd"]
            vorlagen_status.value = f"✅ '{vl_dd.value}' geladen!"; vorlagen_status.color = "green"; page.update()
            
        def del_v(e):
            if vl_dd.value in alle_vorlagen:
                del alle_vorlagen[vl_dd.value]; speichere_vorlagen_lokal(alle_vorlagen)
                vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                vorlagen_status.value = f"🗑️ Gelöscht!"; vorlagen_status.color = "red"; vl_dd.value = None; page.update()
                
        def save_v(e):
            if not (vl_name_in.value or "").strip(): return
            alle_vorlagen[vl_name_in.value] = {"name_in": name_in.value, "ag_dd": ag_dd.value, "typ_dd": typ_dd.value}
            speichere_vorlagen_lokal(alle_vorlagen)
            vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
            vorlagen_status.value = f"✅ Vorlage gespeichert!"; vorlagen_status.color = "orange"; vl_name_in.value = ""; page.update()

        vorlagen_expansion = ft.ExpansionTile(
            title=ft.Text("📋 Vorlage", weight="bold", color="white"),
            collapsed_text_color="white",
            text_color="#4CAF50",
            controls=[
                ft.Container(
                    bgcolor="#002b00", padding=15, border_radius=10,
                    content=ft.Column([
                        vorlagen_status,
                        ft.Row([vl_dd, emoji_btn("📥", lade_v, "#2196F3"), emoji_btn("🗑️", del_v, "#F44336")]),
                        ft.Row([vl_name_in, emoji_btn("💾", save_v, "#FF9800")])
                    ])
                )
            ]
        )

        # ==========================================
        # ZUSAMMENBAU DES HAUPT-LAYOUTS
        # ==========================================
        top_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        haupt_bereich = ft.Column(spacing=15)
        
        def switch_tab(tab_id):
            haupt_bereich.controls.clear(); top_nav.controls.clear()
            # FIX: Oben heißt es Convenience
            tabs = [("stamm", "Stammdaten"), ("tw", "Trinkwasser"), ("se", "Scherbeneis"), ("hfm", "HFM"), ("og", "Convenience")]
            for tid, tname in tabs:
                is_act = (tid == tab_id)
                btn = ft.ElevatedButton(tname, on_click=lambda e, t=tid: switch_tab(t), bgcolor="#004400" if is_act else "#1a1a1a", color="white",
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=12, side=ft.BorderSide(width=1.5, color="#4CAF50")))
                top_nav.controls.append(btn)
            
            if tab_id == "stamm": haupt_bereich.controls.extend([vorlagen_expansion, ft.Divider(color="white24"), ft.Text("Stammdaten", size=20, weight="bold"), datum_row, adr_in, nr_in, auft_in, ag_dd, name_in, typ_dd, bem_in])
            elif tab_id == "tw": haupt_bereich.controls.extend([ft.Text("Trinkwasser-Check", size=24, weight="bold", color="white"), tw_kalt_cb, tw_zeit_in, tw_temp_in, tw_tempkonst_in, ft.Divider(color="white24"), ft.Text("Probenahme / Zapfstelle:", color="white", weight="bold"), tw_entnahmeort_dd, tw_zapf_dd, tw_zapf_sonst_dd, tw_desinf_dd, ft.Row([cb_pn, cb_zwei, cb_sensor, cb_knie], wrap=True), ft.Row([cb_ein, cb_ein_g, cb_eck], wrap=True), ft.Divider(color="white24"), ft.Text("Sensorik & Analytik:", color="white", weight="bold"), tw_inaktiv_dd, tw_kurz1_dd, tw_kurz2_dd, tw_kurz3_dd, tw_kurz4_dd, ft.Divider(color="white24"), ft.Text("Auffälligkeiten:", color="white", weight="bold"), ft.Row([cb_auff_ja, cb_auff_nein], wrap=True), cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf, cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich, cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst, tw_auff_sonstiges_in, ft.Divider(color="white24"), tw_zweck_dd, tw_inhalt_in, tw_verpackung_dd, tw_bemerkung_dd])
            elif tab_id == "se":
                sub_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
                haupt_bereich.controls.extend([ft.Text("Scherbeneis", size=24, weight="bold", color="white"), sub_nav])
                def sw_se(sub):
                    haupt_bereich.controls[2:] = []
                    sub_nav.controls.clear()
                    for sid, sname in [("eis", "❄️ Eis"), ("okz", "🔬 OKZ")]:
                        is_active = (sid == sub)
                        btn = ft.ElevatedButton(sname, on_click=lambda e, s=sid: sw_se(s), bgcolor="#004400" if is_active else "#1a1a1a", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=12, side=ft.BorderSide(width=1.5, color="#4CAF50")))
                        sub_nav.controls.append(btn)
                    if sub == "eis": haupt_bereich.controls.extend([se_kalt_cb, se_zeit_in, se_zapf_dd, ft.Text("Technik:", color="white", weight="bold"), ft.Row([se_cb_eiswanne, se_cb_fallprobe], wrap=True), se_tech_sonst_in, se_desinf_dd, ft.Text("Auffälligkeiten:", color="white", weight="bold"), se_cb_ozon, se_auff_sonst_in, se_inhalt_in, se_verpackung_dd, se_entnahmeort_dd, se_temp_in, se_bemerkung_dd])
                    elif sub == "okz":
                        haupt_bereich.controls.extend([ft.Text("⚠️ Haken prüfen!", color="orange", weight="bold"), se_okz_cb, ft.Divider(color="white24")])
                        for i in range(1, 4):
                            c = se_okz_controls[f"{i:02d}"]
                            haupt_bereich.controls.extend([ft.Text(f"Probe {i}", color="yellow", weight="bold"), ft.Row([c["status"], c["objekt"]], wrap=True), c["ort"], ft.Row([c["abklatsch"], c["tupfer"]], wrap=True), ft.Divider(color="white24")])
                        haupt_bereich.controls.append(se_okz_bemerkung_dd)
                    page.update()
                sw_se("eis")
            elif tab_id == "hfm":
                sub_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
                haupt_bereich.controls.extend([ft.Text("HFM Fleisch", size=20, weight="bold", color="white"), sub_nav])
                def sw_hfm(sub):
                    haupt_bereich.controls[2:] = []
                    sub_nav.controls.clear()
                    for sid, sname in [("hack","🥩 Hack"), ("mett","🍖 Mett"), ("fzs","🐷 FZS"), ("fzg","🐔 FZG"), ("bio","🥩 Bio"), ("okz","🔬 OKZ")]:
                        is_sub_act = (sid == sub)
                        btn = ft.ElevatedButton(sname, on_click=lambda e, s=sid: sw_hfm(s), bgcolor="#004400" if is_sub_act else "#1a1a1a", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=5, side=ft.BorderSide(width=1, color="#4CAF50")))
                        sub_nav.controls.append(btn)
                    if sub == "hack": haupt_bereich.controls.extend([hfm_hack_cb, hfm_hack_entnahmeort_dd, ft.Text("Herstellungsdatum:", color="white"), ft.Row([hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd], wrap=True), hfm_hack_inhalt_in, hfm_hack_verpackung_dd, hfm_hack_lief_schwein_in, hfm_hack_lief_rind_in, ft.Text("MHD (Schwein):", color="yellow"), ft.Row([hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_s_jahr_dd], wrap=True), ft.Text("MHD (Rind):", color="yellow"), ft.Row([hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, hfm_hack_mhd_r_jahr_dd], wrap=True), hfm_hack_charge_schwein_dd, hfm_hack_charge_rind_dd, hfm_hack_temp_in, hfm_hack_bemerkung_dd])
                    elif sub == "mett": haupt_bereich.controls.extend([hfm_mett_cb, hfm_mett_entnahmeort_dd, ft.Text("Herstellungsdatum:", color="white"), ft.Row([hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd], wrap=True), hfm_mett_inhalt_in, hfm_mett_verpackung_dd, hfm_mett_lief_in, ft.Text("MHD:", color="white"), ft.Row([hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, hfm_mett_mhd_jahr_dd], wrap=True), hfm_mett_charge_dd, hfm_mett_temp_in, hfm_mett_bemerkung_dd])
                    elif sub == "fzs": haupt_bereich.controls.extend([hfm_fzs_cb, hfm_fzs_entnahmeort_dd, hfm_fzs_produkt_in, hfm_fzs_marinade_in, ft.Text("Herstellungsdatum:", color="white"), ft.Row([hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_herst_jahr_dd], wrap=True), hfm_fzs_inhalt_in, hfm_fzs_verpackung_dd, hfm_fzs_lief_in, ft.Text("MHD:", color="white"), ft.Row([hfm_fzs_mhd_tag_dd, hfm_fzs_mhd_mon_dd, hfm_fzs_mhd_jahr_dd], wrap=True), hfm_fzs_charge_dd, hfm_fzs_temp_in, hfm_fzs_bemerkung_dd])
                    elif sub == "fzg": haupt_bereich.controls.extend([hfm_fzg_cb, hfm_fzg_entnahmeort_dd, hfm_fzg_produkt_in, hfm_fzg_marinade_in, ft.Text("Herstellungsdatum:", color="white"), ft.Row([hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_herst_jahr_dd], wrap=True), hfm_fzg_inhalt_in, hfm_fzg_verpackung_dd, hfm_fzg_lief_in, ft.Text("MHD:", color="white"), ft.Row([hfm_fzg_mhd_tag_dd, hfm_fzg_mhd_mon_dd, hfm_fzg_mhd_jahr_dd], wrap=True), hfm_fzg_charge_dd, hfm_fzg_temp_in, hfm_fzg_bemerkung_dd])
                    elif sub == "bio": haupt_bereich.controls.extend([hfm_bio_cb, hfm_bio_entnahmeort_dd, ft.Text("Herstellungsdatum:", color="white"), ft.Row([hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_herst_jahr_dd], wrap=True), hfm_bio_inhalt_in, hfm_bio_verpackung_dd, hfm_bio_lief_schwein_in, hfm_bio_lief_rind_in, ft.Text("MHD (Schwein):", color="yellow"), ft.Row([hfm_bio_mhd_s_tag_dd, hfm_bio_mhd_s_mon_dd, hfm_bio_mhd_s_jahr_dd], wrap=True), ft.Text("MHD (Rind):", color="yellow"), ft.Row([hfm_bio_mhd_r_tag_dd, hfm_bio_mhd_r_mon_dd, hfm_bio_mhd_r_jahr_dd], wrap=True), hfm_bio_charge_schwein_dd, hfm_bio_charge_rind_dd, hfm_bio_temp_in, hfm_bio_bemerkung_dd])
                    elif sub == "okz":
                        haupt_bereich.controls.extend([ft.Text("⚠️ Haken prüfen!", color="orange", weight="bold"), hfm_okz_cb, ft.Divider(color="white24")])
                        for i in range(1, 11):
                            c = okz_controls[f"{i:02d}"]
                            haupt_bereich.controls.extend([ft.Text(f"Probe {i}", color="yellow", weight="bold"), ft.Row([c["status"], c["objekt"]], wrap=True), c["ort"], ft.Row([c["abklatsch"], c["tupfer"]], wrap=True), ft.Divider(color="white24")])
                        haupt_bereich.controls.append(hfm_okz_bemerkung_dd)
                    page.update()
                sw_hfm("hack")
            elif tab_id == "og":
                sub_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
                haupt_bereich.controls.extend([ft.Text("Proben", size=24, weight="bold", color="white"), sub_nav])
                def sw_og(sub):
                    haupt_bereich.controls[2:] = []
                    sub_nav.controls.clear()
                    # FIX: Unten heißt es "🥗 Proben"
                    for sid, sname in [("teil", "🥗 Proben"), ("okz", "🔬 OKZ")]:
                        is_sub_act = (sid == sub)
                        btn = ft.ElevatedButton(sname, on_click=lambda e, s=sid: sw_og(s), bgcolor="#004400" if is_sub_act else "#1a1a1a", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=8, side=ft.BorderSide(width=1.5, color="#4CAF50")))
                        sub_nav.controls.append(btn)
                    if sub == "teil":
                        haupt_bereich.controls.extend([og_cb, ft.Divider(color="white24")])
                        for i in range(1, 6):
                            c = og_controls[i]
                            haupt_bereich.controls.extend([ft.Text(f"Teilprobe {i}", color="yellow", weight="bold"), c["name"], c["ort"], ft.Text("Herstellungsdatum:", color="white"), ft.Row([c["h_t"], c["h_m"], c["h_j"]], wrap=True), ft.Text("Verbrauchsdatum:", color="white"), ft.Row([c["v_t"], c["v_m"], c["v_j"]], wrap=True), c["inhalt"], c["verpackung"], c["temp"], ft.Divider(color="white24")])
                    elif sub == "okz":
                        haupt_bereich.controls.extend([ft.Text("⚠️ Haken prüfen!", color="orange", weight="bold"), og_okz_cb, ft.Divider(color="white24")])
                        for i in range(1, 6):
                            c = og_okz_controls[f"{i:02d}"]
                            if i == 2: haupt_bereich.controls.append(ft.Text("💡 Info: Bei Saftpresse bitte hier auswählen.", color="white54", italic=True, size=12))
                            haupt_bereich.controls.extend([ft.Text(f"Probe {i}", color="yellow", weight="bold"), ft.Row([c["status"], c["objekt"]], wrap=True), c["ort"], ft.Row([c["abklatsch"], c["tupfer"]], wrap=True), ft.Divider(color="white24")])
                        haupt_bereich.controls.extend([ft.Text("💡 Wichtig: Wird die Saftpresse beprobt, muss zwingend auch das Messer aufgenommen werden!", color="orange", weight="bold"), og_okz_bemerkung_dd, og_okz_anmerkung_in])
                    page.update()
                sw_og("teil")
            page.update()

        def hole_aktuelle_daten():
            def get_val(ctrl, default_val):
                if ctrl is None or ctrl.value is None or str(ctrl.value).strip() == "": return str(default_val)
                return str(ctrl.value)

            d = {
                "datum": get_date_str(tag_dd.value, mon_dd.value, jahr_dd.value), 
                "adresse": adr_in.value, 
                "marktnummer": nr_in.value, 
                "auftragsnummer": auft_in.value, 
                "mitarbeiter_name": name_in.value, 
                "auftraggeber": get_val(ag_dd, "03509 - REWE Hackfleischmonitoring"), 
                "typ_probenahme": get_val(typ_dd, "Standard"), 
                "bemerkung": bem_in.value,
                
                "tw_kalt": bool(tw_kalt_cb.value), 
                "tw_lims_override": bool(lims_override_cb.value), 
                "tw_zeit": tw_zeit_in.value, 
                "tw_temp": tw_temp_in.value, 
                "tw_desinf": get_val(tw_desinf_dd, "Abflammen"), 
                "tw_zapf": get_val(tw_zapf_dd, "Spülbecken"), 
                "tw_cb_pn": bool(cb_pn.value), 
                "tw_cb_zwei": bool(cb_zwei.value), 
                "tw_cb_sensor": bool(cb_sensor.value), 
                "tw_cb_knie": bool(cb_knie.value), 
                "tw_cb_ein": bool(cb_ein.value), 
                "tw_cb_ein_g": bool(cb_ein_g.value), 
                "tw_cb_eck": bool(cb_eck.value), 
                "tw_zapf_sonst": get_val(tw_zapf_sonst_dd, ""), 
                "tw_inaktiv": get_val(tw_inaktiv_dd, "Na-Thiosulfat"), 
                "tw_kurz1": get_val(tw_kurz1_dd, "1 - nicht wahrnehmbar"), 
                "tw_kurz2": get_val(tw_kurz2_dd, "1 - nicht wahrnehmbar"), 
                "tw_kurz3": get_val(tw_kurz3_dd, "1 - nicht wahrnehmbar"), 
                "tw_kurz4": get_val(tw_kurz4_dd, "1 - nicht wahrnehmbar"), 
                "tw_auff_ja": bool(cb_auff_ja.value), 
                "tw_auff_nein": bool(cb_auff_nein.value), 
                "tw_auff_perlator": bool(cb_auff_perl.value), 
                "tw_auff_kalk": bool(cb_auff_verkalk.value), 
                "tw_auff_verbrueh": bool(cb_auff_verbrueh.value), 
                "tw_auff_durchlauf": bool(cb_auff_durchlauf.value), 
                "tw_auff_eckventil": bool(cb_auff_eck_zu.value), 
                "tw_auff_unterbau": bool(cb_auff_unterbau.value), 
                "tw_auff_unmoeglich": bool(cb_auff_nichtmoeglich.value), 
                "tw_auff_dusche": bool(cb_auff_dusche.value), 
                "tw_auff_handbrause": bool(cb_auff_handbrause.value), 
                "tw_auff_sonstiges": bool(cb_auff_sonst.value), 
                "tw_auff_sonst_text": tw_auff_sonstiges_in.value, 
                "tw_zweck": get_val(tw_zweck_dd, "Zweck B"), 
                "tw_inhalt": get_val(tw_inhalt_in, "ca. 500 ml"), 
                "tw_verpackung": get_val(tw_verpackung_dd, "500ml Kunststoff-Flasche mit Natriumthiosulfat"), 
                "tw_entnahmeort": get_val(tw_entnahmeort_dd, "Metzgerei"), 
                "tw_tempkonst": tw_tempkonst_in.value, 
                "tw_bemerkung_2": tw_bemerkung_dd.value,
                
                "se_kalt": bool(se_kalt_cb.value), 
                "se_zeit": se_zeit_in.value, 
                "se_zapf": get_val(se_zapf_dd, "Eismaschine"), 
                "se_cb_eiswanne": bool(se_cb_eiswanne.value), 
                "se_cb_fallprobe": bool(se_cb_fallprobe.value), 
                "se_tech_sonst": se_tech_sonst_in.value, 
                "se_desinf": get_val(se_desinf_dd, "ohne Desinfektion"), 
                "se_cb_ozon": bool(se_cb_ozon.value), 
                "se_auff_sonst": se_auff_sonst_in.value, 
                "se_inhalt": get_val(se_inhalt_in, "ca. 1000ml"), 
                "se_verpackung": get_val(se_verpackung_dd, "steriler Probenbeutel"), 
                "se_entnahmeort": get_val(se_entnahmeort_dd, "Fischabteilung-Eismaschine"), 
                "se_temp": se_temp_in.value, 
                "se_bemerkung": se_bemerkung_dd.value, 
                "se_abklatsch_cb": bool(se_okz_cb.value), 
                "se_abklatsch_bemerkung": se_okz_bemerkung_dd.value,
                
                "hfm_hack_cb": bool(hfm_hack_cb.value), 
                "hfm_hack_entnahmeort": get_val(hfm_hack_entnahmeort_dd, "Kühlraum"), 
                "hfm_hack_herstelldatum": get_date_str(hfm_hack_herst_tag_dd.value, hfm_hack_herst_mon_dd.value, hfm_hack_herst_jahr_dd.value), 
                "hfm_hack_inhalt": get_val(hfm_hack_inhalt_in, "jeweils ca. 200 g"), 
                "hfm_hack_verpackung": get_val(hfm_hack_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_hack_lief_schwein": hfm_hack_lief_schwein_in.value, 
                "hfm_hack_lief_rind": hfm_hack_lief_rind_in.value, 
                "hfm_hack_mhd_schwein": get_date_str(hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value), 
                "hfm_hack_mhd_rind": get_date_str(hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value), 
                "hfm_hack_charge_schwein": hfm_hack_charge_schwein_dd.value, 
                "hfm_hack_charge_rind": hfm_hack_charge_rind_dd.value, 
                "hfm_hack_temp": hfm_hack_temp_in.value, 
                "hfm_hack_bemerkung": hfm_hack_bemerkung_dd.value,
                
                "hfm_mett_cb": bool(hfm_mett_cb.value), 
                "hfm_mett_entnahmeort": get_val(hfm_mett_entnahmeort_dd, "Kühlraum"), 
                "hfm_mett_herstelldatum": get_date_str(hfm_mett_herst_tag_dd.value, hfm_mett_herst_mon_dd.value, hfm_mett_herst_jahr_dd.value), 
                "hfm_mett_inhalt": get_val(hfm_mett_inhalt_in, "ca. 200 g"), 
                "hfm_mett_verpackung": get_val(hfm_mett_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_mett_lief": hfm_mett_lief_in.value, 
                "hfm_mett_mhd": get_date_str(hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value), 
                "hfm_mett_charge": hfm_mett_charge_dd.value, 
                "hfm_mett_temp": hfm_mett_temp_in.value, 
                "hfm_mett_bemerkung": hfm_mett_bemerkung_dd.value,
                
                "hfm_fzs_cb": bool(hfm_fzs_cb.value), 
                "hfm_fzs_entnahmeort": get_val(hfm_fzs_entnahmeort_dd, "Kühlraum"), 
                "hfm_fzs_produkt": hfm_fzs_produkt_in.value, 
                "hfm_fzs_marinade": hfm_fzs_marinade_in.value, 
                "hfm_fzs_herstelldatum": get_date_str(hfm_fzs_herst_tag_dd.value, hfm_fzs_herst_mon_dd.value, hfm_fzs_herst_jahr_dd.value), 
                "hfm_fzs_inhalt": get_val(hfm_fzs_inhalt_in, "ca. 200 g"), 
                "hfm_fzs_verpackung": get_val(hfm_fzs_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_fzs_lief": hfm_fzs_lief_in.value, 
                "hfm_fzs_mhd": get_date_str(hfm_fzs_mhd_tag_dd.value, hfm_fzs_mhd_mon_dd.value, hfm_fzs_mhd_jahr_dd.value), 
                "hfm_fzs_charge": hfm_fzs_charge_dd.value, 
                "hfm_fzs_temp": hfm_fzs_temp_in.value, 
                "hfm_fzs_bemerkung": hfm_fzs_bemerkung_dd.value,
                
                "hfm_fzg_cb": bool(hfm_fzg_cb.value), 
                "hfm_fzg_entnahmeort": get_val(hfm_fzg_entnahmeort_dd, "Kühlraum"), 
                "hfm_fzg_produkt": hfm_fzg_produkt_in.value, 
                "hfm_fzg_marinade": hfm_fzg_marinade_in.value, 
                "hfm_fzg_herstelldatum": get_date_str(hfm_fzg_herst_tag_dd.value, hfm_fzg_herst_mon_dd.value, hfm_fzg_herst_jahr_dd.value), 
                "hfm_fzg_inhalt": get_val(hfm_fzg_inhalt_in, "ca. 200 g"), 
                "hfm_fzg_verpackung": get_val(hfm_fzg_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_fzg_lief": hfm_fzg_lief_in.value, 
                "hfm_fzg_mhd": get_date_str(hfm_fzg_mhd_tag_dd.value, hfm_fzg_mhd_mon_dd.value, hfm_fzg_mhd_jahr_dd.value), 
                "hfm_fzg_charge": hfm_fzg_charge_dd.value, 
                "hfm_fzg_temp": hfm_fzg_temp_in.value, 
                "hfm_fzg_bemerkung": hfm_fzg_bemerkung_dd.value,
                
                "hfm_bio_cb": bool(hfm_bio_cb.value), 
                "hfm_bio_entnahmeort": get_val(hfm_bio_entnahmeort_dd, "Produktionsraum"), 
                "hfm_bio_inhalt": get_val(hfm_bio_inhalt_in, "jeweils ca. 200 g"), 
                "hfm_bio_verpackung": get_val(hfm_bio_verpackung_dd, "steriler Probenbecher"), 
                "hfm_bio_lief_schwein": hfm_bio_lief_schwein_in.value, 
                "hfm_bio_lief_rind": hfm_bio_lief_rind_in.value, 
                "hfm_bio_mhd_schwein": get_date_str(hfm_bio_mhd_s_tag_dd.value, hfm_bio_mhd_s_mon_dd.value, hfm_bio_mhd_s_jahr_dd.value), 
                "hfm_bio_mhd_rind": get_date_str(hfm_bio_mhd_r_tag_dd.value, hfm_bio_mhd_r_mon_dd.value, hfm_bio_mhd_r_jahr_dd.value), 
                "hfm_bio_charge_schwein": hfm_bio_charge_schwein_dd.value, 
                "hfm_bio_charge_rind": hfm_bio_charge_rind_dd.value, 
                "hfm_bio_temp": hfm_bio_temp_in.value, 
                "hfm_bio_bemerkung": hfm_bio_bemerkung_dd.value, 
                "hfm_abklatsch_cb": bool(hfm_okz_cb.value), 
                "hfm_abklatsch_bemerkung": hfm_okz_bemerkung_dd.value,
                
                "og_cb": bool(og_cb.value), 
                "og_abklatsch_cb": bool(og_okz_cb.value), 
                "og_abklatsch_bemerkung_1": og_okz_bemerkung_dd.value, 
                "og_abklatsch_bemerkung_2": og_okz_anmerkung_in.value,
            }

            for idx, c in se_okz_controls.items(): 
                d[f"0003_status_{idx}"] = get_val(c["status"], "R+D")
                d[f"0003_objekt_{idx}"] = get_val(c["objekt"], se_okz_def[int(idx)])
                d[f"0003_ort_{idx}"] = c["ort"].value
                d[f"0003_abklatsch_{idx}"] = bool(c["abklatsch"].value)
                d[f"0003_tupfer_{idx}"] = bool(c["tupfer"].value)

            for idx, c in okz_controls.items(): 
                d[f"0010_status_{idx}"] = get_val(c["status"], "R+D")
                d[f"0010_objekt_{idx}"] = get_val(c["objekt"], okz_def[int(idx)]["o"])
                d[f"0010_ort_{idx}"] = c["ort"].value
                d[f"0010_abklatsch_{idx}"] = bool(c["abklatsch"].value)
                d[f"0010_tupfer_{idx}"] = bool(c["tupfer"].value)

            for i in range(1, 6):
                idx = f"{i:02d}"; c = og_controls[i]
                d[f"og_name_{idx}"] = c["name"].value; d[f"og_ort_{idx}"] = c["ort"].value; d[f"og_inhalt_{idx}"] = c["inhalt"].value; d[f"og_verp_{idx}"] = c["verpackung"].value; d[f"og_temp_{idx}"] = c["temp"].value; d[f"og_herst_{idx}"] = get_date_str(c["h_t"].value, c["h_m"].value, c["h_j"].value); d[f"og_verb_{idx}"] = get_date_str(c["v_t"].value, c["v_m"].value, c["v_j"].value)
            
            for idx, c in og_okz_controls.items(): 
                d[f"0011_status_{idx}"] = get_val(c["status"], "R+D")
                d[f"0011_objekt_{idx}"] = get_val(c["objekt"], og_okz_def[int(idx)]["o"])
                d[f"0011_ort_{idx}"] = c["ort"].value
                d[f"0011_abklatsch_{idx}"] = bool(c["abklatsch"].value)
                d[f"0011_tupfer_{idx}"] = bool(c["tupfer"].value)

            return d

        def check_pflichtfelder():
            errors = []
            if not (nr_in.value or "").strip(): errors.append("- Marktnummer")
            if not (adr_in.value or "").strip(): errors.append("- Adresse")
            if not (auft_in.value or "").strip(): errors.append("- Auftragsnummer / Etikettennummer")
            if not (name_in.value or "").strip(): errors.append("- Name Probenehmer")

            if tw_kalt_cb.value:
                if not (tw_zeit_in.value or "").strip(): errors.append("- Trinkwasser: Uhrzeit")
                if not (tw_temp_in.value or "").strip(): errors.append("- Trinkwasser: Temperatur")

            if se_kalt_cb.value:
                if not (se_zeit_in.value or "").strip(): errors.append("- Scherbeneis: Uhrzeit")
                if not (se_temp_in.value or "").strip(): errors.append("- Scherbeneis: Temperatur")

            if hfm_hack_cb.value:
                if not (hfm_hack_temp_in.value or "").strip(): errors.append("- Hackfleisch: Temperatur")
                if not (hfm_hack_charge_schwein_dd.value or "").strip() and not (hfm_hack_charge_rind_dd.value or "").strip(): errors.append("- Hackfleisch: Chargennummer")
                if not (hfm_hack_mhd_s_tag_dd.value or "").strip() and not (hfm_hack_mhd_r_tag_dd.value or "").strip(): errors.append("- Hackfleisch: MHD")

            if hfm_mett_cb.value:
                if not (hfm_mett_temp_in.value or "").strip(): errors.append("- Mett: Temperatur")
                if not (hfm_mett_charge_dd.value or "").strip(): errors.append("- Mett: Chargennummer")
                if not (hfm_mett_mhd_tag_dd.value or "").strip(): errors.append("- Mett: MHD")

            if hfm_fzs_cb.value:
                if not (hfm_fzs_temp_in.value or "").strip(): errors.append("- FZ Schwein: Temperatur")
                if not (hfm_fzs_charge_dd.value or "").strip(): errors.append("- FZ Schwein: Chargennummer")
                if not (hfm_fzs_mhd_tag_dd.value or "").strip(): errors.append("- FZ Schwein: MHD")

            if hfm_fzg_cb.value:
                if not (hfm_fzg_temp_in.value or "").strip(): errors.append("- FZ Geflügel: Temperatur")
                if not (hfm_fzg_charge_dd.value or "").strip(): errors.append("- FZ Geflügel: Chargennummer")
                if not (hfm_fzg_mhd_tag_dd.value or "").strip(): errors.append("- FZ Geflügel: MHD")

            if hfm_bio_cb.value:
                if not (hfm_bio_temp_in.value or "").strip(): errors.append("- Bio Hackfleisch: Temperatur")
                if not (hfm_bio_charge_schwein_dd.value or "").strip() and not (hfm_bio_charge_rind_dd.value or "").strip(): errors.append("- Bio Hackfleisch: Chargennummer")
                if not (hfm_bio_mhd_s_tag_dd.value or "").strip() and not (hfm_bio_mhd_r_tag_dd.value or "").strip(): errors.append("- Bio Hackfleisch: MHD")
            
            return errors

        def reset_form(e):
            zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None)

        def nur_speichern(e):
            fehler_text.visible = False
            status_text.value = ""
            page.update()

            errs = check_pflichtfelder()
            if errs:
                fehler_text.value = "⚠️ BITTE FOLGENDE FELDER AUSFÜLLEN:\n" + "\n".join(errs)
                fehler_text.visible = True
                page.update()
                return

            try:
                status_text.value = "⏳ Speichere Tour..."; status_text.color = "yellow"; page.update()
                maerkte = lade_maerkte()
                d = hole_aktuelle_daten()
                tour_aktualisiert = False
                for i, tour in enumerate(maerkte):
                    if tour.get("marktnummer") == nr_in.value: maerkte[i] = d; tour_aktualisiert = True; break
                if not tour_aktualisiert: maerkte.append(d)
                speichere_maerkte(maerkte)
                status_text.value = "✅ Tour erfolgreich gespeichert!"; status_text.color = "orange"; page.update()
            except Exception as ex: 
                status_text.value = "❌ Fehler"; status_text.color = "red"; zeige_fehler(ex)
        
        def save_final(e):
            fehler_text.visible = False
            status_text.value = ""
            page.update()

            errs = check_pflichtfelder()
            if errs:
                fehler_text.value = "⚠️ BITTE FOLGENDE FELDER AUSFÜLLEN:\n" + "\n".join(errs)
                fehler_text.visible = True
                page.update()
                return

            try:
                status_text.value = "⏳ Erstelle PDF..."; status_text.color = "yellow"; page.update()
                maerkte = lade_maerkte()
                d = hole_aktuelle_daten()
                if markt_index is None: maerkte.append(d)
                else: maerkte[markt_index] = d
                speichere_maerkte(maerkte)
                try:
                    saved_path = erstelle_bericht(d)
                    fname = os.path.basename(saved_path)
                    status_text.value = f"✅ BERICHT ERSTELLT!\nDatei: {fname}"; status_text.color = "green"
                except Exception as ex:
                    status_text.value = ""; fehler_text.value = f"⚠️ SPEICHER-FEHLER: {str(ex)}"; fehler_text.visible = True
                page.update()
            except Exception as ex: 
                status_text.value = "❌ Fehler"; status_text.color = "red"; zeige_fehler(ex)

        bottom_buttons = ft.Column([
            ft.Row([
                ft.Container(content=action_btn_form("🚚 Touren", lambda e: zeige_dashboard(), "#F44336"), expand=1),
                ft.Container(content=action_btn_form("🔄 Reset", lambda e: reset_form(e), "#9C27B0"), expand=1),
            ]),
            ft.Row([
                ft.Container(content=action_btn_form("💾 Speichern", lambda e: nur_speichern(e), "#FF9800"), expand=1),
                ft.Container(content=action_btn_form("📄 Bericht", save_final, "#2196F3"), expand=1),
            ])
        ], spacing=10)

        ansicht.controls.extend([
            top_nav, ft.Divider(color="white24"), haupt_bereich, ft.Container(height=20),
            fehler_text, status_text, bottom_buttons
        ])
        
        switch_tab("stamm")
    except Exception as ex: zeige_fehler(ex)