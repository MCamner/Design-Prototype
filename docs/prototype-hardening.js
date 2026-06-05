(function () {
  const VERSION = "0.1.4";
  const path = decodeURIComponent(window.location.pathname.split("/").pop() || "");
  const titles = {
    "Client Readiness Dashboard.html": "Client Readiness Dashboard",
    "Fleet Command Center.html": "Fleet Command Center",
    "macOS Enterprise Dashboard.html": "macOS Enterprise Dashboard",
    "Certificate Expiry Timeline.html": "Certificate Expiry Timeline",
    "MQ Fleet Report.html": "MQ Fleet Report",
    "MQ Client Optimizer.html": "MQ Client Optimizer",
    "MQ Asset Downloader.html": "MQ Asset Downloader",
    "MQ Site Fix Advisor.html": "MQ Site Fix Advisor",
    "handoff.html": "MQ Mirror",
    "handoff-standalone.html": "MQ Mirror standalone handoff",
    "index.html": "Design Prototype"
  };

  if (document.querySelector("[data-prototype-hardening]")) return;

  const title = titles[path] || document.title || "Design Prototype";
  const usesHelper = !["MQ Asset Downloader.html", "MQ Site Fix Advisor.html", "MQ Fleet Report.html", "index.html"].includes(path);

  const style = document.createElement("style");
  style.textContent = `
    .prototype-hardening {
      margin: 28px auto 0;
      padding: 14px 18px;
      max-width: 1120px;
      color: #d7def6;
      background: rgba(10, 15, 30, 0.82);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 8px;
      font: 13px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .prototype-hardening strong { color: #ffffff; }
    .prototype-hardening code {
      color: #a9c8ff;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .prototype-hardening-footer {
      margin-top: 8px;
      color: rgba(215, 222, 246, 0.72);
      font-size: 12px;
    }
  `;

  const note = document.createElement("aside");
  note.className = "prototype-hardening";
  note.setAttribute("data-prototype-hardening", "true");
  note.innerHTML = `
    <strong>${escapeHtml(title)}</strong> uses bundled demo data when live helper data is unavailable.
    ${usesHelper ? "If a helper is offline, the prototype stays usable with sample values and should not be treated as live endpoint evidence." : "Use pasted input, sample content, or static report data for public demos."}
    <div class="prototype-hardening-footer">Design Prototype v${VERSION} · public demo marker · review live data before sharing</div>
  `;

  document.body.appendChild(style);
  document.body.appendChild(note);

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char];
    });
  }
})();
