#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/multitude_cheese_seep_suspense_curiosity_adventure.py
======================================================================================

A standalone story world for a tiny adventure about curiosity, suspense, and a
small rescue around a cheese-filled place. The seed words are woven into the
simulated world: a *multitude* of curious critters gather, a wheel of *cheese*
starts to *seep*, and the characters must choose a careful adventure-minded fix.

The story engine is built from:
- typed entities with physical meters and emotional memes,
- a small forward-chaining causal model,
- a reasonableness gate,
- an inline ASP twin,
- three grounded QA sets.

The domain is child-facing, concrete, and tuned for a suspenseful adventure tone:
the kids discover a strange drip in an underground pantry, follow the clues, and
help before the cheese can spoil further.
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
class Place:
    id: str
    name: str
    dark: bool = False
    damp: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    phrase: str
    seep_source: str
    spread: int = 1
    leaks: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Treasure:
    id: str
    label: str
    phrase: str
    plural: bool = False
    delicate: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_seep(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["wet"] < THRESHOLD:
            continue
        sig = ("seep", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "cellar" in world.entities:
            world.get("cellar").meters["damp"] += 1
        out.append("__seep__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for kid in list(world.entities.values()):
        if kid.role not in {"explorer", "observer"}:
            continue
        if kid.memes["curiosity"] < THRESHOLD:
            continue
        if world.get("cheese").meters["wet"] < THRESHOLD:
            continue
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["suspense"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("seep", "physical", _r_seep), Rule("worry", "social", _r_worry)]


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


def hazard_at_risk(h: Hazard, t: Treasure) -> bool:
    return h.leaks and t.delicate


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def is_contained(tool: Tool, hazard: Hazard, delay: int) -> bool:
    return tool.power >= hazard.spread + delay


@dataclass
@dataclass
class StoryParams:
    place: str
    hazard: str
    treasure: str
    tool: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


PLACES = {
    "cellar": Place("cellar", "the old cellar", dark=True, damp=True),
    "pantry": Place("pantry", "the back pantry", dark=True, damp=True),
    "tunnel": Place("tunnel", "the stone tunnel", dark=True, damp=True),
}

HAZARDS = {
    "seep": Hazard("seep", "a seep", "a slow seep from the ceiling", "the cheese wheel", spread=2, tags={"seep", "cheese"}),
    "drip": Hazard("drip", "a drip", "a drip from the crate roof", "the cheese wheel", spread=1, tags={"cheese"}),
    "leak": Hazard("leak", "a leak", "a leak near the shelf", "the cheese wheel", spread=2, tags={"cheese"}),
}

TREASURES = {
    "cheese": Treasure("cheese", "the cheese", "a tall round wheel of cheese", tags={"cheese"}),
    "stack": Treasure("stack", "the cheese stacks", "a stack of small cheese rounds", plural=True, tags={"cheese"}),
    "box": Treasure("box", "the snack box", "a snack box with crackers", delicate=True, tags={"crackers"}),
}

TOOLS = {
    "cloth": Tool("cloth", "cloth", "a clean cloth", 2, 3, "pressed a clean cloth around the damp edge until the wet spot stopped growing", "pressed a cloth on it, but the dampness kept spreading", "pressed a clean cloth around the damp edge", tags={"cloth"}),
    "bucket": Tool("bucket", "bucket", "a little bucket", 3, 3, "caught the drips and carried them away", "caught some drips, but not enough to matter", "caught the drips before they spread", tags={"bucket"}),
    "seal": Tool("seal", "sealant", "a tin of sealant", 4, 2, "sealed the crack in the stone wall so no more wet could sneak through", "tried to seal the crack, but the leak was already too wide", "sealed the crack in the wall", tags={"seal"}),
    "spoon": Tool("spoon", "spoon", "a wooden spoon", 1, 1, "stirred at the wet spot in a silly way", "stirred at it, but nothing changed", "stirred at the wet spot", tags={"spoon"}),
}

GIRL_NAMES = ["Maya", "Lila", "Nina", "Ada", "Zoe", "Tess"]
BOY_NAMES = ["Noah", "Eli", "Ben", "Theo", "Finn", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for h in HAZARDS:
            for t in TREASURES:
                if hazard_at_risk(HAZARDS[h], TREASURES[t]):
                    out.append((p, h, t))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful adventure storyworld about cheese, seep, and curiosity.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError("(No story: that tool is too silly for the suspenseful fix.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, treasure = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(k for k, v in TOOLS.items() if v.sense >= SENSE_MIN))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(place, hazard, treasure, tool, hero, hero_gender, friend, friend_gender, parent, delay)


def predict(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    sim.get(hazard_id).meters["wet"] += 1
    propagate(sim, narrate=False)
    return {"wet": sim.get(hazard_id).meters["wet"], "damp": sim.get("cellar").meters["damp"]}


def setup_story(world: World, p: StoryParams) -> None:
    hero = world.add(Entity(p.hero, kind="character", type=p.hero_gender, role="explorer"))
    friend = world.add(Entity(p.friend, kind="character", type=p.friend_gender, role="observer"))
    parent = world.add(Entity("Parent", kind="character", type=p.parent, role="parent", label="the parent"))
    world.add(Entity("cellar", type="room", label=PLACES[p.place].name))
    hazard = world.add(Entity("hazard", type="thing", label=HAZARDS[p.hazard].label))
    treasure = world.add(Entity("cheese", type="thing", label=TREASURES[p.treasure].label))
    tool = world.add(Entity("tool", type="tool", label=TOOLS[p.tool].label))
    hero.memes["curiosity"] = 2
    friend.memes["curiosity"] = 1
    world.facts.update(hero=hero, friend=friend, parent=parent, hazard=hazard, treasure=treasure, tool=tool, params=p)


def tell(p: StoryParams) -> World:
    world = World()
    setup_story(world, p)
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    hazard = world.facts["hazard"]
    treasure = world.facts["treasure"]
    tool = world.facts["tool"]

    world.say(f"{hero.id} and {friend.id} were on an adventure in {PLACES[p.place].name}.")
    world.say(f"They had come to see {TREASURES[p.treasure].phrase}, because a whole multitude of tiny crumbs and boots had passed through that place before them.")
    world.say(f"Then {hero.id} noticed something odd: {HAZARDS[p.hazard].phrase}.")
    world.para()
    world.say(f"{friend.id} shivered. \"It feels a little spooky down here,\" {friend.pronoun()} whispered.")
    world.say(f"{hero.id} leaned closer anyway, curious as a lantern in the dark.")
    world.say(f"\"We should be careful,\" said {friend.id}, but the wet spot kept growing.")
    hazard.meters["wet"] += 1
    treasure.meters["wet"] += 1
    propagate(world, narrate=False)
    world.say(f"The seep touched {treasure.label}, and now the cheese looked damp and lonely.")
    world.say(f"{hero.id} could hear water ticking somewhere above the stones.")
    world.para()
    tool_def = TOOLS[p.tool]
    if is_contained(tool_def, HAZARDS[p.hazard], p.delay):
        world.say(f"At last, {parent.label_word} arrived with {tool_def.phrase}.")
        world.say(f"{parent.pronoun().capitalize()} {tool_def.text}.")
        treasure.meters["wet"] = 0
        hazard.meters["wet"] = 0
        world.say(f"The room grew still again, and the cheese stopped seeping at once.")
        world.say(f"{hero.id} and {friend.id} smiled at the quiet, solved mystery.")
        world.say(f"Later, the multitude of little visitors could come back without worry, and the cheese sat safe and round in the pantry.")
        outcome = "contained"
    else:
        world.say(f"At last, {parent.label_word} arrived, but the {tool_def.label} was too small for the problem.")
        world.say(f"{parent.pronoun().capitalize()} {tool_def.fail}.")
        hazard.meters["wet"] += 1
        treasure.meters["wet"] += 1
        world.say(f"The seep kept creeping, and the cheese had to be moved before it spoiled.")
        world.say(f"{hero.id} and {friend.id} carried it out with careful hands, and the adventure ended with a rescue instead of a feast.")
        outcome = "burned"
    world.facts["outcome"] = outcome
    world.facts["delay"] = p.delay
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write an adventure story for a young child that includes the words multitude, cheese, and seep.",
        f"Tell a suspenseful curiosity-filled story about {p.hero} and {p.friend} discovering why the cheese in {PLACES[p.place].name} started to seep.",
        f"Write a child-friendly adventure where curiosity leads to a small mystery and a careful grown-up fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    outcome = world.facts["outcome"]
    qas = [
        QAItem(question="Who is the story about?", answer=f"It is about {p.hero} and {p.friend}, two children on a small adventure in {PLACES[p.place].name}. They follow curiosity into a damp mystery and learn how to keep the cheese safe."),
        QAItem(question="What was odd in the room?", answer=f"The odd thing was {HAZARDS[p.hazard].phrase}. It made the cheese start to seep and turned the adventure into a suspenseful search for a fix."),
    ]
    if outcome == "contained":
        qas.append(QAItem(question="How was the problem solved?", answer=f"{p.parent.capitalize()} brought {TOOLS[p.tool].phrase} and used it to stop the wet from spreading. That careful fix let the cheese stay safe and ended the suspense." ))
        qas.append(QAItem(question="How did the ending feel?", answer=f"The ending felt brave and calm. The children got to keep their curiosity, and the pantry was safe again."))
    else:
        qas.append(QAItem(question="What happened when the fix was too small?", answer=f"The tool was not strong enough, so the seep kept going. The cheese had to be moved to safety, and the adventure ended with a rescue instead of a snack."))
        qas.append(QAItem(question="What did the children learn?", answer="They learned that curiosity is good, but some problems need a grown-up with the right tool. Careful choices matter when something in the dark starts to seep."))
    return qas


KNOWLEDGE = {
    "cheese": [("What is cheese?", "Cheese is a food made from milk. It can be soft or hard, and it needs to be kept clean and dry.")],
    "seep": [("What does seep mean?", "To seep means to slowly move through a small crack or wet a place little by little.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask questions, and learn more.")],
    "suspense": [("What is suspense?", "Suspense is the feeling of wondering what will happen next, often when something is uncertain or hidden.")],
    "adventure": [("What is an adventure?", "An adventure is an exciting trip or event where people explore, discover, or solve a problem.")],
    "multitude": [("What does multitude mean?", "A multitude means a very large number of things or people.")],
}

KNOWLEDGE_ORDER = ["multitude", "curiosity", "suspense", "adventure", "cheese", "seep"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"multitude", "curiosity", "suspense", "adventure", "cheese", "seep"}
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cellar", "seep", "cheese", "cloth", "Maya", "girl", "Noah", "boy", "mother", 0),
    StoryParams("pantry", "drip", "stack", "bucket", "Eli", "boy", "Lila", "girl", "father", 0),
    StoryParams("tunnel", "leak", "cheese", "seal", "Ada", "girl", "Finn", "boy", "mother", 1),
]


def generate(params: StoryParams) -> StorySample:
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


ASP_RULES = r"""
hazard(F, T) :- hazard(F), treasure(T), leaks(F), delicate(T).
sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
contained(T, H, D) :- tool(T), hazard(H), power(T, P), spread(H, S), delay(D), P >= S + D.
valid(P, H, T) :- place(P), hazard(H), treasure(T), hazard(H, T).
outcome(contained) :- chosen_tool(T), chosen_hazard(H), delay(D), contained(T, H, D).
outcome(failed) :- chosen_tool(T), chosen_hazard(H), delay(D), not contained(T, H, D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("leaks", hid))
        lines.append(asp.fact("spread", hid, h.spread))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("delicate", tid))
    for toid, t in TOOLS.items():
        lines.append(asp.fact("tool", toid))
        lines.append(asp.fact("sense", toid, t.sense))
        lines.append(asp.fact("power", toid, t.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    if set(asp_sensible()) == {t for t, v in TOOLS.items() if v.sense >= SENSE_MIN}:
        print("OK: sensible tools match.")
    else:
        print("MISMATCH in sensible tools.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def explain_rejection(h: Hazard, t: Treasure) -> str:
    if not hazard_at_risk(h, t):
        return "(No story: this hazard does not really threaten that treasure, so the suspense never gets started.)"
    return "(No story: this combination is not reasonable.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        for p, h, t in asp_valid_combos():
            print(f"  {p:8} {h:6} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero} & {p.friend}: {p.hazard} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
