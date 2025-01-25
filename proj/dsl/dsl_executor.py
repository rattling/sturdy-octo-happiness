import sqlite3
import yaml
import importlib
import inspect
import logging
import traceback
import re

from proj.config.logging_config import setup_logging
from proj.utils.path_helpers import get_db_file

setup_logging()


class DSLExecutor:
    def __init__(self, app_name):
        self.app_name = app_name
        db_path = get_db_file(app_name)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.dsl_context = {}
        self.step_registry = self._register_steps(self.app_name)

    def execute_task(self, task_yaml):
        task = yaml.safe_load(task_yaml)
        steps = task.get("steps", [])
        for step in steps:
            self._execute_step(step)

    def _execute_loop(self, loop_variable, loop_over, steps):
        """
        Executes a loop, iterating over a list or range and executing nested steps.

        Args:
            loop_variable (str): The variable name to assign in the loop.
            loop_over (str): The string representation of the iterable (e.g., "{pending_orders}").
            steps (list): Nested steps to execute for each iteration.

        Returns:
            None
        """
        # Resolve placeholders in `loop_over`
        resolved_loop_over = self._resolve_placeholders(loop_over)

        try:
            # Ensure the resolved `loop_over` is iterable
            resolved_iterable = eval(resolved_loop_over, {}, self.dsl_context)

            if not isinstance(resolved_iterable, (list, range)):
                raise ValueError(
                    f"Resolved value is not iterable: {resolved_iterable}"
                )

            for item in resolved_iterable:
                # Create a combined context with the loop variable
                loop_context = {**self.dsl_context, loop_variable: item}
                logging.info(f"Loop iteration with {loop_variable} = {item}")

                for step in steps:
                    # Pass the updated context with the loop variable to each nested step
                    self._execute_step(step, additional_context=loop_context)
        except Exception as e:
            logging.error(
                f"Loop variable '{loop_variable}' cannot iterate over unresolved or invalid value: {resolved_loop_over}. Error: {e}"
            )

    def _execute_condition(self, condition, steps, additional_context=None):
        """
        Evaluates a condition and executes nested steps if the condition is true.

        Args:
            condition (str): A Python expression to evaluate.
            steps (list): A list of nested steps to execute if the condition is true.
            additional_context (dict, optional): Additional context for resolving placeholders.

        Returns:
            None
        """
        # Merge global context and additional context
        context = {**self.dsl_context, **(additional_context or {})}

        resolved_condition = self._resolve_condition(condition, context)

        if (
            resolved_condition
        ):  # Only execute steps if the condition resolves to True
            logging.info(f"Condition '{condition}' evaluated to True.")
            for step in steps:
                self._execute_step(step, additional_context=context)
        else:
            logging.info(f"Condition '{condition}' evaluated to False.")

    def _execute_step(self, step, additional_context=None):
        """
        Executes a single DSL step.

        Args:
            step (dict): The step definition containing:
                - name: The name of the step.
                - function: The function to execute (e.g., 'product.get_products').
                - arguments: A dictionary of arguments to pass to the function.
                - output_var: The variable to store the result in the DSL context.
            additional_context (dict, optional): Additional context for resolving placeholders (e.g., loop variables).

        Returns:
            None
        """

        # Check for loop
        loop = step.get("loop")
        if loop:
            loop_variable = loop.get("variable")
            loop_over = loop.get("over")
            nested_steps = step.get("steps", [])
            self._execute_loop(loop_variable, loop_over, nested_steps)
            return

        # Extract the condition if present
        condition = step.get("condition")
        if condition:
            nested_steps = step.get("steps", [])
            condition_resolved = self._resolve_arguments(
                condition, additional_context=additional_context
            )
            self._execute_condition(
                condition_resolved,
                nested_steps,
                additional_context=additional_context,
            )
            return

        step_name = step.get("name", "Unnamed Step")
        func_name = step.get("function")
        args = step.get("arguments", {})
        output_var = step.get("output_var")

        logging.info(f"Executing Step: {step_name}")
        logging.debug(f"Step Details: {step}")
        logging.debug(f"Current Context: {self.dsl_context}")

        # Retrieve the function metadata from the registry
        func_metadata = self.step_registry.get(func_name)
        if not func_metadata:
            logging.error(f"Function '{func_name}' not implemented.")
            return

        func = func_metadata["function"]  # Extract the actual function

        # Resolve arguments with additional context
        resolved_args = self._resolve_arguments(args, additional_context)

        try:
            # Call the function
            result = func(**resolved_args)
        except Exception as e:
            logging.error(f"Error executing function '{func_name}': {e}")
            return

        # Store the result in the DSL context if output_var is provided
        if output_var:
            self.dsl_context[output_var] = result
            logging.info(
                f"Step '{step_name}' completed. Output: {output_var} = {result}"
            )

    def _register_steps(self, app_name):
        """
        Dynamically creates a registry of core and app-specific step functions.

        Args:
            app_name (str): The name of the app for app-specific steps.

        Returns:
            dict: A registry mapping "Namespace.method_name" to the function object,
                with metadata indicating whether the step is "core" or "app".
        """
        registry = {}

        # Register core functions
        self._register_core_steps(registry)

        # Register app-specific functions
        self._register_app_steps(app_name, registry)

        return registry

    def _register_core_steps(self, registry):
        """
        Registers core step functions (from `CORE`) into the registry.

        Args:
            registry (dict): The step registry to populate.

        Returns:
            None
        """
        from proj.dsl.dsl_steps import (
            CORE,
        )  # Import CORE directly since we know its location

        try:
            core_instance = CORE(cursor=self.cursor)  # Initialize CORE class
            for attr_name in dir(core_instance):
                attr = getattr(core_instance, attr_name)
                if inspect.isclass(
                    type(attr)
                ):  # Check if it's a nested class (e.g., `Message`)
                    methods = inspect.getmembers(
                        attr, predicate=inspect.ismethod
                    )
                    for method_name, method in methods:
                        key = f"{attr_name.lower()}.{method_name}"
                        registry[key] = {"function": method, "source": "core"}
                        logging.info(f"Registered core function: {key}")
        except ImportError as e:
            logging.error("Core steps class 'CORE' not found.")
            logging.debug(traceback.format_exc())

    def _register_app_steps(self, app_name, registry):
        """
        Registers app-specific step functions into the registry.

        Args:
            app_name (str): The app name to load the API module from.
            registry (dict): The step registry to populate.

        Returns:
            None
        """
        try:
            app_module = importlib.import_module(f"proj.apps.{app_name}.api")
            api_classes = inspect.getmembers(app_module, inspect.isclass)

            # Identify the top-level API class by naming convention
            top_level_class_name = f"{app_name.upper()}API"
            top_level_class = next(
                (
                    cls
                    for cls_name, cls in api_classes
                    if cls_name == top_level_class_name
                ),
                None,
            )

            if not top_level_class:
                logging.error(
                    f"Top-level API class '{top_level_class_name}' not found in 'proj.apps.{app_name}.api'."
                )
                return

            # Initialize the top-level API class
            api_instance = top_level_class(cursor=self.cursor)

            # Register methods from the app-specific API
            for attr_name in dir(api_instance):
                attr = getattr(api_instance, attr_name)
                if inspect.isclass(type(attr)):
                    methods = inspect.getmembers(
                        attr, predicate=inspect.ismethod
                    )
                    for method_name, method in methods:
                        key = f"{attr_name.lower()}.{method_name}"
                        registry[key] = {"function": method, "source": "app"}
                        logging.info(
                            f"Registered app-specific function: {key}"
                        )

        except ImportError as e:
            logging.error(
                f"App-specific module 'proj.apps.{app_name}.api' not found."
            )
            logging.debug(traceback.format_exc())

    def _resolve_arguments(self, args, additional_context=None):
        """
        Resolves arguments, supporting strings, nested dictionaries, and lists.

        Args:
            args (Any): The arguments to resolve. Can be a string, dictionary, or list.
            additional_context (dict, optional): Additional context to use for resolving placeholders,
                                                such as loop-specific variables.

        Returns:
            Any: Resolved arguments with placeholders replaced by their values.
        """
        # Merge global context and additional context if provided
        context = {**self.dsl_context, **(additional_context or {})}

        def resolve(value):
            if isinstance(value, str) and "{" in value and "}" in value:
                # Resolve placeholders using the merged context
                return self._resolve_placeholders(value, context)
            elif isinstance(value, list):
                return [resolve(v) for v in value]
            elif isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            else:
                return value

        # Handle the case where args itself is a string
        if isinstance(args, str):
            return self._resolve_placeholders(args, context)

        # Handle cases where args is a dictionary or other iterable
        return {key: resolve(value) for key, value in args.items()}

    def _resolve_placeholders(self, text, context=None):
        """
        Resolves placeholders within a string using the provided context.

        Args:
            text (str): String containing placeholders (e.g., '{pending_orders[0]}' or '{len(pending_orders)}').
            context (dict, optional): A dictionary to use for resolving placeholders. Defaults to self.dsl_context.

        Returns:
            str: Resolved string with evaluated placeholders.
        """
        # Use the provided context or fallback to the DSL context
        context = context or self.dsl_context

        # Define a regex pattern to match placeholders enclosed in curly braces
        pattern = r"\{([^\}]+)\}"

        # Define a safe evaluation environment
        safe_globals = {
            "datetime": __import__(
                "datetime"
            ).datetime,  # Import the `datetime.datetime` class
            "timedelta": __import__(
                "datetime"
            ).timedelta,  # Import `timedelta` if needed
            "abs": abs,  # Add built-in functions as needed
        }

        def resolve_match(match):
            expression = match.group(
                1
            )  # Extract the expression inside the curly braces
            logging.debug(f"Attempting to resolve expression: {expression}")
            try:
                # Evaluate the expression in the safe environment with the given context
                value = eval(expression, safe_globals, context)
                logging.debug(f"Resolved '{expression}' to '{value}'")
                return str(value)  # Convert the result to a string
            except KeyError as e:
                logging.error(
                    f"Key error resolving placeholder '{expression}': {e}",
                    exc_info=True,
                )
                return f"<Unresolved {expression}>"
            except Exception as e:
                logging.error(
                    f"Error resolving placeholder '{expression}': {e}",
                    exc_info=True,
                )
                return f"<Error resolving {expression}>"

        try:
            # Use regex to find and resolve all placeholders in the string
            resolved_text = re.sub(pattern, resolve_match, text)
            logging.debug(f"Resolved text: {resolved_text}")
            return resolved_text
        except Exception as e:
            logging.error(
                f"Unexpected error resolving placeholders in '{text}': {e}",
                exc_info=True,
            )
            return f"<Error resolving {text}>"

    def _resolve_condition(self, condition, context=None):
        """
        Resolves and evaluates a condition expression using the given context.

        Args:
            condition (str): The condition expression to evaluate (e.g., 'len(pending_orders) > 0').
            context (dict, optional): A dictionary to use for resolving the condition. Defaults to self.dsl_context.

        Returns:
            bool: The result of the evaluated condition (True or False).
        """
        context = context or self.dsl_context

        # 1) Create a safe environment with datetime, timedelta, etc.
        safe_globals = {
            "datetime": __import__("datetime").datetime,
            "timedelta": __import__("datetime").timedelta,
            "abs": abs,
            # Add other built-ins or imports if we need them
        }

        logging.debug(f"Attempting to resolve condition: {condition}")
        try:
            # 2) Evaluate the condition using safe_globals (instead of {})
            result = eval(condition, safe_globals, context)
            logging.debug(f"Condition '{condition}' resolved to: {result}")
            return bool(result)
        except KeyError as e:
            logging.error(
                f"Key error resolving condition '{condition}': {e}",
                exc_info=True,
            )
            return False
        except Exception as e:
            logging.error(
                f"Error resolving condition '{condition}': {e}", exc_info=True
            )
            return False
