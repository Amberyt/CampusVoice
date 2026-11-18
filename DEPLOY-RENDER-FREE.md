# CampusVoice — free demo deployment on Render

This configuration is for a **temporary single-college demo**, not production student records.

## Important free-plan limitations

- Render free web services support custom domains and managed TLS certificates.
- A free web service spins down after 15 minutes without inbound traffic and can take about a minute to wake up.
- Its filesystem is ephemeral. The SQLite database files used by CampusVoice (`python/campus.db` and `python/tenants/`) can be lost when the service spins down, restarts, or redeploys.
- Therefore, use this free setup only with demo/test data. Do not enter real student records or depend on the database being retained. For reliable college data, use paid hosting with persistent storage or migrate the app to a durable managed database.
- Render hosting does not include domain registration. You must already own or purchase the domain separately.

## 1. Push the project to GitHub

1. Extract the ZIP.
2. Create an empty GitHub repository, e.g. `campusvoice-demo`.
3. Upload the **contents** of this project folder (so `render.yaml` is at repository root, and `python/` is a top-level directory).
4. Do not commit `.env` files, SQLite databases, passwords, or real campus records. The `.gitignore` excludes local SQLite data.

## 2. Deploy on Render

1. Sign in to Render: https://render.com/
2. Choose **New + → Blueprint**.
3. Connect GitHub and select `campusvoice-demo`.
4. Render reads the root-level `render.yaml`. Confirm the service is named `campusvoice-demo` and the plan is **Free**.
5. Apply/create the Blueprint and wait for the first deployment to finish.
6. Open the service's `onrender.com` URL and check `/api/health`. It should return JSON with `"ok": true` and `"engine": "python"`.
7. Open `/college` and register the first college administrator. Use demo-only content.

## 3. Add your custom domain

1. You must own a domain first (for example, `campusvoice.in`). Domain purchase/renewal is separate from Render hosting.
2. In Render, open the `campusvoice-demo` web service → **Settings** → **Custom Domains**.
3. Add the exact domain or subdomain you want (for example, `www.campusvoice.in` or `campusvoice.in`).
4. Render displays the DNS record(s) to create. Open your domain registrar's DNS management page and add those records exactly. For a subdomain, this is commonly a CNAME; for an apex/root domain, the registrar may support ALIAS/ANAME or an A/AAAA record depending on Render's instructions.
5. Return to Render and click **Verify**. Allow time for DNS propagation. Render provisions and renews TLS automatically; HTTPS is redirected once configured.
6. Keep the generated `onrender.com` address as a fallback.

## 4. Launch check

- Visit `/api/health` on the custom domain.
- Test college registration at `/college`.
- Test student and teacher registration using that college's codes.
- Test `/student`, `/teacher`, and the voice assistant.
- Check microphone permission using the HTTPS custom domain.
- Do not load real/personal student data on the free demo deployment.

## Free demo vs. production

This Blueprint intentionally has no persistent disk and uses the app's default SQLite paths. That makes the service eligible for the free compute plan but means the data is not durable. For a real college rollout, switch to paid hosting with persistent storage or migrate SQLite to a managed database and implement backups before collecting real records.
