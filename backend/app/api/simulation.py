from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
import asyncio
import json

from app.core.database import get_db, AsyncSessionLocal
from app.models import Scenario, SimulationRun, SimulationStatus, Event, Bed, Patient, BedStatus
from app.schemas import (
    SimulationRun as SimulationRunSchema,
    SimulationRunCreate,
    SimulationResults,
    APIResponse,
)
from app.worker import run_simulation_task

router = APIRouter()


@router.post("/run", response_model=SimulationRunSchema)
async def start_simulation(
    scenario_id: int,
    baseline_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Start a new simulation run"""
    # Verify scenario exists
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Create simulation run record
    sim_run = SimulationRun(
        scenario_id=scenario_id,
        status=SimulationStatus.PENDING,
        progress=0
    )
    db.add(sim_run)
    await db.commit()
    await db.refresh(sim_run)
    
    # Queue the simulation task
    run_simulation_task.delay(sim_run.id, scenario_id, baseline_id)
    
    return sim_run


@router.get("/{job_id}/status", response_model=SimulationRunSchema)
async def get_simulation_status(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get simulation job status"""
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == job_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run


@router.get("/{scenario_id}/results", response_model=SimulationResults)
async def get_simulation_results(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """Get simulation results for a scenario"""
    result = await db.execute(
        select(SimulationRun)
        .where(
            SimulationRun.scenario_id == scenario_id,
            SimulationRun.status == SimulationStatus.COMPLETED
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


@router.delete("/{job_id}", response_model=APIResponse)
async def cancel_simulation(job_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a running simulation"""
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == job_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    
    if run.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]:
        return APIResponse(success=False, message="Simulation already finished")
    
    run.status = SimulationStatus.FAILED
    run.error_message = "Cancelled by user"
    await db.commit()
    
    return APIResponse(success=True, message="Simulation cancelled")


# WebSocket for simulation progress
@router.websocket("/ws/{job_id}")
async def simulation_progress_ws(websocket: WebSocket, job_id: int):
    """WebSocket for real-time simulation progress"""
    await websocket.accept()
    
    try:
        while True:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SimulationRun).where(SimulationRun.id == job_id)
                )
                run = result.scalar_one_or_none()
                
                if not run:
                    await websocket.send_json({"error": "Run not found"})
                    break
                
                await websocket.send_json({
                    "job_id": run.id,
                    "status": run.status.value,
                    "progress": run.progress,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    "error_message": run.error_message
                })
                
                if run.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]:
                    break
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
