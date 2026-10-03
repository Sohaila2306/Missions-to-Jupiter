# Missions to Jupiter

Eight small Python projects, one per spacecraft, each rebuilding the Earth-to-Jupiter part of a real mission from its actual launch, flyby and arrival dates. Every folder is self-contained: its own README with the history of the mission, the code, and the plots and animation it produces.

| Project | Launch | Jupiter | Route |
|---|---|---|---|
| [Pioneer10](Pioneer10) | Mar 1972 | Dec 1973 | direct |
| [Pioneer11](Pioneer11) | Apr 1973 | Dec 1974 | direct |
| [Voyager1](Voyager1) | Sep 1977 | Mar 1979 | direct |
| [Voyager2](Voyager2) | Aug 1977 | Jul 1979 | direct |
| [Galileo](Galileo) | Oct 1989 | Dec 1995 | Venus, Earth, Earth |
| [Cassini](Cassini) | Oct 1997 | Dec 2000 | Venus, Venus, Earth |
| [Juno](Juno) | Aug 2011 | Jul 2016 | two-year loop, Earth |
| [EuropaClipper](EuropaClipper) | Oct 2024 | Apr 2030 (planned) | Mars, Earth |

To run any of them:

```
cd galileo-jupiter
pip install -r requirements.txt
python main.py
```

The projects use only numpy and matplotlib, and no data has to be downloaded.
