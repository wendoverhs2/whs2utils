import math

EPS = 1e-12

def dB(spl):
    # spl is linear SPL (power). Avoid log10 of 0 or negative.
    sv = max(spl, EPS)
    return 10.0 * math.log10(sv)

def spl(dB_value):
    # dB_value in dB, returns linear power
    return 10.0 ** (dB_value / 10.0)

def log_sum(levels):
    return dB(sum(spl(L) for L in levels))

def roundTo(num, places):
    # JS version uses string exponent shifting ("1.23e+2") to round to places.
    # Python equivalent is round(num, places), but:
    #   ⚠️ JS Math.round rounds half away from zero (0.5 -> 1, -0.5 -> -1)
    #   ⚠️ Python round uses "banker's rounding" (to even: -0.5 -> 0)
    # If exact JS behaviour is needed, must reimplement.
    return round(num, places)

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

