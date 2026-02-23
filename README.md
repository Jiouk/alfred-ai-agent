# AI Agent SaaS Platform

Zero-dashboard AI agent configuration via conversation.

## Quick Start

1. Copy `.env.example` to `.env` and fill in values
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`
4. API docs: http://localhost:8000/docs

## Auth for client-scoped endpoints

Endpoints under `/credits/*` now require:
- `X-Client-Id`: numeric client id
- `X-Client-Token`: required only when `CLIENT_AUTH_TOKEN` is set in env

## Architecture

- **FastAPI** - Async web framework
- **SQLModel** - Database ORM with SQLite
- **Pyrogram** - Telegram bot integration
- **Twilio** - VoIP & SMS
- **Mailgun** - Email
- **Stripe** - Billing & credits

## Project Structure

```
app/
├── models.py          # Database models (SQLModel)
├── config.py          # Configuration & settings
├── core/              # Core business logic
│   ├── bot_pool.py    # BotPoolManager
│   ├── agent_engine.py # AgentEngine + Runtimes
│   ├── router.py      # ConversationRouter
│   ├── setup.py       # SetupOrchestrator
│   ├── integrations/  # Integration classes
│   └── compiler.py    # SystemPromptCompiler
├── routers/           # API endpoints
│   ├── onboarding.py
│   ├── webhooks.py
│   ├── admin.py
│   └── billing.py
└── services/          # External service clients
    ├── telegram.py
    ├── stripe.py
    └── twilio.py
tests/                 # Test suite
docs/                  # Documentation
```

## Build Order

1. ✅ FastAPI project structure + DB models
2. ⏳ BotPoolManager
3. ⏳ AgentEngine + BaseRuntime + OpenClawRuntime
4. ⏳ SystemPromptCompiler
5. ⏳ CreditManager
6. ⏳ ConversationRouter + Intent Classifier
7. ⏳ SetupOrchestrator + Flows
8. ⏳ IntegrationRegistry
9. ⏳ Onboarding endpoint
10. ⏳ Webhook handlers
11. ⏳ Stripe billing
12. ⏳ Admin endpoints
