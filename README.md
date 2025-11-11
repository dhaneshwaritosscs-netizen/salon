# Pretty Saloon Management System

A comprehensive cloud-based salon management system built with Python Flask, designed to digitize and automate salon operations including appointments, billing, inventory, and customer management.

## Features

### Core Modules

- **Dashboard**: Key metrics, upcoming appointments, revenue summary
- **Customer Management**: Complete customer database with loyalty points tracking
- **Appointment System**: Schedule, reschedule, and manage appointments with calendar view
- **Staff Management**: Staff directory, schedules, and performance tracking
- **Services**: Service catalog with pricing and duration
- **Finance & Billing**: Digital invoices, payment tracking, and financial reports
- **Promotions & Marketing**: Campaign creation and tracking via WhatsApp and Email
- **Settings**: System configuration and API integrations

### Key Features

- ✅ Role-based access control (Admin, Manager, Staff)
- ✅ WhatsApp integration (placeholder for API)
- ✅ Email notifications (placeholder for SMTP)
- ✅ Loyalty points system
- ✅ Digital invoice generation (PDF)
- ✅ Financial reports (Excel export)
- ✅ Real-time dashboard analytics
- ✅ Multi-branch support ready

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download the project**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python app.py
   ```
   This will create the SQLite database and a default admin user.

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and navigate to: `http://localhost:5000`
   - Default login credentials:
     - Username: `admin`
     - Password: `admin123`

## Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root for production settings:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///salon.db
WHATSAPP_API_URL=https://api.whatsapp.com/v1/messages
WHATSAPP_API_KEY=your-whatsapp-api-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

### WhatsApp Integration

The system includes **WhatsApp Appointment Booking** feature that allows customers to book appointments directly via WhatsApp. Customers can interact with the salon's WhatsApp number (7879501625) and book appointments through a conversational flow.

#### Features:
- ✅ Step-by-step appointment booking via WhatsApp
- ✅ Automatic customer creation if not exists
- ✅ Staff and service selection through numbered options
- ✅ Date and time selection
- ✅ Appointment confirmation via WhatsApp
- ✅ Supports Hindi and English messages

#### Setup WhatsApp API:

1. **Choose a WhatsApp Business API Provider:**
   - **Twilio WhatsApp API**: https://www.twilio.com/whatsapp
   - **WhatsApp Cloud API (Meta)**: https://developers.facebook.com/docs/whatsapp
   - **Other providers**: Any service that supports webhooks

2. **Configure Webhook:**
   - Set webhook URL: `https://your-domain.com/webhook/whatsapp`
   - Verify token: `salon_verify_token` (or set `WHATSAPP_VERIFY_TOKEN` in environment)

3. **Set Environment Variables:**
   ```env
   WHATSAPP_API_URL=https://api.whatsapp.com/v1/messages
   WHATSAPP_API_KEY=your-api-key-here
   WHATSAPP_PHONE_NUMBER=7879501625
   WHATSAPP_VERIFY_TOKEN=salon_verify_token
   ```

4. **Testing Without API:**
   - The system will print messages to console if API is not configured
   - Use `/webhook/whatsapp/test` endpoint (requires login) for testing

#### How It Works:

1. Customer sends any message to salon's WhatsApp number
2. System responds with welcome message and asks for name
3. System asks questions one by one:
   - Name
   - Mobile number (if new customer)
   - Staff selection (numbered list)
   - Date (DD-MM-YYYY format)
   - Time (HH:MM format)
   - Services (can select multiple, comma-separated)
   - Notes (optional)
4. System shows summary and asks for confirmation
5. On confirmation, appointment is created and customer receives confirmation message

#### Webhook Endpoints:

- `GET/POST /webhook/whatsapp` - Main webhook for receiving WhatsApp messages
- `POST /webhook/whatsapp/test` - Test endpoint (requires login) for manual testing

### Email Integration

To enable email notifications:

1. Install Flask-Mail: `pip install flask-mail`
2. Update `utils.py` to use Flask-Mail or your preferred email service
3. Configure SMTP settings in `config.py` or environment variables

## Project Structure

```
salon/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── forms.py              # WTForms form definitions
├── utils.py              # Utility functions (PDF, Excel, messaging)
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/           # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── customers.html
│   ├── appointments.html
│   ├── staff.html
│   ├── services.html
│   ├── finance.html
│   ├── promotions.html
│   └── settings.html
└── static/              # Static files (CSS, JS, images)
```

## Usage Guide

### Adding Customers

1. Navigate to **Customers** → **Add Customer**
2. Fill in customer details (Name, Mobile are required)
3. Save to add to the database

### Creating Appointments

1. Go to **Appointments** → **New Appointment**
2. Select customer, staff member, date/time, and services
3. Save to create the appointment

### Completing Appointments

1. Find the scheduled appointment in the appointments list
2. Click **Complete**
3. Enter discount (if any) and payment method
4. System automatically generates invoice and credits loyalty points

### Managing Services

1. Go to **Services** → **Add Service**
2. Enter service name, description, price, and duration
3. Services can be selected when creating appointments

### Generating Reports

1. Navigate to **Finance**
2. Select period (Today, Week, Month, Year)
3. Click **Download Report** to export as Excel

### Creating Promotions

1. Go to **Promotions** → **Create Promotion**
2. Set discount, target audience, and validity period
3. Use **Send Campaign** to distribute via WhatsApp/Email

## Database Models

- **User**: System users with role-based access
- **Customer**: Customer information and loyalty points
- **Service**: Service catalog
- **Staff**: Staff members and their details
- **Appointment**: Booking information
- **Transaction**: Billing and payment records
- **LoyaltyHistory**: Loyalty points tracking
- **Promotion**: Marketing campaigns
- **CampaignStats**: Campaign performance metrics

## Security Notes

- Change the default admin password immediately
- Use environment variables for sensitive data in production
- Implement proper SSL/TLS for production deployment
- Regularly backup the database
- Use a production-grade database (PostgreSQL, MySQL) instead of SQLite

## Development

### Adding New Features

1. Create database models in `models.py`
2. Add forms in `forms.py` if needed
3. Create routes in `app.py`
4. Add templates in `templates/`
5. Update navigation in `base.html`

### Testing

Currently, the system uses SQLite for easy setup. For production:
- Migrate to PostgreSQL or MySQL
- Use Flask-Migrate for database migrations
- Add unit tests and integration tests

## Troubleshooting

### Database Issues
- Delete `salon.db` and restart the app to recreate the database
- Ensure write permissions in the project directory

### Import Errors
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility

### Port Already in Use
- Change the port in `app.py`: `app.run(debug=True, port=5001)`

## Future Enhancements

- [ ] Calendar view for appointments
- [ ] Inventory management module
- [ ] Advanced analytics and charts
- [ ] Multi-branch support with branch selection
- [ ] Mobile app integration
- [ ] Online payment gateway integration
- [ ] Automated reminder system
- [ ] Customer feedback system

## Support

For issues, questions, or contributions, please contact:
- Email: info@tossconsultancyservices.com
- Website: www.tossconsultancyservices.com

## License

This project is developed by Toss Solutions for salon management purposes.

---

**Version**: 1.0.0  
**Last Updated**: 2025

