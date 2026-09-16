from dataclasses import dataclass
import argparse

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.axes import Axes
from matplotlib.patches import FancyArrowPatch, Patch, Rectangle

from parameters import GebiedToestand, Parameters


@dataclass
class Waterbalk:
    overig: Rectangle
    openwater: Rectangle
    bassin_rl: Rectangle
    bassin_nrl: Rectangle


@dataclass
class GebiedsgraafTekening:
    figuur: plt.Figure
    graaf: nx.DiGraph
    posities: dict[int, tuple[float, float]]
    waterbalken: dict[int, Waterbalk]


def maak_gebiedsgraaf(params: Parameters) -> nx.DiGraph:
    graaf = nx.DiGraph()
    for gebied_id, gebied_params in enumerate(params.gebied_params):
        graaf.add_node(
            gebied_id,
            heeft_pomp=gebied_params.pomp_params is not None,
        )

    for van, verbindingen in params.verbindingen_map.items():
        for naar, _stuwbreedte in verbindingen:
            graaf.add_edge(van, naar)

    return graaf


def bepaal_knoopposities(graaf: nx.DiGraph) -> dict[int, tuple[float, float]]:
    if not graaf.nodes:
        return {}

    if nx.is_directed_acyclic_graph(graaf):
        # Deel knopen in op hun grootste afstand tot een benedenstrooms eindpunt.
        # Daardoor staat bijvoorbeeld een gebied dat rechtstreeks naar de pomp
        # stroomt ook daadwerkelijk in de kolom direct voor die pomp.
        afstand_tot_eind: dict[int, int] = {}
        for gebied_id in reversed(list(nx.topological_sort(graaf))):
            opvolgers = list(graaf.successors(gebied_id))
            afstand_tot_eind[gebied_id] = (
                1 + max(afstand_tot_eind[opvolger] for opvolger in opvolgers)
                if opvolgers
                else 0
            )

        grootste_afstand = max(afstand_tot_eind.values())
        generaties: list[list[int]] = [
            sorted(
                gebied_id
                for gebied_id, afstand in afstand_tot_eind.items()
                if grootste_afstand - afstand == generatie_id
            )
            for generatie_id in range(grootste_afstand + 1)
        ]
        ruwe_posities: dict[int, tuple[float, float]] = {}
        for generatie_id, generatie in enumerate(generaties):
            midden = (len(generatie) - 1) / 2
            for rij, gebied_id in enumerate(generatie):
                ruwe_posities[gebied_id] = (float(generatie_id), midden - rij)
    else:
        # Ook bij een kring blijven de posities door de vaste seed reproduceerbaar.
        spring_posities = nx.spring_layout(graaf, seed=42)
        ruwe_posities = {
            gebied_id: (float(x), float(y))
            for gebied_id, (x, y) in spring_posities.items()
        }

    return normaliseer_knoopposities(ruwe_posities)


def normaliseer_knoopposities(
    posities: dict[int, tuple[float, float]],
    marge: float = 0.12,
) -> dict[int, tuple[float, float]]:
    if not 0.0 <= marge < 0.5:
        raise ValueError("marge moet tussen 0 en 0.5 liggen")
    if not posities:
        return {}

    xs = [positie[0] for positie in posities.values()]
    ys = [positie[1] for positie in posities.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    beschikbare_ruimte = 1.0 - 2.0 * marge

    def schaal(waarde: float, minimum: float, maximum: float) -> float:
        if minimum == maximum:
            return 0.5
        return marge + (waarde - minimum) / (maximum - minimum) * beschikbare_ruimte

    return {
        gebied_id: (
            schaal(x, x_min, x_max),
            schaal(y, y_min, y_max),
        )
        for gebied_id, (x, y) in posities.items()
    }


def randpunt_van_box(
    start: tuple[float, float],
    eind: tuple[float, float],
    box_breedte: float,
    box_hoogte: float,
) -> tuple[float, float]:
    dx = eind[0] - start[0]
    dy = eind[1] - start[1]
    if dx == 0.0 and dy == 0.0:
        return start

    schaal_x = box_breedte / 2.0 / abs(dx) if dx != 0.0 else float("inf")
    schaal_y = box_hoogte / 2.0 / abs(dy) if dy != 0.0 else float("inf")
    schaal = min(schaal_x, schaal_y)
    return start[0] + schaal * dx, start[1] + schaal * dy


def teken_gerichte_pijlen(
    ax: Axes,
    graaf: nx.DiGraph,
    posities: dict[int, tuple[float, float]],
    box_breedte: float,
    box_hoogte: float,
) -> None:
    for van, naar in graaf.edges:
        bron_midden = posities[van]
        doel_midden = posities[naar]
        bron_rand = randpunt_van_box(
            bron_midden, doel_midden, box_breedte, box_hoogte
        )
        doel_rand = randpunt_van_box(
            doel_midden, bron_midden, box_breedte, box_hoogte
        )
        pijl = FancyArrowPatch(
            bron_rand,
            doel_rand,
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=20,
            linewidth=1.8,
            color="#555555",
            connectionstyle="arc3,rad=0.04",
            zorder=1,
        )
        ax.add_patch(pijl)


def teken_gebiedsgraaf(
    params: Parameters,
    gebied_toestanden: list[GebiedToestand],
    balkhoogte: float,
    tijd_idx: int = 0,
    ax: Axes | None = None,
) -> GebiedsgraafTekening:
    if balkhoogte <= 0.0:
        raise ValueError("balkhoogte moet groter dan 0 zijn")
    if len(gebied_toestanden) != params.n_gebieden:
        raise ValueError("Voor ieder gebied moet precies één toestand aanwezig zijn")

    if ax is None:
        figuur, ax = plt.subplots(figsize=(13, 8))
    else:
        figuur = ax.figure

    graaf = maak_gebiedsgraaf(params)
    posities = bepaal_knoopposities(graaf)
    knoop_breedte = 0.10
    aantal_per_kolom = {
        x: sum(1 for knoop_x, _ in posities.values() if knoop_x == x)
        for x, _ in posities.values()
    }
    drukste_kolom = max(aantal_per_kolom.values(), default=1)
    knoop_hoogte = min(0.25, 0.76 / drukste_kolom)

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_title("Beschikbare waterruimte en verbindingen per gebied", pad=20)
    ax.axis("off")

    teken_gerichte_pijlen(
        ax,
        graaf,
        posities,
        knoop_breedte,
        knoop_hoogte,
    )

    waterbalken: dict[int, Waterbalk] = {}

    for gebied_id, (x, y) in posities.items():
        knoop_ax = ax.inset_axes(
            [
                x - knoop_breedte / 2,
                y - knoop_hoogte / 2,
                knoop_breedte,
                knoop_hoogte,
            ],
            transform=ax.transAxes,
            zorder=3,
        )
        knoop_ax.set_xlim(-0.6, 0.6)
        knoop_ax.set_ylim(0.0, balkhoogte)
        knoop_ax.set_xticks([])
        knoop_ax.set_yticks([])
        knoop_ax.set_facecolor("white")

        pomp_tekst = " (pomp)" if graaf.nodes[gebied_id]["heeft_pomp"] else ""
        knoop_ax.set_title(f"Gebied {gebied_id}{pomp_tekst}", fontsize=9, pad=3)

        overig = knoop_ax.bar(0, balkhoogte, width=0.72, color="black")[0]
        openwater = knoop_ax.bar(0, 0.0, width=0.72, color="#1976d2")[0]
        bassin_rl = knoop_ax.bar(
            0, 0.0, width=0.72, color="#d9d9d9", edgecolor="#777777"
        )[0]
        bassin_nrl = knoop_ax.bar(0, 0.0, width=0.72, color="#555555")[0]
        waterbalken[gebied_id] = Waterbalk(
            overig=overig,
            openwater=openwater,
            bassin_rl=bassin_rl,
            bassin_nrl=bassin_nrl,
        )

    ax.legend(
        handles=[
            Patch(facecolor="black", label="Overig"),
            Patch(facecolor="#1976d2", label="Open water"),
            Patch(facecolor="#d9d9d9", edgecolor="#777777", label="RL-bassin"),
            Patch(facecolor="#555555", label="NRL-bassin"),
        ],
        ncols=4,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.1),
    )

    tekening = GebiedsgraafTekening(
        figuur=figuur,
        graaf=graaf,
        posities=posities,
        waterbalken=waterbalken,
    )
    werk_waterbalken_bij(tekening, gebied_toestanden, tijd_idx, balkhoogte)
    return tekening


def werk_waterbalken_bij(
    tekening: GebiedsgraafTekening,
    gebied_toestanden: list[GebiedToestand],
    tijd_idx: int,
    balkhoogte: float,
) -> None:
    if balkhoogte <= 0.0:
        raise ValueError("balkhoogte moet groter dan 0 zijn")
    if set(tekening.waterbalken) != set(range(len(gebied_toestanden))):
        raise ValueError("De waterbalken en gebiedstoestanden komen niet overeen")

    for gebied_id, toestand in enumerate(gebied_toestanden):
        try:
            nrl_mm, rl_mm, openwater_mm = toestand.waterruimte_matrix[tijd_idx]
        except IndexError as fout:
            raise IndexError(f"Geen tijdindex {tijd_idx} voor gebied {gebied_id}") from fout

        totale_ruimte_mm = nrl_mm + rl_mm + openwater_mm
        overig_mm = max(0.0, balkhoogte - totale_ruimte_mm)
        balk = tekening.waterbalken[gebied_id]

        balk.overig.set_height(overig_mm)
        balk.openwater.set_y(overig_mm)
        balk.openwater.set_height(openwater_mm)
        balk.bassin_rl.set_y(overig_mm + openwater_mm)
        balk.bassin_rl.set_height(rl_mm)
        balk.bassin_nrl.set_y(overig_mm + openwater_mm + rl_mm)
        balk.bassin_nrl.set_height(nrl_mm)

    tekening.figuur.canvas.draw_idle()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Toon de gebieden, waterberging en gerichte verbindingen."
    )
    parser.add_argument(
        "configuratie",
        nargs="?",
        default="gebieden.yaml",
        help="YAML-bestand met gebiedsparameters (standaard: gebieden.yaml)",
    )
    parser.add_argument(
        "--balkhoogte",
        type=float,
        default=70.0,
        help="Hoogte van iedere waterbalk in mm (standaard: 70)",
    )
    argumenten = parser.parse_args()

    params = Parameters()
    params.lees_in(argumenten.configuratie)
    gebied_toestanden = [
        GebiedToestand(gebied_params)
        for gebied_params in params.gebied_params
    ]

    teken_gebiedsgraaf(
        params=params,
        gebied_toestanden=gebied_toestanden,
        balkhoogte=argumenten.balkhoogte,
    )
    plt.show()


if __name__ == "__main__":
    main()
