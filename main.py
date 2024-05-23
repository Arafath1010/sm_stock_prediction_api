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
        file_name = file.filename
        with open(email+file_name, "wb") as file_object:
            file_object.write(file.file.read())
        uuid1 = uuid.uuid1()
        llm = OpenAI(api_token=secret,save_charts=True)

        # Determine the file type and read accordingly
        if file_name.endswith('.csv'):
            df = pd.read_csv(email+file_name)
        elif file_name.endswith('.xls') or file_name.endswith('.xlsx'):
            df = pd.read_excel(email+file_name)
        else:
            return {"error": "Unsupported file type"}
            
        sdf = SmartDataframe(df, config={"llm": llm})
        sdf.chat(query)  

        code_to_exec = "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
        code_to_exec = code_to_exec + sdf.last_code_generated.replace("dfs[0]","dfs")
        code_to_exec = code_to_exec.replace("exports/charts/temp_chart.png",email+file_name+".png")
        code_to_exec = code_to_exec+f"\nplt.savefig('{email+file_name}.png')"
    
        print(code_to_exec)
        local_vars = {'dfs': df}
        exec(code_to_exec, globals(), local_vars)
        try:

            print(email+file_name+".png",df.head())
            
            return FileResponse(email+file_name+".png")
            
            image_path = "exports/charts/temp_chart.png"  # Replace with your image's path
            base64str = convert_image_to_base64(image_path)
            
            return {"id":str(uuid1),"image":base64str}
        except Exception as e:
            print(str(e))
            return "try again"
