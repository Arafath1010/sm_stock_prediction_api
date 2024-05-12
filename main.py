from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import StringIO
import os

from pandasai import SmartDataframe
import pandas as pd
from pandasai.llm import OpenAI


secret = os.environ["key"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/get_image_for_text")
async def get_image_for_text(email,query,file: UploadFile = File(...)):
        print(file.filename)
        with open(email+".csv", "wb") as file_object:
            file_object.write(file.file.read())
        llm = OpenAI(api_token=secret,save_charts=True)
        df = pd.read_csv(email+".csv") 
        sdf = SmartDataframe(df, config={"llm": llm})
        sdf.chat(query)
        image_path = "exports/charts/temp_chart.png"  # Replace with your image's path
        return FileResponse(image_path)
