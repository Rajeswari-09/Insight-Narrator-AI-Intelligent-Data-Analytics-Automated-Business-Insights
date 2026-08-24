"""
visualizer.py — Visualizer Agent
Generates charts from a DataFrame and returns them as base64-encoded PNG strings.
Uses matplotlib and seaborn — no LLM required.
"""

import io
import base64
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from backend.utils.data_utils import classify_columns

warnings.filterwarnings("ignore")


# ── Design palette ─────────────────────────────────────────────
PALETTE = [
    "#00d4ff", "#7c3aed", "#06b6d4", "#a78bfa", "#34d399",
    "#f59e0b", "#ec4899", "#10b981", "#3b82f6", "#f97316"
]

BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#334155"


# ── Styling Utility ─────────────────────────────────────────────
def _apply_dark_style(fig, ax_list):

    fig.patch.set_facecolor(BG_COLOR)

    if isinstance(ax_list, np.ndarray):
        ax_list = ax_list.flatten().tolist()
    elif not isinstance(ax_list, (list, tuple)):
        ax_list = [ax_list]

    for ax in ax_list:
        ax.set_facecolor(CARD_COLOR)
        ax.tick_params(colors=TEXT_COLOR, labelsize=9)

        ax.xaxis.label.set_color(TEXT_COLOR)
        ax.yaxis.label.set_color(TEXT_COLOR)
        ax.title.set_color(TEXT_COLOR)

        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)

        ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.6)


# ── Convert Figure to Base64 ─────────────────────────────────────
def _fig_to_b64(fig):

    buf = io.BytesIO()

    fig.savefig(
        buf,
        format="png",
        dpi=130,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    buf.seek(0)

    img_b64 = base64.b64encode(buf.read()).decode("utf-8")

    plt.close(fig)

    return img_b64


# ── Visualizer Agent ─────────────────────────────────────────────
class VisualizerAgent:

    def run(self, df: pd.DataFrame) -> list:

        col_types = classify_columns(df)

        charts = []

        charts += self._numeric_distributions(df, col_types)
        charts += self._correlation_heatmap(df, col_types)
        charts += self._category_bar_charts(df, col_types)
        charts += self._time_series_charts(df, col_types)
        charts += self._revenue_by_category(df, col_types)

        return charts


    # ── Numeric Distributions ────────────────────────────────────
    def _numeric_distributions(self, df, col_types):

        numeric_cols = col_types["numeric"][:4]

        if not numeric_cols:
            return []

        n = len(numeric_cols)

        fig, axes = plt.subplots(1, n, figsize=(5*n,4))

        if n == 1:
            axes = [axes]

        for ax, col in zip(axes, numeric_cols):

            data = df[col].dropna()

            ax.hist(
                data,
                bins=25,
                color=PALETTE[0],
                edgecolor=BG_COLOR,
                alpha=0.85
            )

            ax.axvline(
                data.mean(),
                color=PALETTE[4],
                linewidth=1.5,
                linestyle="--",
                label=f"Mean: {data.mean():.1f}"
            )

            ax.legend(
                fontsize=8,
                facecolor=CARD_COLOR,
                labelcolor=TEXT_COLOR,
                edgecolor=GRID_COLOR
            )

            ax.set_title(
                f"Distribution — {col}",
                fontsize=10,
                fontweight="bold"
            )

            ax.set_xlabel(col, fontsize=9)
            ax.set_ylabel("Frequency", fontsize=9)

        _apply_dark_style(fig, axes)

        fig.suptitle(
            "Numeric Distributions",
            color=TEXT_COLOR,
            fontsize=13,
            fontweight="bold",
            y=1.02
        )

        fig.tight_layout()

        return [{"title":"Numeric Distributions","image":_fig_to_b64(fig)}]


    # ── Correlation Heatmap ─────────────────────────────────────
    def _correlation_heatmap(self, df, col_types):

        numeric_cols = col_types["numeric"]

        if len(numeric_cols) < 2:
            return []

        corr = df[numeric_cols].corr()

        fig, ax = plt.subplots(
            figsize=(max(6,len(numeric_cols)), max(5,len(numeric_cols)-1))
        )

        cmap = sns.diverging_palette(220,20,as_cmap=True)

        sns.heatmap(
            corr,
            ax=ax,
            cmap=cmap,
            annot=True,
            fmt=".2f",
            linewidths=0.5,
            linecolor=BG_COLOR,
            annot_kws={"size":9,"color":TEXT_COLOR},
            cbar_kws={"shrink":0.8}
        )

        ax.set_title(
            "Correlation Heatmap",
            fontsize=12,
            fontweight="bold",
            color=TEXT_COLOR,
            pad=12
        )

        ax.tick_params(axis="x",rotation=45,colors=TEXT_COLOR,labelsize=9)
        ax.tick_params(axis="y",rotation=0,colors=TEXT_COLOR,labelsize=9)

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(CARD_COLOR)

        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)

        fig.tight_layout()

        return [{"title":"Correlation Heatmap","image":_fig_to_b64(fig)}]


    # ── Category Bar Charts ─────────────────────────────────────
    def _category_bar_charts(self, df, col_types):

        charts = []

        cat_cols = [c for c in col_types["categorical"] if df[c].nunique()<=20][:2]
        numeric_cols = col_types["numeric"][:1]

        if not cat_cols or not numeric_cols:
            return charts

        num_col = numeric_cols[0]

        for cat_col in cat_cols:

            grouped = (
                df.groupby(cat_col)[num_col]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )

            fig, ax = plt.subplots(figsize=(8,4))

            bars = ax.bar(
                grouped.index.astype(str),
                grouped.values,
                color=PALETTE[:len(grouped)],
                edgecolor=BG_COLOR
            )

            for bar in bars:

                h = bar.get_height()

                ax.text(
                    bar.get_x()+bar.get_width()/2,
                    h*1.01,
                    f"{h:,.0f}",
                    ha="center",
                    va="bottom",
                    color=TEXT_COLOR,
                    fontsize=8
                )

            ax.set_title(
                f"Total {num_col} by {cat_col}",
                fontsize=11,
                fontweight="bold",
                color=TEXT_COLOR
            )

            ax.set_xlabel(cat_col)
            ax.set_ylabel(num_col)

            ax.tick_params(axis="x",rotation=30)

            _apply_dark_style(fig, ax)

            fig.tight_layout()

            charts.append({
                "title":f"{num_col} by {cat_col}",
                "image":_fig_to_b64(fig)
            })

        return charts


    # ── Time Series Charts ─────────────────────────────────────
    def _time_series_charts(self, df, col_types):

        if not col_types["datetime"] or not col_types["numeric"]:
            return []

        charts = []

        date_col = col_types["datetime"][0]

        df_sorted = df.sort_values(date_col)

        for num_col in col_types["numeric"][:2]:

            fig, ax = plt.subplots(figsize=(10,4))

            monthly = (
                df_sorted.set_index(date_col)[num_col]
                .resample("ME")
                .sum()
            )

            ax.plot(
                monthly.index,
                monthly.values,
                color=PALETTE[0],
                linewidth=2.5,
                marker="o"
            )

            ax.set_title(
                f"{num_col} Over Time",
                fontsize=11,
                fontweight="bold",
                color=TEXT_COLOR
            )

            ax.set_xlabel("Date")
            ax.set_ylabel(num_col)

            ax.tick_params(axis="x",rotation=30)

            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x,_:f"{x:,.0f}")
            )

            _apply_dark_style(fig, ax)

            fig.tight_layout()

            charts.append({
                "title":f"{num_col} Trend Over Time",
                "image":_fig_to_b64(fig)
            })

        return charts


    # ── Revenue Share Pie Chart ─────────────────────────────────
    def _revenue_by_category(self, df, col_types):

        cat_cols = [c for c in col_types["categorical"] if 2 <= df[c].nunique() <= 8]
        numeric_cols = col_types["numeric"]

        if not cat_cols or not numeric_cols:
            return []

        cat_col = cat_cols[0]
        num_col = numeric_cols[0]

        grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)

        fig, ax = plt.subplots(figsize=(7,5))

        wedges, texts, autotexts = ax.pie(
            grouped.values,
            labels=grouped.index.astype(str),
            autopct="%1.1f%%",
            colors=PALETTE[:len(grouped)],
            pctdistance=0.8,
            wedgeprops={"edgecolor":BG_COLOR,"linewidth":1.5}
        )

        for t in texts:
            t.set_color(TEXT_COLOR)
            t.set_fontsize(9)

        for at in autotexts:
            at.set_color(BG_COLOR)
            at.set_fontsize(8)
            at.set_fontweight("bold")

        ax.set_title(
            f"{num_col} Share by {cat_col}",
            fontsize=11,
            fontweight="bold",
            color=TEXT_COLOR
        )

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(CARD_COLOR)

        fig.tight_layout()

        return [{
            "title":f"{num_col} Share by {cat_col}",
            "image":_fig_to_b64(fig)
        }]