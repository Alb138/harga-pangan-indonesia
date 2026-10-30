"""Chart helpers in one consistent style: thin marks, hairline grid, a validated palette.

Colors come from the dataviz reference palette (categorical slots in fixed order,
blue sequential ramp, blue<->red diverging pair with a neutral gray midpoint).
"""

from collections.abc import Callable
from functools import wraps
from pathlib import Path

import matplotlib as mpl
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter

from pangan.config import FIG_DIR

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
CHEAPER, NEUTRAL, PRICIER = "#2a78d6", "#c3c2b7", "#e34948"
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SOURCE = "Source: PIHPS Nasional, Bank Indonesia"
FONT = {"font.family": ["Segoe UI", "DejaVu Sans"]}


def _styled(plot: Callable[..., Figure]) -> Callable[..., Figure]:
    """Build the figure inside the house font so ticks, labels and titles match."""

    @wraps(plot)
    def wrapper(*args, **kwargs) -> Figure:
        with mpl.rc_context(FONT):
            return plot(*args, **kwargs)

    return wrapper


def _figure(width: float = 8, height: float = 4.5) -> tuple[Figure, Axes]:
    fig = Figure(figsize=(width, height), facecolor=SURFACE, layout="constrained")
    ax = fig.subplots()
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=INK_2, labelsize=9, length=0)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def _finish(fig: Figure, ax: Axes, title: str, xlabel: str, ylabel: str = "", source=SOURCE):
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, color=INK_2, fontsize=9)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=9)
    fig.supxlabel(source, x=0.01, ha="left", fontsize=7.5, color=MUTED)
    return fig


def _name(df: pd.DataFrame, column: str = "commodity_name") -> str:
    return str(df[column].iloc[0]) if column in df and not df.empty else ""


def _barh_height(n_bars: int) -> float:
    return max(3.0, 0.28 * n_bars + 1.2)


@_styled
def plot_lebaran_index(df: pd.DataFrame, commodity_id: str) -> Figure:
    """Each Lebaran season as a thin gray line, the median season emphasised in blue."""
    data = df[df["commodity_id"] == commodity_id]
    fig, ax = _figure()
    for _, season in data.groupby("lebaran_year"):
        ax.plot(season["t"], season["price_index"], color=AXIS, linewidth=1)
    median = data.groupby("t")["price_index"].median()
    ax.plot(median.index, median.values, color=SERIES[0], linewidth=2)
    ax.axhline(1.0, color=AXIS, linewidth=1)
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.annotate("Idul Fitri", xy=(0, 1), xycoords=("data", "axes fraction"), xytext=(4, -12),
                textcoords="offset points", color=INK_2, fontsize=8)
    ax.legend(
        handles=[
            Line2D([], [], color=AXIS, linewidth=1, label="Each year"),
            Line2D([], [], color=SERIES[0], linewidth=2,
                   label=f"Median of {data['lebaran_year'].nunique()} years"),
        ],
        frameon=False, fontsize=8, loc="upper left",
    )
    return _finish(
        fig, ax,
        f"{_name(data) or commodity_id}: prices around Lebaran",
        "Days relative to Idul Fitri (negative = before)",
        "Price index (H-60 to H-46 = 1.0)",
    )


@_styled
def plot_volatility(df: pd.DataFrame) -> Figure:
    """Ranked bars of average week-to-week volatility per commodity."""
    ranked = df.groupby("commodity_name")["std_pct_1w"].mean().sort_values()
    fig, ax = _figure(height=_barh_height(len(ranked)))
    ax.barh(ranked.index, ranked.values, color=SERIES[0], height=0.6)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", visible=False)
    return _finish(fig, ax, "How much prices swing week to week",
                   "Typical weekly price change (std. dev. of % change)")


@_styled
def plot_province_index(df: pd.DataFrame, commodity_id: str) -> Figure:
    """Diverging bars: how far each province sits above/below the median province."""
    data = df[df["commodity_id"] == commodity_id]
    gap = (data.groupby("province_name")["index_vs_median"].mean() - 1).sort_values()
    colors = [PRICIER if g > 0.02 else CHEAPER if g < -0.02 else NEUTRAL for g in gap]
    fig, ax = _figure(height=_barh_height(len(gap)))
    ax.barh(gap.index, gap.values, color=colors, height=0.6)
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", visible=False)
    return _finish(fig, ax, f"{_name(data) or commodity_id}: price gap between provinces",
                   "Price vs. the median province")


@_styled
def plot_markup(df: pd.DataFrame) -> Figure:
    """Grouped bars: price increase at each step of the supply chain, per commodity."""
    df = df.assign(step=df["from_level"] + " → " + df["to_level"])
    steps = list(dict.fromkeys(df["step"]))
    table = df.pivot_table(index="commodity_name", columns="step", values="markup_pct")
    table = table[steps].sort_values(steps[0])
    fig, ax = _figure(height=_barh_height(len(table) * len(steps) * 0.5))
    bar = 0.8 / len(steps)
    for i, step in enumerate(steps):
        # first chain step on top of each group, matching the legend's reading order
        positions = [y + ((len(steps) - 1) / 2 - i) * bar for y in range(len(table))]
        ax.barh(positions, table[step], height=bar * 0.9, color=SERIES[i], label=step)
    ax.set_yticks(range(len(table)), table.index)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    return _finish(fig, ax, "Where the price grows along the supply chain",
                   "Price increase vs. the previous level")


@_styled
def plot_affordability(df: pd.DataFrame) -> Figure:
    """Ranked bars of the food basket's share of the provincial minimum wage."""
    ranked = df.groupby("province_name")["share_of_ump"].mean().sort_values()
    fig, ax = _figure(height=_barh_height(len(ranked)))
    ax.barh(ranked.index, ranked.values, color=SERIES[0], height=0.6)
    for province in {ranked.index[0], ranked.index[-1]}:
        ax.annotate(f"{ranked[province]:.0%}", xy=(ranked[province], province), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8, color=INK_2)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", visible=False)
    return _finish(fig, ax, "Monthly food basket as a share of the minimum wage",
                   "Basket cost for a 4-person household (% of UMP)",
                   source=SOURCE + "; Badan Pusat Statistik")


@_styled
def plot_coverage(df: pd.DataFrame) -> Figure:
    """Heatmap of the share of business days with a price, per province and year."""
    grid = df.pivot_table(index="province_name", columns="year", values="pct_business_days")
    fig, ax = _figure(width=8, height=_barh_height(len(grid)))
    cmap = LinearSegmentedColormap.from_list("blue_seq", SEQUENTIAL)
    image = ax.imshow(grid.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(len(grid.columns)), grid.columns)
    ax.set_yticks(range(len(grid.index)), grid.index)
    ax.grid(visible=False)
    bar = fig.colorbar(image, ax=ax, format=PercentFormatter(1.0, decimals=0), shrink=0.6)
    bar.outline.set_visible(False)
    bar.ax.tick_params(colors=INK_2, labelsize=8, length=0)
    return _finish(fig, ax, "Data coverage: share of business days with a price", "Year")


def save_fig(fig: Figure, name: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    return path
