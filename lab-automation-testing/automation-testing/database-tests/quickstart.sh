#!/bin/bash

# Database Testing Quick Start Script
# This script helps you set up and run database tests

set -e  # Exit on error

echo "=========================================="
echo "Database Testing Quick Start"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Install Python dependencies
echo "Step 1: Installing Python dependencies..."
if pip install -r requirements.txt; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi
echo ""

# Step 2: Check MongoDB connection
echo "Step 2: Checking MongoDB connection..."
if python3 -c "import pymongo; client = pymongo.MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000); client.admin.command('ping')" 2>/dev/null; then
    print_success "MongoDB is running and accessible"
    MONGO_AVAILABLE=true
else
    print_warning "MongoDB is not accessible at localhost:27017"
    print_warning "You can:"
    echo "  - Install MongoDB: sudo apt-get install mongodb (Ubuntu) or brew install mongodb-community (macOS)"
    echo "  - Start MongoDB: sudo systemctl start mongodb (Linux) or brew services start mongodb-community (macOS)"
    echo "  - Use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas"
    MONGO_AVAILABLE=false
fi
echo ""

# Step 3: Check MySQL connection
echo "Step 3: Checking MySQL connection..."
if python3 -c "import mysql.connector; mysql.connector.connect(host='localhost', user='root', password='', connect_timeout=2)" 2>/dev/null; then
    print_success "MySQL is running and accessible"
    MYSQL_AVAILABLE=true
else
    print_warning "MySQL is not accessible at localhost:3306"
    print_warning "You need to:"
    echo "  - Install MySQL: sudo apt-get install mysql-server (Ubuntu) or brew install mysql (macOS)"
    echo "  - Start MySQL: sudo systemctl start mysql (Linux) or brew services start mysql (macOS)"
    echo "  - Update MYSQL_CONFIG in test_mysql_queries.py with correct credentials"
    MYSQL_AVAILABLE=false
fi
echo ""

# Step 4: Run tests
echo "Step 4: Running tests..."
echo ""

if [ "$MONGO_AVAILABLE" = true ]; then
    echo "Running MongoDB tests..."
    if pytest test_mongodb_queries.py -v --tb=short; then
        print_success "MongoDB tests passed"
    else
        print_error "MongoDB tests failed"
    fi
    echo ""
else
    print_warning "Skipping MongoDB tests (MongoDB not available)"
    echo ""
fi

if [ "$MYSQL_AVAILABLE" = true ]; then
    echo "Running MySQL tests..."
    if pytest test_mysql_queries.py -v --tb=short; then
        print_success "MySQL tests passed"
    else
        print_error "MySQL tests failed - Check MYSQL_CONFIG in test_mysql_queries.py"
    fi
    echo ""
else
    print_warning "Skipping MySQL tests (MySQL not available)"
    echo ""
fi

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "MongoDB: $([ "$MONGO_AVAILABLE" = true ] && echo -e "${GREEN}Available${NC}" || echo -e "${YELLOW}Not Available${NC}")"
echo "MySQL:   $([ "$MYSQL_AVAILABLE" = true ] && echo -e "${GREEN}Available${NC}" || echo -e "${YELLOW}Not Available${NC}")"
echo ""
echo "For detailed setup instructions, see README.md"
echo ""
