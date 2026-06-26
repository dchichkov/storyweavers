#!/usr/bin/env python3
"""
storyworlds/worlds/wreath_moral_value_myth.py
=============================================

A tiny myth-style story world about a wreath, a moral value, and a turning
point that changes the ending image.

Premise:
- A young helper wants to make or carry a wreath for a festival, shrine, or
  blessing.
- The wreath is precious because it stands for a moral value such as honesty,
  generosity, courage, or kindness.
- A temptation, mistake, or boast threatens to spoil the wreath's meaning.
- The hero tells the truth, shares, returns, or repairs the wreath.
- The moral value becomes visible in the final scene.

This world keeps the prose concrete and state-driven:
- physical meters track things like damage, brightness, leaves, and tide
- emotional memes track pride, worry, shame, relief, trust, and gratitude
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
# Core model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    wreath: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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


@dataclass
class Setting:
    place: str
    light: str
    afford: set[str] = field(default_factory=set)
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
class Wreath:
    id: str
    label: str
    phrase: str
    value: str
    material: str
    can_be_broken: bool
    can_be_hidden: bool
    region: str = "head"
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
class Trial:
    id: str
    name: str
    temptation: str
    action: str
    consequence: str
    damage_kind: str
    risk_zone: str
    moral_value: str
    turn: str
    remedy: str
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shrine": Setting(place="the hill shrine", light="golden", afford={"carry", "offer", "hide"}),
    "grove": Setting(place="the sacred grove", light="green", afford={"weave", "carry", "offer"}),
    "harbor": Setting(place="the sea harbor", light="salt-bright", afford={"carry", "lose", "return"}),
    "courtyard": Setting(place="the temple courtyard", light="warm", afford={"weave", "carry", "offer"}),
}

WREATHS = {
    "laurel": Wreath(
        id="laurel",
        label="laurel wreath",
        phrase="a fresh laurel wreath",
        value="honor",
        material="laurel leaves",
        can_be_broken=True,
        can_be_hidden=True,
    ),
    "flowers": Wreath(
        id="flowers",
        label="flower wreath",
        phrase="a bright flower wreath",
        value="kindness",
        material="wildflowers",
        can_be_broken=True,
        can_be_hidden=True,
    ),
    "olive": Wreath(
        id="olive",
        label="olive wreath",
        phrase="an olive wreath",
        value="peace",
        material="olive branches",
        can_be_broken=True,
        can_be_hidden=True,
    ),
    "shells": Wreath(
        id="shells",
        label="shell wreath",
        phrase="a shell wreath",
        value="truth",
        material="small shells and blue thread",
        can_be_broken=False,
        can_be_hidden=True,
    ),
}

TRIALS = {
    "pride": Trial(
        id="pride",
        name="pride",
        temptation="boast that the wreath was made all alone",
        action="speak a boast",
        consequence="the others would hear the boast and feel shut out",
        damage_kind="shadowed",
        risk_zone="heart",
        moral_value="humility",
        turn="admit the help of others",
        remedy="share the credit",
        tags={"honor", "truth"},
    ),
    "greed": Trial(
        id="greed",
        name="greed",
        temptation="keep the wreath and its bright ribbon all to yourself",
        action="hide the wreath away",
        consequence="the festival altar would stay bare",
        damage_kind="hidden",
        risk_zone="hands",
        moral_value="generosity",
        turn="bring it back for all to see",
        remedy="return the wreath",
        tags={"kindness", "peace"},
    ),
    "lie": Trial(
        id="lie",
        name="lie",
        temptation="say the wreath was never touched after it fell",
        action="tell a lie",
        consequence="the stain would stay on the story",
        damage_kind="stained",
        risk_zone="tongue",
        moral_value="honesty",
        turn="tell the truth at once",
        remedy="confess and repair",
        tags={"truth"},
    ),
    "envy": Trial(
        id="envy",
        name="envy",
        temptation="wish for the other child’s wreath instead of the one offered",
        action="reach for the other wreath",
        consequence="a good gift would be spoiled by wishing",
        damage_kind="twisted",
        risk_zone="eyes",
        moral_value="contentment",
        turn="bless the other child’s gift",
        remedy="accept the given wreath",
        tags={"honor", "kindness"},
    ),
    "fear": Trial(
        id="fear",
        name="fear",
        temptation="hide behind a pillar and let the ceremony begin without speaking",
        action="step back and stay silent",
        consequence="the vow would go unsaid",
        damage_kind="dimmed",
        risk_zone="voice",
        moral_value="courage",
        turn="step forward and speak",
        remedy="offer the wreath openly",
        tags={"courage"},
    ),
}

CHARACTER_KINDS = ["girl", "boy", "mother", "father", "priestess", "priest", "queen", "king"]
NAMES = ["Ari", "Mina", "Taro", "Lena", "Suri", "Pavi", "Kian", "Niko", "Ira", "Ravi"]
TRAITS = ["small", "bright-eyed", "steady", "quick", "kind", "bold", "gentle", "curious"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
trial_value(T, V) :- trial(T), moral_value(T, V).
setting_affords(S, A) :- setting(S), affords(S, A).
valid_story(S, T, W) :- setting_affords(S, _), trial(T), wreath(W),
                        value_of(W, V), moral_value(T, V).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for wid, w in WREATHS.items():
        lines.append(asp.fact("wreath", wid))
        lines.append(asp.fact("value_of", wid, w.value))
        lines.append(asp.fact("material_of", wid, w.material))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("moral_value", tid, t.moral_value))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, trial in TRIALS.items():
            for wid, wreath in WREATHS.items():
                if wreath.value == trial.moral_value and any(tag in trial.tags for tag in wreath.value.split()):
                    combos.append((sid, tid, wid))
                elif wreath.value == trial.moral_value:
                    combos.append((sid, tid, wid))
    return combos

def explain_rejection(setting_id: str, trial_id: str, wreath_id: str) -> str:
    s, t, w = _safe_lookup(SETTINGS, setting_id), _safe_lookup(TRIALS, trial_id), _safe_lookup(WREATHS, wreath_id)
    return (
        f"(No story: {t.name} tests {t.moral_value}, but the {w.label} stands for {w.value}. "
        f"These do not fit together well enough for a mythic tale at {s.place}.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def choose_name(rng: random.Random, kind: str) -> str:
    if kind in {"mother", "father", "priestess", "priest", "queen", "king"}:
        return rng.choice(["Nia", "Orin", "Mara", "Elios", "Sela", "Thane"])
    return rng.choice(NAMES)

def article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"

def setup_lines(world: World, hero: Entity, guide: Entity, wreath: Entity, trial: Trial) -> None:
    place = world.setting.place
    world.say(
        f"Long ago, at {place}, there lived {article(hero.type)} {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} was {next(iter(hero.memes.keys()), 'steady')} and loved the sign of the {wreath.label}."
    )
    world.say(
        f"That wreath stood for {trial.moral_value}, and its leaves were bright under the {world.setting.light} light."
    )
    world.say(
        f"{guide.id} had woven it for the holy day, and {hero.id} was chosen to carry it."
    )

def simulate_trial(world: World, hero: Entity, wreath: Entity, trial: Trial) -> None:
    hero.memes[trial.name] = hero.memes.get(trial.name, 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    wreath.meters["glow"] = wreath.meters.get("glow", 0.0) - 0.25
    world.say(
        f"But on the road, {hero.id} felt the pull of {trial.name}: {trial.temptation}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} knew that would mean {trial.consequence}."
    )

def fall_or_loss(world: World, hero: Entity, wreath: Entity, trial: Trial) -> None:
    if trial.id == "fear":
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    elif trial.id == "lie":
        wreath.meters["stain"] = wreath.meters.get("stain", 0.0) + 1
    elif trial.id == "greed":
        wreath.meters["hidden"] = wreath.meters.get("hidden", 0.0) + 1
    elif trial.id == "pride":
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    elif trial.id == "envy":
        hero.memes["envy"] = hero.memes.get("envy", 0.0) + 1

def resolve(world: World, hero: Entity, guide: Entity, wreath: Entity, trial: Trial) -> None:
    if trial.id == "lie":
        hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
        world.say(
            f"Then {hero.id} stopped, bowed {hero.pronoun('possessive')} head, and told the truth."
        )
        world.say(
            f"{hero.pronoun('subject').capitalize()} washed the stain from the wreath and made it bright again."
        )
    elif trial.id == "greed":
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
        world.say(
            f"Then {hero.id} carried the wreath back to the altar and placed it where all could see."
        )
        world.say(
            f"The people smiled, because generosity had returned to the shrine."
        )
    elif trial.id == "pride":
        hero.memes["humble"] = hero.memes.get("humble", 0.0) + 1
        world.say(
            f"Then {hero.id} said that many hands had helped weave the leaves together."
        )
        world.say(
            f"{guide.id} nodded, and the wreath grew dearer when the truth was spoken."
        )
    elif trial.id == "envy":
        hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
        world.say(
            f"Then {hero.id} blessed the other child's gift and returned to the wreath that had been given."
        )
        world.say(
            f"The old wishing faded, and contentment sat softly in {hero.pronoun('possessive')} chest."
        )
    elif trial.id == "fear":
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
        world.say(
            f"Then {hero.id} stepped forward, lifted the wreath high, and spoke the vow."
        )
        world.say(
            f"The voice was small, but it carried farther than fear."
        )
    else:
        world.say(f"Then {hero.id} chose the better way and kept the wreath true.")

def finish(world: World, hero: Entity, guide: Entity, wreath: Entity, trial: Trial) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    wreath.meters["glow"] = wreath.meters.get("glow", 0.0) + 1
    world.say(
        f"In the end, the {wreath.label} shone for {trial.moral_value}, and {hero.id} was not the same child as before."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} carried it with a steadier heart, and {guide.id} walked beside {hero.pronoun('object')} like a blessing."
    )

def tell(setting: Setting, trial: Trial, wreath_cfg: Wreath, hero_kind: str, guide_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=choose_name(random.Random(7), hero_kind),
        kind="character",
        type=hero_kind,
        label="hero",
        memes={"worry": 0.0},
    ))
    guide = world.add(Entity(
        id=choose_name(random.Random(13), guide_kind),
        kind="character",
        type=guide_kind,
        label="guide",
        memes={"trust": 1.0},
    ))
    wreath = world.add(Entity(
        id="wreath",
        type="wreath",
        label=wreath_cfg.label,
        phrase=wreath_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
        meters={"glow": 1.0},
        memes={"meaning": 1.0},
    ))

    setup_lines(world, hero, guide, wreath, trial)
    world.para()
    simulate_trial(world, hero, wreath, trial)
    fall_or_loss(world, hero, wreath, trial)
    world.para()
    resolve(world, hero, guide, wreath, trial)
    world.para()
    finish(world, hero, guide, wreath, trial)

    world.facts.update(hero=hero, guide=guide, wreath=wreath, trial=trial, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Story QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, trial, wreath = f["hero"], f["guide"], f["trial"], f["wreath"]
    return [
        f'Write a short myth for a child about {hero.id}, a {hero.type}, a {trial.name}, and {wreath.label}.',
        f"Tell a gentle legend where {hero.id} must choose {trial.moral_value} over {trial.temptation}.",
        f'Write a story with a sacred {wreath.label} that ends in courage, honesty, or kindness.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, trial, wreath = f["hero"], f["guide"], f["trial"], f["wreath"]
    return [
        QAItem(
            question=f"What did {hero.id} carry in the story?",
            answer=f"{hero.id} carried the {wreath.label}, a sign of {trial.moral_value}.",
        ),
        QAItem(
            question=f"What was the moral value in the {wreath.label}?",
            answer=f"The wreath stood for {trial.moral_value}, so the choice had to be truthful and good.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the wreath?",
            answer=f"{guide.id} made or guarded the wreath and walked beside {hero.id}.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wreath?",
            answer="A wreath is a ring made from leaves, flowers, branches, or shells, often used in ceremonies or on doors.",
        ),
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth and not pretending something false is real.",
        ),
        QAItem(
            question="What is generosity?",
            answer="Generosity means sharing, giving, and letting others enjoy a good thing too.",
        ),
        QAItem(
            question="What is courage?",
            answer="Courage means doing the right thing even when you feel nervous or afraid.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    trial: str
    wreath: str
    hero_kind: str
    guide_kind: str
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


CURATED = [
    StoryParams("shrine", "lie", "shells", "girl", "priestess"),
    StoryParams("grove", "greed", "flowers", "boy", "priest"),
    StoryParams("courtyard", "pride", "laurel", "girl", "queen"),
    StoryParams("harbor", "fear", "olive", "boy", "mother"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic wreath story world with moral value turns.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--trial", choices=sorted(TRIALS))
    ap.add_argument("--wreath", choices=sorted(WREATHS))
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--guide-kind", choices=["mother", "father", "priestess", "priest", "queen", "king"])
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
    combos = [c for c in combos
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "trial", None) is None or c[1] == getattr(args, "trial", None))
              and (getattr(args, "wreath", None) is None or c[2] == getattr(args, "wreath", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, trial, wreath = rng.choice(list(combos))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(["girl", "boy"])
    guide_kind = getattr(args, "guide_kind", None) or rng.choice(["mother", "father", "priestess", "priest", "queen", "king"])
    return StoryParams(setting, trial, wreath, hero_kind, guide_kind)

def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TRIALS, params.trial), _safe_lookup(WREATHS, params.wreath), params.hero_kind, params.guide_kind)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.setting} / {p.trial} / {p.wreath}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
