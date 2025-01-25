import yaml
import logging
import inspect
from openai import OpenAI
import re
import os

from proj.utils.path_helpers import (
    get_base_prompt_file,
    get_scenario_file,
    get_prompt_dir,
    get_db_dir,
)
from proj.config.logging_config import setup_logging
from proj.dsl.dsl_executor import DSLExecutor
from proj.utils.env_helpers import get_openai_api_key

setup_logging()

OPENAPI_KEY = get_openai_api_key()
client = OpenAI(api_key=OPENAPI_KEY)
GPT_MODEL = "gpt-4o"


class Orchestrator:
    def __init__(self, app_name):
        self.app_name = app_name
        self.base_prompt_path = get_base_prompt_file(app_name)
        self.prompt_dir = get_prompt_dir(app_name)
        self.db_dir = get_db_dir(app_name)
        self.executor = DSLExecutor(app_name)
        self.dsl_context = self.executor.dsl_context

    def orchestrate_workflow(self, scenario_num):

        self.scenario_path = get_scenario_file(self.app_name, scenario_num)

        prompt = self.assemble_prompt(
            self.db_dir,
            self.base_prompt_path,
            self.scenario_path,
            self.executor.step_registry,
        )

        logging.info("Prompt:\n%s", prompt)

        response = client.chat.completions.create(
            model=GPT_MODEL, messages=[{"role": "user", "content": prompt}]
        )
        dsl_plan = self.clean_llm_output(
            response.choices[0].message.content.strip()
        )

        logging.info("Generated DSL Plan:\n%s", dsl_plan)

        # Validate and execute DSL plan
        try:
            yaml.safe_load(dsl_plan)
            logging.info("Executing DSL plan...")
            self.executor.execute_task(dsl_plan)
        except yaml.YAMLError as e:
            logging.error(f"Error in DSL YAML: {e}")

    def assemble_prompt(
        self, db_dir, base_prompt_path, scenario_path, step_registry
    ):
        """
        Assembles the full prompt by combining base prompt, function descriptions, and scenario.

        Args:
            scenario_number (int): The scenario number.
            step_registry (dict): The function registry for the application.

        Returns:
            str: The complete prompt.
        """

        # Assmble content for Prompt
        base_prompt = self.read_file(base_prompt_path)
        scenario_details = self.read_file(scenario_path)
        db_schema = self.read_file(f"{db_dir}/db_schema.md")
        step_functions_docstring = self.describe_functions(step_registry)

        # Define replacements
        replacements = {
            "{step_functions_docstring}": step_functions_docstring,
            "{db_schema}": db_schema,
            "{scenario_details}": scenario_details,
        }

        # Perform explicit replacements
        for placeholder, replacement in replacements.items():
            base_prompt = base_prompt.replace(placeholder, replacement)

        return base_prompt

    def describe_functions(self, step_registry):
        """
        Generates Markdown descriptions for the given function registry.

        Args:
            step_registry (dict): A dictionary of function names and metadata.

        Returns:
            str: Markdown-formatted string describing each function.
        """
        function_descriptions = []
        for name, metadata in step_registry.items():
            # Extract the actual function
            func = (
                metadata.get("function")
                if isinstance(metadata, dict)
                else None
            )

            # Check if the function is callable
            if callable(func):
                # Get the docstring for the function
                doc = inspect.getdoc(func) or "No description available."
                function_descriptions.append(f"### {name}\n\n{doc}\n")
            else:
                function_descriptions.append(
                    f"### {name}\n\nNo valid function found.\n"
                )

        return "\n".join(function_descriptions)

    def _mock_llm_response(self, prompt):
        """Simulates an LLM response for testing purposes."""
        logging.debug(f"Prompt sent to LLM: {prompt}")
        return """
        task: sample_task
        steps:
          - name: Sample Step
            type: action
            function: query_table
            arguments:
              table: SampleTable
              condition: "status = 'Pending'"
              output_fields: id, name
            output_var: sample_output
        """

    def clean_llm_output(self, llm_output):
        """
        Cleans the raw output from the LLM by removing enclosing code fences and extra whitespace.

        Args:
            llm_output (str): The raw output from the LLM.

        Returns:
            str: The cleaned output ready for YAML processing.
        """
        # Remove any enclosing triple backticks (e.g., ```yaml or ```).
        cleaned_output = re.sub(
            r"^```(?:yaml)?\n|```$", "", llm_output.strip(), flags=re.MULTILINE
        )
        return cleaned_output

    def read_file(self, file):
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}")
        with open(file, "r") as f:
            return f.read()
