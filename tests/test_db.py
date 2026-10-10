"""Unit tests for SQLite database operations.
"""

import unittest
from datetime import date
from cyclenest.db import Database
from cyclenest.models import DailyLog, FlowLevel, MucusType, SexualActivity


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def test_save_and_retrieve_log(self):
        log = DailyLog(
            date=date(2026, 10, 1),
            flow=FlowLevel.HEAVY,
            cramps_pain=3,
            bbt=36.4,
            mucus=MucusType.STICKY,
            sexual_activity=SexualActivity.PROTECTED,
            sleep_hours=7.5,
            symptoms=["Cramps", "Fatigue / Exhaustion"],
            moods=["Irritable / Snappy"],
            notes="Felt tired today",
        )
        self.db.save_daily_log(log)

        retrieved = self.db.get_daily_log(date(2026, 10, 1))
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.flow, FlowLevel.HEAVY)
        self.assertEqual(retrieved.cramps_pain, 3)
        self.assertEqual(retrieved.bbt, 36.4)
        self.assertEqual(retrieved.mucus, MucusType.STICKY)
        self.assertEqual(retrieved.sexual_activity, SexualActivity.PROTECTED)
        self.assertEqual(retrieved.sleep_hours, 7.5)
        self.assertIn("Cramps", retrieved.symptoms)
        self.assertIn("Irritable / Snappy", retrieved.moods)
        self.assertEqual(retrieved.notes, "Felt tired today")

    def test_update_existing_log(self):
        log1 = DailyLog(date=date(2026, 10, 2), flow=FlowLevel.LIGHT, cramps_pain=1)
        self.db.save_daily_log(log1)

        log2 = DailyLog(date=date(2026, 10, 2), flow=FlowLevel.HEAVY, cramps_pain=4)
        self.db.save_daily_log(log2)

        retrieved = self.db.get_daily_log(date(2026, 10, 2))
        self.assertEqual(retrieved.flow, FlowLevel.HEAVY)
        self.assertEqual(retrieved.cramps_pain, 4)

    def test_delete_log(self):
        log = DailyLog(date=date(2026, 10, 3), flow=FlowLevel.MEDIUM)
        self.db.save_daily_log(log)
        self.assertTrue(self.db.delete_daily_log(date(2026, 10, 3)))
        self.assertIsNone(self.db.get_daily_log(date(2026, 10, 3)))

    def test_settings(self):
        self.db.set_setting("temp_unit", "F")
        self.assertEqual(self.db.get_setting("temp_unit"), "F")
        self.assertEqual(self.db.get_setting("non_existent", "default_val"), "default_val")


if __name__ == "__main__":
    unittest.main()
