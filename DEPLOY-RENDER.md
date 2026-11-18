# Put CampusVoice online with Render

This package is prepared for a single-instance Render Web Service. It keeps the existing FastAPI + SQLite implementation and stores the primary database and per-college databases on a persistent disk.

## Before you start

- Create a GitHub account/repository and a Render account.
- Upload the contents of this project folder to the GitHub repository (keep `render.yaml` at the repository root).
- The included Render Blueprint uses a paid `starter` web service and a 1 GB persistent disk. This is intentional: the app stores the college registry in `campus.db` and each institution's campus data in a separate SQLite file. Do not deploy a real multi-college service on an ephemeral filesystem. Check Render's current pricing before creating the service.

## Deploy

1. Push this project to a GitHub repository. Do not commit local `.env` files, SQLite databases, or uploaded private data. The `.gitignore` excludes these files.
2. In Render, choose **New → Blueprint** and connect the GitHub repository.
3. Render reads `render.yaml`. Review the service and disk configuration, then apply it.
4. Wait for the first deploy to complete. Open the service's public `onrender.com` URL.
5. Check `<your-service-url>/api/health`. The response should include `"ok": true` and the `premium-university-layout-redesign-2026-11-15` UI build.
6. Open `/college` on the public HTTPS URL and register the first institution administrator. Then upload that institution's data and share its student/teacher join codes privately.

## Important deployment settings

The Blueprint configures:

- Root directory: `python`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
- Health check: `/api/health`
- Persistent disk: `/var/data`
- Main SQLite file: `/var/data/campus.db`
- College databases: `/var/data/tenants/`
- Secure session cookies: `COOKIE_SECURE=true`
- Demo student/teacher accounts disabled: `AURA_DISABLE_DEMO_ACCOUNTS=true`

One worker is deliberate: the current code holds process-local SQLite connections. Do not increase the worker count or scale to multiple instances without first migrating the database layer to a shared production database (for example, PostgreSQL) and revising the tenant storage implementation.

## Browser microphone

Use the public HTTPS URL and allow microphone access in Chrome or Edge. The Web Speech API is browser-dependent; typed questions remain available when speech recognition is unsupported.

## Costs and free-tier warning

Render's free web services use an ephemeral filesystem and spin down after inactivity. That is suitable for a temporary demonstration only, not for storing college registrations and uploaded campus data. The included persistent-disk Blueprint uses a paid service plan. Check Render's current pricing and limitations before confirming deployment.

## Production checklist

- Use a unique admin email and strong password for each college.
- Keep the teacher join code private; in this project it is the college code prefixed with `teach`, so it is not a strong independent proof of staff status. Add institutional staff verification before accepting sensitive student records.
- Set a custom domain only after the app is working on its Render URL.
- Back up the persistent disk regularly.
- Before real student records are used, add stronger role verification, rate limiting, audit logging, data retention rules, and a tested backup/restore procedure.
