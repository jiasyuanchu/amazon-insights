# Deployment Guide

## Overview

This guide covers different deployment strategies for Amazon Insights platform, from simple frontend-only deployment to full-stack production setup.

## 🌐 GitHub Pages Deployment (Frontend Only)

### Step 1: Enable GitHub Pages

1. **Go to Repository Settings**:
   ```
   https://github.com/jiasyuanchu/amazon-insights/settings/pages
   ```

2. **Configure Source**:
   - Select "GitHub Actions" (not "Deploy from a branch")
   - Save settings

### Step 2: Create Pages Deployment Workflow

Create `.github/workflows/deploy-pages.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v4
      - name: Prepare frontend
        run: |
          mkdir -p _site
          cp -r frontend/* _site/
      - uses: actions/upload-pages-artifact@v3
        with:
          path: '_site'
      - uses: actions/deploy-pages@v4
        id: deployment
```

### Step 3: Access Your Deployed Frontend

After deployment, your dashboard will be available at:
```
https://jiasyuanchu.github.io/amazon-insights/
```

## 🖥️ API Server Deployment Options

Since GitHub Pages only hosts static files, you need to deploy the API server separately:

### Option 1: Heroku (Recommended for beginners)

1. **Install Heroku CLI**
2. **Create Heroku App**:
   ```bash
   heroku create amazon-insights-api
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set FIRECRAWL_API_KEY=your_key
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set DATABASE_URL=postgresql://...
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### Option 2: Railway

1. **Connect GitHub repo to Railway**
2. **Set environment variables in Railway dashboard**
3. **Automatic deployment on push**

### Option 3: DigitalOcean App Platform

1. **Create App from GitHub repo**
2. **Configure environment variables**
3. **Automatic deployment**

### Option 4: Self-hosted with Docker

```bash
# Clone and setup
git clone https://github.com/jiasyuanchu/amazon-insights.git
cd amazon-insights
cp .env.example .env
# Edit .env with your configuration

# Deploy with Docker Compose
docker-compose up -d
```

## 🔄 Complete CI/CD Setup

### Current CI Pipeline ✅

**Triggers**: Every push to main
**Checks**:
- Python environment setup
- Dependency installation
- Basic functionality tests
- Project structure validation

### Enhanced CD Pipeline Options

#### Option A: Frontend-Only Deployment
```yaml
name: CD - Frontend Only

on:
  push:
    branches: [main]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v4
      - name: Deploy to Pages
        # ... (frontend deployment)
```

#### Option B: Full-Stack Deployment
```yaml
name: CD - Full Stack

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker images
        run: |
          docker build -t amazon-insights-api .
          docker build -f Dockerfile.frontend -t amazon-insights-frontend .
      - name: Deploy to production
        # Deploy to your chosen platform
```

## 🎯 Recommended Deployment Strategy

### Phase 1: Frontend Demo (GitHub Pages)
- ✅ **Deploy frontend to GitHub Pages** (free)
- ✅ **Use mock data or demo API**
- ✅ **Perfect for showcasing UI/UX**

### Phase 2: Full-Stack Development
- 🚀 **Deploy API to Heroku/Railway** (free tier)
- 🔗 **Connect frontend to live API**
- 🗄️ **Use PostgreSQL add-on**

### Phase 3: Production Scale
- 🏢 **Professional hosting** (DigitalOcean/AWS)
- 🔒 **Custom domain with SSL**
- 📊 **Monitoring and scaling**

## 🛠️ Quick Start: GitHub Pages

### Immediate Setup (Frontend Only)

1. **Create the Pages workflow** (copy the YAML above)
2. **Enable GitHub Pages** in repo settings
3. **Push any change** to trigger deployment
4. **Access at**: `https://jiasyuanchu.github.io/amazon-insights/`

### API Connection Options

For the deployed frontend to work with data:

#### Option A: Mock Data Demo
```javascript
// Add to frontend/script.js
const DEMO_MODE = window.location.hostname.includes('github.io');
if (DEMO_MODE) {
    // Use mock data for demo
    loadDemoData();
}
```

#### Option B: Deploy API Separately
- Deploy API to Heroku/Railway
- Update frontend API_BASE_URL
- Full functionality available

## 📋 Implementation Steps

### 1. GitHub Pages Setup (5 minutes)

1. **Go to repo Settings → Pages**
2. **Select "GitHub Actions" as source**
3. **Create deploy-pages.yml workflow**
4. **Push to trigger deployment**

### 2. API Deployment (15-30 minutes)

Choose one platform:
- **Heroku**: Easy setup, free tier available
- **Railway**: Modern platform, GitHub integration
- **DigitalOcean**: More control, slightly more complex

### 3. Connect Frontend to API (5 minutes)

Update frontend configuration to point to deployed API.

## 🎉 Benefits of This Approach

### GitHub Pages Frontend
- ✅ **Free hosting**
- ✅ **Automatic SSL** (HTTPS)
- ✅ **CDN distribution** (fast globally)
- ✅ **Custom domain support**
- ✅ **Automatic deployment** on push

### Separate API Deployment
- ✅ **Full backend functionality**
- ✅ **Database persistence**
- ✅ **Real-time data**
- ✅ **Scalable architecture**

Want me to help you set up GitHub Pages deployment first? It's the quickest way to get your frontend online!