#!/usr/bin/env python3
"""
A tiny story world of a nursery-rhyme quest for quintuplets, with sound effects
and a little foreshadowing.
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sib: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Place:
    name: str
    rhyme: str
    sounds: list[str]
    clue: str
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
class QuestItem:
    id: str
    label: str
    plural: bool = False
    sound: str = ""
    clue: str = ""
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
    hero_kind: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "nursery": Place(
        name="the nursery",
        rhyme="glow and grow",
        sounds=["tick-tock", "shh-shh", "ding-dong"],
        clue="soft blankets and a tiny lamp",
    ),
    "garden": Place(
        name="the garden gate",
        rhyme="breeze and bees",
        sounds=["buzz-buzz", "swish", "tap-tap"],
        clue="a stone path and a curly vine",
    ),
    "attic": Place(
        name="the attic",
        rhyme="dust and gust",
        sounds=["creak-creak", "whoosh", "tap-tap"],
        clue="a small box under a round moon window",
    ),
}

QUESTS = {
    "starbell": QuestItem(
        id="starbell",
        label="the star bell",
        sound="ting-ting",
        clue="a bright bell with a star on its side",
    ),
    "moonbutton": QuestItem(
        id="moonbutton",
        label="the moon button",
        sound="plink-plink",
        clue="a round button that looked like a little moon",
        plural=False,
    ),
    "goldenkey": QuestItem(
        id="goldenkey",
        label="the golden key",
        sound="clink-clink",
        clue="a tiny key that shone like honey",
    ),
}

NAMES = ["Mia", "Nina", "Lily", "Toby", "Pip", "Nora", "Eli", "June"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def foreshadow(place: Place, quest: QuestItem) -> str:
    if quest.id == "starbell":
        return "A little shine peeped from under the curtain, as if something wanted to sing."
    if place.name == "the attic":
        return "Up in the rafters, something whispered with a sleepy creak, like a clue in disguise."
    return "The wind gave one soft hint, as though a secret had already started to wake."


def quest_need(quest: QuestItem) -> str:
    return {
        "starbell": "find the missing star bell before bedtime",
        "moonbutton": "bring back the moon button that could calm the sleepy toy",
        "goldenkey": "fetch the golden key that opened the little music box",
    }[quest.id]


def quest_reason(quest: QuestItem) -> str:
    return {
        "starbell": "The nursery rhyme game could not begin without its bright ding.",
        "moonbutton": "Without it, the bedtime song would stay shut tight.",
        "goldenkey": "Without it, the music box would only sigh and wait.",
    }[quest.id]


def sound_line(quest: QuestItem, place: Place) -> str:
    return f"{quest.sound} went the quest clue, while {place.sounds[0]} whispered back."


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_kind,
        label=params.hero_name,
        meters={"hope": 1.0, "bravery": 1.0},
        memes={"curiosity": 1.0},
    ))
    siblings = []
    for i in range(5):
        sib = world.add(Entity(
            id=f"quintuplet{i+1}",
            kind="character",
            type=params.hero_kind,
            label=f"{params.hero_name}'s quintuplet",
            plural=False,
            meters={"hope": 1.0},
            memes={"joy": 1.0},
        ))
        siblings.append(sib)

    world.facts["hero"] = hero
    world.facts["siblings"] = siblings
    world.facts["quest"] = quest
    world.facts["place"] = place

    # Act 1
    world.say(f"In {place.name}, five little quintuplets tucked their toes and dreamed the same sweet dream.")
    world.say(f"{params.hero_name} listened to the hush of the room and knew a quest was waiting.")
    world.say(foreshadow(place, quest))
    world.para()

    # Act 2
    world.say(f'"We must {quest_need(quest)}," said {params.hero_name}, and the others nodded in a row.')
    world.say(f"They stepped where the moonlight fell, and {sound_line(quest, place)}")
    world.say(quest_reason(quest))
    world.say(f"The clues were small but sure: {quest.clue}, and a trail that glittered with {quest.sound} sounds.")
    world.facts["search_started"] = True
    world.para()

    # Act 3
    world.say(f"At last, the quintuplets found {quest.label} waiting in a cozy corner of {place.name}.")
    world.say(f"{params.hero_name} lifted it up, and {quest.sound}—{quest.sound}—it sang like a bedtime star.")
    world.say(f"The five children laughed together, and the nursery felt warm and bright again.")
    world.say(f"Then all was still, except for a happy little hum, and the quest was done.")

    world.facts["quest_done"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest = _safe_fact(world, f, "quest")
    place = _safe_fact(world, f, "place")
    hero = _safe_fact(world, f, "hero")
    return [
        f"Write a nursery-rhyme story about quintuplets in {place.name} who must {quest_need(quest)}.",
        f"Tell a gentle quest tale where {hero.label} and the quintuplets follow {quest.sound} clues.",
        f"Write a small rhyming story with foreshadowing, a quest, and a happy ending in {place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who led the quest in {place.name}?",
            answer=f"{hero.label} led the quest with the five quintuplets beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What did they need to do?",
            answer=f"They needed to {quest_need(quest)}.",
        ),
        QAItem(
            question=f"What sound helped point them to the answer?",
            answer=f"The clue sounded like {quest.sound}, and that helped guide them to the right spot.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the quintuplets finding {quest.label} and the room growing calm and happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quintuplet?",
            answer="A quintuplet is one of five children born at the same time, so the group has five together.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint early in a story that points to something important later.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or solve a problem.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help make a scene feel lively, like you can hear the action in your mind.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
place(P) :- place_name(P).
quest(Q) :- quest_name(Q).

valid_story(P,Q) :- place(P), quest(Q), needs_clue(Q), has_sound(Q).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pname in PLACES:
        lines.append(asp.fact("place_name", pname))
    for qname, q in QUESTS.items():
        lines.append(asp.fact("quest_name", qname))
        lines.append(asp.fact("needs_clue", qname))
        lines.append(asp.fact("has_sound", qname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, q) for p in PLACES for q in QUESTS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} story pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    hero_kind = getattr(args, "kind", None) or rng.choice(["girl", "boy"])
    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if quest not in QUESTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, quest=quest, hero_name=hero_name, hero_kind=hero_kind)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.name}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme quest world for quintuplets.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["girl", "boy"])
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


CURATED = [
    StoryParams(place="nursery", quest="starbell", hero_name="Mia", hero_kind="girl"),
    StoryParams(place="garden", quest="goldenkey", hero_name="Pip", hero_kind="boy"),
    StoryParams(place="attic", quest="moonbutton", hero_name="Nora", hero_kind="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for p, q in asp_valid_stories():
            print(p, q)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 20, 20)):
            if len(samples) >= getattr(args, "n", None):
                break
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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
