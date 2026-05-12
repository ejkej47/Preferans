"""
Logika i rukovanje igrom - licitacija, provere, bot akcije
"""
import pygame
from engine.game_logic import BiddingSession

class GameHandler:
    """Sve logike vezane za igru"""
    
    def __init__(self, gui):
        self.gui = gui
            
    def bot_odluci_licitaciju(self, bot_id):
        if bot_id not in self.gui.licitacija.aktivni_igraci: 
            return
        self.gui.igraci_imali_potez_licitacije.add(bot_id)
        
        broj_asa = sum(1 for k in self.gui.ruke[bot_id] if "A" in k)
        max_limit = 2 + broj_asa 
        
        trenutni = self.gui.trenutna_licitacija_broj
        akcija = self.gui.poslednja_akcija 

        if self.gui.stanje == "FAZA_IZBORA":
            if broj_asa >= 1: 
                msg = "Licitiram 2"
                self.gui.poslednja_akcija = "broj"
                self.gui.trenutna_licitacija_broj = 2
                self.gui.stanje = "FAZA_LICITACIJE"
                # OBAVEZNO: Javi engine-u
                self.gui.licitacija.procesuiraj_odgovor(bot_id, 2)
            else:
                self.gui.licitacija.procesuiraj_odgovor(bot_id, 'dalje')
                msg = "Dalje"
        
        else:
            if trenutni < max_limit or (trenutni == max_limit and akcija == "broj"):
                if akcija == "broj":
                    self.gui.poslednja_akcija = "moje"
                    msg = f"Moje {trenutni}"
                    # Engine ne mora da menja broj, ali zna da je bot i dalje aktivan
                    self.gui.licitacija.procesuiraj_odgovor(bot_id, trenutni)
                else:
                    if akcija == "moje":
                        self.gui.trenutna_licitacija_broj += 1
                    self.gui.poslednja_akcija = "broj"
                    msg = f"Licitiram {self.gui.trenutna_licitacija_broj}"
                    # OBAVEZNO: Javi engine-u novi broj
                    self.gui.licitacija.procesuiraj_odgovor(bot_id, self.gui.trenutna_licitacija_broj)
            else:
                self.gui.licitacija.procesuiraj_odgovor(bot_id, 'dalje')
                msg = "Dalje"
        
        self.gui.bot_poruke[bot_id] = msg
        self.gui.vreme_bot_poruke[bot_id] = pygame.time.get_ticks()
        self.gui.istorija_licitacije.append(f"Bot {bot_id}: {msg}")

    def bot_faza_igra(self, bot_id):
        if bot_id not in self.gui.licitacija.aktivni_igraci:
            return
        
        self.gui.igraci_imali_potez_licitacije.add(bot_id)

        nivoi = {
            "igra": 1,
            "betl": 2,
            "sans": 3,
        }

        trenutni_nivo = self.gui.specijalna_igra_nivo

        asa = sum(1 for k in self.gui.ruke[bot_id] if k.startswith("A "))

        odluka = "dalje"

        if trenutni_nivo < nivoi["igra"]:
            if asa >= 1:
                odluka = "igra"

        elif trenutni_nivo < nivoi["betl"]:
            if asa >= 2:
                odluka = "betl"

        elif trenutni_nivo < nivoi["sans"]:
            if asa >= 3:
                odluka = "sans"

        if odluka == "dalje":
            self.gui.licitacija.procesuiraj_odgovor(bot_id, "dalje")
            self.gui.istorija_licitacije.append(f"Bot {bot_id}: Dalje")
            msg = "Dalje"
        else:
            self.gui.prijavi_specijalnu_igru(bot_id, odluka)
            msg = odluka.capitalize()

        self.gui.bot_poruke[bot_id] = msg
        self.gui.vreme_bot_poruke[bot_id] = pygame.time.get_ticks()


    def bot_faza_najava(self, bot_id):
        """Bot najavljuje igru"""
        if bot_id not in self.gui.licitacija.aktivni_igraci:
            return
            
        trenutni_max = max(self.gui.igra_dekleresi.values()) if self.gui.igra_dekleresi else 0
        broj_asa = sum(1 for k in self.gui.ruke[bot_id] if "A" in k)
        moj_nivo = min(2 + broj_asa, 5)
        
        # Bot prijavljuje igru samo ako je jača od trenutno najjače na stolu
        if moj_nivo > trenutni_max:
            self.gui.igra_dekleresi[bot_id] = moj_nivo
            msg = f"Najavljujem {moj_nivo}"
        else:
            msg = "Dalje (Slabiji sam)"
            
        # Prikaz iznad karata i u istoriji
        self.gui.bot_poruke[bot_id] = msg
        self.gui.vreme_bot_poruke[bot_id] = pygame.time.get_ticks()
        self.gui.istorija_licitacije.append(f"Bot {bot_id}: {msg}")

    def proveri_kraj_licitacije(self, screen):
        """Proveri da li je neko pobedio u licitaciji"""
        aktivni = self.gui.licitacija.aktivni_igraci
        
        if len(aktivni) == 0:
            if self.gui.poslednja_akcija is None:
                # Svi dobijaju po jednu refu
                for i in range(3):
                    self.gui.aktivne_refe[i] += 1
                    
                self.gui.round_history.dodaj_refa_red()
                self.gui.istorija_licitacije.append("REFE - Svi su rekli dalje (novo deljenje)")
                self.reset_licitaciju()
                self.gui.cekaj_bot_akcije = False
            else:
                # Neko je licitirao - poslednji koji je licitirao dobija talon
                # Pronađi ko je poslednji rekao broj iz istorije
                poslednji = None
                for stavka in reversed(self.gui.istorija_licitacije):
                    if "Licitiram" in stavka or "Moje" in stavka:
                        if stavka.startswith("Ja"):
                            poslednji = 0
                        elif stavka.startswith("Bot 1"):
                            poslednji = 1
                        elif stavka.startswith("Bot 2"):
                            poslednji = 2
                        break
                
                if poslednji is not None:
                    self.gui.istorija_licitacije.append(f"{'Ja' if poslednji == 0 else f'Bot {poslednji}'}: Jedini licitant, uzima talon")
                    self.obradi_pobednika_igre(poslednji, None)
                else:
                    self.reset_licitaciju()
                
                self.gui.cekaj_bot_akcije = False
            return
            
        # 2. Ako je ostao samo JEDAN igrač
        if len(aktivni) == 1:
            pobednik_id = aktivni[0]
            ko_pobedio = "Ja" if pobednik_id == 0 else f"Bot {pobednik_id}"
            
            if self.gui.poslednja_akcija is None:
                return
            else:
                self.gui.istorija_licitacije.append(f"{ko_pobedio}: Dobija talon!")
            
            self.obradi_pobednika_igre(pobednik_id, None)
            self.gui.cekaj_bot_akcije = False
            return

        # 3. Fallback na engine logiku
        pob = self.gui.licitacija.proglasi_pobednika()
        if pob is not None:
            if isinstance(pob, str) and not pob.isdigit():
                return 
            igrac_id = int(pob)
            self.obradi_pobednika_igre(igrac_id, None)
            self.gui.cekaj_bot_akcije = False

    def proveri_krug(self, screen, aktivni_igraci=None):
        if aktivni_igraci is None:
            aktivni_igraci = self.aktivni_za_igru()

        broj_aktivnih = len(aktivni_igraci)

        if len(self.gui.karte_na_stolu) == broj_aktivnih:
            pob = self.gui.logika.ko_nosi_odnetak(self.gui.karte_na_stolu, self.gui.adut)

            stih = [k for pid, k in self.gui.karte_na_stolu]
            self.gui.odnete_karte[pob].extend(stih)
            self.gui.poslednji_stih_pobednik = pob
            self.gui.round_history.zabelezi_stih(self.gui.karte_na_stolu, pob)

            if self.gui.adut == "Betl" and pob == self.gui.pobednik_licitacije:
                self.gui.osvezi_ekran(screen)
                pygame.time.delay(300)
                self.gui.karte_na_stolu = []
                self.zavrsi_rundu(screen, aktivni_igraci)
                return

            self.gui.osvezi_ekran(screen)
            pygame.time.delay(100)
            self.gui.karte_na_stolu = []

            if pob in aktivni_igraci:
                self.gui.na_potezu = pob
            else:
                self.gui.na_potezu = self._sledeci_aktivni(pob, aktivni_igraci)

            if self.gui.adut != "Betl":
                nosioac = self.gui.pobednik_licitacije
                pratioci = [pid for pid in aktivni_igraci if pid != nosioac]
                karata_po_stihu = getattr(self.gui, 'broj_karata_po_stihu', broj_aktivnih)

                ukupno_pratioci = sum(
                    len(self.gui.odnete_karte[pid]) // karata_po_stihu
                    for pid in pratioci
                )

                cilj = 5 

                if ukupno_pratioci >= cilj:
                    self.zavrsi_rundu(screen, aktivni_igraci)
                    return

            if all(len(self.gui.ruke[i]) == 0 for i in aktivni_igraci):
                self.zavrsi_rundu(screen, aktivni_igraci)

    def zavrsi_rundu(self, screen, aktivni_igraci):
        """Izračunaj score na kraju runde i prikaži rezultat"""
        
        # --- POPRAVLJENO: Broj karata u štihu zavisi od broja aktivnih igrača ---
        broj_aktivnih = len(aktivni_igraci)
        karata_po_stihu = broj_aktivnih if broj_aktivnih > 0 else 3
        
        stihovi_po_igracu = {}
        for pid in aktivni_igraci:
            karte = self.gui.odnete_karte[pid]
            stihovi_po_igracu[pid] = len(karte) // karata_po_stihu
        
        # Provera i trošenje refe za nosioca
        nosilac = self.gui.pobednik_licitacije
        igra_se_pod_refom = False
        if self.gui.aktivne_refe[nosilac] > 0:
            igra_se_pod_refom = True
            self.gui.aktivne_refe[nosilac] -= 1  # Nosilac troši svoju refu
            
            # Crtanje reckice na odigranoj refi
            self.gui.round_history.oznaci_refu_odigranom(nosilac)
            
            self.gui.istorija_licitacije.append(f"Napomena: Igra se pod REFOM (duplo)!")

        # Pozovi scoring
        rezultat, vrednost = self.gui.scoring.izracunaj_rundu(
            nosioac_id=nosilac,
            adut=self.gui.adut,
            stihovi_po_igracu=stihovi_po_igracu,
            kontra=self.gui.kontra_aktivan,
            refa=igra_se_pod_refom,
            direktna_igra=self.gui.direktna_igra,
            zvanje_tip=self.gui.zvanje_tip,
            zvanje_igrac=self.gui.zvanje_igrac
        )

        self.gui.round_history.zabelezi_score_snapshot(self.gui.scoring)

        self.gui.round_history.zabelezi_rundu(
            nosilac_id=self.gui.pobednik_licitacije,
            adut=self.gui.adut,
            vrednost=vrednost,
            direktna_igra=self.gui.direktna_igra,
            kontra=self.gui.kontra_aktivan,
            zvanje_tip=self.gui.zvanje_tip,
            zvanje_igrac=self.gui.zvanje_igrac,
            stihovi_po_igracu=stihovi_po_igracu,
            rezultat=rezultat,
            pocetne_ruke=self.gui.pocetne_ruke,  
            pocetni_talon=self.gui.pocetni_talon
        )

        # Upiši u istoriju
        for pid, opis in rezultat.items():
            ko = "Ja" if pid == 0 else f"Bot {pid}"
            self.gui.istorija_licitacije.append(f"{ko}: {opis}")
        
        # Provjeri kraj igre
        if self.gui.scoring.proveri_kraj():
            self.gui.poruka = "KRAJ IGRE!"
            self.gui.stanje = "KRAJ"
            return
        
        # Inače reset za novu rundu
        pygame.time.delay(100)
        self.reset_licitaciju()            

    def izvrsi_poteze_do_igraca(self, screen):
        import pygame

        aktivni_igraci = self.aktivni_za_igru()
        broj_aktivnih = len(aktivni_igraci)

        while True:
            if self.gui.stanje != "IGRA":
                break

            if all(len(self.gui.ruke[i]) == 0 for i in aktivni_igraci):
                self.gui.poruka = "Igra je završena!"
                break

            p_id = self.gui.na_potezu

            if p_id not in aktivni_igraci:
                self.gui.na_potezu = self._sledeci_aktivni(p_id, aktivni_igraci)
                continue

            if p_id == 0:
                break

            if len(self.gui.karte_na_stolu) == broj_aktivnih:
                break

            self.gui.osvezi_ekran(screen)
            pygame.time.delay(100)

            if len(self.gui.ruke[p_id]) == 0:
                self.gui.na_potezu = self._sledeci_aktivni(p_id, aktivni_igraci)
                continue

            prva = self.gui.karte_na_stolu[0][1] if self.gui.karte_na_stolu else None
            dozvoljene = self.gui.logika.validni_potezi(self.gui.ruke[p_id], prva, self.gui.adut)

            if not dozvoljene:
                print(f"ERROR: Bot {p_id} nema validnih poteza!")
                break

            k = dozvoljene[0]
            self.gui.ruke[p_id].remove(k)
            self.gui.karte_na_stolu.append((p_id, k))
            self.gui.na_potezu = self._sledeci_aktivni(p_id, aktivni_igraci)

            if len(self.gui.karte_na_stolu) == broj_aktivnih:
                self.proveri_krug(screen, aktivni_igraci)

                if self.gui.stanje != "IGRA":
                    break


    def sledeci_licitant(self):
        """Prebacuje potez na sledećeg aktivnog igrača u licitaciji"""
        aktivni = self.gui.licitacija.aktivni_igraci
        if not aktivni: return
        trenutni = self.gui.na_potezu_licitacija
        
        for i in range(1, 4):
            sledeci = (trenutni + i) % 3
            if sledeci in aktivni:
                self.gui.na_potezu_licitacija = sledeci
                break
    
           
    def _sledeci_aktivni(self, trenutni, aktivni_igraci):
        """Vraća sledećeg aktivnog igrača"""
        n = len(aktivni_igraci)
        idx = aktivni_igraci.index(trenutni) if trenutni in aktivni_igraci else -1
        return aktivni_igraci[(idx + 1) % n]

    def obradi_pobednika_igre(self, igrac_id, tip_igre):
        """Igrac je pobedio - uzima talon i skartira"""
        self.gui.pobednik_licitacije = igrac_id
        
        if tip_igre == "betl":
            self.gui.pobednik_licitacije = igrac_id
            self.gui.adut = "Betl"
            self.gui.moj_izbor_igre = "betl"

            self.gui.kontra_aktivan = False
            self.gui.zvanje_tip = None
            self.gui.zvanje_igrac = None

            self.gui.moj_izbor_zvanja = "dodjem" if igrac_id == 0 else None
            self.gui.igraci_koji_dolaze = [True, True]
            self.gui.botovi_desili_odluku = [True, True]

            self.gui.karte_na_stolu = []
            self.gui.odnete_karte = {0: [], 1: [], 2: []}
            self.gui.poslednji_stih_pobednik = None
            self.gui.round_history.resetuj_trenutnu_rundu()
            self.napravi_krajnji_snapshot()

            self.gui.istorija_licitacije.append("Igra: BETL - svi igraju")
            self.gui.stanje = "IGRA"
            self.gui.poruka = "Igra se BETL!"

            aktivni = [0, 1, 2]
            self.gui.na_potezu = self.prvi_na_potezu(aktivni)

            if self.gui.na_potezu != 0:
                self.izvrsi_poteze_do_igraca(self.gui.screen)

            return

        # 2. Specijalni slučaj: SANS (ima fazu dolaska)
        elif tip_igre == "sans":
            self.gui.pobednik_licitacije = igrac_id
            self.gui.adut = "Sans"
            self.gui.moj_izbor_igre = "sans"
            self.gui.moj_izbor_zvanja = "dodjem" if igrac_id == 0 else None
            self.gui.kontra_aktivan = False
            self.gui.karte_na_stolu = []
            self.gui.odnete_karte = {0: [], 1: [], 2: []}
            self.gui.poslednji_stih_pobednik = None

            self.gui.istorija_licitacije.append("Igra: SANS")
            self.gui.stanje = "FAZA_DOLASKA"
            self.gui.poruka = "Igra se SANS! Boti deklarišu dolazak..."

            self.gui.igraci_koji_dolaze = [None, None]
            self.gui.botovi_desili_odluku = [False, False]
            self.gui.moj_izbor_zvanja = None

            # Ako je bot nosilac, on ne treba sam sebi da se izjašnjava
            if igrac_id in (1, 2):
                self.gui.botovi_desili_odluku[igrac_id - 1] = True

            ko_zove = "Ja" if igrac_id == 0 else f"Bot {igrac_id}"
            self.gui.istorija_dolaska = [f"{ko_zove}: Zove Sans"]
            self.gui.bot_timer = 0
            self.gui.sledeci_bot_dolaska = 1

            return
        
        elif igrac_id == 0:
            # Igrač NE uzima talon u ruku odmah, već on ide direktno u slotove za skart
            self.gui.karte_za_skart = list(self.gui.talon) 
            self.gui.stanje = "SKARTIRANJE"
            self.gui.poruka = "Talon je u skartu. Možeš zameniti karte ili potvrditi."
            self.gui.istorija_licitacije.append("Ja: Uzimam kup")
        else:
            # Bot uzima talon, skartira nasumično i bira aduta (najzastupljenija boja)
            bot_ruka = self.gui.ruke[igrac_id]
            bot_ruka.extend(self.gui.talon)
            skart = bot_ruka[:2]
            self.gui.ruke[igrac_id] = bot_ruka[2:]
            
            self.gui.odbacene_karte = list(skart)  # <-- DODATO (Beležimo šta je bot škartirao)
            
            self.gui.istorija_licitacije.append(f"Bot {igrac_id}: Uzima kup, skartira 2 karte")

            boje_vrednosti = {"Pik": 2, "Karo": 3, "Herc": 4, "Tref": 5}
            minimum = self.gui.trenutna_licitacija_broj  # npr. 3 znači minimum Karo

            # Samo boje koje su >= minimumu licitacije
            dozvoljene_boje = [b for b, v in boje_vrednosti.items() if v >= minimum]

            # Ako nema dozvoljenih (ne bi trebalo), uzmi minimum direktno
            if not dozvoljene_boje:
                dozvoljene_boje = [b for b, v in boje_vrednosti.items() if v == minimum]

            broji = {b: sum(1 for k in self.gui.ruke[igrac_id] if b in k) for b in dozvoljene_boje}
            self.gui.adut = max(broji, key=broji.get)
            self.gui.istorija_licitacije.append(f"Bot {igrac_id}: Adut je {self.gui.adut}")
            
            # Prelaz na fazu pracenja
            self.gui.stanje = "FAZA_DOLASKA"
            self.gui.poruka = "Bot je objavio igru - da li pratiš?"
            self.gui.igraci_koji_dolaze = [None, None]
            self.gui.botovi_desili_odluku = [False, False]
            self.gui.moj_izbor_zvanja = None
            
            # ---> KLJUČNA IZMENA: Pobednik ne mora da se izjašnjava
            self.gui.botovi_desili_odluku[igrac_id - 1] = True 
            
            self.gui.istorija_dolaska = [f"Bot {igrac_id}: Igra {self.gui.adut}"]
            self.gui.bot_timer = 0
            self.gui.pobednik_licitacije = igrac_id
            
            sledeci = (igrac_id + 1) % 3

            if sledeci == 0:
                self.gui.sledeci_bot_dolaska = 3
                self.gui.stanje = "FAZA_ZVANJA"
                self.gui.poruka = "Bot je objavio igru - da li ti pratiš?"
            else:
                self.gui.sledeci_bot_dolaska = sledeci

    def obradi_pobednika_igre_bez_skarta(self, igrac_id):
        """Igrac je pobedio u Igra modu - bez skartiranja"""
        import pygame
        
        self.gui.pobednik_licitacije = igrac_id
        
        if self.gui.moj_izbor_igre == "betl":
            self.gui.adut = "Betl"
            self.gui.istorija_licitacije.append("Igra: BETL - svi igraju automatski")
            # U betlu svi automatski prate - nema faze dolaska
            self.gui.stanje = "IGRA"
            self.gui.poruka = "Igra se BETL! (svi igraju)"
            self.gui.na_potezu = 1
            if self.gui.na_potezu != 0:
                self.izvrsi_poteze_do_igraca(self.gui.screen)
            return
        elif self.gui.moj_izbor_igre == "sans":
            self.gui.adut = "Sans"
            self.gui.istorija_licitacije.append("Igra: SANS")
            
            # Idemo u FAZA_DOLASKA umesto u IGRA
            self.gui.stanje = "FAZA_DOLASKA"
            self.gui.poruka = "Igra se SANS! Boti deklarišu dolazak..."
            self.gui.igraci_koji_dolaze = [None, None]
            self.gui.botovi_desili_odluku = [False, False]
            self.gui.istorija_dolaska = ["Ja: Zovem Sans"]
            self.gui.bot_timer = 0
            self.gui.sledeci_bot_dolaska = 1
            return
        else:
            # Igra bez skarta - adut se bira po najavljenom nivou
            najjaci = max(self.gui.igra_dekleresi.values()) if self.gui.igra_dekleresi else 2
            self.gui.adut = self.nivo_do_boje(najjaci)
            self.gui.istorija_licitacije.append(f"Igra počinje! Adut: {self.gui.adut}")
        
        if igrac_id == 0:
            self.gui.istorija_licitacije.append("Ja: Pobednik (Igra bez skarta)")
            self.gui.na_potezu = 1
        else:
            self.gui.istorija_licitacije.append(f"Bot {igrac_id}: Pobednik (Igra bez skarta)")
            self.gui.na_potezu = igrac_id
        
        self.napravi_krajnji_snapshot()
        
        self.gui.stanje = "IGRA"
        self.gui.poruka = f"Igra: {self.gui.adut}!"
        
        if self.gui.na_potezu != 0:
            self.izvrsi_poteze_do_igraca(self.gui.screen)

    def reset_licitaciju(self):
        """Reset nakon REFE"""
        from engine.game_logic import BiddingSession
        
        self.gui.licitacija = BiddingSession()
        self.gui.trenutna_licitacija_broj = 2
        self.gui.poslednja_akcija = None
        self.gui.moj_izbor_igre = None
        self.gui.moj_izbor_zvanja = None
        self.gui.igra_dekleresi = {}
        self.gui.kontra_aktivan = False
        self.gui.igraci_koji_dolaze = [None, None]
        self.gui.botovi_desili_odluku = [False, False]
        self.gui.istorija_dolaska = []
        self.gui.odnete_karte = {0: [], 1: [], 2: []} 
        self.gui.poslednji_stih_pobednik = None       
        self.gui.stanje = "FAZA_IZBORA"
        self.gui.poruka = "Odaberi igru: Dalje, 2, Igra, Betl, Sans"
        self.gui.istorija_licitacije = []
        self.gui.istorija_scroll = 0
        self.gui.spil.reset_spil()
        self.gui.ruke, self.gui.talon = self.gui.spil.podeli()
        self.gui.pocetne_ruke = [list(r) for r in self.gui.ruke]
        self.gui.pocetni_talon = list(self.gui.talon)
        self.gui.moje_karte = self.gui.ruke[0]
        self.gui.sortiraj_moju_ruku()
        self.gui.prvi_licitant = (self.gui.prvi_licitant + 1) % 3
        self.gui.na_potezu_licitacija = self.gui.prvi_licitant
        self.gui.direktna_igra = False
        self.gui.bot_poruke = {1: "", 2: ""}
        self.gui.igrac_licitirao = False
        self.gui.igrac_imao_prvi_krug_licitacije = False
        self.gui.zvanje_tip = None
        self.gui.zvanje_igrac = None
        self.gui.kontra_red = []
        self.gui.kontra_index = 0
        self.gui.round_history.resetuj_trenutnu_rundu()
        self.gui.specijalna_igra_tip = None
        self.gui.specijalna_igra_igrac = None
        self.gui.specijalna_igra_nivo = 0
        self.gui.igraci_imali_potez_licitacije = set()
        self.gui.odbacene_karte = []

    def nivo_do_boje(self, nivo):
        """Konverzija nivoa (2-7) u naziv boje"""
        mapa = {2: "Pik", 3: "Karo", 4: "Herc", 5: "Tref", 6: "Betl", 7: "Sans"}
        return mapa.get(nivo, "Pik")

    def bot_faza_dolaska(self, bot_id):
        """Bot deklaruje da li dolazi na igru (prati nosioca)"""
        # Pobednik licitacije ne prati sam sebe
        if bot_id == self.gui.pobednik_licitacije:
            self.gui.botovi_desili_odluku[bot_id - 1] = True
            if all(self.gui.botovi_desili_odluku):
                self._prelaz_na_fazu_zvanja()
            return
        
        # Bot procenjuje da li ima dovoljno karata da prati
        # Prati ako ima bar 2 aduta ili 4+ karata u jednoj boji
        adut = self.gui.adut
        karte = self.gui.ruke[bot_id]
        adut_karte = sum(1 for k in karte if adut in k) if adut not in ("Betl", "Sans") else 0
        
        dolazi = adut_karte >= 2 or len(karte) >= 8
        
        self.gui.igraci_koji_dolaze[bot_id - 1] = dolazi
        self.gui.botovi_desili_odluku[bot_id - 1] = True
        
        akcija = "Dodjem" if dolazi else "Ne dodjem"
        self.gui.bot_poruke[bot_id] = akcija  
        self.gui.vreme_bot_poruke[bot_id] = pygame.time.get_ticks()
        self.gui.istorija_dolaska.append(f"Bot {bot_id}: {akcija}")
        self.gui.istorija_licitacije.append(f"Bot {bot_id}: {akcija}")
        
        if all(self.gui.botovi_desili_odluku):
            self._prelaz_na_fazu_zvanja()

    def prvi_za_sans(self, nosilac_id, aktivni_igraci):
        levo_od = {
            0: 2,
            2: 1,
            1: 0,
        }

        kandidat = levo_od[nosilac_id]

        for _ in range(3):
            if kandidat in aktivni_igraci and kandidat != nosilac_id:
                return kandidat
            kandidat = levo_od[kandidat]

        return nosilac_id
    

    def _prelaz_na_fazu_zvanja(self):
        g = self.gui

        if g.pobednik_licitacije == 0:
            pratioci = self.pratioci_ids()
            dosli = [pid for pid in pratioci if g.igraci_koji_dolaze[pid - 1] is True]
            nisu = [pid for pid in pratioci if g.igraci_koji_dolaze[pid - 1] is False]

            if len(dosli) == 2:
                self.zapocni_kontra_fazu()
                return

            if len(dosli) == 1 and len(nisu) == 1:
                pid = dosli[0]
                odluka = self.bot_odluci_zvanje(pid)

                if odluka in ("kontra", "zovem"):
                    self.aktiviraj_zvanje(odluka, pid)
                    return

                self.start_igre()
                return

            if len(dosli) == 0:
                g.istorija_licitacije.append("Niko ne prati - nova igra")
                self.reset_licitaciju()
                return

            self.start_igre()
            return

        if g.moj_izbor_zvanja in ("dodjem", "ne_dodjem", "kontra"):
            svi_odlucili = all(
                g.botovi_desili_odluku[pid - 1]
                for pid in (1, 2)
                if pid != g.pobednik_licitacije
            )

            if not svi_odlucili:
                return

            bots_come = any(
                x is True and (i + 1) != g.pobednik_licitacije
                for i, x in enumerate(g.igraci_koji_dolaze)
            )

            if g.moj_izbor_zvanja == "ne_dodjem":
                if not bots_come:
                    g.istorija_licitacije.append("Niko ne prati - nova igra")
                    self.reset_licitaciju()
                    return

                self.start_igre()
                return

            if g.moj_izbor_zvanja in ("dodjem", "kontra"):
                if bots_come:
                    self.zapocni_kontra_fazu()
                    return

                self.start_igre()
                return

        g.stanje = "FAZA_ZVANJA"

        bots_come = sum(
            1 for i, x in enumerate(g.igraci_koji_dolaze)
            if x and (i + 1) != g.pobednik_licitacije
        )

        if bots_come == 0:
            g.poruka = "Niko ne prati - da li ti pratiš?"
        else:
            g.poruka = f"{bots_come} bot(a) prati - da li ti pratiš?"

    def bot_faza_najava(self, bot_id):
        """Bot deklaruje nivo u Igri"""
        if bot_id not in self.gui.licitacija.aktivni_igraci:
            return
        
        asa = sum(1 for k in self.gui.ruke[bot_id] if "A" in k)
        nivo = min(2 + asa, 5)
        
        # Nivo mora biti >= izlicitiranom minimumu
        minimum = self.gui.trenutna_licitacija_broj
        if nivo < minimum:
            nivo = minimum  # Pokušaj igrati na minimumu ako možeš
        
        trenutni_max = max(self.gui.igra_dekleresi.values()) if self.gui.igra_dekleresi else 0
        if nivo > trenutni_max:
            self.gui.igra_dekleresi[bot_id] = nivo
            self.gui.bot_poruke[bot_id] = f"Najavljujem {nivo}"
            self.gui.vreme_bot_poruke[bot_id] = pygame.time.get_ticks()
            self.gui.istorija_licitacije.append(f"Bot {bot_id}: Najavljujem {nivo}")
        else:
            self.gui.bot_poruke[bot_id] = "Slabiji sam"
            self.gui.vreme_bot_poruke[bot_id] = pygame.time.get_ticks()
            self.gui.istorija_licitacije.append(f"Bot {bot_id}: Slabiji sam, dalje")

    def prvi_na_potezu(self, aktivni_igraci):
        """Ko prvi igra - kreće od prvi_licitant u smeru 0->1->2->0"""
        pocetak = self.gui.prvi_licitant
        for i in range(3):
            kandidat = (pocetak + i) % 3
            if kandidat in aktivni_igraci:
                return kandidat
        return aktivni_igraci[0]
    
    def pratioci_ids(self):
        return [pid for pid in range(3) if pid != self.gui.pobednik_licitacije]


    def forsiraj_sve_pratioce(self):
        for pid in self.pratioci_ids():
            if pid == 0:
                self.gui.moj_izbor_zvanja = "dodjem"
            else:
                self.gui.igraci_koji_dolaze[pid - 1] = True


    def aktivni_za_igru(self):
        if self.gui.adut == "Betl":
            return [0, 1, 2]

        if self.gui.zvanje_tip in ("kontra", "zovem"):
            return sorted([self.gui.pobednik_licitacije] + self.pratioci_ids())

        aktivni = [self.gui.pobednik_licitacije]

        if self.gui.moj_izbor_zvanja in ("dodjem", "kontra"):
            aktivni.append(0)

        for pid in (1, 2):
            if self.gui.igraci_koji_dolaze[pid - 1] is True:
                aktivni.append(pid)

        return sorted(set(aktivni))


    def start_igre(self):
        g = self.gui
        aktivni = self.aktivni_za_igru()

        g.round_history.resetuj_trenutnu_rundu()
        self.napravi_krajnji_snapshot()

        g.stanje = "IGRA"

        if g.adut == "Sans" and hasattr(self, "prvi_za_sans"):
            g.na_potezu = self.prvi_za_sans(g.pobednik_licitacije, aktivni)
        else:
            g.na_potezu = self.prvi_na_potezu(aktivni)

        if g.na_potezu != 0:
            self.izvrsi_poteze_do_igraca(g.screen)


    def zapocni_kontra_fazu(self):
        g = self.gui
        pratioci = self.pratioci_ids()

        # OVO JE PROMENJENO: Redosled pitanja za kontru sada kreće od onog levo od nosioca
        nosilac = g.pobednik_licitacije
        prvi = (nosilac + 1) % 3
        if prvi not in pratioci:
            prvi = (prvi + 1) % 3
        drugi = [pid for pid in pratioci if pid != prvi][0]

        g.kontra_red = [prvi, drugi]
        g.kontra_index = 0
        g.stanje = "FAZA_KONTRE"
        g.poruka = "Oba igrača prate - može ili kontra?"

        self.nastavi_kontra_fazu()


    def nastavi_kontra_fazu(self):
        g = self.gui

        while g.kontra_index < len(g.kontra_red):
            pid = g.kontra_red[g.kontra_index]

            if pid == 0:
                g.stanje = "FAZA_KONTRE"
                return

            odluka = self.bot_odluci_kontru(pid)

            if odluka == "kontra":
                self.aktiviraj_zvanje("kontra", pid)
                return

            g.istorija_dolaska.append(f"Bot {pid}: Može")
            g.istorija_licitacije.append(f"Bot {pid}: Može")
            g.kontra_index += 1

        self.start_igre()


    def bot_odluci_kontru(self, bot_id):
        asa = sum(1 for k in self.gui.ruke[bot_id] if k.startswith("A "))
        return "kontra" if asa >= 2 else "moze"


    def aktiviraj_zvanje(self, tip, igrac_id):
        g = self.gui

        g.zvanje_tip = tip
        g.zvanje_igrac = igrac_id
        g.kontra_aktivan = tip == "kontra"

        self.forsiraj_sve_pratioce()

        ime = "Ja" if igrac_id == 0 else f"Bot {igrac_id}"
        tekst = "Kontra" if tip == "kontra" else "Zovem"

        g.istorija_dolaska.append(f"{ime}: {tekst}")
        g.istorija_licitacije.append(f"{ime}: {tekst}")
        g.poruka = f"{tekst}! Igra se {g.adut}!"

        self.start_igre()

    def pusti_preostalog_bota_ako_treba(self):
        g = self.gui

        if g.pobednik_licitacije == 0:
            return False

        preostali_botovi = [
            pid for pid in (1, 2)
            if pid != g.pobednik_licitacije
        ]

        if not preostali_botovi:
            return False

        bot_id = preostali_botovi[0]

        if g.botovi_desili_odluku[bot_id - 1] is False:
            g.stanje = "FAZA_DOLASKA"
            g.sledeci_bot_dolaska = bot_id
            g.bot_timer = 0
            g.poruka = f"Čeka se Bot {bot_id}..."
            return True

        return False
    
    def obradi_igraca_pratilac(self, akcija):
        g = self.gui

        if akcija == "ne_dodjem":
            g.moj_izbor_zvanja = "ne_dodjem"
            g.istorija_dolaska.append("Ja: Ne dodjem")
            g.istorija_licitacije.append("Ja: Ne pratim")

            if self.pusti_preostalog_bota_ako_treba():
                return

            neko_prati = any(x is True for x in g.igraci_koji_dolaze)

            if not neko_prati:
                g.istorija_licitacije.append("Niko ne prati - nova igra")
                self.reset_licitaciju()
                return

            self.start_igre()
            return

        if akcija == "dodjem":
            g.moj_izbor_zvanja = "dodjem"
            g.istorija_dolaska.append("Ja: Dodjem")
            g.istorija_licitacije.append("Ja: Pratim")

            if self.pusti_preostalog_bota_ako_treba():
                return

            pratioci = self.pratioci_ids()
            drugi = [pid for pid in pratioci if pid != 0][0]

            if g.igraci_koji_dolaze[drugi - 1] is True:
                self.zapocni_kontra_fazu()
                return

            self.start_igre()
            return

        if akcija == "zovem":
            g.moj_izbor_zvanja = "dodjem"
            self.aktiviraj_zvanje("zovem", 0)
            return

        if akcija == "kontra":
            g.moj_izbor_zvanja = "kontra"
            self.aktiviraj_zvanje("kontra", 0)
            return
        
    def napravi_krajnji_snapshot(self):
        """Beleži pravo stanje karata u rukama igrača NAKON škartiranja"""
        g = self.gui
        g.pocetne_ruke = [list(r) for r in g.ruke]
        
        if hasattr(g, 'odbacene_karte') and g.odbacene_karte:
            g.pocetni_talon = list(g.odbacene_karte)
        else:
            g.pocetni_talon = list(g.talon)