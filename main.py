import flet as ft
import os
import json 

LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")

def main(page: ft.Page):
    page.title = "Bilacon"
    page.bgcolor = "#050a05"
    page.padding = 20
    page.scroll = "auto"

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Text("LOGO", color="white")

        # Dein Neon-Button
        def leucht_button(text_inhalt, on_click, color="#4CAF50"):
            return ft.ElevatedButton(
                content=ft.Text(text_inhalt, color=color, weight="bold", size=16),
                on_click=on_click,
                bgcolor="#0b1a0b",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                    side=ft.BorderSide(width=2, color=color),
                    padding=20
                ),
            )

        # ==========================================
        # 1. REGISTRIERUNG
        # ==========================================
        def zeige_registrierung():
            page.clean() # Löscht alles restlos
            name_in = ft.TextField(label="Vorname Nachname", color="white", border_color="#4CAF50")
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type="number", color="white", border_color="#4CAF50", max_length=4)
            fehler = ft.Text("", color="red", weight="bold")

            def do_reg(e):
                if not name_in.value or not pin_in.value:
                    fehler.value = "⚠️ Bitte alles ausfüllen!"
                    page.update()
                    return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success:
                    zeige_login()
                else:
                    fehler.value = msg
                    page.update()

            ansicht = ft.Column(horizontal_alignment="center", spacing=20)
            ansicht.controls.append(ft.Container(height=20))
            ansicht.controls.append(get_logo_bild())
            ansicht.controls.append(ft.Text("Profil einrichten", size=20, color="#4CAF50", weight="bold"))
            ansicht.controls.append(name_in)
            ansicht.controls.append(pin_in)
            ansicht.controls.append(fehler)
            ansicht.controls.append(leucht_button("PROFIL ERSTELLEN", do_reg, "#4CAF50"))

            page.add(ansicht)

        # ==========================================
        # 2. LOGIN
        # ==========================================
        def zeige_login():
            page.clean() # Löscht alles restlos
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", color="white", border_color="#4CAF50", text_align="center", max_length=4)
            fehler = ft.Text("", color="red", weight="bold")

            def do_login(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    v, z = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(v, z)
                    zeige_dashboard()
                else:
                    fehler.value = "⚠️ PIN falsch!"
                    page.update()

            ansicht = ft.Column(horizontal_alignment="center", spacing=20)
            ansicht.controls.append(ft.Container(height=40))
            ansicht.controls.append(get_logo_bild())
            ansicht.controls.append(ft.Text("Mitarbeiter Login", size=20, color="#4CAF50", weight="bold"))
            ansicht.controls.append(pin_in)
            ansicht.controls.append(fehler)
            ansicht.controls.append(leucht_button("EINLOGGEN", do_login, "#4CAF50"))

            page.add(ansicht)

        # ==========================================
        # 3. DASHBOARD (Test-Ansicht)
        # ==========================================
        def zeige_dashboard():
            page.clean() # Löscht die Login-Seite restlos!
            v, z = lade_benutzer()

            ansicht = ft.Column(spacing=20)
            ansicht.controls.append(ft.Text(f"WILLKOMMEN {v}!", size=24, color="#4CAF50", weight="bold"))
            ansicht.controls.append(ft.Text("Der Login hat funktioniert und der Seitenwechsel klappt ohne grauen Balken!", color="white"))
            
            page.add(ansicht)

        # START LOGIK
        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter:
            zeige_registrierung()
        else:
            zeige_login()

    except Exception as e:
        page.add(ft.Text(f"Systemfehler: {e}", color="red"))

if __name__ == "__main__":
    ft.app(target=main)
