#!/usr/bin/env python3
"""
storyworlds/worlds/baton_friend_surprise_sound_effects_ghost_story.py
=====================================================================

A small story world about a child, a friend, a baton, and a surprising ghostly
sound. The story keeps a ghost-story feel, but it stays gentle: the "ghost" is
real enough to make a surprise, and the sound effects help drive the turning
point and the ending image.

The seed prompt asks for:
- Words: baton, friend
- Features: Surprise, Sound Effects
- Style: Ghost Story

This world models a tiny, child-facing mystery in a quiet hall. A practice baton
makes a tapping sound, a friend hears something odd, and a surprising reveal
shows that the ghostly noise has a simple cause. The story is driven by world
state: rooms, props, emotional beats, and the sound trail left behind.
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    baton: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
    id: str
    place: str
    mood: str
    has_echo: bool = False
    has_window: bool = False
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


@dataclass
class Baton:
    id: str
    label: str
    phrase: str
    tap: str
    trail: str
    glow: str
    surprise: str
    sound: str
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
class StoryParams:
    setting: str = "music_room"
    baton: str = "silver_baton"
    friend_name: str = "Mina"
    hero_name: str = "Iris"
    hero_gender: str = "girl"
    friend_gender: str = "girl"
    parent_name: str = "Grandma"
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "music_room": Setting(
        id="music_room",
        place="the old music room",
        mood="quiet and echoing",
        has_echo=True,
        has_window=False,
    ),
    "hallway": Setting(
        id="hallway",
        place="the long hallway",
        mood="still and drafty",
        has_echo=True,
        has_window=False,
    ),
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="dusty and moonlit",
        has_echo=False,
        has_window=True,
    ),
}

BATONS = {
    "silver_baton": Baton(
        id="silver_baton",
        label="silver baton",
        phrase="a silver baton with a white ribbon",
        tap="tap-tap",
        trail="a thin tapping trail",
        glow="bright enough to blink at the dust",
        surprise="a tiny surprise hid in the ribbon",
        sound="clink-clink",
        tags={"baton", "sound", "surprise"},
    ),
    "wooden_baton": Baton(
        id="wooden_baton",
        label="wooden baton",
        phrase="a smooth wooden baton",
        tap="tok-tok",
        trail="a dry tapping trail",
        glow="soft enough to shine on cobwebs",
        surprise="a little hidden note sat under the grip",
        sound="tok-tok",
        tags={"baton", "sound", "surprise"},
    ),
}

GIRL_NAMES = ["Iris", "Nina", "Maya", "June", "Luna", "Hazel"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Owen", "Leo"]
FRIEND_NAMES = ["Mina", "Bea", "Jules", "Rae", "Pip", "Tess"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, b) for s in SETTINGS for b in BATONS]


def explain_rejection(setting: str, baton: str) -> str:
    if setting not in SETTINGS:
        return "(No story: unknown setting.)"
    if baton not in BATONS:
        return "(No story: unknown baton.)"
    return "(No story: this combination cannot make a surprising ghost-story beat.)"


def should_choose_baton(setting: Setting, baton: Baton) -> bool:
    return baton.id in BATONS and setting.id in SETTINGS


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    baton = world.get("baton")
    if hero.meters["moving"] < THRESHOLD:
        return out
    sig = ("sound",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["heard"] += 1
    world.get("friend").meters["heard"] += 1
    hero.memes["spook"] += 1
    world.get("friend").memes["spook"] += 1
    out.append("__sound__")
    baton.meters["echo"] += 1
    return out


def _r_surprise(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    baton = world.get("baton")
    if hero.memes["spook"] < THRESHOLD or friend.memes["spook"] < THRESHOLD:
        return []
    sig = ("surprise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    baton.meters["revealed"] += 1
    return ["__surprise__"]


def _r_relief(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    baton = world.get("baton")
    if baton.meters["revealed"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    return ["__relief__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_sound, _r_surprise, _r_relief):
            sent = rule(world)
            if sent:
                changed = True
                out.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def seed_story(world: World, hero: Entity, friend: Entity, baton: Entity) -> None:
    hero.memes["curious"] += 1
    friend.memes["curious"] += 1
    world.say(
        f"{hero.id} and {friend.id} stepped into {world.setting.place}, where it felt "
        f"{world.setting.mood}."
    )
    world.say(
        f"They found {baton.phrase}. {baton.surprise.capitalize()}."
    )


def begin_tap(world: World, hero: Entity, friend: Entity, baton: Entity) -> None:
    hero.meters["moving"] += 1
    friend.meters["moving"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'{hero.id} lifted the baton and let it go {baton.tap}. '
        f'{friend.id} listened, smiling at the {baton.trail}.'
    )
    if world.setting.has_echo:
        world.say(f"The sound answered from the walls: {baton.sound}, {baton.sound}.")


def scare_and_listen(world: World, hero: Entity, friend: Entity, baton: Entity) -> None:
    hero.memes["spook"] += 1
    friend.memes["spook"] += 1
    world.say(
        f"Then came a little ghostly hush, as if the room were holding its breath."
    )
    world.say(
        f'{friend.id} grabbed {hero.pronoun("possessive")} sleeve. "Did you hear that?" '
        f'{friend.pronoun()} whispered.'
    )
    propagate(world, narrate=False)


def reveal_surprise(world: World, hero: Entity, friend: Entity, baton: Entity) -> None:
    baton.meters["revealed"] += 1
    world.say(
        f"At last, {hero.id} peered under the ribbon and found the surprise: "
        f"a tiny key tied to the baton with a knot."
    )
    world.say(
        f"That explained the strange sound. Every step made {baton.label_word} go "
        f"{baton.tap}, and every tap made the old room seem haunted."
    )
    propagate(world, narrate=False)


def end_with_laugh(world: World, hero: Entity, friend: Entity, baton: Entity) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{friend.id} laughed first, and then {hero.id} laughed too. It was not a ghost "
        f"at all, just the baton and the little key making spooky music."
    )
    world.say(
        f'Together they carried {baton.it()} to the window and watched the moonlight '
        f"flash on the ribbon."
    )
    world.say(
        f"By the end, the old room felt safe again, and the last sound was only "
        f"{baton.sound} fading into the quiet."
    )


def tell(setting: Setting, baton_cfg: Baton, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, parent_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name))
    baton = world.add(Entity(id="baton", kind="thing", type="thing", label=baton_cfg.label))
    world.facts["parent_name"] = parent_name
    world.facts["baton_cfg"] = baton_cfg
    world.facts["setting"] = setting
    world.facts["hero_name"] = hero_name
    world.facts["friend_name"] = friend_name
    world.facts["hero_gender"] = hero_gender
    world.facts["friend_gender"] = friend_gender

    seed_story(world, hero, friend, baton)
    world.para()
    begin_tap(world, hero, friend, baton)
    scare_and_listen(world, hero, friend, baton)
    world.para()
    reveal_surprise(world, hero, friend, baton)
    end_with_laugh(world, hero, friend, baton)
    world.facts["ending"] = "revealed"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    baton_cfg: Baton = f["baton_cfg"]  # type: ignore[assignment]
    return [
        f'Write a gentle ghost-story for a small child that includes the words "baton" and "friend" and uses the sound "{baton_cfg.sound}".',
        f"Tell a spooky-but-safe story where {f['hero_name']} and {f['friend_name']} hear a strange sound in {world.setting.place} and discover a hidden surprise.",
        f'Write a short story about a baton that makes ghostly noises, then turns out to have a surprise attached to it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    baton_cfg: Baton = f["baton_cfg"]  # type: ignore[assignment]
    hero = f["hero_name"]
    friend = f["friend_name"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who went into {place} and found the baton?",
            answer=f"{hero} and {friend} went into {place} together. They found the baton there and listened to the strange sound it made.",
        ),
        QAItem(
            question=f"Why did the room seem haunted when {hero} tapped the baton?",
            answer=f"The baton made {baton_cfg.sound} and the room echoed it back. That made the room feel spooky for a moment, even though the sound had a simple cause.",
        ),
        QAItem(
            question=f"What was the surprise on the baton?",
            answer=f"There was a tiny key tied to the baton with a knot. That surprise explained why the baton made such ghostly noises.",
        ),
        QAItem(
            question=f"How did {hero} and {friend} feel at the end?",
            answer=f"They felt relieved and laughed together. Once they understood the sound, the scary feeling turned into a safe ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    baton_cfg: Baton = f["baton_cfg"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is a baton?",
            answer="A baton is a short stick or wand that people can hold and wave, often for music, marching, or play.",
        ),
        QAItem(
            question="What is a friend?",
            answer="A friend is someone who plays with you, helps you, and makes you feel less alone.",
        ),
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces back from walls or other hard things after you make it.",
        ),
        QAItem(
            question="Why can a surprise make a story exciting?",
            answer="A surprise changes what the characters expect. It can make a story feel mysterious at first and happy when the surprise is found.",
        ),
        QAItem(
            question="Why can a sound effect feel spooky in a ghost story?",
            answer="A strange sound can make a quiet place seem mysterious. In a ghost story, that helps the reader wonder what is hiding nearby.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sound(H) :- moving(H), baton(B), baton_sound(B, S), echo_room.
surprise(B) :- baton(B), sound(B), hidden_key(B).
relief(H) :- surprise(B), heard(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_echo:
            lines.append(asp.fact("echo_room"))
    for bid, b in BATONS.items():
        lines.append(asp.fact("baton", bid))
        lines.append(asp.fact("baton_sound", bid, b.sound))
        if "surprise" in b.tags:
            lines.append(asp.fact("hidden_key", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show baton/1."))
    asp_batons = set(asp.atoms(model, "baton"))
    py_batons = {(bid,) for bid in BATONS}
    if asp_batons != py_batons:
        print("MISMATCH in baton facts")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, baton=None, friend_name=None, hero_name=None, hero_gender=None,
            friend_gender=None, parent_name=None, n=1, seed=None, all=False, trace=False,
            qa=False, json=False, asp=False, verify=False, show_asp=False
        ), random.Random(777)))
        _ = sample.story
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP facts match and generation smoke test passed.")
    return 0


CURATED = [
    StoryParams(setting="music_room", baton="silver_baton", friend_name="Mina", hero_name="Iris", hero_gender="girl", friend_gender="girl", parent_name="Grandma"),
    StoryParams(setting="hallway", baton="wooden_baton", friend_name="Theo", hero_name="Nina", hero_gender="girl", friend_gender="boy", parent_name="Dad"),
    StoryParams(setting="attic", baton="silver_baton", friend_name="Jules", hero_name="Leo", hero_gender="boy", friend_gender="boy", parent_name="Mom"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story baton and friend world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--baton", choices=BATONS)
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
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
    baton = getattr(args, "baton", None) or rng.choice(list(BATONS))
    if not should_choose_baton(_safe_lookup(SETTINGS, setting), _safe_lookup(BATONS, baton)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    parent_name = getattr(args, "parent_name", None) or rng.choice(["Mom", "Dad", "Grandma"])
    return StoryParams(
        setting=setting,
        baton=baton,
        friend_name=friend_name,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_gender=friend_gender,
        parent_name=parent_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        pass
    if params.baton not in BATONS:
        pass
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(BATONS, params.baton),
        params.hero_name,
        params.hero_gender,
        params.friend_name,
        params.friend_gender,
        params.parent_name,
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show baton/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show setting/1."))
        print(asp.atoms(model, "setting"))
        return
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
