import csv
import math
import copy
from dataclasses import dataclass, fields, asdict
from typing import Dict, List
from datetime import datetime
from noisemodels import *
from noiseio import *
from noisecalc import *
from noisesensitivity import *

def run():

    # Generate a unique run ID of 14 characters from the system date time
    run = datetime.now().strftime("%Y%m%d%H%M%S")

    # Load the input data
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
    sresults = []

    for r in receptors.values():
        for p in params.values():
            print(f"Runs for receptor {r.key}, params {p.key}")

            # Base result for this receptor and parameter set
            (base_results,base_impact) = runscenario(run,r,p)
            results += base_results
            impacts.append(base_impact)

            # Now do some analysis on the sensitivity of the results to various
            # changes in the parameters
            basedb = base_impact.maxdb
            basespl = base_impact.sumspl 
            sresults.append(SensitivityResult(
                run=run,
                param=p.key,
                receptor=r.key,
                key="_baseline",
                db=0.0,
                spl=0.0,
                basedb=basedb,
                basespl=basespl,
                deltadb = basedb,
                deltaspl= basespl
            ))

            for f in sensitivity_funcs:
                sresults.append(runsensitivity(run,r,p,basedb,basespl,f))

    write_list_to_csv(impacts, f"noisedata/{run}_impacts.csv")
    write_list_to_csv(results, f"noisedata/{run}_results.csv")
    write_list_to_csv(sresults, f"noisedata/{run}_sresults.csv")

def runsensitivity(run,r,p,basedb,basespl,modify_param_func) -> SensitivityResult:

    key = modify_param_func.__name__

    print(f"Run sensitivity: {key}")

    q = copy.deepcopy(p)
    modify_param_func(q) 

    (results, impact) = runscenario(run,r,q)
    sresult = SensitivityResult(
        run=run,
        param=p.key,
        receptor=r.key,
        key=key,
        db=impact.maxdb,
        spl=impact.sumspl,
        basedb=basedb,
        basespl=basespl,
        deltadb= impact.maxdb-basedb,
        deltaspl= round(100*(impact.sumspl-basespl)/basespl,1)
    )

    return sresult

def runscenario(run,r,p) -> tuple[list[Result],Impact]:

    results = []

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
    
    # Furthest point of noise source from reference point
    offset = p.tlen + p.pstart + p.plen

    db = getNoise(p, r.x - p.refpt, r.y, offset)
    impact = Impact(
        run=run,
        param=p.key,
        receptor=r.key,
        impacts=r.impacts,
        db=roundTo(db,2),
        maxdb= max(r.db for r in results),
        sumspl= sum(r.spl for r in results)
    )

    return (results, impact)

