import os
import re
import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
USE_OPENAI = os.environ.get("USE_OPENAI", "true").lower() not in {"0", "false", "no", "off"}

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


def local_diagram_xml(description, diagram_type):
    items = extract_items(description)
    if not items:
        items = ["Start", description[:80] or "Diagram", "Slut"]

    if diagram_type in {"auto", "flowchart"}:
        return flowchart_xml(items)

    return architecture_xml(items)


def extract_items(description):
    parts = re.split(r"(?:\n+|[.;:]+|\s+-\s+)", description)
    cleaned = []
    for part in parts:
        text = re.sub(r"\s+", " ", part).strip(" -")
        if text:
            cleaned.append(text[:80])
    return cleaned[:10]


def cell(root, cell_id, value="", style="", parent="1", vertex=None, edge=None, source=None, target=None):
    attrs = {"id": str(cell_id), "value": value, "style": style, "parent": parent}
    if vertex:
        attrs["vertex"] = "1"
    if edge:
        attrs["edge"] = "1"
    if source:
        attrs["source"] = str(source)
    if target:
        attrs["target"] = str(target)
    return ET.SubElement(root, "mxCell", attrs)


def geometry(parent, **attrs):
    attrs = {key: str(value) for key, value in attrs.items()}
    attrs["as"] = "geometry"
    return ET.SubElement(parent, "mxGeometry", attrs)


def diagram_root():
    model = ET.Element("mxGraphModel", {
        "dx": "1422",
        "dy": "762",
        "grid": "1",
        "gridSize": "10",
        "guides": "1",
        "tooltips": "1",
        "connect": "1",
        "arrows": "1",
        "fold": "1",
        "page": "1",
        "pageScale": "1",
        "pageWidth": "1169",
        "pageHeight": "827",
        "math": "0",
        "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    return model, root


def flowchart_xml(items):
    model, root = diagram_root()
    previous_id = None
    next_id = 2
    x = 390
    y = 60

    for index, item in enumerate(items):
        style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        if index == 0:
            style = "ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
        elif index == len(items) - 1:
            style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"

        node = cell(root, next_id, item, style, vertex=True)
        geometry(node, x=x, y=y, width=320, height=70)

        if previous_id is not None:
            edge = cell(
                root,
                next_id + 1,
                "",
                "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;",
                edge=True,
                source=previous_id,
                target=next_id,
            )
            geometry(edge, relative=1)
            next_id += 1

        previous_id = next_id
        next_id += 1
        y += 120

    return ET.tostring(model, encoding="unicode")


def architecture_xml(items):
    model, root = diagram_root()
    node_ids = []
    next_id = 2

    for index, item in enumerate(items):
        row = index // 3
        col = index % 3
        style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        lowered = item.lower()
        if any(word in lowered for word in ["db", "database", "databas", "postgres", "mysql", "redis"]):
            style = "shape=mxgraph.flowchart.database;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
        elif any(word in lowered for word in ["extern", "external", "api", "stripe", "sendgrid", "aws", "azure"]):
            style = "shape=cloud;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"

        node = cell(root, next_id, item, style, vertex=True)
        geometry(node, x=80 + col * 350, y=80 + row * 160, width=240, height=80)
        node_ids.append(next_id)
        next_id += 1

    for source, target in zip(node_ids, node_ids[1:]):
        edge = cell(
            root,
            next_id,
            "",
            "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;",
            edge=True,
            source=source,
            target=target,
        )
        geometry(edge, relative=1)
        next_id += 1

    return ET.tostring(model, encoding="unicode")


def openai_error_response(error):
    code = getattr(error, "code", None)
    status_code = getattr(error, "status_code", 500)

    if code == "insufficient_quota":
        return jsonify({
            "error": (
                "OpenAI-kontot saknar API-quota. Kontrollera billing, credits "
                "och usage limits på https://platform.openai.com/settings/organization/billing."
            )
        }), 402

    if status_code == 401:
        return jsonify({"error": "OpenAI API-nyckeln är ogiltig eller saknar åtkomst."}), 401

    if status_code == 429:
        return jsonify({"error": "OpenAI rate limit nåddes. Vänta en stund och försök igen."}), 429

    return jsonify({"error": str(error)}), status_code


@app.route("/")
def index():
    return render_template("index.html", diagram_types=DIAGRAM_TYPES)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    diagram_type = data.get("diagram_type", "auto")

    if not description:
        return jsonify({"error": "Beskrivning saknas"}), 400

    if diagram_type not in DIAGRAM_TYPES:
        return jsonify({"error": "Okänd diagramtyp"}), 400

    if not USE_OPENAI or not os.environ.get("OPENAI_API_KEY"):
        return jsonify({
            "xml": local_diagram_xml(description, diagram_type),
            "source": "local",
        })

    type_hint = ""
    if diagram_type != "auto":
        type_hint = f"\n\nDiagramtyp att använda: {DIAGRAM_TYPES[diagram_type]}"

    user_message = f"{description}{type_hint}"

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=SYSTEM_PROMPT,
            input=user_message,
            max_output_tokens=8096,
        )

        xml_content = (response.output_text or "").strip()

        # Strip markdown code fences if the model included them anyway.
        if xml_content.startswith("```"):
            lines = xml_content.split("\n")
            xml_content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        if not xml_content.startswith("<mxGraphModel"):
            return jsonify({"error": "Kunde inte generera giltigt draw.io XML"}), 500

        return jsonify({"xml": xml_content})

    except Exception as e:
        if getattr(e, "code", None) == "insufficient_quota":
            return jsonify({
                "xml": local_diagram_xml(description, diagram_type),
                "source": "local",
                "warning": "OpenAI-kontot saknar quota, så ett enklare lokalt diagram genererades.",
            })
        return openai_error_response(e)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
