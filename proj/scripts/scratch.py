import sqlite3
from proj.apps.scm.api import SCMAPI
from proj.utils.path_helpers import get_db_file
from proj.scripts.reset_db import reset_db

APP_NAME = "scm"

reset_db()
# WARNING! RESETTING DB TO SEED DATA

db_path = get_db_file(APP_NAME)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

api = SCMAPI(cursor)


def expedite_customer_orders(customer_id):
    """
    Expedites all pending orders for a specific customer.
    """
    pending_orders = api.customer_order.get_pending_orders(
        customer_id=customer_id
    )

    for order in pending_orders:
        order_id = order["order_id"]

        # Step 1: Print Initial Order Details
        order_details = api.customer_order.get_order_details(order_id)
        print(f"\nOrder Details for Order ID {order_id}:")
        for detail in order_details:
            print(
                f"- Product: {detail['product_id']}, "
                f"Requested: {detail['quantity']}, "
                f"Allocated: {detail['allocated_quantity']}, "
                f"Remaining: {detail['remaining_quantity']}"
            )

        # Step 2: Allocate Stock
        stock_allocation_results = api.inventory.allocate_stock(order_id)
        print("\nStock Allocation Results:")
        for result in stock_allocation_results:
            print(
                f"- Product: {result['product_id']}, "
                f"Newly Allocated: {result['newly_allocated_quantity']}, "
                f"Remaining: {result['remaining_quantity']}"
            )

        partially_allocated = any(
            item["remaining_quantity"] > 0 for item in stock_allocation_results
        )

        if partially_allocated:
            # Step 3: Allocate from Planned Production
            production_allocation_results = (
                api.production.allocate_prebooked_production(order_id)
            )
            print("\nProduction Allocation Results:")
            for result in production_allocation_results:
                print(
                    f"- Product: {result['product_id']}, "
                    f"Newly Allocated: {result['newly_allocated_quantity']}, "
                    f"Remaining: {result['remaining_quantity']}"
                )

            partially_allocated = any(
                item["remaining_quantity"] > 0
                for item in production_allocation_results
            )

            # Step 4: Schedule New Production if Needed
            if partially_allocated:
                production_schedule = api.production.schedule_production(
                    order_id,
                )
                print("\nNew Production Scheduled:")
                for schedule in production_schedule:
                    print(
                        f"- Product: {schedule['product_id']}, "
                        f"Quantity: {schedule['quantity']}, "
                        f"Start Date: {schedule['start_date']}"
                    )

                # Step 5: Allocate the New Production
                production_allocation_results = (
                    api.production.allocate_prebooked_production(order_id)
                )
                print("\nProduction Allocation Results (Post-Scheduling):")
                for result in production_allocation_results:
                    print(
                        f"- Product: {result['product_id']}, "
                        f"Newly Allocated: {result['newly_allocated_quantity']}, "
                        f"Remaining: {result['remaining_quantity']}"
                    )

                # Step 6: Reserve Components for New Production
                for schedule in production_schedule:
                    reserved_components = (
                        api.component.reserve_stock_components(
                            schedule["product_id"], schedule["quantity"]
                        )
                    )
                    print("\nComponent Reservations:")
                    for component in reserved_components:
                        print(
                            f"- Component: {component['component_id']}, "
                            f"Reserved: {component['reserved_quantity']}, "
                            f"Shortfall: {component['shortfall']}"
                        )
        else:
            print(f"Order ID {order_id} is Fully Allocated.\n")

    print("\nExpedited Orders Completed.")


expedite_customer_orders("C001")
