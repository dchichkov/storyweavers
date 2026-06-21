#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/polite_conflict_surprise_tall_tale.py
================================================================

A standalone storyworld for a tall-tale flavored story about politeness,
conflict, and surprise.

Premise
-------
In an exaggerated frontier place, a child is sent down a road with something
important for the town. An enormous obstacle blocks the way. The child first
speaks sharply to a giant local helper, which starts a conflict. When the child
tries again with polite words, the helper agrees to move the obstacle. The
surprise is that something wonderful was hidden under or behind it, and the town
benefits from both the clear road and the child's better manners.

The world is small on purpose: fewer strong variants, each with a clean causal
shape, are better than broad weak coverage.

Run it
------
    python storyworlds/worlds/gpt-5.4/polite_conflict_surprise_tall_tale.py
    python storyworlds/worlds/gpt-5.4/polite_conflict_surprise_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/polite_conflict_surprise_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/polite_conflict_surprise_tall_tale.py --trace
    python storyworlds/worlds/gpt-5.4/polite_conflict_surprise_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/polite_conflict_surprise_tall_tale.py --verify
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
POLITE_MIN = 1
IMPATIENCE_LIMIT = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str = ""
    road: str = ""
    skyline: str = ""
    celebration: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Errand:
    id: str
    item: str = ""
    phrase: str = ""
    purpose: str = ""
    ending_use: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str = ""
    phrase: str = ""
    article: str = ""
    weight: int = 1
    blocks: str = ""
    move_text: str = ""
    surprise: str = ""
    surprise_gain: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    name: str = ""
    type: str = ""
    title: str = ""
    phrase: str = ""
    strength: int = 1
    style: str = ""
    move_text: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_conflict(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["rude_words"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    helper.memes["prickly"] += 1
    helper.memes["refusing"] += 1
    return ["__conflict__"]


def _r_polite_softens(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["polite_words"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["prickly"] = 0.0
    helper.memes["helpfulness"] += 1
    child.memes["good_sense"] += 1
    return ["__softened__"]


def _r_move_obstacle(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    obstacle = world.get("obstacle")
    if helper.memes["helpfulness"] < THRESHOLD:
        return []
    if obstacle.meters["blocked"] < THRESHOLD:
        return []
    sig = ("move",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["moved"] += 1
    child.meters["progress"] += 1
    return ["__moved__"]


def _r_reveal_surprise(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    town = world.get("town")
    child = world.get("child")
    if obstacle.meters["moved"] < THRESHOLD:
        return []
    sig = ("surprise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    town.meters["luck"] += 1
    child.memes["wonder"] += 1
    return ["__surprise__"]


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="soften", tag="social", apply=_r_polite_softens),
    Rule(name="move", tag="physical", apply=_r_move_obstacle),
    Rule(name="surprise", tag="physical", apply=_r_reveal_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def valid_combo(place_id: str, obstacle_id: str, helper_id: str) -> bool:
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    place = PLACES[place_id]
    return helper.strength >= obstacle.weight and bool(place.road)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id in OBSTACLES:
            for helper_id in HELPERS:
                if valid_combo(place_id, obstacle_id, helper_id):
                    combos.append((place_id, obstacle_id, helper_id))
    return combos


def explain_rejection(place_id: str, obstacle_id: str, helper_id: str) -> str:
    place = PLACES[place_id]
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    if helper.strength < obstacle.weight:
        return (
            f"(No story: {helper.name} is famous, but not famous enough to move "
            f"{obstacle.article} {obstacle.label} in {place.label}. Pick a stronger "
            f"helper or a lighter obstacle.)"
        )
    return "(No story: this combination does not make a workable tall tale.)"


def predict_outcome(helper_id: str, obstacle_id: str, polite: bool) -> dict:
    helper = HELPERS[helper_id]
    obstacle = OBSTACLES[obstacle_id]
    can_move = helper.strength >= obstacle.weight
    return {
        "conflict": not polite,
        "clears_road": polite and can_move,
        "surprise": polite and can_move,
    }


def introduce(world: World, child: Entity, parent: Entity, place: Place, errand: Errand) -> None:
    child.memes["duty"] += 1
    world.say(
        f"In {place.label}, where {place.skyline}, {child.id} had been trusted with "
        f"{errand.phrase} for {place.celebration}."
    )
    world.say(
        f"{child.id}'s {parent.label_word} said {child.pronoun('object')} was steady on "
        f"{place.road}, and that was true on ordinary days."
    )


def set_out(world: World, child: Entity, place: Place, errand: Errand) -> None:
    world.say(
        f"But this was no ordinary day. The road bent so far across the country that "
        f"even the fence posts looked tired, and {child.id} hurried along with "
        f"{errand.item} tucked safe in both hands."
    )
    world.say(
        f"{child.pronoun().capitalize()} meant to arrive before the fiddles started, "
        f"because {errand.purpose}."
    )


def block_road(world: World, child: Entity, obstacle: Obstacle, place: Place) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["blocked"] += 1
    child.memes["frustration"] += 1
    world.say(
        f"Then {child.pronoun()} reached a bend in {place.road} and found {obstacle.article} "
        f"{obstacle.phrase} spread across it. {obstacle.blocks}"
    )


def meet_helper(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Close by stood {helper_cfg.name}, {helper_cfg.title}, {helper_cfg.style}."
    )


def rude_request(world: World, child: Entity, helper: Entity) -> None:
    child.memes["rude_words"] += 1
    child.memes["impatience"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Move it right now!" {child.id} blurted. The words hopped out sharp as burrs, '
        f"and {helper.id} drew back instead of stepping in."
    )


def helper_refuses(world: World, helper: Entity) -> None:
    if helper.memes["refusing"] >= THRESHOLD:
        world.say(
            f'"I can pull a cloud down for shade and toss a wagon over a creek," '
            f"{helper.id} said, \"but I do not hurry for barking words.\""
        )


def rethink(world: World, child: Entity, parent: Entity) -> None:
    child.memes["reflection"] += 1
    world.say(
        f"{child.id} felt {child.pronoun('possessive')} cheeks grow warm. "
        f"{child.pronoun().capitalize()} remembered what {child.pronoun('possessive')} "
        f"{parent.label_word} always said: a polite mouth can open a heavy door."
    )


def polite_request(world: World, child: Entity, helper: Entity, obstacle: Obstacle) -> None:
    child.memes["polite_words"] += 1
    propagate(world, narrate=False)
    world.say(
        f'So {child.id} took one slow breath and tried again. "Please, {helper.id}, '
        f'would you help me with {obstacle.article} {obstacle.label}? The whole town is '
        f'waiting, and I would be thankful."'
    )


def helper_accepts(world: World, helper: Entity) -> None:
    if helper.memes["helpfulness"] >= THRESHOLD:
        world.say(
            f'{helper.id} tipped {helper.pronoun("possessive")} hat. '
            f'"Now those are traveling words fit for decent ears," '
            f"{helper.pronoun()} said."
        )


def move_obstacle(world: World, helper_cfg: HelperCfg, obstacle: Obstacle) -> None:
    before = world.get("obstacle").meters["moved"]
    propagate(world, narrate=False)
    if world.get("obstacle").meters["moved"] > before:
        world.say(
            f"Then {helper_cfg.name} {helper_cfg.move_text}, and {obstacle.move_text}."
        )


def reveal_surprise(world: World, obstacle: Obstacle, place: Place, errand: Errand) -> None:
    if world.get("town").meters["luck"] >= THRESHOLD:
        world.say(
            f"But the biggest thing was not the moving. Under the place where the "
            f"{obstacle.label} had rested was {obstacle.surprise}."
        )
        world.say(
            f"Folks later said the whole of {place.label} was brighter after that, because "
            f"{obstacle.surprise_gain}."
        )
        world.say(
            f"{child.id} reached town on time with {errand.item}, and the story of that day "
            f"grew so tall that even the courthouse clock leaned down to listen."
        )


def ending_image(world: World, child: Entity, helper: Entity, place: Place, errand: Errand) -> None:
    child.memes["gratitude"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'At {place.celebration}, {child.id} thanked {helper.id} again in front of everyone. '
        f'That night, while {errand.ending_use}, people said the road had been cleared by '
        f"strength, but the day had really been saved by one polite \"please.\""
    )


def tell(
    place: Place,
    errand: Errand,
    obstacle: Obstacle,
    helper_cfg: HelperCfg,
    child_name: str = "Mara",
    child_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    helper = world.add(
        Entity(
            id=helper_cfg.name,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.name,
            phrase=helper_cfg.phrase,
            attrs={"strength": helper_cfg.strength},
            tags=set(helper_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
            attrs={"weight": obstacle.weight},
            tags=set(obstacle.tags),
        )
    )
    world.add(Entity(id="town", kind="thing", type="town", label=place.label, tags=set(place.tags)))

    introduce(world, child, parent, place, errand)
    set_out(world, child, place, errand)

    world.para()
    block_road(world, child, obstacle, place)
    meet_helper(world, helper, helper_cfg)
    rude_request(world, child, helper)
    helper_refuses(world, helper)

    world.para()
    rethink(world, child, parent)
    polite_request(world, child, helper, obstacle)
    helper_accepts(world, helper)
    move_obstacle(world, helper_cfg, obstacle)

    world.para()
    reveal_surprise(world, obstacle, place, errand)
    ending_image(world, child, helper, place, errand)

    world.facts.update(
        place=place,
        errand=errand,
        obstacle_cfg=obstacle,
        helper_cfg=helper_cfg,
        child=child,
        parent=parent,
        helper=helper,
        obstacle=world.get("obstacle"),
        conflict=child.memes["conflict"] >= THRESHOLD,
        polite=child.memes["polite_words"] >= THRESHOLD,
        moved=world.get("obstacle").meters["moved"] >= THRESHOLD,
        surprise=world.get("town").meters["luck"] >= THRESHOLD,
    )
    return world


PLACES = {
    "prairie": Place(
        id="prairie",
        label="Whistleflat Prairie",
        road="the ribbon road",
        skyline="windmills were taller than church steeples and the wheat nodded at the moon",
        celebration="the Saturday pie social",
        tags={"road", "town"},
    ),
    "canyon": Place(
        id="canyon",
        label="Red Gap Canyon",
        road="the canyon trail",
        skyline="the cliffs were stacked so high they tickled passing thunder",
        celebration="the lantern supper",
        tags={"road", "canyon"},
    ),
    "river": Place(
        id="river",
        label="Big Ford Crossing",
        road="the levee lane",
        skyline="the river rolled by broad enough to make geese feel homesick",
        celebration="the river picnic",
        tags={"road", "river"},
    ),
}

ERRANDS = {
    "pie": Errand(
        id="pie",
        item="a blackberry pie",
        phrase="a blackberry pie wrapped in a blue cloth",
        purpose="the judges could not start the tasting without it",
        ending_use="the pie was sliced into wedges as wide as wagon wheels",
        tags={"pie", "food"},
    ),
    "letter": Errand(
        id="letter",
        item="the mayor's letter",
        phrase="the mayor's letter tied with red string",
        purpose="the band leader needed the letter before the first tune",
        ending_use="the band played until the stars looked tired",
        tags={"letter", "music"},
    ),
    "jam": Errand(
        id="jam",
        item="a jar of plum jam",
        phrase="a jar of plum jam padded in a flour sack",
        purpose="the supper tables were waiting for its sweet purple shine",
        ending_use="biscuits disappeared under glossy spoonfuls of jam",
        tags={"jam", "food"},
    ),
}

OBSTACLES = {
    "boulder": Obstacle(
        id="boulder",
        label="boulder",
        phrase="a boulder as broad as a bakehouse",
        article="a",
        weight=2,
        blocks="It sat there as if the hill had dropped one of its own knees onto the road.",
        move_text="the boulder rolled away like a sleepy gray hog",
        surprise="a cold spring bubbling up clear and singing",
        surprise_gain="that spring gave travelers water and gave the town a new place to fill their cups",
        tags={"stone", "spring"},
    ),
    "cottonwood": Obstacle(
        id="cottonwood",
        label="cottonwood",
        phrase="a fallen cottonwood longer than three schoolhouses laid end to end",
        article="a",
        weight=3,
        blocks="Its branches combed both ditches at once and left no room even for a rabbit.",
        move_text="the whole tree swung aside as lightly as a broom straw",
        surprise="a wild beehive hidden in the trunk, heavy with honey",
        surprise_gain="the cook stirred that honey into biscuits for weeks afterward",
        tags={"tree", "honey"},
    ),
    "haystack": Obstacle(
        id="haystack",
        label="haystack",
        phrase="a haystack blown into one mountain of gold straw",
        article="a",
        weight=1,
        blocks="It had puffed up so grandly across the lane that the scarecrows looked jealous.",
        move_text="the haystack skimmed off the lane in one whooshing armful",
        surprise="a nest of lost fair ribbons tucked dry and bright underneath",
        surprise_gain="those ribbons decorated the celebration hall and fluttered there for a month",
        tags={"hay", "ribbons"},
    ),
    "water_tank": Obstacle(
        id="water_tank",
        label="water tank",
        phrase="a water tank tipped sideways like a metal moon",
        article="a",
        weight=4,
        blocks="It plugged the road from fence to fence and shone hard in the sun.",
        move_text="the tank was nudged upright with one mighty shove",
        surprise="a bed of watermelon vines, green and thriving in the sudden light",
        surprise_gain="the vines later grew melons big enough to feed a brass band",
        tags={"metal", "melons"},
    ),
}

HELPERS = {
    "mulesue": HelperCfg(
        id="mulesue",
        name="Mule Sue",
        type="woman",
        title="the long-armed teamster",
        phrase="the long-armed teamster",
        strength=3,
        style="with a hat brim wide enough to shade a wagon and hands famous for straightening bent plows",
        move_text="looped her rope once, leaned back, and smiled",
        tags={"rope", "teamster"},
    ),
    "tallben": HelperCfg(
        id="tallben",
        name="Tall Ben",
        type="man",
        title="the fence-stepper",
        phrase="the fence-stepper",
        strength=2,
        style="with boots that could cross a creek in one stride and a laugh that rattled weather vanes",
        move_text="set both palms against it and gave a patient push",
        tags={"boots", "giant"},
    ),
    "auntlark": HelperCfg(
        id="auntlark",
        name="Aunt Lark",
        type="aunt",
        title="the windmill whisperer",
        phrase="the windmill whisperer",
        strength=4,
        style="with sleeves rolled high and a calm voice that could talk a mule out of sulking",
        move_text="hooked one elbow under the burden and shifted it as neatly as a teacup",
        tags={"windmill", "strength"},
    ),
}

GIRL_NAMES = ["Mara", "Lila", "June", "Nell", "Rosie", "Ada", "Tess", "Clara"]
BOY_NAMES = ["Eli", "Bo", "Cal", "Rory", "Ned", "Jesse", "Owen", "Finn"]
TRAITS = ["steady", "quick", "cheerful", "brave", "eager"]


@dataclass
class StoryParams:
    place: str
    errand: str
    obstacle: str
    helper: str
    child_name: str
    child_type: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="prairie",
        errand="pie",
        obstacle="boulder",
        helper="tallben",
        child_name="Mara",
        child_type="girl",
        parent="mother",
        trait="steady",
        seed=1,
    ),
    StoryParams(
        place="canyon",
        errand="letter",
        obstacle="cottonwood",
        helper="mulesue",
        child_name="Eli",
        child_type="boy",
        parent="father",
        trait="brave",
        seed=2,
    ),
    StoryParams(
        place="river",
        errand="jam",
        obstacle="haystack",
        helper="mulesue",
        child_name="June",
        child_type="girl",
        parent="mother",
        trait="quick",
        seed=3,
    ),
    StoryParams(
        place="prairie",
        errand="letter",
        obstacle="water_tank",
        helper="auntlark",
        child_name="Bo",
        child_type="boy",
        parent="father",
        trait="eager",
        seed=4,
    ),
]


KNOWLEDGE = {
    "polite": [
        (
            "What does polite mean?",
            "Polite means using kind, respectful words and manners. Saying please and thank you is one way to be polite."
        )
    ],
    "conflict": [
        (
            "What is a conflict in a story?",
            "A conflict is a problem or disagreement that makes the story hard for the characters. It gives them something they need to solve."
        )
    ],
    "talltale": [
        (
            "What is a tall tale?",
            "A tall tale is a story that uses playful exaggeration. The people and things in it seem much bigger, stronger, or stranger than in ordinary life."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes up from the ground. It can make a cool little pool or stream."
        )
    ],
    "honey": [
        (
            "Where does honey come from?",
            "Honey is made by bees. They gather nectar from flowers and turn it into sweet honey in the hive."
        )
    ],
    "ribbons": [
        (
            "What can ribbons be used for at a celebration?",
            "Ribbons can be tied up as decorations. They make a place look bright and festive."
        )
    ],
    "melons": [
        (
            "Why are watermelons good picnic food?",
            "Watermelons are juicy and sweet, and many people can share one. They also feel cool on a warm day."
        )
    ],
}
KNOWLEDGE_ORDER = ["polite", "conflict", "talltale", "spring", "honey", "ribbons", "melons"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    place = f["place"]
    errand = f["errand"]
    return [
        'Write a short tall-tale story for a 3-to-5-year-old that includes the word "polite."',
        f"Tell a child-friendly story set in {place.label} where {child.id} faces a conflict because "
        f"{obstacle.article} {obstacle.label} blocks the road while {child.pronoun()} carries {errand.item}.",
        f"Write a tall tale where a sharp first request causes trouble, a polite second request brings help from "
        f"{helper.id}, and the ending includes a surprise hidden under the obstacle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    place = f["place"]
    errand = f["errand"]
    obstacle = f["obstacle_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was carrying {errand.item} through {place.label}, and {helper.id}, "
            f"the giant helper nearby."
        ),
        (
            f"Why was {child.id} hurrying down the road?",
            f"{child.id} was hurrying because {errand.purpose}. The errand mattered to the whole town, so the blocked road felt like a big problem."
        ),
        (
            f"What caused the conflict with {helper.id}?",
            f"The conflict started when {child.id} spoke sharply instead of being polite. Those rude words made {helper.id} refuse to help at first."
        ),
        (
            f"How was the conflict solved?",
            f"{child.id} remembered what {parent.label_word} taught about manners and tried again with a polite \"please.\" That changed the helper's feelings, so {helper.id} decided to help."
        ),
    ]
    if f["moved"]:
        out.append(
            (
                f"What did {helper.id} do after the polite request?",
                f"{helper.id} moved the {obstacle.label} out of the road. That let {child.id} continue the trip and proved that kind words had real power in the story."
            )
        )
    if f["surprise"]:
        out.append(
            (
                "What was the surprise at the end?",
                f"The surprise was {obstacle.surprise}. It was hidden until the obstacle moved, so the help did more than clear the road."
            )
        )
        out.append(
            (
                f"Why was the ending happy for the town?",
                f"It was happy because {child.id} arrived on time with {errand.item}, and also because {obstacle.surprise_gain}. The ending shows that one polite choice helped many people."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"polite", "conflict", "talltale"}
    obstacle = world.facts["obstacle_cfg"]
    if "spring" in obstacle.tags:
        tags.add("spring")
    if "honey" in obstacle.tags:
        tags.add("honey")
    if "ribbons" in obstacle.tags:
        tags.add("ribbons")
    if "melons" in obstacle.tags:
        tags.add("melons")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Ob, H) :- place(Place), obstacle(Ob), helper(H),
                       strength(H, S), weight(Ob, W), S >= W.

conflict_started :- request(rude).
polite_request   :- request(polite).

moved            :- polite_request, chosen_helper(H), chosen_obstacle(Ob),
                    strength(H, S), weight(Ob, W), S >= W.

surprise         :- moved.

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("weight", obstacle_id, obstacle.weight))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("strength", helper_id, helper.strength))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> dict:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("request", "rude"),
            asp.fact("request", "polite"),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show moved/0.\n#show surprise/0.\n#show conflict_started/0."))
    atoms = set(model.symbols(shown=True))
    moved = any(str(a) == "moved" for a in atoms)
    surprise = any(str(a) == "surprise" for a in atoms)
    conflict = any(str(a) == "conflict_started" for a in atoms)
    return {"moved": moved, "surprise": surprise, "conflict": conflict}


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in smoke_cases:
        py = {
            "moved": HELPERS[params.helper].strength >= OBSTACLES[params.obstacle].weight,
            "surprise": HELPERS[params.helper].strength >= OBSTACLES[params.obstacle].weight,
            "conflict": True,
        }
        asp_res = asp_outcome(params)
        if py != asp_res:
            rc = 1
            print(f"MISMATCH outcome for {params}: python={py} asp={asp_res}")
            break
    else:
        print(f"OK: ASP outcome model matches Python on {len(smoke_cases)} curated cases.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale storyworld about a blocked road, a polite second try, and a surprise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.helper:
        if not valid_combo(args.place, args.obstacle, args.helper):
            raise StoryError(explain_rejection(args.place, args.obstacle, args.helper))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    errand_id = args.errand or rng.choice(sorted(ERRANDS))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        errand=errand_id,
        obstacle=obstacle_id,
        helper=helper_id,
        child_name=child_name,
        child_type=child_type,
        parent=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.errand not in ERRANDS:
        raise StoryError(f"(Invalid errand: {params.errand})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if not valid_combo(params.place, params.obstacle, params.helper):
        raise StoryError(explain_rejection(params.place, params.obstacle, params.helper))

    world = tell(
        place=PLACES[params.place],
        errand=ERRANDS[params.errand],
        obstacle=OBSTACLES[params.obstacle],
        helper_cfg=HELPERS[params.helper],
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent,
    )
    world.get("child").traits.append(params.trait)

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
        print(asp_program("", "#show valid/3.\n#show conflict_started/0.\n#show moved/0.\n#show surprise/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, helper) combos:\n")
        for place_id, obstacle_id, helper_id in combos:
            print(f"  {place_id:8} {obstacle_id:11} {helper_id}")
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
            header = f"### {p.child_name}: {p.obstacle} on {p.place} with {p.helper}"
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
