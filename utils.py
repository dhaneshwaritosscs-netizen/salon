from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment
from datetime import datetime
import requests
import os
from flask import current_app

def generate_invoice_pdf(transaction):
    """Generate PDF invoice for a transaction"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Title
    story.append(Paragraph("Pretty Saloon", title_style))
    story.append(Paragraph("INVOICE", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Invoice details
    invoice_data = [
        ['Invoice Number:', transaction.invoice_number],
        ['Date:', transaction.created_at.strftime('%Y-%m-%d %H:%M')],
        ['Customer:', transaction.customer.name],
        ['Mobile:', transaction.customer.mobile],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Services
    services_data = [['Service', 'Price']]
    if transaction.appointment:
        for aps in transaction.appointment.services:
            services_data.append([aps.service.name, f"₹{aps.price:.2f}"])
    
    services_table = Table(services_data, colWidths=[4*inch, 2*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(services_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Totals
    totals_data = [
        ['Subtotal:', f"₹{transaction.amount:.2f}"],
        ['Discount:', f"₹{transaction.discount:.2f}"],
        ['Tax (18%):', f"₹{transaction.tax:.2f}"],
        ['Total:', f"₹{transaction.total_amount:.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
    ]))
    story.append(totals_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_excel_report(period='month'):
    """Generate Excel report for financial data"""
    from models import Transaction, db
    from datetime import datetime, timedelta
    
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
    else:
        start_date = datetime.now().replace(month=1, day=1).date()
        end_date = today
    
    transactions = Transaction.query.filter(
        db.func.date(Transaction.created_at) >= start_date,
        db.func.date(Transaction.created_at) <= end_date
    ).order_by(Transaction.created_at).all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Report {period.title()}"
    
    # Headers
    headers = ['Date', 'Invoice #', 'Customer', 'Amount', 'Discount', 'Tax', 'Total', 'Payment Method', 'Status']
    ws.append(headers)
    
    # Style headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Data
    for txn in transactions:
        ws.append([
            txn.created_at.strftime('%Y-%m-%d %H:%M'),
            txn.invoice_number,
            txn.customer.name,
            txn.amount,
            txn.discount,
            txn.tax,
            txn.total_amount,
            txn.payment_method,
            txn.payment_status
        ])
    
    # Summary
    ws.append([])
    ws.append(['Total Revenue:', f"=SUM(G2:G{len(transactions)+1})"])
    ws.append(['Total Transactions:', len(transactions)])
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def send_whatsapp_message(phone_number, message):
    """Send WhatsApp message using API"""
    # Normalize phone number
    phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
    if phone.startswith('91') and len(phone) == 12:
        phone = phone
    elif len(phone) == 10:
        phone = '91' + phone
    
    api_url = current_app.config.get('WHATSAPP_API_URL')
    api_key = current_app.config.get('WHATSAPP_API_KEY')
    salon_number = current_app.config.get('WHATSAPP_PHONE_NUMBER', '7879501625')
    
    # If no API configured, use print for testing
    if not api_url or not api_key:
        try:
            # Try to print with UTF-8 encoding
            import sys
            if sys.stdout.encoding != 'utf-8':
                # Replace emojis for Windows console compatibility
                safe_message = message.encode('ascii', 'ignore').decode('ascii')
            else:
                safe_message = message
            print(f"\n{'='*60}")
            print(f"[WhatsApp Message]")
            print(f"To: {phone_number} ({phone})")
            print(f"From: {salon_number}")
            print(f"{'-'*60}")
            print(safe_message)
            print(f"{'='*60}\n")
        except:
            # Fallback: print without emojis
            safe_message = message.encode('ascii', 'ignore').decode('ascii')
            print(f"\n{'='*60}")
            print(f"[WhatsApp Message]")
            print(f"To: {phone_number} ({phone})")
            print(f"From: {salon_number}")
            print(f"{'-'*60}")
            print(safe_message)
            print(f"{'='*60}\n")
        return True
    
    try:
        # WhatsApp Cloud API format
        if 'graph.facebook.com' in api_url or 'whatsapp' in api_url.lower():
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'text',
                'text': {'body': message}
            }
            response = requests.post(api_url, headers=headers, json=payload)
            return response.status_code == 200
        
        # Twilio format
        elif 'twilio' in api_url.lower():
            from requests.auth import HTTPBasicAuth
            account_sid = api_key.split(':')[0] if ':' in api_key else api_key
            auth_token = api_key.split(':')[1] if ':' in api_key else current_app.config.get('WHATSAPP_AUTH_TOKEN', '')
            
            twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            payload = {
                'From': f'whatsapp:+{salon_number}',
                'To': f'whatsapp:+{phone}',
                'Body': message
            }
            response = requests.post(twilio_url, auth=HTTPBasicAuth(account_sid, auth_token), data=payload)
            return response.status_code in [200, 201]
        
        # Generic API format
        else:
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            payload = {'to': phone, 'message': message, 'from': salon_number}
            response = requests.post(api_url, headers=headers, json=payload)
            return response.status_code == 200
            
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        # Fallback to print for debugging
        print(f"\n[WhatsApp] Would send to {phone_number}: {message}\n")
        return False

def send_email(to_email, subject, body):
    """Send email (placeholder implementation)"""
    # This is a placeholder - integrate with actual email service
    # Example: Flask-Mail, SendGrid, AWS SES, etc.
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_username = current_app.config.get('MAIL_USERNAME')
    
    if not mail_server or not mail_username:
        print(f"[Email] Would send to {to_email}: {subject}\n{body}")
        return False
    
    try:
        # Example email sending code
        # from flask_mail import Message
        # msg = Message(subject, recipients=[to_email], body=body)
        # mail.send(msg)
        print(f"[Email] Would send to {to_email}: {subject}\n{body}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

