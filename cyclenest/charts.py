"""Custom High-Resolution Terminal Graphics and Unicode Visualizations for CycleNest.
Pure Python + Rich rendering: zero dependency issues, cross-platform Windows compatibility.
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import RenderableType
from rich import box

from cyclenest.models import Cycle, DailyLog, CyclePhase


def render_cycle_length_barchart(
    completed_cycles: List[Cycle], avg_len: float
) -> RenderableType:
    """Render a horizontal bar visualization of historical cycle lengths."""
    table = Table(
        title="📈 Historical Cycle Length Progression",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("Cycle", style="bold yellow", width=10)
    table.add_column("Start Date", style="dim", width=12)
    table.add_column("Length", justify="right", width=9)
    table.add_column("Visual Distribution (20 - 40 Days)", width=42)
    table.add_column("Delta vs Avg", justify="right", width=14)

    if not completed_cycles:
        table.add_row("-", "-", "-", "[dim]No completed cycles recorded yet[/dim]", "-")
        return table

    min_scale = 20
    max_scale = 40
    bar_width = 32

    for c in completed_cycles:
        c_len = c.length_days or 28
        delta = c_len - avg_len
        delta_str = (
            f"[green]+{delta:.1f}d[/green]"
            if delta > 0.2
            else f"[cyan]{delta:.1f}d[/cyan]"
            if delta < -0.2
            else "[dim]0.0d[/dim]"
        )

        # Scale length to bar width
        clamped = max(min_scale, min(max_scale, c_len))
        fill_count = int(((clamped - min_scale) / (max_scale - min_scale)) * bar_width)
        fill_count = max(1, min(bar_width, fill_count))

        # Color based on clinical classification
        if 24 <= c_len <= 35:
            bar_color = "green"
            status_tag = "Normal"
        elif 21 <= c_len < 24 or 35 < c_len <= 38:
            bar_color = "yellow"
            status_tag = "Variable"
        else:
            bar_color = "bright_red"
            status_tag = "Irregular"

        bar = f"[{bar_color}]{'█' * fill_count}[/{bar_color}]{'░' * (bar_width - fill_count)}"

        table.add_row(
            f"Cycle #{c.cycle_number}",
            c.start_date.isoformat(),
            f"[bold]{c_len} days[/bold]",
            f"{bar} [{bar_color}]{status_tag}[/{bar_color}]",
            delta_str,
        )

    return table


def render_bbt_curve(logs: List[DailyLog]) -> RenderableType:
    """Render a terminal ASCII/Unicode curve for Basal Body Temperature (BBT)."""
    bbt_logs = [l for l in logs if l.bbt is not None]
    if len(bbt_logs) < 5:
        p_text = Text(
            "⚠️ Insufficient temperature logs. Log at least 5 days of morning BBT to display thermal shift curve.",
            style="yellow",
        )
        return Panel(p_text, title="🌡️ Basal Body Temperature (BBT) Thermal Shift Curve", box=box.ROUNDED)

    # Use the most recent 30 logged days
    recent = bbt_logs[-30:]
    temps = [l.bbt for l in recent]
    dates = [l.date for l in recent]

    min_t = min(temps)
    max_t = max(temps)

    # Pad temperature range
    min_t_bound = math_floor_step(min_t - 0.1, 0.1)
    max_t_bound = math_ceil_step(max_t + 0.1, 0.1)

    chart_height = 10
    step = (max_t_bound - min_t_bound) / (chart_height - 1) if chart_height > 1 else 0.1

    # Grid rows
    lines: List[str] = []
    # Identify coverline (average of all temps, or midpoint between low & high)
    coverline = sum(temps) / len(temps)

    for row_idx in range(chart_height - 1, -1, -1):
        row_temp = min_t_bound + row_idx * step
        label = f"{row_temp:5.2f}°C │"
        row_chars = []

        for t in temps:
            # Check if temperature is close to this row
            dist = abs(t - row_temp)
            if dist <= (step * 0.55):
                if t >= coverline + 0.1:
                    row_chars.append("[bright_red]●[/bright_red]")  # Post-ovulatory luteal high
                elif t >= coverline:
                    row_chars.append("[yellow]●[/yellow]")
                else:
                    row_chars.append("[bright_cyan]●[/bright_cyan]")  # Follicular low
            elif abs(coverline - row_temp) <= (step * 0.3):
                row_chars.append("[dim]---[/dim]"[0])  # Coverline dashed
            else:
                row_chars.append(" ")
        lines.append(f"{label} {'  '.join(row_chars)}")

    # X-axis
    axis_line = "      └" + "─" * (len(temps) * 3 + 1)
    lines.append(axis_line)

    # Day labels (dates or day indices)
    day_labels = "       " + " ".join(f"{d.day:2d}" for d in dates)
    lines.append(day_labels)
    lines.append("       [dim](Day of month)[/dim]")

    legend = (
        "\n[bold]Legend:[/bold] "
        "[bright_cyan]● Follicular Phase (Low)[/bright_cyan]   "
        "[dim]--- Coverline[/dim]   "
        "[bright_red]● Luteal Phase (Thermal Shift +0.2-0.5°C Progesterone Rise)[/bright_red]"
    )

    full_content = Text.from_markup("\n".join(lines) + "\n" + legend)
    return Panel(
        full_content,
        title="🌡️ Basal Body Temperature (BBT) Biphasic Thermal Shift Curve",
        border_style="magenta",
        box=box.ROUNDED,
    )


def render_symptom_frequency_chart(top_symptoms: List[Tuple[str, int]], total_days: int) -> RenderableType:
    """Render a horizontal bar chart of top logged symptoms."""
    table = Table(
        title="🩺 Symptom Occurrence Frequency",
        box=box.ROUNDED,
        header_style="bold red",
        show_lines=False,
    )
    table.add_column("Symptom", style="bold white", width=24)
    table.add_column("Count", justify="right", style="cyan", width=8)
    table.add_column("Frequency Bar", width=36)
    table.add_column("% of Days", justify="right", style="green", width=12)

    if not top_symptoms:
        table.add_row("-", "-", "[dim]No symptoms logged yet[/dim]", "-")
        return table

    max_count = top_symptoms[0][1] if top_symptoms else 1
    bar_width = 24

    for sym, count in top_symptoms:
        fill_len = int((count / max_count) * bar_width)
        fill_len = max(1, fill_len)
        bar = f"[red]{'█' * fill_len}[/red][dim]{'░' * (bar_width - fill_len)}[/dim]"
        pct = (count / total_days * 100) if total_days > 0 else 0
        table.add_row(sym, str(count), bar, f"{pct:.1f}%")

    return table


def render_mood_distribution_chart(top_moods: List[Tuple[str, int]], total_days: int) -> RenderableType:
    """Render a horizontal bar chart of top logged moods."""
    table = Table(
        title="🧠 Mood & Emotional State Frequency",
        box=box.ROUNDED,
        header_style="bold magenta",
        show_lines=False,
    )
    table.add_column("Mood", style="bold white", width=24)
    table.add_column("Count", justify="right", style="cyan", width=8)
    table.add_column("Distribution Bar", width=36)
    table.add_column("% of Days", justify="right", style="green", width=12)

    if not top_moods:
        table.add_row("-", "-", "[dim]No moods logged yet[/dim]", "-")
        return table

    max_count = top_moods[0][1] if top_moods else 1
    bar_width = 24

    for mood, count in top_moods:
        fill_len = int((count / max_count) * bar_width)
        fill_len = max(1, fill_len)
        bar = f"[magenta]{'█' * fill_len}[/magenta][dim]{'░' * (bar_width - fill_len)}[/dim]"
        pct = (count / total_days * 100) if total_days > 0 else 0
        table.add_row(mood, str(count), bar, f"{pct:.1f}%")

    return table


def render_cramps_by_cycle_day(cramps_by_day: Dict[int, float]) -> RenderableType:
    """Render cramp / pain intensity across cycle days (1 to 10)."""
    table = Table(
        title="⚡ Pain / Cramp Intensity by Cycle Day",
        box=box.ROUNDED,
        header_style="bold yellow",
        show_lines=False,
    )
    table.add_column("Cycle Day", style="bold yellow", width=12)
    table.add_column("Avg Pain (0-5)", justify="right", style="bold red", width=16)
    table.add_column("Intensity Bar", width=30)
    table.add_column("Clinical Severity", width=18)

    if not cramps_by_day:
        table.add_row("-", "-", "[dim]No cramp pain logged yet[/dim]", "-")
        return table

    for day in range(1, 11):
        if day in cramps_by_day:
            avg_pain = cramps_by_day[day]
            fill = int((avg_pain / 5.0) * 20)
            bar = f"[bold red]{'█' * fill}[/bold red][dim]{'░' * (20 - fill)}[/dim]"
            if avg_pain >= 3.5:
                sev = "[bold red]Severe (Peak)[/bold red]"
            elif avg_pain >= 2.0:
                sev = "[yellow]Moderate[/yellow]"
            elif avg_pain >= 0.5:
                sev = "[cyan]Mild[/cyan]"
            else:
                sev = "[dim]Minimal[/dim]"
            table.add_row(f"Day {day}", f"{avg_pain:.1f} / 5.0", bar, sev)

    return table


def math_floor_step(val: float, step: float) -> float:
    return math_round(math_floor(val / step) * step, 2)


def math_ceil_step(val: float, step: float) -> float:
    return math_round(math_ceil(val / step) * step, 2)


def math_floor(x: float) -> int:
    import math
    return math.floor(x)


def math_ceil(x: float) -> int:
    import math
    return math.ceil(x)


def math_round(x: float, n: int) -> float:
    return round(x, n)
