from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import StringIO
import os
import uuid

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

import base64
from PIL import Image
from io import BytesIO

def convert_image_to_base64(image_path):
    with Image.open(image_path) as image:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes)
        img_base64_string = img_base64.decode("utf-8")
    return img_base64_string

@app.post("/get_image_for_text")
async def get_image_for_text(email,query,file: UploadFile = File(...)):
        print(file.filename)
        with open(email+".csv", "wb") as file_object:
            file_object.write(file.file.read())
        uuid1 = uuid.uuid1()
        llm = OpenAI(api_token=secret,save_charts=True)
        try:
            df = pd.read_csv(email+".csv") 
            sdf = SmartDataframe(df, config={"llm": llm})
            sdf.chat(query)
            image_path = "exports/charts/temp_chart.png"  # Replace with your image's path
            base64str = convert_image_to_base64(image_path)
            return {"id":str(uuid1),"image":base64str}
        except Exception as e:
            print(str(e))
            return "try again"
