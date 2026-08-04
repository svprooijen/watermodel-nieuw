
class Tijdstap:
    def __init__(self, dt_s: float | int):
        self.dt_s = dt_s
        self.dt_m = self.dt_s / 60.0
        self.dt_u = self.dt_m / 60.0

class Reservoir:
    def __init__(self, naam, a, c, h, tijd: Tijdstap):
        self.naam = naam
        self.a = a
        self.c = c
        self.h_init = h # initieel
        self.h = h      # huidig
        self.tijd = tijd

        # Nog onbepaalde arrays
        self.V_in_regen = []    # Volume (m³)
        self.V_in_gebieden = [] # Volume (m³)
        self.V_in_totaal = []   # Volume (m³)
        self.Q_in = []          # Toevoer (m³/u)
        self.Q_in_regen = []    # Toevoer door regen (m³/u)
        self.Q_uit = []         # Afvoer (m³/u)
        self.h_lijst = []       # Hoogte per tijdstap (m)
