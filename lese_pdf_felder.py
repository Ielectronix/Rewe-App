import pypdf

def lese_pdf_ids(pdf_pfad):
    print(f"Lese PDF ein: {pdf_pfad}\n" + "="*40)
    
    try:
        reader = pypdf.PdfReader(pdf_pfad)
        felder = reader.get_fields()
        
        if felder:
            zaehler = 0
            for feld_name, feld_daten in felder.items():
                zaehler += 1
                # Holt den Typ des Feldes (z.B. /Tx für Text, /Btn für Button/Checkbox, /Ch für Dropdown)
                feld_typ = feld_daten.get("/FT", "Unbekannt")
                
                print(f"ID: '{feld_name}'  -->  Typ: {feld_typ}")
                
            print("="*40)
            print(f"FERTIG! {zaehler} Felder gefunden.")
        else:
            print("Keine ausfüllbaren Formularfelder in dieser PDF gefunden!")
            
    except FileNotFoundError:
        print(f"FEHLER: Die Datei '{pdf_pfad}' wurde nicht gefunden.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

# === HIER DEINEN DATEINAMEN EINTRAGEN ===
meine_pdf_datei = "okz-hfm.pdf" # Passe den Namen an deine PDF an!

if __name__ == "__main__":
    lese_pdf_ids(meine_pdf_datei)