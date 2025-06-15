import os
import uuid
import tensorflow as tf
import cv2
import numpy as np
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from models import LabelingRequest

router = APIRouter()
VIDEO_DIR = "/recordings"

jobs = {}  # job_id 별 상태 저장 (필요 시 DB 등으로 대체 가능)

def extract_video_segment_frames(video_path, start_time, end_time, target_size=(224, 224)):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("영상 파일을 열 수 없습니다.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    start_frame = int(fps * start_time)
    end_frame = min(int(fps * end_time), total_frames - 1)

    frames = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    for frame_idx in range(start_frame, end_frame + 1):
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, target_size)
        frames.append(frame)

        logging.info(f"Extracting frame {frame_idx} / {end_frame}, collected frames: {len(frames)}")

    cap.release()
    return np.array(frames)


def train_segment_task(job_id: str, req: LabelingRequest):
    video_path = os.path.join(VIDEO_DIR, req.filename)
    try:
        frames = extract_video_segment_frames(video_path, req.start_time, req.end_time)
        if len(frames) == 0:
            jobs[job_id] = {"status": "failed", "detail": "해당 구간에서 프레임을 추출하지 못했습니다."}
            return

        input_tensor = tf.convert_to_tensor(frames / 255.0, dtype=tf.float32)
        input_tensor = tf.expand_dims(input_tensor, axis=0)

        # TODO: 모델 학습/추론 수행
        # predictions = model.predict(input_tensor)

        # 단순하게 프레임 평균으로 하나의 이미지로 축소 (예시)
        avg_frame = tf.reduce_mean(input_tensor, axis=0)  # shape: (H, W, C)

        training_data = []
        training_labels = []

        training_data.append(avg_frame.numpy())  # numpy로 변환 후 저장
        training_labels.append(req.label)  # 정수 인코딩된 라벨 추가
        train_model(training_data, training_labels)
        logging.info(f"Train segment with label '{req.label}' processed for video {req.filename}")
        jobs[job_id] = {"status": "completed", "frames_count": len(frames)}

    except Exception as e:
        logging.error(f"Training task failed: {e}")
        jobs[job_id] = {"status": "failed", "detail": str(e)}

def train_model(training_data, training_labels):
    X = np.array(training_data)
    y = np.array(training_labels)

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(224, 224, 3)),  # 예시 이미지 크기
        tf.keras.layers.Conv2D(16, 3, activation='relu'),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(32, 3, activation='relu'),
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(len(training_labels), activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=10)

    model.save("my_model")  # SavedModel 형식 저장

@router.post("/train_segment")
def train_segment(req: LabelingRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}

    background_tasks.add_task(train_segment_task, job_id, req)

    return {"job_id": job_id, "status": "processing"}
