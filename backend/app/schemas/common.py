from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import DecisionAction, MarketCode, MarketStatus


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class DataSource(BaseModel):
    name: str
    type: str
    status: str


class DataQuality(BaseModel):
    provider: str
    is_mock: bool
    quality: str
    warnings: list[str]


class AgentVote(BaseModel):
    agent: str
    vote: DecisionAction
    confidence: float = Field(ge=0, le=1)


class TimestampedModel(BaseModel):
    timestamp: datetime


MarketCodeField = MarketCode
MarketStatusField = MarketStatus
