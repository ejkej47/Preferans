import random

# KONSTANTE
BOJE = ['Pik', 'Karo', 'Herc', 'Tref']
VREDNOSTI = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
JAČINA_KARTE = {v: i for i, v in enumerate(VREDNOSTI)} # 7=0, A=7

# Vrednosti igara (licitacija)
IGRE_VREDNOST = {
    'Pik': 2, 'Karo': 3, 'Herc': 4, 'Tref': 5, 
    'Betl': 0, 'Sans': 1 # Betl i Sans imaju specifičnu logiku licitacije
}

class GameLogic:
    def __init__(self):
        self.adut = None
        self.prva_karta_na_stolu = None

    @staticmethod
    def ko_nosi_odnetak(karte_na_stolu, adut):
        """
        karte_na_stolu: lista tuplova [(igrac_id, "Karta Boja"), ...]
        Vraća igrac_id koji je odneo krug.
        """
        prvi_igrac, prva_karta = karte_na_stolu[0]
        v_prve, b_prve = prva_karta.split()
        
        pobednik_id = prvi_igrac
        najaca_karta = prva_karta
        
        for i_id, karta in karte_na_stolu[1:]:
            v_trenutna, b_trenutna = karta.split()
            v_najaca, b_najaca = najaca_karta.split()

            # Ako je bačen adut na običnu boju
            if b_trenutna == adut and b_najaca != adut:
                pobednik_id = i_id
                najaca_karta = karta
            # Ako su obe karte u istoj boji (obe adut ili obe prva boja)
            elif b_trenutna == b_najaca:
                if JAČINA_KARTE[v_trenutna] > JAČINA_KARTE[v_najaca]:
                    pobednik_id = i_id
                    najaca_karta = karta
            # Ako je bačena prva boja na aduta - ne nosi (već pokriveno gore)
            
        return pobednik_id

    @staticmethod
    def validni_potezi(ruka, prva_karta_na_stolu, adut):
        """
        Vraća listu karata koje igrač SME da baci po pravilima preferansa.
        """
        if not prva_karta_na_stolu:
            return ruka # Prvi igrač može bilo šta

        v_prve, b_prve = prva_karta_na_stolu.split()
        
        # 1. Mora da odgovori na boju
        na_boju = [k for k in ruka if k.split()[1] == b_prve]
        if na_boju:
            return na_boju
            
        # 2. Ako nema boju, mora da seče adutom
        if adut and adut != 'Sans' and adut != 'Betl':
            na_adut = [k for k in ruka if k.split()[1] == adut]
            if na_adut:
                return na_adut
                
        # 3. Ako nema ni boju ni adut, može bilo šta
        return ruka

    @staticmethod
    def izracunaj_vrednost_igre(nivo, boja):
        """
        Npr. Igra 2 u Hercu vredi 4 poena (u tabeli se piše npr. 40 ili 4)
        """
        if boja == 'Betl': return 6 # Specifično za tabelu
        if boja == 'Sans': return 7
        return IGRE_VREDNOST[boja]
    
class BiddingSession:
    def __init__(self):
        self.aktivni_igraci = [0, 1, 2] 
        self.trenutna_igra = 1 
        self.pobednik = None
        self.refe = False # Novi flag za slučaj kad niko ne igra

    def procesuiraj_odgovor(self, igrac_id, odgovor):
        """
        odgovor može biti: 'dalje', 'igra', 'dva', 2, 3, 'tri'...
        """
        # 1. Ako igrač nije aktivan, ignoriši ga
        if igrac_id not in self.aktivni_igraci:
            return f"Igrač {igrac_id} više nije u licitaciji."

        # 2. Logika za DALJE
        if odgovor == 'dalje':
            self.aktivni_igraci.remove(igrac_id)
            # Ako nema više nikoga, proglasi REFE
            if not self.aktivni_igraci:
                self.refe = True
            return f"Igrač {igrac_id} je rekao DALJE."

        # 3. Logika za podizanje (podržava i reči i brojeve)
        mapa_licitacije = {
            'dva': 2, 'tri': 3, 'četiri': 4, 'pet': 5, 'šest': 6, 'sedam': 7,
            2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7 # Podrška za integer-e iz GUI-a
        }

        if odgovor == 'igra':
            nivo = 2
        else:
            nivo = mapa_licitacije.get(odgovor, 0)

        if nivo > self.trenutna_igra:
            self.trenutna_igra = nivo
            return f"Licitacija na nivou {nivo}."
        
        return "Nevalidna licitacija (broj mora biti veći od trenutnog)."

    def proglasi_pobednika(self):
        """
        Vraća:
        - igrac_id (ako je ostao samo jedan)
        - 'REFE' (ako su svi odustali)
        - None (ako licitacija još traje)
        """
        if self.refe or len(self.aktivni_igraci) == 0:
            return 'REFE'
        
        if len(self.aktivni_igraci) == 1:
            self.pobednik = self.aktivni_igraci[0]
            return self.pobednik
            
        return None
    
class GameSession:
    def __init__(self, igraci, talon):
        self.igraci = igraci  # Lista ruku igrača (liste karata)
        self.talon = talon    # One 2 karte koje niko nije video
        self.skart = []
        self.konacni_adut = None

    def uzmi_talon(self, pobednik_id):
        """Pobednik licitacije spaja talon sa svojim kartama."""
        print(f"Igrač {pobednik_id} uzima talon: {self.talon}")
        self.igraci[pobednik_id].extend(self.talon)
        self.talon = [] # Talon je sada prazan

    def skartiraj_karte(self, pobednik_id, karte_to_discard):
        """
        Igrač bira 2 karte koje izbacuje.
        karte_to_discard: lista od tačno 2 stringa (karte)
        """
        if len(karte_to_discard) != 2:
            return False, "Moraš izbaciti tačno dve karte."
            
        ruka = self.igraci[pobednik_id]
        
        # Provera da li igrač zaista ima te karte u ruci
        for karta in karte_to_discard:
            if karta in ruka:
                ruka.remove(karta)
                self.skart.append(karta)
            else:
                return False, f"Nemaš kartu {karta} u ruci."
        
        return True, "Uspešno skartiranje."

    def proglasi_igru(self, igrac_id, adut_ili_specijal):
        """
        Nakon škarta, igrač kaže šta igra (npr. 'Herc' ili 'Betl').
        """
        self.konacni_adut = adut_ili_specijal
        return f"Igrač {igrac_id} igra: {adut_ili_specijal}"
    

class Engagement:
    def __init__(self, izvodjac_id, igra_tip):
        self.izvodjac_id = izvodjac_id
        self.igra_tip = igra_tip
        self.pratioci = [] # Lista onih koji igraju protiv izvođača
        self.odustali = []

    def odluci_pratnju(self, igrac_id, odluka):
        """
        odluka: 'pratim', 'prolazim'
        """
        if igrac_id == self.izvodjac_id:
            return "Izvođač ne može da prati samog sebe."

        if odluka == 'pratim':
            self.pratioci.append(igrac_id)
            return f"Igrač {igrac_id} PRATI."
        else:
            self.odustali.append(igrac_id)
            return f"Igrač {igrac_id} PROLAZI."

    def proveri_kupovinu(self):
        """
        Ako jedan igrač prođe, a drugi prati, ovaj što prati može da 
        'kupi' ruku drugog igrača (igraju zajedno protiv izvođača).
        """
        if len(self.pratioci) == 1 and len(self.odustali) == 1:
            return f"Igrač {self.pratioci[0]} igra sam protiv izvođača ili kupuje drugog."
        return "Oba igrača prate ili su oba prošla."