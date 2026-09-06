#!/usr/bin/env python3
"""
A tall-tale storyworld about a grand act, a bit of arithmetic, and teak wood.

The seed tale that inspired this world:
- A child tries to put on a brave act.
- They must count and compare pieces with arithmetic.
- Teak wood matters because it is sturdy and valuable.
- A transformation happens when the counting goes wrong.
- The ending is a bad ending: the plan fails, but the world changes.

This world keeps the premise small and classical:
a boastful child plans a big stage act using a teak prop,
then arithmetic decides whether the stunt is safe.
If the numbers do not work out, the prop transforms in a way
that makes the ending funny, lopsided, and sad rather than triumphant.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    count: int = 0
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    extra: object | None = None
    helper: object | None = None
    hero: object | None = None
    teak: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None
    combos: list = field(default_factory=list)
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


SETTINGS = {
    "barnyard": "the barnyard",
    "schoolroom": "the schoolroom",
    "dock": "the dock",
    "orchard": "the orchard",
}

PLACE_DETAILS = {
    "barnyard": ("between the red barn and the hay cart", "a mound of hay", "the weather vane"),
    "schoolroom": ("beneath the high classroom clock", "a pile of old gym mats", "the school bell"),
    "dock": ("beside the tied-up fishing boats", "a coil of soft rope", "the harbor flag"),
    "orchard": ("between two rows of apple trees", "a heap of empty apple sacks", "the tallest pear tree"),
}

NAMES = ["Mabel", "Hank", "Tilly", "Otis", "Nell", "Benny", "Ruby", "Cal"]
HELPERS = ["grandfather", "aunt", "neighbor", "teacher"]


@dataclass
class Gear:
    id: str
    label: str
    goodness: str
    covers: set[str]
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
class ActPlan:
    id: str
    verb: str
    gerund: str
    trick: str
    count_needed: int
    count_extra: int
    prop: str = "teak pieces"
    preparation: str = "build the prop"
    failed_motion: str = "the whole setup toppled"
    risky_word: str = "act"
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


GEAR = [
    Gear(id="ladder", label="a tall ladder", goodness="steady", covers={"up"}),
    Gear(id="stage", label="a little stage", goodness="safe", covers={"up", "front"}),
]

ACTS = {
    "stilt_act": ActPlan(
        id="stilt_act",
        verb="do a daring act on stilts",
        gerund="doing a daring act on stilts",
        trick="balance on one foot while waving a hat",
        count_needed=4,
        count_extra=1,
        prop="two teak stilts",
        preparation="fasten crossbars to the teak stilts",
        failed_motion="the left stilt folded under the first step",
        tags={"act"},
    ),
    "teak_tower_act": ActPlan(
        id="teak_tower_act",
        verb="stack teak blocks into a tower for the act",
        gerund="stacking teak blocks",
        trick="make the tower tall enough to touch the rafters",
        count_needed=6,
        count_extra=2,
        prop="a tower of teak blocks",
        preparation="stack the teak blocks into a narrow tower",
        failed_motion="the tower bowed sideways before the climb began",
        tags={"teak", "act"},
    ),
    "counting_act": ActPlan(
        id="counting_act",
        verb="perform a counting-and-clapping act",
        gerund="doing arithmetic",
        trick="climb a teak staircase and clap on every number",
        count_needed=5,
        count_extra=3,
        prop="a staircase of teak steps",
        preparation="lay out the teak steps in counting order",
        failed_motion="the numbered steps folded into one another",
        tags={"arithmetic", "act"},
    ),
}

TEAK_ITEMS = [
    "smooth teak pieces",
    "golden-brown teak pieces",
    "old teak pieces polished until they shone",
    "sturdy teak pieces borrowed from the workshop",
]

INTRODUCTIONS = [
    "announced a towering act so loudly that everyone nearby came to watch",
    "painted a sign promising the tallest act anyone had ever seen",
    "rang a handbell and promised an act grand enough to tickle the clouds",
    "boasted that the act would make the town clock look short",
]

TRANSFORMATIONS = [
    {
        "kind": "spiraled",
        "phrase": "teak curled into a giant wooden corkscrew",
        "change": "the teak curled into a giant wooden corkscrew, twisting every joint out of line",
        "failure": "the corkscrew-shaped prop spun under the child's first touch",
        "scar": "a spiral-shaped hitching post",
    },
    {
        "kind": "rooted",
        "phrase": "teak rooted itself into the ground",
        "change": "roots burst from the teak and gripped the ground so firmly that six adults could not budge it",
        "failure": "the rooted prop would not move into position for the trick",
        "scar": "a stubborn little teak tree",
    },
    {
        "kind": "shrunken",
        "phrase": "teak shrank to the size of building toys",
        "change": "the teak shrank piece by piece until the entire prop could fit inside a lunch basket",
        "failure": "the tiny prop was much too small to climb or balance upon",
        "scar": "a tiny teak model of the failed act",
    },
    {
        "kind": "hinged",
        "phrase": "teak folded like an accordion",
        "change": "invisible hinges appeared in the teak, and the tall prop folded like an accordion",
        "failure": "the hinged prop snapped shut at the child's first touch",
        "scar": "a zigzag teak bench",
    },
    {
        "kind": "overgrown",
        "phrase": "teak stretched far too tall",
        "change": "the teak shot upward past the promised height and would not stop growing",
        "failure": "the useful end of the prop rose beyond anyone's reach",
        "scar": "a teak pole taller than every roof in town",
    },
]


class WorldModel:
    def __init__(self, world: World) -> None:
        self.world = world
        self.fired: set[str] = set()

    def transform_teak(self, hero: Entity, item: Entity, transformation: dict[str, str]) -> None:
        if "transform" in self.fired:
            return
        self.fired.add("transform")
        item.type = f"{transformation['kind']}_teak"
        item.label = transformation["phrase"]
        item.phrase = transformation["phrase"]
        item.meters["tilt"] = 1
        hero.memes["shock"] = hero.memes.get("shock", 0) + 1
        self.world.say(f"At the sound of the wrong answer, {transformation['change']}.")

    def fail_badly(
        self,
        hero: Entity,
        helper: Entity,
        plan: ActPlan,
        landing: str,
        scar: dict[str, str],
    ) -> None:
        if "bad_end" in self.fired:
            return
        self.fired.add("bad_end")
        hero.memes["disappointment"] = hero.memes.get("disappointment", 0) + 1
        helper.memes["worry"] = helper.memes.get("worry", 0) + 1
        self.world.say(
            f"{hero.label} tried to begin anyway, but {scar['failure']}. "
            f"The sudden stop sent the child tumbling harmlessly into {landing}, while the audience scattered."
        )
        self.world.say(
            f"The promised act never happened. {helper.label.capitalize()} helped {hero.label} "
            "check the piles again, and this time they found the missing pieces."
        )
        self.world.say(
            f"Nobody applauded, and the transformed wood could not be repaired; it remained {scar['scar']}."
        )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall tale about act, arithmetic, and teak.")
    ap.add_argument("--place", choices=SETTINGS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, helper=helper)


def choose_plan(rng: random.Random) -> ActPlan:
    return rng.choice(list(ACTS.values()))


def tell(params: StoryParams, rng: random.Random) -> World:
    world = World(place=_safe_lookup(SETTINGS, params.place))

    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    plan = choose_plan(rng)
    place_detail, landing, landmark = PLACE_DETAILS[params.place]
    needed = plan.count_needed + rng.choice([0, 1, 2, 3])
    shortfall = rng.randint(1, min(3, needed - 2))
    actual_total = needed - shortfall
    first_pile = rng.randint(1, actual_total - 1)
    second_pile = actual_total - first_pile
    claimed_total = needed + rng.choice([0, 1, 2])
    transformation = rng.choice(TRANSFORMATIONS)
    material_description = rng.choice(TEAK_ITEMS)
    announcement = rng.choice(INTRODUCTIONS)
    teak = world.add(Entity(
        id="teak",
        kind="thing",
        type="teak",
        label="teak",
        phrase=material_description,
        count=first_pile,
    ))
    extra = world.add(Entity(
        id="extra",
        kind="thing",
        type="teak",
        label="teak scraps",
        phrase="the second pile of teak pieces",
        count=second_pile,
    ))

    world.say(f"One morning in {world.place}, {hero.label} {announcement}.")
    world.say(
        f"The plan was to {plan.verb}: {hero.pronoun()} would {plan.trick} {place_detail}."
    )
    world.say(
        f"{helper.label.capitalize()} supplied {teak.phrase}. Teak was strong enough for a tall prop, "
        "but only if every piece was counted and fitted correctly."
    )
    world.para()
    world.say(
        f"The plan required {needed} pieces. {hero.label} counted {first_pile} in one pile and "
        f"{second_pile} in another, then cried, \"{first_pile} plus {second_pile} is {claimed_total}! "
        "We have enough!\""
    )
    world.say(
        f"{helper.label.capitalize()} asked for the arithmetic once more. In fact, {first_pile} plus "
        f"{second_pile} was only {actual_total}, leaving {plan.prop} {shortfall} "
        f"{'piece' if shortfall == 1 else 'pieces'} short."
    )
    world.say(
        f"Too proud to delay the crowd, {hero.label} hurried to {plan.preparation} with the incomplete set."
    )

    model = WorldModel(world)
    model.transform_teak(hero, teak, transformation)

    world.para()
    model.fail_badly(hero, helper, plan, landing, transformation)
    world.say(
        f"At sunset, {hero.label} carried the chalked equation home. Beside {landmark}, "
        f"{transformation['scar']} remained as a tall reminder that a confident answer is not always a correct one."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        plan=plan,
        teak=teak,
        extra=extra,
        needed=needed,
        actual_total=actual_total,
        first_pile=first_pile,
        second_pile=second_pile,
        shortfall=shortfall,
        claimed_total=claimed_total,
        material_description=material_description,
        announcement=announcement,
        landmark=landmark,
        transformation=transformation,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    plan = _safe_fact(world, f, "plan")
    return [
        f"Write a tall tale about {hero.label} who wants to {plan.verb} and must use arithmetic to do it.",
        f"Tell a short story where teak matters, the numbers go wrong, and the ending is bad but memorable.",
        f"Write a child-friendly tall tale that includes act, arithmetic, and teak in a funny disaster.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, plan, teak = f["hero"], f["helper"], f["plan"], f["teak"]
    return [
        QAItem(
            question=(
                f"What act did {hero.label} plan after {hero.pronoun()} {f['announcement']}?"
            ),
            answer=(
                f"{hero.label} planned to {plan.verb} in {world.place}, using {plan.prop}. "
                f"The {helper.label} supplied {f['material_description']}, and the plan needed "
                f"{f['needed']} pieces. Before the attempt, {hero.label} wrongly claimed that "
                f"{f['first_pile']} plus {f['second_pile']} was {f['claimed_total']}, and then "
                f"{f['transformation']['change']}."
            ),
        ),
        QAItem(
            question=(
                f"After {hero.label} {f['announcement']}, what arithmetic mistake did "
                f"{hero.pronoun()} make while counting {f['material_description']} for {plan.prop}?"
            ),
            answer=(
                f"{hero.label} had {f['first_pile']} plus {f['second_pile']}, which equals "
                f"{f['actual_total']}. The act needed {f['needed']} pieces, so the setup was "
                f"{f['shortfall']} {'piece' if f['shortfall'] == 1 else 'pieces'} short. The wrong "
                f"answer then caused this transformation: {f['transformation']['change']}."
            ),
        ),
        QAItem(
            question=(
                f"After {hero.label} {f['announcement']}, what happened to {f['material_description']} "
                f"when {hero.pronoun()} claimed that {f['first_pile']} plus {f['second_pile']} was "
                f"{f['claimed_total']} during the {plan.id.replace('_', ' ')}?"
            ),
            answer=(
                f"In {world.place}, the {teak.label}. The act failed, and the wood remained "
                f"{f['transformation']['scar']} beside {f['landmark']}."
            ),
        ),
    ]


def params_placeholder(world: World) -> str:
    return world.facts["hero"].name


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teak?",
            answer="Teak is a hard, strong kind of wood that people use for furniture and sturdy things.",
        ),
        QAItem(
            question="What is arithmetic?",
            answer="Arithmetic is the part of math used for counting, adding, subtracting, and comparing numbers.",
        ),
        QAItem(
            question="What is an act?",
            answer="An act is something a person does, and it can also mean a performance on a stage.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
thing(teak).
concept(act).
concept(arithmetic).

uses_arithmetic(X) :- concept(X), X = arithmetic.
story_word(act).
story_word(arithmetic).
story_word(teak).

valid_story(P) :- place(P), story_word(act), story_word(arithmetic), story_word(teak).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", p) for p in SETTINGS
    ]
    lines += [asp.fact("word", "act"), asp.fact("word", "arithmetic"), asp.fact("word", "teak")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    python_ok = {(p,) for p in SETTINGS}
    if atoms == python_ok:
        print(f"OK: ASP parity matches Python ({len(atoms)} places).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY:", sorted(python_ok))
    return 1


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params, rng)
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
        print("\n-- trace --")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type} label={e.label} count={e.count} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = [StoryParams(place=p, name=n, helper=h) for p in SETTINGS for n in NAMES[:2] for h in HELPERS[:1]]
        for p in combos:
            p.seed = base_seed
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
