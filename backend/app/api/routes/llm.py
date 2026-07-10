from fastapi import APIRouter

from app.llm.model_catalog import get_provider_model_catalog, refresh_provider_model_catalog
from app.llm.provider_registry import get_llm_status
from app.llm.schemas import (
    LLMConnectionTestRequest,
    LLMConnectionTestResponse,
    LLMModelCatalogResponse,
    LLMModelRefreshRequest,
    LLMProviderName,
    LLMSettingsResponse,
    LLMSettingsUpdate,
    LLMStatusResponse,
)
from app.llm.settings_store import get_llm_settings_response, test_llm_connection, update_llm_settings

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/status", response_model=LLMStatusResponse)
def get_status() -> LLMStatusResponse:
    return get_llm_status()


@router.get("/settings", response_model=LLMSettingsResponse)
def get_settings() -> LLMSettingsResponse:
    return get_llm_settings_response()


@router.patch("/settings", response_model=LLMSettingsResponse)
def patch_settings(payload: LLMSettingsUpdate) -> LLMSettingsResponse:
    return update_llm_settings(payload)


@router.post("/test", response_model=LLMConnectionTestResponse)
def test_connection(payload: LLMConnectionTestRequest) -> LLMConnectionTestResponse:
    return test_llm_connection(payload)


@router.get("/models", response_model=LLMModelCatalogResponse)
def get_models(provider: LLMProviderName) -> LLMModelCatalogResponse:
    return get_provider_model_catalog(provider)


@router.post("/models/refresh", response_model=LLMModelCatalogResponse)
def refresh_models(payload: LLMModelRefreshRequest) -> LLMModelCatalogResponse:
    return refresh_provider_model_catalog(payload.provider)
