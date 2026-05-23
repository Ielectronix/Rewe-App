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
    try:
        ansicht.controls.clear()
        ansicht.horizontal_alignment = ft.CrossAxisAlignment.STRETCH 
        
        # UI Elemente Definitionen
        haupt_bereich = ft.Column(spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        top_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        
        current_tab_state = ["stamm"]
        current_sub_tab_state = [""]
        markierte_fehler_controls = [] 
        
        fehler_container = ft.Column(spacing=5, visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        status_text = ft.Text("", color="yellow", weight="bold", size=18, text_align=ft.TextAlign.CENTER)

        maerkte = lade_maerkte()
        v, z = lade_benutzer()
        heute_str = datetime.datetime.now().strftime('%d.%m.%Y')
        aktuelle_daten = maerkte[markt_index] if (markt_index is not None and markt_index < len(maerkte)) else {"datum": heute_str, "mitarbeiter_name": f"{v} {z}".strip()}

        # Hilfsfunktionen für UI
        def tf(label, val, hint="", w=None, oc=None, ob=None, multiline=False):
            return ft.TextField(label=label, value=val or "", hint_text=hint, multiline=multiline, hint_style=ft.TextStyle(color="white54", size=12), color="yellow", text_style=ft.TextStyle(size=14, color="yellow"), label_style=ft.TextStyle(color="white", size=14), border_color="white", content_padding=15, width=w, on_change=oc, on_blur=ob)

        def combo(label, val, opts, w=None, oc=None, multiline=True):
            is_date = label in ["Tag", "Mon", "Jahr"]
            pad = 5 if is_date else 15
            echter_wert = val if val is not None else ""
            c = ft.TextField(label=label, value=echter_wert, multiline=False if is_date else multiline, color="yellow", text_style=ft.TextStyle(size=14, color="yellow"), label_style=ft.TextStyle(color="white", size=12 if is_date else 14), border_color="white", dense=True, content_padding=pad, width=w, on_change=oc)
            items = [ft.PopupMenuItem(content=ft.Text(o, size=14), on_click=lambda e, opt=o: (setattr(c, 'value', opt), c.update())) for o in opts]
            c.suffix = ft.PopupMenuButton(items=items, content=ft.Container(content=ft.Text("▼", color="white", size=16), padding=pad))
            return c
            
        def action_btn_form(text, oc, farbe):
            return ft.ElevatedButton(content=ft.Text(text, size=16, weight="bold"), on_click=oc, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=20, side=ft.BorderSide(width=2, color=farbe)))
            
        def emoji_btn(text, oc, farbe):
            return ft.ElevatedButton(text, on_click=oc, bgcolor="#1a1a1a", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=15, side=ft.BorderSide(width=1.5, color=farbe)))

        def parse_datum(d, dt="", dm="", dj=""):
            if not d: return dt, dm, dj
            p = d.split(".")
            return (p[0], p[1], p[2]) if len(p)==3 else (dt, dm, dj)

        def get_date_str(t, m, j):
            t, m, j = (t or "").strip(), (m or "").strip(), (j or "").strip()
            return f"{t}.{m}.{j}" if (t or m or j) else ""

        def format_zeit(e):
            val = e.control.value or ""
            zahlen = "".join([c for c in val if c.isdigit()])[:4]
            neu = zahlen[:2] + ":" + zahlen[2:] if len(zahlen) >= 3 else zahlen
            if e.control.value != neu: e.control.value = neu; e.control.update()

        def format_temp(e):
            val = (e.control.value or "").strip().replace(" °C", "").replace("°C", "").strip()
            if val: e.control.value = val + " °C"; e.control.update()

        def cb(label, val, oc=None, bold=False):
            return ft.Checkbox(label=label, value=bool(val), on_change=oc, label_style=ft.TextStyle(color="white", size=16 if bold else 14, weight="bold" if bold else "normal"), fill_color="yellow", check_color="black")

        def d_row(t_dd, m_dd, j_dd):
            return ft.Row([ft.Container(content=t_dd, expand=1), ft.Container(content=m_dd, expand=1), ft.Container(content=j_dd, expand=1)], spacing=5)

        # UI Komponenten Definitionen (Stamm, TW, SE, HFM, OG - unverändert wie zuvor)
        htoday, mtoday, jtoday = heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2]
        d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), htoday, mtoday, jtoday)
        tag_dd, mon_dd, jahr_dd = combo("Tag", d_tag, tage_opts), combo("Mon", d_mon, mon_opts), combo("Jahr", d_jahr, jahr_opts)
        datum_row = ft.Column([ft.Text("Datum der Probenahme", color="white", weight="bold", size=16), d_row(tag_dd, mon_dd, jahr_dd)])
        
        adr_in = tf("Adresse Markt", aktuelle_daten.get("adresse", ""), multiline=True)
        nr_in = tf("Marktnummer", aktuelle_daten.get("marktnummer", ""))
        auft_in = tf("Auftragsnummer", aktuelle_daten.get("auftragsnummer", ""), "Etikettenummer: XX-XXXXXXX")
        name_in = tf("Name Probenehmer", aktuelle_daten.get("mitarbeiter_name", ""))
        bem_in = tf("Zusätzliche Bemerkung", aktuelle_daten.get("bemerkung", ""), multiline=True)
        ag_dd = combo("Auftraggeber", aktuelle_daten.get("auftraggeber", "03509 - REWE Hackfleischmonitoring"), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund (Hackfleischmonitoring)"])
        typ_dd = combo("Typ der Probenahme", aktuelle_daten.get("typ_probenahme", "Standard"), ["Standard", "Nachkontrolle", "Mehrwöchig"])

        tw_kalt_cb = cb("Trinkwasser kalt", aktuelle_daten.get("tw_kalt", False), bold=True)
        tw_override_cb = cb("Trotzdem speichern", aktuelle_daten.get("tw_override", False))
        tw_zeit_in, tw_temp_in, tw_tempkonst_in = tf("Probenahmezeit", aktuelle_daten.get("tw_zeit", ""), ob=format_zeit), tf("Temp Probenahme", aktuelle_daten.get("tw_temp", ""), ob=format_temp), tf("Temp Konstante", aktuelle_daten.get("tw_tempkonst", ""), ob=format_temp)
        # ... (restliche Komponenten TW, SE, HFM, OG bleiben wie im vorherigen Code unverändert)
        # (Um den Rahmen nicht zu sprengen, hier die Logik-Blöcke)

        # Die Logik-Funktionen (hole_aktuelle_daten, check_pflichtfelder, etc.) müssen hier hin.
        # Wichtig: reset_fehler_markierungen und check_pflichtfelder verwenden die Variablen aus dem lokalen Scope.

        def switch_tab(tab_id, sub_tab_id=None):
            nonlocal top_nav, haupt_bereich # <-- HIER IST DIE KORREKTUR
            current_tab_state[0] = tab_id
            haupt_bereich.controls.clear(); top_nav.controls.clear()
            # ... (Rest der Tab-Logik)
            if page: page.update()

        # ... (Abschluss der Funktion)
        ansicht.controls.extend([top_nav, ft.Divider(color="white24"), haupt_bereich, ft.Container(height=20), fehler_container, status_text, bottom_buttons])
        switch_tab("stamm")
    except Exception as ex: 
        if zeige_fehler: zeige_fehler(ex)
        else: ansicht.controls.append(ft.Text(f"CRASH: {str(ex)}", color="red"))
