from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import os
import io
import requests

app = FastAPI()


@app.on_event("startup")
@repeat_every(seconds=60 * 10)  # 1 hour
def refresh_the_api():
    
    url = "https://research-project-h4fb.onrender.com/refresh_api"
    
    payload = {}
    headers = {
      'accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    print(response.text)
    return response.text


@app.get("/test")
def read_root():
    return {"message":"running"}

