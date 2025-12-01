# Testing Guide for lesson10_Dev Examples

This directory contains tests for the example scripts in `src/lesson10_Dev`. The test suite validates that example scripts run successfully and produce expected output.

## Overview

The test approach:

- **Subprocess execution**: Each example script is run as a separate Python subprocess (no source modifications needed)
- **Keyword validation**: Tests check that output contains expected keywords/regexes (tolerates AIGC variability)
- **Global blacklist**: Tests fail if output contains forbidden patterns (errors, tracebacks, exceptions)
- **Self-maintenance**: Coverage test fails if new scripts lack YAML entries

## Files

- `expected_keywords.yaml` — Configuration file mapping each example script to expected keywords and skip status
- `test_script_coverage.py` — Enforces that all scripts are registered in the YAML
- `test_run_examples.py` — Runs each script as subprocess and validates output
- `README.md` — This file

## Running Tests

### Install test dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

### Run all tests

```powershell
pytest tests/lesson10_dev/
```

### Run only coverage checks (fast)

```powershell
pytest tests/lesson10_dev/test_script_coverage.py
```

### Run example scripts (requires API keys)

```powershell
pytest tests/lesson10_dev/test_run_examples.py -m examples
```

### Skip tests that need live API access

```powershell
pytest tests/lesson10_dev/ -m "not live_api"
```

### Run a specific script test

```powershell
pytest tests/lesson10_dev/test_run_examples.py -k "10101010"
```

## Adding New Example Scripts

When you add a new example script to `src/lesson10_Dev`, you must:

1. **Add an entry to `expected_keywords.yaml`** under the `scripts` section
2. **Choose keywords** — identify 2-5 stable phrases/patterns that will appear in the script's output
3. **Set flags** if needed:
   - `requires_env: true` — if script needs API keys from `.env`
   - `skip: true` — if script should not be tested yet

### Example YAML entry

```yaml
scripts:
  "src/lesson10_Dev/1010_Langchain/my_new_example.py":
    keywords:
      - "expected_phrase"
      - "another.*keyword"
      - "tool|function" # matches "tool" OR "function"
    requires_env: true
```

### Choosing good keywords

- Use stable, non-AIGC text (e.g., function names, fixed prompts, script output labels)
- Avoid exact LLM responses (they vary)
- Use regex for flexibility: `weather|sunny` matches either word
- At least one keyword must match for test to pass

### Skipping a script temporarily

```yaml
scripts:
  "src/lesson10_Dev/1010_Langchain/work_in_progress.py":
    skip: true
```

Or add a comment in the script itself:

```python
# test:skip
```

## Forbidden Patterns (Global Blacklist)

All script outputs are checked against a global blacklist in `expected_keywords.yaml`:

```yaml
forbidden_patterns:
  - "Traceback \\(most recent call last\\)"
  - "Exception:"
  - "ERROR:"
```

If any forbidden pattern appears in output, the test fails immediately. Update the blacklist as needed.

## Environment Setup

Example scripts use `python-dotenv` to load API keys from `.env` in the repository root. Make sure you have:

```
OPENAI_API_KEY=sk-...
# Add other API keys as needed
```

Tests marked with `requires_env: true` will skip if `.env` is missing.

## Troubleshooting

**Test fails with "Script not found"**

- Check the path in `expected_keywords.yaml` matches the actual file location
- Paths should be relative to repository root: `src/lesson10_Dev/...`

**Test fails with "No expected keywords found"**

- Run the script manually to see its output: `python "src/lesson10_Dev/path/to/script.py"`
- Update keywords in YAML to match actual output patterns

**Test fails with forbidden pattern**

- Script likely has a runtime error
- Check the test output for the full stdout/stderr
- Fix the script or update API keys in `.env`

**Coverage test reports unregistered scripts**

- Add entries to `expected_keywords.yaml` for the new scripts
- Or add `# test:skip` comment to scripts that shouldn't be tested

## CI/CD Integration

To run tests in CI:

```yaml
- name: Install dependencies
  run: pip install -r requirements-dev.txt

- name: Run coverage checks
  run: pytest tests/lesson10_dev/test_script_coverage.py

- name: Run example tests (if API keys available)
  run: pytest tests/lesson10_dev/test_run_examples.py -m examples
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Design Rationale

- **Why subprocess?** Preserves examples as-is; no `if __name__ == "__main__"` needed
- **Why keywords?** Tolerates AIGC variability while catching failures
- **Why coverage test?** Enforces self-maintenance when adding new examples
- **Why global blacklist?** Single source for common failure indicators
