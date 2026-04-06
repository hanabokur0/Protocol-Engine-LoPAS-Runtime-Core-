🧠 Protocol Engine (LoPAS Runtime Core)

Protocol Engine is a classification-first execution system that converts observations into actionable protocols.

It sits at the final layer of the LoPAS pipeline:

FieldVoice → Feature Extraction → Orchestrator → Protocol Engine → Action

Unlike traditional rule engines, this system:

Learns from unknown cases
Evolves protocols over time
Separates classification from execution
Integrates human review as a first-class component
🚀 Overview

This engine processes structured observations and determines:

✅ Auto execution
👤 Human review
❓ Unknown case (learning candidate)

Core entry point:

from protocol_engine import ProtocolEngine

engine = ProtocolEngine()
result = engine.process_observation(observation)
🧩 Core Concepts
1. Classification-first architecture

Instead of rule matching, the system starts from classification:

AUTO_OK
IGNORE
REVIEW
ESCALATE
UNKNOWN

These are generated upstream (Feature Extraction v0.2).

The Protocol Engine only executes or routes.

👉 ここがかなり重要
「判断」と「実行」を分離してる

2. Protocol Store

Protocols are stored in protocols.json.

Example:

{
  "AUTO_OK": {
    "description": "分類結果: 自動処理可能",
    "action": "protocol_accept",
    "auto": true,
    "severity": "low"
  }
}

Managed via:

store = ProtocolStore()
store.get("AUTO_OK")
store.add("E99", "timeout", "retry_connection")

3. Execution Layer

Actions are mapped to handlers:

execute("protocol_accept", row)

Examples:

protocol_accept
store_only
escalate_review
log_and_review
4. Unknown Case Learning

Unknown inputs are logged:

unknown_errors.csv

Automatically stored with:

classification_class
6 axes (K,Q,C,S,T,F)
input_state
log_unknown(row)

5. Self-Evolving Protocols

Unknown cases are clustered and converted into candidates:

suggest_new_protocols()

This computes:

Frequency
Similarity
Stability
Risk

Then outputs:

{
  "error_type": "UNK_workflow_xxxx",
  "status": "candidate",
  "rii": 0.72
}

6. Human-in-the-loop Promotion

Protocol lifecycle:

UNKNOWN → candidate → registered → automated
Step 1: Candidate generation
suggest_new_protocols()
Step 2: Human review
append_review_feedback(...)
Step 3: Promotion
promote_to_auto(error_type)

🔁 Full Pipeline Integration

This engine is designed to work with:

Feature Extraction (classification axes)
Orchestrator (routing)
LPTM / COCLI (optional engines)

End-to-end:

from orchestrator_v02 import orchestrate_field_voices

result = orchestrate_field_voices(field_voices)

📊 Metrics

The engine tracks:

Metric	Meaning
DPR	Auto execution rate
HBR	Human intervention rate
EDR	Unknown rate
AMI	Automation maturity
BPI	Bottleneck pressure
engine.report()
🧪 Example
schema_like = {
  "states": {
    "classification_class": "AUTO_OK"
  }
}

engine = ProtocolEngine()
result = engine.process_observation(schema_like)

print(result)

Output:

{
  "status": "auto",
  "result": "分類プロトコル受理"
}
⚙️ Design Philosophy

This is not a rule engine.

It is:

A learning execution system
A protocol evolution layer
A human-AI boundary controller

Key ideas:

Separation of concerns
Classification → upstream
Execution → protocol engine
Unknown-first design
Unknowns are not errors
They are future protocols
Gradual automation
Nothing is auto by default
Everything earns automation
📁 File Structure
protocol_engine.py          # Core engine
protocol_evolution_v01.py   # Learning + clustering
review_feedback_v01.py      # Human review system
orchestrator_v02.py         # Pipeline integration
feature_extraction_v02.py   # Classification core
🧠 Position in LoPAS

Protocol Engine corresponds to:

LoPAS Layer: Execution / Responsibility Layer

It connects:

DoQ / CCI / SCI → classification
→ actionable decision
→ real-world effect
🔮 Roadmap
 protocol versioning
 provenance tracking
 distributed protocol store
 real-time learning loop (streaming)
📜 License

MIT
