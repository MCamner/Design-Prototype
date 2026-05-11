#!/usr/bin/env python3
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
README = ROOT / "README.md"

errors = []
warnings = []

required_files = [
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "LICENSE",
    "docs/index.html",
    "docs/DEMO-GALLERY.md",
    "docs/PROJECT-MAP.md",
    "docs/PROJECT-STATUS.md",
]

required_screenshots = [
    "docs/screenshots/client-readiness-dashboard.png",
    "docs/screenshots/fleet-command-center.png",
    "docs/screenshots/macos-enterprise-dashboard.png",
    "docs/screenshots/certificate-expiry-timeline.png",
    "docs/screenshots/mq-client-optimizer.png",
    "docs/screenshots/mq-mirror.png",
]


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def exists(path):
    return (ROOT / path).exists()


print("Design-Prototype public docs check")
print("==================================")

for file in required_files:
    if not exists(file):
        fail(f"Missing required file: {file}")

for file in required_screenshots:
    if not exists(file):
        fail(f"Missing screenshot: {file}")

if README.exists():
    readme = README.read_text(errors="ignore")

    required_readme_terms = [
        "Start here",
        "Demo Catalog",
        "Safe sharing",
        "Quick Start",
        "Project navigation",
    ]

    for term in required_readme_terms:
        if term not in readme:
            fail(f"README missing section/text: {term}")

    if "Interactive web prototypes and macOS developer tools." in readme:
        warn("README still contains old generic positioning sentence.")

if (DOCS / "DEMO-GALLERY.md").exists():
    gallery = (DOCS / "DEMO-GALLERY.md").read_text(errors="ignore")
    if "Needs screenshot" in gallery:
        warn("DEMO-GALLERY still contains 'Needs screenshot' markers.")


def collect_links(path):
    text = path.read_text(errors="ignore")
    links = []

    if path.suffix.lower() in [".html", ".htm"]:
        links.extend(re.findall(r'href="([^"]+)"', text))
        links.extend(re.findall(r'src="([^"]+)"', text))

    if path.suffix.lower() == ".md":
        links.extend(re.findall(r'\[[^\]]+\]\(([^)]+)\)', text))

    return links


check_files = [
    README,
    DOCS / "index.html",
    DOCS / "DEMO-GALLERY.md",
    DOCS / "PROJECT-MAP.md",
    DOCS / "PROJECT-STATUS.md",
]

for file in check_files:
    if not file.exists():
        continue

    base = file.parent

    for link in collect_links(file):
        if not link:
            continue

        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue

        clean = link.split("#", 1)[0]
        clean = clean.split("?", 1)[0]

        if not clean:
            continue

        target = (base / unquote(clean)).resolve()

        try:
            target.relative_to(ROOT)
        except ValueError:
            warn(f"{file.relative_to(ROOT)} links outside repo: {link}")
            continue

        if not target.exists():
            fail(f"Broken local link in {file.relative_to(ROOT)}: {link}")

if warnings:
    print()
    print("Warnings")
    print("--------")
    for item in warnings:
        print(f"- {item}")

if errors:
    print()
    print("Errors")
    print("------")
    for item in errors:
        print(f"- {item}")
    print()
    print("Result: FAIL")
    sys.exit(1)

print()
print("Result: OK")
