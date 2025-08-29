import csv
import math
from dataclasses import dataclass, fields, asdict
from typing import Dict, List
from datetime import datetime

@dataclass
class Source:
    set: str
    type: str
    sval: float
    sht: float

@dataclass
class Receptor:
    key: str
    x: float
    y: float
    impacts: float

@dataclass
class Barrier:
    key: str
    slen: float
    bht: List[float]
    bpos: List[float]
    angles: List[float]

@dataclass
class Param:
    key: str
    kph: float
    rht: float
    tlen: float
    slen: float
    refpt: float
    dirn: float
    rstart: float
    rlen: float
    pstart: float
    plen: float
    corr: float
    railht: float
    offset: float
    toffset: float
    barrier1: Barrier
    barrier2: Barrier
    sources: Dict[str,Source]
    tsects: float

@dataclass
class Impact:
    run: str
    param: str
    receptor: str
    impacts: float
    db: float

@dataclass
class Result:
    run: str
    param: str
    receptor: str
    sect: int
    label: int
    timing: float
    bht1: float
    bpos1: float
    bht2: float
    bpos2: float
    db: float
    spl: float

def run():

    # Generate a unique run ID of 14 characters from the system date time
    run = datetime.now().strftime("%Y%m%d%H%M%S")

    print("Loading receptors")
    receptors = load_receptors_csv("noisedata/WHS2 Noise Analysis 2025 - Receptors.csv")
    print(f"Loaded {len(receptors)} receptors")
    print("Loading barriers")
    barriers = load_barriers_csv("noisedata/WHS2 Noise Analysis 2025 - Barriers.csv")
    print(f"Loaded {len(barriers)} barriers")
    print("Loading sourcesets")
    sourcesets = load_sourcesets_csv("noisedata/WHS2 Noise Analysis 2025 - Sources.csv")
    print(f"Loaded {len(sourcesets)} sourcesets")
    print("Loading params")
    params = load_params_csv("noisedata/WHS2 Noise Analysis 2025 - Params.csv", barriers, sourcesets)
    print(f"Loaded {len(params)} params")
    print("Loading sourcesets")

    # Write out a playback of the inputs used in this run
    # The barriers and sources are included inline as fields of the params
    write_list_to_csv(list(receptors.values()), f"noisedata/{run}_receptors.csv")
    write_list_to_csv(list(params.values()), f"noisedata/{run}_params.csv")

    impacts = []
    results = []

    for r in receptors.values():
        for p in params.values():

            sectorcount = len(p.barrier1.bht)

            # Zero based indexing of sectors
            for sect in range(sectorcount):

                # How many seconds does it take for the train to travel from the first sector
                # to this sector - time = length / speed in metres per second
                if p.dirn == "s":
                    # Southbound
                    timing = roundTo((sectorcount-sect-1) * p.slen / (p.kph * 1000 / 3600), 2)
                else:
                    # Northbound
                    timing = roundTo(p.slen * sect / (p.kph * 1000 / 3600), 2)

                # How far has the train travelled at the end of this sector
                tpos = p.slen * (sect + 1)

                # Calculate the noise in decibels when the train is at this position (the end of the sector)
                # as at the receptor location
                db = getNoise(p, r.x - p.refpt, r.y, tpos)

                result = Result(
                    run=run,
                    param=p.key,
                    receptor=r.key,
                    sect=sect,
                    label=(55100 - p.refpt + p.slen * sect), # 55100 converts the train position to a 'chainage'
                    timing=timing,
                    bht1=p.barrier1.bht[sect],
                    bht2=p.barrier2.bht[sect],
                    bpos1=p.barrier1.bpos[sect],
                    bpos2=p.barrier2.bpos[sect],
                    db=roundTo(db,2),
                    spl=roundTo(spl(db),2)
                )

                results.append(result)
                        
            # Calculate the noise in decibels when the train is at a 
            # position described as 'furthest point of noise source from reference point'
            # Not clear what's special about this point

            db = getNoise(p, r.x - p.refpt, r.y, p.offset)
            impact = Impact(
                run=run,
                param=p.key,
                receptor=r.key,
                impacts=r.impacts,
                db=roundTo(db,2)
            )
            impacts.append(impact)

    write_list_to_csv(impacts, f"noisedata/{run}_impacts.csv")
    write_list_to_csv(results, f"noisedata/{run}_results.csv")



def parse_float_list(value: str) -> List[float]:
    """Convert a + separated string into a list of floats."""
    return [float(v) for v in value.split("+") if v.strip()]

def getAngles(slen, bpos):
    # bpos: list of barrier positions for each sector
    # returns a 2D list: angles[i][j] is angle from barrier j to sector i
    angles = []

    for i in range(len(bpos)):
        angle1 = [0] * (len(bpos) + 1)  # pre-allocate list with length len(bpos)+1
        angle1[0] = math.pi / 2  # first element

        # loop backwards from last barrier to 1
        for j in range(len(bpos) - 1, 0, -1):
            if bpos[j - 1] > 0:
                angle1[j] = math.atan(((i - j + 0.5) * slen) / bpos[j - 1])
            elif bpos[j] > 0:
                angle1[j] = math.atan(((i - j + 0.5) * slen) / bpos[j])
            else:
                # use next angle (angle1[j+1]) if no barrier
                angle1[j] = angle1[j + 1]

        angle1[len(bpos)] = -math.pi / 2  # last element
        angles.append(angle1)

    return angles

def load_barriers_csv(file_path: str) -> Dict[str, Barrier]:
    barriers: Dict[str, Barrier] = {}
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            slen = float(row["slen"]) 
            bht = parse_float_list(row["bht"])
            bpos = parse_float_list(row["bpos"])

            if len(bht) != len(bpos):
                raise ValueError(f"Barrier {row['key']} has mismatched bht/bpos lengths")

            angles = getAngles(slen, bpos)

            barrier = Barrier(
                key=row["key"],
                slen=slen,
                bht=bht,
                bpos=bpos,
                angles=angles
            )
            barriers[barrier.key] = barrier
    return barriers

def load_receptors_csv(file_path: str) -> Dict[str, Receptor]:
    receptors: Dict[str, Receptor] = {}
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            receptor = Receptor(
                key=row["key"],
                x=float(row["x"]),
                y=float(row["y"]),
                impacts=float(row["impacts"]),
            )
            receptors[receptor.key] = receptor
    return receptors


def load_sourcesets_csv(file_path: str) -> Dict[str, Dict[str, Source]]:
    sourcesets = {}
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            source = Source(
                set=row["set"],
                type=row["type"],
                sval=float(row["sval"]),
                sht=float(row["sht"]),
            )

            if not sourcesets.get(source.set):
                sourcesets[source.set] = {}

            sourcesets[source.set][source.type] = source

    return sourcesets

def load_params_csv(file_path: str, barriers: Dict[str,Barrier], sourcesets: Dict[str,Dict[str,Source]]) -> Dict[str, Param]:
    params: Dict[str, Param] = {}
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            param = Param(
                key=row["key"],
                kph=float(row["kph"]),
                rht=float(row["rht"]),
                tlen=float(row["tlen"]),
                slen=float(row["slen"]),
                refpt=float(row["refpt"]),
                dirn=row["dirn"],
                rstart=float(row["rstart"]),
                rlen=float(row["rlen"]),
                pstart=float(row["pstart"]),
                plen=float(row["plen"]),
                corr=float(row["corr"]),
                railht=float(row["railht"]),
                offset=float(row["offset"]),
                toffset=float(row["toffset"]),
                barrier1=barriers[row["barrier1"]],
                barrier2=barriers[row["barrier2"]],
                sources=sourcesets[row["sources"]],
                tsects=0.0
            )
            
            if not param.offset:
                # Furthest point of noise source from reference point
                param.offset = param.tlen + param.pstart + param.plen

            if (param.dirn=="s" and param.toffset > 0.0) or (param.dirn=="n" and param.toffset < 0.0):
                # toffset is the offset of the source from the mid-point of the two tracks
                # This should always be positive for northbound trains and negative for southbound trains
                param.toffset = param.toffset * - 1

            # Number of sectors that the train spans
            param.tsects = math.ceil(param.tlen / param.slen)

            params[param.key] = param

    return params

def write_list_to_csv(list, filename: str) -> None:
    """Write a list of dataclass objects to a CSV file."""
    if not list:
        raise ValueError("List is empty, nothing to write.")

    # Get fieldnames automatically from dataclass
    fieldnames = list[0].__dataclass_fields__.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in list:
            writer.writerow(asdict(item))

def dB(spl):
    # JS: 10 * Math.log10(spl)
    # Both JS and Python raise/log errors for spl <= 0:
    #   JS: log10(0) -> -Infinity
    #   Python: math.log10(0) -> ValueError
    return 10 * math.log10(spl)

def spl(dB_value):
    # JS: Math.pow(10, dB / 10)
    # Python equivalent: 10 ** (dB_value / 10)
    return 10 ** (dB_value / 10)

def roundTo(num, places):
    # JS version uses string exponent shifting ("1.23e+2") to round to places.
    # Python equivalent is round(num, places), but:
    #   ⚠️ JS Math.round rounds half away from zero (0.5 -> 1, -0.5 -> -1)
    #   ⚠️ Python round uses "banker's rounding" (to even: -0.5 -> 0)
    # If exact JS behaviour is needed, must reimplement.
    return round(num, places)

def barrier(hs, hb, hr, dsb, dsr, bt, corr):

    #Barrier attenuation calculation
    #Parameters: height of source, barrier, receptor; shortest distance source-barrier, source-receptor, barrier type (a or r)

    # If corr is set, applies barrier height correction
    # Note this doesn't seem to actually use the value of corr, just a switch based on whether or not it is zero
    if corr != 0:
        # JS: all arithmetic uses floats; in Python, division is float by default
        zk = hs + (hr - hs) * dsb / dsr
        zl = zk + dsb * (dsr - dsb) / (dsr * 26)
        hb2 = (hb - zl) + hs

        # ⚠️ JS commented out alternative calculation:
        # hb2 = hb - hr - (hs - hr + dsb / 26) * (dsr - dsb) / dsr

        # Assign corrected barrier height
        hb = hb2

    # Path difference calculation (pd)
    pd = (
        math.sqrt((hb - hs) ** 2 + dsb ** 2)
        + math.sqrt((hb - hr) ** 2 + (dsr - dsb) ** 2)
        - math.sqrt((hr - hs) ** 2 + dsr ** 2)
    )

    # Attenuation calculation
    atten = 0
    if bt == "r":
        if hb / dsb >= hr / dsr:
            if pd > 0.01:
                atten = -11 * (pd ** 0.262)   # JS Math.pow == Python **
            else:
                atten = -3.3
        else:
            atten = -math.exp(1.1958 - 14 * pd)
    else:
        if hb / dsb > hr / dsr:
            expr = 2.5 + 30 * (pd + 0.025)
            # ⚠️ Python math.log10 throws ValueError if expr <= 0
            # JS Math.log10 would return NaN instead of crashing.
            if expr > 0:
                atten = -10 * math.log10(expr)
            else:
                atten = float("nan")  # mimic JS NaN
        else:
            atten = -math.exp(1.63 - 12 * pd)

    return atten

def getNoise2(p: Param, bht, bht2, bpos, bpos2, dist, angle, tsect, bt, padj, tadj):
    # HS2 noise model ported from javascript in noisemap.htm in Aug 2025 with help from ChatGPT

    s = {}
    l = {}

    # Adjust for track offset
    x = dist * math.sin(angle)
    y = dist * math.cos(angle) + p.toffset

    # ⚠️ JS atan(x / y) vs Python math.atan(x / y) are equivalent,
    # BUT if y == 0, JS gives Infinity and atan(Infinity) == PI/2.
    # In Python, ZeroDivisionError will be raised instead.
    angle = math.atan(x / y)

    # ⚠️ In JS, division is always float. In Python, ensure float division
    bpos = (bpos + p.toffset) / math.cos(angle)
    bpos2 = (bpos2 + p.toffset) / math.cos(angle)
    dist = y / math.cos(angle)

    # Not found a source for the reason for the 
    # adjustment adjust of 2 / number of sector train spans for 400m long trains
    # With a sector length of 12.5 metres = 2/32 adjustment factor
    fact400 = 1
    if p.tlen == 400:
        fact400 = 2

    # Every sector produces rolling noise (wheels on the track)
    # ⚠️ Math.log10 in JS == math.log10 in Python
    s["rolling"] = dB(spl(p.sources["rolling"].sval + 30.0 * math.log10(p.kph)) * fact400 / p.tsects) - padj
    
    # Just the front of the train produces aerodynamic noise
    if tsect == 0:
        s["aero"] = p.sources["aero"].sval + 70.0 * math.log10(p.kph) - padj
    else:
        s["aero"] = 0

    # Every sector produces engine noise on an electric train
    s["startup"] = dB(spl(p.sources["startup"].sval) * fact400 / p.tsects) - padj

    # Just the back of the train produces pantograph noise
    if tsect == p.tsects - 1:
        s["panto"] = p.sources["panto"].sval + 70 * math.log10(p.kph) - padj
    else:
        s["panto"] = 0

    for key, sval in s.items():
        
        sht = p.sources[key].sht + p.railht #Add the rail height to the source height (which is relative to the rail)
        
        # See 1.3.17 of spec: "geometric spreading"
        attnd = -14.5 * math.log10(dist / 25)
        # See 1.3.17 of spec: "air absorbtion"
        attna = -dist / 120

        # mph = mean propogation height
        # Halfway between the top of the source/barrier and the rail height 
        mph = max(((max(sht, bht) + p.rht) / 2), 1)
        # See 1.3.17 of spec: "ground attenuation"
        # More height = Less ground attenuation
        attng = -dist / (130 * mph)

        # Now allow for any attenuation due to the barrier(s) - zero, one or two barriers
        attnb = 0
        if not bht and not bht2:
            # No barriers defined at this train position
            attnb = 0
        elif bht and not bht2:
            # Just barrier 1 defined at this train position
            attnb = barrier(sht, bht, p.rht + tadj, bpos, dist, bt, p.corr)
        elif bht2 and not bht:
            # Just barrier 2 defined at this train position
            attnb = barrier(sht, bht2, p.rht + tadj, bpos2, dist, bt, p.corr)
        else:
            # Both barrier 1 and barrier 2 defined at this train position
            attnb1 = barrier(sht, bht, p.rht + tadj, bpos, dist, bt, p.corr)
            attnb2 = barrier(sht, bht2, p.rht + tadj, bpos2, dist, bt, p.corr)
            attnba = min(attnb1, attnb2)
            attnbb = max(attnb1, attnb2)
            J = (abs(bpos - bpos2) / dist) ** 0.25

            # ⚠️ JS Math.pow(10, -x/10) handles negative bases differently than Python **.
            # Note if this value is negative then the subsequent maths raises an error
            working = (10 ** (-attnba / 10)) + (10 ** (-attnbb * J / 10)) - 1
            attnb = -10 * math.log10(working)

        lval = sval + attnd + attna
        if bht > 0 or bht2 > 0:
            lval += attnb
        else:
            lval += attng

        l[key] = lval

    noise = dB(
        spl(l["rolling"]) +
        spl(l["startup"]) +
        spl(max(l["aero"], l["panto"]))
    )

    return noise

def intersect(angles, sect, angle):
    # angles: list of lists (or 2D array), angles[sect] is a list
    # returns the first index i where angles[sect][i + 1] < angle, or 0 if none

    angle_list = angles[sect]

    for i in range(len(angle_list)):
        # ⚠️ JS allows out-of-bounds access; Python will raise IndexError if i+1 >= len(angle_list)
        if i + 1 < len(angle_list) and angle_list[i + 1] < angle:
            return i

    return 0

def getNoise(p: Param, distx, disty, tpos):
    # Return noise at a given distance (horizontal, vertical) and train position (furthest point which may be front or back) 
    # relative to reference point

    splev = 0  # cumulative spl

    # last sector containing any part of train (0-based)
    sect = math.ceil(tpos / p.slen) - 1
    # number of sectors containing part of train
    sects = min(sect + 1, p.tsects)

    # first and last train sector counting from front of train (0-based)
    if p.dirn == 's':
        tsect0 = p.tsects - sects
        tsect1 = p.tsects - 1
    else:
        tsect0 = 0
        tsect1 = sects - 1

    # loop over train sectors
    for tsect in range(tsect0, tsect1 + 1):
        if p.dirn == 's':
            sectt = sect + tsect - p.tsects + 1
        else:
            sectt = sect - tsect

        distt = (sectt + 0.5) * p.slen
        distxc = distx + distt
        dist = math.sqrt(distxc ** 2 + disty ** 2)
        # ⚠️ JS atan(x / y) vs Python math.atan(x / y)
        # If disty == 0, JS returns ±Infinity, Python raises ZeroDivisionError
        angle = math.atan(distxc / disty)

        btype = 'a'  # barrier type
        if p.rstart <= sectt * p.slen < p.rstart + p.rlen:
            btype = 'r'

        padj = 0  # porous portal adjustment
        if p.pstart <= sectt * p.slen < p.pstart + p.plen:
            padj = 10

        tadj = -0.000004 * (distt - p.refpt) ** 2 + 0.0149 * (distt - p.refpt)

        sectt1 = intersect(p.barrier1.angles, sectt, angle)  # adjusted for intersect
        sectt2 = intersect(p.barrier2.angles, sectt, angle)

        noise = getNoise2(
            p,
            p.barrier1.bht[sectt1],
            p.barrier2.bht[sectt2],
            p.barrier1.bpos[sectt1],
            p.barrier2.bpos[sectt2],
            dist,
            angle,
            tsect,
            btype,
            padj,
            tadj
        )

        # ⚠️ summing in SPL domain: Python spl() equivalent used
        splev += spl(noise)

    return dB(splev)