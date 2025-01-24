# sturdy-octo-happiness
**R&amp;D for LLM powered workflows**

This is a Python project that accepts a scenario in English to perform some tasks against an applications API. The scenario will be sent to your LLM of choice along with a base prompt and the LLM will return a task plan in our Domain Specific Language. The task plan will be executed on the app and the results will be returned.

For now the LLM is one-shot and the test app is a simple SQLite database with an API for querying and updating tables. The test app is called "scm" (Supply Chain Management).

You can run various tasks using the native API or DSL directly These tasks are then replicated from English language instruction in the tests to see how well the LLM can generate the same tasks dynamically from a prompt. The tasks progress in complexity to test the limits of the LLM and the process.


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

# Usage
```bash
python scripts/run_with_api.py # Run a task with the scm app using it's native python API
python scripts/run_with_dsl.py # Run a task with the app against a pre-baked DSL task
#COMING SOON! python scripts/run_with_llm.py # Run the task against an English scenario prompt provided to an LLM 
```
pytest # Run the tests
```

# Create a New App
<UNDER HEAVY CONSTRUCTION>
```bash
mkdir apps/new_app
touch apps/new_app/__init__.py


