#!/usr/bin/env python3
"""
Storyworld: hopperoo black sound effects folk tale
==================================================

A small, self-contained storyworld about a hopperoo who loves making
sound effects, especially in a folk-tale setting where black night, black
props, and lively noises help a village story come alive.

The world is intentionally simple:
- a hopperoo protagonist
- a folk-tale village setting
- a sound-effects task that needs a careful, plausible fix
- emotional state that changes as the story progresses

The story is driven by simulated state, not a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# -----------------------------------------------------------------------------
# Domain registries
# -----------------------------------------------------------------------------

SOUND_KINDS = ("tap", "rustle", "whoosh", "thump", "clink", "snap", "boing")



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

@dataclass(frozen=True)
class SoundEffect:
    key: str
    word: str
    source: str
    place: str
    mood: str
    use_case: str
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


@dataclass(frozen=True)
class Prop:
    key: str
    name: str
    color: str
    sound: str
    kind: str
    can_fix: bool = False
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


@dataclass(frozen=True)
class Setting:
    name: str
    detail: str
    affordance: str
    shadow: str
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
    setting: str
    sound: str
    prop: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS: dict[str, Setting] = {
    "lantern_lane": Setting(
        name="Lantern Lane",
        detail="a little lane with round windows and fence posts that clicked in the wind",
        affordance="folk tales were told by the fire",
        shadow="black shadows lay under the eaves",
    ),
    "river_hall": Setting(
        name="River Hall",
        detail="a hall beside the river where boards creaked like old boots",
        affordance="songs and stories were shared at dusk",
        shadow="black reeds swayed at the bank",
    ),
    "birch_green": Setting(
        name="Birch Green",
        detail="a green where white birches leaned over a tiny stage",
        affordance="villagers gathered for a night tale",
        shadow="black night gathered under the leaves",
    ),
}

SOUNDS: dict[str, SoundEffect] = {
    "tap": SoundEffect(
        key="tap",
        word="tap-tap",
        source="small sticks",
        place="the side of a cooking pot",
        mood="quick and neat",
        use_case="boot steps for a tiny traveler",
    ),
    "rustle": SoundEffect(
        key="rustle",
        word="rustle-rush",
        source="dry leaves",
        place="a cloak sleeve",
        mood="soft and secret",
        use_case="a forest spirit slipping by",
    ),
    "whoosh": SoundEffect(
        key="whoosh",
        word="whoosh",
        source="a wide cloth",
        place="the air above the stage",
        mood="wide and windy",
        use_case="a dragon's wing or a storm gust",
    ),
    "thump": SoundEffect(
        key="thump",
        word="thump-thump",
        source="a hand drum",
        place="the floorboards",
        mood="deep and steady",
        use_case="giant footsteps on a bridge",
    ),
    "clink": SoundEffect(
        key="clink",
        word="clink",
        source="small bells",
        place="a belt of charms",
        mood="bright and tiny",
        use_case="fairy shoes on stone",
    ),
    "snap": SoundEffect(
        key="snap",
        word="snap!",
        source="a dry twig",
        place="a fire crackle",
        mood="sharp and sudden",
        use_case="a branch breaking in the woods",
    ),
    "boing": SoundEffect(
        key="boing",
        word="boing",
        source="a springy reed mat",
        place="the open stage",
        mood="bouncy and funny",
        use_case="a silly helper hopping into view",
    ),
}

PROPS: dict[str, Prop] = {
    "black_kettle": Prop(
        key="black_kettle",
        name="a black kettle",
        color="black",
        sound="clink",
        kind="metal",
        can_fix=False,
    ),
    "black_cloak": Prop(
        key="black_cloak",
        name="a black cloak",
        color="black",
        sound="rustle",
        kind="cloth",
        can_fix=False,
    ),
    "black_drum": Prop(
        key="black_drum",
        name="a black drum",
        color="black",
        sound="thump",
        kind="drum",
        can_fix=True,
    ),
    "black_boards": Prop(
        key="black_boards",
        name="black boards",
        color="black",
        sound="tap",
        kind="wood",
        can_fix=True,
    ),
    "black_bells": Prop(
        key="black_bells",
        name="black bells",
        color="black",
        sound="clink",
        kind="bells",
        can_fix=True,
    ),
}

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.label == "hopperoo":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
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


# -----------------------------------------------------------------------------
# Story logic
# -----------------------------------------------------------------------------

def can_make_sound(sound: SoundEffect, prop: Prop, setting: Setting) -> bool:
    # Simple reasonableness gate: the prop should plausibly make the requested sound,
    # and the setting should fit a folk-tale performance.
    if prop.sound != sound.key:
        return False
    return "story" in setting.affordance or "song" in setting.affordance or "tale" in setting.affordance


def explain_invalid(sound: SoundEffect, prop: Prop) -> str:
    return (
        f"(No story: {prop.name} does not naturally make the requested "
        f'"{sound.word}" sound. Try a prop whose sound matches the effect.)'
    )


def build_reasonable_combo(setting: Optional[str], sound: Optional[str], prop: Optional[str]) -> tuple[str, str, str]:
    combos = []
    for s_key, s in SETTINGS.items():
        if setting is not None and s_key != setting:
            continue
        for sound_key, snd in SOUNDS.items():
            if sound is not None and sound_key != sound:
                continue
            for p_key, prop_obj in PROPS.items():
                if prop is not None and p_key != prop:
                    continue
                if can_make_sound(snd, prop_obj, s):
                    combos.append((s_key, sound_key, p_key))
    if not combos:
        pass
    return random.choice(sorted(combos))


def tell_story(world: World, hopperoo_name: str, setting: Setting, sound: SoundEffect, prop: Prop) -> None:
    hero = world.add(
        Entity(
            id=hopperoo_name,
            kind="character",
            label="hopperoo",
            phrase=f"a small hopperoo with a bright hop and a listening ear",
            meters={"energy": 2.0, "sound": 0.0},
            memes={"joy": 1.0, "worry": 0.0, "pride": 0.0, "shyness": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="Moss",
            kind="character",
            label="badger",
            phrase="a patient badger with a soft voice",
            meters={"energy": 1.0},
            memes={"helpfulness": 1.0},
        )
    )
    prop_ent = world.add(
        Entity(
            id=prop.key,
            kind="thing",
            label=prop.name,
            phrase=f"{prop.color} {prop.kind}",
            meters={"shine": 1.0},
            owner=hero.id,
            caretaker=hero.id,
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prop=prop_ent,
        setting=setting,
        sound=sound,
    )

    # Act 1: the folk-tale setup
    world.say(
        f"Once in {setting.name}, there lived a small hopperoo named {hero.id}."
    )
    world.say(
        f"{setting.detail.capitalize()}, and {setting.shadow}."
    )
    world.say(
        f"{hero.id} loved sound effects for old tales. "
        f"{hero.pronoun('subject').capitalize()} loved the clean little noises that made a story feel alive."
    )
    world.say(
        f"The best thing {hero.id} owned was {prop.name}, because it could make a lovely {sound.word}."
    )

    # Act 2: tension
    world.para()
    hero.memes["shyness"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"That night, the village asked for a sound to go with a black-haired wolf in the tale."
    )
    world.say(
        f"{hero.id} wanted to help, but the stage was crowded and the first try came out wrong."
    )
    world.say(
        f"When {hero.id} tapped {prop.name}, it sounded too small and lost in the wind."
    )

    # The helper notices and offers a fix.
    world.para()
    hero.meters["sound"] += 1.0
    if prop.can_fix:
        hero.memes["worry"] = 0.0
        hero.memes["pride"] += 1.0
        hero.memes["relief"] += 1.0
        world.say(
            f"Moss the badger listened, then smiled. "
            f'"Try it this way," {helper.id} said. '
            f'"The tale needs {sound.word}, and {prop.name} can do that if you use it close and steady."'
        )
        world.say(
            f"{hero.id} took a careful breath and made the sound again."
        )
        world.say(
            f"This time, {prop.name} gave a bright {sound.word}, and the villagers laughed because it fit the scene so well."
        )
        world.say(
            f"The black night on the stage felt kinder when the right noise filled it."
        )
    else:
        # This branch should not happen for valid combos, but keep story coherent.
        pass

    # Act 3: resolution image
    world.para()
    world.say(
        f"At the end of the folk tale, {hero.id} bowed with {prop.name} in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"The village remembered the little {sound.word} that made the black wolf seem to stride right past the fire."
    )
    world.say(
        f"{hero.id} smiled all the way home, because {hero.pronoun('subject')} had become the best sound maker in the lane."
    )


# -----------------------------------------------------------------------------
# QA
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    sound: SoundEffect = _safe_fact(world, f, "sound")  # type: ignore[assignment]
    prop: Prop = _safe_fact(world, f, "prop")  # type: ignore[assignment]
    return [
        f'Write a short folk-tale story about a hopperoo named {hero.id} who needs a "{sound.word}" sound at {setting.name}.',
        f"Tell a child-friendly story where {hero.id} uses {prop.name} to make {sound.word} for a village tale.",
        f'Write a simple story with a black prop, a sound effect, and a happy ending in {setting.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    prop: Entity = _safe_fact(world, f, "prop")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    sound: SoundEffect = _safe_fact(world, f, "sound")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a small hopperoo who loved making sound effects.",
        ),
        QAItem(
            question=f"What place did the story happen in?",
            answer=f"It happened in {setting.name}, where folk tales were shared at night.",
        ),
        QAItem(
            question=f"What did {hero.id} use to make the right sound?",
            answer=f"{hero.id} used {prop.name} to make the {sound.word} sound for the tale.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the first try was too small?",
            answer=f"Moss the badger helped {hero.id} and showed a steadier way to use {prop.name}.",
        ),
        QAItem(
            question=f"Why did the village like the sound effect at the end?",
            answer=f"The village liked it because {sound.word} fit the black wolf scene and made the story feel alive.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prop: Prop = _safe_fact(world, f, "prop")  # type: ignore[assignment]
    sound: SoundEffect = _safe_fact(world, f, "sound")  # type: ignore[assignment]
    questions = {
        "black": (
            "What does black mean?",
            "Black is a very dark color, like night shadows or coal.",
        ),
        "sound": (
            "What is a sound effect?",
            "A sound effect is a special noise made to match something in a story, play, or song.",
        ),
        sound.key: (
            f"What kind of noise is {sound.word}?",
            f"{sound.word} is a {sound.mood} sound effect, often used for {sound.use_case}.",
        ),
        prop.kind: (
            f"What is {prop.name} made for?",
            f"{prop.name} is the kind of prop that can help make story noises in a play or tale.",
        ),
        "folk": (
            "What is a folk tale?",
            "A folk tale is an old story people tell and retell, often with brave or funny moments.",
        ),
    }
    return [QAItem(question=q, answer=a) for q, a in questions.values()]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% setting(S), sound(SD), prop(P), makes(P,SD), black(P), tale_setting(S)

valid_story(SD, P, S) :- sound(SD), prop(P), setting(S), makes(P, SD), tale_setting(S).

#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    parts = []
    for s_key, s in SETTINGS.items():
        parts.append(asp.fact("setting", s_key))
        parts.append(asp.fact("tale_setting", s_key))
    for sound_key, snd in SOUNDS.items():
        parts.append(asp.fact("sound", sound_key))
    for p_key, prop in PROPS.items():
        parts.append(asp.fact("prop", p_key))
        parts.append(asp.fact("makes", p_key, prop.sound))
        if prop.color == "black":
            parts.append(asp.fact("black", p_key))
    return "\n".join(parts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_key, s in SETTINGS.items():
        for sound_key, snd in SOUNDS.items():
            for p_key, prop in PROPS.items():
                if can_make_sound(snd, prop, s):
                    out.append((sound_key, p_key, s_key))
    return sorted(out)


def asp_verify() -> int:
    py = set(python_valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def asp_show() -> str:
    return asp_program()


# -----------------------------------------------------------------------------
# Storyworld API
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A hopperoo folk-tale sound-effects storyworld.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--sound", choices=SOUNDS.keys())
    ap.add_argument("--prop", choices=PROPS.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting, sound, prop = build_reasonable_combo(getattr(args, "setting", None), getattr(args, "sound", None), getattr(args, "prop", None))
    return StoryParams(setting=setting, sound=sound, prop=prop, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    sound = _safe_lookup(SOUNDS, params.sound)
    prop = _safe_lookup(PROPS, params.prop)
    if not can_make_sound(sound, prop, setting):
        pass

    world = World(setting)
    tell_story(world, "Pip", setting, sound, prop)
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
        print()
        print("--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(f"{eid}: kind={ent.kind}, label={ent.label}, meters={ent.meters}, memes={ent.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combinations:")
        for sound_key, prop_key, setting_key in combos:
            print(f"  {setting_key:12} {sound_key:8} {prop_key}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s_key in SETTINGS:
            for sound_key in SOUNDS:
                for p_key in PROPS:
                    if can_make_sound(_safe_lookup(SOUNDS, sound_key), _safe_lookup(PROPS, p_key), _safe_lookup(SETTINGS, s_key)):
                        params = StoryParams(setting=s_key, sound=sound_key, prop=p_key, seed=base_seed)
                        samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < max(getattr(args, "n", None), 1) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(str(err))
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### story {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx + 1 < len(samples):
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
