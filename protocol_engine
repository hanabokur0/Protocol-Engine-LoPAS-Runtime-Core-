from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL_FILE = "protocols.json"
UNKNOWN_LOG = "unknown_errors.csv"


# ============================================================
# Optional imports (LoPAS Common Schema)
# ============================================================

try:
    from common_schema_models import (  # type: ignore
        EngineName,
        EngineOutput,
        LoPASObservation,
        NumericIndicator,
        ProtocolResult,
        ProtocolStatus,
        Results,
    )
except Exception:
    EngineName = None
    EngineOutput = None
    LoPASObservation = None
    NumericIndicator = None
    ProtocolResult = None
    ProtocolStatus = None
    Results = None


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


# ============================================================
# Protocol Store
# ============================================================

class ProtocolStore:
    def __init__(self, path: str = PROTOCOL_FILE):
        self.path = Path(path)
        self.protocols: dict[str, dict[str, Any]] = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            raise ValueError("protocol file must contain a JSON object")

        return {
            # legacy
            "E01": {
                "description": "必須項目欠損",
                "action": "fill_missing_data",
                "auto": True,
                "severity": "medium",
            },
            "E02": {
                "description": "契約照合不一致",
                "action": "recheck_contract",
                "auto": True,
                "severity": "high",
            },
            "E03": {
                "description": "データ形式不正",
                "action": "normalize_format",
                "auto": True,
                "severity": "medium",
            },

            # classification-first canonical routes
            "AUTO_OK": {
                "description": "分類結果: 自動処理可能",
                "action": "protocol_accept",
                "auto": True,
                "severity": "low",
            },
            "IGNORE": {
                "description": "分類結果: 保存のみ / 無視可能",
                "action": "store_only",
                "auto": True,
                "severity": "low",
            },
            "REVIEW": {
                "description": "分類結果: 人間確認",
                "action": "escalate_review",
                "auto": False,
                "severity": "medium",
            },
            "ESCALATE": {
                "description": "分類結果: 上位判断",
                "action": "escalate_review",
                "auto": False,
                "severity": "critical",
            },
            "UNKNOWN": {
                "description": "分類結果: 未知ケース",
                "action": "log_and_review",
                "auto": False,
                "severity": "high",
            },

            # backward-compatible review/error routes
            "LPTM_L3": {
                "description": "L3到達: 人間レビューへエスカレーション",
                "action": "escalate_review",
                "auto": False,
                "severity": "critical",
            },
            "LOW_CONF": {
                "description": "信頼度低下: 人間確認",
                "action": "escalate_review",
                "auto": False,
                "severity": "high",
            },
            "SCI_HIGH": {
                "description": "崩壊リスク高: 人間確認",
                "action": "escalate_review",
                "auto": False,
                "severity": "critical",
            },
            "AUTO_PROTOCOL": {
                "description": "従来の自動プロトコル通過",
                "action": "protocol_accept",
                "auto": True,
                "severity": "low",
            },
        }

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.protocols, f, ensure_ascii=False, indent=2)

    def get(self, error_type: str) -> dict[str, Any] | None:
        return self.protocols.get(error_type)

    def add(
        self,
        error_type: str,
        description: str,
        action: str,
        auto: bool = False,
        severity: str = "medium",
    ) -> None:
        self.protocols[error_type] = {
            "description": description,
            "action": action,
            "auto": auto,
            "severity": severity,
            "added_at": _now_iso(),
        }
        self.save()
        print(f"[learned] {error_type} -> {action}")


# ============================================================
# Protocol Execution
# ============================================================

def execute(action: str, row: dict[str, Any]) -> str:
    handlers = {
        "fill_missing_data": lambda r: f"欠損補完完了 -> {r.get('input_state', '')}",
        "recheck_contract": lambda r: f"契約再照合完了 -> {r.get('input_state', '')}",
        "normalize_format": lambda r: f"フォーマット修正完了 -> {r.get('input_state', '')}",
        "escalate_review": lambda r: f"人間レビューへ送付 -> {r.get('input_state', '')}",
        "protocol_accept": lambda r: f"分類プロトコル受理 -> {r.get('input_state', '')}",
        "store_only": lambda r: f"保存のみ -> {r.get('input_state', '')}",
        "log_and_review": lambda r: f"未知ケース記録 + 人間レビュー -> {r.get('input_state', '')}",
    }
    handler = handlers.get(action)
    return handler(row) if handler else f"未実装アクション: {action}"


# ============================================================
# Unknown Log
# ============================================================

def log_unknown(row: dict[str, Any]) -> None:
    path = Path(UNKNOWN_LOG)
    is_new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "error_type",
                "input_state",
                "domain",
                "source",
                "classification_class",
                "K",
                "Q",
                "C",
                "S",
                "T",
                "F",
                "logged_at",
            ],
        )
        if is_new:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": row.get("timestamp", ""),
                "error_type": row.get("error_type", ""),
                "input_state": row.get("input_state", ""),
                "domain": row.get("domain", ""),
                "source": row.get("source", ""),
                "classification_class": row.get("classification_class", ""),
                "K": row.get("K", ""),
                "Q": row.get("Q", ""),
                "C": row.get("C", ""),
                "S": row.get("S", ""),
                "T": row.get("T", ""),
                "F": row.get("F", ""),
                "logged_at": _now_iso(),
            }
        )


# ============================================================
# Row Normalizer
# ============================================================

def observation_to_protocol_row(observation: Any) -> dict[str, Any]:
    """
    Priority:
      1. classification_class
      2. legacy error_type
      3. review_reason / SCI / LPTM fallback
    """
    if isinstance(observation, dict) and "error_type" in observation and "states" not in observation:
        return observation

    obj = observation
    if is_dataclass(obj):
        obj = asdict(obj)

    if hasattr(observation, "model_dump"):
        obj = observation.model_dump(exclude_none=True)

    if isinstance(obj, dict) and "meta" in obj:
        meta = obj.get("meta", {}) or {}
        routing = obj.get("routing", {}) or {}
        results = obj.get("results", {}) or {}
        indicators = obj.get("indicators", {}) or {}
        states = obj.get("states", {}) or {}

        # classification-first
        classification_class = states.get("classification_class")
        classification_reason = states.get("classification_reason", "")
        classification_confidence = states.get("classification_confidence")

        # 6 axes
        K = _safe_float((indicators.get("K") or {}).get("value"))
        Q = _safe_float((indicators.get("Q") or {}).get("value"))
        C = _safe_float((indicators.get("C") or {}).get("value"))
        S = _safe_float((indicators.get("S") or {}).get("value"))
        T = _safe_float((indicators.get("T") or {}).get("value"))
        F = _safe_float((indicators.get("F") or {}).get("value"))

        if classification_class:
            error_type = str(classification_class).strip()
            return {
                "timestamp": obj.get("timestamp", _now_iso()),
                "error_type": error_type,
                "input_state": (
                    f"class={classification_class}; reason={classification_reason}; "
                    f"K={K:.3f},Q={Q:.3f},C={C:.3f},S={S:.3f},T={T:.3f},F={F:.3f}"
                ),
                "domain": obj.get("domain", ""),
                "source": obj.get("source", ""),
                "classification_class": classification_class,
                "classification_reason": classification_reason,
                "classification_confidence": classification_confidence,
                "K": K,
                "Q": Q,
                "C": C,
                "S": S,
                "T": T,
                "F": F,
                "raw": obj,
            }


        # legacy fallback
        review_reason = meta.get("review_reason") or ""
        review_required = bool(meta.get("human_review_required", False))
        flags = meta.get("flags", []) or []

        engine_outputs = results.get("engine_outputs", []) or []
        lptm_layer = states.get("layer")
        for out in engine_outputs:
            if out.get("engine") == "LPTM":
                lptm_layer = out.get("states", {}).get("layer", lptm_layer)

        sci_val = None
        sci_obj = indicators.get("SCI")
        if isinstance(sci_obj, dict):
            sci_val = sci_obj.get("value")

        error_type = "UNKNOWN_CASE"
        if "low_confidence" in review_reason:
            error_type = "LOW_CONF"
        elif sci_val is not None and float(sci_val) > 0.80:
            error_type = "SCI_HIGH"
        elif lptm_layer == "L3":
            error_type = "LPTM_L3"
        elif review_required:
            error_type = "REVIEW"
        elif routing.get("next_action") == "route_to_protocol":
            error_type = "AUTO_PROTOCOL"

        return {
            "timestamp": obj.get("timestamp", _now_iso()),
            "error_type": error_type,
            "input_state": f"domain={obj.get('domain', '')}; flags={','.join(flags)}; review={review_reason}",
            "domain": obj.get("domain", ""),
            "source": obj.get("source", ""),
            "classification_class": "",
            "K": "",
            "Q": "",
            "C": "",
            "S": "",
            "T": "",
            "F": "",
            "raw": obj,
        }

    raise TypeError("Unsupported observation type for protocol conversion")


# ============================================================
# Protocol Engine
# ============================================================

class ProtocolEngine:
    def __init__(self, protocol_path: str = PROTOCOL_FILE):
        self.store = ProtocolStore(protocol_path)
        self.stats = {"auto": 0, "human": 0, "unknown": 0, "total": 0}

    def process(self, row: dict[str, Any]) -> dict[str, Any]:
        self.stats["total"] += 1
        error_type = str(row.get("error_type", "")).strip()
        protocol = self.store.get(error_type)

        if protocol is None:
            log_unknown(row)
            self.stats["unknown"] += 1
            return {
                "status": "unknown",
                "error_type": error_type,
                "input_state": row.get("input_state", ""),
                "classification_class": row.get("classification_class"),
            }

        if bool(protocol.get("auto", False)):
            result = execute(str(protocol.get("action", "")), row)
            self.stats["auto"] += 1
            return {
                "status": "auto",
                "result": result,
                "error_type": error_type,
                "severity": protocol.get("severity"),
                "classification_class": row.get("classification_class"),
                "axes": {
                    "K": row.get("K"),
                    "Q": row.get("Q"),
                    "C": row.get("C"),
                    "S": row.get("S"),
                    "T": row.get("T"),
                    "F": row.get("F"),
                },
            }

        # UNKNOWN class is canonical but still loggable
        if error_type == "UNKNOWN":
            log_unknown(row)

        self.stats["human"] += 1
        return {
            "status": "human",
            "description": protocol.get("description", ""),
            "error_type": error_type,
            "severity": protocol.get("severity"),
            "classification_class": row.get("classification_class"),
            "axes": {
                "K": row.get("K"),
                "Q": row.get("Q"),
                "C": row.get("C"),
                "S": row.get("S"),
                "T": row.get("T"),
                "F": row.get("F"),
            },
        }

    def process_observation(self, observation: Any) -> dict[str, Any]:
        row = observation_to_protocol_row(observation)
        return self.process(row)

    def process_and_attach(self, observation: Any) -> Any:
        result = self.process_observation(observation)

        if LoPASObservation is None or not hasattr(observation, "results"):
            return result

        if getattr(observation, "results", None) is None and Results is not None:
            observation.results = Results(engine_outputs=[], protocol_result=None)

        if Results is not None and observation.results is None:
            observation.results = Results(engine_outputs=[], protocol_result=None)

        if EngineOutput is not None:
            engine_output = EngineOutput(
                engine=EngineName.ProtocolEngine,
                states={
                    "status": result.get("status", "unknown"),
                    "classification_class": result.get("classification_class"),
                },
                indicators={
                    "DPR": NumericIndicator(value=1.0 if result.get("status") == "auto" else 0.0, scale_min=0.0, scale_max=1.0, kind="derived", method="ProtocolEngine.process_and_attach")
                    if NumericIndicator is not None else None,
                    "HBR": NumericIndicator(value=1.0 if result.get("status") == "human" else 0.0, scale_min=0.0, scale_max=1.0, kind="derived", method="ProtocolEngine.process_and_attach")
                    if NumericIndicator is not None else None,
                    "EDR": NumericIndicator(value=1.0 if result.get("status") == "unknown" else 0.0, scale_min=0.0, scale_max=1.0, kind="derived", method="ProtocolEngine.process_and_attach")
                    if NumericIndicator is not None else None,
                },
                summary=result.get("result") or result.get("description") or result.get("error_type"),
                confidence=1.0,
            )
            engine_output.indicators = {k: v for k, v in engine_output.indicators.items() if v is not None}
            observation.results.engine_outputs.append(engine_output)

        if ProtocolResult is not None:
            status_value = result.get("status")
            observation.results.protocol_result = ProtocolResult(
                status=ProtocolStatus(status_value) if status_value in {"auto", "human", "unknown"} else None,
                result=result.get("result"),
                description=result.get("description"),
                error_type=result.get("error_type"),
            )
        return observation

    def report(self) -> dict[str, Any]:
        t = self.stats["total"]
        if t == 0:
            return {}
        auto = self.stats["auto"]
        human = self.stats["human"]
        unknown = self.stats["unknown"]
        return {
            "total": t,
            "auto": auto,
            "human": human,
            "unknown": unknown,
            "auto_rate": round(auto / t * 100, 1),
            "human_rate": round(human / t * 100, 1),
            "unknown_rate": round(unknown / t * 100, 1),
            "DPR": round(auto / t, 4),
            "HBR": round(human / t, 4),
            "EDR": round(unknown / t, 4),
            "AMI": round((auto - unknown) / t, 4),
            "BPI": round((human + unknown) / t, 4),
        }


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    engine = ProtocolEngine()

    schema_like = {
        "timestamp": _now_iso(),
        "domain": "workflow",
        "source": "Grok",
        "indicators": {
            "K": {"value": 0.82},
            "Q": {"value": 0.12},
            "C": {"value": 0.61},
            "S": {"value": 0.18},
            "T": {"value": 0.34},
            "F": {"value": 0.88},
        },
        "states": {
            "classification_class": "AUTO_OK",
            "classification_reason": "known pattern / high confidence / low risk",
            "classification_confidence": 0.86,
        },
        "meta": {
            "human_review_required": False,
            "flags": ["class:AUTO_OK"],
        },
    }

    print("[classification-first]", engine.process_observation(schema_like))
    print("[report]", engine.report())
