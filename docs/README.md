# KeyProse

KeyProse drafts listing copy, a comparable-sale summary, social posts, email sequences, and an outreach preview. It is a working software asset. The buyer supplies the AI key and the hosting. The repo does not include accounts, billing, a customer database, traffic, revenue, or a user list.

The public site is [https://keyprose.com](https://keyprose.com). `www.keyprose.com` redirects there. `keyprose.app` and `www.keyprose.app` serve the same site. Privacy: [https://keyprose.com/privacy](https://keyprose.com/privacy). Terms: [https://keyprose.com/terms](https://keyprose.com/terms).

Source today: [https://github.com/K-Love/keyprose](https://github.com/K-Love/keyprose).

## Tools

| Tool | Page | Endpoint | What it does |
|------|------|----------|----------------|
| Listing Writer | `/tools/listing` | `POST /api/listing-writer` | MLS description from `property_details`, `tone` (`luxury`, `family`, `investment`, `casual`, `professional`), and `length` (`short`, `medium`, `long`). |
| CMA Assistant | `/tools/cma` | `POST /api/cma` | Value, range, price per square foot, and a written summary from the comps you submit, plus a PDF. The PDF says it is not an appraisal. |
| Social Generator | `/tools/social` | `POST /api/social` | Draft posts for `instagram`, `facebook`, `twitter`, `linkedin`, or `all`. Nothing is published. |
| Email Campaigns | `/tools/email` | `POST /api/email` | Draft sequence for `buyer`, `seller`, `investor`, `past_client`, or `cold_lead`. Nothing is sent. |
| Outreach Engine | `/tools/outreach` | `POST /api/outreach` | Preview for `new_listing`, `price_drop`, `open_house`, `follow_up`, or `custom`. Stock templates do not call the model. `custom` can. Nothing is sent. |

`GET /api/health` returns `status`, `version`, `ai_mode`, and `provider_host`. The Netlify function also returns `host: "netlify"`. Tool JSON adds `ai_mode` and, when sample copy was used, `notice`.

## Architecture

```
frontend/                         static pages (no build)
  index.html, tools/*.html
  api-docs.html                   public /docs on Netlify
  _redirects                      same paths as netlify.toml
netlify/functions/api.mjs         hosted /api/* handler
netlify/functions/ai_provider.mjs prompts and Chat Completions
netlify/functions/ai_limits.mjs   Netlify Blobs counters
backend/server.py                 FastAPI: pages + /api/*
backend/demo_http.py              route dispatch for the Python app
backend/ai/*.py                   the five tools
backend/services/ai_client.py     Chat Completions for Python
backend/services/pdf_generator.py CMA PDF files
backend/models/schemas.py         Pydantic bodies for the Python app
```

The browser calls `/api/*` on the same origin. On Netlify, that request hits `api.mjs`. Locally and in Docker, `server.py` handles it in Python. The prompts are duplicated on purpose so the hosted function does not need Python.

Python CMA returns `cma_pdf_url` as `/api/cma/pdf/{filename}` and stores the file under `PDF_OUTPUT_DIR`. The hosted function returns a `data:application/pdf;base64,...` URL in the JSON and does not keep the file.

Python CORS allows every origin (`allow_origins=["*"]` in `backend/server.py`). The Netlify function does not send an `Access-Control-Allow-Origin` header. The pages on the same host do not need one.

## Environment variables

Name and purpose only. Do not put secret values in the repo, the docs, or a zip.

| Name | Where it is read | Purpose |
|------|------------------|---------|
| `OPENAI_API_KEY` | `backend/services/ai_client.py`, `netlify/functions/ai_provider.mjs` | Key sent as a bearer token. Unset or blank: demo mode, no outbound model call. |
| `AI_BASE_URL` | same | API root. Unset, both clients use the built-in root in those files. The client posts to the root plus the chat-completions path, unless the root already ends with that path. |
| `AI_MODEL` | same | Model id. Takes priority over `OPENAI_MODEL`. |
| `OPENAI_MODEL` | same | Model id when `AI_MODEL` is unset. When both are unset, both clients use the built-in model id in those files. |
| `AI_MAX_INPUT_CHARS` | same | Max characters of prompt plus system text. Over the cap: sample copy. Unset, the code default applies. Zero disables the cap. |
| `AI_MAX_TOKENS` | same | Cap on `max_tokens`. Unset, the code default applies. |
| `AI_MAX_BODY_CHARS` | `netlify/functions/ai_provider.mjs` only | Max request body. Over the cap: HTTP 413. Unset, the code default applies. Zero disables the cap. |
| `AI_RATE_LIMIT_PER_HOUR` | hosted function only | Live calls per IP per hour. Unset, the code default applies. Zero disables the cap. Counts go to the Blobs store `keyprose-ai-limits`, or to process memory if Blobs cannot be opened. |
| `AI_DAILY_CAP` | hosted function only | Live calls per UTC day for the site. Unset, the code default applies. Zero disables the cap. |
| `PORT` | `backend/server.py`, `scripts/run_demo.sh` | Python listen port. Unset, the code default applies. |
| `PDF_OUTPUT_DIR` | `backend/services/pdf_generator.py`, `backend/demo_http.py` | CMA PDF directory for the Python server. Unset, the system temp directory is used. |
| `DB_FILE` | `scripts/seed_db.sh` only | SQLite file for the sample seed. Unset, the script uses `keyprose.db`. If that file is missing and `listing_pilot.db` exists, the script updates the old file. The application does not read it. |

There is no `API_KEY` variable and no `DATABASE_URL` in the running code.

## Plug in a provider key

1. Create a key at the Chat Completions host you want to use.
2. Set `OPENAI_API_KEY` to that key. The variable name stays `OPENAI_API_KEY` for every host.
3. Set `AI_BASE_URL` to that host's API root, and `AI_MODEL` to a model id the host lists.
4. Restart the Python process, or redeploy Netlify after saving the variables for the deploy contexts you use.

Confirm with `GET /api/health`. `ai_mode` is `live` when the key is set. `provider_host` is the hostname only.

No key, a failed call, an over-long prompt, or a hosted rate limit: the tool returns the built-in sample copy and says so in `notice` when it can. `ai_mode` on that tool response stays `demo` unless the model text was used. Social and email can mix the two. A partial mix uses the notice `Part of this result is sample copy because a model call failed.`

The privacy page says that on November 7, 2026 the public site sent live drafts to Abacus RouteLLM. That host is a Netlify environment setting, not a key in this repo.

## Local development

Python 3.11+ and pip. Node.js 18+ for the function tests.

```bash
python3 -m pip install -r backend/requirements.txt
python3 backend/server.py
```

- App: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

`bash scripts/run_demo.sh` does the same start, and prints whether `OPENAI_API_KEY` is set.

Docker (Python server and `frontend/` only):

```bash
docker build -t keyprose .
docker run -p 8000:8000 keyprose
```

## Tests

```bash
python3 -m pytest backend/tests/
npm ci
node --test netlify/api.test.mjs
```

No provider key is required. CI is `.github/workflows/ci.yml`.

## Deploy on Netlify

Default host for the public site.

1. Transfer the existing site, or create one. The current site name is `listingp`. Do not rename `listingp` as part of a transfer. The name is not stored in this repo.
2. Connect the GitHub repo. Publish directory is `frontend` (`netlify.toml`). Leave the build command empty. Netlify still installs `package.json` so `@netlify/blobs` is available to the function.
3. Set the variables in **Site configuration → Environment variables**. Include `OPENAI_API_KEY` only if you want live copy.
4. Deploy. `npx netlify deploy --prod --build` from a logged-in CLI does the same against a linked site.
5. Domains. Add `keyprose.com`, `www.keyprose.com`, `keyprose.app`, and `www.keyprose.app`. Use the DNS targets Netlify displays. Redirect `www.keyprose.com` to `https://keyprose.com`. Serve the same site on `keyprose.app` and `www.keyprose.app`. HTTPS follows once DNS verifies.

`[functions.api] timeout` is 26 seconds, which is the synchronous function maximum this file is written for. The Python client uses a 30 second HTTP timeout and is not part of the Netlify deploy.

Redirects in `netlify.toml` and `frontend/_redirects`:

| From | To |
|------|----|
| `/docs` | `/api-docs.html` |
| `/tools/listing` | `/tools/listing.html` |
| `/tools/cma` | `/tools/cma.html` |
| `/tools/social` | `/tools/social.html` |
| `/tools/email` | `/tools/email.html` |
| `/tools/outreach` | `/tools/outreach.html` |
| `/privacy` and `/privacy/` | `/privacy.html` |
| `/terms` and `/terms/` | `/terms.html` |

`netlify.toml` does not define response headers. There is no `_headers` file. Add headers on the host you choose if you want them.

## Moving to another registrar

`keyprose.com` and `keyprose.app` are registered at Porkbun. You can leave both there and point DNS at any host.

To transfer a domain to another registrar: unlock it at Porkbun, copy the authorization (EPP) code, and start the transfer with the new registrar. Do that once per domain. ICANN lets a registrar refuse a transfer during the first 60 days after registration or after an earlier transfer. A registrant-contact change can start that same 60-day lock. DNS can stay at the old registrar, move with the domain, or move to the host. The website host is whichever server the DNS records name.

## Hosting elsewhere

Netlify is the documented default. This repo has no Vercel project file and no Cloudflare Wrangler config. Port the pieces below. Do not expect the Netlify handler to run unchanged.

### What is specific to Netlify

- **Function format.** `netlify/functions/api.mjs` exports `handler(req)` (web `Request` in, `Response` out) and `config.path = "/api/*"`. `netlify/functions/ai_provider.mjs` is imported by that handler. `netlify/functions/ai_limits.mjs` calls `getStore` from `@netlify/blobs` on the store `keyprose-ai-limits`.
- **`netlify.toml`.** Publish directory, the 26 second function timeout, and the redirects in the table above. No headers block.
- **`frontend/_redirects`.** The same redirects, in Netlify's published-folder redirects file.
- **Environment variables.** The function reads `process.env`. Set them in the Netlify UI or CLI. The Python app reads the same AI names with `os.getenv`.

Hosted-only behavior sits in those JavaScript files: body size cap, hourly and daily live caps, `host: "netlify"` on the health check, and the inline PDF.

### Plain VPS, or any host that runs the Python app

This path is already in the repo. Use `python3 backend/server.py` or the `Dockerfile` (`backend/` and `frontend/` only). `backend/server.py` serves the pages, the extensionless tool URLs, `/privacy`, and `/terms`. `backend/demo_http.py` implements `/api/*`. You do not need `netlify.toml`, `api.mjs`, or Blobs.

You do need to supply TLS and the domain yourself (a reverse proxy is the usual way). Set `PORT`, `PDF_OUTPUT_DIR`, and the AI variables in the environment. There is no hourly or daily cap in Python. Request bodies must satisfy `backend/models/schemas.py`. CMA PDFs are files on disk, fetched from `/api/cma/pdf/{filename}`.

### Vercel

Publish `frontend/` as the static root. Copy the redirects into `vercel.json`. Vercel will not run `netlify/functions/api.mjs` as-is: the export and the request object differ, and `@netlify/blobs` is not available. Port `api.mjs` and `ai_provider.mjs` onto a Vercel function, and replace `ai_limits.mjs` with another counter or drop the caps. Set the same variable names in the Vercel project. The Python server is a separate process. Vercel static hosting does not start it.

### Cloudflare Pages or Workers

Pages can publish `frontend/`. `frontend/_redirects` lists the same rewrites as `netlify.toml`, in the redirects file both Netlify and Pages understand. These rules are plain path rewrites. Confirm them on Pages before you rely on them. A Worker does not load the Netlify handler unchanged: the handler signature differs, `ai_provider.mjs` imports `node:crypto`, and `ai_limits.mjs` depends on Netlify Blobs. Port `api.mjs` and `ai_provider.mjs`, and replace the Blobs counter. Bind the environment variables the way that platform expects. To avoid a JavaScript port, run `backend/server.py` on a VPS and point the domain at it.

## Release zip

`bash scripts/build_release.sh` or `make release` writes `release/keyprose-release.zip` from tracked files and untracked files that are not gitignored. The script leaves out `.git`, `.env` files, databases, `node_modules`, caches, and anything already zipped under `release/`. The zip is gitignored. Commit the script, not the archive. The previous `release/listing-pilot.zip` was removed.

## Known limits

- No accounts, no billing, and no stored user listings. The seed database is optional local sample data.
- The public function accepts partial JSON objects. `property_details` must be an object for the listing writer. CMA needs an `address` and a non-empty `comps` array, and each comp is not schema-checked. Social needs `property_id`. Email needs `recipient_type` and a `context` object. Outreach needs a non-empty `target_list`, and a contact does not need `name` or `email`. Missing numbers fall back to sample defaults (for example 3 bedrooms, 2 bathrooms, 1800 square feet). A body that is not valid JSON returns HTTP 400. The Python models reject missing required fields with HTTP 422. A comp there needs `address`, `price`, `sqft`, `beds`, `baths`, and `sold_date`. A contact needs `name` and `email`.
- Sample copy adds generic lines. Medium and long listings append kitchen, bath, yard, garage, and school sentences the user did not enter. Social sample posts add Austin wording and Austin hashtags even when the address is somewhere else, and missing details become a stand-in price and highlight. Email sample templates fill blanks with a generic agent name, a 512 phone number, stand-in prices, a seller's-market line, and a fixed market snapshot, and some buyer and investor templates add interest, offer, and renovation lines. The CMA summary adds a fixed sentence about moderate demand and limited inventory. The numeric range is computed from the comps (low about 3% under the cheapest, high about 3% over the dearest).
- Live listing prompts still substitute those bedroom, bath, and size defaults when the fields are empty, and they include a non-empty neighborhood. The privacy page currently says the neighborhood is not sent on the live listing request. That sentence does not match `listingPrompt` in `backend/ai/listing_writer.py` and `netlify/functions/ai_provider.mjs`. Update it when you edit the legal pages. Do not treat this note as a change to those pages.
- `docs/API_REFERENCE.md` shows an `API_KEY` header the server does not check. `docs/DEMO_SCRIPT.md` is a spoken walkthrough and is not the spec.
