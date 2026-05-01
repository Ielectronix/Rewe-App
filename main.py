import flet as ft

def main(page: ft.Page):
    page.title = "REWE Monitoring"
    page.bgcolor = "#003300"
    page.padding = 0
    page.scroll = None # Hauptseite bleibt starr, schützt vor Abstürzen

    # 1. Kopfzeile (Navigation)
    nav_leiste = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)
    
    # 2. Hauptbereich (Hier wird immer nur EINE Kategorie geladen)
    # ListView ist der sicherste Container in Flet gegen graue Fenster!
    haupt_bereich = ft.ListView(expand=True, padding=20, spacing=15)

    # 3. Das Teilen-Modul (Streng isoliert!)
    share = None
    if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
        share = ft.Share()
        page.overlay.append(share) # Wird NUR auf dem Handy geladen! Roter Balken am PC ist weg!

    # --- DIE NEUE LOGIK ---
    def lade_stammdaten(e=None):
        haupt_bereich.controls.clear()
        haupt_bereich.controls.append(ft.Text("Stammdaten", size=24, weight="bold", color="white"))
        # Hier kommen NUR die Stammdaten-Felder rein
        haupt_bereich.controls.append(ft.TextField(label="Marktnummer"))
        page.update()

    def lade_trinkwasser(e=None):
        haupt_bereich.controls.clear() # Wirft alles andere raus!
        haupt_bereich.controls.append(ft.Text("Trinkwasser-Check", size=24, weight="bold", color="white"))
        # Hier kommen NUR die Trinkwasser-Felder rein
        haupt_bereich.controls.append(ft.Checkbox(label="Kaltwasser"))
        page.update()

    # Buttons für die Navigation
    nav_leiste.controls.extend([
        ft.ElevatedButton("Stammdaten", on_click=lade_stammdaten),
        ft.ElevatedButton("Trinkwasser", on_click=lade_trinkwasser),
    ])

    # Zusammenbau
    page.add(
        ft.SafeArea(
            ft.Column([
                nav_leiste,
                ft.Divider(color="white"),
                haupt_bereich # Nimmt den restlichen Platz ein
            ])
        )
    )

    # Start-Zustand
    lade_stammdaten()

ft.app(target=main)