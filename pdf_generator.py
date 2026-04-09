import os
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, create_string_object, DictionaryObject

# --- PFAD-LOGIK FÜR ANDROID & PC ---
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
    raise PermissionError("Schreibrechte fehlen! Bitte Android-Berechtigungen prüfen.")

def get_tages_ordner():
    t_ordner = os.path.join(create_base_folder(), datetime.datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(t_ordner, exist_ok=True)
    return t_ordner

# --- PRÄZISE ID-ZUORDNUNG FÜR DEINE PDF ---
def hole_okz_werte(daten, sektion_prefix, prefix_in_pdf, anzahl):
    w = {}
    haken_okz = NameObject('/j') # OKZ Felder in deiner PDF brauchen /j
    for i in range(1, anzahl + 1):
        idx = f"{i:02d}"
        if daten.get(f"{sektion_prefix}_ort_{idx}") or daten.get(f"{sektion_prefix}_objekt_{idx}"):
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002287"] = daten.get(f"{sektion_prefix}_status_{idx}", "")
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002288"] = daten.get(f"{sektion_prefix}_objekt_{idx}", "")
            w[f"txt_{prefix_in_pdf}_{idx}_ZS-002290"] = daten.get(f"{sektion_prefix}_ort_{idx}", "")
            if daten.get(f"{sektion_prefix}_abklatsch_{idx}"): 
                w[f"cb_{prefix_in_pdf}_{idx}_ZS-002294"] = haken_okz
            if daten.get(f"{sektion_prefix}_tupfer_{idx}"): 
                w[f"cb_{prefix_in_pdf}_{idx}_ZS-002295"] = haken_okz
    return w

def bereite_daten_vor(daten):
    w = {}
    h_std = NameObject('/Yes') # Standard-Haken brauchen /Yes

    # STAMMDATEN (Seite 1)
    w["txt_0000_00_MA-Name"] = daten.get("mitarbeiter_name", "")
    w["txt_0000_00_Datum"] = daten.get("datum", "")
    w["txt_0000_00_REWE-Adresse"] = f"{daten.get('marktnummer', '')} - {daten.get('adresse', '')}"
    w["txt_0000_00_Auftrags-Nr"] = daten.get("auftragsnummer", "")
    w["txt_0000_00_Kunde"] = daten.get("auftraggeber", "")
    w["txt_0000_00_ZS-002286"] = daten.get("typ_probenahme", "")
    w["txt_0000_00_ZS-002293"] = daten.get("bemerkung", "")

    # TRINKWASSER (Seite 2-4)
    if daten.get("tw_kalt"):
        w["cb_0001_00"] = h_std
        w["txt_0001_00_PE_ZS-1274"] = daten.get("tw_zeit", "")
        w["txt_0001_00_PE_ZS-002304"] = daten.get("tw_temp", "")
        w["txt_0001_00_PE_ZS-002305"] = daten.get("tw_tempkonst", "")
        w["txt_0001_00_PE_ZS-002281"] = daten.get("tw_entnahmeort", "")
        w["txt_0001_00_PE_ZS-002282"] = daten.get("tw_bemerkung", "")
        if daten.get("tw_cb_pn"): w["cb_0001_00_PE_ZS-002304_PN-Hahn"] = h_std
        if daten.get("cb_auff_unterbau"): w["cb_0001_00_PE_ZS-1268_ Unterbauspeicher [L]"] = h_std

    # HACKFLEISCH GEMISCHT (Seite 6)
    if daten.get("hfm_hack_cb"):
        w["cb_0004_00"] = h_std
        w["txt_0004_00_PE_ZS-002281"] = daten.get("hfm_hack_entnahmeort", "")
        w["txt_0004_00_PE_ZS-002298"] = daten.get("hfm_hack_herstelldatum", "")
        w["txt_0004_00_PE_ZS-002299"] = daten.get("hfm_hack_lief_schwein", "")
        w["txt_0004_00_PE_ZS-002300"] = daten.get("hfm_hack_lief_rind", "")
        w["txt_0004_00_PE_ZS-002301"] = daten.get("hfm_hack_mhd_schwein", "")
        w["txt_0004_00_PE_ZS-002302"] = daten.get("hfm_hack_mhd_rind", "")
        w["txt_0004_00_PE_ZS-002296"] = daten.get("hfm_hack_charge_schwein", "")
        w["txt_0004_00_PE_ZS-002297"] = daten.get("hfm_hack_charge_rind", "")
        w["txt_0004_00_PE_ZS-002304"] = daten.get("hfm_hack_temp", "")

    # OKZ HFM (Seite 10-14)
    if daten.get("hfm_okz_cb"):
        w["cb_0010_00"] = h_std
        w.update(hole_okz_werte(daten, "okz", "0010", 10))

    # CONVENIENCE OG (Seite 15-21)
    if daten.get("og_cb"):
        for i in range(1, 6):
            idx = f"{i:02d}"
            if daten.get(f"og_name_{idx}"):
                w[f"txt_0012_{idx}_ZS-002289"] = daten.get(f"og_name_{idx}")
                w[f"txt_0012_{idx}_ZS-002281"] = daten.get(f"og_ort_{idx}", "")
                w[f"txt_0012_{idx}_ZS-002304"] = daten.get(f"og_temp_{idx}", "")

    if daten.get("og_okz_cb"):
        w["cb_0011_00"] = h_std
        w.update(hole_okz_werte(daten, "og_okz", "0011", 5))

    return w

# --- CHIRURGISCHE GENERIERUNG OHNE VERSCHIEBEN ---
def erstelle_bericht(daten):
    assets_dir = "assets"
    # Wir nutzen deine hochgeladene Datei als Basis
    vorlage_name = "REWE_Neu_2026 (2).pdf"
    vorlage_pfad = os.path.join(assets_dir, vorlage_name)
    
    if not os.path.exists(vorlage_pfad):
        raise FileNotFoundError(f"Vorlage {vorlage_name} fehlt im assets-Ordner!")

    ziel_ordner = get_tages_ordner()
    markt_nr = daten.get("marktnummer", "").strip() or "Ohne_Nummer"
    dateiname = f"REWE_Monitoring_{markt_nr}_{daten.get('datum','').replace('.','_')}.pdf"
    ziel_pfad = os.path.join(ziel_ordner, dateiname)

    werte_mapping = bereite_daten_vor(daten)
    reader = PdfReader(vorlage_pfad)
    writer = PdfWriter()

    # Wir kopieren die Seiten der Vorlage und füllen NUR die Felder aus
    for page in reader.pages:
        writer.add_page(page)

    # Felder im Writer befüllen (IDs bleiben exakt erhalten für LIMS)
    for page in writer.pages:
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                if "/T" in annot:
                    f_id = str(annot["/T"]).strip("()").strip()
                    if f_id in werte_mapping:
                        val = werte_mapping[f_id]
                        if isinstance(val, NameObject):
                            annot.update({NameObject("/V"): val, NameObject("/AS"): val})
                        else:
                            annot.update({NameObject("/V"): create_string_object(str(val))})

    # Sichtbarkeit erzwingen (Wichtig für Handy-Viewer)
    if "/AcroForm" not in writer.root_object:
        writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
    writer.root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})

    with open(ziel_pfad, "wb") as output_file:
        writer.write(output_file)

    return ziel_pfad