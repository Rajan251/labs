#!/bin/bash
# ============================================================================
# RUN ALL TESTS SCRIPT
# Usage: ./scripts/run-tests.sh [options]
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="test"
COVERAGE_THRESHOLD=80
RUN_LOAD_TESTS=false
PARALLEL=false
MARKERS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --coverage)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --load-tests)
            RUN_LOAD_TESTS=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --markers)
            MARKERS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --env ENV              Environment (default: test)"
            echo "  --coverage NUM         Coverage threshold (default: 80)"
            echo "  --load-tests           Run load tests"
            echo "  --parallel             Run tests in parallel"
            echo "  --markers MARKERS      Pytest markers (e.g., 'unit', 'not slow')"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Running Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Set environment variables
export ENVIRONMENT=$ENVIRONMENT
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Build pytest command
PYTEST_CMD="pytest"

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

PYTEST_CMD="$PYTEST_CMD -v --cov=app --cov-report=xml --cov-report=html --cov-report=term-missing --cov-fail-under=$COVERAGE_THRESHOLD"

# Run unit tests
echo -e "${YELLOW}Running unit tests...${NC}"
eval "$PYTEST_CMD -m unit --junitxml=junit-unit.xml --html=report-unit.html --self-contained-html" || {
    echo -e "${RED}Unit tests failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓ Unit tests passed${NC}"
echo ""

# Run integration tests
echo -e "${YELLOW}Running integration tests...${NC}"
eval "$PYTEST_CMD -m integration --junitxml=junit-integration.xml --html=report-integration.html --self-contained-html" || {
    echo -e "${RED}Integration tests failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓ Integration tests passed${NC}"
echo ""

# Run E2E tests
echo -e "${YELLOW}Running E2E tests...${NC}"
eval "$PYTEST_CMD -m e2e --junitxml=junit-e2e.xml --html=report-e2e.html --self-contained-html" || {
    echo -e "${RED}E2E tests failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓ E2E tests passed${NC}"
echo ""

# Run load tests (optional)
if [ "$RUN_LOAD_TESTS" = true ]; then
    echo -e "${YELLOW}Running load tests...${NC}"
    
    # Start application
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    APP_PID=$!
    sleep 5
    
    # Run Locust
    locust -f tests/performance/load_tests.py \
        --host=http://localhost:8000 \
        --headless \
        --users 100 \
        --spawn-rate 10 \
        --run-time 5m \
        --html=locust-report.html \
        --csv=locust-stats || {
        kill $APP_PID
        echo -e "${RED}Load tests failed!${NC}"
        exit 1
    }
    
    # Stop application
    kill $APP_PID
    echo -e "${GREEN}✓ Load tests passed${NC}"
    echo ""
fi

# Generate coverage report
echo -e "${YELLOW}Generating coverage report...${NC}"
coverage report
echo ""

# Check coverage threshold
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
    echo -e "${RED}Coverage ($COVERAGE%) is below threshold ($COVERAGE_THRESHOLD%)${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All tests passed! ✓${NC}"
echo -e "${GREEN}Coverage: $COVERAGE%${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Reports generated:"
echo "  - HTML Coverage: htmlcov/index.html"
echo "  - Unit Tests: report-unit.html"
echo "  - Integration Tests: report-integration.html"
echo "  - E2E Tests: report-e2e.html"
if [ "$RUN_LOAD_TESTS" = true ]; then
    echo "  - Load Tests: locust-report.html"
fi
