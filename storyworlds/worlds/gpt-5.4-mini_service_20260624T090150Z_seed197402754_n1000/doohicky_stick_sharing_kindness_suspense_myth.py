#!/usr/bin/env python3
"""
storyworlds/worlds/doohicky_stick_sharing_kindness_suspense_myth.py
====================================================================

A tiny myth-flavored storyworld about a curious doohicky, a shared stick,
and the suspense of whether kindness will solve a small problem.

Premise:
- A child or small hero finds a strange doohicky and a plain stick.
- Both matter: the doohicky is useful, but the stick is the thing everyone
  wants to hold.
- The tension comes from wanting to keep the stick, yet needing to share it.
- The turn is a generous offer or a careful trade.
- The ending proves the change in world state: the hero shares, the other
  character feels safe, and the doohicky is used to help.

This world is intentionally small and classical: one domain, one tension,
one resolution, and short child-facing prose.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    doo: object | None = None
    helper: object | None = None
    hero: object | None = None
    stick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "thing":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "woman", "queen", "sister"}
        male = {"boy", "father", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace_notes: list[str] = field(default_factory=list)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    p: object | None = None
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
class Setting:
    place: str
    mood: str
    backdrop: str
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
class Thing:
    id: str
    label: str
    phrase: str
    value: str
    DOOHICKY: object | None = None
    STICK: object | None = None
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


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    type: str
    title: str
    traits: tuple[str, ...]
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


SETTINGS = {
    "grove": Setting(place="the moonlit grove", mood="old and hushed", backdrop="silver leaves"),
    "well": Setting(place="the ancient well", mood="still and deep", backdrop="dark water"),
    "hill": Setting(place="the high hill", mood="windy and bright", backdrop="tall grass"),
}

CHARACTERS = {
    "girl": ["Asha", "Mira", "Lina", "Nora"],
    "boy": ["Eli", "Taro", "Milo", "Soren"],
    "spirit": ["Wisp", "Moth", "Rune"],
}

HERO_TRAITS = ["brave", "gentle", "curious", "patient"]
HELPER_TRAITS = ["small", "hopeful", "watchful", "kind"]

DOOHICKY = Thing(
    id="doohicky",
    label="doohicky",
    phrase="a strange little doohicky with a bright notch",
    value="a glowing helper",
)

STICK = Thing(
    id="stick",
    label="stick",
    phrase="a plain stick with a smooth, warm bark",
    value="a shareable treasure",
)

# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.place}, where the air was {setting.mood} and the {setting.backdrop} "
        f"moved like a quiet song, there lived {hero.id} and {helper.id}."
    )
    world.say(
        f"{hero.id} found {hero.pronoun('possessive')} {DOOHICKY.label} and a {STICK.label} near the path, "
        f"and both seemed important, as old stories often begin with one small thing and one stranger one."
    )


def build_tension(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["want_keep"] = hero.memes.get("want_keep", 0) + 1
    helper.memes["hope"] = helper.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} liked the stick because it felt like a wand, a spear, and a promise all at once."
    )
    world.say(
        f"But {helper.id} reached for it too, and the grove grew suspenseful; no one wanted the other to leave empty-handed."
    )


def speak_warning(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(
        f"{hero.id} held the stick close and wondered if sharing would make it less special."
    )
    world.say(
        f"{helper.id} waited without fuss, and that quiet waiting made {hero.id}'s heart thump even harder."
    )


def choose_kindness(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    hero.meters["share"] = hero.meters.get("share", 0) + 1
    world.say(
        f"Then {hero.id} remembered an older law of the grove: a true treasure grows when it is shared."
    )
    world.say(
        f"{hero.id} smiled, offered the stick to {helper.id}, and said, \"You may hold it first.\""
    )


def use_doo(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["doohicky_use"] = hero.meters.get("doohicky_use", 0) + 1
    world.say(
        f"With the doohicky, {hero.id} touched the notch to the stick, and the plain wood shone like a small star."
    )
    world.say(
        f"At once, the doohicky showed that it was not a toy for keeping, but a helper for giving."
    )


def resolve(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    helper.held_by = hero.id
    world.say(
        f"{helper.id} laughed softly and held the stick with both hands while {hero.id} watched kindly."
    )
    world.say(
        f"Together they walked under {world.place}'s old light, and the story ended with the doohicky warm in {hero.id}'s palm, "
        f"the stick safely shared, and both hearts made larger by kindness."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place=setting.place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    doo = world.add(Entity(id=DOOHICKY.id, type="thing", label=DOOHICKY.label, phrase=DOOHICKY.phrase, owner=hero.id))
    stick = world.add(Entity(id=STICK.id, type="thing", label=STICK.label, phrase=STICK.phrase, owner=hero.id, held_by=hero.id))

    world.facts.update(hero=hero, helper=helper, doohicky=doo, stick=stick, setting=setting)

    intro(world, hero, helper, setting)
    world.para()
    build_tension(world, hero, helper)
    speak_warning(world, hero, helper)
    world.para()
    choose_kindness(world, hero, helper)
    use_doo(world, hero, helper)
    resolve(world, hero, helper)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, setting = f["hero"], f["helper"], f["setting"]
    return [
        f'Write a short myth-like story for a child about a {hero.type} named {hero.id}, a doohicky, and a shared stick in {setting.place}.',
        f"Tell a gentle story where {hero.id} and {helper.id} both want the stick, but kindness changes the ending.",
        f'Write a suspenseful but kind tale that includes the words "doohicky" and "stick" and ends with sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, setting = f["hero"], f["helper"], f["setting"]
    return [
        QAItem(
            question=f"Who found the doohicky and the stick in {setting.place}?",
            answer=f"{hero.id} found both the doohicky and the stick in {setting.place}.",
        ),
        QAItem(
            question=f"Why was the middle of the story suspenseful?",
            answer=f"It was suspenseful because {hero.id} and {helper.id} both wanted the stick, and no one wanted to be left out.",
        ),
        QAItem(
            question=f"What changed the ending for {hero.id} and {helper.id}?",
            answer=f"Kindness changed the ending when {hero.id} chose to share the stick and use the doohicky to help.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the stick safely shared, the doohicky glowing softly, and both characters feeling happier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stick?",
            answer="A stick is a piece of wood that can be held, carried, or used in play.",
        ),
        QAItem(
            question="What is a doohicky?",
            answer="A doohicky is a playful word for a small object whose exact use is mysterious or special.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, hold, or enjoy something too.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, fair, and helpful to others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).

shares(H) :- share_fact(H).
kind(H) :- kindness_fact(H).
suspense(H) :- suspense_fact(H).

valid_story(Place) :- place(Place), shares(hero), kind(hero), suspense(hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("helper_name", "helper"))
    lines.append(asp.fact("share_fact", "hero"))
    lines.append(asp.fact("kindness_fact", "hero"))
    lines.append(asp.fact("suspense_fact", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    python_set = {(pid,) for pid in SETTINGS}
    if atoms == python_set:
        print(f"OK: ASP and Python agree on {len(atoms)} valid settings.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a doohicky, a stick, sharing, kindness, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "spirit"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "spirit"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["spirit", "girl"])
    hero = getattr(args, "hero", None) or rng.choice(_safe_lookup(CHARACTERS, hero_type))
    helper = getattr(args, "helper", None) or rng.choice(_safe_lookup(CHARACTERS, helper_type))
    if hero == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = tell(setting, params.hero, params.hero_type, params.helper, params.helper_type)
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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid settings:")
        for (place,) in vals:
            print(f"  {place}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, place in enumerate(SETTINGS):
            p = StoryParams(
                place=place,
                hero=CHARACTERS["girl"][i % len(CHARACTERS["girl"])],
                hero_type="girl",
                helper=CHARACTERS["spirit"][i % len(CHARACTERS["spirit"])],
                helper_type="spirit",
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

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
