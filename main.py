from fastapi import FastAPI
import logging
import routers

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 라우터 임포트
from routers import transcribe, labeling

app.include_router(transcribe.router, prefix="/transcribe", tags=["Transcription"])
app.include_router(labeling.router, prefix="/label", tags=["Labeling"])
