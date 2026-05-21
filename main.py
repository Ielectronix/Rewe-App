import flet as ft
import os
import datetime
import shutil
import json

LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent.png")
START_LOGO_PFAD = os.path.join("assets", "bilacon_logo_transparent1.png")


def main(page: ft.Page):
    page.title = "Rewe Monitoring"
    page.bgcolor = "#001a00"
    page.scroll = "auto"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    aktive_ansicht = "touren"

    share_obj = None
    if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
        try:
            share_obj = ft.Share()
            page.services.append(share_obj)
        except Exception as ex:
            print(f"Share-Service konnte nicht geladen werden: {ex}")
            share_obj = None

    try:
        from datenverwaltung import (
            lade_maerkte,
            speichere_maerkte,
            lade_benutzer,
            speichere_benutzer,
            hole_alle_benutzer,
            registriere_neuen_benutzer,
            authentifiziere_benutzer,
        )
        from pdf_generator import get_all_rewe_bases
        from formular import zeige_maske_ui

        # ==========================================
        # PERSISTENTER GESENDET-STATUS
        # ==========================================

        APP_DATA_DIR = os.getenv("FLET_APP_STORAGE_DATA", ".")
        GESENDET_DATEI = os.path.join(APP_DATA_DIR, "rewe_monitoring_gesendet.json")

        def lade_gesendet_status():
            try:
                with open(GESENDET_DATEI, "r", encoding="utf-8") as f:
                    daten = json.load(f)
                    if isinstance(daten, dict):
                        return daten
            except Exception:
                pass
            return {}

        def speichere_gesendet_status(daten):
            try:
                os.makedirs(APP_DATA_DIR, exist_ok=True)
                with open(GESENDET_DATEI, "w", encoding="utf-8") as f:
                    json.dump(daten, f, ensure_ascii=False, indent=2)
            except Exception as ex:
                print(f"Speicherfehler: {ex}")

        def ist_gesendet(pfad):
            return pfad in lade_gesendet_status()

        def markiere_als_gesendet(pfad, raw=""):
            daten = lade_gesendet_status()
            daten[pfad] = {
                "zeit": datetime.datetime.now().isoformat(timespec="seconds"),
                "raw": raw or "",
            }
            speichere_gesendet_status(daten)

        def entferne_gesendet_markierung(pfad):
            daten = lade_gesendet_status()
            if pfad in daten:
                del daten[pfad]
                speichere_gesendet_status(daten)

        def get_share_status_name(result):
            try:
                status = getattr(result, "status", "")
                name = getattr(status, "name", str(status))
                return str(name).upper()
            except Exception:
                return ""

        def meldung(text):
            try:
                page.show_dialog(ft.SnackBar(ft.Text(text)))
            except Exception:
                try:
                    page.snack_bar = ft.SnackBar(ft.Text(text))
                    page.snack_bar.open = True
                    page.update()
                except Exception:
                    print(text)

        def setze_aktive_ansicht(name):
            nonlocal aktive_ansicht
            aktive_ansicht = name

        def on_lifecycle(e: ft.AppLifecycleStateChangeEvent):
            try:
                if e.state in [ft.AppLifecycleState.RESTART, ft.AppLifecycleState.RESUME]:
                    if aktive_ansicht == "senden":
                        zeige_postausgang()
                    elif aktive_ansicht == "archiv":
                        zeige_archiv()
            except Exception:
                pass

        try:
            page.on_app_lifecycle_state_change = on_lifecycle
        except Exception:
            pass

        def get_erweiterte_bases():
            try:
                return get_all_rewe_bases() + ["/storage/emulated/0/Download/Rewe_Monitoring"]
            except Exception:
                return []

        def bereinige_archiv():
            heute = datetime.datetime.now()

            for base in get_erweiterte_bases():
                if not os.path.exists(base):
                    continue

                try:
                    for ordner in os.listdir(base):
                        ordner_pfad = os.path.join(base, ordner)

                        if os.path.isdir(ordner_pfad) and ordner != "temp":
                            try:
                                ordner_datum = datetime.datetime.strptime(ordner, "%Y-%m-%d")

                                if (heute - ordner_datum).days > 14:
                                    shutil.rmtree(ordner_pfad)
                            except Exception:
                                pass

                except PermissionError:
                    pass

        def get_logo_bild():
            if os.path.exists(LOGO_PFAD):
                return ft.Image(src=LOGO_PFAD, width=200, height=100, fit="contain")
            return ft.Text("LOGO", color="white")

        def get_start_logo_bild():
            if os.path.exists(START_LOGO_PFAD):
                return ft.Image(src=START_LOGO_PFAD, height=80, fit="contain")
            return ft.Text("REWE Monitoring", color="white", weight="bold", size=28)

        def nav_leiste(active_tab="touren"):
            def make_btn(text, tab_id, on_click):
                is_active = active_tab == tab_id

                return ft.ElevatedButton(
                    content=ft.Text(text, size=13, weight="bold"),
                    on_click=on_click,
                    bgcolor="#004400" if is_active else "#1a1a1a",
                    color="white",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=10,
                        side=ft.BorderSide(width=1.5, color="#4CAF50"),
                    ),
                )

            return ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
                wrap=True,
                controls=[
                    make_btn("Touren", "touren", lambda e: zeige_dashboard()),
                    make_btn("Senden", "senden", lambda e: zeige_postausgang()),
                    make_btn("Archiv", "archiv", lambda e: zeige_archiv()),
                ],
            )

        def action_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=14, weight="bold"),
                on_click=on_click,
                bgcolor="#0b1a0b",
                color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=25),
                    padding=15,
                    side=ft.BorderSide(width=2, color=farbe),
                ),
            )

        def list_action_btn(text, on_click, farbe, ref=None):
            return ft.ElevatedButton(
                ref=ref,
                content=ft.Text(text, size=12, weight="bold"),
                on_click=on_click,
                bgcolor="#0b1a0b",
                color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=15),
                    padding=8,
                    side=ft.BorderSide(width=1.5, color=farbe),
                ),
            )

        def small_btn(text, on_click, farbe):
            return ft.ElevatedButton(
                content=ft.Text(text, size=16),
                on_click=on_click,
                bgcolor="#0b1a0b",
                color=farbe,
                style=ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    padding=0,
                    side=ft.BorderSide(width=2, color=farbe),
                ),
                width=45,
                height=45,
            )

        def baue_pdf_zeile(pfad, mit_loeschen=False):
            dateiname = os.path.basename(pfad)
            start_gesendet = ist_gesendet(pfad)

            text_ref = ft.Ref[ft.Text]()
            mark_ref = ft.Ref[ft.Text]()
            send_ref = ft.Ref[ft.ElevatedButton]()

            def setze_status_ui(gesendet=False, pending=False):
                if not text_ref.current or not mark_ref.current:
                    return

                if pending:
                    text_ref.current.color = "#FFEB3B"
                    mark_ref.current.value = "..."
                    mark_ref.current.color = "#FFEB3B"

                elif gesendet:
                    text_ref.current.color = "#4CAF50"
                    mark_ref.current.value = "✓"
                    mark_ref.current.color = "#4CAF50"

                else:
                    text_ref.current.color = "white"
                    mark_ref.current.value = ""
                    mark_ref.current.color = "#4CAF50"

            async def on_teilen_click(e):
                if not share_obj:
                    meldung("Teilen ist auf dieser Plattform nicht verfügbar.")
                    return

                try:
                    send_ref.current.disabled = True
                    send_ref