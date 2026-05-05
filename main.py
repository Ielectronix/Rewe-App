import flet as ft
import os
import datetime
import shutil
import json 

# --- KONFIGURATION DES LOGOS ---
LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")

def main(page: ft.Page):
    page.title = "Bilacon Monitoring"
    page.bgcolor = "#050a05" 
    page.scroll = "auto"
    ansicht = ft.Column(spacing=20, horizontal_alignment="center")
    page.add(ft.SafeArea(ansicht))

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Icon("business", color="white54", size=50)

        # Vereinfachter Button ohne komplizierte Rahmen-Logik
        def leucht_button(text, icon_name, on_click):
            return ft.ElevatedButton(
                content=ft.Row([ft.Icon(icon_name), ft.Text(text, weight="bold")], alignment="center"),
                on_click=on_click,
                bgcolor="#4CAF50",
                color="white",
                height=50,
                width=300
            )

        def zeige_registrierung():
            ansicht.controls.clear()
            
            name_in = ft.TextField(
                label="Vorname Nachname", 
                border_color="#4CAF50", 
                color="white",
                focused_border_color="yellow"
            )
            pin_in = ft.TextField(
                label="Wunsch-PIN (4 Zahlen)", 
                password=True, 
                keyboard_type="number", 
                border_color="#4CAF50", 
                color="white",
                max_length=4
            )
            
            fehler_text = ft.Text("", color="red", weight="bold")

            def save_reg(e):
                if not name_in.value or not pin_in.value:
                    fehler_text.value = "⚠️ Bitte alles ausfüllen!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler_text.value = f"⚠️ {msg}"; page.update()

            # Der Container bekommt jetzt eine feste Breite und einfaches Design
            reg_card = ft.Container(
                content=ft.Column([
                    get_logo_bild(), 
                    ft.Text("Monitoring App", size=24, weight="bold", color="#4CAF50"),
                    ft.Divider(height=20, color="white24"), 
                    name_in, 
                    pin_in, 
                    fehler_text,
                    leucht_button("Profil erstellen", "person_add", save_reg)
                ], horizontal_alignment="center", spacing=15, tight=True),
                bgcolor="#111a11", 
                padding=20, 
                border_radius=15, 
                width=350
            )
            
            ansicht.controls.append(ft.Container(content=reg_card, padding=ft.padding.only(top=40)))
            page.update()

        def zeige_login():
            ansicht.controls.clear()
            pin_in = ft.TextField(
                label="Deine PIN", 
                password=True, 
                keyboard_type="number", 
                border_color="#4CAF50", 
                color="white", 
                text_align="center", 
                max_length=4
            )
            fehler_text = ft.Text("", color="red", weight="bold")

            def do_login(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    v, z = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(v, z) 
                    zeige_dashboard()
                else:
                    fehler_text.value = "⚠️ PIN falsch!"; page.update()

            login_card = ft.Container(
                content=ft.Column([
                    ft.Text("Login", size=24, weight="bold", color="#4CAF50"),
                    pin_in, 
                    fehler_text,
                    leucht_button("Einloggen", "lock_open", do_login)
                ], horizontal_alignment="center", spacing=15, tight=True),
                bgcolor="#111a11", padding=20, border_radius=15, width=350
            )
            ansicht.controls.append(ft.Container(content=login_card, padding=ft.padding.only(top=100)))
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            user_info = lade_benutzer()
            header = ft.Row([ft.Text("Bilacon", weight="bold", color="#4CAF50"), ft.Text(user_info[0])], alignment="spaceBetween")
            ansicht.controls.append(ft.Container(header, padding=10))
            ansicht.controls.append(ft.Text("Dashboard aktiv!"))
            page.update()

        benutzer_liste = hole_alle_benutzer()
        if not benutzer_liste: zeige_registrierung()
        else: zeige_login()

    except Exception as e: 
        ansicht.controls.append(ft.Text(f"Fehler: {e}", color="red"))
        page.update()

if __name__ == "__main__": ft.app(target=main)