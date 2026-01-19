from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.llm import copilot

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    include_tools: bool = True


class ChatResponse(BaseModel):
    content: str
    tool_calls: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    citations: List[Dict[str, str]] = []


@router.get("/status")
async def get_copilot_status():
    """Check if copilot is available"""
    return {
        "available": copilot.is_available(),
        "model": copilot.model if copilot.is_available() else None
    }


@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(request: ChatRequest):
    """
    Chat with the ops copilot.
    
    The copilot can call tools to query state, run simulations, and retrieve policies.
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    try:
        result = copilot.chat(messages, include_tools=request.include_tools)
        return ChatResponse(**result)
    except Exception as e:
        error_detail = str(e)
        if "403" in error_detail or "not enabled" in error_detail:
            # LLM API key issue
            return ChatResponse(
                content=f"Copilot API error: {error_detail}. Please verify LLM_API_KEY is valid in backend/.env.local",
                tool_calls=[],
                actions=[],
                citations=[]
            )
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/tools")
async def get_available_tools():
    """Get list of available tools the copilot can use"""
    from app.llm.tools import TOOL_DEFINITIONS
    
    return {
        "tools": [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"]
            }
            for t in TOOL_DEFINITIONS
        ]
    }
