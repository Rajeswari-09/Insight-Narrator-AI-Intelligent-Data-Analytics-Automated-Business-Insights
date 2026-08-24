import time
from backend.agents.forecast_agent import ForecastAgent
from backend.agents.anomaly_agent import AnomalyAgent
from backend.agents.analyzer import AnalyzerAgent
from backend.agents.visualizer import VisualizerAgent
from backend.agents.narrator import NarratorAgent
from backend.utils.data_utils import classify_columns


class OrchestratorAgent:

    def __init__(self):
        # instantiate every agent used in the pipeline
        self.analyzer = AnalyzerAgent()
        self.visualizer = VisualizerAgent()
        self.narrator = NarratorAgent()
        self.forecaster = ForecastAgent()
        self.anomaly = AnomalyAgent()

    def run(self, df, dataset_name: str = "dataset"):
        """Execute the full analysis pipeline and return a consolidated result.

        Parameters
        ----------
        df : pandas.DataFrame
            The dataset to analyze.
        dataset_name : str, optional
            A human-readable name for the dataset (used by the narrator).
        """
        
        pipeline_log = []
        start_time_total = time.time()

        # first analyse the dataframe to produce insights and column types
        start_time = time.time()
        insights = self.analyzer.run(df)
        elapsed = round(time.time() - start_time, 2)
        pipeline_log.append({"agent": "Analyzer", "elapsed_s": elapsed})
        
        col_types = insights.get("col_types", classify_columns(df))

        start_time = time.time()
        charts = self.visualizer.run(df)
        elapsed = round(time.time() - start_time, 2)
        pipeline_log.append({"agent": "Visualizer", "elapsed_s": elapsed})

        results = {
            "insights": insights,
            "charts": charts,
        }

        # forecasting/anomaly detection only when appropriate columns exist
        if col_types.get("datetime") and col_types.get("numeric"):
            date_col = col_types["datetime"][0]
            value_col = col_types["numeric"][0]
            
            start_time = time.time()
            results["forecast"] = self.forecaster.run(df, date_col, value_col)
            elapsed = round(time.time() - start_time, 2)
            pipeline_log.append({"agent": "Forecaster", "elapsed_s": elapsed})
            
            start_time = time.time()
            results["anomalies"] = self.anomaly.run(df, value_col)
            elapsed = round(time.time() - start_time, 2)
            pipeline_log.append({"agent": "Anomaly", "elapsed_s": elapsed})

        # generate a narrative based on the insights
        start_time = time.time()
        results["narrative"] = self.narrator.run(insights, dataset_name)
        elapsed = round(time.time() - start_time, 2)
        pipeline_log.append({"agent": "Narrator", "elapsed_s": elapsed})

        results["pipeline_log"] = pipeline_log
        results["total_elapsed_s"] = round(time.time() - start_time_total, 2)

        return results
