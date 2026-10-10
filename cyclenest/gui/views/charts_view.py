"""Interactive Embedded Matplotlib Charts View for CycleNest GUI.
"""

from __future__ import annotations
from typing import Callable, List
import customtkinter as ctk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from cyclenest.analyzer import CycleAnalyzer


class ChartsView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        analyzer_callback: Callable[[], CycleAnalyzer],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.analyzer_callback = analyzer_callback
        self.current_tab = "Cycle Lengths"
        self.canvas: FigureCanvasTkAgg | None = None

        self._build_ui()
        self.render_chart()

    def _build_ui(self) -> None:
        # Header & Segmented Button
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title = ctk.CTkLabel(
            top_bar,
            text="📈 Visual Health & Biological Trends",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E05688",
        )
        title.pack(side="left")

        self.tab_seg = ctk.CTkSegmentedButton(
            top_bar,
            values=["Cycle Lengths", "BBT Temperature", "Symptoms", "Pain Profile"],
            command=self._on_tab_change,
            selected_color="#D94073",
            selected_hover_color="#B83262",
            height=34,
        )
        self.tab_seg.set("Cycle Lengths")
        self.tab_seg.pack(side="right")

        # Container for matplotlib canvas
        self.chart_container = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        self.chart_container.pack(fill="both", expand=True, padx=25, pady=(5, 20))

    def _on_tab_change(self, choice: str) -> None:
        self.current_tab = choice
        self.render_chart()

    def render_chart(self) -> None:
        # Clear existing canvas
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        analyzer = self.analyzer_callback()
        fig = Figure(figsize=(8.5, 4.8), dpi=100)

        # Matplotlib theme colors based on current CTk appearance
        mode = ctk.get_appearance_mode().lower()
        is_dark = (mode != "light")
        bg_color = "#202124" if is_dark else "#F4F4F6"
        text_color = "#FFFFFF" if is_dark else "#1A1A1A"
        grid_color = "#333538" if is_dark else "#E0E0E0"

        fig.patch.set_facecolor(bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)
        ax.tick_params(colors=text_color, labelsize=10)
        ax.grid(True, linestyle="--", alpha=0.4, color=grid_color)
        for spine in ax.spines.values():
            spine.set_color(grid_color)

        if self.current_tab == "Cycle Lengths":
            self._plot_cycle_lengths(ax, analyzer, text_color)
        elif self.current_tab == "BBT Temperature":
            self._plot_bbt(ax, analyzer, text_color)
        elif self.current_tab == "Symptoms":
            self._plot_symptoms(ax, analyzer, text_color)
        elif self.current_tab == "Pain Profile":
            self._plot_pain(ax, analyzer, text_color)

        fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    def _plot_cycle_lengths(self, ax, analyzer: CycleAnalyzer, text_color: str) -> None:
        completed = analyzer.get_completed_cycles()
        if not completed:
            ax.text(0.5, 0.5, "Log at least 2 full cycles to view length progression.", ha="center", va="center", color="gray", fontsize=13)
            return

        cycle_labels = [f"Cycle #{c.cycle_number}" for c in completed]
        lens = [c.length_days for c in completed]
        avg_len = sum(lens) / len(lens)

        # Highlight normal clinical band (24-38 days)
        ax.axhspan(24, 38, color="#2D6A4F", alpha=0.15, label="Normal Range (24-38d)")
        ax.axhline(avg_len, color="#FFAA00", linestyle="--", linewidth=1.8, label=f"Your Average ({avg_len:.1f}d)")

        bars = ax.bar(cycle_labels, lens, color="#D94073", width=0.5, edgecolor="#B83262", linewidth=1.2)
        ax.set_ylabel("Cycle Length (Days)", color=text_color, fontsize=12)
        ax.set_title("Historical Cycle Length Progression vs. Clinical Normal Zone", color=text_color, fontsize=14, weight="bold")
        ax.set_ylim(min(18, min(lens) - 2), max(42, max(lens) + 3))

        for bar, l in zip(bars, lens):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6, f"{l}d", ha="center", va="bottom", color=text_color, fontweight="bold")

        ax.legend(facecolor=ax.get_facecolor(), edgecolor="gray", labelcolor=text_color)

    def _plot_bbt(self, ax, analyzer: CycleAnalyzer, text_color: str) -> None:
        bbt_logs = [l for l in analyzer.logs if l.bbt is not None]
        if len(bbt_logs) < 5:
            ax.text(0.5, 0.5, "Log at least 5 morning BBT entries to view thermal curve.", ha="center", va="center", color="gray", fontsize=13)
            return

        recent = bbt_logs[-32:]
        dates = [l.date.strftime("%b %d") for l in recent]
        temps = [l.bbt for l in recent]
        avg_temp = sum(temps) / len(temps)

        # Coverline
        ax.axhline(avg_temp, color="gray", linestyle=":", linewidth=1.5, label=f"Coverline ({avg_temp:.2f}°C)")

        ax.plot(dates, temps, marker="o", color="#E05688", linewidth=2, markersize=6, label="Morning BBT")

        # Color high vs low points
        high_dates = [d for d, t in zip(dates, temps) if t >= avg_temp]
        high_temps = [t for t in temps if t >= avg_temp]
        ax.scatter(high_dates, high_temps, color="#FFB703", s=60, zorder=5, label="Elevated (Luteal Phase)")

        ax.set_ylabel("Basal Body Temperature (°C)", color=text_color, fontsize=12)
        ax.set_title("Basal Body Temperature (BBT) Biphasic Shift Curve", color=text_color, fontsize=14, weight="bold")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(facecolor=ax.get_facecolor(), edgecolor="gray", labelcolor=text_color)

    def _plot_symptoms(self, ax, analyzer: CycleAnalyzer, text_color: str) -> None:
        s_data = analyzer.analyze_symptom_patterns()
        top_syms = s_data.get("top_symptoms", [])[:8]

        if not top_syms:
            ax.text(0.5, 0.5, "No symptoms logged yet.", ha="center", va="center", color="gray", fontsize=13)
            return

        sym_names = [s[0] for s in reversed(top_syms)]
        counts = [s[1] for s in reversed(top_syms)]

        bars = ax.barh(sym_names, counts, color="#5E60CE", height=0.55, edgecolor="#3E4092")
        ax.set_xlabel("Occurrence Frequency (Days)", color=text_color, fontsize=12)
        ax.set_title("Top Reported Symptoms & Occurrence Frequency", color=text_color, fontsize=14, weight="bold")

        for bar, c in zip(bars, counts):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2, f"{c}x", ha="left", va="center", color=text_color, fontweight="bold")

    def _plot_pain(self, ax, analyzer: CycleAnalyzer, text_color: str) -> None:
        s_data = analyzer.analyze_symptom_patterns()
        cramps_by_day = s_data.get("avg_cramps_by_day", {})

        days = list(range(1, 8))
        pains = [cramps_by_day.get(d, 0.0) for d in days]

        if sum(pains) == 0:
            ax.text(0.5, 0.5, "No cramp / pelvic pain logged yet.", ha="center", va="center", color="gray", fontsize=13)
            return

        day_labels = [f"Day {d}" for d in days]
        bars = ax.bar(day_labels, pains, color="#E63946", width=0.5, edgecolor="#9D0208")
        ax.set_ylabel("Average Pain Intensity (0-5)", color=text_color, fontsize=12)
        ax.set_title("Menstrual Cramp / Pelvic Pain Intensity by Cycle Day", color=text_color, fontsize=14, weight="bold")
        ax.set_ylim(0, 5.5)

        for bar, p in zip(bars, pains):
            if p > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15, f"{p:.1f}", ha="center", va="bottom", color=text_color, fontweight="bold")
