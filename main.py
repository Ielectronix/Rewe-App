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

    share_obj = None
    try:
        if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
            share_obj = ft.Share()
            try:
                page.services.append(share_obj)
            except Exception:
                pass
    except Exception:
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
        # SPEICHER FÜR GESENDET-STATUS
        # ==========================================

        def lade_gesendet():
            try:
                if page.client_storage.contains_key("gesendet_pdfs"):
                    daten = page.client_storage.get("gesendet_pdfs")
                    if daten:
                        return set(daten)
            except Exception:
                pass
            return set()

        def markiere_als_gesendet(pfad):
            gesendet = lade_gesendet()
            gesendet.add(pfad)
            try:
                page.client_storage.set("gesendet_pdfs", list(gesendet))
            except Exception: