from app.db.repositories.decision_repository import DecisionRepository
from app.schemas.decisions import DecisionListResponse, DecisionResponse


class DecisionService:
    def __init__(self, repository: DecisionRepository | None = None) -> None:
        self.repository = repository or DecisionRepository()

    def save_decision(self, decision: DecisionResponse) -> DecisionResponse:
        return self.repository.save(decision)

    def list_decisions(self, limit: int = 100) -> DecisionListResponse:
        items = self.repository.list(limit=limit)
        return DecisionListResponse(items=items, total=len(items))

    def get_decision(self, decision_id: str) -> DecisionResponse | None:
        return self.repository.get_by_id(decision_id)
