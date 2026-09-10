#!/usr/bin/env python3
"""Refresh selected full schema fragments from the pinned NIST release."""

import argparse
import datetime
import json
from pathlib import Path

from verify import EVIDENCE, NIST_SCHEMAS, _nist_schema


def refresh(name: str) -> None:
    path = Path(EVIDENCE) / f"{name}.json"
    record = json.loads(path.read_text())
    if record.get("fragment_note"):
        raise ValueError(f"{name}: partial fragments require an explicit extraction rule")
    model = "assessment-plan" if record["model"] == "shared" else record["model"]
    schema = _nist_schema(model)
    fragment = schema["definitions"][record["definition"]]
    record.update(model=model, schema_id=schema.get("$id", schema.get("id")),
                  oscal_version="1.2.1", fragment=fragment)
    record["provenance"] = f"Extracted from {NIST_SCHEMAS[model]} at definitions/{record['definition']}."
    original = json.loads(path.read_text())
    if record != original:
        record["fetched_at"] = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(f"{name}: verified against NIST OSCAL 1.2.1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="+", choices=[p.stem for p in Path(EVIDENCE).glob("*.json")])
    for item in parser.parse_args().names:
        refresh(item)