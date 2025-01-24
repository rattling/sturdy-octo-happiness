import yaml

from proj.utils.path_helpers import construct_app_path
from proj.config.logging_config import setup_logging

from proj.dsl.dsl_executor import DSLExecutor

setup_logging()


class Orchestrator:
    def __init__(self, app_name):
        self.app_name = app_name
        self.paths = construct_app_path(app_name)
        self.executor = DSLExecutor(self.paths.db_path)
        self.dsl_context = self.executor.dsl_context

    def orchestrate_workflow(self, scenario_num):
        scenario_path = (
            self.paths.scenarios_dir / f"scenario{scenario_num}.yaml"
        )
        base_prompt_path = self.paths.prompts_dir / "base_prompt.md"

        # Read scenario and base prompt
        with open(scenario_path, "r") as f:
            scenario_details = f.read()

        with open(base_prompt_path, "r") as f:
            base_prompt = f.read()

        prompt = base_prompt.replace("{scenario_details}", scenario_details)

        # Call the LLM (mocked here)
        logging.info("Sending prompt to LLM...")
        dsl_plan = self._mock_llm_response(prompt)

        # Validate and execute DSL plan
        try:
            yaml.safe_load(dsl_plan)
            logging.info("Executing DSL plan...")
            self.executor.execute_task(dsl_plan)
        except yaml.YAMLError as e:
            logging.error(f"Error in DSL YAML: {e}")

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
