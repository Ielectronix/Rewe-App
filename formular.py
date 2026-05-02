
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
        maerkte = lade_maerkte()
        v, z = lade_benutzer()
        heute_str = datetime.datetime.now().strftime('%d.%m.%Y')
        aktuelle_daten = maerkte[markt_index] if markt_index is not None else {"datum": heute_str, "mitarbeiter_name": f"{v} {z}".strip()}

        def tf(label, val, hint="", w=320, oc=None, ob=None):
            return ft.TextField(label=label, value=val or "", hint_text=hint, color="yellow", border_color="white", width=w, on_change=oc, on_blur=ob, text_style=ft.TextStyle(size=12))

        def combo(label, val, opts, w=320, oc=None):
            echter_wert = val if val else (opts[0] if opts else "")
            c = ft.TextField(label=label, value=echter_wert, color="yellow", border_color="white", content_padding=10, width=w, on_change=oc)
            items = [ft.PopupMenuItem(content=ft.Text(o), on_click=lambda e, opt=o: (setattr(c, 'value', opt), c.update())) for o in opts]
            c.suffix = ft.PopupMenuButton(items=items, content=ft.Text("▼", color="white"))
            return c
            
        def action_btn_form(text, oc, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=13, weight="bold"), 
                on_click=oc, bgcolor="#0b1a0b", color=farbe, 
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=12, side=ft.BorderSide(width=1.5, color=farbe))
            )
            
        def emoji_btn(text, oc, farbe):
            return ft.ElevatedButton(text, on_click=oc, bgcolor="#1a1a1a", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10, side=ft.BorderSide(width=1.5, color=farbe)))

        htoday, mtoday, jtoday = heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2]
        def get_herst(key):
            val = str(aktuelle_daten.get(key, "")).strip()
            if not val or len(val.split(".")) != 3: return htoday, mtoday, jtoday
            return val.split(".")[0], val.split(".")[1], val.split(".")[2]

        tage_opts, mon_opts, jahr_opts = [""]+[f"{i:02d}" for i in range(1,32)], [""]+[f"{i:02d}" for i in range(1,13)], [""]+[str(i) for i in range(2024,2035)]
        
        # UI ELEMENTE
        nr_in = tf("Marktnummer", aktuelle_daten.get("marktnummer", ""))
        adr_in = tf("Adresse Markt", aktuelle_daten.get("adresse", ""))
        auft_in = tf("Auftragsnummer", aktuelle_daten.get("auftragsnummer", ""))
        name_in = tf("Name Probenehmer", aktuelle_daten.get("mitarbeiter_name", ""))
        ag_dd = combo("Auftraggeber", aktuelle_daten.get("auftraggeber"), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund"])
        typ_dd = combo("Typ", aktuelle_daten.get("typ_probenahme"), ["Standard", "Nachkontrolle"])
        
        fehler_text = ft.Text("", color="red", weight="bold", visible=False)
        status_text = ft.Text("", color="yellow", weight="bold")

        def save_final(e):
            fehler_text.visible = False; status_text.value = "⏳ Erstelle PDF..."; page.update()
            if not nr_in.value: fehler_text.value = "⚠️ Marktnummer fehlt!"; fehler_text.visible = True; page.update(); return
            try:
                d = hole_aktuelle_daten()
                saved_path = erstelle_bericht(d)
                fname = os.path.basename(saved_path)
                status_text.value = f"✅ NEU GESPEICHERT!\nDatei: {fname}"; status_text.color = "green"
                page.update()
            except Exception as ex:
                fehler_text.value = f"❌ FEHLER: {str(ex)}"; fehler_text.visible = True; page.update()

        # Haupt-Tabs
        top_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        haupt_bereich = ft.Column(spacing=15)
        
        def switch_tab(tab_id):
            haupt_bereich.controls.clear(); top_nav.controls.clear()
            tabs = [("stamm", "Stammdaten"), ("tw", "Trinkwasser"), ("se", "Scherbeneis"), ("hfm", "HFM"), ("og", "Proben")]
            for tid, tname in tabs:
                is_act = (tid == tab_id)
                btn = ft.ElevatedButton(tname, on_click=lambda e, t=tid: switch_tab(t), bgcolor="#004400" if is_act else "#1a1a1a", color="white",
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=12, side=ft.BorderSide(width=1.5, color="#4CAF50")))
                top_nav.controls.append(btn)
            
            if tab_id == "stamm": haupt_bereich.controls.extend([vorlagen_expansion, ft.Divider(color="white24"), ft.Text("Stammdaten", size=20, weight="bold"), datum_row, adr_in, nr_in, auft_in, ag_dd, name_in, typ_dd, bem_in])
            elif tab_id == "hfm":
                sub_nav = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
                haupt_bereich.controls.extend([ft.Text("HFM Fleisch", size=20, weight="bold"), sub_nav])
                for sid, sname in [("hack","🥩 Hack"), ("mett","🍖 Mett"), ("fzs","🐷 FZS"), ("fzg","🐔 FZG"), ("bio","🥩 Bio"), ("okz","🔬 OKZ")]:
                    is_sub_act = (sid == "hack")
                    btn = ft.ElevatedButton(sname, bgcolor="#004400" if is_sub_act else "#1a1a1a", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=5, side=ft.BorderSide(width=1, color="#4CAF50")))
                    sub_nav.controls.append(btn)
            page.update()

        def hole_aktuelle_daten():
            return {"marktnummer": nr_in.value, "adresse": adr_in.value, "datum": heute_str, "mitarbeiter_name": name_in.value}

        # ==========================================
        # VORLAGEN LOGIK (JETZT ZUM AUFKLAPPEN!)
        # ==========================================
        alle_vorlagen = lade_vorlagen_lokal()
        vorlagen_status = ft.Text("", weight="bold", size=12) 
        vl_dd = ft.Dropdown(options=[ft.dropdown.Option(k) for k in alle_vorlagen.keys()], hint_text="Vorlage wählen...", dense=True, content_padding=10, color="yellow", text_style=ft.TextStyle(color="yellow", size=12), border_color="white", width=200)
        vl_name_in = tf("Als neue Vorlage speichern", "", w=200)

        def lade_v(e):
            if not vl_dd.value: return
            v = alle_vorlagen.get(vl_dd.value, {})
            if "name_in" in v: name_in.value = v["name_in"]
            if "ag_dd" in v: ag_dd.value = v["ag_dd"]
            if "typ_dd" in v: typ_dd.value = v["typ_dd"]
            vorlagen_status.value = f"✅ '{vl_dd.value}' geladen!"; vorlagen_status.color = "green"; page.update()
            
        def del_v(e):
            if vl_dd.value in alle_vorlagen:
                del alle_vorlagen[vl_dd.value]; speichere_vorlagen_lokal(alle_vorlagen)
                vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
                vorlagen_status.value = f"🗑️ Gelöscht!"; vorlagen_status.color = "red"; vl_dd.value = None; page.update()
                
        def save_v(e):
            if not (vl_name_in.value or "").strip(): return
            alle_vorlagen[vl_name_in.value] = {"name_in": name_in.value, "ag_dd": ag_dd.value, "typ_dd": typ_dd.value}
            speichere_vorlagen_lokal(alle_vorlagen)
            vl_dd.options = [ft.dropdown.Option(k) for k in alle_vorlagen.keys()]
            vorlagen_status.value = f"✅ Vorlage gespeichert!"; vorlagen_status.color = "orange"; vl_name_in.value = ""; page.update()

        # FIX: Das ist das einklappbare Menü! Spart unglaublich viel Platz.
        vorlagen_expansion = ft.ExpansionTile(
            title=ft.Text("📋 Vorlagen laden / speichern", weight="bold", color="white"),
            collapsed_text_color="white",
            text_color="#4CAF50",
            controls=[
                ft.Container(
                    bgcolor="#002b00", padding=15, border_radius=10,
                    content=ft.Column([
                        vorlagen_status,
                        ft.Row([vl_dd, emoji_btn("📥", lade_v, "#2196F3"), emoji_btn("🗑️", del_v, "#F44336")]),
                        ft.Row([vl_name_in, emoji_btn("💾", save_v, "#FF9800")])
                    ])
                )
            ]
        )
        
        # FIX: Der graue Balken-Killer! Keine "expand=1" mehr in diesen Elementen.
        bottom_buttons = ft.Row(
            controls=[
                action_btn_form("🚚 Touren", lambda e: zeige_dashboard(), "#F44336"),
                action_btn_form("🔄 Reset", lambda e: reset_form(e), "#9C27B0"),
                action_btn_form("💾 Speichern", lambda e: None, "#FF9800"),
                action_btn_form("📄 Bericht", save_final, "#2196F3"),
            ],
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

        ansicht.controls.extend([
            top_nav, ft.Divider(color="white24"), haupt_bereich, ft.Container(height=20),
            fehler_text, status_text,
            bottom_buttons
        ])
        
        # Dummys für layout tests (ersetzt durch echte ui später)
        d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
        tag_dd, mon_dd, jahr_dd = combo("Tag", d_tag, tage_opts, 90), combo("Mon", d_mon, mon_opts, 90), combo("Jahr", d_jahr, jahr_opts, 120)
        datum_row = ft.Column([ft.Text("Datum der Probenahme", color="white", weight="bold"), ft.Row([tag_dd, mon_dd, jahr_dd], wrap=True)])
        bem_in = tf("Zusätzliche Bemerkung", aktuelle_daten.get("bemerkung", ""))

        switch_tab("stamm")
    except Exception as ex: zeige_fehler(ex)