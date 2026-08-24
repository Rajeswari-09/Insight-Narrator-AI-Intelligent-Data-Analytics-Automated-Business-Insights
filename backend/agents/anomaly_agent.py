import pandas as pd
from sklearn.ensemble import IsolationForest

class AnomalyAgent:

    def run(self, df, value_col):

        data = df[[value_col]].dropna()

        model = IsolationForest(contamination=0.05)

        data["anomaly_score"] = model.fit_predict(data)

        anomalies = data[data["anomaly_score"] == -1]

        return anomalies.head(10).to_dict(orient="records")
