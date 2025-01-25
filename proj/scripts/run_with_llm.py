from proj.orchestrator import Orchestrator

if __name__ == "__main__":
    app_name = "scm"
    scenario_num = 3
    orchestrator = Orchestrator(app_name)
    orchestrator.orchestrate_workflow(scenario_num)
