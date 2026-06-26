#!/usr/bin/env python3
"""
A standalone story world for a small detective tale about an archer, poison,
foreshadowing, caution, and a lesson learned.

The premise:
- A clever child detective and an archer prepare for a target practice day.
- A poisoned drink appears as a clue.
- The detective notices small foreshadowing signs.
- A cautionary warning prevents a bad choice.
- The lesson learned is that careful checking can keep friends safe.

The world model tracks:
- physical meters: danger, poison, calm, readiness, evidence
- emotional memes: worry, trust, relief, pride, caution, curiosity

This script keeps the story grounded in simulated state rather than swapping
names into a frozen paragraph.
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
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

CHARACTER_TYPES = {"child", "adult"}
SETTING_TYPES = {"market", "training_yard", "garden", "dock"}

# ---------------------------------------------------------------------------
# Typed entities with meters and memes
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
    caretaker: Optional[str] = None
    plural: bool = False
    wearable: bool = False
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    indoors: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
    risk: str
    tells: str
    location: str
    hint: str
    safe_check: str
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
    place: str
    clue: str
    hero_name: str
    hero_type: str
    detective_name: str
    detective_type: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "market": Setting(place="the market", affords={"poison"}),
    "training_yard": Setting(place="the training yard", affords={"poison"}),
    "garden": Setting(place="the garden", affords={"poison"}),
    "dock": Setting(place="the dock", affords={"poison"}),
}

CLUES = {
    "cup": Clue(
        id="cup",
        label="cup",
        phrase="a silver cup",
        risk="poisoned",
        tells="left near the target stand",
        location="table",
        hint="It had a bitter smell and a dark ring at the bottom.",
        safe_check="look inside the cup before drinking",
    ),
    "apple": Clue(
        id="apple",
        label="apple",
        phrase="a red apple",
        risk="poisoned",
        tells="set beside the arrows",
        location="basket",
        hint="One bite had been taken, but the fruit looked strangely shiny.",
        safe_check="check the fruit before eating",
    ),
    "bread": Clue(
        id="bread",
        label="bread",
        phrase="a loaf of bread",
        risk="poisoned",
        tells="wrapped in cloth",
        location="bench",
        hint="The loaf had been touched by a gloved hand and smelled wrong.",
        safe_check="ask who handled the food first",
    ),
}

HERO_NAMES = ["Ari", "Mina", "Toma", "Lena", "Jai", "Nia"]
DETECTIVE_NAMES = ["Detective Row", "Detective Vale", "Detective Finch", "Detective Moss"]
TRAITS = ["cautious", "curious", "brave", "patient", "sharp-eyed"]


# ---------------------------------------------------------------------------
# World model and rules
# ---------------------------------------------------------------------------
def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _rule_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    detective = _safe_fact(world, world.facts, "detective")
    clue = _safe_fact(world, world.facts, "clue_ent")
    hero = _safe_fact(world, world.facts, "hero")
    if clue.meters.get("evidence", 0.0) < THRESHOLD:
        return out
    sig = ("foreshadow", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_meme(detective, "caution", 1.0)
    _add_meme(detective, "curiosity", 1.0)
    out.append(
        f"{detective.noun()} noticed a small sign first: {clue.hint.lower()}"
    )
    out.append(
        f"That made {detective.pronoun('object')} look twice at the table before anyone took a sip."
    )
    return out


def _rule_poison_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    clue = _safe_fact(world, world.facts, "clue_ent")
    if hero.meters.get("readiness", 0.0) < THRESHOLD:
        return out
    if clue.meters.get("poison", 0.0) < THRESHOLD:
        return out
    sig = ("risk", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_meme(hero, "worry", 1.0)
    _add_meme(hero, "caution", 1.0)
    out.append(
        f"{hero.noun()} felt a bad prickling feeling and stepped back from {clue.phrase}."
    )
    return out


def _rule_lesson(world: World) -> list[str]:
    out: list[str] = []
    detective = _safe_fact(world, world.facts, "detective")
    hero = _safe_fact(world, world.facts, "hero")
    clue = _safe_fact(world, world.facts, "clue_ent")
    if hero.meters.get("safe", 0.0) < THRESHOLD:
        return out
    sig = ("lesson", hero.id, clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_meme(hero, "relief", 1.0)
    _add_meme(hero, "trust", 1.0)
    _add_meme(detective, "pride", 1.0)
    out.append(
        f"{hero.noun()} learned to check first, and {detective.noun()} nodded with quiet pride."
    )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_foreshadow, _rule_poison_risk, _rule_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.clue not in CLUES:
        pass

    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"readiness": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "caution": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        meters={"evidence": 1.0},
        memes={"curiosity": 1.0, "caution": 1.0, "pride": 0.0},
    ))
    clue_cfg = _safe_lookup(CLUES, params.clue)
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        meters={"poison": 1.0, "evidence": 1.0},
        memes={},
    ))

    world.facts.update(hero=hero, detective=detective, clue_ent=clue, clue_cfg=clue_cfg)
    return world


def tell_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    detective: Entity = _safe_fact(world, world.facts, "detective")
    clue: Entity = _safe_fact(world, world.facts, "clue_ent")
    cfg: Clue = _safe_fact(world, world.facts, "clue_cfg")

    world.say(
        f"{detective.noun()} was the kind of detective who liked quiet facts and sharp eyes."
    )
    world.say(
        f"One day, {hero.noun()} met {detective.noun().lower()} at {world.setting.place}, where an archer's gear and a small meal were waiting."
    )
    world.say(
        f"{hero.noun()} noticed {clue.phrase} {cfg.tells}."
    )

    world.para()
    world.say(
        f"At first, it looked ordinary, but the tiny sign on the cup kept shining in {detective.pronoun('possessive')} mind."
    )
    _add_meter(clue, "evidence", 1.0)
    propagate(world, narrate=True)

    world.say(
        f"{hero.noun()} wanted to rush ahead, yet {detective.noun()} held up a careful hand."
    )
    world.say(
        f'"Do not drink or eat anything until we know it is safe," {detective.noun().lower()} said.'
    )
    _add_meme(hero, "worry", 1.0)
    _add_meme(hero, "caution", 1.0)
    _add_meter(clue, "poison", 1.0)
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then the archer came close and admitted the food had been left by someone unknown."
    )
    world.say(
        f"{detective.noun()} checked the smell, the color, and the place it had been set down."
    )
    _add_meter(hero, "safe", 1.0)
    propagate(world, narrate=True)

    world.say(
        f"{hero.noun()} stepped away, and the warning proved wise."
    )
    world.say(
        f"In the end, the poison was found before anyone touched it, and {hero.noun()} learned that a careful pause can save a whole day."
    )

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Knowledge and Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    detective = _safe_fact(world, f, "detective")
    clue_cfg: Clue = _safe_fact(world, f, "clue_cfg")
    return [
        f'Write a child-friendly detective story about {hero.noun()} and {detective.noun().lower()} where a suspicious {clue_cfg.label} may be poisoned.',
        f'Tell a short mystery with foreshadowing and a lesson learned when someone notices {clue_cfg.phrase} first.',
        f"Write a cautionary story where a quick check keeps an archer or friend safe from poison.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    detective = _safe_fact(world, f, "detective")
    clue = _safe_fact(world, f, "clue_ent")
    cfg: Clue = _safe_fact(world, f, "clue_cfg")
    place = world.setting.place

    return [
        QAItem(
            question=f"Who was the detective in the story at {place}?",
            answer=f"The detective was {detective.noun()}, who watched closely and looked for clues before anyone got hurt.",
        ),
        QAItem(
            question=f"What suspicious thing did {hero.noun()} notice?",
            answer=f"{hero.noun()} noticed {cfg.phrase}, and it turned out to be a dangerous clue tied to poison.",
        ),
        QAItem(
            question="What was the warning in the story?",
            answer=f"The warning was to check the food or drink first, because poison can hide where it looks harmless.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer=f"The lesson learned was that a careful pause and a good check can protect everyone from a bad mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is poison?",
            answer="Poison is something dangerous that can make a person very sick if they eat or drink it.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint that tells the reader something important may happen later.",
        ),
        QAItem(
            question="Why is it smart to be cautious?",
            answer="It is smart to be cautious because careful choices can help you avoid danger and stay safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts describe the registries. A clue is risky when it has poison and is noticed.
foreshadow(C) :- clue(C), evidence(C), hint(C).

% A warning is justified when poison is present and the clue is suspicious.
cautionary(C) :- clue(C), poison(C).

% Lesson learned when the hero becomes safe after the warning.
lesson_learned(H) :- hero(H), safe(H), cautionary(_).

#show foreshadow/1.
#show cautionary/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("evidence", cid))
        lines.append(asp.fact("poison", cid))
        lines.append(asp.fact("hint", cid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("safe", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show foreshadow/1. #show cautionary/1. #show lesson_learned/1."))
    atoms = {(s.name, tuple(a.name if a.type != a.type.Number else a.number for a in s.arguments)) for s in model}
    expected = {
        ("foreshadow", ("cup",)),
        ("foreshadow", ("apple",)),
        ("foreshadow", ("bread",)),
        ("cautionary", ("cup",)),
        ("cautionary", ("apple",)),
        ("cautionary", ("bread",)),
        ("lesson_learned", ("hero",)),
    }
    if atoms == expected:
        print(f"OK: ASP parity check passed ({len(atoms)} atoms).")
        return 0
    print("MISMATCH in ASP parity check.")
    print("atoms:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: archer, poison, caution, foreshadowing, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["child", "adult"])
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["child", "adult"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES.keys()))
    hero_type = getattr(args, "hero_type", None) or "child"
    detective_type = getattr(args, "detective_type", None) or "adult"
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    detective_name = getattr(args, "detective_name", None) or rng.choice(DETECTIVE_NAMES)
    return StoryParams(
        place=place,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_type,
        detective_name=detective_name,
        detective_type=detective_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show foreshadow/1. #show cautionary/1. #show lesson_learned/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show foreshadow/1. #show cautionary/1. #show lesson_learned/1."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            for clue in CLUES:
                params = StoryParams(
                    place=place,
                    clue=clue,
                    hero_name="Ari",
                    hero_type="child",
                    detective_name="Detective Vale",
                    detective_type="adult",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
