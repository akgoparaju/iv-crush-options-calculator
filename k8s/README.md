# Kubernetes Deployment Guide - Options Trading Calculator

This directory contains Kubernetes manifests for deploying the Advanced Options Trading Calculator v2.0.0 in a production environment.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │   API Service   │    │   Database      │
│   (SSL/TLS)     │────│   (3 replicas)  │────│   (PostgreSQL)  │
│   nginx         │    │   FastAPI       │    │   + Init SQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Cache         │    │   Storage       │
                       │   (Redis)       │    │   (PVC)         │
                       │   1 replica     │    │   10Gi + 2Gi    │
                       └─────────────────┘    └─────────────────┘
```

## 📦 Components

### Core Services
- **API Service**: FastAPI backend with 3 replicas for high availability
- **PostgreSQL**: Database with persistent storage and initialization scripts
- **Redis**: Cache layer for session management and performance
- **Ingress**: NGINX ingress controller with SSL/TLS termination

### Storage
- **PostgreSQL PVC**: 10Gi persistent volume for database data
- **Redis PVC**: 2Gi persistent volume for cache persistence

### Configuration
- **ConfigMaps**: Application configuration and database initialization
- **Secrets**: Sensitive data (API keys, passwords, JWT secrets)
- **Kustomization**: Environment-specific configuration management

## 🚀 Quick Deployment

### Prerequisites
- Kubernetes cluster (v1.20+)
- kubectl configured for your cluster
- NGINX Ingress Controller installed
- cert-manager installed (for SSL certificates)

### 1. Deploy All Components
```bash
# Apply all manifests at once
kubectl apply -k .

# Or apply individually
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres-init-configmap.yaml
kubectl apply -f persistent-volumes.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f ingress.yaml
```

### 2. Verify Deployment
```bash
# Check all resources in the namespace
kubectl get all -n options-trading

# Check persistent volumes
kubectl get pvc -n options-trading

# Check ingress
kubectl get ingress -n options-trading

# View logs
kubectl logs -f deployment/api-deployment -n options-trading
```

## 🔧 Configuration

### 1. Update Secrets
Before deploying, update the secrets in `secrets.yaml`:

```bash
# Generate base64 encoded secrets
echo -n "your-postgres-password" | base64
echo -n "your-jwt-secret-key" | base64
echo -n "your-alpha-vantage-api-key" | base64
```

Update the values in `secrets.yaml` with your actual base64-encoded secrets.

### 2. Configure Ingress
Update the hostnames in `ingress.yaml`:
```yaml
rules:
- host: api.yourdomain.com    # Update with your API domain
- host: app.yourdomain.com    # Update with your frontend domain
```

### 3. Environment Variables
Modify `configmap.yaml` to adjust application settings:
- Database configuration
- Redis settings
- Application parameters
- Feature flags

## 📊 Monitoring & Health Checks

### Health Endpoints
- **API Health**: `GET /api/health`
- **Database Health**: Automatic via PostgreSQL `pg_isready`
- **Redis Health**: Automatic via `redis-cli ping`

### Resource Monitoring
```bash
# Monitor resource usage
kubectl top pods -n options-trading
kubectl top nodes

# Check resource quotas
kubectl describe quota -n options-trading
```

### Logs
```bash
# API logs
kubectl logs -f deployment/api-deployment -n options-trading

# Database logs
kubectl logs -f deployment/postgres-deployment -n options-trading

# Redis logs
kubectl logs -f deployment/redis-deployment -n options-trading
```

## 🔒 Security Configuration

### 1. Network Policies (Optional)
```yaml
# Example network policy - create as needed
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: options-trading
spec:
  podSelector:
    matchLabels:
      app: options-trading-api
  policyTypes:
  - Ingress
  - Egress
```

### 2. Pod Security Standards
The manifests include security best practices:
- Non-root user execution
- Resource limits and requests
- Liveness and readiness probes
- Secure secret management

### 3. SSL/TLS Configuration
SSL certificates are managed by cert-manager with Let's Encrypt:
- Automatic certificate provisioning
- Certificate renewal
- Secure HTTPS endpoints

## 🔄 Scaling & Updates

### Horizontal Scaling
```bash
# Scale API replicas
kubectl scale deployment api-deployment --replicas=5 -n options-trading

# Auto-scaling (HPA)
kubectl autoscale deployment api-deployment --cpu-percent=70 --min=3 --max=10 -n options-trading
```

### Rolling Updates
```bash
# Update API image
kubectl set image deployment/api-deployment api=options-trading-api:2.1.0 -n options-trading

# Check rollout status
kubectl rollout status deployment/api-deployment -n options-trading

# Rollback if needed
kubectl rollout undo deployment/api-deployment -n options-trading
```

## 💾 Backup & Recovery

### Database Backups
```bash
# Create backup
kubectl exec -n options-trading deployment/postgres-deployment -- pg_dump -U postgres options_trading > backup.sql

# Restore from backup
kubectl exec -i -n options-trading deployment/postgres-deployment -- psql -U postgres -d options_trading < backup.sql
```

### Persistent Volume Snapshots
Configure volume snapshots based on your storage provider's capabilities.

## 🐛 Troubleshooting

### Common Issues

#### 1. Pod Startup Issues
```bash
# Check pod status
kubectl describe pod <pod-name> -n options-trading

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp -n options-trading
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it deployment/postgres-deployment -n options-trading -- psql -U postgres -d options_trading -c "SELECT 1;"

# Check database logs
kubectl logs deployment/postgres-deployment -n options-trading
```

#### 3. Service Discovery Issues
```bash
# Check service endpoints
kubectl get endpoints -n options-trading

# Test service connectivity
kubectl exec -it deployment/api-deployment -n options-trading -- nslookup postgres-service
```

### Resource Issues
```bash
# Check resource limits
kubectl describe nodes

# Check pod resource usage
kubectl top pods -n options-trading --sort-by=memory
```

## 📝 Development vs Production

### Development Environment
- Single replicas
- Smaller resource requests
- Local storage classes
- Self-signed certificates

### Production Environment
- Multiple replicas (3+ for API)
- Proper resource limits
- High-performance storage
- Valid SSL certificates
- Monitoring and alerting
- Backup strategies

## 🔗 External Dependencies

### Required External Services
- **DNS**: Configure DNS records for your ingress hostnames
- **Certificate Authority**: Let's Encrypt for SSL certificates
- **Storage**: Persistent storage provider (AWS EBS, GCE PD, etc.)
- **Load Balancer**: Cloud provider load balancer for ingress

### Optional Integrations
- **Monitoring**: Prometheus/Grafana
- **Logging**: ELK/EFK stack
- **Secrets Management**: HashiCorp Vault, AWS Secrets Manager
- **CI/CD**: GitLab CI/CD, GitHub Actions, Jenkins

## 📞 Support

For deployment issues or questions:
1. Check the application logs
2. Verify configuration in ConfigMaps and Secrets
3. Ensure external dependencies are available
4. Review Kubernetes cluster health

## 🏷️ Version Information

- **Application Version**: 2.0.0
- **Kubernetes Version**: 1.20+
- **API Version**: v1
- **Database Version**: PostgreSQL 15
- **Cache Version**: Redis 7