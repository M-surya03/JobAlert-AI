import re

INTERNSHIP_TERMS = (
    "internship", "intern", "summer intern", "winter intern",
    "graduate intern", "machine learning intern", "ai intern",
    "ml intern", "software engineering intern", "data science intern",
)

JOB_TERMS = (
    "job opening", "job opportunity", "full-time", "full time",
    "part-time", "part time", "permanent role",
    "staff software engineer", "software engineer", "software developer",
    "senior engineer", "junior engineer", "data scientist",
    "machine learning engineer", "ai engineer", "content writer",
    "technical writer", "business analyst", "data analyst",
    "product manager", "developer", "hiring", "vacancy",
    "recruitment", "career opportunity",
)

EXCLUDE_TERMS = (
    "application received", "application has been received",
    "application submitted successfully", "application status",
    "application update", "your application", "otp",
    "one time password", "verification code", "login code",
    "interview scheduled", "interview invitation", "not selected",
    "application rejected", "position has been filled",
)

QUOTED_BOUNDARIES = (
    r"^\s*[-_]{2,}\s*forwarded message\s*[-_]{2,}\s*$",
    r"^\s*begin forwarded message\s*:\s*$",
    r"^\s*on .{5,200}wrote:\s*$",
    r"^\s*from:\s+.+$",
)


def _normalize(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _contains_term(text, term):
    pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _has_any(text, terms):
    return any(_contains_term(text, term) for term in terms)


def _remove_quoted_content(body):
    lines = str(body or "").splitlines()
    kept = []
    for line in lines:
        if any(re.search(p, line, flags=re.IGNORECASE) for p in QUOTED_BOUNDARIES):
            break
        kept.append(line)
    return _normalize("\n".join(kept))


def _result(is_opportunity, category="other", confidence=0.0):
    return {
        "is_opportunity": is_opportunity,
        "category": category,
        "confidence": confidence,
    }


def detect_job(subject, body):
    """Detect job alerts using subject-first rules and a trimmed email body."""
    subject_text = _normalize(subject)
    body_text = _remove_quoted_content(body)

    if _has_any(subject_text, EXCLUDE_TERMS):
        return _result(False)

    # Explicit subject terms take priority over unrelated body text.
    if _has_any(subject_text, INTERNSHIP_TERMS):
        return _result(True, "internship", 0.95)

    if _has_any(subject_text, JOB_TERMS):
        return _result(True, "job", 0.90)

    # Check only the opening, unquoted portion for status notifications.
    if _has_any(body_text[:1200], EXCLUDE_TERMS):
        return _result(False)

    has_internship = _has_any(body_text, INTERNSHIP_TERMS)
    has_job = _has_any(body_text, JOB_TERMS)

    # A concrete job title takes precedence over incidental internship text.
    if has_job and has_internship:
        return _result(True, "job", 0.75)
    if has_internship:
        return _result(True, "internship", 0.80)
    if has_job:
        return _result(True, "job", 0.75)

    return _result(False)
