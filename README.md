# Grok ITSD Voicebot Starter

This repository contains a starter implementation for an **IT Service Desk (ITSD) voicebot** that uses the **Grok Voice Agent API** over WebSocket and a relational database for both:

- IT troubleshooting knowledge retrieval
- Ticket lifecycle operations (create, status, update)

## What this starter includes

- **Realtime Grok Voice websocket agent** (`src/grokvoicebot/grok_voice_agent.py`)
  - Connects to `wss://api.x.ai/v1/realtime`
  - Registers tools the model can call:
    - `search_knowledge`
    - `create_ticket`
    - `get_ticket_status`
    - `update_ticket`
  - Executes tool calls against the database and returns results to Grok.

- **Database models & service layer**
  - `KnowledgeArticle`
  - `Ticket`
  - `TicketUpdate`
  - SQLAlchemy-backed service functions for query/create/update flows.

- **FastAPI service** (`src/grokvoicebot/api.py`)
  - Adds REST endpoints for integration testing and non-voice channels.

## Architecture

```text
Caller (voice)
   -> Telephony/Web client (optional)
      -> Grok Voice Realtime WebSocket (wss://api.x.ai/v1/realtime)
         -> Tool calls
            -> Python tool handler
               -> SQL database (knowledge + tickets)
```

## Quick start

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```


> If `pip install -e .` fails in restricted environments, try:
> ```bash
> pip install --no-build-isolation -e .
> ```
> or:
> ```bash
> pip install -r requirements.txt
> pip install --no-build-isolation -e .
> ```

### 2) Set environment variables

```bash
export GROK_API_KEY="your_api_key"
export GROK_MODEL="grok-voice"
# Optional: defaults to sqlite:///./itsd.db
export DATABASE_URL="sqlite:///./itsd.db"
```

### 3) Initialize and seed DB

```bash
python -m grokvoicebot
```

### 4) Run API service

```bash
uvicorn grokvoicebot.api:app --host 0.0.0.0 --port 8000 --reload
```



### 4.1) Open the test web UI

Open:

```
http://localhost:8000/
```

The page now runs a **webpage-based voicebot** flow:
- browser microphone input (SpeechRecognition)
- assistant endpoint `/assistant/respond` for conversational ticket/knowledge actions
- browser text-to-speech playback for bot responses
- direct endpoint testing tools for troubleshooting

### 5) Run voice agent

```bash
python -m grokvoicebot.grok_voice_agent
```

## Core voicebot capabilities

1. **Knowledge retrieval**
   - User asks troubleshooting question.
   - Model calls `search_knowledge`.
   - Voicebot returns top matches.

2. **Create ticket**
   - Collects requester name, email, issue details, priority.
   - Model calls `create_ticket`.
   - Bot confirms generated ticket ID.

3. **Ticket status**
   - User asks for status by ticket ID.
   - Model calls `get_ticket_status`.
   - Bot reads current status and timestamp.

4. **Ticket update**
   - User requests update (e.g., mark in_progress/resolved + note).
   - Model calls `update_ticket`.
   - Bot confirms updated state.


## So what do I do now? (Practical rollout plan)

If your goal is to move from prototype to a working ITSD voicebot quickly, follow this order:

1. **Stand up local backend first (no voice yet)**
   - Create env + install deps:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     pip install -e .
     ```
   - Copy env file and add your API key:
     ```bash
     cp .env.example .env
     # edit .env and set GROK_API_KEY
     ```
   - Initialize DB:
     ```bash
     python -m grokvoicebot
     ```
   - Start API:
     ```bash
     uvicorn grokvoicebot.api:app --host 0.0.0.0 --port 8000
     ```

2. **Validate ticket and knowledge flows via REST**
   - Health check:
     ```bash
     curl http://localhost:8000/health
     ```
   - Search knowledge:
     ```bash
     curl -X POST http://localhost:8000/knowledge/search \
       -H "Content-Type: application/json" \
       -d '{"query":"vpn"}'
     ```
   - Create ticket:
     ```bash
     curl -X POST http://localhost:8000/tickets \
       -H "Content-Type: application/json" \
       -d '{"requester_name":"Jane Doe","requester_email":"jane@example.com","title":"VPN issue","description":"Unable to connect","priority":"high"}'
     ```

3. **Run voice agent with Grok realtime websocket**
   - In a second terminal:
     ```bash
     source .venv/bin/activate
     python -m grokvoicebot.grok_voice_agent
     ```
   - Confirm logs show websocket connection and tool call handling.

4. **Integrate your channel**
   - Connect Twilio/SIP/web client audio stream to the Grok voice session.
   - Keep this service as the tool backend for ticket/knowledge actions.

5. **Go-live hardening (minimum)**
   - Move DB to PostgreSQL.
   - Add auth + per-user access control for tickets.
   - Add audit logging + PII redaction.
   - Add monitoring/alerts on websocket disconnects and tool errors.

### Suggested 2-week implementation sequence

- **Days 1–2:** finalize DB schema + IT knowledge ingestion
- **Days 3–4:** enforce ticket workflow states (`open`, `in_progress`, `resolved`)
- **Days 5–6:** channel integration (Twilio/web app)
- **Days 7–8:** authentication and RBAC
- **Days 9–10:** QA with scripted call scenarios and load tests

## Production hardening recommendations

- Replace SQLite with PostgreSQL.
- Add authentication/authorization for ticket access.
- Add PII redaction and audit logging.
- Add observability (OpenTelemetry traces, structured logs).
- Add SSO identity lookup and CMDB integration.
- Use a message queue for async follow-up actions.
