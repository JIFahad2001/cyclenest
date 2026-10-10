"""Interactive Monthly Calendar View for CycleNest GUI.
"""

from __future__ import annotations
import calendar
from datetime import date, timedelta
from typing import Callable, Optional
import customtkinter as ctk

from cyclenest.models import CyclePhase, DailyLog, PredictionResult
from cyclenest.analyzer import CycleAnalyzer
from cyclenest.predictor import EnsembleCyclePredictor


class CalendarView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        analyzer_callback: Callable[[], CycleAnalyzer],
        predictor: EnsembleCyclePredictor,
        on_select_date: Callable[[date], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.analyzer_callback = analyzer_callback
        self.predictor = predictor
        self.on_select_date = on_select_date

        today = date.today()
        self.year = today.year
        self.month = today.month

        self._build_ui()
        self.render_calendar()

    def _build_ui(self) -> None:
        # Header & Navigation
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=25, pady=(15, 10))

        title = ctk.CTkLabel(
            nav_frame,
            text="🗓️ Interactive Cycle Calendar",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E05688",
        )
        title.pack(side="left")

        # Month Controls
        ctrl_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        ctrl_frame.pack(side="right")

        prev_btn = ctk.CTkButton(
            ctrl_frame,
            text="◀",
            width=36,
            height=32,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#6C757D", "#343A40"),
            command=self._prev_month,
        )
        prev_btn.pack(side="left", padx=2)

        self.month_lbl = ctk.CTkLabel(
            ctrl_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=150,
        )
        self.month_lbl.pack(side="left", padx=5)

        next_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶",
            width=36,
            height=32,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#6C757D", "#343A40"),
            command=self._next_month,
        )
        next_btn.pack(side="left", padx=2)

        today_btn = ctk.CTkButton(
            ctrl_frame,
            text="Today",
            width=65,
            height=32,
            fg_color="#D94073",
            hover_color="#B83262",
            command=self._jump_today,
        )
        today_btn.pack(side="left", padx=(8, 0))

        # Calendar Grid Container Card
        self.cal_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        self.cal_card.pack(fill="both", expand=True, padx=25, pady=8)

        self.grid_container = ctk.CTkFrame(self.cal_card, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Legend Card
        legend_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("#F4F4F6", "#202124"))
        legend_card.pack(fill="x", padx=25, pady=(5, 20))

        leg_inner = ctk.CTkFrame(legend_card, fg_color="transparent")
        leg_inner.pack(fill="x", padx=15, pady=8)

        items = [
            ("🩸 Period Bleed", "#E63946"),
            ("🥚 Ovulation Day", "#B5179E"),
            ("✨ Fertile Window", "#F4A261"),
            ("⚡ PMS Window", "#E76F51"),
            ("🔮 Predicted Period", "#52B788"),
            ("🔵 Today", "#0077B6"),
        ]
        for label, color in items:
            p = ctk.CTkFrame(leg_inner, fg_color="transparent")
            p.pack(side="left", expand=True)
            dot = ctk.CTkFrame(p, width=12, height=12, corner_radius=6, fg_color=color)
            dot.pack(side="left", padx=(0, 5))
            ctk.CTkLabel(p, text=label, font=ctk.CTkFont(size=12)).pack(side="left")

    def _prev_month(self) -> None:
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.render_calendar()

    def _next_month(self) -> None:
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.render_calendar()

    def _jump_today(self) -> None:
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.render_calendar()

    def render_calendar(self) -> None:
        for widget in self.grid_container.winfo_children():
            widget.destroy()

        month_name = calendar.month_name[self.month]
        self.month_lbl.configure(text=f"{month_name} {self.year}")

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

        cal = calendar.Calendar(firstweekday=6)  # Sunday first
        days_header = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        for col, h_name in enumerate(days_header):
            lbl = ctk.CTkLabel(
                self.grid_container,
                text=h_name,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#E05688",
            )
            lbl.grid(row=0, column=col, sticky="nsew", padx=3, pady=(0, 6))

        month_weeks = cal.monthdatescalendar(self.year, self.month)

        for row_idx, week in enumerate(month_weeks, start=1):
            for col_idx, d in enumerate(week):
                is_curr_month = (d.month == self.month)
                log = analyzer.log_map.get(d)
                is_today = (d == today)

                # Determine badge styling
                cell_bg = ("#FFFFFF", "#2B2D31") if is_curr_month else ("#E9ECEF", "#1E1F22")
                border_color = None
                border_width = 0

                tag_text = ""
                tag_color = "#D94073"

                if is_today:
                    border_color = "#0077B6"
                    border_width = 2

                if log and log.flow.is_bleeding():
                    tag_text = f"🩸 {log.flow.value.title()}"
                    tag_color = "#E63946"
                elif d == prediction.ovulation_date:
                    tag_text = "🥚 Ovulation"
                    tag_color = "#B5179E"
                elif prediction.fertile_window_start <= d <= prediction.fertile_window_end:
                    tag_text = "✨ Fertile"
                    tag_color = "#F4A261"
                elif d == prediction.next_period_start:
                    tag_text = "🔮 Period"
                    tag_color = "#52B788"
                elif prediction.confidence_interval_80[0] <= d <= prediction.confidence_interval_80[1]:
                    tag_text = "🔮 Expected"
                    tag_color = "#2D6A4F"
                elif prediction.pms_window_start <= d <= prediction.pms_window_end:
                    tag_text = "⚡ PMS"
                    tag_color = "#E76F51"

                # Cell button frame
                cell = ctk.CTkFrame(
                    self.grid_container,
                    fg_color=cell_bg,
                    corner_radius=8,
                    border_width=border_width,
                    border_color=border_color,
                    height=70,
                )
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
                self.grid_container.grid_columnconfigure(col_idx, weight=1)

                # Top row: Day number
                top_row = ctk.CTkFrame(cell, fg_color="transparent")
                top_row.pack(fill="x", padx=4, pady=(3, 0))

                num_color = "white" if is_curr_month else "gray"
                if is_today:
                    num_color = "#0077B6"

                day_num_lbl = ctk.CTkLabel(
                    top_row,
                    text=str(d.day),
                    font=ctk.CTkFont(size=13, weight="bold" if (is_today or is_curr_month) else "normal"),
                    text_color=num_color,
                )
                day_num_lbl.pack(side="left")

                # Indicators for log entries
                if log:
                    ind_txt = "📝"
                    if log.bbt:
                        ind_txt += f" {log.bbt:.1f}°"
                    ctk.CTkLabel(
                        top_row,
                        text=ind_txt,
                        font=ctk.CTkFont(size=10),
                        text_color="gray",
                    ).pack(side="right")

                # Bottom row: Phase Badge / Tag
                if tag_text:
                    tag_lbl = ctk.CTkLabel(
                        cell,
                        text=tag_text,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=tag_color,
                    )
                    tag_lbl.pack(anchor="w", padx=4, pady=(2, 0))

                # Bind click on cell to jump to logging that date
                target_d = d

                def make_click_handler(click_date):
                    return lambda event: self.on_select_date(click_date)

                cell.bind("<Button-1>", make_click_handler(target_d))
                day_num_lbl.bind("<Button-1>", make_click_handler(target_d))
                top_row.bind("<Button-1>", make_click_handler(target_d))
