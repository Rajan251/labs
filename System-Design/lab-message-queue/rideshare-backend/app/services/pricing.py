"""
Pricing service with surge calculation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis import redis_client
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt
import geohash2

class PricingService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km
    
    async def calculate_surge_multiplier(self, lat: float, lon: float) -> float:
        """Calculate surge multiplier for area"""
        
        geohash = geohash2.encode(lat, lon, precision=5)
        
        # Check cache
        cached = await redis_client.get(f'surge:{geohash}')
        if cached:
            return float(cached)
        
        # Get demand (active ride requests in area)
        demand = await redis_client.zcount(f'ride_requests:{geohash}', '-inf', '+inf')
        
        # Get supply (available drivers in area)
        from app.services.location import LocationService
        location_service = LocationService(self.db)
        drivers = await location_service.find_nearby_drivers(lat, lon, radius_km=2)
        supply = len(drivers)
        
        # Calculate multiplier
        if supply == 0:
            multiplier = 3.0  # Max surge
        else:
            ratio = demand / supply
            multiplier = 1.0 + (ratio * 0.5)
            multiplier = min(multiplier, 3.0)  # Cap at 3x
            multiplier = max(multiplier, 1.0)  # Min 1x
        
        # Cache for 1 minute
        await redis_client.setex(f'surge:{geohash}', 60, str(multiplier))
        
        return round(multiplier, 2)
    
    async def calculate_fare(
        self,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: float,
        dropoff_lon: float,
        vehicle_type: str = 'sedan'
    ):
        """Calculate total fare with surge"""
        
        # Calculate distance
        distance_km = self.haversine_distance(
            pickup_lat, pickup_lon,
            dropoff_lat, dropoff_lon
        )
        
        # Pricing config
        pricing = {
            'sedan': {'base': 2.50, 'per_km': 1.50, 'per_min': 0.30},
            'suv': {'base': 3.50, 'per_km': 2.00, 'per_min': 0.40},
            'luxury': {'base': 5.00, 'per_km': 3.00, 'per_min': 0.50}
        }
        
        config = pricing.get(vehicle_type, pricing['sedan'])
        
        # Estimated time (simplified: ~20 km/h average)
        estimated_minutes = distance_km * 3
        
        # Base fare
        base_fare = (
            config['base'] +
            (distance_km * config['per_km']) +
            (estimated_minutes * config['per_min'])
        )
        
        # Get surge
        surge = await self.calculate_surge_multiplier(pickup_lat, pickup_lon)
        
        # Final fare
        final_fare = base_fare * surge
        
        return {
            'base_fare': Decimal(str(round(base_fare, 2))),
            'surge_multiplier': Decimal(str(surge)),
            'final_fare': Decimal(str(round(final_fare, 2))),
            'estimated_distance_km': Decimal(str(round(distance_km, 2))),
            'estimated_duration_min': int(estimated_minutes)
        }
