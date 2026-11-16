# CodexGuard Learning Path

This seven-module learning path moves from AI coding-agent fundamentals through local and cloud infrastructure concepts to a source-level understanding of CodexGuard. Each lab stands on its own and links to the original Poridhi module. Read each guide alongside its Poridhi material; the guides explain concepts and connect them to this repository without claiming to reproduce the lab platform's exact steps.

> **Source note:** The supplied Poridhi URLs could not be retrieved as readable lesson content during this documentation pass; the first URL returned a JavaScript application shell. Lab topics come from the module descriptions in the project request, not unverified course-specific steps. Exact course commands, platform outputs, and lesson durations are not invented. Follow the linked Poridhi lesson for its own environment and steps.

![Seven module journey from agent fundamentals to networking, mapped to CodexGuard](../assets/learning-journey.svg)

## Recommended sequence

| # | Lab | Status | Key concepts | CodexGuard connection |
|---:|---|---|---|---|
| 01 | [Claude Code Fundamentals](lab-01-claude-code-fundamentals.md) | **Completed** | Sessions, context, permissions, sandboxing, rollback, project memory. | Repository instruction risk and inert auditing; no Claude-specific implementation. |
| 02 | [Agentic Engineering with Claude](lab-02-agentic-engineering-with-claude.md) | **Completed** | Agent workflows, tools, external integrations, trust, permissions. | MCP definitions, hooks, and configuration heuristics. |
| 03 | [Basic Docker Concepts](lab-03-basic-docker-concepts.md) | In progress | Images, containers, networking, mounts, users, resources. | Actual Docker image and restricted runtime profile. |
| 04 | [AWS Basics](lab-04-aws-basics.md) | In progress | Regions, IAM, EC2, security groups, shared responsibility. | Security workflow context only; no AWS integration. |
| 05 | [Docker Compose](lab-05-docker-compose.md) | In progress | Services, dependencies, networks, volumes, environment. | A deployment pattern that could package a CLI; this repo has no Compose file. |
| 06 | [GitHub Actions with Docker](lab-06-github-actions-with-docker.md) | In progress | CI workflows, jobs, Docker actions, token permissions, supply chain. | Actual local Actions definitions; no hosted result claimed. |
| 07 | [AWS Networking](lab-07-aws-networking.md) | In progress | VPCs, subnets, routes, gateways, security groups, SSH. | Network isolation concepts; no AWS/VPC deployment in this project. |

The statuses above are the learner status supplied for this documentation. They do not certify course completion or describe CodexGuard implementation maturity.

## Why this sequence?

Labs 01–02 build a model of agent context and tool authority. Labs 03 and 05 explain local process isolation and repeatable packaging; Lab 04 adds cloud identity and infrastructure context. Lab 06 shows how checks can run in a repository workflow, while Lab 07 explains network boundaries around remote environments. The practical project connection is made explicit in every lab and summarized in [Learning-to-project mapping](LEARNING-TO-CODEXGUARD.md).

## How to use each guide

Each document follows the same twelve-section format: introduction, overview, objectives, prerequisites, concepts, workflow, step-by-step exercises, security considerations, CodexGuard connection, takeaways, conclusion, and references. A lab workflow diagram is included where it helps. Commands are examples for the learner's own trusted environment; they are not asserted to have been executed in this repository.

## Learning outcomes

At the end of the sequence, a learner should be able to:

- Separate model behavior from the tools, permissions, context, and environment around an agent.
- Explain how local sandbox settings differ from Docker and cloud network boundaries.
- Distinguish a Docker image configuration from runtime controls.
- Describe least privilege in IAM, GitHub Actions, filesystem mounts, and container capabilities.
- Trace CodexGuard from explicit scan root through bounded discovery, parsing, rules, redaction, and reporting.
- Explain why heuristic findings are review leads and why clean output is not proof of safety.

## Continue into the implementation

Read the [Architecture Guide](../architecture.md), [Security Rules](../security-rules.md), [Source Code Guide](../source-code-guide.md), [Security Model](../security-model.md), and [Threat Model](../threat-model.md). A scan audits only supported local file patterns. CodexGuard is not an MCP server, Claude Code extension, AWS service, CI enforcement gate, malware detector, or auto-remediation tool.
