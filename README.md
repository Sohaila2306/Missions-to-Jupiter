# Missions to Jupiter

Eight small Python projects, one per spacecraft, each rebuilding the Earth-to-Jupiter part of a real mission from its actual launch, flyby and arrival dates. Every folder is self-contained: its own README with the history of the mission, the code, and the plots and animation it produces.

| Project | Launch | Jupiter | Route |
|---|---|---|---|
| [pioneer-10-jupiter](pioneer-10-jupiter) | Mar 1972 | Dec 1973 | direct |
| [pioneer-11-jupiter](pioneer-11-jupiter) | Apr 1973 | Dec 1974 | direct |
| [voyager-1-jupiter](voyager-1-jupiter) | Sep 1977 | Mar 1979 | direct |
| [voyager-2-jupiter](voyager-2-jupiter) | Aug 1977 | Jul 1979 | direct |
| [galileo-jupiter](galileo-jupiter) | Oct 1989 | Dec 1995 | Venus, Earth, Earth |
| [cassini-jupiter](cassini-jupiter) | Oct 1997 | Dec 2000 | Venus, Venus, Earth |
| [juno-jupiter](juno-jupiter) | Aug 2011 | Jul 2016 | two-year loop, Earth |
| [europa-clipper-jupiter](europa-clipper-jupiter) | Oct 2024 | Apr 2030 (planned) | Mars, Earth |

To run any of them:

```
cd galileo-jupiter
pip install -r requirements.txt
python main.py
```

The projects use only numpy and matplotlib, and no data has to be downloaded.
