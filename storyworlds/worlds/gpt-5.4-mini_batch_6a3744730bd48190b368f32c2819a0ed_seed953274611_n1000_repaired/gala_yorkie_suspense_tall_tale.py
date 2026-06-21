#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gala_yorkie_suspense_tall_tale.py
===================================================================

A tiny storyworld for a gala-night tall tale with suspense: a small yorkie,
a missing sparkle, a nervous search, and a grand reveal that turns worry into
cheers. The world is built from simulated state, not a frozen paragraph.

The story can vary within a narrow, reasonable domain:
- a gala hall with a stage, lights, and decorations
- a yorkie who senses something odd
- a suspenseful clue trail
- a calm helper who solves the problem
- a final image that proves what changed

This script follows the shared Storyweavers contract:
- standalone stdlib script
- imports results eagerly for QAItem, StoryError, StorySample
- imports asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python and ASP reasonableness gates
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    glamour: str
    shadow: str
    echo: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class SuspenseTrigger:
    id: str
    clue: str
    sound: str
    hidden: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    where: str
    value: str
    recoverable: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Helper:
    id: str
    label: str
    action: str
    reveal: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class EntitySpec:
    id: str
    type: str
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("tension_started") and ("tension", 1) not in world.fired:
        world.fired.add(("tension", 1))
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["worry"] += 1
        out.append("__tension__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reveal_ready") and ("reveal", 1) not in world.fired:
        world.fired.add(("reveal", 1))
        out.append("__reveal__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("tension", "social", _r_tension),
    Rule("reveal", "social", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def suspicion_level(trigger: SuspenseTrigger, thing: MissingThing) -> bool:
    return trigger.hidden == thing.id and thing.recoverable


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.power >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for trigger_id, trig in TRIGGERS.items():
            for thing_id, thing in MISSING.items():
                if suspicion_level(trig, thing):
                    combos.append((setting_id, trigger_id, thing_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    trigger: str
    missing: str
    helper: str
    hero_name: str
    hero_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "gala": Setting(
        id="gala",
        place="the grand gala hall",
        glamour="gold ribbons, bright chandeliers, and a long red carpet",
        shadow="behind the velvet curtains",
        echo="the music bounced off the high walls",
        tags={"gala", "hall", "light"},
    ),
    "mansion": Setting(
        id="mansion",
        place="the old mansion ballroom",
        glamour="silver mirrors, candle-cups, and pearl-white flowers",
        shadow="under the sweeping staircase",
        echo="every footstep sounded extra important",
        tags={"gala", "mansion", "light"},
    ),
    "dock": Setting(
        id="dock",
        place="the river dock banquet tent",
        glamour="lanterns, bunting, and a shining cake table",
        shadow="near the crate stack",
        echo="the wind made every ribbon whisper",
        tags={"gala", "tent", "light"},
    ),
}

TRIGGERS = {
    "clock": SuspenseTrigger(
        id="clock",
        clue="the big clock stopped at the stroke of nine",
        sound="tick... tick... tick...",
        hidden="star",
        tags={"suspense", "clock"},
    ),
    "curtain": SuspenseTrigger(
        id="curtain",
        clue="the curtain bulged like it was hiding a secret",
        sound="fssst...",
        hidden="star",
        tags={"suspense", "curtain"},
    ),
    "box": SuspenseTrigger(
        id="box",
        clue="the velvet box sat open with one shining place empty",
        sound="clink...",
        hidden="star",
        tags={"suspense", "box"},
    ),
}

MISSING = {
    "star": MissingThing(
        id="star",
        label="the gala star",
        phrase="the gala star pin",
        where="on the stage dress",
        value="the brightest honor at the gala",
        recoverable=True,
        tags={"star", "pin"},
    ),
    "bow": MissingThing(
        id="bow",
        label="the silver bow",
        phrase="the silver bow",
        where="on the prize basket",
        value="the ribbon that made the basket look grand",
        recoverable=True,
        tags={"bow", "ribbon"},
    ),
    "bell": MissingThing(
        id="bell",
        label="the tiny bell",
        phrase="the tiny bell",
        where="beside the announcement stand",
        value="the bell that rang the opening cheer",
        recoverable=True,
        tags={"bell", "sound"},
    ),
}

HELPERS = {
    "stagehand": Helper(
        id="stagehand",
        label="the stagehand",
        action="slid back the curtain and searched by flashlight",
        reveal="found the shining thing tucked safely in a pocket",
        power=3,
        tags={"helper", "flashlight"},
    ),
    "yorkie": Helper(
        id="yorkie",
        label="the yorkie",
        action="scratched at the hem and pointed with a tiny nose",
        reveal="found the secret trail by sniffing the floor",
        power=2,
        tags={"helper", "yorkie"},
    ),
    "host": Helper(
        id="host",
        label="the host",
        action="lifted the cloth cover and looked under the table",
        reveal="found the missing prize where nobody expected it",
        power=4,
        tags={"helper", "host"},
    ),
}

HERO_NAMES = ["Mia", "Nora", "Theo", "Ella", "Max", "Lily", "Finn", "Ava"]
PARENT_NAMES = ["Mrs. Bell", "Mr. Reed", "Aunt June", "Uncle Walt"]


def tell(setting: Setting, trigger: SuspenseTrigger, missing: MissingThing, helper: Helper,
         hero_name: str, hero_gender: str, parent_name: str, parent_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["small", "brave"]))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent", label="the grown-up"))
    yorkie = world.add(Entity(id="Yorkie", kind="character", type="dog", role="watcher", label="the yorkie", traits=["tiny", "sharp-eared"]))
    helper_ent = world.add(Entity(id=helper.id, kind="character", type="adult", role="helper", label=helper.label))
    world.facts.update(setting=setting, trigger=trigger, missing=missing, helper=helper, hero=hero, parent=parent, yorkie=yorkie)
    hero.memes["joy"] += 1
    yorkie.memes["alert"] += 1

    world.say(
        f"At {setting.place}, the gala glittered like a pocketful of stars. "
        f"{setting.glamour} were all around, and {setting.echo}."
    )
    world.say(
        f"{hero.id} came in with {parent_name}, and the little yorkie trotted along "
        f"as if it owned the moonlit floor."
    )
    world.say(
        f"Then came the strange part: {trigger.sound} {trigger.clue}. "
        f"{hero.id} looked up, and the yorkie looked too."
    )

    world.para()
    world.say(
        f'"Something is wrong," whispered {hero.id}. '
        f'Under the music and the shine, the empty place felt suspiciously quiet.'
    )
    world.say(
        f'The yorkie gave a soft little bark, because {missing.label} was supposed to be '
        f"{missing.where}."
    )
    world.facts["tension_started"] = True
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{parent_name} did not scold. {parent_name} only leaned close and said, "
        f'"Let us follow the clue without making a fuss."'
    )
    world.say(
        f"That was the suspense of it: everyone moved slow, while the gala music kept on "
        f"playing like it had no idea a mystery was walking by."
    )

    world.para()
    world.say(
        f"At last, {helper.label_word if hasattr(helper, 'label_word') else helper.label} "
        f"{helper.action}. {helper.reveal}."
    )
    world.facts["reveal_ready"] = True
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.id} laughed first, then the whole hall laughed with {hero.id}. "
        f"The yorkie spun in a proud little circle, and {missing.label} was restored "
        f"to the stage just in time for the grand cheer."
    )
    world.say(
        f"By the end, the gala shone even brighter than before, and the yorkie sat tall "
        f"beside the prize as if it had always belonged to the story."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the words "gala" and "yorkie" '
        f"and feels suspenseful, but ends happily.",
        f"Tell a story where a yorkie notices a mystery at a gala and a grown-up helps "
        f"solve it after a slow, spooky search.",
        f'Write a suspenseful, child-friendly gala story with a tiny dog, a missing prize, '
        f"and a reveal that makes everyone cheer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    trigger: SuspenseTrigger = f["trigger"]
    missing: MissingThing = f["missing"]
    helper: Helper = f["helper"]
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    yorkie: Entity = f["yorkie"]
    return [
        QAItem(
            question="What kind of event was happening?",
            answer=f"It was a gala, so the hall was dressed up with shining lights and fancy decorations. The whole place felt grand enough for a tall tale to tiptoe through it.",
        ),
        QAItem(
            question="Why did the story feel suspenseful?",
            answer=f"Because something seemed wrong: {trigger.clue}. The quiet clue made everyone slow down and look carefully instead of rushing ahead.",
        ),
        QAItem(
            question="What did the yorkie do?",
            answer=f"The yorkie stayed alert, barked softly, and helped point the way. In the end, that tiny dog was part of how the mystery got solved.",
        ),
        QAItem(
            question="What happened to the missing thing?",
            answer=f"{missing.label} was found and put back where it belonged. The search ended in relief, so the gala could continue with cheers instead of worry.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} laughing, the yorkie sitting proudly near the prize, and the gala shining brighter than before. The ending image proves the mystery was fixed and the celebration could go on.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "gala": [
        QAItem(
            question="What is a gala?",
            answer="A gala is a fancy event where people dress up, gather together, and celebrate something special.",
        )
    ],
    "yorkie": [
        QAItem(
            question="What is a yorkie?",
            answer="A yorkie is a very small dog with a big personality. It can be alert, lively, and quick to notice things.",
        )
    ],
    "suspense": [
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling that something important might happen soon. It makes readers wonder, wait, and listen closely.",
        )
    ],
    "tall tale": [
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story that feels bigger than life, with bold details and a playful, grand way of telling events.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["gala"])
    out.extend(WORLD_KNOWLEDGE["yorkie"])
    out.extend(WORLD_KNOWLEDGE["suspense"])
    out.extend(WORLD_KNOWLEDGE["tall tale"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, trigger: SuspenseTrigger, missing: MissingThing) -> str:
    return f"(No story: the clue and missing thing do not fit a reasonable suspense scene.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, trig in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        lines.append(asp.fact("hidden", tid, trig.hidden))
    for mid, thing in MISSING.items():
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("recoverable", mid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("power", hid, helper.power))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,T,M) :- setting(S), trigger(T), missing(M), hidden(T,M), recoverable(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import asp
    c = set(asp_valid_combos())
    p = set(valid_combos())
    ok = True
    if c != p:
        ok = False
        print("MISMATCH in valid combos")
        print("clingo-only:", sorted(c - p))
        print("python-only:", sorted(p - c))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, trigger=None, missing=None, helper=None,
            hero_name=None, hero_gender=None, parent_name=None, parent_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale gala storyworld with a yorkie and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name", dest="parent_name")
    ap.add_argument("--parent-gender", dest="parent_gender", choices=["woman", "man", "mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.trigger is None or c[1] == args.trigger)
              and (args.missing is None or c[2] == args.missing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trigger, missing = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    return StoryParams(
        setting=setting,
        trigger=trigger,
        missing=missing,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.trigger not in TRIGGERS or params.missing not in MISSING or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        TRIGGERS[params.trigger],
        MISSING[params.missing],
        HELPERS[params.helper],
        params.hero_name,
        params.hero_gender,
        params.parent_name,
        params.parent_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
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


CURATED = [
    StoryParams(setting="gala", trigger="clock", missing="star", helper="stagehand", hero_name="Mia", hero_gender="girl", parent_name="Mrs. Bell", parent_gender="woman"),
    StoryParams(setting="mansion", trigger="curtain", missing="bow", helper="yorkie", hero_name="Theo", hero_gender="boy", parent_name="Mr. Reed", parent_gender="man"),
    StoryParams(setting="dock", trigger="box", missing="bell", helper="host", hero_name="Ava", hero_gender="girl", parent_name="Aunt June", parent_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        for s, t, m in triples:
            print(f"{s} {t} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.setting} / {p.trigger} / {p.missing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
