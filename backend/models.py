from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    """Users table - stores customer information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    phone = Column(String(15), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")


class Vehicle(Base):
    """Vehicles table - stores vehicle information for each user"""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    make = Column(String(50))  # e.g., "Tata", "Maruti"
    model = Column(String(50))  # e.g., "Nexon", "Swift"
    year = Column(Integer)  # e.g., 2023
    registration = Column(String(15), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="vehicles")
    bookings = relationship("Booking", back_populates="vehicle", cascade="all, delete-orphan")


class Booking(Base):
    """Bookings table - stores service booking records"""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), index=True)
    service_center_id = Column(Integer, default=1)
    date = Column(String(10))  # YYYY-MM-DD format
    time = Column(String(5))   # HH:MM format
    service_type = Column(String(100), default="General Service")
    status = Column(String(20), default="Pending")  # Pending, Confirmed, Completed, Cancelled
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    vehicle = relationship("Vehicle", back_populates="bookings")


class ServiceCenter(Base):
    """Service Centers table - stores service center information"""
    __tablename__ = "service_centers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    address = Column(String(200))
    phone = Column(String(15))
    city = Column(String(50))
    available_slots = Column(JSON, default=lambda: {
        "09:00": 5, "10:00": 5, "11:00": 5, "12:00": 5,
        "14:00": 5, "15:00": 5, "16:00": 5, "17:00": 5
    })
    created_at = Column(DateTime, default=datetime.utcnow)
