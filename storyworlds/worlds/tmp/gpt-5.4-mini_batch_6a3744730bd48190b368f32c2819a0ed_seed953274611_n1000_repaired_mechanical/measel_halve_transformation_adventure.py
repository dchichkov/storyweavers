#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/measel_halve_transformation_adventure.py
=========================================================================

A small adventure storyworld about a child, a strange little measel, and a
careful transformation that helps them finish a journey.

The seed words are woven in literally:
- "measel" appears as the name of a tiny cave-guide creature.
- "halve" appears as the action of splitting a trail snack and the spell word
  the child must say carefully.

The world is modeled with typed entities, physical meters, and emotional memes.
One concrete turn drives the story: the measel can transform only after it gets
split-share fuel, and that transformation helps the explorers cross a risky
path and reach a bright ending image.

This file is standalone and follows the shared Storyweavers result contract.
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    dangerous: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    transforms: bool = False
    risky: bool = False
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
class Creature:
    id: str
    label: str
    phrase: str
    kind: str = "measel"
    small: bool = True
    can_transform: bool = True
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    scout = world.entities.get("measel")
    if not scout or scout.meters["fed"] < THRESHOLD:
        return out
    if scout.meters["transformed"] >= THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scout.meters["transformed"] += 1
    scout.memes["spark"] += 1
    path = world.entities.get("path")
    if path:
        path.meters["open"] += 1
    out.append("__transform__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    scout = world.entities.get("child")
    guide = world.entities.get("measel")
    if not scout or not guide:
        return out
    if guide.meters["transformed"] < THRESHOLD:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scout.memes["joy"] += 1
    scout.memes["bravery"] += 1
    out.append("The little trail felt less scary at once.")
    return out


CAUSAL_RULES = [Rule("transform", _r_transform), Rule("bravery", _r_bravery)]


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


def fed_meal(kind: str) -> bool:
    return kind in {"half_cookie", "trail_cracker"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for tool_id, tool in TOOLS.items():
            for creature_id, creature in CREATURES.items():
                if place.dark and tool.transforms and creature.can_transform:
                    combos.append((place_id, tool_id, creature_id))
    return combos


@dataclass
class StoryParams:
    place: str
    tool: str
    creature: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    snack: str
    delay: int = 0
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
    ap = argparse.ArgumentParser(description="Adventure storyworld about measel and halve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--snack", choices=["half_cookie", "trail_cracker"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.creature is None or c[2] == args.creature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, creature = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    snack = args.snack or rng.choice(["half_cookie", "trail_cracker"])
    return StoryParams(place=place, tool=tool, creature=creature, child_name=child_name,
                       child_gender=child_gender, helper_name=helper_name,
                       helper_gender=helper_gender, snack=snack)


def predict(world: World) -> dict:
    sim = world.copy()
    do_feed(sim, narrate=False)
    return {"transformed": sim.get("measel").meters["transformed"] >= THRESHOLD}


def do_setup(world: World, child: Entity, helper: Entity, place: Place, creature: Creature) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At {place.label}, {child.id} and {helper.id} found a tiny {creature.label} "
        f"skipping beside a dark path."
    )
    world.say(
        f"The {creature.label} looked small enough to fit in a pocket, but its eyes "
        f"kept glancing toward the cave turn."
    )


def do_need(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"The way ahead was { 'very dark' if place.dark else 'shadowy' }, and "
        f"{child.id} could not see the far stones."
    )
    world.say(f'"We need a guide," {child.id} whispered.')


def do_worry(world: World, helper: Entity, tool: Tool) -> None:
    helper.memes["warning"] += 1
    world.say(
        f'{helper.id} touched the little bundle in {helper.pronoun("possessive")} pack. '
        f'"Maybe the {tool.label} can help, but only if we use it the right way."'
    )


def do_halve(world: World, child: Entity, helper: Entity, tool: Tool, creature: Creature) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'{child.id} remembered the trail riddle and said, "Let us {tool.label}!" '
        f'Then {helper.id} took out a snack and helped {child.id} halve it.'
    )
    if fed_meal(world.facts["snack"]):
        world.get("measel").meters["fed"] += 1
        world.say(
            f"The measel nibbled the half snack, and its fur began to shine like a tiny torch."
        )
    else:
        world.say("The measel sniffed, but the snack was no good for adventure.")


def do_feed(world: World, narrate: bool = True) -> None:
    propagate(world, narrate=narrate)


def do_transform_story(world: World, child: Entity, creature: Creature, place: Place) -> None:
    if world.get("measel").meters["transformed"] >= THRESHOLD:
        world.say(
            f"With a soft pop, the measel transformed into a bright cave guide, "
            f"its tail curling into a glowing arrow."
        )
        if place.dangerous:
            world.say(
                f"It pointed around the broken stones, and the path opened safely."
            )
        else:
            world.say(
                f"It pointed to the good trail, and the adventure felt easy at once."
            )
        child.memes["confidence"] += 1


def do_end(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"{child.id} followed the shining guide, {helper.id} right behind, and the team "
        f"walked on until the cave mouth glowed gold."
    )
    world.say(
        f"By the end, the measel was not little and shy anymore; it was a brave lantern-like friend."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    creature = CREATURES[params.creature]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    world.add(Entity(id="measel", kind="character", type="measel", label=creature.label, role="guide"))
    world.add(Entity(id="path", kind="thing", type="path", label="the path"))

    world.facts.update(place=place, tool=tool, creature=creature, snack=params.snack,
                       child=child, helper=helper, outcome="", transformed=False)

    do_setup(world, child, helper, place, creature)
    world.para()
    do_need(world, child, place)
    do_worry(world, helper, tool)
    do_halve(world, child, helper, tool, creature)
    world.para()
    do_feed(world)
    do_transform_story(world, child, creature, place)
    do_end(world, child, helper, place)

    world.facts["transformed"] = world.get("measel").meters["transformed"] >= THRESHOLD
    world.facts["outcome"] = "transformed" if world.facts["transformed"] else "notransform"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words '
        f'"measel" and "halve".',
        f"Tell a gentle cave adventure where {f['child'].id} meets a measel, "
        f"shares a snack, and the measel can transform into a guide.",
        f"Write a short transformation story where saying the right tiny word and "
        f"sharing food helps a measel brighten the trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    qa = [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{child.id} and {helper.id} went on the adventure, and they met a little measel on the trail."
        ),
        QAItem(
            question="What had to happen before the measel changed?",
            answer=f"{child.id} and {helper.id} had to halve their trail snack and share it with the measel. That small act gave the creature enough strength to transform."
        ),
    ]
    if f["transformed"]:
        qa.append(QAItem(
            question="What did the measel become?",
            answer="The measel transformed into a bright cave guide. It was no longer just shy and small; it showed the way through the dark place."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does halve mean?",
            answer="To halve something means to split it into two equal parts. People can halve a snack so each person gets half."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change from one form or kind to another. In stories, a creature can transform when magic or a special event changes it."
        ),
        QAItem(
            question="Why is a dark trail hard to cross?",
            answer="A dark trail is hard to cross because you cannot see the stones or holes well. A guide or a light can help keep everyone safe."
        ),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACES = {
    "cave": Place(id="cave", label="the cave", dark=True, dangerous=True, tags={"dark"}),
    "ruins": Place(id="ruins", label="the old ruins", dark=True, dangerous=True, tags={"dark"}),
    "glen": Place(id="glen", label="the moonlit glen", dark=False, dangerous=False, tags={"light"}),
}

TOOLS = {
    "halve": Tool(id="halve", label="halve", phrase="a tiny halve-word", transforms=True, risky=False, tags={"transform"}),
    "glow": Tool(id="glow", label="glow charm", phrase="a glow charm", transforms=True, risky=False, tags={"transform"}),
    "spark": Tool(id="spark", label="spark key", phrase="a spark key", transforms=True, risky=False, tags={"transform"}),
}

CREATURES = {
    "measel": Creature(id="measel", label="measel", phrase="a little measel", tags={"measel", "transform"}),
    "measelkin": Creature(id="measelkin", label="measelkin", phrase="a small measelkin", tags={"measel", "transform"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Arlo", "Finn", "Owen", "Theo", "Jude", "Max"]

CURATED = [
    StoryParams(place="cave", tool="halve", creature="measel", child_name="Mina", child_gender="girl", helper_name="Arlo", helper_gender="boy", snack="half_cookie", delay=0),
    StoryParams(place="ruins", tool="glow", creature="measelkin", child_name="Finn", child_gender="boy", helper_name="Lila", helper_gender="girl", snack="trail_cracker", delay=0),
]


def explain_rejection(place: Place, tool: Tool, creature: Creature) -> str:
    return f"(No story: this adventure needs a dark place, a transforming tool, and a creature like {creature.label}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.dangerous:
            lines.append(asp.fact("dangerous", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.transforms:
            lines.append(asp.fact("transforms", tid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if c.can_transform:
            lines.append(asp.fact("can_transform", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,C) :- place(P), tool(T), creature(C), dark(P), transforms(T), can_transform(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) == set(valid_combos()):
            print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        else:
            rc = 1
            print("MISMATCH between clingo and Python valid_combos().")
        sample = generate(resolve_params(argparse.Namespace(place=None, tool=None, creature=None, snack=None, name=None, helper=None, gender=None, helper_gender=None), random.Random(7)))
        if not sample.story or "measel" not in sample.story or "halve" not in sample.story:
            rc = 1
            print("MISMATCH: smoke test story missing required content.")
        else:
            print("OK: smoke test story generated successfully.")
    except Exception:
        rc = 1
        traceback.print_exc()
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.tool not in TOOLS or params.creature not in CREATURES:
        raise StoryError("Invalid params.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.creature is None or c[2] == args.creature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, creature = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    snack = args.snack or rng.choice(["half_cookie", "trail_cracker"])
    return StoryParams(place=place, tool=tool, creature=creature, child_name=child_name,
                       child_gender=child_gender, helper_name=helper_name,
                       helper_gender=helper_gender, snack=snack)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for tid, t in TOOLS.items():
            for cid, c in CREATURES.items():
                if p.dark and t.transforms and c.can_transform:
                    combos.append((pid, tid, cid))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
