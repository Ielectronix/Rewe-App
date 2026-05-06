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
    page.padding = 10
    
    # Die Spalte passt sich jetzt flexibel an
    ansicht = ft.Column(spacing=20, horizontal_alignment="center")
    page.add(ft.SafeArea(ansicht))

    share_obj = ft.Share() if page.platform in ["android", "ios"] else None

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def get_logo_bild(w=200, h=100):
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=w, height=h, fit="contain")
            return ft.Icon("business", color="#4CAF50", size=50)

        # --- DEINE ORIGINALEN BUTTON-STYLES (SICHER UMGESETZT) ---

        def leucht_button(text_inhalt, on_click, color="#4CAF50"):
            return ft.ElevatedButton(
                content=ft.Text(text_inhalt, color=color, weight="bold", size=16),
                on_click=on_click, bgcolor="#0b1a0b",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), side=ft.BorderSide(width=2, color=color), padding=20),
            )

        def nav_leiste(active_tab="touren"):
            def make_btn(text_inhalt, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.Container(
                    expand=1,
                    content=ft.ElevatedButton(
                        content=ft.Text(text_inhalt, size=12, weight="bold", color="white"),
                        on_click=on_click,
                        bgcolor="#1b5e20" if is_active else "#111a11",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10)
                    )
                )
            return ft.Row(alignment="center", spacing=5, controls=[
                make_btn("🚚 TOUREN", "touren", lambda e: zeige_dashboard()),
                make_btn("📤 SENDEN", "senden", lambda e: zeige_postausgang()),
                make_btn("🗄️ ARCHIV", "archiv", lambda e: zeige_archiv())
            ])

        def action_btn(text_inhalt, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text_inhalt, size=16, weight="bold", color="white"),
                on_click=on_click, bgcolor=farbe,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25), padding=ft.padding.symmetric(horizontal=20, vertical=15)),
                width=350, height=55
            )

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#111a11", color=farbe, style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0), width=45, height=45)

        # ==========================================
        # LOGIN & REGISTRIERUNG
        # ==========================================
        def zeige_registrierung():
            ansicht.controls.clear()
            name_in = ft.TextField(label="Vorname Nachname", border_color="#4CAF50", color="white", label_style=ft.TextStyle(color="white"))
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type="number", border_color="#4CAF50", color="white", max_length=4, label_style=ft.TextStyle(color="white"))
            fehler = ft.Text("", color="red", weight="bold")

            def do_reg(e):
                if not name_in.value or not pin_in.value:
                    fehler.value = "⚠️ Bitte alles ausfüllen!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler.value = msg; page.update()

            ansicht.controls.append(ft.Container(height=40))
            ansicht.controls.append(get_logo_bild())
            ansicht.controls.append(ft.Container(
                content=ft.Column([
                    ft.Text("Profil einrichten", size=20, color="#4CAF50", weight="bold"),
                    name_in, pin_in, fehler,
                    leucht_button("PROFIL ERSTELLEN", do_reg)
                ], horizontal_alignment="center", spacing=15),
                bgcolor="#111a11", padding=25, border_radius=15, border=ft.border.all(1, "#333333"), width=380
            ))
            page.update()

        def zeige_login():
            ansicht.controls.clear()
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", border_color="#4CAF50", color="white", text_align="center", label_style=ft.TextStyle(color="white"))
            fehler = ft.Text("", color="red", weight="bold")

            def do_login(e):
                try:
                    name = authentifiziere_benutzer(pin_in.value)
                    if name:
                        v, z = (name.split(" ", 1) + [""])[:2]
                        speichere_benutzer(v, z)
                        zeige_dashboard()
                    else:
                        fehler.value = "⚠️ PIN falsch!"; page.update()
                except Exception as ex:
                    fehler.value = f"Fehler: {ex}"; page.update()

            ansicht.controls.append(ft.Container(height=80))
            ansicht.controls.append(get_logo_bild())
            ansicht.controls.append(ft.Container(
                content=ft.Column([
                    ft.Text("Mitarbeiter Login", size=20, color="#4CAF50", weight="bold"),
                    pin_in, fehler,
                    leucht_button("EINLOGGEN", do_login)
                ], horizontal_alignment="center", spacing=20),
                bgcolor="#111a11", padding=25, border_radius=15, border=ft.border.all(1, "#333333"), width=380
            ))
            page.update()

        # ==========================================
        # 3. DASHBOARD (RESTAURIERTES DESIGN)
        # ==========================================
        def zeige_dashboard():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            name_str = f"{v} {z}".strip()
            
            # Kopfzeile wie im Original
            header = ft.Row([
                ft.Text("BILACON", size=22, weight="bold", color="#4CAF50"),
                ft.Row([ft.Icon("person", color="#2196F3"), ft.Text(name_str, color="white", weight="bold")], spacing=5)
            ], alignment="spaceBetween")
            
            ansicht.controls.append(ft.Container(content=header, padding=ft.padding.only(top=10, left=15, right=15)))
            ansicht.controls.append(nav_leiste("touren"))
            
            # Status-Text
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=20, weight="bold", color="white"))
            
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Keine Touren geplant.", color="white54", italic=True))
            else:
                for i, m in enumerate(maerkte):
                    txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                    # Flexible Breite (max 400 für Tablet, passt sich auf Handy an)
                    ansicht.controls.append(ft.Container(
                        bgcolor="#111a11", padding=15, border_radius=15, width=380, 
                        border=ft.border.all(1, "#333333"), 
                        content=ft.Row([
                            ft.Text(txt, color="white", weight="bold", size=14, expand=True),
                            small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                            small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                        ])
                    ))
                    
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(action_btn("➕ NEUEN TAG STARTEN", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"))
            page.update()

        # ... (Restliche Funktionen)
        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste("senden"))
            ansicht.controls.append(ft.Text("Postausgang geladen.", color="white"))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste("archiv"))
            ansicht.controls.append(ft.Text("Archiv geladen.", color="white"))
            page.update()

        # START
        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        ansicht.controls.append(ft.Text(f"Fehler: {e}", color="red"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)