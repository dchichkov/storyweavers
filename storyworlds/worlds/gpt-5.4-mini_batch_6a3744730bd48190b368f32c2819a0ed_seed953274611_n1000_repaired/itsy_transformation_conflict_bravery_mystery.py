#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/itsy_transformation_conflict_bravery_mystery.py
=================================================================================

A standalone storyworld about a tiny mystery: a child follows itysized clues,
meets a conflict, acts bravely, and witnesses a transformation that solves the
puzzle.

The world is intentionally small and classical:
- one child protagonist
- one tiny mysterious object/creature
- one pressure/conflict
- one brave action
- one transformation outcome

The story reads like a child-facing mystery with a concrete ending image.
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
BRAVERY_INIT = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    darkness: str
    mystery_image: str
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
class MysteryThing:
    id: str
    label: str
    clue: str
    revealed: str
    tiny_detail: str
    transform_to: str
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
class Conflict:
    id: str
    label: str
    danger: str
    pressure: str
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
class BraveryMove:
    id: str
    label: str
    method: str
    result: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
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


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["fear"] >= THRESHOLD and ("bravery", "child") not in world.fired:
        world.fired.add(("bravery", "child"))
        child.memes["bravery"] += 1
        child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
        out.append("__bravery__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("itsy")
    if clue.meters["revealed"] >= THRESHOLD and ("transform", "itsy") not in world.fired:
        world.fired.add(("transform", "itsy"))
        clue.meters["transformed"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("bravery", _r_bravery), Rule("transform", _r_transform)]


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


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    simulate_discovery(sim, narrate=False)
    return {
        "revealed": sim.get("itsy").meters["revealed"] >= THRESHOLD,
        "transformed": sim.get("itsy").meters["transformed"] >= THRESHOLD,
    }


def simulate_discovery(world: World, narrate: bool = True) -> None:
    clue = world.get("itsy")
    clue.meters["revealed"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, setting: Setting, clue: MysteryThing) -> None:
    world.say(
        f"That night, {child.id} wandered into {setting.place}, where the air felt "
        f"still and {setting.darkness}."
    )
    world.say(
        f"Near the floor, {child.id} noticed an {clue.label} clue -- so {clue.tiny_detail} "
        f"it was easy to miss."
    )
    child.memes["curiosity"] += 1


def question(world: World, child: Entity, clue: MysteryThing) -> None:
    child.memes["mystery"] += 1
    world.say(
        f'"What are you hiding?" {child.id} whispered. The clue looked ordinary, '
        f"but it seemed to point somewhere."
    )


def conflict_scene(world: World, child: Entity, conflict: Conflict, setting: Setting) -> None:
    child.memes["fear"] += 1
    world.say(
        f"Then {conflict.label} stirred in the corner. {conflict.danger} {conflict.pressure}."
    )
    world.say(
        f"The small room felt larger and lonelier, and even the shadows around "
        f"{setting.mystery_image} seemed to hold their breath."
    )


def brave_action(world: World, child: Entity, move: BraveryMove, clue: MysteryThing) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} took a shaky breath and chose to be brave. {move.method}."
    )
    simulate_discovery(world, narrate=False)
    world.say(move.result.format(clue=clue.label))


def reveal(world: World, child: Entity, clue: MysteryThing, setting: Setting) -> None:
    world.get("itsy").meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {clue.label} was not a warning at all. It was the first sign that "
        f"something tiny was about to change."
    )
    world.say(
        f"With one soft shimmer, the {clue.label} transformed into {clue.revealed}, "
        f"bright against {setting.mystery_image}."
    )


def ending(world: World, child: Entity, clue: MysteryThing) -> None:
    child.memes["relief"] += 1
    world.say(
        f"{child.id} smiled at the new shape and kept the little {clue.transform_to} "
        f"cupped safely in both hands."
    )
    world.say(
        "The mystery was solved, and the night no longer felt strange -- only "
        "quiet, glowing, and a little magical."
    )


def tell(setting: Setting, clue: MysteryThing, conflict: Conflict, move: BraveryMove,
         child_name: str = "Nia", child_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    world.add(Entity(id="setting", type="setting", label=setting.place, tags=setting.tags))
    itsy = world.add(Entity(id="itsy", type="thing", label=clue.label, tags=clue.tags))
    child.memes["bravery"] = BRAVERY_INIT

    setup(world, child, setting, clue)
    world.para()
    question(world, child, clue)
    conflict_scene(world, child, conflict, setting)
    world.para()
    brave_action(world, child, move, clue)
    reveal(world, child, clue, setting)
    ending(world, child, clue)

    world.facts.update(
        child=child,
        setting=setting,
        clue=clue,
        conflict=conflict,
        move=move,
        itsy=itsy,
        revealed=itsy.meters["revealed"] >= THRESHOLD,
        transformed=itsy.meters["transformed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        darkness="dusty and dim",
        mystery_image="the cobwebby window",
        tags={"attic", "dark"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden shed",
        darkness="full of old shadows",
        mystery_image="the rain-speckled glass",
        tags={"garden", "dark"},
    ),
    "closet": Setting(
        id="closet",
        place="the hallway closet",
        darkness="small and secret",
        mystery_image="the coat hooks",
        tags={"closet", "dark"},
    ),
}

MYSTERY_THINGS = {
    "glowseed": MysteryThing(
        id="glowseed",
        label="itsy",
        clue="an itsy silver seed",
        revealed="a tiny moonflower",
        tiny_detail="small and pale",
        transform_to="moonflower",
        tags={"itsy", "seed", "transform"},
    ),
    "lanternbug": MysteryThing(
        id="lanternbug",
        label="itsy",
        clue="an itsy glass bug",
        revealed="a little lantern bug",
        tiny_detail="no bigger than a button",
        transform_to="lantern bug",
        tags={"itsy", "bug", "transform"},
    ),
    "paperfold": MysteryThing(
        id="paperfold",
        label="itsy",
        clue="an itsy folded note",
        revealed="a map shaped like a star",
        tiny_detail="folded into a pebble-sized square",
        transform_to="star map",
        tags={"itsy", "note", "transform"},
    ),
}

CONFLICTS = {
    "cat": Conflict(
        id="cat",
        label="a hissing cat",
        danger="Its whiskers bristled, and it blocked the path.",
        pressure="It would not let anyone near the clue.",
        tags={"conflict", "cat"},
    ),
    "wind": Conflict(
        id="wind",
        label="a hard wind",
        danger="It rattled the loose boards and shook the lamp.",
        pressure="It kept trying to blow the tiny clue away.",
        tags={"conflict", "wind"},
    ),
    "door": Conflict(
        id="door",
        label="a stuck door",
        danger="The latch held tight, and the room felt trapped.",
        pressure="It made the child feel nervous about stepping closer.",
        tags={"conflict", "door"},
    ),
}

BRAVERY_MOVES = {
    "lamp": BraveryMove(
        id="lamp",
        label="lantern",
        method="Nia lifted a little lamp and held it steady with both hands",
        result="The light touched the clue, and the room finally gave up its secret.",
        tags={"bravery", "light"},
    ),
    "call": BraveryMove(
        id="call",
        label="call",
        method="Nia called softly for help, then stood her ground instead of running",
        result="The brave call made the hiding place feel safe enough to open.",
        tags={"bravery", "help"},
    ),
    "step": BraveryMove(
        id="step",
        label="step",
        method="Nia took one small step forward and did not look away",
        result="That tiny step was enough to let the clue shine in the dark.",
        tags={"bravery", "step"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    conflict: str
    bravery: str
    child_name: str = "Nia"
    child_gender: str = "girl"
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


CURATED = [
    StoryParams(setting="attic", mystery="glowseed", conflict="cat", bravery="lamp", child_name="Nia", child_gender="girl"),
    StoryParams(setting="garden", mystery="lanternbug", conflict="wind", bravery="call", child_name="Milo", child_gender="boy"),
    StoryParams(setting="closet", mystery="paperfold", conflict="door", bravery="step", child_name="Ada", child_gender="girl"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERY_THINGS:
            for c in CONFLICTS:
                for b in BRAVERY_MOVES:
                    combos.append((s, m, c, b))
    return combos


def explain_rejection(_: str) -> str:
    return "(No story: this mystery world accepts the listed tiny clues, conflicts, and brave moves.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about itsy clues, conflict, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERY_THINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--bravery", choices=BRAVERY_MOVES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.conflict is None or c[2] == args.conflict)
              and (args.bravery is None or c[3] == args.bravery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, conflict, bravery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Nia", "Milo", "Ada", "Theo", "Iris", "Pip"])
    return StoryParams(setting=setting, mystery=mystery, conflict=conflict, bravery=bravery, child_name=name, child_gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "itsy" and ends with a transformation.',
        f"Tell a brave little mystery about {f['child'].id} in {f['setting'].place} where an itsy clue leads to a bigger surprise.",
        f'Write a short mystery where a tiny thing seems puzzling at first, then changes when someone is brave enough to look closer.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    clue = f["clue"]
    conflict = f["conflict"]
    move = f["move"]
    setting = f["setting"]
    answers = [
        QAItem(
            question="What was the mystery clue?",
            answer=f"It was {clue.clue}. At first it looked tiny and ordinary, but it was hiding a bigger secret."
        ),
        QAItem(
            question="What got in the way of the child?",
            answer=f"{conflict.label} did. It made the scene tense and kept the child from walking straight to the clue."
        ),
        QAItem(
            question="How did the child solve the mystery?",
            answer=f"{child.id} chose a brave move: {move.method}. That let the clue be seen clearly, and the hidden change could finally happen."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The {clue.label} transformed into {clue.revealed}, and the dark place felt peaceful instead of puzzling."
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean when something is tiny?", answer="It means it is very small, little, or hard to notice."),
        QAItem(question="What is bravery?", answer="Bravery is doing the right thing even when you feel scared."),
        QAItem(question="What is a mystery?", answer="A mystery is something puzzling that you try to figure out."),
        QAItem(question="What is transformation?", answer="Transformation means something changes into a new form or a new way of being."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, mystery: MysteryThing, conflict: Conflict, bravery: BraveryMove, child_name: str, child_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    world.add(Entity(id="setting", type="setting", label=setting.place, tags=setting.tags))
    itsy = world.add(Entity(id="itsy", type="thing", label=mystery.label, tags=mystery.tags))
    world.add(Entity(id="conflict", type="thing", label=conflict.label, tags=conflict.tags))
    world.add(Entity(id="bravery", type="thing", label=bravery.label, tags=bravery.tags))
    child.memes["bravery"] = BRAVERY_INIT

    world.say(f"At {setting.place}, the night felt {setting.darkness}.")
    world.say(f"{child.id} found {mystery.clue}, an itsy clue that was {mystery.tiny_detail}.")
    world.para()
    world.say(f"Then {conflict.label} appeared. {conflict.danger} {conflict.pressure}")
    child.memes["fear"] += 1
    world.para()
    child.memes["bravery"] += 1
    world.say(f"{child.id} did not run away. {bravery.method}.")
    itsy.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(f"The tiny clue transformed into {mystery.revealed}, and the mystery made sense at last.")
    world.say(f"{child.id} held the new {mystery.transform_to} close and smiled at the quiet dark.")

    world.facts.update(child=child, setting=setting, clue=mystery, conflict=conflict, move=bravery, itsy=itsy)
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERY_THINGS or params.conflict not in CONFLICTS or params.bravery not in BRAVERY_MOVES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], MYSTERY_THINGS[params.mystery], CONFLICTS[params.conflict], BRAVERY_MOVES[params.bravery], params.child_name, params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
setting(attic). setting(garden). setting(closet).
mystery(glowseed). mystery(lanternbug). mystery(paperfold).
conflict(cat). conflict(wind). conflict(door).
bravery(lamp). bravery(call). bravery(step).
valid(S,M,C,B) :- setting(S), mystery(M), conflict(C), bravery(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERY_THINGS:
        lines.append(asp.fact("mystery", m))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    for b in BRAVERY_MOVES:
        lines.append(asp.fact("bravery", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
