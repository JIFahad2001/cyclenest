"""Settings and Data Management View for CycleNest GUI.
"""

from __future__ import annotations
from tkinter import filedialog, messagebox
from typing import Callable
from datetime import date
import customtkinter as ctk

from cyclenest.db import Database
from cyclenest.sample_data import generate_sample_data
from cyclenest.export import export_to_csv, export_to_json, import_from_csv, import_from_json


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        db: Database,
        on_data_updated: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.db = db
        self.on_data_updated = on_data_updated

        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="⚙️ Preferences & Data Management",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E05688",
        )
        title.pack(anchor="w")

        # 1. Appearance Mode
        app_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        app_card.pack(fill="x", padx=25, pady=8)

        a_inner = ctk.CTkFrame(app_card, fg_color="transparent")
        a_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(a_inner, text="🎨 Theme & Appearance", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        row1 = ctk.CTkFrame(a_inner, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text="Color Theme:", font=ctk.CTkFont(size=14)).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            row1,
            values=["Dark", "Light", "System"],
            command=self._on_theme_change,
            fg_color="#D94073",
            button_color="#B83262",
            height=32,
        )
        self.theme_menu.set(ctk.get_appearance_mode().title())
        self.theme_menu.pack(side="right")

        # 2. Cycle Baseline Defaults
        base_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        base_card.pack(fill="x", padx=25, pady=8)

        b_inner = ctk.CTkFrame(base_card, fg_color="transparent")
        b_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(b_inner, text="📐 Personal Biological Baselines", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        # Defaults
        c_len = self.db.get_setting("default_cycle_length", "28")
        p_len = self.db.get_setting("default_period_length", "5")
        l_len = self.db.get_setting("default_luteal_length", "14")

        # Cycle Length
        cr1 = ctk.CTkFrame(b_inner, fg_color="transparent")
        cr1.pack(fill="x", pady=4)
        ctk.CTkLabel(cr1, text="Default Cycle Length (days):", font=ctk.CTkFont(size=14)).pack(side="left")
        self.cycle_len_entry = ctk.CTkEntry(cr1, width=80, height=32)
        self.cycle_len_entry.insert(0, c_len)
        self.cycle_len_entry.pack(side="right")

        # Period Length
        cr2 = ctk.CTkFrame(b_inner, fg_color="transparent")
        cr2.pack(fill="x", pady=4)
        ctk.CTkLabel(cr2, text="Default Period Bleeding Duration (days):", font=ctk.CTkFont(size=14)).pack(side="left")
        self.period_len_entry = ctk.CTkEntry(cr2, width=80, height=32)
        self.period_len_entry.insert(0, p_len)
        self.period_len_entry.pack(side="right")

        # Luteal Length
        cr3 = ctk.CTkFrame(b_inner, fg_color="transparent")
        cr3.pack(fill="x", pady=4)
        ctk.CTkLabel(cr3, text="Default Luteal Phase Length (days, post-ovulation):", font=ctk.CTkFont(size=14)).pack(side="left")
        self.luteal_len_entry = ctk.CTkEntry(cr3, width=80, height=32)
        self.luteal_len_entry.insert(0, l_len)
        self.luteal_len_entry.pack(side="right")

        save_base_btn = ctk.CTkButton(
            b_inner,
            text="Save Baselines",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#D94073",
            hover_color="#B83262",
            height=34,
            command=self._save_baselines,
        )
        save_base_btn.pack(anchor="e", pady=(10, 0))

        # 3. Data Backup, Export & Benchmark Data
        data_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        data_card.pack(fill="x", padx=25, pady=8)

        d_inner = ctk.CTkFrame(data_card, fg_color="transparent")
        d_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(d_inner, text="💾 Data Management & Privacy", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            d_inner,
            text=f"Your data is stored locally in an encrypted SQLite database at: {self.db.db_path}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(anchor="w", pady=(0, 12))

        # Buttons Grid
        btn_grid = ctk.CTkFrame(d_inner, fg_color="transparent")
        btn_grid.pack(fill="x", pady=5)

        # Preload Benchmark Data
        ctk.CTkButton(
            btn_grid,
            text="⚡ Load 6-Month Clinical Benchmark Data",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2D6A4F", "#1B4332"),
            hover_color="#081C15",
            height=36,
            command=self._load_benchmark,
        ).pack(fill="x", pady=4)

        # Export CSV / JSON
        exp_row = ctk.CTkFrame(btn_grid, fg_color="transparent")
        exp_row.pack(fill="x", pady=4)

        ctk.CTkButton(
            exp_row,
            text="📤 Export to CSV",
            height=34,
            command=self._export_csv,
            fg_color=("#6C757D", "#343A40"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            exp_row,
            text="📤 Export to JSON",
            height=34,
            command=self._export_json,
            fg_color=("#6C757D", "#343A40"),
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Import CSV / JSON
        imp_row = ctk.CTkFrame(btn_grid, fg_color="transparent")
        imp_row.pack(fill="x", pady=4)

        ctk.CTkButton(
            imp_row,
            text="📥 Import from CSV",
            height=34,
            command=self._import_csv,
            fg_color=("#6C757D", "#343A40"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            imp_row,
            text="📥 Import from JSON",
            height=34,
            command=self._import_json,
            fg_color=("#6C757D", "#343A40"),
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Clear All Data
        ctk.CTkButton(
            btn_grid,
            text="⚠️ Wipe All Stored Data",
            font=ctk.CTkFont(size=13),
            fg_color="#E63946",
            hover_color="#C1121F",
            height=36,
            command=self._clear_data,
        ).pack(fill="x", pady=(12, 4))

    def _on_theme_change(self, mode: str) -> None:
        ctk.set_appearance_mode(mode.lower())

    def _save_baselines(self) -> None:
        c_val = self.cycle_len_entry.get().strip()
        p_val = self.period_len_entry.get().strip()
        l_val = self.luteal_len_entry.get().strip()

        if c_val.isdigit():
            self.db.set_setting("default_cycle_length", c_val)
        if p_val.isdigit():
            self.db.set_setting("default_period_length", p_val)
        if l_val.isdigit():
            self.db.set_setting("default_luteal_length", l_val)

        messagebox.showinfo("CycleNest", "Personal baselines updated successfully!")
        self.on_data_updated()

    def _load_benchmark(self) -> None:
        if messagebox.askyesno("Load Benchmark Data", "Load 6 months of realistic clinical benchmark cycles? This will add realistic symptoms, BBT shifts, and moods."):
            sample_logs = generate_sample_data(date.today())
            self.db.batch_save_logs(sample_logs)
            messagebox.showinfo("CycleNest", f"Loaded {len(sample_logs)} benchmark logs across 6 cycles!")
            self.on_data_updated()

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            logs = self.db.get_all_daily_logs()
            count = export_to_csv(logs, path)
            messagebox.showinfo("CycleNest", f"Exported {count} logs to {path}")

    def _export_json(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            logs = self.db.get_all_daily_logs()
            count = export_to_json(logs, path)
            messagebox.showinfo("CycleNest", f"Exported {count} logs to {path}")

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                logs = import_from_csv(path)
                self.db.batch_save_logs(logs)
                messagebox.showinfo("CycleNest", f"Successfully imported {len(logs)} logs!")
                self.on_data_updated()
            except Exception as e:
                messagebox.showerror("Import Error", str(e))

    def _import_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            try:
                logs = import_from_json(path)
                self.db.batch_save_logs(logs)
                messagebox.showinfo("CycleNest", f"Successfully imported {len(logs)} logs!")
                self.on_data_updated()
            except Exception as e:
                messagebox.showerror("Import Error", str(e))

    def _clear_data(self) -> None:
        if messagebox.askyesno("Clear All Data", "⚠️ Are you sure you want to permanently delete all health logs? This cannot be undone."):
            self.db.clear_all()
            messagebox.showinfo("CycleNest", "All data has been cleared.")
            self.on_data_updated()
