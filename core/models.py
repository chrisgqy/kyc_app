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


# =========================
# 5. Rule definition
# =========================

@dataclass
class Rule:
    rule_id: str
    expression: str  # raw rule string


# =========================
# 6. Rule evaluation result
# =========================

@dataclass
class RuleEvaluationResult:
    record_id: str
    rule_id: str
    datasource_id: str
    passed: bool
    confidence: Optional[float]


# =========================
# 7. Final onboarding decision
# =========================

@dataclass
class OnboardingResult:
    record_id: str
    is_approved: bool
    rules_satisfied: Dict[str, str]  # rule_id → datasource_id
    datasource_coverage: int  # how many of 8 sources used
    max_confidence: float