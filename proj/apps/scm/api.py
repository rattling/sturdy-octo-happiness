import sqlite3
from datetime import datetime, timedelta


class SCMAPI:
    def __init__(self, cursor):
        self.cursor = cursor
        self.product = Product(cursor)
        self.customer = Customer(cursor)
        self.customer_order = CustomerOrder(cursor)
        self.inventory = Inventory(cursor)
        self.production = Production(cursor)
        self.shipping = Shipping(cursor)
        self.component = Component(cursor)
        self.report = Report(cursor)


class Customer:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_customer_details(self, customer_id: str) -> dict:
        """
        Retrieves details for a specific customer.

        Args:
            customer_id (str): The ID of the customer.

        Returns:
            dict: Customer details including name, address, and contact information.
            Examp

        DSL Example:
        ```
        - name: Get Customer Details
        function: get_customer_details
        arguments:
            customer_id: "C001"
        output_var: customer_details
        ```
        """
        self.cursor.execute(
            """
            SELECT name, address, contact_info
            FROM Customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        )
        row = self.cursor.fetchone()
        return (
            {"name": row[0], "address": row[1], "contact_info": row[2]}
            if row
            else {}
        )


class Product:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_products(self) -> list[dict]:
        """
        Retrieves a list of all products.

        Returns:
        list[dict]: A list of products with details.

        DSL Example:
        ```
        - name: Get Products
          function: product.get_products
          output_var: products
        ```
        """
        self.cursor.execute("SELECT product_id, name, price FROM Products")
        rows = self.cursor.fetchall()
        return [
            {"product_id": row[0], "name": row[1], "price": row[2]}
            for row in rows
        ]


class CustomerOrder:
    def __init__(self, cursor):
        self.cursor = cursor

    def partial_allocate_order(self, order_id: str) -> dict:
        """
        Partially allocates stock for an order without requiring full allocation.

        Args:
            order_id (str): The ID of the order to allocate.

        Returns:
            dict: Partial allocation details.

        DSL Example:
        ```
        - name: Partially Allocate Order
          function: customer_order.partial_allocate_order
          arguments:
            order_id: "O001"
          output_var: partial_allocation
        ```
        """
        self.cursor.execute(
            """
            SELECT od.product_id, od.quantity, i.stock_quantity
            FROM OrderDetails od
            LEFT JOIN Inventory i ON od.product_id = i.product_id
            WHERE od.order_id = ?
            """,
            (order_id,),
        )
        rows = self.cursor.fetchall()
        allocations = []

        for product_id, quantity, stock in rows:
            allocated = min(quantity, stock)
            allocations.append(
                {
                    "product_id": product_id,
                    "requested_quantity": quantity,
                    "allocated_quantity": allocated,
                }
            )
            self.cursor.execute(
                "UPDATE Inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                (allocated, product_id),
            )

        self.cursor.execute(
            "UPDATE Orders SET status = ? WHERE order_id = ?",
            ("Partially Allocated", order_id),
        )
        return allocations

    def get_order_status(self, order_id: str) -> str:
        """
        Retrieves the status of a specific order.

        Args:
            order_id (str): The ID of the order to query.

        Returns:
            str: Status of the order.

        DSL Example:
        ```
        - name: Get Order Status
          function: customer_order.get_order_status
          arguments:
            order_id: "O001"
          output_var: order_status
        ```
        """
        self.cursor.execute(
            "SELECT status FROM Orders WHERE order_id = ?", (order_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else "Order not found"

    def get_pending_orders(self, customer_id: str = None) -> list[dict]:
        """
        Retrieves pending orders, optionally filtered by customer.

        Args:
            customer_id (str, optional): The ID of the customer to filter orders. Defaults to None.

        Returns:
            list[dict]: List of pending orders.

        DSL Example:
        ```
        - name: Get Pending Orders
          function: customer_order.get_pending_orders
          arguments:
            customer_id: "C001"
          output_var: pending_orders
        ```
        """
        if customer_id:
            self.cursor.execute(
                "SELECT order_id, order_date, status FROM Orders WHERE status = 'Pending' AND customer_id = ?",
                (customer_id,),
            )
        else:
            self.cursor.execute(
                "SELECT order_id, order_date, status FROM Orders WHERE status = 'Pending'"
            )
        rows = self.cursor.fetchall()
        return [
            {"order_id": row[0], "order_date": row[1], "status": row[2]}
            for row in rows
        ]

    def update_order_status(self, order_id: str, status: str) -> bool:
        """
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
        """
        self.cursor.execute(
            "UPDATE Orders SET status = ? WHERE order_id = ?",
            (status, order_id),
        )
        return self.cursor.rowcount > 0

    def create_order(self, customer_id: str, order_details: list[dict]) -> str:
        """
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
        """
        import uuid

        order_id = str(uuid.uuid4())[:8]
        self.cursor.execute(
            "INSERT INTO Orders (order_id, customer_id, order_date, status) VALUES (?, ?, date('now'), 'Pending')",
            (order_id, customer_id),
        )
        for detail in order_details:
            self.cursor.execute(
                "INSERT INTO OrderDetails (order_id, product_id, quantity) VALUES (?, ?, ?)",
                (order_id, detail["product_id"], detail["quantity"]),
            )
        return order_id

    def cancel_order(self, order_id: str) -> bool:
        """
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
        """
        self.cursor.execute(
            "DELETE FROM OrderDetails WHERE order_id = ?", (order_id,)
        )
        self.cursor.execute(
            "DELETE FROM Orders WHERE order_id = ?", (order_id,)
        )
        return self.cursor.rowcount > 0

    def get_order_details(self, order_id: str) -> list[dict]:
        """
        Retrieves detailed information for a specific order.

        Args:
            order_id (str): The ID of the order to retrieve details for.

        Returns:
            list[dict]: A list of order details, including product ID, requested quantity,
                        allocated quantity, and remaining quantity.

        DSL Example:
        ```
        - name: Get Order Details
          function: customer_order.get_order_details
          arguments:
            order_id: "O001"
          output_var: order_details
        ```
        """
        self.cursor.execute(
            """
            SELECT od.product_id, od.quantity, od.allocated_quantity, od.remaining_quantity
            FROM OrderDetails od
            WHERE od.order_id = ?
            """,
            (order_id,),
        )
        rows = self.cursor.fetchall()
        return [
            {
                "product_id": row[0],
                "quantity": row[1],
                "allocated_quantity": row[2],
                "remaining_quantity": row[3],
            }
            for row in rows
        ]


class Inventory:
    def __init__(self, cursor):
        self.cursor = cursor

    def check_stock(self, product_id: str) -> int:
        """
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
        """
        self.cursor.execute(
            "SELECT stock_quantity FROM Inventory WHERE product_id = ?",
            (product_id,),
        )
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def allocate_stock(self, order_id: str) -> dict:
        """
        Allocates available stock for a given order.

        Args:
            order_id (str): The ID of the order to allocate stock.

        Returns:
            dict:
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
        """
        self.cursor.execute(
            """
            SELECT od.product_id, od.remaining_quantity, i.available_quantity
            FROM OrderDetails od
            LEFT JOIN Inventory i ON od.product_id = i.product_id
            WHERE od.order_id = ? 
            """,
            (order_id,),
        )
        allocations = []
        rows = self.cursor.fetchall()

        for (
            product_id,
            remaining_quantity,
            available_quantity,
        ) in rows:
            allocated = min(remaining_quantity, available_quantity)
            new_remaining_quantity = (
                remaining_quantity - allocated
            )  # Calculate dynamically
            allocations.append(
                {
                    "product_id": product_id,
                    "newly_allocated_quantity": allocated,
                    "remaining_quantity": new_remaining_quantity,
                }
            )
            self.cursor.execute(
                """
                UPDATE Inventory
                SET reserved_quantity = reserved_quantity + ?
                WHERE product_id = ?
                """,
                (allocated, product_id),
            )

            self.cursor.execute(
                "UPDATE Orders SET status = ? WHERE order_id = ?",
                (
                    (
                        "Allocated"
                        if all(
                            a["newly_allocated_quantity"] > 0
                            for a in allocations
                        )
                        else "Partially Allocated"
                    ),
                    order_id,
                ),
            )

            self.cursor.execute(
                """UPDATE OrderDetails
                SET allocated_quantity = allocated_quantity + ?
                WHERE order_id = ? AND product_id = ?
                """,
                (allocated, order_id, product_id),
            )

        return allocations

    def adjust_stock(self, product_id: str, quantity_delta: int) -> bool:
        """
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
        """
        self.cursor.execute(
            "UPDATE Inventory SET stock_quantity = stock_quantity + ? WHERE product_id = ?",
            (quantity_delta, product_id),
        )
        return self.cursor.rowcount > 0


class Production:

    def __init__(self, cursor):
        self.cursor = cursor

    def schedule_production(self, order_id: str) -> list[dict]:
        """
        Schedules production runs for an order's unallocated quantities.

        Args:
            order_id (str): The ID of the order to schedule production for.

        Returns:
            list[dict]: A list of newly created production schedule records.

        DSL Example:
        ```
        - name: Schedule Production
          function: production.schedule_production
          arguments:
            order_id: "O001"
          output_var: production_schedule
        ```
        """
        self.cursor.execute(
            """
            SELECT od.product_id, od.remaining_quantity
            FROM OrderDetails od
            WHERE od.order_id = ? AND od.remaining_quantity > 0
            """,
            (order_id,),
        )
        rows = self.cursor.fetchall()

        # Get the earliest production schedule date for fallback
        self.cursor.execute("SELECT MIN(start_date) FROM ProductionSchedule")
        earliest_date_row = self.cursor.fetchone()
        earliest_date = (
            earliest_date_row[0] if earliest_date_row else "2025-01-01"
        )

        production_schedules = []

        for product_id, remaining_quantity in rows:
            # Find the latest production date for this product
            self.cursor.execute(
                """
                SELECT MAX(end_date)
                FROM ProductionSchedule
                WHERE product_id = ?
                """,
                (product_id,),
            )
            latest_date_row = self.cursor.fetchone()
            latest_date = (
                latest_date_row[0] if latest_date_row[0] else earliest_date
            )

            # Calculate new production start and end dates
            new_start_date = datetime.strptime(
                latest_date, "%Y-%m-%d"
            ) + timedelta(days=1)
            new_end_date = (
                new_start_date  # Assuming single-day production for now
            )

            # Generate a unique schedule ID
            schedule_id = f"PS_{order_id}_{product_id}_{new_start_date.strftime('%Y%m%d')}"

            # Insert the new production schedule
            self.cursor.execute(
                """
                INSERT INTO ProductionSchedule (
                    schedule_id, product_id, start_date, end_date, total_capacity, allocated_capacity, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    schedule_id,
                    product_id,
                    new_start_date.strftime("%Y-%m-%d"),
                    new_end_date.strftime("%Y-%m-%d"),
                    remaining_quantity,
                    0,  # No capacity allocated yet
                    "Scheduled",
                ),
            )

            # Add to the result
            production_schedules.append(
                {
                    "schedule_id": schedule_id,
                    "product_id": product_id,
                    "start_date": new_start_date.strftime("%Y-%m-%d"),
                    "end_date": new_end_date.strftime("%Y-%m-%d"),
                    "quantity": remaining_quantity,
                    "status": "Scheduled",
                }
            )

        return production_schedules

    def get_production_backlog(self, product_id: str = None) -> list[dict]:
        """
        Retrieves backlogged production items, optionally filtered by product.

        Args:
            product_id (str, optional): The ID of the product to filter by.

        Returns:
            list[dict]: A list of backlogged production items.

        DSL Example:
        ```
        - name: Get Production Backlog
          function: production.get_production_backlog
          arguments:
            product_id: "P001"
          output_var: backlog
        ```
        """
        query = """
            SELECT schedule_id, product_id, start_date, end_date, available_capacity, status
            FROM ProductionSchedule
            WHERE status = 'Backlogged'
        """
        params = []
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [
            {
                "schedule_id": row[0],
                "product_id": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "quantity": row[4],
                "status": row[5],
            }
            for row in rows
        ]

    def allocate_prebooked_production(self, order_id: str) -> list[dict]:
        """
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
        """
        self.cursor.execute(
            """
            SELECT od.product_id, od.remaining_quantity
            FROM OrderDetails od
            WHERE od.order_id = ? AND od.remaining_quantity > 0
            """,
            (order_id,),
        )
        rows = self.cursor.fetchall()

        allocation_result = []

        for (
            product_id,
            remaining_quantity,
        ) in rows:
            self.cursor.execute(
                """
                SELECT schedule_id, available_capacity
                FROM ProductionSchedule
                WHERE product_id = ? AND available_capacity > 0 AND status = 'Scheduled'
                ORDER BY start_date ASC
                """,
                (product_id,),
            )
            production_rows = self.cursor.fetchall()

            for schedule_id, available_capacity in production_rows:
                allocation = min(available_capacity, remaining_quantity)

                # Allocate capacity
                self.cursor.execute(
                    """
                    UPDATE ProductionSchedule
                    SET allocated_capacity = allocated_capacity + ?
                    WHERE schedule_id = ?
                    """,
                    (allocation, schedule_id),
                )

                # Create ProductionAllocation record
                self.cursor.execute(
                    """
                    INSERT INTO ProductionAllocation (allocation_id, production_schedule_id, order_id, allocated_quantity)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        f"PA_{schedule_id}_{order_id}",
                        schedule_id,
                        order_id,
                        allocation,
                    ),
                )

                # Update OrderDetails
                self.cursor.execute(
                    """
                    UPDATE OrderDetails
                    SET allocated_quantity = allocated_quantity + ?
                    WHERE order_id = ? AND product_id = ?
                    """,
                    (allocation, order_id, product_id),
                )

                # Update remaining_quantity dynamically
                remaining_quantity -= allocation

                # Add allocation status for this product
                allocation_result.append(
                    {
                        "product_id": product_id,
                        "newly_allocated_quantity": allocation,
                        "remaining_quantity": remaining_quantity,  # Include in output
                    }
                )

                # Stop allocation if fully allocated
                if remaining_quantity <= 0:
                    break

        # Update order status if all items are fully allocated
        self.cursor.execute(
            """
            SELECT COUNT(*) FROM OrderDetails
            WHERE order_id = ? AND remaining_quantity > 0
            """,
            (order_id,),
        )
        unallocated_count = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            UPDATE Orders
            SET status = ?
            WHERE order_id = ?
            """,
            (
                (
                    "Allocated"
                    if unallocated_count == 0
                    else "Partially Allocated"
                ),
                order_id,
            ),
        )

        return allocation_result


class Shipping:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_shipping_options(self, order_id: str) -> list[dict]:
        """
        Retrieves available shipping options for a given order.

        Args:
            order_id (str): The ID of the order.

        Returns:
            list[dict]: Available shipping options.

        DSL Example:
        ```
        - name: Get Shipping Options
          function: shipping.get_shipping_options
          arguments:
            order_id: "O001"
          output_var: shipping_options
        ```
        """
        self.cursor.execute(
            """
            SELECT so.destination, so.shipping_option_id, so.carrier_id, so.service_level, so.cost, so.estimated_days
            FROM Orders o
            JOIN ShippingOptions so ON so.destination = o.customer_id
            WHERE o.order_id = ?
            """,
            (order_id,),
        )
        rows = self.cursor.fetchall()
        return [
            {
                "shipping_option_id": row[1],
                "carrier_id": row[2],
                "service_level": row[3],
                "cost": row[4],
                "estimated_days": row[5],
            }
            for row in rows
        ]

    def confirm_shipment(self, order_id: str, shipping_option_id: str) -> dict:
        """
        Confirms shipment for a specific order.

        Args:
            order_id (str): The ID of the order.
            shipping_option_id (str): The ID of the chosen shipping option.

        Returns:
            dict: Shipment confirmation details.

        DSL Example:
        ```
        - name: Confirm Shipment
          function: shipping.confirm_shipment
          arguments:
            order_id: "O001"
            shipping_option_id: "SO001"
          output_var: shipment_details
        ```
        """
        shipment_id = f"SHIP_{order_id}"
        tracking_number = f"TRACK_{order_id}"
        shipped_date = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            """
            INSERT INTO Shipments (shipment_id, order_id, shipping_option_id, shipped_date, tracking_number)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                shipment_id,
                order_id,
                shipping_option_id,
                shipped_date,
                tracking_number,
            ),
        )
        self.cursor.execute(
            "UPDATE Orders SET status = ? WHERE order_id = ?",
            ("Shipped", order_id),
        )
        return {
            "shipment_id": shipment_id,
            "tracking_number": tracking_number,
        }

    def track_shipment(self, tracking_number: str) -> dict:
        """
        Tracks a shipment using its tracking number.

        Args:
            tracking_number (str): The tracking number of the shipment.

        Returns:
            dict: Current shipment details.

        DSL Example:
        ```
        - name: Track Shipment
          function: shipping.track_shipment
          arguments:
            tracking_number: "TRK12345"
          output_var: shipment_status
        ```
        """
        self.cursor.execute(
            """
            SELECT shipment_id, order_id, shipping_option_id, shipped_date
            FROM Shipments
            WHERE tracking_number = ?
            """,
            (tracking_number,),
        )
        row = self.cursor.fetchone()
        if not row:
            return {"status": "Not Found"}
        return {
            "shipment_id": row[0],
            "order_id": row[1],
            "shipping_option_id": row[2],
            "shipped_date": row[3],
        }


class Component:
    def __init__(self, cursor):
        self.cursor = cursor

    def check_components_for_product(self, product_id: str) -> list[dict]:
        """
        Checks component stock for a given product

        Args:
            product_id (str): The ID of the product to check inventory for.

        Returns:
            list(dict): A dictionary with component availability and required quantities.

        DSL Example:
        ```
        - name: Get Inventory for Production
          function: component.check_components_for_product
          arguments:
            product_id: "P001"
          output_var: production_inventory
        ```
        """
        self.cursor.execute(
            """
            SELECT pc.component_id, pc.quantity_needed_per_unit, c.stock_quantity
            FROM ProductComponents pc
            JOIN Components c ON pc.component_id = c.component_id
            WHERE pc.product_id = ?
            """,
            (product_id,),
        )
        rows = self.cursor.fetchall()
        return [
            {
                "component_id": row[0],
                "required_quantity": row[1],
                "available_quantity": row[2],
            }
            for row in rows
        ]

    def reserve_stock_components(self, product_id: str, quantity: int) -> dict:
        """
        Reserves stock for production by reducing available stock quantities for components.

        Args:
            product_id (str): The ID of the product to reserve stock for.
            quantity (int): The number of units to produce.

        Returns:
            dict: Details of reserved components, including any shortfalls.

        DSL Example:
        ```
        - name: Reserve Components
          function: component.reserve_stock_components
          arguments:
            product_id: "P001"
            quantity: 50
          output_var: reservation_result
        ```
        """
        inventory = self.check_components_for_product(product_id)
        reservation_result = []
        for item in inventory:
            required = item["required_quantity"] * quantity
            available = item["available_quantity"]
            reserved = min(required, available)
            shortfall = required - reserved

            # Update stock in the database
            self.cursor.execute(
                "UPDATE Components SET stock_quantity = stock_quantity - ? WHERE component_id = ?",
                (reserved, item["component_id"]),
            )
            reservation_result.append(
                {
                    "component_id": item["component_id"],
                    "reserved_quantity": reserved,
                    "shortfall": shortfall if shortfall > 0 else 0,
                }
            )
        return reservation_result

    def check_component_availability(self, component_id: str) -> int:
        """
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
        """
        self.cursor.execute(
            "SELECT stock_quantity FROM Components WHERE component_id = ?",
            (component_id,),
        )
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def check_supplier_components(self, supplier_id: str) -> list[dict]:
        """
        Retrieves the list of components available from a specific supplier.

        Args:
            supplier_id (str): The ID of the supplier.

        Returns:
            list[dict]: A list of components with quantity and cost information.

        DSL Example:
        ```
        - name: Check Supplier Components
          function: component.check_supplier_components
          arguments:
            supplier_id: "S001"
          output_var: supplier_components
        ```
        """
        self.cursor.execute(
            """
            SELECT component_id, available_quantity, cost_per_unit
            FROM SupplierComponents
            WHERE supplier_id = ?
            """,
            (supplier_id,),
        )
        rows = self.cursor.fetchall()
        return [
            {
                "component_id": row[0],
                "available_quantity": row[1],
                "cost_per_unit": row[2],
            }
            for row in rows
        ]

    def place_component_order(
        self, supplier_id: str, component_id: str, quantity: int
    ) -> dict:
        """
        Places an order for components from a supplier.

        Args:
            supplier_id (str): The ID of the supplier.
            component_id (str): The ID of the component.
            quantity (int): The quantity to order.

        Returns:
            dict: Order confirmation details, including cost.

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
        """
        self.cursor.execute(
            """
            SELECT available_quantity, cost_per_unit
            FROM SupplierComponents
            WHERE supplier_id = ? AND component_id = ?
            """,
            (supplier_id, component_id),
        )
        result = self.cursor.fetchone()
        if not result or result[0] < quantity:
            return {
                "status": "Failed",
                "reason": "Insufficient stock from supplier",
            }

        cost = quantity * result[1]
        return {
            "status": "Success",
            "supplier_id": supplier_id,
            "component_id": component_id,
            "quantity_ordered": quantity,
            "total_cost": cost,
        }


class Report:
    def __init__(self, cursor):
        self.cursor = cursor

    def generate_replenishment_report(self, threshold: int) -> list[dict]:
        """
        Generates a report of components with stock below a specified threshold.

        Args:
            threshold (int): The stock level threshold.

        Returns:
            list[dict]: A list of components below the threshold, with stock details.

        DSL Example:
        ```
        - name: Generate Replenishment Report
          function: report.generate_replenishment_report
          arguments:
            threshold: 50
          output_var: replenishment_report
        ```
        """
        self.cursor.execute(
            "SELECT component_id, name, stock_quantity FROM Components WHERE stock_quantity < ?",
            (threshold,),
        )
        rows = self.cursor.fetchall()
        return [
            {
                "component_id": row[0],
                "name": row[1],
                "stock_quantity": row[2],
            }
            for row in rows
        ]

    def generate_production_report(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """
        Generates a report of production schedules within a specific date range.

        Args:
            start_date (str): Start date of the report (inclusive).
            end_date (str): End date of the report (inclusive).

        Returns:
            list[dict]: A list of production schedule details.

        DSL Example:
        ```
        - name: Generate Production Report
          function: report.generate_production_report
          arguments:
            start_date: "2025-01-01"
            end_date: "2025-01-31"
          output_var: production_report
        ```
        """
        self.cursor.execute(
            """
            SELECT schedule_id, product_id, start_date, end_date, total_capacity, status
            FROM ProductionSchedule
            WHERE start_date >= ? AND end_date <= ?
            """,
            (start_date, end_date),
        )
        rows = self.cursor.fetchall()
        return [
            {
                "schedule_id": row[0],
                "product_id": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "quantity": row[4],
                "status": row[5],
            }
            for row in rows
        ]

    def generate_order_report(
        self, status: str = None, customer_id: str = None
    ) -> list[dict]:
        """
        Generates a report of orders filtered by status or customer.

        Args:
            status (str, optional): The status of the orders to filter by (e.g., 'Pending').
            customer_id (str, optional): The customer ID to filter orders for.

        Returns:
            list[dict]: A list of order details matching the filters.

        DSL Example:
        ```
        - name: Generate Order Report
          function: report.generate_order_report
          arguments:
            status: "Pending"
            customer_id: "C001"
          output_var: order_report
        ```
        """
        query = "SELECT order_id, customer_id, order_date, status FROM Orders WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [
            {
                "order_id": row[0],
                "customer_id": row[1],
                "order_date": row[2],
                "status": row[3],
            }
            for row in rows
        ]

    def generate_summary_report(self) -> dict:
        """
        Generates a summary report of current stock levels, pending orders, and production schedules.

        Returns:
            dict: Summary of inventory, pending orders, and production schedule details.

        DSL Example:
        ```
        - name: Generate Summary Report
          function: report.generate_summary_report
          arguments: {}
          output_var: summary_report
        ```
        """
        self.cursor.execute("SELECT product_id, stock_quantity FROM Inventory")
        inventory = [
            {"product_id": row[0], "stock_quantity": row[1]}
            for row in self.cursor.fetchall()
        ]

        self.cursor.execute(
            """
            SELECT order_id, customer_id, order_date, status
            FROM Orders
            WHERE status = 'Pending'
            """
        )
        pending_orders = [
            {
                "order_id": row[0],
                "customer_id": row[1],
                "order_date": row[2],
                "status": row[3],
            }
            for row in self.cursor.fetchall()
        ]

        self.cursor.execute(
            """
            SELECT schedule_id, product_id, start_date, end_date, total_capacity, status
            FROM ProductionSchedule
            """
        )
        production_schedule = [
            {
                "schedule_id": row[0],
                "product_id": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "quantity": row[4],
                "status": row[5],
            }
            for row in self.cursor.fetchall()
        ]

        return {
            "inventory": inventory,
            "pending_orders": pending_orders,
            "production_schedule": production_schedule,
        }
