# Development Handoff — Demand, Provisioning, and Performance

This is the internal record of how the work was done and of what is still open. It is written in English because it is not a professor-facing deliverable; `README.md` and `RELATORIO.md` are in Portuguese, as the course requires.

## Status

The assignment's technical work is **complete**: three applications, the virtual machine, four provisioning scenarios measured end to end, raw data, figures, and the results document. What remains is delivery — committing the code, the LCC3 demonstration and the delivery form — plus the open items at the end of this file. **Nothing has been committed**; the user commits personally.

## Working agreement

- **Python**, one shared implementation built on the colleague-authored baseline. The earlier Java / Spring Boot / Spec Kit material at the repository root (`apps/cpu-bound/`) is superseded and is kept only because its removal was never authorized.
- **Language:** code and internal documents in English; professor-facing documents in Portuguese.
- **Commits:** never without explicit approval; the user commits personally.
- **Pace:** short messages, one stage at a time, ask before anything long or expensive.
- **Time budget:** roughly 10 hours in total, including VM setup and the experiments.
- The agreed RED → review → GREEN → review → REFACTOR cycle was followed while the applications were being written. That work is closed; the cycle is no longer an active gate, but the review habit is: do not silently decide design questions, and do not broaden scope.

## Assignment requirements

- Three backend web applications, one per predominant profile: CPU-bound, memory-bound, IO-bound.
- Run and test all three locally.
- Configure a VirtualBox VM from the professor's guide, deploy one application and demonstrate it.
- Demonstrate the applications on the LCC machines.
- **Generate the load from outside the VM.**
- At least **four** provisioning scenarios, each with more than one demand level. The activity statement's four take precedence over the report template's "at least two".
- Collect application metrics (latency, throughput, failures/timeouts) and VM infrastructure metrics (CPU, memory).
- Preserve the raw data; compare scenarios with plots; document methodology, results and conclusions in the professor's template.
- Each group member submits the delivery form once.

## What was built

**One implementation, three applications.** `apps/server.py` holds all three profiles behind a shared `ThreadingHTTPServer`. `apps/cpu/server.py`, `apps/memory/server.py` and `apps/io/server.py` are thin launchers that load it by absolute path — loading it by name would collide, since each launcher is itself `server.py`.

**Contract.** `GET /health` → `{"status": "ok", "profile": ...}`. `GET /work?size=N` → `{"profile", "duration_seconds", "result"}`. Errors: 404 unknown route, 400 invalid `size`, 503 no free work slot, 500 storage failure (IO profile only).

**Profile parameters.** `DEFAULT_SIZE` cpu 10 / memory 32 MiB / io 1024 KiB. `MAX_SIZE` cpu 300 / memory 256 MiB / io 32768 KiB. `DEFAULT_MAX_CONCURRENCY` cpu 32 / memory 4 / io 16. Admission control is a per-instance `threading.BoundedSemaphore`: a request that cannot take a slot is answered immediately with HTTP 503 rather than queueing without bound. The ceilings exist so a load test cannot drive the machine into uncontrolled resource use.

**CPU profile and the GIL.** The baseline hashed a chain of small digests, which stays entirely inside the GIL, so the profile could gain nothing from extra vCPUs — the very relationship the assignment has to measure. `compute_cpu` now hashes a fixed 1 MiB block and writes the digest back into its first 32 bytes. CPython releases the GIL for `hashlib` inputs of 2048 bytes or more, so concurrent requests can occupy several cores; an isolated probe measured ~2.3x scaling for the large-block version against 0.27x for the small-digest version. The workload stays deterministic and bounded.

**Memory profile — do not "optimise" the page loop.** `compute_memory` allocates `size` MiB and then touches one byte per 4 KiB page. The loop looks like waste, because `bytearray()` already faults the pages in C, but it is load-bearing: it yields the GIL every ~5 ms, which is what lets concurrent allocations coexist. Measured in the guest with four concurrent 256 MiB requests: with the loop, 298 ms per request and 1033 MB peak RSS; without it, 288 ms and 265 MB peak RSS — the allocations stop overlapping and the 1 GB scenarios would no longer swap at all. The loop costs about 3% of the request time and produces the central finding of the study. See `RELATORIO.md` §3.4.4.

**IO profile.** Writes `size` KiB to a temporary file, `fsync`s it, and reads it back.

**Tests.** `tests/test_applications.py`, 9 tests: profile identity, per-profile result shape, determinism, default size, invalid-size rejection, unknown route, the shared `--profile` entry point, unknown-profile rejection, and the 503 admission limit. All 9 pass on the host (Python 3.12) and inside the VM (Python 3.10.12). No test asserts latency or throughput — those depend on the machine and belong to the experiments.

**Scripts.** `load_test.py` (external load generator: one thread per client, percentiles by linear interpolation over the full sample, per-kind error classification), `monitor.py` (VM-side sampling into `results/resources.csv`), `run_scenario.py` (host-side sweep of every demand level of one scenario, per-level warm-up, UTC windows written to `results/run_log.csv`), `plot_results.py` (joins resource samples to demand levels through those windows, writes `summary.csv` and the figures), `capture_evidence.py` (reads the provisioning straight from VirtualBox). `scripts/smoke_test.py` is a weaker legacy duplicate of the test suite; deleting it was never authorized.

## The virtual machine

- `Po-2026.2`, Ubuntu Server 22.04 LTS, 12 GB disk, user `daniel`, Python 3.10.12, `python3-psutil` 5.9.0 from apt. There is no `pip` in the guest and none is needed. Code copied to `~/atividade2`.
- Network: NAT, guest address 10.0.2.15, port forwarding `ssh` 2222→22 and `app` 8080→8000.
- Host-side access uses the ed25519 key at `~/.ssh/po_atividade2`. The password helper used once to install it was deleted; every later command is key-based.
- Host: Intel Core i3-6006U, **2 physical cores** (4 logical). The guest, the load generator and VirtualBox's NAT engine share them, and that is the main source of measurement noise.
- **Operational note.** A stale process holding host port 8080 silently disables the VM's port forward for the whole lifetime of the VM: the NAT rule fails to bind at boot, so requests are answered by whatever else owns the port. Check that the port is free before starting the guest. The rule can be restored live with `VBoxManage controlvm "Po-2026.2" natpf1 delete "app"` followed by `natpf1 "app,tcp,,8080,,8000"`.

## The experiment

**Application under test:** memory-bound, size fixed at **256 MiB** per request — the only setting at which a 1 GB guest swaps and a 2 GB guest does not.

**Protocol:** demand levels 1, 2 and 4 concurrent clients (4 is the profile's admission limit, so the rejection path is not part of the measurement); 5 s of unrecorded warm-up plus 40 s measured per level; 120 s request timeout; one repetition; load generated from the **host**; guest sampled every ~0.5 s; each level's UTC window recorded in `run_log.csv`.

**Matrix:** C1 1 vCPU / 1 GB, C2 2 vCPU / 1 GB, C3 1 vCPU / 2 GB, C4 2 vCPU / 2 GB — one variable changed per step.

| scenario | L1 rps | L2 rps | L4 rps | L4 p95 | peak guest swap |
| --- | --- | --- | --- | --- | --- |
| C1 (1 vCPU / 1 GB) | 3.72 | 3.59 | 1.98 | 5128 ms | 507 MB |
| C2 (2 vCPU / 1 GB) | 3.39 | 3.47 | 1.19 | 11616 ms | 545 MB |
| C3 (1 vCPU / 2 GB) | 3.44 | 2.12 | 2.05 | 5633 ms | 0 MB |
| C4 (2 vCPU / 2 GB) | 3.68 | 1.65 | 2.07 | 3545 ms | 0 MB |

**Findings.**

1. **RAM provisioning is the decisive variable.** Both 1 GB scenarios drove the guest into swap (507 MB, 545 MB); both 2 GB scenarios recorded **zero** swap at every level. Peak resident memory was 877–879 MB at 1 GB against 1202–1204 MB at 2 GB.
2. **Extra vCPUs do not help this application.** Guest CPU settles at ~48% of the two-core total in C2 and C4 — about one core — and at 96–99% of the single core in C1 and C3. The second vCPU is never used.
3. **Why: the GIL, and the page loop.** The memory-bound work is pure Python bytecode serialised by the GIL, so throughput is capped at ~3.5 rps and additional demand only accumulates latency; that same serialisation keeps too few requests in flight for the 503 path to trigger. Flat throughput with linearly growing latency is the classic saturated-resource signature (Little's Law).

**Independent confirmation that the matrix was applied during the runs.** The raw samples in `results/resources.csv` record `cpu_count` 1 / 2 / 1 / 2 and the memory peaks quoted above, matching C1–C4 exactly. The scenarios were not merely configured; they were in force while the numbers were taken.

**Evidence.** `capture_evidence.py` was run once per scenario, producing `evidencias/C{1..4}-config.txt` (provisioning summary plus the full `VBoxManage showvminfo --machinereadable`) and `evidencias/C{1..4}-console.png` (guest console, captured in the same boot as the measurement). The user's own `vm-configuracao-placa-mae.png`, `vm-configuracao-processador.png` and `vm-ubuntu-instalada.png` sit alongside them. The free-text caption of `C1-config.txt` was corrected after the fact — it carried a leftover note naming the cpu-bound profile while the other three named the memory-bound one; the machine-derived content of the file was not touched.

## Deliverables written

- **`RELATORIO.md`** — the professor's three sections, with the comparative results (§3.3) and the interpretation and conclusions (§3.4) nested inside the stress-test section. It states the three findings, the GIL / page-loop mechanism, and six declared limitations. **Figures 1–9 are embedded** with relative paths and captions, and cited in the body: 1–3 are the VM configuration screenshots (§2.6) and 4–9 the comparative graphs (§3.3.3). **Keep that shape:** the first draft numbered five top-level sections and had to be rewritten.
  - The four `C{1..4}-console.png` screenshots are listed but deliberately not embedded: they show only the guest's login prompt after boot, so they would add pages without evidencing anything. If a screenshot of the application actually serving requests is wanted, it has to be captured in a new VM session.
- **`README.md`** — the profile table filled in with what each application actually does, plus a section recording the group, the application deployed, the scenario matrix, the measurement protocol, where each artefact lives, how to run everything, and the headline results.
- A final revision pass over all three documents fixed two broken cross-references (§3.9.4 / §3.9.5 → §3.4.4 / §3.4.5), a column labelled "peak memory" that actually held a mean, a sentence quoting available-memory figures that could not be checked against the raw data (replaced by the measured peaks), and a claim about local execution of the three applications that was reworded to say only what the test suite demonstrates.

## Known limitations of the data

Declared in `RELATORIO.md` §3.4.5. They are to stay declared, not smoothed over.

- **Host contention inflates the variance.** Two physical cores are shared by the guest, the load generator and the NAT engine — the likely cause of the two anomalies with no physical explanation: C3 at L2 (2.12 rps) and C4 at L2 (1.65 rps) came out worse than C1 at L2 (3.59 rps) although both have more RAM than C1.
- **One repetition per level.** No standard deviation and no confidence interval; conclusions rest on trends between scenarios, not on differences between neighbouring levels.
- **Small samples.** The ~3.5 rps ceiling yields only 57–149 requests per level, so p95 and especially p99 rest on few observations — the C1 L4 p99 of 35405 ms is a single event.
- **C1 carried residual swap.** The guest was not rebooted between the probes behind §3.4.4 and C1's measurement, so the very first resource sample of C1 — taken before level 1 began — already shows 62.98 MB of swap in use, and that is the baseline quoted for C1 at L1 and L2. It affects C1's absolute baseline, not its 507 MB peak or any conclusion.
- **HTTP 503 was never observed under load**, for the reason recorded above. The path exists and is unit-tested; at this throughput it is unreachable by design.

## Open items

1. **Group size.** The group table lists two members; the assignment states groups of three. Unresolved — only the user can settle it.
2. **Nested repository / gitlink.** The outer repository stores `atividade2-demanda-desempenho/` as a gitlink (mode 160000) pointing at `https://github.com/RanyaG/atividade2-demanda-desempenho.git`, and there is no `.gitmodules`. A fresh clone therefore yields an empty folder, which blocks the "código no repositório da disciplina" checklist item. `RELATORIO.md` references the figures by paths inside that nested folder, so the two are coupled: whichever fix is chosen, the code has to be reachable at those paths.
3. **Evidence of local execution for all three applications.** The assignment asks for it and the captured evidence covers the VM experiment only. Today the sole support for that item is the test suite, and `RELATORIO.md` §3.4.5 is worded to claim exactly that and no more. Capturing real local-run evidence would close the item properly.
4. **Superseded Java / Spec Kit material** under the repository root's `apps/cpu-bound/` is still present; its removal was never authorized.
5. **Pending user actions:** the commit, the LCC3 demonstration, and the delivery form once per member.

## Continuation instructions

1. Read this file and check the actual workspace before assuming anything is in the state described here.
2. Respect the working agreement — in particular, never commit and never delete delivered artefacts without explicit approval.
3. `RELATORIO.md` and `README.md` are professor-facing: Portuguese, the professor's template shape, and no claim the data does not support.
4. Report unfinished work as unfinished rather than smoothing it over.
