"""Export comparisons, blinded packets, and descriptive human-rating summaries."""
from collections import Counter
from dataclasses import asdict
import hashlib
from html import escape
import json
from pathlib import Path
import random
from statistics import mean, stdev

from .content import STORIES, EXTENDED_IDS
from .model import simulate
from .pipeline import VERSIONS, CONFIGS, generate
from .research_view import export_research
from .story_io import save_story


FACTORS = {
    "overall": "Quality as a short fairy tale",
    "style": "Appropriateness of the writing style",
    "grammaticality": "Grammar and sentence construction",
    "flow": "Connection and flow between sentences",
    "diction": "Appropriateness of word choices",
    "readability": "Ease of reading (A is easiest)",
    "logicality": "Logical ordering of events",
    "detail": "Appropriateness of the amount of detail",
    "believability": "Believability of character behavior",
}
GRADES = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
STYLE = """
:root {color-scheme:light} * {box-sizing:border-box} body {margin:0; background:#f5f2eb;
color:#202d35; font:17px/1.65 system-ui,sans-serif} main {max-width:1280px; margin:auto;
padding:40px 28px} h1 {font:700 40px/1.15 Georgia,serif; margin:12px 0} h2 {margin-top:40px}
.intro {max-width:850px} .grid {display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr));
gap:20px; align-items:start} article {background:white; border:1px solid #d8d4ca;
border-radius:12px; padding:24px} article p {font:19px/1.7 Georgia,serif}
.meta {font-size:13px; color:#51616a} .tag {font-size:13px; text-transform:uppercase;
letter-spacing:1px; color:#325f5b} table {border-collapse:collapse; width:100%; background:white}
th,td {padding:10px; text-align:left; border-bottom:1px solid #ddd} a {color:#225e68}
label {display:block; margin:8px 0} select,button,textarea {font:inherit; padding:7px}
textarea {width:100%; min-height:70px} button {background:#225e68; color:white; border:0;
border-radius:5px; cursor:pointer} details {margin-top:20px} @media(max-width:500px) {
main {padding:24px 14px} .grid {grid-template-columns:1fr} h1 {font-size:32px}}
"""


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def document(title, body, script=""):
    return (f'<!doctype html><html lang="en"><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)}</title><style>{STYLE}</style><main>{body}</main>{script}</html>')


def prose(text):
    return "".join(f"<p>{escape(p)}</p>" for p in text.split("\n\n"))


def all_outputs(story_ids=None, versions=None):
    # One simulation per story, shared across all five versions.
    story_ids = tuple(STORIES) if story_ids is None else tuple(story_ids)
    versions = tuple(VERSIONS) if versions is None else tuple(versions)
    if not story_ids or len(set(story_ids)) != len(story_ids) or any(s not in STORIES for s in story_ids):
        raise ValueError("Select distinct, known story IDs")
    if not versions or len(set(versions)) != len(versions) or any(v not in CONFIGS for v in versions):
        raise ValueError("Select distinct, known versions")
    snapshots = [simulate(STORIES[sid]) for sid in story_ids]
    return snapshots, [generate(s, v) for s in snapshots for v in versions]


def export_comparison(out, story_ids=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    snapshots, outputs = all_outputs(story_ids, CONFIGS)
    write_json(out / "content.json", [asdict(s) for s in snapshots])
    write_json(out / "traces.json", outputs)
    for snapshot in snapshots:
        save_story(out / f"{snapshot.story.id}.content.json", snapshot.story)
    body = ('<div class="tag">STORYBOOK mini · component ablations</div>'
            '<h1>Same events. Different prose.</h1><div class="intro">'
            f'<p>{len(snapshots)} original narrative streams, five main configurations, '
            'and separate marker/paragraph controls. Each stream has one fixed content trace.</p>'
            '<p>The counts below describe mechanics, not reader preference. No human ratings '
            'have been collected. This is an architectural mini reproduction, not the original system.</p>'
            '<p><a href="traces.json">Inspect all pipeline stages</a> · '
            '<a href="content.json">Inspect content and world states</a> · '
            '<a href="research.html">Read the expanded experiment</a></p></div>')
    lines = ["# Mechanical ablation report", "", "No human ratings collected. These are diagnostics, not quality scores.", "",
             "| Story | Version | Facts | Sentences | Words | Pronouns | Aggregations | Verb forms | Paragraphs | Markers |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for snapshot in snapshots:
        story = snapshot.story
        body += f"<h2>{escape(story.title)}</h2><div class='grid'>"
        for result in (r for r in outputs if r["story_id"] == story.id):
            version, m = result["version"], result["metrics"]
            file = f"{story.id}.{version}.txt"
            (out / file).write_text(result["text"] + "\n", encoding="utf-8")
            body += (f'<article><div class="tag">{escape(version.replace("_", " "))}</div>'
                     f'<div class="meta">{m["facts"]} facts · {m["sentences"]} sentences · '
                     f'{m["pronouns"]} pronouns · {m["aggregations"]} combinations</div>'
                     + prose(result["text"]) + f'<a href="{file}">Plain text</a></article>')
            lines.append(f'| {story.id} | {version} | ' + " | ".join(str(m[key]) for key in
                         ("facts", "sentences", "words", "pronouns", "aggregations", "verb_forms", "paragraphs", "markers")) + " |")
        body += "</div>"
    lines.extend(["", "All versions preserve each story's ordered fact IDs and content hash.",
                  "This checks structural coverage, not complete semantic equivalence of English.", ""])
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "comparison.html").write_text(document("STORYBOOK mini — comparison", body), encoding="utf-8")
    export_research(out, outputs)
    return outputs


def balanced_orders(n, count, seed):
    """Even-n Williams design: position and first-order carryover balance per n rows."""
    if n % 2 or count < 1:
        raise ValueError("Need an even stimulus count and positive participant count")
    base = [0]
    for i in range(1, n):
        base.append((i + 1) // 2 if i % 2 else n - i // 2)
    rng = random.Random(seed)
    labels = list(range(n))
    rng.shuffle(labels)
    rows = [[labels[(value + shift) % n] for value in base] for shift in range(n)]
    # Shuffle whole cycles; each completed cycle retains balance.
    result = []
    while len(result) < count:
        cycle = rows.copy()
        rng.shuffle(cycle)
        result.extend(cycle)
    return result[:count]


def participant_html(packet):
    body = (f'<div class="tag">Reading study · {packet["participant_id"]}</div>'
            f'<h1>{len(packet["items"])} readings</h1><p>Read in the order shown. Rate each version independently '
            'using A (best), B, C, D, or F (worst). Some stories repeat with different wording. '
            'Judge the prose you see; there is no correct ranking.</p>'
            '<p>Finish all nine ratings for each reading, then download your answers. '
            'Nothing is sent over the network. Keep this page open until you download; '
            'unsaved answers are lost when it closes.</p><form id="ratings">')
    for i, item in enumerate(packet["items"]):
        body += f'<h2>Reading {i + 1}</h2><article>' + prose(item["text"])
        for key, label in FACTORS.items():
            body += (f'<label>{escape(label)} <select required name="{item["item_id"]}:{key}">'
                     '<option value="">Choose</option>' + ''.join(f'<option>{g}</option>' for g in GRADES)
                     + '</select></label>')
        body += f'<label>Comments (optional)<textarea name="{item["item_id"]}:comments"></textarea></label></article>'
    body += '<p><button type="submit">Download completed ratings</button></p></form>'
    encoded = json.dumps(packet, ensure_ascii=True).replace("<", "\\u003c")
    script = """<script>
const packet = PACKET;
document.getElementById('ratings').addEventListener('submit', event => {
  event.preventDefault();
  const data = new FormData(event.target);
  for (const item of packet.items) {
    for (const factor of Object.keys(item.ratings)) item.ratings[factor] = data.get(item.item_id + ':' + factor);
    item.comments = data.get(item.item_id + ':comments');
  }
  const blob = new Blob([JSON.stringify(packet, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = packet.participant_id + '.json'; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
</script>""".replace("PACKET", encoded)
    return document("Reading study", body, script)


def make_study(out, participants=20, seed=2001, story_ids=EXTENDED_IDS):
    if participants < 1:
        raise ValueError("Participant count must be positive")
    _, outputs = all_outputs(story_ids)
    orders = balanced_orders(len(outputs), participants, seed)
    out = Path(out)
    # Never overwrite a packet set that may already have been distributed.
    out.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": 1, "seed": seed, "participants": {}, "factors": FACTORS,
                "grades": GRADES, "position_balanced": participants % len(outputs) == 0,
                "story_ids": list(story_ids), "versions": list(VERSIONS),
                "source_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(Path(__file__).parent.glob("*.py"))},
                "note": "Private condition key. Distribute only each participant's HTML file."}
    rng = random.Random(seed + 1)
    for n, order in enumerate(orders, 1):
        pid = f"p{n:02d}"
        packet = {"schema": 1, "participant_id": pid, "items": []}
        keys = {}
        for index in order:
            r = outputs[index]
            token = f"r{rng.getrandbits(64):016x}"
            keys[token] = {"story_id": r["story_id"], "version": r["version"],
                           "content_sha256": r["content_sha256"],
                           "text_sha256": hashlib.sha256(r["text"].encode()).hexdigest()}
            packet["items"].append({"item_id": token, "text": r["text"],
                                    "ratings": dict.fromkeys(FACTORS, ""), "comments": ""})
        manifest["participants"][pid] = keys
        (out / f"{pid}.html").write_text(participant_html(packet), encoding="utf-8")
    write_json(out / "private_manifest.json", manifest)
    return manifest


def summarize_ratings(manifest, responses):
    """Validate entire packets. Pair within participant/story, never treat 200 rows as independent."""
    cells, accepted = {}, set()
    for packet in responses:
        pid = packet["participant_id"]
        if packet.get("schema") != 1 or pid not in manifest["participants"] or pid in accepted:
            raise ValueError(f"Unknown, duplicate, or invalid participant: {pid}")
        key = manifest["participants"][pid]
        items = packet["items"]
        if Counter(i["item_id"] for i in items) != Counter(key.keys()):
            raise ValueError(f"{pid}: missing, extra, or duplicate readings")
        for item in items:
            info = key[item["item_id"]]
            if hashlib.sha256(item["text"].encode()).hexdigest() != info["text_sha256"]:
                raise ValueError(f"{pid}: altered stimulus text")
            ratings = item["ratings"]
            if set(ratings) != set(FACTORS) or any(g not in GRADES for g in ratings.values()):
                raise ValueError(f"{pid}: each reading needs all nine A/B/C/D/F ratings")
            for factor, grade in ratings.items():
                cells[pid, info["story_id"], info["version"], factor] = GRADES[grade]
        accepted.add(pid)
    if not accepted:
        return {"participants": 0, "status": "No human ratings supplied; no quality conclusions."}
    # Identify design from the frozen key, not from today's regenerated stories.
    design = next(iter(manifest["participants"].values()))
    stories = sorted({r["story_id"] for r in design.values()})
    versions = list(manifest.get("versions", VERSIONS))
    means, contrasts = {}, {}
    for story in stories + ["pooled"]:
        selected = stories if story == "pooled" else [story]
        means[story], contrasts[story] = {}, {}
        for version in versions:
            means[story][version] = {factor: round(mean(cells[p, s, version, factor]
                for p in accepted for s in selected), 4) for factor in FACTORS}
            if version == "full":
                continue
            contrasts[story][version] = {}
            for factor in FACTORS:
                deltas = [mean(cells[p, s, "full", factor] - cells[p, s, version, factor]
                               for s in selected) for p in sorted(accepted)]
                contrasts[story][version][factor] = {
                    "full_minus_ablated": round(mean(deltas), 4),
                    "participant_sd": round(stdev(deltas), 4) if len(deltas) > 1 else None,
                    "n_participants": len(deltas)}
    return {"participants": len(accepted), "status": "Descriptive human results; no significance test.",
            "means": means, "paired_contrasts": contrasts,
            "limitations": "Small authored content family; repeated exposure; no population-level claim."}


def evaluate(study_dir, responses_dir):
    manifest = json.loads((Path(study_dir) / "private_manifest.json").read_text(encoding="utf-8"))
    responses = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(responses_dir).glob("*.json"))]
    return summarize_ratings(manifest, responses)
