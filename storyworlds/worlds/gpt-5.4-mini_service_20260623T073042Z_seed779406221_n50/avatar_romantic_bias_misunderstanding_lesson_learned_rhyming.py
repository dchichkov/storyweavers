#!/usr/bin/env python3
"""
storyworlds/worlds/avatar_romantic_bias_misunderstanding_lesson_learned_rhyming.py
=================================================================================

A standalone storyworld in a tiny rhyming style about an avatar, a romantic
bias, a misunderstanding, and a lesson learned.

Seed-tale inspiration:
---
An avatar named Mira loved making kind drawings for her class wall. She thought
her friend Jun only liked the sporty kids, because Jun always cheered loudest for
the players on the field. Mira felt a little hurt and stopped waving at Jun.

But Jun was not being biased against Mira at all. Jun had been cheering for
a cousin at practice, and Jun had saved a bright heart sticker for Mira's art.
When Mira finally asked, Jun explained the mix-up, and the two friends laughed.
Mira learned not to guess too quickly from one small moment.

This world turns that seed into a small simulation:
- a social avatar in a simple place,
- a biased-looking clue,
- a misunderstanding that raises hurt feelings,
- a patient explanation,
- and a warm ending image proving the lesson learned.

The prose is intentionally rhyming and sing-song, but still state-driven.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    pal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
    vibe: str
    affordance: str
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Avatar:
    id: str
    label: str
    style: str
    rhyme: str
    bias_kind: str
    bias_clue: str
    misunderstanding: str
    lesson: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class SocialCue:
    id: str
    label: str
    phrase: str
    true_reason: str
    mistaken_reason: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Outcome:
    id: str
    label: str
    reveal: str
    repair: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def _r_hurt(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.memes.get("hurt", 0.0) < THRESHOLD:
            continue
        sig = ("hurt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["silence"] = ent.memes.get("silence", 0.0) + 1
        out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _r_hurt(world):
            if s is not None:
                changed = True
                if s:
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for av in AVATARS.values():
        for cue in CUES.values():
            if av.bias_kind == cue.id:
                combos.append((av.id, cue.id))
    return combos


@dataclass
class StoryParams:
    avatar: str
    cue: str
    setting: str
    name: str
    friend: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    "schoolyard": Setting(place="the schoolyard", vibe="bright and airy", affordance="talk"),
    "studio": Setting(place="the art studio", vibe="soft and glowy", affordance="paint"),
    "garden": Setting(place="the garden path", vibe="gentle and green", affordance="stroll"),
}

AVATARS = {
    "heart": Avatar(
        id="heart",
        label="heart avatar",
        style="soft and bright",
        rhyme="light",
        bias_kind="spark",
        bias_clue="glad cheers for a single friend",
        misunderstanding="thought the cheers meant dislike",
        lesson="one small clue can trick the view",
        tags={"avatar", "romantic", "bias"},
    ),
    "star": Avatar(
        id="star",
        label="star avatar",
        style="quick and keen",
        rhyme="gleam",
        bias_kind="flower",
        bias_clue="loved the flower club parade",
        misunderstanding="thought the smiles meant sides had formed",
        lesson="kindly ask before you decide",
        tags={"avatar", "romantic", "bias"},
    ),
}

CUES = {
    "spark": SocialCue(
        id="spark",
        label="spark cue",
        phrase="loud cheers for a cousin on the field",
        true_reason="The cheers were for family practice, not for picking favorites.",
        mistaken_reason="It seemed like the avatar liked only sporty kids.",
        tags={"bias"},
    ),
    "flower": SocialCue(
        id="flower",
        label="flower cue",
        phrase="a heart sticker tucked for a craft table",
        true_reason="The sticker was a gift for art, not a secret club sign.",
        mistaken_reason="It seemed like the avatar was leaving others out.",
        tags={"romantic"},
    ),
}

OUTCOMES = {
    "lesson": Outcome(
        id="lesson",
        label="lesson learned",
        reveal="Then the truth came clear in a friendly swirl.",
        repair="They laughed and talked, and the hurt went still.",
        ending_image="Two friends drew hearts and stars by the shore of the page.",
        tags={"lesson", "misunderstanding"},
    )
}

GIRL_NAMES = ["Mira", "Nina", "Tessa", "Lina", "Ruby"]
BOY_NAMES = ["Jun", "Arlo", "Ben", "Noah", "Pax"]
FRIENDS = ["a classmate", "a friend", "a neighbor", "a cousin"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming avatar storyworld with bias and misunderstanding.")
    ap.add_argument("--avatar", choices=AVATARS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "avatar", None) is None or c[0] == getattr(args, "avatar", None))
              and (getattr(args, "cue", None) is None or c[1] == getattr(args, "cue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    avatar, cue = rng.choice(list(combos))
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    return StoryParams(avatar=avatar, cue=cue, setting=setting, name=name, friend=friend)


def tell(setting: Setting, avatar: Avatar, cue: SocialCue, name: str, friend: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl" if name in GIRL_NAMES else "boy"))
    pal = world.add(Entity(id="Friend", kind="character", type="boy", label=friend))
    hero.meters["presence"] = 1
    hero.memes["worry"] = 0
    hero.memes["hurt"] = 0
    pal.meters["presence"] = 1
    pal.memes["calm"] = 1
    world.facts["avatar"] = avatar
    world.facts["cue"] = cue
    world.facts["hero"] = hero
    world.facts["friend"] = pal

    world.say(f"In {setting.place}, {name} moved in a silver stream, with a {avatar.style} gleam.")
    world.say(f"{name} had a {avatar.label}, and loved to rhyme in time.")
    world.para()
    world.say(f"One day {name} saw {cue.phrase}, and a hush fell in the chime.")
    world.say(f"{name} thought, '{cue.mistaken_reason}' and frowned at the scene.")
    hero.memes["worry"] += 1
    hero.memes["hurt"] += 1
    world.para()
    world.say(f"But {friend} said, '{cue.true_reason}' with a smile so serene.")
    world.say(f"'{avatar.misunderstanding},' {name} sighed, 'I guessed too fast and missed the light.'")
    hero.memes["worry"] = 0
    hero.memes["hurt"] = 0
    hero.memes["lesson"] += 1
    world.para()
    world.say(f"{name} and {friend} sat down to talk, and the moon seemed warm and bright.")
    world.say(f"{avatar.lesson.capitalize()}, and so the day grew sweet and true.")
    world.say(OUTCOMES["lesson"].reveal)
    world.say(OUTCOMES["lesson"].repair)
    world.say(OUTCOMES["lesson"].ending_image)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child about an avatar, romantic bias, and a misunderstanding in {world.setting.place}.',
        f"Tell a gentle rhyming tale where {f['hero'].id} notices {f['cue'].phrase} and learns not to guess too soon.",
        "Write a short, sing-song story with a warm ending and the lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, avatar, cue = f["hero"], f["friend"], f["avatar"], f["cue"]
    return [
        QAItem(
            question=f"Who is the story about in {world.setting.place}?",
            answer=f"It is about {hero.id}, who saw the {avatar.label} and had a misunderstanding before learning the truth.",
        ),
        QAItem(
            question=f"What made {hero.id} feel upset at first?",
            answer=f"{cue.phrase} looked like bias to {hero.id}, so {hero.id} felt hurt and guessed too fast.",
        ),
        QAItem(
            question=f"What did {friend.id} explain?",
            answer=f"{cue.true_reason} That helped clear up the misunderstanding.",
        ),
        QAItem(
            question="What lesson did the avatar story teach?",
            answer=f"It taught that one small clue can trick the view, so it is best to ask kindly before deciding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avatar?",
            answer="An avatar is a little character or picture that stands in for a person in a story or game.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something is true, but they do not have the whole story yet.",
        ),
        QAItem(
            question="What does bias mean?",
            answer="Bias means leaning toward one choice, person, or idea too quickly instead of being fair to everyone.",
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
        lines.append(f"  {e.id:8} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,C) :- avatar(A), cue(C), avatar_bias(A,C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for aid, a in AVATARS.items():
        lines.append(asp.fact("avatar", aid))
        lines.append(asp.fact("avatar_bias", aid, a.bias_kind))
    for cid, c in CUES.items():
        lines.append(asp.fact("cue", cid))
        lines.append(asp.fact("cue_kind", cid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(AVATARS, params.avatar), _safe_lookup(CUES, params.cue), params.name, params.friend)
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
    StoryParams(avatar="heart", cue="spark", setting="schoolyard", name="Mira", friend="a cousin"),
    StoryParams(avatar="star", cue="flower", setting="studio", name="Jun", friend="a friend"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
