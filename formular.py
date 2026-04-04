import flet as ft
import datetime
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_vorlagen, speichere_vorlagen
from pdf_generator import erstelle_bericht

def zeige_maske_ui(page, ansicht, zeige_dashboard, markt_index):
    maerkte = lade_maerkte()
    d = maerkte[markt_index] if markt_index is not None else {"datum": datetime.datetime.now().strftime('%d.%m.%Y')}

    def erstelle_combo(label, wert, optionen):
        c = ft.TextField(label=label, value=wert, color="yellow", border_color="white", expand=True, text_size=12)
        c.suffix = ft.PopupMenuButton(items=[ft.PopupMenuItem(content=ft.Text(o), on_click=lambda e, opt=o: (setattr(c, 'value', opt), c.update())) for o in optionen])
        return c

    # Felder
    tag_in = ft.TextField(label="Tag", value=d.get("datum", "").split(".")[0] if "." in d.get("datum", "") else "", width=60)
    mon_in = ft.TextField(label="Mon", value=d.get("datum", "").split(".")[1] if "." in d.get("datum", "") else "", width=60)
    jahr_in = ft.TextField(label="Jahr", value=d.get("datum", "").split(".")[2] if "." in d.get("datum", "") else "2026", width=80)
    nr_in = ft.TextField(label="Marktnummer", value=d.get("marktnummer", ""), expand=True)
    adr_in = ft.TextField(label="Adresse", value=d.get("adresse", ""), expand=True)
    
    hfm_okz_cb = ft.Checkbox(label="HFM OKZ aktivieren", value=d.get("hfm_okz_cb", False))
    okz_ctrls = {}
    okz_ui = []
    for i in range(1, 11):
        idx = f"{i:02d}"
        abk = ft.Checkbox(label="A", value=d.get(f"okz_abklatsch_{idx}", True))
        tup = ft.Checkbox(label="T", value=d.get(f"okz_tupfer_{idx}", False))
        okz_ctrls[idx] = {"abklatsch": abk, "tupfer": tup}
        okz_ui.append(ft.Row([ft.Text(f"P{i}"), abk, tup]))

    status_text = ft.Text("", color="yellow")

    def speichern(e):
        daten = {"datum": f"{tag_in.value}.{mon_in.value}.{jahr_in.value}", "adresse": adr_in.value, 
                 "marktnummer": nr_in.value, "hfm_okz_cb": hfm_okz_cb.value}
        for k, v in okz_ctrls.items():
            daten[f"okz_abklatsch_{k}"] = v["abklatsch"].value
            daten[f"okz_tupfer_{k}"] = v["tupfer"].value
        
        if markt_index is None: maerkte.append(daten)
        else: maerkte[markt_index] = daten
        speichere_maerkte(maerkte)
        
        try:
            path = erstelle_bericht(daten)
            status_text.value = f"✅ Gespeichert: {os.path.basename(path)}"; status_text.color = "green"
        except Exception as ex:
            status_text.value = f"❌ Fehler: {str(ex)}"; status_text.color = "red"
        page.update()

    ansicht.controls.clear()
    ansicht.controls.extend([
        ft.Row([tag_in, mon_in, jahr_in]), nr_in, adr_in, ft.Divider(),
        hfm_okz_cb, ft.Column(okz_ui, scroll=ft.ScrollMode.AUTO, height=300),
        ft.Divider(), status_text,
        ft.Row([ft.ElevatedButton("Speichern", on_click=speichern), ft.ElevatedButton("Zurück", on_click=lambda _: zeige_dashboard())])
    ])
    page.update()