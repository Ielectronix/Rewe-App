import flet as ft
import os
import datetime
import shutil
import json 

# --- KONFIGURATION ---
LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")
THEME_COLOR = "#4CAF50" # Bilacon Grün
BG_COLOR = "#050a05"    # Dunkler Hintergrund

def main(page: ft.Page):
    page.title = "Bilacon Monitoring"
    page.bgcolor = BG_COLOR
    page.scroll = "auto"
    page.padding = 10
    
    # Haupt-Spalte
    ansicht = ft.Column(spacing=20, horizontal_alignment="center")
    page.add(ft.SafeArea(ansicht))

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # --- DESIGN-FUNKTIONEN (BASIEREND AUF DASHBOARD-STIL) ---
        
        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Icon("business", color=THEME_COLOR, size=50)

        # Dieser Button-Typ hat im Dashboard funktioniert:
        def dashboard_style_button(text, on_click, farbe=THEME_COLOR):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", color="white", size=14),
                on_click=on_click,
                bgcolor=farbe,
                width=300,
                height=50
            )

        def nav_leiste(active_tab):
            def make_btn(text, target_func, is_active):
                return ft.Container(
                    expand=1,
                    content=ft.ElevatedButton(
                        content=ft.Text(text, size=10, color="white"),
                        on_click=lambda e: target_func(),
                        bgcolor="#1b5e20" if is_active else "#111a11"
                    )
                )
            return ft.Row(
                controls=[
                    make_btn("🚚 TOUREN", zeige_dashboard, active_tab == "touren"),
                    make_btn("📤 SENDEN", zeige_postausgang, active_tab == "senden"),
                    make_btn("🗄️ ARCHIV", zeige_archiv, active_tab == "archiv")
                ],
                alignment="center", spacing=5
            )

        # ==========================================
        # 1. REGISTRIERUNG (Dashboard-Layout-Stil)
        # ==========================================
        def zeige_registrierung():
            ansicht.controls.clear()
            
            # Eingabefelder im stabilen Design
            name_in = ft.TextField(label="Vorname Nachname", border_color=THEME_COLOR, color="white", bgcolor="#000000")
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type="number", border_color=THEME_COLOR, color="white", bgcolor="#000000", max_length=4)
            fehler = ft.Text("", color="red")

            def reg_check(e):
                if not name_in.value or len(pin_in.value) < 4:
                    fehler.value = "⚠️ Bitte Name und 4-stellige PIN angeben!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler.value = f"⚠️ {msg}"; page.update()

            # Wir bauen die Seite wie eine Dashboard-Karte auf
            ansicht.controls.append(ft.Container(height=20))
            ansicht.controls.append(get_logo_bild())
            ansicht.controls.append(ft.Text("MONITORING APP", size=22, weight="bold", color=THEME_COLOR))
            
            # Die Eingabe-Box
            reg_box = ft.Container(
                content=ft.Column([
                    ft.Text("Profil einrichten", size=16, color="white70"),
                    name_in, 
                    pin_in, 
                    fehler,
                    dashboard_style_button("PROFIL ERSTELLEN", reg_check)
                ], spacing=15, horizontal_alignment="center"),
                bgcolor="#111a11", padding=20, border_radius=15, border=ft.border.all(1, "#333333")
            )
            ansicht.controls.append(reg_box)
            page.update()

        # ==========================================
        # 2. LOGIN (Dashboard-Layout-Stil)
        # ==========================================
        def zeige_login():
            ansicht.controls.clear()
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", border_color=THEME_COLOR, color="white", bgcolor="#000000", text_align="center")
            fehler = ft.Text("", color="red")

            def login_check(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    v, z = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(v, z) 
                    zeige_dashboard()
                else:
                    fehler.value = "⚠️ PIN falsch!"; page.update()

            ansicht.controls.append(ft.Container(height=50))
            ansicht.controls.append(get_logo_bild())
            
            login_box = ft.Container(
                content=ft.Column([
                    ft.Text("Anmeldung", size=18, weight="bold", color=THEME_COLOR),
                    pin_in, fehler,
                    dashboard_style_button("EINLOGGEN", login_check)
                ], spacing=20, horizontal_alignment="center"),
                bgcolor="#111a11", padding=20, border_radius=15, border=ft.border.all(1, "#333333")
            )
            ansicht.controls.append(login_box)
            page.update()

        # ==========================================
        # 3. DASHBOARD (Originaler stabiler Code)
        # ==========================================
        def zeige_dashboard():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            
            header = ft.Row([
                ft.Text("BILACON", weight="bold", color=THEME_COLOR, size=20),
                ft.Text(f"👤 {v}", color="white70")
            ], alignment="spaceBetween")
            
            ansicht.controls.append(ft.Container(header, padding=10))
            ansicht.controls.append(nav_leiste("touren"))
            
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Keine Touren vorhanden.", color="white24", italic=True))
            else:
                for i, m in enumerate(maerkte):
                    txt = m.get("adresse") or m.get("marktnummer") or f"Tour {i+1}"
                    ansicht.controls.append(ft.Container(
                        bgcolor="#111a11", padding=10, border_radius=10, width=400,
                        border=ft.border.all(1, "#222222"),
                        content=ft.Row([
                            ft.Text(txt, color="white", size=13, expand=True),
                            ft.IconButton("edit", icon_color="#2196F3", on_click=lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx)),
                            ft.IconButton("delete", icon_color="#F44336", on_click=lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()))
                        ])
                    ))
            
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(dashboard_style_button("➕ NEUE TOUR STARTEN", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"))
            page.update()

        # Postausgang & Archiv (vereinfacht)
        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste("senden"))
            ansicht.controls.append(ft.Text("Postausgang folgt...", color="white54"))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste("archiv"))
            ansicht.controls.append(ft.Text("Archiv folgt...", color="white54"))
            page.update()

        # Start
        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        ansicht.controls.append(ft.Text(f"Fehler: {e}", color="red"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)