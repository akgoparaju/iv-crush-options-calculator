# External Services Setup Guide

## Overview
The Advanced Options Trading Calculator requires **Redis** and **PostgreSQL** for full UI functionality:
- **PostgreSQL**: User authentication, portfolio tracking, data persistence
- **Redis**: Performance caching, session management

## Quick Setup with Docker

### 1. Start External Services
```bash
# Start Redis and PostgreSQL in Docker
docker-compose -f docker-compose.services.yml up -d

# Check services are running
docker-compose -f docker-compose.services.yml ps
```

### 2. Verify Services
```bash
# Test PostgreSQL connection
docker exec trade_calc_postgres pg_isready -U postgres

# Test Redis connection  
docker exec trade_calc_redis redis-cli ping
```

### 3. Start API Server
```bash
cd api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Stop Services When Done
```bash
docker-compose -f docker-compose.services.yml down
```

## Configuration

### Environment Variables (.env)
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/options_trading
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password

# Redis Configuration  
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Custom IP/Port Configuration
If you're running Docker services on different hosts/ports:

```bash
# For external Docker host
DATABASE_URL=postgresql://postgres:password@YOUR_DOCKER_IP:5432/options_trading
REDIS_URL=redis://YOUR_DOCKER_IP:6379/0

# Update corresponding HOST variables
DB_HOST=YOUR_DOCKER_IP
REDIS_HOST=YOUR_DOCKER_IP
```

## Service Endpoints
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **API Server**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

## Troubleshooting

### Port Conflicts
If ports 5432 or 6379 are already in use:
```bash
# Edit docker-compose.services.yml
# Change "5432:5432" to "5433:5432" for PostgreSQL
# Change "6379:6379" to "6380:6379" for Redis
# Update .env accordingly
```

### Connection Issues
1. Ensure Docker services are running: `docker-compose -f docker-compose.services.yml ps`
2. Check logs: `docker-compose -f docker-compose.services.yml logs`
3. Verify .env configuration matches Docker ports
4. Test connections manually using docker exec commands above

## Database Schema
The PostgreSQL database will automatically create the `options_trading` database. For full schema setup, add your SQL initialization scripts to `sql/init.sql` and uncomment the volume mapping in `docker-compose.services.yml`.