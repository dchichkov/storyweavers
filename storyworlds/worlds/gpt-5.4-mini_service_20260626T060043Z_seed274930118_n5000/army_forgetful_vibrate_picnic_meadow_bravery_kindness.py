#!/usr/bin/env python3
"""
A small standalone storyworld: an army scout in a picnic meadow, a vibrating
signal, a forgotten supply crate, and a brave-kind turn that saves the picnic.

The domain is kept intentionally compact and space-adventure flavored: the
"army" is a tiny star-scout crew, the meadow is a peaceful picnic field under
the sky, and the tension comes from a forgetful mistake plus a vibrating beacon
that helps the crew find what they need.
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
# World model
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crate: object | None = None
    gear: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "commander", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"lieutenant", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the picnic meadow"
    sky: str = "bright"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
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
class Gear:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str
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
    place: str
    action: str
    gear: str
    hero_name: str
    hero_type: str
    helper_name: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the picnic meadow", sky="bright", affords={"signal", "search"}),
}

ACTIONS = {
    "signal": Action(
        id="signal",
        verb="tap the beacon",
        gerund="tapping the beacon",
        rush="rush to the beacon",
        mess="vibrate",
        zone={"hands"},
        keyword="vibrate",
        tags={"space", "signal", "vibrate"},
    ),
    "search": Action(
        id="search",
        verb="search for the missing crate",
        gerund="searching for the missing crate",
        rush="hurry across the grass",
        mess="dust",
        zone={"feet"},
        keyword="army",
        tags={"space", "search", "army"},
    ),
}

GEAR = {
    "scanner": Gear(
        id="scanner",
        label="a pocket scanner",
        guards={"vibrate"},
        prep="turn on the pocket scanner",
        tail="followed the scanner's hum",
    ),
    "gloves": Gear(
        id="gloves",
        label="soft gloves",
        guards={"dust"},
        prep="pull on soft gloves",
        tail="tucked the gloves away",
    ),
}

TRAITS = ["forgetful", "careful", "kind", "brave", "gentle"]
NAMES = ["Milo", "Nia", "Tess", "Kai", "Ari", "Sora", "Theo", "Luna"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _narrate_setup(world: World, hero: Entity, helper: Entity, action: Action, gear: Entity) -> None:
    hero.memes["bravery"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{hero.id} was a little {hero.type} in the army scout team, and {helper.id} was the kind helper who kept the camp calm."
    )
    world.say(
        f"At {world.setting.place}, the sky was bright, and the whole meadow looked ready for a tiny space picnic."
    )
    world.say(
        f"{hero.id} loved {action.gerund}, because the little beacon made the grass seem like it could talk to the stars."
    )
    world.say(
        f"The team had {gear.label}, but {hero.id} was a bit forgetful and had left the supply crate behind."
    )


def _predict_missing(world: World, hero: Entity, action: Action, gear: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters[action.mess] = 1.0
    return True if gear.id == "scanner" else False


def _warn(world: World, helper: Entity, hero: Entity, action: Action) -> None:
    world.say(
        f'"If we hurry without checking, the tiny mission could get messy," {helper.id} said.'
    )
    world.say(
        f'{hero.id} heard that, but the urge to {action.verb} was still buzzing.'
    )


def _act_conflict(world: World, hero: Entity, action: Action) -> None:
    hero.memes["forgetful"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} tried to {action.rush}, and the beacon gave a little {action.keyword} vibrate in the grass."
    )


def _resolve(world: World, hero: Entity, helper: Entity, action: Action, gear: Entity) -> None:
    hero.memes["bravery"] += 1
    hero.memes["worry"] = 0.0
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} smiled and said, f\"Let's use {gear.label} first, then we can finish the search together.\""
    )
    world.say(
        f"{hero.id} took a slow breath, and the brave choice made the buzzing feel friendly instead of scary."
    )


def _complete(world: World, hero: Entity, helper: Entity, action: Action, gear: Entity) -> None:
    crate = world.get("crate")
    crate.owner = helper.id
    crate.carried_by = hero.id
    hero.meters["joy"] = hero.meters.get("joy", 0.0) + 1.0
    helper.meters["joy"] = helper.meters.get("joy", 0.0) + 1.0
    world.say(
        f"They found the missing crate under a striped blanket near a daisylike patch of grass."
    )
    world.say(
        f"{hero.id} used the scanner, {helper.id} used kindness, and soon the army picnic was safe again."
    )
    world.say(
        f"At the end, {hero.id} was {action.gerund}, the crate was back in sight, and the meadow felt peaceful and bright."
    )


def tell(setting: Setting, action: Action, gear_def: Gear, hero_name: str, hero_type: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type="lieutenant"))
    gear = world.add(Entity(id=gear_def.id, type="thing", label=gear_def.label))
    crate = world.add(Entity(id="crate", type="thing", label="the supply crate"))
    crate.caretaker = helper.id

    _narrate_setup(world, hero, helper, action, gear)
    world.para()
    _warn(world, helper, hero, action)
    _act_conflict(world, hero, action)
    world.para()
    _resolve(world, hero, helper, action, gear)
    _complete(world, hero, helper, action, gear)

    world.facts.update(
        hero=hero,
        helper=helper,
        gear=gear,
        crate=crate,
        action=action,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Questions and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    return [
        f'Write a short space-adventure story for children about a {hero.type} named {hero.id} who is a little forgetful but still brave.',
        f"Tell a gentle story in the {world.setting.place} where {hero.id} must {action.verb} and kindness helps the team finish the mission.",
        f'Write a story that includes the word "{action.keyword}" and ends with a picnic being saved by a friendly army scout team.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    action = _safe_fact(world, f, "action")
    gear = _safe_fact(world, f, "gear")
    qa = [
        QAItem(
            question=f"Who was the story about in the picnic meadow?",
            answer=f"It was about {hero.id}, a little {hero.type} in the army scout team, and {helper.id}, the kind helper beside them.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry when {hero.id} wanted to {action.verb}?",
            answer=f"{helper.id} worried because {hero.id} was forgetful and had left the supply crate behind, so the tiny mission could get messy.",
        ),
        QAItem(
            question=f"What helped the team after the warning?",
            answer=f"{gear.label} helped the team listen for the beacon, and kindness helped everyone stay calm while they searched.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the crate found, the picnic safe, and {hero.id} still {action.gerund} in the bright meadow.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery help a child do?",
            answer="Bravery helps a child keep going, even when a task feels a little scary or hard.",
        ),
        QAItem(
            question="What does kindness help people do?",
            answer="Kindness helps people be gentle, share, and help each other when something goes wrong.",
        ),
        QAItem(
            question="What is a beacon in a space story?",
            answer="A beacon is a signal that can guide people or machines to the right place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params, generation, emit
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld: army, forgetful, vibrate, picnic meadow.")
    ap.add_argument("--place", choices=["meadow"], default=None)
    ap.add_argument("--action", choices=list(ACTIONS), default=None)
    ap.add_argument("--gear", choices=list(GEAR), default=None)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["boy", "girl", "neutral"])
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
    place = getattr(args, "place", None) or "meadow"
    action = getattr(args, "action", None) or rng.choice(list(ACTIONS))
    gear = getattr(args, "gear", None) or ("scanner" if action == "signal" else "gloves")
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice([n for n in NAMES if n != hero_name])
    hero_type = getattr(args, "gender", None) or rng.choice(["boy", "girl", "neutral"])
    return StoryParams(place=place, action=action, gear=gear, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    if params.place != "meadow":
        pass
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), GEAR[params.gear], params.hero_name, params.hero_type, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A simple declarative twin: this storyworld is valid only in the picnic meadow
% with a compatible action/gear pair.
valid_place(meadow).

valid_action(signal).
valid_action(search).

compatible(signal, scanner).
compatible(search, gloves).

valid_story(P, A, G) :- valid_place(P), valid_action(A), compatible(A, G).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "meadow")]
    lines.append(asp.fact("action", "signal"))
    lines.append(asp.fact("action", "search"))
    lines.append(asp.fact("gear", "scanner"))
    lines.append(asp.fact("gear", "gloves"))
    lines.append(asp.fact("compatible", "signal", "scanner"))
    lines.append(asp.fact("compatible", "search", "gloves"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {("meadow", "signal", "scanner"), ("meadow", "search", "gloves")}
    got = set(asp_valid_stories())
    if got == expected:
        print("OK: ASP matches the scripted compatibility gate.")
        return 0
    print("MISMATCH:")
    print("expected:", sorted(expected))
    print("got:", sorted(got))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="meadow", action="signal", gear="scanner", hero_name="Milo", hero_type="boy", helper_name="Nia"),
    StoryParams(place="meadow", action="search", gear="gloves", hero_name="Luna", hero_type="girl", helper_name="Kai"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
