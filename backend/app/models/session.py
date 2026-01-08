from pydantic import BaseModel
from typing import Optional

class SessionData(BaseModel):
    session_id: str
    user_id: str
    user_role: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str
    last_activity: str
    extra_data: dict = {}