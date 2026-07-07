class BaseAgent:
    name = "base_agent"

    def vote(self, signal, confidence: float):
        return {"agent": self.name, "vote": signal, "confidence": confidence}
