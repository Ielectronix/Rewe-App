import os

# Standard-Ordner für die fertigen Dateien
OUTPUT_ORDNER = "fertige_pdfs"

# Falls der Ordner nicht existiert, legt die App ihn an
if not os.path.exists(OUTPUT_ORDNER):
    os.makedirs(OUTPUT_ORDNER)

# LIMS-MAPPING (Platzhalter, bis du die IDs gescannt hast)
PDF_IDS_STAMMDATEN = {
    "marktnummer": "PLATZHALTER_MARKT",
    "probenehmer": "PLATZHALTER_NAME",
    "datum": "PLATZHALTER_DATUM",
    "lims_haken": "PLATZHALTER_HAKEN"
}
