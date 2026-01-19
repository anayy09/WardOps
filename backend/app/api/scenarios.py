from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models import Scenario, SimulationRun, SimulationStatus
from app.schemas import (
    Scenario as ScenarioSchema,
    ScenarioCreate,
    SimulationRun as SimulationRunSchema,
    SimulationRunCreate,
    SimulationResults,
    APIResponse,
)

router = APIRouter()


@router.get("", response_model=List[ScenarioSchema])
async def get_scenarios(
    db: AsyncSession = Depends(get_db),
    include_baseline: bool = True
):
    """Get all scenarios"""
    query = select(Scenario).order_by(Scenario.created_at.desc())
    
    if not include_baseline:
        query = query.where(Scenario.is_baseline == False)
    
    result = await db.execute(query)
    scenarios = result.scalars().all()
    return scenarios


@router.get("/{scenario_id}", response_model=ScenarioSchema)
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific scenario"""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("", response_model=ScenarioSchema)
async def create_scenario(
    scenario: ScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scenario"""
    db_scenario = Scenario(
        name=scenario.name,
        description=scenario.description,
        is_baseline=scenario.is_baseline,
        parameters=scenario.parameters.model_dump()
    )
    db.add(db_scenario)
    await db.commit()
    await db.refresh(db_scenario)
    return db_scenario


@router.put("/{scenario_id}", response_model=ScenarioSchema)
async def update_scenario(
    scenario_id: int,
    scenario: ScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update a scenario"""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    db_scenario = result.scalar_one_or_none()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    db_scenario.name = scenario.name
    db_scenario.description = scenario.description
    db_scenario.parameters = scenario.parameters.model_dump()
    
    await db.commit()
    await db.refresh(db_scenario)
    return db_scenario


@router.delete("/{scenario_id}", response_model=APIResponse)
async def delete_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a scenario"""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    if scenario.is_baseline:
        raise HTTPException(status_code=400, detail="Cannot delete baseline scenario")
    
    await db.delete(scenario)
    await db.commit()
    
    return APIResponse(success=True, message="Scenario deleted")


@router.get("/{scenario_id}/runs", response_model=List[SimulationRunSchema])
async def get_scenario_runs(
    scenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all simulation runs for a scenario"""
    result = await db.execute(
        select(SimulationRun)
        .where(SimulationRun.scenario_id == scenario_id)
        .order_by(SimulationRun.started_at.desc())
    )
    runs = result.scalars().all()
    return runs


@router.get("/{scenario_id}/results", response_model=SimulationResults)
async def get_scenario_results(
    scenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the latest completed simulation results for a scenario"""
    result = await db.execute(
        select(SimulationRun)
        .where(
            and_(
                SimulationRun.scenario_id == scenario_id,
                SimulationRun.status == SimulationStatus.COMPLETED
            )
        )
        .order_by(SimulationRun.completed_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="No completed simulation found")
    
    return SimulationResults(
        run_id=run.id,
        scenario_id=scenario_id,
        metrics=run.metrics or {},
        timeseries=run.timeseries or {},
        bottlenecks=run.bottlenecks or []
    )
