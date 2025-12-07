"""
Database models for ride-sharing system
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint, Index, text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from geoalchemy2 import Geography
import uuid

Base = declarative_base()

class User(Base):
    """Base user model for both riders and drivers"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True)
    full_name = Column(String(200), nullable=False)
    user_type = Column(String(20), nullable=False)  # 'rider' or 'driver'
    profile_photo_url = Column(String(500))
    rating = Column(Numeric(3, 2), default=5.00)
    total_trips = Column(Integer, default=0)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    driver_profile = relationship("Driver", back_populates="user", uselist=False)
    rider_profile = relationship("Rider", back_populates="user", uselist=False)
    
    __table_args__ = (
        Index('idx_user_type', 'user_type'),
    )

class Driver(Base):
    """Driver-specific information"""
    __tablename__ = "drivers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Vehicle
    vehicle_type = Column(String(50), nullable=False)
    vehicle_make = Column(String(100))
    vehicle_model = Column(String(100))
    vehicle_year = Column(Integer)
    vehicle_color = Column(String(50))
    license_plate = Column(String(20), unique=True, nullable=False)
    
    # Documents
    drivers_license_number = Column(String(50), unique=True, nullable=False)
    drivers_license_expiry = Column(DateTime, nullable=False)
    
    # Verification
    background_check_status = Column(String(20), default='pending')
    is_approved = Column(Boolean, default=False)
    
    # Availability
    is_online = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    current_location = Column(Geography(geometry_type='POINT', srid=4326))
    last_location_update = Column(DateTime)
    
    # Stats
    acceptance_rate = Column(Numeric(3, 2), default=1.00)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="driver_profile")
    
    __table_args__ = (
        Index('idx_driver_online', 'is_online', 'is_available'),
        Index('idx_driver_location', 'current_location', postgresql_using='gist'),
    )

class Rider(Base):
    """Rider-specific information"""
    __tablename__ = "riders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    default_payment_method_id = Column(UUID(as_uuid=True))
    preferred_vehicle_types = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="rider_profile")

class Trip(Base):
    """Trip/ride information"""
    __tablename__ = "trips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Locations
    pickup_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    pickup_address = Column(String)
    dropoff_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    dropoff_address = Column(String)
    
    # Trip details
    vehicle_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)
    
    # Pricing
    base_fare = Column(Numeric(10, 2))
    surge_multiplier = Column(Numeric(3, 2), default=1.00)
    final_fare = Column(Numeric(10, 2))
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow)
    driver_assigned_at = Column(DateTime)
    driver_arrived_at = Column(DateTime)
    trip_started_at = Column(DateTime)
    trip_completed_at = Column(DateTime)
    
    # Actual trip data
    actual_distance_km = Column(Numeric(8, 2))
    actual_duration_min = Column(Integer)
    route_polyline = Column(String)
    
    # Ratings
    rider_rating = Column(Integer)
    driver_rating = Column(Integer)
    
    # Cancellation
    cancelled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cancellation_reason = Column(String)
    cancellation_fee = Column(Numeric(10, 2), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('rider_rating >= 1 AND rider_rating <= 5', name='check_rider_rating'),
        CheckConstraint('driver_rating >= 1 AND driver_rating <= 5', name='check_driver_rating'),
        Index('idx_trip_rider', 'rider_id', 'created_at'),
        Index('idx_trip_driver', 'driver_id', 'created_at'),
        Index('idx_trip_status', 'status'),
    )

class Payment(Base):
    """Payment transactions"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False)
    stripe_payment_intent_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_payment_trip', 'trip_id'),
    )

class PaymentMethod(Base):
    """User payment methods"""
    __tablename__ = "payment_methods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    stripe_payment_method_id = Column(String(100))
    last_four_digits = Column(String(4))
    card_brand = Column(String(20))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_payment_method_user', 'user_id'),
    )
