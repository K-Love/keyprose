"""HTTP demo API: FastAPI routes and the Netlify function handler."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient

import server
from demo_http import handle_api, normalize_path

client = TestClient(server.app)

LISTING = {
    "property_details": {
        "address": "123 Maple Street, Austin, TX 78701",
        "beds": 4,
        "baths": 3,
        "sqft": 2400,
        "price": 650000,
        "neighborhood": "South Congress",
        "features": ["pool", "chef's kitchen"],
    },
    "tone": "luxury",
    "length": "short",
}

COMPS = {
    "address": "456 Oak Avenue, Austin, TX 78702",
    "comps": [
        {
            "address": "100 Maple St",
            "price": 635000,
            "sqft": 2350,
            "beds": 4,
            "baths": 3,
            "sold_date": "2025-05-15",
        }
    ],
}


def test_health_demo_mode(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["ai_mode"] == "demo"
    assert body["provider_host"] == "api.openai.com"
    assert "api_key" not in body


def test_homepage_links_every_tool():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    for path in ("/tools/listing", "/tools/cma", "/tools/social", "/tools/email", "/tools/outreach"):
        assert path in html
    assert "https://github.com/K-Love/listing-pilot" in html
    assert "KeyProse" in html
    assert "the AI back office for listing agents" in html
    assert "Real Estate AI" not in html
    assert "Business-in-a-Box" not in html
    assert "</html>" in html.lower()


@pytest.mark.parametrize(
    "path",
    ["/tools/listing", "/tools/cma", "/tools/social", "/tools/email", "/tools/outreach"],
)
def test_tool_pages_render(path):
    response = client.get(path)
    assert response.status_code == 200
    assert "<form" in response.text or "generate" in response.text.lower()


LEGAL_LINKS = ('href="/privacy"', 'href="/terms"')
FORBIDDEN_POLICY_CLAIMS = (
    "never store",
    "never stored",
    "not used for training",
    "do not train",
    "zero data retention",
    "encrypted at rest",
    "binding arbitration",
    "Edmonds",
    "GDPR",
    "CCPA",
    "$100",
)


def test_legal_pages_and_navigation():
    home = client.get("/")
    assert home.status_code == 200
    for link in LEGAL_LINKS:
        assert link in home.text
    assert 'rel="canonical" href="https://keyprose.com/"' in home.text

    for path in ("/tools/listing", "/tools/cma", "/tools/social", "/tools/email", "/tools/outreach"):
        page = client.get(path)
        assert page.status_code == 200
        for link in LEGAL_LINKS:
            assert link in page.text

    privacy = client.get("/privacy")
    terms = client.get("/terms")
    assert privacy.status_code == 200
    assert terms.status_code == 200
    assert "Privacy Policy" in privacy.text
    assert "Terms of Use" in terms.text
    assert "November 7, 2026" in privacy.text
    assert "November 7, 2026" in terms.text
    assert "Kevin Love" in privacy.text
    assert "routellm.abacus.ai" in privacy.text
    assert "A lawyer has not reviewed" in privacy.text
    assert "A lawyer has not reviewed" in terms.text
    assert 'rel="canonical" href="https://keyprose.com/privacy"' in privacy.text
    assert 'rel="canonical" href="https://keyprose.com/terms"' in terms.text
    combined = (privacy.text + terms.text).lower()
    for claim in FORBIDDEN_POLICY_CLAIMS:
        assert claim.lower() not in combined

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "https://keyprose.com/privacy" in sitemap.text
    assert "https://keyprose.com/terms" in sitemap.text
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "https://keyprose.com/sitemap.xml" in robots.text


def test_unknown_page_uses_branded_404():
    response = client.get("/missing-page")
    assert response.status_code == 404
    assert "Page not found" in response.text


def test_listing_email_outreach_round_trip():
    listing = client.post("/api/listing-writer", json=LISTING)
    assert listing.status_code == 200
    assert "Maple" in listing.json()["listing_text"] or "bedroom" in listing.json()["listing_text"].lower()

    emails = client.post(
        "/api/email",
        json={
            "recipient_type": "buyer",
            "context": {"agent_name": "Sarah Johnson", "address": "123 Maple Street", "first_name": "Alex"},
            "num_emails": 2,
        },
    )
    assert emails.status_code == 200
    assert len(emails.json()["emails"]) == 2
    assert "Sarah Johnson" in emails.json()["emails"][0]["body"]

    outreach = client.post(
        "/api/outreach",
        json={
            "target_list": [{"name": "Alex Rivera", "email": "alex@example.com", "type": "buyer"}],
            "sequence_template": "open_house",
        },
    )
    assert outreach.status_code == 200
    body = outreach.json()
    assert body["status"] == "ready"
    assert body["total_contacts"] == 1
    assert "Alex Rivera" in body["preview"]


def test_cma_pdf_downloads():
    created = client.post("/api/cma", json=COMPS)
    assert created.status_code == 200
    payload = created.json()
    assert payload["estimated_value"] > 0
    assert payload["cma_pdf_url"]
    downloaded = client.get(payload["cma_pdf_url"])
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"%PDF")


def test_hosted_demo_function_is_javascript():
    """Netlify no longer deploys Python functions, so the public /api is JavaScript."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    source = open(os.path.join(root, "netlify", "functions", "api.mjs"), encoding="utf-8").read()
    assert "export default" in source
    assert 'path: "/api/*"' in source
    assert "AI_BASE_URL" in source or "readAiConfig" in source
    assert "chat/completions" in open(os.path.join(root, "netlify", "functions", "ai_provider.mjs"), encoding="utf-8").read()
    assert not os.path.exists(os.path.join(root, "netlify", "functions", "api.py"))


def test_normalize_path_accepts_function_splat():
    assert normalize_path("/.netlify/functions/api/listing-writer") == "/api/listing-writer"
    assert normalize_path("/api/health/") == "/api/health"


def test_handler_rejects_bad_listing_payload():
    result = handle_api("POST", "/api/listing-writer", {})
    assert result.status == 422
