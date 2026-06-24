#!/usr/bin/env python3
"""
storyworlds/worlds/gristle_whir_real_ist_dialogue_ghost_story.py
===============================================================

A small ghost-story world with dialogue, built from the seed words
"gristle", "whir", and "real-ist".

Premise:
- A child who thinks only real things matter hears a strange whir in an old
  house.
- A gentle ghost tries to prove it is real.
- The child starts as a real-ist skeptic, then learns to trust what they can
  hear, see, and feel.
- Dialogue carries the turn and the ending image.

The world is intentionally tiny and classical: a few entities, a few state
variables, and one clear resolution.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ghost: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    mood: str
    source: str
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
class Action:
    id: str
    verb: str
    question: str
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
class Prize:
    id: str
    label: str
    phrase: str
    danger: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty", source="a small fan"),
    "hall": Setting(place="the hallway", mood="blue-dark", source="the old radiator"),
    "cellar": Setting(place="the cellar", mood="cool", source="a loose vent"),
}

ACTIONS = {
    "listen": Action(
        id="listen",
        verb="listen for the sound",
        question="What makes the strange sound in the house?",
        tags={"sound", "ghost"},
    ),
    "peek": Action(
        id="peek",
        verb="peek into the dark corner",
        question="What does the child want to look at?",
        tags={"dark", "ghost"},
    ),
    "follow": Action(
        id="follow",
        verb="follow the whir",
        question="What does the child follow in the house?",
        tags={"sound", "whir"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        danger="the dark",
    ),
    "blanket": Prize(
        id="blanket",
        label="blanket",
        phrase="a warm blue blanket",
        danger="the cold air",
    ),
    "bell": Prize(
        id="bell",
        label="bell",
        phrase="a tiny silver bell",
        danger="the rattling drafts",
    ),
}

NAMES = ["Mia", "Ivy", "Noah", "Eli", "Nora", "Theo", "Luna", "Ada"]
PARENTS = ["mother", "father", "grandma", "grandpa"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, act, prize) for place in SETTINGS for act in ACTIONS for prize in PRIZES]


def explain_rejection() -> str:
    return "(No story: this tiny ghost world expects a place, an action, and a prize from the registries.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small ghost-story world with dialogue, whirs, and a real-ist child."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        parent=getattr(args, "parent", None) or rng.choice(PARENTS),
    )


def _setup(world: World, hero: Entity, parent: Entity, ghost: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} was a small real-ist child who said only real things mattered."
    )
    world.say(
        f"One night, {hero.id} went to {world.setting.place} with {hero.pronoun('possessive')} {parent.type if parent.type in {'mother','father'} else parent.label}."
    )
    world.say(
        f"The air was {world.setting.mood}, and {world.setting.source} made a soft whir-whir sound."
    )
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} {prize.label} close and listened."
    )
    hero.memes["doubt"] += 1
    hero.memes["curiosity"] += 1
    ghost.memes["waiting"] += 1


def _first_turn(world: World, hero: Entity, ghost: Entity, action: Action) -> None:
    hero.memes["fear"] += 1
    world.say(
        f'"Did you hear that?" {hero.id} whispered.'
    )
    world.say(
        f'"I did," said the ghost. "That was the whir of the house, and I am real."'
    )
    world.say(
        f'{hero.id} frowned. "You sound like a joke," {hero.id} said, "and I am a real-ist."'
    )
    ghost.memes["hurt"] += 1
    ghost.meters["glow"] += 1
    world.say(
        f'"I know," said the ghost, "but I can still speak, and I can still help."'
    )
    world.say(
        f'{hero.id} took one careful step toward {action.verb}.'
    )


def _middle_turn(world: World, hero: Entity, ghost: Entity, prize: Entity) -> None:
    hero.meters["dark"] = hero.meters.get("dark", 0.0) + 1
    hero.meters["sound"] = hero.meters.get("sound", 0.0) + 1
    world.say(
        f"Then the floor gave a tiny gristle-crack under {hero.id}'s shoe."
    )
    world.say(
        f'"What was that?" {hero.id} asked.'
    )
    world.say(
        f'"Only an old board," said the ghost. "Old things talk in funny ways."'
    )
    world.say(
        f'The {prize.label} in {hero.id}\'s hand shook a little, but the ghost floated closer and pointed.'
    )
    world.say(
        f'"See? The whir comes from the fan, not from fear," said the ghost.'
    )


def _resolution(world: World, hero: Entity, parent: Entity, ghost: Entity, prize: Entity) -> None:
    hero.memes["doubt"] = 0.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    ghost.memes["hurt"] = 0.0
    world.say(
        f'"You really are real," {hero.id} said at last.'
    )
    world.say(
        f'"As real as a lantern in the dark," the ghost answered, and {hero.id} smiled.'
    )
    world.say(
        f'{hero.id} lifted the {prize.label}, and the little brass light made a bright circle on the wall.'
    )
    world.say(
        f"Then {hero.id}, {hero.pronoun('possessive')} {parent.type if parent.type in {'mother','father'} else parent.label}, and the ghost watched the whir settle into a soft hum."
    )
    world.say(
        f"By the end, the real-ist child was still careful, but no longer afraid to believe the ghost."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    world.facts.update(hero=hero, parent=parent, ghost=ghost, prize=prize, action=action, setting=setting)

    _setup(world, hero, parent, ghost, prize, action)
    world.para()
    _first_turn(world, hero, ghost, action)
    world.para()
    _middle_turn(world, hero, ghost, prize)
    world.para()
    _resolution(world, hero, parent, ghost, prize)

    world.facts["resolved"] = hero.memes["trust"] > 0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    action = f["action"]
    return [
        f'Write a short ghost story for a young child that uses the words "gristle", "whir", and "real-ist".',
        f"Tell a gentle spooky story where {hero.id} hears a whir in {world.setting.place} and learns that a ghost can be real.",
        f"Write a dialogue-heavy story about a child, a ghost, and {prize.label}, ending with a calm, bright image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, ghost, prize, action = f["hero"], f["parent"], f["ghost"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a real-ist child who meets a ghost in {world.setting.place}.",
        ),
        QAItem(
            question=f"What sound did the child hear in the house?",
            answer=f"The child heard a soft whir from {world.setting.source}.",
        ),
        QAItem(
            question=f"What did the ghost say to prove it was not just a trick?",
            answer='The ghost said, "I am real."',
        ),
        QAItem(
            question=f"What made {hero.id} stop being so doubtful?",
            answer=f"{hero.id} heard the whir, saw the ghost speak, and noticed the old house really did make strange sounds.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} believed the ghost, and the {prize.label} shone a bright circle on the wall while the whir turned into a soft hum.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character people imagine as a spirit from long ago, often shown floating and speaking in a quiet voice.",
        ),
        QAItem(
            question="What does whir mean?",
            answer="Whir is a soft spinning sound, like a fan or a small machine turning round and round.",
        ),
        QAItem(
            question="What is a real-ist?",
            answer="A real-ist is someone who wants proof and likes to believe only what seems real and true.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives a little light so people can see in the dark.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place,Action,Prize) :- place(Place), action(Action), prize(Prize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="attic", action="listen", prize="lantern", name="Mia", parent="mother"),
    StoryParams(place="hall", action="peek", prize="blanket", name="Noah", parent="father"),
    StoryParams(place="cellar", action="follow", prize="bell", name="Ivy", parent="grandma"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid_story combinations:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
