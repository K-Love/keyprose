# KeyProse

KeyProse is a working software asset for listing agents: five tools that draft MLS descriptions, a comparable-sale summary, social posts, email sequences, and an outreach preview. The public site is [keyprose.com](https://keyprose.com). `www.keyprose.com` redirects there. `keyprose.app` and `www.keyprose.app` serve the same site.

The buyer brings their own AI provider key and their own hosting. This repository has no accounts, no billing, and no customer database. It does not record traffic, revenue, or users.

Current source: [github.com/K-Love/keyprose](https://github.com/K-Love/keyprose).

## Tools

| Tool | Page | Endpoint | What it does |
|------|------|----------|----------------|
| Listing Writer | `/tools/listing` | `POST /api/listing-writer` | Drafts an MLS description from property details, a tone, and a length. |
| CMA Assistant | `/tools/cma` | `POST /api/cma` | Summarizes comparable sales, estimates a value range, and returns a PDF. |
| Social Generator | `/tools/social` | `POST /api/social` | Drafts posts for Instagram, Facebook, Twitter/X, LinkedIn, or all four. It does not publish them. |
| Email Campaigns | `/tools/email` | `POST /api/email` | Drafts a short sequence for a buyer, seller, investor, past client, or cold lead. It does not send mail. |
| Outreach Engine | `/tools/outreach` | `POST /api/outreach` | Shows a multi-step preview for a contact list. Stock templates stay on the built-in text. The `custom` template can call the model. It does not email anyone. |

`GET /api/health` reports `ai_mode` (`live` or `demo`) and `provider_host` (hostname only). The hosted function also returns `host` of `netlify`. The key is never included.

## Architecture

Two ways to serve the same five routes:

1. **Static frontend + Netlify Function.** `netlify.toml` publishes `frontend/`. Pages are HTML, CSS, and a little JavaScript, with no build step. `netlify/functions/api.mjs` handles `/api/*`. Prompts and the Chat Completions call live in `netlify/functions/ai_provider.mjs`. Live-generation counters use Netlify Blobs from `netlify/functions/ai_limits.mjs`.
2. **Python backend.** `python3 backend/server.py` (or the `Dockerfile`) serves those pages and the API together. `backend/demo_http.py` dispatches to `backend/ai/`. `backend/services/ai_client.py` performs the same style of Chat Completions call. `backend/services/pdf_generator.py` writes the CMA PDF to disk.

On Netlify, `/docs` is the static page `frontend/api-docs.html`. On the Python server, `/docs` is Swagger and `/redoc` is ReDoc.

The Python app checks request bodies with `backend/models/schemas.py`. The hosted function checks only a few required keys and accepts a partial object. See [Known limits](#known-limits).

## Environment variables

Names as they appear in code. Set them in the shell for the Python server, or in the Netlify site environment for the function. Do not commit them. This list has no secret values.

| Name | Purpose |
|------|---------|
| `OPENAI_API_KEY` | Bearer key for live Chat Completions. Read by `backend/services/ai_client.py` and `netlify/functions/ai_provider.mjs`. Blank or unset: demo mode. |
| `AI_BASE_URL` | Chat Completions API root, read by those same files. Unset, both clients use the built-in root in those files. A root that already ends in `/chat/completions` is called as-is. Any `http` or `https` Chat Completions host works. |
| `AI_MODEL` | Model id. Used ahead of `OPENAI_MODEL` when both are set. |
| `OPENAI_MODEL` | Model id when `AI_MODEL` is unset. When both are unset, both clients use the built-in model id in those files. |
| `AI_MAX_INPUT_CHARS` | Largest combined prompt and system text sent to the model, in both runtimes. Over the cap, the reply is sample copy. Unset, the code default applies. Zero disables the cap. |
| `AI_MAX_TOKENS` | Upper bound on `max_tokens` sent to the provider, in both runtimes. Unset, the code default applies. |
| `AI_MAX_BODY_CHARS` | Hosted function only. Larger request bodies get HTTP 413. Unset, the code default applies. Zero disables the cap. |
| `AI_RATE_LIMIT_PER_HOUR` | Hosted function only. Live generations per client IP per hour, counted in Netlify Blobs. Unset, the code default applies. Zero disables the cap. Over the cap, the reply is sample copy. |
| `AI_DAILY_CAP` | Hosted function only. Live generations per UTC day for the whole site. Unset, the code default applies. Zero disables the cap. |
| `PORT` | Listen port for `backend/server.py`. Unset, the code default applies. |
| `PDF_OUTPUT_DIR` | Directory where the Python server writes CMA PDFs. Unset, the system temp directory is used. |
| `DB_FILE` | Path for `scripts/seed_db.sh` only. Unset, the script uses `keyprose.db`, or an existing `listing_pilot.db` when `keyprose.db` is absent. The server never opens this file. |

`AI_RATE_LIMIT_PER_HOUR`, `AI_DAILY_CAP`, and `AI_MAX_BODY_CHARS` are read only by the Netlify function. The Python server ignores them.

## Your own AI key

Set `OPENAI_API_KEY` to a key from the provider you choose. Point `AI_BASE_URL` at that provider's Chat Completions root, and set `AI_MODEL` (or `OPENAI_MODEL`) to a model id that host accepts. Restart the Python process after changing the shell. On Netlify, set the variables in **Site configuration → Environment variables** for every deploy context you use, then redeploy.

With no key, every tool still answers. The copy is the built-in sample text, and `ai_mode` is `demo`. With a key, `GET /api/health` reports `ai_mode` of `live`. A tool response reports `live` only when the model text was actually used. If the call fails, the input is too long, or the hosted rate limit is hit, the response is sample copy plus a `notice`.

Stock outreach templates (`new_listing`, `price_drop`, `open_house`, `follow_up`) do not call the model, even when a key is set. Only `custom` does.

The public privacy page, dated November 7, 2026, says live drafts on keyprose.com were sent to Abacus RouteLLM. A new owner chooses the host with `AI_BASE_URL`.

## Local development

Requirements: Python 3.11 or newer (CI runs 3.11 and 3.12), pip, and Git. Node.js 18 or newer is only needed for the function tests.

```bash
python3 -m pip install -r backend/requirements.txt
python3 backend/server.py
```

Open `http://localhost:8000`. `bash scripts/run_demo.sh` installs the Python dependencies if FastAPI is missing and starts the same server.

`bash scripts/seed_db.sh` loads sample rows into `keyprose.db`. Nothing in the server reads that file. If an older `listing_pilot.db` is already in the repo root and `keyprose.db` is not, the script keeps writing the old file.

The Docker image runs the Python server and the static pages. It does not run the Netlify function.

```bash
docker build -t keyprose .
docker run -p 8000:8000 keyprose
```

Pass `OPENAI_API_KEY`, `AI_BASE_URL`, and `AI_MODEL` with `-e` when you want live copy.

## Tests

```bash
python3 -m pytest backend/tests/
npm ci
node --test netlify/api.test.mjs
```

Both suites run without a provider key. GitHub Actions (`.github/workflows/ci.yml`) runs the pytest suite on Python 3.11 and 3.12, then the Node tests.

## Deploy on your own Netlify

`netlify.toml` is the site config. Publish directory is `frontend`. There is no build command. Netlify installs the root `package.json` so the function can import `@netlify/blobs`. `[functions.api] timeout` is 26 seconds. Redirects map `/docs`, the five tool paths, `/privacy`, and `/terms` onto the HTML files. The same redirects are in `frontend/_redirects`. This repo has no `[[headers]]` block and no `_headers` file.

The existing Netlify site is named `listingp`. Leave that name unchanged if you transfer the site. A new site can use any name. The name is not in this repository.

1. Create or transfer a Netlify site and connect this repo, or deploy from a checkout with the Netlify CLI (`npx netlify login`, then `npx netlify init` or `npx netlify link`, then `npx netlify deploy --prod --build`).
2. Set the environment variables above in the site settings. Put the provider key only there.
3. Add the domains `keyprose.com`, `www.keyprose.com`, `keyprose.app`, and `www.keyprose.app`. Point DNS at the records Netlify shows. Configure `www.keyprose.com` to redirect to `https://keyprose.com`, matching the privacy and terms pages. `keyprose.app` and `www.keyprose.app` should serve this same site. Netlify provisions HTTPS after DNS verifies.

Domain registration for `keyprose.com` and `keyprose.app` is at Porkbun. DNS can point those names at Netlify while the registrar stays Porkbun. Moving the registration, or hosting somewhere else, is covered in [docs/README.md](docs/README.md) and [release/TRANSFER_INSTRUCTIONS.md](release/TRANSFER_INSTRUCTIONS.md).

## Transfer pack

- [docs/ONBOARDING.md](docs/ONBOARDING.md) — buyer setup
- [docs/README.md](docs/README.md) — architecture, variables, Netlify, other registrars, other hosts
- [release/INSTALLATION.md](release/INSTALLATION.md) — local run and deploy
- [release/TRANSFER_INSTRUCTIONS.md](release/TRANSFER_INSTRUCTIONS.md) — GitHub, Netlify, domains, keys, legal pages
- [release/LICENSE.txt](release/LICENSE.txt) — MIT

`bash scripts/build_release.sh` or `make release` writes `release/keyprose-release.zip`. That zip is gitignored. The old committed `release/listing-pilot.zip` was a stale snapshot and has been removed.

## Known limits

- No accounts, no sign-in, no billing, and no database of listings, contacts, or past generations. `scripts/seed_db.sh` only creates a local sample file the app does not read. Rate-limit counts on Netlify are counters, not user records.
- The hosted API accepts a JSON object with only some fields filled in. Invalid JSON, including a truncated `{`, returns HTTP 400. The Python server returns 422 when a required field is missing. Details are in [docs/README.md](docs/README.md#known-limits).
- Sample and demo copy adds generic lines that were not in the request: extra rooms and neighborhood claims in listings, Austin wording in social posts, stand-in agent and market figures in emails, and a fixed demand sentence in the CMA summary.
- The tools draft text. They do not file an MLS listing, send email, publish a social post, or produce an appraisal.
- `docs/API_REFERENCE.md` is an example write-up. It mentions an `API_KEY` check that this code does not implement. `docs/DEMO_SCRIPT.md` is a talk track. The limits in this file are the product.

## License

MIT. See [release/LICENSE.txt](release/LICENSE.txt).
