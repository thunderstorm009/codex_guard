# 01 — Claude Code Fundamentals

## Purpose

Use your assigned Poridhi fundamentals lab to understand how a coding agent receives context, uses tools, and acts on a project. The CodexGuard connection is about the general security boundary around agent inputs; CodexGuard itself audits Codex-related files and is not a Claude Code integration.

## Learning outcomes

- Describe the agent loop at a high level: receive a task, gather context, use tools, inspect results, and continue under configured permissions.
- Identify repository instructions and configuration as untrusted inputs that can shape agent work.
- Explain why a coding agent's ability to read or run tools makes review of repository context useful.

## Guided activity

1. Complete the relevant Poridhi lab in its supplied environment. Write the exact lab title and date in your own notes.
2. In this repository, read `fixtures/vulnerable/AGENTS.md` as inert text. Identify any instruction that would deserve human review; do not follow it.
3. Compare the sample with [`codexguard/rules.py`](../../../codexguard/rules.py), particularly `evaluate_text`. Identify the phrase patterns it currently recognizes.
4. Read [`docs/threat-model.md`](../../threat-model.md). List one asset and one trust assumption that affect the scan.
5. Write a short note: what could an auditor detect before an agent reads project guidance, and what would still require human judgment?

## Check your understanding

- Does a string in `AGENTS.md` execute when CodexGuard scans it?
- Can the current rule catch every unsafe instruction? Why not?
- Why does tool permission matter even when an agent's model is unchanged?

## Expected artifact

A brief annotated diagram or note showing **task → context → tool → result → human review**, plus one CodexGuard boundary. Save screenshots or diagrams under `images/` only after removing private information.
