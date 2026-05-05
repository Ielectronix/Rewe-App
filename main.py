import flet as ft
import os
import datetime
import shutil
import json 

# --- FARBEN & ASSETS ---
THEME_GREEN = "#4CAF50"
BG_BLACK = "#050a05"
CARD_BLACK = "#111a11"
LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")

def main(page: ft.Page):
    page.title = "Bilacon Monitoring"
    page.bgcolor = BG_BLACK
    page.scroll = "auto"
    page.padding = 10
    
    ansicht = ft.Column(spacing=20, horizontal_alignment="center")
    page.add(ft.SafeArea(ansicht))

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # --- STABILE DESIGN-BAUSTEINE ---
        def get_logo():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Icon("business", color=THEME_GREEN, size=50)

        def app_input(label, password=False):
            return ft.TextField(
                label=label,
                password=password,
                can_reveal_password=password,
                keyboard_type="number" if "PIN" in label else "text",
                border_color=THEME_GREEN,
                focused_border_color="yellow",
                color="white",
                bgcolor="#000000",
                border_radius=10,
                width=300
            )

        def app_button(text, on_click, farbe=THEME_GREEN):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", color="white", size=14),
                on_click=on_click,
                bgcolor=farbe,
                width=300,
                height=50,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25)) # Schöne runde Ecken wie im Screenshot
            )

        def nav_leiste(active_tab):
            def make_btn(text, tab_id, func):
                is_active = (active_tab == tab_id)
                return ft.Container(
                    expand=1,
                    content=ft.ElevatedButton(
                        content=ft.Text(text, size=11, color="white", weight="bold"),
                        on_click=lambda e: func(),
                        bgcolor="#1b5e20" if is_active else "#111a11",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                )
            return ft.Row(
                controls=[
                    make_btn("🚚 TOUREN", "touren", zeige_dashboard),
                    make_btn("📤 SENDEN", "senden", zeige_postausgang),
                    make_btn("🗄️ ARCHIV", "archiv", zeige_archiv)
                ],
                alignment="center", spacing=5
            )

        # ==========================================
        # SEITE: REGISTRIERUNG
        # ==========================================
        def zeige_registrierung():
            try:
                ansicht.controls.clear()
                name_in = app_input("Vorname Nachname")
                pin_in = app_input("Wunsch-PIN (4 Zahlen)", password=True)
                pin_in.max_length = 4
                fehler = ft.Text("", color="red", weight="bold")

                def reg_check(e):
                    try:
                        if not name_in.value or len(pin_in.value) < 4:
                            fehler.value = "⚠️ Bitte alles korrekt ausfüllen!"; page.update(); return
                        success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                        if success: zeige_login()
                        else: fehler.value = f"⚠️ {msg}"; page.update()
                    except Exception as ex:
                        fehler.value = f"Fehler bei Registrierung: {ex}"
                        page.update()

                ansicht.controls.append(ft.Container(height=20))
                ansicht.controls.append(get_logo())
                
                reg_box = ft.Container(
                    content=ft.Column([
                        ft.Text("Profil einrichten", size=20, weight="bold", color=THEME_GREEN),
                        name_in, pin_in, fehler,
                        app_button("PROFIL ERSTELLEN", reg_check)
                    ], spacing=15, horizontal_alignment="center"),
                    bgcolor=CARD_BLACK, padding=20, border_radius=15, border=ft.border.all(1, "#222222")
                )
                ansicht.controls.append(reg_box)
                page.update()
            except Exception as ex:
                ansicht.controls.append(ft.Text(f"Ladefehler Reg: {ex}", color="red"))
                page.update()

        # ==========================================
        # SEITE: LOGIN
        # ==========================================
        def zeige_login():
            try:
                ansicht.controls.clear()
                pin_in = app_input("PIN", password=True)
                pin_in.text_align = "center"
                fehler = ft.Text("", color="red", weight="bold")

                def login_check(e):
                    try:
                        fehler.value = "Lade..."
                        page.update()
                        
                        name = authentifiziere_benutzer(pin_in.value)
                        if name:
                            v, z = (name.split(" ", 1) + [""])[:2]
                            speichere_benutzer(v, z) 
                            zeige_dashboard()
                        else:
                            fehler.value = "⚠️ PIN falsch!"
                            pin_in.value = ""
                            page.update()
                    except Exception as ex:
                        fehler.value = f"Systemfehler beim Login: {ex}"
                        page.update()

                ansicht.controls.append(ft.Container(height=60))
                ansicht.controls.append(get_logo())
                
                login_box = ft.Container(
                    content=ft.Column([
                        ft.Text("Login", size=20, weight="bold", color=THEME_GREEN),
                        pin_in, fehler,
                        app_button("ANMELDEN", login_check)
                    ], spacing=20, horizontal_alignment="center"),
                    bgcolor=CARD_BLACK, padding=25, border_radius=15, border=ft.border.all(1, "#222222")
                )
                ansicht.controls.append(login_box)
                page.update()
            except Exception as ex:
                ansicht.controls.append(ft.Text(f"Ladefehler Login: {ex}", color="red"))
                page.update()

        # ==========================================
        # SEITE: DASHBOARD
        # ==========================================
        def zeige_dashboard():
            try:
                ansicht.controls.clear()
                v, z = lade_benutzer()
                
                header = ft.Row([
                    ft.Text("BILACON", weight="bold", color=THEME_GREEN, size=20),
                    ft.Text(f"👤 {v}", color="white70")
                ], alignment="spaceBetween")
                
                ansicht.controls.append(ft.Container(header, padding=10))
                ansicht.controls.append(nav_leiste("touren"))
                
                maerkte = lade_maerkte()
                if not maerkte:
                    ansicht.controls.append(ft.Text("Keine Touren geplant.", color="white24", italic=True))
                else:
                    for i, m in enumerate(maerkte):
                        txt = m.get("adresse") or m.get("marktnummer") or f"Tour {i+1}"
                        ansicht.controls.append(ft.Container(
                            bgcolor=CARD_BLACK, padding=12, border_radius=10, width=350,
                            border=ft.border.all(1, "#222222"),
                            content=ft.Row([
                                ft.Text(txt, color="white", size=14, expand=True),
                                ft.IconButton("edit", icon_color="#2196F3", on_click=lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx)),
                                ft.IconButton("delete", icon_color="#F44336", on_click=lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()))
                            ])
                        ))
                
                ansicht.controls.append(ft.Container(height=10))
                ansicht.controls.append(app_button("➕ NEUEN TAG STARTEN", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"))
                page.update()
            except Exception as ex:
                ansicht.controls.append(ft.Text(f"Dashboard Absturz: {ex}", color="red", weight="bold"))
                page.update()

        # ==========================================
        # SEITE: POSTAUSGANG / ARCHIV
        # ==========================================
        def zeige_postausgang():
            try:
                ansicht.controls.clear()
                ansicht.controls.append(nav_leiste("senden"))
                ansicht.controls.append(ft.Text("Berichte zum Senden", weight="bold", size=18, color="white"))
                # PDF Liste hier...
                page.update()
            except Exception as ex:
                ansicht.controls.append(ft.Text(f"Postausgang Absturz: {ex}", color="red"))
                page.update()

        def zeige_archiv():
            try:
                ansicht.controls.clear()
                ansicht.controls.append(nav_leiste("archiv"))
                ansicht.controls.append(ft.Text("Archiv (14 Tage)", weight="bold", size=18, color="white"))
                # Archiv Liste hier...
                page.update()
            except Exception as ex:
                ansicht.controls.append(ft.Text(f"Archiv Absturz: {ex}", color="red"))
                page.update()

        # START LOGIK
        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        ansicht.controls.append(ft.Text(f"Kritischer System-Fehler: {e}", color="red"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
