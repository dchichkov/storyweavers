#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/secure_mess_moral_value_cautionary_rhyming_story.py
==============================================================================

A standalone story world about carrying something messy to a cozy hideout.

Tiny domain:
- A child wants to bring a messy thing to a fun little place.
- A wiser helper warns that the container is not secure enough for the route.
- Sometimes the warning prevents the accident.
- Sometimes the child rushes, a spill happens, and a grown-up helps clean it.
- In the saddest branch, the mess grows too big and play must stop for the day.

The style aims for child-facing, concrete, lightly rhyming prose with a clear
moral: secure the lid, slow your feet, and ask for help before a small problem
turns into a big mess.

Run it
------
    python storyworlds/worlds/gpt-5.4/secure_mess_moral_value_cautionary_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/secure_mess_moral_value_cautionary_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/secure_mess_moral_value_cautionary_rhyming_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/secure_mess_moral_value_cautionary_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4/secure_mess_moral_value_cautionary_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
BOLD_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "thoughtful", "gentle"}


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
    closable: bool = False
    secure_ready: bool = False
    messy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Hideout:
    id: str
    label: str
    scene: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    spill_text: str
    stain_text: str
    clean_text: str
    spread: int
    messy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    lid_text: str
    closable: bool
    secure_bonus: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    move_text: str
    warning_text: str
    bump: int
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"carrier", "helper"}]

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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    carrier = world.get("carrier")
    helper = world.get("helper")
    material = world.get("material")
    if material.meters["spilled"] >= THRESHOLD:
        sig = ("spread", material.id)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["mess"] += 1
            carrier.memes["fear"] += 1
            helper.memes["worry"] += 1
            out.append("__mess__")
    if room.meters["mess"] >= THRESHOLD:
        sig = ("play_stop", room.id)
        if sig not in world.fired:
            world.fired.add(sig)
            room.memes["fun_low"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="spread", tag="physical", apply=_r_spread),
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


HIDEOUTS = {
    "fort": Hideout(
        id="fort",
        label="blanket fort",
        scene="a blanket fort with pillows piled high",
        opening="The chairs were cliffs, the blankets were night, and the fort looked warm in the lamplight.",
        ending="the fort glowed calm and snug for the rest of the night",
        tags={"fort"},
    ),
    "nook": Hideout(
        id="nook",
        label="window nook",
        scene="a window nook with a quilt and three soft bears",
        opening="The cushion was a little boat, the quilt was the sea, and the nook felt as snug as snug could be.",
        ending="the nook stayed neat and sweet by the moonlit pane",
        tags={"nook"},
    ),
    "castle": Hideout(
        id="castle",
        label="cardboard castle",
        scene="a cardboard castle with a paper crown",
        opening="The boxes were towers, the rug was the town, and the castle looked fit for a crinkly crown.",
        ending="the castle stood tidy from turret to ground",
        tags={"castle"},
    ),
}

MATERIALS = {
    "glitter_glue": Material(
        id="glitter_glue",
        label="glitter glue",
        phrase="a tub of silver glitter glue",
        spill_text="silver streaks and sticky stars",
        stain_text="sticky and sparkly",
        clean_text="wiped the glitter glue with damp cloths until the silver stopped spreading",
        spread=2,
        messy=True,
        tags={"glitter", "mess"},
    ),
    "blue_paint": Material(
        id="blue_paint",
        label="blue paint",
        phrase="a cup of blue paint",
        spill_text="blue swirls like puddles of sky",
        stain_text="blue and blotchy",
        clean_text="dabbed the blue paint with towels and soapy water before it set",
        spread=3,
        messy=True,
        tags={"paint", "mess"},
    ),
    "berry_jam": Material(
        id="berry_jam",
        label="berry jam",
        phrase="a jar of berry jam",
        spill_text="purple smears and sweet sticky trails",
        stain_text="sticky and purple",
        clean_text="scooped up the berry jam and washed the sticky trail away",
        spread=2,
        messy=True,
        tags={"jam", "mess"},
    ),
    "dry_beads": Material(
        id="dry_beads",
        label="dry beads",
        phrase="a cup of dry beads",
        spill_text="little beads skipping and bouncing",
        stain_text="scattered everywhere",
        clean_text="swept the beads into a pan before tiny feet could slip",
        spread=1,
        messy=True,
        tags={"beads", "mess"},
    ),
}

CONTAINERS = {
    "jar": ContainerCfg(
        id="jar",
        label="jar",
        phrase="a screw-top jar",
        lid_text="twist the lid until it felt snug and secure",
        closable=True,
        secure_bonus=2,
        tags={"lid", "secure"},
    ),
    "snap_box": ContainerCfg(
        id="snap_box",
        label="snap box",
        phrase="a clear snap box",
        lid_text="press the lid until it clicked secure",
        closable=True,
        secure_bonus=1,
        tags={"lid", "secure"},
    ),
    "paper_cup": ContainerCfg(
        id="paper_cup",
        label="paper cup",
        phrase="a paper cup with no lid",
        lid_text="hold it very still, though it could never be secure",
        closable=False,
        secure_bonus=0,
        tags={"open_container"},
    ),
    "bowl": ContainerCfg(
        id="bowl",
        label="bowl",
        phrase="a little bowl",
        lid_text="hold it flat, though it had no lid to secure",
        closable=False,
        secure_bonus=0,
        tags={"open_container"},
    ),
}

ROUTES = {
    "stairs": Route(
        id="stairs",
        label="the stairs",
        move_text="tiptoe up the stairs to the hideout",
        warning_text="stairs bounce little hands and make wobbly things sway",
        bump=2,
        risky=True,
        tags={"stairs"},
    ),
    "toy_hall": Route(
        id="toy_hall",
        label="the toy-strewn hall",
        move_text="hurry through the toy-strewn hall to the hideout",
        warning_text="a hall full of toys can catch a toe and tip a hand",
        bump=2,
        risky=True,
        tags={"hall"},
    ),
    "porch_step": Route(
        id="porch_step",
        label="the porch step",
        move_text="step over the porch step to the hideout",
        warning_text="one high step can jolt a loose thing and send it slant",
        bump=1,
        risky=True,
        tags={"step"},
    ),
    "flat_rug": Route(
        id="flat_rug",
        label="the flat rug",
        move_text="walk across the flat rug to the hideout",
        warning_text="even a flat rug can slosh a loose cup if someone rushes",
        bump=0,
        risky=False,
        tags={"rug"},
    ),
}

FIXES = {
    "mop_and_wash": Fix(
        id="mop_and_wash",
        label="mop and wash",
        sense=3,
        power=3,
        text="came with a basin, a mop, and calm hands, and cleaned the floor before the sticky trail could travel",
        fail="hurried in with a damp rag, but the spreading mess had already slipped under blankets and books",
        qa_text="cleaned the mess with a basin, a mop, and careful washing",
        tags={"cleaning", "adult_help"},
    ),
    "towels_and_pause": Fix(
        id="towels_and_pause",
        label="towels and pause",
        sense=2,
        power=2,
        text="laid down towels, scooped the spill together, and washed the floor in slow careful circles",
        fail="tried towels first, but the mess had already spread too wide and too far",
        qa_text="used towels and slow careful washing to clean the spill",
        tags={"cleaning", "adult_help"},
    ),
    "quick_wipe": Fix(
        id="quick_wipe",
        label="quick wipe",
        sense=1,
        power=1,
        text="gave the spot one quick wipe",
        fail="gave the spot one quick wipe, but the mess only smeared farther",
        qa_text="gave the spill one quick wipe",
        tags={"cleaning"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah"]
TRAITS = ["careful", "curious", "patient", "thoughtful", "quick", "bold"]


@dataclass
class StoryParams:
    hideout: str
    material: str
    container: str
    route: str
    fix: str
    carrier: str
    carrier_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    delay: int = 0
    carrier_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hideout="fort",
        material="glitter_glue",
        container="jar",
        route="stairs",
        fix="mop_and_wash",
        carrier="Tom",
        carrier_gender="boy",
        helper="Lily",
        helper_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        carrier_age=6,
        helper_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        hideout="nook",
        material="blue_paint",
        container="snap_box",
        route="toy_hall",
        fix="towels_and_pause",
        carrier="Mia",
        carrier_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=0,
        carrier_age=5,
        helper_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        hideout="castle",
        material="berry_jam",
        container="jar",
        route="toy_hall",
        fix="towels_and_pause",
        carrier="Noah",
        carrier_gender="boy",
        helper="Ava",
        helper_gender="girl",
        parent="mother",
        trait="quick",
        delay=1,
        carrier_age=6,
        helper_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        hideout="fort",
        material="blue_paint",
        container="snap_box",
        route="stairs",
        fix="mop_and_wash",
        carrier="Ella",
        carrier_gender="girl",
        helper="Lucy",
        helper_gender="girl",
        parent="father",
        trait="patient",
        delay=1,
        carrier_age=5,
        helper_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        hideout="castle",
        material="blue_paint",
        container="jar",
        route="stairs",
        fix="quick_wipe",
        carrier="Max",
        carrier_gender="boy",
        helper="Anna",
        helper_gender="girl",
        parent="mother",
        trait="careful",
        delay=1,
        carrier_age=7,
        helper_age=5,
        relation="siblings",
        trust=2,
    ),
]


def valid_material_container_route(material: Material, container: ContainerCfg, route: Route) -> bool:
    return material.messy and container.closable and route.risky


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def mess_severity(material: Material, container: ContainerCfg, route: Route, delay: int) -> int:
    return material.spread + route.bump + max(0, 1 - container.secure_bonus) + delay


def is_contained(fix: Fix, material: Material, container: ContainerCfg, route: Route, delay: int) -> bool:
    return fix.power >= mess_severity(material, container, route, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, carrier_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > carrier_age
    authority = initial_care(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > BOLD_INIT


def predict_spill(world: World) -> dict:
    sim = world.copy()
    material = sim.get("material")
    _do_trip(sim, material, narrate=False)
    return {
        "spilled": material.meters["spilled"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def _do_trip(world: World, material: Entity, narrate: bool = True) -> None:
    material.meters["spilled"] += 1
    material.meters["lost"] += 1
    propagate(world, narrate=narrate)


def opening_scene(world: World, carrier: Entity, helper: Entity, hideout: Hideout) -> None:
    for kid in (carrier, helper):
        kid.memes["joy"] += 1
    world.say(
        f"{carrier.id} and {helper.id} had built {hideout.scene}. {hideout.opening}"
    )
    world.say(
        f'"Let us make it extra grand," {carrier.id} sang. "A shiny snack and a crafty light will make our hideout bright tonight."'
    )


def choose_material(world: World, carrier: Entity, material: Material, container: ContainerCfg, hideout: Hideout) -> None:
    world.say(
        f"On the table sat {material.phrase} in {container.phrase}. "
        f"{carrier.id} wanted to {ROUTES[world.facts['route_id']].move_text}, all the way to the {hideout.label}."
    )


def tempt(world: World, carrier: Entity, container: ContainerCfg) -> None:
    carrier.memes["bold"] += 1
    world.say(
        f'{carrier.id} reached for it with a grin and a twirl. "I can carry it fast," {carrier.pronoun()} said. '
        f'"I do not need to stop or secure the top before I go ahead."'
    )
    if not container.closable:
        world.say(
            f"But that was just the trouble: {container.phrase} had no lid to hold things tight."
        )


def warn(world: World, helper: Entity, carrier: Entity, route: Route, container: ContainerCfg, parent: Entity) -> None:
    pred = predict_spill(world)
    helper.memes["care"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    secure_line = "The lid is not secure yet" if container.closable else "That cup can never be secure"
    extra = ""
    if helper.memes["care"] >= 6:
        extra = " The warning came soft, but it came out strong and clear."
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "{secure_line}, and {route.warning_text}. '
        f'If it tips, there will be a mess from here to there, and {parent.label_word} will have to stop and care."{extra}'
    )


def back_down(world: World, carrier: Entity, helper: Entity, container: ContainerCfg, parent: Entity) -> None:
    carrier.memes["relief"] += 1
    helper.memes["relief"] += 1
    carrier.memes["bold"] = 0.0
    world.say(
        f'{carrier.id} looked at {helper.id}, then back at the lid. "You are right," {carrier.pronoun()} said. '
        f'"Fast is not best when sticky things ride. We should make it secure before we stride."'
    )
    world.say(
        f"They set the container down by {parent.label_word}'s side and asked for help before taking another stride."
    )


def defy(world: World, carrier: Entity, helper: Entity) -> None:
    carrier.memes["defiance"] += 1
    world.say(
        f'"It will be fine," {carrier.id} said, too quick, too bright, and dashed off with the tub held light.'
    )
    if carrier.attrs.get("relation") == "siblings" and carrier.age > helper.age and helper.memes["trust"] >= 6:
        world.say(
            f"{helper.id} hurried after {carrier.pronoun('object')}, still worried, but trusting for one small beat."
        )


def stumble(world: World, carrier: Entity, material_ent: Entity, material: Material, route: Route) -> None:
    _do_trip(world, material_ent, narrate=True)
    world.say(
        f"Halfway across {route.label}, one bump came, then a sway, then a slip. "
        f"Out flew {material.spill_text}, and down went the drip."
    )
    world.say(
        f"{carrier.id} froze where {carrier.pronoun()} stood. The floor turned {material.stain_text}, and the game no longer felt good."
    )


def call_for_help(world: World, helper: Entity, parent: Entity) -> None:
    helper.memes["brave"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}!" {helper.id} called. "Please come quick, but calm and slow. We made a mess, and we do not know where it may go."'
    )


def rescue(world: World, parent: Entity, fix: Fix, material: Material, hideout: Hideout) -> None:
    material_ent = world.get("material")
    material_ent.meters["spilled"] = 0.0
    room = world.get("room")
    room.meters["mess"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came at once and {fix.text}."
    )
    world.say(
        f'Soon the room could breathe again. "A small mess can grow if feet fly fast," {parent.pronoun()} said. '
        f'"But calm hands and honest calling help it pass."'
    )
    world.say(
        f"After that, {container_secure_line(world)} and they carried things the careful way. Then {hideout.ending}."
    )


def rescue_fail(world: World, parent: Entity, fix: Fix, material: Material) -> None:
    room = world.get("room")
    room.meters["mess"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} came fast and {fix.fail}."
    )
    world.say(
        f"The sticky trail crept under blankets, books, and blocks. For that day, the game had to stop."
    )


def moral_after_clean(world: World, parent: Entity, carrier: Entity, helper: Entity, container: ContainerCfg) -> None:
    for kid in (carrier, helper):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "When something is messy, make it secure before you carry it," '
        f'{parent.pronoun()} said. "Slow feet save fun, and asking for help is brave, not scary."'
    )
    if container.closable:
        world.say(
            f"Together they tried again and learned to {container.lid_text}."
        )


def moral_after_loss(world: World, parent: Entity, carrier: Entity, helper: Entity, container: ContainerCfg) -> None:
    for kid in (carrier, helper):
        kid.memes["lesson"] += 1
        kid.memes["sad"] += 1
    world.say(
        f'{parent.label_word.capitalize()} hugged them both. "You are safe, and that matters most," {parent.pronoun()} said. '
        f'"Still, this is why we secure messy things before we carry them, and why we ask for help before we hurry."'
    )
    if container.closable:
        world.say(
            f"Later, when the floor was finally clear, they practiced how to {container.lid_text}."
        )
    world.say(
        "They did not play in the hideout again that day, but they remembered the lesson in a steady, careful way."
    )


def container_secure_line(world: World) -> str:
    container: ContainerCfg = world.facts["container_cfg"]
    if container.closable:
        return f"they made the {container.label} secure"
    return "they chose a better container with a lid"


def safe_retry(world: World, carrier: Entity, helper: Entity, hideout: Hideout) -> None:
    for kid in (carrier, helper):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"At last they walked, not dashed; they held, not flung. Their careful song was quiet, and their careful song was sung."
    )
    world.say(
        f"Inside the {hideout.label}, they sat knee to knee. The room was neat, the lid was secure, and their play felt light and free."
    )


def tell(
    hideout: Hideout,
    material: Material,
    container: ContainerCfg,
    route: Route,
    fix: Fix,
    carrier_name: str = "Tom",
    carrier_gender: str = "boy",
    helper_name: str = "Lily",
    helper_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    carrier_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    carrier = world.add(Entity(
        id=carrier_name,
        kind="character",
        type=carrier_gender,
        role="carrier",
        traits=["eager"],
        age=carrier_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[trait],
        age=helper_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    material_ent = world.add(Entity(
        id="material",
        type="material",
        label=material.label,
        phrase=material.phrase,
        messy=True,
        tags=set(material.tags),
    ))
    world.add(Entity(
        id="container",
        type="container",
        label=container.label,
        phrase=container.phrase,
        closable=container.closable,
        secure_ready=False,
        tags=set(container.tags),
    ))

    helper.memes["care"] = initial_care(trait)
    helper.memes["trust"] = float(trust)
    carrier.memes["bold"] = BOLD_INIT
    world.facts["route_id"] = route.id

    opening_scene(world, carrier, helper, hideout)
    choose_material(world, carrier, material, container, hideout)

    world.para()
    tempt(world, carrier, container)
    warn(world, helper, carrier, route, container, parent)

    averted = would_avert(relation, carrier_age, helper_age, trait)

    if averted:
        back_down(world, carrier, helper, container, parent)
        world.para()
        moral_after_clean(world, parent, carrier, helper, container)
        safe_retry(world, carrier, helper, hideout)
        outcome = "averted"
    else:
        defy(world, carrier, helper)
        world.para()
        stumble(world, carrier, material_ent, material, route)
        call_for_help(world, helper, parent)
        severity = mess_severity(material, container, route, delay)
        material_ent.meters["severity"] = float(severity)
        contained = is_contained(fix, material, container, route, delay)
        world.para()
        if contained:
            rescue(world, parent, fix, material, hideout)
            moral_after_clean(world, parent, carrier, helper, container)
            safe_retry(world, carrier, helper, hideout)
            outcome = "contained"
        else:
            rescue_fail(world, parent, fix, material)
            moral_after_loss(world, parent, carrier, helper, container)
            outcome = "ruined"

    world.facts.update(
        carrier=carrier,
        helper=helper,
        parent=parent,
        hideout=hideout,
        material_cfg=material,
        container_cfg=container,
        route_cfg=route,
        fix=fix,
        outcome=outcome,
        delay=delay,
        spilled=material_ent.meters["lost"] >= THRESHOLD,
        relation=relation,
    )
    return world


KNOWLEDGE = {
    "secure": [
        (
            "What does secure mean?",
            "Secure means held safely in place so it will not slip, spill, or fall open. A secure lid helps keep messy things inside where they belong.",
        )
    ],
    "mess": [
        (
            "What is a mess?",
            "A mess is when things spill, scatter, or get out of place. Little messes are easier to fix when people stop, stay calm, and clean them early.",
        )
    ],
    "glitter": [
        (
            "Why is glitter glue messy?",
            "Glitter glue is sticky and sparkly, so it can spread onto hands and floors. Once it smears around, it takes patient wiping to clean."
        )
    ],
    "paint": [
        (
            "Why should paint cups have lids or careful hands?",
            "Paint can splash and stain quickly if it tips. A lid or slow careful carrying helps keep the color where you want it."
        )
    ],
    "jam": [
        (
            "Why can jam make a sticky trail?",
            "Jam is thick and sweet, so when it spills it clings to floors and fingers. That is why jars should stay closed when people carry them."
        )
    ],
    "beads": [
        (
            "Why should spilled beads be cleaned up quickly?",
            "Little beads can roll under feet and make someone slip. Sweeping them up fast keeps the floor safer."
        )
    ],
    "stairs": [
        (
            "Why are stairs tricky for carrying messy things?",
            "Stairs make hands bounce and bodies sway. If a lid is loose, that extra movement can turn a wobble into a spill."
        )
    ],
    "adult_help": [
        (
            "When should a child call a grown-up for help with a spill?",
            "A child should call a grown-up when something messy spills and they are not sure how to make it safe. Asking for help early can stop the mess from spreading."
        )
    ],
    "cleaning": [
        (
            "Why is it smart to clean a spill right away?",
            "Cleaning right away can keep a spill from spreading, staining, or making the floor slippery. Quick calm action often saves more work later."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "secure",
    "mess",
    "glitter",
    "paint",
    "jam",
    "beads",
    "stairs",
    "adult_help",
    "cleaning",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    carrier = f["carrier"]
    helper = f["helper"]
    hideout = f["hideout"]
    material = f["material_cfg"]
    route = f["route_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a gentle rhyming cautionary story for ages 3 to 5 that includes the words "secure" and "mess".',
            f"Tell a rhyming story where {carrier.id} wants to carry {material.label} to a {hideout.label}, but {helper.id} warns that the lid is not secure and prevents a mess.",
            f"Write a moral story in rhyme where a child slows down, asks for help, and learns to make a container secure before carrying it across {route.label}.",
        ]
    if outcome == "ruined":
        return [
            f'Write a rhyming cautionary story for ages 3 to 5 that includes the words "secure" and "mess".',
            f"Tell a rhyme about {carrier.id} rushing {material.label} toward a {hideout.label} without making it secure, so a mess spreads and play must stop.",
            f"Write a moral-value story in rhyme where children learn that hurrying with messy things can spoil the game, even though everyone stays safe.",
        ]
    return [
        f'Write a rhyming cautionary story for ages 3 to 5 that includes the words "secure" and "mess".',
        f"Tell a rhyming story where {carrier.id} hurries {material.label} toward a {hideout.label}, makes a mess, and learns to secure the lid and ask for help.",
        f"Write a moral story in rhyme with a warning, a cleanup, and a careful happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier = f["carrier"]
    helper = f["helper"]
    parent = f["parent"]
    hideout = f["hideout"]
    material = f["material_cfg"]
    container = f["container_cfg"]
    route = f["route_cfg"]
    fix = f["fix"]
    relation = f["relation"]
    pair = pair_noun(carrier, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {carrier.id} and {helper.id}, who were playing near a {hideout.label}. Their {parent.label_word} also helped when the problem grew too big for children alone.",
        ),
        (
            f"Why did {carrier.id} want to carry the {material.label}?",
            f"{carrier.id} wanted to take it to the {hideout.label} to make the game feel extra special. The wish to make play grand is what made rushing seem tempting.",
        ),
        (
            f"What warning did {helper.id} give?",
            f"{helper.id} warned that the container was not secure enough for {route.label}. {helper.pronoun().capitalize()} knew a loose top and a bumpy path could quickly turn into a mess.",
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append(
            (
                f"How did the children stop the problem before it started?",
                f"{carrier.id} listened and set the container down instead of dashing off. Then they asked {parent.label_word} for help and learned to make it secure before carrying it.",
            )
        )
        qa.append(
            (
                "What is the lesson at the end?",
                f"The lesson is to slow down with messy things and make the lid secure first. Asking for help early kept the room neat and let the game stay fun.",
            )
        )
    elif outcome == "contained":
        qa.append(
            (
                f"What happened on {route.label}?",
                f"{carrier.id} stumbled and spilled {material.label}, so the floor became {material.stain_text}. The mess started because the child hurried before the container was secure.",
            )
        )
        qa.append(
            (
                f"How did {parent.label_word} fix the problem?",
                f"{parent.label_word.capitalize()} {fix.qa_text}. The calm cleanup stopped the spill from spreading farther and gave the children time to learn a better way.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the room clean, the lid secure, and the children walking carefully back to play. The ending proves they changed because they moved slowly and wisely the second time.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the game have to stop?",
                f"The spill spread under blankets, books, and blocks, so the hideout could not stay cozy or clean. One rushed choice made a bigger mess than a quick wipe could fix.",
            )
        )
        qa.append(
            (
                "What did the children learn from the sad ending?",
                f"They learned that messy things should be made secure before anyone carries them. They also learned that asking for help before hurrying can save the fun.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"secure", "mess"}
    material = f["material_cfg"]
    route = f["route_cfg"]
    fix = f["fix"]
    if "glitter" in material.tags:
        tags.add("glitter")
    if "paint" in material.tags:
        tags.add("paint")
    if "jam" in material.tags:
        tags.add("jam")
    if "beads" in material.tags:
        tags.add("beads")
    if route.id == "stairs":
        tags.add("stairs")
    tags |= set(fix.tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for hideout_id in HIDEOUTS:
        for material_id, material in MATERIALS.items():
            for container_id, container in CONTAINERS.items():
                for route_id, route in ROUTES.items():
                    if valid_material_container_route(material, container, route):
                        combos.append((hideout_id, material_id, container_id, route_id))
    return combos


def explain_rejection(material: Material, container: ContainerCfg, route: Route) -> str:
    if not container.closable:
        return (
            f"(No story: {container.phrase} cannot be made secure, so this world refuses to treat it as a careful carrying plan. "
            f"Pick a closable container like a jar or snap box.)"
        )
    if not route.risky:
        return (
            f"(No story: {route.label} is too calm for this cautionary setup. "
            f"Pick a route with a real wobble, like stairs or a toy-strewn hall.)"
        )
    if not material.messy:
        return "(No story: the chosen material does not make the kind of mess this world models.)"
    return "(No story: this combination does not fit the cautionary mess pattern.)"


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try a calmer cleanup like: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.carrier_age, params.helper_age, params.trait):
        return "averted"
    fix = FIXES[params.fix]
    material = MATERIALS[params.material]
    container = CONTAINERS[params.container]
    route = ROUTES[params.route]
    return "contained" if is_contained(fix, material, container, route, params.delay) else "ruined"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(H, M, C, R) :- hideout(H), material(M), container(C), route(R),
                     messy(M), closable(C), risky(R).

sensible(Fx) :- fix(Fx), sense(Fx, S), sense_min(Min), S >= Min.

% --- outcome model ---------------------------------------------------------
care_now(T)    :- trait(T), careful_trait(T).
init_care(5)   :- trait(T), care_now(T).
init_care(3)   :- trait(T), not care_now(T).

helper_older   :- relation(siblings), carrier_age(CA), helper_age(HA), HA > CA.
bonus(3)       :- helper_older.
bonus(0)       :- not helper_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted        :- helper_older, authority(A), bold_init(BI), A > BI.

severity(SP + RB + Pen + D) :- chosen_material(M), spread(M, SP),
                               chosen_route(R), bump(R, RB),
                               chosen_container(C), secure_penalty(C, Pen),
                               delay(D).

contained      :- chosen_fix(Fx), power(Fx, P), severity(V), P >= V.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(ruined)    :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        if material.messy:
            lines.append(asp.fact("messy", material_id))
        lines.append(asp.fact("spread", material_id, material.spread))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        if container.closable:
            lines.append(asp.fact("closable", container_id))
        lines.append(asp.fact("secure_penalty", container_id, max(0, 1 - container.secure_bonus)))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        if route.risky:
            lines.append(asp.fact("risky", route_id))
        lines.append(asp.fact("bump", route_id, route.bump))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_container", params.container),
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("carrier_age", params.carrier_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_fix = set(asp_sensible())
    python_fix = {f.id for f in sensible_fixes()}
    if clingo_fix == python_fix:
        print(f"OK: sensible fixes match ({sorted(clingo_fix)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_fix)} python={sorted(python_fix)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming cautionary story world about secure lids and messy spills."
    )
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before cleanup")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.container and args.route:
        material = MATERIALS[args.material]
        container = CONTAINERS[args.container]
        route = ROUTES[args.route]
        if not valid_material_container_route(material, container, route):
            raise StoryError(explain_rejection(material, container, route))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.hideout is None or combo[0] == args.hideout)
        and (args.material is None or combo[1] == args.material)
        and (args.container is None or combo[2] == args.container)
        and (args.route is None or combo[3] == args.route)
    ]
    if not combos:
        if args.material and args.container and args.route:
            raise StoryError(explain_rejection(MATERIALS[args.material], CONTAINERS[args.container], ROUTES[args.route]))
        raise StoryError("(No valid combination matches the given options.)")

    hideout_id, material_id, container_id, route_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    carrier, carrier_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=carrier)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    carrier_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        hideout=hideout_id,
        material=material_id,
        container=container_id,
        route=route_id,
        fix=fix_id,
        carrier=carrier,
        carrier_gender=carrier_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        carrier_age=carrier_age,
        helper_age=helper_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"Unknown hideout: {params.hideout}")
    if params.material not in MATERIALS:
        raise StoryError(f"Unknown material: {params.material}")
    if params.container not in CONTAINERS:
        raise StoryError(f"Unknown container: {params.container}")
    if params.route not in ROUTES:
        raise StoryError(f"Unknown route: {params.route}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")

    material = MATERIALS[params.material]
    container = CONTAINERS[params.container]
    route = ROUTES[params.route]
    if not valid_material_container_route(material, container, route):
        raise StoryError(explain_rejection(material, container, route))
    if FIXES[params.fix].sense < SENSE_MIN and outcome_of(params) != "ruined":
        raise StoryError(explain_fix(params.fix))

    world = tell(
        hideout=HIDEOUTS[params.hideout],
        material=material,
        container=container,
        route=route,
        fix=FIXES[params.fix],
        carrier_name=params.carrier,
        carrier_gender=params.carrier_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        carrier_age=params.carrier_age,
        helper_age=params.helper_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (hideout, material, container, route) combos:\n")
        for hideout_id, material_id, container_id, route_id in combos:
            print(f"  {hideout_id:8} {material_id:13} {container_id:9} {route_id}")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
                f"### {p.carrier} & {p.helper}: {p.material} in {p.container} via {p.route} "
                f"({p.hideout}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
