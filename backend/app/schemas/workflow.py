from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WorkflowCreate(BaseModel):
    agent_id: str
    name: str = "Новый воркфлоу"


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    graph_json: Optional[dict] = None
    is_active: Optional[bool] = None


class WorkflowRunResponse(BaseModel):
    id: str
    workflow_id: str
    trigger_type: str
    status: str
    result_json: Optional[dict] = None
    error: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkflowResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    is_active: bool
    graph_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
