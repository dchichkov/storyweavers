#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swill_signature_storage_closet_sharing_space_adventure.py
==========================================================================================

A standalone story world for a small Space Adventure in a storage closet:
two kids share a cramped "spaceship" mission, a sticky swill spill threatens a
precious signature sheet, and a careful swap for sharing tools saves the day.

The world is intentionally tiny and classical:
- a few typed entities
- physical meters and emotional memes
- forward-chained causal rules
- state-driven prose
- grounded QA
- a Python reasonableness gate with an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    scene: str
    narrow: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    role: str
    thing: str
    fragile: bool = False
    shareable: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flags: dict[str, bool] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.flags = dict(self.flags)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_swill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["swill"] < THRESHOLD:
            continue
        sig = ("swill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "signature" in world.entities:
            world.get("signature").meters["smudged"] += 1
            out.append("__swill__")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    if not world.flags.get("shared_tools"):
        return out
    for kid in world.characters():
        if kid.role == "captain":
            kid.memes["joy"] += 1
        if kid.role == "mate":
            kid.memes["trust"] += 1
    out.append("__sharing__")
    return out


CAUSAL_RULES = [Rule("swill", "physical", _r_swill), Rule("sharing", "social", _r_sharing)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(swill: Item, signature: Item) -> bool:
    return swill.fragile and signature.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.get("cargo").meters["swill"] += 1
    _do_swill(sim, narrate=False)
    return {"smudged": sim.get("signature").meters["smudged"] >= THRESHOLD}


def _do_swill(world: World, narrate: bool = True) -> None:
    world.get("signature").meters["smudged"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"In the storage closet, {a.id} and {b.id} turned a stack of boxes into a tiny spacecraft."
    )
    world.say(
        "A broom became the antenna, a flashlight became the star map, and the closet door became the airlock."
    )


def need_sign(world: World, a: Entity, sig: Item) -> None:
    world.say(
        f"They needed {sig.phrase} to mark their mission, because every brave space crew kept a neat signature."
    )


def tempt(world: World, a: Entity, swill: Item) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"We can use the swill cup as a fuel drum," {a.id} said, pointing at the sticky {swill.label}.'
    )
    world.say("The idea sounded exciting for one second.")
    

def warn(world: World, b: Entity, a: Entity, sig: Item, swill: Item, parent: Entity) -> None:
    pred = predict_spill(world)
    b.memes["caution"] += 1
    world.facts["predicted_smudge"] = pred["smudged"]
    world.say(
        f'"No," {b.id} said. "If that swill tips over, it will smear the signature sheet."'
    )
    if pred["smudged"]:
        world.say(f'"Then {parent.label_word} would have to clean it, and the mission log would be ruined."')


def share_tools(world: World, a: Entity, b: Entity) -> None:
    world.flags["shared_tools"] = True
    a.memes["cooperation"] += 1
    b.memes["cooperation"] += 1
    world.say(
        f'Instead of grabbing the sticky cup, {a.id} slid the marker to {b.id} and asked to share the work.'
    )


def spill(world: World, swill: Item) -> None:
    swill.thing = "spilled"
    swill.label = "swill spill"
    world.get("cargo").meters["swill"] += 1
    _do_swill(world)
    world.say("Oops -- the swill tipped anyway, and a brown streak crawled toward the signature.")


def rescue(world: World, parent: Entity, response: Response, sig: Item) -> None:
    sig.meters["smudged"] = 0.0
    body = response.text
    world.say(f"{parent.label_word.capitalize()} came in fast and {body}.")
    world.say("The signature page stayed bright and the little spaceship stayed tidy.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, sig: Item) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say("For a moment, everyone watched the page and breathed out.")
    world.say(
        f'Then {parent.label_word.capitalize()} smiled. "Sharing is smart," {parent.pronoun()} said, '
        f'"because it keeps the {sig.label} safe and the crew calm."'
    )
    world.say(f'"We promise," whispered {a.id} and {b.id} together.')


def shared_finish(world: World, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        "After that, the two children shared the last clean marker and added stars around the signature."
    )
    world.say("Their closet spaceship floated on with a bright new crew mark, safe from the swill.")


def tell(setting: Setting, swill: Item, signature: Item, response: Response,
         captain: str = "Nia", captain_gender: str = "girl",
         mate: str = "Owen", mate_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World(setting)
    a = world.add(Entity(id=captain, kind="character", type=captain_gender, role="captain"))
    b = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    cargo = world.add(Entity(id="cargo", type="thing", label="the cargo box"))
    sw = world.add(Entity(id="swill", type="thing", label=swill.label, role="hazard"))
    sig = world.add(Entity(id="signature", type="thing", label=signature.label, role="goal"))
    world.facts["setting"] = setting
    world.facts["swill_cfg"] = swill
    world.facts["signature_cfg"] = signature
    world.facts["response"] = response
    world.facts["delay"] = delay

    setup(world, a, b)
    world.para()
    need_sign(world, a, signature)
    tempt(world, a, swill)
    warn(world, b, a, signature, swill, parent)
    world.para()
    if delay <= 0 and response.id == "quick_fix":
        share_tools(world, a, b)
        spill(world, sw)
        rescue(world, parent, response, sig)
        lesson(world, parent, a, b, sig)
        world.para()
        shared_finish(world, a, b)
        outcome = "contained"
    else:
        share_tools(world, a, b)
        if delay > 0:
            spill(world, sw)
        if is_contained(response, delay):
            rescue(world, parent, response, sig)
            lesson(world, parent, a, b, sig)
            world.para()
            shared_finish(world, a, b)
            outcome = "contained"
        else:
            world.say(
                f"{parent.label_word.capitalize()} tried to help, but the swill had already smeared the signature."
            )
            world.say("The crew cleaned the closet together and drew a fresh signature on a new page.")
            outcome = "messy"
    world.facts["outcome"] = outcome
    world.facts["instigator"] = a
    world.facts["cautioner"] = b
    world.facts["parent"] = parent
    world.facts["signature"] = sig
    world.facts["swill"] = sw
    return world


SETTINGS = {
    "closet": Setting("closet", "the storage closet", "a cramped storage closet full of boxes, ropes, and old lamps", True, {"storage", "closet"}),
}

ITEMS = {
    "swill": Item("swill", "swill cup", "a swill cup", "hazard", "swill", fragile=True, tags={"swill"}),
    "signature": Item("signature", "signature sheet", "a signature sheet", "goal", "signature", fragile=True, shareable=True, tags={"signature"}),
}

RESPONSES = {
    "quick_fix": Response("quick_fix", 3, 2, "wiped the swill away with a cloth before it could spread", "could not wipe the swill away in time", "wiped the swill away with a cloth", {"share", "cleanup"}),
    "careful_tray": Response("careful_tray", 2, 1, "slid the signature sheet onto a tray and moved the swill cup aside", "moved too slowly and the swill smeared the page", "slid the signature sheet onto a tray", {"share", "cleanup"}),
    "new_page": Response("new_page", 3, 3, "put the damaged page aside and started a fresh signature sheet", "reached for a new page, but the mess spread too fast", "started a fresh signature sheet", {"share", "cleanup"}),
}

NAMES_GIRL = ["Nia", "Maya", "Zoe", "Ava", "Lena", "Iris"]
NAMES_BOY = ["Owen", "Kai", "Leo", "Milo", "Noah", "Ezra"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for wid in ITEMS:
            for pid in ITEMS:
                if wid != pid and hazard_at_risk(ITEMS[wid], ITEMS[pid]):
                    combos.append((sid, wid, pid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    swill: str
    signature: str
    response: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a Space Adventure story set in a storage closet that includes the words "{f["swill_cfg"].label}" and "{f["signature_cfg"].label}".',
        f"Tell a child-friendly story where {f['instigator'].id} and {f['cautioner'].id} share tools in a cramped closet spaceship and protect the signature sheet.",
        "Write a story about sharing, a sticky swill spill, and a brave cleanup in a tiny storage-closet rocket.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    sig = f["signature_cfg"]
    sw = f["swill_cfg"]
    out = [
        ("Where does the story take place?",
         "It takes place in a storage closet that the children turn into a tiny spaceship. The cramped space makes the mission feel exciting and a little tricky."),
        ("What did the children want to protect?",
         f'They wanted to protect the {sig.label} so their mission could have a neat crew mark. A clean signature showed they had finished the space adventure together.'),
        ("Why did one child warn the other?",
         f'{b.id} warned {a.id} because the swill could tip and smear the {sig.label}. That would have made extra cleanup and spoiled the mission log.'),
    ]
    if f["outcome"] == "contained":
        out.append((
            "How did they solve the problem?",
            f"They shared the tools, kept the swill under control, and used {world.facts['response'].qa_text}. That let them keep the {sig.label} safe and finish together."
        ))
        out.append((
            "How did the story end?",
            "It ended with a clean signature and a tidy closet spaceship. The children were proud because sharing helped them finish safely."
        ))
    else:
        out.append((
            "What changed after the spill?",
            f"The {sig.label} got smudged, so the crew had to clean up and start a fresh page. Even then, they still shared the work and stayed together."
        ))
    return out


KNOWLEDGE = {
    "signature": [("What is a signature?",
                   "A signature is a special mark or name that shows who made or approved something. People sign papers to agree or to say they were there.")],
    "swill": [("What is swill?",
               "Swill is a sloppy liquid or leftover mixture that can splash or spill. It is messy and can stain paper or clothes.")],
    "sharing": [("What does sharing mean?",
                 "Sharing means using things together and taking turns. It helps people work as a team and feel fair and kind.")],
    "closet": [("What is a storage closet?",
               "A storage closet is a small room or space where boxes, supplies, and tools are kept.")],
    "spaceship": [("What is a spaceship?",
                  "A spaceship is a craft people imagine flying through space. In pretend play, a box or closet can become a spaceship.")],
}
KNOWLEDGE_ORDER = ["closet", "swill", "signature", "sharing", "spaceship"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"closet", "swill", "signature", "sharing", "spaceship"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(swill: Item, signature: Item) -> str:
    return (
        f"(No story: the chosen swill and signature must both be fragile enough for a spill to matter. "
        f"Here, {swill.label} and {signature.label} do not form a believable danger.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
hazard(S, G) :- fragile(S), fragile(G).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
valid(setting(C), swill(S), signature(G)) :- fragile(S), fragile(G), hazard(S, G), setting(C).
outcome(contained) :- chosen_response(R), delay(D), power(R, P), P >= D + 1.
outcome(messy) :- chosen_response(R), delay(D), power(R, P), P < D + 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.fragile:
            lines.append(asp.fact("fragile", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_response", params.response), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH in sensible responses.")
        rc = 1
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(7))
        sample = generate(p)
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    cases = [StoryParams("closet", "swill", "signature", "quick_fix", "Nia", "girl", "Owen", "boy", "mother", 0)]
    if all(asp_outcome(c) in {"contained", "messy"} for c in cases):
        print("OK: ASP outcome model runs.")
    else:
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world in a storage closet.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--swill", choices=ITEMS)
    ap.add_argument("--signature", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for sw in ITEMS:
            for sig in ITEMS:
                if sw != sig and hazard_at_risk(ITEMS[sw], ITEMS[sig]):
                    combos.append((s, sw, sig))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.swill and args.signature and args.swill == args.signature:
        raise StoryError("(No story: the swill and the signature cannot be the same item.)")
    if args.swill and args.signature and not hazard_at_risk(ITEMS[args.swill], ITEMS[args.signature]):
        raise StoryError(explain_rejection(ITEMS[args.swill], ITEMS[args.signature]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.swill is None or c[1] == args.swill)
              and (args.signature is None or c[2] == args.signature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, swill, signature = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    captain_gender = "girl" if rng.random() < 0.5 else "boy"
    mate_gender = "boy" if captain_gender == "girl" else "girl"
    captain = args.captain or rng.choice(NAMES_GIRL if captain_gender == "girl" else NAMES_BOY)
    mate = args.mate or rng.choice(NAMES_BOY if mate_gender == "boy" else NAMES_GIRL)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, swill, signature, response, captain, captain_gender, mate, mate_gender, parent, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.swill],
        ITEMS[params.signature],
        RESPONSES[params.response],
        params.captain,
        params.captain_gender,
        params.mate,
        params.mate_gender,
        params.parent,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("closet", "swill", "signature", "quick_fix", "Nia", "girl", "Owen", "boy", "mother", 0),
    StoryParams("closet", "swill", "signature", "careful_tray", "Maya", "girl", "Kai", "boy", "father", 1),
    StoryParams("closet", "swill", "signature", "new_page", "Lena", "girl", "Leo", "boy", "mother", 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} and {p.mate}: swill and signature in the closet"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
