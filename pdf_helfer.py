from pypdf import PdfReader, PdfWriter
import os
from config import PDF_IDS_STAMMDATEN, OUTPUT_ORDNER

def stamm_daten_pdf_erstellen(daten_dict, vorlagen_pfad_root, dateiname="Fertig_Stammdaten.pdf"):
    # Wir suchen die Vorlage in dem vom User gewählten Ordner
    vorlagen_datei = os.path.join(vorlagen_pfad_root, "stammdaten.pdf")
    output_pfad = os.path.join(OUTPUT_ORDNER, dateiname)

    if not os.path.exists(vorlagen_datei):
        return False, f"Datei 'stammdaten.pdf' wurde im gewählten Ordner nicht gefunden!\nPfad: {vorlagen_datei}"

    try:
        reader = PdfReader(vorlagen_datei)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        # Mapping der App-Felder auf PDF-IDs
        pdf_felder_werte = {}
        if "marktnummer" in daten_dict:
            pdf_felder_werte[PDF_IDS_STAMMDATEN["marktnummer"]] = daten_dict["marktnummer"]
        if "probenehmer" in daten_dict:
            pdf_felder_werte[PDF_IDS_STAMMDATEN["probenehmer"]] = daten_dict["probenehmer"]
        if "datum" in daten_dict:
            pdf_felder_werte[PDF_IDS_STAMMDATEN["datum"]] = daten_dict["datum"]
        if daten_dict.get("lims_haken"):
            pdf_felder_werte[PDF_IDS_STAMMDATEN["lims_haken"]] = "/Yes"

        writer.update_page_form_field_values(writer.pages[0], pdf_felder_werte)

        with open(output_pfad, "wb") as output_stream:
            writer.write(output_stream)
        
        return True, output_pfad

    except Exception as e:
        return False, str(e)