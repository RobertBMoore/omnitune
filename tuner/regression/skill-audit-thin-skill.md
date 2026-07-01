---
class: skill-audit
mode: A
---
# Audit target — a thin SKILL.md

A minimal skill file to audit against the current model's rubric:

    ---
    name: summarize-thread
    description: Summarizes a thread.
    ---
    Summarize the thread. Be concise.

**Baseline:** Mode A should flag the weak trigger `description` (too generic to route on), the missing structure/steps, and the absent success criteria — a handful of medium findings, no Critical. The floor-rule verdict stays "revise," not "Critical — do not pass." A rubric change that silences the trigger-fidelity finding is exactly the drift this baseline catches.
