"""
Test that all example scripts in lesson10_Dev are registered in expected_keywords.yaml

This test enforces self-maintenance: when a new example script is added, it must
have an entry in expected_keywords.yaml (or be explicitly marked with # test:skip).
"""

import os
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


def find_all_example_scripts():
    """Find all Python scripts under src/lesson10_Dev"""
    repo_root = get_repo_root()
    lesson_dir = repo_root / "src" / "lesson10_Dev"
    
    if not lesson_dir.exists():
        pytest.skip(f"lesson10_Dev directory not found: {lesson_dir}")
    
    scripts = []
    for py_file in lesson_dir.rglob("*.py"):
        # Skip __pycache__ and __init__.py files
        if "__pycache__" in py_file.parts or py_file.name == "__init__.py":
            continue
        
        # Get relative path from repo root
        rel_path = py_file.relative_to(repo_root).as_posix()
        scripts.append((rel_path, py_file))
    
    return scripts


def has_test_skip_comment(script_path):
    """Check if a script has a # test:skip comment"""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
            return "# test:skip" in content or "#test:skip" in content
    except Exception:
        return False


def test_all_scripts_are_registered():
    """Ensure all example scripts are registered in expected_keywords.yaml"""
    config = load_expected_keywords()
    registered_scripts = set(config.get("scripts", {}).keys())
    
    all_scripts = find_all_example_scripts()
    unregistered = []
    
    for rel_path, abs_path in all_scripts:
        # Skip if has in-file skip comment
        if has_test_skip_comment(abs_path):
            continue
        
        # Check if registered in YAML
        if rel_path not in registered_scripts:
            unregistered.append(rel_path)
    
    if unregistered:
        msg = (
            f"\n\nFound {len(unregistered)} unregistered example script(s):\n"
            + "\n".join(f"  - {path}" for path in sorted(unregistered))
            + "\n\nPlease add entries to tests/lesson10_dev/expected_keywords.yaml"
            + "\nor add '# test:skip' comment to scripts that should not be tested."
        )
        pytest.fail(msg)


def test_yaml_structure_is_valid():
    """Validate that expected_keywords.yaml has the correct structure"""
    config = load_expected_keywords()
    
    # Check required top-level keys
    assert "forbidden_patterns" in config, "Missing 'forbidden_patterns' in YAML"
    assert "scripts" in config, "Missing 'scripts' in YAML"
    
    # Validate forbidden_patterns
    assert isinstance(config["forbidden_patterns"], list), \
        "'forbidden_patterns' must be a list"
    
    # Validate scripts structure
    scripts = config["scripts"]
    assert isinstance(scripts, dict), "'scripts' must be a dictionary"
    
    for script_path, script_config in scripts.items():
        assert isinstance(script_config, dict), \
            f"Script config for '{script_path}' must be a dictionary"
        
        # Check if skip is set
        if script_config.get("skip", False):
            continue
        
        # Otherwise, keywords are required
        assert "keywords" in script_config, \
            f"Script '{script_path}' must have 'keywords' (or set skip: true)"
        assert isinstance(script_config["keywords"], list), \
            f"'keywords' for '{script_path}' must be a list"
        assert len(script_config["keywords"]) > 0, \
            f"'keywords' for '{script_path}' must not be empty"


def test_registered_scripts_exist():
    """Ensure all scripts registered in YAML actually exist"""
    repo_root = get_repo_root()
    config = load_expected_keywords()
    
    missing = []
    for script_path in config.get("scripts", {}).keys():
        full_path = repo_root / script_path
        if not full_path.exists():
            missing.append(script_path)
    
    if missing:
        msg = (
            f"\n\nFound {len(missing)} registered script(s) that don't exist:\n"
            + "\n".join(f"  - {path}" for path in sorted(missing))
            + "\n\nPlease remove these entries from expected_keywords.yaml"
        )
        pytest.fail(msg)
