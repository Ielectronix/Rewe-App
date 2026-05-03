import flet as ft
import os
import datetime
import shutil
import json 

def main(page: ft.Page):
    page.title = "Rewe Monitoring"
    page.bgcolor = "#001a00"
    page.scroll = "auto"
    ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ft.SafeArea(ansicht))

    share_obj = ft.Share() if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS] else None

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
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
                except PermissionError: pass

        # ==========================================
        # UI ELEMENTE & NAVIGATION
        # ==========================================
        def nav_leiste(active_tab="touren"):
            def make_btn(text, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.Container(
                    expand=1,
                    content=ft.ElevatedButton(
                        content=ft.Text(text, size=13, weight="bold"), # FIX: Schriftgröße 13, damit es perfekt passt
                        on_click=on_click,
                        bgcolor="#004400" if is_active else "#1a1a1a",
                        color="white",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.padding.symmetric(horizontal=2, vertical=10), # FIX: Weniger Randabstand
                            side=ft.BorderSide(width=1.5, color="#4CAF50")
                        )
                    )
                )
            # FIX: Senden heißt wieder Senden
            return ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5, controls=[
                make_btn("🚚 Touren", "touren", lambda e: zeige_dashboard()),
                make_btn("📤 Senden", "senden", lambda e: zeige_postausgang()),
                make_btn("🗄️ Archiv", "archiv", lambda e: zeige_archiv())
            ])

        # Der große, dicke Button (Für Startbildschirm etc.)
        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold"),
                on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=25), 
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                    side=ft.BorderSide(width=2, color=farbe)
                )
            )

        # FIX: Der neue, kompakte Button extra für die Listen im Postausgang/Archiv
        def list_action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=12, weight="bold"),
                on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=15), 
                    padding=ft.padding.symmetric(horizontal=12, vertical=8), # Sehr viel schlanker
                    side=ft.BorderSide(width=1.5, color=farbe)
                )
            )

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#0b1a0b", color=farbe,
                                     style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=45, height=45)

        # ==========================================
        # SEITEN / TABS
        # ==========================================
        def zeige_startbildschirm():
            ansicht.controls.clear()
            bereinige_archiv() 
            v, z = lade_benutzer()
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", text_style=ft.TextStyle(color="yellow"), label_style=ft.TextStyle(color="white54"), border_color="white", width=300, text_align="center")
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", text_style=ft.TextStyle(color="yellow"), label_style=ft.TextStyle(color="white54"), border_color="white", width=300, text_align="center")
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()
                
            ansicht.controls.extend([
                ft.Container(height=30),
                ft.Text("REWE Monitoring", color="white", weight="bold", size=28),
                ft.Container(height=10),
                v_in, z_in,
                ft.Container(height=10),
                action_btn("🚀 Tag starten", start_klick, "#F44336")
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste("touren"))
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=20, weight="bold", color="white"))
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren angelegt.", color="white54"))
            else:
                for i, m in enumerate(maerkte):
                    txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                    ansicht.controls.append(ft.Container(bgcolor="#002200", padding=15, border_radius=15, width=380, content=ft.Row([
                        ft.Text(txt, color="white", weight="bold", size=12, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                        small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                    ])))
            ansicht.controls.append(action_btn("➕ Neue Tour anlegen", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3"))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
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
                            
                            async def teilen_jetzt(e, p=pfad):
                                if share_obj: 
                                    await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                                    markiere_als_gesendet(p)
                                    zeige_postausgang() 
                                else: print("Share geht auf dem PC nicht.")

                            def rm(e, p=pfad):
                                if os.path.exists(p): os.remove(p)
                                zeige_postausgang()

                            ansicht.controls.append(
                                ft.Container(
                                    # FIX: padding=10 spart Platz
                                    bgcolor="#002200", padding=10, border_radius=15, width=380,
                                    content=ft.Row([
                                        ft.Text(anzeige_text, color=farbe, size=12, expand=True, weight=text_gewicht, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                        # FIX: Schlanker Senden-Button hier im Postausgang
                                        list_action_btn("📤 Senden", teilen_jetzt, "#2196F3"),
                                        small_btn("🗑️", rm, "#F44336")
                                    ])
                                )
                            )
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte zum Senden.", color="white54"))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste("archiv"))
            ansicht.controls.append(ft.Text("Archiv (Letzte 14 Tage)", size=20, weight="bold", color="white"))
            
            email_val = "registration-mibi.ber@tentamus.com"
            ansicht.controls.append(ft.Container(bgcolor="#1a1a1a", padding=15, border_radius=15, width=380, content=ft.Column([
                ft.Text("E-MAIL KOPIEREN:", color="#FF9800", weight="bold", size=14), 
                ft.Text(email_val, color="white", size=13, selectable=True)
            ], horizontal_alignment="center")))
            
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
                        ansicht.controls.append(ft.Text(f"{ordner}", color="yellow", weight="bold", size=12))
                        for f in p_list:
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            
                            ist_gesendet = pfad in gesendet_set
                            farbe = "#4CAF50" if ist_gesendet else "white"
                            text_gewicht = "bold" if ist_gesendet else "normal"
                            anzeige_text = f"✅ {f}" if ist_gesendet else f
                            
                            async def teilen_archiv(e, p=pfad):
                                if share_obj: 
                                    await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                                    markiere_als_gesendet(p)
                                    zeige_archiv()
                                else: print("Share geht auf dem PC nicht.")

                            ansicht.controls.append(
                                ft.Container(
                                    # FIX: padding=10 spart Platz
                                    bgcolor="#002200", padding=10, border_radius=15, width=380, 
                                    content=ft.Row([
                                        ft.Text(anzeige_text, color=farbe, size=12, expand=True, weight=text_gewicht, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS), 
                                        # FIX: Schlanker Senden-Button hier im Archiv
                                        list_action_btn("📤 Senden", teilen_archiv, "#2196F3")
                                    ])
                                )
                            )
                        ansicht.controls.append(ft.Divider(color="white24"))
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="white54"))
            page.update()

        zeige_startbildschirm()
    except Exception as e: ansicht.controls.append(ft.Text(f"Fehler: {e}", color="red")); page.update()

if __name__ == "__main__": ft.app(target=main)