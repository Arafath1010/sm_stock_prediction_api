from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import os
import io
temp = open("t.txt","w")
temp.write("aaaaaaaaaaaaa")
temp.close()

temp = open("t.txt","r")

app = FastAPI()




@app.get("/sample")
def read_root():
    return {"message": str(temp.read())}

