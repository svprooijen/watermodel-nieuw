import sys

from parameters import Parameters


def main():
    if len(sys.argv) < 3:
        print("Gebruik: python3 main.py <gebieden.in> <grafiektype>")
        sys.exit(1)

    params = Parameters()
    params.lees_in(sys.argv[1])
    print(params)

if __name__ == "__main__":
    main()