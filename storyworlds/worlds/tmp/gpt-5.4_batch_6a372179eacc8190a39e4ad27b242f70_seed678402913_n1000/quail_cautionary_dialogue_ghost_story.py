#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py
===================================================================

A small storyworld about a child who mistakes a quail's nighttime call for a
ghostly whisper and feels tempted to wander into the dark alone. The world model
checks whether the setting, the quail's hiding place, and the hazard fit
together, then tells a cautionary ghost-story-shaped tale with lots of dialogue.
The happy endings are not "nothing happened" blanks: the child learns what the
sound really was and ends with a safe new habit.

Run it
------
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py --setting farmhouse --hazard well --response porch_call
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py --hazard reeds
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/quail_cautionary_dialogue_ghost_story.py --verify
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "quiet", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    house_image: str
    dark_place: str
    night_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuailSpot:
    id: str
    phrase: str
    call_text: str
    flutter_text: str
    explain_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    warning: str
    stumble_text: str
    severity: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class SafeTool:
    id: str
    phrase: str
    glow: str
    use_text: str
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


def _r_dark_risk(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["outside_alone"] < THRESHOLD:
        return []
    sig = ("dark_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["risk"] += 1
    child.memes["fear"] += 1
    return ["__risk__"]


def _r_hazard(world: World) -> list[str]:
    child = world.get("child")
    place = world.get("place")
    if child.meters["toward_voice"] < THRESHOLD:
        return []
    if child.meters["risk"] < THRESHOLD:
        return []
    sig = ("hazard",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["danger"] += 1
    child.meters["startled"] += 1
    child.memes["fear"] += 1
    return ["__hazard__"]


CAUSAL_RULES = [
    Rule(name="dark_risk", tag="physical", apply=_r_dark_risk),
    Rule(name="hazard", tag="physical", apply=_r_hazard),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def habitat_match(setting: Setting, spot: QuailSpot, hazard: Hazard) -> bool:
    return bool(setting.tags & spot.tags) and bool(setting.tags & hazard.tags)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_heed(relation: str, elder_age: int, child_age: int, trait: str) -> bool:
    older = relation == "grandparent" or elder_age > child_age
    authority = initial_caution(trait) + (3.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def hazard_severity(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= hazard_severity(hazard, delay)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["outside_alone"] += 1
    child.meters["toward_voice"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": child.meters["risk"],
        "fear": child.memes["fear"],
        "danger": sim.get("place").meters["danger"],
    }


def open_door(world: World, child: Entity) -> None:
    child.meters["outside_alone"] += 1
    child.meters["toward_voice"] += 1
    propagate(world, narrate=False)


def opening(world: World, child: Entity, elder: Entity, setting: Setting, tool: SafeTool) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Night gathered around {setting.place}, and {setting.house_image}. "
        f"{setting.night_detail}"
    )
    world.say(
        f"{child.id} stood by the window with {tool.phrase} nearby, listening so hard "
        f"that even the ticking clock seemed to whisper."
    )
    world.say(
        f'"Did you hear that?" {child.id} asked. "It sounds like a ghost calling from {setting.dark_place}."'
    )
    world.say(
        f'{elder.label_word.capitalize()} looked up from the rocking chair. '
        f'"I heard it," {elder.pronoun()} said, "but not every strange sound belongs to a ghost."'
    )


def first_call(world: World, spot: QuailSpot) -> None:
    world.say(
        f"From the dark came a thin cry: {spot.call_text}. The sound floated once, "
        f"then again, as if the night itself had learned to talk."
    )


def warning(world: World, elder: Entity, child: Entity, hazard: Hazard, spot: QuailSpot) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["caution"] += 1
    extra = ""
    if child.memes["caution"] >= 6:
        extra = f" {child.pronoun().capitalize()} hugged {child.pronoun('possessive')} elbows and listened."
    world.say(
        f'"Stay inside until I come with you," {elder.label_word} said. '
        f'"The voice may be only a quail hidden in {spot.phrase}, but {hazard.warning}."{extra}'
    )


def temptation(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"But what if it really is a ghost?" {child.id} whispered. '
        f'"What if it wants me to follow?"'
    )


def heed(world: World, elder: Entity, child: Entity, tool: SafeTool) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{child.id} put a hand on the latch, then pulled it back. '
        f'"I will wait," {child.pronoun()} said.'
    )
    world.say(
        f'{elder.label_word.capitalize()} nodded and lifted {tool.phrase}. '
        f'"That is the brave kind of waiting," {elder.pronoun()} said.'
    )


def sneak_out(world: World, child: Entity, setting: Setting) -> None:
    open_door(world, child)
    world.say(
        f'Before the grown-up could rise, {child.id} eased the door open and slipped toward {setting.dark_place}.'
    )


def hazard_turn(world: World, child: Entity, hazard: Hazard, spot: QuailSpot) -> None:
    world.say(
        f"The night felt larger outside. Then {spot.flutter_text}, and {hazard.stumble_text}."
    )
    world.say(
        f'"Oh!" cried {child.id}. The ghostly voice broke into beating wings, and fear rushed in where curiosity had been.'
    )


def rescue(world: World, elder: Entity, child: Entity, hazard: Hazard, response: Response, spot: QuailSpot) -> None:
    child.meters["outside_alone"] = 0.0
    child.meters["toward_voice"] = 0.0
    world.get("place").meters["danger"] = 0.0
    body = response.text.format(hazard=hazard.label)
    world.say(
        f'{elder.label_word.capitalize()} came after {child.id} at once and {body}.'
    )
    world.say(
        f'Together they listened again. This time the call came small and birdlike, and {elder.label_word} pointed toward {spot.phrase}.'
    )


def rescue_fail(world: World, elder: Entity, child: Entity, hazard: Hazard, response: Response) -> None:
    body = response.fail.format(hazard=hazard.label)
    world.say(
        f'{elder.label_word.capitalize()} hurried after {child.id} and {body}.'
    )
    world.say(
        f"For one awful moment, the dark felt bigger than the house, and even the little yard seemed full of shadows."
    )


def explanation(world: World, elder: Entity, child: Entity, spot: QuailSpot) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    child.memes["wonder"] += 1
    world.say(
        f'"Listen now," {elder.label_word} said softly. "{spot.explain_text}"'
    )
    world.say(
        f'"A quail?" {child.id} asked.'
    )
    world.say(
        f'"Yes," {elder.pronoun()} said. "A living bird in the dark grass sounds spooky at night, but spooky is not the same as magic, and mystery is never a reason to wander off alone."'
    )


def porch_resolution(world: World, elder: Entity, child: Entity, tool: SafeTool, spot: QuailSpot) -> None:
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    world.say(
        f"After that, they stayed on the porch together with {tool.phrase}, and {tool.glow}."
    )
    world.say(
        f"Again the night called {spot.call_text}, but now {child.id} smiled instead of shivering."
    )
    world.say(
        f'"That is the quail," {child.pronoun()} said proudly. "And if I want to hear it, I wait for a grown-up and bring a light."'
    )


def uneasy_end(world: World, elder: Entity, child: Entity, tool: SafeTool) -> None:
    child.memes["lesson"] += 1
    child.memes["fear"] += 1
    world.say(
        f'{elder.label_word.capitalize()} carried {child.id} back inside and set {tool.phrase} on the table.'
    )
    world.say(
        f'The room felt warm again, but {child.id} did not forget the dark outside the door.'
    )
    world.say(
        f'From then on, whenever a strange cry drifted over the yard, {child.pronoun()} called for a grown-up before taking even one step.'
    )


def tell(
    setting: Setting,
    spot: QuailSpot,
    hazard: Hazard,
    tool: SafeTool,
    response: Response,
    child_name: str = "Nora",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    elder_name: str = "Elder",
    trait: str = "careful",
    child_age: int = 5,
    elder_age: int = 67,
    relation: str = "grandparent",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        age=child_age,
        attrs={"name": child_name, "relation": relation},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_name,
        phrase=elder_name,
        role="elder",
        age=elder_age,
        attrs={"relation": relation},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=setting.place,
        phrase=setting.place,
    ))

    child.memes["bravery"] = BRAVERY_INIT
    child.memes["caution"] = initial_caution(trait)
    world.facts["child_name"] = child_name
    world.facts["elder_name"] = elder_name

    opening(world, child, elder, setting, tool)
    first_call(world, spot)

    world.para()
    warning(world, elder, child, hazard, spot)
    temptation(world, child)

    averted = would_heed(relation, elder_age, child_age, trait)
    severity = hazard_severity(hazard, delay)
    contained = True

    if averted:
        heed(world, elder, child, tool)
        world.para()
        explanation(world, elder, child, spot)
        porch_resolution(world, elder, child, tool, spot)
    else:
        sneak_out(world, child, setting)
        world.para()
        hazard_turn(world, child, hazard, spot)
        contained = is_contained(response, hazard, delay)
        world.para()
        if contained:
            rescue(world, elder, child, hazard, response, spot)
            explanation(world, elder, child, spot)
            world.para()
            porch_resolution(world, elder, child, tool, spot)
        else:
            rescue_fail(world, elder, child, hazard, response)
            uneasy_end(world, elder, child, tool)

    outcome = "averted" if averted else ("contained" if contained else "shaken")
    world.facts.update(
        setting=setting,
        spot=spot,
        hazard_cfg=hazard,
        tool=tool,
        response=response,
        child=child,
        elder=elder,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    quail_spot: str
    hazard: str
    tool: str
    response: str
    child_name: str
    child_gender: str
    elder_type: str
    elder_name: str
    trait: str
    child_age: int = 5
    elder_age: int = 67
    relation: str = "grandparent"
    delay: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "farmhouse": Setting(
        id="farmhouse",
        place="an old farmhouse",
        house_image="its porch boards held silver moonlight",
        dark_place="the yard beyond the old pump",
        night_detail="The wind rubbed softly through the corn and made the screens hum.",
        tags={"field", "yard", "well"},
    ),
    "orchard": Setting(
        id="orchard",
        place="a cottage beside an apple orchard",
        house_image="its windows shone like yellow eyes in the dark",
        dark_place="the path beside the hedge",
        night_detail="Leaves clicked together overhead, and fallen apples breathed out a sweet smell.",
        tags={"hedge", "orchard", "path"},
    ),
    "cabin": Setting(
        id="cabin",
        place="a little cabin by the reeds",
        house_image="its doorway spilled one square of lamplight onto the porch",
        dark_place="the bank where the reeds leaned over the water",
        night_detail="The river moved in black folds, and the reeds whispered to each other.",
        tags={"reeds", "bank", "water"},
    ),
}

QUAIL_SPOTS = {
    "field_grass": QuailSpot(
        id="field_grass",
        phrase="the field grass",
        call_text='"bob-white, bob-white"',
        flutter_text="a quail burst up from the field grass with a wild thrum of wings",
        explain_text="That is a quail calling from the field grass. In daylight it would look ordinary, but at night its voice can sound like a little lost spirit.",
        tags={"field"},
    ),
    "hedge_root": QuailSpot(
        id="hedge_root",
        phrase="the roots of the hedge",
        call_text='"bob-white... bob-white..."',
        flutter_text="a quail sprang from the roots of the hedge and brushed the leaves with its wings",
        explain_text="That is a quail tucked under the hedge. The dark makes its tiny voice stretch and echo.",
        tags={"hedge", "orchard"},
    ),
    "reed_edge": QuailSpot(
        id="reed_edge",
        phrase="the dry grass beside the reeds",
        call_text='"bob-white!"',
        flutter_text="a quail shot out from the dry grass beside the reeds and rattled the stalks",
        explain_text="That is a quail hiding beside the reeds. Night carries the sound over the water and turns it strange.",
        tags={"reeds", "bank"},
    ),
}

HAZARDS = {
    "well": Hazard(
        id="well",
        label="the old well",
        the="the old well",
        warning="the old well sits there with broken stones around it",
        stumble_text="the ground dipped suddenly near the old well",
        severity=2,
        tags={"well", "yard"},
    ),
    "hedge": Hazard(
        id="hedge",
        label="the thorn hedge",
        the="the thorn hedge",
        warning="the thorn hedge catches sleeves and scratches bare hands",
        stumble_text="the thorn hedge reached out with sharp twigs and snagged at a sleeve",
        severity=1,
        tags={"hedge", "path", "orchard"},
    ),
    "reeds": Hazard(
        id="reeds",
        label="the muddy reeds",
        the="the muddy reeds",
        warning="the reeds hide slick mud by the water's edge",
        stumble_text="the mud beside the reeds sucked at one small shoe",
        severity=2,
        tags={"reeds", "water", "bank"},
    ),
}

SAFE_TOOLS = {
    "lantern": SafeTool(
        id="lantern",
        phrase="a tin lantern",
        glow="its round window made a steady honey-colored ring on the porch",
        use_text="carried the lantern low so the ground showed clearly",
        tags={"lantern", "light"},
    ),
    "flashlight": SafeTool(
        id="flashlight",
        phrase="a flashlight",
        glow="its beam made a clean white path over the boards",
        use_text="shone the flashlight over every dark step",
        tags={"flashlight", "light"},
    ),
    "porch_lamp": SafeTool(
        id="porch_lamp",
        phrase="the porch lamp",
        glow="its soft bulb pushed the shadows back from the door",
        use_text="kept the porch lamp bright while calling from the steps",
        tags={"lamp", "light"},
    ),
}

RESPONSES = {
    "porch_call": Response(
        id="porch_call",
        sense=3,
        power=3,
        text='called "{name}! Freeze there," then kept {tool} steady and guided the child back step by step',
        fail='called for the child, but the dark swallowed the words for a moment before the little feet stopped',
        qa_text="called from the porch and guided the child back carefully",
        tags={"call_adult", "light"},
    ),
    "hand_lantern": Response(
        id="hand_lantern",
        sense=3,
        power=2,
        text="hurried close, took a small hand, and led the child away from {hazard}",
        fail="reached the child only after one frightened stumble beside {hazard}",
        qa_text="took the child's hand and led the child away from danger",
        tags={"hand_holding", "light"},
    ),
    "scold_from_window": Response(
        id="scold_from_window",
        sense=1,
        power=0,
        text="shouted from the window",
        fail="shouted from the window, but shouting alone did not light the ground or make the danger smaller",
        qa_text="shouted from the window",
        tags={"scold"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Rose", "Ava", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Jack", "Theo", "Finn", "Noah", "Eli"]
ELDER_NAMES = {
    "grandmother": ["Grandma May", "Grandma Ruth", "Grandma June"],
    "grandfather": ["Grandpa Will", "Grandpa Abe", "Grandpa Tom"],
    "mother": ["Mom", "Mother"],
    "father": ["Dad", "Father"],
}
TRAITS = ["careful", "curious", "quiet", "brave", "thoughtful", "sensible"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for sid, setting in SETTINGS.items():
        for qid, spot in QUAIL_SPOTS.items():
            for hid, hazard in HAZARDS.items():
                if habitat_match(setting, spot, hazard):
                    combos.append((sid, qid, hid))
    return sorted(combos)


def explain_rejection(setting: Setting, spot: QuailSpot, hazard: Hazard) -> str:
    return (
        f"(No story: {spot.phrase} and {hazard.the} do not fit naturally with {setting.place}. "
        f"The quail's hiding place, the danger, and the setting should belong to the same little world.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_heed(params.relation, params.elder_age, params.child_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay)
    return "contained" if contained else "shaken"


KNOWLEDGE = {
    "quail": [(
        "What is a quail?",
        "A quail is a small round bird that hides in grass and brush. It can make a clear call that sounds surprisingly loud in the evening."
    )],
    "night_sounds": [(
        "Why do sounds seem spooky at night?",
        "At night, when everything is dark and quiet, ordinary sounds can seem bigger and stranger. Your ears notice little noises more, and your imagination fills in the shadows."
    )],
    "well": [(
        "Why should children stay away from an old well?",
        "An old well can have loose stones and a deep opening. That makes it dangerous to play near without a grown-up."
    )],
    "hedge": [(
        "Why can a thorn hedge hurt you?",
        "A thorn hedge has sharp points on its branches. Those thorns can scratch skin and catch clothes."
    )],
    "reeds": [(
        "Why is mud by the water dangerous in the dark?",
        "Mud near water can be slippery and hard to see. A child can lose a shoe or fall without warning."
    )],
    "light": [(
        "Why is it smart to bring a light outside at night?",
        "A light helps you see where your feet are going and what is around you. That makes it easier to notice steps, mud, and other dangers."
    )],
    "call_adult": [(
        "What should a child do when a strange sound outside feels scary?",
        "The child should tell a grown-up and stay where the grown-up can see them. Going alone into the dark can turn a mystery into a real danger."
    )],
}
KNOWLEDGE_ORDER = ["quail", "night_sounds", "well", "hedge", "reeds", "light", "call_adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    hazard = f["hazard_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a child-facing ghost-story-style cautionary tale with dialogue, where a child hears a quail at night near {setting.place} and mistakes it for something spooky.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle ghost-story where {f['child_name']} wants to follow a mysterious voice into the dark, but {elder.label_word} warns {child.pronoun('object')} in time and {child.pronoun()} chooses to wait.",
            f'Write a spooky-but-safe story that teaches children not to wander toward mysterious sounds alone, ending with the child correctly naming a quail.',
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a dialogue-heavy cautionary story where {f['child_name']} slips outside toward {hazard.the}, gets frightened, and is safely guided back by {elder.label_word}.",
            f'Write a ghost-story-shaped story with a real-world explanation at the end: the strange voice turns out to be a quail, and the child learns to bring a grown-up and a light.',
        ]
    return [
        base,
        f"Tell a spooky cautionary story where {f['child_name']} goes outside alone, the dark feels dangerous near {hazard.the}, and the child never forgets the lesson.",
        f'Write a story with dialogue that warns children not to follow odd nighttime sounds alone, even if the sound later turns out to be only a quail.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    spot = f["spot"]
    hazard = f["hazard_cfg"]
    tool = f["tool"]
    response = f["response"]
    outcome = f["outcome"]
    child_name = f["child_name"]
    elder_word = elder.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child who hears a spooky sound at night, and {elder_word}, the grown-up who helps. Their talk is what turns the fear into a lesson."
        ),
        (
            "What strange sound did the child hear?",
            f"The child heard a voice-like cry in the dark that sounded ghostly at first. Later, the grown-up explained that the sound came from a quail hiding in {spot.phrase}."
        ),
        (
            f"Why did {elder_word} tell {child_name} not to go alone?",
            f"{elder_word.capitalize()} knew that the dark around {hazard.the} was dangerous. The warning was not about being mean; it was about keeping the child safe while the mystery was still unclear."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What did {child_name} do after the warning?",
            f"{child_name} stopped at the door and chose to wait instead of following the sound. That small choice kept the mystery spooky but prevented the danger from becoming real."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the child and grown-up listening safely together from the porch with {tool.phrase}. The child learned to name the quail and to wait for help before going into the dark."
        ))
    elif outcome == "contained":
        qa.append((
            f"What happened when {child_name} went outside?",
            f"The child got frightened near {hazard.the} when the dark suddenly felt real and the quail burst up nearby. That scary moment showed why following strange sounds alone was a bad idea."
        ))
        qa.append((
            f"How did {elder_word} help?",
            f"{elder_word.capitalize()} {response.qa_text}. The help worked because the grown-up acted quickly and kept the child from wandering farther."
        ))
        qa.append((
            "What was the 'ghost' really?",
            f"It was really a quail calling from the dark. Once the child was safe and listening calmly, the sound changed from spooky mystery into a real thing that could be understood."
        ))
    else:
        qa.append((
            f"Did {elder_word} stop the danger right away?",
            f"Not right away. The child had one frightened stumble in the dark first, which made the lesson feel serious and unforgettable."
        ))
        qa.append((
            "How did the story end?",
            f"It ended back inside the warm house, but with the child still remembering how frightening the dark had felt. After that, the child always called for a grown-up before stepping outside at night."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quail", "night_sounds", "light"}
    hazard = world.facts["hazard_cfg"]
    if hazard.id == "well":
        tags.add("well")
    if hazard.id == "hedge":
        tags.add("hedge")
    if hazard.id == "reeds":
        tags.add("reeds")
    if world.facts["outcome"] != "averted":
        tags.add("call_adult")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="farmhouse",
        quail_spot="field_grass",
        hazard="well",
        tool="lantern",
        response="porch_call",
        child_name="Nora",
        child_gender="girl",
        elder_type="grandmother",
        elder_name="Grandma May",
        trait="careful",
        child_age=5,
        elder_age=68,
        relation="grandparent",
        delay=0,
    ),
    StoryParams(
        setting="orchard",
        quail_spot="hedge_root",
        hazard="hedge",
        tool="flashlight",
        response="hand_lantern",
        child_name="Ben",
        child_gender="boy",
        elder_type="grandfather",
        elder_name="Grandpa Abe",
        trait="curious",
        child_age=6,
        elder_age=70,
        relation="grandparent",
        delay=0,
    ),
    StoryParams(
        setting="cabin",
        quail_spot="reed_edge",
        hazard="reeds",
        tool="porch_lamp",
        response="hand_lantern",
        child_name="Lucy",
        child_gender="girl",
        elder_type="mother",
        elder_name="Mom",
        trait="brave",
        child_age=6,
        elder_age=30,
        relation="parent",
        delay=1,
    ),
]


ASP_RULES = r"""
habitat_match(S, Q, H) :- setting(S), quail_spot(Q), hazard(H),
                          setting_tag(S, T1), spot_tag(Q, T1),
                          setting_tag(S, T2), hazard_tag(H, T2).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, Q, H) :- habitat_match(S, Q, H).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_guardian :- relation(grandparent).
older_guardian :- elder_age(EA), child_age(CA), EA > CA.

authority(C + B) :- init_caution(C), bonus(B).
bonus(3) :- older_guardian.
bonus(0) :- not older_guardian.

averted :- older_guardian, authority(A), bravery_init(BR), A > BR.

severity(V + D) :- chosen_hazard(H), hazard_severity(H, V), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- not averted, resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(shaken) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(setting.tags):
            lines.append(asp.fact("setting_tag", sid, tag))
    for qid, spot in QUAIL_SPOTS.items():
        lines.append(asp.fact("quail_spot", qid))
        for tag in sorted(spot.tags):
            lines.append(asp.fact("spot_tag", qid, tag))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_severity", hid, hazard.severity))
        for tag in sorted(hazard.tags):
            lines.append(asp.fact("hazard_tag", hid, tag))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("child_age", params.child_age),
        asp.fact("elder_age", params.elder_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.quail_spot not in QUAIL_SPOTS:
        raise StoryError(f"(Unknown quail_spot: {params.quail_spot})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.tool not in SAFE_TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    setting = SETTINGS[params.setting]
    spot = QUAIL_SPOTS[params.quail_spot]
    hazard = HAZARDS[params.hazard]
    if not habitat_match(setting, spot, hazard):
        raise StoryError(explain_rejection(setting, spot, hazard))


def asp_verify() -> int:
    rc = 0
    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatch = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome predictions differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a ghostly quail call, a tempting dark, and a cautionary lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quail-spot", dest="quail_spot", choices=QUAIL_SPOTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=SAFE_TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", dest="elder_type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="head start the child gets in the dark")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def pick_elder_name(rng: random.Random, elder_type: str) -> str:
    return rng.choice(ELDER_NAMES[elder_type])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.setting and args.quail_spot and args.hazard:
        setting = SETTINGS[args.setting]
        spot = QUAIL_SPOTS[args.quail_spot]
        hazard = HAZARDS[args.hazard]
        if not habitat_match(setting, spot, hazard):
            raise StoryError(explain_rejection(setting, spot, hazard))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.quail_spot is None or combo[1] == args.quail_spot)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, quail_spot, hazard = rng.choice(combos)
    tool = args.tool or rng.choice(sorted(SAFE_TOOLS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    relation = "grandparent" if elder_type in {"grandmother", "grandfather"} else "parent"
    child_name = pick_child(rng, child_gender)
    elder_name = pick_elder_name(rng, elder_type)
    trait = args.trait or rng.choice(TRAITS)
    child_age = rng.choice([4, 5, 6, 7])
    elder_age = rng.choice([30, 34, 38]) if relation == "parent" else rng.choice([62, 67, 71])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    params = StoryParams(
        setting=setting,
        quail_spot=quail_spot,
        hazard=hazard,
        tool=tool,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        elder_name=elder_name,
        trait=trait,
        child_age=child_age,
        elder_age=elder_age,
        relation=relation,
        delay=delay,
    )
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        spot=QUAIL_SPOTS[params.quail_spot],
        hazard=HAZARDS[params.hazard],
        tool=SAFE_TOOLS[params.tool],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        elder_name=params.elder_name,
        trait=params.trait,
        child_age=params.child_age,
        elder_age=params.elder_age,
        relation=params.relation,
        delay=params.delay,
    )

    story_text = world.render()
    child_name = world.facts["child_name"]
    elder_name = world.facts["elder_name"]
    story_text = story_text.replace("child", child_name).replace("elder", elder_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (setting, quail_spot, hazard) combos:\n")
        for setting, spot, hazard in combos:
            print(f"  {setting:10} {spot:12} {hazard}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.setting}, {p.quail_spot}, {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
