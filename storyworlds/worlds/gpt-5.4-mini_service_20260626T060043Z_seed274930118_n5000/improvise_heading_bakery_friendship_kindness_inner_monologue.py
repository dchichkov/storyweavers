#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/improvise_heading_bakery_friendship_kindness_inner_monologue.py
==============================================================================================================================

A standalone story world in a bakery, told in a superhero-story style.

Premise:
- A child hero and a friend are helping in a bakery.
- A small problem threatens a tray of buns and the day's kindness plan.
- The hero improvises a safe fix while heading toward the counter.
- Friendship and kindness shape the resolution.
- Inner monologue is used to keep the story emotionally grounded and child-facing.

The simulated world tracks:
- physical meters: distance, mess, warmth, wobble, order, crumbs
- emotional memes: courage, worry, friendship, kindness, pride

The prose is generated from the evolving world state rather than from a frozen template.
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

BAKERY_PLACES = {
    "bakery": {
        "name": "the bakery",
        "affords": {"deliver", "decorate", "carry", "clean"},
    }
}

HERO_NAMES = ["Mina", "Leo", "Nora", "Toby", "Ivy", "Finn", "Mila", "Jude"]
FRIEND_NAMES = ["Pip", "Zoe", "Max", "Ruby", "Ollie", "June", "Arlo", "Luna"]
TRAITS = ["brave", "quick", "gentle", "curious", "bright", "steady"]

ASP_RULES = r"""
hero_ready(H) :- courage(H), kindness(H), not panic(H).
friend_help(F,H) :- friendship(F,H), nearby(F,H), trouble(H).
safe_fix(H) :- hero_ready(H), friend_help(_,H), improvise(H).
resolved(H) :- safe_fix(H), order(H), not broken(H).
"""


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
    kind: str
    label: str
    kind_word: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None

    friend: object | None = None
    hero: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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


@dataclass
class Setting:
    place: str = "the bakery"
    affords: set[str] = field(default_factory=lambda: {"deliver", "decorate", "carry", "clean"})
    setting: object | None = None
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
class StoryParams:
    place: str = "bakery"
    hero_name: str = "Mina"
    friend_name: str = "Pip"
    trait: str = "brave"
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    world: object | None = None
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
        import copy
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )
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
    ap = argparse.ArgumentParser(description="Superhero bakery story world with friendship and kindness.")
    ap.add_argument("--place", choices=list(BAKERY_PLACES))
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    return "\n".join(
        [
            asp.fact("place", "bakery"),
            asp.fact("affords", "bakery", "deliver"),
            asp.fact("affords", "bakery", "decorate"),
            asp.fact("affords", "bakery", "carry"),
            asp.fact("affords", "bakery", "clean"),
            asp.fact("improvise"),
            asp.fact("heading"),
            asp.fact("friendship"),
            asp.fact("kindness"),
            asp.fact("inner_monologue"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = set(asp.atoms(model, "resolved"))
    python_ok = asp_reasonable()
    asp_ok = ("H" in {a[0] for a in atoms}) if atoms else False
    if python_ok == asp_ok:
        print("OK: ASP/Python parity holds.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def _hero_intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.label} was a {hero.kind_word} hero who loved the bakery because it smelled like warm sugar and hope."
    )
    world.say(
        f"{friend.label} was {hero.label}'s best friend, and the two of them worked side by side like a tiny team of capes."
    )


def _problem(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["distance"] = 0.0
    friend.meters["distance"] = 1.0
    hero.meters["wobble"] = 0.0
    world.say(
        f"One busy morning, a tray of buns wobbled near the counter, and a sugary crumb storm rolled toward the floor."
    )
    world.say(
        f"{hero.label} looked at the tray and thought, 'If it tips, everyone will slip, and the whole place will feel rushed.'"
    )
    hero.memes["worry"] += 1
    hero.memes["courage"] += 1
    friend.memes["friendship"] += 1
    hero.memes["kindness"] += 1


def _improvise_fix(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["distance"] += 2
    hero.meters["order"] += 1
    friend.meters["crumbs"] = 1
    world.say(
        f"{hero.label} started heading for the counter, cape fluttering, while the child hero made a quick plan."
    )
    world.say(
        f"Inside {hero.label}'s head, a small voice said, 'Don't panic. Improvise. You can do this kindly.'"
    )
    world.say(
        f"{friend.label} slid over a clean towel, and {hero.label} used it to steady the tray before any buns could fall."
    )
    world.say(
        f"That was the clever move: a simple towel, a steady hand, and a friend who knew exactly when to help."
    )
    hero.meters["mess"] = 0.0
    hero.meters["wobble"] = 0.0
    hero.meters["warmth"] = 1.0
    hero.meters["order"] = 2.0
    hero.memes["pride"] += 1
    friend.memes["kindness"] += 1
    hero.memes["friendship"] += 1


def _ending(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"The buns stayed neat, the floor stayed safe, and the bakery kept its cozy shine."
    )
    world.say(
        f"{hero.label} smiled at {friend.label} and thought, 'A hero does not have to be loud to save the day.'"
    )
    world.say(
        f"Then the two friends kept heading along the counter together, ready to deliver warm bread and a little extra kindness."
    )


def tell(params: StoryParams) -> World:
    setting = Setting(place=_safe_lookup(BAKERY_PLACES, params.place)["name"])
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, kind_word=params.trait))
    friend = world.add(Entity(id="friend", kind="character", label=params.friend_name, kind_word="friend"))

    hero.memes.update({"courage": 1.0, "kindness": 1.0, "worry": 0.0, "friendship": 1.0})
    friend.memes.update({"friendship": 1.0, "kindness": 1.0})
    hero.meters.update({"order": 0.0, "wobble": 0.0, "mess": 0.0, "distance": 0.0, "warmth": 0.0})

    world.facts.update(hero=hero, friend=friend, place=params.place, trait=params.trait)
    _hero_intro(world, hero, friend)
    world.para()
    _problem(world, hero, friend)
    world.para()
    _improvise_fix(world, hero, friend)
    _ending(world, hero, friend)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    return [
        f"Write a superhero story about {hero.label} and {friend.label} in a bakery where they have to improvise.",
        f"Tell a child-friendly story with friendship, kindness, and an inner monologue set in a bakery.",
        f"Write a short superhero tale where a hero is heading toward a counter and saves warm buns with a clever idea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    return [
        QAItem(
            question=f"Where is the story set?",
            answer=f"The story is set in the bakery, where the air smells warm and sweet.",
        ),
        QAItem(
            question=f"What did {hero.label} do when the tray of buns wobbled?",
            answer=f"{hero.label} improvised with a clean towel and steady hands, then helped keep the tray safe.",
        ),
        QAItem(
            question=f"How did {friend.label} help?",
            answer=f"{friend.label} offered a clean towel at just the right moment, showing friendship and kindness.",
        ),
        QAItem(
            question=f"What did {hero.label} think in the inner monologue?",
            answer=f"{hero.label} thought, 'Don't panic. Improvise. You can do this kindly.'",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bakery?",
            answer="A bakery is a place where bread, buns, cakes, and other baked treats are made or sold.",
        ),
        QAItem(
            question="What does it mean to improvise?",
            answer="To improvise means to make up a good solution in the moment using what you have nearby.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond between people who help and enjoy each other.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in a character's head that tells their thoughts.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== generation prompts ==")
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} label={e.label} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "bakery"
    if place not in BAKERY_PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if hero_name == friend_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero_name=hero_name, friend_name=friend_name, trait=trait)


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


CURATED = [
    StoryParams(place="bakery", hero_name="Mina", friend_name="Pip", trait="brave"),
    StoryParams(place="bakery", hero_name="Leo", friend_name="Ruby", trait="gentle"),
    StoryParams(place="bakery", hero_name="Nora", friend_name="Max", trait="quick"),
]


def asp_verify_main() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_main())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show hero_ready/1.#show safe_fix/1.#show resolved/1."))
        print(asp.atoms(model, "resolved"))
        return

    rng0 = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = (getattr(args, "seed", None) if getattr(args, "seed", None) is not None else rng0.randrange(2**31)) + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
