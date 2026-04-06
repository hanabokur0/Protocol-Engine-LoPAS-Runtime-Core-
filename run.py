"""
RNC + Protocol Engine 統合システム v0.1
run.py - エントリポイント

二層構造：
  Layer 1: RNC Validator  → 入力品質チェック（責任をユーザーに返す）
  Layer 2: Protocol Engine → エラー自動処理（未知例外の学習）

使い方：
  python run.py --mode demo
  python run.py --mode live --csv your_log.csv
  python run.py --mode live --csv your_log.csv --dry-run
"""

import csv
import json
import argparse
from datetime import datetime
from pathlib import Path

from rnc_validator   import RNCValidator
from protocol_engine import ProtocolEngine


# ============================================================
# 監査ログ
# ============================================================

def save_run_report(report: dict, path: str = "run_report.json"):
    report["run_at"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  [監査] レポート保存 → {path}")


# ============================================================
# デモデータ
# ============================================================

DEMO_LOGS = [
    # 正常
    {"timestamp": "2026-03-01", "error_type": "E01", "input_state": "missing_field"},
    {"timestamp": "2026-03-01", "error_type": "E02", "input_state": "contract_mismatch"},
    {"timestamp": "2026-03-02", "error_type": "E03", "input_state": "bad_date_format"},
    # RNC弾き（入力不正）
    {"timestamp": "",           "error_type": "E01", "input_state": "missing_field"},     # timestamp欠損
    {"timestamp": "2026-03-03", "error_type": "ZZ9", "input_state": "bad_code"},          # コード不正
    # Protocol Engine 未知
    {"timestamp": "2026-03-03", "error_type": "E99", "input_state": "unknown_condition"},
    {"timestamp": "2026-03-04", "error_type": "E77", "input_state": "system_timeout"},
    # 正常続き
    {"timestamp": "2026-03-04", "error_type": "E01", "input_state": "missing_amount"},
    {"timestamp": "2026-03-05", "error_type": "E02", "input_state": "contract_id_002"},
]


# ============================================================
# メイン処理
# ============================================================

def run(rows: list, dry_run: bool = False):

    validator = RNCValidator()
    engine    = ProtocolEngine()

    rnc_stats = {"pass": 0, "fail": 0, "total": 0}

    print("\n" + "="*60)
    print("RNC + Protocol Engine 統合システム v0.1")
    print(f"モード: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"登録済みプロトコル数: {len(engine.store.protocols)}")
    print("="*60)

    for row in rows:
        rnc_stats["total"] += 1
        ts  = row.get("timestamp","")
        et  = row.get("error_type","")
        ipt = row.get("input_state","")

        print(f"\n[{ts}] {et} / {ipt}")

        # ── Layer 1: RNC ──────────────────────────────
        rnc_result = validator.validate(row)

        if not rnc_result["result"]:
            rnc_stats["fail"] += 1
            print(f"  [RNC ✗] 入力不正 → ユーザーへ返却")
            for msg in rnc_result["messages"]:
                print(f"    → {msg}")
            print(f"  ※ Protocol Engine には渡さない")
            continue

        rnc_stats["pass"] += 1
        print(f"  [RNC ✓] 入力OK → Protocol Engine へ")

        # ── Layer 2: Protocol Engine ──────────────────
        if dry_run:
            print(f"  [DRY RUN] 実行スキップ")
            continue

        pe_result = engine.process(row)

        if pe_result["status"] == "auto":
            print(f"  [自動] {pe_result['result']}")
        elif pe_result["status"] == "human":
            print(f"  [人間] {pe_result['description']} → 手動対応キューへ")
        elif pe_result["status"] == "unknown":
            print(f"  [未知] unknown_errors.csv に記録 → 学習待ち")

    # ── サマリ ───────────────────────────────────────
    pe_report = engine.report()

    print("\n" + "="*60)
    print("処理結果サマリ")
    print("="*60)
    print(f"  総入力数        : {rnc_stats['total']}")
    print(f"  RNC通過         : {rnc_stats['pass']}")
    print(f"  RNC弾き         : {rnc_stats['fail']}  ← ユーザー入力不正")
    if pe_report:
        print(f"  ─────────────────────────────")
        print(f"  自動処理        : {pe_report['auto']}  ({pe_report['auto_rate']}%)")
        print(f"  人間対応        : {pe_report['human']}  ({pe_report['human_rate']}%)")
        print(f"  未知エラー      : {pe_report['unknown']}  ({pe_report['unknown_rate']}%)")

        # 危険条件チェック
        print()
        if pe_report["unknown_rate"] > 40:
            print("  ⚠️  警告: 未知エラー率 > 40% → 手動確認を推奨")
        else:
            print("  ✓  未知エラー率は許容範囲内")

        if pe_report["auto_rate"] >= 60:
            print("  ✓  自動処理率は目標達成（>60%）")
        else:
            print("  ⚠️  警告: 自動処理率 < 60% → プロトコル追加を推奨")

    print("="*60)

    if pe_report.get("unknown", 0) > 0:
        print(f"\n→ unknown_errors.csv を確認し、新プロトコルを登録してください。")
        print("  例: engine.store.add('E99', '説明', 'action_name', auto=True)")

    # 監査ログ保存
    full_report = {
        "rnc":      rnc_stats,
        "protocol": pe_report,
        "dry_run":  dry_run
    }
    save_run_report(full_report)

    return full_report


# ============================================================
# エントリポイント
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="RNC + Protocol Engine v0.1")
    parser.add_argument("--mode",    choices=["demo","live"], default="demo")
    parser.add_argument("--csv",     help="ログCSVファイルパス")
    parser.add_argument("--dry-run", action="store_true", help="実行せずに確認のみ")
    args = parser.parse_args()

    if args.mode == "demo":
        run(DEMO_LOGS, dry_run=args.dry_run)

    elif args.mode == "live":
        if not args.csv:
            print("--csv でログファイルを指定してください")
            return
        rows = []
        with open(args.csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        run(rows, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
