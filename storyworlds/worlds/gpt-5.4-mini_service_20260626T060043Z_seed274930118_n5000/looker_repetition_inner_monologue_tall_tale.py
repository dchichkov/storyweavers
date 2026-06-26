#!/usr/bin/env python3
"""
A small tall-tale storyworld about a looker with a sharp eye, a repeating
mistake, and a private inner monologue that turns the day around.

The seed image:
- A looker spots trouble far off.
- The looker keeps repeating the same boast and the same plan.
- The looker thinks to itself, changes course, and saves the day.

This world keeps the simulation small and state-driven:
- physical meters: distance, height, wear, dust, safety
- emotional memes: pride, worry, courage, relief, trust

The prose is child-facing, concrete, and built from simulated state.
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
# Core domain model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        return mapping[case]

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
class Place:
    name: str
    horizon: str
    affordances: set[str] = field(default_factory=set)
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
class Challenge:
    id: str
    verb: str
    repeated_verb: str
    monologue: str
    risk: str
    remedy: str
    physical_risk: str
    emotional_risk: str
    action_tag: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    use_verb: str
    tail: str
    tags: set[str] = field(default_factory=set)
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
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
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

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


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


PLACES = {
    "ridge": Place(
        name="the ridge",
        horizon="wide prairie",
        affordances={"scan", "watch"},
    ),
    "harbor": Place(
        name="the harbor",
        horizon="blue water",
        affordances={"scan", "watch"},
    ),
    "tower": Place(
        name="the tower",
        horizon="far roofs",
        affordances={"scan", "watch"},
    ),
    "meadow": Place(
        name="the meadow",
        horizon="tall grass",
        affordances={"scan", "watch"},
    ),
}

CHALLENGES = {
    "storm": Challenge(
        id="storm",
        verb="watch for the storm",
        repeated_verb="watch the storm",
        monologue="I can spot that storm before it spots us",
        risk="the wind would chase the chickens and twist the fence",
        remedy="send a warning and tie down the loose boards",
        physical_risk="windy",
        emotional_risk="worried",
        action_tag="storm",
        tags={"storm", "weather"},
    ),
    "river": Challenge(
        id="river",
        verb="watch the river rise",
        repeated_verb="watch the river",
        monologue="I can tell that river is growing by the inch and the grin",
        risk="the banks would slosh over the path",
        remedy="guide everyone to the high path and the dry stones",
        physical_risk="wet",
        emotional_risk="spooked",
        action_tag="river",
        tags={"river", "water"},
    ),
    "train": Challenge(
        id="train",
        verb="watch for the train",
        repeated_verb="watch the train",
        monologue="I can hear that train before the rails can",
        risk="the crossing would rattle and the gate might stay open too long",
        remedy="pull the gate shut and wave the lantern",
        physical_risk="loud",
        emotional_risk="startled",
        action_tag="train",
        tags={"train", "sound"},
    ),
    "cattle": Challenge(
        id="cattle",
        verb="watch the cattle",
        repeated_verb="watch the cattle",
        monologue="I can count that herd faster than a squirrel can blink",
        risk="the herd would wander into the vegetable patch",
        remedy="swing the gate and steer the herd to the north lane",
        physical_risk="dusty",
        emotional_risk="tense",
        action_tag="cattle",
        tags={"animals", "farm"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with a bright face",
        helps={"train"},
        covers={"dark"},
        use_verb="lift the lantern high",
        tail="lifted the lantern high and let the train know the way",
        tags={"light", "train"},
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a long rope with a sure knot",
        helps={"storm", "cattle"},
        covers={"wind", "gate"},
        use_verb="tie the rope tight",
        tail="tied the rope tight and kept the loose boards from flapping",
        tags={"tool", "storm", "farm"},
    ),
    "boots": Tool(
        id="boots",
        label="boots",
        phrase="a pair of tall boots",
        helps={"river"},
        covers={"wet"},
        use_verb="stomp through the wet path",
        tail="stomped through the wet path and kept their feet dry",
        tags={"tool", "water"},
    ),
    "whistle": Tool(
        id="whistle",
        label="whistle",
        phrase="a tin whistle",
        helps={"cattle"},
        covers={"sound"},
        use_verb="blow the whistle twice",
        tail="blew the whistle twice and turned the herd with one sharp note",
        tags={"tool", "animals"},
    ),
}

NAMES = ["Mabel", "Ivy", "Nell", "Jesse", "Ruth", "Hank", "Ollie", "Pearl"]
QUALITIES = ["brave", "steady", "sly", "quick", "clear-eyed", "stubborn"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    challenge: str
    looker_name: str
    quality: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
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


def challenge_needs_tool(challenge: Challenge, tool: Tool) -> bool:
    return challenge.id in tool.helps


def valid_choices() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for challenge_id in place.affordances:
            ch = _safe_lookup(CHALLENGES, challenge_id)
            for tool_id, tool in TOOLS.items():
                if challenge_needs_tool(ch, tool):
                    out.append((place_id, challenge_id, tool_id))
    return out


def explain_rejection(place: str, challenge: str, tool: str) -> str:
    return (
        f"(No story: {_safe_lookup(TOOLS, tool).label} does not fit the danger of "
        f"{_safe_lookup(CHALLENGES, challenge).verb} at {_safe_lookup(PLACES, place).name}. "
        f"Pick a tool that genuinely helps with that challenge.)"
    )


def introduce(world: World, looker: Entity) -> None:
    world.say(
        f"{looker.id} was a {world.facts['quality']} looker who lived for the far-off view."
    )


def repetitive_boast(world: World, looker: Entity, challenge: Challenge) -> None:
    looker.memes["pride"] = looker.meme("pride") + 1
    world.say(
        f"{looker.id} kept saying, \"I can {challenge.repeated_verb} better than anyone!\""
    )
    world.say(
        f"\"I can {challenge.repeated_verb}, I can {challenge.repeated_verb}, I can {challenge.repeated_verb}.\""
    )


def reach_and_notice(world: World, looker: Entity, challenge: Challenge) -> None:
    looker.memes["worry"] = looker.meme("worry") + 1
    looker.meters["distance"] = 1
    world.say(
        f"Up on {world.place.name}, {looker.id} looked and looked."
    )
    world.say(
        f"Then {looker.id} noticed {challenge.risk}."
    )


def inner_monologue(world: World, looker: Entity, challenge: Challenge) -> None:
    looker.memes["courage"] = looker.meme("courage") + 1
    world.say(
        f"Inside, {looker.id} thought, \"{challenge.monologue}.\""
    )
    world.say(
        f"\"If I keep pretending, the day may get meaner. If I act, the day may turn kinder.\""
    )


def act_with_tool(world: World, looker: Entity, tool: Tool, challenge: Challenge) -> None:
    looker.meters["safety"] = looker.meter("safety") + 1
    looker.meters["wear"] = looker.meter("wear") + 1
    world.say(
        f"So {looker.id} reached for {tool.phrase}."
    )
    world.say(
        f"{tool.use_verb.capitalize()}, and {tool.tail}."
    )
    world.say(
        f"That old tall-tale trick made room for {challenge.remedy}."
    )


def resolve(world: World, looker: Entity, challenge: Challenge) -> None:
    looker.memes["relief"] = looker.meme("relief") + 1
    looker.memes["trust"] = looker.meme("trust") + 1
    world.say(
        f"By the end, {looker.id} was smiling so wide it might have shaded a fence rail."
    )
    world.say(
        f"The trouble was handled, the warning was sent, and the whole place felt safer."
    )
    world.say(
        f"{looker.id} had started with a boast, thought a private thought, and finished with a useful deed."
    )


def tell_story(world: World, params: StoryParams) -> World:
    looker = world.add(
        Entity(
            id=params.looker_name,
            kind="character",
            type="looker",
            label="looker",
            meters={"distance": 0.0, "safety": 0.0, "wear": 0.0},
            memes={"pride": 0.0, "worry": 0.0, "courage": 0.0, "relief": 0.0, "trust": 0.0},
        )
    )
    tool = world.add(
        Entity(
            id=params.tool,
            kind="thing",
            type="tool",
            label=_safe_lookup(TOOLS, params.tool).label,
            phrase=_safe_lookup(TOOLS, params.tool).phrase,
            owner=looker.id,
        )
    )
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    world.facts.update(
        looker=looker,
        tool=tool,
        challenge=challenge,
        quality=params.quality,
        place=params.place,
    )

    introduce(world, looker)
    repetitive_boast(world, looker, challenge)
    world.para()
    reach_and_notice(world, looker, challenge)
    inner_monologue(world, looker, challenge)
    act_with_tool(world, looker, tool, challenge)
    world.para()
    resolve(world, looker, challenge)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall-tale story about a {f["quality"]} looker at {f["place"]} who keeps repeating a boast before choosing a smarter move.',
        f"Tell a child-friendly story where {f['looker'].id} thinks to itself, notices {f['challenge'].risk}, and uses {(f.get('tool') or next(iter(TOOLS.values()))).label} to help.",
        f'Write a story that includes the word "looker", repeats a line for emphasis, and ends with a brave fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    looker: Entity = _safe_fact(world, f, "looker")
    challenge: Challenge = _safe_fact(world, f, "challenge")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    place = _safe_fact(world, f, "place")
    quality = _safe_fact(world, f, "quality")

    return [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"It is about {looker.id}, a {quality} looker with a very far-reaching eye.",
        ),
        QAItem(
            question=f"What did {looker.id} keep repeating before the trouble changed?",
            answer=f"{looker.id} kept repeating that {challenge.repeated_verb} better than anyone.",
        ),
        QAItem(
            question=f"What did {looker.id} think to itself before acting?",
            answer=f"{looker.id} thought, \"{challenge.monologue}.\"",
        ),
        QAItem(
            question=f"What tool helped {looker.id} with the problem?",
            answer=f"{tool.label.capitalize()} helped because it fit the job and let {looker.id} handle the risk.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"The trouble got handled, the warning went out, and {looker.id} finished "
                f"with more courage and relief than pride."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "storm": [
        QAItem(
            question="What is a storm?",
            answer="A storm is rough weather that can bring strong wind, rain, and loud thunder.",
        )
    ],
    "river": [
        QAItem(
            question="What is a river?",
            answer="A river is a long stream of moving water that travels across the land.",
        )
    ],
    "train": [
        QAItem(
            question="What is a train?",
            answer="A train is a long vehicle that rides on tracks and can carry people or cargo.",
        )
    ],
    "cattle": [
        QAItem(
            question="What are cattle?",
            answer="Cattle are large farm animals like cows and bulls.",
        )
    ],
    "lantern": [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern holds light and helps people see when it is dark.",
        )
    ],
    "rope": [
        QAItem(
            question="What is rope for?",
            answer="Rope is strong cord people use to tie, pull, or hold things in place.",
        )
    ],
    "boots": [
        QAItem(
            question="Why wear boots in wet ground?",
            answer="Boots help keep feet dry and steady when the ground is muddy or wet.",
        )
    ],
    "whistle": [
        QAItem(
            question="Why might someone use a whistle?",
            answer="A whistle makes a sharp sound that can carry far and help people pay attention.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    tags |= set(world.facts["tool"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_combo(P, C, T) :- place(P), challenge(C), tool(T),
    affords(P, C), helps(T, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, a))
    for cid, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_choices())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_choices() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_choices():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about a looker, repetition, and inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--quality", choices=QUALITIES)
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
    if getattr(args, "place", None) and getattr(args, "challenge", None) and getattr(args, "tool", None):
        if not (getattr(args, "challenge", None) in _safe_lookup(PLACES, getattr(args, "place", None)).affordances and challenge_needs_tool(_safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(TOOLS, getattr(args, "tool", None)))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_choices()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, challenge, tool = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    quality = getattr(args, "quality", None) or rng.choice(QUALITIES)
    return StoryParams(place=place, challenge=challenge, looker_name=name, quality=quality, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = World(place=_safe_lookup(PLACES, params.place))
    world.facts["params"] = params
    world = tell_story(world, params)
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
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
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [
            generate(StoryParams(place=p, challenge=c, looker_name=_safe_lookup(NAMES, i % len(NAMES)), quality=_safe_lookup(QUALITIES, i % len(QUALITIES)), tool=t))
            for i, (p, c, t) in enumerate(sorted(valid_choices()))
        ]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
