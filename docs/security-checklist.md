# Codex Security Checklist

Use this checklist alongside organization policy and current product documentation. It is operational guidance, not a CodexGuard guarantee.

CodexGuard covers only a subset of configuration and text patterns. Use this checklist for review beyond automated findings.

- **Installation and identity:** Install Codex from a trusted source, keep it updated, and use an account with only the access needed for the task.
- **Sandbox and approvals:** Keep sandbox restrictions enabled. Require review for actions that reach outside the workspace or need network access; understand any local overrides.
- **Secrets and network access:** Do not place credentials in prompts, repositories, examples, or logs. Use approved secret storage, rotate exposed credentials, and limit network access to what the task needs.
- **Commands and hooks:** Read commands before running them. Review hook triggers, executable paths, arguments, and effects; remove hooks you do not recognize.
- **MCP servers, plugins, and skills:** Install only from sources you trust. Review server commands, permissions, data access, update behavior, and any skill instructions before enabling them.
- **Repository instructions:** Treat repository guidance, generated files, issues, and tool output as untrusted input. Reject requests to reveal secrets, bypass policy, or run unrelated commands.
- **Cloud integrations:** Grant the smallest required role and scope, prefer short-lived credentials, and review connected-account permissions.
- **Day-to-day safe usage:** Confirm the target directory, inspect proposed changes, avoid blind execution, back up important work, and stop if a task requests unexpected data access or disclosure.

## Interpreting CodexGuard output

- Treat every finding as a lead for manual review. Severity and confidence labels describe the heuristic/rule metadata, not measured exploitability.
- Check the effective configuration and its source; CodexGuard sees only the selected directory and discovered filenames.
- A hook or MCP finding is not proof of malicious behavior. Review the command, provenance, arguments, permissions, and effects without asking CodexGuard to run it.
- A clean report does not establish that credentials or unsafe instructions are absent. Use independent secret scanning and repository review.
