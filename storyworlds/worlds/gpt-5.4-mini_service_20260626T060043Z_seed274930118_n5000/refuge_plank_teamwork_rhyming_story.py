#!/usr/bin/env python3
"""
storyworlds/worlds/refuge_plank_teamwork_rhyming_story.py
==========================================================

A small storyworld about teamwork, a plank, and a safe refuge.

Premise:
A child and a helper are caught in a sudden squall while carrying a little boat
toy and a basket of berries. They need to reach a dry refuge across a shallow
stream. A loose plank can become a bridge, but only if they work together.

The story is written in a gentle rhyming style. The simulation tracks the
physical state of the plank, the stream, the shelter, and the emotional state
of the characters as they plan, lift, balance, and finally make it safely to
refuge.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- imports shared result containers eagerly
- lazily imports ASP helpers only in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    stored_at: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    plank: object | None = None
    refuge: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the meadow path"
    refuge: str = "the little barn"
    stream: str = "the silver stream"
    weather: str = "breezy"
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
class Goal:
    id: str
    verb: str
    gerund: str
    risk: str
    rhyming_hint: str
    keyword: str = "plank"
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
class Tool:
    id: str
    label: str
    phrase: str
    can_bridge: bool = True
    can_huddle: bool = False
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
    refuge: str
    goal: str
    tool: str
    name: str
    helper: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def move_plank(world: World, plank: Entity, from_place: str, to_place: str) -> None:
    plank.stored_at = to_place
    world.say(f"The plank was light in the hand, not hard to span,")
    world.say(f"and soon it was moved from {from_place} to {to_place}.")

def place_bridge(world: World, plank: Entity, actor: Entity, helper: Entity) -> None:
    plank.meters["placed"] = 1
    actor.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"{actor.id} and {helper.id} worked side by side, with a cheerful cheer, "
        f"and set the plank over the stream to make a path clear."
    )

def cross_bridge(world: World, actor: Entity, helper: Entity, refuge: Entity, goal: Goal) -> None:
    actor.meters["safe"] = 1
    helper.meters["safe"] = 1
    actor.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"They tiptoed across, with a hop and a stride, "
        f"to the refuge where dryness and warmth both stayed inside."
    )
    world.say(
        f"{actor.id} smiled at the end, the worry now slight; "
        f"{helper.id} smiled too, for teamwork had turned night to light."
    )

def predict_safe_crossing(world: World, plank: Entity, actor: Entity, helper: Entity, goal: Goal) -> bool:
    sim = world.copy()
    sim.get(plank.id).meters["placed"] = 1
    sim.get(actor.id).meters["safe"] = 1
    sim.get(helper.id).meters["safe"] = 1
    return True


SETTINGS = {
    "meadow": Setting(place="the meadow path", refuge="the little barn", stream="the silver stream", weather="breezy"),
    "orchard": Setting(place="the orchard lane", refuge="the apple shed", stream="the narrow brook", weather="windy"),
    "garden": Setting(place="the garden gate", refuge="the stone nook", stream="the rippling ditch", weather="drizzly"),
}

GOALS = {
    "berries": Goal(
        id="berries",
        verb="carry the berry basket home",
        gerund="carrying the berry basket home",
        risk="the berries might get splashed and spill",
        rhyming_hint="berry and merry",
        keyword="plank",
    ),
    "boat": Goal(
        id="boat",
        verb="save the little boat toy",
        gerund="saving the little boat toy",
        risk="the toy boat might drift away",
        rhyming_hint="boat and float",
        keyword="plank",
    ),
    "lantern": Goal(
        id="lantern",
        verb="bring the lantern to refuge",
        gerund="bringing the lantern to refuge",
        risk="the lantern might wobble and dim",
        rhyming_hint="light and bright",
        keyword="plank",
    ),
}

TOOLS = {
    "plank": Tool(id="plank", label="a plank", phrase="a sturdy plank"),
    "wide_plank": Tool(id="wide_plank", label="a wide plank", phrase="a wide, sturdy plank"),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Sam", "Lily", "Noah"]
HELPERS = ["mother", "father", "grandpa", "grandma", "big sister", "big brother"]
PAIRS = [("girl", "mother"), ("boy", "father"), ("girl", "grandma"), ("boy", "grandpa")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork storyworld with a plank and a refuge.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--refuge", choices={k: v.refuge for k, v in SETTINGS.items()}.values())
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, goal, tool) for place in SETTINGS for goal in GOALS for tool in TOOLS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, goal, tool = rng.choice(list(combos))
    setting = _safe_lookup(SETTINGS, place)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, refuge=setting.refuge, goal=goal, tool=tool, name=name, helper=helper)


def intro(world: World, child: Entity, helper: Entity, goal: Goal, tool: Tool) -> None:
    world.say(
        f"{child.id} was a bright little soul, quick with a grin and ready to stroll, "
        f"and {helper.id} stayed close, with a caring role."
    )
    world.say(
        f"They loved to {goal.verb}, yet the path ahead was not fine; "
        f"for the stream was wide, and the weather was brine."
    )
    world.say(
        f"By the fence lay {tool.phrase}, a simple thing to see, "
        f"and it seemed like the answer to crossing safely."
    )

def conflict(world: World, child: Entity, helper: Entity, goal: Goal) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} looked at the water and sighed, 'Oh dear, oh me! "
        f"{goal.risk}, and we need a way to be free.'"
    )
    world.say(
        f"{helper.id} nodded and said, 'No need to fret; we can make a bridge, "
        f"and get to the refuge yet.'"
    )

def teamwork_plan(world: World, child: Entity, helper: Entity, plank: Entity) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"They lifted the plank together, not one and not lone; "
        f"one held the front, and one held the back like stone."
    )
    world.say(
        f"With a count of 'one, two, three,' they laid it in place, "
        f"and the stream made room for a narrow grace."
    )

def finish(world: World, child: Entity, helper: Entity, refuge: Entity, goal: Goal) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last they reached {refuge.label}, where the air was warm and dry; "
        f"the clouds kept moving on in the sky."
    )
    world.say(
        f"So {child.id} kept {goal.gerund}, safe and light, "
        f"and teamwork made the hard road right."
    )


def tell(setting: Setting, goal: Goal, tool_def: Tool, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="child", label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="helper", label=helper_name))
    plank = world.add(Entity(id="plank", type="plank", label="plank", phrase=tool_def.phrase))
    refuge = world.add(Entity(id="refuge", type="refuge", label=setting.refuge, stored_at=setting.refuge))

    world.say(
        f"On {setting.place}, the wind was brisk, and the day felt small but bright; "
        f"a little refuge waited ahead, like a lantern of light."
    )
    intro(world, child, helper, goal, tool_def)
    world.para()
    conflict(world, child, helper, goal)
    teamwork_plan(world, child, helper, plank)
    place_bridge(world, plank, child, helper)
    world.para()
    cross_bridge(world, child, helper, refuge, goal)
    finish(world, child, helper, refuge, goal)

    world.facts.update(setting=setting, goal=goal, tool=tool_def, child=child, helper=helper, plank=plank, refuge=refuge)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(GOALS, params.goal), _safe_lookup(TOOLS, params.tool), params.name, params.helper)
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
    return [
        "Write a short rhyming story for a small child about teamwork, a plank, and a safe refuge.",
        f"Tell a gentle story where {f['child'].id} and {f['helper'].id} use a plank to reach {f['setting'].refuge}.",
        f"Write a child-friendly rhyme about crossing {f['setting'].stream} together with a plank.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    goal = _safe_fact(world, f, "goal")
    setting = _safe_fact(world, f, "setting")
    refuge = _safe_fact(world, f, "refuge")
    return [
        QAItem(
            question=f"Who worked together in the story?",
            answer=f"{child.id} and {helper.id} worked together as a team."
        ),
        QAItem(
            question=f"What helped them cross the stream?",
            answer=f"They used {(f.get('tool') or next(iter(TOOLS.values()))).phrase} as a bridge over {setting.stream}."
        ),
        QAItem(
            question=f"Where did they end up safe?",
            answer=f"They reached {refuge.label}, which was their refuge."
        ),
        QAItem(
            question=f"What were they trying to do when they needed the plank?",
            answer=f"They were trying to {goal.verb}, but the water made the path tricky."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work so a hard job becomes easier."
        ),
        QAItem(
            question="What is a plank?",
            answer="A plank is a long, flat piece of wood. People can use it as a board or a little bridge."
        ),
        QAItem(
            question="What is a refuge?",
            answer="A refuge is a safe place where someone can rest, hide from trouble, or stay dry and secure."
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.stored_at:
            bits.append(f"stored_at={e.stored_at}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid story needs a place, a goal, a tool, and a safe refuge.
valid_story(P, G, T) :- place(P), goal(G), tool(T), can_bridge(T), goal_needs_plank(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GOALS:
        lines.append(asp.fact("goal", g))
        lines.append(asp.fact("goal_needs_plank", g))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if tool.can_bridge:
            lines.append(asp.fact("can_bridge", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser_all() -> argparse.ArgumentParser:
    return build_parser()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params_wrapper(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, goal, tool) combos:\n")
        for p, g, t in triples:
            print(f"  {p:8} {g:10} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, refuge=_safe_lookup(SETTINGS, p).refuge, goal=g, tool=t, name="Mia", helper="mother")) for p, g, t in valid_combos()]
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, g, t) for p in SETTINGS for g in GOALS for t in TOOLS]


if __name__ == "__main__":
    main()
