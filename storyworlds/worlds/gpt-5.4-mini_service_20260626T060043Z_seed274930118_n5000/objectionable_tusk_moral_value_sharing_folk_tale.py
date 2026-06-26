#!/usr/bin/env python3
"""
A tiny folk-tale storyworld about sharing something objectionable: a tusk.

Premise:
- A small village has one prized tusk kept as a symbol of plenty.
- A child or creature wants to keep it, but a neighbor needs it for a shared
  village need.
- The tension is not about greed alone; the tusk is awkward and a little
  objectionable to carry around, so the story asks what is fair to do with it.
- A wise elder teaches that sharing can turn a problem into help.

The simulation tracks:
- physical ownership and carrying state
- whether the tusk is hidden, displayed, lent, or shared
- emotional states: pride, worry, fairness, gratitude, shame, warmth

The story ends with the tusk being shared in a way that helps the whole village.
"""

from __future__ import annotations

import argparse
import copy
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
    bearer: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    helper: object | None = None
    hero: object | None = None
    tusk: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Village:
    name: str
    place: str
    needs_water: bool = True
    needs_song: bool = True
    needs_story: bool = True
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
class Tusk:
    label: str = "tusk"
    phrase: str = "a long ivory tusk"
    objectionable: bool = True
    burden: str = "awkward to carry"
    value: str = "a token of the village's luck"
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
    village: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    elder_name: str
    elder_type: str
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


class World:
    def __init__(self, village: Village) -> None:
        self.village = village
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(copy.deepcopy(self.village))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


VILLAGES = {
    "brook": Village(name="Brook Hollow", place="by the silver brook"),
    "hill": Village(name="Mossy Hill", place="on a green hill"),
    "oak": Village(name="Oak Lantern", place="under the old oaks"),
}

HEROES = [
    ("boy", ["brave", "stubborn", "kind"]),
    ("girl", ["curious", "gentle", "earnest"]),
]
HELPERS = [
    ("boy", ["quiet", "helpful"]),
    ("girl", ["wise", "cheerful"]),
]
ELDERS = [
    ("woman", ["old", "wise"]),
    ("man", ["old", "kind"]),
]

NAMES = ["Ari", "Mina", "Taro", "Lena", "Jory", "Nia", "Pico", "Sana", "Oren", "Tila"]


def _emotion(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def predict_sharing(world: World, hero: Entity) -> bool:
    sim = world.copy()
    tusk = sim.get("tusk")
    helper = sim.get("helper")
    tusk.owner = helper.id
    tusk.bearer = helper.id
    _emotion(helper, "gratitude", 1)
    _emotion(hero, "fairness", 1)
    return True


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity, tusk: Entity) -> None:
    world.say(
        f"In {world.village.name}, {hero.id} lived {world.village.place}. "
        f"{hero.pronoun().capitalize()} had found {tusk.phrase}, and everyone said it was a little objectionable "
        f"because it was so long and awkward to carry."
    )
    world.say(
        f"{hero.id} liked having it close, while {helper.id} kept saying the village could use {tusk.it()} together."
    )
    _emotion(hero, "pride", 1)
    _emotion(helper, "need", 1)
    _emotion(elder, "watchfulness", 1)


def problem(world: World, hero: Entity, helper: Entity, elder: Entity, tusk: Entity) -> None:
    world.para()
    world.say(
        f"One dry morning, the brook grew thin and the little baskets of grain stood waiting. "
        f"{helper.id} said the people needed a strong bucket handle, and {tusk.label} was just the right size."
    )
    world.say(
        f"{hero.id} frowned. {hero.pronoun().capitalize()} did not want to let go of something so special."
    )
    _emotion(hero, "worry", 1)
    _emotion(helper, "hope", 1)
    tusk.bearer = hero.id


def warning(world: World, elder: Entity, hero: Entity, helper: Entity, tusk: Entity) -> None:
    world.say(
        f"Then {elder.id} came slowly from the path and said, "
        f'"A thing can be fine to keep, but better to share when the village is thirsty."'
    )
    world.say(
        f'"If {hero.id} holds {tusk.it()} alone, it stays only a tusk. If {hero.id} shares it, it becomes help."'
    )
    _emotion(elder, "wisdom", 1)
    _emotion(hero, "shame", 0.5)
    _emotion(hero, "fairness", 0.5)


def turn(world: World, hero: Entity, helper: Entity, elder: Entity, tusk: Entity) -> None:
    world.para()
    if predict_sharing(world, hero):
        world.say(
            f"{hero.id} looked at the dry brook, then at the waiting baskets, and then at {helper.id}. "
            f"{hero.pronoun().capitalize()} took a breath and nodded."
        )
        world.say(
            f'"All right," said {hero.id}. "We will share {tusk.it()}."'
        )
        tusk.owner = "village"
        tusk.bearer = helper.id
        _emotion(hero, "fairness", 1)
        _emotion(hero, "warmth", 1)
        _emotion(helper, "gratitude", 1)
        _emotion(elder, "joy", 1)
        hero.memes["worry"] = 0.0


def resolution(world: World, hero: Entity, helper: Entity, elder: Entity, tusk: Entity) -> None:
    world.say(
        f"So {hero.id} and {helper.id} tied {tusk.it()} to a strong rope and used it as a handle for the water bucket. "
        f"The village filled its jars, and the people smiled as the brook sang again."
    )
    world.say(
        f"{hero.id} no longer had the tusk alone, but now everyone had the water, the thanks, and the good feeling that comes from sharing."
    )


def tell(params: StoryParams) -> World:
    village = _safe_lookup(VILLAGES, params.village)
    world = World(village)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    elder = world.add(Entity(id=params.elder_name, kind="character", type=params.elder_type))
    tusk = world.add(Entity(id="tusk", type="tusk", label="tusk", phrase="a long ivory tusk", owner=hero.id, bearer=hero.id))

    world.facts.update(hero=hero, helper=helper, elder=elder, tusk=tusk, village=village)

    introduce(world, hero, helper, elder, tusk)
    problem(world, hero, helper, elder, tusk)
    warning(world, elder, hero, helper, tusk)
    turn(world, hero, helper, elder, tusk)
    resolution(world, hero, helper, elder, tusk)
    return world


REGISTRY = {
    "brook": VILLAGES["brook"],
    "hill": VILLAGES["hill"],
    "oak": VILLAGES["oak"],
}

TUSK_FACTS = {
    "objectionable": "A tusk can be objectionable because it is big, hard, and not meant to be carried like a toy.",
    "sharing": "Sharing means letting other people use something so more than one person can benefit from it.",
    "moral value": "A moral value is a good rule for living, like kindness, fairness, or sharing.",
}


def asp_facts() -> str:
    import asp
    lines = []
    for vid, v in REGISTRY.items():
        lines.append(asp.fact("village", vid))
        lines.append(asp.fact("place", vid, v.place))
    lines.append(asp.fact("thing", "tusk"))
    lines.append(asp.fact("objectionable", "tusk"))
    lines.append(asp.fact("moral_value", "sharing"))
    lines.append(asp.fact("moral_value", "fairness"))
    lines.append(asp.fact("enables_help", "sharing", "village_water"))
    return "\n".join(lines)


ASP_RULES = r"""
% A thing is fit to share if it is objectionable to hoard but useful to many.
fit_to_share(T) :- objectionable(T), shared_use(T).

% Sharing is a moral value when it turns one thing into help for many.
good_choice(A) :- moral_value(sharing), shares(A, T), fit_to_share(T).

shared_use(tusk).
shares(hero, tusk).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    tusk = _safe_fact(world, f, "tusk")
    return [
        "Write a short folk tale about sharing something objectionable.",
        f"Tell a village story where {hero.id} learns to share {tusk.label} with {helper.id}.",
        "Write a gentle moral tale about fairness, a tusk, and helping the whole village.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, elder, tusk = f["hero"], f["helper"], f["elder"], f["tusk"]
    return [
        QAItem(
            question=f"What was the object that caused trouble in {world.village.name}?",
            answer=f"It was {tusk.phrase}. It was a little objectionable because it was awkward to carry, but it could still be useful.",
        ),
        QAItem(
            question=f"Why did {helper.id} want {tusk.it()}?",
            answer="The village needed help, and the tusk could become a strong handle for the water bucket.",
        ),
        QAItem(
            question=f"What did {elder.id} teach about the tusk?",
            answer=f"{elder.id} taught that a good thing to do was to share it, because sharing is a moral value that helps everyone.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt warm, fair, and proud in a kinder way, because sharing let the whole village benefit.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer=TUSK_FACTS["sharing"],
        ),
        QAItem(
            question="What is a moral value?",
            answer=TUSK_FACTS["moral value"],
        ),
        QAItem(
            question="Why might a tusk be objectionable?",
            answer=TUSK_FACTS["objectionable"],
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.owner:
            parts.append(f"owner={e.owner}")
        if e.bearer:
            parts.append(f"bearer={e.bearer}")
        if e.memes:
            parts.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {' '.join(parts)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about sharing a tusk.")
    ap.add_argument("--village", choices=REGISTRY.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--elder-name")
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
    village = getattr(args, "village", None) or rng.choice(list(REGISTRY.keys()))
    hero_type, _ = rng.choice(HEROES)
    helper_type, _ = rng.choice(HELPERS)
    elder_type, _ = rng.choice(ELDERS)
    hero_name = getattr(args, "hero_name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in NAMES if n != hero_name])
    elder_name = getattr(args, "elder_name", None) or rng.choice([n for n in NAMES if n not in {hero_name, helper_name}])
    if hero_name == helper_name or hero_name == elder_name or helper_name == elder_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        village=village,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show objectionable/1.\n#show moral_value/1."))
    atoms = set((s.name, tuple(a.string if a.type == a.type.String else a.name if a.type == a.type.Function else a.number for a in s.arguments)) for s in model)
    expected = {("objectionable", ("tusk",)), ("moral_value", ("sharing",)), ("moral_value", ("fairness",))}
    if atoms == expected:
        print("OK: ASP facts match the intended moral-value gate.")
        return 0
    print("MISMATCH:")
    print(" got:", sorted(atoms))
    print(" expected:", sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show objectionable/1.\n#show moral_value/1.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show objectionable/1.\n#show moral_value/1.\n"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for village in REGISTRY.keys():
            params = StoryParams(
                village=village,
                hero_name="Ari",
                hero_type="boy",
                helper_name="Mina",
                helper_type="girl",
                elder_name="Oren",
                elder_type="man",
            )
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
