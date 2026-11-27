import argparse
import logging
import os
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from gmail_service import fetch_emails
from job_detector import detect_job
from ai_summarizer import summarize_email
from whatsapp_service import send_notification
from state_store import load_processed, save_processed

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("jobalert")


def run_agent(dry_run=False):
    """Fetch new Gmail messages, detect opportunities, summarize, and notify."""
    processed = load_processed()
    emails = fetch_emails()

    logger.info("Fetched %d email(s)", len(emails))
    opportunities_handled = 0
    dry_run_mode = (
        dry_run
        or os.getenv("DRY_RUN", "false").strip().lower() == "true"
    )

    for email in emails:
        message_id = email["id"]
        if message_id in processed:
            continue

        try:
            subject = email.get("subject", "")
            body = email.get("body", "")
            logger.info("Checking subject: %s", subject)

            detection = detect_job(subject, body)

            if not detection["is_opportunity"]:
                logger.info("Not a new job opportunity: %s", message_id)
                processed.add(message_id)
                save_processed(processed)
                continue

            logger.info(
                "Potential %s detected (confidence=%.2f): %s",
                detection["category"],
                detection["confidence"],
                message_id,
            )

            time.sleep(2)
            summary = summarize_email(email)

            if dry_run_mode:
                logger.info("DRY RUN summary for %s:\n%s", message_id, summary)
                # Do not mark opportunities processed during dry-run.
                opportunities_handled += 1
                continue

            # Mark processed only after the WhatsApp call succeeds.
            provider_id = send_notification(summary)
            logger.info("WhatsApp request accepted: %s", provider_id)

            processed.add(message_id)
            save_processed(processed)
            opportunities_handled += 1

        except Exception:
            logger.exception(
                "Could not process message %s; it will be retried",
                message_id,
            )

    logger.info(
        "Run complete. Opportunities handled: %d (dry_run=%s)",
        opportunities_handled,
        dry_run_mode,
    )
    return opportunities_handled


def main():
    parser = argparse.ArgumentParser(
        description="JobAlert AI email-to-WhatsApp agent"
    )
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Summarize without sending WhatsApp messages",
    )
    args = parser.parse_args()

    if args.once:
        run_agent(dry_run=args.dry_run)
        return

    interval = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))
    if interval < 1:
        raise ValueError("POLL_INTERVAL_MINUTES must be at least 1")

    scheduler = BlockingScheduler(
        timezone=os.getenv("TIMEZONE", "Asia/Kolkata")
    )
    scheduler.add_job(
        run_agent,
        "interval",
        minutes=interval,
        kwargs={"dry_run": args.dry_run},
        id="gmail-poll",
        max_instances=1,
        coalesce=True,
    )

    logger.info("Starting scheduled monitoring every %d minute(s)", interval)
    run_agent(dry_run=args.dry_run)
    scheduler.start()


if __name__ == "__main__":
    main()
