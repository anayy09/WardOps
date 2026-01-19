from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models import Unit, Bed, BedStatus, Patient, Event, EventType, Nurse, Shift
from app.schemas import (
    Unit as UnitSchema,
    Bed as BedSchema,
    BedWithPatient,
    Patient as PatientSchema,
    PatientSummary,
    PatientTrace,
    Event as EventSchema,
    Nurse as NurseSchema,
    NurseWithAssignments,
    KPIMetrics,
    APIResponse,
)

router = APIRouter()


@router.get("/units", response_model=List[UnitSchema])
async def get_units(db: AsyncSession = Depends(get_db)):
    """Get all hospital units"""
    result = await db.execute(select(Unit))
    units = result.scalars().all()
    return units


@router.get("/units/{unit_id}", response_model=UnitSchema)
async def get_unit(unit_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific unit by ID"""
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.get("/units/{unit_id}/beds", response_model=List[BedWithPatient])
async def get_unit_beds(unit_id: int, db: AsyncSession = Depends(get_db)):
    """Get all beds for a unit with current patient info"""
    result = await db.execute(
        select(Bed).where(Bed.unit_id == unit_id).order_by(Bed.bed_number)
    )
    beds = result.scalars().all()
    
    beds_with_patients = []
    for bed in beds:
        bed_data = BedWithPatient(
            id=bed.id,
            unit_id=bed.unit_id,
            bed_number=bed.bed_number,
            bed_type=bed.bed_type,
            status=bed.status,
            x_position=bed.x_position,
            y_position=bed.y_position,
            current_patient_id=bed.current_patient_id,
        )
        
        if bed.current_patient_id:
            patient_result = await db.execute(
                select(Patient).where(Patient.id == bed.current_patient_id)
            )
            patient = patient_result.scalar_one_or_none()
            if patient:
                bed_data.patient_name = patient.name
                bed_data.patient_acuity = patient.acuity
                bed_data.patient_chief_complaint = patient.chief_complaint
        
        beds_with_patients.append(bed_data)
    
    return beds_with_patients


@router.get("/patients", response_model=List[PatientSummary])
async def get_patients(
    db: AsyncSession = Depends(get_db),
    unit_id: Optional[int] = None,
    active_only: bool = True,
    limit: int = Query(default=100, le=500),
    offset: int = 0
):
    """Get patients with optional filters"""
    query = select(Patient)
    
    if unit_id:
        query = query.where(Patient.current_unit_id == unit_id)
    
    if active_only:
        query = query.where(Patient.discharge_time.is_(None))
    
    query = query.order_by(Patient.arrival_time.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    patients = result.scalars().all()
    
    summaries = []
    for p in patients:
        # Get current bed number
        current_bed = None
        if p.current_bed_id:
            bed_result = await db.execute(select(Bed).where(Bed.id == p.current_bed_id))
            bed = bed_result.scalar_one_or_none()
            if bed:
                current_bed = bed.bed_number
        
        summaries.append(PatientSummary(
            id=p.id,
            mrn=p.mrn,
            name=p.name,
            acuity=p.acuity,
            chief_complaint=p.chief_complaint,
            arrival_time=p.arrival_time,
            current_bed=current_bed
        ))
    
    return summaries


@router.get("/patients/{patient_id}", response_model=PatientSchema)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific patient by ID"""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/patients/{patient_id}/trace", response_model=PatientTrace)
async def get_patient_trace(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Get patient trace with all events and metrics"""
    # Get patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get events
    events_result = await db.execute(
        select(Event)
        .where(Event.patient_id == patient_id)
        .order_by(Event.timestamp)
    )
    events = events_result.scalars().all()
    
    # Calculate metrics
    metrics = calculate_patient_metrics(patient, events)
    
    return PatientTrace(
        patient=patient,
        events=events,
        metrics=metrics
    )


def calculate_patient_metrics(patient: Patient, events: List[Event]) -> dict:
    """Calculate metrics for a patient journey"""
    metrics = {
        "total_events": len(events),
        "total_time_minutes": 0,
        "wait_time_minutes": 0,
        "imaging_time_minutes": 0,
        "handoffs": 0,
        "delays": []
    }
    
    arrival_time = None
    bed_assignment_time = None
    imaging_start = None
    
    for event in events:
        if event.event_type == EventType.ARRIVAL:
            arrival_time = event.timestamp
        elif event.event_type == EventType.BED_ASSIGNMENT:
            bed_assignment_time = event.timestamp
            if arrival_time:
                wait = (bed_assignment_time - arrival_time).total_seconds() / 60
                metrics["wait_time_minutes"] = round(wait, 1)
        elif event.event_type == EventType.IMAGING_START:
            imaging_start = event.timestamp
        elif event.event_type == EventType.IMAGING_END and imaging_start:
            imaging_time = (event.timestamp - imaging_start).total_seconds() / 60
            metrics["imaging_time_minutes"] = round(imaging_time, 1)
            imaging_start = None
        elif event.event_type == EventType.NURSE_ASSIGNMENT:
            metrics["handoffs"] += 1
    
    # Calculate total time
    if arrival_time:
        end_time = patient.discharge_time or events[-1].timestamp if events else arrival_time
        total_minutes = (end_time - arrival_time).total_seconds() / 60
        metrics["total_time_minutes"] = round(total_minutes, 1)
    
    return metrics


@router.get("/events", response_model=List[EventSchema])
async def get_events(
    db: AsyncSession = Depends(get_db),
    unit_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0
):
    """Get events with optional filters"""
    query = select(Event)
    
    conditions = []
    if unit_id:
        conditions.append(Event.unit_id == unit_id)
    if patient_id:
        conditions.append(Event.patient_id == patient_id)
    if event_type:
        conditions.append(Event.event_type == event_type)
    if start_time:
        conditions.append(Event.timestamp >= start_time)
    if end_time:
        conditions.append(Event.timestamp <= end_time)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Event.timestamp).limit(limit).offset(offset)
    
    result = await db.execute(query)
    events = result.scalars().all()
    return events


@router.get("/nurses", response_model=List[NurseWithAssignments])
async def get_nurses(
    db: AsyncSession = Depends(get_db),
    unit_id: Optional[int] = None
):
    """Get nurses with their current assignments"""
    query = select(Nurse)
    if unit_id:
        query = query.where(Nurse.unit_id == unit_id)
    
    result = await db.execute(query)
    nurses = result.scalars().all()
    
    nurses_with_assignments = []
    for nurse in nurses:
        # Get current shift
        shift_result = await db.execute(
            select(Shift)
            .where(Shift.nurse_id == nurse.id)
            .order_by(Shift.start_time.desc())
            .limit(1)
        )
        shift = shift_result.scalar_one_or_none()
        
        assigned_patients = shift.assigned_patients if shift else []
        
        nurses_with_assignments.append(NurseWithAssignments(
            id=nurse.id,
            unit_id=nurse.unit_id,
            name=nurse.name,
            employee_id=nurse.employee_id,
            specialty=nurse.specialty,
            max_patients=nurse.max_patients,
            assigned_patient_count=len(assigned_patients),
            assigned_patients=assigned_patients
        ))
    
    return nurses_with_assignments


@router.get("/metrics/kpi", response_model=KPIMetrics)
async def get_kpi_metrics(
    db: AsyncSession = Depends(get_db),
    unit_id: int = 1,
    timestamp: Optional[datetime] = None
):
    """Get current KPI metrics for a unit"""
    # Get bed counts
    total_beds_result = await db.execute(
        select(func.count(Bed.id)).where(Bed.unit_id == unit_id)
    )
    total_beds = total_beds_result.scalar() or 24
    
    occupied_beds_result = await db.execute(
        select(func.count(Bed.id)).where(
            and_(
                Bed.unit_id == unit_id,
                Bed.status == BedStatus.OCCUPIED
            )
        )
    )
    occupied_beds = occupied_beds_result.scalar() or 0
    
    # Calculate occupancy
    occupancy_percent = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
    
    # Get average LOS for discharged patients (last 24 hours)
    los_result = await db.execute(
        select(func.avg(
            func.extract('epoch', Patient.discharge_time - Patient.arrival_time) / 3600
        )).where(Patient.discharge_time.isnot(None))
    )
    avg_los = los_result.scalar() or 6.0
    
    # Get average time to bed
    time_to_bed_events = await db.execute(
        select(Event.data)
        .where(Event.event_type == EventType.BED_ASSIGNMENT)
        .order_by(Event.timestamp.desc())
        .limit(50)
    )
    wait_times = [e.get("wait_minutes", 30) for e in time_to_bed_events.scalars().all() if e]
    avg_time_to_bed = sum(wait_times) / len(wait_times) if wait_times else 30
    
    # Count SLA breaches (wait > 60 minutes)
    sla_breaches = len([w for w in wait_times if w > 60])
    
    # Get queue lengths (simplified)
    ed_waiting = await db.execute(
        select(func.count(Patient.id)).where(
            and_(
                Patient.current_bed_id.is_(None),
                Patient.discharge_time.is_(None)
            )
        )
    )
    ed_waiting_count = ed_waiting.scalar() or 0
    
    # Nurse load (simplified)
    nurse_count = await db.execute(
        select(func.count(Nurse.id)).where(Nurse.unit_id == unit_id)
    )
    nurses = nurse_count.scalar() or 6
    nurse_load = occupied_beds / nurses if nurses > 0 else 0
    
    return KPIMetrics(
        occupancy_percent=round(occupancy_percent, 1),
        average_los_hours=round(avg_los, 1),
        average_time_to_bed_minutes=round(avg_time_to_bed, 1),
        sla_breaches=sla_breaches,
        imaging_queue_length=0,  # Would need more complex query
        ed_waiting_count=ed_waiting_count,
        nurse_load_average=round(nurse_load, 2)
    )
