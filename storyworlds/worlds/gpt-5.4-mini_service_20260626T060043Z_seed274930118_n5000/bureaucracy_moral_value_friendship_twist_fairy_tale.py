#!/usr/bin/env python3
"""
A small fairy-tale storyworld about bureaucracy, moral value, friendship, and a
twist ending.

Premise:
A kind traveler wants to help someone in a tiny kingdom, but the castle's
bureaucracy demands papers, stamps, and signatures. A friend helps navigate the
forms, and the twist is that the most important "approval" comes from a simple
act of honesty and kindness, not from the highest seal.

The world is simulated: characters have physical meters and emotional memes,
documents can be incomplete or stamped, and the final story is assembled from
state changes rather than a frozen template.
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
# Data model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clerk: object | None = None
    friend: object | None = None
    hero: object | None = None
    permit: object | None = None
    petitioner: object | None = None
    seal: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "princess", "mother"}
        male = {"boy", "man", "king", "prince", "father"}
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
class Setting:
    place: str = "the little castle"
    delay: str = "a long line of forms"
    clerks: int = 2
    affords: set[str] = field(default_factory=lambda: {"help_petition", "request_seal"})
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
class Quest:
    name: str
    action: str
    goal: str
    risk: str
    rule: str
    keyword: str
    resolution: str
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
class StoryParams:
    place: str
    quest: str
    hero_name: str
    friend_name: str
    hero_type: str
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


THRESHOLD = 1.0


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "castle": Setting(place="the little castle", delay="a long line of forms", clerks=2),
    "hall": Setting(place="the town hall", delay="three stamped pages", clerks=3),
    "office": Setting(place="the narrow office", delay="a shelf of dusty ledgers", clerks=1),
}

QUESTS = {
    "petitioner": Quest(
        name="help petition",
        action="help the poor miller",
        goal="get a petition approved",
        risk="the petition could be rejected for missing a seal",
        rule="every request needs three stamps",
        keyword="bureaucracy",
        resolution="the clerk finally accepted the honest request",
    ),
    "permit": Quest(
        name="request seal",
        action="open the market gate",
        goal="get a permit approved",
        risk="the permit could be delayed by missing paperwork",
        rule="every permit must be filed in triplicate",
        keyword="bureaucracy",
        resolution="the gate was opened when the truth came out",
    ),
}

GIRL_NAMES = ["Ella", "Mira", "Luna", "Ada", "Ivy", "Nora"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Eli", "Owen", "Ben"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a setting can host the quest and the quest has a moral twist:
% a bureaucratic obstacle, a friendship helper, and an honest resolution.
valid_story(S,Q) :- setting(S), quest(Q), affords(S,Q), has_friendship(Q), has_twist(Q).
has_friendship(help_petition).
has_friendship(request_seal).
has_twist(help_petition).
has_twist(request_seal).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for q in sorted(_safe_lookup(SETTINGS, sid).affords):
            lines.append(asp.fact("affords", sid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, q) for s in SETTINGS for q in _safe_lookup(SETTINGS, s).affords}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: ASP matches Python gate ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    clerk = world.add(Entity(id="Clerk", kind="character", type="clerk", label="the clerk"))
    petitioner = world.add(Entity(
        id="Petitioner",
        kind="character",
        type="villager",
        label="the miller",
    ))
    permit = world.add(Entity(
        id="paper",
        type="document",
        label="petition paper",
        phrase="a folded petition paper",
        owner=hero.id,
    ))
    seal = world.add(Entity(
        id="seal",
        type="thing",
        label="red wax seal",
        phrase="a red wax seal",
        owner=clerk.id,
    ))

    world.facts.update(hero=hero, friend=friend, clerk=clerk, petitioner=petitioner,
                        permit=permit, seal=seal, quest=_safe_lookup(QUESTS, params.quest))
    return world


def predict_rejection(world: World) -> bool:
    permit = world.get("paper")
    return permit.m("stamped") < THRESHOLD


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    clerk: Entity = _safe_fact(world, f, "clerk")
    petitioner: Entity = _safe_fact(world, f, "petitioner")
    permit: Entity = _safe_fact(world, f, "permit")
    quest: Quest = _safe_fact(world, f, "quest")

    world.say(f"Long ago, {hero.id} lived near {world.setting.place}, where even kindness had to wait in line.")
    world.say(f"{hero.id} wanted to {quest.action}, but in that kingdom, {quest.rule}.")
    world.say(f"So {hero.id} carried {permit.phrase} to {world.setting.place}, hoping the clerk would approve {permit.it()}.")

    world.para()
    world.say(f"At the door, {hero.id} saw {world.setting.delay}, and {friend.id} appeared beside {hero.id} like a lantern in fog.")
    hero.memes["hope"] = hero.e("hope") + 1
    friend.memes["loyalty"] = friend.e("loyalty") + 1
    world.say(f"{friend.id} said, \"I'll help you sort the papers.\" That was the first warm thing in the whole hall.")

    if predict_rejection(world):
        hero.memes["worry"] = hero.e("worry") + 1
        world.say(f"But the clerk frowned, because {quest.risk}.")
        world.say(f"{hero.id} almost gave up, yet {friend.id} checked the pages and noticed one blank line where a promise should be.")

        world.para()
        permit.meters["filled"] = 1
        permit.meters["stamped"] = 3
        hero.memes["honesty"] = hero.e("honesty") + 1
        friend.memes["care"] = friend.e("care") + 1
        world.say(f"{hero.id} returned the paper and told the truth: the request was not for gold or glory, only to {quest.action}.")
        world.say(f"{friend.id} added the missing details, and together they made the petition neat and clear.")
        world.say(f"The clerk blinked, then pressed a bright seal onto {permit.label}.")
        world.say(f"After that, {quest.resolution}.")
        world.say(f"{petitioner.id} smiled, because the help finally reached the right hands.")
        hero.memes["joy"] = hero.e("joy") + 1
        friend.memes["joy"] = friend.e("joy") + 1
    else:
        world.say(f"The papers were already complete, so the clerk stamped {permit.it()} at once.")
        world.say(f"{quest.resolution}, and {friend.id} laughed because the answer had been simple all along.")

    world.para()
    world.say(f"In the end, {hero.id} learned that in a kingdom of stamps and ledgers, moral value mattered more than showy seals.")
    world.say(f"{friend.id} learned that friendship can make even the longest queue feel short.")
    world.say(f"And the little castle was quieter after the visit, because one honest request had opened a door no heavy lock could keep shut.")


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    quest: Quest = _safe_fact(world, f, "quest")
    return [
        f'Write a fairy-tale story about bureaucracy, friendship, and a moral value, using the word "{quest.keyword}".',
        f"Tell a child-friendly story in which {hero.id} needs help from {friend.id} to navigate castle paperwork.",
        f"Write a short tale where a kind request gets delayed by stamps and forms, then ends with an unexpected twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    quest: Quest = _safe_fact(world, f, "quest")
    qas = [
        QAItem(
            question=f"Why did {hero.id} go to {world.setting.place}?",
            answer=f"{hero.id} went there to {quest.action}. The problem was that the kingdom's bureaucracy made the request slow and fussy.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id}?",
            answer=f"{friend.id} helped by sorting the papers, finding the missing detail, and staying loyal while the forms were checked.",
        ),
        QAItem(
            question=f"What was the moral value in the story?",
            answer=f"The moral value was that honesty and kindness matter more than fancy-looking official stamps.",
        ),
        QAItem(
            question=f"What was the twist ending?",
            answer=f"The twist was that the most important approval came when {hero.id} told the truth, not when the highest seal was added.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bureaucracy?",
            answer="Bureaucracy is a system of rules, papers, stamps, and official steps that people must follow before something is approved.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind even when things are hard.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an idea about how to behave well, like being honest, fair, or kind.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader expected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bureaucracy storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
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
    if getattr(args, "place", None) and getattr(args, "quest", None):
        if getattr(args, "quest", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(_safe_lookup(SETTINGS, place).affords))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    hero_type = gender
    friend_type = "girl" if gender == "boy" else "boy"
    return StoryParams(place=place, quest=quest, hero_name=hero_name, friend_name=friend_name,
                       hero_type=hero_type, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


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
    StoryParams(place="castle", quest="petitioner", hero_name="Ella", friend_name="Finn", hero_type="girl", friend_type="boy"),
    StoryParams(place="hall", quest="permit", hero_name="Milo", friend_name="Nora", hero_type="boy", friend_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        models = asp_valid()
        print(f"{len(models)} valid stories:")
        for s, q in models:
            print(f"  {s} {q}")
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
