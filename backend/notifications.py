"""
Notification System for AutoPilot AI
Handles email, SMS, and push notifications (simulated)
"""

from datetime import datetime, timedelta
from typing import Dict, List
import json

# Simulated email/SMS gateway (in production, use Twilio, SendGrid, etc.)
class NotificationService:
    """Mock notification service for MVP"""
    
    # Store notifications in memory for this session
    sent_notifications = []
    
    @staticmethod
    def log_notification(notification: Dict) -> str:
        """Log notification to console and storage"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification["timestamp"] = timestamp
        NotificationService.sent_notifications.append(notification)
        
        print(f"\n{'='*80}")
        print(f"📧 NOTIFICATION LOG [{timestamp}]")
        print(f"{'='*80}")
        print(f"Type: {notification.get('type', 'Unknown')}")
        print(f"To: {notification.get('to', 'N/A')}")
        print(f"Subject: {notification.get('subject', 'N/A')}")
        print(f"\n{notification.get('message', 'No message')}")
        print(f"{'='*80}\n")
        
        return notification.get("id", "notification")
    
    @staticmethod
    def send_confirmation_email(booking_id: int, user_name: str, phone: str, 
                               email: str, vehicle: str, date: str, time: str,
                               service_center: str, confirmation_number: str) -> Dict:
        """Send booking confirmation email"""
        
        subject = f"✅ AutoPilot AI - Booking Confirmed (#{confirmation_number})"
        
        message = f"""
Dear {user_name},

🎉 Your service appointment has been confirmed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 BOOKING DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔔 Confirmation Number: {confirmation_number}
📅 Appointment Date: {date}
🕐 Appointment Time: {time}
🚗 Vehicle: {vehicle}
🏢 Service Center: {service_center}
📞 Phone: {phone}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ WHAT TO EXPECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Please arrive 5-10 minutes early
✓ Bring vehicle documents
✓ Service typically takes 1-2 hours
✓ We'll notify you when your vehicle is ready

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❓ QUESTIONS?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Contact our support team:
📧 support@autopilot-ai.com
📞 1800-AUTO-PILOT
🌐 www.autopilot-ai.com

Thank you for choosing AutoPilot AI! 🚗✨

Best regards,
AutoPilot AI Team
EY Techathon 6.0
"""
        
        notification = {
            "id": f"EMAIL-{booking_id}",
            "type": "email",
            "to": email,
            "subject": subject,
            "message": message,
            "booking_id": booking_id,
            "status": "sent"
        }
        
        return NotificationService.log_notification(notification)
    
    @staticmethod
    def send_confirmation_sms(booking_id: int, phone: str, confirmation_number: str, 
                             date: str, time: str, service_center: str) -> Dict:
        """Send booking confirmation SMS"""
        
        message = f"""
🎉 AutoPilot AI Booking Confirmed!

Booking: {confirmation_number}
Date: {date} | Time: {time}
Center: {service_center}

Arrive 5-10 min early. Track status: www.autopilot-ai.com/booking/{confirmation_number}

Questions? Call 1800-AUTO-PILOT
"""
        
        notification = {
            "id": f"SMS-{booking_id}",
            "type": "sms",
            "to": phone,
            "subject": "Booking Confirmation",
            "message": message,
            "booking_id": booking_id,
            "status": "sent"
        }
        
        return NotificationService.log_notification(notification)
    
    @staticmethod
    def send_reminder_notification(booking_id: int, user_name: str, phone: str, 
                                  email: str, date: str, time: str, 
                                  vehicle: str, confirmation_number: str) -> Dict:
        """Send pre-appointment reminder (24 hours before)"""
        
        subject = f"🔔 Reminder - Your AutoPilot AI Service Tomorrow"
        
        message = f"""
Hi {user_name},

📢 We want to remind you about your upcoming service appointment!

🕐 Tomorrow at {time}
🚗 Your {vehicle}
📍 Service Center location confirmed

Please confirm you'll be able to make it by replying to this email or calling us.

Confirmation #: {confirmation_number}

Drive safe!
AutoPilot AI Team
"""
        
        notification = {
            "id": f"REMINDER-{booking_id}",
            "type": "reminder",
            "to": email,
            "subject": subject,
            "message": message,
            "booking_id": booking_id,
            "status": "scheduled"
        }
        
        return NotificationService.log_notification(notification)
    
    @staticmethod
    def send_completion_notification(booking_id: int, user_name: str, email: str, 
                                    phone: str, vehicle: str, service_type: str,
                                    cost: str = "₹2,500", feedback_link: str = None) -> Dict:
        """Send service completion notification"""
        
        subject = f"✅ Your {vehicle} service is complete!"
        
        message = f"""
Dear {user_name},

Great news! Your {vehicle} {service_type} is complete! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 SERVICE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Vehicle: {vehicle}
Service: {service_type}
Booking ID: {booking_id}
Status: ✅ Completed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 AMOUNT PAYABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimated: {cost}

Payment methods:
✓ Card/UPI at center
✓ Online payment link below
✓ EMI options available

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your vehicle is ready for pickup at your scheduled service center.

We'd love your feedback! {feedback_link or 'Rate us on AutoPilot AI app'}

Thank you for choosing us! 🚗✨
"""
        
        notification = {
            "id": f"COMPLETE-{booking_id}",
            "type": "completion",
            "to": email,
            "subject": subject,
            "message": message,
            "booking_id": booking_id,
            "status": "sent"
        }
        
        return NotificationService.log_notification(notification)
    
    @staticmethod
    def get_all_notifications() -> List[Dict]:
        """Get all sent notifications"""
        return NotificationService.sent_notifications
    
    @staticmethod
    def get_notification_history(booking_id: int) -> List[Dict]:
        """Get all notifications for a specific booking"""
        return [n for n in NotificationService.sent_notifications if n.get("booking_id") == booking_id]
    
    @staticmethod
    def clear_notifications() -> Dict:
        """Clear all notifications (for testing)"""
        count = len(NotificationService.sent_notifications)
        NotificationService.sent_notifications = []
        return {"status": "success", "cleared": count}
