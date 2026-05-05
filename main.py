import flet as ft
import os
import datetime
import shutil
import json 

# --- KONFIGURATION ---
LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")
THEME_COLOR = "#4CAF50"  # Das Bilacon-Grün
BG_COLOR = "#050a05"     # Der dunkle Hintergrund
CARD_BG = "#111a11"      # Hintergrund der Eingabe-Box

def main(page: ft.Page):
    page.title = "Bilacon Monitoring"
    page.bgcolor = BG_COLOR
    page.scroll = "auto"
    page.padding = 0
    
    ansicht = ft.Column(spacing=20, horizontal_alignment="center")
    page.add(ft.SafeArea(ansicht))

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # --- DESIGN-STILE (IDENTISCH ZUR APP) ---
        def get_input_style(label, is_password=False):
            return ft.TextField(
                label=label,
                password=is_password,
                can_reveal_password=is_password,
                keyboard_type="number" if label.count("PIN") else "text",
                border_color=THEME_COLOR,
                focused_border_color="yellow",
                color="white",
                bgcolor="#000000",
                label_style=ft.TextStyle(color="white70"),
                border_radius=10,
                width=300,
                height=60,
                selection_color=THEME_COLOR
            )

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=220, height=110, fit="contain")
            return ft.Icon("business", color=THEME_COLOR, size=50)

        def app_button(text, on_click, color=THEME_COLOR):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", size=16, color="white"),
                on_click=on_click,
                bgcolor=color,
                height=50,
                width=300,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            )

        def nav_leiste(active_tab):
            def make_btn(text, tab_id, target_func):
                is_active = (active_tab == tab_id)
                return ft.Container(
                    expand=1,
                    content=ft.ElevatedButton(
                        content=ft.Text(text, size=11, weight="bold", color="white"),
                        on_click=lambda e: target_func(),
                        bgcolor="#1b5e20" if is_active else "#111a11",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
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
        # 1. REGISTRIERUNG (CI DESIGN)
        # ==========================================
        def zeige_registrierung():
            ansicht.controls.clear()
            name_in = get_input_style("Vorname Nachname")
            pin_in = get_input_style("Wunsch-PIN (4-stellig)", is_password=True)
            pin_in.max_length = 4
            fehler = ft.Text("", color="red", weight="bold")

            def reg_check(e):
                if not name_in.value or len(pin_in.value) < 4:
                    fehler.value = "⚠️ Daten unvollständig!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler.value = f"⚠️ {msg}"; page.update()

            ansicht.controls.append(ft.Container(
                content=ft.Column([
                    get_logo_bild(),
                    ft.Text("Monitoring App", size=26, weight="bold", color=THEME_COLOR),
                    ft.Text("EINRICHTUNG", size=14, color="white54", letter_spacing=2),
                    ft.Divider(color="white10", height=40),
                    name_in, 
                    pin_in, 
                    fehler,
                    ft.Container(height=10),
                    app_button("PROFIL ERSTELLEN", reg_check)
                ], horizontal_alignment="center", spacing=10),
                bgcolor=CARD_BG, padding=35, border_radius=20, 
                border=ft.border.all(1, "#222222"), width=360, margin=ft.margin.only(top=40)
            ))
            page.update()

        # ==========================================
        # 2. LOGIN (CI DESIGN)
        # ==========================================
        def zeige_login():
            ansicht.controls.clear()
            pin_in = get_input_style("PIN eingeben", is_password=True)
            pin_in.text_align = "center"
            pin_in.max_length = 4
            fehler = ft.Text("", color="red", weight="bold")

            def login_check(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    parts = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(parts[0], parts[1])
                    zeige_dashboard()
                else:
                    fehler.value = "⚠️ PIN ist nicht korrekt!"; page.update()

            ansicht.controls.append(ft.Container(
                content=ft.Column([
                    get_logo_bild(),
                    ft.Text("LOGIN", size=26, weight="bold", color=THEME_COLOR),
                    ft.Divider(color="white10", height=40),
                    pin_in, 
                    fehler,
                    ft.Container(height=10),
                    app_button("ANMELDEN", login_check)
                ], horizontal_alignment="center", spacing=10),
                bgcolor=CARD_BG, padding=35, border_radius=20, 
                border=ft.border.all(1, "#222222"), width=360, margin=ft.margin.only(top=100)
            ))
            page.update()

        # ==========================================
        # 3. DASHBOARD & REST (UNVERÄNDERT PROFESSIOELL)
        # ==========================================
        def zeige_dashboard():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            ansicht.controls.append(ft.Container(
                content=ft.Row([
                    ft.Text("BILACON", weight="bold", color=THEME_COLOR, size=20),
                    ft.Text(f"👤 {v}", color="white70")
                ], alignment="spaceBetween"),
                padding=15
            ))
            ansicht.controls.append(ft.Container(nav_leiste("touren"), padding=ft.padding.symmetric(horizontal=10)))
            
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Keine aktiven Touren.", color="white24", italic=True))
            else:
                for i, m in enumerate(maerkte):
                    txt = m.get("adresse") or m.get("marktnummer") or f"Tour {i+1}"
                    ansicht.controls.append(ft.Container(
                        bgcolor=CARD_BG, padding=12, border_radius=12, width=380,
                        border=ft.border.all(1, "#222222"),
                        content=ft.Row([
                            ft.Text(txt, color="white", size=14, expand=True),
                            ft.IconButton("edit", icon_color="#2196F3", on_click=lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx)),
                            ft.IconButton("delete", icon_color="#F44336", on_click=lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()))
                        ])
                    ))
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(app_button("➕ NEUE TOUR STARTEN", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(ft.Container(nav_leiste("senden"), padding=15))
            # ... (Postausgang Logik wie gehabt)
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(ft.Container(nav_leiste("archiv"), padding=15))
            # ... (Archiv Logik wie gehabt)
            page.update()

        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        ansicht.controls.append(ft.Text(f"Fehler: {e}", color="red"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)