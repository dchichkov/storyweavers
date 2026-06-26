#!/usr/bin/env python3
"""
A small animal-story world about a gentle quest shadowed by wicked trouble,
with foreshadowing and sound effects driving the turn.

The premise:
- A gentle animal wants to complete a small quest.
- A wicked obstacle threatens the goal.
- Early signs foreshadow the trouble.
- The hero uses a careful plan and the story ends with a satisfying change.

The simulation tracks both physical meters and emotional memes:
- meters: carried items, distance, readiness, noise, damage
- memes: worry, courage, patience, kindness, wickedness, relief

This file is self-contained and follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    reward: object | None = None
    rival: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "cat", "bear", "dog", "hare", "rabbit", "mouse", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def a(self) -> str:
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
class Place:
    id: str
    label: str
    path: str
    sounds: list[str] = field(default_factory=list)
    foreshadow: str = ""
    quest_items: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)
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


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    item: str
    item_phrase: str
    item_label: str
    item_kind: str
    item_reach: str
    reward: str
    sound_ok: str
    sound_bad: str
    safe_help: str
    foreshadow_sign: str
    hazard: str
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
class Companions:
    helper: str
    observer: str
    trickster: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.weather = self.weather
        return w


def noise(word: str) -> str:
    return {
        "rustle": "rustle-rustle",
        "tap": "tap-tap",
        "clink": "clink-clink",
        "hush": "hush-hush",
        "thump": "thump-thump",
        "splash": "splash-splash",
        "creak": "creak-creak",
    }.get(word, word)


def is_wicked(ent: Entity) -> bool:
    return ent.memes.get("wickedness", 0.0) >= THRESHOLD


def is_gentle(ent: Entity) -> bool:
    return ent.memes.get("gentleness", 0.0) >= THRESHOLD


def foreshadow(world: World, hero: Entity, quest: Quest, rival: Entity) -> None:
    world.say(
        f"At {world.place.label}, {world.place.foreshadow} "
        f"{hero.id} heard {noise(quest.foreshadow_sign)} in the reeds."
    )
    hero.memes["worry"] += 1
    world.facts["foreshadow"] = quest.foreshadow_sign
    if rival.memes.get("wickedness", 0.0) >= THRESHOLD:
        world.say(
            f"{rival.id} smiled a sly smile, and that made the little sound feel even less friendly."
        )


def start_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["kindness"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} was a gentle little {hero.type} who wanted to {quest.verb}."
    )
    world.say(
        f"{hero.id} knew the reward was {quest.reward}, but first {hero.id} had to find {quest.item_phrase}."
    )


def set_item(world: World, item: Entity, keeper: Entity) -> None:
    item.owner = keeper.id
    keeper.carries = item.id
    world.say(
        f"{keeper.id} carried {item.phrase} in {keeper.pronoun('possessive')} mouth."
    )


def hazard_check(world: World, hero: Entity, quest: Quest, rival: Entity) -> bool:
    if not is_wicked(rival):
        return False
    world.facts["hazard"] = quest.hazard
    hero.memes["worry"] += 1
    world.say(
        f"Then the wicked {rival.type} sprang from behind a stump with a loud {noise(quest.sound_bad)}!"
    )
    world.say(
        f"The path went still, as if it were holding its breath."
    )
    return True


def helper_step(world: World, helper: Entity, hero: Entity, quest: Quest) -> None:
    helper.memes["gentleness"] += 1
    hero.memes["relief"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    world.say(
        f"{helper.id} gave a gentle nod and whispered, '{quest.safe_help}.'"
    )


def resolve_quest(world: World, hero: Entity, item: Entity, quest: Quest, reward: Entity) -> None:
    hero.meters["distance"] += 1
    hero.meters["ready"] += 1
    hero.memes["courage"] += 1
    reward.owner = hero.id
    world.say(
        f"{hero.id} waited for the right moment, then went forward with a quiet {noise(quest.sound_ok)}."
    )
    world.say(
        f"With a careful step, {hero.id} reached {item.phrase} and brought it home."
    )
    world.say(
        f"At last, {hero.id} earned {reward.phrase}, and the wicked trouble was left behind."
    )
    world.say(
        f"The ending felt warm and small, like sunlight on fur after rain."
    )


def tell_story(place: Place, quest: Quest, names: dict[str, str]) -> World:
    world = World(place)
    hero = world.add(Entity(id=names["hero"], kind="character", type=names["hero_type"], label=names["hero_type"]))
    helper = world.add(Entity(id=names["helper"], kind="character", type=names["helper_type"], label=names["helper_type"]))
    rival = world.add(Entity(id=names["rival"], kind="character", type=names["rival_type"], label=names["rival_type"]))
    item = world.add(Entity(id="item", kind="thing", type=quest.item_kind, label=quest.item_label, phrase=quest.item_phrase))
    reward = world.add(Entity(id="reward", kind="thing", type="treasure", label="reward", phrase=quest.reward))

    hero.memes["gentleness"] += 1
    helper.memes["gentleness"] += 1
    rival.memes["wickedness"] += 1

    start_quest(world, hero, quest)
    world.para()
    foreshadow(world, hero, quest, rival)
    hazard_check(world, hero, quest, rival)
    set_item(world, item, helper)
    helper_step(world, helper, hero, quest)
    world.para()
    resolve_quest(world, hero, item, quest, reward)

    world.facts.update(
        hero=hero,
        helper=helper,
        rival=rival,
        item=item,
        reward=reward,
        quest=quest,
        place=place,
    )
    return world


SETTINGS = {
    "meadow": Place(
        id="meadow",
        label="the meadow",
        path="a narrow path through tall grass",
        sounds=["rustle", "tap"],
        foreshadow="The grass leaned one way, and every leaf seemed to listen.",
        quest_items={"berry", "bell", "crown"},
        hazards={"shadow", "snag"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        path="a pebbly trail beside the water",
        sounds=["splash", "clink"],
        foreshadow="The water kept making little circles near the stones.",
        quest_items={"shell", "reed", "glowstone"},
        hazards={"current", "splash"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        path="rows of trees with soft dirt between them",
        sounds=["creak", "rustle"],
        foreshadow="A branch above creaked once, though there was no wind.",
        quest_items={"apple", "key", "lantern"},
        hazards={"branch", "fox"},
    ),
}

QUESTS = {
    "berry": Quest(
        id="berry",
        goal="bring home the bright berry",
        verb="fetch the bright berry",
        item="berry",
        item_phrase="the bright berry on the thorny bush",
        item_label="berry",
        item_kind="berry",
        item_reach="bush",
        reward="a sweet supper",
        sound_ok="tap",
        sound_bad="snarl",
        safe_help="I will hold the thorny branch while you reach",
        foreshadow_sign="rustle-rustle",
        hazard="thorn",
    ),
    "bell": Quest(
        id="bell",
        goal="ring the little bell for the nest",
        verb="carry the little bell to the nest",
        item="bell",
        item_phrase="the little bell under the root",
        item_label="bell",
        item_kind="bell",
        item_reach="root",
        reward="a song at dusk",
        sound_ok="clink",
        sound_bad="crash",
        safe_help="we can lift the root together",
        foreshadow_sign="tap-tap",
        hazard="root",
    ),
    "shell": Quest(
        id="shell",
        goal="return the shell to the friend",
        verb="find the shiny shell",
        item="shell",
        item_phrase="the shiny shell by the water",
        item_label="shell",
        item_kind="shell",
        item_reach="shore",
        reward="a little ribbon",
        sound_ok="splash",
        sound_bad="growl",
        safe_help="let us wait until the water is calm",
        foreshadow_sign="splash-splash",
        hazard="current",
    ),
}

HERO_TYPES = ["rabbit", "mouse", "badger", "fox", "otter", "deer", "hare"]
HELPER_TYPES = ["bird", "turtle", "squirrel", "goat", "cat"]
RIVAL_TYPES = ["wolf", "crow", "weasel", "fox", "boar"]
NAMES = ["Pip", "Milo", "Tara", "Nia", "Penny", "Bram", "Luna", "Dove"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    rival_name: str
    rival_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with foreshadowing, quest, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--rival-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--rival-type", choices=RIVAL_TYPES)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            combos.append((s, q))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    rival_type = getattr(args, "rival_type", None) or rng.choice(RIVAL_TYPES)
    return StoryParams(
        setting=setting,
        quest=quest,
        hero_name=getattr(args, "hero_name", None) or rng.choice(NAMES),
        hero_type=hero_type,
        helper_name=getattr(args, "helper_name", None) or rng.choice([n for n in NAMES if n != getattr(args, "hero_name", None)]),
        helper_type=helper_type,
        rival_name=getattr(args, "rival_name", None) or rng.choice([n for n in NAMES if n not in {getattr(args, "hero_name", None), getattr(args, "helper_name", None)}]),
        rival_type=rival_type,
    )


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(SETTINGS, params.setting)
    quest = _safe_lookup(QUESTS, params.quest)
    world = tell_story(place, quest, {
        "hero": params.hero_name,
        "hero_type": params.hero_type,
        "helper": params.helper_name,
        "helper_type": params.helper_type,
        "rival": params.rival_name,
        "rival_type": params.rival_type,
    })
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    return [
        f'Write a gentle animal story with a wicked shadow and a small quest to {q.verb}.',
        f'Write a story where a gentle {f["hero"].type} hears {q.foreshadow_sign} before meeting a wicked rival.',
        f'Tell a child-friendly tale with sound effects like {q.sound_ok} and {q.sound_bad}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, rival, quest, place = f["hero"], f["helper"], f["rival"], f["quest"], f["place"]
    return [
        QAItem(
            question=f"Who wanted to {quest.verb}?",
            answer=f"{hero.id}, the gentle {hero.type}, wanted to {quest.verb}.",
        ),
        QAItem(
            question=f"What sound foreshadowed trouble at {place.label}?",
            answer=f"The sound {quest.foreshadow_sign} foreshadowed that something tricky might happen.",
        ),
        QAItem(
            question=f"Who helped {hero.id} during the quest?",
            answer=f"{helper.id}, the gentle {helper.type}, helped by saying, '{quest.safe_help}.'",
        ),
        QAItem(
            question=f"What made the rival wicked?",
            answer=f"{rival.id} was wicked because {rival.id} showed wickedness and caused the sudden {quest.sound_bad} of trouble.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} brought home {quest.item_phrase} and earned {quest.reward}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    place = _safe_fact(world, world.facts, "place")
    quest = _safe_fact(world, world.facts, "quest")
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue early in the story that hints something important may happen later.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that a character tries to complete by going somewhere or finding something.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make actions feel lively and to help the reader imagine what is happening.",
        ),
        QAItem(
            question=f"What kind of place is {place.label}?",
            answer=f"{place.label.capitalize()} is a setting with {place.path} and sounds like {', '.join(place.sounds)}.",
        ),
        QAItem(
            question=f"What does {quest.sound_ok} suggest?",
            answer=f"It suggests a small, careful, or bright sound that fits a gentle moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
quest(Q) :- goal(Q).
gentle(H) :- hero(H), kind(H,gentle).
wicked(R) :- rival(R), kind(R,wicked).
foreshadows(P) :- sign(P).
has_quest_story(S,Q) :- setting(S), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for snd in s.sounds:
            lines.append(asp.fact("sound", sid, snd))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("goal", qid))
        lines.append(asp.fact("sign", q.foreshadow_sign))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show setting/1. #show quest/1."))
    if model is None:
        print("No ASP model.")
        return 1
    print("OK: ASP rules parse and solve.")
    return 0


CURATED = [
    StoryParams("meadow", "berry", "Pip", "rabbit", "Dove", "bird", "Moss", "wolf"),
    StoryParams("orchard", "bell", "Milo", "mouse", "Tara", "turtle", "Bran", "fox"),
    StoryParams("riverbank", "shell", "Nia", "otter", "Penny", "cat", "Grey", "weasel"),
]


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
        print(asp_program("#show setting/1. #show quest/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
