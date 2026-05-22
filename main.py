import flet as ft
import os
import datetime
import shutil
import json 
import asyncio

LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")
START_LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent1.png")

def main(page: ft.Page):
    page.title = "Rewe Monitoring"
    page.bgcolor = "#001a00"
    page.scroll = "auto"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER 

    share_obj = ft.Share() if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS] else None

    try:
        from datenverwaltung import (lade_maerkte, speichere_maerkte, lade_benutzer, 
                                     speichere_benutzer, hole_alle_benutzer, 
                                     registriere_neuen_benutzer, authentifiziere_benutzer)
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        def lade_gesendet():
            try:
                if page.client_storage.contains_key("gesendet_pdfs"):
                    daten = page.client_storage.get("gesendet_pdfs")
                    if daten: return set(daten)
            except: pass
            return set()

        def markiere_als_gesendet(pfad):
            gesendet = lade_gesendet()
            gesendet.add(pfad)
            try:
                page.client_storage.set("gesendet_pdfs", list(gesendet))
            except: pass

        def get_erweiterte_bases():
            try: return get_all_rewe_bases() + ["/storage/emulated/0/Download/Rewe_Monitoring"]
            except: return []

        def bereinige_archiv():
            heute = datetime.datetime.now()
            for base in get_erweiterte_bases():
                if not os.path.exists(base): continue
                try:
                    for ordner in os.listdir(base):
                        ordner_pfad = os.path.join(base, ordner)
                        if os.path.isdir(ordner_pfad) and ordner != "temp":
                            try:
                                ordner_datum = datetime.datetime.strptime(ordner, '%Y-%m-%d')
                                if (heute - ordner_datum).days > 14: shutil.rmtree(ordner_pfad)
                            except: pass
                except PermissionError: pass

        def get_start_logo_bild():
            if os.path.exists(START_LOGO_PFAD):
                return ft.Image(src=START_LOGO_PFAD, height=80, fit="contain")
            return ft.Text("REWE Monitoring", color="white", weight="bold", size=28)

        def nav_leiste(active_tab="touren"):
            def make_btn(text, tab_id, on_click):
                is_active = (active_tab == tab_id)
                return ft.ElevatedButton(
                    content=ft.Text(text, size=13, weight="bold"),
                    on_click=on_click,
                    bgcolor="#004400" if is_active else "#1a1a1a",
                    color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10, side=ft.BorderSide(width=1.5, color="#4CAF50"))
                )
            return ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5, wrap=True, controls=[
                make_btn("🚚 Touren", "touren", lambda e: zeige_dashboard()),
                make_btn("📤 Senden", "senden", lambda e: zeige_postausgang()),
                make_btn("🗄️ Archiv", "archiv", lambda e: zeige_archiv())
            ])

        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(text, size=14, weight="bold"), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25), padding=15, side=ft.BorderSide(width=2, color=farbe)))

        def small_btn(emoji, on_click, farbe):
            return ft.ElevatedButton(content=ft.Text(emoji, size=16), on_click=on_click, bgcolor="#0b1a0b", color=farbe, style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0, side=ft.BorderSide(width=2, color=farbe)), width=45, height=45)

        def zeige_registrierung():
            page.clean() 
            name_in = ft.TextField(label="Vorname Nachname", color="yellow", label_style=ft.TextStyle(color="white"), border_color="white", width=400, text_align="center")
            pin_in = ft.TextField(label="Wunsch-PIN (4 Zahlen)", password=True, keyboard_type="number", color="yellow", label_style=ft.TextStyle(color="white"), border_color="white", width=400, text_align="center", max_length=4)
            fehler = ft.Text("", color="red", weight="bold")
            def do_reg(e):
                if not name_in.value or not pin_in.value: fehler.value = "⚠️ Bitte alles ausfüllen!"; page.update(); return
                success, msg = registriere_neuen_benutzer(name_in.value, pin_in.value)
                if success: zeige_login()
                else: fehler.value = msg; page.update()
            page.add(ft.SafeArea(ft.Column([ft.Container(height=30), get_start_logo_bild(), ft.Text("Profil einrichten", color="#4CAF50", size=18), name_in, pin_in, fehler, action_btn("💾 PROFIL ERSTELLEN", do_reg, "#4CAF50")], horizontal_alignment="center")))

        def zeige_login():
            page.clean() 
            bereinige_archiv
