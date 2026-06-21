#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boiled_homosexual_sound_effects_kindness_mystery_to.py
==================================================================================

A standalone storyworld for a small comic mystery: a child hears silly kitchen
sound effects while food boils, starts to wonder what secret creature or trick is
hiding in the pot, and solves the mystery by investigating kindly instead of
blaming someone.

This world is built around a tight causal shape:

    setup: a child is cooking with two loving parents in a warm home
    tension: a pot starts making odd comic sounds
    wrong guess: someone or something is suspected
    turn: the child chooses kindness and careful checking
    resolution: the harmless cause is found, and the family laughs

The generated stories stay in one tiny domain and prefer only plausible,
common-sense combinations. The mystery is always solvable from the simulated
state, and the prose is driven by that state.

Run it
------
    python storyworlds/worlds/gpt-5.4/boiled_homosexual_sound_effects_kindness_mystery_to.py
    python storyworlds/worlds/gpt-5.4/boiled_homosexual_sound_effects_kindness_mystery_to.py --meal soup --source lid
    python storyworlds/worlds/gpt-5.4/boiled_homosexual_sound_effects_kindness_mystery_to.py --meal cocoa
    python storyworlds/worlds/gpt-5.4/boiled_homosexual_sound_effects_kindness_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/boiled_homosexual_sound_effects_kindness_mystery_to.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/boiled_homosexual_sound_effects_kindness_mystery_to.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Meal:
    id: str
    label: str
    phrase: str
    vessel: str
    boiling_word: str
    aroma: str
    safe_source_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Source:
    id: str
    label: str
    place: str
    sounds: list[str]
    cause: str
    reveal: str
    kind: str
    works_with: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    label: str
    phrase: str
    innocent_reason: str
    kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Method:
    id: str
    label: str
    sense: int
    kind: str
    text: str
    qa_text: str
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


def _r_noise(world: World) -> list[str]:
    pot = world.get("pot")
    if pot.meters["boiling"] < THRESHOLD or world.facts.get("source_active") is not True:
        return []
    sig = ("noise", world.facts.get("source_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pot.meters["noise"] += 1
    for eid in ("child", "dad1", "dad2"):
        if eid in world.entities:
            world.get(eid).memes["wonder"] += 1
    return ["__noise__"]


def _r_blame(world: World) -> list[str]:
    child = world.get("child")
    suspect = world.get("suspect")
    if child.memes["blame"] < THRESHOLD:
        return []
    sig = ("blame", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["worry"] += 1
    return ["__blame__"]


def _r_kindness(world: World) -> list[str]:
    child = world.get("child")
    suspect = world.get("suspect")
    if child.memes["kindness"] < THRESHOLD or suspect.memes["worry"] < THRESHOLD:
        return []
    sig = ("kindness", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["worry"] = 0.0
    suspect.memes["relief"] += 1
    return ["__kindness__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="blame", tag="social", apply=_r_blame),
    Rule(name="kindness", tag="social", apply=_r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def source_works(meal: Meal, source: Source) -> bool:
    return source.id in meal.safe_source_ids and meal.id in source.works_with


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def predict_noise(world: World, source_id: str) -> dict:
    sim = world.copy()
    sim.facts["source_active"] = True
    sim.facts["source_id"] = source_id
    sim.get("pot").meters["boiling"] += 1
    propagate(sim, narrate=False)
    return {
        "noisy": sim.get("pot").meters["noise"] >= THRESHOLD,
        "wonder": sim.get("child").memes["wonder"],
    }


def introduce(world: World, child: Entity, dad1: Entity, dad2: Entity, meal: Meal) -> None:
    child.memes["joy"] += 1
    dad1.memes["joy"] += 1
    dad2.memes["joy"] += 1
    world.say(
        f"{child.id} was helping {dad1.id} and {dad2.id} make {meal.phrase} in the kitchen. "
        f"The family was cheerful, and the room already smelled like {meal.aroma}."
    )
    world.say(
        f"Sometimes grown-ups used the word homosexual for a family with two dads or two moms in love, "
        f"and {child.id} knew it was just another true word for love in their home."
    )


def start_boiling(world: World, child: Entity, meal: Meal) -> None:
    pot = world.get("pot")
    pot.meters["boiling"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Soon the {meal.vessel} on the stove began to boil. "
        f'"{meal.boiling_word}!" said {child.id}, wiggling with excitement.'
    )


def hear_sounds(world: World, child: Entity, source: Source) -> None:
    pred = predict_noise(world, source.id)
    world.facts["predicted_wonder"] = pred["wonder"]
    world.facts["source_active"] = True
    world.facts["source_id"] = source.id
    propagate(world, narrate=False)
    sound_text = " ".join(source.sounds)
    world.say(
        f"Then the kitchen filled with sound effects: {sound_text} "
        f"{child.id} blinked at the {source.place}."
    )
    world.say(
        f'"That is either a tiny kitchen band or a mystery to solve," {child.id} said.'
    )


def guess_wrong(world: World, child: Entity, suspect: Suspect) -> None:
    child.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} looked at {suspect.phrase}. "Was it {suspect.label}?" {child.pronoun()} whispered.'
    )


def kind_pause(world: World, dad1: Entity, dad2: Entity, child: Entity, suspect: Suspect) -> None:
    child.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{dad1.id} knelt beside {child.id}. "Let\'s be kind before we blame," {dad1.pronoun()} said. '
        f'{dad2.id} nodded and reminded {child.pronoun("object")} that {suspect.innocent_reason}.'
    )
    world.say(
        f'{child.id} took a slow breath. "Okay," {child.pronoun()} said. "We can solve the mystery nicely."'
    )


def investigate(world: World, method: Method, source: Source) -> None:
    child = world.get("child")
    child.memes["care"] += 1
    world.say(method.text.format(place=source.place, label=source.label))


def solve_mystery(world: World, child: Entity, source: Source, meal: Meal) -> None:
    world.facts["solved"] = True
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(source.reveal.format(meal=meal.label))
    world.say(
        f'"So that was it!" laughed {child.id}. "Not a monster. Just {source.cause}."'
    )


def ending(world: World, child: Entity, dad1: Entity, dad2: Entity, meal: Meal, suspect: Suspect) -> None:
    child.memes["lesson"] += 1
    dad1.memes["love"] += 1
    dad2.memes["love"] += 1
    world.say(
        f"{suspect.label.capitalize()} was innocent, the mystery was solved, and everybody giggled. "
        f"The {meal.label} kept bubbling while the three of them added one last stir."
    )
    world.say(
        f"At supper, {child.id} made the sound effects again -- \"{world.facts['closing_sound']}\" -- "
        f"and even {dad1.id} nearly laughed soup through {dad1.pronoun('possessive')} nose."
    )


def tell(
    meal: Meal,
    source: Source,
    suspect: Suspect,
    method: Method,
    child_name: str = "Nico",
    child_type: str = "boy",
    dad1_name: str = "Papa Ben",
    dad2_name: str = "Dad Luis",
    pet_name: str = "Pickles",
    helper_trait: str = "patient",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    dad1 = world.add(Entity(id="dad1", kind="character", type="father", label=dad1_name, role="parent",
                            traits=[helper_trait]))
    dad2 = world.add(Entity(id="dad2", kind="character", type="father", label=dad2_name, role="parent",
                            traits=["funny"]))
    pot = world.add(Entity(id="pot", kind="thing", type="pot", label=meal.vessel))
    suspect_ent = world.add(Entity(id="suspect", kind="thing", type=suspect.kind, label=suspect.label,
                                   attrs={"pet_name": pet_name}))
    child.attrs["name"] = child_name
    dad1.attrs["name"] = dad1_name
    dad2.attrs["name"] = dad2_name
    pot.attrs["meal"] = meal.id
    world.facts["source_active"] = False
    world.facts["source_id"] = source.id
    world.facts["closing_sound"] = source.sounds[0].strip("!?,.")
    world.facts["solved"] = False

    introduce(world, child, dad1, dad2, meal)
    start_boiling(world, child, meal)

    world.para()
    hear_sounds(world, child, source)
    guess_wrong(world, child, suspect)
    kind_pause(world, dad1, dad2, child, suspect)

    world.para()
    investigate(world, method, source)
    solve_mystery(world, child, source, meal)
    ending(world, child, dad1, dad2, meal, suspect)

    world.facts.update(
        meal=meal,
        source=source,
        suspect_cfg=suspect,
        method=method,
        child=child,
        dad1=dad1,
        dad2=dad2,
        pot=pot,
        innocent=suspect_ent.memes["relief"] >= THRESHOLD,
        blamed=suspect_ent.memes["worry"] < THRESHOLD and child.memes["blame"] >= THRESHOLD,
    )
    return world


MEALS = {
    "soup": Meal(
        id="soup",
        label="tomato soup",
        phrase="a red pot of tomato soup",
        vessel="pot",
        boiling_word="It boiled and bobbled",
        aroma="warm tomatoes and butter",
        safe_source_ids={"lid", "spoon"},
        tags={"boiled", "kitchen"},
    ),
    "eggs": Meal(
        id="eggs",
        label="boiled eggs",
        phrase="a pan of boiled eggs",
        vessel="pan",
        boiling_word="The eggs were getting properly boiled",
        aroma="toast and a little steam",
        safe_source_ids={"egg_tap", "lid"},
        tags={"boiled", "kitchen", "eggs"},
    ),
    "cocoa": Meal(
        id="cocoa",
        label="hot cocoa",
        phrase="a small pot of cocoa",
        vessel="pot",
        boiling_word="The cocoa was close to a bubbly boil",
        aroma="chocolate and cinnamon",
        safe_source_ids={"spoon"},
        tags={"boiled", "kitchen", "cocoa"},
    ),
}

SOURCES = {
    "lid": Source(
        id="lid",
        label="the loose lid",
        place="pot",
        sounds=["Clink!", "clink!", "clink!"],
        cause="a lid dancing on little puffs of steam",
        reveal="When they peeked closer, they found the loose lid hopping in tiny jumps over the {meal}.",
        kind="lid",
        works_with={"soup", "eggs"},
        tags={"steam", "lid", "sound"},
    ),
    "spoon": Source(
        id="spoon",
        label="the long spoon",
        place="pot",
        sounds=["Tonk!", "tonk!", "swish!"],
        cause="a spoon bumping the side whenever the bubbles rolled under it",
        reveal="Inside the pot, the long spoon had slid sideways, and each rising bubble nudged it against the rim of the {meal}.",
        kind="spoon",
        works_with={"soup", "cocoa"},
        tags={"spoon", "sound"},
    ),
    "egg_tap": Source(
        id="egg_tap",
        label="one bouncing egg",
        place="pan",
        sounds=["Tok!", "tok!", "tok!"],
        cause="an egg gently tapping the pan as the water jiggled",
        reveal="The mystery turned out to be one bouncing egg, softly tapping the side of the pan while the water danced.",
        kind="egg",
        works_with={"eggs"},
        tags={"egg", "sound"},
    ),
}

SUSPECTS = {
    "pet": Suspect(
        id="pet",
        label="Pickles the cat",
        phrase="Pickles the cat under the chair",
        innocent_reason="Pickles had only been licking one paw and blinking sleepily",
        kind="animal",
        tags={"pet", "kindness"},
    ),
    "dad": Suspect(
        id="dad",
        label="Dad Luis",
        phrase="Dad Luis by the sink",
        innocent_reason="Dad Luis was only slicing bread and making a silly face at the steam",
        kind="person",
        tags={"family", "kindness"},
    ),
    "ladle": Suspect(
        id="ladle",
        label="the soup ladle",
        phrase="the soup ladle on the towel",
        innocent_reason="the soup ladle was lying still on the towel and had not moved at all",
        kind="tool",
        tags={"kitchen", "kindness"},
    ),
}

METHODS = {
    "peek": Method(
        id="peek",
        label="peek together",
        sense=3,
        kind="observe",
        text="They stood on tiptoe together and took a careful peek at the {place}.",
        qa_text="They solved it by taking a careful peek together before blaming anyone.",
        tags={"observe", "kindness"},
    ),
    "listen": Method(
        id="listen",
        label="listen close",
        sense=3,
        kind="observe",
        text='First they went still and listened close. "The sound is coming from the {place}," said {label}.',
        qa_text="They solved it by stopping, listening carefully, and following the sound.",
        tags={"observe", "listening"},
    ),
    "shake": Method(
        id="shake",
        label="shake the pot",
        sense=1,
        kind="rough",
        text="They gave the pot a big shake right away.",
        qa_text="They shook the pot.",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Ella", "June", "Nora"]
BOY_NAMES = ["Nico", "Leo", "Milo", "Finn", "Toby", "Eli"]
PET_NAMES = ["Pickles", "Bean", "Muffin", "Pepper"]
TRAITS = ["patient", "gentle", "funny", "calm"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for meal_id, meal in MEALS.items():
        for source_id, source in SOURCES.items():
            if source_works(meal, source):
                combos.append((meal_id, source_id))
    return combos


@dataclass
class StoryParams:
    meal: str
    source: str
    suspect: str
    method: str
    child_name: str
    child_gender: str
    dad1_name: str
    dad2_name: str
    pet_name: str
    helper_trait: str
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


KNOWLEDGE = {
    "boiled": [
        (
            "What does boiled mean?",
            "Boiled means something got very hot in bubbling water or liquid. You often see little bubbles rise and pop."
        )
    ],
    "steam": [
        (
            "Why do pots sometimes make little noises when food boils?",
            "Boiling water makes bubbles and steam push things around. A lid or spoon can rattle when those bubbles bump it."
        )
    ],
    "sound": [
        (
            "What are sound effects?",
            "Sound effects are playful words like clink, tok, and swish that help you hear a scene in your mind. They can make a story feel funny and lively."
        )
    ],
    "kindness": [
        (
            "What does it mean to be kind when something seems wrong?",
            "It means you do not blame or scold too fast. You slow down, think, and treat people gently while you figure out what happened."
        )
    ],
    "mystery": [
        (
            "What is a mystery to solve?",
            "A mystery is something you do not understand yet. You solve it by noticing clues and checking carefully."
        )
    ],
    "pet": [
        (
            "Why should you not blame a pet too quickly?",
            "Pets cannot explain themselves with long words. It is kinder to look for the real cause first."
        )
    ],
    "homosexual": [
        (
            "What does homosexual mean?",
            "Homosexual is a word for a person who loves someone of the same gender in a grown-up way. In this story, it is simply one more word about a loving family."
        )
    ],
}
KNOWLEDGE_ORDER = ["boiled", "steam", "sound", "kindness", "mystery", "pet", "homosexual"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    meal = f["meal"]
    source = f["source"]
    suspect = f["suspect_cfg"]
    return [
        f'Write a funny kitchen story for a 3-to-5-year-old that includes the words "boiled" and "homosexual", with comic sound effects and a small mystery to solve.',
        f"Tell a comedy where {child.attrs['name']} hears silly noises while {meal.label} boils, wrongly suspects {suspect.label}, and then solves the mystery by being kind.",
        f"Write a short family story with a gentle mystery, kitchen noises, and a happy ending where the strange sound turns out to be {source.cause}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    meal = f["meal"]
    source = f["source"]
    suspect = f["suspect_cfg"]
    method = f["method"]
    dad1 = f["dad1"]
    dad2 = f["dad2"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.attrs['name']} and {dad1.attrs['name']} and {dad2.attrs['name']} in the kitchen. They are making {meal.label} together and hearing a silly mystery noise."
        ),
        (
            f"What mystery did {child.attrs['name']} want to solve?",
            f"{child.attrs['name']} wanted to know what was making the funny sounds while the {meal.vessel} boiled. The noise made the kitchen feel like a tiny comedy show."
        ),
        (
            f"Who did {child.attrs['name']} suspect first?",
            f"{child.attrs['name']} first suspected {suspect.label}. That guess was wrong, because {suspect.innocent_reason}."
        ),
        (
            f"How did the family solve the mystery?",
            f"{method.qa_text} That careful choice helped them notice the real clue instead of being cross with anyone."
        ),
        (
            "What was really making the sound?",
            f"It was {source.cause}. Once they looked closely, the mystery stopped feeling spooky and started feeling funny."
        ),
        (
            "How did kindness help in the story?",
            f"Kindness stopped the family from blaming {suspect.label} too fast. Because they stayed gentle, they found the true answer and everybody could laugh together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"boiled", "sound", "kindness", "mystery", "homosexual"}
    source = world.facts["source"]
    suspect = world.facts["suspect_cfg"]
    if "steam" in source.tags or "lid" in source.tags:
        tags.add("steam")
    if "pet" in suspect.tags:
        tags.add("pet")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        meal="soup",
        source="lid",
        suspect="pet",
        method="peek",
        child_name="Nico",
        child_gender="boy",
        dad1_name="Papa Ben",
        dad2_name="Dad Luis",
        pet_name="Pickles",
        helper_trait="patient",
    ),
    StoryParams(
        meal="eggs",
        source="egg_tap",
        suspect="dad",
        method="listen",
        child_name="Maya",
        child_gender="girl",
        dad1_name="Papa Joel",
        dad2_name="Dad Amir",
        pet_name="Bean",
        helper_trait="gentle",
    ),
    StoryParams(
        meal="cocoa",
        source="spoon",
        suspect="ladle",
        method="peek",
        child_name="Leo",
        child_gender="boy",
        dad1_name="Papa Ivo",
        dad2_name="Dad Marco",
        pet_name="Pepper",
        helper_trait="calm",
    ),
]


def explain_rejection(meal: Meal, source: Source) -> str:
    return (
        f"(No story: {source.label} is not a sensible sound source for {meal.label}. "
        f"Pick a source that could really rattle, tap, or bump while that meal boils.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = " / ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try a kinder observation method like {better}.)"
    )


ASP_RULES = r"""
compatible(Meal, Source) :- meal(Meal), source(Source), allows(Meal, Source), works_with(Source, Meal).
sensible(Method) :- method(Method), sense(Method, S), sense_min(M), S >= M.
valid(Meal, Source) :- compatible(Meal, Source).

kind_resolution :- chosen_method(M), sensible(M).
outcome(kind_solved) :- valid(_, _), kind_resolution.
outcome(bad_method) :- valid(_, _), not kind_resolution.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for meal_id, meal in MEALS.items():
        lines.append(asp.fact("meal", meal_id))
        for source_id in sorted(meal.safe_source_ids):
            lines.append(asp.fact("allows", meal_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for meal_id in sorted(source.works_with):
            lines.append(asp.fact("works_with", source_id, meal_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_meal", params.meal),
            asp.fact("chosen_source", params.source),
            asp.fact("valid", params.meal, params.source),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "kind_solved" if METHODS[params.method].sense >= SENSE_MIN else "bad_method"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a funny boiling-sound mystery solved with kindness."
    )
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.meal and args.source:
        meal = MEALS[args.meal]
        source = SOURCES[args.source]
        if not source_works(meal, source):
            raise StoryError(explain_rejection(meal, source))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        c
        for c in valid_combos()
        if (args.meal is None or c[0] == args.meal)
        and (args.source is None or c[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    meal_id, source_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    suspect_id = args.suspect or rng.choice(sorted(SUSPECTS))
    child_gender = rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    dad1_name = rng.choice(["Papa Ben", "Papa Ivo", "Papa Joel", "Papa Sami"])
    dad2_name = rng.choice([n for n in ["Dad Luis", "Dad Amir", "Dad Marco", "Dad Rene"] if n != dad1_name.replace("Papa", "Dad")])
    pet_name = rng.choice(PET_NAMES)
    helper_trait = rng.choice(TRAITS)
    return StoryParams(
        meal=meal_id,
        source=source_id,
        suspect=suspect_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        dad1_name=dad1_name,
        dad2_name=dad2_name,
        pet_name=pet_name,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.meal not in MEALS:
        raise StoryError(f"(Unknown meal '{params.meal}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source '{params.source}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect '{params.suspect}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    meal = MEALS[params.meal]
    source = SOURCES[params.source]
    if not source_works(meal, source):
        raise StoryError(explain_rejection(meal, source))

    world = tell(
        meal=meal,
        source=source,
        suspect=SUSPECTS[params.suspect],
        method=METHODS[params.method],
        child_name=params.child_name,
        child_type=params.child_gender,
        dad1_name=params.dad1_name,
        dad2_name=params.dad2_name,
        pet_name=params.pet_name,
        helper_trait=params.helper_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_methods, p_methods = set(asp_sensible_methods()), {m.id for m in sensible_methods()}
    if c_methods == p_methods:
        print(f"OK: sensible methods match ({sorted(c_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_methods)} python={sorted(p_methods)}")

    cases = list(CURATED)
    for s in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        methods = asp_sensible_methods()
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (meal, source) combos:\n")
        for meal, source in combos:
            print(f"  {meal:8} {source}")
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
            header = f"### {p.child_name}: {p.meal} with {p.source} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
