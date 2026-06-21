#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/incapacitate_misunderstanding_cautionary_suspense_folk_tale.py
=========================================================================================

A standalone storyworld for a small folk-tale domain built around a dangerous
misunderstanding: a child mistakes a sleep-making herb for a harmless one and
feeds it to the family animal on the way to a narrow crossing. The wrong herb
can incapacitate the animal, turning an ordinary errand into a tense lesson.

This world keeps the domain small and concrete:

* a child and an elder travel with an animal helper
* the child misunderstands one herb for another
* the helper animal grows weak and sleepy
* an elder responds in a more-or-less sensible way
* the ending is either a safe recovery or a sad loss, with everyone still safe

The prose aims for a simple child-facing folk-tale tone, while the world model
tracks physical meters and emotional memes and uses a small causal system.

Run it
------
    python storyworlds/worlds/gpt-5.4/incapacitate_misunderstanding_cautionary_suspense_folk_tale.py
    python storyworlds/worlds/gpt-5.4/incapacitate_misunderstanding_cautionary_suspense_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/incapacitate_misunderstanding_cautionary_suspense_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/incapacitate_misunderstanding_cautionary_suspense_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/incapacitate_misunderstanding_cautionary_suspense_folk_tale.py --trace --seed 17
    python storyworlds/worlds/gpt-5.4/incapacitate_misunderstanding_cautionary_suspense_folk_tale.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    route: str
    hazard: str
    crossing: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalKind:
    id: str
    label: str
    phrase: str
    burden: str
    gait: str
    recovery_pose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HerbMistake:
    id: str
    safe_name: str
    dangerous_name: str
    clue: str
    safe_use: str
    danger_text: str
    strength: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    animal: str
    confusion: str
    response: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    delay: int = 0
    seed: Optional[int] = None


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


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    child = world.entities.get("child")
    route = world.entities.get("route")
    if animal is None or child is None or route is None:
        return out
    if animal.meters["drugged"] < THRESHOLD:
        return out
    sig = ("sleep", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["stagger"] += 1
    animal.meters["strength_lost"] += 1
    route.meters["danger"] += 1
    child.memes["fear"] += 1
    out.append("__stagger__")
    return out


def _r_bridge(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    route = world.entities.get("route")
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    bundle = world.entities.get("bundle")
    if animal is None or route is None or child is None or elder is None or bundle is None:
        return out
    if animal.meters["stagger"] < THRESHOLD:
        return out
    if route.meters["at_crossing"] < THRESHOLD:
        return out
    sig = ("bridge", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    route.meters["danger"] += 1
    child.memes["fear"] += 1
    elder.memes["alarm"] += 1
    bundle.meters["risk"] += 1
    out.append("__peril__")
    return out


CAUSAL_RULES = [
    Rule(name="sleep", tag="physical", apply=_r_sleep),
    Rule(name="bridge", tag="physical", apply=_r_bridge),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for item in produced:
            world.say(item)
    return produced


SETTINGS = {
    "willow_bridge": Setting(
        id="willow_bridge",
        place="the Willow Valley",
        route="the mill road by the reeds",
        hazard="the river under the old willow bridge",
        crossing="the old willow bridge",
        ending_image="the bridge looked small again under the evening swallows",
        tags={"bridge", "river", "village"},
    ),
    "stone_ford": Setting(
        id="stone_ford",
        place="the Stone Ford village",
        route="the cart path beside the cold stream",
        hazard="the water that rushed between the ford stones",
        crossing="the stepping-stone ford",
        ending_image="the stones shone quietly while the first stars came out",
        tags={"ford", "water", "village"},
    ),
    "pine_pass": Setting(
        id="pine_pass",
        place="the Pine Pass hamlet",
        route="the high goat path under the dark pines",
        hazard="the steep ravine below the rope bridge",
        crossing="the rope bridge",
        ending_image="the pines stopped whispering, and the bridge hung still at last",
        tags={"bridge", "ravine", "mountain"},
    ),
}

ANIMALS = {
    "donkey": AnimalKind(
        id="donkey",
        label="donkey",
        phrase="a gray donkey with wise eyes",
        burden="two sacks of flour",
        gait="picked careful steps over every root and stone",
        recovery_pose="stood again with its nose deep in a bucket of cool water",
        tags={"donkey", "load"},
    ),
    "pony": AnimalKind(
        id="pony",
        label="pony",
        phrase="a little brown pony with a braided mane",
        burden="a basket of loaves and apples",
        gait="walked with a soft clop-clop that echoed on the path",
        recovery_pose="lifted its head and stamped once on the dry ground",
        tags={"pony", "load"},
    ),
    "goat": AnimalKind(
        id="goat",
        label="goat",
        phrase="a sturdy white goat with a bell at its neck",
        burden="a bundle of herbs and a crock of milk",
        gait="trotted lightly, as if the hill belonged to it",
        recovery_pose="shook its bell and nibbled a safe leaf at last",
        tags={"goat", "load"},
    ),
}

CONFUSIONS = {
    "bluebell_moonsleep": HerbMistake(
        id="bluebell_moonsleep",
        safe_name="bluebell mint",
        dangerous_name="moonsleep weed",
        clue="its leaves carried a dusty silver on their backs",
        safe_use="freshen an animal after a long road",
        danger_text="can incapacitate even a strong animal until its legs feel like rope",
        strength=2,
        tags={"herb", "misunderstanding", "sleep"},
    ),
    "fennel_dreamfern": HerbMistake(
        id="fennel_dreamfern",
        safe_name="meadow fennel",
        dangerous_name="dreamfern",
        clue="it smelled sweet at first and bitter after",
        safe_use="settle a beast's stomach",
        danger_text="can incapacitate a beast so quickly that its knees fold under it",
        strength=1,
        tags={"herb", "misunderstanding", "sleep"},
    ),
    "thyme_drowseleaf": HerbMistake(
        id="thyme_drowseleaf",
        safe_name="hill thyme",
        dangerous_name="drowseleaf",
        clue="its stems bent too softly and oozed pale milk when broken",
        safe_use="perk up a tired traveler",
        danger_text="can incapacitate a pack animal and leave it too weak to cross safely",
        strength=2,
        tags={"herb", "misunderstanding", "sleep"},
    ),
}

RESPONSES = {
    "rest_water": Response(
        id="rest_water",
        sense=3,
        power=3,
        text="slipped the straps from the load, led the animal away from the edge, and let it drink cold water while the herb's spell wore thin",
        fail="slipped the straps from the load and fetched water, but the animal's legs still sagged and the day kept slipping away",
        qa_text="loosened the load, moved the animal away from danger, and let it drink cool water until it steadied",
        tags={"water", "rest", "help"},
    ),
    "wake_broth": Response(
        id="wake_broth",
        sense=3,
        power=2,
        text="mixed a sharp wake-broth of onion, salt, and water, then waited beside the animal until its blinking eyes grew clear again",
        fail="mixed a sharp wake-broth, but the herb had gone too deep into the animal's body for a quick fix",
        qa_text="made a sharp broth and waited until the animal's eyes cleared",
        tags={"water", "rest", "help"},
    ),
    "drop_load": Response(
        id="drop_load",
        sense=2,
        power=1,
        text="cut the cords, rolled the bundle aside, and kept the animal still until the worst of the weakness passed",
        fail="cut the cords and pulled the bundle clear, but the animal slumped before the crossing could be made",
        qa_text="cut the cords and took the load off so the animal could rest",
        tags={"rest", "help"},
    ),
    "shout_only": Response(
        id="shout_only",
        sense=1,
        power=0,
        text="only shouted and waved frightened hands",
        fail="only shouted and waved frightened hands while the danger kept growing",
        qa_text="only shouted instead of helping wisely",
        tags={"poor_help"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tala", "Nora", "Sela", "Asha", "Bria", "Ivy"]
BOY_NAMES = ["Tobin", "Eli", "Rian", "Milo", "Bram", "Oren", "Luca", "Ned"]
TRAITS = ["careful", "eager", "curious", "thoughtful", "quick", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for animal_id in ANIMALS:
            for confusion_id in CONFUSIONS:
                combos.append((setting_id, animal_id, confusion_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(params: StoryParams) -> int:
    return CONFUSIONS[params.confusion].strength + params.delay


def outcome_of(params: StoryParams) -> str:
    return "contained" if RESPONSES[params.response].power >= severity_of(params) else "lost"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_danger(world: World, confusion: HerbMistake) -> dict:
    sim = world.copy()
    animal = sim.get("animal")
    route = sim.get("route")
    animal.meters["drugged"] += 1
    route.meters["at_crossing"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": route.meters["danger"],
        "stagger": animal.meters["stagger"] >= THRESHOLD,
        "risk": sim.get("bundle").meters["risk"] >= THRESHOLD,
        "warning": confusion.danger_text,
    }


def introduce(world: World, child: Entity, elder: Entity, animal: Entity,
              setting: Setting, animal_cfg: AnimalKind) -> None:
    child.memes["duty"] += 1
    world.say(
        f"In {setting.place}, {child.id} lived with {child.pronoun('possessive')} "
        f"{elder.label_word}, who taught that every path has two faces: the one it shows at sunrise, "
        f"and the one it shows when trouble wakes."
    )
    world.say(
        f"That morning they set out along {setting.route} with {animal_cfg.phrase}. "
        f"The animal carried {animal_cfg.burden} and {animal_cfg.gait}."
    )


def errand(world: World, child: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"They needed to reach {setting.crossing} before the light grew thin, "
        f"for the village on the far side was waiting."
    )
    world.say(
        f'"Keep your eyes on the path and your questions on your tongue," '
        f'{elder.label_word} said. "{setting.hazard.capitalize()} is no friend to hurry."'
    )


def spot_herb(world: World, child: Entity, confusion: HerbMistake) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Near a bend in the road, {child.id} saw a patch of green and smiled. "
        f"{child.pronoun().capitalize()} thought it was {confusion.safe_name}, the herb elders used to "
        f"{confusion.safe_use}."
    )
    world.say(
        f"But it was really {confusion.dangerous_name}, and {confusion.clue}."
    )


def misunderstanding(world: World, child: Entity, animal: Entity,
                      confusion: HerbMistake) -> None:
    child.memes["confidence"] += 1
    world.say(
        f"Wanting to be helpful, {child.id} picked a little handful and held it out to the {animal.label}. "
        f"The animal chewed, and for a moment nothing seemed wrong at all."
    )


def warning_beat(world: World, elder: Entity, confusion: HerbMistake) -> None:
    pred = predict_danger(world, confusion)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"Then {elder.label_word} turned, saw the torn stems, and went pale. "
        f'"Child," {elder.pronoun()} said, "that is {confusion.dangerous_name}. It {confusion.danger_text}."'
    )


def approach_crossing(world: World, setting: Setting) -> None:
    route = world.get("route")
    route.meters["at_crossing"] += 1
    world.say(
        f"Just as {setting.crossing} came into view, the air seemed to hold its breath."
    )


def drug_effect(world: World, animal: Entity, child: Entity, confusion: HerbMistake) -> None:
    animal.meters["drugged"] += 1
    propagate(world, narrate=False)
    animal.memes["distress"] += 1
    child.memes["guilt"] += 1
    world.say(
        f"The {animal.label}'s ears drooped. Its knees trembled. One step after another grew slower, "
        f"as if sleep had been poured into its bones."
    )
    world.say(
        f"{child.id}'s heart thudded. {child.pronoun().capitalize()} understood then that a kind wish can still carry a wrong hand."
    )


def suspense(world: World, setting: Setting, animal: Entity) -> None:
    route = world.get("route")
    propagate(world, narrate=False)
    if route.meters["danger"] >= THRESHOLD:
        world.say(
            f"The path narrowed beside {setting.hazard}, and the {animal.label} swayed toward the crossing. "
            f"For one long breath, it looked as if one more weak step might undo the whole journey."
        )


def rescue(world: World, elder: Entity, child: Entity, animal: Entity,
           response: Response, animal_cfg: AnimalKind) -> None:
    animal.meters["drugged"] = 0.0
    animal.meters["stagger"] = 0.0
    world.get("route").meters["danger"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    elder.memes["care"] += 1
    world.say(
        f"{elder.label_word.capitalize()} did not waste even a blink. {elder.pronoun().capitalize()} {response.text}."
    )
    world.say(
        f"Slowly the danger unwound. At last the {animal.label} {animal_cfg.recovery_pose}, and the road no longer seemed to tilt beneath them."
    )


def lesson(world: World, elder: Entity, child: Entity, confusion: HerbMistake) -> None:
    world.say(
        f'"Remember this," {elder.label_word} said softly. "In the wild, a leaf is not what it seems because we hope it is. '
        f'Ask before you pluck, and look before you trust."'
    )
    world.say(
        f"{child.id} nodded and repeated the name {confusion.dangerous_name} until {child.pronoun()} knew it would not slip from memory again."
    )


def changed_end(world: World, child: Entity, elder: Entity, setting: Setting,
                confusion: HerbMistake) -> None:
    world.say(
        f"When they finally crossed, {child.id} kept {child.pronoun('possessive')} hands folded unless {elder.label_word} pointed the way first."
    )
    world.say(
        f"From that day on, {child.pronoun()} carried a little herb cloth stitched with safe names, "
        f"and {setting.ending_image}."
    )


def fail_rescue(world: World, elder: Entity, response: Response) -> None:
    bundle = world.get("bundle")
    route = world.get("route")
    bundle.meters["lost"] += 1
    route.meters["danger"] += 1
    world.say(
        f"{elder.label_word.capitalize()} {response.fail}."
    )
    world.say(
        "The animal sank to its knees before the crossing was safely done, and the load slid away with a hard, unhappy spill."
    )


def loss_end(world: World, child: Entity, elder: Entity, setting: Setting,
             animal: Entity, confusion: HerbMistake) -> None:
    child.memes["lesson"] += 1
    child.memes["sadness"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"{elder.label_word.capitalize()} pulled {child.id} back from the edge and soothed the {animal.label} until the danger to bodies had passed, "
        f"but the day's goods were lost to the water and mud below."
    )
    world.say(
        f"That evening, no one in {setting.place} laughed over the tale. They spoke of how a mistake born from haste can wound a whole day's work."
    )
    world.say(
        f"After that, {child.id} never touched a roadside herb without asking its true name first, "
        f"and the sound of {setting.crossing} stayed in {child.pronoun('possessive')} mind whenever a guess tried to dress itself up as knowledge."
    )


def tell(setting: Setting, animal_cfg: AnimalKind, confusion: HerbMistake, response: Response,
         child_name: str = "Mira", child_gender: str = "girl", elder_type: str = "grandmother",
         child_trait: str = "curious", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[child_trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label=elder_type,
        role="elder",
    ))
    animal = world.add(Entity(
        id="animal",
        kind="thing",
        type=animal_cfg.id,
        label=animal_cfg.label,
        phrase=animal_cfg.phrase,
        role="helper",
        tags=set(animal_cfg.tags),
    ))
    route = world.add(Entity(
        id="route",
        kind="thing",
        type="route",
        label=setting.crossing,
        role="route",
        tags=set(setting.tags),
    ))
    bundle = world.add(Entity(
        id="bundle",
        kind="thing",
        type="bundle",
        label="load",
        phrase=animal_cfg.burden,
        role="bundle",
    ))

    introduce(world, child, elder, animal, setting, animal_cfg)
    errand(world, child, elder, setting)

    world.para()
    spot_herb(world, child, confusion)
    misunderstanding(world, child, animal, confusion)
    warning_beat(world, elder, confusion)

    world.para()
    approach_crossing(world, setting)
    drug_effect(world, animal, child, confusion)
    suspense(world, setting, animal)

    for _ in range(delay):
        world.get("route").meters["danger"] += 1

    world.para()
    if response.power >= confusion.strength + delay:
        rescue(world, elder, child, animal, response, animal_cfg)
        lesson(world, elder, child, confusion)
        world.para()
        changed_end(world, child, elder, setting, confusion)
        outcome = "contained"
    else:
        fail_rescue(world, elder, response)
        loss_end(world, child, elder, setting, animal, confusion)
        outcome = "lost"

    world.facts.update(
        child=child,
        elder=elder,
        animal=animal,
        route=route,
        bundle=bundle,
        setting=setting,
        animal_cfg=animal_cfg,
        confusion=confusion,
        response=response,
        delay=delay,
        severity=confusion.strength + delay,
        outcome=outcome,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    confusion = f["confusion"]
    animal = f["animal"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            'Write a short folk tale for a young child that uses the word "incapacitate" and centers on a dangerous misunderstanding about a plant.',
            f"Tell a cautionary folk tale where {child.id} mistakes {confusion.dangerous_name} for {confusion.safe_name}, feeds it to a {animal.label}, and the journey near {setting.crossing} turns tense and sad.",
            f"Write a suspenseful village tale where {elder.label_word} explains that the wrong herb can incapacitate an animal, and the child learns too late why guessing in the wild is dangerous.",
        ]
    return [
        'Write a short folk tale for a young child that uses the word "incapacitate" and centers on a dangerous misunderstanding about a plant.',
        f"Tell a cautionary folk tale where {child.id} mistakes {confusion.dangerous_name} for {confusion.safe_name}, and {elder.label_word} must act quickly before the {animal.label} reaches {setting.crossing}.",
        f"Write a suspenseful but gentle story in a village setting where a child learns that the wrong herb can incapacitate an animal, and the ending shows wiser habits afterward.",
    ]


KNOWLEDGE = {
    "herb": [
        (
            "Why should children ask before picking wild plants?",
            "Because many wild plants look alike, and some are safe while others can make people or animals sick. Asking a grown-up helps you learn the true name before anyone gets hurt."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding is when someone thinks something means one thing, but it really means another. It can cause trouble when people act on the wrong idea."
        )
    ],
    "sleep": [
        (
            "What does incapacitate mean?",
            "To incapacitate means to make someone or something unable to act normally for a while. In a story like this, it can make an animal too weak or sleepy to walk safely."
        )
    ],
    "bridge": [
        (
            "Why is a narrow bridge dangerous for a weak animal?",
            "A weak animal can stumble or stop when the path is tight. That is dangerous because there is little room to turn or rest safely."
        )
    ],
    "river": [
        (
            "Why do people move away from an edge in an emergency?",
            "Because edges near water or steep drops leave less room to help safely. Moving back first gives people space to think and work."
        )
    ],
    "water": [
        (
            "Why might cool water help a tired animal rest?",
            "Cool water can comfort a hot, tired animal and help it settle. It is not magic, but gentle care can help while the body recovers."
        )
    ],
    "rest": [
        (
            "Why is rest important when a body grows weak?",
            "Rest gives the body time to recover and keeps the danger from growing worse. Moving too soon can make weakness more dangerous."
        )
    ],
    "donkey": [
        (
            "Why do people use donkeys and ponies on rough paths?",
            "Because they can carry loads and walk where wheels or tired people may struggle. Helpers like that must be treated carefully."
        )
    ],
}

KNOWLEDGE_ORDER = ["misunderstanding", "herb", "sleep", "bridge", "river", "water", "rest", "donkey"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    animal = f["animal"]
    setting = f["setting"]
    confusion = f["confusion"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.label_word}, and the {animal.label} they were guiding along the road."
        ),
        (
            f"What misunderstanding started the trouble?",
            f"{child.id} thought the plant was {confusion.safe_name}, but it was really {confusion.dangerous_name}. The mistake mattered because the dangerous plant could weaken the animal instead of helping it."
        ),
        (
            f"Why did the moment near {setting.crossing} feel scary?",
            f"It felt scary because the {animal.label} had begun to stagger just as they neared the crossing. A weak animal and a narrow place are a dangerous pair."
        ),
        (
            f"What did {elder.label_word} mean by saying the herb could incapacitate the animal?",
            f"{elder.pronoun().capitalize()} meant the herb could make the animal too weak and sleepy to walk safely. That is why the crossing suddenly became so dangerous."
        ),
    ]
    if outcome == "contained":
        qa.append(
            (
                f"How did {elder.label_word} help?",
                f"{elder.pronoun().capitalize()} {response.qa_text}. That careful help gave the animal time to recover before the danger could grow worse."
            )
        )
        qa.append(
            (
                f"What did {child.id} learn at the end?",
                f"{child.id} learned not to trust a guess just because it feels helpful. After the scare, {child.pronoun()} only touched herbs when an elder named them first."
            )
        )
    else:
        qa.append(
            (
                "Did everyone stay safe?",
                f"Yes, the people and the animal were kept from falling, but the day's load was lost. The sad ending shows that one quick mistake can still bring real harm."
            )
        )
        qa.append(
            (
                f"What lesson stayed with {child.id} afterward?",
                f"The lesson was to ask the true name of a plant before touching it or feeding it to an animal. Guessing had already cost the family a whole day's work."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["setting"].tags) | set(f["animal_cfg"].tags) | set(f["confusion"].tags)
    tags |= set(f["response"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="willow_bridge",
        animal="donkey",
        confusion="bluebell_moonsleep",
        response="rest_water",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="curious",
        delay=0,
    ),
    StoryParams(
        setting="stone_ford",
        animal="goat",
        confusion="fennel_dreamfern",
        response="wake_broth",
        child_name="Tobin",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="eager",
        delay=1,
    ),
    StoryParams(
        setting="pine_pass",
        animal="pony",
        confusion="thyme_drowseleaf",
        response="drop_load",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="quick",
        delay=2,
    ),
    StoryParams(
        setting="willow_bridge",
        animal="pony",
        confusion="fennel_dreamfern",
        response="rest_water",
        child_name="Eli",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="thoughtful",
        delay=0,
    ),
]


ASP_RULES = r"""
hazard(S, C) :- setting(S), confusion(C).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
valid(S, A, C) :- setting(S), animal(A), confusion(C), hazard(S, C).

severity(V) :- chosen_confusion(C), strength(C, S), delay(D), V = S + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(contained) :- contained.
outcome(lost) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for cid, c in CONFUSIONS.items():
        lines.append(asp.fact("confusion", cid))
        lines.append(asp.fact("strength", cid, c.strength))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_confusion", params.confusion),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: empty story.)")
    if "incapacitate" not in sample.story.lower():
        raise StoryError("(Smoke test failed: required seed word missing from story.)")
    sample.to_dict()


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sense = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sense == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  clingo:", sorted(asp_sense))
        print("  python:", sorted(py_sense))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test story generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a folk-tale misunderstanding about a wild herb that can incapacitate an animal."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--confusion", choices=CONFUSIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.animal is None or combo[1] == args.animal)
        and (args.confusion is None or combo[2] == args.confusion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, animal_id, confusion_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    child_name = _pick_child(rng, gender)
    child_trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        animal=animal_id,
        confusion=confusion_id,
        response=response_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        child_trait=child_trait,
        delay=delay,
    )


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.confusion not in CONFUSIONS:
        raise StoryError(f"(Unknown confusion: {params.confusion})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.elder_type not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder type: {params.elder_type})")


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        animal_cfg=ANIMALS[params.animal],
        confusion=CONFUSIONS[params.confusion],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, animal, confusion) combos:\n")
        for setting_id, animal_id, confusion_id in combos:
            print(f"  {setting_id:14} {animal_id:8} {confusion_id}")
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
            header = (
                f"### {p.child_name}: {p.confusion} with {p.animal} at {p.setting} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
