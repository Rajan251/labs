# 🔄 Test Cleanup & Data Management Guide

## ✅ YES - Tests Automatically Revert Changes!

The test scripts are designed to **automatically clean up all test data** after each test runs. Here's how it works:

---

## 🧹 How Cleanup Works

### MongoDB Cleanup

```python
@pytest.fixture(scope="function")
def test_db(mongo_client):
    """Get test database and clean up after each test."""
    db = mongo_client[MONGO_CONFIG["database"]]
    yield db
    
    # 🔄 CLEANUP: Drop all collections after each test
    for collection_name in db.list_collection_names():
        db[collection_name].drop()
```

**What happens:**
1. ✅ Test creates collections and inserts data
2. ✅ Test runs and validates results
3. ✅ **After test completes** → All collections are dropped
4. ✅ Next test starts with a clean database

### MySQL Cleanup

```python
@pytest.fixture(scope="function")
def clean_database(mysql_connection, cursor):
    """Clean database before each test."""
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    # Drop all tables before test
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in tables:
        table_name = list(table.values())[0]
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    mysql_connection.commit()
    yield
    
    # 🔄 CLEANUP: Drop all tables after test (same process)
```

**What happens:**
1. ✅ Before test → Drop all existing tables
2. ✅ Test creates tables and inserts data
3. ✅ Test runs and validates results
4. ✅ **After test completes** → All tables are dropped again
5. ✅ Next test starts with a clean database

---

## 🎯 Key Points About Cleanup

### ✅ What Gets Cleaned Up

| Item | MongoDB | MySQL |
|------|---------|-------|
| **Tables/Collections** | ✅ Dropped | ✅ Dropped |
| **Data/Documents** | ✅ Deleted | ✅ Deleted |
| **Indexes** | ✅ Removed | ✅ Removed |
| **Test artifacts** | ✅ Removed | ✅ Removed |

### ✅ What Stays

| Item | Status |
|------|--------|
| **Database itself** | ✅ Remains (only `test_db`) |
| **Connection** | ✅ Reused across tests |
| **Production data** | ✅ **NEVER TOUCHED** (different database) |

### 🔒 Safety Features

1. **Isolated Test Database**: Uses `test_db` - separate from production
2. **Automatic Cleanup**: No manual intervention needed
3. **Fresh State**: Each test starts with clean slate
4. **No Data Pollution**: Tests don't affect each other

---

## 📍 Where Should You Run These Tests?

### ✅ Recommended Environments

#### 1. **Local Development (Best for Learning)**

**Setup:**
```bash
# Your laptop/workstation
cd /home/rk/Documents/labs/lab-automation-testing/automation-testing/database-tests
./quickstart.sh
```

**Pros:**
- ✅ Fast feedback
- ✅ Easy debugging
- ✅ No network latency
- ✅ Free

**Cons:**
- ❌ Need to install databases locally
- ❌ Only you can run tests

**When to use:**
- Learning database concepts
- Developing new tests
- Quick validation
- Debugging issues

---

#### 2. **CI/CD Pipeline (Best for Automation)**

**Jenkins Example:**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup Databases') {
            steps {
                sh '''
                    # Start MongoDB container
                    docker run -d --name mongo-test -p 27017:27017 mongo:latest
                    
                    # Start MySQL container
                    docker run -d --name mysql-test \
                        -e MYSQL_ROOT_PASSWORD=testpass \
                        -e MYSQL_DATABASE=test_db \
                        -p 3306:3306 mysql:8.0
                    
                    # Wait for databases to be ready
                    sleep 10
                '''
            }
        }
        
        stage('Run Database Tests') {
            steps {
                sh '''
                    cd automation-testing/database-tests
                    pip install -r requirements.txt
                    pytest test_mongodb_queries.py -v --html=report_mongo.html
                    pytest test_mysql_queries.py -v --html=report_mysql.html
                '''
            }
        }
        
        stage('Cleanup') {
            steps {
                sh '''
                    docker stop mongo-test mysql-test
                    docker rm mongo-test mysql-test
                '''
            }
        }
    }
}
```

**Pros:**
- ✅ Automated on every commit
- ✅ Consistent environment
- ✅ Team-wide visibility
- ✅ Isolated containers

**When to use:**
- Before merging code
- Scheduled nightly tests
- Release validation
- Continuous integration

---

#### 3. **Docker Containers (Best for Isolation)**

**Setup:**
```bash
# Create docker-compose.yml
cd /home/rk/Documents/labs/lab-automation-testing/automation-testing/database-tests

# Start databases
docker-compose up -d

# Run tests
pytest test_mongodb_queries.py -v
pytest test_mysql_queries.py -v

# Cleanup
docker-compose down -v
```

**Pros:**
- ✅ Completely isolated
- ✅ No local installation needed
- ✅ Easy cleanup (just remove containers)
- ✅ Reproducible environment

**When to use:**
- Don't want to install databases locally
- Need exact version control
- Testing different database versions
- Team collaboration

---

#### 4. **Dedicated Test Server**

**Setup:**
```bash
# SSH to test server
ssh test-server

# Run tests
cd /path/to/tests
pytest test_mongodb_queries.py -v
```

**Pros:**
- ✅ Shared resource
- ✅ More powerful hardware
- ✅ Always available
- ✅ Centralized logs

**When to use:**
- Team needs shared environment
- Load/performance testing
- Integration with other services
- Production-like setup

---

### ❌ Where NOT to Run

| Environment | Why NOT |
|-------------|---------|
| **Production Database** | ❌ Tests DROP tables - will delete real data! |
| **Staging with Real Data** | ❌ Cleanup will remove important test data |
| **Shared Dev Database** | ❌ Will interfere with other developers |

---

## 🎯 Recommended Setup by Use Case

### For Learning & Development
```
Local Machine
├── MongoDB (local install or Docker)
├── MySQL (local install or Docker)
└── Run: pytest test_*.py -v
```

### For Team Collaboration
```
Docker Compose
├── MongoDB container
├── MySQL container
├── Test runner container
└── Run: docker-compose up --abort-on-container-exit
```

### For CI/CD
```
Jenkins/GitHub Actions
├── Spin up database containers
├── Run tests
├── Generate reports
└── Cleanup containers
```

---

## 🐳 Docker Setup (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: test-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: test_db
    volumes:
      - mongo-data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  mysql:
    image: mysql:8.0
    container_name: test-mysql
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: testpassword
      MYSQL_DATABASE: test_db
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mongo-data:
  mysql-data:
```

**Usage:**
```bash
# Start databases
docker-compose up -d

# Wait for health checks
docker-compose ps

# Update test configs to use localhost
# Run tests
pytest test_mongodb_queries.py -v
pytest test_mysql_queries.py -v

# Stop and remove everything
docker-compose down -v  # -v removes volumes too
```

---

## 🔄 Test Lifecycle Explained

### Single Test Execution

```
1. Test Starts
   ↓
2. Fixture Setup (create tables/collections)
   ↓
3. Insert Test Data
   ↓
4. Run Test Logic
   ↓
5. Assertions/Validations
   ↓
6. ✅ Test Passes/Fails
   ↓
7. 🔄 Fixture Cleanup (drop tables/collections)
   ↓
8. Test Ends
```

### Multiple Tests Execution

```
Test 1: Insert → Validate → ✅ Pass → 🔄 Cleanup
Test 2: Insert → Validate → ✅ Pass → 🔄 Cleanup
Test 3: Insert → Validate → ❌ Fail → 🔄 Cleanup (still runs!)
Test 4: Insert → Validate → ✅ Pass → 🔄 Cleanup
```

**Key Point:** Cleanup happens **even if test fails**!

---

## 💡 Best Practices

### 1. **Use Separate Test Database**
```python
# ✅ GOOD
MONGO_CONFIG = {"database": "test_db"}

# ❌ BAD
MONGO_CONFIG = {"database": "production_db"}  # NEVER!
```

### 2. **Run Tests in Isolation**
```bash
# ✅ GOOD - Each test is independent
pytest test_mongodb_queries.py -v

# ⚠️ AVOID - Running against shared database
pytest test_mongodb_queries.py --reuse-db
```

### 3. **Use Docker for Consistency**
```bash
# ✅ GOOD - Same environment everywhere
docker-compose up -d
pytest test_*.py -v
docker-compose down -v

# ⚠️ OK but less consistent - Local installs vary
pytest test_*.py -v
```

### 4. **Verify Cleanup**
```bash
# After tests, check database is clean
mongo test_db --eval "db.getCollectionNames()"  # Should be empty
mysql -e "SHOW TABLES FROM test_db;"            # Should be empty
```

---

## 🎓 Summary

### ✅ What You Should Know

1. **Tests are SAFE** - They only touch `test_db`
2. **Cleanup is AUTOMATIC** - No manual intervention needed
3. **Each test is ISOLATED** - Fresh start every time
4. **Production is PROTECTED** - Different database name

### 📍 Where to Run

| Environment | Best For | Setup Effort |
|-------------|----------|--------------|
| **Local Machine** | Learning, debugging | Low |
| **Docker** | Consistency, isolation | Medium |
| **CI/CD** | Automation, team | High |
| **Test Server** | Shared resource | Medium |

### 🚀 Quick Start

```bash
# 1. Start databases (Docker recommended)
docker-compose up -d

# 2. Update configs
# Edit test_mongodb_queries.py and test_mysql_queries.py

# 3. Run tests
pytest test_mongodb_queries.py -v
pytest test_mysql_queries.py -v

# 4. Cleanup
docker-compose down -v
```

**Remember:** Tests clean up automatically, but the database (`test_db`) remains for reuse!
