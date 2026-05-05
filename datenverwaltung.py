import json
import os

# ==========================================
# 1. TOUREN & DATEN (SICHER IM DOWNLOAD-ORDNER)
# Diese Daten überleben es, wenn die App "gelöscht" wird!
# ==========================================
if os.name == 'nt':
    base_folder = os.path.join(os.path.expanduser('~'), 'Desktop', 'Rewe_Monitoring')
else:
    base_folder = "/storage/emulated/0/Download/Rewe_Monitoring"

os.makedirs(base_folder, exist_ok=True)

SPEICHER_DATEI = os.path.join(base_folder, "meine_monitoring_daten.json")
BENUTZER_DATEI = os.path.join(base_folder, "benutzer_daten.json")
VORLAGEN_DATEI = os.path.join(base_folder, "tour_vorlagen.json")

def lade_maerkte():
    if os.path.exists(SPEICHER_DATEI):
        with open(SPEICHER_DATEI, "r", encoding="utf-8") as d: return json.load(d)
    return []

def speichere_maerkte(liste):
    with open(SPEICHER_DATEI, "w", encoding="utf-8") as d: json.dump(liste, d)

def lade_benutzer():
    if os.path.exists(BENUTZER_DATEI):
        with open(BENUTZER_DATEI, "r", encoding="utf-8") as d:
            daten = json.load(d)
            return daten.get("vorname", ""), daten.get("zuname", "")
    return "", ""

def speichere_benutzer(v, z):
    with open(BENUTZER_DATEI, "w", encoding="utf-8") as d: 
        json.dump({"vorname": v, "zuname": z}, d)

def lade_vorlagen():
    if os.path.exists(VORLAGEN_DATEI):
        with open(VORLAGEN_DATEI, "r", encoding="utf-8") as d: return json.load(d)
    return {}

def speichere_vorlagen(daten):
    with open(VORLAGEN_DATEI, "w", encoding="utf-8") as d: json.dump(daten, d)


# ==========================================
# 2. PIN-DATEN (INTERNER APP-TRESOR)
# Diese Daten werden absichtlich gelöscht, wenn man "App Daten löschen" drückt!
# ==========================================
PIN_DATEI = "mitarbeiter_pins.json" 

def hole_alle_benutzer():
    if os.path.exists(PIN_DATEI):
        try:
            with open(PIN_DATEI, "r", encoding="utf-8") as d: return json.load(d)
        except: pass
    return {}

def registriere_neuen_benutzer(name, pin):
    alle = hole_alle_benutzer()
    name = str(name).strip()
    pin = str(pin).strip()
    
    if not name or len(pin) != 4 or not pin.isdigit():
        return False, "Name fehlt oder PIN ist nicht 4-stellig!"
    if pin in alle:
        return False, "Diese PIN ist schon vergeben!"
    
    alle[pin] = name
    try:
        with open(PIN_DATEI, "w", encoding="utf-8") as d:
            json.dump(alle, d, ensure_ascii=False, indent=4)
        return True, f"Mitarbeiter {name} erfolgreich angelegt!"
    except:
        return False, "Fehler beim Speichern!"

def authentifiziere_benutzer(pin):
    alle = hole_alle_benutzer()
    pin = str(pin).strip()
    return alle.get(pin)