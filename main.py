import json
import os

# Pfad für Touren (Bleibt erhalten bei Reset)
if os.name == 'nt':
    base_folder = os.path.join(os.path.expanduser('~'), 'Desktop', 'Rewe_Monitoring')
else:
    base_folder = "/storage/emulated/0/Download/Rewe_Monitoring"

os.makedirs(base_folder, exist_ok=True)

SPEICHER_DATEI = os.path.join(base_folder, "meine_monitoring_daten.json")
BENUTZER_DATEI = os.path.join(base_folder, "benutzer_daten.json")
VORLAGEN_DATEI = os.path.join(base_folder, "tour_vorlagen.json")

# PIN-Datei im internen Speicher (Wird bei "Daten löschen" entfernt)
PIN_DATEI = "mitarbeiter_pins.json" 

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
    if pin in alle: return False, "PIN vergeben!"
    alle[pin] = name
    with open(PIN_DATEI, "w", encoding="utf-8") as d:
        json.dump(alle, d, ensure_ascii=False, indent=4)
    return True, "Erfolg"

def authentifiziere_benutzer(pin):
    alle = hole_alle_benutzer()
    return alle.get(pin)