import flet as ft
import datetime
import json
import os
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer
from pdf_generator import erstelle_bericht

def lade_vorlagen_lokal():
    try:
        if os.path.exists("tour_vorlagen.json"):
            with open("tour_vorlagen.json", "r", encoding="utf-8") as f: return json.load(f)
    except: pass
    return {}

def speichere_vorlagen_lokal(daten):
    try:
        with open("tour_vorlagen.json", "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)
    except: pass

def zeige_maske_ui(page: ft.Page, ansicht: ft.Column, nav_leiste, zeige_dashboard, zeige_fehler, markt_index):
    haupt_bereich = ft.Column(spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    top_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=5)
    
    current_tab_state = ["stamm"]
    current_sub_tab_state = [""]
    markierte_fehler_controls = [] 
    
    fehler_container = ft.Column(spacing=5, visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    status_text = ft.Text("", color="#FF9800", weight="bold", size=18, text_align=ft.TextAlign.CENTER)

    tage_opts = [""]+[f"{i:02d}" for i in range(1,32)]
    mon_opts = [""]+[f"{i:02d}" for i in range(1,13)]
    jahr_opts = [""]+[str(i) for i in range(2024,2035)]
    c_opts_s = ["", "z. Z. nicht vorrätig", "keine Eigenproduktion", "Kein Schweinehackfleisch"]
    c_opts_r = ["", "z. Z. nicht vorrätig", "keine Eigenproduktion", "Kein Rinderhackfleisch"]
    c_opts_g = ["", "z. Z. nicht vorrätig", "keine Eigenproduktion", "Kein Geflügel"]
    ort_opts = ["", "Fischabteilung", "Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke"]
    verp_opts = ["", "steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel u. etikett", "Pappschale mit Kunststofffolie umwickelt", "tiefgezogene Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie umwickelt", "SB-Kunststoffverpackung"]

    try:
        ansicht.controls.clear()
        ansicht.horizontal_alignment = ft.CrossAxisAlignment.STRETCH 
        
        maerkte = lade_maerkte()
        v, z = lade_benutzer()
        heute_str = datetime.datetime.now().strftime('%d.%m.%Y')
        aktuelle_daten = maerkte[markt_index] if (markt_index is not None and markt_index < len(maerkte)) else {"datum": heute_str, "mitarbeiter_name": f"{v} {z}".strip()}

        def tf(label, val, hint="", w=None, oc=None, ob=None, multiline=False):
            return ft.TextField(
                label=label, value=val or "", hint_text=hint, 
                multiline=multiline,
                hint_style=ft.TextStyle(color="white54", size=12), 
                color="#FF9800", text_style=ft.TextStyle(size=14, color="#FF9800"), 
                label_style=ft.TextStyle(color="white", size=14), 
                border_color="white", content_padding=15, width=w, on_change=oc, on_blur=ob
            )

        def combo(label, val, opts, w=None, oc=None, multiline=True):
            is_date = label in ["Tag", "Mon", "Jahr"]
            pad = 5 if is_date else 15
            txt_size = 14
            lbl_size = 12 if is_date else 14
            icon_sz = 16 if is_date else 24
            
            echter_wert = val if val is not None else ""
            c = ft.TextField(
                label=label, value=echter_wert, 
                multiline=False if is_date else multiline,
                color="#FF9800", text_style=ft.TextStyle(size=txt_size, color="#FF9800"), 
                label_style=ft.TextStyle(color="white", size=lbl_size), 
                border_color="white", dense=True, content_padding=pad, width=w, on_change=oc
            )
            items = [ft.PopupMenuItem(content=ft.Text(o, size=14), on_click=lambda e, opt=o: (setattr(c, 'value', opt), c.update())) for o in opts]
            
            c.suffix = ft.PopupMenuButton(
                items=items, 
                content=ft.Container(content=ft.Text("▼", color="white", size=icon_sz), padding=pad)
            )
            return c
            
        def action_btn_form(text, oc, farbe):
            return ft.ElevatedButton(content=ft.Text(text, size=16, weight="bold"), on_click=oc, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=20, side=ft.BorderSide(width=2, color=farbe)))
            
        def emoji_btn(text, oc, farbe):
            return ft.ElevatedButton(content=ft.Text(text, size=14, weight="bold"), on_click=oc, bgcolor="#1a1a1a", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=15, side=ft.BorderSide(width=1.5, color=farbe)))

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
            if val:
                e.control.value = val + " °C"
                e.control.update()

        def format_gramm(e):
            val = (e.control.value or "").strip()
            if val and not val.lower().endswith("g") and not val.lower().endswith("ml"):
                e.control.value = val + " g"; e.control.update()

        def cb(label, val, oc=None, bold=False):
            return ft.Checkbox(
                label=label, value=bool(val), on_change=oc, 
                label_style=ft.TextStyle(color="white", size=16 if bold else 14, weight="bold" if bold else "normal"), 
                fill_color="#FF9800", check_color="black"
            )

        def d_row(t_dd, m_dd, j_dd):
            return ft.Row([ft.Container(content=t_dd, expand=1), ft.Container(content=m_dd, expand=1), ft.Container(content=j_dd, expand=1)], spacing=5)

        htoday, mtoday, jtoday = heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2]
        
        def get_herst(key):
            val = str(aktuelle_daten.get(key, "")).strip()
            if not val or len(val.split(".")) != 3 or val == "..": return "", "", jtoday
            return val.split(".")[0], val.split(".")[1], val.split(".")[2]

        # ==========================================
        # STAMMDATEN
        # ==========================================
        d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
        tag_dd, mon_dd, jahr_dd = combo("Tag", d_tag, tage_opts), combo("Mon", d_mon, mon_opts), combo("Jahr", d_jahr, jahr_opts)
        datum_row = ft.Column([ft.Text("Datum der Probenahme", color="#2196F3", weight="bold", size=16), d_row(tag_dd, mon_dd, jahr_dd)])
        
        adr_in = tf("Adresse Markt", aktuelle_daten.get("adresse", ""), multiline=True)
        nr_in = tf("Marktnummer", aktuelle_daten.get("marktnummer", ""))
        auft_in = tf("Auftragsnummer", aktuelle_daten.get("auftragsnummer", ""), "Etikettenummer: XX-XXXXXXX")
        name_in = tf("Name Probenehmer", aktuelle_daten.get("mitarbeiter_name", ""))
        bem_in = tf("Zusätzliche Bemerkung", aktuelle_daten.get("bemerkung", ""), multiline=True)
        ag_dd = combo("Auftraggeber", aktuelle_daten.get("auftraggeber", "03509 - REWE Hackfleischmonitoring"), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund (Hackfleischmonitoring)"])
        typ_dd = combo("Typ der Probenahme", aktuelle_daten.get("typ_probenahme", "Standard"), ["Standard", "Nachkontrolle", "Mehrwöchig"])

        # ==========================================
        # TRINKWASSER & SCHERBENEIS
        # ==========================================
        tw_kalt_cb = cb("Trinkwasser kalt", aktuelle_daten.get("tw_kalt", False), bold=True)
        tw_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("tw_override", False))
        
        tw_zeit_in, tw_temp_in, tw_tempkonst_in = tf("Probenahmezeit", aktuelle_daten.get("tw_zeit", ""), ob=format_zeit), tf("Temp Probenahme", aktuelle_daten.get("tw_temp", ""), ob=format_temp), tf("Temp Konstante", aktuelle_daten.get("tw_tempkonst", ""), ob=format_temp)
        tw_desinf_dd = combo("Desinfektion", aktuelle_daten.get("tw_desinf", "Abflammen"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
        tw_zapf_dd = combo("Zapfstelle", aktuelle_daten.get("tw_zapf", "Spülbecken"), ["Spülbecken", "Handwaschbecken"])
        tw_zapf_sonst_dd = combo("Sonstiges Zapfstelle", aktuelle_daten.get("tw_zapf_sonst", ""), ["", "Schlaucharmatur", "Schlauchbrause", "Schlauch mit Brause"])
        tw_inaktiv_dd = combo("Inaktivierung", aktuelle_daten.get("tw_inaktiv", "Na-Thiosulfat"), ["Na-Thiosulfat"])
        tw_kurz1_dd = combo("Farbe", aktuelle_daten.get("tw_kurz1", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
        tw_kurz2_dd = combo("Trübung", aktuelle_daten.get("tw_kurz2", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
        tw_kurz3_dd = combo("Bodensatz", aktuelle_daten.get("tw_kurz3", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
        tw_kurz4_dd = combo("Geruch", aktuelle_daten.get("tw_kurz4", "1 - nicht wahrnehmbar"), ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"])
        tw_zweck_dd = combo("Zweck", aktuelle_daten.get("tw_zweck", "Zweck B"), ["Zweck A", "Zweck B", "Zweck C"])
        tw_verpackung_dd = combo("Verpackung", aktuelle_daten.get("tw_verpackung", "500ml Kunststoff-Flasche mit Natriumthiosulfat"), ["", "500ml Kunststoff-Flasche mit Natriumthiosulfat", "steriler Probenbecher", "steriler Probenbeutel"])
        tw_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("tw_entnahmeort", "Metzgerei"), ort_opts)
        tw_bemerkung_dd = combo("TW Bemerkung", aktuelle_daten.get("tw_bemerkung_2", ""), ["", "Keine Besonderheiten"])
        
        cb_pn, cb_zwei, cb_sensor, cb_knie = cb("PN-Hahn", aktuelle_daten.get("tw_cb_pn", False)), cb("Zweigriff", aktuelle_daten.get("tw_cb_zwei", False)), cb("Sensor", aktuelle_daten.get("tw_cb_sensor", False)), cb("Knie", aktuelle_daten.get("tw_cb_knie", False))
        cb_ein, cb_ein_g, cb_eck = cb("Einhebel", aktuelle_daten.get("tw_cb_ein", False)), cb("Eingriff", aktuelle_daten.get("tw_cb_ein_g", False)), cb("Eckventil", aktuelle_daten.get("tw_cb_eck", False))
        cb_auff_ja, cb_auff_nein, cb_auff_perl = cb("ja", aktuelle_daten.get("tw_auff_ja", False)), cb("nein", aktuelle_daten.get("tw_auff_nein", False)), cb("Perlator nicht entfernbar", aktuelle_daten.get("tw_auff_perlator", False))
        cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf = cb("Starke Verkalkung", aktuelle_daten.get("tw_auff_kalk", False)), cb("Armatur mit Verbrühschutz", aktuelle_daten.get("tw_auff_verbrueh", False)), cb("Durchlauferhitzer", aktuelle_daten.get("tw_auff_durchlauf", False))
        cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich = cb("Unterbauspeicher", aktuelle_daten.get("tw_auff_unterbau", False)), cb("Eckventil warm/kalt geschlossen", aktuelle_daten.get("tw_auff_eckventil", False)), cb("nicht möglich", aktuelle_daten.get("tw_auff_unmoeglich", False))
        cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst = cb("Entnahme Dusche", aktuelle_daten.get("tw_auff_dusche", False)), cb("Handbrause", aktuelle_daten.get("tw_auff_handbrause", False)), cb("Sonstiges", aktuelle_daten.get("tw_auff_sonstiges", False))
        tw_auff_sonstiges_in, tw_inhalt_in = tf("Auffälligkeiten (Sonstiges)", aktuelle_daten.get("tw_auff_sonst_text", ""), multiline=True), tf("Inhalt", aktuelle_daten.get("tw_inhalt", ""))

        se_kalt_cb = cb("Scherbeneis Eigenkontrolle", aktuelle_daten.get("se_kalt", False), bold=True)
        se_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("se_override", False))
        se_zeit_in = tf("Probenahmezeit", aktuelle_daten.get("se_zeit", ""), ob=format_zeit)
        se_zapf_dd = combo("Zapfstelle (Eis)", aktuelle_daten.get("se_zapf", "Eismaschine"), ["Eismaschine"])
        se_cb_eiswanne, se_cb_fallprobe = cb("Eiswanne/Schöpfprobe", aktuelle_daten.get("se_cb_eiswanne", False)), cb("Fallprobe", aktuelle_daten.get("se_cb_fallprobe", True))
        se_tech_sonst_in = tf("Sonstiges (Technik)", aktuelle_daten.get("se_tech_sonst", ""), multiline=True)
        se_desinf_dd = combo("Art der Desinfektion", aktuelle_daten.get("se_desinf", "ohne Desinfektion"), ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"])
        se_cb_ozon = cb("Ozonsterilisator", aktuelle_daten.get("se_cb_ozon", False))
        se_auff_sonst_in = tf("Sonstiges (Auffälligkeiten)", aktuelle_daten.get("se_auff_sonst", ""), multiline=True)
        se_inhalt_in = tf("Inhalt", aktuelle_daten.get("se_inhalt", ""))
        se_verpackung_dd = combo("Verpackung", aktuelle_daten.get("se_verpackung", "steriler Probenbeutel"), verp_opts)
        se_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("se_entnahmeort", "Fischabteilung-Eismaschine"), ort_opts)
        se_temp_in = tf("Probenahmetemperatur", aktuelle_daten.get("se_temp", ""), ob=format_temp)
        se_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("se_bemerkung", ""), ["", "Keine Besonderheiten"])

        # ==========================================
        # FLEISCH (HFM)
        # ==========================================
        hfm_hack_cb = cb("Hackfleisch gemischt", aktuelle_daten.get("hfm_hack_cb", False), bold=True)
        hfm_hack_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("hfm_hack_override", False))
        hfm_hack_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_hack_entnahmeort", "Kühlraum"), ort_opts)
        ht, hm, hj = get_herst("hfm_hack_herstelldatum")
        hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd = combo("Tag", ht, tage_opts), combo("Mon", hm, mon_opts), combo("Jahr", hj, jahr_opts)
        
        t, m, j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_schwein", ""), "", "", jtoday)
        hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_s_jahr_dd = combo("Tag", t, tage_opts), combo("Mon", m, mon_opts), combo("Jahr", j, jahr_opts)
        
        t, m, j = parse_datum(aktuelle_daten.get("hfm_hack_mhd_rind", ""), "", "", jtoday)
        hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, hfm_hack_mhd_r_jahr_dd = combo("Tag", t, tage_opts), combo("Mon", m, mon_opts), combo("Jahr", j, jahr_opts)
        
        hfm_hack_inhalt_in = tf("Inhalt", aktuelle_daten.get("hfm_hack_inhalt", ""))
        hfm_hack_verpackung_dd = combo("Verpackung", aktuelle_daten.get("hfm_hack_verpackung", "steriler Probenbeutel"), verp_opts)
        hfm_hack_lief_schwein_in = tf("Lieferant (Schwein)", aktuelle_daten.get("hfm_hack_lief_schwein", ""))
        hfm_hack_lief_rind_in = tf("Lieferant (Rind)", aktuelle_daten.get("hfm_hack_lief_rind", ""))
        hfm_hack_charge_schwein_dd = combo("Charge Schwein", aktuelle_daten.get("hfm_hack_charge_schwein", ""), c_opts_s)
        hfm_hack_charge_rind_dd = combo("Charge Rind", aktuelle_daten.get("hfm_hack_charge_rind", ""), c_opts_r)
        hfm_hack_temp_in = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_hack_temp", ""), ob=format_temp)
        hfm_hack_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("hfm_hack_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_mett_cb = cb("Gewürztes Schweinemett", aktuelle_daten.get("hfm_mett_cb", False), bold=True)
        hfm_mett_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("hfm_mett_override", False))
        hfm_mett_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_mett_entnahmeort", "Kühlraum"), ort_opts)
        ht, hm, hj = get_herst("hfm_mett_herstelldatum")
        hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd = combo("Tag", ht, tage_opts), combo("Mon", hm, mon_opts), combo("Jahr", hj, jahr_opts)
        
        t, m, j = parse_datum(aktuelle_daten.get("hfm_mett_mhd", ""), "", "", jtoday)
        hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, hfm_mett_mhd_jahr_dd = combo("Tag", t, tage_opts), combo("Mon", m, mon_opts), combo("Jahr", j, jahr_opts)
        
        hfm_mett_inhalt_in = tf("Inhalt", aktuelle_daten.get("hfm_mett_inhalt", ""))
        hfm_mett_verpackung_dd = combo("Verpackung", aktuelle_daten.get("hfm_mett_verpackung", "steriler Probenbeutel"), verp_opts)
        hfm_mett_lief_in = tf("Lieferant Rohware", aktuelle_daten.get("hfm_mett_lief", ""))
        hfm_mett_charge_dd = combo("Charge Rohware", aktuelle_daten.get("hfm_mett_charge", ""), c_opts_s)
        hfm_mett_temp_in = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_mett_temp", ""), ob=format_temp)
        hfm_mett_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("hfm_mett_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_fzs_cb = cb("Fleischzubereitung Schwein", aktuelle_daten.get("hfm_fzs_cb", False), bold=True)
        hfm_fzs_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("hfm_fzs_override", False))
        hfm_fzs_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_fzs_entnahmeort", "Kühlraum"), ort_opts)
        hfm_fzs_produkt_in = tf("Produkt", aktuelle_daten.get("hfm_fzs_produkt", ""))
        hfm_fzs_marinade_in = tf("Marinade", aktuelle_daten.get("hfm_fzs_marinade", ""))
        ht, hm, hj = get_herst("hfm_fzs_herstelldatum")
        hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_herst_jahr_dd = combo("Tag", ht, tage_opts), combo("Mon", hm, mon_opts), combo("Jahr", hj, jahr_opts)
        
        t, m, j = parse_datum(aktuelle_daten.get("hfm_fzs_mhd", ""), "", "", jtoday)
        hfm_fzs_mhd_tag_dd, hfm_fzs_mhd_mon_dd, hfm_fzs_mhd_jahr_dd = combo("Tag", t, tage_opts), combo("Mon", m, mon_opts), combo("Jahr", j, jahr_opts)
        
        hfm_fzs_inhalt_in = tf("Inhalt", aktuelle_daten.get("hfm_fzs_inhalt", ""))
        hfm_fzs_verpackung_dd = combo("Verpackung", aktuelle_daten.get("hfm_fzs_verpackung", "steriler Probenbeutel"), verp_opts)
        hfm_fzs_lief_in = tf("Lieferant Rohware", aktuelle_daten.get("hfm_fzs_lief", ""))
        hfm_fzs_charge_dd = combo("Charge Rohware", aktuelle_daten.get("hfm_fzs_charge", ""), c_opts_s)
        hfm_fzs_temp_in = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_fzs_temp", ""), ob=format_temp)
        hfm_fzs_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("hfm_fzs_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_fzg_cb = cb("Fleischzubereitung Geflügel", aktuelle_daten.get("hfm_fzg_cb", False), bold=True)
        hfm_fzg_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("hfm_fzg_override", False))
        hfm_fzg_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_fzg_entnahmeort", "Kühlraum"), ort_opts)
        hfm_fzg_produkt_in = tf("Produkt", aktuelle_daten.get("hfm_fzg_produkt", ""))
        hfm_fzg_marinade_in = tf("Marinade", aktuelle_daten.get("hfm_fzg_marinade", ""))
        ht, hm, hj = get_herst("hfm_fzg_herstelldatum")
        hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_herst_jahr_dd = combo("Tag", ht, tage_opts), combo("Mon", hm, mon_opts), combo("Jahr", hj, jahr_opts)
        
        t, m, j = parse_datum(aktuelle_daten.get("hfm_fzg_mhd", ""), "", "", jtoday)
        hfm_fzg_mhd_tag_dd, hfm_fzg_mhd_mon_dd, hfm_fzg_mhd_jahr_dd = combo("Tag", t, tage_opts), combo("Mon", m, mon_opts), combo("Jahr", j, jahr_opts)
        
        hfm_fzg_inhalt_in = tf("Inhalt", aktuelle_daten.get("hfm_fzg_inhalt", ""))
        hfm_fzg_verpackung_dd = combo("Verpackung", aktuelle_daten.get("hfm_fzg_verpackung", "steriler Probenbeutel"), verp_opts)
        hfm_fzg_lief_in = tf("Lieferant Rohware", aktuelle_daten.get("hfm_fzg_lief", ""))
        hfm_fzg_charge_dd = combo("Charge Rohware", aktuelle_daten.get("hfm_fzg_charge", ""), c_opts_g)
        hfm_fzg_temp_in = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_fzg_temp", ""), ob=format_temp)
        hfm_fzg_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("hfm_fzg_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_bio_cb = cb("Bio-Hackfleisch", aktuelle_daten.get("hfm_bio_cb", False), bold=True)
        hfm_bio_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("hfm_bio_override", False))
        hfm_bio_entnahmeort_dd = combo("Entnahmeort", aktuelle_daten.get("hfm_bio_entnahmeort", "Produktionsraum"), ort_opts)
        ht, hm, hj = get_herst("hfm_bio_herstelldatum")
        hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_herst_jahr_dd = combo("Tag", ht, tage_opts), combo("Mon", hm, mon_opts), combo("Jahr", hj, jahr_opts)
        
        t, m, j = parse_datum(aktuelle_daten.get("hfm_bio_mhd_schwein", ""), "", "", jtoday)
        hfm_bio_mhd_s_tag_dd, hfm_bio_mhd_s_mon_dd, hfm_bio_mhd_s_jahr_dd = combo("Tag", t, tage_opts), combo("Mon", m, mon_opts), combo("Jahr", j, jahr_opts)
        
        t, m, j = parse_datum(aktuelle_daten.get("hfm_bio_mhd_rind", ""), "", "", jtoday)
        hfm_bio_mhd_r_tag_dd, hfm_bio_mhd_r_mon_dd, hfm_bio_mhd_r_jahr_dd = combo("Tag", t, tage_opts), combo("Mon", m, mon_opts), combo("Jahr", j, jahr_opts)
        
        hfm_bio_inhalt_in = tf("Inhalt", aktuelle_daten.get("hfm_bio_inhalt", ""))
        hfm_bio_verpackung_dd = combo("Verpackung", aktuelle_daten.get("hfm_bio_verpackung", "steriler Probenbecher"), verp_opts)
        hfm_bio_lief_schwein_in = tf("Lieferant (Schwein)", aktuelle_daten.get("hfm_bio_lief_schwein", ""))
        hfm_bio_lief_rind_in = tf("Lieferant (Rind)", aktuelle_daten.get("hfm_bio_lief_rind", ""))
        hfm_bio_charge_schwein_dd = combo("Charge Schwein", aktuelle_daten.get("hfm_bio_charge_schwein", ""), c_opts_s)
        hfm_bio_charge_rind_dd = combo("Charge Rind", aktuelle_daten.get("hfm_bio_charge_rind", ""), c_opts_r)
        hfm_bio_temp_in = tf("Probenahmetemperatur", aktuelle_daten.get("hfm_bio_temp", ""), ob=format_temp)
        hfm_bio_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("hfm_bio_bemerkung", ""), ["", "Keine Besonderheiten"])

        hfm_okz_cb = cb("Abklatschproben HFM", aktuelle_daten.get("hfm_abklatsch_cb", False), bold=True)
        hfm_okz_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("hfm_abklatsch_override", False))
        hfm_okz_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("hfm_abklatsch_bemerkung", ""), ["", "Keine Besonderheiten"])
        okz_obj_opts = ["", "Fleischwolf-Auflage", "Fleischwolf-Lochscheibe", "Fleischwolf-Auswurf", "Fleischwolf-Spirale", "Wand am Fleischwolf", "Hackstecher", "Schaufel", "Thekenschale", "Messer", "Schneidebrett", "Auflage Knochensäge", "Tisch", "Fleischwanne", "Kühlhausgriff", "Schüssel", "Seifenspender"]
        okz_def = {1: {"o": "Fleischwolf-Auflage", "a": True, "t": False}, 2: {"o": "Fleischwolf-Auswurf", "a": True, "t": True}, 3: {"o": "Thekenschale", "a": True, "t": False}, 4: {"o": "Hackstecher", "a": True, "t": True}, 5: {"o": "Messer", "a": True, "t": False}, 6: {"o": "Schneidebrett", "a": True, "t": False}, 7: {"o": "Wand am Fleischwolf", "a": True, "t": True}, 8: {"o": "", "a": False, "t": False}, 9: {"o": "", "a": False, "t": False}, 10: {"o": "", "a": False, "t": False}}
        okz_controls = {}
        for i in range(1, 11):
            idx = f"{i:02d}"
            okz_controls[idx] = {"status": combo("Status", aktuelle_daten.get(f"0010_status_{idx}", "R+D"), ["R+D", "R", "P", "-"]), "objekt": combo("Objekt", aktuelle_daten.get(f"0010_objekt_{idx}") or okz_def[i]["o"], okz_obj_opts), "ort": combo("Probenahmeort", aktuelle_daten.get(f"0010_ort_{idx}", "Kühlraum"), ["Kühlraum", "Produktionsbereich", "Theke"]), "abklatsch": cb("Abklatsch", aktuelle_daten.get(f"0010_abklatsch_{idx}", okz_def[i]["a"])), "tupfer": cb("Tupfer", aktuelle_daten.get(f"0010_tupfer_{idx}", okz_def[i]["t"]))}

        # ==========================================
        # CONVENIENCE (OG)
        # ==========================================
        og_cb = cb("Obst-/Gemüse Convenience", aktuelle_daten.get("og_cb", False), bold=True)
        og_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("og_override", False))
        
        og_controls = {}
        for i in range(1, 6):
            idx = f"{i:02d}"
            ht, hm, hj = parse_datum(aktuelle_daten.get(f"og_herst_{idx}", ""), "", "", jtoday)
            vt, vm, vj = parse_datum(aktuelle_daten.get(f"og_verb_{idx}", ""), "", "", jtoday)
            og_controls[i] = {
                "name": tf(f"Name Teilprobe {i}", aktuelle_daten.get(f"og_name_{idx}", "")),
                "ort": combo("Entnahmeort", aktuelle_daten.get(f"og_ort_{idx}", "Produktionsraum"), ["Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Kühlraum", "SB-Theke", "Salatbar", "Saftpresse"]),
                "h_t": combo("Tag", ht, tage_opts), "h_m": combo("Mon", hm, mon_opts), "h_j": combo("Jahr", hj, jahr_opts),
                "v_t": combo("Tag", vt, tage_opts), "v_m": combo("Mon", vm, mon_opts), "v_j": combo("Jahr", vj, jahr_opts),
                "inhalt": tf("Inhalt", aktuelle_daten.get(f"og_inhalt_{idx}", ""), "Grammzahl", ob=format_gramm),
                "verpackung": combo("Verpackung", aktuelle_daten.get(f"og_verp_{idx}", "steriler Probenbecher"), verp_opts),
                "temp": tf("Probenahmetemperatur", aktuelle_daten.get(f"og_temp_{idx}", ""), ob=format_temp)
            }

        og_okz_cb = cb("Abklatschproben Convenience", aktuelle_daten.get("og_abklatsch_cb", False), bold=True)
        og_okz_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("og_abklatsch_override", False))
        og_okz_bemerkung_dd = combo("Bemerkungen", aktuelle_daten.get("og_abklatsch_bemerkung_1", ""), ["", "Keine Besonderheiten"])
        og_okz_anmerkung_in = tf("Anmerkung", aktuelle_daten.get("og_abklatsch_bemerkung_2", ""), multiline=True)
        
        og_okz_opts = ["", "Schneidebrett", "Messer", "Saftpresse Auffanggitter", "Saftpresse Rückwand", "Saftpresse Auslass", "Waagenauflage", "Schüssel", "Löffel", "GN-Behälter"]
        og_okz_def = {1: {"o": "Schneidebrett", "a": True, "t": True}, 2: {"o": "Messer", "a": True, "t": True}, 3: {"o": "Waagenauflage", "a": True, "t": False}, 4: {"o": "", "a": False, "t": False}, 5: {"o": "", "a": False, "t": False}}
        og_okz_controls = {}
        for i in range(1, 6):
            idx = f"{i:02d}"
            og_okz_controls[idx] = {"status": combo("Status", aktuelle_daten.get(f"0011_status_{idx}", "R+D"), ["R+D", "R", "P", "-"]), "objekt": combo("Objekt", aktuelle_daten.get(f"0011_objekt_{idx}") or og_okz_def[i]["o"], og_okz_opts), "ort": combo("Probenahmeort", aktuelle_daten.get(f"0011_ort_{idx}", "Produktionsbereich"), ["Kühlraum", "Produktionsbereich", "Theke"]), "abklatsch": cb("Abklatsch", aktuelle_daten.get(f"0011_abklatsch_{idx}", og_okz_def[i]["a"])), "tupfer": cb("Tupfer", aktuelle_daten.get(f"0011_tupfer_{idx}", og_okz_def[i]["t"]))}

        # ==========================================
        # VORLAGEN LOGIK 
        # ==========================================
        alle_vorlagen = lade_vorlagen_lokal()
        vorlagen_status = ft.Text("", weight="bold", size=14) 
        
        vl_dd = ft.Dropdown(
            options=[ft.dropdown.Option(k) for k in alle_vorlagen.keys()], 
            hint_text="Vorlage wählen...", dense=True, content_padding=15, 
            color="#FF9800", text_style=ft.TextStyle(color="#FF9800", size=14), 
            border_color="white" 
        )
        vl_name_in = tf("Als neue Vorlage speichern", "")

        def lade_v(e):
            if not vl_dd.value: return
            v = alle_vorlagen.get(vl_dd.value, {})
            
            def setze_wert(ctrl, key, default=""):
                if ctrl is None: return
                val = v.get(key, default)
                if isinstance(ctrl, ft.Checkbox): ctrl.value = bool(val)
                else: ctrl.value = str(val) if val is not None else ""

            tag_dd.value, mon_dd.value, jahr_dd.value = htoday, mtoday, jtoday
            setze_wert(adr_in, "adresse")
            setze_wert(nr_in, "marktnummer")
            setze_wert(auft_in, "auftragsnummer")
            setze_wert(name_in, "mitarbeiter_name")
            setze_wert(ag_dd, "auftraggeber")
            setze_wert(typ_dd, "typ_probenahme")
            setze_wert(bem_in, "bemerkung")

            setze_wert(tw_kalt_cb, "tw_kalt", False)
            setze_wert(tw_override_cb, "tw_override", False)
            setze_wert(tw_zeit_in, "tw_zeit")
            setze_wert(tw_temp_in, "tw_temp")
            setze_wert(tw_tempkonst_in, "tw_tempkonst")
            setze_wert(tw_desinf_dd, "tw_desinf")
            setze_wert(tw_zapf_dd, "tw_zapf")
            setze_wert(cb_pn, "tw_cb_pn", False)
            setze_wert(cb_zwei, "tw_cb_zwei", False)
            setze_wert(cb_sensor, "tw_cb_sensor", False)
            setze_wert(cb_knie, "tw_cb_knie", False)
            setze_wert(cb_ein, "tw_cb_ein", False)
            setze_wert(cb_ein_g, "tw_cb_ein_g", False)
            setze_wert(cb_eck, "tw_cb_eck", False)
            setze_wert(tw_zapf_sonst_dd, "tw_zapf_sonst")
            setze_wert(tw_inaktiv_dd, "tw_inaktiv")
            setze_wert(tw_kurz1_dd, "tw_kurz1")
            setze_wert(tw_kurz2_dd, "tw_kurz2")
            setze_wert(tw_kurz3_dd, "tw_kurz3")
            setze_wert(tw_kurz4_dd, "tw_kurz4")
            setze_wert(cb_auff_ja, "tw_auff_ja", False)
            setze_wert(cb_auff_nein, "tw_auff_nein", False)
            setze_wert(cb_auff_perl, "tw_auff_perlator", False)
            setze_wert(cb_auff_verkalk, "tw_auff_kalk", False)
            setze_wert(cb_auff_verbrueh, "tw_auff_verbrueh", False)
            setze_wert(cb_auff_durchlauf, "tw_auff_durchlauf", False)
            setze_wert(cb_auff_eck_zu, "tw_auff_eckventil", False)
            setze_wert(cb_auff_unterbau, "tw_auff_unterbau", False)
            setze_wert(cb_auff_nichtmoeglich, "tw_auff_unmoeglich", False)
            setze_wert(cb_auff_dusche, "tw_auff_dusche", False)
            setze_wert(cb_auff_handbrause, "tw_auff_handbrause", False)
            setze_wert(cb_auff_sonst, "tw_auff_sonstiges", False)
            setze_wert(tw_auff_sonstiges_in, "tw_auff_sonst_text")
            setze_wert(tw_zweck_dd, "tw_zweck")
            setze_wert(tw_inhalt_in, "tw_inhalt")
            setze_wert(tw_verpackung_dd, "tw_verpackung")
            setze_wert(tw_entnahmeort_dd, "tw_entnahmeort")
            setze_wert(tw_bemerkung_dd, "tw_bemerkung_2")

            setze_wert(se_kalt_cb, "se_kalt", False)
            setze_wert(se_override_cb, "se_override", False)
            setze_wert(se_zeit_in, "se_zeit")
            setze_wert(se_zapf_dd, "se_zapf")
            setze_wert(se_cb_eiswanne, "se_cb_eiswanne", False)
            setze_wert(se_cb_fallprobe, "se_cb_fallprobe", False)
            setze_wert(se_tech_sonst_in, "se_tech_sonst")
            setze_wert(se_desinf_dd, "se_desinf")
            setze_wert(se_cb_ozon, "se_cb_ozon", False)
            setze_wert(se_auff_sonst_in, "se_auff_sonst")
            setze_wert(se_inhalt_in, "se_inhalt")
            setze_wert(se_verpackung_dd, "se_verpackung")
            setze_wert(se_entnahmeort_dd, "se_entnahmeort")
            setze_wert(se_temp_in, "se_temp")
            setze_wert(se_bemerkung_dd, "se_bemerkung")

            def set_hfm_base(cb_c, over_c, ort_c, inhalt_c, verp_c, temp_c, bem_c, htag_c, hmon_c, hjahr_c, prefix):
                setze_wert(cb_c, f"{prefix}_cb", False)
                setze_wert(over_c, f"{prefix}_override", False)
                setze_wert(ort_c, f"{prefix}_entnahmeort")
                setze_wert(inhalt_c, f"{prefix}_inhalt")
                setze_wert(verp_c, f"{prefix}_verpackung")
                setze_wert(temp_c, f"{prefix}_temp")
                setze_wert(bem_c, f"{prefix}_bemerkung")
                ht, hm, hj = parse_datum(v.get(f"{prefix}_herstelldatum", ""))
                htag_c.value, hmon_c.value, hjahr_c.value = ht, hm, hj or jtoday

            set_hfm_base(hfm_hack_cb, hfm_hack_override_cb, hfm_hack_entnahmeort_dd, hfm_hack_inhalt_in, hfm_hack_verpackung_dd, hfm_hack_temp_in, hfm_hack_bemerkung_dd, hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd, "hfm_hack")
            setze_wert(hfm_hack_lief_schwein_in, "hfm_hack_lief_schwein")
            setze_wert(hfm_hack_charge_schwein_dd, "hfm_hack_charge_schwein")
            mst, msm, msj = parse_datum(v.get("hfm_hack_mhd_schwein", ""), "", "", jtoday)
            hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value = mst, msm, msj
            setze_wert(hfm_hack_lief_rind_in, "hfm_hack_lief_rind")
            setze_wert(hfm_hack_charge_rind_dd, "hfm_hack_charge_rind")
            mrt, mrm, mrj = parse_datum(v.get("hfm_hack_mhd_rind", ""), "", "", jtoday)
            hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value = mrt, mrm, mrj

            set_hfm_base(hfm_mett_cb, hfm_mett_override_cb, hfm_mett_entnahmeort_dd, hfm_mett_inhalt_in, hfm_mett_verpackung_dd, hfm_mett_temp_in, hfm_mett_bemerkung_dd, hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd, "hfm_mett")
            setze_wert(hfm_mett_lief_in, "hfm_mett_lief")
            setze_wert(hfm_mett_charge_dd, "hfm_mett_charge")
            mt, mm, mj = parse_datum(v.get("hfm_mett_mhd", ""), "", "", jtoday)
            hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value = mt, mm, mj

            set_hfm_base(hfm_fzs_cb, hfm_fzs_override_cb, hfm_fzs_entnahmeort_dd, hfm_fzs_inhalt_in, hfm_fzs_verpackung_dd, hfm_fzs_temp_in, hfm_fzs_bemerkung_dd, hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_herst_jahr_dd, "hfm_fzs")
            setze_wert(hfm_fzs_produkt_in, "hfm_fzs_produkt")
            setze_wert(hfm_fzs_marinade_in, "hfm_fzs_marinade")
            setze_wert(hfm_fzs_lief_in, "hfm_fzs_lief")
            setze_wert(hfm_fzs_charge_dd, "hfm_fzs_charge")
            mt, mm, mj = parse_datum(v.get("hfm_fzs_mhd", ""), "", "", jtoday)
            hfm_fzs_mhd_tag_dd.value, hfm_fzs_mhd_mon_dd.value, hfm_fzs_mhd_jahr_dd.value = mt, mm, mj

            set_hfm_base(hfm_fzg_cb, hfm_fzg_override_cb, hfm_fzg_entnahmeort_dd, hfm_fzg_inhalt_in, hfm_fzg_verpackung_dd, hfm_fzg_temp_in, hfm_fzg_bemerkung_dd, hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_herst_jahr_dd, "hfm_fzg")
            setze_wert(hfm_fzg_produkt_in, "hfm_fzg_produkt")
            setze_wert(hfm_fzg_marinade_in, "hfm_fzg_marinade")
            setze_wert(hfm_fzg_lief_in, "hfm_fzg_lief")
            setze_wert(hfm_fzg_charge_dd, "hfm_fzg_charge")
            mt, mm, mj = parse_datum(v.get("hfm_fzg_mhd", ""), "", "", jtoday)
            hfm_fzg_mhd_tag_dd.value, hfm_fzg_mhd_mon_dd.value, hfm_fzg_mhd_jahr_dd.value = mt, mm, mj

            set_hfm_base(hfm_bio_cb, hfm_bio_override_cb, hfm_bio_entnahmeort_dd, hfm_bio_inhalt_in, hfm_bio_verpackung_dd, hfm_bio_temp_in, hfm_bio_bemerkung_dd, hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_herst_jahr_dd, "hfm_bio")
            setze_wert(hfm_bio_lief_schwein_in, "hfm_bio_lief_schwein")
            setze_wert(hfm_bio_charge_schwein_dd, "hfm_bio_charge_schwein")
            mst, msm, msj = parse_datum(v.get("hfm_bio_mhd_schwein", ""), "", "", jtoday)
            hfm_bio_mhd_s_tag_dd.value, hfm_bio_mhd_s_mon_dd.value, hfm_bio_mhd_s_jahr_dd.value = mst, msm, msj
            setze_wert(hfm_bio_lief_rind_in, "hfm_bio_lief_rind")
            setze_wert(hfm_bio_charge_rind_dd, "hfm_bio_charge_rind")
            mrt, mrm, mrj = parse_datum(v.get("hfm_bio_mhd_rind", ""), "", "", jtoday)
            hfm_bio_mhd_r_tag_dd.value, hfm_bio_mhd_r_mon_dd.value, hfm_bio_mhd_r_jahr_dd.value = mrt, mrm, mrj

            setze_wert(hfm_okz_cb, "hfm_abklatsch_cb", False)
            setze_wert(hfm_okz_override_cb, "hfm_abklatsch_override", False)
            setze_wert(hfm_okz_bemerkung_dd, "hfm_abklatsch_bemerkung")
            for idx, c in okz_controls.items():
                c["status"].value = v.get(f"0010_status_{idx}", "R+D")
                setze_wert(c["objekt"], f"0010_objekt_{idx}")
                c["ort"].value = v.get(f"0010_ort_{idx}", "Kühlraum")
                setze_wert(c["abklatsch"], f"0010_abklatsch_{idx}", False)
                setze_wert(c["tupfer"], f"0010_tupfer_{idx}", False)

            setze_wert(og_cb, "og_cb", False)
            setze_wert(og_override_cb, "og_override", False)
            for i in range(1, 6):
                idx = f"{i:02d}"; c = og_controls[i]
                setze_wert(c["name"], f"og_name_{idx}")
                c["ort"].value = v.get(f"og_ort_{idx}", "Produktionsraum")
                setze_wert(c["inhalt"], f"og_inhalt_{idx}")
                c["verpackung"].value = v.get(f"og_verp_{idx}", "steriler Probenbecher")
                setze_wert(c["temp"], f"og_temp_{idx}")
                ht, hm, hj = parse_datum(v.get(f"og_herst_{idx}", ""))
                c["h_t"].value, c["h_m"].value, c["h_j"].value = ht, hm, hj or jtoday
                vt, vm, vj = parse_datum(v.get(f"og_verb_{idx}", ""), "", "", jtoday)
                c["v_t"].value, c["v_m"].value, c["v_j"].value = vt, vm, vj

            setze_wert(og_okz_cb, "og_abklatsch_cb", False)
            setze_wert(og_okz_override_cb, "og_abklatsch_override", False)
            setze_wert(og_okz_bemerkung_dd, "og_abklatsch_bemerkung_1")
            setze_wert(og_okz_anmerkung_in, "og_abklatsch_bemerkung_2")
            for idx, c in og_okz_controls.items():
                c["status"].value = v.get(f"0011_status_{idx}", "R+D")
                setze_wert(c["objekt"], f"0011_objekt_{idx}")
                c["ort"].value = v.get(f"0011_ort_{idx}", "Produktionsbereich")
                setze_wert(c["abklatsch"], f"0011_abklatsch_{idx}", False)
                setze_wert(c["tupfer"], f"0011_tupfer_{idx}", False)

            vorlagen_status.value = f"✅ '{vl_dd.value}' geladen!"
            vorlagen_status.color = "green"
            page.update()

        def del_v(e):
            if vl_dd.value in alle_vorlagen:
                del alle_vorlagen[vl_dd.value]
                speichere_vorlagen_lokal(alle_vorlagen)
                vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                vorlagen_status.value = f"🗑️ Gelöscht!"
                vorlagen_status.color = "red"
                vl_dd.value = None
                page.update()

        def save_v(e):
            if not (vl_name_in.value or "").strip(): return
            alle_vorlagen[vl_name_in.value] = hole_aktuelle_daten()
            speichere_vorlagen_lokal(alle_vorlagen)
            vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
            vl_dd.update() 
            vorlagen_status.value = f"✅ Vorlage gespeichert!"
            vorlagen_status.color = "#FF9800"
            vl_name_in.value = ""
            page.update()

        vorlagen_expansion = ft.ExpansionTile(
            title=ft.Text("📋 Vorlagen (Schnellauswahl)", weight="bold", color="white", size=18),
            collapsed_text_color="white", text_color="#4CAF50",
            controls=[
                ft.Container(bgcolor="#002b00", padding=15, border_radius=10, content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        vorlagen_status,
                        vl_dd, 
                        ft.Row([
                            ft.Container(content=emoji_btn("📥 Laden", lade_v, "#2196F3"), expand=1), 
                            ft.Container(content=emoji_btn("🗑️ Löschen", del_v, "#F44336"), expand=1)
                        ], spacing=10),
                        ft.Container(height=5),
                        vl_name_in,
                        emoji_btn("💾 Als Neu Speichern", save_v, "#FF9800")
                    ]
                ))
            ]
        )

        # ==========================================
        # DATEN SAMMELN
        # ==========================================
        def hole_aktuelle_daten():
            def get_val(ctrl, default_val):
                if ctrl is None or ctrl.value is None or str(ctrl.value).strip() == "": return str(default_val)
                return str(ctrl.value)

            d = {
                "datum": get_date_str(tag_dd.value, mon_dd.value, jahr_dd.value), 
                "adresse": adr_in.value, "marktnummer": nr_in.value, "auftragsnummer": auft_in.value, 
                "mitarbeiter_name": name_in.value, "auftraggeber": get_val(ag_dd, "03509 - REWE Hackfleischmonitoring"), 
                "typ_probenahme": get_val(typ_dd, "Standard"), "bemerkung": bem_in.value,
                
                "tw_kalt": bool(tw_kalt_cb.value), "tw_override": bool(tw_override_cb.value), 
                "tw_zeit": tw_zeit_in.value, "tw_temp": tw_temp_in.value, 
                "tw_desinf": get_val(tw_desinf_dd, "Abflammen"), "tw_zapf": get_val(tw_zapf_dd, "Spülbecken"), 
                "tw_cb_pn": bool(cb_pn.value), "tw_cb_zwei": bool(cb_zwei.value), "tw_cb_sensor": bool(cb_sensor.value), "tw_cb_knie": bool(cb_knie.value), 
                "tw_cb_ein": bool(cb_ein.value), "tw_cb_ein_g": bool(cb_ein_g.value), "tw_cb_eck": bool(cb_eck.value), 
                "tw_zapf_sonst": get_val(tw_zapf_sonst_dd, ""), "tw_inaktiv": get_val(tw_inaktiv_dd, "Na-Thiosulfat"), 
                "tw_kurz1": get_val(tw_kurz1_dd, "1 - nicht wahrnehmbar"), "tw_kurz2": get_val(tw_kurz2_dd, "1 - nicht wahrnehmbar"), 
                "tw_kurz3": get_val(tw_kurz3_dd, "1 - nicht wahrnehmbar"), "tw_kurz4": get_val(tw_kurz4_dd, "1 - nicht wahrnehmbar"), 
                "tw_auff_ja": bool(cb_auff_ja.value), "tw_auff_nein": bool(cb_auff_nein.value), "tw_auff_perlator": bool(cb_auff_perl.value), 
                "tw_auff_kalk": bool(cb_auff_verkalk.value), "tw_auff_verbrueh": bool(cb_auff_verbrueh.value), 
                "tw_auff_durchlauf": bool(cb_auff_durchlauf.value), "tw_auff_eckventil": bool(cb_auff_eck_zu.value), 
                "tw_auff_unterbau": bool(cb_auff_unterbau.value), "tw_auff_unmoeglich": bool(cb_auff_nichtmoeglich.value), 
                "tw_auff_dusche": bool(cb_auff_dusche.value), "tw_auff_handbrause": bool(cb_auff_handbrause.value), 
                "tw_auff_sonstiges": bool(cb_auff_sonst.value), "tw_auff_sonst_text": tw_auff_sonstiges_in.value, 
                "tw_zweck": get_val(tw_zweck_dd, "Zweck B"), "tw_inhalt": get_val(tw_inhalt_in, "ca. 500 ml"), 
                "tw_verpackung": get_val(tw_verpackung_dd, "500ml Kunststoff-Flasche mit Natriumthiosulfat"), 
                "tw_entnahmeort": get_val(tw_entnahmeort_dd, "Metzgerei"), "tw_tempkonst": tw_tempkonst_in.value, "tw_bemerkung_2": tw_bemerkung_dd.value,
                
                "se_kalt": bool(se_kalt_cb.value), "se_override": bool(se_override_cb.value), "se_zeit": se_zeit_in.value, "se_zapf": get_val(se_zapf_dd, "Eismaschine"), 
                "se_cb_eiswanne": bool(se_cb_eiswanne.value), "se_cb_fallprobe": bool(se_cb_fallprobe.value), 
                "se_tech_sonst": se_tech_sonst_in.value, "se_desinf": get_val(se_desinf_dd, "ohne Desinfektion"), 
                "se_cb_ozon": bool(se_cb_ozon.value), "se_auff_sonst": se_auff_sonst_in.value, "se_inhalt": get_val(se_inhalt_in, "ca. 1000ml"), 
                "se_verpackung": get_val(se_verpackung_dd, "steriler Probenbeutel"), "se_entnahmeort": get_val(se_entnahmeort_dd, "Fischabteilung-Eismaschine"), 
                "se_temp": se_temp_in.value, "se_bemerkung": se_bemerkung_dd.value, 
                
                "hfm_hack_cb": bool(hfm_hack_cb.value), "hfm_hack_override": bool(hfm_hack_override_cb.value), "hfm_hack_entnahmeort": get_val(hfm_hack_entnahmeort_dd, "Kühlraum"), 
                "hfm_hack_herstelldatum": get_date_str(hfm_hack_herst_tag_dd.value, hfm_hack_herst_mon_dd.value, hfm_hack_herst_jahr_dd.value), 
                "hfm_hack_inhalt": get_val(hfm_hack_inhalt_in, "jeweils ca. 200 g"), "hfm_hack_verpackung": get_val(hfm_hack_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_hack_lief_schwein": hfm_hack_lief_schwein_in.value, "hfm_hack_lief_rind": hfm_hack_lief_rind_in.value, 
                "hfm_hack_mhd_schwein": get_date_str(hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value), 
                "hfm_hack_mhd_rind": get_date_str(hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value), 
                "hfm_hack_charge_schwein": hfm_hack_charge_schwein_dd.value, "hfm_hack_charge_rind": hfm_hack_charge_rind_dd.value, 
                "hfm_hack_temp": hfm_hack_temp_in.value, "hfm_hack_bemerkung": hfm_hack_bemerkung_dd.value,
                
                "hfm_mett_cb": bool(hfm_mett_cb.value), "hfm_mett_override": bool(hfm_mett_override_cb.value), "hfm_mett_entnahmeort": get_val(hfm_mett_entnahmeort_dd, "Kühlraum"), 
                "hfm_mett_herstelldatum": get_date_str(hfm_mett_herst_tag_dd.value, hfm_mett_herst_mon_dd.value, hfm_mett_herst_jahr_dd.value), 
                "hfm_mett_inhalt": get_val(hfm_mett_inhalt_in, "ca. 200 g"), "hfm_mett_verpackung": get_val(hfm_mett_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_mett_lief": hfm_mett_lief_in.value, "hfm_mett_mhd": get_date_str(hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value), 
                "hfm_mett_charge": hfm_mett_charge_dd.value, "hfm_mett_temp": hfm_mett_temp_in.value, "hfm_mett_bemerkung": hfm_mett_bemerkung_dd.value,
                
                "hfm_fzs_cb": bool(hfm_fzs_cb.value), "hfm_fzs_override": bool(hfm_fzs_override_cb.value), "hfm_fzs_entnahmeort": get_val(hfm_fzs_entnahmeort_dd, "Kühlraum"), 
                "hfm_fzs_produkt": hfm_fzs_produkt_in.value, "hfm_fzs_marinade": hfm_fzs_marinade_in.value, 
                "hfm_fzs_herstelldatum": get_date_str(hfm_fzs_herst_tag_dd.value, hfm_fzs_herst_mon_dd.value, hfm_fzs_herst_jahr_dd.value), 
                "hfm_fzs_inhalt": get_val(hfm_fzs_inhalt_in, "ca. 200 g"), "hfm_fzs_verpackung": get_val(hfm_fzs_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_fzs_lief": hfm_fzs_lief_in.value, "hfm_fzs_mhd": get_date_str(hfm_fzs_mhd_tag_dd.value, hfm_fzs_mhd_mon_dd.value, hfm_fzs_mhd_jahr_dd.value), 
                "hfm_fzs_charge": hfm_fzs_charge_dd.value, "hfm_fzs_temp": hfm_fzs_temp_in.value, "hfm_fzs_bemerkung": hfm_fzs_bemerkung_dd.value,
                
                "hfm_fzg_cb": bool(hfm_fzg_cb.value), "hfm_fzg_override": bool(hfm_fzg_override_cb.value), "hfm_fzg_entnahmeort": get_val(hfm_fzg_entnahmeort_dd, "Kühlraum"), 
                "hfm_fzg_produkt": hfm_fzg_produkt_in.value, "hfm_fzg_marinade": hfm_fzg_marinade_in.value, 
                "hfm_fzg_herstelldatum": get_date_str(hfm_fzg_herst_tag_dd.value, hfm_fzg_herst_mon_dd.value, hfm_fzg_herst_jahr_dd.value), 
                "hfm_fzg_inhalt": get_val(hfm_fzg_inhalt_in, "ca. 200 g"), "hfm_fzg_verpackung": get_val(hfm_fzg_verpackung_dd, "steriler Probenbeutel"), 
                "hfm_fzg_lief": hfm_fzg_lief_in.value, "hfm_fzg_mhd": get_date_str(hfm_fzg_mhd_tag_dd.value, hfm_fzg_mhd_mon_dd.value, hfm_fzg_mhd_jahr_dd.value), 
                "hfm_fzg_charge": hfm_fzg_charge_dd.value, "hfm_fzg_temp": hfm_fzg_temp_in.value, "hfm_fzg_bemerkung": hfm_fzg_bemerkung_dd.value,
                
                "hfm_bio_cb": bool(hfm_bio_cb.value), "hfm_bio_override": bool(hfm_bio_override_cb.value), "hfm_bio_entnahmeort": get_val(hfm_bio_entnahmeort_dd, "Produktionsraum"), 
                "hfm_bio_inhalt": get_val(hfm_bio_inhalt_in, "jeweils ca. 200 g"), "hfm_bio_verpackung": get_val(hfm_bio_verpackung_dd, "steriler Probenbecher"), 
                "hfm_bio_lief_schwein": hfm_bio_lief_schwein_in.value, "hfm_bio_lief_rind": hfm_bio_lief_rind_in.value, 
                "hfm_bio_mhd_schwein": get_date_str(hfm_bio_mhd_s_tag_dd.value, hfm_bio_mhd_s_mon_dd.value, hfm_bio_mhd_s_jahr_dd.value), 
                "hfm_bio_mhd_rind": get_date_str(hfm_bio_mhd_r_tag_dd.value, hfm_bio_mhd_r_mon_dd.value, hfm_bio_mhd_r_jahr_dd.value), 
                "hfm_bio_charge_schwein": hfm_bio_charge_schwein_dd.value, "hfm_bio_charge_rind": hfm_bio_charge_rind_dd.value, 
                "hfm_bio_temp": hfm_bio_temp_in.value, "hfm_bio_bemerkung": hfm_bio_bemerkung_dd.value, 
                
                "hfm_abklatsch_cb": bool(hfm_okz_cb.value), "hfm_abklatsch_override": bool(hfm_okz_override_cb.value), "hfm_abklatsch_bemerkung": hfm_okz_bemerkung_dd.value,
                
                "og_cb": bool(og_cb.value), "og_override": bool(og_override_cb.value), 
                "og_abklatsch_cb": bool(og_okz_cb.value), "og_abklatsch_override": bool(og_okz_override_cb.value),
                "og_abklatsch_bemerkung_1": og_okz_bemerkung_dd.value, "og_abklatsch_bemerkung_2": og_okz_anmerkung_in.value,
            }

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

        # ==========================================
        # DIE INTELLIGENTE PFLICHTFELD-PRÜFUNG
        # ==========================================
        def reset_fehler_markierungen():
            for ctrl in markierte_fehler_controls:
                if hasattr(ctrl, "border_color"):
                    ctrl.border_color = "white"
                if isinstance(ctrl, ft.Checkbox):
                    old_size = ctrl.label_style.size if ctrl.label_style else 16
                    old_weight = ctrl.label_style.weight if ctrl.label_style else "bold"
                    ctrl.label_style = ft.TextStyle(color="white", size=old_size, weight=old_weight)
                try: ctrl.update()
                except: pass
            markierte_fehler_controls.clear()

        def check_pflichtfelder():
            reset_fehler_markierungen() 
            errors = []
            
            def highlight_ctrl(ctrl):
                if ctrl is None: return
                if hasattr(ctrl, "border_color"):
                    ctrl.border_color = "red"
                if isinstance(ctrl, ft.Checkbox):
                    old_size = ctrl.label_style.size if ctrl.label_style else 16
                    old_weight = ctrl.label_style.weight if ctrl.label_style else "bold"
                    ctrl.label_style = ft.TextStyle(color="red", size=old_size, weight=old_weight)
                markierte_fehler_controls.append(ctrl)
                try: ctrl.update()
                except: pass

            def err(msg, tab, sub_tab, ctrl):
                errors.append({"msg": msg, "tab": tab, "sub": sub_tab, "ctrl": ctrl})
                highlight_ctrl(ctrl)

            def markiere_extra(ctrl):
                highlight_ctrl(ctrl)

            # --- Stammdaten ---
            if not (nr_in.value or "").strip(): err("Stammdaten: Marktnummer fehlt", "stamm", None, nr_in)
            if not (adr_in.value or "").strip(): err("Stammdaten: Adresse fehlt", "stamm", None, adr_in)
            if not (auft_in.value or "").strip(): err("Stammdaten: Auftragsnummer fehlt", "stamm", None, auft_in)
            if not (name_in.value or "").strip(): err("Stammdaten: Probenehmer fehlt", "stamm", None, name_in)

            def check_datum_komplett(t_ctrl, m_ctrl, feld_name, tab, sub_tab):
                t = (t_ctrl.value or "").strip()
                m = (m_ctrl.value or "").strip()
                if not t or not m:
                    err(f"{feld_name}: Tag und Monat müssen angegeben werden", tab, sub_tab, t_ctrl)
                    markiere_extra(m_ctrl)

            # --- Trinkwasser ---
            if not tw_override_cb.value:
                tw_daten = any([(tw_temp_in.value or "").strip(), (tw_zeit_in.value or "").strip()])
                if tw_daten and not tw_kalt_cb.value: 
                    err("Trinkwasser: Daten eingetragen, aber Haken vergessen!", "tw", "wasser", tw_kalt_cb)
                elif tw_kalt_cb.value:
                    if not (tw_temp_in.value or "").strip(): err("Trinkwasser: Temperatur fehlt", "tw", "wasser", tw_temp_in)
                    if not (tw_zeit_in.value or "").strip(): err("Trinkwasser: Uhrzeit fehlt", "tw", "wasser", tw_zeit_in)
                    
                    armaturen_cbs = [cb_pn, cb_zwei, cb_sensor, cb_knie, cb_ein, cb_ein_g, cb_eck]
                    anzahl_angekreuzt = sum(1 for c in armaturen_cbs if c.value)
                    
                    if anzahl_angekreuzt == 0:
                        for c in armaturen_cbs: markiere_extra(c)
                        err("Trinkwasser: Bitte genau EINE Entnahmestelle ankreuzen!", "tw", "wasser", cb_pn)
                    elif anzahl_angekreuzt > 1:
                        for c in armaturen_cbs: 
                            if c.value: markiere_extra(c)
                        err("Trinkwasser: Es darf nur EINE Entnahmestelle angekreuzt sein!", "tw", "wasser", cb_pn)

            # --- Scherbeneis ---
            if not se_override_cb.value:
                se_daten = any([(se_temp_in.value or "").strip(), (se_zeit_in.value or "").strip()])
                if se_daten and not se_kalt_cb.value: 
                    err("Scherbeneis: Daten eingetragen, aber Haken vergessen!", "tw", "eis", se_kalt_cb)
                elif se_kalt_cb.value:
                    if not (se_temp_in.value or "").strip(): err("Scherbeneis: Temperatur fehlt", "tw", "eis", se_temp_in)
                    if not (se_zeit_in.value or "").strip(): err("Scherbeneis: Uhrzeit fehlt", "tw", "eis", se_zeit_in)

            # --- HFM FLEISCH ---
            def check_hfm(cb_ctrl, override_cb, temp, h_t, h_m, l_s, l_r, c_s, c_r, mhd_s_t, mhd_s_m, mhd_r_t, mhd_r_m, name, tab):
                if override_cb.value: return 
                alle_felder = [f for f in [temp, h_t, h_m, l_s, l_r, c_s, c_r, mhd_s_t, mhd_s_m, mhd_r_t, mhd_r_m] if f is not None]
                daten_vorhanden = any([(f.value or "").strip() for f in alle_felder])
                
                if daten_vorhanden and not cb_ctrl.value: 
                    err(f"{name}: Daten eingetragen, aber Haupt-Haken vergessen!", "hfm", tab, cb_ctrl)
                elif cb_ctrl.value:
                    if not (temp.value or "").strip(): err(f"{name}: Temperatur fehlt", "hfm", tab, temp)
                    check_datum_komplett(h_t, h_m, f"{name}: Herstellungsdatum", "hfm", tab)
                    if l_s and not (l_s.value or "").strip(): err(f"{name}: Lieferant (Schwein) fehlt", "hfm", tab, l_s)
                    if c_s and not (c_s.value or "").strip(): err(f"{name}: Charge (Schwein) fehlt", "hfm", tab, c_s)
                    if mhd_s_t: check_datum_komplett(mhd_s_t, mhd_s_m, f"{name}: MHD (Schwein)", "hfm", tab)
                    if l_r and not (l_r.value or "").strip(): err(f"{name}: Lieferant (Rind) fehlt", "hfm", tab, l_r)
                    if c_r and not (c_r.value or "").strip(): err(f"{name}: Charge (Rind) fehlt", "hfm", tab, c_r)
                    if mhd_r_t: check_datum_komplett(mhd_r_t, mhd_r_m, f"{name}: MHD (Rind)", "hfm", tab)

            check_hfm(hfm_hack_cb, hfm_hack_override_cb, hfm_hack_temp_in, hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_lief_schwein_in, hfm_hack_lief_rind_in, hfm_hack_charge_schwein_dd, hfm_hack_charge_rind_dd, hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, "Hackfleisch", "hack")
            check_hfm(hfm_mett_cb, hfm_mett_override_cb, hfm_mett_temp_in, hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_lief_in, None, hfm_mett_charge_dd, None, None, None, hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, "Mett", "mett")
            check_hfm(hfm_fzs_cb, hfm_fzs_override_cb, hfm_fzs_temp_in, hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_lief_in, None, hfm_fzs_charge_dd, None, None, None, hfm_fzs_mhd_tag_dd, hfm_fzs_mhd_mon_dd, "FZ Schwein", "fzs")
            check_hfm(hfm_fzg_cb, hfm_fzg_override_cb, hfm_fzg_temp_in, hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_lief_in, None, hfm_fzg_charge_dd, None, None, None, hfm_fzg_mhd_tag_dd, hfm_fzg_mhd_mon_dd, "FZ Geflügel", "fzg")
            check_hfm(hfm_bio_cb, hfm_bio_override_cb, hfm_bio_temp_in, hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_lief_schwein_in, hfm_bio_lief_rind_in, hfm_bio_charge_schwein_dd, hfm_bio_charge_rind_dd, hfm_bio_mhd_s_tag_dd, hfm_bio_mhd_s_mon_dd, hfm_bio_mhd_r_tag_dd, hfm_bio_mhd_r_mon_dd, "Bio Hack", "bio")

            # --- HFM OKZ Prüfung (INTELLIGENT) ---
            if not hfm_okz_override_cb.value:
                hfm_okz_modified = False
                hfm_okz_valid_data = False
                for i in range(1, 11):
                    c = okz_controls[f"{i:02d}"]
                    obj_val = (c["objekt"].value or "").strip()
                    def_o = okz_def[i]["o"]
                    def_a = okz_def[i]["a"]
                    def_t = okz_def[i]["t"]
                    
                    if obj_val != def_o or c["abklatsch"].value != def_a or c["tupfer"].value != def_t:
                        hfm_okz_modified = True
                        
                    if obj_val or c["abklatsch"].value or c["tupfer"].value:
                        hfm_okz_valid_data = True
                        
                if hfm_okz_modified and not hfm_okz_cb.value:
                    err("HFM OKZ: Daten manuell geändert, aber Haupt-Haken vergessen!", "hfm", "okz", hfm_okz_cb)
                elif hfm_okz_cb.value and not hfm_okz_valid_data:
                    err("HFM OKZ: Haupt-Haken gesetzt, aber alle Proben sind leer!", "hfm", "okz", hfm_okz_cb)
                elif hfm_okz_cb.value:
                    for i in range(1, 11):
                        c = okz_controls[f"{i:02d}"]
                        obj_val = (c["objekt"].value or "").strip()
                        has_a = c["abklatsch"].value
                        has_t = c["tupfer"].value
                        
                        if obj_val and not (has_a or has_t):
                            err(f"HFM OKZ (Probe {i}): Objekt gewählt, aber kein Abklatsch/Tupfer angekreuzt!", "hfm", "okz", c["abklatsch"])
                            markiere_extra(c["tupfer"])
                        elif (has_a or has_t) and not obj_val:
                            err(f"HFM OKZ (Probe {i}): Haken gesetzt, aber Objekt fehlt!", "hfm", "okz", c["objekt"])

            # --- CONVENIENCE (OG) TEILPROBEN ---
            if not og_override_cb.value:
                og_daten_vorhanden = False
                for i in range(1, 6):
                    c = og_controls[i]
                    if any([(f.value or "").strip() for f in [c["name"], c["temp"], c["h_t"], c["h_m"]]]):
                        og_daten_vorhanden = True
                        break
                        
                if og_daten_vorhanden and not og_cb.value: 
                    err("Convenience: Daten eingetragen, aber Haupt-Haken vergessen!", "og", "teil", og_cb)
                elif og_cb.value:
                    for i in range(1, 6):
                        c = og_controls[i]
                        if (c["name"].value or "").strip():
                            if not (c["temp"].value or "").strip(): err(f"OG (Probe {i}): Temperatur fehlt", "og", "teil", c["temp"])
                            check_datum_komplett(c["h_t"], c["h_m"], f"OG (Probe {i}): Herstellungsdatum", "og", "teil")

            # --- CONVENIENCE OKZ Prüfung (INTELLIGENT) ---
            if not og_okz_override_cb.value:
                og_okz_modified = False
                og_okz_valid_data = False
                for i in range(1, 6):
                    c = og_okz_controls[f"{i:02d}"]
                    obj_val = (c["objekt"].value or "").strip()
                    def_o = og_okz_def[i]["o"]
                    def_a = og_okz_def[i]["a"]
                    def_t = og_okz_def[i]["t"]
                    
                    if obj_val != def_o or c["abklatsch"].value != def_a or c["tupfer"].value != def_t:
                        og_okz_modified = True
                        
                    if obj_val or c["abklatsch"].value or c["tupfer"].value:
                        og_okz_valid_data = True
                        
                if og_okz_modified and not og_okz_cb.value:
                    err("Convenience OKZ: Daten manuell geändert, aber Haupt-Haken vergessen!", "og", "okz", og_okz_cb)
                elif og_okz_cb.value and not og_okz_valid_data:
                    err("Convenience OKZ: Haupt-Haken gesetzt, aber alle Proben sind leer!", "og", "okz", og_okz_cb)
                elif og_okz_cb.value:
                    for i in range(1, 6):
                        c = og_okz_controls[f"{i:02d}"]
                        obj_val = (c["objekt"].value or "").strip()
                        has_a = c["abklatsch"].value
                        has_t = c["tupfer"].value
                        
                        if obj_val and not (has_a or has_t):
                            err(f"Convenience OKZ (Probe {i}): Objekt gewählt, aber kein Abklatsch/Tupfer angekreuzt!", "og", "okz", c["abklatsch"])
                            markiere_extra(c["tupfer"])
                        elif (has_a or has_t) and not obj_val:
                            err(f"Convenience OKZ (Probe {i}): Haken gesetzt, aber Objekt fehlt!", "og", "okz", c["objekt"])

            return errors

        # ==========================================
        # TARGETED RESET LOGIK
        # ==========================================
        def reset_form(e):
            reset_fehler_markierungen() 
            
            t = current_tab_state[0]
            if t == "stamm":
                adr_in.value, nr_in.value, auft_in.value, name_in.value, bem_in.value = "", "", "", "", ""
                ag_dd.value = "03509 - REWE Hackfleischmonitoring"
                typ_dd.value = "Standard"
                tag_dd.value, mon_dd.value, jahr_dd.value = htoday, mtoday, jtoday
            elif t == "tw":
                sub = current_sub_tab_state[0]
                if sub == "wasser":
                    for c in [tw_kalt_cb, tw_override_cb, cb_pn, cb_zwei, cb_sensor, cb_knie, cb_ein, cb_ein_g, cb_eck, cb_auff_ja, cb_auff_nein, cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf, cb_auff_eck_zu, cb_auff_unterbau, cb_auff_nichtmoeglich, cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst]: c.value = False
                    for c in [tw_zeit_in, tw_temp_in, tw_tempkonst_in, tw_zapf_sonst_dd, tw_auff_sonstiges_in, tw_bemerkung_dd, tw_inhalt_in]: c.value = ""
                    tw_desinf_dd.value = "Abflammen"
                    tw_zapf_dd.value = "Spülbecken"
                    tw_inaktiv_dd.value = "Na-Thiosulfat"
                    tw_kurz1_dd.value, tw_kurz2_dd.value, tw_kurz3_dd.value, tw_kurz4_dd.value = "1 - nicht wahrnehmbar", "1 - nicht wahrnehmbar", "1 - nicht wahrnehmbar", "1 - nicht wahrnehmbar"
                    tw_zweck_dd.value = "Zweck B"
                    tw_verpackung_dd.value = "500ml Kunststoff-Flasche mit Natriumthiosulfat"
                    tw_entnahmeort_dd.value = "Metzgerei"
                elif sub == "eis":
                    for c in [se_kalt_cb, se_override_cb, se_cb_eiswanne, se_cb_ozon]: c.value = False
                    se_cb_fallprobe.value = True
                    for c in [se_zeit_in, se_tech_sonst_in, se_auff_sonst_in, se_inhalt_in, se_temp_in, se_bemerkung_dd]: c.value = ""
                    se_zapf_dd.value = "Eismaschine"
                    se_desinf_dd.value = "ohne Desinfektion"
                    se_verpackung_dd.value = "steriler Probenbeutel"
                    se_entnahmeort_dd.value = "Fischabteilung-Eismaschine"
            elif t == "hfm":
                sub = current_sub_tab_state[0]
                if sub == "hack":
                    hfm_hack_cb.value, hfm_hack_override_cb.value = False, False
                    hfm_hack_entnahmeort_dd.value = "Kühlraum"
                    hfm_hack_herst_tag_dd.value, hfm_hack_herst_mon_dd.value, hfm_hack_herst_jahr_dd.value = "", "", jtoday
                    hfm_hack_inhalt_in.value, hfm_hack_verpackung_dd.value, hfm_hack_lief_schwein_in.value, hfm_hack_lief_rind_in.value = "", "steriler Probenbeutel", "", ""
                    hfm_hack_mhd_s_tag_dd.value, hfm_hack_mhd_s_mon_dd.value, hfm_hack_mhd_s_jahr_dd.value = "", "", jtoday
                    hfm_hack_mhd_r_tag_dd.value, hfm_hack_mhd_r_mon_dd.value, hfm_hack_mhd_r_jahr_dd.value = "", "", jtoday
                    hfm_hack_charge_schwein_dd.value, hfm_hack_charge_rind_dd.value, hfm_hack_temp_in.value, hfm_hack_bemerkung_dd.value = "", "", "", ""
                elif sub == "mett":
                    hfm_mett_cb.value, hfm_mett_override_cb.value = False, False
                    hfm_mett_entnahmeort_dd.value = "Kühlraum"
                    hfm_mett_herst_tag_dd.value, hfm_mett_herst_mon_dd.value, hfm_mett_herst_jahr_dd.value = "", "", jtoday
                    hfm_mett_inhalt_in.value, hfm_mett_verpackung_dd.value, hfm_mett_lief_in.value = "", "steriler Probenbeutel", ""
                    hfm_mett_mhd_tag_dd.value, hfm_mett_mhd_mon_dd.value, hfm_mett_mhd_jahr_dd.value = "", "", jtoday
                    hfm_mett_charge_dd.value, hfm_mett_temp_in.value, hfm_mett_bemerkung_dd.value = "", "", ""
                elif sub == "fzs":
                    hfm_fzs_cb.value, hfm_fzs_override_cb.value = False, False
                    hfm_fzs_entnahmeort_dd.value = "Kühlraum"
                    hfm_fzs_produkt_in.value, hfm_fzs_marinade_in.value, hfm_fzs_inhalt_in.value = "", "", ""
                    hfm_fzs_herst_tag_dd.value, hfm_fzs_herst_mon_dd.value, hfm_fzs_herst_jahr_dd.value = "", "", jtoday
                    hfm_fzs_verpackung_dd.value = "steriler Probenbeutel"
                    hfm_fzs_lief_in.value, hfm_fzs_mhd_tag_dd.value, hfm_fzs_mhd_mon_dd.value, hfm_fzs_mhd_jahr_dd.value = "", "", jtoday
                    hfm_fzs_charge_dd.value, hfm_fzs_temp_in.value, hfm_fzs_bemerkung_dd.value = "", "", ""
                elif sub == "fzg":
                    hfm_fzg_cb.value, hfm_fzg_override_cb.value = False, False
                    hfm_fzg_entnahmeort_dd.value = "Kühlraum"
                    hfm_fzg_produkt_in.value, hfm_fzg_marinade_in.value, hfm_fzg_inhalt_in.value = "", "", ""
                    hfm_fzg_herst_tag_dd.value, hfm_fzg_herst_mon_dd.value, hfm_fzg_herst_jahr_dd.value = "", "", jtoday
                    hfm_fzg_verpackung_dd.value = "steriler Probenbeutel"
                    hfm_fzg_lief_in.value, hfm_fzg_mhd_tag_dd.value, hfm_fzg_mhd_mon_dd.value, hfm_fzg_mhd_jahr_dd.value = "", "", jtoday
                    hfm_fzg_charge_dd.value, hfm_fzg_temp_in.value, hfm_fzg_bemerkung_dd.value = "", "", ""
                elif sub == "bio":
                    hfm_bio_cb.value, hfm_bio_override_cb.value = False, False
                    hfm_bio_entnahmeort_dd.value = "Produktionsraum"
                    hfm_bio_herst_tag_dd.value, hfm_bio_herst_mon_dd.value, hfm_bio_herst_jahr_dd.value = "", "", jtoday
                    hfm_bio_inhalt_in.value, hfm_bio_verpackung_dd.value, hfm_bio_lief_schwein_in.value, hfm_bio_lief_rind_in.value = "", "steriler Probenbecher", "", ""
                    hfm_bio_mhd_s_tag_dd.value, hfm_bio_mhd_s_mon_dd.value, hfm_bio_mhd_s_jahr_dd.value = "", "", jtoday
                    hfm_bio_mhd_r_tag_dd.value, hfm_bio_mhd_r_mon_dd.value, hfm_bio_mhd_r_jahr_dd.value = "", "", jtoday
                    hfm_bio_charge_schwein_dd.value, hfm_bio_charge_rind_dd.value, hfm_bio_temp_in.value, hfm_bio_bemerkung_dd.value = "", "", "", ""
                elif sub == "okz":
                    hfm_okz_cb.value, hfm_okz_override_cb.value, hfm_okz_bemerkung_dd.value = False, False, ""
                    for idx, c in okz_controls.items():
                        c["status"].value, c["objekt"].value, c["ort"].value = "R+D", okz_def[int(idx)]["o"], "Kühlraum"
                        c["abklatsch"].value, c["tupfer"].value = okz_def[int(idx)]["a"], okz_def[int(idx)]["t"]
            elif t == "og":
                sub = current_sub_tab_state[0]
                if sub == "teil":
                    og_cb.value, og_override_cb.value = False, False
                    for i in range(1, 6):
                        c = og_controls[i]
                        c["name"].value, c["inhalt"].value, c["temp"].value = "", "", ""
                        c["ort"].value, c["verpackung"].value = "Produktionsraum", "steriler Probenbecher"
                        c["h_t"].value, c["h_m"].value, c["h_j"].value = "", "", jtoday
                        c["v_t"].value, c["v_m"].value, c["v_j"].value = "", "", jtoday
                elif sub == "okz":
                    og_okz_cb.value, og_okz_override_cb.value, og_okz_bemerkung_dd.value, og_okz_anmerkung_in.value = False, False, "", ""
                    for idx, c in og_okz_controls.items():
                        c["status"].value, c["objekt"].value, c["ort"].value = "R+D", og_okz_def[int(idx)]["o"], "Produktionsbereich"
                        c["abklatsch"].value, c["tupfer"].value = og_okz_def[int(idx)]["a"], og_okz_def[int(idx)]["t"]

            fehler_container.visible = False
            status_text.value = "🔄 REITER GELEERT!"
            status_text.color = "#FF9800"
            page.update()

        def nur_speichern(e):
            fehler_container.visible = False
            status_text.value = ""
            page.update()

            try:
                status_text.value = "⏳ Speichere..."; status_text.color = "#FF9800"; page.update()
                maerkte = lade_maerkte()
                d = hole_aktuelle_daten()
                
                tour_aktualisiert = False
                if nr_in.value.strip(): 
                    for i, tour in enumerate(maerkte):
                        if tour.get("marktnummer") == nr_in.value: 
                            maerkte[i] = d
                            tour_aktualisiert = True
                            break
                            
                if not tour_aktualisiert:
                    if markt_index is not None and markt_index < len(maerkte):
                        maerkte[markt_index] = d
                    else:
                        maerkte.append(d)
                        
                speichere_maerkte(maerkte)
                status_text.value = "✅ Gespeichert!"; status_text.color = "#FF9800"; page.update()
            except Exception as ex: 
                status_text.value = "❌ Fehler"; status_text.color = "red"; zeige_fehler(ex)
        
        def save_final(e):
            fehler_container.visible = False
            status_text.value = ""
            page.update()

            errs = check_pflichtfelder()
            if errs:
                first_err = errs[0]
                switch_tab(first_err["tab"], first_err["sub"])
                
                fehler_container.controls.clear()
                fehler_container.controls.append(ft.Text("⚠️ BITTE PRÜFEN (Fehler sind rot markiert):", color="red", weight="bold", size=16))
                
                for i, err_item in enumerate(errs):
                    fehler_container.controls.append(ft.Text(f"{i+1}. {err_item['msg']}", color="#ffcccc", size=14))
                
                fehler_container.visible = True
                try: fehler_container.update()
                except: pass
                try: ansicht.update()
                except: pass
                page.update()
                return

            try:
                status_text.value = "⏳ PDF..."; status_text.color = "#FF9800"; page.update()
                maerkte = lade_maerkte()
                d = hole_aktuelle_daten()
                
                tour_aktualisiert = False
                if nr_in.value.strip(): 
                    for i, tour in enumerate(maerkte):
                        if tour.get("marktnummer") == nr_in.value: 
                            maerkte[i] = d
                            tour_aktualisiert = True
                            break
                            
                if not tour_aktualisiert:
                    if markt_index is not None and markt_index < len(maerkte):
                        maerkte[markt_index] = d
                    else:
                        maerkte.append(d)
                        
                speichere_maerkte(maerkte)
                
                try:
                    saved_path = erstelle_bericht(d)
                    fname = os.path.basename(saved_path)
                    status_text.value = f"✅ BERICHT!\n{fname}"; status_text.color = "green"
                except Exception as ex:
                    status_text.value = ""; fehler_container.controls.append(ft.Text(f"⚠️ FEHLER: {str(ex)}", color="red"))
                page.update()
            except Exception as ex: 
                status_text.value = "❌ Fehler"; status_text.color = "red"; zeige_fehler(ex)

        bottom_buttons = ft.Column([
            ft.Row([
                ft.Container(content=action_btn_form("🚚 Touren", lambda e: zeige_dashboard(), "#F44336"), expand=1),
                ft.Container(content=action_btn_form("🔄 Reset", reset_form, "#9C27B0"), expand=1),
            ]),
            ft.Row([
                ft.Container(content=action_btn_form("💾 Speichern", nur_speichern, "#FF9800"), expand=1),
                ft.Container(content=action_btn_form("📄 Bericht", save_final, "#2196F3"), expand=1),
            ])
        ], spacing=10)

        def switch_tab(tab_id, sub_tab_id=None):
            nonlocal top_nav, haupt_bereich
            current_tab_state[0] = tab_id
            haupt_bereich.controls.clear(); top_nav.controls.clear()
            tabs = [("stamm", "Stammdaten"), ("tw", "Trinkwasser"), ("hfm", "HFM"), ("og", "Convenience")]
            for tid, tname in tabs:
                is_act = (tid == tab_id)
                btn = ft.ElevatedButton(tname, on_click=lambda e, t=tid: switch_tab(t), bgcolor="#004400" if is_act else "#1a1a1a", color="white",
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=12, side=ft.BorderSide(width=1.5, color="#4CAF50")))
                top_nav.controls.append(btn)
            
            if tab_id == "stamm":
                haupt_bereich.controls.extend([vorlagen_expansion, ft.Divider(color="white24"), ft.Text("Stammdaten", size=24, weight="bold", color="#FF9800", text_align=ft.TextAlign.CENTER), datum_row, adr_in, nr_in, auft_in, ag_dd, name_in, typ_dd, bem_in])
            elif tab_id == "tw":
                tab_title = ft.Text("Trinkwasser & Eis", size=24, weight="bold", color="#FF9800", text_align=ft.TextAlign.CENTER)
                sub_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
                haupt_bereich.controls.extend([tab_title, sub_nav])
                def sw_tw(sub):
                    current_sub_tab_state[0] = sub
                    haupt_bereich.controls[2:] = []
                    sub_nav.controls.clear()
                    for sid, sname in [("wasser", "🚰 Trinkwasser"), ("eis", "❄️ Scherbeneis")]:
                        is_active = (sid == sub)
                        btn = ft.ElevatedButton(sname, on_click=lambda e, s=sid: sw_tw(s), bgcolor="#004400" if is_active else "#1a1a1a", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=12, side=ft.BorderSide(width=1.5, color="#4CAF50")))
                        sub_nav.controls.append(btn)
                    if sub == "wasser":
                        tab_title.value = "Trinkwasser"
                        haupt_bereich.controls.extend([ft.Row([tw_kalt_cb, tw_override_cb], wrap=True), tw_zeit_in, tw_temp_in, tw_tempkonst_in, ft.Divider(color="white24"), ft.Text("Probenahme / Zapfstelle:", color="#2196F3", weight="bold"), tw_entnahmeort_dd, tw_zapf_dd, tw_zapf_sonst_dd, tw_desinf_dd, ft.Row([cb_pn, cb_zwei, cb_sensor, cb_knie], wrap=True), ft.Row([cb_ein, cb_ein_g, cb_eck], wrap=True), ft.Divider(color="white24"), ft.Text("Sensorik & Analytik:", color="#2196F3", weight="bold"), tw_inaktiv_dd, tw_kurz1_dd, tw_kurz2_dd, tw_kurz3_dd, tw_kurz4_dd, ft.Divider(color="white24"), ft.Text("Auffälligkeiten:", color="#2196F3", weight="bold"), ft.Row([cb_auff_ja, cb_auff_nein], wrap=True), cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf, cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich, cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst, tw_auff_sonstiges_in, ft.Divider(color="white24"), tw_zweck_dd, tw_inhalt_in, tw_verpackung_dd, tw_bemerkung_dd])
                    elif sub == "eis":
                        tab_title.value = "Scherbeneis"
                        haupt_bereich.controls.extend([ft.Row([se_kalt_cb, se_override_cb], wrap=True), se_zeit_in, se_zapf_dd, ft.Text("Technik:", color="#2196F3", weight="bold"), ft.Row([se_cb_eiswanne, se_cb_fallprobe], wrap=True), se_tech_sonst_in, se_desinf_dd, ft.Text("Auffälligkeiten:", color="#2196F3", weight="bold"), se_cb_ozon, se_auff_sonst_in, se_inhalt_in, se_verpackung_dd, se_entnahmeort_dd, se_temp_in, se_bemerkung_dd])
                    if page: page.update()
                sw_tw(sub_tab_id if sub_tab_id else "wasser")
            elif tab_id == "hfm":
                tab_title = ft.Text("HFM Fleisch", size=24, weight="bold", color="#FF9800", text_align=ft.TextAlign.CENTER)
                sub_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
                haupt_bereich.controls.extend([tab_title, sub_nav])
                def sw_hfm(sub):
                    current_sub_tab_state[0] = sub
                    haupt_bereich.controls[2:] = []
                    sub_nav.controls.clear()
                    for sid, sname in [("hack","🥩 Hack"), ("mett","🍖 Mett"), ("fzs","🐷 FZS"), ("fzg","🐔 FZG"), ("bio","🥩 Bio"), ("okz","🔬 OKZ")]:
                        is_sub_act = (sid == sub)
                        btn = ft.ElevatedButton(sname, on_click=lambda e, s=sid: sw_hfm(s), bgcolor="#004400" if is_sub_act else "#1a1a1a", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=5, side=ft.BorderSide(width=1, color="#4CAF50")))
                        sub_nav.controls.append(btn)
                    if sub == "hack":
                        tab_title.value = "HFM Fleisch Hackfleisch"
                        haupt_bereich.controls.extend([ft.Row([hfm_hack_cb, hfm_hack_override_cb], wrap=True), hfm_hack_entnahmeort_dd, ft.Text("Herstellungsdatum:", color="#2196F3", weight="bold"), d_row(hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd), hfm_hack_inhalt_in, hfm_hack_verpackung_dd, hfm_hack_lief_schwein_in, hfm_hack_lief_rind_in, ft.Text("MHD (Schwein):", color="#2196F3", weight="bold"), d_row(hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_s_jahr_dd), ft.Text("MHD (Rind):", color="#2196F3", weight="bold"), d_row(hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, hfm_hack_mhd_r_jahr_dd), hfm_hack_charge_schwein_dd, hfm_hack_charge_rind_dd, hfm_hack_temp_in, hfm_hack_bemerkung_dd])
                    elif sub == "mett":
                        tab_title.value = "HFM Fleisch Mett"
                        haupt_bereich.controls.extend([ft.Row([hfm_mett_cb, hfm_mett_override_cb], wrap=True), hfm_mett_entnahmeort_dd, ft.Text("Herstellungsdatum:", color="#2196F3", weight="bold"), d_row(hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd), hfm_mett_inhalt_in, hfm_mett_verpackung_dd, hfm_mett_lief_in, ft.Text("MHD:", color="#2196F3", weight="bold"), d_row(hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, hfm_mett_mhd_jahr_dd), hfm_mett_charge_dd, hfm_mett_temp_in, hfm_mett_bemerkung_dd])
                    elif sub == "fzs":
                        tab_title.value = "HFM Fleisch Schweine Zubereitung"
                        haupt_bereich.controls.extend([ft.Row([hfm_fzs_cb, hfm_fzs_override_cb], wrap=True), hfm_fzs_entnahmeort_dd, hfm_fzs_produkt_in, hfm_fzs_marinade_in, ft.Text("Herstellungsdatum:", color="#2196F3", weight="bold"), d_row(hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_herst_jahr_dd), hfm_fzs_inhalt_in, hfm_fzs_verpackung_dd, hfm_fzs_lief_in, ft.Text("MHD:", color="#2196F3", weight="bold"), d_row(hfm_fzs_mhd_tag_dd, hfm_fzs_mhd_mon_dd, hfm_fzs_mhd_jahr_dd), hfm_fzs_charge_dd, hfm_fzs_temp_in, hfm_fzs_bemerkung_dd])
                    elif sub == "fzg":
                        tab_title.value = "HFM Fleisch Geflügel Zubereitung"
                        haupt_bereich.controls.extend([ft.Row([hfm_fzg_cb, hfm_fzg_override_cb], wrap=True), hfm_fzg_entnahmeort_dd, hfm_fzg_produkt_in, hfm_fzg_marinade_in, ft.Text("Herstellungsdatum:", color="#2196F3", weight="bold"), d_row(hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_herst_jahr_dd), hfm_fzg_inhalt_in, hfm_fzg_verpackung_dd, hfm_fzg_lief_in, ft.Text("MHD:", color="#2196F3", weight="bold"), d_row(hfm_fzg_mhd_tag_dd, hfm_fzg_mhd_mon_dd, hfm_fzg_mhd_jahr_dd), hfm_fzg_charge_dd, hfm_fzg_temp_in, hfm_fzg_bemerkung_dd])
                    elif sub == "bio":
                        tab_title.value = "HFM Bio Fleisch"
                        haupt_bereich.controls.extend([ft.Row([hfm_bio_cb, hfm_bio_override_cb], wrap=True), hfm_bio_entnahmeort_dd, ft.Text("Herstellungsdatum:", color="#2196F3", weight="bold"), d_row(hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_herst_jahr_dd), hfm_bio_inhalt_in, hfm_bio_verpackung_dd, hfm_bio_lief_schwein_in, hfm_bio_lief_rind_in, ft.Text("MHD (Schwein):", color="#2196F3", weight="bold"), d_row(hfm_bio_mhd_s_tag_dd, hfm_bio_mhd_s_mon_dd, hfm_bio_mhd_s_jahr_dd), ft.Text("MHD (Rind):", color="#2196F3", weight="bold"), d_row(hfm_bio_mhd_r_tag_dd, hfm_bio_mhd_r_mon_dd, hfm_bio_mhd_r_jahr_dd), hfm_bio_charge_schwein_dd, hfm_bio_charge_rind_dd, hfm_bio_temp_in, hfm_bio_bemerkung_dd])
                    elif sub == "okz":
                        tab_title.value = "HFM OKZ"
                        haupt_bereich.controls.extend([ft.Row([hfm_okz_cb, hfm_okz_override_cb], wrap=True), ft.Divider(color="white24")])
                        for i in range(1, 11):
                            c = okz_controls[f"{i:02d}"]
                            haupt_bereich.controls.extend([ft.Text(f"Probe {i}", color="#FF9800", weight="bold"), ft.Row([ft.Container(content=c["status"], expand=1), ft.Container(content=c["objekt"], expand=3)]), c["ort"], ft.Row([ft.Container(content=c["abklatsch"], expand=1), ft.Container(content=c["tupfer"], expand=1)]), ft.Divider(color="white24")])
                        haupt_bereich.controls.append(hfm_okz_bemerkung_dd)
                    if page: page.update()
                sw_hfm(sub_tab_id if sub_tab_id else "hack")
            elif tab_id == "og":
                tab_title = ft.Text("Convenience", size=24, weight="bold", color="#FF9800", text_align=ft.TextAlign.CENTER)
                sub_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
                haupt_bereich.controls.extend([tab_title, sub_nav])
                def sw_og(sub):
                    current_sub_tab_state[0] = sub
                    haupt_bereich.controls[2:] = []
                    sub_nav.controls.clear()
                    for sid, sname in [("teil", "🥗 Proben"), ("okz", "🔬 OKZ")]:
                        is_sub_act = (sid == sub)
                        btn = ft.ElevatedButton(sname, on_click=lambda e, s=sid: sw_og(s), bgcolor="#004400" if is_sub_act else "#1a1a1a", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=8, side=ft.BorderSide(width=1.5, color="#4CAF50")))
                        sub_nav.controls.append(btn)
                    if sub == "teil":
                        tab_title.value = "Convenience"
                        haupt_bereich.controls.extend([ft.Row([og_cb, og_override_cb], wrap=True), ft.Divider(color="white24")])
                        for i in range(1, 6):
                            c = og_controls[i]
                            haupt_bereich.controls.extend([
                                ft.Text(f"Teilprobe {i}", color="#2196F3", weight="bold", size=20), 
                                c["name"], c["ort"], 
                                ft.Text("Herstellungsdatum:", color="#2196F3", weight="bold"), d_row(c["h_t"], c["h_m"], c["h_j"]), 
                                ft.Text("Verbrauchsdatum:", color="#2196F3", weight="bold"), d_row(c["v_t"], c["v_m"], c["v_j"]), 
                                c["inhalt"], c["verpackung"], c["temp"], 
                                ft.Container(height=15),
                                ft.Divider(color="white24"),
                                ft.Container(height=15)
                            ])
                    elif sub == "okz":
                        tab_title.value = "Convenience OKZ"
                        haupt_bereich.controls.extend([ft.Row([og_okz_cb, og_okz_override_cb], wrap=True), ft.Divider(color="white24")])
                        for i in range(1, 6):
                            c = og_okz_controls[f"{i:02d}"]
                            if i == 2: haupt_bereich.controls.append(ft.Text("💡 Info: Bei Saftpresse bitte hier auswählen.", color="white54", italic=True, size=14))
                            haupt_bereich.controls.extend([ft.Text(f"Probe {i}", color="#FF9800", weight="bold"), ft.Row([ft.Container(content=c["status"], expand=1), ft.Container(content=c["objekt"], expand=3)]), c["ort"], ft.Row([ft.Container(content=c["abklatsch"], expand=1), ft.Container(content=c["tupfer"], expand=1)]), ft.Divider(color="white24")])
                        haupt_bereich.controls.extend([ft.Text("💡 Wichtig: Wird die Saftpresse beprobt, muss zwingend auch das Messer aufgenommen werden!", color="#FF9800", weight="bold"), og_okz_bemerkung_dd, og_okz_anmerkung_in])
                    if page: page.update()
                sw_og(sub_tab_id if sub_tab_id else "teil")
            if page: page.update()

        ansicht.controls.extend([top_nav, ft.Divider(color="white24"), haupt_bereich, ft.Container(height=20), fehler_container, status_text, bottom_buttons])
        switch_tab("stamm")
    except Exception as ex: 
        if zeige_fehler: zeige_fehler(ex)
        else: ansicht.controls.append(ft.Text(f"CRASH: {str(ex)}", color="red"))
