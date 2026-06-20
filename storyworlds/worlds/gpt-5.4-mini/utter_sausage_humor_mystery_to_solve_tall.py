#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/utter_sausage_humor_mystery_to_solve_tall.py
=============================================================================

A standalone story world for a tall-tale mystery with humor:
a hungry kid, a missing sausage, a bewildering trail of clues, and a ridiculous
but sensible resolution that proves what changed.

The world keeps state with typed entities, physical meters, and emotional memes.
It also includes a Python reasonableness gate, an inline ASP twin, and the
standard Storyweavers CLI.

Theme words required by the seed:
- utter
- sausage

Style goals:
- tall tale energy
- humorous tone
- mystery to solve
- complete beginning / turn / ending
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    tall: str
    details: str
    clue_style: str
    needs_tally: str

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
class Clue:
    id: str
    label: str
    trail: str
    hint: str
    weirdness: str

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
class Sausage:
    id: str
    label: str
    phrase: str
    aroma: str
    rolling: bool = False

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
    sense: int
    power: int
    action: str
    fail: str
    ending: str

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


def _r_grumble(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_spun") and not world.facts.get("mystery_solved"):
        for e in list(world.entities.values()):
            if e.role == "hero":
                if e.memes["worry"] < THRESHOLD:
                    e.memes["worry"] += 1
                    out.append("__worry__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("odd_scene") and not world.facts.get("mystery_solved"):
        clown = world.facts.get("sidekick")
        if clown and clown.memes["funny"] < THRESHOLD:
            clown.memes["funny"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("grumble", "social", _r_grumble), Rule("laugh", "social", _r_laugh)]


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


def silly_noise() -> str:
    return random.choice(["twang", "boing", "whizzle", "honk", "plunk"])


def hazard_at_risk(sa: Sausage, clue: Clue) -> bool:
    return sa.rolling and bool(clue.trail)


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def is_solved(fix: Fix, clue: Clue, delay: int) -> bool:
    return fix.power >= (1 + delay if clue.weirdness else delay + 1)


def predict_mystery(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _do_spill(sim, sim.get(clue_id), narrate=False)
    return {
        "odd": sim.facts.get("odd_scene", False),
        "worry": sum(e.memes["worry"] for e in sim.entities.values()),
    }


def _do_spill(world: World, clue_ent: Entity, narrate: bool = True) -> None:
    clue_ent.meters["noticed"] += 1
    world.facts["mystery_spun"] = True
    world.facts["odd_scene"] = True
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, sidekick: Entity, setting: Setting, sa: Sausage) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"One bright morning, {hero.id} and {sidekick.id} went down to {setting.place}, "
        f"a place so tall it made the fence look like a picket pencil."
    )
    world.say(
        f"The {setting.tall} was all dressed up with {setting.details}, and the air "
        f"had the {sa.aroma} smell of {sa.label}."
    )


def mystery(world: World, hero: Entity, sidekick: Entity, sa: Sausage, setting: Setting) -> None:
    world.say(
        f"But then the prize went missing: the great {sa.label} was gone, and only "
        f"a crumbly clue remained on the porch."
    )
    hero.memes["curiosity"] += 1
    world.say(
        f'{hero.id} put on a serious face and said, "This is an utter mystery." '
        f'That made {sidekick.id} snort so hard it nearly bounced off the step.'
    )
    world.say(
        f"{sidekick.id} peered at the ground and saw a {setting.clue_style} clue "
        f"leading toward the hayloft."
    )


def clue_scene(world: World, hero: Entity, sidekick: Entity, clue: Clue) -> None:
    world.facts["mystery_spun"] = True
    world.facts["odd_scene"] = True
    world.say(
        f"The trail was no ordinary trail. It was {clue.trail}, which looked as if "
        f"a goose and a sock had argued in a thunderstorm."
    )
    world.say(
        f'{sidekick.id} pointed and said, "{clue.hint}" '
        f'That was funny enough to make even the barn cat blink.'
    )


def warn(world: World, hero: Entity, sidekick: Entity, clue: Clue, sa: Sausage, delay: int) -> None:
    pred = predict_mystery(world, "clue")
    world.facts["predicted_odd"] = pred["odd"]
    world.facts["predicted_worry"] = pred["worry"]
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} scratched {hero.pronoun('possessive')} chin. "
        f'"If we follow that trail too long, we may find a sausage-snatcher, or a '
        f'horse wearing a hat."'
    )
    if delay > 0:
        world.say(
            f"{sidekick.id} laughed, but the worry still grew like a hill in a rainstorm."
        )


def search(world: World, hero: Entity, sidekick: Entity, clue: Clue) -> None:
    hero.meters["searching"] += 1
    sidekick.meters["searching"] += 1
    world.say(
        f"They followed the clue past the broom shed, past three sleepy chickens, and "
        f"past one very offended wheelbarrow."
    )
    world.say(
        f"At the end of the trail sat a basket, wobbling like a cup on a wagon wheel."
    )


def reveal(world: World, hero: Entity, sidekick: Entity, sa: Sausage) -> None:
    world.facts["mystery_solved"] = True
    hero.memes["surprise"] += 1
    sidekick.memes["surprise"] += 1
    world.say(
        f'Inside the basket was the missing {sa.label} -- not stolen at all, but tucked '
        f"inside a pie tin so it wouldn't roll away."
    )
    world.say(
        f"And there beside it was the culprit: a squirrel wearing a jam jar like a crown."
    )


def fix_story(world: World, hero: Entity, sidekick: Entity, fix: Fix, sa: Sausage) -> None:
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    world.say(
        f"At last, {hero.id} did not chase the squirrel with a shovel or a trumpet. "
        f"Instead, {hero.pronoun()} {fix.action}."
    )
    world.say(
        f"{fix.ending} The squirrel scampered off, the basket stayed put, and the "
        f"{sa.label} was safe at last."
    )


def ending(world: World, hero: Entity, sidekick: Entity, sa: Sausage) -> None:
    world.say(
        f"By sunset, {hero.id} and {sidekick.id} sat on the porch, laughing so hard "
        f"their boots shivered."
    )
    world.say(
        f'The mystery was solved, the {sa.label} was returned, and {hero.id} declared, '
        f'"That was the most utter sausage business I ever heard of."'
    )


def tell(setting: Setting, sa: Sausage, clue: Clue, fix: Fix,
         hero_name: str = "Mabel", sidekick_name: str = "Pip") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy", role="sidekick"))
    barn = world.add(Entity(id="barn", type="place", label=setting.place))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label))
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick
    world.facts["setting"] = setting
    world.facts["sausage"] = sa
    world.facts["clue_cfg"] = clue
    world.facts["fix"] = fix

    opening(world, hero, sidekick, setting, sa)
    world.para()
    mystery(world, hero, sidekick, sa, setting)
    clue_scene(world, hero, sidekick, clue)
    warn(world, hero, sidekick, clue, sa, delay=0)
    search(world, hero, sidekick, clue)
    reveal(world, hero, sidekick, sa)
    world.para()
    fix_story(world, hero, sidekick, fix, sa)
    ending(world, hero, sidekick, sa)
    world.facts["barn"] = barn
    return world


@dataclass
@dataclass
class StoryParams:
    setting: str
    sausage: str
    clue: str
    fix: str
    hero_name: str
    sidekick_name: str
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


SETTINGS = {
    "fair": Setting(
        "fairgrounds", "county fair", "tall as a wagon mast",
        "paper lanterns, striped flags, and a brass band that kept sneezing notes",
        "zigzag", "needed a sharp eye"
    ),
    "farm": Setting(
        "farmyard", "barnyard", "taller than a feed sack stack",
        "twine, sunflower hats, and a rooster with a reputation for speeches",
        "muddy", "needed a clever nose"
    ),
    "carnival": Setting(
        "carnival", "traveling carnival", "so tall it could tickle a cloud",
        "bunting, pop bottles, and a ferris wheel spinning like a giant dandelion",
        "sparkly", "needed a steady foot"
    ),
}

SAUSAGES = {
    "link": Sausage("link", "sausage link", "the old sausage link", "smelled peppery and brave", rolling=True),
    "big": Sausage("big", "sausage", "the biggest sausage in town", "smelled smoky and proud", rolling=False),
    "tiny": Sausage("tiny", "tiny sausage", "the tiny sausage", "smelled sweet and silly", rolling=True),
}

CLUES = {
    "crumb": Clue("crumb", "crumb trail", "a crumb trail", "follow me, follow me", "crumbly"),
    "hoof": Clue("hoof", "hoofprint trail", "a hoofprint trail", "not a goose, not a goose", "muddy"),
    "spoon": Clue("spoon", "spoon track", "a spoon track", "the spoon did it", "shiny"),
}

FIXES = {
    "ladle": Fix("ladle", 3, 3, "used a wooden spoon as a pointer and lifted the pie tin carefully",
                 "grabbed the wrong end and sent the basket wobbling",
                 "The spoon worked like a flagpole, and the basket stayed steady."),
    "whistle": Fix("whistle", 2, 2, "gave one sharp whistle and coaxed the squirrel down with a biscuit",
                  "blew so hard that the hens started a committee",
                  "The whistle called the squirrel out without a chase."),
    "hat": Fix("hat", 3, 4, "placed a straw hat under the basket and rolled it back by hand",
               "wore the hat too low and bumped the jam jar",
               "The hat made a soft ramp, and the sausage rolled home safely."),
}

GIRL_NAMES = ["Mabel", "Ruby", "Daisy", "June", "Ivy", "Nell", "Ada", "Rosie"]
BOY_NAMES = ["Pip", "Otis", "Beau", "Finn", "Walt", "Toby", "Clive", "Jeb"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, sa in SAUSAGES.items():
        for cid, clue in CLUES.items():
            if hazard_at_risk(sa, clue):
                for setid in SETTINGS:
                    combos.append((setid, sid, cid))
    return combos


def explain_rejection(sa: Sausage, clue: Clue) -> str:
    return (
        f"(No story: the {sa.label} would not make a strong enough mystery with {clue.label}. "
        f"Pick a rolling sausage and a clue trail that can actually lead somewhere.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    if fix.sense < SENSE_MIN:
        return f"(Refusing fix '{fid}': it is too silly even for a tall tale.)"
    return ""


@dataclass
class StoryParams:
    setting: str
    sausage: str
    clue: str
    fix: str
    hero_name: str
    sidekick_name: str
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
    "sausage": [("What is a sausage?",
                 "A sausage is a long, seasoned food made from meat or beans. People cook it and eat it warm.")],
    "utter": [("What does utter mean?",
               "Utter can mean complete or total. People use it to say something is very big, very true, or very surprising.")],
    "mystery": [("What is a mystery?",
                "A mystery is a puzzling thing you do not understand yet. You solve it by looking for clues.")],
    "clue": [("What is a clue?",
              "A clue is a hint that helps solve a mystery. Clues can be tracks, crumbs, sounds, or strange signs.")],
    "tall_tale": [("What is a tall tale?",
                   "A tall tale is a funny story that makes things sound extra big or extra wild on purpose.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale mystery for a child that includes the words "utter" and "{f["sausage"].label}".',
        f"Tell a funny farm mystery where {f['hero'].id} and {f['sidekick'].id} search for a missing {f['sausage'].label} and solve it with clues.",
        f'Write a humorous story about a mystery to solve at {f["setting"].tall} with a silly ending and a safe, clear solution.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick = f["hero"], f["sidekick"]
    sa, clue, fix = f["sausage"], f["clue_cfg"], f["fix"]
    return [
        ("Who are the story about?",
         f"The story is about {hero.id} and {sidekick.id}, who tried to solve a mystery together."),
        ("What was missing?",
         f"The missing thing was {sa.label}. That was the mystery they had to solve."),
        ("What clue did they follow?",
         f"They followed {clue.label}, which led them toward the hiding place and helped them solve the mystery."),
        ("How did they solve the problem?",
         f"They used a calm plan instead of chasing around. {hero.id} {fix.action}, and that kept the basket steady."),
        ("How did the story end?",
         f"It ended happily. The {sa.label} was returned, the squirrel ran off, and everyone laughed at the silly surprise."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"sausage", "utter", "mystery", "clue", "tall_tale"}
    out: list[QAItem] = []
    for key in tags:
        for q, a in KNOWLEDGE.get(key, []):
            out.append(QAItem(question=q, answer=a))
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
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S, C) :- sausage(S), clue(C), rolling(S), trail(C).
sensible(F) :- fix(F), sense(F, N), sense_min(M), N >= M.
valid(Setting, S, C) :- setting(Setting), sausage(S), clue(C), hazard(S, C).
solved(F) :- chosen_fix(F), power(F, P), clue_strength(V), P >= V.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, sa in SAUSAGES.items():
        lines.append(asp.fact("sausage", sid))
        if sa.rolling:
            lines.append(asp.fact("rolling", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("trail", cid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP valid combos match ({len(valid_combos())}).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    if set(asp_sensible()) == {fid for fid, f in FIXES.items() if f.sense >= SENSE_MIN}:
        print("OK: sensible fix set matches.")
    else:
        rc = 1
        print("MISMATCH: sensible fixes differ.")
    # Smoke test ordinary generation.
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.prompts
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale sausage mystery world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sausage", choices=SAUSAGES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if args.sausage and args.clue:
        sa = SAUSAGES[args.sausage]
        cl = CLUES[args.clue]
        if not hazard_at_risk(sa, cl):
            raise StoryError(explain_rejection(sa, cl))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sausage is None or c[1] == args.sausage)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sausage, clue = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(fid for fid, f in FIXES.items() if f.sense >= SENSE_MIN))
    hero = args.hero or rng.choice(GIRL_NAMES)
    sidekick = args.sidekick or rng.choice(BOY_NAMES)
    return StoryParams(setting, sausage, clue, fix, hero, sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SAUSAGES[params.sausage], CLUES[params.clue], FIXES[params.fix], params.hero_name, params.sidekick_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
    StoryParams("farm", "link", "crumb", "ladle", "Mabel", "Pip"),
    StoryParams("fair", "big", "spoon", "whistle", "Ruby", "Otis"),
    StoryParams("carnival", "tiny", "hoof", "hat", "June", "Beau"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}")
        print()
        for combo in asp_valid_combos():
            print(combo)
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
            header = f"### {p.hero_name} and {p.sidekick_name}: {p.sausage} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
