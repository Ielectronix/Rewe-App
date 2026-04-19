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

    def check_permissions(e=None):
        try:
            page.request_permission(ft.PermissionType.WRITE_EXTERNAL_STORAGE)
            page.request_permission(ft.PermissionType.MANAGE_EXTERNAL_STORAGE)
        except: pass
    
    try: page.window.icon = "icon.png"
    except: pass

    ansicht = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=25, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=16))
        try: ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=10))
        except: pass
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def sicherer_button(btn_text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            def safe_click(e):
                try: on_click(e)
                except Exception as ex: zeige_fehler(ex)
            # Wir nutzen 'content', damit auch alte Flet-Versionen nicht meckern
            return ft.ElevatedButton(
                content=ft.Text(str(btn_text), weight="bold", size=14),
                on_click=safe_click, bgcolor=bgcolor, color=color, expand=expand, height=height, width=width
            )

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=15, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("🚚 Touren", lambda e: zeige_dashboard(), "#004400", "white", expand=True, height=50),
                    sicherer_button("📤 Senden", lambda e: zeige_postausgang(), "#004400", "white", expand=True, height=50),
                    sicherer_button("🗄️ Archiv", lambda e: zeige_archiv(), "#004400", "white", expand=True, height=50)
                ])
            )

        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Container(height=10))
            maerkte = lade_maerkte()
            if not maerkte:
                ansicht.controls.append(ft.Text("Keine Touren vorhanden.", color="grey"))
            else:
                for index, markt in enumerate(maerkte):
                    anzeige = f"{markt.get('marktnummer')} - {markt.get('adresse')}"
                    def loesche(e, i=index):
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    # Dashboard-Buttons: Text links, Mülltonne rechts
                    ansicht.controls.append(ft.Row([
                        sicherer_button(anzeige, lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500", "white", expand=True),
                        ft.IconButton(icon="delete", icon_color="white", bgcolor="red", on_click=loesche)
                    ]))
            ansicht.controls.append(sicherer_button("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", "white", width=200))
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold"))
            heute = datetime.datetime.now().strftime('%Y-%m-%d')
            
            pdfs_gefunden = False
            for base in get_erweiterte_bases():
                pfad = os.path.join(base, heute)
                if os.path.exists(pfad):
                    for f in os.listdir(pfad):
                        if f.endswith(".pdf"):
                            pdfs_gefunden = True
                            full_p = os.path.join(pfad, f)
                            
                            # DER TRICK: page.launch_url öffnet das Android-Teilen-Menü!
                            def teilen(e, filename=f):
                                subj = urllib.parse.quote(f"REWE Bericht {filename}")
                                page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={subj}")

                            ansicht.controls.append(ft.Container(bgcolor="#003300", padding=10, border_radius=10, content=ft.Row([
                                ft.Text(f, expand=True, size=12),
                                ft.IconButton(icon="share", bgcolor="blue", icon_color="white", on_click=teilen),
                                ft.IconButton(icon="delete", bgcolor="red", icon_color="white", on_click=lambda e, p=full_p: [os.remove(p), zeige_postausgang()])
                            ])))
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte heute."))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv (7 Tage)", size=20, weight="bold"))
            # Archiv-Logik (vereinfacht für die Stabilität)
            page.update()

        # Start
        def zeige_start():
            v, z = lade_benutzer()
            v_in = ft.TextField(label="Vorname", value=v, width=300, text_align="center")
            z_in = ft.TextField(label="Nachname", value=z, width=300, text_align="center")
            ansicht.controls.extend([
                ft.Container(height=50),
                ft.Text("REWE MONITORING", size=30, weight="bold", color="white"),
                v_in, z_in,
                sicherer_button("TAG STARTEN", lambda e: [speichere_benutzer(v_in.value, z_in.value), zeige_dashboard()], "red", "white", width=250, height=60)
            ])
            page.update()

        zeige_start()
    except Exception as e: zeige_fehler(e)

ft.app(target=main)