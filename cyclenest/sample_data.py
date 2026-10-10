"""Realistic Benchmark Sample Data Generator for CycleNest.
Generates 6+ months of clinically realistic menstrual logs (BBT shifts, mucus, cramps, moods).
"""

from __future__ import annotations
import random
from datetime import date, timedelta
from typing import List

from cyclenest.models import (
    DailyLog,
    FlowLevel,
    MucusType,
    SexualActivity,
)


def generate_sample_data(reference_date: date = date.today()) -> List[DailyLog]:
    """Generate 6 realistic clinical cycles ending near reference_date."""
    # Historical cycle lengths: 28, 29, 27, 28, 29, 28 days
    cycle_lengths = [28, 29, 27, 28, 29, 28]
    total_days = sum(cycle_lengths)

    # Current cycle day ~16 (post-ovulation luteal phase)
    current_cycle_day = 16
    start_date = reference_date - timedelta(days=(total_days - cycle_lengths[-1] + current_cycle_day))

    logs: List[DailyLog] = []
    curr_date = start_date

    # Use a fixed seed for reproducible realistic data
    rng = random.Random(42)

    for cycle_idx, c_len in enumerate(cycle_lengths):
        is_current_cycle = (cycle_idx == len(cycle_lengths) - 1)
        cycle_days_to_gen = current_cycle_day if is_current_cycle else c_len
        ovulation_day = c_len - 14  # luteal phase = 14 days

        for day in range(1, cycle_days_to_gen + 1):
            log_date = curr_date
            flow = FlowLevel.NONE
            cramps = 0
            energy = 3
            mucus = MucusType.NONE
            sex = SexualActivity.NONE
            symptoms: List[str] = []
            moods: List[str] = []
            bbt: float = 36.35 + rng.uniform(-0.08, 0.08)
            sleep_hours = round(rng.uniform(6.8, 8.4), 1)
            notes = ""

            # Phase 1: Menstruation (Days 1 to 5)
            if day == 1:
                flow = FlowLevel.HEAVY
                cramps = rng.choice([3, 4])
                symptoms.extend(["Cramps", "Fatigue / Exhaustion", "Lower Back Pain"])
                moods.append(rng.choice(["Low Motivation", "Sensitive"]))
                energy = 2
                notes = "Period started today. Warm tea and heating pad helped."
            elif day == 2:
                flow = FlowLevel.HEAVY
                cramps = rng.choice([3, 4])
                symptoms.extend(["Cramps", "Headache / Migraine"])
                moods.append("Irritable / Snappy")
                energy = 2
            elif day == 3:
                flow = FlowLevel.MEDIUM
                cramps = rng.choice([1, 2])
                symptoms.append("Cramps")
                moods.append("Calm / Balanced")
                energy = 3
            elif day == 4:
                flow = FlowLevel.LIGHT
                cramps = 0
                energy = 3
                moods.append("Calm / Balanced")
            elif day == 5:
                flow = FlowLevel.SPOTTING
                cramps = 0
                energy = 4
                moods.append("Happy / Content")

            # Phase 2: Follicular / Pre-ovulation (Days 6 to ovulation_day - 3)
            elif 6 <= day < ovulation_day - 2:
                mucus = MucusType.STICKY if day <= 8 else MucusType.CREAMY
                energy = 4
                moods.append(rng.choice(["Creative / Focused", "High Energy"]))
                bbt = 36.32 + rng.uniform(-0.06, 0.06)

            # Phase 3: Fertile Window & Ovulation (ovulation_day - 2 to ovulation_day + 1)
            elif ovulation_day - 2 <= day <= ovulation_day + 1:
                energy = 5
                moods.extend(["High Energy", "Happy / Content"])
                if day == ovulation_day:
                    mucus = MucusType.EGG_WHITE
                    sex = SexualActivity.HIGH_LIBIDO
                    symptoms.append("Pelvic Heaviness")
                    notes = "Noticed peak fertile egg-white discharge today. High energy!"
                elif day == ovulation_day - 1:
                    mucus = MucusType.WATERY
                    sex = SexualActivity.PROTECTED
                else:
                    mucus = MucusType.CREAMY
                bbt = 36.30 + rng.uniform(-0.05, 0.05)

            # Phase 4: Luteal Phase (ovulation_day + 2 to c_len - 5)
            elif ovulation_day + 2 <= day < c_len - 4:
                # Progesterone thermal shift!
                bbt = 36.68 + rng.uniform(-0.07, 0.07)
                mucus = MucusType.DRY
                energy = 3
                moods.append(rng.choice(["Calm / Balanced", "Creative / Focused"]))

            # Phase 5: Late Luteal / Pre-Menstrual Window (c_len - 4 to c_len)
            else:
                bbt = 36.70 + rng.uniform(-0.06, 0.06)
                mucus = MucusType.DRY
                energy = 2
                symptoms.extend(rng.sample(["Bloating", "Breast Tenderness", "Food Cravings", "Acne / Breakouts"], k=2))
                moods.append(rng.choice(["Mood Swings", "Irritable / Snappy", "Anxious / Stressed"]))
                if day == c_len - 1:
                    notes = "Craving chocolate, mild bloating."

            logs.append(
                DailyLog(
                    date=log_date,
                    flow=flow,
                    cramps_pain=cramps,
                    energy_level=energy,
                    bbt=round(bbt, 2),
                    mucus=mucus,
                    sexual_activity=sex,
                    sleep_hours=sleep_hours,
                    symptoms=list(set(symptoms)),
                    moods=list(set(moods)),
                    notes=notes,
                )
            )
            curr_date += timedelta(days=1)

    return logs
