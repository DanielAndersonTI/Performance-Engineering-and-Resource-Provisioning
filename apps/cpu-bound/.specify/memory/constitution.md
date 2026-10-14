<!--
Sync Impact Report
Version: 0.1.0 draft -> 1.0.0 ratified (initial constitution approved by the user)
Modified principles: five project principles established for scope, safety, gated TDD,
measurement integrity, and maintainability.
Added sections: Technology Constraints; Security, Performance, and Experiment Constraints;
Workflow and Review Gates; Governance.
Removed sections: None.
Templates reviewed: .specify/templates/spec-template.md, plan-template.md, and
tasks-template.md reviewed; no changes required before first feature artifacts exist.
Follow-up: JDK version, web framework, build tool, and request/response contract remain undecided.
-->

# CPU-Bound Prime Service Constitution

## Core Principles

### I. Assignment-Aligned Scope
This project MUST remain a backend-only web application whose primary operation
counts prime numbers up to a caller-provided limit. It MUST serve the assignment's
CPU-bound experiment and MUST NOT acquire unrelated product features without the
user's explicit approval.

### II. Bounded and Safe Work
Every externally supplied value that controls computation MUST be validated and
subject to an explicit upper bound. Invalid values MUST produce an explicit error;
the service MUST NOT silently reinterpret, clamp, or accept invalid work. Limits
must be specified and justified before implementation so a request cannot cause
unbounded CPU or memory consumption.

### III. Human-Gated Test-Driven Development
Each task MUST follow RED, GREEN, and REFACTOR in order. RED adds or updates tests
only and must demonstrate failure for the intended missing behavior. The user must
review and approve RED before production implementation. GREEN implements only
what is needed to pass the approved tests and must be reviewed before refactoring.
REFACTOR MUST preserve specified behavior, and relevant tests must pass afterward.
The assistant MUST pause for user review after every phase and MUST NOT start the
next phase or task until the user approves.

### IV. Reproducible Measurement
End-to-end response latency, throughput, failures, and timeouts MUST be measured
by a load generator outside the VM. VM CPU and memory utilization MUST be collected
using infrastructure-side monitoring. Unit tests MUST verify functional behavior,
not machine-dependent latency targets. Application instrumentation MUST be bounded
and MUST NOT materially distort the workload being measured.

### V. Simplicity and Maintainability
The application MUST use Java and remain runnable, testable, understandable, and
maintainable. The design MUST use the simplest structure that meets the specification.
DDD, unnecessary abstractions, databases, authentication, frontend code, and other
unrequested capabilities are out of scope unless the user approves a justified need.

## Technology Constraints

- Language: Java, as agreed by the user.
- JDK version, web framework, build tool, and test libraries: pending user review
  before the implementation plan is finalized.
- The application is a standalone HTTP backend; persistence is not currently required.
- Internal source code and documentation must be in English. Course deliverables may
  use the language and format required by the professor.

## Security, Performance, and Experiment Constraints

- Validate request inputs, return explicit errors, and avoid exposing stack traces or
  sensitive information in client responses.
- Keep computational work bounded. Select and document the maximum accepted limit
  before implementing the endpoint; do not choose a limit based on an unverified
  assumption about VM capacity.
- Keep behavior deterministic for a given valid input so correctness can be tested
  and experiment results can be interpreted.
- Keep application-side measurement lightweight. Use external client measurements
  for end-to-end latency and throughput, and infrastructure tools for VM resource use.
- Record relevant runtime and experiment settings. Account for JVM warm-up before
  comparing measured runs.

## Workflow and Review Gates

- Spec Kit requirements, specification, implementation plan, and medium-sized tasks
  MUST be reviewed with the user before implementation begins.
- Each task MUST be completed as a full RED → user review → GREEN → user review →
  REFACTOR → validation → user review cycle.
- Tests MUST cover specified successful behavior, invalid input, boundaries, and
  relevant HTTP contract behavior.
- After refactoring, run the focused tests and relevant regression checks. Report
  the actual commands and results; do not claim unrun validation.
- Explain each completed phase briefly and offer the user clear next-step choices.
- Do not create commits unless the user explicitly requests or approves them.

## Governance

The user has final authority over requirements, technical choices, tests, and acceptance.
Any change that affects scope, API behavior, architecture, resource limits, or this
constitution requires user review before it is treated as approved. Amendments to this
constitution must be recorded, reviewed with the user, and reflected in the semantic
version. No task may bypass the review gates defined above.

**Version**: 1.0.0 | **Ratified**: 2026-10-13 | **Last Amended**: 2026-10-13
