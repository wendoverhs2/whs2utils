import csv
from dataclasses import dataclass
from typing import Dict, List

def run():
    print("Loading receptors")
    receptors = load_receptors_csv("noisedata/WHS2 Noise Analysis 2025 - Receptors.csv")
    print(f"Loaded {len(receptors)} receptors")
    print("Loading barriers")
    barriers = load_barriers_csv("noisedata/WHS2 Noise Analysis 2025 - Barriers.csv")
    print(f"Loaded {len(barriers)} barriers")
    print("Loading params")
    params = load_params_csv("noisedata/WHS2 Noise Analysis 2025 - Params.csv", barriers)
    print(f"Loaded {len(params)} params")

    for receptor in receptors.values():
        for param in params.values():
            print(f"Receptor: {receptor.key} Param: {param.key}")
    
@dataclass
class Barrier:
    key: str
    bht: List[float]
    bpos: List[float]

def parse_float_list(value: str) -> List[float]:
    """Convert a + separated string into a list of floats."""
    return [float(v) for v in value.split("+") if v.strip()]


def load_barriers_csv(file_path: str) -> Dict[str, Barrier]:
    barriers: Dict[str, Barrier] = {}
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bht = parse_float_list(row["bht"])
            bpos = parse_float_list(row["bpos"])

            if len(bht) != len(bpos):
                raise ValueError(f"Barrier {row['key']} has mismatched bht/bpos lengths")

            barrier = Barrier(
                key=row["key"],
                bht=bht,
                bpos=bpos,
            )
            barriers[barrier.key] = barrier
    return barriers

@dataclass
class Receptor:
    key: str
    x: float
    y: float
    impacts: float


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

def load_params_csv(file_path: str, barriers: Dict[str,Barrier]) -> Dict[str, Param]:
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
                barrier2=barriers[row["barrier2"]]
            )
            params[param.key] = param
    return params