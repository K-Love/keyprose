# Buyer onboarding

KeyProse is the listing-agent drafting app in this repository: five tools, a static frontend, a Netlify function, and a Python server that can run the same routes. You host it and you bring the AI key. Nothing here is an account system, a billing system, or a book of business.

Pages to read with this one: [README.md](README.md), [../README.md](../README.md), [../release/INSTALLATION.md](../release/INSTALLATION.md), [../release/TRANSFER_INSTRUCTIONS.md](../release/TRANSFER_INSTRUCTIONS.md).

## 1. Take the code

The repository is [github.com/K-Love/keyprose](https://github.com/K-Love/keyprose). After the GitHub transfer, clone your copy. `bash scripts/build_release.sh` builds `release/keyprose-release.zip` if you want a snapshot without `.git`. See the transfer checklist for what that zip leaves out.

## 2. Run it locally

Python 3.11 or newer.

```bash
python3 -m pip install -r backend/requirements.txt
python3 backend/server.py
```

Open `http://localhost:8000`. Interactive API docs on this server are `http://localhost:8000/docs`. `bash scripts/run_demo.sh` is the same start.

With `OPENAI_API_KEY` unset, the tools return sample copy and `/api/health` reports `ai_mode` of `demo`.

`bash scripts/seed_db.sh` writes sample rows to `keyprose.db`. The server does not read that file. An existing `listing_pilot.db` is kept when `keyprose.db` is not there yet. Set `DB_FILE` to pick a path.

## 3. Add your AI key

Set `OPENAI_API_KEY` to your provider's key. Set `AI_BASE_URL` to that provider's Chat Completions root, and `AI_MODEL` to the model id. The variable is named `OPENAI_API_KEY` for every host.

Restart the Python process. `GET /api/health` then reports `ai_mode` of `live` and `provider_host` as a hostname. A failed or over-long call still returns sample copy and a `notice`.

Every variable the code reads is listed in [README.md](README.md#environment-variables). Do not paste key values into files in this repo.

## 4. Deploy on Netlify

This is the default host.

1. Transfer the existing site, or create a new one and connect the repo. The existing site name is `keyprose`. Its default URL is https://keyprose.netlify.app. A buyer may rename it. Only the .netlify.app address changes. Custom domains keep working.
2. Publish directory: `frontend`, from `netlify.toml`. No build command. The root `package.json` supplies `@netlify/blobs` for the live-generation counters.
3. Set the environment variables in the Netlify site settings for each deploy context you use.
4. Add `keyprose.com`, `www.keyprose.com`, `keyprose.app`, and `www.keyprose.app`. Point DNS using the records Netlify shows. Redirect `www.keyprose.com` to `https://keyprose.com`. `keyprose.app` and `www.keyprose.app` redirect to `https://keyprose.com` from the rules at the top of `frontend/_redirects`.

`npx netlify login` and `npx netlify deploy --prod --build` deploy a linked site from a checkout.

## 5. Registrar

Both domains are at Porkbun. Keep them there and change DNS if you only need a new host. To move a domain, unlock it, take the authorization (EPP) code, and submit the transfer at the new registrar. Repeat for the other domain. A domain registered or transferred in the last 60 days cannot be transferred again until that ICANN window ends. A registrant-contact change can start the same lock. The registrar and the website host are separate. DNS decides the host.

## 6. Another host

Netlify-specific pieces are `netlify/functions/api.mjs` (handler plus `/api/*`), `netlify/functions/ai_provider.mjs`, `netlify/functions/ai_limits.mjs` (Netlify Blobs), `netlify.toml` (publish directory, function timeout, redirects), and `frontend/_redirects`. This repo does not set custom response headers.

A VPS runs the Python app that is already here: `python3 backend/server.py` or the `Dockerfile`. That process serves the pages and the API. It does not use the Netlify function or Blobs. You terminate TLS yourself.

Vercel or Cloudflare needs a port of `api.mjs` and `ai_provider.mjs`. The Blobs helper does not run there. Cloudflare Pages can publish `frontend/` and understands `frontend/_redirects`. Details, including the files to touch, are in [README.md](README.md#hosting-elsewhere).

## 7. Tests

```bash
python3 -m pytest backend/tests/
npm ci
node --test netlify/api.test.mjs
```

Both pass without a provider key.

## 8. Before you call it yours

Work through [../release/TRANSFER_INSTRUCTIONS.md](../release/TRANSFER_INSTRUCTIONS.md): GitHub transfer, Netlify transfer or a new site, Porkbun domains, key rotation, and the Privacy and Terms pages. Those pages name Kevin Love and Backstage Interactive. They are still the published legal text. Update them. Do not change them in the product until you mean to.

## Limits to plan around

- No sign-in, no payments, and no database-backed user data.
- The hosted API accepts a partial JSON object and fills gaps with defaults. The Python API rejects a missing required field. Neither runtime accepts truncated JSON.
- Sample copy adds generic lines (extra property claims, Austin social wording, stand-in email figures, a fixed CMA market sentence). Read a draft before a client sees it.
- The tools do not publish, send, or appraise.

`docs/DEMO_SCRIPT.md` is a talk track from an earlier pass. `docs/API_REFERENCE.md` includes an `API_KEY` example this server does not enforce. Use this onboarding guide and [README.md](README.md) for what the code does.
