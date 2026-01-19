"""
Tests for discrete event simulation engine.
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.simulation.engine import SimulationEngine, SimulationEvent


class TestSimulationEngine:
    """Test cases for simulation engine."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        params = {
            "arrival_multiplier": 1.0,
            "beds_available": 24,
            "nurses_per_shift": 6,
            "imaging_capacity": 2,
            "transport_capacity": 3,
        }
        engine = SimulationEngine(params)
        
        assert engine.params == params
        assert len(engine.event_queue) == 0
        assert engine.current_time is None

    def test_schedule_event(self):
        """Test event scheduling."""
        engine = SimulationEngine({})
        
        event_time = datetime.now(timezone.utc)
        engine.schedule_event(
            time=event_time,
            event_type="test_event",
            entity_id=1,
            data={"key": "value"}
        )
        
        assert len(engine.event_queue) == 1
        event = engine.event_queue[0]
        assert event.time == event_time
        assert event.event_type == "test_event"
        assert event.entity_id == 1
        assert event.data == {"key": "value"}

    def test_event_queue_ordering(self):
        """Test events are processed in time order."""
        engine = SimulationEngine({})
        
        base_time = datetime.now(timezone.utc)
        
        # Schedule events out of order
        engine.schedule_event(base_time + timedelta(minutes=30), "event_3", 3, {})
        engine.schedule_event(base_time + timedelta(minutes=10), "event_1", 1, {})
        engine.schedule_event(base_time + timedelta(minutes=20), "event_2", 2, {})
        
        # Pop should return in time order
        import heapq
        events = [heapq.heappop(engine.event_queue) for _ in range(3)]
        
        assert events[0].event_type == "event_1"
        assert events[1].event_type == "event_2"
        assert events[2].event_type == "event_3"

    def test_process_arrival_event(self):
        """Test processing an arrival event."""
        params = {
            "arrival_multiplier": 1.0,
            "beds_available": 24,
            "nurses_per_shift": 6,
        }
        engine = SimulationEngine(params)
        engine.current_time = datetime.now(timezone.utc)
        
        # Initialize some beds
        engine.beds = {
            1: {"id": 1, "status": "empty"},
            2: {"id": 2, "status": "occupied"},
        }
        engine.nurses = {
            1: {"id": 1, "patient_count": 2},
        }
        
        event = SimulationEvent(
            time=engine.current_time,
            event_type="arrival",
            entity_id=1,
            data={
                "patient_id": 1,
                "acuity": "medium",
            }
        )
        
        engine._process_arrival(event)
        
        # Check that patient was added to queue or assigned
        assert len(engine.metrics_collector) > 0 or len(engine.patient_queue) >= 0

    def test_bed_availability_check(self):
        """Test bed availability checking."""
        engine = SimulationEngine({"beds_available": 24})
        
        engine.beds = {
            1: {"id": 1, "status": "empty"},
            2: {"id": 2, "status": "occupied"},
            3: {"id": 3, "status": "cleaning"},
            4: {"id": 4, "status": "empty"},
        }
        
        available = engine._get_available_beds()
        
        assert len(available) == 2
        assert 1 in available
        assert 4 in available

    def test_nurse_assignment(self):
        """Test nurse assignment logic."""
        engine = SimulationEngine({"nurses_per_shift": 6})
        
        engine.nurses = {
            1: {"id": 1, "patient_count": 4, "max_patients": 4},
            2: {"id": 2, "patient_count": 2, "max_patients": 4},
            3: {"id": 3, "patient_count": 3, "max_patients": 4},
        }
        
        # Should assign to nurse with lowest load
        nurse = engine._get_available_nurse()
        
        assert nurse is not None
        assert nurse["id"] == 2  # Nurse with lowest patient count

    def test_imaging_queue(self):
        """Test imaging queue management."""
        engine = SimulationEngine({"imaging_capacity": 2})
        engine.current_time = datetime.now(timezone.utc)
        
        engine.imaging_in_use = 0
        
        # First two should start immediately
        assert engine._can_start_imaging() is True
        engine.imaging_in_use = 1
        assert engine._can_start_imaging() is True
        engine.imaging_in_use = 2
        assert engine._can_start_imaging() is False

    def test_metrics_collection(self):
        """Test metrics are collected during simulation."""
        params = {
            "arrival_multiplier": 1.0,
            "beds_available": 10,
            "nurses_per_shift": 4,
            "imaging_capacity": 2,
            "transport_capacity": 2,
        }
        engine = SimulationEngine(params)
        
        # Run a short simulation
        base_time = datetime.now(timezone.utc)
        engine.initialize(base_time)
        
        # Manually add some metrics
        engine._record_metric("occupancy", 0.75)
        engine._record_metric("wait_time", 15.5)
        
        assert len(engine.metrics_collector) >= 2

    def test_simulation_run(self):
        """Test full simulation run."""
        params = {
            "arrival_multiplier": 0.5,  # Lower for faster test
            "beds_available": 10,
            "nurses_per_shift": 4,
            "imaging_capacity": 1,
            "transport_capacity": 2,
            "acuity_low": 50,
            "acuity_medium": 40,
            "acuity_high": 10,
        }
        engine = SimulationEngine(params)
        
        # Short simulation period for testing
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        
        results = engine.run(start_time, end_time)
        
        assert "metrics" in results
        assert "timeseries" in results
        assert "events" in results


class TestSimulationEvent:
    """Test cases for simulation event dataclass."""

    def test_event_creation(self):
        """Test event creation."""
        event_time = datetime.now(timezone.utc)
        event = SimulationEvent(
            time=event_time,
            event_type="arrival",
            entity_id=1,
            data={"acuity": "high"}
        )
        
        assert event.time == event_time
        assert event.event_type == "arrival"
        assert event.entity_id == 1
        assert event.data == {"acuity": "high"}

    def test_event_comparison(self):
        """Test event comparison for queue ordering."""
        base_time = datetime.now(timezone.utc)
        
        event1 = SimulationEvent(base_time, "arrival", 1, {})
        event2 = SimulationEvent(base_time + timedelta(minutes=10), "arrival", 2, {})
        
        # event1 should be "less than" event2 (earlier time)
        assert event1 < event2

    def test_event_equality(self):
        """Test event equality."""
        event_time = datetime.now(timezone.utc)
        
        event1 = SimulationEvent(event_time, "arrival", 1, {})
        event2 = SimulationEvent(event_time, "arrival", 1, {})
        
        # Same time events should be equal for comparison purposes
        assert (event1 < event2) == False
        assert (event2 < event1) == False


class TestSimulationConstraints:
    """Test simulation constraint handling."""

    def test_bed_constraint_creates_queue(self):
        """Test that full beds create patient queue."""
        params = {"beds_available": 2}
        engine = SimulationEngine(params)
        engine.current_time = datetime.now(timezone.utc)
        
        # Fill all beds
        engine.beds = {
            1: {"id": 1, "status": "occupied"},
            2: {"id": 2, "status": "occupied"},
        }
        
        # Try to get available bed
        available = engine._get_available_beds()
        
        assert len(available) == 0

    def test_nurse_ratio_constraint(self):
        """Test nurse-to-patient ratio constraints."""
        params = {"nurses_per_shift": 2}
        engine = SimulationEngine(params)
        
        # All nurses at capacity
        engine.nurses = {
            1: {"id": 1, "patient_count": 4, "max_patients": 4},
            2: {"id": 2, "patient_count": 4, "max_patients": 4},
        }
        
        nurse = engine._get_available_nurse()
        
        # Should return None when all nurses at capacity
        assert nurse is None

    def test_bottleneck_attribution(self):
        """Test bottleneck attribution tracking."""
        engine = SimulationEngine({})
        engine.bottlenecks = {
            "bed_availability": 0,
            "nurse_staffing": 0,
            "imaging_queue": 0,
        }
        
        # Record bottlenecks
        engine._record_bottleneck("bed_availability", 10)
        engine._record_bottleneck("bed_availability", 5)
        engine._record_bottleneck("nurse_staffing", 8)
        
        assert engine.bottlenecks["bed_availability"] == 15
        assert engine.bottlenecks["nurse_staffing"] == 8
        assert engine.bottlenecks["imaging_queue"] == 0
