from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import data_collector as dc
import pandas as pd
from prophet import Prophet
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def forecast(monthly_sales):
    # Prepare the data for Prophet
    monthly_sales.rename(columns={'transaction_date': 'ds', 'sell_qty': 'y'}, inplace=True)

    # Initialize and fit the Prophet model
    model = Prophet()
    model.fit(monthly_sales)

    # Make a future dataframe for the next month
    future = model.make_future_dataframe(periods=1, freq='M')
    forecast = model.predict(future)

    # Extract the forecasted sales for the next month
    forecasted_sales = forecast[['ds', 'yhat']].tail(2)

    # Combine historical and forecasted data
    combined_sales = pd.concat([monthly_sales, forecasted_sales[-1:]], ignore_index=True)
    original_forecasted_value = combined_sales.tail(1)
    rounded_value = combined_sales.tail(1)

    rounded_value['yhat'] = rounded_value['yhat'].apply(lambda x: max(0, math.ceil(x)))

    return combined_sales, original_forecasted_value, rounded_value

def process_product(product_name, data):
    try:
        # Summarize the sales count per month
        data['transaction_date'] = pd.to_datetime(data['transaction_date'])
        data.set_index('transaction_date', inplace=True)
        monthly_sales = data['sell_qty'].resample('M').sum().reset_index()

        full_trend, forecasted_value, rounded_value = forecast(monthly_sales)
        rounded_value.columns = ["next_month", "y", "predicted_count"]
        # Convert to dictionary
        result_dict = rounded_value.to_dict(orient="records")[0]

        return {
            "Product Name": product_name,
            "next_month": str(result_dict["next_month"]),
            "predicted_count": result_dict["predicted_count"]
        }
    except Exception as e:
        return {
            "Product Name": product_name,
            "next_month": str(e),
            "predicted_count": "not predicted"
        }

@app.post("/get_product_count_prediction")
async def get_product_count_prediction(b_id: int):
    try:
        # main
        data, message = dc.get_data(b_id=b_id, product_name="sample")

        if message == "done":

            grouped_df = data.groupby('product_name')

            results = []
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_product, product_name, product_df.copy()) for product_name, product_df in grouped_df]
                for future in as_completed(futures):
                    results.append(future.result())

            response_content = {
                "status": "success",
                "message": "Prediction successful",
                "data": results
            }
            return JSONResponse(content=response_content, status_code=200)
            
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        print(str(e))
        response_content = {
            "status": "error",
            "message": str(e),
            "data": None
        }
        return JSONResponse(content=response_content, status_code=500)
