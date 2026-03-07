"""Import record schemas."""
from datetime import datetime
from pydantic import BaseModel


class ImportRecordResponse(BaseModel):
    id: int
    file_name: str | None
    source_type: str
    record_count: int
    status: str
    notes: str | None
    imported_at: datetime

    class Config:
        from_attributes = True


class ImportListResponse(BaseModel):
    id: int
    file_name: str | None
    source_type: str
    record_count: int
    status: str
    imported_at: datetime

    class Config:
        from_attributes = True
