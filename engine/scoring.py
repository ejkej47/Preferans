VREDNOSTI_IGRE = {
    "Pik": 4, "Karo": 6, "Herc": 8, "Tref": 10, "Betl": 12, "Sans": 14
}

class ScoringTable:
    def __init__(self, pocetna_bula=60):
        self.bula = {0: pocetna_bula, 1: pocetna_bula, 2: pocetna_bula}
        # supe[x][y] = x piše supu prema y (x je pratilac, y je nosioac)
        self.supe = {
            0: {1: 0, 2: 0},
            1: {0: 0, 2: 0},
            2: {0: 0, 1: 0},
        }

    def izracunaj_rundu(self, nosioac_id, adut, stihovi_po_igracu,
                    kontra=False, refa=False, direktna_igra=False,
                    zvanje_tip=None, zvanje_igrac=None):
        vrednost = VREDNOSTI_IGRE.get(adut, 4)

        if direktna_igra:
            vrednost += 2

        multiplikator = 1
        if kontra:
            multiplikator *= 2
        if refa:
            multiplikator *= 2

        vrednost_final = vrednost * multiplikator

        rezultat = {}
        nosioac_stihovi = stihovi_po_igracu.get(nosioac_id, 0)
        pratioci = [pid for pid in stihovi_po_igracu if pid != nosioac_id]
        ukupno_pratioci = sum(stihovi_po_igracu[p] for p in pratioci)

        if adut == "Betl":
            betl_prosao = nosioac_stihovi == 0

            if zvanje_tip == "kontra" and zvanje_igrac is not None:
                if betl_prosao:
                    self.bula[nosioac_id] -= vrednost_final
                    rezultat[nosioac_id] = (
                        f"Prošao Betl pod kontrom (0 štihova), "
                        f"bula -{vrednost_final}"
                    )

                    self.bula[zvanje_igrac] += vrednost_final
                    rezultat[zvanje_igrac] = (
                        f"Pao na kontru Betl, "
                        f"bula +{vrednost_final}"
                    )

                    for pid in pratioci:
                        if pid != zvanje_igrac:
                            rezultat[pid] = "Igrao uz kontru Betl"

                else:
                    self.bula[nosioac_id] += vrednost_final
                    rezultat[nosioac_id] = (
                        f"Pao Betl pod kontrom ({nosioac_stihovi} štihova), "
                        f"bula +{vrednost_final}"
                    )

                    supa = vrednost_final * 5
                    self.supe[zvanje_igrac][nosioac_id] += supa
                    rezultat[zvanje_igrac] = (
                        f"Oborio Betl kontrom, "
                        f"supa +{supa}"
                    )

                    for pid in pratioci:
                        if pid != zvanje_igrac:
                            rezultat[pid] = "Igrao uz kontru Betl"

                return rezultat, vrednost_final

            if betl_prosao:
                self.bula[nosioac_id] -= vrednost_final
                rezultat[nosioac_id] = (
                    f"Prošao Betl (0 štihova), "
                    f"bula -{vrednost_final}"
                )

                for pid in pratioci:
                    rezultat[pid] = "Nije oborio Betl"

            else:
                self.bula[nosioac_id] += vrednost_final
                rezultat[nosioac_id] = (
                    f"Pao Betl ({nosioac_stihovi} štihova), "
                    f"bula +{vrednost_final}"
                )

                for pid in pratioci:
                    supa = vrednost_final * 5
                    self.supe[pid][nosioac_id] += supa
                    rezultat[pid] = f"Oborio Betl, supa +{supa}"

            return rezultat, vrednost_final

        if nosioac_stihovi >= 6:
            self.bula[nosioac_id] -= vrednost_final
            rezultat[nosioac_id] = f"Prošao ({nosioac_stihovi} štihova), bula -{vrednost_final}"
        else:
            self.bula[nosioac_id] += vrednost_final
            rezultat[nosioac_id] = f"Pao ({nosioac_stihovi} štihova), bula +{vrednost_final}"

        if zvanje_tip in ("kontra", "zovem") and zvanje_igrac is not None:
            cilj = 5 if zvanje_tip == "kontra" else 4
            supa = vrednost_final * ukupno_pratioci

            self.supe[zvanje_igrac][nosioac_id] += supa

            if ukupno_pratioci < cilj:
                self.bula[zvanje_igrac] += vrednost_final
                rezultat[zvanje_igrac] = (
                    f"Pao na {zvanje_tip} ({ukupno_pratioci} štihova), "
                    f"bula +{vrednost_final}, supa +{supa}"
                )
            else:
                rezultat[zvanje_igrac] = (
                    f"Prošao {zvanje_tip} ({ukupno_pratioci} štihova), "
                    f"supa +{supa}"
                )

            for pid in pratioci:
                if pid != zvanje_igrac:
                    rezultat[pid] = f"Igrao uz {zvanje_tip}"

            return rezultat, vrednost_final

        for pid in pratioci:
            stihovi = stihovi_po_igracu[pid]
            supa = vrednost_final * stihovi
            self.supe[pid][nosioac_id] += supa

            if len(pratioci) == 1:
                pao = stihovi < 2
            else:
                pao = ukupno_pratioci < 4 and stihovi < 2

            if pao:
                self.bula[pid] += vrednost_final
                rezultat[pid] = (
                    f"Pao ({stihovi} štihova), "
                    f"bula +{vrednost_final}, supa +{supa}"
                )
            else:
                rezultat[pid] = f"Prošao ({stihovi} štihova), supa +{supa}"

        return rezultat, vrednost_final

    def proveri_kraj(self):
        """Kraj kad zbir svih bula = 0"""
        return sum(self.bula.values()) == 0

    def get_stanje(self):
        return {
            "bula": self.bula,
            "supe": self.supe
        }