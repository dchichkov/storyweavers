#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spectacular_microphone_lasagne_suspense_misunderstanding_cautionary_space.py
=========================================================================================================

A standalone storyworld about a child on a small moon station who misunderstands
a crackly microphone message during a spectacular sky event. The misunderstanding
pulls the child toward a dangerous hatch, a careful companion or calm grown-up
intervenes, and the story ends with a safer way to enjoy the space adventure.

Run it
------
python storyworlds/worlds/gpt-5.4/spectacular_microphone_lasagne_suspense_misunderstanding_cautionary_space.py
python storyworlds/worlds/gpt-5.4/spectacular_microphone_lasagne_suspense_misunderstanding_cautionary_space.py --event meteor_shower --target rover_bay
python storyworlds/worlds/gpt-5.4/spectacular_microphone_lasagne_suspense_misunderstanding_cautionary_space.py --target pantry
python storyworlds/worlds/gpt-5.4/spectacular_microphone_lasagne_suspense_misunderstanding_cautionary_space.py --all
python storyworlds/worlds/gpt-5.4/spectacular_microphone_lasagne_suspense_misunderstanding_cautionary_space.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/spectacular_microphone_lasagne_suspense_misunderstanding_cautionary_space.py --verify
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
BOLDNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    dangerous: bool = False
    sealed: bool = True
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


@dataclass
class SpaceEvent:
    id: str
    sky: str
    call: str
    glow: str
    safe_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishear:
    id: str
    actual: str
    mistaken: str
    lead: str
    object_phrase: str
    plausible_targets: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    place: str
    action: str
    danger_text: str
    consequence: str
    spread: int = 2
    dangerous: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


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
class SafeView:
    id: str
    phrase: str
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_pressure_drop(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["ajar"] < THRESHOLD or not ent.dangerous:
            continue
        sig = ("pressure_drop", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "station" in world.entities:
            world.get("station").meters["danger"] += 1
            world.get("station").meters["alarm"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [
    Rule(name="pressure_drop", tag="physical", apply=_r_pressure_drop),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_possible(mishear: Mishear, target: Target) -> bool:
    return target.dangerous and target.id in mishear.plausible_targets


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def risk_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= risk_severity(target, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_care(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BOLDNESS_INIT


def predict_alarm(world: World, target_id: str) -> dict:
    sim = world.copy()
    touch_target(sim, sim.get(target_id), narrate=False)
    return {
        "alarm": sim.get("station").meters["alarm"],
        "danger": sim.get("station").meters["danger"],
    }


def touch_target(world: World, target_ent: Entity, narrate: bool = True) -> None:
    target_ent.meters["ajar"] += 1
    target_ent.sealed = False
    propagate(world, narrate=narrate)


EVENTS = {
    "meteor_shower": SpaceEvent(
        id="meteor_shower",
        sky="a meteor shower",
        call="a spectacular meteor shower",
        glow="silver sparks stitched across the black sky",
        safe_place="the round dome window",
        tags={"meteor", "space"},
    ),
    "ring_sunrise": SpaceEvent(
        id="ring_sunrise",
        sky="ring sunrise",
        call="a spectacular ring sunrise",
        glow="gold light slid through Saturn's rings like ribbons",
        safe_place="the high observation dome",
        tags={"rings", "space"},
    ),
    "comet_tail": SpaceEvent(
        id="comet_tail",
        sky="a comet tail",
        call="a spectacular comet tail",
        glow="a blue-white brush of light swept over the stars",
        safe_place="the clear galley viewport",
        tags={"comet", "space"},
    ),
}

MISHEARS = {
    "rover_bay": Mishear(
        id="rover_bay",
        actual='“Wait by the rover bay door,”',
        mistaken='“Wake the rover bay door,”',
        lead="the crackly station microphone chewed the words into something stranger",
        object_phrase="the rover bay button",
        plausible_targets={"rover_bay"},
        tags={"microphone", "misunderstanding"},
    ),
    "airlock": Mishear(
        id="airlock",
        actual='“Meet me by the airlock window,”',
        mistaken='“Open the airlock window,”',
        lead="static popped in the speaker and swallowed the middle of the sentence",
        object_phrase="the airlock panel",
        plausible_targets={"airlock"},
        tags={"microphone", "misunderstanding"},
    ),
    "antenna_hatch": Mishear(
        id="antenna_hatch",
        actual='“Stand near the antenna hatch sign,”',
        mistaken='“Start the antenna hatch,”',
        lead="the tiny microphone fizzed so hard that one word sounded like another",
        object_phrase="the antenna hatch switch",
        plausible_targets={"antenna_hatch"},
        tags={"microphone", "misunderstanding"},
    ),
}

TARGETS = {
    "rover_bay": Target(
        id="rover_bay",
        label="rover bay door",
        the="the rover bay door",
        place="at the rover bay",
        action="reached for the wide silver release button beside the parked moon buggy",
        danger_text="The rover bay opened to the black outside.",
        consequence="Cold air would rush away if that door opened at the wrong time.",
        spread=2,
        dangerous=True,
        tags={"door", "bay", "danger"},
    ),
    "airlock": Target(
        id="airlock",
        label="airlock",
        the="the airlock",
        place="at the airlock hall",
        action="put a hand on the blinking airlock panel",
        danger_text="The airlock separated the warm station from empty space.",
        consequence="Unsealing it without a grown-up could make the whole hall unsafe.",
        spread=3,
        dangerous=True,
        tags={"airlock", "danger"},
    ),
    "antenna_hatch": Target(
        id="antenna_hatch",
        label="antenna hatch",
        the="the antenna hatch",
        place="under the ladder to the antenna deck",
        action="stretched toward the yellow hatch switch",
        danger_text="The hatch led to the windy service deck on the station roof.",
        consequence="It was not a play door, even during a beautiful sky show.",
        spread=2,
        dangerous=True,
        tags={"hatch", "danger"},
    ),
    "pantry": Target(
        id="pantry",
        label="pantry door",
        the="the pantry door",
        place="in the little galley pantry",
        action="reached for the pantry handle",
        danger_text="The pantry only held dinner trays.",
        consequence="Opening it would be ordinary, not dangerous.",
        spread=0,
        dangerous=False,
        tags={"pantry"},
    ),
}

RESPONSES = {
    "seal_switch": Response(
        id="seal_switch",
        sense=3,
        power=3,
        text="slapped the seal switch, wrapped one arm around the child, and watched the red lights turn calm blue again",
        fail="slapped the seal switch, but the warning had already spread through too many parts of the station",
        qa_text="used the seal switch and pulled the hatch secure again",
        tags={"seal_switch", "safety"},
    ),
    "bulkhead": Response(
        id="bulkhead",
        sense=3,
        power=4,
        text="hit the emergency bulkhead button so a thick safety door slid down and blocked the danger",
        fail="hit the emergency bulkhead button, but the station was already sealing section after section",
        qa_text="closed the emergency bulkhead to block off the danger",
        tags={"bulkhead", "safety"},
    ),
    "shout_only": Response(
        id="shout_only",
        sense=1,
        power=1,
        text="only shouted from across the hall until the child finally jumped back",
        fail="shouted from across the hall, but shouting alone was too slow once the alarm had started",
        qa_text="only shouted a warning",
        tags={"warning"},
    ),
}

SAFE_VIEWS = {
    "window": SafeView(
        id="window",
        phrase="the round dome window",
        text="pressed their noses to the thick glass and watched the sky safely from inside",
        tags={"window", "safe_view"},
    ),
    "camera": SafeView(
        id="camera",
        phrase="the roof camera screen",
        text="huddled around the roof camera screen and saw every spark in bright, steady color",
        tags={"camera", "safe_view"},
    ),
    "periscope": SafeView(
        id="periscope",
        phrase="the station periscope",
        text="took turns at the station periscope and gasped at the shining streaks without touching any hatch",
        tags={"periscope", "safe_view"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Ava", "Nora", "Zoe", "Ivy", "Maya", "Tess"]
BOY_NAMES = ["Jax", "Leo", "Milo", "Finn", "Owen", "Eli", "Noah", "Theo"]
TRAITS = ["careful", "curious", "patient", "brave", "eager", "sensible", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for event_id in EVENTS:
        for mishear_id, mishear in MISHEARS.items():
            for target_id, target in TARGETS.items():
                if hazard_possible(mishear, target):
                    combos.append((event_id, mishear_id, target_id))
    return combos


@dataclass
class StoryParams:
    event: str
    mishear: str
    target: str
    response: str
    safe_view: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    meal: str = "lasagne"
    seed: Optional[int] = None


def intro(world: World, a: Entity, b: Entity, event: SpaceEvent, meal: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On Moonbeam Station, {a.id} and {b.id} could hardly sit still because that night "
        f"they were promised {event.call}. Through the curved window, {event.glow}."
    )
    world.say(
        f"In the galley, warm {meal} baked in the oven, filling the station with a cozy smell that made "
        f"the whole metal place feel like home."
    )


def setup_microphone(world: World, a: Entity) -> None:
    a.memes["showoff"] += 1
    world.say(
        f"{a.id} held a toy microphone and whispered like a captain on a famous starship, "
        f'"Crew, get ready for the most spectacular view in space."'
    )


def call_over_intercom(world: World, parent: Entity, mishear: Mishear) -> None:
    world.say(
        f"Then {parent.label_word.capitalize()}'s voice came over the station microphone. "
        f"{mishear.lead}. {parent.pronoun().capitalize()} had really said {mishear.actual}"
    )


def misunderstanding(world: World, a: Entity, mishear: Mishear) -> None:
    a.memes["boldness"] += 1
    world.say(
        f"But {a.id} heard {mishear.mistaken} {a.pronoun().capitalize()} blinked, looked at "
        f"{mishear.object_phrase}, and decided there must be a special job to do before the sky show."
    )


def warn(world: World, b: Entity, a: Entity, target: Target) -> None:
    pred = predict_alarm(world, "target")
    world.facts["predicted_alarm"] = pred["alarm"]
    b.memes["care"] += 1
    extra = ""
    if b.memes["care"] >= 6:
        extra = f" {b.id} took one quick look at the warning stripes and knew it was not a game."
    world.say(
        f'"Wait," said {b.id}. "{target.The} is not for play. {target.consequence}"{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, safe_view: SafeView, event: SpaceEvent, meal: str) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked from the blinking controls to {b.id}'s face, then lowered the toy microphone. "
        f'"Maybe I heard it wrong," {a.pronoun()} admitted.'
    )
    world.say(
        f"They hurried to {event.safe_place} instead. Soon they {safe_view.text}, while "
        f"{parent.label_word} set out hot squares of {meal} on the table."
    )
    world.say(
        f"The sky was still spectacular, but now the best sound in the station was the happy clink of forks "
        f"and the soft, safe buzz of the microphone with its switch turned off."
    )


def defy(world: World, a: Entity, b: Entity, target: Target) -> None:
    a.memes["defiance"] += 1
    world.say(
        f"{a.id} hurried ahead anyway. Before {b.id} could catch up, {a.pronoun()} {target.action}."
    )


def trigger_alarm(world: World, a: Entity, b: Entity, target_ent: Entity, target: Target) -> None:
    touch_target(world, target_ent)
    world.say(
        f"A sharp beep cut through the hall. {target.danger_text} Yellow warning lights began to chase each other along the wall."
    )
    world.say(
        f'"{a.id}!" cried {b.id}. The toy microphone slipped from {a.pronoun("possessive")} hand and clattered on the floor.'
    )


def rescue(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["ajar"] = 0.0
    target_ent.sealed = True
    world.get("station").meters["danger"] = 0.0
    world.get("station").meters["alarm"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running and {response.text}."
    )
    world.say(
        f"In one more breath, the lights stopped racing, and the hall felt warm and still again."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, target: Target) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} knelt between them. "
        f'"A crackly message can fool your ears," {parent.pronoun()} said softly. '
        f'"But space doors and hatches are never guessing games. If you are not sure, stop and ask."'
    )
    world.say(
        f"{a.id} nodded hard. {b.id} leaned close. They both looked at {target.the} in a new, serious way."
    )


def safe_finish(world: World, parent: Entity, a: Entity, b: Entity, safe_view: SafeView, event: SpaceEvent, meal: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Then {parent.label_word} led them to {safe_view.phrase}. Together they {safe_view.text}."
    )
    world.say(
        f"Afterward they ate steaming {meal}, and {a.id} used the toy microphone the right way at last: "
        f'to announce, "All crew may enjoy dessert from inside the station."'
    )


def rescue_fail(world: World, parent: Entity, response: Response, target_ent: Entity) -> None:
    target_ent.meters["ajar"] += 1
    world.get("station").meters["danger"] += 1
    world.get("station").meters["alarm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail}."
    )
    world.say(
        "A heavy safety door boomed down farther down the corridor, and the station computer ordered everyone back to the galley."
    )


def shelter_end(world: World, parent: Entity, a: Entity, b: Entity, event: SpaceEvent, meal: str) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"They waited together behind the sealed galley door while the sky show flashed unseen outside. "
        f"The {meal} went a little cold, and nobody felt like talking for a moment."
    )
    world.say(
        f"At last the station grew quiet again. {parent.label_word.capitalize()} hugged them tight and said that being safe mattered more than seeing every shining streak."
    )
    world.say(
        f"Later they watched a replay of {event.sky} on the wall screen and promised never to touch a hatch or bay control unless a grown-up was right there."
    )


def tell(
    event: SpaceEvent,
    mishear: Mishear,
    target: Target,
    response: Response,
    safe_view: SafeView,
    instigator: str = "Jax",
    instigator_gender: str = "boy",
    cautioner: str = "Lina",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    meal: str = "lasagne",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["eager"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    station = world.add(Entity(
        id="station",
        type="station",
        label="station",
    ))
    target_ent = world.add(Entity(
        id="target",
        type="hatch",
        label=target.label,
        dangerous=target.dangerous,
        sealed=True,
    ))
    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["care"] = initial_care(trait)

    intro(world, a, b, event, meal)
    setup_microphone(world, a)
    world.para()
    call_over_intercom(world, parent, mishear)
    misunderstanding(world, a, mishear)
    warn(world, b, a, target)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        world.para()
        back_down(world, a, b, parent, safe_view, event, meal)
        severity = 0
        contained = True
    else:
        defy(world, a, b, target)
        world.para()
        trigger_alarm(world, a, b, target_ent, target)
        severity = risk_severity(target, delay)
        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            rescue(world, parent, response, target_ent, target)
            lesson(world, parent, a, b, target)
            world.para()
            safe_finish(world, parent, a, b, safe_view, event, meal)
        else:
            rescue_fail(world, parent, response, target_ent)
            shelter_end(world, parent, a, b, event, meal)

    outcome = "averted" if averted else ("contained" if contained else "sealed_off")
    world.facts.update(
        event=event,
        mishear=mishear,
        target_cfg=target,
        response=response,
        safe_view=safe_view,
        instigator=a,
        cautioner=b,
        parent=parent,
        station=station,
        target=target_ent,
        meal=meal,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        touched=target_ent.meters["ajar"] >= THRESHOLD,
        learned=a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "microphone": [
        (
            "What is a microphone?",
            "A microphone is a tool that picks up your voice and makes it louder through a speaker or a radio system."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. That is why it helps to stop and ask questions."
        )
    ],
    "airlock": [
        (
            "What is an airlock?",
            "An airlock is a special small room or doorway that helps keep air inside a space station when people go in or out."
        )
    ],
    "bay": [
        (
            "What is a rover bay?",
            "A rover bay is the place where a moon rover is parked and kept ready. Its big door should only be opened safely by a grown-up."
        )
    ],
    "hatch": [
        (
            "What is a hatch?",
            "A hatch is a strong door on a ship or station. It is not a play door, because it can lead to dangerous places."
        )
    ],
    "safe_view": [
        (
            "Why is it better to watch space through a window or camera?",
            "A thick window or a camera lets you enjoy the view while staying safe inside. In space, the safe place is the best place to look from."
        )
    ],
    "lasagne": [
        (
            "What is lasagne?",
            "Lasagne is a baked pasta dish with soft layers. It comes out warm and can make a whole room smell cozy."
        )
    ],
    "meteor": [
        (
            "What is a meteor shower?",
            "A meteor shower is when many small bits of space rock streak across the sky and glow like quick little lines of light."
        )
    ],
    "rings": [
        (
            "What are Saturn's rings?",
            "Saturn's rings are wide bands of ice and rock that circle the planet. Sunlight can make them shine beautifully."
        )
    ],
    "comet": [
        (
            "What is a comet tail?",
            "A comet tail is a long trail of glowing dust and gas that follows a comet as it moves through space."
        )
    ],
    "seal_switch": [
        (
            "What does a seal switch do?",
            "A seal switch helps lock a space door or hatch closed again so the safe air stays where it belongs."
        )
    ],
    "bulkhead": [
        (
            "What is an emergency bulkhead?",
            "An emergency bulkhead is a strong safety door inside a ship or station. It can close off danger from the rest of the place."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "microphone",
    "misunderstanding",
    "airlock",
    "bay",
    "hatch",
    "safe_view",
    "lasagne",
    "meteor",
    "rings",
    "comet",
    "seal_switch",
    "bulkhead",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young crewmates"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    event = f["event"]
    target = f["target_cfg"]
    meal = f["meal"]
    outcome = f["outcome"]
    base = (
        f'Write a short space adventure for a 3-to-5-year-old that includes the words '
        f'"spectacular," "microphone," and "{meal}", and uses suspense, misunderstanding, and a cautionary ending or lesson.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle moon-station story where {a.id} misunderstands a crackly microphone message about {target.the}, but {b.id} stops the mistake before any alarm starts.",
            f"Write a cozy but suspenseful story about children waiting to see {event.call} and learning to ask a grown-up when a message sounds confusing.",
        ]
    if outcome == "sealed_off":
        return [
            base,
            f"Tell a cautionary space story where {a.id} touches {target.the} after misunderstanding a microphone message, and the station has to seal everyone safely inside.",
            f"Write a suspenseful moon-base story where a beautiful sky event and a warm pan of {meal} are interrupted by an alarm after a child guesses instead of asking.",
        ]
    return [
        base,
        f"Tell a space adventure where {a.id} misunderstands a station microphone message, reaches for {target.the}, and a calm grown-up fixes the danger and teaches a safety lesson.",
        f"Write a child-facing cautionary story that ends with the family safely watching {event.sky} from inside while eating {meal}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    event = f["event"]
    mishear = f["mishear"]
    target = f["target_cfg"]
    response = f["response"]
    safe_view = f["safe_view"]
    meal = f["meal"]
    pair = pair_noun(a, b, f["relation"])
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, on a moon station with their {parent.label_word}. They were waiting for {event.call}."
        ),
        (
            "Why were they excited at the beginning?",
            f"They were excited because the sky outside was going to do something spectacular, and warm {meal} was baking in the galley. The beautiful view and cozy dinner made the station feel special."
        ),
        (
            f"What caused the misunderstanding?",
            f"The station microphone sounded crackly, so {a.id} heard the wrong words. {parent.label_word.capitalize()} really said {mishear.actual}, but {a.id} thought {mishear.mistaken}."
        ),
        (
            f"Why did {b.id} try to stop {a.id}?",
            f"{b.id} knew {target.the} was not part of a game. {target.consequence}"
        ),
    ]
    if f["outcome"] == "averted":
        out.append(
            (
                f"What did {a.id} do when {b.id} warned {a.pronoun('object')}?",
                f"{a.id} stopped, admitted {a.pronoun()} might have heard the message wrong, and went to the safe viewing place instead. Asking would have been safer than guessing, and that is what the story teaches."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended peacefully with the children watching from {safe_view.phrase} and eating {meal}. The ending shows that the adventure could stay spectacular without touching any dangerous controls."
            )
        )
    elif f["outcome"] == "contained":
        body = response.qa_text
        out.append(
            (
                f"What happened when {a.id} touched {target.the}?",
                f"A warning alarm started, and the hall suddenly felt scary. The danger began because {a.id} touched a real station control after misunderstanding the message."
            )
        )
        out.append(
            (
                f"How did {parent.label_word} fix the problem?",
                f"{parent.label_word.capitalize()} came running and {body}. The quick response stopped the danger before it spread farther."
            )
        )
        out.append(
            (
                "What lesson did the children learn?",
                f"They learned that crackly words can trick your ears, but space doors and hatches are never for guessing games. If something sounds unclear, the safe choice is to stop and ask."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended with the family safely watching from {safe_view.phrase} and eating {meal}. The last image proves they could still have a space adventure from inside the station."
            )
        )
    else:
        out.append(
            (
                f"Could {parent.label_word} stop the whole problem right away?",
                f"No. {parent.label_word.capitalize()} reacted fast, but the warning had already forced the station to seal everyone in the galley. That happened because touching {target.the} started a bigger safety problem than one quick shout could solve."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"The family stayed safe, but they missed the first part of the sky show and their {meal} cooled down. Later they watched a replay and promised never to touch a hatch or bay control without a grown-up."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"microphone", "misunderstanding", "safe_view", "lasagne"}
    target = f["target_cfg"]
    response = f["response"]
    event = f["event"]
    if target.id == "airlock":
        tags.add("airlock")
    if target.id == "rover_bay":
        tags.add("bay")
    if target.id == "antenna_hatch":
        tags.add("hatch")
    if response.id == "seal_switch":
        tags.add("seal_switch")
    if response.id == "bulkhead":
        tags.add("bulkhead")
    if event.id == "meteor_shower":
        tags.add("meteor")
    if event.id == "ring_sunrise":
        tags.add("rings")
    if event.id == "comet_tail":
        tags.add("comet")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.dangerous:
            bits.append("dangerous=True")
        if not e.sealed:
            bits.append("sealed=False")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        event="meteor_shower",
        mishear="rover_bay",
        target="rover_bay",
        response="seal_switch",
        safe_view="window",
        instigator="Jax",
        instigator_gender="boy",
        cautioner="Lina",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        meal="lasagne",
    ),
    StoryParams(
        event="ring_sunrise",
        mishear="airlock",
        target="airlock",
        response="bulkhead",
        safe_view="periscope",
        instigator="Mira",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="patient",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        meal="lasagne",
    ),
    StoryParams(
        event="comet_tail",
        mishear="antenna_hatch",
        target="antenna_hatch",
        response="seal_switch",
        safe_view="camera",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Ava",
        cautioner_gender="girl",
        parent="mother",
        trait="brave",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        meal="lasagne",
    ),
    StoryParams(
        event="meteor_shower",
        mishear="airlock",
        target="airlock",
        response="seal_switch",
        safe_view="window",
        instigator="Noah",
        instigator_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        parent="father",
        trait="curious",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        meal="lasagne",
    ),
]


def explain_rejection(mishear: Mishear, target: Target) -> str:
    if not target.dangerous:
        return (
            f"(No story: {target.the} is ordinary, so misunderstanding a microphone message about it does not create real space-station danger. "
            f"Pick a dangerous target like an airlock, rover bay, or antenna hatch.)"
        )
    return (
        f"(No story: the misunderstanding '{mishear.id}' does not sensibly point a child toward {target.the}. "
        f"Choose a target that matches the heard words.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay)
    return "contained" if contained else "sealed_off"


ASP_RULES = r"""
hazard(M, T) :- mishear(M), target(T), dangerous(T), points_to(M, T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(E, M, T) :- event(E), hazard(M, T).

careful_now(T) :- trait(T), careful_trait(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- older_sibling, authority(A), boldness_init(B), A > B.

severity(SP + D) :- chosen_target(T), spread(T, SP), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(sealed_off) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for event_id in EVENTS:
        lines.append(asp.fact("event", event_id))
    for mishear_id, mishear in MISHEARS.items():
        lines.append(asp.fact("mishear", mishear_id))
        for target_id in sorted(mishear.plausible_targets):
            lines.append(asp.fact("points_to", mishear_id, target_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("spread", target_id, target.spread))
        if target.dangerous:
            lines.append(asp.fact("dangerous", target_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_resp, python_resp = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_resp == python_resp:
        print(f"OK: sensible responses match ({sorted(clingo_resp)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_resp)} python={sorted(python_resp)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            args = parser.parse_args([])
            cases.append(resolve_params(args, random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(smoke, trace=False, qa=False, header="SMOKE TEST")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a crackly microphone, a dangerous hatch, a spectacular sky, and a safety lesson."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--mishear", choices=MISHEARS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--safe-view", choices=SAFE_VIEWS, dest="safe_view")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="head start the alarm gets before the grown-up reaches the hatch")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos and sensible responses from clingo")
    ap.add_argument("--verify", action="store_true", help="verify Python/ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target:
        target = TARGETS[args.target]
        if not target.dangerous:
            mishear = MISHEARS[args.mishear] if args.mishear else next(iter(MISHEARS.values()))
            raise StoryError(explain_rejection(mishear, target))
    if args.mishear and args.target:
        mishear = MISHEARS[args.mishear]
        target = TARGETS[args.target]
        if not hazard_possible(mishear, target):
            raise StoryError(explain_rejection(mishear, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.event is None or c[0] == args.event)
        and (args.mishear is None or c[1] == args.mishear)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    event, mishear, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    safe_view = args.safe_view or rng.choice(sorted(SAFE_VIEWS))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        event=event,
        mishear=mishear,
        target=target,
        response=response,
        safe_view=safe_view,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        meal="lasagne",
    )


def _check_params(params: StoryParams) -> None:
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.mishear not in MISHEARS:
        raise StoryError(f"(Unknown mishear: {params.mishear})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.safe_view not in SAFE_VIEWS:
        raise StoryError(f"(Unknown safe_view: {params.safe_view})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_possible(MISHEARS[params.mishear], TARGETS[params.target]):
        raise StoryError(explain_rejection(MISHEARS[params.mishear], TARGETS[params.target]))


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        event=EVENTS[params.event],
        mishear=MISHEARS[params.mishear],
        target=TARGETS[params.target],
        response=RESPONSES[params.response],
        safe_view=SAFE_VIEWS[params.safe_view],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        meal=params.meal,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, mishear, target) combos:\n")
        for event, mishear, target in combos:
            print(f"  {event:13} {mishear:14} {target}")
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
                f"### {p.instigator} & {p.cautioner}: {p.event}, {p.mishear}, {p.target} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
