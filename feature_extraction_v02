from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from common_schema_models import (
    Domain,
    EngineName,
    FieldVoice,
    InputType,
    LoPASObservation,
    Meta,
    NumericIndicator,
    Payload,
    Priority,
    Source,
    TraceStep,
)

# v0.1 の既存 proxy を再利用
from feature_extraction_v01 import (
    compute_question_density,
    compute_quality,
    estimate_collapse_risk,
    estimate_confidence,
    estimate_resonance,
    normalize_count,
    clamp,
)


# ============================================================
# Classification Core v0.1
# ============================================================

CLASS_OUTPUTS = ("AUTO_OK", "REVIEW", "ESCALATE", "UNKNOWN", "IGNORE")


@dataclass
class ClassificationAxes:
    K: float  # Knownness
    Q: float  # DoQ proxy
    C: float  # CCI proxy
    S: float  # SCI proxy
    T: float  # TRS proxy
    F: float  # Confidence

    def as_dict(self) -> dict[str, float]:
        return {
            "K": self.K,
            "Q": self.Q,
            "C": self.C,
            "S": self.S,
            "T": self.T,
            "F": self.F,
        }


# ============================================================
# Helpers
# ============================================================

def _safe_len_unique(values: Iterable[str | None]) -> int:
    return len({v for v in values if v})


def _count_sources(field_voices: list[FieldVoice]) -> int:
    return _safe_len_unique(v.source_account for v in field_voices)


def _count_locations(field_voices: list[FieldVoice]) -> int:
    return _safe_len_unique(v.location for v in field_voices)


def _count_tags(field_voices: list[FieldVoice]) -> int:
    tags: set[str] = set()
    for voice in field_voices:
        tags.update(voice.tags)
    return len(tags)


def _default_context_links(field_voices: list[FieldVoice]) -> int:
    """
    軽量 CCI proxy 用:
    source / location / tags の広がりを「接続可能性」の代替入力にする。
    """
    return (
        _count_sources(field_voices)
        + _count_locations(field_voices)
        + _count_tags(field_voices)
    )


# ============================================================
# 6-axis feature extraction
# ============================================================

def compute_knownness(
    *,
    similar_case_score: float = 0.0,
    history_matches: int = 0,
) -> float:
    """
    K: 既知度
    """
    return clamp(
        0.7 * similar_case_score
        + 0.3 * normalize_count(history_matches, 5.0)
    )


def compute_connectivity(
    *,
    context_links: int = 0,
    source_count: int = 0,
    knownness: float = 0.0,
) -> float:
    """
    C: CCI minimal proxy
    """
    return clamp(
        0.5 * normalize_count(context_links, 6.0)
        + 0.3 * normalize_count(source_count, 4.0)
        + 0.2 * knownness
    )


def compute_meaning(
    *,
    resonance: float,
    connectivity: float,
) -> float:
    """
    T: TRS minimal proxy
    resonance を主成分にしつつ、接続性を少し乗せる。
    """
    return clamp(0.7 * resonance + 0.3 * connectivity)


def build_classification_axes(
    field_voices: list[FieldVoice],
    *,
    similar_case_score: float = 0.0,
    history_matches: int = 0,
    context_links: int | None = None,
    source_count: int | None = None,
    risk_flags: list[str] | None = None,
) -> ClassificationAxes:
    """
    Classification Core v0.1 用の 6軸を構築する。
    """
    risk_flags = risk_flags or []

    if context_links is None:
        context_links = _default_context_links(field_voices)
    if source_count is None:
        source_count = _count_sources(field_voices)

    # 既存 proxy を流用
    Q = compute_question_density(field_voices)
    field_quality = compute_quality(field_voices)
    S = estimate_collapse_risk(field_voices)
    resonance = estimate_resonance(field_voices)
    F = estimate_confidence(field_voices, field_quality)

    # 新設軸
    K = compute_knownness(
        similar_case_score=similar_case_score,
        history_matches=history_matches,
    )
    C = compute_connectivity(
        context_links=context_links,
        source_count=source_count,
        knownness=K,
    )
    T = compute_meaning(
        resonance=resonance,
        connectivity=C,
    )

    # リスク補正
    if "critical" in risk_flags:
        S = clamp(S + 0.20)
    elif "warning" in risk_flags:
        S = clamp(S + 0.10)

    return ClassificationAxes(
        K=round(K, 4),
        Q=round(Q, 4),
        C=round(C, 4),
        S=round(S, 4),
        T=round(T, 4),
        F=round(F, 4),
    )


# ============================================================
# Classification
# ============================================================

def classify_from_axes(axes: ClassificationAxes) -> tuple[str, str]:
    """
    最終クラス判定。
    """
    a = axes

    if a.S > 0.70:
        return "ESCALATE", "high SCI / risk"

    if a.F < 0.40:
        return "REVIEW", "low confidence"

    if a.K < 0.30:
        return "UNKNOWN", "low knownness"

    if a.Q < 0.20 and a.T < 0.20 and a.S < 0.30:
        return "IGNORE", "low question / low meaning / low risk"

    if a.K > 0.70 and a.F > 0.70 and a.S < 0.30:
        return "AUTO_OK", "known pattern / high confidence / low risk"

    return "REVIEW", "default safe fallback"


def classification_confidence(axes: ClassificationAxes) -> float:
    """
    最終クラス自体の確信度。
    F を主成分にして、K と S の明確さを少し加味。
    """
    risk_clarity = 1.0 - abs(axes.S - 0.5) * 2.0
    risk_clarity = 1.0 - clamp(risk_clarity)  # 0.5付近は曖昧、端ほど明確
    score = 0.6 * axes.F + 0.25 * axes.K + 0.15 * risk_clarity
    return round(clamp(score), 4)


# ============================================================
# Indicator conversion
# ============================================================

def axes_to_indicators(axes: ClassificationAxes) -> dict[str, NumericIndicator]:
    method = "feature_extraction_v02.build_classification_axes"
    return {
        "K": NumericIndicator(value=axes.K, scale_min=0.0, scale_max=1.0, kind="derived", method=method),
        "Q": NumericIndicator(value=axes.Q, scale_min=0.0, scale_max=1.0, kind="derived", method=method),
        "C": NumericIndicator(value=axes.C, scale_min=0.0, scale_max=1.0, kind="derived", method=method),
        "S": NumericIndicator(value=axes.S, scale_min=0.0, scale_max=1.0, kind="derived", method=method),
        "T": NumericIndicator(value=axes.T, scale_min=0.0, scale_max=1.0, kind="derived", method=method),
        "F": NumericIndicator(value=axes.F, scale_min=0.0, scale_max=1.0, kind="derived", method=method),
    }


# ============================================================
# End-to-end observation builder
# ============================================================

def build_observation_with_classification_axes(
    field_voices: list[FieldVoice],
    *,
    observation_id: str | None = None,
    timestamp: datetime | None = None,
    domain: Domain = Domain.geopolitics,
    source: Source = Source.Grok,
    summary: str | None = None,
    requested_engines: list[EngineName] | None = None,
    similar_case_score: float = 0.0,
    history_matches: int = 0,
    context_links: int | None = None,
    source_count: int | None = None,
    risk_flags: list[str] | None = None,
) -> LoPASObservation:
    """
    FieldVoice[] -> 6軸 -> class判定 -> LoPASObservation
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    axes = build_classification_axes(
        field_voices=field_voices,
        similar_case_score=similar_case_score,
        history_matches=history_matches,
        context_links=context_links,
        source_count=source_count,
        risk_flags=risk_flags,
    )

    cls, reason = classify_from_axes(axes)
    cls_conf = classification_confidence(axes)

    indicators = axes_to_indicators(axes)

    flags = list(risk_flags or [])
    flags.append(f"class:{cls}")

    review_required = cls in {"REVIEW", "ESCALATE", "UNKNOWN"}
    review_reason = reason if review_required else None

    priority = Priority.medium
    if cls == "ESCALATE":
        priority = Priority.critical
    elif cls in {"REVIEW", "UNKNOWN"}:
        priority = Priority.high

    observation = LoPASObservation(
        observation_id=observation_id or f"obs-{timestamp.strftime('%Y%m%dT%H%M%SZ')}-ccp",
        timestamp=timestamp,
        domain=domain,
        source=source,
        engine_route=requested_engines or [],
        payload=Payload(
            input_type=InputType.field_voice_batch,
            summary=summary,
            field_voices=field_voices,
        ),
        indicators=indicators,
        states={
            "classification_class": cls,
            "classification_reason": reason,
            "classification_confidence": cls_conf,
        },
        meta=Meta(
            confidence=cls_conf,
            human_review_required=review_required,
            review_reason=review_reason,
            flags=flags,
            priority=priority,
            trace=[
                TraceStep(
                    engine="FeatureExtractionV02",
                    at=datetime.now(timezone.utc),
                    action="classification_core_axes",
                    note=f"6 axes generated; class={cls}",
                )
            ],
            provenance={
                "collector": source.value,
                "model": "feature_extraction_v02",
                "version": "0.1",
            },
        ),
    )
    return observation


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    sample = [
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

    obs = build_observation_with_classification_axes(
        sample,
        summary="classification core demo",
        similar_case_score=0.42,
        history_matches=1,
        risk_flags=["warning"],
    )

    print(obs.model_dump_json(indent=2, exclude_none=True))
