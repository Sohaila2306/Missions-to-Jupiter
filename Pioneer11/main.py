"""
Run the trajectory simulation for this mission.

    python main.py            # PNG plots, CSV, summary and an animated GIF
    python main.py --no-gif   # skip the animation (faster)
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from mission import MISSION
from trajectory import (AU_DAY_TO_KMS, MU, jd_to_date, julian_date, lambert,
                        planet_position, planet_velocity, propagate, resonant_leg)

BG = "#0b0d17"
FG = "#d7dae5"
BODY_COLOR = {"Venus": "#ffb347", "Earth": "#4aa3ff", "Mars": "#e5593f", "Jupiter": "#d9b382"}
LEG_COLORS = ["#4fc3f7", "#9ccc65", "#ffd54f", "#f48fb1", "#ba68c8"]
LABEL_OFFSETS = [(-70, -26), (12, 14), (-76, 16), (14, -30), (14, 12), (-70, 14)]


def solve_legs(events):
    """One Lambert arc between every pair of consecutive events."""
    legs = []
    for ev, nxt in zip(events[:-1], events[1:]):
        j1, j2 = julian_date(ev["date"]), julian_date(nxt["date"])
        r1, r2 = planet_position(ev["body"], j1), planet_position(nxt["body"], j2)
        if ev.get("resonant"):
            # Earth-to-Earth loop: keep |v_inf| from the previous flyby
            v1, v2 = resonant_leg(r1, planet_velocity(ev["body"], j1), planet_velocity(nxt["body"], j2),
                                  j2 - j1, ev["revs"], legs[-1]["vinf_in"])
        else:
            v1, v2 = lambert(r1, r2, j2 - j1, ev.get("revs", 0), ev.get("branch", 0))
        legs.append(dict(jd1=j1, jd2=j2, r1=r1, r2=r2, v1=v1, v2=v2,
                         vinf_out=np.linalg.norm(v1 - planet_velocity(ev["body"], j1)) * AU_DAY_TO_KMS,
                         vinf_in=np.linalg.norm(v2 - planet_velocity(nxt["body"], j2)) * AU_DAY_TO_KMS))
    return legs


def sample_path(legs, step_days=4.0):
    """Sample position / velocity along every leg."""
    rows = []
    for k, leg in enumerate(legs):
        n = max(30, int((leg["jd2"] - leg["jd1"]) / step_days))
        for dt in np.linspace(0, leg["jd2"] - leg["jd1"], n, endpoint=(k == len(legs) - 1)):
            r, v = propagate(leg["r1"], leg["v1"], dt)
            rows.append((leg["jd1"] + dt, k, r, v))
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "leg", "x_au", "y_au", "z_au", "dist_sun_au", "speed_kms", "dist_earth_au"])
        for jd, k, r, v in rows:
            earth = planet_position("Earth", jd)
            w.writerow([jd_to_date(jd).isoformat(), k + 1, *np.round(r, 5), round(np.linalg.norm(r), 4),
                        round(np.linalg.norm(v) * AU_DAY_TO_KMS, 3), round(np.linalg.norm(r - earth), 4)])


def summary_text(events, legs, rows):
    lines = [MISSION["name"] + " - Earth to Jupiter", ""]
    t0 = legs[0]["jd1"]
    total = legs[-1]["jd2"] - t0
    lines.append(f"Launch     : {events[0]['date']}")
    lines.append(f"Arrival    : {events[-1]['date']}")
    lines.append(f"Flight time: {total:.0f} days ({total / 365.25:.2f} years)")
    path = sum(np.linalg.norm(rows[i + 1][2] - rows[i][2]) for i in range(len(rows) - 1))
    lines.append(f"Path length: {path:.2f} AU ({path * 149.5978707:.0f} million km), heliocentric")
    lines.append("")
    lines.append(f"{'#':<3}{'event':<22}{'date':<12}{'day':>6}{'dist Sun':>10}")
    for i, ev in enumerate(events):
        jd = julian_date(ev["date"])
        r = np.linalg.norm(planet_position(ev["body"], jd))
        lines.append(f"{i:<3}{ev['label']:<22}{ev['date']:<12}{jd - t0:>6.0f}{r:>8.2f} AU")
    lines.append("")
    lines.append("Leg by leg (heliocentric conic between events)")
    for i, leg in enumerate(legs):
        a = 1 / (2 / np.linalg.norm(leg["r1"]) - np.dot(leg["v1"], leg["v1"]) / MU)
        lines.append(f"  {events[i]['label']} -> {events[i + 1]['label']}: {leg['jd2'] - leg['jd1']:.0f} d, "
                     f"semi-major axis {a:.2f} AU, v_inf out {leg['vinf_out']:.2f} km/s, v_inf in {leg['vinf_in']:.2f} km/s")
    lines.append("")
    lines.append("Flyby check (|v_inf| should match before and after an unpowered flyby)")
    for i in range(1, len(events) - 1):
        d = legs[i]["vinf_out"] - legs[i - 1]["vinf_in"]
        lines.append(f"  {events[i]['label']}: in {legs[i - 1]['vinf_in']:.2f} / out {legs[i]['vinf_out']:.2f} km/s "
                     f"(difference {d:+.2f} km/s)")
    if len(events) == 2:
        lines.append("  (single direct arc, no flybys)")
    return "\n".join(lines) + "\n"


def style(ax):
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.tick_params(colors=FG, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#3a3f55")
    ax.set_xlabel("x (AU)", color=FG)
    ax.set_ylabel("y (AU)", color=FG)
    ax.grid(color="#1c2033", lw=0.6)


def draw_orbits(ax, bodies, jd_ref):
    th = np.linspace(0, 2 * np.pi, 400)
    for b in bodies:
        # use the real orbit shape: sample one planet period around jd_ref
        period = {"Venus": 224.7, "Earth": 365.25, "Mars": 687.0, "Jupiter": 4332.6}[b]
        pts = np.array([planet_position(b, jd_ref + d)[:2] for d in np.linspace(0, period, 300)])
        ax.plot(pts[:, 0], pts[:, 1], color=BODY_COLOR[b], lw=0.7, alpha=0.35)
    ax.scatter([0], [0], s=140, color="#ffdd55", zorder=5)


def plot_leg_lines(ax, events, legs, rows, lw=2.2, with_label=True):
    xy = np.array([r[:2] for _, _, r, _ in rows])
    ks = np.array([k for _, k, _, _ in rows])
    for k in range(len(legs)):
        sel = xy[ks == k]
        if k < len(legs) - 1:  # include first point of next leg so segments join
            sel = np.vstack([sel, xy[ks == k + 1][:1]])
        ax.plot(sel[:, 0], sel[:, 1], color=LEG_COLORS[k % len(LEG_COLORS)], lw=lw, zorder=4,
                label=f"{events[k]['label']} to {events[k + 1]['label']}" if with_label else None)


def label_events(ax, events, keep, fontsize=8):
    """Label events chosen by `keep(position)`; push labels away from the Sun and stack overlapping ones."""
    placed = []
    for ev in events:
        p = planet_position(ev["body"], julian_date(ev["date"]))[:2]
        ax.scatter(*p, s=150 if ev["body"] == "Jupiter" else 60, color=BODY_COLOR[ev["body"]],
                   edgecolor="white", linewidth=0.8, zorder=6)
        if not keep(p):
            continue
        n = sum(1 for q in placed if np.linalg.norm(q - p) < 0.25)
        placed.append(p)
        d = p / (np.linalg.norm(p) or 1.0)
        dist = 26 + 24 * n
        off = (d[0] * dist, d[1] * dist)
        ax.annotate(f"{ev['label']}\n{ev['date']}", p, xytext=off, textcoords="offset points",
                    color="white", fontsize=fontsize, ha="left" if d[0] >= 0 else "right",
                    arrowprops=dict(arrowstyle="-", color="#8890a8", lw=0.7), zorder=7)


def plot_trajectory(path, events, legs, rows):
    bodies = sorted({e["body"] for e in events} | {"Earth", "Jupiter"}, key=["Venus", "Earth", "Mars", "Jupiter"].index)
    inner_bodies = [b for b in bodies if b != "Jupiter"]
    inner_lim = 2.2 if "Mars" in bodies else 1.9

    fig = plt.figure(figsize=(14, 8), facecolor=BG)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.35, 1], height_ratios=[1.15, 1], wspace=0.12, hspace=0.18)
    ax = fig.add_subplot(gs[:, 0])
    zoom = fig.add_subplot(gs[0, 1])
    facts = fig.add_subplot(gs[1, 1])

    # left: the whole trip out to Jupiter
    style(ax)
    draw_orbits(ax, bodies, legs[0]["jd1"])
    plot_leg_lines(ax, events, legs, rows)
    jl = planet_position("Jupiter", legs[0]["jd1"])
    ax.scatter(*jl[:2], s=70, color=BODY_COLOR["Jupiter"], alpha=0.3, zorder=3)
    ax.annotate("Jupiter at launch", jl[:2], xytext=(8, -14), textcoords="offset points",
                color=FG, fontsize=7, alpha=0.6)
    label_events(ax, events, keep=lambda p: np.linalg.norm(p) > inner_lim + 0.3)
    ax.set_xlim(-6.4, 6.4)
    ax.set_ylim(-6.4, 6.4)
    total = legs[-1]["jd2"] - legs[0]["jd1"]
    ax.set_title(f"{MISSION['name']}: Earth to Jupiter in {total / 365.25:.1f} years", color="white", fontsize=13, pad=12)
    leg = ax.legend(loc="upper left", fontsize=8, facecolor=BG, edgecolor="#3a3f55")
    for t in leg.get_texts():
        t.set_color(FG)

    # top right: zoom on the inner solar system, where the flybys happen
    style(zoom)
    draw_orbits(zoom, inner_bodies, legs[0]["jd1"])
    plot_leg_lines(zoom, events, legs, rows, lw=2.0, with_label=False)
    label_events(zoom, events, keep=lambda p: np.linalg.norm(p) <= inner_lim + 0.3, fontsize=7)
    zoom.set_xlim(-inner_lim, inner_lim)
    zoom.set_ylim(-inner_lim, inner_lim)
    zoom.set_title("Inner solar system (zoom)", color="white", fontsize=11, pad=14)

    # bottom right: key numbers
    facts.set_facecolor(BG)
    facts.axis("off")
    lines = [f"Launch        {events[0]['date']}",
             f"Arrival       {events[-1]['date']}",
             f"Flight time   {total:.0f} days ({total / 365.25:.2f} years)",
             f"Launch v_inf  {legs[0]['vinf_out']:.2f} km/s  (C3 = {legs[0]['vinf_out'] ** 2:.1f} km2/s2)",
             f"Arrival v_inf {legs[-1]['vinf_in']:.2f} km/s (relative to Jupiter)",
             f"Gravity assists in the model: {max(len(events) - 2, 0)}"]
    facts.text(0.02, 0.95, "\n".join(lines), color=FG, fontsize=10, va="top", family="monospace",
               transform=facts.transAxes)
    facts.text(0.02, 0.30, "Top view of the ecliptic plane.\nSun-only gravity, instantaneous flybys,\n"
               "planet positions from JPL approximate elements.", color="#8890a8", fontsize=8.5,
               va="top", transform=facts.transAxes)
    fig.savefig(path, dpi=130, facecolor=BG, bbox_inches="tight")
    plt.close(fig)


def plot_telemetry(path, events, legs, rows):
    t0 = legs[0]["jd1"]
    days = np.array([jd - t0 for jd, *_ in rows])
    rs = np.array([np.linalg.norm(r) for _, _, r, _ in rows])
    sp = np.array([np.linalg.norm(v) * AU_DAY_TO_KMS for *_, v in rows])
    de = np.array([np.linalg.norm(r - planet_position("Earth", jd)) for jd, _, r, _ in rows])
    fig, axs = plt.subplots(3, 1, figsize=(9, 8), sharex=True, facecolor=BG)
    data = [(rs, "Distance from Sun (AU)", "#ffd54f"), (sp, "Speed relative to Sun (km/s)", "#4fc3f7"),
            (de, "Distance from Earth (AU)", "#9ccc65")]
    for ax, (y, lab, col) in zip(axs, data):
        ax.set_facecolor(BG)
        ax.plot(days, y, color=col, lw=1.8)
        ax.set_ylabel(lab, color=FG, fontsize=9)
        ax.tick_params(colors=FG, labelsize=8)
        ax.grid(color="#1c2033", lw=0.6)
        for s in ax.spines.values():
            s.set_color("#3a3f55")
        for ev in events[1:-1]:
            ax.axvline(julian_date(ev["date"]) - t0, color="#8890a8", ls="--", lw=0.8)
    for ev in events[1:-1]:
        axs[0].text(julian_date(ev["date"]) - t0, axs[0].get_ylim()[1], " " + ev["label"], color=FG,
                    fontsize=7, rotation=90, va="top")
    axs[-1].set_xlabel("Days since launch", color=FG)
    axs[0].set_title(f"{MISSION['name']}: flight profile", color="white")
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor=BG)
    plt.close(fig)


def make_gif(path, events, legs, rows, frames=100):
    bodies = sorted({e["body"] for e in events} | {"Earth", "Jupiter"}, key=["Venus", "Earth", "Mars", "Jupiter"].index)
    jd_start, jd_end = legs[0]["jd1"], legs[-1]["jd2"]
    pad = 8  # hold the last frame a moment
    jds = np.concatenate([np.linspace(jd_start, jd_end, frames), np.full(pad, jd_end)])
    path_jd = np.array([jd for jd, *_ in rows])
    path_xy = np.array([r[:2] for _, _, r, _ in rows])
    path_v = np.array([np.linalg.norm(v) * AU_DAY_TO_KMS for *_, v in rows])

    fig, ax = plt.subplots(figsize=(6.4, 6.4), facecolor=BG)
    style(ax)
    draw_orbits(ax, bodies, jd_start)
    lim = 6.0
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_title(f"{MISSION['name']} to Jupiter", color="white", fontsize=12)
    trail, = ax.plot([], [], color="#4fc3f7", lw=2, zorder=4)
    craft, = ax.plot([], [], "o", color="white", ms=6, zorder=8)
    dots = {b: ax.plot([], [], "o", color=BODY_COLOR[b], ms=9 if b == "Jupiter" else 6, zorder=6)[0] for b in bodies}
    for b in bodies:
        ax.text(0, 0, "", color=FG)  # placeholder so text order stays stable
    labels = {b: ax.text(0, 0, b, color=FG, fontsize=7, zorder=7) for b in bodies}
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, color="white", fontsize=9, va="top", family="monospace")

    def update(i):
        jd = jds[i]
        m = path_jd <= jd
        trail.set_data(path_xy[m, 0], path_xy[m, 1])
        idx = max(0, m.sum() - 1)
        craft.set_data([path_xy[idx, 0]], [path_xy[idx, 1]])
        for b in bodies:
            p = planet_position(b, jd)
            dots[b].set_data([p[0]], [p[1]])
            labels[b].set_position((p[0] + 0.15, p[1] + 0.15))
        info.set_text(f"{jd_to_date(jd).isoformat()}\nday {jd - jd_start:4.0f}\n{path_v[idx]:5.1f} km/s")
        return []

    anim = FuncAnimation(fig, update, frames=len(jds), blit=False)
    anim.save(path, writer=PillowWriter(fps=18), dpi=100, savefig_kwargs={"facecolor": BG})
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=MISSION["name"] + " trajectory simulation")
    ap.add_argument("--no-gif", action="store_true", help="skip the animated GIF")
    ap.add_argument("--outdir", default="output", help="where to write results (default: output)")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    events = MISSION["events"]
    legs = solve_legs(events)
    rows = sample_path(legs)

    text = summary_text(events, legs, rows)
    print(text)
    with open(os.path.join(args.outdir, "summary.txt"), "w") as fh:
        fh.write(text)
    write_csv(os.path.join(args.outdir, "trajectory.csv"), rows)
    plot_trajectory(os.path.join(args.outdir, "trajectory.png"), events, legs, rows)
    plot_telemetry(os.path.join(args.outdir, "telemetry.png"), events, legs, rows)
    if not args.no_gif:
        make_gif(os.path.join(args.outdir, "flight.gif"), events, legs, rows)
    print("Files written to", os.path.abspath(args.outdir))


if __name__ == "__main__":
    main()
