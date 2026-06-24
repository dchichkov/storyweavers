#!/usr/bin/env python3
"""
storyworlds/worlds/intellectual_condense_peek_quest_ghost_story.py
==================================================================

A gentle ghost-story world about a small quest where a curious child learns to
peek carefully, condense clues, and use an intellectual plan to help a friendly
ghost finish one unfinished task.

Seed words:
- intellectual
- condense
- peek

Style note:
- Keep the mood ghost-story-ish: moonlight, whispers, old rooms, tiny chills.
- Keep the ending warm: the ghost is helped, the quest is completed, and the
  world becomes calm.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared containers importable when run as a script.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    g: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    details: str
    afford_quest: bool = True
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
class Quest:
    id: str
    goal: str
    clue_word: str
    action: str
    peek_spot: str
    solve_line: str
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
class Ghost:
    id: str
    label: str
    type: str
    unfinished: str
    reward: str
    location: str = "the old house"
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# World content
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(
        place="the attic",
        mood="moonlit",
        details="Dusty beams crossed the ceiling, and the small window let in a silver stripe of moonlight.",
    ),
    "library": Setting(
        place="the old library",
        mood="quiet",
        details="Tall shelves stood like sleeping trees, and every page seemed to whisper.",
    ),
    "hall": Setting(
        place="the empty hall",
        mood="echoing",
        details="The floorboards creaked softly, and the walls held a chilly hush.",
    ),
}

QUESTS = {
    "key": Quest(
        id="key",
        goal="find the little brass key",
        clue_word="key",
        action="peek behind the blue box",
        peek_spot="behind the blue box",
        solve_line="the little brass key was tucked in a folded paper boat",
        tags={"peek", "quest"},
    ),
    "bell": Quest(
        id="bell",
        goal="find the silver bell rope",
        clue_word="bell",
        action="peek under the old bench",
        peek_spot="under the old bench",
        solve_line="the silver bell rope hung from a hook above the door",
        tags={"peek", "quest"},
    ),
    "map": Quest(
        id="map",
        goal="find the folded map page",
        clue_word="map",
        action="peek inside the cracked teacup",
        peek_spot="inside the cracked teacup",
        solve_line="the folded map page was hidden beneath a stack of song sheets",
        tags={"peek", "quest"},
    ),
}

GHOSTS = {
    "pale": Ghost(
        id="pale",
        label="a pale little ghost",
        type="ghost",
        unfinished="could not leave the house until the lost thing was found",
        reward="a grateful smile and a soft glow",
        tags={"ghost", "quest"},
    ),
    "lantern": Ghost(
        id="lantern",
        label="a lantern ghost",
        type="ghost",
        unfinished="kept circling the room because one final clue was missing",
        reward="a warm twinkle in the dark",
        tags={"ghost", "quest"},
    ),
}

NAMES = ["Mina", "Iris", "Owen", "Eli", "Lena", "June", "Milo", "Nora"]
TRAITS = ["brave", "quiet", "curious", "careful", "smart", "kind"]
GHOST_WORDS = {"ghost", "whisper", "moon", "shadow", "cold", "silver", "dust"}


def _m(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mm(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_m(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = _m(ent, key) + amount


def _add_mm(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = _mm(ent, key) + amount


def _propagate(world: World) -> None:
    # If the child peeks and has enough clues, the quest becomes clear.
    hero = world.get(world.facts["hero"].id)
    ghost = world.get(world.facts["ghost"].id)
    if _m(hero, "clues") >= THRESHOLD and (("clear",) not in world.fired):
        world.fired.add(("clear",))
        _add_mm(hero, "confidence", 1)
        _add_mm(ghost, "hope", 1)
        world.say("The clues began to line up like little moonbeams, and the answer felt close.")
    if _m(hero, "solved") >= THRESHOLD and (("gentle_release",) not in world.fired):
        world.fired.add(("gentle_release",))
        _add_mm(ghost, "peace", 1)
        _add_mm(hero, "joy", 1)
        world.say("The ghost stopped shivering, because the quest was finally coming to an end.")


def _introduce(world: World, hero: Entity, ghost: Ghost, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} {hero.type} "
        f"who loved an intellectual puzzle."
    )
    world.say(
        f"One night, {hero.pronoun()} noticed {ghost.label} waiting in {world.setting.place}."
    )
    world.say(
        f"{ghost.label.capitalize()} was on a quest to {quest.goal}, but {ghost.unfinished}."
    )


def _peek(world: World, hero: Entity, quest: Quest) -> None:
    _add_m(hero, "caution", 1)
    _add_m(hero, "clues", 1)
    _add_mm(hero, "curiosity", 1)
    world.say(
        f"{hero.id} decided to peek {quest.peek_spot} instead of rushing in."
    )
    world.say(
        f"That careful peek found a tiny clue, and {hero.pronoun()} remembered to condense the mystery into one simple thought: {quest.clue_word}."
    )


def _think(world: World, hero: Entity, ghost: Ghost, quest: Quest) -> None:
    _add_mm(hero, "thinking", 1)
    _add_m(hero, "solved", 1)
    world.say(
        f"{hero.id} made an intellectual plan: follow the clue, stay quiet, and use the same little idea twice if needed."
    )
    world.say(
        f"The plan led straight to {quest.solve_line}."
    )
    _propagate(world)


def _finish(world: World, hero: Entity, ghost: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} held up the answer, and {ghost.label} gave a relieved little sway."
    )
    world.say(
        f"At last, the quest was done, and the room felt warm instead of spooky."
    )
    world.say(
        f"{ghost.label.capitalize()} left behind {ghost.reward}, while {hero.id} smiled at the quiet dark."
    )


def tell(setting: Setting, quest: Quest, ghost: Ghost, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
        meters={"clues": 0.0, "solved": 0.0, "caution": 0.0},
        memes={"curiosity": 0.0, "thinking": 0.0, "confidence": 0.0, "joy": 0.0},
    ))
    g = world.add(Entity(
        id=ghost.id,
        kind="character",
        type=ghost.type,
        label=ghost.label,
        phrase=ghost.label,
        traits=["gentle", "unfinished"],
        meters={"hope": 0.0, "peace": 0.0},
        memes={"hope": 0.0, "peace": 0.0},
    ))
    world.facts.update(hero=hero, ghost=g, quest=quest, setting=setting)

    _introduce(world, hero, ghost, quest)
    world.para()
    _peek(world, hero, quest)
    _think(world, hero, g, quest)
    world.para()
    _finish(world, hero, g, quest)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting_key: str, quest_key: str, ghost_key: str) -> bool:
    return setting_key in SETTINGS and quest_key in QUESTS and ghost_key in GHOSTS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, g) for s in SETTINGS for q in QUESTS for g in GHOSTS if valid_combo(s, q, g)]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    ghost: str
    name: str
    gender: str
    trait: str
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


CURATED = [
    StoryParams(setting="attic", quest="key", ghost="pale", name="Mina", gender="girl", trait="curious"),
    StoryParams(setting="library", quest="map", ghost="lantern", name="Owen", gender="boy", trait="careful"),
    StoryParams(setting="hall", quest="bell", ghost="pale", name="Nora", gender="girl", trait="smart"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story quest world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    ghost = getattr(args, "ghost", None) or rng.choice(list(GHOSTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if not valid_combo(setting, quest, ghost):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, quest=quest, ghost=ghost, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(QUESTS, params.quest), _safe_lookup(GHOSTS, params.ghost), params.name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, ghost, quest = f["hero"], f["ghost"], f["quest"]
    return [
        f'Write a gentle ghost story for a young child using the words "intellectual", "condense", and "peek".',
        f"Tell a moonlit story where {hero.id} helps {ghost.label} {quest.goal} by using a careful clue and a smart plan.",
        f"Write a short story about a child who must peek first, condense the clue, and finish a quest in a spooky room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, quest, setting = f["hero"], f["ghost"], f["quest"], f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, who met {ghost.label} in {setting.place} and helped with a quest.",
        ),
        QAItem(
            question=f"What did {hero.id} do before making a plan?",
            answer=f"{hero.id} chose to peek {quest.peek_spot} and look for a tiny clue instead of rushing.",
        ),
        QAItem(
            question=f"What did the child condense the mystery into?",
            answer=f"{hero.id} condensed the mystery into one simple thought: {quest.clue_word}.",
        ),
        QAItem(
            question=f"How did the quest end?",
            answer=f"The answer led to {quest.solve_line}, and the ghost felt peaceful when the quest was done.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a gentle story like this?",
            answer="A ghost is a spooky-looking character, but in this story it is friendly, quiet, and needs help with an unfinished task.",
        ),
        QAItem(
            question="What does peek mean?",
            answer="Peek means to look carefully for a moment, usually from a small or hidden place.",
        ),
        QAItem(
            question="What does condense mean?",
            answer="Condense means to make something shorter or smaller while keeping the important part.",
        ),
        QAItem(
            question="What does intellectual mean?",
            answer="Intellectual means using thinking, ideas, and careful reasoning.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special job or search with a goal to finish.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting(S).
quest(Q) :- quest(Q).
ghost(G) :- ghost(G).

compatible(S,Q,G) :- setting(S), quest(Q), ghost(G).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
        for t in sorted(_safe_lookup(QUESTS, q).tags):
            lines.append(asp.fact("quest_tag", q, t))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
        for t in sorted(_safe_lookup(GHOSTS, g).tags):
            lines.append(asp.fact("ghost_tag", g, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Output / CLI
# ---------------------------------------------------------------------------
def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:7}) meters={meters} memes={memes}")
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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
