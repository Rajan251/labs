#!/bin/bash

# ============================================
# MongoDB Replica Set - Complete Test Suite
# ============================================
# This script tests all aspects of your MongoDB replica set
# Run this AFTER completing the setup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONGO_URI="mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"
APP_URI="mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}MongoDB Replica Set - Test Suite${NC}"
echo -e "${BLUE}============================================${NC}\n"

# Test 1: Check if all MongoDB servers are running
echo -e "${YELLOW}Test 1: Checking MongoDB services...${NC}"
for server in mongo-1 mongo-2 mongo-3; do
    if ssh root@$server "systemctl is-active mongod" &>/dev/null; then
        echo -e "  ${GREEN}✅ $server: MongoDB is running${NC}"
    else
        echo -e "  ${RED}❌ $server: MongoDB is NOT running${NC}"
        exit 1
    fi
done
echo ""

# Test 2: Check replica set status
echo -e "${YELLOW}Test 2: Checking replica set status...${NC}"
STATUS=$(mongosh "$MONGO_URI" --quiet --eval "
    var status = rs.status();
    var primary = status.members.filter(m => m.stateStr === 'PRIMARY').length;
    var secondary = status.members.filter(m => m.stateStr === 'SECONDARY').length;
    var healthy = status.members.filter(m => m.health === 1).length;
    print(JSON.stringify({primary: primary, secondary: secondary, healthy: healthy}));
")

PRIMARY_COUNT=$(echo $STATUS | jq -r '.primary')
SECONDARY_COUNT=$(echo $STATUS | jq -r '.secondary')
HEALTHY_COUNT=$(echo $STATUS | jq -r '.healthy')

if [ "$PRIMARY_COUNT" -eq 1 ] && [ "$SECONDARY_COUNT" -eq 2 ] && [ "$HEALTHY_COUNT" -eq 3 ]; then
    echo -e "  ${GREEN}✅ Replica set status: 1 PRIMARY, 2 SECONDARYs, all healthy${NC}"
else
    echo -e "  ${RED}❌ Replica set status: PRIMARY=$PRIMARY_COUNT, SECONDARY=$SECONDARY_COUNT, HEALTHY=$HEALTHY_COUNT${NC}"
    exit 1
fi
echo ""

# Test 3: Check replication lag
echo -e "${YELLOW}Test 3: Checking replication lag...${NC}"
LAG=$(mongosh "$MONGO_URI" --quiet --eval "
    var status = rs.status();
    var primary = status.members.find(m => m.stateStr === 'PRIMARY');
    var maxLag = 0;
    status.members.forEach(function(m) {
        if (m.stateStr === 'SECONDARY') {
            var lag = (primary.optimeDate - m.optimeDate) / 1000;
            if (lag > maxLag) maxLag = lag;
        }
    });
    print(maxLag);
")

if (( $(echo "$LAG < 10" | bc -l) )); then
    echo -e "  ${GREEN}✅ Replication lag: ${LAG} seconds (< 10s threshold)${NC}"
else
    echo -e "  ${RED}❌ Replication lag: ${LAG} seconds (> 10s threshold)${NC}"
    exit 1
fi
echo ""

# Test 4: Test write with majority concern
echo -e "${YELLOW}Test 4: Testing write with majority concern...${NC}"
WRITE_RESULT=$(mongosh "$APP_URI" --quiet --eval "
    db.test_suite.insertOne(
        { test: 'write_concern_test', timestamp: new Date() },
        { writeConcern: { w: 'majority', wtimeout: 5000 } }
    );
    print('SUCCESS');
" 2>&1)

if echo "$WRITE_RESULT" | grep -q "SUCCESS"; then
    echo -e "  ${GREEN}✅ Write with majority concern: SUCCESS${NC}"
else
    echo -e "  ${RED}❌ Write with majority concern: FAILED${NC}"
    echo "$WRITE_RESULT"
    exit 1
fi
echo ""

# Test 5: Verify replication to secondaries
echo -e "${YELLOW}Test 5: Verifying replication to secondaries...${NC}"
sleep 2  # Wait for replication

REPLICATED=$(mongosh "mongodb://admin:AdminSecurePassword123!@mongo-2:27017/mydb?authSource=admin" --quiet --eval "
    rs.secondaryOk();
    var count = db.test_suite.countDocuments({ test: 'write_concern_test' });
    print(count);
")

if [ "$REPLICATED" -gt 0 ]; then
    echo -e "  ${GREEN}✅ Data replicated to SECONDARY-1 (mongo-2)${NC}"
else
    echo -e "  ${RED}❌ Data NOT replicated to SECONDARY-1${NC}"
    exit 1
fi
echo ""

# Test 6: Test connection pool
echo -e "${YELLOW}Test 6: Checking connection pool...${NC}"
CONNECTIONS=$(mongosh "$MONGO_URI" --quiet --eval "
    var stats = db.serverStatus().connections;
    print(JSON.stringify(stats));
")

CURRENT=$(echo $CONNECTIONS | jq -r '.current')
AVAILABLE=$(echo $CONNECTIONS | jq -r '.available')

echo -e "  ${GREEN}✅ Connection pool: $CURRENT current, $AVAILABLE available${NC}"
echo ""

# Test 7: Test failover (optional - requires manual intervention)
echo -e "${YELLOW}Test 7: Failover test (manual)...${NC}"
echo -e "  ${BLUE}ℹ️  To test failover manually, run:${NC}"
echo -e "  ${BLUE}   mongosh \"$MONGO_URI\" --eval \"rs.stepDown(60)\"${NC}"
echo -e "  ${BLUE}   Then check rs.status() to see new PRIMARY${NC}"
echo ""

# Test 8: Performance benchmark
echo -e "${YELLOW}Test 8: Performance benchmark (1000 writes)...${NC}"
START_TIME=$(date +%s)
mongosh "$APP_URI" --quiet --eval "
    for (var i = 0; i < 1000; i++) {
        db.benchmark.insertOne(
            { index: i, data: 'x'.repeat(100), timestamp: new Date() },
            { writeConcern: { w: 'majority' } }
        );
    }
" &>/dev/null
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
WRITES_PER_SEC=$((1000 / DURATION))

echo -e "  ${GREEN}✅ Performance: $WRITES_PER_SEC writes/second${NC}"
echo ""

# Test 9: Verify oplog size
echo -e "${YELLOW}Test 9: Checking oplog size...${NC}"
OPLOG_INFO=$(mongosh "$MONGO_URI" --quiet --eval "
    var stats = db.getSiblingDB('local').oplog.rs.stats();
    var sizeGB = (stats.maxSize / 1024 / 1024 / 1024).toFixed(2);
    print(sizeGB);
")

echo -e "  ${GREEN}✅ Oplog size: ${OPLOG_INFO} GB${NC}"
echo ""

# Test 10: Verify authentication
echo -e "${YELLOW}Test 10: Verifying authentication...${NC}"
AUTH_TEST=$(mongosh "$APP_URI" --quiet --eval "
    var status = db.runCommand({ connectionStatus: 1 });
    print(status.authInfo.authenticatedUsers.length > 0 ? 'AUTHENTICATED' : 'NOT_AUTHENTICATED');
")

if [ "$AUTH_TEST" = "AUTHENTICATED" ]; then
    echo -e "  ${GREEN}✅ Authentication: Working${NC}"
else
    echo -e "  ${RED}❌ Authentication: Failed${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ All tests passed successfully!${NC}"
echo -e "${BLUE}============================================${NC}\n"

echo -e "${BLUE}Replica Set Summary:${NC}"
mongosh "$MONGO_URI" --quiet --eval "
    var status = rs.status();
    status.members.forEach(function(m) {
        print('  ' + m.name + ': ' + m.stateStr + ' (health: ' + m.health + ')');
    });
"

echo -e "\n${BLUE}Connection String for Applications:${NC}"
echo -e "${GREEN}$APP_URI${NC}\n"

echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Deploy your application with the connection string above"
echo -e "  2. Set up monitoring (Prometheus + Grafana)"
echo -e "  3. Configure automated backups"
echo -e "  4. Test failover manually"
echo -e "  5. Load test with production-like traffic\n"
