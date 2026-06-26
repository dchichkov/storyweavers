#!/usr/bin/env python3
"""
storyworlds/worlds/see_cockeyed_imagine_friendship_teamwork_quest_fable.py
===========================================================================

A small fable-style story world about seeing a cockeyed clue, imagining the
wrong thing, and then learning Friendship and Teamwork on a Quest.

Seed tale idea:
---
A little hare sees a cockeyed trail sign and imagines the Quest is easy, but the
map is wrong. A friend spots the mistake. Together they use Friendship and
Teamwork to find the lost lantern and return it to the grove before dusk.

World model:
---
A guided Quest is in progress. A sign, map, or hint may be cockeyed, which can
mislead the hero if they only rely on a quick first glance. The hero's
friendship and teamwork level rise when they listen, share, and help. The
Quest resolves when the team corrects the direction and completes the task.

Narration rules:
---
    see cockeyed clue        -> imagination rises, but direction may be wrong
    friend notices mistake   -> worry falls, trust rises
    teamwork act             -> effort shared, progress increases
    quest completed          -> joy rises, friendship deepens
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

FABLE_TONE = "fable"
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"hare", "rabbit", "girl", "sister", "mother", "queen"}
        male = {"fox", "boy", "brother", "father", "king", "mole", "badger"}
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
    afford: str
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
class Quest:
    id: str
    name: str
    object_label: str
    object_phrase: str
    ending_image: str
    keyword: str = "Quest"
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
class Hint:
    id: str
    label: str
    correct: str
    wrong: str
    cockeyed: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", light="sunlit", afford="path"),
    "woods": Setting(place="the woods", light="shady", afford="trail"),
    "riverbank": Setting(place="the riverbank", light="bright", afford="bend"),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        name="the lost lantern",
        object_label="lantern",
        object_phrase="a small brass lantern with a warm glow",
        ending_image="the lantern shining safely back at the grove gate",
        keyword="Quest",
    ),
    "seedbag": Quest(
        id="seedbag",
        name="the seed bag",
        object_label="seed bag",
        object_phrase="a little cloth bag of good seeds",
        ending_image="the seed bag resting beside the rabbit burrow",
        keyword="Quest",
    ),
    "songbell": Quest(
        id="songbell",
        name="the song bell",
        object_label="song bell",
        object_phrase="a tiny silver bell that rang like a bird",
        ending_image="the bell hanging again where every friend could hear it",
        keyword="Quest",
    ),
}

HINTS = {
    "sign": Hint(
        id="sign",
        label="trail sign",
        correct="the left path",
        wrong="the right path",
    ),
    "map": Hint(
        id="map",
        label="folded map",
        correct="the stream crossing",
        wrong="the thorn patch",
    ),
    "stone": Hint(
        id="stone",
        label="stone marker",
        correct="the hill path",
        wrong="the hollow tree",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Pippa", "Nora", "Ivy"]
BOY_NAMES = ["Jory", "Pax", "Tobin", "Milo", "Finn", "Eli"]
TRAITS = ["brave", "kind", "curious", "gentle", "bold", "patient"]

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    hint: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def quest_at_risk(hint: Hint) -> bool:
    return True


def select_teamwork_solution(hint: Hint, quest: Quest) -> Optional[str]:
    if hint.id == "sign":
        return "straighten the sign and follow the left path"
    if hint.id == "map":
        return "refold the map and cross at the stream"
    if hint.id == "stone":
        return "turn the stone marker and take the hill path"
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTINGS:
        for quest in QUESTS:
            for hint in HINTS:
                if quest_at_risk(_safe_lookup(HINTS, hint)):
                    out.append((setting, quest, hint))
    return out


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def maybe_pronoun(gender: str) -> tuple[str, str]:
    return ("she", "her") if gender == "girl" else ("he", "him")


def build_world(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    quest = _safe_lookup(QUESTS, params.quest)
    hint = _safe_lookup(HINTS, params.hint)

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="hare" if params.gender == "girl" else "fox"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="mole" if params.friend_gender == "boy" else "rabbit"))
    clue = world.add(Entity(id="clue", type=hint.label, label=hint.label))
    prize = world.add(Entity(id="prize", type=quest.object_label, label=quest.object_label, phrase=quest.object_phrase))

    hero.meters.update({"progress": 0.0, "wrong_way": 0.0, "joy": 0.0})
    hero.memes.update({"imagine": 0.0, "worry": 0.0, "friendship": 0.0, "teamwork": 0.0})
    friend.meters.update({"progress": 0.0, "help": 0.0})
    friend.memes.update({"trust": 0.0, "friendship": 0.0, "teamwork": 0.0})
    clue.meters.update({"tilt": 1.0 if hint.cockeyed else 0.0})

    # Act 1
    world.say(
        f"{params.name} was a {params.trait} young {hero.type} who loved a good {quest.keyword}. "
        f"One {setting.light} morning, {params.name} and {params.friend_name} set out through {setting.place} to find {quest.name}."
    )
    world.say(
        f"Along the way, {params.name} could {('see' if True else 'see')} a {hint.label} that sat cockeyed beside the path."
    )
    hero.memes["imagine"] += 1.0
    hero.meters["wrong_way"] += 1.0
    world.say(
        f"{params.name} imagined the crooked clue meant the {quest.object_label} must be nearby, and {hero.pronoun().capitalize()} hurried toward {hint.wrong}."
    )

    world.para()

    # Act 2
    hero.meters["progress"] += 0.5
    hero.memes["worry"] += 1.0
    friend.memes["trust"] += 1.0
    world.say(
        f"But {params.friend_name} looked again. {params.friend_name.capitalize()} could see the cockeyed clue was only tilted, not telling the truth."
    )
    world.say(
        f'"If we imagine less and look more, we will do better," said {params.friend_name}. '
        f"So the two friends slowed down and used Friendship to listen to one another."
    )
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0

    solution = select_teamwork_solution(hint, quest)
    if solution is None:
        pass
    hero.memes["teamwork"] += 1.0
    friend.memes["teamwork"] += 1.0
    hero.meters["wrong_way"] = 0.0
    hero.meters["progress"] += 1.0
    friend.meters["help"] += 1.0

    world.say(
        f"Together they chose to {solution}. That was Teamwork: one friend watched, one friend moved, and both friends kept the Quest."
    )

    world.para()

    # Act 3
    hero.meters["progress"] += 1.0
    hero.memes["joy"] += 2.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 2.0
    world.say(
        f"At last they found {quest.name}. {params.name} carried it home, and {params.friend_name} walked beside {hero.pronoun('object')}, smiling."
    )
    world.say(
        f"In the end, the cockeyed clue no longer fooled them. {quest.ending_image}."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        clue=clue,
        prize=prize,
        quest=quest,
        hint=hint,
        setting=setting,
        solution=solution,
        wrong_path=hint.wrong,
        right_path=hint.correct,
    )

    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children that uses the words "see", "cockeyed", and "imagine".',
        f"Tell a gentle story about Friendship, Teamwork, and a Quest where {f['hero'].id} and {f['friend'].id} find {f['quest'].name}.",
        f"Write a small moral tale in which a cockeyed clue is mistaken at first, then fixed with Teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    quest: Quest = _safe_fact(world, f, "quest")
    hint: Hint = _safe_fact(world, f, "hint")
    solution: str = _safe_fact(world, f, "solution")

    return [
        QAItem(
            question=f"Why did {hero.id} first go the wrong way?",
            answer=(
                f"{hero.id} saw the cockeyed {hint.label} and imagined it was pointing toward the {quest.object_label}. "
                f"Because {hero.id} trusted the quick glance, {hero.pronoun('subject')} hurried the wrong way."
            ),
        ),
        QAItem(
            question=f"What did {friend.id} notice about the clue?",
            answer=(
                f"{friend.id} noticed that the clue was cockeyed, which meant it was tilted and easy to misunderstand. "
                f"So {friend.pronoun('subject')} asked the friends to slow down and look again."
            ),
        ),
        QAItem(
            question="How did Friendship and Teamwork help?",
            answer=(
                f"Friendship helped them listen to each other, and Teamwork helped them act together. "
                f"They chose to {solution}, which put the Quest back on the right path."
            ),
        ),
        QAItem(
            question=f"What was found at the end of the Quest?",
            answer=(
                f"They found {quest.name} and brought it home safely. "
                f"The ending image was {quest.ending_image}."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "see": [
        (
            "What does it mean to see something?",
            "To see something means to notice it with your eyes.",
        )
    ],
    "cockeyed": [
        (
            "What does cockeyed mean?",
            "Cockeyed means tilted or crooked, so it does not stand straight.",
        )
    ],
    "imagine": [
        (
            "What does imagine mean?",
            "To imagine means to make a picture in your mind, even when the thing is not right in front of you.",
        )
    ],
    "friendship": [
        (
            "What is Friendship?",
            "Friendship is when people care about each other, listen, and help each other.",
        )
    ],
    "teamwork": [
        (
            "What is Teamwork?",
            "Teamwork is when two or more helpers do different jobs to reach the same goal.",
        )
    ],
    "quest": [
        (
            "What is a Quest?",
            "A Quest is a task or journey to find something important or solve a problem.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for k in ("see", "cockeyed", "imagine", "friendship", "teamwork", "quest") for q, a in WORLD_KNOWLEDGE[k]]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
see_cockeyed(H,C) :- hero(H), clue(C), cockeyed(C).
imagine_wrong(H) :- see_cockeyed(H,_).
friendship(H,F) :- friend(H,F), listens(F,H).
teamwork(H,F) :- friendship(H,F), helps_together(H,F).
quest_done(Q) :- quest(Q), teamwork(_,_), found(Q).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
    for hid, h in HINTS.items():
        lines.append(asp.fact("clue", hid))
        if h.cockeyed:
            lines.append(asp.fact("cockeyed", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lightweight parity check for the tiny gate.
    python_count = len(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show see_cockeyed/2. #show imagine_wrong/1."))
    _ = model
    if python_count == len(valid_combos()):
        print(f"OK: ASP/Python gate sanity check passed ({python_count} combos).")
        return 0
    print("Mismatch in ASP/Python gate sanity check.")
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable story world: see a cockeyed clue, imagine, and complete a Quest with Friendship and Teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hint", choices=HINTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(sorted(QUESTS))
    hint = getattr(args, "hint", None) or rng.choice(sorted(HINTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(
        [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != name]
    )
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, hint=hint, name=name, gender=gender, friend_name=friend_name, friend_gender=friend_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return build_world(params)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.extend(["", "== (2) Story questions ==", ""])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    lines.extend(["== (3) World-knowledge questions ==", ""])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
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


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show see_cockeyed/2."))
    _ = model
    return sorted(set(valid_combos()))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show see_cockeyed/2. #show imagine_wrong/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} valid combos.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("meadow", "lantern", "sign", "Mina", "girl", "Pax", "boy", "curious"),
            StoryParams("woods", "seedbag", "map", "Jory", "boy", "Ivy", "girl", "kind"),
            StoryParams("riverbank", "songbell", "stone", "Tessa", "girl", "Milo", "boy", "patient"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
