#!/usr/bin/env python3
"""Log action finder operations to a YAML history file."""

import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install it with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def log_error(error_msg: str, script_dir: Path, exception: Exception = None):
    """Log errors to error.log file."""
    error_file = script_dir / 'error.log'
    try:
        with open(error_file, 'a', encoding='utf-8') as ef:
            ef.write(f"\n=== ERROR {datetime.now().isoformat()} ===\n")
            ef.write(f"Error: {error_msg}\n")
            if exception:
                import traceback
                ef.write(f"Exception: {exception}\n")
                ef.write(f"Traceback:\n{traceback.format_exc()}\n")
            ef.write(f"Arguments received: {sys.argv}\n")
            ef.write(f"Script directory: {script_dir}\n")
            ef.write(f"Current working directory: {Path.cwd()}\n")
            ef.write("=" * 50 + "\n")
            ef.flush()
    except Exception:
        pass  # Silently fail if error logging fails


def load_history(log_file: Path) -> list:
    """Load existing history from YAML file."""
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('operations', []) if data else []
        except Exception:
            return []
    return []


def save_history(log_file: Path, operations: list):
    """Save history to YAML file."""
    script_dir = Path(__file__).parent.resolve()
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(log_file, 'w', encoding='utf-8') as f:
            yaml.dump({'operations': operations}, f, default_flow_style=False, sort_keys=False)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        # Verify file was written
        if not log_file.exists():
            error_msg = f"save_history ERROR: File was not created at {log_file}"
            log_error(error_msg, script_dir)
            raise FileNotFoundError(error_msg)
            
    except Exception as e:
        error_msg = f"save_history ERROR: {e}"
        log_error(error_msg, script_dir, e)
        raise


def log_operation(entity_name: str, template_selected: str, actions: list[str]):
    """
    Log an operation to the history file.
    
    Args:
        entity_name: Name of the entity
        template_selected: Template that was selected (CIDED, CIDRA, or CID)
        actions: List of action names that were found and returned
    """
    try:
        # Get the log file path relative to the script directory
        # Use resolve() to get absolute path to avoid issues with working directory
        script_dir = Path(__file__).parent.resolve()
        log_file = script_dir / 'history.yaml'
        
        # Load existing history
        operations = load_history(log_file)
        
        # Create new operation entry
        operation = {
            'datetime': datetime.now().isoformat(),
            'entity_name': entity_name,
            'template_selected': template_selected,
            'actions_found': actions,
            'actions_count': len(actions)
        }
        
        # Append to history
        operations.append(operation)
        
        # Save updated history
        save_history(log_file, operations)
        
        # Print success message to stdout
        print(f"SUCCESS: Logged operation: {entity_name} with template {template_selected} to {log_file}", file=sys.stdout)
        sys.stdout.flush()
    except Exception as e:
        import traceback
        error_msg = f"ERROR in log_operation: {e}"
        script_dir = Path(__file__).parent.resolve()
        log_error(error_msg, script_dir, e)
        raise


def main():
    """Main entry point for the script."""
    try:
        script_dir = Path(__file__).parent.resolve()
    except Exception:
        # Fallback if __file__ doesn't work
        script_dir = Path.cwd() / 'scripts'
    
    if len(sys.argv) < 4:
        error_msg = f"Invalid arguments: Expected at least 4 arguments (entity_name, template, and at least one action), but got {len(sys.argv)} arguments.\nUsage: log.py <entity_name> <template> <action1> [action2] ...\nExample: log.py User CIDED createUser listUsers getUser editUser deleteUser"
        print(error_msg, file=sys.stderr)
        log_error(error_msg, script_dir)
        sys.exit(1)
    
    entity_name = sys.argv[1]
    template_selected = sys.argv[2]
    actions = sys.argv[3:]
    
    # Validate template
    valid_templates = ['CIDED', 'CIDRA', 'CID']
    if template_selected not in valid_templates:
        error_msg = f"Invalid template: '{template_selected}'. Valid templates are: {', '.join(valid_templates)}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        log_error(error_msg, script_dir)
        sys.exit(1)
    
    # Validate actions (check if they look like template names instead of camelCase)
    template_action_names = ['Create', 'Index', 'Details', 'Edit', 'Delete', 'Reject', 'Approve']
    suspicious_actions = [action for action in actions if action in template_action_names]
    if suspicious_actions:
        error_msg = f"Invalid action names detected: {suspicious_actions}. These look like template action names, not generated camelCase names. Expected format: createUser, listUsers, etc. (camelCase)."
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        log_error(error_msg, script_dir)
        # Don't exit - log the error but continue, as the script might still work
    
    try:
        log_operation(entity_name, template_selected, actions)
    except Exception as e:
        error_msg = f"ERROR in main() during log_operation: {e}"
        print(error_msg, file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        log_error(error_msg, script_dir, e)
        raise


if __name__ == "__main__":
    main()
