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
    page.scroll = "auto"

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

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Text("LOGO", color="white")

        # ==========================================
        # DEIN DESIGN: BUTTONS & NEON
        # ==========================================
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

        def nav_leiste(active_tab="touren"):
            def make_btn(text_inhalt, tab_id, on_click):
                is_active = (active_tab == tab_id)
                rand_farbe = "#4CAF50" if is_active else "#333333"
                hintergrund = "#0b1a0b" if is_active else "#111a11"
                return ft.ElevatedButton(
                    content=ft.Text(text_inhalt, size=11, weight="bold", color="white"),
                    on_click=on_click,
                    bgcolor=hintergrund,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10, side=ft.BorderSide(width=1.5, color=rand_farbe))
                )
            # WICHTIG: wrap=True verhindert den grauen Balken, falls das Handy schmal ist!
            return ft.Row(
                alignment=ft.MainAxisAlignment.CENTER, 
                spacing=5, 
                wrap=True, 
                controls=[
                    make_btn("🚚 TOUREN", "touren", lambda e: zeige_dashboard()),
                    make_btn("📤 SENDEN", "senden", lambda e: zeige_postausgang()),
                    make_btn("🗄️ ARCHIV", "archiv", lambda e: zeige_archiv())
                ]
            )

        def action_btn(text_inhalt, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text_inhalt, size=15, weight="bold", color=farbe),
                on_click=on_click, bgcolor="#0b1a0b",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25), padding=ft.padding.symmetric(horizontal=20, vertical=15), side=ft.BorderSide(width=2, color=farbe))
            )

        def list_action_btn(text_inhalt, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text_inhalt, size=11, weight="bold", color=farbe),
                on_click=on_click, bgcolor="#0b1a0b",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=ft.padding.symmetric(horizontal=10, vertical=8), side=ft.BorderSide(width=1.5, color=farbe))
            )

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=14), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=40, height=40)


        # ==========================================
        # 1. REGISTRIERUNG
        # ==========================================
        def zeige_registrierung():
            page.clean()
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
            page.clean()
            bereinige_archiv()
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
        # 3. DASHBOARD (Vollständig & Absturzsicher)
        # ==========================================
        def zeige_dashboard():
            page.clean()
            v, z = lade_benutzer()
            name_str = f"{v} {z}".strip()
            
            # WICHTIG: wrap=True verhindert Absturz bei zu langen Namen!
            header = ft.Row([
                ft.Text("BILACON", size=20, weight="bold", color="#4CAF50"),
                ft.Row([ft.Icon("person", color="#2196F3", size=18), ft.Text(name_str, color="white", weight="bold")], wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
            
            ansicht = ft.Column(spacing=20)
            ansicht.controls.append(ft.Container(height=5))
            ansicht.controls.append(header)
            ansicht.controls.append(nav_leiste("touren"))
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=18, weight="bold", color="white"))
            
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Keine Touren geplant.", color="white54", italic=True))
            else:
                for i, m in enumerate(maerkte):
                    txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                    ansicht.controls.append(ft.Container(
                        bgcolor="#111a11", padding=15, border_radius=15, border=ft.border.all(1, "#333333"), 
                        content=ft.Row([
                            ft.Text(txt, color="white", weight="bold", size=13, expand=True, max_lines=2),
                            small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                            small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                        ])
                    ))
                    
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(ft.Row([
                action_btn("➕ NEUEN TAG STARTEN", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3")
            ], alignment=ft.MainAxisAlignment.CENTER))
            
            page.add(ansicht)

        # ==========================================
        # 4. POSTAUSGANG
        # ==========================================
        def zeige_postausgang():
            page.clean()
            v, z = lade_benutzer()
            name_str = f"{v} {z}".strip()
            
            header = ft.Row([
                ft.Text("POSTAUSGANG", size=20, weight="bold", color="#4CAF50"),
                ft.Row([ft.Icon("person", color="#2196F3", size=18), ft.Text(name_str, color="white", weight="bold")], wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
            
            ansicht = ft.Column(spacing=20)
            ansicht.controls.append(ft.Container(height=5))
            ansicht.controls.append(header)
            ansicht.controls.append(nav_leiste("senden"))
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=18, weight="bold", color="white"))
            
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
                                    bgcolor="#111a11", padding=10, border_radius=15, border=ft.border.all(1, "#333333"),
                                    content=ft.Row([
                                        ft.Text(anzeige_text, color=farbe, size=11, expand=True, weight=text_gewicht, max_lines=2),
                                        list_action_btn("📤 Senden", teilen_jetzt, "#2196F3"),
                                        small_btn("🗑️", rm, "#F44336")
                                    ])
                                )
                            )
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte zum Senden.", color="white54"))
            
            page.add(ansicht)

        # ==========================================
        # 5. ARCHIV
        # ==========================================
        def zeige_archiv():
            page.clean()
            v, z = lade_benutzer()
            name_str = f"{v} {z}".strip()
            
            header = ft.Row([
                ft.Text("ARCHIV", size=20, weight="bold", color="#4CAF50"),
                ft.Row([ft.Icon("person", color="#2196F3", size=18), ft.Text(name_str, color="white", weight="bold")], wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
            
            ansicht = ft.Column(spacing=20)
            ansicht.controls.append(ft.Container(height=5))
            ansicht.controls.append(header)
            ansicht.controls.append(nav_leiste("archiv"))
            ansicht.controls.append(ft.Text("Archiv (Letzte 14 Tage)", size=18, weight="bold", color="white"))
            
            email_val = "registration-mibi.ber@tentamus.com"
            ansicht.controls.append(ft.Container(bgcolor="#111a11", padding=15, border_radius=15, border=ft.border.all(1, "#333333"), content=ft.Column([ 
                ft.Text("E-MAIL KOPIEREN:", color="#FF9800", weight="bold", size=13), 
                ft.Text(email_val, color="white", size=12, selectable=True)
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
                                    bgcolor="#111a11", padding=10, border_radius=15, border=ft.border.all(1, "#333333"),
                                    content=ft.Row([
                                        ft.Text(anzeige_text, color=farbe, size=11, expand=True, weight=text_gewicht, max_lines=2), 
                                        list_action_btn("📤 Senden", teilen_archiv, "#2196F3")
                                    ])
                                )
                            )
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="white54"))
            
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
