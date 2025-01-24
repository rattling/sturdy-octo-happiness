import pytest
import yaml
from proj.dsl.dsl_executor import DSLExecutor
from proj.scripts.reset_db import reset_db
from proj.utils.path_helpers import get_sample_plans_dir


@pytest.fixture(scope="module")
def dsl_executor():
    """Fixture to initialize DSLExecutor with a reset database."""
    reset_db()
    return DSLExecutor("scm")


@pytest.fixture
def sample_task_yaml():
    """Fixture to load a sample multi-step task YAML."""
    SAMPLE_PLANS_DIR = get_sample_plans_dir("scm")
    PLAN_PATH = f"{SAMPLE_PLANS_DIR}/task1.yaml"
    with open(PLAN_PATH, "r") as f:
        return f.read()


def test_multistep_task(dsl_executor, sample_task_yaml):
    """
    Test a multi-step DSL task by executing the task and verifying the context outputs.

    Args:
        dsl_executor (DSLExecutor): The initialized DSLExecutor.
        sample_task_yaml (str): The YAML string of the multi-step task.
    """
    # Execute the task
    dsl_executor.execute_task(sample_task_yaml)

    # Load the task YAML for reference
    task = yaml.safe_load(sample_task_yaml)

    # Assertions for context outputs
    expected_outputs = {
        "pending_orders": [
            {
                "order_id": "O001",
                "order_date": "2025-01-01",
                "status": "Pending",
            },
            {
                "order_id": "O003",
                "order_date": "2025-01-03",
                "status": "Pending",
            },
        ],
        "stock_allocation_results": [
            {
                "product_id": "P003",
                "newly_allocated_quantity": 1,
                "remaining_quantity": 99,
            },
        ],
        "production_allocation_results": [
            {
                "product_id": "P003",
                "newly_allocated_quantity": 1,
                "remaining_quantity": 98,
            },
        ],
        "production_schedule_results": [
            {
                "schedule_id": "PS_O003_P003_20250108",
                "product_id": "P003",
                "start_date": "2025-01-08",
                "end_date": "2025-01-08",
                "quantity": 98,
                "status": "Scheduled",
            },
        ],
        "notification_result": {"status": "success", "message": "Yay!"},
    }

    for key, expected_value in expected_outputs.items():
        assert (
            key in dsl_executor.dsl_context
        ), f"{key} is missing in DSL context."
        assert dsl_executor.dsl_context[key] == expected_value, (
            f"Value for {key} did not match.\n"
            f"Expected: {expected_value}\n"
            f"Got: {dsl_executor.dsl_context[key]}"
        )
