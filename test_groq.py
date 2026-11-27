
from dotenv import load_dotenv
from ai_summarizer import summarize_email

load_dotenv()

test_email = {
    "sender": "careers@example.com",
    "subject": "AI Engineer Internship Opportunity",
    "body": """
    Company: ABC Technologies

    Role: AI Engineer Intern
    Location: Bangalore
    Stipend: Rs. 20,000 per month
    Duration: 6 months

    Skills: Python, Machine Learning,
    Deep Learning.

    Eligibility: B.Tech students.

    Deadline: 30 November 2026.

    Apply: https://example.com/apply
    """
}

try:
    result = summarize_email(test_email)

    print("\nSUCCESS: Groq generated a summary\n")
    print(result)

except Exception as error:
    print("\nFAILED:", repr(error))
