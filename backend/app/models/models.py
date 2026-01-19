from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
import enum

from app.core.database import Base


class BedStatus(str, enum.Enum):
    EMPTY = "empty"
    OCCUPIED = "occupied"
    CLEANING = "cleaning"
    BLOCKED = "blocked"
    ISOLATION = "isolation"


class AcuityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, enum.Enum):
    ARRIVAL = "arrival"
    TRIAGE = "triage"
    ADMISSION_REQUEST = "admission_request"
    BED_ASSIGNMENT = "bed_assignment"
    TRANSFER = "transfer"
    IMAGING_REQUEST = "imaging_request"
    IMAGING_START = "imaging_start"
    IMAGING_END = "imaging_end"
    CONSULT_REQUEST = "consult_request"
    CONSULT_START = "consult_start"
    CONSULT_END = "consult_end"
    CLEANING_START = "cleaning_start"
    CLEANING_END = "cleaning_end"
    DISCHARGE = "discharge"
    ESCALATION = "escalation"
    NURSE_ASSIGNMENT = "nurse_assignment"
    TRANSPORT_REQUEST = "transport_request"
    TRANSPORT_START = "transport_start"
    TRANSPORT_END = "transport_end"


class SimulationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Unit(Base):
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    floor = Column(Integer, default=1)
    capacity = Column(Integer, default=24)
    unit_type = Column(String(50), default="medical")  # medical, surgical, icu, ed
    
    # Relationships
    beds = relationship("Bed", back_populates="unit")
    nurses = relationship("Nurse", back_populates="unit")


class Bed(Base):
    __tablename__ = "beds"
    
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    bed_number = Column(String(20), nullable=False)
    bed_type = Column(String(50), default="standard")  # standard, isolation, icu
    status = Column(String(50), default="empty")
    x_position = Column(Float, default=0)  # For map visualization
    y_position = Column(Float, default=0)
    
    # Current occupant
    current_patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Relationships
    unit = relationship("Unit", back_populates="beds")
    current_patient = relationship("Patient", foreign_keys=[current_patient_id])


class Nurse(Base):
    __tablename__ = "nurses"
    
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    name = Column(String(100), nullable=False)
    employee_id = Column(String(20), unique=True, nullable=False)
    specialty = Column(String(50), nullable=True)
    max_patients = Column(Integer, default=4)
    
    # Relationships
    unit = relationship("Unit", back_populates="nurses")
    shifts = relationship("Shift", back_populates="nurse")


class Shift(Base):
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    nurse_id = Column(Integer, ForeignKey("nurses.id"), nullable=False)
    shift_date = Column(DateTime, nullable=False)
    shift_type = Column(String(20), nullable=False)  # day, evening, night
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Assigned patients (JSON array of patient IDs)
    assigned_patients = Column(JSONB, default=list)
    
    # Relationships
    nurse = relationship("Nurse", back_populates="shifts")


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(20), unique=True, nullable=False)  # Medical Record Number
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    acuity = Column(String(50), default="medium")
    chief_complaint = Column(String(255), nullable=True)
    
    # Timestamps
    arrival_time = Column(DateTime, nullable=False)
    discharge_time = Column(DateTime, nullable=True)
    
    # Current location
    current_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    current_bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)
    
    # Flags
    is_isolation = Column(Boolean, default=False)
    requires_imaging = Column(Boolean, default=False)
    requires_consult = Column(Boolean, default=False)
    
    # Relationships
    events = relationship("Event", back_populates="patient")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Context
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)
    nurse_id = Column(Integer, ForeignKey("nurses.id"), nullable=True)
    
    # Additional data
    data = Column(JSONB, default=dict)
    notes = Column(Text, nullable=True)
    
    # For scenario tracking
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="events")


class StateSnapshot(Base):
    __tablename__ = "state_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    
    # Snapshot data
    beds_state = Column(JSONB, nullable=False)  # bed_id -> status, patient_id
    queues_state = Column(JSONB, nullable=False)  # queue_name -> [patient_ids]
    metrics = Column(JSONB, nullable=False)  # occupancy, wait times, etc.


class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_baseline = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Parameters
    parameters = Column(JSONB, nullable=False, default=dict)
    # Example parameters:
    # {
    #   "arrival_multiplier": 1.0,
    #   "acuity_mix": {"low": 0.3, "medium": 0.5, "high": 0.2},
    #   "beds_available": 24,
    #   "nurse_count": {"day": 6, "evening": 5, "night": 4},
    #   "imaging_capacity": 1.0,
    #   "transport_capacity": 1.0
    # }
    
    # Relationships
    simulation_runs = relationship("SimulationRun", back_populates="scenario")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    status = Column(String(50), default="pending")
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress (0-100)
    progress = Column(Integer, default=0)
    
    # Results
    metrics = Column(JSONB, nullable=True)
    timeseries = Column(JSONB, nullable=True)
    bottlenecks = Column(JSONB, nullable=True)
    
    # Error info
    error_message = Column(Text, nullable=True)
    
    # Relationships
    scenario = relationship("Scenario", back_populates="simulation_runs")


class PolicyDoc(Base):
    __tablename__ = "policy_docs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    doc_type = Column(String(50), nullable=False)  # protocol, guideline, sla
    created_at = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column(JSONB, default=dict)  # Renamed from metadata to avoid SQLAlchemy conflict


class PolicyEmbedding(Base):
    __tablename__ = "policy_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("policy_docs.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
    
    # Relationships
    doc = relationship("PolicyDoc")
