# JupyterHub load test, 24 September 2026

## Scope and environment

Twelve disposable accounts (`test1`–`test12`) used the deployed AChPrak at
`https://lserver.chemie.uni-marburg.de/jhub/`. Each account had a separate Hub
server and browser session. The Hub reported version 6.0.1. The deployment and
local checkout were both at Git revision `f63f2b1`. The Linux host had an AMD
Ryzen 5 5600X (6 cores, 12 logical processors), 32,780,200 kB of RAM, and
2,097,856 kB of swap. Its application configuration allowed one calculation per
user instance.

Each simulated student generated a structure, optimized a minimum structure,
and calculated a UV/Vis spectrum. The next calculation started only after the
previous one completed. All students started the first calculation together
after their application sessions were ready. The client polled job status every
second. No transition-structure search was included.

The baseline used unsubstituted trans-azobenzene (24 atoms). The larger run used
four students per structure: trans NMe₂/NMe₂ (40 atoms), trans NMe₂/CF₃
(35 atoms), and cis CF₃/CF₃ (30 atoms). The two substituents occupied the first
configurable position on each phenyl ring (indices 0 and 5 in the API settings).

## Results

| Run | Accounts ready | Completed workflows | Ready time | Concurrent workload wall time | HTTP p95 | Peak host CPU busy | Lowest available RAM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| One remote student, trans-H | 1/1 | 1/1 | 0.55 s | 14.97 s | 0.13 s | — | — |
| Initial cold 12-account start, trans-H | 4/12 | 4/12 | 3.96 s | 16.02 s for the four ready accounts | 2.40 s | 63.1% | 28,309 MiB |
| 12 accounts, trans-H, after startup | 12/12 | 12/12 | 3.31 s | 26.53 s | 0.18 s | 100% | 26,397 MiB |
| 12 accounts, larger double substitutions | 12/12 | 12/12 | 2.16 s | 32.30 s | 0.17 s | 100% | 25,660 MiB |

The initial simultaneous start returned HTTP 424 from the Hub for eight
application-session requests. Four accounts completed their workflows. A later
single-account check succeeded for one of the affected accounts, and a repeat
with startup retry logic reached all 12 accounts. This is a startup-readiness
finding; the first client stopped at the initial 424 response, so it did not
establish whether a student's browser would recover automatically. Hub logs were
not readable with the supplied non-sudo SSH account.

All 24 workflows in the two successful 12-account runs completed all three jobs.
All 24 minimum optimizations reported convergence. The table below reports the
median client-observed duration from job submission through its completed status;
one-second polling adds up to about a second of timing resolution.

| 12-account run | Structure generation | Minimum optimization | UV/Vis spectrum | Median full workflow per student |
| --- | ---: | ---: | ---: | ---: |
| Trans-H | 6.35 s | 10.56 s | 8.60 s | 25.48 s |
| Mixed double substitutions | 5.34 s | 12.88 s | 12.99 s | 32.20 s |

In the successful 12-account runs, the peak summed resident set size of chemistry
workers was 4,554 MiB for trans-H and 5,489 MiB for the larger structures. RSS
sums can count shared pages more than once. The Linux `MemAvailable` minimum and
the process RSS should therefore be read as separate indicators, not added
together. Swap use stayed at 31 MiB in the samples. CPU busy reached 100% of the
12 logical processors in both successful concurrent runs.

## Comparison with one local user

The same Git revision ran on an Apple Silicon Mac with 10 logical processors and
32 GiB of RAM. One local application instance processed the same cases through a
private Unix socket, with the Pixi `web` environment and one native compute
thread. Each case used a fresh application session. These local figures exclude
Hub login, proxy startup, and network transit. The remote figures are medians of
the corresponding students in the 12-account runs and include remote HTTP
round trips. Different hardware and operating systems also affect the comparison.

| Structure | Local single-user workflow | Remote concurrent workflow, median | Remote/local ratio |
| --- | ---: | ---: | ---: |
| Trans-H | 11.05 s | 25.48 s | 2.31× |
| Trans NMe₂/NMe₂ | 16.11 s | 32.25 s | 2.00× |
| Trans NMe₂/CF₃ | 15.09 s | 32.21 s | 2.14× |
| Cis CF₃/CF₃ | 15.09 s | 31.19 s | 2.07× |

The remote **single-user** trans-H workflow took 14.97 s, compared with 11.05 s
locally. The larger ratios under 12 remote users are consistent with shared CPU
contention, but this experiment does not isolate CPU contention from hardware,
operating-system, proxy, or network differences. The local UV/Vis calculations
initially failed because a manual server launch omitted the Pixi executable path;
the server was restarted with the full environment and only the successful rerun
is used above.

## Reproduction and limits

- [Hub workload script](../scripts/load_test_hub.py) logs in, waits for each
  application to become ready, and records each job and HTTP timing. Credentials
  are supplied through an environment variable and are absent from the result
  files. The run data are [one remote student](../results/hub-load/baseline-one.json),
  [initial cold start](../results/hub-load/baseline-12.json),
  [successful 12-account baseline](../results/hub-load/baseline-12-retry.json),
  and [double-substitution run](../results/hub-load/double-12.json).
- [Host sampler](../scripts/monitor_hub.py) reads `/proc` once per second. Its
  [CSV samples](../results/hub-load/host-samples.csv) began after the one-student
  baseline, so that run has no host-resource measurements.
- [Local comparison script](../scripts/benchmark_local_web.py) produced the
  [corrected local run](../results/hub-load/local-one-corrected.json).
- Each scenario was run once, with four repeats per larger molecular case and
  12 students for trans-H. The results characterize this host and these settings,
  not a guaranteed maximum class size. The benchmark did not exercise image
  export, downloads, cancellation, or transition-structure searches.
- All 12 disposable Hub servers were stopped after the test; the Linux test
  accounts remain for manual removal.
