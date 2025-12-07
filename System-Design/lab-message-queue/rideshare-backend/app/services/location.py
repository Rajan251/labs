"""
Location tracking service with Redis Geo and WebSocket support
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis import redis_client
from typing import List, Dict, Optional
import json
from datetime import datetime
import uuid
import geohash2

class LocationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_driver_location(self, driver_id: uuid.UUID, lat: float, lon: float):
        """Update driver location in Redis Geo"""
        
        # Store in Redis Geo (for proximity queries)
        await redis_client.geoadd(
            'drivers:online',
            lon, lat, str(driver_id)
        )
        
        # Set expiry (30 seconds - if driver disconnects)
        await redis_client.expire(f'driver:{driver_id}:location', 30)
        
        # Store detailed location data
        await redis_client.setex(
            f'driver:{driver_id}:location',
            30,
            json.dumps({
                'lat': lat,
                'lon': lon,
                'timestamp': datetime.utcnow().isoformat()
            })
        )
        
        # Update database (async, non-blocking)
        from sqlalchemy import text
        await self.db.execute(
            text("""
                UPDATE drivers
                SET current_location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                    last_location_update = NOW()
                WHERE user_id = :driver_id
            """),
            {"lon": lon, "lat": lat, "driver_id": str(driver_id)}
        )
        await self.db.commit()
        
        # Update geohash index
        geohash = geohash2.encode(lat, lon, precision=6)
        await redis_client.sadd(f'drivers:geohash:{geohash}', str(driver_id))
        await redis_client.expire(f'drivers:geohash:{geohash}', 60)
    
    async def find_nearby_drivers(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5,
        vehicle_type: Optional[str] = None
    ) -> List[Dict]:
        """Find available drivers within radius"""
        
        # GEORADIUS query
        nearby = await redis_client.georadius(
            'drivers:online',
            lon, lat,
            radius_km,
            unit='km',
            withdist=True,
            withcoord=True,
            sort='ASC'
        )
        
        available_drivers = []
        for item in nearby:
            driver_id = item[0]
            distance = item[1]
            coords = item[2]
            
            # Check if driver is available
            is_available = await redis_client.get(f'driver:{driver_id}:available')
            if is_available == '1':
                available_drivers.append({
                    'driver_id': driver_id,
                    'distance_km': float(distance),
                    'location': {'lat': coords[1], 'lon': coords[0]}
                })
        
        return available_drivers
    
    async def mark_driver_online(self, driver_id: uuid.UUID):
        """Mark driver as online and available"""
        await redis_client.set(f'driver:{driver_id}:available', '1')
    
    async def mark_driver_offline(self, driver_id: uuid.UUID):
        """Remove driver from online pool"""
        await redis_client.delete(f'driver:{driver_id}:available')
        await redis_client.zrem('drivers:online', str(driver_id))
    
    async def mark_driver_busy(self, driver_id: uuid.UUID):
        """Mark driver as busy (on trip)"""
        await redis_client.set(f'driver:{driver_id}:available', '0')
