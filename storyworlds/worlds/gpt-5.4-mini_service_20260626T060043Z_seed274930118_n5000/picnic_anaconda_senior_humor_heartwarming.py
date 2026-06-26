#!/usr/bin/env python3
"""
Standalone story world: picnic, an anaconda, and a senior helper.

Seed premise:
- A picnic is being prepared.
- An anaconda unexpectedly becomes part of the day.
- A senior character brings warmth, patience, and humor.
- The story should feel heartwarming rather than frightening.

The world models a small causal chain:
- Picnic plans depend on weather, basket contents, and a safe spot.
- The anaconda is not a monster; it is a large, calm animal that may cause worry
  because of its size, but can also become the source of a funny misunderstanding.
- The senior character uses experience and kindness to turn tension into laughter.
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
# Shared world model
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
    kind: str = "thing"          # character | thing | animal
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    worn_by: Optional[str] = None

    anaconda: object | None = None
    hero: object | None = None
    senior: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother", "senior woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather", "senior man"}:
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


@dataclass
class Location:
    place: str = "the park"
    shade: bool = True
    benches: bool = True
    ponds: bool = False
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
class BasketItem:
    id: str
    label: str
    phrase: str
    edible: bool = True
    tasty: bool = True
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
    snack: str
    name: str
    age_label: str
    tone: str = "heartwarming"
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


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        w = World(self.location)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
LOCATIONS = {
    "park": Location(place="the park", shade=True, benches=True, ponds=False),
    "garden": Location(place="the garden", shade=True, benches=False, ponds=False),
    "riverside": Location(place="the riverside lawn", shade=False, benches=True, ponds=True),
    "backyard": Location(place="the backyard", shade=True, benches=True, ponds=False),
}

SNACKS = {
    "sandwiches": BasketItem("sandwiches", "sandwiches", "fresh sandwiches"),
    "cookies": BasketItem("cookies", "cookies", "soft cookies"),
    "fruit": BasketItem("fruit", "fruit", "bright fruit"),
    "lemonade": BasketItem("lemonade", "lemonade", "cold lemonade"),
}

GENTLE_NAMES = ["Mina", "June", "Eli", "Noa", "Maya", "Theo", "Lena", "Iris", "Owen", "Ruby"]
TRAITS = ["cheerful", "kind", "curious", "patient", "spirited", "gentle"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def story_start(world: World, senior: Entity, hero: Entity, snack: BasketItem) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'cheerful')} child who loved picnic days."
    )
    world.say(
        f"{senior.label} was a {senior.type} with a calm smile and a pocket full of patient jokes."
    )
    world.say(
        f"That morning, {hero.id} helped pack {snack.phrase}, and {senior.pronoun('subject').capitalize()} said the day already felt special."
    )


def introduce_anaconda(world: World, anaconda: Entity) -> None:
    world.say(
        f"At the park, they noticed a huge anaconda resting in the grass like a curly green rope."
    )
    world.say(
        f"At first, {world.get('hero').id} froze, because the snake looked so long it seemed to have its own weather."
    )
    world.facts["worry"] = True


def turn_to_humor(world: World, senior: Entity, hero: Entity, anaconda: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    senior.memes["humor"] = senior.memes.get("humor", 0) + 1
    world.say(
        f"{senior.label} peered over their glasses and chuckled, 'Well, I did ask for a picnic with a big appetite.'"
    )
    world.say(
        f"Then {senior.pronoun('subject')} pointed out that the anaconda was only sniffing the picnic blanket, not chasing anyone."
    )
    world.say(
        f"{hero.id} blinked, and the scary moment began to wobble into a funny one."
    )


def resolution(world: World, senior: Entity, hero: Entity, snack: BasketItem, anaconda: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    senior.memes["joy"] = senior.memes.get("joy", 0) + 1
    anaconda.meters["near_blanket"] = 1
    world.say(
        f"{senior.label} calmly moved the basket a little farther away and offered the anaconda a safe, empty patch of shade."
    )
    world.say(
        f"The anaconda settled beside the blanket like a very long guest, and everyone laughed when its tail curled around a stray napkin as if it were helping."
    )
    world.say(
        f"Soon {hero.id} was sharing {snack.phrase} with {senior.label}, and the picnic felt warm, funny, and safe."
    )
    world.say(
        f"By the end of the afternoon, the biggest thing at the picnic was no longer the snake; it was the kindness in the air."
    )


def build_world(params: StoryParams) -> World:
    if params.place not in LOCATIONS:
        pass
    if params.snack not in SNACKS:
        pass

    world = World(_safe_lookup(LOCATIONS, params.place))

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        memes={"trait": params.age_label, "joy": 0, "worry": 0},
    ))
    senior = world.add(Entity(
        id="Senior",
        kind="character",
        type="senior",
        label="Grandma",
        memes={"humor": 0, "joy": 0},
    ))
    anaconda = world.add(Entity(
        id="Anaconda",
        kind="animal",
        type="anaconda",
        label="an anaconda",
        phrase="a very long anaconda",
        meters={"length": 8.0},
    ))
    snack = _safe_lookup(SNACKS, params.snack)
    world.add(Entity(
        id="Basket",
        kind="thing",
        type="basket",
        label="basket",
        phrase=snack.phrase,
        owner=hero.id,
    ))

    story_start(world, senior, hero, snack)
    world.para()
    world.say(
        f"They carried everything to {world.location.place}, where the grass was soft and the air felt good for sitting."
    )
    introduce_anaconda(world, anaconda)
    world.para()
    turn_to_humor(world, senior, hero, anaconda)
    world.para()
    resolution(world, senior, hero, snack, anaconda)

    world.facts.update(
        hero=hero,
        senior=senior,
        anaconda=anaconda,
        snack=snack,
        params=params,
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story for young children about a picnic, an anaconda, and a kind senior who uses humor.',
        f"Tell a gentle story where {f['hero'].id} is surprised by an anaconda during a picnic at {f['place']}.",
        f"Write a funny-but-soft story in which a senior turns worry into laughter while sharing {f['snack'].phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    senior = _safe_fact(world, f, "senior")
    snack = _safe_fact(world, f, "snack")
    return [
        QAItem(
            question=f"Who went on the picnic with {hero.id}?",
            answer=f"{hero.id} went with {senior.label}, who stayed calm and helped make the picnic feel safe.",
        ),
        QAItem(
            question="Why did the picnic become a little scary at first?",
            answer="It became scary because a huge anaconda was lying in the grass and looked surprising at first.",
        ),
        QAItem(
            question=f"What did they share by the end of the story?",
            answer=f"They shared {snack.phrase}, and the picnic ended with laughter instead of worry.",
        ),
        QAItem(
            question="How did the senior character help?",
            answer="The senior used a calm joke, moved the basket a little farther away, and helped everyone see the anaconda as harmless.",
        ),
        QAItem(
            question="What changed most by the end?",
            answer="The worry changed into comfort and humor, so the picnic felt warm and heartwarming.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a picnic?",
        answer="A picnic is a meal eaten outside, often on a blanket in a park or garden.",
    ),
    QAItem(
        question="What is an anaconda?",
        answer="An anaconda is a very large snake that can live near warm wetlands and rivers.",
    ),
    QAItem(
        question="Why can a senior person be helpful in a story?",
        answer="A senior person can be helpful because they often have experience, patience, and a steady way of calming others.",
    ),
    QAItem(
        question="How can humor help when someone feels worried?",
        answer="Humor can help by making a tense moment feel lighter, which can help people relax and smile.",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.

location(park).
location(garden).
location(riverside).
location(backyard).

snack(sandwiches).
snack(cookies).
snack(fruit).
snack(lemonade).

picnic_ok(P,S) :- location(P), snack(S).
valid_story(P,S,A) :- picnic_ok(P,S), anaconda(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for snack in SNACKS:
        lines.append(asp.fact("snack", snack))
    lines.append(asp.fact("anaconda", "anaconda"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(loc, snack, "anaconda") for loc in LOCATIONS for snack in SNACKS}
    cl = set(asp_valid_stories())
    if cl == py:
        print(f"OK: clingo gate matches Python ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming picnic story world with an anaconda and a senior helper.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name")
    ap.add_argument("--age-label", choices=["curious", "cheerful", "gentle", "spirited", "kind"])
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
    place = getattr(args, "place", None) or rng.choice(list(LOCATIONS))
    snack = getattr(args, "snack", None) or rng.choice(list(SNACKS))
    name = getattr(args, "name", None) or rng.choice(GENTLE_NAMES)
    age_label = getattr(args, "age_label", None) or rng.choice(TRAITS)
    return StoryParams(place=place, snack=snack, name=name, age_label=age_label)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=WORLD_KNOWLEDGE,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="park", snack="cookies", name="Mina", age_label="cheerful"),
            StoryParams(place="garden", snack="fruit", name="Theo", age_label="curious"),
            StoryParams(place="riverside", snack="sandwiches", name="Ruby", age_label="gentle"),
            StoryParams(place="backyard", snack="lemonade", name="Eli", age_label="kind"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: picnic at {p.place} with {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
