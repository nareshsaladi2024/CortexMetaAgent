# Docker Deployment Guide for CortexMetaAgent

This guide explains how to build and run CortexMetaAgent agents using Docker.

## Overview

CortexMetaAgent consists of 5 agents:
- **CortexMetaAgent**: Main meta agent
- **AutoEvalAgent**: Automated evaluation agent
- **MetricsAgent**: Metrics collection agent
- **ReasoningCostAgent**: Reasoning cost analysis agent
- **TokenCostAgent**: Token cost analysis agent

## Prerequisites

1. **Docker Desktop** installed and running
2. **.env file** configured in project root (copied from Day1a)
3. **Service account JSON** file (if using Vertex AI)

## Quick Start

### Build and Start All Agents

```bash
cd C:\Capstone\CortexMetaAgent
docker-compose up --build
```

### Run in Detached Mode

```bash
docker-compose up -d --build
```

## Services

All agents share the same base image (`cortex-meta-agent:latest`) but run as separate containers:

1. **cortex-meta-agent** - Main meta agent
2. **cortex-auto-eval-agent** - AutoEvalAgent
3. **cortex-metrics-agent** - MetricsAgent
4. **cortex-reasoning-cost-agent** - ReasoningCostAgent
5. **cortex-token-cost-agent** - TokenCostAgent

## Environment Variables

All agents use these environment variables (loaded from `.env` file):

- `GOOGLE_CLOUD_PROJECT`: GCP project ID (default: aiagent-capstoneproject)
- `GOOGLE_CLOUD_LOCATION`: GCP location (default: us-central1)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON
- `GOOGLE_GENAI_USE_VERTEXAI`: Use Vertex AI (default: 1)
- `ADK_LOG_LEVEL`: Logging level (default: DEBUG)

## Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f cortex-meta-agent
```

### Stop Services
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

### Run Specific Agent
```bash
docker-compose up cortex-meta-agent
```

### Access Container Shell
```bash
docker exec -it cortex-meta-agent /bin/bash
```

## Building Individual Images

```bash
# Build agents image
docker build -t cortex-meta-agent:latest -f Dockerfile .
```

## Troubleshooting

### Environment Variables Not Loading
1. Check that `.env` file exists in project root
2. Verify volume mounts in `docker-compose.yml`
3. Check container logs: `docker-compose logs`

### Service Account Authentication
1. Ensure `service_account.json` exists in project root
2. Verify `GOOGLE_APPLICATION_CREDENTIALS` path in `.env` file
3. Check volume mount in `docker-compose.yml`

### Agent Import Errors
1. Check that all agent directories are copied in Dockerfile
2. Verify requirements.txt files exist
3. Check container logs for import errors

## Notes

- All agents share the same Docker image but run as separate containers
- `.env` file is mounted as read-only volume
- Service account JSON is mounted for authentication
- Agents don't expose ports (run as background services)

