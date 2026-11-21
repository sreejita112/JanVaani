from typing import TypedDict, Optional, List, Dict

class AgentState(TypedDict):
    # Input fields
    ticket_id: str
    citizen_text: str
    citizen_name: Optional[str]
    citizen_email: Optional[str]
    citizen_phone: Optional[str]
    
    # Agent outputs
    intent: Optional[str]          # Complaint, Suggestion, Appreciation
    sentiment: Optional[str]       # Positive, Neutral, Negative
    sector: Optional[str]
    subcategory: Optional[str]
    priority: Optional[str]        # P0, P1, P2, P3, P4
    risk_level: Optional[str]      # high / low
    confidence: float
    
    # Deduplication
    duplicate_of: Optional[str]    # ticket_id of original
    embedding: Optional[List[float]]
    
    # HITL
    needs_review: bool
    human_corrections: Dict[str, str]
    
    # Email
    email_sent: bool
    
    # System
    retry_count: int
    errors: List[str]