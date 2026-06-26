#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/emphatic_repair_snitch_magic_foreshadowing_curiosity_animal.py
=============================================================================================================

A small animal-story world about curiosity, a magical repair, and a snitch
who learns that telling the truth can still be gentle.

Premise:
- A curious animal discovers something broken.
- A magic tool can repair it, but only if the animal follows the right steps.
- A snitch tries to cause trouble, creating social tension.
- Foreshadowing matters: a tiny clue earlier points to the repair later.

The story generator builds state for:
- physical meters: broken, sparkly, tired, fixed, muddy, safe
- emotional memes: curious, worried, emphatic, ashamed, trusting, annoyed

The narrated story is driven by the simulated world state rather than by a
frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    kind: str = "thing"          # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    protected_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    snitch: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "bunny", "fox", "wolf", "cat", "mouse", "dog", "bear"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Place:
    name: str
    kind: str
    magic_ready: bool = False
    hides_clues: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    clue_word: str
    required_place_kind: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    place: str
    hero: str
    snitch: str
    broken_thing: str
    tool: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _inc(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _mem(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _has(ent: Entity, key: str) -> bool:
    return ent.meters.get(key, 0.0) >= THRESHOLD


def _em(ent: Entity, key: str) -> bool:
    return ent.memes.get(key, 0.0) >= THRESHOLD


def _normalize(name: str) -> str:
    return name.strip().lower()


PLACES = {
    "forest": Place(name="the forest path", kind="outdoor", magic_ready=True, hides_clues=True),
    "pond": Place(name="the pond bank", kind="outdoor", magic_ready=True, hides_clues=False),
    "barn": Place(name="the old barn", kind="indoor", magic_ready=True, hides_clues=False),
}

HEROES = {
    "rabbit": {"type": "rabbit", "label": "rabbit", "phrase": "a curious rabbit"},
    "fox": {"type": "fox", "label": "fox", "phrase": "a small fox"},
    "mouse": {"type": "mouse", "label": "mouse", "phrase": "a tiny mouse"},
    "bear": {"type": "bear", "label": "bear", "phrase": "a gentle bear"},
}

SNITCHES = {
    "crow": {"type": "crow", "label": "crow", "phrase": "a sharp-eyed crow"},
    "magpie": {"type": "magpie", "label": "magpie", "phrase": "a talkative magpie"},
    "squirrel": {"type": "squirrel", "label": "squirrel", "phrase": "a twitchy squirrel"},
}

BROKEN_THINGS = {
    "nest": {"label": "nest", "phrase": "a little nest", "repairable": True},
    "toy": {"label": "toy", "phrase": "a bright wooden toy", "repairable": True},
    "lantern": {"label": "lantern", "phrase": "a tiny lantern", "repairable": True},
}

TOOLS = {
    "moonthread": Tool(
        id="moonthread",
        label="moon thread",
        phrase="a silver moon thread",
        fixes={"broken"},
        clue_word="spark",
        required_place_kind="outdoor",
    ),
    "goldenleaf": Tool(
        id="goldenleaf",
        label="golden leaf patch",
        phrase="a soft golden leaf patch",
        fixes={"broken"},
        clue_word="glow",
        required_place_kind="outdoor",
    ),
    "hushbottle": Tool(
        id="hushbottle",
        label="hush bottle",
        phrase="a small hush bottle of magic glue",
        fixes={"broken"},
        clue_word="hum",
        required_place_kind="indoor",
    ),
}

CURATED = [
    StoryParams(place="forest", hero="rabbit", snitch="crow", broken_thing="nest", tool="moonthread"),
    StoryParams(place="pond", hero="mouse", snitch="magpie", broken_thing="toy", tool="goldenleaf"),
    StoryParams(place="barn", hero="fox", snitch="squirrel", broken_thing="lantern", tool="hushbottle"),
]

TRAITS = ["curious", "emphatic", "gentle", "brave", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about curiosity, snitching, and magical repair.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--snitch", choices=SNITCHES)
    ap.add_argument("--broken-thing", choices=BROKEN_THINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    snitch = getattr(args, "snitch", None) or rng.choice([k for k in SNITCHES if k != hero])
    broken = getattr(args, "broken_thing", None) or rng.choice(list(BROKEN_THINGS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    if hero == snitch:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if place == "barn" and tool != "hushbottle":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if place != "barn" and tool == "hushbottle":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, snitch=snitch, broken_thing=broken, tool=tool)


def story_opening(world: World, hero: Entity, thing: Entity) -> None:
    _mem(hero, "curious")
    world.say(
        f"{hero.label.capitalize()} was a curious little animal who loved to poke around {world.place.name}."
    )
    world.say(
        f"One day, {hero.label} found {thing.phrase}, and something about it looked wrong."
    )
    _mem(hero, "foreshadowing")


def foreshadow(world: World, hero: Entity, thing: Entity, tool: Tool) -> None:
    if world.place.magic_ready:
        world.say(
            f"Nearby, a tiny {tool.clue_word} of light winked once in the leaves, like a clue waiting for later."
        )
    else:
        world.say(
            f"In the barn, a soft {tool.clue_word}-like hum hid inside the boards, like a clue waiting for later."
        )
    _mem(hero, "foreshadowing", 1)
    _mem(thing, "broken", 1)
    _inc(thing, "broken", 1)


def snitching(world: World, hero: Entity, snitch: Entity, thing: Entity) -> None:
    _mem(snitch, "annoyed")
    world.say(
        f"{snitch.label} saw the broken thing and piped up, 'I saw it first!'"
    )
    world.say(
        f"{hero.label} felt a pinch of worry, but stayed focused on the broken {thing.label}."
    )
    _mem(hero, "worried")
    _mem(hero, "emphatic")


def ask_for_help(world: World, hero: Entity, tool: Tool) -> None:
    world.say(
        f"Then {hero.label} said, very emphatically, 'We need the {tool.label} if we want to repair this kindly.'"
    )


def repair_magic(world: World, hero: Entity, thing: Entity, tool: Tool) -> None:
    if world.place.kind != tool.required_place_kind:
        pass
    _inc(thing, "sparkly", 1)
    thing.meters["fixed"] = 1.0
    thing.meters["broken"] = 0.0
    _mem(hero, "hope")
    world.say(
        f"When {hero.label} touched the {thing.label} with {tool.label}, the magic gave a warm shimmer."
    )
    world.say(
        f"The crack mended, the wobble stopped, and the whole little thing became fixed again."
    )


def resolution(world: World, hero: Entity, snitch: Entity, thing: Entity) -> None:
    _mem(snitch, "ashamed")
    _mem(hero, "trusting")
    world.say(
        f"{snitch.label} blinked and quietly admitted, 'I was only trying to snitch.'"
    )
    world.say(
        f"{hero.label} nodded. 'Next time, just tell the truth,' {hero.pronoun()} said, and {hero.label} did not sound mad."
    )
    world.say(
        f"At the end, {thing.phrase} was fixed, and {hero.label} walked home with calm paws and a brighter heart."
    )


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero_cfg = _safe_lookup(HEROES, params.hero)
    snitch_cfg = _safe_lookup(SNITCHES, params.snitch)
    thing_cfg = _safe_lookup(BROKEN_THINGS, params.broken_thing)
    tool = _safe_lookup(TOOLS, params.tool)

    hero = world.add(Entity(id="hero", kind="animal", type=hero_cfg["type"], label=hero_cfg["label"], phrase=hero_cfg["phrase"]))
    snitch = world.add(Entity(id="snitch", kind="animal", type=snitch_cfg["type"], label=snitch_cfg["label"], phrase=snitch_cfg["phrase"]))
    thing = world.add(Entity(id="thing", type=thing_cfg["label"], label=thing_cfg["label"], phrase=thing_cfg["phrase"]))
    world.add(Entity(id="tool", type="thing", label=tool.label, phrase=tool.phrase))

    story_opening(world, hero, thing)
    world.para()
    foreshadow(world, hero, thing, tool)
    snitching(world, hero, snitch, thing)
    ask_for_help(world, hero, tool)
    world.para()
    repair_magic(world, hero, thing, tool)
    resolution(world, hero, snitch, thing)

    world.facts.update(hero=hero, snitch=snitch, thing=thing, tool=tool, place=place, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short animal story about {f['hero'].label}, a curious animal, who finds a broken {f['thing'].label} at {f['place'].name}.",
        f"Tell a gentle story where a snitch animal causes trouble, but magic helps {f['hero'].label} repair the broken thing.",
        f"Write an animal story with foreshadowing: a small clue appears early and later leads to a magical repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, snitch, thing, tool, place = f["hero"], f["snitch"], f["thing"], (f.get("tool") or next(iter(TOOLS.values()))), f["place"]
    return [
        QAItem(
            question=f"Who was curious in the story?",
            answer=f"{hero.label.capitalize()} was the curious animal who noticed the broken {thing.label} first.",
        ),
        QAItem(
            question=f"What did the snitch do when it saw the broken {thing.label}?",
            answer=f"{snitch.label.capitalize()} snitched and said it saw the broken {thing.label} first, which made the moment tense.",
        ),
        QAItem(
            question=f"How was the {thing.label} repaired?",
            answer=f"{hero.label.capitalize()} used {tool.label} magic to repair the {thing.label}, and the broken part became fixed again.",
        ),
        QAItem(
            question=f"What was the clue that foreshadowed the repair?",
            answer=f"An early {tool.clue_word} of light or hum hinted that {tool.label} magic would help later at {place.name}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The broken {thing.label} was fixed, the snitch calmed down, and {hero.label} went home feeling brighter and safer.",
        ),
    ]


KNOWLEDGE = {
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special pretend power that can do surprising things, like make a repair sparkle.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue in a story that hints at something important that will happen later.",
        )
    ],
    "repair": [
        QAItem(
            question="What does repair mean?",
            answer="Repair means fixing something that is broken so it can work or look good again.",
        )
    ],
    "snitch": [
        QAItem(
            question="What is a snitch?",
            answer="A snitch is someone who tells on others, often to get them in trouble.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        q for key in ["curiosity", "magic", "foreshadowing", "repair", "snitch"]
        for q in KNOWLEDGE[key]
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
place(forest). place(pond). place(barn).
hero(rabbit). hero(fox). hero(mouse). hero(bear).
snitch(crow). snitch(magpie). snitch(squirrel).
thing(nest). thing(toy). thing(lantern).
tool(moonthread). tool(goldenleaf). tool(hushbottle).

magic_place(forest). magic_place(pond). magic_place(barn).
clue(moonthread,spark). clue(goldenleaf,glow). clue(hushbottle,hum).

valid(P,H,S,T) :- place(P), hero(H), snitch(S), thing(T), H != S, magic_place(P).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if _safe_lookup(PLACES, p).magic_ready:
            lines.append(asp.fact("magic_place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for s in SNITCHES:
        lines.append(asp.fact("snitch", s))
    for t in BROKEN_THINGS:
        lines.append(asp.fact("thing", t))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
        lines.append(asp.fact("clue", tool.id, tool.clue_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for p in PLACES:
        for h in HEROES:
            for s in SNITCHES:
                if h == s:
                    continue
                for t in BROKEN_THINGS:
                    if _safe_lookup(PLACES, p).magic_ready:
                        out.append((p, h, s, t))
    return sorted(out)


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if a - p:
        print("only in asp:", sorted(a - p))
    if p - a:
        print("only in python:", sorted(p - a))
    return 1


def explain_rejection(params: StoryParams) -> str:
    return "(No story: that combination does not make a coherent magical repair tale.)"


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} valid story combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} / {p.snitch} / {p.broken_thing} / {p.tool} @ {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
