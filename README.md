# 🎯 AI Interview Coach

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live_Demo-black?style=flat&logo=vercel)](https://ai-interview-coach-eight-xi.vercel.app)
[![GitHub Repository](https://img.shields.io/badge/GitHub-ai--interview--coach-blue?style=flat&logo=github)](https://github.com/Krishlayy/ai-interview-coach)

> **Live Production Demo**: [https://ai-interview-coach-eight-xi.vercel.app](https://ai-interview-coach-eight-xi.vercel.app)

A production-grade AI-powered interview preparation platform built with Python, Streamlit, and Llama 3.3-70B via Groq API.

---

## Features

- **AI-Driven Interviews** — Contextual questions that progressively increase in difficulty
- **Real-Time Scoring** — Live feedback on Technical, Communication, Problem Solving, Confidence, Completeness
- **5 Target Roles** — Software Engineer, Python Developer, Full Stack Developer, AI Engineer, Data Analyst
- **3 Difficulty Levels** — Beginner, Intermediate, Advanced
- **Resume-Based Questions** — Upload a PDF to get personalized questions from your projects and skills
- **Detailed Reports** — Strengths, weaknesses, hiring recommendation, and improvement roadmap
- **Performance Analytics** — Charts tracking growth over time across all dimensions
- **Full Interview History** — Persistent SQLite storage with per-question breakdowns

---

## Tech Stack

| Layer      | Technology            |
|------------|-----------------------|
| Frontend   | Streamlit + Plotly    |
| AI Model   | Llama 3.3-70B (Groq)  |
| Backend    | Python 3.10+          |
| Database   | SQLite                |
| Resume     | pdfplumber            |
| Env Mgmt   | python-dotenv         |

---

## Setup

### 1. Clone & Install

```bash
git clone <repo-url>
cd ai-interview-coach
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=gsk_your_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com).

### 3. Run Locally

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## Folder Structure

```
ai-interview-coach/
├── app.py                    # Entry point — layout, CSS, routing
├── pages/
│   ├── interview.py          # Interview session (setup → active → report)
│   ├── dashboard.py          # KPI cards + analytics charts
│   └── reports.py            # Historical reports + Q&A drilldown
├── services/
│   ├── ai_service.py         # Groq API client with retry logic
│   ├── evaluation_service.py # Answer scoring engine
│   ├── interview_service.py  # Question generation + report generation
│   └── resume_service.py     # PDF parsing + skill extraction
├── database/
│   └── database.py           # SQLite schema + all query helpers
├── prompts/
│   ├── interviewer_prompt.txt  # System prompt for question generation
│   └── evaluator_prompt.txt    # System prompt for answer evaluation
├── data/                     # Auto-created — SQLite DB lives here
├── requirements.txt
├── .env.example
└── README.md
```

---

## Deployment — Streamlit Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set the main file to `app.py`
5. Under **Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
6. Deploy

> **Note:** SQLite data is ephemeral on Streamlit Cloud. For persistent storage in production, swap the database layer for PostgreSQL (Supabase free tier works well).

---

## Environment Variables

| Variable      | Required | Description                    |
|---------------|----------|--------------------------------|
| GROQ_API_KEY  | ✅ Yes   | Your Groq API key              |
| APP_ENV       | No       | `development` or `production`  |
| LOG_LEVEL     | No       | `DEBUG`, `INFO`, `WARNING`     |

---

## Production Improvements Roadmap

### Phase 1 — Auth & Multi-User
- [ ] Add Google OAuth via `streamlit-oauth` or Auth0
- [ ] Replace session-based IDs with proper user accounts
- [ ] Role-based access for team/enterprise use

### Phase 2 — Storage & Scalability
- [ ] Migrate SQLite → PostgreSQL (Supabase / Neon)
- [ ] Add Redis caching for AI responses
- [ ] Store resume PDFs in S3/Cloudflare R2

### Phase 3 — Advanced AI Features
- [ ] Voice interview mode (Whisper API + TTS)
- [ ] Code execution sandbox for coding questions
- [ ] Mock technical screen share simulation
- [ ] Custom interview templates by company (FAANG, startups)

### Phase 4 — Analytics & Monetization
- [ ] Stripe billing integration for premium tier
- [ ] Team dashboard for bootcamps / universities
- [ ] Candidate comparison analytics
- [ ] Export reports as PDF

### Phase 5 — Infrastructure
- [ ] Rate limiting per user (token bucket)
- [ ] Background job queue (Celery + Redis) for report generation
- [ ] Docker + Kubernetes deployment config
- [ ] Monitoring with Sentry + Prometheus
