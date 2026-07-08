import json
from datetime import datetime, timezone

from app.core.constants import DecisionAction, MarketCode
from app.data_providers.instrument_metadata import build_instrument_metadata
from app.db.database import get_connection, initialize_database
from app.schemas.evaluations import DecisionEvaluationResponse, DirectionalResult


class EvaluationRepository:
    def __init__(self) -> None:
        initialize_database()

    def save(self, evaluation: DecisionEvaluationResponse) -> DecisionEvaluationResponse:
        payload = evaluation.model_dump(mode="json")
        now = datetime.now(timezone.utc).isoformat()

        with get_connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO decision_evaluations (
                    evaluation_id,
                    decision_id,
                    ticker,
                    company_name,
                    normalized_ticker,
                    display_symbol,
                    market,
                    decision,
                    confidence,
                    decision_timestamp,
                    decision_price,
                    evaluation_status,
                    forward_return_1d,
                    forward_return_5d,
                    forward_return_20d,
                    forward_return_60d,
                    max_drawdown_20d,
                    max_drawdown_60d,
                    max_runup_20d,
                    max_runup_60d,
                    directional_result,
                    evaluation_summary,
                    data_provider,
                    data_quality,
                    data_disclaimer,
                    data_warnings_json,
                    full_payload_json,
                    evaluated_at,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evaluation.evaluation_id,
                    evaluation.decision_id,
                    evaluation.ticker,
                    evaluation.company_name,
                    evaluation.normalized_ticker,
                    evaluation.display_symbol,
                    evaluation.market.value,
                    evaluation.decision.value,
                    evaluation.confidence,
                    evaluation.decision_timestamp,
                    evaluation.decision_price,
                    evaluation.evaluation_status.value,
                    evaluation.forward_return_1d,
                    evaluation.forward_return_5d,
                    evaluation.forward_return_20d,
                    evaluation.forward_return_60d,
                    evaluation.max_drawdown_20d,
                    evaluation.max_drawdown_60d,
                    evaluation.max_runup_20d,
                    evaluation.max_runup_60d,
                    evaluation.directional_result.value,
                    evaluation.evaluation_summary,
                    evaluation.data_provider,
                    evaluation.data_quality,
                    evaluation.data_disclaimer,
                    json.dumps(evaluation.data_warnings),
                    json.dumps(payload),
                    evaluation.evaluated_at,
                    now,
                ),
            )
            connection.commit()

        return evaluation

    def list(
        self,
        ticker: str | None = None,
        market: MarketCode | None = None,
        decision: DecisionAction | None = None,
        directional_result: DirectionalResult | None = None,
        min_confidence: float | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DecisionEvaluationResponse], int]:
        where_clauses: list[str] = []
        params: list[object] = []

        if ticker:
            where_clauses.append("ticker = ?")
            params.append(ticker.upper())
        if market:
            where_clauses.append("market = ?")
            params.append(market.value)
        if decision:
            where_clauses.append("decision = ?")
            params.append(decision.value)
        if directional_result:
            where_clauses.append("directional_result = ?")
            params.append(directional_result.value)
        if min_confidence is not None:
            where_clauses.append("confidence >= ?")
            params.append(min_confidence)
        if start_date:
            where_clauses.append("decision_timestamp >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("decision_timestamp <= ?")
            params.append(end_date)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        with get_connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM decision_evaluations {where_sql}",
                params,
            ).fetchone()["count"]
            rows = connection.execute(
                f"""
                SELECT full_payload_json
                FROM decision_evaluations
                {where_sql}
                ORDER BY evaluated_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()

        return [self._payload_to_evaluation(row["full_payload_json"]) for row in rows], total

    def list_all(self) -> list[DecisionEvaluationResponse]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT full_payload_json
                FROM decision_evaluations
                ORDER BY evaluated_at DESC
                """
            ).fetchall()
        return [self._payload_to_evaluation(row["full_payload_json"]) for row in rows]

    def get_by_id(self, evaluation_id: str) -> DecisionEvaluationResponse | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT full_payload_json
                FROM decision_evaluations
                WHERE evaluation_id = ?
                """,
                (evaluation_id,),
            ).fetchone()

        if row is None:
            return None
        return self._payload_to_evaluation(row["full_payload_json"])

    def get_latest_for_decision(self, decision_id: str) -> DecisionEvaluationResponse | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT full_payload_json
                FROM decision_evaluations
                WHERE decision_id = ?
                ORDER BY evaluated_at DESC
                LIMIT 1
                """,
                (decision_id,),
            ).fetchone()

        if row is None:
            return None
        return self._payload_to_evaluation(row["full_payload_json"])

    def _payload_to_evaluation(self, raw_payload: str) -> DecisionEvaluationResponse:
        payload = json.loads(raw_payload)
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
        return DecisionEvaluationResponse.model_validate(payload)
