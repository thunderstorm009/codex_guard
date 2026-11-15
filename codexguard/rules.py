"""Heuristic CodexGuard security rules and secret redaction."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .constants import SEVERITIES

SECRET_PATTERNS = [
    re.compile(r"(?i)(\b[A-Z0-9_-]*(?:api[_-]?key|access[_-]?token|auth[_-]?token|token|password|passwd|secret)\s*[=:]\s*)(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s,;]+)"),
    re.compile(r"(?i)(--?(?:api-key|access-token|auth-token|token|password|secret)\s+)(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s,;]+)"),
    re.compile(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@"),
    re.compile(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk_(?:live|test|proj)_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"),
]


def redact(value: str) -> str:
    """Redact common credential formats before evidence enters a finding."""
    result = value
    for pattern in SECRET_PATTERNS:
        if pattern.groups:
            result = pattern.sub(lambda match: match.group(1) + "[REDACTED]", result)
        else:
            result = pattern.sub("[REDACTED]", result)
    return result


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    severity: str
    confidence: str
    description: str
    why: str
    recommendation: str


SEVERITY_RANK = {severity: index for index, severity in enumerate(SEVERITIES)}


def load_rules(path: Optional[Path] = None) -> List[Rule]:
    """Load rule metadata from JSON, or the bundled rules file by default."""
    rules_path = path or Path(__file__).resolve().parent / "security_rules.json"
    with rules_path.open("r", encoding="utf-8") as handle:
        entries = json.load(handle)
    rules = []
    for entry in entries:
        severity = str(entry["severity"]).upper()
        confidence = str(entry.get("confidence", "LOW")).upper()
        if severity not in SEVERITIES or confidence not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError("rule severity or confidence is invalid")
        rules.append(Rule(
            rule_id=str(entry["rule_id"]), name=str(entry["name"]), severity=severity,
            confidence=confidence,
            description=str(entry["description"]), why=str(entry["why"]),
            recommendation=str(entry["recommendation"]),
        ))
    return rules


def _walk(value: Any, prefix: str = "") -> Iterable[tuple]:
    if isinstance(value, dict):
        for key, child in value.items():
            location = "{}.{}".format(prefix, key) if prefix else str(key)
            yield from _walk(child, location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, "{}[{}]".format(prefix, index))
    else:
        yield prefix, value


def _finding(rule: Rule, file: str, location: str, evidence: str, severity: Optional[str] = None) -> Dict[str, str]:
    return {
        "rule_id": rule.rule_id,
        "rule_name": rule.name,
        "severity": severity or rule.severity,
        "assessment": "Heuristic match; verify the effective behavior in context.",
        "confidence": rule.confidence,
        "title": rule.name,
        "file": file,
        "location": location,
        "description": rule.description,
        "evidence": redact(evidence)[:500],
        "why_it_matters": rule.why,
        "recommendation": rule.recommendation,
    }


def evaluate_config(config: Dict[str, Any], file: str, rules: Optional[List[Rule]] = None) -> List[Dict[str, str]]:
    """Evaluate parsed Codex TOML settings and redact evidence."""
    rule_map = {rule.rule_id: rule for rule in (rules if rules is not None else load_rules())}
    findings = []
    flat = list(_walk(config))
    for location, value in flat:
        key = location.lower().split(".")[-1]
        normalized = str(value).lower() if not isinstance(value, (dict, list)) else ""
        unsafe_sandbox_field = key in ("sandbox_mode", "sandbox") or (key == "mode" and "sandbox" in location.lower())
        if rule_map.get("CG-001") and unsafe_sandbox_field and normalized in ("danger-full-access", "unsafe", "disabled", "none", "false"):
            findings.append(_finding(rule_map["CG-001"], file, location, "{}={}".format(location, value)))
        secret_match = any(pattern.search("{}={}".format(location, value)) for pattern in SECRET_PATTERNS)
        if rule_map.get("CG-005") and secret_match:
            findings.append(_finding(rule_map["CG-005"], file, location, "{}={}".format(location, value)))
    approval_policy = config.get("approval_policy")
    if rule_map.get("CG-002") and str(approval_policy).lower() == "never":
        sandbox_mode = config.get("sandbox_mode")
        sandbox_text = str(sandbox_mode) if sandbox_mode is not None else "not specified"
        severity = "MEDIUM" if str(sandbox_mode).lower() == "danger-full-access" else "LOW"
        findings.append(_finding(
            rule_map["CG-002"], file, "approval_policy",
            "approval_policy=never; sandbox_mode={}".format(sandbox_text), severity=severity,
        ))
    mcp = config.get("mcp_servers", {})
    servers = mcp.items() if isinstance(mcp, dict) else enumerate(mcp) if isinstance(mcp, list) else []
    for server_name, server in servers:
        if not isinstance(server, dict):
            continue
        command_parts = [server.get("command", "")]
        args = server.get("args", [])
        command_parts.extend(args if isinstance(args, list) else [args])
        command = " ".join(str(part) for part in command_parts)
        if rule_map.get("CG-003") and re.search(
            r"(?:\b(?:sh|bash|zsh)\s+-c\b|curl\b.*\|\s*(?:sh|bash)|wget\b.*\|\s*(?:sh|bash)|python(?:3)?\s+-c\b)",
            command,
            re.I,
        ):
            findings.append(_finding(rule_map["CG-003"], file, "mcp_servers.{}.command".format(server_name), command))
    hooks = config.get("hooks")
    if rule_map.get("CG-006") and hooks not in (None, False, "", [], {}):
        findings.append(_finding(rule_map["CG-006"], file, "hooks", "hooks are configured"))
    return findings


def evaluate_text(text: str, file: str, kind: str, rules: Optional[List[Rule]] = None) -> List[Dict[str, str]]:
    """Evaluate instruction/environment text without interpreting or executing it."""
    rule_map = {rule.rule_id: rule for rule in (rules if rules is not None else load_rules())}
    findings = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if rule_map.get("CG-005") and any(pattern.search(line) for pattern in SECRET_PATTERNS):
            findings.append(_finding(rule_map["CG-005"], file, "line {}".format(line_number), line.strip()))
        if kind == "environment" and rule_map.get("CG-004") and re.search(r"(?i)^\s*(?:export\s+)?CODEX_HOME\s*=", line):
            findings.append(_finding(rule_map["CG-004"], file, "line {}".format(line_number), "CODEX_HOME override is configured"))
        if kind == "instructions" and rule_map.get("CG-007") and re.search(
            r"(?i)(ignore (?:all )?(?:previous|prior) instructions|send .*?(?:secret|token|credential)|curl\b.*\|\s*(?:sh|bash)|exfiltrat)", line
        ):
            findings.append(_finding(rule_map["CG-007"], file, "line {}".format(line_number), line.strip()))
    return findings
