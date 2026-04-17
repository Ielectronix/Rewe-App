import flet as ft
import os
import glob
import traceback

def main(page: ft.Page):
    # --- 1. GRUND-DESIGN (Exakt nach deinen Screenshots) ---
    page.title = "Rewe Monitoring System"
    page.bgcolor = "#002200" # Ein tiefes, dunkles REWE-Grün
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = ft.padding.only(left=15, top=50, right=15, bottom=15)
    page.scroll = ft.ScrollMode.AUTO

    # Das Teilen-Modul (unsichtbar im Hintergrund)
    share = ft.Share()
    page.overlay.append(share)

    # Haupt-Container (Zentriert die Elemente)
    ansicht = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    page.add(ansicht)

    def zeige_fehler(e):
        page.snack_bar = ft.SnackBar(ft.Text(f"Fehler: {e}", color="white"), bgcolor="red")
        page.snack_bar.open = True
        page.update()

    try:
        # Import deiner Logik-Dateien
        from datenverwaltung import lade_maerkte, speichere_maerkte, lade_benutzer, speichere_benutzer
        from formular import zeige_maske_ui

        # --- NAVIGATION (Die schicke Leiste oben) ---
        def nav_leiste():
            return ft.Container(
                bgcolor="#001100", 
                padding=10, 
                border_radius=20, 
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY, 
                    controls=[
                        ft.ElevatedButton("🚚\nTouren", on_click=lambda _: zeige_dashboard(), bgcolor="#003300", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                        ft.ElevatedButton("📤\nSenden", on_click=lambda _: zeige_postausgang(), bgcolor="#003300", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                        ft.ElevatedButton("🗄️\nArchiv", on_click=lambda _: zeige_archiv(), bgcolor="#003300", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                    ]
                )
            )

        # --- STARTBILDSCHIRM ---
        def zeige_startbildschirm():
            ansicht.controls.clear()
            v, z = lade_benutzer()
            
            v_in = ft.TextField(label="Vorname", value=v, width=300, border_color="#005500", bgcolor="#001100")
            z_in = ft.TextField(label="Nachname", value=z, width=300, border_color="#005500", bgcolor="#001100")
            
            def start_klick(e):
                speichere_benutzer(v_in.value, z_in.value)
                zeige_dashboard()

            ansicht.controls.extend([
                ft.Container(height=40),
                # REWE Rot, MONITORING Weiß (Zentriert)
                ft.Row([
                    ft.Text("REWE", size=32, weight="bold", color="#ff4444"),
                    ft.Text("MONITORING", size=32, weight="bold", color="white")
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=40),
                v_in, 
                z_in,
                ft.Container(height=40),
                # Großer roter Button
                ft.ElevatedButton(
                    "TAG STARTEN", 
                    on_click=start_klick, 
                    bgcolor="#ff4444", 
                    color="white", 
                    height=60, 
                    width=250,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30))
                )
            ])
            page.update()

        # --- DASHBOARD (MEINE TOUREN) ---
        def zeige_dashboard():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Container(height=10))
            
            # Überschrift linksbündig (wie auf deinem Bild)
            ansicht.controls.append(
                ft.Row([ft.Text("Meine Touren", size=24, weight="bold", color="white")], alignment=ft.MainAxisAlignment.START)
            )
            
            maerkte = lade_maerkte()
            for index, markt in enumerate(maerkte):
                # Hier wird jetzt Nummer UND Adresse angezeigt!
                markt_nr = markt.get('marktnummer', 'Unbekannt')
                adresse = markt.get('adresse', '')
                anzeige_text = f"Tour: {markt_nr} - {adresse}" if adresse else f"Tour: {markt_nr}"

                btn = ft.ElevatedButton(
                    text=anzeige_text, 
                    on_click=lambda e, i=index: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, i), 
                    bgcolor="#004400", 
                    color="white",
                    height=50,
                    width=350,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
                )
                ansicht.controls.append(btn)
            
            ansicht.controls.append(ft.Container(height=10))
            btn_neu = ft.ElevatedButton(
                "➕ Neue Tour", 
                on_click=lambda _: zeige_maske_ui(page, ansicht, nav_leiste, zeige_dashboard, zeige_fehler, None), 
                bgcolor="#ff4444", 
                color="white",
                height=40,
                width=200,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20))
            )
            ansicht.controls.append(btn_neu)
            page.update()

        # --- SENDEN (POSTAUSGANG) ---
        def zeige_postausgang():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Container(height=10))
            
            ansicht.controls.append(
                ft.Row([ft.Text("Senden", size=24, weight="bold", color="white")], alignment=ft.MainAxisAlignment.START)
            )
            
            # --- PDF SUCH-LOGIK ---
            # Sucht im Standard-Download-Ordner von Android nach PDFs
            download_ordner = "/storage/emulated/0/Download"
            gefundene_pdfs = []
            
            if os.path.exists(download_ordner):
                # Sucht nach allen PDFs, die mit "REWE" anfangen (passe das ggf. an deinen Dateinamen an)
                gefundene_pdfs = glob.glob(os.path.join(download_ordner, "*.pdf"))

            if not gefundene_pdfs:
                ansicht.controls.append(ft.Container(height=30))
                ansicht.controls.append(ft.Text("Keine PDFs zum Senden gefunden.", color="grey", size=16))
                ansicht.controls.append(ft.Text(f"Gesucht in: {download_ordner}", color="white30", size=10))
            else:
                for pdf_pfad in gefundene_pdfs:
                    dateiname = os.path.basename(pdf_pfad)
                    
                    async def teilen_klick(e, pfad=pdf_pfad):
                        try:
                            # Der echte Teilen-Befehl!
                            await share.share_files([ft.ShareFile.from_path(pfad)])
                        except Exception as ex:
                            zeige_fehler(f"Fehler beim Teilen: {ex}")

                    ansicht.controls.append(
                        ft.Container(
                            padding=10,
                            bgcolor="#003300",
                            border_radius=10,
                            content=ft.Column([
                                ft.Text(dateiname, color="white", weight="bold"),
                                ft.ElevatedButton(
                                    "📤 PDF TEILEN", 
                                    on_click=teilen_klick, 
                                    bgcolor="#2196F3", # Das Blau aus deinem Screenshot
                                    color="white", 
                                    width=350,
                                    height=50,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
                                )
                            ])
                        )
                    )
            page.update()

        # --- ARCHIV ---
        def zeige_archiv():
            ansicht.controls.clear()
            ansicht.controls.append(nav_leiste())
            ansicht.controls.append(ft.Container(height=10))
            ansicht.controls.append(
                ft.Row([ft.Text("Archiv", size=24, weight="bold", color="white")], alignment=ft.MainAxisAlignment.START)
            )
            page.update()

        # --- APP STARTEN ---
        zeige_startbildschirm()

    except Exception as e:
        zeige_fehler(str(e))
        ansicht.controls.append(ft.Text(traceback.format_exc(), color="white30", size=10))
        page.update()

if __name__ == "__main__":
    ft.app(target=main)