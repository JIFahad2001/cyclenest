"""Multi-Model Prediction Suite for Menstrual Cycles, Fertile Windows, and Ovulation.
"""

from __future__ import annotations
import math
from datetime import date, timedelta
from typing import List, Optional, Tuple, Dict, Any

from cyclenest.models import (
    Cycle,
    DailyLog,
    PredictionResult,
    MucusType,
)


class BaseCyclePredictor:
    """Base class for cycle prediction models."""

    def __init__(self, name: str):
        self.name = name

    def predict(
        self,
        completed_cycles: List[Cycle],
        current_cycle: Optional[Cycle],
        recent_logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> PredictionResult:
        raise NotImplementedError


class WeightedMovingAveragePredictor(BaseCyclePredictor):
    """Model 1: Exponentially Weighted Moving Average (EWMA / Recency-Weighted).
    Gives higher predictive weight to more recent cycles, adapting quickly to hormonal or lifestyle changes.
    """

    def __init__(self):
        super().__init__("Weighted Moving Average (EWMA)")

    def predict(
        self,
        completed_cycles: List[Cycle],
        current_cycle: Optional[Cycle],
        recent_logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> PredictionResult:
        valid_lens = [c.length_days for c in completed_cycles if c.length_days is not None]

        if not valid_lens:
            predicted_len = float(default_cycle_length)
            std_dev = 2.5
            confidence = 0.40
            explanation = f"Default clinical baseline ({default_cycle_length} days). No historical cycles recorded yet."
        elif len(valid_lens) == 1:
            predicted_len = float(valid_lens[0])
            std_dev = 2.0
            confidence = 0.55
            explanation = f"Based on 1 recorded cycle ({valid_lens[0]} days)."
        else:
            # Weighted average favoring newest cycles
            # Ex: 3 cycles -> weights [0.55, 0.30, 0.15]
            weights = []
            alpha = 0.45
            for i in range(len(valid_lens)):
                weights.append((1 - alpha) ** (len(valid_lens) - 1 - i))
            total_w = sum(weights)
            norm_weights = [w / total_w for w in weights]

            predicted_len = sum(w * l for w, l in zip(norm_weights, valid_lens))

            # Standard deviation
            variance = sum((l - predicted_len) ** 2 for l in valid_lens) / len(valid_lens)
            std_dev = max(1.5, math.sqrt(variance))
            confidence = min(0.92, 0.50 + 0.08 * len(valid_lens))
            explanation = (
                f"Recency-weighted average of {len(valid_lens)} cycles: "
                f"most recent cycles weighted up to {round(norm_weights[-1]*100)}%."
            )

        ref_start = current_cycle.start_date if current_cycle else date.today()
        round_len = round(predicted_len)

        next_start = ref_start + timedelta(days=round_len)
        ovulation = ref_start + timedelta(days=max(5, round_len - default_luteal_length))
        fertile_start = ovulation - timedelta(days=5)
        fertile_end = ovulation + timedelta(days=1)
        pms_start = next_start - timedelta(days=5)
        pms_end = next_start - timedelta(days=1)

        ci80_days = round(1.282 * std_dev)
        ci95_days = round(1.960 * std_dev)

        return PredictionResult(
            model_name=self.name,
            next_period_start=next_start,
            predicted_cycle_length=round(predicted_len, 1),
            confidence_interval_80=(
                next_start - timedelta(days=ci80_days),
                next_start + timedelta(days=ci80_days),
            ),
            confidence_interval_95=(
                next_start - timedelta(days=ci95_days),
                next_start + timedelta(days=ci95_days),
            ),
            fertile_window_start=fertile_start,
            fertile_window_end=fertile_end,
            ovulation_date=ovulation,
            pms_window_start=pms_start,
            pms_window_end=pms_end,
            confidence_score=confidence,
            explanation=explanation,
        )


class BayesianNormalPredictor(BaseCyclePredictor):
    """Model 2: Bayesian Normal Distribution / Probabilistic Predictor.
    Combines an informative gynecological prior distribution (mu=28.5, sigma=3.5)
    with the user's empirical data to produce calibrated credible intervals.
    """

    def __init__(self):
        super().__init__("Bayesian Normal Distribution")

    def predict(
        self,
        completed_cycles: List[Cycle],
        current_cycle: Optional[Cycle],
        recent_logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> PredictionResult:
        prior_mu = 28.5
        prior_var = 3.5 ** 2
        prior_precision = 1.0 / prior_var

        valid_lens = [c.length_days for c in completed_cycles if c.length_days is not None]
        n = len(valid_lens)

        if n == 0:
            post_mu = prior_mu
            post_std = 3.5
            confidence = 0.45
            explanation = f"Prior distribution based on population biology (mean {prior_mu}d, sd {post_std}d)."
        else:
            sample_mean = sum(valid_lens) / n
            sample_var = sum((x - sample_mean) ** 2 for x in valid_lens) / n if n > 1 else (2.5 ** 2)
            sample_var = max(sample_var, 1.5 ** 2)
            data_precision = n / sample_var

            post_precision = prior_precision + data_precision
            post_var = 1.0 / post_precision
            post_mu = (prior_precision * prior_mu + data_precision * sample_mean) / post_precision
            post_std = math.sqrt(post_var)

            confidence = min(0.95, 0.55 + 0.07 * n)
            explanation = (
                f"Bayesian update over {n} cycle(s): population prior "
                f"blended with empirical mean ({round(sample_mean, 1)}d)."
            )

        ref_start = current_cycle.start_date if current_cycle else date.today()
        round_len = round(post_mu)

        next_start = ref_start + timedelta(days=round_len)
        ovulation = ref_start + timedelta(days=max(5, round_len - default_luteal_length))
        fertile_start = ovulation - timedelta(days=5)
        fertile_end = ovulation + timedelta(days=1)
        pms_start = next_start - timedelta(days=5)
        pms_end = next_start - timedelta(days=1)

        ci80_days = max(1, round(1.282 * post_std))
        ci95_days = max(2, round(1.960 * post_std))

        return PredictionResult(
            model_name=self.name,
            next_period_start=next_start,
            predicted_cycle_length=round(post_mu, 1),
            confidence_interval_80=(
                next_start - timedelta(days=ci80_days),
                next_start + timedelta(days=ci80_days),
            ),
            confidence_interval_95=(
                next_start - timedelta(days=ci95_days),
                next_start + timedelta(days=ci95_days),
            ),
            fertile_window_start=fertile_start,
            fertile_window_end=fertile_end,
            ovulation_date=ovulation,
            pms_window_start=pms_start,
            pms_window_end=pms_end,
            confidence_score=confidence,
            explanation=explanation,
        )


class SymptoThermalBiomarkerPredictor(BaseCyclePredictor):
    """Model 3: Sympto-Thermal / Biomarker Dynamic Model (Fertility Awareness Method).
    Dynamically tracks real-time biomarkers in the active cycle (BBT thermal shift, fertile mucus).
    Once ovulation is confirmed by biomarkers, predicts period arrival based on personal luteal phase.
    """

    def __init__(self):
        super().__init__("Sympto-Thermal Biomarker (FAM)")

    def predict(
        self,
        completed_cycles: List[Cycle],
        current_cycle: Optional[Cycle],
        recent_logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> PredictionResult:
        ref_start = current_cycle.start_date if current_cycle else date.today()

        # Calculate personal historical luteal phase average if available
        known_luteals = [
            c.luteal_length_days for c in completed_cycles if c.luteal_length_days is not None
        ]
        luteal_len = round(sum(known_luteals) / len(known_luteals)) if known_luteals else default_luteal_length
        luteal_len = max(10, min(16, luteal_len))

        # Check current cycle logs for biomarker signals
        c_logs = [l for l in recent_logs if l.date >= ref_start]

        ovulation_detected_date: Optional[date] = None
        biomarker_reason = ""

        # 1. Check for egg-white cervical mucus in current cycle
        for l in c_logs:
            if l.mucus == MucusType.EGG_WHITE:
                ovulation_detected_date = l.date
                biomarker_reason = f"Peak fertile egg-white mucus logged on {l.date.isoformat()}."

        # 2. Check for BBT thermal shift (3-over-6) in current cycle
        bbt_entries = [(l.date, l.bbt) for l in c_logs if l.bbt is not None]
        if len(bbt_entries) >= 6:
            for idx in range(5, len(bbt_entries) - 2):
                baseline = [t[1] for t in bbt_entries[idx - 5: idx + 1]]
                max_base = max(baseline)
                next_3 = [t[1] for t in bbt_entries[idx + 1: idx + 4]]
                if all(t >= max_base + 0.15 for t in next_3):
                    ovulation_detected_date = bbt_entries[idx][0]
                    biomarker_reason = (
                        f"BBT thermal shift (+0.2°C) confirmed on {bbt_entries[idx+1][0].isoformat()}."
                    )
                    break

        if ovulation_detected_date:
            # Ovulation has happened! Next period is exactly ovulation + luteal_len
            next_start = ovulation_detected_date + timedelta(days=luteal_len)
            cycle_len = (next_start - ref_start).days
            ovulation = ovulation_detected_date
            confidence = 0.94
            explanation = (
                f"Biomarker confirmed: {biomarker_reason} "
                f"Projected next period in {luteal_len} days based on individual luteal phase."
            )
            std_dev = 1.2
        else:
            # Ovulation not yet observed, estimate using historical follicular average
            hist_follicular = [
                c.follicular_length_days for c in completed_cycles if c.follicular_length_days is not None
            ]
            foll_len = (
                round(sum(hist_follicular) / len(hist_follicular))
                if hist_follicular
                else (default_cycle_length - luteal_len)
            )
            ovulation = ref_start + timedelta(days=foll_len)
            next_start = ovulation + timedelta(days=luteal_len)
            cycle_len = (next_start - ref_start).days
            confidence = 0.65
            explanation = (
                f"Awaiting current cycle biomarker shift. Projected using luteal phase offset ({luteal_len}d)."
            )
            std_dev = 2.4

        fertile_start = ovulation - timedelta(days=5)
        fertile_end = ovulation + timedelta(days=1)
        pms_start = next_start - timedelta(days=5)
        pms_end = next_start - timedelta(days=1)

        ci80_days = max(1, round(1.282 * std_dev))
        ci95_days = max(2, round(1.960 * std_dev))

        return PredictionResult(
            model_name=self.name,
            next_period_start=next_start,
            predicted_cycle_length=float(cycle_len),
            confidence_interval_80=(
                next_start - timedelta(days=ci80_days),
                next_start + timedelta(days=ci80_days),
            ),
            confidence_interval_95=(
                next_start - timedelta(days=ci95_days),
                next_start + timedelta(days=ci95_days),
            ),
            fertile_window_start=fertile_start,
            fertile_window_end=fertile_end,
            ovulation_date=ovulation,
            pms_window_start=pms_start,
            pms_window_end=pms_end,
            confidence_score=confidence,
            explanation=explanation,
        )


class TrendHoltSmoothingPredictor(BaseCyclePredictor):
    """Model 4: Trend-Adjusted Holt's Exponential Smoothing (Double Exponential Smoothing).
    Detects whether cycle lengths are gradually trending longer (perimenopause/stress) or shorter.
    """

    def __init__(self, alpha: float = 0.4, beta: float = 0.2):
        super().__init__("Trend-Adjusted Holt's Smoothing")
        self.alpha = alpha
        self.beta = beta

    def predict(
        self,
        completed_cycles: List[Cycle],
        current_cycle: Optional[Cycle],
        recent_logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> PredictionResult:
        valid_lens = [float(c.length_days) for c in completed_cycles if c.length_days is not None]
        n = len(valid_lens)

        if n < 3:
            # Fall back to simple mean or default
            pred_len = float(sum(valid_lens) / n if n > 0 else default_cycle_length)
            trend_val = 0.0
            explanation = f"Insufficient cycle depth for trend estimation (< 3 cycles). Fallback to average ({round(pred_len, 1)}d)."
            confidence = 0.50
            std_dev = 2.8
        else:
            # Holt's linear trend algorithm
            level = valid_lens[0]
            trend = valid_lens[1] - valid_lens[0]

            for i in range(1, n):
                val = valid_lens[i]
                prev_level = level
                level = self.alpha * val + (1 - self.alpha) * (level + trend)
                trend = self.beta * (level - prev_level) + (1 - self.beta) * trend

            # Next 1-step forecast
            pred_len = level + trend
            # Constrain to physiologically plausible cycle boundary (18 - 50 days)
            pred_len = max(18.0, min(50.0, pred_len))
            trend_val = trend

            trend_desc = (
                f"lengthening trend (+{round(trend, 2)}d/cycle)"
                if trend > 0.2
                else f"shortening trend ({round(trend, 2)}d/cycle)"
                if trend < -0.2
                else "stable stationary trend"
            )
            explanation = f"Double exponential smoothing detected {trend_desc} across {n} cycles."
            confidence = min(0.90, 0.60 + 0.05 * n)

            residuals = [
                (valid_lens[i] - valid_lens[i - 1]) ** 2 for i in range(1, n)
            ]
            std_dev = math.sqrt(sum(residuals) / len(residuals)) if residuals else 2.5
            std_dev = max(1.4, std_dev)

        ref_start = current_cycle.start_date if current_cycle else date.today()
        round_len = round(pred_len)

        next_start = ref_start + timedelta(days=round_len)
        ovulation = ref_start + timedelta(days=max(5, round_len - default_luteal_length))
        fertile_start = ovulation - timedelta(days=5)
        fertile_end = ovulation + timedelta(days=1)
        pms_start = next_start - timedelta(days=5)
        pms_end = next_start - timedelta(days=1)

        ci80_days = max(1, round(1.282 * std_dev))
        ci95_days = max(2, round(1.960 * std_dev))

        return PredictionResult(
            model_name=self.name,
            next_period_start=next_start,
            predicted_cycle_length=round(pred_len, 1),
            confidence_interval_80=(
                next_start - timedelta(days=ci80_days),
                next_start + timedelta(days=ci80_days),
            ),
            confidence_interval_95=(
                next_start - timedelta(days=ci95_days),
                next_start + timedelta(days=ci95_days),
            ),
            fertile_window_start=fertile_start,
            fertile_window_end=fertile_end,
            ovulation_date=ovulation,
            pms_window_start=pms_start,
            pms_window_end=pms_end,
            confidence_score=confidence,
            explanation=explanation,
        )


class EnsembleCyclePredictor(BaseCyclePredictor):
    """Model 5: Smart Ensemble Model.
    Intelligently combines the individual predictors, weighting by reliability,
    sample volume, and real-time active biomarker confirmations.
    """

    def __init__(self):
        super().__init__("Smart Ensemble (Consensus)")
        self.wma_model = WeightedMovingAveragePredictor()
        self.bayesian_model = BayesianNormalPredictor()
        self.biomarker_model = SymptoThermalBiomarkerPredictor()
        self.holt_model = TrendHoltSmoothingPredictor()

    def get_all_model_predictions(
        self,
        completed_cycles: List[Cycle],
        current_cycle: Optional[Cycle],
        recent_logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> List[PredictionResult]:
        args = (completed_cycles, current_cycle, recent_logs, default_cycle_length, default_luteal_length)
        return [
            self.wma_model.predict(*args),
            self.bayesian_model.predict(*args),
            self.biomarker_model.predict(*args),
            self.holt_model.predict(*args),
        ]

    def predict(
        self,
        completed_cycles: List[Cycle],
        current_cycle: Optional[Cycle],
        recent_logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> PredictionResult:
        all_preds = self.get_all_model_predictions(
            completed_cycles, current_cycle, recent_logs, default_cycle_length, default_luteal_length
        )

        # Dynamic ensemble weighting
        bio_pred = all_preds[2]
        if bio_pred.confidence_score >= 0.90:
            # Active cycle ovulation biomarker confirmed!
            weights = [0.15, 0.15, 0.55, 0.15]
        else:
            n = len([c for c in completed_cycles if c.length_days is not None])
            if n <= 1:
                weights = [0.25, 0.45, 0.15, 0.15]
            elif n < 4:
                weights = [0.35, 0.35, 0.15, 0.15]
            else:
                weights = [0.30, 0.25, 0.20, 0.25]

        ensemble_len = sum(w * p.predicted_cycle_length for w, p in zip(weights, all_preds))
        ensemble_conf = sum(w * p.confidence_score for w, p in zip(weights, all_preds))

        ref_start = current_cycle.start_date if current_cycle else date.today()
        round_len = round(ensemble_len)

        next_start = ref_start + timedelta(days=round_len)
        ovulation = ref_start + timedelta(days=max(5, round_len - default_luteal_length))
        fertile_start = ovulation - timedelta(days=5)
        fertile_end = ovulation + timedelta(days=1)
        pms_start = next_start - timedelta(days=5)
        pms_end = next_start - timedelta(days=1)

        # Conservative confidence interval across model spread
        all_starts = [p.next_period_start for p in all_preds]
        min_start = min(all_starts)
        max_start = max(all_starts)
        spread_days = max(2, (max_start - min_start).days)

        ci80_days = max(1, round(spread_days * 0.75))
        ci95_days = max(2, round(spread_days * 1.25))

        explanation = (
            f"Consensus of 4 models (EWMA, Bayesian, Sympto-Thermal, Holt Trend) "
            f"weighted by biomarker confidence and historical depth."
        )

        return PredictionResult(
            model_name=self.name,
            next_period_start=next_start,
            predicted_cycle_length=round(ensemble_len, 1),
            confidence_interval_80=(
                next_start - timedelta(days=ci80_days),
                next_start + timedelta(days=ci80_days),
            ),
            confidence_interval_95=(
                next_start - timedelta(days=ci95_days),
                next_start + timedelta(days=ci95_days),
            ),
            fertile_window_start=fertile_start,
            fertile_window_end=fertile_end,
            ovulation_date=ovulation,
            pms_window_start=pms_start,
            pms_window_end=pms_end,
            confidence_score=round(ensemble_conf, 2),
            explanation=explanation,
        )

    def forecast_upcoming_cycles(
        self,
        count: int = 4,
        completed_cycles: Optional[List[Cycle]] = None,
        current_cycle: Optional[Cycle] = None,
        recent_logs: Optional[List[DailyLog]] = None,
        default_cycle_length: int = 28,
        default_luteal_length: int = 14,
    ) -> List[PredictionResult]:
        """Project multiple future cycles ahead."""
        completed_cycles = completed_cycles or []
        recent_logs = recent_logs or []

        forecasts: List[PredictionResult] = []
        curr_ref = current_cycle

        for i in range(count):
            pred = self.predict(
                completed_cycles,
                curr_ref,
                recent_logs,
                default_cycle_length,
                default_luteal_length,
            )
            # Annotate model name for sequence
            pred.model_name = f"Cycle +{i + 1} Forecast"
            # Decay confidence slightly for distant future cycles
            pred.confidence_score = max(0.35, round(pred.confidence_score - (i * 0.08), 2))
            forecasts.append(pred)

            # Advance reference cycle for next iteration
            next_start = pred.next_period_start
            curr_ref = Cycle(
                cycle_number=(curr_ref.cycle_number + 1) if curr_ref else (i + 2),
                start_date=next_start,
                length_days=round(pred.predicted_cycle_length),
            )

        return forecasts
