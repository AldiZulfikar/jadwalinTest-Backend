from typing import Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, HTTPException
from app.models.enums import BookingStatus, TestType, UserRole
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingApprovePayload,
    BookingRejectPayload,
    BookingStartPayload,
    BookingCompletePayload,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.booking_service import BookingService
from app.api.deps import get_booking_service, get_current_user, require_role

router = APIRouter(prefix="/bookings", tags=["Bookings"])

qa_only = require_role([UserRole.QA])


@router.post(
    "",
    response_model=APIResponse[BookingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Performance Test Booking",
    description="Schedules a new performance test booking and associates it with the authenticated user."
)
async def create_booking(
    payload: BookingCreate,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user)
):
    booking = await service.create_booking(payload, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Booking created successfully.",
        data=BookingResponse.model_validate(booking)
    )


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[BookingResponse]],
    status_code=status.HTTP_200_OK,
    summary="List & Filter Bookings (Paginated & RBAC Scoped)",
    description="Retrieves paginated bookings. QA users view all bookings; Requesters view all bookings by default for calendar scheduling, or filter to my_bookings_only."
)
async def list_bookings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    sort: str = Query("created_at"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    booking_date: Optional[date] = Query(None),
    environment_id: Optional[UUID] = Query(None),
    status: Optional[BookingStatus] = Query(None),
    project_name: Optional[str] = Query(None),
    pic_name: Optional[str] = Query(None),
    test_type: Optional[TestType] = Query(None),
    my_bookings_only: Optional[bool] = Query(False),
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user)
):
    filter_user_id = None
    filter_user_email = None
    if my_bookings_only:
        filter_user_id = current_user.id
        filter_user_email = current_user.email

    items, total = await service.get_bookings_paginated(
        page=page,
        size=size,
        sort=sort,
        order=order,
        booking_date=booking_date,
        environment_id=environment_id,
        status=status,
        project_name=project_name,
        pic_name=pic_name,
        test_type=test_type,
        user_id=filter_user_id,
        user_email=filter_user_email
    )

    total_pages = (total + size - 1) // size if total > 0 else 0
    response_items = [BookingResponse.model_validate(b) for b in items]

    paginated_data = PaginatedResponse[BookingResponse](
        page=page,
        size=size,
        total=total,
        total_pages=total_pages,
        items=response_items
    )

    return APIResponse(
        success=True,
        message="Bookings retrieved successfully.",
        data=paginated_data
    )


@router.get(
    "/{id}",
    response_model=APIResponse[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Booking Details by ID",
    description="Retrieve detailed information for a specific booking by its UUID."
)
async def get_booking_by_id(
    id: UUID,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user)
):
    booking = await service.get_booking_by_id(id)

    # Ownership check for Requester
    if current_user.role == UserRole.REQUESTER:
        is_owner = (booking.user_id == current_user.id) or (booking.pic_email.lower() == current_user.email.lower())
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden. Requesters are only allowed to view their own bookings."
            )

    return APIResponse(
        success=True,
        message="Booking details retrieved successfully.",
        data=BookingResponse.model_validate(booking)
    )


# ------------------------------------------------------------------------------
# Sprint 3 Lifecycle Action Endpoints (QA Role Required)
# ------------------------------------------------------------------------------

@router.post(
    "/{id}/approve",
    response_model=APIResponse[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve Booking Request (QA Only)",
    description="Transitions booking status from Pending to Approved. Requires QA role."
)
async def approve_booking(
    id: UUID,
    payload: Optional[BookingApprovePayload] = None,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(qa_only)
):
    approved_by = payload.approved_by if payload and payload.approved_by else current_user.full_name
    booking = await service.approve_booking(id, approved_by=approved_by)
    return APIResponse(
        success=True,
        message=f"Booking {booking.booking_number} approved successfully.",
        data=BookingResponse.model_validate(booking)
    )


@router.post(
    "/{id}/reject",
    response_model=APIResponse[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject Booking Request (QA Only)",
    description="Transitions booking status from Pending to Rejected. Requires QA role."
)
async def reject_booking(
    id: UUID,
    payload: BookingRejectPayload,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(qa_only)
):
    rejected_by = payload.rejected_by if payload.rejected_by else current_user.full_name
    booking = await service.reject_booking(id, rejection_reason=payload.rejection_reason, rejected_by=rejected_by)
    return APIResponse(
        success=True,
        message=f"Booking {booking.booking_number} rejected.",
        data=BookingResponse.model_validate(booking)
    )


@router.post(
    "/{id}/start",
    response_model=APIResponse[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="Start Performance Testing (QA Only)",
    description="Transitions booking status from Approved to InProgress. Requires QA role."
)
async def start_testing(
    id: UUID,
    payload: Optional[BookingStartPayload] = None,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(qa_only)
):
    started_by = payload.started_by if payload and payload.started_by else current_user.full_name
    booking = await service.start_testing(id, started_by=started_by)
    return APIResponse(
        success=True,
        message=f"Testing started for booking {booking.booking_number}.",
        data=BookingResponse.model_validate(booking)
    )


@router.post(
    "/{id}/complete",
    response_model=APIResponse[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="Complete Performance Testing (QA Only)",
    description="Transitions booking status from InProgress to Completed. Requires QA role."
)
async def complete_testing(
    id: UUID,
    payload: Optional[BookingCompletePayload] = None,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(qa_only)
):
    completed_by = payload.completed_by if payload and payload.completed_by else current_user.full_name
    booking = await service.complete_testing(id, completed_by=completed_by)
    return APIResponse(
        success=True,
        message=f"Testing completed for booking {booking.booking_number}.",
        data=BookingResponse.model_validate(booking)
    )


@router.delete(
    "/{id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Cancel / Soft-Delete Booking",
    description="Transitions booking status to Cancelled. Requesters can only cancel their own bookings."
)
async def delete_booking(
    id: UUID,
    deleted_by: Optional[str] = Query(None),
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user)
):
    booking = await service.get_booking_by_id(id)

    # Ownership check for Requester
    if current_user.role == UserRole.REQUESTER:
        is_owner = (booking.user_id == current_user.id) or (booking.pic_email.lower() == current_user.email.lower())
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden. Requesters can only cancel their own bookings."
            )

    deleter = deleted_by or current_user.full_name
    await service.delete_booking(id, deleted_by=deleter)
    return APIResponse(
        success=True,
        message=f"Booking with ID {id} cancelled successfully.",
        data={"id": str(id)}
    )
