from dataclasses import dataclass


@dataclass(frozen=True)
class PromptSpec:
    prompt_name: str
    prompt_version: str
    system_instructions: str


SAFETY_INSTRUCTIONS = (
    "Summarize deterministic AlphaCouncil evidence only. Do not provide chain-of-thought. "
    "Do not create executable orders. Do not claim guaranteed returns. Respect all Risk Manager vetoes."
)

PROMPTS: dict[str, PromptSpec] = {
    "bull_bear_summary": PromptSpec(
        prompt_name="bull_bear_summary_v1",
        prompt_version="v1",
        system_instructions=f"{SAFETY_INSTRUCTIONS} Produce a concise bull and bear synthesis.",
    ),
    "decision_memo": PromptSpec(
        prompt_name="decision_memo_v1",
        prompt_version="v1",
        system_instructions=f"{SAFETY_INSTRUCTIONS} Produce a concise decision memo.",
    ),
    "risk_explanation": PromptSpec(
        prompt_name="risk_explanation_v1",
        prompt_version="v1",
        system_instructions=f"{SAFETY_INSTRUCTIONS} Explain risk controls in plain language.",
    ),
    "research_report": PromptSpec(
        prompt_name="research_report_v1",
        prompt_version="v1",
        system_instructions=f"{SAFETY_INSTRUCTIONS} Produce a compact research report.",
    ),
}


def get_prompt(prompt_key: str) -> PromptSpec:
    return PROMPTS[prompt_key]
