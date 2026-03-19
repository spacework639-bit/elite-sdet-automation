/* =========================================================
   CLEAN DROP (Respect FK Order)
========================================================= */

IF OBJECT_ID('orders', 'U') IS NOT NULL DROP TABLE orders;
IF OBJECT_ID('inventory', 'U') IS NOT NULL DROP TABLE inventory;
IF OBJECT_ID('products', 'U') IS NOT NULL DROP TABLE products;
IF OBJECT_ID('users_elite', 'U') IS NOT NULL DROP TABLE users_elite;
IF OBJECT_ID('vendors', 'U') IS NOT NULL DROP TABLE vendors;
IF OBJECT_ID('playwrights', 'U') IS NOT NULL DROP TABLE playwrights;


/* =========================================================
   BASE TABLES
========================================================= */

CREATE TABLE playwrights (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    skill NVARCHAR(255) NOT NULL
);


/* ================= USERS ================= */

CREATE TABLE users_elite (
    id INT IDENTITY PRIMARY KEY,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME()
);


/* ================= VENDORS (FIXED DESIGN) ================= */

CREATE TABLE vendors (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(255) NOT NULL
);


/* ================= PRODUCTS ================= */

CREATE TABLE products (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category NVARCHAR(100) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL,
    image_url VARCHAR(500),

    CONSTRAINT chk_price_positive CHECK (price > 0)
);


/* ================= INVENTORY ================= */

CREATE TABLE inventory (
    product_id INT PRIMARY KEY,
    stock INT NOT NULL,
    updated_at DATETIME2 DEFAULT SYSDATETIME(),

    CONSTRAINT chk_stock_non_negative CHECK (stock >= 0),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
);


/* ================= ORDERS ================= */

CREATE TABLE orders (
    order_id INT IDENTITY PRIMARY KEY,

    user_id INT NOT NULL,

    -- ✅ now properly linked
    vendor_id INT NOT NULL,

    product_id INT NOT NULL,

    -- ⚠️ derived from products.category (kept for compatibility)
    product_type NVARCHAR(100) NOT NULL,

    quantity INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status NVARCHAR(50) NOT NULL,

    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL,

    idempotency_key NVARCHAR(255) UNIQUE,

    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_total_amount_positive CHECK (total_amount > 0),

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
        REFERENCES products(id),

    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id)
        REFERENCES users_elite(id),

    CONSTRAINT fk_orders_vendor
        FOREIGN KEY (vendor_id)
        REFERENCES vendors(id)
);


/* =========================================================
   PERFORMANCE INDEXES
========================================================= */

CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_user_id ON orders(user_id);

CREATE INDEX idx_inventory_updated_at ON inventory(updated_at);
CREATE INDEX idx_products_category ON products(category);


/* =========================================================
   SEED DATA
========================================================= */

-- ✅ default vendor (keeps your existing tests working)
INSERT INTO vendors (name) VALUES ('Default Vendor');


-- ✅ optional safety user (staging stability)
INSERT INTO users_elite (email, password_hash)
VALUES ('seed_user@test.com', 'hashed_pw');


INSERT INTO products (name, price, category)
VALUES
('iPhone 15',79999,'phones'),
('Samsung Galaxy S23',69999,'phones'),
('MacBook Air M2',109999,'laptops'),
('Dell XPS 13',99999,'laptops'),
('Sony WH1000XM5 Headphones',29999,'audio'),
('Apple Watch Series 9',42999,'wearables'),
('OnePlus 12',64999,'phones'),
('iPad Air',59999,'tablets'),
('Samsung Galaxy Tab S9',54999,'tablets'),
('Logitech MX Master 3 Mouse',9999,'accessories'),
('Mechanical Keyboard RGB',6999,'accessories'),
('Gaming Monitor 27 Inch',24999,'monitors'),
('Wireless Earbuds Pro',7999,'audio'),
('Smart TV 55 Inch',59999,'electronics'),
('PS5 Console',54999,'gaming'),
('Xbox Series X',52999,'gaming'),
('External SSD 1TB',11999,'storage'),
('Laptop Backpack',2499,'accessories'),
('USB-C Hub',1999,'accessories'),
('HD Webcam',3999,'accessories');


INSERT INTO inventory (product_id, stock)
SELECT id, 100 FROM products;