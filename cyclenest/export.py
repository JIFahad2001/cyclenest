"""Data Export and Import utilities (JSON & CSV) for CycleNest.
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import date

from cyclenest.models import DailyLog, FlowLevel, MucusType, SexualActivity


def export_to_json(logs: List[DailyLog], file_path: str | Path) -> int:
    """Export list of DailyLogs to a JSON file."""
    path = Path(file_path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    data = [l.to_dict() for l in logs]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return len(logs)


def export_to_csv(logs: List[DailyLog], file_path: str | Path) -> int:
    """Export list of DailyLogs to a clean CSV file."""
    path = Path(file_path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "date",
        "flow",
        "cramps_pain",
        "energy_level",
        "bbt",
        "mucus",
        "sexual_activity",
        "sleep_hours",
        "symptoms",
        "moods",
        "medications",
        "notes",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for log in logs:
            row = {
                "date": log.date.isoformat(),
                "flow": log.flow.value,
                "cramps_pain": log.cramps_pain,
                "energy_level": log.energy_level if log.energy_level is not None else "",
                "bbt": log.bbt if log.bbt is not None else "",
                "mucus": log.mucus.value,
                "sexual_activity": log.sexual_activity.value,
                "sleep_hours": log.sleep_hours if log.sleep_hours is not None else "",
                "symptoms": "; ".join(log.symptoms),
                "moods": "; ".join(log.moods),
                "medications": "; ".join(log.medications),
                "notes": log.notes,
            }
            writer.writerow(row)
    return len(logs)


def import_from_json(file_path: str | Path) -> List[DailyLog]:
    """Import DailyLogs from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logs: List[DailyLog] = []
    for item in data:
        logs.append(DailyLog.from_dict(item))
    return logs


def import_from_csv(file_path: str | Path) -> List[DailyLog]:
    """Import DailyLogs from a CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logs: List[DailyLog] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_val = date.fromisoformat(row["date"].strip())
            flow_val = FlowLevel.from_str(row.get("flow", "none"))
            cramps = int(row.get("cramps_pain") or 0)
            energy = int(row["energy_level"]) if row.get("energy_level") else None
            bbt = float(row["bbt"]) if row.get("bbt") else None
            mucus = MucusType.from_str(row.get("mucus", "none"))
            sex = SexualActivity.from_str(row.get("sexual_activity", "none"))
            sleep = float(row["sleep_hours"]) if row.get("sleep_hours") else None
            symptoms = [s.strip() for s in row.get("symptoms", "").split(";") if s.strip()]
            moods = [m.strip() for m in row.get("moods", "").split(";") if m.strip()]
            meds = [m.strip() for m in row.get("medications", "").split(";") if m.strip()]
            notes = row.get("notes", "")

            logs.append(
                DailyLog(
                    date=d_val,
                    flow=flow_val,
                    cramps_pain=cramps,
                    energy_level=energy,
                    bbt=bbt,
                    mucus=mucus,
                    sexual_activity=sex,
                    sleep_hours=sleep,
                    symptoms=symptoms,
                    moods=moods,
                    medications=meds,
                    notes=notes,
                )
            )
    return logs
