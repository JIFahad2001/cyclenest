"""Pattern and Clinical Regularity Analytics View for CycleNest GUI.
"""

from __future__ import annotations
from typing import Callable
import customtkinter as ctk

from cyclenest.analyzer import CycleAnalyzer


class AnalyticsView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        analyzer_callback: Callable[[], CycleAnalyzer],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.analyzer_callback = analyzer_callback

        self.refresh()

    def refresh(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        analyzer = self.analyzer_callback()
        stats = analyzer.compute_statistics()
        symptom_data = analyzer.analyze_symptom_patterns()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="📊 Pattern & Gynecological Regularity Analytics",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E05688",
        )
        title.pack(anchor="w")

        # 1. FIGO Regularity Rating Card
        reg_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        reg_card.pack(fill="x", padx=25, pady=8)

        r_inner = ctk.CTkFrame(reg_card, fg_color="transparent")
        r_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            r_inner,
            text="FIGO Regularity Classification",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(anchor="w")

        status_text = stats["regularity_status"]
        reg_colors = {
            "high": ("#2D6A4F", "#52B788"),
            "normal": ("#2D6A4F", "#52B788"),
            "mild": ("#C77700", "#FFD166"),
            "irregular": ("#D90429", "#FF4D4D"),
            "short": ("#D90429", "#FF4D4D"),
            "long": ("#D90429", "#FF4D4D"),
        }
        color = reg_colors.get(stats["regularity_code"], ("#6C757D", "white"))

        ctk.CTkLabel(
            r_inner,
            text=status_text,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=color[1],
        ).pack(anchor="w", pady=(2, 6))

        expl = (
            f"Based on International Federation of Gynecology and Obstetrics guidelines. "
            f"Cycles vary by ±{stats['std_cycle_length']} days across history "
            f"(Range: {stats['min_cycle_length']} - {stats['max_cycle_length']} days)."
        )
        ctk.CTkLabel(r_inner, text=expl, font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")

        # 2. Key Metrics Grid (4 Stat Boxes)
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=8)

        b1 = self._stat_box(grid, "Recorded Cycles", f"{stats['cycle_count']} ({stats['completed_cycles']} completed)")
        b1.pack(side="left", fill="both", expand=True, padx=(0, 6))

        b2 = self._stat_box(grid, "Average Cycle Length", f"{stats['mean_cycle_length']} Days (Median: {stats['median_cycle_length']}d)")
        b2.pack(side="left", fill="both", expand=True, padx=4)

        b3 = self._stat_box(grid, "Variability (Std Dev)", f"±{stats['std_cycle_length']} Days (IQR: {stats['iqr_cycle_length']}d)")
        b3.pack(side="left", fill="both", expand=True, padx=4)

        b4 = self._stat_box(grid, "Average Period Flow", f"{stats['mean_period_length']} Days (Median: {stats['median_period_length']}d)")
        b4.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # 3. Two Columns: PMS Symptom Clusters & BBT Phase Shifts
        row_two = ctk.CTkFrame(self, fg_color="transparent")
        row_two.pack(fill="x", padx=25, pady=8)

        # PMS Cluster Card
        pms_card = ctk.CTkFrame(row_two, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        pms_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        p_inner = ctk.CTkFrame(pms_card, fg_color="transparent")
        p_inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            p_inner,
            text="⚡ Identified PMS Symptom Cluster",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            p_inner,
            text="Symptoms clustering during the pre-menstrual luteal window (5 days before bleeding):",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=350,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        pms_syms = symptom_data.get("pms_symptoms", [])
        if pms_syms:
            for sym, count in pms_syms:
                r = ctk.CTkFrame(p_inner, fg_color="transparent")
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text=f"• {sym}", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
                ctk.CTkLabel(r, text=f"{count} times", font=ctk.CTkFont(size=13), text_color="gray").pack(side="right")
        else:
            ctk.CTkLabel(p_inner, text="No pre-menstrual symptoms recorded yet.", font=ctk.CTkFont(size=13, slant="italic"), text_color="gray").pack(anchor="w")

        # BBT Phase Card
        bbt_card = ctk.CTkFrame(row_two, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        bbt_card.pack(side="right", fill="both", expand=True, padx=(8, 0))

        b_inner = ctk.CTkFrame(bbt_card, fg_color="transparent")
        b_inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            b_inner,
            text="🌡️ BBT Phase Thermal Distribution",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            b_inner,
            text="Morning Basal Body Temperature shifts driven by progesterone:",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(anchor="w", pady=(0, 10))

        bbt_phases = symptom_data.get("avg_bbt_by_phase", {})
        if bbt_phases:
            for ph_key, t_val in bbt_phases.items():
                r = ctk.CTkFrame(b_inner, fg_color="transparent")
                r.pack(fill="x", pady=2)
                ph_name = ph_key.replace("_", " ").title()
                ctk.CTkLabel(r, text=f"• {ph_name}", font=ctk.CTkFont(size=13)).pack(side="left")
                ctk.CTkLabel(r, text=f"{t_val:.2f}°C", font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFB703").pack(side="right")
        else:
            ctk.CTkLabel(b_inner, text="Insufficient BBT logs for phase calculation.", font=ctk.CTkFont(size=13, slant="italic"), text_color="gray").pack(anchor="w")

        # 4. Cramp / Pain Intensity Progression by Cycle Day
        cramp_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        cramp_card.pack(fill="x", padx=25, pady=(8, 25))

        c_inner = ctk.CTkFrame(cramp_card, fg_color="transparent")
        c_inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            c_inner,
            text="⚡ Pelvic Pain / Cramps Intensity Profile",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        ).pack(anchor="w", pady=(0, 8))

        cramps_by_day = symptom_data.get("avg_cramps_by_day", {})
        if cramps_by_day:
            for day in range(1, 8):
                if day in cramps_by_day:
                    avg_p = cramps_by_day[day]
                    r = ctk.CTkFrame(c_inner, fg_color="transparent")
                    r.pack(fill="x", pady=2)
                    ctk.CTkLabel(r, text=f"Cycle Day {day}:", font=ctk.CTkFont(size=13), width=100, anchor="w").pack(side="left")

                    p_bar = ctk.CTkProgressBar(r, height=12, progress_color="#E63946")
                    p_bar.set(avg_p / 5.0)
                    p_bar.pack(side="left", fill="x", expand=True, padx=10)

                    ctk.CTkLabel(r, text=f"{avg_p:.1f} / 5.0", font=ctk.CTkFont(size=13, weight="bold"), width=60, anchor="e").pack(side="right")
        else:
            ctk.CTkLabel(c_inner, text="No pelvic pain / cramps logged yet.", font=ctk.CTkFont(size=13, slant="italic"), text_color="gray").pack(anchor="w")

    def _stat_box(self, parent, title: str, val: str):
        box = ctk.CTkFrame(parent, corner_radius=10, fg_color=("#F4F4F6", "#202124"))
        b_inner = ctk.CTkFrame(box, fg_color="transparent")
        b_inner.pack(padx=12, pady=12)
        ctk.CTkLabel(b_inner, text=title, font=ctk.CTkFont(size=12), text_color="gray").pack()
        ctk.CTkLabel(b_inner, text=val, font=ctk.CTkFont(size=14, weight="bold"), text_color=("#B83262", "#FF6B9D")).pack(pady=(4, 0))
        return box
