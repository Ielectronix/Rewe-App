import flet as ft
import datetime
import json
import os
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer
from pdf_generator import erstelle_bericht

def lade_vorlagen_lokal():
    try:
        if os.path.exists("tour_vorlagen.json"):
            with open("tour_vorlagen.json", "r", encoding="utf-8") as f: return json.load(f)
    except: pass
    return {}

def speichere_vorlagen_lokal(daten):
    try:
        with open("tour_vorlagen.json", "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)
    except: pass

def zeige_maske_ui(page: ft.Page, ansicht: ft.Column, nav_leiste, zeige_dashboard, zeige_fehler, markt_index):
    # --- Globale UI Variablen für den Scope ---
    haupt_bereich = ft.Column(spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    top_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=5)
    markierte_fehler_controls = []
    
    # Optionen
    tage_opts = [""]+[f"{i:02d}" for i in range(1,32)]
    mon_opts = [""]+[f"{i:02d}" for i in range(1,13)]
    jahr_opts = [""]+[str(i) for i in range(2024,2035)]
    ort_opts = ["", "Fischabteilung", "Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke"]
    verp_opts = ["", "steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel u. etikett", "Pappschale mit Kunststofffolie umwickelt", "tiefgezogene Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie umwickelt", "SB-Kunststoffverpackung"]
    
    try:
        current_tab_state = ["stamm"]
        current_sub_tab_state = [""]
        fehler_container = ft.Column(spacing=5, visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        status_text = ft.Text("", color="yellow", weight="bold", size=18, text_align=ft.TextAlign.CENTER)

        maerkte = lade_maerkte()
        v, z = lade_benutzer()
        heute_str = datetime.datetime.now().strftime('%d.%m.%Y')
        aktuelle_daten = maerkte[markt_index] if (markt_index is not None and markt_index < len(maerkte)) else {"datum": heute_str, "mitarbeiter_name": f"{v} {z}".strip()}

        # Hilfsfunktionen
        def tf(label, val, hint="", w=None, oc=None, ob=None, multiline=False):
            return ft.TextField(label=label, value=val or "", hint_text=hint, multiline=multiline, hint_style=ft.TextStyle(color="white54", size=12), color="yellow", text_style=ft.TextStyle(size=14, color="yellow"), label_style=ft.TextStyle(color="white", size=14), border_color="white", content_padding=15, width=w, on_change=oc, on_blur=ob)

        def combo(label, val, opts, w=None, oc=None, multiline=True):
            echter_wert = val if val is not None else ""
            c = ft.TextField(label=label, value=echter_wert, color="yellow", text_style=ft.TextStyle(size=14, color="yellow"), label_style=ft.TextStyle(color="white", size=12), border_color="white", dense=True, content_padding=15, width=w, on_change=oc)
            items = [ft.PopupMenuItem(content=ft.Text(o, size=14), on_click=lambda e, opt=o: (setattr(c, 'value', opt), c.update())) for o in opts]
            c.suffix = ft.PopupMenuButton(items=items, content=ft.Container(content=ft.Text("▼", color="white", size=16), padding=5))
            return c

        def cb(label, val, oc=None, bold=False):
            return ft.Checkbox(label=label, value=bool(val), on_change=oc, label_style=ft.TextStyle(color="white", size=16 if bold else 14, weight="bold" if bold else "normal"), fill_color="yellow", check_color="black")

        # --- UI KOMPONENTEN ---
        tag_dd, mon_dd, jahr_dd = combo("Tag", "", tage_opts), combo("Mon", "", mon_opts), combo("Jahr", "", jahr_opts)
        datum_row = ft.Column([ft.Text("Datum der Probenahme", color="white", weight="bold", size=16), ft.Row([tag_dd, mon_dd, jahr_dd])])
        adr_in = tf("Adresse Markt", aktuelle_daten.get("adresse", ""))
        nr_in = tf("Marktnummer", aktuelle_daten.get("marktnummer", ""))
        auft_in = tf("Auftragsnummer", aktuelle_daten.get("auftragsnummer", ""))
        name_in = tf("Name Probenehmer", aktuelle_daten.get("mitarbeiter_name", ""))
        
        # Trinkwasser
        tw_kalt_cb = cb("Trinkwasser kalt", aktuelle_daten.get("tw_kalt", False), bold=True)
        tw_zeit_in, tw_temp_in = tf("Probenahmezeit", ""), tf("Temp", "")
        
        # Fleisch (Beispiel HFM)
        hfm_hack_cb = cb("Hackfleisch gemischt", False, bold=True)
        hfm_hack_temp_in = tf("Temp", "")
        hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd = combo("Tag", "", tage_opts), combo("Mon", "", mon_opts)
        hfm_hack_lief_schwein_in = tf("Lief. Schwein", "")
        hfm_hack_charge_schwein_dd = combo("Charge Schwein", "", c_opts_s)
        
        # --- LOGIK ---
        def reset_fehler_markierungen():
            for ctrl in markierte_fehler_controls:
                if hasattr(ctrl, "border_color"): ctrl.border_color = "white"
                if isinstance(ctrl, ft.Checkbox): ctrl.fill_color = "yellow"; ctrl.label_style.color = "white"
                try: ctrl.update()
                except: pass
            markierte_fehler_controls.clear()

        def check_pflichtfelder():
            reset_fehler_markierungen()
            errors = []
            
            def err(msg, ctrl):
                errors.append(msg)
                if ctrl and hasattr(ctrl, "border_color"):
                    ctrl.border_color = "red"
                    if isinstance(ctrl, ft.Checkbox):
                        ctrl.fill_color = "red"
                        ctrl.label_style.color = "red"
                    markierte_fehler_controls.append(ctrl)
                    try: ctrl.update()
                    except: pass

            # Prüfung Beispiel: HFM
            if (hfm_hack_temp_in.value or "").strip() and not hfm_hack_cb.value:
                err("Hackfleisch: Daten eingetragen, Haken fehlt!", hfm_hack_cb)
            elif hfm_hack_cb.value:
                if not (hfm_hack_temp_in.value or "").strip(): err("Hack: Temp fehlt", hfm_hack_temp_in)
                if not (hfm_hack_herst_tag_dd.value or "").strip() or not (hfm_hack_herst_mon_dd.value or "").strip():
                    err("Hack: Herstellungsdatum fehlt", hfm_hack_herst_tag_dd)

            return errors

        def save_final(e):
            errs = check_pflichtfelder()
            if errs:
                fehler_container.controls.clear()
                for e in errs: fehler_container.controls.append(ft.Text(e, color="red"))
                fehler_container.visible = True
                page.update()
            else:
                # PDF erstellen...
                pass

        def switch_tab(tab_id, sub_tab_id=None):
            nonlocal top_nav, haupt_bereich
            haupt_bereich.controls.clear()
            # ... UI befüllen basierend auf Tab ...
            page.update()

        ansicht.controls.extend([top_nav, haupt_bereich, fehler_container, status_text])
        switch_tab("stamm")
    except Exception as ex: 
        ansicht.controls.append(ft.Text(f"CRASH: {str(ex)}", color="red"))
        page.update()
