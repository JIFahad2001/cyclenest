"""Interactive Desktop Console Application Controller and CLI entry point for CycleNest.
"""

from __future__ import annotations
import sys
import argparse
from datetime import date, datetime, timedelta
from typing import Optional, List
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        if sys.stdout:
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr:
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich import box

from cyclenest.models import DailyLog, FlowLevel
from cyclenest.db import Database, DEFAULT_DB_PATH
from cyclenest.analyzer import CycleAnalyzer
from cyclenest.predictor import EnsembleCyclePredictor
from cyclenest.ui import ConsoleUI
from cyclenest.sample_data import generate_sample_data
from cyclenest.export import export_to_csv, export_to_json, import_from_csv, import_from_json
from cyclenest.charts import (
    render_cycle_length_barchart,
    render_bbt_curve,
    render_symptom_frequency_chart,
    render_mood_distribution_chart,
    render_cramps_by_cycle_day,
)


class CycleNestApp:
    def __init__(self, db_path: Optional[str] = None):
        self.console = Console(legacy_windows=False)
        self.ui = ConsoleUI(self.console)
        self.db = Database(db_path)
        self.predictor = EnsembleCyclePredictor()

    def get_analyzer(self) -> CycleAnalyzer:
        logs = self.db.get_all_daily_logs()
        def_cycle = int(self.db.get_setting("default_cycle_length", "28"))
        def_period = int(self.db.get_setting("default_period_length", "5"))
        def_luteal = int(self.db.get_setting("default_luteal_length", "14"))
        return CycleAnalyzer(
            logs=logs,
            default_cycle_length=def_cycle,
            default_period_length=def_period,
            default_luteal_length=def_luteal,
        )

    def run_menu(self) -> None:
        self.console.clear()
        self.ui.print_banner()

        # If database is completely empty, offer to preload sample data
        if self.db.get_total_log_count() == 0:
            self.console.print(
                Panel(
                    "👋 [bold yellow]Welcome to CycleNest![/bold yellow]\n"
                    "Your database is currently brand new and empty.\n"
                    "Would you like to preload [bold green]6 months of realistic clinical benchmark data[/bold green] "
                    "to immediately experience the pattern analysis, prediction models, and terminal charts?",
                    box=box.ROUNDED,
                    border_style="yellow",
                )
            )
            if Confirm.ask("Preload sample benchmark data?", default=True):
                sample_logs = generate_sample_data(date.today())
                self.db.batch_save_logs(sample_logs)
                self.console.print(f"[bold green]✓ Loaded {len(sample_logs)} daily logs across 6 cycles![/bold green]\n")

        while True:
            analyzer = self.get_analyzer()
            prediction = self.predictor.predict(
                analyzer.get_completed_cycles(),
                analyzer.get_current_cycle(),
                analyzer.logs,
                analyzer.default_cycle_length,
                analyzer.default_luteal_length,
            )

            # Show Today's Status Banner
            today_log = self.db.get_daily_log(date.today())
            self.ui.print_today_dashboard(analyzer, prediction, today_log)

            self.console.print("\n[bold magenta]═════════ MAIN MENU ═════════[/bold magenta]")
            self.console.print("  [bold cyan]1[/bold cyan] 📅 Refresh Today's Dashboard")
            self.console.print("  [bold cyan]2[/bold cyan] ✍️  Log Daily Health Data (Quick / Detailed)")
            self.console.print("  [bold cyan]3[/bold cyan] 🗓️  Monthly Cycle Calendar (Visual Grid)")
            self.console.print("  [bold cyan]4[/bold cyan] 📊 Pattern & Regularity Analytics (Clinical stats)")
            self.console.print("  [bold cyan]5[/bold cyan] 🔮 Multi-Model Predictions & Comparisons")
            self.console.print("  [bold cyan]6[/bold cyan] 🔭 Forward Horizon Forecast (Next 4-6 Cycles)")
            self.console.print("  [bold cyan]7[/bold cyan] 📈 Visual Terminal Charts (BBT, Lengths, Symptoms)")
            self.console.print("  [bold cyan]8[/bold cyan] 📜 Browse / Inspect / Edit Historical Logs")
            self.console.print("  [bold cyan]9[/bold cyan] 🩸 Record Past Period Dates (Quick Batch)")
            self.console.print(" [bold cyan]10[/bold cyan] 💾 Data Management (Export, Import, Benchmark)")
            self.console.print(" [bold cyan]11[/bold cyan] ⚙️  Settings & Preferences")
            self.console.print(" [bold magenta]12[/bold magenta] 🖥️  Launch Graphical Desktop App (GUI)")
            self.console.print("  [bold red]0[/bold red] 🚪 Exit")

            choice = Prompt.ask("\n[bold]Select an option[/bold]", choices=[str(i) for i in range(13)], default="1")

            if choice == "0":
                self.console.print("\n[bold magenta]Thank you for using CycleNest. Take care of yourself! 🌸[/bold magenta]")
                break
            elif choice == "1":
                self.console.clear()
                self.ui.print_banner()
            elif choice == "2":
                self._handle_logging_flow()
            elif choice == "3":
                self._handle_calendar_flow(analyzer, prediction)
            elif choice == "4":
                self._handle_analytics_flow(analyzer)
            elif choice == "5":
                self._handle_predictions_flow(analyzer)
            elif choice == "6":
                self._handle_forecast_flow(analyzer)
            elif choice == "7":
                self._handle_charts_flow(analyzer)
            elif choice == "8":
                self._handle_logs_flow()
            elif choice == "9":
                self._handle_batch_period_flow()
            elif choice == "10":
                self._handle_data_management_flow()
            elif choice == "11":
                self._handle_settings_flow()
            elif choice == "12":
                self.console.print("[bold green]Launching CycleNest GUI...[/bold green]")
                from cyclenest.gui.app import launch_gui
                launch_gui(self.db.db_path)

    def _handle_logging_flow(self) -> None:
        self.console.print("\n[bold cyan]Select Date to Log:[/bold cyan]")
        self.console.print("  1) Today (" + date.today().isoformat() + ")")
        self.console.print("  2) Yesterday (" + (date.today() - timedelta(days=1)).isoformat() + ")")
        self.console.print("  3) Specific Custom Date")
        d_choice = Prompt.ask("Choose date", choices=["1", "2", "3"], default="1")

        if d_choice == "1":
            target_date = date.today()
        elif d_choice == "2":
            target_date = date.today() - timedelta(days=1)
        else:
            d_str = Prompt.ask("Enter date (YYYY-MM-DD)", default=date.today().isoformat())
            try:
                target_date = date.fromisoformat(d_str)
            except ValueError:
                self.console.print("[red]Invalid date format. Using today.[/red]")
                target_date = date.today()

        existing = self.db.get_daily_log(target_date)
        if existing:
            self.console.print(f"[yellow]⚠️ Existing entry found for {target_date.isoformat()}. Modifying will overwrite.[/yellow]")

        self.console.print("\n[bold]Logging Mode:[/bold]")
        self.console.print("  1) ⚡ Quick Check-in (Flow & Cramps - 15 seconds)")
        self.console.print("  2) 📋 Detailed Log (BBT, Mucus, Moods, Symptoms, Notes)")
        mode = Prompt.ask("Choose mode", choices=["1", "2"], default="1")

        if mode == "1":
            log = self.ui.prompt_quick_log(target_date)
        else:
            log = self.ui.prompt_detailed_log(existing, target_date)

        self.db.save_daily_log(log)
        self.console.print(f"[bold green]✓ Successfully saved log for {target_date.isoformat()}![/bold green]\n")
        Prompt.ask("Press Enter to continue")

    def _handle_calendar_flow(self, analyzer: CycleAnalyzer, prediction: PredictionResult) -> None:
        curr_y = date.today().year
        curr_m = date.today().month

        while True:
            self.console.clear()
            self.ui.render_monthly_calendar(curr_y, curr_m, analyzer, prediction)
            self.console.print("\n[bold]Calendar Navigation:[/bold] [P]revious Month  |  [N]ext Month  |  [J]ump to Month  |  [B]ack to Menu")
            nav = Prompt.ask("Navigation", choices=["P", "p", "N", "n", "J", "j", "B", "b"], default="b").upper()

            if nav == "B":
                break
            elif nav == "P":
                if curr_m == 1:
                    curr_m = 12
                    curr_y -= 1
                else:
                    curr_m -= 1
            elif nav == "N":
                if curr_m == 12:
                    curr_m = 1
                    curr_y += 1
                else:
                    curr_m += 1
            elif nav == "J":
                y_in = IntPrompt.ask("Enter Year (e.g. 2026)", default=curr_y)
                m_in = IntPrompt.ask("Enter Month (1-12)", default=curr_m)
                if 1 <= m_in <= 12 and 1900 <= y_in <= 2100:
                    curr_y, curr_m = y_in, m_in

    def _handle_analytics_flow(self, analyzer: CycleAnalyzer) -> None:
        self.console.clear()
        self.ui.render_pattern_analytics(analyzer)
        Prompt.ask("\nPress Enter to return to menu")

    def _handle_predictions_flow(self, analyzer: CycleAnalyzer) -> None:
        self.console.clear()
        self.ui.render_prediction_comparison(analyzer, self.predictor)
        Prompt.ask("\nPress Enter to return to menu")

    def _handle_forecast_flow(self, analyzer: CycleAnalyzer) -> None:
        self.console.clear()
        count = IntPrompt.ask("How many future cycles to forecast (1 to 6)?", default=4)
        count = max(1, min(6, count))
        self.ui.render_multi_cycle_forecast(analyzer, self.predictor, count=count)
        Prompt.ask("\nPress Enter to return to menu")

    def _handle_charts_flow(self, analyzer: CycleAnalyzer) -> None:
        while True:
            self.console.clear()
            self.console.print("[bold magenta]📈 Terminal Charts & Graphical Trends[/bold magenta]")
            self.console.print("  1) Cycle Length Historical Progression")
            self.console.print("  2) Basal Body Temperature (BBT) Biphasic Shift Curve")
            self.console.print("  3) Top Symptom Frequency Distribution")
            self.console.print("  4) Mood & Emotional State Frequency")
            self.console.print("  5) Cramp / Pain Intensity by Cycle Day")
            self.console.print("  0) Back to Menu")

            c_choice = Prompt.ask("Select chart to render", choices=["0", "1", "2", "3", "4", "5"], default="1")
            if c_choice == "0":
                break

            self.console.clear()
            if c_choice == "1":
                stats = analyzer.compute_statistics()
                chart = render_cycle_length_barchart(analyzer.get_completed_cycles(), stats["mean_cycle_length"])
                self.console.print(chart)
            elif c_choice == "2":
                chart = render_bbt_curve(analyzer.logs)
                self.console.print(chart)
            elif c_choice == "3":
                s_data = analyzer.analyze_symptom_patterns()
                chart = render_symptom_frequency_chart(s_data["top_symptoms"], s_data["total_logged_days"])
                self.console.print(chart)
            elif c_choice == "4":
                s_data = analyzer.analyze_symptom_patterns()
                chart = render_mood_distribution_chart(s_data["top_moods"], s_data["total_logged_days"])
                self.console.print(chart)
            elif c_choice == "5":
                s_data = analyzer.analyze_symptom_patterns()
                chart = render_cramps_by_cycle_day(s_data["avg_cramps_by_day"])
                self.console.print(chart)

            Prompt.ask("\nPress Enter to continue")

    def _handle_logs_flow(self) -> None:
        self.console.clear()
        logs = self.db.get_all_daily_logs()
        self.ui.render_logs_table(logs, limit=20)

        self.console.print("\n[bold]Log Actions:[/bold] [I]nspect Date Detail  |  [D]elete Date  |  [B]ack")
        act = Prompt.ask("Action", choices=["I", "i", "D", "d", "B", "b"], default="B").upper()

        if act == "I":
            d_str = Prompt.ask("Enter date to inspect (YYYY-MM-DD)")
            try:
                d = date.fromisoformat(d_str)
                log = self.db.get_daily_log(d)
                if log:
                    self.console.print(Panel(str(log.to_dict()), title=f"Log: {d_str}", box=box.ROUNDED))
                else:
                    self.console.print(f"[yellow]No log found for {d_str}[/yellow]")
            except ValueError:
                self.console.print("[red]Invalid date[/red]")
            Prompt.ask("Press Enter to continue")
        elif act == "D":
            d_str = Prompt.ask("Enter date to delete (YYYY-MM-DD)")
            try:
                d = date.fromisoformat(d_str)
                if Confirm.ask(f"Are you sure you want to delete log for {d_str}?", default=False):
                    if self.db.delete_daily_log(d):
                        self.console.print("[green]Deleted successfully.[/green]")
                    else:
                        self.console.print("[yellow]Date not found.[/yellow]")
            except ValueError:
                self.console.print("[red]Invalid date[/red]")
            Prompt.ask("Press Enter to continue")

    def _handle_batch_period_flow(self) -> None:
        self.console.print("\n[bold magenta]🩸 Record Past Period Dates[/bold magenta]")
        self.console.print("[dim]Quickly add past period start date and duration to rebuild your cycle history.[/dim]")

        start_str = Prompt.ask("Period Start Date (YYYY-MM-DD)")
        try:
            start_d = date.fromisoformat(start_str)
        except ValueError:
            self.console.print("[red]Invalid date format[/red]")
            return

        duration = IntPrompt.ask("Duration of bleeding (days, typically 4-6)", default=5)
        duration = max(1, min(14, duration))

        new_logs: List[DailyLog] = []
        for i in range(duration):
            curr_d = start_d + timedelta(days=i)
            # Heavy on day 1-2, medium day 3, light after
            flow = (
                FlowLevel.HEAVY
                if i in (0, 1)
                else FlowLevel.MEDIUM
                if i == 2
                else FlowLevel.LIGHT
            )
            cramps = 3 if i == 0 else 2 if i == 1 else 0
            new_logs.append(
                DailyLog(
                    date=curr_d,
                    flow=flow,
                    cramps_pain=cramps,
                    notes="Logged via batch period entry",
                )
            )

        self.db.batch_save_logs(new_logs)
        self.console.print(f"[bold green]✓ Recorded {duration} days of period flow starting {start_str}![/bold green]")
        Prompt.ask("Press Enter to continue")

    def _handle_data_management_flow(self) -> None:
        self.console.clear()
        self.console.print("[bold magenta]💾 Data Management & Backups[/bold magenta]")
        self.console.print("  1) Export all data to CSV")
        self.console.print("  2) Export all data to JSON")
        self.console.print("  3) Import data from CSV")
        self.console.print("  4) Import data from JSON")
        self.console.print("  5) Preload 6-Month Clinical Benchmark Sample Data")
        self.console.print("  6) ⚠️  Wipe / Clear All Data")
        self.console.print("  0) Back to Menu")

        choice = Prompt.ask("Select option", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")
        logs = self.db.get_all_daily_logs()

        if choice == "1":
            file_name = Prompt.ask("Enter CSV file path", default="./cyclenest_export.csv")
            count = export_to_csv(logs, file_name)
            self.console.print(f"[bold green]✓ Exported {count} logs to {file_name}![/bold green]")
        elif choice == "2":
            file_name = Prompt.ask("Enter JSON file path", default="./cyclenest_export.json")
            count = export_to_json(logs, file_name)
            self.console.print(f"[bold green]✓ Exported {count} logs to {file_name}![/bold green]")
        elif choice == "3":
            file_name = Prompt.ask("Enter CSV file path to import")
            try:
                imported = import_from_csv(file_name)
                self.db.batch_save_logs(imported)
                self.console.print(f"[bold green]✓ Imported {len(imported)} logs from {file_name}![/bold green]")
            except Exception as e:
                self.console.print(f"[bold red]Import error: {e}[/bold red]")
        elif choice == "4":
            file_name = Prompt.ask("Enter JSON file path to import")
            try:
                imported = import_from_json(file_name)
                self.db.batch_save_logs(imported)
                self.console.print(f"[bold green]✓ Imported {len(imported)} logs from {file_name}![/bold green]")
            except Exception as e:
                self.console.print(f"[bold red]Import error: {e}[/bold red]")
        elif choice == "5":
            if Confirm.ask("Load 6-month benchmark dataset? (Will append/update logs)", default=True):
                sample_logs = generate_sample_data(date.today())
                self.db.batch_save_logs(sample_logs)
                self.console.print(f"[bold green]✓ Loaded {len(sample_logs)} sample logs across 6 cycles![/bold green]")
        elif choice == "6":
            if Confirm.ask("⚠️ Are you sure you want to delete ALL logged data? This cannot be undone!", default=False):
                self.db.clear_all()
                self.console.print("[bold red]Database cleared.[/bold red]")

        Prompt.ask("\nPress Enter to continue")

    def _handle_settings_flow(self) -> None:
        self.console.clear()
        self.console.print("[bold magenta]⚙️  Settings & Preferences[/bold magenta]")

        curr_cycle = self.db.get_setting("default_cycle_length", "28")
        curr_period = self.db.get_setting("default_period_length", "5")
        curr_luteal = self.db.get_setting("default_luteal_length", "14")
        curr_unit = self.db.get_setting("temp_unit", "C")

        self.console.print(f"  Current baseline cycle length: [bold cyan]{curr_cycle} days[/bold cyan]")
        self.console.print(f"  Current baseline period length: [bold cyan]{curr_period} days[/bold cyan]")
        self.console.print(f"  Current baseline luteal length: [bold cyan]{curr_luteal} days[/bold cyan]")
        self.console.print(f"  Temperature unit: [bold cyan]°{curr_unit}[/bold cyan]")

        if Confirm.ask("\nWould you like to modify these settings?", default=False):
            new_cycle = IntPrompt.ask("Default cycle length (days, 21-45)", default=int(curr_cycle))
            new_period = IntPrompt.ask("Default period bleeding length (days, 3-9)", default=int(curr_period))
            new_luteal = IntPrompt.ask("Default luteal phase length (days, 10-16)", default=int(curr_luteal))
            new_unit = Prompt.ask("Temperature unit (C or F)", choices=["C", "F"], default=curr_unit)

            self.db.set_setting("default_cycle_length", str(new_cycle))
            self.db.set_setting("default_period_length", str(new_period))
            self.db.set_setting("default_luteal_length", str(new_luteal))
            self.db.set_setting("temp_unit", new_unit)
            self.console.print("[bold green]✓ Settings updated successfully![/bold green]")

        Prompt.ask("\nPress Enter to continue")


def main() -> None:
    parser = argparse.ArgumentParser(description="CycleNest - Desktop Menstrual Cycle Tracker & Intelligence Suite")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch the modern graphical desktop application (GUI)")
    parser.add_argument("--today", "-t", action="store_true", help="Print today's cycle dashboard and exit")
    parser.add_argument("--predict", "-p", action="store_true", help="Print prediction models comparison and exit")
    parser.add_argument("--stats", "-s", action="store_true", help="Print cycle pattern analytics and exit")
    parser.add_argument("--calendar", "-c", nargs="?", const="current", help="Print monthly calendar (optional: YYYY-MM)")
    parser.add_argument("--load-benchmark", action="store_true", help="Load realistic 6-month clinical test data")
    parser.add_argument("--db", type=str, default=None, help="Custom database path")

    args = parser.parse_args()

    if args.gui:
        from cyclenest.gui.app import launch_gui
        launch_gui(args.db)
        return

    app = CycleNestApp(db_path=args.db)

    if args.load_benchmark:
        sample_logs = generate_sample_data(date.today())
        app.db.batch_save_logs(sample_logs)
        app.console.print(f"[bold green]✓ Preloaded {len(sample_logs)} benchmark logs![/bold green]")
        return

    if args.today:
        analyzer = app.get_analyzer()
        pred = app.predictor.predict(
            analyzer.get_completed_cycles(),
            analyzer.get_current_cycle(),
            analyzer.logs,
            analyzer.default_cycle_length,
            analyzer.default_luteal_length,
        )
        app.ui.print_today_dashboard(analyzer, pred, app.db.get_daily_log(date.today()))
        return

    if args.predict:
        analyzer = app.get_analyzer()
        app.ui.render_prediction_comparison(analyzer, app.predictor)
        app.ui.render_multi_cycle_forecast(analyzer, app.predictor, count=4)
        return

    if args.stats:
        analyzer = app.get_analyzer()
        app.ui.render_pattern_analytics(analyzer)
        return

    if args.calendar:
        analyzer = app.get_analyzer()
        pred = app.predictor.predict(
            analyzer.get_completed_cycles(),
            analyzer.get_current_cycle(),
            analyzer.logs,
            analyzer.default_cycle_length,
            analyzer.default_luteal_length,
        )
        today = date.today()
        year, month = today.year, today.month
        if args.calendar != "current":
            try:
                parts = args.calendar.split("-")
                year, month = int(parts[0]), int(parts[1])
            except Exception:
                pass
        app.ui.render_monthly_calendar(year, month, analyzer, pred)
        return

    # Default: launch interactive menu
    app.run_menu()


if __name__ == "__main__":
    main()
