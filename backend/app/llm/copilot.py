"""
LLM Copilot Chat Handler

Manages conversations with the LLM, including tool calls.
Includes a mock mode for demo when LLM API is unavailable.
"""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.llm.tools import (
    TOOL_DEFINITIONS, 
    COPILOT_SYSTEM_PROMPT,
    MEDICAL_REFUSAL_PATTERNS,
    MEDICAL_REFUSAL_RESPONSE
)
from app.llm.router import ToolRouter


class CopilotHandler:
    """Handles copilot chat interactions with LLM"""
    
    def __init__(self):
        self.client = None
        self.use_mock = False
        if settings.LLM_API_KEY:
            self.client = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_URL.replace("/chat/completions", "")
            )
        else:
            self.use_mock = True
        self.tool_router = ToolRouter()
        self.model = settings.LLM_MODEL
    
    def is_available(self) -> bool:
        """Check if LLM is configured (or can use mock)"""
        return True  # Always available - use mock if needed
    
    def _mock_response(self, user_message: str) -> Dict[str, Any]:
        """Generate a mock copilot response for demo mode"""
        message_lower = user_message.lower()
        
        # Mock responses based on keywords
        if "bottleneck" in message_lower or "delay" in message_lower:
            return {
                "content": "Based on current unit state, the primary bottleneck is **Imaging queue** with 3.8 avg wait patients. "
                           "This accounts for ~25% of bed delays. Secondary concern: Nurse staffing ratio at 92% utilization. "
                           "Recommendation: Add temporary imaging tech or defer non-urgent scans to next shift.",
                "tool_calls": [],
                "actions": [
                    {"type": "suggest_action", "action": "increase_imaging_staff", "label": "Add Imaging Tech"},
                    {"type": "suggest_action", "action": "run_simulation", "label": "Simulate Staffing Change"}
                ],
                "citations": []
            }
        elif "scenario" in message_lower or "what if" in message_lower:
            return {
                "content": "I can help you explore scenarios. Common ones: *Flu surge* (+50% arrivals), *Staffing shortage* (-2 nurses), "
                           "*Imaging downtime* (50% capacity). Try: \"Run a scenario with 50% more arrivals and 2 fewer nurses.\"",
                "tool_calls": [],
                "actions": [],
                "citations": []
            }
        elif "handoff" in message_lower or "transfer" in message_lower:
            return {
                "content": "Recent patient handoffs show avg 2.3 transfers per patient, with 8.5 min per handoff. "
                           "High-acuity patients average 3.1 transfers. Workflow bottleneck: ED → Floor bed assignment (avg wait 45 min). "
                           "This adds 18% to total LOS.",
                "tool_calls": [],
                "actions": [],
                "citations": []
            }
        else:
            return {
                "content": f"I'm the WardOps operations copilot (running in demo mode). I can help you: "
                           f"\n• **Analyze bottlenecks** - Ask about delays or queues"
                           f"\n• **Run scenarios** - What-if analysis on staffing, arrivals, or resources"
                           f"\n• **Trace handoffs** - Analyze patient flow and transfers"
                           f"\n\nWhat operational question can I help with?",
                "tool_calls": [],
                "actions": [],
                "citations": []
            }
    
    def _check_medical_refusal(self, message: str) -> Optional[str]:
        """Check if message requires medical refusal"""
        message_lower = message.lower()
        for pattern in MEDICAL_REFUSAL_PATTERNS:
            if pattern in message_lower:
                return MEDICAL_REFUSAL_RESPONSE
        return None
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        include_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process a chat message and return response.
        Uses mock mode if LLM API is unavailable.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            include_tools: Whether to enable tool calling
            
        Returns:
            Dict with 'content', 'tool_calls', 'actions', 'citations'
        """
        # Check for medical refusal
        if messages:
            last_message = messages[-1].get("content", "")
            refusal = self._check_medical_refusal(last_message)
            if refusal:
                return {
                    "content": refusal,
                    "tool_calls": [],
                    "actions": [],
                    "citations": []
                }
        
        # Use mock if LLM not available
        if self.use_mock or not self.client:
            if messages:
                return self._mock_response(messages[-1].get("content", ""))
            return {
                "content": "Welcome to WardOps Copilot (demo mode). How can I help with operations?",
                "tool_calls": [],
                "actions": [],
                "citations": []
            }
        
        # Prepare messages with system prompt
        full_messages = [{"role": "system", "content": COPILOT_SYSTEM_PROMPT}]
        full_messages.extend(messages)
        
        # Make initial API call
        kwargs = {
            "model": self.model,
            "messages": full_messages,
        }
        
        if include_tools:
            kwargs["tools"] = TOOL_DEFINITIONS
            kwargs["tool_choice"] = "auto"
        
        try:
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
        except Exception as api_error:
            error_str = str(api_error)
            if "403" in error_str or "401" in error_str or "not enabled" in error_str or "expired" in error_str or "invalid" in error_str.lower():
                # Fall back to mock on API key errors (401, 403, or session expired)
                if messages:
                    return self._mock_response(messages[-1].get("content", ""))
                return {
                    "content": "Copilot API key issue. Using demo mode.",
                    "tool_calls": [],
                    "actions": [],
                    "citations": []
                }
            raise
        
        # Handle tool calls
        tool_results = []
        tool_calls = []
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                
                # Execute tool
                result = self.tool_router.execute(tool_name, arguments)
                
                tool_calls.append({
                    "name": tool_name,
                    "arguments": arguments,
                    "result": result
                })
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": json.dumps(result)
                })
            
            # If we had tool calls, make another API call with results
            if tool_results:
                full_messages.append(message.model_dump())
                full_messages.extend(tool_results)
                
                # Get final response
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                )
                message = final_response.choices[0].message
        
        # Extract actions and citations from response
        content = message.content or ""
        actions = self._extract_actions(content)
        citations = self._extract_citations(content, tool_calls)
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "actions": actions,
            "citations": citations
        }
    
    def _extract_actions(self, content: str) -> List[Dict[str, Any]]:
        """Extract action objects from response"""
        actions = []
        
        # Look for JSON action blocks
        try:
            if '{"actions":' in content or '"actions":' in content:
                import re
                matches = re.findall(r'\{[^}]*"actions":\s*\[[^\]]*\][^}]*\}', content)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if "actions" in data:
                            actions.extend(data["actions"])
                    except:
                        pass
        except:
            pass
        
        return actions
    
    def _extract_citations(
        self, 
        content: str, 
        tool_calls: List[Dict]
    ) -> List[Dict[str, str]]:
        """Extract policy citations"""
        citations = []
        
        # Look for policy references in tool call results
        for tc in tool_calls:
            if tc["name"] == "retrieve_policy_snippets":
                result = tc.get("result", {})
                for doc in result.get("results", []):
                    citations.append({
                        "doc_title": doc.get("doc_title", ""),
                        "doc_type": doc.get("doc_type", ""),
                        "snippet": doc.get("snippet", "")[:200]
                    })
        
        return citations


# Singleton instance
copilot = CopilotHandler()
