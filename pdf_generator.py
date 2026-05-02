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
    def get_val(key, default=""):
        v = daten.get(key)
        if v is None or str(v).strip() == "": return str(default)
        return str(v)
    def check(key, pdf_id):
        w[pdf_id] = bool(daten.get(key))

    w["cal_templateLaborderprobenahmeDatum"] = get_val("datum")
    w["tf_0000_00_ZS-1408"] = get_val("marktnummer")
    w["tf_0000_00_ZS-001870"] = get_val("adresse") 
    w["dd_0000_00_ZS-1566"] = get_val("auftraggeber", "03509 - REWE Hackfleischmonitoring")
    w["dd_0000_00_ZS-002314"] = get_val("mitarbeiter_name")
    w["dd_0000_00_ZS-002315"] = get_val("typ_probenahme", "Standard")
    w["tf_0000_00_ZS-002000"] = get_val("auftragsnummer")
    w["dd_0000_00_ZS-001796"] = get_val("bemerkung")

    # Trinkwasser
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
    w["dd_0001_00_PE_ZS-002317"] = get_val("tw_zweck", "DIN EN ISO 19458 Zweck B")
    w["tf_0001_00_ZS-1215"] = get_val("tw_inhalt", "ca. 500 ml")
    w["dd_0001_00_ZS-001798"] = get_val("tw_verpackung", "500ml Kunststoff-Flasche mit Natriumthiosulfat")
    w["dd_0001_00_ZS-001799"] = get_val("tw_entnahmeort", "Metzgerei")

    # Fleisch (Mett / Bio / Hack) Panzerbrecher
    m_mett = get_val("hfm_mett_mhd")
    if m_mett.replace(".", "").strip(): w["tf_0006_00_ZS-001835"] = m_mett

    bio_herst = get_val("hfm_bio_herstelldatum")
    if bio_herst.replace(".", "").strip():
        w["cal_0005_00_ZS-001810"] = bio_herst
        w["tf_0005_00_ZS-001810"] = bio_herst
        w["cal_0005_00"] = bio_herst

    return w

# --- HAUPT-FUNKTION ---
def erstelle_bericht(daten):
    master_pfad = os.path.join("assets", "Rewe_PDF.pdf")
    neu_pfad = os.path.join("assets", "hfm_neu.pdf")
    
    if not os.path.exists(master_pfad): return f"FEHLER: {master_pfad} fehlt!"
    
    # FIX: Dateiname bekommt IMMER die genaue Uhrzeit, um Überschreib-Fehler zu vermeiden
    zeit_jetzt = datetime.datetime.now().strftime('%H-%M-%S')
    dateiname = f"REWE_{daten.get('marktnummer', 'Unbekannt')}_{datetime.datetime.now().strftime('%Y-%m-%d')}_{zeit_jetzt}.pdf"
    ziel_pfad = os.path.join(get_tages_ordner(), dateiname)

    reader_master = PdfReader(master_pfad)
    writer = PdfWriter()
    
    # PDF Zusammenbau (Seiten-Logik beibehalten)
    if os.path.exists(neu_pfad):
        reader_neu = PdfReader(neu_pfad)
        writer.append(reader_master, pages=list(range(0, 5)))
        writer.append(reader_neu)
        writer.append(reader_master, pages=list(range(5, len(reader_master.pages))))
    else:
        writer.append(reader_master)
    
    if "/AcroForm" not in writer.root_object:
        if "/AcroForm" in reader_master.trailer["/Root"]:
            writer.root_object.update({NameObject("/AcroForm"): reader_master.trailer["/Root"]["/AcroForm"]})
        else:
            writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
            
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
                    if "/Parent" in current_obj: current_obj = current_obj["/Parent"].get_object()
                    else: break
                if not f_id: continue

                if f_id in mapping and isinstance(mapping[f_id], bool):
                    val = mapping[f_id]
                    on_state = NameObject("/Yes")
                    if "/AP" in annot and "/N" in annot["/AP"]:
                        for k in annot["/AP"]["/N"].keys():
                            if k != "/Off": on_state = NameObject(k); break
                    state = on_state if val else NameObject("/Off")
                    annot.update({NameObject("/V"): state, NameObject("/AS"): state})
                elif f_id in mapping and not isinstance(mapping[f_id], bool):
                    val = str(mapping[f_id])
                    if val and val != "..":
                        annot.update({NameObject("/V"): create_string_object(val)})
                        if "/Parent" in annot:
                            annot["/Parent"].get_object().update({NameObject("/V"): create_string_object(val)})

    with open(ziel_pfad, "wb") as f: writer.write(f)
    return ziel_pfad