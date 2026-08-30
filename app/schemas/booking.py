import uuid
from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator

from app.models.enums import BookingStatus, TestType
from app.schemas.environment import EnvironmentResponse


class BookingBase(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=100, examples=["Core Banking Transformation"])
    application_name: str = Field(..., min_length=1, max_length=100, examples=["Payment Gateway Microservice"])
    pic_name: str = Field(..., min_length=1, max_length=100, examples=["John Doe"])
    pic_email: EmailStr = Field(..., examples=["john.doe@example.com"])
    booking_date: date = Field(..., examples=["2026-08-15"])
    start_time: time = Field(..., examples=["09:00:00"])
    end_time: time = Field(..., examples=["12:00:00"])
    environment_id: uuid.UUID = Field(..., examples=["11111111-1111-1111-1111-111111111111"])
    test_type: TestType = Field(..., examples=[TestType.LOAD_TEST])
    description: Optional[str] = Field(None, max_length=1000, examples=["Stress testing end-of-month batch processes"])

    @model_validator(mode="after")
    def validate_time_range(self) -> "BookingBase":
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be earlier than end time.")
        return self


class BookingCreate(BookingBase):
    created_by: Optional[str] = Field(None, max_length=255, examples=["john.doe@example.com"])

    @field_validator("booking_date")
    @classmethod
    def validate_booking_date_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Booking date cannot be in the past.")
        return v


class BookingUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=1, max_length=100)
    application_name: Optional[str] = Field(None, min_length=1, max_length=100)
    pic_name: Optional[str] = Field(None, min_length=1, max_length=100)
    pic_email: Optional[EmailStr] = None
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    environment_id: Optional[uuid.UUID] = None
    test_type: Optional[TestType] = None
    description: Optional[str] = None
    status: Optional[BookingStatus] = None
    updated_by: Optional[str] = Field(None, max_length=255)


# Sprint 3 Lifecycle Action Payloads
class BookingApprovePayload(BaseModel):
    approved_by: Optional[str] = Field(None, max_length=255, examples=["qa.lead@example.com"])


class BookingRejectPayload(BaseModel):
    rejection_reason: str = Field(..., min_length=1, max_length=1000, examples=["Environment under maintenance for load test."])
    rejected_by: Optional[str] = Field(None, max_length=255, examples=["qa.lead@example.com"])


class BookingStartPayload(BaseModel):
    started_by: Optional[str] = Field(None, max_length=255, examples=["tester@example.com"])


class BookingCompletePayload(BaseModel):
    completed_by: Optional[str] = Field(None, max_length=255, examples=["tester@example.com"])


class BookingResponse(BookingBase):
    id: uuid.UUID = Field(..., examples=["a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"])
    booking_number: str = Field(..., examples=["BK-20260815-0001"], description="Public human-friendly booking identifier")
    duration_minutes: int = Field(..., examples=[180], description="Calculated booking duration in minutes")
    status: BookingStatus = Field(..., examples=[BookingStatus.PENDING])
    user_id: Optional[uuid.UUID] = Field(None)

    # Audit fields
    created_by: Optional[str] = Field(None, examples=["john.doe@example.com"])
    updated_by: Optional[str] = Field(None)
    deleted_by: Optional[str] = Field(None)
    deleted_at: Optional[datetime] = Field(None)

    approved_at: Optional[datetime] = Field(None)
    approved_by: Optional[str] = Field(None)
    rejected_at: Optional[datetime] = Field(None)
    rejected_by: Optional[str] = Field(None)
    rejection_reason: Optional[str] = Field(None)
    started_at: Optional[datetime] = Field(None)
    started_by: Optional[str] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    completed_by: Optional[str] = Field(None)

    created_at: datetime = Field(..., examples=["2026-07-28T20:30:00Z"])
    updated_at: datetime = Field(..., examples=["2026-07-28T20:30:00Z"])
    environment: Optional[EnvironmentResponse] = Field(None, alias="environment_rel")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
