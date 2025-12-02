# 🗄️ Database Query Testing Scripts - Complete Guide

## 📦 What You Have

I've created **comprehensive database testing scripts** for both **MongoDB** and **MySQL** with complete setup guides and automation tools.

### Files Created

```
database-tests/
├── test_mongodb_queries.py    # MongoDB testing script (20KB)
├── test_mysql_queries.py      # MySQL testing script (10KB)
├── README.md                  # Detailed setup & usage guide (11KB)
├── requirements.txt           # Python dependencies
└── quickstart.sh             # Automated setup script
```

---

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
cd /home/rk/Documents/labs/lab-automation-testing/automation-testing/database-tests
pip install -r requirements.txt
```

### 2. Configure Database Connections

**MongoDB** (`test_mongodb_queries.py`):
```python
MONGO_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "test_db",
    "username": None,  # Set if auth enabled
    "password": None
}
```

**MySQL** (`test_mysql_queries.py`):
```python
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",  # UPDATE THIS!
    "database": "test_db"
}
```

### 3. Run Tests
```bash
# Automated way
./quickstart.sh

# Manual way
pytest test_mongodb_queries.py -v
pytest test_mysql_queries.py -v
```

---

## 📊 What Each Script Tests

### MongoDB Tests (`test_mongodb_queries.py`)

| Category | Tests | Key Features |
|----------|-------|--------------|
| **Insert** | `insert_one()`, `insert_many()`, duplicates | Document creation |
| **Find** | Filters, projections, sorting, pagination | Query operations |
| **Update** | `update_one()`, `update_many()`, `$inc`, `$push` | Document modification |
| **Delete** | `delete_one()`, `delete_many()` | Document removal |
| **Aggregation** | `$group`, `$match`, `$project` | Complex queries |
| **Performance** | Index testing, bulk operations | Speed optimization |

**Example Test:**
```python
def test_find_with_filter(self, users_collection, sample_users):
    """Test finding documents with filter."""
    users_collection.insert_many(sample_users)
    
    active_users = list(users_collection.find({"status": "active"}))
    
    assert len(active_users) == 2
```

### MySQL Tests (`test_mysql_queries.py`)

| Category | Tests | Key Features |
|----------|-------|--------------|
| **Insert** | `INSERT`, `INSERT MULTIPLE`, constraints | Row creation |
| **Select** | `WHERE`, `LIKE`, `IN`, `BETWEEN` | Data retrieval |
| **Aggregates** | `COUNT()`, `AVG()`, `SUM()`, `GROUP BY` | Statistical queries |
| **Update** | `UPDATE`, increment operations | Row modification |
| **Delete** | `DELETE`, cascading | Row removal |
| **Joins** | `INNER JOIN`, `LEFT JOIN` | Table relationships |
| **Transactions** | `COMMIT`, `ROLLBACK` | ACID compliance |
| **Performance** | Index testing, bulk operations | Speed optimization |

**Example Test:**
```python
def test_select_with_aggregates(self, mysql_connection, users_table, sample_users):
    """Test aggregate functions."""
    # Insert data...
    
    users_table.execute("SELECT AVG(age) as avg_age FROM users")
    result = users_table.fetchone()
    assert result["avg_age"] == 30.0
```

---

## 🔧 Prerequisites & Setup

### MongoDB Setup

**Option 1: Local Installation**
```bash
# Ubuntu/Debian
sudo apt-get install -y mongodb
sudo systemctl start mongodb

# macOS
brew install mongodb-community
brew services start mongodb-community

# Verify
mongo --eval "db.adminCommand('ping')"
```

**Option 2: MongoDB Atlas (Cloud)**
1. Sign up at https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string
4. Update `MONGO_CONFIG` in script

### MySQL Setup

**Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install mysql-server
sudo systemctl start mysql
sudo mysql_secure_installation

# macOS
brew install mysql
brew services start mysql

# Create test database
mysql -u root -p
CREATE DATABASE test_db;
EXIT;
```

**Update Configuration:**
Edit `test_mysql_queries.py` with your MySQL password!

---

## 🎯 How to Use

### Run All Tests
```bash
# MongoDB
pytest test_mongodb_queries.py -v

# MySQL
pytest test_mysql_queries.py -v
```

### Run Specific Test Class
```bash
# Only insert tests
pytest test_mongodb_queries.py::TestMongoDBInsert -v

# Only select tests
pytest test_mysql_queries.py::TestMySQLSelect -v
```

### Run Single Test
```bash
pytest test_mongodb_queries.py::TestMongoDBInsert::test_insert_one_document -v
```

### Generate HTML Report
```bash
pip install pytest-html
pytest test_mongodb_queries.py --html=report.html
```

### Show Print Statements
```bash
pytest test_mongodb_queries.py -v -s
```

---

## 🔍 Test Structure

### Fixtures (Reusable Components)

Both scripts use **pytest fixtures** for clean, reusable test setup:

```python
@pytest.fixture(scope="session")
def mysql_connection():
    """Created once for all tests"""
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    yield connection
    connection.close()

@pytest.fixture(scope="function")
def users_table(mysql_connection, cursor):
    """Created fresh for each test"""
    cursor.execute("CREATE TABLE users (...)")
    yield cursor
    # Automatic cleanup after test
```

**Benefits:**
- ✅ Automatic setup and teardown
- ✅ Isolated test environment
- ✅ No data pollution between tests
- ✅ Reusable across multiple tests

### Test Organization

```
TestMongoDBInsert / TestMySQLInsert
├── test_insert_single
├── test_insert_multiple
└── test_duplicate_handling

TestMongoDBFind / TestMySQLSelect
├── test_find_all
├── test_find_with_filter
├── test_find_with_sorting
└── test_pagination

TestMongoDBUpdate / TestMySQLUpdate
TestMongoDBDelete / TestMySQLDelete
TestMongoDBAggregate / TestMySQLJoins
TestMongoDBPerformance / TestMySQLPerformance
TestMongoDBTransactions / TestMySQLTransactions
```

---

## 🐛 Common Issues & Solutions

### MongoDB Issues

**❌ Connection Refused**
```bash
# Check if running
sudo systemctl status mongodb

# Start it
sudo systemctl start mongodb
```

**❌ Authentication Failed**
```python
# Update config with credentials
MONGO_CONFIG = {
    "username": "your_user",
    "password": "your_pass"
}
```

### MySQL Issues

**❌ Access Denied**
```bash
# Reset password
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'newpass';
FLUSH PRIVILEGES;
```

**❌ Database Not Found**
```bash
mysql -u root -p
CREATE DATABASE test_db;
```

**❌ Can't Connect**
```bash
# Check if running
sudo systemctl status mysql

# Start it
sudo systemctl start mysql
```

---

## 📚 What You Need to Know

### MongoDB Concepts

**1. Documents & Collections**
- MongoDB stores data as **documents** (like JSON)
- Documents are grouped in **collections** (like tables)

**2. Query Operators**
```python
# Comparison
{"age": {"$gt": 25}}        # Greater than
{"age": {"$gte": 25}}       # Greater than or equal
{"age": {"$lt": 30}}        # Less than
{"age": {"$in": [25, 30]}}  # In array

# Logical
{"$and": [...]}
{"$or": [...]}
{"$not": {...}}
```

**3. Update Operators**
```python
{"$set": {"age": 30}}           # Set value
{"$inc": {"age": 1}}            # Increment
{"$push": {"tags": "new"}}      # Add to array
{"$pull": {"tags": "old"}}      # Remove from array
```

### MySQL Concepts

**1. Tables & Rows**
- MySQL stores data in **tables** with fixed schema
- Each row represents a record

**2. SQL Query Types**
```sql
-- Data Manipulation
INSERT INTO users (name, age) VALUES ('John', 30);
SELECT * FROM users WHERE age > 25;
UPDATE users SET age = 31 WHERE name = 'John';
DELETE FROM users WHERE age < 18;

-- Aggregation
SELECT COUNT(*) FROM users;
SELECT AVG(age) FROM users;
SELECT status, COUNT(*) FROM users GROUP BY status;

-- Joins
SELECT users.name, orders.product
FROM users
INNER JOIN orders ON users.id = orders.user_id;
```

**3. Transactions**
```python
connection.start_transaction()
try:
    cursor.execute("INSERT ...")
    cursor.execute("UPDATE ...")
    connection.commit()
except:
    connection.rollback()
```

---

## 🎓 Learning Path

### For Beginners

1. **Start with basic CRUD tests**
   - Run `TestMongoDBInsert` and `TestMySQLInsert`
   - Understand how data is created

2. **Learn querying**
   - Run `TestMongoDBFind` and `TestMySQLSelect`
   - Experiment with different filters

3. **Explore updates and deletes**
   - Modify test data
   - See how changes work

4. **Advanced topics**
   - Aggregations
   - Joins (MySQL)
   - Transactions
   - Performance optimization

### For Advanced Users

1. **Customize tests** for your use case
2. **Add integration tests** with your application
3. **Set up CI/CD** to run tests automatically
4. **Monitor performance** and optimize queries
5. **Add stress tests** for high load scenarios

---

## 🔗 Additional Resources

### MongoDB
- 📖 [Official Docs](https://docs.mongodb.com/)
- 🐍 [PyMongo Docs](https://pymongo.readthedocs.io/)
- 🎓 [MongoDB University](https://university.mongodb.com/) (Free courses)

### MySQL
- 📖 [Official Docs](https://dev.mysql.com/doc/)
- 🐍 [MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/)
- 🎓 [MySQL Tutorial](https://www.mysqltutorial.org/)

### Testing
- 📖 [Pytest Docs](https://docs.pytest.org/)
- 🔧 [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

---

## ✅ Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set up databases**: MongoDB and/or MySQL
3. **Update configurations**: Edit connection settings in scripts
4. **Run quickstart**: `./quickstart.sh`
5. **Explore tests**: Run individual test classes
6. **Customize**: Add your own test scenarios
7. **Integrate**: Add to your CI/CD pipeline

---

## 💡 Pro Tips

1. **Use fixtures** - They make tests cleaner and more maintainable
2. **Test one thing** - Each test should verify one specific behavior
3. **Clean up** - Always clean test data to avoid pollution
4. **Use indexes** - Performance tests show the difference
5. **Handle errors** - Test both success and failure cases
6. **Document tests** - Clear docstrings help others understand

---

**Need Help?** Check `README.md` for detailed troubleshooting and examples!
