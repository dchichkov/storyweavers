#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/breaker_dialogue_kindness_curiosity_animal_story.py
====================================================================================

A small standalone storyworld for an animal-story premise about curiosity,
kindness, and dialogue around a little "breaker" that changes what the animals
can do.

Premise:
- A curious animal finds a breaker in the river path that has stopped a toy boat
  / blocked a little trail.
- Another animal worries, and they talk about it.
- Kindness turns the moment gentle: they help one another, fix the blocker, and
  end with a calmer, brighter outing.

This world is intentionally small and concrete. It uses typed entities with
physical meters and emotional memes, a forward-chained causal engine, a Python
reasonableness gate, and an inline ASP twin.
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
KINDNESS_MIN = 2
CURIOSITY_MIN = 2
BREAKER_BLOCK_MIN = 1.0
BREAK_THROUGH = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    detail: str
    water: str
    sounds: str
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
class Animal:
    id: str
    type: str
    label: str
    role: str
    dialogue_line: str
    curiosity_line: str
    kindness_line: str
    ending_line: str
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
class Breaker:
    id: str
    label: str
    phrase: str
    kind: str
    blocks: str
    fix_action: str
    fix_result: str
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
    use: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_open: bool = False
        self.dialogue: list[str] = []

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.path_open = self.path_open
        clone.dialogue = list(self.dialogue)
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


def _r_dialogue(world: World) -> list[str]:
    out: list[str] = []
    for animal in world.characters():
        if animal.memes["speech"] < THRESHOLD:
            continue
        sig = ("dialogue", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(animal.dialogue_line)
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for animal in world.characters():
        if animal.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(animal.kindness_line)
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for animal in world.characters():
        if animal.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("curiosity", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(animal.curiosity_line)
    return out


def _r_open_path(world: World) -> list[str]:
    if world.path_open:
        return []
    if world.get("breaker").meters["blocked"] < BREAKER_BLOCK_MIN:
        return []
    if world.get("helper").meters["used"] < BREAK_THROUGH:
        return []
    sig = ("open_path",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.path_open = True
    return ["__open__"]


CAUSAL_RULES = [
    Rule("dialogue", "social", _r_dialogue),
    Rule("curiosity", "social", _r_curiosity),
    Rule("kindness", "social", _r_kindness),
    Rule("open_path", "physical", _r_open_path),
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


def breaker_at_risk(breaker: Breaker) -> bool:
    return breaker.kind in {"blocker", "snag"}


def helper_matches(breaker: Breaker, helper: Helper) -> bool:
    return breaker.fix_action == helper.use


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid, a in ANIMALS.items():
            for bid, b in BREAKERS.items():
                for hid, h in HELPERS.items():
                    if breaker_at_risk(b) and helper_matches(b, h):
                        combos.append((sid, aid, bid))
    return combos


def path_strength(breaker: Breaker, helper: Helper) -> int:
    return 2 if helper_matches(breaker, helper) else 0


def can_fix(breaker: Breaker, helper: Helper) -> bool:
    return path_strength(breaker, helper) >= 2


def predict_path(world: World, breaker_id: str, helper_id: str) -> dict:
    sim = world.copy()
    sim.get(breaker_id).meters["blocked"] += 1
    sim.get(helper_id).meters["used"] += 1
    propagate(sim, narrate=False)
    return {"opened": sim.path_open}


@dataclass
class StoryParams:
    setting: str
    animal1: str
    animal2: str
    breaker: str
    helper: str
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
    "pond": Setting(
        id="pond",
        place="by the pond",
        detail="A little wooden bridge crossed the water, and reeds whispered at the edge.",
        water="pond water",
        sounds="soft splashes",
    ),
    "meadow": Setting(
        id="meadow",
        place="in the meadow",
        detail="A narrow trail curved through tall grass and yellow flowers.",
        water="morning dew",
        sounds="small rustles",
    ),
    "stream": Setting(
        id="stream",
        place="beside the stream",
        detail="A stone path ran along the bright stream, with tadpoles flicking below.",
        water="stream water",
        sounds="gentle ripples",
    ),
}

ANIMALS = {
    "rabbit": Animal(
        id="Pip",
        type="rabbit",
        label="Pip",
        role="curious one",
        dialogue_line='"What is that little breaker doing here?" Pip asked.',
        curiosity_line="Pip leaned closer and sniffed the air, wondering why the path had stopped.",
        kindness_line="Pip waited and made room so the other animal could look too.",
        ending_line="Pip hopped ahead with a happy little bounce.",
        tags={"animal"},
    ),
    "fox": Animal(
        id="Fenn",
        type="fox",
        label="Fenn",
        role="careful one",
        dialogue_line='"Maybe we should call it a funny stone," Fenn said softly.',
        curiosity_line="Fenn peered around the side, curious but careful.",
        kindness_line="Fenn smiled and helped nudge the breaker aside with a twig.",
        ending_line="Fenn trotted along with bright eyes.",
        tags={"animal"},
    ),
    "duck": Animal(
        id="Dot",
        type="duck",
        label="Dot",
        role="gentle one",
        dialogue_line='"I can hear the path complaining," Dot quacked.',
        curiosity_line="Dot tilted her head, curious about the blocked bend.",
        kindness_line="Dot shared the twig and held it steady with a careful bill.",
        ending_line="Dot waddled happily behind the others.",
        tags={"animal"},
    ),
}

BREAKERS = {
    "branch_breaker": Breaker(
        id="branch_breaker",
        label="branch breaker",
        phrase="a branch breaker across the path",
        kind="blocker",
        blocks="the little trail",
        fix_action="nudge",
        fix_result="the trail opens",
        tags={"breaker", "blocker"},
    ),
    "rock_breaker": Breaker(
        id="rock_breaker",
        label="rock breaker",
        phrase="a rock breaker that has jammed the stones together",
        kind="blocker",
        blocks="the bridge corner",
        fix_action="lift",
        fix_result="the bridge corner clears",
        tags={"breaker", "blocker"},
    ),
    "reed_breaker": Breaker(
        id="reed_breaker",
        label="reed breaker",
        phrase="a reed breaker tangled in the path",
        kind="snag",
        blocks="the narrow bend",
        fix_action="untangle",
        fix_result="the bend clears",
        tags={"breaker", "snag"},
    ),
}

HELPERS = {
    "twig": Helper(
        id="twig",
        label="twig",
        phrase="a thin twig",
        use="nudge",
        tags={"helper"},
    ),
    "stick": Helper(
        id="stick",
        label="stick",
        phrase="a smooth stick",
        use="lift",
        tags={"helper"},
    ),
    "leaf": Helper(
        id="leaf",
        label="leaf",
        phrase="a wide leaf",
        use="untangle",
        tags={"helper"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Poppy", "Wren"]
BOY_NAMES = ["Otis", "Finn", "Bram", "Toby", "Milo"]
TRAITS = ["gentle", "curious", "kind", "careful"]


def _animal_name(rng: random.Random, species: str) -> str:
    if species in {"duck"}:
        return "Dot"
    if species in {"fox"}:
        return "Fenn"
    if species in {"rabbit"}:
        return "Pip"
    return rng.choice(GIRL_NAMES + BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with dialogue, kindness, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--breaker", choices=BREAKERS)
    ap.add_argument("--helper", choices=HELPERS)
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


def explain_rejection(breaker: Breaker, helper: Helper) -> str:
    return (
        f"(No story: {breaker.label} needs a helper that can {breaker.fix_action}, "
        f"but {helper.label} is for {helper.use}. Pick a matching helper.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.breaker and args.helper:
        if not can_fix(BREAKERS[args.breaker], HELPERS[args.helper]):
            raise StoryError(explain_rejection(BREAKERS[args.breaker], HELPERS[args.helper]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.animal1 is None or c[1] == args.animal1)
              and (args.animal2 is None or c[1] == args.animal2 or True)
              and (args.breaker is None or c[2] == args.breaker)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal1, breaker = rng.choice(sorted(combos))
    animal2 = args.animal2 or rng.choice([k for k in ANIMALS if k != animal1])
    helper = args.helper or next(h for h, obj in HELPERS.items() if can_fix(BREAKERS[breaker], obj))
    return StoryParams(setting=setting, animal1=animal1, animal2=animal2, breaker=breaker, helper=helper)


def tell(setting: Setting, a1: Animal, a2: Animal, breaker: Breaker, helper: Helper) -> World:
    world = World()
    narrator = world.add(Entity(id=a1.id, kind="character", type=a1.type, role="curious", attrs={"species": a1.type}))
    partner = world.add(Entity(id=a2.id, kind="character", type=a2.type, role="kind", attrs={"species": a2.type}))
    block = world.add(Entity(id="breaker", type="thing", label=breaker.label, attrs={"phrase": breaker.phrase}))
    assist = world.add(Entity(id="helper", type="thing", label=helper.label, attrs={"use": helper.use}))
    world.facts["setting"] = setting
    world.facts["animals"] = (a1, a2)
    world.facts["breaker_cfg"] = breaker
    world.facts["helper_cfg"] = helper
    world.facts["breaker"] = block
    world.facts["helper"] = assist

    narrator.memes["curiosity"] = 2
    partner.memes["kindness"] = 2
    world.say(f"One bright day {a1.id} and {a2.id} wandered {setting.place}. {setting.detail}")
    world.say(f"They paused when they found {breaker.phrase}.")
    world.say(f'"{breaker.phrase.capitalize()}?" {a1.id} asked. "{a2.id}, do you know why it is here?"')
    world.say(f'"Not yet," {a2.id} said. "Let us look carefully and speak gently."')

    world.para()
    narrator.meters["blocked"] = 1
    partner.memes["kindness"] += 1
    narrator.memes["speech"] += 1
    partner.memes["speech"] += 1
    world.say(f'{a1.id} leaned in, full of curiosity. {a1.curiosity_line}')
    world.say(f'{a2.id} answered kindly. {a2.kindness_line}')
    world.say(f'Together they talked about the little {breaker.label} and what it was blocking.')

    world.para()
    predict_path(world, "breaker", "helper")
    block.meters["blocked"] += 1
    assist.meters["used"] += 1
    propagate(world, narrate=True)
    world.say(f'{a2.id} found {helper.phrase} and used it with care.')
    world.say(f'The {breaker.label} shifted, and {breaker.fix_result}.')
    world.say(f'"We did it together," {a1.id} said. "{a2.id}, thank you for helping."')
    world.say(f'"You were brave to ask," {a2.id} said. "{a1.id}, your curiosity helped us solve it."')
    world.say(f'Hand in hand, they went on along the path, and the water beside them shone again.')

    world.facts.update(
        setting=setting,
        animal1=a1,
        animal2=a2,
        breaker_cfg=breaker,
        helper_cfg=helper,
        outcome="opened",
        opened=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.animal1 not in ANIMALS or params.animal2 not in ANIMALS or params.breaker not in BREAKERS or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal1], ANIMALS[params.animal2], BREAKERS[params.breaker], HELPERS[params.helper])
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
    a1, a2 = f["animal1"], f["animal2"]
    breaker = f["breaker_cfg"]
    return [
        f'Write an animal story for a young child that includes the word "breaker" and has dialogue, kindness, and curiosity.',
        f"Tell a gentle story where {a1.id} and {a2.id} find {breaker.phrase}, talk about it, and solve the problem kindly.",
        f"Write a small animal adventure that begins with curiosity about a breaker and ends with a helpful fix.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a1, a2 = f["animal1"], f["animal2"]
    breaker = f["breaker_cfg"]
    helper = f["helper_cfg"]
    return [
        ("Who are the story friends?",
         f"The story is about {a1.id} and {a2.id}, two animals who met on a little walk and stayed gentle with each other."),
        ("What did they find on the path?",
         f"They found {breaker.phrase}, which was blocking the way. That is why they had to stop and think before they could continue."),
        ("How did they solve the problem?",
         f"{a2.id} used {helper.phrase} carefully, and that matched the kind of fix the breaker needed. Their teamwork made the path open again."),
        ("How did curiosity help?",
         f"{a1.id} was curious and asked about the breaker instead of rushing past it. That question helped them notice the problem and solve it safely."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to look, ask, and learn about something new."),
        ("What is kindness?",
         "Kindness means helping, sharing, and being gentle with someone else."),
        ("Why is dialogue useful?",
         "Dialogue is useful because talking helps friends understand each other and decide what to do next."),
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
    lines.append(f"  path_open={world.path_open}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="pond", animal1="rabbit", animal2="fox", breaker="branch_breaker", helper="twig"),
    StoryParams(setting="stream", animal1="duck", animal2="rabbit", breaker="reed_breaker", helper="leaf"),
    StoryParams(setting="meadow", animal1="fox", animal2="duck", breaker="rock_breaker", helper="stick"),
]


ASP_RULES = r"""
valid(S,A,B) :- setting(S), animal(A), breaker(B), helper(H), needs(B, U), uses(H, U).
opened :- blocked(B), helper_used(H), match(B,H).
dialogue_done :- speaker(A).
kindness_done :- kind(B).
curiosity_done :- curious(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for bid, b in BREAKERS.items():
        lines.append(asp.fact("breaker", bid))
        lines.append(asp.fact("needs", bid, b.fix_action))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("uses", hid, h.use))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke generate succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.animal1 is None or c[1] == args.animal1)
              and (args.breaker is None or c[2] == args.breaker)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal1, breaker = rng.choice(sorted(combos))
    animal2 = args.animal2 or rng.choice([k for k in ANIMALS if k != animal1])
    helper = args.helper or next(h for h, obj in HELPERS.items() if can_fix(BREAKERS[breaker], obj))
    return StoryParams(setting=setting, animal1=animal1, animal2=animal2, breaker=breaker, helper=helper)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = build_params_from_args(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
