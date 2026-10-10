"""Unit tests for the multiple prediction models and ensemble.
"""

import unittest
from datetime import date, timedelta
from cyclenest.models import Cycle, DailyLog, MucusType
from cyclenest.predictor import (
    WeightedMovingAveragePredictor,
    BayesianNormalPredictor,
    SymptoThermalBiomarkerPredictor,
    TrendHoltSmoothingPredictor,
    EnsembleCyclePredictor,
)


class TestPredictors(unittest.TestCase):
    def setUp(self):
        # 4 completed cycles of lengths: 28, 29, 28, 30
        c1 = Cycle(cycle_number=1, start_date=date(2026, 1, 1), end_date=date(2026, 1, 28), length_days=28)
        c2 = Cycle(cycle_number=2, start_date=date(2026, 1, 29), end_date=date(2026, 2, 26), length_days=29)
        c3 = Cycle(cycle_number=3, start_date=date(2026, 2, 27), end_date=date(2026, 3, 26), length_days=28)
        c4 = Cycle(cycle_number=4, start_date=date(2026, 3, 27), end_date=date(2026, 4, 25), length_days=30)
        self.completed_cycles = [c1, c2, c3, c4]
        self.current_cycle = Cycle(cycle_number=5, start_date=date(2026, 4, 26))
        self.recent_logs = []

    def test_wma_predictor(self):
        model = WeightedMovingAveragePredictor()
        res = model.predict(self.completed_cycles, self.current_cycle, self.recent_logs)
        self.assertAlmostEqual(res.predicted_cycle_length, 29.0, delta=1.5)
        self.assertGreater(res.confidence_score, 0.70)
        self.assertLess(res.fertile_window_start, res.ovulation_date)
        self.assertEqual(res.next_period_start, self.current_cycle.start_date + timedelta(days=round(res.predicted_cycle_length)))

    def test_bayesian_predictor(self):
        model = BayesianNormalPredictor()
        res = model.predict(self.completed_cycles, self.current_cycle, self.recent_logs)
        self.assertAlmostEqual(res.predicted_cycle_length, 28.7, delta=1.5)
        self.assertGreater(res.confidence_score, 0.75)
        self.assertLess(res.confidence_interval_80[0], res.next_period_start)
        self.assertGreater(res.confidence_interval_80[1], res.next_period_start)

    def test_biomarker_predictor_with_peak_mucus(self):
        model = SymptoThermalBiomarkerPredictor()
        # Log peak fertile mucus on Day 14
        ovulation_day = self.current_cycle.start_date + timedelta(days=14)
        logs = [DailyLog(date=ovulation_day, mucus=MucusType.EGG_WHITE)]
        res = model.predict(self.completed_cycles, self.current_cycle, logs)
        self.assertEqual(res.ovulation_date, ovulation_day)
        self.assertEqual(res.next_period_start, ovulation_day + timedelta(days=14))
        self.assertGreaterEqual(res.confidence_score, 0.90)

    def test_holt_trend_predictor(self):
        model = TrendHoltSmoothingPredictor()
        res = model.predict(self.completed_cycles, self.current_cycle, self.recent_logs)
        self.assertTrue(25.0 <= res.predicted_cycle_length <= 35.0)

    def test_ensemble_consensus_and_forecast(self):
        ensemble = EnsembleCyclePredictor()
        res = ensemble.predict(self.completed_cycles, self.current_cycle, self.recent_logs)
        self.assertAlmostEqual(res.predicted_cycle_length, 28.9, delta=1.5)

        # Multi-cycle projection
        forecasts = ensemble.forecast_upcoming_cycles(
            count=3,
            completed_cycles=self.completed_cycles,
            current_cycle=self.current_cycle,
            recent_logs=self.recent_logs,
        )
        self.assertEqual(len(forecasts), 3)
        self.assertLess(forecasts[0].next_period_start, forecasts[1].next_period_start)
        self.assertLess(forecasts[1].next_period_start, forecasts[2].next_period_start)


if __name__ == "__main__":
    unittest.main()
