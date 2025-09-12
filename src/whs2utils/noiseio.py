import csv
from noisemodels import *
from typing import Dict, List

def parse_float_list(value: str) -> List[float]:
    """Convert a + separated string into a list of floats."""
    return [float(v) for v in value.split("+") if v.strip()]


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
                v=int(row["v"]),
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
                toffset=float(row["toffset"]),
                barrier1=barriers[row["barrier1"]],
                barrier2=barriers[row["barrier2"]],
                sources=sourcesets[row["sources"]]
            )
            
            if (param.dirn=="s" and param.toffset > 0.0) or (param.dirn=="n" and param.toffset < 0.0):
                # toffset is the offset of the source from the mid-point of the two tracks
                raise ValueError("toffset must be positive for southbound or negative for northboard")

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