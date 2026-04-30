# 🧠 Protocol Engine (LoPAS Runtime Core)
　　　
> This is the skeleton of an AI agent.  
> A system that separates responsibility, execution, and learning.

---

## 🚀 Quick Start

```bash
python run.py --mode demo
🔗 Pipeline
External Input
   ↓
[RNC] → input validation (True / False)
   ↓
[Pipeline] → classification
   ↓
[Protocol Engine] → execution
   ↓
[Learning] → unknown → protocol evolution
🧩 What this does

Given an input:

✅ AUTO → executed immediately
👤 REVIEW → sent to human
❓ UNKNOWN → stored and learned
🧠 Core Design
1. Classification-first

All decisions start from classification:

AUTO_OK
REVIEW
ESCALATE
UNKNOWN
IGNORE
2. Responsibility separation
Layer	Role
RNC	Input validation (external)
Pipeline	Classification
Protocol Engine	Execution
Learning	Evolution
3. Unknown is not failure

Unknown cases are not errors.

They become future protocols.

UNKNOWN → cluster → candidate → protocol
📁 Structure
core/
  protocol_engine.py

pipeline/
  feature_extraction_v02.py
  orchestrator_v02.py

learning/
  protocol_evolution_v01.py
  review_feedback_v01.py

rnc/
  rnc_validator.py

run.py
README.md
🧪 Example
from orchestrator_v02 import orchestrate_field_voices

result = orchestrate_field_voices(field_voices)
print(result)
🔄 Learning

Unknown cases are automatically:

logged
clustered
converted into candidate protocols

This enables continuous system evolution.

⚙️ Execution Flow
RNC PASS → Protocol Engine → AUTO / HUMAN / UNKNOWN
                              ↓
                         UNKNOWN → Learning
⚠️ Design Principles
No manual decision in execution layer
Unknown is a signal, not an error
Exceptions must become rules
Responsibility must be explicit
🧱 System Position

This repository is the execution + learning layer of a larger system:

RNC → input responsibility layer (external)
Protocol Engine → execution layer (this repo)
Learning → evolution layer (this repo)
📌 Status

Experimental / evolving system

📜 License

MIT
