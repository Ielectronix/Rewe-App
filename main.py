import flet as ft
import os
import datetime
import shutil
import json 

LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")

def main(page: ft.Page):
    page.title = "Bilacon Monitoring"
    page.bgcolor = "#050a05" 
    page.padding = 20

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Text("LOGO", color="white")

        # ==========================================
        # 1. LOGIN (Bleibt wie er ist)
        # ==========================================
        def zeige_login():
            page.clean()
            ansicht = ft.Column(horizontal_alignment="center", spacing=20)
            
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", color="white", text_align="center")
            fehler = ft.Text("", color="red", weight="bold")

            def do_login(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    v, z = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(v, z)
                    zeige_dashboard() # <-- Hier geht es ins nackte Dashboard!
                else:
                    fehler.value = "⚠️ PIN falsch!"; page.update()

            ansicht.controls.append(ft.Container(height=40))
            ansicht.controls.append(get_logo_bild())
            ansicht.controls.append(ft.Text("Mitarbeiter Login", size=20, color="#4CAF50"))
            ansicht.controls.append(pin_in)
            ansicht.controls.append(fehler)
            ansicht.controls.append(ft.ElevatedButton("EINLOGGEN", on_click=do_login))
            
            page.add(ansicht)

        # ==========================================
        # 2. DAS NACKTE DASHBOARD (Der ultimative Test)
        # ==========================================
        def zeige_dashboard():
            page.clean()
            ansicht = ft.Column() # Eine ganz simple, dumme Spalte. Kein Stretch, kein Align.
            
            v, z = lade_benutzer()
            
            ansicht.controls.append(ft.Text(f"Hallo {v}, willkommen im System!", size=20, color="white"))
            ansicht.controls.append(ft.Text("Wenn du das hier siehst und KEIN grauer Balken da ist, funktioniert der Seitenwechsel perfekt!", color="#4CAF50"))
            ansicht.controls.append(ft.ElevatedButton("Test: Zurück zum Login", on_click=lambda e: zeige_login()))
            
            page.add(ansicht)

        # START
        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter:
            # Notlösung für leere Datenbank (Registrierung übersprungen für diesen Test)
            page.add(ft.Text("Bitte erstelle manuell einen User in der JSON.", color="red"))
        else:
            zeige_login()

    except Exception as e:
        page.add(ft.Text(f"Fehler: {e}", color="red"))

if __name__ == "__main__":
    ft.app(target=main)
