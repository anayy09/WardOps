from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import json

from app.core.database import AsyncSessionLocal
from app.models import Event, Bed, Patient, BedStatus, EventType
from app.schemas import ReplayDelta, KPIMetrics

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for replay"""
    
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/replay")
async def replay_websocket(
    websocket: WebSocket,
    unit_id: int = Query(default=1),
    start_time: Optional[str] = None,
    speed: float = Query(default=1.0, ge=0.1, le=10.0)
):
    """
    WebSocket endpoint for timeline replay.
    
    Streams events and state changes at the specified speed multiplier.
    """
    client_id = f"replay_{id(websocket)}"
    await manager.connect(websocket, client_id)
    
    try:
        # Parse start time or use beginning of simulation day
        if start_time:
            current_time = datetime.fromisoformat(start_time)
        else:
            current_time = datetime(2026, 1, 15, 0, 0, 0)
        
        end_time = current_time + timedelta(hours=24)
        tick_interval = 60  # 1 minute ticks
        
        is_playing = True
        
        while current_time < end_time:
            try:
                # Check for control messages (non-blocking)
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(), 
                        timeout=0.01
                    )
                    
                    if message.get("action") == "pause":
                        is_playing = False
                    elif message.get("action") == "play":
                        is_playing = True
                    elif message.get("action") == "seek":
                        current_time = datetime.fromisoformat(message.get("time"))
                    elif message.get("action") == "speed":
                        speed = float(message.get("value", 1.0))
                    elif message.get("action") == "stop":
                        break
                        
                except asyncio.TimeoutError:
                    pass
                
                if not is_playing:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get state for current time
                async with AsyncSessionLocal() as db:
                    delta = await get_replay_delta(db, unit_id, current_time)
                
                await manager.send_message({
                    "type": "tick",
                    "timestamp": current_time.isoformat(),
                    "delta": delta
                }, client_id)
                
                # Move time forward
                current_time += timedelta(seconds=tick_interval)
                
                # Sleep based on speed (1 minute simulation = 1/speed seconds real time)
                await asyncio.sleep(1.0 / speed)
                
            except Exception as e:
                await manager.send_message({
                    "type": "error",
                    "message": str(e)
                }, client_id)
                break
        
        # Send completion message
        await manager.send_message({
            "type": "complete",
            "message": "Replay finished"
        }, client_id)
        
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(client_id)


async def get_replay_delta(db, unit_id: int, timestamp: datetime) -> dict:
    """Get the state delta for a specific timestamp"""
    
    # Get bed states at this time
    beds_result = await db.execute(
        select(Bed).where(Bed.unit_id == unit_id)
    )
    beds = beds_result.scalars().all()
    
    # Get events in the last minute
    window_start = timestamp - timedelta(minutes=1)
    events_result = await db.execute(
        select(Event)
        .where(
            and_(
                Event.unit_id == unit_id,
                Event.timestamp >= window_start,
                Event.timestamp <= timestamp
            )
        )
        .order_by(Event.timestamp)
    )
    events = events_result.scalars().all()
    
    # Build bed changes based on events
    bed_changes = []
    event_markers = []
    
    for event in events:
        # Add to event markers
        event_markers.append({
            "id": event.id,
            "type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "patient_id": event.patient_id,
            "bed_id": event.bed_id,
            "data": event.data
        })
        
        # Track bed status changes
        if event.bed_id and event.event_type in [
            EventType.BED_ASSIGNMENT, 
            EventType.DISCHARGE,
            EventType.CLEANING_START,
            EventType.CLEANING_END
        ]:
            status = "occupied"
            patient_id = event.patient_id
            
            if event.event_type == EventType.DISCHARGE:
                status = "empty"
                patient_id = None
            elif event.event_type == EventType.CLEANING_START:
                status = "cleaning"
                patient_id = None
            elif event.event_type == EventType.CLEANING_END:
                status = "empty"
                patient_id = None
            
            bed_changes.append({
                "bed_id": event.bed_id,
                "status": status,
                "patient_id": patient_id
            })
    
    # Calculate metrics
    occupied_count = len([b for b in beds if b.status == BedStatus.OCCUPIED])
    total_beds = len(beds)
    
    metrics = {
        "occupancy_percent": round(occupied_count / total_beds * 100, 1) if total_beds > 0 else 0,
        "average_los_hours": 6.5,  # Simplified
        "average_time_to_bed_minutes": 35.0,
        "sla_breaches": 0,
        "imaging_queue_length": 0,
        "ed_waiting_count": 0,
        "nurse_load_average": occupied_count / 6.0 if occupied_count > 0 else 0
    }
    
    return {
        "bed_changes": bed_changes,
        "event_markers": event_markers,
        "metrics": metrics
    }
