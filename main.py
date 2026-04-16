import flet as ft
import traceback
import os
import datetime
import shutil
import urllib.parse

def main(page: ft.Page):
    # --- MODULE VORBEREITEN (Keine Abfrage beim Start!) ---
    ph = ft.PermissionHandler()
    share = ft.Share()
    page.overlay.extend([ph, share])
    
    # Grund-Einstellungen
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300"
    page.padding = ft.padding.only(left=10, top=55, right=10, bottom=10)
    page.scroll = ft.ScrollMode.AUTO

    # Icon-Versuch (Optional)
    try: 
        page.window.icon = "icon.png"
    except: 
        pass

    # Haupt-Container für den Inhalt
    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    page.add(ansicht)

    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=20))
        try: 
            ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=12))
        except: 
            pass
        page.update()

    try:
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            text_size = 18 if text in ["🗑️", "📤"] else 12 
            txt_obj = ft.Text(text, weight="bold", size=text_size, text_align=ft.TextAlign.CENTER)
            
            return ft.ElevatedButton(
                content=txt_obj,
                on_click=on_click, bgcolor=bgcolor, color=color, expand=expand, height=height, width=width,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=10, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("🚚 Touren", lambda e: zeige_dashboard(), "#004400", "white", expand=True, height=50),
                    sicherer_button("📤 Senden", lambda e: zeige_postausgang(), "#004400", "white", expand=True, height=50),
                    sicherer_button("🗄️ Archiv", lambda e: zeige_archiv(), "#004400", "white", expand=True, height=50)
                ])
            )

        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            
            v_in = ft.TextField(label="Vorname", value=v, color="yellow", border_color="white", width=300)
            z_in = ft.TextField(label="Nachname", value=z, color="yellow", border_color="white", width=300)
            
            def start_klick(e):
                # JETZT fragen wir nach den Rechten!
                try:
                    ph.request_permission(ft.PermissionType.STORAGE)
                except:
                    pass
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()

            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            header = ft.Text(spans=[ft.TextSpan("REWE ", ft.TextStyle(color="red", weight="bold", size=32)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=32))])
            
            ansicht.controls.extend([
                ft.Container(height=50), 
                ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), 
                ft.Container(height=40), 
                ft.Row([ft.Column([v_in, z_in])], alignment=ft.MainAxisAlignment.CENTER), 
                ft.Container(height=40), 
                ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Row([ft.Text("Meine Touren", size=25, weight="bold", color="white")]))
            
            if not maerkte:
                ansicht.controls.append(ft.Text("Noch keine Touren.", color="grey"))
            else:
                for index, markt in enumerate(maerkte):
                    mnr = markt.get("marktnummer", "Unbekannt")
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    btn_tour = sicherer_button(f"🚚 Tour: {mnr}", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500", "white", expand=True)
                    btn_del = sicherer_button("🗑️", loesche_t, "red", "white", width=50)
                    ansicht.controls.append(ft.Row([btn_tour, btn_del]))
                    
            btn_neu = sicherer_button("➕ Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", "white", height=50, width=200)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        # ... (Restliche Funktionen wie Archiv/Postausgang bleiben gleich) ...
        # (Ich kürze hier ab, damit der Code nicht zu lang wird, die Logik ist dieselbe)

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            # Deine Postausgangs-Logik hier... (wie gehabt)
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            # Deine Archiv-Logik hier... (wie gehabt)
            page.update()

        # Startbildschirm laden
        zeige_startbildschirm()
        
    except Exception as e: 
        zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")