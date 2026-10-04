# Standalone CrystalForge API

CrystalForge's competition service is independent of `mattervis-saas`. It
owns session storage, model configuration and the read-only Forge workflow.
MatterVis is used only through the pinned upstream package/submodule selected by
this repository.

Install the optional API surface:

```bash
python -m pip install -e external/molcryskit -e "external/mattervis[web]" -e ".[api]"
mat-chat serve --host 127.0.0.1 --port 8051
```

Endpoints:

- `GET /healthz`
- `POST /v1/sessions`
- `GET /v1/sessions/{id}`
- `POST /v1/sessions/{id}/inputs` with multipart `file`
- `POST /v1/sessions/{id}/messages` with `{ "text": "..." }`
- `POST /v1/sessions/{id}/inspect`
- `DELETE /v1/sessions/{id}`

Set `FORGE_API_KEY` to require `X-API-Key`. Set `FORGE_ROOT` to a writable
volume for SQLite sessions and registered CIF copies. The service exposes no
MatterVis SaaS routes and does not import the `mattervis-saas` package.

