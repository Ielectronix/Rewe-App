import os
import datetime
from pdfrw import PdfReader, PdfWriter, PdfName, PdfString, PdfDict

# SUCHT DEN RICHTIGEN BASIS-ORDNER FÜR ANDROID ODER WINDOWS
def get_all_rewe_bases():
    if os.name == 'nt':
        desk = os.path.join(os.path.expanduser('~'), 'Desktop', 'Rewe_Monitoring')
        return [desk]
    else:
        return [
            "/storage/emulated/0/Download/Rewe_Monitoring",
            "/storage/emulated/0/Downloads/Rewe_Monitoring",
            "/storage/emulated/0/Documents/Rewe_Monitoring",
            "/storage/emulated/0/Download"
        ]

# SICHERES ERSTELLEN DES ORDNERS
def create_base_folder():
    bases = get_all_rewe_bases()
    for base in bases:
        try:
            if not os.path.exists(base):
                os.makedirs(base, exist_ok=True)
            return base
        except PermissionError:
            continue
    raise PermissionError("KEINE SCHREIBRECHTE AUF DEM HANDY! Bitte App-Berechtigungen (Dateien/Medien) prüfen.")

# DATUM FÜR DATEINAMEN
def get_heute_str():
    return datetime.datetime.now().strftime('%Y-%m-%d')

# GIBT DEN PFAD ZUM TAGESORDNER ZURÜCK
def get_tages_ordner():
    base = create_base_folder()
    tages_ordner = os.path.join(base, get_heute_str())
    os.makedirs(tages_ordner, exist_ok=True)
    return tages_ordner

def create_pdf_string(text):
    if not text:
        return PdfString("()")
    
    # ISO-8859-1 Encoding für Umlaute im PDF (sehr wichtig für pdfrw)
    encoded = text.encode('iso-8859-1', 'replace').decode('iso-8859-1')
    
    # Spezielle Zeichen für PDF formatieren
    encoded = encoded.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    return PdfString(f"({encoded})")

def set_field_value(field, value):
    if value is None:
        return

    if isinstance(value, str):
        # Textfeld setzen
        field.update(PdfDict(V=create_pdf_string(value)))
    elif isinstance(value, PdfName):
        # Checkbox setzen (z. B. PdfName("/Yes") oder PdfName("/j"))
        field.update(PdfDict(AS=value, V=value))

def hole_okz_werte(daten, sektion_prefix, prefix_in_pdf, anzahl, erwartet_j=True):
    # Hilfsfunktion für OKZ (Abklatsch/Tupfer).
    # erwartet_j=True bedeutet, wir nutzen /j statt /Yes für den Haken.
    haken_wert = PdfName('/j') if erwartet_j else PdfName('/Yes')
    w = {}
    for i in range(1, anzahl + 1):
        idx = f"{i:02d}"
        ort = daten.get(f"{sektion_prefix}_ort_{idx}", "")
        obj = daten.get(f"{sektion_prefix}_objekt_{idx}", "")
        
        # Nur wenn es ein Ort oder Objekt gibt, setzen wir die Werte
        if ort or obj:
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002287"] = daten.get(f"{sektion_prefix}_status_{idx}", "")
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002288"] = obj
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002290"] = ort
            
            if daten.get(f"{sektion_prefix}_abklatsch_{idx}", False):
                w[f"cb_{prefix_in_pdf}_{idx}_ZS-002294"] = haken_wert
            if daten.get(f"{sektion_prefix}_tupfer_{idx}", False):
                w[f"cb_{prefix_in_pdf}_{idx}_ZS-002295"] = haken_wert
    return w

def bereite_daten_vor(daten):
    # Bereitet das Dictionary für pdfrw vor (Mapping auf die internen PDF-Feldnamen)
    
    w = {}
    
    # STAMMDATEN (ALLGEMEIN)
    w["txt_0000_00_MA-Name"] = daten.get("mitarbeiter_name", "")
    w["txt_0000_00_Datum"] = daten.get("datum", "")
    w["txt_0000_00_REWE-Adresse"] = f"{daten.get('marktnummer', '')} - {daten.get('adresse', '')}"
    w["txt_0000_00_Kunde"] = daten.get("auftraggeber", "")
    w["txt_0000_00_Auftrags-Nr"] = daten.get("auftragsnummer", "")
    w["txt_0000_00_ZS-002286"] = daten.get("typ_probenahme", "")
    w["txt_0000_00_ZS-002293"] = daten.get("bemerkung", "")

    # TRINKWASSER
    if daten.get("tw_kalt", False):
        w["cb_0001_00"] = PdfName('/Yes')
        w["txt_0001_00_PE_ZS-1274"] = daten.get("tw_zeit", "")
        w["txt_0001_00_PE_ZS-002304"] = daten.get("tw_temp", "")
        w["txt_0001_00_PE_ZS-002305"] = daten.get("tw_tempkonst", "")
        
        # Desinfektion
        desinf = daten.get("tw_desinf", "")
        if desinf == "Abflammen": w["cb_0001_00_PE_ZS-1262_ Abflammen"] = PdfName('/Yes')
        elif desinf == "Sprühdesinfektion": w["cb_0001_00_PE_ZS-1262_ Sprühdesinfektion"] = PdfName('/Yes')
        elif desinf == "ohne Desinfektion": w["cb_0001_00_PE_ZS-1262_ ohne"] = PdfName('/Yes')
        
        w["txt_0001_00_PE_ZS-1260"] = daten.get("tw_zapf", "")
        w["txt_0001_00_PE_ZS-1261"] = daten.get("tw_zapf_sonst", "")
        w["txt_0001_00_PE_ZS-1267"] = daten.get("tw_inaktiv", "")
        
        # Kurzsensorik
        kurz1 = daten.get("tw_kurz1", "")
        if "1 -" in kurz1: w["cb_0001_00_PE_ZS-1270_ 1"] = PdfName('/Yes')
        elif "2 -" in kurz1: w["cb_0001_00_PE_ZS-1270_ 2"] = PdfName('/Yes')
        elif "3 -" in kurz1: w["cb_0001_00_PE_ZS-1270_ 3"] = PdfName('/Yes')
        
        kurz2 = daten.get("tw_kurz2", "")
        if "1 -" in kurz2: w["cb_0001_00_PE_ZS-1271_ 1"] = PdfName('/Yes')
        elif "2 -" in kurz2: w["cb_0001_00_PE_ZS-1271_ 2"] = PdfName('/Yes')
        elif "3 -" in kurz2: w["cb_0001_00_PE_ZS-1271_ 3"] = PdfName('/Yes')
        
        kurz3 = daten.get("tw_kurz3", "")
        if "1 -" in kurz3: w["cb_0001_00_PE_ZS-1272_ 1"] = PdfName('/Yes')
        elif "2 -" in kurz3: w["cb_0001_00_PE_ZS-1272_ 2"] = PdfName('/Yes')
        elif "3 -" in kurz3: w["cb_0001_00_PE_ZS-1272_ 3"] = PdfName('/Yes')
        
        kurz4 = daten.get("tw_kurz4", "")
        if "1 -" in kurz4: w["cb_0001_00_PE_ZS-1273_ 1"] = PdfName('/Yes')
        elif "2 -" in kurz4: w["cb_0001_00_PE_ZS-1273_ 2"] = PdfName('/Yes')
        elif "3 -" in kurz4: w["cb_0001_00_PE_ZS-1273_ 3"] = PdfName('/Yes')
        
        w["txt_0001_00_PE_ZS-002278"] = daten.get("tw_zweck", "")
        w["txt_0001_00_PE_ZS-002279"] = daten.get("tw_inhalt", "")
        w["txt_0001_00_PE_ZS-002280"] = daten.get("tw_verpackung", "")
        w["txt_0001_00_PE_ZS-002281"] = daten.get("tw_entnahmeort", "")
        w["txt_0001_00_PE_ZS-002282"] = daten.get("tw_bemerkung", "")
        w["txt_0001_00_PE_ZS-1269"] = daten.get("tw_auff_sonstiges", "")

        # Alle Technik/Auffälligkeits-Checkboxen für Trinkwasser (nach deiner Liste /Yes)
        if daten.get("tw_cb_pn"): w["cb_0001_00_PE_ZS-002304_PN-Hahn"] = PdfName('/Yes')
        if daten.get("tw_cb_ein"): w["cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur"] = PdfName('/Yes')
        if daten.get("tw_cb_zwei"): w["cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur"] = PdfName('/Yes')
        if daten.get("tw_cb_ein_g"): w["cb_0001_00_PE_ZS-002304_ Eingriff-Armmatur"] = PdfName('/Yes')
        if daten.get("tw_cb_sensor"): w["cb_0001_00_PE_ZS-002304_ Sensor-Armatur"] = PdfName('/Yes')
        if daten.get("tw_cb_eck"): w["cb_0001_00_PE_ZS-002304_ Eckventil"] = PdfName('/Yes')
        if daten.get("tw_cb_knie"): w["cb_0001_00_PE_ZS-002304_ Armatur mit Kniebestätigung"] = PdfName('/Yes')
        
        if daten.get("cb_auff_ja"): w["cb_0001_00_PE_ZS-1268_ja"] = PdfName('/Yes')
        if daten.get("cb_auff_nein"): w["cb_0001_00_PE_ZS-1268_ nein"] = PdfName('/Yes')
        if daten.get("cb_auff_perl"): w["cb_0001_00_PE_ZS-1268_ Perlator nicht entfernbar"] = PdfName('/Yes')
        if daten.get("cb_auff_verkalk"): w["cb_0001_00_PE_ZS-1268_ Starke Verkalkung"] = PdfName('/Yes')
        if daten.get("cb_auff_verbrueh"): w["cb_0001_00_PE_ZS-1268_ Armatur mit Verbrühschutz"] = PdfName('/Yes')
        if daten.get("cb_auff_durchlauf"): w["cb_0001_00_PE_ZS-1268_ Durchlauferhitzer"] = PdfName('/Yes')
        if daten.get("cb_auff_unterbau"): w["cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]"] = PdfName('/Yes')
        if daten.get("cb_auff_eck_zu"): w["cb_0001_00_PE_ZS-1268_ Eckventil warm/kalt geschlossen"] = PdfName('/Yes')
        if daten.get("cb_auff_nichtmoeglich"): w["cb_0001_00_PE_ZS-1268_ nicht möglich"] = PdfName('/Yes')
        if daten.get("cb_auff_dusche"): w["cb_0001_00_PE_ZS-1268_ Entnahme aus der Dusche"] = PdfName('/Yes')
        if daten.get("cb_auff_handbrause"): w["cb_0001_00_PE_ZS-1268_ Handbrause"] = PdfName('/Yes')
        if daten.get("cb_auff_sonst"): w["cb_0001_00_PE_ZS-1268_ Sonstiges"] = PdfName('/Yes')

    # SCHERBENEIS
    if daten.get("se_kalt", False):
        w["cb_0002_00"] = PdfName('/Yes')
        w["txt_0002_00_PE_ZS-1274"] = daten.get("se_zeit", "")
        w["txt_0002_00_PE_ZS-002304"] = daten.get("se_temp", "")
        w["txt_0002_00_PE_ZS-1260"] = daten.get("se_zapf", "")
        w["txt_0002_00_PE_ZS-1269"] = daten.get("se_auff_sonst", "")
        w["txt_0002_00_PE_ZS-1261"] = daten.get("se_tech_sonst", "")
        
        se_desinf = daten.get("se_desinf", "")
        if se_desinf == "Abflammen": w["cb_0002_00_PE_ZS-1262_ Abflammen"] = PdfName('/Yes')
        elif se_desinf == "Sprühdesinfektion": w["cb_0002_00_PE_ZS-1262_ Sprühdesinfektion"] = PdfName('/Yes')
        elif se_desinf == "ohne Desinfektion": w["cb_0002_00_PE_ZS-1262_ ohne"] = PdfName('/Yes')

        if daten.get("se_cb_eiswanne"): w["cb_0002_00_PE_ZS-002304_ Eiswanne/Schöpfprobe"] = PdfName('/Yes')
        if daten.get("se_cb_fallprobe"): w["cb_0002_00_PE_ZS-002304_ Fallprobe"] = PdfName('/Yes')
        if daten.get("se_cb_ozon"): w["cb_0002_00_PE_ZS-1268_ Ozonsterilisator"] = PdfName('/Yes')

        w["txt_0002_00_PE_ZS-002279"] = daten.get("se_inhalt", "")
        w["txt_0002_00_PE_ZS-002280"] = daten.get("se_verpackung", "")
        w["txt_0002_00_PE_ZS-002281"] = daten.get("se_entnahmeort", "")
        w["txt_0002_00_PE_ZS-002282"] = daten.get("se_bemerkung", "")

    # SCHERBENEIS - OKZ (Erwartet /j laut Liste)
    if daten.get("se_okz_cb", False):
        w["cb_0003_00"] = PdfName('/Yes')
        w["txt_0003_00_PE_ZS-002282"] = daten.get("se_okz_bemerkung", "")
        w.update(hole_okz_werte(daten, "se_okz", "0003", 3, erwartet_j=True))

    # HFM - HACKFLEISCH GEMISCHT
    if daten.get("hfm_hack_cb", False):
        w["cb_0004_00"] = PdfName('/Yes')
        w["txt_0004_00_PE_ZS-002281"] = daten.get("hfm_hack_entnahmeort", "")
        w["txt_0004_00_PE_ZS-002298"] = daten.get("hfm_hack_herstelldatum", "")
        w["txt_0004_00_PE_ZS-002279"] = daten.get("hfm_hack_inhalt", "")
        w["txt_0004_00_PE_ZS-002280"] = daten.get("hfm_hack_verpackung", "")
        w["txt_0004_00_PE_ZS-002299"] = daten.get("hfm_hack_lief_schwein", "")
        w["txt_0004_00_PE_ZS-002300"] = daten.get("hfm_hack_lief_rind", "")
        w["txt_0004_00_PE_ZS-002301"] = daten.get("hfm_hack_mhd_schwein", "")
        w["txt_0004_00_PE_ZS-002302"] = daten.get("hfm_hack_mhd_rind", "")
        w["txt_0004_00_PE_ZS-002296"] = daten.get("hfm_hack_charge_schwein", "")
        w["txt_0004_00_PE_ZS-002297"] = daten.get("hfm_hack_charge_rind", "")
        w["txt_0004_00_PE_ZS-002304"] = daten.get("hfm_hack_temp", "")
        w["txt_0004_00_PE_ZS-002282"] = daten.get("hfm_hack_bemerkung", "")

    # HFM - SCHWEINEMETT
    if daten.get("hfm_mett_cb", False):
        w["cb_0005_00"] = PdfName('/Yes')
        w["txt_0005_00_PE_ZS-002281"] = daten.get("hfm_mett_entnahmeort", "")
        w["txt_0005_00_PE_ZS-002298"] = daten.get("hfm_mett_herstelldatum", "")
        w["txt_0005_00_PE_ZS-002279"] = daten.get("hfm_mett_inhalt", "")
        w["txt_0005_00_PE_ZS-002280"] = daten.get("hfm_mett_verpackung", "")
        w["txt_0005_00_PE_ZS-002299"] = daten.get("hfm_mett_lief", "")
        w["txt_0005_00_PE_ZS-002301"] = daten.get("hfm_mett_mhd", "")
        w["txt_0005_00_PE_ZS-002296"] = daten.get("hfm_mett_charge", "")
        w["txt_0005_00_PE_ZS-002304"] = daten.get("hfm_mett_temp", "")
        w["txt_0005_00_PE_ZS-002282"] = daten.get("hfm_mett_bemerkung", "")

    # HFM - FZ SCHWEIN
    if daten.get("hfm_fzs_cb", False):
        w["cb_0006_00"] = PdfName('/Yes')
        w["txt_0006_00_PE_ZS-002281"] = daten.get("hfm_fzs_entnahmeort", "")
        w["txt_0006_00_PE_ZS-002303"] = daten.get("hfm_fzs_produkt", "")
        w["txt_0006_00_PE_ZS-002306"] = daten.get("hfm_fzs_marinade", "")
        w["txt_0006_00_PE_ZS-002298"] = daten.get("hfm_fzs_herstelldatum", "")
        w["txt_0006_00_PE_ZS-002279"] = daten.get("hfm_fzs_inhalt", "")
        w["txt_0006_00_PE_ZS-002280"] = daten.get("hfm_fzs_verpackung", "")
        w["txt_0006_00_PE_ZS-002299"] = daten.get("hfm_fzs_lief", "")
        w["txt_0006_00_PE_ZS-002301"] = daten.get("hfm_fzs_mhd", "")
        w["txt_0006_00_PE_ZS-002296"] = daten.get("hfm_fzs_charge", "")
        w["txt_0006_00_PE_ZS-002304"] = daten.get("hfm_fzs_temp", "")
        w["txt_0006_00_PE_ZS-002282"] = daten.get("hfm_fzs_bemerkung", "")

    # HFM - FZ GEFLÜGEL
    if daten.get("hfm_fzg_cb", False):
        w["cb_0007_00"] = PdfName('/Yes')
        w["txt_0007_00_PE_ZS-002281"] = daten.get("hfm_fzg_entnahmeort", "")
        w["txt_0007_00_PE_ZS-002303"] = daten.get("hfm_fzg_produkt", "")
        w["txt_0007_00_PE_ZS-002306"] = daten.get("hfm_fzg_marinade", "")
        w["txt_0007_00_PE_ZS-002298"] = daten.get("hfm_fzg_herstelldatum", "")
        w["txt_0007_00_PE_ZS-002279"] = daten.get("hfm_fzg_inhalt", "")
        w["txt_0007_00_PE_ZS-002280"] = daten.get("hfm_fzg_verpackung", "")
        w["txt_0007_00_PE_ZS-002299"] = daten.get("hfm_fzg_lief", "")
        w["txt_0007_00_PE_ZS-002301"] = daten.get("hfm_fzg_mhd", "")
        w["txt_0007_00_PE_ZS-002296"] = daten.get("hfm_fzg_charge", "")
        w["txt_0007_00_PE_ZS-002304"] = daten.get("hfm_fzg_temp", "")
        w["txt_0007_00_PE_ZS-002282"] = daten.get("hfm_fzg_bemerkung", "")

    # HFM - BIO HACKFLEISCH
    if daten.get("hfm_bio_cb", False):
        w["cb_0008_00"] = PdfName('/Yes')
        w["txt_0008_00_PE_ZS-002281"] = daten.get("hfm_bio_entnahmeort", "")
        w["txt_0008_00_PE_ZS-002298"] = daten.get("hfm_bio_herstelldatum", "")
        w["txt_0008_00_PE_ZS-002279"] = daten.get("hfm_bio_inhalt", "")
        w["txt_0008_00_PE_ZS-002280"] = daten.get("hfm_bio_verpackung", "")
        w["txt_0008_00_PE_ZS-002299"] = daten.get("hfm_bio_lief_schwein", "")
        w["txt_0008_00_PE_ZS-002300"] = daten.get("hfm_bio_lief_rind", "")
        w["txt_0008_00_PE_ZS-002301"] = daten.get("hfm_bio_mhd_schwein", "")
        w["txt_0008_00_PE_ZS-002302"] = daten.get("hfm_bio_mhd_rind", "")
        w["txt_0008_00_PE_ZS-002296"] = daten.get("hfm_bio_charge_schwein", "")
        w["txt_0008_00_PE_ZS-002297"] = daten.get("hfm_bio_charge_rind", "")
        w["txt_0008_00_PE_ZS-002304"] = daten.get("hfm_bio_temp", "")
        w["txt_0008_00_PE_ZS-002282"] = daten.get("hfm_bio_bemerkung", "")

    # HFM - OKZ (Erwartet /j laut Liste)
    if daten.get("hfm_okz_cb", False):
        w["cb_0010_00"] = PdfName('/Yes')
        w["txt_0010_00_PE_ZS-002282"] = daten.get("hfm_okz_bemerkung", "")
        w.update(hole_okz_werte(daten, "okz", "0010", 10, erwartet_j=True))

    # CONVENIENCE OG - TEILPROBEN
    if daten.get("og_cb", False):
        for i in range(1, 6):
            idx = f"{i:02d}"
            name_val = daten.get(f"og_name_{idx}", "")
            if name_val:
                w[f"txt_0012_{idx}_ZS-002289"] = name_val
                w[f"txt_0012_{idx}_ZS-002281"] = daten.get(f"og_ort_{idx}", "")
                w[f"txt_0012_{idx}_ZS-002298"] = daten.get(f"og_herst_{idx}", "")
                w[f"txt_0012_{idx}_ZS-002301"] = daten.get(f"og_verb_{idx}", "")
                w[f"txt_0012_{idx}_ZS-002279"] = daten.get(f"og_inhalt_{idx}", "")
                w[f"txt_0012_{idx}_ZS-002280"] = daten.get(f"og_verp_{idx}", "")
                w[f"txt_0012_{idx}_ZS-002304"] = daten.get(f"og_temp_{idx}", "")

    # CONVENIENCE OG - OKZ (Erwartet /j laut Liste für 01-05)
    if daten.get("og_okz_cb", False):
        w["cb_0011_00"] = PdfName('/Yes')
        w["txt_0011_00_PE_ZS-002282"] = daten.get("og_okz_bemerkung", "")
        w["txt_0011_00_PE_ZS-002293"] = daten.get("og_okz_anmerkung", "")
        w.update(hole_okz_werte(daten, "og_okz", "0011", 5, erwartet_j=True))

    return w

def erstelle_bericht(daten):
    basis_pdf_pfad = "assets/formular_blanko.pdf"
    if not os.path.exists(basis_pdf_pfad):
        raise FileNotFoundError(f"Die Datei {basis_pdf_pfad} wurde nicht im App-Ordner gefunden!")

    ziel_ordner = get_tages_ordner()
    
    # Dateiname zusammenbauen: "REWE_Monitoring_MarktNr_Datum.pdf"
    markt_nr = daten.get("marktnummer", "").strip()
    if not markt_nr: markt_nr = "Ohne_Nummer"
    datum_str = daten.get("datum", "").replace(".", "_")
    if not datum_str: datum_str = get_heute_str()
    
    dateiname = f"REWE_Monitoring_{markt_nr}_{datum_str}.pdf"
    ziel_pfad = os.path.join(ziel_ordner, dateiname)

    pdf = PdfReader(basis_pdf_pfad)
    werte_mapping = bereite_daten_vor(daten)

    # Durch das PDF gehen und Felder ausfüllen
    for page in pdf.pages:
        annotations = page.Annots
        if annotations:
            for annotation in annotations:
                if annotation.Subtype == '/Widget' and annotation.T:
                    field_name = annotation.T[1:-1]
                    if field_name in werte_mapping:
                        set_field_value(annotation, werte_mapping[field_name])

    PdfWriter().write(ziel_pfad, pdf)
    return ziel_pfad
