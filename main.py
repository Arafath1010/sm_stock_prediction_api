from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from io import StringIO
import os
import uuid,requests
import data_collector as dc

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/get_image_for_text")
async def get_image_for_text(b_id:int,product_name:str):
    # main
    data,message = dc.get_data(b_id = b_id , product_name = product_name)
    
    if message=="done":
      # Summarize the sales count per month
      data['transaction_date'] = pd.to_datetime(data['transaction_date'])
      data.set_index('transaction_date', inplace=True)
      monthly_sales = data['sell_qty'].resample('M').sum().reset_index()
        
      full_trend,forecasted_value,rounded_value = dc.forecast(monthly_sales)
      print(full_trend,forecasted_value,rounded_value)
      return rounded_value