from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from review_thresholds_v01 import (
    ReviewChecklist,
    ReviewThresholdsV01,
    DEFAULT_THRESHOLDS,
    compute_drift,
    evaluate_auto_promotion,
)


REVIEW_FEEDBACK_LOG = "review_feedback.csv"


# ============================================================
# Helpers
# ============================================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y", "pass", "approved"}:
        return True
    if s in {"0", "false", "no", "n", "fail", "rejected"}:
        return False
    return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


# ============================================================
# Data models
# ============================================================

@dataclass
class ReviewFeedbackRecord:
    timestamp: str
    error_type: str
    status_before: str
    reviewer: str
    approved: bool

    rvi_repair_value: bool
    cci_connectivity: bool
    doq_question_preserved: bool

    note: str

    classification_class: str
    classification_confidence: float

    K: float
    Q: float
    C: float
    S: float
    T: float
    F: float

    execution_success: bool
    required_manual_fix: bool

    logged_at: str

    @property
    def axes(self) -> dict[str, float]:
        return {
            "K": self.K,
            "Q": self.Q,
            "C": self.C,
            "S": self.S,
            "T": self.T,
            "F": self.F,
        }


# ============================================================
# CSV I/O
# ============================================================

def append_review_feedback(
    *,
    error_type: str,
    status_before: str,
    checklist: ReviewChecklist,
    classification_class: str = "",
    classification_confidence: float = 0.0,
    axes: dict[str, float] | None = None,
    execution_success: bool = False,
    required_manual_fix: bool = True,
    timestamp: str | None = None,
    log_path: str = REVIEW_FEEDBACK_LOG,
) -> None:
    """
    人間レビュー結果を review_feedback.csv に追記する。
    """
    axes = axes or {}
    path = Path(log_path)
    is_new = not path.exists()

    approved = checklist.is_approved()

    row = {
        "timestamp": timestamp or _now_iso(),
        "error_type": error_type,
        "status_before": status_before,
        "reviewer": checklist.reviewer or "",
        "approved": approved,
        "rvi_repair_value": checklist.rvi_repair_value,
        "cci_connectivity": checklist.cci_connectivity,
        "doq_question_preserved": checklist.doq_question_preserved,
        "note": checklist.note,
        "classification_class": classification_class,
        "classification_confidence": classification_confidence,
        "K": axes.get("K", 0.0),
        "Q": axes.get("Q", 0.0),
        "C": axes.get("C", 0.0),
        "S": axes.get("S", 0.0),
        "T": axes.get("T", 0.0),
        "F": axes.get("F", 0.0),
        "execution_success": execution_success,
        "required_manual_fix": required_manual_fix,
        "logged_at": _now_iso(),
    }

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "error_type",
                "status_before",
                "reviewer",
                "approved",
                "rvi_repair_value",
                "cci_connectivity",
                "doq_question_preserved",
                "note",
                "classification_class",
                "classification_confidence",
                "K", "Q", "C", "S", "T", "F",
                "execution_success",
                "required_manual_fix",
                "logged_at",
            ],
        )
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def load_review_feedback(log_path: str = REVIEW_FEEDBACK_LOG) -> list[ReviewFeedbackRecord]:
    path = Path(log_path)
    if not path.exists():
        return []

    records: list[ReviewFeedbackRecord] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                ReviewFeedbackRecord(
                    timestamp=row.get("timestamp", ""),
                    error_type=row.get("error_type", ""),
                    status_before=row.get("status_before", ""),
                    reviewer=row.get("reviewer", ""),
                    approved=_safe_bool(row.get("approved")),
                    rvi_repair_value=_safe_bool(row.get("rvi_repair_value")),
                    cci_connectivity=_safe_bool(row.get("cci_connectivity")),
                    doq_question_preserved=_safe_bool(row.get("doq_question_preserved")),
                    note=row.get("note", ""),
                    classification_class=row.get("classification_class", ""),
                    classification_confidence=_safe_float(row.get("classification_confidence")),
                    K=_safe_float(row.get("K")),
                    Q=_safe_float(row.get("Q")),
                    C=_safe_float(row.get("C")),
                    S=_safe_float(row.get("S")),
                    T=_safe_float(row.get("T")),
                    F=_safe_float(row.get("F")),
                    execution_success=_safe_bool(row.get("execution_success")),
                    required_manual_fix=_safe_bool(row.get("required_manual_fix")),
                    logged_at=row.get("logged_at", ""),
                )
            )
    return records


# ============================================================
# Aggregation
# ============================================================

def _filter_by_error_type(
    records: list[ReviewFeedbackRecord],
    error_type: str,
) -> list[ReviewFeedbackRecord]:
    return [r for r in records if r.error_type == error_type]


def summarize_feedback_for_protocol(
    error_type: str,
    *,
    log_path: str = REVIEW_FEEDBACK_LOG,
) -> dict[str, Any]:
    """
    registered -> automated の判定材料を集計する。
    """
    records = _filter_by_error_type(load_review_feedback(log_path), error_type)

    if not records:
        return {
            "error_type": error_type,
            "count": 0,
            "approved_count": 0,
            "approval_rate": 0.0,
            "success_rate": 0.0,
            "manual_fix_rate": 0.0,
            "avg_risk": 0.0,
            "avg_axes": {k: 0.0 for k in ["K", "Q", "C", "S", "T", "F"]},
            "drift": 0.0,
        }

    avg_axes = {
        k: round(mean(getattr(r, k) for r in records), 4)
        for k in ["K", "Q", "C", "S", "T", "F"]
    }

    first_axes = records[0].axes
    drift = compute_drift(first_axes, avg_axes)

    approved_count = sum(1 for r in records if r.approved)
    success_count = sum(1 for r in records if r.execution_success)
    manual_fix_count = sum(1 for r in records if r.required_manual_fix)

    return {
        "error_type": error_type,
        "count": len(records),
        "approved_count": approved_count,
        "approval_rate": round(approved_count / len(records), 4),
        "success_rate": round(success_count / len(records), 4),
        "manual_fix_rate": round(manual_fix_count / len(records), 4),
        "avg_risk": round(mean(r.S for r in records), 4),
        "avg_axes": avg_axes,
        "drift": round(drift, 4),
    }


# ============================================================
# Promotion decision
# ============================================================

def evaluate_protocol_promotion_readiness(
    error_type: str,
    *,
    log_path: str = REVIEW_FEEDBACK_LOG,
    thresholds: ReviewThresholdsV01 = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    """
    review_feedback.csv を元に automated 昇格可否を判定する。
    """
    summary = summarize_feedback_for_protocol(error_type, log_path=log_path)

    decision = evaluate_auto_promotion(
        frequency=summary["count"],
        success_rate=summary["success_rate"],
        avg_risk=summary["avg_risk"],
        drift=summary["drift"],
        thresholds=thresholds,
    )

    return {
        "error_type": error_type,
        "ready": decision["pass"],
        "summary": summary,
        "decision": decision,
    }


# ============================================================
# Convenience helper
# ============================================================

def record_candidate_review(
    *,
    candidate: dict[str, Any],
    checklist: ReviewChecklist,
    execution_success: bool = False,
    required_manual_fix: bool = True,
    log_path: str = REVIEW_FEEDBACK_LOG,
) -> None:
    """
    candidate / registered のレビュー結果をそのまま記録する。
    candidate dict は protocol_evolution_v01.py の candidate を想定。
    """
    evidence = candidate.get("evidence", {}) or {}
    avg_axes = evidence.get("avg_axes", {}) or {}

    append_review_feedback(
        error_type=candidate.get("error_type", ""),
        status_before=candidate.get("status", "candidate"),
        checklist=checklist,
        classification_class=evidence.get("classification_class", ""),
        classification_confidence=0.0,
        axes=avg_axes,
        execution_success=execution_success,
        required_manual_fix=required_manual_fix,
        log_path=log_path,
    )


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    check = ReviewChecklist(
        rvi_repair_value=True,
        cci_connectivity=True,
        doq_question_preserved=True,
        reviewer="user",
        note="candidate looks structurally reusable",
    )

    append_review_feedback(
        error_type="UNK_workflow_deadbeef",
        status_before="registered",
        checklist=check,
        classification_class="UNKNOWN",
        classification_confidence=0.62,
        axes={"K": 0.21, "Q": 0.18, "C": 0.44, "S": 0.27, "T": 0.22, "F": 0.61},
        execution_success=True,
        required_manual_fix=False,
    )

    result = evaluate_protocol_promotion_readiness("UNK_workflow_deadbeef")
    print(result)
