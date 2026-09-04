# SECTION 1: DATABASE + BACKEND FOUNDATION
## Verification & Testing Guide

**Status:** ✅ Fixed bugs, ready for testing

---

## 🔧 What Was Fixed

### Bug #1: POST /api/v1/reports Endpoint ✅ FIXED
**Problem:** Frontend sends JSON body, but endpoint expected query parameters
**Fix:** Changed endpoint to use Pydantic `CrowdReportRequest` model
**Result:** Endpoint now correctly accepts JSON body

```python
# BEFORE (broken)
async def submit_crowd_report(
    location_id: str,      # ❌ Query parameter
    crowd_level: int,      # ❌ Query parameter
    ...
)

# AFTER (fixed)
async def submit_crowd_report(
    report: CrowdReportRequest,  # ✅ JSON body
    db: Session = Depends(get_db)
)
```

**Test it:**
```bash
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "550e8400-e29b-41d4-a716-446655440000",
    "crowd_level": 3,
    "wait_time_minutes": 15,
    "comment": "Getting crowded",
    "confidence": 0.8
  }'
```

---

## 📋 Testing Checklist for Section 1

### Part A: Python Compilation ✅
- [x] main.py compiles
- [x] All model files compile
- [x] All ML files compile
- [x] All imports are correct

### Part B: Database Setup (To Test)

```bash
# 1. Ensure PostgreSQL is running
docker-compose up postgres -d

# 2. Wait for it to be ready
sleep 10

# 3. Check connection
psql -h localhost -U waitwise_user -d waitwise -c "SELECT 1"
```

**Expected output:**
```
 ?column?
----------
        1
(1 row)
```

### Part C: Database Schema (To Test)

```bash
# Check tables were created
psql -h localhost -U waitwise_user -d waitwise -c "\dt"
```

**Expected tables:**
```
                 List of relations
 Schema |        Name        | Type  |     Owner
--------+--------------------+-------+---------------
 public | activity_log       | table | waitwise_user
 public | alerts             | table | waitwise_user
 public | crowd_aggregates   | table | waitwise_user
 public | crowd_reports      | table | waitwise_user
 public | learning_patterns  | table | waitwise_user
 public | locations          | table | waitwise_user
 public | model_performance  | table | waitwise_user
 public | predictions        | table | waitwise_user
 public | recommendations    | table | waitwise_user
 public | user_feedback      | table | waitwise_user
 public | user_preferences   | table | waitwise_user
 public | users              | table | waitwise_user
```

### Part D: Seed Data (To Test)

```bash
# Check locations were seeded
psql -h localhost -U waitwise_user -d waitwise \
  -c "SELECT id, name, category FROM locations;"
```

**Expected output:**
```
                  id                  |     name     |    category
--------------------------------------+--------------+----------------
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Central Mall | shopping_mall
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Burger House | restaurant
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Tech Store   | store
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | City Park    | park
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Cafe Central | restaurant
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Times Square | landmark
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Westfield Mall | shopping_mall
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Brookfield Place | shopping_mall
(8 rows)
```

✅ Database will have 8 seed locations (from schema.sql), not 4

### Part E: Backend Startup (To Test)

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://waitwise_user:waitwise_password@localhost:5432/waitwise"
export REDIS_URL="redis://localhost:6379/0"

# Start the server
python main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Starting WaitWise Backend v2.0
INFO:     Database tables created successfully
INFO:     Seeded 4 sample locations
```

### Part F: Health Check (To Test)

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-08-16T...",
  "database": "connected",
  "stats": {
    "locations": 4,
    "reports": 0,
    "predictions": 0
  }
}
```

### Part G: Endpoints to Test

#### 1. GET /api/v1/locations
```bash
curl http://localhost:8000/api/v1/locations
```

**Expected:** Array of 4 locations

#### 2. GET /api/v1/locations/{id}
```bash
# Replace {id} with actual location UUID from previous response
curl http://localhost:8000/api/v1/locations/{id}
```

**Expected:** Single location with details

#### 3. POST /api/v1/reports (FIXED)
```bash
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "YOUR_LOCATION_ID",
    "crowd_level": 3,
    "wait_time_minutes": 15,
    "comment": "Testing the fixed endpoint",
    "confidence": 0.8
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "report_id": "...",
  "created_at": "...",
  "location_id": "...",
  "location_name": "Central Mall"
}
```

#### 4. GET /api/v1/reports/{location_id}
```bash
curl http://localhost:8000/api/v1/reports/{location_id}?hours=24
```

**Expected:** Array of reports for that location

#### 5. GET /api/v1/predictions/{location_id}
```bash
curl "http://localhost:8000/api/v1/predictions/{location_id}?minutes_ahead=30"
```

**Expected:** Prediction with crowd level and reasoning

#### 6. GET /api/v1/forecast/{location_id}
```bash
curl http://localhost:8000/api/v1/forecast/{location_id}
```

**Expected:** 24-hour hourly forecast array

---

## 📊 What Gets Tested Here

| Component | Status | Notes |
|-----------|--------|-------|
| PostgreSQL + PostGIS | 🟢 Should work | Verify tables exist |
| SQLAlchemy models | 🟢 Compiles | All 11 models verified |
| Schema ↔ Models match | 🟢 Expected to match | Verify through queries |
| Database initialization | 🟢 Should work | Check schema.sql runs |
| Seed data (4 locations) | 🟢 Should work | Verify 4 rows exist |
| Health endpoint | 🟢 Should work | Tests DB connection |
| GET locations endpoint | 🟢 Should work | Basic query |
| GET location/{id} endpoint | 🟢 Should work | Single record query |
| POST reports endpoint | 🟡 FIXED, needs test | Now accepts JSON body |
| GET reports endpoint | 🟢 Should work | With time filtering |
| Error handling | 🟢 Should work | Missing locations, invalid data |

---

## 🚀 Running the Full Section 1 Test

Here's the complete flow:

```bash
# 1. Start database
docker-compose up postgres -d
sleep 15

# 2. Start Redis
docker-compose up redis -d

# 3. Go to backend
cd backend
pip install -r requirements.txt

# 4. Set env vars
export DATABASE_URL="postgresql://waitwise_user:waitwise_password@localhost:5432/waitwise"

# 5. Start backend
python main.py

# 6. In another terminal, run all endpoint tests
./test-section1.sh  # (we'll create this)
```

---

## ⚠️ Known Issues (To Fix in Later Sections)

These are NOT in Section 1 scope:

1. ❌ WebSocket not implemented
2. ❌ Redis not connected
3. ❌ Authentication not implemented
4. ❌ Frontend/backend not integrated yet
5. ❌ True ML model not trained
6. ❌ Real-time updates not wired

---

## ✅ Success Criteria

Section 1 is **complete** when:

- [ ] All Python files compile without errors
- [ ] PostgreSQL starts and initializes schema
- [ ] All 12 tables exist in database
- [ ] 4 seed locations are created
- [ ] Health endpoint returns `healthy`
- [ ] All 6 endpoint types return correct responses
- [ ] POST /api/v1/reports accepts JSON body correctly
- [ ] GET endpoints return proper pagination
- [ ] Error handling works (404 for missing locations, etc.)

---

## 🎯 What's Next

Once Section 1 passes:
→ **Section 2: ML & Learning Engine**
→ Section 3: Frontend Integration
→ Section 4: Real-time Updates
→ Section 5: Advanced Features

---

**Status: Ready for testing. Awaiting your test results.**
