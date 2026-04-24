# RiskShield Deployment Guide

## Prerequisites

- Docker & Docker Compose (for local/staging)
- Kubernetes cluster (for production)
- kubectl CLI configured
- Domain name and SSL certificates

## Quick Start (Docker Compose)

### 1. Generate JWT Secret

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Create .env file

```bash
cp .env.example .env
# Edit .env and set JWT_SECRET
```

### 3. Build and Run

```bash
cd deploy
docker-compose up -d
```

### 4. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### 5. Check Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 6. Stop Services

```bash
docker-compose down
```

## Production Deployment (Kubernetes)

### 1. Create Namespace

```bash
kubectl apply -f k8s-namespace.yaml
```

### 2. Configure Secrets

Edit `k8s-secrets.yaml` with your actual values:
- Generate secure JWT secret
- Set MongoDB connection string

```bash
kubectl apply -f k8s-secrets.yaml
```

### 3. Deploy MongoDB

```bash
kubectl apply -f k8s-mongodb.yaml
```

### 4. Build Docker Images

```bash
# Backend
docker build -f Dockerfile.backend -t riskshield-backend:latest ../

# Frontend
docker build -f Dockerfile.frontend -t riskshield-frontend:latest ../

# Push to your registry
docker tag riskshield-backend:latest your-registry/riskshield-backend:latest
docker push your-registry/riskshield-backend:latest

docker tag riskshield-frontend:latest your-registry/riskshield-frontend:latest
docker push your-registry/riskshield-frontend:latest
```

### 5. Deploy Backend

```bash
kubectl apply -f k8s-backend.yaml
```

### 6. Deploy Frontend

```bash
kubectl apply -f k8s-frontend.yaml
```

### 7. Verify Deployment

```bash
kubectl get pods -n riskshield
kubectl get services -n riskshield
```

### 8. Access Application

```bash
# Get LoadBalancer IP
kubectl get svc riskshield-frontend -n riskshield
```

## Configuration

### Environment Variables

**Backend:**
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `JWT_SECRET`: Secret key for JWT tokens (REQUIRED)
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
- `ENVIRONMENT`: Environment name (development/production)

**Frontend:**
- `REACT_APP_BACKEND_URL`: Backend API URL

### Security Checklist

- [ ] Set strong JWT_SECRET (minimum 32 characters)
- [ ] Configure proper CORS_ORIGINS (not *)
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Configure MongoDB authentication
- [ ] Set resource limits in K8s
- [ ] Enable network policies
- [ ] Set up monitoring and logging

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8001/api/

# Frontend health
curl http://localhost:3000/health
```

### Logs

```bash
# Kubernetes
kubectl logs -f deployment/riskshield-backend -n riskshield
kubectl logs -f deployment/riskshield-frontend -n riskshield

# Docker Compose
docker-compose logs -f
```

## Backup and Recovery

### MongoDB Backup

```bash
# Docker Compose
docker-compose exec mongo mongodump --out /backup

# Kubernetes
kubectl exec -it mongodb-pod -n riskshield -- mongodump --out /backup
```

### Restore

```bash
# Docker Compose
docker-compose exec mongo mongorestore /backup

# Kubernetes
kubectl exec -it mongodb-pod -n riskshield -- mongorestore /backup
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend
kubectl scale deployment riskshield-backend --replicas=5 -n riskshield

# Scale frontend
kubectl scale deployment riskshield-frontend --replicas=3 -n riskshield
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
kubectl logs deployment/riskshield-backend -n riskshield

# Common issues:
# 1. JWT_SECRET not set
# 2. MongoDB connection failed
# 3. Port already in use
```

### Frontend can't connect to backend

```bash
# Check REACT_APP_BACKEND_URL is correct
# Check CORS_ORIGINS includes frontend domain
# Check backend is accessible
curl http://backend-url/api/
```

### Database connection issues

```bash
# Check MongoDB is running
kubectl get pods -n riskshield | grep mongo

# Test connection
kubectl exec -it mongodb-pod -n riskshield -- mongo
```

## Support

For issues and support:
1. Check logs first
2. Review deployment readiness report
3. Consult architecture documentation
4. Contact platform team
