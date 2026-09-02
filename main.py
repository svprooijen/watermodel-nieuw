import sys
import matplotlib.pyplot as plt
import pandas as pd

from parameters import (
    BassinParameters,
    BassinToestand,
    GebiedToestand,
    Parameters,
    ReservoirParameters,
    ReservoirToestand,
)


def tijdstap(idx: int,
             dt_u: float | int,
             neerslag_mm: float | int,
             params: Parameters,
             gebied_toestanden: list[GebiedToestand]):

    def update_reservoir(reservoir_params: ReservoirParameters,
                         reservoir_toestand: ReservoirToestand) -> float | int:
        neerslag_m = neerslag_mm / 1000.0
        q_in = neerslag_m * reservoir_params.opp / dt_u
        q_uit = reservoir_params.opp * reservoir_params.c * reservoir_toestand.h
        dh_dt = (q_in - q_uit) / reservoir_params.opp
        reservoir_toestand.h += dh_dt * dt_u
        reservoir_toestand.q_in_arr.append(q_in)
        reservoir_toestand.h_arr.append(reservoir_toestand.h)

        reservoir_toestand.q_uit_arr.append(q_uit)
        return q_uit

    def update_bassin(bassin_params: BassinParameters,
                      bassin_toestand: BassinToestand,
                      v_toevoer: float | int) -> float | int:
        v_huidig = bassin_toestand.h * bassin_params.opp
        q_klep = 0.0

        # als rain leveler mogelijk minder toevoer door uitstroom via klep
        if bassin_toestand.is_RL:
            if bassin_toestand.klep_open:
                q_cap = bassin_params.q_klep_max
                q_wens = bassin_toestand.te_lozen / dt_u
                q_mogelijk = (v_huidig + v_toevoer) / dt_u
                q_klep = min(q_cap, q_wens, q_mogelijk)
                if bassin_toestand.te_lozen > 0.0:
                    bassin_toestand.te_lozen = max(0.0, bassin_toestand.te_lozen - q_klep * dt_u)
                if bassin_toestand.te_lozen <= 0.0:
                    bassin_toestand.water_geloosd = True
                    bassin_toestand.klep_open = False

            v_toevoer -= q_klep * dt_u

        v_hat = v_huidig + v_toevoer
        v_max = bassin_params.h_max * bassin_params.opp
        if v_hat <= v_max:
            v_huidig = v_hat
            overflow = 0.0
        else:
            v_huidig = v_max
            overflow = v_hat - v_max
        bassin_toestand.h = v_huidig / bassin_params.opp
        bassin_toestand.h_arr.append(bassin_toestand.h)
        return q_klep + overflow / dt_u

    q_lokaal_per_gebied = [0.0] * params.n_gebieden

    for gebied_id, (gebied_params, toestand) in enumerate(zip(
        params.gebied_params,
        gebied_toestanden,
        strict=True,
    )):
        q_uit_in_gebied = 0.0 # stroomt naar open water binnen eigen gebied
        q_uit_in_gebied += update_reservoir(gebied_params.onverhard_params, toestand.onverhard)

        q_uit_glasNRL = update_reservoir(gebied_params.glasNRL_params, toestand.glasNRL)
        q_uit_glasRL = update_reservoir(gebied_params.glasRL_params, toestand.glasRL)
        overflow_per_u_glasNRL = update_bassin(gebied_params.bassinNRL_params, toestand.bassinNRL, q_uit_glasNRL * dt_u)
        overflow_per_u_glasRL = update_bassin(gebied_params.bassinRL_params, toestand.bassinRL, q_uit_glasRL * dt_u)
        q_uit_in_gebied += overflow_per_u_glasNRL
        q_uit_in_gebied += overflow_per_u_glasRL
        q_uit_in_gebied += (neerslag_mm / 1000.0 * gebied_params.openwater_params.opp / dt_u)
        q_lokaal_per_gebied[gebied_id] = q_uit_in_gebied

    q_van_andere_gebieden = [0.0] * params.n_gebieden
    q_uit_openwater = [0.0] * params.n_gebieden

    for gebied_id, (gebied_params, toestand) in enumerate(zip(
        params.gebied_params,
        gebied_toestanden,
        strict=True,
    )):
        openwater = toestand.openwater
        openwater_opp = gebied_params.openwater_params.opp
        beschikbaar_volume = max(0.0, openwater.h * openwater_opp + q_lokaal_per_gebied[gebied_id] * dt_u)
        verbindingen = params.verbindingen_map[gebied_id]

        # uitstroom naar minstens 1 ander gebied
        if verbindingen:
            # * 3600 want geeft debiet in m^3/s
            kruinhoogte = gebied_params.openwater_params.h_streef
            debieten_per_stuw = [stuw.c * stuw.b * max(openwater.h - kruinhoogte, 0.0) ** 1.5 * 3600.0
                                 for stuw in gebied_params.stuw_params]
            q_stuw_berekend = sum(debieten_per_stuw)
            q_max_beschikbaar = beschikbaar_volume / dt_u
            q_stuw = min(q_stuw_berekend, q_max_beschikbaar)
            schaal = (q_stuw / q_stuw_berekend if q_stuw_berekend > 0.0 else 0.0)

            # voeg uitstroom stuwen toe aan open water andere gebieden
            for (naar, _), debiet_per_stuw in zip(
                verbindingen,
                debieten_per_stuw,
                strict=True,
            ):
                q_van_andere_gebieden[naar] += debiet_per_stuw * schaal

            q_uit_openwater[gebied_id] = q_stuw
        # geen uitstroom; pomp
        else:
            pomp = gebied_params.pomp_params
            beschikbaar_peil = (openwater.h + q_lokaal_per_gebied[gebied_id] * dt_u / openwater_opp)

            # zet status pomp
            if beschikbaar_peil <= pomp.h_uit:
                toestand.pomp_aan = False
            elif beschikbaar_peil >= pomp.h_aan:
                toestand.pomp_aan = True

            q_uit_openwater[gebied_id] = (pomp.q_max if toestand.pomp_aan else 0.0)

    # update open water hoogte en arrays
    for gebied_id, (gebied_params, toestand) in enumerate(zip(
        params.gebied_params,
        gebied_toestanden,
        strict=True,
    )):
        openwater = toestand.openwater
        openwater_opp = gebied_params.openwater_params.opp
        q_in = (q_lokaal_per_gebied[gebied_id] + q_van_andere_gebieden[gebied_id])
        q_uit = q_uit_openwater[gebied_id]
        openwater.h += (q_in - q_uit) * dt_u / openwater_opp
        openwater.q_in_arr.append(q_in)
        openwater.q_uit_arr.append(q_uit)
        openwater.h_arr.append(openwater.h)
        toestand.voeg_waterruimte_toe(gebied_params)


def plot_resultaten(
    tijd_u_arr: list[float],
    neerslag_mm_arr: list[float],
    gebied_toestanden: list[GebiedToestand],
    grafiektype: str,
) -> None:
    fig = plt.figure(figsize=(13, 9))
    raster = fig.add_gridspec(2, 1, height_ratios=(2.2, 1.0), hspace=0.35)
    ax = fig.add_subplot(raster[0])
    ax_ruimte = fig.add_subplot(raster[1])

    if grafiektype == "waterstand":
        waarden_per_gebied = [toestand.openwater.h_arr for toestand in gebied_toestanden]
        y_label = "Waterstand open water (m)"
        titel = "Openwaterstand per gebied"
    elif grafiektype == "afvoer":
        waarden_per_gebied = [toestand.openwater.q_uit_arr for toestand in gebied_toestanden]
        y_label = "Afvoer open water (m³/u)"
        titel = "Openwaterafvoer per gebied"
    else:
        raise ValueError("Grafiektype moet 'waterstand' of 'afvoer' zijn.")

    for gebied_id, waarden in enumerate(waarden_per_gebied):
        ax.plot(tijd_u_arr, waarden, label=f"Gebied {gebied_id}")

    dt_u_arr = [
        tijd_u_arr[idx] - tijd_u_arr[idx - 1]
        for idx in range(1, len(tijd_u_arr))
    ]
    ax_neerslag = ax.twinx()
    ax_neerslag.bar(
        tijd_u_arr[:-1],
        neerslag_mm_arr[1:],
        width=dt_u_arr,
        align="edge",
        alpha=0.2,
        color="tab:blue",
        label="Neerslag",
    )
    ax_neerslag.set_ylabel("Neerslag per tijdstap (mm)")

    ax.set_xlabel("Tijd (uur)")
    ax.set_ylabel(y_label)
    ax.set_title(titel)
    ax.grid(True, alpha=0.3)
    lijnen, lijn_labels = ax.get_legend_handles_labels()
    balken, balk_labels = ax_neerslag.get_legend_handles_labels()
    ax.legend(lijnen + balken, lijn_labels + balk_labels)

    # Iedere balk is altijd 100 mm hoog. De drie soorten beschikbare
    # waterruimte worden gestapeld boven de zwarte overige ruimte.
    gebied_ids = list(range(len(gebied_toestanden)))
    balk_breedte = 0.72
    zwart_balken = ax_ruimte.bar(
        gebied_ids, [100.0] * len(gebied_ids), width=balk_breedte,
        color="black", label="Overig",
    )
    openwater_balken = ax_ruimte.bar(
        gebied_ids, [0.0] * len(gebied_ids), width=balk_breedte,
        color="#1976d2", label="Open water",
    )
    rl_balken = ax_ruimte.bar(
        gebied_ids, [0.0] * len(gebied_ids), width=balk_breedte,
        color="#d9d9d9", edgecolor="#777777", label="RL-bassin",
    )
    nrl_balken = ax_ruimte.bar(
        gebied_ids, [0.0] * len(gebied_ids), width=balk_breedte,
        color="#555555", label="NRL-bassin",
    )
    ax_ruimte.set_ylim(0.0, 100.0)
    ax_ruimte.set_xticks(gebied_ids, [f"Gebied {gebied_id}" for gebied_id in gebied_ids])
    ax_ruimte.set_ylabel("Waterruimte (mm)")
    ax_ruimte.set_title("Beschikbare waterruimte per gebied")
    ax_ruimte.grid(axis="y", alpha=0.25)
    ax_ruimte.legend(ncols=4, loc="upper center", bbox_to_anchor=(0.5, -0.18))

    tijdlijn = ax.axvline(tijd_u_arr[0], color="tab:red", linewidth=2.0, zorder=10)
    tijdtekst = ax.text(
        0.01, 0.98, "", transform=ax.transAxes, va="top", ha="left",
        color="tab:red", bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )

    def werk_waterruimte_bij(tijd_idx: int) -> None:
        for gebied_id, toestand in enumerate(gebied_toestanden):
            nrl_mm, rl_mm, openwater_mm = toestand.waterruimte_matrix[tijd_idx]
            totale_ruimte_mm = nrl_mm + rl_mm + openwater_mm
            overig_mm = max(0.0, 100.0 - totale_ruimte_mm)

            zwart_balken[gebied_id].set_height(overig_mm)
            openwater_balken[gebied_id].set_y(overig_mm)
            openwater_balken[gebied_id].set_height(openwater_mm)
            rl_balken[gebied_id].set_y(overig_mm + openwater_mm)
            rl_balken[gebied_id].set_height(rl_mm)
            nrl_balken[gebied_id].set_y(overig_mm + openwater_mm + rl_mm)
            nrl_balken[gebied_id].set_height(nrl_mm)

        gekozen_tijd_u = tijd_u_arr[tijd_idx]
        tijdlijn.set_xdata([gekozen_tijd_u, gekozen_tijd_u])
        tijdtekst.set_text(f"Tijd: {gekozen_tijd_u:.2f} uur")
        fig.canvas.draw_idle()

    def dichtstbijzijnde_tijd_idx(tijd_u: float) -> int:
        return min(range(len(tijd_u_arr)), key=lambda idx: abs(tijd_u_arr[idx] - tijd_u))

    slepen = {"actief": False}
    interactieve_assen = (ax, ax_neerslag)

    def selecteer_tijd(event) -> None:
        if event.inaxes in interactieve_assen and event.xdata is not None:
            werk_waterruimte_bij(dichtstbijzijnde_tijd_idx(event.xdata))

    def bij_muis_indrukken(event) -> None:
        if event.inaxes in interactieve_assen and event.button == 1:
            slepen["actief"] = True
            selecteer_tijd(event)

    def bij_muis_bewegen(event) -> None:
        if slepen["actief"]:
            selecteer_tijd(event)

    def bij_muis_loslaten(_event) -> None:
        slepen["actief"] = False

    fig.canvas.mpl_connect("button_press_event", bij_muis_indrukken)
    fig.canvas.mpl_connect("motion_notify_event", bij_muis_bewegen)
    fig.canvas.mpl_connect("button_release_event", bij_muis_loslaten)

    werk_waterruimte_bij(0)
    # fig.tight_layout()
    plt.show()


def toon_waterbalans(
    tijd_u_arr: list[float],
    neerslag_mm_arr: list[float],
    params: Parameters,
    gebied_toestanden: list[GebiedToestand],
) -> None:
    componenten = (
        ("onverhard", "onverhard_params"),
        ("glasNRL", "glasNRL_params"),
        ("glasRL", "glasRL_params"),
        ("openwater", "openwater_params"),
        ("bassinNRL", "bassinNRL_params"),
        ("bassinRL", "bassinRL_params"),
    )
    totale_opslagverandering = 0.0

    print("\nWaterbalans")
    print("Opslagverandering per gebied en component:")
    for gebied_id, (gebied_params, toestand) in enumerate(zip(
        params.gebied_params,
        gebied_toestanden,
        strict=True,
    )):
        print(f"  Gebied {gebied_id}:")
        for toestand_naam, params_naam in componenten:
            component_toestand = getattr(toestand, toestand_naam)
            component_params = getattr(gebied_params, params_naam)
            delta_volume = (component_toestand.h_arr[-1] - component_toestand.h_arr[0]) * component_params.opp
            totale_opslagverandering += delta_volume
            print(f"    {toestand_naam:<10} {delta_volume:12.2f} m³")

    totaal_regenoppervlak = sum(
        gebied_params.onverhard_params.opp
        + gebied_params.glasNRL_params.opp
        + gebied_params.glasRL_params.opp
        + gebied_params.openwater_params.opp
        for gebied_params in params.gebied_params
    )
    regenvolume = sum(neerslag_mm_arr[1:]) / 1000.0 * totaal_regenoppervlak

    uitgepompt_volume = 0.0
    for gebied_id, toestand in enumerate(gebied_toestanden):
        if params.verbindingen_map[gebied_id]:
            continue
        uitgepompt_volume += sum(
            toestand.openwater.q_uit_arr[idx]
            * (tijd_u_arr[idx] - tijd_u_arr[idx - 1])
            for idx in range(1, len(tijd_u_arr))
        )

    balans_rechts = totale_opslagverandering + uitgepompt_volume
    balansverschil = regenvolume - balans_rechts
    relatief_verschil = (balansverschil / regenvolume * 100.0 if regenvolume != 0.0 else 0.0)

    print("\nTotalen:")
    print(f"  Regenvolume:             {regenvolume:12.2f} m³")
    print(f"  Opslagverandering:       {totale_opslagverandering:12.2f} m³")
    print(f"  Uitgepompt volume:       {uitgepompt_volume:12.2f} m³")
    print(f"  Opslag + uitgepompt:     {balans_rechts:12.2f} m³")
    print(f"  Balansverschil:          {balansverschil:12.6f} m³")
    print(f"  Relatief verschil:       {relatief_verschil:12.6f} %")


def main():
    if len(sys.argv) < 4:
        print("Gebruik: python3 main.py <gebieden.in> <regen.csv> <grafiektype>")
        sys.exit(1)

    # parameters inlezen
    params: Parameters = Parameters()
    params.lees_in(sys.argv[1])
    print(params)

    # regen inlezen
    regen_bestand: str = sys.argv[2]
    df = pd.read_csv(regen_bestand)
    if "rain_mm" not in df.columns or "time_h" not in df.columns:
        raise ValueError("CSV moet een kolom 'time_h' en 'rain_mm' bevatten.")
    tijd_u_arr = df["time_h"].astype(float).tolist()
    neerslag_mm_arr = df["rain_mm"].astype(float).tolist()

    grafiektype = sys.argv[3].lower()

    gebied_toestanden = [GebiedToestand(gp) for gp in params.gebied_params]
    totale_bui_m = sum(neerslag_mm_arr[1:]) / 1000.0
    loos_deel = 0.30
    bui_start_u = next( # eerste tijdstip met bui
        (tijd_u for tijd_u, neerslag_mm in zip(
                tijd_u_arr[1:],
                neerslag_mm_arr[1:],
                strict=True) if neerslag_mm > 0.0
        ), None
    )
    rainleveler_start_u = (max(0.0, bui_start_u - params.rainleveler_respons) if bui_start_u is not None else None)
    voormalen_start_u = (max(0.0, bui_start_u - params.voormalen_respons) if bui_start_u is not None else None)
    voormalen_uitgevoerd = False

    # te lozen deel via RL is deel van totale neerslag op glasRL
    for gebied_params, toestand in zip(
        params.gebied_params,
        gebied_toestanden,
        strict=True,
    ):
        toestand.bassinRL.te_lozen = (loos_deel * totale_bui_m * gebied_params.glasRL_params.opp)

    # simuleer proces adhv vele tijdstappen
    for idx in range(1, len(tijd_u_arr)):
        dt_u = tijd_u_arr[idx] - tijd_u_arr[idx - 1]

        if dt_u <= 0:
            raise ValueError(f"time_h moet moet strikt stijgen; gaat mis bij rij {idx + 1}")

        interval_start_u = tijd_u_arr[idx - 1]
        if (params.rainleveler_aan and rainleveler_start_u is not None and interval_start_u >= rainleveler_start_u):
            for toestand in gebied_toestanden:
                bassin = toestand.bassinRL
                if not bassin.water_geloosd and bassin.te_lozen > 0.0:
                    bassin.klep_open = True

        if (not voormalen_uitgevoerd and params.voormalen_aan
                and voormalen_start_u is not None and interval_start_u >= voormalen_start_u):
            for gebied_params in params.gebied_params:
                if gebied_params.pomp_params is not None:
                    gebied_params.pomp_params.h_aan -= 0.1
                    gebied_params.pomp_params.h_uit -= 0.1

                if params.voormalen_aan == 2 and gebied_params.stuw_params:
                    gebied_params.openwater_params.h_streef -= 0.1
            voormalen_uitgevoerd = True

        tijdstap(
            idx=idx,
            dt_u=dt_u,
            neerslag_mm=neerslag_mm_arr[idx],
            params=params,
            gebied_toestanden=gebied_toestanden,
        )

    toon_waterbalans(
        tijd_u_arr,
        neerslag_mm_arr,
        params,
        gebied_toestanden,
    )

    plot_resultaten(
        tijd_u_arr,
        neerslag_mm_arr,
        gebied_toestanden,
        grafiektype,
    )


if __name__ == "__main__":
    main()
