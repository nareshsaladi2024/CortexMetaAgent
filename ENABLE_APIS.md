# Enabling Required Google Cloud APIs

This guide lists all required Google Cloud APIs for the CortexMetaAgent project and how to enable them.

## Required APIs



### 2. Vertex AI API
**Required for:** Agent deployment and Reasoning Engine

**Enable:**
```powershell
gcloud services enable aiplatform.googleapis.com --project=aiagent-capstoneproject
```

### 3. Cloud Run API
**Required for:** Deploying MCP servers to Cloud Run

**Enable:**
```powershell
gcloud services enable run.googleapis.com --project=aiagent-capstoneproject
```

### 4. Cloud Build API
**Required for:** Building Docker images for Cloud Run

**Enable:**
```powershell
gcloud services enable cloudbuild.googleapis.com --project=aiagent-capstoneproject
```

### 5. Artifact Registry API
**Required for:** Storing Docker images

**Enable:**
```powershell
gcloud services enable artifactregistry.googleapis.com --project=aiagent-capstoneproject
```

## Enable All APIs at Once

```powershell
gcloud services enable `

  aiplatform.googleapis.com `
  run.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  --project=aiagent-capstoneproject
```

## Verify APIs Are Enabled

```powershell
gcloud services list --enabled --project=aiagent-capstoneproject --filter="name:(aiplatform.googleapis.com OR run.googleapis.com OR cloudbuild.googleapis.com OR artifactregistry.googleapis.com)"
```

## Common Errors



### Error: "SERVICE_DISABLED"

**Solution:**
- Enable the specific API mentioned in the error message
- Check that billing is enabled for your project
- Verify you have the necessary permissions

## API Propagation Time

After enabling an API, it may take 2-5 minutes for the change to propagate across Google Cloud systems. If you get an error immediately after enabling, wait a few minutes and retry.

## Check API Status

To check if an API is enabled:

```powershell
gcloud services list --enabled --project=aiagent-capstoneproject --filter="name:aiplatform.googleapis.com"
```

If the API is enabled, you'll see it in the list. If not, enable it using the commands above.

