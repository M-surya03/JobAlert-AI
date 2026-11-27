from job_detector import detect_job


def test_detects_internship():
    result = detect_job("AI Engineer Internship", "We are hiring interns.")
    assert result["is_opportunity"] is True
    assert result["category"] == "internship"


def test_rejection_is_not_new_opportunity():
    result = detect_job("Application update", "Your application was rejected.")
    assert result["is_opportunity"] is False


def test_unrelated_email():
    result = detect_job("Sale this weekend", "Get discounts on electronics.")
    assert result["is_opportunity"] is False
