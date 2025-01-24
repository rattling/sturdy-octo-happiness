import sqlite3
import yaml
import importlib
import inspect
import logging
import traceback

from proj.config.logging_config import setup_logging
from proj.utils.path_helpers import get_db_file
import proj.dsl.dsl_steps as dsl_steps


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
            loop_over (list or range): The iterable to loop over.
            steps (list): Nested steps to execute for each iteration.

        Returns:
            None
        """
        # Check if `loop_over` resolves to a valid list
        if not isinstance(loop_over, (list, range)):
            logging.error(
                f"Loop variable '{loop_variable}' cannot iterate over unresolved or invalid value: {loop_over}"
            )
            return

        try:
            for item in loop_over:
                self.dsl_context[loop_variable] = item
                logging.info(f"Loop iteration with {loop_variable} = {item}")
                for step in steps:
                    self._execute_step(step)
        except Exception as e:
            logging.error(f"Error executing loop over '{loop_over}': {e}")

    def _execute_condition(self, condition, steps):
        """
        Evaluates a condition and executes nested steps if the condition is true.

        Args:
            condition (str): A Python expression to evaluate.
            steps (list): A list of nested steps to execute if the condition is true.

        Returns:
            None
        """
        try:
            condition_result = eval(condition, {}, self.dsl_context)
            if condition_result:
                logging.info(f"Condition '{condition}' evaluated to True.")
                for step in steps:
                    self._execute_step(step)
            else:
                logging.info(f"Condition '{condition}' evaluated to False.")
        except Exception as e:
            logging.error(f"Error evaluating condition '{condition}': {e}")

    def _execute_step(self, step):
        """
        Executes a single DSL step.

        Args:
            step (dict): The step definition containing:
                - name: The name of the step.
                - function: The function to execute (e.g., 'product.get_products').
                - arguments: A dictionary of arguments to pass to the function.
                - output_var: The variable to store the result in the DSL context.

        Returns:
            None
        """

        # Check for loop
        loop = step.get("loop")
        if loop:
            loop_variable = loop.get("variable")
            loop_over = self._resolve_arguments(loop.get("over"))
            nested_steps = step.get("steps", [])
            self._execute_loop(loop_variable, loop_over, nested_steps)
            return

        # Extract the condition if present
        condition = step.get("condition")
        if condition:
            nested_steps = step.get("steps", [])
            self._execute_condition(condition, nested_steps)
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

        # Resolve arguments
        resolved_args = self._resolve_arguments(args)

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

    def _resolve_arguments(self, args):
        """
        Resolves arguments, supporting strings, nested dictionaries, and lists.

        Args:
            args (Any): The arguments to resolve. Can be a string, dictionary, or list.

        Returns:
            Any: Resolved arguments with placeholders replaced by their values.
        """

        def resolve(value):
            if isinstance(value, str) and "{" in value and "}" in value:
                return self._resolve_placeholders(value)
            elif isinstance(value, list):
                return [resolve(v) for v in value]
            elif isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            else:
                return value

        # Handle the case where args itself is a string
        if isinstance(args, str):
            return self._resolve_placeholders(args)

        # Handle cases where args is a dictionary or other iterable
        return {key: resolve(value) for key, value in args.items()}

    def _resolve_placeholders(self, text):
        """
        Resolves placeholders within a string using the DSL context.

        Args:
            text (str): String containing placeholders (e.g., '{{var_name}}').

        Returns:
            str: Resolved string or a warning about unresolved variables.
        """
        try:
            return eval(text.strip("{}"), {}, self.dsl_context)
        except KeyError as e:
            logging.error(
                f"Failed to resolve '{text}' in context. Missing variable: {e}",
                exc_info=True,
            )
            return f"<Unresolved {text}>"
        except Exception as e:
            logging.error(
                f"Error resolving placeholders in '{text}': {e}",
                exc_info=True,
            )
            return f"<Error resolving {text}>"
