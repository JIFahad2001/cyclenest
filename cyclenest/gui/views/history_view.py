"""Log History and Record Management View for CycleNest GUI.
"""

from __future__ import annotations
from datetime import date
from typing import Callable, List, Optional
import customtkinter as ctk

from cyclenest.db import Database
from cyclenest.models import DailyLog, FlowLevel


class HistoryView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        db: Database,
        on_edit_date: Callable[[date], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.db = db
        self.on_edit_date = on_edit_date
        self.filter_mode = "All Logs"

        self.refresh()

    def refresh(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        logs = self.db.get_all_daily_logs()
        # Newest first
        sorted_logs = sorted(logs, key=lambda l: l.date, reverse=True)

        if self.filter_mode == "Bleeding Only":
            sorted_logs = [l for l in sorted_logs if l.flow.is_bleeding()]
        elif self.filter_mode == "With Symptoms":
            sorted_logs = [l for l in sorted_logs if l.symptoms or l.moods]

        # Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title = ctk.CTkLabel(
            top_bar,
            text=f"📜 Historical Records ({len(sorted_logs)} entries)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E05688",
        )
        title.pack(side="left")

        filter_menu = ctk.CTkOptionMenu(
            top_bar,
            values=["All Logs", "Bleeding Only", "With Symptoms"],
            command=self._on_filter_change,
            fg_color="#D94073",
            button_color="#B83262",
            height=32,
        )
        filter_menu.set(self.filter_mode)
        filter_menu.pack(side="right")

        if not sorted_logs:
            empty_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("#F4F4F6", "#202124"))
            empty_card.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(
                empty_card,
                text="No logs match the selected filter.",
                font=ctk.CTkFont(size=14, slant="italic"),
                text_color="gray",
            ).pack(padx=20, pady=20)
            return

        # List of cards
        for log in sorted_logs[:50]:  # Up to 50 latest
            card = ctk.CTkFrame(self, corner_radius=12, fg_color=("#F4F4F6", "#202124"))
            card.pack(fill="x", padx=25, pady=4)

            c_inner = ctk.CTkFrame(card, fg_color="transparent")
            c_inner.pack(fill="both", expand=True, padx=16, pady=10)

            # Left side: Date & Badges
            left = ctk.CTkFrame(c_inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            d_row = ctk.CTkFrame(left, fg_color="transparent")
            d_row.pack(anchor="w")

            ctk.CTkLabel(
                d_row,
                text=log.date.strftime("%A, %b %d, %Y"),
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="left")

            if log.flow != FlowLevel.NONE:
                flow_color = "#E63946" if log.flow.is_bleeding() else "#FFAA00"
                ctk.CTkLabel(
                    d_row,
                    text=f"  {log.flow.display_badge()}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=flow_color,
                ).pack(side="left", padx=5)

            if log.cramps_pain > 0:
                ctk.CTkLabel(
                    d_row,
                    text=f"• Pain: {log.cramps_pain}/5",
                    font=ctk.CTkFont(size=12),
                    text_color="#FF6B9D",
                ).pack(side="left", padx=5)

            if log.bbt:
                ctk.CTkLabel(
                    d_row,
                    text=f"• {log.bbt:.2f}°C",
                    font=ctk.CTkFont(size=12),
                    text_color="#FFB703",
                ).pack(side="left", padx=5)

            # Detail summary line
            details = []
            if log.symptoms:
                details.append(f"Symptoms: {', '.join(log.symptoms)}")
            if log.moods:
                details.append(f"Mood: {', '.join(log.moods)}")
            if log.notes:
                details.append(f"Notes: \"{log.notes}\"")

            detail_str = " | ".join(details) if details else "No symptoms or notes recorded."
            ctk.CTkLabel(
                left,
                text=detail_str,
                font=ctk.CTkFont(size=12),
                text_color="gray",
                wraplength=600,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

            # Right side: Edit & Delete buttons
            right = ctk.CTkFrame(c_inner, fg_color="transparent")
            right.pack(side="right")

            target_d = log.date
            edit_btn = ctk.CTkButton(
                right,
                text="Edit",
                width=65,
                height=28,
                fg_color="#D94073",
                hover_color="#B83262",
                command=lambda d=target_d: self.on_edit_date(d),
            )
            edit_btn.pack(side="left", padx=4)

            del_btn = ctk.CTkButton(
                right,
                text="Delete",
                width=65,
                height=28,
                fg_color="#E63946",
                hover_color="#C1121F",
                command=lambda d=target_d: self._delete_entry(d),
            )
            del_btn.pack(side="left", padx=2)

    def _on_filter_change(self, mode: str) -> None:
        self.filter_mode = mode
        self.refresh()

    def _delete_entry(self, entry_date: date) -> None:
        self.db.delete_daily_log(entry_date)
        self.refresh()
