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

    # --- DER GEHEIMTRICK ALS FUNKTION ---
    def system_teilen(dateiname):
        betreff = urllib.parse.quote(f"REWE Bericht: {dateiname}")
        # Ruft das Android-Teilen/Senden-Menü auf!
        page.launch_url(f"mailto:?subject={betreff}")

    # DER RICHTIGE BUTTON: Nutzt 'content' statt 'text', damit es NICHT abstürzt!
    def sicherer_button(t, on_click, bg="blue", expand=False, height=None, width=None):
        return ft.ElevatedButton(
            content=ft.Text(str(t), weight="bold", size=14), 
            on_click=on_click, 
            bgcolor=bg, 
            color="white", 
            expand=expand,
            height=height,
            width=width,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=5)
        )

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def nav_leiste():
            return ft.Row([
                sicherer_button("Touren", lambda e: zeige_dashboard(), "#004400", True, 50),
                sicherer_button("Senden", lambda e: zeige_postausgang(), "#004400", True, 50),
            ])

        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Container(height=10))
            maerkte = lade_maerkte()
            for i, m in enumerate(maerkte):
                txt = f"{m.get('marktnummer')} - {m.get('adresse')}"
                ansicht.controls.append(ft.Row([
                    sicherer_button(txt, lambda e, idx=i: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, print, idx), "#005500", True),
                    ft.IconButton("delete", icon_color="white", bgcolor="red", on_click=lambda e, idx=i: [maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()])
                ]))
            ansicht.controls.append(sicherer_button("Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, print, None), "red", width=200))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            heute = datetime.datetime.now().strftime('%Y-%m-%d')
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
                                    ft.IconButton("share", bgcolor="blue", icon_color="white", on_click=lambda e, fname=f: system_teilen(fname)),
                                    ft.IconButton("delete", bgcolor="red", icon_color="white", on_click=lambda e, p=os.path.join(pfad, f): [os.remove(p), zeige_postausgang()])
                                ])
                            ))
            if not gefunden:
                ansicht.controls.append(ft.Text("Keine Berichte gefunden."))
            page.update()

        # Startbildschirm
        v, z = lade_benutzer()
        v_in = ft.TextField(label="Vorname", value=v, width=300)
        z_in = ft.TextField(label="Nachname", value=z, width=300)
        ansicht.controls.extend([
            ft.Text("REWE MONITORING", size=25, weight="bold"),
            v_in, z_in,
            sicherer_button("START", lambda e: [speichere_benutzer(v_in.value, z_in.value), zeige_dashboard()], "red", width=250, height=60)
        ])
        page.update()

    except Exception as e:
        ansicht.controls.append(ft.Text(f"Fehler beim Laden: {e}", color="red"))
        page.update()

ft.app(target=main)