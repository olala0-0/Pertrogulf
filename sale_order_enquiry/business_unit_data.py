# -*- coding: utf-8 -*-

BUSINESS_UNIT_SELECTION = [
    ("pg_marine", "PG-Marine"),
    ("pg_auto", "PG-Auto"),
    ("pg_powerx", "PG-PowerX"),
    ("pg_aviation", "PG-Aviation"),
    ("pg_tblnd", "PG-Toll Blending"),
    ("pg_sing", "PG-SING"),
    ("pg_greece", "PG-GREECE"),
    ("pg_golden", "PG-GOLDEN"),
    ("pg_fujairah", "PG-FUJAIRAH"),
    ("pg_ajman", "PG-AJMAN"),
]

BUSINESS_UNIT_PREFIX_MAP = {
    "pg_marine": "PG-MARINE",
    "pg_auto": "PG-AUTO",
    "pg_powerx": "PG-POWERX",
    "pg_aviation": "PG-AVIATION",
    "pg_tblnd": "PG-TBLND",
    "pg_sing": "PG-SING",
    "pg_greece": "PG-GREECE",
    "pg_golden": "PG-GOLDEN",
    "pg_fujairah": "PG-FUJAIRAH",
    "pg_ajman": "PG-AJMAN",
}


def get_business_unit_prefix(business_unit):
    """Return sequence/report prefix for a business unit code."""
    return BUSINESS_UNIT_PREFIX_MAP.get(business_unit)
