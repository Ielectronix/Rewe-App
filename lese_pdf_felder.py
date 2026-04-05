import pypdf

def lese_pdf_felder(dateipfad):
    print(f"\n🔍 Analysiere PDF: {dateipfad}")
    print("=" * 60)
    
    try:
        reader = pypdf.PdfReader(dateipfad)
        felder_gefunden = False
        
        for page in reader.pages:
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    obj = annot.get_object()
                    
                    if "/T" in obj:
                        felder_gefunden = True
                        name = obj["/T"]
                        typ = obj.get("/FT", "Unbekannt")
                        
                        if typ == "/Btn":
                            print(f"Checkbox ID: '{name}'")
                            if "/AP" in obj and "/N" in obj["/AP"]:
                                werte = list(obj["/AP"]["/N"].keys())
                                ein_wert = [w for w in werte if w != "/Off"]
                                
                                if ein_wert:
                                    print(f"    🟢 WICHTIG! Der Haken-Code lautet: {ein_wert[0]}")
                                else:
                                    print("    🟡 Konnte Haken-Code nicht eindeutig ermitteln.")
                            else:
                                print("    🔵 Standard Checkbox (vermutlich '/Yes')")
                            print("-" * 50)
                            
        if not felder_gefunden:
            print("Keine Formularfelder in dieser PDF gefunden!")
            
    except FileNotFoundError:
        print(f"FEHLER: Die Datei '{dateipfad}' wurde nicht gefunden.")
    except Exception as e:
        print(f"FEHLER: {e}")

# ==========================================
# TRAGE HIER DEN NAMEN DER PDF EIN:
# ==========================================
meine_pdf = "okz-og.pdf"

if __name__ == "__main__":
    lese_pdf_felder(meine_pdf)
