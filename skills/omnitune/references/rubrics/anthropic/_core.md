---
name: rubric-core
description: Model-invariant prompt-engineering rules shared by every per-model rubric in the omnitune library. Read this first, then apply the session model's rubric for model-specific calibration.
applies_to: current Claude models (4.x family)
lastReviewed: 2026-06-14
---

# Rubric Core — model-invariant rules

The prompt-engineering rules that hold across current Claude models. Each per-model rubric (`claude-<model>.md`) reads this core first, then layers its model-specific calibration (effort defaults, literalness, tool-triggering, context window, house defaults) on top.

Both modes use this file:
- **Mode A (audit)** scores a target file against these rules; each finding quotes a section + rule number (e.g. "Core §1.2").
- **Mode B (rewrite)** rewrites a prompt to satisfy them; the QA loop scores the draft against them.

Where a per-model file says a rule is "HIGH severity here," that model's behavior makes the rule especially load-bearing.

## 1. Instruction hygiene
1. **State scope explicitly.** "Apply this formatting to every section, not just the first." A single example with no declared pattern is applied only to the example.
2. **Positive framing over negative.** Replace "Do not use markdown" with "Write in flowing prose paragraphs." Flag stacks of `NEVER`/`DO NOT`/`AVOID` with no positive counterpart.
3. **Calm directive register.** "Use this tool when…" beats "CRITICAL: You MUST…". Flag all-caps shouting and `MUST`/`CRITICAL`/`ABSOLUTELY` where calm direction would do. **Exception:** a genuinely safety-critical invariant (destructive action, PII, a fail-closed clause) warrants emphasis.
4. **Add the "why" behind arbitrary-feeling constraints.** "Never use ellipses — a text-to-speech engine reads this aloud and can't pronounce them." Motivation generalizes to adjacent cases.
5. **Request "above and beyond" explicitly.** Vague "make it great" yields minimum-viable output. For more: "Include as many relevant features and interactions as possible. Go beyond the basics."
6. **No hedge words on load-bearing steps.** "Probably," "consider," "if possible," "when appropriate" read as optional. Mandatory steps take imperative verbs: "Run X," "Read Y first." Flag undisciplined "should"/"must" mixing.
7. **Golden rule (colleague test).** If a colleague with minimal context would be confused, the model will be too. Flag rules assuming unstated conventions or insider jargon.
8. **Declare the verbosity target.** Models calibrate length to judged complexity, so an unstated target yields unpredictable length. For stability: "Provide concise, focused responses; skip non-essential context."

## 2. Structure
1. **XML tags for distinct content types.** Wrap instructions/context/examples/data in named tags (`<instructions>`, `<context>`, `<examples>`, `<input>`). Flag examples spliced into prose with no delimiters.
2. **Long data at the top, the ask at the end.** For large inputs (20k+ tokens) this materially improves quality, especially multi-document. Flag files that lead with instructions then dump reference material below the ask.
3. **Frontmatter is a contract.** `name` and `description` must be specific enough to trigger correctly; automation reads optional fields (`lastReviewed`, `sources`, `allowed-tools`) — keep them current. Flag descriptions under ~40 words or third-person-passive with no trigger phrasing.
4. **Consistent, descriptive tag names.** Reusing `<example>` is fine; inventing `<ex>`/`<sample>`/`<demo>` inconsistently causes parsing ambiguity.
5. **Match prompt style to desired output.** Prompt format influences output format; removing markdown from the prompt reduces markdown in the output. Flag heavy-markdown prompts whose outputs should be prose or JSON.
6. **Ground long-doc tasks in quotes.** Ask for relevant passages in `<quotes>` before answering; pair with `<answer>`. Cuts noise, improves grounding.
7. **Sequential numbered steps when order matters.** Flag multi-step workflows buried in paragraphs — undeclared steps get skipped.
8. **`<document index="n">` for multi-document inputs**, each with `<document_content>` and `<source>` subtags, for clean citation.

## 3. Tool use
1. **Describe when and how to use each tool, not just what.** Tools with vague trigger conditions get skipped.
2. **Parallelize independent tool calls.** Reading three files is one batch, not three round-trips. State: "Make independent calls in parallel; never guess missing parameters."
3. **Never guess missing parameters.** If a required parameter isn't available or inferable, ask — don't fabricate. State this explicitly.
4. **Sequence only when dependent.** If B needs A's output, serialize; otherwise parallel. Flag habitual serialization with no real dependency.
5. **"Suggest" vs "make the changes" is load-bearing.** Literal models read "Can you suggest changes?" as suggestions, not edits. For action: "Change this function…" / "Make these edits…".
6. **Effort is the main lever on tool-use frequency** (the exact relationship is per-model). Reach for effort before adding "use the tool more" prose.
7. **Describe behavior on tool failure.** "Report it and stop" vs "retry once then stop" vs "fall back to tool X." Specify it, or error handling is unpredictable.
8. **Narrow `allowed-tools`.** Declare the minimum the target actually uses. Broad access widens blast radius and dilutes tool relevance.

## 4. Thinking & reasoning
1. **Prefer effort over prescriptive chain-of-thought.** "Think thoroughly" often beats a hand-written step plan. (Effort defaults and level calibration are model-specific — see your model file.)
2. **Match effort to workload.** Higher for coding/agentic and intelligence-sensitive work; lower only for scoped, latency-sensitive work.
3. **If reasoning feels shallow, raise effort — don't prompt around it.**
4. **Steer adaptive thinking when it over-fires.** "Thinking adds latency; use it only when it will meaningfully improve quality — typically multi-step reasoning. When in doubt, respond directly."
5. **Ask for self-verification before finalizing.** "Before you finish, verify your answer against [criteria]." Cheap; catches coding/math errors.
6. **Commit to an approach once chosen.** "Choose an approach and commit; avoid revisiting decisions unless new information directly contradicts your reasoning."
7. **Skip thinking for simple queries.** Factual lookups, classification, summarization gain nothing and pay latency.
8. **Use `<thinking>` tags in few-shot examples** to show the reasoning pattern; pair with `<answer>` to separate work from output.

## 5. Known failure modes
1. **Overengineering.** "Only make changes directly requested or clearly necessary. Don't add features, refactor, or improve beyond what was asked."
2. **Hard-coding to pass tests.** "Implement a solution correct for all valid inputs, not just the test cases."
3. **Hallucinating about unopened code.** "Never speculate about code you have not opened. If the user references a file, read it before answering."
4. **Subagent over/under-use.** "Use subagents for parallel, isolated-context, or independent workstreams. For simple/sequential/single-file work, work directly." (Default tendency is per-model.)
5. **Destructive action without confirmation.** List which actions need confirmation; forbid `--no-verify`/`--force` shortcuts. Safety-critical — emphasis warranted here (the §1.3 exception).
6. **Tempfile sprawl.** "Remove any temporary files or scripts you create for iteration at the end of the task."
7. **Code-review recall drops from faithful filtering.** "Only report high-severity issues" makes the model investigate fully then self-filter below the bar — precision up, recall down. For coverage: "Report every issue, including low-severity and uncertain ones, with confidence + severity. Do not filter at this stage."
8. **User-facing status scaffolding backfires.** Current models give regular high-quality updates; flag and remove "after every 3 tool calls, summarize" scaffolding.
9. **Anti-laziness prompts overtrigger.** "If in doubt, use the tool" / "default to [tool]" now overuse. Replace with "Use [tool] when it would enhance your understanding of the problem."
10. **Mirroring user mistakes.** "Fix this bug" on a multi-bug snippet fixes only the named one. For broader fixes: "Fix this bug and any related bugs in the same function."

## 6. Skill & agent idioms
1. **Frontmatter is the trigger contract.** `name` matches the directory; `description` carries enough lexical signal that the Skill tool fires on user intent.
2. **List trigger phrases in the description.** End with "Triggers on prompts like: '…', '/slash-command'." Vague descriptions never fire reliably.
3. **Agent files are subagent system prompts** loaded into isolated context with no memory of the caller. Restate constraints, working directory, and success criteria inside the file.
4. **Subagents don't share caller state.** Pass everything in the dispatch prompt: paths, branch/SHA, success criteria.
5. **Skill invocation is blocking.** When a skill matches, invoke it before any other response, including clarifying questions.
6. **General-purpose subagents for investigation, specialized for execution.** Don't cross the two.
7. **Before-you-begin clarifying-question gate.** Literal models make guessing costly — ask one question rather than ship the wrong artifact.
8. **Self-review before returning.** Re-check work against the dispatch's success criteria (draft → review against criteria → refine).
9. **Concise reports, not essays.** Status (DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT), what was done, key findings, absolute paths. No preamble.
10. **Scope your writes.** Don't create files the task doesn't require.
11. **Keep reference files focused** (~250 lines each). Split large references and link from the entry point.
12. **Version references with frontmatter `lastSynced` / `lastReviewed`.** Update on every refresh.

## Audit severity cheat sheet (Mode A)
Rank findings by blast radius:
- **CRITICAL** — §5.3 / §5.5 (hallucinating unopened code, destructive actions without confirmation). Safety and correctness.
- **HIGH** — §1.1 / §1.2 / §1.3 (scope ambiguity, negative-only framing, aggression) and §3.1 / §3.5 (vague tool triggers, suggest-vs-act). Wrong output on common tasks.
- **MEDIUM** — §4 thinking mistuning, §6.1 / §6.2 (frontmatter weakness, missing triggers). Reliability and trigger rate.
- **LOW** — §2 structure drift, §6.10 / §6.11 (write scoping, file length). Polish, not blocker.

## How Mode A aggregates (hardened)
The report is driven by **per-dimension findings**, not a single average. The overall verdict uses a **floor rule, not an arithmetic mean**: any dimension scoring 1 (Critical) caps the overall verdict at **"Critical — do not pass,"** regardless of how strong the other dimensions are. A safety-critical finding must never be averaged away. Dimensions that don't apply are recorded **N/A** and excluded entirely.

## Delegation defaults (Mode C teams)
When Mode C composes an orchestration team, this rubric supplies the **fan-out posture** — never the team roster. Two levers, two owners:
- **Who runs what** (per-role model + effort) comes from `references/delegation-tiers.md`, keyed to the model each role *runs on*, not the generating session's model. The provider-general frame: orchestrator = frontier tier; builder/implementer = workhorse tier; read-only explorer/auditor = cheap tier. A tiered team beats an all-one-model team by a wide margin (the 90.2% result); defaulting every role to one model is a finding.
- **Fan-out posture** — more vs fewer subagents, blocking vs async dispatch, long-lived vs disposable workers — is model-specific and lives in each per-model rubric's Delegation-defaults block. `_core §5.4` sets the shared floor ("subagents for parallel/isolated/independent work; direct for simple/sequential/single-file"); the per-model file sets the *degree*. Where a per-model file reverses this floor, that file wins.
The correctness invariant — one writer per file/branch, parallel writers on isolated worktrees — is not a posture; it holds on every model (topology point X5).
