import sys
import pandas as pd
from parameters import Parameters

def main():
    if len(sys.argv) < 4:
        print("Gebruik: python3 main.py <gebieden.in> <regen.csv> <grafiektype>")
        sys.exit(1)

    params = Parameters()
    params.lees_in(sys.argv[1])
    print(params)

    regen_bestand = sys.argv[2]
    df = pd.read_csv(regen_bestand)
    if "rain_mm" not in df.columns:
        raise ValueError("CSV moet een kolom 'rain_mm' bevatten.")

if __name__ == "__main__":
    main()