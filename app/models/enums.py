from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"


class TestType(str, Enum):
    LOAD_TEST = "LoadTest"
    STRESS_TEST = "StressTest"


class UserRole(str, Enum):
    QA = "QA"
    REQUESTER = "Requester"
