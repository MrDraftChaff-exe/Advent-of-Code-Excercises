"""Starter-kit quantities. These numbers are embossed on the parts."""

# 20 unique run parts. Some are more than one printed piece.
# piece id, starter quantity, human name, parent part id
PIECES = [
    ("FN", 1, "Funnel start", "FN"),
    ("T1", 4, "Short tube", "T1"),
    ("T2", 4, "Medium tube", "T2"),
    ("T3", 6, "Long tube", "T3"),
    ("CL", 2, "Curve left 90", "CL"),
    ("CR", 2, "Curve right 90", "CR"),
    ("CU", 1, "U-turn 180", "CU"),
    ("SP", 1, "Spiral drop", "SP"),
    ("WF", 1, "Waterfall", "WF"),
    ("WF-C", 1, "Waterfall cover", "WF"),
    ("YS", 1, "Splitter", "YS"),
    ("MG", 1, "Merger", "MG"),
    ("SW-B", 1, "Seesaw base", "SW"),
    ("SW-A", 1, "Seesaw beam", "SW"),
    ("SW-P", 1, "Seesaw pin", "SW"),
    ("LP-A", 1, "Loop track", "LP"),
    ("LP-B", 1, "Loop cover", "LP"),
    ("LP-C", 1, "Loop entry", "LP"),
    ("LP-D", 1, "Loop exit", "LP"),
    ("EL-B", 1, "Elevator base", "EL"),
    ("EL-W", 1, "Elevator wheel", "EL"),
    ("EL-C", 1, "Elevator crank", "EL"),
    ("ZZ", 1, "Zigzag brake", "ZZ"),
    ("JP", 1, "Jump ramp", "JP"),
    ("LD", 1, "Jump landing", "LD"),
    ("SN-B", 1, "Spinner base", "SN"),
    ("SN-W", 1, "Spinner wheel", "SN"),
    ("SN-C", 1, "Spinner cap", "SN"),
    ("ST-P", 8, "Support post", "ST"),
    ("ST-Y", 8, "Support clip", "ST"),
    ("BX", 1, "Finish box", "BX"),
    ("FIT", 1, "Hinge fit coupon", "FIT"),
    ("LG", 1, "Legend and ball gauge", "LG"),
]

PART_IDS = [
    "FN", "T1", "T2", "T3", "CL", "CR", "CU", "SP", "WF", "YS",
    "MG", "SW", "LP", "EL", "ZZ", "JP", "LD", "SN", "ST", "BX",
]
