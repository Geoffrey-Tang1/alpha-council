from fastapi import APIRouter

from app.llm.provider_registry import get_llm_status
from app.llm.schemas import LLMStatusResponse

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/status", response_model=LLMStatusResponse)
def get_status() -> LLMStatusResponse:
    return get_llm_status()
