# CampusVoice — Python web application

This repository contains the Python/FastAPI CampusVoice application and its static HTML/CSS/JavaScript portals.

## Run locally

```powershell
py -m venv .\python\.venv
.\python\.venv\Scripts\python.exe -m pip install -r .\python\requirements.txt
.\python\.venv\Scripts\python.exe .\python\main.py
```

Open http://localhost:8000.

## Deploy a free demo

See [DEPLOY-RENDER-FREE.md](DEPLOY-RENDER-FREE.md). The included root-level `render.yaml` creates a Free Render web service. Free hosting supports custom domains but has an ephemeral filesystem and sleep/wake delays. Use demo data only; SQLite registrations and uploads may be lost on spin-down, restart, or redeploy.
