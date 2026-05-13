from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


# =========================
# 1. Core Value States
# =========================

# Supported rule evaluation checks
class MatchFieldState(str, Enum):
    MATCH = "match"
    NOMATCH = "nomatch"
    MISSING = "missing"
    UNKNOWN = "unknown"


#=========================
# 2. Match Check  
#=========================

# Supported rule evaluation checks
class MatchCheck(str, Enum):

    MATCH = "match"
    NOMATCH = "nomatch"
    MISSING = "missing"
    UNKNOWN = "unknown"

    NOT_MATCH = "not_match"
    NOT_NOMATCH = "not_nomatch"
    NOT_MISSING = "not_missing"
    NOT_UNKNOWN = "not_unknown"



#=========================
# 3. Operators 
#=========================

# Supported identity fields used in rule evaluation
class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"


# ================================
# 4. Assumption: Full Match Fields, and Required Columns
# ================================

# Supported identity fields used in rule evaluation
class FullMatchField(str, Enum):

    FIRSTINITIAL = "firstinitial"
    FIRSTNAME = "firstname"
    MIDDLENAME = "middlename"
    LASTNAME = "lastname"

    DAYOFBIRTH = "dayofbirth"
    MONTHOFBIRTH = "monthofbirth"
    YEAROFBIRTH = "yearofbirth"

    STREETNAME = "streetname"
    STREETNUMBER = "streetnumber"
    STREETTYPE = "streettype"

    CITY = "city"
    REGION = "region"
    POSTALCODE = "postalcode"

    UNITNUMBER = "unitnumber"
    ADDRESS1 = "address1"

    TAXID = "taxid"
    SOCIALINSURANCENUMBER = "socialinsurancenumber"
    VOTERID = "voterid"

    GENDER = "gender"

# Required columns for input datasets
class RequiredColumn(str, Enum):

    RECORD_ID = "recordid"
    DATASOURCE = "datasource"
    TRUMATCH_CONFIDENCE = "trumatch_confidence"


# =========================
# 5. Field-level result
# =========================
# Result for a single field comparison
@dataclass
class FieldResult:
    field_name: str
    state: MatchFieldState


# =========================
# 6. Datasource result (per user per source)
# =========================
# Evaluation result from one datasource
@dataclass
class DataSourceResult:
    datasource_id: str
    fields: Dict[str, MatchFieldState]
    confidence: float  # TruMatch score


# =========================
# 7. User record (core entity)
# =========================
# Aggregated datasource results for one record
@dataclass
class RecordEntry:
    record_id: str
    datasources: Dict[str, DataSourceResult]

