#!/usr/bin/env python3
"""
Story world: profile humor reconciliation heartwarming.

A small, self-contained story simulation about a child, a profile picture, a
small misunderstanding, and a warm funny apology that ends in a shared smile.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    friend: object | None = None
    hero: object | None = None
    prop: object | None = None
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


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
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
class Prop:
    id: str
    label: str
    phrase: str
    mess: str
    kind: str
    required: set[str] = field(default_factory=set)
    joke: str = ""
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
    setting: str
    prop: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

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

SETTINGS = {
    "classroom": Setting("the classroom", {"profile", "paint"}),
    "library": Setting("the library corner", {"profile"}),
    "hallway": Setting("the hallway bulletin board", {"profile"}),
}

PROPS = {
    "hat": Prop(
        id="hat",
        label="silly hat",
        phrase="a bright silly hat with a tiny feather",
        mess="crooked",
        kind="prop",
        required={"profile"},
        joke="It looked so fancy that even the feather seemed proud.",
    ),
    "glasses": Prop(
        id="glasses",
        label="huge glasses",
        phrase="huge pretend glasses",
        mess="squinty",
        kind="prop",
        required={"profile"},
        joke="They made everybody look like a tiny librarian owl.",
    ),
    "sticker": Prop(
        id="sticker",
        label="star sticker",
        phrase="a shiny star sticker",
        mess="sparkly",
        kind="prop",
        required={"profile"},
        joke="It stuck so well that it seemed determined to become part of the story.",
    ),
}

HERO_NAMES = ["Mia", "Noah", "Luna", "Eli", "Ivy", "Theo", "Ava", "Ben"]
FRIEND_NAMES = ["Pip", "Jun", "Ruby", "Max", "Zoe", "Milo", "Nina", "Kai"]

TRAITS = ["playful", "shy", "curious", "silly", "gentle", "bright"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_ok(S) :- setting(S).
prop_ok(P) :- prop(P).

compatible(S,P) :- setting_ok(S), prop_ok(P), setting_affords(S, profile), prop_requires(P, profile).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_affords", sid, a))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for r in sorted(p.required):
            lines.append(asp.fact("prop_requires", pid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PROPS if "profile" in _safe_lookup(SETTINGS, s).affords and "profile" in _safe_lookup(PROPS, p).required]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python only:", sorted(py - cl))
    print(" asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={"joy": 0.0}, memes={"worry": 0.0}))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type, meters={"joy": 0.0}, memes={"hurt": 0.0}))
    prop = world.add(Entity(id="prop", type="prop", label=_safe_lookup(PROPS, params.prop).label, phrase=_safe_lookup(PROPS, params.prop).phrase, owner=hero.id))

    world.facts.update(hero=hero, friend=friend, prop=prop, setting=params.setting, prop_id=params.prop)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero = world.get(params.hero_name)
    friend = world.get(params.friend_name)
    prop = world.get("prop")
    prop_def = _safe_lookup(PROPS, params.prop)

    world.say(f"{hero.id} was a {random.choice(TRAITS)} {hero.type} who wanted a nice profile picture.")
    world.say(f"{hero.pronoun('possessive').capitalize()} favorite part was the funny {prop.label}: {prop.joke}")
    world.say(f"At {world.setting.place}, {hero.id} and {friend.id} sat by the board where pictures could be shared.")

    world.para()
    hero.memes["worry"] += 1
    world.say(f"{hero.id} wanted the picture to look just right, but the first try came out a little crooked.")
    world.say(f"{friend.id} laughed, not meanly, just in surprise. Still, it made {hero.id} feel small.")
    friend.memes["hurt"] += 1
    world.say(f"{hero.id} crossed {hero.pronoun('possessive')} arms and said, \"I was trying to make it cute!\"")

    world.para()
    hero.meters["pause"] = 1
    if prop_def.id == "hat":
        world.say(f"Then {hero.id} tilted the silly hat even farther on purpose, and that was so funny that {friend.id} snorted.")
    elif prop_def.id == "glasses":
        world.say(f"Then {hero.id} pushed up the huge glasses and made a serious owl face, which was too funny to stay upset about.")
    else:
        world.say(f"Then {hero.id} held up the star sticker and said, \"Maybe the profile needs one more sparkle and one less grumpy face.\"")

    world.say(f"{friend.id} blinked, then smiled because {hero.id} was being funny on purpose instead of being mad back.")

    world.para()
    hero.memes["joy"] += 2
    friend.memes["joy"] += 2
    hero.memes["worry"] = 0
    friend.memes["hurt"] = 0
    world.say(f"{friend.id} said sorry for laughing too fast.")
    world.say(f"{hero.id} said sorry for snapping so quickly, and then both of them leaned in to make a new profile picture together.")
    world.say(f"This time the photo showed {hero.id}, {friend.id}, and the {prop.label}, all grinning like they had shared the best secret in the room.")
    world.say(f"The board looked brighter, and so did they.")


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    prop: Entity = _safe_fact(world, f, "prop")
    return [
        f'Write a heartwarming story about a child making a profile picture with a {prop.label}.',
        f"Tell a funny but gentle story where {hero.id} and {friend.id} start with a small misunderstanding and end by making up.",
        f'Write a short story that includes the word "profile" and ends with two friends smiling together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    prop: Entity = _safe_fact(world, f, "prop")
    return [
        QAItem(
            question=f"What kind of picture did {hero.id} want to make?",
            answer=f"{hero.id} wanted to make a profile picture for the board at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {friend.id} stop smiling for a moment?",
            answer=f"{friend.id} laughed too quickly when the first picture looked crooked, and that made {hero.id} feel small.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the problem?",
            answer=f"They apologized to each other and made a new profile picture together with the {prop.label}.",
        ),
        QAItem(
            question=f"What did the final picture show?",
            answer=f"It showed {hero.id}, {friend.id}, and the {prop.label}, all smiling together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a profile picture?",
            answer="A profile picture is a small picture that helps show who someone is on a page, board, or account.",
        ),
        QAItem(
            question="Why can funny hats or glasses make people laugh?",
            answer="Funny hats or glasses can look a little odd on purpose, and that playful look often makes people smile.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    bits = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(bits)


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming profile storyworld with humor and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "prop", None) and (getattr(args, "setting", None), getattr(args, "prop", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    choices = [c for c in combos if (not getattr(args, "setting", None) or c[0] == getattr(args, "setting", None)) and (not getattr(args, "prop", None) or c[1] == getattr(args, "prop", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, prop = rng.choice(choices)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    friend_type = "girl" if gender == "boy" else "boy"
    hero_type = gender
    return StoryParams(setting=setting, prop=prop, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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
    StoryParams(setting="classroom", prop="hat", hero_name="Mia", hero_type="girl", friend_name="Pip", friend_type="boy"),
    StoryParams(setting="library", prop="glasses", hero_name="Noah", hero_type="boy", friend_name="Ruby", friend_type="girl"),
    StoryParams(setting="hallway", prop="sticker", hero_name="Luna", hero_type="girl", friend_name="Kai", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        for s, p in combos:
            print(s, p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
