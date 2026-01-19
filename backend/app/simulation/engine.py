"""
Discrete Event Simulation (DES) Engine for Hospital Operations

Simulates patient flow through a hospital unit with:
- Arrivals, triage, bed assignment, imaging, consults, discharge
- Resource constraints: beds, nurses, imaging equipment, transport
- Tracks metrics: wait times, occupancy, queue lengths, bottlenecks
"""

import heapq
import random
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import defaultdict


class EntityType(Enum):
    PATIENT = "patient"
    BED = "bed"
    NURSE = "nurse"
    IMAGING = "imaging"
    TRANSPORT = "transport"


class SimEventType(Enum):
    ARRIVAL = "arrival"
    TRIAGE_START = "triage_start"
    TRIAGE_END = "triage_end"
    BED_REQUEST = "bed_request"
    BED_ASSIGNED = "bed_assigned"
    IMAGING_REQUEST = "imaging_request"
    IMAGING_START = "imaging_start"
    IMAGING_END = "imaging_end"
    CONSULT_REQUEST = "consult_request"
    CONSULT_END = "consult_end"
    DISCHARGE = "discharge"
    CLEANING_START = "cleaning_start"
    CLEANING_END = "cleaning_end"


@dataclass(order=True)
class SimEvent:
    """An event in the simulation"""
    time: float
    event_type: SimEventType = field(compare=False)
    entity_id: int = field(compare=False)
    data: Dict[str, Any] = field(default_factory=dict, compare=False)


@dataclass
class SimPatient:
    """A patient entity in the simulation"""
    id: int
    acuity: str  # low, medium, high, critical
    arrival_time: float
    requires_imaging: bool = False
    requires_consult: bool = False
    
    # Timestamps
    triage_time: Optional[float] = None
    bed_assigned_time: Optional[float] = None
    imaging_start_time: Optional[float] = None
    imaging_end_time: Optional[float] = None
    discharge_time: Optional[float] = None
    
    # Assignment
    bed_id: Optional[int] = None
    nurse_id: Optional[int] = None


@dataclass
class SimBed:
    """A bed resource in the simulation"""
    id: int
    bed_type: str = "standard"
    is_occupied: bool = False
    is_cleaning: bool = False
    patient_id: Optional[int] = None
    available_at: float = 0


@dataclass
class SimNurse:
    """A nurse resource in the simulation"""
    id: int
    max_patients: int = 4
    assigned_patients: List[int] = field(default_factory=list)
    shift_start: float = 0
    shift_end: float = 480  # 8 hours in minutes


class SimulationEngine:
    """
    Discrete Event Simulation engine for hospital operations.
    
    Uses an event-driven approach where time advances to the next scheduled event.
    """
    
    def __init__(self, parameters: Dict[str, Any], seed: int = 42):
        self.params = parameters
        self.rng = np.random.default_rng(seed)
        random.seed(seed)
        
        # Simulation state
        self.current_time = 0.0
        self.end_time = 24 * 60  # 24 hours in minutes
        
        # Event queue (min-heap)
        self.event_queue: List[SimEvent] = []
        
        # Entities
        self.patients: Dict[int, SimPatient] = {}
        self.beds: Dict[int, SimBed] = {}
        self.nurses: Dict[int, SimNurse] = {}
        
        # Queues
        self.bed_queue: List[int] = []  # patient IDs waiting for beds
        self.imaging_queue: List[int] = []
        self.transport_queue: List[int] = []
        
        # Resource pools
        self.imaging_capacity = int(parameters.get("imaging_capacity", 1.0) * 2)
        self.imaging_in_use = 0
        self.transport_capacity = int(parameters.get("transport_capacity", 1.0) * 2)
        self.transport_in_use = 0
        
        # Counters
        self.patient_counter = 0
        
        # Metrics collection
        self.timeseries = defaultdict(list)
        self.patient_outcomes: List[Dict] = []
        self.bottleneck_events: List[Dict] = []
        
        # Initialize resources
        self._initialize_resources()
    
    def _initialize_resources(self):
        """Set up beds and nurses based on parameters"""
        # Create beds
        num_beds = self.params.get("beds_available", 24)
        for i in range(1, num_beds + 1):
            bed_type = "isolation" if i in [1, num_beds] else "standard"
            self.beds[i] = SimBed(id=i, bed_type=bed_type)
        
        # Create nurses (simplified - one set for the day)
        nurse_count = self.params.get("nurse_count", {}).get("day", 6)
        for i in range(1, nurse_count + 1):
            self.nurses[i] = SimNurse(id=i)
    
    def _schedule_event(self, event: SimEvent):
        """Add an event to the queue"""
        heapq.heappush(self.event_queue, event)
    
    def _generate_arrivals(self):
        """Generate patient arrival events"""
        arrival_rate = 12.5 * self.params.get("arrival_multiplier", 1.0)  # per hour
        acuity_mix = self.params.get("acuity_mix", {
            "low": 0.3, "medium": 0.5, "high": 0.15, "critical": 0.05
        })
        
        current_arrival = 0.0
        while current_arrival < self.end_time:
            # Exponential inter-arrival time
            inter_arrival = self.rng.exponential(60 / arrival_rate)
            current_arrival += inter_arrival
            
            if current_arrival >= self.end_time:
                break
            
            self.patient_counter += 1
            
            # Determine acuity
            acuity = self.rng.choice(
                list(acuity_mix.keys()),
                p=list(acuity_mix.values())
            )
            
            # Schedule arrival
            self._schedule_event(SimEvent(
                time=current_arrival,
                event_type=SimEventType.ARRIVAL,
                entity_id=self.patient_counter,
                data={
                    "acuity": acuity,
                    "requires_imaging": self.rng.random() < 0.4,
                    "requires_consult": self.rng.random() < 0.25
                }
            ))
    
    def _handle_arrival(self, event: SimEvent):
        """Process patient arrival"""
        patient = SimPatient(
            id=event.entity_id,
            acuity=event.data["acuity"],
            arrival_time=event.time,
            requires_imaging=event.data["requires_imaging"],
            requires_consult=event.data["requires_consult"]
        )
        self.patients[patient.id] = patient
        
        # Schedule triage
        triage_duration = self.rng.integers(5, 15)
        self._schedule_event(SimEvent(
            time=event.time + triage_duration,
            event_type=SimEventType.TRIAGE_END,
            entity_id=patient.id
        ))
    
    def _handle_triage_end(self, event: SimEvent):
        """Process triage completion and request bed"""
        patient = self.patients[event.entity_id]
        patient.triage_time = event.time
        
        # Request bed
        self._request_bed(patient.id, event.time)
    
    def _request_bed(self, patient_id: int, time: float):
        """Try to assign a bed or add to queue"""
        patient = self.patients[patient_id]
        
        # Find available bed
        available_bed = None
        for bed in self.beds.values():
            if not bed.is_occupied and not bed.is_cleaning and bed.available_at <= time:
                available_bed = bed
                break
        
        if available_bed:
            self._assign_bed(patient, available_bed, time)
        else:
            # Add to queue
            self.bed_queue.append(patient_id)
            self.bottleneck_events.append({
                "time": time,
                "constraint": "bed_availability",
                "patient_id": patient_id,
                "queue_length": len(self.bed_queue)
            })
    
    def _assign_bed(self, patient: SimPatient, bed: SimBed, time: float):
        """Assign a bed to a patient"""
        bed.is_occupied = True
        bed.patient_id = patient.id
        patient.bed_id = bed.id
        patient.bed_assigned_time = time
        
        # Assign nurse
        self._assign_nurse(patient, time)
        
        # Schedule imaging if needed
        if patient.requires_imaging:
            imaging_delay = self.rng.integers(15, 45)
            self._schedule_event(SimEvent(
                time=time + imaging_delay,
                event_type=SimEventType.IMAGING_REQUEST,
                entity_id=patient.id
            ))
        
        # Calculate length of stay
        los_ranges = {
            "low": (120, 360),      # 2-6 hours
            "medium": (240, 720),   # 4-12 hours
            "high": (480, 1440),    # 8-24 hours
            "critical": (720, 2880) # 12-48 hours
        }
        los_range = los_ranges.get(patient.acuity, (240, 720))
        los_minutes = self.rng.integers(*los_range)
        
        # Schedule discharge
        discharge_time = time + los_minutes
        if discharge_time < self.end_time:
            self._schedule_event(SimEvent(
                time=discharge_time,
                event_type=SimEventType.DISCHARGE,
                entity_id=patient.id
            ))
    
    def _assign_nurse(self, patient: SimPatient, time: float):
        """Assign a nurse to a patient"""
        # Find nurse with lowest load
        best_nurse = None
        min_load = float('inf')
        
        for nurse in self.nurses.values():
            load = len(nurse.assigned_patients)
            if load < nurse.max_patients and load < min_load:
                best_nurse = nurse
                min_load = load
        
        if best_nurse:
            best_nurse.assigned_patients.append(patient.id)
            patient.nurse_id = best_nurse.id
        else:
            # Record staffing bottleneck
            self.bottleneck_events.append({
                "time": time,
                "constraint": "nurse_staffing",
                "patient_id": patient.id,
                "description": "All nurses at max capacity"
            })
    
    def _handle_imaging_request(self, event: SimEvent):
        """Process imaging request"""
        patient_id = event.entity_id
        
        if self.imaging_in_use < self.imaging_capacity:
            # Start imaging immediately
            self.imaging_in_use += 1
            self._schedule_event(SimEvent(
                time=event.time + self.rng.integers(20, 60),
                event_type=SimEventType.IMAGING_END,
                entity_id=patient_id
            ))
            self.patients[patient_id].imaging_start_time = event.time
        else:
            # Add to queue
            self.imaging_queue.append(patient_id)
            self.bottleneck_events.append({
                "time": event.time,
                "constraint": "imaging_capacity",
                "patient_id": patient_id,
                "queue_length": len(self.imaging_queue)
            })
    
    def _handle_imaging_end(self, event: SimEvent):
        """Process imaging completion"""
        self.patients[event.entity_id].imaging_end_time = event.time
        self.imaging_in_use -= 1
        
        # Process next in queue
        if self.imaging_queue:
            next_patient_id = self.imaging_queue.pop(0)
            self.imaging_in_use += 1
            self._schedule_event(SimEvent(
                time=event.time + self.rng.integers(20, 60),
                event_type=SimEventType.IMAGING_END,
                entity_id=next_patient_id
            ))
            self.patients[next_patient_id].imaging_start_time = event.time
    
    def _handle_discharge(self, event: SimEvent):
        """Process patient discharge"""
        patient = self.patients[event.entity_id]
        patient.discharge_time = event.time
        
        # Free bed
        if patient.bed_id:
            bed = self.beds[patient.bed_id]
            bed.is_occupied = False
            bed.is_cleaning = True
            bed.patient_id = None
            
            # Schedule cleaning end
            cleaning_time = self.rng.integers(15, 30)
            self._schedule_event(SimEvent(
                time=event.time + cleaning_time,
                event_type=SimEventType.CLEANING_END,
                entity_id=patient.bed_id,
                data={"bed_id": patient.bed_id}
            ))
        
        # Free nurse
        if patient.nurse_id:
            nurse = self.nurses[patient.nurse_id]
            if patient.id in nurse.assigned_patients:
                nurse.assigned_patients.remove(patient.id)
        
        # Record patient outcome
        self.patient_outcomes.append({
            "patient_id": patient.id,
            "acuity": patient.acuity,
            "wait_time": (patient.bed_assigned_time - patient.arrival_time) if patient.bed_assigned_time else None,
            "los": (patient.discharge_time - patient.arrival_time) if patient.discharge_time else None,
            "had_imaging": patient.requires_imaging,
            "imaging_delay": (patient.imaging_start_time - patient.bed_assigned_time) if patient.imaging_start_time and patient.bed_assigned_time else None
        })
    
    def _handle_cleaning_end(self, event: SimEvent):
        """Process bed cleaning completion"""
        bed_id = event.data["bed_id"]
        bed = self.beds[bed_id]
        bed.is_cleaning = False
        bed.available_at = event.time
        
        # Assign to waiting patient if any
        if self.bed_queue:
            patient_id = self.bed_queue.pop(0)
            patient = self.patients[patient_id]
            self._assign_bed(patient, bed, event.time)
    
    def _process_event(self, event: SimEvent):
        """Route event to appropriate handler"""
        handlers = {
            SimEventType.ARRIVAL: self._handle_arrival,
            SimEventType.TRIAGE_END: self._handle_triage_end,
            SimEventType.IMAGING_REQUEST: self._handle_imaging_request,
            SimEventType.IMAGING_END: self._handle_imaging_end,
            SimEventType.DISCHARGE: self._handle_discharge,
            SimEventType.CLEANING_END: self._handle_cleaning_end,
        }
        
        handler = handlers.get(event.event_type)
        if handler:
            handler(event)
    
    def _collect_metrics(self):
        """Collect metrics at current time"""
        # Occupancy
        occupied = sum(1 for b in self.beds.values() if b.is_occupied)
        total = len(self.beds)
        
        self.timeseries["time"].append(self.current_time)
        self.timeseries["occupancy"].append(occupied / total * 100 if total > 0 else 0)
        self.timeseries["bed_queue"].append(len(self.bed_queue))
        self.timeseries["imaging_queue"].append(len(self.imaging_queue))
        
        # Nurse load
        avg_load = np.mean([len(n.assigned_patients) for n in self.nurses.values()]) if self.nurses else 0
        self.timeseries["nurse_load"].append(avg_load)
    
    def run(self, progress_callback: Callable[[int], None] = None) -> Dict[str, Any]:
        """
        Run the simulation.
        
        Args:
            progress_callback: Optional callback for progress updates (0-100)
            
        Returns:
            Dictionary with metrics, timeseries, and bottlenecks
        """
        # Generate arrivals
        self._generate_arrivals()
        
        # Main simulation loop
        metric_interval = 15  # Collect metrics every 15 minutes
        last_metric_time = 0
        last_progress = 0
        
        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            # Process event
            self._process_event(event)
            
            # Collect metrics periodically
            if self.current_time - last_metric_time >= metric_interval:
                self._collect_metrics()
                last_metric_time = self.current_time
            
            # Report progress
            if progress_callback:
                progress = int(self.current_time / self.end_time * 100)
                if progress > last_progress:
                    progress_callback(progress)
                    last_progress = progress
        
        # Calculate final metrics
        return self._calculate_results()
    
    def _calculate_results(self) -> Dict[str, Any]:
        """Calculate final simulation results"""
        # Aggregate patient outcomes
        wait_times = [p["wait_time"] for p in self.patient_outcomes if p["wait_time"] is not None]
        los_times = [p["los"] for p in self.patient_outcomes if p["los"] is not None]
        
        # Bottleneck summary
        bottleneck_summary = defaultdict(lambda: {"count": 0, "total_queue": 0})
        for b in self.bottleneck_events:
            constraint = b["constraint"]
            bottleneck_summary[constraint]["count"] += 1
            if "queue_length" in b:
                bottleneck_summary[constraint]["total_queue"] += b["queue_length"]
        
        bottlenecks = []
        for constraint, data in bottleneck_summary.items():
            bottlenecks.append({
                "constraint": constraint,
                "impact_score": data["count"] / max(len(self.patient_outcomes), 1),
                "occurrences": data["count"],
                "avg_queue": data["total_queue"] / data["count"] if data["count"] > 0 else 0,
                "description": self._describe_bottleneck(constraint)
            })
        
        bottlenecks.sort(key=lambda x: x["impact_score"], reverse=True)
        
        return {
            "metrics": {
                "total_patients": len(self.patient_outcomes),
                "avg_wait_time_minutes": np.mean(wait_times) if wait_times else 0,
                "median_wait_time_minutes": np.median(wait_times) if wait_times else 0,
                "max_wait_time_minutes": max(wait_times) if wait_times else 0,
                "avg_los_minutes": np.mean(los_times) if los_times else 0,
                "sla_breaches": sum(1 for w in wait_times if w > 60),
                "avg_occupancy": np.mean(self.timeseries["occupancy"]) if self.timeseries["occupancy"] else 0,
                "peak_occupancy": max(self.timeseries["occupancy"]) if self.timeseries["occupancy"] else 0,
                "avg_nurse_load": np.mean(self.timeseries["nurse_load"]) if self.timeseries["nurse_load"] else 0,
            },
            "timeseries": dict(self.timeseries),
            "bottlenecks": bottlenecks[:5]  # Top 5 bottlenecks
        }
    
    def _describe_bottleneck(self, constraint: str) -> str:
        """Generate human-readable bottleneck description"""
        descriptions = {
            "bed_availability": "Insufficient bed capacity causing patient wait times",
            "nurse_staffing": "Nurse staffing ratios exceeded, delaying patient care",
            "imaging_capacity": "Imaging equipment utilization at maximum capacity",
            "transport_capacity": "Transport resources insufficient for demand"
        }
        return descriptions.get(constraint, f"Constraint: {constraint}")
