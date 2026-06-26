#!/usr/bin/env python3
"""
A tiny mythic storyworld about ramen, misunderstanding, humor, and transformation.

Seed story premise:
- In a small noodle shrine, a bowl of ramen is treated like a sacred offering.
- A hungry child misunderstands a blessing as a boast, which causes comic trouble.
- A gentle transformation follows: the ramen changes shape, the child's feelings change,
  and the shrine's strictness softens into laughter and sharing.

This script generates one short, complete story per sample with grounded QA and an ASP twin.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    bowl: object | None = None
    elder: object | None = None
    hero: object | None = None
    shrine: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "priest", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "priestess", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    elder: str
    elder_type: str
    shrine: str
    ramen_style: str
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


HEROES = [
    ("Mika", "girl"),
    ("Ren", "boy"),
    ("Sora", "boy"),
    ("Aya", "girl"),
    ("Tomo", "boy"),
]

ELDERS = [
    ("Grandmother", "elder"),
    ("Priest", "priest"),
    ("Monk", "priest"),
    ("Aunt", "elder"),
]

SHRINES = [
    "the lantern shrine",
    "the hill shrine",
    "the moon gate",
    "the cedar courtyard",
]

RAMEN_STYLES = {
    "plain": {
        "label": "a steaming bowl of ramen",
        "mood": "simple and holy",
        "transform": "the noodles curled into a smiling spiral",
        "humor": "the steam made the elder's mustache wiggle like a caterpillar",
    },
    "egg": {
        "label": "ramen with a golden egg",
        "mood": "bright and lucky",
        "transform": "the egg split into two perfect moons",
        "humor": "one noodle slurped itself into a ribbon on the bowl's rim",
    },
    "miso": {
        "label": "miso ramen",
        "mood": "deep and warm",
        "transform": "the broth turned from cloudy gold into a tiny shining pond",
        "humor": "a bean sprout stood up like a little spear and saluted",
    },
    "spicy": {
        "label": "spicy ramen",
        "mood": "bold and fiery",
        "transform": "the red oil softened into a sunset swirl",
        "humor": "the pepper flakes danced in circles like tiny red lanterns",
    },
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic ramen storyworld with humor and transformation.")
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["elder", "priest"])
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--ramen-style", choices=sorted(RAMEN_STYLES))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero, hero_type = rng.choice(HEROES)
    elder, elder_type = rng.choice(ELDERS)
    shrine = rng.choice(SHRINES)
    ramen_style = rng.choice(sorted(RAMEN_STYLES))

    if getattr(args, "hero", None):
        hero = getattr(args, "hero", None)
    if getattr(args, "hero_type", None):
        hero_type = getattr(args, "hero_type", None)
    if getattr(args, "elder", None):
        elder = getattr(args, "elder", None)
    if getattr(args, "elder_type", None):
        elder_type = getattr(args, "elder_type", None)
    if getattr(args, "shrine", None):
        shrine = getattr(args, "shrine", None)
    if getattr(args, "ramen_style", None):
        ramen_style = getattr(args, "ramen_style", None)

    return StoryParams(
        hero=hero,
        hero_type=hero_type,
        elder=elder,
        elder_type=elder_type,
        shrine=shrine,
        ramen_style=ramen_style,
    )


def _make_world(params: StoryParams) -> World:
    world = World()
    style = _safe_lookup(RAMEN_STYLES, params.ramen_style)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero,
        traits=["young", "curious", "hungry"],
        meters={"hunger": 2.0},
        memes={"wonder": 1.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder_type,
        label=params.elder,
        traits=["wise", "stern", "gentle"],
        meters={"patience": 2.0},
        memes={"pride": 1.0},
    ))
    bowl = world.add(Entity(
        id="ramen",
        kind="thing",
        type="ramen",
        label=style["label"],
        owner=elder.id,
        meters={"steam": 1.0, "broth": 1.0},
        memes={"sacred": 1.0, "funny": 0.0, "changed": 0.0},
    ))
    shrine = world.add(Entity(
        id="shrine",
        kind="place",
        type="shrine",
        label=params.shrine,
        traits=["quiet", "ancient", "listening"],
        meters={"bells": 1.0},
        memes={"solemn": 1.0},
    ))

    world.facts.update(
        hero=hero,
        elder=elder,
        bowl=bowl,
        shrine=shrine,
        style=params.ramen_style,
        style_data=style,
    )
    return world


def _paragraph_one(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    bowl: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "bowl")
    shrine: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "shrine")
    style = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "style_data")

    world.say(
        f"At {shrine.label}, {elder.label} lifted {bowl.label} as if it were a gift for the sky."
    )
    world.say(
        f"{hero.label}, a young {hero.type}, came near the stone steps and smelled the broth."
    )
    world.say(
        f"It looked {style['mood']}, and the steam rose like a white ribbon in a tale."
    )


def _misunderstanding(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    bowl: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "bowl")
    style = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "style_data")

    hero.meters["hunger"] += 1
    hero.memes["confusion"] += 1
    elder.memes["pride"] += 1

    world.say(
        f"{hero.label} heard {elder.label} murmur, 'This ramen is for the worthy,' and took it the wrong way."
    )
    world.say(
        f"{hero.label} thought the bowl was being bragged about, which was a very small mistake with a very loud face."
    )
    world.say(
        f"{hero.label} pointed at the bowl and said, 'It is only noodles,' and the shrine seemed to gasp."
    )
    world.say(
        f"Then {style['humor']}, and even the bells looked ready to laugh."
    )


def _turn(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    bowl: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "bowl")
    style = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "style_data")

    hero.memes["embarrassment"] = 1.0
    elder.memes["surprise"] = 1.0

    world.say(
        f"{elder.label} blinked, then smiled, for {hero.label} had mistaken a blessing for a boast."
    )
    world.say(
        f"To make peace, {elder.label} lifted the chopsticks and spoke the old words of change."
    )
    world.say(
        f"At once, {style['transform']}."
    )
    bowl.memes["changed"] = 1.0
    bowl.meters["steam"] = 0.5


def _resolution(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    bowl: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "bowl")

    hero.memes["joy"] = 2.0
    hero.memes["confusion"] = 0.0
    elder.memes["pride"] = 0.0
    elder.memes["warmth"] = 1.0

    world.say(
        f"{hero.label} saw the changed bowl and laughed, because the ramen had become a little miracle."
    )
    world.say(
        f"{elder.label} shared it with {hero.label}, and the two of them ate in peace while the shrine kept the secret."
    )
    world.say(
        f"In the end, the bowl was still ramen, but it had also become a lesson: laughter can turn misunderstanding into a feast."
    )


def generate_storyworld(params: StoryParams) -> World:
    world = _make_world(params)
    _paragraph_one(world)
    world.para()
    _misunderstanding(world)
    world.para()
    _turn(world)
    _resolution(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/4.
#show has_fix/4.

valid(Hero, Elder, Shrine, Style) :-
    hero(Hero), elder(Elder), shrine(Shrine), ramen_style(Style),
    misunderstanding(Hero, Elder, Style),
    transformation(Style),
    humor(Style),
    mythic(Shrine).

has_fix(Hero, Elder, Shrine, Style) :-
    valid(Hero, Elder, Shrine, Style).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for h, t in HEROES:
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("hero_type", h, t))
    for e, t in ELDERS:
        lines.append(asp.fact("elder", e))
        lines.append(asp.fact("elder_type", e, t))
    for s in SHRINES:
        lines.append(asp.fact("shrine", s))
        lines.append(asp.fact("mythic", s))
    for style in RAMEN_STYLES:
        lines.append(asp.fact("ramen_style", style))
        lines.append(asp.fact("transformation", style))
        lines.append(asp.fact("humor", style))
        lines.append(asp.fact("misunderstanding", "any_hero", "any_elder", style))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4.\n#show has_fix/4."))
    atoms = set((sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model)
    if atoms:
        print("OK: ASP program produced a model.")
        return 0
    print("MISMATCH: ASP program did not produce any shown atoms.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short mythic story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label}, ramen, and a mistaken message at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "shrine").label}.",
        f"Tell a gentle tale where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder").label} offers {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "style_data")['label']} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label} misunderstands the blessing.",
        f"Make a child-friendly myth in which ramen changes in a funny way and everyone learns from the mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    shrine: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "shrine")
    style = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "style_data")
    bowl: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "bowl")

    return [
        QAItem(
            question=f"Who came to {shrine.label} and misunderstood the ramen blessing?",
            answer=f"{hero.label} came to {shrine.label} and misunderstood what {elder.label} meant."
        ),
        QAItem(
            question=f"What did the elder say was special about the ramen?",
            answer=f"The ramen was treated like a gift, and it felt {style['mood']} before the change."
        ),
        QAItem(
            question=f"What changed after the mistake was cleared up?",
            answer=f"The ramen changed shape in a magical way, and {hero.label} changed from confused to laughing."
        ),
        QAItem(
            question=f"Why did the scene become funny?",
            answer=f"It became funny because the steam, the elder's words, and {hero.label}'s misunderstanding all collided at once."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ramen?",
            answer="Ramen is a noodle soup, usually served in a bowl with broth, noodles, and tasty toppings."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing and reacts to that mistake."
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or becomes very different."
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can help because laughter makes a mistake feel lighter and helps people get along again."
        ),
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = generate_storyworld(params)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(h[0], e[0], s) for h in HEROES for e in ELDERS for s in SHRINES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        hero=getattr(args, "hero", None) or rng.choice(HEROES)[0],
        hero_type=getattr(args, "hero_type", None) or rng.choice(HEROES)[1],
        elder=getattr(args, "elder", None) or rng.choice(ELDERS)[0],
        elder_type=getattr(args, "elder_type", None) or rng.choice(ELDERS)[1],
        shrine=getattr(args, "shrine", None) or rng.choice(SHRINES),
        ramen_style=getattr(args, "ramen_style", None) or rng.choice(sorted(RAMEN_STYLES)),
    )
    return params


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for h, ht in HEROES:
            for e, et in ELDERS:
                for shrine in SHRINES[:2]:
                    for style in sorted(RAMEN_STYLES):
                        params = StoryParams(h, ht, e, et, shrine, style, seed=base_seed)
                        samples.append(generate(params))
        return samples

    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4.\n#show has_fix/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    samples = build_samples(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
