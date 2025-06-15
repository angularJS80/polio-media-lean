from fastapi import APIRouter, BackgroundTasks, HTTPException
import whisper
import os
import uuid
import logging
from models import TranscribeRequest

router = APIRouter()
model = whisper.load_model("base")
AUDIO_DIR = "/recordings"
jobs = {}

def transcribe_task(job_id: str, audio_path: str):
    result = model.transcribe(audio_path, word_timestamps=True)
    segments = []
    for segment in result["segments"]:
        logging.info(f"[Segment] {segment['start']}s - {segment['end']}s:\n{segment['text']}\n")
        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"]
        })
    jobs[job_id] = {
        "filename": os.path.basename(audio_path),
        "segments": segments,
        "full_text": result["text"],
        "status": "completed"
    }

@router.post("/")
def transcribe_audio(req: TranscribeRequest, background_tasks: BackgroundTasks):
    audio_path = os.path.join(AUDIO_DIR, req.filename)
    if not os.path.isfile(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(transcribe_task, job_id, audio_path)

    return {"job_id": job_id, "status": "processing"}
