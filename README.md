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
