from operator import pos

import pygame
import sys
import os

# POPRAVKA PUTANJE
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.deck import Deck
from engine.game_logic import GameLogic, BiddingSession
from engine.scoring import ScoringTable
from ui.constants import *
from ui.components import UIComponents
from ui.game_handler import GameHandler
from ui.display_handler import DisplayHandler
from ui.round_history import RoundHistory

class PreferansGUI:
    def __init__(self):
        self.spil = Deck()
        self.logika = GameLogic()
        self.licitacija = BiddingSession()
        self.istorija_scroll = 0  # Trenutni pomeraj skrola
        self.scoring = ScoringTable(60)
        self.round_history = RoundHistory()
        self.round_history.zabelezi_score_snapshot(self.scoring)

        self.ruke, self.talon = self.spil.podeli()
        self.pocetne_ruke = [list(r) for r in self.ruke]
        self.pocetni_talon = list(self.talon)
        self.stanje = "FAZA_IZBORA"
        self.pod_faza = None
        
        self.adut = None
        self.na_potezu = 0 
        self.moje_karte = self.ruke[0]
        self.karte_na_stolu = []
        self.skart_izabrane = [] 
        
        self.istorija_licitacije = [] 
        self.istorija_rezultata = [("0", "100", "0")]
        
        self.trenutna_licitacija_broj = 2 
        self.poslednja_akcija = None
        self.moj_izbor_igre = None
        self.igra_dekleresi = {}
        self.pobednik_licitacije = None
        self.direktna_igra = False
        self.igrac_licitirao = False
        self.igrac_imao_prvi_krug_licitacije = False
        self.aktivne_refe = {0: 0, 1: 0, 2: 0}
        
        # Dolazak i zvanje
        self.igraci_koji_dolaze = [None, None]  # [bot1, bot2] - True/False
        self.moj_izbor_zvanja = None  # "dodjem", "ne_dodjem", "kontra"
        self.botovi_desili_odluku = [False, False]  # Da li su oba bota odlučila?
        self.istorija_dolaska = []  # Posebna istorija za dolazak i zvanja
        self.kontra_aktivan = False  # Da li je kontra data u ovoj partiji
        self.zvanje_tip = None
        self.zvanje_igrac = None
        self.kontra_red = []
        self.kontra_index = 0
        
        # Bot timer - za sporo deklarovanje bota
        self.bot_timer = 0
        self.sledeci_bot_dolaska = 1
        self.bot_licitacija_timer = 0  # Timer za bot akcije u licitaciji
        self.sledeci_bot_za_akciju = 1  # Koji bot je sledeći za akciju
        self.cekaj_bot_akcije = False  # Flag da li broj čekamo bot akcije u licitaciji
        self.bot_poruke = {1: "", 2: ""}  # Poruke koje prikazujemo iznad botova
        self.vreme_bot_poruke = {1: 0, 2: 0}

        # Skartiranje - talon kartice i odbačene kartice
        self.karte_za_skart = []  
        self.odbacene_karte = []  # Odbačene kartice nakon potvrde skarta
        
        self.poruka = "Odaberi igru: Dalje, 2, Igra, Betl, Sans"
        
        self.slike_karata = {}
        self.slike_karata_velike = {}
        self.poledina = None
        
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.ucitaj_slike()
        self.sortiraj_moju_ruku()
        
        self.dugmici_licitacije = []
        self.dugmici_aduta = []
        self.dugme_potvrdi_skart = None
        self.talon_rects = []  # Pravougaonici za talon kartice tokom skarting faze
        self.ruka_rects = []   # Pravougaonici za moje kartice tokom skarting faze
        
        # Praćenje odnetih karata i hovera
        self.odnete_karte = {0: [], 1: [], 2: []}
        self.poslednji_stih_pobednik = None
        self.prikaz_odnetih = None  # Ako nije None, prikazuje overlay za taj ID
        self.mis_pozicija = (0, 0)
        self.gomilice_rects = {}
        self.prvi_licitant = 0  # Ko prvi licitira, rotira se svaku rundu
        self.na_potezu_licitacija = 0
        self.specijalna_igra_tip = None
        self.specijalna_igra_igrac = None
        self.specijalna_igra_nivo = 0
        self.igraci_imali_potez_licitacije = set()
        

        # Inicijalizuj handler-e
        self.game_handler = GameHandler(self)
        self.display_handler = DisplayHandler(self)
        self.rects = []

    def sortiraj_moju_ruku(self):
        red_boja = {'Pik': 0, 'Karo': 1, 'Tref': 2, 'Herc': 3}
        red_vrednosti = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, '10': 4, '9': 5, '8': 6, '7': 7}
        self.moje_karte.sort(key=lambda x: (red_boja[x.split()[1]], red_vrednosti[x.split()[0]]))

    def ucitaj_slike(self):
        # Putanje do tvoja dva foldera sa pripremljenim PNG-ovima
        path_male = os.path.join("ui", "assets", "Karte", "Male")
        path_velike = os.path.join("ui", "assets", "Karte", "Velike")
        
        # 1. Učitavanje poleđine (koristi tvoj novi "2B.png")
        try:
            self.poledina = pygame.image.load(os.path.join(path_male, "2B.png")).convert_alpha()
            self.poledina_velika = pygame.image.load(os.path.join(path_velike, "2B.png")).convert_alpha()
        except Exception as e: 
            print(f"GREŠKA pri učitavanju poleđine (2B.png): {e}")

        # 2. Učitavanje svih karata iz špila
        for karta in self.spil.karte:
            v, b = karta.split()
            
            # Mapiranje prema tvojim novim imenima fajlova sa slike
            # Boje: Clubs (C), Diamonds (D), Hearts (H), Spades (S)
            boje_map = {'Herc': 'H', 'Karo': 'D', 'Pik': 'S', 'Tref': 'C'}
            
            # Vrednosti: 10 je 'T', ostalo je isto (A, K, Q, J, 9, 8, 7)
            vred_map = {
                '7': '7', '8': '8', '9': '9', '10': 'T', 
                'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
            }
            
            # NOVI FORMAT IMENA: npr. '7C.png', 'TS.png', 'AH.png'
            ime = f"{vred_map[v]}{boje_map[b]}.png"
            
            try:
                # Učitavamo direktno - slike su već 70x100 i 100x140 iz eksporta
                img_mala = pygame.image.load(os.path.join(path_male, ime)).convert_alpha()
                img_velika = pygame.image.load(os.path.join(path_velike, ime)).convert_alpha()
                
                self.slike_karata[karta] = img_mala
                self.slike_karata_velike[karta] = img_velika
            except Exception as e: 
                print(f"GREŠKA pri učitavanju slike '{ime}' za kartu {karta}: {e}")
                self.slike_karata[karta] = None

    def osvezi_ekran(self, screen):
        """Delegiraj na display handler"""
        self.display_handler.osvezi_ekran(screen)

    def loop(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60)  # Održava 60 FPS
            
            # 1. BOT TIMER - FAZA DOLASKA (Da li botovi prate igru)
            if self.stanje == "FAZA_DOLASKA" and self.sledeci_bot_dolaska <= 2:
                self.bot_timer += dt
                if self.bot_timer > 100:  # 1 sekunda pauze između odluka botova
                    # Provjeravamo da li bot uopšte treba da odlučuje (možda je on nosilac)
                    if not self.botovi_desili_odluku[self.sledeci_bot_dolaska - 1]:
                        self.game_handler.bot_faza_dolaska(self.sledeci_bot_dolaska)
                    
                    self.bot_timer = 0
                    self.sledeci_bot_dolaska += 1
                    # Preskoči na sledećeg bota ako je ovaj već "obrađen"
                    while (self.sledeci_bot_dolaska <= 2 and 
                           self.botovi_desili_odluku[self.sledeci_bot_dolaska - 1]):
                        self.sledeci_bot_dolaska += 1

            # 2. BOT TIMER - KRUŽNA LICITACIJA (Faza izbora i licitacije)
            if self.stanje in ["FAZA_IZBORA", "FAZA_LICITACIJE"]:
                # Ako NIJE moj red (na_potezu_licitacija je 1 ili 2), bot igra
                if self.na_potezu_licitacija != 0:
                    self.bot_licitacija_timer += dt
                    if self.bot_licitacija_timer > 100:  # 0.8 sekundi delay za prirodniji osjećaj
                        bot_id = self.na_potezu_licitacija
                        
                        # Samo ako je bot još uvijek aktivan u licitaciji
                        if bot_id in self.licitacija.aktivni_igraci:
                            self.game_handler.bot_odluci_licitaciju(bot_id)
                            self.game_handler.proveri_kraj_licitacije(self.screen)
                        
                        # Ako licitacija još traje, prebaci na sledećeg
                        if self.stanje in ["FAZA_IZBORA", "FAZA_LICITACIJE"]:
                            self.game_handler.sledeci_licitant()
                            
                        self.bot_licitacija_timer = 0
                
                # Ako sam ja ispao (rekao DALJE), a botovi još licitiraju
                elif 0 not in self.licitacija.aktivni_igraci:
                    # Samo proslijedi red sledećem botu
                    self.game_handler.sledeci_licitant()

            if self.stanje == "FAZA_IGRA":
                if self.na_potezu_licitacija != 0:
                    self.bot_licitacija_timer += dt

                    if self.bot_licitacija_timer > 100:
                        bot_id = self.na_potezu_licitacija

                        if bot_id in self.licitacija.aktivni_igraci:
                            self.game_handler.bot_faza_igra(bot_id)

                        if self.stanje == "FAZA_IGRA":
                            if self.svi_ostali_vec_imali_potez(bot_id):
                                self.zavrsi_specijalnu_licitaciju()
                            else:
                                self.game_handler.sledeci_licitant()

                                if self.na_potezu_licitacija == 0:
                                    self.zavrsi_specijalnu_licitaciju()

                        self.bot_licitacija_timer = 0

            # OSVEŽAVANJE EKRANA
            self.mis_pozicija = pygame.mouse.get_pos()
            self.osvezi_ekran(self.screen)

            # EVENT HANDLING
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    pygame.quit()
                    sys.exit()

                # Scroll istorije licitacije mišem
                if event.type == pygame.MOUSEWHEEL:
                    mis = pygame.mouse.get_pos()
                    istorija_rect = pygame.Rect(10, 10, 180, 350)
                    if istorija_rect.collidepoint(mis):
                        ukupna_visina = len(self.istorija_licitacije) * 22
                        vidljiva_visina = 310
                        if ukupna_visina > vidljiva_visina:
                            self.istorija_scroll += event.y * 20
                            max_scroll = -(ukupna_visina - vidljiva_visina)
                            self.istorija_scroll = max(max_scroll, min(0, self.istorija_scroll))

                # Klikovi mišem
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self._handle_click(pos)

    def _handle_click(self, pos):
        if self.round_history.handle_click(pos):
            return
        
        if self.stanje in ["FAZA_IZBORA", "FAZA_LICITACIJE"] and self.na_potezu_licitacija != 0:
            print("Sačekaj, botovi su na potezu...")
            return
        
        # Ako je otvoren pregled odnetih karata, klik bilo gde ga zatvara
        if self.prikaz_odnetih is not None:
            self.prikaz_odnetih = None
            return
            
        # Provera da li je kliknuto na nečiju gomilicu odnetih karata
        for pid, rect in self.gomilice_rects.items():
            if rect.collidepoint(pos):
                self.prikaz_odnetih = pid
                return
                
        trenutni_dugmici = list(self.dugmici_licitacije)
        #print(f"Trenutni dugmići: {trenutni_dugmici}")  # Debug: Prikaz trenutnih dugmića
        gh = self.game_handler
        print(self.stanje)  # Debug: Prikaz trenutnog stanja
        if self.stanje == "FAZA_IZBORA":
            self._handle_faza_izbora(pos, gh)
        elif self.stanje == "FAZA_LICITACIJE":
            self._handle_faza_licitacije(pos, gh)
        elif self.stanje == "FAZA_IGRA":
            self._handle_faza_igra(pos, gh)
        elif self.stanje == "FAZA_DOLASKA":
            self._handle_faza_dolaska(pos, gh)
        elif self.stanje == "FAZA_ZVANJA":
            self._handle_faza_zvanja(pos, gh)
        elif self.stanje == "FAZA_KONTRE":
            self._handle_faza_kontre(pos, gh)
        elif self.stanje == "FAZA_NAJAVA":
            self._handle_faza_najava(pos, gh)
        elif self.stanje == "SKARTIRANJE":
            self._handle_skartiranje(pos, gh)
        elif self.stanje == "IZBOR_ADUTA":
            self._handle_izbor_aduta(pos, gh)
        elif self.stanje == "IGRA" and self.na_potezu == 0:
            self._handle_igra(pos, gh)

    def _handle_faza_izbora(self, pos, gh):
        # Kopiramo dugmiće i odmah praznimo originalnu listu zbog bezbednosti
        za_proveru = list(self.dugmici_licitacije)
        self.dugmici_licitacije = []

        for d, akcija in za_proveru:
            if d.collidepoint(pos):
                self.igrac_imao_prvi_krug_licitacije = True
                self.igraci_imali_potez_licitacije.add(0)
                if akcija == "dalje":
                    self.licitacija.procesuiraj_odgovor(0, 'dalje')
                    self.istorija_licitacije.append("Ja: Dalje")
                    
                    # Proveravamo odmah da li je ovo bio zadnji "dalje"
                    if len(self.licitacija.aktivni_igraci) <= 1:
                        gh.proveri_kraj_licitacije(self.screen)
                        return
                        
                    self.stanje = "FAZA_LICITACIJE" # Boti preuzimaju
                    gh.sledeci_licitant()
                    return

                elif akcija == "dva":
                    self.trenutna_licitacija_broj = 2
                    self.poslednja_akcija = "broj"
                    self.istorija_licitacije.append("Ja: Licitiram 2")
                    self.stanje = "FAZA_LICITACIJE"
                    gh.sledeci_licitant()
                    return

                elif akcija in ("igra", "betl", "sans"):
                    self.igrac_licitirao = True
                    self.prijavi_specijalnu_igru(0, akcija)

                    if self.svi_ostali_vec_imali_potez(0):
                        self.zavrsi_specijalnu_licitaciju()
                        return

                    gh.sledeci_licitant()
                    return

    def _handle_faza_licitacije(self, pos, gh):
        """Upravlja klikovima tokom licitacije"""
        for d, akcija in self.dugmici_licitacije:
            if d.collidepoint(pos):
                self.dugmici_licitacije = []
                self.igrac_imao_prvi_krug_licitacije = True
                self.igraci_imali_potez_licitacije.add(0)


                # --- SPECIJALNE IGRE (Igra, Betl, Sans) ---
                if akcija in ("igra", "betl", "sans"):
                    self.igrac_licitirao = True
                    self.prijavi_specijalnu_igru(0, akcija)

                    if self.svi_ostali_vec_imali_potez(0):
                        self.zavrsi_specijalnu_licitaciju()
                        return

                    gh.sledeci_licitant()
                    return

                # --- LICITACIJA BROJEVIMA ---
                elif akcija == "moje":
                    
                    if self.poslednja_akcija == "broj":
                        self.poslednja_akcija = "moje"
                        self.istorija_licitacije.append(f"Ja: Moje {self.trenutna_licitacija_broj}")
                        self.licitacija.procesuiraj_odgovor(0, self.trenutna_licitacija_broj)
                    else:
                        self.trenutna_licitacija_broj += 1
                        self.poslednja_akcija = "broj"
                        self.istorija_licitacije.append(f"Ja: Licitiram {self.trenutna_licitacija_broj}")
                        self.licitacija.procesuiraj_odgovor(0, self.trenutna_licitacija_broj)
                    
                    self.bot_licitacija_timer = 0
                    gh.sledeci_licitant() 
                    return
                    
                # --- ODUSTAJANJE ---
                elif akcija == "dalje":
                    self.licitacija.procesuiraj_odgovor(0, 'dalje')
                    self.istorija_licitacije.append("Ja: Dalje")
                    
                    # Elegantnije: prepuštamo glavnoj funkciji da sredi i REFE i dodelu talona
                    if len(self.licitacija.aktivni_igraci) <= 1:
                        gh.proveri_kraj_licitacije(self.screen)
                        return
                    
                    self.bot_licitacija_timer = 0
                    gh.sledeci_licitant()
                    return

    def _handle_faza_igra(self, pos, gh):
        for d, akcija in self.dugmici_licitacije:
            if d.collidepoint(pos):
                if akcija == "dalje":
                    self.igraci_imali_potez_licitacije.add(0)
                    self.licitacija.procesuiraj_odgovor(0, "dalje")
                    self.istorija_licitacije.append("Ja: Dalje")

                    gh.sledeci_licitant()

                    if self.na_potezu_licitacija == 0:
                        self.zavrsi_specijalnu_licitaciju()

                    return

                mapa = {
                    "igra_igra": "igra",
                    "igra_betl": "betl",
                    "igra_sans": "sans",
                }

                if akcija in mapa:
                    tip = mapa[akcija]

                    if self.prijavi_specijalnu_igru(0, tip):
                        gh.sledeci_licitant()

                        if self.na_potezu_licitacija == 0:
                            self.zavrsi_specijalnu_licitaciju()

                    return

    def _handle_faza_dolaska(self, pos, gh):
        """Boti deklarišu da li dolaze na igru"""
        for d, akcija in self.dugmici_licitacije:
            if d.collidepoint(pos):
                if akcija == "bot_dolazi":
                    # Bot je već deklarisao u bot_faza_dolaska
                    pass

    def _handle_faza_zvanja(self, pos, gh):
        for d, akcija in self.dugmici_licitacije:
            if d.collidepoint(pos):
                self.bot_timer = 0
                self.sledeci_bot_dolaska = 3

                if akcija in ("dodjem", "ne_dodjem", "kontra", "zovem"):
                    gh.obradi_igraca_pratilac(akcija)

                return

    def prijavi_specijalnu_igru(self, igrac_id, tip):
        nivoi = {
            "igra": 1,
            "betl": 2,
            "sans": 3,
        }

        novi_nivo = nivoi[tip]

        if novi_nivo <= self.specijalna_igra_nivo:
            return False

        self.direktna_igra = True
        self.moj_izbor_igre = tip
        self.moj_izbor_zvanja = "dodjem" if igrac_id == 0 else self.moj_izbor_zvanja

        self.specijalna_igra_tip = tip
        self.specijalna_igra_igrac = igrac_id
        self.specijalna_igra_nivo = novi_nivo

        ime = "Ja" if igrac_id == 0 else f"Bot {igrac_id}"
        self.istorija_licitacije.append(f"{ime}: {tip.capitalize()}")

        self.stanje = "FAZA_IGRA"

        if tip == "igra":
            self.poruka = "Igra je prijavljena - može Betl ili Sans"
        elif tip == "betl":
            self.poruka = "Betl je prijavljen - može samo Sans"
        elif tip == "sans":
            self.poruka = "Sans je prijavljen - najjača igra"

        return True
    
    def zavrsi_specijalnu_licitaciju(self):
        tip = self.specijalna_igra_tip
        igrac = self.specijalna_igra_igrac

        if tip is None or igrac is None:
            self.game_handler.reset_licitaciju()
            return

        self.pobednik_licitacije = igrac

        if tip == "igra":
            if igrac == 0:
                self.stanje = "FAZA_NAJAVA"
                self.poruka = "Izaberi koju igru igraš"
                self.dugmici_licitacije = []
            else:
                self.game_handler.obradi_pobednika_igre_bez_skarta(igrac)

        elif tip == "betl":
            self.moj_izbor_igre = "betl"
            self.game_handler.obradi_pobednika_igre(igrac, "betl")

        elif tip == "sans":
            self.moj_izbor_igre = "sans"
            self.game_handler.obradi_pobednika_igre(igrac, "sans")

    def _handle_faza_kontre(self, pos, gh):
        for d, akcija in self.dugmici_licitacije:
            if d.collidepoint(pos):
                if akcija == "kontra":
                    gh.aktiviraj_zvanje("kontra", 0)
                    return

                if akcija == "moze":
                    self.istorija_dolaska.append("Ja: Može")
                    self.istorija_licitacije.append("Ja: Može")
                    self.kontra_index += 1
                    gh.nastavi_kontra_fazu()
                    return

    def _handle_faza_najava(self, pos, gh):
        for d, akcija in self.dugmici_licitacije:
            if d.collidepoint(pos):
                if akcija.startswith("najava_"):
                    nivo = int(akcija.split("_")[1])
                    self.igra_dekleresi[0] = nivo
                    self.istorija_licitacije.append(f"Ja: Najavljujem {nivo}")
                    
                    # Boti najavljuju svoje nivoe
                    gh.bot_faza_najava(1)
                    gh.bot_faza_najava(2)
                    
                    # Određujemo ko je dao najjaču najavu
                    pobednik = max(self.igra_dekleresi.keys(), key=lambda k: self.igra_dekleresi[k])
                    najjaci_nivo = self.igra_dekleresi[pobednik]
                    
                    # Određujemo aduta prema najjačoj najavi
                    self.adut = gh.nivo_do_boje(najjaci_nivo)
                    self.pobednik_licitacije = pobednik
                    
                    # Zapisujemo ko nosi igru iz ruke
                    ko_nosi = "Ja" if pobednik == 0 else f"Bot {pobednik}"
                    self.istorija_licitacije.append(f"{ko_nosi}: Nosi igru iz ruke ({self.adut})")
                    
                    # NEMA ŠKARTIRANJA KAD SE ZOVE "IGRA"!
                    # Idemo direktno u fazu gde se ostali izjašnjavaju da li prate
                    self.stanje = "FAZA_DOLASKA"
                    self.poruka = f"Igra se {self.adut} iz ruke! Boti deklarišu dolazak..."
                    
                    # Inicijalizacija za fazu dolaska
                    self.igraci_koji_dolaze = [None, None]
                    self.botovi_desili_odluku = [False, False]
                    self.istorija_dolaska = [f"{ko_nosi}: Nosi ({self.adut})"]
                    
                    self.bot_timer = 0
                    self.sledeci_bot_dolaska = 1
                    
                    self.dugmici_licitacije = []
                    return

    def _handle_skartiranje(self, pos, gh):
        # 1. Dugme potvrdi
        if self.dugme_potvrdi_skart and self.dugme_potvrdi_skart.collidepoint(pos):
            if len(self.karte_za_skart) == 2:
                self.odbacene_karte = list(self.karte_za_skart)
                self.istorija_licitacije.append(f"Ja: Skartirao {self.odbacene_karte}")
                
                self.karte_za_skart = []
                self.sortiraj_moju_ruku()
                
                # KLJUČNA IZMENA: Posle skarta uvek ideš na IZBOR_ADUTA
                self.stanje = "IZBOR_ADUTA"
                self.poruka = "Izaberi boju za igru (aduta)"
                self.dugmici_licitacije = []
                return

        # 2. Klik na karte (Pomeranje između ruke i skarta)
        for rect, karta, tip in reversed(self.rects):
            if rect.collidepoint(pos):
                if tip == 'skart':
                    # Izbaci iz skarta, vrati u ruku
                    self.karte_za_skart.remove(karta)
                    self.moje_karte.append(karta)
                    self.sortiraj_moju_ruku()
                elif tip == 'ruka':
                    # Izbaci iz ruke, prebaci u skart (samo ako ima mesta)
                    if len(self.karte_za_skart) < 2:
                        if karta in self.moje_karte:
                            self.moje_karte.remove(karta)
                            self.karte_za_skart.append(karta)
                break
    
    def _handle_izbor_aduta(self, pos, gh):
        """Rukovanje izborom aduta nakon skarting faze"""
        for d, boja in self.dugmici_licitacije:
            if d.collidepoint(pos):
                self.adut = boja
                self.istorija_licitacije.append(f"Ja: Igram {boja}")
                
                # Umešta direktnog prelaska u igru, pokrećemo fazu dolaska za botove
                self.stanje = "FAZA_DOLASKA"
                self.poruka = "Boti deklarišu dolazak..."
                self.igraci_koji_dolaze = [None, None]
                self.botovi_desili_odluku = [False, False]
                self.istorija_dolaska = [f"Ja: Igra {self.adut}"]
                self.bot_timer = 0
                self.sledeci_bot_dolaska = 1
                self.pobednik_licitacije = 0 # Postavljamo tebe kao nosioca igre
                
                self.dugmici_licitacije = []
                break

    def _handle_igra(self, pos, gh):
        if 0 not in gh.aktivni_za_igru():
            return

        for rect, karta in reversed(self.rects):
            if rect.collidepoint(pos):
                prva = self.karte_na_stolu[0][1] if self.karte_na_stolu else None

                if karta in self.logika.validni_potezi(self.moje_karte, prva, self.adut):
                    self.moje_karte.remove(karta)
                    self.karte_na_stolu.append((0, karta))

                    aktivni = gh.aktivni_za_igru()

                    if len(self.karte_na_stolu) < len(aktivni):
                        self.na_potezu = gh._sledeci_aktivni(0, aktivni)
                        gh.izvrsi_poteze_do_igraca(self.screen)
                    else:
                        gh.proveri_krug(self.screen, aktivni)

                        if self.na_potezu != 0:
                            gh.izvrsi_poteze_do_igraca(self.screen)

                break

    def svi_ostali_vec_imali_potez(self, igrac_id):
        ostali = [pid for pid in range(3) if pid != igrac_id]
        return all(pid in self.igraci_imali_potez_licitacije for pid in ostali) 

if __name__ == "__main__":
    PreferansGUI().loop()