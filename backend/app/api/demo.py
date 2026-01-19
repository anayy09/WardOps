from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, delete
from typing import Dict, Any
import traceback
import sys

from app.core.database import get_db, Base, async_engine
from app.models import (
    Unit, Bed, Nurse, Shift, Patient, Event, 
    Scenario, SimulationRun, PolicyDoc, PolicyEmbedding, StateSnapshot
)
from app.services import (
    SyntheticDataGenerator, 
    GeneratorConfig, 
    generate_policy_docs,
    generate_baseline_scenario
)
from app.schemas import APIResponse

router = APIRouter()


@router.post("/load", response_model=APIResponse)
async def load_demo_data(
    db: AsyncSession = Depends(get_db),
    seed: int = 42
):
    """Load demo dataset with synthetic data"""
    try:
        # Clear existing data
        await db.execute(delete(PolicyEmbedding))
        await db.execute(delete(PolicyDoc))
        await db.execute(delete(StateSnapshot))
        await db.execute(delete(SimulationRun))
        await db.execute(delete(Scenario))
        await db.execute(delete(Event))
        await db.execute(delete(Shift))
        await db.execute(delete(Patient))
        await db.execute(delete(Nurse))
        await db.execute(delete(Bed))
        await db.execute(delete(Unit))
        await db.commit()
        
        # Generate synthetic data
        config = GeneratorConfig(seed=seed)
        generator = SyntheticDataGenerator(config)
        data = generator.generate_all()
        
        # Insert unit - use the Unit object directly
        unit = data["unit"]
        db.add(unit)
        await db.flush()
        
        # Insert beds - use the Bed objects directly since they're already SQLAlchemy models
        for bed in data["beds"]:
            db.add(bed)
        await db.flush()
        
        # Insert nurses
        for nurse in data["nurses"]:
            db.add(nurse)
        await db.flush()
        
        # Insert shifts
        for shift in data["shifts"]:
            db.add(shift)
        await db.flush()
        
        # Insert patients
        for patient in data["patients"]:
            db.add(patient)
        await db.flush()
        
        # Insert events
        for event in data["events"]:
            db.add(event)
        await db.flush()
        
        # Insert policy docs
        policy_docs = generate_policy_docs()
        for doc in policy_docs:
            db.add(PolicyDoc(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                doc_type=doc.doc_type,
                doc_metadata=doc.doc_metadata if hasattr(doc, 'doc_metadata') else {}
            ))
        await db.flush()
        
        # Insert baseline scenario
        baseline = generate_baseline_scenario()
        db.add(Scenario(
            id=baseline.id,
            name=baseline.name,
            description=baseline.description,
            is_baseline=baseline.is_baseline,
            parameters=baseline.parameters
        ))
        
        await db.commit()
        
        return APIResponse(
            success=True,
            message="Demo data loaded successfully",
            data={
                "patients": len(data["patients"]),
                "events": len(data["events"]),
                "beds": len(data["beds"]),
                "nurses": len(data["nurses"]),
                "policy_docs": len(policy_docs)
            }
        )
        
    except Exception as e:
        await db.rollback()
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"\n\n=== FULL ERROR TRACEBACK ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{''.join(traceback.format_tb(exc_traceback))}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@router.get("/status", response_model=APIResponse)
async def get_demo_status(db: AsyncSession = Depends(get_db)):
    """Check if demo data is loaded"""
    try:
        result = await db.execute(text("SELECT COUNT(*) FROM patients"))
        patient_count = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM events"))
        event_count = result.scalar()
        
        is_loaded = patient_count > 0
        
        return APIResponse(
            success=True,
            message="Demo status retrieved",
            data={
                "is_loaded": is_loaded,
                "patient_count": patient_count,
                "event_count": event_count
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error checking status: {str(e)}",
            data={"is_loaded": False}
        )


@router.delete("/clear", response_model=APIResponse)
async def clear_demo_data(db: AsyncSession = Depends(get_db)):
    """Clear all demo data"""
    try:
        await db.execute(delete(PolicyEmbedding))
        await db.execute(delete(PolicyDoc))
        await db.execute(delete(StateSnapshot))
        await db.execute(delete(SimulationRun))
        await db.execute(delete(Scenario))
        await db.execute(delete(Event))
        await db.execute(delete(Shift))
        await db.execute(delete(Patient))
        await db.execute(delete(Nurse))
        await db.execute(delete(Bed))
        await db.execute(delete(Unit))
        await db.commit()
        
        return APIResponse(
            success=True,
            message="Demo data cleared successfully"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
