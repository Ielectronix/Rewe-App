import os
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, create_string_object, BooleanObject

# --- HELFER-FUNKTIONEN ---

def formatiere_uhrzeit(wert):
    if not wert or str(wert).strip() == "": return ""
    w = str(wert).strip().lower().replace("uhr", "").replace(" ", "").strip()
    if len(w) == 4 and w.isdigit(): w = f"{w[:2]}:{w[2:]}"
    elif len(w) == 2 and w.isdigit(): w = f"{w}:00"
    return f"{w} Uhr"

def formatiere_temperatur(wert):
    if not wert or str(wert).strip() == "": return ""
    w = str(wert).strip().replace("°C", "").replace("°", "").strip().replace(".", ",")
    if not w.startswith("+") and not w.startswith("-"): w = f"+ {w}"
    return f"{w} °C"

def clean_id(raw_id):
    return str(raw_id).replace("\r", "").replace("\n", "").replace("\t", "").strip()

# --- ORDNER-LOGIK ---

def get_all_rewe_bases():
    if os.name == 'nt':
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        return [os.path.join(desktop, 'MeineApp'), os.path.join(desktop, 'Rewe_Monitoring')]
    return ["/storage/emulated/0/Download/Rewe_Monitoring", "/storage/emulated/0/Download"]

def create_base_folder():
    for base in get_all_rewe_bases() + [os.getcwd()]:
        try:
            if not os.path.exists(base): os.makedirs(base, exist_ok=True)
            return base
        except: continue
    return os.getcwd()

def get_tages_ordner():
    t_ordner = os.path.join(create_base_folder(), datetime.datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(t_ordner, exist_ok=True)
    return t_ordner

# --- DATEN-MAPPING ---

def sammle_alle_daten(daten):
    w = {}
    h_yes = NameObject('/Yes')
    h_j = NameObject('/j')

    # --- STAMMDATEN ---
    w["cal_templateLaborderprobenahmeDatum"] = daten.get("datum", "")
    w["tf_0000_00_ZS-1408"] = daten.get("marktnummer", "")
    w["tf_0000_00_ZS-001870"] = daten.get("adresse", "") 
    w["dd_0000_00_ZS-1566"] = daten.get("auftraggeber", "")
    w["dd_0000_00_ZS-002314"] = daten.get("mitarbeiter_name", "")
    w["dd_0000_00_ZS-002315"] = daten.get("typ_probenahme", "")
    w["tf_0000_00_ZS-002000"] = daten.get("auftragsnummer", "")
    w["dd_0000_00_ZS-001796"] = daten.get("bemerkung", "")

    # --- TRINKWASSER KALT (Seite 2, 3, 4) ---
    if daten.get("tw_kalt"): w["cb_0001_00"] = h_yes
    # Werte werden IMMER eingetragen, auch wenn Haken oben fehlt!
    w["tf_0001_00_probenahmeUhrzeit"] = formatiere_uhrzeit(daten.get("tw_zeit", ""))
    w["tf_0001_00_ZS-1441"] = formatiere_temperatur(daten.get("tw_temp", ""))
    w["tf_0001_00_PE_ZS-1514"] = formatiere_temperatur(daten.get("tw_tempkonst", ""))
    w["dd_0001_00_PE_ZS-002255"] = daten.get("tw_desinf", "")
    w["dd_0001_00_PE_ZS-002318"] = daten.get("tw_zapf", "")
    
    if daten.get("tw_cb_pn"): w["cb_0001_00_PE_ZS-002304_PN-Hahn"] = h_yes
    if daten.get("tw_cb_ein"): w["cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur"] = h_yes
    if daten.get("tw_cb_zwei"): w["cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur"] = h_yes
    if daten.get("tw_cb_eingriff"): w["cb_0001_00_PE_ZS-002304_ Eingriff-Armmatur"] = h_yes
    if daten.get("tw_cb_sensor"): w["cb_0001_00_PE_ZS-002304_ Sensor-Armatur"] = h_yes
    if daten.get("tw_cb_eckventil"): w["cb_0001_00_PE_ZS-002304_ Eckventil"] = h_yes
    if daten.get("tw_cb_knie"): w["cb_0001_00_PE_ZS-002304_ Armatur mit Kniebestätigung"] = h_yes
    w["cb_0001_00_PE_ZS-002304_Sonstiges"] = daten.get("tw_zapf_sonstiges_text", "")

    # Auffälligkeiten & Sensorik (Seite 3)
    w["dd_0001_00_PE_ZS-001948"] = daten.get("tw_inaktivierung", "")
    w["dd_0001_00_PE_ZS-002305_Farbe"] = daten.get("tw_farbe", "")
    w["dd_0001_00_PE_ZS-002305_ Trübung"] = daten.get("tw_truebung", "")
    w["dd_0001_00_PE_ZS-002305_ Bodensatz"] = daten.get("tw_bodensatz", "")
    w["dd_0001_00_PE_ZS-002305_ Geruch"] = daten.get("tw_geruch", "")
    
    if daten.get("tw_auff_ja"): w["cb_0001_00_PE_ZS-1268_ja"] = h_yes
    if daten.get("tw_auff_nein"): w["cb_0001_00_PE_ZS-1268_ nein"] = h_yes
    if daten.get("tw_auff_perlator"): w["cb_0001_00_PE_ZS-1268_ Perlator nicht entfernbar"] = h_yes
    if daten.get("tw_auff_kalk"): w["cb_0001_00_PE_ZS-1268_ Starke Verkalkung"] = h_yes
    if daten.get("tw_auff_verbrueh"): w["cb_0001_00_PE_ZS-1268_ Armatur mit Verbrühschutz"] = h_yes
    if daten.get("tw_auff_durchlauf"): w["cb_0001_00_PE_ZS-1268_ Durchlauferhitzer"] = h_yes
    if daten.get("tw_auff_unterbau"): w["cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]"] = h_yes
    if daten.get("tw_auff_eckventil"): w["cb_0001_00_PE_ZS-1268_ Eckventil warm/kalt geschlossen"] = h_yes
    if daten.get("tw_auff_unmoeglich"): w["cb_0001_00_PE_ZS-1268_ nicht möglich"] = h_yes
    if daten.get("tw_auff_dusche"): w["cb_0001_00_PE_ZS-1268_ Entnahme aus der Dusche"] = h_yes
    if daten.get("tw_auff_handbrause"): w["cb_0001_00_PE_ZS-1268_ Handbrause"] = h_yes
    
    # FIX FÜR DAS SONSTIGES-FELD: Checkbox hat Leerzeichen, Textfeld nicht!
    if daten.get("tw_auff_sonstiges"): w["cb_0001_00_PE_ZS-1268_ Sonstiges"] = h_yes
    w["cb_0001_00_PE_ZS-1268_Sonstiges"] = daten.get("tw_auff_sonst_text", "")

    w["dd_0001_00_PE_ZS-002317"] = daten.get("tw_zweck", "")
    w["tf_0001_00_ZS-1215"] = daten.get("tw_inhalt", "")
    w["dd_0001_00_ZS-001798"] = daten.get("tw_verpackung", "")
    w["dd_0001_00_ZS-001799"] = daten.get("tw_entnahmeort", "")
    w["dd_0001_00_ZS-001796"] = daten.get("tw_bemerkung_2", "")

    # --- SCHERBENEIS (Seite 5) ---
    if daten.get("se_kalt"): w["cb_0002_00"] = h_yes
    w["tf_0002_00_probenahmeUhrzeit"] = formatiere_uhrzeit(daten.get("se_zeit", ""))
    w["tf_0002_00_ZS-1441"] = formatiere_temperatur(daten.get("se_temp", ""))
    w["dd_0002_00_PE_ZS-002319"] = daten.get("se_zapf", "")
    if daten.get("se_cb_eiswanne"): w["cb_0002_00_PE_ZS-002304_Eiswanne"] = h_yes
    if daten.get("se_cb_fallprobe"): w["cb_0002_00_PE_ZS-002304_ Fallprobe"] = h_yes
    w["cb_0002_00_PE_ZS-002304_Sonstiges"] = daten.get("se_zapf_sonstiges_text", "")
    w["dd_0002_00_PE_ZS-002255"] = daten.get("se_desinf", "")
    if daten.get("se_cb_ozon"): w["cb_0002_00_PE_ZS-1268_Ozonsterilisator"] = h_yes
    w["cb_0002_00_PE_ZS-1268_Sonstiges"] = daten.get("se_sonstiges_text", "")
    w["tf_0002_00_ZS-1215"] = daten.get("se_inhalt", "")
    w["dd_0002_00_ZS-001798"] = daten.get("se_verpackung", "")
    w["dd_0002_00_ZS-001799"] = daten.get("se_entnahmeort", "")
    w["dd_0002_00_ZS-001796"] = daten.get("se_bemerkung", "")

    # --- HACKFLEISCH (Seite 6) ---
    if daten.get("hfm_hack_cb"): w["cb_0004_00"] = h_yes
    w["dd_0004_00_ZS-001799"] = daten.get("hfm_hack_entnahmeort", "")
    w["cal_0004_00_ZS-001810"] = daten.get("hfm_hack_herstelldatum", "")
    w["tf_0004_00_ZS-1215"] = daten.get("hfm_hack_inhalt", "")
    w["dd_0004_00_ZS-001798"] = daten.get("hfm_hack_verpackung", "")
    w["tf_0004_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_hack_temp", ""))
    w["dd_0004_00_ZS-001796"] = daten.get("hfm_hack_bemerkung", "")
    
    l_r = daten.get("hfm_hack_lief_rind", "").strip()
    if l_r: w["tf_0004_00_ZS-1209_Rindfleisch: XXX"] = f"Rindfleisch: {l_r}"
    c_r = daten.get("hfm_hack_charge_rind", "").strip()
    if c_r: w["tf_0004_00_ZS-002081_Rindfleisch: XXX"] = f"Rindfleisch: {c_r}"
    l_s = daten.get("hfm_hack_lief_schwein", "").strip()
    if l_s: w["tf_0004_00_ZS-1209_Schweinefleisch: XXX"] = f"Schweinefleisch: {l_s}"
    c_s = daten.get("hfm_hack_charge_schwein", "").strip()
    if c_s: w["tf_0004_00_ZS-002081_Schweinefleisch: XXX"] = f"Schweinefleisch: {c_s}"
    
    # MHD Daten jetzt IMMER auswerten
    m_r = daten.get("hfm_hack_mhd_rind", "").strip()
    if m_r and m_r != "..": w["tf_0004_00_ZS-001835_Rindfleisch: XXX"] = f"Rindfleisch: {m_r}"
    m_s = daten.get("hfm_hack_mhd_schwein", "").strip()
    if m_s and m_s != "..": w["tf_0004_00_ZS-001835_Schweinefleisch: XXX"] = f"Schweinefleisch: {m_s}"

    # --- METT (Seite 7) ---
    if daten.get("hfm_mett_cb"): w["cb_0006_00"] = h_yes
    w["dd_0006_00_ZS-001799"] = daten.get("hfm_mett_entnahmeort", "")
    w["cal_0006_00_ZS-001810"] = daten.get("hfm_mett_herstelldatum", "")
    w["tf_0006_00_ZS-1215"] = daten.get("hfm_mett_inhalt", "")
    w["dd_0006_00_ZS-001798"] = daten.get("hfm_mett_verpackung", "")
    w["tf_0006_00_ZS-1209"] = daten.get("hfm_mett_lief", "")
    w["tf_0006_00_ZS-002081"] = daten.get("hfm_mett_charge", "")
    w["tf_0006_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_mett_temp", ""))
    w["dd_0006_00_ZS-001796"] = daten.get("hfm_mett_bemerkung", "")
    m_mett = daten.get("hfm_mett_mhd", "").strip()
    if m_mett and m_mett != "..": w["tf_0006_00_ZS-001835"] = m_mett

    # --- FZS Schwein (Seite 8) ---
    if daten.get("hfm_fzs_cb"): w["cb_0008_00"] = h_yes
    p, m = str(daten.get("hfm_fzs_produkt", "")).strip(), str(daten.get("hfm_fzs_marinade", "")).strip()
    w['tf_0008_00_ Produkt "Marinade"'] = f'{p} "{m}"' if p and m else p + m
    w["dd_0008_00_ZS-001799"] = daten.get("hfm_fzs_entnahmeort", "")
    w["cal_0008_00_ZS-001810"] = daten.get("hfm_fzs_herstelldatum", "")
    w["tf_0008_00_ZS-1215"] = daten.get("hfm_fzs_inhalt", "")
    w["dd_0008_00_ZS-001798"] = daten.get("hfm_fzs_verpackung", "")
    w["tf_0008_00_ZS-1209"] = daten.get("hfm_fzs_lief", "")
    w["tf_0008_00_ZS-002081"] = daten.get("hfm_fzs_charge", "")
    w["tf_0008_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_fzs_temp", ""))
    w["dd_0008_00_ZS-001796"] = daten.get("hfm_fzs_bemerkung", "")
    m_fzs = daten.get("hfm_fzs_mhd", "").strip()
    if m_fzs and m_fzs != "..": w["tf_0008_00_ZS-001835"] = m_fzs

    # --- FZG Geflügel (Seite 9) ---
    if daten.get("hfm_fzg_cb"): w["cb_0007_00"] = h_yes
    p, m = str(daten.get("hfm_fzg_produkt", "")).strip(), str(daten.get("hfm_fzg_marinade", "")).strip()
    w['tf_0007_00_ Produkt "Marinade"'] = f'{p} "{m}"' if p and m else p + m
    w["dd_0007_00_ZS-001799"] = daten.get("hfm_fzg_entnahmeort", "")
    w["cal_0007_00_ZS-001810"] = daten.get("hfm_fzg_herstelldatum", "")
    w["tf_0007_00_ZS-1215"] = daten.get("hfm_fzg_inhalt", "")
    w["dd_0007_00_ZS-001798"] = daten.get("hfm_fzg_verpackung", "")
    w["tf_0007_00_ZS-1209"] = daten.get("hfm_fzg_lief", "")
    w["tf_0007_00_ZS-002081"] = daten.get("hfm_fzg_charge", "")
    w["tf_0007_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_fzg_temp", ""))
    w["dd_0007_00_ZS-001796"] = daten.get("hfm_fzg_bemerkung", "")
    m_fzg = daten.get("hfm_fzg_mhd", "").strip()
    if m_fzg and m_fzg != "..": w["tf_0007_00_ZS-001835"] = m_fzg

    # --- ABKLATSCH HFM (Seite 10-14) ---
    def map_abklatsch(prefix, start_idx, num_items):
        for i in range(1, num_items + 1):
            pdf_idx = f"{start_idx + i - 1:02d}"
            app_idx = str(i)
            status = daten.get(f"{prefix}_status_{app_idx}", "")
            objekt = daten.get(f"{prefix}_objekt_{app_idx}", "")
            ort = daten.get(f"{prefix}_ort_{app_idx}", "")
            if status: w[f"dd_{prefix}_{pdf_idx}_ZS-001880"] = status
            if objekt: w[f"dd_{prefix}_{pdf_idx}_ZS-1419"] = objekt
            if ort: w[f"dd_{prefix}_{pdf_idx}_ZS-001792"] = ort
            if daten.get(f"{prefix}_abklatsch_{app_idx}"): w[f"cb_{prefix}_{pdf_idx}_ZS-002294"] = h_j
            if daten.get(f"{prefix}_tupfer_{app_idx}"): w[f"cb_{prefix}_{pdf_idx}_ZS-002295"] = h_yes

    if daten.get("hfm_abklatsch_cb"): w["cb_0010_00"] = h_yes
    w["dd_0010_00_ZS-001796"] = daten.get("hfm_abklatsch_bemerkung", "")
    map_abklatsch("0010", 1, 10)

    # --- OBST/GEMÜSE (Seite 15-18) ---
    if daten.get("og_cb"): w["cb_0009_00"] = h_yes
    for i in range(1, 6):
        idx = f"{i:02d}" 
        val = daten.get(f"og_name_{idx}", "")
        if val: w[f"tf_0009_00_ Teilprobe {i}:"] = f"Teilprobe {i}:{val}"
        w[f"dd_0009_{idx}_ZS-001799"] = daten.get(f"og_ort_{idx}", "")
        w[f"cal_0009_{idx}_ZS-001810"] = daten.get(f"og_herst_{idx}", "")
        w[f"tf_0009_{idx}_ZS-1527"] = daten.get(f"og_verb_{idx}", "")
        w[f"tf_0009_{idx}_ZS-1215"] = daten.get(f"og_inhalt_{idx}", "")
        w[f"dd_0009_{idx}_ZS-001798"] = daten.get(f"og_verp_{idx}", "")
        w[f"tf_0009_{idx}_ZS-1441"] = formatiere_temperatur(daten.get(f"og_temp_{idx}", ""))

    # --- ABKLATSCH OBST/GEMÜSE (Seite 19-21) ---
    if daten.get("og_abklatsch_cb"): w["cb_0011_00"] = h_yes
    w["dd_0011_00_ZS-001796"] = daten.get("og_abklatsch_bemerkung_1", "")
    w["Anmerkung"] = daten.get("og_abklatsch_bemerkung_2", "")
    map_abklatsch("0011", 1, 5)

    # --- ABKLATSCH SCHERBENEIS (Seite 22-23) ---
    if daten.get("se_abklatsch_cb"): w["cb_0003_00"] = h_yes
    w["dd_0003_00_ZS-001796"] = daten.get("se_abklatsch_bemerkung", "")
    map_abklatsch("0003", 1, 3)

    # --- BIO HACKFLEISCH (Seite 24-25) ---
    if daten.get("hfm_bio_cb"): w["cb_0005_00"] = h_yes
    w["dd_0005_00_ZS-001799"] = daten.get("hfm_bio_entnahmeort", "")
    
    # HIER FEHLTE DAS DATUM:
    w["cal_0005_00_ZS-001810"] = daten.get("hfm_bio_herstelldatum", "")
    
    w["tf_0005_00_ZS-1215"] = daten.get("hfm_bio_inhalt", "")
    w["dd_0005_00_ZS-001798"] = daten.get("hfm_bio_verpackung", "")
    w["tf_0005_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_bio_temp", ""))
    w["dd_0005_00_ZS-001796"] = daten.get("hfm_bio_bemerkung", "")
    
    l_s = daten.get("hfm_bio_lief_schwein", "").strip()
    if l_s: w["tf_0005_00_ZS-1209_Schweinefleisch: XXX"] = f"Schweinefleisch: {l_s}"
    c_s = daten.get("hfm_bio_charge_schwein", "").strip()
    if c_s: w["tf_0005_00_ZS-002081_Schweinefleisch: XXX"] = f"Schweinefleisch: {c_s}"
    
    # HIER FEHLTE DER LIEFERANT UND DIE CHARGE FÜR RIND:
    l_r = daten.get("hfm_bio_lief_rind", "").strip()
    if l_r: w["tf_0005_00_ZS-1209_Rindfleisch: XXX"] = f"Rindfleisch: {l_r}"
    c_r = daten.get("hfm_bio_charge_rind", "").strip()
    if c_r: w["tf_0005_00_ZS-002081_Rindfleisch: XXX"] = f"Rindfleisch: {c_r}"

    m_r = daten.get("hfm_bio_mhd_rind", "").strip()
    if m_r and m_r != "..": w["tf_0005_00_ZS-001835_Rindfleisch: XXX"] = f"Rindfleisch: {m_r}"
    m_s = daten.get("hfm_bio_mhd_schwein", "").strip()
    if m_s and m_s != "..": w["tf_0005_00_ZS-001835_Schweinefleisch: XXX"] = f"Schweinefleisch: {m_s}"

    return w
# --- HAUPT-FUNKTION ---

# --- HAUPT-FUNKTION ---

def erstelle_bericht(daten):
    master_pfad = os.path.join("assets", "Rewe_PDF.pdf")
    neu_pfad = os.path.join("assets", "hfm_neu.pdf")
    
    if not os.path.exists(master_pfad): return f"FEHLER: {master_pfad} fehlt!"
    if not os.path.exists(neu_pfad): return f"FEHLER: {neu_pfad} fehlt!"

    dateiname = f"REWE_{daten.get('marktnummer', 'Unbekannt')}_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf"
    ziel_pfad = os.path.join(get_tages_ordner(), dateiname)

    reader_master = PdfReader(master_pfad)
    reader_neu = PdfReader(neu_pfad)
    writer = PdfWriter()
    
    # ==================================================
    # REPARIERTE PDF-ZUSAMMENFÜHRUNG (Nichts wird mehr gelöscht!)
    # ==================================================
    writer.append(reader_master, pages=list(range(0, 5)))
    writer.append(reader_neu)
    writer.append(reader_master, pages=list(range(5, len(reader_master.pages))))
    # ==================================================
    
    # Formularstruktur kopieren (wichtig für AcroForm Erhalt!)
    if "/AcroForm" not in writer.root_object:
        if "/AcroForm" in reader_master.trailer["/Root"]:
            writer.root_object.update({NameObject("/AcroForm"): reader_master.trailer["/Root"]["/AcroForm"]})
        else:
            writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
            
    writer.root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})

    mapping = sammle_alle_daten(daten)
    text_mapping = {k: str(v) for k, v in mapping.items() if not isinstance(v, NameObject)}

    for page in writer.pages:
        # Sicheres Beschreiben der Textfelder
        writer.update_page_form_field_values(page, text_mapping)

        # ==================================================
        # DER MAGISCHE CHECKBOX-HACKER
        # Liest vollautomatisch aus, welches Wort die Checkbox will (/Yes, /j, etc.)
        # ==================================================
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                if "/T" in annot:
                    f_id = clean_id(str(annot["/T"]).strip("()"))
                    is_checkbox = f_id.startswith("cb_") or f_id.startswith("Check Box")

                    if f_id in mapping and isinstance(mapping[f_id], NameObject):
                        val = mapping[f_id]
                        try:
                            # Wir fragen das PDF: "Welches Wort bedeutet bei dir 'Haken gesetzt'?"
                            if "/AP" in annot and "/N" in annot["/AP"]:
                                for k in annot["/AP"]["/N"].keys():
                                    if k != "/Off": 
                                        val = NameObject(k) 
                                        break
                        except: pass
                        annot.update({NameObject("/V"): val, NameObject("/AS"): val})
                    elif is_checkbox and f_id not in mapping:
                        # Schaltet nur echte Haken aus, lässt Textfelder in Ruhe!
                        # Wenn wir keinen Haken haben, zwingend auf AUS setzen
                        annot.update({NameObject("/V"): NameObject("/Off"), NameObject("/AS"): NameObject("/Off")})

    with open(ziel_pfad, "wb") as f: writer.write(f)
    print(f"✅ Perfekter Kombi-Bericht erstellt: {ziel_pfad}")
    return ziel_pfad
