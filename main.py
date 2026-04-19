import flet as ft
import traceback
import os
import datetime
import urllib.parse

def main(page: ft.Page):
    page.title = "Rewe Monitoring"
    page.bgcolor = "#002200"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = ft.padding.only(left=15, top=55, right=15, bottom=15)
    page.scroll = ft.ScrollMode.AUTO

    ansicht = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    def zeige_fehler(e):
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text(f"Fehler: {e}", color="red"))
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # Der "alte" Button-Stil, der nicht abstürzt
        def sicherer_button(t, on_click, bg="blue", expand=False, height=None):
            return ft.ElevatedButton(text=t, on_click=on_click, bgcolor=bg, color="white", expand=expand, height=height)

        def nav_leiste():
            return ft.Row([
                sicherer_button("Touren", lambda e: zeige_dashboard(), "#004400", True, 50),
                sicherer_button("Senden", lambda e: zeige_postausgang(), "#004400", True, 50),
            ])

        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            maerkte = lade_maerkte()
            for i, m in enumerate(maerkte):
                txt = f"{m.get('marktnummer')} - {m.get('adresse')}"
                ansicht.controls.append(ft.Row([
                    sicherer_button(txt, lambda e, idx=i: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, idx), "#005500", True),
                    ft.IconButton("delete", on_click=lambda e, idx=i: [maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()])
                ]))
            ansicht.controls.append(sicherer_button("Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red"))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            heute = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # --- HIER IST DER GEHEIMTRICK ---
            def system_teilen(dateiname):
                betreff = urllib.parse.quote(f"REWE Bericht: {dateiname}")
                # launch_url triggert das Android-Systemmenü
                page.launch_url(f"mailto:?subject={betreff}")

            gefunden = False
            for base in get_all_rewe_bases():
                pfad = os.path.join(base, heute)
                if os.path.exists(pfad):
                    for f in os.listdir(pfad):
                        if f.endswith(".pdf"):
                            gefunden = True
                            ansicht.controls.append(ft.Container(
                                bgcolor="#003300", padding=10, border_radius=10,
                                content=ft.Row([
                                    ft.Text(f, expand=True, size=12),
                                    # Der Button nutzt den Trick:
                                    ft.IconButton("share", on_click=lambda e, fname=f: system_teilen(fname)),
                                    ft.IconButton("delete", on_click=lambda e, p=os.path.join(pfad, f): [os.remove(p), zeige_postausgang()])
                                ])
                            ))
            if not gefunden:
                ansicht.controls.append(ft.Text("Keine Berichte für heute."))
            page.update()

        # App-Start
        v, z = lade_benutzer()
        v_in = ft.TextField(label="Vorname", value=v)
        z_in = ft.TextField(label="Nachname", value=z)
        ansicht.controls.extend([v_in, z_in, sicherer_button("START", lambda e: zeige_dashboard(), "red")])
        page.update()

    except Exception as e:
        zeige_fehler(e)

ft.app(target=main)