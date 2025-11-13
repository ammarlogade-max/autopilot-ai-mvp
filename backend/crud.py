from sqlalchemy.orm import Session
from . import models
from pydantic import BaseModel
from datetime import datetime

# Pydantic schemas (for request/response validation)
class UserCreate(BaseModel):
    name: str
    phone: str
    email: str

class VehicleCreate(BaseModel):
    user_id: int
    make: str
    model: str
    year: int

class BookingCreate(BaseModel):
    user_name: str
    phone: str
    email: str
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int = 2023
    preferred_date: str  # YYYY-MM-DD
    preferred_time: str  # HH:MM
    service_type: str = "General Service"

class BookingResponse(BaseModel):
    id: int
    user_id: int
    vehicle_id: int
    date: str
    time: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# CRUD Operations
def create_or_get_user(db: Session, name: str, phone: str, email: str):
    """Create user if doesn't exist, otherwise return existing user"""
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if user:
        return user
    
    db_user = models.User(name=name, phone=phone, email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_or_get_vehicle(db: Session, user_id: int, make: str, model: str, year: int):
    """Create vehicle if doesn't exist, otherwise return existing vehicle"""
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.user_id == user_id,
        models.Vehicle.make == make,
        models.Vehicle.model == model
    ).first()
    
    if vehicle:
        return vehicle
    
    db_vehicle = models.Vehicle(user_id=user_id, make=make, model=model, year=year)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def create_booking(db: Session, booking: BookingCreate):
    """Create a new booking"""
    # Get or create user
    user = create_or_get_user(db, booking.user_name, booking.phone, booking.email)
    
    # Get or create vehicle
    vehicle = create_or_get_vehicle(
        db, user.id, booking.vehicle_make, booking.vehicle_model, booking.vehicle_year
    )
    
    # Create booking
    db_booking = models.Booking(
        user_id=user.id,
        vehicle_id=vehicle.id,
        date=booking.preferred_date,
        time=booking.preferred_time,
        service_type=booking.service_type,
        status="Confirmed",  # Automatically confirmed in MVP
        service_center_id=1
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def get_all_bookings(db: Session):
    """Get all bookings with user and vehicle details"""
    bookings = db.query(models.Booking).all()
    result = []
    for booking in bookings:
        result.append({
            "id": booking.id,
            "user_name": booking.user.name,
            "phone": booking.user.phone,
            "vehicle": f"{booking.vehicle.make} {booking.vehicle.model}",
            "date": booking.date,
            "time": booking.time,
            "status": booking.status,
            "service_type": booking.service_type,
            "service_center": "EY Service Center - Mumbai"
        })
    return result


def get_booking_by_id(db: Session, booking_id: int):
    """Get specific booking"""
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()


def cancel_booking(db: Session, booking_id: int):
    """Cancel a booking"""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if booking:
        booking.status = "Cancelled"
        db.commit()
        db.refresh(booking)
    return booking


def get_service_centers(db: Session):
    """Get all service centers"""
    return db.query(models.ServiceCenter).all()


def initialize_service_centers(db: Session):
    """Initialize default service centers"""
    # Check if service centers already exist
    if db.query(models.ServiceCenter).count() > 0:
        return
    
    centers = [
        models.ServiceCenter(
            name="EY Auto Service Center - Mumbai",
            address="Andheri East, Mumbai",
            phone="+91-22-1234-5678",
            city="Mumbai"
        ),
        models.ServiceCenter(
            name="EY Auto Service Center - Pune",
            address="Koregaon Park, Pune",
            phone="+91-20-1234-5678",
            city="Pune"
        ),
        models.ServiceCenter(
            name="EY Auto Service Center - Bangalore",
            address="Whitefield, Bangalore",
            phone="+91-80-1234-5678",
            city="Bangalore"
        )
    ]
    
    for center in centers:
        db.add(center)
    
    db.commit()
