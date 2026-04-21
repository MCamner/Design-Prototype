# Design Prototype

**Web App Prototypes for Enterprise Client Platforms**  
Author: Mattias Camner

---

## 🚀 Overview

This repository contains a collection of **interactive web-based prototypes** used to design, validate, and demonstrate client-side platform concepts.

Focus areas include:

- Client readiness validation
- Endpoint baseline verification
- Citrix / VDI environments
- Thin client platforms (IGEL OS12, eLux)
- Browser-based diagnostic tooling

These prototypes are built to run directly in the browser — including **restricted environments like thin clients**.

---

## 🧠 Why this exists

Most enterprise environments struggle with:

- Unknown client state
- Inconsistent configurations
- Lack of visibility before accessing critical services (e.g. Citrix)

This repo explores a different approach:

👉 **Move validation to the client**  
👉 **Run lightweight checks in-browser**  
👉 **Generate immediate readiness feedback**

---

## 🧩 Key Prototypes

### Client Readiness Check (v2)

A browser-based diagnostic tool that evaluates whether a client meets a defined baseline.

**Capabilities:**
- Detect environment (browser / client type)
- Validate endpoint connectivity
- Check helper services (local agents)
- Evaluate baseline compliance
- Generate structured output (JSON / TXT)

**Example use cases:**
- IGEL OS12 Citrix validation
- eLux client verification
- Pre-access checks before VDI launch

---

### Fleet Command Center (Concept)

A prototype for aggregating multiple client states into a centralized view.

**Goal:**
- Provide visibility across distributed endpoints
- Identify readiness gaps at scale
- Support operational decision-making

---

## ⚙️ How it works

The prototypes are:

- Static web apps (HTML + JS)
- Config-driven (JSON profiles)
- Designed for portability (no backend required)

Example flow:

1. Load prototype in browser
2. Detect environment
3. Execute checks (endpoints / helper / config)
4. Evaluate against baseline
5. Output readiness result

---

## 🔌 Configuration

Client readiness is driven by external configuration:

- `client-readiness-config.json`
- `profiles/index.json`

Supports:

- Multiple client profiles (IGEL, eLux, macOS, kiosk)
- Custom endpoints
- Timeout handling
- URL overrides (query parameters)

---

## 🧪 Example

```bash
/client-readiness-v2.html?profile=igel-os12-citrix
```

---

## 🎯 Design Principles

- **Zero install** — runs in browser
- **Environment aware** — adapts to client type
- **Config-driven** — no hardcoded logic
- **Portable** — works in locked-down environments
- **Observable** — produces structured output

---

## 📁 Repository Structure

```
docs/
  client-readiness-v2.html
  evaluator.js
  client-readiness-config.v2.json
  profiles/
    index.json

helper/
  fleet_collector.py
  fleet_clients.json
```

---

## 🔭 Future Direction

- Certificate visibility & validation
- Smartcard detection & state handling
- Network diagnostics (LAN / WiFi)
- Integration with local helper agents
- Fleet-level analytics

---

## 🧭 Positioning

This is not a finished product.

It is a **design and architecture exploration** of:

👉 Client-side validation in enterprise environments  
👉 Browser-based diagnostics in restricted platforms  
👉 Baseline-driven endpoint control  

---

## 📌 Related Work

- macos-scripts → unified CLI workflows  
- zephyr-workbench → architecture modelling (YAML-driven)

---

## 📄 License

MIT License
