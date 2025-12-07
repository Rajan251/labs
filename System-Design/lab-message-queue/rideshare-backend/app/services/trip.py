"""
Trip management service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.database import Trip
from app.services.matching import MatchingService
from app.services.pricing import PricingService
from app.services.location import LocationService
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime
import uuid

class TripService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.matching_service = MatchingService(db)
        self.pricing_service = PricingService(db)
        self.location_service = LocationService(db)
    
    async def request_ride(
        self,
        rider_id: uuid.UUID,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: float,
        dropoff_lon: float,
        vehicle_type: str = 'sedan'
    ):
        """Create ride request and match with driver"""
        
        # 1. Calculate fare
        fare = await self.pricing_service.calculate_fare(
            pickup_lat, pickup_lon,
            dropoff_lat, dropoff_lon,
            vehicle_type
        )
        
        # 2. Create trip
        trip_id = uuid.uuid4()
        
        await self.db.execute(
            text("""
                INSERT INTO trips (
                    id, rider_id, pickup_location, dropoff_location,
                    vehicle_type, status, base_fare, surge_multiplier, final_fare
                )
                VALUES (
                    :id, :rider_id,
                    ST_SetSRID(ST_MakePoint(:pickup_lon, :pickup_lat), 4326),
                    ST_SetSRID(ST_MakePoint(:dropoff_lon, :dropoff_lat), 4326),
                    :vehicle_type, 'REQUESTED', :base_fare, :surge, :final_fare
                )
            """),
            {
                "id": str(trip_id),
                "rider_id": str(rider_id),
                "pickup_lon": pickup_lon,
                "pickup_lat": pickup_lat,
                "dropoff_lon": dropoff_lon,
                "dropoff_lat": dropoff_lat,
                "vehicle_type": vehicle_type,
                "base_fare": fare['base_fare'],
                "surge": fare['surge_multiplier'],
                "final_fare": fare['final_fare']
            }
        )
        await self.db.commit()
        
        # 3. Find driver
        driver = await self.matching_service.find_best_driver(
            pickup_lat, pickup_lon, vehicle_type
        )
        
        if not driver:
            await self._update_status(trip_id, 'NO_DRIVERS_AVAILABLE')
            raise HTTPException(404, "No drivers available")
        
        # 4. Assign driver
        await self.assign_driver(trip_id, uuid.UUID(driver['driver_id']))
        
        return {
            'trip_id': str(trip_id),
            'driver': driver,
            'estimated_fare': fare['final_fare'],
            'surge_multiplier': fare['surge_multiplier'],
            'eta_minutes': 5
        }
    
    async def assign_driver(self, trip_id: uuid.UUID, driver_id: uuid.UUID):
        """Assign driver to trip"""
        await self.db.execute(
            text("""
                UPDATE trips
                SET driver_id = :driver_id,
                    status = 'DRIVER_ASSIGNED',
                    driver_assigned_at = NOW()
                WHERE id = :trip_id
            """),
            {"driver_id": str(driver_id), "trip_id": str(trip_id)}
        )
        await self.db.commit()
        
        # Mark driver as busy
        await self.location_service.mark_driver_busy(driver_id)
    
    async def start_trip(self, trip_id: uuid.UUID):
        """Start trip (rider picked up)"""
        await self._update_status(trip_id, 'IN_PROGRESS')
        await self.db.execute(
            text("UPDATE trips SET trip_started_at = NOW() WHERE id = :id"),
            {"id": str(trip_id)}
        )
        await self.db.commit()
    
    async def complete_trip(self, trip_id: uuid.UUID, actual_distance_km: float):
        """Complete trip"""
        await self._update_status(trip_id, 'COMPLETED')
        await self.db.execute(
            text("""
                UPDATE trips
                SET trip_completed_at = NOW(),
                    actual_distance_km = :distance
                WHERE id = :id
            """),
            {"distance": actual_distance_km, "id": str(trip_id)}
        )
        await self.db.commit()
        
        # Get driver and mark available
        result = await self.db.execute(
            text("SELECT driver_id FROM trips WHERE id = :id"),
            {"id": str(trip_id)}
        )
        row = result.fetchone()
        if row and row[0]:
            await self.location_service.mark_driver_online(uuid.UUID(row[0]))
    
    async def _update_status(self, trip_id: uuid.UUID, status: str):
        """Update trip status"""
        await self.db.execute(
            text("UPDATE trips SET status = :status WHERE id = :id"),
            {"status": status, "id": str(trip_id)}
        )
