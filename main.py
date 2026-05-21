import flet as ft
import os
import datetime
import shutil
import json 

LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")
START_LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent1.png")

def main(page: ft.Page):
    page.title = "Rewe Monitoring"
    page.bgcolor = "#001a00"
    page.scroll = "auto"
    
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER 

    share_obj = ft.Share() if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS] else None

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # ==========================================
        # KUGELSICHERER SPEICHER FÜR GESENDET-STATUS
        # ==========================================
        def lade_gesendet():
            try:
                if page.client_storage.contains_key("gesendet_pdfs"):
                    daten = page.client_storage.get("gesendet_pdfs")
                    if daten: return set(daten)
            except: pass
            return set()

        def markiere_als_gesendet(pfad):
            gesendet = lade_gesendet()
            gesendet.add(pfad)
            try:
                page.client_storage.set("gesendet_pdfs", list(gesendet))
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
                except PermissionError: pass

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Text("LOGO", color="white")

        def get_start_logo_bild():
            if os.path.exists(START_LOGO_PFAD):
                return ft.Image(src=START_LOGO_PFAD, height=80, fit="contain")
            return ft.Text("REWE Monitoring", color="white", weight="bold", size=28)

        def nav_leiste(active_tab="touren"):
            def make_btn(text, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.ElevatedButton(
                    content=ft.Text(text, size=13, weight="bold"),
                    on_click=on_click,
                    bgcolor="#004400" if is_active else "#1a1a1a",
                    color="white",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=10,
                        side=ft.BorderSide(width=1.5, color="#4CAF50")
                    )
                )
            return ft.Row(
                alignment=ft.MainAxisAlignment.CENTER, 
                spacing=5, 
                wrap=True, 
                controls=[
                    make_btn("🚚 Touren", "touren", lambda e: zeige_dashboard()),
                    make_btn("📤 Senden", "senden", lambda e: zeige_postausgang()),
                    make_btn("🗄️ Archiv", "archiv", lambda e: zeige_archiv())
                ]
            )

        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold"),
                on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=25), 
                    padding=15,
                    side=ft.BorderSide(width=2, color=farbe)
                )
            )

        def list_action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=12, weight="bold"),
                on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=15), 
                    padding=8,
                    side=ft.BorderSide(width=1.5, color=farbe)
                )
            )

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                                     style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=45, height=45)

        def zeige_registrierung():
            page.clean() 
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            name_in = ft.TextField(label="Vorname Nachname", color="yellow", label_style=ft.TextStyle(color="white"), border_color="white", width=400, text_align="center")
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type="number", color="yellow", label_style=ft.TextStyle(color="white"), border_color="white", width=400, text_align="center", max_length=4)
            fehler = ft.Text("", color="red", weight="bold")
            def do_reg(e):
                if not name_in.value or not pin_in.value:
                    fehler.value = "⚠️ Bitte alles ausfüllen!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler.value = msg; page.update()
            ansicht.controls.extend([ft.Container(height=30), get_start_logo_bild(), ft.Text("Profil einrichten", color="#4CAF50", size=18), ft.Container(height=10), name_in, pin_in, fehler, action_btn("💾 PROFIL ERSTELLEN", do_reg, "#4CAF50")])
            page.add(ft.SafeArea(ansicht))

        def zeige_login():
            page.clean() 
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            bereinige_archiv() 
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", color="yellow", label_style=ft.TextStyle(color="white"), border_color="white", width=400, text_align="center", max_length=4)
            fehler = ft.Text("", color="red", weight="bold")
            def do_login(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    v, z = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(v, z)
                    zeige_dashboard()
                else:
                    fehler.value = "⚠️ PIN falsch!"; page.update()
            ansicht.controls.extend([ft.Container(height=30), get_start_logo_bild(), ft.Text("Mitarbeiter Login", color="#4CAF50", size=18), ft.Container(height=10), pin_in, fehler, action_btn("🔑 EINLOGGEN", do_login, "#4CAF50")])
            page.add(ft.SafeArea(ansicht))

        def zeige_dashboard():
            page.clean() 
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            ansicht.controls.append(nav_leiste("touren"))
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=20, weight="bold", color="white", text_align="center"))
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren angelegt.", color="white54", text_align="center"))
            else:
                for i, m in enumerate(maerkte):
                    txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                    ansicht.controls.append(ft.Container(bgcolor="#002200", padding=15, border_radius=15, content=ft.Row([
                        ft.Text(txt, color="white", weight="bold", size=12, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                        small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                    ])))
            ansicht.controls.append(ft.Row([action_btn("➕ Neue Tour anlegen", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3")], alignment=ft.MainAxisAlignment.CENTER))
            page.add(ft.SafeArea(ansicht))

        def zeige_postausgang():
            page.clean()
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            ansicht.controls.append(nav_leiste("senden"))
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="white", text_align="center"))
            
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
                            text_groesse = 14 if ist_gesendet else 13
                            anzeige_text = f"✅ {f}" if ist_gesendet else f
                            
                            async def teilen_jetzt(e, p=pfad):
                                markiere_als_gesendet(p)
                                zeige_postausgang() 
                                if share_obj: 
                                    await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                                else: print("Share geht auf dem PC nicht.")

                            def rm(e, p=pfad):
                                if os.path.exists(p): os.remove(p)
                                zeige_postausgang()

                            ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=15, content=ft.Row([ft.Text(anzeige_text, color=farbe, size=text_groesse, expand=True, weight=text_gewicht, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS), list_action_btn("📤 Senden", teilen_jetzt, "#2196F3"), small_btn("🗑️", rm, "#F44336")])))
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte zum Senden.", color="white54", text_align="center"))
            page.add(ft.SafeArea(ansicht))

        def zeige_archiv():
            page.clean()
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            ansicht.controls.append(nav_leiste("archiv"))
            ansicht.controls.append(ft.Text("Archiv (Letzte 14 Tage)", size=20, weight="bold", color="white", text_align="center"))
            ansicht.controls.append(ft.Container(bgcolor="#1a1a1a", padding=15, border_radius=15, content=ft.Column([ ft.Text("E-MAIL KOPIEREN:", color="#FF9800", weight="bold", size=14), ft.Text("registration-mibi.ber@tentamus.com", color="white", size=13, selectable=True)], horizontal_alignment="center")))
            
            bereinige_archiv()
            pdfs_gefunden = False
            such_ordner = []
            heute = datetime.datetime.now()
            gueltige_datums = [(heute - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(15)]
            
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                for d_str in gueltige_datums:
                    pfad = os.path.join(base, d_str)
                    if os.path.exists(pfad) and os.path.isdir(pfad):
                        if pfad not in such_ordner: such_ordner.append(pfad)
            
            gesendet_set = lade_gesendet() 
            such_ordner.sort(reverse=True)
            
            for ordner in such_ordner:
                try:
                    p_list = [f for f in os.listdir(ordner) if f.lower().endswith(".pdf")]
                    if p_list:
                        d = datetime.datetime.strptime(os.path.basename(ordner), '%Y-%m-%d')
                        ansicht.controls.append(ft.Text(f"📅 {d.strftime('%d.%m.%Y')}", color="yellow", weight="bold", size=14))
                        for f in p_list:
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            ist_gesendet = pfad in gesendet_set
                            farbe = "#4CAF50" if ist_gesendet else "white"
                            text_gewicht = "bold" if ist_gesendet else "normal"
                            text_groesse = 14 if ist_gesendet else 13
                            anzeige_text = f"✅ {f}" if ist_gesendet else f
                            
                            async def teilen_archiv(e, p=pfad):
                                markiere_als_gesendet(p)
                                zeige_archiv()
                                if share_obj: 
                                    await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                                else: print("Share geht auf dem PC nicht.")

                            ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=15, content=ft.Row([ft.Text(anzeige_text, color=farbe, size=text_groesse, expand=True, weight=text_gewicht, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS), list_action_btn("📤 Senden", teilen_archiv, "#2196F3")])))
                        ansicht.controls.append(ft.Divider(color="white24"))
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="white54", text_align="center"))
            page.add(ft.SafeArea(ansicht))

        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        page.add(ft.Text(f"Fehler: {e}", color="red"))

if __name__ == "__main__":
    ft.app(target=main)
