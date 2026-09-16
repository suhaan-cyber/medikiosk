"""MEDIKOISK FastAPI backend — routes, helpers, seeding."""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import time, random, string

from database import Base, engine, SessionLocal, get_db
import models, schemas, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MEDIKOISK API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://medikiosk-flax-gamma.vercel.app",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
            "Access-Control-Max-Age": "3600",
        },
    )
    
# ═════════════════════ HELPERS ═════════════════════
def uid(p=""):
    return p + "".join(random.choices(string.ascii_lowercase + string.digits, k=13))


CAMEL = {
    "patient_id": "patientId", "doctor_id": "doctorId",
    "patient_name": "patientName", "doctor_name": "doctorName",
    "doctor_email": "doctorEmail", "patient_email": "patientEmail",
    "dept_name": "deptName", "meet_url": "meetUrl",
    "calendar_invite_url": "calendarInviteUrl",
    "meeting_status": "meetingStatus", "completion_details": "completionDetails",
    "created_at": "createdAt", "follow_up": "followUp",
    "file_name": "fileName", "uploaded_by": "uploadedBy",
    "txn_id": "txnId", "ref_id": "refId",
    "doctor_emp_id": "doctorEmpId", "appointment_id": "appointmentId",
    "requester_id": "requesterId", "requester_name": "requesterName",
    "requester_role": "requesterRole", "approver_id": "approverId",
    "resolved_at": "resolvedAt", "user_id": "userId",
    "heart_rate": "heartRate", "bp_sys": "bpSys", "bp_dia": "bpDia",
    "blood_sugar": "bloodSugar",
    "first_name": "firstName", "last_name": "lastName",
    "emp_id": "empId", "aadhaar_last4": "aadhaarLast4",
    "aadhaar_verified": "aadhaarVerified",
    "degree_file_name": "degreeFileName", "degree_status": "degreeStatus",
    "profile_photo": "profilePhoto",
    # AYUSH additions
    "symptom_labels": "symptomLabels",
    "ayush_notes": "ayushNotes",
}

SNAKE = {v: k for k, v in CAMEL.items()}


def row_dict(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def camelize(row: dict) -> dict:
    return {CAMEL.get(k, k): v for k, v in row.items()}


def snakeize(payload: dict) -> dict:
    return {SNAKE.get(k, k): v for k, v in payload.items()}


def user_out(u) -> dict:
    out = {}
    for c in u.__table__.columns:
        if c.name == "password_hash":
            continue
        out[CAMEL.get(c.name, c.name)] = getattr(u, c.name)
    return out


def upsert(db: Session, Model, id_: str, data: dict):
    obj = db.query(Model).filter(Model.id == id_).first()
    if not obj:
        obj = Model(id=id_)
        db.add(obj)
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


# ═════════════════════ AUTH ═════════════════════
DEPT_FEES = {
    # Allopathic
    "CARD": 800, "NEUR": 950, "ORTH": 750,
    "PEDI": 650, "DERM": 700, "GENM": 500,
    # AYUSH
    "AYUR": 600, "YOGN": 500, "UNAN": 550,
    "SIDD": 550, "SOWA": 550, "HOME": 500,
}

AYUSH_DEPTS = {"AYUR", "YOGN", "UNAN", "SIDD", "SOWA", "HOME"}


@app.get("/")
def root():
    return {"name": "MEDIKOISK API", "version": "2.0.0", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"ok": True, "ts": int(time.time() * 1000)}


@app.post("/auth/register")
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(400, "An account with this email already exists.")

    is_doc = body.role == "doctor"
    dept = (body.dept or "GENM") if is_doc else ""
    is_ayush = bool(body.ayush) or (is_doc and dept in AYUSH_DEPTS)
    emp_id = ""
    if is_doc:
        count = db.query(models.User).filter(
            models.User.dept == dept, models.User.role == "doctor"
        ).count()
        prefix = "AY-" if is_ayush else ""
        emp_id = f"{prefix}{dept}-{str(count + 1).zfill(4)}"

    name = f"Dr. {body.firstName} {body.lastName}" if is_doc else f"{body.firstName} {body.lastName}"
    if is_ayush and body.firstName.lower().startswith(("vaidya", "hakim", "amchi")):
        name = f"{body.firstName} {body.lastName}"  # already has prefix

    u = models.User(
        id=uid("doc_" if is_doc else "pat_"),
        role=body.role,
        ayush=is_ayush,
        name=name,
        first_name=body.firstName,
        last_name=body.lastName,
        email=email,
        password_hash=auth.hash_password(body.password),
        phone=body.phone or "",
        blood=body.blood or "",
        patient_id="" if is_doc else "MK-" + str(random.randint(10000, 99999)),
        dob="" if is_doc else "",
        gender="" if is_doc else "",
        allergies="" if is_doc else "",
        aadhaar_last4=(body.aadhaarLast4 or "") if not is_doc else "",
        aadhaar_verified=not is_doc,
        dept=dept,
        emp_id=emp_id,
        exp=1 if is_doc else 0,
        qual="BAMS" if is_ayush else ("MBBS" if is_doc else ""),
        rating=4.5,
        fee=DEPT_FEES.get(dept, 500) if is_doc else 0,
        slots=["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"] if is_doc else [],
        online=True,
        bio=f"Newly registered {dept} specialist on MEDIKOISK." if is_doc else "",
        degree_file_name=body.degreeFileName or "",
        degree_status="pending" if is_doc else "",
        created_at=int(time.time() * 1000),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"token": auth.make_token(u.id), "user": user_out(u)}


@app.post("/auth/login")
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    u = db.query(models.User).filter(models.User.email == email).first()
    if not u or not auth.verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Incorrect email or password.")
    if u.role != body.role:
        raise HTTPException(400, f"This email is registered as a {u.role}.")
    return {"token": auth.make_token(u.id), "user": user_out(u)}


@app.get("/auth/me")
def me(u=Depends(auth.current_user)):
    return user_out(u)


@app.post("/auth/logout")
def logout():
    return {"ok": True}


# ═════════════════════ BOOTSTRAP ═════════════════════
@app.get("/bootstrap")
def bootstrap(u=Depends(auth.current_user), db: Session = Depends(get_db)):
    users = db.query(models.User).all()

    if u.role == "patient":
        apts = db.query(models.Appointment).filter(
            models.Appointment.patient_id == u.id
        ).all()
        rxs = db.query(models.Prescription).filter(
            models.Prescription.patient_id == u.id
        ).all()
        reps = db.query(models.Report).filter(
            models.Report.patient_id == u.id
        ).all()
        pays = db.query(models.Payment).filter(
            models.Payment.patient_id == u.id
        ).all()
        crs = db.query(models.ChangeRequest).filter(
            models.ChangeRequest.requester_id == u.id
        ).all()
        tls = db.query(models.TimelineEvent).filter(
            models.TimelineEvent.user_id == u.id
        ).all()
        vs = db.query(models.Vitals).filter(
            models.Vitals.patient_id == u.id
        ).all()
    else:
        apts = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == u.id
        ).all()
        patient_ids = list({a.patient_id for a in apts})
        if patient_ids:
            rxs = db.query(models.Prescription).filter(
                (models.Prescription.doctor_id == u.id) |
                (models.Prescription.patient_id.in_(patient_ids))
            ).all()
            reps = db.query(models.Report).filter(
                (models.Report.doctor_id == u.id) |
                (models.Report.patient_id.in_(patient_ids))
            ).all()
            vs = db.query(models.Vitals).filter(
                models.Vitals.patient_id.in_(patient_ids)
            ).all()
        else:
            rxs = db.query(models.Prescription).filter(
                models.Prescription.doctor_id == u.id
            ).all()
            reps = db.query(models.Report).filter(
                models.Report.doctor_id == u.id
            ).all()
            vs = []
        pays = db.query(models.Payment).filter(
            models.Payment.doctor_id == u.id
        ).all()
        crs = db.query(models.ChangeRequest).filter(
            (models.ChangeRequest.approver_id == u.id) |
            (models.ChangeRequest.requester_id == u.id)
        ).all()
        tls = db.query(models.TimelineEvent).filter(
            models.TimelineEvent.user_id == u.id
        ).all()

    vitals_map = {}
    for v in vs:
        vitals_map.setdefault(v.patient_id, []).append(camelize(row_dict(v)))
    for pid in vitals_map:
        vitals_map[pid].sort(
            key=lambda x: (x.get("date") or "", x.get("createdAt") or 0),
            reverse=True,
        )

    chat = db.query(models.Chat).filter(models.Chat.user_id == u.id).first()

    return {
        "users": [user_out(x) for x in users],
        "appointments": [camelize(row_dict(x)) for x in apts],
        "prescriptions": [camelize(row_dict(x)) for x in rxs],
        "reports": [camelize(row_dict(x)) for x in reps],
        "payments": [camelize(row_dict(x)) for x in pays],
        "changeRequests": [camelize(row_dict(x)) for x in crs],
        "timeline": [camelize(row_dict(x)) for x in tls],
        "vitals": vitals_map,
        "chats": {u.id: (chat.messages if chat else [])},
    }


# ═════════════════════ APPOINTMENTS ═════════════════════
@app.post("/appointments")
def create_appt(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    data = snakeize(body)
    if "id" not in data:
        raise HTTPException(400, "Missing id")
    if u.role == "patient" and data.get("patient_id") != u.id:
        raise HTTPException(403, "Cannot create an appointment for another patient")
    upsert(db, models.Appointment, data["id"], data)
    return {"ok": True}


@app.patch("/appointments/{aid}")
def patch_appt(aid: str, body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    apt = db.query(models.Appointment).filter(models.Appointment.id == aid).first()
    if not apt:
        raise HTTPException(404, "Appointment not found")
    if u.role == "patient" and apt.patient_id != u.id:
        raise HTTPException(403, "Not your appointment")
    if u.role == "doctor" and apt.doctor_id != u.id:
        raise HTTPException(403, "Not your appointment")
    data = snakeize(body)
    data.pop("id", None)
    for k, v in data.items():
        if hasattr(apt, k):
            setattr(apt, k, v)
    db.commit()
    return {"ok": True}


# ═════════════════════ PRESCRIPTIONS ═════════════════════
@app.post("/prescriptions")
def create_rx(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    if u.role != "doctor":
        raise HTTPException(403, "Only doctors can issue prescriptions")
    data = snakeize(body)
    if "id" not in data:
        raise HTTPException(400, "Missing id")
    if data.get("doctor_id") != u.id:
        raise HTTPException(403, "Cannot issue a prescription as another doctor")
    upsert(db, models.Prescription, data["id"], data)
    return {"ok": True}


@app.patch("/prescriptions/{rid}")
def patch_rx(rid: str, body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    rx = db.query(models.Prescription).filter(models.Prescription.id == rid).first()
    if not rx:
        raise HTTPException(404, "Prescription not found")
    if u.role == "doctor" and rx.doctor_id != u.id:
        raise HTTPException(403, "Not your prescription")
    data = snakeize(body)
    data.pop("id", None)
    for k, v in data.items():
        if hasattr(rx, k):
            setattr(rx, k, v)
    db.commit()
    return {"ok": True}


# ═════════════════════ REPORTS ═════════════════════
@app.post("/reports")
def create_report(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    data = snakeize(body)
    if "id" not in data:
        raise HTTPException(400, "Missing id")
    if u.role == "patient":
        if data.get("patient_id") != u.id:
            raise HTTPException(403, "Cannot upload for another patient")
        data["uploaded_by"] = "patient"
    else:
        existing_apt = db.query(models.Appointment).filter(
            models.Appointment.patient_id == data.get("patient_id"),
            models.Appointment.doctor_id == u.id,
        ).first()
        if not existing_apt:
            raise HTTPException(403, "Not your patient")
    upsert(db, models.Report, data["id"], data)
    return {"ok": True}


@app.patch("/reports/{rid}")
def patch_report(rid: str, body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    r = db.query(models.Report).filter(models.Report.id == rid).first()
    if not r:
        raise HTTPException(404, "Report not found")
    if u.role == "patient" and r.patient_id != u.id:
        raise HTTPException(403, "Not your report")
    if u.role == "doctor" and r.doctor_id != u.id:
        raise HTTPException(403, "Not your report")
    data = snakeize(body)
    data.pop("id", None)
    for k, v in data.items():
        if hasattr(r, k):
            setattr(r, k, v)
    db.commit()
    return {"ok": True}


@app.delete("/reports/{rid}")
def delete_report(rid: str, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    r = db.query(models.Report).filter(models.Report.id == rid).first()
    if not r:
        raise HTTPException(404, "Report not found")
    if u.role == "patient" and r.patient_id != u.id:
        raise HTTPException(403, "Not your report")
    if u.role == "doctor" and r.doctor_id != u.id:
        raise HTTPException(403, "Not your report")
    db.delete(r)
    db.commit()
    return {"ok": True}


# ═════════════════════ PAYMENTS ═════════════════════
@app.post("/payments")
def create_payment(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    if u.role != "patient":
        raise HTTPException(403, "Only patients can pay")
    utr = str(body.get("utr") or "").strip()
    if not utr:
        raise HTTPException(400, "Missing UTR")
    if db.query(models.Payment).filter(models.Payment.utr == utr).first():
        raise HTTPException(400, "Duplicate UTR — already recorded")

    data = snakeize(body)
    data["utr"] = utr
    if data.get("patient_id") != u.id:
        raise HTTPException(403, "Cannot pay for another patient")
    if "id" not in data:
        raise HTTPException(400, "Missing id")

    upsert(db, models.Payment, data["id"], data)

    kind = body.get("kind")
    ref_id = body.get("refId")
    if kind == "appointment" and ref_id:
        apt = db.query(models.Appointment).filter(models.Appointment.id == ref_id).first()
        if apt:
            apt.paid = True
            db.commit()
    elif kind == "prescription" and ref_id:
        rx = db.query(models.Prescription).filter(models.Prescription.id == ref_id).first()
        if rx:
            rx.paid = True
            db.commit()

    return {"ok": True}


# ═════════════════════ VITALS ═════════════════════
@app.post("/vitals")
def create_vitals(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    data = snakeize(body)
    if "id" not in data:
        raise HTTPException(400, "Missing id")
    if u.role == "patient" and data.get("patient_id") != u.id:
        raise HTTPException(403, "Cannot record vitals for another patient")
    upsert(db, models.Vitals, data["id"], data)
    return {"ok": True}


# ═════════════════════ CHANGE REQUESTS ═════════════════════
@app.post("/change-requests")
def create_cr(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    data = snakeize(body)
    if "id" not in data:
        raise HTTPException(400, "Missing id")
    if data.get("requester_id") != u.id:
        raise HTTPException(403, "Cannot create a request on behalf of another user")
    upsert(db, models.ChangeRequest, data["id"], data)
    return {"ok": True}


@app.patch("/change-requests/{cid}")
def patch_cr(cid: str, body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    cr = db.query(models.ChangeRequest).filter(models.ChangeRequest.id == cid).first()
    if not cr:
        raise HTTPException(404, "Change request not found")
    if cr.approver_id != u.id:
        raise HTTPException(403, "Not your request to resolve")
    data = snakeize(body)
    data.pop("id", None)
    for k, v in data.items():
        if hasattr(cr, k):
            setattr(cr, k, v)
    db.commit()
    return {"ok": True}


# ═════════════════════ TIMELINE ═════════════════════
@app.post("/timeline")
def create_timeline(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    data = snakeize(body)
    if "id" not in data:
        raise HTTPException(400, "Missing id")
    target_user = data.get("user_id")
    if target_user != u.id:
        if u.role == "doctor":
            rel = db.query(models.Appointment).filter(
                models.Appointment.patient_id == target_user,
                models.Appointment.doctor_id == u.id,
            ).first()
            if not rel:
                raise HTTPException(403, "Not your patient")
        else:
            raise HTTPException(403, "Cannot write to another user's timeline")
    upsert(db, models.TimelineEvent, data["id"], data)
    return {"ok": True}


# ═════════════════════ CHATS ═════════════════════
@app.put("/chats")
def put_chats(body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    msgs = body.get("messages", [])
    if not isinstance(msgs, list):
        raise HTTPException(400, "messages must be an array")
    chat = db.query(models.Chat).filter(models.Chat.user_id == u.id).first()
    if not chat:
        chat = models.Chat(user_id=u.id, messages=msgs)
        db.add(chat)
    else:
        chat.messages = msgs
    db.commit()
    return {"ok": True}


# ═════════════════════ USERS (profile edits) ═════════════════════
EDITABLE_USER_FIELDS = {
    "profile_photo", "phone", "blood", "dob", "gender", "allergies",
    "qual", "exp", "fee", "bio", "slots", "online",
    "name", "first_name", "last_name",
    "degree_status", "patient_id", "emp_id",
}


@app.patch("/users/{uid_}")
def patch_user(uid_: str, body: dict, u=Depends(auth.current_user), db: Session = Depends(get_db)):
    if uid_ != u.id:
        if u.role == "doctor":
            rel = db.query(models.Appointment).filter(
                models.Appointment.patient_id == uid_,
                models.Appointment.doctor_id == u.id,
            ).first()
            if not rel:
                raise HTTPException(403, "Not your patient")
        else:
            raise HTTPException(403, "Not allowed")

    target = db.query(models.User).filter(models.User.id == uid_).first()
    if not target:
        raise HTTPException(404, "User not found")

    data = snakeize(body)
    for k, v in data.items():
        if k in EDITABLE_USER_FIELDS and hasattr(target, k):
            setattr(target, k, v)
    db.commit()
    return {"ok": True}


# ═════════════════════ SEED — ALLOPATHIC ═════════════════════
SEED_DOCTORS = [
    ("Priya", "Sharma", "CARD", 14, "MD, DM (Cardiology)", 4.9, 800,
     ["09:00", "09:30", "10:30", "11:00", "14:00", "15:30", "16:00"]),
    ("Arjun", "Nair", "CARD", 11, "MBBS, MD, DNB", 4.7, 750,
     ["10:00", "11:30", "12:00", "15:00", "16:30", "17:00"]),
    ("Kavita", "Rao", "NEUR", 17, "MD, DM (Neurology)", 4.8, 950,
     ["09:30", "10:30", "11:30", "14:30", "16:00"]),
    ("Sameer", "Khan", "NEUR", 9, "MBBS, MD (Neuro)", 4.6, 850,
     ["11:00", "12:00", "15:00", "16:00", "17:30"]),
    ("Rohan", "Gupta", "ORTH", 13, "MS (Ortho), FRCS", 4.8, 750,
     ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]),
    ("Meera", "Joshi", "ORTH", 8, "MBBS, MS (Ortho)", 4.5, 700,
     ["10:30", "11:30", "12:30", "15:30", "17:00"]),
    ("Ananya", "Iyer", "PEDI", 12, "MD (Pediatrics)", 4.9, 650,
     ["09:00", "09:30", "10:00", "11:00", "16:00", "17:00"]),
    ("Vikram", "Desai", "PEDI", 10, "MBBS, DCH", 4.7, 600,
     ["10:00", "11:30", "12:30", "15:00", "16:30"]),
    ("Sneha", "Patel", "DERM", 11, "MD (Dermatology)", 4.8, 700,
     ["09:30", "10:30", "11:30", "14:30", "16:00"]),
    ("Karan", "Malhotra", "DERM", 7, "MBBS, DDVL", 4.5, 650,
     ["10:00", "11:00", "12:00", "15:30", "17:00"]),
    ("Anil", "Mehta", "GENM", 16, "MD (Gen. Medicine)", 4.9, 500,
     ["09:00", "09:30", "10:00", "10:30", "11:00", "15:00", "16:00", "17:00"]),
    ("Deepa", "Krishnan", "GENM", 9, "MBBS, MD", 4.6, 450,
     ["10:00", "11:00", "12:00", "14:00", "15:00", "16:30"]),
]

# ═════════════════════ SEED — AYUSH (2 per system) ═════════════════════
SEED_AYUSH_DOCTORS = [
    # Ayurveda
    ("Vaidya Anjali", "Verma", "AYUR", 18, "BAMS, MD (Kayachikitsa)", 4.9, 600,
     ["09:00", "10:00", "11:00", "14:00", "15:30", "16:30"]),
    ("Vaidya Ramesh", "Iyer", "AYUR", 12, "BAMS, PhD (Ayurveda)", 4.7, 550,
     ["09:30", "10:30", "12:00", "15:00", "16:00", "17:00"]),
    # Yoga & Naturopathy
    ("Dr. Sunita", "Menon", "YOGN", 14, "BNYS, MD (Yoga)", 4.8, 500,
     ["07:00", "08:00", "09:00", "17:00", "18:00", "19:00"]),
    ("Dr. Kiran", "Bhat", "YOGN", 10, "BNYS, DYSc", 4.6, 450,
     ["07:30", "08:30", "09:30", "16:30", "17:30", "18:30"]),
    # Unani
    ("Hakim Ayesha", "Khan", "UNAN", 16, "BUMS, MD (Moalijat)", 4.8, 550,
     ["09:00", "10:00", "11:00", "15:00", "16:00", "17:00"]),
    ("Hakim Yusuf", "Ali", "UNAN", 11, "BUMS, Diploma (Unani)", 4.6, 500,
     ["09:30", "10:30", "11:30", "14:30", "15:30", "16:30"]),
    # Siddha
    ("Dr. Meenakshi", "Sundaram", "SIDD", 20, "BSMS, MD (Siddha)", 4.9, 550,
     ["08:00", "09:00", "10:00", "14:00", "15:00", "16:00"]),
    ("Dr. Arun", "Kumar", "SIDD", 9, "BSMS, PhD", 4.5, 500,
     ["09:00", "10:00", "11:00", "15:00", "16:00", "17:00"]),
    # Sowa-Rigpa
    ("Amchi Tenzin", "Norbu", "SOWA", 22, "BSRMS, MD (Sowa-Rigpa)", 4.9, 600,
     ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]),
    ("Amchi Pema", "Dolma", "SOWA", 13, "BSRMS", 4.7, 550,
     ["09:30", "10:30", "11:30", "14:30", "15:30", "16:30"]),
    # Homoeopathy
    ("Dr. Neha", "Sharma", "HOME", 15, "BHMS, MD (Hom.)", 4.8, 500,
     ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]),
    ("Dr. Vikram", "Joshi", "HOME", 8, "BHMS, CCH", 4.5, 450,
     ["09:30", "10:30", "11:30", "15:30", "16:30", "17:30"]),
]


def _slug(s):
    return "".join(ch.lower() for ch in s if ch.isalnum() or ch == " ").replace(" ", ".")


def seed_data():
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            _ensure_ayush_doctors(db)
            return

        doctor_objs = []
        for i, (f, l, dept, exp, qual, rating, fee, slots) in enumerate(SEED_DOCTORS):
            d = models.User(
                id=uid("doc_"),
                role="doctor",
                ayush=False,
                name=f"Dr. {f} {l}",
                first_name=f,
                last_name=l,
                email=f"{f.lower()}.{l.lower()}@medikoisk.health",
                password_hash=auth.hash_password("doctor123"),
                phone=f"+91 90000 {10000 + i * 7}",
                blood="",
                dob="",
                gender="",
                allergies="",
                dept=dept,
                emp_id=f"{dept}-{str(1000 + i + 1).zfill(4)}",
                exp=exp,
                qual=qual,
                rating=rating,
                fee=fee,
                slots=slots,
                online=True,
                bio=f"Experienced {dept} specialist with {exp}+ years of clinical practice.",
                created_at=int(time.time() * 1000),
            )
            db.add(d)
            doctor_objs.append(d)

        for i, (f, l, dept, exp, qual, rating, fee, slots) in enumerate(SEED_AYUSH_DOCTORS):
            first_name = f.split(" ", 1)[1] if " " in f else f
            surname = l
            email_local = _slug(f) + "." + _slug(l)
            d = models.User(
                id=uid("ayd_"),
                role="doctor",
                ayush=True,
                name=f"{f} {l}",
                first_name=first_name,
                last_name=surname,
                email=f"{email_local}@medikoisk.ayush",
                password_hash=auth.hash_password("doctor123"),
                phone=f"+91 90000 {20000 + i * 7}",
                blood="",
                dob="",
                gender="",
                allergies="",
                dept=dept,
                emp_id=f"AY-{dept}-{str(100 + i + 1).zfill(4)}",
                exp=exp,
                qual=qual,
                rating=rating,
                fee=fee,
                slots=slots,
                online=True,
                bio=f"{qual} with {exp}+ years of experience in {dept}.",
                degree_file_name="degree.pdf",
                degree_status="verified",
                created_at=int(time.time() * 1000),
            )
            db.add(d)
            doctor_objs.append(d)

        patient = models.User(
            id=uid("pat_"),
            role="patient",
            ayush=False,
            name="Rahul Sharma",
            first_name="Rahul",
            last_name="Sharma",
            email="rahul@demo.com",
            password_hash=auth.hash_password("demo1234"),
            phone="+91 98765 43210",
            blood="O+",
            dob="1992-04-18",
            gender="Male",
            patient_id="MED-20481",
            allergies="Penicillin",
            aadhaar_last4="4821",
            aadhaar_verified=True,
            created_at=int(time.time() * 1000),
        )
        db.add(patient)
        db.commit()
        for d in doctor_objs:
            db.refresh(d)
        db.refresh(patient)

        cardio = next((d for d in doctor_objs if d.dept == "CARD"), doctor_objs[0])

        apt = models.Appointment(
            id=uid("apt_"),
            patient_id=patient.id,
            patient_name=patient.name,
            patient_email=patient.email,
            doctor_id=cardio.id,
            doctor_name=cardio.name,
            doctor_email=cardio.email,
            dept="CARD",
            dept_name="Cardiology",
            date=time.strftime("%Y-%m-%d", time.localtime(time.time() + 2 * 86400)),
            time="10:30",
            mode="video",
            reason="Routine cardiac follow-up & BP review",
            status="confirmed",
            token="TKN-CARD-014",
            fee=800,
            paid=False,
            meet_url="https://meet.google.com/new",
            meeting_status="scheduled",
            ayush=False,
            created_at=int(time.time() * 1000),
        )
        db.add(apt)

        db.add(models.Prescription(
            id=uid("rx_"),
            appointment_id=apt.id,
            patient_id=patient.id,
            doctor_id=cardio.id,
            doctor_name=cardio.name,
            doctor_emp_id=cardio.emp_id,
            dept_name="Cardiology",
            diagnosis="Essential hypertension — stable, on treatment",
            advice="Low-sodium diet, 30 min brisk walk daily, monitor BP twice weekly.",
            follow_up=time.strftime("%Y-%m-%d", time.localtime(time.time() + 30 * 86400)),
            meds=[
                {"name": "Telmisartan", "dose": "40 mg", "freq": "Once daily",
                 "duration": "30 days", "timing": "Morning, before food"},
                {"name": "Atorvastatin", "dose": "10 mg", "freq": "Once daily",
                 "duration": "30 days", "timing": "Night, before bed"},
                {"name": "Metformin", "dose": "500 mg", "freq": "Twice daily",
                 "duration": "30 days", "timing": "After breakfast & dinner"},
            ],
            ayush=False,
            created_at=int(time.time() * 1000) - 5 * 86400 * 1000,
        ))

        db.add(models.Report(
            id=uid("rep_"),
            patient_id=patient.id,
            doctor_id=cardio.id,
            doctor_name=cardio.name,
            uploaded_by="doctor",
            title="Complete Blood Count",
            type="Lab Report",
            kind="pdf",
            notes="Mild anaemia, otherwise unremarkable.",
            date=time.strftime("%Y-%m-%d", time.localtime(time.time() - 3 * 86400)),
            created_at=int(time.time() * 1000) - 3 * 86400 * 1000,
        ))
        db.add(models.Report(
            id=uid("rep_"),
            patient_id=patient.id,
            doctor_id=cardio.id,
            doctor_name=cardio.name,
            uploaded_by="doctor",
            title="ECG Report",
            type="Cardiology",
            kind="pdf",
            notes="Normal sinus rhythm. No ST-T changes.",
            date=time.strftime("%Y-%m-%d", time.localtime(time.time() - 11 * 86400)),
            created_at=int(time.time() * 1000) - 11 * 86400 * 1000,
        ))

        db.add(models.Vitals(
            id=uid("vit_"),
            patient_id=patient.id,
            date=time.strftime("%Y-%m-%d", time.localtime()),
            heart_rate=78,
            bp_sys=120,
            bp_dia=80,
            blood_sugar=98,
            spo2=98,
            notes="Routine home reading",
            created_at=int(time.time() * 1000),
        ))

        db.commit()
        print("[SEED] Demo users created (allopathic + AYUSH)")
        print("[SEED] Patient: rahul@demo.com / demo1234")
        print("[SEED] Doctor : priya.sharma@medikoisk.health / doctor123")
        print("[SEED] AYUSH  : vaidya.anjali.verma@medikoisk.ayush / doctor123")
    except Exception as e:
        print("[SEED] Failed:", e)
        db.rollback()
    finally:
        db.close()


def _ensure_ayush_doctors(db):
    """Idempotently create the AYUSH doctors if missing (for existing DBs)."""
    try:
        existing = {u.email for u in db.query(models.User).all()}
        added = 0
        for i, (f, l, dept, exp, qual, rating, fee, slots) in enumerate(SEED_AYUSH_DOCTORS):
            email = _slug(f) + "." + _slug(l) + "@medikoisk.ayush"
            if email in existing:
                continue
            first_name = f.split(" ", 1)[1] if " " in f else f
            d = models.User(
                id=uid("ayd_"),
                role="doctor",
                ayush=True,
                name=f"{f} {l}",
                first_name=first_name,
                last_name=l,
                email=email,
                password_hash=auth.hash_password("doctor123"),
                phone=f"+91 90000 {20000 + i * 7}",
                blood="",
                dept=dept,
                emp_id=f"AY-{dept}-{str(100 + i + 1).zfill(4)}",
                exp=exp,
                qual=qual,
                rating=rating,
                fee=fee,
                slots=slots,
                online=True,
                bio=f"{qual} with {exp}+ years of experience in {dept}.",
                degree_file_name="degree.pdf",
                degree_status="verified",
                created_at=int(time.time() * 1000),
            )
            db.add(d)
            added += 1
        if added:
            db.commit()
            print(f"[SEED] Ensured {added} AYUSH doctors")
    except Exception as e:
        print("[SEED] AYUSH ensure failed:", e)
        db.rollback()


seed_data()
