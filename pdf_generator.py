import os
import datetime
from pypdf import PdfReader, PdfWriter
# NEU: DictionaryObject hinzugefügt, um den Fehler zu beheben!
from pypdf.generic import NameObject, BooleanObject, create_string_object, DictionaryObject

# SUCHT DEN RICHTIGEN BASIS-ORDNER
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

def create_base_folder():
    bases = get_all_rewe_bases()
    for base in bases:
        try:
            if not os.path.exists(base):
                os.makedirs(base, exist_ok=True)
            return base
        except PermissionError:
            continue
    raise PermissionError("KEINE SCHREIBRECHTE! Bitte App-Berechtigungen prüfen.")

def get_heute_str():
    return datetime.datetime.now().strftime('%Y-%m-%d')

def get_tages_ordner():
    base = create_base_folder()
    tages_ordner = os.path.join(base, get_heute_str())
    os.makedirs(tages_ordner, exist_ok=True)
    return tages_ordner

def hole_okz_werte(daten, sektion_prefix, prefix_in_pdf, anzahl, erwartet_j=True):
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
    w = {}
    # STAMMDATEN
    w["txt_0000_00_MA-Name"] = daten.get("mitarbeiter_name", "")
    w["txt_0000_00_Datum"] = daten.get("datum", "")
    w["txt_0000_00_REWE-Adresse"] = f"{daten.get('marktnummer', '')} - {daten.get('adresse', '')}"
    w["txt_0000_00_Kunde"] = daten.get("auftraggeber", "")
    w["txt_0000_00_Auftrags-Nr"] = daten.get("auftragsnummer", "")
    w["txt_0000_00_ZS-002286"] = daten.get("typ_probenahme", "")
    w["txt_0000_00_ZS-002293"] = daten.get("bemerkung", "")

    # TRINKWASSER
    if daten.get("tw_kalt"):
        w["cb_0001_00"] = NameObject('/Yes')
        w["txt_0001_00_PE_ZS-1274"] = daten.get("tw_zeit", "")
        w["txt_0001_00_PE_ZS-002304"] = daten.get("tw_temp", "")
        w["txt_0001_00_PE_ZS-002305"] = daten.get("tw_tempkonst", "")
        if daten.get("tw_cb_pn"): w["cb_0001_00_PE_ZS-002304_PN-Hahn"] = NameObject('/Yes')
        if daten.get("tw_cb_ein"): w["cb_0001_00_PE_ZS-002304_ Einhebel-Mischarmatur"] = NameObject('/Yes')
        if daten.get("tw_cb_zwei"): w["cb_0001_00_PE_ZS-002304_ Zweigriff-Mischarmatur"] = NameObject('/Yes')
        if daten.get("tw_cb_ein_g"): w["cb_0001_00_PE_ZS-002304_ Eingriff-Armmatur"] = NameObject('/Yes')
        if daten.get("tw_cb_sensor"): w["cb_0001_00_PE_ZS-002304_ Sensor-Armatur"] = NameObject('/Yes')
        if daten.get("tw_cb_eck"): w["cb_0001_00_PE_ZS-002304_ Eckventil"] = NameObject('/Yes')
        if daten.get("tw_cb_knie"): w["cb_0001_00_PE_ZS-002304_ Armatur mit Kniebestätigung"] = NameObject('/Yes')
        if daten.get("cb_auff_unterbau"): w["cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]"] = NameObject('/Yes')
        if daten.get("cb_auff_dusche"): w["cb_0001_00_PE_ZS-1268_ Entnahme aus der Dusche"] = NameObject('/Yes')
        if daten.get("cb_auff_handbrause"): w["cb_0001_00_PE_ZS-1268_ Handbrause"] = NameObject('/Yes')
        w["txt_0001_00_PE_ZS-002278"] = daten.get("tw_zweck", "")
        w["txt_0001_00_PE_ZS-002279"] = daten.get("tw_inhalt", "")
        w["txt_0001_00_PE_ZS-002280"] = daten.get("tw_verpackung", "")
        w["txt_0001_00_PE_ZS-002281"] = daten.get("tw_entnahmeort", "")
        w["txt_0001_00_PE_ZS-002282"] = daten.get("tw_bemerkung", "")
        w["txt_0001_00_PE_ZS-1269"] = daten.get("tw_auff_sonstiges", "")

    # HACKFLEISCH GEMISCHT (HFM)
    if daten.get("hfm_hack_cb"):
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

    # OKZ HFM
    if daten.get("hfm_okz_cb"):
        w["cb_0010_00"] = NameObject('/Yes')
        w["txt_0010_00_PE_ZS-002282"] = daten.get("hfm_okz_bemerkung", "")
        w.update(hole_okz_werte(daten, "okz", "0010", 10, erwartet_j=True))

    return w

def erstelle_bericht(daten):
    assets_dir = "assets"
    ziel_ordner = get_tages_ordner()
    
    # DATEINAME: Überschreibt alte Berichte derselben Tour am selben Tag
    markt_nr = daten.get("marktnummer", "").strip() or "Ohne_Nummer"
    datum_str = daten.get("datum", "").replace(".", "_")
    dateiname = f"REWE_Monitoring_{markt_nr}_{datum_str}.pdf"
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
        raise ValueError("Keine Proben ausgewählt!")

    for pdf_name in benoetigte_pdfs:
        pdf_pfad = os.path.join(assets_dir, pdf_name)
        if not os.path.exists(pdf_pfad):
            continue

        reader = PdfReader(pdf_pfad)
        
        # NeedAppearances auf dem Reader setzen
        if "/AcroForm" in reader.trailer["/Root"]:
            reader.trailer["/Root"]["/AcroForm"].update({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })

        for page in reader.pages:
            if "/Annots" in page:
                for annot_ref in page["/Annots"]:
                    annot = annot_ref.get_object()
                    if "/T" in annot:
                        field_name = annot["/T"].strip("()")
                        if field_name in werte_mapping:
                            val = werte_mapping[field_name]
                            if isinstance(val, NameObject):
                                annot.update({NameObject("/V"): val, NameObject("/AS"): val})
                            else:
                                annot.update({NameObject("/V"): create_string_object(val)})
            writer.add_page(page)

    # --- FIX FÜR DEN SYSTEM-FEHLER (PdfDict -> DictionaryObject) ---
    if "/AcroForm" not in writer.root_object:
        writer.root_object.update({
            NameObject("/AcroForm"): DictionaryObject({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })
        })
    else:
        writer.root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })

    # SPEICHERN
    with open(ziel_pfad, "wb") as output_file:
        writer.write(output_file)

    return ziel_pfad