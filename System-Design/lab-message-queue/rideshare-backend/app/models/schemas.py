"""
Pydantic schemas for API validation
"""
from pydantic import BaseModel, UUID4, Field, ConfigDict, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum

# Enums
class UserType(str, Enum):
    RIDER = "rider"
    DRIVER = "driver"

class TripStatus(str, Enum):
    REQUESTED = "REQUESTED"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    DRIVER_ARRIVING = "DRIVER_ARRIVING"
    DRIVER_ARRIVED = "DRIVER_ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class VehicleType(str, Enum):
    SEDAN = "sedan"
    SUV = "suv"
    LUXURY = "luxury"

# Location
class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

# User Schemas
class UserRegister(BaseModel):
    phone_number: str
    full_name: str
    email: Optional[str] = None
    user_type: UserType

class DriverRegister(UserRegister):
    user_type: UserType = UserType.DRIVER
    vehicle_type: VehicleType
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    vehicle_color: str
    license_plate: str
    drivers_license_number: str
    drivers_license_expiry: datetime

class User(BaseModel):
    id: UUID4
    phone_number: str
    full_name: str
    email: Optional[str]
    user_type: UserType
    rating: Decimal
    total_trips: int
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Trip Schemas
class TripRequest(BaseModel):
    pickup_location: Location
    dropoff_location: Location
    vehicle_type: VehicleType = VehicleType.SEDAN

class TripResponse(BaseModel):
    trip_id: UUID4
    status: TripStatus
    driver: Optional[dict] = None
    estimated_fare: Decimal
    surge_multiplier: Decimal
    eta_minutes: Optional[int] = None

class Trip(BaseModel):
    id: UUID4
    rider_id: UUID4
    driver_id: Optional[UUID4]
    status: TripStatus
    vehicle_type: VehicleType
    base_fare: Optional[Decimal]
    surge_multiplier: Decimal
    final_fare: Optional[Decimal]
    requested_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Location Update
class LocationUpdate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

# Driver Status
class DriverStatus(BaseModel):
    is_online: bool
    is_available: bool
    current_location: Optional[Location] = None

# Fare Estimate
class FareEstimate(BaseModel):
    base_fare: Decimal
    surge_multiplier: Decimal
    final_fare: Decimal
    estimated_distance_km: Decimal
    estimated_duration_min: int

# Payment
class PaymentMethodCreate(BaseModel):
    stripe_payment_method_id: str
    is_default: bool = False

# Auth
class PhoneVerify(BaseModel):
    phone_number: str
    otp: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
