class DisabledExecutionProvider:
    """No live trading exists in Phase 1.

    This stub documents the future boundary for paper trading or broker adapters.
    It must not place real orders or connect to broker APIs.
    """

    def place_order(self, *args, **kwargs):
        raise NotImplementedError("Live trading is not implemented in the AlphaCouncil MVP.")
