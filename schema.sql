IF OBJECT_ID('orders', 'U') IS NOT NULL DROP TABLE orders;
IF OBJECT_ID('inventory', 'U') IS NOT NULL DROP TABLE inventory;
IF OBJECT_ID('products', 'U') IS NOT NULL DROP TABLE products;
IF OBJECT_ID('playwrights', 'U') IS NOT NULL DROP TABLE playwrights;


CREATE TABLE playwrights (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(255),
    skill NVARCHAR(255)
);


CREATE TABLE products (
    id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category NVARCHAR(100),
    created_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE inventory (
    product_id INT PRIMARY KEY,
    stock INT NOT NULL,
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE orders (
    order_id INT IDENTITY PRIMARY KEY,
    user_id INT,
    vendor_id INT,
    product_type NVARCHAR(100),
    product_id INT NOT NULL,
    total_amount DECIMAL(10,2),
    status NVARCHAR(50),
    created_at DATETIME DEFAULT GETDATE(),
    idempotency_key NVARCHAR(255),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Seed initial data
INSERT INTO products (name, price, category)
VALUES 
('Ashwagandha Powder', 299.00, 'Herbal'),
('Tulsi Capsules', 199.00, 'Herbal'),
('Neem Tablets', 249.00, 'Herbal');

INSERT INTO inventory (product_id, stock)
SELECT id, 100 FROM products;
