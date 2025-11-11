# WhatsApp Appointment Booking - उपयोग गाइड

## 📱 WhatsApp से Appointment कैसे बुक करें

### Customer के लिए (ग्राहक):

1. **WhatsApp खोलें** और salon के नंबर पर message भेजें: **7879501625**

2. **कोई भी message भेजें** (जैसे: "Hi", "Appointment", "Booking", आदि)

3. **System automatically questions पूछेगा**, आपको step-by-step जवाब देने होंगे:

   - **नाम** (Name) - अपना पूरा नाम भेजें
   - **मोबाइल नंबर** (Mobile) - 10 अंकों का नंबर (अगर नया customer है)
   - **Staff चुनें** - नंबर भेजें (जैसे: 1, 2, 3...)
   - **तारीख** (Date) - DD-MM-YYYY format में (जैसे: 15-01-2025)
   - **समय** (Time) - HH:MM format में (जैसे: 14:30 या 09:00)
   - **Services चुनें** - एक या अधिक services के लिए comma से अलग करें (जैसे: 1,2,3)
   - **Notes** (वैकल्पिक) - कोई special requirement है तो बताएं, नहीं तो "no" भेजें
   - **Confirmation** - "yes" या "हाँ" भेजें confirm करने के लिए

4. **Appointment confirm होने पर** आपको confirmation message मिलेगा appointment details के साथ!

---

## 🔧 Setup (Admin के लिए)

### Option 1: बिना API के Testing (Development)

अगर आप अभी testing करना चाहते हैं बिना WhatsApp API setup किए:

1. **App को run करें:**
   ```bash
   python app.py
   ```

2. **Console में messages दिखेंगे** जब कोई customer message भेजेगा

3. **Test करने के लिए:**
   - Browser में जाएं: `http://localhost:5000`
   - Login करें (admin/admin123)
   - Postman या curl से test endpoint को call करें:
   
   ```bash
   curl -X POST http://localhost:5000/webhook/whatsapp/test \
     -H "Content-Type: application/json" \
     -d '{"phone": "9876543210", "message": "Hi"}'
   ```

4. **Console में देखें** कि system क्या response भेज रहा है

---

### Option 2: Real WhatsApp API Setup (Production)

#### A. Twilio WhatsApp API (Recommended for beginners)

1. **Twilio Account बनाएं:**
   - https://www.twilio.com पर sign up करें
   - WhatsApp Sandbox activate करें (free trial available)

2. **Environment Variables set करें:**
   
   `.env` file बनाएं project root में:
   ```env
   WHATSAPP_API_URL=https://api.twilio.com
   WHATSAPP_API_KEY=your_account_sid:your_auth_token
   WHATSAPP_PHONE_NUMBER=7879501625
   WHATSAPP_VERIFY_TOKEN=salon_verify_token
   ```

3. **Webhook Setup:**
   - Twilio Console में जाएं
   - WhatsApp Sandbox configure करें
   - Webhook URL set करें: `https://your-domain.com/webhook/whatsapp`

---

#### B. WhatsApp Cloud API (Meta/Facebook)

1. **Meta Business Account बनाएं:**
   - https://business.facebook.com पर account बनाएं
   - WhatsApp Business API access के लिए apply करें

2. **Environment Variables:**
   ```env
   WHATSAPP_API_URL=https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages
   WHATSAPP_API_KEY=your_access_token
   WHATSAPP_PHONE_NUMBER=7879501625
   WHATSAPP_VERIFY_TOKEN=salon_verify_token
   ```

3. **Webhook Setup:**
   - Meta Developer Console में webhook configure करें
   - Callback URL: `https://your-domain.com/webhook/whatsapp`
   - Verify Token: `salon_verify_token`

---

## 📋 Step-by-Step Example Conversation

```
Customer: Hi
System: 👋 Pretty Saloon में आपका स्वागत है!
        आप WhatsApp के माध्यम से appointment बुक कर सकते हैं।
        कृपया अपना नाम बताएं:

Customer: Rajesh Kumar
System: धन्यवाद Rajesh Kumar! 🙏
        कृपया अपना मोबाइल नंबर भेजें (10 अंकों का):

Customer: 9876543210
System: मोबाइल नंबर: 9876543210 ✅
        कृपया staff member चुनें:
        1. Priya Sharma
        2. Anjali Patel
        3. Ravi Singh
        केवल नंबर भेजें (जैसे: 1)

Customer: 1
System: Staff: Priya Sharma ✅
        कृपया appointment की तारीख बताएं:
        फॉर्मेट: DD-MM-YYYY
        उदाहरण: 15-01-2025

Customer: 20-01-2025
System: तारीख: 20-01-2025 ✅
        कृपया समय बताएं:
        फॉर्मेट: HH:MM (24-hour format)
        उदाहरण: 14:30 या 09:00

Customer: 14:30
System: समय: 14:30 ✅
        कृपया services चुनें (एक या अधिक):
        1. Haircut - ₹500
        2. Hair Color - ₹2000
        3. Facial - ₹1500
        4. Manicure - ₹800
        कई services के लिए नंबर को comma से अलग करें (जैसे: 1,2,3)

Customer: 1,3
System: Services: Haircut (₹500), Facial (₹1500) ✅
        कुल राशि: ₹2000
        क्या कोई notes या विशेष आवश्यकताएं हैं? (अगर नहीं, तो 'no' या 'नहीं' भेजें):

Customer: no
System: 📋 Appointment Summary:
        👤 Customer: Rajesh Kumar
        📱 Mobile: 9876543210
        👨‍💼 Staff: Priya Sharma
        📅 Date: 20-01-2025
        ⏰ Time: 14:30
        💆 Services: Haircut, Facial
        💰 Total: ₹2000
        📝 Notes: None
        
        क्या यह सही है? 'yes' या 'हाँ' भेजें confirm करने के लिए

Customer: yes
System: ✅ Appointment Confirmed!
        आपका appointment सफलतापूर्वक बुक हो गया है!
        ...
        Appointment ID: #123
        कृपया समय पर पहुंचें। धन्यवाद! 🙏
```

---

## 🛠️ Troubleshooting

### Problem: Messages नहीं जा रहे

**Solution:**
1. Check करें कि API credentials सही हैं
2. Console में errors check करें
3. Webhook URL सही है या नहीं verify करें

### Problem: Customer को response नहीं मिल रहा

**Solution:**
1. WhatsApp API account active है या नहीं check करें
2. Phone number format सही है या नहीं (91XXXXXXXXXX)
3. API quota exhausted तो नहीं

### Problem: Conversation stuck हो गया

**Solution:**
1. Customer को "cancel" भेजने को कहें
2. Database में `whatsapp_conversations` table check करें
3. `is_active = False` set करके conversation reset करें

---

## 📞 Support

अगर कोई problem है:
- Console logs check करें
- Database में conversations देखें
- Test endpoint use करें: `/webhook/whatsapp/test`

---

## ✅ Quick Checklist

- [ ] App running है
- [ ] Database में `whatsapp_conversations` table है
- [ ] Staff और Services add किए गए हैं
- [ ] WhatsApp API configured है (अगर production में)
- [ ] Webhook URL set है (अगर production में)
- [ ] Test message भेजकर verify किया है

---

**Note:** Development/testing के लिए API setup जरूरी नहीं है। Console में messages देख सकते हैं। Production के लिए proper WhatsApp Business API setup करें।

