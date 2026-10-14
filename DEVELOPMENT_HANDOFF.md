# Development Handoff — Demand, Provisioning, and Performance

This file is the internal source of truth for the agreed development workflow and its current progress. It is written in English because it is an internal project document, not a professor-facing deliverable. Update the progress log whenever a stage is completed so another AI assistant can continue without requiring the user to repeat prior decisions.

## Project purpose

Build three small, well-engineered web backend applications for the course assignment. Each application must represent a distinct computational profile:

1. CPU-bound
2. Memory-bound
3. IO-bound

The applications are experimental instruments for studying how workload demand and VM resource provisioning affect application performance and infrastructure utilization. They are not intended to be feature-complete commercial products.

## Confirmed decisions

- Use **Java** for all three applications.
- Keep each application in its own directory within this repository. Proposed layout:
  - `apps/cpu-bound/`
  - `apps/memory-bound/`
  - `apps/io-bound/`
- Develop **one application at a time** and finish its tasks before starting the next application.
- Use Spec Kit to define requirements, specifications, and implementation tasks before implementing each application.
- Do not use DDD/domain modeling unless a later, explicit requirement makes it necessary. The user has chosen to leave it out.
- Tasks must be cohesive and medium-sized: not trivial micro-tasks, and not so large that they combine an entire application or multiple reviewable behaviors.
- Complete each task through the full **RED → human review → GREEN → human review → REFACTOR → validation → human review** cycle before proceeding to the next task.
- At each review point, briefly explain what was done and present clear options for the user to approve, request changes, or inspect further. Do not continue to the next phase until the user evaluates and authorizes it.
- The user remains the decision-maker for requirements, architecture choices, tests, and acceptance. Do not invent requirements or silently broaden task scope.
- Aim for secure, correct, runnable, maintainable, and appropriately performant code. Keep the design as simple as possible while meeting the assignment's experimental goals; do not add commercial-product features without approval.
- Do not create commits unless the user explicitly requests or approves them.
- All code and internal documentation that will **not** be submitted to the professor must be in English, including filenames. Professor-facing assignment documentation may follow the language and format required by the course.

## Assignment requirements to preserve

- Develop three web applications, backend only, each with a different predominant profile: CPU-bound, memory-bound, or IO-bound.
- Run and test all three applications locally.
- Configure a VirtualBox VM using the professor's provided guide, deploy one application, and demonstrate it running.
- Demonstrate the applications running on the LCC as required by the professor.
- Generate load from **outside** the VM.
- Run several demand levels for each provisioning scenario and use **at least four provisioning scenarios**. The assignment's four-scenario requirement takes precedence over the report template's reference to at least two.
- Collect application metrics, including response latency/time and throughput (requests per second), as applicable. Record failures/timeouts too.
- Collect VM infrastructure metrics, including CPU utilization and memory consumption/utilization.
- Compare scenarios using plots and explain how demand, provisioned resources, performance, and utilization relate, including observed performance degradation.
- Preserve raw experiment data and document methodology, results, and conclusions using the professor's report template.
- Each group member must submit the delivery form once.

## Measurement and engineering guidance

- Measure client-observed latency and throughput at the external load generator. Measurements only inside the application omit client-to-server effects and are not the primary end-to-end result.
- Measure VM CPU and memory using suitable monitoring on the VM/host side. Application-side instrumentation may be added only when it is useful, bounded, and does not materially distort the workload.
- The applications must provide controlled, bounded operations that exercise their intended profiles. Validate inputs and cap work/allocation so tests cannot trigger uncontrolled resource use.
- Keep experiment settings and test conditions reproducible. Record VM CPU/vCPU and memory settings, load-generation location/tool, load levels, run duration, repetitions, warm-up, and relevant runtime configuration.
- Do not encode environment-dependent latency targets as ordinary unit-test pass/fail criteria. Use functional tests for behavior and controlled load experiments for performance conclusions.
- For Java measurements, keep the JDK/runtime and relevant JVM configuration consistent and record them. Account for JVM warm-up before collecting comparable measurements.
- Compare the three applications primarily as separate demonstrations of resource profiles. Do not assume their absolute performance is directly comparable unless the methodology controls the relevant differences.

## Development workflow for each application

1. **Agree on scope:** identify the computational profile, the minimal useful backend behavior, safety limits, and what the experiment needs to observe. Resolve significant design choices with the user.
2. **Spec Kit requirements and specification:** capture requirements, scenarios, constraints, and testable acceptance criteria in the repository's Spec Kit artifacts. Keep the specification focused on the assignment; do not add an unrelated business domain.
3. **Create medium-sized tasks:** each task should describe its goal, context, constraints, completion criteria, and expected tests. Keep traceability from requirements to tasks and tests.
4. **RED:** add tests for the current task only; run them and confirm they fail for the expected missing behavior. Do not implement production behavior during RED. Explain the tests and request the user's review.
5. **GREEN:** after user approval, implement the minimum behavior needed to pass the approved tests. Run the focused tests and explain the change and results; request review.
6. **REFACTOR:** after user approval, improve structure without changing the specified behavior. Run the focused tests and relevant regression checks; explain the changes and request review.
7. **Finish the task:** update relevant documentation and Spec Kit task status. Proceed only after the user's review and approval.
8. **Finish the application:** run the appropriate tests/build, verify local execution, document how to run it, and record remaining limitations before starting the next application.

The RED/GREEN/REFACTOR stages apply to each task, not to an entire application as one oversized cycle. User review is required after each stage as agreed.

## Not yet decided

Do not silently decide these items. Present a concise recommendation and obtain the user's agreement when they become relevant:

- Which application to develop first. CPU-bound is a reasonable proposed starting point, but is not yet confirmed.
- Java framework, JDK version, build tool, and testing libraries.
- The concrete operation and bounded parameters used to represent each computational profile.
- The external load-generation and infrastructure-monitoring tools.
- Exact VM provisioning levels, demand levels, run durations, and repetition counts.
- How Spec Kit is installed or initialized in this workspace, if it is not already available.
- Any extra application-level metrics endpoint or instrumentation beyond the external and VM-side measurements.

## Proposed repository organization

```text
.
├── apps/
│   ├── cpu-bound/
│   ├── memory-bound/
│   └── io-bound/
├── DEVELOPMENT_HANDOFF.md
├── README.md
└── ...
```

This is a proposed layout, not an instruction to create application files before the user authorizes the first application. Spec Kit's own files and any shared experiment tooling should be placed according to its conventions and the agreed project organization.

## Progress log

### Stage 0 — Agreement and workspace preparation

- **Status:** Complete.
- **Completed:** Recorded the assignment goals, confirmed Java, separate application directories, one-application-at-a-time sequencing, omission of DDD, task sizing expectations, user-reviewed RED/GREEN/REFACTOR workflow, engineering quality goals, measurement guidance, and handoff requirements.
- **Workspace inspection:** The project root contains the existing `README.md` and `LICENSE`; no application source or Spec Kit project files were present at preparation time.
- **Files changed:** Added this internal handoff document only. The existing professor-facing `README.md` was not changed.
- **Not done:** No application, Spec Kit specification/task, source code, test, dependency setup, or experiment tooling has been created or executed.

### Stage 1 — CPU-bound application scoping and Spec Kit setup

- **Status:** Complete; constitution ratified. Feature behavior is still being scoped.
- **Completed:** User authorized starting with the CPU-bound application and selected counting primes up to a configurable limit as its workload. Confirmed `specify` CLI is installed and `specify check` reports it is ready. Initialized Spec Kit with the Copilot integration and PowerShell scripts under `apps/cpu-bound/`.
- **Generated setup:** Spec Kit templates, scripts, workflow, and Copilot skills are under `apps/cpu-bound/.specify/` and `apps/cpu-bound/.github/skills/`. Initialization also generated the root `.vscode/settings.json` with command-specific terminal approvals; inspect before any future edits.
- **Setup safety:** An initial attempt to initialize Spec Kit at the repository root was cancelled by the CLI's non-empty-directory confirmation. It made no changes. Do not use `--force` at the root because existing project files must be preserved.
- **Constitution:** `.specify/memory/constitution.md` in the CPU app directory records the confirmed scope and TDD/review gates. The user reviewed and approved it; it is ratified as version 1.0.0 on 2026-10-13.
- **Validation:** `git diff --check` completed without whitespace errors, and a placeholder scan found no unresolved `[ALL_CAPS]` template tokens in the constitution. No build or tests were run because no application code exists.
- **Files changed/generated:** Added this handoff document, the draft constitution, Spec Kit's CPU-app scaffolding, and `.vscode/settings.json`. The existing `README.md` and `LICENSE` remain untouched.
- **Not done:** No application source, tests, feature specification, implementation plan, task list, dependency setup, or experiment tooling has been created. API response shape, work limit, framework, JDK version, and build tool remain undecided.

### Stage 2 — CPU workload, stack, and feature specification

- **Status:** Specification drafted and quality-checked; awaiting user review.
- **Agreed behavior:** The CPU workload counts prime numbers up to a configurable limit. The response should contain the requested limit and the prime count, not the full list, to avoid adding unnecessary response-transfer work.
- **Agreed safety limit:** Start with a configurable maximum request limit of 1,000,000. Validate locally that this is safe and produces measurable work before VM experiments; revisit only with user review if evidence supports a change.
- **Agreed stack:** Java 21, Spring Boot, and Maven Wrapper. Java 21.0.2 LTS is available locally; Maven and Gradle are not on PATH, so use the project wrapper rather than requiring a global Maven install.
- **Spec Kit artifacts:** Feature directory `apps/cpu-bound/specs/001-prime-count-api/`; specification in `spec.md`; requirements checklist in `checklists/requirements.md`; `.specify/feature.json` points to this feature.
- **Validation:** Reviewed all mandatory spec sections and acceptance criteria; the requirements checklist is complete; no unresolved specification placeholders remain. `git diff --check` reported no whitespace errors.
- **Not done:** No Java source, build project, or Java tests exist. No implementation plan or task list has been created. Exact HTTP method/path, response field names, and error schema remain for the plan/API contract and user review.

### Next stage — User review of the feature specification

- **Status:** Paused at the user's request on 2026-10-13, before the specification was approved.
- **Resume point:** Ask the user to approve or request edits to `apps/cpu-bound/specs/001-prime-count-api/spec.md`. The user has not approved it yet.
- **Next actions after approval:** Draft the implementation plan and API contract using Java 21, Spring Boot, and Maven Wrapper; propose medium-sized tasks that each receive a complete user-reviewed RED/GREEN/REFACTOR cycle. Do not begin application implementation until the plan and tasks are approved.
- **Current code status:** No Java source, Maven project, or test files have been created. No RED phase has started.
- **Current estimate:** Approximately 2–4 more hours of active work for the first locally runnable, tested, refactored, and documented application. VM deployment, load experiments, and the course report are excluded; actual elapsed time depends on review cycles and environment issues.

## Continuation instructions for another assistant

1. Read this file before making changes.
2. Respect all confirmed decisions and preserve the user's review gates.
3. Check the latest progress log and actual workspace state; do not assume that a planned or listed stage is complete unless the log and files confirm it.
4. If a significant design decision is unresolved, ask the user before proceeding. Do not treat approval to start scoping as approval of unreviewed requirements or implementation.
5. At each completed stage, update this file in English with the status, actions, validation performed, files affected, and the next gated action.
