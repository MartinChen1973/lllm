"""
Utility functions for human-in-the-loop workflows in DeepAgents.

This module provides reusable functions for handling user decisions
when agent actions are interrupted for approval.
"""

import json


def edit_argument(current_value: str, argument_name: str) -> str:
    """
    Simple text-based UI for editing a single argument.
    
    Args:
        current_value: The current value of the argument
        argument_name: The name of the argument being edited
    
    Returns:
        The new value (or original if user pressed Enter without changes)
    """
    print(f"Current {argument_name}: {current_value}")
    new_value = input("Modify to (press Enter to keep unchanged): ").strip()
    
    if not new_value:
        return current_value
    
    return new_value


def edit_email_arguments_interactive(original_args: dict) -> dict:
    """
    Interactive UI for editing email arguments (to, subject, body).
    
    Args:
        original_args: The original arguments dictionary
    
    Returns:
        Dictionary with edited arguments
    """
    edited_args = dict(original_args)
    
    print("\n--- Editing Email Arguments ---")
    
    # Edit 'to' (recipient)
    if 'to' in original_args:
        edited_value = edit_argument(str(original_args['to']), 'to (recipient)')
        edited_args['to'] = edited_value
    
    # Edit 'subject' (title)
    if 'subject' in original_args:
        edited_value = edit_argument(str(original_args['subject']), 'subject (title)')
        edited_args['subject'] = edited_value
    
    # Edit 'body'
    if 'body' in original_args:
        edited_value = edit_argument(str(original_args['body']), 'body')
        edited_args['body'] = edited_value
    
    return edited_args


def edit_arguments_json(original_args: dict) -> dict:
    """
    JSON-based editing for arguments (simple but less user-friendly).
    
    Args:
        original_args: The original arguments dictionary
    
    Returns:
        Dictionary with edited arguments (or original if user didn't provide input)
    """
    print(f"\nCurrent arguments: {original_args}")
    print("Enter new arguments (or press Enter to keep current):")
    edited_args_str = input("Edited args (JSON format, or Enter to keep current): ").strip()
    
    if not edited_args_str:
        return original_args
    
    try:
        return json.loads(edited_args_str)
    except json.JSONDecodeError:
        print("Invalid JSON format. Keeping original arguments.")
        return original_args


def get_single_decision(action, review_config, edit_handler=None, action_index=None, total_actions=None):
    """
    Get user decision for a single action request.
    
    Args:
        action: The action request that needs approval
        review_config: The review configuration for this action
        edit_handler: Optional callable to handle editing (takes original_args, returns edited_args)
                     If None and "edit" is selected, uses JSON-based editing
        action_index: Optional index for display (e.g., "Action 1/3")
        total_actions: Optional total number of actions for display
    
    Returns:
        A decision dictionary (approve, edit, or reject)
    """
    allowed_decisions = review_config['allowed_decisions']
    
    # Display action header
    if action_index is not None and total_actions is not None:
        print(f"\n--- Action {action_index}/{total_actions} ---")
        print(f"Tool: {action['name']}")
    else:
        print(f"\n--- Tool: {action['name']} ---")
    
    print(f"Arguments: {action['args']}")
    print(f"\nAllowed decisions: {', '.join(allowed_decisions)}")
    
    # Display numbered options
    for idx, decision_type in enumerate(allowed_decisions, 1):
        print(f"  {idx}. {decision_type}")
    
    # Get user choice
    while True:
        try:
            choice = input(f"\nSelect decision (1-{len(allowed_decisions)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(allowed_decisions):
                selected_decision = allowed_decisions[choice_num - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(allowed_decisions)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Handle edit decision
    if selected_decision == "edit":
        original_args = action['args']
        
        # Use provided edit handler or default to JSON editing
        if edit_handler is not None:
            edited_args = edit_handler(original_args)
        else:
            edited_args = edit_arguments_json(original_args)
        
        return {
            "type": "edit",
            "edited_action": {
                "name": action["name"],
                "args": edited_args
            }
        }
    
    # Handle approve or reject
    return {"type": selected_decision}


def get_user_decision_with_editing(action_req, review_cfg):
    """
    Get user decision for a single action request, with interactive email editing support.
    
    DEPRECATED: This function is now a wrapper around get_user_decisions for backward compatibility.
    It's recommended to use get_user_decisions directly, which handles both single and multiple actions.
    
    Args:
        action_req: The action request that needs approval
        review_cfg: The review configuration for this action
    
    Returns:
        A list containing a single decision dictionary (approve, edit, or reject)
    """
    # Create a config_map for the single action
    config_map = {action_req["name"]: review_cfg}
    
    # Use get_user_decisions which now handles editing automatically
    return get_user_decisions([action_req], config_map, use_interactive_email_editing=True)


def get_user_decisions(action_requests, config_map, use_interactive_email_editing=True):
    """
    Get user decisions for each action request (handles 1 to N actions).
    
    This unified function supports:
    - Single or multiple action requests
    - Interactive email editing (for send_email tool)
    - JSON-based editing (for other tools)
    
    Args:
        action_requests: List of action requests that need user approval
        config_map: Dictionary mapping tool names to their review configs
        use_interactive_email_editing: If True, uses interactive UI for editing email arguments.
                                       If False, uses JSON-based editing for all tools.
    
    Returns:
        List of decision dictionaries, one per action request
    """
    decisions = []
    
    for i, action in enumerate(action_requests, 1):
        review_config = config_map[action["name"]]
        
        # Choose edit handler based on tool name and user preference
        edit_handler = None
        if use_interactive_email_editing and action["name"] == "send_email":
            edit_handler = edit_email_arguments_interactive
        # For other tools or if interactive editing is disabled, use None (defaults to JSON)
        
        # Get single decision using the helper function
        decision = get_single_decision(
            action,
            review_config,
            edit_handler=edit_handler,
            action_index=i,
            total_actions=len(action_requests)
        )
        
        decisions.append(decision)
    
    return decisions

