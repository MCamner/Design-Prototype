# Architecture Diagram

Design-Prototype uses a browser-first prototype model: most public demos are
static HTML files with embedded demo data, while optional local helper agents
provide live endpoint or fleet signals.

```mermaid
flowchart LR
  user[Operator or reviewer]
  pages[GitHub Pages / docs index]
  demos[Static HTML prototypes]
  helper[Local helper agents]
  fleet[Fleet collector]
  tools[Local tools]
  output[Dashboard, report, or handoff view]

  user --> pages
  pages --> demos
  demos --> output
  helper --> demos
  helper --> fleet
  fleet --> demos
  tools --> output

  subgraph Local helper ports
    macos[macOS Agent :38764]
    client[Client Readiness Agent :38765]
    collector[Fleet Collector :38766]
    mirror[MQ Mirror :7070]
    optimizer[MQ Client Optimizer :38865]
  end

  helper --> macos
  helper --> client
  fleet --> collector
  tools --> mirror
  tools --> optimizer
```

## Read path

1. A reviewer opens the GitHub Pages front door or a local HTML file.
2. The prototype loads bundled demo data by default.
3. If a helper endpoint is reachable, the dashboard can use live data.
4. Operators use the visible status, checks, and recommendations for triage or
   handoff.

## Safety boundary

Public docs, screenshots, and GitHub issues should use demo data or redacted
helper output. Live helper responses can include hostnames, usernames, IP
addresses, certificate subjects, and serial numbers.
