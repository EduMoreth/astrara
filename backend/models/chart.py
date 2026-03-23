from pydantic import BaseModel
from typing import Optional


class ChartRequest(BaseModel):
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    country: Optional[str] = None


class ChartSaveRequest(BaseModel):
    chart_id: str
