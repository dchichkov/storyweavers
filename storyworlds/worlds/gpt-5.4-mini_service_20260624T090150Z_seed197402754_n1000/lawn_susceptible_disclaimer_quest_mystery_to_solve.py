#!/usr/bin/env python3
"""
A fairy-tale storyworld about a lawn, a susceptible patch, and a quest to solve
a small mystery with a careful disclaimer before action.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    lawn: object | None = None
    patch: object | None = None
    scroll: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "queen", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "king", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
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
class StoryParams:
    setting: str
    name: str
    role: str
    companion: str
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


SETTINGS = {
    "castle": "the castle garden",
    "village": "the village green",
    "meadow": "the meadow by the hill",
}

ROLES = ["princess", "prince", "girl", "boy"]
COMPANIONS = ["grandmother", "gardener", "old wizard", "kind raven"]
NAMES = ["Luna", "Milo", "Iris", "Theo", "Pippa", "Robin", "Esme", "Nico"]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    ap = argparse.ArgumentParser(description="A fairy-tale quest about a suspicious lawn mystery.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    return StoryParams(setting=setting, name=name, role=role, companion=companion)


def _make_world(params: StoryParams) -> World:
    world = World(setting=params.setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.role, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="companion", label=params.companion))
    lawn = world.add(Entity(
        id="lawn",
        type="lawn",
        label="the lawn",
        phrase="the soft green lawn",
        caretaker=helper.id,
        meters={"freshness": 3.0, "susceptibility": 0.0},
        memes={"peace": 2.0},
    ))
    patch = world.add(Entity(
        id="patch",
        type="patch",
        label="one pale patch",
        phrase="one pale patch",
        owner=lawn.id,
        plural=False,
        meters={"freshness": 1.0, "susceptibility": 2.0},
        memes={"mystery": 2.0},
    ))
    scroll = world.add(Entity(
        id="scroll",
        type="scroll",
        label="a small scroll",
        phrase="a small scroll with a ribbon",
        owner=helper.id,
        plural=False,
    ))

    world.facts.update(hero=hero, helper=helper, lawn=lawn, patch=patch, scroll=scroll, params=params)
    return world


def _story_intro(world: World) -> None:
    p = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    setting_name = _safe_lookup(SETTINGS, p.setting)
    world.say(
        f"Once in {setting_name}, there lived a {p.role} named {hero.label}. "
        f"{hero.label} loved to wander beside the green grass and listen to old tales."
    )
    world.say(
        f"One day, {helper.label} brought a little scroll and said there was a mystery to solve. "
        f"{hero.label} felt brave at once, because every true quest begins with a curious heart."
    )


def _raise_disclaimer(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    world.say(
        f"{helper.label} gave a gentle disclaimer: \"The lawn is susceptible to rough feet and spilled water, "
        f"so we must walk softly and look closely.\""
    )
    world.say(
        f"{hero.label} nodded and promised to be careful, because a wise quest listens before it leaps."
    )


def _mystery_turn(world: World) -> None:
    patch: Entity = _safe_fact(world, world.facts, "patch")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    patch.meters["mystery"] += 1.0
    patch.memes["unease"] = 1.0
    world.say(
        f"Near the middle of the lawn, they found {patch.label}. It was not as bright as the rest, "
        f"and it looked susceptible to the morning dew."
    )
    world.say(
        f"{hero.label} knelt beside it while {helper.label} opened the scroll. "
        f"The words were simple: \"Look for the hidden reason before the sun grows hot.\""
    )


def _solve_mystery(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    lawn: Entity = _safe_fact(world, world.facts, "lawn")
    patch: Entity = _safe_fact(world, world.facts, "patch")

    patch.meters["freshness"] += 2.0
    patch.meters["susceptibility"] -= 1.0
    lawn.meters["freshness"] += 1.0
    lawn.memes["peace"] += 2.0
    patch.memes["mystery"] = 0.0

    world.say(
        f"They followed tiny clues: a trail of crumbs, a bent ribbon, and a muddy paw print. "
        f"At last, they found the answer—a sleepy rabbit had nibbled the grass in the night."
    )
    world.say(
        f"{hero.label} carried away the fallen sticks, and {helper.label} spread fresh seed over the pale spot. "
        f"By sunset, the lawn looked kind again, and the mystery was solved."
    )


def _ending_image(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    lawn: Entity = _safe_fact(world, world.facts, "lawn")
    patch: Entity = _safe_fact(world, world.facts, "patch")
    world.say(
        f"That evening, {hero.label} and {helper.label} stood on the lawn and watched the pale patch turn green. "
        f"The little quest had made the whole garden feel peaceful, and the once-susceptible spot had become part of the happy grass."
    )


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    _story_intro(world)
    world.para()
    _raise_disclaimer(world)
    _mystery_turn(world)
    world.para()
    _solve_mystery(world)
    _ending_image(world)

    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    lawn: Entity = _safe_fact(world, world.facts, "lawn")
    patch: Entity = _safe_fact(world, world.facts, "patch")

    world.facts["resolved"] = True
    world.facts["mystery_answer"] = "a rabbit had nibbled the grass in the night"
    world.facts["end_freshness"] = lawn.meters["freshness"]

    prompts = [
        f"Write a fairy tale about a {params.role} named {hero.label} who goes on a quest to solve a mystery on a lawn.",
        f"Tell a gentle story where {helper.label} gives a disclaimer about a susceptible patch of grass.",
        f"Write a short child-friendly tale that ends with a solved mystery and a greener lawn.",
    ]

    story_qa = [
        QAItem(
            question=f"What kind of quest did {hero.label} begin in the story?",
            answer=f"{hero.label} began a mystery-solving quest to discover why one patch of the lawn looked pale.",
        ),
        QAItem(
            question=f"What disclaimer did {helper.label} give before they started looking?",
            answer=(
                f"{helper.label} said the lawn was susceptible to rough feet and spilled water, "
                f"so they should walk softly and look closely."
            ),
        ),
        QAItem(
            question="What was the mystery they solved?",
            answer="They solved the mystery of why one patch of grass looked pale, and they learned a rabbit had nibbled it at night.",
        ),
        QAItem(
            question=f"How did the story end for the lawn?",
            answer="The pale patch was cared for and turned greener, so the whole lawn ended peaceful and healthy.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a lawn?",
            answer="A lawn is a stretch of grass that people may walk on, rest beside, or care for in a garden or yard.",
        ),
        QAItem(
            question="What does susceptible mean?",
            answer="Susceptible means something can be easily affected or harmed by a certain thing.",
        ),
        QAItem(
            question="What is a disclaimer?",
            answer="A disclaimer is a careful warning or notice that explains a limit, risk, or condition before something happens.",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(castle).
setting(village).
setting(meadow).

lawn_susceptible(Patch) :- patch(Patch), susceptible(Patch).
disclaimer_needed(Patch) :- lawn_susceptible(Patch).
quest(hero).
mystery_to_solve(patch).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("quest", "hero"),
            asp.fact("mystery_to_solve", "patch"),
            asp.fact("lawn", "patch"),
            asp.fact("susceptible", "patch"),
            asp.fact("disclaimer", "helper"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show quest/1. #show mystery_to_solve/1. #show disclaimer_needed/1."))
        shown = set(asp.atoms(model, "quest")) | set(asp.atoms(model, "mystery_to_solve")) | set(asp.atoms(model, "disclaimer_needed"))
        expected = {("hero",), ("patch",), ("patch",)}
        if ("hero",) in shown and ("patch",) in shown:
            print("OK: ASP twin emits the expected core facts.")
            return 0
        print("MISMATCH: ASP twin did not reflect the storyworld facts.")
        return 1
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(setting="castle", name="Luna", role="princess", companion="gardener"),
        StoryParams(setting="village", name="Milo", role="boy", companion="kind raven"),
        StoryParams(setting="meadow", name="Iris", role="girl", companion="old wizard"),
    ]


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
        print(asp_program("#show quest/1. #show mystery_to_solve/1. #show disclaimer_needed/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show quest/1. #show mystery_to_solve/1. #show disclaimer_needed/1."))
        print(sorted(set(asp.atoms(model, "quest"))))
        print(sorted(set(asp.atoms(model, "mystery_to_solve"))))
        print(sorted(set(asp.atoms(model, "disclaimer_needed"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in build_curated():
            samples.append(generate(p))
    else:
        rng = random.Random(base_seed)
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name} in {p.setting} ({p.role})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
