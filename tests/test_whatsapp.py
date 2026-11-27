from whatsapp_service import format_notification


def test_message_contains_role_and_link():
    text = format_notification({
        "company": "Example Co",
        "role": "AI Intern",
        "application_link": "https://example.com/apply",
        "skills": ["Python"],
        "summary": "Example Co is hiring an AI intern.",
    })
    assert "AI Intern" in text
    assert "https://example.com/apply" in text
