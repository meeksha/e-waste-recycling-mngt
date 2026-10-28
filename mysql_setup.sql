-- =======================================
--  E-Waste DB: FULL SETUP SCRIPT
--  Schema + Sample Data + Triggers + Procedures
-- =======================================

CREATE DATABASE IF NOT EXISTS ewaste_db;
USE ewaste_db;

-- Optional: clean old tables if re-running
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS batch_item;
DROP TABLE IF EXISTS recycling_batch;
DROP TABLE IF EXISTS ewaste_item;
DROP TABLE IF EXISTS pickup_request;
DROP TABLE IF EXISTS ewaste_category;
DROP TABLE IF EXISTS collection_center;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- ======================
--  TABLES
-- ======================

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    user_type ENUM('citizen','center_admin','admin') DEFAULT 'citizen',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE collection_center (
    center_id INT AUTO_INCREMENT PRIMARY KEY,
    center_name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(100),
    contact_no VARCHAR(15),
    capacity_kg DECIMAL(10,2) NOT NULL,
    current_load_kg DECIMAL(10,2) NOT NULL DEFAULT 0.00
);

CREATE TABLE ewaste_category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    hazard_level ENUM('Low','Medium','High') DEFAULT 'Medium'
);

CREATE TABLE pickup_request (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pickup_address VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    request_date DATE,
    preferred_slot ENUM('Morning','Afternoon','Evening'),
    status ENUM('Pending','Scheduled','Completed','Cancelled'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pickup_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE ewaste_item (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NULL,
    center_id INT NOT NULL,
    category_id INT NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(100),
    weight_kg DECIMAL(10,2) NOT NULL,
    item_condition ENUM('Working','Damaged','Scrap') DEFAULT 'Damaged', -- renamed from condition
    intake_type ENUM('Pickup','Dropoff') NOT NULL,
    intake_date DATE,  -- removed DEFAULT CURRENT_DATE for compatibility
    status ENUM('Stored','Recycled','Disposed') DEFAULT 'Stored',
    CONSTRAINT fk_item_request
        FOREIGN KEY (request_id) REFERENCES pickup_request(request_id),
    CONSTRAINT fk_item_center
        FOREIGN KEY (center_id) REFERENCES collection_center(center_id),
    CONSTRAINT fk_item_category
        FOREIGN KEY (category_id) REFERENCES ewaste_category(category_id)
);

CREATE TABLE recycling_batch (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    center_id INT NOT NULL,
    batch_date DATE NOT NULL,
    total_weight_kg DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    treatment_type ENUM('Recycling','Refurbish','Safe_Disposal') DEFAULT 'Recycling',
    status ENUM('Open','Closed') DEFAULT 'Open',
    CONSTRAINT fk_batch_center
        FOREIGN KEY (center_id) REFERENCES collection_center(center_id)
);

CREATE TABLE batch_item (
    batch_id INT NOT NULL,
    item_id INT NOT NULL,
    PRIMARY KEY (batch_id, item_id),
    CONSTRAINT fk_batchitem_batch
        FOREIGN KEY (batch_id) REFERENCES recycling_batch(batch_id),
    CONSTRAINT fk_batchitem_item
        FOREIGN KEY (item_id) REFERENCES ewaste_item(item_id)
);

-- ======================
--  SAMPLE DATA
-- ======================

INSERT INTO users (full_name, email, phone, user_type) VALUES
('Rahul Sharma', 'rahul@example.com', '9876543210', 'citizen'),
('Green Center Admin', 'center1@example.com', '9000000001', 'center_admin');

INSERT INTO collection_center (center_name, address, city, contact_no, capacity_kg)
VALUES
('Green E-Waste Hub', 'Street 1, Area A', 'Bengaluru', '9000000001', 1000.00),
('EcoRecycle Point', 'Street 2, Area B', 'Bengaluru', '9000000002', 500.00);

INSERT INTO ewaste_category (category_name, hazard_level) VALUES
('Mobile Phone', 'Medium'),
('Laptop', 'High'),
('Television', 'High');

-- One example pickup_request
INSERT INTO pickup_request (user_id, pickup_address, city, preferred_slot)
VALUES (1, 'Flat 101, Area A', 'Bengaluru', 'Morning');

-- ======================
--  TRIGGERS
-- ======================

DELIMITER $$

-- Before insert on pickup_request: ensure default status and date
CREATE TRIGGER trg_before_pickup_insert
BEFORE INSERT ON pickup_request
FOR EACH ROW
BEGIN
    IF NEW.status IS NULL THEN
        SET NEW.status = 'Pending';
    END IF;
    IF NEW.request_date IS NULL THEN
        SET NEW.request_date = CURDATE();
    END IF;
END$$

-- After insert on ewaste_item: update center load
CREATE TRIGGER trg_after_item_insert
AFTER INSERT ON ewaste_item
FOR EACH ROW
BEGIN
    UPDATE collection_center
    SET current_load_kg = current_load_kg + NEW.weight_kg
    WHERE center_id = NEW.center_id;
END$$

-- After update on recycling_batch: when closed, reduce center load
CREATE TRIGGER trg_after_batch_update
AFTER UPDATE ON recycling_batch
FOR EACH ROW
BEGIN
    IF NEW.status = 'Closed' AND OLD.status <> 'Closed' THEN
        UPDATE collection_center
        SET current_load_kg = current_load_kg - NEW.total_weight_kg
        WHERE center_id = NEW.center_id;
    END IF;
END$$

DELIMITER ;

-- ======================
--  STORED PROCEDURES
-- ======================

DELIMITER $$

-- Create pickup request
CREATE PROCEDURE sp_create_pickup_request (
    IN p_user_id INT,
    IN p_pickup_address VARCHAR(255),
    IN p_city VARCHAR(100),
    IN p_slot VARCHAR(20)
)
BEGIN
    INSERT INTO pickup_request (user_id, pickup_address, city, preferred_slot)
    VALUES (p_user_id, p_pickup_address, p_city, p_slot);
END$$

-- Center load report by city
CREATE PROCEDURE sp_center_load_report (
    IN p_city VARCHAR(100)
)
BEGIN
    SELECT center_name,
           capacity_kg,
           current_load_kg,
           ROUND((current_load_kg / capacity_kg) * 100, 2) AS utilization_pct
    FROM collection_center
    WHERE city = p_city;
END$$

-- User recycling summary
CREATE PROCEDURE sp_user_recycling_summary (
    IN p_user_id INT
)
BEGIN
    SELECT u.full_name,
           COUNT(e.item_id) AS total_items,
           SUM(e.weight_kg) AS total_weight_kg
    FROM users u
    JOIN pickup_request p ON u.user_id = p.user_id
    JOIN ewaste_item e ON p.request_id = e.request_id
    WHERE u.user_id = p_user_id
    GROUP BY u.user_id, u.full_name;
END$$

DELIMITER ;
