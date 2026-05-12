class Player:
    def __init__(self, id, ime="Igrac"):
        self.id = id
        self.ime = ime
        self.ruka = []
        self.odneti_krugovi = [] # Karte koje je igrac pokupio sa stola

    def primi_karte(self, karte):
        self.ruka = karte
        # Sortiranje karata po boji radi lakšeg snalaženja
        self.ruka.sort(key=lambda x: x.split()[1])

    def izaberi_potez(self, validne_karte):
        """
        Ovo je metoda koju ćeš 'pregaziti' (override) kod bota.
        Za čoveka, ovde ide input().
        """
        print(f"Tvoje karte: {self.ruka}")
        print(f"Dozvoljeni potezi: {validne_karte}")
        
        izbor = input(f"Igrač {self.id}, izaberi kartu: ")
        while izbor not in validne_karte:
            izbor = input("Nevalidna karta, probaj ponovo: ")
        
        self.ruka.remove(izbor)
        return izbor