import pytest
import yaml
from proj.dsl.dsl_executor import DSLExecutor
from proj.scripts.reset_db import reset_db


@pytest.fixture(scope="module")
def dsl_executor():
    """Fixture to initialize DSLExecutor with a reset database."""
    reset_db()
    return DSLExecutor("scm")


def test_simple_output_resolution(dsl_executor):
    """
    Test simple resolution of an output variable from a previous step.
    """
    task_yaml = """
    task: Test Simple Output Resolution
    steps:
      - name: Fetch Pending Orders
        function: customer_order.get_pending_orders
        arguments: {}
        output_var: pending_orders

      - name: Print First Pending Order
        function: message.write_message
        arguments:
          message: "The first pending order is {pending_orders[0]}."
        output_var: message_result
    """
    # Execute the task
    dsl_executor.execute_task(task_yaml)

    # Verify that the output variable resolves correctly
    expected_message = {
        "status": "success",
        "message": "The first pending order is {'order_id': 'O001', 'order_date': '2025-01-01', 'status': 'Pending'}.",
    }
    assert "message_result" in dsl_executor.dsl_context
    assert dsl_executor.dsl_context["message_result"] == expected_message


def test_expression_on_output_var(dsl_executor):
    """
    Test resolving an expression involving an output variable from a previous step.
    """
    task_yaml = """
    task: Test Expression on Output Variable
    steps:
      - name: Fetch Pending Orders
        function: customer_order.get_pending_orders
        arguments: {}
        output_var: pending_orders

      - name: Calculate Total Orders
        function: message.write_message
        arguments:
          message: "Twice the pending orders count is {len(pending_orders) * 2}."
        output_var: message_result
    """
    # Execute the task
    dsl_executor.execute_task(task_yaml)

    # Verify that the expression resolves correctly
    expected_message = {
        "status": "success",
        "message": "Twice the pending orders count is 4.",  # Assuming 2 pending orders for this test
    }
    assert "message_result" in dsl_executor.dsl_context
    assert dsl_executor.dsl_context["message_result"] == expected_message


def test_expression_with_loop_variable(dsl_executor):
    """
    Test resolving expressions with loop variables.
    """
    task_yaml = """
    task: Test Loop Variable
    steps:
      - name: Fetch Pending Orders
        function: customer_order.get_pending_orders
        arguments: {}
        output_var: pending_orders

      - name: Process Each Order
        loop:
          variable: order
          over: "{pending_orders}"
        steps:
          - name: Print Order ID
            function: message.write_message
            arguments:
              message: "Processing order {order['order_id']}"
            output_var: order_message
    """

    # Execute the task
    dsl_executor.execute_task(task_yaml)

    # Assertions
    expected_context = {
        "pending_orders": [
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
        ],
        "order_message": {
            "status": "success",
            "message": "Processing order O003",
        },  # Last iteration
    }

    for key, expected_value in expected_context.items():
        assert (
            key in dsl_executor.dsl_context
        ), f"{key} is missing in DSL context."
        assert dsl_executor.dsl_context[key] == expected_value, (
            f"Value for {key} did not match.\n"
            f"Expected: {expected_value}\n"
            f"Got: {dsl_executor.dsl_context[key]}"
        )


def test_expression_with_loop_variable_expression(dsl_executor):
    """
    Test resolving expressions with loop variables during iterations.
    """

    from datetime import datetime

    # Set today's date for the test
    dsl_executor.dsl_context["today_date"] = "2025-01-10"  # Mock today's date

    task_yaml = """
    task: Test Loop Variable with Expression
    steps:
    - name: Fetch Pending Orders
      function: customer_order.get_pending_orders
      arguments: {}
      output_var: pending_orders

    - name: Process Each Order with Expression
      loop:
        variable: order
        over: "{pending_orders}"
      steps:
        - name: Print Delay for Order
          function: message.write_message
          arguments:
            message: "Order {order['order_id']} was created {abs((datetime.strptime(today_date, '%Y-%m-%d') - datetime.strptime(order['order_date'], '%Y-%m-%d')).days)} days ago."
          output_var: delay_message
    """

    # Execute the task
    dsl_executor.execute_task(task_yaml)

    # Assertions
    expected_context = {
        "pending_orders": [
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
        ],
        "delay_message": {
            "status": "success",
            "message": "Order O003 was created 7 days ago.",
        },  # Message for the last iteration
    }

    for key, expected_value in expected_context.items():
        assert (
            key in dsl_executor.dsl_context
        ), f"{key} is missing in DSL context."
        assert dsl_executor.dsl_context[key] == expected_value, (
            f"Value for {key} did not match.\n"
            f"Expected: {expected_value}\n"
            f"Got: {dsl_executor.dsl_context[key]}"
        )
