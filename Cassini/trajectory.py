"""
Small two-body trajectory toolkit used by this project.

Units: AU for distance, days for time.  The Sun is the only attracting body
(patched conics), planets follow the JPL approximate Keplerian elements
(valid 1800-2050, good to a few thousand km for the inner planets and a few
hundred thousand km for Jupiter - plenty for plotting a transfer arc).
"""
import math
from datetime import date, datetime

import numpy as np

GAUSS_K = 0.01720209895          # Gaussian gravitational constant
MU = GAUSS_K ** 2                # Sun, AU^3 / day^2
AU_KM = 149597870.7
AU_DAY_TO_KMS = AU_KM / 86400.0

# a [AU], e, i [deg], L [deg], long. perihelion [deg], long. node [deg]
# followed by their rates per Julian century
ELEMENTS = {
    "Venus":   ([0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255],
                [0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418]),
    "Earth":   ([1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0],
                [0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0]),
    "Mars":    ([1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891],
                [0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343]),
    "Jupiter": ([5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909],
                [-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106]),
}


def julian_date(d):
    """Julian date from a date / datetime / 'YYYY-MM-DD' string (0h UTC)."""
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d")
    if isinstance(d, datetime):
        frac = (d.hour + d.minute / 60 + d.second / 3600) / 24
        d = d.date()
    else:
        frac = 0.0
    return d.toordinal() + 1721424.5 + frac


def jd_to_date(jd):
    return date.fromordinal(int(math.floor(jd - 1721424.5 + 0.5)))


def _kepler(M, e):
    E = M if e < 0.8 else math.pi
    for _ in range(50):
        dE = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= dE
        if abs(dE) < 1e-13:
            break
    return E


def planet_position(name, jd):
    """Heliocentric ecliptic (J2000) position of a planet in AU."""
    base, rate = ELEMENTS[name]
    T = (jd - 2451545.0) / 36525.0
    a, e, inc, L, wbar, node = [b + r * T for b, r in zip(base, rate)]
    M = math.radians((L - wbar) % 360.0)
    if M > math.pi:
        M -= 2 * math.pi
    E = _kepler(M, e)
    xp = a * (math.cos(E) - e)
    yp = a * math.sqrt(1 - e * e) * math.sin(E)
    w = math.radians(wbar - node)
    O, i = math.radians(node), math.radians(inc)
    cw, sw, cO, sO, ci, si = math.cos(w), math.sin(w), math.cos(O), math.sin(O), math.cos(i), math.sin(i)
    x = (cw * cO - sw * sO * ci) * xp + (-sw * cO - cw * sO * ci) * yp
    y = (cw * sO + sw * cO * ci) * xp + (-sw * sO + cw * cO * ci) * yp
    z = (sw * si) * xp + (cw * si) * yp
    return np.array([x, y, z])


def planet_velocity(name, jd):
    h = 0.25
    return (planet_position(name, jd + h) - planet_position(name, jd - h)) / (2 * h)


# --- Stumpff functions -------------------------------------------------------
def _C(z):
    if z > 1e-6:
        return (1 - math.cos(math.sqrt(z))) / z
    if z < -1e-6:
        return (math.cosh(math.sqrt(-z)) - 1) / (-z)
    return 0.5 - z / 24 + z * z / 720


def _S(z):
    if z > 1e-6:
        s = math.sqrt(z)
        return (s - math.sin(s)) / s ** 3
    if z < -1e-6:
        s = math.sqrt(-z)
        return (math.sinh(s) - s) / s ** 3
    return 1 / 6 - z / 120 + z * z / 5040


# --- Lambert problem (universal variables, multi-revolution) -----------------
def lambert(r1, r2, tof, revs=0, branch=0, prograde=True):
    """
    Solve Lambert's problem around the Sun.

    r1, r2 : position vectors [AU];  tof : time of flight [days]
    revs   : number of complete revolutions (0 = direct transfer)
    branch : for revs >= 1 there are two solutions; 0 = low-z, 1 = high-z
    Returns (v1, v2) velocity vectors [AU/day].
    """
    r1n, r2n = np.linalg.norm(r1), np.linalg.norm(r2)
    cosd = np.dot(r1, r2) / (r1n * r2n)
    cosd = max(-1.0, min(1.0, cosd))
    dth = math.acos(cosd)
    cross_z = r1[0] * r2[1] - r1[1] * r2[0]
    if (prograde and cross_z < 0) or (not prograde and cross_z >= 0):
        dth = 2 * math.pi - dth
    A = math.sin(dth) * math.sqrt(r1n * r2n / (1 - math.cos(dth)))

    def y_of(z):
        return r1n + r2n + A * (z * _S(z) - 1) / math.sqrt(_C(z))

    def t_of(z):
        y = y_of(z)
        if y < 0:
            return float("nan")
        chi = math.sqrt(y / _C(z))
        return (chi ** 3 * _S(z) + A * math.sqrt(y)) / GAUSS_K

    lo = (2 * math.pi * revs) ** 2 + 1e-6 if revs else -4 * math.pi ** 2 * 6
    hi = (2 * math.pi * (revs + 1)) ** 2 - 1e-6
    zs = np.linspace(lo, hi, 6000)
    ts = np.array([t_of(z) for z in zs]) - tof
    roots = []
    for i in range(len(zs) - 1):
        a, b = ts[i], ts[i + 1]
        if np.isnan(a) or np.isnan(b) or a * b > 0:
            continue
        zl, zh = zs[i], zs[i + 1]
        for _ in range(80):
            zm = 0.5 * (zl + zh)
            tm = t_of(zm) - tof
            if np.isnan(tm):
                break
            if (t_of(zl) - tof) * tm <= 0:
                zh = zm
            else:
                zl = zm
        roots.append(0.5 * (zl + zh))
    if not roots:
        raise ValueError("no Lambert solution for the given revs/time of flight")
    z = roots[min(branch, len(roots) - 1)]
    y = y_of(z)
    f = 1 - y / r1n
    g = A * math.sqrt(y / MU)
    gdot = 1 - y / r2n
    v1 = (r2 - f * r1) / g
    v2 = (gdot * r2 - r1) / g
    return v1, v2


# --- Universal-variable propagator -------------------------------------------
def propagate(r0, v0, dt):
    """Advance (r0, v0) by dt days under the Sun's gravity."""
    r0n, v0n = np.linalg.norm(r0), np.linalg.norm(v0)
    vr0 = np.dot(r0, v0) / r0n
    alpha = 2 / r0n - v0n ** 2 / MU
    sq = GAUSS_K
    chi = sq * abs(alpha) * dt if alpha != 0 else sq * dt / r0n
    for _ in range(100):
        z = alpha * chi ** 2
        C, S = _C(z), _S(z)
        F = (r0n * vr0 / sq * chi ** 2 * C + (1 - alpha * r0n) * chi ** 3 * S + r0n * chi - sq * dt)
        dF = (r0n * vr0 / sq * chi * (1 - alpha * chi ** 2 * S)
              + (1 - alpha * r0n) * chi ** 2 * C + r0n)
        step = F / dF
        chi -= step
        if abs(step) < 1e-12:
            break
    z = alpha * chi ** 2
    C, S = _C(z), _S(z)
    f = 1 - chi ** 2 / r0n * C
    g = dt - chi ** 3 / sq * S
    r = f * r0 + g * v0
    rn = np.linalg.norm(r)
    fdot = sq / (rn * r0n) * (alpha * chi ** 3 * S - chi)
    gdot = 1 - chi ** 2 / rn * C
    return r, fdot * r0 + gdot * v0


def resonant_leg(r1, v_planet1, v_planet2, tof, revs, vinf_kms):
    """
    Planet-to-same-planet leg that closes after `revs` full orbits (e.g. the
    2-year Earth-Earth loop of Galileo).  Lambert's problem is ill-conditioned
    when both ends sit at almost the same point, so instead we fix the orbital
    period and pick the departure angle that keeps |v_inf| equal to the value
    the spacecraft arrived with (an unpowered flyby only rotates v_inf).
    Returns (v1, v2) in AU/day.
    """
    r = np.linalg.norm(r1)
    period = tof / revs
    a = (MU * (period / (2 * math.pi)) ** 2) ** (1.0 / 3.0)
    speed = math.sqrt(MU * (2 / r - 1 / a))
    rhat = r1 / r
    that = np.cross([0.0, 0.0, 1.0], rhat)
    w = vinf_kms / AU_DAY_TO_KMS

    def vel(phi):
        return speed * (math.sin(phi) * rhat + math.cos(phi) * that)

    def f(phi):
        return np.linalg.norm(vel(phi) - v_planet1) - w

    lo, hi = 0.0, math.pi / 2
    if f(lo) * f(hi) > 0:
        raise ValueError("no resonant solution for this v_inf")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    v1 = vel(0.5 * (lo + hi))
    _, v2 = propagate(r1, v1, tof)
    return v1, v2
