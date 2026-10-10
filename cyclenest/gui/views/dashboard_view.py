"""Dashboard View for CycleNest GUI.
"""

from __future__ import annotations
from datetime import date
from typing import Optional, Callable
import customtkinter as ctk

from cyclenest.models import CyclePhase, DailyLog, FlowLevel
from cyclenest.analyzer import CycleAnalyzer
from cyclenest.predictor import EnsembleCyclePredictor


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        analyzer_callback: Callable[[], CycleAnalyzer],
        predictor: EnsembleCyclePredictor,
        on_navigate: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.analyzer_callback = analyzer_callback
        self.predictor = predictor
        self.on_navigate = on_navigate

        self.refresh()

    def refresh(self) -> None:
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        analyzer = self.analyzer_callback()
        today = date.today()

        completed = analyzer.get_completed_cycles()
        current = analyzer.get_current_cycle()
        prediction = self.predictor.predict(
            completed,
            current,
            analyzer.logs,
            analyzer.default_cycle_length,
            analyzer.default_luteal_length,
        )

        phase, c_day, phase_desc = analyzer.get_phase_for_date(
            today, expected_next_period=prediction.next_period_start
        )
        days_to_period = (prediction.next_period_start - today).days

        # Top Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=f"🌸 Welcome to CycleNest",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#E05688",
        )
        title_lbl.pack(anchor="w")

        date_lbl = ctk.CTkLabel(
            header_frame,
            text=f"Today is {today.strftime('%A, %B %d, %Y')}",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        date_lbl.pack(anchor="w")

        # Hero Cycle Status Card
        hero_card = ctk.CTkFrame(self, corner_radius=16, fg_color=("#FBE8EF", "#2A1822"))
        hero_card.pack(fill="x", padx=20, pady=10)

        hero_inner = ctk.CTkFrame(hero_card, fg_color="transparent")
        hero_inner.pack(fill="x", padx=25, pady=20)

        # Left Column: Cycle Day & Phase Badge
        left_box = ctk.CTkFrame(hero_inner, fg_color="transparent")
        left_box.pack(side="left", fill="both", expand=True)

        day_badge = ctk.CTkLabel(
            left_box,
            text=f"CYCLE DAY {c_day}",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        )
        day_badge.pack(anchor="w")

        cycle_len_sub = ctk.CTkLabel(
            left_box,
            text=f"of an estimated {round(prediction.predicted_cycle_length)} day cycle",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        cycle_len_sub.pack(anchor="w", pady=(0, 10))

        # Phase Pill
        phase_colors = {
            CyclePhase.MENSTRUAL: ("#FF4D4D", "#3D1515"),
            CyclePhase.FOLLICULAR: ("#00B4D8", "#0B2B38"),
            CyclePhase.FERTILE_WINDOW: ("#FFAA00", "#3D2B05"),
            CyclePhase.OVULATION: ("#B5179E", "#380D35"),
            CyclePhase.LUTEAL: ("#E07A5F", "#3B1E16"),
            CyclePhase.LATE_LUTEAL_PMS: ("#D90429", "#3D0A12"),
        }
        text_c, bg_c = phase_colors.get(phase, ("#B83262", "#2A1822"))

        phase_pill = ctk.CTkButton(
            left_box,
            text=phase.display_title(),
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=bg_c,
            text_color=text_c,
            hover=False,
            corner_radius=20,
            height=32,
        )
        phase_pill.pack(anchor="w", pady=(0, 6))

        phase_expl = ctk.CTkLabel(
            left_box,
            text=phase_desc,
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray",
            wraplength=350,
            justify="left",
        )
        phase_expl.pack(anchor="w")

        # Right Column: Period Countdown & Conception Status
        right_box = ctk.CTkFrame(hero_inner, fg_color="transparent")
        right_box.pack(side="right", fill="both", expand=True)

        if phase == CyclePhase.MENSTRUAL:
            count_txt = "Period Active"
            count_sub = "Active menstrual bleeding"
            count_color = "#FF4D4D"
        elif days_to_period > 0:
            count_txt = f"{days_to_period} Days"
            count_sub = f"Until expected period ({prediction.next_period_start.strftime('%b %d')})"
            count_color = ("#2D6A4F", "#52B788")
        elif days_to_period == 0:
            count_txt = "Period Due Today"
            count_sub = f"Expected date: {prediction.next_period_start.strftime('%b %d')}"
            count_color = "#FFAA00"
        else:
            count_txt = f"{abs(days_to_period)}d Overdue"
            count_sub = f"Expected on {prediction.next_period_start.strftime('%b %d')}"
            count_color = "#E63946"

        cd_lbl = ctk.CTkLabel(
            right_box,
            text=count_txt,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=count_color,
        )
        cd_lbl.pack(anchor="e")

        cd_sub = ctk.CTkLabel(
            right_box,
            text=count_sub,
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        cd_sub.pack(anchor="e", pady=(0, 12))

        # Conception probability pill
        if phase in (CyclePhase.OVULATION, CyclePhase.FERTILE_WINDOW):
            fert_text = "🔥 Peak Conception Chance"
            fert_fg = ("#FFD166", "#3D2B05")
            fert_tx = "#C77700"
        elif phase in (CyclePhase.MENSTRUAL, CyclePhase.LUTEAL):
            fert_text = "Low Conception Chance"
            fert_fg = ("#D8F3DC", "#143321")
            fert_tx = ("#1B4332", "#74C69D")
        else:
            fert_text = "Moderate Conception Chance"
            fert_fg = ("#E2EAFC", "#1B243B")
            fert_tx = ("#3D5A80", "#90E0EF")

        fert_pill = ctk.CTkButton(
            right_box,
            text=fert_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=fert_fg[1],
            text_color=fert_tx[1] if isinstance(fert_tx, tuple) else fert_tx,
            hover=False,
            corner_radius=20,
            height=30,
        )
        fert_pill.pack(anchor="e")

        # Quick Action Buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=5)

        log_today_btn = ctk.CTkButton(
            btn_bar,
            text="✍️ Log Today's Health",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#D94073",
            hover_color="#B83262",
            height=40,
            corner_radius=10,
            command=lambda: self.on_navigate("log"),
        )
        log_today_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        cal_btn = ctk.CTkButton(
            btn_bar,
            text="🗓️ View Calendar",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#6C757D", "#495057"),
            hover_color="#343A40",
            height=40,
            corner_radius=10,
            command=lambda: self.on_navigate("calendar"),
        )
        cal_btn.pack(side="left", fill="x", expand=True, padx=4)

        pred_btn = ctk.CTkButton(
            btn_bar,
            text="🔮 View Predictions",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#5E60CE", "#4E50B2"),
            hover_color="#3E4092",
            height=40,
            corner_radius=10,
            command=lambda: self.on_navigate("predictions"),
        )
        pred_btn.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Bottom Grid (2 Cards: Key Milestones & Today's Log)
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="x", padx=20, pady=12)

        # Card 1: Key Milestones
        milestone_card = ctk.CTkFrame(grid_frame, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        milestone_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        m_inner = ctk.CTkFrame(milestone_card, fg_color="transparent")
        m_inner.pack(fill="both", expand=True, padx=18, pady=16)

        m_title = ctk.CTkLabel(
            m_inner,
            text="🎯 Key Cycle Milestones",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        )
        m_title.pack(anchor="w", pady=(0, 10))

        milestones = [
            ("🥚 Next Ovulation", prediction.ovulation_date.strftime("%A, %b %d")),
            ("✨ Fertile Window", f"{prediction.fertile_window_start.strftime('%b %d')} - {prediction.fertile_window_end.strftime('%b %d')}"),
            ("⚡ PMS Alert Window", f"{prediction.pms_window_start.strftime('%b %d')} - {prediction.pms_window_end.strftime('%b %d')}"),
            ("🩸 Expected Period", prediction.next_period_start.strftime("%A, %b %d")),
            ("🎯 80% Confidence Range", f"{prediction.confidence_interval_80[0].strftime('%b %d')} - {prediction.confidence_interval_80[1].strftime('%b %d')}"),
        ]

        for label, val in milestones:
            row = ctk.CTkFrame(m_inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=13), text_color="gray").pack(side="left")
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=13, weight="bold")).pack(side="right")

        # Card 2: Today's Log Summary
        log_card = ctk.CTkFrame(grid_frame, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        log_card.pack(side="right", fill="both", expand=True, padx=(10, 0))

        l_inner = ctk.CTkFrame(log_card, fg_color="transparent")
        l_inner.pack(fill="both", expand=True, padx=18, pady=16)

        l_title = ctk.CTkLabel(
            l_inner,
            text="📝 Today's Log Status",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        )
        l_title.pack(anchor="w", pady=(0, 10))

        today_log: Optional[DailyLog] = analyzer.log_map.get(today)
        if today_log:
            flow_str = today_log.flow.display_badge()
            cramp_str = f"{today_log.cramps_pain} / 5" if today_log.cramps_pain > 0 else "None"
            bbt_str = f"{today_log.bbt:.2f}°C" if today_log.bbt else "Not recorded"
            sym_str = ", ".join(today_log.symptoms[:3]) if today_log.symptoms else "None recorded"
            mood_str = ", ".join(today_log.moods[:2]) if today_log.moods else "None recorded"

            items = [
                ("Bleeding Flow:", flow_str),
                ("Pelvic Cramps:", cramp_str),
                ("Morning BBT:", bbt_str),
                ("Cervical Mucus:", today_log.mucus.display_badge()),
                ("Logged Symptoms:", sym_str),
                ("Mood / Emotions:", mood_str),
            ]
            for l_lbl, l_val in items:
                row = ctk.CTkFrame(l_inner, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=l_lbl, font=ctk.CTkFont(size=13), text_color="gray").pack(side="left")
                ctk.CTkLabel(row, text=l_val, font=ctk.CTkFont(size=13, weight="bold")).pack(side="right")
        else:
            ctk.CTkLabel(
                l_inner,
                text="No entry recorded yet for today.",
                font=ctk.CTkFont(size=14, slant="italic"),
                text_color="gray",
            ).pack(anchor="w", pady=(15, 15))

            ctk.CTkButton(
                l_inner,
                text="Quick Check-In Now",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#D94073",
                hover_color="#B83262",
                command=lambda: self.on_navigate("log"),
            ).pack(anchor="w")

        # Card 3: Clinical Health & FIGO Summary
        stats = analyzer.compute_statistics()
        stat_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        stat_card.pack(fill="x", padx=20, pady=(5, 20))

        s_inner = ctk.CTkFrame(stat_card, fg_color="transparent")
        s_inner.pack(fill="x", padx=18, pady=14)

        s_title = ctk.CTkLabel(
            s_inner,
            text=f"📊 Historical Rhythm & Regularity",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        )
        s_title.pack(anchor="w", pady=(0, 6))

        s_text = (
            f"Average Cycle Length: {stats['mean_cycle_length']} days (±{stats['std_cycle_length']}d)  |  "
            f"Average Period Duration: {stats['mean_period_length']} days  |  "
            f"FIGO Classification: {stats['regularity_status']}"
        )
        ctk.CTkLabel(s_inner, text=s_text, font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w")
