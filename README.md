# Enigma_MAYA_NET

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

### Backend Setup (Django + Supabase)

1. **Clone the repository:**
```bash
git clone https://github.com/ErDashrath/Enigma_MAYA_NET.git
cd Enigma_MAYA_NET
```

2. **Set up Python environment:**
```bash
cd backend
python -m venv ../venv
../venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
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

### API Endpoints

- `GET /api/health` - Health check
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT)
- `GET /api/auth/me` - Get current user (requires JWT)
- `GET /api/docs` - Interactive API documentation

**Team**: MAYA_NET | **Event**: Enigma Hackathon 2025
