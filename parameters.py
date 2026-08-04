import yaml
from typing import List
from copy import deepcopy

class ReservoirParameters:
    def __init__(self):
        self.opp = -1
        self.c = -1
        self.h_init = -1
    def set_opp(self, opp):
        self.opp = opp
    def set_c(self, c):
        self.c = c
    def set_h_init(self, h_init):
        self.h_init = h_init

class BassinParameters:
    def __init__(self):
        self.opp = -1
        self.h_cur = -1
        self.h_max = -1
    def set_opp(self, opp):
        self.opp = opp
    def set_h_cur(self, h_cur):
        self.h_cur = h_cur
    def set_h_max(self, h_max):
        self.h_max = h_max

class StuwParameters:
    def __init__(self):
        self.b = -1 # breedte
        self.c = -1
        self.h_kruin = -1
    def set_b(self, b):
        self.b = b
    def set_c(self, c):
        self.c = c
    def set_h_kruin(self, h_kruin):
        self.h_kruin = h_kruin

class PompParameters:
    def __init__(self):
        self.q_max = -1
        self.h_aan = -1
        self.h_uit = -1
    def set_q_max(self, q_max):
        self.q_max = q_max
    def set_h_aan(self, h_aan):
        self.h_aan = h_aan
    def set_h_uit(self, h_uit):
        self.h_uit = h_uit

class GebiedParameters:
    def __init__(self):
        self.onverhard_params: ReservoirParameters | None = None
        self.glasNRL_params: ReservoirParameters | None = None
        self.glasRL_params: ReservoirParameters | None = None
        self.openwater_params: ReservoirParameters | None = None
        self.bassinNRL_params: BassinParameters | None = None
        self.bassinRL_params: BassinParameters | None = None
        self.stuw_params: StuwParameters | None = None
        self.pomp_params: PompParameters | None = None
        self.met_pomp: bool | None = None

    def set_overig(self, bassinNRL_params: BassinParameters,
                         bassinRL_params: BassinParameters,
                         glasNRL_params: ReservoirParameters,
                         glasRL_params: ReservoirParameters,
                         pomp_params: PompParameters,
                         opp_tot: float | int,
                         gemaal_cap: float | int):
        bassinNRL_grootte = 1000 # Aantal m^3 bassin per hectare -> gem. hoogte in mm/10
        bassinRL_grootte = 1000
        bassinNRL_opp = bassinNRL_grootte * glasNRL_params.opp / bassinNRL_params.h_max / 10000
        bassinRL_opp = bassinRL_grootte * glasRL_params.opp / bassinRL_params.h_max / 10000
        bassinNRL_params.set_opp(bassinNRL_opp)
        bassinRL_params.set_opp(bassinRL_opp)

        gemaal_cap_m_per_u = gemaal_cap / 1000 / 24
        q_max = opp_tot * gemaal_cap_m_per_u
        pomp_params.set_q_max(q_max)

    def convert_raw_to_object(self, gebied_params_raw):
        onverhard_params = ReservoirParameters()
        onverhard_params.set_opp(gebied_params_raw["onverhard"]["opp"])
        onverhard_params.set_c(gebied_params_raw["onverhard"]["c"])
        onverhard_params.set_h_init(gebied_params_raw["onverhard"]["h_init"])

        glasNRL_params = ReservoirParameters()
        glasNRL_params.set_opp(gebied_params_raw["glasNRL"]["opp"])
        glasNRL_params.set_c(gebied_params_raw["glasNRL"]["c"])
        glasNRL_params.set_h_init(gebied_params_raw["glasNRL"]["h_init"])

        glasRL_params = ReservoirParameters()
        glasRL_params.set_opp(gebied_params_raw["glasRL"]["opp"])
        glasRL_params.set_c(gebied_params_raw["glasRL"]["c"])
        glasRL_params.set_h_init(gebied_params_raw["glasRL"]["h_init"])

        openwater_params = ReservoirParameters()
        openwater_params.set_opp(gebied_params_raw["openwater"]["opp"])
        openwater_params.set_h_init(gebied_params_raw["openwater"]["h_init"])

        bassinNRL_params = BassinParameters()
        bassinNRL_params.set_h_cur(gebied_params_raw["bassinNRL"]["h_cur"])
        bassinNRL_params.set_h_max(gebied_params_raw["bassinNRL"]["h_max"])

        bassinRL_params = BassinParameters()
        bassinRL_params.set_h_cur(gebied_params_raw["bassinRL"]["h_cur"])
        bassinRL_params.set_h_max(gebied_params_raw["bassinRL"]["h_max"])

        stuw_params = StuwParameters()
        stuw_params.set_b(gebied_params_raw["stuw_pomp"]["b_stuw"])
        stuw_params.set_c(gebied_params_raw["stuw_pomp"]["c_stuw"])
        stuw_params.set_h_kruin(gebied_params_raw["stuw_pomp"]["h_kruin_stuw"])

        pomp_params = PompParameters()
        pomp_params.set_h_aan(gebied_params_raw["stuw_pomp"]["h_aan_pomp"])
        pomp_params.set_h_uit(gebied_params_raw["stuw_pomp"]["h_uit_pomp"])

        gemaal_cap = gebied_params_raw["stuw_pomp"]["gemaal_cap"]
        opp_tot = onverhard_params.opp + glasNRL_params.opp + glasRL_params.opp + openwater_params.opp
        self.set_overig(bassinNRL_params,
                        bassinRL_params,
                        glasNRL_params,
                        glasRL_params,
                        pomp_params,
                        opp_tot,
                        gemaal_cap)

        self.onverhard_params = onverhard_params
        self.glasNRL_params = glasNRL_params
        self.glasRL_params = glasRL_params
        self.openwater_params = openwater_params
        self.bassinNRL_params = bassinNRL_params
        self.bassinRL_params = bassinRL_params
        self.stuw_params = stuw_params
        self.pomp_params = pomp_params
        self.met_pomp = bool(gebied_params_raw["stuw_pomp"]["met_pomp"])


class Parameters:
    def __init__(self):
        self.n_gebieden: int = 0
        self.gebied_params: list[GebiedParameters] | None = None
        self.verbindingen_map: dict[int, list[tuple[int, float | int]]] | None = None
        self.overschrijdingsmarge: float | int | None = None

    def lees_in(self, bestandsnaam):
        with open(bestandsnaam) as f:
            config = yaml.safe_load(f)

        # gebied parameters
        gebied_params: List[GebiedParameters] = []
        defaults = config["defaults"]
        for gebied in config["gebieden"]:
            params_raw = deepcopy(defaults)
            for categorie, wijzigingen in gebied.items():
                params_raw[categorie].update(wijzigingen)

            params = GebiedParameters()
            params.convert_raw_to_object(params_raw)
            gebied_params.append(params)
        self.gebied_params = gebied_params
        self.n_gebieden = len(gebied_params)

        # extra
        self.overschrijdingsmarge = config["extra"]["overschrijdingsmarge"]

        # verbindingen tussen gebieden
        verbindingen_map: dict[int, list[tuple[int, float | int]]] = {
            gebied_id: [] for gebied_id in range(len(gebied_params))
        }
        for van, naar, weging in config["verbindingen"]:
            verbindingen_map[van].append((naar, weging))
        # normaliseer
        for van, verbindingen in verbindingen_map.items():
            tot = sum(w for _,w in verbindingen)
            if tot <= 0 and verbindingen:
                raise ValueError(f"De totale weging vanuit gebied {van} is <= 0.")
            verbindingen_map[van] = [(naar, w / tot) for naar, w in verbindingen]
        self.verbindingen_map = verbindingen_map
        print(verbindingen_map)
