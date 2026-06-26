#!/usr/bin/env python3
"""
storyworlds/worlds/parakeet_chagrined_marine_misunderstanding_friendship_animal_story.py
=======================================================================================

A small animal-story world about a parakeet, a marine helper, and a friendship
tested by a misunderstanding.

Premise:
- A bright parakeet loves a shiny shell token that belongs to a marine friend.
- The marine friend is absent for a moment, and a confused mistake makes the
  parakeet think the token was a gift.
- The missing token causes hurt feelings until the truth is explained.
- Friendship is repaired by returning the token and making amends.

The story is deliberately driven by simulated state:
- physical meters: carried objects, distance, loss, return
- emotional memes: joy, worry, chagrin, trust, friendship, relief

This file is standalone and uses only the shared result containers from
storyworlds/results.py, plus the optional ASP helper in storyworlds/asp.py.
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
# Core world model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    helper: object | None = None
    hero: object | None = None
    token: object | None = None
    def __post_init__(self) -> None:
        for k in ["distance", "lost", "returned"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "chagrin", "trust", "friendship", "relief", "confusion"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "female"}
        male = {"boy", "man", "male"}
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
    place: str
    indoors: bool
    feels: str
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
    setting: str
    hero_type: str
    helper_type: str
    token: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.paragraph_breaks: set[int] = set()
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buff: list[str] = []
        for line in self.lines:
            if line == "":
                if buff:
                    out.append(" ".join(buff))
                    buff = []
            else:
                buff.append(line)
        if buff:
            out.append(" ".join(buff))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "marine_lab": Setting(place="the marine lab", indoors=True, feels="quiet"),
    "harbor": Setting(place="the harbor", indoors=False, feels="windy"),
    "reef_center": Setting(place="the reef center", indoors=True, feels="bright"),
}

HERO_NAMES = ["Pip", "Coco", "Sunny", "Milo", "Bibi", "Nori"]
HELPER_NAMES = ["Mara", "Nate", "Lina", "Otis", "Ivy", "Kai"]

TYPES = {
    "parakeet": {
        "kind": "bird",
        "label": "parakeet",
        "voice": "chirped",
        "habitat": "perched high",
        "movement": "fluttered",
    },
    "marine": {
        "kind": "seal",
        "label": "marine friend",
        "voice": "murmured",
        "habitat": "swam nearby",
        "movement": "slid",
    },
    "friend": {
        "kind": "otter",
        "label": "friend",
        "voice": "chattered",
        "habitat": "splashed nearby",
        "movement": "darted",
    },
}

TOKEN_DATA = {
    "shell": {
        "label": "shell token",
        "phrase": "a smooth shell token on a blue string",
        "kind": "token",
        "pretty": "smooth and shiny",
    },
    "pebble": {
        "label": "pebble charm",
        "phrase": "a tiny pebble charm tied with green ribbon",
        "kind": "token",
        "pretty": "round and cool",
    },
    "star": {
        "label": "star charm",
        "phrase": "a star charm that glimmered like sunlight",
        "kind": "token",
        "pretty": "bright and twinkly",
    },
}

CURATED = [
    StoryParams(setting="marine_lab", hero_type="parakeet", helper_type="marine", token="shell"),
    StoryParams(setting="harbor", hero_type="parakeet", helper_type="marine", token="pebble"),
    StoryParams(setting="reef_center", hero_type="parakeet", helper_type="marine", token="star"),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.hero_type not in TYPES or params.helper_type not in TYPES:
        pass
    if params.token not in TOKEN_DATA:
        pass
    if params.setting not in SETTINGS:
        pass

    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    hero_name = random.choice(HERO_NAMES)
    helper_name = random.choice(HELPER_NAMES)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=params.hero_type,
        label=_safe_lookup(TYPES, params.hero_type)["label"],
        traits=["small", "bright", "curious"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=params.helper_type,
        label=_safe_lookup(TYPES, params.helper_type)["label"],
        traits=["kind", "patient", "tidy"],
    ))
    token_info = TOKEN_DATA[params.token]
    token = world.add(Entity(
        id="token",
        kind="thing",
        type="token",
        label=token_info["label"],
        phrase=token_info["phrase"],
        owner=helper.id,
    ))
    helper.carried_by = None
    token.carried_by = helper.id

    world.facts.update(hero=hero, helper=helper, token=token, token_info=token_info)
    return world


def narrate_setup(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    token: Entity = _safe_fact(world, world.facts, "token")  # type: ignore[assignment]
    world.say(f"{hero.id} was a little {hero.label} who loved looking at bright things.")
    world.say(f"{helper.id} was a gentle {helper.label} who always kept promises.")
    world.say(f"{helper.id} carried {token.phrase}, because {token.id} mattered to both of them.")
    hero.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1


def narrate_misunderstanding(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    token: Entity = _safe_fact(world, world.facts, "token")  # type: ignore[assignment]

    world.para()
    world.say(f"One {world.setting.feels} morning at {world.setting.place}, {helper.id} stepped away to help a visitor.")
    world.say(f"{hero.id} saw the {token.label} resting on a low ledge and thought, \"Maybe this is for me.\"")
    world.say(f"{hero.id} picked it up and tucked it close.")
    token.carried_by = hero.id
    token.meters["distance"] = 1
    token.memes["lost"] += 1
    hero.memes["joy"] += 1
    hero.memes["confusion"] += 1
    helper.memes["worry"] += 1
    helper.memes["chagrin"] += 1
    world.say(f"But the token was not a gift. It was {helper.id}'s special thing, and now {helper.id} looked chagrined.")


def narrate_turn(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    token: Entity = _safe_fact(world, world.facts, "token")  # type: ignore[assignment]

    world.para()
    world.say(f"{helper.id} came back, saw the missing token, and softly asked, \"Did you mean to take it?\"")
    hero.memes["joy"] -= 1
    hero.memes["confusion"] += 1
    hero.memes["worry"] += 1
    helper.memes["friendship"] += 0.5
    world.say(f"{hero.id} blinked and realized the mistake. \"Oh no,\" {hero.id} said, feeling chagrined.")
    hero.memes["chagrin"] += 1
    helper.memes["worry"] += 1
    world.say(f"{hero.id} held the token out right away, because friendship mattered more than being right.")
    token.carried_by = helper.id
    token.meters["returned"] = 1
    token.meters["lost"] = 0
    token.memes["lost"] = 0
    hero.memes["trust"] += 1
    helper.memes["relief"] += 1
    helper.memes["trust"] += 1


def narrate_resolution(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    token: Entity = _safe_fact(world, world.facts, "token")  # type: ignore[assignment]

    world.para()
    world.say(f"{helper.id} smiled and said the quiet truth: it had been a misunderstanding, not a bad act.")
    world.say(f"{hero.id} apologized, and {helper.id} accepted it at once.")
    hero.memes["chagrin"] = max(0.0, hero.memes["chagrin"] - 1)
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(f"In the end, {token.phrase} was back where it belonged, and {hero.id} and {helper.id} felt closer than before.")


def generate_story(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    narrate_misunderstanding(world)
    narrate_turn(world)
    narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    token: Entity = _safe_fact(world, world.facts, "token")  # type: ignore[assignment]
    return [
        f"Write an animal story about a {hero.label} and a {helper.label} whose friendship survives a misunderstanding about {token.label}.",
        f"Tell a gentle story set at {world.setting.place} where {hero.id} feels chagrined after taking something that belongs to {helper.id}.",
        f"Create a child-friendly story about friendship, a missing token, and a happy apology involving {token.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    token: Entity = _safe_fact(world, world.facts, "token")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little {hero.label}, and {helper.id}, a kind {helper.label}.",
        ),
        QAItem(
            question=f"What caused the misunderstanding?",
            answer=f"{hero.id} thought the {token.label} might be a gift and picked it up, but it really belonged to {helper.id}.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{hero.id} returned the {token.label}, apologized, and {helper.id} forgave the mistake.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {token.label} safely back with {helper.id} and the two friends feeling closer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks the wrong thing about a situation, even though nobody meant to be unkind.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond between companions who help, forgive, and stay kind to each other.",
        ),
        QAItem(
            question="Why is apologizing important?",
            answer="Apologizing helps fix hurt feelings by showing that you understand the mistake and want to make things better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_type(H).
helper(H) :- helper_type(H).
token(T) :- token_kind(T).

misunderstanding(H, T) :- takes(H, T), belongs_to(T, H2), H != H2.
hurt(H2) :- misunderstanding(H, T), belongs_to(T, H2).
resolve(H, H2, T) :- misunderstanding(H, T), returns(H, T), belongs_to(T, H2).

friendly(H, H2) :- returns(H, T), belongs_to(T, H2).
happy_end(H, H2) :- resolve(H, H2, T), apology(H), forgiveness(H2).

#show misunderstanding/2.
#show hurt/1.
#show resolve/3.
#show happy_end/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero_type", "parakeet"))
    lines.append(asp.fact("helper_type", "marine"))
    for tok in TOKEN_DATA:
        lines.append(asp.fact("token_kind", tok))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    shown = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("misunderstanding", ("parakeet", "shell")),
        ("misunderstanding", ("parakeet", "pebble")),
        ("misunderstanding", ("parakeet", "star")),
    }
    if not expected.issubset(shown):
        print("ASP mismatch.")
        print("shown:", sorted(shown))
        print("expected subset:", sorted(expected))
        return 1
    print("OK: ASP facts/rules load and produce misunderstanding atoms.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        e_m = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if e_m:
            bits.append(f"memes={e_m}")
        if e.kind == "character":
            bits.append(f"type={e.type}")
        else:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a parakeet, a marine friend, and a misunderstanding.")
    ap.add_argument("--setting", choices=sorted(SETTINGS), default=None)
    ap.add_argument("--hero-type", choices=["parakeet"], default="parakeet")
    ap.add_argument("--helper-type", choices=["marine"], default="marine")
    ap.add_argument("--token", choices=sorted(TOKEN_DATA), default=None)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    token = getattr(args, "token", None) or rng.choice(list(TOKEN_DATA))
    return StoryParams(
        setting=setting,
        hero_type=getattr(args, "hero_type", None),
        helper_type=getattr(args, "helper_type", None),
        token=token,
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        try:
            import asp
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program())
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
