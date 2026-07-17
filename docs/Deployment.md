# Deployment Manual - LeadForgeAI

LeadForgeAI is designed to be fully containerized.

## Local Development Deployment

Start all services locally using Docker Compose:

```bash
# Clone the repository
git clone <repository_url>
cd LeadForgeAI

# Create your .env from template
cp .env.example .env

# Build and start services
docker-compose up --build
```

Services will start on the following ports:
- **API Entrypoint**: `http://localhost:80` (routed via Nginx proxy)
- **FastAPI Core**: `http://localhost:8000` (direct)
- **FastAPI docs**: `http://localhost:8000/docs`
- **React Client**: `http://localhost:5173` (direct)
- **MongoDB Database**: `mongodb://localhost:27017`

---

## Production Deployment Checklist

1. **MongoDB Replica Set**: Production environments should use a managed MongoDB instance (like MongoDB Atlas) or deploy MongoDB in a replica-set layout to enable ACID transactions (required by Beanie ODM).
2. **Reverse Proxy SSL**: Bind Port 443 with valid SSL certificates inside the Nginx container configurations.
3. **Environment Secrets**: Update all API credentials (`OPENROUTER_API_KEY`, `JWT_SECRET_KEY`) inside production environment files.
4. **Celery Scalability**: Scale the `celery_worker` container cluster relative to background scraping workloads.
