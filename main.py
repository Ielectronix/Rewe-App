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

# =========================================================================
# GLOBALE PFADE & KONSTANTEN
# =========================================================================
LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")
START_LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent1.png")
# Speichert permanent ab, welche PDFs bereits via Share-Sheet gesendet wurden
GESENDET_FILE = "gesendet_log.json" 

def main(page: ft.Page):
    # Basis-Konfiguration der Flet-App (Fenstertitel, Hintergrundfarbe, Scrollverhalten)
    page.title = "Rewe Monitoring"
    page.bgcolor = "#001a00"
    page.scroll = "auto"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER 

    # Initialisiert die native Teilen-Funktion (Share Sheet) für iOS / Android.
    # Auf Desktop-Systemen (Windows) wird dies auf None gesetzt.
    share_obj = ft.Share() if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS] else None

    try:
        # Lokale Module importieren (Trennt UI, Logik und Datenhaltung)
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # =========================================================================
        # TRACKING-LOGIK: GESENDETE BERICHTE
        # Verhindert, dass Nutzer aus Versehen denselben Bericht doppelt senden.
        # =========================================================================
        def lade_gesendet():
            """Lädt die Liste (als Set) der bereits gesendeten Datei-Pfade aus der JSON."""
            try:
                if os.path.exists(GESENDET_FILE):
                    with open(GESENDET_FILE, "r", encoding="utf-8") as f:
                        return set(json.load(f))
            except: pass
            return set()

        def markiere_als_gesendet(pfad):
            """Fügt einen Dateipfad dem Log hinzu und speichert es permanent ab."""
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
            """
            Kombiniert die Basispfade aus dem PDF-Generator mit spezifischen
            Android-Download-Pfaden, um sicherzustellen, dass das Archiv alle
            relevanten Ordner auf dem Tablet findet.
            """
            try: 
                bases = get_all_rewe_bases()
                zusatz = "/storage/emulated/0/Download/Rewe_Monitoring"
                if zusatz not in bases:
                    bases.append(zusatz)
                return list(set([os.path.normpath(b) for b in bases]))
            except: return []

        def bereinige_archiv():
            """
            Smarte Löschroutine (Garbage Collection):
            Scannt alle Tages-Ordner (Namensschema YYYY-MM-DD). Ist ein Ordner 
            älter als 14 Tage, wird er samt Inhalt (PDFs) unwiderruflich gelöscht.
            Wird laut DSGVO/Datensparsamkeit bei jedem Login und Archiv-Aufruf getriggert.
            """
            heute = datetime.datetime.now()
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                try:
                    for ordner in os.listdir(base):
                        ordner_pfad = os.path.join(base, ordner)
                        if os.path.isdir(ordner_pfad) and ordner != "temp":
                            try:
                                ordner_datum = datetime.datetime.strptime(ordner, '%Y-%m-%d')
                                if (heute - ordner_datum).days > 14: 
                                    shutil.rmtree(ordner_pfad)
                            except: pass
                except PermissionError: pass

        # =========================================================================
        # UI-HELPER & KOMPONENTEN
        # =========================================================================
        def get_start_logo_bild():
            """Lädt das Firmenlogo oder zeigt einen Fallback-Text an, falls das Bild fehlt."""
            if os.path.exists(START_LOGO_PFAD):
                return ft.Image(src=START_LOGO_PFAD, height=80, fit="contain")
            return ft.Text("REWE Monitoring", color="white", weight="bold", size=28)

        def nav_leiste(active_tab="touren"):
            """Erzeugt die dynamische Haupt-Navigationsleiste (Touren, Senden, Archiv)."""
            def make_btn(text, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.ElevatedButton(
                    content=ft.Text(text, size=13, weight="bold"),
                    on_click=on_click,
                    bgcolor="#004400" if is_active else "#1a1a1a",
                    color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10, side=ft.BorderSide(width=1.5, color="#4CAF50"))
                )
            return ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5, wrap=True, controls=[
                make_btn("🚚 Touren", "touren", lambda e: zeige_dashboard()),
                make_btn("📤 Senden", "senden", lambda e: zeige_postausgang()),
                make_btn("🗄️ Archiv", "archiv", lambda e: zeige_archiv())
            ])

        def action_btn(text, on_click, farbe):
            """Standardisiertes Design für primäre Aktionsbuttons."""
            return ft.ElevatedButton(content=ft.Text(text, size=14, weight="bold"), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25), padding=15, side=ft.BorderSide(width=2, color=farbe)))

        def small_btn(emoji, on_click, farbe):
            """Standardisiertes Design für kleine, runde Icon-Buttons (z.B. Löschen/Editieren)."""
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=45, height=45)

        # =========================================================================
        # ANSICHTEN (ROUTING)
        # =========================================================================
        def zeige_registrierung():
            """Zeigt die initiale Registrierungsmaske beim allerersten App-Start."""
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
            """Zeigt den PIN-Login-Screen an und triggert die Archiv-Bereinigung."""
            page.clean() 
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            # WICHTIG: Hier wird automatisch das 14-Tage-Archiv gereinigt!
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
            """Zeigt das Haupt-Dashboard mit der Liste der heutigen/aktiven Touren."""
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
                        # Übergibt den Index (i) an zeige_maske_ui, um genau diese Tour zu bearbeiten
                        small_btn("✏️", lambda e, idx=i: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, idx), "#2196F3"),
                        small_btn("🗑️", lambda e, idx=i: (maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()), "#F44336")
                    ])))
                    
            ansicht.controls.append(ft.Row([action_btn("➕ Neue Tour anlegen", lambda e: zeige_maske_ui(page, ansicht, None, zeige_dashboard, None, None), "#2196F3")], alignment=ft.MainAxisAlignment.CENTER))
            page.add(ft.SafeArea(ansicht))
            page.update()

        def zeige_postausgang():
            """Scannt den Tagesordner nach erzeugten PDFs und bereitet sie zum nativen Teilen vor."""
            try:
                page.clean()
                ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
                ansicht.controls.append(nav_leiste("senden"))
                ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="white", text_align="center"))
                
                heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
                pdfs_gefunden = False
                such_ordner_liste = get_erweiterte_bases()
                aktuelles_gesendet_set = lade_gesendet() 
                gesehene_dateien = set()

                def erstelle_eintrag(dateiname, pfad):
                    """Baut das UI-Element für eine einzelne zu sendende PDF."""
                    ist_gesendet = pfad in aktuelles_gesendet_set
                    text_ctrl = ft.Text(f"{dateiname} ✅" if ist_gesendet else dateiname, color="#4CAF50" if ist_gesendet else "white", size=13, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                    
                    btn_text = "✅ Gesendet" if ist_gesendet else "📤 Senden"
                    btn_color = "#4CAF50" if ist_gesendet else "#2196F3"
                    senden_btn = ft.ElevatedButton(content=ft.Text(btn_text, size=12, weight="bold"), bgcolor="#0b1a0b", color=btn_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=8, side=ft.BorderSide(width=1.5, color=btn_color)))
                    
                    container = ft.Container(bgcolor="#002200", padding=10, border_radius=15)
                    
                    async def teilen_jetzt(e):
                        """Asynchrone Funktion: Öffnet das Android/iOS Share-Sheet für die PDF."""
                        # UI sofort aktualisieren (Visuelles Feedback)
                        text_ctrl.value = f"{dateiname} ✅"; text_ctrl.color = "#4CAF50"; text_ctrl.update()
                        senden_btn.content.value = "✅ Gesendet"; senden_btn.color = "#4CAF50"; senden_btn.style.side = ft.BorderSide(width=1.5, color="#4CAF50"); senden_btn.update()
                        
                        # In JSON speichern
                        markiere_als_gesendet(pfad)
                        aktuelles_gesendet_set.add(pfad)
                        
                        await asyncio.sleep(0.3)
                        # Natives Teilen auslösen
                        if share_obj: await share_obj.share_files([ft.ShareFile.from_path(pfad)], text="REWE Bericht")
                    senden_btn.on_click = teilen_jetzt
                    
                    def loeschen(e):
                        """Löscht die PDF von der Festplatte und aus dem Gesendet-Log."""
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

                # Durchsucht alle Ordner nach heutigen PDFs
                for base in such_ordner_liste:
                    ziel_ordner = os.path.join(base, heute_ordner)
                    for ordner in list(set([ziel_ordner, base])):
                        if not os.path.exists(ordner): continue
                        for f in os.listdir(ordner):
                            if f.lower().endswith(".pdf"):
                                pfad = os.path.normpath(os.path.join(ordner, f))
                                
                                # Filtern von defekten (leeren) 0-Byte PDF-Dateien
                                try:
                                    if os.path.getsize(pfad) < 2048: 
                                        os.remove(pfad)
                                        continue 
                                except Exception:
                                    pass

                                if f in gesehene_dateien: continue
                                gesehene_dateien.add(f)
                                pdfs_gefunden = True
                                ansicht.controls.append(erstelle_eintrag(f, pfad))
                
                if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte gefunden.\nFehlerhafte Berichte wurden aussortiert.", color="white54", text_align="center"))
                page.add(ft.SafeArea(ansicht)); page.update()
            except Exception as e:
                page.add(ft.Text(f"CRASH Postausgang: {e}", color="red", weight="bold")); page.update()

        def zeige_archiv():
            """Scannt die Historie nach alten PDF-Tagesordnern (max. 14 Tage)."""
            page.clean()
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            ansicht.controls.append(nav_leiste("archiv"))
            ansicht.controls.append(ft.Text("Archiv (Letzte 14 Tage)", size=20, weight="bold", color="white", text_align="center"))
            
            # Bereinigung triggern, damit wirklich nur max. 14 Tage angezeigt werden
            bereinige_archiv()
            pdfs_gefunden = False
            such_ordner = []
            heute = datetime.datetime.now()
            
            # Generiert Liste der erlaubten Datum-Strings der letzten 15 Tage
            gueltige_datums = [(heute - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(15)]
            
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                for d_str in gueltige_datums:
                    pfad = os.path.join(base, d_str)
                    if os.path.exists(pfad) and os.path.isdir(pfad):
                        if pfad not in such_ordner: such_ordner.append(pfad)
            
            aktuelles_gesendet_set = lade_gesendet() 
            such_ordner.sort(reverse=True) # Neueste Ordner ganz oben anzeigen
            gesehene_dateien_archiv = set()
            
            for ordner in such_ordner:
                try:
                    p_list = [f for f in os.listdir(ordner) if f.lower().endswith(".pdf")]
                    if p_list:
                        d = datetime.datetime.strptime(os.path.basename(ordner), '%Y-%m-%d')
                        titel_angelegt = False
                        
                        for f in p_list:
                            pfad = os.path.normpath(os.path.join(ordner, f))
                            
                            try:
                                if os.path.getsize(pfad) < 2048:
                                    os.remove(pfad)
                                    continue
                            except Exception:
                                pass

                            if f in gesehene_dateien_archiv: continue
                            gesehene_dateien_archiv.add(f)
                            
                            pdfs_gefunden = True
                            
                            # Rendert die Datums-Überschrift (z.B. '📅 12.06.2026') über den Block
                            if not titel_angelegt:
                                ansicht.controls.append(ft.Text(f"📅 {d.strftime('%d.%m.%Y')}", color="yellow", weight="bold", size=14))
                                titel_angelegt = True

                            ist_gesendet = pfad in aktuelles_gesendet_set
                            text_ctrl = ft.Text(f"{f} ✅" if ist_gesendet else f, color="#4CAF50" if ist_gesendet else "white", size=13, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                            btn_text, btn_color = ("✅ Gesendet", "#4CAF50") if ist_gesendet else ("📤 Senden", "#2196F3")
                            senden_btn = ft.ElevatedButton(content=ft.Text(btn_text, size=12, weight="bold"), bgcolor="#0b1a0b", color=btn_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=8, side=ft.BorderSide(width=1.5, color=btn_color)))
                            
                            async def teilen_archiv(e, p=pfad, tc=text_ctrl, btn=senden_btn, dateiname=f):
                                tc.value = f"{dateiname} ✅"; tc.color = "#4CAF50"; tc.update()
                                btn.content.value = "✅ Gesendet"; btn.color = "#4CAF50"; btn.style.side = ft.BorderSide(width=1.5, color="#4CAF50"); btn.update()
                                markiere_als_gesendet(p); await asyncio.sleep(0.3)
                                if share_obj: await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                            
                            senden_btn.on_click = teilen_archiv
                            ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=15, content=ft.Row([text_ctrl, senden_btn])))
                        
                        if titel_angelegt:
                            ansicht.controls.append(ft.Divider(color="white24"))
                except: pass
            
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="white54", text_align="center"))
            page.add(ft.SafeArea(ansicht)); page.update()

        # =========================================================================
        # APP START-LOGIK
        # Prüft, ob Benutzerprofile existieren, um auf die korrekte Startmaske zu leiten.
        # =========================================================================
        mitarbeiter = hole_alle_benutzer()
        if not mitarbeiter: zeige_registrierung()
        else: zeige_login()

    except Exception as e:
        page.add(ft.Text(f"Fehler: {e}", color="red"))

# Flet Applikation starten
if __name__ == "__main__":
    ft.app(target=main)
