# lex-pdftotext Docker Deployment

Docker deployment for the lex-pdftotext PDF extraction service.

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Architecture

```
                    ┌─────────────────┐
                    │   API Server    │
                    │  (FastAPI)      │
                    │   Port: 8000    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Redis       │
                    │  (Job Queue)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │  Worker 1 │  │  Worker 2 │  │  Worker N │
        │   (RQ)    │  │   (RQ)    │  │   (RQ)    │
        └───────────┘  └───────────┘  └───────────┘
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/extract` | Extract text from PDF |
| POST | `/batch` | Batch extract multiple PDFs |
| POST | `/tables` | Extract tables from PDF |
| POST | `/merge` | Merge PDFs by process |
| POST | `/info` | Get PDF information |
| GET | `/jobs/{job_id}` | Get job status |
| GET | `/jobs/{job_id}/result` | Get job result |
| DELETE | `/jobs/{job_id}` | Delete job |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | `8000` | API server port |
| `MAX_UPLOAD_SIZE` | `52428800` | Max upload size (50MB) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `WORKER_REPLICAS` | `2` | Number of workers |
| `STORAGE_TYPE` | `local` | Storage backend (local/s3) |
| `S3_BUCKET` | - | S3 bucket name |
| `S3_ACCESS_KEY` | - | S3 access key |
| `S3_SECRET_KEY` | - | S3 secret key |
| `S3_ENDPOINT` | - | S3 endpoint (MinIO) |
| `S3_REGION` | `us-east-1` | S3 region |

## Usage Examples

### Extract single PDF

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@documento.pdf" \
  -F "format=markdown"
```

### Extract with RAG chunking

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@documento.pdf" \
  -F "chunk_for_rag=true" \
  -F "chunk_size=1000"
```

### Check job status

```bash
curl http://localhost:8000/jobs/{job_id}
```

### Get result

```bash
curl http://localhost:8000/jobs/{job_id}/result
```

## Production Deployment

```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker-compose up -d --scale worker=4
```

## Storage Options

### Local Storage (default)

Files are stored in Docker volumes:
- `lex-pdftotext-uploads`: Uploaded PDFs
- `lex-pdftotext-outputs`: Processed results

### S3 Storage

Configure S3 in `.env`:

```env
STORAGE_TYPE=s3
S3_BUCKET=my-bucket
S3_ACCESS_KEY=xxxxx
S3_SECRET_KEY=xxxxx
S3_REGION=us-east-1
```

For MinIO or S3-compatible:

```env
S3_ENDPOINT=http://minio:9000
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "redis": "healthy",
  "workers": 2
}
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

## Troubleshooting

### Worker not processing jobs

1. Check Redis connection:
   ```bash
   docker-compose exec redis redis-cli ping
   ```

2. Check worker logs:
   ```bash
   docker-compose logs worker
   ```

### API returning 500 errors

1. Check API logs:
   ```bash
   docker-compose logs api
   ```

2. Verify Redis is healthy:
   ```bash
   docker-compose ps redis
   ```

### Out of memory

Increase memory limits in `docker-compose.prod.yml` or reduce `WORKER_REPLICAS`.
