"""
MySQL Query Testing Script
===========================

This script tests MySQL queries including CRUD operations, joins, transactions,
stored procedures, and performance testing.

Requirements:
- mysql-connector-python or PyMySQL
- pytest

Installation:
    pip install mysql-connector-python pytest

Setup:
1. Install MySQL locally or use a cloud instance
2. Create a test database
3. Update the connection configuration in the script
4. Run tests: pytest test_mysql_queries.py -v
"""

import pytest
import mysql.connector
from mysql.connector import Error, errorcode
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any


# ============================================================================
# CONFIGURATION
# ============================================================================
# MySQL Connection Configuration
# For Docker: Use password "testpassword" (from docker-compose.yml)
# For Local: Use your actual MySQL root password
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "testpassword",  # Docker default, change for local MySQL
    "database": "test_db",
    "auth_plugin": "mysql_native_password"
}


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def mysql_connection():
    """Create MySQL connection for the entire test session."""
    connection = None
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"\n✓ Connected to MySQL Server version {db_info}")
            yield connection
    except Error as e:
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            pytest.fail("MySQL: Invalid username or password")
        elif e.errno == errorcode.ER_BAD_DB_ERROR:
            pytest.fail("MySQL: Database does not exist")
        else:
            pytest.fail(f"MySQL Error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n✓ MySQL connection closed")


@pytest.fixture(scope="function")
def cursor(mysql_connection):
    """Create cursor for each test and handle cleanup."""
    cursor = mysql_connection.cursor(dictionary=True)
    yield cursor
    cursor.close()


@pytest.fixture(scope="function")
def clean_database(mysql_connection, cursor):
    """Clean database before each test."""
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in tables:
        table_name = list(table.values())[0]
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    mysql_connection.commit()
    yield


@pytest.fixture(scope="function")
def users_table(mysql_connection, cursor, clean_database):
    """Create users table for testing."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        age INT,
        status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_username (username),
        INDEX idx_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    cursor.execute(create_table_query)
    mysql_connection.commit()
    yield cursor


@pytest.fixture
def sample_users() -> List[Dict[str, Any]]:
    """Generate sample user data."""
    return [
        {"username": "john_doe", "email": "john@example.com", "age": 30, "status": "active"},
        {"username": "jane_smith", "email": "jane@example.com", "age": 25, "status": "active"},
        {"username": "bob_wilson", "email": "bob@example.com", "age": 35, "status": "inactive"}
    ]


# ============================================================================
# CREATE (INSERT) TESTS
# ============================================================================

class TestMySQLInsert:
    """Test MySQL INSERT operations."""
    
    def test_insert_single_row(self, mysql_connection, users_table):
        """Test inserting a single row."""
        insert_query = "INSERT INTO users (username, email, age, status) VALUES (%s, %s, %s, %s)"
        values = ("test_user", "test@example.com", 28, "active")
        users_table.execute(insert_query, values)
        mysql_connection.commit()
        
        assert users_table.rowcount == 1
        
        users_table.execute("SELECT * FROM users WHERE username = %s", ("test_user",))
        user = users_table.fetchone()
        assert user["username"] == "test_user"
    
    def test_insert_multiple_rows(self, mysql_connection, users_table, sample_users):
        """Test inserting multiple rows."""
        insert_query = "INSERT INTO users (username, email, age, status) VALUES (%s, %s, %s, %s)"
        values = [(u["username"], u["email"], u["age"], u["status"]) for u in sample_users]
        
        users_table.executemany(insert_query, values)
        mysql_connection.commit()
        
        assert users_table.rowcount == 3


# ============================================================================
# READ (SELECT) TESTS
# ============================================================================

class TestMySQLSelect:
    """Test MySQL SELECT operations."""
    
    def test_select_all_rows(self, mysql_connection, users_table, sample_users):
        """Test selecting all rows."""
        insert_query = "INSERT INTO users (username, email, age, status) VALUES (%s, %s, %s, %s)"
        values = [(u["username"], u["email"], u["age"], u["status"]) for u in sample_users]
        users_table.executemany(insert_query, values)
        mysql_connection.commit()
        
        users_table.execute("SELECT * FROM users")
        users = users_table.fetchall()
        assert len(users) == 3
    
    def test_select_with_where(self, mysql_connection, users_table, sample_users):
        """Test SELECT with WHERE clause."""
        insert_query = "INSERT INTO users (username, email, age, status) VALUES (%s, %s, %s, %s)"
        values = [(u["username"], u["email"], u["age"], u["status"]) for u in sample_users]
        users_table.executemany(insert_query, values)
        mysql_connection.commit()
        
        users_table.execute("SELECT * FROM users WHERE status = %s", ("active",))
        active_users = users_table.fetchall()
        assert len(active_users) == 2
    
    def test_select_with_aggregates(self, mysql_connection, users_table, sample_users):
        """Test aggregate functions."""
        insert_query = "INSERT INTO users (username, email, age, status) VALUES (%s, %s, %s, %s)"
        values = [(u["username"], u["email"], u["age"], u["status"]) for u in sample_users]
        users_table.executemany(insert_query, values)
        mysql_connection.commit()
        
        users_table.execute("SELECT AVG(age) as avg_age FROM users")
        result = users_table.fetchone()
        assert result["avg_age"] == 30.0


# ============================================================================
# UPDATE TESTS
# ============================================================================

class TestMySQLUpdate:
    """Test MySQL UPDATE operations."""
    
    def test_update_single_row(self, mysql_connection, users_table, sample_users):
        """Test updating a single row."""
        insert_query = "INSERT INTO users (username, email, age, status) VALUES (%s, %s, %s, %s)"
        values = [(u["username"], u["email"], u["age"], u["status"]) for u in sample_users]
        users_table.executemany(insert_query, values)
        mysql_connection.commit()
        
        update_query = "UPDATE users SET age = %s WHERE username = %s"
        users_table.execute(update_query, (31, "john_doe"))
        mysql_connection.commit()
        
        assert users_table.rowcount == 1


# ============================================================================
# DELETE TESTS
# ============================================================================

class TestMySQLDelete:
    """Test MySQL DELETE operations."""
    
    def test_delete_single_row(self, mysql_connection, users_table, sample_users):
        """Test deleting a single row."""
        insert_query = "INSERT INTO users (username, email, age, status) VALUES (%s, %s, %s, %s)"
        values = [(u["username"], u["email"], u["age"], u["status"]) for u in sample_users]
        users_table.executemany(insert_query, values)
        mysql_connection.commit()
        
        delete_query = "DELETE FROM users WHERE username = %s"
        users_table.execute(delete_query, ("john_doe",))
        mysql_connection.commit()
        
        assert users_table.rowcount == 1


# ============================================================================
# TRANSACTION TESTS
# ============================================================================

class TestMySQLTransactions:
    """Test MySQL transaction handling."""
    
    def test_transaction_commit(self, mysql_connection, users_table):
        """Test successful transaction commit."""
        try:
            mysql_connection.start_transaction()
            
            insert_query = "INSERT INTO users (username, email, age) VALUES (%s, %s, %s)"
            users_table.execute(insert_query, ("user1", "user1@example.com", 25))
            users_table.execute(insert_query, ("user2", "user2@example.com", 30))
            
            mysql_connection.commit()
        except Error as e:
            mysql_connection.rollback()
            pytest.fail(f"Transaction failed: {e}")
        
        users_table.execute("SELECT COUNT(*) as count FROM users")
        result = users_table.fetchone()
        assert result["count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
