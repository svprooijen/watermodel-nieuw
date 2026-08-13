import sys
import pandas as pd

from componenten import Reservoir
from parameters import Parameters, GebiedToestand, ReservoirParameters, ReservoirToestand


def tijdstap(idx: int,
             dt_u: float | int,
             neerslag_mm: float | int,
             params: Parameters,
             gebied_toestanden: list[GebiedToestand]):
    def update_reservoir(reservoir_params: ReservoirParameters,
                         reservoir_toestand: ReservoirToestand) -> float | int:
        neerslag_m = neerslag_mm / 1000.0
        q_in = neerslag_m * reservoir_params.opp / dt_u
        dh_dt = q_in / reservoir_params.opp - reservoir_params.c * reservoir_toestand.h
        reservoir_toestand.h += dh_dt * dt_u
        reservoir_toestand.q_in_arr.append(q_in)
        reservoir_toestand.h_arr.append(reservoir_toestand.h)

        q_uit = reservoir_params.opp * reservoir_params.c * reservoir_toestand.h
        reservoir_toestand.q_uit_arr.append(q_uit)
        return q_uit

    for gebied_params, toestand in zip(params.gebied_params, gebied_toestanden):
        q_uit_in_gebied = 0.0 # stroomt naar open water
        q_uit_in_gebied += update_reservoir(gebied_params.onverhard_params, toestand.onverhard)
        q_uit_in_gebied += update_reservoir(gebied_params.glasNRL_params, toestand.glasNRL)
        q_uit_in_gebied += update_reservoir(gebied_params.glasRL_params, toestand.glasRL)

        q_in


def main():
    if len(sys.argv) < 4:
        print("Gebruik: python3 main.py <gebieden.in> <regen.csv> <grafiektype>")
        sys.exit(1)

    params: Parameters = Parameters()
    params.lees_in(sys.argv[1])
    print(params)

    regen_bestand: str = sys.argv[2]
    df = pd.read_csv(regen_bestand)
    if "rain_mm" not in df.columns or "time_h" not in df.columns:
        raise ValueError("CSV moet een kolom 'time_h' en 'rain_mm' bevatten.")

    tijd_u_arr = df["time_h"].astype(float).tolist()
    neerslag_mm_arr = df["rain_mm"].astype(float).tolist()

    gebied_toestanden = [
        GebiedToestand(gp) for gp in params.gebied_params
    ]

    for idx in range(1, len(tijd_u_arr)):
        dt_u = tijd_u_arr[idx] - tijd_u_arr[idx - 1]

        if dt_u <= 0:
            raise ValueError(f"time_h moet moet strikt stijgen; gaat mis bij rij {idx + 1}")

        tijdstap(
            idx=idx,
            dt_u=dt_u,
            neerslag_mm=neerslagneerslag_mm_arr_mm[idx],
            params=params,
            gebied_toestanden=gebied_toestanden,
        )


if __name__ == "__main__":
    main()