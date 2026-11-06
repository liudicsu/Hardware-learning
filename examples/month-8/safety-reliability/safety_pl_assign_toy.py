#!/usr/bin/env python3
"""Pedagogic S/F/P risk graph -> required PLr ONLY, never achieved PL.
ISO 13849-1:2023 edition metadata verified on ISO catalogue; secondary risk
literacy: Pilz EN ISO 13849-1 page. No automatic risk selection from robot type.
User supplies S/F/P for each named safety function in a JSON list.
Missing/null/empty field -> insufficient_data; bad values -> invalid_input.
This intentionally excludes application-specific Type-C requirements and any
probability-based adjustment; not a complete ISO assessment or certification.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

GRAPH = {
    ("S1", "F1", "P1"): "a", ("S1", "F1", "P2"): "b",
    ("S1", "F2", "P1"): "b", ("S1", "F2", "P2"): "c",
    ("S2", "F1", "P1"): "c", ("S2", "F1", "P2"): "d",
    ("S2", "F2", "P1"): "d", ("S2", "F2", "P2"): "e",
}


def assign_plr(record):
    keys = ("application", "function", "S", "F", "P")
    if not isinstance(record, dict):
        return "invalid_input"
    if any(k not in record or record[k] is None or record[k] == "" for k in keys):
        return "insufficient_data"
    if any(not isinstance(record[k], str) for k in keys):
        return "invalid_input"
    return GRAPH.get(tuple(record[k] for k in ("S", "F", "P")), "invalid_input")


def self_test():
    expected = ("a", "b", "b", "c", "c", "d", "d", "e")
    base = {"application": "test", "function": "safe_stop"}
    for risk, plr in zip(itertools.product(("S1", "S2"), ("F1", "F2"), ("P1", "P2")), expected):
        row = dict(base, **dict(zip(("S", "F", "P"), risk)))
        assert assign_plr(row) == plr
        for key in row:
            missing = dict(row)
            del missing[key]
            assert assign_plr(missing) == "insufficient_data"
    assert assign_plr(dict(base, S="S3", F="F1", P="P1")) == "invalid_input"
    assert assign_plr(dict(base, S=[], F="F1", P="P1")) == "invalid_input"
    assert assign_plr(dict(base, S="S1", F="F1", P=None)) == "insufficient_data"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="user-supplied JSON list; no inferred S/F/P")
    args = parser.parse_args()
    rows = json.loads(args.input.read_text())
    if not isinstance(rows, list):
        parser.error("input must be a JSON list")
    self_test()
    print("method=S/F/P_base_risk_graph; edition=ISO_13849-1:2023; result=PLr_only")
    print("application function S F P result")
    for row in rows:
        fields = [str(row.get(k, "missing")) for k in ("application", "function", "S", "F", "P")] if isinstance(row, dict) else ["invalid"] * 5
        print(" ".join(fields), assign_plr(row))
    print("achieved_PL=out_of_scope: category,MTTFd,DCavg,CCF_needed")
    print("self_tests=8_branches+each_missing_field+invalid_values; toy_not_certification")


if __name__ == "__main__":
    main()
