# Ride-Sharing Backend System Design (Uber-like)

> Complete backend architecture for a scalable ride-sharing platform

## Table of Contents

1. [System Overview](#system-overview)
2. [Rider & Driver Registration](#rider--driver-registration)
3. [Real-Time Location Tracking](#real-time-location-tracking)
4. [Driver-Rider Matching](#driver-rider-matching)
5. [Surge Pricing](#surge-pricing)
6. [Trip Lifecycle](#trip-lifecycle)
7. [Payment Processing](#payment-processing)
8. [Scaling for Large Cities](#scaling-for-large-cities)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Apps                          │
│                  (Rider App | Driver App)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│              (Load Balancer + Rate Limiting)                │
└────────┬────────────────────────────────────────────────────┘
         │
         ├──────────┬──────────┬──────────┬──────────┬─────────┐
         ▼          ▼          ▼          ▼          ▼         ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │ User   │ │Location│ │Matching│ │ Trip   │ │Payment │ │Pricing │
    │Service │ │Service │ │Service │ │Service │ │Service │ │Service │
    └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼          ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                     Data Layer                               │
    │  PostgreSQL | Redis | Cassandra | Kafka | Elasticsearch     │
    └──────────────────────────────────────────────────────────────┘
```

### Core Services

| Service | Purpose | Technology |
|---------|---------|------------|
| **User Service** | Registration, profiles, auth | PostgreSQL, JWT |
| **Location Service** | Real-time GPS tracking | Redis Geo, WebSocket |
| **Matching Service** | Driver-rider pairing | Redis, Geohashing |
| **Trip Service** | Trip lifecycle management | PostgreSQL, State Machine |
| **Payment Service** | Payment processing | Stripe, PostgreSQL |
| **Pricing Service** | Fare calculation, surge | Redis, Time-series DB |
| **Notification Service** | Push notifications | FCM, SNS |

---

## Rider & Driver Registration

### Data Models

```sql
-- Users table (both riders and drivers)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(200) NOT NULL,
    user_type VARCHAR(20) NOT NULL, -- 'rider' or 'driver'
    profile_photo_url VARCHAR(500),
    rating DECIMAL(3,2) DEFAULT 5.00,
    total_trips INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, banned
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_phone (phone_number),
    INDEX idx_email (email),
    INDEX idx_type (user_type)
);

-- Driver-specific information
CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) UNIQUE NOT NULL,
    
    -- Vehicle info
    vehicle_type VARCHAR(50) NOT NULL, -- sedan, suv, luxury
    vehicle_make VARCHAR(100),
    vehicle_model VARCHAR(100),
    vehicle_year INT,
    vehicle_color VARCHAR(50),
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    
    -- Documents
    drivers_license_number VARCHAR(50) UNIQUE NOT NULL,
    drivers_license_expiry DATE NOT NULL,
    vehicle_registration_number VARCHAR(50),
    insurance_policy_number VARCHAR(50),
    
    -- Verification
    background_check_status VARCHAR(20) DEFAULT 'pending',
    document_verification_status VARCHAR(20) DEFAULT 'pending',
    is_approved BOOLEAN DEFAULT FALSE,
    
    -- Availability
    is_online BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE, -- not on trip
    current_location GEOGRAPHY(POINT),
    last_location_update TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user (user_id),
    INDEX idx_online (is_online, is_available),
    INDEX idx_location (current_location) USING GIST
);

-- Rider-specific information
CREATE TABLE riders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) UNIQUE NOT NULL,
    
    -- Payment methods
    default_payment_method_id UUID,
    
    -- Preferences
    preferred_vehicle_types VARCHAR(100)[], -- ['sedan', 'suv']
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Payment methods
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    type VARCHAR(20) NOT NULL, -- card, wallet, cash
    
    -- Card details (tokenized)
    stripe_payment_method_id VARCHAR(100),
    last_four_digits VARCHAR(4),
    card_brand VARCHAR(20),
    
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user (user_id)
);
```

### Registration Flow

**Rider Registration**:
```
1. Phone number verification (OTP)
2. Basic profile (name, email, photo)
3. Add payment method
4. Account created → Can request rides
```

**Driver Registration**:
```
1. Phone number verification (OTP)
2. Personal information
3. Vehicle details
4. Document upload (license, registration, insurance)
5. Background check (3rd party API)
6. Admin approval
7. Account activated → Can accept rides
```

### API Endpoints

```python
# Rider Registration
POST /api/v1/auth/register/rider
{
  "phone_number": "+1234567890",
  "full_name": "John Doe",
  "email": "john@example.com"
}

# Driver Registration
POST /api/v1/auth/register/driver
{
  "phone_number": "+1234567890",
  "full_name": "Jane Driver",
  "email": "jane@example.com",
  "vehicle": {
    "type": "sedan",
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "license_plate": "ABC123"
  },
  "documents": {
    "drivers_license": "DL123456",
    "license_expiry": "2025-12-31"
  }
}

# Phone verification
POST /api/v1/auth/verify-phone
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

---

## Real-Time Location Tracking

### Architecture

```
Driver App → WebSocket → Location Service → Redis Geo + Kafka
                                                ↓
                                         Location Stream
                                                ↓
                                    [Matching Service]
                                    [Analytics Service]
```

### Technology Stack

- **WebSocket**: Persistent connection for real-time updates
- **Redis Geo**: Geospatial queries (nearby drivers)
- **Kafka**: Location event streaming
- **Time-series DB**: Historical location data

### Implementation

**Driver Location Updates**:

```python
# Driver sends location every 5 seconds
class LocationService:
    async def update_driver_location(self, driver_id: UUID, lat: float, lon: float):
        """Update driver location in Redis"""
        
        # Store in Redis Geo
        await redis.geoadd(
            'drivers:online',
            lon, lat, str(driver_id)
        )
        
        # Set expiry (if driver disconnects)
        await redis.expire(f'driver:{driver_id}:location', 30)
        
        # Update database (async)
        await db.execute(
            """
            UPDATE drivers
            SET current_location = ST_SetSRID(ST_MakePoint($1, $2), 4326),
                last_location_update = NOW()
            WHERE user_id = $3
            """,
            lon, lat, driver_id
        )
        
        # Publish to Kafka for analytics
        await kafka.produce('driver-locations', {
            'driver_id': str(driver_id),
            'lat': lat,
            'lon': lon,
            'timestamp': datetime.now().isoformat()
        })
```

**Find Nearby Drivers**:

```python
async def find_nearby_drivers(self, lat: float, lon: float, radius_km: float = 5):
    """Find drivers within radius using Redis Geo"""
    
    # GEORADIUS query
    nearby = await redis.georadius(
        'drivers:online',
        lon, lat,
        radius_km,
        unit='km',
        withdist=True,
        withcoord=True,
        sort='ASC'  # Closest first
    )
    
    # Filter available drivers
    available_drivers = []
    for driver_id, distance, coords in nearby:
        # Check if driver is available (not on trip)
        is_available = await redis.get(f'driver:{driver_id}:available')
        if is_available == '1':
            available_drivers.append({
                'driver_id': driver_id,
                'distance_km': distance,
                'location': {'lat': coords[1], 'lon': coords[0]}
            })
    
    return available_drivers
```

**WebSocket Connection**:

```python
from fastapi import WebSocket

@app.websocket("/ws/driver/{driver_id}")
async def driver_location_websocket(websocket: WebSocket, driver_id: UUID):
    await websocket.accept()
    
    try:
        while True:
            # Receive location update
            data = await websocket.receive_json()
            
            # Update location
            await location_service.update_driver_location(
                driver_id,
                data['lat'],
                data['lon']
            )
            
            # Send acknowledgment
            await websocket.send_json({"status": "ok"})
            
    except WebSocketDisconnect:
        # Mark driver offline
        await redis.delete(f'driver:{driver_id}:location')
```

### Geohashing for Efficient Queries

```python
import geohash2

def get_geohash_prefix(lat: float, lon: float, precision: int = 6):
    """Convert lat/lon to geohash for indexing"""
    return geohash2.encode(lat, lon, precision=precision)

# Store drivers by geohash
geohash = get_geohash_prefix(37.7749, -122.4194)  # San Francisco
await redis.sadd(f'drivers:geohash:{geohash}', driver_id)

# Find drivers in same geohash cell
drivers = await redis.smembers(f'drivers:geohash:{geohash}')
```

---

## Driver-Rider Matching

### Matching Algorithm

**Factors Considered**:
1. **Distance**: Closest driver first
2. **Driver Rating**: Prefer higher-rated drivers
3. **Acceptance Rate**: Drivers who accept more rides
4. **Vehicle Type**: Match rider preference
5. **Estimated Time to Pickup**: Traffic-aware ETA

### Implementation

```python
class MatchingService:
    async def find_best_driver(
        self,
        pickup_lat: float,
        pickup_lon: float,
        vehicle_type: str = 'sedan',
        max_distance_km: float = 5
    ):
        """Find best available driver"""
        
        # 1. Find nearby drivers
        nearby_drivers = await location_service.find_nearby_drivers(
            pickup_lat, pickup_lon, max_distance_km
        )
        
        if not nearby_drivers:
            return None
        
        # 2. Get driver details
        driver_ids = [d['driver_id'] for d in nearby_drivers]
        drivers_info = await db.fetch_all(
            """
            SELECT 
                d.user_id,
                d.vehicle_type,
                u.rating,
                d.acceptance_rate,
                d.current_location
            FROM drivers d
            JOIN users u ON u.id = d.user_id
            WHERE d.user_id = ANY($1)
              AND d.vehicle_type = $2
              AND d.is_online = TRUE
              AND d.is_available = TRUE
            """,
            driver_ids, vehicle_type
        )
        
        # 3. Score each driver
        scored_drivers = []
        for driver in drivers_info:
            distance = next(
                d['distance_km'] for d in nearby_drivers 
                if d['driver_id'] == str(driver['user_id'])
            )
            
            # Scoring formula
            score = (
                (1 / (distance + 0.1)) * 0.5 +  # Distance weight: 50%
                driver['rating'] * 0.3 +         # Rating weight: 30%
                driver['acceptance_rate'] * 0.2  # Acceptance weight: 20%
            )
            
            scored_drivers.append({
                'driver_id': driver['user_id'],
                'score': score,
                'distance_km': distance,
                'rating': driver['rating']
            })
        
        # 4. Sort by score
        scored_drivers.sort(key=lambda x: x['score'], reverse=True)
        
        # 5. Return best driver
        return scored_drivers[0] if scored_drivers else None
    
    async def dispatch_ride_request(
        self,
        ride_request_id: UUID,
        driver_id: UUID,
        timeout_seconds: int = 30
    ):
        """Send ride request to driver with timeout"""
        
        # Store request in Redis with expiry
        await redis.setex(
            f'ride_request:{ride_request_id}',
            timeout_seconds,
            json.dumps({
                'driver_id': str(driver_id),
                'status': 'pending',
                'expires_at': (datetime.now() + timedelta(seconds=timeout_seconds)).isoformat()
            })
        )
        
        # Send push notification to driver
        await notification_service.send_push(
            driver_id,
            {
                'type': 'ride_request',
                'request_id': str(ride_request_id),
                'pickup_location': {...},
                'estimated_fare': 15.50
            }
        )
        
        # Wait for response (with timeout)
        response = await self._wait_for_driver_response(
            ride_request_id,
            timeout_seconds
        )
        
        if response == 'accepted':
            return {'status': 'matched', 'driver_id': str(driver_id)}
        else:
            # Try next driver
            return await self._try_next_driver(ride_request_id)
```

### Cascading Dispatch

If first driver declines, try next best driver:

```python
async def cascade_dispatch(self, ride_request_id: UUID, ranked_drivers: List):
    """Try drivers in order until one accepts"""
    
    for driver in ranked_drivers:
        result = await self.dispatch_ride_request(
            ride_request_id,
            driver['driver_id'],
            timeout_seconds=15  # Shorter timeout for cascade
        )
        
        if result['status'] == 'matched':
            return result
    
    # No drivers accepted
    return {'status': 'no_drivers_available'}
```

---

## Surge Pricing

### Dynamic Pricing Model

**Formula**:
```
Final Fare = Base Fare × Surge Multiplier

Surge Multiplier = 1.0 + (Demand / Supply) × Surge Factor

Where:
- Demand = Active ride requests in area
- Supply = Available drivers in area
- Surge Factor = Configurable (e.g., 0.5)
```

### Implementation

```python
class SurgePricingService:
    async def calculate_surge_multiplier(
        self,
        lat: float,
        lon: float,
        radius_km: float = 2
    ) -> float:
        """Calculate surge multiplier for area"""
        
        # Get geohash for area
        geohash = get_geohash_prefix(lat, lon, precision=5)
        
        # Check cache first
        cached = await redis.get(f'surge:{geohash}')
        if cached:
            return float(cached)
        
        # Calculate demand (active ride requests)
        demand = await redis.zcount(
            f'ride_requests:{geohash}',
            '-inf', '+inf'
        )
        
        # Calculate supply (available drivers)
        supply = len(await location_service.find_nearby_drivers(
            lat, lon, radius_km
        ))
        
        # Prevent division by zero
        if supply == 0:
            multiplier = 3.0  # Max surge
        else:
            ratio = demand / supply
            multiplier = 1.0 + (ratio * 0.5)  # Surge factor = 0.5
            multiplier = min(multiplier, 3.0)  # Cap at 3x
            multiplier = max(multiplier, 1.0)  # Min 1x
        
        # Cache for 1 minute
        await redis.setex(f'surge:{geohash}', 60, str(multiplier))
        
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
        
        # Base fare calculation
        distance_km = haversine_distance(
            pickup_lat, pickup_lon,
            dropoff_lat, dropoff_lon
        )
        
        # Pricing config
        pricing = {
            'sedan': {'base': 2.50, 'per_km': 1.50, 'per_min': 0.30},
            'suv': {'base': 3.50, 'per_km': 2.00, 'per_min': 0.40},
            'luxury': {'base': 5.00, 'per_km': 3.00, 'per_min': 0.50}
        }
        
        config = pricing[vehicle_type]
        
        # Estimated time (simplified)
        estimated_minutes = distance_km * 3  # ~20 km/h average
        
        # Base fare
        base_fare = (
            config['base'] +
            (distance_km * config['per_km']) +
            (estimated_minutes * config['per_min'])
        )
        
        # Get surge multiplier
        surge = await self.calculate_surge_multiplier(pickup_lat, pickup_lon)
        
        # Final fare
        final_fare = base_fare * surge
        
        return {
            'base_fare': round(base_fare, 2),
            'surge_multiplier': surge,
            'final_fare': round(final_fare, 2),
            'estimated_distance_km': round(distance_km, 2),
            'estimated_duration_min': round(estimated_minutes, 0)
        }
```

### Surge Zones

```python
# Define surge zones (geohashes)
SURGE_ZONES = {
    'downtown_sf': {
        'geohash_prefix': '9q8yy',
        'peak_hours': [(7, 9), (17, 19)],  # Morning & evening rush
        'base_surge': 1.2
    },
    'airport': {
        'geohash_prefix': '9q8zh',
        'always_surge': True,
        'base_surge': 1.5
    }
}

async def get_zone_surge(geohash: str, hour: int) -> float:
    """Get zone-specific surge"""
    for zone, config in SURGE_ZONES.items():
        if geohash.startswith(config['geohash_prefix']):
            if config.get('always_surge'):
                return config['base_surge']
            
            # Check peak hours
            for start, end in config.get('peak_hours', []):
                if start <= hour < end:
                    return config['base_surge']
    
    return 1.0
```

---

## Trip Lifecycle

### State Machine

```
REQUESTED → DRIVER_ASSIGNED → DRIVER_ARRIVING → 
DRIVER_ARRIVED → IN_PROGRESS → COMPLETED → PAID

Cancellation states:
- CANCELLED_BY_RIDER (before driver arrives)
- CANCELLED_BY_DRIVER (before pickup)
- CANCELLED_NO_SHOW (driver arrived, rider no-show)
```

### Data Model

```sql
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rider_id UUID REFERENCES users(id) NOT NULL,
    driver_id UUID REFERENCES users(id),
    
    -- Locations
    pickup_location GEOGRAPHY(POINT) NOT NULL,
    pickup_address TEXT,
    dropoff_location GEOGRAPHY(POINT) NOT NULL,
    dropoff_address TEXT,
    
    -- Trip details
    vehicle_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    
    -- Pricing
    base_fare DECIMAL(10,2),
    surge_multiplier DECIMAL(3,2) DEFAULT 1.00,
    final_fare DECIMAL(10,2),
    
    -- Timestamps
    requested_at TIMESTAMP DEFAULT NOW(),
    driver_assigned_at TIMESTAMP,
    driver_arrived_at TIMESTAMP,
    trip_started_at TIMESTAMP,
    trip_completed_at TIMESTAMP,
    
    -- Actual trip data
    actual_distance_km DECIMAL(8,2),
    actual_duration_min INT,
    route_polyline TEXT, -- Encoded polyline
    
    -- Ratings
    rider_rating INT CHECK (rider_rating BETWEEN 1 AND 5),
    driver_rating INT CHECK (driver_rating BETWEEN 1 AND 5),
    
    -- Cancellation
    cancelled_by UUID REFERENCES users(id),
    cancellation_reason TEXT,
    cancellation_fee DECIMAL(10,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_rider (rider_id, created_at DESC),
    INDEX idx_driver (driver_id, created_at DESC),
    INDEX idx_status (status),
    INDEX idx_requested (requested_at)
);

-- Trip events (audit trail)
CREATE TABLE trip_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_trip (trip_id, created_at)
);
```

### Trip Flow Implementation

```python
class TripService:
    async def request_ride(
        self,
        rider_id: UUID,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: float,
        dropoff_lon: float,
        vehicle_type: str = 'sedan'
    ):
        """Create ride request"""
        
        # 1. Calculate fare estimate
        fare = await pricing_service.calculate_fare(
            pickup_lat, pickup_lon,
            dropoff_lat, dropoff_lon,
            vehicle_type
        )
        
        # 2. Create trip record
        trip_id = await db.fetch_val(
            """
            INSERT INTO trips (
                rider_id, pickup_location, dropoff_location,
                vehicle_type, status, base_fare, surge_multiplier, final_fare
            )
            VALUES (
                $1,
                ST_SetSRID(ST_MakePoint($2, $3), 4326),
                ST_SetSRID(ST_MakePoint($4, $5), 4326),
                $6, 'REQUESTED', $7, $8, $9
            )
            RETURNING id
            """,
            rider_id, pickup_lon, pickup_lat, dropoff_lon, dropoff_lat,
            vehicle_type, fare['base_fare'], fare['surge_multiplier'], fare['final_fare']
        )
        
        # 3. Find and dispatch to driver
        driver = await matching_service.find_best_driver(
            pickup_lat, pickup_lon, vehicle_type
        )
        
        if not driver:
            await self._update_trip_status(trip_id, 'NO_DRIVERS_AVAILABLE')
            raise NoDriversAvailableError()
        
        # 4. Assign driver
        await self.assign_driver(trip_id, driver['driver_id'])
        
        return {
            'trip_id': str(trip_id),
            'driver': driver,
            'estimated_fare': fare['final_fare'],
            'surge_multiplier': fare['surge_multiplier']
        }
    
    async def assign_driver(self, trip_id: UUID, driver_id: UUID):
        """Assign driver to trip"""
        
        await db.execute(
            """
            UPDATE trips
            SET driver_id = $1,
                status = 'DRIVER_ASSIGNED',
                driver_assigned_at = NOW()
            WHERE id = $2
            """,
            driver_id, trip_id
        )
        
        # Mark driver as unavailable
        await redis.set(f'driver:{driver_id}:available', '0')
        
        # Log event
        await self._log_trip_event(trip_id, 'DRIVER_ASSIGNED', {
            'driver_id': str(driver_id)
        })
        
        # Notify rider
        await notification_service.send_push(
            rider_id,
            {
                'type': 'driver_assigned',
                'driver_name': '...',
                'vehicle': '...',
                'eta_minutes': 5
            }
        )
    
    async def start_trip(self, trip_id: UUID, driver_id: UUID):
        """Driver starts trip (rider picked up)"""
        
        await db.execute(
            """
            UPDATE trips
            SET status = 'IN_PROGRESS',
                trip_started_at = NOW()
            WHERE id = $1 AND driver_id = $2
            """,
            trip_id, driver_id
        )
        
        await self._log_trip_event(trip_id, 'TRIP_STARTED', {})
    
    async def complete_trip(
        self,
        trip_id: UUID,
        driver_id: UUID,
        actual_distance_km: float,
        route_polyline: str
    ):
        """Complete trip"""
        
        # Calculate actual duration
        trip = await db.fetch_one(
            "SELECT trip_started_at FROM trips WHERE id = $1",
            trip_id
        )
        
        duration_min = (datetime.now() - trip['trip_started_at']).seconds // 60
        
        # Update trip
        await db.execute(
            """
            UPDATE trips
            SET status = 'COMPLETED',
                trip_completed_at = NOW(),
                actual_distance_km = $1,
                actual_duration_min = $2,
                route_polyline = $3
            WHERE id = $4
            """,
            actual_distance_km, duration_min, route_polyline, trip_id
        )
        
        # Mark driver available
        await redis.set(f'driver:{driver_id}:available', '1')
        
        # Process payment
        await payment_service.process_trip_payment(trip_id)
        
        await self._log_trip_event(trip_id, 'TRIP_COMPLETED', {
            'distance_km': actual_distance_km,
            'duration_min': duration_min
        })
```

---

## Payment Processing

### Payment Flow

```
1. Rider adds payment method (Stripe)
2. Trip completed
3. Charge rider
4. Hold driver payout (7 days)
5. Transfer to driver (minus commission)
```

### Implementation

```python
import stripe

class PaymentService:
    async def process_trip_payment(self, trip_id: UUID):
        """Charge rider and schedule driver payout"""
        
        # Get trip details
        trip = await db.fetch_one(
            """
            SELECT 
                t.rider_id,
                t.driver_id,
                t.final_fare,
                r.default_payment_method_id
            FROM trips t
            JOIN riders r ON r.user_id = t.rider_id
            WHERE t.id = $1
            """,
            trip_id
        )
        
        # Get payment method
        payment_method = await db.fetch_one(
            "SELECT stripe_payment_method_id FROM payment_methods WHERE id = $1",
            trip['default_payment_method_id']
        )
        
        # Charge rider
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(trip['final_fare'] * 100),  # Convert to cents
                currency='usd',
                payment_method=payment_method['stripe_payment_method_id'],
                confirm=True,
                metadata={'trip_id': str(trip_id)}
            )
            
            # Record payment
            await db.execute(
                """
                INSERT INTO payments (
                    trip_id, user_id, amount, status, stripe_payment_intent_id
                )
                VALUES ($1, $2, $3, 'completed', $4)
                """,
                trip_id, trip['rider_id'], trip['final_fare'], payment_intent.id
            )
            
            # Update trip
            await db.execute(
                "UPDATE trips SET status = 'PAID' WHERE id = $1",
                trip_id
            )
            
            # Schedule driver payout (80% of fare, 20% commission)
            driver_amount = trip['final_fare'] * 0.80
            await self._schedule_driver_payout(
                trip['driver_id'],
                driver_amount,
                trip_id
            )
            
        except stripe.error.CardError as e:
            # Handle payment failure
            await self._handle_payment_failure(trip_id, str(e))
    
    async def _schedule_driver_payout(
        self,
        driver_id: UUID,
        amount: Decimal,
        trip_id: UUID
    ):
        """Schedule payout to driver (7-day hold)"""
        
        payout_date = datetime.now() + timedelta(days=7)
        
        await db.execute(
            """
            INSERT INTO driver_payouts (
                driver_id, trip_id, amount, status, scheduled_at
            )
            VALUES ($1, $2, $3, 'pending', $4)
            """,
            driver_id, trip_id, amount, payout_date
        )
```

---

## Scaling for Large Cities

### Horizontal Scaling Strategies

#### 1. Geographic Sharding

```python
# Shard by city/region
SHARDS = {
    'us-west': {
        'cities': ['san_francisco', 'los_angeles', 'seattle'],
        'db': 'postgresql://us-west-db:5432/rideshare',
        'redis': 'redis://us-west-redis:6379'
    },
    'us-east': {
        'cities': ['new_york', 'boston', 'miami'],
        'db': 'postgresql://us-east-db:5432/rideshare',
        'redis': 'redis://us-east-redis:6379'
    }
}

def get_shard_for_location(lat: float, lon: float) -> str:
    """Route request to appropriate shard"""
    city = geocode_to_city(lat, lon)
    for shard_name, config in SHARDS.items():
        if city in config['cities']:
            return shard_name
    return 'default'
```

#### 2. Microservices Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ User Service │  │Location Svc  │  │Matching Svc  │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
                    Message Bus
                    (Kafka/RabbitMQ)
```

#### 3. Database Optimization

**Read Replicas**:
```python
# Write to master
await master_db.execute("INSERT INTO trips ...")

# Read from replica
trips = await replica_db.fetch_all("SELECT * FROM trips WHERE rider_id = $1")
```

**Partitioning**:
```sql
-- Partition trips by month
CREATE TABLE trips_2024_01 PARTITION OF trips
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE trips_2024_02 PARTITION OF trips
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### 4. Caching Strategy

```python
# Multi-level caching
class CacheService:
    async def get_driver_info(self, driver_id: UUID):
        # L1: In-memory cache
        if driver_id in memory_cache:
            return memory_cache[driver_id]
        
        # L2: Redis cache
        cached = await redis.get(f'driver:{driver_id}')
        if cached:
            return json.loads(cached)
        
        # L3: Database
        driver = await db.fetch_one(
            "SELECT * FROM drivers WHERE user_id = $1",
            driver_id
        )
        
        # Populate caches
        await redis.setex(f'driver:{driver_id}', 3600, json.dumps(driver))
        memory_cache[driver_id] = driver
        
        return driver
```

#### 5. Load Balancing

```nginx
# Nginx configuration
upstream api_servers {
    least_conn;  # Route to server with fewest connections
    server api1.rideshare.com:8000 weight=3;
    server api2.rideshare.com:8000 weight=3;
    server api3.rideshare.com:8000 weight=2;
}

server {
    listen 80;
    location /api/ {
        proxy_pass http://api_servers;
    }
}
```

### Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| **Location Update Latency** | < 100ms | WebSocket, Redis Geo |
| **Driver Matching Time** | < 2 seconds | Geohashing, Caching |
| **API Response Time (p99)** | < 500ms | Load balancing, CDN |
| **Concurrent Users** | 1M+ | Horizontal scaling |
| **Trips per Second** | 10,000+ | Sharding, Async processing |

---

## Summary

This ride-sharing backend provides:

✅ **User Management** - Rider/driver registration with verification  
✅ **Real-Time Tracking** - WebSocket + Redis Geo for live locations  
✅ **Smart Matching** - Multi-factor algorithm for optimal pairing  
✅ **Dynamic Pricing** - Surge pricing based on supply/demand  
✅ **Trip Management** - Complete lifecycle with state machine  
✅ **Payment Processing** - Stripe integration with driver payouts  
✅ **Massive Scale** - Geographic sharding, caching, load balancing  

**Architecture Highlights**:
- Microservices for independent scaling
- Redis for real-time operations
- PostgreSQL for transactional data
- Kafka for event streaming
- WebSocket for live updates
- Geospatial indexing for location queries

**Scaling Capabilities**:
- Handle millions of concurrent users
- Process 10,000+ trips per second
- Sub-second driver matching
- Real-time location tracking
- Multi-region deployment
