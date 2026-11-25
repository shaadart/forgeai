"""Every structure that crosses a stage boundary or comes back from a model."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CAPABILITIES = ("retrieval", "lookup_rows", "arithmetic", "today", "live_weather")
SECTIONS = (
    "role",
    "scope",
    "audience_and_tone",
    "grounding_rules",
    "refusal_policy",
    "clarification_policy",
    "citation_rules",
    "tool_rules",
    "conflict_policy",
)
DEFAULT_REFERRAL = "your manager or the responsible department"
BOUNDS = {
    "top_k": (3, 12),
    "chunk_size": (200, 1000),
    "chunk_overlap": (0, 150),
    "bm25_weight": (0.0, 1.0),
    "min_score": (0.0, 0.5),
}
OUTPUT_CONTRACT = {
    "status": "answered | refused | needs_clarification",
    "answer": "string",
    "citations": [{"chunk_id": "string", "quote": "string"}],
    "clarifying_question": "string or null",
}

Status = Literal["answered", "refused", "needs_clarification"]
Behavior = Literal["answer", "refuse", "clarify"]
State = Literal["passed", "failed", "unknown"]


class Chunk(BaseModel):
    chunk_id: str
    doc: str
    text: str


# --- intake and groundability ---


class Question(BaseModel):
    id: str
    question: str
    why_it_matters: str = ""
    trigger: str
    default_answer: str


class Questions(BaseModel):
    questions: list[Question]


class Topic(BaseModel):
    id: str
    topic: str
    example_question: str
    capabilities: list[str] = []
    scope_note: str = ""


class RefuseTopic(BaseModel):
    id: str
    topic: str
    reason: str = ""
    referral: str = DEFAULT_REFERRAL


class Assumption(BaseModel):
    text: str
    from_question: str = ""


class Requirements(BaseModel):
    scope: str
    audience: str
    tone: str
    must_answer: list[Topic]
    must_refuse: list[RefuseTopic] = []
    assumptions: list[Assumption] = []


class Quote(BaseModel):
    chunk_id: str
    quote: str

    @field_validator("chunk_id")
    @classmethod
    def _bare_id(cls, value):
        return value.strip("[] ")  # small models copy the brackets from the context


class Groundability(BaseModel):
    topic_id: str = ""
    verdict: Literal["supported", "partial", "unsupported"]
    evidence: list[Quote] = []
    missing: str = ""
    confidence: Literal["high", "low"] = "high"


# --- agent definition ---


class ToolChoice(BaseModel):
    name: str
    topic_ids: list[str] = []
    why: str = ""


class GeneratedAgent(BaseModel):
    name: str
    system_prompt: dict[str, str]
    tools: list[ToolChoice] = []
    refusal_message: str

    @field_validator("system_prompt", mode="before")
    @classmethod
    def _join_rule_lists(cls, value):
        if isinstance(value, dict):  # some models send each section as a list of rules
            return {k: "\n".join(map(str, v)) if isinstance(v, list) else v for k, v in value.items()}
        return value

    @field_validator("system_prompt")
    @classmethod
    def _all_sections(cls, value):
        missing = [s for s in SECTIONS if s not in value]
        if missing:
            raise ValueError(f"system_prompt is missing sections: {', '.join(missing)}")
        return value


class Retrieval(BaseModel):
    top_k: int = Field(5, ge=BOUNDS["top_k"][0], le=BOUNDS["top_k"][1])
    chunk_size: int = Field(500, ge=BOUNDS["chunk_size"][0], le=BOUNDS["chunk_size"][1])
    chunk_overlap: int = Field(50, ge=BOUNDS["chunk_overlap"][0], le=BOUNDS["chunk_overlap"][1])
    bm25_weight: float = Field(0.4, ge=0, le=1)
    min_score: float = Field(0.0, ge=0, le=BOUNDS["min_score"][1])


class AgentDef(BaseModel):
    name: str
    version: int = 0
    docs_dir: str
    documents: dict[str, str]  # file name -> sha256
    system_prompt: dict[str, str]
    retrieval: Retrieval = Retrieval()
    tools: list[ToolChoice] = []
    refusal_message: str
    output_contract: dict = OUTPUT_CONTRACT


# --- runtime ---


class Reply(BaseModel):
    status: Status
    answer: str = ""
    citations: list[Quote] = []
    clarifying_question: str | None = None


class ToolCall(BaseModel):
    name: str
    args: dict = {}
    result: str
    ok: bool
    chunks: list[Chunk] = []


class Turn(Reply):
    retrieved: list[Chunk] = []
    tool_calls: list[ToolCall] = []
    contract_valid: bool = True

    @property
    def text(self) -> str:
        """Everything the user reads."""
        return "\n".join(p for p in (self.answer, self.clarifying_question) if p)


# --- eval set ---


class KeyFact(BaseModel):
    id: str = ""
    fact: str
    quote: str | None = None
    chunk_id: str | None = None
    derived: str | None = None


class Interpretation(BaseModel):
    reading: str = ""
    chunk_id: str = ""


class RawCase(BaseModel):
    question: str
    expected_behavior: Behavior
    key_facts: list[KeyFact] = []
    source_chunk_ids: list[str] = []
    near_chunk_id: str | None = None
    why_unanswerable: str = ""
    interpretations: list[Interpretation] = []
    expected_tools: list[str] = []


class RawCases(BaseModel):
    cases: list[dict]  # validated one by one, so one bad case does not sink the batch

    @model_validator(mode="before")
    @classmethod
    def _bare_list(cls, value):
        if isinstance(value, dict) and "question" in value and "cases" not in value:
            return {"cases": [value]}
        return {"cases": value} if isinstance(value, list) else value


class Case(BaseModel):
    id: str
    category: str
    question: str
    expected_behavior: Behavior
    key_facts: list[KeyFact] = []
    source_chunks: list[Chunk] = []
    expected_tools: list[str] = []
    why_unanswerable: str = ""
    flags: list[str] = []


# --- judging, diagnosis, fixing ---


class Claim(BaseModel):
    claim: str
    verdict: Literal["supported", "unsupported", "contradicted"]
    evidence_id: str | None = None

    @field_validator("evidence_id", mode="before")
    @classmethod
    def _one_string(cls, value):
        return ", ".join(map(str, value)) or None if isinstance(value, list) else value


class FactLabel(BaseModel):
    id: str
    verdict: Literal["present", "partial", "absent"]


class Labels(BaseModel):
    claims: list[Claim]
    key_facts: list[FactLabel]
    is_refusal: bool
    asks_clarification: bool


class Result(BaseModel):
    case_id: str
    state: State
    turn: Turn
    reasons: list[str] = []
    contract_valid: bool = True
    gold_in_topk: bool | None = None
    gold_rank: int | None = None
    unsupported: list[str] = []
    contradicted: list[str] = []
    missing_facts: list[str] = []
    facts_present: bool = False
    number_flag: bool = False
    shuffle_disagree: bool = False
    number_disagree: bool = False
    answer_words: int = 0


class Diagnosis(BaseModel):
    category: str
    subtype: str
    fix_target: str = ""
    evidence: str = ""
    hypothesis: str = ""


class PatchOp(BaseModel):
    op: Literal["set", "append_rule", "replace_sentence"]
    path: str
    value: Any = None
    old: str | None = None
    new: str | None = None


class Patch(BaseModel):
    rationale: str = ""
    addresses: list[str] = []
    ops: list[PatchOp]
    expected_effect: str = ""
    risk: str = ""


class Prose(BaseModel):
    summary: str
    what_still_fails: str
    why_by_category: str
    pipeline_doubts: str
    next_fixes: str
