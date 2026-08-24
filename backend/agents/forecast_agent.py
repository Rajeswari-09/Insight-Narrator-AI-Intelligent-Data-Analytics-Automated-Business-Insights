import pandas as pd
from prophet import Prophet

class ForecastAgent:

    def run(self, df, date_col, value_col):

        data = df[[date_col, value_col]].dropna()

        data = data.rename(columns={
            date_col: "ds",
            value_col: "y"
        })

        model = Prophet()

        model.fit(data)

        future = model.make_future_dataframe(periods=30)

        forecast = model.predict(future)

        result = forecast[["ds", "yhat"]].tail(30)

        return result.to_dict(orient="records")
