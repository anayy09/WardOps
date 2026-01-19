from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class BedStatusEnum(str, Enum):
    empty = "empty"
    occupied = "occupied"
    cleaning = "cleaning"
    blocked = "blocked"
    isolation = "isolation"


class AcuityLevelEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EventTypeEnum(str, Enum):
    arrival = "arrival"
    triage = "triage"
    admission_request = "admission_request"
    bed_assignment = "bed_assignment"
    transfer = "transfer"
    imaging_request = "imaging_request"
    imaging_start = "imaging_start"
    imaging_end = "imaging_end"
    consult_request = "consult_request"
    consult_start = "consult_start"
    consult_end = "consult_end"
    cleaning_start = "cleaning_start"
    cleaning_end = "cleaning_end"
    discharge = "discharge"
    escalation = "escalation"
    nurse_assignment = "nurse_assignment"
    transport_request = "transport_request"
    transport_start = "transport_start"
    transport_end = "transport_end"


class SimulationStatusEnum(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# Base schemas
class UnitBase(BaseModel):
    name: str
    code: str
    floor: int = 1
    capacity: int = 24
    unit_type: str = "medical"


class UnitCreate(UnitBase):
    pass


class Unit(UnitBase):
    id: int

    class Config:
        from_attributes = True


class BedBase(BaseModel):
    unit_id: int
    bed_number: str
    bed_type: str = "standard"
    status: BedStatusEnum = BedStatusEnum.empty
    x_position: float = 0
    y_position: float = 0


class BedCreate(BedBase):
    pass


class Bed(BedBase):
    id: int
    current_patient_id: Optional[int] = None

    class Config:
        from_attributes = True


class BedWithPatient(Bed):
    patient_name: Optional[str] = None
    patient_acuity: Optional[AcuityLevelEnum] = None
    patient_chief_complaint: Optional[str] = None


class NurseBase(BaseModel):
    unit_id: int
    name: str
    employee_id: str
    specialty: Optional[str] = None
    max_patients: int = 4


class NurseCreate(NurseBase):
    pass


class Nurse(NurseBase):
    id: int

    class Config:
        from_attributes = True


class NurseWithAssignments(Nurse):
    assigned_patient_count: int = 0
    assigned_patients: List[int] = []


class ShiftBase(BaseModel):
    nurse_id: int
    shift_date: datetime
    shift_type: str
    start_time: datetime
    end_time: datetime
    assigned_patients: List[int] = []


class ShiftCreate(ShiftBase):
    pass


class Shift(ShiftBase):
    id: int

    class Config:
        from_attributes = True


class PatientBase(BaseModel):
    mrn: str
    name: str
    age: int
    gender: str
    acuity: AcuityLevelEnum = AcuityLevelEnum.medium
    chief_complaint: Optional[str] = None
    arrival_time: datetime
    is_isolation: bool = False
    requires_imaging: bool = False
    requires_consult: bool = False


class PatientCreate(PatientBase):
    pass


class Patient(PatientBase):
    id: int
    discharge_time: Optional[datetime] = None
    current_unit_id: Optional[int] = None
    current_bed_id: Optional[int] = None

    class Config:
        from_attributes = True


class PatientSummary(BaseModel):
    id: int
    mrn: str
    name: str
    acuity: AcuityLevelEnum
    chief_complaint: Optional[str]
    arrival_time: datetime
    current_bed: Optional[str] = None


class EventBase(BaseModel):
    patient_id: Optional[int] = None
    event_type: EventTypeEnum
    timestamp: datetime
    unit_id: Optional[int] = None
    bed_id: Optional[int] = None
    nurse_id: Optional[int] = None
    data: Dict[str, Any] = {}
    notes: Optional[str] = None


class EventCreate(EventBase):
    scenario_id: Optional[int] = None


class Event(EventBase):
    id: int
    scenario_id: Optional[int] = None

    class Config:
        from_attributes = True


class PatientTrace(BaseModel):
    patient: Patient
    events: List[Event]
    metrics: Dict[str, Any]


class ScenarioParameters(BaseModel):
    arrival_multiplier: float = Field(1.0, ge=0.5, le=3.0)
    acuity_mix: Dict[str, float] = {"low": 0.3, "medium": 0.5, "high": 0.2}
    beds_available: int = Field(24, ge=1, le=100)
    nurse_count: Dict[str, int] = {"day": 6, "evening": 5, "night": 4}
    imaging_capacity: float = Field(1.0, ge=0.2, le=5.0)
    transport_capacity: float = Field(1.0, ge=0.2, le=5.0)


class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_baseline: bool = False
    parameters: ScenarioParameters


class ScenarioCreate(ScenarioBase):
    pass


class Scenario(ScenarioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SimulationRunBase(BaseModel):
    scenario_id: int


class SimulationRunCreate(SimulationRunBase):
    pass


class SimulationRun(SimulationRunBase):
    id: int
    status: SimulationStatusEnum
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class SimulationResults(BaseModel):
    run_id: int
    scenario_id: int
    metrics: Dict[str, Any]
    timeseries: Dict[str, List[Any]]
    bottlenecks: List[Dict[str, Any]]


class StateSnapshot(BaseModel):
    timestamp: datetime
    beds_state: Dict[str, Any]
    queues_state: Dict[str, Any]
    metrics: Dict[str, Any]


class KPIMetrics(BaseModel):
    occupancy_percent: float
    average_los_hours: float
    average_time_to_bed_minutes: float
    sla_breaches: int
    imaging_queue_length: int
    ed_waiting_count: int
    nurse_load_average: float


class ReplayDelta(BaseModel):
    timestamp: datetime
    bed_changes: List[Dict[str, Any]]
    event_markers: List[Dict[str, Any]]
    metrics: KPIMetrics


# LLM Tool schemas
class QueryStateRequest(BaseModel):
    time_iso: str
    unit_id: int


class QueryStateResponse(BaseModel):
    occupancy: Dict[str, Any]
    queues: Dict[str, Any]
    staffing: Dict[str, Any]


class BottleneckSummary(BaseModel):
    constraint: str
    impact_score: float
    affected_patients: int
    description: str
    supporting_stats: Dict[str, Any]


class IncidentNote(BaseModel):
    note_text: str


class ParsedIncident(BaseModel):
    event_type: str
    timestamp: Optional[datetime]
    entities: Dict[str, Any]
    confidence: float


class ScenarioFromText(BaseModel):
    text: str


class ProposedScenario(BaseModel):
    parameters: ScenarioParameters
    reasoning: str


class PolicySnippet(BaseModel):
    doc_id: int
    doc_title: str
    chunk_text: str
    relevance_score: float


# API Response wrappers
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
