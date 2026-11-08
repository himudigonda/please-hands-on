# TaskPulse Instructions

Related docs:
- `docs/setup-and-run.md`
- `docs/benchmark-methodology.md`

## 1. Prerequisites

Required tools:
- `python3` (3.11+)
- `node` + `npm`
- `make`
- `just`
- `git`
- `cargo`

## 2. Build Broski Binaries (Before/After)

Run from the Broski repo:

```bash
cd /Users/himudigonda/Documents/Projects/BroSki
mkdir -p /Users/himudigonda/Desktop/test/benchmark/bin

# baseline v0.5.1
rm -rf /tmp/broski-v051
git worktree add /tmp/broski-v051 v0.5.1
cd /tmp/broski-v051
cargo build -p broski-cli
cp target/debug/broski /Users/himudigonda/Desktop/test/benchmark/bin/broski-v051

# candidate (current branch)
cd /Users/himudigonda/Documents/Projects/BroSki
cargo build -p broski-cli
cp target/debug/broski /Users/himudigonda/Desktop/test/benchmark/bin/broski-v060
```

## 3. Run Setup Once

```bash
cd /Users/himudigonda/Desktop/test
benchmark/bin/broski-v060 --workspace . run setup
```

## 4. Run Stable vs Candidate Benchmark

```bash
cd /Users/himudigonda/Desktop/test
BROSKI_BASELINE_BIN=benchmark/bin/broski-v051 \
BROSKI_CANDIDATE_BIN=benchmark/bin/broski-v060 \
COMPARE_MODE=both \
python3 scripts/benchmark.py
```

Artifacts:
- `benchmark/benchmark.csv`
- `benchmark/benchmark.txt`
- `benchmark/comparison.md`

## 5. Switch Active Local Broski Symlink (Optional)

```bash
./scripts/use_broski.sh baseline
./scripts/use_broski.sh candidate
./scripts/use_broski.sh show
```

## 6. Functional Smoke Commands

```bash
benchmark/bin/broski-v060 --workspace . run ci --explain
benchmark/bin/broski-v060 --workspace . ci --jobs=4
benchmark/bin/broski-v060 --workspace . doctor
benchmark/bin/broski-v060 --workspace . cache prune --max-size 512
```

## 7. Troubleshooting

- If baseline fails to parse: verify `scripts/benchmark.py` switches to `broskifile.v051`.
- If candidate fails in strict staging: verify `broskifile.v060` includes required `@in` and `@stage_ro` paths.
- If `make`/`just` missing, install them or set `TOOL_FILTER=broski`.
