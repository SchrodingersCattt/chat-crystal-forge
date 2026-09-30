# Model configuration

Status: implemented for the read-only chat/inspection preview. Configuration and
tool-calling unit tests exist; no live provider has been verified without locally
supplied credentials/model. Later preparation tools remain planned.

## Environment variables

Track a secret-free [`.env.example`](../.env.example). Users copy it to `.env` and
edit values locally. `.env` and `.env.*` are ignored, except `.env.example`.

| Variable | Meaning |
| --- | --- |
| `OPENAI_API_KEY` | Credential for the chosen endpoint; required if that endpoint requires authentication |
| `OPENAI_BASE_URL` | API root supplied by the provider, including `/v1` when applicable |
| `OPENAI_MODEL` | Provider-specific model ID / SKU / deployment name sent in requests |

The example uses `https://api.openai.com/v1` as an illustrative API root, not a
commitment to a provider. Key and model are intentionally blank. Do not hard-code
a model SKU or silently fall back to a different endpoint/model.

Use the same configuration in TUI and UI. An already-set process environment
variable takes precedence over `.env`; a local file must not overwrite credentials
injected by a server or scheduler. Load only the intended application's `.env`
from the launch directory, not arbitrary parent-directory files. Explicit paths
or per-project profiles can be considered later if needed.

## Compatibility and startup

Use an OpenAI-compatible chat/tool-calling interface. Compatibility is verified
against the configured endpoint, not inferred from a marketing label. Check that
the chosen model supports the tool-call request/response contract needed by the
workflow. Missing configuration and unsupported capability should produce an
actionable error, not an apparent successful run.

Prefer streaming responses when supported; a non-streaming response can use the
same execution and event path. Do not require optional reasoning, vision or
provider-specific APIs for the initial core. Structured tool arguments are still
validated locally, even if the endpoint offers a structured-output feature.

Treat the configured API root as authoritative. Do not append `/v1` twice or
assume every provider uses the same path. Permit local OpenAI-compatible endpoints
with their actual authentication requirements; do not send a cloud credential to
another provider as a fallback.

## Credential and data handling

- Model requests run in the TUI process or the UI backend, never directly from
  browser JavaScript with a server credential.
- Do not ask for keys in chat. Users enter them locally or through their deployment
  environment. Do not commit `.env`, authorization headers or credential-bearing URLs.
- Validate configured URLs; prefer HTTPS for hosted endpoints and use loopback HTTP
  only for intentional local setups. Do not silently disable TLS verification.
- Send only task-relevant information to the configured model service. Do not
  automatically upload unrelated files, whole research directories or raw credentials.
- Show which endpoint/model is active without exposing secrets. Redact credentials
  from errors and tool records; avoid dumping request headers or `.env` contents.
- Keep `.env.example` limited to empty credentials and non-secret examples. A Git
  ignore rule does not remove secrets already tracked in history.

When implemented, test environment precedence, blank required values, local
endpoint behavior, tool-call capability errors, and secret-free error reporting.