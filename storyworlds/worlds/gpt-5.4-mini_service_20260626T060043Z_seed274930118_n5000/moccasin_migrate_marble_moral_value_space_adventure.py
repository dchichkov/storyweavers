#!/usr/bin/env python3
"""
storyworlds/worlds/moccasin_migrate_marble_moral_value_space_adventure.py
=========================================================================

A small classical story world in a space-adventure style.

Premise:
A child explorer on a tiny ship wants to help a drifting colony migrate to a
new moon. The child also treasures a lucky marble and a soft pair of moccasins.
A mission choice creates a moral value tension: keep the marble safe and follow
the rules, or risk a small shortcut to help everyone migrate faster. The story
resolves by choosing the careful, kind path.

The world model tracks physical meters and emotional memes:
- meters: distance, fuel, dust, safety, wear
- memes: trust, worry, pride, gratitude, courage

The story is generated from simulated state, not from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    companion: object | None = None
    hero: object | None = None
    marble: object | None = None
    moccasin: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Ship:
    name: str
    place: str
    target_moon: str
    moral_value: str
    fuel: float = 5.0
    safety: float = 5.0
    dust: float = 0.0
    distance_to_moon: float = 6.0
    migrated: bool = False
    trust: float = 0.0
    worry: float = 0.0
    pride: float = 0.0
    gratitude: float = 0.0
    courage: float = 0.0
    facts: dict = field(default_factory=dict)
    ship: object | None = None
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
    place: str
    moral_value: str
    name: str
    gender: str
    companion: str
    prize: str
    seed: Optional[int] = None
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


SETTINGS = {
    "orbital_dock": "the orbital dock",
    "silver_habitat": "the silver habitat",
    "red_station": "the red station",
}

MORAL_VALUES = {
    "kindness": "kindness",
    "honesty": "honesty",
    "responsibility": "responsibility",
    "courage": "courage",
    "patience": "patience",
}

NAMES_GIRL = ["Mira", "Nova", "Ada", "Tess", "Luna", "Iris"]
NAMES_BOY = ["Pax", "Leo", "Otto", "Finn", "Sage", "Eli"]
COMPANIONS = ["captain", "engineer", "pilot", "guide"]

ASP_RULES = r"""
#show valid/3.
place(orbital_dock; silver_habitat; red_station).

moral_value(kindness; honesty; responsibility; courage; patience).

tool(moccasin).
prize(marble).

valid(P, M, T) :- place(P), moral_value(M), tool(T).
"""

MORAL_GATES = {
    "kindness": "share the safe plan",
    "honesty": "tell the truth about the marble",
    "responsibility": "check the ship before leaving",
    "courage": "keep going even when the route feels scary",
    "patience": "wait for the docking light to turn green",
}


def safe_meter(x: float) -> float:
    return max(0.0, x)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.ship = Ship(
            name="Little Comet",
            place=_safe_lookup(SETTINGS, params.place),
            target_moon="Lantern Moon",
            moral_value=params.moral_value,
        )
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(
            f"  ship      place={self.ship.place} fuel={self.ship.fuel:.1f} "
            f"safety={self.ship.safety:.1f} dust={self.ship.dust:.1f} "
            f"distance_to_moon={self.ship.distance_to_moon:.1f} migrated={self.ship.migrated}"
        )
        lines.append(
            f"  memes     trust={self.ship.trust:.1f} worry={self.ship.worry:.1f} "
            f"pride={self.ship.pride:.1f} gratitude={self.ship.gratitude:.1f} courage={self.ship.courage:.1f}"
        )
        for e in self.entities.values():
            bits = []
            if e.worn_by:
                bits.append(f"worn_by={e.worn_by}")
            if e.plural:
                bits.append("plural=True")
            lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
        return "\n".join(lines)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure moral-value story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--moral-value", dest="moral_value", choices=MORAL_VALUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--prize", choices=["marble"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MORAL_VALUES:
        lines.append(asp.fact("moral_value", m))
    lines.append(asp.fact("tool", "moccasin"))
    lines.append(asp.fact("prize", "marble"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for m in MORAL_VALUES:
            out.append((p, m, "moccasin"))
    return out


def asp_verify() -> int:
    import asp
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    moral_value = getattr(args, "moral_value", None) or rng.choice(list(MORAL_VALUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(rng, gender)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    prize = getattr(args, "prize", None) or "marble"
    return StoryParams(place=place, moral_value=moral_value, name=name, gender=gender, companion=companion, prize=prize)


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    hero = world.get("hero")
    companion = world.get("companion")
    return [
        QAItem(
            question=f"What did {hero.id} carry on the space trip?",
            answer=f"{hero.id} carried a small marble and wore moccasins for the trip through the ship.",
        ),
        QAItem(
            question=f"Why did the {companion.type} ask {hero.id} to slow down?",
            answer=f"The {companion.type} worried that rushing could drop the marble and waste fuel, so they chose a careful plan.",
        ),
        QAItem(
            question=f"What moral value guided the ending?",
            answer=f"The ending was guided by {p.moral_value}, and that helped the crew choose the safe way to migrate.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are moccasins?",
            answer="Moccasins are soft shoes that help feet stay comfortable when walking.",
        ),
        QAItem(
            question="What is a marble?",
            answer="A marble is a small smooth ball, often made of glass or stone.",
        ),
        QAItem(
            question="What does migrate mean?",
            answer="To migrate means to move from one place to another, often to live or travel there for a long time.",
        ),
        QAItem(
            question="What is moral value?",
            answer="A moral value is a good rule for how to treat others, like kindness or honesty.",
        ),
    ]


def generate_story(world: World) -> None:
    p = world.params
    hero = world.add(Entity(id=p.name, kind="character", type=p.gender, traits=["little", "brave"]))
    companion = world.add(Entity(id="companion", kind="character", type=p.companion))
    marble = world.add(Entity(id="marble", type="marble", label="marble", phrase="a bright blue marble", owner=hero.id))
    moccasin = world.add(Entity(id="moccasin", type="moccasin", label="moccasins", phrase="soft moccasins", owner=hero.id, plural=True))
    moccasin.worn_by = hero.id

    world.say(f"{hero.id} lived at {world.ship.place} and loved space trips more than quiet days.")
    world.say(f"{hero.id} kept a bright marble in one pocket and wore soft moccasins on {hero.pronoun('possessive')} feet.")
    world.say(f"One day, the colony had to migrate to {world.ship.target_moon}, and everyone hurried to the launch ring.")

    world.para()
    world.say(f"{hero.id} wanted to help right away, but the route lights blinked yellow and the deck felt slippery.")
    world.ship.worry += 1.0
    world.ship.trust += 0.5
    world.say(f"The {companion.type} noticed the marble wobbling in {hero.pronoun('possessive')} hand and said, \"Let's be careful.\"")
    world.say(f"That was the moral value of {p.moral_value}: {_safe_lookup(MORAL_GATES, p.moral_value)}.")
    if p.moral_value == "honesty":
        world.ship.gratitude += 1.0
        world.say(f"{hero.id} told the truth and admitted the marble made {hero.pronoun('object')} nervous to rush.")
    elif p.moral_value == "responsibility":
        world.ship.courage += 1.0
        world.say(f"{hero.id} checked the hatch straps twice before stepping forward.")
    elif p.moral_value == "kindness":
        world.ship.trust += 1.0
        world.say(f"{hero.id} offered to carry a crate for the smaller hatchling crew first.")
    elif p.moral_value == "courage":
        world.ship.courage += 1.5
        world.say(f"{hero.id} took a slow breath and kept walking, even though the ship hummed loudly.")
    else:
        world.ship.pride += 1.0
        world.say(f"{hero.id} waited until the docking light turned green instead of sneaking ahead.")

    world.para()
    world.ship.fuel -= 1.0
    world.ship.distance_to_moon -= 2.5
    world.ship.safety += 1.0
    world.ship.dust += 0.2
    world.say(f"They used the careful path through the cargo tunnel, so the marble stayed safe and the moccasins did not slip.")
    world.say(f"At last, the ship reached the new moon, and the colony began to migrate in peace.")
    world.ship.migrated = True
    world.ship.gratitude += 1.0
    world.ship.pride += 0.5
    world.say(f"{hero.id} smiled at the shining moon, clutching the marble and looking proud in {hero.pronoun('possessive')} moccasins.")

    world.ship.facts.update(
        hero=hero,
        companion=companion,
        marble=marble,
        moccasin=moccasin,
        moral_value=p.moral_value,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly space adventure where {p.name} must migrate with a colony and learn the value of {p.moral_value}.",
        f"Tell a short story about a child in moccasins, a marble, and a careful trip to a moon base.",
        f"Write a gentle science-fiction story where a little {p.gender} helps a group migrate while keeping a lucky marble safe.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="orbital_dock", moral_value="kindness", name="Mira", gender="girl", companion="pilot", prize="marble"),
    StoryParams(place="silver_habitat", moral_value="honesty", name="Pax", gender="boy", companion="engineer", prize="marble"),
    StoryParams(place="red_station", moral_value="responsibility", name="Nova", gender="girl", companion="captain", prize="marble"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid()
        print(f"{len(triples)} compatible combos:\n")
        for p, m, t in triples:
            print(f"  {p:15} {m:14} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.moral_value} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
