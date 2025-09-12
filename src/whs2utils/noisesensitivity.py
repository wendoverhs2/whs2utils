import sys
import math
from noisecalc import *
from noisemodels import Param

sensitivity_funcs = []

def sensitivity(func):
    sensitivity_funcs.append(func)
    return func

@sensitivity
def v_0(p):
    p.v = 0

@sensitivity
def v_2509(p):
    p.v = 2509

@sensitivity
def toffset_variant(p):
    if p.dirn == "n": # northbound = 'down' line = positive track offset 
        p.toffset = +2.35 # distance to the inside rail = track separation / 2 = 4.7m / 2
    elif p.dirn == "s": # southbound = 'up' line = negative track offset
        p.toffset = -3.785 # distance to the outside rail = track separation / 2 + track width = 4.7m / 2 + 1.435

@sensitivity
def src_act(p):
    set_sval(p.sources,360,90,90,73,82,0)

@sensitivity
def src_now(p):
    # Not clear in kph should be 360 (recovery) or 342 (normal) here
    set_sval(p.sources,360,90,92,73,91,79)

@sensitivity
def src_ndr(p):
    # Note this is at a different speed from the above - 320kph vs 360kph
    set_sval(p.sources,320,89,88,73,88,76)

@sensitivity
def src_none(p):
    set_sval(p.sources,320,0,0,0,0,0)

@sensitivity
def src_rolling_zero(p):
    p.sources["rolling"].sval = 0

@sensitivity
def src_rolling_only(p):
    # p.sources["rolling"].sval = 0
    p.sources["aero"].sval = 0
    p.sources["startup"].sval = 0
    p.sources["panto"].sval = 0
    p.sources["pantowell"].sval = 0

@sensitivity
def src_aero_zero(p):
    p.sources["aero"].sval = 0

@sensitivity
def src_aero_only(p):
    p.sources["rolling"].sval = 0
    # p.sources["aero"].sval = 0
    p.sources["startup"].sval = 0
    p.sources["panto"].sval = 0
    p.sources["pantowell"].sval = 0


@sensitivity
def src_startup_zero(p):
    p.sources["startup"].sval = 0.0

@sensitivity
def src_startup_only(p):
    p.sources["rolling"].sval = 0
    p.sources["aero"].sval = 0
    # p.sources["startup"].sval = 0
    p.sources["panto"].sval = 0
    p.sources["pantowell"].sval = 0


@sensitivity
def src_panto_zero(p):
    p.sources["panto"].sval = 0

@sensitivity
def src_panto_only(p):
    p.sources["rolling"].sval = 0
    p.sources["aero"].sval = 0
    p.sources["startup"].sval = 0
    # p.sources["panto"].sval = 0
    p.sources["pantowell"].sval = 0


@sensitivity
def src_pantowell_zero(p):
    p.sources["pantowell"].sval = 0

@sensitivity
def src_pantowell_only(p):
    p.sources["rolling"].sval = 0
    p.sources["aero"].sval = 0
    p.sources["startup"].sval = 0
    p.sources["panto"].sval = 0
    # p.sources["pantowell"].sval = 0


@sensitivity
def sht_plus_10_percent(p):
    factor_sht(p.sources,1.1)

@sensitivity
def sht_minus_10_percent(p):
    factor_sht(p.sources,1.0/1.1)

@sensitivity
def sht_minus_1(p):
    shift_sht(p.sources,-1)

@sensitivity
def sht_plus_1(p):
    shift_sht(p.sources,+1)

@sensitivity
def kph_plus_10_percent(p):
    p.kph = p.kph * 1.1 

@sensitivity
def kph_minus_10_percent(p):
    p.kph = p.kph / 1.1 

@sensitivity
def railht_plus_10_percent(p):
    p.railht = p.railht * 1.1 

@sensitivity
def railht_minus_10_percent(p):
    p.railht = p.railht / 1.1 

@sensitivity
def reverse_direction(p):
    if p.dirn == "n":
        p.dirn= "s"
        p.toffset -= 6.135
    elif p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def bht_zero(p):
    barriers = [p.barrier1,p.barrier2]
    for b in barriers:
        if b:
            b.bht = [0.0] * len(b.bht)

@sensitivity
def bht_plus_10_percent(p):
    barriers = [p.barrier1,p.barrier2]
    for b in barriers:
        if b:
           b.bht = [v * 1.1 for v in b.bht]

@sensitivity
def bht_minus_10_percent(p):
    barriers = [p.barrier1,p.barrier2]
    for b in barriers:
        if b:
           b.bht = [v / 1.1 for v in b.bht]

@sensitivity
def bpos_plus_10_percent(p):
    barriers = [p.barrier1,p.barrier2]
    for b in barriers:
        if b:
            b.bpos = [v * 1.1 for v in b.bpos]

@sensitivity
def bpos_minus_10_percent(p):
    barriers = [p.barrier1,p.barrier2]
    for b in barriers:
        if b:
            b.bpos = [v / 1.1 for v in b.bpos]

@sensitivity
def plen_zero(p):
    p.plen = 0.0

@sensitivity
def plen_plus_10_percent(p):
    p.plen = p.plen * 1.1

@sensitivity
def plen_minus_10_percent(p):
    p.plen = p.plen / 1.1

@sensitivity
def refpt_zero(p):
    p.refpt = 0.0

@sensitivity
def refpt_plus_10_percent(p):
    p.refpt = p.refpt * 1.1

@sensitivity
def refpt_minus_10_percent(p):
    p.refpt = p.refpt / 1.1

@sensitivity
def rht_1point8(p):
    p.rht = 1.8

@sensitivity
def rht_plus_10_percent(p):
    p.rht = p.rht * 1.1

@sensitivity
def rht_minus_10_percent(p):
    p.rht = p.rht / 1.1

# @sensitivity
# def tlen_x2(p):
#     p.tlen = p.tlen * 2

# @sensitivity
# def tlen_200(p):
#     p.tlen = 200.0

# @sensitivity
# def tlen_400(p):
#     p.tlen = 400.0

@sensitivity
def tlen_slen_x2(p):
    p.tlen = p.tlen * 2
    p.slen = p.slen * 2

@sensitivity
def tlen_slen_x4(p):
    p.tlen = p.tlen * 4
    p.slen = p.slen * 4

@sensitivity
def down_330kph(p):
    p.kph = 330.0
    if p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def up_330kph(p):
    p.kph = 330.0
    if p.dirn == "n":
        p.dirn = "s"
        p.toffset -= 6.135

@sensitivity
def down_360kph(p):
    p.kph = 360.0
    if p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def up_360kph(p):
    p.kph = 360.0
    if p.dirn == "n":
        p.dirn = "s"
        p.toffset -= 6.135

@sensitivity
def down_342kph(p):
    p.kph = 342.0
    if p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def up_342kph(p):
    p.kph = 342.0
    if p.dirn == "n":
        p.dirn = "s"
        p.toffset -= 6.135

@sensitivity
def down_299kph(p):
    p.kph = 299.0
    if p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def up_299kph(p):
    p.kph = 299.0
    if p.dirn == "n":
        p.dirn = "s"
        p.toffset -= 6.135

@sensitivity
def down_299kph(p):
    p.kph = 299.0
    if p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def up_300kph(p):
    p.kph = 300.0
    if p.dirn == "n":
        p.dirn = "s"
        p.toffset -= 6.135

@sensitivity
def down_300kph(p):
    p.kph = 300.0
    if p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def up_315kph(p):
    p.kph = 315.0
    if p.dirn == "n":
        p.dirn = "s"
        p.toffset -= 6.135

@sensitivity
def down_328kph(p):
    p.kph = 328.0
    if p.dirn == "s":
        p.dirn = "n"
        p.toffset += 6.135

@sensitivity
def up_328kph(p):
    p.kph = 328.0
    if p.dirn == "n":
        p.dirn = "s"
        p.toffset -= 6.135


def factor_sht(sources,factor):
    sources["rolling"].sht = sources["rolling"].sht * factor
    sources["aero"].sht = sources["aero"].sht * factor
    sources["startup"].sht = sources["startup"].sht * factor
    sources["panto"].sht = sources["panto"].sht * factor
    sources["pantowell"].sht = sources["pantowell"].sht * factor

def shift_sht(sources,shift):
    sources["rolling"].sht = sources["rolling"].sht + shift
    sources["aero"].sht = sources["aero"].sht + shift
    sources["startup"].sht = sources["startup"].sht + shift
    sources["panto"].sht = sources["panto"].sht + shift
    sources["pantowell"].sht = sources["pantowell"].sht + shift

def set_sval(sources,kph,rolling,aero,startup,panto,pantowell):

    if rolling > 0:
        sources["rolling"].sval = round(rolling - 30 * math.log10(kph),1)
    else:
        sources["rolling"].sval = 0.0

    if aero > 0:
        sources["aero"].sval = round(aero - 70 * math.log10(kph),1)
    else:
        sources["aero"].sval = 0.0

    sources["startup"].sval = startup

    if panto > 0:
        sources["panto"].sval = round(aero - 70 * math.log10(kph),1)
    else:
        sources["panto"].sval = 0.0

    if pantowell > 0:
        sources["pantowell"].sval = round(aero - 70 * math.log10(kph),1)
    else:
        sources["pantowell"].sval = 0.0
