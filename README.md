# User_Service
Service to handdel, vloge avtentikacijem  

## Deployment

### Prerequisites

This service uses GitHub Actions to automatically deploy to Azure Kubernetes Service (AKS) on every push to the `main` branch.

### Required GitHub Secrets

Configure the following secrets in your GitHub repository settings (`Settings` → `Secrets and variables` → `Actions`):

- `AZURE_CLIENT_ID` - Azure AD application (service principal) client ID for OIDC authentication
- `AZURE_TENANT_ID` - Azure AD tenant ID
- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID

**Note:** These credentials use OIDC (OpenID Connect) authentication. No client secret is required.

### Automatic Deployment

Push to the `main` branch triggers:
1. Docker image build and push to `courtmateacr.azurecr.io/user-service:<commit-sha>`
2. Helm deployment to AKS cluster `testCluster` in namespace `myapp`
3. Ingress configuration for path `/api/users`

### Manual Deployment

If you need to deploy manually:

```bash
# Login to Azure
az login

# Login to ACR
az acr login --name courtmateacr

# Build and push image (use --platform for cross-platform builds)
IMAGE_TAG=$(git rev-parse HEAD)
docker buildx build --platform linux/amd64 \
  -t courtmateacr.azurecr.io/user-service:${IMAGE_TAG} \
  --push .

# Set AKS context
az aks get-credentials --resource-group RSO --name testCluster

# Create namespace if needed
kubectl create namespace myapp --dry-run=client -o yaml | kubectl apply -f -

# Deploy with Helm
helm upgrade --install user-service chart/user-service \
  --namespace myapp \
  --set image.repository=courtmateacr.azurecr.io/user-service \
  --set image.tag=${IMAGE_TAG} \
  --wait

# Check deployment status
kubectl rollout status deployment/user-service -n myapp
```

### Ingress Configuration

The service is exposed via Ingress at path `/api/users`.

**To change the ingress path:**
Edit `chart/user-service/values.yaml`:
```yaml
ingress:
  path: /api/users  # Change this to your desired path
```

**To add a custom domain:**
Edit `chart/user-service/values.yaml`:
```yaml
ingress:
  host: "api.yourdomain.com"  # Add your domain here
```

**To add ingress annotations** (e.g., for URL rewriting):
```yaml
ingress:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
```

**Note:** An nginx ingress controller must be installed in your AKS cluster for the Ingress resource to work. Without it, the Ingress won't get an external address.

### Checking Deployment

```bash
# Check pod status
kubectl get pods -n myapp -l app.kubernetes.io/name=user-service

# Check service
kubectl get svc -n myapp user-service

# Check ingress
kubectl get ingress -n myapp user-service

# View logs
kubectl logs -n myapp -l app.kubernetes.io/name=user-service --tail=100

# Test health endpoint
kubectl port-forward -n myapp svc/user-service 8080:80
curl http://localhost:8080/health
```

