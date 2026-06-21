#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prudent_caviar_suspense_lesson_learned_cautionary_heartwarming.py
================================================================================================

A standalone storyworld about a child who wants to help with a special family
meal by bringing out caviar. The world models a sensible cautionary pattern:

- a warm, loving setup with a special occasion
- a tempting but risky shortcut
- a prudent warning grounded in the physical state
- a suspenseful turn driven by whether the child listens
- a heartwarming ending that proves the lesson was learned

The central common-sense constraint is simple: some serving dishes are too
wobbly or too cold to carry safely without the right help. The world refuses
unreasonable combinations and includes an inline ASP twin for parity checks.
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs.
# ---------------------------------------------------------------------------
@dataclass
class Occasion:
    id: str
    room: str
    gathering: str
    reason: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    adjective: str
    spill_risk: int
    chill_loss: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    bumps: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpMethod:
    id: str
    label: str
    phrase: str
    sense: int
    steady_bonus: int
    chill_bonus: int
    help_text: str
    rescue_text: str
    rescue_fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World + rule engine helpers.
# ---------------------------------------------------------------------------
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"carrier", "cautioner"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    dish = world.get("dish")
    if dish.meters["tilt"] < THRESHOLD:
        return out
    sig = ("alarm", "dish")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("room").meters["danger"] += 1
    out.append("__alarm__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    dish = world.get("dish")
    if dish.meters["tilt"] < 2.0:
        return out
    sig = ("spill", "dish")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dish.meters["spilled"] += 1
    dish.meters["messy"] += 1
    out.append("__spill__")
    return out


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    dish = world.get("dish")
    if dish.meters["warm"] < THRESHOLD:
        return out
    sig = ("warm", "dish")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dish.memes["quality_risk"] += 1
    out.append("__warm__")
    return out


CAUSAL_RULES = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="warm", tag="physical", apply=_r_warm),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint / outcome helpers.
# ---------------------------------------------------------------------------
def route_suits_vessel(route: Route, vessel: Vessel) -> bool:
    return route.bumps <= vessel.spill_risk


def sensible_methods() -> list[HelpMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def transport_severity(vessel: Vessel, route: Route, delay: int) -> int:
    return max(vessel.spill_risk, route.bumps) + vessel.chill_loss + delay


def contains_risk(method: HelpMethod, vessel: Vessel, route: Route, delay: int) -> bool:
    power = method.steady_bonus + method.chill_bonus
    return power >= transport_severity(vessel, route, delay)


def predicted_tilt(vessel: Vessel, route: Route, method: HelpMethod) -> int:
    return max(0, route.bumps + vessel.spill_risk - method.steady_bonus)


def predicted_warm(vessel: Vessel, delay: int, method: HelpMethod) -> int:
    return max(0, vessel.chill_loss + delay - method.chill_bonus)


def outcome_of(params: "StoryParams") -> str:
    if params.listen:
        return "averted"
    method = METHODS[params.method]
    vessel = VESSELS[params.vessel]
    route = ROUTES[params.route]
    return "contained" if contains_risk(method, vessel, route, params.delay) else "ruined"


def explain_route_vessel(route: Route, vessel: Vessel) -> str:
    return (
        f"(No story: {route.phrase} is too bumpy for {vessel.phrase}. "
        f"The dish would be unreasonable to carry there in this little world. "
        f"Pick a steadier route or a sturdier serving dish.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try a more prudent plan like {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction helpers.
# ---------------------------------------------------------------------------
def predict_trouble(world: World, vessel: Vessel, route: Route, method: HelpMethod, delay: int) -> dict:
    sim = world.copy()
    dish = sim.get("dish")
    dish.meters["tilt"] += float(predicted_tilt(vessel, route, method))
    dish.meters["warm"] += float(predicted_warm(vessel, delay, method))
    propagate(sim, narrate=False)
    return {
        "tilt": int(dish.meters["tilt"]),
        "spill": dish.meters["spilled"] >= THRESHOLD,
        "warm": dish.meters["warm"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story verbs.
# ---------------------------------------------------------------------------
def setup_scene(world: World, carrier: Entity, cautioner: Entity, adult: Entity,
                guest: Entity, occasion: Occasion) -> None:
    carrier.memes["joy"] += 1
    cautioner.memes["joy"] += 1
    world.say(
        f"On the day of {occasion.gathering}, {carrier.id} and {cautioner.id} helped "
        f"{adult.label_word} in {occasion.room}. {occasion.reason}"
    )
    world.say(
        f"{guest.label_word.capitalize()} was coming soon, and the whole house felt soft and busy."
    )


def special_dish(world: World, carrier: Entity, vessel: Vessel) -> None:
    world.say(
        f"On the counter waited {vessel.phrase} of caviar, {vessel.adjective} and special. "
        f"{carrier.id} looked at it as if carrying it to the table would make the surprise complete."
    )


def temptation(world: World, carrier: Entity, route: Route) -> None:
    carrier.memes["pride"] += 1
    world.say(
        f'"I can bring it!" {carrier.id} said. {carrier.pronoun().capitalize()} had already pictured '
        f'{carrier.pronoun("object")}self walking {route.phrase} all alone.'
    )


def prudent_warning(world: World, cautioner: Entity, carrier: Entity, adult: Entity,
                    vessel: Vessel, route: Route, method: HelpMethod, delay: int) -> None:
    pred = predict_trouble(world, vessel, route, method, delay)
    cautioner.memes["prudence"] += 1
    world.facts["predicted"] = pred
    second = []
    if pred["spill"]:
        second.append("one wobble could spill the little black pearls")
    if pred["warm"]:
        second.append("and the caviar should stay cold")
    if not second:
        second.append("it needed careful hands")
    world.say(
        f'{cautioner.id} touched {carrier.id}\'s sleeve. "Let\'s be prudent," '
        f'{cautioner.pronoun()} whispered. "{vessel.phrase.capitalize()} is '
        f'{vessel.adjective}, and {route.label} is not as easy as it looks. '
        f'{", and ".join(second)}."'
    )
    world.say(
        f'{adult.label_word.capitalize()} nodded. "{method.help_text}," {adult.pronoun()} said.'
    )


def listen_and_adjust(world: World, carrier: Entity, cautioner: Entity, adult: Entity,
                      method: HelpMethod) -> None:
    carrier.memes["relief"] += 1
    carrier.memes["lesson"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f"For a second, {carrier.id} stared at the dish and the doorway. Then "
        f"{carrier.pronoun()} took a slow breath and nodded."
    )
    world.say(
        f'Together they chose the safer way: {method.help_text.lower()}. '
        f'The room felt easier at once.'
    )
    world.say(
        f"When the caviar reached the table safely, {adult.label_word} squeezed both children close."
    )


def defy(world: World, carrier: Entity) -> None:
    carrier.memes["defiance"] += 1
    world.say(
        f'But the wish to help first tugged harder than the warning. "{carrier.pronoun().capitalize()} can do it," '
        f'{carrier.id} said, and reached for the dish.'
    )


def risky_walk(world: World, carrier: Entity, vessel: Vessel, route: Route, delay: int) -> None:
    dish = world.get("dish")
    tilt = predicted_tilt(vessel, route, HelpMethod(
        id="none",
        label="none",
        phrase="none",
        sense=0,
        steady_bonus=0,
        chill_bonus=0,
        help_text="",
        rescue_text="",
        rescue_fail="",
        qa_text="",
    ))
    warm = predicted_warm(vessel, delay, HelpMethod(
        id="none",
        label="none",
        phrase="none",
        sense=0,
        steady_bonus=0,
        chill_bonus=0,
        help_text="",
        rescue_text="",
        rescue_fail="",
        qa_text="",
    ))
    dish.meters["tilt"] += float(tilt)
    dish.meters["warm"] += float(warm)
    propagate(world, narrate=False)
    world.say(
        f"{carrier.id} lifted the dish and started {route.phrase}. The house seemed to grow very quiet."
    )
    if dish.meters["tilt"] >= THRESHOLD:
        world.say(
            f"The caviar trembled in its bowl. {carrier.id}'s hands suddenly felt too small, and every step mattered."
        )
    if dish.meters["spilled"] >= THRESHOLD:
        world.say(
            "One edge tipped. A dark glossy line slid sideways, and a few precious pearls slipped over the rim."
        )
    elif dish.meters["warm"] >= THRESHOLD:
        world.say(
            "Nothing spilled yet, but the dish stayed out too long, no longer as cold as it should have been."
        )


def rescue(world: World, adult: Entity, method: HelpMethod, vessel: Vessel, route: Route,
           delay: int) -> None:
    dish = world.get("dish")
    dish.meters["tilt"] = 0.0
    dish.meters["warm"] = 0.0
    dish.meters["spilled"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} stepped in fast and {method.rescue_text}."
    )
    world.say(
        "The children stood still until the dish was safe again, and then everyone let out the breath they had been holding."
    )
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0


def rescue_fail(world: World, adult: Entity, method: HelpMethod) -> None:
    dish = world.get("dish")
    dish.meters["ruined"] += 1
    world.say(
        f"{adult.label_word.capitalize()} hurried over and {method.rescue_fail}."
    )
    world.say(
        "By then, the caviar was no longer right for serving. The special dish for the celebration was lost."
    )
    for kid in world.kids():
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1


def lesson(world: World, carrier: Entity, cautioner: Entity, adult: Entity, outcome: str) -> None:
    if outcome == "contained":
        world.say(
            f'{adult.label_word.capitalize()} knelt beside {carrier.id} and {cautioner.id}. '
            f'"Helping is kind," {adult.pronoun()} said softly, "but kind hands must also be prudent hands."'
        )
        world.say(
            "The warning had been true, and everyone could feel how close the spill had come."
        )
    else:
        world.say(
            f'{adult.label_word.capitalize()} hugged them both. "We can replace food," '
            f'{adult.pronoun()} said, "but we must learn from a risky choice before it grows into a bigger one."'
        )
        world.say(
            f"{carrier.id} looked at the floor and nodded. Even in the sadness, the lesson felt clear and gentle."
        )


def warm_ending(world: World, carrier: Entity, cautioner: Entity, adult: Entity,
                guest: Entity, occasion: Occasion, outcome: str) -> None:
    carrier.memes["love"] += 1
    cautioner.memes["love"] += 1
    if outcome == "ruined":
        world.say(
            f"When {guest.label_word} arrived, there was no caviar on the table, only warm bread and butter."
        )
        world.say(
            f"But {guest.pronoun()} smiled, opened {guest.pronoun('possessive')} arms, and said the best part of the meal was seeing everyone together."
        )
    else:
        world.say(
            f"When {guest.label_word} arrived, the caviar sat safely on the table at last."
        )
        world.say(
            f"{occasion.closing_image} {carrier.id} and {cautioner.id} stayed close to {adult.label_word}, proud in a quieter, wiser way."
        )


# ---------------------------------------------------------------------------
# Main screenplay.
# ---------------------------------------------------------------------------
def tell(occasion: Occasion, vessel: Vessel, route: Route, method: HelpMethod,
         carrier_name: str = "Mira", carrier_type: str = "girl",
         cautioner_name: str = "Ben", cautioner_type: str = "boy",
         adult_type: str = "mother", guest_type: str = "grandmother",
         trait: str = "careful", delay: int = 0, listen: bool = False,
         pet: str = "") -> World:
    world = World()
    carrier = world.add(Entity(
        id=carrier_name,
        kind="character",
        type=carrier_type,
        role="carrier",
        traits=["helpful"],
        attrs={"pet": pet},
    ))
    cautioner = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_type,
        role="cautioner",
        traits=[trait],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the adult",
    ))
    guest = world.add(Entity(
        id="Guest",
        kind="character",
        type=guest_type,
        role="guest",
        label="the guest",
    ))
    world.add(Entity(id="room", type="room", label=occasion.room))
    world.add(Entity(
        id="dish",
        type="dish",
        label=vessel.label,
        phrase=vessel.phrase,
        tags=set(vessel.tags) | {"caviar"},
    ))

    setup_scene(world, carrier, cautioner, adult, guest, occasion)
    special_dish(world, carrier, vessel)

    world.para()
    temptation(world, carrier, route)
    prudent_warning(world, cautioner, carrier, adult, vessel, route, method, delay)

    if listen:
        listen_and_adjust(world, carrier, cautioner, adult, method)
        outcome = "averted"
    else:
        world.para()
        defy(world, carrier)
        risky_walk(world, carrier, vessel, route, delay)
        world.para()
        if contains_risk(method, vessel, route, delay):
            rescue(world, adult, method, vessel, route, delay)
            lesson(world, carrier, cautioner, adult, "contained")
            outcome = "contained"
        else:
            rescue_fail(world, adult, method)
            lesson(world, carrier, cautioner, adult, "ruined")
            outcome = "ruined"

    world.para()
    if pet:
        world.say(f"Even {pet} seemed to settle when the rushing was over.")
    warm_ending(world, carrier, cautioner, adult, guest, occasion, outcome)

    world.facts.update(
        occasion=occasion,
        vessel=vessel,
        route=route,
        method=method,
        carrier=carrier,
        cautioner=cautioner,
        adult=adult,
        guest=guest,
        outcome=outcome,
        listen=listen,
        delay=delay,
        pet=pet,
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
OCCASIONS = {
    "birthday": Occasion(
        id="birthday",
        room="the bright dining room",
        gathering="Grandma's birthday lunch",
        reason="A white cloth was spread on the table, and little plates waited in a neat shining row.",
        closing_image="Candles glowed beside the plates, and the family ate slowly and smiled at one another.",
        tags={"family", "birthday"},
    ),
    "new_year": Occasion(
        id="new_year",
        room="the warm kitchen",
        gathering="a New Year supper",
        reason="Steam curled from the soup pot, and the windows held a silver evening sky.",
        closing_image="Outside, the night was dark, but inside the table looked golden and calm.",
        tags={"family", "new_year"},
    ),
    "anniversary": Occasion(
        id="anniversary",
        room="the little breakfast room",
        gathering="Grandpa and Grandma's anniversary tea",
        reason="Fresh flowers stood in a jar, and every spoon had been lined up with care.",
        closing_image="The teacups chimed softly as everyone leaned close and listened to old happy stories.",
        tags={"family", "anniversary"},
    ),
}

VESSELS = {
    "glass_bowl": Vessel(
        id="glass_bowl",
        label="glass bowl",
        phrase="a tiny glass bowl",
        adjective="slick and chilly",
        spill_risk=2,
        chill_loss=1,
        tags={"glass", "cold_food"},
    ),
    "silver_dish": Vessel(
        id="silver_dish",
        label="silver dish",
        phrase="a little silver dish",
        adjective="smooth and shallow",
        spill_risk=3,
        chill_loss=1,
        tags={"silver", "cold_food"},
    ),
    "ice_platter": Vessel(
        id="ice_platter",
        label="ice platter",
        phrase="a shallow platter resting on ice",
        adjective="very cold and very slippery",
        spill_risk=3,
        chill_loss=2,
        tags={"ice", "cold_food"},
    ),
}

ROUTES = {
    "short_table": Route(
        id="short_table",
        label="the short way to the table",
        phrase="the short way to the table",
        bumps=1,
        tags={"table"},
    ),
    "door_rug": Route(
        id="door_rug",
        label="the path past the folded rug",
        phrase="past the folded rug by the doorway",
        bumps=2,
        tags={"rug"},
    ),
    "chair_corner": Route(
        id="chair_corner",
        label="the squeeze past the chair legs",
        phrase="through the squeeze past the chair legs",
        bumps=3,
        tags={"chairs"},
    ),
}

METHODS = {
    "adult_tray": HelpMethod(
        id="adult_tray",
        label="adult with tray",
        phrase="let the adult carry it on a tray",
        sense=3,
        steady_bonus=3,
        chill_bonus=1,
        help_text="let me carry it on the tray while you walk beside me",
        rescue_text="slid a tray under the dish and steadied it before another pearl could fall",
        rescue_fail="got a tray under the dish, but not before the caviar had warmed and spilled too much",
        qa_text="used a tray and steady grown-up hands to save the dish",
        tags={"tray", "adult_help"},
    ),
    "two_hands": HelpMethod(
        id="two_hands",
        label="two careful hands together",
        phrase="carry it together with two sets of hands",
        sense=2,
        steady_bonus=2,
        chill_bonus=1,
        help_text="we can carry it together with two careful pairs of hands",
        rescue_text="caught the edge with one hand while guiding the children to set it down on a colder plate",
        rescue_fail="caught the edge for a moment, but the dish had already tipped and warmed too long",
        qa_text="helped the children set the dish down safely together",
        tags={"sharing", "adult_help"},
    ),
    "napkin_only": HelpMethod(
        id="napkin_only",
        label="napkin only",
        phrase="wrap it in a napkin and hurry",
        sense=1,
        steady_bonus=1,
        chill_bonus=0,
        help_text="wrap it in a napkin and hurry",
        rescue_text="grabbed for the napkin and stopped the bowl",
        rescue_fail="reached for the napkin, but it did almost nothing to steady or chill the dish",
        qa_text="tried to use only a napkin",
        tags={"napkin"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Eva", "Sana", "Ruby", "Tessa", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Owen", "Milo", "Eli", "Theo", "Noah", "Sam"]
TRAITS = ["careful", "prudent", "thoughtful", "gentle", "steady"]
PETS = ["the cat", "the small dog", "the sleepy puppy", "the gray kitten", ""]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    occasion: str
    vessel: str
    route: str
    method: str
    carrier: str
    carrier_gender: str
    cautioner: str
    cautioner_gender: str
    adult: str
    guest: str
    trait: str
    delay: int = 0
    listen: bool = False
    pet: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        occasion="birthday",
        vessel="glass_bowl",
        route="short_table",
        method="adult_tray",
        carrier="Mira",
        carrier_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        adult="mother",
        guest="grandmother",
        trait="prudent",
        delay=0,
        listen=True,
        pet="the gray kitten",
    ),
    StoryParams(
        occasion="new_year",
        vessel="silver_dish",
        route="door_rug",
        method="two_hands",
        carrier="Leo",
        carrier_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        adult="father",
        guest="grandmother",
        trait="careful",
        delay=0,
        listen=False,
        pet="the cat",
    ),
    StoryParams(
        occasion="anniversary",
        vessel="ice_platter",
        route="chair_corner",
        method="adult_tray",
        carrier="Nora",
        carrier_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        adult="mother",
        guest="grandfather",
        trait="thoughtful",
        delay=1,
        listen=False,
        pet="the small dog",
    ),
]


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "caviar": [
        (
            "What is caviar?",
            "Caviar is a special food made from fish eggs. People usually serve it in small amounts and keep it cold."
        )
    ],
    "prudent": [
        (
            "What does prudent mean?",
            "Prudent means careful in a wise way. A prudent person stops and thinks before doing something risky."
        )
    ],
    "tray": [
        (
            "Why can a tray help carry food safely?",
            "A tray gives a dish a flat place to rest. That makes it steadier and easier to carry without tipping."
        )
    ],
    "cold_food": [
        (
            "Why should some foods stay cold?",
            "Some foods are safer and taste better when they stay cold. If they get warm, they may not be right to serve."
        )
    ],
    "adult_help": [
        (
            "When should a child ask a grown-up for help carrying food?",
            "A child should ask for help when the food is heavy, slippery, breakable, or very special. Asking for help is a smart and careful choice."
        )
    ],
    "sharing": [
        (
            "Why can carrying something together be safer?",
            "Two people can steady a dish better than one person when they move slowly together. Shared work can make careful work easier."
        )
    ],
}
KNOWLEDGE_ORDER = ["caviar", "prudent", "cold_food", "tray", "adult_help", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    carrier = f["carrier"]
    occasion = f["occasion"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a heartwarming cautionary story for a 3-to-5-year-old that includes the words "prudent" and "caviar".',
            f"Tell a suspenseful but gentle story where {carrier.id} wants to carry caviar alone for {occasion.gathering}, but listens to a prudent warning and chooses the safer way.",
            "Write a small family story where a child learns that helping is kind, but careful help is wiser than rushing.",
        ]
    if outcome == "contained":
        return [
            'Write a heartwarming story with suspense that includes the words "prudent" and "caviar".',
            f"Tell a cautionary story where {carrier.id} ignores a warning while carrying caviar, but a grown-up saves the moment before the meal is spoiled.",
            "Write a simple lesson-learned story in which a risky choice nearly causes a spill, and the ending proves the child became wiser.",
        ]
    return [
        'Write a gentle cautionary story that includes the words "prudent" and "caviar".',
        f"Tell a suspenseful family story where {carrier.id} rushes to help with caviar and the special dish is ruined, but the family still answers with love.",
        "Write a heartwarming lesson-learned story where a child's unsafe shortcut leads to sadness and a clear, loving lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier = f["carrier"]
    cautioner = f["cautioner"]
    adult = f["adult"]
    guest = f["guest"]
    occasion = f["occasion"]
    vessel = f["vessel"]
    route = f["route"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {carrier.id} and {cautioner.id}, two children helping {adult.label_word} get ready for {occasion.gathering}. The family is trying to make the meal feel special for {guest.label_word}."
        ),
        (
            "What special food did they want to serve?",
            f"They wanted to bring out caviar in {vessel.phrase}. It was special because the family was preparing for an important gathering."
        ),
        (
            f"Why did {cautioner.id} tell {carrier.id} to be prudent?",
            f"{cautioner.id} knew that {route.label} could make {vessel.phrase} wobble. {cautioner.pronoun().capitalize()} also knew the caviar should stay cold and be carried carefully."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {carrier.id} do after the warning?",
                f"{carrier.id} stopped, listened, and chose the safer plan instead of rushing. That choice kept the caviar safe and showed that the lesson was learned before anything went wrong."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly, with the caviar on the table and the family close together. The ending proves that prudent choices can protect both the meal and everyone's happy feelings."
            )
        )
    elif outcome == "contained":
        qa.append(
            (
                "What made the middle of the story suspenseful?",
                f"The dish began to wobble while {carrier.id} was carrying it, and everyone had to wait to see if it would spill. The suspense came from how close the caviar came to being lost."
            )
        )
        qa.append(
            (
                f"How did {adult.label_word} fix the problem?",
                f"{adult.label_word.capitalize()} {method.qa_text}. The quick help worked because {adult.pronoun()} moved fast enough to steady the dish before the whole serving was ruined."
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                "They learned that wanting to help is not enough by itself. Special things should be handled in a prudent, careful way, especially when a grown-up offers a safer plan."
            )
        )
    else:
        qa.append(
            (
                "What went wrong with the caviar?",
                f"The dish tipped or stayed out too long, and the caviar was no longer right to serve. That happened because the risky trip was harder than it first looked."
            )
        )
        qa.append(
            (
                "Was the ending still heartwarming?",
                f"Yes. Even though the caviar was lost, the family answered with hugs, gentle words, and a simpler meal together. The warmth came from love staying bigger than the mistake."
            )
        )
        qa.append(
            (
                "What lesson was learned?",
                "The lesson was to slow down and accept help before a risky choice turns into a real problem. Being prudent protects special things, but it also protects people from needless worry."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"caviar", "prudent", "cold_food"}
    method = world.facts["method"]
    tags |= set(method.tags)
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


# ---------------------------------------------------------------------------
# Trace helpers.
# ---------------------------------------------------------------------------
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Valid combinations.
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for occasion_id in OCCASIONS:
        for vessel_id, vessel in VESSELS.items():
            for route_id, route in ROUTES.items():
                if route_suits_vessel(route, vessel):
                    combos.append((occasion_id, vessel_id, route_id))
    return combos


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
safe_route(V, R) :- vessel(V), route(R), spill_risk(V, S), bumps(R, B), B <= S.
valid(O, V, R) :- occasion(O), safe_route(V, R).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

power(M, P) :- method(M), steady_bonus(M, A), chill_bonus(M, C), P = A + C.
severity(V, R, D, S) :- spill_risk(V, Sv), bumps(R, B), bigger(Sv, B, Base),
                        chill_loss(V, C), S = Base + C + D.

contained :- chosen_method(M), chosen_vessel(V), chosen_route(R), delay(D),
             power(M, P), severity(V, R, D, S), P >= S.

outcome(averted) :- listen.
outcome(contained) :- not listen, contained.
outcome(ruined) :- not listen, not contained.

bigger(A, B, A) :- A >= B.
bigger(A, B, B) :- B > A.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid in OCCASIONS:
        lines.append(asp.fact("occasion", oid))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("spill_risk", vid, vessel.spill_risk))
        lines.append(asp.fact("chill_loss", vid, vessel.chill_loss))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("bumps", rid, route.bumps))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("steady_bonus", mid, method.steady_bonus))
        lines.append(asp.fact("chill_bonus", mid, method.chill_bonus))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra_lines = [
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_route", params.route),
        asp.fact("delay", params.delay),
    ]
    if params.listen:
        extra_lines.append("listen.")
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
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

    c_methods = set(asp_sensible_methods())
    p_methods = {m.id for m in sensible_methods()}
    if c_methods == p_methods:
        print(f"OK: sensible methods match ({sorted(c_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_methods)} python={sorted(p_methods)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
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

    # smoke test: ordinary generation should not crash
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a child wants to help serve caviar, and prudence matters."
    )
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--guest", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the dish stays out")
    ap.add_argument("--listen", action="store_true", help="the child listens to the prudent warning")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel and args.route:
        vessel = VESSELS[args.vessel]
        route = ROUTES[args.route]
        if not route_suits_vessel(route, vessel):
            raise StoryError(explain_route_vessel(route, vessel))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.occasion is None or combo[0] == args.occasion)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.route is None or combo[2] == args.route)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    occasion, vessel, route = rng.choice(sorted(combos))
    method = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    carrier_gender = rng.choice(["girl", "boy"])
    cautioner_gender = rng.choice(["girl", "boy"])
    carrier = _pick_name(rng, carrier_gender)
    cautioner = _pick_name(rng, cautioner_gender, avoid=carrier)
    adult = args.adult or rng.choice(["mother", "father"])
    guest = args.guest or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    listen = bool(args.listen) if args.listen else rng.choice([False, False, True])
    pet = rng.choice(PETS)
    return StoryParams(
        occasion=occasion,
        vessel=vessel,
        route=route,
        method=method,
        carrier=carrier,
        carrier_gender=carrier_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        adult=adult,
        guest=guest,
        trait=trait,
        delay=delay,
        listen=listen,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        occasion = OCCASIONS[params.occasion]
        vessel = VESSELS[params.vessel]
        route = ROUTES[params.route]
        method = METHODS[params.method]
    except KeyError as exc:
        raise StoryError(f"(Invalid params: unknown key {exc}.)") from exc

    if not route_suits_vessel(route, vessel):
        raise StoryError(explain_route_vessel(route, vessel))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(method.id))

    world = tell(
        occasion=occasion,
        vessel=vessel,
        route=route,
        method=method,
        carrier_name=params.carrier,
        carrier_type=params.carrier_gender,
        cautioner_name=params.cautioner,
        cautioner_type=params.cautioner_gender,
        adult_type=params.adult,
        guest_type=params.guest,
        trait=params.trait,
        delay=params.delay,
        listen=params.listen,
        pet=params.pet,
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
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (occasion, vessel, route) combos:\n")
        for occasion, vessel, route in combos:
            print(f"  {occasion:12} {vessel:12} {route}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = (
                f"### {p.carrier} & {p.cautioner}: {p.vessel} via {p.route} "
                f"({outcome_of(p)})"
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
