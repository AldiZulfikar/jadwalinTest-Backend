from datetime import datetime, timezone, time, date, timedelta


def get_utc_now() -> datetime:
    """Returns current UTC-aware datetime."""
    return datetime.now(timezone.utc)


def calculate_duration_minutes(start_time: time, end_time: time) -> int:
    """
    Calculates duration in minutes between start_time and end_time.
    Assumes start_time and end_time occur on the same day.
    """
    dummy_date = date.today()
    dt_start = datetime.combine(dummy_date, start_time)
    dt_end = datetime.combine(dummy_date, end_time)
    
    if dt_end <= dt_start:
        raise ValueError("End time must be greater than start time.")
        
    duration = dt_end - dt_start
    return int(duration.total_seconds() // 60)
