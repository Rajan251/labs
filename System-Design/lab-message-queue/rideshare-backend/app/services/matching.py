"""
Driver-rider matching service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import Driver, User
from app.services.location import LocationService
from typing import Optional, Dict
import uuid

class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.location_service = LocationService(db)
    
    async def find_best_driver(
        self,
        pickup_lat: float,
        pickup_lon: float,
        vehicle_type: str = 'sedan',
        max_distance_km: float = 5
    ) -> Optional[Dict]:
        """Find best available driver using multi-factor scoring"""
        
        # 1. Find nearby drivers
        nearby_drivers = await self.location_service.find_nearby_drivers(
            pickup_lat, pickup_lon, max_distance_km
        )
        
        if not nearby_drivers:
            return None
        
        # 2. Get driver details
        driver_ids = [uuid.UUID(d['driver_id']) for d in nearby_drivers]
        
        result = await self.db.execute(
            select(Driver, User)
            .join(User, Driver.user_id == User.id)
            .where(
                Driver.user_id.in_(driver_ids),
                Driver.vehicle_type == vehicle_type,
                Driver.is_online == True,
                Driver.is_available == True
            )
        )
        
        drivers_info = result.all()
        
        # 3. Score each driver
        scored_drivers = []
        for driver, user in drivers_info:
            distance = next(
                float(d['distance_km']) for d in nearby_drivers 
                if d['driver_id'] == str(driver.user_id)
            )
            
            # Scoring formula
            score = (
                (1 / (distance + 0.1)) * 0.5 +  # Distance: 50%
                float(user.rating) * 0.3 +       # Rating: 30%
                float(driver.acceptance_rate) * 0.2  # Acceptance: 20%
            )
            
            scored_drivers.append({
                'driver_id': str(driver.user_id),
                'score': score,
                'distance_km': distance,
                'rating': float(user.rating),
                'vehicle_type': driver.vehicle_type,
                'driver_name': user.full_name
            })
        
        # 4. Sort by score
        scored_drivers.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_drivers[0] if scored_drivers else None
