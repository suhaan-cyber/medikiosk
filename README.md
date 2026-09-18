# MEDIKOISK — Connected Health Intelligence

> A full-stack digital health platform for patients and doctors.
> Built for **Smart India Hackathon 2026 — PS ID: SIH26047**.

![Status](https://img.shields.io/badge/status-working-success)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-Vanilla%20JS-f7df1e)
![Database](https://img.shields.io/badge/database-SQLite-003b57)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 What It Does

MEDIKOISK connects **patients** and **doctors** on one platform with:

- 📅 **Smart appointments** — online or offline, digital tokens, Google Meet for video
- 💊 **E-prescriptions** — medicine schedules, dosage, timing, PDF export
- 📄 **Health records** — lab reports, X-rays, ECG uploads with image preview
- 📈 **Vitals tracking** — heart rate, BP, blood sugar, SpO₂ with history
- 💳 **UPI payments** — QR + deep-link + UTR verification
- 🤖 **AI Health Assistant** — context-aware chatbot with role-specific responses
- 🔐 **JWT authentication** — bcrypt-hashed passwords, 12h session expiry
- 👥 **Role-based access** — separate dashboards for patients and doctors

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   BROWSER                            │
│  Frontend/index.html + api.js                        │
│  ├─ Vanilla JS (no framework)                        │
│  ├─ JWT in localStorage                              │
│  ├─ AI runs 100% client-side                         │
│  └─ Talks to backend via fetch()                     │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS + JSON + Bearer token
                     ▼
┌─────────────────────────────────────────────────────┐
│              FASTAPI BACKEND                         │
│  ├─ /auth/*         → register, login, me            │
│  ├─ /bootstrap      → role-filtered data dump        │
│  ├─ /appointments   → CRUD                           │
│  ├─ /prescriptions  → CRUD                           │
│  ├─ /reports        → upload, list, delete           │
│  ├─ /payments       → UTR verification               │
│  ├─ /vitals         → health readings                │
│  └─ /change-requests → profile update workflow       │
└────────────────────┬────────────────────────────────┘
                     │ SQLAlchemy ORM
                     ▼
┌─────────────────────────────────────────────────────┐
│           SQLITE DATABASE (medikoisk.db)             │
│  users • appointments • prescriptions • reports      │
│  payments • vitals • change_requests • timeline      │
└─────────────────────────────────────────────────────┘
```

**AI:** Runs entirely in the browser. Zero external dependencies. No API keys.

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- A modern browser (Chrome, Edge, Firefox)

### 1. Clone or download the repo

```bash
git clone <your-repo-url>
cd medikiosk
```

### 2. Set up the backend

```bash
cd Backend

# Install Python dependencies
pip install -r requirements.txt

# Generate a JWT secret
python -c "import secrets; print(secrets.token_hex(32))"

# Create .env with the secret
echo JWT_SECRET=<paste-the-generated-secret-here> > .env
echo ENV=dev >> .env

# Start the server
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
[auth] ✅ JWT_SECRET loaded from environment (64 chars)
INFO:     Application startup complete.
```

### 3. Serve the frontend

**In a new terminal:**

```bash
cd Frontend
python -m http.server 5500
```

### 4. Open the app

```
http://localhost:5500/index.html
```

### 5. Login with demo credentials

| Role | Email | Password |
|---|---|---|
| 👤 **Patient** | `rahul@demo.com` | `demo1234` |
| 👨‍⚕️ **Doctor** | `priya.sharma@medikoisk.health` | `doctor123` |

---

## 📁 Project Structure

```
medikiosk/
├── Backend/
│   ├── main.py              ← FastAPI app + all routes
│   ├── models.py            ← SQLAlchemy tables
│   ├── schemas.py           ← Pydantic request/response models
│   ├── database.py          ← SQLite engine + session factory
│   ├── auth.py              ← JWT + bcrypt
│   ├── requirements.txt
│   ├── .env                 ← secrets (gitignored)
│   ├── .env.example         ← template
│   └── medikoisk.db         ← SQLite database (gitignored)
│
├── Frontend/
│   ├── index.html           ← the entire SPA
│   └── api.js               ← fetch wrapper + JWT handling
│
├── .gitignore
└── README.md
```

---

## 🔐 Security

| Layer | Implementation |
|---|---|
| **Password storage** | bcrypt via `passlib`, 72-byte truncated |
| **Authentication** | JWT HS256, 12-hour expiry |
| **Session** | `mk_token` in browser localStorage |
| **Authorization** | Per-route ownership checks |
| **Secrets** | `.env` file, gitignored, refuses to start in prod without it |
| **Input sanitization** | Client-side escaping via `esc()` on all user data |
| **Rate limiting** | Client-side + server-side UTR uniqueness |
| **CORS** | Configurable — restrict origins in production |

---

## 🎬 Demo Flow

1. **Login as patient** → dashboard shows upcoming appointment, active medicines, reports
2. **Book a new appointment** → pick doctor, date, slot → get token PDF
3. **Pay via UPI** → QR + UTR verification → receipt PDF
4. **Ask AI Assistant** → "who is my doctor?", "what medicines am I taking?"
5. **Logout, login as doctor** → see the patient's appointment in queue
6. **Write a prescription** → patient sees it after refresh
7. **Upload a report** → patient sees it in health records

---

## 🛠️ Tech Stack

| Layer | Tech | Why |
|---|---|---|
| Frontend | Vanilla JS + HTML + CSS | Zero build step, no framework overhead |
| Backend | FastAPI | Auto-generated docs, Pydantic validation, async |
| ORM | SQLAlchemy 2.0 | Type-safe, industry standard |
| Database | SQLite (dev) / Postgres (prod) | Zero-config for dev, scalable for prod |
| Auth | python-jose + passlib[bcrypt] | Battle-tested JWT + hashing |
| PDFs | jsPDF + qrcodejs | Client-side, no server load |
| AI | Custom rule-based engine | No API keys, works offline |

---

## 🚀 Roadmap (What's Next)

- [ ] **AYUSH Ministry integration** — 6 systems (Ayurveda, Yoga, Unani, Siddha, Sowa-Rigpa, Homoeopathy)
- [ ] **Real LLM AI** — Gemini / GPT integration
- [ ] **ABDM / ABHA** — national health ID sandbox
- [ ] **Razorpay test mode** — real UPI gateway
- [ ] **WebRTC video** — in-app consultation
- [ ] **PostgreSQL** — production database
- [ ] **Post-deploy** — HTTPS, CORS lockdown, rate limiting middleware

---

## 🤝 Contributing

This is a hackathon prototype. For SIH evaluation, the code is intentionally compact and dependency-light.

---

## 📄 License

MIT — see LICENSE file.

---


[SEED] Demo users created (allopathic + AYUSH)
[SEED] Patient: rahul@demo.com / demo1234
[SEED] Doctor : priya.sharma@medikoisk.health / doctor123
[SEED] AYUSH  : vaidya.anjali.verma@medikoisk.ayush / doctor123

test it
🚀 **Live Demo:** [https://medikiosk.suhaan-sameer-gadda.workers.dev](https://medikiosk.suhaan-sameer-gadda.workers.dev)
📚 **API Docs:** [https://medikiosk-6.onrender.com/docs](https://medikiosk-6.onrender.com/docs)




## 👥 Credits

Built for **Smart India Hackathon 2026** — Problem Statement **SIH26047**
Ministry of Ayush · Case-taking & Health Record System
