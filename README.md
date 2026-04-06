# 🧠 Protocol Engine (LoPAS Runtime Core)

This repository implements a **classification-first execution system**.

It converts structured observations into actions.

---

## 🔗 Pipeline

FieldVoice → Classification → Protocol Engine → Action  
　　　　　　　　　　　　　　　↓  
　　　　　　　　　　　　　UNKNOWN → Learning

---

## 🚀 What this does

Given an input observation:

- ✅ AUTO → executed immediately  
- 👤 REVIEW → sent to human  
- ❓ UNKNOWN → stored and learned  

---

## 🧩 Example

```python
from orchestrator_v02 import orchestrate_field_voices

result = orchestrate_field_voices(field_voices)
print(result)
🧠 Core Design
1. Classification-first

All decisions start from classification:

AUTO_OK
REVIEW
ESCALATE
UNKNOWN
IGNORE
2. Execution layer

Protocol Engine decides:

auto execution
human review
unknown handling
3. Learning layer

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
🔄 Evolution

The system improves over time:

Unknown cases are logged
Patterns are extracted
New protocols are created
🧱 System Position

This is the execution layer of a larger system:

RNC → input validation (external)
Protocol Engine → execution (this repo)
Learning → evolution (this repo)
⚠️ Design Principles
No manual decision in execution layer
Unknown is not failure
Exceptions must become rules
📌 Status

Experimental / evolving system

📜 License

MIT
