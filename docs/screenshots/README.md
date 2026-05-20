# Screenshots

Use this folder for screenshots shown in the README, demo gallery, and GitHub Pages front door.

## Recommended files

```text
client-readiness-dashboard.png
fleet-command-center.png
macos-enterprise-dashboard.png
certificate-expiry-timeline.png
mq-fleet-report.png
mq-client-optimizer.png
mq-site-fix-advisor.png
mq-asset-downloader.png
mq-mirror.png
```

## macOS capture command

Interactive selection:

```bash
screencapture -i docs/screenshots/client-readiness-dashboard.png
```

Window capture:

```bash
screencapture -w docs/screenshots/client-readiness-dashboard.png
```

Clipboard to file:

```bash
pngpaste docs/screenshots/client-readiness-dashboard.png
```

If `pngpaste` is missing:

```bash
brew install pngpaste
```

## Screenshot checklist

```text
[ ] Browser zoom looks normal
[ ] No private tabs visible
[ ] No hostname/user/serial/IP visible
[ ] No tokens or .env values visible
[ ] Screenshot filename is lowercase and descriptive
[ ] Screenshot is linked from docs/DEMO-GALLERY.md
```

## Suggested flow

```bash
./tools/run-demo.sh client
screencapture -i docs/screenshots/client-readiness-dashboard.png

./tools/run-demo.sh fleet
screencapture -i docs/screenshots/fleet-command-center.png

./tools/run-demo.sh macos
screencapture -i docs/screenshots/macos-enterprise-dashboard.png
```
