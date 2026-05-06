import json
import os

# --- NEU: Interner Speicher ---
# Dieser Ordner gehört nur der App. Wird die App gelöscht, ist alles restlos weg.
# Android blockiert hier absolut nichts mehr!
base_folder = "app_daten"
os.makedirs(base_folder, exist_ok=True)

SPEICHER_DATEI = os.path.join(base_folder, "meine_monitoring_daten.json")
BENUTZER_DATEI = os.path.join(base_folder, "benutzer_daten.json")
VORLAGEN_DATEI = os.path.join(base_folder, "tour_vorlagen.json")
PIN_DATEI = os.path.join(base_folder, "mitarbeiter_pins.json") 

def lade_maerkte():
    if os.path.exists(SPEICHER_DATEI):
        try:
            with open(SPEICHER_DATEI, "r", encoding="utf-8") as d: return json.load(d)
        except: return []
    return []

def speichere_maerkte(liste):
    with open(SPEICHER_DATEI, "w", encoding="utf-8") as d: json.dump(liste, d)

def lade_benutzer():
    if os.path.exists(BENUTZER_DATEI):
        try:
            with open(BENUTZER_DATEI, "r", encoding="utf-8") as d:
                daten = json.load(d)
                return daten.get("vorname", ""), daten.get("zuname", "")
        except: return "", ""
    return "", ""

def speichere_benutzer(v, z):
    with open(BENUTZER_DATEI, "w", encoding="utf-8") as d: 
        json.dump({"vorname": v, "zuname": z}, d)

def hole_alle_benutzer():
    if os.path.exists(PIN_DATEI):
        try:
            with open(PIN_DATEI, "r", encoding="utf-8") as d: return json.load(d)
        except: pass
    return {}

def registriere_neuen_benutzer(name, pin):
    alle = hole_alle_benutzer()
    if pin in alle: return False, "PIN ist bereits vergeben!"
    alle[pin] = name
    try:
        with open(PIN_DATEI, "w", encoding="utf-8") as d:
            json.dump(alle, d, ensure_ascii=False, indent=4)
        return True, "Erfolg"
    except Exception as e:
        return False, f"Fehler beim Speichern: {e}"

def authentifiziere_benutzer(pin):
    alle = hole_alle_benutzer()
    return alle.get(pin)