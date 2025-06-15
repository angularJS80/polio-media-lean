- FFMPEG 무거운 자원이 많아서 파이썬 API 코드에서 참조하는 자원은 Dockerfile에 내장함. 

docker build -t whisper-api .
docker run -it --rm \
-v $(pwd):/app \
-v /Users/admin/kurento-record:/recordings \
-p 8000:8000 \
whisper-api \
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
