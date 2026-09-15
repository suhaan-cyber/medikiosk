"""Every table. JSON columns let us store lists/dicts without extra tables."""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, JSON
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    role = Column(String, index=True)                 # 'patient' | 'doctor'
    name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    phone = Column(String, default="")
    blood = Column(String, default="")

    # patient fields
    dob = Column(String, default="")
    gender = Column(String, default="")
    patient_id = Column(String, default="")           # human-readable "MED-20481"
    allergies = Column(String, default="")
    aadhaar_last4 = Column(String, default="")
    aadhaar_verified = Column(Boolean, default=False)

    # doctor fields
    dept = Column(String, default="")
    emp_id = Column(String, default="")
    exp = Column(Integer, default=0)
    qual = Column(String, default="")
    rating = Column(Float, default=4.5)
    fee = Column(Integer, default=500)
    slots = Column(JSON, default=list)
    online = Column(Boolean, default=True)
    bio = Column(Text, default="")
    degree_file_name = Column(String, default="")
    degree_status = Column(String, default="pending")

    # AYUSH flags + fields
    ayush = Column(Boolean, default=False)            # True if AYUSH practitioner

    # common
    profile_photo = Column(Text, default="")
    created_at = Column(Integer, default=0)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True)
    patient_id = Column(String, index=True)
    doctor_id = Column(String, index=True)
    patient_name = Column(String, default="")
    patient_email = Column(String, default="")
    doctor_name = Column(String, default="")
    doctor_email = Column(String, default="")
    dept = Column(String, default="")
    dept_name = Column(String, default="")
    date = Column(String, default="")
    time = Column(String, default="")
    mode = Column(String, default="video")            # 'video' | 'offline'
    reason = Column(Text, default="")
    status = Column(String, default="confirmed")      # 'confirmed' | 'completed' | 'cancelled'
    token = Column(String, default="")
    fee = Column(Integer, default=0)
    paid = Column(Boolean, default=False)
    meet_url = Column(String, default="")
    calendar_invite_url = Column(String, default="")
    meeting_status = Column(String, default="scheduled")
    completion_details = Column(JSON, nullable=True)
    created_at = Column(Integer, default=0)

    # AYUSH-specific
    ayush = Column(Boolean, default=False)
    prakriti = Column(String, default="")             # vata | pitta | kapha | ...
    agni = Column(String, default="")                 # sama | vishama | tikshna | manda
    symptoms = Column(JSON, default=list)             # ["joint-pain", "digestion", ...]
    symptom_labels = Column(JSON, default=list)       # ["Joint pain / arthritis", ...]
    ayush_notes = Column(Text, default="")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(String, primary_key=True)
    appointment_id = Column(String, nullable=True)
    patient_id = Column(String, index=True)
    doctor_id = Column(String, index=True)
    doctor_name = Column(String, default="")
    doctor_emp_id = Column(String, default="")
    dept_name = Column(String, default="")
    diagnosis = Column(Text, default="")
    advice = Column(Text, default="")
    follow_up = Column(String, default="")
    meds = Column(JSON, default=list)                 # [{name, dose, freq, duration, timing}]
    paid = Column(Boolean, default=False)
    created_at = Column(Integer, default=0)

    # AYUSH-specific
    ayush = Column(Boolean, default=False)
    prakriti = Column(String, default="")
    agni = Column(String, default="")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    patient_id = Column(String, index=True)
    doctor_id = Column(String, index=True, default="")
    doctor_name = Column(String, default="")
    uploaded_by = Column(String, default="doctor")    # 'doctor' | 'patient'
    title = Column(String)
    type = Column(String, default="")
    notes = Column(Text, default="")
    kind = Column(String, default="pdf")              # 'pdf' | 'image'
    data = Column(Text, default="")                   # base64 payload
    file_name = Column(String, default="")
    date = Column(String, default="")
    created_at = Column(Integer, default=0)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    patient_id = Column(String, index=True)
    patient_name = Column(String, default="")
    doctor_id = Column(String, index=True, default="")
    title = Column(String, default="")
    kind = Column(String, default="")                 # 'appointment' | 'prescription'
    ref_id = Column(String, default="")
    amount = Column(Integer, default=0)
    utr = Column(String, unique=True)                 # enforced unique
    txn_id = Column(String, default="")
    status = Column(String, default="success")
    method = Column(String, default="UPI")
    created_at = Column(Integer, default=0)

    # AYUSH pass-through
    ayush = Column(Boolean, default=False)


class Vitals(Base):
    __tablename__ = "vitals"

    id = Column(String, primary_key=True)
    patient_id = Column(String, index=True)
    date = Column(String, default="")
    heart_rate = Column(Integer, default=0)
    bp_sys = Column(Integer, default=0)
    bp_dia = Column(Integer, default=0)
    blood_sugar = Column(Integer, default=0)
    spo2 = Column(Integer, default=0)
    notes = Column(Text, default="")
    created_at = Column(Integer, default=0)


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id = Column(String, primary_key=True)
    requester_id = Column(String, index=True)
    requester_name = Column(String, default="")
    requester_role = Column(String, default="")
    approver_id = Column(String, index=True)
    changes = Column(JSON, default=dict)
    reason = Column(Text, default="")
    status = Column(String, default="pending")        # 'pending' | 'approved' | 'rejected'
    note = Column(String, default="")
    created_at = Column(Integer, default=0)
    resolved_at = Column(Integer, nullable=True)


class TimelineEvent(Base):
    __tablename__ = "timeline"

    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    title = Column(String, default="")
    desc = Column(Text, default="")
    date = Column(String, default="")
    tags = Column(JSON, default=list)
    at = Column(Integer, default=0)


class Chat(Base):
    __tablename__ = "chats"

    user_id = Column(String, primary_key=True)
    messages = Column(JSON, default=list)