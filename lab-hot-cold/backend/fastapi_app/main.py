import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_separation.router import QueryRouter
from data_separation.config import HOT_DB_CONFIG, COLD_DB_CONFIG
from monitoring.data_metrics import DataMetrics

app = FastAPI(title="Hot-Cold Data Separation API")

# Global instances
query_router: QueryRouter = None
metrics_tracker: DataMetrics = None

@app.on_event("startup")
async def startup_db_client():
    """Initialize database connections and query router"""
    global query_router, metrics_tracker
    
    # Initialize query router
    query_router = QueryRouter()
    await query_router.connect()
    
    # Initialize metrics tracker
    metrics_tracker = DataMetrics()
    await metrics_tracker.connect()
    
    print(f"✓ Connected to Hot DB: {HOT_DB_CONFIG['uri']}")
    print(f"✓ Connected to Cold DB: {COLD_DB_CONFIG['uri']}")
    print(f"✓ Query router initialized")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connections"""
    global query_router, metrics_tracker
    
    if query_router:
        await query_router.disconnect()
    
    if metrics_tracker:
        await metrics_tracker.disconnect()
    
    print("✓ Disconnected from databases")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hot-Cold Data Separation API",
        "version": "1.0.0",
        "features": [
            "Intelligent query routing",
            "Automatic hot-cold separation",
            "Performance monitoring"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "router_stats": query_router.get_stats() if query_router else {}
    }

# ============================================================================
# USER ENDPOINTS (Example using query router)
# ============================================================================

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """
    Get user by ID - automatically checks hot DB first, then cold
    """
    try:
        user = await query_router.find_one(
            'users',
            {'_id': user_id}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users")
async def list_users(limit: int = 10, skip: int = 0):
    """
    List users - queries across both hot and cold storage
    """
    try:
        users = await query_router.find(
            'users',
            {},
            limit=limit,
            skip=skip
        )
        
        total = await query_router.count_documents('users', {})
        
        return {
            "users": users,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users")
async def create_user(user_data: dict):
    """
    Create new user - always inserted into hot storage
    """
    try:
        # Add timestamps
        user_data['created_at'] = datetime.utcnow()
        user_data['last_login'] = datetime.utcnow()
        user_data['last_accessed'] = datetime.utcnow()
        
        result = await query_router.insert_one('users', user_data)
        
        return {
            "message": "User created",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ORDERS ENDPOINTS
# ============================================================================

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get order by ID"""
    try:
        order = await query_router.find_one('orders', {'_id': order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def list_orders(limit: int = 10, skip: int = 0):
    """List orders"""
    try:
        orders = await query_router.find(
            'orders',
            {},
            limit=limit,
            skip=skip,
            sort=[('created_at', -1)]
        )
        
        total = await query_router.count_documents('orders', {})
        
        return {
            "orders": orders,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# METRICS & MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/metrics/storage")
async def get_storage_metrics():
    """Get storage usage metrics"""
    try:
        metrics = await metrics_tracker.get_storage_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/distribution")
async def get_distribution_metrics():
    """Get data distribution metrics"""
    try:
        metrics = await metrics_tracker.get_distribution_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/router-stats")
async def get_router_stats():
    """Get query router statistics"""
    return {
        "stats": query_router.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/metrics/reset-router-stats")
async def reset_router_stats():
    """Reset query router statistics"""
    query_router.reset_stats()
    return {"message": "Router statistics reset"}

@app.get("/api/metrics/migration-history")
async def get_migration_history(days: int = 7):
    """Get migration history"""
    try:
        history = await metrics_tracker.get_migration_history(days=days)
        return {
            "history": history,
            "period_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ADMIN/MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/admin/migrate/{collection}")
async def trigger_migration(collection: str, dry_run: bool = False):
    """
    Manually trigger migration for a collection
    """
    try:
        from data_separation.migrator import DataMigrator
        
        migrator = DataMigrator()
        await migrator.connect()
        
        result = await migrator.migrate_collection(collection, dry_run=dry_run)
        
        await migrator.disconnect()
        
        return {
            "collection": collection,
            "dry_run": dry_run,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ARCHIVE/COLD DATA ENDPOINTS (Different URL pattern)
# ============================================================================

@app.get("/api/archive/users/{user_id}")
async def get_archived_user(user_id: str):
    """
    Get user from COLD storage only
    Different URL pattern for cold data access
    """
    try:
        # Query cold database directly
        cold_coll = query_router.cold_db[query_router.cold_db.get_collection('users_archive')]
        user = await query_router.cold_db['users_archive'].find_one({'_id': user_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="Archived user not found")
        
        # Add metadata to indicate this is from cold storage
        user['_source'] = 'cold_storage'
        user['_accessed_at'] = datetime.utcnow().isoformat()
        
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archive/users")
async def list_archived_users(limit: int = 10, skip: int = 0):
    """
    List users from COLD storage only
    """
    try:
        cursor = query_router.cold_db['users_archive'].find({}).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        total = await query_router.cold_db['users_archive'].count_documents({})
        
        return {
            "users": users,
            "total": total,
            "limit": limit,
            "skip": skip,
            "source": "cold_storage"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archive/orders/{order_id}")
async def get_archived_order(order_id: str):
    """Get order from COLD storage only"""
    try:
        order = await query_router.cold_db['orders_archive'].find_one({'_id': order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Archived order not found")
        
        order['_source'] = 'cold_storage'
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archive/orders")
async def list_archived_orders(limit: int = 10, skip: int = 0):
    """List orders from COLD storage only"""
    try:
        cursor = query_router.cold_db['orders_archive'].find({}).skip(skip).limit(limit).sort('created_at', -1)
        orders = await cursor.to_list(length=limit)
        
        total = await query_router.cold_db['orders_archive'].count_documents({})
        
        return {
            "orders": orders,
            "total": total,
            "limit": limit,
            "skip": skip,
            "source": "cold_storage"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# STORAGE INFO ENDPOINT
# ============================================================================

@app.get("/api/storage/info")
async def get_storage_info():
    """Get information about storage configuration"""
    from data_separation.config import (
        HOT_DB_CONFIG, 
        COLD_DB_CONFIG, 
        COLD_STORAGE_BACKEND,
        HOT_READ_CONFIG,
        COLD_READ_CONFIG,
        ROUTING_CONFIG
    )
    
    return {
        "hot_storage": {
            "uri": HOT_DB_CONFIG['uri'],
            "database": HOT_DB_CONFIG['database'],
            "read_url": HOT_READ_CONFIG['base_url'] + HOT_READ_CONFIG['endpoint_prefix'],
        },
        "cold_storage": {
            "backend": COLD_STORAGE_BACKEND,
            "uri": COLD_DB_CONFIG['uri'],
            "database": COLD_DB_CONFIG['database'],
            "read_url": COLD_READ_CONFIG['base_url'] + COLD_READ_CONFIG['endpoint_prefix'],
        },
        "routing": {
            "use_different_urls": ROUTING_CONFIG['use_different_urls'],
            "cold_url_pattern": ROUTING_CONFIG['cold_url_pattern'],
        }
    }

