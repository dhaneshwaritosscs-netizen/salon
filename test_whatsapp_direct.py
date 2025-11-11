"""
Direct test script for WhatsApp booking
Uses handler directly without web server
"""
import sys
import os
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from app import app, db
from models import Staff, Service, Appointment, Customer
from whatsapp_handler import WhatsAppAppointmentHandler

def test_whatsapp_booking():
    phone = "1245343453"
    
    with app.app_context():
        # Initialize database
        db.create_all()
        
        # Get tomorrow's date
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime("%d-%m-%Y")
        
        print("="*60)
        print("WhatsApp Appointment Booking Test")
        print("="*60)
        print(f"Phone Number: {phone}")
        print(f"Date: {date_str} (Tomorrow)")
        print("="*60)
        
        try:
            # Step 1: Start conversation
            print("\n[Step 1] Sending: Hi")
            handler = WhatsAppAppointmentHandler(phone)
            response1 = handler.handle_message("Hi")
            print("✓ Step 1 completed")
            print(f"Response preview: {response1[:100] if response1 else 'None'}...")
            
            # Step 2: Send name
            print("\n[Step 2] Sending: Test Customer")
            handler = WhatsAppAppointmentHandler(phone)
            response2 = handler.handle_message("Test Customer")
            print("✓ Step 2 completed")
            
            # Step 3: Send mobile
            print("\n[Step 3] Sending: 1245343453")
            handler = WhatsAppAppointmentHandler(phone)
            response3 = handler.handle_message("1245343453")
            print("✓ Step 3 completed")
            
            # Step 4: Select staff (1)
            print("\n[Step 4] Sending: 1")
            handler = WhatsAppAppointmentHandler(phone)
            response4 = handler.handle_message("1")
            print("✓ Step 4 completed")
            
            # Step 5: Send date (tomorrow)
            print(f"\n[Step 5] Sending: {date_str}")
            handler = WhatsAppAppointmentHandler(phone)
            response5 = handler.handle_message(date_str)
            print("✓ Step 5 completed")
            
            # Step 6: Send time
            print("\n[Step 6] Sending: 14:30")
            handler = WhatsAppAppointmentHandler(phone)
            response6 = handler.handle_message("14:30")
            print("✓ Step 6 completed")
            
            # Step 7: Select service (1)
            print("\n[Step 7] Sending: 1")
            handler = WhatsAppAppointmentHandler(phone)
            response7 = handler.handle_message("1")
            print("✓ Step 7 completed")
            
            # Step 8: Notes (no)
            print("\n[Step 8] Sending: no")
            handler = WhatsAppAppointmentHandler(phone)
            response8 = handler.handle_message("no")
            print("✓ Step 8 completed")
            
            # Step 9: Confirm (yes)
            print("\n[Step 9] Sending: yes")
            handler = WhatsAppAppointmentHandler(phone)
            response9 = handler.handle_message("yes")
            print("✓ Step 9 completed")
            
            # Check if appointment was created
            print("\n" + "="*60)
            print("Checking if appointment was created...")
            print("="*60)
            
            # Get customer
            customer = Customer.query.filter_by(mobile="1245343453").first()
            if customer:
                print(f"✓ Customer found: {customer.name} (ID: {customer.id})")
                
                # Get appointments
                appointments = Appointment.query.filter_by(customer_id=customer.id).order_by(
                    Appointment.created_at.desc()
                ).all()
                
                if appointments:
                    latest = appointments[0]
                    print(f"\n✓ Appointment created successfully!")
                    print(f"  Appointment ID: {latest.id}")
                    print(f"  Date: {latest.appointment_date.strftime('%d-%m-%Y %H:%M')}")
                    print(f"  Staff: {latest.staff.name}")
                    print(f"  Status: {latest.status}")
                    print(f"  Services: {', '.join([aps.service.name for aps in latest.services])}")
                    print("\n" + "="*60)
                    print("SUCCESS! Appointment is ready to show in frontend.")
                    print("="*60)
                    return True
                else:
                    print("X No appointments found")
                    return False
            else:
                print("X Customer not found")
                return False
                
        except Exception as e:
            print(f"\nX Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_whatsapp_booking()
    sys.exit(0 if success else 1)

