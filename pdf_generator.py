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
    w = str(wert).strip().replace("°C", "").replace("°", "").replace(" C", "").replace("C", "").strip().replace(".", ",")
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
    try:
        os.makedirs(t_ordner, exist_ok=True)
    except Exception:
        pass
    return t_ordner

# --- DATEN-MAPPING (Die Brücke zwischen App und PDF) ---

def sammle_alle_daten(daten):
    w = {}

    def get_val(key, default=""):
        v = daten.get(key)
        if v is None or str(v).strip() == "": return str(default)
        return str(v)

    def check(key, pdf_id):
        w[pdf_id] = bool(daten.get(key))

    # --- STAMMDATEN ---
    w["cal_templateLaborderprobenahmeDatum"] = get_val("datum")
    w["tf_0000_00_ZS-1408"] = get_val("marktnummer")
    w["tf_0000_00_ZS-001870"] = get_val("adresse") 
    w["dd_0000_00_ZS-1566"] = get_val("auftraggeber", "03509 - REWE Hackfleischmonitoring")
    w["dd_0000_00_ZS-002314"] = get_val("mitarbeiter_name")
    w["dd_0000_00_ZS-002315"] = get_val("typ_probenahme", "Standard")
    w["tf_0000_00_ZS-002000"] = get_val("auftragsnummer")
    w["dd_0000_00_ZS-001796"] = get_val("bemerkung")

    # --- TRINKWASSER ---
    check("tw_kalt", "cb_0001_00")
    w["tf_0001_00"] = "Trinkwasser kalt"
    w["tf_0001_00_probenahmeUhrzeit"] = formatiere_uhrzeit(get_val("tw_zeit"))
    w["tf_0001_00_ZS-1441"] = formatiere_temperatur(get_val("tw_temp"))
    w["tf_0001_00_PE_ZS-1514"] = formatiere_temperatur(get_val("tw_tempkonst"))
    w["dd_0001_00_PE_ZS-002255"] = get_val("tw_desinf", "Sprühdesinfektion")
    w["dd_0001_00_PE_ZS-002318"] = get_val("tw_zapf", "Spülbecken")
    
    check("tw_cb_pn", "cb_0001_00_PE_ZS-002304_PN-Hahn")
    check("tw_cb_ein", "cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur")
    check("tw_cb_zwei", "cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur")
    check("tw_cb_ein_g", "cb_0001_00_PE_ZS-002304_ Eingriff-Armmatur")
    check("tw_cb_sensor", "cb_0001_00_PE_ZS-002304_ Sensor-Armatur")
    check("tw_cb_eck", "cb_0001_00_PE_ZS-002304_ Eckventil")
    check("tw_cb_knie", "cb_0001_00_PE_ZS-002304_ Armatur mit Kniebestätigung")
    w["cb_0001_00_PE_ZS-002304_Sonstiges"] = get_val("tw_zapf_sonst")

    w["dd_0001_00_PE_ZS-001948"] = get_val("tw_inaktiv", "Na-Thiosulfat")
    w["dd_0001_00_PE_ZS-002305_Farbe"] = get_val("tw_kurz1", "1 - nicht wahrnehmbar")
    w["dd_0001_00_PE_ZS-002305_ Trübung"] = get_val("tw_kurz2", "1 - nicht wahrnehmbar")
    w["dd_0001_00_PE_ZS-002305_ Bodensatz"] = get_val("tw_kurz3", "1 - nicht wahrnehmbar")
    w["dd_0001_00_PE_ZS-002305_ Geruch"] = get_val("tw_kurz4", "1 - nicht wahrnehmbar")
    
    check("tw_auff_ja", "cb_0001_00_PE_ZS-1268_ja")
    check("tw_auff_nein", "cb_0001_00_PE_ZS-1268_ nein")
    check("tw_auff_perlator", "cb_0001_00_PE_ZS-1268_ Perlator nicht entfernbar")
    check("tw_auff_kalk", "cb_0001_00_PE_ZS-1268_ Starke Verkalkung")
    check("tw_auff_verbrueh", "cb_0001_00_PE_ZS-1268_ Armatur mit Verbrühschutz")
    check("tw_auff_durchlauf", "cb_0001_00_PE_ZS-1268_ Durchlauferhitzer")
    check("tw_auff_unterbau", "cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]")
    check("tw_auff_eckventil", "cb_0001_00_PE_ZS-1268_ Eckventil warm/kalt geschlossen")
    check("tw_auff_unmoeglich", "cb_0001_00_PE_ZS-1268_ nicht möglich")
    check("tw_auff_dusche", "cb_0001_00_PE_ZS-1268_ Entnahme aus der Dusche")
    check("tw_auff_handbrause", "cb_0001_00_PE_ZS-1268_ Handbrause")
    check("tw_auff_sonstiges", "cb_0001_00_PE_ZS-1268_ Sonstiges")
    w["cb_0001_00_PE_ZS-1268_Sonstiges"] = get_val("tw_auff_sonst_text")

    w["dd_0001_00_PE_ZS-002317"] = get_val("tw_zweck", "DIN EN ISO 19458 Zweck B")
    w["tf_0001_00_ZS-1215"] = get_val("tw_inhalt", "ca. 500 ml")
    w["dd_0001_00_ZS-001798"] = get_val("tw_verpackung", "500ml Kunststoff-Flasche mit Natriumthiosulfat")
    w["dd_0001_00_ZS-001799"] = get_val("tw_entnahmeort", "Metzgerei")
    w["dd_0001_00_ZS-001796"] = get_val("tw_bemerkung_2")

    # --- SCHERBENEIS ---
    check("se_kalt", "cb_0002_00")
    w["tf_0002_00"] = "Scherbeneis Eigenkontrolle"
    w["tf_0002_00_probenahmeUhrzeit"] = formatiere_uhrzeit(get_val("se_zeit"))
    w["dd_0002_00_PE_ZS-002319"] = get_val("se_zapf", "Eismaschine")
    check("se_cb_eiswanne", "cb_0002_00_PE_ZS-002304_Eiswanne")
    check("se_cb_fallprobe", "cb_0002_00_PE_ZS-002304_ Fallprobe")
    w["cb_0002_00_PE_ZS-002304_Sonstiges"] = get_val("se_tech_sonst")
    w["dd_0002_00_PE_ZS-002255"] = get_val("se_desinf", "ohne Desinfektion")
    check("se_cb_ozon", "cb_0002_00_PE_ZS-1268_Ozonsterilisator")
    w["cb_0002_00_PE_ZS-1268_Sonstiges"] = get_val("se_auff_sonst")
    w["tf_0002_00_ZS-1215"] = get_val("se_inhalt", "ca. 1000ml")
    w["dd_0002_00_ZS-001798"] = get_val("se_verpackung", "steriler Probenbeutel")
    w["dd_0002_00_ZS-001799"] = get_val("se_entnahmeort", "Fischabteilung-Eismaschine")
    w["tf_0002_00_ZS-1441"] = formatiere_temperatur(get_val("se_temp"))
    w["dd_0002_00_ZS-001796"] = get_val("se_bemerkung")

    # --- HACKFLEISCH ---
    check("hfm_hack_cb", "cb_0004_00")
    w["tf_0004_00"] = "Hackfleisch gemischt"
    w["dd_0004_00_ZS-001799"] = get_val("hfm_hack_entnahmeort", "Kühlraum")
    w["tf_0004_00_ZS-1215"] = get_val("hfm_hack_inhalt", "jeweils ca. 200 g")
    w["dd_0004_00_ZS-001798"] = get_val("hfm_hack_verpackung", "steriler Probenbeutel")
    
    hack_herst = get_val("hfm_hack_herstelldatum")
    if hack_herst.replace(".", "").strip():
        w["cal_0004_00_ZS-001810"] = hack_herst
        w["tf_0004_00_ZS-001810"] = hack_herst

    l_s = get_val("hfm_hack_lief_schwein")
    if l_s: w["tf_0004_00_ZS-1209_Schweinefleisch: XXX"] = f"Schweinefleisch: {l_s}"
    l_r = get_val("hfm_hack_lief_rind")
    if l_r: w["tf_0004_00_ZS-1209_Rindfleisch: XXX"] = f"Rindfleisch: {l_r}"
    
    m_r = get_val("hfm_hack_mhd_rind")
    if m_r.replace(".", "").strip(): w["tf_0004_00_ZS-001835_Rindfleisch: XXX"] = f"Rindfleisch: {m_r}"
    m_s = get_val("hfm_hack_mhd_schwein")
    if m_s.replace(".", "").strip(): w["tf_0004_00_ZS-001835_Schweinefleisch: XXX"] = f"Schweinefleisch: {m_s}"
    
    c_s = get_val("hfm_hack_charge_schwein")
    if c_s: w["tf_0004_00_ZS-002081_Schweinefleisch: XXX"] = f"Schweinefleisch: {c_s}"
    c_r = get_val("hfm_hack_charge_rind")
    if c_r: w["tf_0004_00_ZS-002081_Rindfleisch: XXX"] = f"Rindfleisch: {c_r}"
    
    w["tf_0004_00_ZS-1441"] = formatiere_temperatur(get_val("hfm_hack_temp"))
    w["dd_0004_00_ZS-001796"] = get_val("hfm_hack_check_bemerkung")

    # --- METT ---
    check("hfm_mett_cb", "cb_0006_00")
    w["tf_0006_00"] = "gewürztes Schweinemett"
    w["dd_0006_00_ZS-001799"] = get_val("hfm_mett_entnahmeort", "Kühlraum")
    w["cal_0006_00_ZS-001810"] = get_val("hfm_mett_herstelldatum")
    w["tf_0006_00_ZS-1215"] = get_val("hfm_mett_inhalt", "ca. 200 g")
    w["dd_0006_00_ZS-001798"] = get_val("hfm_mett_verpackung", "steriler Probenbeutel")
    w["tf_0006_00_ZS-1209"] = get_val("hfm_mett_lief")
    w["tf_0006_00_ZS-002081"] = get_val("hfm_mett_charge")
    w["tf_0006_00_ZS-1441"] = formatiere_temperatur(get_val("hfm_mett_temp"))
    w["dd_0006_00_ZS-001796"] = get_val("hfm_mett_bemerkung")
    
    extra_mett = get_val("hfm_mett_mhd")
    if extra_mett.replace(".", "").strip(): w["tf_0006_00_ZS-001835"] = extra_mett

    # --- FZS Schwein ---
    check("hfm_fzs_cb", "cb_0008_00")
    w["tf_0008_00"] = "Fleischzubereitung Schwein"
    p, m = get_val("hfm_fzs_produkt"), get_val("hfm_fzs_marinade")
    w['tf_0008_00_ Produkt "Marinade"'] = f'{p} "{m}"' if p and m else p + m
    w["dd_0008_00_ZS-001799"] = get_val("hfm_fzs_entnahmeort", "Kühlraum")
    w["cal_0008_00_ZS-001810"] = get_val("hfm_fzs_herstelldatum")
    w["tf_0008_00_ZS-1215"] = get_val("hfm_fzs_inhalt", "ca. 200 g")
    w["dd_0008_00_ZS-001798"] = get_val("hfm_fzs_verpackung", "steriler Probenbeutel")
    w["tf_0008_00_ZS-1209"] = get_val("hfm_fzs_lief")
    w["tf_0008_00_ZS-002081"] = get_val("hfm_fzs_charge")
    w["tf_0008_00_ZS-1441"] = formatiere_temperatur(get_val("hfm_fzs_temp"))
    w["dd_0008_00_ZS-001796"] = get_val("hfm_fzs_bemerkung")
    m_fzs = get_val("hfm_fzs_mhd")
    if m_fzs.replace(".", "").strip(): w["tf_0008_00_ZS-001835"] = m_fzs

    # --- FZG Geflügel ---
    check("hfm_fzg_cb", "cb_0007_00")
    w["tf_0007_00"] = "Fleischzubereitung Geflügel"
    p, m = get_val("hfm_fzg_produkt"), get_val("hfm_fzg_marinade")
    w['tf_0007_00_ Produkt "Marinade"'] = f'{p} "{m}"' if p and m else p + m
    w["dd_0007_00_ZS-001799"] = get_val("hfm_fzg_entnahmeort", "Kühlraum")
    w["cal_0007_00_ZS-001810"] = get_val("hfm_fzg_herstelldatum")
    w["tf_0007_00_ZS-1215"] = get_val("hfm_fzg_inhalt", "ca. 200 g")
    w["dd_0007_00_ZS-001798"] = get_val("hfm_fzg_verpackung", "steriler Probenbeutel")
    w["tf_0007_00_ZS-1209"] = get_val("hfm_fzg_lief")
    w["tf_0007_00_ZS-002081"] = get_val("hfm_fzg_charge")
    w["tf_0007_00_ZS-1441"] = formatiere_temperatur(get_val("hfm_fzg_temp"))
    w["dd_0007_00_ZS-001796"] = get_val("hfm_fzg_bemerkung")
    m_fzg = get_val("hfm_fzg_mhd")
    if m_fzg.replace(".", "").strip(): w["tf_0007_00_ZS-001835"] = m_fzg

    # --- ABKLATSCHPROBEN HFM ---
    def map_abklatsch(prefix, start_idx, num_items):
        for i in range(1, num_items + 1):
            pdf_idx = f"{start_idx + i - 1:02d}" 
            app_idx = f"{i:02d}" 
            
            w[f"dd_{prefix}_{pdf_idx}_ZS-001880"] = get_val(f"{prefix}_status_{app_idx}", "R+D")
            obj = get_val(f"{prefix}_objekt_{app_idx}")
            if obj: w[f"dd_{prefix}_{pdf_idx}_ZS-1419"] = obj
            w[f"dd_{prefix}_{pdf_idx}_ZS-001792"] = get_val(f"{prefix}_ort_{app_idx}")
            
            check(f"{prefix}_abklatsch_{app_idx}", f"cb_{prefix}_{pdf_idx}_ZS-002294")
            check(f"{prefix}_tupfer_{app_idx}", f"cb_{prefix}_{pdf_idx}_ZS-002295")

    check("hfm_okz_cb", "cb_0010_00")
    w["tf_0010_00"] = "Abklatschproben HFM"
    w["dd_0010_00_ZS-001796"] = get_val("hfm_abklatsch_bemerkung")
    map_abklatsch("0010", 1, 10)

    # --- CONVENIENCE / PROBEN ---
    check("og_cb", "cb_0009_00")
    w["tf_0009_00"] = "Obst-/Gemüse Convenience"
    for i in range(1, 6):
        idx = f"{i:02d}" 
        val = get_val(f"og_name_{idx}")
        
        # FIX: Der Reihen-Index wird nun korrekt mit 'idx' übergeben (01, 02, 03...) statt starr '00'!
        if val: 
            w[f"tf_0009_{idx}_ Teilprobe {i}:"] = f"Teilprobe {i}:{val}"
            w[f"tf_0009_{idx}"] = val  # Fallback-ID für geänderte REWE Formularfelder
            
        w[f"dd_0009_{idx}_ZS-001799"] = get_val(f"og_ort_{idx}")
        w[f"cal_0009_{idx}_ZS-001810"] = get_val(f"og_herst_{idx}")
        w[f"tf_0009_{idx}_ZS-1527"] = get_val(f"og_verb_{idx}")
        w[f"tf_0009_{idx}_ZS-1215"] = get_val(f"og_inhalt_{idx}")
        w[f"dd_0009_{idx}_ZS-001798"] = get_val(f"og_verp_{idx}")
        w[f"tf_0009_{idx}_ZS-1441"] = formatiere_temperatur(get_val(f"og_temp_{idx}"))

    # --- CONVENIENCE OKZ ---
    check("og_abklatsch_cb", "cb_0011_00")
    w["tf_0011_00"] = "Obst-Gemüse Abklatschproben"
    w["dd_0011_00_ZS-001796"] = get_val("og_abklatsch_bemerkung_1")
    w["Anmerkung"] = get_val("og_abklatsch_bemerkung_2")
    map_abklatsch("0011", 1, 5)

    return w

# --- HAUPT-FUNKTION ---

def erstelle_bericht(daten):
    master_pfad = os.path.join("assets", "Rewe_PDF.pdf")
    neu_pfad = os.path.join("assets", "hfm_neu.pdf")
    
    if not os.path.exists(master_pfad): return f"FEHLER: {master_pfad} fehlt!"

    zeit_jetzt = datetime.datetime.now().strftime('%H-%M-%S')
    datum_heute = datetime.datetime.now().strftime('%Y-%m-%d')
    dateiname = f"REWE_{daten.get('marktnummer', 'Unbekannt')}_{datum_heute}_{zeit_jetzt}.pdf"
    
    ziel_pfad = os.path.join(get_tages_ordner(), dateiname)

    reader_master = PdfReader(master_pfad)
    writer = PdfWriter()
    
    if os.path.exists(neu_pfad):
        reader_neu = PdfReader(neu_pfad)
        writer.append(reader_master, pages=list(range(0, 5)))
        writer.append(reader_neu)
        writer.append(reader_master, pages=list(range(5, len(reader_master.pages))))
    else:
        writer.append(reader_master)
    
    if "/AcroForm" in writer.root_object:
        writer.root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})

    mapping = sammle_alle_daten(daten)
    text_mapping = {k: str(v) for k, v in mapping.items() if not isinstance(v, bool)}
    
    for page in writer.pages:
        writer.update_page_form_field_values(page, text_mapping)
        
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                current_obj = annot
                f_id = None
                
                while current_obj:
                    if "/T" in current_obj:
                        f_id = clean_id(str(current_obj["/T"]).strip("()"))
                        break
                    if "/Parent" in current_obj: 
                        current_obj = current_obj["/Parent"].get_object()
                    else: 
                        break
                if not f_id: continue

                # HAKEN / CHECKBOXEN
                if f_id in mapping and isinstance(mapping[f_id], bool):
                    val = mapping[f_id]
                    on_state = NameObject("/Yes")
                    if "/AP" in annot and "/N" in annot["/AP"]:
                        for k in annot["/AP"]["/N"].keys():
                            if k != "/Off": on_state = NameObject(k); break
                    state = on_state if val else NameObject("/Off")
                    
                    current_obj.update({NameObject("/V"): state})
                    annot.update({NameObject("/AS"): state})
                
                # TEXTFELDER FALLBACK
                elif f_id in mapping and not isinstance(mapping[f_id], bool):
                    val = str(mapping[f_id])
                    if val and val != "..":
                        current_obj.update({NameObject("/V"): create_string_object(val)})
                        if "/AP" in annot:
                            del annot["/AP"]

    with open(ziel_pfad, "wb") as f: writer.write(f)
    print(f"✅ Bericht erstellt: {ziel_pfad}")
    return ziel_pfad
