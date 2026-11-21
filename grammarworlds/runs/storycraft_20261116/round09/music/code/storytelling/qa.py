"""Reading questions grounded in selected text and its semantic event trace.

This handles our generated stories, not arbitrary external English. No prose
parser or model invents an answer. Evidence offsets are checked against the
exact story; changing the text invalidates its semantic alignment.
"""
import hashlib


def questions(row, limit=6):
    if limit < 0:
        raise ValueError("QA limit cannot be negative")
    story = row["story"]
    if hashlib.sha256(story.encode()).hexdigest() != row["text_sha256"]:
        raise ValueError("story changed; regenerate its text/semantic alignment")
    available, seen = [], set()
    history = {e["id"]: e for e in row["final_world"]["history"]}
    by_key = {}
    for s in row["scenes"]:
        if story[s["start"]:s["end"]] != s["text"]:
            raise ValueError("QA evidence does not match story text")
        event = history[s["event_id"]]
        if not event["narrated"] or event["sentence"] != s["text"]:
            raise ValueError("QA scene is not a narrated world event")
        for c in s["claims"]:
            if c["key"] in by_key:
                raise ValueError("ambiguous semantic evidence key")
            by_key[c["key"]] = (s, c)
    def support_closure(key, path=()):
        if key in path:
            raise ValueError("cyclic semantic evidence")
        if key not in by_key:
            return None
        item = by_key[key]
        if not set(item[1]["entities"]) <= row["final_world"]["entities"].keys():
            raise ValueError("QA mentions an unknown carrier")
        closure = {key: item}
        for dependency in item[1].get("supports", ()):
            nested = support_closure(dependency, (*path, key))
            if nested is None:
                return None
            closure.update(nested)
        return closure

    for s in row["scenes"]:
        for c in s["claims"]:
            if c.get('evidence_only'):
                continue  # Retained in by_key for full transitive evidence.
            if c["key"] in seen:
                continue
            if not set(c["entities"]) <= row["final_world"]["entities"].keys():
                raise ValueError("QA mentions an unknown carrier")
            seen.add(c["key"])
            closure = support_closure(c["key"])
            if closure is None:
                continue  # Every transitive premise must also be visibly supported.
            supporting = list(closure.values())
            evidence_scenes = {item["event_id"]: item for item in [s] + [x[0] for x in supporting]}
            entities = sorted(set(c["entities"]).union(*(set(x[1]["entities"]) for x in supporting)))
            available.append(dict(id=f"{row['scenario']}:{s['event_id']}:{c['key']}",
                kind=c["kind"], question=c["question"], answer=c["answer"],
                entity_ids=entities, event_ids=sorted(evidence_scenes),
                evidence=[dict(start=e["start"], end=e["end"], text=e["text"])
                          for e in sorted(evidence_scenes.values(), key=lambda e: e["start"])],
                text_sha256=row["text_sha256"]))
    if 'beats' in row['final_world'].get('narrative',{}):
        from ..beat_qa import questions as beat_questions
        available=beat_questions(row)+available
    # Cover question kinds before adding another question of the same kind.
    # State-changing branches deserve a question even if another who/what came first.
    available.sort(key=lambda c: 0 if c["id"].rsplit(":", 1)[-1] in {"atlas", "design", "outcome", "respect"} else 1)
    selected, kinds = [], set()
    for candidate in available:
        if candidate["kind"] not in kinds and len(selected) < limit:
            selected.append(candidate)
            kinds.add(candidate["kind"])
    selected_ids = {c["id"] for c in selected}
    selected += [c for c in available if c["id"] not in selected_ids][:max(0, limit - len(selected))]
    return selected
