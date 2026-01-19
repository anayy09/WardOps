"""
LLM Tool Definitions for WardOps Copilot

Defines JSON schemas for all tools that the LLM can call.
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "query_state",
            "description": "Get the current operational state of a hospital unit at a specific time, including occupancy, queue lengths, and staffing summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_iso": {
                        "type": "string",
                        "description": "ISO 8601 timestamp for the state query (e.g., '2026-01-15T14:30:00')"
                    },
                    "unit_id": {
                        "type": "integer",
                        "description": "The ID of the hospital unit to query"
                    }
                },
                "required": ["time_iso", "unit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_trace",
            "description": "Get the complete journey of a patient including all events, timestamps, and calculated metrics like wait times and handoffs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "integer",
                        "description": "The ID of the patient"
                    }
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_bottlenecks",
            "description": "Analyze and summarize the top operational bottlenecks for a given time range and scenario, with supporting statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "Start of the analysis period (ISO 8601)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End of the analysis period (ISO 8601)"
                    },
                    "scenario_id": {
                        "type": "integer",
                        "description": "Optional scenario ID to analyze (uses baseline if not specified)"
                    }
                },
                "required": ["start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_simulation",
            "description": "Start a new simulation run with specified scenario parameters. Returns a job ID to track progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {
                        "type": "integer",
                        "description": "The scenario ID to simulate"
                    },
                    "baseline_id": {
                        "type": "integer",
                        "description": "Optional baseline scenario ID for comparison"
                    }
                },
                "required": ["scenario_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_simulation_status",
            "description": "Check the status and progress of a running simulation job.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "The simulation job ID"
                    }
                },
                "required": ["job_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_simulation_results",
            "description": "Get the complete results of a finished simulation including metrics, timeseries data, and bottleneck analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {
                        "type": "integer",
                        "description": "The scenario ID to get results for"
                    }
                },
                "required": ["scenario_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parse_incident_note",
            "description": "Parse a free-text incident note and extract structured event information including type, timestamp, and entities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_text": {
                        "type": "string",
                        "description": "The incident note text to parse"
                    }
                },
                "required": ["note_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_scenario_from_text",
            "description": "Convert a natural language scenario description into normalized simulation parameters with reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Natural language description of the scenario (e.g., 'Flu surge for 6 hours with 50% more arrivals')"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_policy_snippets",
            "description": "Search hospital policy documents and retrieve relevant snippets with source citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for policy documents"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of snippets to retrieve (default: 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# System prompt for the copilot
COPILOT_SYSTEM_PROMPT = """You are the WardOps Operations Copilot, an AI assistant for hospital operations management.

Your role is to help operations staff:
- Understand current unit state and patient flow
- Identify bottlenecks and operational issues
- Create and compare simulation scenarios
- Reference hospital policies when relevant

IMPORTANT RULES:
1. ALWAYS call query_state before making claims about current operational status
2. ALWAYS cite policy documents when referencing rules or guidelines
3. NEVER provide medical advice, diagnosis, or treatment recommendations
4. If asked medical questions, redirect to "This is an operations tool. For clinical questions, please consult the appropriate clinical staff."
5. When suggesting actions, output them as structured action objects that the UI can render as buttons

RESPONSE FORMAT:
- Be concise and data-driven
- Use specific numbers from tool calls
- Include citations like [Policy: Isolation Protocol] when referencing policies
- For actionable suggestions, include an "actions" array with button definitions

Example action format:
{
  "actions": [
    {"type": "run_simulation", "label": "Run Scenario", "params": {"scenario_id": 2}},
    {"type": "open_view", "label": "View Patient", "params": {"view": "patient", "id": 123}}
  ]
}
"""

# Medical advice refusal patterns
MEDICAL_REFUSAL_PATTERNS = [
    "diagnos",
    "treatment",
    "prescri",
    "medication",
    "drug",
    "symptom",
    "medical advice",
    "clinical decision",
    "should I give",
    "what medicine"
]

MEDICAL_REFUSAL_RESPONSE = """I'm the WardOps Operations Copilot, focused on hospital operations and patient flow management.

For clinical questions about diagnosis, treatment, or medications, please consult the appropriate clinical staff or reference your clinical decision support systems.

I can help you with:
- Patient flow and bed management
- Staffing and capacity planning
- Operational bottleneck analysis
- Scenario simulation and comparison
- Policy references for operational procedures

How can I assist with your operational needs?"""
