import os
import json
from flask import Flask, request, jsonify, render_template
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert at generating draw.io (diagrams.net) XML diagrams from natural language descriptions.

When given a description of a technical solution, architecture, process, or system, you MUST respond with ONLY valid draw.io XML — no explanation, no markdown, no code fences, just the raw XML.

The XML must follow the mxGraph format used by draw.io:
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    ... diagram elements ...
  </root>
</mxGraphModel>

Diagram type guidelines based on description:
- Architecture/system overview → use rounded rectangles, cylinders for databases, clouds for external services
- Process/workflow → flowchart with diamonds for decisions, rectangles for steps
- UML class diagram → class boxes with compartments for attributes and methods
- Sequence diagram → use swimlanes with lifelines and arrows
- ER diagram → entity boxes with relationship lines
- Network diagram → use network icons and connection lines

Style guidelines:
- Use sensible spacing: minimum 40px between elements
- Group related elements visually
- Use colors sparingly: blue (#dae8fc) for processes, green (#d5e8d4) for success/output, yellow (#fff2cc) for decisions, red (#f8cecc) for errors/problems, gray (#f5f5f5) for external systems
- Use appropriate font size (typically 14px)
- Keep labels concise
- Ensure the diagram fits on an A4 landscape page (1169x827)

Common styles:
- Rectangle: rounded=1;whiteSpace=wrap;html=1;
- Diamond: rhombus;whiteSpace=wrap;html=1;
- Cylinder (DB): shape=mxgraph.flowchart.database;whiteSpace=wrap;html=1;
- Cloud: shape=cloud;whiteSpace=wrap;html=1;
- Arrow: edgeStyle=orthogonalEdgeStyle;
- Swimlane: swimlane;

Always use sequential numeric IDs starting from 2 (0 and 1 are reserved).
Generate IDs like: "2", "3", "4", etc.

IMPORTANT: Output ONLY the XML, nothing else. Do not include ```xml or ``` markers."""

DIAGRAM_TYPES = {
    "auto": "Välj automatiskt baserat på beskrivningen",
    "flowchart": "Flödesdiagram",
    "architecture": "Systemarkitektur",
    "uml_class": "UML Klassdiagram",
    "sequence": "Sekvensdiagram",
    "er": "ER-diagram",
    "network": "Nätverksdiagram",
}


@app.route("/")
def index():
    return render_template("index.html", diagram_types=DIAGRAM_TYPES)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    description = data.get("description", "").strip()
    diagram_type = data.get("diagram_type", "auto")

    if not description:
        return jsonify({"error": "Beskrivning saknas"}), 400

    type_hint = ""
    if diagram_type != "auto":
        type_hint = f"\n\nDiagramtyp att använda: {DIAGRAM_TYPES[diagram_type]}"

    user_message = f"{description}{type_hint}"

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        xml_content = message.content[0].text.strip()

        # Strip markdown code fences if Claude included them anyway
        if xml_content.startswith("```"):
            lines = xml_content.split("\n")
            xml_content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        if not xml_content.startswith("<mxGraphModel"):
            return jsonify({"error": "Kunde inte generera giltigt draw.io XML"}), 500

        return jsonify({"xml": xml_content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
