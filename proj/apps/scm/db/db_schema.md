**Table: Products**

    - product_id TEXT PRIMARY KEY
    - name TEXT NOT NULL
    - description TEXT

**Table: Components**

    - component_id TEXT PRIMARY KEY
    - name TEXT NOT NULL
    - description TEXT
    - stock_quantity INTEGER

**Table: ProductComponents**

    - product_id TEXT PRIMARY KEY NOT NULL
    - component_id TEXT PRIMARY KEY NOT NULL
    - quantity_needed_per_unit INTEGER NOT NULL

**Table: Inventory**

    - product_id TEXT PRIMARY KEY
    - stock_quantity INTEGER

**Table: Suppliers**

    - supplier_id TEXT PRIMARY KEY
    - name TEXT NOT NULL
    - contact_info TEXT

**Table: SupplierComponents**

    - supplier_id TEXT PRIMARY KEY NOT NULL
    - component_id TEXT PRIMARY KEY NOT NULL
    - available_quantity INTEGER
    - cost_per_unit REAL

**Table: Customers**

    - customer_id TEXT PRIMARY KEY
    - name TEXT NOT NULL
    - address TEXT
    - contact_info TEXT

**Table: Orders**

    - order_id TEXT PRIMARY KEY
    - customer_id TEXT NOT NULL
    - order_date TEXT NOT NULL
    - status TEXT

**Table: OrderDetails**

    - order_id TEXT PRIMARY KEY NOT NULL
    - product_id TEXT PRIMARY KEY NOT NULL
    - quantity INTEGER NOT NULL

**Table: ProductionSchedule**

    - schedule_id TEXT PRIMARY KEY
    - product_id TEXT NOT NULL
    - start_date TEXT NOT NULL
    - end_date TEXT NOT NULL
    - quantity INTEGER NOT NULL
    - status TEXT

**Table: ShippingOptions**

    - shipping_option_id TEXT PRIMARY KEY
    - destination TEXT NOT NULL
    - carrier_id TEXT NOT NULL
    - service_level TEXT
    - cost REAL
    - estimated_days INTEGER

**Table: Shipments**

    - shipment_id TEXT PRIMARY KEY
    - order_id TEXT NOT NULL
    - shipping_option_id TEXT NOT NULL
    - shipped_date TEXT
    - tracking_number TEXT
