# Installation

Run KeyProse on your machine, on Netlify, or on a host that can run the Python server. You supply the AI key. The app has no accounts and no billing.

## Requirements

- Python 3.11 or newer, pip, and Git
- Node.js 18 or newer, only to run `netlify/api.test.mjs`
- About 512 MB of RAM for the Python server
- macOS, Linux, or Windows with WSL

## Local run

```bash
git clone https://github.com/K-Love/keyprose.git
cd keyprose
python3 -m pip install -r backend/requirements.txt
python3 backend/server.py
```

Check:

```bash
curl -s http://localhost:8000/api/health
```

With no key, `ai_mode` is `demo`. Open `http://localhost:8000`. Swagger is `http://localhost:8000/docs` on this Python server. On a Netlify deploy, `/docs` is the static page `frontend/api-docs.html`.

`bash scripts/run_demo.sh` installs the Python requirements when FastAPI is missing and starts the server on `PORT`.

The optional sample database is `bash scripts/seed_db.sh`. It creates `keyprose.db` and does not connect the app to it. If `listing_pilot.db` is already present and `keyprose.db` is not, the script updates the old file. Override the path with `DB_FILE`.

## Tests

From the repo root, after `python3 -m pip install -r backend/requirements.txt` and `npm ci`:

```bash
python3 -m pytest backend/tests/
node --test netlify/api.test.mjs
```

No AI key is required.

## AI key

Set `OPENAI_API_KEY` in the environment, then start the server again. Set `AI_BASE_URL` and `AI_MODEL` when the host is not the code's default OpenAI root and model. Names and purposes are in the table below. Do not write the key into a file that you commit.

Stock outreach templates never call the model. The `custom` template does, when a key is set. Any other failure, over-long prompt, or (on Netlify) rate limit falls back to sample copy.

## Docker

The image runs `backend/server.py` and copies `frontend/`. It does not include the Netlify function.

```bash
docker build -t keyprose .
docker run -p 8000:8000 keyprose
```

Add `-e` flags for `OPENAI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`, `PORT`, or `PDF_OUTPUT_DIR` when you need them.

## Environment variables

| Name | Purpose |
|------|---------|
| `OPENAI_API_KEY` | Provider key. Unset or blank: demo mode. |
| `AI_BASE_URL` | Chat Completions API root. Unset, the client uses the built-in root in `backend/services/ai_client.py` and `netlify/functions/ai_provider.mjs`. A root ending in `/chat/completions` is used as the full URL. |
| `AI_MODEL` | Model id. Overrides `OPENAI_MODEL`. |
| `OPENAI_MODEL` | Model id when `AI_MODEL` is unset. When both are unset, the client uses the built-in model id in those files. |
| `AI_MAX_INPUT_CHARS` | Max prompt size sent to the model. Unset, the code default applies. Zero disables the cap. Over the cap: sample copy. |
| `AI_MAX_TOKENS` | Cap on `max_tokens`. Unset, the code default applies. |
| `AI_MAX_BODY_CHARS` | Netlify function only. Max body size. Unset, the code default applies. Zero disables the cap. Over the cap: HTTP 413. |
| `AI_RATE_LIMIT_PER_HOUR` | Netlify function only. Live calls per IP per hour. Unset, the code default applies. Zero disables the cap. |
| `AI_DAILY_CAP` | Netlify function only. Live calls per UTC day. Unset, the code default applies. Zero disables the cap. |
| `PORT` | Python listen port. Unset, the code default applies. |
| `PDF_OUTPUT_DIR` | Python CMA PDF directory. Unset, the system temp directory is used. |
| `DB_FILE` | Seed-script SQLite path only. Unset, the script uses `keyprose.db`, or an existing `listing_pilot.db` when the new file is absent. |

## Deploy on Netlify

Default production host. Config is `netlify.toml`: publish `frontend`, function timeout 26 seconds, redirects for `/docs`, `/tools/*`, `/privacy`, and `/terms`. `frontend/_redirects` repeats the redirects. There is no headers file.

The live site's Netlify name is `listingp`. Keep that name if you transfer the site.

1. Log in with `npx netlify login`, or sign in at the Netlify UI.
2. Link or create the site (`npx netlify init` or `npx netlify link`). Connect the GitHub repository if you want Git deploys.
3. Set the variables under site environment settings. Save them for each deploy context you publish.
4. `npx netlify deploy --prod --build`.
5. Attach `keyprose.com`, `www.keyprose.com`, `keyprose.app`, and `www.keyprose.app`. Enter the DNS records Netlify gives you at the DNS host. Redirect `www.keyprose.com` to `https://keyprose.com`. Point the `.app` hostnames at the same site.

Domains are registered at Porkbun. You can leave them there. See [TRANSFER_INSTRUCTIONS.md](TRANSFER_INSTRUCTIONS.md) to transfer a domain out, including the 60-day ICANN lock.

## Hosting elsewhere

Use the Python server when you are not on Netlify. `backend/server.py` already serves the static pages and `/api/*` by calling `backend/demo_http.py` and `backend/ai/`. Put it behind your own TLS proxy and set the environment variables in the process. The Dockerfile is this same server. `netlify.toml` and `netlify/functions/` are unused on this path. Python has no Blobs rate limit, and it validates JSON with `backend/models/schemas.py`.

To stay on a static host such as Vercel or Cloudflare Pages, publish `frontend/` and port `netlify/functions/api.mjs` plus `netlify/functions/ai_provider.mjs`. Replace `netlify/functions/ai_limits.mjs`, which imports `@netlify/blobs`. Recreate the redirects from `netlify.toml` or `frontend/_redirects` in that host's config. `frontend/_redirects` is the same rewrite list Pages can publish. Confirm those rules on Pages before you rely on them. This repository does not ship those adapters. The file-by-file notes are in [../docs/README.md](../docs/README.md#hosting-elsewhere).

## Troubleshooting

**`ModuleNotFoundError: No module named 'fastapi'`**

```bash
python3 -m pip install -r backend/requirements.txt
```

Run `python3 backend/server.py` from the repo root.

**Port in use**

Set `PORT` to a free port and start the server again.

**Scripts are not executable**

```bash
bash scripts/run_demo.sh
bash scripts/seed_db.sh
bash scripts/build_release.sh
```

**Browser calls to a different origin fail on Netlify**

The function does not add a CORS header. The shipped pages call `/api` on the same host. The Python server allows every origin.
