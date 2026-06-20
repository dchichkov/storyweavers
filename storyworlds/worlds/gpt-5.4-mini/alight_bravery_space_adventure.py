#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alight_bravery_space_adventure.py
==================================================================

A small standalone story world for a space-adventure tale about bravery:
two children on a moon-base find a dark tunnel, one child wants to use a
forbidden flare, the braver choice is to call for help, and they finish with a
safe light that leaves the tunnel alight.

The domain is intentionally tiny and constraint-checked. The story engine models
typed entities with physical meters and emotional memes, a forward rule for
danger, a reasonableness gate, and a declarative ASP twin for parity checks.
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
BRAVERY_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    makes_spark: bool = False
    gives_light: bool = False

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
    dark_spot: str
    scene: str
    mood: str

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
class Forbidden:
    id: str
    label: str
    phrase: str
    where: str
    spark_word: str
    too_risky: str
    makes_spark: bool = True

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
class Target:
    id: str
    label: str
    phrase: str
    near: str
    flammable: bool = True
    spread: int = 2

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
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
    gives_light: bool = True

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
class Rescue:
    id: str
    sense: int
    power: int
    success: str
    fail: str
    qa: str

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "ship" in world.entities:
            world.get("ship").meters["danger"] += 1
        for kid in [x for x in list(world.entities.values()) if x.role in {"instigator", "cautioner"}]:
            kid.memes["fear"] += 1
        out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    emitted: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                emitted.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in emitted:
            world.say(s)


def hazard_ok(forbidden: Forbidden, target: Target) -> bool:
    return forbidden.makes_spark and target.flammable


def sensible_responses() -> list[Rescue]:
    return [r for r in RESPONSES.values() if r.sense >= BRAVERY_MIN]


def fire_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def response_works(response: Rescue, target: Target, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def would_avert(relation: str, older: int, younger: int, courage_trait: str) -> bool:
    if relation != "siblings":
        return False
    return older > younger and courage_trait in {"calm", "steady", "brave"}


def tell(setting: Setting, forbidden: Forbidden, target: Target, lights: tuple[SafeLight, SafeLight],
         response: Rescue, instigator: str = "Nia", instigator_gender: str = "girl",
         cautioner: str = "Finn", cautioner_gender: str = "boy", parent_type: str = "mother",
         trait: str = "brave", delay: int = 0, relation: str = "siblings",
         instigator_age: int = 7, cautioner_age: int = 9) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator"))
    b = world.add(Entity(id=cautioner, kind="character", type=cautioner_gender, role="cautioner", traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    ship = world.add(Entity(id="ship", type="ship", label="the space station"))
    tunnel = world.add(Entity(id="target", type="target", label=target.label, flammable=target.flammable))
    a.memes["bravery"] = 2.0
    b.memes["bravery"] = 1.0 if trait in {"calm", "steady", "brave"} else 0.0
    world.facts["relation"] = relation
    world.facts["delay"] = delay

    world.say(
        f"On the moon station, {a.id} and {b.id} turned a quiet service hall into {setting.scene}. "
        f"{setting.mood}"
    )
    world.say(
        f"They wanted to reach {setting.dark_spot}, where the shadow under the antenna made everything feel like a real space cave."
    )
    world.para()
    world.say(
        f"{a.id} pointed at {forbidden.phrase} {forbidden.where}. \"We could use a little flame to see,\" {a.id} said."
    )
    world.say(
        f"{b.id} hugged {b.pronoun('possessive')} knees and said, \"No, {forbidden.label} is too risky. "
        f"{forbidden.too_risky}.\""
    )

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        world.say(
            f"{a.id} looked at {b.id}, swallowed {a.pronoun('possessive')} bravado, and chose not to touch it."
        )
        world.para()
        world.say(
            f"Instead, {parent.label_word} brought out {lights[0].phrase} and {lights[1].phrase}, both bright and safe."
        )
        world.say(
            f"At last the tunnel was alight with a soft glow, and the two children went on bravely without any danger."
        )
        outcome = "averted"
    else:
        world.say(f"{a.id} still went ahead, and {forbidden.spark_word} made the small spark jump alive.")
        world.get("target").meters["burning"] += 1
        propagate(world)
        world.para()
        world.say(
            f"The spark touched {target.near}, and a thin orange line began to creep along the wall panel."
        )
        world.say(f"{b.id} shouted, \"{parent.label_word.upper()}!\"")
        sev = fire_severity(target, delay)
        contained = response_works(response, target, delay)
        world.facts["severity"] = sev
        if contained:
            world.say(
                f"{parent.label_word.capitalize()} ran in and {response.success.replace('{target}', target.label)}."
            )
            world.say(
                f"The little fire sighed out, and the hall smelled smoky but safe."
            )
            world.para()
            world.say(
                f"{parent.label_word.capitalize()} knelt down, held both children close, and praised their brave call for help."
            )
            world.say(
                f"Then came the next day surprise: {lights[0].phrase} and {lights[1].phrase}, so they could explore with safe light."
            )
            world.say(
                f"This time the tunnel was alight the right way, and the children smiled at the bright blue wall panels."
            )
            outcome = "contained"
        else:
            world.say(
                f"{parent.label_word.capitalize()} ran in and {response.fail.replace('{target}', target.label)}."
            )
            world.say("The flame raced faster than the hands could move, and the station began to fill with smoke.")
            world.say(f"{parent.label_word.capitalize()} rushed the children out into the safe airlock.")
            world.para()
            world.say(
                f"Later, they stood together under the stars, shaken and quiet, remembering that bravery can mean calling for help fast."
            )
            world.say(f"They never touched {forbidden.label} again.")
            outcome = "burned"

    world.facts.update(
        instigator=a, cautioner=b, parent=parent, setting=setting, forbidden=forbidden,
        target_cfg=target, target=tunnel, lights=lights, response=response,
        outcome=outcome, averted=averted, contained=(outcome == "contained"),
    )
    return world


SETTINGS = {
    "moonbase": Setting("moonbase", "the moon station", "the antenna tunnel",
                        "a moon-base adventure", "The windows showed the stars, and the hallway hummed softly."),
    "asteroid": Setting("asteroid", "the asteroid outpost", "the repair tunnel",
                        "a faraway asteroid mission", "Outside, the rocks floated like tiny islands in black space."),
    "cargo": Setting("cargo", "the cargo ship", "the loading tunnel",
                     "a spaceship rescue mission", "The cargo bay lights blinked gently over stacked crates."),
}

FORBIDDEN = {
    "flare": Forbidden("flare", "flare", "a small flare", "in a locked drawer", "The flare", "it could make a real fire in a tiny place"),
    "sparkstick": Forbidden("sparkstick", "spark stick", "a spark stick", "in the equipment box", "The spark stick", "it could jump bright sparks onto the wall"),
}

TARGETS = {
    "panel": Target("panel", "wall panel", "the wall panel", "the corner seam", True, 2),
    "curtain": Target("curtain", "hanging curtain", "the hanging curtain", "the edge of the curtain", True, 3),
    "foam": Target("foam", "insulation foam", "the insulation foam", "the foam strip", True, 1),
}

SAFE_LIGHTS = {
    "lamp": SafeLight("lamp", "star lamp", "a star lamp", "glowed blue and gold"),
    "beacon": SafeLight("beacon", "hand beacon", "a hand beacon", "glowed like a tiny moon"),
    "glowband": SafeLight("glowband", "glow band", "a glow band", "shone softly on their wrists"),
}

RESPONSES = {
    "extinguisher": Rescue("extinguisher", 2, 4, "sprayed the fire until every spark was gone", "sprayed, but the fire was already too big", "put the fire out with the extinguisher"),
    "blanket": Rescue("blanket", 2, 3, "covered the flame with a thick blanket and pressed it out", "covered it, but the flame kept climbing", "smothered the fire under a thick blanket"),
    "stomp": Rescue("stomp", 1, 2, "stamped on the little flames until they went dark", "stamped, but the flames only leaped higher", "stamped the flames out"),
}

CURATED = [
    StoryParams("moonbase", "flare", "panel", "lamp", "beacon", "extinguisher", "Nia", "girl", "Finn", "boy", "mother", "brave", 0, "siblings", 7, 9),
    StoryParams("asteroid", "sparkstick", "curtain", "glowband", "lamp", "blanket", "Mina", "girl", "Arlo", "boy", "father", "steady", 0, "siblings", 5, 8),
    StoryParams("cargo", "flare", "foam", "beacon", "glowband", "stomp", "Oli", "boy", "Aya", "girl", "mother", "calm", 1, "siblings", 6, 10),
]


@dataclass
class StoryParams:
    setting: str
    forbidden: str
    target: str
    light1: str
    light2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    relation: str = "siblings"
    instigator_age: int = 7
    cautioner_age: int = 9
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
    return [(s, f, t) for s in SETTINGS for f in FORBIDDEN for t in TARGETS if hazard_ok(FORBIDDEN[f], TARGETS[t])]


KNOWLEDGE = {
    "flare": [("What is a flare?", "A flare is a bright tool that makes a strong flame. It is for emergencies and should only be used by grown-ups.")],
    "sparkstick": [("What is a spark stick?", "A spark stick is a tool that can send out sparks. Sparks can start fire, so children should not use one.")],
    "fire": [("Why is fire dangerous?", "Fire can spread fast and get bigger than you expect. It can hurt people and damage things quickly.")],
    "lamp": [("What is a star lamp?", "A star lamp is a safe light that shines without fire. It helps people see in the dark.")],
    "beacon": [("What does a hand beacon do?", "A hand beacon glows with safe light. It can help you see a path without any flame.")],
    "glowband": [("What is a glow band?", "A glow band shines softly and is cool to the touch. It is a fun and safe way to make light.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the word "alight" and a brave choice.',
        f"Tell a moon-base story where {f['instigator'].id} wants to use {f['forbidden'].label}, but {f['cautioner'].id} warns about the danger and the children choose safety.",
        f'Write a child-friendly spaceship story where the tunnel ends up alight with safe light instead of flame.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    forbidden, target = f["forbidden"], f["target_cfg"]
    l1, l2 = f["lights"]
    qa = [
        ("Who is the story about?", f"It is about {a.id} and {b.id} on a space station, with {parent.label_word} helping when things get scary."),
        ("What did the children want to explore?", f"They wanted to explore {f['setting'].dark_spot}, a dark tunnel that felt like a moon cave."),
        (f"What did {a.id} want to use, and what did {b.id} say?", f"{a.id} wanted to use {forbidden.label}, but {b.id} said it was too risky because it could make a real fire."),
    ]
    if f["outcome"] == "averted":
        qa.append(("How did the story end?", f"It ended safely. {a.id} listened, and the children used {l1.phrase} and {l2.phrase} instead, so the tunnel was alight with safe light."))
    elif f["outcome"] == "contained":
        qa.append(("How did the adults help?", f"{parent.label_word.capitalize()} came in fast and {RESPONSES[f['response'].id].qa.replace('{target}', target.label)}. Then the children got safe lights for the next day."))
        qa.append(("Why were the children brave?", f"They were brave because they called for help right away and stayed together. That helped the fire stop before it spread farther."))
    else:
        qa.append(("What happened when the fire grew?", f"The fire spread too fast and the family had to run out to safety. They were brave because they escaped and stayed together."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["forbidden"].id, world.facts["target_cfg"].id}
    if world.facts["outcome"] != "burned":
        tags |= {x.id for x in world.facts["lights"]}
    out = []
    for k, pairs in KNOWLEDGE.items():
        if k in tags:
            out.extend(pairs)
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
        if e.flammable:
            bits.append("flammable=True")
        if e.gives_light:
            bits.append("gives_light=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(forbidden: Forbidden, target: Target) -> str:
    if not target.flammable:
        return f"(No story: {target.label} won't catch fire.)"
    return f"(No story: {forbidden.label} does not create a hazard here.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is too weak for the story model, sense={r.sense}.)"


ASP_RULES = r"""
hazard(F,T) :- makes_spark(F), flammable(T).
valid(S,F,T) :- setting(S), forbidden(F), target(T), hazard(F,T).
sense_ok(R) :- response(R), sense(R,S), min_sense(M), S >= M.
outcome(averted) :- older_cautioner, brave_trait.
outcome(contained) :- not outcome(averted), chosen_response(R), response_power(R,P), severity(V), P >= V.
outcome(burned) :- not outcome(averted), not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for f, obj in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", f))
        if obj.makes_spark:
            lines.append(asp.fact("makes_spark", f))
    for t, obj in TARGETS.items():
        lines.append(asp.fact("target", t))
        if obj.flammable:
            lines.append(asp.fact("flammable", t))
        lines.append(asp.fact("spread", t, obj.spread))
    for r, obj in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, obj.sense))
        lines.append(asp.fact("response_power", r, obj.power))
    lines.append(asp.fact("min_sense", BRAVERY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about bravery and safe light.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["brave", "calm", "steady", "nervous"])
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
    if args.forbidden and args.target and not hazard_ok(FORBIDDEN[args.forbidden], TARGETS[args.target]):
        raise StoryError(explain_rejection(FORBIDDEN[args.forbidden], TARGETS[args.target]))
    if args.response and RESPONSES[args.response].sense < BRAVERY_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    l1, l2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    return StoryParams(
        setting, forbidden, target, l1, l2, response,
        instigator=rng.choice(["Nia", "Mina", "Oli", "Kai"]),
        instigator_gender=rng.choice(["girl", "boy"]),
        cautioner=rng.choice(["Finn", "Aya", "Jin", "Luz"]),
        cautioner_gender=rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(["brave", "calm", "steady"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], FORBIDDEN[params.forbidden], TARGETS[params.target],
        (SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]), RESPONSES[params.response],
        params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender,
        params.parent, params.trait, params.delay, params.relation, params.instigator_age, params.cautioner_age
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, f, t in asp_valid_combos():
            print(f"  {s:10} {f:10} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("moonbase", "flare", "panel", "lamp", "beacon", "extinguisher", "Nia", "girl", "Finn", "boy", "mother", "brave", 0),
    StoryParams("asteroid", "sparkstick", "curtain", "glowband", "lamp", "blanket", "Mina", "girl", "Aya", "girl", "father", "steady", 0),
    StoryParams("cargo", "flare", "foam", "beacon", "glowband", "stomp", "Oli", "boy", "Jin", "boy", "mother", "calm", 1),
]


if __name__ == "__main__":
    main()
