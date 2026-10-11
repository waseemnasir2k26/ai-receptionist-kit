# Changelog

## 1.0.0 - 2026-10-12

First release.

- `init`, `build`, `lint`, `validate`, `validate-n8n`, `presets` commands. Python 3.10+, standard library only.
- Renderers for Vapi, Retell and Bland (assistant JSON, system prompt, four tool schemas).
- Six trade presets: plumber, hvac, electrician, dental, cleaning, roofer.
- Fifteen lint rules (RCP001 to RCP015), text and JSON output, exit codes for CI.
- Intake schema validation with all errors reported together.
- `n8n/booking-webhook.json` tool-call responder and a structural validator.
- pytest suite: golden files for 6 presets x 3 platforms, positive and negative fixture per rule, intake errors, responder shape (including a Node run of the n8n Code node when Node is installed).
- GitHub Actions workflow for Python 3.10 to 3.13 shipped as `docs/ci.yml`.
