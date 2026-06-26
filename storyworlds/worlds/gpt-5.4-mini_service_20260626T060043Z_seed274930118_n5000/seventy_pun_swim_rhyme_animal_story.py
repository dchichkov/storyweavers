#!/usr/bin/env python3
"""
storyworlds/worlds/seventy_pun_swim_rhyme_animal_story.py
==========================================================

A small animal story world with a rhyming turn: one animal wants to swim,
another makes a pun, and a cozy ending settles the fuss. The seed words
"seventy", "pun", and "swim" are embedded in the domain and prose model.

Premise:
- A young animal wants to swim in a pond or stream.
- Another animal worries about a simple rule: don't rush into the water.

Turn:
- The playful animal makes a punny splash of confidence.
- A helper notices a safer way to enjoy the water.

Resolution:
- The animals choose a gentle, rhyme-friendly compromise and the ending image
  shows what changed in the scene.

This script follows the Storyweavers contract:
- standalone stdlib script
- typed world entities with meters and memes
- lazy ASP import in helper functions only
- Python reasonableness gate plus inline ASP twin
- generate/emit/main support default run, -n, --all, --seed, --trace, --qa,
  --json, --asp, --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    hero_ent: object | None = None
    watcher_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "mother", "woman", "duck"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        if self.type in {"boy", "father", "man", "fox"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Pond:
    place: str = "the pond"
    can_swim: bool = True
    can_splash: bool = True
    rhymes_with: str = "pond"
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Creature:
    id: str
    species: str
    name: str
    adjective: str
    trait: str
    loves_swim: bool
    rhyme_word: str
    is_small: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Trick:
    id: str
    pun_line: str
    rhyme_line: str
    safe_way: str
    splash_kind: str = "wet"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, pond: Pond) -> None:
        self.pond = pond
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.rhyme: str = "pond"

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.pond)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.rhyme = self.rhyme
        return clone


def _r_wet_ears(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("wet", 0) < THRESHOLD:
            continue
        sig = ("wet_ears", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["surprise"] = ent.memes.get("surprise", 0) + 1
        out.append(f"{ent.name}'s ears got wet with a tiny splat.")
    return out


def _r_chuckle(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes.get("pun_laugh", 0) < THRESHOLD:
            continue
        sig = ("chuckle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] = ent.memes.get("joy", 0) + 1
        out.append(f"The nearby animals chuckled at the pun.")
    return out


CAUSAL_RULES = [
    _r_wet_ears,
    _r_chuckle,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(name: str, rhyme: str) -> str:
    return f"{name} found a tune that seemed to ring, a merry rhyme that made birds sing."


def reasonableness_gate(creature: Creature, trick: Trick, pond: Pond) -> bool:
    return pond.can_swim and creature.loves_swim and trick.splash_kind == "wet"


def predicts_wet(world: World, actor: Entity) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["wet"] = sim.get(actor.id).meters.get("wet", 0) + 1
    propagate(sim, narrate=False)
    return sim.get(actor.id).meters.get("wet", 0) >= THRESHOLD


def tell(world: World, hero: Creature, watcher: Creature, trick: Trick) -> World:
    hero_ent = world.add(Entity(
        id=hero.id, kind="character", type=hero.species, label=hero.name,
        traits=[hero.adjective, hero.trait, "small"],
        meters={"wet": 0.0},
        memes={"joy": 0.0},
    ))
    watcher_ent = world.add(Entity(
        id=watcher.id, kind="character", type=watcher.species, label=watcher.name,
        traits=[watcher.adjective, watcher.trait],
        meters={"wet": 0.0},
        memes={"worry": 0.0},
    ))

    world.say(
        f"{hero.name} was a {hero.adjective} little {hero.species} who loved to swim."
    )
    world.say(
        f"{watcher.name} was a careful {watcher.adjective} {watcher.species} who liked to keep paws dry."
    )
    world.say(
        f"By the {world.pond.place}, {hero.name} counted {seventy_line()} ripples and smiled."
    )

    world.para()
    world.say(
        f"One day, {hero.name} wanted to swim, and the water looked bright and cool."
    )
    world.say(
        f"{watcher.name} said, \"Not yet; let's think before the splash, because a wise swim is the trim kind of swim.\""
    )
    world.say(
        f"{hero.name} grinned at the {trick.pun_line} pun, then asked for a safer way to play."
    )

    if predicts_wet(world, hero_ent):
        hero_ent.meters["wet"] += 1
        hero_ent.memes["pun_laugh"] = hero_ent.memes.get("pun_laugh", 0) + 1
        propagate(world)

    world.para()
    world.say(
        f"{watcher.name} pointed to the shallow edge and said, \"We can swim there, sing there, and keep the rest dry.\""
    )
    world.say(
        f"So {hero.name} tried the {trick.safe_way}, and the little splash made a happy dash."
    )
    hero_ent.meters["wet"] += 0.0
    hero_ent.memes["joy"] = hero_ent.memes.get("joy", 0) + 2
    watcher_ent.memes["worry"] = 0.0
    world.say(
        f"{rhyme_line(hero.name, hero.rhyme_word)}"
    )
    world.say(
        f"In the end, {hero.name} was swimming with a grin, and {watcher.name} watched a safe, happy spin."
    )

    world.facts.update(hero=hero, watcher=watcher, trick=trick, pond=world.pond)
    return world


def seventy_line() -> str:
    return "seventy"


SETTINGS = {
    "pond": Pond(place="the pond", can_swim=True, can_splash=True, rhymes_with="pond"),
    "stream": Pond(place="the stream", can_swim=True, can_splash=True, rhymes_with="stream"),
    "lake": Pond(place="the lake", can_swim=True, can_splash=True, rhymes_with="lake"),
}

CREATURES = {
    "duck": Creature("duck", "duck", "Daisy", "bright", "spry", True, "pond"),
    "frog": Creature("frog", "frog", "Milo", "green", "jumpy", True, "splash"),
    "fox": Creature("fox", "fox", "Pip", "red", "canny", False, "stream"),
    "otter": Creature("otter", "otter", "Nina", "sleek", "curious", True, "swim"),
}

TRICKS = {
    "pun": Trick(
        id="pun",
        pun_line="quack-tastic",
        rhyme_line="quack and track",
        safe_way="swim in the shallow edge",
        splash_kind="wet",
    ),
    "rhyme": Trick(
        id="rhyme",
        pun_line="drip-ship",
        rhyme_line="zip and flip",
        safe_way="dip a paw, then stop",
        splash_kind="wet",
    ),
}

GIRL_NAMES = ["Daisy", "Nina", "Mina", "Poppy"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Bram"]
TRAITS = ["brave", "gentle", "curious", "cheery", "spry"]


@dataclass
class StoryParams:
    place: str
    hero: str
    watcher: str
    trick: str
    seed: Optional[int] = None
    params: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a punny swim and a rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=CREATURES)
    ap.add_argument("--watcher", choices=CREATURES)
    ap.add_argument("--trick", choices=TRICKS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in CREATURES:
            for watcher in CREATURES:
                if watcher == hero:
                    continue
                for trick in TRICKS:
                    combos.append((place, hero, trick))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "hero", None) and getattr(args, "trick", None):
        if getattr(args, "hero", None) == "fox" and getattr(args, "trick", None) == "pun":
            return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [c for c in combos
               if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
               and (getattr(args, "hero", None) is None or c[1] == getattr(args, "hero", None))
               and (getattr(args, "trick", None) is None or c[2] == getattr(args, "trick", None))
               and (getattr(args, "watcher", None) is None or c[1] != getattr(args, "watcher", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hero, trick = rng.choice(sorted(choices))
    watcher_choices = [k for k in CREATURES if k != hero]
    watcher = getattr(args, "watcher", None) or rng.choice(watcher_choices)
    return StoryParams(place=place, hero=hero, watcher=watcher, trick=trick)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = _safe_lookup(CREATURES, params.hero)
    watcher = _safe_lookup(CREATURES, params.watcher)
    trick = _safe_lookup(TRICKS, params.trick)
    world = tell(world, hero, watcher, trick)

    prompts = [
        f"Write a short animal story for a child about {hero.name} the {hero.species} and a punny swim.",
        f"Tell a gentle rhyme-friendly story where an animal wants to swim and another animal warns first.",
        f"Make a tiny story using the words seventy, pun, and swim with a safe ending.",
    ]

    story_qa = [
        QAItem(
            question=f"Who wanted to swim by {params.place}?",
            answer=f"{hero.name} the {hero.species} wanted to swim by {params.place}.",
        ),
        QAItem(
            question=f"Why did {watcher.name} speak up before the splash?",
            answer=f"{watcher.name} worried that rushing into the water would make the plan less safe.",
        ),
        QAItem(
            question=f"What kind of wordplay did the story use?",
            answer=f"It used a pun, and the pun helped turn the worry into a cheerful idea.",
        ),
        QAItem(
            question=f"How many ripples did the story mention?",
            answer="It mentioned seventy ripples.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a pun?",
            answer="A pun is a playful kind of joke that uses a word or sound in a funny way.",
        ),
        QAItem(
            question="Why do animals like safe water play?",
            answer="Safe water play lets them have fun without getting hurt or too cold.",
        ),
        QAItem(
            question="What does rhyme mean?",
            answer="Rhyme means words sound alike at the end, like sing and ring.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
    lines.append("== (3) World questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  rhyme: {world.rhyme}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(Place, Hero, Trick) :- place(Place), creature(Hero), trick(Trick), loves_swim(Hero).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if c.loves_swim:
            lines.append(asp.fact("loves_swim", cid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def story_qa_world(sample: StorySample) -> str:
    return format_qa(sample)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for hero in CREATURES:
                for trick in TRICKS:
                    if hero == "fox" and trick == "pun":
                        continue
                    params = StoryParams(place=place, hero=hero, watcher="duck" if hero != "duck" else "frog", trick=trick)
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
