from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from common_schema_models import (
    Domain,
    EngineName,
    FieldVoice,
    LoPASObservation,
    ProtocolResult,
    Results,
    Routing,
    EngineOutput,
    NextAction,
)
from feature_extraction_v02 import build_observation_with_classification_axes
from protocol_engine import ProtocolEngine
from lptm_e2e_minimal import (
    lopas_observation_to_lptm_input,
    run_lptm_minimal,
    decide_human_review,
)


# ============================================================
# Optional COCLI stub
# ============================================================

def run_cocli_stub(observation: LoPASObservation) -> EngineOutput:
    field_quality = observation.indicators.get("F")
    confidence = field_quality.confidence if field_quality and field_quality.confidence is not None else 0.5

    return EngineOutput(
        engine=EngineName.COCLI,
        states={"status": "stub"},
        indicators={},
        summary="COCLI stub executed",
        confidence=confidence,
    )


# ============================================================
# Engine selection
# ============================================================

def select_engines(observation: LoPASObservation) -> list[EngineName]:
    """
    v0.2:
    - engine_route があれば尊重
    - なければ ProtocolEngine を基本にしつつ、必要時のみ LPTM / COCLI を追加
    """
    if observation.engine_route:
        return observation.engine_route

    cls = observation.states.get("classification_class")

    if cls == "ESCALATE":
        return [EngineName.ProtocolEngine, EngineName.LPTM, EngineName.HumanReview]

    if cls in {"REVIEW", "UNKNOWN"}:
        return [EngineName.ProtocolEngine, EngineName.HumanReview]

    if observation.domain == Domain.geopolitics:
        return [EngineName.ProtocolEngine, EngineName.LPTM, EngineName.COCLI]

    return [EngineName.ProtocolEngine]


# ============================================================
# Classification-first routing
# ============================================================

def route_from_classification(observation: LoPASObservation) -> tuple[NextAction, EngineName, ProtocolResult]:
    cls = observation.states.get("classification_class", "REVIEW")
    reason = observation.states.get("classification_reason", "")
    conf = observation.states.get("classification_confidence", 0.5)

    if cls == "AUTO_OK":
        return (
            NextAction.route_to_protocol,
            EngineName.ProtocolEngine,
            ProtocolResult(
                status="auto",
                result=f"classification accepted: AUTO_OK ({reason})",
            ),
        )

    if cls == "IGNORE":
        return (
            NextAction.store_only,
            EngineName.ProtocolEngine,
            ProtocolResult(
                status="auto",
                result=f"classification stored: IGNORE ({reason})",
            ),
        )

    if cls == "ESCALATE":
        return (
            NextAction.route_to_human,
            EngineName.HumanReview,
            ProtocolResult(
                status="human",
                description=f"classification escalation: ESCALATE ({reason}) / confidence={conf}",
            ),
        )

    if cls == "UNKNOWN":
        return (
            NextAction.route_to_human,
            EngineName.HumanReview,
            ProtocolResult(
                status="unknown",
                description=f"classification unknown: UNKNOWN ({reason}) / confidence={conf}",
            ),
        )

    # REVIEW fallback
    return (
        NextAction.route_to_human,
        EngineName.HumanReview,
        ProtocolResult(
            status="human",
            description=f"classification review: REVIEW ({reason}) / confidence={conf}",
        ),
    )


# ============================================================
# Main orchestrator
# ============================================================

def orchestrate_observation(observation: LoPASObservation) -> LoPASObservation:
    """
    Common Schema observation -> classification-first routing -> optional engines
    """
    selected_engines = select_engines(observation)
    engine_outputs: list[EngineOutput] = []

    review_required = observation.meta.human_review_required
    review_reasons = []
    if observation.meta.review_reason:
        review_reasons.append(observation.meta.review_reason)

    # --------------------------------------------------------
    # First decision comes from classification core
    # --------------------------------------------------------
    next_action, fallback_engine, protocol_result = route_from_classification(observation)

    if next_action == NextAction.route_to_human:
        review_required = True
        if observation.states.get("classification_reason"):
            review_reasons.append(observation.states["classification_reason"])

    # --------------------------------------------------------
    # Optional LPTM route
    # Only run when explicitly selected and not IGNORE/store_only
    # --------------------------------------------------------
    if EngineName.LPTM in selected_engines and next_action != NextAction.store_only:
        lptm_input = lopas_observation_to_lptm_input(observation)
        lptm_output = run_lptm_minimal(lptm_input)
        review = decide_human_review(observation, lptm_output)

        if review["human_review_required"]:
            review_required = True
            review_reasons.extend(review["reasons"])
            next_action = NextAction.route_to_human
            fallback_engine = EngineName.HumanReview
            protocol_result = ProtocolResult(
                status="human",
                description=f"LPTM review required: layer={lptm_output.layer}, band={lptm_output.band}",
            )

        engine_outputs.append(
            EngineOutput(
                engine=EngineName.LPTM,
                states={
                    "layer": lptm_output.layer,
                    "band": lptm_output.band,
                    "status": "completed",
                },
                indicators={
                    "PST": {
                        "value": lptm_output.PST,
                        "unit": "score",
                        "scale_min": 0.0,
                        "scale_max": 1.0,
                        "kind": "derived",
                        "confidence": lptm_output.confidence,
                        "method": "run_lptm_minimal",
                    }
                },
                summary=lptm_output.notes,
                confidence=lptm_output.confidence,
            )
        )

    # --------------------------------------------------------
    # Optional COCLI route
    # --------------------------------------------------------
    if EngineName.COCLI in selected_engines and next_action != NextAction.store_only:
        cocli_out = run_cocli_stub(observation)
        engine_outputs.append(cocli_out)

    # --------------------------------------------------------
    # Always append classification output as engine trace
    # --------------------------------------------------------
    engine_outputs.insert(
        0,
        EngineOutput(
            engine=EngineName.FeatureExtraction,
            states={
                "classification_class": observation.states.get("classification_class"),
                "classification_reason": observation.states.get("classification_reason"),
            },
            indicators={
                k: v for k, v in observation.indicators.items()
                if k in {"K", "Q", "C", "S", "T", "F"}
            },
            summary="Classification Core v0.1 decision",
            confidence=observation.states.get("classification_confidence"),
        ),
    )

    # --------------------------------------------------------
    # Write routing + results back into observation
    # --------------------------------------------------------
    observation.routing = Routing(
        selected_engines=selected_engines,
        fallback_engine=fallback_engine,
        next_action=next_action,
    )

    observation.results = Results(
        engine_outputs=engine_outputs,
        protocol_result=protocol_result,
    )

    observation.meta.human_review_required = review_required
    if review_reasons:
        observation.meta.review_reason = ";".join(sorted(set(review_reasons)))

    return observation


# ============================================================
# End-to-end helper
# ============================================================

def orchestrate_field_voices(
    field_voices: list[FieldVoice],
    *,
    observation_id: str | None = None,
    timestamp: datetime | None = None,
    domain: Domain = Domain.geopolitics,
    requested_engines: list[EngineName] | None = None,
    summary: str | None = None,
    similar_case_score: float = 0.0,
    history_matches: int = 0,
    context_links: int | None = None,
    source_count: int | None = None,
    risk_flags: list[str] | None = None,
) -> LoPASObservation:
    """
    FieldVoice[] -> Classification Core v0.1 -> Orchestrator -> ProtocolEngine
    """
    observation = build_observation_with_classification_axes(
        field_voices=field_voices,
        observation_id=observation_id,
        timestamp=timestamp,
        domain=domain,
        requested_engines=requested_engines,
        summary=summary,
        similar_case_score=similar_case_score,
        history_matches=history_matches,
        context_links=context_links,
        source_count=source_count,
        risk_flags=risk_flags,
    )
    observation = orchestrate_observation(observation)

    engine = ProtocolEngine()
    return engine.process_and_attach(observation)


# ============================================================
# Demo
# ============================================================

def demo() -> None:
    field_voices = [
        FieldVoice(
            priority="high",
            content="後継危機と混乱が拡大し、崩壊リスクが高まっている。",
            source_account="@ConflictWatch",
            location="Qom",
            observed_at=datetime(2026, 3, 4, 6, 30, tzinfo=timezone.utc),
            language="ja",
            tags=["collapse", "transition"],
        ),
        FieldVoice(
            priority="medium",
            content="制度的責任と分析が必要だ。",
            source_account="@AnalystDesk",
            location="Tehran",
            observed_at=datetime(2026, 3, 4, 7, 10, tzinfo=timezone.utc),
            language="ja",
            tags=["analysis"],
        ),
    ]

    result = orchestrate_field_voices(
        field_voices,
        observation_id="obs-ccp-orch-001",
        timestamp=datetime(2026, 3, 4, 9, 30, tzinfo=timezone.utc),
        domain=Domain.geopolitics,
        requested_engines=[EngineName.ProtocolEngine, EngineName.LPTM, EngineName.COCLI],
        summary="Classification-first orchestrator demo",
        similar_case_score=0.42,
        history_matches=1,
        risk_flags=["warning"],
    )

    print(result.model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    demo()
