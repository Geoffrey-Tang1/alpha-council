import numpy as np
import pandas as pd

from app.agents.base import BaseAgent
from app.core.constants import AgentSignal
from app.schemas.agents import TechnicalAnalysisOutput


class TechnicalAnalysisAgent(BaseAgent):
    name = "technical_analysis"

    def analyze(self, collected_data: dict) -> TechnicalAnalysisOutput:
        history: pd.DataFrame = collected_data["price_history"]
        if history.empty or "close" not in history:
            return TechnicalAnalysisOutput(
                technical_signal=AgentSignal.WATCH,
                confidence=0.2,
                explanation="Price history is unavailable, so technical analysis is inconclusive.",
                key_indicators={},
                risks=["Missing price history."],
            )

        closes = history["close"].astype(float)
        returns = closes.pct_change().dropna()
        sma_20 = float(closes.rolling(20).mean().iloc[-1]) if len(closes) >= 20 else None
        sma_50 = float(closes.rolling(50).mean().iloc[-1]) if len(closes) >= 50 else None
        rsi_14 = self._rsi(closes, period=14)
        macd = self._macd(closes)
        volatility_20d = float(returns.tail(20).std() * np.sqrt(252)) if len(returns) >= 20 else None

        risks: list[str] = []
        if len(closes) < 50:
            risks.append("Price history is too short for full 20/50-day technical confirmation.")
        if volatility_20d is not None and volatility_20d > 0.35:
            risks.append("20-day annualized volatility is elevated.")
        if rsi_14 is not None and rsi_14 > 70:
            risks.append("RSI is overbought.")

        if sma_20 is None or sma_50 is None:
            signal = AgentSignal.WATCH
            explanation = "Price history is too short for a reliable technical signal."
            confidence = 0.3
        elif sma_20 > sma_50 and (rsi_14 or 50) < 72:
            signal = AgentSignal.BUY
            explanation = "Short-term trend is above the medium-term trend with acceptable momentum."
            confidence = 0.66
        elif sma_20 < sma_50:
            signal = AgentSignal.WATCH
            explanation = "Short-term trend is below the medium-term trend, so confirmation is weak."
            confidence = 0.52
        else:
            signal = AgentSignal.HOLD
            explanation = "Trend indicators are mixed and do not strongly favor action."
            confidence = 0.55

        return TechnicalAnalysisOutput(
            technical_signal=signal,
            confidence=confidence,
            explanation=explanation,
            key_indicators={
                "sma_20": round(sma_20, 2) if sma_20 is not None else None,
                "sma_50": round(sma_50, 2) if sma_50 is not None else None,
                "rsi_14": round(rsi_14, 2) if rsi_14 is not None else None,
                "macd": round(macd, 4) if macd is not None else None,
                "volatility_20d": round(volatility_20d, 4) if volatility_20d is not None else None,
            },
            risks=risks,
        )

    def _rsi(self, closes: pd.Series, period: int = 14) -> float | None:
        if len(closes) <= period:
            return None
        delta = closes.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        latest_loss = loss.iloc[-1]
        if latest_loss == 0:
            return 100.0
        rs = gain.iloc[-1] / latest_loss
        return float(100 - (100 / (1 + rs)))

    def _macd(self, closes: pd.Series) -> float | None:
        if len(closes) < 26:
            return None
        ema_12 = closes.ewm(span=12, adjust=False).mean()
        ema_26 = closes.ewm(span=26, adjust=False).mean()
        return float((ema_12 - ema_26).iloc[-1])
