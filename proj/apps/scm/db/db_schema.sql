-- SQLite Database Schema

-- Table: Products
CREATE TABLE Products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL,
    metadata TEXT
);

-- Table: Components
CREATE TABLE Components (
    component_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    stock_quantity INTEGER DEFAULT 0,
    metadata TEXT
);

-- Table: ProductComponents
CREATE TABLE ProductComponents (
    product_id TEXT NOT NULL,
    component_id TEXT NOT NULL,
    quantity_needed_per_unit INTEGER NOT NULL,
    PRIMARY KEY (product_id, component_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (component_id) REFERENCES Components(component_id)
);

-- Table: Inventory
CREATE TABLE Inventory (
    product_id TEXT PRIMARY KEY,
    stock_quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER AS (stock_quantity - reserved_quantity) STORED,
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- Table: Suppliers
CREATE TABLE Suppliers (
    supplier_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    contact_info TEXT,
    metadata TEXT
);

-- Table: SupplierComponents
CREATE TABLE SupplierComponents (
    supplier_id TEXT NOT NULL,
    component_id TEXT NOT NULL,
    available_quantity INTEGER DEFAULT 0,
    cost_per_unit REAL,
    PRIMARY KEY (supplier_id, component_id),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
    FOREIGN KEY (component_id) REFERENCES Components(component_id)
);

-- Table: Customers
CREATE TABLE Customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    contact_info TEXT,
    metadata TEXT
);

-- Table: Orders
CREATE TABLE Orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    metadata TEXT,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

-- Table: OrderDetails
CREATE TABLE OrderDetails (
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    allocated_quantity INTEGER DEFAULT 0,
    remaining_quantity INTEGER AS (quantity - allocated_quantity) STORED,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- Table: ProductionSchedule
CREATE TABLE ProductionSchedule (
    schedule_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_capacity INTEGER NOT NULL,
    allocated_capacity INTEGER DEFAULT 0,
    available_capacity INTEGER AS (total_capacity - allocated_capacity) STORED,
    status TEXT DEFAULT 'Scheduled',
    metadata TEXT,
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- Table: ProductionAllocation
CREATE TABLE ProductionAllocation (
    allocation_id TEXT PRIMARY KEY,
    production_schedule_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    allocated_quantity INTEGER NOT NULL,
    FOREIGN KEY (production_schedule_id) REFERENCES ProductionSchedule(schedule_id),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
);

-- Table: ShippingOptions
CREATE TABLE ShippingOptions (
    shipping_option_id TEXT PRIMARY KEY,
    destination TEXT NOT NULL,
    carrier_id TEXT NOT NULL,
    service_level TEXT,
    cost REAL,
    estimated_days INTEGER,
    metadata TEXT
);

-- Table: Shipments
CREATE TABLE Shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    shipping_option_id TEXT NOT NULL,
    shipped_date TEXT,
    tracking_number TEXT,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (shipping_option_id) REFERENCES ShippingOptions(shipping_option_id)
);

-- Table: TaskLogs
CREATE TABLE TaskLogs (
    task_id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    status TEXT DEFAULT 'In Progress',
    details TEXT
);

-- Sample Data: Products
INSERT INTO Products (product_id, name, price, description) VALUES
('P001', 'Smart Home Hub', 150.99, 'A central hub for smart home devices'),
('P002', 'Smart Thermostat', 69.99, 'An advanced thermostat with AI capabilities'),
('P003', 'Smart Light Bulb', 29.99, 'Energy-saving light bulb with smart control');

-- Sample Data: Components
INSERT INTO Components (component_id, name, description, stock_quantity) VALUES
('C001', 'Main Processor', 'The brain of the device', 150),
('C002', 'Temperature Sensor', 'Measures temperature', 250),
('C003', 'Plastic Casing', 'Protective outer shell', 500),
('C004', 'LED Element', 'Illumination component', 400);

-- Sample Data: ProductComponents
INSERT INTO ProductComponents (product_id, component_id, quantity_needed_per_unit) VALUES
('P001', 'C001', 1),
('P001', 'C003', 2),
('P002', 'C001', 1),
('P002', 'C002', 1),
('P002', 'C003', 1),
('P003', 'C004', 3),
('P003', 'C003', 1);

-- Sample Data: Inventory
INSERT INTO Inventory (product_id, stock_quantity, reserved_quantity) VALUES
('P001', 15, 10),  -- Enough for partial allocation
('P002', 6, 5),   -- Partial allocation possible
('P003', 21, 20);  -- Needs production to fulfill remaining

-- Sample Data: Customers
INSERT INTO Customers (customer_id, name, address, contact_info) VALUES
('C001', 'ElectroWorld', '123 Market Street, Los Angeles, CA', 'contact@electroworld.com'),
('C002', 'HomeTech', '456 Tech Avenue, New York, NY', 'info@hometech.com'),
('C003', 'SmartStuff', '789 Smart Street, Austin, TX', 'info@smartstuff.com');

-- Sample Data: Orders
INSERT INTO Orders (order_id, customer_id, order_date, status) VALUES
('O001', 'C001', '2025-01-01', 'Pending'),
('O002', 'C002', '2025-01-02', 'Shipped'),
('O003', 'C001', '2025-01-03', 'Pending');

-- Sample Data: OrderDetails
INSERT INTO OrderDetails (order_id, product_id, quantity, allocated_quantity) VALUES
('O001', 'P001', 30, 10),  -- 10 allocated, 20 left to allocate
('O001', 'P002', 15, 5),   -- 5 allocated, 10 left to allocate
('O003', 'P003', 100, 0);  -- None allocated yet

-- Sample Data: ProductionSchedule
INSERT INTO ProductionSchedule (schedule_id, product_id, start_date, end_date, total_capacity, allocated_capacity, status) VALUES
('PS001', 'P001', '2025-01-01', '2025-01-05', 60, 59, 'Scheduled'),  -- 1 unallocated
('PS002', 'P002', '2025-01-02', '2025-01-06', 50, 49, 'Scheduled'),  -- 1 unallocated
('PS003', 'P003', '2025-01-03', '2025-01-07', 200, 199, 'Scheduled'); -- 1 unallocated

-- Sample Data: ProductionAllocation
INSERT INTO ProductionAllocation (allocation_id, production_schedule_id, order_id, allocated_quantity) VALUES
('PA001', 'PS001', 'O999', 59),
('PA002', 'PS002', 'O999', 49);

-- Sample Data: ShippingOptions
INSERT INTO ShippingOptions (shipping_option_id, destination, carrier_id, service_level, cost, estimated_days) VALUES
('SO001', 'Los Angeles', 'CarrierX', 'Standard', 100.0, 5),
('SO002', 'New York', 'CarrierY', 'Express', 200.0, 2);

-- Sample Data: Shipments
INSERT INTO Shipments (shipment_id, order_id, shipping_option_id, shipped_date, tracking_number) VALUES
('SH001', 'O002', 'SO002', '2025-01-03', 'TRK12345');

-- Sample Data: TaskLogs
INSERT INTO TaskLogs (task_id, task_name, start_time, status, details) VALUES
('T001', 'Process Order O001', '2025-01-01T08:00:00', 'In Progress', 'Processing inventory and production allocation.');
