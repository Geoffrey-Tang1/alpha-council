import json
from datetime import datetime, timezone

from app.db.database import get_connection, initialize_database
from app.schemas.decisions import DecisionResponse


class DecisionRepository:
    def __init__(self) -> None:
        initialize_database()

    def save(self, decision: DecisionResponse) -> DecisionResponse:
        payload = decision.model_dump(mode="json")
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
                    market,
                    latest_price,
                    market_status,
                    final_decision,
                    confidence,
                    time_horizon,
                    full_payload_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    saved_decision.decision_id,
                    saved_decision.timestamp,
                    saved_decision.ticker,
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

        return [DecisionResponse.model_validate(json.loads(row["full_payload_json"])) for row in rows]
