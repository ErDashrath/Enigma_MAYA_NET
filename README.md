# Enigma_MAYA_NET
team:
Dashrath Parekar
Kartik Shukla
Tulasi Desai
Vignesh Anil Thandessary
ps:vitalCircle
# VitalCircle – Predictive Chronic Care Ecosystem  

## 🚑 Problem Statement  
Current chronic care platforms are **reactive** and burden patients with manual logging while clinicians drown in raw data. Patients often don’t get predictive support until a crisis happens.  

**VitalCircle** solves this by providing:  
- **Predictive AI Stability Score** (forecasts health risks).  
- **Context-aware nudges** (personalized lifestyle suggestions).  
- **Clinician portal** (risk overview + suggested protocols).  
- **Dashboard** (visual health trends, goals, and progress).  

---

## ⚙️ Tech Stack  
- **Backend**: Django + Django Ninja (API)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT tokens
- **Frontend**: React + TailwindCSS + DaisyUI  
- **AI**: webLLM with small quantized LLM (for predictions & nudges)  
- **Deployment**: Vercel  

---

## ✨ Features (Hackathon Build)  
- Patient dashboard with vitals input (BP, HR, stress, sodium intake).  
- **Stability Score Engine** → predicts risk % (rule-based + LLM).  
- AI-generated **nudges** for lifestyle support.  
- Clinician portal with patient risk list & suggested protocols.  
- Visual graphs for vitals & Stability Score trends.  
- (Optional) Community forum & gamified progress tracking.  

---

## 🚀 Quick Start  

### Prerequisites
- Python 3.11+ 
- Node.js 18+ (for WebLLM frontend integration)
- Git
- PostgreSQL (or Supabase account)

### Backend Setup (Django + Supabase)

1. **Clone the repository:**
```bash
git clone https://github.com/ErDashrath/Enigma_MAYA_NET.git
cd Enigma_MAYA_NET
```

2. **Set up Python environment:**
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database and configuration settings:
# - DATABASE_URL: Your Supabase/PostgreSQL connection string
# - SECRET_KEY: Django secret key (generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - JWT_SECRET_KEY: JWT signing key
# - SUPABASE_URL and SUPABASE_KEY: From your Supabase project settings
```

4. **Run migrations:**
```bash
python manage.py migrate
python manage.py createsuperuser  # optional
```

5. **Start development server:**
```bash
python manage.py runserver
```

### Frontend & WebLLM Setup

The project includes WebLLM integration for local AI processing. For detailed setup:

- **WebLLM Implementation**: See [WEBLLM_IMPLEMENTATION_GUIDE.md](WEBLLM_IMPLEMENTATION_GUIDE.md)
- **Dependencies**: See [WEBLLM_DEPENDENCIES.md](WEBLLM_DEPENDENCIES.md)  
- **Integration Guide**: See [WEBLLM_INTEGRATION.md](WEBLLM_INTEGRATION.md)
- **Mental Health Model**: See [MINDMENDERS_MODEL_SETUP.md](MINDMENDERS_MODEL_SETUP.md)

**Quick Frontend Setup:**
```bash
# The WebLLM service is included in backend/static/js/
# Access the test interface at: http://127.0.0.1:8000/webllm-test/
# No additional frontend build required for basic functionality
```

### Troubleshooting

**Common Issues:**

1. **Database Connection Errors:**
   ```bash
   # Check your DATABASE_URL in .env
   # For local PostgreSQL: postgresql://username:password@localhost:5432/dbname
   # For Supabase: Get connection string from Project Settings > Database
   ```

2. **Migration Errors:**
   ```bash
   # Reset migrations if needed
   python manage.py migrate --fake-initial
   ```

3. **Import Errors:**
   ```bash
   # Ensure all dependencies are installed
   pip install -r requirements.txt
   
   # Check Python version compatibility
   python --version  # Should be 3.11+
   ```

4. **WebLLM Issues:**
   - Ensure browser supports WebGPU (Chrome 113+, Edge 113+)
   - Check browser developer console for WebLLM errors
   - See [WEBLLM_DEPENDENCIES.md](WEBLLM_DEPENDENCIES.md) for detailed troubleshooting

### API Endpoints

**Core API:**
- `GET /api/health` - Health check endpoint
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT token)
- `GET /api/auth/me` - Get current user profile (requires JWT)
- `GET /api/docs` - Interactive API documentation (Swagger UI)

**Patient & Health Data:**
- `POST /api/vitals/` - Record vital signs (BP, HR, stress, sodium)
- `GET /api/vitals/` - Get patient vital history
- `GET /api/stability-score/` - Get AI-calculated stability scores
- `GET /api/nudges/` - Get personalized health recommendations

**Clinician Portal:**
- `GET /api/clinicians/patients/` - List assigned patients
- `GET /api/clinicians/dashboard/` - Clinician dashboard data
- `POST /api/clinical-notes/` - Create clinical notes

**Access the API documentation at:** `http://127.0.0.1:8000/api/docs` after starting the server.

---

## 📚 Additional Documentation

- [WebLLM Implementation Guide](WEBLLM_IMPLEMENTATION_GUIDE.md) - Comprehensive WebLLM setup and usage
- [WebLLM Dependencies](WEBLLM_DEPENDENCIES.md) - Dependency management and requirements
- [WebLLM Integration](WEBLLM_INTEGRATION.md) - Integration patterns and best practices  
- [MindMenders Model Setup](MINDMENDERS_MODEL_SETUP.md) - Mental health chatbot model configuration

## 🧪 Testing

```bash
# Run basic connection tests
python test_connection.py

# Test JWT authentication
python test_jwt.py

# Test API integration
python test_api_integration.py

# Create test data
python create_test_data.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## 📄 License

This project is part of the Enigma Hackathon 2025.

## 👥 Team

**MAYA_NET Team:**
- Dashrath Parekar
- Kartik Shukla  
- Tulasi Desai
- Vignesh Anil Thandessary

**Event:** Enigma Hackathon 2025  
**Project:** VitalCircle - Predictive Chronic Care Ecosystem
