#!/usr/bin/env python3
"""
Story world: a child-friendly ghost story with a mystery, a twist, and a quest.

Premise imagined from the seed:
A little curious kid hears a strange "woo" drifting through an old house at dusk.
They think a ghost is nearby, but the mystery turns out to be something the house
has been trying to tell them. The child follows the clues, learns the truth, and
helps the lonely ghost find peace.

This world models:
- physical meters: fear, chill, glow, dust, bravery, trust, relief, curiosity
- emotional memes: worry, hope, wonder, loneliness, comfort, friendship

The story shape is always:
1) setup in a spooky place
2) mystery and quest through clues
3) twist reveal
4) gentle resolution
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
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
    vibe: str
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
class Mystery:
    id: str
    clue: str
    false_guess: str
    twist: str
    reveal: str
    solved_by: str
    ghost_reason: str
    keyword: str = "woo"
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
class Quest:
    id: str
    goal: str
    path: str
    ending: str
    helper: str
    reward: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "old_house": Setting(place="the old house", vibe="dusty and moonlit", affords={"search", "listen", "follow"}),
    "attic": Setting(place="the attic", vibe="creaky and high", affords={"search", "listen", "follow"}),
    "garden": Setting(place="the moon garden", vibe="silver and still", affords={"search", "listen", "follow"}),
}

MYSTERIES = {
    "woo_window": Mystery(
        id="woo_window",
        clue="a soft woo from the window",
        false_guess="a hungry ghost",
        twist="the woo was wind slipping through a loose shutter",
        reveal="the shutter had been tapping like a tiny drum in the dark",
        solved_by="closing the shutter and finding the hidden note",
        ghost_reason="the lonely ghost was trying to ask for help",
        keyword="woo",
    ),
    "woo_hall": Mystery(
        id="woo_hall",
        clue="a long woo from the hallway",
        false_guess="a ghost chasing someone",
        twist="the woo came from an old music box under a rug",
        reveal="the music box had a broken spring that hummed at night",
        solved_by="winding the box carefully and lifting the rug",
        ghost_reason="the ghost was guarding a lost keepsake",
        keyword="woo",
    ),
}

QUESTS = {
    "note_quest": Quest(
        id="note_quest",
        goal="find who left the pale note",
        path="follow the clues room by room",
        ending="place the note beside the right door",
        helper="a glowing firefly",
        reward="a soft thank-you from the ghost",
    ),
    "lantern_quest": Quest(
        id="lantern_quest",
        goal="find the missing lantern key",
        path="search the dusty shelves and tiny drawers",
        ending="light the lantern in the hallway",
        helper="a squeaky floorboard that pointed the way",
        reward="warm light spreading through the house",
    ),
}

HEROES = [
    ("Maya", "girl"),
    ("Niko", "boy"),
    ("Lina", "girl"),
    ("Theo", "boy"),
]

TRAITS = ["curious", "careful", "brave", "gentle", "patient"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    quest: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a mystery, twist, and quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def reasonableness_ok(setting: Setting, mystery: Mystery, quest: Quest) -> bool:
    return "follow" in setting.affords and mystery.keyword == "woo" and quest.id in QUESTS


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for q in QUESTS:
                if reasonableness_ok(_safe_lookup(SETTINGS, s), _safe_lookup(MYSTERIES, m), _safe_lookup(QUESTS, q)):
                    out.append((s, m, q))
    return out


def explain_rejection() -> str:
    return "(No story: this ghost mystery needs a place where the child can listen and follow clues.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "quest", None) is None or c[2] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery, quest = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        names = [n for n, g in HEROES if g == gender]
        name = rng.choice(names)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, quest=quest, name=name, gender=gender, trait=trait)


ASP_RULES = r"""
valid(S,M,Q) :- setting(S), mystery(M), quest(Q), can_follow(S), woo_mystery(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "follow" in s.affords:
            lines.append(asp.fact("can_follow", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.keyword == "woo":
            lines.append(asp.fact("woo_mystery", mid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def _setup(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(f"On a quiet evening, {hero.id} stood in {world.setting.place}, where everything felt {world.setting.vibe}.")
    world.say(f"{hero.pronoun().capitalize()} heard a strange {mystery.keyword}: {mystery.clue}.")
    world.say(f"{hero.id} was {hero.traits[0]} and wanted to know who, or what, was making that sound.")


def _mystery_turn(world: World, hero: Entity, mystery: Mystery, quest: Quest) -> None:
    hero.meters["curiosity"] += 1
    hero.memes["wonder"] += 1
    world.say(f"{hero.id} decided to start a little quest and {quest.path}.")
    world.say(f"First, {hero.pronoun()} followed {quest.helper} past a dusty mirror and a cold stair.")
    world.say(f"Then {hero.pronoun()} found {mystery.false_guess}, and for a moment the house felt even spookier.")


def _twist(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["fear"] += 1
    hero.memes["worry"] += 1
    world.say(f"But the real twist was this: {mystery.twist}.")
    world.say(f"That changed everything, because {mystery.ghost_reason}.")


def _resolution(world: World, hero: Entity, mystery: Mystery, quest: Quest) -> None:
    hero.meters["bravery"] += 1
    hero.memes["comfort"] += 1
    hero.memes["hope"] += 1
    world.say(f"{hero.id} did not run away. {hero.pronoun().capitalize()} used the clue and chose to help.")
    world.say(f"With careful hands, {hero.id} could {mystery.solved_by}, and that finished the quest: {quest.goal}.")
    world.say(f"In the end, {quest.ending}, and {quest.reward} stayed in the warm air like a tiny blessing.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "kind"]))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    quest = _safe_lookup(QUESTS, params.quest)
    world.facts.update(hero=hero, mystery=mystery, quest=quest, setting=world.setting)

    _setup(world, hero, mystery)
    world.say("")
    _mystery_turn(world, hero, mystery, quest)
    world.say("")
    _twist(world, hero, mystery)
    world.say("")
    _resolution(world, hero, mystery, quest)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mystery, quest = f["hero"], f["mystery"], f["quest"]
    return [
        f'Write a child-friendly ghost story where a {hero.type} named {hero.id} hears "{mystery.keyword}" and solves a mystery.',
        f"Tell a spooky-but-gentle quest story with a twist, where {hero.id} must {quest.goal}.",
        f"Write a short mystery story set in {world.setting.place} that ends with a kind ghost being helped.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mystery, quest = f["hero"], f["mystery"], f["quest"]
    return [
        QAItem(question=f"What strange sound did {hero.id} hear?", answer=f"{hero.id} heard a soft {mystery.keyword} in {world.setting.place}."),
        QAItem(question=f"What did {hero.id} do about the spooky clue?", answer=f"{hero.id} started a quest to {quest.path.lower()}."),
        QAItem(question=f"What was the twist in the story?", answer=f"The twist was that {mystery.twist}."),
        QAItem(question=f"How did the story end?", answer=f"It ended when {hero.id} finished the quest and helped the lonely ghost feel better."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a ghost story?", answer="A ghost story is a story about spooky places, strange clues, and sometimes a friendly ghost."),
        QAItem(question="What does a mystery mean?", answer="A mystery is something puzzling that you try to figure out."),
        QAItem(question="What is a quest?", answer="A quest is a search or journey to find something important or solve a problem."),
        QAItem(question="Why can old houses feel spooky?", answer="Old houses can feel spooky because they are quiet, dark, and full of creaky sounds."),
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
    lines.append("== World-knowledge questions ==")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(setting="old_house", mystery="woo_window", quest="note_quest", name="Maya", gender="girl", trait="curious"),
    StoryParams(setting="attic", mystery="woo_hall", quest="lantern_quest", name="Theo", gender="boy", trait="brave"),
    StoryParams(setting="garden", mystery="woo_window", quest="note_quest", name="Lina", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
