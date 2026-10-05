# ============================================================

# JARVIS COMPUTER AGENT

# ============================================================

#

# Local computer-operation layer.

#

# Core loop:

#

#     Observe

#        ↓

#     Decide

#        ↓

#     Act

#        ↓

#     Observe

#        ↓

#     Verify

#        ↓

#     Recover if necessary

#

# IMPORTANT:

# - No Groq/API calls for computer actions.

# - No AI reasoning inside this class.

# - Uses ToolRegistry for actual machine operations.

#

# ============================================================





class ComputerAgent:



    # ============================================================

    # INITIALIZATION

    # ============================================================



    def __init__(self, registry, brain=None):

        self.registry = registry

        self.brain = brain



    # ============================================================

    # OBSERVE

    # ============================================================



    def observe(self):

        """

        Observe the current computer screen.

        """



        return self.registry.execute(

            "observe_screen"

        )



    # ============================================================

    # EXECUTE ONE LOCAL ACTION

    # ============================================================



    def execute_action(self, action):

        """

        Execute one computer action.



        Direct ComputerAgent capabilities:

            computer_click_target

            computer_click_spatial



        Everything else goes through ToolRegistry.

        """



        if not isinstance(action, dict):

            raise TypeError(

                "Computer action must be a dictionary."

            )



        name = action.get("action")



        arguments = action.get(

            "arguments",

            {},

        )



        if not name:

            raise ValueError(

                "Computer action is missing 'action'."

            )



        if not isinstance(arguments, dict):

            raise TypeError(

                "Computer action arguments must be a dictionary."

            )



        # ==========================================================

        # SPECIAL DIRECT COMPUTER CAPABILITIES

        # ==========================================================



        # These are NOT registry tools.

        # They belong directly to ComputerAgent.



        if name == "computer_click_target":



            target = arguments.get("target")



            position = arguments.get(

                "position",

                "first",

            )



            if not target:

                raise ValueError(

                    "computer_click_target requires 'target'."

                )



            return self.click_target(

                target=target,

                position=position,

            )



        # ==========================================================



        if name == "computer_click_spatial":



            relationship = arguments.get(

                "relationship",

                arguments.get(

                    "relation"

                ),

            )



            reference_text = arguments.get(

                "reference_text"

            )



            target_text = arguments.get(

                "target_text"

            )



            if not relationship:

                raise ValueError(

                    "computer_click_spatial requires "

                    "'relationship'."

                )



            if not reference_text:

                raise ValueError(

                    "computer_click_spatial requires "

                    "'reference_text'."

                )



            if not target_text:

                raise ValueError(

                    "computer_click_spatial requires "

                    "'target_text'."

                )



            relationship = str(

                relationship

            ).lower().strip()



            if relationship == "below":



                return self.click_below(

                    reference_text,

                    target_text,

                )



            if relationship == "above":



                return self.click_above(

                    reference_text,

                    target_text,

                )



            if relationship == "left_of":



                return self.click_left_of(

                    reference_text,

                    target_text,

                )



            if relationship == "right_of":



                return self.click_right_of(

                    reference_text,

                    target_text,

                )



            raise ValueError(

                "Unknown spatial relationship: "

                f"{relationship}"

            )



        # ==========================================================

        # SAFETY

        # ==========================================================



        if name == "run_actions":

            raise ValueError(

                "ComputerAgent cannot execute "

                "nested run_actions."

            )



        if name == "AI_QUERY":

            raise ValueError(

                "ComputerAgent cannot execute "

                "AI_QUERY."

            )



        # ==========================================================

        # NORMAL LOCAL TOOL

        # ==========================================================



        return self.registry.execute(

            name,

            arguments,

        )



    # ============================================================

    # EXECUTE SEQUENCE

    # ============================================================



    def execute_sequence(

        self,

        actions,

    ):

        """

        Execute multiple local actions in order.

        """



        if not isinstance(

            actions,

            list,

        ):

            raise TypeError(

                "Actions must be a list."

            )



        results = []



        for action in actions:



            result = self.execute_action(

                action

            )



            results.append(

                {

                    "action": action.get(

                        "action"

                    ),

                    "result": result,

                }

            )



        return results



    # ============================================================

    # FIND TEXT

    # ============================================================



    def find_text(

        self,

        text,

    ):

        return self.registry.execute(

            "find_text_on_screen",

            {

                "text": text,

            },

        )



    # ============================================================

    # FIND ALL TEXT

    # ============================================================



    def find_all_text(

        self,

        text,

    ):

        return self.registry.execute(

            "find_all_text_on_screen",

            {

                "text": text,

            },

        )



    # ============================================================

    # CLICK TEXT

    # ============================================================



    def click_text(

        self,

        text,

    ):

        return self.registry.execute(

            "click_text_on_screen",

            {

                "text": text,

            },

        )



    # ============================================================

    # FIND BELOW

    # ============================================================



    def find_below(

        self,

        reference_text,

        target_text,

    ):

        return self.registry.execute(

            "find_text_below",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



    # ============================================================

    # FIND ABOVE

    # ============================================================



    def find_above(

        self,

        reference_text,

        target_text,

    ):

        return self.registry.execute(

            "find_text_above",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



    # ============================================================

    # FIND LEFT

    # ============================================================



    def find_left_of(

        self,

        reference_text,

        target_text,

    ):

        return self.registry.execute(

            "find_text_left_of",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



    # ============================================================

    # FIND RIGHT

    # ============================================================



    def find_right_of(

        self,

        reference_text,

        target_text,

    ):

        return self.registry.execute(

            "find_text_right_of",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



    # ============================================================

    # CLICK BELOW

    # ============================================================



    def click_below(self, reference_text, target_text):

        result = self.registry.execute(

            "find_text_below",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



        if not result:

            return {

                "success": False,

                "message": (

                    f"Could not find '{target_text}' "

                    f"below '{reference_text}'."

                ),

            }



        x = result.get("x")

        y = result.get("y")



        if x is None or y is None:

            return {

                "success": False,

                "message": (

                    "Spatial target was found, "

                    "but coordinates are unavailable."

                ),

            }



        click_result = self.registry.execute(

            "click_mouse",

            {

                "x": x,

                "y": y,

                "button": "left",

            },

        )



        return {

            "success": True,

            "relationship": "below",

            "reference_text": reference_text,

            "target_text": target_text,

            "x": x,

            "y": y,

            "result": click_result,

        }





    def click_above(self, reference_text, target_text):

        result = self.registry.execute(

            "find_text_above",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



        if not result:

            return {

                "success": False,

                "message": (

                    f"Could not find '{target_text}' "

                    f"above '{reference_text}'."

                ),

            }



        x = result.get("x")

        y = result.get("y")



        if x is None or y is None:

            return {

                "success": False,

                "message": (

                    "Spatial target was found, "

                    "but coordinates are unavailable."

                ),

            }



        click_result = self.registry.execute(

            "click_mouse",

            {

                "x": x,

                "y": y,

                "button": "left",

            },

        )



        return {

            "success": True,

            "relationship": "above",

            "reference_text": reference_text,

            "target_text": target_text,

            "x": x,

            "y": y,

            "result": click_result,

        }





    def click_left_of(self, reference_text, target_text):

        result = self.registry.execute(

            "find_text_left_of",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



        if not result:

            return {

                "success": False,

                "message": (

                    f"Could not find '{target_text}' "

                    f"left of '{reference_text}'."

                ),

            }



        x = result.get("x")

        y = result.get("y")



        if x is None or y is None:

            return {

                "success": False,

                "message": (

                    "Spatial target was found, "

                    "but coordinates are unavailable."

                ),

            }



        click_result = self.registry.execute(

            "click_mouse",

            {

                "x": x,

                "y": y,

                "button": "left",

            },

        )



        return {

            "success": True,

            "relationship": "left_of",

            "reference_text": reference_text,

            "target_text": target_text,

            "x": x,

            "y": y,

            "result": click_result,

        }





    def click_right_of(self, reference_text, target_text):

        result = self.registry.execute(

            "find_text_right_of",

            {

                "reference_text": reference_text,

                "target_text": target_text,

            },

        )



        if not result:

            return {

                "success": False,

                "message": (

                    f"Could not find '{target_text}' "

                    f"right of '{reference_text}'."

                ),

            }



        x = result.get("x")

        y = result.get("y")



        if x is None or y is None:

            return {

                "success": False,

                "message": (

                    "Spatial target was found, "

                    "but coordinates are unavailable."

                ),

            }



        click_result = self.registry.execute(

            "click_mouse",

            {

                "x": x,

                "y": y,

                "button": "left",

            },

        )



        return {

            "success": True,

            "relationship": "right_of",

            "reference_text": reference_text,

            "target_text": target_text,

            "x": x,

            "y": y,

            "result": click_result,

        }



    # ============================================================

    # CLICK TARGET

    # ============================================================



    def click_target(

        self,

        target,

        position="first",

    ):

        """

        Generic OCR-based click.



        position:

            first

            topmost

            bottommost

            leftmost

            rightmost

        """



        if not target:

            raise ValueError(

                "Click target cannot be empty."

            )



        target = str(

            target

        ).strip()



        position = str(

            position or "first"

        ).lower().strip()



        if position == "first":



            return self.click_text(

                target

            )



        matches = self.find_all_text(

            target

        )



        if not matches:



            return {

                "success": False,

                "message": (

                    f"Could not find '{target}' "

                    "on the screen."

                ),

            }



        if position == "topmost":



            selected = min(

                matches,

                key=lambda item: item.get(

                    "y",

                    float("inf"),

                ),

            )



        elif position == "bottommost":



            selected = max(

                matches,

                key=lambda item: item.get(

                    "y",

                    float("-inf"),

                ),

            )



        elif position == "leftmost":



            selected = min(

                matches,

                key=lambda item: item.get(

                    "x",

                    float("inf"),

                ),

            )



        elif position == "rightmost":



            selected = max(

                matches,

                key=lambda item: item.get(

                    "x",

                    float("-inf"),

                ),

            )



        else:



            raise ValueError(

                "Unknown click position: "

                f"{position}"

            )



        x = selected.get(

            "x"

        )



        y = selected.get(

            "y"

        )



        if x is None or y is None:



            return {

                "success": False,

                "message": (

                    f"Found '{target}', but "

                    "its screen coordinates "

                    "are unavailable."

                ),

            }



        result = self.registry.execute(

            "click_mouse",

            {

                "x": x,

                "y": y,

            },

        )



        return {

            "success": True,

            "target": target,

            "position": position,

            "x": x,

            "y": y,

            "result": result,

        }



    # ============================================================

    # WAIT

    # ============================================================



    def wait(

        self,

        seconds,

    ):

        return self.registry.execute(

            "wait",

            {

                "seconds": seconds,

            },

        )



    # ============================================================

    # SCREEN SIGNATURE

    # ============================================================



    def screen_signature(

        self,

        screen,

    ):

        """

        Create a deterministic OCR-based screen signature.

        """



        if not isinstance(

            screen,

            dict,

        ):

            return ()



        elements = screen.get(

            "elements",

            [],

        )



        if not isinstance(

            elements,

            list,

        ):

            return ()



        signature = []



        for element in elements:



            if not isinstance(

                element,

                dict,

            ):

                continue



            text = str(

                element.get(

                    "text",

                    "",

                )

            ).strip().lower()



            if not text:

                continue



            x = element.get(

                "x",

                0,

            )



            y = element.get(

                "y",

                0,

            )



            try:



                x = round(

                    float(x) / 5

                ) * 5



            except (

                TypeError,

                ValueError,

            ):



                x = 0



            try:



                y = round(

                    float(y) / 5

                ) * 5



            except (

                TypeError,

                ValueError,

            ):



                y = 0



            signature.append(

                (

                    text,

                    x,

                    y,

                )

            )



        signature.sort()



        return tuple(

            signature

        )



    # ============================================================

    # SCREEN CHANGE DETECTION

    # ============================================================



    def screen_changed(

        self,

        before,

        after,

    ):

        return (

            self.screen_signature(

                before

            )

            !=

            self.screen_signature(

                after

            )

        )



    # ============================================================

    # TEXT VISIBLE

    # ============================================================



    def text_visible(

        self,

        screen,

        text,

    ):

        """

        Check exact OCR text in an already-observed screen.

        """



        if not text:

            return False



        if not isinstance(

            screen,

            dict,

        ):

            return False



        target = str(

            text

        ).strip().lower()



        elements = screen.get(

            "elements",

            [],

        )



        if not isinstance(

            elements,

            list,

        ):

            return False



        for element in elements:



            if not isinstance(

                element,

                dict,

            ):

                continue



            current = str(

                element.get(

                    "text",

                    "",

                )

            ).strip().lower()



            if current == target:

                return True



        return False



    # ============================================================

    # VERIFY TEXT VISIBLE

    # ============================================================



    def verify_text_visible(

        self,

        text,

        wait_seconds=0.5,

    ):

        if wait_seconds > 0:

            self.wait(

                wait_seconds

            )



        screen = self.observe()



        return {

            "text": text,

            "visible": self.text_visible(

                screen,

                text,

            ),

            "screen": screen,

        }



    # ============================================================

    # ACT + OBSERVE

    # ============================================================



    def act_and_observe(

        self,

        action,

        wait_seconds=0.5,

    ):

        """

        Observe → Act → Wait → Observe → Compare.

        """



        before = self.observe()



        result = self.execute_action(

            action

        )



        if wait_seconds > 0:

            self.wait(

                wait_seconds

            )



        after = self.observe()



        changed = self.screen_changed(

            before,

            after,

        )



        return {

            "before": before,

            "action": action,

            "result": result,

            "after": after,

            "screen_changed": changed,

        }



    # ============================================================

    # ACT + VERIFY

    # ============================================================



    def act_and_verify(

        self,

        action,

        expected_text=None,

        wait_seconds=0.5,
        before=None,

    ):

        """

        Observe → Act → Wait → Observe → Verify.

        """



        if before is None:
            before = self.observe()



        result = self.execute_action(

            action

        )



        if wait_seconds > 0:

            self.wait(

                wait_seconds

            )



        after = self.observe()



        changed = self.screen_changed(

            before,

            after,

        )



        expected_visible = None



        if expected_text:

            expected_visible = self.text_visible(

                after,

                expected_text,

            )



        success = changed



        if expected_text:

            success = expected_visible



        return {

            "success": success,

            "action": action,

            "result": result,

            "screen_changed": changed,

            "expected_text": expected_text,

            "expected_visible": expected_visible,

            "before": before,

            "after": after,

        }



    # ============================================================

    # RECOVERY: FIND TEXT AND CLICK

    # ============================================================



    def recover_click_text(

        self,

        text,

        position="first",

        wait_seconds=0.5,

    ):

        """

        Recovery helper.



        Re-observe the screen and try clicking the target again.



        This is deliberately local.

        """



        before = self.observe()



        result = self.click_target(

            text,

            position,

        )



        if wait_seconds > 0:

            self.wait(

                wait_seconds

            )



        after = self.observe()



        changed = self.screen_changed(

            before,

            after,

        )



        return {

            "success": changed,

            "recovery_action": "click_target",

            "target": text,

            "position": position,

            "result": result,

            "screen_changed": changed,

            "before": before,

            "after": after,

        }



    # ============================================================

    # RECOVERY: SPATIAL CLICK

    # ============================================================



    def recover_spatial_click(

        self,

        relation,

        reference_text,

        target_text,

        wait_seconds=0.5,

    ):

        """

        Recovery helper for spatial OCR actions.



        relation:

            below

            above

            left

            right

        """



        relation = str(

            relation

        ).strip().lower()



        before = self.observe()



        if relation == "below":



            result = self.click_below(

                reference_text,

                target_text,

            )



        elif relation == "above":



            result = self.click_above(

                reference_text,

                target_text,

            )



        elif relation == "left":



            result = self.click_left_of(

                reference_text,

                target_text,

            )



        elif relation == "right":



            result = self.click_right_of(

                reference_text,

                target_text,

            )



        else:



            raise ValueError(

                "Unknown spatial relation: "

                f"{relation}"

            )



        if wait_seconds > 0:

            self.wait(

                wait_seconds

            )



        after = self.observe()



        changed = self.screen_changed(

            before,

            after,

        )



        return {

            "success": changed,

            "recovery_action": "spatial_click",

            "relation": relation,

            "reference_text": reference_text,

            "target_text": target_text,

            "result": result,

            "screen_changed": changed,

            "before": before,

            "after": after,

        }



    # ============================================================

    # AUTOMATIC LOCAL RECOVERY

    # ============================================================



    def recover(

        self,

        original_action,

        expected_text=None,

        wait_seconds=0.5,

    ):

        """

        Try safe local recovery strategies.



        Current recovery strategies:



        1. If original action is click_target:

           retry using the same target.



        2. If original action is a spatial click:

           retry using the same spatial relationship.



        No AI/API call is made.

        """



        if not isinstance(

            original_action,

            dict,

        ):

            raise TypeError(

                "Original action must be a dictionary."

            )



        action_name = original_action.get(

            "action"

        )



        arguments = original_action.get(

            "arguments",

            {},

        )



        if not isinstance(

            arguments,

            dict,

        ):

            arguments = {}



        # --------------------------------------------------------

        # RECOVERY: GENERIC CLICK

        # --------------------------------------------------------



        if action_name == "computer_click_target":



            target = arguments.get(

                "target"

            )



            position = arguments.get(

                "position",

                "first",

            )



            if target:



                result = self.recover_click_text(

                    target,

                    position,

                    wait_seconds,

                )



                if expected_text:

                    result[

                        "expected_visible"

                    ] = self.text_visible(

                        result["after"],

                        expected_text,

                    )



                    result["success"] = (

                        result["expected_visible"]

                    )



                return result



        # --------------------------------------------------------

        # RECOVERY: SPATIAL CLICK

        # --------------------------------------------------------



        if action_name == "computer_click_spatial":



            relation = arguments.get(

                "relation"

            )



            reference_text = arguments.get(

                "reference_text"

            )



            target_text = arguments.get(

                "target_text"

            )



            if (

                relation

                and reference_text

                and target_text

            ):



                result = self.recover_spatial_click(

                    relation,

                    reference_text,

                    target_text,

                    wait_seconds,

                )



                if expected_text:

                    result[

                        "expected_visible"

                    ] = self.text_visible(

                        result["after"],

                        expected_text,

                    )



                    result["success"] = (

                        result["expected_visible"]

                    )



                return result



        return {

            "success": False,

            "recovered": False,

            "message": (

                "No local recovery strategy "

                "is available for this action."

            ),

        }



    # ============================================================

    # ACT + AUTOMATIC RECOVERY

    # ============================================================



    def act_with_recovery(

        self,

        action,

        expected_text=None,

        wait_seconds=0.5,

        max_retries=1,
        before=None,

    ):

        """

        Execute an action.



        If verification fails, retry locally.



        Flow:



            Observe

              ↓

            Act

              ↓

            Verify

              ↓

            Success?

             /   \\

           YES    NO

            |      |

           DONE   Recover

                    ↓

                  Verify

        """



        if not isinstance(

            action,

            dict,

        ):

            raise TypeError(

                "Action must be a dictionary."

            )



        # --------------------------------------------------------

        # FIRST ATTEMPT

        # --------------------------------------------------------



        first = self.act_and_verify(

            action,

            expected_text,

            wait_seconds,
            before=before,

        )



        attempts = [

            {

                "attempt": 1,

                "type": "original",

                "result": first,

            }

        ]



        if first["success"]:



            return {

                "success": True,

                "recovered": False,

                "attempts": attempts,

                "final_screen": first[

                    "after"

                ],

            }



        # --------------------------------------------------------

        # RECOVERY ATTEMPTS

        # --------------------------------------------------------



        for retry_number in range(

            1,

            max_retries + 1,

        ):



            recovery = self.recover(

                action,

                expected_text,

                wait_seconds,

            )



            attempts.append(

                {

                    "attempt": retry_number + 1,

                    "type": "recovery",

                    "result": recovery,

                }

            )



            if recovery.get(

                "success",

                False,

            ):



                return {

                    "success": True,

                    "recovered": True,

                    "attempts": attempts,

                    "final_screen": recovery.get(

                        "after"

                    ),

                }



        # --------------------------------------------------------

        # FAILED

        # --------------------------------------------------------



        final_screen = self.observe()



        return {

            "success": False,

            "recovered": False,

            "attempts": attempts,

            "final_screen": final_screen,

        }



    # ============================================================

    # EXECUTE COMPUTER GOAL

    # ============================================================



    def execute_goal(

        self,

        goal,

        actions,

    ):

        """

        Execute a locally prepared computer goal.



        Every action uses:



            Observe

            Act

            Wait

            Observe

            Verify



        Failed supported click actions receive one

        local recovery attempt.

        """



        if not isinstance(

            actions,

            list,

        ):

            raise TypeError(

                "Goal actions must be a list."

            )



        steps = []
        previous_after = None



        for action in actions:



            step = self.act_with_recovery(

                action,

                expected_text=None,

                wait_seconds=0.5,

                max_retries=1,
                before=previous_after,

            )



            steps.append(

                step

            )
            previous_after = step.get("final_screen")



            # ----------------------------------------------------

            # Stop if a local action could not be completed.

            # ----------------------------------------------------



            if not step.get(

                "success",

                False,

            ):



                break



        final_screen = (
            previous_after
            if previous_after is not None
            else self.observe()
        )



        return {

            "goal": goal,

            "success": all(

                step.get(

                    "success",

                    False,

                )

                for step in steps

            ) if steps else True,

            "steps": steps,

            "final_screen": final_screen,

        }