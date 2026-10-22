#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (from the README):
- Skip lines that can't be read, and events without a txn_id.
- A payment can be attempted more than once; only the latest attempt for each
  txn_id counts (latest by ts, not by position in the file).
- A payment counts as collected only if its latest attempt is "success".
"""
import json
from decimal import Decimal


def parse_amount(value):
    """Amounts are numbers or strings like "4,804.15"."""
    return Decimal(str(value).replace(",", "").strip())


# txn_id -> (ts, line_number, event). ts is ISO 8601 UTC with a trailing Z, so
# comparing the strings orders them in time; the line number breaks ties.
latest = {}

with open("payments.jsonl", encoding="utf-8") as f:
    for line_number, line in enumerate(f):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        txn_id = event.get("txn_id")
        if not txn_id:
            continue
        key = (event["ts"], line_number)
        if txn_id not in latest or key > latest[txn_id][:2]:
            latest[txn_id] = (event["ts"], line_number, event)

total = Decimal(0)
count = 0
for _, _, event in latest.values():
    if event["status"] == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
