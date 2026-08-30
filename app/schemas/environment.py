import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EnvironmentResponse(BaseModel):
    id: uuid.UUID = Field(..., examples=["11111111-1111-1111-1111-111111111111"])
    code: str = Field(..., examples=["PERF01"])
    name: str = Field(..., examples=["Performance Environment 01"])
    description: Optional[str] = Field(None, examples=["Primary high-throughput performance testing environment"])
    active: bool = Field(True, examples=[True])
    created_at: datetime = Field(..., examples=["2026-07-28T20:35:00Z"])
    updated_at: datetime = Field(..., examples=["2026-07-28T20:35:00Z"])

    model_config = {
        "from_attributes": True
    }
