import os
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, create_string_object, DictionaryObject

def get_all_rewe_bases():
    if os.name == 'nt':
        return [os.path.join(os.path.expanduser('~'), 'Desktop', 'Rewe_Monitoring')]
    else:
        return ["/storage/emulated/0/Download/Rewe_Monitoring", "/storage/emulated/0/Download"]

def create_base_folder():
    for base in get_all_rewe_bases():
        try:
            if not os.path.exists(base): os.makedirs(base, exist_ok=True)
            return base
        except: continue
    raise PermissionError("Schreibrechte fehlen!")

def get_tages_ordner():
    t_ordner = os.path.join(create_base_folder(), datetime.datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(t_ordner, exist_ok=True)
    return t_ordner

def bereite_stammdaten_vor(daten):
    w = {}
    # EXAKTE ZUORDNUNG FÜR SEITE 1
    w["txt_0000_00_Datum"] = daten.get("datum", "")
    w["txt_0000_00_REWE-Adresse"] = f"{daten.get('marktnummer', '')} - {daten.get('adresse', '')}"
    w["txt_0000_00_Kunde"] = daten.get("auftraggeber", "")
    w["txt_0000_00_MA-Name"] = daten.get("mitarbeiter_name", "")
    w["txt_0000_00_ZS-002286"] = daten.get("typ_probenahme", "")
    w["txt_0000_00_Auftrags-Nr"] = daten.get("auftragsnummer", "")
    w["txt_0000_00_ZS-002293"] = daten.get("bemerkung", "")
    return w

def erstelle_bericht(daten):
    assets_dir = "assets"
    pdf_name = "stammdaten_1.pdf"
    pdf_pfad = os.path.join(assets_dir, pdf_name)
    
    if not os.path.exists(pdf_pfad):
        raise FileNotFoundError(f"Test-Datei {pdf_name} fehlt im assets-Ordner!")

    ziel_ordner = get_tages_ordner()
    dateiname = f"TEST_Stammdaten_{daten.get('marktnummer', 'Ohne_Nr')}.pdf"
    ziel_pfad = os.path.join(ziel_ordner, dateiname)

    werte_mapping = bereite_stammdaten_vor(daten)
    reader = PdfReader(pdf_pfad)
    writer = PdfWriter()

    # Seite 1 einlesen und befüllen
    for page in reader.pages:
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                if "/T" in annot:
                    f_id = str(annot["/T"]).strip("()").strip()
                    if f_id in werte_mapping:
                        val = werte_mapping[f_id]
                        annot.update({NameObject("/V"): create_string_object(str(val))})
        writer.add_page(page)

    # Sichtbarkeit für Handys erzwingen
    if "/AcroForm" not in writer.root_object:
        writer.root_object.update({NameObject("/AcroForm"): DictionaryObject()})
    writer.root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})

    with open(ziel_pfad, "wb") as output_file:
        writer.write(output_file)

    return ziel_pfad
