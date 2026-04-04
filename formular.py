import flet as ft
import datetime
import os
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer
from pdf_generator import erstelle_bericht

def zeige_maske_ui(page, ansicht, zeige_dashboard, markt_index):
    maerkte = lade_maerkte()
    v, z = lade_benutzer()
    heute = datetime.datetime.now().strftime('%d.%m.%Y')
    
    d = maerkte[markt_index] if markt_index is not None else {"datum": heute, "mitarbeiter_name": f"{v} {z}".strip(), "auftraggeber": "03509 - REWE Hackfleischmonitoring", "typ_probenahme": "Standard"}

    ctrls = {}

    def TF(k, l, dv="", w=None, exp=False):
        ctrls[k] = ft.TextField(label=l, value=str(d.get(k, dv)), width=w, expand=exp, color="yellow", border_color="white", text_size=12, content_padding=5, label_style=ft.TextStyle(color="white"))
        return ctrls[k]
        
    def CB(k, l, dv=False):
        ctrls[k] = ft.Checkbox(label=l, value=bool(d.get(k, dv)), label_style=ft.TextStyle(color="white"), fill_color="yellow", check_color="black")
        return ctrls[k]
        
    def DD(k, l, opts, dv="", exp=False):
        c = TF(k, l, dv, exp=exp)
        c.suffix = ft.PopupMenuButton(items=[ft.PopupMenuItem(content=ft.Text(o), on_click=lambda e, opt=o: (setattr(c, 'value', opt), c.update())) for o in opts], icon="arrow_drop_down", icon_color="white")
        return c

    opts_ort = ["Fischabteilung", "Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke"]
    opts_verp = ["steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel u. etikett", "Pappschale mit Kunststofffolie umwickelt", "tiefgezogene Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie umwickelt", "SB-Kunststoffverpackung"]
    opts_s = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Schweinehackfleisch"]
    opts_r = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Rinderhackfleisch"]
    opts_g = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Geflügel"]

    dp = d.get("datum", heute).split(".")
    stamm_ui = ft.Column([
        ft.Row([TF("tag", "Tag", dp[0] if len(dp)>0 else "", w=60), TF("mon", "Monat", dp[1] if len(dp)>1 else "", w=60), TF("jahr", "Jahr", dp[2] if len(dp)>2 else "2026", w=80)]),
        TF("adresse", "Adresse Markt", exp=True), TF("marktnummer", "Marktnummer", exp=True), TF("auftragsnummer", "Auftragsnummer", exp=True),
        TF("mitarbeiter_name", "Probenehmer", exp=True), DD("auftraggeber", "Auftraggeber", ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund"], "03509 - REWE Hackfleischmonitoring", exp=True),
        DD("typ_probenahme", "Typ der Probenahme", ["Standard", "Nachkontrolle", "Mehrwöchig"], "Standard", exp=True), TF("bemerkung", "Zusätzliche Bemerkung", exp=True)
    ], scroll=ft.ScrollMode.AUTO)

    tw_se_ui = ft.Column([
        ft.Text("TRINKWASSER", size=18, color="white", weight="bold"),
        CB("tw_kalt", "Trinkwasser kalt"), ft.Row([TF("tw_zeit", "Uhrzeit", exp=True), TF("tw_temp", "Temp", exp=True)]),
        TF("tw_tempkonst", "Temp Konstante", exp=True), DD("tw_desinf", "Desinfektion", ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"], "Abflammen", exp=True),
        DD("tw_zapf", "Zapfstelle", ["Spülbecken", "Handwaschbecken"], "Spülbecken", exp=True), DD("tw_zapf_sonst", "Sonstiges Zapfstelle", ["Schlaucharmatur", "Schlauchbrause", "Schlauch mit Brause"], exp=True),
        ft.Text("Probenahmetechnik", color="white"),
        ft.Row([CB("tw_cb_pn", "PN-Hahn"), CB("tw_cb_ein", "Einhebel"), CB("tw_cb_zwei", "Zweigriff")]),
        ft.Row([CB("tw_cb_ein_g", "Eingriff"), CB("tw_cb_sensor", "Sensor"), CB("tw_cb_eck", "Eckventil")]), CB("tw_cb_knie", "Kniebestätigung"),
        DD("tw_inaktiv", "Inaktivierung", ["Na-Thiosulfat"], "Na-Thiosulfat", exp=True),
        ft.Text("Sensorik & Auffälligkeiten", color="white"),
        DD("tw_kurz1", "Farbe", ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], "1 - nicht wahrnehmbar", exp=True),
        DD("tw_kurz2", "Trübung", ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], "1 - nicht wahrnehmbar", exp=True),
        DD("tw_kurz3", "Bodensatz", ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], "1 - nicht wahrnehmbar", exp=True),
        DD("tw_kurz4", "Geruch", ["1 - nicht wahrnehmbar", "2 - wahrnehmbar", "3 - deutlich wahrnehmbar"], "1 - nicht wahrnehmbar", exp=True),
        ft.Row([CB("cb_auff_ja", "ja"), CB("cb_auff_nein", "nein")]), 
        CB("cb_auff_perl", "Perlator nicht entfernbar"), CB("cb_auff_verkalk", "Starke Verkalkung"), CB("cb_auff_verbrueh", "Verbrühschutz"), CB("cb_auff_durchlauf", "Durchlauferhitzer"), 
        CB("cb_auff_unterbau", "Unterbauspeicher"), CB("cb_auff_eck_zu", "Eckventil warm/kalt zu"), CB("cb_auff_nichtmoeglich", "nicht möglich"), CB("cb_auff_dusche", "Dusche"), 
        CB("cb_auff_handbrause", "Handbrause"), CB("cb_auff_sonst", "Sonstiges"), TF("tw_auff_sonstiges", "Auffälligkeiten Sonstiges", exp=True),
        DD("tw_zweck", "Zweck", ["Zweck A", "Zweck B", "Zweck C"], "Zweck B", exp=True), TF("tw_inhalt", "Inhalt", "ca. 500 ml", exp=True),
        DD("tw_verpackung", "Verpackung", ["500ml Kunststoff-Flasche mit Natriumthiosulfat"], "500ml Kunststoff-Flasche mit Natriumthiosulfat", exp=True), 
        DD("tw_entnahmeort", "Entnahmeort", opts_ort + ["Salatbar", "Convenience Küche"], "Metzgerei", exp=True), DD("tw_bemerkung", "Bemerkung", ["Bitte eingeben", "Keine Besonderheiten"], "Bitte eingeben", exp=True),
        ft.Divider(),
        ft.Text("SCHERBENEIS", size=18, color="white", weight="bold"),
        CB("se_kalt", "Scherbeneis"), ft.Row([TF("se_zeit", "Uhrzeit", exp=True), TF("se_temp", "Temp", exp=True)]),
        DD("se_zapf", "Zapfstelle (Eis)", ["Eismaschine"], "Eismaschine", exp=True), ft.Row([CB("se_cb_eiswanne", "Eiswanne/Schöpfprobe"), CB("se_cb_fallprobe", "Fallprobe", True)]),
        TF("se_tech_sonst", "Sonstiges (Technik)", exp=True), DD("se_desinf", "Desinfektion", ["Abflammen", "Sprühdesinfektion", "ohne Desinfektion"], "ohne Desinfektion", exp=True),
        CB("se_cb_ozon", "Ozonsterilisator"), TF("se_auff_sonst", "Sonstiges (Auffälligkeiten)", exp=True),
        TF("se_inhalt", "Inhalt", "ca. 1000ml", exp=True), DD("se_verpackung", "Verpackung", ["steriler Probenbeutel"], "steriler Probenbeutel", exp=True),
        DD("se_entnahmeort", "Entnahmeort", ["Fischabteilung-Eismaschine", "Metzgerei", "Produktionsraum"], "Fischabteilung-Eismaschine", exp=True), DD("se_bemerkung", "Bemerkungen", ["Bitte eingeben", "Keine Besonderheiten"], "Bitte eingeben", exp=True)
    ], scroll=ft.ScrollMode.AUTO)

    def make_hfm_block(prefix, name, is_bio=False):
        return ft.Column([
            CB(f"{prefix}_cb", name), DD(f"{prefix}_entnahmeort", "Entnahmeort", opts_ort, "Kühlraum", exp=True),
            TF(f"{prefix}_produkt", "Produkt", exp=True) if prefix in ["hfm_fzs", "hfm_fzg"] else ft.Container(),
            TF(f"{prefix}_marinade", "Marinade", exp=True) if prefix in ["hfm_fzs", "hfm_fzg"] else ft.Container(),
            ft.Text("Herstelldatum", color="white"), ft.Row([TF(f"{prefix}_h_t", "Tag", dp[0] if len(dp)>0 else "", w=50), TF(f"{prefix}_h_m", "Mon", dp[1] if len(dp)>1 else "", w=50), TF(f"{prefix}_h_j", "Jahr", dp[2] if len(dp)>2 else "2026", w=70)]),
            TF(f"{prefix}_inhalt", "Inhalt", "jeweils ca. 200 g" if prefix in ["hfm_hack", "hfm_bio"] else "ca. 200 g", exp=True),
            DD(f"{prefix}_verpackung", "Verpackung", opts_verp, "steriler Probenbeutel", exp=True),
            TF(f"{prefix}_lief_schwein", "Lieferant Schwein", exp=True) if prefix in ["hfm_hack", "hfm_bio"] else TF(f"{prefix}_lief", "Lieferant Rohware", exp=True),
            TF(f"{prefix}_lief_rind", "Lieferant Rind", exp=True) if prefix in ["hfm_hack", "hfm_bio"] else ft.Container(),
            ft.Text("MHD Schwein" if prefix in ["hfm_hack", "hfm_bio"] else "MHD Rohware", color="white"),
            ft.Row([TF(f"{prefix}_mhd_s_t", "Tag", w=50), TF(f"{prefix}_mhd_s_m", "Mon", w=50), TF(f"{prefix}_mhd_s_j", "Jahr", w=70)]) if prefix in ["hfm_hack", "hfm_bio"] else ft.Row([TF(f"{prefix}_mhd_t", "Tag", w=50), TF(f"{prefix}_mhd_m", "Mon", w=50), TF(f"{prefix}_mhd_j", "Jahr", w=70)]),
            ft.Text("MHD Rind", color="white") if prefix in ["hfm_hack", "hfm_bio"] else ft.Container(),
            ft.Row([TF(f"{prefix}_mhd_r_t", "Tag", w=50), TF(f"{prefix}_mhd_r_m", "Mon", w=50), TF(f"{prefix}_mhd_r_j", "Jahr", w=70)]) if prefix in ["hfm_hack", "hfm_bio"] else ft.Container(),
            DD(f"{prefix}_charge_schwein", "Charge Schwein", opts_s, "Bitte eingeben", exp=True) if prefix in ["hfm_hack", "hfm_bio"] else DD(f"{prefix}_charge", "Charge Rohware", opts_s if prefix != "hfm_fzg" else opts_g, "Bitte eingeben", exp=True),
            DD(f"{prefix}_charge_rind", "Charge Rind", opts_r, "Bitte eingeben", exp=True) if prefix in ["hfm_hack", "hfm_bio"] else ft.Container(),
            TF(f"{prefix}_temp", "Temp", exp=True), DD(f"{prefix}_bemerkung", "Bemerkung", ["Bitte eingeben", "Keine Besonderheiten"], "Bitte eingeben", exp=True)
        ], scroll=ft.ScrollMode.AUTO)

    hfm_ui = ft.Tabs(tabs=[
        ft.Tab(text="Hack", content=make_hfm_block("hfm_hack", "Hack gemischt")), ft.Tab(text="Mett", content=make_hfm_block("hfm_mett", "Schweinemett")),
        ft.Tab(text="FZS", content=make_hfm_block("hfm_fzs", "FZ Schwein")), ft.Tab(text="FZG", content=make_hfm_block("hfm_fzg", "FZ Geflügel")),
        ft.Tab(text="Bio", content=make_hfm_block("hfm_bio", "Bio-Hack", True))
    ], expand=True)

    og_ui_rows = [CB("og_cb", "Obst-/Gemüse Convenience")]
    for i in range(1, 6):
        idx = f"{i:02d}"
        og_ui_rows.extend([
            ft.Text(f"Teilprobe {i}", color="white", weight="bold"), TF(f"og_name_{idx}", "Name", exp=True), DD(f"og_ort_{idx}", "Entnahmeort", opts_ort + ["Saftpresse", "Salatbar"], exp=True),
            ft.Text("Herstelldatum", color="white54", size=10), ft.Row([TF(f"og_h_t_{idx}", "T", w=50), TF(f"og_h_m_{idx}", "M", w=50), TF(f"og_h_j_{idx}", "J", w=70)]),
            ft.Text("Verbrauchsdatum", color="white54", size=10), ft.Row([TF(f"og_v_t_{idx}", "T", w=50), TF(f"og_v_m_{idx}", "M", w=50), TF(f"og_v_j_{idx}", "J", w=70)]),
            TF(f"og_inhalt_{idx}", "Inhalt", exp=True), DD(f"og_verp_{idx}", "Verpackung", opts_verp, exp=True), TF(f"og_temp_{idx}", "Temp", exp=True), ft.Divider(color="white24")
        ])
    og_ui = ft.Column(og_ui_rows, scroll=ft.ScrollMode.AUTO)

    def make_okz(prefix, count, cb_label, defaults, opts_obj):
        r = [CB(f"{prefix}_cb", cb_label), DD(f"{prefix}_bemerkung", "Bemerkung", ["Bitte eingeben", "Keine Besonderheiten"], "Bitte eingeben", exp=True)]
        if prefix == "og_okz": r.append(TF(f"{prefix}_anmerkung", "Anmerkung", exp=True))
        for i in range(1, count + 1):
            idx = f"{i:02d}"
            r.append(ft.Column([
                ft.Text(f"Probe {i}", color="white", weight="bold"),
                ft.Row([DD(f"{prefix}_status_{idx}", "Status", ["R+D", "R", "P", "-"], "R+D", exp=True), DD(f"{prefix}_objekt_{idx}", "Objekt", opts_obj, defaults.get(i, ""), exp=True)]),
                DD(f"{prefix}_ort_{idx}", "Ort", ["Kühlraum", "Produktionsbereich", "Theke", "Fischabteilung", "Metzgerei"], exp=True),
                ft.Row([CB(f"{prefix}_abklatsch_{idx}", "Abklatsch", True), CB(f"{prefix}_tupfer_{idx}", "Tupfer", False)]), ft.Divider(color="white24")
            ]))
        return ft.Column(r, scroll=ft.ScrollMode.AUTO)

    se_okz_ui = make_okz("se_okz", 3, "Abklatschproben Scherbeneis", {1:"Eiswanne innen rechts", 2:"Eiswanne innen links", 3:"Auswurfrohr"}, ["Eiswanne innen rechts", "Eiswanne innen links", "Auswurfrohr", "Eisschaufel", "Eiswanne", "Eismaschine innen", "Klappe/Deckel", "Sonstiges"])
    hfm_okz_ui = make_okz("okz", 10, "Abklatschproben HFM", {1:"Fleischwolf-Auflage", 2:"Fleischwolf-Auswurf", 3:"Thekenschale", 4:"Hackstecher", 5:"Messer", 6:"Schneidebrett", 7:"Wand am Fleischwolf"}, ["Fleischwolf-Auflage", "Fleischwolf-Lochscheibe", "Fleischwolf-Auswurf", "Fleischwolf-Spirale", "Wand am Fleischwolf", "Hackstecher", "Schaufel", "Thekenschale", "Messer", "Schneidebrett", "Auflage Knochensäge", "Tisch", "Flesichwanne", "Kühlhausgriff", "Schüssel", "Seifenspender"])
    og_okz_ui = make_okz("og_okz", 6, "Abklatschproben OG", {1:"Schneidebrett", 2:"Messer", 3:"Waagenauflage", 4:"Schüssel", 5:"Löffel"}, ["Schneidebrett", "Messer", "Saftpresse Auffanggitter", "Saftpresse Rückwand", "Saftpresse Auslass", "Waagenauflage", "Schüssel", "Löffel", "GN-Behälter"])
    okz_tabs = ft.Tabs(tabs=[ft.Tab(text="SE OKZ", content=se_okz_ui), ft.Tab(text="HFM OKZ", content=hfm_okz_ui), ft.Tab(text="OG OKZ", content=og_okz_ui)], expand=True)

    status_text = ft.Text("", color="yellow", weight="bold")

    def speichere_tour(e):
        try:
            status_text.value = "⏳ Erstelle Bericht..."; page.update()
            d_neu = {k: v.value for k, v in ctrls.items()}
            
            d_neu["datum"] = f"{d_neu.get('tag','')}.{d_neu.get('mon','')}.{d_neu.get('jahr','')}"
            if markt_index is None: maerkte.append(d_neu)
            else: maerkte[markt_index] = d_neu
            speichere_maerkte(maerkte)

            pfad = erstelle_bericht(d_neu)
            status_text.value = f"✅ PDF erstellt!\nOrdner: {os.path.basename(os.path.dirname(pfad))}"; status_text.color = "green"
        except Exception as ex:
            status_text.value = f"❌ Fehler: {str(ex)}"; status_text.color = "red"
        page.update()

    ansicht.controls.clear()
    ansicht.controls.extend([
        ft.Text("TOUR BEARBEITEN", size=20, weight="bold", color="white"),
        ft.Tabs(selected_index=0, expand=True, tabs=[
            ft.Tab(text="STAMM", content=stamm_ui), ft.Tab(text="TW/SE", content=tw_se_ui),
            ft.Tab(text="HFM", content=hfm_ui), ft.Tab(text="OG", content=og_ui), ft.Tab(text="OKZ", content=okz_tabs)
        ]),
        ft.Divider(), status_text,
        ft.Row([
            ft.ElevatedButton("📄 SPEICHERN & PDF", on_click=speichere_tour, bgcolor="blue", color="white", expand=True),
            ft.ElevatedButton("🔙 ZURÜCK", on_click=lambda _: zeige_dashboard(), bgcolor="red", color="white")
        ])
    ])
    page.update()