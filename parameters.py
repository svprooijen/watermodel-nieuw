import yaml
from typing import List
from copy import deepcopy

class ReservoirParameters:
    def __init__(self):
        self.opp: float | int = 0
        self.c: float | int | None = None
        self.h_init: float | int = 0
    def set_opp(self, opp):
        self.opp = opp
    def set_c(self, c):
        self.c = c
    def set_h_init(self, h_init):
        self.h_init = h_init

    def __str__(self):
        return (
            f"opp={"None" if self.opp is None else f"{self.opp:.0f}"}, "
            f"c={"None" if self.c is None else f"{self.c:.1f}"}, "
            f"h_init={"None" if self.h_init is None else f"{self.h_init:.1f}"}"
        )

class BassinParameters:
    def __init__(self):
        self.opp: float | int = 0
        self.h_init: float | int = 0
        self.h_max: float | int | None = None
        self.q_klep_max: float | int | None = None
    def set_opp(self, opp):
        self.opp = opp
    def set_h_init(self, h_init):
        self.h_init = h_init
    def set_h_max(self, h_max):
        self.h_max = h_max
    def set_q_klep_max(self, q_klep_max):
        self.q_klep_max = q_klep_max

    def __str__(self):
        return (
            f"opp={"None" if self.opp is None else f"{self.opp:.0f}"}, "
            f"h_init={"None" if self.h_init is None else f"{self.h_init:.1f}"}, "
            f"h_max={"None" if self.h_max is None else f"{self.h_max:.1f}"}"
        )

class StuwParameters:
    def __init__(self):
        self.b: float | int = 0 # breedte
        self.c: float | int | None = None
        self.h_kruin: float | int = 0
    def set_b(self, b):
        self.b = b
    def set_c(self, c):
        self.c = c
    def set_h_kruin(self, h_kruin):
        self.h_kruin = h_kruin

    def __str__(self):
        return (
            f"b={"None" if self.b is None else f"{self.b:.1f}"}, "
            f"c={"None" if self.c is None else f"{self.c:.1f}"}, "
            f"h_kruin={"None" if self.h_kruin is None else f"{self.h_kruin:.1f}"}"
        )

class PompParameters:
    def __init__(self):
        self.q_max: float | int | None = None
        self.gemaal_cap: float | int | None = None
        self.h_aan: float | int = 0
        self.h_uit: float | int = 0
    def set_q_max(self, q_max):
        self.q_max = q_max
    def set_gemaal_cap(self, gemaal_cap):
        self.gemaal_cap = gemaal_cap
    def set_h_aan(self, h_aan):
        self.h_aan = h_aan
    def set_h_uit(self, h_uit):
        self.h_uit = h_uit

    def __str__(self):
        return (
            f"q_max={"None" if self.q_max is None else f"{self.q_max:.1f}"}, "
            f"h_aan={"None" if self.h_aan is None else f"{self.h_aan:.2f}"}, "
            f"h_uit={"None" if self.h_uit is None else f"{self.h_uit:.2f}"}"
        )

class GebiedParameters:
    def __init__(self):
        self.onverhard_params: ReservoirParameters = ReservoirParameters()
        self.glasNRL_params: ReservoirParameters = ReservoirParameters()
        self.glasRL_params: ReservoirParameters = ReservoirParameters()
        self.openwater_params: ReservoirParameters = ReservoirParameters()
        self.bassinNRL_params: BassinParameters = BassinParameters()
        self.bassinRL_params: BassinParameters = BassinParameters()
        self.stuw_params: list[StuwParameters] = []
        self.pomp_params: PompParameters | None = None
        self.c_stuw: float | int | None = None

    def stel_stuwen_in(self, stuwen: list[tuple[float | int, float | int]]):
        self.stuw_params = []
        if stuwen:
            self.pomp_params = None
            for breedte, hoogte in stuwen:
                stuw_params = StuwParameters()
                stuw_params.set_b(breedte)
                stuw_params.set_c(self.c_stuw)
                stuw_params.set_h_kruin(hoogte)
                self.stuw_params.append(stuw_params)

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
        pomp_params.set_gemaal_cap(gemaal_cap)


    def converteer_ruw_naar_object(self, gebied_params_raw, opp_tot: float | int):
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
        bassinNRL_params.set_h_init(gebied_params_raw["bassinNRL"]["h_init"])
        bassinNRL_params.set_h_max(gebied_params_raw["bassinNRL"]["h_max"])

        bassinRL_params = BassinParameters()
        bassinRL_params.set_h_init(gebied_params_raw["bassinRL"]["h_init"])
        bassinRL_params.set_h_max(gebied_params_raw["bassinRL"]["h_max"])

        pomp_params = PompParameters()
        pomp_params.set_h_aan(gebied_params_raw["stuw_pomp"]["h_aan_pomp"])
        pomp_params.set_h_uit(gebied_params_raw["stuw_pomp"]["h_uit_pomp"])
        if pomp_params.h_uit >= pomp_params.h_aan:
            raise ValueError("h_uit_pomp moet kleiner dan h_aan_pomp zijn.")

        opp_tot += onverhard_params.opp + glasNRL_params.opp + glasRL_params.opp + openwater_params.opp
        gemaal_cap = gebied_params_raw["stuw_pomp"]["gemaal_cap"]
        self.set_overig(bassinNRL_params,
                        bassinRL_params,
                        glasNRL_params,
                        glasRL_params,
                        pomp_params,
                        opp_tot,
                        gemaal_cap)
        bassinRL_params.set_q_klep_max(gebied_params_raw["bassinRL"]["dh_klep_max"] * bassinRL_params.opp)
        self.onverhard_params = onverhard_params
        self.glasNRL_params = glasNRL_params
        self.glasRL_params = glasRL_params
        self.openwater_params = openwater_params
        self.bassinNRL_params = bassinNRL_params
        self.bassinRL_params = bassinRL_params
        self.pomp_params = pomp_params
        self.c_stuw = gebied_params_raw["stuw_pomp"]["c_stuw"]
        return opp_tot

    def __str__(self):
        regels = [
            f"  onverhard:\t{self.onverhard_params}",
            f"  glas NRL:\t{self.glasNRL_params}",
            f"  glas RL:\t{self.glasRL_params}",
            f"  openwater:\t{self.openwater_params}",
            f"  bassin NRL:\t{self.bassinNRL_params}",
            f"  bassin RL:\t{self.bassinRL_params}",
        ]
        regels.extend(
            f"  stuw {stuw_id}:\t{stuw_params}"
            for stuw_id, stuw_params in enumerate(self.stuw_params)
        )
        if self.pomp_params is not None:
            regels.append(f"  pomp: \t{self.pomp_params}")
        return "\n".join(regels)

class Parameters:
    def __init__(self):
        self.n_gebieden: int = 0
        self.gebied_params: list[GebiedParameters] = []
        self.verbindingen_map: dict[int, list[tuple[int, float | int, float | int]]] = {}
        self.overschrijdingsmarge: float | int | None = None
        self.rainleveler_aan: bool = False
        self.rainleveler_respons: float | int = 0.0
        self.voormalen_aan: int = 0
        self.voormalen_respons: float | int = 0.0

    def lees_in(self, bestandsnaam):
        with open(bestandsnaam) as f:
            config = yaml.safe_load(f)

        # gebied parameters
        gebied_params: List[GebiedParameters] = []
        defaults = config["defaults"]
        opp_tot = 0.0
        for gebied in config["gebieden"]:
            params_raw = deepcopy(defaults)
            for categorie, wijzigingen in gebied.items():
                params_raw[categorie].update(wijzigingen)

            params = GebiedParameters()
            opp_tot = params.converteer_ruw_naar_object(params_raw, opp_tot)
            gebied_params.append(params)

        self.gebied_params = gebied_params
        self.n_gebieden = len(gebied_params)

        # extra
        self.overschrijdingsmarge = config["extra"]["overschrijdingsmarge"]
        self.rainleveler_aan = bool(config["extra"]["rainleveler_aan"])
        self.rainleveler_respons = float(config["extra"]["rainleveler_respons"])
        self.voormalen_aan = int(config["extra"]["voormalen_aan"])
        self.voormalen_respons = float(config["extra"]["voormalen_respons"])
        if self.voormalen_aan not in (0, 1, 2):
            raise ValueError("voormalen_aan moet 0, 1 of 2 zijn")
        if self.rainleveler_respons < 0.0 or self.voormalen_respons < 0.0:
            raise ValueError("rainleveler_respons mag niet negatief zijn")

        # verbindingen tussen gebieden
        verbindingen_map: dict[int, list[tuple[int, float | int, float | int]]] = {
            gebied_id: [] for gebied_id in range(len(gebied_params))
        }
        for verbinding in config["verbindingen"]:
            van = verbinding["van"]
            naar = verbinding["naar"]
            verbindingen_map[van].append((naar, verbinding["b_stuw"], verbinding["h_kruin_stuw"]))
        # zet hoogte en breedte van stuwen in self.stuw_params
        for gebied_id, params in enumerate(gebied_params):
            stuwen = [
                (breedte, kruinhoogte) for _, breedte, kruinhoogte in verbindingen_map[gebied_id]
            ]
            params.stel_stuwen_in(stuwen)
            if params.pomp_params is not None:
                gemaal_cap_m_per_u = params.pomp_params.gemaal_cap / 1000 / 24
                q_max = opp_tot * gemaal_cap_m_per_u
                params.pomp_params.set_q_max(q_max)
        self.verbindingen_map = verbindingen_map

    def __str__(self):
        verbindingen_tekst = "\n\t\t".join(
            f"{van} -> {naar} (stuw_b {stuw.b:.1f}, stuw_h_kruin {stuw.h_kruin:.1f})"
            for van, verbindingen in self.verbindingen_map.items()
            for (naar, _, _), stuw in zip(verbindingen, self.gebied_params[van].stuw_params)
        )

        regels = [
            "",
            "Parameters",
            f"Aantal gebieden: {self.n_gebieden}",
            f"Overschrijdingsmarge: {"None" if self.overschrijdingsmarge is None else f"{self.overschrijdingsmarge:.2f}"}",
            f"Verbindingen:\t{verbindingen_tekst}",
        ]

        for gebied_id, gebied in enumerate(self.gebied_params):
            regels.extend([
                "",
                f"Gebied {gebied_id}:",
                str(gebied),
            ])

        return "\n".join(regels)

class ReservoirToestand:
    def __init__(self, h_init: float | int):
        self.h: float | int = h_init
        self.h_arr: list[float | int] = [self.h]
        self.q_in_arr: list[float | int] = [0.0]
        self.q_uit_arr: list[float | int] = [0.0]

class BassinToestand:
    def __init__(self, h: float | int, is_RL: bool):
        self.h: float | int = h
        self.h_arr: list[float | int] = [self.h]
        self.is_RL: bool = is_RL
        self.klep_open: bool = False
        self.water_geloosd: bool = False
        self.te_lozen: float = 0.0

class GebiedToestand:
    def __init__(self, params: GebiedParameters):
        self.onverhard: ReservoirToestand = ReservoirToestand(params.onverhard_params.h_init)
        self.glasNRL: ReservoirToestand = ReservoirToestand(params.glasNRL_params.h_init)
        self.glasRL: ReservoirToestand = ReservoirToestand(params.glasRL_params.h_init)
        self.openwater: ReservoirToestand = ReservoirToestand(params.openwater_params.h_init)
        self.bassinNRL: BassinToestand = BassinToestand(params.bassinNRL_params.h_init, is_RL=False)
        self.bassinRL: BassinToestand = BassinToestand(params.bassinRL_params.h_init, is_RL=True)
        self.pomp_aan: bool = False
        self.vm_resterend = 0.0
