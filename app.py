from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os
from sqlalchemy import text
from config import Config
from models import db, User, Customer, Service, Staff, Appointment, AppointmentService, Transaction, LoyaltyHistory, Attendance, Promotion, CampaignStats, WhatsAppConversation
from forms import LoginForm, CustomerForm, AppointmentForm, StaffForm, ServiceForm, PromotionForm
from utils import generate_invoice_pdf, generate_excel_report, send_whatsapp_message, send_email
from whatsapp_handler import WhatsAppAppointmentHandler

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

def has_column(table_name, column_name):
    """Check if a column exists on a SQLite table (compatible with SQLAlchemy 2.x Row)."""
    try:
        result = db.session.execute(text(f"PRAGMA table_info({table_name});"))
        for row in result:
            col_name = None
            # SQLAlchemy Row supports _mapping; fallback to tuple indexing
            mapping = getattr(row, '_mapping', None)
            if mapping and 'name' in mapping:
                col_name = mapping['name']
            else:
                try:
                    col_name = row[1]
                except Exception:
                    col_name = None
            if col_name == column_name:
                return True
    except Exception:
        pass
    return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        db.create_all()
        # Ensure 'is_archived' column exists for customers (lightweight migration for SQLite)
        try:
            result = db.session.execute(text("PRAGMA table_info(customers);"))
            columns = [row[1] for row in result]
            if 'is_archived' not in columns:
                db.session.execute(text("ALTER TABLE customers ADD COLUMN is_archived BOOLEAN DEFAULT 0;"))
                db.session.commit()
                print("Added is_archived column to customers table")
        except Exception as e:
            db.session.rollback()
            print(f"Migration error (may be OK if column exists): {e}")
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@salon.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

# Ensure migration runs before any requests
@app.before_request
def ensure_migration():
    """Ensure database schema is up to date before handling requests"""
    try:
        # Check if is_archived column exists
        if not has_column('customers', 'is_archived'):
            db.session.execute(text("ALTER TABLE customers ADD COLUMN is_archived BOOLEAN DEFAULT 0;"))
            db.session.commit()
    except Exception:
        db.session.rollback()

# Ensure DB is initialized when module is imported (Flask 3 removed before_first_request)
init_db()

# Routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    start_of_month = datetime.now().replace(day=1).date()
    
    # Key metrics
    total_customers = Customer.query.count()
    total_appointments = Appointment.query.filter(
        Appointment.appointment_date >= datetime.now(),
        Appointment.status == 'scheduled'
    ).count()
    
    monthly_revenue = db.session.query(db.func.sum(Transaction.total_amount)).filter(
        Transaction.created_at >= start_of_month,
        Transaction.payment_status == 'paid'
    ).scalar() or 0
    
    today_revenue = db.session.query(db.func.sum(Transaction.total_amount)).filter(
        db.func.date(Transaction.created_at) == today,
        Transaction.payment_status == 'paid'
    ).scalar() or 0
    
    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date >= datetime.now(),
        Appointment.status == 'scheduled'
    ).order_by(Appointment.appointment_date).limit(10).all()
    
    # Recent transactions
    recent_transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(5).all()
    
    return render_template('dashboard.html',
                         total_customers=total_customers,
                         total_appointments=total_appointments,
                         monthly_revenue=monthly_revenue,
                         today_revenue=today_revenue,
                         upcoming_appointments=upcoming_appointments,
                         recent_transactions=recent_transactions)

# Customer routes
@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '')
    # Exclude archived customers from main list
    base_query = Customer.query.filter(Customer.is_archived == False)
    if search:
        search_pattern = f'%{search}%'
        base_query = base_query.filter(
            (db.func.lower(Customer.name).like(db.func.lower(search_pattern))) |
            (Customer.mobile.contains(search)) |
            (db.func.lower(Customer.email).like(db.func.lower(search_pattern)))
        )
    customers_list = base_query.all()
    return render_template('customers.html', customers=customers_list, search=search)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            mobile=form.mobile.data,
            address=form.address.data
        )
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', form=form, title='Add Customer')

@app.route('/customers/<int:id>')
@login_required
def customer_detail(id):
    customer = Customer.query.get_or_404(id)
    appointments = Appointment.query.filter_by(customer_id=id).order_by(
        Appointment.appointment_date.desc()
    ).all()
    transactions = Transaction.query.filter_by(customer_id=id).order_by(
        Transaction.created_at.desc()
    ).all()
    loyalty_history = LoyaltyHistory.query.filter_by(customer_id=id).order_by(
        LoyaltyHistory.created_at.desc()
    ).all()
    return render_template('customer_detail.html', customer=customer,
                         appointments=appointments, transactions=transactions,
                         loyalty_history=loyalty_history)

@app.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete_customer(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to delete customers.', 'error')
        return redirect(url_for('customers'))
    
    customer = Customer.query.get_or_404(id)
    
    # Prevent deletion if there are transactions for audit integrity
    if customer.transactions:
        flash('Cannot delete customer with existing transactions. Please archive instead.', 'error')
        return redirect(url_for('customers'))
    
    try:
        # Appointments have cascade delete; remove the customer
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete customer: {str(e)}', 'error')
    return redirect(url_for('customers'))

@app.route('/customers/<int:id>/archive', methods=['POST'])
@login_required
def archive_customer(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to archive customers.', 'error')
        return redirect(url_for('customers'))
    customer = Customer.query.get_or_404(id)
    if customer.is_archived:
        flash('Customer already archived.', 'info')
        return redirect(url_for('customers'))
    customer.is_archived = True
    db.session.commit()
    flash('Customer archived successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/archives/customers')
@login_required
def archived_customers():
    archived = Customer.query.filter(Customer.is_archived == True).all()
    return render_template('archived_customers.html', customers=archived)

@app.route('/customers/<int:id>/unarchive', methods=['POST'])
@login_required
def unarchive_customer(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to unarchive.', 'error')
        return redirect(url_for('archived_customers'))
    customer = Customer.query.get_or_404(id)
    if not customer.is_archived:
        flash('Customer is not archived.', 'info')
        return redirect(url_for('customers'))
    customer.is_archived = False
    db.session.commit()
    flash('Customer unarchived successfully!', 'success')
    return redirect(url_for('archived_customers'))

# Appointment routes
@app.route('/appointments')
@login_required
def appointments():
    date_filter = request.args.get('date')
    status_filter = request.args.get('status', '')
    show_all = request.args.get('show_all', '')
    
    query = Appointment.query
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Appointment.appointment_date) == filter_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    elif not show_all:
        # Show appointments from the last 30 days and future (default view)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        query = query.filter(Appointment.appointment_date >= thirty_days_ago)
    # If show_all is set, don't apply any date filter
    
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    appointments_list = query.order_by(Appointment.appointment_date.desc()).all()
    
    return render_template('appointments.html', appointments=appointments_list, 
                         date_filter=date_filter, status_filter=status_filter)

@app.route('/appointments/add', methods=['GET', 'POST'])
@login_required
def add_appointment():
    form = AppointmentForm()
    form.customer_id.choices = [(c.id, f"{c.name} - {c.mobile}") for c in Customer.query.all()]
    form.staff_id.choices = [(s.id, s.name) for s in Staff.query.filter_by(is_active=True).all()]
    form.service_ids.choices = [(s.id, f"{s.name} - ₹{s.price}") for s in Service.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        try:
            appointment = Appointment(
                customer_id=form.customer_id.data,
                staff_id=form.staff_id.data,
                appointment_date=form.appointment_date.data,
                notes=form.notes.data
            )
            db.session.add(appointment)
            db.session.flush()
            
            # Add services
            total_amount = 0
            for service_id in form.service_ids.data:
                service = Service.query.get(service_id)
                if service:
                    appointment_service = AppointmentService(
                        appointment_id=appointment.id,
                        service_id=service_id,
                        price=service.price
                    )
                    total_amount += service.price
                    db.session.add(appointment_service)
            
            db.session.commit()
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating appointment: {str(e)}', 'error')
    else:
        # Show form validation errors
        if request.method == 'POST':
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
    
    return render_template('appointment_form.html', form=form, title='Add Appointment')

@app.route('/appointments/<int:id>/complete', methods=['GET', 'POST'])
@login_required
def complete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    if request.method == 'GET':
        # Show completion form
        total_amount = sum(aps.price for aps in appointment.services)
        return render_template('complete_appointment.html', appointment=appointment, total_amount=total_amount)
    
    # POST - Complete appointment
    appointment.status = 'completed'
    
    # Create transaction
    total_amount = sum(aps.price for aps in appointment.services)
    discount = float(request.form.get('discount', 0))
    tax = total_amount * 0.18  # 18% GST
    final_amount = total_amount - discount + tax
    
    transaction = Transaction(
        customer_id=appointment.customer_id,
        appointment_id=appointment.id,
        amount=total_amount,
        discount=discount,
        tax=tax,
        total_amount=final_amount,
        payment_method=request.form.get('payment_method', 'cash'),
        payment_status='paid',
        invoice_number=Transaction.generate_invoice_number()
    )
    
    # Calculate loyalty points
    from config import Config
    points_earned = int(final_amount * Config.LOYALTY_POINTS_PER_RUPEE)
    transaction.loyalty_points_earned = points_earned
    
    # Update customer
    customer = appointment.customer
    customer.loyalty_points += points_earned
    customer.total_spent += final_amount
    
    # Add loyalty history
    loyalty_history = LoyaltyHistory(
        customer_id=customer.id,
        transaction_id=transaction.id,
        points=points_earned,
        description=f"Points earned for transaction #{transaction.invoice_number}"
    )
    
    db.session.add(transaction)
    db.session.add(loyalty_history)
    db.session.commit()
    
    flash('Appointment completed and invoice generated!', 'success')
    return redirect(url_for('appointments'))

@app.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    # Check if appointment can be cancelled
    if appointment.status == 'completed':
        flash('Cannot cancel a completed appointment.', 'error')
        return redirect(url_for('appointments'))
    
    if appointment.status == 'cancelled':
        flash('Appointment is already cancelled.', 'error')
        return redirect(url_for('appointments'))
    
    # Update appointment status
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Send notification to customer
    try:
        customer = appointment.customer
        appointment_date = appointment.appointment_date.strftime('%d-%m-%Y')
        appointment_time = appointment.appointment_date.strftime('%I:%M %p')
        services_list = ', '.join([aps.service.name for aps in appointment.services])
        
        message = f"Dear {customer.name},\n\n"
        message += f"Your appointment has been cancelled.\n\n"
        message += f"Appointment Details:\n"
        message += f"Date: {appointment_date}\n"
        message += f"Time: {appointment_time}\n"
        message += f"Services: {services_list}\n"
        message += f"Staff: {appointment.staff.name}\n\n"
        message += f"If you have any questions, please contact us.\n\n"
        message += f"Thank you,\nPretty Saloon"
        
        send_whatsapp_message(customer.mobile, message)
        flash('Appointment cancelled and customer notified successfully!', 'success')
    except Exception as e:
        flash(f'Appointment cancelled but notification failed: {str(e)}', 'warning')
    
    return redirect(url_for('appointments'))

# Staff routes
@app.route('/staff')
@login_required
def staff():
    staff_list = Staff.query.all()
    return render_template('staff.html', staff_list=staff_list)

@app.route('/staff/add', methods=['GET', 'POST'])
@login_required
def add_staff():
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to add staff.', 'error')
        return redirect(url_for('staff'))
    
    form = StaffForm()
    if form.validate_on_submit():
        staff = Staff(
            name=form.name.data,
            email=form.email.data,
            mobile=form.mobile.data,
            specialization=form.specialization.data
        )
        db.session.add(staff)
        db.session.commit()
        flash('Staff added successfully!', 'success')
        return redirect(url_for('staff'))
    return render_template('staff_form.html', form=form, title='Add Staff')

@app.route('/staff/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_staff(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to edit staff.', 'error')
        return redirect(url_for('staff'))
    
    staff = Staff.query.get_or_404(id)
    form = StaffForm(obj=staff)
    
    if form.validate_on_submit():
        staff.name = form.name.data
        staff.email = form.email.data
        staff.mobile = form.mobile.data
        staff.specialization = form.specialization.data
        db.session.commit()
        flash('Staff updated successfully!', 'success')
        return redirect(url_for('staff'))
    
    return render_template('staff_form.html', form=form, title='Edit Staff', staff=staff)

@app.route('/staff/<int:id>/delete', methods=['POST'])
@login_required
def delete_staff(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to delete staff.', 'error')
        return redirect(url_for('staff'))
    
    staff = Staff.query.get_or_404(id)
    
    # Check if staff has appointments
    if staff.appointments:
        flash('Cannot delete staff member with existing appointments. Please deactivate instead.', 'error')
        return redirect(url_for('staff'))
    
    db.session.delete(staff)
    db.session.commit()
    flash('Staff deleted successfully!', 'success')
    return redirect(url_for('staff'))

# Service routes
@app.route('/services')
@login_required
def services():
    services_list = Service.query.all()
    return render_template('services.html', services=services_list)

@app.route('/services/add', methods=['GET', 'POST'])
@login_required
def add_service():
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to add services.', 'error')
        return redirect(url_for('services'))
    
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            duration=form.duration.data
        )
        db.session.add(service)
        db.session.commit()
        flash('Service added successfully!', 'success')
        return redirect(url_for('services'))
    return render_template('service_form.html', form=form, title='Add Service')

@app.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_service(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to edit services.', 'error')
        return redirect(url_for('services'))
    
    service = Service.query.get_or_404(id)
    form = ServiceForm(obj=service)
    
    if form.validate_on_submit():
        service.name = form.name.data
        service.description = form.description.data
        service.price = form.price.data
        service.duration = form.duration.data
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('services'))
    
    return render_template('service_form.html', form=form, title='Edit Service', service=service)

@app.route('/services/<int:id>/delete', methods=['POST'])
@login_required
def delete_service(id):
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to delete services.', 'error')
        return redirect(url_for('services'))
    
    service = Service.query.get_or_404(id)
    
    # Check if service has appointments
    if service.appointment_services:
        flash('Cannot delete service with existing appointments. Please deactivate instead.', 'error')
        return redirect(url_for('services'))
    
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('services'))

# Finance routes
@app.route('/finance')
@login_required
def finance():
    period = request.args.get('period', 'month')  # day, week, month, year
    today = datetime.now().date()
    
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == 'month':
        start_date = datetime.now().replace(day=1).date()
        end_date = today
    else:  # year
        start_date = datetime.now().replace(month=1, day=1).date()
        end_date = today
    
    transactions = Transaction.query.filter(
        db.func.date(Transaction.created_at) >= start_date,
        db.func.date(Transaction.created_at) <= end_date
    ).order_by(Transaction.created_at.desc()).all()
    
    total_revenue = sum(t.total_amount for t in transactions if t.payment_status == 'paid')
    total_transactions = len(transactions)
    
    return render_template('finance.html', transactions=transactions,
                         period=period, total_revenue=total_revenue,
                         total_transactions=total_transactions)

@app.route('/finance/invoice/<int:transaction_id>')
@login_required
def download_invoice(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    pdf = generate_invoice_pdf(transaction)
    return send_file(pdf, as_attachment=True, download_name=f'invoice_{transaction.invoice_number}.pdf')

@app.route('/finance/report')
@login_required
def download_report():
    period = request.args.get('period', 'month')
    format_type = request.args.get('format', 'excel')  # excel or pdf
    
    # Generate report based on period
    if format_type == 'excel':
        excel_file = generate_excel_report(period)
        return send_file(excel_file, as_attachment=True, download_name=f'report_{period}.xlsx')
    else:
        # PDF report can be implemented similarly
        flash('PDF reports coming soon!', 'info')
        return redirect(url_for('finance'))

# Promotions routes
@app.route('/promotions')
@login_required
def promotions():
    promotions_list = Promotion.query.order_by(Promotion.created_at.desc()).all()
    return render_template('promotions.html', promotions=promotions_list)

@app.route('/promotions/add', methods=['GET', 'POST'])
@login_required
def add_promotion():
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to create promotions.', 'error')
        return redirect(url_for('promotions'))
    
    form = PromotionForm()
    if form.validate_on_submit():
        promotion = Promotion(
            title=form.title.data,
            description=form.description.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            target_audience=form.target_audience.data
        )
        db.session.add(promotion)
        db.session.commit()
        flash('Promotion created successfully!', 'success')
        return redirect(url_for('promotions'))
    return render_template('promotion_form.html', form=form, title='Add Promotion')

@app.route('/promotions/<int:id>/send', methods=['POST'])
@login_required
def send_promotion(id):
    promotion = Promotion.query.get_or_404(id)
    send_via = request.form.getlist('send_via')  # whatsapp, email
    
    # Get target customers
    if promotion.target_audience == 'all':
        customers = Customer.query.all()
    elif promotion.target_audience == 'new_customers':
        # Customers with less than 3 transactions
        customers = [c for c in Customer.query.all() if len(c.transactions) < 3]
    else:  # loyal_customers
        customers = [c for c in Customer.query.all() if c.loyalty_points > 100]
    
    sent_count = 0
    for customer in customers:
        if 'whatsapp' in send_via:
            send_whatsapp_message(customer.mobile, f"{promotion.title}\n{promotion.description}")
            promotion.sent_via_whatsapp = True
        
        if 'email' in send_via and customer.email:
            send_email(customer.email, promotion.title, promotion.description)
            promotion.sent_via_email = True
        
        # Track campaign stats
        stats = CampaignStats(
            promotion_id=promotion.id,
            customer_id=customer.id
        )
        db.session.add(stats)
        sent_count += 1
    
    db.session.commit()
    flash(f'Promotion sent to {sent_count} customers!', 'success')
    return redirect(url_for('promotions'))

# Settings route
@app.route('/settings')
@login_required
def settings():
    if current_user.role != 'admin':
        flash('Only administrators can access settings.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('settings.html')

# WhatsApp Test route
@app.route('/whatsapp-test')
@login_required
def whatsapp_test_page():
    """Frontend page for testing WhatsApp booking"""
    return render_template('whatsapp_test.html')

# API routes
@app.route('/api/customers')
@login_required
def api_customers():
    customers = Customer.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'mobile': c.mobile} for c in customers])

@app.route('/api/appointments')
@login_required
def api_appointments():
    start = request.args.get('start')
    end = request.args.get('end')
    
    if start and end:
        appointments = Appointment.query.filter(
            Appointment.appointment_date >= datetime.fromisoformat(start),
            Appointment.appointment_date <= datetime.fromisoformat(end)
        ).all()
    else:
        appointments = Appointment.query.all()
    
    events = []
    for apt in appointments:
        events.append({
            'id': apt.id,
            'title': f"{apt.customer.name} - {', '.join([aps.service.name for aps in apt.services])}",
            'start': apt.appointment_date.isoformat(),
            'color': '#3b82f6' if apt.status == 'scheduled' else '#10b981' if apt.status == 'completed' else '#ef4444'
        })
    
    return jsonify(events)

# WhatsApp Webhook Routes
@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Webhook endpoint for receiving WhatsApp messages"""
    # For GET request (webhook verification)
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # Set your verify token in config
        if verify_token == app.config.get('WHATSAPP_VERIFY_TOKEN', 'salon_verify_token'):
            return challenge, 200
        return 'Invalid verification token', 403
    
    # For POST request (receiving messages)
    try:
        data = request.get_json()
        
        # Handle different WhatsApp API formats
        # Format 1: WhatsApp Cloud API / Twilio format
        if 'messages' in data or 'entry' in data:
            # Extract message details based on API format
            phone_number = None
            message_text = None
            
            # Try WhatsApp Cloud API format
            if 'entry' in data:
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        if 'messages' in value:
                            for message in value['messages']:
                                if message.get('type') == 'text':
                                    phone_number = message.get('from', '').replace('whatsapp:', '')
                                    message_text = message.get('text', {}).get('body', '')
            
            # Try Twilio format
            elif 'messages' in data:
                message = data['messages'][0] if data['messages'] else {}
                phone_number = message.get('from', '').replace('whatsapp:', '')
                message_text = message.get('body', '')
            
            # Try generic format
            else:
                phone_number = data.get('from', '').replace('whatsapp:', '')
                message_text = data.get('body', data.get('text', data.get('message', '')))
            
            if phone_number and message_text:
                # Process the message
                handler = WhatsAppAppointmentHandler(phone_number)
                handler.handle_message(message_text)
                return jsonify({'status': 'success'}), 200
        
        # Format 2: Simple JSON format (for testing)
        elif 'from' in data or 'phone' in data:
            phone_number = data.get('from') or data.get('phone')
            message_text = data.get('body') or data.get('text') or data.get('message', '')
            
            if phone_number and message_text:
                handler = WhatsAppAppointmentHandler(phone_number)
                handler.handle_message(message_text)
                return jsonify({'status': 'success'}), 200
        
        return jsonify({'status': 'no message found'}), 200
        
    except Exception as e:
        print(f"Error processing WhatsApp webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook/whatsapp/test', methods=['POST'])
@login_required
def whatsapp_test():
    """Test endpoint for WhatsApp (requires login)"""
    data = request.get_json()
    phone_number = data.get('phone')
    message_text = data.get('message', '')
    
    if not phone_number or not message_text:
        return jsonify({'error': 'Phone number and message required'}), 400
    
    try:
        handler = WhatsAppAppointmentHandler(phone_number)
        response = handler.handle_message(message_text)
        return jsonify({'status': 'success', 'response': response}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

