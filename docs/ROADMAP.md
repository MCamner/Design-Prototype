# Roadmap

Design-Prototype is a browser-based enterprise validation lab for client
readiness, endpoint visibility, macOS compliance, certificate risk, and
operator handoff workflows.

## Current release

Latest release: `0.1.4` - Prototype hardening metadata and public presentation polish

## v0.1.5 - Prototype hardening

Goal: make the main prototypes easier to validate, explain, and safely reuse.

Status checked: 2026-06-05. Local hardening work is complete for `v0.1.5`.

### Documentation

- [x] Add one short use-case page per main prototype.
- [x] Add architecture documentation for the overall repo.
- [x] Add a visual architecture diagram for the overall repo.
- [x] Add sample data documentation.
- [x] Add safe sharing examples.
- [x] Add helper-agent troubleshooting notes.

### Prototype quality

- [x] Verify all dashboard links from GitHub Pages.
- [x] Add fallback/demo-data notes inside each dashboard.
- [x] Improve empty states and helper-offline states.
- [x] Add consistent visible version/footer marker to public pages.

### Tools

- [x] Add smoke test for helper scripts.
- [x] Add quick command reference for MQ Mirror.
- [x] Add sample report output for MQ Client Optimizer.
- [x] Add validation command for public docs.

### Release readiness

- [x] `tools/check-public-docs.py` passes.
- [x] README links are valid.
- [x] GitHub Pages deploy is successful.
- [x] CHANGELOG has a clear release entry.
- [x] No private/local data is committed.

Verification:

- `python3 tools/check-public-docs.py` passes.
- `bash tools/check-frontdoor.sh` passes.
- `bash tools/smoke-check.sh` passes.
- GitHub Pages front door and main dashboard URLs returned `HTTP/2 200`.
- Demo sample data was sanitized to use documentation IP ranges and demo serials.

## Later ideas

- Turn demo gallery into richer visual case studies.
- Add comparison screenshots before/after helper data is connected.
- Add GitHub Actions check for public docs.
- Add lightweight test coverage for Python helper tools.
