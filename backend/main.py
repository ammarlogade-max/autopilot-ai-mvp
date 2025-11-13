import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models
from .database import engine, SessionLocal, Base, get_db
from .models import User, Vehicle, Booking, ServiceCenter
from .crud import (
    BookingCreate, BookingResponse, create_booking, get_all_bookings,
    get_booking_by_id, cancel_booking, initialize_service_centers,
    create_or_get_user, create_or_get_vehicle
)
from .nlp_parser import parse_booking_request

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AutoPilot AI - Backend API",
    description="Autonomous Vehicle Service Scheduler Backend",
    version="1.0.0"
)

# ==================== CORS CONFIGURATION (PRODUCTION-READY) ====================
# Get allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://localhost:3000"
).split(",")

# Add CORS middleware with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event - initialize service centers
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        initialize_service_centers(db)
    finally:
        db.close()

# ==================== HEALTH CHECK ====================

@app.get("/")
def read_root():
    """Root endpoint - Health check"""
    return {
        "message": "✅ AutoPilot AI Backend is Running!",
        "version": "1.0.0",
        "status": "operational",
        "environment": "production" if os.getenv("ENVIRONMENT") == "production" else "development"
    }

# ==================== BOOKING ENDPOINTS ====================

@app.post("/bookings", response_model=dict)
def create_new_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """
    Create a new service booking
    
    Request body:
    - user_name: str
    - phone: str (unique)
    - email: str (unique)
    - vehicle_make: str (e.g., "Tata")
    - vehicle_model: str (e.g., "Nexon")
    - vehicle_year: int (default: 2023)
    - preferred_date: str (YYYY-MM-DD format)
    - preferred_time: str (HH:MM format)
    - service_type: str (default: "General Service")
    """
    try:
        new_booking = create_booking(db, booking)
        return {
            "status": "success",
            "message": "✅ Booking confirmed successfully!",
            "booking_id": new_booking.id,
            "date": new_booking.date,
            "time": new_booking.time,
            "confirmation_number": f"AP-{new_booking.id:05d}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/bookings")
def get_bookings(db: Session = Depends(get_db)):
    """
    Get all bookings
    
    Returns: List of all bookings with user and vehicle details
    """
    try:
        bookings = get_all_bookings(db)
        return {
            "status": "success",
            "total": len(bookings),
            "bookings": bookings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """
    Get specific booking by ID
    
    Path parameter:
    - booking_id: int
    """
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {
        "status": "success",
        "booking": {
            "id": booking.id,
            "user_name": booking.user.name,
            "phone": booking.user.phone,
            "vehicle": f"{booking.vehicle.make} {booking.vehicle.model}",
            "date": booking.date,
            "time": booking.time,
            "status": booking.status
        }
    }

@app.put("/bookings/{booking_id}/cancel")
def cancel_booking_endpoint(booking_id: int, db: Session = Depends(get_db)):
    """
    Cancel a booking
    
    Path parameter:
    - booking_id: int
    """
    booking = cancel_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {
        "status": "success",
        "message": "✅ Booking cancelled successfully",
        "booking_id": booking.id
    }

# ==================== SERVICE CENTERS ENDPOINTS ====================

@app.get("/service-centers")
def get_service_centers_list(db: Session = Depends(get_db)):
    """
    Get all available service centers
    
    Returns: List of service centers with available slots
    """
    centers = db.query(ServiceCenter).all()
    result = []
    for center in centers:
        result.append({
            "id": center.id,
            "name": center.name,
            "address": center.address,
            "phone": center.phone,
            "city": center.city,
            "available_slots": center.available_slots
        })
    return {
        "status": "success",
        "total": len(result),
        "centers": result
    }

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Get booking statistics
    
    Returns: Total bookings, confirmed, pending, cancelled
    """
    total_bookings = db.query(Booking).count()
    confirmed = db.query(Booking).filter(Booking.status == "Confirmed").count()
    pending = db.query(Booking).filter(Booking.status == "Pending").count()
    cancelled = db.query(Booking).filter(Booking.status == "Cancelled").count()
    return {
        "status": "success",
        "stats": {
            "total_bookings": total_bookings,
            "confirmed": confirmed,
            "pending": pending,
            "cancelled": cancelled
        }
    }

# ==================== SCHEDULER ENDPOINTS ====================

@app.post("/schedule-appointment")
def schedule_appointment(booking: BookingCreate, db: Session = Depends(get_db)):
    """
    Smart appointment scheduling with AI slot optimization
    Uses greedy algorithm to find best available slot
    """
    from .scheduler import (
        find_preferred_slot, find_best_service_center, 
        get_booking_details, optimize_slots_for_day, predict_wait_time,
        get_slot_occupancy
    )
    try:
        # Find best service center for user
        service_center_id = find_best_service_center(db)
        
        # Find optimal slot using greedy algorithm
        assigned_date, assigned_time = find_preferred_slot(
            db, 
            booking.preferred_date,
            booking.preferred_time,
            service_center_id
        )
        
        # Get slot occupancy for predictions
        occupancy = get_slot_occupancy(db, assigned_date, service_center_id)
        
        # Predict wait time
        wait_time = predict_wait_time(occupancy, assigned_time)
        
        # Create the booking
        user = create_or_get_user(db, booking.user_name, booking.phone, booking.email)
        vehicle = create_or_get_vehicle(
            db, user.id, booking.vehicle_make, booking.vehicle_model, booking.vehicle_year
        )
        
        db_booking = models.Booking(
            user_id=user.id,
            vehicle_id=vehicle.id,
            date=assigned_date,
            time=assigned_time,
            service_type=booking.service_type,
            status="Confirmed",
            service_center_id=service_center_id
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        
        # Get booking details
        booking_details = get_booking_details(assigned_date, assigned_time, service_center_id, db)
        
        return {
            "status": "success",
            "message": "✅ Appointment scheduled successfully!",
            "booking_id": db_booking.id,
            "confirmation_number": f"AP-{db_booking.id:05d}",
            "customer_name": user.name,
            "vehicle": f"{vehicle.make} {vehicle.model}",
            "preferred_request": {
                "date": booking.preferred_date,
                "time": booking.preferred_time
            },
            "assigned_slot": {
                "date": assigned_date,
                "time": assigned_time
            },
            "slot_changed": assigned_date != booking.preferred_date or assigned_time != booking.preferred_time,
            "booking_details": booking_details,
            "estimated_wait": wait_time,
            "email_confirmation": f"Confirmation sent to {user.email}",
            "sms_notification": f"Notification sent to {user.phone}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scheduling failed: {str(e)}")

@app.get("/available-slots/{date}")
def get_available_slots(date: str, db: Session = Depends(get_db)):
    """
    Get all available slots for a given date
    
    Path parameter:
    - date: YYYY-MM-DD format
    """
    from .scheduler import optimize_slots_for_day
    try:
        # Get first service center
        center = db.query(models.ServiceCenter).first()
        if not center:
            raise HTTPException(status_code=404, detail="No service centers available")
        
        stats = optimize_slots_for_day(db, date, center.id)
        
        return {
            "status": "success",
            "date": date,
            "service_center": center.name,
            "available_slots_count": stats["total_available"],
            "occupancy": f"{stats['occupancy_percentage']}%",
            "slots": stats["occupancy_by_slot"],
            "peak_slot": stats["peak_slot"],
            "off_peak_slot": stats["off_peak_slot"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/schedule-analytics")
def get_schedule_analytics(db: Session = Depends(get_db)):
    """
    Get scheduling analytics for next 7 days
    Shows occupancy trends and recommendations
    """
    from .scheduler import optimize_slots_for_day
    from datetime import datetime, timedelta
    try:
        center = db.query(models.ServiceCenter).first()
        if not center:
            raise HTTPException(status_code=404, detail="No service centers available")
        
        analytics = []
        # Get stats for next 7 days
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            stats = optimize_slots_for_day(db, date, center.id)
            analytics.append(stats)
        
        # Find best day (least occupied)
        best_day = min(analytics, key=lambda x: x["occupancy_percentage"])
        
        return {
            "status": "success",
            "next_7_days": analytics,
            "recommendation": f"Best day to book: {best_day['date']} ({best_day['occupancy_percentage']}% occupied)",
            "best_slot": best_day["off_peak_slot"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== NLP / VOICE ASSISTANT ENDPOINTS ====================

@app.post("/nlp/parse")
def parse_voice_request(request: dict, db: Session = Depends(get_db)):
    """
    Parse natural language text for booking intent and entity extraction
    
    Request:
    {
        "text": "Book Tata Nexon service for tomorrow at 10 AM"
    }
    
    Returns:
    {
        "success": true/false,
        "intent": "book_service",
        "overall_confidence": 0.92,
        "extracted": {...},
        "confidence_scores": {...}
    }
    """
    try:
        text = request.get("text", "")
        if not text:
            raise ValueError("Text input required")
        
        result = parse_booking_request(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/nlp/entities")
def get_nlp_entities(db: Session = Depends(get_db)):
    """
    Get list of supported entities for voice parsing
    
    Useful for frontend to show what the NLP can understand
    """
    from .nlp_parser import VEHICLE_MAKES, SERVICE_TYPES
    
    return {
        "status": "success",
        "vehicle_makes": list(VEHICLE_MAKES.keys()),
        "service_types": SERVICE_TYPES,
        "available_times": ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"],
        "supported_date_formats": [
            "tomorrow",
            "next Monday/Tuesday/etc",
            "YYYY-MM-DD",
            "DD/MM/YYYY",
            "next N days"
        ]
    }

# ==================== NOTIFICATION ENDPOINTS ====================

@app.post("/notify/send-confirmation")
def send_booking_confirmation(booking_id: int, db: Session = Depends(get_db)):
    """
    Send confirmation email & SMS for a booking
    
    Query parameter:
    - booking_id: int
    """
    from .notifications import NotificationService
    
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        user = booking.user
        vehicle = booking.vehicle
        center = db.query(ServiceCenter).filter(ServiceCenter.id == booking.service_center_id).first()
        
        # Send email
        NotificationService.send_confirmation_email(
            booking_id=booking.id,
            user_name=user.name,
            phone=user.phone,
            email=user.email,
            vehicle=f"{vehicle.make} {vehicle.model}",
            date=booking.date,
            time=booking.time,
            service_center=center.name if center else "EY Service Center",
            confirmation_number=f"AP-{booking.id:05d}"
        )
        
        # Send SMS
        NotificationService.send_confirmation_sms(
            booking_id=booking.id,
            phone=user.phone,
            confirmation_number=f"AP-{booking.id:05d}",
            date=booking.date,
            time=booking.time,
            service_center=center.name if center else "EY Service Center"
        )
        
        return {
            "status": "success",
            "message": "✅ Confirmation email & SMS sent successfully",
            "booking_id": booking.id,
            "notifications": ["email", "sms"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/notify/send-reminder")
def send_booking_reminder(booking_id: int, db: Session = Depends(get_db)):
    """
    Send reminder notification for upcoming appointment
    """
    from .notifications import NotificationService
    
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        user = booking.user
        vehicle = booking.vehicle
        
        NotificationService.send_reminder_notification(
            booking_id=booking.id,
            user_name=user.name,
            phone=user.phone,
            email=user.email,
            date=booking.date,
            time=booking.time,
            vehicle=f"{vehicle.make} {vehicle.model}",
            confirmation_number=f"AP-{booking.id:05d}"
        )
        
        return {
            "status": "success",
            "message": "✅ Reminder notification sent",
            "booking_id": booking.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/notify/send-completion")
def send_completion_notification(booking_id: int, db: Session = Depends(get_db)):
    """
    Send completion notification when service is done
    """
    from .notifications import NotificationService
    
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        user = booking.user
        vehicle = booking.vehicle
        
        NotificationService.send_completion_notification(
            booking_id=booking.id,
            user_name=user.name,
            email=user.email,
            phone=user.phone,
            vehicle=f"{vehicle.make} {vehicle.model}",
            service_type=booking.service_type
        )
        
        # Update booking status
        booking.status = "Completed"
        db.commit()
        
        return {
            "status": "success",
            "message": "✅ Completion notification sent",
            "booking_id": booking.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/notifications/history/{booking_id}")
def get_booking_notification_history(booking_id: int, db: Session = Depends(get_db)):
    """
    Get all notifications sent for a specific booking
    """
    from .notifications import NotificationService
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    history = NotificationService.get_notification_history(booking_id)
    
    return {
        "status": "success",
        "booking_id": booking_id,
        "total_notifications": len(history),
        "notifications": history
    }

@app.get("/notifications/all")
def get_all_notifications():
    """
    Get all notifications sent in this session
    (Useful for testing and debugging)
    """
    from .notifications import NotificationService
    
    notifications = NotificationService.get_all_notifications()
    
    return {
        "status": "success",
        "total": len(notifications),
        "notifications": notifications
    }

@app.delete("/notifications/clear")
def clear_all_notifications():
    """
    Clear all notifications (for testing)
    """
    from .notifications import NotificationService
    
    result = NotificationService.clear_notifications()
    
    return {
        "status": "success",
        "message": f"✅ {result['cleared']} notifications cleared"
    }

# ==================== ERROR HANDLING ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global error handler for HTTP exceptions"""
    return {
        "status": "error",
        "detail": exc.detail,
        "status_code": exc.status_code
    }