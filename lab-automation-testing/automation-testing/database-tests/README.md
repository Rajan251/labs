# Database Query Testing Guide

This guide explains how to use the MongoDB and MySQL query testing scripts.

## 📋 Table of Contents

1. [Overview](#overview)
2. [MongoDB Testing](#mongodb-testing)
3. [MySQL Testing](#mysql-testing)
4. [Running the Tests](#running-the-tests)
5. [Common Issues & Solutions](#common-issues--solutions)

---

## Overview

Both test scripts provide comprehensive testing for database operations including:
- **CRUD Operations** (Create, Read, Update, Delete)
- **Query Filtering** (WHERE clauses, comparison operators)
- **Aggregations** (COUNT, AVG, SUM, GROUP BY)
- **Performance Testing** (with and without indexes)
- **Transactions** (commit and rollback)

---

## MongoDB Testing

### Prerequisites

**1. Install MongoDB**

**Option A: Local Installation**
```bash
# Ubuntu/Debian
sudo apt-get install -y mongodb

# macOS
brew install mongodb-community

# Start MongoDB service
sudo systemctl start mongodb  # Linux
brew services start mongodb-community  # macOS
```

**Option B: MongoDB Atlas (Cloud)**
- Sign up at https://www.mongodb.com/cloud/atlas
- Create a free cluster
- Get your connection string

**2. Install Python Dependencies**
```bash
pip install pymongo pytest pytest-asyncio motor
```

### Configuration

Edit `test_mongodb_queries.py` and update the connection settings:

```python
MONGO_CONFIG = {
    "host": "localhost",      # Change to your MongoDB host
    "port": 27017,           # Default MongoDB port
    "database": "test_db",   # Database name for testing
    "username": None,        # Set if authentication is enabled
    "password": None,        # Set if authentication is enabled
}
```

**For MongoDB Atlas:**
```python
# Use connection string instead
connection_string = "mongodb+srv://username:password@cluster.mongodb.net/test_db"
```

### What the MongoDB Script Tests

| Test Category | What It Tests | Example |
|--------------|---------------|---------|
| **Insert Operations** | `insert_one()`, `insert_many()`, duplicate handling | Creating new documents |
| **Find Operations** | `find()`, filters, projections, sorting, pagination | Querying documents |
| **Update Operations** | `update_one()`, `update_many()`, `$inc`, `$push`, `$pull` | Modifying documents |
| **Delete Operations** | `delete_one()`, `delete_many()` | Removing documents |
| **Aggregations** | `$group`, `$match`, `$project`, averages, counts | Complex queries |
| **Performance** | Index performance, bulk operations | Speed optimization |

### Key MongoDB Concepts Tested

**1. Query Operators**
```python
# Comparison operators
{"age": {"$gt": 28}}           # Greater than
{"age": {"$gte": 25, "$lte": 32}}  # Range

# Logical operators
{"$and": [{"status": "active"}, {"age": {"$gt": 28}}]}
{"$or": [{"status": "inactive"}, {"age": {"$gt": 32}}]}

# Array operators
{"tags": {"$in": ["developer", "designer"]}}
```

**2. Nested Documents**
```python
# Query nested fields
{"profile.location": "New York"}
```

**3. Aggregation Pipeline**
```python
pipeline = [
    {"$match": {"status": "active"}},
    {"$group": {"_id": "$status", "count": {"$sum": 1}}}
]
```

---

## MySQL Testing

### Prerequisites

**1. Install MySQL**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mysql-server
sudo systemctl start mysql
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

**Windows:**
- Download from https://dev.mysql.com/downloads/installer/
- Run the installer

**2. Create Test Database**
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE test_db;
EXIT;
```

**3. Install Python Dependencies**
```bash
pip install mysql-connector-python pytest
```

### Configuration

Edit `test_mysql_queries.py` and update the connection settings:

```python
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",  # UPDATE THIS!
    "database": "test_db",
    "auth_plugin": "mysql_native_password"
}
```

### What the MySQL Script Tests

| Test Category | What It Tests | Example |
|--------------|---------------|---------|
| **Insert Operations** | `INSERT`, `INSERT MULTIPLE`, unique constraints | Adding new rows |
| **Select Operations** | `SELECT`, `WHERE`, `LIKE`, `IN`, `BETWEEN` | Querying data |
| **Aggregate Functions** | `COUNT()`, `AVG()`, `SUM()`, `MIN()`, `MAX()` | Statistical queries |
| **Group By** | `GROUP BY`, `HAVING` | Grouping results |
| **Update Operations** | `UPDATE`, increment operations | Modifying rows |
| **Delete Operations** | `DELETE`, cascading deletes | Removing rows |
| **Joins** | `INNER JOIN`, `LEFT JOIN` | Combining tables |
| **Transactions** | `COMMIT`, `ROLLBACK` | ACID compliance |
| **Performance** | Index performance, bulk operations | Speed optimization |

### Key MySQL Concepts Tested

**1. SQL Query Patterns**
```sql
-- Basic SELECT
SELECT * FROM users WHERE status = 'active';

-- Comparison operators
SELECT * FROM users WHERE age > 28;
SELECT * FROM users WHERE age BETWEEN 25 AND 32;

-- Pattern matching
SELECT * FROM users WHERE username LIKE '%john%';

-- Sorting and pagination
SELECT * FROM users ORDER BY age DESC LIMIT 10 OFFSET 0;
```

**2. Aggregate Functions**
```sql
SELECT COUNT(*) FROM users;
SELECT AVG(age) FROM users;
SELECT status, COUNT(*) FROM users GROUP BY status;
```

**3. Joins**
```sql
SELECT users.username, orders.product_name
FROM users
INNER JOIN orders ON users.id = orders.user_id;
```

**4. Transactions**
```sql
START TRANSACTION;
INSERT INTO users (username, email) VALUES ('user1', 'user1@example.com');
INSERT INTO users (username, email) VALUES ('user2', 'user2@example.com');
COMMIT;  -- or ROLLBACK;
```

---

## Running the Tests

### Run All Tests

**MongoDB:**
```bash
cd /home/rk/Documents/labs/lab-automation-testing/automation-testing/database-tests
pytest test_mongodb_queries.py -v
```

**MySQL:**
```bash
cd /home/rk/Documents/labs/lab-automation-testing/automation-testing/database-tests
pytest test_mysql_queries.py -v
```

### Run Specific Test Classes

```bash
# MongoDB - Run only insert tests
pytest test_mongodb_queries.py::TestMongoDBInsert -v

# MySQL - Run only select tests
pytest test_mysql_queries.py::TestMySQLSelect -v
```

### Run Specific Test Functions

```bash
# MongoDB - Run single test
pytest test_mongodb_queries.py::TestMongoDBInsert::test_insert_one_document -v

# MySQL - Run single test
pytest test_mysql_queries.py::TestMySQLInsert::test_insert_single_row -v
```

### Run with Detailed Output

```bash
# Show print statements
pytest test_mongodb_queries.py -v -s

# Show detailed error traces
pytest test_mongodb_queries.py -v --tb=long
```

### Generate Test Report

```bash
# Install pytest-html
pip install pytest-html

# Generate HTML report
pytest test_mongodb_queries.py --html=report_mongodb.html
pytest test_mysql_queries.py --html=report_mysql.html
```

---

## Common Issues & Solutions

### MongoDB Issues

**Issue 1: Connection Refused**
```
Error: ConnectionFailure: [Errno 111] Connection refused
```
**Solution:**
```bash
# Check if MongoDB is running
sudo systemctl status mongodb

# Start MongoDB
sudo systemctl start mongodb

# Check port
netstat -tuln | grep 27017
```

**Issue 2: Authentication Failed**
```
Error: Authentication failed
```
**Solution:**
```python
# Update MONGO_CONFIG with correct credentials
MONGO_CONFIG = {
    "username": "your_username",
    "password": "your_password"
}
```

**Issue 3: Database Not Found**
```
MongoDB will automatically create the database when you insert data.
No action needed - this is normal behavior.
```

### MySQL Issues

**Issue 1: Access Denied**
```
Error: ER_ACCESS_DENIED_ERROR: Access denied for user 'root'@'localhost'
```
**Solution:**
```bash
# Reset MySQL root password
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'new_password';
FLUSH PRIVILEGES;
EXIT;
```

**Issue 2: Database Does Not Exist**
```
Error: ER_BAD_DB_ERROR: Unknown database 'test_db'
```
**Solution:**
```bash
mysql -u root -p
CREATE DATABASE test_db;
EXIT;
```

**Issue 3: Can't Connect to MySQL Server**
```
Error: Can't connect to MySQL server on 'localhost'
```
**Solution:**
```bash
# Check if MySQL is running
sudo systemctl status mysql

# Start MySQL
sudo systemctl start mysql

# Check port
netstat -tuln | grep 3306
```

**Issue 4: Authentication Plugin Error**
```
Error: Authentication plugin 'caching_sha2_password' cannot be loaded
```
**Solution:**
```python
# Update MYSQL_CONFIG
MYSQL_CONFIG = {
    ...
    "auth_plugin": "mysql_native_password"
}
```

Or change MySQL user authentication:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
```

### General Testing Issues

**Issue: Tests are slow**
**Solution:**
- Use test fixtures properly
- Clean up data after each test
- Use indexes for better performance

**Issue: Tests fail intermittently**
**Solution:**
- Ensure proper cleanup in fixtures
- Use transactions where appropriate
- Avoid hardcoded IDs or timestamps

---

## Test Structure Explanation

### Fixtures

Both scripts use pytest fixtures for:

1. **Session-level fixtures**: Database connections (created once per test session)
2. **Function-level fixtures**: Tables/collections (created/cleaned for each test)
3. **Data fixtures**: Sample data generators

```python
@pytest.fixture(scope="session")
def mysql_connection():
    # Created once for all tests
    
@pytest.fixture(scope="function")
def users_table(mysql_connection):
    # Created for each test function
```

### Test Organization

Tests are organized into classes by operation type:

```
TestMongoDBInsert / TestMySQLInsert
TestMongoDBFind / TestMySQLSelect
TestMongoDBUpdate / TestMySQLUpdate
TestMongoDBDelete / TestMySQLDelete
TestMongoDBAggregate / TestMySQLJoins
TestMongoDBPerformance / TestMySQLPerformance
TestMongoDBTransactions / TestMySQLTransactions
```

---

## Next Steps

1. **Customize the tests** for your specific use cases
2. **Add more test scenarios** based on your application needs
3. **Integrate with CI/CD** pipeline (Jenkins, GitHub Actions, etc.)
4. **Monitor test performance** and optimize slow queries
5. **Add data validation tests** for your specific business logic

---

## Additional Resources

### MongoDB
- Official Docs: https://docs.mongodb.com/
- PyMongo Docs: https://pymongo.readthedocs.io/
- MongoDB University: https://university.mongodb.com/

### MySQL
- Official Docs: https://dev.mysql.com/doc/
- MySQL Connector/Python: https://dev.mysql.com/doc/connector-python/en/
- MySQL Tutorial: https://www.mysqltutorial.org/

### Pytest
- Pytest Docs: https://docs.pytest.org/
- Pytest Fixtures: https://docs.pytest.org/en/stable/fixture.html
