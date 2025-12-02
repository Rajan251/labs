"""
MongoDB Query Testing Script
============================

This script tests MongoDB queries including CRUD operations, aggregations,
indexing, and performance testing.

Requirements:
- pymongo
- pytest
- pytest-asyncio (for async tests)
- motor (for async MongoDB operations)

Installation:
    pip install pymongo pytest pytest-asyncio motor

Setup:
1. Install MongoDB locally or use MongoDB Atlas (cloud)
2. Update the connection string in the script
3. Run tests: pytest test_mongodb_queries.py -v
"""

import pytest
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any


# ============================================================================
# CONFIGURATION
# ============================================================================

# MongoDB Connection Configuration
MONGO_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "test_db",
    "username": None,  # Set if authentication is enabled
    "password": None,  # Set if authentication is enabled
}

# Connection string format:
# mongodb://username:password@host:port/database
# For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/database


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def mongo_client():
    """Create MongoDB client for the entire test session."""
    if MONGO_CONFIG["username"] and MONGO_CONFIG["password"]:
        connection_string = (
            f"mongodb://{MONGO_CONFIG['username']}:{MONGO_CONFIG['password']}"
            f"@{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}/{MONGO_CONFIG['database']}"
        )
    else:
        connection_string = f"mongodb://{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"
    
    try:
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print(f"\n✓ Connected to MongoDB at {MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}")
        yield client
    except ConnectionFailure as e:
        pytest.fail(f"Failed to connect to MongoDB: {e}")
    finally:
        client.close()
        print("\n✓ MongoDB connection closed")


@pytest.fixture(scope="function")
def test_db(mongo_client):
    """Get test database and clean up after each test."""
    db = mongo_client[MONGO_CONFIG["database"]]
    yield db
    # Cleanup: Drop all collections after each test
    for collection_name in db.list_collection_names():
        db[collection_name].drop()


@pytest.fixture(scope="function")
def users_collection(test_db):
    """Create and return users collection."""
    collection = test_db["users"]
    # Create indexes
    collection.create_index("email", unique=True)
    collection.create_index("username")
    collection.create_index([("created_at", DESCENDING)])
    return collection


@pytest.fixture(scope="function")
def sample_users() -> List[Dict[str, Any]]:
    """Generate sample user data."""
    return [
        {
            "username": "john_doe",
            "email": "john@example.com",
            "age": 30,
            "status": "active",
            "tags": ["developer", "python"],
            "created_at": datetime.utcnow(),
            "profile": {
                "bio": "Software Developer",
                "location": "New York"
            }
        },
        {
            "username": "jane_smith",
            "email": "jane@example.com",
            "age": 25,
            "status": "active",
            "tags": ["designer", "ui/ux"],
            "created_at": datetime.utcnow() - timedelta(days=1),
            "profile": {
                "bio": "UI/UX Designer",
                "location": "San Francisco"
            }
        },
        {
            "username": "bob_wilson",
            "email": "bob@example.com",
            "age": 35,
            "status": "inactive",
            "tags": ["manager", "agile"],
            "created_at": datetime.utcnow() - timedelta(days=2),
            "profile": {
                "bio": "Project Manager",
                "location": "Boston"
            }
        }
    ]


# ============================================================================
# CREATE (INSERT) TESTS
# ============================================================================

class TestMongoDBInsert:
    """Test MongoDB insert operations."""
    
    def test_insert_one_document(self, users_collection):
        """Test inserting a single document."""
        user = {
            "username": "test_user",
            "email": "test@example.com",
            "age": 28
        }
        
        result = users_collection.insert_one(user)
        
        assert result.inserted_id is not None
        assert result.acknowledged is True
        
        # Verify insertion
        found_user = users_collection.find_one({"_id": result.inserted_id})
        assert found_user["username"] == "test_user"
        assert found_user["email"] == "test@example.com"
    
    def test_insert_many_documents(self, users_collection, sample_users):
        """Test inserting multiple documents."""
        result = users_collection.insert_many(sample_users)
        
        assert len(result.inserted_ids) == 3
        assert result.acknowledged is True
        
        # Verify count
        count = users_collection.count_documents({})
        assert count == 3
    
    def test_insert_duplicate_unique_field(self, users_collection):
        """Test that duplicate unique field raises error."""
        user1 = {"username": "user1", "email": "duplicate@example.com"}
        user2 = {"username": "user2", "email": "duplicate@example.com"}
        
        users_collection.insert_one(user1)
        
        with pytest.raises(DuplicateKeyError):
            users_collection.insert_one(user2)


# ============================================================================
# READ (FIND) TESTS
# ============================================================================

class TestMongoDBFind:
    """Test MongoDB find operations."""
    
    def test_find_all_documents(self, users_collection, sample_users):
        """Test finding all documents."""
        users_collection.insert_many(sample_users)
        
        all_users = list(users_collection.find())
        
        assert len(all_users) == 3
    
    def test_find_with_filter(self, users_collection, sample_users):
        """Test finding documents with filter."""
        users_collection.insert_many(sample_users)
        
        active_users = list(users_collection.find({"status": "active"}))
        
        assert len(active_users) == 2
        for user in active_users:
            assert user["status"] == "active"
    
    def test_find_with_projection(self, users_collection, sample_users):
        """Test finding documents with field projection."""
        users_collection.insert_many(sample_users)
        
        users = list(users_collection.find(
            {},
            {"username": 1, "email": 1, "_id": 0}
        ))
        
        assert len(users) == 3
        for user in users:
            assert "username" in user
            assert "email" in user
            assert "_id" not in user
            assert "age" not in user
    
    def test_find_with_comparison_operators(self, users_collection, sample_users):
        """Test finding with comparison operators ($gt, $lt, $gte, $lte)."""
        users_collection.insert_many(sample_users)
        
        # Find users older than 28
        older_users = list(users_collection.find({"age": {"$gt": 28}}))
        assert len(older_users) == 2
        
        # Find users age between 25 and 32
        age_range_users = list(users_collection.find({
            "age": {"$gte": 25, "$lte": 32}
        }))
        assert len(age_range_users) == 2
    
    def test_find_with_logical_operators(self, users_collection, sample_users):
        """Test finding with logical operators ($and, $or, $not)."""
        users_collection.insert_many(sample_users)
        
        # Find active users older than 28
        result = list(users_collection.find({
            "$and": [
                {"status": "active"},
                {"age": {"$gt": 28}}
            ]
        }))
        assert len(result) == 1
        
        # Find users who are either inactive OR older than 32
        result = list(users_collection.find({
            "$or": [
                {"status": "inactive"},
                {"age": {"$gt": 32}}
            ]
        }))
        assert len(result) == 2
    
    def test_find_with_array_operators(self, users_collection, sample_users):
        """Test finding with array operators ($in, $all)."""
        users_collection.insert_many(sample_users)
        
        # Find users with specific tags
        developers = list(users_collection.find({
            "tags": {"$in": ["developer", "designer"]}
        }))
        assert len(developers) == 2
    
    def test_find_nested_fields(self, users_collection, sample_users):
        """Test querying nested document fields."""
        users_collection.insert_many(sample_users)
        
        # Find users in New York
        ny_users = list(users_collection.find({
            "profile.location": "New York"
        }))
        assert len(ny_users) == 1
        assert ny_users[0]["username"] == "john_doe"
    
    def test_find_with_sorting(self, users_collection, sample_users):
        """Test finding with sorting."""
        users_collection.insert_many(sample_users)
        
        # Sort by age descending
        sorted_users = list(users_collection.find().sort("age", DESCENDING))
        
        assert sorted_users[0]["age"] == 35
        assert sorted_users[1]["age"] == 30
        assert sorted_users[2]["age"] == 25
    
    def test_find_with_limit_and_skip(self, users_collection, sample_users):
        """Test pagination with limit and skip."""
        users_collection.insert_many(sample_users)
        
        # Get first 2 users
        page1 = list(users_collection.find().limit(2))
        assert len(page1) == 2
        
        # Get next user (skip first 2)
        page2 = list(users_collection.find().skip(2).limit(2))
        assert len(page2) == 1


# ============================================================================
# UPDATE TESTS
# ============================================================================

class TestMongoDBUpdate:
    """Test MongoDB update operations."""
    
    def test_update_one_document(self, users_collection, sample_users):
        """Test updating a single document."""
        users_collection.insert_many(sample_users)
        
        result = users_collection.update_one(
            {"username": "john_doe"},
            {"$set": {"age": 31, "status": "premium"}}
        )
        
        assert result.matched_count == 1
        assert result.modified_count == 1
        
        # Verify update
        updated_user = users_collection.find_one({"username": "john_doe"})
        assert updated_user["age"] == 31
        assert updated_user["status"] == "premium"
    
    def test_update_many_documents(self, users_collection, sample_users):
        """Test updating multiple documents."""
        users_collection.insert_many(sample_users)
        
        result = users_collection.update_many(
            {"status": "active"},
            {"$set": {"verified": True}}
        )
        
        assert result.matched_count == 2
        assert result.modified_count == 2
        
        # Verify updates
        verified_users = list(users_collection.find({"verified": True}))
        assert len(verified_users) == 2
    
    def test_update_with_increment(self, users_collection, sample_users):
        """Test updating with $inc operator."""
        users_collection.insert_many(sample_users)
        
        result = users_collection.update_one(
            {"username": "john_doe"},
            {"$inc": {"age": 1}}
        )
        
        assert result.modified_count == 1
        
        user = users_collection.find_one({"username": "john_doe"})
        assert user["age"] == 31  # Was 30, incremented by 1
    
    def test_update_array_push(self, users_collection, sample_users):
        """Test adding to array with $push."""
        users_collection.insert_many(sample_users)
        
        result = users_collection.update_one(
            {"username": "john_doe"},
            {"$push": {"tags": "senior"}}
        )
        
        assert result.modified_count == 1
        
        user = users_collection.find_one({"username": "john_doe"})
        assert "senior" in user["tags"]
    
    def test_update_array_pull(self, users_collection, sample_users):
        """Test removing from array with $pull."""
        users_collection.insert_many(sample_users)
        
        result = users_collection.update_one(
            {"username": "john_doe"},
            {"$pull": {"tags": "python"}}
        )
        
        assert result.modified_count == 1
        
        user = users_collection.find_one({"username": "john_doe"})
        assert "python" not in user["tags"]
    
    def test_upsert_operation(self, users_collection):
        """Test upsert (update or insert)."""
        result = users_collection.update_one(
            {"username": "new_user"},
            {"$set": {"email": "new@example.com", "age": 22}},
            upsert=True
        )
        
        assert result.upserted_id is not None
        
        # Verify insertion
        user = users_collection.find_one({"username": "new_user"})
        assert user is not None
        assert user["email"] == "new@example.com"


# ============================================================================
# DELETE TESTS
# ============================================================================

class TestMongoDBDelete:
    """Test MongoDB delete operations."""
    
    def test_delete_one_document(self, users_collection, sample_users):
        """Test deleting a single document."""
        users_collection.insert_many(sample_users)
        
        result = users_collection.delete_one({"username": "john_doe"})
        
        assert result.deleted_count == 1
        
        # Verify deletion
        user = users_collection.find_one({"username": "john_doe"})
        assert user is None
    
    def test_delete_many_documents(self, users_collection, sample_users):
        """Test deleting multiple documents."""
        users_collection.insert_many(sample_users)
        
        result = users_collection.delete_many({"status": "active"})
        
        assert result.deleted_count == 2
        
        # Verify remaining count
        remaining = users_collection.count_documents({})
        assert remaining == 1


# ============================================================================
# AGGREGATION TESTS
# ============================================================================

class TestMongoDBAggregate:
    """Test MongoDB aggregation pipeline."""
    
    def test_aggregate_count_by_status(self, users_collection, sample_users):
        """Test counting documents by status."""
        users_collection.insert_many(sample_users)
        
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        result = list(users_collection.aggregate(pipeline))
        
        status_counts = {item["_id"]: item["count"] for item in result}
        assert status_counts["active"] == 2
        assert status_counts["inactive"] == 1
    
    def test_aggregate_average_age(self, users_collection, sample_users):
        """Test calculating average age."""
        users_collection.insert_many(sample_users)
        
        pipeline = [
            {"$group": {
                "_id": None,
                "avg_age": {"$avg": "$age"}
            }}
        ]
        
        result = list(users_collection.aggregate(pipeline))
        
        assert result[0]["avg_age"] == 30  # (30 + 25 + 35) / 3
    
    def test_aggregate_with_match_and_project(self, users_collection, sample_users):
        """Test aggregation with $match and $project."""
        users_collection.insert_many(sample_users)
        
        pipeline = [
            {"$match": {"status": "active"}},
            {"$project": {
                "username": 1,
                "email": 1,
                "age": 1,
                "_id": 0
            }}
        ]
        
        result = list(users_collection.aggregate(pipeline))
        
        assert len(result) == 2
        for user in result:
            assert "_id" not in user
            assert "username" in user


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestMongoDBPerformance:
    """Test MongoDB query performance."""
    
    def test_query_performance_with_index(self, test_db):
        """Test query performance with and without index."""
        collection = test_db["performance_test"]
        
        # Insert 10000 documents
        docs = [{"value": i, "data": f"data_{i}"} for i in range(10000)]
        collection.insert_many(docs)
        
        # Query without index
        start = time.time()
        result = list(collection.find({"value": 5000}))
        time_without_index = time.time() - start
        
        # Create index
        collection.create_index("value")
        
        # Query with index
        start = time.time()
        result = list(collection.find({"value": 5000}))
        time_with_index = time.time() - start
        
        print(f"\nQuery time without index: {time_without_index:.4f}s")
        print(f"Query time with index: {time_with_index:.4f}s")
        
        # Index should improve performance
        assert time_with_index < time_without_index
    
    def test_bulk_insert_performance(self, test_db):
        """Test bulk insert performance."""
        collection = test_db["bulk_test"]
        
        docs = [{"value": i} for i in range(1000)]
        
        start = time.time()
        collection.insert_many(docs)
        bulk_time = time.time() - start
        
        print(f"\nBulk insert of 1000 docs: {bulk_time:.4f}s")
        
        assert bulk_time < 1.0  # Should complete in less than 1 second


# ============================================================================
# TRANSACTION TESTS (Requires Replica Set)
# ============================================================================

class TestMongoDBTransactions:
    """Test MongoDB transactions (requires replica set)."""
    
    @pytest.mark.skip(reason="Requires MongoDB replica set configuration")
    def test_transaction_commit(self, mongo_client, test_db):
        """Test successful transaction commit."""
        collection = test_db["transactions_test"]
        
        with mongo_client.start_session() as session:
            with session.start_transaction():
                collection.insert_one({"value": 1}, session=session)
                collection.insert_one({"value": 2}, session=session)
        
        # Verify both documents were inserted
        assert collection.count_documents({}) == 2
    
    @pytest.mark.skip(reason="Requires MongoDB replica set configuration")
    def test_transaction_rollback(self, mongo_client, test_db):
        """Test transaction rollback on error."""
        collection = test_db["transactions_test"]
        
        try:
            with mongo_client.start_session() as session:
                with session.start_transaction():
                    collection.insert_one({"value": 1}, session=session)
                    raise Exception("Simulated error")
                    collection.insert_one({"value": 2}, session=session)
        except Exception:
            pass
        
        # Verify no documents were inserted
        assert collection.count_documents({}) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
