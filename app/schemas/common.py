from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = Field(..., description="Indicates if the request was successful", examples=[True])
    message: str = Field(..., description="Human-readable response message", examples=["Operation completed successfully."])
    data: Optional[T] = Field(default=None, description="Response payload data")


class PaginatedResponse(BaseModel, Generic[T]):
    page: int = Field(..., description="Current page number (1-indexed)", examples=[1])
    size: int = Field(..., description="Page size (number of items per page)", examples=[20])
    total: int = Field(..., description="Total number of matching records", examples=[124])
    total_pages: int = Field(..., description="Total number of available pages", examples=[7])
    items: List[T] = Field(default_factory=list, description="List of paginated items")


class ErrorResponseData(BaseModel):
    details: Optional[Any] = Field(default=None, description="Detailed error information if available")
