# Ride-Sharing Backend

> Complete FastAPI-based ride-sharing platform like Uber

## Features

✅ **Rider & Driver Registration** - Phone verification, profiles  
✅ **Real-Time Location Tracking** - WebSocket + Redis Geo  
✅ **Smart Matching** - Multi-factor driver-rider pairing  
✅ **Surge Pricing** - Dynamic pricing based on supply/demand  
✅ **Trip Management** - Complete lifecycle (request → complete)  
✅ **Payment Integration** - Stripe-ready payment processing  
✅ **Scalable Architecture** - Microservices, horizontal scaling  

## Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f rideshare-api

# Access API docs
open http://localhost:8000/docs
```

## API Endpoints

### Trip Management

```bash
# Request a ride
POST /api/v1/trips/request
{
  "pickup_location": {"lat": 37.7749, "lon": -122.4194},
  "dropoff_location": {"lat": 37.7849, "lon": -122.4094},
  "vehicle_type": "sedan"
}

# Start trip
POST /api/v1/trips/{trip_id}/start

# Complete trip
POST /api/v1/trips/{trip_id}/complete?actual_distance_km=5.2
```

### Pricing

```bash
# Get fare estimate
POST /api/v1/pricing/estimate
{
  "pickup": {"lat": 37.7749, "lon": -122.4194},
  "dropoff": {"lat": 37.7849, "lon": -122.4094},
  "vehicle_type": "sedan"
}
```

### Driver Location

```bash
# Update location (HTTP)
POST /api/v1/driver/location
{
  "lat": 37.7749,
  "lon": -122.4194
}

# Go online
POST /api/v1/driver/online

# WebSocket connection
ws://localhost:8000/ws/driver/{driver_id}
```

### Registration

```bash
# Register rider
POST /api/v1/auth/register/rider
{
  "phone_number": "+1234567890",
  "full_name": "John Doe",
  "email": "john@example.com",
  "user_type": "rider"
}

# Register driver
POST /api/v1/auth/register/driver
{
  "phone_number": "+1234567890",
  "full_name": "Jane Driver",
  "email": "jane@example.com",
  "vehicle_type": "sedan",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_year": 2020,
  "vehicle_color": "Black",
  "license_plate": "ABC123",
  "drivers_license_number": "DL123456",
  "drivers_license_expiry": "2025-12-31T00:00:00"
}
```

## Architecture

```
Client Apps → API Gateway → Services → Databases
                              ↓
                        Redis + PostgreSQL
```

### Services

- **Trip Service** - Ride lifecycle management
- **Location Service** - Real-time GPS tracking
- **Matching Service** - Driver-rider pairing
- **Pricing Service** - Fare calculation + surge

### Technology Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL + PostGIS
- **Cache**: Redis (Geo queries)
- **WebSocket**: Real-time updates
- **Container**: Docker

## Project Structure

```
rideshare-backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Config (database, redis)
│   ├── models/           # SQLAlchemy + Pydantic
│   ├── services/         # Business logic
│   └── main.py           # FastAPI app
├── database/
│   └── init.sql          # Database setup
├── docs/
│   └── SYSTEM_DESIGN.md  # Complete design doc
├── docker-compose.yml    # Docker setup
├── Dockerfile
└── requirements.txt
```

## Key Features

### 1. Real-Time Location Tracking

```python
# WebSocket connection for continuous updates
ws = websocket.connect(f"ws://localhost:8000/ws/driver/{driver_id}")

# Send location every 5 seconds
ws.send(json.dumps({"lat": 37.7749, "lon": -122.4194}))
```

### 2. Driver-Rider Matching

Multi-factor scoring:
- Distance (50%)
- Driver rating (30%)
- Acceptance rate (20%)

### 3. Surge Pricing

```
Surge = 1.0 + (Demand / Supply) × 0.5
Capped at 3.0x
```

### 4. Trip Lifecycle

```
REQUESTED → DRIVER_ASSIGNED → IN_PROGRESS → COMPLETED
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# Run tests
pytest tests/
```

## API Documentation

Interactive docs: http://localhost:8000/docs

## Scaling

- **Geographic Sharding** - Shard by city/region
- **Read Replicas** - Scale database reads
- **Caching** - Redis for hot data
- **Load Balancing** - Multiple API instances

## License

MIT
