"""
Scheduler Logic for AutoPilot AI
Handles slot allocation, conflict detection, and optimization
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models
import random

# Available service slots throughout the day
AVAILABLE_SLOTS = [
    "09:00", "10:00", "11:00", "12:00",
    "14:00", "15:00", "16:00", "17:00"
]

# Slot capacity per time slot
SLOTS_PER_TIMEFRAME = 5


def check_slot_availability(db: Session, date: str, time: str, service_center_id: int) -> bool:
    """
    Check if a specific slot is available
    
    Args:
        db: Database session
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format
        service_center_id: Service center ID
    
    Returns:
        bool: True if slot available, False if booked
    """
    # Count existing bookings for this slot
    existing_bookings = db.query(models.Booking).filter(
        models.Booking.date == date,
        models.Booking.time == time,
        models.Booking.service_center_id == service_center_id,
        models.Booking.status != "Cancelled"
    ).count()
    
    # If less than max capacity, slot is available
    return existing_bookings < SLOTS_PER_TIMEFRAME


def get_slot_occupancy(db: Session, date: str, service_center_id: int) -> dict:
    """
    Get occupancy for all slots on a given date
    
    Args:
        db: Database session
        date: Date in YYYY-MM-DD format
        service_center_id: Service center ID
    
    Returns:
        dict: {time: occupancy_count}
    """
    occupancy = {}
    
    for slot in AVAILABLE_SLOTS:
        count = db.query(models.Booking).filter(
            models.Booking.date == date,
            models.Booking.time == slot,
            models.Booking.service_center_id == service_center_id,
            models.Booking.status != "Cancelled"
        ).count()
        occupancy[slot] = count
    
    return occupancy


def find_preferred_slot(db: Session, preferred_date: str, preferred_time: str, 
                       service_center_id: int) -> tuple:
    """
    Try to book the preferred slot, if not available, find next best option
    
    Args:
        db: Database session
        preferred_date: Customer's preferred date (YYYY-MM-DD)
        preferred_time: Customer's preferred time (HH:MM)
        service_center_id: Service center ID
    
    Returns:
        tuple: (assigned_date, assigned_time) - Best available slot
    """
    
    # Step 1: Try to book preferred slot
    if preferred_time in AVAILABLE_SLOTS:
        if check_slot_availability(db, preferred_date, preferred_time, service_center_id):
            return preferred_date, preferred_time
    
    # Step 2: Try same day, different time slots
    occupancy = get_slot_occupancy(db, preferred_date, service_center_id)
    
    # Sort slots by availability (least occupied first)
    available_slots_today = sorted(AVAILABLE_SLOTS, key=lambda x: occupancy.get(x, 0))
    
    for slot in available_slots_today:
        if check_slot_availability(db, preferred_date, slot, service_center_id):
            return preferred_date, slot
    
    # Step 3: Try next day
    next_date = (datetime.strptime(preferred_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for slot in AVAILABLE_SLOTS:
        if check_slot_availability(db, next_date, slot, service_center_id):
            return next_date, slot
    
    # Step 4: Try within next 7 days
    for i in range(2, 7):
        search_date = (datetime.strptime(preferred_date, "%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
        
        for slot in AVAILABLE_SLOTS:
            if check_slot_availability(db, search_date, slot, service_center_id):
                return search_date, slot
    
    # Fallback: Return next available (this should rarely happen)
    return next_date, AVAILABLE_SLOTS[0]


def find_best_service_center(db: Session, user_city: str = None) -> int:
    """
    Find the best service center based on location or default
    
    Args:
        db: Database session
        user_city: User's city (optional)
    
    Returns:
        int: Service center ID
    """
    # For MVP, just return first available service center
    # In production, this would use geolocation and ratings
    center = db.query(models.ServiceCenter).first()
    return center.id if center else 1


def get_booking_details(booked_date: str, booked_time: str, service_center_id: int, db: Session) -> dict:
    """
    Get detailed booking information for confirmation
    
    Args:
        booked_date: Booked date
        booked_time: Booked time
        service_center_id: Service center ID
        db: Database session
    
    Returns:
        dict: Booking details with center info
    """
    center = db.query(models.ServiceCenter).filter(
        models.ServiceCenter.id == service_center_id
    ).first()
    
    return {
        "date": booked_date,
        "time": booked_time,
        "service_center": center.name if center else "EY Auto Service Center",
        "address": center.address if center else "Contact for location",
        "phone": center.phone if center else "+91-XXXX-XXXX",
        "city": center.city if center else "India"
    }


def optimize_slots_for_day(db: Session, date: str, service_center_id: int) -> dict:
    """
    Get optimization statistics for a given day
    
    Args:
        db: Database session
        date: Date in YYYY-MM-DD format
        service_center_id: Service center ID
    
    Returns:
        dict: Optimization metrics
    """
    occupancy = get_slot_occupancy(db, date, service_center_id)
    
    total_capacity = len(AVAILABLE_SLOTS) * SLOTS_PER_TIMEFRAME
    total_booked = sum(occupancy.values())
    total_available = total_capacity - total_booked
    occupancy_percentage = (total_booked / total_capacity) * 100 if total_capacity > 0 else 0
    
    # Find peak and off-peak hours
    peak_slot = max(occupancy, key=occupancy.get) if occupancy else "N/A"
    off_peak_slot = min(occupancy, key=occupancy.get) if occupancy else "N/A"
    
    return {
        "date": date,
        "total_capacity": total_capacity,
        "total_booked": total_booked,
        "total_available": total_available,
        "occupancy_percentage": round(occupancy_percentage, 2),
        "peak_slot": peak_slot,
        "off_peak_slot": off_peak_slot,
        "occupancy_by_slot": occupancy
    }


def predict_wait_time(occupancy: dict, selected_slot: str) -> str:
    """
    Predict customer wait time based on slot occupancy
    
    Args:
        occupancy: Occupancy dict for the day
        selected_slot: Selected time slot
    
    Returns:
        str: Estimated wait time message
    """
    booked_count = occupancy.get(selected_slot, 0)
    
    # Rough calculation: ~30 min per service slot
    estimated_minutes = booked_count * 30
    
    if estimated_minutes == 0:
        return "No wait - You'll be first!"
    elif estimated_minutes <= 30:
        return f"~{estimated_minutes} min wait"
    elif estimated_minutes <= 60:
        return f"~{estimated_minutes} min wait (about 1 hour)"
    else:
        hours = estimated_minutes // 60
        minutes = estimated_minutes % 60
        return f"~{hours}h {minutes}m wait"
