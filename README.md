## watermodel-nieuw

Voer eenmalig uit:

```
uv sync
```
Om daarna te runnen:
```
uv run python3 main.py <gebieden.in> <regen.csv> <grafiektype>
```

Gebruik voor `<grafiektype>`:

- `waterstand` voor de openwaterstand van ieder gebied;
- `afvoer` voor de openwaterafvoer van ieder gebied.

In beide grafieken wordt de neerslag op een tweede y-as getoond. Na de
simulatie wordt in de terminal ook de waterbalans afgedrukt.

### Parameters

Zie alle beschikbare parameters onder ```default:```. Deze bepalen de standaardinstellingen van elk toegevoegd gebied.
Vervolgens staan gebieds-onafhankelijke instellingen onder ```extra:```, waar de maximale overschrijding van het open water en het management kan worden ingesteld.

Als men wenst dat bepaalde gebieds-parameters voor specifieke gebieden af moeten wijken van de standaardinstellingen, kan dat vervolgens gedaan worden onder ```gebieden:```.
Hier staat in eerste instantie een ```-``` voor elk gebied, gevolgd door ```{}``` als het gebied geen gewijzigde parameters moet bevatten t.o.v. de default.
Indien er wel behoefte is aan andere parameters, neem dan precies de structuur over zoals onder ```default``` staat: specificeer eerst onder welke component (zoals ```glasNRL``` of ```stuw_pomp```) de instelling valt zoals ook onder ```default```, en specificeer daaronder vervolgens de parameter met zijn nieuwe waarde.

Tot slot staat er onderaan nog een kopje ```verbindingen:```, waar de doorstroming van gebied naar gebied wordt gespecificeerd. Per element in de lijst (wederom aangegeven met een ```-```) moeten de twee gebieden waartussen water stroomt staan naast ```van:``` en ```naar:```, en de breedte van de stuw die deze twee gebieden verbindt naast ```b_stuw:```.
#### Voorbeelden
Zie onderstaand vier gebieden met aangepaste parameters. Gebied 1 (tweede in de lijst) behoudt de default-parameters.
```bash
gebieden:
  - openwater:
      h_init: 2.1
      h_streef: 2.1
  - {}
  - bassinRL:
      h_init: 25
      dh_klep_max: 0.01
    stuw_pomp:
      gemaal_cap: 15
  - openwater:
      opp: 180000
    glasRL:
      opp: 300000
```
