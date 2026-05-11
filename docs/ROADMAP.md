# Roadmap

Design-Prototype is a browser-based enterprise validation lab for client
readiness, endpoint visibility, macOS compliance, certificate risk, and
operator handoff workflows.

## Current release

Latest release: `0.1.3` - Public presentation polish

## v0.1.4 - Prototype hardening

Goal: make the main prototypes easier to validate, explain, and safely reuse.

### Documentation

- [ ] Add one short use-case page per main prototype.
- [ ] Add one architecture diagram for the overall repo.
- [ ] Add sample data documentation.
- [ ] Add safe sharing examples.
- [ ] Add helper-agent troubleshooting notes.

### Prototype quality

- [ ] Verify all dashboard links from GitHub Pages.
- [ ] Add fallback/demo-data notes inside each dashboard.
- [ ] Improve empty states and helper-offline states.
- [ ] Add visible version/footer marker to public pages.

### Tools

- [ ] Add smoke test for helper scripts.
- [ ] Add quick command reference for MQ Mirror.
- [ ] Add sample report output for MQ Client Optimizer.
- [ ] Add validation command for public docs.

### Release readiness

- [ ] `tools/check-public-docs.py` passes.
- [ ] README links are valid.
- [ ] GitHub Pages deploy is successful.
- [ ] CHANGELOG has a clear release entry.
- [ ] No private/local data is committed.

## Later ideas

- Turn demo gallery into richer visual case studies.
- Add comparison screenshots before/after helper data is connected.
- Add GitHub Actions check for public docs.
- Add lightweight test coverage for Python helper tools.
