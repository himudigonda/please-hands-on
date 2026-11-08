# Broski Benchmark Comparison (v0.5.1 vs v0.6.0-candidate)

Generated: 2026-03-07T12:33:33

## Before/After (Broski)

| Scenario | Baseline mean (s) | Candidate mean (s) | Delta % | Baseline p95 (s) | Candidate p95 (s) | Baseline stddev | Candidate stddev | Failures (base/cand) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| cold_ci | 10.3987 | 2.7966 | -73.11% | 10.4799 | 2.8132 | 0.0431 | 0.0103 | 0/0 |
| warm_ci | 0.0142 | 0.0219 | +53.82% | 0.0156 | 0.0226 | 0.0010 | 0.0005 | 0/0 |
| touch_no_content_backend | 0.0137 | 0.0221 | +61.08% | 0.0144 | 0.0227 | 0.0006 | 0.0005 | 0/0 |
| content_change_backend | 3.5871 | 0.5066 | -85.88% | 3.8835 | 0.5163 | 0.1235 | 0.0056 | 0/0 |
| content_change_frontend | 5.4311 | 2.3333 | -57.04% | 5.4825 | 2.3534 | 0.0325 | 0.0127 | 0/0 |
| cache_explain_hit | 0.0135 | 0.0224 | +66.28% | 0.0141 | 0.0228 | 0.0005 | 0.0003 | 0/0 |
| cache_bypass_no_cache | 10.4738 | 2.8172 | -73.10% | 10.6004 | 2.8413 | 0.0642 | 0.0149 | 0/0 |
| cache_bypass_force | 10.4727 | 2.8300 | -72.98% | 10.5503 | 2.8501 | 0.0469 | 0.0099 | 0/0 |
| dry_run_ci | 0.0132 | 0.0207 | +57.49% | 0.0135 | 0.0216 | 0.0002 | 0.0006 | 0/0 |
| passthrough_path | 0.0147 | 0.0149 | +1.90% | 0.0150 | 0.0156 | 0.0003 | 0.0005 | 0/0 |
| interactive_smoke | 0.0139 | 0.0140 | +0.73% | 0.0152 | 0.0168 | 0.0008 | 0.0013 | 0/0 |

## Candidate Budget Check

- PASS: cold_ci mean=2.7966s (budget <= 6.0000s)
- PASS: content_change_frontend mean=2.3333s (budget <= 3.0000s)
- PASS: warm_ci mean=0.0219s (budget <= 0.0500s)

## Regression Warnings

- WARN: warm_ci candidate mean is >10% slower (0.0219s vs 0.0142s)
- WARN: touch_no_content_backend candidate mean is >10% slower (0.0221s vs 0.0137s)
- WARN: cache_explain_hit candidate mean is >10% slower (0.0224s vs 0.0135s)
- WARN: dry_run_ci candidate mean is >10% slower (0.0207s vs 0.0132s)
