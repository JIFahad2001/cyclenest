"""Daily Logging Form View for CycleNest GUI.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, Callable, Dict, List
import customtkinter as ctk

from cyclenest.models import (
    DailyLog,
    FlowLevel,
    MucusType,
    SexualActivity,
    COMMON_SYMPTOMS,
    COMMON_MOODS,
)
from cyclenest.db import Database


class LoggingView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        db: Database,
        on_saved: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.db = db
        self.on_saved = on_saved
        self.current_date = date.today()

        self.symptom_vars: Dict[str, ctk.BooleanVar] = {}
        self.mood_vars: Dict[str, ctk.BooleanVar] = {}

        self._build_ui()
        self.load_date(self.current_date)

    def _build_ui(self) -> None:
        # Header & Date Switcher
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="✍️ Daily Health & Biomarker Logger",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E05688",
        )
        title.pack(anchor="w")

        # Date Navigator Card
        date_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("#F4F4F6", "#202124"))
        date_card.pack(fill="x", padx=25, pady=8)

        date_inner = ctk.CTkFrame(date_card, fg_color="transparent")
        date_inner.pack(fill="x", padx=15, pady=10)

        prev_btn = ctk.CTkButton(
            date_inner,
            text="◀ Previous Day",
            width=110,
            command=self._prev_day,
            fg_color=("#6C757D", "#343A40"),
        )
        prev_btn.pack(side="left")

        self.date_display = ctk.CTkLabel(
            date_inner,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#B83262", "#FF6B9D"),
        )
        self.date_display.pack(side="left", expand=True)

        today_btn = ctk.CTkButton(
            date_inner,
            text="Today",
            width=70,
            command=self._today,
            fg_color="#D94073",
            hover_color="#B83262",
        )
        today_btn.pack(side="left", padx=5)

        next_btn = ctk.CTkButton(
            date_inner,
            text="Next Day ▶",
            width=110,
            command=self._next_day,
            fg_color=("#6C757D", "#343A40"),
        )
        next_btn.pack(side="right")

        # Toast / Alert banner
        self.alert_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="green")
        self.alert_lbl.pack(pady=(0, 5))

        # Form Container Card
        form = ctk.CTkFrame(self, corner_radius=14, fg_color=("#F4F4F6", "#202124"))
        form.pack(fill="x", padx=25, pady=5)

        form_inner = ctk.CTkFrame(form, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Menstrual Flow
        ctk.CTkLabel(form_inner, text="1. Menstrual Flow Intensity", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(5, 5))
        self.flow_var = ctk.StringVar(value="None")
        self.flow_seg = ctk.CTkSegmentedButton(
            form_inner,
            values=["None", "Spotting", "Light", "Medium", "Heavy", "Super Heavy"],
            variable=self.flow_var,
            selected_color="#D94073",
            selected_hover_color="#B83262",
            height=34,
        )
        self.flow_seg.pack(fill="x", pady=(0, 15))

        # 2. Cramps / Pelvic Pain Slider
        pain_header = ctk.CTkFrame(form_inner, fg_color="transparent")
        pain_header.pack(fill="x", pady=(5, 2))
        ctk.CTkLabel(pain_header, text="2. Pelvic Pain / Cramps", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        self.pain_val_lbl = ctk.CTkLabel(pain_header, text="0 - None", font=ctk.CTkFont(size=14, weight="bold"), text_color="#E63946")
        self.pain_val_lbl.pack(side="right")

        self.pain_slider = ctk.CTkSlider(
            form_inner,
            from_=0,
            to=5,
            number_of_steps=5,
            progress_color="#E63946",
            command=self._on_pain_change,
        )
        self.pain_slider.set(0)
        self.pain_slider.pack(fill="x", pady=(0, 15))

        # 3. Biomarkers Row: BBT & Cervical Mucus & Sexual Activity
        bio_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        bio_row.pack(fill="x", pady=(5, 15))

        # BBT
        bbt_col = ctk.CTkFrame(bio_row, fg_color="transparent")
        bbt_col.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(bbt_col, text="3. Morning BBT (°C)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.bbt_entry = ctk.CTkEntry(bbt_col, placeholder_text="e.g. 36.45", height=35)
        self.bbt_entry.pack(fill="x", pady=(4, 0))

        # Mucus
        mucus_col = ctk.CTkFrame(bio_row, fg_color="transparent")
        mucus_col.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(mucus_col, text="4. Cervical Mucus", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.mucus_var = ctk.StringVar(value="None")
        self.mucus_menu = ctk.CTkOptionMenu(
            mucus_col,
            variable=self.mucus_var,
            values=["None", "Dry", "Sticky", "Creamy", "Watery", "Egg White"],
            fg_color="#D94073",
            button_color="#B83262",
            height=35,
        )
        self.mucus_menu.pack(fill="x", pady=(4, 0))

        # Sexual Activity
        sex_col = ctk.CTkFrame(bio_row, fg_color="transparent")
        sex_col.pack(side="left", fill="both", expand=True, padx=(8, 0))
        ctk.CTkLabel(sex_col, text="5. Intimacy / Activity", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.sex_var = ctk.StringVar(value="None")
        self.sex_menu = ctk.CTkOptionMenu(
            sex_col,
            variable=self.sex_var,
            values=["None", "Protected", "Unprotected", "High Libido"],
            fg_color=("#6C757D", "#343A40"),
            height=35,
        )
        self.sex_menu.pack(fill="x", pady=(4, 0))

        # 4. Lifestyle Row: Energy & Sleep
        life_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        life_row.pack(fill="x", pady=(0, 15))

        energy_col = ctk.CTkFrame(life_row, fg_color="transparent")
        energy_col.pack(side="left", fill="both", expand=True, padx=(0, 8))
        energy_hdr = ctk.CTkFrame(energy_col, fg_color="transparent")
        energy_hdr.pack(fill="x")
        ctk.CTkLabel(energy_hdr, text="6. Energy Level (1-5)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.energy_val_lbl = ctk.CTkLabel(energy_hdr, text="3 - Balanced", font=ctk.CTkFont(size=13), text_color="gray")
        self.energy_val_lbl.pack(side="right")
        self.energy_slider = ctk.CTkSlider(
            energy_col, from_=1, to=5, number_of_steps=4, command=self._on_energy_change
        )
        self.energy_slider.set(3)
        self.energy_slider.pack(fill="x", pady=(4, 0))

        sleep_col = ctk.CTkFrame(life_row, fg_color="transparent")
        sleep_col.pack(side="right", fill="both", expand=True, padx=(8, 0))
        ctk.CTkLabel(sleep_col, text="7. Sleep Duration (Hours)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.sleep_entry = ctk.CTkEntry(sleep_col, placeholder_text="e.g. 7.5", height=35)
        self.sleep_entry.pack(fill="x", pady=(4, 0))

        # 5. Physical Symptoms Checkbox Grid
        ctk.CTkLabel(form_inner, text="8. Physical Symptoms", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(5, 6))
        sym_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        sym_frame.pack(fill="x", pady=(0, 15))

        # 3 columns for symptoms
        for idx, sym in enumerate(COMMON_SYMPTOMS):
            var = ctk.BooleanVar(value=False)
            self.symptom_vars[sym] = var
            cb = ctk.CTkCheckBox(
                sym_frame,
                text=sym,
                variable=var,
                checkbox_width=20,
                checkbox_height=20,
                fg_color="#D94073",
                hover_color="#B83262",
                font=ctk.CTkFont(size=13),
            )
            col = idx % 3
            row = idx // 3
            cb.grid(row=row, column=col, sticky="w", padx=6, pady=4)

        # 6. Mood & Emotions Checkbox Grid
        ctk.CTkLabel(form_inner, text="9. Mood & Emotional State", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(5, 6))
        mood_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        mood_frame.pack(fill="x", pady=(0, 15))

        for idx, mood in enumerate(COMMON_MOODS):
            var = ctk.BooleanVar(value=False)
            self.mood_vars[mood] = var
            cb = ctk.CTkCheckBox(
                mood_frame,
                text=mood,
                variable=var,
                checkbox_width=20,
                checkbox_height=20,
                fg_color="#5E60CE",
                hover_color="#3E4092",
                font=ctk.CTkFont(size=13),
            )
            col = idx % 3
            row = idx // 3
            cb.grid(row=row, column=col, sticky="w", padx=6, pady=4)

        # 7. Personal Journal Notes
        ctk.CTkLabel(form_inner, text="10. Personal Journal & Observations", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(5, 5))
        self.notes_box = ctk.CTkTextbox(form_inner, height=80, corner_radius=8)
        self.notes_box.pack(fill="x", pady=(0, 15))

        # Action Buttons
        act_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        act_row.pack(fill="x", pady=(10, 5))

        self.save_btn = ctk.CTkButton(
            act_row,
            text="💾 Save Daily Log",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#D94073",
            hover_color="#B83262",
            height=44,
            corner_radius=10,
            command=self._save_log,
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.del_btn = ctk.CTkButton(
            act_row,
            text="🗑️ Delete Entry",
            font=ctk.CTkFont(size=14),
            fg_color="#E63946",
            hover_color="#C1121F",
            height=44,
            corner_radius=10,
            command=self._delete_log,
        )
        self.del_btn.pack(side="right", padx=(8, 0))

    def _on_pain_change(self, value) -> None:
        p_val = int(round(float(value)))
        labels = {
            0: "0 - None",
            1: "1 - Mild",
            2: "2 - Moderate",
            3: "3 - Significant",
            4: "4 - Severe",
            5: "5 - Intense",
        }
        self.pain_val_lbl.configure(text=labels.get(p_val, f"{p_val}"))

    def _on_energy_change(self, value) -> None:
        e_val = int(round(float(value)))
        labels = {
            1: "1 - Exhausted",
            2: "2 - Low",
            3: "3 - Balanced",
            4: "4 - High",
            5: "5 - Peak Energy",
        }
        self.energy_val_lbl.configure(text=labels.get(e_val, f"{e_val}"))

    def _prev_day(self) -> None:
        self.load_date(self.current_date - timedelta(days=1))

    def _next_day(self) -> None:
        self.load_date(self.current_date + timedelta(days=1))

    def _today(self) -> None:
        self.load_date(date.today())

    def load_date(self, target_date: date) -> None:
        self.current_date = target_date
        self.date_display.configure(text=target_date.strftime("%A, %B %d, %Y"))
        self.alert_lbl.configure(text="")

        log = self.db.get_daily_log(target_date)
        if log:
            # Flow
            flow_name = log.flow.value.replace("_", " ").title()
            if flow_name == "None":
                self.flow_var.set("None")
            elif flow_name in ["Spotting", "Light", "Medium", "Heavy", "Super Heavy"]:
                self.flow_var.set(flow_name)
            else:
                self.flow_var.set("None")

            # Pain
            self.pain_slider.set(log.cramps_pain)
            self._on_pain_change(log.cramps_pain)

            # BBT
            self.bbt_entry.delete(0, "end")
            if log.bbt:
                self.bbt_entry.insert(0, f"{log.bbt:.2f}")

            # Mucus
            muc_str = log.mucus.value.replace("_", " ").title()
            self.mucus_var.set(muc_str if muc_str in ["None", "Dry", "Sticky", "Creamy", "Watery", "Egg White"] else "None")

            # Sex
            sex_str = log.sexual_activity.value.replace("_", " ").title()
            self.sex_var.set(sex_str if sex_str in ["None", "Protected", "Unprotected", "High Libido"] else "None")

            # Energy & Sleep
            self.energy_slider.set(log.energy_level if log.energy_level else 3)
            self._on_energy_change(log.energy_level if log.energy_level else 3)

            self.sleep_entry.delete(0, "end")
            if log.sleep_hours:
                self.sleep_entry.insert(0, str(log.sleep_hours))

            # Symptoms
            for sym, var in self.symptom_vars.items():
                var.set(sym in log.symptoms)

            # Moods
            for mood, var in self.mood_vars.items():
                var.set(mood in log.moods)

            # Notes
            self.notes_box.delete("1.0", "end")
            self.notes_box.insert("1.0", log.notes)
        else:
            # Reset defaults
            self.flow_var.set("None")
            self.pain_slider.set(0)
            self._on_pain_change(0)
            self.bbt_entry.delete(0, "end")
            self.mucus_var.set("None")
            self.sex_var.set("None")
            self.energy_slider.set(3)
            self._on_energy_change(3)
            self.sleep_entry.delete(0, "end")
            for var in self.symptom_vars.values():
                var.set(False)
            for var in self.mood_vars.values():
                var.set(False)
            self.notes_box.delete("1.0", "end")

    def _save_log(self) -> None:
        flow_raw = self.flow_var.get().strip().lower().replace(" ", "_")
        flow = FlowLevel.from_str(flow_raw)
        cramps = int(round(self.pain_slider.get()))

        bbt_val = None
        bbt_text = self.bbt_entry.get().strip()
        if bbt_text:
            try:
                bbt_val = float(bbt_text)
            except ValueError:
                pass

        mucus = MucusType.from_str(self.mucus_var.get())
        sex = SexualActivity.from_str(self.sex_var.get())
        energy = int(round(self.energy_slider.get()))

        sleep_val = None
        sleep_text = self.sleep_entry.get().strip()
        if sleep_text:
            try:
                sleep_val = float(sleep_text)
            except ValueError:
                pass

        selected_symptoms = [sym for sym, var in self.symptom_vars.items() if var.get()]
        selected_moods = [m for m, var in self.mood_vars.items() if var.get()]
        notes = self.notes_box.get("1.0", "end").strip()

        log = DailyLog(
            date=self.current_date,
            flow=flow,
            cramps_pain=cramps,
            energy_level=energy,
            bbt=bbt_val,
            mucus=mucus,
            sexual_activity=sex,
            sleep_hours=sleep_val,
            symptoms=selected_symptoms,
            moods=selected_moods,
            notes=notes,
        )

        self.db.save_daily_log(log)
        self.alert_lbl.configure(
            text=f"✓ Successfully saved log for {self.current_date.strftime('%B %d, %Y')}!",
            text_color="#52B788",
        )
        self.on_saved()

    def _delete_log(self) -> None:
        self.db.delete_daily_log(self.current_date)
        self.load_date(self.current_date)
        self.alert_lbl.configure(
            text=f"Deleted log for {self.current_date.strftime('%B %d, %Y')}.",
            text_color="#E63946",
        )
        self.on_saved()
