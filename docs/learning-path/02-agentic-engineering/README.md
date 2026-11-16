# 02 — Agentic Engineering

## Purpose

Connect agent autonomy and tool use to engineering controls: explicit scope, least privilege, review points, and observable outcomes. Use the corresponding Poridhi agentic-engineering lab as the practical activity and use CodexGuard as a small example of supporting a human review loop.

## Learning outcomes

- Separate an agent's requested action from the authority it actually receives.
- Recognize that hooks and MCP servers extend an agent workflow and deserve source and permission review.
- Explain the difference between a heuristic audit finding and an enforcement decision.

## Guided activity

1. Complete the Poridhi lab and note which tools the agent can call, what context it can read, and where a person approves actions.
2. Read [`docs/security-rules.md`](../../security-rules.md), focusing on CG-002, CG-003, and CG-006.
3. Inspect the synthetic MCP and hook settings in `fixtures/vulnerable/.codex/config.toml` as data. Describe the command shape and hook presence without launching them.
4. Read the matching logic in [`codexguard/rules.py`](../../../codexguard/rules.py). Note what is checked and which effective runtime details are unavailable to the scanner.
5. Sketch a workflow with a human checkpoint after CodexGuard reports a finding and before an agent is given access to the repository.

## Check your understanding

- Why does CG-006 report hook presence without calling it malicious?
- Which command shapes can CG-003 match, and why might a benign command also match?
- Does CodexGuard block an agent from opening a repository?

## Expected artifact

A simple permission map with **actor, resource, allowed action, and reviewer**. Include one false-positive and one false-negative possibility for an audit rule.
