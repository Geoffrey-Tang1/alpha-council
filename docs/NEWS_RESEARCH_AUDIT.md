# News and Research Source Audit

Phase 7.2 goal: Wisoka Compass must never invent news, article URLs, citations, publishers, or sentiment. Verified news and research sources are represented through a provider-neutral foundation. Missing sources are explicit unavailable states.

## Current Feature Audit

| Area | Files | Current status | Data type | URLs | Timestamps | Sentiment | LLM citation risk | Repair required | Test coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Legacy market provider news | `backend/app/data_providers/mock_provider.py`, `backend/app/data_providers/yfinance_provider.py` | Legacy compatibility only. `DataCollectorAgent` now converts the provider-neutral news snapshot into a legacy list for older call sites. | Mock or placeholder. yfinance news is no longer trusted as verified research evidence through this path. | No verified URLs used. | Legacy list has no source timestamps. | Legacy sentiment values are placeholders. | Low after Phase 7.2 because report evidence comes from `news_research`, not legacy headlines. | Keep for compatibility; do not treat as verified. | Covered indirectly by analysis and provider tests. |
| NewsSentimentAgent | `backend/app/agents/news_sentiment.py` | Uses `NewsSentimentSnapshot` when available. Returns unavailable when verified news is unavailable. | Provider-neutral snapshot. | Does not create URLs. | Uses snapshot `fetched_at`. | Disabled mode marks sentiment unavailable. Mock mode marks sentiment as mock deterministic, not real sentiment. | Low: explanations explicitly describe mock/unavailable status. | Maintain strict separation between mock and verified article evidence. | Added in Phase 7.2 tests. |
| Research pipeline evidence | `backend/app/services/research_pipeline_service.py` | Adds `news_research` evidence, unavailable verified-news evidence, and mock sentiment evidence when applicable. | Mock, unavailable, or future verified provider data. | Source references remain `null` unless a provider marks a URL verified. | Evidence includes fetched/observed timestamps from the snapshot. | Sentiment evidence is labeled mock or unavailable. | Low: LLM outputs remain `model_inference`, not external sources. | Future live providers must set `is_verified_url=true` only for validated public URLs. | Added in Phase 7.2 tests. |
| Structured Research Report | `frontend/src/components/analysis/StructuredResearchReport.jsx` | Shows a News / Research Sources section from structured evidence. | Evidence-derived. | Does not render clickable links unless future evidence supplies verified references. | Shows evidence metadata where present. | Shows mock/unavailable evidence badges. | Low: raw provider errors and LLM prose are not treated as citations. | Future UI can expand verified article details when real providers are added. | Frontend build verification. |
| Settings status | `frontend/src/pages/SettingsPage.jsx` | Adds read-only News & Research provider status. | Backend status endpoint. | N/A | Shows provider status fetch result only. | Shows whether sentiment is supported. | Low. | Keep financial and LLM settings separate. | Frontend build verification. |
| LLM research memo | `backend/app/llm/*`, `frontend/src/components/analysis/LLMResearchMemo.jsx` | Optional reasoning aid. It is not a source provider. | Model inference. | Must not create source URLs. | Prompt metadata only. | LLM may summarize but not create verified sentiment. | Managed by report evidence labeling and prompt safety text. | Continue rejecting provider output as external evidence unless backed by evidence IDs. | Existing LLM tests plus research pipeline tests. |

## Provider Strategy

Phase 7.2 implements:

- `DisabledNewsProvider`: default for non-mock data modes unless `NEWS_RESEARCH_PROVIDER=mock` is explicitly selected. It returns unavailable states and the message: `News provider is disabled. No verified news sources are available.`
- `MockNewsProvider`: deterministic offline provider used when `NEWS_RESEARCH_PROVIDER=mock`, or when `NEWS_RESEARCH_PROVIDER=auto` and `DATA_PROVIDER=mock`. It returns mock-only articles without real URLs and mock deterministic sentiment clearly labeled as not real.

Future providers such as RSS, GDELT, yfinance-derived news, OpenAlex, or vendor APIs must implement the provider-neutral contract before entering the research pipeline. They must not pass raw provider payloads or unverified URLs directly into evidence.

## Known Limitations

- No verified live news provider is connected by default.
- No real sentiment model is connected.
- No filings, earnings-call transcripts, analyst revision feeds, or macro news feeds are connected.
- Mock article titles are development-only and must not be interpreted as real headlines.
- Missing news remains visible as unavailable information, not as empty success.

