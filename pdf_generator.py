import os, datetime, platform, pypdf
from pypdf.generic import DictionaryObject, NameObject, ArrayObject

def get_all_rewe_bases():
    if platform.system() == "Windows" or platform.system() == "Darwin":
        return [os.path.join(os.path.expanduser("~"), "Downloads", "REWE")]
    return ["/storage/emulated/0/Download/REWE", "/storage/emulated/0/Documents/REWE", 
            "/storage/emulated/0/Android/media/com.rewe.app.rewe_app/REWE", 
            "/storage/emulated/0/Android/data/com.rewe.app.rewe_app/files/REWE"]

def erstelle_bericht(d, assets_dir="assets"):
    pdf_dateien = ["stammdaten.pdf", "trinkwasser.pdf", "scherbeneis.pdf", "okz-se.pdf",
                   "hackfleisch_gemischt.pdf", "schweinemett.pdf", "fz_schwein.pdf", 
                   "fz_huhn.pdf", "bio.pdf", "okz-hfm.pdf", "og.pdf", "okz-og.pdf"]
    writer = pypdf.PdfWriter()
    for pdf in pdf_dateien: writer.append(pypdf.PdfReader(os.path.join(assets_dir, pdf)))
    
    def cb_val(key, val):
        if not val: return "/Off"
        # HIER IST DEINE LISTE EINGEARBEITET:
        if "cb_0010_" in key: # HFM OKZ
            if "2294" in key: return "/j" # Abklatscher sind alle /j
            if "2295" in key: # Tupfer-Speziallogik
                if any(x in key for x in ["_02_", "_04_", "_07_"]): return "/j"
                return "/Yes"
        if "cb_0011_" in key: # OG OKZ (falls dort auch /j gebraucht wird)
            return "/j" if "2294" in key else "/Yes"
        return "/Yes"

    # Mapping (Stammdaten & HFM OKZ als Beispiel - erweitere dies analog für die anderen)
    f_map = {
        "tf_0000_00_ZS-1408": d.get("marktnummer", ""), "cal_templateLaborderprobenahmeDatum": d.get("datum", ""),
        "tf_0000_00_ZS-002000": d.get("auftragsnummer", ""), "tf_0000_00_ZS-001870": d.get("adresse", "")
    }
    if d.get("hfm_okz_cb"):
        for i in range(1, 11):
            idx = f"{i:02d}"
            f_map[f"cb_0010_{idx}_ZS-002294"] = cb_val(f"cb_0010_{idx}_ZS-002294", d.get(f"okz_abklatsch_{idx}"))
            f_map[f"cb_0010_{idx}_ZS-002295"] = cb_val(f"cb_0010_{idx}_ZS-002295", d.get(f"okz_tupfer_{idx}"))

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
    raise PermissionError("Speichern nicht möglich. Berechtigung prüfen!")