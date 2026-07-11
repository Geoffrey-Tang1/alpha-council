from datetime import date, datetime, timezone

from app.financial_data.schemas import DataAvailability, DataFreshness


def classify_quote_freshness(
    observed_at: str | None,
    *,
    delayed: bool,
    availability: DataAvailability,
) -> DataFreshness:
    if availability not in {DataAvailability.AVAILABLE, DataAvailability.PARTIAL}:
        return DataFreshness.UNAVAILABLE
    if not observed_at:
        return DataFreshness.UNKNOWN
    parsed = _parse_date_or_datetime(observed_at)
    if parsed is None:
        return DataFreshness.UNKNOWN
    age_days = (datetime.now(timezone.utc).date() - parsed).days
    if age_days > 5:
        return DataFreshness.STALE
    return DataFreshness.DELAYED if delayed else DataFreshness.CURRENT


def classify_history_freshness(last_date: str | None, availability: DataAvailability) -> DataFreshness:
    if availability not in {DataAvailability.AVAILABLE, DataAvailability.PARTIAL}:
        return DataFreshness.UNAVAILABLE
    if not last_date:
        return DataFreshness.UNKNOWN
    parsed = _parse_date_or_datetime(last_date)
    if parsed is None:
        return DataFreshness.UNKNOWN
    age_days = (datetime.now(timezone.utc).date() - parsed).days
    if age_days <= 5:
        return DataFreshness.CURRENT
    if age_days <= 15:
        return DataFreshness.STALE
    return DataFreshness.MATERIALLY_STALE


def classify_financial_period_freshness(period_end: str | None, availability: DataAvailability) -> DataFreshness:
    if availability not in {DataAvailability.AVAILABLE, DataAvailability.PARTIAL}:
        return DataFreshness.UNAVAILABLE
    if not period_end:
        return DataFreshness.UNKNOWN
    parsed = _parse_date_or_datetime(period_end)
    if parsed is None:
        return DataFreshness.UNKNOWN
    age_days = (datetime.now(timezone.utc).date() - parsed).days
    if age_days <= 460:
        return DataFreshness.CURRENT
    if age_days <= 730:
        return DataFreshness.STALE
    return DataFreshness.MATERIALLY_STALE


def _parse_date_or_datetime(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None

