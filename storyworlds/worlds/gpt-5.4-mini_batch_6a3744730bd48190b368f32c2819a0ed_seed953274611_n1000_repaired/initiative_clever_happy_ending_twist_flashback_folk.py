#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/initiative_clever_happy_ending_twist_flashback_folk.py
======================================================================================

A tiny folk-tale storyworld about initiative, cleverness, a mistaken loss, a
flashback that explains it, and a happy ending with a twist.

Premise
-------
A child notices a problem in a village, takes initiative, and uses cleverness
instead of force. The story first seems like a simple search for something lost,
then reveals via flashback that the "loss" began with a forgotten kindness. The
twist is that the missing thing was never truly stolen: it was borrowed by the
village's own helpful creature, who needed it for a good reason. The ending is
happy because the child listens, remembers, and returns with a practical plan.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-causal simulation that drives prose
- a Python reasonableness gate plus an inline ASP twin
- story-grounded and world-knowledge QA generated from world state, not prose

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
BRAVE_INIT = 3.0
COWARDLY_INIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
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
    mood: str
    details: str
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
class LostThing:
    id: str
    label: str
    phrase: str
    owner: str
    useful_for: str
    can_be_borrowed: bool = True
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
class HelpfulCreature:
    id: str
    label: str
    phrase: str
    reason: str
    return_time: str
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
class Plan:
    id: str
    method: str
    cleverness: int
    success_power: int
    text: str
    twist_text: str
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
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    elder_name: str
    elder_gender: str
    lost_thing: str
    creature: str
    plan: str
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
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("thing_missing") and "child" in world.entities:
        child = world.get("child")
        if child.memes["worry"] < THRESHOLD:
            child.memes["worry"] += 1
            out.append("")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("thing_returned") and "child" in world.entities:
        child = world.get("child")
        if child.memes["relief"] < THRESHOLD:
            child.memes["relief"] += 1
            out.append("")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("relief", "social", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            before = tuple((e.id, dict(e.memes)) for e in world.entities.values())
            rule.apply(world)
            after = tuple((e.id, dict(e.memes)) for e in world.entities.values())
            if before != after:
                changed = True
    if narrate:
        pass


def remind_flashback(world: World, child: Entity, elder: Entity, creature: Entity, thing: Entity) -> None:
    world.say(
        f"That evening, when the lantern was low, {elder.id} told a story from long ago."
    )
    world.say(
        f"In that story, {thing.label_word} had been left on the hearth for the winter night, "
        f"so {creature.id} took it to keep the village warm and made sure it would come back."
    )
    world.say(
        f"Now {child.id} understood: the thing had not been lost to greed at all, only borrowed by a kind friend."
    )


def child_init(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["initiative"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, {child.id} was the kind of child who took initiative."
    )
    world.say(
        f"{child.id} was clever too, quick to notice when something did not fit the day."
    )


def village_problem(world: World, child: Entity, thing: Entity, setting: Setting) -> None:
    thing.meters["missing"] += 1
    world.facts["thing_missing"] = True
    world.say(
        f"At the market square, a hush fell because {thing.label_word} was gone from its usual place."
    )
    world.say(
        f"The villagers looked around the {setting.mood} square, but no one could find it."
    )
    child.memes["worry"] += 1


def clever_search(world: World, child: Entity, helper: Entity, thing: Entity, creature: Entity, plan: Plan) -> None:
    helper.memes["hope"] += 1
    world.say(
        f"{child.id} did not waste a breath. {child.id} asked the right questions and followed the small clues."
    )
    world.say(
        f"Then {child.id} tried a clever idea: {plan.text}."
    )
    if plan.id == "crumb_trail":
        world.say(
            f"By watching the crumbs and the mud, {child.id} realized the trail led toward the old bridge."
        )
    elif plan.id == "lantern_call":
        world.say(
            f"{child.id} held a lantern high and saw a tiny mark on the path, just where a careful friend had passed."
        )
    else:
        world.say(
            f"{child.id} listened for soft footsteps and heard a gentle rustle near the willow tree."
        )


def twist(world: World, creature: Entity, thing: Entity, helper: Entity, child: Entity, plan: Plan) -> None:
    creature.meters["holding"] += 1
    if creature.attrs.get("borrowed_reason"):
        world.say(
            f"At first it seemed like a theft, but the truth gave the tale a twist."
        )
        world.say(
            f"{creature.id} had borrowed {thing.label_word} for a good reason: {creature.attrs['borrowed_reason']}."
        )
    else:
        world.say(
            f"At the bridge, the surprise was kinder than anyone expected: {creature.id} had kept {thing.label_word} safe all along."
        )
    world.say(
        f"{helper.id} blinked, then laughed with relief, because the problem was smaller than the fear around it."
    )


def return_and_end(world: World, child: Entity, elder: Entity, creature: Entity, thing: Entity, plan: Plan) -> None:
    thing.meters["missing"] = 0
    world.facts["thing_returned"] = True
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    elder.memes["pride"] += 1
    world.say(
        f"{child.id} used {plan.method} to help carry {thing.label_word} back, and everyone thanked {creature.id} for the honest care."
    )
    world.say(
        f"By sunrise, {thing.label_word} was home again, and the village square shone bright and whole."
    )
    world.say(
        f"{child.id} stood tall beside {elder.id}, happy that quick thinking had turned worry into a sweet ending."
    )


SETTINGS = {
    "village": Setting(
        id="village",
        place="the village",
        mood="quiet",
        details="stone paths and apple carts",
        tags={"folk", "village"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor",
        mood="windy",
        details="ropes, nets, and gulls",
        tags={"folk", "harbor"},
    ),
    "hill": Setting(
        id="hill",
        place="the hill town",
        mood="bright",
        details="green slopes and a little bell tower",
        tags={"folk", "hill"},
    ),
}

LOST_THINGS = {
    "lantern": LostThing(
        id="lantern",
        label="lantern",
        phrase="the old brass lantern",
        owner="village",
        useful_for="lighting the path at night",
        tags={"light", "lantern"},
    ),
    "key": LostThing(
        id="key",
        label="key",
        phrase="the iron key",
        owner="mill",
        useful_for="opening the granary",
        tags={"key"},
    ),
    "bell": LostThing(
        id="bell",
        label="bell",
        phrase="the small bell",
        owner="bridge",
        useful_for="calling workers home",
        tags={"bell"},
    ),
}

CREATURES = {
    "fox": HelpfulCreature(
        id="fox",
        label="fox",
        phrase="a quick fox",
        reason="to guide travelers through the dark path",
        return_time="before dawn",
        tags={"animal", "fox"},
    ),
    "crow": HelpfulCreature(
        id="crow",
        label="crow",
        phrase="a clever crow",
        reason="to free its nest from a snagged ribbon",
        return_time="at sunrise",
        tags={"animal", "crow"},
    ),
    "otter": HelpfulCreature(
        id="otter",
        label="otter",
        phrase="a shy otter",
        reason="to line a nest with something warm and dry",
        return_time="by morning",
        tags={"animal", "otter"},
    ),
}

PLANS = {
    "crumb_trail": Plan(
        id="crumb_trail",
        method="a trail of crumbs and a careful look at the mud",
        cleverness=3,
        success_power=3,
        text="left a thin trail of crumbs and followed the muddy prints",
        twist_text="the trail showed the way more clearly than shouting ever could",
        tags={"clever", "trail"},
    ),
    "lantern_call": Plan(
        id="lantern_call",
        method="a lantern held high and a soft call to the rooftops",
        cleverness=4,
        success_power=4,
        text="held a lantern high and looked for a glint in the dark",
        twist_text="the lantern showed not a thief, but a friend with careful paws",
        tags={"clever", "light"},
    ),
    "listen_first": Plan(
        id="listen_first",
        method="quiet listening at the old bridge",
        cleverness=2,
        success_power=2,
        text="listened under the bridge before making any guess",
        twist_text="what sounded like stealing was really a borrowed kindness",
        tags={"clever", "listening"},
    ),
}

GIRLS = ["Mira", "Elin", "Sara", "Tessa", "Nina"]
BOYS = ["Pavel", "Oren", "Jonas", "Arin", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in LOST_THINGS:
            for pid in PLANS:
                if reason_ok(LOST_THINGS[tid], CREATURES["fox"], PLANS[pid]):
                    combos.append((sid, tid, pid))
    return combos


def reason_ok(thing: LostThing, creature: HelpfulCreature, plan: Plan) -> bool:
    return thing.can_be_borrowed and plan.cleverness >= 2 and creature.reason


def explain_rejection(thing: LostThing, plan: Plan) -> str:
    return f"(No story: {plan.method} is not a fitting clever move for {thing.label_word}.)"


def explain_plan(rid: str) -> str:
    plan = PLANS[rid]
    return f"(Refusing plan '{rid}': the storyworld expects a clever enough plan, and this one is too plain.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of initiative and cleverness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lost-thing", choices=LOST_THINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    if args.plan and PLANS[args.plan].cleverness < 2:
        raise StoryError(explain_plan(args.plan))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.lost_thing is None or c[1] == args.lost_thing)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, lost_thing, plan = rng.choice(sorted(combos))
    thing = LOST_THINGS[lost_thing]
    creature = args.creature or rng.choice(sorted(CREATURES))
    gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRLS if gender == "girl" else BOYS)
    helper = args.helper or rng.choice(GIRLS if gender == "girl" else BOYS)
    elder = args.elder or rng.choice(GIRLS + BOYS)
    return StoryParams(setting=setting, child_name=name, child_gender=gender,
                       helper_name=helper, helper_gender="girl" if helper in GIRLS else "boy",
                       elder_name=elder, elder_gender="girl" if elder in GIRLS else "boy",
                       lost_thing=lost_thing, creature=creature, plan=plan)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    thing_cfg = LOST_THINGS[params.lost_thing]
    creature_cfg = CREATURES[params.creature]
    plan_cfg = PLANS[params.plan]
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    elder = world.add(Entity(id=params.elder_name, kind="character", type=params.elder_gender, role="elder"))
    thing = world.add(Entity(id="thing", kind="thing", type="thing", label=thing_cfg.label, attrs={"useful_for": thing_cfg.useful_for}))
    creature = world.add(Entity(id=creature_cfg.id, kind="character", type="thing", label=creature_cfg.label, attrs={"borrowed_reason": creature_cfg.reason}))
    child.memes["initiative"] = BRAVE_INIT
    helper.memes["hope"] = 1.0
    elder.memes["memory"] = 1.0

    child_init(world, child, helper, setting)
    village_problem(world, child, thing, setting)
    world.para()
    clever_search(world, child, helper, thing, creature, plan_cfg)
    world.say(f"The search wound through {setting.details}, and the question grew stranger.")
    world.para()
    twist(world, creature, thing, helper, child, plan_cfg)
    world.para()
    remind_flashback(world, child, elder, creature, thing)
    world.para()
    return_and_end(world, child, elder, creature, thing, plan_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        elder=elder,
        thing=thing,
        creature=creature,
        plan=plan_cfg,
        setting=setting,
        thing_missing=True,
        thing_returned=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale for a child that includes the words "initiative" and "clever".',
        f"Tell a happy village story where {f['child'].id} takes initiative to find a missing thing, and the ending has a twist and a flashback.",
        f"Write a gentle folk tale about a clever child, a helpful creature, and a happy ending after a mistaken worry.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    thing = f["thing"]
    creature = f["creature"]
    plan = f["plan"]
    elder = f["elder"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, a child who took initiative when something seemed wrong in the village."),
        (f"What made {child.id} clever?",
         f"{child.id} noticed small clues, asked careful questions, and chose a plan that fit the situation."),
        (f"What was the twist in the story?",
         f"The twist was that {creature.id} did not steal {thing.label_word} at all. {creature.id} had only borrowed it for a good reason."),
        (f"Why did the story need a flashback?",
         f"The flashback showed an older, forgotten kindness from before the search began. It explained why the missing thing was really part of a good deed."),
        (f"How did {child.id} help in the end?",
         f"{child.id} used {plan.method} to help bring {thing.label_word} home. That made the village happy again."),
    ]
    qa.append((
        "How did the story end?",
        f"It ended happily, with {thing.label_word} back where it belonged and {child.id} standing proud beside {elder.id}. The worry turned into relief and a warm village evening."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["plan"].tags) | set(world.facts["thing"].tags) | set(world.facts["creature"].tags)
    if "clever" in tags:
        out.append(("What does clever mean?", "Clever means smart in a useful way, like noticing clues and thinking of a good plan."))
    if "trail" in tags:
        out.append(("What is a trail?", "A trail is a path or line of signs that can lead you from one place to another."))
    if "light" in tags:
        out.append(("Why can a lantern help at night?", "A lantern gives safe light, so people can see without stumbling in the dark."))
    if "animal" in tags:
        out.append(("Why might an animal borrow something?", "An animal might borrow something to carry, line, or protect a nest, den, or path."))
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
clever_plan(P) :- plan(P), cleverness(P, C), C >= 2.
valid(S, T, P) :- setting(S), thing(T), plan(P), clever_plan(P).
outcome(happy) :- thing_returned.
twist :- thing_missing, thing_returned.
flashback :- remembered_kindness.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in LOST_THINGS:
        lines.append(asp.fact("thing", tid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("cleverness", pid, p.cleverness))
    lines.append(asp.fact("thing_returned"))
    lines.append(asp.fact("thing_missing"))
    lines.append(asp.fact("remembered_kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, lost_thing=None, creature=None, plan=None, name=None, helper=None, elder=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_reasonableness(setting: Setting, thing: LostThing, plan: Plan) -> str:
    return f"(No story: the chosen setting and plan do not support a strong folk-tale problem for {thing.label_word}.)"


def build_story_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.lost_thing is None or c[1] == args.lost_thing)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, lost_thing, plan = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    elder_gender = rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRLS if gender == "girl" else BOYS)
    helper_name = args.helper or rng.choice(GIRLS if helper_gender == "girl" else BOYS)
    elder_name = args.elder or rng.choice(GIRLS if elder_gender == "girl" else BOYS)
    return StoryParams(setting=setting, child_name=child_name, child_gender=gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       elder_name=elder_name, elder_gender=elder_gender,
                       lost_thing=lost_thing, creature=args.creature or rng.choice(sorted(CREATURES)),
                       plan=plan)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return build_story_choices(args, rng)


CURATED = [
    StoryParams(setting="village", child_name="Mira", child_gender="girl", helper_name="Pavel", helper_gender="boy", elder_name="Elin", elder_gender="girl", lost_thing="lantern", creature="fox", plan="lantern_call"),
    StoryParams(setting="harbor", child_name="Arin", child_gender="boy", helper_name="Sara", helper_gender="girl", elder_name="Bram", elder_gender="boy", lost_thing="key", creature="crow", plan="crumb_trail"),
    StoryParams(setting="hill", child_name="Tessa", child_gender="girl", helper_name="Jonas", helper_gender="boy", elder_name="Nina", elder_gender="girl", lost_thing="bell", creature="otter", plan="listen_first"),
]


def generate_from_params(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, thing, plan) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.lost_thing} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
