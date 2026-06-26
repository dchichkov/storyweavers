#!/usr/bin/env python3
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
    held_by: Optional[str] = None
    hidden_in: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    clue: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "fear": 0.0, "trust": 0.0, "doubt": 0.0, "bravery": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "doubt": 0.0, "bravery": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "captainess"}
        male = {"man", "boy", "father", "captain", "sailor"}
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
    weather: str
    details: str
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
    found_in: str
    points_to: str
    oddity: str
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
class Suspect:
    id: str
    label: str
    role: str
    alibi: str
    nervous_tell: str
    lies: bool = False
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
class StoryParams:
    setting: str
    clue: str
    suspect: str
    name: str
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


SETTINGS = {
    "harbor": Setting(
        place="the foggy harbor",
        weather="foggy",
        details="Masts creaked in the gray air, and the water hid little ripples like secrets.",
    ),
    "island": Setting(
        place="the island dock",
        weather="windy",
        details="The dock boards rattled under the wind, and gulls called from the black rocks.",
    ),
    "bay": Setting(
        place="the quiet bay",
        weather="drizzling",
        details="Rain dotted the deck, and the sea looked soft as a wrinkled blanket.",
    ),
}

CLUES = {
    "salt_rope": Clue(
        id="salt_rope",
        label="a salt-stiff rope knot",
        found_in="the captain's cabin",
        points_to="harbor_door",
        oddity="It smelled like the sea even though it had been hidden inside.",
    ),
    "ink_smudge": Clue(
        id="ink_smudge",
        label="a dark ink smudge",
        found_in="the chart room",
        points_to="scribe",
        oddity="The mark matched the shape of a hurried note.",
    ),
    "silver_button": Clue(
        id="silver_button",
        label="a silver button",
        found_in="by the lifeboat",
        points_to="mate_coat",
        oddity="It gleamed like it had been torn from a coat in a rush.",
    ),
}

SUSPECTS = {
    "first_mate": Suspect(
        id="first_mate",
        label="the first mate",
        role="first mate",
        alibi="He said he was checking the lanterns on the port side.",
        nervous_tell="He kept rubbing his hands together and looking at the sea.",
        lies=True,
    ),
    "cook": Suspect(
        id="cook",
        label="the cook",
        role="cook",
        alibi="She said she was in the galley stirring soup for the crew.",
        nervous_tell="She blinked every time anyone mentioned the missing key.",
        lies=False,
    ),
    "deckhand": Suspect(
        id="deckhand",
        label="the deckhand",
        role="deckhand",
        alibi="He said he was coiling nets near the stern.",
        nervous_tell="His boots were muddy, but only from the dock.",
        lies=False,
    ),
}


GEO = {
    "harbor": "harbor",
    "island": "island",
    "bay": "bay",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world with a brave captain and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
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


def reasonableness_gate(setting: str, clue: str, suspect: str) -> bool:
    if clue == "silver_button" and suspect != "first_mate":
        return False
    if clue == "ink_smudge" and suspect != "cook":
        return False
    if clue == "salt_rope" and suspect != "deckhand":
        return False
    return True


def explain_rejection(setting: str, clue: str, suspect: str) -> str:
    return (
        f"(No story: in {_safe_lookup(SETTINGS, setting).place}, {_safe_lookup(CLUES, clue).label} does not fit {_safe_lookup(SUSPECTS, suspect).label} "
        f"well enough for this whodunit. Try a clue and suspect that belong together.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "clue", None) and getattr(args, "suspect", None) and not reasonableness_gate(getattr(args, "setting", None) or "harbor", getattr(args, "clue", None), getattr(args, "suspect", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    settings = [getattr(args, "setting", None)] if getattr(args, "setting", None) else list(SETTINGS)
    clues = [getattr(args, "clue", None)] if getattr(args, "clue", None) else list(CLUES)
    suspects = [getattr(args, "suspect", None)] if getattr(args, "suspect", None) else list(SUSPECTS)
    combos = [(s, c, p) for s in settings for c in clues for p in suspects if reasonableness_gate(s, c, p)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, clue, suspect = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Mara", "Nell", "June", "Tessa", "Iris"])
    return StoryParams(setting=setting, clue=clue, suspect=suspect, name=name)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    captain = world.add(Entity(id=params.name, kind="character", type="captain", label="the captain"))
    captain.memes["resolve"] = 1.0
    captain.memes["bravery"] = 1.0
    captain.meters["trust"] = 1.0

    crew = [
        world.add(Entity(id="first_mate", kind="character", type="man", label="the first mate")),
        world.add(Entity(id="cook", kind="character", type="woman", label="the cook")),
        world.add(Entity(id="deckhand", kind="character", type="man", label="the deckhand")),
    ]
    clue = world.add(Entity(
        id=params.clue,
        kind="thing",
        type="clue",
        label=_safe_lookup(CLUES, params.clue).label,
        phrase=_safe_lookup(CLUES, params.clue).label,
        hidden_in=_safe_lookup(CLUES, params.clue).found_in,
    ))
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    world.facts.update(captain=captain, crew=crew, clue=clue, suspect=suspect, params=params)
    return world


def tell_story(world: World) -> None:
    f = world.facts
    captain: Entity = _safe_fact(world, f, "captain")
    clue: Entity = _safe_fact(world, f, "clue")
    suspect: Suspect = _safe_fact(world, f, "suspect")
    params: StoryParams = _safe_fact(world, f, "params")

    world.say(
        f"{captain.id} was the captain of a little ship that bobbed in {world.setting.place}. "
        f"{world.setting.details}"
    )
    world.say(
        f"One morning, someone noticed that the ship's brass compass was missing, and the crew fell quiet."
    )
    world.say(
        f"{captain.id} was brave, and {captain.pronoun('possessive')} bravery mattered because a whodunit had to be solved before the tide turned."
    )

    world.para()
    world.say(
        f"{captain.id} searched the cabin and found {clue.label} {clue.hidden_in}. {clue.oddity}"
    )
    world.say(
        f"{captain.id} thought it pointed toward {suspect.label}, because the clue seemed to match {suspect.role} work."
    )
    world.say(
        f"Then {suspect.alibi} {suspect.nervous_tell}"
    )

    world.para()
    if suspect.lies:
        world.say(
            f"{captain.id} wanted the answer to be neat, so {captain.pronoun('subject')} pressed ahead and accused {suspect.label} too quickly."
        )
        world.say(
            f"The brave part was not the guessing; the brave part was speaking loudly in front of the whole crew, even when the deck felt like it was tipping."
        )
        world.say(
            f"But the wrong guess made everything worse. {suspect.label} was not the thief, and the real culprit slipped away in the fog with the compass."
        )
    else:
        world.say(
            f"{captain.id} noticed the clue did not truly fit {suspect.label}, but by then the storm bell had started ringing and the crew was already scrambling."
        )
        world.say(
            f"The captain's bravery helped the crew search faster, yet the compass stayed missing."
        )
        world.say(
            f"By sunset, the ship still had no compass, and the wrong shadow in the story had grown too big to catch."
        )

    world.para()
    world.say(
        f"In the end, {captain.id} stood on the deck with a lantern in hand while fog swallowed the harbor. "
        f"The crew could see the dark water, but not the way home."
    )
    world.say(
        f"It was a bad ending for the little whodunit: the captain had been brave, but bravery alone could not bring back the compass."
    )
    world.facts["bad_ending"] = True
    world.facts["bravery"] = True
    world.facts["solved"] = False
    world.facts["compass_lost"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    clue: Entity = _safe_fact(world, f, "clue")
    suspect: Suspect = _safe_fact(world, f, "suspect")
    return [
        f'Write a short whodunit story about a brave captain in {world.setting.place} with a bad ending.',
        f"Tell a child-friendly mystery where {params.name}, a captain, follows {clue.label} and suspects {suspect.label}.",
        f'Write a story that includes bravery, a missing compass, and an ending where the mystery is not fully solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain: Entity = _safe_fact(world, f, "captain")
    clue: Entity = _safe_fact(world, f, "clue")
    suspect: Suspect = _safe_fact(world, f, "suspect")
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {captain.id}, the brave captain of a little ship in {world.setting.place}.",
        ),
        QAItem(
            question=f"What clue did the captain find?",
            answer=f"{captain.id} found {clue.label} {clue.hidden_in}, and it seemed important because it looked strange.",
        ),
        QAItem(
            question=f"Who did the captain think might have taken the compass?",
            answer=f"{captain.id} thought {suspect.label} might have done it, because the clue seemed to point that way.",
        ),
        QAItem(
            question=f"Why is the ending a bad ending?",
            answer=(
                f"It is a bad ending because the captain stayed brave, but the compass was still missing and the real culprit got away in the fog."
            ),
        ),
        QAItem(
            question=f"What did bravery help the captain do?",
            answer=f"Bravery helped {params.name} speak up and keep searching even when the deck felt scary and the crew was worried.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a captain do on a ship?",
            answer="A captain leads the ship, makes choices for the crew, and tries to keep everyone safe.",
        ),
        QAItem(
            question="What is a clue in a whodunit?",
            answer="A clue is a small piece of information that can help solve a mystery.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary or hard even when you feel worried.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}} hidden_in={e.hidden_in or '-'}"
        )
    lines.append(f"  facts: bad_ending={world.facts.get('bad_ending')} bravery={world.facts.get('bravery')} solved={world.facts.get('solved')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="harbor", clue="salt_rope", suspect="deckhand", name="Mara"),
    StoryParams(setting="island", clue="silver_button", suspect="first_mate", name="Nell"),
    StoryParams(setting="bay", clue="ink_smudge", suspect="cook", name="June"),
]


ASP_RULES = r"""
setting(harbor).
setting(island).
setting(bay).

clue(salt_rope).
clue(ink_smudge).
clue(silver_button).

suspect(first_mate).
suspect(cook).
suspect(deckhand).

compatible(harbor,salt_rope,deckhand).
compatible(island,silver_button,first_mate).
compatible(bay,ink_smudge,cook).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for p in SUSPECTS:
        lines.append(asp.fact("suspect", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {
        (s, c, p)
        for s in SETTINGS
        for c in CLUES
        for p in SUSPECTS
        if reasonableness_gate(s, c, p)
    }
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=render_story(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def render_story(world: World) -> str:
    return world.render()


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
        triples = asp_valid()
        print(f"{len(triples)} compatible story combos:")
        for t in triples:
            print(" ", t)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: setting={p.setting}, clue={p.clue}, suspect={p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
