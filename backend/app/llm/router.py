"""
Tool Router for LLM Copilot

Executes tool calls from the LLM and returns results.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.database import sync_engine
from app.models import (
    Unit, Bed, Patient, Event, Nurse, Shift, 
    Scenario, SimulationRun, SimulationStatus,
    PolicyDoc, PolicyEmbedding, BedStatus, EventType
)
from app.worker import run_simulation_task


class ToolRouter:
    """Routes and executes LLM tool calls"""
    
    def __init__(self):
        self.tool_handlers = {
            "query_state": self._query_state,
            "get_patient_trace": self._get_patient_trace,
            "summarize_bottlenecks": self._summarize_bottlenecks,
            "run_simulation": self._run_simulation,
            "get_simulation_status": self._get_simulation_status,
            "get_simulation_results": self._get_simulation_results,
            "parse_incident_note": self._parse_incident_note,
            "propose_scenario_from_text": self._propose_scenario_from_text,
            "retrieve_policy_snippets": self._retrieve_policy_snippets,
        }
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return handler(**arguments)
        except Exception as e:
            return {"error": str(e)}
    
    def _query_state(self, time_iso: str, unit_id: int) -> Dict[str, Any]:
        """Query the operational state at a specific time"""
        timestamp = datetime.fromisoformat(time_iso)
        
        with Session(sync_engine) as db:
            # Get unit
            unit = db.query(Unit).filter(Unit.id == unit_id).first()
            if not unit:
                return {"error": "Unit not found"}
            
            # Get bed states
            beds = db.query(Bed).filter(Bed.unit_id == unit_id).all()
            total_beds = len(beds)
            occupied = sum(1 for b in beds if b.status == BedStatus.OCCUPIED)
            cleaning = sum(1 for b in beds if b.status == BedStatus.CLEANING)
            blocked = sum(1 for b in beds if b.status == BedStatus.BLOCKED)
            
            # Get active patients
            active_patients = db.query(Patient).filter(
                and_(
                    Patient.current_unit_id == unit_id,
                    Patient.discharge_time.is_(None)
                )
            ).count()
            
            # Get nurses on shift
            nurses = db.query(Nurse).filter(Nurse.unit_id == unit_id).all()
            
            # Calculate queue estimates from recent events
            waiting_for_bed = db.query(Patient).filter(
                and_(
                    Patient.current_bed_id.is_(None),
                    Patient.discharge_time.is_(None)
                )
            ).count()
            
            return {
                "timestamp": time_iso,
                "unit": {"id": unit.id, "name": unit.name, "code": unit.code},
                "occupancy": {
                    "total_beds": total_beds,
                    "occupied": occupied,
                    "cleaning": cleaning,
                    "blocked": blocked,
                    "available": total_beds - occupied - cleaning - blocked,
                    "occupancy_percent": round(occupied / total_beds * 100, 1) if total_beds > 0 else 0
                },
                "queues": {
                    "waiting_for_bed": waiting_for_bed,
                    "imaging_queue": 0,  # Simplified
                    "transport_queue": 0
                },
                "staffing": {
                    "nurses_on_duty": len(nurses),
                    "patients_per_nurse": round(active_patients / len(nurses), 1) if nurses else 0
                }
            }
    
    def _get_patient_trace(self, patient_id: int) -> Dict[str, Any]:
        """Get patient journey trace"""
        with Session(sync_engine) as db:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {"error": "Patient not found"}
            
            events = db.query(Event).filter(
                Event.patient_id == patient_id
            ).order_by(Event.timestamp).all()
            
            # Calculate metrics
            arrival_time = patient.arrival_time
            bed_time = None
            imaging_time = 0
            handoffs = 0
            
            for event in events:
                if event.event_type == EventType.BED_ASSIGNMENT:
                    bed_time = event.timestamp
                elif event.event_type == EventType.NURSE_ASSIGNMENT:
                    handoffs += 1
            
            wait_time = (bed_time - arrival_time).total_seconds() / 60 if bed_time else None
            
            total_time = None
            if patient.discharge_time:
                total_time = (patient.discharge_time - arrival_time).total_seconds() / 60
            
            return {
                "patient": {
                    "id": patient.id,
                    "mrn": patient.mrn,
                    "name": patient.name,
                    "acuity": patient.acuity.value,
                    "chief_complaint": patient.chief_complaint
                },
                "events": [
                    {
                        "type": e.event_type.value,
                        "timestamp": e.timestamp.isoformat(),
                        "data": e.data
                    }
                    for e in events
                ],
                "metrics": {
                    "total_time_minutes": round(total_time, 1) if total_time else None,
                    "wait_for_bed_minutes": round(wait_time, 1) if wait_time else None,
                    "handoffs": handoffs,
                    "had_imaging": patient.requires_imaging,
                    "had_consult": patient.requires_consult
                }
            }
    
    def _summarize_bottlenecks(
        self, 
        start_time: str, 
        end_time: str, 
        scenario_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Summarize bottlenecks for a time range"""
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        
        with Session(sync_engine) as db:
            # Get events in time range
            events = db.query(Event).filter(
                and_(
                    Event.timestamp >= start,
                    Event.timestamp <= end
                )
            ).all()
            
            # Analyze bed assignment delays
            bed_waits = []
            for event in events:
                if event.event_type == EventType.BED_ASSIGNMENT:
                    wait = event.data.get("wait_minutes")
                    if wait:
                        bed_waits.append(wait)
            
            # Count SLA breaches
            sla_breaches = len([w for w in bed_waits if w > 60])
            
            bottlenecks = []
            
            if bed_waits:
                avg_wait = sum(bed_waits) / len(bed_waits)
                if avg_wait > 30:
                    bottlenecks.append({
                        "constraint": "bed_availability",
                        "impact_score": min(avg_wait / 60, 1.0),
                        "affected_patients": len(bed_waits),
                        "description": f"Average bed wait time of {avg_wait:.1f} minutes exceeds target",
                        "supporting_stats": {
                            "avg_wait_minutes": round(avg_wait, 1),
                            "max_wait_minutes": max(bed_waits),
                            "sla_breaches": sla_breaches
                        }
                    })
            
            # Check staffing
            patients_per_nurse = 4.5  # Simplified estimate
            if patients_per_nurse > 4:
                bottlenecks.append({
                    "constraint": "nurse_staffing",
                    "impact_score": (patients_per_nurse - 4) / 2,
                    "affected_patients": 0,
                    "description": f"Nurse-to-patient ratio ({patients_per_nurse:.1f}:1) exceeds guideline (4:1)",
                    "supporting_stats": {
                        "current_ratio": patients_per_nurse,
                        "target_ratio": 4.0
                    }
                })
            
            return {
                "time_range": {"start": start_time, "end": end_time},
                "bottlenecks": sorted(bottlenecks, key=lambda x: x["impact_score"], reverse=True),
                "summary": f"Found {len(bottlenecks)} significant bottlenecks with {sla_breaches} SLA breaches"
            }
    
    def _run_simulation(
        self, 
        scenario_id: int, 
        baseline_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Start a simulation run"""
        with Session(sync_engine) as db:
            scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
            if not scenario:
                return {"error": "Scenario not found"}
            
            # Create simulation run
            run = SimulationRun(
                scenario_id=scenario_id,
                status=SimulationStatus.PENDING,
                progress=0
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            
            # Queue task
            run_simulation_task.delay(run.id, scenario_id, baseline_id)
            
            return {
                "job_id": run.id,
                "scenario_id": scenario_id,
                "status": "pending",
                "message": "Simulation queued successfully"
            }
    
    def _get_simulation_status(self, job_id: int) -> Dict[str, Any]:
        """Get simulation job status"""
        with Session(sync_engine) as db:
            run = db.query(SimulationRun).filter(SimulationRun.id == job_id).first()
            if not run:
                return {"error": "Simulation run not found"}
            
            return {
                "job_id": run.id,
                "status": run.status.value,
                "progress": run.progress,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error": run.error_message
            }
    
    def _get_simulation_results(self, scenario_id: int) -> Dict[str, Any]:
        """Get simulation results"""
        with Session(sync_engine) as db:
            run = db.query(SimulationRun).filter(
                and_(
                    SimulationRun.scenario_id == scenario_id,
                    SimulationRun.status == SimulationStatus.COMPLETED
                )
            ).order_by(SimulationRun.completed_at.desc()).first()
            
            if not run:
                return {"error": "No completed simulation found for this scenario"}
            
            return {
                "run_id": run.id,
                "scenario_id": scenario_id,
                "metrics": run.metrics,
                "bottlenecks": run.bottlenecks,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None
            }
    
    def _parse_incident_note(self, note_text: str) -> Dict[str, Any]:
        """Parse incident note into structured events"""
        # Simple rule-based parsing (would use LLM in production)
        events = []
        confidence = 0.7
        
        note_lower = note_text.lower()
        
        # Detect event types
        if "fall" in note_lower:
            events.append({
                "type": "incident",
                "subtype": "fall",
                "confidence": 0.9
            })
        
        if "delay" in note_lower:
            events.append({
                "type": "operational_delay",
                "confidence": 0.8
            })
        
        if "transfer" in note_lower:
            events.append({
                "type": "transfer",
                "confidence": 0.85
            })
        
        if "wait" in note_lower or "waiting" in note_lower:
            events.append({
                "type": "wait_time_issue",
                "confidence": 0.75
            })
        
        # Extract entities (simplified)
        entities = {
            "mentioned_locations": [],
            "mentioned_times": [],
            "mentioned_staff": []
        }
        
        if "ed" in note_lower or "emergency" in note_lower:
            entities["mentioned_locations"].append("ED")
        if "icu" in note_lower:
            entities["mentioned_locations"].append("ICU")
        
        return {
            "original_text": note_text,
            "parsed_events": events,
            "entities": entities,
            "overall_confidence": confidence,
            "requires_review": confidence < 0.8
        }
    
    def _propose_scenario_from_text(self, text: str) -> Dict[str, Any]:
        """Convert natural language to scenario parameters"""
        params = {
            "arrival_multiplier": 1.0,
            "acuity_mix": {"low": 0.3, "medium": 0.5, "high": 0.15, "critical": 0.05},
            "beds_available": 24,
            "nurse_count": {"day": 6, "evening": 5, "night": 4},
            "imaging_capacity": 1.0,
            "transport_capacity": 1.0
        }
        
        reasoning = []
        text_lower = text.lower()
        
        # Parse arrival changes
        if "surge" in text_lower or "increase" in text_lower:
            if "50%" in text or "1.5" in text:
                params["arrival_multiplier"] = 1.5
                reasoning.append("Set arrival multiplier to 1.5x based on '50% increase' or '1.5x'")
            elif "double" in text_lower or "2x" in text:
                params["arrival_multiplier"] = 2.0
                reasoning.append("Set arrival multiplier to 2.0x based on 'double' or '2x'")
            else:
                params["arrival_multiplier"] = 1.3
                reasoning.append("Set arrival multiplier to 1.3x based on generic surge mention")
        
        # Parse staffing changes
        if "add" in text_lower and "nurse" in text_lower:
            if "2" in text:
                params["nurse_count"]["day"] += 2
                reasoning.append("Added 2 nurses to day shift")
            elif "1" in text:
                params["nurse_count"]["day"] += 1
                reasoning.append("Added 1 nurse to day shift")
        
        if "reduce" in text_lower and "nurse" in text_lower:
            params["nurse_count"]["day"] = max(3, params["nurse_count"]["day"] - 1)
            reasoning.append("Reduced day shift nurses by 1")
        
        # Parse bed changes
        if "close" in text_lower and "bed" in text_lower:
            if any(str(n) in text for n in range(1, 10)):
                for n in range(1, 10):
                    if str(n) in text:
                        params["beds_available"] -= n
                        reasoning.append(f"Closed {n} beds")
                        break
        
        # Parse capacity changes
        if "imaging" in text_lower:
            if "reduce" in text_lower or "decrease" in text_lower:
                if "20%" in text:
                    params["imaging_capacity"] = 0.8
                    reasoning.append("Reduced imaging capacity by 20%")
                else:
                    params["imaging_capacity"] = 0.7
                    reasoning.append("Reduced imaging capacity by 30% (default reduction)")
        
        # Parse acuity changes
        if "high acuity" in text_lower or "sicker" in text_lower:
            params["acuity_mix"] = {"low": 0.2, "medium": 0.4, "high": 0.3, "critical": 0.1}
            reasoning.append("Shifted acuity mix toward higher acuity patients")
        
        return {
            "original_text": text,
            "parameters": params,
            "reasoning": reasoning,
            "suggested_name": f"Scenario from: {text[:50]}..."
        }
    
    def _retrieve_policy_snippets(self, query: str, k: int = 3) -> Dict[str, Any]:
        """Retrieve relevant policy document snippets"""
        with Session(sync_engine) as db:
            # Simple keyword search (would use vector search in production)
            docs = db.query(PolicyDoc).all()
            
            results = []
            query_terms = query.lower().split()
            
            for doc in docs:
                content_lower = doc.content.lower()
                relevance = sum(1 for term in query_terms if term in content_lower)
                
                if relevance > 0:
                    # Extract relevant snippet
                    lines = doc.content.split("\n")
                    snippet_lines = []
                    for line in lines:
                        if any(term in line.lower() for term in query_terms):
                            snippet_lines.append(line.strip())
                            if len(snippet_lines) >= 5:
                                break
                    
                    results.append({
                        "doc_id": doc.id,
                        "doc_title": doc.title,
                        "doc_type": doc.doc_type,
                        "snippet": "\n".join(snippet_lines) if snippet_lines else doc.content[:500],
                        "relevance_score": relevance / len(query_terms)
                    })
            
            # Sort by relevance and limit
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            results = results[:k]
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results)
            }
