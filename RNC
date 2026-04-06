RNC Validator v0.1
Layer 1 - 入力チェック（Responsibility Normalization Contract）

役割：
  入力データを Schema + Rules で判定し True / False のみ返す。
  False の場合は ErrorCatalog から修正指示を返す。
  人間の判断は介在しない。
"""

import json
from pathlib import Path
from datetime import datetime


# ============================================================
# デフォルト Schema（実業務に合わせて差し替える）
# ============================================================

DEFAULT_SCHEMA = {
    "timestamp":   {"type": "date",   "required": True},
    "error_type":  {"type": "string", "required": True,  "pattern": "^E[0-9]{2}$"},
    "input_state": {"type": "string", "required": True},
    "team":        {"type": "string", "required": False}
}

# ============================================================
# デフォルト ErrorCatalog
# ============================================================

DEFAULT_ERROR_CATALOG = {
    "RNC-001": "timestamp が未入力です。YYYY-MM-DD 形式で入力してください。",
    "RNC-002": "error_type が未入力です。",
    "RNC-003": "error_type の形式が不正です。E01〜E99 の形式で入力してください。",
    "RNC-004": "input_state が未入力です。",
    "RNC-005": "timestamp の形式が不正です。YYYY-MM-DD で入力してください。",
}


# ============================================================
# RNC Validator
# ============================================================

class RNCValidator:

    def __init__(self, schema: dict = None, error_catalog: dict = None):
        self.schema        = schema        or DEFAULT_SCHEMA
        self.error_catalog = error_catalog or DEFAULT_ERROR_CATALOG
        self.policy_version = "1.0"

    def validate(self, row: dict) -> dict:
        """
        入力1行を検証する。

        Returns:
            {
                "result": True | False,
                "error_ids": ["RNC-001", ...],
                "messages": ["修正指示..."]
            }
        """
        error_ids = []

        for field, rules in self.schema.items():
            value = row.get(field, "").strip() if row.get(field) else ""

            # 必須チェック
            if rules.get("required") and not value:
                eid = self._required_error_id(field)
                if eid:
                    error_ids.append(eid)
                continue

            if not value:
                continue

            # 型チェック
            if rules.get("type") == "date":
                if not self._is_date(value):
                    error_ids.append("RNC-005")

            # パターンチェック
            if rules.get("pattern"):
                import re
                if not re.match(rules["pattern"], value):
                    error_ids.append(self._pattern_error_id(field))

        error_ids = list(dict.fromkeys(filter(None, error_ids)))  # 重複除去
        messages  = [self.error_catalog.get(e, e) for e in error_ids]

        return {
            "result":    len(error_ids) == 0,
            "error_ids": error_ids,
            "messages":  messages
        }

    # ----------------------------------------------------------
    # ヘルパー
    # ----------------------------------------------------------

    def _required_error_id(self, field: str) -> str:
        mapping = {
            "timestamp":   "RNC-001",
            "error_type":  "RNC-002",
            "input_state": "RNC-004",
        }
        return mapping.get(field)

    def _pattern_error_id(self, field: str) -> str:
        mapping = {
            "error_type": "RNC-003",
        }
        return mapping.get(field)

    def _is_date(self, value: str) -> bool:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False
