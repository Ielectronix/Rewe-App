import os
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, create_string_object

# --- BASIS-ORDNER LOGIK ---
def get_all_rewe_bases():
    if os.name == 'nt':
        desk = os.path.join(os.path.expanduser('~'), 'Desktop', 'Rewe_Monitoring')
        return [desk]
    else:
        return ["/storage/emulated/0/Download/Rewe_Monitoring", "/storage/emulated/0/Download"]

def create_base_folder():
    bases = get_all_rewe_bases()
    for base in bases:
        try:
            if not os.path.exists(base): os.makedirs(base, exist_ok=True)
            return base
        except: continue
    raise PermissionError("Keine Schreibrechte!")

def get_tages_ordner():
    tages_ordner = os.path.join(create_base_folder(), datetime.datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(tages_ordner, exist_ok=True)
    return tages_ordner

# --- DATEN-VORBEREITUNG (IDs bleiben exakt gleich) ---
def hole_okz_werte(daten, sektion_prefix, prefix_in_pdf, anzahl):
    w = {}
    haken = NameObject('/j')
    for i in range(1, anzahl + 1):
        idx = f"{i:02d}"
        if daten.get(f"{sektion_prefix}_ort_{idx}") or daten.get(f"{sektion_prefix}_objekt_{idx}"):
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002287"] = daten.get(f"{sektion_prefix}_status_{idx}", "")
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002288"] = daten.get(f"{sektion_prefix}_objekt_{idx}", "")
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002290"] = daten.get(f"{sektion_prefix}_ort_{idx}", "")
            if daten.get(f"{sektion_prefix}_abklatsch_{idx}"): w[f"cb_{prefix_in_pdf}_{idx}_ZS-002294"] = haken
            if daten.get(f"{sektion_prefix}_tupfer_{idx}"): w[f"cb_{prefix_in_pdf}_{idx}_ZS-002295"] = haken
    return w

def bereite_daten_vor(daten):
    w = {}
    # Stammdaten
    w["txt_0000_00_MA-Name"] = daten.get("mitarbeiter_name", "")
    w["txt_0000_00_Datum"] = daten.get("datum", "")
    w["txt_0000_00_REWE-Adresse"] = f"{daten.get('marktnummer', '')} - {daten.get('adresse', '')}"
    w["txt_0000_00_Auftrags-Nr"] = daten.get("auftragsnummer", "")
    
    # HFM Hackfleisch gemischt
    if daten.get("hfm_hack_cb"):
        w["cb_0004_00"] = NameObject('/Yes')
        w["txt_0004_00_PE_ZS-002281"] = daten.get("hfm_hack_entnahmeort", "")
        w["txt_0004_00_PE_ZS-002298"] = daten.get("hfm_hack_herstelldatum", "")
        w["txt_0004_00_PE_ZS-002299"] = daten.get("hfm_hack_lief_schwein", "")
        w["txt_0004_00_PE_ZS-002300"] = daten.get("hfm_hack_lief_rind", "")
        w["txt_0004_00_PE_ZS-002301"] = daten.get("hfm_hack_mhd_schwein", "")
        w["txt_0004_00_PE_ZS-002302"] = daten.get("hfm_hack_mhd_rind", "")
        w["txt_0004_00_PE_ZS-002296"] = daten.get("hfm_hack_charge_schwein", "")
        w["txt_0004_00_PE_ZS-002297"] = daten.get("hfm_hack_charge_rind", "")
        w["txt_0004_00_PE_ZS-002304"] = daten.get("hfm_hack_temp", "")

    # OKZ HFM
    if daten.get("hfm_okz_cb"):
        w["cb_0010_00"] = NameObject('/Yes')
        w.update(hole_okz_werte(daten, "okz", "0010", 10))
    
    return w

# --- HAUPTFUNKTION (LIMS-Safe) ---
def erstelle_bericht(daten):
    assets_dir = "assets"
    ziel_ordner = get_tages_ordner()
    markt_nr = daten.get("marktnummer", "").strip() or "Ohne_Nummer"
    dateiname = f"REWE_Monitoring_{markt_nr}_{daten.get('datum','').replace('.','_')}.pdf"
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

    for pdf_name in benoetigte_pdfs:
        pdf_pfad = os.path.join(assets_dir, pdf_name)
        if not os.path.exists(pdf_pfad): continue

        reader = PdfReader(pdf_pfad)
        # Wir fügen die Seiten hinzu
        for page in reader.pages:
            writer.add_page(page)
    
    # WICHTIG: Die Felder nach dem Zusammenfügen befüllen, damit die IDs global im Dokument bleiben
    writer.update_page_form_field_values(writer.pages, werte_mapping)

    # LIMS-RELEVANT: NeedAppearances auf True setzen
    # Das sorgt dafür, dass die Daten im PDF-Viewer angezeigt werden, ohne die IDs zu löschen
    if "/AcroForm" not in writer.root_object:
        writer.root_object.update({
            NameObject("/AcroForm"): writer._add_object({})
        })
    
    writer.root_object["/AcroForm"].update({
        NameObject("/NeedAppearances"): BooleanObject(True)
    })

    with open(ziel_pfad, "wb") as output_file:
        writer.write(output_file)

    return ziel_pfad