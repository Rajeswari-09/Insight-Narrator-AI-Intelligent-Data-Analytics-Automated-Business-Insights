"""
narrator.py — Narrator Agent
Generates a human-readable narrative story from the insights dict.
Primary: OpenAI GPT-4o (if OPENAI_API_KEY set in environment)
Fallback: Rule-based template engine (works with no API key)
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()


class NarratorAgent:
    """
    Agentic Narrator: turns raw insights into a compelling written story.
    """

    def run(self, insights: dict, dataset_name: str = "the dataset") -> dict:
        """
        Returns a dict:
        {
          "story": str,       # Full narrative
          "source": str,      # "openai" | "rule-based"
          "sections": [...]   # Named sections for structured display
        }
        """
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if api_key:
            try:
                return self._openai_narrator(insights, dataset_name, api_key)
            except Exception as e:
                print(f"[NarratorAgent] OpenAI call failed: {e}. Falling back to rule-based.")
        return self._rule_based_narrator(insights, dataset_name)

    # ------------------------------------------------------------------
    # OpenAI Path
    # ------------------------------------------------------------------

    def _openai_narrator(self, insights: dict, dataset_name: str, api_key: str) -> dict:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Build a compact summary of the insights for the prompt
        overview = insights.get("overview", {})
        trends   = insights.get("trends", {})
        corr     = insights.get("correlations", {}).get("top_pairs", [])
        outliers = insights.get("outliers", {})
        top_cats = insights.get("categorical_summary", {})
        stats    = insights.get("descriptive_stats", {})

        prompt = f"""You are a senior data analyst writing a compelling executive report.

Dataset: {dataset_name}
- Rows: {overview.get("rows")}, Columns: {overview.get("columns")}
- Numeric columns: {overview.get("numeric_count")}, Categorical: {overview.get("categorical_count")}
- Missing values: {overview.get("total_missing")}

Key trends detected:
{json.dumps(trends, indent=2)}

Top correlations:
{json.dumps(corr[:3], indent=2)}

Outliers detected:
{json.dumps(outliers, indent=2)}

Descriptive stats (means):
{json.dumps({k: v.get("mean") for k, v in stats.items()}, indent=2)}

Top categories:
{json.dumps({k: v.get("top_categories") for k, v in top_cats.items()}, indent=2)}

Write a clear, concise narrative report in 4 sections:
1. **Executive Summary** — 2-3 sentences overview
2. **Key Trends** — discuss the most significant trends found
3. **Notable Patterns** — correlations, category leaders, anomalies
4. **Recommendations** — 2-3 action items based on the data

Use markdown bold for key terms. Be specific with numbers. Keep it under 400 words.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7,
        )
        story = response.choices[0].message.content.strip()
        sections = self._parse_sections(story)
        return {"story": story, "source": "openai", "sections": sections}

    # ------------------------------------------------------------------
    # Rule-based Fallback
    # ------------------------------------------------------------------

    def _rule_based_narrator(self, insights: dict, dataset_name: str) -> dict:
        overview  = insights.get("overview", {})
        trends    = insights.get("trends", {})
        corr      = insights.get("correlations", {}).get("top_pairs", [])
        outliers  = insights.get("outliers", {})
        stats     = insights.get("descriptive_stats", {})
        cat_sum   = insights.get("categorical_summary", {})
        top_ins   = insights.get("top_insights", [])

        rows   = overview.get("rows", "N/A")
        cols   = overview.get("columns", "N/A")
        n_num  = overview.get("numeric_count", 0)
        n_cat  = overview.get("categorical_count", 0)
        missing = overview.get("total_missing", 0)

        sections = []

        # ── Section 1: Executive Summary ─────────────────────────────
        missing_note = (
            f" There are **{missing} missing values** that may need attention."
            if missing > 0 else " The dataset is complete with no missing values."
        )
        exec_summary = (
            f"This report analyses **{dataset_name}**, a dataset containing "
            f"**{rows:,} records** across **{cols} variables** "
            f"({n_num} numeric, {n_cat} categorical).{missing_note}"
        )
        sections.append({"title": "Executive Summary", "content": exec_summary})

        # ── Section 2: Key Trends ────────────────────────────────────
        trend_lines = []
        for col, t in trends.items():
            direction = t["direction"]
            slope = abs(t["slope_per_month"])
            r2 = t["r_squared"]
            sig = "statistically significant" if t["significant"] else "not statistically significant"
            trend_lines.append(
                f"- **{col}** exhibits a clear **{direction} trend** with an average change of "
                f"**{slope:,.2f} units per month** (R²={r2:.2f}, {sig})."
            )

        if trend_lines:
            trend_text = (
                "Time-series analysis reveals the following patterns:\n\n"
                + "\n".join(trend_lines)
            )
        else:
            trend_text = "No clear time-based trends were detected in this dataset."

        sections.append({"title": "Key Trends", "content": trend_text})

        # ── Section 3: Notable Patterns ──────────────────────────────
        pattern_lines = []

        if corr:
            top = corr[0]
            r = top["r"]
            strength = "strong" if abs(r) > 0.7 else "moderate"
            pattern_lines.append(
                f"- A **{strength} {'positive' if r > 0 else 'negative'} correlation** "
                f"(r={r:.2f}) exists between **{top['col_a']}** and **{top['col_b']}**."
            )

        if outliers:
            for col, o in outliers.items():
                pattern_lines.append(
                    f"- **{o['count']} outlier(s)** detected in **{col}** "
                    f"(expected range: {o['lower_bound']:,.2f} – {o['upper_bound']:,.2f})."
                )

        for col, cs in cat_sum.items():
            mode = cs.get("mode")
            uc   = cs.get("unique_count")
            if mode:
                pattern_lines.append(
                    f"- In the **{col}** dimension, **'{mode}'** is the most frequent category "
                    f"across {uc} unique values."
                )

        if stats:
            for col, s in list(stats.items())[:2]:
                pattern_lines.append(
                    f"- **{col}** ranges from {s['min']:,.2f} to {s['max']:,.2f}, "
                    f"with a mean of **{s['mean']:,.2f}** and std dev of {s['std']:,.2f}."
                )

        pattern_text = (
            "\n".join(pattern_lines)
            if pattern_lines
            else "No significant patterns were identified beyond normal variation."
        )
        sections.append({"title": "Notable Patterns & Correlations", "content": pattern_text})

        # ── Section 4: Recommendations ───────────────────────────────
        recs = []
        for col, t in trends.items():
            if t["direction"] == "upward" and t["significant"]:
                recs.append(
                    f"- **Capitalise on growth**: **{col}** is growing consistently — "
                    f"consider scaling resources or marketing efforts in this area."
                )
        if outliers:
            col = list(outliers.keys())[0]
            recs.append(
                f"- **Investigate outliers**: Review the {outliers[col]['count']} anomalous "
                f"records in **{col}** to determine if they represent data errors or extraordinary events."
            )
        if corr and abs(corr[0]["r"]) > 0.7:
            recs.append(
                f"- **Leverage correlation**: The high correlation between "
                f"**{corr[0]['col_a']}** and **{corr[0]['col_b']}** can be used for "
                f"predictive modelling or strategic planning."
            )
        if not recs:
            recs.append("- Continue regular monitoring of data quality and trends.")
            recs.append("- Consider enriching the dataset with additional variables for deeper analysis.")

        rec_text = "\n".join(recs)
        sections.append({"title": "Recommendations", "content": rec_text})

        # Assemble full story
        story_parts = [f"## {s['title']}\n\n{s['content']}" for s in sections]
        story = "\n\n---\n\n".join(story_parts)

        return {"story": story, "source": "rule-based", "sections": sections}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_sections(self, story: str) -> list:
        """Parse markdown sections from GPT response."""
        import re
        sections = []
        pattern = re.compile(r"##?\s+\*{0,2}(.*?)\*{0,2}\n+(.*?)(?=\n##|\Z)", re.DOTALL)
        for m in pattern.finditer(story):
            sections.append({"title": m.group(1).strip(), "content": m.group(2).strip()})
        if not sections:
            sections = [{"title": "Analysis", "content": story}]
        return sections
