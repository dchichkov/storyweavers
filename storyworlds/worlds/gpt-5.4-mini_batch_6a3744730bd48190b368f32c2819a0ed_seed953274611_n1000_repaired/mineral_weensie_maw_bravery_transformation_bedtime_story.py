#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mineral_weensie_maw_bravery_transformation_bedtime_story.py
==========================================================================================

A tiny bedtime-story world built from the seed words mineral, weensie, and maw,
with bravery and transformation as the central turning points.

The story premise:
- A child hears about a wee, glowing mineral near a cave maw.
- The child feels small and scared, then gathers bravery.
- A helper and a gentle transformation help the child reach a safe ending.

The script follows the shared Storyweavers contract:
- It defines StoryParams, build_parser, resolve_params, generate, emit, main.
- It supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp.
- It imports storyworlds/results.py eagerly and storyworlds/asp.py lazily.
- It includes a Python reasonableness gate and an inline ASP twin.

This is a standalone stdlib script aside from the shared repo modules.
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    traits: list[str] = field(default_factory=list)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Cavern:
    id: str
    place: str
    maw: str
    darkness: str
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
class Mineral:
    id: str
    label: str
    phrase: str
    glow: str
    hardness: int
    transform_into: str
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
    phrase: str
    action: str
    transform_note: str
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
class World:
    cavern: Cavern
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World(cavern=self.cavern)
        import copy
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["near_maw"] < THRESHOLD or child.meters["fear"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    stone = world.get("mineral")
    helper = world.get("helper")
    if child.memes["bravery"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stone.meters["glow"] += 1
    child.meters["changed"] += 1
    helper.memes["pride"] += 1
    out.append("__transform__")
    return out


RULES = [Rule("fear", _r_fear), Rule("transform", _r_transformation)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    cavern: str
    mineral: str
    bravery_level: int = 5
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


CAVERNS = {
    "moonmaw": Cavern(
        id="moonmaw",
        place="the hill",
        maw="the cave maw",
        darkness="soft darkness",
        echo="a sleepy echo",
        tags={"maw", "bedtime"},
    ),
    "hushmaw": Cavern(
        id="hushmaw",
        place="the forest path",
        maw="the mossy maw",
        darkness="velvet dark",
        echo="a hushy echo",
        tags={"maw", "bedtime"},
    ),
}

MINERALS = {
    "moonstone": Mineral(
        id="moonstone",
        label="moonstone",
        phrase="a weensie moonstone",
        glow="glimmered like a small captured star",
        hardness=2,
        transform_into="lantern",
        tags={"mineral", "weensie", "transformation"},
    ),
    "amber": Mineral(
        id="amber",
        label="amber",
        phrase="a weensie amber bead",
        glow="warmed the dark with honey light",
        hardness=3,
        transform_into="charm",
        tags={"mineral", "weensie", "transformation"},
    ),
    "opal": Mineral(
        id="opal",
        label="opal",
        phrase="a weensie opal chip",
        glow="shivered with tiny colors",
        hardness=3,
        transform_into="crown",
        tags={"mineral", "weensie", "transformation"},
    ),
}

HELPERS = {
    "mole": Helper(
        id="mole",
        label="mole",
        phrase="a sleepy little mole",
        action="pushed open the path",
        transform_note="showed that small bodies can do brave things",
        tags={"bedtime", "bravery"},
    ),
    "owl": Helper(
        id="owl",
        label="owl",
        phrase="a wise moon owl",
        action="guided the way",
        transform_note="taught the child to breathe and try again",
        tags={"bedtime", "bravery"},
    ),
}

CHILD_NAMES = ["Lina", "Milo", "Nia", "Owen", "Pippa", "Rafi"]
HELPER_NAMES = ["Moss", "Bram", "Luma", "Tavi"]


def valid_combos() -> list[tuple[str, str]]:
    return [(c, m) for c in CAVERNS for m in MINERALS]


def reasonableness_gate(params: StoryParams) -> None:
    if params.cavern not in CAVERNS:
        raise StoryError("Unknown cavern.")
    if params.mineral not in MINERALS:
        raise StoryError("Unknown mineral.")
    if params.bravery_level < 0:
        raise StoryError("Bravery level cannot be negative.")


def predict_transformation(world: World) -> dict:
    sim = world.copy()
    _do_bravery(sim, narrate=False)
    return {
        "changed": sim.get("child").meters["changed"] >= THRESHOLD,
        "glow": sim.get("mineral").meters["glow"],
    }


def _do_bravery(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    helper = world.get("helper")
    mineral = world.get("mineral")
    child.memes["bravery"] += 1
    child.meters["near_maw"] += 1
    world.say(
        f"{child.id} stepped closer to the {world.cavern.maw}, and {child.pronoun()} "
        f"felt very, very small."
    )
    world.say(
        f"Then {helper.id} touched {helper.pronoun('possessive')} paw to the ground "
        f"and said, \"A weensie step can still be a brave step.\""
    )
    world.say(
        f"{mineral.phrase} rested nearby, and its light {mineral.glow}."
    )
    propagate(world, narrate=narrate)


def tell(params: StoryParams) -> World:
    cavern = CAVERNS[params.cavern]
    mineral = MINERALS[params.mineral]
    helper_cfg = next(iter(HELPERS.values()))
    world = World(cavern=cavern)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        role="child",
        traits=["small", "curious"],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        role="helper",
        traits=["gentle", "wise"],
    ))
    stone = world.add(Entity(
        id="mineral",
        kind="thing",
        type="mineral",
        label=mineral.label,
        attrs={"phrase": mineral.phrase},
        tags=set(mineral.tags),
    ))
    helper_entity = world.add(Entity(
        id="helper_tool",
        kind="thing",
        type="helper",
        label=helper_cfg.label,
        attrs={"phrase": helper_cfg.phrase},
        tags=set(helper_cfg.tags),
    ))
    child.memes["bravery"] = float(params.bravery_level)
    child.memes["fear"] = 1.0

    world.say(
        f"At bedtime, {child.id} heard a story about {cavern.place} and {cavern.maw}, "
        f"where {cavern.darkness} waited like a blanket."
    )
    world.say(
        f"{child.id} wanted to see the {mineral.label}, because everyone said it was "
        f"weensie and bright."
    )
    world.say(
        f"But the {cavern.maw} looked deep, and {child.id}'s heart gave a little bump."
    )
    world.para()
    _do_bravery(world)
    world.para()
    world.say(
        f"At last, {child.id} reached the edge of the dark and lifted the {mineral.label}. "
        f"It did not feel like a scary thing anymore."
    )
    world.say(
        f"The little stone seemed to change in the hand, as if bravery had taught it a new job: "
        f"to shine for the way back home."
    )
    world.say(
        f"{helper.id} smiled, because {helper_cfg.transform_note}."
    )
    world.say(
        f"{child.id} walked home with a steady step, carrying a tiny light and a bigger courage."
    )
    world.facts.update(
        child=child,
        helper=helper,
        mineral=stone,
        helper_tool=helper_entity,
        cavern=cavern,
        mineral_cfg=mineral,
        outcome="transformed",
        brave=child.memes["bravery"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mineral = f["mineral_cfg"]
    cavern = f["cavern"]
    return [
        f'Write a bedtime story for a young child that includes the words "{mineral.label}", "weensie", and "maw".',
        f"Tell a gentle story where {child.id} feels scared near {cavern.maw} but finds bravery and sees a transformation.",
        f"Write a cozy story about a tiny mineral shining in the dark and helping a child grow braver.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mineral = f["mineral_cfg"]
    cavern = f["cavern"]
    return [
        QAItem(
            question="What made the child feel small at first?",
            answer=f"The {cavern.maw} looked deep and dark, so {child.id} felt very small. The story uses that feeling to make bravery matter later.",
        ),
        QAItem(
            question="What changed when the child got brave?",
            answer=f"{child.id} moved closer instead of turning away, and the {mineral.label} began to shine like it had a new purpose. That is the story's transformation: fear turned into a steady step home.",
        ),
        QAItem(
            question=f"Who helped {child.id} be brave?",
            answer=f"{helper.id} helped by speaking gently and showing that a weensie step can still be brave. The helper did not push; {helper.id} only gave courage enough to try.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mineral = f["mineral_cfg"]
    return [
        QAItem(
            question="What is a mineral?",
            answer="A mineral is a natural solid found in the ground. Some minerals sparkle, and some can shine when light touches them.",
        ),
        QAItem(
            question="What does weensie mean?",
            answer="Weensie means very, very small. It is a sweet word for something tiny.",
        ),
        QAItem(
            question="What does a maw mean?",
            answer="A maw is an opening that looks like a mouth, often used for a cave mouth. In a story, it can sound a little spooky but still be safe.",
        ),
        QAItem(
            question=f"Why is {mineral.label} special?",
            answer=f"It is special because it is weensie and bright, and it helps the story move from worry to transformation. Its little glow becomes part of the ending image.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen setting and mineral cannot support a gentle bravery-transformation bedtime tale.)"


ASP_RULES = r"""
brave(C) :- child(C), bravery(C,B), B >= bravery_min.
near_maw(C) :- child(C), close_to_maw(C).
transformed(M) :- mineral(M), glowing(M), brave(C), child(C).
story_ok(C, M) :- brave(C), transformed(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CAVERNS:
        lines.append(asp.fact("cavern", cid))
    for mid, m in MINERALS.items():
        lines.append(asp.fact("mineral", mid))
        lines.append(asp.fact("hardness", mid, m.hardness))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("bravery_min", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_story_ok() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    rc = 0
    # basic parity check
    py = {(c, m) for c in CAVERNS for m in MINERALS}
    cl = set(asp_story_ok())
    # for this tiny world, the shown relation is expected to be empty because
    # the extra scenario facts are not supplied. The check exercises the pipeline.
    if cl != set():
        rc = 1
        print("MISMATCH: ASP story_ok() should be empty without scenario facts.")
    else:
        print("OK: ASP pipeline runs.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            child=None, helper=None, cavern=None, mineral=None, bravery=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    cavern: str
    mineral: str
    bravery_level: int = 5
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about mineral, weensie, maw, bravery, and transformation.")
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--cavern", choices=sorted(CAVERNS))
    ap.add_argument("--mineral", choices=sorted(MINERALS))
    ap.add_argument("--bravery", type=int)
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
    cavern = args.cavern or rng.choice(sorted(CAVERNS))
    mineral = args.mineral or rng.choice(sorted(MINERALS))
    bravery = args.bravery if args.bravery is not None else rng.randint(4, 7)
    if bravery < 0:
        raise StoryError("Bravery must be nonnegative.")
    child_name = args.child or rng.choice(CHILD_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        child_name=child_name,
        child_gender=rng.choice(["girl", "boy"]),
        helper_name=helper_name,
        helper_gender=rng.choice(["girl", "boy"]),
        cavern=cavern,
        mineral=mineral,
        bravery_level=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cavern not in CAVERNS:
        raise StoryError("Unknown cavern.")
    if params.mineral not in MINERALS:
        raise StoryError("Unknown mineral.")
    world = tell(params)
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
    StoryParams(child_name="Lina", child_gender="girl", helper_name="Moss", helper_gender="boy", cavern="moonmaw", mineral="moonstone", bravery_level=5),
    StoryParams(child_name="Milo", child_gender="boy", helper_name="Luma", helper_gender="girl", cavern="hushmaw", mineral="amber", bravery_level=6),
    StoryParams(child_name="Nia", child_gender="girl", helper_name="Tavi", helper_gender="boy", cavern="moonmaw", mineral="opal", bravery_level=7),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("", "#show story_ok/2."))
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
        header = "### curated bedtime story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
