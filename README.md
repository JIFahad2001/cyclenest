# 🌸 CycleNest — Menstrual Tracking & Predictive Intelligence

**A Desktop Menstrual Cycle Tracker, Pattern Intelligence Engine & Multi-Model Predictive Forecasting Suite.**

Available both as a **Modern Desktop GUI Application** (CustomTkinter + Matplotlib) and a **Terminal Console Application** (Rich + ANSI/Unicode).

---

## 🌟 Modern Desktop GUI Overview

CycleNest features a modern desktop graphical user interface with smooth dark/light mode, soft rose/teal medical accents, and embedded interactive charts:

1. 🏠 **Dashboard:**
   - Prominent **Cycle Day Badge** (e.g. Day 17 of 28).
   - Dynamic **Phase Pill** (`Menstrual`, `Follicular`, `Fertile Window`, `Ovulation`, `Luteal`, `Late Luteal PMS`).
   - Countdown status badge to next period and conception probability indicator (`Peak`, `High`, `Low`).
   - Upcoming milestones (ovulation, fertile window, PMS alerts).
2. ✍️ **Daily Health Logger:**
   - Date navigator (Today, Yesterday, Custom date).
   - Segmented buttons for flow intensity (`None`, `Spotting`, `Light`, `Medium`, `Heavy`, `Super Heavy`).
   - Pelvic pain / cramps slider (0 to 5) with live clinical severity rating.
   - Morning Basal Body Temperature (BBT) in °C/°F.
   - Cervical Mucus dropdown (`Dry`, `Sticky`, `Creamy`, `Watery`, `Egg White`).
   - Intimacy / sexual activity tracking, energy level (1–5), sleep hours.
   - 14 symptom checkboxes & 12 mood checkboxes.
   - Personal journal notes & quick save/delete.
3. 🗓️ **Interactive Calendar:**
   - Month-by-month grid with color-coded day badges:
     - 🩸 Red for Period days
     - 🥚 Magenta for Ovulation day
     - ✨ Amber for Fertile window
     - ⚡ Orange for PMS window
     - 🔮 Soft green for Predicted period range
   - **Click on any calendar day** to immediately inspect or edit that date's log!
4. 🔮 **Multi-Model Predictions:**
   - Side-by-side comparison cards for **4 distinct prediction architectures**:
     1. *Weighted Moving Average (EWMA)*: Recency-weighted decay ($w_i = \alpha (1-\alpha)^i$).
     2. *Bayesian Normal Distribution*: Prior update ($\mu_0 = 28.5, \sigma_0 = 3.5$) with **80% and 95% Credible Intervals**.
     3. *Sympto-Thermal Biomarker Model (FAM)*: Real-time active cycle BBT shifts & peak mucus detection ($\ge 94\%$ certainty).
     4. *Trend-Adjusted Holt's Smoothing*: Double exponential smoothing capturing progressive drift.
   - Featured **⭐ Smart Ensemble Consensus** card with confidence score and scientific rationale.
   - **Forward Horizon Projections**: Projects the next 4–6 upcoming cycles.
5. 📊 **Pattern & Regularity Analytics:**
   - **FIGO Regularity Rating**: Clinical cycle classification (*Highly Regular*, *Normal Variation*, *Mildly Variable*, *Irregular*, *Polymenorrhea*, *Oligomenorrhea*).
   - Statistical spread ($\mu$, median, $\sigma$, IQR, min/max).
   - **PMS Symptom Cluster Analysis**: Automatically identifies symptoms that peak during the pre-menstrual luteal phase.
   - BBT thermal distribution across phases ($\Delta T$ progesterone rise).
6. 📈 **Interactive Embedded Charts:**
   - Cycle Length Historical Progression vs. 24–38 day clinical normal zone.
   - BBT Biphasic Thermal Shift Curve with coverline.
   - Top Symptoms occurrence frequency bar chart.
   - Menstrual cramp / pelvic pain intensity profile by cycle day.
7. 📜 **Historical Records:**
   - Scrollable feed of all past logs with filter toggles (*All*, *Bleeding Only*, *With Symptoms*).
   - Quick 1-click **Edit** and **Delete** buttons.
8. ⚙️ **Settings & Data Management:**
   - Theme toggle (**Dark Mode** / **Light Mode** / **System**).
   - Personal biological baselines customization (default cycle length, period duration, luteal length).
   - ⚡ **1-Click Clinical Benchmark Loader**: Preloads 6 months of realistic clinical cycles.
   - **Export to CSV / JSON** & **Import from CSV / JSON**.
   - 100% Offline & Private local SQLite database storage.

---

## 🚀 Quick Launch Guide

### Requirements
- Python 3.10+
- Install dependencies:
  ```powershell
  pip install -r requirements.txt
  ```

### Launch the Modern GUI Application
Run either:
```powershell
python gui.py
```
Or double-click [run_gui.bat](file:///C:/Users/Biswas%20Tech/.gemini/antigravity/scratch/cyclenest/run_gui.bat) (or run `./run_gui.ps1`).

You can also launch the GUI via the main script:
```powershell
python main.py --gui
```

### Launch the Terminal Console Application
If you prefer running inside your terminal:
```powershell
python main.py
```
*(Or double-click [run.bat](file:///C:/Users/Biswas%20Tech/.gemini/antigravity/scratch/cyclenest/run.bat))*

### CLI Direct Commands
```powershell
# Today's status & biological phase
python main.py --today

# Prediction comparison and multi-cycle forecast
python main.py --predict

# Gynecological pattern analytics & PMS clusters
python main.py --stats

# Monthly calendar
python main.py --calendar
```

---

## 🔒 Privacy & Architecture
- **Zero Cloud Tracking:** All logs and personal notes remain 100% on your local machine in an ACID-compliant SQLite database at `~/.cyclenest/cyclenest.db`.
- **Easy Sharing:** Sharing or uploading this repository to GitHub does not expose your personal data (protected by `.gitignore`).