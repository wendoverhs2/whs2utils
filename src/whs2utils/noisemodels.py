import math
from dataclasses import dataclass, fields, asdict
from typing import Dict, List
from noisecore import *

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
    v: int
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
    toffset: float
    barrier1: Barrier
    barrier2: Barrier
    sources: Dict[str,Source]

@dataclass
class Impact:
    run: str
    param: str
    receptor: str
    impacts: float
    db: float
    maxdb: float
    sumspl: float

@dataclass
class SensitivityResult:
    run: str
    param: str
    receptor: str
    key: str
    db: float
    spl: float
    basedb: float
    basespl: float
    deltadb: float
    deltaspl: float

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