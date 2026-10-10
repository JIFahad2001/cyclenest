"""Multi-Model Prediction & Forecasting View for CycleNest GUI.
"""

from __future__ import annotations
from typing import Callable, List
import customtkinter as ctk

from cyclenest.analyzer import CycleAnalyzer
from cyclenest.predictor import EnsembleCyclePredictor
from cyclenest.models import PredictionResult


class PredictionsView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        analyzer_callback: Callable[[], CycleAnalyzer],
        predictor: EnsembleCyclePredictor,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.analyzer_callback = analyzer_callback
        self.predictor = predictor

        self.refresh()

    def refresh(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        analyzer = self.analyzer_callback()
        completed = analyzer.get_completed_cycles()
        current = analyzer.get_current_cycle()
        logs = analyzer.logs

        consensus = self.predictor.predict(
            completed,
            current,
            logs,
            analyzer.default_cycle_length,
            analyzer.default_luteal_length,
        )

        all_models = self.predictor.get_all_model_predictions(
            completed,
            current,
            logs,
            analyzer.default_cycle_length,
            analyzer.default_luteal_length,
        )

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="🔮 Predictive Models & Horizon Forecasting",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E05688",
        )
        title.pack(anchor="w")

        sub = ctk.CTkLabel(
            header,
            text="Multi-architecture comparative modeling synthesizing recency weighting, Bayesian credible intervals, and real-time biomarkers.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        sub.pack(anchor="w")

        # Featured Hero Card: Smart Ensemble Consensus
        hero = ctk.CTkFrame(self, corner_radius=16, fg_color=("#E8F5E9", "#1B3828"))
        hero.pack(fill="x", padx=25, pady=10)

        hero_inner = ctk.CTkFrame(hero, fg_color="transparent")
        hero_inner.pack(fill="both", expand=True, padx=22, pady=18)

        # Top row: title & confidence
        top_row = ctk.CTkFrame(hero_inner, fg_color="transparent")
        top_row.pack(fill="x")

        hero_title = ctk.CTkLabel(
            top_row,
            text="⭐ Smart Ensemble Consensus Prediction",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#2E7D32", "#81C784"),
        )
        hero_title.pack(side="left")

        conf_badge = ctk.CTkButton(
            top_row,
            text=f"{int(consensus.confidence_score * 100)}% Confidence",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#81C784", "#2E7D32"),
            text_color="white",
            hover=False,
            height=28,
            corner_radius=14,
        )
        conf_badge.pack(side="right")

        # Metrics row
        metrics_row = ctk.CTkFrame(hero_inner, fg_color="transparent")
        metrics_row.pack(fill="x", pady=(15, 12))

        m1 = self._build_stat_box(
            metrics_row, "Next Period Start", consensus.next_period_start.strftime("%A, %b %d, %Y"), "#E63946"
        )
        m1.pack(side="left", fill="both", expand=True, padx=(0, 6))

        m2 = self._build_stat_box(
            metrics_row, "Predicted Cycle Length", f"{consensus.predicted_cycle_length:.1f} Days", "#2A9D8F"
        )
        m2.pack(side="left", fill="both", expand=True, padx=4)

        m3 = self._build_stat_box(
            metrics_row, "Ovulation Day", consensus.ovulation_date.strftime("%b %d, %Y"), "#B5179E"
        )
        m3.pack(side="left", fill="both", expand=True, padx=4)

        m4 = self._build_stat_box(
            metrics_row, "Fertile Window", f"{consensus.fertile_window_start.strftime('%b %d')} - {consensus.fertile_window_end.strftime('%b %d')}", "#F4A261"
        )
        m4.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # Credible intervals & Explanation
        ci80_str = f"{consensus.confidence_interval_80[0].strftime('%b %d')} - {consensus.confidence_interval_80[1].strftime('%b %d')}"
        ci95_str = f"{consensus.confidence_interval_95[0].strftime('%b %d')} - {consensus.confidence_interval_95[1].strftime('%b %d')}"

        expl_text = (
            f"80% Credible Range: {ci80_str}  |  95% Credible Range: {ci95_str}\n"
            f"Consensus Methodology: {consensus.explanation}"
        )
        ctk.CTkLabel(
            hero_inner,
            text=expl_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

        # Comparative Architecture Section
        ctk.CTkLabel(
            self,
            text="🔬 Individual Architecture Comparison",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#E05688",
        ).pack(anchor="w", padx=25, pady=(15, 6))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=5)

        for idx, model in enumerate(all_models):
            card = ctk.CTkFrame(grid, corner_radius=12, fg_color=("#F4F4F6", "#202124"))
            card.pack(fill="x", pady=5)

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="both", expand=True, padx=16, pady=12)

            top = ctk.CTkFrame(card_inner, fg_color="transparent")
            top.pack(fill="x")

            ctk.CTkLabel(
                top,
                text=model.model_name,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=("#B83262", "#FF6B9D"),
            ).pack(side="left")

            ctk.CTkLabel(
                top,
                text=f"{int(model.confidence_score * 100)}% Conf.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="gray",
            ).pack(side="right")

            # Row with stats
            stat_row = ctk.CTkFrame(card_inner, fg_color="transparent")
            stat_row.pack(fill="x", pady=4)

            s_text = (
                f"Next Period: {model.next_period_start.strftime('%b %d, %Y')}  |  "
                f"Cycle Length: {model.predicted_cycle_length:.1f}d  |  "
                f"80% Range: {model.confidence_interval_80[0].strftime('%b %d')} - {model.confidence_interval_80[1].strftime('%b %d')}  |  "
                f"Ovulation: {model.ovulation_date.strftime('%b %d')}"
            )
            ctk.CTkLabel(stat_row, text=s_text, font=ctk.CTkFont(size=13), text_color="white").pack(anchor="w")

            ctk.CTkLabel(
                card_inner,
                text=model.explanation,
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="gray",
            ).pack(anchor="w")

        # Forward Horizon (Next 4 Cycles)
        ctk.CTkLabel(
            self,
            text="🔭 Forward Horizon Projection (Upcoming 4 Cycles)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#E05688",
        ).pack(anchor="w", padx=25, pady=(20, 6))

        forecasts = self.predictor.forecast_upcoming_cycles(
            count=4,
            completed_cycles=completed,
            current_cycle=current,
            recent_logs=logs,
            default_cycle_length=analyzer.default_cycle_length,
            default_luteal_length=analyzer.default_luteal_length,
        )

        f_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("#F4F4F6", "#202124"))
        f_card.pack(fill="x", padx=25, pady=(5, 25))

        f_inner = ctk.CTkFrame(f_card, fg_color="transparent")
        f_inner.pack(fill="both", expand=True, padx=16, pady=12)

        for f in forecasts:
            row = ctk.CTkFrame(f_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(
                row,
                text=f.model_name,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=160,
                anchor="w",
            ).pack(side="left")

            f_info = (
                f"Period Starts: {f.next_period_start.strftime('%b %d, %Y')}  |  "
                f"Length: {round(f.predicted_cycle_length)}d  |  "
                f"Fertile: {f.fertile_window_start.strftime('%b %d')} - {f.fertile_window_end.strftime('%b %d')}  |  "
                f"Ovulation: {f.ovulation_date.strftime('%b %d')}  |  "
                f"PMS Alert: {f.pms_window_start.strftime('%b %d')}"
            )
            ctk.CTkLabel(row, text=f_info, font=ctk.CTkFont(size=13), text_color="white").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(row, text=f"{int(f.confidence_score * 100)}%", font=ctk.CTkFont(size=13, weight="bold"), text_color="gray").pack(side="right")

    def _build_stat_box(self, parent, title: str, val: str, color: str):
        box = ctk.CTkFrame(parent, corner_radius=10, fg_color=("#FFFFFF", "#2B2D31"))
        b_inner = ctk.CTkFrame(box, fg_color="transparent")
        b_inner.pack(padx=12, pady=10)
        ctk.CTkLabel(b_inner, text=title, font=ctk.CTkFont(size=12), text_color="gray").pack()
        ctk.CTkLabel(b_inner, text=val, font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(pady=(2, 0))
        return box
