"""
Main FastAPI application for ride-sharing backend
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import schemas
from app.services.trip import TripService
from app.services.location import LocationService
from app.services.pricing import PricingService
from typing import List
import uuid

app = FastAPI(
    title="Ride-Sharing API",
    description="Complete ride-sharing backend like Uber",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ============ Trip Management ============

@app.post("/api/v1/trips/request", response_model=schemas.TripResponse)
async def request_ride(
    request: schemas.TripRequest,
    rider_id: uuid.UUID,  # TODO: Get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Request a ride"""
    service = TripService(db)
    
    result = await service.request_ride(
        rider_id,
        request.pickup_location.lat,
        request.pickup_location.lon,
        request.dropoff_location.lat,
        request.dropoff_location.lon,
        request.vehicle_type.value
    )
    
    return schemas.TripResponse(
        trip_id=uuid.UUID(result['trip_id']),
        status=schemas.TripStatus.DRIVER_ASSIGNED,
        driver=result['driver'],
        estimated_fare=result['estimated_fare'],
        surge_multiplier=result['surge_multiplier'],
        eta_minutes=result.get('eta_minutes')
    )

@app.post("/api/v1/trips/{trip_id}/start")
async def start_trip(
    trip_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Driver starts trip (rider picked up)"""
    service = TripService(db)
    await service.start_trip(trip_id)
    return {"status": "trip_started"}

@app.post("/api/v1/trips/{trip_id}/complete")
async def complete_trip(
    trip_id: uuid.UUID,
    actual_distance_km: float,
    db: AsyncSession = Depends(get_db)
):
    """Complete trip"""
    service = TripService(db)
    await service.complete_trip(trip_id, actual_distance_km)
    return {"status": "trip_completed"}

@app.get("/api/v1/trips/{trip_id}")
async def get_trip(
    trip_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get trip details"""
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT * FROM trips WHERE id = :id"),
        {"id": str(trip_id)}
    )
    trip = result.fetchone()
    if not trip:
        raise HTTPException(404, "Trip not found")
    return dict(trip._mapping)

# ============ Pricing ============

@app.post("/api/v1/pricing/estimate", response_model=schemas.FareEstimate)
async def estimate_fare(
    pickup: schemas.Location,
    dropoff: schemas.Location,
    vehicle_type: schemas.VehicleType = schemas.VehicleType.SEDAN,
    db: AsyncSession = Depends(get_db)
):
    """Get fare estimate"""
    service = PricingService(db)
    
    fare = await service.calculate_fare(
        pickup.lat, pickup.lon,
        dropoff.lat, dropoff.lon,
        vehicle_type.value
    )
    
    return schemas.FareEstimate(**fare)

# ============ Driver Location ============

@app.post("/api/v1/driver/location")
async def update_driver_location(
    location: schemas.LocationUpdate,
    driver_id: uuid.UUID,  # TODO: Get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Update driver location"""
    service = LocationService(db)
    await service.update_driver_location(driver_id, location.lat, location.lon)
    return {"status": "location_updated"}

@app.post("/api/v1/driver/online")
async def driver_go_online(
    driver_id: uuid.UUID,  # TODO: Get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Mark driver as online"""
    service = LocationService(db)
    await service.mark_driver_online(driver_id)
    return {"status": "online"}

@app.post("/api/v1/driver/offline")
async def driver_go_offline(
    driver_id: uuid.UUID,  # TODO: Get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Mark driver as offline"""
    service = LocationService(db)
    await service.mark_driver_offline(driver_id)
    return {"status": "offline"}

# ============ WebSocket for Real-Time Location ============

@app.websocket("/ws/driver/{driver_id}")
async def driver_location_websocket(
    websocket: WebSocket,
    driver_id: uuid.UUID
):
    """WebSocket for continuous driver location updates"""
    await websocket.accept()
    
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        service = LocationService(db)
        
        try:
            while True:
                # Receive location update
                data = await websocket.receive_json()
                
                # Update location
                await service.update_driver_location(
                    driver_id,
                    data['lat'],
                    data['lon']
                )
                
                # Send acknowledgment
                await websocket.send_json({"status": "ok"})
                
        except WebSocketDisconnect:
            # Mark driver offline
            await service.mark_driver_offline(driver_id)

# ============ User Registration ============

@app.post("/api/v1/auth/register/rider", response_model=schemas.User)
async def register_rider(
    user: schemas.UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register new rider"""
    from sqlalchemy import text
    
    user_id = uuid.uuid4()
    
    # Create user
    await db.execute(
        text("""
            INSERT INTO users (id, phone_number, full_name, email, user_type)
            VALUES (:id, :phone, :name, :email, 'rider')
        """),
        {
            "id": str(user_id),
            "phone": user.phone_number,
            "name": user.full_name,
            "email": user.email
        }
    )
    
    # Create rider profile
    await db.execute(
        text("INSERT INTO riders (id, user_id) VALUES (:id, :user_id)"),
        {"id": str(uuid.uuid4()), "user_id": str(user_id)}
    )
    
    await db.commit()
    
    return schemas.User(
        id=user_id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        email=user.email,
        user_type=schemas.UserType.RIDER,
        rating=5.00,
        total_trips=0,
        status="active",
        created_at=datetime.now()
    )

@app.post("/api/v1/auth/register/driver", response_model=schemas.User)
async def register_driver(
    driver: schemas.DriverRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register new driver"""
    from sqlalchemy import text
    from datetime import datetime
    
    user_id = uuid.uuid4()
    
    # Create user
    await db.execute(
        text("""
            INSERT INTO users (id, phone_number, full_name, email, user_type)
            VALUES (:id, :phone, :name, :email, 'driver')
        """),
        {
            "id": str(user_id),
            "phone": driver.phone_number,
            "name": driver.full_name,
            "email": driver.email
        }
    )
    
    # Create driver profile
    await db.execute(
        text("""
            INSERT INTO drivers (
                id, user_id, vehicle_type, vehicle_make, vehicle_model,
                vehicle_year, vehicle_color, license_plate,
                drivers_license_number, drivers_license_expiry
            )
            VALUES (
                :id, :user_id, :vtype, :make, :model,
                :year, :color, :plate, :license, :expiry
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "vtype": driver.vehicle_type.value,
            "make": driver.vehicle_make,
            "model": driver.vehicle_model,
            "year": driver.vehicle_year,
            "color": driver.vehicle_color,
            "plate": driver.license_plate,
            "license": driver.drivers_license_number,
            "expiry": driver.drivers_license_expiry
        }
    )
    
    await db.commit()
    
    return schemas.User(
        id=user_id,
        phone_number=driver.phone_number,
        full_name=driver.full_name,
        email=driver.email,
        user_type=schemas.UserType.DRIVER,
        rating=5.00,
        total_trips=0,
        status="active",
        created_at=datetime.now()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
