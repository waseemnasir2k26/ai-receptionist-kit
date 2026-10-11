// Minimal tool-call responder for the AI receptionist tools.
// DEMO LOGIC ONLY: replace the handle() bodies with your calendar / CRM calls.
// Input: Vapi-style server message (message.toolCallList or message.toolCalls).
// Output: { results: [ { toolCallId, result } ] } where result is a single-line string.
function handle(name, args) {
  if (name === "check_availability") {
    const svc = args.service_type || "service";
    return (
      "Open windows for " +
      svc +
      ": morning and afternoon slots are available. Offer the caller at most two options."
    );
  }
  if (name === "book_appointment") {
    return (
      "Booking request recorded for " +
      (args.customer_name || "the caller") +
      ". The team will confirm by text."
    );
  }
  if (name === "transfer_to_human") {
    return "Transfer requested.";
  }
  if (name === "log_lead") {
    return "Lead logged.";
  }
  return "Unknown tool: " + name;
}

const first = $input.first().json || {};
const body = first.body || first;
const msg = body.message || body;
let calls = Array.isArray(msg.toolCallList) ? msg.toolCallList : [];
if (!calls.length && Array.isArray(msg.toolCalls)) {
  calls = msg.toolCalls.map((c) => ({
    id: c.id,
    name: c.function && c.function.name,
    arguments: c.function && c.function.arguments,
  }));
}
const results = [];
for (const c of calls) {
  if (!c || !c.id) continue;
  let args = c.arguments || {};
  if (typeof args === "string") {
    try {
      args = JSON.parse(args);
    } catch (e) {
      args = {};
    }
  }
  results.push({ toolCallId: c.id, result: handle(c.name, args) });
}
return [{ json: { results } }];
