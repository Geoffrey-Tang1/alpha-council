import json
from datetime import datetime, timezone

from app.data_providers.instrument_metadata import build_instrument_metadata
from app.db.database import get_connection, initialize_database
from app.schemas.decisions import DecisionResponse


class DecisionRepository:
    def __init__(self) -> None:
        initialize_database()

    def save(self, decision: DecisionResponse) -> DecisionResponse:
        payload = decision.model_dump(mode="json")
        payload = self._normalize_legacy_payload(payload)
        payload["saved"] = True
        saved_decision = DecisionResponse.model_validate(payload)
        now = datetime.now(timezone.utc).isoformat()

        with get_connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO decisions (
                    decision_id,
                    timestamp,
                    ticker,
                    company_name,
                    normalized_ticker,
                    display_symbol,
                    market,
                    latest_price,
                    market_status,
                    final_decision,
                    confidence,
                    time_horizon,
                    full_payload_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    saved_decision.decision_id,
                    saved_decision.timestamp,
                    saved_decision.ticker,
                    saved_decision.company_name,
                    saved_decision.normalized_ticker,
                    saved_decision.display_symbol,
                    saved_decision.market.value,
                    saved_decision.latest_price,
                    saved_decision.market_status.value,
                    saved_decision.decision.value,
                    saved_decision.confidence,
                    saved_decision.time_horizon,
                    json.dumps(saved_decision.model_dump(mode="json")),
                    now,
                ),
            )
            connection.commit()

        return saved_decision

    def list(self, limit: int = 100) -> list[DecisionResponse]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT full_payload_json
                FROM decisions
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._payload_to_decision(row["full_payload_json"]) for row in rows]

    def get_by_id(self, decision_id: str) -> DecisionResponse | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT full_payload_json
                FROM decisions
                WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()

        if row is None:
            return None
        return self._payload_to_decision(row["full_payload_json"])

    def _payload_to_decision(self, raw_payload: str) -> DecisionResponse:
        payload = json.loads(raw_payload)
        return DecisionResponse.model_validate(self._normalize_legacy_payload(payload))

    def _normalize_legacy_payload(self, payload: dict) -> dict:
        metadata = build_instrument_metadata(
            ticker=payload.get("ticker", ""),
            market=payload.get("market", "US"),
            company_name=payload.get("company_name"),
        )
        payload["company_name"] = (
            metadata["company_name"]
            if payload.get("company_name") in {None, "", "Unknown Company"}
            else payload["company_name"]
        )
        payload["normalized_ticker"] = payload.get("normalized_ticker") or metadata["normalized_ticker"]
        payload["display_symbol"] = payload.get("display_symbol") or metadata["display_symbol"]

        if "data_disclaimer" not in payload:
            payload["data_disclaimer"] = "MVP Mode: using deterministic mock data. Not real market data."

        if "data_provider" not in payload:
            data_sources = payload.get("data_sources") or []
            source_provider = data_sources[0].get("name", "mock") if data_sources else "mock"
            payload["data_provider"] = "mock" if source_provider == "mock_provider" else source_provider

        legacy_quality = payload.get("data_quality")
        if isinstance(legacy_quality, dict):
            normalized_quality = str(legacy_quality.get("quality", "MOCK")).upper()
            payload["data_quality"] = "MOCK" if "MOCK" in normalized_quality else normalized_quality
            payload["data_warnings"] = legacy_quality.get("warnings", [])
        elif "data_quality" not in payload:
            payload["data_quality"] = "MOCK"

        if "data_warnings" not in payload:
            payload["data_warnings"] = [
                payload["data_disclaimer"],
                "Legacy payload did not store full Phase 3 data metadata.",
            ]

        if "agent_outputs" not in payload:
            payload["agent_outputs"] = self._legacy_agent_outputs(payload)

        payload.setdefault("llm_enabled", False)
        payload.setdefault("llm_provider", "disabled")
        payload.setdefault("llm_used", False)
        payload.setdefault("llm_warnings", [])
        payload.setdefault("llm_outputs", {})

        return payload

    def _legacy_agent_outputs(self, payload: dict) -> dict:
        legacy_explanation = "Legacy Phase 1 payload did not store this full agent output."
        legacy_risks = ["Legacy payload; inspect agent votes and final explanation for available context."]
        return {
            "technical_analysis": {
                "technical_signal": "WATCH",
                "confidence": payload.get("confidence", 0.5),
                "explanation": legacy_explanation,
                "key_indicators": {},
                "risks": legacy_risks,
            },
            "fundamental_analysis": {
                "fundamental_signal": "WATCH",
                "confidence": payload.get("confidence", 0.5),
                "explanation": legacy_explanation,
                "key_metrics": {},
                "risks": legacy_risks,
            },
            "news_sentiment": {
                "sentiment_signal": "WATCH",
                "confidence": payload.get("confidence", 0.5),
                "explanation": legacy_explanation,
                "catalysts": [],
                "risks": legacy_risks,
                "data_sources": ["legacy_payload"],
            },
            "macro_cross_market": {
                "macro_signal": "WATCH",
                "confidence": payload.get("confidence", 0.5),
                "explanation": legacy_explanation,
                "macro_factors": [],
                "risks": legacy_risks,
            },
            "risk_manager": {
                "risk_level": "UNKNOWN",
                "max_position_size_pct": payload.get("max_position_size_pct", 0),
                "stop_loss_required": True,
                "risk_warnings": payload.get("risk_warnings", legacy_risks),
                "veto": payload.get("decision") == "BUY" and payload.get("stop_loss") is None,
                "veto_reason": None,
                "confidence_adjustment": 0,
            },
            "portfolio_manager": {
                "portfolio_fit": "legacy_unknown",
                "recommended_position_size_pct": payload.get("max_position_size_pct", 0),
                "concentration_warning": None,
                "explanation": legacy_explanation,
            },
        }
