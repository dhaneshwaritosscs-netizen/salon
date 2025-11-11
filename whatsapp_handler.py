"""
WhatsApp Conversation Handler for Appointment Booking
Handles step-by-step conversation flow for booking appointments via WhatsApp
"""
import json
import re
from datetime import datetime, timedelta
from flask import current_app
from models import db, Customer, Staff, Service, Appointment, AppointmentService, WhatsAppConversation
from utils import send_whatsapp_message

class WhatsAppAppointmentHandler:
    """Handles WhatsApp appointment booking conversations"""
    
    SALON_NUMBER = "7879501625"
    
    # Conversation steps
    STEP_START = 'start'
    STEP_NAME = 'name'
    STEP_MOBILE = 'mobile'
    STEP_EMAIL = 'email'
    STEP_STAFF = 'staff'
    STEP_DATE = 'date'
    STEP_TIME = 'time'
    STEP_SERVICES = 'services'
    STEP_NOTES = 'notes'
    STEP_CONFIRM = 'confirm'
    STEP_COMPLETED = 'completed'
    
    def __init__(self, phone_number):
        self.phone_number = self._normalize_phone(phone_number)
        self.conversation = self._get_or_create_conversation()
        self.data = self._load_data()
    
    def _normalize_phone(self, phone):
        """Normalize phone number (remove +, spaces, etc.)"""
        phone = re.sub(r'[^\d]', '', phone)
        if phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        if len(phone) == 10:
            phone = '91' + phone
        return phone
    
    def _get_or_create_conversation(self):
        """Get existing conversation or create new one"""
        conv = WhatsAppConversation.query.filter_by(
            phone_number=self.phone_number,
            is_active=True
        ).first()
        
        if not conv:
            conv = WhatsAppConversation(
                phone_number=self.phone_number,
                step=self.STEP_START,
                data=json.dumps({})
            )
            db.session.add(conv)
            db.session.commit()
        
        return conv
    
    def _load_data(self):
        """Load conversation data from JSON"""
        try:
            return json.loads(self.conversation.data) if self.conversation.data else {}
        except:
            return {}
    
    def _save_data(self):
        """Save conversation data to JSON"""
        self.conversation.data = json.dumps(self.data)
        self.conversation.updated_at = datetime.utcnow()
        db.session.commit()
    
    def _send_message(self, message):
        """Send WhatsApp message"""
        # Remove country code for display
        display_number = self.phone_number[2:] if self.phone_number.startswith('91') else self.phone_number
        return send_whatsapp_message(display_number, message)
    
    def _get_staff_list(self):
        """Get list of active staff"""
        staff_list = Staff.query.filter_by(is_active=True).all()
        return staff_list
    
    def _get_services_list(self):
        """Get list of active services"""
        services_list = Service.query.filter_by(is_active=True).all()
        return services_list
    
    def _format_staff_options(self):
        """Format staff list as numbered options"""
        staff_list = self._get_staff_list()
        if not staff_list:
            return None
        
        options = []
        for idx, staff in enumerate(staff_list, 1):
            options.append(f"{idx}. {staff.name}")
        return "\n".join(options)
    
    def _format_services_options(self):
        """Format services list as numbered options"""
        services_list = self._get_services_list()
        if not services_list:
            return None
        
        options = []
        for idx, service in enumerate(services_list, 1):
            options.append(f"{idx}. {service.name} - ₹{service.price}")
        return "\n".join(options)
    
    def handle_message(self, message_text):
        """Handle incoming WhatsApp message"""
        message_text = message_text.strip()
        
        # Check for cancel command
        if message_text.lower() in ['cancel', 'stop', 'exit']:
            self._cancel_conversation()
            return
        
        # Handle based on current step
        if self.conversation.step == self.STEP_START:
            return self._handle_start()
        elif self.conversation.step == self.STEP_NAME:
            return self._handle_name(message_text)
        elif self.conversation.step == self.STEP_MOBILE:
            return self._handle_mobile(message_text)
        elif self.conversation.step == self.STEP_EMAIL:
            return self._handle_email(message_text)
        elif self.conversation.step == self.STEP_STAFF:
            return self._handle_staff(message_text)
        elif self.conversation.step == self.STEP_DATE:
            return self._handle_date(message_text)
        elif self.conversation.step == self.STEP_TIME:
            return self._handle_time(message_text)
        elif self.conversation.step == self.STEP_SERVICES:
            return self._handle_services(message_text)
        elif self.conversation.step == self.STEP_NOTES:
            return self._handle_notes(message_text)
        elif self.conversation.step == self.STEP_CONFIRM:
            return self._handle_confirm(message_text)
        else:
            return self._handle_start()
    
    def _handle_start(self):
        """Start the conversation"""
        welcome_msg = """👋 Welcome to *Pretty Saloon*!

You can book an appointment through WhatsApp.

Please provide your *name*:"""
        
        self.conversation.step = self.STEP_NAME
        self._save_data()
        self._send_message(welcome_msg)
        return welcome_msg
    
    def _handle_name(self, name):
        """Handle name input"""
        if not name or len(name) < 2:
            msg = "Please enter a valid name (at least 2 characters):"
            self._send_message(msg)
            return msg
        
        self.data['name'] = name
        self.conversation.step = self.STEP_MOBILE
        self._save_data()
        
        # Check if customer exists
        customer = Customer.query.filter_by(mobile=self.phone_number[2:] if self.phone_number.startswith('91') else self.phone_number).first()
        if customer:
            self.data['mobile'] = customer.mobile
            self.conversation.customer_id = customer.id
            self.conversation.step = self.STEP_STAFF
            self._save_data()
            msg = f"Hello {name}! 👋\n\nPlease select a staff member:\n\n{self._format_staff_options()}\n\nSend only the number (e.g., 1)"
            self._send_message(msg)
            return msg
        
        msg = f"Thank you {name}! 🙏\n\nPlease provide your *mobile number* (10 digits):"
        self._send_message(msg)
        return msg
    
    def _handle_mobile(self, mobile):
        """Handle mobile number input"""
        mobile = re.sub(r'[^\d]', '', mobile)
        
        if len(mobile) != 10 or not mobile.isdigit():
            msg = "Please enter a valid 10-digit mobile number:"
            self._send_message(msg)
            return msg
        
        self.data['mobile'] = mobile
        # Ask for email after mobile
        self.conversation.step = self.STEP_EMAIL
        self._save_data()
        
        # Check if customer exists, if not create (without email yet)
        customer = Customer.query.filter_by(mobile=mobile).first()
        if not customer:
            customer = Customer(
                name=self.data.get('name', ''),
                mobile=mobile
            )
            db.session.add(customer)
            db.session.commit()
        
        self.conversation.customer_id = customer.id
        self._save_data()

        msg = "Mobile number saved ✅\n\nPlease provide your *email address* (optional, send 'skip' to continue):"
        self._send_message(msg)
        return msg

    def _handle_email(self, email_input):
        """Handle email input (optional)"""
        email_text = email_input.strip()
        if email_text.lower() in ['skip', 'no', 'na', 'none', '']:
            email_text = ''
        else:
            # Basic email validation
            if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email_text):
                msg = "Please enter a valid email address or type 'skip' to continue:"
                self._send_message(msg)
                return msg

        self.data['email'] = email_text
        self.conversation.step = self.STEP_STAFF
        self._save_data()

        # Update customer's email if provided
        if self.conversation.customer_id and email_text:
            try:
                customer = Customer.query.get(self.conversation.customer_id)
                if customer:
                    customer.email = email_text
                    db.session.commit()
            except Exception:
                db.session.rollback()

        staff_options = self._format_staff_options()
        if not staff_options:
            msg = "Sorry, no staff members are available at this time."
            self._cancel_conversation()
            self._send_message(msg)
            return msg

        msg = f"Email {'saved' if email_text else 'skipped'} ✅\n\nPlease select a staff member:\n\n{staff_options}\n\nSend only the number (e.g., 1)"
        self._send_message(msg)
        return msg
    
    def _handle_staff(self, staff_input):
        """Handle staff selection"""
        try:
            staff_num = int(staff_input.strip())
            staff_list = self._get_staff_list()
            
            if staff_num < 1 or staff_num > len(staff_list):
                msg = f"Please select a number between 1 and {len(staff_list)}:"
                self._send_message(msg)
                return msg
            
            selected_staff = staff_list[staff_num - 1]
            self.data['staff_id'] = selected_staff.id
            self.data['staff_name'] = selected_staff.name
            self.conversation.step = self.STEP_DATE
            self._save_data()
            
            msg = f"Staff: {selected_staff.name} ✅\n\nPlease provide the appointment *date*:\n\nFormat: DD-MM-YYYY\nExample: 15-01-2025"
            self._send_message(msg)
            return msg
        except ValueError:
            msg = "Please send only a number:"
            self._send_message(msg)
            return msg
    
    def _handle_date(self, date_input):
        """Handle date input"""
        # Try to parse date in various formats
        date_formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y']
        parsed_date = None
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_input.strip(), fmt).date()
                break
            except:
                continue
        
        if not parsed_date:
            msg = "Please send the date in correct format:\nDD-MM-YYYY\nExample: 15-01-2025"
            self._send_message(msg)
            return msg
        
        # Check if date is in the past
        if parsed_date < datetime.now().date():
            msg = "Please select today's date or a future date:"
            self._send_message(msg)
            return msg
        
        self.data['date'] = parsed_date.strftime('%Y-%m-%d')
        self.conversation.step = self.STEP_TIME
        self._save_data()
        
        msg = f"Date: {parsed_date.strftime('%d-%m-%Y')} ✅\n\nPlease provide the *time*:\n\nFormat: HH:MM (24-hour format)\nExample: 14:30 or 09:00"
        self._send_message(msg)
        return msg
    
    def _handle_time(self, time_input):
        """Handle time input"""
        # Handle AM/PM format
        time_input_clean = time_input.strip().lower()
        hour = None
        minute = None
        
        # Try 12-hour format with AM/PM
        am_pm_match = re.match(r'(\d{1,2})[:.](\d{2})\s*(am|pm)', time_input_clean)
        if am_pm_match:
            hour = int(am_pm_match.group(1))
            minute = int(am_pm_match.group(2))
            period = am_pm_match.group(3)
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
        else:
            # Try 24-hour format
            time_pattern = r'(\d{1,2})[:.](\d{2})'
            match = re.match(time_pattern, time_input_clean)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
        
        if hour is None or minute is None:
            msg = "Please send time in correct format:\nHH:MM (24-hour) or HH:MM AM/PM\nExample: 14:30 or 02:30 PM"
            self._send_message(msg)
            return msg
        
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            msg = "Please enter a valid time (00:00 to 23:59):"
            self._send_message(msg)
            return msg
        
        # Combine date and time
        appointment_datetime = datetime.strptime(self.data['date'], '%Y-%m-%d').replace(hour=hour, minute=minute)
        
        # Check if time is in the past (if today's date)
        if appointment_datetime < datetime.now():
            msg = "Please select a future time:"
            self._send_message(msg)
            return msg
        
        self.data['appointment_datetime'] = appointment_datetime.isoformat()
        self.conversation.step = self.STEP_SERVICES
        self._save_data()
        
        services_options = self._format_services_options()
        if not services_options:
            msg = "Sorry, no services are available at this time."
            self._cancel_conversation()
            self._send_message(msg)
            return msg
        
        msg = f"Time: {hour:02d}:{minute:02d} ✅\n\nPlease select *services* (one or more):\n\n{services_options}\n\nFor multiple services, separate numbers with comma (e.g., 1,2,3)"
        self._send_message(msg)
        return msg
    
    def _handle_services(self, services_input):
        """Handle services selection"""
        try:
            service_nums = [int(x.strip()) for x in services_input.split(',')]
            services_list = self._get_services_list()
            
            if not service_nums or any(n < 1 or n > len(services_list) for n in service_nums):
                msg = f"Please select numbers between 1 and {len(services_list)}:"
                self._send_message(msg)
                return msg
            
            selected_services = [services_list[n - 1] for n in service_nums]
            self.data['service_ids'] = [s.id for s in selected_services]
            self.data['service_names'] = [s.name for s in selected_services]
            self.data['total_price'] = sum(s.price for s in selected_services)
            
            self.conversation.step = self.STEP_NOTES
            self._save_data()
            
            services_text = ", ".join([f"{s.name} (₹{s.price})" for s in selected_services])
            msg = f"Services: {services_text} ✅\n\nTotal amount: ₹{self.data['total_price']}\n\nDo you have any *notes* or special requirements? (If not, send 'no'):"
            self._send_message(msg)
            return msg
        except ValueError:
            msg = "Please separate numbers with comma (e.g., 1,2,3):"
            self._send_message(msg)
            return msg
    
    def _handle_notes(self, notes_input):
        """Handle notes input"""
        if notes_input.lower() in ['no', 'na', 'none', '']:
            self.data['notes'] = ''
        else:
            self.data['notes'] = notes_input
        
        self.conversation.step = self.STEP_CONFIRM
        self._save_data()
        
        return self._show_confirmation()
    
    def _show_confirmation(self):
        """Show appointment summary for confirmation"""
        date_obj = datetime.fromisoformat(self.data['appointment_datetime'])
        
        summary = f"""📋 *Appointment Summary:*

👤 *Customer:* {self.data.get('name', 'N/A')}
📱 *Mobile:* {self.data.get('mobile', 'N/A')}
👨‍💼 *Staff:* {self.data.get('staff_name', 'N/A')}
📅 *Date:* {date_obj.strftime('%d-%m-%Y')}
⏰ *Time:* {date_obj.strftime('%H:%M')}
💆 *Services:* {', '.join(self.data.get('service_names', []))}
💰 *Total:* ₹{self.data.get('total_price', 0)}
📝 *Notes:* {self.data.get('notes', 'None')}

Is this correct? Send 'yes' to confirm, or 'no' to cancel."""
        
        self._send_message(summary)
        return summary
    
    def _handle_confirm(self, confirm_input):
        """Handle confirmation"""
        if confirm_input.lower() not in ['yes', 'y', 'ok', 'confirm']:
            self._cancel_conversation()
            msg = "Appointment has been cancelled. Thank you!"
            self._send_message(msg)
            return msg
        
        # Create appointment
        try:
            appointment_datetime = datetime.fromisoformat(self.data['appointment_datetime'])
            
            appointment = Appointment(
                customer_id=self.conversation.customer_id,
                staff_id=self.data['staff_id'],
                appointment_date=appointment_datetime,
                notes=self.data.get('notes', ''),
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.flush()
            
            # Add services
            for service_id in self.data['service_ids']:
                service = Service.query.get(service_id)
                if service:
                    appointment_service = AppointmentService(
                        appointment_id=appointment.id,
                        service_id=service_id,
                        price=service.price
                    )
                    db.session.add(appointment_service)
            
            self.conversation.appointment_id = appointment.id
            self.conversation.step = self.STEP_COMPLETED
            self.conversation.is_active = False
            self._save_data()
            
            db.session.commit()
            
            # Send confirmation message
            date_obj = datetime.fromisoformat(self.data['appointment_datetime'])
            confirm_msg = f"""✅ *Appointment Confirmed!*

Your appointment has been successfully booked!

📋 *Appointment Details:*
• Date: {date_obj.strftime('%d-%m-%Y')}
• Time: {date_obj.strftime('%H:%M')}
• Staff: {self.data.get('staff_name', 'N/A')}
• Services: {', '.join(self.data.get('service_names', []))}
• Total: ₹{self.data.get('total_price', 0)}

Appointment ID: #{appointment.id}

Please arrive on time. Thank you! 🙏"""
            
            self._send_message(confirm_msg)
            return confirm_msg
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Sorry, there was an error booking the appointment. Please try again later.\n\nError: {str(e)}"
            self._send_message(error_msg)
            self._cancel_conversation()
            return error_msg
    
    def _cancel_conversation(self):
        """Cancel the conversation"""
        self.conversation.is_active = False
        self.conversation.step = self.STEP_COMPLETED
        self._save_data()


