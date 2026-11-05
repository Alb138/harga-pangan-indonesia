"""Every chart helper returns a labelled matplotlib Figure for small synthetic inputs."""

import matplotlib

matplotlib.use("Agg")

import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from pangan import plots  # noqa: E402

LEBARAN = pd.DataFrame(
    {
        "commodity_id": ["com_1"] * 6,
        "commodity_name": ["Beras Kualitas Bawah I"] * 6,
        "lebaran_year": [2023, 2023, 2023, 2024, 2024, 2024],
        "t": [-60, -7, 10, -60, -7, 10],
        "price_index": [1.0, 1.15, 1.02, 1.0, 1.25, 1.05],
    }
)
VOLATILITY = pd.DataFrame(
    {"commodity_name": ["Cabai Rawit Merah", "Beras Kualitas Bawah I"], "std_pct_1w": [0.08, 0.01]}
)
PROVINCE_INDEX = pd.DataFrame(
    {
        "commodity_id": ["com_1"] * 3,
        "commodity_name": ["Beras Kualitas Bawah I"] * 3,
        "province_name": ["Papua", "DKI Jakarta", "Jawa Tengah"],
        "index_vs_median": [1.4, 1.05, 0.9],
    }
)
MARKUP = pd.DataFrame(
    {
        "commodity_name": ["Cabai Rawit Merah"] * 3,
        "from_level": ["Produsen", "Pedagang Besar", "Pasar Tradisional"],
        "to_level": ["Pedagang Besar", "Pasar Tradisional", "Pasar Modern"],
        "markup_pct": [0.2, 0.25, 0.1],
    }
)
AFFORDABILITY = pd.DataFrame(
    {"province_name": ["Jawa Tengah", "DKI Jakarta"], "share_of_ump": [0.45, 0.25]}
)
COVERAGE = pd.DataFrame(
    {
        "province_name": ["Aceh", "Aceh", "Papua", "Papua"],
        "year": [2018, 2019, 2018, 2019],
        "pct_business_days": [0.96, 0.95, 0.0, 0.5],
    }
)


@pytest.mark.parametrize(
    ("make", "frame"),
    [
        (lambda df: plots.plot_lebaran_index(df, "com_1"), LEBARAN),
        (plots.plot_volatility, VOLATILITY),
        (lambda df: plots.plot_province_index(df, "com_1"), PROVINCE_INDEX),
        (plots.plot_markup, MARKUP),
        (plots.plot_affordability, AFFORDABILITY),
        (plots.plot_coverage, COVERAGE),
    ],
)
def test_plots_return_figures(make, frame):
    fig = make(frame)
    assert isinstance(fig, Figure)
    ax = fig.axes[0]
    assert ax.get_title(loc="left")  # titles are left-aligned by design
    assert ax.get_xlabel()
    assert ax.get_ylabel() or ax.get_yticklabels()


def test_save_fig_writes_png(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "FIG_DIR", tmp_path)
    path = plots.save_fig(plots.plot_volatility(VOLATILITY), "volatility")
    assert path == tmp_path / "volatility.png"
    assert path.stat().st_size > 0


def test_lebaran_median_line_is_continuous():
    """Years report on different weekdays; the median line must not break or zig-zag on gaps."""
    gappy = pd.DataFrame(
        {
            "commodity_id": ["com_1"] * 8,
            "commodity_name": ["Beras"] * 8,
            "lebaran_year": [2023] * 4 + [2024] * 4,
            "t": [-10, -8, -6, -4, -9, -7, -5, -3],
            "price_index": [1.0, 1.1, 1.2, 1.3, 1.0, 1.1, 1.2, 1.3],
        }
    )
    fig = plots.plot_lebaran_index(gappy, "com_1")
    median_line = next(line for line in fig.axes[0].lines if line.get_color() == plots.SERIES[0])
    assert list(median_line.get_xdata()) == list(range(-10, -2))
    # each year is interpolated across its own gaps before the median is taken, so the
    # two identical-but-shifted seasons give a smooth ramp instead of a staircase
    expected = [1.0, 1.025, 1.075, 1.125, 1.175, 1.225, 1.275, 1.3]
    assert list(median_line.get_ydata()) == pytest.approx(expected)
