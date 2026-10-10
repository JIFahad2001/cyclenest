"""Menstrual Cycle Pattern Analyzer, Clinical Classifications, and Biomarker Correlation.
"""

from __future__ import annotations
import math
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict

from cyclenest.models import (
    DailyLog,
    Cycle,
    CyclePhase,
    FlowLevel,
    MucusType,
)


class CycleAnalyzer:
    def __init__(
        self,
        logs: List[DailyLog],
        default_cycle_length: int = 28,
        default_period_length: int = 5,
        default_luteal_length: int = 14,
    ):
        self.logs = sorted(logs, key=lambda l: l.date)
        self.log_map: Dict[date, DailyLog] = {l.date: l for l in self.logs}
        self.default_cycle_length = default_cycle_length
        self.default_period_length = default_period_length
        self.default_luteal_length = default_luteal_length

        self.cycles = self._detect_cycles()

    def _detect_cycles(self) -> List[Cycle]:
        """Detect cycles by identifying distinct menstrual bleeding episodes."""
        if not self.logs:
            return []

        # Find all bleeding days (Light, Medium, Heavy, Super Heavy)
        bleeding_dates = [l.date for l in self.logs if l.flow.is_bleeding()]
        if not bleeding_dates:
            return []

        # Group bleeding dates into distinct period bleeding episodes
        # Any gap >= 14 days marks a new cycle
        episodes: List[List[date]] = []
        curr_episode: List[date] = [bleeding_dates[0]]

        for d in bleeding_dates[1:]:
            gap = (d - curr_episode[-1]).days
            if gap <= 3:  # Up to 2-3 days pause within same period is normal
                curr_episode.append(d)
            else:
                episodes.append(curr_episode)
                curr_episode = [d]
        episodes.append(curr_episode)

        detected_cycles: List[Cycle] = []
        for i, ep in enumerate(episodes):
            cycle_start = ep[0]
            period_len = (ep[-1] - ep[0]).days + 1
            if period_len < 1:
                period_len = 1

            # End date is day before next episode start
            if i + 1 < len(episodes):
                next_start = episodes[i + 1][0]
                cycle_len = (next_start - cycle_start).days
                cycle_end = next_start - timedelta(days=1)
            else:
                cycle_len = None
                cycle_end = None

            c = Cycle(
                cycle_number=i + 1,
                start_date=cycle_start,
                end_date=cycle_end,
                length_days=cycle_len,
                period_length_days=period_len,
            )
            detected_cycles.append(c)

        # Detect BBT thermal shift and estimate ovulation dates for each cycle
        for c in detected_cycles:
            self._analyze_cycle_biomarkers(c)

        return detected_cycles

    def _analyze_cycle_biomarkers(self, cycle: Cycle) -> None:
        """Detect BBT thermal shift and identify ovulation window for a cycle."""
        c_start = cycle.start_date
        c_end = cycle.end_date or (c_start + timedelta(days=cycle.length_days or self.default_cycle_length))

        cycle_logs = [l for l in self.logs if c_start <= l.date <= c_end]
        temp_logs = [(l.date, l.bbt) for l in cycle_logs if l.bbt is not None]

        # Check for 3-over-6 BBT rule
        shift_found = False
        ovulation_date = None

        if len(temp_logs) >= 9:
            temps = [t[1] for t in temp_logs]
            dates = [t[0] for t in temp_logs]

            for idx in range(6, len(temps) - 2):
                baseline = temps[idx - 6: idx]
                max_baseline = max(baseline)
                next_3 = temps[idx: idx + 3]

                # If next 3 days are elevated by >= 0.15 deg C above highest of baseline
                if all(t >= max_baseline + 0.15 for t in next_3):
                    shift_found = True
                    # Ovulation occurs approx 1 day before the thermal shift
                    ovulation_date = dates[idx] - timedelta(days=1)
                    break

        # Check for peak fertile cervical mucus (egg white)
        mucus_ovulation = None
        for l in cycle_logs:
            if l.mucus == MucusType.EGG_WHITE:
                mucus_ovulation = l.date

        if shift_found and ovulation_date:
            cycle.bbt_shift_detected = True
            cycle.ovulation_date = ovulation_date
        elif mucus_ovulation:
            cycle.ovulation_date = mucus_ovulation
        elif cycle.length_days:
            # Fallback clinical back-calculation: Luteal phase is ~14 days
            cycle.ovulation_date = cycle.start_date + timedelta(
                days=max(5, cycle.length_days - self.default_luteal_length)
            )
        else:
            cycle.ovulation_date = cycle.start_date + timedelta(
                days=max(5, self.default_cycle_length - self.default_luteal_length)
            )

        if cycle.ovulation_date and cycle.end_date:
            cycle.follicular_length_days = (cycle.ovulation_date - cycle.start_date).days
            cycle.luteal_length_days = (cycle.end_date - cycle.ovulation_date).days + 1

    def get_completed_cycles(self) -> List[Cycle]:
        return [c for c in self.cycles if c.is_completed]

    def get_current_cycle(self) -> Optional[Cycle]:
        if not self.cycles:
            return None
        latest = self.cycles[-1]
        if not latest.is_completed:
            return latest
        return latest

    def get_cycle_length_history(self) -> List[int]:
        return [c.length_days for c in self.get_completed_cycles() if c.length_days is not None]

    def get_period_length_history(self) -> List[int]:
        return [c.period_length_days for c in self.cycles if c.period_length_days > 0]

    def compute_statistics(self) -> Dict[str, Any]:
        """Compute standard gynecological cycle statistics and FIGO classifications."""
        c_lens = self.get_cycle_length_history()
        p_lens = self.get_period_length_history()

        if not c_lens:
            return {
                "cycle_count": len(self.cycles),
                "completed_cycles": 0,
                "mean_cycle_length": float(self.default_cycle_length),
                "median_cycle_length": float(self.default_cycle_length),
                "std_cycle_length": 0.0,
                "min_cycle_length": self.default_cycle_length,
                "max_cycle_length": self.default_cycle_length,
                "iqr_cycle_length": 0.0,
                "mean_period_length": float(self.default_period_length),
                "median_period_length": float(self.default_period_length),
                "regularity_status": "Insufficient Data (Log at least 2 full cycles)",
                "regularity_code": "unknown",
                "variation_days": 0.0,
            }

        mean_c = sum(c_lens) / len(c_lens)
        sorted_c = sorted(c_lens)
        median_c = sorted_c[len(sorted_c) // 2]
        min_c = min(c_lens)
        max_c = max(c_lens)

        # Standard Deviation
        variance = sum((x - mean_c) ** 2 for x in c_lens) / len(c_lens)
        std_c = math.sqrt(variance)

        # IQR
        q1 = sorted_c[int(len(sorted_c) * 0.25)]
        q3 = sorted_c[int(len(sorted_c) * 0.75)]
        iqr_c = q3 - q1

        # Period statistics
        mean_p = sum(p_lens) / len(p_lens) if p_lens else float(self.default_period_length)
        median_p = sorted(p_lens)[len(p_lens) // 2] if p_lens else self.default_period_length

        # FIGO / Clinical Regularity Evaluation
        # Normal cycle: 24 - 38 days. Variation across cycles <= 7-9 days.
        variation = max_c - min_c
        if std_c <= 2.2:
            reg_status = "Highly Regular (Cycle length varies by < 2-3 days)"
            reg_code = "high"
        elif std_c <= 4.2 and 21 <= mean_c <= 38:
            reg_status = "Regular (Normal physiological cycle variability)"
            reg_code = "normal"
        elif std_c <= 7.0 and 21 <= mean_c <= 38:
            reg_status = "Mildly Variable (Occasional shorter or longer cycles)"
            reg_code = "mild"
        elif mean_c < 21:
            reg_status = "Polymenorrhea / Short Cycles (< 21 days; consult healthcare provider)"
            reg_code = "short"
        elif mean_c > 38:
            reg_status = "Oligomenorrhea / Long Cycles (> 38 days; consult healthcare provider)"
            reg_code = "long"
        else:
            reg_status = "Irregular (High cycle length dispersion > 7 days)"
            reg_code = "irregular"

        return {
            "cycle_count": len(self.cycles),
            "completed_cycles": len(c_lens),
            "mean_cycle_length": round(mean_c, 1),
            "median_cycle_length": round(median_c, 1),
            "std_cycle_length": round(std_c, 1),
            "min_cycle_length": min_c,
            "max_cycle_length": max_c,
            "iqr_cycle_length": round(iqr_c, 1),
            "mean_period_length": round(mean_p, 1),
            "median_period_length": round(median_p, 1),
            "regularity_status": reg_status,
            "regularity_code": reg_code,
            "variation_days": variation,
        }

    def get_phase_for_date(
        self, target_date: date, expected_next_period: Optional[date] = None
    ) -> Tuple[CyclePhase, int, str]:
        """Determine cycle phase, cycle day, and description for a specific date."""
        if not self.cycles:
            return CyclePhase.FOLLICULAR, 1, "No cycle history recorded yet."

        # Find the cycle that contains this date, or the latest active cycle
        matching_cycle = None
        for c in reversed(self.cycles):
            if c.start_date <= target_date:
                matching_cycle = c
                break

        if not matching_cycle:
            # Date is before any recorded cycle
            return CyclePhase.FOLLICULAR, 1, "Before first recorded cycle"

        cycle_day = (target_date - matching_cycle.start_date).days + 1

        # Use matching cycle length or default
        cycle_len = matching_cycle.length_days or self.default_cycle_length
        period_len = matching_cycle.period_length_days or self.default_period_length

        if expected_next_period and matching_cycle == self.cycles[-1]:
            cycle_len = (expected_next_period - matching_cycle.start_date).days

        # Ovulation day estimate
        ovulation_day_num = cycle_len - self.default_luteal_length
        if ovulation_day_num < period_len + 3:
            ovulation_day_num = period_len + 3

        # Check if user has logged bleeding on target date
        log = self.log_map.get(target_date)
        if log and log.flow.is_bleeding():
            return CyclePhase.MENSTRUAL, cycle_day, "Menstruation (active flow logged)"

        if cycle_day <= period_len:
            return CyclePhase.MENSTRUAL, cycle_day, f"Menstrual bleeding phase (Day {cycle_day})"

        fertile_start = ovulation_day_num - 5
        fertile_end = ovulation_day_num + 1

        if cycle_day < fertile_start:
            return CyclePhase.FOLLICULAR, cycle_day, "Follicular phase (estrogen rising, energy building)"

        if fertile_start <= cycle_day < ovulation_day_num:
            return CyclePhase.FERTILE_WINDOW, cycle_day, "Fertile window (high chance of conception)"

        if cycle_day == ovulation_day_num:
            return CyclePhase.OVULATION, cycle_day, "Ovulation day (peak fertility, egg release)"

        pms_start = cycle_len - 4
        if cycle_day < pms_start:
            return CyclePhase.LUTEAL, cycle_day, "Luteal phase (progesterone dominant, calming)"

        return CyclePhase.LATE_LUTEAL_PMS, cycle_day, "Pre-menstrual window (potential PMS symptoms, low hormone drop)"

    def analyze_symptom_patterns(self) -> Dict[str, Any]:
        """Analyze frequency and phase distribution of symptoms and moods."""
        symptom_counts: Counter[str] = Counter()
        mood_counts: Counter[str] = Counter()

        symptoms_by_phase: Dict[CyclePhase, Counter[str]] = defaultdict(Counter)
        moods_by_phase: Dict[CyclePhase, Counter[str]] = defaultdict(Counter)
        cramps_by_cycle_day: Dict[int, List[int]] = defaultdict(list)
        bbt_by_phase: Dict[CyclePhase, List[float]] = defaultdict(list)

        for l in self.logs:
            phase, c_day, _ = self.get_phase_for_date(l.date)

            for s in l.symptoms:
                symptom_counts[s] += 1
                symptoms_by_phase[phase][s] += 1

            for m in l.moods:
                mood_counts[m] += 1
                moods_by_phase[phase][m] += 1

            if l.cramps_pain > 0 and c_day <= 35:
                cramps_by_cycle_day[c_day].append(l.cramps_pain)

            if l.bbt is not None:
                bbt_by_phase[phase].append(l.bbt)

        # Average cramp intensity by cycle day
        avg_cramps_day = {
            day: round(sum(vals) / len(vals), 2)
            for day, vals in sorted(cramps_by_cycle_day.items())
        }

        # Average BBT by phase
        avg_bbt_phase = {
            phase.value: round(sum(vals) / len(vals), 2)
            for phase, vals in bbt_by_phase.items()
            if vals
        }

        # PMS symptoms cluster (symptoms appearing during Late Luteal or right before period)
        pms_symptoms = symptoms_by_phase[CyclePhase.LATE_LUTEAL_PMS].most_common(5)

        return {
            "total_logged_days": len(self.logs),
            "top_symptoms": symptom_counts.most_common(10),
            "top_moods": mood_counts.most_common(10),
            "symptoms_by_phase": {
                k.value: dict(v.most_common(5)) for k, v in symptoms_by_phase.items()
            },
            "moods_by_phase": {
                k.value: dict(v.most_common(5)) for k, v in moods_by_phase.items()
            },
            "avg_cramps_by_day": avg_cramps_day,
            "avg_bbt_by_phase": avg_bbt_phase,
            "pms_symptoms": pms_symptoms,
        }
