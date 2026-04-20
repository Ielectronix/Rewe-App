import flet as ft
import traceback
import os
import datetime
import shutil
import urllib.parse

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#002200" 
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = ft.padding.only(left=15, top=55, right=15, bottom=15)
    page.scroll = ft.ScrollMode.AUTO

    # Die Struktur bleibt genau wie sie war
    ansicht = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    # --- DER GEHEIMTRICK ---
    def system_teilen(e, dateiname):
        # Wir erzeugen einen speziellen Link. 
        # Da wir keinen Empfänger angeben, fragt Android: "Mit welcher App senden?"
        betreff = urllib.parse.quote(f"REWE Bericht: {dateiname}")
        page.launch_url(f"mailto:?subject={betreff}")

    def zeige_fehler(e):
        ansicht.controls.clear()
        ansicht.controls.append(ft.Text(f"System-Fehler: {e}", color="red"))
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # Deine gewohnte Button-Funktion
        def sicherer_button(t, on_click, bg="blue", expand=False, height=None, width=None):
            return ft.ElevatedButton(
                str(t), 
                on_click=on_click, 
                bgcolor=bg, 
                color="white", 
                expand=expand, 
                height=height, 
                width=width
            )

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=15, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("🚚 Touren", lambda e: zeige_dashboard(), "#004400", True, 50),
                    sicherer_button("📤 Senden", lambda e: zeige_postausgang(), "#004400", True, 50),
                    sicherer_button("🗄️ Archiv", lambda e: zeige_archiv(), "#004400", True, 50)
                ])
            )

        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            maerkte = lade_maerkte()
            for i, markt in enumerate(maerkte):
                mnr = markt.get("marktnummer", "")
                adr = markt.get("adresse", "")
                # Wir bauen die Zeile genau so wie früher
                ansicht.controls.append(ft.Row([
                    sicherer_button(f"{mnr} - {adr}", lambda e, idx=i: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, idx), "#005500", True),
                    ft.IconButton(icon="delete", icon_color="white", bgcolor="red", on_click=lambda e, idx=i: [maerkte.pop(idx), speichere_maerkte(maerkte), zeige_dashboard()])
                ]))
            ansicht.controls.append(sicherer_button("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", width=200))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="white"))
            heute = datetime.datetime.now().strftime('%Y-%m-%d')
            
            for base in get_all_rewe_bases():
                pfad = os.path.join(base, heute)
                if os.path.exists(pfad):
                    for f in os.listdir(pfad):
                        if f.endswith(".pdf"):
                            full_path = os.path.join(pfad, f)
                            ansicht.controls.append(ft.Container(
                                bgcolor="#003300", padding=10, border_radius=10, 
                                content=ft.Row([
                                    ft.Text(f, expand=True, size=12),
                                    # HIER WIRD DER TRICK GEZÜNDET
                                    ft.IconButton(icon="share", bgcolor="blue", icon_color="white", on_click=lambda e, fname=f: system_teilen(e, fname)),
                                    ft.IconButton(icon="delete", bgcolor="red", icon_color="white", on_click=lambda e, p=full_path: [os.remove(p), zeige_postausgang()])
                                ])
                            ))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv", size=20, color="white"))
            page.update()

        # Startbildschirm (unveränderte Grundstruktur)
        v, z = lade_benutzer()
        v_in = ft.TextField(label="Vorname", value=v, width=300)
        z_in = ft.TextField(label="Nachname", value=z, width=300)
        ansicht.controls.extend([
            ft.Text("REWE MONITORING", size=25, weight="bold", color="white"),
            v_in, z_in,
            sicherer_button("TAG STARTEN", lambda e: [speichere_benutzer(v_in.value, z_in.value), zeige_dashboard()], "red", width=250, height=60)
        ])
        page.update()

    except Exception as e:
        zeige_fehler(e)

if __name__ == "__main__":
    ft.app(target=main)