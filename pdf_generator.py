import os, datetime, platform, pypdf

def get_all_rewe_bases():
    if platform.system() == "Windows" or platform.system() == "Darwin":
        return [os.path.join(os.path.expanduser("~"), "Downloads", "REWE")]
    return [
        "/storage/emulated/0/Download/REWE", "/storage/emulated/0/Documents/REWE",
        "/storage/emulated/0/Android/media/com.rewe.app.rewe_app/REWE",
        "/storage/emulated/0/Android/data/com.rewe.app.rewe_app/files/REWE"
    ]

def erstelle_bericht(d, assets_dir="assets"):
    pdf_dateien = [
        "stammdaten.pdf", "trinkwasser.pdf", "scherbeneis.pdf", "okz-se.pdf",
        "hackfleisch_gemischt.pdf", "schweinemett.pdf", "fz_schwein.pdf", 
        "fz_huhn.pdf", "bio.pdf", "okz-hfm.pdf", "og.pdf", "okz-og.pdf"
    ]
    
    fehlende = [p for p in pdf_dateien if not os.path.exists(os.path.join(assets_dir, p))]
    if fehlende: raise FileNotFoundError(f"Fehlende PDFs: {', '.join(fehlende)}")

    writer = pypdf.PdfWriter()
    for pdf in pdf_dateien: writer.append(pypdf.PdfReader(os.path.join(assets_dir, pdf)))
    
    def cb_val(key, val): 
        if not val: return "/Off"
        if any(x in key for x in ["cb_0010_", "cb_0011_", "cb_0003_"]):
            if "2294" in key: return "/j" 
            if "2295" in key: return "/j" if any(y in key for y in ["_02_", "_04_", "_07_"]) else "/Yes"
        return "/Yes"

    f_map = {
        "tf_0000_00_ZS-001870": d.get("adresse", ""), "tf_0000_00_ZS-1408": d.get("marktnummer", ""),
        "tf_0000_00_ZS-002000": d.get("auftragsnummer", ""), "cal_templateLaborderprobenahmeDatum": d.get("datum", ""),
        "dd_0000_00_ZS-002314": d.get("mitarbeiter_name", ""), "dd_0000_00_ZS-1566": d.get("auftraggeber", ""),
        "dd_0000_00_ZS-002315": d.get("typ_probenahme", ""), "dd_0000_00_ZS-001796": d.get("bemerkung", "")
    }

    # HFM OKZ MAPPING
    if d.get("hfm_okz_cb"):
        f_map["cb_0010_00"] = cb_val("cb_0010_00", True)
        for i in range(1, 11):
            idx = f"{i:02d}"
            f_map[f"cb_0010_{idx}_ZS-002294"] = cb_val(f"cb_0010_{idx}_ZS-002294", d.get(f"okz_abklatsch_{idx}"))
            f_map[f"cb_0010_{idx}_ZS-002295"] = cb_val(f"cb_0010_{idx}_ZS-002295", d.get(f"okz_tupfer_{idx}"))
            f_map[f"dd_0010_{idx}_ZS-001880"] = d.get(f"okz_status_{idx}", "")
            f_map[f"dd_0010_{idx}_ZS-1419"] = d.get(f"okz_objekt_{idx}", "")
            f_map[f"dd_0010_{idx}_ZS-001792"] = d.get(f"okz_ort_{idx}", "")

    # OG OKZ MAPPING
    if d.get("og_okz_cb"):
        f_map["cb_0011_00"] = cb_val("cb_0011_00", True)
        f_map["dd_0011_00_ZS-001796"] = d.get("og_okz_bemerkung", "")
        f_map["Anmerkung"] = d.get("og_okz_anmerkung", "")
        for i in range(1, 6):
            idx = f"{i:02d}"
            f_map[f"cb_0011_{idx}_ZS-002294"] = cb_val(f"cb_0011_{idx}_ZS-002294", d.get(f"og_okz_abklatsch_{idx}"))
            f_map[f"cb_0011_{idx}_ZS-002295"] = cb_val(f"cb_0011_{idx}_ZS-002295", d.get(f"og_okz_tupfer_{idx}"))
            f_map[f"dd_0011_{idx}_ZS-001880"] = d.get(f"og_okz_status_{idx}", "")
            f_map[f"dd_0011_{idx}_ZS-1419"] = d.get(f"og_okz_objekt_{idx}", "")
            f_map[f"dd_0011_{idx}_ZS-001792"] = d.get(f"og_okz_ort_{idx}", "")

    if "/AcroForm" not in writer.root_object: writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
    if "/Fields" not in writer.root_object["/AcroForm"]: writer.root_object["/AcroForm"].update({NameObject("/Fields"): ArrayObject()})
        
    for p in writer.pages: writer.update_page_form_field_values(p, f_map)
    s_markt = "".join([c for c in d.get("marktnummer", "") if c.isalnum()]) or "Unbekannt"
    filename = f"REWE_{s_markt}_{datetime.datetime.now().strftime('%d%m%y_%H%M%S')}.pdf"
    
    for base in get_all_rewe_bases():
        target_dir = os.path.join(base, datetime.datetime.now().strftime('%Y-%m-%d'))
        try:
            os.makedirs(target_dir, exist_ok=True)
            path = os.path.join(target_dir, filename)
            with open(path, "wb") as f: writer.write(f)
            return path
        except: continue
    raise PermissionError("Dein Handy blockiert das Speichern!")