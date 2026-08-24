"""
analyzer.py — Analyzer Agent
Performs deep statistical analysis on a DataFrame and returns a structured insights dict.
No LLM required — uses pandas, numpy, and scipy.
"""
import numpy as np
import pandas as pd
from scipy import stats
from backend.utils.data_utils import classify_columns


class AnalyzerAgent:
    """
    Agentic Analyzer: extracts comprehensive insights from a DataFrame.
    """

    def run(self, df: pd.DataFrame) -> dict:
        col_types = classify_columns(df)
        insights = {
            "overview": self._overview(df, col_types),
            "descriptive_stats": self._descriptive_stats(df, col_types),
            "missing_values": self._missing_values(df),
            "correlations": self._correlations(df, col_types),
            "trends": self._trends(df, col_types),
            "outliers": self._outliers(df, col_types),
            "categorical_summary": self._categorical_summary(df, col_types),
            "top_insights": [],  # Filled at the end
            "col_types": col_types,
        }
        insights["top_insights"] = self._derive_top_insights(insights)
        return insights

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _overview(self, df: pd.DataFrame, col_types: dict) -> dict:
        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": df.columns.tolist(),
            "numeric_count": len(col_types["numeric"]),
            "categorical_count": len(col_types["categorical"]),
            "datetime_count": len(col_types["datetime"]),
            "total_missing": int(df.isnull().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        }

    def _descriptive_stats(self, df: pd.DataFrame, col_types: dict) -> dict:
        stats_dict = {}
        for col in col_types["numeric"]:
            series = df[col].dropna()
            if len(series) == 0:
                continue
            stats_dict[col] = {
                "mean": round(float(series.mean()), 4),
                "median": round(float(series.median()), 4),
                "std": round(float(series.std()), 4),
                "min": round(float(series.min()), 4),
                "max": round(float(series.max()), 4),
                "q1": round(float(series.quantile(0.25)), 4),
                "q3": round(float(series.quantile(0.75)), 4),
                "skewness": round(float(stats.skew(series)), 4),
                "kurtosis": round(float(stats.kurtosis(series)), 4),
            }
        return stats_dict

    def _missing_values(self, df: pd.DataFrame) -> dict:
        missing = df.isnull().sum()
        pct = (missing / len(df) * 100).round(2)
        return {
            col: {"count": int(missing[col]), "pct": float(pct[col])}
            for col in df.columns
            if missing[col] > 0
        }

    def _correlations(self, df: pd.DataFrame, col_types: dict) -> dict:
        numeric_df = df[col_types["numeric"]].dropna()
        if len(col_types["numeric"]) < 2 or len(numeric_df) < 3:
            return {}
        corr_matrix = numeric_df.corr().round(3)
        # Extract top correlating pairs (excluding self-correlation)
        pairs = []
        cols = corr_matrix.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr_matrix.iloc[i, j]
                pairs.append({"col_a": cols[i], "col_b": cols[j], "r": round(float(val), 3)})
        pairs_sorted = sorted(pairs, key=lambda x: abs(x["r"]), reverse=True)
        return {
            "matrix": corr_matrix.to_dict(),
            "top_pairs": pairs_sorted[:5],
        }

    def _trends(self, df: pd.DataFrame, col_types: dict) -> dict:
        trends = {}
        if not col_types["datetime"]:
            return trends

        date_col = col_types["datetime"][0]
        df_sorted = df.sort_values(date_col).copy()
        # Convert dates to numeric for regression
        date_numeric = (
            (df_sorted[date_col] - df_sorted[date_col].min())
            .dt.total_seconds()
            .values
        )

        for num_col in col_types["numeric"]:
            series = df_sorted[num_col].dropna()
            if len(series) < 5:
                continue
            x = date_numeric[: len(series)]
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, series.values)
            # Normalise slope to "per month" (approx 30 days)
            slope_per_month = slope * 60 * 60 * 24 * 30
            direction = "upward" if slope > 0 else "downward"
            trends[num_col] = {
                "slope_per_month": round(float(slope_per_month), 4),
                "direction": direction,
                "r_squared": round(float(r_value ** 2), 4),
                "p_value": round(float(p_value), 6),
                "significant": bool(p_value < 0.05),
            }
        return trends

    def _outliers(self, df: pd.DataFrame, col_types: dict) -> dict:
        outlier_report = {}
        for col in col_types["numeric"]:
            series = df[col].dropna()
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = series[(series < lower) | (series > upper)]
            if len(outliers) > 0:
                outlier_report[col] = {
                    "count": int(len(outliers)),
                    "lower_bound": round(float(lower), 4),
                    "upper_bound": round(float(upper), 4),
                    "values": [round(float(v), 4) for v in outliers.values[:10]],
                }
        return outlier_report

    def _categorical_summary(self, df: pd.DataFrame, col_types: dict) -> dict:
        summary = {}
        for col in col_types["categorical"]:
            vc = df[col].value_counts()
            summary[col] = {
                "unique_count": int(df[col].nunique()),
                "top_categories": {str(k): int(v) for k, v in vc.head(5).items()},
                "mode": str(vc.index[0]) if len(vc) > 0 else None,
            }
        return summary

    def _derive_top_insights(self, insights: dict) -> list:
        """Derive top 5 human-readable bullet-point insights from analysis."""
        top = []

        # Trend insight
        for col, trend in insights.get("trends", {}).items():
            if trend["significant"]:
                direction = trend["direction"]
                monthly = abs(trend["slope_per_month"])
                top.append(
                    f"📈 **{col}** shows a strong **{direction} trend** "
                    f"(~{monthly:,.2f} per month, R²={trend['r_squared']:.2f})"
                )
                if len(top) >= 2:
                    break

        # Correlation insight
        top_pairs = insights.get("correlations", {}).get("top_pairs", [])
        if top_pairs:
            p = top_pairs[0]
            r = p["r"]
            strength = "strong" if abs(r) > 0.7 else "moderate"
            top.append(
                f"🔗 **{p['col_a']}** and **{p['col_b']}** have a {strength} "
                f"{'positive' if r > 0 else 'negative'} correlation (r={r:.2f})"
            )

        # Outlier insight
        for col, outlier_info in insights.get("outliers", {}).items():
            count = outlier_info["count"]
            top.append(f"⚠️ **{col}** has **{count} outlier(s)** detected via the IQR method")
            break

        # Top category insight
        for col, cat_info in insights.get("categorical_summary", {}).items():
            mode = cat_info["mode"]
            uc = cat_info["unique_count"]
            top.append(f"🏆 In **{col}**, the dominant value is **'{mode}'** across {uc} unique categories")
            break

        return top[:5]
