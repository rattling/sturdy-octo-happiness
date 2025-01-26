# sturdy-octo-happiness
**R&amp;D for LLM powered workflows**

This Python project enables the creation of workflows from English-language prompts, executed directly on your application's API. It bridges the gap between natural language and precise API calls using a structured Domain Specific Language (DSL). 

### How it Works

1. **Define Your API:** Write and expose your API with functionality documented using a DSL. Each API method includes example DSL instructions in its docstring, guiding how it can be used. These will be injected into the prompt.
   
2. **Generate DSL from Prompts:** A  instruction describing the DSL format is sent to the LLM, alongside your specific task or scenario. The LLM generates valid DSL workflows tailored to your API.

3. **Execute DSL Workflows:** The generated DSL is parsed and executed, translating natural language instructions into actionable workflows.

### Why Use a DSL layer?

By defining a DSL layer, you guide LLMs to produce precise workflows, minimizing errors and ambiguity. This approach ensures:

- Clear and consistent output from LLMs, tailored to your API.
- The ability to handle complex workflows with loops, conditions, and multi-step logic.
- A clean separation between natural language and API logic, making your system robust and easier to maintain.

The theory is that this will form a powerful foundation for integrating LLMs into systems requiring precise, reliable API interactions.

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
python scripts/run_with_llm.py # Run the task against an English scenario prompt provided to an LLM. Choose a scenario 1 to 5.
```

Add your own scenarios to the scenarios folder as scenario_6.md etc. and test them with run_with_llm.py

# Run the tests

A lot of testing on the DSL side to make sure pre-baked DSL tasks are working as expected.
```bash
pytest
```

# Create a New App

**UNDER HEAVY CONSTRUCTION**

To create a new app, create a new folder in the apps folder and add a __init__.py file. This will be the entry point for the app.

```bash
mkdir apps/new_app
touch apps/new_app/__init__.py
```
---

# Developer Notes

- Archive folder contains some old code that may not run but keeping temporarily for reference..
- See base_prompt_resolved.md for latest prompt with injections for function docstrings etc.

---


# Dicussion and Future Work

- Much of the work is in nailing down the API and DSL to minimize ambiguity and maximize flexibility. This is a work in progress.
  But results are promising. Injecting API docstrings etc. is working well to guide outputs.
- It is set to GPT 4o for now. We should add flags to choose model and also provide generic interface to add different providers
  including DeepSeek.
- The API is a bit uneven in terms of functionality and return signature, e.g. should be able to create customers/components etc.
- Currently it is one-shot, a ReAct loop to respond to errors and iterate until successful might be useful.
- Session management could be on system side and/or on LLM side (with e.g. OpenAI Assistant API)
- Would be good to formalize testing on the LLM scenario side and get a benchmark for improvements. (LLM to help build use cases and   score them?)
- Will look at BAML to see if can improve on DSl generation and validation - fuzzier matching would definitely be useful e.g.
    accepting alternative formulations such as timestamp.today, timestamp.timestamp.today and today.
- Should add a couple more apps and streamline the process of adding them or providing a layer to add existing apps with minimal   effort. 
- While concerns are reasonably seperated at the moment between API/DSL/Prompt, there are a few areas to improve e.g. inject connections rather than pass them as assuming a db connection needed. Should be able to expand to work against web APIs etc. where DB not exposed.


