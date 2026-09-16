#!/usr/bin/env python3
"""LEAN *-summary.json 핵심 지표만 출력한다. 백테스트를 다시 돌리지 않는다."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KEYS = (
    "Start Equity",
    "End Equity",
    "Net Profit",
    "Compounding Annual Return",
    "Sharpe Ratio",
    "Drawdown",
    "Total Orders",
    "Total Fees",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "summary",
        nargs="?",
        default="lean-results/SamsungBuyAndHold-summary.json",
        help="QuantConnect LEAN summary JSON path",
    )
    args = parser.parse_args()
    path = Path(args.summary)
    if not path.is_file():
        print(f"missing: {path}", file=sys.stderr)
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    stats = payload.get("statistics")
    if not isinstance(stats, dict):
        print("no statistics object", file=sys.stderr)
        return 1
    print(f"file\t{path}")
    for key in KEYS:
        if key in stats:
            print(f"{key}\t{stats[key]}")
    print("note\tCustom-data LEAN sample. Not a live trading signal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
