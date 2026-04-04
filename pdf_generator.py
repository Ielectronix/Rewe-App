import os
import datetime
import platform
import pypdf
from pypdf.generic import DictionaryObject, NameObject, ArrayObject

def get_all_rewe_bases():
    if platform.system() == "Windows" or platform.system() == "Darwin":
        return [os.path.join(os.path.expanduser("~"), "Downloads", "REWE")]
    
    raw_bases = [
        "/storage/emulated/0/Download/REWE",
        "/storage/emulated/0/Documents/REWE",
        "/storage/emulated/0/Android/media/com.rewe.app.rewe_app/REWE",
        "/storage/emulated/0/Android/data/com.rewe.app.rewe_app/files/REWE",
        os.path.join(os.path.expanduser("~"), "Downloads", "REWE")
    ]
    bases = []
    for b in raw_bases:
        if b not in bases: bases.append(b)
    return bases

def erstelle_bericht(d, assets_dir="assets"):
    pdf_dateien = [
        "stammdaten.pdf", "trinkwasser.pdf", "scherbeneis.pdf", "okz-se.pdf",
        "hackfleisch_gemischt.pdf", "schweinemett.pdf", "fz_schwein.pdf", 
        "fz_huhn.pdf", "bio.pdf", "okz-hfm.pdf", "og.pdf", "okz-og.pdf"
    ]
    
    fehlende_pdfs = [p for p in pdf_dateien if not os.path.exists(os.path.join(assets_dir, p))]
    if fehlende_pdfs:
        raise FileNotFoundError(f"⚠️ FEHLENDE PDF-VORLAGEN:\n{', '.join(fehlende_pdfs)}")

    writer = pypdf.PdfWriter()
    for pdf_datei in pdf_dateien:
        writer.append(pypdf.PdfReader(os.path.join(assets_dir, pdf_datei)))
    
    # ---------------------------------------------------------
    # DER MAGISCHE SCHLOSSKNACKER FÜR ADOBE CHECKBOXEN!
    # ---------------------------------------------------------
    def cb_val(key, val): 
        if not val: return "/Off" # Haken nicht gesetzt = immer /Off
        
        # 1. HFM-OKZ Haken entschlüsselt:
        if "cb_0010_" in key:
            if "2294" in key: return "/j"
            if "2295" in key:
                if any(x in key for x in ["_02_", "_04_", "_07_"]): return "/j"
                return "/Yes"
                
        # 2. Scherbeneis-OKZ Haken entschlüsselt:
        if "cb_0003_" in key and ("2294" in key or "2295" in key):
            return "/j"
            
        # 3. Obst/Gemüse-OKZ Haken entschlüsselt (NEU!):
        if "cb_0011_" in key:
            if "2294" in key: return "/j" # Abklatsch immer /j
            if "2295" in key:
                if "_01_" in key or "_02_" in key: return "/j" # Tupfer 1 und 2 sind /j
                return "/Yes" # Tupfer 3, 4, 5 sind /Yes
            
        # Für alle normalen Haken in der App:
        return "/Yes" 
    # ---------------------------------------------------------
        
    tw_sonst_text = d.get("tw_auff_sonstiges", "")
    
    f_map = {
        "tf_0000_00_ZS-001870": d.get("adresse", ""),
        "tf_0000_00_ZS-1408": d.get("marktnummer", ""),
        "tf_0000_00_ZS-002000": d.get("auftragsnummer", ""),
        "cal_templateLaborderprobenahmeDatum": d.get("datum", ""),
        "dd_0000_00_ZS-002314": d.get("mitarbeiter_name", ""),
        "dd_0000_00_ZS-1566": d.get("auftraggeber", ""),
        "dd_0000_00_ZS-002315": d.get("typ_probenahme", ""),
        "dd_0000_00_ZS-001796": d.get("bemerkung", "")
    }
    
    if d.get("tw_kalt", False):
        f_map.update({
            "cb_0001_00": cb_val("cb_0001_00", True), 
            "tf_0001_00_probenahmeUhrzeit": d.get("tw_zeit", ""), 
            "tf_0001_00_ZS-1441": d.get("tw_temp", ""), "tf_0001_00_PE_ZS-1514": d.get("tw_tempkonst", ""), 
            "dd_0001_00_PE_ZS-002255": d.get("tw_desinf", ""), "dd_0001_00_PE_ZS-002318": d.get("tw_zapf", ""), 
            "cb_0001_00_PE_ZS-002304_PN-Hahn": cb_val("cb", d.get("tw_cb_pn")), "cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur": cb_val("cb", d.get("tw_cb_ein")), 
            "cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur": cb_val("cb", d.get("tw_cb_zwei")), "cb_0001_00_PE_ZS-002304_ Eingriff-Armmatur": cb_val("cb", d.get("tw_cb_ein_g")), 
            "cb_0001_00_PE_ZS-002304_ Sensor-Armatur": cb_val("cb", d.get("tw_cb_sensor")), "cb_0001_00_PE_ZS-002304_ Eckventil": cb_val("cb", d.get("tw_cb_eck")), 
            "cb_0001_00_PE_ZS-002304_ Armatur mit Kniebestätigung": cb_val("cb", d.get("tw_cb_knie")), "cb_0001_00_PE_ZS-002304_Sonstiges": d.get("tw_zapf_sonst", ""), 
            "dd_0001_00_PE_ZS-001948": d.get("tw_inaktiv", ""), "dd_0001_00_PE_ZS-002305_Farbe": d.get("tw_kurz1", ""), 
            "dd_0001_00_PE_ZS-002305_ Trübung": d.get("tw_kurz2", ""), "dd_0001_00_PE_ZS-002305_ Bodensatz": d.get("tw_kurz3", ""), 
            "dd_0001_00_PE_ZS-002305_ Geruch": d.get("tw_kurz4", ""), "cb_0001_00_PE_ZS-1268_ja": cb_val("cb", d.get("cb_auff_ja")), 
            "cb_0001_00_PE_ZS-1268_ nein": cb_val("cb", d.get("cb_auff_nein")), "cb_0001_00_PE_ZS-1268_ Perlator nicht entfernbar": cb_val("cb", d.get("cb_auff_perl")), 
            "cb_0001_00_PE_ZS-1268_ Starke Verkalkung": cb_val("cb", d.get("cb_auff_verkalk")), "cb_0001_00_PE_ZS-1268_ Armatur mit Verbrühschutz": cb_val("cb", d.get("cb_auff_verbrueh")), 
            "cb_0001_00_PE_ZS-1268_ Durchlauferhitzer": cb_val("cb", d.get("cb_auff_durchlauf")), "cb_0001_00_PE_ZS-1268_ Unterbauspeicher": cb_val("cb", d.get("cb_auff_unterbau")), 
            "cb_0001_00_PE_ZS-1268_ Eckventil warm/kalt geschlossen": cb_val("cb", d.get("cb_auff_eck_zu")), "cb_0001_00_PE_ZS-1268_ nicht möglich": cb_val("cb", d.get("cb_auff_nichtmoeglich")), 
            "cb_0001_00_PE_ZS-1268_ Entnahme aus der Dusche": cb_val("cb", d.get("cb_auff_dusche")), "cb_0001_00_PE_ZS-1268_ Handbrause": cb_val("cb", d.get("cb_auff_handbrause")), 
            "cb_0001_00_PE_ZS-1268_ Sonstiges": cb_val("cb", bool(tw_sonst_text)), "cb_0001_00_PE_ZS-1268_Sonstiges": tw_sonst_text, 
            "dd_0001_00_PE_ZS-002317": d.get("tw_zweck", ""), "tf_0001_00_ZS-1215": d.get("tw_inhalt", ""), 
            "dd_0001_00_ZS-001798": d.get("tw_verpackung", ""), "dd_0001_00_ZS-001799": d.get("tw_entnahmeort", ""), "dd_0001_00_ZS-001796": d.get("tw_bemerkung", "")
        })

    if d.get("se_kalt", False):
        f_map.update({
            "cb_0002_00": cb_val("cb_0002_00", True), "tf_0002_00_probenahmeUhrzeit": d.get("se_zeit", ""), 
            "dd_0002_00_PE_ZS-002319": d.get("se_zapf", ""), "cb_0002_00_PE_ZS-002304_Eiswanne": cb_val("cb", d.get("se_cb_eiswanne")), 
            "cb_0002_00_PE_ZS-002304_ Fallprobe": cb_val("cb", d.get("se_cb_fallprobe")), "cb_0002_00_PE_ZS-002304_Sonstiges": d.get("se_tech_sonst", ""), 
            "dd_0002_00_PE_ZS-002255": d.get("se_desinf", ""), "cb_0002_00_PE_ZS-1268_Ozonsterilisator": cb_val("cb", d.get("se_cb_ozon")), 
            "cb_0002_00_PE_ZS-1268_Sonstiges": d.get("se_auff_sonst", ""), "tf_0002_00_ZS-1215": d.get("se_inhalt", ""), 
            "dd_0002_00_ZS-001798": d.get("se_verpackung", ""), "dd_0002_00_ZS-001799": d.get("se_entnahmeort", ""), 
            "tf_0002_00_ZS-1441": d.get("se_temp", ""), "dd_0002_00_ZS-001796": d.get("se_bemerkung", "")
        })

    if d.get("se_okz_cb", False):
        f_map.update({
            "cb_0003_00": cb_val("cb_0003_00", True), "tf_0003_00": "Abklatschproben Scherbeneis", "dd_0003_00_ZS-001796": d.get("se_okz_bemerkung", "")
        })
        for i in range(1, 4):
            idx = f"{i:02d}"
            f_map.update({
                f"dd_0003_{idx}_ZS-001880": d.get(f"se_okz_status_{idx}", ""), f"dd_0003_{idx}_ZS-1419": d.get(f"se_okz_objekt_{idx}", ""),
                f"dd_0003_{idx}_ZS-001792": d.get(f"se_okz_ort_{idx}", ""), 
                f"cb_0003_{idx}_ZS-002294": cb_val(f"cb_0003_{idx}_ZS-002294", d.get(f"se_okz_abklatsch_{idx}")),
                f"cb_0003_{idx}_ZS-002295": cb_val(f"cb_0003_{idx}_ZS-002295", d.get(f"se_okz_tupfer_{idx}"))
            })

    if d.get("hfm_hack_cb", False):
        f_map.update({
            "cb_0004_00": cb_val("cb_0004_00", True), "tf_0004_00": "Hackfleisch gemischt", "dd_0004_00_ZS-001799": d.get("hfm_hack_entnahmeort", ""),
            "cal_0004_00_ZS-001810": d.get("hfm_hack_herstelldatum", ""), "tf_0004_00_ZS-1215": d.get("hfm_hack_inhalt", ""), 
            "dd_0004_00_ZS-001798": d.get("hfm_hack_verpackung", ""), "tf_0004_00_ZS-1209_Schweinefleisch: XXX": d.get("hfm_hack_lief_schwein", ""),
            "tf_0004_00_ZS-1209_Rindfleisch: XXX": d.get("hfm_hack_lief_rind", ""), "tf_0004_00_ZS-001835_Schweinefleisch: XXX": d.get("hfm_hack_mhd_schwein", ""),
            "tf_0004_00_ZS-001835_Rindfleisch: XXX": d.get("hfm_hack_mhd_rind", ""), "tf_0004_00_ZS-002081_Schweinefleisch: XXX": d.get("hfm_hack_charge_schwein", ""),
            "tf_0004_00_ZS-002081_Rindfleisch: XXX": d.get("hfm_hack_charge_rind", ""), "tf_0004_00_ZS-1441": d.get("hfm_hack_temp", ""), "dd_0004_00_ZS-001796": d.get("hfm_hack_bemerkung", "")
        })

    if d.get("hfm_mett_cb", False):
        f_map.update({
            "cb_0006_00": cb_val("cb_0006_00", True), "tf_0006_00": "gewürztes Schweinemett", "dd_0006_00_ZS-001799": d.get("hfm_mett_entnahmeort", ""),
            "cal_0006_00_ZS-001810": d.get("hfm_mett_herstelldatum", ""), "tf_0006_00_ZS-1215": d.get("hfm_mett_inhalt", ""), "dd_0006_00_ZS-001798": d.get("hfm_mett_verpackung", ""),
            "tf_0006_00_ZS-1209": d.get("hfm_mett_lief", ""), "tf_0006_00_ZS-001835": d.get("hfm_mett_mhd", ""),
            "tf_0006_00_ZS-002081": d.get("hfm_mett_charge", ""), "tf_0006_00_ZS-1441": d.get("hfm_mett_temp", ""), "dd_0006_00_ZS-001796": d.get("hfm_mett_bemerkung", "")
        })

    if d.get("hfm_fzs_cb", False):
        prod_s = (d.get("hfm_fzs_produkt", "")).strip(); mar_s = (d.get("hfm_fzs_marinade", "")).strip()
        prod_mar_str_s = f"{prod_s} / {mar_s}" if (prod_s and mar_s) else (prod_s or mar_s)
        f_map.update({
            "cb_0008_00": cb_val("cb_0008_00", True), "tf_0008_00": "Fleischzubereitung Schwein", "tf_0008_00_ Produkt \"Marinade\"": prod_mar_str_s,
            "dd_0008_00_ZS-001799": d.get("hfm_fzs_entnahmeort", ""), "cal_0008_00_ZS-001810": d.get("hfm_fzs_herstelldatum", ""),
            "tf_0008_00_ZS-1215": d.get("hfm_fzs_inhalt", ""), "dd_0008_00_ZS-001798": d.get("hfm_fzs_verpackung", ""),
            "tf_0008_00_ZS-1209": d.get("hfm_fzs_lief", ""), "tf_0008_00_ZS-001835": d.get("hfm_fzs_mhd", ""),
            "tf_0008_00_ZS-002081": d.get("hfm_fzs_charge", ""), "tf_0008_00_ZS-1441": d.get("hfm_fzs_temp", ""), "dd_0008_00_ZS-001796": d.get("hfm_fzs_bemerkung", "")
        })

    if d.get("hfm_fzg_cb", False):
        prod_g = (d.get("hfm_fzg_produkt", "")).strip(); mar_g = (d.get("hfm_fzg_marinade", "")).strip()
        prod_mar_str_g = f"{prod_g} / {mar_g}" if (prod_g and mar_g) else (prod_g or mar_g)
        f_map.update({
            "cb_0007_00": cb_val("cb_0007_00", True), "tf_0007_00": "Fleischzubereitung Geflügel", "tf_0007_00_ Produkt \"Marinade\"": prod_mar_str_g, 
            "dd_0007_00_ZS-001799": d.get("hfm_fzg_entnahmeort", ""), "cal_0007_00_ZS-001810": d.get("hfm_fzg_herstelldatum", ""),
            "tf_0007_00_ZS-1215": d.get("hfm_fzg_inhalt", ""), "dd_0007_00_ZS-001798": d.get("hfm_fzg_verpackung", ""),
            "tf_0007_00_ZS-1209": d.get("hfm_fzg_lief", ""), "tf_0007_00_ZS-001835": d.get("hfm_fzg_mhd", ""),
            "tf_0007_00_ZS-002081": d.get("hfm_fzg_charge", ""), "tf_0007_00_ZS-1441": d.get("hfm_fzg_temp", ""), "dd_0007_00_ZS-001796": d.get("hfm_fzg_bemerkung", "")
        })

    if d.get("hfm_bio_cb", False):
        f_map.update({
            "cb_0005_00": cb_val("cb_0005_00", True), "tf_0005_00": "Biohackfleisch", "dd_0005_00_ZS-001799": d.get("hfm_bio_entnahmeort", ""),
            "cal_0005_00_ZS-001810": d.get("hfm_bio_herstelldatum", ""), "tf_0005_00_ZS-1215": d.get("hfm_bio_inhalt", ""), 
            "dd_0005_00_ZS-001798": d.get("hfm_bio_verpackung", ""), "tf_0005_00_ZS-1209_Schweinefleisch: XXX": d.get("hfm_bio_lief_schwein", ""),
            "tf_0005_00_ZS-1209_Rindfleisch: XXX": d.get("hfm_bio_lief_rind", ""), "tf_0005_00_ZS-001835_Schweinefleisch: XXX": d.get("hfm_bio_mhd_schwein", ""),
            "tf_0005_00_ZS-001835_Rindfleisch: XXX": d.get("hfm_bio_mhd_rind", ""), "tf_0005_00_ZS-002081_Schweinefleisch: XXX": d.get("hfm_bio_charge_schwein", ""),
            "tf_0005_00_ZS-002081_Rindfleisch: XXX": d.get("hfm_bio_charge_rind", ""), "tf_0005_00_ZS-1441": d.get("hfm_bio_temp", ""), "dd_0005_00_ZS-001796": d.get("hfm_bio_bemerkung", "")
        })

    if d.get("hfm_okz_cb", False):
        f_map.update({
            "cb_0010_00": cb_val("cb_0010_00", True), "tf_0010_00": "Abklatschproben HFM", "dd_0010_00_ZS-001796": d.get("hfm_okz_bemerkung", "")
        })
        for i in range(1, 11):
            idx = f"{i:02d}"
            f_map.update({
                f"dd_0010_{idx}_ZS-001880": d.get(f"okz_status_{idx}", ""), f"dd_0010_{idx}_ZS-1419": d.get(f"okz_objekt_{idx}", ""),
                f"dd_0010_{idx}_ZS-001792": d.get(f"okz_ort_{idx}", ""), 
                f"cb_0010_{idx}_ZS-002294": cb_val(f"cb_0010_{idx}_ZS-002294", d.get(f"okz_abklatsch_{idx}")),
                f"cb_0010_{idx}_ZS-002295": cb_val(f"cb_0010_{idx}_ZS-002295", d.get(f"okz_tupfer_{idx}"))
            })
            
    if d.get("og_cb", False):
        f_map.update({"cb_0009_00": cb_val("cb_0009_00", True), "tf_0009_00": "Obst-/Gemüse Convenience"})
        for i in range(1, 6):
            idx = f"{i:02d}"
            f_map.update({
                f"tf_0009_00_ Teilprobe {i}:": d.get(f"og_name_{idx}", ""), f"dd_0009_{idx}_ZS-001799": d.get(f"og_ort_{idx}", ""),
                f"cal_0009_{idx}_ZS-001810": d.get(f"og_herst_{idx}", ""), f"tf_0009_{idx}_ZS-1527": d.get(f"og_verb_{idx}", ""),
                f"tf_0009_{idx}_ZS-1215": d.get(f"og_inhalt_{idx}", ""), f"dd_0009_{idx}_ZS-001798": d.get(f"og_verp_{idx}", ""),
                f"tf_0009_{idx}_ZS-1441": d.get(f"og_temp_{idx}", "")
            })
            
    if d.get("og_okz_cb", False):
        f_map.update({
            "cb_0011_00": cb_val("cb_0011_00", True), "tf_0011_00": "Obst-Gemüse Abklatschproben", "dd_0011_00_ZS-001796": d.get("og_okz_bemerkung", ""), "Anmerkung": d.get("og_okz_anmerkung", "")
        })
        for i in range(1, 6):
            idx = f"{i:02d}"
            f_map.update({
                f"dd_0011_{idx}_ZS-001880": d.get(f"og_okz_status_{idx}", ""), f"dd_0011_{idx}_ZS-1419": d.get(f"og_okz_objekt_{idx}", ""),
                f"dd_0011_{idx}_ZS-001792": d.get(f"og_okz_ort_{idx}", ""), 
                f"cb_0011_{idx}_ZS-002294": cb_val(f"cb_0011_{idx}_ZS-002294", d.get(f"og_okz_abklatsch_{idx}")),
                f"cb_0011_{idx}_ZS-002295": cb_val(f"cb_0011_{idx}_ZS-002295", d.get(f"og_okz_tupfer_{idx}"))
            })
        
    if "/AcroForm" not in writer.root_object: 
        writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
        
    if "/Fields" not in writer.root_object["/AcroForm"]: 
        writer.root_object["/AcroForm"].update({NameObject("/Fields"): ArrayObject()})
        
    for p in writer.pages: 
        writer.update_page_form_field_values(p, f_map)
        
    roh_nummer = d.get("marktnummer", "")
    s_markt = "".join([c for c in roh_nummer if c.isalnum()])
    if not s_markt: s_markt = "Unbekannt"

    heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
    date_str = datetime.datetime.now().strftime('%d%m%y')
    time_str = datetime.datetime.now().strftime('%H%M%S') 
    filename = f"REWE_{s_markt}_{date_str}_{time_str}.pdf"
    
    saved = False
    saved_path = ""
    
    for base in get_all_rewe_bases():
        target_dir = os.path.join(base, heute_ordner)
        target_file = os.path.join(target_dir, filename)
        try:
            os.makedirs(target_dir, exist_ok=True)
            with open(target_file, "wb") as f:
                writer.write(f)
            saved = True
            saved_path = target_file
            break
        except (PermissionError, OSError):
            continue
            
    if not saved:
        raise PermissionError("Handy blockiert das Speichern in allen verfügbaren Ordnern.")
        
    return saved_path
