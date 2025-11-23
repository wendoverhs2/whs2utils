import math
import logging
from noisemodels import *
from noisecore import *

EPS = 1e-12

def barrier(hs, hb, hr, dsb, dsr, bt, corr):

    logger = logger = logging.getLogger(__name__)

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

    logger.debug(f"path difference {pd}")

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

    # Number of sectors that the train spans
    tsects = math.ceil(p.tlen / p.slen)

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

    # console.log ('getNoise2: x ' + x + ' y ' + y + ' bht ' + bht + ' bht2 ' + bht2 + ' bpos ' + bpos + ' bpos2 ' + bpos2 + ' dist ' + dist + ' angle ' + angle + ' tsect ' + tsect + ' bt ' + bt + ' padj ' + padj +' tadj ' + tadj);
    logger = logging.getLogger(__name__)
    logger.debug(f"getNoise2: {x} y {y} bht {bht} bht2 {bht2} bpos {bpos} bpos2 {bpos2} dist {dist} angle {angle} tsect {tsect} bt {bt} padj {padj} tadj {tadj}")

    # Every sector produces rolling noise (wheels on the track)
    if p.sources["rolling"].sval:
        s["rolling"] = dB(spl(p.sources["rolling"].sval + 30.0 * math.log10(p.kph)) * fact400 / tsects) - padj
    else:
        s["rolling"] = 0
    
    # Just the front of the train produces aerodynamic noise
    if tsect == 0 and p.sources["aero"].sval:
        s["aero"] = p.sources["aero"].sval + 70.0 * math.log10(p.kph) - padj
    else:
        s["aero"] = 0

    # Every sector produces engine noise on an electric train
    if p.sources["startup"].sval:
        s["startup"] = dB(spl(p.sources["startup"].sval) * fact400 / tsects) - padj
    else:
        s["startup"] = 0

    # Just the back of the train produces pantograph noise
    include_panto = (tsect == tsects - 1)
    # Except 400m trains have a panto at 200m from the front as well
    if p.v >= 2511:
        if not include_panto:
            if p.tlen == 400.0 and (tsect * p.slen) >= 200.0 and ((tsect-1) * p.slen) < 200.0:
                include_panto = True

    if include_panto and p.sources["panto"].sval:
        s["panto"] = p.sources["panto"].sval + 70 * math.log10(p.kph) - padj
    else:
        s["panto"] = 0

    if include_panto and p.sources["pantowell"].sval:
        s["pantowell"] = p.sources["pantowell"].sval + 70 * math.log10(p.kph) - padj
    else:
        s["pantowell"] = 0

    #if (debug == 2) {console.log ('getNoise2: src '); console.log(src);}
    logger.debug(f"getNoise2: src {s}")

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
            working = (10 ** (-attnba / 10)) + (10 ** (-attnbb * J / 10)) - 1
            # Note if this value is negative then the subsequent maths raises an error
            working = max(working, EPS)
            attnb = -10 * math.log10(working)

            #if (debug == 2) {console.log ('getNoise2: attnba ' + attnba + ' attnbb ' + attnbb + ' J ' + J + ' attnb ' + attnb);}
            logger.debug(f"getNoise2: {attnba} attnbb {attnbb} J {J} attnb {attnb}")

        lval = sval + attnd + attna
        if bht > 0 or bht2 > 0:
            lval += attnb
        else:
            lval += attng

        #if (debug == 2) {console.log ('getNoise2: key ' + key + ' src ' + src[key] + ' attnd ' + attnd + ' attna ' + attna + ' attng ' + attng + ' attnb ' + attnb);}
        logger.debug(f"getNoise2: key {key} src {sval} attnd {attnd} attna {attna} attng {attng} attnb {attnb})")

        l[key] = lval

    #console.log ('getNoise2: lamax '); console.log(lamax);
    logger.debug(f"getNoise2: lamax {l}")

    if p.v >= 2509:

        # 250828 Align South Heath NDR Appendix D:
        # LpAFmax=MAX [ (RLpAF,max  BLpAF,max  SLpAF,max) , (RLpAF,max  PLpAF,max  SLpAF,max) ] (Equation 1)
        combo1 = log_sum([l["rolling"], l["aero"],   l["startup"]])  # R + B + S
        # combo2 = log_sum([l["rolling"], l["panto"], l["startup"]])  # R + P + S
        combo2 = log_sum([l["rolling"], l["panto"], l["pantowell"], l["startup"]]) # TODO - spec not clear - check how to add in new term for panto recess

        noise = max(combo1, combo2)

    else:
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

    # Number of sectors that the train spans
    tsects = math.ceil(p.tlen / p.slen)

    # last sector containing any part of train (0-based)
    sect = math.ceil(tpos / p.slen) - 1
    # number of sectors containing part of train
    sects = min(sect + 1, tsects)

    # first and last train sector counting from front of train (0-based)
    if p.dirn == 's':
        tsect0 = tsects - sects
        tsect1 = tsects - 1
    else:
        tsect0 = 0
        tsect1 = sects - 1

    # loop over train sectors
    for tsect in range(tsect0, tsect1 + 1):
        if p.dirn == 's':
            sectt = sect + tsect - tsects + 1
        else:
            sectt = sect - tsect

        # if (debug) {console.log('getNoise starting sectt ' + sectt);}
        logger = logging.getLogger(__name__)
        logger.debug(f"getNoise starting sectt {sectt}")

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
            # The assumption used is that noise emissions from sources inside the porous portal are reduced by 10dB.
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
          
        # if (debug) {
        #     let data = {distx: distx, disty: disty, tpos: tpos, sect: sect, sects: sects, tsect0: tsect0, tsect1: tsect1, tsect: tsect, sectt: sectt, sectt1: sectt1, sectt2: sectt2, distxc: distxc, dist: dist, angle: angle, bht: bhts[sectt], bpos: bposs[sectt], tadj: tadj, noise: noise}; 
        #     console.log ('getNoise: data '); console.log(data);
        # }

        logger.debug(f"distx: {distx}, disty: {disty}, tpos: {tpos}, sect: {sect}, sects: {sects}, tsect0: {tsect0}, tsect1: {tsect1}, tsect: {tsect}, sectt: {sectt}, sectt1: {sectt1}, sectt2: {sectt2}, distxc: {distxc}, dist: {dist}, angle: {angle}, bht: {p.barrier1.bht[sectt]}, bpos: {p.barrier1.bpos[sectt]}, tadj: {tadj}, noise: {noise}")

        # ⚠️ summing in SPL domain: Python spl() equivalent used
        splev += spl(noise)

    return dB(splev)


