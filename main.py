import flet as ft
import os
import datetime
import shutil
import json 

LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")

def main(page: ft.Page):
    page.title = "Bilacon Diagnose"
    page.bgcolor = "#050a05" 
    page.scroll = "auto"
    page.padding = 15
    
    # Absolute Basis-Ansicht ohne jeden Schnickschnack
    ansicht = ft.Column(spacing=15)
    page.add(ansicht)

    share_obj = ft.Share() if page.platform in ["android", "ios"] else None

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100)
            return ft.Text("LOGO", color="white")

        # --- DEINE ORIGINAL-BAUSTEINE (Für den Test bereitgehalten) ---
        def nav_leiste():
            return ft.Row(controls=[
                ft.ElevatedButton("TOUREN", bgcolor="#1b5e20", color="white"),
                ft.ElevatedButton("SENDEN", bgcolor="#111a11", color="white"),
                ft.ElevatedButton("ARCHIV", bgcolor="#111a11", color="white")
            ], alignment="center", wrap=True)

        def small_btn(emoji, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji), bgcolor="#0b1a0b", color=farbe, width=45, height=45)

        # ==========================================
        # 1. LOGIN (Standard)
        # ==========================================
        def zeige_login():
            ansicht.controls.clear()
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", color="white")
            fehler = ft.Text("", color="red")

            def do_login(e):
                try:
                    name = authentifiziere_benutzer(pin_in.value)
                    if name:
                        v, z = (name.split(" ", 1) + [""])[:2]
                        speichere_benutzer(v, z)
                        zeige_diagnose_menue() # HIER STARTET JETZT DER SCANNER!
                    else:
                        fehler.value = "PIN falsch!"; page.update()
                except Exception as ex:
                    fehler.value = f"Fehler beim Einloggen: {ex}"; page.update()

            ansicht.controls.append(get_logo_bild())
            ansicht.controls.append(ft.Text("Mitarbeiter Login", size=20, color="#4CAF50"))
            ansicht.controls.append(pin_in)
            ansicht.controls.append(fehler)
            ansicht.controls.append(ft.ElevatedButton("EINLOGGEN", on_click=do_login, bgcolor="#4CAF50", color="white"))
            page.update()

        # ==========================================
        # 2. DER DIAGNOSE-SCANNER (NEU!)
        # ==========================================
        def zeige_diagnose_menue():
            ansicht.controls.clear()
            ansicht.controls.append(ft.Text("🛠️ DIAGNOSE-MODUS AKTIV", color="orange", size=20, weight="bold"))
            ansicht.controls.append(ft.Text("Bitte klicke nacheinander auf die Buttons. Sag mir, bei welchem Schritt der Bildschirm grau wird oder ein Fehler erscheint.", color="white"))
            
            log_ausgabe = ft.Text("Warte auf Eingabe...", color="yellow")

            # --- TEST 1: KOPFZEILE ---
            def test_1_header(e):
                try:
                    v, z = lade_benutzer()
                    header = ft.Row([
                        ft.Text("BILACON", color="#4CAF50", weight="bold"),
                        ft.Text(f"User: {v} {z}", color="white")
                    ], alignment="spaceBetween")
                    ansicht.controls.append(ft.Container(bgcolor="#222222", padding=10, content=header))
                    log_ausgabe.value = "Schritt 1 (Kopfzeile) erfolgreich!"
                    page.update()
                except Exception as ex:
                    log_ausgabe.value = f"FEHLER IN SCHRITT 1: {ex}"; page.update()

            # --- TEST 2: NAVIGATION ---
            def test_2_nav(e):
                try:
                    ansicht.controls.append(ft.Container(bgcolor="#222222", padding=10, content=nav_leiste()))
                    log_ausgabe.value = "Schritt 2 (Navigation) erfolgreich!"
                    page.update()
                except Exception as ex:
                    log_ausgabe.value = f"FEHLER IN SCHRITT 2: {ex}"; page.update()

            # --- TEST 3: TOUREN-LISTE LESE-TEST ---
            def test_3_daten(e):
                try:
                    maerkte = lade_maerkte()
                    log_ausgabe.value = f"Schritt 3 (Daten) erfolgreich! {len(maerkte)} Touren gefunden."
                    page.update()
                except Exception as ex:
                    log_ausgabe.value = f"FEHLER IN SCHRITT 3: {ex}"; page.update()

            # --- TEST 4: TOUREN-KARTEN GRAFIK-TEST ---
            def test_4_karten(e):
                try:
                    maerkte = lade_maerkte()
                    for i, m in enumerate(maerkte):
                        txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                        karte = ft.Container(
                            bgcolor="#111a11", padding=10, border=ft.border.all(1, "white"),
                            content=ft.Row([
                                ft.Text(txt, color="white", expand=True),
                                small_btn("E", "blue"),
                                small_btn("D", "red")
                            ])
                        )
                        ansicht.controls.append(karte)
                    log_ausgabe.value = "Schritt 4 (Karten-Grafik) erfolgreich!"
                    page.update()
                except Exception as ex:
                    log_ausgabe.value = f"FEHLER IN SCHRITT 4: {ex}"; page.update()

            ansicht.controls.append(ft.Divider(color="white"))
            ansicht.controls.append(ft.ElevatedButton("1. Lade Kopfzeile", on_click=test_1_header, bgcolor="blue", color="white"))
            ansicht.controls.append(ft.ElevatedButton("2. Lade Navigation", on_click=test_2_nav, bgcolor="blue", color="white"))
            ansicht.controls.append(ft.ElevatedButton("3. Lade Touren-Daten (ohne Grafik)", on_click=test_3_daten, bgcolor="blue", color="white"))
            ansicht.controls.append(ft.ElevatedButton("4. Lade Touren-Grafik", on_click=test_4_karten, bgcolor="blue", color="white"))
            ansicht.controls.append(ft.Divider(color="white"))
            ansicht.controls.append(log_ausgabe)
            
            page.update()

        # START
        zeige_login()

    except Exception as e:
        ansicht.controls.append(ft.Text(f"Kritischer Start-Fehler: {e}", color="red"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
