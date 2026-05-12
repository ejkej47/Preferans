"""
Prikazivanje i iscrtavanje na ekranu - sve vezano za vidljive elemente
"""
import pygame
from ui.constants import *
from ui.components import UIComponents

class DisplayHandler:
    """Svo iscrtavanje UI elementa"""
    
    def __init__(self, gui):
        self.gui = gui
    
    def osvezi_ekran(self, screen):
        screen.fill(IPREF_SIVA)
        
        # 1. Crtamo panele (okvire)
        self.nacrtaj_okvire_panela(screen)
        
        # 2. Crtamo sadržaj levog panela
        self.nacrtaj_istoriju_licitacije(screen)
        self.nacrtaj_info_box(screen)
        
        # 3. Ostali elementi (desni panel, karte, sto)
        self.nacrtaj_desni_panel(screen) # Rezultati
        self.nacrtaj_moje_karte(screen)
        self.nacrtaj_bot_karte(screen)
        self.nacrtaj_centralni_deo(screen)
        self.nacrtaj_gomilice(screen)
        self.nacrtaj_scoring(screen)  
        #self.nacrtaj_placeholder_prozor(screen)

        
        if self.gui.prikaz_odnetih is not None:
            self.nacrtaj_pregled_odnetih(screen)

        if self.gui.round_history.show_round_overlay:
            self.nacrtaj_overlay_istorije_rundi(screen)

        pygame.display.flip()


    def nacrtaj_placeholder_prozor(self, screen):
        w = 450  # širina prozora
        h = 280  # visina prozora
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x,y,w,h))
        pygame.draw.rect(screen, CRNA, (x,y,w,h), 2)
        txt = FONT_SMALL.render("x=210, y=140, w=580, h=370", True, (150,150,150))
        screen.blit(txt, (220, 150))

    def nacrtaj_scoring(self, screen):
        """Prikazuje score pored karata svakog igrača"""
        scoring = self.gui.scoring
        
        redosled = {
            0: (2, 1),
            1: (0, 2),
            2: (1, 0),
        }
        
        pozicije = {
            0: (500, 515),
            1: (600, 165),
            2: (300, 165),
        }
        
        CEL_W = 90   # ukupna širina celog score boxa
        COL_W = 28   # širina jedne kolone
        H = 20       # visina
        
        for pid, (x, y) in pozicije.items():
            levo_id, desno_id = redosled[pid]
            
            supa_levo  = scoring.supe[pid][levo_id]
            bula      = scoring.bula[pid]
            supa_desno = scoring.supe[pid][desno_id]
            
            vrednosti = [str(supa_levo), str(bula), str(supa_desno)]
            boje_pozadine = [
                (200, 200, 200),  # supa levo - svetlo siva
                (60, 60, 180),    # bula - plava da se istakne
                (200, 200, 200),  # supa desno - svetlo siva
            ]
            boje_teksta = [
                CRNA,
                ZLATNA,
                CRNA,
            ]
            
            for i, (vrednost, boja_poz, boja_txt) in enumerate(zip(vrednosti, boje_pozadine, boje_teksta)):
                rx = x + i * (COL_W + 1)
                # Pozadina
                pygame.draw.rect(screen, boja_poz, (rx, y, COL_W, H), border_radius=3)
                # Okvir
                pygame.draw.rect(screen, CRNA, (rx, y, COL_W, H), 1, border_radius=3)
                # Tekst centriran
                txt = FONT_SMALL.render(vrednost, True, boja_txt)
                tx = rx + (COL_W - txt.get_width()) // 2
                ty = y + (H - txt.get_height()) // 2
                screen.blit(txt, (tx, ty))

    def nacrtaj_okvire_panela(self, screen):
        """Crtanje osnovnih kontejnera za UI"""
        # Gornji levi: Istorija (Skraćen na 350px visine)
        UIComponents.nacrtaj_okvir(screen, "Istorija Licitacije", 10, 10, 180, 350)
        
        # Donji levi: Info Box
        UIComponents.nacrtaj_okvir(screen, "", 10, 370, 180, 320)
        
       
        # Desni panel: Score + odvojeno dugme za detalje rundi
        UIComponents.nacrtaj_okvir(screen, "", 810, 10, 180, 600)

    def nacrtaj_istoriju_licitacije(self, screen):
        ukupna_visina = len(self.gui.istorija_licitacije) * 22
        vidljiva_visina = 310
        
        # Reset scroll ako nema overflow
        if ukupna_visina <= vidljiva_visina:
            self.gui.istorija_scroll = 0

        povrsina_istorije = pygame.Surface((160, vidljiva_visina))
        povrsina_istorije.fill(BELA)
        
        for i, stavka in enumerate(self.gui.istorija_licitacije):
            txt = FONT_SMALL.render(stavka, True, CRNA)
            povrsina_istorije.blit(txt, (5, 5 + i * 22 + self.gui.istorija_scroll))
            
        screen.blit(povrsina_istorije, (20, 40))

    def nacrtaj_info_box(self, screen):
        panel_x = 10
        panel_y = 370
        panel_w = 180
        panel_h = 320

        pob_id = self.gui.pobednik_licitacije
        odigravac = "Čeka se..."
        if pob_id is not None:
            odigravac = "Ja" if pob_id == 0 else f"Bot {pob_id}"
            
        kontrakt = self.gui.adut if self.gui.adut else "Licitacija..."
        
        prate_lista = []
        for i, dolazi in enumerate(self.gui.igraci_koji_dolaze):
            if dolazi is True: prate_lista.append(f"Bot {i+1}")
        if self.gui.moj_izbor_zvanja in ["dodjem", "kontra"]: prate_lista.append("Ja")
        prate = ", ".join(prate_lista) if prate_lista else "Niko"
        vrednost = str(self.gui.trenutna_licitacija_broj)

        # STATUS - zakucan za vrh
        y = panel_y + 8
        n_txt = FONT_BOLD.render("STATUS:", True, CRVENA_PANEL)
        screen.blit(n_txt, (panel_x + 10, y))
        y += 16
        if len(self.gui.poruka) > 20:
            reci = self.gui.poruka.split()
            prvi_red = " ".join(reci[:3])
            drugi_red = " ".join(reci[3:])
            screen.blit(FONT_SMALL.render(prvi_red, True, CRNA), (panel_x + 10, y))
            y += 14
            screen.blit(FONT_SMALL.render(drugi_red, True, CRNA), (panel_x + 10, y))
        else:
            screen.blit(FONT_SMALL.render(self.gui.poruka, True, CRNA), (panel_x + 10, y))

        # Separator ispod statusa
        sep_y = panel_y + 60
        pygame.draw.line(screen, (150, 150, 150), (panel_x, sep_y), (panel_x + panel_w, sep_y), 1)

        # Ostale stavke - ravnomerno od sep_y do dna
        stavke = [
            ("ODIGRAVAČ:", odigravac),
            ("KONTRAKT:", kontrakt),
            ("PRATE:", prate),
            ("VREDNOST:", vrednost)
        ]

        visina_stavke = 45  # stara visina
        preostalo = panel_h - 60  # prostor ispod separatora
        y_start = panel_y + panel_h - len(stavke) * visina_stavke

        for i, (naslov, vred) in enumerate(stavke):
            y = y_start + i * visina_stavke
            n_txt = FONT_BOLD.render(naslov, True, CRNA)
            screen.blit(n_txt, (panel_x + 10, y))

            if len(vred) > 20:
                reci = vred.split()
                prvi_red = " ".join(reci[:3])
                drugi_red = " ".join(reci[3:])
                screen.blit(FONT_SMALL.render(prvi_red, True, CRNA), (panel_x + 10, y + 18))
                screen.blit(FONT_SMALL.render(drugi_red, True, CRNA), (panel_x + 10, y + 33))
            else:
                screen.blit(FONT_SMALL.render(vred, True, CRNA), (panel_x + 10, y + 18))

            if i < len(stavke) - 1:
                pygame.draw.line(screen, (150, 150, 150), 
                            (panel_x, y + visina_stavke - 4), 
                            (panel_x + panel_w, y + visina_stavke - 4), 1)

    def nacrtaj_desni_panel(self, screen):
        rh = self.gui.round_history

        rh.tab_rects = []
        rh.details_button_rect = None

        # Gornji deo: Tabovi koji potpuno popunjavaju vrh panela
        tab_x = 811
        tab_y = 11
        tab_w = 178

        self.nacrtaj_score_tabove(screen, tab_x, tab_y, tab_w)
        
        # Tabela ide malo ispod tabova, sa uklonjenim praznim naslovom
        tabela_x = 815
        tabela_y = tab_y + 35
        tabela_w = 170
        tabela_h = 560

        self.nacrtaj_score_tabelu(screen, tabela_x, tabela_y, tabela_w, tabela_h)

        # Donji deo: posebno dugme za detalje rundi
        dugme_x = 810
        dugme_y = 620
        dugme_w = 180
        dugme_h = 70

        self.nacrtaj_dugme_detalji_rundi(screen, dugme_x, dugme_y, dugme_w, dugme_h)

    def nacrtaj_score_tabove(self, screen, x, y, w):
        rh = self.gui.round_history

        tabovi = [
            (2, "Levi"),
            (0, "Ja"),
            (1, "Desni"),
        ]

        tab_w = w // 3

        for i, (pid, label) in enumerate(tabovi):
            # Poslednji tab preuzima eventualni ostatak piksela do desne ivice
            trenutni_w = tab_w if i < 2 else w - (tab_w * 2)
            
            rect = pygame.Rect(x + i * tab_w, y, trenutni_w, 28)
            aktivan = rh.selected_score_player == pid
            
            # Aktivni tab je beo da se utopi u pozadinu, neaktivni su sivi
            boja = BELA if aktivan else (220, 220, 220)

            # Crtamo tab sa zaobljenim spoljnim ivicama
            pygame.draw.rect(screen, boja, rect, border_top_left_radius=4 if i==0 else 0, border_top_right_radius=4 if i==2 else 0)
            pygame.draw.rect(screen, CRNA, rect, 1, border_top_left_radius=4 if i==0 else 0, border_top_right_radius=4 if i==2 else 0)

            if aktivan:
                txt = FONT_BOLD.render(label, True, CRVENA_PANEL)
            else:
                txt = FONT_SMALL.render(label, True, CRNA)

            screen.blit(
                txt,
                (
                    rect.x + (rect.w - txt.get_width()) // 2,
                    rect.y + (rect.h - txt.get_height()) // 2,
                )
            )

            rh.tab_rects.append((rect, pid))
            
        # Fina linija koja razdvaja tabove od tabele, a brišemo je ispod aktivnog taba!
        pygame.draw.line(screen, CRNA, (x, y + 27), (x + w - 1, y + 27), 1)
        for rect, pid in rh.tab_rects:
            if rh.selected_score_player == pid:
                pygame.draw.line(screen, BELA, (rect.left + 1, rect.bottom - 1), (rect.right - 2, rect.bottom - 1), 2)

    def nacrtaj_score_tabelu(self, screen, x, y, w, h):
        rh = self.gui.round_history
        pid = rh.selected_score_player
        rows = rh.score_history.get(pid, [])

        levo_id, desno_id = rh.score_redosled(pid)

        col_w = w // 3
        row_h = 18

        headers = [
            rh.ime(levo_id),
            "Bula",
            rh.ime(desno_id),
        ]

        header_rect = pygame.Rect(x, y, w - 2, row_h)
        pygame.draw.rect(screen, (220, 220, 220), header_rect)
        pygame.draw.rect(screen, CRNA, header_rect, 1)

        for i, header in enumerate(headers):
            txt = FONT_SMALL.render(header, True, CRNA)
            tx = x + i * col_w + (col_w - txt.get_width()) // 2
            screen.blit(txt, (tx, y + 2))

        y += row_h

        max_rows = max(1, (h - 20) // row_h)
        visible_rows = rows[-max_rows:]

        for row in visible_rows:
            row_rect = pygame.Rect(x, y, w - 2, row_h)

            pygame.draw.rect(screen, (245, 245, 245), row_rect)
            
            # ELIMINIŠEMO DUPLU LINIJU - crtamo samo bočne strane i dno
            pygame.draw.line(screen, CRNA, (x, y), (x, y + row_h), 1) # Leva
            pygame.draw.line(screen, CRNA, (x + w - 3, y), (x + w - 3, y + row_h), 1) # Desna
            pygame.draw.line(screen, CRNA, (x, y + row_h - 1), (x + w - 3, y + row_h - 1), 1) # Dno

            # REFA LOGIKA
            if row.get("is_refa"):
                bula_col_x = x + col_w
                line_start_x = bula_col_x + 6
                line_end_x = bula_col_x + col_w - 6
                line_y = y + row_h // 2
                
                # Horizontalna linija "šešir"
                pygame.draw.line(screen, CRNA, (line_start_x, line_y), (line_end_x, line_y), 2)
                
                refa_obj = row.get("refa_obj", {"odigrao": {0:False, 1:False, 2:False}})
                
                # Leva recka
                if refa_obj["odigrao"][levo_id]:
                    pygame.draw.line(screen, CRNA, (line_start_x, line_y - 6), (line_start_x, line_y + 6), 2)
                
                # Desna recka
                if refa_obj["odigrao"][desno_id]:
                    pygame.draw.line(screen, CRNA, (line_end_x, line_y - 6), (line_end_x, line_y + 6), 2)
                    
                # Srednja recka
                if refa_obj["odigrao"][pid]:
                    mid_x = (line_start_x + line_end_x) // 2
                    pygame.draw.line(screen, CRNA, (mid_x, line_y - 6), (mid_x, line_y + 6), 2)
                    
            else:
                values = [
                    row.get("supa_levo", 0),
                    row.get("bula", 0),
                    row.get("supa_desno", 0),
                ]

                for i, value in enumerate(values):
                    boja_txt = CRVENA_PANEL if i == 1 else CRNA
                    txt = FONT_SMALL.render(str(value), True, boja_txt)
                    tx = x + i * col_w + (col_w - txt.get_width()) // 2
                    screen.blit(txt, (tx, y + 2))

            y += row_h

    def nacrtaj_overlay_istorije_rundi(self, screen):
        rh = self.gui.round_history

        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.set_alpha(225)
        s.fill((25, 25, 25))
        screen.blit(s, (0, 0))

        overlay = pygame.Rect(40, 35, 920, 630)
        pygame.draw.rect(screen, BELA, overlay, border_radius=6)
        pygame.draw.rect(screen, CRNA, overlay, 2, border_radius=6)

        self.nacrtaj_overlay_navigaciju(screen, overlay)

        runda = rh.aktivna_runda()
        if not runda:
            txt = FONT_MSG.render("Još nema završenih rundi.", True, CRNA)
            screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 330))
            return

        # Malo smo pomerili Y koordinate nadole da bi sve lepo stalo
        self.nacrtaj_overlay_info_runde(screen, runda, overlay.x + 20, overlay.y + 55)
        self.nacrtaj_overlay_rezultat_runde(screen, runda, overlay.x + 20, overlay.y + 165)
        self.nacrtaj_overlay_stihove(screen, runda, overlay.x + 20, overlay.y + 265)

    def nacrtaj_overlay_navigaciju(self, screen, overlay):
        rh = self.gui.round_history

        if rh.rounds:
            naslov = f"Runda {rh.active_round_index + 1} / {len(rh.rounds)}"
        else:
            naslov = "Istorija rundi"

        txt = FONT_MSG.render(naslov, True, CRVENA_PANEL)
        naslov_x = overlay.centerx - txt.get_width() // 2
        naslov_y = 47
        
        screen.blit(txt, (naslov_x, naslov_y))

        # Dugmići sada računaju svoju poziciju u odnosu na naslov
        rh.overlay_prev_rect = pygame.Rect(naslov_x - 105, 45, 90, 26)
        rh.overlay_next_rect = pygame.Rect(naslov_x + txt.get_width() + 15, 45, 90, 26)
        rh.overlay_close_rect = pygame.Rect(925, 45, 24, 24)

        pygame.draw.rect(screen, (230, 230, 230), rh.overlay_prev_rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rh.overlay_prev_rect, 1, border_radius=4)
        txt_prev = FONT_SMALL.render("< Prethodna", True, CRNA)
        screen.blit(txt_prev, (rh.overlay_prev_rect.x + (rh.overlay_prev_rect.w - txt_prev.get_width()) // 2, rh.overlay_prev_rect.y + 5))

        pygame.draw.rect(screen, (230, 230, 230), rh.overlay_next_rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rh.overlay_next_rect, 1, border_radius=4)
        txt_next = FONT_SMALL.render("Sledeća >", True, CRNA)
        screen.blit(txt_next, (rh.overlay_next_rect.x + (rh.overlay_next_rect.w - txt_next.get_width()) // 2, rh.overlay_next_rect.y + 5))

        pygame.draw.rect(screen, (240, 200, 200), rh.overlay_close_rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rh.overlay_close_rect, 1, border_radius=4)
        txt_x = FONT_BOLD.render("X", True, CRNA)
        screen.blit(txt_x, (rh.overlay_close_rect.x + (rh.overlay_close_rect.w - txt_x.get_width()) // 2, rh.overlay_close_rect.y + 3))

    def nacrtaj_overlay_info_runde(self, screen, runda, x, y):
        rh = self.gui.round_history

        nosilac = rh.ime(runda["nosilac"])
        adut = runda["adut"]
        vrednost = runda["vrednost"]

        tipovi = []
        if runda["direktna_igra"]: tipovi.append("iz ruke")
        else: tipovi.append("sa talonom")

        if runda["kontra"]:
            if runda["zvanje_igrac"] is not None: tipovi.append(f"kontra: {rh.ime(runda['zvanje_igrac'])}")
            else: tipovi.append("kontra")

        if runda["zvanje_tip"] == "zovem":
            tipovi.append(f"zovem: {rh.ime(runda['zvanje_igrac'])}")

        dodatak = ", ".join(tipovi)

        linije = [
            f"Nosilac: {nosilac}",
            f"Igra: {adut} ({dodatak})",
            f"Vrednost: {vrednost}",
        ]

        # Ispis generalnih informacija uspravno
        trenutni_y = y
        for linija in linije:
            txt = FONT_BOLD.render(linija, True, CRNA)
            screen.blit(txt, (x, trenutni_y))
            trenutni_y += 24

        stihovi = runda["stihovi_po_igracu"]
        stih_txt = f"Štihovi: Ja {stihovi.get(0, 0)} | Levi {stihovi.get(2, 0)} | Desni {stihovi.get(1, 0)}"
        txt = FONT_BOLD.render(stih_txt, True, CRVENA_PANEL)
        screen.blit(txt, (x, trenutni_y))

        # Poziv funkcije za crtanje početnih karata na desnoj strani (x + 350)
        self.nacrtaj_overlay_pocetne_karte(screen, runda, x + 350, y)

    def nacrtaj_overlay_pocetne_karte(self, screen, runda, x, y):
        naslov = FONT_BOLD.render("Početne karte igrača i talon:", True, CRVENA_PANEL)
        screen.blit(naslov, (x, y))
        y += 38

        ruke = runda.get("pocetne_ruke", [[], [], []])
        talon = runda.get("pocetni_talon", [])
        redosled = [(0, "Ja"), (2, "Levi"), (1, "Desni")]

        # Interna helper funkcija za crtanje "tekstualne" karte u okviru
        def nacrtaj_mini(karta, dx, dy):
            v, b = karta.split()
            znak_mapa = {'Pik': '♠', 'Karo': '♦', 'Herc': '♥', 'Tref': '♣'}
            boja_znaka = {'Pik': CRNA, 'Karo': (220, 0, 0), 'Herc': (220, 0, 0), 'Tref': CRNA}
            
            txt_v = FONT_MSG.render(v, True, CRNA)
            txt_s = FONT_MSG.render(znak_mapa.get(b, b), True, boja_znaka.get(b, CRNA))
            
            # FIKSNE DIMENZIJE KARTE
            box_w = 44  # Dovoljno široko da stane "10" i znak
            box_h = 38
            
            box_rect = pygame.Rect(dx, dy - 8, box_w, box_h)
            
            # Pozadina i okvir "karte"
            pygame.draw.rect(screen, BELA, box_rect, border_radius=4)
            pygame.draw.rect(screen, (150, 150, 150), box_rect, 1, border_radius=4)
            
            # Centriramo kombinovani tekst (broj + razmak + znak) unutar fiksne širine
            ukupna_sirina = txt_v.get_width() + txt_s.get_width() + 2
            pocetni_x = box_rect.x + (box_w - ukupna_sirina) // 2
            tekst_y = box_rect.y + (box_h - txt_v.get_height()) // 2 + 1
            
            # Iscrtavanje
            screen.blit(txt_v, (pocetni_x, tekst_y))
            screen.blit(txt_s, (pocetni_x + txt_v.get_width() + 2, tekst_y))
            
            return box_w + 6  # Vraća fiksnu širinu + razmak do sledeće karte

        # Pravila za sortiranje kao u ruci
        red_boja = {'Pik': 0, 'Karo': 1, 'Tref': 2, 'Herc': 3}
        red_vrednosti = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, '10': 4, '9': 5, '8': 6, '7': 7}
        
        def sortiraj_niz(niz):
            return sorted(niz, key=lambda karta: (red_boja[karta.split()[1]], red_vrednosti[karta.split()[0]]))

        # Crtamo karte u rukama
        for pid, ime in redosled:
            ime_txt = FONT_SMALL.render(f"{ime}: ", True, (100, 100, 100))
            screen.blit(ime_txt, (x, y + 4))
            
            kart_x = x + 40
            for karta in sortiraj_niz(ruke[pid]):
                kart_x += nacrtaj_mini(karta, kart_x, y)
            y += 42  # Povećan razmak između redova

        # Crtamo talon ispod svega
        ime_txt = FONT_SMALL.render("Talon: ", True, (100, 100, 100))
        screen.blit(ime_txt, (x , y + 4)) # Pomereno malo levo zbog dužeg teksta
        kart_x = x + 40
        for karta in sortiraj_niz(talon):
            kart_x += nacrtaj_mini(karta, kart_x, y)


    def nacrtaj_overlay_rezultat_runde(self, screen, runda, x, y):
        rh = self.gui.round_history

        naslov = FONT_BOLD.render("Rezultat i promene:", True, CRVENA_PANEL)
        screen.blit(naslov, (x, y))
        y += 24

        rezultat = runda["rezultat"]

        for pid in (0, 2, 1):
            if pid not in rezultat:
                continue

            tekst = f"{rh.ime(pid)}: {rezultat[pid]}"
            tekst = self.skrati_tekst(tekst, 75)

            txt = FONT_SMALL.render(tekst, True, CRNA)
            screen.blit(txt, (x, y))
            y += 18


    def nacrtaj_overlay_stihove(self, screen, runda, x, y):
        naslov = FONT_BOLD.render("Štihovi:", True, CRVENA_PANEL)
        screen.blit(naslov, (x, y))
        y += 25

        stihovi = runda["stihovi"]
        leva_kolona = stihovi[:5]
        desna_kolona = stihovi[5:10]

        self.nacrtaj_kolonu_stihova(screen, leva_kolona, x, y)
        self.nacrtaj_kolonu_stihova(screen, desna_kolona, x + 455, y)


    def nacrtaj_kolonu_stihova(self, screen, stihovi, x, y):
        for stih in stihovi:
            self.nacrtaj_jedan_stih(screen, stih, x, y)
            y += 67


    def nacrtaj_jedan_stih(self, screen, stih, x, y):
        rh = self.gui.round_history

        rect = pygame.Rect(x, y, 430, 58)
        pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rect, 1, border_radius=4)

        pobednik = stih["pobednik"]

        naslov = f"Štih {stih['broj']}"
        txt_naslov = FONT_BOLD.render(naslov, True, CRNA)
        screen.blit(txt_naslov, (x + 8, y + 5))

        # Rečnici za pretvaranje teksta u simbole i boje
        znak_mapa = {'Pik': '♠', 'Karo': '♦', 'Herc': '♥', 'Tref': '♣'}
        boja_znaka = {'Pik': CRNA, 'Karo': (220, 0, 0), 'Herc': (220, 0, 0), 'Tref': CRNA}

        start_x = x + 8
        box_y = y + 27
        box_h = 24

        for idx, (pid, karta) in enumerate(stih["karte"]):
            v, b = karta.split()
            simbol = znak_mapa.get(b, b)
            boja = boja_znaka.get(b, CRNA)
            
            je_pobednik = (pid == pobednik)
            ime_txt = rh.ime(pid)
            
            # Priprema teksta
            ime_surf = FONT_SMALL.render(f"{ime_txt}  {v}", True, CRNA)
            simbol_surf = FONT_SMALL.render(simbol, True, boja)
            
            # Računanje širine malog okvira (box-a)
            box_w = ime_surf.get_width() + simbol_surf.get_width() + 10
    
            # Crtanje box-a za tog igrača
            box_rect = pygame.Rect(start_x, box_y, box_w, box_h)
            boja_pozadine = (220, 240, 220) if je_pobednik else BELA
            boja_okvira = (0, 150, 0) if je_pobednik else (150, 150, 150)
            
            pygame.draw.rect(screen, boja_pozadine, box_rect, border_radius=3)
            pygame.draw.rect(screen, boja_okvira, box_rect, 1, border_radius=3)
            
            # Iscrtavanje unutrašnjosti box-a
            trenutni_x = start_x + 5
            tekst_y = box_y + (box_h - ime_surf.get_height()) // 2
            
            screen.blit(ime_surf, (trenutni_x, tekst_y))
            trenutni_x += ime_surf.get_width()
            
            screen.blit(simbol_surf, (trenutni_x, tekst_y))
            trenutni_x += simbol_surf.get_width()
            
            start_x += box_w + 10 # Odmaknemo se za crtanje strelice
            
            # Crtanje strelice između igrača (samo ako nije poslednji u nizu)
            if idx < len(stih["karte"]) - 1:
                strelica_surf = FONT_SMALL.render("→", True, (120, 120, 120))
                screen.blit(strelica_surf, (start_x, tekst_y))
                start_x += strelica_surf.get_width() + 10


    def skrati_tekst(self, tekst, max_len):
        if len(tekst) <= max_len:
            return tekst
        return tekst[:max_len - 3] + "..."

    def nacrtaj_dugme_detalji_rundi(self, screen, x, y, w, h):
        rh = self.gui.round_history

        rect = pygame.Rect(x, y, w, h)
        rh.details_button_rect = rect

        ima_rundi = len(rh.rounds) > 0

        boja_dugmeta = (205, 230, 245)
        boja_hover = (185, 215, 235)
        boja_teksta = (15, 30, 40) if ima_rundi else (105, 115, 120)

        mis_pos = pygame.mouse.get_pos()
        boja_final = boja_hover if rect.collidepoint(mis_pos) else boja_dugmeta

        pygame.draw.rect(screen, boja_final, rect, border_radius=5)
        pygame.draw.rect(screen, CRNA, rect, 1, border_radius=5)

        naslov = "DETALJI RUNDI"
        podnaslov = f"{len(rh.rounds)} završeno" if ima_rundi else "Još nema rundi"

        txt1 = FONT_BOLD.render(naslov, True, boja_teksta)
        txt2 = FONT_SMALL.render(podnaslov, True, boja_teksta)

        screen.blit(txt1, (rect.x + (rect.w - txt1.get_width()) // 2, rect.y + 11))
        screen.blit(txt2, (rect.x + (rect.w - txt2.get_width()) // 2, rect.y + 34))  

    def nacrtaj_moje_karte(self, screen):
        """Moje karte sa mogućnostima izbora i hover efektom"""
        if self.gui.stanje == "SKARTIRANJE":
            return
            
        self.gui.rects = []
        mis_pos = self.gui.mis_pozicija
        
        # Proveri validne poteze ako smo u igri i ako smo mi na potezu
        validni = []
        if self.gui.stanje == "IGRA" and self.gui.na_potezu == 0:
            prva = self.gui.karte_na_stolu[0][1] if self.gui.karte_na_stolu else None
            validni = self.gui.logika.validni_potezi(self.gui.moje_karte, prva, self.gui.adut)
            
        # 1. Prvo tražimo kartu na kojoj je miš (od nazad, da bi hvatali najgornju na preklopu)
        n = len(self.gui.moje_karte)
        KARTA_W = 100
        razmak = 45
        ukupna_sirina = (n - 1) * razmak + KARTA_W
        start_x = (SCREEN_W - ukupna_sirina) // 2

        hoverovana_karta = None
        for i in reversed(range(len(self.gui.moje_karte))):
            karta = self.gui.moje_karte[i]
            y_baza = 480 if karta in getattr(self.gui, 'skart_izabrane', []) else 540
            rect = pygame.Rect(start_x + i * razmak, y_baza, 100, 140)
            if rect.collidepoint(mis_pos):
                hoverovana_karta = karta
                break

        for i, karta in enumerate(self.gui.moje_karte):
            y_pos = 480 if karta in getattr(self.gui, 'skart_izabrane', []) else 540
            
            if karta == hoverovana_karta and self.gui.stanje == "IGRA" and self.gui.na_potezu == 0:
                if karta in validni:
                    y_pos -= 15  
            
            slika = self.gui.slike_karata_velike.get(karta)
            rect = pygame.Rect(start_x + i * razmak, y_pos, 100, 140)
            
            if slika:
                screen.blit(slika, rect)
                pygame.draw.rect(screen, CRNA, rect, 1, border_radius=3)
                
                if karta in getattr(self.gui, 'skart_izabrane', []):
                    pygame.draw.rect(screen, (255, 0, 0), rect, 3, border_radius=3) 
            self.gui.rects.append((rect, karta))

    def nacrtaj_bot_karte(self, screen):
        """Karte bot-ova (samo poledina) + njihove poruke i statusi"""
        
        pozicije = {
            2: (220, 10), # Bot 2 levo
            1: (580, 10)  # Bot 1 desno
        }
        
        # 1. Pronalazimo ko je poslednji komunicirao za zlatni okvir (samo u licitaciji)
        zadnji_bot_vreme = -1
        zadnji_bot_id = None
        for b_id, vreme in getattr(self.gui, 'vreme_bot_poruke', {}).items():
            if vreme > zadnji_bot_vreme:
                zadnji_bot_vreme = vreme
                zadnji_bot_id = b_id
        
        u_licitaciji = self.gui.stanje in ["FAZA_IZBORA", "FAZA_LICITACIJE"]
        
        for bot_id, (x, y) in pozicije.items():
            # Crtanje poleđina karata
            if self.gui.poledina:
                for i in range(len(self.gui.ruke[bot_id])): 
                    screen.blit(self.gui.poledina, (x + i * 15, y + 30))
            
            # Ime bota
            ime_tekst = f"Bot {bot_id}"
            ime_surf = FONT_BOLD.render(ime_tekst, True, CRNA)
            screen.blit(ime_surf, (x, y))
            
            # 2. Određivanje poruke i boja oblačića
            msg = self.gui.bot_poruke.get(bot_id, "")
            boja_txt = CRNA
            boja_pozadine = BELA
            zlatni_okvir = False
            prikazi_oblak = False
            
            if u_licitaciji:
                # --- LOGIKA ZA VREME LICITACIJE ---
                if msg:
                    prikazi_oblak = True
                    if "Dalje" in msg:
                        boja_txt = (100, 100, 100) # Siva slova
                    else:
                        boja_pozadine = (230, 240, 255) # Svetlo plava
                    
                    # Zlatni okvir oko oblačića samo za onog koji je zadnji odigrao
                    if bot_id == zadnji_bot_id:
                        zlatni_okvir = True
            else:
                # --- LOGIKA KAD SE LICITACIJA ZAVRŠI ---
                prikazi_oblak = True
                
                # Ako je ovaj bot NOSILAC
                if self.gui.pobednik_licitacije == bot_id:
                    adut = getattr(self.gui, 'adut', 'Igru')
                    msg = f"[NOSILAC] Igra {adut}"
                    boja_pozadine = (255, 235, 100) # Zlatno/žuta pozadina
                    boja_txt = CRNA
                else:
                    # Ako je ovaj bot PRATILAC
                    odluka = self.gui.igraci_koji_dolaze[bot_id - 1]
                    
                    if self.gui.kontra_aktivan and odluka is True:
                        # Ako je pala kontra, a on je pratio -> Plavo za obojicu
                        msg = "KONTRA!"
                        boja_pozadine = (40, 100, 220) # Plava
                        boja_txt = BELA
                    elif odluka is True:
                        msg = "Dodjem"
                        boja_pozadine = (40, 150, 40) # Zelena
                        boja_txt = BELA
                    elif odluka is False:
                        msg = "Ne dodjem"
                        boja_pozadine = (180, 40, 40) # Crvena
                        boja_txt = BELA
                    else:
                        # Nije se još izjasnio, prikazujemo njegov default msg ako ga ima
                        if not msg:
                            prikazi_oblak = False
                        else:
                            boja_txt = (100, 100, 100)
            
            # 3. Finalno crtanje oblačića pored imena bota
            if prikazi_oblak and msg:
                txt_surf = FONT_BOLD.render(msg, True, boja_txt)
                pad_x, pad_y = 8, 4
                rect_w = txt_surf.get_width() + pad_x * 2
                rect_h = txt_surf.get_height() + pad_y * 2
                
                # Pozicija oblačića se fiksira odmah desno od "Bot X" teksta
                oblac_x = x + ime_surf.get_width() + 10
                oblac_y = y - 4
                msg_rect = pygame.Rect(oblac_x, oblac_y, rect_w, rect_h)
                
                # Ako je aktivan zlatni okvir (tokom licitacije)
                if zlatni_okvir:
                    pygame.draw.rect(screen, (255, 215, 0), (msg_rect.x - 3, msg_rect.y - 3, msg_rect.w + 6, msg_rect.h + 6), border_radius=5)
                
                # Crta pozadinu, tanak crni okvir i sam tekst
                pygame.draw.rect(screen, boja_pozadine, msg_rect, border_radius=4)
                pygame.draw.rect(screen, CRNA, msg_rect, 1, border_radius=4)
                screen.blit(txt_surf, (msg_rect.x + pad_x, msg_rect.y + pad_y))

    def nacrtaj_centralni_deo(self, screen):
        """Centralni deo - dugmići i karte na stolu"""
        import pygame
        
        if self.gui.stanje == "FAZA_IZBORA":
            self.nacrtaj_faza_izbora(screen)
        elif self.gui.stanje == "FAZA_LICITACIJE":
            self.nacrtaj_faza_licitacije(screen)
        elif self.gui.stanje == "FAZA_IGRA":
            self.nacrtaj_faza_igra(screen)
        elif self.gui.stanje == "FAZA_DOLASKA":
            self.nacrtaj_faza_dolaska(screen)
        elif self.gui.stanje == "FAZA_ZVANJA":
            self.nacrtaj_faza_zvanja(screen)
        elif self.gui.stanje == "FAZA_NAJAVA":
            self.nacrtaj_faza_najava(screen)
        elif self.gui.stanje == "SKARTIRANJE":
            self.nacrtaj_skartiranje(screen)
        elif self.gui.stanje == "IZBOR_ADUTA":
            self.nacrtaj_izbor_aduta(screen)
        elif self.gui.stanje == "IGRA":
            self.nacrtaj_karte_na_stolu(screen)
        elif self.gui.stanje == "FAZA_KONTRE":
            self.nacrtaj_faza_kontre(screen)

    def nacrtaj_faza_izbora(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2

        if self.gui.na_potezu_licitacija != 0:
            txt = FONT_SMALL.render(f"Bot {self.gui.na_potezu_licitacija} bira početnu igru...", True, CRNA)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, y + h//2))
            return
        

        pygame.draw.rect(screen, BELA, (x, y, w, h))
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2)
        self.gui.dugmici_licitacije = []
        
        opcije = [("Dalje", "dalje"), ("Dva (2)", "dva"), ("Igra", "igra"), 
                ("Betl (6)", "betl"), ("Sans (7)", "sans")]
        
        for i, (txt, akcija) in enumerate(opcije):
            d = UIComponents.nacrtaj_dugme(screen, txt, x + 75, y + 20 + i * 48, 300, 40)
            self.gui.dugmici_licitacije.append((d, akcija))

    def nacrtaj_faza_licitacije(self, screen):
        # Koristimo identične dimenzije kao u faza_izbora
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2

        # 1. Provera da li je igrač ispao
        if 0 not in self.gui.licitacija.aktivni_igraci:
            pygame.draw.rect(screen, BELA, (x, y, w, h))
            pygame.draw.rect(screen, CRNA, (x, y, w, h), 2)
            txt = FONT_SMALL.render("Ispali ste. Botovi licitiraju...", True, CRNA)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, y + h//2))
            return

        # 2. Crtanje okvira (identično faza_izbora)
        pygame.draw.rect(screen, BELA, (x, y, w, h))
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2)
        self.gui.dugmici_licitacije = []

        # 3. Logika za opcije
        # Osnovne dve opcije koje uvek postoje
        opcije = [("Dalje", "dalje")]
        
        trenutni = self.gui.trenutna_licitacija_broj
        if self.gui.poslednja_akcija == "broj":
            opcije.append((f"Moje {trenutni}", "moje"))
        else:
            opcije.append((f"Licitiram {trenutni + 1}", "moje"))

        # Dodatne tri opcije SAMO ako igrač još nije "ušao" u licitaciju brojevima
        if not self.gui.igrac_imao_prvi_krug_licitacije:
            opcije.append(("Igra", "igra"))
            opcije.append(("Betl (6)", "betl"))
            opcije.append(("Sans (7)", "sans"))

        # 4. Crtanje dugmića (isti razmak i pozicija kao u faza_izbora)
        nije_moj_red = self.gui.na_potezu_licitacija != 0
        
        for i, (txt_opcija, akcija) in enumerate(opcije):
            # Koristimo tvoju formulu: y + 20 + i * 48
            dy = y + 20 + i * 48
            boja = (200, 200, 200) if nije_moj_red else (230, 230, 230)
            
            d = UIComponents.nacrtaj_dugme(screen, txt_opcija, x + 75, dy, 300, 40, boja)
            
            if not nije_moj_red:
                self.gui.dugmici_licitacije.append((d, akcija))
            else:
                # Ako bot razmišlja, ispisujemo preko boxa
                if i == 0: # Samo jednom ispiši
                    msg = f"Bot {self.gui.na_potezu_licitacija} razmišlja..."
                    razm_surf = FONT_SMALL.render(msg, True, CRNA)
                    # Brišemo sredinu da se ne meša sa dugmićima dok bot igra
                    pygame.draw.rect(screen, BELA, (x+2, y+2, w-4, h-4))
                    pygame.draw.rect(screen, CRNA, (x, y, w, h), 2)
                    screen.blit(razm_surf, (SCREEN_W//2 - razm_surf.get_width()//2, y + h//2))

    def nacrtaj_faza_igra(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x, y, w, h))
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2)
        self.gui.dugmici_licitacije = []

        opcije = [("Dalje", "dalje")]

        nivo = self.gui.specijalna_igra_nivo

        if nivo < 1:
            opcije.append(("Igra", "igra_igra"))

        if nivo < 2:
            opcije.append(("Betl", "igra_betl"))

        if nivo < 3:
            opcije.append(("Sans", "igra_sans"))

        for i, (txt, akcija) in enumerate(opcije):
            d = UIComponents.nacrtaj_dugme(screen, txt, x + 75, y + 20 + i * 55, 300, 45)
            self.gui.dugmici_licitacije.append((d, akcija))

    def nacrtaj_faza_dolaska(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x, y, w, h))
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 3)

        naslov = FONT_MSG.render("DOLAZAK NA IGRU", True, CRNA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, y + 15))

        dy = y + 55
        for stavka in self.gui.istorija_dolaska:
            txt = FONT_SMALL.render(stavka, True, CRNA)
            screen.blit(txt, (x + 20, dy))
            dy += 30

        if self.gui.botovi_desili_odluku[0]:
            status1 = "✓ Pratim" if self.gui.igraci_koji_dolaze[0] else "✗ Ne pratim"
            txt1 = FONT_SMALL.render(f"Bot 1: {status1}", True, CRNA)
        else:
            txt1 = FONT_SMALL.render("Bot 1: čeka...", True, (200, 200, 200))
        screen.blit(txt1, (x + 20, y + 180))

        if self.gui.botovi_desili_odluku[1]:
            status2 = "✓ Pratim" if self.gui.igraci_koji_dolaze[1] else "✗ Ne pratim"
            txt2 = FONT_SMALL.render(f"Bot 2: {status2}", True, CRNA)
        else:
            txt2 = FONT_SMALL.render("Bot 2: čeka...", True, (200, 200, 200))
        screen.blit(txt2, (x + 20, y + 210))

        if not all(self.gui.botovi_desili_odluku):
            waiting = FONT_SMALL.render("Čeka se odluka bota...", True, (200, 0, 0))
            screen.blit(waiting, (x + 20, y + h - 25))

    def nacrtaj_faza_zvanja(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x, y, w, h))
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 3)
        self.gui.dugmici_licitacije = []

        naslov = FONT_MSG.render("DA LI PRATIŠ?", True, CRNA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, y + 15))

        # Prikazujemo centralno koja je igra
        adut_txt = FONT_BOLD.render(f"Objavljena igra: {self.gui.adut}", True, CRVENA_PANEL)
        screen.blit(adut_txt, (SCREEN_W//2 - adut_txt.get_width()//2, y + 45))

        pratioci = [pid for pid in range(3) if pid != self.gui.pobednik_licitacije]
        drugi = [pid for pid in pratioci if pid != 0][0]
        drugi_odluka = self.gui.igraci_koji_dolaze[drugi - 1]

        # Prikazujemo isključivo odluku drugog igrača umesto cele istorije
        status_txt = "čeka se..."
        if drugi_odluka is True:
            status_txt = "Prati"
        elif drugi_odluka is False:
            status_txt = "Odustao"
            
        info_txt = FONT_BOLD.render(f"Bot {drugi}: {status_txt}", True, CRNA)
        screen.blit(info_txt, (SCREEN_W//2 - info_txt.get_width()//2, y + 70))

        opcije = [("Dodjem", "dodjem"), ("Ne dodjem", "ne_dodjem")]
        drugi_odustao = drugi_odluka is False

        if drugi_odustao:
            opcije = [
                ("Dodjem", "dodjem"),
                ("Zovem", "zovem"),
                ("Kontra", "kontra"),
                ("Ne dodjem", "ne_dodjem"),
            ]

        # Računamo dimenzije dugmića tako da uvek lepo stanu i budu veća
        btn_h = 35 if len(opcije) > 2 else 45
        razmak = 42 if len(opcije) > 2 else 55
        start_y = y + 105 if len(opcije) > 2 else y + 120

        for i, (txt, akcija) in enumerate(opcije):
            boja = (255, 200, 200) if akcija == "kontra" else (230, 230, 230)
            d = UIComponents.nacrtaj_dugme(screen, txt, x + 75, start_y + i * razmak, 300, btn_h, boja)
            self.gui.dugmici_licitacije.append((d, akcija))


    def nacrtaj_faza_kontre(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x, y, w, h))
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 3)
        self.gui.dugmici_licitacije = []

        if not self.gui.kontra_red:
            return

        pid = self.gui.kontra_red[self.gui.kontra_index]
        ime = "Ja" if pid == 0 else f"Bot {pid}"

        # Naslov
        naslov = FONT_MSG.render("MOŽE ILI KONTRA?", True, CRNA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, y + 15))

        # Objavljena igra — isto kao faza zvanja
        adut_txt = FONT_BOLD.render(f"Objavljena igra: {self.gui.adut}", True, CRVENA_PANEL)
        screen.blit(adut_txt, (SCREEN_W//2 - adut_txt.get_width()//2, y + 45))

        # Samo jedna kratka statusna linija — isto kao faza zvanja
        if self.gui.kontra_index > 0:
            prethodni_igrac = self.gui.kontra_red[self.gui.kontra_index - 1]
            prethodni_ime = "Ja" if prethodni_igrac == 0 else f"Bot {prethodni_igrac}"
            status_txt = f"{prethodni_ime}: Može"
        else:
            status_txt = f"Na potezu: {ime}"

        info_txt = FONT_BOLD.render(status_txt, True, CRNA)
        screen.blit(info_txt, (SCREEN_W//2 - info_txt.get_width()//2, y + 70))

        if pid != 0:
            txt = FONT_SMALL.render("Bot odlučuje...", True, CRNA)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, y + 120))
            return

        # Fiksirano isto kao faza zvanja sa 2 dugmeta
        opcije = [("Može", "moze"), ("Kontra", "kontra")]
        btn_h = 45
        razmak = 55
        start_y = y + 120

        for i, (txt, akcija) in enumerate(opcije):
            boja = (255, 200, 200) if akcija == "kontra" else (230, 230, 230)
            d = UIComponents.nacrtaj_dugme(screen, txt, x + 75, start_y + i * razmak, 300, btn_h, boja)
            self.gui.dugmici_licitacije.append((d, akcija))

    def nacrtaj_skartiranje(self, screen):
        self.gui.rects = []
        karte_za_skart = self.gui.karte_za_skart
        karte_u_ruci = [k for k in self.gui.moje_karte if k not in karte_za_skart]

        # Centralni prozor
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2

        pygame.draw.rect(screen, BELA, (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2, border_radius=4)

        lbl = FONT_BOLD.render("ODABERI 2 KARTE ZA ŠKART", True, CRVENA_PANEL)
        screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + 10))

        # Slotovi za skart karte
        KARTA_W, KARTA_H = 100, 140
        slotovi_x = [x + 60, x + 305]

        for i in range(2):
            x_pos = slotovi_x[i]
            y_pos = y + 40
            slot_rect = pygame.Rect(x_pos, y_pos, KARTA_W, KARTA_H)

            pygame.draw.rect(screen, (200, 200, 200), slot_rect, 2, border_radius=4)

            if i < len(karte_za_skart):
                karta = karte_za_skart[i]
                slika = self.gui.slike_karata_velike.get(karta)
                if slika:
                    screen.blit(slika, slot_rect)
                    pygame.draw.rect(screen, CRVENA_PANEL, slot_rect, 3, border_radius=4)
                self.gui.rects.append((slot_rect, karta, 'skart'))
            else:
                lbl_prazno = FONT_SMALL.render("prazno", True, (150, 150, 150))
                screen.blit(lbl_prazno, (x_pos + KARTA_W//2 - lbl_prazno.get_width()//2, y_pos + KARTA_H//2 - 8))

        # Dugme / info
        btn_y = y + h - 50
        if len(karte_za_skart) == 2:
            self.gui.dugme_potvrdi_skart = UIComponents.nacrtaj_dugme(
                screen, "✓ POTVRDI ŠKART",
                x + w//2 - 120, btn_y, 240, 40, (255, 210, 50))
        else:
            self.gui.dugme_potvrdi_skart = None
            info = FONT_MSG.render("Klikni na kartu iz ruke da je odložiš", True, CRNA)
            screen.blit(info, (SCREEN_W//2 - info.get_width()//2, btn_y + 10))

        # Moje karte dole
        n = len(karte_u_ruci)
        RUKA_W, RUKA_H = 100, 140
        available_w = 480
        if n > 1:
            razmak = min(45, available_w // (n - 1))
        else:
            razmak = 0

        ukupna_sirina = (n - 1) * razmak + RUKA_W
        start_x = SCREEN_W // 2 - ukupna_sirina // 2
        y_ruka = 540

        for i, karta in enumerate(karte_u_ruci):
            slika = self.gui.slike_karata_velike.get(karta) # Slika je već 100x140
            x_k = start_x + i * razmak
            rect = pygame.Rect(x_k, y_ruka, RUKA_W, RUKA_H)

            if slika:
                # Obrisano duplo skaliranje!
                screen.blit(slika, rect)
                pygame.draw.rect(screen, CRNA, rect, 1, border_radius=2)

            self.gui.rects.append((rect, karta, 'ruka'))

    def nacrtaj_izbor_aduta(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x, y, w, h))
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 3)

        naslov = FONT_MSG.render("ODABERI FINALNU IGRU", True, CRNA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, y + 15))

        nivo = self.gui.trenutna_licitacija_broj
        info_txt = FONT_SMALL.render(f"Minimum: {nivo} (moraš igrati to ili jače)", True, (100, 100, 200))
        screen.blit(info_txt, (SCREEN_W//2 - info_txt.get_width()//2, y + 45))

        nivo_na_boje = {
            2: ["Pik", "Karo", "Herc", "Tref", "Betl", "Sans"],
            3: ["Karo", "Herc", "Tref", "Betl", "Sans"],
            4: ["Herc", "Tref", "Betl", "Sans"],
            5: ["Tref", "Betl", "Sans"],
            6: ["Betl", "Sans"],
            7: ["Sans"],
        }
        validne_boje = nivo_na_boje.get(nivo, ["Sans"])

        self.gui.dugmici_licitacije = []
        for i, boja in enumerate(validne_boje):
            boja_dugmeta = (230, 230, 255) if boja in ["Betl", "Sans"] else (230, 230, 230)
            d = UIComponents.nacrtaj_dugme(screen, boja, x + 125, y + 75 + i * 35, 200, 30, boja_dugmeta)
            self.gui.dugmici_licitacije.append((d, boja))

    def nacrtaj_karte_na_stolu(self, screen):
        """Karte na stolu raspoređene prema poziciji igrača (Obrnuti trougao)"""
        import pygame
        
        # Centralni sivi sto
        sto_rect = pygame.Rect(350, 230, 300, 220)
        pygame.draw.rect(screen, TAMNO_ZELENA, sto_rect)
        pygame.draw.rect(screen, CRNA, sto_rect, 2)
        
        # Definisanje pozicija za svakog igrača (relativno u odnosu na sto)
        # ID 0: Ja (dole), ID 1: Bot 1 (desno), ID 2: Bot 2 (levo)
        pozicije = {
            0: (sto_rect.centerx - 35, sto_rect.bottom - 110),
            1: (sto_rect.right - 90, sto_rect.top + 20),
            2: (sto_rect.left + 20, sto_rect.top + 20)
        }

        for p_id, karta in self.gui.karte_na_stolu:
            slika = self.gui.slike_karata.get(karta)
            if slika: 
                pos_x, pos_y = pozicije[p_id]
                rect = pygame.Rect(pos_x, pos_y, 70, 100)
                
                # Crtamo kartu
                screen.blit(slika, rect)
                # Okvir oko karte
                pygame.draw.rect(screen, CRNA, rect, 1, border_radius=3)
                
                # Opciono: Mali tekst iznad karte da se zna čija je
                vlasnik = "Ja" if p_id == 0 else f"B{p_id}"
                oznaka = FONT_SMALL.render(vlasnik, True, BELA)
                screen.blit(oznaka, (pos_x + 20, pos_y - 15))

    def nacrtaj_poruku(self, screen):
        """Poruka na vrhu ekrana"""
        msg = FONT_MSG.render(self.gui.poruka, True, CRNA)
        screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, 10))

    def nacrtaj_gomilice(self, screen):
        """Iscrtava gomilice osvojenih karata relativno u odnosu na ekran i karte"""
        if self.gui.stanje != "IGRA" or not self.gui.poledina: 
            return
            
        mala_poledina = pygame.transform.smoothscale(self.gui.poledina, (35, 50))
        self.gui.gomilice_rects = {}
        

        pozi = {
            2: (220, 150), 
            1: (750, 150), 
            0: (420, 480) 
        }
        
        for pid, pos in pozi.items():
            rect = pygame.Rect(pos[0], pos[1], 35, 50)
            self.gui.gomilice_rects[pid] = rect
            
            # Žuti sjaj za poslednji odnetak (samo ako je neko zaista odneo nešto)
            if self.gui.poslednji_stih_pobednik == pid and len(self.gui.odnete_karte[pid]) > 0:
                pygame.draw.rect(screen, (255, 215, 0), (pos[0]-4, pos[1]-4, 43, 58), 4, border_radius=6)
            
            # Crtamo samu sličicu - SADA UVEK VIDLJIVO
            screen.blit(mala_poledina, pos)
            
            # Tekst sa brojem štihova
            # --- POPRAVLJENO: Dinamički brojimo koliko karata čini jedan štih ---
            aktivni_igraci = [i for i in range(3) if (i == self.gui.pobednik_licitacije) or 
                              (i == 0 and self.gui.moj_izbor_zvanja in ("dodjem", "kontra", None)) or 
                              (i > 0 and self.gui.igraci_koji_dolaze[i-1] is True) or 
                              self.gui.adut == "Betl"]
            broj_aktivnih = len(aktivni_igraci) if len(aktivni_igraci) > 0 else 3
            
            # Sada delimo sa brojem_aktivnih, a ne zakucano sa 3
            broj_stihova = len(self.gui.odnete_karte[pid]) // broj_aktivnih
            txt = FONT_BOLD.render(str(broj_stihova), True, BELA)
            
            # Tamna podloga da se tekst bolje vidi
            pygame.draw.rect(screen, CRNA, (pos[0] + 8, pos[1] + 15, 20, 20), border_radius=3)
            screen.blit(txt, (pos[0] + 13, pos[1] + 16))

    def nacrtaj_pregled_odnetih(self, screen):
        """Polu-providni overlay koji pokazuje detalje šta je ko odneo"""
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.set_alpha(220)
        s.fill((30, 30, 30))
        screen.blit(s, (0,0))
        
        p_id = self.gui.prikaz_odnetih
        karte = self.gui.odnete_karte[p_id]
        
        # LOGIKA PRIKAZA PO PRAVILIMA:
        if p_id == 0:
            # Ti (igrač) uvek vidiš sve svoje odnete karte
            naslov_tekst = "Tvoje odnete karte"
            karte_za_prikaz = karte
            prikazujem_samo_kraj = False
        else:
            # Botove karte vidiš SAMO ako je on odneo apsolutno poslednji štih na stolu
            if self.gui.poslednji_stih_pobednik == p_id and len(karte) > 0:
                naslov_tekst = f"Bot {p_id} - Poslednji odneti štih"
                karte_za_prikaz = karte[-3:]
                prikazujem_samo_kraj = True
            else:
                naslov_tekst = f"Bot {p_id} - Karte su zatvorene (nije nosilac poslednjeg štiha)!"
                karte_za_prikaz = [] # Ne prikazujemo ništa
                prikazujem_samo_kraj = True
                
        naslov = FONT_MSG.render(naslov_tekst, True, BELA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, 50))
        
        start_x = 100
        start_y = 120
        
        # --- POPRAVLJENO I OVDE ---
        aktivni_igraci = [i for i in range(3) if (i == self.gui.pobednik_licitacije) or (i == 0 and self.gui.moj_izbor_zvanja in ("dodjem", "kontra", None)) or (i > 0 and self.gui.igraci_koji_dolaze[i-1] is True) or self.gui.adut == "Betl"]
        broj_aktivnih = len(aktivni_igraci) if len(aktivni_igraci) > 0 else 3
        
        # Crtanje karata koje su dozvoljene za prikaz
        for stih_idx in range(len(karte_za_prikaz) // broj_aktivnih):
            stih = karte_za_prikaz[stih_idx * broj_aktivnih : stih_idx * broj_aktivnih + broj_aktivnih]
            
            if prikazujem_samo_kraj:
                x_offset = SCREEN_W // 2 - 100
                y_offset = 200
                je_poslednji = True
            else:
                x_offset = start_x + (stih_idx % 3) * 260
                y_offset = start_y + (stih_idx // 3) * 130
                je_poslednji = (stih_idx == (len(karte_za_prikaz)//3 - 1)) and (self.gui.poslednji_stih_pobednik == p_id)
            
            if je_poslednji:
                pygame.draw.rect(screen, (255, 215, 0), (x_offset - 10, y_offset - 10, 220, 120), 3, border_radius=10)
            
            for i, k in enumerate(stih):
                slika = self.gui.slike_karata.get(k)
                if slika:
                    rect = pygame.Rect(x_offset + i*70, y_offset, 70, 100)
                    screen.blit(slika, rect)
                    pygame.draw.rect(screen, CRNA, rect, 1, border_radius=3)
        
        zatvori = FONT_SMALL.render("[ Klikni bilo gde za zatvaranje ]", True, ZLATNA)
        screen.blit(zatvori, (SCREEN_W//2 - zatvori.get_width()//2, SCREEN_H - 40))