from proj.dsl.dsl_executor import DSLExecutor
from proj.utils.path_helpers import get_sample_plans_dir
from proj.scripts.reset_db import reset_db


if __name__ == "__main__":
    """
    Run some pre-baked plans for SCM test db to try out tasks in DSL
    WARNING - THIS SCRIPT WILL RESET THE SCM DATABASE
    """

    reset_db()
    APP_NAME = "scm"
    SAMPLE_PLANS_DIR = get_sample_plans_dir(APP_NAME)
    PLAN_PATH = f"{SAMPLE_PLANS_DIR}/task1.yaml"

    executor = DSLExecutor(APP_NAME)

    with open(PLAN_PATH, "r") as f:
        task_yaml = f.read()
    executor.execute_task(task_yaml)
