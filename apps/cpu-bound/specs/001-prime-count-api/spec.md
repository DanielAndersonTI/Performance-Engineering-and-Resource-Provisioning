# Feature Specification: CPU-Bound Prime Count Service

**Feature Branch**: `001-prime-count-api`

**Created**: 2026-10-13

**Status**: Draft — awaiting user review

**Input**: Create a CPU-bound backend that returns the number of primes up to a validated configurable limit.

## User Scenarios & Testing

### User Story 1 - Request a Prime Count (Priority: P1)

As an experimenter or load generator, I want to request the number of primes up to a chosen limit so I can exercise a controlled, repeatable CPU workload and observe the application's behavior under demand.

**Why this priority**: This is the application's sole required workload and the basis for the CPU-bound assignment experiment.

**Independent Test**: Submit valid limits and verify the returned limit and prime count against known mathematical results. Submit invalid and out-of-range inputs and verify they are rejected without starting unbounded work.

**Acceptance Scenarios**:

1. **Given** a valid limit from zero through the configured maximum, **When** a client requests a prime count, **Then** the service returns the requested limit and the exact count of primes less than or equal to it.
2. **Given** a limit of zero or one, **When** a client requests a prime count, **Then** the service returns a count of zero.
3. **Given** a valid request, **When** the service responds, **Then** the response contains the limit and count only, not the list of primes.
4. **Given** a missing, malformed, fractional, negative, or above-maximum limit, **When** a client submits the request, **Then** the service rejects it with a client error and does not begin the prime-counting workload.
5. **Given** the maximum is configured to a permitted value, **When** a client requests that exact value, **Then** the request is accepted; a value above it is rejected.

### Edge Cases

- Limits zero and one are valid and produce a count of zero.
- The configured maximum is inclusive.
- Missing, non-numeric, fractional, negative, and above-maximum limits are rejected.
- Invalid requests must not trigger the computational workload.
- Error responses must not expose stack traces, internal implementation details, or sensitive information.
- Repeated requests with the same valid limit produce the same count.

## Requirements

### Functional Requirements

- **FR-001**: The service MUST provide a backend request that counts prime numbers up to and including a supplied integer limit.
- **FR-002**: The service MUST return the supplied limit and the exact prime count, without returning the full prime list.
- **FR-003**: The service MUST accept limits from zero through an operator-configured maximum, inclusive.
- **FR-004**: The initial default maximum MUST be 1,000,000 and MUST be configurable without changing application source code.
- **FR-005**: The service MUST reject missing, malformed, fractional, negative, and above-maximum limits with a client-error response.
- **FR-006**: The service MUST validate the limit before starting computation and MUST NOT silently clamp or reinterpret invalid values.
- **FR-007**: Error responses MUST provide a safe indication of invalid input and MUST NOT reveal stack traces or internal implementation details.
- **FR-008**: For a given valid limit, the service MUST return a deterministic result.
- **FR-009**: The prime-count operation MUST remain bounded by the configured maximum and MUST avoid generating or transmitting the prime list.
- **FR-010**: The service MUST be runnable locally and reachable by a load generator outside the VM when deployed for the course experiment.

### Key Entities

- **Prime-count request**: A transient request containing an integer upper limit.
- **Prime-count result**: A transient response containing the requested limit and the number of primes less than or equal to it. No persistence is required.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Known input cases produce exact results, including zero primes for limits zero and one, one prime for limit two, and four primes for limit ten.
- **SC-002**: A request at the configured maximum is accepted, while a request above the maximum is rejected before computation.
- **SC-003**: Valid responses contain the requested limit and the correct count, and do not contain a prime list.
- **SC-004**: Invalid input cases are rejected with a client error and without exposing stack traces or internal details.
- **SC-005**: During course experiments, an external load generator records response latency, throughput, failures, and timeouts while VM monitoring records CPU and memory use across at least four provisioning scenarios and multiple demand levels per scenario.

## Assumptions

- The application is a backend-only service; no frontend, database, authentication, or unrelated business functionality is required.
- A valid limit is inclusive, and zero is permitted.
- The default maximum is 1,000,000; its configurable value may be adjusted only after local evidence and user review.
- The response will use a structured representation, with the precise HTTP method, route, field names, and error schema defined in the implementation plan and reviewed before coding.
- End-to-end latency and throughput are measured externally; VM CPU and memory are collected using infrastructure-side monitoring.
- Performance results are experiment observations, not fixed timing guarantees in functional tests.
