#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/enthusiastic_spirit_river_path_transformation_conflict_pirate.py
================================================================================================

A standalone storyworld for a tiny pirate tale set along a river path.

Premise:
- A child and a friend explore a river path like pirates.
- They meet an enthusiastic little river spirit and want a treasure light.
- A conflict arises because someone wants a risky shortcut.
- The spirit transforms the scene in a safe, magical way.
- The ending shows the path changed and the pirates learning a better way.

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates three QA sets from world state
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
    path_detail: str
    dark_spot: str
    treasure_goal: str
    send_off: str

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
class Spirit:
    id: str
    label: str
    glow: str
    transform: str
    help_text: str
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
class Hazard:
    id: str
    label: str
    makes_mud: bool = False
    makes_slip: bool = False
    risky: bool = True
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
class Fix:
    id: str
    label: str
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
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    mate = world.entities.get("mate")
    if not hero or not mate:
        return out
    if hero.memes["stubborn"] < THRESHOLD:
        return out
    if mate.memes["worry"] < THRESHOLD:
        return out
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    mate.memes["conflict"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


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


def hazard_at_risk(hazard: Hazard, setting: Setting) -> bool:
    return hazard.risky and setting.id == "river_path"


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def transformation_possible(hazard: Hazard, spirit: Spirit) -> bool:
    return hazard.makes_mud or hazard.makes_slip or spirit.id == "river_spirit"


def fixable(fix: Fix, hazard: Hazard) -> bool:
    return fix.power >= 2 and hazard.risky


def predict(world: World, hazard_id: str, spirit_id: str) -> dict:
    sim = world.copy()
    _trigger_hazard(sim, sim.get(hazard_id), sim.get(spirit_id), narrate=False)
    return {
        "conflict": sim.get("hero").memes["conflict"],
        "mud": sim.get("path").meters["mud"],
        "shine": sim.get("path").meters["shine"],
    }


def _trigger_hazard(world: World, hazard: Entity, spirit: Entity, narrate: bool = True) -> None:
    hazard.meters["mud"] += 1
    spirit.memes["glad"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright day, {hero.id} and {mate.id} marched along {setting.place}, "
        f"pretending the river path was a pirate trail. The path curled past reeds, "
        f"and {setting.path_detail}."
    )
    world.say(
        f'"We are {setting.scene}!" {hero.id} cried, with an enthusiastic spirit that '
        f"made the whole walk feel like an adventure."
    )


def meet_spirit(world: World, spirit: Spirit, setting: Setting) -> None:
    world.say(
        f"Then a little river spirit rose from the water grass, all {spirit.glow}. "
        f'"I know this path," it said. "{spirit.help_text}"'
    )


def want_treasure(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["want"] += 1
    world.say(
        f'{hero.id} pointed down the path. "If we follow {setting.dark_spot}, we can '
        f'find {setting.treasure_goal}!"'
    )


def warn(world: World, mate: Entity, hero: Entity, hazard: Hazard, spirit: Spirit) -> None:
    pred = predict(world, "path", "spirit")
    mate.memes["worry"] += 1
    world.facts["pred"] = pred
    world.say(
        f'{mate.id} bit {mate.pronoun("possessive")} lip. "{hero.id}, that trick path '
        f'could turn muddy and slippery. {spirit.label} says the safe way is better."'
    )


def defy(world: World, hero: Entity, mate: Entity, hazard: Hazard) -> None:
    hero.memes["stubborn"] += 1
    world.say(
        f'"Come on!" {hero.id} said. "{mate.id}, don\'t lose your pirate spirit." '
        f"Then {hero.id} hurried toward the shortcut."
    )


def transform(world: World, spirit: Spirit, setting: Setting, hazard: Hazard) -> None:
    _trigger_hazard(world, world.get("path"), world.get("spirit"))
    path = world.get("path")
    path.meters["shine"] += 1
    path.meters["mud"] += 1
    world.say(
        f"{spirit.label} laughed softly and waved {spirit.transform}. At once, the "
        f"river path changed: a muddy patch turned into a shining stepping-stone line, "
        f"and the slippery place became easy to cross."
    )


def alarm(world: World, mate: Entity, hero: Entity, setting: Setting) -> None:
    world.say(
        f'"{hero.id}! Watch your step!" {mate.id} shouted. "The river path is changing!"'
    )


def fix_story(world: World, fix: Fix, spirit: Spirit, hero: Entity, mate: Entity, setting: Setting) -> None:
    world.get("path").meters["mud"] = 0
    world.get("path").meters["shine"] += 1
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    world.say(
        f"A calm grown-up fix was not needed, because {spirit.label} {fix.text}. "
        f"The pirates slowed down, held hands, and crossed the path the safe way."
    )
    world.say(
        f"By the end, {setting.place} looked brand-new, with a bright trail where the mud had been."
    )


def ending(world: World, hero: Entity, mate: Entity, spirit: Spirit, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"{hero.id} grinned at {mate.id}. The enthusiastic spirit floated beside them, "
        f"glowing over the path like a lantern, and the pirate pair sailed on toward "
        f"{setting.send_off}."
    )


def tell(setting: Setting, spirit: Spirit, hazard: Hazard, fix: Fix,
         hero_name: str = "Nia", hero_type: str = "girl",
         mate_name: str = "Pip", mate_type: str = "boy") -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    mate = world.add(Entity("mate", kind="character", type=mate_type, label=mate_name, role="mate"))
    spirit_ent = world.add(Entity("spirit", kind="character", type="spirit", label=spirit.label, role="spirit"))
    path = world.add(Entity("path", type="path", label="the river path"))
    hazard_ent = world.add(Entity("hazard", type="hazard", label=hazard.label))

    intro(world, hero, mate, setting)
    world.para()
    meet_spirit(world, spirit, setting)
    want_treasure(world, hero, setting)
    warn(world, mate, hero, hazard, spirit)
    defy(world, hero, mate, hazard)
    world.para()
    transform(world, spirit, setting, hazard)
    alarm(world, mate, hero, setting)
    fix_story(world, fix, spirit, hero, mate, setting)
    ending(world, hero, mate, spirit, setting)

    world.facts.update(
        hero=hero, mate=mate, spirit=spirit_ent, setting=setting, hazard=hazard,
        fix=fix, outcome="transformed", route="river path"
    )
    return world


SETTINGS = {
    "river_path": Setting(
        id="river_path",
        place="the river path",
        scene="pirate scouts",
        path_detail="the old stones were damp and shiny",
        dark_spot="the bend under the willow",
        treasure_goal="the glowing shell at the water's edge",
        send_off="the next bend in the river",
    ),
    "reed_path": Setting(
        id="river_path",
        place="the river path by the reeds",
        scene="deckhands on a secret voyage",
        path_detail="the reeds hissed in the wind",
        dark_spot="the narrow bend by the reeds",
        treasure_goal="the silver coin hidden in the grass",
        send_off="the far dock",
    ),
}

SPIRITS = {
    "river_spirit": Spirit(
        id="river_spirit",
        label="the river spirit",
        glow="green-blue and bright-eyed",
        transform="a silver swirl",
        help_text="If you get stuck, call kindly and I will change the path.",
        tags={"spirit", "river", "transformation"},
    ),
    "brook_spirit": Spirit(
        id="brook_spirit",
        label="the brook spirit",
        glow="gold and misty",
        transform="a splash of light",
        help_text="I can make a safe bridge when the trail gets messy.",
        tags={"spirit", "river", "transformation"},
    ),
}

HAZARDS = {
    "mud_patch": Hazard("mud_patch", "mud patch", makes_mud=True, risky=True, tags={"conflict"}),
    "slip_stone": Hazard("slip_stone", "slippery stone", makes_slip=True, risky=True, tags={"conflict"}),
}

FIXES = {
    "bridge": Fix("bridge", "a little bridge", 3, 3,
                  "made a little bridge of light across the muddy patch",
                  "tried to make a bridge, but the path stayed slippery",
                  "built a little bridge of light across the muddy patch",
                  tags={"transformation"}),
    "stones": Fix("stones", "stepping stones", 2, 2,
                  "turned the mud into stepping stones one by one",
                  "could not turn the whole path in time",
                  "turned the mud into stepping stones one by one",
                  tags={"transformation"}),
    "lamp": Fix("lamp", "a lantern lamp", 2, 2,
                 "lit the path so clearly that everyone could see the safe way",
                 "the light was not enough",
                 "lit the path so clearly that everyone could see the safe way",
                 tags={"transformation"}),
}

GIRL_NAMES = ["Nia", "Mina", "Lily", "Ava", "Maya"]
BOY_NAMES = ["Pip", "Tom", "Ben", "Finn", "Noah"]
TRAITS = ["bold", "curious", "cheerful", "sly", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, haz in HAZARDS.items():
            for spid, spirit in SPIRITS.items():
                if hazard_at_risk(haz, setting) and transformation_possible(haz, spirit):
                    combos.append((sid, hid, spid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    spirit: str
    fix: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    trait: str
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


KNOWLEDGE = {
    "spirit": [("What is a spirit in a story?",
                "A spirit is a magical character that can appear in a special place and help change what is happening.")],
    "transformation": [("What is a transformation?",
                        "A transformation is a change from one thing into another, like mud becoming a safe path.")],
    "conflict": [("What is a conflict in a story?",
                  "A conflict is a problem or disagreement that makes the characters need to decide what to do.")],
    "river": [("What is a river?",
               "A river is a long flow of water that moves through land.")],
    "path": [("What is a path?",
              "A path is a trail people walk on to get from one place to another.")],
    "mud": [("Why is mud slippery?",
             "Mud is wet and soft, so shoes can slide on it easily.")],
    "stepping stones": [("What are stepping stones?",
                         "Stepping stones are stones you can walk on to cross wet ground safely.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light that helps people see in the dark.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style story for a young child that includes the words "enthusiastic" and "spirit" and takes place on a {f["setting"].place}.',
        f"Tell a short pirate tale where {f['hero'].label} and {f['mate'].label} meet a river spirit and run into a conflict on the path.",
        f"Write a story with a magical transformation on a river path, where a spirit helps the pirates choose the safe way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, spirit, setting = f["hero"], f["mate"], f["spirit"], f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.label} and {mate.label}, two little pirates exploring {setting.place}. They also meet {spirit.label}, who changes the path."),
        ("What problem do they have?",
         f"They get into a conflict because {hero.label} wants to take a risky shortcut, while {mate.label} worries the path will get muddy and slippery. The disagreement makes the choice feel important."),
        ("What changes on the path?",
         f"The river spirit turns the muddy place into a safe shining crossing. That transformation lets them keep going without slipping."),
        ("How does the story end?",
         f"They cross the river path safely and keep their pirate adventure going. The ending shows that the path is bright, calm, and changed for the better."),
    ]
    if world.get("path").meters["shine"] >= THRESHOLD:
        qa.append((
            "What proves the transformation worked?",
            f"The path now shines where the mud used to be, so the children can walk on it safely. That bright ending shows the spirit's help made a real difference."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["spirit"].label_word.lower() for _ in [0])
    tags = {"spirit", "transformation", "conflict", "river", "path", "mud", "stepping stones"}
    out: list[tuple[str, str]] = []
    for key in ["spirit", "transformation", "conflict", "river", "path", "mud", "stepping stones", "lantern"]:
        if key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(hazard: Hazard, setting: Setting) -> str:
    if not hazard_at_risk(hazard, setting):
        return "(No story: this hazard does not create a real conflict on the river path.)"
    return "(No story: no sensible transformation exists for that combination.)"


ASP_RULES = r"""
hazard(F, S) :- risky(F), setting(S).
valid(S, H, P) :- setting(S), hazard(H, S), spirit(P).
outcome(transformed) :- valid(S, H, P), transformable(H, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("risky", hid))
    for pid in SPIRITS:
        lines.append(asp.fact("spirit", pid))
        lines.append(asp.fact("transformable", "mud_patch", pid))
        lines.append(asp.fact("transformable", "slip_stone", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(_: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if a - b:
            print("  only in clingo:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, spirit=None, fix=None, hero=None, hero_gender=None, mate=None, mate_gender=None, trait=None), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: default generation smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate river-path storyworld with spirit transformation and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.spirit is None or c[2] == args.spirit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, spirit = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice(GIRL_NAMES if mate_gender == "girl" else BOY_NAMES)
    if hero == mate:
        mate += "a"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, hazard, spirit, fix, hero, hero_gender, mate, mate_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPIRITS[params.spirit], HAZARDS[params.hazard], FIXES[params.fix],
                 params.hero, params.hero_gender, params.mate, params.mate_gender)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, h, sp, "bridge", "Nia", "girl", "Pip", "boy", "bold")) for s, h, sp in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
