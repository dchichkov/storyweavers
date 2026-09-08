"""Common conditional realization. Catalogs are data; the runtime selects text.

    {name:ada}       an existing entity's display name
    {phrase:box.mark} a complete, explicitly authored phrase for this state value

No raw-value fallback. Cards select against a precise before/after state; their
tested/bound facts are retained for auditing. Free words still need semantic QA.
"""
import json
import re
from runtime import Condition, holds, StoryError

SLOT = re.compile(r"\{(name|phrase):([^{}]+)\}")


def lint(text):
    defects = []
    if re.search(r"\b[a-z]+_[a-z_]+\b", text):
        defects.append("literal_state_value")
    if re.search(r"\bor did not\b|\bshe said, or\b|\bhe said, or\b|—or the |\b(?:TODO|TBD)\b", text):
        defects.append("unresolved_alternative")
    if re.search(r"\b(\w{4,})\s+\1\b", text, re.I):
        defects.append("repeated_word")
    if "{" in text or "}" in text:
        defects.append("unresolved_slot")
    return defects


def render_book(run, rng, book):
    sections = {s["scene"]: s for s in book["scenes"]}
    if len(sections) != len(book["scenes"]):
        raise StoryError("Duplicate prose scene")
    lexicon = {(x["key"], json.dumps(x["value"], sort_keys=True)): x["text"] for x in book["lexicon"]}
    paragraphs, bridge = [], None

    def card(cards, event, kind):
        time = 0 if kind == "beginning" else event["id"]
        current = run["initial"] if time == 0 else event["after"]
        before = run["initial"] if time <= 1 else run["events"][time - 2]["after"]
        points = {"initial": (0, run["initial"]), "before": (max(0, time - 1), before), "after": (time, current)}
        eligible = []
        for option in cards:
            facts, ok = [], True
            for cond in option["when"]:
                at, state = points[cond["at"]]
                if not holds(state, (Condition(cond["key"], cond["op"], cond["value"]),)):
                    ok = False
                    break
                facts.append(dict(at=at, key=cond["key"], value=state[cond["key"]]))
            if ok:
                eligible.append((len(option["when"]), option, facts))
        if not eligible:
            keys = {c['key'] for option in cards for c in option['when']}
            values = {name: {k: state.get(k) for k in keys} for name, (_, state) in points.items()}
            raise StoryError(f"No eligible prose card: {kind}/{event['scene'] if event else 'opening'}; tested state: {values}")
        most_specific = max(item[0] for item in eligible)
        _, option, facts = rng.choice([x for x in eligible if x[0] == most_specific])

        def bind(match):
            typ, key = match.groups()
            if typ == "name":
                if key not in run["entities"]:
                    raise StoryError(f"Unknown entity placeholder: {key}")
                return run["entities"][key]["name"]
            if key not in current:
                raise StoryError(f"Unknown phrase state: {key}")
            signature = (key, json.dumps(current[key], sort_keys=True))
            if signature not in lexicon:
                raise StoryError(f"Missing grammatical realization: {signature}")
            facts.append(dict(at=time, key=key, value=current[key]))
            return lexicon[signature]

        text = SLOT.sub(bind, option["text"])
        defects = lint(text)
        if defects:
            raise StoryError(f"Prose defects {defects}: {text[:200]}")
        return dict(text=text, event_ids=[] if time == 0 else [time], kind=kind, facts=facts)

    paragraphs.append(card(book["openings"], None, "beginning"))
    for event in run["events"]:
        if event["scene"] not in sections:
            raise StoryError(f"Missing prose for scene {event['scene']}")
        section = sections[event["scene"]]
        paragraph = card(section["variants"], event, "scene")
        if section["role"] == "bridge":
            if bridge is None:
                bridge = paragraph
            else:
                bridge["text"] += " " + paragraph["text"]
                bridge["event_ids"] += paragraph["event_ids"]
                bridge["facts"] += paragraph["facts"]
        else:
            if bridge:
                paragraphs.append(bridge)
                bridge = None
            paragraphs.append(paragraph)
    if bridge:
        paragraphs.append(bridge)
    paragraphs.append(card(book["endings"], run["events"][-1], "ending"))
    return paragraphs
