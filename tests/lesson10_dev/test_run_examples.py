"""
Run example scripts as subprocesses and validate their output

This test suite runs each example script registered in expected_keywords.yaml
as a subprocess, captures its output, and validates:
1. No forbidden patterns (errors, tracebacks) appear in output
2. At least one expected keyword/regex matches the output
"""

import os
import re
import subprocess
import sys
from pathlib import Path
import pytest
import yaml


def get_repo_root():
    """Find the repository root by looking for pytest.ini"""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pytest.ini").exists():
            return parent
    raise RuntimeError("Could not find repository root (pytest.ini not found)")


def load_expected_keywords():
    """Load the expected_keywords.yaml file"""
    repo_root = get_repo_root()
    yaml_path = repo_root / "tests" / "lesson10_dev" / "expected_keywords.yaml"
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_test_params():
    """Generate test parameters from expected_keywords.yaml"""
    config = load_expected_keywords()
    scripts = config.get("scripts", {})
    
    params = []
    for script_path, script_config in scripts.items():
        params.append((script_path, script_config))
    
    return params


@pytest.fixture(scope="session")
def repo_root():
    """Provide repository root path"""
    return get_repo_root()


@pytest.fixture(scope="session")
def forbidden_patterns():
    """Load global forbidden patterns"""
    config = load_expected_keywords()
    return config.get("forbidden_patterns", [])


@pytest.mark.examples
@pytest.mark.parametrize("script_path,script_config", get_test_params())
def test_example_script(script_path, script_config, repo_root, forbidden_patterns):
    """Run an example script and validate its output"""
    
    # Check if script should be skipped
    if script_config.get("skip", False):
        print(f"\n⏭️ Script skipped: {script_path}")
        pytest.skip(f"Script marked as skip in YAML: {script_path}")
    
    # Check if script requires environment variables
    if script_config.get("requires_env", False):
        # Mark test so it can be filtered
        pytest.mark.live_api
        
        # Check for common API key environment variables
        # Scripts use dotenv to load .env, so we don't strictly need to check here,
        # but we can provide a helpful skip message if .env is missing
        env_file = repo_root / ".env"
        if not env_file.exists():
            pytest.skip(
                f"Script requires environment variables but .env not found. "
                f"Create .env file with required API keys to run this test."
            )
    
    # Construct full path to script
    full_script_path = repo_root / script_path
    if not full_script_path.exists():
        pytest.fail(f"Script not found: {full_script_path}")
    
    # Run script as subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(full_script_path)],
            cwd=str(repo_root),  # Run from repo root so relative imports work
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
            encoding="utf-8",
            errors="replace"  # Handle encoding errors gracefully
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"Script timed out after 60 seconds: {script_path}")
    except Exception as e:
        pytest.fail(f"Failed to run script {script_path}: {e}")
    
    # Combine stdout and stderr for checking
    output = result.stdout + "\n" + result.stderr
    
    # Check for forbidden patterns (global blacklist)
    forbidden_found = []
    for pattern in forbidden_patterns:
        if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
            forbidden_found.append(pattern)
    
    if forbidden_found:
        print(f"\n❌ Script failed: {script_path}")
        msg = (
            "\n\nScript output contains forbidden pattern(s):\n"
            + "\n".join(f"  - {p}" for p in forbidden_found)
            + f"\n\nExit code: {result.returncode}"
            + f"\n\n--- STDOUT ---\n{result.stdout}"
            + f"\n\n--- STDERR ---\n{result.stderr}"
        )
        pytest.fail(msg)
    
    # Check that at least one expected keyword matches
    keywords = script_config.get("keywords", [])
    if not keywords:
        pytest.skip(f"No keywords defined for {script_path}")
    
    matched_keywords = []
    for keyword in keywords:
        if re.search(keyword, output, re.IGNORECASE | re.MULTILINE):
            matched_keywords.append(keyword)
    
    if not matched_keywords:
        print(f"\n❌ Script failed: {script_path}")
        msg = (
            "\n\nNo expected keywords found in output."
            f"\n\nExpected at least one of: {keywords}"
            f"\n\nExit code: {result.returncode}"
            + f"\n\n--- STDOUT ---\n{result.stdout[:2000]}"  # Truncate for readability
            + f"\n\n--- STDERR ---\n{result.stderr[:1000]}"
        )
        pytest.fail(msg)
    
    # Success: at least one keyword matched and no forbidden patterns found
    print(f"\n✅ Script ran successfully: {script_path}")
    print(f"  Matched keywords: {matched_keywords}")
