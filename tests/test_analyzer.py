"""Unit tests for cycle analyzer and clinical statistics.
"""

import unittest
from datetime import date, timedelta
from cyclenest.analyzer import CycleAnalyzer
from cyclenest.models import DailyLog, FlowLevel, MucusType, CyclePhase


class TestCycleAnalyzer(unittest.TestCase):
    def test_cycle_detection_and_statistics(self):
        # Build 3 cycles: Cycle 1 = 28 days, Cycle 2 = 29 days, Cycle 3 ongoing
        base = date(2026, 1, 1)
        logs = []

        # Cycle 1: starts Jan 1, bleeds 5 days
        for i in range(5):
            logs.append(DailyLog(date=base + timedelta(days=i), flow=FlowLevel.HEAVY if i < 2 else FlowLevel.LIGHT))

        # Cycle 2: starts Jan 29 (28 days later), bleeds 4 days
        c2_start = base + timedelta(days=28)
        for i in range(4):
            logs.append(DailyLog(date=c2_start + timedelta(days=i), flow=FlowLevel.HEAVY if i < 2 else FlowLevel.LIGHT))

        # Cycle 3: starts Feb 27 (29 days later), bleeds 5 days
        c3_start = c2_start + timedelta(days=29)
        for i in range(5):
            logs.append(DailyLog(date=c3_start + timedelta(days=i), flow=FlowLevel.HEAVY if i < 2 else FlowLevel.LIGHT))

        analyzer = CycleAnalyzer(logs)
        self.assertEqual(len(analyzer.cycles), 3)

        completed = analyzer.get_completed_cycles()
        self.assertEqual(len(completed), 2)
        self.assertEqual(completed[0].length_days, 28)
        self.assertEqual(completed[1].length_days, 29)

        stats = analyzer.compute_statistics()
        self.assertEqual(stats["completed_cycles"], 2)
        self.assertEqual(stats["mean_cycle_length"], 28.5)
        self.assertIn("Regular", stats["regularity_status"])

    def test_phase_determination(self):
        start = date(2026, 5, 1)
        logs = [
            DailyLog(date=start, flow=FlowLevel.HEAVY),
            DailyLog(date=start + timedelta(days=1), flow=FlowLevel.HEAVY),
            DailyLog(date=start + timedelta(days=2), flow=FlowLevel.LIGHT),
        ]
        analyzer = CycleAnalyzer(logs, default_cycle_length=28, default_period_length=5, default_luteal_length=14)

        # Day 1 -> Menstrual
        p1, d1, _ = analyzer.get_phase_for_date(start)
        self.assertEqual(p1, CyclePhase.MENSTRUAL)
        self.assertEqual(d1, 1)

        # Day 7 -> Follicular
        p7, d7, _ = analyzer.get_phase_for_date(start + timedelta(days=6))
        self.assertEqual(p7, CyclePhase.FOLLICULAR)
        self.assertEqual(d7, 7)

        # Day 14 -> Ovulation
        p14, d14, _ = analyzer.get_phase_for_date(start + timedelta(days=13))
        self.assertEqual(p14, CyclePhase.OVULATION)

        # Day 20 -> Luteal
        p20, d20, _ = analyzer.get_phase_for_date(start + timedelta(days=19))
        self.assertEqual(p20, CyclePhase.LUTEAL)

        # Day 26 -> Late Luteal PMS
        p26, d26, _ = analyzer.get_phase_for_date(start + timedelta(days=25))
        self.assertEqual(p26, CyclePhase.LATE_LUTEAL_PMS)


if __name__ == "__main__":
    unittest.main()
