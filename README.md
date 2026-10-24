# AI Receptionist Kit

**Fill in one `business.json`, get a ready-to-paste AI phone receptionist config for Vapi, Retell and Bland, then lint it for the mistakes that cost you calls.**

![License: MIT](https://img.shields.io/badge/license-MIT-green.svg) ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg) ![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

![Lint report for a deliberately bad receptionist prompt](docs/lint-report.svg)

The image is generated from the real CLI output of `ai-receptionist-kit lint examples/bad-prompt.md`.

## What it does

- `init --preset <trade>` writes a starter `business.json` (plumber, hvac, electrician, dental, cleaning, roofer) with emergency keywords, FAQs, qualifying questions and hours.
- `build ... --platform vapi|retell|bland|all` writes `assistant.json`, `prompt.md` and `tools.json` per platform.
- Four tool schemas: `check_availability`, `book_appointment`, `transfer_to_human`, `log_lead`.
- `lint` runs 15 rules (RCP001 to RCP015): missing emergency escalation, price promises, no human fallback, no recording consent, claiming to be human, missing capture of name/phone/address, promised arrival times, medical advice and more.
- `validate` reports every problem in `business.json` at once (bad time zone, non-E.164 number, unknown keys).
- `n8n/booking-webhook.json` is a responder for tool calls, with a structural validator.
- pytest golden-file tests cover 6 presets x 3 platforms.

## Quickstart

```bash
git clone https://github.com/waseemnasir2k26/ai-receptionist-kit
cd ai-receptionist-kit
pip install -e .            # or run everything as: python -m kit ...
ai-receptionist-kit init --preset plumber --name "Sample Plumbing Co."
ai-receptionist-kit build business.json --platform all --out dist/
ai-receptionist-kit lint dist/vapi/assistant.json
```

Edit `business.json` (hours, service-area ZIPs, transfer number, price policy, recording-consent rule, languages), rebuild, lint, then paste the generated prompt and tools into your platform. Worked examples are in `examples/`.

## For you if

You set up voice agents for trades or local service businesses and want a repeatable config plus a safety check before the first live call.

## Status and limits

- The lint rules are regex heuristics. A clean result means the common mistakes are absent, not that the agent is safe. Test with real calls.
- Platform schemas change; check generated files against the current Vapi, Retell and Bland docs.
- Recording-consent rules vary by place. The kit does not give legal advice.
- Not published to PyPI; install from the clone.
- Last reviewed October 2026.

## Built by SkynetLabs

Built by [SkynetLabs](https://skynetjoe.com). Questions: info@skynetjoe.com

Need this wired into your business? SkynetLabs builds voice agents, n8n back offices and sites that convert → https://skynetjoe.com
