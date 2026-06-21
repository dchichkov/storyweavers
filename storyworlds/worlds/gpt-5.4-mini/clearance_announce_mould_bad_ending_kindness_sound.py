#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clearance_announce_mould_bad_ending_kindness_sound.py
=====================================================================================

A small standalone storyworld for a ghost-story-style tale about a child, a
clearance notice, a mouldy room, kindness, and sound effects.

Premise
-------
A curious child finds a spooky clearance announcement in an old house. The
notice says a room must be cleared out because mould has grown there. The child
tries to be kind and helpful, but the dark, echoing place and the strange sounds
push the story toward a bad ending: the mould spreads, the room is shut, and the
child learns that some places must be left alone until grown-ups fix them.

This is a classical simulation with:
- typed entities with meters and memes
- state-driven prose
- a Python reasonableness gate plus inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    spooky: str
    entry: str
    echo: str
    hidden: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Notice:
    id: str
    text: str
    phrase: str
    requires_clearance: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class MoldSpot:
    id: str
    label: str
    the: str
    smell: str
    visible: bool = True
    spreads_fast: int = 2
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class SoundEffect:
    id: str
    text: str
    effect: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
            value = __import__("collections").defaultdict(float)
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    notice: str
    mould: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SETTINGS = {
    "attic": Setting("attic", "the attic", "dusty beams and whispered shadows", "the narrow stairs", "the old floorboards", "the corners"),
    "cellar": Setting("cellar", "the cellar", "cold pipes and a dripping wall", "the stone steps", "the damp air", "the back shelves"),
    "hall": Setting("hall", "the old hall", "a long, creaking hallway", "the front door", "the echoing floor", "the closet"),
}

NOTICES = {
    "clearance": Notice("clearance", "Clearance! Please clear this room by sunset.", "clearance", True, {"clearance"}),
    "announce": Notice("announce", "Announcement: keep out while the room is being cleaned.", "announce", True, {"announce"}),
}

MOULDS = {
    "green": MoldSpot("green", "green mould", "the green mould", "a sour, earthy smell", True, 3, {"mould"}),
    "black": MoldSpot("black", "black mould", "the black mould", "a sharp, damp smell", True, 4, {"mould"}),
}

SOUND_EFFECTS = {
    "creak": SoundEffect("creak", "Creeeak.", "a long creak", {"sound"}),
    "drip": SoundEffect("drip", "Drip... drip... drip...", "slow dripping", {"sound"}),
    "bump": SoundEffect("bump", "Bump!", "a sudden bump", {"sound"}),
}

RESPONSES = {
    "cover": Response("cover", 3, 4, "closed the door, covered the mouldy patch with a sheet, and called a grown-up", "tried to cover it, but the mould had already spread too far", "closed the door and called a grown-up", {"kindness"}),
    "clean": Response("clean", 3, 3, "wore gloves, scrubbed the spot, and kept the windows open", "scrubbed quickly, but the damp air made the mould come back", "scrubbed the spot with care", {"kindness"}),
    "wait": Response("wait", 2, 2, "stood back and waited for the helper to arrive", "waited, but the room grew worse by the minute", "waited for help", {"kindness"}),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Ivy", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Sam", "Max", "Eli"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MOULDS:
            combos.append((s, m))
    return combos


def reason_ok(setting: Setting, mould: MoldSpot) -> bool:
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 3]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def mould_severity(mould: MoldSpot, delay: int) -> int:
    return mould.spreads_fast + delay


def contained(response: Response, mould: MoldSpot, delay: int) -> bool:
    return response.power >= mould_severity(mould, delay)


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["moulding"] < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["closed"] += 1
        for c in world.characters():
            c.memes["unease"] += 1
        out.append("__spooky__")
    return out


CAUSAL_RULES = [_r_spread]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_mould(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["moulding"] += 1
    propagate(world, narrate=narrate)


def predict_mould(world: World, mould_id: str) -> dict:
    sim = world.copy()
    _do_mould(sim, sim.get(mould_id), narrate=False)
    return {"spread": sim.get(mould_id).meters["moulding"] >= THRESHOLD, "closed": sim.get("room").meters["closed"]}


def play_open(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    world.say(
        f"On a grey afternoon, {child.id} and {helper.id} went into {setting.place}. "
        f"{setting.spooky} made the house feel like a ghost story."
    )
    world.say(f"The air felt {setting.echo}, and {setting.entry} seemed to groan each time it moved.")


def notice_story(world: World, notice: Notice, setting: Setting, mould: MoldSpot) -> None:
    world.say(
        f"On the wall hung a faded note. It said, \"{notice.text}\""
    )
    world.say(
        f"Everyone could smell {mould.smell} near {setting.hidden}."
    )


def soundy(world: World, se: SoundEffect) -> None:
    world.say(f"Then came {se.text} It was the sound of {se.effect} in the dark.")


def kindness(world: World, helper: Entity, child: Entity, mould: MoldSpot, notice: Notice) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f'{helper.id} spoke softly. "{child.id}, we can help, but we have to be careful." '
        f'"{notice.phrase.capitalize()} means this place needs grown-up help."'
    )


def urge(world: World, child: Entity, notice: Notice) -> None:
    child.memes["wanting"] += 1
    world.say(f'{child.id} wanted to be brave and announce, "I can fix it!"')


def warn(world: World, helper: Entity, child: Entity, mould: MoldSpot) -> None:
    pred = predict_mould(world, "mould")
    if pred["spread"]:
        world.facts["predicted_closed"] = pred["closed"]
        world.say(
            f'{helper.id} shook {helper.pronoun("possessive")} head. "That mould can spread fast," '
            f"{helper.pronoun()} said. \"We should not touch it alone.\""
        )


def bad_turn(world: World, child: Entity, mould: MoldSpot, se: SoundEffect) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} ignored the warning and pushed the curtain aside. {se.text} '
        f'The mould had a wet, sleepy look, and then it woke up all at once.'
    )


def alarm(world: World, helper: Entity, child: Entity) -> None:
    world.say(
        f'"{child.id}!" {helper.id} cried. "Back away!"'
    )


def rescue_fail(world: World, response: Response, mould: MoldSpot) -> None:
    body = response.fail.replace("{target}", mould.label)
    world.say(f"A grown-up tried to help, but {body}.")
    world.say("The damp patch kept growing, and the room had to be shut at once.")


def closing_loss(world: World, child: Entity, helper: Entity, setting: Setting, mould: MoldSpot) -> None:
    child.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"In the end, the family put up a warning sign and closed {setting.place}. "
        f"The mould stayed on the walls, and the old room became too dangerous to use."
    )
    world.say(
        f"{child.id} went home quiet and small, still hearing the {setting.echo} in {setting.place}."
    )
    world.say(
        "That was the bad ending: kindness was there, but it was not enough to save the room."
    )


def tell(setting: Setting, notice: Notice, mould: MoldSpot, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Dad", helper_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(child_name, "character", child_gender, role="child"))
    helper = world.add(Entity(helper_name, "character", helper_gender, role="helper"))
    room = world.add(Entity("room", "thing", "room", label=setting.place))
    mould_ent = world.add(Entity("mould", "thing", "mould", label=mould.label))
    world.facts["setting"] = setting
    world.facts["notice"] = notice
    world.facts["mould_cfg"] = mould
    world.facts["response"] = response

    play_open(world, child, helper, setting)
    world.para()
    notice_story(world, notice, setting, mould)
    soundy(world, SOUND_EFFECTS["creak"])
    kindness(world, helper, child, mould, notice)
    urge(world, child, notice)
    warn(world, helper, child, mould)
    world.para()
    bad_turn(world, child, mould, SOUND_EFFECTS["drip"])
    _do_mould(world, mould_ent)
    alarm(world, helper, child)
    response.use = response.text
    response_obj = response
    if contained(response_obj, mould, delay=1):
        world.say("The room could have been saved, but this world keeps the sad ending.")
    rescue_fail(world, response_obj, mould)
    closing_loss(world, child, helper, setting, mould)
    world.facts.update(child=child, helper=helper, room=room, mould=mould_ent, outcome="bad")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["setting"]
    m = f["mould_cfg"]
    return [
        f'Write a spooky story for a young child that includes the words "clearance", "announce", and "mould".',
        f"Tell a ghost-story-style tale set in {s.place} where a kind helper notices {m.label} and a clearance notice, but things end badly.",
        f'Write a short, eerie story with kindness and sound effects where someone tries to announce a fix for mould, but the room is lost.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    setting, notice, mould = f["setting"], f["notice"], f["mould_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id} in {setting.place}. They found a spooky notice and a mouldy room."),
        ("What did the notice ask for?",
         f"It asked for clearance. The note said the room needed to be cleared out because it was no longer safe."),
        ("Why did the helper act kindly?",
         f"{helper.id} wanted to help {child.id} without being unkind. {helper.id} spoke softly and tried to keep {child.id} safe while warning about the mould."),
        ("How did the story end?",
         f"It ended badly. The mould spread, the room was closed, and the family could not keep using it."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is mould?",
         "Mould is a fuzzy growth that can appear on damp walls or old food. It is a sign that a place may be wet and unhealthy."),
        ("What does clearance mean?",
         "Clearance means making a place empty or cleared out, often so it can be cleaned or fixed."),
        ("Why do old houses creak?",
         "Old houses creak because wood and boards move a little when people walk on them or when the air changes."),
        ("What are sound effects in a story?",
         "Sound effects are little words that help you hear the story in your head, like creak, drip, or bump."),
        ("Why should you avoid mould?",
         "You should avoid mould because it can be unhealthy and can spread if it is left alone."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "clearance", "green", "cover", "Mina", "girl", "Dad", "boy"),
    StoryParams("cellar", "announce", "black", "clean", "Theo", "boy", "Mom", "girl"),
    StoryParams("hall", "clearance", "black", "wait", "Ivy", "girl", "Dad", "boy"),
]


def explain_rejection() -> str:
    return "(No story: this world only builds sad ghost-story scenes where clearance, mould, kindness, and sound effects fit together.)"


def valid_story_choice(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.notice in NOTICES and params.mould in MOULDS and params.response in RESPONSES


ASP_RULES = r"""
valid(S, N, M) :- setting(S), notice(N), mould(M).
kind(R) :- response(R), sense(R, X), sense_min(Y), X >= Y.
bad_ending :- valid(S, N, M), chosen(S), chosen_notice(N), chosen_mould(M), not helped.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in NOTICES:
        lines.append(asp.fact("notice", nid))
    for mid in MOULDS:
        lines.append(asp.fact("mould", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, notice=None, mould=None, response=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story style world about clearance, mould, kindness, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--notice", choices=NOTICES)
    ap.add_argument("--mould", choices=MOULDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 3:
        raise StoryError("The chosen response is too weak for this story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    notice = args.notice or rng.choice(list(NOTICES))
    mould = args.mould or rng.choice(list(MOULDS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(setting, notice, mould, response, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], NOTICES[params.notice], MOULDS[params.mould], RESPONSES[params.response], params.child, params.child_gender, params.helper, params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
