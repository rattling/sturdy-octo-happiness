import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_project_dir(*args):
    """
    Constructs a path relative to the project base directory.
    :param args: Path components relative to the base directory.
    :return: Absolute path as a string.
    """
    return os.path.join(BASE_DIR, *args)


def get_app_dir(app_name, *args):
    """
    Constructs a path relative to a specific app directory.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :param args: Additional path components relative to the app directory.
    :return: Absolute path as a string with trailing slash.
    """
    return os.path.join(get_project_dir("apps"), app_name, *args)


def get_prompt_dir(app_name):
    """
    Constructs a path to the prompts folder within an app.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :return: Absolute path as a string with trailing slash.
    """
    return f"{get_app_dir(app_name, 'prompts')}/"


def get_scenario_dir(app_name):
    """
    Constructs a path to the scenarios folder within an app.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :return: Absolute path as a string with trailing slash.
    """
    return f"{get_app_dir(app_name, 'scenarios')}/"


def get_scenario_file(app_name, scenario_number):
    """
    Constructs a path to a specific scenario markdown file.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :param scenario_number: The number of the scenario.
    :return: Absolute path as a string.
    """
    return os.path.join(
        get_scenario_dir(app_name), f"scenario{scenario_number}.md"
    )


def get_db_dir(app_name):
    """
    Constructs a path to the database folder of an app.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :return: Absolute path as a string with trailing slash.
    """
    return f"{get_app_dir(app_name, 'db')}/"


def get_db_file(app_name):
    """
    Constructs a path to the database file of an app.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :return: Absolute path as a string.
    """
    return os.path.join(get_db_dir(app_name), f"{app_name}.db")


def get_sample_plans_dir(app_name):
    """
    Constructs a path to the sample plans folder of an app.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :return: Absolute path as a string with trailing slash.
    """
    return f"{get_app_dir(app_name, 'sample_plans')}/"


def get_sample_plan_file(app_name, plan_num):
    """
    Constructs a path to a specific sample plan YAML file within an app.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :param plan_num: The number of the sample plan.
    :return: Absolute path as a string.
    """
    return os.path.join(get_sample_plans_dir(app_name), f"task{plan_num}.yaml")


def get_base_prompt_file(app_name):
    """
    Constructs a path to the base_prompt.md file within the prompts folder of an app.
    :param app_name: The name of the app (e.g., 'scm', 'franchise').
    :return: Absolute path as a string.
    """
    return os.path.join(get_prompt_dir(app_name), "base_prompt.md")
