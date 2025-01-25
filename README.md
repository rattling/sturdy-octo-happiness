# sturdy-octo-happiness
**R&amp;D for LLM powered workflows**

This Python project enables the creation of workflows from English-language prompts, executed directly on your application's API. It bridges the gap between natural language and precise API calls using a structured Domain Specific Language (DSL). 

### How it Works

1. **Define Your API:** Write and expose your API with functionality documented using a DSL. Each API method includes example DSL instructions in its docstring, guiding how it can be used.
   
2. **Generate DSL from Prompts:** A base instruction describing the DSL format is sent to the LLM, alongside your specific task or scenario. The LLM generates valid DSL workflows tailored to your API.

3. **Execute DSL Workflows:** The generated DSL is parsed and executed, translating natural language instructions into actionable workflows.

### Why Use This?

By defining a DSL layer, you guide LLMs to produce precise workflows, minimizing errors and ambiguity. This approach ensures:

- Clear and consistent output from LLMs, tailored to your API.
- The ability to handle complex workflows with loops, conditions, and multi-step logic.
- A clean separation between natural language and API logic, making your system robust and easier to maintain.

This makes it a powerful foundation for integrating LLMs into systems requiring precise, reliable API interactions.

---

# Installation
```bash
python 3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e . # Install the app
python scripts/reset_db.py # Create and populate the db for the test app "scm"
```
Copy env.example to .env and fill in the values for your LLM keys etc.

---

# Usage
```bash
python scripts/run_with_api.py # Run a task with the scm app using it's native python API
python scripts/run_with_dsl.py # Run a task with the app against a pre-baked DSL task
#COMING SOON! python scripts/run_with_llm.py # Run the task against an English scenario prompt provided to an LLM 
```
# Run the tests
```bash
pytest
```

# Create a New App
<UNDER HEAVY CONSTRUCTION>
```bash
mkdir apps/new_app
touch apps/new_app/__init__.py

---

# Developer Notes

Archive folder contains some old code that may not run but keeping temporarily for reference..


