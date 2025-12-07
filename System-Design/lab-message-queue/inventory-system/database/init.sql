-- Initialize database schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (run models to generate via Alembic in production)

-- Sample data
INSERT INTO warehouses (id, code, name, type, is_active, priority) VALUES
    (uuid_generate_v4(), 'WH1', 'Main Warehouse', 'fulfillment', true, 1),
    (uuid_generate_v4(), 'WH2', 'East Coast Warehouse', 'fulfillment', true, 2),
    (uuid_generate_v4(), 'WH3', 'West Coast Warehouse', 'fulfillment', true, 2);

INSERT INTO categories (id, name, slug, level) VALUES
    (uuid_generate_v4(), 'Electronics', 'electronics', 0),
    (uuid_generate_v4(), 'Clothing', 'clothing', 0);

INSERT INTO brands (id, name, slug) VALUES
    (uuid_generate_v4(), 'TechCorp', 'techcorp'),
    (uuid_generate_v4(), 'FashionBrand', 'fashionbrand');
