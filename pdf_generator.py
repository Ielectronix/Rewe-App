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

    # STAMMDATEN
    w["cal_templateLaborderprobenahmeDatum"] = daten.get("datum", "")
    w["tf_0000_00_ZS-1408"] = daten.get("marktnummer", "")
    w["tf_0000_00_ZS-001870"] = daten.get("adresse", "") 
    w["dd_0000_00_ZS-1566"] = daten.get("auftraggeber", "")
    w["dd_0000_00_ZS-002314"] = daten.get("mitarbeiter_name", "")
    w["dd_0000_00_ZS-002315"] = daten.get("typ_probenahme", "")
    w["tf_0000_00_ZS-002000"] = daten.get("auftragsnummer", "")
    w["dd_0000_00_ZS-001796"] = daten.get("bemerkung", "")

    # TRINKWASSER & EIS
    if daten.get("tw_kalt"):
        w["cb_0001_00"] = h_yes
        w["tf_0001_00_probenahmeUhrzeit"] = formatiere_uhrzeit(daten.get("tw_zeit", ""))
        w["tf_0001_00_ZS-1441"] = formatiere_temperatur(daten.get("tw_temp", ""))
        w["tf_0001_00_PE_ZS-1514"] = formatiere_temperatur(daten.get("tw_tempkonst", ""))
        w["dd_0001_00_PE_ZS-002255"] = daten.get("tw_desinf", "")
        w["dd_0001_00_PE_ZS-002318"] = daten.get("tw_zapf", "")
        if daten.get("tw_cb_pn"): w["cb_0001_00_PE_ZS-002304_PN-Hahn"] = h_yes
        if daten.get("tw_cb_ein"): w["cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur"] = h_yes
        if daten.get("tw_cb_zwei"): w["cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur"] = h_yes
        if daten.get("tw_cb_sensor"): w["cb_0001_00_PE_ZS-002304_ Sensor-Armatur"] = h_yes

    if daten.get("se_kalt"):
        w["cb_0002_00"] = h_yes
        w["tf_0002_00_probenahmeUhrzeit"] = formatiere_uhrzeit(daten.get("se_zeit", ""))
        w["tf_0002_00_ZS-1441"] = formatiere_temperatur(daten.get("se_temp", ""))
        w["dd_0002_00_PE_ZS-002319"] = daten.get("se_zapf", "")
        if daten.get("se_cb_eiswanne"): w["cb_0002_00_PE_ZS-002304_Eiswanne"] = h_yes
        if daten.get("se_cb_fallprobe"): w["cb_0002_00_PE_ZS-002304_ Fallprobe"] = h_yes

    # HACKFLEISCH (Seite 6)
    if daten.get("hfm_hack_cb"):
        w["cb_0004_00"] = h_yes
        w["cal_0004_00_ZS-001810"] = daten.get("hfm_hack_herstelldatum", "")
        w["dd_0004_00_ZS-001799"] = daten.get("hfm_hack_entnahmeort", "")
        w["tf_0004_00_ZS-1215"] = daten.get("hfm_hack_inhalt", "")
        w["dd_0004_00_ZS-001798"] = daten.get("hfm_hack_verpackung", "")
        w["tf_0004_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_hack_temp", ""))
        
        l_r = daten.get("hfm_hack_lief_rind", "").strip()
        if l_r: w["tf_0004_00_ZS-1209_Rindfleisch: XXX"] = f"Rindfleisch: {l_r}"
        c_r = daten.get("hfm_hack_charge_rind", "").strip()
        if c_r: w["tf_0004_00_ZS-002081_Rindfleisch: XXX"] = f"Rindfleisch: {c_r}"

        l_s = daten.get("hfm_hack_lief_schwein", "").strip()
        if l_s: w["tf_0004_00_ZS-1209_Schweinefleisch: XXX"] = f"Schweinefleisch: {l_s}"
        c_s = daten.get("hfm_hack_charge_schwein", "").strip()
        if c_s: w["tf_0004_00_ZS-002081_Schweinefleisch: XXX"] = f"Schweinefleisch: {c_s}"

        m_r = daten.get("hfm_hack_mhd_rind", "").strip()
        if m_r and m_r != "..": w["tf_0004_00_ZS-001835_Rindfleisch: XXX"] = f"Rindfleisch: {m_r}"
            
        m_s = daten.get("hfm_hack_mhd_schwein", "").strip()
        if m_s and m_s != "..": w["tf_0004_00_ZS-001835_Schweinefleisch: XXX"] = f"Schweinefleisch: {m_s}"

    # METT & ZUBEREITUNG (Seite 7-9)
    if daten.get("hfm_mett_cb"):
        w["cb_0006_00"] = h_yes
        w["cal_0006_00_ZS-001810"] = daten.get("hfm_mett_herstelldatum", "")
        w["tf_0006_00_ZS-1209"] = daten.get("hfm_mett_lief", "")
        w["tf_0006_00_ZS-002081"] = daten.get("hfm_mett_charge", "")
        w["tf_0006_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_mett_temp", ""))
        
        m_mett = daten.get("hfm_mett_mhd", "").strip()
        if m_mett and m_mett != "..": w["tf_0006_00_ZS-001835"] = m_mett

    if daten.get("hfm_fzs_cb"):
        w["cb_0008_00"] = h_yes
        p, m = str(daten.get("hfm_fzs_produkt", "")).strip(), str(daten.get("hfm_fzs_marinade", "")).strip()
        w['tf_0008_00_ Produkt "Marinade"'] = f'{p} "{m}"' if p and m else p + m
        w["tf_0008_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_fzs_temp", ""))
        
        m_fzs = daten.get("hfm_fzs_mhd", "").strip()
        if m_fzs and m_fzs != "..": w["tf_0008_00_ZS-001835"] = m_fzs

    if daten.get("hfm_fzg_cb"):
        w["cb_0007_00"] = h_yes
        p, m = str(daten.get("hfm_fzg_produkt", "")).strip(), str(daten.get("hfm_fzg_marinade", "")).strip()
        w['tf_0007_00_ Produkt "Marinade"'] = f'{p} "{m}"' if p and m else p + m
        w["tf_0007_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_fzg_temp", ""))
        
        m_fzg = daten.get("hfm_fzg_mhd", "").strip()
        if m_fzg and m_fzg != "..": w["tf_0007_00_ZS-001835"] = m_fzg

    # OBST/GEMÜSE CONVENIENCE
    if daten.get("og_cb"):
        w["cb_0009_00"] = h_yes
        for i in range(1, 6):
            idx = f"{i:02d}" 
            val = daten.get(f"og_name_{idx}", "") or daten.get(f"og_probe_{idx}", "")
            if val: w[f"tf_0009_00_ Teilprobe {i}:"] = f"Teilprobe {i}:{val}"
            w[f"dd_0009_{idx}_ZS-001799"] = daten.get(f"og_ort_{idx}", "")
            w[f"cal_0009_{idx}_ZS-001810"] = daten.get(f"og_herst_{idx}", "")
            w[f"tf_0009_{idx}_ZS-1527"] = daten.get(f"og_verb_{idx}", "")
            w[f"tf_0009_{idx}_ZS-1215"] = daten.get(f"og_inhalt_{idx}", "")
            w[f"dd_0009_{idx}_ZS-001798"] = daten.get(f"og_verp_{idx}", "")
            w[f"tf_0009_{idx}_ZS-1441"] = formatiere_temperatur(daten.get(f"og_temp_{idx}", ""))

    # BIO-HACKFLEISCH
    if daten.get("hfm_bio_cb"):
        w["cb_0005_00"] = h_yes
        w["cal_0005_00_ZS-001810"] = daten.get("hfm_bio_herstelldatum", "")
        
        l_s = daten.get("hfm_bio_lief_schwein", "").strip()
        if l_s: w["tf_0005_00_ZS-1209_Schweinefleisch: XXX"] = f"Schweinefleisch: {l_s}"
        c_s = daten.get("hfm_bio_charge_schwein", "").strip()
        if c_s: w["tf_0005_00_ZS-002081_Schweinefleisch: XXX"] = f"Schweinefleisch: {c_s}"
        
        m_r = daten.get("hfm_bio_mhd_rind", "").strip()
        if m_r and m_r != "..": w["tf_0005_00_ZS-001835_Rindfleisch: XXX"] = f"Rindfleisch: {m_r}"
        
        m_s = daten.get("hfm_bio_mhd_schwein", "").strip()
        if m_s and m_s != "..": w["tf_0005_00_ZS-001835_Schweinefleisch: XXX"] = f"Schweinefleisch: {m_s}"
            
        w["tf_0005_00_ZS-1441"] = formatiere_temperatur(daten.get("hfm_bio_temp", ""))

    return w

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
    # DER CHIRURGISCHE EINGRIFF: PDFs ZUSAMMENFÜGEN
    # ==================================================
    
    # 1. Seiten 1 bis 5 aus der alten Datei laden
    writer.append(reader_master, pages=(0, 5))
    
    # 2. Die 4 neuen, heilen Seiten (Hack, Mett, FZS, FZG) einfügen
    writer.append(reader_neu)
    
    # 3. Den Rest ab Seite 10 aus der alten Datei wieder anhängen
    writer.append(reader_master, pages=(9, len(reader_master.pages)))
    
    # ==================================================
    
    # WICHTIG: Das Formularverzeichnis VOR dem Beschreiben kopieren/erstellen
    if "/AcroForm" not in writer.root_object:
        if "/AcroForm" in reader_master.trailer["/Root"]:
            writer.root_object.update({NameObject("/AcroForm"): reader_master.trailer["/Root"]["/AcroForm"]})
        else:
            writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
            
    writer.root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})

    mapping = sammle_alle_daten(daten)
    text_mapping = {k: str(v) for k, v in mapping.items() if not isinstance(v, NameObject)}

    # Felder sicher befüllen
    for page in writer.pages:
        # Die native Routine füllt Textfelder sanft aus
        writer.update_page_form_field_values(page, text_mapping)

        # Checkboxen separat verarbeiten
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                if "/T" in annot:
                    f_id = clean_id(str(annot["/T"]).strip("()"))
                    if f_id in mapping and isinstance(mapping[f_id], NameObject):
                        val = mapping[f_id]
                        annot.update({NameObject("/V"): val, NameObject("/AS"): val})

    with open(ziel_pfad, "wb") as f: writer.write(f)
    print(f"✅ Perfekter Kombi-Bericht erstellt: {ziel_pfad}")
    return ziel_pfad
