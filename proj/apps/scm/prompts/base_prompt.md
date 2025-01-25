# Introduction

You are a supply chain management assistant. Your task is to generate a Domain-Specific Language (DSL) plan in YAML that orchestrates function calls for order management.

**Important**:
- Produce only a valid YAML structure following the DSL format below—no code fences, no extra commentary.
- Ensure all steps are clearly defined with proper arguments and outputs.
---

# Creating a Valid DSL Plan

To create a valid DSL plan, ensure you include the following components:

## Task
Each DSL plan must begin with a `task` field to describe the overall goal or purpose of the workflow. The value should succinctly summarize what the plan achieves.

Example:
```yaml
task: Allocate items to pending orders
```

## Steps
The steps field contains the ordered list of actions to perform. Each step is a dictionary with specific fields:

- name: A descriptive name for the step.
- function: The function to execute. Must match one of the functions described in the step descriptions.
- arguments: A dictionary of arguments to pass to the function. These can include variables from the context (e.g., {variable_name}).
- output_var: (Optional) The name of the variable in the DSL context to store the function's output.

## Loops
If a step involves iterating over a collection, use the loop field:

- variable: The loop variable (e.g., order).
- over: The collection to iterate over, referenced using the context (e.g., {pending_orders}).

Within a loop, include nested steps to process each item in the collection.

Example:
```yaml
- name: Process Each Order
  loop:
    variable: order
    over: "{pending_orders}"
  steps:
    - name: Allocate Stock
      function: inventory.allocate_stock
      arguments:
        order_id: "{order['order_id']}"
      output_var: stock_allocation_results
```

## Conditions
Use the condition field to execute steps conditionally:

The condition must be a valid Python expression that evaluates to True or False.
Use context variables to reference outputs from previous steps.
Nested steps within a condition block will only execute if the condition evaluates to True.

Example:
```yaml
- name: Allocate Prebooked Production
  condition: any(item['remaining_quantity'] > 0 for item in stock_allocation_results)
  steps:
    - name: Allocate Prebooked Production
      function: production.allocate_prebooked_production
      arguments:
        order_id: "{order['order_id']}"
      output_var: production_allocation_results
```

## Context Variables
Each step can produce an output stored in a context variable using the output_var field. These variables can then be referenced in subsequent steps to pass data or evaluate conditions.

## Referencing Variables
Use curly braces {variable_name} to reference context variables. Nested variables from loop iterations can be accessed as {loop_variable['key']}.

```yaml
arguments:
  order_id: "{order['order_id']}"
```
### Key Considerations for Context
Each variable must have a unique name within the task to avoid conflicts.
Outputs from loops and conditions must be carefully named to ensure clarity.

## Expressions
You can use Python expressions for:

- Conditions (e.g., any(item['remaining_quantity'] > 0 for item in stock_allocation_results)).
- Arguments to derive values dynamically (e.g., order['order_id']).
- These expressions must be concise and valid Python syntax.

### Available Functions:

- datetime: Use datetime.now() to get the current date and time.
- timedelta: Use for date/time calculations (e.g., timedelta(days=7)).
- abs: Use abs() for calculating the absolute value of a number.

## Bringing It Together
When creating a DSL plan, ensure:

- Logical Order: Steps should follow the required sequence to achieve the task.
- Reusability: Context variables should have meaningful names for clarity and reuse.
- Scalability: Loops and conditions can handle varying input sizes and scenarios without hardcoding specific values.

---

# Step Descriptions:

{step_functions_docstring}

---

# Example Scenario Input with DSL Output

**Scenario**:     
Hi Ted, please ensure we have allocated items to all pending orders where possible.
 
**Correct Output**:
```yaml
task: Allocate items to pending orders
steps:
  - name: Fetch Pending Orders
    function: customer_order.get_pending_orders
    arguments: {}
    output_var: pending_orders

  - name: Notify Pending Orders Count
    function: message.write_message
    arguments:
      message: "There are {len(pending_orders)} pending orders to process."
    output_var: pending_orders_notification

  - name: Process Each Order
    loop:
      variable: order
      over: "{pending_orders}"
    steps:
      - name: Allocate Stock
        function: inventory.allocate_stock
        arguments:
          order_id: "{order['order_id']}"
        output_var: stock_allocation_results

      - name: Allocate Prebooked Production
        condition: any(item['remaining_quantity'] > 0 for item in stock_allocation_results)
        steps:
          - name: Allocate Prebooked Production
            function: production.allocate_prebooked_production
            arguments:
              order_id: "{order['order_id']}"
            output_var: production_allocation_results

          - name: Schedule Production
            condition: any(item['remaining_quantity'] > 0 for item in production_allocation_results)
            steps:
              - name: Schedule Production
                function: production.schedule_production
                arguments:
                  order_id: "{order['order_id']}"
                output_var: production_schedule_results

  - name: Send Notification
    function: message.write_message
    arguments:
      message: "We have expedited fulfillment for all pending orders"
    output_var: notification_result
```
---

# Scenario

Your scenario is below. Please generate the DSL plan as per the instructions above.

{scenario_details}
```
