# DEPLOYMENT.md - AI Agent SaaS Platform

## Prerequisites

- Docker & Docker Compose installed
- Server with ports 80/443 available
- Domain name (optional for local)

## Local Docker Test

```bash
cd /Users/jarvis/.openclaw/workspace/agents/fullstack-dev/projects/ai-agent-saas

# Build and run
docker-compose up --build

# Test
curl http://localhost:8000/health
```

## Production Deployment

### 1. Clone and setup on server
```bash
git clone <repo> /opt/ai-agent-saas
cd /opt/ai-agent-saas
```

### 2. Create data directory
```bash
mkdir -p data
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with production values
```

### 4. Deploy
```bash
docker-compose up -d --build
```

### 5. Setup reverse proxy (Caddy/Nginx) for SSL

Example Caddyfile:
```
yourdomain.com {
    reverse_proxy localhost:8000
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FERNET_KEY` | Encryption key | Yes |
| `ADMIN_API_KEY` | Admin access | Yes |
| `STRIPE_SECRET_KEY` | Payments | For billing |
| `OPENCLAW_API_URL` | LLM endpoint | Yes |

## Updating

```bash
cd /opt/ai-agent-saas
git pull
docker-compose up -d --build
```

## Troubleshooting

- Check logs: `docker-compose logs -f`
- Database: `sqlite3 data/ai_agent_saas.db`
- Restart: `docker-compose restart`
