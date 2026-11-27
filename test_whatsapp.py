
from whatsapp_service import send_notification

test_data = {
    "company": "JobAlert AI Test",
    "role": "AI Engineer Intern",
    "category": "Internship",
    "location": "Bengaluru",
    "stipend_or_salary": "Rs. 15,000/month",
    "duration": "3 months",
    "eligibility": "B.Tech students",
    "deadline": "Not specified",
    "skills": ["Python", "Machine Learning", "Deep Learning"],
    "summary": "This is a test notification from JobAlert AI.",
    "bullets": [
        "Test WhatsApp integration",
        "Twilio Sandbox connection",
        "JobAlert AI notification test"
    ],
    "application_link": "https://example.com/apply"
}

if __name__ == "__main__":
    message_sid = send_notification(test_data)
    print("WhatsApp test submitted successfully!")
    print("Twilio Message SID:", message_sid)
