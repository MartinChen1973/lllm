"""
Utility functions for human-in-the-loop workflows in DeepAgents.

This module provides reusable functions for handling user decisions
when agent actions are interrupted for approval.
"""

import json


def get_user_decisions(action_requests, config_map):
    """
    Get user decisions for each action request.
    
    Args:
        action_requests: List of action requests that need user approval
        config_map: Dictionary mapping tool names to their review configs
    
    Returns:
        List of decision dictionaries, one per action request
    """
    decisions = []
    
    for i, action in enumerate(action_requests, 1):
        review_config = config_map[action["name"]]
        allowed_decisions = review_config['allowed_decisions']
        
        print(f"\n--- Action {i}/{len(action_requests)} ---")
        print(f"Tool: {action['name']}")
        print(f"Arguments: {action['args']}")
        print("\nAllowed decisions:")
        
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
        
        # Build decision based on user choice
        if selected_decision == "edit":
            # For edit, we need to get the edited arguments
            print(f"\nCurrent arguments: {action['args']}")
            print("Enter new arguments (or press Enter to keep current):")
            # For simplicity, we'll use the original args, but in a real scenario
            # you'd want to parse user input and construct the edited args
            edited_args = input("Edited args (JSON format, or Enter to keep current): ").strip()
            if not edited_args:
                edited_args = action['args']
            else:
                edited_args = json.loads(edited_args)
            
            decisions.append({
                "type": "edit",
                "edited_action": {
                    "name": action["name"],
                    "args": edited_args
                }
            })
        else:
            decisions.append({"type": selected_decision})
    
    return decisions


