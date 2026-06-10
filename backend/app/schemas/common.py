from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


class UUIDSchema(BaseModel):
    id: UUID

    model_config = {"from_attributes": True}


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
