docker build -t whisper-api .
docker run -it --rm \
-v $(pwd):/app \
-v /Users/admin/kurento-record:/recordings \
-p 8000:8000 \
whisper-api \
uvicorn main:app --host 0.0.0.0 --port 8000 --reload