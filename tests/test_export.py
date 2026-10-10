"""Unit tests for JSON and CSV import and export.
"""

import unittest
import tempfile
import os
from datetime import date
from cyclenest.models import DailyLog, FlowLevel, MucusType
from cyclenest.export import export_to_json, import_from_json, export_to_csv, import_from_csv


class TestExportImport(unittest.TestCase):
    def setUp(self):
        self.test_logs = [
            DailyLog(
                date=date(2026, 10, 1),
                flow=FlowLevel.HEAVY,
                cramps_pain=3,
                bbt=36.35,
                mucus=MucusType.STICKY,
                symptoms=["Cramps", "Fatigue / Exhaustion"],
                moods=["Irritable / Snappy"],
                notes="Day 1 flow",
            ),
            DailyLog(
                date=date(2026, 10, 2),
                flow=FlowLevel.MEDIUM,
                cramps_pain=2,
                bbt=36.38,
                mucus=MucusType.CREAMY,
                symptoms=["Cramps"],
                moods=["Calm / Balanced"],
                notes="Day 2 flow",
            ),
        ]

    def test_json_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_path = tf.name

        try:
            count = export_to_json(self.test_logs, temp_path)
            self.assertEqual(count, 2)
            imported = import_from_json(temp_path)
            self.assertEqual(len(imported), 2)
            self.assertEqual(imported[0].date, date(2026, 10, 1))
            self.assertEqual(imported[0].flow, FlowLevel.HEAVY)
            self.assertEqual(imported[0].symptoms, ["Cramps", "Fatigue / Exhaustion"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_csv_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
            temp_path = tf.name

        try:
            count = export_to_csv(self.test_logs, temp_path)
            self.assertEqual(count, 2)
            imported = import_from_csv(temp_path)
            self.assertEqual(len(imported), 2)
            self.assertEqual(imported[0].date, date(2026, 10, 1))
            self.assertEqual(imported[0].flow, FlowLevel.HEAVY)
            self.assertEqual(imported[1].flow, FlowLevel.MEDIUM)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
