class ToolRegistry:

    def __init__(self, memory=None):
        self.tools = {}
        self.memory = memory

    # ==========================================================
    # REGISTRATION
    # ==========================================================

    def register(
        self,
        name,
        function,
        description="",
        parameters=None,
    ):
        self.tools[name] = {
            "function": function,
            "description": description,
            "parameters": parameters or {},
        }

    # ==========================================================
    # SINGLE TOOL EXECUTION
    # ==========================================================

    def execute(self, name, arguments=None):

        if name not in self.tools:
            raise ValueError(
                f"Unknown tool: {name}"
            )

        if arguments is None:
            arguments = {}

        if not isinstance(arguments, dict):
            raise TypeError(
                "Tool arguments must be a dictionary."
            )

        tool = self.tools[name]

        function = tool["function"]

        parameters = tool["parameters"]

        filtered_arguments = {
            parameter_name: arguments.get(parameter_name)
            for parameter_name in parameters
        }

        return function(**filtered_arguments)

    # ==========================================================
    # MULTI-ACTION EXECUTION
    # ==========================================================

    def execute_sequence(self, actions):

        if not isinstance(actions, list):
            raise TypeError(
                "Actions must be a list."
            )

        if not actions:
            raise ValueError(
                "Action sequence cannot be empty."
            )

        results = []

        for index, action in enumerate(actions, start=1):

            if not isinstance(action, dict):
                raise TypeError(
                    f"Action {index} must be an object."
                )

            tool_name = action.get("action")

            arguments = action.get(
                "arguments",
                {},
            )

            if not isinstance(tool_name, str):
                raise ValueError(
                    f"Action {index} is missing a valid action name."
                )

            if not isinstance(arguments, dict):
                raise TypeError(
                    f"Arguments for action {index} must be an object."
                )

            # Prevent recursive sequences.
            if tool_name == "run_actions":
                raise ValueError(
                    "Nested action sequences are not allowed."
                )

            if not self.has(tool_name):
                raise ValueError(
                    f"Unknown tool in action {index}: "
                    f"{tool_name}"
                )

            result = self.execute(
                tool_name,
                arguments,
            )

            results.append({
                "action": tool_name,
                "result": result,
            })

        return results

    # ==========================================================
    # HELPERS
    # ==========================================================

    def has(self, name):
        return name in self.tools

    def descriptions(self):
        return {
            name: tool["description"]
            for name, tool in self.tools.items()
        }

    def schemas(self):
        return {
            name: tool["parameters"]
            for name, tool in self.tools.items()
        }

    def get(self, name):
        return self.tools.get(name)