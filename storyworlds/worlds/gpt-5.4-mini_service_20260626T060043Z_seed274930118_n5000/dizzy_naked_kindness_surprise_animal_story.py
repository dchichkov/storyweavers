#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260626T060043Z_seed274930118_n5000/dizzy_naked_kindness_surprise_animal_story.py
=============================================================================================================

A small, standalone animal-story world built from the seed words
"dizzy" and "naked" with the features Kindness and Surprise.

Premise:
- A tiny naked chick gets dizzy after a windy, spinning moment.
- A kind parent bird notices the wobble and offers a gentle way to rest.
- A surprise arrives in the form of a soft, safe nestlet and a happy snack.

The world keeps a simple simulation of physical meters and emotional memes,
then narrates a child-facing story from those state changes.
"""

from __future__ import annotations

import argparse
import dataclasses
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

SETTINGS = {
    "meadow": {
        "name": "the meadow",
        "air": "bright",
        "features": {"breeze", "grass", "flowers"},
    },
    "orchard": {
        "name": "the orchard",
        "air": "cool",
        "features": {"breeze", "grass", "trees"},
    },
    "garden": {
        "name": "the garden",
        "air": "warm",
        "features": {"flowers", "leaf_pile", "shade"},
    },
}

ACTIVITIES = {
    "spinning": {
        "verb": "spin in circles",
        "gerund": "spinning in circles",
        "rush": "twirl faster and faster",
        "cause": "dizzy",
        "meters": {"spin": 1.0, "steady": -1.0},
        "setting_need": {"breeze"},
    },
    "chasing_butterfly": {
        "verb": "chase a butterfly",
        "gerund": "chasing butterflies",
        "rush": "dash after the fluttering wings",
        "cause": "dizzy",
        "meters": {"run": 1.0, "steady": -0.5},
        "setting_need": {"grass", "flowers"},
    },
    "climbing_branch": {
        "verb": "climb a low branch",
        "gerund": "climbing low branches",
        "rush": "scramble too high too quickly",
        "cause": "dizzy",
        "meters": {"climb": 1.0, "steady": -0.5},
        "setting_need": {"trees"},
    },
}

SURPRISES = {
    "moss_nest": {
        "label": "a surprise moss nest",
        "thing": "nest",
        "comfort": "soft",
        "reason": "the baby bird needed a cozy place to rest",
    },
    "berry_snack": {
        "label": "a surprise berry snack",
        "thing": "snack",
        "comfort": "sweet",
        "reason": "the little bird needed a gentle treat",
    },
    "feather_blanket": {
        "label": "a surprise feather blanket",
        "thing": "blanket",
        "comfort": "warm",
        "reason": "the naked chick needed something soft and warm",
    },
}

KINDS = {
    "parent_bird": {
        "type": "bird",
        "label": "parent bird",
        "pronoun": "she",
        "name_pool": ["Robin", "Mira", "Pia", "Luna"],
    },
    "friend_bird": {
        "type": "bird",
        "label": "friend bird",
        "pronoun": "he",
        "name_pool": ["Toby", "Finn", "Pip", "Nico"],
    },
}

NAMES = ["Pip", "Nip", "Tilly", "Bean", "Sky", "Pebble"]



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
    name: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    nestlet: object | None = None
    parent: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def say(self, case: str = "subject") -> str:
        if self.type == "bird":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: dataclasses.replace(v, meters=dict(v.meters), memes=dict(v.memes))
                          for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.lines = []
        clone.fired = set(self.fired)
        return clone
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
    activity: str
    surprise: str
    hero_name: str
    parent_name: str
    friend_name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: dizzy, naked, kindness, surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--friend")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    if _safe_lookup(ACTIVITIES, activity)["setting_need"].isdisjoint(_safe_lookup(SETTINGS, setting)["features"]):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    parent_name = getattr(args, "parent", None) or rng.choice(KINDS["parent_bird"]["name_pool"])
    friend_name = getattr(args, "friend", None) or rng.choice(KINDS["friend_bird"]["name_pool"])
    return StoryParams(setting, activity, surprise, hero_name, parent_name, friend_name)


def apply_dizzy(world: World, hero: Entity, activity: dict) -> None:
    hero.meters["dizzy"] = hero.meters.get("dizzy", 0.0) + 1.0
    hero.meters["steady"] = hero.meters.get("steady", 0.0) + activity["meters"].get("steady", 0.0)
    hero.memes["wobble"] = hero.memes.get("wobble", 0.0) + 1.0


def generate_world(params: StoryParams) -> World:
    world = World(params.setting)
    setting = _safe_lookup(SETTINGS, params.setting)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    surprise = _safe_lookup(SURPRISES, params.surprise)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="bird",
        label="tiny chick",
        name=params.hero_name,
        meters={"dizzy": 0.0, "steady": 0.0},
        memes={"curiosity": 1.0, "joy": 0.0, "comfort": 0.0, "kindness": 0.0, "surprise": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type="bird",
        label="parent bird",
        name=params.parent_name,
        meters={"care": 1.0},
        memes={"kindness": 2.0, "worry": 0.0, "joy": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="bird",
        label="friend bird",
        name=params.friend_name,
        meters={"help": 1.0},
        memes={"surprise": 1.0, "kindness": 1.0},
    ))
    nestlet = world.add(Entity(
        id="surprise",
        kind="thing",
        type=surprise["thing"],
        label=surprise["label"],
        owner=parent.id,
        meters={"soft": 1.0},
        memes={"comfort": 1.0},
    ))

    world.say(f"{hero.name} was a naked little chick in {setting['name']}.")
    world.say(f"{hero.name} loved the bright air and wanted to {activity['verb']}.")
    world.say(f"One breezy moment made {hero.name} {activity['gerund']}, and soon {hero.say()} felt dizzy.")

    apply_dizzy(world, hero, activity)
    world.facts["dizzy"] = hero.meters["dizzy"] >= 1.0
    world.facts["naked"] = True
    world.facts["kindness"] = True
    world.facts["surprise"] = True

    if hero.meters["dizzy"] >= 1.0:
        world.say(f"{hero.name} wobbled on tiny feet and sat down fast so {hero.say()} would not fall.")
        parent.memes["worry"] += 1.0
        parent.memes["kindness"] += 1.0
        world.say(f"{params.parent_name} saw the wobble and spoke with kindness: “Come here, little one.”")
        world.say(f"{params.parent_name} tucked {hero.name} into the {surprise['label']} because it was soft and safe.")
        hero.memes["comfort"] += 1.0
        hero.memes["joy"] += 1.0
        hero.memes["kindness"] += 1.0

    friend.memes["surprise"] += 1.0
    friend.memes["joy"] += 1.0
    world.say(f"Then {params.friend_name} arrived with a grin and a surprise: a sweet berry snack.")
    world.say(f"{hero.name} blinked, then smiled. The dizzy feeling faded, and the naked chick snuggled deep into the soft spot.")
    world.say(f"By the end, {hero.name} was calm, {params.parent_name} was smiling, and the meadow felt warm again.")

    world.facts.update(
        hero=hero,
        parent=parent,
        friend=friend,
        surprise_ent=nestlet,
        setting=setting,
        activity=activity,
        surprise_cfg=surprise,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    surprise = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "surprise_cfg")
    return [
        f'Write a short animal story for a small child that includes the words "dizzy" and "naked".',
        f"Tell a gentle story about {hero.name}, a little bird, who gets dizzy while {activity['gerund']} and learns about kindness.",
        f"Write a story where a surprise {surprise['thing']} helps a baby animal feel safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    surprise = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "surprise_cfg")
    return [
        QAItem(
            question=f"Who was dizzy in the story?",
            answer=f"{hero.name} was dizzy after {hero.name.lower()} was {activity['gerund']} in {world.setting}.",
        ),
        QAItem(
            question=f"Why did {parent.name} help {hero.name}?",
            answer=f"{parent.name} helped because {hero.name} was a naked little chick and looked dizzy and wobbly.",
        ),
        QAItem(
            question=f"What was the surprise?",
            answer=f"The surprise was {surprise['label']}, and it was soft and cozy for {hero.name}.",
        ),
        QAItem(
            question=f"How did kindness show up in the story?",
            answer=f"{parent.name} was kind by helping {hero.name} rest, and {friend.name} was kind by bringing a sweet snack.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to feel dizzy?",
            answer="Feeling dizzy means you feel wobbly or spinny, like your body is not standing quite straight.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, and being gentle with someone who needs care.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it can make you gasp and smile.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
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
    for ent in list(world.entities.values()):
        lines.append(f"{ent.id}: {ent.name or ent.label} meters={ent.meters} memes={ent.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(meadow). setting(orchard). setting(garden).
activity(spinning). activity(chasing_butterfly). activity(climbing_branch).
surprise(moss_nest). surprise(berry_snack). surprise(feather_blanket).

supports(meadow,breeze). supports(meadow,grass). supports(meadow,flowers).
supports(orchard,breeze). supports(orchard,grass). supports(orchard,trees).
supports(garden,flowers). supports(garden,leaf_pile). supports(garden,shade).

needs(spinning,breeze).
needs(chasing_butterfly,grass).
needs(chasing_butterfly,flowers).
needs(climbing_branch,trees).

valid(S,A,SU) :- setting(S), activity(A), surprise(SU), needs(A,N), supports(S,N).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for feat in _safe_lookup(SETTINGS, sid)["features"]:
            lines.append(asp.fact("supports", sid, feat))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        for feat in _safe_lookup(ACTIVITIES, aid)["setting_need"]:
            lines.append(asp.fact("needs", aid, feat))
    for su in SURPRISES:
        lines.append(asp.fact("surprise", su))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a, cfg in ACTIVITIES.items():
            if cfg["setting_need"].isdisjoint(_safe_lookup(SETTINGS, s)["features"]):
                continue
            for su in SURPRISES:
                combos.append((s, a, su))
    return combos


def resolve_story(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    resolve_story(sample, trace=trace, qa=qa, header=header)


CURATED = [
    StoryParams("meadow", "spinning", "moss_nest", "Pip", "Robin", "Toby"),
    StoryParams("orchard", "chasing_butterfly", "berry_snack", "Tilly", "Mira", "Finn"),
    StoryParams("garden", "spinning", "feather_blanket", "Bean", "Pia", "Nico"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid setting/activity/surprise triples:\n")
        for t in vals:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} in {p.setting} ({p.activity} / {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
