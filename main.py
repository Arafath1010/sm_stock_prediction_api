from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import data_collector as dc
import pandas as pd

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/get_product_count_prediction")
async def get_product_count_prediction(b_id: int):
    try:
        # main
        data, message = dc.get_data(b_id=b_id, product_name="sample")
        
        if message == "done":

            grouped_df = data.groupby('product_name')

            results = []
            for product_name, data in grouped_df:
                # Summarize the sales count per month
                data['transaction_date'] = pd.to_datetime(data['transaction_date'])
                data.set_index('transaction_date', inplace=True)
                monthly_sales = data['sell_qty'].resample('M').sum().reset_index()
                
                try:
                    full_trend, forecasted_value, rounded_value = forecast(monthly_sales)
                    rounded_value.columns = ["next_month", "y", "predicted_count"]
                    # Convert to dictionary
                    result_dict = rounded_value.to_dict(orient="records")[0]
                    #print(full_trend, forecasted_value, rounded_value)
                    results.append({
                                "Product Name" : product_name,
                                "next_month": str(result_dict["next_month"]),
                                "predicted_count": result_dict["predicted_count"]
                            })
                except Exception as e:
                    print(str(e))
                    results.append({
                                "Product Name" : product_name,
                                "next_month": str(e),
                                "predicted_count": "not predicted"
                            })
                    break      
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
