"""
Natural Language Processing for AutoPilot AI
Handles intent detection and entity extraction
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Vehicle makes database (popular Indian vehicles)
VEHICLE_MAKES = {
    "tata": "Tata",
    "maruti": "Maruti",
    "hyundai": "Hyundai",
    "mahindra": "Mahindra",
    "kia": "Kia",
    "renault": "Renault",
    "nissan": "Nissan",
    "skoda": "Skoda",
    "volkswagen": "Volkswagen",
    "toyota": "Toyota",
    "honda": "Honda",
    "force": "Force",
    "jeep": "Jeep",
    "mg": "MG",
    "citroen": "Citroen"
}

# Vehicle models database
VEHICLE_MODELS = {
    "tata": ["nexon", "harrier", "safari", "altroz", "punch", "tigor"],
    "maruti": ["swift", "wagon-r", "alto", "dzire", "brezza", "s-cross", "baleno"],
    "hyundai": ["creta", "venue", "tucson", "i20", "i10", "kona"],
    "mahindra": ["xuv500", "xuv700", "scorpio", "bolero", "thar", "nuvosport"],
    "kia": ["seltos", "sonet", "carens", "niro"],
    "renault": ["duster", "kwid", "triber"],
    "nissan": ["magnite", "kicks"],
    "skoda": ["rapid", "slavia", "superb"],
    "volkswagen": ["polo", "vento"],
    "toyota": ["innova", "fortuner", "glanza"],
    "honda": ["city", "civic", "jazz"],
    "jeep": ["wrangler", "compass"],
    "mg": ["hector", "astor", "gloster"],
    "citroen": ["c3", "c5"]
}

# Service types
SERVICE_TYPES = [
    "general service", "oil change", "maintenance", "inspection", 
    "repair", "battery replacement", "tire replacement", "alignment"
]

# Time slots
AVAILABLE_SLOTS = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]


def detect_intent(text: str) -> Dict:
    """
    Detect user intent from text
    
    Returns:
        {
            "intent": "book_service" | "check_booking" | "cancel_booking" | "unknown",
            "confidence": 0.0 to 1.0
        }
    """
    text_lower = text.lower()
    
    booking_keywords = ["book", "schedule", "appointment", "service", "need", "want"]
    check_keywords = ["check", "view", "status", "booking", "confirm"]
    cancel_keywords = ["cancel", "delete", "remove", "reschedule"]
    
    if any(kw in text_lower for kw in booking_keywords):
        return {"intent": "book_service", "confidence": 0.95}
    elif any(kw in text_lower for kw in check_keywords):
        return {"intent": "check_booking", "confidence": 0.90}
    elif any(kw in text_lower for kw in cancel_keywords):
        return {"intent": "cancel_booking", "confidence": 0.88}
    
    return {"intent": "unknown", "confidence": 0.0}


def extract_vehicle(text: str) -> Tuple[str, str, float]:
    """
    Extract vehicle make and model from text
    
    Returns:
        (make, model, confidence)
    """
    text_lower = text.lower()
    
    detected_make = None
    detected_model = None
    confidence = 0.0
    
    # Check for vehicle make
    for make_key, make_name in VEHICLE_MAKES.items():
        if make_key in text_lower:
            detected_make = make_name
            confidence = 0.90
            
            # Now check for model
            if make_key in VEHICLE_MODELS:
                for model in VEHICLE_MODELS[make_key]:
                    if model in text_lower:
                        detected_model = model.title()
                        confidence = 0.95
                        break
            break
    
    return (detected_make or "Unknown", detected_model or "Unknown", confidence)


def extract_date(text: str) -> Tuple[str, float]:
    """
    Extract date from text
    
    Supports: "tomorrow", "next Monday", "2025-11-15", "15/11/2025", etc.
    
    Returns:
        (date_string YYYY-MM-DD, confidence)
    """
    text_lower = text.lower()
    today = datetime.today()
    confidence = 0.0
    
    # Tomorrow
    if "tomorrow" in text_lower:
        tomorrow = today + timedelta(days=1)
        return (tomorrow.strftime("%Y-%m-%d"), 0.95)
    
    # Day names
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    for day_name, day_offset in day_map.items():
        if day_name in text_lower:
            days_ahead = day_offset - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            future_date = today + timedelta(days=days_ahead)
            return (future_date.strftime("%Y-%m-%d"), 0.90)
    
    # Regex: YYYY-MM-DD
    match_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match_iso:
        return (match_iso.group(0), 0.95)
    
    # Regex: DD/MM/YYYY
    match_slash = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match_slash:
        day, month, year = match_slash.groups()
        try:
            parsed = datetime(int(year), int(month), int(day))
            return (parsed.strftime("%Y-%m-%d"), 0.92)
        except:
            pass
    
    # Regex: Next N days
    match_days = re.search(r"next\s+(\d+)\s+days?", text_lower)
    if match_days:
        days = int(match_days.group(1))
        future = today + timedelta(days=days)
        return (future.strftime("%Y-%m-%d"), 0.85)
    
    return (today.strftime("%Y-%m-%d"), 0.5)


def extract_time(text: str) -> Tuple[str, float]:
    """
    Extract time from text
    
    Supports: "10:00", "10 AM", "2 PM", "morning", "afternoon", etc.
    
    Returns:
        (time_string HH:MM, confidence)
    """
    text_lower = text.lower()
    confidence = 0.0
    
    # Regex: HH:MM or H:MM
    match_time = re.search(r"(\d{1,2}):(\d{2})", text)
    if match_time:
        hour, minute = match_time.groups()
        time_str = f"{int(hour):02d}:{minute}"
        if time_str in AVAILABLE_SLOTS:
            return (time_str, 0.95)
    
    # AM/PM format
    am_pm_match = re.search(r"(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)", text_lower)
    if am_pm_match:
        hour = int(am_pm_match.group(1))
        period = am_pm_match.group(2).lower()
        
        if "p" in period and hour != 12:
            hour += 12
        elif "a" in period and hour == 12:
            hour = 0
        
        # Map to available slot
        for slot in AVAILABLE_SLOTS:
            if int(slot.split(":")[0]) == hour:
                return (slot, 0.90)
    
    # Morning/Afternoon/Evening keywords
    if "morning" in text_lower:
        return ("09:00", 0.70)
    elif "afternoon" in text_lower:
        return ("14:00", 0.70)
    elif "evening" in text_lower:
        return ("16:00", 0.70)
    
    return ("10:00", 0.5)


def extract_service_type(text: str) -> Tuple[str, float]:
    """
    Extract service type from text
    
    Returns:
        (service_type, confidence)
    """
    text_lower = text.lower()
    confidence = 0.0
    
    for service in SERVICE_TYPES:
        if service in text_lower:
            return (service.title(), 0.90)
    
    return ("General Service", 0.5)


def parse_booking_request(text: str) -> Dict:
    """
    Full NLP parsing for a booking request
    
    Returns complete extracted data with confidence scores
    """
    intent = detect_intent(text)
    
    if intent["intent"] != "book_service":
        return {
            "success": False,
            "intent": intent["intent"],
            "message": f"Detected intent: {intent['intent']} (confidence: {intent['confidence']:.0%})"
        }
    
    vehicle_make, vehicle_model, vehicle_conf = extract_vehicle(text)
    date, date_conf = extract_date(text)
    time, time_conf = extract_time(text)
    service_type, service_conf = extract_service_type(text)
    
    # Calculate overall confidence
    overall_confidence = (vehicle_conf + date_conf + time_conf + service_conf) / 4
    
    return {
        "success": True,
        "intent": intent["intent"],
        "overall_confidence": overall_confidence,
        "extracted": {
            "vehicle_make": vehicle_make,
            "vehicle_model": vehicle_model,
            "date": date,
            "time": time,
            "service_type": service_type
        },
        "confidence_scores": {
            "vehicle": vehicle_conf,
            "date": date_conf,
            "time": time_conf,
            "service": service_conf
        },
        "message": f"🎤 Parsed successfully! Confidence: {overall_confidence:.0%}"
    }
