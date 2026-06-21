#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/genetic_inner_monologue_myth.py
=========================================================

A standalone story world in a child-facing myth style.

This world models a tiny mythic domain: a child from an old family line carries
a small *genetic* mark linked to sun, river, or wind. When a sacred place falls
quiet, the child must bring the right ritual gift to the right place. The story
turn is driven by inner monologue: the hero hears their own worried thoughts,
then chooses courage and tries again.

Run it
------
    python storyworlds/worlds/gpt-5.4/genetic_inner_monologue_myth.py
    python storyworlds/worlds/gpt-5.4/genetic_inner_monologue_myth.py --lineage sun --problem dawn_tree
    python storyworlds/worlds/gpt-5.4/genetic_inner_monologue_myth.py --ritual shell_water
    python storyworlds/worlds/gpt-5.4/genetic_inner_monologue_myth.py --all
    python storyworlds/worlds/gpt-5.4/genetic_inner_monologue_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/genetic_inner_monologue_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Lineage:
    id: str
    element: str
    title: str
    mark: str
    gift: str
    whisper: str
    color: str
    base_courage: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Problem:
    id: str
    need: str
    place: str
    sacred_name: str
    trouble: str
    opening_image: str
    ending_image: str
    restored_meter: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Ritual:
    id: str
    element: str
    label: str
    carry: str
    act: str
    sound: str
    restore_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Helper:
    id: str
    label: str
    type: str
    arrive: str
    advice: str
    comfort: str
    bonus: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    fear_text: str
    fear: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_hesitation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    if hero is None or obstacle is None:
        return out
    if hero.memes["courage"] >= obstacle.meters["fear"]:
        return out
    sig = ("hesitate", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["doubt"] += 1
    hero.meters["hesitation"] += 1
    out.append("__hesitation__")
    return out


def _r_restore(world: World) -> list[str]:
    out: list[str] = []
    place = world.entities.get("place")
    ritual = world.entities.get("ritual")
    if place is None or ritual is None:
        return out
    if ritual.meters["performed"] < THRESHOLD:
        return out
    meter = world.facts.get("restore_meter", "")
    if not meter:
        return out
    sig = ("restore", place.id, meter)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters[meter] += 1
    place.meters["quiet"] = 0.0
    out.append("__restored__")
    return out


CAUSAL_RULES = [
    Rule(name="hesitation", tag="emotional", apply=_r_hesitation),
    Rule(name="restore", tag="physical", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


LINEAGES = {
    "sun": Lineage(
        id="sun",
        element="sun",
        title="House of Dawn",
        mark="a tiny gold spiral on the wrist",
        gift="the dawn-note",
        whisper="Light remembers where to go.",
        color="gold",
        base_courage=2,
        tags={"genetic", "sun"},
    ),
    "river": Lineage(
        id="river",
        element="river",
        title="House of Reeds",
        mark="a silver wave at the ankle",
        gift="the flowing-hum",
        whisper="Even quiet water still knows the sea.",
        color="silver",
        base_courage=1,
        tags={"genetic", "river"},
    ),
    "wind": Lineage(
        id="wind",
        element="wind",
        title="House of Feathers",
        mark="a pale feather-shape behind the ear",
        gift="the sky-breath",
        whisper="Empty air can carry brave songs.",
        color="white",
        base_courage=1,
        tags={"genetic", "wind"},
    ),
}

PROBLEMS = {
    "dawn_tree": Problem(
        id="dawn_tree",
        need="sun",
        place="the hill of first light",
        sacred_name="the Dawn Tree",
        trouble="its leaves had forgotten how to shine",
        opening_image="every morning the village woke to a gray sky instead of a rosy one",
        ending_image="gold fruit glimmered among the branches and warm color ran over the rooftops",
        restored_meter="glow",
        tags={"tree", "sun"},
    ),
    "sleeping_spring": Problem(
        id="sleeping_spring",
        need="river",
        place="the stone bowl beneath the mountain",
        sacred_name="the Sleeping Spring",
        trouble="its water had sunk into silence",
        opening_image="the jars by the village gate stood waiting and dry",
        ending_image="clear water rose singing in the bowl and the jars shone with cold bright drops",
        restored_meter="flow",
        tags={"water", "river"},
    ),
    "still_bells": Problem(
        id="still_bells",
        need="wind",
        place="the tower above the cloud path",
        sacred_name="the Wind Bells",
        trouble="their bronze tongues would not stir",
        opening_image="the valley had no noon song, and even the goats listened for a music that did not come",
        ending_image="the bells rang across the valley and even the clouds seemed to dance aside",
        restored_meter="song",
        tags={"bells", "wind"},
    ),
}

RITUALS = {
    "sun_hymn": Ritual(
        id="sun_hymn",
        element="sun",
        label="sun hymn",
        carry="a little amber bowl",
        act="sang the bright old hymn into the bowl and lifted it toward the east",
        sound="the note opened like a yellow flower",
        restore_text="The waiting light leapt from the bowl into the sacred place.",
        tags={"song", "sun"},
    ),
    "shell_water": Ritual(
        id="shell_water",
        element="river",
        label="shell-water rite",
        carry="a moon-white shell",
        act="poured three drops from the shell and hummed the flowing family note",
        sound="the hum curled softly around the stones",
        restore_text="The hidden water answered from below the earth.",
        tags={"water", "river"},
    ),
    "reed_flute": Ritual(
        id="reed_flute",
        element="wind",
        label="reed-flute rite",
        carry="a reed flute tied with blue thread",
        act="blew one long breath through the flute and held the final note in the air",
        sound="the note flew upward like a thin bright bird",
        restore_text="The waiting wind woke and rushed back into the high places.",
        tags={"flute", "wind"},
    ),
}

HELPERS = {
    "fox": Helper(
        id="fox",
        label="a lantern fox",
        type="fox",
        arrive="A small fox with a tail bright as firelight padded from the stones.",
        advice='"Small steps still climb mountains," the fox seemed to say with its steady eyes.',
        comfort="The fox sat close enough that the path no longer felt lonely.",
        bonus=1,
        tags={"fox"},
    ),
    "heron": Helper(
        id="heron",
        label="a moon heron",
        type="heron",
        arrive="A tall white heron stepped from the reeds as if it had been folded out of mist.",
        advice='"Stand still first," the heron seemed to say. "Then let the true sound find you."',
        comfort="Its quiet patience slowed the hero's breathing.",
        bonus=1,
        tags={"heron"},
    ),
    "grandmother": Helper(
        id="grandmother",
        label="the hero's grandmother",
        type="grandmother",
        arrive="Grandmother climbed the path behind the child, not to do the task, but to witness it.",
        advice='"A gift may begin in blood," she said, "but it becomes real when you choose to use it well."',
        comfort="Her hand on the child's shoulder felt warm and steady.",
        bonus=2,
        tags={"grandmother"},
    ),
}

OBSTACLES = {
    "mist": Obstacle(
        id="mist",
        label="white mist",
        scene="white mist braided itself across the path and hid the next few steps",
        fear_text="The hidden path made the hero wonder if they had come to the wrong place.",
        fear=1,
        tags={"mist"},
    ),
    "echoes": Obstacle(
        id="echoes",
        label="echo cave",
        scene="old echoes circled back from the rocks and made every small sound feel thin",
        fear_text="The bouncing sounds made the hero afraid their own voice was too small.",
        fear=2,
        tags={"echo"},
    ),
    "storm": Obstacle(
        id="storm",
        label="high storm",
        scene="a hard wind shook the stones and clouds pressed low over the sacred place",
        fear_text="The fierce sky made the hero think one child could not possibly be enough.",
        fear=3,
        tags={"storm"},
    ),
}

GIRL_NAMES = ["Iria", "Nera", "Luma", "Tala", "Mira", "Sena"]
BOY_NAMES = ["Orin", "Tarin", "Elio", "Maren", "Kian", "Rami"]
TRAITS = ["gentle", "thoughtful", "steady", "curious", "earnest", "quiet"]


def valid_combo(lineage: Lineage, problem: Problem, ritual: Ritual) -> bool:
    return lineage.element == problem.need == ritual.element


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lid, lineage in LINEAGES.items():
        for pid, problem in PROBLEMS.items():
            for rid, ritual in RITUALS.items():
                if valid_combo(lineage, problem, ritual):
                    combos.append((lid, pid, rid))
    return combos


def courage_score(params: "StoryParams") -> int:
    lineage = LINEAGES[params.lineage]
    helper = HELPERS[params.helper]
    return lineage.base_courage + helper.bonus


def outcome_of(params: "StoryParams") -> str:
    courage = courage_score(params)
    fear = OBSTACLES[params.obstacle].fear
    return "direct" if courage >= fear else "second_try"


@dataclass
class StoryParams:
    lineage: str
    problem: str
    ritual: str
    helper: str
    obstacle: str
    hero: str
    gender: str
    trait: str
    seed: Optional[int] = None
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


def explain_rejection(lineage: Lineage, problem: Problem, ritual: Ritual) -> str:
    return (
        f"(No story: {lineage.title} carries a {lineage.element} gift, but "
        f"{problem.sacred_name} needs {problem.need} and the ritual '{ritual.label}' "
        f"belongs to {ritual.element}. In this myth world, lineage, trouble, and ritual "
        f"must all answer the same sacred element.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child with a genetic family gift, an inner monologue, and a mythic repair."
    )
    ap.add_argument("--lineage", choices=LINEAGES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_hero(rng: random.Random, gender: Optional[str], hero: Optional[str]) -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    if hero:
        return hero, g
    pool = GIRL_NAMES if g == "girl" else BOY_NAMES
    return rng.choice(pool), g


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lineage and args.problem and args.ritual:
        lineage = LINEAGES[args.lineage]
        problem = PROBLEMS[args.problem]
        ritual = RITUALS[args.ritual]
        if not valid_combo(lineage, problem, ritual):
            raise StoryError(explain_rejection(lineage, problem, ritual))

    combos = [
        c for c in valid_combos()
        if (args.lineage is None or c[0] == args.lineage)
        and (args.problem is None or c[1] == args.problem)
        and (args.ritual is None or c[2] == args.ritual)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lineage_id, problem_id, ritual_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    obstacle_id = args.obstacle or rng.choice(sorted(OBSTACLES))
    hero_name, gender = _pick_hero(rng, args.gender, args.hero)
    trait = rng.choice(TRAITS)
    return StoryParams(
        lineage=lineage_id,
        problem=problem_id,
        ritual=ritual_id,
        helper=helper_id,
        obstacle=obstacle_id,
        hero=hero_name,
        gender=gender,
        trait=trait,
    )


def introduce(world: World, hero: Entity, lineage: Lineage, problem: Problem) -> None:
    world.say(
        f"In the old valley, where myths were treated like true memories, {hero.id} was a {hero.attrs['age_word']} {hero.type} from the {lineage.title}. "
        f"On {hero.pronoun('possessive')} skin lay {lineage.mark}, a little genetic sign that every child in that line was born with."
    )
    world.say(
        f"People said the mark did not make a person great by itself. It only meant the ancient family gift, {lineage.gift}, might one day answer when the child called."
    )
    world.say(
        f"That season, {problem.sacred_name} was troubled: {problem.trouble}, and {problem.opening_image}."
    )


def call_to_task(world: World, hero: Entity, lineage: Lineage, problem: Problem, ritual: Ritual) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"So the elders sent {hero.id} to {problem.place} with {ritual.carry}. Only a child of that line could try the old {ritual.label} there."
    )
    hero.memes["doubt"] += 1
    world.say(
        f'Inside, {hero.id} thought, "What if my mark is only a mark? What if I carry the gift of {lineage.title} and still fail?"'
    )


def journey(world: World, hero: Entity, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["fear"] = float(obstacle.fear)
    world.say(
        f"The path was steep, and {obstacle.scene}. {obstacle.fear_text}"
    )


def helper_arrives(world: World, hero: Entity, helper: Helper) -> None:
    guide = world.get("helper")
    hero.memes["hope"] += 1
    hero.memes["courage"] += helper.bonus
    world.say(helper.arrive)
    world.say(helper.advice)
    world.say(helper.comfort)


def first_try(world: World, hero: Entity, ritual: Ritual) -> None:
    ritual_ent = world.get("ritual")
    ritual_ent.meters["performed"] += 1
    world.say(
        f"{hero.id} stood before the sacred place and {ritual.act}. {ritual.sound}"
    )


def direct_restoration(world: World, hero: Entity, problem: Problem, ritual: Ritual) -> None:
    place = world.get("place")
    propagate(world, narrate=False)
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    world.say(ritual.restore_text)
    world.say(
        f"At once, {problem.ending_image}. {hero.id} felt the family gift move through {hero.pronoun('object')} like something remembered at exactly the right moment."
    )
    world.facts["restored_now"] = place.meters[problem.restored_meter] >= THRESHOLD


def falter(world: World, hero: Entity, problem: Problem) -> None:
    propagate(world, narrate=False)
    hero.memes["fear"] += 1
    world.say(
        f"For a moment, nothing changed. The sacred place stayed quiet, and {hero.id}'s heart felt small inside {hero.pronoun('possessive')} chest."
    )
    world.say(
        f'Inside, {hero.id} thought, "Maybe the old stories were too large for me."'
    )


def inner_turn(world: World, hero: Entity, lineage: Lineage, helper: Helper) -> None:
    hero.memes["courage"] += 1
    hero.memes["doubt"] = 0.0
    hero.memes["choice"] += 1
    world.say(
        f"Then {hero.id} remembered {lineage.whisper}"
    )
    world.say(
        f'Inside, {hero.pronoun()} answered {hero.pronoun("object")}self, "The gift may have come to me through my family, but the brave part is my choice."'
    )
    if helper.id == "grandmother":
        world.say(
            "Grandmother nodded, as if she had heard the thought without a sound."
        )


def second_try(world: World, hero: Entity, ritual: Ritual, problem: Problem) -> None:
    ritual_ent = world.get("ritual")
    ritual_ent.meters["performed"] += 1
    world.say(
        f"{hero.id} drew one deeper breath and {ritual.act}. This time the sound was steadier, warmer, and true."
    )
    propagate(world, narrate=False)
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    world.say(ritual.restore_text)
    world.say(
        f"Now {problem.ending_image}."
    )


def return_home(world: World, hero: Entity, problem: Problem) -> None:
    village = world.get("village")
    village.memes["gratitude"] += 1
    world.say(
        f"When {hero.id} came home, the valley did not merely look different. It sounded and smelled alive again, and everyone could see what had changed."
    )
    world.say(
        f"From then on, whenever children asked about the family mark, the grown-ups said it was a genetic beginning, not an ending. A person still had to listen inward, choose well, and act with care."
    )


def tell(
    lineage: Lineage,
    problem: Problem,
    ritual: Ritual,
    helper: Helper,
    obstacle: Obstacle,
    hero_name: str,
    gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"age_word": "young", "hero_name": hero_name},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper.type,
        label=helper.label,
        role="helper",
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="sacred_place",
        label=problem.sacred_name,
        role="place",
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="the valley village",
    ))
    ritual_ent = world.add(Entity(
        id="ritual",
        kind="thing",
        type="ritual",
        label=ritual.label,
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
    ))

    hero.memes["courage"] = float(lineage.base_courage)
    hero.memes["doubt"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["wonder"] = 0.0
    place.meters["quiet"] = 1.0
    place.meters["glow"] = 0.0
    place.meters["flow"] = 0.0
    place.meters["song"] = 0.0
    ritual_ent.meters["performed"] = 0.0
    obstacle_ent.meters["fear"] = float(obstacle.fear)
    world.facts["restore_meter"] = problem.restored_meter
    world.facts["problem"] = problem
    world.facts["lineage"] = lineage
    world.facts["ritual_cfg"] = ritual
    world.facts["helper_cfg"] = helper
    world.facts["obstacle_cfg"] = obstacle

    introduce(world, hero, lineage, problem)
    world.para()
    call_to_task(world, hero, lineage, problem, ritual)
    journey(world, hero, obstacle)
    helper_arrives(world, hero, helper)

    world.para()
    first_try(world, hero, ritual)
    direct = hero.memes["courage"] >= obstacle.fear
    if direct:
        direct_restoration(world, hero, problem, ritual)
        outcome = "direct"
    else:
        falter(world, hero, problem)
        inner_turn(world, hero, lineage, helper)
        second_try(world, hero, ritual, problem)
        outcome = "second_try"

    world.para()
    return_home(world, hero, problem)

    world.facts.update(
        hero=hero,
        helper=helper_ent,
        place=place,
        village=village,
        ritual=ritual_ent,
        obstacle=obstacle_ent,
        outcome=outcome,
        restored=place.meters[problem.restored_meter] >= THRESHOLD,
        direct=(outcome == "direct"),
        hero_name=hero_name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    lineage = world.facts["lineage"]
    problem = world.facts["problem"]
    ritual = world.facts["ritual_cfg"]
    helper = world.facts["helper_cfg"]
    hero = world.facts["hero"]
    return [
        f'Write a short myth for a young child that includes the word "genetic" and uses inner monologue. The hero comes from a family with a sacred {lineage.element} gift.',
        f"Tell a mythic story about a child named {hero.attrs['hero_name']} who goes to restore {problem.sacred_name} with the {ritual.label}, and let the turning point happen inside the child's own thoughts.",
        f"Write a gentle myth where {helper.label} helps a worried child trust an inherited family gift without making the gift feel automatic or easy.",
    ]


KNOWLEDGE = {
    "genetic": [
        (
            "What does genetic mean?",
            "Genetic means something is passed from parents or family to a child through the body. In real life, a genetic trait can shape how a person looks or works, but it does not decide every choice they make.",
        )
    ],
    "sun": [
        (
            "Why do old myths connect the sun with songs or light?",
            "Many myths treat the sun like a living power that wakes the world each morning. A song or prayer in a myth can stand for calling that light back.",
        )
    ],
    "river": [
        (
            "Why is fresh water important in stories and in life?",
            "Fresh water helps people, animals, and plants live. In stories, a spring or river often stands for life returning after a hard time.",
        )
    ],
    "wind": [
        (
            "Why do bells ring when the wind moves them?",
            "Wind pushes the bells so the parts inside strike the metal and make sound. That is why still air makes quiet bells, and moving air makes singing ones.",
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a musical instrument that makes sound when air moves through it. It turns breath into music.",
        )
    ],
    "fox": [
        (
            "Why do myths often use animals as guides?",
            "Myths use animals as guides because animals can feel close to the wild world and its secrets. A guide animal often helps a hero notice courage or wisdom.",
        )
    ],
    "heron": [
        (
            "Why might a heron symbolize patience?",
            "A heron can stand very still while it waits, so stories often use it as a sign of patience and careful attention.",
        )
    ],
    "grandmother": [
        (
            "Why are grandparents often wise in stories?",
            "Grandparents in stories have lived through many seasons, so they can share memory and calm. They often remind younger characters that growing brave takes practice.",
        )
    ],
}
KNOWLEDGE_ORDER = ["genetic", "sun", "river", "wind", "flute", "fox", "heron", "grandmother"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    lineage = world.facts["lineage"]
    problem = world.facts["problem"]
    ritual = world.facts["ritual_cfg"]
    helper = world.facts["helper_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['hero_name']}, a young child from the {lineage.title}. {hero.pronoun().capitalize()} carries {lineage.mark}, which the story calls a small genetic family sign.",
        ),
        (
            f"What was wrong with {problem.sacred_name}?",
            f"{problem.sacred_name} was in trouble because {problem.trouble}. That is why the whole valley felt wrong at the beginning.",
        ),
        (
            f"Why did {hero.attrs['hero_name']} go to {problem.place}?",
            f"{hero.pronoun().capitalize()} went there to use the {ritual.label} and try to restore the sacred place. Only a child whose family gift matched that trouble could honestly attempt it.",
        ),
        (
            "What did the hero think inside?",
            f"Inside, {hero.attrs['hero_name']} worried that the family mark might not be enough. Those thoughts mattered because the story's turning point comes when the child answers that fear with a choice to be brave.",
        ),
        (
            f"How did {helper.label} help?",
            f"{helper.label.capitalize()} helped by giving calm company and wise advice. That support made the task feel less lonely and helped the hero hold steady in front of {obstacle.label}.",
        ),
    ]
    if outcome == "direct":
        qa.append(
            (
                "Did the ritual work right away?",
                f"Yes. The first try worked because the hero had enough courage to meet the fear of the moment, and the sacred place answered at once.",
            )
        )
    else:
        qa.append(
            (
                "Why did the first try fail, and what changed on the second try?",
                f"The first try faltered because the fear of {obstacle.label} made the hero's heart shrink, and the sacred place stayed quiet for a moment. On the second try, the hero listened to the inner voice, chose courage, and performed the ritual more truly.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {problem.ending_image}. That final picture proves the world was healed and that the hero had grown into the family gift.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    lineage = world.facts["lineage"]
    ritual = world.facts["ritual_cfg"]
    helper = world.facts["helper_cfg"]
    tags: set[str] = {"genetic", lineage.element}
    if "flute" in ritual.tags:
        tags.add("flute")
    tags |= helper.tags
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lineage="sun",
        problem="dawn_tree",
        ritual="sun_hymn",
        helper="grandmother",
        obstacle="storm",
        hero="Iria",
        gender="girl",
        trait="steady",
    ),
    StoryParams(
        lineage="river",
        problem="sleeping_spring",
        ritual="shell_water",
        helper="heron",
        obstacle="echoes",
        hero="Orin",
        gender="boy",
        trait="thoughtful",
    ),
    StoryParams(
        lineage="wind",
        problem="still_bells",
        ritual="reed_flute",
        helper="fox",
        obstacle="storm",
        hero="Luma",
        gender="girl",
        trait="quiet",
    ),
    StoryParams(
        lineage="wind",
        problem="still_bells",
        ritual="reed_flute",
        helper="grandmother",
        obstacle="mist",
        hero="Tarin",
        gender="boy",
        trait="earnest",
    ),
    StoryParams(
        lineage="river",
        problem="sleeping_spring",
        ritual="shell_water",
        helper="fox",
        obstacle="storm",
        hero="Mira",
        gender="girl",
        trait="gentle",
    ),
]


ASP_RULES = r"""
valid(L,P,R) :- lineage(L,E), problem(P,E), ritual(R,E).

courage(V) :- chosen_lineage(L), base_courage(L,B), chosen_helper(H), helper_bonus(H,HB), V = B + HB.
direct      :- chosen_obstacle(O), obstacle_fear(O,F), courage(C), C >= F.
outcome(direct) :- direct.
outcome(second_try) :- not direct.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lid, lineage in LINEAGES.items():
        lines.append(asp.fact("lineage", lid, lineage.element))
        lines.append(asp.fact("base_courage", lid, lineage.base_courage))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid, problem.need))
    for rid, ritual in RITUALS.items():
        lines.append(asp.fact("ritual", rid, ritual.element))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_bonus", hid, helper.bonus))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_fear", oid, obstacle.fear))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_lineage", params.lineage),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_obstacle", params.obstacle),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("lineage", LINEAGES),
        ("problem", PROBLEMS),
        ("ritual", RITUALS),
        ("helper", HELPERS),
        ("obstacle", OBSTACLES),
    ):
        key = getattr(params, field_name)
        if key not in registry:
            raise StoryError(f"(Invalid {field_name}: {key})")

    lineage = LINEAGES[params.lineage]
    problem = PROBLEMS[params.problem]
    ritual = RITUALS[params.ritual]
    if not valid_combo(lineage, problem, ritual):
        raise StoryError(explain_rejection(lineage, problem, ritual))

    world = tell(
        lineage=lineage,
        problem=problem,
        ritual=ritual,
        helper=HELPERS[params.helper],
        obstacle=OBSTACLES[params.obstacle],
        hero_name=params.hero,
        gender=params.gender,
        trait=params.trait,
    )

    return StorySample(
        params=params,
        story=world.render().replace(" hero ", f" {params.hero} "),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    text = sample.story.replace("hero", sample.params.hero)
    text = text.replace("hero's", f"{sample.params.hero}'s")
    text = text.replace("hero.", f"{sample.params.hero}.")
    if header:
        print(header)
    print(text)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lineage, problem, ritual) combos:\n")
        for lineage, problem, ritual in combos:
            print(f"  {lineage:8} {problem:16} {ritual}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.lineage} / {p.problem} / {p.ritual} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
