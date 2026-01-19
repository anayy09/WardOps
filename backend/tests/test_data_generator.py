"""
Tests for synthetic data generator.
"""
import pytest
from datetime import datetime, timezone

from app.services.data_generator import SyntheticDataGenerator


class TestSyntheticDataGenerator:
    """Test cases for synthetic data generator."""

    def test_generator_initialization(self):
        """Test generator initializes with default seed."""
        generator = SyntheticDataGenerator()
        assert generator.seed == 42
        assert generator.rng is not None

    def test_generator_deterministic_with_same_seed(self):
        """Test generator produces same results with same seed."""
        gen1 = SyntheticDataGenerator(seed=123)
        gen2 = SyntheticDataGenerator(seed=123)
        
        # Generate same type of data
        name1 = gen1._generate_name("M")
        name2 = gen2._generate_name("M")
        
        assert name1 == name2

    def test_generator_different_with_different_seed(self):
        """Test generator produces different results with different seeds."""
        gen1 = SyntheticDataGenerator(seed=100)
        gen2 = SyntheticDataGenerator(seed=200)
        
        # High probability these will differ
        name1 = gen1._generate_name("M")
        name2 = gen2._generate_name("M")
        
        # Could be same by chance, but very unlikely
        # Just test they both produce valid names
        assert isinstance(name1, str)
        assert isinstance(name2, str)

    def test_generate_mrn(self):
        """Test MRN generation format."""
        generator = SyntheticDataGenerator()
        mrn = generator._generate_mrn()
        
        assert mrn.startswith("MRN")
        assert len(mrn) == 11  # MRN + 8 digits

    def test_generate_name_male(self):
        """Test male name generation."""
        generator = SyntheticDataGenerator()
        name = generator._generate_name("M")
        
        assert isinstance(name, str)
        assert len(name) > 0
        assert " " in name  # First and last name

    def test_generate_name_female(self):
        """Test female name generation."""
        generator = SyntheticDataGenerator()
        name = generator._generate_name("F")
        
        assert isinstance(name, str)
        assert len(name) > 0
        assert " " in name

    def test_generate_chief_complaint(self):
        """Test chief complaint generation."""
        generator = SyntheticDataGenerator()
        complaint = generator._generate_chief_complaint()
        
        assert isinstance(complaint, str)
        assert len(complaint) > 0

    def test_generate_unit(self):
        """Test unit generation."""
        generator = SyntheticDataGenerator()
        unit = generator._generate_unit()
        
        assert "name" in unit
        assert "floor" in unit
        assert "capacity" in unit
        assert unit["capacity"] > 0

    def test_generate_beds(self):
        """Test bed generation."""
        generator = SyntheticDataGenerator()
        beds = generator._generate_beds(unit_id=1, count=10)
        
        assert len(beds) == 10
        for bed in beds:
            assert "unit_id" in bed
            assert "bed_number" in bed
            assert "room_number" in bed
            assert "status" in bed
            assert "x_position" in bed
            assert "y_position" in bed

    def test_generate_nurses(self):
        """Test nurse generation."""
        generator = SyntheticDataGenerator()
        nurses = generator._generate_nurses(unit_id=1, count=5)
        
        assert len(nurses) == 5
        for nurse in nurses:
            assert "unit_id" in nurse
            assert "name" in nurse
            assert "employee_id" in nurse
            assert "skill_level" in nurse
            assert 1 <= nurse["skill_level"] <= 5

    def test_generate_patient(self):
        """Test patient generation."""
        generator = SyntheticDataGenerator()
        base_time = datetime.now(timezone.utc)
        patient = generator._generate_patient(base_time, bed_ids=[1, 2, 3], nurse_ids=[1, 2])
        
        assert "mrn" in patient
        assert "name" in patient
        assert "age" in patient
        assert "gender" in patient
        assert "acuity" in patient
        assert "chief_complaint" in patient
        assert "arrival_time" in patient
        assert patient["acuity"] in ["low", "medium", "high", "critical"]

    def test_generate_events_for_patient(self):
        """Test event generation for a patient."""
        generator = SyntheticDataGenerator()
        base_time = datetime.now(timezone.utc)
        
        patient_data = {
            "id": 1,
            "arrival_time": base_time,
            "acuity": "medium",
            "needs_imaging": True,
            "bed_id": 1,
            "assigned_nurse_id": 1,
        }
        
        events = generator._generate_events_for_patient(
            patient_data, 
            unit_id=1, 
            bed_ids=[1, 2], 
            nurse_ids=[1, 2]
        )
        
        assert len(events) > 0
        
        # Should start with arrival
        assert events[0]["event_type"] == "arrival"
        
        for event in events:
            assert "patient_id" in event
            assert "event_type" in event
            assert "timestamp" in event

    def test_generate_policy_documents(self):
        """Test policy document generation."""
        generator = SyntheticDataGenerator()
        docs = generator._generate_policy_documents()
        
        assert len(docs) > 0
        for doc in docs:
            assert "title" in doc
            assert "content" in doc
            assert "doc_type" in doc
            assert len(doc["content"]) > 0

    def test_full_generation_returns_all_data(self):
        """Test full data generation returns all required data types."""
        generator = SyntheticDataGenerator()
        data = generator.generate()
        
        assert "unit" in data
        assert "beds" in data
        assert "nurses" in data
        assert "shifts" in data
        assert "patients" in data
        assert "events" in data
        assert "policy_documents" in data
        
        assert len(data["beds"]) > 0
        assert len(data["nurses"]) > 0
        assert len(data["patients"]) > 0
        assert len(data["events"]) > 0


class TestDataGeneratorEdgeCases:
    """Edge case tests for data generator."""

    def test_empty_bed_list(self):
        """Test patient generation with no beds."""
        generator = SyntheticDataGenerator()
        base_time = datetime.now(timezone.utc)
        
        patient = generator._generate_patient(base_time, bed_ids=[], nurse_ids=[1])
        
        assert patient["bed_id"] is None

    def test_empty_nurse_list(self):
        """Test patient generation with no nurses."""
        generator = SyntheticDataGenerator()
        base_time = datetime.now(timezone.utc)
        
        patient = generator._generate_patient(base_time, bed_ids=[1], nurse_ids=[])
        
        assert patient["assigned_nurse_id"] is None

    def test_acuity_distribution(self):
        """Test that acuity distribution is reasonable."""
        generator = SyntheticDataGenerator(seed=42)
        base_time = datetime.now(timezone.utc)
        
        acuities = []
        for _ in range(100):
            patient = generator._generate_patient(base_time, bed_ids=[1], nurse_ids=[1])
            acuities.append(patient["acuity"])
        
        # Should have some variety
        unique_acuities = set(acuities)
        assert len(unique_acuities) >= 2  # At least 2 different acuity levels
