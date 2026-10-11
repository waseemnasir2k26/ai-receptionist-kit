# Platform shape reference

**Last reviewed: 2026-10-12.** Written offline from public documentation as understood on that date. This project makes no calls to any platform API, so none of these shapes has been validated against a live account by the kit. Platform schemas change; always validate in your own account (create the assistant in a draft or test workspace first) before pointing a real phone number at it.

Generated files are annotation-rich: every config includes a top-level `metadata` object (`built_with`, `kit_version`, `trade`, `price_policy`, `recording_rule`, `languages`). The linter reads `price_policy`, `recording_rule` and `trade` from it. If a platform rejects unknown fields, delete `metadata` before submitting; the linter then falls back to its defaults (price policy `never`, two-party recording).

## Replace before use

| Placeholder                                    | Where                                 | What to do                                                              |
| ---------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------- |
| `REPLACE_WITH_VOICE_ID` / `REPLACE_WITH_VOICE` | voice field per platform              | Pick a voice available on your account.                                 |
| `REPLACE_WITH_LLM_ID`                          | Retell `agent.response_engine.llm_id` | Create the `llm` object first, then paste its id.                       |
| `https://your-n8n-host.example.com/...`        | tool server URL                       | Your own webhook (see `n8n/booking-webhook.json`).                      |
| `+15555550100`                                 | transfer number                       | A real E.164 number that a human answers 24/7 for emergencies. Test it. |

## Vapi (`build --platform vapi`)

Output: one assistant object.

- `firstMessage`: greeting, includes the AI disclosure and, for two-party rule, the recording line.
- `model.messages[0]`: the system prompt. `model.tools[]`: `function` tools with a `server.url`, and a `transferCall` tool (function name `transfer_to_human`) with `destinations[].number`.
- `transcriber.language`: `en`, or `multi` when more than one language is configured.
- `recordingEnabled`: false when the intake rule is `none`.
- Tool responses are expected as `{ "results": [ { "toolCallId": "...", "result": "..." } ] }` with single-line string results. `n8n/booking-webhook.json` does exactly that.

## Retell (`build --platform retell`)

Output: `{ "llm": {...}, "agent": {...}, "metadata": {...} }`, the two objects you create separately.

- `llm.general_prompt`, `llm.begin_message`, `llm.general_tools[]`: `custom` tools (with `url`), a `transfer_call` tool named `transfer_to_human`, and an `end_call` tool.
- `agent.response_engine` points at the LLM id you receive after creating the `llm` object. `agent.language`: `en-US` or `multi`.

## Bland (`build --platform bland`)

Output: one request body.

- `task` (the prompt), `first_sentence`, `tools[]` with `url`, `method`, `body`, `input_schema`; `transfer_phone_number` handles human transfer (so `transfer_to_human` has no custom-tool entry; the linter counts a set `transfer_phone_number` as that tool's schema).
- `language`: `en-US` or `babel` for multi-language. `record` is false when the rule is `none`.
- The custom-tool `body` template uses `{{input}}`; confirm the exact templating your Bland version expects.

## Known gaps

- Voices, models and provider names (`openai gpt-4o`, `deepgram nova-2`, `11labs`) are defaults, not recommendations.
- Phone numbers, SIP, compliance registration (for example outbound calling rules) and billing are out of scope.
- The tool-call responder only implements demo behaviour.
