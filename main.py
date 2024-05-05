from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi_utils.tasks import repeat_every
import os
import io
import requests

app = FastAPI()


@app.on_event("startup")
@repeat_every(seconds=60 * 12)  # 1 hour
async def refresh_the_api():
    
    url = "https://research-project-h4fb.onrender.com/refresh_api"
    
    payload = {}
    headers = {
      'accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    print(response.text)
    return response.text


@app.get("/test")
async def read_root():
    return {"message":"running"}
    

@app.get("/start_model_trigger")
async def model_trigger(page:str):
    while True:
        page = str(page)
        url = "https://api-ai-service.transexpress.lk/trigger_the_data_fecher?page="+page+"&paginate=10000"
        print(url,page)
        
        payload = {}
        headers = {
          'accept': 'application/json'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        
        print(response.text)

        page = int(page)
        page = page + 1


