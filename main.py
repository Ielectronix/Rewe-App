import flet as ft
import traceback
import json
import os
import datetime
import shutil
import urllib.parse
 
def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO
    
    # Setzt das Icon für die App-Fenster
    try:
        page.window.icon = "icon.png"
    except: pass
 
    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    page.add(ansicht)
 
    # PFADE
    def get_rewe_paths():
        heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
        primary_base = "/storage/emulated/0/Download"
        fallback_base = "/storage/emulated/0/Android/media"
        desktop_base = os.path.join(os.path.expanduser("~"), "Downloads")

        # Prüfen, wo gespeichert werden kann
        if os.path.exists(primary_base):
            rewe_dir = os.path.join(primary_base, "REWE")
            try:
                os.makedirs(rewe_dir, exist_ok=True)
                # Testen, ob wir Schreibrechte haben
                test_file = os.path.join(rewe_dir, ".test_write")
                with open(test_file, "w") as f: f.write("ok")
                os.remove(test_file)
                display_pfad = "Downloads / REWE"
            except (PermissionError, OSError):
                # GEHEIMTRICK: Ausweichen auf Android/media bei fehlenden Rechten
                rewe_dir = os.path.join(fallback_base, "REWE")
                os.makedirs(rewe_dir, exist_ok=True)
                display_pfad = "Android / media / REWE"
        elif os.path.exists(fallback_base):
            rewe_dir = os.path.join(fallback_base, "REWE")
            os.makedirs(rewe_dir, exist_ok=True)
            display_pfad = "Android / media / REWE"
        else:
            rewe_dir = os.path.join(desktop_base, "REWE")
            display_pfad = "Downloads / REWE"

        temp_dir = os.path.join(rewe_dir, "temp")
        final_dir = os.path.join(rewe_dir, heute_ordner)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_dir, exist_ok=True)

        return temp_dir, final_dir, heute_ordner, display_pfad
 
    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=20))
        try:
            ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=12))
        except: pass
        page.update()
 
    try:
        import pypdf
        from pypdf.generic import DictionaryObject, NameObject, ArrayObject
 
        SPEICHER_DATEI = "meine_monitoring_daten.json"
        BENUTZER_DATEI = "benutzer_daten.json"
        VORLAGEN_DATEI = "tour_vorlagen.json"
 
        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", size=12),
                on_click=on_click, bgcolor=bgcolor, color=color,
                expand=expand, height=height, width=width,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=5)
            )
 
        def lade_maerkte():
            if os.path.exists(SPEICHER_DATEI):
                with open(SPEICHER_DATEI, "r", encoding="utf-8") as d: return json.load(d)
            return []
 
        def speichere_maerkte(liste):
            with open(SPEICHER_DATEI, "w", encoding="utf-8") as d: json.dump(liste, d)
 
        def lade_benutzer():
            if os.path.exists(BENUTZER_DATEI):
                with open(BENUTZER_DATEI, "r", encoding="utf-8") as d:
                    daten = json.load(d); return daten.get("vorname", ""), daten.get("zuname", "")
            return "", ""
 
        def speichere_benutzer(v, z):
            with open(BENUTZER_DATEI, "w", encoding="utf-8") as d: json.dump({"vorname": v, "zuname": z}, d)
 
        def lade_vorlagen():
            if os.path.exists(VORLAGEN_DATEI):
                with open(VORLAGEN_DATEI, "r", encoding="utf-8") as d: return json.load(d)
            return {}
 
        def speichere_vorlagen(daten):
            with open(VORLAGEN_DATEI, "w", encoding="utf-8") as d: json.dump(daten, d)
 
        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=10, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("Touren", lambda e: zeige_dashboard(), "#004400", "white"),
                    sicherer_button("Postausg.", lambda e: zeige_postausgang(), "#004400", "white"),
                    sicherer_button("Archiv", lambda e: zeige_archiv(), "#004400", "white")
                ])
            )
 
        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            stil_label_weiss = ft.TextStyle(color="white")
            stil_hint_weiss = ft.TextStyle(color="white", size=12)
            
            v_in = ft.TextField(label="Vorname", hint_text="Dein Vorname", hint_style=stil_hint_weiss, value=v, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            z_in = ft.TextField(label="Nachname", hint_text="Dein Nachname", hint_style=stil_hint_weiss, value=z, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value); zeige_dashboard()
                
            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            header = ft.Text(spans=[ft.TextSpan("REWE ", ft.TextStyle(color="red", weight="bold", size=32)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=32))], text_align=ft.TextAlign.CENTER)
            ansicht.controls.extend([ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(height=40), ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)])
            page.update()
 
        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Row([ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white")], alignment=ft.MainAxisAlignment.CENTER))
            if not maerkte:
                ansicht.controls.append(ft.Row([ft.Text("Noch keine Touren angelegt.", color="grey", size=16)], alignment=ft.MainAxisAlignment.CENTER))
            else:
                for index, markt in enumerate(maerkte):
                    adr = (markt.get("adresse") or "").strip() or "Unbenannter Markt"
                    buchstabe = chr(65 + index) if index < 26 else str(index)
                    def loesche_t(e, i=index): maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    btn_tour = sicherer_button(f"Tour {buchstabe}: {adr}", lambda e, i=index: zeige_maske(i), "#005500", "white", expand=True, height=50)
                    btn_del = sicherer_button("🗑️", loesche_t, "red", "white", height=50, width=65)
                    ansicht.controls.append(ft.Row([btn_tour, btn_del]))
            ansicht.controls.append(ft.Divider(color="white"))
            btn_neu = sicherer_button("Tour voranlegen", lambda e: zeige_maske(None), "red", "white", height=50)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()
 
        def zeige_maske(markt_index):
            try:
                ansicht.controls.clear()
                maerkte = lade_maerkte()
                v, z = lade_benutzer()
                heute_str = datetime.datetime.now().strftime('%d.%m.%Y')
                if markt_index is None:
                    aktuelle_daten = {"datum": heute_str, "adresse": "", "marktnummer": "", "auftragsnummer": "", "mitarbeiter_name": f"{v} {z}".strip(), "auftraggeber": "03509 - REWE Hackfleischmonitoring", "typ_probenahme": "Standard", "bemerkung": ""}
                    titel = "Neue Tour anlegen"
                else:
                    aktuelle_daten = maerkte[markt_index]
                    titel = "Tour bearbeiten"
 
                stil_tf_gelb_12 = ft.TextStyle(color="yellow", size=12)
                stil_label_weiss = ft.TextStyle(color="white")
                stil_cb_weiss = ft.TextStyle(color="white", size=12)
                stil_hint_weiss = ft.TextStyle(color="white54", size=12)
 
                tage_opts = [""] + [f"{i:02d}" for i in range(1, 32)]
                mon_opts = [""] + [f"{i:02d}" for i in range(1, 13)]
                jahr_opts = [""] + [str(i) for i in range(2024, 2035)]
                charge_opts_s = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Schweinehackfleisch"]
                charge_opts_r = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Rinderhackfleisch"]
                charge_opts_g = ["z. Z. nicht vorrätig", "keine Eigenproduktion", "Bitte eingeben", "Kein Geflügel"]
                entnahmeort_opts = ["Fischabteilung", "Produktionsraum", "Bedientheke", "Vorbereitungsraum", "Metzgerei", "Kühlraum", "SB-Theke"]
                verpackung_opts = ["steriler Probenbecher", "steriler Probenbeutel", "Transportverpackung", "Kunststoffbecher mit Anrolldeckel u. etikett", "Pappschale mit Kunststofffolie umwickelt", "tiefgezogene Kunststoffschale mit Anrollfolie", "Styroporschale mit Kunststofffolie umwickelt", "SB-Kunststoffverpackung"]
 
                def parse_datum(datum_str, def_t="", def_m="", def_j=""):
                    if not datum_str: return def_t, def_m, def_j
                    parts = datum_str.split(".")
                    if len(parts) == 3: return parts[0], parts[1], parts[2]
                    return def_t, def_m, def_j

                def get_date_str(t, m, j):
                    t, m, j = (t or "").strip(), (m or "").strip(), (j or "").strip()
                    return f"{t}.{m}.{j}" if (t or m or j) else ""
 
                def erstelle_combo(label_text, wert, optionen, groesse=12, ausdehnbar=1, on_change_func=None):
                    combo = ft.TextField(label=label_text, value=wert, color="yellow", text_style=ft.TextStyle(size=groesse, color="yellow"), label_style=stil_label_weiss, border_color="white", expand=ausdehnbar, content_padding=5, on_change=lambda e: on_change_func(e) if on_change_func else None)
                    items = [ft.PopupMenuItem(content=ft.Text(opt), on_click=lambda e, o=opt: (setattr(combo, "value", o), combo.update(), on_change_func(e) if on_change_func else None)) for opt in optionen]
                    combo.suffix = ft.PopupMenuButton(items=items, icon="arrow_drop_down", icon_color="white")
                    return combo
 
                def hat_charge_wert(val): return bool(val and val != "Bitte eingeben")
                def cb_row(links, rechts): return ft.Row([ft.Container(links, expand=1), ft.Container(rechts, expand=1)], vertical_alignment=ft.CrossAxisAlignment.CENTER)
 
                # UI Felder Initialisierung
                d_tag, d_mon, d_jahr = parse_datum(aktuelle_daten.get("datum", heute_str), heute_str.split(".")[0], heute_str.split(".")[1], heute_str.split(".")[2])
                tag_dd, mon_dd, jahr_dd = erstelle_combo("Tag", d_tag, tage_opts, ausdehnbar=3), erstelle_combo("Mon", d_mon, mon_opts, ausdehnbar=3), erstelle_combo("Jahr", d_jahr, jahr_opts, ausdehnbar=4)
                datum_row = ft.Column([ft.Text("Datum der Probenahme", color="white", weight="bold"), ft.Row([tag_dd, mon_dd, jahr_dd])])
                adr_in = ft.TextField(label="Adresse Markt", value=aktuelle_daten.get("adresse"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                nr_in = ft.TextField(label="Marktnummer", value=aktuelle_daten.get("marktnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                auft_in = ft.TextField(label="Auftragsnummer", value=aktuelle_daten.get("auftragsnummer"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                name_in = ft.TextField(label="Name Probenehmer", value=aktuelle_daten.get("mitarbeiter_name"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                bem_in = ft.TextField(label="Zusätzliche Bemerkung", value=aktuelle_daten.get("bemerkung"), color="yellow", text_style=stil_tf_gelb_12, label_style=stil_label_weiss, border_color="white", content_padding=10, expand=True)
                ag_dd = erstelle_combo("Auftraggeber", aktuelle_daten.get("auftraggeber", ""), ["03509 - REWE Hackfleischmonitoring", "3001767 - REWE Dortmund (Hackfleischmonitoring)"])
                typ_dd = erstelle_combo("Typ der Probenahme", aktuelle_daten.get("typ_probenahme", "Standard"), ["Standard", "Nachkontrolle", "Mehrwöchig"])
                lims_warnung = ft.Text("⚠️ HINWEIS: Aktivierungs-Haken fehlt!", color="red", weight="bold", visible=False)
                lims_override_cb = ft.Checkbox(label="Trotzdem speichern", visible=False, label_style=stil_cb_weiss, fill_color="red", check_color="white")
 
                tw_kalt_cb = ft.Checkbox(label="Trinkwasser kalt", value=aktuelle_daten.get("tw_kalt", False), label_style=stil_label_weiss, fill_color="yellow", check_color="black")
                tw_zeit_in = ft.TextField(label="Zeit", value=aktuelle_daten.get("tw_zeit"), color="yellow")
                tw_temp_in = ft.TextField(label="Temp", value=aktuelle_daten.get("tw_temp"), color="yellow")
                tw_tempkonst_in = ft.TextField(label="Konst", value=aktuelle_daten.get("tw_tempkonst"), color="yellow")
                tw_desinf_dd = erstelle_combo("Desinf", aktuelle_daten.get("tw_desinf", "Abflammen"), ["Abflammen"])
                tw_zapf_dd = erstelle_combo("Zapf", aktuelle_daten.get("tw_zapf", "Spülbecken"), ["Spülbecken"])
                tw_zapf_sonst_dd = erstelle_combo("Sonst", aktuelle_daten.get("tw_zapf_sonst", ""), ["Schlauch"])
                tw_inaktiv_dd = erstelle_combo("Inakt", aktuelle_daten.get("tw_inaktiv", "Na-Thiosulfat"), ["Na-Thiosulfat"])
                tw_kurz1_dd = erstelle_combo("Farbe", aktuelle_daten.get("tw_kurz1", "1"), ["1"])
                tw_kurz2_dd = erstelle_combo("Trübung", aktuelle_daten.get("tw_kurz2", "1"), ["1"])
                tw_kurz3_dd = erstelle_combo("Boden", aktuelle_daten.get("tw_kurz3", "1"), ["1"])
                tw_kurz4_dd = erstelle_combo("Geruch", aktuelle_daten.get("tw_kurz4", "1"), ["1"])
                tw_zweck_dd = erstelle_combo("Zweck", aktuelle_daten.get("tw_zweck", "Zweck B"), ["Zweck B"])
                tw_inhalt_in = ft.TextField(label="Inhalt", value=aktuelle_daten.get("tw_inhalt", "500ml"), color="yellow")
                tw_verpackung_dd = erstelle_combo("Verp", aktuelle_daten.get("tw_verpackung", "Flasche"), ["Flasche"])
                tw_entnahmeort_dd = erstelle_combo("Ort", aktuelle_daten.get("tw_entnahmeort", "Metzgerei"), ["Metzgerei"])
                tw_bemerkung_dd = erstelle_combo("Bem", aktuelle_daten.get("tw_bemerkung", "Keine"), ["Keine"])
                cb_pn, cb_ein, cb_zwei, cb_ein_g, cb_sensor, cb_eck, cb_knie = ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox()
                cb_auff_ja, cb_auff_nein, cb_auff_perl, cb_auff_verkalk, cb_auff_verbrueh, cb_auff_durchlauf, cb_auff_unterbau, cb_auff_eck_zu, cb_auff_nichtmoeglich, cb_auff_dusche, cb_auff_handbrause, cb_auff_sonst = ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox(), ft.Checkbox()
                tw_unterbau_l_in, tw_auff_sonstiges_in = ft.TextField(), ft.TextField()
                se_kalt_cb, se_zeit_in, se_zapf_dd, se_cb_eiswanne, se_cb_fallprobe, se_tech_sonst_in, se_desinf_dd, se_cb_ozon, se_auff_sonst_in, se_inhalt_in, se_verpackung_dd, se_entnahmeort_dd, se_temp_in, se_bemerkung_dd = ft.Checkbox(), ft.TextField(), ft.TextField(), ft.Checkbox(), ft.Checkbox(), ft.TextField(), ft.TextField(), ft.Checkbox(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField()
                se_okz_cb, se_okz_bemerkung_dd = ft.Checkbox(), ft.TextField()
                se_okz_controls = {i: {"status": ft.TextField(), "objekt": ft.TextField(), "ort": ft.TextField(), "abklatsch": ft.Checkbox(), "tupfer": ft.Checkbox()} for i in range(1, 4)}
                hfm_hack_cb, hfm_hack_entnahmeort_dd, hfm_hack_herst_tag_dd, hfm_hack_herst_mon_dd, hfm_hack_herst_jahr_dd, hfm_hack_inhalt_in, hfm_hack_verpackung_dd, hfm_hack_lief_schwein_in, hfm_hack_lief_rind_in, hfm_hack_mhd_s_tag_dd, hfm_hack_mhd_s_mon_dd, hfm_hack_mhd_s_jahr_dd, hfm_hack_mhd_r_tag_dd, hfm_hack_mhd_r_mon_dd, hfm_hack_mhd_r_jahr_dd, hfm_hack_charge_schwein_dd, hfm_hack_charge_rind_dd, hfm_hack_temp_in, hfm_hack_bemerkung_dd = ft.Checkbox(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField()
                hfm_mett_cb, hfm_mett_entnahmeort_dd, hfm_mett_herst_tag_dd, hfm_mett_herst_mon_dd, hfm_mett_herst_jahr_dd, hfm_mett_inhalt_in, hfm_mett_verpackung_dd, hfm_mett_lief_in, hfm_mett_mhd_tag_dd, hfm_mett_mhd_mon_dd, hfm_mett_mhd_jahr_dd, hfm_mett_charge_dd, hfm_mett_temp_in, hfm_mett_bemerkung_dd = ft.Checkbox(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField()
                hfm_fzs_cb, hfm_fzs_entnahmeort_dd, hfm_fzs_produkt_in, hfm_fzs_marinade_in, hfm_fzs_herst_tag_dd, hfm_fzs_herst_mon_dd, hfm_fzs_herst_jahr_dd, hfm_fzs_inhalt_in, hfm_fzs_verpackung_dd, hfm_fzs_lief_in, hfm_fzs_mhd_tag_dd, hfm_fzs_mhd_mon_dd, hfm_fzs_mhd_jahr_dd, hfm_fzs_charge_dd, hfm_fzs_temp_in, hfm_fzs_bemerkung_dd = ft.Checkbox(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField()
                hfm_fzg_cb, hfm_fzg_entnahmeort_dd, hfm_fzg_produkt_in, hfm_fzg_marinade_in, hfm_fzg_herst_tag_dd, hfm_fzg_herst_mon_dd, hfm_fzg_herst_jahr_dd, hfm_fzg_inhalt_in, hfm_fzg_verpackung_dd, hfm_fzg_lief_in, hfm_fzg_mhd_tag_dd, hfm_fzg_mhd_mon_dd, hfm_fzg_mhd_jahr_dd, hfm_fzg_charge_dd, hfm_fzg_temp_in, hfm_fzg_bemerkung_dd = ft.Checkbox(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField()
                hfm_bio_cb, hfm_bio_entnahmeort_dd, hfm_bio_herst_tag_dd, hfm_bio_herst_mon_dd, hfm_bio_herst_jahr_dd, hfm_bio_inhalt_in, hfm_bio_verpackung_dd, hfm_bio_lief_schwein_in, hfm_bio_lief_rind_in, hfm_bio_mhd_s_tag_dd, hfm_bio_mhd_s_mon_dd, hfm_bio_mhd_s_jahr_dd, hfm_bio_mhd_r_tag_dd, hfm_bio_mhd_r_mon_dd, hfm_bio_mhd_r_jahr_dd, hfm_bio_charge_schwein_dd, hfm_bio_charge_rind_dd, hfm_bio_temp_in, hfm_bio_bemerkung_dd = ft.Checkbox(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField(), ft.TextField()
                hfm_okz_cb, hfm_okz_bemerkung_dd = ft.Checkbox(), ft.TextField()
                okz_controls = {f"{i:02d}": {"status": ft.TextField(), "objekt": ft.TextField(), "ort": ft.TextField(), "abklatsch": ft.Checkbox(), "tupfer": ft.Checkbox()} for i in range(1, 11)}
                og_cb, og_okz_cb, og_okz_bemerkung_dd, og_okz_anmerkung_in = ft.Checkbox(), ft.Checkbox(), ft.TextField(), ft.TextField()
                og_controls = {i: {"name": ft.TextField(), "ort": ft.TextField(), "h_t": ft.TextField(), "h_m": ft.TextField(), "h_j": ft.TextField(), "v_t": ft.TextField(), "v_m": ft.TextField(), "v_j": ft.TextField(), "inhalt": ft.TextField(), "verpackung": ft.TextField(), "temp": ft.TextField()} for i in range(1, 6)}
                og_okz_controls = {f"{i:02d}": {"status": ft.TextField(), "objekt": ft.TextField(), "ort": ft.TextField(), "abklatsch": ft.Checkbox(), "tupfer": ft.Checkbox()} for i in range(1, 6)}

                def hole_aktuelle_daten():
                    d = {"datum": f"{tag_dd.value}.{mon_dd.value}.{jahr_dd.value}", "adresse": adr_in.value, "marktnummer": nr_in.value, "auftragsnummer": auft_in.value, "mitarbeiter_name": name_in.value, "auftraggeber": ag_dd.value, "typ_probenahme": typ_dd.value, "bemerkung": bem_in.value, "tw_kalt": tw_kalt_cb.value, "tw_zeit": tw_zeit_in.value, "tw_temp": tw_temp_in.value, "tw_tempkonst": tw_tempkonst_in.value, "tw_desinf": tw_desinf_dd.value, "tw_zapf": tw_zapf_dd.value, "tw_cb_pn": cb_pn.value, "tw_cb_ein": cb_ein.value, "tw_cb_zwei": cb_zwei.value, "tw_cb_ein_g": cb_ein_g.value, "tw_cb_sensor": cb_sensor.value, "tw_cb_eck": cb_eck.value, "tw_cb_knie": cb_knie.value, "tw_zapf_sonst": tw_zapf_sonst_dd.value, "tw_inaktiv": tw_inaktiv_dd.value, "tw_kurz1": tw_kurz1_dd.value, "tw_kurz2": tw_kurz2_dd.value, "tw_kurz3": tw_kurz3_dd.value, "tw_kurz4": tw_kurz4_dd.value, "cb_auff_ja": cb_auff_ja.value, "cb_auff_nein": cb_auff_nein.value, "cb_auff_perl": cb_auff_perl.value, "cb_auff_verkalk": cb_auff_verkalk.value, "cb_auff_verbrueh": cb_auff_verbrueh.value, "cb_auff_durchlauf": cb_auff_durchlauf.value, "cb_auff_unterbau": cb_auff_unterbau.value, "tw_unterbau_l": tw_unterbau_l_in.value, "cb_auff_eck_zu": cb_auff_eck_zu.value, "cb_auff_nichtmoeglich": cb_auff_nichtmoeglich.value, "cb_auff_dusche": cb_auff_dusche.value, "cb_auff_handbrause": cb_auff_handbrause.value, "cb_auff_sonst": cb_auff_sonst.value, "tw_auff_sonstiges": tw_auff_sonstiges_in.value, "tw_zweck": tw_zweck_dd.value, "tw_inhalt": tw_inhalt_in.value, "tw_verpackung": tw_verpackung_dd.value, "tw_entnahmeort": tw_entnahmeort_dd.value, "tw_bemerkung": tw_bemerkung_dd.value}
                    return d

                def save_final(e):
                    try:
                        temp_dir, final_dir, heute_ordner, display_pfad = get_rewe_paths()
                        s_markt = "".join([c for c in nr_in.value if c.isalnum()])
                        base_name = f"REWE_{s_markt}_{datetime.datetime.now().strftime('%d%m%y')}"
                        final_ausg = os.path.join(final_dir, f"{base_name}.pdf")
                        counter = 1
                        while os.path.exists(final_ausg):
                            final_ausg = os.path.join(final_dir, f"{base_name}_{counter}.pdf")
                            counter += 1
                        
                        writer = pypdf.PdfWriter()
                        # (Hier steht die Logik zum Befüllen des PDFs...)
                        # ...
                        with open(final_ausg, "wb") as f: writer.write(f)
                        status_text.value = "✅ PDF erfolgreich erstellt!"
                        status_text.color = "green"
                        page.update()
                    except Exception as ex: 
                        zeige_fehler(ex)
 
                btn_zurueck = sicherer_button("🔙 Touren", lambda e: zeige_dashboard(), "red", "white", expand=True, height=45)
                btn_speichern = sicherer_button("💾 Tour speichern", lambda e: None, "orange", "black", expand=True, height=45)
                btn_final = sicherer_button("📄 Bericht erstellen (PDF)", save_final, "blue", "white", expand=True, height=50)
                _, _, _, ui_pfad = get_rewe_paths()
                info_pfad_text = ft.Text(f"ℹ️ PDFs werden gespeichert unter:\n{ui_pfad}", color="white54", size=12, italic=True, text_align=ft.TextAlign.CENTER)

                ansicht.controls.extend([nav_leiste(), ft.Text(titel, size=20, weight="bold", color="white"), datum_row, adr_in, nr_in, auft_in, name_in, info_pfad_text, ft.Row([btn_zurueck, btn_speichern]), ft.Row([btn_final])])
                page.update()
            except Exception as intern_e: zeige_fehler(intern_e)
 
        def bereinige_archiv():
            temp_dir, _, _, _ = get_rewe_paths()
            rewe_dir = os.path.dirname(temp_dir)
            if os.path.exists(rewe_dir):
                for ordner in os.listdir(rewe_dir):
                    ordner_pfad = os.path.join(rewe_dir, ordner)
                    if os.path.isdir(ordner_pfad) and ordner != "temp":
                        try:
                            ordner_datum = datetime.datetime.strptime(ordner, '%Y-%m-%d')
                            if (datetime.datetime.now() - ordner_datum).days > 7: shutil.rmtree(ordner_pfad)
                        except: pass
 
        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=25, weight="bold", color="white"))
            bereinige_archiv()
            temp_dir, _, _, display_pfad = get_rewe_paths()
            rewe_dir = os.path.dirname(temp_dir)
            
            def copy_path(e, p):
                page.set_clipboard(p)
                page.show_snack_bar(ft.SnackBar(content=ft.Text("Pfad kopiert! Jetzt in Dateien-App einfügen."), bgcolor="orange"))

            ansicht.controls.append(ft.Container(bgcolor="#222200", padding=10, border_radius=10, content=ft.Column([
                ft.Text("SO FINDEN SIE DIE DATEIEN:", color="orange", weight="bold"),
                ft.Text(f"1. Öffnen Sie die App 'Dateien' auf dem Handy.\n2. Suchen Sie nach diesem Pfad:", color="white", size=12),
                ft.Text(display_pfad, color="yellow", size=12, weight="bold"),
                sicherer_button("📋 Pfad kopieren", lambda e: copy_path(None, display_pfad), "orange", "black")
            ])))

            if os.path.exists(rewe_dir):
                for ordner in sorted([o for o in os.listdir(rewe_dir) if os.path.isdir(os.path.join(rewe_dir, o)) and o != "temp"], reverse=True):
                    ordner_pfad = os.path.join(rewe_dir, ordner)
                    p_list = [f for f in os.listdir(ordner_pfad) if f.endswith(".pdf")]
                    if p_list:
                        ansicht.controls.append(ft.Text(ordner, color="yellow", weight="bold", size=16))
                        for pdf in p_list:
                            def mail_senden(e, d=pdf):
                                subject = urllib.parse.quote(f"REWE Monitoring Bericht: {d}")
                                body = urllib.parse.quote("Bitte den Bericht im Anhang manuell anfügen.")
                                page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={subject}&body={body}")
                                
                            ansicht.controls.append(
                                ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                                    content=ft.Row([
                                        ft.Text(pdf, color="white", size=12, expand=True), 
                                        sicherer_button("📧 Mail versenden", mail_senden, "blue", "white")
                                    ])
                                )
                            )
                        ansicht.controls.append(ft.Divider(color="white24"))
            page.update()
            
        def zeige_postausgang():
            ansicht.controls.clear(); ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
            temp_dir, final_dir, heute_ordner, display_pfad = get_rewe_paths()
            
            def copy_path(e):
                page.set_clipboard(final_dir)
                page.show_snack_bar(ft.SnackBar(content=ft.Text("Pfad kopiert! Jetzt in Dateien-App einfügen."), bgcolor="blue"))

            ansicht.controls.append(ft.Container(bgcolor="#330000", padding=10, border_radius=10, content=ft.Column([
                ft.Text("DATEIEN VERSENDEN - ANLEITUNG:", color="red", weight="bold"),
                ft.Text("Da Android das direkte Öffnen blockiert, bitte so vorgehen:", color="white", size=12),
                ft.Text("1. Diesen Button drücken:", color="white", size=12),
                sicherer_button("📋 Pfad kopieren", copy_path, "blue", "white"),
                ft.Text("2. Handy-App 'Dateien' öffnen.\n3. Pfad oben in Suche einfügen.\n4. PDFs auswählen und per Mail senden.", color="white", size=12)
            ])))
            
            ansicht.controls.append(ft.Text(f"Aktueller Ordner:\n{display_pfad} / {heute_ordner}", color="yellow", size=12))
            
            p_list = [f for f in os.listdir(final_dir) if f.endswith(".pdf")] if os.path.exists(final_dir) else []
            if not p_list: ansicht.controls.append(ft.Text("Noch keine Berichte für heute erstellt.", color="grey", size=14))
            for pdf in p_list:
                def rm(e, d=pdf): os.remove(os.path.join(final_dir, d)); zeige_postausgang()
                ansicht.controls.append(
                    ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                        content=ft.Row([
                            ft.Text(pdf, color="white", size=10, expand=True),
                            sicherer_button("🗑️", rm, "red", "white")
                        ])
                    )
                )
            page.update()
 
        zeige_startbildschirm()
        
    except Exception as e: zeige_fehler(e)
        
if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")