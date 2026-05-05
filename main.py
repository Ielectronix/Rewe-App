import flet as ft
import os
import datetime
import shutil
import json 

# --- DESIGN ---
THEME_GREEN = "#4CAF50"
BG_BLACK = "#050a05"
LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")

def main(page: ft.Page):
    page.title = "Bilacon Monitoring"
    page.bgcolor = BG_BLACK
    page.scroll = "auto"
    # SafeArea entfernt, da dies oft Abstürze bei alten Versionen verursacht
    
    ansicht = ft.Column(spacing=20, horizontal_alignment="center")
    page.add(ansicht)

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def get_logo():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100)
            return ft.Icon("business", color=THEME_GREEN, size=50)

        def app_button(text, on_click, farbe=THEME_GREEN):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", color="white"),
                on_click=on_click,
                bgcolor=farbe,
                width=300,
                height=50
            )

        # --- SEITEN ---

        def zeige_registrierung():
            ansicht.controls.clear()
            name_in = ft.TextField(label="Vorname Nachname", border_color=THEME_GREEN, color="white")
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type="number", border_color=THEME_GREEN, color="white", max_length=4)
            fehler = ft.Text("", color="red")

            def reg_check(e):
                if not name_in.value or len(pin_in.value) < 4:
                    fehler.value = "⚠️ Bitte alles ausfüllen!"; page.update(); return
                res, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if res: zeige_login()
                else: fehler.value = msg; page.update()

            ansicht.controls.append(ft.Container(height=20))
            ansicht.controls.append(get_logo())
            ansicht.controls.append(ft.Container(
                content=ft.Column([
                    ft.Text("Registrierung", size=20, color=THEME_GREEN),
                    name_in, pin_in, fehler,
                    app_button("PROFIL ERSTELLEN", reg_check)
                ], horizontal_alignment="center", spacing=15),
                bgcolor="#111a11", padding=20, border_radius=10
            ))
            page.update()

        def zeige_login():
            ansicht.controls.clear()
            pin_in = ft.TextField(label="PIN", password=True, keyboard_type="number", border_color=THEME_GREEN, color="white", text_align="center")
            fehler = ft.Text("", color="red")

            def login_check(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    v, z = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(v, z) 
                    zeige_dashboard()
                else:
                    fehler.value = "⚠️ Falsch!"; page.update()

            ansicht.controls.append(ft.Container(height=50))
            ansicht.controls.append(get_logo())
            ansicht.controls.append(ft.Container(
                content=ft.Column([
                    ft.Text("Login", size=20, color=THEME_GREEN),
                    pin_in, fehler,
                    app_button("ANMELDEN", login_check)
                ], horizontal_alignment="center", spacing=20),
                bgcolor="#111a11", padding=20, border_radius=10
            ))
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            ansicht.controls.append(ft.Row([ft.Text("BILACON", color=THEME_GREEN, weight="bold"), ft.Text(v)], alignment="spaceBetween"))
            
            # Nav-Leiste (Ganz simpel)
            ansicht.controls.append(ft.Row([
                ft.TextButton("TOUREN", on_click=lambda e: zeige_dashboard()),
                ft.TextButton("SENDEN", on_click=lambda e: zeige_postausgang()),
                ft.TextButton("ARCHIV", on_click=lambda e: zeige_archiv()),
            ], alignment="center"))

            maerkte = lade_maerkte()
            for i, m in enumerate(maerkte):
                txt = m.get("adresse") or "Tour"
                ansicht.controls.append(ft.Container(
                    content=ft.Row([
                        ft.Text(txt, expand=True),
                        ft.IconButton("edit", on_click=lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx)),
                        ft.IconButton("delete", on_click=lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()))
                    ]),
                    bgcolor="#111a11", padding=10, border_radius=5
                ))
            ansicht.controls.append(app_button("➕ NEUE TOUR", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(ft.TextButton("ZURÜCK", on_click=lambda e: zeige_dashboard()))
            ansicht.controls.append(ft.Text("Postausgang (PDF Liste)"))
            # ... (Hier PDF Liste wie gehabt)
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(ft.TextButton("ZURÜCK", on_click=lambda e: zeige_dashboard()))
            ansicht.controls.append(ft.Text("Archiv (14 Tage)"))
            page.update()

        # START
        users = hole_alle_benutzer()
        if not users: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        # Falls doch ein Fehler passiert, zeigen wir ihn als Text an
        ansicht.controls.append(ft.Text(f"Start-Fehler: {e}", color="red"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)