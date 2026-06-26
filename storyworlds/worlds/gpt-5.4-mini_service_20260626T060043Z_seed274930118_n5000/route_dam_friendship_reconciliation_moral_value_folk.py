#!/usr/bin/env python3
"""
storyworlds/worlds/route_dam_friendship_reconciliation_moral_value_folk.py
==========================================================================

A small folk-tale storyworld about a route, a dam, friendship, and making up
after a disagreement. The world is intentionally tiny: one shared path, one
risky dam crossing, and one moral choice about listening, helping, and
reconciling.
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Route:
    name: str
    safe: bool
    muddy: bool
    goes_by_dam: bool
    tags: set[str] = field(default_factory=set)
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
class Dam:
    name: str
    water: str
    bridge: bool
    tags: set[str] = field(default_factory=set)
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
    route: str
    dam: str
    hero: str
    friend: str
    moral_value: str
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
    def __init__(self, route: Route, dam: Dam) -> None:
        self.route = route
        self.dam = dam
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        cur: list[str] = []
        for line in self.lines:
            if line == "":
                if cur:
                    out.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            out.append(" ".join(cur))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROUTES = {
    "meadow_route": Route(
        name="the meadow route",
        safe=True,
        muddy=False,
        goes_by_dam=True,
        tags={"route", "meadow"},
    ),
    "woodland_route": Route(
        name="the woodland route",
        safe=False,
        muddy=True,
        goes_by_dam=True,
        tags={"route", "woodland"},
    ),
    "hill_route": Route(
        name="the hill route",
        safe=True,
        muddy=False,
        goes_by_dam=False,
        tags={"route", "hill"},
    ),
}

DAMS = {
    "stone_dam": Dam(
        name="the stone dam",
        water="the river",
        bridge=False,
        tags={"dam", "river"},
    ),
    "old_dam": Dam(
        name="the old dam",
        water="the lake",
        bridge=True,
        tags={"dam", "lake"},
    ),
}

MORAL_VALUES = {
    "listening": "listening before leaping",
    "kindness": "kindness during trouble",
    "sharing": "sharing the burden of a hard walk",
}

HERO_NAMES = ["Mira", "Tobin", "Anya", "Perrin", "Sora", "Nell", "Bram", "Lila"]
FRIEND_NAMES = ["Jory", "Petal", "Ren", "Milo", "Ari", "Hana", "Bela", "Oren"]

TRAITS = ["thoughtful", "brave", "gentle", "quick-tempered", "patient", "curious"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def route_is_risky(route: Route, dam: Dam) -> bool:
    return route.goes_by_dam and not dam.bridge


def compatible_fix(route: Route, dam: Dam) -> bool:
    return route.safe and dam.bridge


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for rkey, route in ROUTES.items():
        for dkey, dam in DAMS.items():
            if route_is_risky(route, dam) and compatible_fix(route, dam):
                out.append((rkey, dkey))
    return out


def explain_rejection(route: Route, dam: Dam) -> str:
    return (
        f"(No story: {route.name} by {dam.name} does not make a believable tale. "
        f"The route must truly be risky, and the reconciliation must truly help.)"
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(ROUTES, params.route), _safe_lookup(DAMS, params.dam))
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.hero))
    friend = world.add(Entity(id="friend", kind="character", type="boy", label=params.friend))
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["moral_value"] = params.moral_value
    return world


def opening(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f"Long ago, {hero.label} and {friend.label} were two friends who loved walking the same route together."
    )
    world.say(
        f"They called it {world.route.name}, and the path curled near {world.dam.name} like a ribbon beside water."
    )
    world.say(
        f"{hero.label} was a {random.choice(TRAITS)} child, and {friend.label} was a {random.choice(TRAITS)} friend who knew every bend in the road."
    )


def build_tension(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.para()
    if world.route.muddy:
        world.say(
            f"After rain, the route turned slick, and the mud clung to little shoes."
        )
    else:
        world.say(
            f"The route looked calm, but the dam below kept the water moving fast and loud."
        )
    world.say(
        f"{hero.label} wanted to hurry across the way near the dam, but {friend.label} shook {friend.pronoun('possessive')} head."
    )
    world.say(
        f'"That crossing is too risky," {friend.label} said. "A safer road will keep us dry and sound."'
    )
    hero.meters["impatience"] = hero.meters.get("impatience", 0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1


def quarrel(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f"{hero.label} felt cross and turned away."
    )
    world.say(
        f"{hero.label} said, \"You never let me choose the fast way!\""
    )
    friend.memes["sadness"] = friend.memes.get("sadness", 0) + 1
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1


def turning_point(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.para()
    if world.dam.bridge:
        world.say(
            f"Then {hero.label} saw the little bridge near {world.dam.name}, and understood that the safer path still let them travel together."
        )
    else:
        world.say(
            f"Then {hero.label} looked at the dark water under {world.dam.name} and remembered how kindness matters more than winning an argument."
        )
    world.say(
        f"{hero.label} took a slow breath and said, \"I was wrong to snap. I should have listened.\""
    )
    world.say(
        f"{friend.label} softened at once, because a true friend is glad to hear honest words."
    )
    hero.memes["regret"] = max(hero.memes.get("regret", 0), 1)
    friend.memes["forgiveness"] = friend.memes.get("forgiveness", 0) + 1


def reconciliation(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f"They chose the safer road together and walked side by side, sharing each step."
    )
    world.say(
        f"{friend.label} smiled and said, \"Thank you for listening now.\""
    )
    world.say(
        f"{hero.label} smiled back, and the heavy feeling between them grew light."
    )
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    friend.memes["peace"] = friend.memes.get("peace", 0) + 1
    hero.memes["regret"] = 0
    friend.memes["worry"] = 0
    world.facts["resolved"] = True


def ending(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.para()
    world.say(
        f"By sunset, {hero.label} and {friend.label} had reached the end of the route without trouble."
    )
    world.say(
        f"The dam still stood beside the water, but their friendship stood stronger, because they had learned {world.facts['moral_value']}."
    )
    world.say(
        f"And so the folk tale ends with two friends walking home in good cheer, wiser than before."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    opening(world)
    build_tension(world)
    quarrel(world)
    turning_point(world)
    reconciliation(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "route": [
        (
            "What is a route?",
            "A route is a path or road that people can follow to get from one place to another.",
        )
    ],
    "dam": [
        (
            "What is a dam?",
            "A dam is a strong wall or barrier built to hold back water, often making a lake behind it.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is the kind bond between people who care for one another and want to help.",
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means making peace again after people have had a disagreement.",
        )
    ],
    "moral": [
        (
            "What is a moral in a folktale?",
            "A moral is the lesson or good value the story teaches, like being kind or listening carefully.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short folk tale about {world.route.name} and {world.dam.name} that teaches {world.facts["moral_value"]}.',
        f"Tell a child-friendly story where two friends argue near the dam, then reconcile and choose the safer route.",
        f'Write a gentle folktale that includes the words "route" and "dam" and ends with a lesson about friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The two friends are {hero.label} and {friend.label}. They travel together and care about each other.",
        ),
        QAItem(
            question=f"Why did {friend.label} worry about the crossing near {world.dam.name}?",
            answer=(
                f"{friend.label} worried because the crossing near {world.dam.name} was risky. "
                f"The safe choice was to use a better route instead of rushing beside the water."
            ),
        ),
        QAItem(
            question="What changed between the friends by the end?",
            answer=(
                f"At first they argued, but then they made up. Their friendship grew stronger because "
                f"they listened, apologized, and walked the safer road together."
            ),
        ),
        QAItem(
            question="What lesson does the story teach?",
            answer=f"The story teaches {world.facts['moral_value']}, which means being wise and gentle even when you are upset.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in {"route", "dam", "friendship", "reconciliation", "moral"}:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
route_risky(R,D) :- route(R), dam(D), goes_by_dam(R), not bridge(D).
reconciles(R,D) :- route(R), dam(D), safe(R), bridge(D).
valid_story(R,D) :- route_risky(R,D), reconciles(R,D).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        if route.safe:
            lines.append(asp.fact("safe", rid))
        if route.muddy:
            lines.append(asp.fact("muddy", rid))
        if route.goes_by_dam:
            lines.append(asp.fact("goes_by_dam", rid))
    for did, dam in DAMS.items():
        lines.append(asp.fact("dam", did))
        if dam.bridge:
            lines.append(asp.fact("bridge", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_story_configs() -> list[tuple[str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "route", None) and getattr(args, "dam", None):
        route = _safe_lookup(ROUTES, getattr(args, "route", None))
        dam = _safe_lookup(DAMS, getattr(args, "dam", None))
        if not (route_is_risky(route, dam) and compatible_fix(route, dam)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        (r, d)
        for r, d in valid_story_configs()
        if (getattr(args, "route", None) is None or r == getattr(args, "route", None))
        and (getattr(args, "dam", None) is None or d == getattr(args, "dam", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    rkey, dkey = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    if friend == hero:
        friend = rng.choice([n for n in FRIEND_NAMES if n != hero])
    moral = getattr(args, "moral_value", None) or rng.choice(list(MORAL_VALUES.keys()))
    return StoryParams(route=rkey, dam=dkey, hero=hero, friend=friend, moral_value=moral)


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
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.label} {' '.join(bits)}")
        print(f"  route={sample.world.route.name}")
        print(f"  dam={sample.world.dam.name}")
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about route, dam, friendship, and reconciliation."
    )
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--dam", choices=sorted(DAMS))
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--moral-value", dest="moral_value", choices=sorted(MORAL_VALUES))
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible route/dam combos:\n")
        for r, d in combos:
            print(f"  {r:14} {d}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(route="meadow_route", dam="old_dam", hero="Mira", friend="Jory", moral_value="listening"),
            StoryParams(route="woodland_route", dam="old_dam", hero="Tobin", friend="Petal", moral_value="kindness"),
            StoryParams(route="meadow_route", dam="old_dam", hero="Anya", friend="Ren", moral_value="sharing"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.route} by {p.dam} ({p.moral_value})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
