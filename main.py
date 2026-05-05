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
    # Wir nutzen hier nur noch Strings ("center") statt ft.CrossAxisAlignment
    ansicht = ft.Column(spacing=20, horizontal_alignment="center")
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

        def get_logo_bild(w=150, h=80):
            if os.path.exists(LOGO_PFAD):
                try:
                    return ft.Image(src=LOGO_PFAD, width=w, height=h, fit="contain")
                except: pass
            return ft.Container(content=ft.Text("🏢 [LOGO]", color="white54", size=20, weight="bold"), width=w, height=h, border=ft.border.all(1, "white24"), border_radius=10)

        def leucht_button(text, icon_name, on_click, color="#4CAF50"):
            return ft.ElevatedButton(
                content=ft.Row([ft.Icon(icon_name, color=color), ft.Text(text, color=color, weight="bold", size=16)], alignment="center"),
                on_click=on_click, bgcolor="#0b1a0b",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12), 
                    side=ft.BorderSide(width=2, color=color), 
                    padding=20
                ),
            )

        def nav_leiste(active_tab="touren"):
            def make_btn(text, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.Container(
                    expand=1,
                    content=ft.ElevatedButton(
                        content=ft.Text(text, size=13, weight="bold"),
                        on_click=on_click,
                        bgcolor="#004400" if is_active else "#111a11",
                        color="white",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=ft.padding.symmetric(horizontal=2, vertical=10), side=ft.BorderSide(width=1.5, color="#4CAF50"))
                    )
                )
            return ft.Row(alignment="center", spacing=5, controls=[
                make_btn("🚚 Touren", "touren", lambda e: zeige_dashboard()),
                make_btn("📤 Senden", "senden", lambda e: zeige_postausgang()),
                make_btn("🗄️ Archiv", "archiv", lambda e: zeige_archiv())
            ])

        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(text, size=14, weight="bold"), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25), padding=ft.padding.symmetric(horizontal=20, vertical=15), side=ft.BorderSide(width=2, color=farbe)))

        def list_action_btn(text, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(text, size=12, weight="bold"), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=ft.padding.symmetric(horizontal=12, vertical=8), side=ft.BorderSide(width=1.5, color=farbe)))

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=45, height=45)

        def zeige_registrierung():
            ansicht.controls.clear()
            logo_bild = ft.Container(content=get_logo_bild(w=200, h=100), margin=ft.margin.only(bottom=20))
            name_in = ft.TextField(label="Vorname Nachname", border_color="white", color="yellow")
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, can_reveal_password=True, keyboard_type="number", border_color="white", color="yellow", max_length=4)
            fehler_text = ft.Text("", color="red", weight="bold")

            def save_reg(e):
                if not name_in.value or not pin_in.value:
                    fehler_text.value = "⚠️ Bitte alle Felder ausfüllen!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler_text.value = f"⚠️ {msg}"; page.update()

            reg_card = ft.Container(
                content=ft.Column([
                    logo_bild, ft.Text("Monitoring App", size=24, weight="bold", color="#4CAF50"),
                    ft.Text("Erstmalige Einrichtung", size=18, color="white70"),
                    ft.Divider(height=20, color="white24"), name_in, pin_in, fehler_text,
                    leucht_button("Profil erstellen", "person_add", save_reg)
                ], horizontal_alignment="center", spacing=15),
                bgcolor="#111a11", padding=30, border_radius=15, border=ft.border.all(1, "white10"), width=400
            )
            ansicht.controls.append(ft.Container(content=reg_card, padding=ft.padding.only(top=50)))
            page.update()

        def zeige_login():
            ansicht.controls.clear()
            bereinige_archiv() 
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", border_color="#4CAF50", color="yellow", text_align="center", text_size=20, max_length=4)
            fehler_text = ft.Text("", color="red", weight="bold")

            def do_login(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    teile = name.split(" ", 1)
                    v = teile[0] if len(teile) > 0 else name
                    z = teile[1] if len(teile) > 1 else ""
                    speichere_benutzer(v, z) 
                    zeige_dashboard()
                else:
                    fehler_text.value = "⚠️ PIN falsch!"; pin_in.value = ""; page.update()

            login_card = ft.Container(
                content=ft.Column([
                    ft.Text("Monitoring App", size=24, weight="bold", color="#4CAF50"),
                    ft.Text("Mitarbeiter Login", size=18, color="white70"),
                    ft.Divider(height=20, color="white24"), pin_in, fehler_text,
                    leucht_button("Einloggen", "lock_open", do_login)
                ], horizontal_alignment="center", spacing=15),
                bgcolor="#111a11", padding=30, border_radius=15, border=ft.border.all(2, "#4CAF50"), width=400
            )
            ansicht.controls.append(ft.Container(content=login_card, padding=ft.padding.only(top=100)))
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            user_info = lade_benutzer()
            name_str = f"{user_info[0]} {user_info[1]}".strip()
            header_content = ft.Row([
                ft.Text("Bilacon Monitoring", size=20, weight="bold", color="#4CAF50"),
                ft.Row([ft.Icon("account_circle", color="white54"), ft.Text(name_str, color="white54", weight="bold")], spacing=5)
            ], alignment="spaceBetween")
            
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
                        ft.Text(txt, color="white", weight="bold", size=14, expand=True, max_lines=2, overflow="ellipsis"),
                        small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                        small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                    ])))
            ansicht.controls.append(ft.Container(content=action_btn("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"), padding=ft.padding.only(bottom=20)))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            user_info = lade_benutzer()
            name_str = f"{user_info[0]} {user_info[1]}".strip()
            header_content = ft.Row([ft.Text("Postausgang", size=20, weight="bold", color="#4CAF50"), ft.Row([ft.Icon("account_circle", color="white54"), ft.Text(name_str, color="white54", weight="bold")], spacing=5)], alignment="spaceBetween")
            ansicht.controls.append(ft.Container(content=header_content, padding=ft.padding.only(top=10, left=15, right=15)))
            ansicht.controls.append(ft.Divider(color="white24"))
            ansicht.controls.append(nav_leiste("senden"))
            
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
                            anzeige_text = f"✅ {f}" if ist_gesendet else f
                            
                            async def teilen_jetzt(e, p=pfad):
                                if share_obj: 
                                    await share_obj.share_files([ft.ShareFile(p)], text="Bilacon Bericht")
                                    markiere_als_gesendet(p)
                                    zeige_postausgang() 

                            ansicht.controls.append(
                                ft.Container(bgcolor="#111a11", padding=10, border_radius=15, width=700, border=ft.border.all(1, "#333333"),
                                    content=ft.Row([
                                        ft.Text(anzeige_text, color="white", size=12, expand=True, max_lines=2, overflow="ellipsis"),
                                        list_action_btn("📤 Senden", teilen_jetzt, "#2196F3"),
                                        small_btn("🗑️", lambda e, p=pfad: (os.remove(p), zeige_postausgang()), "#F44336")
                                    ])
                                )
                            )
                except: pass
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            user_info = lade_benutzer()
            name_str = f"{user_info[0]} {user_info[1]}".strip()
            header_content = ft.Row([ft.Text("Archiv", size=20, weight="bold", color="#4CAF50"), ft.Row([ft.Icon("account_circle", color="white54"), ft.Text(name_str, color="white54", weight="bold")], spacing=5)], alignment="spaceBetween")
            ansicht.controls.append(ft.Container(content=header_content, padding=ft.padding.only(top=10, left=15, right=15)))
            ansicht.controls.append(ft.Divider(color="white24"))
            ansicht.controls.append(nav_leiste("archiv"))
            
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
            
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    p_list = [f for f in os.listdir(ordner) if f.lower().endswith(".pdf")]
                    if p_list:
                        ansicht.controls.append(ft.Text(f"{os.path.basename(ordner)}", color="yellow", weight="bold", size=12))
                        for f in p_list:
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            
                            async def teilen_archiv(e, p=pfad):
                                if share_obj: await share_obj.share_files([ft.ShareFile(p)])

                            ansicht.controls.append(
                                ft.Container(bgcolor="#111a11", padding=10, border_radius=15, width=700, border=ft.border.all(1, "#333333"),
                                    content=ft.Row([
                                        ft.Text(f, color="white", size=12, expand=True), 
                                        list_action_btn("📤 Senden", teilen_archiv, "#2196F3")
                                    ])
                                )
                            )
                except: pass
            page.update()

        benutzer_liste = hole_alle_benutzer()
        if not benutzer_liste: zeige_registrierung()
        else: zeige_login()

    except Exception as e: ansicht.controls.append(ft.Text(f"Fehler: {e}", color="red")); page.update()

if __name__ == "__main__": ft.app(target=main)