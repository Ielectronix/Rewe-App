import flet as ft
import traceback
import os
import datetime
import shutil
import urllib.parse

# Importiere unsere ausgelagerten Module
from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
from pdf_generator import get_all_rewe_bases
from formular import zeige_maske_ui  # Das ist die neue UI-Datei!

def main(page: ft.Page):
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#003300" 
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO
    
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
        def sicherer_button(text, on_click, bgcolor="blue", color="white", expand=False, height=None, width=None):
            return ft.ElevatedButton(
                content=ft.Text(text, weight="bold", size=12),
                on_click=on_click, bgcolor=bgcolor, color=color,
                expand=expand, height=height, width=width,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=5)
            )

        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", padding=10, border_radius=10, 
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                    sicherer_button("Touren", lambda e: zeige_dashboard(), "#004400", "white"),
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
                speichere_benutzer(v_in.value, z_in.value); zeige_dashboard()
                
            btn_start = sicherer_button("Neuen Tag starten", start_klick, "red", "white", height=60, width=250)
            
            header = ft.Text(spans=[
                ft.TextSpan("REWE ", ft.TextStyle(color="red", weight="bold", size=32)),
                ft.TextSpan("Monitoring", ft.TextStyle(color="white", weight="bold", size=32))
            ], text_align=ft.TextAlign.CENTER)

            ansicht.controls.extend([
                ft.Container(height=50), ft.Row([header], alignment=ft.MainAxisAlignment.CENTER), 
                ft.Container(height=40), ft.Column([v_in, z_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=40), ft.Row([btn_start], alignment=ft.MainAxisAlignment.CENTER)
            ])
            page.update()

        def zeige_dashboard():
            ansicht.controls.clear()
            maerkte = lade_maerkte()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Divider(color="transparent"))
            ansicht.controls.append(ft.Row([ft.Text("Meine heutigen Touren", size=25, weight="bold", color="white")], alignment=ft.MainAxisAlignment.CENTER))
            if not maerkte:
                ansicht.controls.append(ft.Row([ft.Text("Noch keine Touren angelegt.", color="grey", size=16)], alignment=ft.MainAxisAlignment.CENTER))
            else:
                for index, markt in enumerate(maerkte):
                    adr = (markt.get("adresse") or "").strip() or "Unbenannter Markt"
                    buchstabe = chr(65 + index) if index < 26 else str(index)
                    def loesche_t(e, i=index): maerkte.pop(i); speichere_maerkte(maerkte); zeige_dashboard()
                    
                    # Hier rufen wir das neue Modul formular.py auf!
                    btn_tour = sicherer_button(f"Tour {buchstabe}: {adr}", lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), "#005500", "white", expand=True, height=50)
                    btn_del = sicherer_button("🗑️", loesche_t, "red", "white", height=50, width=65)
                    ansicht.controls.append(ft.Row([btn_tour, btn_del]))
                    
            ansicht.controls.append(ft.Divider(color="white"))
            btn_neu = sicherer_button("Tour voranlegen", lambda e: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), "red", "white", height=50)
            ansicht.controls.append(ft.Row([btn_neu], alignment=ft.MainAxisAlignment.CENTER))
            page.update()

        def bereinige_archiv():
            heute = datetime.datetime.now()
            for base in get_all_rewe_bases():
                if not os.path.exists(base): continue
                try:
                    for ordner in os.listdir(base):
                        ordner_pfad = os.path.join(base, ordner)
                        if os.path.isdir(ordner_pfad) and ordner != "temp":
                            try:
                                ordner_datum = datetime.datetime.strptime(ordner, '%Y-%m-%d')
                                if (heute - ordner_datum).days > 7:
                                    shutil.rmtree(ordner_pfad)
                            except: pass
                except PermissionError: pass

        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Archiv (Letzte 7 Tage)", size=25, weight="bold", color="white"))
            
            bereinige_archiv()
            
            ansicht.controls.append(ft.Container(
                bgcolor="#330000", padding=10, border_radius=10,
                content=ft.Column([
                    ft.Text("📧 MANUELLER E-MAIL VERSAND:", color="orange", weight="bold"),
                    ft.Text("Empfänger: registration-mibi.ber@tentamus.com", color="yellow", size=14, weight="bold", selectable=True),
                    ft.Text("Betreff: REWE + Marktnummer (z.B. REWE 1234)", color="yellow", size=14, weight="bold", selectable=True),
                    ft.Text("Da Android das automatische Anhängen blockiert, versende den Bericht bitte so:", color="white54", size=11, italic=True),
                    ft.Text("1. Halte die gelbe E-Mail-Adresse gedrückt, um sie zu kopieren.", color="white", size=12),
                    ft.Text("2. Öffne deine E-Mail-App und füge die Adresse und den Betreff ein.", color="white", size=12),
                    ft.Text("3. Drücke auf die Büroklammer und hänge die PDF-Datei an.", color="white", size=12),
                ])
            ))
            
            pdfs_gefunden = False
            for base in get_all_rewe_bases():
                if not os.path.exists(base): continue
                try:
                    ordner_liste = sorted([o for o in os.listdir(base) if os.path.isdir(os.path.join(base, o)) and o != "temp"], reverse=True)
                    for ordner in ordner_liste:
                        ordner_pfad = os.path.join(base, ordner)
                        p_list = [f for f in os.listdir(ordner_pfad) if f.endswith(".pdf")]
                        
                        if p_list:
                            parent_folder = os.path.basename(os.path.dirname(base))
                            ansicht.controls.append(ft.Text(f"{ordner} (in {parent_folder})", color="yellow", weight="bold", size=16))
                            for pdf in p_list:
                                pdfs_gefunden = True
                                def mail_senden(e, d=pdf):
                                    betreff = urllib.parse.quote(f"REWE Monitoring Bericht: {d}")
                                    body = urllib.parse.quote("Hallo,\n\nbitte den Bericht im Anhang finden. (WICHTIG: Die PDF-Datei muss noch manuell angehängt werden!)\n\nViele Grüße")
                                    page.launch_url(f"mailto:registration-mibi.ber@tentamus.com?subject={betreff}&body={body}")
                                    
                                ansicht.controls.append(
                                    ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                                        content=ft.Row([
                                            ft.Text(pdf, color="white", size=12, expand=True, selectable=True), 
                                            sicherer_button("📧 Mail", mail_senden, "blue", "white")
                                        ])
                                    )
                                )
                            ansicht.controls.append(ft.Divider(color="white24"))
                except PermissionError: pass
                        
            if not pdfs_gefunden:
                ansicht.controls.append(ft.Text("Keine Berichte im Archiv.", color="grey", size=14))
                
            page.update()
            
        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Text("Postausgang", size=25, weight="bold", color="white"))
            
            heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
            pdfs_gefunden = False
            
            for base in get_all_rewe_bases():
                final_dir = os.path.join(base, heute_ordner)
                if not os.path.exists(final_dir): continue
                
                try:
                    p_list = [f for f in os.listdir(final_dir) if f.endswith(".pdf")]
                    if p_list:
                        pdfs_gefunden = True
                        
                        def oeffne_ordner(e, path=final_dir):
                            try: page.launch_url(f"file://{path}")
                            except: pass
                            
                        ansicht.controls.append(
                            ft.Container(
                                bgcolor="#330000", padding=10, border_radius=10,
                                content=ft.Column([
                                    ft.Text("Berichte für heute liegen in:", color="red", size=12),
                                    ft.Text(f"{final_dir}", color="red", size=12, weight="bold", selectable=True),
                                    sicherer_button("📂 Ordner öffnen", oeffne_ordner, "blue", "white"),
                                    ft.Text("Info: Falls sich die Datei/Ordner nicht öffnen lässt, blockiert dein Handy den Direktzugriff. Öffne dann manuell deine 'Eigene Dateien'-App und navigiere zu dem Ordner, der oben in fett steht!", color="orange", size=11, italic=True)
                                ])
                            )
                        )
                        
                        for pdf in p_list:
                            def rm(e, d=pdf, p=final_dir): os.remove(os.path.join(p, d)); zeige_postausgang()
                            def oeffne(e, d=pdf, p=final_dir): 
                                try: page.launch_url(f"file://{os.path.join(p, d)}")
                                except: pass
                                
                            ansicht.controls.append(
                                ft.Container(bgcolor="#002200", padding=10, border_radius=10, 
                                    content=ft.Row([
                                        ft.Text(pdf, color="white", size=10, expand=True),
                                        sicherer_button("📄", oeffne, "blue", "white"),
                                        sicherer_button("🗑️", rm, "red", "white")
                                    ])
                                )
                            )
                except PermissionError: pass
                
            if not pdfs_gefunden:
                ansicht.controls.append(ft.Text("Noch keine Berichte für heute erstellt.", color="grey", size=14))
                
            page.update()

        zeige_startbildschirm()
        
    except Exception as e: zeige_fehler(e)

if __name__ == "__main__": 
    ft.app(target=main, assets_dir="assets")
