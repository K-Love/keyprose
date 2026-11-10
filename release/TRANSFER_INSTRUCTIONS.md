# Transfer instructions

Hand off KeyProse as a working software asset. The buyer uses their own AI key and their own hosting. The repository does not include revenue, traffic, users, accounts, or billing.

Source today: [https://github.com/K-Love/keyprose](https://github.com/K-Love/keyprose). License: [LICENSE.txt](LICENSE.txt) (MIT).

## What you are transferring

- This Git repository: `frontend/`, `backend/`, `netlify/`, `docs/`, `demo_data/`, `scripts/`, `Dockerfile`, `netlify.toml`, and GitHub Actions in `.github/workflows/ci.yml`
- The public domains `keyprose.com` and `keyprose.app`, registered at Porkbun
- The Netlify site that serves them, named `keyprose`. Its default URL is https://keyprose.netlify.app. keyprose.com is unchanged.
- Operator identity on the Privacy and Terms pages (Kevin Love, Backstage Interactive)

A release zip is not part of the git history. Build one with `bash scripts/build_release.sh` or `make release`. Output: `release/keyprose-release.zip`. The script packs tracked files and untracked files that are not gitignored. It excludes `.git`, `.env` and other env files, `*.db` / `*.sqlite` / `*.sqlite3`, `node_modules`, `__pycache__`, `.pytest_cache`, `.netlify`, and any zip already in `release/`. The old committed `release/listing-pilot.zip` was a stale archive and has been removed. Docs do not require a binary zip in git, so the replacement is the script.

## Checklist

### GitHub

1. Open `https://github.com/K-Love/keyprose/settings`.
2. Under **Danger Zone**, transfer the repository to the buyer.
3. Buyer clones the new remote and runs the tests in [INSTALLATION.md](INSTALLATION.md).

A fork plus deleting the original is a weaker handoff. Transfer the repo if the buyer should own the history and the issues.

After the transfer, update the GitHub link in `frontend/privacy.html` (`https://github.com/K-Love/keyprose`) and any clone URLs you publish. That edit is a content change to the privacy page. Make it when you update the operator identity, not before.

### Netlify

The production site name is `keyprose`. The default URL is https://keyprose.netlify.app. A buyer may rename the site. Only that .netlify.app address changes. Custom domains keep working.

**Transfer the site** to the buyer's Netlify team if both sides can do that in the Netlify UI. The site keeps its settings, environment variables, and domain attachments. Then rotate every secret (next section). The buyer confirms the publish directory is still `frontend` and that `netlify.toml` is the config the site uses.

**Or create a new site** from the transferred repo. Set the publish directory to `frontend`, leave the build command empty, set environment variables, deploy, and attach the domains. The new site can have any name. `keyprose` can be left in place until DNS has moved, then deleted so it does not keep serving the domains.

`netlify/functions/api.mjs` is the hosted API. Losing the Netlify site does not lose the Python server in `backend/server.py`.

### Domains at Porkbun

`keyprose.com` and `keyprose.app` are both registered at Porkbun. Transfer or repoint each one.

- **Keep Porkbun.** Update DNS so the names point at the buyer's Netlify site, or at another host. `www.keyprose.com` should redirect to `https://keyprose.com`. That www redirect is a DNS or host setting. It is not in `netlify.toml`. `keyprose.app` and `www.keyprose.app` redirect to `https://keyprose.com`, and the path and query string stay on the URL. Those rules are at the top of `frontend/_redirects`. Netlify reads that file before `netlify.toml`. The same four rules are repeated at the top of `netlify.toml`.
- **Move to another registrar.** Unlock the domain at Porkbun, copy the authorization (EPP) code, and start the transfer at the new registrar. Do this separately for `keyprose.com` and `keyprose.app`. ICANN lets the registrar refuse a transfer for 60 days after registration or after a previous transfer. A change to the registrant contact can start that same lock. Wait out the window if it applies. DNS can move with the domain or stay where it is. The website host is whatever the DNS records point at, which can be Netlify or something else.

### Keys

Rotate anything the old operator can still see.

- `OPENAI_API_KEY` in the Netlify site (every deploy context) and in any shell or host environment the buyer uses. Create a new key at the provider. Revoke the old one. The code reads the name `OPENAI_API_KEY` even when the host is not OpenAI. Set `AI_BASE_URL` and `AI_MODEL` for the buyer's host.
- Netlify personal access tokens and the Netlify login on the old account.
- Porkbun account access, and the registrar lock once a transfer finishes.
- GitHub access for the previous owner. Remove the old account from the repo after the transfer.

Do not send key values in email, in this repo, or inside `keyprose-release.zip`.

### Privacy and Terms

`frontend/privacy.html` and `frontend/terms.html` are the legal pages. They say "I" is Kevin Love and that he runs the site as Backstage Interactive, a one-person studio. Contact is the form on backstageinteractive.com. The privacy page also links to `https://github.com/K-Love/keyprose` and describes the AI host as Abacus RouteLLM on November 7, 2026.

Rewrite the operator name, the studio name, the contact path, and the GitHub link so they match the buyer. Read the provider and hosting sentences again after you choose a host and an AI vendor.

The footers and the rest of the UI stay as they are until you choose to edit them.

## After transfer

```bash
python3 -m pip install -r backend/requirements.txt
python3 -m pytest backend/tests/
npm ci
node --test netlify/api.test.mjs
python3 backend/server.py
```

`GET /api/health` should return `ai_mode` of `demo` until the buyer's key is set, then `live`.

Read [../docs/ONBOARDING.md](../docs/ONBOARDING.md) and [../docs/README.md](../docs/README.md).

## Limits the buyer should hear

- No accounts, no billing, no saved customer listings. `scripts/seed_db.sh` writes a local SQLite file the app never opens. The filename is now `keyprose.db`. An existing `listing_pilot.db` is still the file the script updates when `keyprose.db` does not exist.
- The public Netlify API accepts partial JSON: a listing body only needs `property_details` to be an object, and the other tools only require one or two keys. Missing fields become generic defaults. Truncated JSON is rejected. The Python server is stricter and returns 422 for a missing required field.
- Sample copy adds generic lines the user did not type, including extra home features, Austin social wording, stand-in email details, and a fixed market sentence on the CMA.
- Drafts are not sent, posted, or filed with an MLS. CMA output is not an appraisal.
