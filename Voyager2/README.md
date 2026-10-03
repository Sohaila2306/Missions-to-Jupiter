# Voyager 2: Earth to Jupiter

Reconstructing the trajectory of Voyager 2 from Earth to its Jupiter flyby.

![Flight animation](output/flight.gif)

## The mission

Voyager 2 left Cape Canaveral on 20 August 1977, sixteen days before Voyager 1. It followed a slower path, and the flight to Jupiter took almost two years, almost five months longer than Voyager 1 needed. The slower route kept the option open of continuing on to Uranus and Neptune, which is exactly what happened.

Its closest approach to Jupiter came on 9 July 1979, at about 570,000 km from the planet's center. By then Voyager 1 had already found Io's volcanoes, and Voyager 2 returned to watch them: most of the plumes were still active and one had gone quiet. It also imaged the cracked ice surface of Europa and the structure of the Great Red Spot, and confirmed the faint ring around the planet.

Voyager 2 went on to Saturn (August 1981), Uranus (January 1986) and Neptune (August 1989). It is still the only spacecraft that has visited Uranus and Neptune. In November 2018 it crossed the heliopause and entered interstellar space.

- **Launch:** 20 August 1977, Titan IIIE-Centaur
- **Jupiter closest approach:** 9 July 1979, about 570,000 km from the center
- **Uranus / Neptune:** January 1986 / August 1989
- **Interstellar space:** November 2018

## What this project does

The script rebuilds the heliocentric part of the trip, from Earth at launch to Jupiter at arrival, using the real event dates listed below. It places the planets with the JPL approximate orbital elements, solves Lambert's problem for the arc between each pair of events, propagates the spacecraft along that arc and plots the result. There are no flybys in the model, so the whole trip is one arc.

| Event | Date |
|---|---|
| Launch | 1977-08-20 |
| Jupiter flyby | 1979-07-09 |

![Trajectory](output/trajectory.png)

![Flight profile](output/telemetry.png)

## Run it

```
pip install -r requirements.txt
python main.py
```

That takes well under a minute and writes everything to the `output/` folder. Use `python main.py --no-gif` to skip the animation. Python 3.8 or newer, no accounts or data downloads needed.

## Output from the current run

```
Voyager 2 - Earth to Jupiter

Launch     : 1977-08-20
Arrival    : 1979-07-09
Flight time: 688 days (1.88 years)
Path length: 7.47 AU (1118 million km), heliocentric

#  event                 date           day  dist Sun
0  Launch                1977-08-20       0    1.01 AU
1  Jupiter flyby         1979-07-09     688    5.33 AU

Leg by leg (heliocentric conic between events)
  Launch -> Jupiter flyby: 688 d, semi-major axis 3.70 AU, v_inf out 10.23 km/s, v_inf in 7.90 km/s

Flyby check (|v_inf| should match before and after an unpowered flyby)
  (single direct arc, no flybys)
```

`output/trajectory.csv` holds the sampled path (date, position in AU, distance from the Sun, speed, distance from Earth) if you want to plot it yourself.

## How it works

- `trajectory.py` has the numerical part: planet positions from Keplerian elements, a universal-variable Lambert solver that also handles multi-revolution arcs, and a Kepler propagator.
- `mission.py` lists the events (body and date) for this mission. Change the dates there and rerun to see a different launch window.
- `main.py` solves the legs, samples the path and makes the plots, the CSV and the GIF.

Units are AU and days internally. The only gravity is the Sun's, and every flyby is treated as instantaneous, which is the usual patched-conic approximation.

## Limits of the model

One direct arc from Earth to Jupiter. The gravity assists at Jupiter, Saturn and Uranus that make up the rest of the Grand Tour are not modeled.

In general: the planet positions are an approximation (good to a few thousand km for the inner planets and a few hundred thousand km for Jupiter), the spacecraft is a point mass with no maneuvers, and the "flyby check" in the output shows how far each flyby is from conserving the speed relative to the planet. A real unpowered flyby conserves it exactly, so a large difference points at something the model leaves out, usually a deep-space maneuver. This is a reconstruction for learning and visualization, not mission-design software.

## Files

```
main.py            run this
mission.py         event list for Voyager 2
trajectory.py      orbit mechanics
requirements.txt
output/            plots, animation, CSV, summary
```
