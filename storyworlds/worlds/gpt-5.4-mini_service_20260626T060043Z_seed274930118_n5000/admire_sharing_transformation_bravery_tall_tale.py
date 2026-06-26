#!/usr/bin/env python3
"""
A standalone story world: admire, sharing, transformation, bravery, and a
tall-tale-sized turn.

The source tale imagined for this world:
---
A little child admired a tall tale told by a grandparent about a shy bridge
that could grow into a brave ladder when someone shared the right thing at the
right time. One windy afternoon, the child found a lost lantern, wanted to keep
it, then chose to share it with a friend and a giggling river sprite. That act
of sharing made the bridge transform, the crossing become safe, and the child
feel brave enough to cross and help others.

This script turns that premise into a small simulated world with physical meters
and emotional memes, plus a declarative ASP twin for the reasonableness gate.
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
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    helper: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the river bridge"
    wind: str = "windy"
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    region: str
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
class Charm:
    id: str
    label: str
    phrase: str
    transforms_to: str
    requires_sharing: bool = True
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    relic: str
    charm: str
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


SETTINGS = {
    "bridge": Setting(place="the long river bridge", wind="windy", affords={"share", "cross"}),
    "hill": Setting(place="the high hill path", wind="windy", affords={"share", "cross"}),
    "harbor": Setting(place="the harbor pier", wind="blustery", affords={"share", "cross"}),
}

RELICS = {
    "lantern": Relic(id="lantern", label="lantern", phrase="a tiny brass lantern", type="lantern", region="hands"),
    "bell": Relic(id="bell", label="bell", phrase="a silver pocket bell", type="bell", region="hands"),
    "map": Relic(id="map", label="map", phrase="a folded map with red ink", type="map", region="hands"),
}

CHARMS = {
    "spark": Charm(id="spark", label="spark charm", phrase="a bright spark charm", transforms_to="glow bridge"),
    "feather": Charm(id="feather", label="feather charm", phrase="a pale feather charm", transforms_to="wing bridge"),
    "stone": Charm(id="stone", label="stone charm", phrase="a smooth stone charm", transforms_to="steady bridge"),
}

GIRL_NAMES = ["Mina", "Lila", "June", "Nora", "Ruby", "Tessa"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Jude", "Milo", "Ezra"]


class WorldState:
    def __init__(self, world: World) -> None:
        self.world = world
        self.shared = False
        self.transformed = False
        self.brave = False
        self.bridge_form = "shy bridge"

    @property
    def hero(self) -> Entity:
        return self.world.get("hero")

    @property
    def helper(self) -> Entity:
        return self.world.get("helper")

    @property
    def relic(self) -> Entity:
        return self.world.get("relic")


def can_transform(state: WorldState, charm: Charm) -> bool:
    return state.shared and charm.requires_sharing


ASP_RULES = r"""
shared :- gave_away.
transformed(Bridge) :- shared, charm(Bridge).
brave(Hero) :- transformed(_), crossed(Hero).
valid_story(Place, Relic, Charm) :- setting(Place), relic(Relic), charm(Charm).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = {(p, r, c) for p in SETTINGS for r in RELICS for c in CHARMS}
    asp_combos = set(asp_valid_stories())
    if combos == asp_combos:
        print(f"OK: clingo gate matches Python gate ({len(combos)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if asp_combos - combos:
        print("  only in ASP:", sorted(asp_combos - combos))
    if combos - asp_combos:
        print("  only in Python:", sorted(combos - asp_combos))
    return 1


def introduce(world: World, hero: Entity, helper: Entity, relic: Entity, charm: Entity) -> None:
    world.say(
        f"On a {world.setting.wind} day at {world.setting.place}, {hero.id} admired "
        f"{helper.id}'s tall tale about a bridge that could grow brave."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {relic.label} close and kept "
        f"thinking about the {charm.label} hidden in {helper.id}'s pocket."
    )


def desire(world: World, state: WorldState, charm: Charm) -> None:
    hero = state.hero
    hero.memes["admire"] = hero.memes.get("admire", 0.0) + 1
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"{hero.id} wanted to keep {state.relic.pronoun('object') if hasattr(state.relic, 'pronoun') else 'it'} "
        f"all to {hero.pronoun('object')}, but {hero.id} also admired how {state.helper.id} shared "
        f"things that made old tales come true."
    )


def offer_share(world: World, state: WorldState, charm: Charm) -> None:
    hero = state.hero
    helper = state.helper
    world.say(
        f"When the wind rattled the rail, {hero.id} chose to share the {state.relic.label} "
        f"with {helper.id} instead of hiding {hero.pronoun('object')} away."
    )
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    state.shared = True
    helper.memes["thankful"] = helper.memes.get("thankful", 0.0) + 1
    world.say(
        f"{helper.id} smiled, and the {charm.label} began to warm like a little sunrise."
    )


def transform_bridge(world: World, state: WorldState, charm: Charm) -> None:
    if not can_transform(state, charm):
        return
    state.transformed = True
    state.bridge_form = charm.transforms_to
    world.say(
        f"The moment the sharing was done, the bridge stopped trembling like a shy noodle "
        f"and transformed into a {charm.transforms_to} with bright rails."
    )


def bravery_turn(world: World, state: WorldState) -> None:
    hero = state.hero
    if state.transformed:
        state.brave = True
        hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
        world.say(
            f"{hero.id} took one brave step, then another, and crossed while the new bridge "
            f"held steady under {hero.pronoun('possessive')} feet."
        )
        world.say(
            f"By the far side, {hero.id} looked taller than the lamp posts and twice as proud."
        )


def ending_image(world: World, state: WorldState) -> None:
    hero = state.hero
    helper = state.helper
    relic = state.relic
    world.say(
        f"In the end, {hero.id} kept {relic.pronoun('object') if hasattr(relic, 'pronoun') else 'the lantern'} only in "
        f"{hero.pronoun('possessive')} memory, shared the real treasure, and walked home "
        f"braver than before, with {helper.id} laughing beside {hero.pronoun('object')}."
    )


def tell(setting: Setting, hero_name: str, hero_gender: str, helper_name: str, helper_gender: str, relic_cfg: Relic, charm_cfg: Charm) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender))
    relic = world.add(Entity(id="relic", type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase))
    charm = world.add(Entity(id="charm", type="charm", label=charm_cfg.label, phrase=charm_cfg.phrase))
    state = WorldState(world)

    world.facts.update(hero=hero, helper=helper, relic=relic, charm=charm, setting=setting)

    introduce(world, hero, helper, relic, charm)
    world.para()
    desire(world, state, charm_cfg)
    offer_share(world, state, charm_cfg)
    transform_bridge(world, state, charm_cfg)
    bravery_turn(world, state)
    world.para()
    ending_image(world, state)
    world.facts.update(shared=state.shared, transformed=state.transformed, brave=state.brave, bridge_form=state.bridge_form)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    relic = _safe_fact(world, f, "relic")
    charm = _safe_fact(world, f, "charm")
    return [
        f'Write a tall-tale story for a small child about {hero.id}, {helper.id}, and a {charm.label} that rewards sharing.',
        f"Tell a story where {hero.id} admires {helper.id}'s old tale, shares a {relic.label}, and the bridge transforms.",
        f'Write a brave little story that includes the word "admire" and ends with a child crossing a changed bridge.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    relic = _safe_fact(world, f, "relic")
    charm = _safe_fact(world, f, "charm")
    qa = [
        QAItem(
            question=f"Who admired the tall tale at {world.setting.place}?",
            answer=f"{hero.id} admired {helper.id}'s tall tale about the bridge.",
        ),
        QAItem(
            question=f"What did {hero.id} share that helped the story change?",
            answer=f"{hero.id} shared the {relic.label}, and that sharing helped the bridge transform.",
        ),
        QAItem(
            question=f"What did the bridge turn into after the sharing?",
            answer=f"It turned into a {f['bridge_form']}, because the {charm.label} responded to the sharing.",
        ),
    ]
    if f.get("transformed"):
        qa.append(
            QAItem(
                question=f"Why did {hero.id} feel brave at the end?",
                answer=f"{hero.id} felt brave because the transformed bridge stayed steady and {hero.id} crossed it safely.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, hold, or enjoy something instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard even when your knees feel wobbly.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form, like a plain thing becoming something special.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, r, c) for p in SETTINGS for r in RELICS for c in CHARMS]


CURATED = [
    StoryParams(place="bridge", hero_name="Mina", hero_gender="girl", helper_name="Grandpa", helper_gender="man", relic="lantern", charm="spark"),
    StoryParams(place="hill", hero_name="Owen", hero_gender="boy", helper_name="Grandma", helper_gender="woman", relic="bell", charm="feather"),
    StoryParams(place="harbor", hero_name="Lila", hero_gender="girl", helper_name="Uncle Bram", helper_gender="man", relic="map", charm="stone"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "relic", None):
        combos = [c for c in combos if c[1] == getattr(args, "relic", None)]
    if getattr(args, "charm", None):
        combos = [c for c in combos if c[2] == getattr(args, "charm", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, relic, charm = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Grandma", "Grandpa", "Aunt June", "Uncle Bram"])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        relic=relic,
        charm=charm,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
        _safe_lookup(RELICS, params.relic),
        _safe_lookup(CHARMS, params.charm),
    )
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: admire, sharing, transformation, and bravery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.hero_name}: {p.relic} + {p.charm} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
