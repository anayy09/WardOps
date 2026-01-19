"""
Synthetic Data Generator for WardOps Digital Twin

Generates realistic hospital operations data with deterministic seeding.
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.models import (
    Unit, Bed, BedStatus, Nurse, Shift, Patient, AcuityLevel,
    Event, EventType, Scenario, PolicyDoc
)


def convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to native Python types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(convert_numpy_types(item) for item in obj)
    return obj


# Constants
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
]

CHIEF_COMPLAINTS = [
    "Chest pain", "Shortness of breath", "Abdominal pain", "Headache",
    "Back pain", "Fever", "Nausea and vomiting", "Dizziness",
    "Weakness", "Cough", "Fall", "Altered mental status",
    "Leg pain", "Arm pain", "Syncope", "Seizure",
    "Urinary symptoms", "Rash", "Eye pain", "Ear pain"
]

NURSE_NAMES = [
    "Sarah Chen", "Michael Rodriguez", "Emily Johnson", "David Kim",
    "Jessica Williams", "Robert Garcia", "Amanda Martinez", "James Wilson",
    "Nicole Brown", "Christopher Lee", "Stephanie Davis", "Matthew Anderson",
    "Rachel Thomas", "Daniel Taylor", "Lauren Moore", "Kevin Jackson",
    "Ashley Martin", "Brian White", "Megan Harris", "Justin Clark"
]


@dataclass
class GeneratorConfig:
    """Configuration for data generation"""
    seed: int = 42
    simulation_date: datetime = field(default_factory=lambda: datetime(2026, 1, 15, 0, 0, 0))
    duration_hours: int = 24
    
    # Unit configuration
    unit_name: str = "Medical Unit A"
    unit_code: str = "MED-A"
    bed_count: int = 24
    
    # Arrival rates
    base_arrivals_per_hour: float = 12.5  # ~300 per day
    arrival_multiplier: float = 1.0
    
    # Acuity distribution
    acuity_distribution: Dict[str, float] = field(default_factory=lambda: {
        "low": 0.3,
        "medium": 0.5,
        "high": 0.15,
        "critical": 0.05
    })
    
    # Staffing
    nurses_per_shift: Dict[str, int] = field(default_factory=lambda: {
        "day": 6,
        "evening": 5,
        "night": 4
    })
    
    # Service times (in minutes)
    triage_time: Tuple[int, int] = (5, 15)
    bed_wait_time: Tuple[int, int] = (10, 120)
    imaging_probability: float = 0.4
    imaging_time: Tuple[int, int] = (20, 60)
    consult_probability: float = 0.25
    consult_time: Tuple[int, int] = (30, 90)
    cleaning_time: Tuple[int, int] = (15, 30)
    
    # Length of stay by acuity (hours)
    los_by_acuity: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "low": (2, 6),
        "medium": (4, 12),
        "high": (8, 24),
        "critical": (12, 48)
    })


class SyntheticDataGenerator:
    """Generates synthetic hospital operations data"""
    
    def __init__(self, config: GeneratorConfig = None):
        self.config = config or GeneratorConfig()
        self.rng = np.random.default_rng(self.config.seed)
        random.seed(self.config.seed)
        
        # Generated data containers
        self.unit: Unit = None
        self.beds: List[Bed] = []
        self.nurses: List[Nurse] = []
        self.shifts: List[Shift] = []
        self.patients: List[Patient] = []
        self.events: List[Event] = []
        
        # Tracking state
        self._patient_counter = 0
        self._event_counter = 0
        
    def generate_all(self) -> Dict[str, Any]:
        """Generate complete dataset"""
        self._generate_unit()
        self._generate_beds()
        self._generate_nurses()
        self._generate_shifts()
        self._generate_patients_and_events()
        
        return {
            "unit": self.unit,
            "beds": self.beds,
            "nurses": self.nurses,
            "shifts": self.shifts,
            "patients": self.patients,
            "events": self.events
        }
    
    def _generate_unit(self):
        """Generate the hospital unit"""
        self.unit = Unit(
            id=1,
            name=self.config.unit_name,
            code=self.config.unit_code,
            floor=1,
            capacity=self.config.bed_count,
            unit_type="medical"
        )
    
    def _generate_beds(self):
        """Generate beds with positions for visualization"""
        # Layout: 6 rows x 4 columns for 24 beds
        rows, cols = 6, 4
        bed_width, bed_height = 80, 60
        spacing_x, spacing_y = 120, 100
        start_x, start_y = 100, 100
        
        bed_num = 0
        for row in range(rows):
            for col in range(cols):
                bed_num += 1
                
                # Determine bed type (2 isolation beds)
                bed_type = "isolation" if bed_num in [1, 24] else "standard"
                
                bed = Bed(
                    id=bed_num,
                    unit_id=1,
                    bed_number=f"{self.config.unit_code}-{bed_num:02d}",
                    bed_type=bed_type,
                    status="empty",
                    x_position=start_x + col * spacing_x,
                    y_position=start_y + row * spacing_y
                )
                self.beds.append(bed)
    
    def _generate_nurses(self):
        """Generate nursing staff"""
        nurse_names_copy = NURSE_NAMES.copy()
        random.shuffle(nurse_names_copy)
        
        total_nurses = sum(self.config.nurses_per_shift.values())
        
        for i in range(min(total_nurses, len(nurse_names_copy))):
            nurse = Nurse(
                id=i + 1,
                unit_id=1,
                name=nurse_names_copy[i],
                employee_id=f"N{1000 + i}",
                specialty=random.choice(["General", "Critical Care", "Med-Surg"]),
                max_patients=4
            )
            self.nurses.append(nurse)
    
    def _generate_shifts(self):
        """Generate shift assignments"""
        sim_date = self.config.simulation_date.date()
        
        shift_times = {
            "day": (7, 15),      # 7am - 3pm
            "evening": (15, 23),  # 3pm - 11pm
            "night": (23, 7)      # 11pm - 7am (next day)
        }
        
        nurse_idx = 0
        shift_id = 1
        
        for shift_type, (start_hour, end_hour) in shift_times.items():
            num_nurses = self.config.nurses_per_shift[shift_type]
            
            for _ in range(num_nurses):
                if nurse_idx >= len(self.nurses):
                    break
                
                start_dt = datetime.combine(sim_date, datetime.min.time().replace(hour=start_hour))
                if shift_type == "night":
                    end_dt = datetime.combine(sim_date + timedelta(days=1), datetime.min.time().replace(hour=end_hour))
                else:
                    end_dt = datetime.combine(sim_date, datetime.min.time().replace(hour=end_hour))
                
                shift = Shift(
                    id=shift_id,
                    nurse_id=self.nurses[nurse_idx].id,
                    shift_date=start_dt,
                    shift_type=shift_type,
                    start_time=start_dt,
                    end_time=end_dt,
                    assigned_patients=[]
                )
                self.shifts.append(shift)
                
                nurse_idx += 1
                shift_id += 1
    
    def _generate_patients_and_events(self):
        """Generate patients and their events throughout the day"""
        start_time = self.config.simulation_date
        end_time = start_time + timedelta(hours=self.config.duration_hours)
        
        # Generate arrival times using Poisson process
        arrivals_per_hour = self.config.base_arrivals_per_hour * self.config.arrival_multiplier
        
        current_time = start_time
        
        # Track bed state
        bed_occupancy = {bed.id: None for bed in self.beds}
        bed_available_at = {bed.id: start_time for bed in self.beds}
        
        while current_time < end_time:
            # Time to next arrival (exponential)
            inter_arrival = float(self.rng.exponential(60 / arrivals_per_hour))
            current_time += timedelta(minutes=inter_arrival)
            
            if current_time >= end_time:
                break
            
            # Generate patient
            patient = self._generate_patient(current_time)
            self.patients.append(patient)
            
            # Generate events for this patient
            self._generate_patient_journey(
                patient, 
                current_time, 
                end_time,
                bed_occupancy,
                bed_available_at
            )
    
    def _generate_patient(self, arrival_time: datetime) -> Patient:
        """Generate a single patient"""
        self._patient_counter += 1
        
        # Determine acuity
        acuity_probs = list(self.config.acuity_distribution.values())
        acuity_choices = list(self.config.acuity_distribution.keys())
        acuity = str(self.rng.choice(acuity_choices, p=acuity_probs))
        
        # Generate demographics
        gender = str(self.rng.choice(["Male", "Female"]))
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        age = int(self.rng.normal(55, 20))
        age = max(18, min(95, age))
        
        # Determine if requires imaging or consult
        requires_imaging = bool(self.rng.random() < self.config.imaging_probability)
        requires_consult = bool(self.rng.random() < self.config.consult_probability)
        
        # Higher acuity = higher chance of isolation
        isolation_prob = {"low": 0.02, "medium": 0.05, "high": 0.1, "critical": 0.15}
        is_isolation = self.rng.random() < isolation_prob.get(acuity, 0.05)
        
        return Patient(
            id=self._patient_counter,
            mrn=f"MRN{100000 + self._patient_counter}",
            name=f"{first_name} {last_name}",
            age=age,
            gender=gender,
            acuity=acuity,
            chief_complaint=random.choice(CHIEF_COMPLAINTS),
            arrival_time=arrival_time,
            is_isolation=is_isolation,
            requires_imaging=requires_imaging,
            requires_consult=requires_consult
        )
    
    def _generate_patient_journey(
        self, 
        patient: Patient, 
        arrival_time: datetime,
        sim_end_time: datetime,
        bed_occupancy: Dict[int, Any],
        bed_available_at: Dict[int, datetime]
    ):
        """Generate the complete event sequence for a patient"""
        current_time = arrival_time
        
        # Event 1: Arrival
        self._add_event("arrival", patient, current_time, data={
            "source": "ED",
            "chief_complaint": patient.chief_complaint
        })
        
        # Event 2: Triage
        triage_duration = int(self.rng.integers(*self.config.triage_time))
        current_time += timedelta(minutes=triage_duration)
        self._add_event("triage", patient, current_time, data={
            "acuity_assigned": patient.acuity,
            "duration_minutes": triage_duration
        })
        
        # Event 3: Admission Request
        current_time += timedelta(minutes=int(self.rng.integers(5, 15)))
        self._add_event("admission_request", patient, current_time)
        
        # Find available bed
        assigned_bed = None
        wait_for_bed = 0
        
        # Prefer isolation bed if needed
        bed_candidates = self.beds.copy()
        if patient.is_isolation:
            bed_candidates = sorted(bed_candidates, key=lambda b: b.bed_type != "isolation")
        
        for bed in bed_candidates:
            available_time = bed_available_at.get(bed.id, current_time)
            if available_time <= current_time or assigned_bed is None:
                if assigned_bed is None or available_time < bed_available_at.get(assigned_bed.id, datetime.max):
                    assigned_bed = bed
        
        if assigned_bed:
            wait_start = current_time
            current_time = max(current_time, bed_available_at.get(assigned_bed.id, current_time))
            wait_for_bed = (current_time - wait_start).total_seconds() / 60
            
            # Add some random additional wait
            extra_wait = int(self.rng.integers(5, 30))
            current_time += timedelta(minutes=extra_wait)
            wait_for_bed += extra_wait
            
            # Event 4: Bed Assignment
            self._add_event("bed_assignment", patient, current_time, 
                bed_id=assigned_bed.id,
                data={
                    "bed_number": assigned_bed.bed_number,
                    "wait_minutes": wait_for_bed
                }
            )
            
            # Update patient location
            patient.current_bed_id = assigned_bed.id
            patient.current_unit_id = 1
            
            # Mark bed as occupied
            bed_occupancy[assigned_bed.id] = patient.id
        
        # Assign nurse
        available_nurses = [n for n in self.nurses]
        if available_nurses:
            assigned_nurse = random.choice(available_nurses)
            current_time += timedelta(minutes=int(self.rng.integers(2, 10)))
            self._add_event("nurse_assignment", patient, current_time,
                nurse_id=assigned_nurse.id,
                data={"nurse_name": assigned_nurse.name}
            )
        
        # Event 5: Imaging (if required)
        if patient.requires_imaging and current_time < sim_end_time:
            # Request
            current_time += timedelta(minutes=int(self.rng.integers(15, 45)))
            self._add_event("imaging_request", patient, current_time,
                data={"imaging_type": random.choice(["X-ray", "CT", "MRI", "Ultrasound"])}
            )
            
            # Transport to imaging
            current_time += timedelta(minutes=int(self.rng.integers(10, 30)))
            self._add_event("transport_start", patient, current_time,
                data={"destination": "Radiology"}
            )
            
            # Imaging start
            current_time += timedelta(minutes=int(self.rng.integers(5, 15)))
            self._add_event("imaging_start", patient, current_time)
            
            # Imaging end
            imaging_duration = int(self.rng.integers(*self.config.imaging_time))
            current_time += timedelta(minutes=imaging_duration)
            self._add_event("imaging_end", patient, current_time,
                data={"duration_minutes": imaging_duration}
            )
            
            # Transport back
            current_time += timedelta(minutes=int(self.rng.integers(10, 20)))
            self._add_event("transport_end", patient, current_time)
        
        # Event 6: Consult (if required)
        if patient.requires_consult and current_time < sim_end_time:
            current_time += timedelta(minutes=int(self.rng.integers(30, 90)))
            self._add_event("consult_request", patient, current_time,
                data={"specialty": random.choice(["Cardiology", "Neurology", "Surgery", "Pulmonology"])}
            )
            
            current_time += timedelta(minutes=int(self.rng.integers(30, 120)))
            self._add_event("consult_start", patient, current_time)
            
            consult_duration = int(self.rng.integers(*self.config.consult_time))
            current_time += timedelta(minutes=consult_duration)
            self._add_event("consult_end", patient, current_time,
                data={"duration_minutes": consult_duration}
            )
        
        # Possible escalation for high acuity
        if patient.acuity in [AcuityLevel.HIGH, AcuityLevel.CRITICAL]:
            if self.rng.random() < 0.2:
                escalation_time = arrival_time + timedelta(
                    minutes=int(self.rng.integers(60, 300))
                )
                if escalation_time < sim_end_time:
                    self._add_event("escalation", patient, escalation_time,
                        data={
                            "reason": random.choice([
                                "Vitals deterioration",
                                "Pain increase",
                                "Respiratory distress",
                                "Mental status change"
                            ]),
                            "escalated_to": "Rapid Response Team"
                        }
                    )
        
        # Calculate length of stay
        los_range = self.config.los_by_acuity.get(patient.acuity, (4, 12))
        los_hours = float(self.rng.uniform(*los_range))
        
        # Event 7: Discharge (if within simulation window)
        discharge_time = arrival_time + timedelta(hours=los_hours)
        
        if discharge_time < sim_end_time:
            # Discharge event
            self._add_event("discharge", patient, discharge_time,
                bed_id=assigned_bed.id if assigned_bed else None,
                data={
                    "disposition": random.choice(["Home", "Home with services", "Rehab", "SNF"]),
                    "los_hours": los_hours
                }
            )
            patient.discharge_time = discharge_time
            
            # Cleaning events
            if assigned_bed:
                cleaning_start = discharge_time + timedelta(minutes=int(self.rng.integers(5, 15)))
                cleaning_duration = int(self.rng.integers(*self.config.cleaning_time))
                
                self._add_event("cleaning_start", None, cleaning_start,
                    bed_id=assigned_bed.id,
                    data={"bed_number": assigned_bed.bed_number}
                )
                
                cleaning_end = cleaning_start + timedelta(minutes=cleaning_duration)
                self._add_event("cleaning_end", None, cleaning_end,
                    bed_id=assigned_bed.id,
                    data={"duration_minutes": cleaning_duration}
                )
                
                # Update bed availability
                bed_available_at[assigned_bed.id] = cleaning_end
                bed_occupancy[assigned_bed.id] = None
    
    def _add_event(
        self, 
        event_type: str, 
        patient: Patient, 
        timestamp: datetime,
        unit_id: int = 1,
        bed_id: int = None,
        nurse_id: int = None,
        data: Dict = None
    ):
        """Add an event to the list"""
        self._event_counter += 1
        
        # Convert any numpy types in data to native Python types
        clean_data = convert_numpy_types(data) if data else {}
        
        event = Event(
            id=self._event_counter,
            patient_id=patient.id if patient else None,
            event_type=event_type,
            timestamp=timestamp,
            unit_id=unit_id,
            bed_id=bed_id,
            nurse_id=nurse_id,
            data=clean_data
        )
        self.events.append(event)


def generate_policy_docs() -> List[PolicyDoc]:
    """Generate mock policy documents for RAG"""
    
    docs = [
        PolicyDoc(
            id=1,
            title="Isolation Protocol",
            doc_type="protocol",
            content="""
# Isolation Protocol

## Purpose
This protocol establishes guidelines for patient isolation to prevent the spread of infectious diseases.

## Scope
Applies to all patients requiring contact, droplet, or airborne isolation precautions.

## Procedure

### 1. Identification of Isolation Need
- Patients with confirmed or suspected infectious conditions requiring isolation
- Patients with multi-drug resistant organisms (MDROs)
- Patients with respiratory infections requiring droplet precautions
- Patients requiring airborne isolation (e.g., TB, measles, varicella)

### 2. Room Assignment
- Isolation patients MUST be assigned to designated isolation rooms (Beds 1 and 24 in Medical Unit A)
- If no isolation room is available, patient must wait in ED isolation area
- Maximum wait time for isolation room: 2 hours (SLA)

### 3. PPE Requirements
- Contact: Gown and gloves
- Droplet: Surgical mask, gown, gloves
- Airborne: N95 respirator, gown, gloves, negative pressure room

### 4. Documentation
- Isolation status must be clearly documented in EMR
- Isolation signage must be posted outside room
- All visitors must be informed of isolation requirements

### 5. Nurse Assignment
- Isolation patients should be cohorted to same nurse when possible
- Nurse-to-patient ratio for isolation: Maximum 3:1

## Compliance
- Compliance audits conducted monthly
- Breaches must be reported via incident reporting system
"""
        ),
        
        PolicyDoc(
            id=2,
            title="Nurse Staffing Ratio Guidelines",
            doc_type="guideline",
            content="""
# Nurse Staffing Ratio Guidelines

## Purpose
To ensure safe and adequate nursing coverage for all patients based on acuity and unit type.

## Staffing Ratios by Unit Type

### Medical-Surgical Units
- Day Shift (7am-3pm): 1:4 (one nurse to four patients)
- Evening Shift (3pm-11pm): 1:5
- Night Shift (11pm-7am): 1:6

### Critical Adjustments
- If unit acuity index exceeds 2.5: Reduce ratios by 1 patient
- If more than 20% patients are high acuity: Request additional staff

### ICU/Step-down
- ICU: 1:2 (1:1 for unstable patients)
- Step-down: 1:3

## Acuity-Based Adjustments

### Patient Acuity Levels
- Low (1-2): Stable, minimal interventions
- Medium (3): Regular monitoring, moderate interventions
- High (4): Frequent monitoring, multiple interventions
- Critical (5): Continuous monitoring, complex care

### Staffing Triggers
- Average unit acuity > 3.5: Escalate to charge nurse
- Average unit acuity > 4.0: Escalate to nursing supervisor
- More than 3 patients acuity 5: Request ICU transfer evaluation

## Shift Handoff
- Handoff duration: Minimum 15 minutes per patient
- All high-acuity patients require bedside handoff
- Documentation must be current before handoff

## Compliance Monitoring
- Real-time dashboard tracking nurse-to-patient ratios
- Automatic alerts when ratios exceeded
- Monthly staffing adequacy reports
"""
        ),
        
        PolicyDoc(
            id=3,
            title="Transport Service Level Agreement",
            doc_type="sla",
            content="""
# Transport Service Level Agreement (SLA)

## Purpose
Define response time standards for patient transport services.

## Transport Categories

### Emergent (STAT)
- Definition: Life-threatening situation, immediate transport required
- Response time: Within 5 minutes
- Examples: Code situations, critical imaging, OR emergencies

### Urgent
- Definition: Time-sensitive but not immediately life-threatening
- Response time: Within 15 minutes
- Examples: Scheduled OR, urgent imaging, procedural areas

### Routine
- Definition: Scheduled transports, non-time-sensitive
- Response time: Within 30 minutes
- Examples: Discharge transports, routine testing, room transfers

## Performance Standards

### Response Time Compliance
- STAT: 95% within 5 minutes
- Urgent: 90% within 15 minutes
- Routine: 85% within 30 minutes

### Transport Capacity
- Minimum 2 transport staff on duty per shift
- Peak hours (7am-7pm): 4 transport staff minimum
- Wheelchair availability: 10 minimum on each floor

## Escalation Process
1. If transport not arrived within SLA: Contact transport dispatch
2. If still delayed after 10 minutes: Escalate to transport supervisor
3. If patient condition changes during wait: Re-triage transport priority

## Documentation Requirements
- Transport request time must be documented
- Transport arrival time must be documented
- Any delays must be documented with reason code

## Monitoring
- Real-time transport queue dashboard
- Daily compliance reports
- Monthly SLA review meetings
"""
        ),
        
        PolicyDoc(
            id=4,
            title="Imaging Priority and Scheduling Rules",
            doc_type="guideline",
            content="""
# Imaging Priority and Scheduling Rules

## Purpose
Establish prioritization framework for imaging services to optimize patient flow and clinical outcomes.

## Priority Levels

### Priority 1 - STAT (Emergent)
- Timeframe: Immediate, within 30 minutes
- Criteria:
  - Active stroke symptoms (CT/MRI head)
  - Acute chest pain with ECG changes (CT chest)
  - Trauma with hemodynamic instability
  - Suspected pulmonary embolism
- Authorization: ED physician or hospitalist can order directly

### Priority 2 - Urgent
- Timeframe: Within 2 hours
- Criteria:
  - New neurological deficits (non-stroke)
  - Acute abdominal pain with concerning exam
  - Suspected appendicitis, cholecystitis
  - Post-procedural concerns
- Authorization: Attending physician order required

### Priority 3 - Same Day
- Timeframe: Within 8 hours
- Criteria:
  - Pre-operative imaging
  - Follow-up imaging for known conditions
  - Discharge planning imaging
- Authorization: Standard physician order

### Priority 4 - Routine
- Timeframe: Within 24 hours
- Criteria:
  - Screening studies
  - Chronic condition monitoring
  - Non-urgent follow-up
- Authorization: Standard physician order

## Capacity Management

### Imaging Equipment Availability
- CT: 2 scanners, one reserved for STAT
- MRI: 1 scanner, 2 STAT slots per shift
- X-ray: 3 rooms plus portable
- Ultrasound: 2 rooms

### Queue Management Rules
- STAT imaging bumps all lower priorities
- Maximum wait time before escalation:
  - Priority 1: 15 minutes
  - Priority 2: 1 hour
  - Priority 3: 4 hours
  - Priority 4: 8 hours

## Communication Requirements
- STAT results: Call attending within 15 minutes of completion
- Urgent results: Call attending within 1 hour
- Critical findings: Immediate notification per critical results policy

## Performance Metrics
- STAT completion rate within 30 minutes: Target 95%
- Urgent completion rate within 2 hours: Target 90%
- Overall imaging turnaround time tracked daily
"""
        ),
        
        PolicyDoc(
            id=5,
            title="Bed Management and Patient Flow Protocol",
            doc_type="protocol",
            content="""
# Bed Management and Patient Flow Protocol

## Purpose
Optimize patient flow and bed utilization to reduce wait times and improve throughput.

## Bed Status Definitions

### Empty
- Bed is clean, ready for immediate patient placement
- Target: Maintain 10% of beds in empty status

### Occupied
- Patient currently assigned to bed
- Standard patient care in progress

### Cleaning
- Patient discharged, awaiting environmental services
- Target cleaning time: 30 minutes maximum

### Blocked
- Bed temporarily unavailable (maintenance, equipment issue)
- Must be documented with expected resolution time

### Isolation
- Designated for isolation patients only
- Cannot be used for non-isolation patients unless all isolation patients placed

## Bed Assignment Rules

### Priority Order for Bed Assignment
1. ED patients waiting > 4 hours (boarding)
2. ICU step-down patients (create ICU capacity)
3. Post-surgical patients
4. Direct admissions
5. Internal transfers

### Matching Criteria
- Acuity level appropriate for unit
- Isolation requirements met
- Gender-appropriate room (semi-private)
- Special equipment needs available

## Discharge Planning

### Predicted Discharge
- All patients must have predicted discharge date within 24 hours of admission
- Discharge planning rounds: Daily at 10am
- Update discharge prediction if status changes

### Discharge Process Timeline
- Discharge order to patient departure: Target 2 hours
- Bed cleaning notification: Within 5 minutes of departure
- Bed ready notification: Within 35 minutes of departure

## Escalation Triggers

### Capacity Alert Levels
- Yellow: Occupancy > 85%
- Orange: Occupancy > 90%
- Red: Occupancy > 95% or ED boarding > 4 hours

### Actions by Alert Level
- Yellow: Review all potential discharges, expedite
- Orange: Activate surge protocols, notify administration
- Red: Implement full surge plan, consider diversion

## Performance Metrics
- ED boarding time (time from admission decision to bed)
- Bed turnaround time (discharge to next patient)
- Occupancy rate by time of day
- Discharge before noon percentage
"""
        )
    ]
    
    return docs


def generate_baseline_scenario() -> Scenario:
    """Generate the baseline scenario"""
    return Scenario(
        id=1,
        name="Baseline - Normal Operations",
        description="Standard day operations with typical arrival patterns and staffing",
        is_baseline=True,
        parameters={
            "arrival_multiplier": 1.0,
            "acuity_mix": {"low": 0.3, "medium": 0.5, "high": 0.15, "critical": 0.05},
            "beds_available": 24,
            "nurse_count": {"day": 6, "evening": 5, "night": 4},
            "imaging_capacity": 1.0,
            "transport_capacity": 1.0
        }
    )
