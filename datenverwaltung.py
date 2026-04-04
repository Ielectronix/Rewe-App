import json, os

SPEICHER_DATEI = "meine_monitoring_daten.json"
BENUTZER_DATEI = "benutzer_daten.json"
VORLAGEN_DATEI = "tour_vorlagen.json"

def lade_maerkte():
    if os.path.exists(SPEICHER_DATEI):
        with open(SPEICHER_DATEI, "r", encoding="utf-8") as d: return json.load(d)
    return []

def speichere_maerkte(liste):
    with open(SPEICHER_DATEI, "w", encoding="utf-8") as d: json.dump(liste, d)

def lade_benutzer():
    if os.path.exists(BENUTZER_DATEI):
        with open(BENUTZER_DATEI, "r", encoding="utf-8") as d:
            daten = json.load(d); return daten.get("vorname", ""), daten.get("zuname", "")
    return "", ""

def speichere_benutzer(v, z):
    with open(BENUTZER_DATEI, "w", encoding="utf-8") as d: json.dump({"vorname": v, "zuname": z}, d)

def lade_vorlagen():
    if os.path.exists(VORLAGEN_DATEI):
        with open(VORLAGEN_DATEI, "r", encoding="utf-8") as d: return json.load(d)
    return {}

def speichere_vorlagen(daten):
    with open(VORLAGEN_DATEI, "w", encoding="utf-8") as d: json.dump(daten, d)