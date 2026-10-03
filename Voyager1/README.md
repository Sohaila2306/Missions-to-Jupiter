# Voyager 1: Earth to Jupiter

Reconstructing the trajectory of Voyager 1 from Earth to its Jupiter flyby.

![Flight animation](output/flight.gif)

## The mission

Voyager 1 was launched on 5 September 1977 on a Titan IIIE-Centaur, sixteen days after its twin Voyager 2. Despite the later launch it was put on a faster, shorter path and reached Jupiter first, which is why it carries the number 1. Both spacecraft were designed to take advantage of a planetary alignment that comes around only about once every 175 years.

Voyager 1 made its closest approach to Jupiter on 5 March 1979, about 349,000 km from the planet's center. It discovered a thin ring around Jupiter, photographed lightning on the night side, and gave the first detailed look at the Galilean moons. A few days after the encounter, navigation images revealed a volcanic plume rising from Io, the first time active volcanoes had been seen anywhere beyond Earth.

From Jupiter the spacecraft went on to Saturn (November 1980) and then climbed out of the plane of the planets. In August 2012 it crossed the heliopause and became the first human-made object in interstellar space. It is still sending data.

- **Launch:** 5 September 1977, Titan IIIE-Centaur
- **Jupiter closest approach:** 5 March 1979, about 349,000 km from the center
- **Saturn flyby:** November 1980
- **Interstellar space:** August 2012

## What this project does

The script rebuilds the heliocentric part of the trip, from Earth at launch to Jupiter at arrival, using the real event dates listed below. It places the planets with the JPL approximate orbital elements, solves Lambert's problem for the arc between each pair of events, propagates the spacecraft along that arc and plots the result. There are no flybys in the model, so the whole trip is one arc.

| Event | Date |
|---|---|
| Launch | 1977-09-05 |
| Jupiter flyby | 1979-03-05 |

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
Voyager 1 - Earth to Jupiter

Launch     : 1977-09-05
Arrival    : 1979-03-05
Flight time: 546 days (1.49 years)
Path length: 6.73 AU (1007 million km), heliocentric

#  event                 date           day  dist Sun
0  Launch                1977-09-05       0    1.01 AU
1  Jupiter flyby         1979-03-05     546    5.29 AU

Leg by leg (heliocentric conic between events)
  Launch -> Jupiter flyby: 546 d, semi-major axis 5.10 AU, v_inf out 10.31 km/s, v_inf in 10.96 km/s

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

One direct Earth to Jupiter arc, with no deep-space maneuvers. The Jupiter gravity assist that sent Voyager 1 on to Saturn is not modeled.

In general: the planet positions are an approximation (good to a few thousand km for the inner planets and a few hundred thousand km for Jupiter), the spacecraft is a point mass with no maneuvers, and the "flyby check" in the output shows how far each flyby is from conserving the speed relative to the planet. A real unpowered flyby conserves it exactly, so a large difference points at something the model leaves out, usually a deep-space maneuver. This is a reconstruction for learning and visualization, not mission-design software.

## Files

```
main.py            run this
mission.py         event list for Voyager 1
trajectory.py      orbit mechanics
requirements.txt
output/            plots, animation, CSV, summary
```
