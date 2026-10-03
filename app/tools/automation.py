# ============================================================
# GENERIC COMPUTER AUTOMATION
# ============================================================


def register_automation_tools(registry):
    """
    Register generic multi-step automation.

    This allows JARVIS to combine existing capabilities
    without creating a separate tool for every task.
    """

    def run_actions(actions):
        """
        Execute a sequence of registered tools.

        Example:

        [
            {
                "action": "open_application",
                "arguments": {
                    "application": "Chrome"
                }
            },
            {
                "action": "wait",
                "arguments": {
                    "seconds": 2
                }
            },
            {
                "action": "hotkey",
                "arguments": {
                    "keys": "ctrl+l"
                }
            }
        ]
        """

        return registry.execute_sequence(actions)

    registry.register(
        "run_actions",
        run_actions,
        description=(
            "Execute multiple local computer actions in sequence. "
            "Use this when a user request requires several steps. "
            "Only use already registered tools. "
            "Do not invent tools."
        ),
        parameters={
            "actions": {
                "type": "array",
                "description": (
                    "Ordered list of actions. Each action contains "
                    "an action name and an arguments object."
                ),
            },
        },
    )