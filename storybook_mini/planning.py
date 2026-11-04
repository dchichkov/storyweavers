"""Map semantic roles and simulated carrier state to typed protosentences."""
from __future__ import annotations
from dataclasses import dataclass
from .lexicon import LEXICON, Verb
from .model import Snapshot


@dataclass(frozen=True)
class Clause:
    fact_id: str
    scene: str
    predicate: str
    subject: str
    object: str = ""
    target: str = ""
    complement: str = ""
    quote: str = ""
    cause: str = ""
    cue: str = ""
    verb: Verb | None = None
    goal: Clause | None = None
    speech: Clause | None = None
    listener: str = ""
    tense: str = "past"
    negative: bool = False
    contrast: str = ""
    topic: str = ""
    paragraph_break: bool = False
    owners: tuple = ()
    companion: str = ""


EMOTIONS = {"Fear": ("calm again", "uneasy", "afraid"),
            "Sadness": ("cheerful again", "disappointed", "miserable")}


def plan_sentences(snapshot: Snapshot):
    def plan(f, entry):
        if f["predicate"] not in LEXICON:
            raise ValueError(f"Unknown predicate: {f['predicate']}")
        verb = LEXICON[f["predicate"]][0]
        if bool(f["object"]) != verb.object_required:
            raise ValueError(f"{f['id']}: incorrect object role for {f['predicate']}")
        if bool(f["target"]) != bool(verb.target_preposition):
            raise ValueError(f"{f['id']}: incorrect target role for {f['predicate']}")
        complement = f["value"] if f["predicate"] == "be" else ""
        if f["predicate"] == "feel":
            magnitude = entry["after"][f["subject"]]["memes"][f["value"]]
            complement = EMOTIONS[f["value"]][2 if magnitude >= 0.6 else 1 if magnitude >= 0.3 else 0]
        def child(data):
            if not data:
                return None
            return plan(dict(data, id=f["id"], scene=f["scene"], cause="", cue=""), entry)
        if f["predicate"] == "want" and not f.get("goal"):
            raise ValueError(f"{f['id']}: want requires a structured goal")
        if f["predicate"] == "say" and not (f["value"] or f.get("speech")):
            raise ValueError(f"{f['id']}: say requires an utterance")
        return Clause(f["id"], f["scene"], f["predicate"], f["subject"],
                      f["object"], f["target"], complement,
                      f["value"] if f["predicate"] == "say" else "",
                      f["cause"], f["cue"], goal=child(f.get("goal")),
                      speech=child(f.get("speech")), listener=f.get("listener", ""),
                      tense=f.get("tense", "past"), negative=f.get("negative", False),
                      contrast=f.get("contrast", ""), topic=f.get("topic", ""),
                      paragraph_break=f.get("paragraph_break", False),
                      owners=tuple((eid, s["physical"]["owner"]) for eid, s in entry["before"].items()
                                   if s["physical"].get("owner")), companion=f.get("companion", ""))
    return tuple(plan(entry["fact"], entry) for entry in snapshot.history)
