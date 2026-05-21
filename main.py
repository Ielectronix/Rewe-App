        def zeige_postausgang():
            page.clean()
            ansicht = ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            ansicht.controls.append(nav_leiste("senden"))
            ansicht.controls.append(ft.Text("Postausgang (Heute)", size=20, weight="bold", color="white", text_align="center"))
            
            heute_ordner = datetime.datetime.now().strftime('%Y-%m-%d')
            pdfs_gefunden = False
            such_ordner = []
            for base in get_erweiterte_bases():
                such_ordner.append(os.path.join(base, heute_ordner))
                such_ordner.append(base)
            
            # WICHTIG: Hier laden wir den aktuellen Status VOR der Schleife frisch aus dem Speicher!
            aktuelles_gesendet_set = lade_gesendet() 
            
            for ordner in list(set(such_ordner)):
                if not os.path.exists(ordner): continue
                try:
                    for f in os.listdir(ordner):
                        if f.lower().endswith(".pdf"):
                            pdfs_gefunden = True
                            pfad = os.path.join(ordner, f)
                            
                            ist_gesendet = pfad in aktuelles_gesendet_set
                            
                            # Wenn gesendet: grüner Text + Haken. Wenn nicht: weißer Text
                            anzeige_text = f"{f} ✅" if ist_gesendet else f
                            text_farbe = "#4CAF50" if ist_gesendet else "white"
                            
                            async def teilen_jetzt(e, p=pfad):
                                # 1. Datei teilen
                                if share_obj: 
                                    await share_obj.share_files([ft.ShareFile.from_path(p)], text="REWE Bericht")
                                    # 2. Status speichern
                                    markiere_als_gesendet(p)
                                    # 3. SOFORT die Seite neu aufbauen
                                    zeige_postausgang() 
                                else: print("Share geht auf dem PC nicht.")

                            def rm(e, p=pfad):
                                if os.path.exists(p): os.remove(p)
                                zeige_postausgang()

                            ansicht.controls.append(ft.Container(bgcolor="#002200", padding=10, border_radius=15, content=ft.Row([
                                ft.Text(anzeige_text, color=text_farbe, size=13, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS), 
                                list_action_btn("📤 Senden", teilen_jetzt, "#2196F3"), 
                                small_btn("🗑️", rm, "#F44336")
                            ])))
                except: pass
            if not pdfs_gefunden: ansicht.controls.append(ft.Text("Keine Berichte zum Senden.", color="white54", text_align="center"))
            
            page.add(ft.SafeArea(ansicht))
            page.update() # Zwingt das Handy, die neue Ansicht sofort zu zeichnen
