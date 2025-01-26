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

The following Python functions can be used within expressions and only in expressions:
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

### message.write_message

Sends or logs a message.

Args:
    message (str): The resolved message to send or log.

Returns:
    dict: A dictionary containing the message that was sent or logged.

### component.check_component_availability

Checks the stock level of a specific component.

Args:
    component_id (str): The ID of the component to check.

Returns:
    int: The available stock for the component.

DSL Example:
```
- name: Check Component Availability
  function: component.check_component_availability
  arguments:
    component_id: "C001"
  output_var: component_stock
```

### component.check_components_for_product

Checks component stock for a given product

Args:
    product_id (str): The ID of the product to check inventory for.

Returns:
    list(dict):
    Example:
    [
        {
            "component_id": "C001",
            "required_quantity": 10,
            "available_quantity": 5,
        },
        {
            "component_id": "C002",
            "required_quantity": 5,
            "available_quantity": 3,
        },

DSL Example:
```
- name: Get Inventory for Production
  function: component.check_components_for_product
  arguments:
    product_id: "P001"
  output_var: production_inventory
```

### component.check_supplier_components

Retrieves the list of components available from a specific supplier.

Args:
    supplier_id (str): The ID of the supplier.

Returns:
    list[dict]:
    Example:
    [
        {
            "component_id": "C001",
            "available_quantity": 100,
            "cost_per_unit": 10,
        },
        {
            "component_id": "C002",
            "available_quantity": 50,
            "cost_per_unit": 20,
        },

DSL Example:
```
- name: Check Supplier Components
  function: component.check_supplier_components
  arguments:
    supplier_id: "S001"
  output_var: supplier_components
```

### component.place_component_order

Places an order for components from a supplier.

Args:
    supplier_id (str): The ID of the supplier.
    component_id (str): The ID of the component.
    quantity (int): The quantity to order.

Returns:
    dict:
    Example:
    {
        "status": "Success",
        "supplier_id": "S001",
        "component_id": "C001",
        "quantity_ordered": 100,
        "total_cost": 1000,

DSL Example:
```
- name: Place Component Order
  function: component.place_component_order
  arguments:
    supplier_id: "S001"
    component_id: "C001"
    quantity: 100
  output_var: order_confirmation
```

### component.reserve_stock_components

Reserves stock for production by reducing available stock quantities for components.

Args:
    product_id (str): The ID of the product to reserve stock for.
    quantity (int): The number of units to produce.

Returns:
    dict:
    Example:
    [
        {
            "component_id": "C001",
            "reserved_quantity": 10,
            "shortfall": 0,
        },
        {
            "component_id": "C002",
            "reserved_quantity": 3,
            "shortfall": 2,
        },

DSL Example:
```
- name: Reserve Components
  function: component.reserve_stock_components
  arguments:
    product_id: "P001"
    quantity: 50
  output_var: reservation_result
```

### customer.get_customer_details

Retrieves details for a specific customer.

Args:
    customer_id (str): The ID of the customer.

Returns:
    dict: Customer details including name, address, and contact information.
    Example
    [
        {
            "name": "John Doe",
            "address": 78 Laurels,
            "contact_info": "johndoe@gmail.com,
        },
        {
            "name": "Sebastian Tremmels",
            "address": 90 Canyons,
            "contact_info": "seb@gmail.com,
        },
    ]


DSL Example:
```
- name: Get Customer Details
function: get_customer_details
arguments:
    customer_id: "C001"
output_var: customer_details
```

### customer_order.cancel_order

Cancels an order and updates any related allocations, inventory, and production schedules.

Args:
    order_id (str): The ID of the order to cancel.

Returns:
    bool: True if the cancellation was successful, False otherwise.

DSL Example:
```
- name: Cancel Order
function: cancel_order
arguments:
    order_id: "O001"
output_var: cancel_success
```

### customer_order.create_order

Creates a new order for a customer.

Args:
    customer_id (str): The ID of the customer placing the order.
    order_details (list[dict]): A list of product IDs and quantities.

Returns:
    str: The ID of the newly created order.

DSL Example:
```
- name: Create Order
  function: customer_order.create_order
  arguments:
    customer_id: "C001"
    order_details:
      - product_id: "P001"
        quantity: 10
      - product_id: "P002"
        quantity: 5
  output_var: new_order_id
```

### customer_order.get_order_details

Retrieves detailed information for a specific order.

Args:
    order_id (str): The ID of the order to retrieve details for.

Returns:
    list[dict]:
    Example:
    [
        {
            "product_id": "P001",
            "quantity": 10,
            "allocated_quantity": 5,
            "remaining_quantity": 5,
            "order_date": "2025-01-01",
        },
        {
            "product_id": "P002",
            "quantity": 3,
            "allocated_quantity": 0,
            "remaining_quantity": 3,
            "order_date": "2025-01-01",
        },
    ]

DSL Example:
```
- name: Get Order Details
  function: customer_order.get_order_details
  arguments:
    order_id: "O001"
  output_var: order_details
```

### customer_order.get_order_status

Retrieves the status of a specific order.

Args:
    order_id (str): The ID of the order to query.

Returns:
    str: Status of the order.
    Example
    Pending
    or
    Shipped


DSL Example:
```
- name: Get Order Status
  function: customer_order.get_order_status
  arguments:
    order_id: "O001"
  output_var: order_status
```

### customer_order.get_pending_orders

Retrieves pending orders, optionally filtered by customer.

Args:
    customer_id (str, optional): The ID of the customer to filter orders. Defaults to None.

Returns:
    list[dict]: List of pending orders.
    Example:
    [
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
    ]

DSL Example:
```
- name: Get Pending Orders
  function: customer_order.get_pending_orders
  arguments:
    customer_id: "C001"
  output_var: pending_orders
```

### customer_order.partial_allocate_order

Partially allocates stock for an order without requiring full allocation.

Args:
    order_id (str): The ID of the order to allocate.

Returns:
    dict: Partial allocation details.
    Example:
    [

        {
            "product_id": "P001",
            "requested_quantity": 10,
            "stock_quantity": 10,
        },
        {
            "product_id": "P002",
            "requested_quantity": 5,
            "stock_quantity": 3,
        },

DSL Example:
```
- name: Partially Allocate Order
  function: customer_order.partial_allocate_order
  arguments:
    order_id: "O001"
  output_var: partial_allocation
```

### customer_order.update_order_status

Updates the status of an order.

Args:
    order_id (str): The ID of the order.
    status (str): The new status to assign to the order (e.g., 'Pending', 'Shipped').

Returns:
    bool: True if the update was successful, False otherwise.

DSL Example:
```
- name: Update Order Status
  function: customer_order.update_order_status
  arguments:
    order_id: "O001"
    status: "Shipped"
  output_var: update_success
```

### inventory.adjust_stock

Manually adjusts stock levels for a product.

Args:
    product_id (str): The ID of the product to adjust.
    quantity_delta (int): The quantity to add (positive) or subtract (negative).

Returns:
    bool: True if the adjustment was successful, False otherwise.

DSL Example:
```
- name: Adjust Stock
  function: inventory.adjust_stock
  arguments:
    product_id: "P001"
    quantity_delta: -10
  output_var: adjustment_success
```

### inventory.allocate_stock

Allocates available stock for a given order.

Args:
    order_id (str): The ID of the order to allocate stock.

Returns:
    list[dict]:
    Example:
    [
        {
            "product_id": "P001",
            "newly_allocated_quantity": 10,
            "remaining_quantity": 0,
        },
        {
            "product_id": "P002",
            "newly_allocated_quantity": 3,
            "remaining_quantity": 2,
        },
    ]

DSL Example:
```
- name: Allocate Stock
  function: inventory.allocate_stock
  arguments:
    order_id: "O001"
  output_var: allocation_result
```

### inventory.check_stock

Checks the stock level of a specific product.

Args:
    product_id (str): The ID of the product to check.

Returns:
    int: Current stock level.

DSL Example:
```
- name: Check Stock
  function: inventory.check_stock
  arguments:
    product_id: "P001"
  output_var: stock_level
```

### product.get_products

Retrieves a list of all products.

Returns:
list[dict]: A list of products with details.
Example:
[

    {
        "product_id": "P001",
        "name": "Product 1",
        "price": 100,
    },
    {
        "product_id": "P002",
        "name": "Product 2",
        "price": 200,
    },
]


DSL Example:
```
- name: Get Products
  function: product.get_products
  output_var: products
```

### production.allocate_prebooked_production

Allocates prebooked production capacity to fulfill an order.

Args:
    order_id (str): The ID of the order.

Returns:
    list[dict]: Allocation details including product ID, requested, allocated, and remaining quantities.

    Example:
    [
        {
            "product_id": "P001",
            "newly_allocated_quantity": 10,
            "remaining_quantity": 0,
        },
        {
            "product_id": "P002",
            "newly_allocated_quantity": 3,
            "remaining_quantity": 2,
        },
    ]


DSL Example:
```
- name: Allocate Prebooked Production
  function: production.allocate_prebooked_production
  arguments:
    order_id: "O001"
  output_var: allocation_result
```

### production.get_production_backlog

Retrieves backlogged production items, optionally filtered by product.

Args:
    product_id (str, optional): The ID of the product to filter by.

Returns:
    list[dict]: A list of backlogged production items.
    Example:
    [
        {
            "schedule_id": "PS_O001_P001_20250102",
            "product_id": "P001",
            "start_date": "2025-01-02",
            "end_date": "2025-01-02",
            "quantity": 10,
            "status": "Backlogged",
        },
        {
            "schedule_id": "PS_O001_P002_20250102",
            "product_id": "P002",
            "start_date": "2025-01-02",
            "end_date": "2025-01-02",
            "quantity": 5,
            "status": "Backlogged",
        },

DSL Example:
```
- name: Get Production Backlog
  function: production.get_production_backlog
  arguments:
    product_id: "P001"
  output_var: backlog
```

### production.schedule_production

Schedules production runs for an order's unallocated quantities.

Args:
    order_id (str): The ID of the order to schedule production for.

Returns:
    list[dict]: A list of newly created production schedule records.
    Example:
    [
        {
            "schedule_id": "PS_O001_P001_20250102",
            "product_id": "P001",
            "start_date": "2025-01-02",
            "end_date": "2025-01-02",
            "quantity": 10,
            "status": "Scheduled",
        },
        {
            "schedule_id": "PS_O001_P002_20250102",
            "product_id": "P002",
            "start_date": "2025-01-02",
            "end_date": "2025-01-02",
            "quantity": 5,
            "status": "Scheduled",
        },
    ]

DSL Example:
```
- name: Schedule Production
  function: production.schedule_production
  arguments:
    order_id: "O001"
  output_var: production_schedule
```

### report.generate_order_report

Generates a report of orders filtered by status or customer.

Args:
    status (str, optional): The status of the orders to filter by (e.g., 'Pending').
    customer_id (str, optional): The customer ID to filter orders for.

Returns:
    list[dict]:
    Example:
    [
        {
            "order_id": "O001",
            "customer_id": "C001",
            "order_date": "2025-01-01",
            "status": "Pending",
        },
        {
            "order_id": "O003",
            "customer_id": "C001",
            "order_date": "2025-01-03",
            "status": "Pending",

DSL Example:
```
- name: Generate Order Report
  function: report.generate_order_report
  arguments:
    status: "Pending"
    customer_id: "C001"
  output_var: order_report
```

### report.generate_production_report

Generates a report of production schedules within a specific date range.

Args:
    start_date (str): Start date of the report (inclusive).
    end_date (str): End date of the report (inclusive).

Returns:
    list[dict]:
    Example:
    [
        {
            "schedule_id": "PS_O001_P001_20250102",
            "product_id": "P001",
            "start_date": "2025-01-02",
            "end_date": "2025-01-02",
            "quantity": 10,
            "status": "Scheduled",
        },
        {
            "schedule_id": "PS_O001_P002_20250102",
            "product_id": "P002",
            "start_date": "2025-01-02",
            "end_date": "2025-01-02",
            "quantity": 5,
            "status": "Scheduled",
        },

DSL Example:
```
- name: Generate Production Report
  function: report.generate_production_report
  arguments:
    start_date: "2025-01-01"
    end_date: "2025-01-31"
  output_var: production_report
```

### report.generate_replenishment_report

Generates a report of components with stock below a specified threshold.

Args:
    threshold (int): The stock level threshold.

Returns:
    list[dict]:
    Example:
    [
        {
            "component_id": "C001",
            "name": "Component A",
            "stock_quantity": 20,
        },
        {
            "component_id": "C002",
            "name": "Component B",
            "stock_quantity": 30,
        },

DSL Example:
```
- name: Generate Replenishment Report
  function: report.generate_replenishment_report
  arguments:
    threshold: 50
  output_var: replenishment_report
```

### report.generate_summary_report

Generates a summary report of current stock levels, pending orders, and production schedules.

Returns:
    dict:
    Example:
    {
        "inventory": [
            {
                "product_id": "P001",
                "stock_quantity": 100,
            },
            {
                "product_id": "P002",
                "stock_quantity": 50,
            },
        ],
        "pending_orders": [
            {
                "order_id": "O001",
                "customer_id": "C001",
                "order_date": "2025-01-01",
                "status": "Pending",
            },
            {
                "order_id": "O003",
                "customer_id": "C001",
                "order_date": "2025-01-03",
                "status": "Pending",
            },
        ],
        "production_schedule": [
            {
                "schedule_id": "PS_O001_P001_20250102",
                "product_id": "P001",
                "start_date": "2025-01-02",
                "end_date": "2025-01-02",
                "quantity": 10,
                "status": "Scheduled",
            },
            {
                "schedule_id": "PS_O001_P002_20250102",
                "product_id": "P002",
                "start_date": "2025-01-02",
                "end_date": "2025-01-02",
                "quantity": 5,
                "status": "Scheduled",
            },
        ],
    }

DSL Example:
```
- name: Generate Summary Report
  function: report.generate_summary_report
  arguments: {}
  output_var: summary_report
```

### shipping.confirm_shipment

Confirms shipment for a specific order.

Args:
    order_id (str): The ID of the order.
    shipping_option_id (str): The ID of the chosen shipping option.

Returns:
    dict: Shipment confirmation details.
    Example:
    {
        "shipment_id": "SHIP_O001",
        "tracking_number": "TRACK_O001",
    }


DSL Example:
```
- name: Confirm Shipment
  function: shipping.confirm_shipment
  arguments:
    order_id: "O001"
    shipping_option_id: "SO001"
  output_var: shipment_details
```

### shipping.get_shipping_options

Retrieves available shipping options for a given order.

Args:
    order_id (str): The ID of the order.

Returns:
    list[dict]: Available shipping options.
    Example:
    [
        {
            "shipping_option_id": "SO001",
            "carrier_id": "C001",
            "service_level": "Standard",
            "cost": 10,
            "estimated_days": 5,
        },
        {
            "shipping_option_id": "SO002",
            "carrier_id": "C002",
            "service_level": "Express",
            "cost": 20,
            "estimated_days": 2,
        },
    ]

DSL Example:
```
- name: Get Shipping Options
  function: shipping.get_shipping_options
  arguments:
    order_id: "O001"
  output_var: shipping_options
```

### shipping.track_shipment

Tracks a shipment using its tracking number.

Args:
    tracking_number (str): The tracking number of the shipment.

Returns:
    dict: Current shipment details.
    Example:
    {
        "shipment_id": "SHIP_O001",
        "order_id": "O001",
        "shipping_option_id": "SO001",
        "shipped_date": "2025-01-01",
    }

DSL Example:
```
- name: Track Shipment
  function: shipping.track_shipment
  arguments:
    tracking_number: "TRK12345"
  output_var: shipment_status
```


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

    Hi Ted, can you check for any pending orders from ElectroWorld? Please prioritize them and expedite shipping if possible.
```
