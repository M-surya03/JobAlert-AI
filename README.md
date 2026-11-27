# JobAlert AI — Simple Gmail-to-WhatsApp Agent

A small Python application that checks Gmail, detects likely job/internship emails,
asks an LLM to extract a concise summary, and sends it to a WhatsApp number.
It has **no database**. Processed Gmail message IDs are stored in a local JSON file.

## 1. Requirements

- Windows 10/11, macOS, or Linux
- Python 3.11
- A Gmail account and Google Cloud project
- An LLM API key (Groq recommended for this example), or a local Ollama server
- Twilio WhatsApp Sandbox for testing, or a configured production WhatsApp sender

## 2. Create a Google OAuth client

1. Open https://console.cloud.google.com/.
2. Create/select a Google Cloud project.
3. Enable **Gmail API**.
4. Configure the OAuth consent screen and add your Google account as a test user if the app is in Testing.
5. Create an OAuth Client ID of type **Desktop app**.
6. Download the JSON file.
7. Create `credentials/` in the project root and save the file as
   `credentials/credentials.json`.
8. The first run opens a browser for consent. A refreshable token is saved as
   `credentials/token.json`. Never commit either credentials file.

The app requests only `gmail.readonly`. Google OAuth testing-mode refresh tokens may
expire after a limited period; follow Google's current OAuth verification and publishing
requirements for long-running use.

## 3. Configure an LLM

Copy `.env.example` to `.env`.

For Groq:
1. Create an API key at https://console.groq.com/.
2. Set `LLM_PROVIDER=groq`.
3. Put the key in `GROQ_API_KEY`.
4. Set `LLM_MODEL` to a model currently available to your Groq account and compatible
   with JSON response formatting.

Alternative:
- OpenAI: set `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, and a supported `LLM_MODEL`.
- Ollama: run Ollama locally, pull a model that supports the OpenAI-compatible chat API,
  set `LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL`, and `LLM_MODEL`. Local inference avoids
  sending email content to a hosted LLM provider, but requires local compute.

## 4. Configure WhatsApp with Twilio

For a first test:
1. Create a Twilio account at https://www.twilio.com/.
2. Open the WhatsApp Sandbox in the Twilio Console.
3. Follow the displayed instructions to join the sandbox from your WhatsApp account.
4. Copy the Account SID and Auth Token into `.env`.
5. Set `WHATSAPP_FROM` to the sandbox sender shown by Twilio (commonly
   `whatsapp:+14155238886`) and `WHATSAPP_TO` to your joined number in E.164 format
   prefixed with `whatsapp:`, e.g. `whatsapp:+91...`.

For production, configure an approved WhatsApp sender and comply with Meta's opt-in,
template and business messaging rules. A Twilio API acceptance response is not proof
that the recipient received the message.

## 5. Install on Windows

Open PowerShell in the project folder:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your real values. Keep `DRY_RUN=true` initially.

## 6. First run: safe dry run

```powershell
python main.py --once --dry-run
```

The first run should open the Google OAuth consent flow. Sign in and grant read-only
Gmail access. The agent fetches messages matching `GMAIL_QUERY` (default `newer_than:2d`),
detects likely opportunities, and prints the generated summaries without sending WhatsApp.

If no emails are found, send a test email to yourself with a subject such as
"AI Engineer Internship" and a body containing role, company, stipend, duration,
eligibility, deadline and an application URL. Then run again.

## 7. Send a WhatsApp test

1. Confirm your Twilio Sandbox is joined and `.env` has valid Twilio credentials.
2. Change `DRY_RUN=false`.
3. Run:

```powershell
python main.py --once
```

Check the Twilio message log for its status/SID. Start with a test email you control.
Do not assume an API acceptance response means delivery.

## 8. Continuous monitoring

```powershell
python main.py
```

The agent runs once immediately and then polls at `POLL_INTERVAL_MINUTES` (default 5).
Stop with Ctrl+C.

Gmail query examples:
- `newer_than:1d`
- `newer_than:7d`
- `is:unread newer_than:2d`

The local JSON file `processed_emails.json` prevents the same Gmail message ID from
being handled again. It is state, not a database. Back it up and do not delete it
unless you intentionally want previously seen messages to be eligible again.

## 9. Tests

Install dependencies, then run:

```powershell
pytest -v
```

Tests cover the keyword detector, JSON state storage and WhatsApp message formatting.
They do not call Gmail, an LLM provider or Twilio. Use `--dry-run` for a live Gmail/LLM
integration check without sending a WhatsApp message.

## 10. Docker (optional)

Docker mode requires OAuth to be completed on a machine where the browser consent flow
can run, or the token file to be securely provisioned to the container.

1. Complete OAuth locally once and confirm `credentials/token.json` exists.
2. Keep `credentials/credentials.json` and `credentials/token.json` out of source control.
3. Ensure `.env` exists and `DRY_RUN=true` for the first container run.
4. Build and start:

```powershell
docker compose up --build -d
docker compose logs -f jobalert
```

5. Stop:

```powershell
docker compose down
```

The compose file mounts credentials and JSON state from the host. Protect those host
directories. For containerized OAuth, a headless server cannot open a local browser;
provision the token securely or implement a separate OAuth callback flow.

## 11. Troubleshooting

- `credentials.json not found`: check the file path and filename.
- `Access blocked` / OAuth errors: check consent-screen test users, enabled Gmail API,
  OAuth client type (Desktop app), and current Google OAuth policies.
- `invalid_grant`: re-authenticate and review OAuth consent/publishing status.
- LLM model error: use a model name currently available to your provider; check JSON
  mode support.
- Twilio 63007 / sender errors: check the WhatsApp sender and sandbox enrollment.
- No messages found: broaden `GMAIL_QUERY` and send yourself a test message.
- Duplicate alert after a timeout: the provider may have accepted the send even if the
  client did not receive its response. Check Twilio logs before retrying.

## 12. Important limitations and security

- The detector is a simple keyword filter. It can miss unusual wording and may flag
  interview/rejection messages. Improve it with a labeled test set before relying on it.
- Email text is untrusted input. The summarizer prompt instructs the model to ignore
  embedded instructions, but an LLM is not a security boundary. Do not let this agent
  click links, open attachments, apply for jobs or disclose personal information.
- Email bodies are sent to the configured LLM provider. Review that provider's privacy,
  retention and data-processing terms. Use Ollama for local processing if appropriate.
- Protect `.env`, OAuth files and state JSON. Use a secrets manager and encrypted disk
  for a deployed service.
- WhatsApp business-initiated messages may require opt-in and approved templates.
- This simple single-process version is for personal use/small workloads. It does not
  provide transactional exactly-once message delivery or multi-worker coordination.
