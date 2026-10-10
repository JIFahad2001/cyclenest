"""Main CustomTkinter GUI Window for CycleNest.
"""

from __future__ import annotations
import sys
from datetime import date
from typing import Optional, Dict
from pathlib import Path

import customtkinter as ctk

from cyclenest.db import Database, DEFAULT_DB_PATH
from cyclenest.analyzer import CycleAnalyzer
from cyclenest.predictor import EnsembleCyclePredictor
from cyclenest.gui.views.dashboard_view import DashboardView
from cyclenest.gui.views.logging_view import LoggingView
from cyclenest.gui.views.calendar_view import CalendarView
from cyclenest.gui.views.predictions_view import PredictionsView
from cyclenest.gui.views.analytics_view import AnalyticsView
from cyclenest.gui.views.charts_view import ChartsView
from cyclenest.gui.views.history_view import HistoryView
from cyclenest.gui.views.settings_view import SettingsView


class CycleNestApp(ctk.CTk):
    def __init__(self, db_path: Optional[str] = None):
        super().__init__()

        # Window Configuration
        self.title("🌸 CycleNest — Menstrual Cycle Tracking & Predictive Intelligence")
        self.geometry("1140x760")
        self.minsize(980, 640)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Database & Intelligence Services
        self.db = Database(db_path)
        self.predictor = EnsembleCyclePredictor()

        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_views()

        # Initial view
        self.navigate("dashboard")

    def get_analyzer(self) -> CycleAnalyzer:
        logs = self.db.get_all_daily_logs()
        def_c = int(self.db.get_setting("default_cycle_length", "28"))
        def_p = int(self.db.get_setting("default_period_length", "5"))
        def_l = int(self.db.get_setting("default_luteal_length", "14"))
        return CycleAnalyzer(
            logs=logs,
            default_cycle_length=def_c,
            default_period_length=def_p,
            default_luteal_length=def_l,
        )

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#F8F9FA", "#1A1A1E"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Branding
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=18, pady=(20, 25))

        logo_lbl = ctk.CTkLabel(
            brand_frame,
            text="🌸 CycleNest",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#E05688",
        )
        logo_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            brand_frame,
            text="Cycle Intelligence Suite",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        sub_lbl.pack(anchor="w")

        # Nav Buttons
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("log", "✍️  Daily Log"),
            ("calendar", "🗓️  Calendar"),
            ("predictions", "🔮  Predictions"),
            ("analytics", "📊  Analytics"),
            ("charts", "📈  Visual Trends"),
            ("history", "📜  Log History"),
            ("settings", "⚙️  Settings"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=ctk.CTkFont(size=14, weight="normal"),
                anchor="w",
                fg_color="transparent",
                text_color=("gray20", "gray85"),
                hover_color=("#F0D4E0", "#2D1D27"),
                height=40,
                corner_radius=10,
                command=lambda k=key: self.navigate(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[key] = btn

        # Bottom Version & Status
        bottom_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=18, pady=20)

        ctk.CTkLabel(
            bottom_box,
            text="v1.0.0 Desktop GUI",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w")

        ctk.CTkLabel(
            bottom_box,
            text="🔒 100% Offline & Private",
            font=ctk.CTkFont(size=10),
            text_color="#52B788",
        ).pack(anchor="w")

    def _build_main_views(self) -> None:
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.views = {
            "dashboard": DashboardView(
                self.container,
                analyzer_callback=self.get_analyzer,
                predictor=self.predictor,
                on_navigate=self.navigate,
                fg_color="transparent",
            ),
            "log": LoggingView(
                self.container,
                db=self.db,
                on_saved=self._on_data_modified,
                fg_color="transparent",
            ),
            "calendar": CalendarView(
                self.container,
                analyzer_callback=self.get_analyzer,
                predictor=self.predictor,
                on_select_date=self._open_log_for_date,
                fg_color="transparent",
            ),
            "predictions": PredictionsView(
                self.container,
                analyzer_callback=self.get_analyzer,
                predictor=self.predictor,
                fg_color="transparent",
            ),
            "analytics": AnalyticsView(
                self.container,
                analyzer_callback=self.get_analyzer,
                fg_color="transparent",
            ),
            "charts": ChartsView(
                self.container,
                analyzer_callback=self.get_analyzer,
                fg_color="transparent",
            ),
            "history": HistoryView(
                self.container,
                db=self.db,
                on_edit_date=self._open_log_for_date,
                fg_color="transparent",
            ),
            "settings": SettingsView(
                self.container,
                db=self.db,
                on_data_updated=self._on_data_modified,
                fg_color="transparent",
            ),
        }

    def navigate(self, view_name: str, target_date: Optional[date] = None) -> None:
        if view_name not in self.views:
            return

        # Hide all views
        for v in self.views.values():
            v.grid_forget()

        # Update button highlights
        for key, btn in self.nav_buttons.items():
            if key == view_name:
                btn.configure(
                    fg_color=("#FCE4EC", "#3B1B2A"),
                    text_color="#E05688",
                    font=ctk.CTkFont(size=14, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray20", "gray85"),
                    font=ctk.CTkFont(size=14, weight="normal"),
                )

        target_view = self.views[view_name]
        target_view.grid(row=0, column=0, sticky="nsew")

        # Specific view activations
        if view_name == "log" and target_date:
            target_view.load_date(target_date)
        elif hasattr(target_view, "refresh"):
            target_view.refresh()

    def _open_log_for_date(self, target_date: date) -> None:
        self.navigate("log", target_date)

    def _on_data_modified(self) -> None:
        # Refresh current analyzer and active views
        for name, v in self.views.items():
            if name != "log" and hasattr(v, "refresh"):
                v.refresh()
            elif name == "charts" and hasattr(v, "render_chart"):
                v.render_chart()
            elif name == "calendar" and hasattr(v, "render_calendar"):
                v.render_calendar()


def launch_gui(db_path: Optional[str] = None) -> None:
    app = CycleNestApp(db_path=db_path)
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
