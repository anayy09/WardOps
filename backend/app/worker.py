from celery import Celery
from datetime import datetime
import time

from app.core.config import settings

celery_app = Celery(
    "wardops",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.MAX_SIMULATION_TIME_SECONDS,
)


@celery_app.task(bind=True)
def run_simulation_task(self, run_id: int, scenario_id: int, baseline_id: int = None):
    """
    Celery task to run a simulation.
    
    Updates progress in the database and stores results when complete.
    """
    from sqlalchemy.orm import Session
    from app.core.database import sync_engine
    from app.models import SimulationRun, Scenario, SimulationStatus
    from app.simulation.engine import SimulationEngine
    
    print(f"\n[SIMULATION] Starting task: run_id={run_id}, scenario_id={scenario_id}")
    
    with Session(sync_engine) as db:
        # Get the run and scenario
        run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        print(f"[SIMULATION] Found run: {run is not None}, scenario: {scenario is not None}")
        if run:
            print(f"[SIMULATION] Run {run.id}: scenario_id={run.scenario_id}, status={run.status}")
        
        if not run or not scenario:
            return {"error": "Run or scenario not found"}
        
        # Update status to running
        run.status = SimulationStatus.RUNNING
        run.started_at = datetime.utcnow()
        db.commit()
        print(f"[SIMULATION] Updated run {run.id} to RUNNING status")
        
        try:
            # Create and run simulation
            engine = SimulationEngine(scenario.parameters)
            
            # Run with progress updates
            def progress_callback(progress: int):
                run.progress = progress
                db.commit()
                self.update_state(state="PROGRESS", meta={"progress": progress})
            
            results = engine.run(progress_callback=progress_callback)
            
            # Store results
            run.status = SimulationStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.progress = 100
            run.metrics = results["metrics"]
            run.timeseries = results["timeseries"]
            run.bottlenecks = results["bottlenecks"]
            db.commit()
            
            print(f"[SIMULATION] Task completed for run {run.id}, scenario {run.scenario_id}")
            print(f"[SIMULATION] Metrics saved: {list(results['metrics'].keys())}")
            
            return {
                "status": "completed",
                "run_id": run_id,
                "scenario_id": scenario_id,
                "metrics": results["metrics"]
            }
            
        except Exception as e:
            run.status = SimulationStatus.FAILED
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            
            return {"error": str(e)}


@celery_app.task
def generate_embeddings_task(doc_id: int):
    """
    Celery task to generate embeddings for a policy document.
    """
    # Import here to avoid circular imports
    from app.llm.embeddings import generate_doc_embeddings
    
    try:
        generate_doc_embeddings(doc_id)
        return {"status": "completed", "doc_id": doc_id}
    except Exception as e:
        return {"error": str(e), "doc_id": doc_id}
