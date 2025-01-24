import pytest
import yaml
import inspect
import logging
from pprint import pprint


from proj.dsl.dsl_executor import DSLExecutor
from proj.scripts.reset_db import reset_db
from proj.apps.scm import api as scm_api_module


@pytest.fixture(scope="function")
def dsl_executor():
    """Initialize DSLExecutor with a reset database."""
    reset_db()
    return DSLExecutor("scm")


def extract_dsl_examples(module):
    """
    Extracts DSL examples from docstrings of all methods in the given module,
    excluding the SCMAPI class itself.

    Args:
        module (module): The module to inspect.

    Returns:
        list: A list of tuples (method_name, dsl_task).
    """
    dsl_examples = []

    # Iterate over all classes in the module
    for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
        # Skip the SCMAPI class
        if class_name == "SCMAPI":
            continue

        # Iterate over all methods in the class
        for method_name, method in inspect.getmembers(
            class_obj, inspect.isfunction
        ):
            # Skip __init__ methods
            if method_name == "__init__":
                continue
            docstring = inspect.getdoc(method)
            if docstring and "DSL Example" in docstring:
                try:
                    # Extract the DSL YAML block from the docstring
                    dsl_yaml = (
                        docstring.split("DSL Example:")[1].strip().strip("```")
                    )
                    dsl_step = yaml.safe_load(dsl_yaml)

                    # Handle cases where DSL example is a single-step wrapped in a list
                    if isinstance(dsl_step, list) and len(dsl_step) == 1:
                        dsl_step = dsl_step[0]

                    # Wrap the DSL step(s) with a task structure
                    dsl_task = {
                        "task": f"Test {class_name}.{method_name}",
                        "steps": [dsl_step],
                    }

                    logging.info(
                        f"Found DSL Example in {class_name}.{method_name}: {dsl_task}"
                    )
                    dsl_examples.append(
                        (f"{class_name}.{method_name}", dsl_task)
                    )
                except Exception as e:
                    logging.error(
                        f"Failed to parse DSL example for {class_name}.{method_name}: {e}"
                    )

    if not dsl_examples:
        logging.warning("No DSL examples found in the module.")
    return dsl_examples


@pytest.mark.parametrize(
    "method_name,dsl_task", extract_dsl_examples(scm_api_module)
)
def test_api_dsl_examples(dsl_executor, method_name, dsl_task):
    """
    Tests DSL examples extracted from the SCM API module.

    Args:
        dsl_executor (DSLExecutor): The initialized DSLExecutor.
        method_name (str): The name of the API method being tested.
        dsl_task (dict): The DSL task parsed from the docstring.
    """
    print(f"Testing DSL task for method: {method_name}")

    assert (
        "steps" in dsl_task
    ), f"DSL task for {method_name} should contain steps."
    for step in dsl_task["steps"]:
        assert (
            "name" in step
        ), f"Each step in {method_name} should have a name."
        assert (
            "function" in step
        ), f"Each step in {method_name} should define a function."

    try:
        # Execute the DSL task using the DSLExecutor
        dsl_executor.execute_task(yaml.dump(dsl_task))
    except Exception as e:
        pytest.fail(f"DSL execution failed for method {method_name}: {e}")

    # Assert that there is exactly one key-value pair in the context i.e. a step result
    assert (
        len(dsl_executor.dsl_context) == 1
    ), "The DSL context should have exactly one key-value pair."

    # Assert that the value for the single key is not null
    key, value = next(
        iter(dsl_executor.dsl_context.items())
    )  # Get the first (and only) key-value pair
    assert (
        value is not None
    ), f"The value for the context key '{key}' should not be null."
