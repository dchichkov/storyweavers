#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/visa_dialogue_transformation_foreshadowing_animal_story.py
======================================================================================

A standalone story world for a gentle animal tale about a young caterpillar, a
visa, and a journey that becomes possible only after a real transformation.

The seed asked for:
- the word "visa"
- Dialogue
- Transformation
- Foreshadowing
- an Animal Story style

This world rebuilds that prompt as a tiny simulation with typed entities,
physical meters and emotional memes, a reasonableness gate, and an inline ASP
twin.

Premise
-------
A little caterpillar wants to reach a flower place across a marsh border, but
the crossing requires a visa. An impatient shortcut would be unsafe. While the
visa is being prepared, signs in the world foreshadow a coming change: the
caterpillar grows sleepy, hangs still, and becomes a butterfly. The same wait
that felt frustrating turns out to be exactly what was needed.

Run it
------
python storyworlds/worlds/gpt-5.4/visa_dialogue_transformation_foreshadowing_animal_story.py
python storyworlds/worlds/gpt-5.4/visa_dialogue_transformation_foreshadowing_animal_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/visa_dialogue_transformation_foreshadowing_animal_story.py --all --qa
python storyworlds/worlds/gpt-5.4/visa_dialogue_transformation_foreshadowing_animal_story.py --json
python storyworlds/worlds/gpt-5.4/visa_dialogue_transformation_foreshadowing_animal_story.py --verify
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
        female = {"girl", "mother", "hen", "duck", "goose", "ladybug"}
        male = {"boy", "father", "rooster", "drake", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.id


@dataclass
class Border:
    id: str
    label: str
    crossing: str
    hazard: str
    danger: int
    sign_text: str
    foreshadow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Destination:
    id: str
    label: str
    bloom: str
    nectar: str
    travel_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Official:
    id: str
    kind: str
    label: str
    voice: str
    visa_material: str
    visa_mark: str
    helper_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    sense: int
    travel_mode: str
    requires_wings: bool
    safe_without_wings: bool
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    border: str
    destination: str
    official: str
    method: str
    hero_name: str
    helper_name: str
    helper_kind: str
    parent_tone: str
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


def _r_border_risk(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("attempted_crossing") and world.get("hero").meters["wings"] < THRESHOLD:
        sig = ("border_risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["fear"] += 1
            world.get("border").meters["risk"] += 1
            out.append("__risk__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["waiting"] >= THRESHOLD and hero.meters["ready_to_change"] >= THRESHOLD:
        sig = ("transform",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.type = "butterfly"
            hero.label = "butterfly"
            hero.meters["wings"] += 1
            hero.meters["cocooned"] += 1
            hero.memes["relief"] += 1
            hero.memes["wonder"] += 1
            out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="border_risk", tag="physical", apply=_r_border_risk),
    Rule(name="transform", tag="physical", apply=_r_transform),
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


BORDERS = {
    "reed_bridge": Border(
        id="reed_bridge",
        label="Reed Bridge",
        crossing="a narrow bridge of tied reeds over the marsh water",
        hazard="the wet reeds wobbled over dark water",
        danger=2,
        sign_text="VISA CHECK BEFORE CROSSING",
        foreshadow="Even before morning fully woke, the bridge whispered and swayed in the wind.",
        tags={"bridge", "marsh"},
    ),
    "lily_ferry": Border(
        id="lily_ferry",
        label="Lily Ferry",
        crossing="a round lily-pad ferry that drifted from bank to bank",
        hazard="the ferry rocked whenever the water birds landed nearby",
        danger=1,
        sign_text="SHOW YOUR VISA TO THE FERRY KEEPER",
        foreshadow="The lily pad bobbed in little circles, as if the pond were practicing a gentle warning.",
        tags={"ferry", "pond"},
    ),
    "pebble_gate": Border(
        id="pebble_gate",
        label="Pebble Gate",
        crossing="a low stone arch beside a rushing stream",
        hazard="the stream splashed the path and made the stones slippery",
        danger=2,
        sign_text="TRAVELERS NEED A VISA PAST THIS GATE",
        foreshadow="Tiny splashes kept tapping the stones, and each tap sounded like a patient little knock.",
        tags={"gate", "stream"},
    ),
}

DESTINATIONS = {
    "blossom_garden": Destination(
        id="blossom_garden",
        label="Blossom Garden",
        bloom="pink apple blossoms",
        nectar="sweet blossom nectar",
        travel_need="The softest milkweed patch in the valley grew there.",
        tags={"flowers", "garden"},
    ),
    "sunny_orchard": Destination(
        id="sunny_orchard",
        label="Sunny Orchard",
        bloom="white pear blooms",
        nectar="cool drops of pear nectar",
        travel_need="Warm leaves there were perfect for a first fluttering rest.",
        tags={"orchard", "flowers"},
    ),
    "moonlit_meadow": Destination(
        id="moonlit_meadow",
        label="Moonlit Meadow",
        bloom="silver evening flowers",
        nectar="moon-sweet nectar",
        travel_need="At dusk the meadow filled with quiet air for new wings to learn in.",
        tags={"meadow", "flowers"},
    ),
}

OFFICIALS = {
    "owl": Official(
        id="owl",
        kind="owl",
        label="Orrin the Owl",
        voice="deep and calm",
        visa_material="a pale bark card",
        visa_mark="a round plum-stamp",
        helper_text="I can write a visa for careful travelers,",
        tags={"owl", "visa"},
    ),
    "turtle": Official(
        id="turtle",
        kind="turtle",
        label="Tula the Turtle",
        voice="slow and kind",
        visa_material="a smooth leaf pass",
        visa_mark="a berry-red stamp",
        helper_text="A visa takes a little time, but it keeps the crossing gentle,",
        tags={"turtle", "visa"},
    ),
    "beaver": Official(
        id="beaver",
        kind="beaver",
        label="Bram the Beaver",
        voice="busy and cheerful",
        visa_material="a flat willow ticket",
        visa_mark="a muddy paw mark",
        helper_text="No one hurries across my crossing without a visa,",
        tags={"beaver", "visa"},
    ),
}

METHODS = {
    "walk_bridge": Method(
        id="walk_bridge",
        sense=3,
        travel_mode="walk carefully across",
        requires_wings=False,
        safe_without_wings=True,
        success_text="With the visa tucked safely under one wing, {hero} crossed the border the careful way and did not slip at all",
        fail_text="{hero} tried to cross before being ready, and the path felt too wobbly for such a small crawling body",
        qa_text="crossed the border carefully with the visa",
        tags={"travel", "visa"},
    ),
    "ride_ferry": Method(
        id="ride_ferry",
        sense=3,
        travel_mode="ride the little ferry across",
        requires_wings=False,
        safe_without_wings=True,
        success_text="The ferryman checked the visa, nodded, and carried {hero} smoothly over the water",
        fail_text="Without the proper wait, the ferry keeper shook his head and sent {hero} back to shore",
        qa_text="rode the ferry after the visa was checked",
        tags={"travel", "visa", "ferry"},
    ),
    "fly_over": Method(
        id="fly_over",
        sense=3,
        travel_mode="fly over the border",
        requires_wings=True,
        safe_without_wings=False,
        success_text="{hero} lifted into the bright air, visa tied in a ribbon pouch, and flew over the border with new wings",
        fail_text="{hero} had no wings yet, so flying was only a wish and not a real plan",
        qa_text="flew over the border with new wings and a visa",
        tags={"travel", "wings", "visa"},
    ),
    "sneak_under": Method(
        id="sneak_under",
        sense=1,
        travel_mode="sneak under the sign",
        requires_wings=False,
        safe_without_wings=False,
        success_text="{hero} slipped under the sign unseen",
        fail_text="{hero} tried to sneak under the sign, but the border only felt scarier and less safe",
        qa_text="tried to sneak under the sign",
        tags={"travel"},
    ),
}

HELPER_KINDS = {
    "snail": {"type": "snail", "label": "snail", "tags": {"snail", "friend"}},
    "ladybug": {"type": "ladybug", "label": "ladybug", "tags": {"ladybug", "friend"}},
    "duckling": {"type": "duck", "label": "duckling", "tags": {"duck", "friend"}},
}

HERO_NAMES = ["Pip", "Mimi", "Toto", "Lulu", "Nico", "Poppy", "Bean", "Clover"]
HELPER_NAMES = ["Moss", "Dot", "Pebble", "Sunny", "Berry", "Skiff"]

KNOWLEDGE = {
    "visa": [
        (
            "What is a visa?",
            "A visa is a special paper or pass that says you are allowed to travel into a place. It helps the people at the border know who may come through."
        )
    ],
    "caterpillar": [
        (
            "What does a caterpillar become?",
            "A caterpillar can change into a butterfly or moth. First it rests inside a chrysalis, and later it comes out with wings."
        )
    ],
    "butterfly": [
        (
            "Why are butterfly wings useful?",
            "Butterfly wings help a butterfly fly over water, grass, and flowers. Flying can make a trip easier than crawling."
        )
    ],
    "chrysalis": [
        (
            "What is a chrysalis?",
            "A chrysalis is the quiet case where a caterpillar changes. It may look still from outside, but a big change is happening inside."
        )
    ],
    "foreshadow": [
        (
            "What is a warning sign in a story?",
            "A warning sign is a clue that hints something important may happen later. It helps readers notice a coming change before it arrives."
        )
    ],
    "border": [
        (
            "Why do travelers stop at a border?",
            "A border is the edge between one place and another. Travelers may stop there to be checked so the crossing stays orderly and safe."
        )
    ],
    "owl": [
        (
            "Why are owls often shown as careful helpers in stories?",
            "Owls are often shown as careful because they watch quietly and notice details. That makes them good story characters for giving wise advice."
        )
    ],
    "turtle": [
        (
            "Why might a turtle remind someone to be patient?",
            "Turtles move slowly and steadily. In stories, that can make them a gentle symbol of patience."
        )
    ],
    "beaver": [
        (
            "What is a beaver good at?",
            "A beaver is good at building with wood and mud. In stories, that makes a beaver a believable keeper of bridges and crossings."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "visa",
    "border",
    "caterpillar",
    "chrysalis",
    "butterfly",
    "foreshadow",
    "owl",
    "turtle",
    "beaver",
]


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def border_supports_method(border_id: str, method_id: str) -> bool:
    if method_id == "ride_ferry":
        return border_id == "lily_ferry"
    if method_id == "walk_bridge":
        return border_id in {"reed_bridge", "pebble_gate"}
    if method_id == "fly_over":
        return True
    if method_id == "sneak_under":
        return True
    return False


def needs_transformation(method: Method) -> bool:
    return method.requires_wings


def valid_combo(border_id: str, method_id: str) -> bool:
    if method_id not in METHODS or border_id not in BORDERS:
        return False
    method = METHODS[method_id]
    if method.sense < SENSE_MIN:
        return False
    if not border_supports_method(border_id, method_id):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for border_id in sorted(BORDERS):
        for destination_id in sorted(DESTINATIONS):
            for method_id in sorted(METHODS):
                if valid_combo(border_id, method_id):
                    combos.append((border_id, destination_id, method_id))
    return combos


def explain_method_rejection(border_id: str, method_id: str) -> str:
    if method_id not in METHODS:
        return f"(No story: unknown travel method '{method_id}'.)"
    if METHODS[method_id].sense < SENSE_MIN:
        return (
            f"(No story: method '{method_id}' is refused because it is not a careful plan. "
            f"This world prefers safe, honest crossings over sneaking.)"
        )
    if not border_supports_method(border_id, method_id):
        return (
            f"(No story: method '{method_id}' does not fit {BORDERS[border_id].label}. "
            f"Use the ferry only at Lily Ferry, or choose a method that suits that border.)"
        )
    return "(No story: that travel plan is not reasonable here.)"


def outcome_of(params: StoryParams) -> str:
    method = METHODS[params.method]
    return "transformed" if method.requires_wings else "careful_crossing"


def predict_crossing(world: World, method: Method) -> dict:
    sim = world.copy()
    sim.facts["attempted_crossing"] = True
    if method.requires_wings:
        sim.get("hero").meters["wings"] = 0.0
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("border").meters["risk"],
        "fear": sim.get("hero").memes["fear"],
        "possible_now": not method.requires_wings and method.safe_without_wings,
    }


def introduce(world: World, hero: Entity, helper: Entity, destination: Destination) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In a clover patch beside the marsh lived {hero.name}, a small green caterpillar, "
        f"and {helper.name}, {helper.phrase}. {destination.travel_need}"
    )
    world.say(
        f"{hero.name} longed to visit {destination.label}, where {destination.bloom} opened wide "
        f"and the air smelled like {destination.nectar}."
    )


def foreshadow(world: World, border: Border) -> None:
    world.say(border.foreshadow)
    world.say(
        f"Near the crossing stood a sign that read, \"{border.sign_text}.\""
    )
    world.facts["foreshadowed"] = True


def desire(world: World, hero: Entity, destination: Destination) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'"I want to go today," said {hero.name}. "I can almost taste the {destination.nectar} already."'
    )


def warning(world: World, hero: Entity, helper: Entity, official: Official, border: Border, method: Method) -> None:
    pred = predict_crossing(world, method)
    helper.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{helper.name} looked at the sign and then at the water. "{border.hazard.capitalize()}," '
        f'{helper.pronoun()} said. "You need a visa first."'
    )
    if pred["risk"] >= THRESHOLD or method.requires_wings:
        world.say(
            f'"And maybe," {helper.name} added softly, "you are not quite ready for that crossing yet."'
        )
    world.say(
        f'At the little desk by the path sat {official.label}, whose voice was {official.voice}.'
    )
    world.say(
        f'"{official.helper_text} {official.label} said. "Careful travelers arrive best."'
    )


def visit_office(world: World, hero: Entity, official: Official) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.name} crept to the desk, where {official.label} wrote on {official.visa_material} "
        f"and pressed {official.visa_mark} beside {hero.pronoun('possessive')} name."
    )
    world.say(
        f'"Here is your visa," said {official.label}. "But while the ink dries, rest on this branch."'
    )


def waiting_turn(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["waiting"] += 1
    hero.meters["ready_to_change"] += 1
    hero.memes["sleepy"] += 1
    helper.memes["watchful"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.name} wanted to fuss, but instead {hero.pronoun()} tucked in close to the branch. "
        f'"I feel strange," {hero.pronoun()} whispered. "Sleepy, and still, and full all at once."'
    )
    world.say(
        f'"Then be still," said {helper.name}. "Sometimes waiting is not empty. Sometimes it is work you cannot see."'
    )


def transformation(world: World, hero: Entity) -> None:
    if hero.meters["wings"] < THRESHOLD:
        propagate(world, narrate=False)
    if hero.meters["wings"] < THRESHOLD:
        raise StoryError("(Story logic error: the hero never transformed.)")
    world.say(
        "The branch rocked once in the afternoon light. When the quiet shell opened, "
        f"{hero.name} was not a crawling caterpillar anymore."
    )
    world.say(
        f"Out stepped a butterfly with soft new wings, blinking at the wide bright world."
    )
    world.say(
        f'"My waiting was changing me," said {hero.name}.'
    )


def crossing(world: World, hero: Entity, helper: Entity, border: Border, method: Method, destination: Destination) -> None:
    world.facts["attempted_crossing"] = True
    propagate(world, narrate=False)
    if method.requires_wings and hero.meters["wings"] < THRESHOLD:
        raise StoryError("(No story: this method requires wings, but the hero did not transform.)")
    world.say(
        f"{helper.name} smiled and tucked the visa into a tiny ribbon pouch."
    )
    world.say(method.success_text.format(hero=hero.name) + ".")
    if border.id == "reed_bridge":
        world.say(
            f"Below, the marsh water made silver ripples, but the crossing no longer looked frightening."
        )
    elif border.id == "lily_ferry":
        world.say(
            f"The pond shone like a bowl of blue glass while the lily ferry glided to the far bank."
        )
    else:
        world.say(
            f"The stream kept laughing against the stones, but the path beyond the arch was bright and sure."
        )
    world.say(
        f"Soon {hero.name} reached {destination.label}, where {destination.bloom} swayed and every blossom seemed to welcome the new traveler."
    )
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1


def ending(world: World, hero: Entity, helper: Entity, official: Official, method: Method) -> None:
    world.say(
        f'"Now I know," said {hero.name}. "The visa did not only open the border. The waiting opened me."'
    )
    world.say(
        f'"That is why we do things carefully," said {official.label}.'
    )
    if method.requires_wings:
        world.say(
            f"{helper.name} laughed to see {hero.name} rise and circle once in the evening light, no longer impatient, but proud and gentle with {hero.pronoun('possessive')} new wings."
        )
    else:
        world.say(
            f"{helper.name} walked beside {hero.name}, and the little traveler kept the visa safe in a leaf pocket, proud of crossing the honest way."
        )


def tell(
    border: Border,
    destination: Destination,
    official_cfg: Official,
    method: Method,
    hero_name: str,
    helper_name: str,
    helper_kind: str,
    parent_tone: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="caterpillar",
            label="caterpillar",
            phrase="a small green caterpillar",
            role="hero",
            traits=["hopeful", parent_tone],
            tags={"caterpillar"},
        )
    )
    hero.attrs["display_name"] = hero_name
    helper_def = HELPER_KINDS[helper_kind]
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_def["type"],
            label=helper_def["label"],
            phrase=f"a careful {helper_def['label']}",
            role="helper",
            traits=["careful"],
            tags=set(helper_def["tags"]),
        )
    )
    helper.attrs["display_name"] = helper_name
    official = world.add(
        Entity(
            id="official",
            kind="character",
            type=official_cfg.kind,
            label=official_cfg.label,
            phrase=official_cfg.label,
            role="official",
            traits=["patient"],
            tags=set(official_cfg.tags),
        )
    )
    border_ent = world.add(
        Entity(
            id="border",
            kind="thing",
            type="border",
            label=border.label,
            phrase=border.crossing,
            role="border",
            tags=set(border.tags) | {"border"},
        )
    )
    visa = world.add(
        Entity(
            id="visa",
            kind="thing",
            type="document",
            label="visa",
            phrase="a tiny visa",
            role="visa",
            tags={"visa"},
        )
    )

    hero.name = hero_name  # type: ignore[attr-defined]
    helper.name = helper_name  # type: ignore[attr-defined]

    introduce(world, hero, helper, destination)
    foreshadow(world, border)
    world.para()
    desire(world, hero, destination)
    warning(world, hero, helper, official_cfg, border, method)
    visit_office(world, hero, official_cfg)
    world.para()
    waiting_turn(world, hero, helper)
    transformation(world, hero)
    visa.meters["ready"] += 1
    world.para()
    crossing(world, hero, helper, border, method, destination)
    ending(world, hero, helper, official, method)

    world.facts.update(
        hero=hero,
        helper=helper,
        official=official,
        official_cfg=official_cfg,
        border_cfg=border,
        destination_cfg=destination,
        method=method,
        visa=visa,
        transformed=hero.meters["wings"] >= THRESHOLD,
        outcome=outcome_of(
            StoryParams(
                border=border.id,
                destination=destination.id,
                official=official_cfg.id,
                method=method.id,
                hero_name=hero_name,
                helper_name=helper_name,
                helper_kind=helper_kind,
                parent_tone=parent_tone,
            )
        ),
        predicted_risk=world.facts.get("predicted_risk", 0),
    )
    return world


def display_name(ent: Entity) -> str:
    return str(ent.attrs.get("display_name", ent.id))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    border = f["border_cfg"]
    destination = f["destination_cfg"]
    method = f["method"]
    hero = display_name(f["hero"])
    helper = display_name(f["helper"])
    return [
        'Write a gentle animal story for a 3-to-5-year-old that includes the word "visa", uses dialogue, and ends with a real transformation.',
        f"Tell a story about a caterpillar named {hero} who wants to reach {destination.label}, but must stop at {border.label} for a visa first.",
        f"Write a story with foreshadowing where {helper} warns that waiting matters, and later the wait changes the traveler in a way that makes the journey possible by {method.travel_mode}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = display_name(f["hero"])
    helper = display_name(f["helper"])
    official = f["official_cfg"]
    border = f["border_cfg"]
    destination = f["destination_cfg"]
    method = f["method"]
    transformed = f["transformed"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero}, a little caterpillar, and {helper}, the careful friend who stayed nearby. {official.label} also helped by making the visa for the crossing."
        ),
        (
            f"Why did {hero} want to travel?",
            f"{hero} wanted to reach {destination.label}, where {destination.bloom} grew and the air smelled like {destination.nectar}. That place promised something beautiful ahead, so the trip mattered to {hero}."
        ),
        (
            f"Why did {helper} say {hero} should not rush across {border.label}?",
            f"{helper} saw that {border.hazard} and reminded {hero} that travelers needed a visa. The warning also hinted that {hero} was not quite ready for the crossing yet."
        ),
        (
            "What was the foreshadowing in the story?",
            f"The swaying crossing, the border sign, and {hero}'s strange sleepy feeling all hinted that an important change was coming. Those clues made the later transformation feel prepared instead of sudden."
        ),
    ]
    if transformed:
        qa.append(
            (
                f"What changed while {hero} was waiting?",
                f"While waiting for the visa ink to dry, {hero} rested and changed from a caterpillar into a butterfly. The waiting time mattered because it gave the hidden transformation time to happen."
            )
        )
    qa.append(
        (
            f"How did {hero} finally cross the border?",
            f"{hero} {method.qa_text}. The story shows that the safe trip happened only after patience, help, and the right moment came together."
        )
    )
    qa.append(
        (
            "What did the ending prove had changed?",
            f"In the ending, {hero} was no longer only eager and impatient. {hero} had become both a new creature and a more patient traveler, so the border felt open instead of frightening."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"visa", "border", "caterpillar", "chrysalis", "butterfly", "foreshadow"}
    official_cfg = world.facts["official_cfg"]
    if official_cfg.id in KNOWLEDGE:
        tags.add(official_cfg.id)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        border="reed_bridge",
        destination="blossom_garden",
        official="owl",
        method="fly_over",
        hero_name="Pip",
        helper_name="Moss",
        helper_kind="snail",
        parent_tone="eager",
    ),
    StoryParams(
        border="lily_ferry",
        destination="sunny_orchard",
        official="turtle",
        method="ride_ferry",
        hero_name="Mimi",
        helper_name="Dot",
        helper_kind="ladybug",
        parent_tone="hopeful",
    ),
    StoryParams(
        border="pebble_gate",
        destination="moonlit_meadow",
        official="beaver",
        method="walk_bridge",
        hero_name="Bean",
        helper_name="Sunny",
        helper_kind="duckling",
        parent_tone="curious",
    ),
]


ASP_RULES = r"""
% valid combinations: destination is always fine; the gate is about border+method.
sensible(M) :- method(M), sense(M, S), sense_min(K), S >= K.
supports(B, ride_ferry) :- border(B), B = lily_ferry.
supports(B, walk_bridge) :- border(B), B = reed_bridge.
supports(B, walk_bridge) :- border(B), B = pebble_gate.
supports(B, fly_over) :- border(B).
supports(B, sneak_under) :- border(B).

valid(B, D, M) :- border(B), destination(D), method(M), sensible(M), supports(B, M).

% outcome: methods needing wings produce a transformed crossing; others are careful crossings.
outcome(transformed) :- chosen_method(M), requires_wings(M).
outcome(careful_crossing) :- chosen_method(M), not requires_wings(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for border_id in sorted(BORDERS):
        lines.append(asp.fact("border", border_id))
    for destination_id in sorted(DESTINATIONS):
        lines.append(asp.fact("destination", destination_id))
    for method_id, method in sorted(METHODS.items()):
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.requires_wings:
            lines.append(asp.fact("requires_wings", method_id))
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
    return sorted(name for (name,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_method", params.method)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {m.id for m in sensible_methods()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible methods match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible methods: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify smoke test: empty story.)")
        emit(sample, trace=False, qa=False, header="### verify smoke sample")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a caterpillar, a visa, patient dialogue, and a transformation."
    )
    ap.add_argument("--border", choices=sorted(BORDERS))
    ap.add_argument("--destination", choices=sorted(DESTINATIONS))
    ap.add_argument("--official", choices=sorted(OFFICIALS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--helper-kind", choices=sorted(HELPER_KINDS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.border and args.method and not valid_combo(args.border, args.method):
        raise StoryError(explain_method_rejection(args.border, args.method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        border_id = args.border or "reed_bridge"
        raise StoryError(explain_method_rejection(border_id, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.border is None or combo[0] == args.border)
        and (args.destination is None or combo[1] == args.destination)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    border_id, destination_id, method_id = rng.choice(sorted(combos))
    official_id = args.official or rng.choice(sorted(OFFICIALS))
    helper_kind = args.helper_kind or rng.choice(sorted(HELPER_KINDS))
    hero_name = rng.choice(HERO_NAMES)
    helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    parent_tone = rng.choice(["eager", "hopeful", "curious", "restless"])
    return StoryParams(
        border=border_id,
        destination=destination_id,
        official=official_id,
        method=method_id,
        hero_name=hero_name,
        helper_name=helper_name,
        helper_kind=helper_kind,
        parent_tone=parent_tone,
    )


def generate(params: StoryParams) -> StorySample:
    if params.border not in BORDERS:
        raise StoryError(f"(No story: unknown border '{params.border}'.)")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(No story: unknown destination '{params.destination}'.)")
    if params.official not in OFFICIALS:
        raise StoryError(f"(No story: unknown official '{params.official}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")
    if params.helper_kind not in HELPER_KINDS:
        raise StoryError(f"(No story: unknown helper kind '{params.helper_kind}'.)")
    if not valid_combo(params.border, params.method):
        raise StoryError(explain_method_rejection(params.border, params.method))

    world = tell(
        border=BORDERS[params.border],
        destination=DESTINATIONS[params.destination],
        official_cfg=OFFICIALS[params.official],
        method=METHODS[params.method],
        hero_name=params.hero_name,
        helper_name=params.helper_name,
        helper_kind=params.helper_kind,
        parent_tone=params.parent_tone,
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
        print(asp_program("", "#show sensible/1.\n#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (border, destination, method) combos:\n")
        for border_id, destination_id, method_id in combos:
            print(f"  {border_id:11} {destination_id:15} {method_id}")
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
            header = f"### {p.hero_name}: {p.method} at {p.border} toward {p.destination}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
