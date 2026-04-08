import os
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, StringObject, BooleanObject

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

def hole_okz_werte(daten, sektion_prefix, prefix_in_pdf, anzahl, erwartet_j=True):
    # Setzt den Haken auf /j oder /Yes, je nachdem was das PDF verlangt
    haken_wert = NameObject('/j') if erwartet_j else NameObject('/Yes')
    w = {}
    for i in range(1, anzahl + 1):
        idx = f"{i:02d}"
        ort = daten.get(f"{sektion_prefix}_ort_{idx}", "")
        obj = daten.get(f"{sektion_prefix}_objekt_{idx}", "")
        
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
    # Bereitet ALLE Felder als großes Wörterbuch vor
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
        w["cb_0001_00"] = NameObject('/Yes')
        w["txt_0001_00_PE_ZS-1274"] = daten.get("tw_zeit", "")
        w["txt_0001_00_PE_ZS-002304"] = daten.get("tw_temp", "")
        w["txt_0001_00_PE_ZS-002305"] = daten.get("tw_tempkonst", "")
        desinf = daten.get("tw_desinf", "")
        if desinf == "Abflammen": w["cb_0001_00_PE_ZS-1262_ Abflammen"] = NameObject('/Yes')
        elif desinf == "Sprühdesinfektion": w["cb_0001_00_PE_ZS-1262_ Sprühdesinfektion"] = NameObject('/Yes')
        elif desinf == "ohne Desinfektion": w["cb_0001_00_PE_ZS-1262_ ohne"] = NameObject('/Yes')
        w["txt_0001_00_PE_ZS-1260"] = daten.get("tw_zapf", "")
        w["txt_0001_00_PE_ZS-1261"] = daten.get("tw_zapf_sonst", "")
        w["txt_0001_00_PE_ZS-1267"] = daten.get("tw_inaktiv", "")
        
        kurz1 = daten.get("tw_kurz1", "")
        if "1 -" in kurz1: w["cb_0001_00_PE_ZS-1270_ 1"] = NameObject('/Yes')
        elif "2 -" in kurz1: w["cb_0001_00_PE_ZS-1270_ 2"] = NameObject('/Yes')
        elif "3 -" in kurz1: w["cb_0001_00_PE_ZS-1270_ 3"] = NameObject('/Yes')
        kurz2 = daten.get("tw_kurz2", "")
        if "1 -" in kurz2: w["cb_0001_00_PE_ZS-1271_ 1"] = NameObject('/Yes')
        elif "2 -" in kurz2: w["cb_0001_00_PE_ZS-1271_ 2"] = NameObject('/Yes')
        elif "3 -" in kurz2: w["cb_0001_00_PE_ZS-1271_ 3"] = NameObject('/Yes')
        kurz3 = daten.get("tw_kurz3", "")
        if "1 -" in kurz3: w["cb_0001_00_PE_ZS-1272_ 1"] = NameObject('/Yes')
        elif "2 -" in kurz3: w["cb_0001_00_PE_ZS-1272_ 2"] = NameObject('/Yes')
        elif "3 -" in kurz3: w["cb_0001_00_PE_ZS-1272_ 3"] = NameObject('/Yes')
        kurz4 = daten.get("tw_kurz4", "")
        if "1 -" in kurz4: w["cb_0001_00_PE_ZS-1273_ 1"] = NameObject('/Yes')
        elif "2 -" in kurz4: w["cb_0001_00_PE_ZS-1273_ 2"] = NameObject('/Yes')
        elif "3 -" in kurz4: w["cb_0001_00_PE_ZS-1273_ 3"] = NameObject('/Yes')
        
        w["txt_0001_00_PE_ZS-002278"] = daten.get("tw_zweck", "")
        w["txt_0001_00_PE_ZS-002279"] = daten.get("tw_inhalt", "")
        w["txt_0001_00_PE_ZS-002280"] = daten.get("tw_verpackung", "")
        w["txt_0001_00_PE_ZS-002281"] = daten.get("tw_entnahmeort", "")
        w["txt_0001_00_PE_ZS-002282"] = daten.get("tw_bemerkung", "")
        w["txt_0001_00_PE_ZS-1269"] = daten.get("tw_auff_sonstiges", "")

        if daten.get("tw_cb_pn"): w["cb_0001_00_PE_ZS-002304_PN-Hahn"] = NameObject('/Yes')
        if daten.get("tw_cb_ein"): w["cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur"] = NameObject('/Yes')
        if daten.get("tw_cb_zwei"): w["cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur"] = NameObject('/Yes')
        if daten.get("tw_cb_ein_g"): w["cb_0001_00_PE_ZS-002304_ Eingriff-Armmatur"] = NameObject('/Yes')
        if daten.get("tw_cb_sensor"): w["cb_0001_00_PE_ZS-002304_ Sensor-Armatur"] = NameObject('/Yes')
        if daten.get("tw_cb_eck"): w["cb_0001_00_PE_ZS-002304_ Eckventil"] = NameObject('/Yes')
        if daten.get("tw_cb_knie"): w["cb_0001_00_PE_ZS-002304_ Armatur mit Kniebestätigung"] = NameObject('/Yes')
        if daten.get("cb_auff_ja"): w["cb_0001_00_PE_ZS-1268_ja"] = NameObject('/Yes')
        if daten.get("cb_auff_nein"): w["cb_0001_00_PE_ZS-1268_ nein"] = NameObject('/Yes')
        if daten.get("cb_auff_perl"): w["cb_0001_00_PE_ZS-1268_ Perlator nicht entfernbar"] = NameObject('/Yes')
        if daten.get("cb_auff_verkalk"): w["cb_0001_00_PE_ZS-1268_ Starke Verkalkung"] = NameObject('/Yes')
        if daten.get("cb_auff_verbrueh"): w["cb_0001_00_PE_ZS-1268_ Armatur mit Verbrühschutz"] = NameObject('/Yes')
        if daten.get("cb_auff_durchlauf"): w["cb_0001_00_PE_ZS-1268_ Durchlauferhitzer"] = NameObject('/Yes')
        if daten.get("cb_auff_unterbau"): w["cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]"] = NameObject('/Yes')
        if daten.get("cb_auff_eck_zu"): w["cb_0001_00_PE_ZS-1268_ Eckventil warm/kalt geschlossen"] = NameObject('/Yes')
        if daten.get("cb_auff_nichtmoeglich"): w["cb_0001_00_PE_ZS-1268_ nicht möglich"] = NameObject('/Yes')
        if daten.get("cb_auff_dusche"): w["cb_0001_00_PE_ZS-1268_ Entnahme aus der Dusche"] = NameObject('/Yes')
        if daten.get("cb_auff_handbrause"): w["cb_0001_00_PE_ZS-1268_ Handbrause"] = NameObject('/Yes')
        if daten.get("cb_auff_sonst"): w["cb_0001_00_PE_ZS-1268_ Sonstiges"] = NameObject('/Yes')

    # SCHERBENEIS
    if daten.get("se_kalt", False):
        w["cb_0002_00"] = NameObject('/Yes')
        w["txt_0002_00_PE_ZS-1274"] = daten.get("se_zeit", "")
        w["txt_0002_00_PE_ZS-002304"] = daten.get("se_temp", "")
        w["txt_0002_00_PE_ZS-1260"] = daten.get("se_zapf", "")
        w["txt_0002_00_PE_ZS-1269"] = daten.get("se_auff_sonst", "")
        w["txt_0002_00_PE_ZS-1261"] = daten.get("se_tech_sonst", "")
        se_desinf = daten.get("se_desinf", "")
        if se_desinf == "Abflammen": w["cb_0002_00_PE_ZS-1262_ Abflammen"] = NameObject('/Yes')
        elif se_desinf == "Sprühdesinfektion": w["cb_0002_00_PE_ZS-1262_ Sprühdesinfektion"] = NameObject('/Yes')
        elif se_desinf == "ohne Desinfektion": w["cb_0002_00_PE_ZS-1262_ ohne"] = NameObject('/Yes')
        if daten.get("se_cb_eiswanne"): w["cb_0002_00_PE_ZS-002304_ Eiswanne/Schöpfprobe"] = NameObject('/Yes')
        if daten.get("se_cb_fallprobe"): w["cb_0002_00_PE_ZS-002304_ Fallprobe"] = NameObject('/Yes')
        if daten.get("se_cb_ozon"): w["cb_0002_00_PE_ZS-1268_ Ozonsterilisator"] = NameObject('/Yes')
        w["txt_0002_00_PE_ZS-002279"] = daten.get("se_inhalt", "")
        w["txt_0002_00_PE_ZS-002280"] = daten.get("se_verpackung", "")
        w["txt_0002_00_PE_ZS-002281"] = daten.get("se_entnahmeort", "")
        w["txt_0002_00_PE_ZS-002282"] = daten.get("se_bemerkung", "")

    # SCHERBENEIS - OKZ
    if daten.get("se_okz_cb", False):
        w["cb_0003_00"] = NameObject('/Yes')
        w["txt_0003_00_PE_ZS-002282"] = daten.get("se_okz_bemerkung", "")
        w.update(hole_okz_werte(daten, "se_okz", "0003", 3, erwartet_j=True))

    # HFM - HACKFLEISCH GEMISCHT
    if daten.get("hfm_hack_cb", False):
        w["cb_0004_00"] = NameObject('/Yes')
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
        w["cb_0005_00"] = NameObject('/Yes')
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
        w["cb_0006_00"] = NameObject('/Yes')
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
        w["cb_0007_00"] = NameObject('/Yes')
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
        w["cb_0008_00"] = NameObject('/Yes')
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

    # HFM - OKZ
    if daten.get("hfm_okz_cb", False):
        w["cb_0010_00"] = NameObject('/Yes')
        w["txt_0010_00_PE_ZS-002282"] = daten.get("hfm_okz_bemerkung", "")
        w.update(hole_okz_werte(daten, "okz", "0010", 10, erwartet_j=True))

    # CONVENIENCE OG
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

    # CONVENIENCE OG - OKZ
    if daten.get("og_okz_cb", False):
        w["cb_0011_00"] = NameObject('/Yes')
        w["txt_0011_00_PE_ZS-002282"] = daten.get("og_okz_bemerkung", "")
        w["txt_0011_00_PE_ZS-002293"] = daten.get("og_okz_anmerkung", "")
        w.update(hole_okz_werte(daten, "og_okz", "0011", 5, erwartet_j=True))

    return w


def erstelle_bericht(daten):
    assets_dir = "assets"

    ziel_ordner = get_tages_ordner()
    markt_nr = daten.get("marktnummer", "").strip() or "Ohne_Nummer"
    datum_str = daten.get("datum", "").replace(".", "_") or get_heute_str()
    
    # NEU: Hängt die genaue Uhrzeit (Stunde, Minute, Sekunde) an den Namen!
    # Dadurch gibt es NIEMALS die gleiche Datei zweimal, der Android-Cache wird umgangen.
    uhrzeit_str = datetime.datetime.now().strftime('%H-%M-%S')
    dateiname = f"REWE_Monitoring_{markt_nr}_{datum_str}_{uhrzeit_str}.pdf"
    ziel_pfad = os.path.join(ziel_ordner, dateiname)

    werte_mapping = bereite_daten_vor(daten)
    writer = PdfWriter()

    benoetigte_pdfs = []
    
    if daten.get("tw_kalt"): benoetigte_pdfs.append("trinkwasser.pdf")
    if daten.get("se_kalt"): benoetigte_pdfs.append("scherbeneis.pdf")
    if daten.get("se_okz_cb"): benoetigte_pdfs.append("okz-eis.pdf")
    if daten.get("hfm_hack_cb"): benoetigte_pdfs.append("hfm_hack.pdf")
    if daten.get("hfm_mett_cb"): benoetigte_pdfs.append("hfm_mett.pdf")
    if daten.get("hfm_fzs_cb"): benoetigte_pdfs.append("hfm_fzs.pdf")
    if daten.get("hfm_fzg_cb"): benoetigte_pdfs.append("hfm_fzg.pdf")
    if daten.get("hfm_bio_cb"): benoetigte_pdfs.append("hfm_bio.pdf")
    if daten.get("hfm_okz_cb"): benoetigte_pdfs.append("okz-hfm.pdf")
    if daten.get("og_cb"): benoetigte_pdfs.append("og.pdf")
    if daten.get("og_okz_cb"): benoetigte_pdfs.append("okz-og.pdf")
    
    if not benoetigte_pdfs:
        raise ValueError("Keine Proben in der App ausgewählt (Haken gesetzt)! PDF kann nicht erstellt werden.")

    pdfs_nicht_gefunden = []

    # 1. PDFs laden und aneinanderhängen
    for pdf_name in benoetigte_pdfs:
        pdf_pfad = f"assets/{pdf_name}"
        if not os.path.exists(pdf_pfad):
            pdfs_nicht_gefunden.append(pdf_name)
            continue

        reader = PdfReader(pdf_pfad)
        writer.append(reader)

    if pdfs_nicht_gefunden:
        raise FileNotFoundError(f"Die folgenden PDFs fehlen im 'assets' Ordner: {', '.join(pdfs_nicht_gefunden)}")

    # 2. Felder im großen, zusammengefügten PDF ausfüllen
    for page in writer.pages:
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                if annot.get("/Subtype") == "/Widget" and "/T" in annot:
                    field_name_str = str(annot.get("/T"))
                    if field_name_str in werte_mapping:
                        val = werte_mapping[field_name_str]
                        
                        # Wenn es ein NameObject ist (wie /j oder /Yes für Haken)
                        if isinstance(val, NameObject):
                            annot[NameObject("/V")] = val
                            annot[NameObject("/AS")] = val
                        # Wenn es ganz normaler Text ist
                        else:
                            annot[NameObject("/V")] = StringObject(val)

    # 3. ZWINGT ANDROID, DEN TEXT SICHTBAR ZU MACHEN
    if "/AcroForm" in writer.root_object:
        writer.root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    # 4. Datei final abspeichern
    with open(ziel_pfad, "wb") as output_file:
        writer.write(output_file)

    return ziel_pfad