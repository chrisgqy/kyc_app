from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


# =========================
# 1. Core Value States
# =========================

class MatchFieldState(str, Enum):
    MATCH = "match"
    NOMATCH = "nomatch"
    MISSING = "missing"
    UNKNOWN = "unknown"


#=========================
# 2. Match Check  
#=========================

class MatchCheck(str, Enum):

    MATCH = "match"
    NOMATCH = "nomatch"
    MISSING = "missing"
    UNKNOWN = "unknown"

    NOT_MATCH = "not_match"
    NOT_NOMATCH = "not_nomatch"
    NOT_MISSING = "not_missing"
    NOT_UNKNOWN = "not_unknown"



# =========================
# 2. Field-level result
# =========================

@dataclass
class FieldResult:
    field_name: str
    state: MatchFieldState


# =========================
# 3. Datasource result (per user per source)
# =========================

@dataclass
class DataSourceResult:
    datasource_id: str
    fields: Dict[str, MatchFieldState]
    confidence: float  # TruMatch score


# =========================
# 4. User record (core entity)
# =========================

@dataclass
class RecordEntry:
    record_id: str
    datasources: Dict[str, DataSourceResult]


