"""SQLite Database Access Layer for CycleNest.
"""

from __future__ import annotations
import sqlite3
import json
import os
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from cyclenest.models import DailyLog, FlowLevel, MucusType, SexualActivity


DEFAULT_DB_DIR = Path.home() / ".cyclenest"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "cyclenest.db"


class Database:
    def __init__(self, db_path: Optional[str | Path] = None):
        self._mem_conn: Optional[sqlite3.Connection] = None
        if db_path is None:
            DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
            self.db_path = str(DEFAULT_DB_PATH)
        elif str(db_path) == ":memory:":
            self.db_path = ":memory:"
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
        else:
            p = Path(db_path)
            if p.parent and not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = str(p)

        self._init_tables()

    def get_connection(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_logs (
                    date TEXT PRIMARY KEY,
                    flow TEXT NOT NULL,
                    cramps_pain INTEGER NOT NULL DEFAULT 0,
                    energy_level INTEGER,
                    bbt REAL,
                    mucus TEXT,
                    sexual_activity TEXT,
                    sleep_hours REAL,
                    symptoms_json TEXT,
                    moods_json TEXT,
                    medications_json TEXT,
                    notes TEXT,
                    updated_at TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            # Pre-populate sensible defaults if empty
            defaults = {
                "temp_unit": "C",
                "default_cycle_length": "28",
                "default_period_length": "5",
                "default_luteal_length": "14",
                "user_name": "Friend",
            }
            for k, v in defaults.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v)
                )
            conn.commit()

    def save_daily_log(self, log: DailyLog) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO daily_logs (
                    date, flow, cramps_pain, energy_level, bbt, mucus,
                    sexual_activity, sleep_hours, symptoms_json, moods_json,
                    medications_json, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    flow = excluded.flow,
                    cramps_pain = excluded.cramps_pain,
                    energy_level = excluded.energy_level,
                    bbt = excluded.bbt,
                    mucus = excluded.mucus,
                    sexual_activity = excluded.sexual_activity,
                    sleep_hours = excluded.sleep_hours,
                    symptoms_json = excluded.symptoms_json,
                    moods_json = excluded.moods_json,
                    medications_json = excluded.medications_json,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (
                    log.date.isoformat(),
                    log.flow.value,
                    log.cramps_pain,
                    log.energy_level,
                    log.bbt,
                    log.mucus.value,
                    log.sexual_activity.value,
                    log.sleep_hours,
                    json.dumps(log.symptoms, ensure_ascii=False),
                    json.dumps(log.moods, ensure_ascii=False),
                    json.dumps(log.medications, ensure_ascii=False),
                    log.notes,
                    now_iso,
                ),
            )
            conn.commit()

    def batch_save_logs(self, logs: List[DailyLog]) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            for log in logs:
                cursor.execute(
                    """
                    INSERT INTO daily_logs (
                        date, flow, cramps_pain, energy_level, bbt, mucus,
                        sexual_activity, sleep_hours, symptoms_json, moods_json,
                        medications_json, notes, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        flow = excluded.flow,
                        cramps_pain = excluded.cramps_pain,
                        energy_level = excluded.energy_level,
                        bbt = excluded.bbt,
                        mucus = excluded.mucus,
                        sexual_activity = excluded.sexual_activity,
                        sleep_hours = excluded.sleep_hours,
                        symptoms_json = excluded.symptoms_json,
                        moods_json = excluded.moods_json,
                        medications_json = excluded.medications_json,
                        notes = excluded.notes,
                        updated_at = excluded.updated_at
                    """,
                    (
                        log.date.isoformat(),
                        log.flow.value,
                        log.cramps_pain,
                        log.energy_level,
                        log.bbt,
                        log.mucus.value,
                        log.sexual_activity.value,
                        log.sleep_hours,
                        json.dumps(log.symptoms, ensure_ascii=False),
                        json.dumps(log.moods, ensure_ascii=False),
                        json.dumps(log.medications, ensure_ascii=False),
                        log.notes,
                        now_iso,
                    ),
                )
            conn.commit()

    def _row_to_log(self, row: sqlite3.Row) -> DailyLog:
        return DailyLog(
            date=date.fromisoformat(row["date"]),
            flow=FlowLevel.from_str(row["flow"]),
            cramps_pain=int(row["cramps_pain"]),
            energy_level=row["energy_level"],
            bbt=float(row["bbt"]) if row["bbt"] is not None else None,
            mucus=MucusType.from_str(row["mucus"]) if row["mucus"] else MucusType.NONE,
            sexual_activity=SexualActivity.from_str(row["sexual_activity"]) if row["sexual_activity"] else SexualActivity.NONE,
            sleep_hours=float(row["sleep_hours"]) if row["sleep_hours"] is not None else None,
            symptoms=json.loads(row["symptoms_json"]) if row["symptoms_json"] else [],
            moods=json.loads(row["moods_json"]) if row["moods_json"] else [],
            medications=json.loads(row["medications_json"]) if row["medications_json"] else [],
            notes=row["notes"] or "",
        )

    def get_daily_log(self, log_date: date) -> Optional[DailyLog]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM daily_logs WHERE date = ?", (log_date.isoformat(),)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_log(row)
        return None

    def get_all_daily_logs(self) -> List[DailyLog]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_logs ORDER BY date ASC")
            rows = cursor.fetchall()
            return [self._row_to_log(r) for r in rows]

    def get_logs_in_range(self, start_date: date, end_date: date) -> List[DailyLog]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM daily_logs WHERE date >= ? AND date <= ? ORDER BY date ASC",
                (start_date.isoformat(), end_date.isoformat()),
            )
            rows = cursor.fetchall()
            return [self._row_to_log(r) for r in rows]

    def delete_daily_log(self, log_date: date) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM daily_logs WHERE date = ?", (log_date.isoformat(),)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_total_log_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM daily_logs")
            return int(cursor.fetchone()[0])

    def get_setting(self, key: str, default: str = "") -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return str(row["value"])
        return default

    def set_setting(self, key: str, value: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
            conn.commit()

    def clear_all(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM daily_logs")
            conn.commit()
