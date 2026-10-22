"""Common conditional realization. Catalogs are data; the runtime selects text.

    {name:ada}       an existing entity's display name
    {phrase:box.mark} a complete, explicitly authored phrase for this state value

No raw-value fallback. Cards select against a precise before/after state; their
tested/bound facts are retained for auditing. Free words still need semantic QA.
"""
import json
import re
from copy import deepcopy
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
        paragraph = dict(text=text, event_ids=[] if time == 0 else [time], kind=kind, facts=facts)
        if 'dialogue' in option:
            from dialogue import QUOTES, collect_dialogue
            quotes = list(QUOTES.finditer(text)); annotations = []
            for entry in option['dialogue']:
                annotation = deepcopy(entry)
                indices = annotation.pop('quote_indices')
                if not indices or any(type(i) is not int or not 0 <= i < len(quotes) for i in indices):
                    raise StoryError('Invalid dialogue quote index')
                annotation['quotes'] = [dict(start=quotes[i].start()+1,end=quotes[i].end()-1) for i in indices]
                if time: annotation['event_id'] = time
                annotations.append(annotation)
            paragraph['dialogue'] = annotations
            collect_dialogue(run,[paragraph])
        else:
            # Index explicit attributions BEFORE bridge concatenation, while the
            # originating event is still precise. This adds no model output.
            from dialogue import collect_dialogue
            records = collect_dialogue(run,[paragraph])
            if records:
                paragraph['dialogue'] = [dict(speaker=u['speaker'],listener=u['listener'],quotes=u['quotes'],
                                             event_id=u['event_id'],attribution=u['attribution']) for u in records]
        return paragraph

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
                offset = len(bridge['text'])+1
                # Preserve authored quote spans and replies when bridge cards join.
                if 'dialogue' in bridge or 'dialogue' in paragraph:
                    from dialogue import collect_dialogue
                    for part in (bridge,paragraph):
                        if 'dialogue' not in part:
                            part['dialogue'] = [dict(speaker=u['speaker'],listener=u['listener'],quotes=u['quotes'],
                                                     event_id=u['event_id'],attribution=u['attribution'])
                                                for u in collect_dialogue(run,[part])]
                    base = len(bridge['dialogue'])
                    for entry in paragraph['dialogue']:
                        entry = deepcopy(entry)
                        for span in entry['quotes']: span['start'] += offset; span['end'] += offset
                        if entry.get('reply_to') is not None: entry['reply_to'] += base
                        bridge['dialogue'].append(entry)
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
