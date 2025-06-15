from pydantic import BaseModel, Field

class TranscribeRequest(BaseModel):
    filename: str

class LabelingRequest(BaseModel):
    filename: str = Field(..., description="동영상 파일명")
    start_time: float = Field(..., description="구간 시작 시간 (초)")
    end_time: float = Field(..., description="구간 종료 시간 (초)")
    label: str = Field(..., description="해당 구간에 부여할 라벨")
