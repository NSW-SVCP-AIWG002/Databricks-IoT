-- Database initialization script
-- This script runs when the MySQL container is first created

USE databricks_iot;

-- Example: Create a sample table
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Example: Insert sample data
INSERT INTO devices (device_name, device_type, status) VALUES
    ('Sensor-001', 'temperature', 'active'),
    ('Sensor-002', 'humidity', 'active'),
    ('Gateway-001', 'gateway', 'active');
