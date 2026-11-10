"""
Tests for the Email Generator AI module.
All tests run in offline/deterministic mode (no API key required).
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("OPENAI_API_KEY", None)

from ai.email_generator import generate_emails, email_prompt, _fill_template


SAMPLE_CONTEXT = {
    "first_name": "John",
    "agent_name": "Sarah Johnson",
    "agent_phone": "(512) 555-0100",
    "address": "123 Maple Street, Austin, TX",
    "beds": 4,
    "baths": 3,
    "sqft": "2,400",
    "price": 650000,
    "highlight": "stunning pool and chef's kitchen",
    "market_condition": "seller's market",
    "open_house_date": "Saturday, July 20th at 2 PM",
}


class TestFillTemplate:
    def test_basic_fill(self):
        result = _fill_template("Hello {first_name}!", {"first_name": "Alice"})
        assert result == "Hello Alice!"

    def test_missing_key_uses_default(self):
        result = _fill_template("Hello {first_name}!", {})
        assert "there" in result  # default first_name

    def test_price_formatting(self):
        result = _fill_template("Price: ${price:,}", {"price": 650000})
        assert "650,000" in result


class TestGenerateEmails:
    def test_buyer_sequence(self):
        emails = generate_emails("buyer", SAMPLE_CONTEXT)
        assert isinstance(emails, list)
        assert len(emails) > 0

    def test_seller_sequence(self):
        emails = generate_emails("seller", SAMPLE_CONTEXT)
        assert len(emails) > 0

    def test_investor_sequence(self):
        ctx = {**SAMPLE_CONTEXT, "cap_rate": "6.5"}
        emails = generate_emails("investor", ctx)
        assert len(emails) > 0

    def test_past_client_sequence(self):
        emails = generate_emails("past_client", SAMPLE_CONTEXT)
        assert len(emails) > 0

    def test_cold_lead_sequence(self):
        ctx = {**SAMPLE_CONTEXT, "median_price": 485000, "avg_dom": 18, "inventory_level": "low"}
        emails = generate_emails("cold_lead", ctx)
        assert len(emails) > 0

    def test_email_has_required_fields(self):
        emails = generate_emails("buyer", SAMPLE_CONTEXT)
        for email in emails:
            assert "subject" in email
            assert "body" in email
            assert "recipient_type" in email
            assert "sequence_step" in email

    def test_subject_is_string(self):
        emails = generate_emails("buyer", SAMPLE_CONTEXT)
        for email in emails:
            assert isinstance(email["subject"], str)
            assert len(email["subject"]) > 5

    def test_body_contains_agent_name(self):
        emails = generate_emails("buyer", SAMPLE_CONTEXT)
        # At least one email should mention the agent name
        bodies = " ".join(e["body"] for e in emails)
        assert "Sarah Johnson" in bodies

    def test_unknown_recipient_type_falls_back(self):
        emails = generate_emails("unknown_type_xyz", SAMPLE_CONTEXT)
        assert isinstance(emails, list)
        assert len(emails) > 0

    def test_sequence_steps_ordered(self):
        emails = generate_emails("buyer", SAMPLE_CONTEXT)
        steps = [e["sequence_step"] for e in emails]
        assert steps == sorted(steps)

    def test_supplied_specs_stay_in_demo_copy(self):
        emails = generate_emails("buyer", SAMPLE_CONTEXT, num_emails=1)
        body = emails[0]["body"]
        assert "4 Bedrooms" in body
        assert "3 Bathrooms" in body
        assert "2,400 Sq Ft" in body

    def test_omitted_specs_are_not_invented(self):
        emails = generate_emails(
            "buyer",
            {"first_name": "Alex", "agent_name": "Sam Lee", "address": "9 Oak Lane", "price": 410000},
            num_emails=1,
        )
        body = emails[0]["body"]
        assert "9 Oak Lane" in body
        assert "2,400" not in body
        assert "1,800" not in body
        assert "4 bedroom" not in body.lower()
        assert "3 bathroom" not in body.lower()


class TestEmailPrompt:
    def test_prompt_has_no_sample_property(self):
        context = {
            "first_name": "Alex",
            "agent_name": "Sam Lee",
            "address": "9 Oak Lane",
            "highlight": "garden",
        }
        prompt = email_prompt("buyer", context, 2, 1, 0)
        assert "9 Oak Lane" in prompt
        assert "garden" in prompt
        assert "4bd/3ba" not in prompt
        assert "2,400" not in prompt
        assert "2400" not in prompt
        assert "4-bedroom" not in prompt.lower()
        assert "Do not invent bedrooms" in prompt

    def test_prompt_keeps_only_the_caller_details(self):
        prompt = email_prompt(
            "buyer",
            {"address": "9 Oak Lane", "beds": 2, "baths": 1, "sqft": 900},
            1,
            1,
            0,
        )
        assert "9 Oak Lane" in prompt
        assert "900" in prompt
        assert "4bd/3ba" not in prompt
        assert "2,400" not in prompt
        assert "2400" not in prompt

    def test_live_prompt_is_the_email_prompt(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        seen = {}

        def fake_generate(prompt, max_tokens=512, system_message=None, temperature=0.7):
            seen["prompt"] = prompt
            return "Subject: Hello\n\nHi Alex."

        monkeypatch.setattr("ai.email_generator.generate_text", fake_generate)
        context = {"first_name": "Alex", "address": "9 Oak Lane", "highlight": "garden"}
        emails = generate_emails("buyer", context, num_emails=1)
        assert emails[0]["subject"] == "Hello"
        assert seen["prompt"] == email_prompt("buyer", context, 1, 1, 0)
        assert "4bd/3ba" not in seen["prompt"]
        assert "2,400" not in seen["prompt"]
        assert "2400" not in seen["prompt"]
