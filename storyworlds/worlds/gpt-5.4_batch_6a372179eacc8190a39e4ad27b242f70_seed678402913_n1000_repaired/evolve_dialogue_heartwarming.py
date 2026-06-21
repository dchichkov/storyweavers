#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py
==========================================================

A small story world about a child, a caterpillar, and the patient kind of help
that lets change happen in its own time. Every story is built from simulated
state: a caterpillar eats, hangs still, becomes a chrysalis, and finally
evolves into a butterfly. The emotional turn is also simulated: eagerness turns
into worry, then trust and wonder.

The reasonableness gate is simple and child-facing:
- a butterfly species must be paired with one of its real host plants;
- the setting must plausibly contain that plant;
- the chosen protection must be breathable and strong enough for the weather;
- low-sense "help" such as a sealed jar is known to the world but refused.

The stories are heartwarming and dialogue-heavy. The child always wants to help
a little too fast; the grown-up redirects that wish into patient care.

Run it
------
    python storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py
    python storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py --asp
    python storyworlds/worlds/gpt-5.4/evolve_dialogue_heartwarming.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    phrase: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "teacher"}
        male = {"boy", "father", "grandfather", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "teacher": "teacher",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Species:
    id: str
    label: str
    butterfly_label: str
    hosts: set[str] = field(default_factory=set)
    child_word: str = "little caterpillar"
    tags: set[str] = field(default_factory=set)


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    label: str
    severity: int
    opening: str
    motion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpMethod:
    id: str
    label: str
    sense: int
    power: int
    breathable: bool = True
    settings: set[str] = field(default_factory=set)
    prep: str = ""
    watch: str = ""
    qa_text: str = ""
    fail_reason: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_form_chrysalis(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if creature is None:
        return []
    if creature.meters["leaf_full"] < THRESHOLD or creature.meters["hanging"] < THRESHOLD:
        return []
    sig = ("stage", "chrysalis")
    if sig in world.fired or creature.meters["stage_chrysalis"] >= THRESHOLD:
        return []
    world.fired.add(sig)
    creature.meters["stage_caterpillar"] = 0.0
    creature.meters["stage_chrysalis"] = 1.0
    creature.memes["stillness"] += 1
    return ["__chrysalis__"]


def _r_evolve_butterfly(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if creature is None:
        return []
    need = float(world.facts.get("weather_severity", 0))
    if creature.meters["stage_chrysalis"] < THRESHOLD:
        return []
    if creature.meters["shelter"] < need:
        return []
    if creature.meters["waited"] < THRESHOLD:
        return []
    sig = ("stage", "butterfly")
    if sig in world.fired or creature.meters["stage_butterfly"] >= THRESHOLD:
        return []
    world.fired.add(sig)
    creature.meters["stage_chrysalis"] = 0.0
    creature.meters["stage_butterfly"] = 1.0
    creature.memes["freedom"] += 1
    for eid in ("child", "grownup"):
        if eid in world.entities:
            world.get(eid).memes["wonder"] += 1
            world.get(eid).memes["relief"] += 1
    return ["__butterfly__"]


CAUSAL_RULES = [
    Rule(name="form_chrysalis", tag="physical", apply=_r_form_chrysalis),
    Rule(name="evolve_butterfly", tag="physical", apply=_r_evolve_butterfly),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the little garden behind the house",
        indoors=False,
        affords={"milkweed", "parsley", "dill", "mallow"},
        tags={"garden"},
    ),
    "balcony": Setting(
        id="balcony",
        place="the sunny balcony with pots along the rail",
        indoors=False,
        affords={"milkweed", "parsley", "dill"},
        tags={"balcony"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the bright classroom by the window",
        indoors=True,
        affords={"parsley", "dill", "mallow"},
        tags={"classroom"},
    ),
}

SPECIES = {
    "monarch": Species(
        id="monarch",
        label="a monarch caterpillar",
        butterfly_label="an orange monarch butterfly",
        hosts={"milkweed"},
        child_word="striped little caterpillar",
        tags={"monarch", "butterfly"},
    ),
    "swallowtail": Species(
        id="swallowtail",
        label="a swallowtail caterpillar",
        butterfly_label="a yellow swallowtail butterfly",
        hosts={"parsley", "dill"},
        child_word="green little caterpillar",
        tags={"swallowtail", "butterfly"},
    ),
    "painted_lady": Species(
        id="painted_lady",
        label="a painted lady caterpillar",
        butterfly_label="a speckled painted lady butterfly",
        hosts={"mallow"},
        child_word="spiky little caterpillar",
        tags={"painted_lady", "butterfly"},
    ),
}

PLANTS = {
    "milkweed": Plant(
        id="milkweed",
        label="milkweed",
        phrase="a tall milkweed plant",
        tags={"milkweed", "plant"},
    ),
    "parsley": Plant(
        id="parsley",
        label="parsley",
        phrase="a parsley plant in a clay pot",
        tags={"parsley", "plant"},
    ),
    "dill": Plant(
        id="dill",
        label="dill",
        phrase="a feathery dill plant",
        tags={"dill", "plant"},
    ),
    "mallow": Plant(
        id="mallow",
        label="mallow",
        phrase="a soft mallow plant",
        tags={"mallow", "plant"},
    ),
}

WEATHERS = {
    "sunny": Weather(
        id="sunny",
        label="sunny",
        severity=0,
        opening="The morning light fell warm and gold.",
        motion="Only a soft breeze touched the leaves.",
        tags={"sun"},
    ),
    "drizzly": Weather(
        id="drizzly",
        label="drizzly",
        severity=1,
        opening="A silver drizzle tapped softly nearby.",
        motion="Tiny drops gathered on the leaves.",
        tags={"rain"},
    ),
    "breezy": Weather(
        id="breezy",
        label="breezy",
        severity=1,
        opening="The day was bright, but the wind kept nudging everything.",
        motion="The stems swayed and nodded in the breeze.",
        tags={"wind"},
    ),
    "stormy": Weather(
        id="stormy",
        label="stormy",
        severity=2,
        opening="Clouds pressed low, and the air felt full of rain.",
        motion="Every gust made the stems tremble.",
        tags={"storm", "rain", "wind"},
    ),
}

HELP_METHODS = {
    "mesh_cover": HelpMethod(
        id="mesh_cover",
        label="a soft mesh cover",
        sense=3,
        power=2,
        breathable=True,
        settings={"garden", "balcony", "classroom"},
        prep="set a soft mesh cover around the plant so air could flow through while the chrysalis stayed safe",
        watch="The cover made a calm little room around the leaves without closing the air out.",
        qa_text="They used a soft mesh cover that let air in while keeping the chrysalis safe.",
        tags={"mesh", "safe_habitat"},
    ),
    "plant_stake": HelpMethod(
        id="plant_stake",
        label="a plant stake and ribbon",
        sense=3,
        power=2,
        breathable=True,
        settings={"garden", "balcony"},
        prep="tied the stem gently to a plant stake with a soft ribbon so it would not whip in the wind",
        watch="The stake held the plant steady, and the little hanging body hardly rocked at all.",
        qa_text="They steadied the plant with a stake and soft ribbon so the chrysalis could hang safely.",
        tags={"stake", "safe_habitat"},
    ),
    "leaf_tent": HelpMethod(
        id="leaf_tent",
        label="a leaf tent",
        sense=2,
        power=1,
        breathable=True,
        settings={"garden", "balcony"},
        prep="clipped a clear leaf tent over the branch to soften the rain and shield the hanging chrysalis",
        watch="The leaf tent kept the hardest drops off while the air still slipped through.",
        qa_text="They clipped on a small leaf tent that blocked the weather without sealing the chrysalis in.",
        tags={"leaf_tent", "safe_habitat"},
    ),
    "screen_box": HelpMethod(
        id="screen_box",
        label="a screened butterfly box",
        sense=3,
        power=2,
        breathable=True,
        settings={"classroom"},
        prep="placed the host plant inside a screened butterfly box by the window so the chrysalis would stay airy and safe",
        watch="The little box felt bright and roomy, and nothing touched the chrysalis except quiet air.",
        qa_text="They placed the plant in a screened butterfly box so the chrysalis stayed airy and protected.",
        tags={"screen_box", "safe_habitat"},
    ),
    "sealed_jar": HelpMethod(
        id="sealed_jar",
        label="a sealed jar",
        sense=1,
        power=0,
        breathable=False,
        settings={"garden", "balcony", "classroom"},
        prep="closed the creature in a jar with a tight lid",
        watch="The tight lid would trap stale air.",
        qa_text="They shut the caterpillar in a sealed jar.",
        fail_reason="A sealed jar shuts out fresh air, so it is not kind or safe for a chrysalis.",
        tags={"jar"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya", "Rose", "Clara"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Noah", "Eli", "Theo", "Jack", "Finn", "Owen"]
TRAITS = ["curious", "gentle", "hopeful", "eager", "careful", "bright"]


def host_match(species_id: str, plant_id: str) -> bool:
    species = SPECIES[species_id]
    return plant_id in species.hosts


def setting_has_plant(setting_id: str, plant_id: str) -> bool:
    setting = SETTINGS[setting_id]
    return plant_id in setting.affords


def help_allowed(help_id: str, setting_id: str) -> bool:
    method = HELP_METHODS[help_id]
    return setting_id in method.settings


def help_is_sensible(help_id: str) -> bool:
    return HELP_METHODS[help_id].sense >= SENSE_MIN and HELP_METHODS[help_id].breathable


def help_strong_enough(help_id: str, weather_id: str) -> bool:
    return HELP_METHODS[help_id].power >= WEATHERS[weather_id].severity


def valid_story_combo(setting_id: str, species_id: str, plant_id: str,
                      weather_id: str, help_id: str) -> bool:
    return (
        setting_has_plant(setting_id, plant_id)
        and host_match(species_id, plant_id)
        and help_allowed(help_id, setting_id)
        and help_is_sensible(help_id)
        and help_strong_enough(help_id, weather_id)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for species_id in SPECIES:
            for plant_id in PLANTS:
                for weather_id in WEATHERS:
                    for help_id in HELP_METHODS:
                        if valid_story_combo(setting_id, species_id, plant_id, weather_id, help_id):
                            out.append((setting_id, species_id, plant_id, weather_id, help_id))
    return out


def predict_evolution(world: World, help_method: HelpMethod, weather: Weather) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    creature.meters["shelter"] += help_method.power
    creature.meters["waited"] += 1
    sim.facts["weather_severity"] = weather.severity
    propagate(sim, narrate=False)
    return {
        "becomes_chrysalis": creature.meters["stage_chrysalis"] >= THRESHOLD
        or creature.meters["stage_butterfly"] >= THRESHOLD,
        "becomes_butterfly": creature.meters["stage_butterfly"] >= THRESHOLD,
    }


def opening_detail(setting: Setting, weather: Weather) -> str:
    place = setting.place
    if setting.indoors:
        return f"{weather.opening} On the sill beside {place}, leaves leaned toward the glass."
    return f"{weather.opening} In {place}, the stems looked alive with small motions."


def introduce(world: World, child: Entity, grownup: Entity, plant: Plant, setting: Setting) -> None:
    world.say(
        f"{child.id} loved checking on the pots and leaves with {child.pronoun('possessive')} "
        f"{grownup.label_word}. {opening_detail(setting, world.facts['weather'])}"
    )
    world.say(
        f"That day they stopped beside {plant.phrase}, and {child.id} bent close at once."
    )


def discover(world: World, child: Entity, species: Species) -> None:
    creature = world.get("creature")
    child.memes["wonder"] += 1
    world.say(
        f'"Look!" {child.id} whispered. "There is {species.label} on the leaf."'
    )
    world.say(
        f"The {species.child_word} nibbled and rested and nibbled again, as if it had all the time in the world."
    )
    creature.meters["leaf_full"] += 1
    creature.meters["hanging"] += 1
    propagate(world, narrate=False)


def ask_about_change(world: World, child: Entity) -> None:
    child.memes["eagerness"] += 1
    world.say(
        f'"Will it evolve soon?" {child.id} asked. "I want to see every single part."'
    )


def explain_waiting(world: World, grownup: Entity, child: Entity, species: Species) -> None:
    grownup.memes["care"] += 1
    world.say(
        f'"We can watch carefully," {grownup.label_word} said, smiling, '
        f'"but some kinds of growing happen quietly. {species.label.capitalize()} needs calm time as much as it needs leaves."'
    )


def weather_turn(world: World, child: Entity, weather: Weather) -> None:
    child.memes["worry"] += 1
    world.say(weather.motion)
    if weather.severity >= 1:
        world.say(
            f'{child.id} looked up. "Do you think the little one will be all right in this {weather.label} weather?"'
        )
    else:
        world.say(
            f'"It looks so still," {child.id} said softly. "It feels like the whole leaf is holding its breath."'
        )


def rushing_idea(world: World, child: Entity, setting: Setting) -> None:
    child.memes["impatience"] += 1
    if setting.indoors:
        world.say(
            f'"Maybe I should tap the box when it hangs still," {child.id} said. "Maybe that would help it hurry."'
        )
    else:
        world.say(
            f'"Maybe I should bring it inside in my hands," {child.id} said. "Maybe that would help it hurry."'
        )


def guide_gently(world: World, grownup: Entity, child: Entity, help_method: HelpMethod,
                 weather: Weather) -> None:
    pred = predict_evolution(world, help_method, weather)
    world.facts["predicted_butterfly"] = pred["becomes_butterfly"]
    child.memes["trust"] += 1
    world.say(
        f'"The kindest help is not always fast help," {grownup.label_word} answered. '
        f'"If we keep it airy and safe, it can do its own brave work."'
    )
    world.say(
        f'Together they {help_method.prep}.'
    )
    world.say(help_method.watch)


def wait_for_change(world: World, child: Entity, grownup: Entity, species: Species) -> None:
    creature = world.get("creature")
    creature.meters["waited"] += 1
    child.memes["patience"] += 1
    grownup.memes["patience"] += 1
    world.say(
        f"By afternoon, the little body had gone still. By the next check, it had tucked itself into a chrysalis."
    )
    world.say(
        f'"It is not gone," {grownup.label_word} said when {child.id} reached for {grownup.pronoun("possessive")} hand. '
        f'"It is changing. This is how {species.label} gets ready to evolve."'
    )
    propagate(world, narrate=False)


def emerge(world: World, child: Entity, grownup: Entity, species: Species) -> None:
    creature = world.get("creature")
    world.facts["weather_severity"] = world.facts["weather"].severity
    propagate(world, narrate=False)
    if creature.meters["stage_butterfly"] < THRESHOLD:
        raise StoryError("(Internal story error: the butterfly did not emerge.)")
    world.say(
        f"A little later, the chrysalis opened with a neat, quiet split."
    )
    world.say(
        f'{child.id} gasped. "{species.butterfly_label.capitalize()}!"'
    )
    world.say(
        f'"Yes," {grownup.label_word} whispered. "It had to wait, and so did we."'
    )


def release(world: World, child: Entity, grownup: Entity, species: Species, setting: Setting) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    child.memes["wonder"] += 1
    grownup.memes["joy"] += 1
    if setting.indoors:
        place = "the open window"
    else:
        place = "the nearest bright flower"
    world.say(
        f"They watched until the new wings opened wide and steady. Then the butterfly lifted from {place} and floated into the day."
    )
    world.say(
        f'"It really did evolve," {child.id} said, laughing a little.'
    )
    world.say(
        f'"And you helped by being gentle," {grownup.label_word} said. {child.id} leaned close, warm with pride, and waved until the butterfly was only a bright flutter over the leaves.'
    )


def tell(setting: Setting, species: Species, plant: Plant, weather: Weather, help_method: HelpMethod,
         child_name: str = "Lily", child_type: str = "girl",
         grownup_type: str = "grandmother", trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        attrs={"trait": trait},
        tags={trait},
    ))
    grownup = world.add(Entity(
        id="Helper",
        kind="character",
        type=grownup_type,
        label="the grown-up",
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type="caterpillar",
        label=species.label,
        phrase=species.label,
        tags=set(species.tags),
    ))
    host = world.add(Entity(
        id="plant",
        kind="thing",
        type="plant",
        label=plant.label,
        phrase=plant.phrase,
        tags=set(plant.tags),
    ))
    creature.attrs["host"] = plant.id
    creature.meters["stage_caterpillar"] = 1.0
    world.facts["weather"] = weather

    introduce(world, child, grownup, plant, setting)
    discover(world, child, species)
    ask_about_change(world, child)
    explain_waiting(world, grownup, child, species)

    world.para()
    weather_turn(world, child, weather)
    rushing_idea(world, child, setting)
    guide_gently(world, grownup, child, help_method, weather)

    world.para()
    wait_for_change(world, child, grownup, species)
    creature.meters["shelter"] += help_method.power
    world.say(
        f"Morning after morning, {child.id} looked first with wide eyes and then with patient ones."
    )
    emerge(world, child, grownup, species)
    release(world, child, grownup, species, setting)

    world.facts.update(
        child=child,
        grownup=grownup,
        species=species,
        plant=plant,
        setting=setting,
        help_method=help_method,
        evolved=creature.meters["stage_butterfly"] >= THRESHOLD,
        creature=creature,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    species: str
    plant: str
    weather: str
    help_method: str
    child_name: str
    child_gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="garden",
        species="monarch",
        plant="milkweed",
        weather="stormy",
        help_method="mesh_cover",
        child_name="Lily",
        child_gender="girl",
        grownup="grandmother",
        trait="curious",
    ),
    StoryParams(
        setting="balcony",
        species="swallowtail",
        plant="parsley",
        weather="breezy",
        help_method="plant_stake",
        child_name="Leo",
        child_gender="boy",
        grownup="grandfather",
        trait="gentle",
    ),
    StoryParams(
        setting="garden",
        species="swallowtail",
        plant="dill",
        weather="drizzly",
        help_method="leaf_tent",
        child_name="Mia",
        child_gender="girl",
        grownup="mother",
        trait="hopeful",
    ),
    StoryParams(
        setting="classroom",
        species="painted_lady",
        plant="mallow",
        weather="sunny",
        help_method="screen_box",
        child_name="Ben",
        child_gender="boy",
        grownup="teacher",
        trait="bright",
    ),
    StoryParams(
        setting="classroom",
        species="swallowtail",
        plant="dill",
        weather="drizzly",
        help_method="screen_box",
        child_name="Ava",
        child_gender="girl",
        grownup="teacher",
        trait="careful",
    ),
]


KNOWLEDGE = {
    "butterfly": [
        (
            "What does it mean when a caterpillar evolves into a butterfly?",
            "It means the caterpillar changes its body over time. First it makes a chrysalis, and later it comes out as a butterfly.",
        )
    ],
    "chrysalis": [
        (
            "What is a chrysalis?",
            "A chrysalis is the hard case around a changing caterpillar. Inside it, the caterpillar is growing into a butterfly.",
        )
    ],
    "milkweed": [
        (
            "Why do monarch caterpillars need milkweed?",
            "Monarch caterpillars eat milkweed leaves. It is the plant they are made to grow on.",
        )
    ],
    "parsley": [
        (
            "Can some caterpillars live on parsley?",
            "Yes. Some kinds, like swallowtails, can eat parsley leaves while they are growing.",
        )
    ],
    "dill": [
        (
            "Why might a caterpillar be on dill?",
            "Some caterpillars use dill as a food plant. The feathery leaves give them a place to eat and rest.",
        )
    ],
    "mallow": [
        (
            "What is mallow?",
            "Mallow is a leafy plant. Some caterpillars can use it as a host plant while they grow.",
        )
    ],
    "safe_habitat": [
        (
            "Why does a chrysalis need air?",
            "A living creature still needs fresh air while it is changing. A safe cover should protect it without sealing it up.",
        )
    ],
    "mesh": [
        (
            "What does a mesh cover do?",
            "A mesh cover lets air pass through, but it helps keep the creature safe from bumps and rough weather.",
        )
    ],
    "stake": [
        (
            "Why would someone use a plant stake?",
            "A plant stake helps hold a stem steady. That can keep a hanging chrysalis from swinging too hard in the wind.",
        )
    ],
    "leaf_tent": [
        (
            "What is a leaf tent for?",
            "A leaf tent gives a little shelter from drops and splashes while still leaving the plant open to the air.",
        )
    ],
    "screen_box": [
        (
            "What is a screened butterfly box?",
            "It is a box with airy sides that lets people watch safely. The screen protects the butterfly while fresh air still gets in.",
        )
    ],
    "rain": [
        (
            "Why can rain be hard on tiny insects?",
            "Raindrops can feel very heavy to a tiny creature. Too much rough weather can shake or soak the place where it is hanging.",
        )
    ],
    "wind": [
        (
            "Why can wind be a problem for a chrysalis?",
            "A strong wind can whip a stem back and forth. That can make it hard for the chrysalis to hang safely.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "butterfly",
    "chrysalis",
    "milkweed",
    "parsley",
    "dill",
    "mallow",
    "safe_habitat",
    "mesh",
    "stake",
    "leaf_tent",
    "screen_box",
    "rain",
    "wind",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    species = world.facts["species"]
    plant = world.facts["plant"]
    grownup = world.facts["grownup"]
    weather = world.facts["weather"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "evolve" and uses dialogue.',
        f"Tell a gentle story where {child.id} finds {species.label} on {plant.phrase}, worries during {weather.label} weather, and learns from {grownup.label_word} that patient help can be kind.",
        f"Write a small dialogue-rich story about a child waiting for a caterpillar to evolve into a butterfly instead of trying to hurry the change.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    grownup = world.facts["grownup"]
    species = world.facts["species"]
    plant = world.facts["plant"]
    weather = world.facts["weather"]
    help_method = world.facts["help_method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child watching {species.label}, and {child.pronoun('possessive')} {grownup.label_word}, who helps {child.pronoun('object')} care for it.",
        ),
        (
            f"Where did {child.id} find the caterpillar?",
            f"{child.id} found it on {plant.phrase}. That plant mattered because it was the right place for the caterpillar to live and eat.",
        ),
        (
            f"Why was {child.id} worried?",
            f"{child.id} was worried because the weather was {weather.label} and the tiny creature looked delicate. {child.pronoun().capitalize()} wanted to help, but the grown-up knew help had to be gentle and safe.",
        ),
        (
            f"What did {child.id} first want to do?",
            f"{child.id} wanted to hurry the change by moving or tapping near the creature. That idea came from love, but it could have disturbed the quiet time the chrysalis needed.",
        ),
        (
            f"How did the grown-up help?",
            f"{help_method.qa_text} The grown-up chose protection that still left fresh air around the chrysalis, because safe waiting was better than rushing.",
        ),
        (
            "How did the story end?",
            f"The chrysalis opened and the caterpillar had evolved into {species.butterfly_label}. At the end, {child.id} felt proud because {child.pronoun()} had helped by being patient and gentle.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"butterfly", "chrysalis", "safe_habitat"}
    tags |= set(world.facts["species"].tags)
    tags |= set(world.facts["plant"].tags)
    tags |= set(world.facts["help_method"].tags)
    tags |= set(world.facts["weather"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_host(species_id: str, plant_id: str) -> str:
    species = SPECIES[species_id]
    plant = PLANTS[plant_id]
    hosts = ", ".join(sorted(species.hosts))
    return (
        f"(No story: {species.label} does not belong on {plant.label}. "
        f"Try one of its host plants: {hosts}.)"
    )


def explain_setting(setting_id: str, plant_id: str) -> str:
    setting = SETTINGS[setting_id]
    plant = PLANTS[plant_id]
    plants = ", ".join(sorted(setting.affords))
    return (
        f"(No story: {plant.label} is not part of {setting.place} in this world. "
        f"Try one of these plants there: {plants}.)"
    )


def explain_help(help_id: str) -> str:
    method = HELP_METHODS[help_id]
    return (
        f"(Refusing help method '{help_id}': {method.fail_reason or 'it is not a sensible choice here.'})"
    )


def explain_help_setting(help_id: str, setting_id: str) -> str:
    method = HELP_METHODS[help_id]
    setting = SETTINGS[setting_id]
    allowed = ", ".join(sorted(method.settings))
    return (
        f"(No story: {method.label} does not fit {setting.place}. "
        f"Try it in one of these settings: {allowed}.)"
    )


def explain_strength(help_id: str, weather_id: str) -> str:
    method = HELP_METHODS[help_id]
    weather = WEATHERS[weather_id]
    return (
        f"(No story: {method.label} is too weak for {weather.label} weather. "
        f"Choose stronger protection.)"
    )


ASP_RULES = r"""
host_match(S, P) :- host_plant(S, P).
setting_has_plant(St, P) :- affords(St, P).
help_ok(H) :- help(H), sense(H, S), sense_min(M), S >= M, breathable(H).
help_allowed(H, St) :- help_setting(H, St).
help_strong(H, W) :- help(H), weather(W), power(H, P), severity(W, Need), P >= Need.

valid(St, S, P, W, H) :-
    setting(St), species(S), plant(P), weather(W), help(H),
    setting_has_plant(St, P),
    host_match(S, P),
    help_allowed(H, St),
    help_ok(H),
    help_strong(H, W).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for plant_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, plant_id))
    for sid, species in SPECIES.items():
        lines.append(asp.fact("species", sid))
        for plant_id in sorted(species.hosts):
            lines.append(asp.fact("host_plant", sid, plant_id))
    for pid in PLANTS:
        lines.append(asp.fact("plant", pid))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("severity", wid, weather.severity))
    for hid, method in HELP_METHODS.items():
        lines.append(asp.fact("help", hid))
        lines.append(asp.fact("sense", hid, method.sense))
        lines.append(asp.fact("power", hid, method.power))
        if method.breathable:
            lines.append(asp.fact("breathable", hid))
        for setting_id in sorted(method.settings):
            lines.append(asp.fact("help_setting", hid, setting_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if "evolve" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story did not include 'evolve'.)")
        print("OK: random resolve_params() story generation worked.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child learns patient, gentle help while a caterpillar evolves."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--help-method", dest="help_method", choices=HELP_METHODS)
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather", "teacher"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.species and args.plant and not host_match(args.species, args.plant):
        raise StoryError(explain_host(args.species, args.plant))
    if args.setting and args.plant and not setting_has_plant(args.setting, args.plant):
        raise StoryError(explain_setting(args.setting, args.plant))
    if args.help_method and not help_is_sensible(args.help_method):
        raise StoryError(explain_help(args.help_method))
    if args.help_method and args.setting and not help_allowed(args.help_method, args.setting):
        raise StoryError(explain_help_setting(args.help_method, args.setting))
    if args.help_method and args.weather and not help_strong_enough(args.help_method, args.weather):
        raise StoryError(explain_strength(args.help_method, args.weather))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.species is None or combo[1] == args.species)
        and (args.plant is None or combo[2] == args.plant)
        and (args.weather is None or combo[3] == args.weather)
        and (args.help_method is None or combo[4] == args.help_method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, species_id, plant_id, weather_id, help_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather", "teacher"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        species=species_id,
        plant=plant_id,
        weather=weather_id,
        help_method=help_id,
        child_name=child_name,
        child_gender=gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.species not in SPECIES:
        raise StoryError(f"(Invalid species: {params.species})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Invalid plant: {params.plant})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Invalid weather: {params.weather})")
    if params.help_method not in HELP_METHODS:
        raise StoryError(f"(Invalid help method: {params.help_method})")
    if not valid_story_combo(params.setting, params.species, params.plant, params.weather, params.help_method):
        if not host_match(params.species, params.plant):
            raise StoryError(explain_host(params.species, params.plant))
        if not setting_has_plant(params.setting, params.plant):
            raise StoryError(explain_setting(params.setting, params.plant))
        if not help_is_sensible(params.help_method):
            raise StoryError(explain_help(params.help_method))
        if not help_allowed(params.help_method, params.setting):
            raise StoryError(explain_help_setting(params.help_method, params.setting))
        raise StoryError(explain_strength(params.help_method, params.weather))

    world = tell(
        setting=SETTINGS[params.setting],
        species=SPECIES[params.species],
        plant=PLANTS[params.plant],
        weather=WEATHERS[params.weather],
        help_method=HELP_METHODS[params.help_method],
        child_name=params.child_name,
        child_type=params.child_gender,
        grownup_type=params.grownup,
        trait=params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, species, plant, weather, help) combos:\n")
        for setting_id, species_id, plant_id, weather_id, help_id in combos:
            print(f"  {setting_id:10} {species_id:13} {plant_id:8} {weather_id:8} {help_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.species} on {p.plant} at {p.setting} "
                f"({p.weather}, {p.help_method})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
