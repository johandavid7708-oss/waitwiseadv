# WaitWise v2.0

**A predictive human-flow intelligence platform that learns and improves continuously.**

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Version](https://img.shields.io/badge/Version-2.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 What is WaitWise?

WaitWise predicts where people will be, when congestion will happen, and what the smartest alternative is **before you waste time**.

**Core Features:**
- 🔮 **AI-Powered Predictions** - ML-based crowd forecasting
- 🧠 **Self-Learning System** - Improves accuracy continuously from real data
- 📍 **Smart Recommendations** - Suggests better locations based on your preferences
- 🗺️ **Crowd Heatmap** - Real-time visualization of human flow
- 📊 **Analytics & Insights** - Peak times, trends, and patterns
- 🔔 **Smart Alerts** - Get notified when conditions improve
- 👥 **Community Reports** - Verified crowd levels from users

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone <repository-url>
cd waitwise-v2

# Start all services
docker-compose up -d

# Wait for services to initialize
sleep 30

# Access the application
open http://localhost:3000

# Backend API docs
open http://localhost:8000/docs
```

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with PostGIS
- Redis 7+

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/waitwise"
export REDIS_URL="redis://localhost:6379/0"

# Run migrations and start server
python main.py
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

---

## 📁 Project Structure

```
waitwise-v2/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # FastAPI application
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── location.py         # Location data model
│   │   ├── user.py             # User & preferences
│   │   ├── crowd.py            # Crowd reports & aggregates
│   │   ├── prediction.py       # Predictions & patterns
│   │   ├── recommendation.py   # Recommendations
│   │   ├── alert.py            # Alerts & notifications
│   │   ├── feedback.py         # Feedback & performance
│   │   └── activity.py         # Activity logging
│   ├── ml/                     # Machine learning
│   │   ├── predictor.py        # Prediction engine
│   │   └── learner.py          # Self-learning system
│   ├── database/               # Database setup
│   │   └── schema.sql          # PostgreSQL schema
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Backend container
│
├── frontend/                   # Next.js React frontend
│   ├── app/                    # Next.js app directory
│   │   ├── page.tsx            # Main dashboard
│   │   ├── layout.tsx          # Root layout
│   │   └── globals.css         # Global styles
│   ├── components/             # React components
│   │   ├── HeatmapMap.tsx      # Crowd heatmap visualization
│   │   ├── PredictionPanel.tsx # AI predictions
│   │   ├── RecommendationEngine.tsx
│   │   ├── WaitWiseDashboard.tsx
│   │   └── RealTimeUpdates.tsx
│   ├── package.json            # Dependencies
│   ├── tsconfig.json           # TypeScript config
│   ├── tailwind.config.js      # Tailwind CSS
│   └── Dockerfile              # Frontend container
│
├── docker-compose.yml          # Docker orchestration
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🏗️ Architecture

### Backend Stack
- **Framework:** FastAPI with async/await
- **Database:** PostgreSQL + PostGIS (geospatial)
- **Cache:** Redis for real-time data
- **ORM:** SQLAlchemy 2.0
- **ML:** NumPy, scikit-learn, pandas
- **Auth:** JWT tokens (optional)

### Frontend Stack
- **Framework:** Next.js 14 with App Router
- **UI:** React 18 with TypeScript
- **Styling:** Tailwind CSS
- **State:** React hooks
- **API:** Fetch API with real-time updates

### Database Schema
**8 Core Tables:**
1. `locations` - Places to monitor
2. `users` - User accounts & profiles
3. `crowd_reports` - User-submitted data
4. `predictions` - ML-generated forecasts
5. `learning_patterns` - Historical patterns
6. `recommendations` - Smart alternatives
7. `alerts` - User notifications
8. `feedback` - User ratings & ML training

**Plus 5 support tables** for analytics, activity logging, and model performance tracking.

---

## 🤖 ML & Learning System

### Prediction Engine
The `CrowdPredictionEngine` combines:
1. **Historical Patterns** - Learned from past crowd data
2. **Trend Analysis** - Real-time crowd direction
3. **Time-of-Day Adjustments** - Peak hour detection
4. **Anomaly Detection** - Identifies unusual situations
5. **Confidence Scoring** - Measures prediction reliability

### Self-Learning System
The `SelfLearningSystem` continuously:
1. **Learns from Reports** - Updates patterns with new data
2. **Verifies Predictions** - Calculates accuracy
3. **Processes Feedback** - Improves from user ratings
4. **Tracks Performance** - Measures model accuracy
5. **Adapts Weights** - Uses exponential moving averages

---

## 📡 API Endpoints

### Locations
- `GET /api/v1/locations` - Get all locations
- `GET /api/v1/locations/{id}` - Get location details

### Predictions
- `GET /api/v1/predictions/{location_id}` - Get crowd prediction
- `GET /api/v1/forecast/{location_id}` - Get 24-hour forecast

### Reports
- `POST /api/v1/reports` - Submit crowd report
- `GET /api/v1/reports/{location_id}` - Get recent reports

### Recommendations
- `POST /api/v1/recommendations` - Get smart alternatives

### Learning
- `POST /api/v1/learning/run-cycle` - Trigger learning cycle
- `POST /api/v1/feedback` - Submit prediction feedback

### Analytics
- `GET /api/v1/analytics/{location_id}` - Get location analytics

### System
- `GET /health` - Health check

---

## 🔐 Security Considerations

**Current Implementation:**
- CORS enabled for all origins (development)
- No authentication required
- All data treated as public

**Production Recommendations:**
1. Enable JWT authentication
2. Restrict CORS to specific origins
3. Rate limiting on API endpoints
4. Input validation & sanitization
5. Database encryption at rest
6. HTTPS only in production
7. API key rotation
8. Audit logging

---

## 📊 Data Flow

```
User Reports
    ↓
CrowdReport (database)
    ↓
SelfLearningSystem
    ↓
Learning Patterns Updated
    ↓
PredictionEngine
    ↓
Predictions Generated
    ↓
Frontend Display
    ↓
User gets Smart Recommendations
```

---

## 🧪 Testing & Validation

### Manual Testing Checklist
- [ ] Backend health check: `curl http://localhost:8000/health`
- [ ] Get locations: `curl http://localhost:8000/api/v1/locations`
- [ ] Get prediction: `curl http://localhost:8000/api/v1/predictions/{id}`
- [ ] Submit report: `curl -X POST http://localhost:8000/api/v1/reports ...`
- [ ] Frontend loads: `http://localhost:3000`
- [ ] Can view locations
- [ ] Can submit reports
- [ ] Can see predictions
- [ ] Can get recommendations

---

## 🔄 Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Docker Compose (Production)
Update `docker-compose.yml`:
- Set `NODE_ENV=production` and `ENV=production`
- Use health checks
- Set resource limits
- Configure logging

### Kubernetes (Enterprise)
Create manifests for:
- PostgreSQL StatefulSet
- Redis Deployment
- Backend Deployment with HPA
- Frontend Deployment

---

## 📈 Performance Tips

1. **Database:**
   - Add indexes on frequently queried columns
   - Vacuum PostgreSQL regularly
   - Archive old data

2. **Frontend:**
   - Use code splitting
   - Optimize images
   - Enable caching headers

3. **Backend:**
   - Cache frequently accessed data in Redis
   - Batch API requests
   - Implement rate limiting

---

## 🐛 Troubleshooting

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Verify connection string
echo $DATABASE_URL

# Connect to database
psql "postgresql://user:pass@localhost/waitwise"
```

### Backend Doesn't Start
```bash
# Check logs
docker logs waitwise-backend

# Verify Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi
```

### Frontend Shows "Connection Error"
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check frontend API URL
echo $NEXT_PUBLIC_API_URL
```

---

## 📚 Documentation

- **Backend:** See docstrings in Python files
- **Frontend:** Check React component prop types
- **API:** View interactive docs at http://localhost:8000/docs
- **Database:** Review schema in `backend/database/schema.sql`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass
5. Submit a pull request

---

## 📝 License

MIT License - See LICENSE file for details

---

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at `/docs`

---

## 🙏 Acknowledgments

- FastAPI for the backend framework
- Next.js for the frontend
- PostgreSQL + PostGIS for spatial data
- The open-source community

---

**Happy prediciting! Know before you go.** 🎯
