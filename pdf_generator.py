import os
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, create_string_object

# --- PFAD-LOGIK ---
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
    raise PermissionError("Schreibrechte fehlen!")

def get_tages_ordner():
    t_ordner = os.path.join(create_base_folder(), datetime.datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(t_ordner, exist_ok=True)
    return t_ordner

# --- HAKEN-LOGIK FÜR OKZ (LIMS-ID SICHER) ---
def hole_okz_werte(daten, sektion_prefix, prefix_in_pdf, anzahl):
    w = {}
    haken = NameObject('/j')
    for i in range(1, anzahl + 1):
        idx = f"{i:02d}"
        # Nur wenn Ort oder Objekt gefüllt sind, werden die IDs generiert
        if daten.get(f"{sektion_prefix}_ort_{idx}") or daten.get(f"{sektion_prefix}_objekt_{idx}"):
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002287"] = daten.get(f"{sektion_prefix}_status_{idx}", "")
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002288"] = daten.get(f"{sektion_prefix}_objekt_{idx}", "")
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002290"] = daten.get(f"{sektion_prefix}_ort_{idx}", "")
            if daten.get(f"{sektion_prefix}_abklatsch_{idx}"): 
                w[f"cb_{prefix_in_pdf}_{idx}_ZS-002294"] = haken
            if daten.get(f"{sektion_prefix}_tupfer_{idx}"): 
                w[f"cb_{prefix_in_pdf}_{idx}_ZS-002295"] = haken
    return w

def bereite_daten_vor(daten):
    w = {}
    # Stammdaten IDs
    w["txt_0000_00_MA-Name"] = daten.get("mitarbeiter_name", "")
    w["txt_0000_00_Datum"] = daten.get("datum", "")
    w["txt_0000_00_REWE-Adresse"] = f"{daten.get('marktnummer', '')} - {daten.get('adresse', '')}"
    w["txt_0000_00_Auftrags-Nr"] = daten.get("auftragsnummer", "")
    w["txt_0000_00_ZS-002286"] = daten.get("typ_probenahme", "")
    w["txt_0000_00_ZS-002293"] = daten.get("bemerkung", "")

    # Trinkwasser IDs
    if daten.get("tw_kalt"):
        w["cb_0001_00"] = NameObject('/Yes')
        w["txt_0001_00_PE_ZS-1274"] = daten.get("tw_zeit", "")
        w["txt_0001_00_PE_ZS-002304"] = daten.get("tw_temp", "")
        w["txt_0001_00_PE_ZS-002305"] = daten.get("tw_tempkonst", "")
        w["txt_0001_00_PE_ZS-002281"] = daten.get("tw_entnahmeort", "")
        w["txt_0001_00_PE_ZS-002282"] = daten.get("tw_bemerkung", "")
        if daten.get("cb_auff_unterbau"): w["cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]"] = NameObject('/Yes')

    # HFM IDs
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

    # OKZ HFM IDs
    if daten.get("hfm_okz_cb"):
        w["cb_0010_00"] = NameObject('/Yes')
        w.update(hole_okz_werte(daten, "okz", "0010", 10))

    return w

# --- GENERIERUNG ---
def erstelle_bericht(daten):
    assets_dir = "assets"
    ziel_ordner = get_tages_ordner()
    markt_nr = daten.get("marktnummer", "").strip() or "Ohne_Nummer"
    dateiname = f"REWE_Monitoring_{markt_nr}_{daten.get('datum','').replace('.','_')}.pdf"
    ziel_pfad = os.path.join(ziel_ordner, dateiname)

    werte_mapping = bereite_daten_vor(daten)
    writer = PdfWriter()

    benoetigte_pdfs = []
    # (Liste der PDFs wie gehabt...)
    mapping_checks = [
        ("tw_kalt", "trinkwasser.pdf"), ("se_kalt", "scherbeneis.pdf"),
        ("se_okz_cb", "okz-eis.pdf"), ("hfm_hack_cb", "hfm_hack.pdf"),
        ("hfm_mett_cb", "hfm_mett.pdf"), ("hfm_fzs_cb", "hfm_fzs.pdf"),
        ("hfm_fzg_cb", "hfm_fzg.pdf"), ("hfm_bio_cb", "hfm_bio.pdf"),
        ("hfm_okz_cb", "okz-hfm.pdf"), ("og_cb", "og.pdf"),
        ("og_okz_cb", "okz-og.pdf")
    ]
    for check, name in mapping_checks:
        if daten.get(check): benoetigte_pdfs.append(name)

    if not benoetigte_pdfs: raise ValueError("Keine Proben gewählt!")

    # SEITEN EINZELN VERARBEITEN (DER LANGE WEG)
    for pdf_name in benoetigte_pdfs:
        pdf_pfad = os.path.join(assets_dir, pdf_name)
        if not os.path.exists(pdf_pfad): continue

        reader = PdfReader(pdf_pfad)
        for page in reader.pages:
            if "/Annots" in page:
                for annot_ref in page["/Annots"]:
                    annot = annot_ref.get_object()
                    if "/T" in annot:
                        # Hier ist die ID (Name des Feldes)
                        f_id = annot["/T"].strip("()")
                        if f_id in werte_mapping:
                            val = werte_mapping[f_id]
                            # Haken setzen
                            if isinstance(val, NameObject):
                                annot.update({
                                    NameObject("/V"): val,
                                    NameObject("/AS"): val
                                })
                            # Text setzen
                            else:
                                annot.update({
                                    NameObject("/V"): create_string_object(val)
                                })
            writer.add_page(page)

    # NeedAppearances setzen (für die Sichtbarkeit im Handy)
    if "/AcroForm" not in writer.root_object:
        writer.root_object.update({NameObject("/AcroForm"): writer._add_object({})})
    writer.root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})

    with open(ziel_pfad, "wb") as output_file:
        writer.write(output_file)

    return ziel_pfad