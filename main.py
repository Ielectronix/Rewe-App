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
    page.padding = 0
    ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ft.SafeArea(ansicht))

    share_obj = ft.Share() if page.platform in ["android", "ios"] else None

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def lade_gesendet():
            try:
                if os.path.exists("gesendet.json"):
                    with open("gesendet.json", "r", encoding="utf-8") as f:
                        return set(json.load(f))
            except: pass
            return set()

        def markiere_als_gesendet(pfad):
            gesendet = lade_gesendet()
            gesendet.add(pfad)
            try:
                with open("gesendet.json", "w", encoding="utf-8") as f:
                    json.dump(list(gesendet), f)
            except: pass

        def get_erweiterte_bases():
            try: return get_all_rewe_bases() + ["/storage/emulated/0/Download/Rewe_Monitoring"]
            except: return []

        def bereinige_archiv():
            heute = datetime.datetime.now()
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                try:
                    for ordner in os.listdir(base):
                        ordner_pfad = os.path.join(base, ordner)
                        if os.path.isdir(ordner_pfad) and ordner != "temp":
                            try:
                                ordner_datum = datetime.datetime.strptime(ordner, '%Y-%m-%d')
                                if (heute - ordner_datum).days > 14: shutil.rmtree(ordner_pfad)
                            except: pass
                except: pass

        def get_logo_bild(w=200, h=100):
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=w, height=h, fit="contain")
            return ft.Container(content=ft.Text("🏢 [LOGO]", color="white54", size=20, weight="bold"), width=w, height=h)

        # ==========================================
        # DIE GEFIXTEN, SICHEREN BUTTONS
        # ==========================================
        # Absolut simple Schreibweise (ohne fehleranfälliges Icon-Layout)
        def leucht_button(text_inhalt, on_click, color="#4CAF50"):
            return ft.ElevatedButton(
                content=ft.Text(text_inhalt, color=color, weight="bold", size=16),
                on_click=on_click, 
                bgcolor="#0b1a0b",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), side=ft.BorderSide(width=2, color=color), padding=20),
            )

        def nav_leiste(active_tab="touren"):
            def make_btn(text, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.Container(
                    expand=1,
                    content=ft.ElevatedButton(
                        content=ft.Text(text, size=13, weight="bold", color="white"),
                        on_click=on_click,
                        bgcolor="#004400" if is_active else "#111a11",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=ft.padding.symmetric(horizontal=2, vertical=10), side=ft.BorderSide(width=1.5, color="#4CAF50"))
                    )
                )
            return ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5, controls=[
                make_btn("🚚 Touren", "touren", lambda e: zeige_dashboard()),
                make_btn("📤 Senden", "senden", lambda e: zeige_postausgang()),
                make_btn("🗄️ Archiv", "archiv", lambda e: zeige_archiv())
            ])

        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold", color=farbe),
                on_click=on_click, bgcolor="#0b1a0b",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25), padding=ft.padding.symmetric(horizontal=20, vertical=15), side=ft.BorderSide(width=2, color=farbe))
            )

        def list_action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=12, weight="bold", color=farbe),
                on_click=on_click, bgcolor="#0b1a0b",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=ft.padding.symmetric(horizontal=12, vertical=8), side=ft.BorderSide(width=1.5, color=farbe))
            )

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=45, height=45)


        # ==========================================
        # 1. REGISTRIERUNG
        # ==========================================
        def zeige_registrierung():
            ansicht.controls.clear()
            logo_bild = ft.Container(content=get_logo_bild(w=200, h=100), margin=ft.margin.only(bottom=20))
            
            name_in = ft.TextField(
                label="Vorname Nachname", border_color="white", color="yellow", bgcolor="#000000",
                label_style=ft.TextStyle(color="white")
            )
            pin_in = ft.TextField(
                label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type=ft.KeyboardType.NUMBER, border_color="white", color="yellow", bgcolor="#000000", max_length=4,
                label_style=ft.TextStyle(color="white")
            )
            fehler_text = ft.Text("", color="red", weight="bold")

            def save_reg(e):
                try:
                    if not name_in.value or not pin_in.value:
                        fehler_text.value = "⚠️ Bitte alle Felder ausfüllen!"; page.update(); return
                    success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                    if success: zeige_login()
                    else: fehler_text.value = f"⚠️ {msg}"; page.update()
                except Exception as ex:
                    fehler_text.value = f"Systemfehler: {ex}"
                    page.update()

            reg_card = ft.Container(
                content=ft.Column([
                    logo_bild, ft.Text("Monitoring App", size=24, weight="bold", color="#4CAF50"),
                    ft.Text("Erstmalige Einrichtung", size=18, color="white70"),
                    ft.Divider(height=20, color="white24"), name_in, pin_in, fehler_text,
                    leucht_button("Profil erstellen", save_reg, "#4CAF50")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                bgcolor="#111a11", padding=30, border_radius=15, border=ft.border.all(2, "#4CAF50"), width=380
            )
            ansicht.controls.append(ft.Container(content=reg_card, padding=ft.padding.only(top=50)))
            page.update()

        # ==========================================
        # 2. LOGIN
        # ==========================================
        def zeige_login():
            ansicht.controls.clear()
            bereinige_archiv() 
            logo_bild = ft.Container(content=get_logo_bild(w=200, h=100), margin=ft.margin.only(bottom=20))
            
            pin_in = ft.TextField(
                label="Deine PIN", password=True, keyboard_type=ft.KeyboardType.NUMBER, border_color="#4CAF50", color="yellow", bgcolor="#000000", text_align=ft.TextAlign.CENTER, text_size=20, max_length=4,
                label_style=ft.TextStyle(color="white")
            )
            fehler_text = ft.Text("", color="red", weight="bold")

            def do_login(e):
                # FEHLER-FANG: Falls das Dashboard abstürzt, wird es hier angezeigt!
                try:
                    name = authentifiziere_benutzer(pin_in.value)
                    if name:
                        teile = name.split(" ", 1)
                        v = teile[0] if len(teile) > 0 else name
                        z = teile[1] if len(teile) > 1 else ""
                        speichere_benutzer(v, z) 
                        zeige_dashboard()
                    else:
                        fehler_text.value = "⚠️ PIN falsch!"; pin_in.value = ""; page.update()
                except Exception as ex:
                    fehler_text.value = f"Dashboard-Fehler: {ex}"
                    page.update()

            login_card = ft.Container(
                content=ft.Column([
                    logo_bild, ft.Text("Monitoring App", size=24, weight="bold", color="#4CAF50"),
                    ft.Text("Mitarbeiter Login", size=18, color="white70"),
                    ft.Divider(height=20, color="white24"), 
                    ft.Text("Bitte gib deine 4-stellige PIN ein:", color="white54"),
                    pin_in, fehler_text, 
                    leucht_button("Einloggen", do_login, "#4CAF50")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                bgcolor="#111a11", padding=30, border_radius=15, border=ft.border.all(2, "#4CAF50"), width=380
            )
            ansicht.controls.append(ft.Container(content=login_card, padding=ft.padding.only(top=50)))
            page.update()

        # ==========================================
        # 3. DASHBOARD (100% DEIN ORIGINAL CODE)
        # ==========================================
        def zeige_dashboard():
            ansicht.controls.clear()
            user_info = lade_benutzer()
            name_str = f"{user_info[0]} {user_info[1]}".strip()
            
            header_content = ft.Row([
                ft.Text("Bilacon Monitoring", size=20, weight="bold", color="#4CAF50"),
                ft.Row([ft.Icon("account_circle", color="white54"), ft.Text(name_str, color="white54", weight="bold")], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
            ansicht.controls.append(ft.Container(content=header_content, padding=ft.padding.only(top=10, left=15, right=15)))
            ansicht.controls.append(ft.Divider(color="white24"))
            ansicht.controls.append(nav_leiste("touren"))
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=20, weight="bold", color="white"))
            
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren angelegt.", color="white54"))
            else:
                for i, m in enumerate(maerkte):
                    txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                    ansicht.controls.append(ft.Container(bgcolor="#111a11", padding=15, border_radius=15, width=700, border=ft.border.all(1, "#333333"), content=ft.Row([
                        ft.Text(txt, color="white", weight="bold", size=14, expand=True, max_lines=2),
                        small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                        small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                    ])))
            ansicht.controls.append(ft.Container(content=action_btn("➕ Neue Tour anlegen", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"), padding=ft.padding.only(bottom=20)))
            page.update()

        # ==========================================
        # 4. POSTAUSGANG (100% DEIN ORIGINAL CODE)
        # ==========================================
        def zeige_postausgang():
            ansicht.controls.clear()
            user_info = lade_benutzer()
            name_str = f"{user_info[0]} {user_info[1]}".strip()
            
            header_content = ft.Row([
                ft.Text("Postausgang", size=20, weight="bold", color="#4CAF50"), 
                ft.Row([ft.Icon("account_circle", color="white54"), ft.Text(name_str, color="white54", weight="bold")], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
            ansicht.controls.append(ft.Container(content=header_content, padding=ft.padding.only(top=10, left=15, right=15)))
            ansicht.controls.append(ft.Divider(color="white24"))
            ansicht.controls.append(nav_leiste("senden"))
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="white"))
            
            heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
            pdfs_gefunden = False
            such_ordner = []
            for base in get_erweiterte_bases():
                such_ordner.append(os.path.join(base, heute_ordner))
                such_ordner.append(base)
            
            gesendet_set = lade_gesendet() 
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    for f in os.listdir(ordner):
                        if f.lower().endswith(".pdf"):
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            ist_gesendet = pfad in gesendet_set
                            farbe = "#4CAF50" if ist_gesendet else "white"
                            text_gewicht = "bold" if ist_gesendet else "normal"
                            anzeige_text = f"✅ {f}" if ist_gesendet else f
                            
                            def teilen_jetzt(e, p=pfad):
                                if share_obj: 
                                    try: page.run_task(lambda: share_obj.share_files([ft.ShareFile(p)], text="Bilacon Bericht"))
                                    except: pass
                                    markiere_als_gesendet(p)
                                    zeige_postausgang() 

                            def rm(e, p=pfad):
                                if os.path.exists(p): os.remove(p)
                                zeige_postausgang()

                            ansicht.controls.append(
                                ft.Container(
                                    bgcolor="#111a11", padding=10, border_radius=15, width=700, border=ft.border.all(1, "#333333"),
                                    content=ft.Row([
                                        ft.Text(anzeige_text, color=farbe, size=12, expand=True, weight=text_gewicht, max_lines=2),
                                        list_action_btn("📤 Senden", teilen_jetzt, "#2196F3"),
                                        small_btn("🗑️", rm, "#F44336")
                                    ])
                                )
                            )
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte zum Senden.", color="white54"))
            page.update()

        # ==========================================
        # 5. ARCHIV (100% DEIN ORIGINAL CODE)
        # ==========================================
        def zeige_archiv():
            ansicht.controls.clear()
            user_info = lade_benutzer()
            name_str = f"{user_info[0]} {user_info[1]}".strip()
            
            header_content = ft.Row([
                ft.Text("Archiv", size=20, weight="bold", color="#4CAF50"), 
                ft.Row([ft.Icon("account_circle", color="white54"), ft.Text(name_str, color="white54", weight="bold")], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
            ansicht.controls.append(ft.Container(content=header_content, padding=ft.padding.only(top=10, left=15, right=15)))
            ansicht.controls.append(ft.Divider(color="white24"))
            ansicht.controls.append(nav_leiste("archiv"))
            ansicht.controls.append(ft.Text("Archiv (Letzte 14 Tage)", size=20, weight="bold", color="white"))
            
            email_val = "registration-mibi.ber@tentamus.com"
            ansicht.controls.append(ft.Container(bgcolor="#111a11", padding=15, border_radius=15, width=700, border=ft.border.all(1, "#333333"), content=ft.Column([ 
                ft.Text("E-MAIL KOPIEREN:", color="#FF9800", weight="bold", size=14), 
                ft.Text(email_val, color="white", size=13, selectable=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)))
            
            pdfs_gefunden = False
            such_ordner = []
            for base in get_erweiterte_bases():
                if os.path.exists(base):
                    such_ordner.append(base)
                    try:
                        for o in os.listdir(base):
                            p = os.path.join(base, o)
                            if os.path.isdir(p) and o != "temp": such_ordner.append(p)
                    except: pass
            
            gesendet_set = lade_gesendet() 
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    p_list = [f for f in os.listdir(ordner) if f.lower().endswith(".pdf")]
                    if p_list:
                        ansicht.controls.append(ft.Text(f"{os.path.basename(ordner)}", color="yellow", weight="bold", size=12))
                        for f in p_list:
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            ist_gesendet = pfad in gesendet_set
                            farbe = "#4CAF50" if ist_gesendet else "white"
                            text_gewicht = "bold" if ist_gesendet else "normal"
                            anzeige_text = f"✅ {f}" if ist_gesendet else f
                            
                            def teilen_archiv(e, p=pfad):
                                if share_obj: 
                                    try: page.run_task(lambda: share_obj.share_files([ft.ShareFile(p)], text="Bilacon Bericht"))
                                    except: pass
                                    markiere_als_gesendet(p)
                                    zeige_archiv()

                            ansicht.controls.append(
                                ft.Container(
                                    bgcolor="#111a11", padding=10, border_radius=15, width=700, border=ft.border.all(1, "#333333"),
                                    content=ft.Row([
                                        ft.Text(anzeige_text, color=farbe, size=12, expand=True, weight=text_gewicht, max_lines=2), 
                                        list_action_btn("📤 Senden", teilen_archiv, "#2196F3")
                                    ])
                                )
                            )
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="white54"))
            page.update()

        # START LOGIK:
        benutzer_liste = hole_alle_benutzer()
        if not benutzer_liste:
            zeige_registrierung()
        else:
            zeige_login()

    except Exception as e: 
        ansicht.controls.append(ft.Text(f"Systemfehler beim Laden der Dateien: {e}", color="red", weight="bold"))
        page.update()

if __name__ == "__main__": 
    ft.app(target=main)