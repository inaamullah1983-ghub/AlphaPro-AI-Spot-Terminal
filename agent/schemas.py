from pydantic import BaseModel
from typing import List, Dict


class AnalyzeRequest(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str = "1m"
    limit: int = 100


class KlinePoint(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class AnalyzeResponse(BaseModel):
    symbol: str
    interval: str
    klines: List[KlinePoint]
    summary: Dict[str, float]
