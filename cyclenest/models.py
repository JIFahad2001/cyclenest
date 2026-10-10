"""Domain data models and enums for CycleNest.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
import json


class FlowLevel(str, Enum):
    NONE = "none"
    SPOTTING = "spotting"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    SUPER_HEAVY = "super_heavy"

    @classmethod
    def from_str(cls, val: str) -> "FlowLevel":
        val_clean = val.strip().lower()
        for member in cls:
            if member.value == val_clean:
                return member
        return cls.NONE

    def is_bleeding(self) -> bool:
        """Returns True if there is actual menstrual bleeding (light or above)."""
        return self in (FlowLevel.LIGHT, FlowLevel.MEDIUM, FlowLevel.HEAVY, FlowLevel.SUPER_HEAVY)

    def display_badge(self) -> str:
        icons = {
            FlowLevel.NONE: "⚪ None",
            FlowLevel.SPOTTING: "🌸 Spotting",
            FlowLevel.LIGHT: "🩸 Light",
            FlowLevel.MEDIUM: "🩸🩸 Medium",
            FlowLevel.HEAVY: "🩸🩸🩸 Heavy",
            FlowLevel.SUPER_HEAVY: "🌊 Super Heavy",
        }
        return icons.get(self, "⚪ None")


class MucusType(str, Enum):
    NONE = "none"
    DRY = "dry"
    STICKY = "sticky"
    CREAMY = "creamy"
    WATERY = "watery"
    EGG_WHITE = "egg_white"

    @classmethod
    def from_str(cls, val: str) -> "MucusType":
        val_clean = val.strip().lower().replace(" ", "_")
        for member in cls:
            if member.value == val_clean:
                return member
        return cls.NONE

    def is_fertile(self) -> bool:
        return self in (MucusType.WATERY, MucusType.EGG_WHITE)

    def display_badge(self) -> str:
        badges = {
            MucusType.NONE: "None",
            MucusType.DRY: "🏜️ Dry",
            MucusType.STICKY: "🧴 Sticky",
            MucusType.CREAMY: "🥛 Creamy",
            MucusType.WATERY: "💧 Watery (Fertile)",
            MucusType.EGG_WHITE: "✨ Egg White (Peak Fertile)",
        }
        return badges.get(self, "None")


class SexualActivity(str, Enum):
    NONE = "none"
    PROTECTED = "protected"
    UNPROTECTED = "unprotected"
    HIGH_LIBIDO = "high_libido"

    @classmethod
    def from_str(cls, val: str) -> "SexualActivity":
        val_clean = val.strip().lower().replace(" ", "_")
        for member in cls:
            if member.value == val_clean:
                return member
        return cls.NONE

    def display_badge(self) -> str:
        badges = {
            SexualActivity.NONE: "None",
            SexualActivity.PROTECTED: "🛡️ Protected",
            SexualActivity.UNPROTECTED: "❤️ Unprotected",
            SexualActivity.HIGH_LIBIDO: "🔥 High Libido",
        }
        return badges.get(self, "None")


class CyclePhase(str, Enum):
    MENSTRUAL = "menstrual"
    FOLLICULAR = "follicular"
    FERTILE_WINDOW = "fertile_window"
    OVULATION = "ovulation"
    LUTEAL = "luteal"
    LATE_LUTEAL_PMS = "late_luteal_pms"

    def display_title(self) -> str:
        names = {
            CyclePhase.MENSTRUAL: "🩸 Menstrual Phase",
            CyclePhase.FOLLICULAR: "🌱 Follicular Phase",
            CyclePhase.FERTILE_WINDOW: "✨ Fertile Window",
            CyclePhase.OVULATION: "🥚 Ovulation Phase",
            CyclePhase.LUTEAL: "🍂 Luteal Phase",
            CyclePhase.LATE_LUTEAL_PMS: "⚡ Pre-Menstrual (PMS) Window",
        }
        return names.get(self, self.value.title())

    def color(self) -> str:
        colors = {
            CyclePhase.MENSTRUAL: "bright_red",
            CyclePhase.FOLLICULAR: "cyan",
            CyclePhase.FERTILE_WINDOW: "yellow",
            CyclePhase.OVULATION: "bright_magenta",
            CyclePhase.LUTEAL: "dark_orange",
            CyclePhase.LATE_LUTEAL_PMS: "magenta",
        }
        return colors.get(self, "white")


COMMON_SYMPTOMS = [
    "Cramps",
    "Bloating",
    "Breast Tenderness",
    "Headache / Migraine",
    "Fatigue / Exhaustion",
    "Acne / Breakouts",
    "Lower Back Pain",
    "Food Cravings",
    "Nausea",
    "Insomnia",
    "Joint / Muscle Ache",
    "Hot Flashes",
    "Pelvic Heaviness",
    "Digestive Upset",
]

COMMON_MOODS = [
    "Calm / Balanced",
    "Happy / Content",
    "High Energy",
    "Creative / Focused",
    "Irritable / Snappy",
    "Anxious / Stressed",
    "Sad / Tearful",
    "Mood Swings",
    "Brain Fog",
    "Low Motivation",
    "Sensitive",
    "Restless",
]


@dataclass
class DailyLog:
    date: date
    flow: FlowLevel = FlowLevel.NONE
    cramps_pain: int = 0  # 0 to 5
    energy_level: Optional[int] = None  # 1 to 5
    bbt: Optional[float] = None  # Basal Body Temperature
    mucus: MucusType = MucusType.NONE
    sexual_activity: SexualActivity = SexualActivity.NONE
    sleep_hours: Optional[float] = None
    symptoms: List[str] = field(default_factory=list)
    moods: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "flow": self.flow.value,
            "cramps_pain": self.cramps_pain,
            "energy_level": self.energy_level,
            "bbt": self.bbt,
            "mucus": self.mucus.value,
            "sexual_activity": self.sexual_activity.value,
            "sleep_hours": self.sleep_hours,
            "symptoms": self.symptoms,
            "moods": self.moods,
            "medications": self.medications,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyLog":
        d_val = data["date"]
        if isinstance(d_val, str):
            d_val = date.fromisoformat(d_val)
        return cls(
            date=d_val,
            flow=FlowLevel.from_str(data.get("flow", "none")),
            cramps_pain=int(data.get("cramps_pain", 0)),
            energy_level=data.get("energy_level"),
            bbt=float(data["bbt"]) if data.get("bbt") is not None else None,
            mucus=MucusType.from_str(data.get("mucus", "none")),
            sexual_activity=SexualActivity.from_str(data.get("sexual_activity", "none")),
            sleep_hours=float(data["sleep_hours"]) if data.get("sleep_hours") is not None else None,
            symptoms=data.get("symptoms") or [],
            moods=data.get("moods") or [],
            medications=data.get("medications") or [],
            notes=data.get("notes") or "",
        )


@dataclass
class Cycle:
    cycle_number: int
    start_date: date
    end_date: Optional[date] = None  # Day before next period
    length_days: Optional[int] = None
    period_length_days: int = 5
    ovulation_date: Optional[date] = None
    follicular_length_days: Optional[int] = None
    luteal_length_days: Optional[int] = None
    bbt_shift_detected: bool = False

    @property
    def is_completed(self) -> bool:
        return self.end_date is not None and self.length_days is not None


@dataclass
class PredictionResult:
    model_name: str
    next_period_start: date
    predicted_cycle_length: float
    confidence_interval_80: Tuple[date, date]
    confidence_interval_95: Tuple[date, date]
    fertile_window_start: date
    fertile_window_end: date
    ovulation_date: date
    pms_window_start: date
    pms_window_end: date
    confidence_score: float  # 0.0 to 1.0
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "next_period_start": self.next_period_start.isoformat(),
            "predicted_cycle_length": round(self.predicted_cycle_length, 1),
            "confidence_interval_80": [d.isoformat() for d in self.confidence_interval_80],
            "confidence_interval_95": [d.isoformat() for d in self.confidence_interval_95],
            "fertile_window_start": self.fertile_window_start.isoformat(),
            "fertile_window_end": self.fertile_window_end.isoformat(),
            "ovulation_date": self.ovulation_date.isoformat(),
            "pms_window_start": self.pms_window_start.isoformat(),
            "pms_window_end": self.pms_window_end.isoformat(),
            "confidence_score": round(self.confidence_score, 2),
            "explanation": self.explanation,
        }
