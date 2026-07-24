"""
main.py
=======
Dies ist der Haupteinstiegspunkt (Entry Point) der REWE Monitoring App.
Dieses Modul steuert den initialen Start der Flet-UI, das Routing zwischen den 
verschiedenen Ansichten (Login, Dashboard, Postausgang, Archiv) und verwaltet 
Hintergrund-Routinen wie die automatische Bereinigung alter PDF-Dateien.
"""

import flet as ft
import os
import datetime
import shutil
import json 
import asyncio
import re

# =========================================================================
# GLOBALE PFADE & KONSTANTEN
# =========================================================================
LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")
START_LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent1.png")
GESENDET_FILE = "gesendet_log.json" 

def main(page: ft.Page):
    # Basis-Konfiguration der Flet-App (Helles Design)
    page.title = "Rewe Monitoring"
    page.bgcolor = "white"
    page.scroll = "auto"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER 

    share_obj = ft.Share() if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS] else None

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # =========================================================================
        # TRACKING-LOGIK: GESENDETE BERICHTE
        # =========================================================================
        def lade_gesendet():
            try:
                if os.path.exists(GESENDET_FILE):
                    with open(GESENDET_FILE, "r", encoding="utf-8") as f:
                        return set(json.load(f))
            except: pass
            return set()

        def markiere_als_gesendet(pfad):
            gesendet = lade_gesendet()
            gesendet.add(pfad)
            try:
                with open(GESENDET_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(gesendet), f, ensure_ascii=False, indent=4)
            except: pass

        # =========================================================================
        # SPEICHER- & BEREINIGUNGS-LOGIK (GARBAGE COLLECTION)
        # =========================================================================
        def get_erweiterte_bases():
            try: 
                bases = get_all_rewe_bases()
                zusatz = "/storage/emulated/0/Download/Rewe_Monitoring"
                if zusatz not in bases:
                    bases.append(zusatz)
                return list(set([os.path.normpath(b) for b in bases]))
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
                                if (heute - ordner_datum).days > 30: 
                                    shutil.rmtree(ordner_pfad)
                            except: pass
                except PermissionError: pass

        def bereinige_alte_touren():
            maerkte = lade_maerkte()
            heute = datetime.datetime.now()
            aktuelle_maerkte = []
            geaendert = False
            
            for m in maerkte:
                datum_str = m.get("datum", "")
                behalten = True
                if datum_str:
                    try:
                        tour_datum = datetime.datetime.strptime(datum_str, '%d.%m.%Y')
                        if (heute - tour_datum).days > 30: 
                            behalten = False
                            geaendert = True
                    except:
                        pass 
                
                if behalten:
                    aktuelle_maerkte.append(m)
            
            if geaendert:
                speichere_maerkte(aktuelle_maerkte)

        # =========================================================================
        # UI-HELPER & KOMPONENTEN
        # =========================================================================
        def get_start_logo_bild():
            if os.path.exists(START_LOGO_PFAD):
                return ft.Image(src=START_LOGO_PFAD, height=80, fit="contain")
            return ft.Text("REWE Monitoring", color="black", weight="bold", size=28)

        def nav_leiste(active_tab="touren"):
            def make_btn(text, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.ElevatedButton(
                    content=ft.Text(text, size=13, weight="bold"),
                    on_click=on_click,
                    bgcolor="#c8e6c9" if is_active else "#f0f0f0",
                    color="black",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10, side=ft.BorderSide(width=1.5, color="#006400"))
                )
            return ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5, wrap=True, controls=[
                make_btn("🚚 Touren", "touren", lambda e: zeige_dashboard()),
                make_btn("📤 Senden", "senden", lambda e: zeige_postausgang()),
                make_btn("🗄️ Archiv", "archiv", lambda e: zeige_archiv())
            ])

        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(text, size=14, weight="bold"), on_click=on_click, bgcolor="#ffffff", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25), padding=15, side=ft.BorderSide(width=2, color=farbe)))

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#ffffff", color=farbe, style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=45, height=45)

        # =========================================================================
        # ANSICHTEN (ROUTING)
        # =========================================================================
        def zeige_registrierung():
            page.clean() 
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            name_in = ft.TextField(label="Vorname Nachname", color="#006400", label_style=ft.TextStyle(color="black"), border_color="grey", width=400, text_align="center")
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type="number", color="#006400", label_style=ft.TextStyle(color="black"), border_color="grey", width=400, text_align="center", max_length=4)
            fehler = ft.Text("", color="red", weight="bold")
            
            def do_reg(e):
                if not name_in.value or not pin_in.value:
                    fehler.value = "⚠️ Bitte alles ausfüllen!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler.value = msg; page.update()
                
            ansicht.controls.extend([ft.Container(height=30), get_start_logo_bild(), ft.Text("Profil einrichten", color="black", weight="bold", size=18), ft.Container(height=10), name_in, pin_in, fehler, action_btn("💾 PROFIL ERSTELLEN", do_reg, "#006400")])
            page.add(ft.SafeArea(ansicht))

        def zeige_login():
            page.clean() 
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            bereinige_archiv() 
            bereinige_alte_touren()
            
            pin_in = ft.TextField(label="Deine PIN", password=True, keyboard_type="number", color="#006400", label_style=ft.TextStyle(color="black"), border_color="grey", width=400, text_align="center", max_length=4)
            fehler = ft.Text("", color="red", weight="bold")
            
            def do_login(e):
                name = authentifiziere_benutzer(pin_in.value)
                if name:
                    v, z = (name.split(" ", 1) + [""])[:2]
                    speichere_benutzer(v, z)
                    zeige_dashboard()
                else:
                    fehler.value = "⚠️ PIN falsch!"; page.update()
                    
            ansicht.controls.extend([ft.Container(height=30), get_start_logo_bild(), ft.Text("Mitarbeiter Login", color="black", weight="bold", size=18), ft.Container(height=10), pin_in, fehler, action_btn("🔑 EINLOGGEN", do_login, "#006400")])
            page.add(ft.SafeArea(ansicht))

        def zeige_dashboard():
            page.clean() 
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            ansicht.controls.append(nav_leiste("touren"))
            ansicht.controls.append(ft.Text("Meine aktuellen Touren", size=20, weight="bold", color="black", text_align="center"))
            
            maerkte = lade_maerkte()
            aktive_touren = [(i, m) for i, m in enumerate(maerkte) if not m.get("erledigt", False)]
            
            if not aktive_touren:
                ansicht.controls.append(ft.Text("Noch keine offenen Touren angelegt.", color="grey", text_align="center"))
            else:
                for i, m in aktive_touren:
                    txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                    ansicht.controls.append(ft.Container(bgcolor="#f9f9f9", padding=15, border_radius=15, content=ft.Row([
                        ft.Text(txt, color="black", weight="bold", size=12, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                        small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                    ])))
                    
            ansicht.controls.append(ft.Row([action_btn("➕ Neue Tour anlegen", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3")], alignment=ft.MainAxisAlignment.CENTER))
            page.add(ft.SafeArea(ansicht))
            page.update()

        def zeige_postausgang():
            try:
                page.clean()
                ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
                ansicht.controls.append(nav_leiste("senden"))
                ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="black", text_align="center"))
                
                heute = datetime.datetime.now()
                heute_ordner = heute.strftime('%Y-%m-%d')
                heute_de = heute.strftime('%d.%m.%Y')
                pdfs_gefunden = False
                such_ordner_liste = get_erweiterte_bases()
                aktuelles_gesendet_set = lade_gesendet() 
                gesehene_dateien = set()

                heute_pdfs = []
                for base in such_ordner_liste:
                    ziel_ordner = os.path.join(base, heute_ordner)
                    # Suche im Tagesordner UND im Hauptverzeichnis
                    for ordner in list(set([ziel_ordner, base])):
                        if not os.path.exists(ordner): continue
                        for f in os.listdir(ordner):
                            if f.lower().endswith(".pdf"):
                                pfad = os.path.normpath(os.path.join(ordner, f))
                                
                                # HIER IST DER FEHLER BEHOBEN: Es wird keine Dateigröße mehr blind gelöscht!
                                
                                von_heute = False
                                # Prüft, ob es im heutigen Ordner ist oder das Datum im Namen trägt
                                if heute_ordner in pfad or heute_de in f:
                                    von_heute = True
                                else:
                                    try:
                                        file_date = datetime.datetime.fromtimestamp(os.path.getmtime(pfad)).date()
                                        if file_date == heute.date():
                                            von_heute = True
                                    except: pass

                                # Wenn es im Basis-Ordner liegt und wir das Datum nicht sicher kennen, lieber anzeigen
                                if not von_heute and ordner == base:
                                    von_heute = True

                                if von_heute:
                                    try: mtime = os.path.getmtime(pfad)
                                    except: mtime = 0
                                    heute_pdfs.append({"f": f, "pfad": pfad, "mtime": mtime})

                # --- DUPLIKAT FILTER ---
                gruppen = {}
                for item in heute_pdfs:
                    name = item["f"][:-4] # .pdf abschneiden
                    # Bereinigt Zeitstempel und Kopie-Zahlen um zusammengehörige Dateien zu erkennen
                    name = re.sub(r'\s*\(\d+\)$', '', name)
                    name = re.sub(r'_[0-9]{6}$', '', name)
                    name = re.sub(r'-[0-9]{6}$', '', name)
                    name = re.sub(r'_[0-9]{2}-[0-9]{2}-[0-9]{2}$', '', name)
                    name = re.sub(r'_[0-9]{2}_[0-9]{2}_[0-9]{2}$', '', name)
                    
                    if name not in gruppen:
                        gruppen[name] = []
                    gruppen[name].append(item)

                bereinigte_pdfs = []
                for basis, dateien in gruppen.items():
                    # Sortiert nach Zeitstempel/Namen, um die Neueste ganz vorn zu haben
                    dateien.sort(key=lambda x: (x["mtime"], x["f"]), reverse=True)
                    bereinigte_pdfs.append(dateien[0])
                    
                    # Löscht alle älteren Versionen dieser speziellen Tour vom Gerät
                    for alt in dateien[1:]:
                        try:
                            os.remove(alt["pfad"])
                            if alt["pfad"] in aktuelles_gesendet_set:
                                aktuelles_gesendet_set.remove(alt["pfad"])
                        except: pass
                
                try:
                    with open(GESENDET_FILE, "w", encoding="utf-8") as f_log:
                        json.dump(list(aktuelles_gesendet_set), f_log, ensure_ascii=False, indent=4)
                except: pass
                # -----------------------

                def erstelle_eintrag(dateiname, pfad):
                    ist_gesendet = pfad in aktuelles_gesendet_set
                    text_ctrl = ft.Text(f"{dateiname} ✅" if ist_gesendet else dateiname, color="#006400" if ist_gesendet else "black", size=13, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                    
                    btn_text = "✅ Gesendet" if ist_gesendet else "📤 Senden"
                    btn_color = "#006400" if ist_gesendet else "#2196F3"
                    senden_btn = ft.ElevatedButton(content=ft.Text(btn_text, size=12, weight="bold"), bgcolor="#ffffff", color=btn_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=8, side=ft.BorderSide(width=1.5, color=btn_color)))
                    
                    container = ft.Container(bgcolor="#f9f9f9", padding=10, border_radius=15)
                    
                    async def teilen_jetzt(e):
                        text_ctrl.value = f"{dateiname} ✅"; text_ctrl.color = "#006400"; text_ctrl.update()
                        senden_btn.content.value = "✅ Gesendet"; senden_btn.color = "#006400"; senden_btn.style.side = ft.BorderSide(width=1.5, color="#006400"); senden_btn.update()
                        
                        markiere_als_gesendet(pfad)
                        aktuelles_gesendet_set.add(pfad)

                        try:
                            maerkte = lade_maerkte()
                            tour_geaendert = False
                            for m in maerkte:
                                nr = str(m.get("marktnummer", "")).strip()
                                auftr = str(m.get("auftragsnummer", "")).strip()
                                # Schiebt die Tour ins Archiv, wenn sie im Dateinamen gefunden wird
                                if (nr and nr in dateiname) or (auftr and auftr in dateiname):
                                    if not m.get("erledigt", False):
                                        m["erledigt"] = True
                                        tour_geaendert = True
                            if tour_geaendert:
                                speichere_maerkte(maerkte)
                        except: pass
                        
                        await asyncio.sleep(0.3)
                        if share_obj: await share_obj.share_files([ft.ShareFile.from_path(pfad)], text="REWE Bericht")
                    senden_btn.on_click = teilen_jetzt
                    
                    def loeschen(e):
                        try:
                            if os.path.exists(pfad): os.remove(pfad)
                            if pfad in aktuelles_gesendet_set:
                                aktuelles_gesendet_set.remove(pfad)
                                with open(GESENDET_FILE, "w", encoding="utf-8") as f:
                                    json.dump(list(aktuelles_gesendet_set), f, ensure_ascii=False, indent=4)
                        except: pass
                        container.visible = False; container.update()
                        
                    container.content = ft.Row([text_ctrl, senden_btn, small_btn("🗑️", loeschen, "#F44336")])
                    return container

                for item in bereinigte_pdfs:
                    f = item["f"]
                    pfad = item["pfad"]
                    if f in gesehene_dateien: continue
                    gesehene_dateien.add(f)
                    
                    # WICHTIG: Überspringt Dateien von HEUTE, die bereits gesendet WURDEN
                    if pfad in aktuelles_gesendet_set: 
                        continue

                    pdfs_gefunden = True
                    ansicht.controls.append(erstelle_eintrag(f, pfad))
                
                if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine offenen Berichte gefunden.", color="grey", text_align="center"))
                page.add(ft.SafeArea(ansicht)); page.update()
            except Exception as e:
                page.add(ft.Text(f"CRASH Postausgang: {e}", color="red", weight="bold")); page.update()

        def zeige_archiv():
            page.clean()
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            ansicht.controls.append(nav_leiste("archiv"))
            
            maerkte = lade_maerkte()
            erledigte_touren = [(i, m) for i, m in enumerate(maerkte) if m.get("erledigt", False)]
            
            if erledigte_touren:
                ansicht.controls.append(ft.Text("Erledigte Touren (Zur Nachbearbeitung)", size=16, weight="bold", color="#006400", text_align="center"))
                for i, m in erledigte_touren:
                    txt = m.get("adresse") or m.get("marktnummer") or "Tour"
                    ansicht.controls.append(ft.Container(bgcolor="#e8f5e9", padding=15, border_radius=15, content=ft.Row([
                        ft.Text(f"✅ {txt}", color="black", weight="bold", size=12, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_archiv, None, idx), "#2196F3"),
                        small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_archiv()), "#F44336")
                    ])))
                ansicht.controls.append(ft.Divider(color="#cccccc"))
            
            ansicht.controls.append(ft.Text("Archivierte PDF Berichte (Letzte 30 Tage)", size=18, weight="bold", color="black", text_align="center"))
            
            bereinige_archiv()
            pdfs_gefunden = False
            such_ordner = []
            heute = datetime.datetime.now()
            heute_str = heute.strftime('%Y-%m-%d')
            
            gueltige_datums = [(heute - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
            
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                for d_str in gueltige_datums:
                    pfad = os.path.join(base, d_str)
                    if os.path.exists(pfad) and os.path.isdir(pfad):
                        if pfad not in such_ordner: such_ordner.append(pfad)
            
            aktuelles_gesendet_set = lade_gesendet() 
            such_ordner.sort(reverse=True) 
            gesehene_dateien_archiv = set()
            
            for ordner in such_ordner:
                try:
                    p_list = [f for f in os.listdir(ordner) if f.lower().endswith(".pdf")]
                    if p_list:
                        d = datetime.datetime.strptime(os.path.basename(ordner), '%Y-%m-%d')
                        titel_angelegt = False
                        
                        for f in p_list:
                            pfad = os.path.normpath(os.path.join(ordner, f))
                            
                            # Auch hier die Fehlerquelle behoben (Größen-Löschung weg)

                            ist_gesendet = pfad in aktuelles_gesendet_set
                            ordner_datum_str = os.path.basename(ordner)
                            
                            # Verhindert, dass ungesendete PDFs von heute schon im Archiv auftauchen
                            if ordner_datum_str == heute_str and not ist_gesendet:
                                continue

                            if f in gesehene_dateien_archiv: continue
                            gesehene_dateien_archiv.add(f)
                            
                            pdfs_gefunden = True
                            
                            if not titel_angelegt:
                                ansicht.controls.append(ft.Text(f"📅 {d.strftime('%d.%m.%Y')}", color="#006400", weight="bold", size=14))
                                titel_angelegt = True

                            text_ctrl = ft.Text(f"{f} ✅" if ist_gesendet else f, color="#006400" if ist_gesendet else "black", size=13, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                            btn_text, btn_color = ("✅ Gesendet", "#006400") if ist_gesendet else ("📤 Senden", "#2196F3")
                            senden_btn = ft.ElevatedButton(content=ft.Text(btn_text, size=12, weight="bold"), bgcolor="#ffffff", color=btn_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=8, side=ft.BorderSide(width=1.5, color=btn_color)))
                            
                            async def teilen_archiv(e, p=pfad, tc=text_ctrl, btn=senden_btn, dateiname=f):
                                tc.value = f"{dateiname} ✅"; tc.color = "#006400"; tc.update()
                                btn.content.value = "✅ Gesendet"; btn.color = "#006400"; btn.style.side = ft.BorderSide(width=1.5, color="#006400"); btn.update()
                                markiere_als_gesendet(p)
                                aktuelles_gesendet_set.add(p)

                                try:
                                    maerkte = lade_maerkte()
                                    tour_geaendert = False
                                    for m in maerkte:
                                        nr = str(m.get("marktnummer", "")).strip()
                                        auftr = str(m.get("auftragsnummer", "")).strip()
                                        if (nr and nr in dateiname) or (auftr and auftr in dateiname):
                                            if not m.get("erledigt", False):
                                                m["erledigt"] = True
                                                tour_geaendert = True
                                    if tour_geaendert:
                                        speichere_maerkte(maerkte)
                                except: pass

                                await asyncio.sleep(0.3)
                                if share_obj: await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                            
                            senden_btn.on_click = teilen_archiv
                            ansicht.controls.append(ft.Container(bgcolor="#f9f9f9", padding=10, border_radius=15, content=ft.Row([text_ctrl, senden_btn])))
                        
                        if titel_angelegt:
                            ansicht.controls.append(ft.Divider(color="#cccccc"))
                except: pass
            
            if not pdfs_gefunden and not erledigte_touren: 
                ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="grey", text_align="center"))
            page.add(ft.SafeArea(ansicht)); page.update()

        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        page.add(ft.Text(f"Fehler: {e}", color="red"))

if __name__ == "__main__":
    ft.app(target=main)
