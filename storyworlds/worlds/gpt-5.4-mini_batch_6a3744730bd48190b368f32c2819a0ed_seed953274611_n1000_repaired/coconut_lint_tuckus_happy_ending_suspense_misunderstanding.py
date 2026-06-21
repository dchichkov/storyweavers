#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/coconut_lint_tuckus_happy_ending_suspense_misunderstanding.py
================================================================================================

A standalone storyworld for a tiny superhero-style misunderstanding story.

Premise:
- A child superhero team hears a strange sound and sees a coconut, some lint,
  and a device called the Tuckus.
- Suspense comes from the hero thinking something dangerous has happened.
- The misunderstanding is that the "lint" is not a clue from a villain; it is
  just fluff from the costume machine.
- The ending is happy: the team calms down, fixes the real problem, and enjoys
  a bright, safe mission.

This world follows the shared Storyweavers contract:
- typed entities with physical meters and emotional memes
- forward-caused world state that drives prose
- grounded prompts and QA
- inline ASP twin plus Python reasonableness gate
- verify mode with a generation smoke test
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
SUSPENSE_MIN = 1
MISUNDERSTANDING_MIN = 1

HERO_NAMES = ["Nova", "Piper", "Milo", "Zuri", "Juno", "Arlo", "Tess", "Bea"]
SIDEKICK_NAMES = ["Zip", "Dot", "Rae", "Finn", "Lumi", "Kai", "Puck", "Wren"]
GUARDIAN_NAMES = ["Captain Bright", "Mayor Halo", "Aunt Comet", "Chief Spark"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Scene:
    id: str
    place: str
    mood: str
    props: str
    dark_spot: str
    mission: str
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


@dataclass
class Misunderstanding:
    id: str
    clue: str
    false_meaning: str
    true_meaning: str
    reveal: str
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
class Hazard:
    id: str
    label: str
    cause: str
    fix: str
    severity: int
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
class Gadget:
    id: str
    label: str
    phrase: str
    glow: str
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
class StoryParams:
    scene: str
    misunderstanding: str
    hazard: str
    gadget: str
    hero: str
    hero_type: str
    sidekick: str
    sidekick_type: str
    guardian: str
    guardian_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["danger"] >= THRESHOLD and ("alarm", e.id) not in world.fired:
            world.fired.add(("alarm", e.id))
            for c in list(world.entities.values()):
                if c.role in {"hero", "sidekick"}:
                    c.memes["suspense"] += 1
            out.append("__alarm__")
    return out


def _r_reveal(world: World) -> list[str]:
    if world.facts.get("misunderstood") and ("reveal", 1) not in world.fired:
        world.fired.add(("reveal", 1))
        return ["__reveal__"]
    return []


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("reveal", "social", _r_reveal)]


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SCENES = {
    "rooftop": Scene(
        id="rooftop",
        place="the moonlit rooftop",
        mood="high above the city",
        props="A red cape fluttered on the line, a silver ladder leaned by the wall, and the city lights blinked below.",
        dark_spot="the space behind the water tower",
        mission="watch the rooftop for trouble",
    ),
    "lab": Scene(
        id="lab",
        place="the busy hero lab",
        mood="full of bright buttons and gentle beeps",
        props="A gadget shelf buzzed softly, a comic book lay open, and a fan hummed near the desk.",
        dark_spot="the corner under the repair table",
        mission="sort the mission gear",
    ),
    "harbor": Scene(
        id="harbor",
        place="the windy harbor pier",
        mood="filled with salt air and creaking ropes",
        props="A coil of rope sat by a crate, gulls circled overhead, and lanterns bobbed on the water.",
        dark_spot="the shadow beside the loading crate",
        mission="check the crates for clues",
    ),
}

MISUNDERSTANDINGS = {
    "coconut": Misunderstanding(
        id="coconut",
        clue="a coconut rolled out of the shadow",
        false_meaning="a villain had hidden a secret bomb",
        true_meaning="the coconut had fallen from a snack crate",
        reveal="it was only a snack for the team",
        tags={"coconut"},
    ),
    "lint": Misunderstanding(
        id="lint",
        clue="a puff of lint floated from the costume dryer",
        false_meaning="a smoke signal from danger",
        true_meaning="the costume machine had shaken out fluff",
        reveal="it was just fluff from the dryer",
        tags={"lint"},
    ),
    "tuckus": Misunderstanding(
        id="tuckus",
        clue="the Tuckus gave one strange tuck-tuck sound",
        false_meaning="a warning from a sneaky machine bug",
        true_meaning="the Tuckus was only asking for a reset",
        reveal="it needed a gentle reset, not a rescue",
        tags={"tuckus"},
    ),
}

HAZARDS = {
    "sticky_door": Hazard(
        id="sticky_door",
        label="the stubborn storage door",
        cause="jammed halfway open",
        fix="squeeze it shut with both hands",
        severity=1,
        tags={"door"},
    ),
    "glitchy_tuckus": Hazard(
        id="glitchy_tuckus",
        label="the Tuckus panel",
        cause="blinked in a warning pattern",
        fix="press the reset button and wait",
        severity=1,
        tags={"tuckus"},
    ),
    "coconut_crate": Hazard(
        id="coconut_crate",
        label="the snack crate",
        cause="wobbled on the edge of the ledge",
        fix="move it back from the edge",
        severity=1,
        tags={"coconut"},
    ),
}

GADGETS = {
    "signal_lamp": Gadget(
        id="signal_lamp",
        label="signal lamp",
        phrase="a signal lamp",
        glow="glowed like a small star",
        tags={"lamp"},
    ),
    "cape_beacon": Gadget(
        id="cape_beacon",
        label="cape beacon",
        phrase="a cape beacon",
        glow="blinked blue and calm",
        tags={"beacon"},
    ),
}

# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for m in MISUNDERSTANDINGS:
            for h in HAZARDS:
                combos.append((s, m, h))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this world needs a scene, a misunderstanding, and a small hazard.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
combo(S,M,H) :- scene(S), misunderstanding(M), hazard(H).
valid(S,M,H) :- combo(S,M,H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in valid_combos()")
        if a - b:
            print("  only in clingo:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
        rc = 1
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test completed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


# ---------------------------------------------------------------------------
# Narrative verbs
# ---------------------------------------------------------------------------
def setup(world: World, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    hero.memes["hope"] += 1
    sidekick.memes["hope"] += 1
    world.say(
        f"At {scene.place}, {hero.id} and {sidekick.id} were on a superhero watch."
    )
    world.say(scene.props)


def suspense(world: World, hero: Entity, sidekick: Entity, scene: Scene, mis: Misunderstanding) -> None:
    hero.memes["suspense"] += 1
    sidekick.memes["suspense"] += 1
    world.say(
        f"Then {mis.clue}. It felt like trouble hiding in plain sight."
    )
    world.say(
        f'"Maybe {mis.false_meaning}," {sidekick.id} whispered.'
    )
    world.say(
        f'{hero.id} stared toward {scene.dark_spot} and held still, listening.'
    )


def misunderstanding(world: World, hero: Entity, sidekick: Entity, mis: Misunderstanding) -> None:
    world.facts["misunderstood"] = True
    world.say(
        f"But that was a misunderstanding. {mis.reveal.capitalize()}."
    )
    world.say(
        f"{sidekick.id} blinked, then laughed softly when the truth came out."
    )


def hazard_turn(world: World, hazard: Hazard) -> None:
    world.get("hazard").meters["danger"] += hazard.severity
    propagate(world, narrate=False)
    world.say(
        f"Inside {hazard.label}, something was {hazard.cause}, and the room felt tight with suspense."
    )


def fix(world: World, guardian: Entity, hazard: Hazard, gadget: Gadget) -> None:
    guardian.memes["calm"] += 1
    world.say(
        f"{guardian.id} came in with {gadget.phrase}. {gadget.glow.capitalize()}."
    )
    world.say(
        f"{guardian.id} used {hazard.fix}, and the problem loosened at once."
    )


def ending(world: World, hero: Entity, sidekick: Entity, gadget: Gadget) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"In the end, {hero.id} and {sidekick.id} stood together, smiling at the safe light."
    )
    world.say(
        f"Their {gadget.label} blinked, the coconut stayed just a coconut, the lint was only fluff, and the Tuckus purred along happily."
    )


# ---------------------------------------------------------------------------
# Story / QA
# ---------------------------------------------------------------------------
def tell(scene: Scene, mis: Misunderstanding, hazard: Hazard, gadget: Gadget,
         hero_name: str, hero_type: str, sidekick_name: str, sidekick_type: str,
         guardian_name: str, guardian_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type, role="sidekick"))
    guardian = world.add(Entity(id=guardian_name, kind="character", type=guardian_type, role="guardian"))
    world.add(Entity(id="hazard", type="thing", label=hazard.label))
    world.facts.update(scene=scene, misunderstanding=mis, hazard_cfg=hazard, gadget=gadget)

    setup(world, hero, sidekick, scene)
    world.para()
    suspense(world, hero, sidekick, scene, mis)
    hazard_turn(world, hazard)
    world.para()
    misunderstanding(world, hero, sidekick, mis)
    fix(world, guardian, hazard, gadget)
    world.para()
    ending(world, hero, sidekick, gadget)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        guardian=guardian,
        mis=mis,
        hazard=hazard,
        gadget=gadget,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a small child that includes the words "{f["mis"].id}", coconut, lint, and tuckus.',
        f"Tell a suspenseful but happy superhero story where {f['hero'].id} thinks {f['mis'].clue} means danger, but it turns out to be a misunderstanding.",
        f"Write a superhero tale with a misunderstanding, some suspense, and a happy ending, where the Tuckus and a coconut both show up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    guardian = f["guardian"]
    mis = f["mis"]
    hazard = f["hazard"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {sidekick.id}, and {guardian.id}, who were acting like a superhero team."),
        ("What made the story feel suspenseful?",
         f"{mis.clue} made everyone pause and listen. They thought it might be {mis.false_meaning}, so the moment felt tense until the truth came out."),
        ("What was the misunderstanding?",
         f"They first thought {mis.false_meaning}, but it was really {mis.true_meaning}. That mistake is what changed the worried moment into a happy one."),
        ("How did the problem get fixed?",
         f"{guardian.id} used {hazard.fix}, and the team calmed down. The danger was small, so the fix worked quickly and neatly."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a coconut?",
         "A coconut is a hard fruit with a shell. People can crack it open to eat or drink from it."),
        ("What is lint?",
         "Lint is soft fluff from fabric, like tiny fibers that come off clothes or blankets."),
        ("What is a misunderstanding?",
         "A misunderstanding is when someone thinks the wrong thing at first. Then the truth gets explained and the mix-up is cleared up."),
        ("What does suspense mean in a story?",
         "Suspense is the feeling of wondering what will happen next. It makes the story exciting for a moment."),
        ("What is a happy ending?",
         "A happy ending is when the problem gets solved and the characters finish feeling safe or glad."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        scene="rooftop",
        misunderstanding="coconut",
        hazard="sticky_door",
        gadget="signal_lamp",
        hero="Nova",
        hero_type="girl",
        sidekick="Zip",
        sidekick_type="boy",
        guardian="Captain Bright",
        guardian_type="man",
    ),
    StoryParams(
        scene="lab",
        misunderstanding="lint",
        hazard="glitchy_tuckus",
        gadget="cape_beacon",
        hero="Piper",
        hero_type="girl",
        sidekick="Rae",
        sidekick_type="girl",
        guardian="Aunt Comet",
        guardian_type="aunt",
    ),
    StoryParams(
        scene="harbor",
        misunderstanding="tuckus",
        hazard="coconut_crate",
        gadget="signal_lamp",
        hero="Milo",
        hero_type="boy",
        sidekick="Finn",
        sidekick_type="boy",
        guardian="Chief Spark",
        guardian_type="man",
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = args.scene if hasattr(args, "scene") and args.scene else rng.choice(list(SCENES))
    misunderstanding = args.misunderstanding if hasattr(args, "misunderstanding") and args.misunderstanding else rng.choice(list(MISUNDERSTANDINGS))
    hazard = args.hazard if hasattr(args, "hazard") and args.hazard else rng.choice(list(HAZARDS))
    gadget = args.gadget if hasattr(args, "gadget") and args.gadget else rng.choice(list(GADGETS))
    hero = args.hero if hasattr(args, "hero") and args.hero else rng.choice(HERO_NAMES)
    sidekick = args.sidekick if hasattr(args, "sidekick") and args.sidekick else rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    guardian = args.guardian if hasattr(args, "guardian") and args.guardian else rng.choice(GUARDIAN_NAMES)
    hero_type = args.hero_type if hasattr(args, "hero_type") and args.hero_type else rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type if hasattr(args, "sidekick_type") and args.sidekick_type else rng.choice(["girl", "boy"])
    guardian_type = args.guardian_type if hasattr(args, "guardian_type") and args.guardian_type else rng.choice(["man", "woman", "aunt", "uncle"])
    if scene not in SCENES or misunderstanding not in MISUNDERSTANDINGS or hazard not in HAZARDS or gadget not in GADGETS:
        raise StoryError("Invalid selection for this storyworld.")
    return StoryParams(
        scene=scene,
        misunderstanding=misunderstanding,
        hazard=hazard,
        gadget=gadget,
        hero=hero,
        hero_type=hero_type,
        sidekick=sidekick,
        sidekick_type=sidekick_type,
        guardian=guardian,
        guardian_type=guardian_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"Unknown scene: {params.scene}")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"Unknown misunderstanding: {params.misunderstanding}")
    if params.hazard not in HAZARDS:
        raise StoryError(f"Unknown hazard: {params.hazard}")
    if params.gadget not in GADGETS:
        raise StoryError(f"Unknown gadget: {params.gadget}")
    world = tell(
        SCENES[params.scene],
        MISUNDERSTANDINGS[params.misunderstanding],
        HAZARDS[params.hazard],
        GADGETS[params.gadget],
        params.hero,
        params.hero_type,
        params.sidekick,
        params.sidekick_type,
        params.guardian,
        params.guardian_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style storyworld with coconut, lint, tuckus, suspense, and a happy ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
    ap.add_argument("--guardian")
    ap.add_argument("--guardian-type", choices=["man", "woman", "aunt", "uncle"])
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


ASP_RULES = r"""
valid(S,M,H) :- scene(S), misunderstanding(M), hazard(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test completed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, misunderstanding, hazard) combos:")
        for s, m, h in combos:
            print(f"  {s:10} {m:16} {h}")
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
            params = resolve_params(args, random.Random(seed))
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
