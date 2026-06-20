#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/converse_incense_bad_ending_conflict_flashback_ghost.py
=======================================================================================

A standalone storyworld for a small ghost-story domain.

Premise
-------
Two children explore an old house at dusk. One wants to converse with a ghost;
the other is uneasy because incense smoke wakes a painful flashback. The smoke,
the memory, and the ghostly presence create conflict. If the children choose
carefully, they can calm the room, but the seed asks for a bad ending, so this
world usually ends with the ghost staying, the room growing colder, and the
children leaving with more fear than courage.

This file follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose with a causal turn and ending image
- QA sets grounded in world state
- Python reasonableness gate plus inline ASP twin
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
FLASHBACK_MIN = 1.0
GHOST_MIN = 1.0


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
    mood: str
    darkness: str
    afford: set[str] = field(default_factory=set)

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
class Incense:
    id: str
    label: str
    phrase: str
    smoke: str
    scent: str
    makes_smoke: bool = True
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
class Ghost:
    id: str
    label: str
    phrase: str
    cold: str
    whisper: str
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
    calm: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

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


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    incense = world.get("incense")
    if incense.meters["lit"] < THRESHOLD:
        return out
    sig = ("smoke",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["smoke"] += 1
    for kid in world.characters():
        kid.memes["unease"] += 1
    out.append("__smoke__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    smoke = world.get("room").meters["smoke"]
    if smoke < FLASHBACK_MIN:
        return out
    for kid in world.characters():
        if kid.memes.get("memory", 0.0) < THRESHOLD:
            continue
        sig = ("flashback", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        kid.memes["flashback"] += 1
        out.append("__flashback__")
    return out


def _r_ghost(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.meters["present"] < GHOST_MIN:
        return out
    sig = ("cold",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["cold"] += 1
    for kid in world.characters():
        kid.memes["fear"] += 1
    out.append("__cold__")
    return out


CAUSAL_RULES = [Rule("smoke", _r_smoke), Rule("flashback", _r_flashback), Rule("cold", _r_ghost)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                produced.extend(p for p in parts if not p.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reason_gate(incense: Incense, ghost: Ghost) -> bool:
    return incense.makes_smoke and bool(ghost.whisper)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def chosen_story_kind(params: "StoryParams") -> str:
    return "bad_ending"


def predict_consequence(world: World, kid_id: str) -> dict:
    sim = world.copy()
    _light_incense(sim, narrate=False)
    return {
        "smoke": sim.get("room").meters["smoke"],
        "flashback": sim.get(kid_id).memes["flashback"],
        "cold": sim.get("room").meters["cold"],
    }


def _light_incense(world: World, narrate: bool = True) -> None:
    world.get("incense").meters["lit"] += 1
    propagate(world, narrate=narrate)


def converse(world: World, a: Entity, b: Entity, ghost: Ghost) -> None:
    world.say(
        f"At the old house, {a.id} and {b.id} stepped through the dusty hall and "
        f"stopped by the parlor window. The air was dim, and {ghost.phrase} seemed "
        f"to wait in the corners."
    )
    world.say(
        f'{a.id} took a slow breath. "Maybe we can converse with the ghost," {a.id} said.'
    )


def incense_setup(world: World, incense: Incense) -> None:
    world.say(
        f"{incense.phrase} sat on a small plate near the lamp, and the first curl of "
        f"{incense.smoke} drifted up like a ribbon."
    )


def warn(world: World, cautious: Entity, instigator: Entity, incense: Incense, ghost: Ghost) -> None:
    cautious.memes["care"] += 1
    cautious.memes["memory"] += 1
    pred = predict_consequence(world, cautious.id)
    world.facts["predicted_smoke"] = pred["smoke"]
    world.facts["predicted_flashback"] = pred["flashback"]
    world.say(
        f'{cautious.id} frowned. "I do not like that incense smoke," {cautious.id} said. '
        f'"It makes me remember the dark night in the hallway, and I do not want a ghost '
        f'and a flashback at the same time."'
    )
    world.say(
        f'{cautious.id} pointed at {ghost.label}. "{ghost.whisper} might not sound kind."'
    )


def defy(world: World, instigator: Entity, incense: Incense) -> None:
    instigator.memes["curiosity"] += 1
    world.say(
        f'{instigator.id} shook {instigator.pronoun("possessive")} head. '
        f'"I still want to try," {instigator.id} said, and touched the incense carefully.'
    )


def turn_flashback(world: World, cautious: Entity) -> None:
    if cautious.memes.get("flashback", 0.0) >= THRESHOLD:
        world.say(
            f"Then the smell pulled {cautious.id} back into a flashback. For one shaky "
            f"moment, the house was not the house at all, but a dark hallway with no safe light."
        )


def ghost_answers(world: World, ghost: Ghost) -> None:
    ghost.meters["present"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The ghost answered with a low whisper: {ghost.whisper}. Its cold drifted over "
        f"the room, and the window glass felt like winter."
    )


def bad_end(world: World, a: Entity, b: Entity, ghost: Ghost, incense: Incense) -> None:
    world.say(
        f"{a.id} and {b.id} looked for brave words, but the room only grew quieter. "
        f"The incense kept smoking, the ghost kept waiting, and nobody found a kind answer."
    )
    world.say(
        f"By the time the children backed out of the parlor, {ghost.label} was still there, "
        f"and {incense.label} had left the whole house smelling like a warning."
    )
    world.say(
        f"In the end, they left the old house with their shoulders hunched and their voices small, "
        f"knowing that some doors stay closed."
    )


def tell(setting: Setting, incense: Incense, ghost: Ghost,
         instigator_name: str = "Maya", instigator_gender: str = "girl",
         cautious_name: str = "Noah", cautious_gender: str = "boy",
         parent_type: str = "mother", flashback_note: str = "the dark hallway") -> World:
    world = World(setting)
    a = world.add(Entity(id=instigator_name, kind="character", type=instigator_gender,
                         role="instigator", traits=["curious"], attrs={"note": flashback_note}))
    b = world.add(Entity(id=cautious_name, kind="character", type=cautious_gender,
                         role="cautious", traits=["careful"], attrs={"note": flashback_note}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the parlor"))
    inc = world.add(Entity(id="incense", type="thing", label=incense.label))
    gh = world.add(Entity(id="ghost", type="ghost", label=ghost.label))
    a.memes["memory"] = 0.0
    b.memes["memory"] = 1.0

    converse(world, a, b, ghost)
    incense_setup(world, incense)
    world.para()
    warn(world, b, a, incense, ghost)
    defy(world, a, incense)
    _light_incense(world)
    turn_flashback(world, b)
    ghost_answers(world, ghost)
    world.para()
    bad_end(world, a, b, ghost, incense)

    world.facts.update(
        instigator=a, cautious=b, parent=parent, room=room,
        incense_cfg=incense, ghost_cfg=ghost,
        incense=inc, ghost=gh, outcome="bad_ending",
        flashback=b.memes.get("flashback", 0.0) >= THRESHOLD,
        smoky=room.meters["smoke"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "old_house": Setting("old_house", "the old house", "haunted", "dim", afford={"converse"}),
    "parlor": Setting("parlor", "the parlor", "haunted", "dim", afford={"converse"}),
    "attic": Setting("attic", "the attic", "dusty", "dim", afford={"converse"}),
}

INCENSES = {
    "sandalwood": Incense("sandalwood", "incense", "a little stick of incense", "smoke", "sandalwood"),
    "jasmine": Incense("jasmine", "incense", "a tiny bowl of incense", "smoke", "jasmine"),
    "cedar": Incense("cedar", "incense", "a bundle of incense", "smoke", "cedar"),
}

GHOSTS = {
    "whisper": Ghost("whisper", "ghost", "the ghost", "cold", "come closer"),
    "lady": Ghost("lady", "ghost", "the lady in gray", "cold", "be careful"),
    "child": Ghost("child", "ghost", "the little ghost", "cold", "listen"),
}

RESPONSES = {
    "leave": Response("leave", 3, 3, "left the room and shut the door gently",
                      "tried to leave, but the hallway felt too long and cold",
                      "left the room"),
    "speak": Response("speak", 2, 2, "spoke softly and asked if it wanted to rest",
                      "spoke, but the whisper felt too far away to answer",
                      "spoke softly"),
    "window": Response("window", 1, 1, "opened a window and hoped the smoke would clear",
                       "opened a window, but the smoke still hung in the air",
                       "opened a window"),
}

GIRL_NAMES = ["Maya", "Luna", "Ivy", "Nina", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Owen", "Leo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    incense: str
    ghost: str
    instigator_name: str
    instigator_gender: str
    cautious_name: str
    cautious_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in INCENSES:
            for g in GHOSTS:
                if reason_gate(INCENSES[i], GHOSTS[g]):
                    combos.append((s, i, g))
    return combos


KNOWLEDGE = {
    "incense": [("What is incense?",
                 "Incense is a little stick or bundle that makes scented smoke when it burns.")],
    "ghost": [("What is a ghost in a story?",
               "A ghost is a spooky character in a story, usually quiet, pale, or cold.")],
    "smoke": [("Why can smoke make people cough?",
                "Smoke can sting the nose and throat, so people often cough to get clean air again.")],
    "flashback": [("What is a flashback?",
                    "A flashback is when a memory feels so strong that the story jumps back into the past for a moment.")],
    "converse": [("What does converse mean?",
                  "To converse means to talk together and exchange words.")],
}

KNOWLEDGE_ORDER = ["converse", "incense", "ghost", "smoke", "flashback"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that includes the word "converse" and the word "incense".',
        f"Tell a spooky but child-friendly story where {f['instigator'].id} wants to converse with {f['ghost_cfg'].label}, "
        f"while {f['cautious'].id} remembers a flashback from incense smoke.",
        "Write a ghost-story scene with a conflict over incense, a flashback, and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["instigator"], f["cautious"]
    ghost = f["ghost_cfg"]
    inc = f["incense_cfg"]
    return [
        QAItem("Who wanted to converse with the ghost?",
               f"{a.id} wanted to converse with the ghost and ask it a question. The room felt spooky, but {a.id} was still curious."),
        QAItem("Why was the other child worried about the incense?",
               f"{b.id} was worried because the incense smoke brought back a flashback of the dark hallway. The smell made the memory feel close again."),
        QAItem("What happened when the incense was lit?",
               f"The incense made smoke, the room got colder, and the ghost seemed closer. That made the conflict stronger instead of calmer."),
        QAItem("How did the story end?",
               f"It ended badly: the children left without making peace, and the ghost stayed in the house. The incense smoke and the flashback made the night feel unfinished."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["incense_cfg"].tags) | set(world.facts["ghost_cfg"].tags) | {"incense", "flashback", "converse"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("old_house", "sandalwood", "whisper", "Maya", "girl", "Noah", "boy", "mother"),
    StoryParams("parlor", "jasmine", "lady", "Ivy", "girl", "Finn", "boy", "father"),
    StoryParams("attic", "cedar", "child", "Theo", "boy", "Luna", "girl", "mother"),
]


def explain_rejection(incense: Incense, ghost: Ghost) -> str:
    return f"(No story: {incense.label} can make smoke, but this world only tells a ghost tale when the ghost has a speaking whisper.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
valid(S, I, G) :- setting(S), incense(I), ghost(G), makes_smoke(I), whisper(G).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(bad_ending) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, i in INCENSES.items():
        lines.append(asp.fact("incense", iid))
        if i.makes_smoke:
            lines.append(asp.fact("makes_smoke", iid))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("whisper", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible response set matches.")
    else:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with incense, converse, flashback, conflict, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--incense", choices=INCENSES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.incense and args.ghost and not reason_gate(INCENSES[args.incense], GHOSTS[args.ghost]):
        raise StoryError(explain_rejection(INCENSES[args.incense], GHOSTS[args.ghost]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.incense is None or c[1] == args.incense)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, incense, ghost = rng.choice(sorted(combos))
    instigator_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    cautious_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != instigator_name])
    instigator_gender = "girl" if instigator_name in GIRL_NAMES else "boy"
    cautious_gender = "girl" if cautious_name in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, incense, ghost, instigator_name, instigator_gender, cautious_name, cautious_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], INCENSES[params.incense], GHOSTS[params.ghost],
                 params.instigator_name, params.instigator_gender,
                 params.cautious_name, params.cautious_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, i, g in asp_valid_combos():
            print(f"  {s:8} {i:10} {g}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
