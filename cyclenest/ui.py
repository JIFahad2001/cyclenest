"""Rich Interactive Desktop Console UI for CycleNest.
"""

from __future__ import annotations
import calendar
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich import box

from cyclenest.models import (
    DailyLog,
    Cycle,
    CyclePhase,
    FlowLevel,
    MucusType,
    SexualActivity,
    COMMON_SYMPTOMS,
    COMMON_MOODS,
    PredictionResult,
)
from cyclenest.analyzer import CycleAnalyzer
from cyclenest.predictor import EnsembleCyclePredictor
from cyclenest.charts import (
    render_cycle_length_barchart,
    render_bbt_curve,
    render_symptom_frequency_chart,
    render_mood_distribution_chart,
    render_cramps_by_cycle_day,
)


class ConsoleUI:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console(legacy_windows=False)

    def print_banner(self) -> None:
        banner_text = Text()
        banner_text.append("🌸 CycleNest", style="bold magenta")
        banner_text.append("  ─  Desktop Menstrual Cycle Tracker & Intelligence Suite\n", style="bold white")
        banner_text.append("Precision Biomarker Logging • Pattern Analysis • Multi-Model Forecasts", style="dim cyan")
        self.console.print(Panel(banner_text, border_style="magenta", box=box.ROUNDED))

    def print_today_dashboard(
        self,
        analyzer: CycleAnalyzer,
        prediction: PredictionResult,
        today_log: Optional[DailyLog],
        target_date: Optional[date] = None,
    ) -> None:
        today = target_date or date.today()
        phase, c_day, phase_desc = analyzer.get_phase_for_date(
            today, expected_next_period=prediction.next_period_start
        )

        # Days until next period
        days_to_period = (prediction.next_period_start - today).days
        if phase == CyclePhase.MENSTRUAL:
            period_status = "[bold bright_red]Active Menstrual Bleeding[/bold bright_red]"
        elif days_to_period > 0:
            period_status = f"[bold green]{days_to_period} days away[/bold green] (Expected: {prediction.next_period_start.strftime('%b %d, %Y')})"
        elif days_to_period == 0:
            period_status = "[bold yellow]Expected TODAY[/bold yellow]"
        else:
            period_status = f"[bold red]Overdue by {abs(days_to_period)} days[/bold red]"

        # Conception probability estimation
        if phase in (CyclePhase.OVULATION, CyclePhase.FERTILE_WINDOW):
            fertility_status = "[bold bright_magenta]🔥 PEAK / HIGH (Fertile Window Active)[/bold bright_magenta]"
        elif phase == CyclePhase.MENSTRUAL:
            fertility_status = "[cyan]Low (Menstrual bleeding)[/cyan]"
        elif phase == CyclePhase.LUTEAL:
            fertility_status = "[cyan]Low (Post-ovulatory luteal phase)[/cyan]"
        else:
            fertility_status = "[dim]Low to Moderate[/dim]"

        # Overview Table
        table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
        table.add_column("Key", style="bold white", width=22)
        table.add_column("Value", width=55)

        table.add_row("📅 Current Date:", f"[bold cyan]{today.strftime('%A, %B %d, %Y')}[/bold cyan]")
        table.add_row("🔄 Cycle Status:", f"[bold yellow]Day {c_day}[/bold yellow] of ~{round(prediction.predicted_cycle_length)} day cycle")
        table.add_row("🌙 Active Phase:", f"[{phase.color()}]{phase.display_title()}[/{phase.color()}]  [dim]({phase_desc})[/dim]")
        table.add_row("🩸 Next Period:", period_status)
        table.add_row("✨ Conception Chance:", fertility_status)
        table.add_row("🥚 Projected Ovulation:", f"{prediction.ovulation_date.strftime('%b %d, %Y')} [dim](Fertile: {prediction.fertile_window_start.strftime('%b %d')} - {prediction.fertile_window_end.strftime('%b %d')})[/dim]")
        table.add_row("⚡ PMS Alert Window:", f"{prediction.pms_window_start.strftime('%b %d')} - {prediction.pms_window_end.strftime('%b %d')}")

        if today_log:
            log_summary = f"{today_log.flow.display_badge()}"
            if today_log.cramps_pain > 0:
                log_summary += f" | Pain: {today_log.cramps_pain}/5"
            if today_log.bbt:
                log_summary += f" | BBT: {today_log.bbt:.2f}°C"
            if today_log.symptoms:
                log_summary += f" | Symptoms: {', '.join(today_log.symptoms[:3])}"
            if today_log.moods:
                log_summary += f" | Mood: {', '.join(today_log.moods[:2])}"
            table.add_row("📝 Today's Entry:", f"[green]{log_summary}[/green]")
        else:
            table.add_row("📝 Today's Entry:", "[dim yellow]No log recorded yet for today (Option 2 to log)[/dim yellow]")

        self.console.print(
            Panel(
                table,
                title="✨ Daily Overview & Biological Status",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )

    def render_monthly_calendar(
        self,
        year: int,
        month: int,
        analyzer: CycleAnalyzer,
        prediction: PredictionResult,
    ) -> None:
        cal = calendar.Calendar(firstweekday=6)  # Sunday first
        month_days = cal.monthdatescalendar(year, month)
        month_name = calendar.month_name[month]

        table = Table(
            title=f"🗓️ Cycle Calendar: {month_name} {year}",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        days_header = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for d in days_header:
            table.add_column(d, justify="center", width=12)

        today = date.today()

        for week in month_days:
            row_cells: List[str] = []
            for d in week:
                if d.month != month:
                    row_cells.append(f"[dim]{d.day}[/dim]")
                    continue

                log = analyzer.log_map.get(d)
                phase, c_day, _ = analyzer.get_phase_for_date(d, prediction.next_period_start)

                badges = []
                day_num_str = f"{d.day}"
                if d == today:
                    day_num_str = f"[bold underline white on blue] {d.day} [/bold underline white on blue]"

                # Bleeding
                if log and log.flow.is_bleeding():
                    badges.append(f"[bold red]🩸{log.flow.value[:3].upper()}[/bold red]")
                elif d == prediction.next_period_start:
                    badges.append("[bold green]🔮PERIOD[/bold green]")
                elif prediction.confidence_interval_80[0] <= d <= prediction.confidence_interval_80[1]:
                    badges.append("[dim green]🔮exp[/dim green]")
                elif d == prediction.ovulation_date:
                    badges.append("[bold magenta]🥚OVUL[/bold magenta]")
                elif prediction.fertile_window_start <= d <= prediction.fertile_window_end:
                    badges.append("[yellow]✨FERT[/yellow]")
                elif prediction.pms_window_start <= d <= prediction.pms_window_end:
                    badges.append("[magenta]⚡PMS[/magenta]")

                # Symptoms or note indicator
                if log:
                    if log.symptoms:
                        badges.append("[cyan]•sym[/cyan]")
                    if log.bbt:
                        badges.append(f"[dim]{log.bbt:.1f}°[/dim]")

                cell_content = f"{day_num_str}\n" + ("\n".join(badges) if badges else "[dim]·[/dim]")
                row_cells.append(cell_content)

            table.add_row(*row_cells)

        self.console.print(table)

        legend_text = (
            "[bold]Legend:[/bold] "
            "[bold red]🩸 Period[/bold red]   "
            "[bold magenta]🥚 Ovulation[/bold magenta]   "
            "[yellow]✨ Fertile Window[/yellow]   "
            "[magenta]⚡ PMS Anticipation[/magenta]   "
            "[bold green]🔮 Predicted Period[/bold green]   "
            "[underline white on blue] Today [/underline white on blue]"
        )
        self.console.print(Panel(Text.from_markup(legend_text), box=box.SIMPLE))

    def render_prediction_comparison(
        self,
        analyzer: CycleAnalyzer,
        ensemble: EnsembleCyclePredictor,
    ) -> None:
        completed = analyzer.get_completed_cycles()
        current = analyzer.get_current_cycle()
        logs = analyzer.logs

        all_preds = ensemble.get_all_model_predictions(
            completed,
            current,
            logs,
            analyzer.default_cycle_length,
            analyzer.default_luteal_length,
        )
        consensus = ensemble.predict(
            completed,
            current,
            logs,
            analyzer.default_cycle_length,
            analyzer.default_luteal_length,
        )

        table = Table(
            title="🔮 Multi-Model Menstrual & Fertility Forecast Comparison",
            box=box.ROUNDED,
            header_style="bold cyan",
        )
        table.add_column("Model Architecture", style="bold white", width=26)
        table.add_column("Pred. Cycle", justify="right", width=12)
        table.add_column("Next Period", justify="center", width=14)
        table.add_column("80% Credible Range", justify="center", width=22)
        table.add_column("Ovulation Date", justify="center", width=15)
        table.add_column("Confidence", justify="right", width=12)

        for p in all_preds:
            c_score = f"{int(p.confidence_score * 100)}%"
            ci_str = f"{p.confidence_interval_80[0].strftime('%b %d')} - {p.confidence_interval_80[1].strftime('%b %d')}"
            table.add_row(
                p.model_name,
                f"{p.predicted_cycle_length:.1f} d",
                p.next_period_start.strftime("%b %d, %Y"),
                ci_str,
                p.ovulation_date.strftime("%b %d"),
                c_score,
            )

        # Consensus row
        c_ci = f"{consensus.confidence_interval_80[0].strftime('%b %d')} - {consensus.confidence_interval_80[1].strftime('%b %d')}"
        table.add_section()
        table.add_row(
            f"[bold green]⭐ {consensus.model_name}[/bold green]",
            f"[bold green]{consensus.predicted_cycle_length:.1f} d[/bold green]",
            f"[bold green]{consensus.next_period_start.strftime('%b %d, %Y')}[/bold green]",
            f"[bold green]{c_ci}[/bold green]",
            f"[bold green]{consensus.ovulation_date.strftime('%b %d')}[/bold green]",
            f"[bold green]{int(consensus.confidence_score * 100)}%[/bold green]",
        )

        self.console.print(table)
        self.console.print(
            Panel(
                f"[bold cyan]Consensus Synthesis:[/bold cyan] {consensus.explanation}",
                box=box.ROUNDED,
                border_style="green",
            )
        )

    def render_multi_cycle_forecast(
        self,
        analyzer: CycleAnalyzer,
        ensemble: EnsembleCyclePredictor,
        count: int = 4,
    ) -> None:
        completed = analyzer.get_completed_cycles()
        current = analyzer.get_current_cycle()
        logs = analyzer.logs

        forecasts = ensemble.forecast_upcoming_cycles(
            count=count,
            completed_cycles=completed,
            current_cycle=current,
            recent_logs=logs,
            default_cycle_length=analyzer.default_cycle_length,
            default_luteal_length=analyzer.default_luteal_length,
        )

        table = Table(
            title=f"🔭 Forward Horizon Forecast (Next {count} Cycles)",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        table.add_column("Cycle Projection", style="bold yellow", width=18)
        table.add_column("Est. Start Date", justify="center", style="bold red", width=16)
        table.add_column("Est. Cycle Length", justify="right", width=16)
        table.add_column("Fertile Window", justify="center", style="yellow", width=22)
        table.add_column("Ovulation Day", justify="center", style="magenta", width=16)
        table.add_column("PMS Onset Alert", justify="center", style="dim", width=16)
        table.add_column("Confidence", justify="right", width=12)

        for f in forecasts:
            fertile = f"{f.fertile_window_start.strftime('%b %d')} - {f.fertile_window_end.strftime('%b %d')}"
            table.add_row(
                f.model_name,
                f.next_period_start.strftime("%b %d, %Y"),
                f"{round(f.predicted_cycle_length)} days",
                fertile,
                f.ovulation_date.strftime("%b %d, %Y"),
                f.pms_window_start.strftime("%b %d"),
                f"{int(f.confidence_score * 100)}%",
            )

        self.console.print(table)

    def render_pattern_analytics(self, analyzer: CycleAnalyzer) -> None:
        stats = analyzer.compute_statistics()
        symptom_data = analyzer.analyze_symptom_patterns()

        # Clinical Statistics Table
        table = Table(title="📊 Gynecological Pattern & Regularity Analysis", box=box.ROUNDED)
        table.add_column("Metric", style="bold white", width=28)
        table.add_column("Value / Clinical Classification", style="bold cyan", width=48)

        table.add_row("Total Recorded Cycles:", f"{stats['cycle_count']} cycles ({stats['completed_cycles']} completed)")
        table.add_row("Average Cycle Length:", f"{stats['mean_cycle_length']} days (Median: {stats['median_cycle_length']}d)")
        table.add_row("Cycle Length Variability (Std Dev):", f"±{stats['std_cycle_length']} days (IQR: {stats['iqr_cycle_length']}d)")
        table.add_row("Historical Cycle Span (Min - Max):", f"{stats['min_cycle_length']} days - {stats['max_cycle_length']} days (Range: {stats['variation_days']}d)")
        table.add_row("Average Period Flow Duration:", f"{stats['mean_period_length']} days (Median: {stats['median_period_length']}d)")

        reg_color = "green" if stats["regularity_code"] in ("high", "normal") else "yellow" if stats["regularity_code"] == "mild" else "red"
        table.add_row("FIGO Regularity Rating:", f"[{reg_color}]{stats['regularity_status']}[/{reg_color}]")

        self.console.print(table)

        # Symptom-Phase correlations
        pms_syms = symptom_data["pms_symptoms"]
        if pms_syms:
            pms_list = ", ".join([f"[bold]{s}[/bold] ({c}x)" for s, c in pms_syms])
            self.console.print(
                Panel(
                    f"Top symptoms clustering during the pre-menstrual luteal window:\n{pms_list}",
                    title="⚡ Identified PMS Symptom Cluster",
                    border_style="magenta",
                    box=box.ROUNDED,
                )
            )

        # BBT phase differences
        bbt_phases = symptom_data.get("avg_bbt_by_phase", {})
        if bbt_phases:
            bbt_summary = "  |  ".join([f"{k.replace('_', ' ').title()}: [bold]{v}°C[/bold]" for k, v in bbt_phases.items()])
            self.console.print(
                Panel(
                    f"Thermal distribution across phases:\n{bbt_summary}",
                    title="🌡️ Average Basal Body Temperature by Phase",
                    border_style="yellow",
                    box=box.ROUNDED,
                )
            )

    def prompt_quick_log(self, target_date: date) -> DailyLog:
        self.console.print(f"\n[bold magenta]⚡ Quick Daily Check-In for {target_date.strftime('%B %d, %Y')}[/bold magenta]")
        self.console.print("[dim]Flow: 0=None, 1=Spotting, 2=Light, 3=Medium, 4=Heavy, 5=Super Heavy[/dim]")
        flow_choice = IntPrompt.ask("Bleeding Flow Level (0-5)", choices=["0", "1", "2", "3", "4", "5"], default=0)
        flow_map = {
            0: FlowLevel.NONE,
            1: FlowLevel.SPOTTING,
            2: FlowLevel.LIGHT,
            3: FlowLevel.MEDIUM,
            4: FlowLevel.HEAVY,
            5: FlowLevel.SUPER_HEAVY,
        }
        flow = flow_map[flow_choice]

        cramps = 0
        if flow != FlowLevel.NONE or Confirm.ask("Any cramps / pelvic pain today?", default=False):
            cramps = IntPrompt.ask("Cramp Pain Level (0=None to 5=Severe)", choices=["0", "1", "2", "3", "4", "5"], default=1)

        bbt_in = Prompt.ask("Basal Body Temperature in °C (optional, press Enter to skip)", default="")
        bbt = float(bbt_in) if bbt_in.replace(".", "", 1).isdigit() else None

        notes = Prompt.ask("Quick note (optional, press Enter to skip)", default="")

        return DailyLog(
            date=target_date,
            flow=flow,
            cramps_pain=cramps,
            bbt=bbt,
            notes=notes,
        )

    def prompt_detailed_log(self, existing_log: Optional[DailyLog], target_date: date) -> DailyLog:
        self.console.print(f"\n[bold cyan]📝 Comprehensive Daily Health Log: {target_date.strftime('%A, %B %d, %Y')}[/bold cyan]")

        # 1. Flow
        self.console.print("\n[bold]1. Menstrual Flow:[/bold]")
        self.console.print("  0) None  1) Spotting  2) Light  3) Medium  4) Heavy  5) Super Heavy")
        def_flow = 0
        if existing_log and existing_log.flow != FlowLevel.NONE:
            def_flow = {
                FlowLevel.NONE: 0,
                FlowLevel.SPOTTING: 1,
                FlowLevel.LIGHT: 2,
                FlowLevel.MEDIUM: 3,
                FlowLevel.HEAVY: 4,
                FlowLevel.SUPER_HEAVY: 5,
            }.get(existing_log.flow, 0)
        flow_num = IntPrompt.ask("Select flow level", choices=["0", "1", "2", "3", "4", "5"], default=def_flow)
        flow = {
            0: FlowLevel.NONE,
            1: FlowLevel.SPOTTING,
            2: FlowLevel.LIGHT,
            3: FlowLevel.MEDIUM,
            4: FlowLevel.HEAVY,
            5: FlowLevel.SUPER_HEAVY,
        }[flow_num]

        # 2. Pain / Cramps
        cramps = IntPrompt.ask(
            "\n[bold]2. Cramps / Pelvic Pain (0 = None, 5 = Intense)[/bold]",
            choices=["0", "1", "2", "3", "4", "5"],
            default=existing_log.cramps_pain if existing_log else 0,
        )

        # 3. BBT
        def_bbt = f"{existing_log.bbt:.2f}" if (existing_log and existing_log.bbt) else ""
        bbt_str = Prompt.ask("\n[bold]3. Morning Basal Body Temp in °C (e.g. 36.42, press Enter to skip)[/bold]", default=def_bbt)
        bbt = float(bbt_str) if bbt_str.replace(".", "", 1).isdigit() else None

        # 4. Cervical Mucus
        self.console.print("\n[bold]4. Cervical Mucus / Fluid:[/bold]")
        self.console.print("  0) None  1) Dry  2) Sticky  3) Creamy  4) Watery (Fertile)  5) Egg White (Peak Fertile)")
        mucus_num = IntPrompt.ask("Select mucus type", choices=["0", "1", "2", "3", "4", "5"], default=0)
        mucus = {
            0: MucusType.NONE,
            1: MucusType.DRY,
            2: MucusType.STICKY,
            3: MucusType.CREAMY,
            4: MucusType.WATERY,
            5: MucusType.EGG_WHITE,
        }[mucus_num]

        # 5. Sexual Activity
        self.console.print("\n[bold]5. Sexual Activity / Intimacy:[/bold]")
        self.console.print("  0) None  1) Protected  2) Unprotected  3) High Libido")
        sex_num = IntPrompt.ask("Select activity", choices=["0", "1", "2", "3"], default=0)
        sex = {
            0: SexualActivity.NONE,
            1: SexualActivity.PROTECTED,
            2: SexualActivity.UNPROTECTED,
            3: SexualActivity.HIGH_LIBIDO,
        }[sex_num]

        # 6. Energy & Sleep
        energy = IntPrompt.ask("\n[bold]6. Energy Level (1 = Exhausted, 5 = Peak Energy)[/bold]", choices=["1", "2", "3", "4", "5"], default=3)
        sleep_str = Prompt.ask("\n[bold]7. Hours of Sleep (e.g. 7.5, press Enter to skip)[/bold]", default="")
        sleep = float(sleep_str) if sleep_str.replace(".", "", 1).isdigit() else None

        # 8. Physical Symptoms Selector
        self.console.print("\n[bold]8. Physical Symptoms (select by numbers separated by commas, or press Enter for none):[/bold]")
        for i, s in enumerate(COMMON_SYMPTOMS, 1):
            self.console.print(f"  {i:2d}) {s}")
        sym_input = Prompt.ask("Enter symptom numbers", default="")
        selected_symptoms: List[str] = []
        if sym_input.strip():
            for num_str in sym_input.split(","):
                num_str = num_str.strip()
                if num_str.isdigit() and 1 <= int(num_str) <= len(COMMON_SYMPTOMS):
                    selected_symptoms.append(COMMON_SYMPTOMS[int(num_str) - 1])

        # 9. Mood Selector
        self.console.print("\n[bold]9. Mood & Emotions (select by numbers separated by commas, or press Enter for none):[/bold]")
        for i, m in enumerate(COMMON_MOODS, 1):
            self.console.print(f"  {i:2d}) {m}")
        mood_input = Prompt.ask("Enter mood numbers", default="")
        selected_moods: List[str] = []
        if mood_input.strip():
            for num_str in mood_input.split(","):
                num_str = num_str.strip()
                if num_str.isdigit() and 1 <= int(num_str) <= len(COMMON_MOODS):
                    selected_moods.append(COMMON_MOODS[int(num_str) - 1])

        # 10. Notes
        notes = Prompt.ask("\n[bold]10. Personal Journal / Symptoms Notes[/bold]", default=existing_log.notes if existing_log else "")

        return DailyLog(
            date=target_date,
            flow=flow,
            cramps_pain=cramps,
            energy_level=energy,
            bbt=bbt,
            mucus=mucus,
            sexual_activity=sex,
            sleep_hours=sleep,
            symptoms=selected_symptoms,
            moods=selected_moods,
            notes=notes,
        )

    def render_logs_table(self, logs: List[DailyLog], limit: int = 15) -> None:
        table = Table(title=f"📜 Recent Health Logs (Latest {min(limit, len(logs))})", box=box.ROUNDED)
        table.add_column("Date", style="bold cyan", width=12)
        table.add_column("Flow", width=14)
        table.add_column("Pain", justify="center", width=8)
        table.add_column("BBT", justify="right", width=9)
        table.add_column("Mucus", width=14)
        table.add_column("Symptoms", width=25)
        table.add_column("Mood", width=20)
        table.add_column("Notes", width=24)

        if not logs:
            table.add_row("-", "-", "-", "-", "-", "[dim]No logs recorded[/dim]", "-", "-")
            self.console.print(table)
            return

        display_logs = sorted(logs, key=lambda l: l.date, reverse=True)[:limit]
        for l in display_logs:
            sym_str = ", ".join(l.symptoms[:2]) + ("..." if len(l.symptoms) > 2 else "")
            mood_str = ", ".join(l.moods[:2]) + ("..." if len(l.moods) > 2 else "")
            bbt_str = f"{l.bbt:.2f}°" if l.bbt else "-"
            table.add_row(
                l.date.isoformat(),
                l.flow.display_badge(),
                f"{l.cramps_pain}/5" if l.cramps_pain > 0 else "-",
                bbt_str,
                l.mucus.display_badge() if l.mucus != MucusType.NONE else "-",
                sym_str or "-",
                mood_str or "-",
                (l.notes[:22] + "...") if len(l.notes) > 22 else l.notes or "-",
            )

        self.console.print(table)
