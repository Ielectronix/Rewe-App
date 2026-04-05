import flet as ft
import traceback
import os
import datetime
import shutil
import urllib.parse
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
from pdf_generator import get_all_rewe_bases
from formular import zeige_maske_ui

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO

    def check_permissions(e=None):
        page.request_permission(ft.PermissionType.WRITE_EXTERNAL_STORAGE)
        page.request_permission(ft.PermissionType.MANAGE_EXTERNAL_STORAGE)
    
    try: page.window.icon = "icon.png"
    except: pass

    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    page.add(ansicht)

    def zeige_fehler(e):
        ansicht.controls.clear()
        page.bgcolor = "black"
        ansicht.controls.append(ft.Text("SYSTEM-FEHLER:", color="red", size=30, weight="bold"))
        ansicht.controls.append(ft.Text(str(e), color="yellow", size=20))
        try: ansicht.controls.append(ft.Text(traceback.format_exc(), color="white", size=12))
        except: pass
        page.update()

    try:
        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None, bild_name=None, ft_icon_name=None):
            inhalt = []
            
            # 1. Handle Bild-Icons
            if bild_name:
                icon_groesse = 30
                inhalt.append(ft.Image(src=bild_name, width=icon_groesse, height=icon_groesse, fit="contain"))
            # 2. Handle Flet-interne Icons (Diskette, Mülleimer)
            elif ft_icon_name:
                icon_groesse = 30
                inhalt.append(ft.Icon(name=ft_icon_name, color=color, size=icon_groesse))
                
            if text:
                # Text wird zentriert!
                txt_obj = ft.Text(text, weight="bold", size=12, text_align=ft.TextAlign.CENTER)
                
                # Wir packen den Text in einen Container, damit er bei Bedarf umbrechen darf
                # aber der Text selbst ist im Container zentriert.
                inhalt.append(ft.Container(content=txt_obj, expand=True))
                    
            return ft.ElevatedButton(
                # Der komplette Inhalt der Row wird zentriert!
                content=ft.Row(inhalt, alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                on_click=on_click, bgcolor=bgcolor, color=color, expand=expand, height=height, width=width,
                # Padding auf 2 reduziert, damit das Bild richtig groß werden kann!
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=2)
            )

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=10, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("Touren", lambda e: zeige_dashboard(), "#004400", "white", bild_name="touren.png"),
                    sicherer_button("Senden", lambda e: zeige_postausgang(), "#004400", "white"),
                    sicherer_button("Archiv", lambda e: zeige_archiv(), "#004400", "white")
                ])
            )

        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            stil_label_weiss = ft.TextStyle(color="white")
            stil_hint_weiss = ft.TextStyle(color="white54", size=12)
            v_in = ft.TextField(label="Vorname", hint_text="Dein Vorname", hint_style=stil_hint_weiss, value=v, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            z_in = ft.TextField(label="Nachname", hint_text="Dein Nachname", hint_style=stil_hint_weiss, value=z, color="yellow", border_color="white", text_align=ft.TextAlign.CENTER, label_style=stil_label_weiss, width=300)
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()
            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            header = ft.Text(spans=[ft.TextSpan("REWE ", ft.TextStyle(color="red", weight="bold", size=32)), ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=32))], text_align=ft.TextAlign.CENTER)
            ansicht.controls.extend([ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(height=40), ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Divider(color="transparent"))
            ansicht.controls.append(ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white"))
            
            if not maerkte:
                ansicht.controls.append(ft.Row([ft.Text("Noch keine Touren angelegt.", color="grey", size=16)], alignment=ft.MainAxisAlignment.CENTER))
            else:
                for index, markt in enumerate(maerkte):
                    adr = (markt.get("adresse") or "").strip()
                    mnr = (markt.get("marktnummer") or "").strip()
                    anzeige_text = f"{mnr} - {adr}" if mnr and adr else (mnr or adr or "Unbenannte Tour")
                    buchstabe = chr(65 + index) if index < 26 else str(index)
                    def loesche_t(e, i=index): 
                        maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    # WICHTIG: height=None erlaubt dem Button nach unten zu wachsen (Wrap)
                    btn_tour = sicherer_button(f"Tour {buchstabe}: {anzeige_text}", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500", "white", expand=True, height=None)
                    btn_del = sicherer_button("", loesche_t, "red", "white", height=50, width=60, bild_name="löschen.png")
                    ansicht.controls.append(ft.Row([btn_tour, btn_del], vertical_alignment=ft.CrossAxisAlignment.CENTER))
                    
            ansicht.controls.append(ft.Divider(color="white"))
            btn_neu = sicherer_button("Neue Tour", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", "white", height=50, width=200)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=25, weight="bold", color="white"))
            email_feld = ft.TextField(value="registration-mibi.ber@tentamus.com", read_only=True, color="white", selection_color="yellow", border=ft.InputBorder.NONE, content_padding=0, text_style=ft.TextStyle(size=14, weight="bold"))
            ansicht.controls.append(ft.Container(bgcolor="#330000", padding=10, border_radius=10, content=ft.Column([ft.Text("MANUELLER E-MAIL VERSAND:", color="orange", weight="bold"), ft.Text("Empfänger:", color="orange", size=14, weight="bold"), email_feld, ft.Text("Betreff: REWE + Marktnummer", color="yellow", size=14, weight="bold", selectable=True)])))
            # Archiv-Loop folgt hier... (gekürzt für Übersicht)
            page.update()

        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
            # Postausgang-Logik folgt hier... (gekürzt)
            page.update()

        page.on_connect = check_permissions
        zeige_startbildschirm()
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")
