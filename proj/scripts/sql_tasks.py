import sqlite3
from datetime import datetime, timedelta
import os

# Connect to the SQLite database
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Connect to SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect(f"{CURRENT_DIR}/scm_db.sqlite")
cursor = conn.cursor()


# Task 1: Check the stock level of a specific product
def check_stock(product_id):
    """
    "Hi Ted, can you check how many units of the Smart Home Hub (P001) we currently have in stock?"
    """
    cursor.execute(
        "SELECT stock_quantity FROM Inventory WHERE product_id = ?",
        (product_id,),
    )
    result = cursor.fetchone()
    if result:
        print(f"Stock level for product {product_id}: {result[0]}")
    else:
        print(f"Product {product_id} not found in inventory.")


# Task 2: Find components running low on stock
def low_stock_components(threshold=50):
    """
    "Ted, could you please find out if any components are running low on stock, say below 50 units?
     We need to ensure we don't run into shortages."
    """
    cursor.execute(
        "SELECT component_id, name, stock_quantity FROM Components WHERE stock_quantity < ?",
        (threshold,),
    )
    results = cursor.fetchall()
    if results:
        print("Components running low on stock:")
        for row in results:
            print(f"Component ID: {row[0]}, Name: {row[1]}, Stock: {row[2]}")
    else:
        print("No components are running low on stock.")


# Task 3: Check for delayed orders
"""
"Are there any pending orders placed more than 7 days ago? 
Let me know if any orders are delayed so we can take action."
"""


def delayed_orders(days=7):
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT order_id, customer_id, order_date FROM Orders WHERE status = 'Pending' AND order_date < ?",
        (cutoff_date,),
    )
    results = cursor.fetchall()
    if results:
        print("Delayed orders:")
        for row in results:
            print(
                f"Order ID: {row[0]}, Customer ID: {row[1]}, Order Date: {row[2]}"
            )
    else:
        print("No delayed orders found.")


# Task 4: Expedite Orders for a Specific Customer
def expedite_orders(customer_name):
    """
    "Hi Ted, can you check for any pending orders from ElectroWorld?
     Please prioritize them and expedite shipping if possible."
    """
    cursor.execute(
        """
        SELECT o.order_id, o.status
        FROM Orders o
        JOIN Customers c ON o.customer_id = c.customer_id
        WHERE c.name = ? AND o.status = 'Pending'
    """,
        (customer_name,),
    )
    results = cursor.fetchall()
    if results:
        print(f"Expediting orders for {customer_name}:")
        for order_id, status in results:
            print(
                f"- Order ID: {order_id} (Status: {status}) - Marking as 'Expedited'"
            )
            cursor.execute(
                "UPDATE Orders SET status = 'Expedited' WHERE order_id = ?",
                (order_id,),
            )
        conn.commit()
    else:
        print(f"No pending orders found for {customer_name}.")


# Task 5: Allocate Inventory for Pending Orders
def allocate_inventory():
    """
    "Please go through all pending orders and allocate inventory where possible.
     For orders we can't fulfill, let me know the shortfall."
    """
    cursor.execute(
        """
        SELECT od.order_id, od.product_id, od.quantity, i.stock_quantity
        FROM OrderDetails od
        JOIN Orders o ON od.order_id = o.order_id
        JOIN Inventory i ON od.product_id = i.product_id
        WHERE o.status = 'Pending'
    """
    )
    results = cursor.fetchall()
    for order_id, product_id, quantity, stock in results:
        if stock >= quantity:
            print(
                f"Allocating {quantity} units of {product_id} for Order {order_id}."
            )
            cursor.execute(
                "UPDATE Inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                (quantity, product_id),
            )
            cursor.execute(
                "UPDATE Orders SET status = 'Fulfilled' WHERE order_id = ?",
                (order_id,),
            )
        else:
            print(
                f"Insufficient stock for {product_id} on Order {order_id}. Remaining: {stock}."
            )
    conn.commit()


# Task 6: Schedule Production for a Product
def schedule_production(product_id, required_quantity):
    """
    "Ted, could you schedule production for Smart Thermostats (P002) to fulfill the upcoming demand?
     Ensure production aligns with future orders."
    """
    today = datetime.now().strftime("%Y-%m-%d")
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO ProductionSchedule (schedule_id, product_id, start_date, end_date, quantity, status) VALUES (?, ?, ?, ?, ?, ?)",
        (
            f"PS_{product_id}_{today}",
            product_id,
            today,
            future_date,
            required_quantity,
            "Scheduled",
        ),
    )
    conn.commit()
    print(
        f"Scheduled production of {required_quantity} units for product {product_id}."
    )


# Task 7: Order Components from Suppliers
def order_components(component_id, threshold):
    """
    "We're running low on Main Processors (C001).
    Check if we have enough for upcoming production.
    If not, order additional stock from the supplier with the best price."
    """
    cursor.execute(
        "SELECT stock_quantity FROM Components WHERE component_id = ?",
        (component_id,),
    )
    stock = cursor.fetchone()
    if stock and stock[0] < threshold:
        cursor.execute(
            """
            SELECT supplier_id, available_quantity, cost_per_unit
            FROM SupplierComponents
            WHERE component_id = ? AND available_quantity > 0
            ORDER BY cost_per_unit ASC
        """,
            (component_id,),
        )
        supplier = cursor.fetchone()
        if supplier:
            print(
                f"Ordering {threshold - stock[0]} units of {component_id} from Supplier {supplier[0]} at {supplier[2]} per unit."
            )
        else:
            print(f"No suppliers available for {component_id}.")
    else:
        print(f"Stock for {component_id} is above the threshold.")


# Task 8: Optimize Shipment Costs
def optimize_shipment(destination):
    """
    "Can you review shipping options for pending deliveries to Los Angeles and pick the most cost-effective carrier?"
    """
    cursor.execute(
        """
        SELECT shipping_option_id, cost, estimated_days
        FROM ShippingOptions
        WHERE destination = ?
        ORDER BY cost ASC
    """,
        (destination,),
    )
    options = cursor.fetchall()
    if options:
        best_option = options[0]
        print(f"Cheapest shipping option to {destination}: {best_option}")
    else:
        print(f"No shipping options available to {destination}.")


# Task 9: Prioritize a Customer's Shipments
def prioritize_customer_shipments(customer_name):
    """
    "Ted, ensure that all pending shipments for ElectroWorld are prioritized.
     If necessary, adjust inventory and production schedules to accommodate them."
    """
    cursor.execute(
        """
        SELECT o.order_id
        FROM Orders o
        JOIN Customers c ON o.customer_id = c.customer_id
        WHERE c.name = ? AND o.status = 'Pending'
    """,
        (customer_name,),
    )
    orders = cursor.fetchall()
    for order in orders:
        allocate_inventory()
        print(f"Prioritized fulfillment for Order ID {order[0]}.")


# Task 10: Fulfill All Pending Orders
def fulfill_all_orders():
    """
    "Please ensure all pending orders are fulfilled as soon as possible.
     If there’s not enough inventory, schedule production or arrange for additional components, and let me know the plan."
    """
    cursor.execute(
        """
        SELECT od.order_id, od.product_id, od.quantity, i.stock_quantity
        FROM OrderDetails od
        JOIN Orders o ON od.order_id = o.order_id
        JOIN Inventory i ON od.product_id = i.product_id
        WHERE o.status = 'Pending'
    """
    )
    orders = cursor.fetchall()
    for order_id, product_id, quantity, stock in orders:
        if stock >= quantity:
            print(
                f"Allocating {quantity} units of {product_id} for Order {order_id}."
            )
            cursor.execute(
                "UPDATE Inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                (quantity, product_id),
            )
            cursor.execute(
                "UPDATE Orders SET status = 'Fulfilled' WHERE order_id = ?",
                (order_id,),
            )
        else:
            print(
                f"Order {order_id} requires more stock for {product_id}. Scheduling production."
            )
            schedule_production(product_id, quantity - stock)
    conn.commit()


# Task 11: Increase Order Quantity and Plan Fulfillment
def increase_order_and_plan(customer_name, product_id, new_quantity):
    """
    ElectroWorld has placed a large order for 100 units of the Smart Home Hub. Please:
        Allocate available inventory for immediate fulfillment.
        Check if scheduled production can cover the shortfall.
        If not, schedule new production and ensure we have enough components.
        Finally, prepare a message to the customer detailing what we can ship now, what will be ready next week, and what’s on backlog.
    """
    # Step 1: Find the customer
    cursor.execute(
        "SELECT customer_id FROM Customers WHERE name = ?", (customer_name,)
    )
    customer = cursor.fetchone()
    if not customer:
        print(f"Customer {customer_name} not found.")
        return
    customer_id = customer[0]

    # Step 2: Increase the order quantity
    order_id = (
        f"NEW_ORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}"  # Unique ID
    )
    cursor.execute(
        """
        INSERT INTO Orders (order_id, customer_id, order_date, status) VALUES (?, ?, ?, ?)
    """,
        (
            order_id,
            customer_id,
            datetime.now().strftime("%Y-%m-%d"),
            "Pending",
        ),
    )
    cursor.execute(
        """
        INSERT INTO OrderDetails (order_id, product_id, quantity) VALUES (?, ?, ?)
    """,
        (order_id, product_id, new_quantity),
    )
    conn.commit()
    print(
        f"Order {order_id} created for {new_quantity} units of product {product_id}."
    )

    # Step 3: Check inventory for immediate allocation
    cursor.execute(
        "SELECT stock_quantity FROM Inventory WHERE product_id = ?",
        (product_id,),
    )
    inventory = cursor.fetchone()
    allocated_quantity = 0
    if inventory and inventory[0] > 0:
        allocated_quantity = min(new_quantity, inventory[0])
        cursor.execute(
            """
            UPDATE Inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?
        """,
            (allocated_quantity, product_id),
        )
        new_quantity -= allocated_quantity
        conn.commit()
        print(f"Allocated {allocated_quantity} units from inventory.")

    # Step 4: Check existing production schedules
    cursor.execute(
        """
        SELECT SUM(quantity) FROM ProductionSchedule
        WHERE product_id = ? AND status IN ('Scheduled', 'In Progress')
        AND start_date >= ?
    """,
        (product_id, datetime.now().strftime("%Y-%m-%d")),
    )
    scheduled_quantity = cursor.fetchone()[0] or 0

    if scheduled_quantity >= new_quantity:
        print(
            f"Scheduled production can cover the remaining {new_quantity} units."
        )
    else:
        # Step 5: Schedule additional production
        additional_quantity = new_quantity - scheduled_quantity
        schedule_id = (
            f"PS_{product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute(
            """
            INSERT INTO ProductionSchedule (schedule_id, product_id, start_date, end_date, quantity, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                schedule_id,
                product_id,
                start_date,
                end_date,
                additional_quantity,
                "Scheduled",
            ),
        )
        conn.commit()
        print(
            f"Scheduled additional production for {additional_quantity} units."
        )

    # Step 6: Check components availability for production
    cursor.execute(
        """
        SELECT pc.component_id, pc.quantity_needed_per_unit, c.stock_quantity
        FROM ProductComponents pc
        JOIN Components c ON pc.component_id = c.component_id
        WHERE pc.product_id = ?
    """,
        (product_id,),
    )
    components = cursor.fetchall()
    for component_id, needed_per_unit, stock_quantity in components:
        required_quantity = needed_per_unit * additional_quantity
        if stock_quantity < required_quantity:
            print(
                f"Component {component_id} is short by {required_quantity - stock_quantity} units."
            )
        else:
            print(f"Component {component_id} is sufficient.")

    # Step 7: Generate customer message
    message = (
        f"Dear {customer_name},\n\n"
        f"Your order for {new_quantity + allocated_quantity} units of {product_id}:\n"
        f"- {allocated_quantity} units will be shipped immediately.\n"
        f"- {scheduled_quantity if scheduled_quantity >= new_quantity else additional_quantity} units are scheduled for production and will be ready next week.\n"
        f"- Remaining {new_quantity - scheduled_quantity if new_quantity > scheduled_quantity else 0} units are on backlog.\n\n"
        "Thank you for your patience.\n"
    )
    print("\nCustomer Message:")
    print(message)


# Execute the tasks
print("Task 1: Check Stock")
check_stock("P001")  # Replace 'P001' with another product ID if needed

# print("\nTask 2: Low Stock Components")
# low_stock_components()

# print("\nTask 3: Delayed Orders")
# delayed_orders()

# # Execute the tasks
# print("Task 4: Expedite Orders")
# expedite_orders("ElectroWorld")

# print("\nTask 5: Allocate Inventory")
# allocate_inventory()

# print("\nTask 6: Schedule Production")
# schedule_production("P002", 50)

# print("\nTask 7: Order Components")
# order_components("C001", 200)

# print("\nTask 8: Optimize Shipment Costs")
# optimize_shipment("Los Angeles")

# print("\nTask 9: Prioritize Customer Shipments")
# prioritize_customer_shipments("ElectroWorld")

# print("\nTask 10: Fulfill All Pending Orders")
# fulfill_all_orders()

# print("\nTask 11: Increase Order Quantity and Plan Fulfillment")
# increase_order_and_plan("ElectroWorld", "P002", 100)

# Close the database connection
conn.close()
