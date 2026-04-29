import os
import re
import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify, render_template

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

app = Flask(__name__)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
client = None
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
USE_OPENAI = os.environ.get("USE_OPENAI", "true").lower() not in {"0", "false", "no", "off"}

if USE_OPENAI and OPENAI_API_KEY:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

COMPONENT_PATTERNS = [
    r"\b[A-Za-zÅÄÖåäö0-9.+#]+-(?:frontend|backend|api|server|cache)\b",
    r"\b[A-ZÅÄÖ][A-Za-zÅÄÖåäö0-9.+#/-]*(?:\s+[A-ZÅÄÖ][A-Za-zÅÄÖåäö0-9.+#/-]*){0,2}\s+(?:frontend|backend|API|Service|Server|Gateway|Database|Cache|CDN|Queue|Broker)\b",
    r"\bAPI(?::t)?\b",
    r"\b(?:React|Next\.js|Vue|Angular|Node\.js|Express|FastAPI|Django|Flask|API Gateway|PostgreSQL|MySQL|MongoDB|Redis|RabbitMQ|Kafka|Stripe|SendGrid|S3|AWS S3|CloudFront|Azure|GitHub Actions|Kubernetes|Docker|ECR|Slack|JWT|bcrypt)\b",
    r"\b[A-ZÅÄÖ][A-Za-zÅÄÖåäö0-9.+#/-]*(?:\s+(?:Service|API|Gateway|Database|Cache|CDN|Queue|Broker))\b",
]

RELATION_WORDS = [
    "pratar med",
    "kommunicerar med",
    "använder",
    "hämtar data från",
    "skriver till",
    "läser från",
    "pushar till",
    "skickar till",
    "via",
    "framför",
    "bakom",
    "till",
]

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
    if diagram_type in {"auto", "flowchart"}:
        items = extract_flow_steps(description)
        if not items:
            items = ["Start", description[:80] or "Diagram", "Slut"]
        return flowchart_xml(items)

    components, relations = extract_architecture(description)
    if not components:
        components = extract_flow_steps(description) or [description[:80] or "Diagram"]
    return architecture_xml(components, relations)


def extract_flow_steps(description):
    parts = re.split(r"(?:\n+|(?<=[.!?])\s+|[;:]+|\s+-\s+)", description)
    cleaned = []
    for part in parts:
        text = re.sub(r"\s+", " ", part).strip(" -")
        if text:
            cleaned.append(text[:80])
    return cleaned[:10]


def extract_architecture(description):
    components = []
    relations = []

    for pattern in COMPONENT_PATTERNS:
        for match in re.finditer(pattern, description):
            add_component(components, clean_component(match.group(0)))

    for sentence in re.split(r"(?:\n+|(?<=[.!?])\s+|[;]+)", description):
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if not sentence:
            continue

        sentence_components = components_in_text(sentence, components)
        for component in sentence_components:
            add_component(components, component)

        relations.extend(extract_sentence_relations(sentence, sentence_components, components))

        if not relations and len(sentence_components) >= 2 and not any_relation_for_sentence(relations, sentence_components):
            for source, target in zip(sentence_components, sentence_components[1:]):
                relations.append((source, target, ""))

    if len(components) < 2:
        components = extract_fallback_components(description)

    if not relations and len(components) >= 2:
        relations = [(source, target, "") for source, target in zip(components, components[1:])]

    components, relations = collapse_generic_api(components, relations)

    return components[:14], unique_relations(relations, components[:14])


def add_component(components, name):
    if not name or len(name) < 2:
        return
    normalized = normalize_name(name)
    for index, item in enumerate(components):
        existing = normalize_name(item)
        if normalized == existing:
            return
        if normalized != "api" and existing != "api" and existing in normalized:
            components[index] = name[:60]
            return
        if normalized != "api" and existing != "api" and normalized in existing:
            return
    components.append(name[:60])


def clean_component(value):
    for word in RELATION_WORDS:
        value = re.split(rf"\b{re.escape(word)}\b", value, maxsplit=1, flags=re.I)[0]
    value = re.split(r"(?<=[.!?])\s+", value, maxsplit=1)[0]
    value = re.split(r"\b(?:för|inkluderar|include|includes|med|som)\b|[;:]", value, maxsplit=1, flags=re.I)[0]
    value = re.sub(r":t\b", "", value, flags=re.I)
    value = re.sub(r"\b(?:en|ett|the|a|an|och|som|med|för|via|i|på|till|från)\b$", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" ,:-.")
    return value


def normalize_name(value):
    return re.sub(r"[^a-z0-9åäö]+", "", value.lower())


def components_in_text(text, known_components):
    found = []

    for component in known_components:
        if re.search(rf"\b{re.escape(component)}\b", text, flags=re.I):
            add_component(found, component)

    for pattern in COMPONENT_PATTERNS:
        for match in re.finditer(pattern, text):
            add_component(found, clean_component(match.group(0)))

    return found


def extract_sentence_relations(sentence, sentence_components, all_components):
    relations = []
    if len(sentence_components) < 2:
        return relations

    lowered = sentence.lower()
    for word in RELATION_WORDS:
        if word not in lowered:
            continue

        pieces = re.split(rf"\b{re.escape(word)}\b", sentence, maxsplit=1, flags=re.I)
        if len(pieces) != 2:
            continue

        left = nearest_component(pieces[0], sentence_components, prefer_last=True)
        right_components = components_in_text(pieces[1], all_components + sentence_components)
        if not right_components:
            right_components = split_component_list(pieces[1])

        for right in right_components:
            add_component(all_components, right)
            if left and left != right:
                label = "" if word in {"till", "via"} else word
                relations.append((left, right, label))

    if "bakom" in lowered and len(sentence_components) >= 2:
        relations.append((sentence_components[0], sentence_components[1], "bakom"))

    return relations


def nearest_component(text, components, prefer_last=False):
    matches = []
    for component in components:
        match = list(re.finditer(re.escape(component), text, flags=re.I))
        if match:
            matches.append((match[-1].start(), component))
    if not matches:
        return components[-1] if prefer_last and components else (components[0] if components else None)
    matches.sort()
    return matches[-1][1] if prefer_last else matches[0][1]


def split_component_list(text):
    pieces = re.split(r",|\boch\b|\bsamt\b", text, flags=re.I)
    components = []
    for piece in pieces:
        name = clean_component(piece)
        name = re.sub(r"^(?:tre|två|flera)\s+", "", name, flags=re.I)
        if 2 <= len(name) <= 60 and len(name.split()) <= 5:
            components.append(name)
    return components[:6]


def extract_fallback_components(description):
    items = []
    for item in extract_flow_steps(description):
        for part in split_component_list(item):
            add_component(items, part)
    return items[:10]


def any_relation_for_sentence(relations, sentence_components):
    sentence_set = {normalize_name(component) for component in sentence_components}
    for source, target, _ in relations:
        if normalize_name(source) in sentence_set and normalize_name(target) in sentence_set:
            return True
    return False


def unique_relations(relations, components):
    component_names = {normalize_name(component): component for component in components}
    unique = []
    seen = set()
    for source, target, label in relations:
        source_key = normalize_name(source)
        target_key = normalize_name(target)
        if source_key == target_key or source_key not in component_names or target_key not in component_names:
            continue
        key = (source_key, target_key, label)
        if key not in seen:
            unique.append((component_names[source_key], component_names[target_key], label))
            seen.add(key)
    return unique[:18]


def collapse_generic_api(components, relations):
    api_target = None
    for component in components:
        lowered = component.lower()
        if component != "API" and "api" in lowered and "gateway" not in lowered:
            api_target = component
            break

    if not api_target or "API" not in components:
        return components, relations

    collapsed_components = [component for component in components if component != "API"]
    collapsed_relations = []
    for source, target, label in relations:
        collapsed_relations.append((
            api_target if source == "API" else source,
            api_target if target == "API" else target,
            label,
        ))

    return collapsed_components, collapsed_relations


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


def architecture_xml(items, relations=None):
    relations = relations or []
    model, root = diagram_root()
    node_ids = {}
    next_id = 2
    lane_counts = {}

    for index, item in enumerate(items):
        lane = component_lane(item)
        lane_index = lane_counts.get(lane, 0)
        lane_counts[lane] = lane_index + 1
        x = 70 + lane_index * 270
        y = 70 + lane * 145
        style = component_style(item)

        node = cell(root, next_id, item, style, vertex=True)
        geometry(node, x=x, y=y, width=230, height=76)
        node_ids[normalize_name(item)] = next_id
        next_id += 1

    if not relations:
        relations = [(source, target, "") for source, target in zip(items, items[1:])]

    for source, target, label in relations:
        source_id = node_ids.get(normalize_name(source))
        target_id = node_ids.get(normalize_name(target))
        if not source_id or not target_id:
            continue

        edge = cell(
            root,
            next_id,
            label,
            "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;",
            edge=True,
            source=source_id,
            target=target_id,
        )
        geometry(edge, relative=1)
        next_id += 1

    return ET.tostring(model, encoding="unicode")


def component_lane(item):
    lowered = item.lower()
    if any(word in lowered for word in ["frontend", "react", "next", "vue", "angular", "client", "webb"]):
        return 0
    if any(word in lowered for word in ["postgres", "mysql", "mongodb", "redis", "databas", "database", "db", "cache"]):
        return 2
    if any(word in lowered for word in ["stripe", "sendgrid", "slack", "s3", "cloudfront", "extern", "external", "cdn"]):
        return 3
    return 1


def component_style(item):
    lowered = item.lower()
    if any(word in lowered for word in ["postgres", "mysql", "mongodb", "databas", "database", "db"]):
        return "shape=mxgraph.flowchart.database;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
    if any(word in lowered for word in ["redis", "cache"]):
        return "shape=mxgraph.flowchart.database;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
    if any(word in lowered for word in ["stripe", "sendgrid", "slack", "aws", "azure", "s3", "cloudfront", "extern", "external", "cdn"]):
        return "shape=cloud;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
    if any(word in lowered for word in ["gateway", "api"]):
        return "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
    if any(word in lowered for word in ["queue", "broker", "rabbitmq", "kafka"]):
        return "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
    return "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"


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

    if not USE_OPENAI or client is None:
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
