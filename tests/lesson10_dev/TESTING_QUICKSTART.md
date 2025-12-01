# Testing Quick Start Guide

## What We Built

A complete testing harness for `lesson10_Dev` LangChain example scripts that:

✅ **Runs scripts as-is** (no modifications needed)  
✅ **Auto-detects untested scripts** (enforces coverage)  
✅ **Validates output with keywords** (tolerates AIGC variability)  
✅ **Catches real errors** (global blacklist for exceptions/tracebacks)  
✅ **Self-maintaining** (requires YAML entry for new scripts)

## Test Results (Initial Run)

```
23 passed, 4 skipped in ~4.5 minutes
```

**Passed**: 23 example scripts ran successfully  
**Skipped**: 4 scripts with known issues (documented in YAML)

## Quick Commands

### Run all tests

```powershell
pytest tests/lesson10_dev/
```

### Run only coverage checks (fast, no script execution)

```powershell
pytest tests/lesson10_dev/test_script_coverage.py
```

### Run examples (requires API keys in .env)

```powershell
pytest tests/lesson10_dev/test_run_examples.py
```

### Run specific script test

```powershell
pytest tests/lesson10_dev/test_run_examples.py -k "10101010"
```

### See verbose output

```powershell
pytest tests/lesson10_dev/ -v -s
```

## Files Added

1. **`pytest.ini`** — Test configuration with markers
2. **`requirements-dev.txt`** — Test dependencies (pytest, pyyaml)
3. **`tests/lesson10_dev/expected_keywords.yaml`** — Keyword mapping for all scripts
4. **`tests/lesson10_dev/test_script_coverage.py`** — Enforces all scripts are registered
5. **`tests/lesson10_dev/test_run_examples.py`** — Subprocess runner + validation
6. **`tests/lesson10_dev/README.md`** — Full documentation
7. **`tests/lesson10_dev/TESTING_QUICKSTART.md`** — This file

## Adding New Scripts

When you add a new script to `src/lesson10_Dev`, add an entry to `expected_keywords.yaml`:

```yaml
scripts:
  "src/lesson10_Dev/path/to/your_script.py":
    keywords:
      - "expected_output_phrase"
      - "another.*keyword"
    requires_env: true # if needs API keys
```

Then run coverage test to verify:

```powershell
pytest tests/lesson10_dev/test_script_coverage.py
```

## Skipped Scripts (Current)

These scripts are temporarily skipped due to known issues:

1. **10101020 Build a real-world agent.py** — TypeError with unexpected 'top_k' argument
2. **10102070 Ticket booking with middle_ware.py** — Placeholder, no code yet
3. **10102080 Streaming.py** — Unicode encoding issue on Windows
4. **10103021-a Invocation-stream-basic.py** — Transient network errors

To fix: Update the script, remove `skip: true` from YAML, re-run tests.

## Forbidden Patterns (Global Blacklist)

Tests fail immediately if output contains:

- `TypeError:`
- `ValueError:`
- `KeyError:`
- `AttributeError:`
- `ImportError:`
- `ModuleNotFoundError:`
- `ConnectionError:`
- `TimeoutError:`
- `UnicodeEncodeError:`
- `Failed to connect`

These indicate real bugs, not AIGC variability.

## How It Works

1. **Coverage Test**: Globs all `.py` files in `src/lesson10_Dev`, checks each has a YAML entry
2. **Runner Test**: For each registered script:
   - Runs as subprocess (Python interpreter from repo root)
   - Captures stdout + stderr
   - Checks: no forbidden patterns present
   - Checks: at least one keyword regex matches
   - Marks with `@pytest.mark.live_api` if `requires_env: true`

## Environment Setup

Scripts use `.env` for API keys. Make sure you have:

```
OPENAI_API_KEY=sk-...
```

Tests skip if `.env` is missing (when `requires_env: true`).

## CI/CD Integration

To run in CI:

```yaml
- name: Install test dependencies
  run: pip install -r requirements-dev.txt

- name: Run coverage tests
  run: pytest tests/lesson10_dev/test_script_coverage.py

- name: Run example tests (with API keys)
  run: pytest tests/lesson10_dev/test_run_examples.py
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Troubleshooting

**"Script not found" error**  
→ Check path in YAML matches actual file location (relative to repo root)

**"No expected keywords found"**  
→ Run script manually, check output, update keywords in YAML

**Test hangs**  
→ Script may have infinite loop; tests timeout after 60 seconds

**False positive forbidden pattern**  
→ Update YAML keywords to be more specific or adjust global blacklist

## Design Benefits

✅ **No source changes** — Examples remain simple and clear  
✅ **Self-maintaining** — Coverage test enforces YAML entries  
✅ **AIGC-tolerant** — Regex keywords handle output variability  
✅ **Fast feedback** — Coverage tests run in <1 second  
✅ **Real bug detection** — Caught 4 actual issues in initial run

## Next Steps

1. Fix the 4 skipped scripts (see list above)
2. Run tests after each new example is added
3. Update keywords if LLM outputs change significantly
4. Consider adding more granular markers (e.g., `@pytest.mark.slow` for >30s tests)

---

**Questions?** See full docs in `tests/lesson10_dev/README.md`
