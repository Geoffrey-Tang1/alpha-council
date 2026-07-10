from app.agents.bear_case import BearCaseAgent
from app.agents.bull_case import BullCaseAgent
from app.agents.data_collector import DataCollectorAgent
from app.agents.decision_committee import DecisionCommitteeAgent
from app.agents.fundamental_analysis import FundamentalAnalysisAgent
from app.agents.macro_cross_market import MacroCrossMarketAgent
from app.agents.news_sentiment import NewsSentimentAgent
from app.agents.portfolio_manager import PortfolioManagerAgent
from app.agents.risk_manager import RiskManagerAgent
from app.agents.technical_analysis import TechnicalAnalysisAgent
from app.core.constants import DecisionAction
from app.data_providers.provider_registry import get_data_provider
from app.schemas.analysis import AnalysisRequest
from app.schemas.decisions import DecisionResponse
from app.services.decision_service import DecisionService
from app.services.llm_reasoning_service import LLMReasoningService
from app.services.research_pipeline_service import ResearchPipelineService


class AnalysisService:
    def __init__(self, decision_service: DecisionService | None = None) -> None:
        provider = get_data_provider()
        self.data_collector = DataCollectorAgent(provider=provider)
        self.technical_agent = TechnicalAnalysisAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()
        self.news_agent = NewsSentimentAgent()
        self.macro_agent = MacroCrossMarketAgent()
        self.bull_case_agent = BullCaseAgent()
        self.bear_case_agent = BearCaseAgent()
        self.risk_manager = RiskManagerAgent()
        self.portfolio_manager = PortfolioManagerAgent()
        self.decision_committee = DecisionCommitteeAgent()
        self.decision_service = decision_service or DecisionService()
        self.research_pipeline = ResearchPipelineService()

    def run_analysis(self, request: AnalysisRequest) -> DecisionResponse:
        collected = self.data_collector.collect(ticker=request.ticker, market=request.market)
        technical = self.technical_agent.analyze(collected)
        fundamental = self.fundamental_agent.analyze(collected)
        news = self.news_agent.analyze(collected)
        macro = self.macro_agent.analyze(collected)
        bull_case = self.bull_case_agent.analyze(technical, fundamental, news, macro)
        bear_case = self.bear_case_agent.analyze(technical, fundamental, news, macro)

        latest_price = collected.get("latest_price")
        proposed_stop_loss = round(latest_price * 0.95, 2) if latest_price else None
        risk = self.risk_manager.evaluate(
            collected_data=collected,
            technical=technical,
            proposed_decision=DecisionAction.BUY,
            proposed_stop_loss=proposed_stop_loss,
        )
        portfolio = self.portfolio_manager.evaluate(risk)
        decision = self.decision_committee.decide(
            collected_data=collected,
            time_horizon=request.time_horizon,
            technical=technical,
            fundamental=fundamental,
            news=news,
            macro=macro,
            bull_case=bull_case,
            bear_case=bear_case,
            risk=risk,
            portfolio=portfolio,
        )
        decision = LLMReasoningService().enrich_decision(decision)
        decision.research_report = self.research_pipeline.build_report(
            request=request,
            collected_data=collected,
            technical=technical,
            fundamental=fundamental,
            news=news,
            macro=macro,
            bull_case=bull_case,
            bear_case=bear_case,
            risk=risk,
            portfolio=portfolio,
            decision=decision,
        )
        return self.decision_service.save_decision(decision)
