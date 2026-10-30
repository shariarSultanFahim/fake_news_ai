# DEPLOY.md: Production & Local Deployment Guide

This document provides step-by-step instructions for deploying the Bangla Fake News Detector backend service.

---

## 1. Production Deployment on Ubuntu VPS (e.g. Hostinger KVM 2)

Target Server Specs: Ubuntu 22.04 / 24.04 LTS, 2 vCPU, 8 GB RAM.

### Step 1: Install Docker and Docker Compose
Log into your VPS via SSH and install Docker:
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key & repository
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Ensure current user can run docker without sudo
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Clone Repository and Setup Directory
```bash
sudo mkdir -p /opt/fake_news
sudo chown -R $USER:$USER /opt/fake_news
cd /opt/fake_news

# Clone or copy project files to /opt/fake_news
git clone <YOUR_GIT_REPO_URL> .
```

### Step 3: Copy Model Files
As model files are git-ignored and human-supplied, copy the `backend/model` folder from your local machine to `/opt/fake_news/backend/model`:
```bash
# On your local machine:
scp -r ./backend/model user@<VPS_IP>:/opt/fake_news/backend/model
```
Verify the contents on the VPS:
```bash
ls -la /opt/fake_news/backend/model
# Expected: config.json, inference_config.json, model.safetensors, tokenizer.json, tokenizer_config.json
```

### Step 4: Configure Domain and Environment
Configure the DNS A record of your domain or subdomain (e.g. `api.yourdomain.com`) to point to your VPS IP address.

Create `.env` inside `/opt/fake_news/deploy/.env`:
```bash
cd /opt/fake_news/deploy
cp ../.env.example .env
nano .env
```
Set your domain:
```env
DOMAIN=api.yourdomain.com
CORS_ALLOWED_ORIGINS=chrome-extension://*
RATE_LIMIT_PER_MINUTE=30
```

### Step 5: Start Containers
```bash
cd /opt/fake_news/deploy
docker compose up -d --build
```

### Step 6: Verify Deployment
```bash
# Check running containers
docker compose ps

# Check logs
docker compose logs -f

# Test HTTPS /health endpoint
curl -f https://api.yourdomain.com/health
# Response: {"status":"ok","model_version":"v1","threshold":0.4}
```

---

## 2. Local Demo Alternative (No Docker / Local Laptop)

If running directly on a developer laptop or for a demo:

### Step 1: Activate Virtual Environment
```powershell
# Windows
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate
```

### Step 2: Run Uvicorn Server
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Step 3: Verify
Open `http://127.0.0.1:8000/health` in your browser or curl:
```bash
curl http://127.0.0.1:8000/health
```

### Step 4: Exposing to Another Device / Mobile (Optional)
If another device needs to connect for testing, use a secure tunnel tool (e.g., Cloudflare Tunnel or ngrok):
```bash
cloudflared tunnel --url http://127.0.0.1:8000
```
Use the resulting `https://*.trycloudflare.com` URL in the Chrome Extension options.
