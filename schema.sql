/* =========================================================
   CLEAN DROP (Respect FK Order)
========================================================= */

IF OBJECT_ID('orders', 'U') IS NOT NULL DROP TABLE orders;
IF OBJECT_ID('inventory', 'U') IS NOT NULL DROP TABLE inventory;
IF OBJECT_ID('products', 'U') IS NOT NULL DROP TABLE products;
IF OBJECT_ID('playwrights', 'U') IS NOT NULL DROP TABLE playwrights;


/* =========================================================
   BASE TABLES
========================================================= */

CREATE TABLE playwrights (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    skill NVARCHAR(255) NOT NULL
);


CREATE TABLE products (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category NVARCHAR(100) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL,

    CONSTRAINT chk_price_positive CHECK (price > 0)
);


CREATE TABLE inventory (
    product_id INT PRIMARY KEY,
    stock INT NOT NULL,
    updated_at DATETIME2 DEFAULT SYSDATETIME(),

    CONSTRAINT chk_stock_non_negative CHECK (stock >= 0),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE NO ACTION
);


CREATE TABLE orders (
    order_id INT IDENTITY PRIMARY KEY,
    user_id INT NOT NULL,
    vendor_id INT NOT NULL,
    product_id INT NOT NULL,
    product_type NVARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status NVARCHAR(50) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL,
    idempotency_key NVARCHAR(255) UNIQUE,

    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_total_amount_positive CHECK (total_amount > 0),

    -- ✅ UPDATED STATUS CONSTRAINT (LOWERCASE + FULL LIFECYCLE)
    CONSTRAINT chk_status_valid CHECK (
        status IN (
            'pending',
            'confirmed',
            'shipped',
            'completed',
            'return_requested',
            'returned',
            'refunded',
            'cancelled'
        )
    ),

    CONSTRAINT fk_orders_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE NO ACTION
);

/* =========================================================
   PERFORMANCE INDEXES (CRITICAL)
========================================================= */

-- Orders performance
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- Inventory lookup optimization
CREATE INDEX idx_inventory_updated_at ON inventory(updated_at);

-- Products category search optimization
CREATE INDEX idx_products_category ON products(category);


/* =========================================================
   SEED DATA
========================================================= */

INSERT INTO products (name, price, category)
VALUES 
('Ashwagandha Powder', 299.00, 'Herbal'),
('Tulsi Capsules', 199.00, 'Herbal'),
('Neem Tablets', 249.00, 'Herbal');

INSERT INTO inventory (product_id, stock)
SELECT id, 100 FROM products;
