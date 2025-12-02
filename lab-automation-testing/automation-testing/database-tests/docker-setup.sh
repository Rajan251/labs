#!/bin/bash

# Docker Database Setup Script
# This script helps you set up and manage test databases using Docker

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

echo "=========================================="
echo "Database Testing - Docker Setup"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "Docker and Docker Compose are installed"
echo ""

# Menu
echo "What would you like to do?"
echo "1) Start databases"
echo "2) Stop databases"
echo "3) Restart databases"
echo "4) View database status"
echo "5) View logs"
echo "6) Clean up (remove containers and volumes)"
echo "7) Run tests"
echo ""
read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        print_info "Starting databases..."
        docker-compose up -d
        echo ""
        print_info "Waiting for databases to be ready..."
        sleep 10
        
        # Check health
        if docker-compose ps | grep -q "healthy"; then
            print_success "Databases are running and healthy!"
        else
            print_warning "Databases are starting... (may take a few more seconds)"
        fi
        
        echo ""
        print_info "Connection details:"
        echo "  MongoDB: localhost:27017 (database: test_db)"
        echo "  MySQL:   localhost:3306 (database: test_db, user: root, password: testpassword)"
        echo ""
        print_info "Update your test configs:"
        echo "  - test_mongodb_queries.py: host='localhost', port=27017"
        echo "  - test_mysql_queries.py: host='localhost', user='root', password='testpassword'"
        ;;
    
    2)
        print_info "Stopping databases..."
        docker-compose stop
        print_success "Databases stopped"
        ;;
    
    3)
        print_info "Restarting databases..."
        docker-compose restart
        sleep 5
        print_success "Databases restarted"
        ;;
    
    4)
        print_info "Database status:"
        docker-compose ps
        ;;
    
    5)
        echo "Which logs do you want to see?"
        echo "1) MongoDB"
        echo "2) MySQL"
        echo "3) Both"
        read -p "Enter choice (1-3): " log_choice
        
        case $log_choice in
            1) docker-compose logs -f mongodb ;;
            2) docker-compose logs -f mysql ;;
            3) docker-compose logs -f ;;
            *) print_error "Invalid choice" ;;
        esac
        ;;
    
    6)
        print_warning "This will remove all containers and data volumes!"
        read -p "Are you sure? (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            print_info "Cleaning up..."
            docker-compose down -v
            print_success "Cleanup complete"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
    
    7)
        print_info "Running tests..."
        echo ""
        
        # Check if databases are running
        if ! docker-compose ps | grep -q "Up"; then
            print_warning "Databases are not running. Starting them..."
            docker-compose up -d
            sleep 10
        fi
        
        # Install dependencies
        print_info "Installing Python dependencies..."
        pip install -r requirements.txt > /dev/null 2>&1
        print_success "Dependencies installed"
        echo ""
        
        # Run MongoDB tests
        print_info "Running MongoDB tests..."
        if pytest test_mongodb_queries.py -v --tb=short; then
            print_success "MongoDB tests passed!"
        else
            print_error "MongoDB tests failed"
        fi
        echo ""
        
        # Run MySQL tests
        print_info "Running MySQL tests..."
        if pytest test_mysql_queries.py -v --tb=short; then
            print_success "MySQL tests passed!"
        else
            print_error "MySQL tests failed"
        fi
        ;;
    
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
