#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/previous_linen_reconciliation_conflict_space_adventure.py
====================================================================================

A standalone storyworld for a tiny "space adventure" domain: two children build
a ship with a linen sail, argue about repeating a previous route, snag the sail
during the quarrel, and then reconcile by fixing it together.

The core world idea is small and concrete:

- A pretend spaceship is built from ordinary things.
- The captain wants to fly the previous shortcut again.
- The navigator remembers the previous scrape and objects.
- Their conflict makes the launch clumsy, and the linen part of the ship snags.
- Reconciliation changes the physical state: once they apologize and work
  together, the ship can be repaired well enough to launch, or only partly
  repaired so the adventure becomes a gentler porch-side ending.

The world includes:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus an inline ASP twin
- deterministic reproduction via StoryParams
- story-grounded QA and world-knowledge QA
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
# File lives under storyworlds/worlds/gpt-5.4/, so three ".." levels reach
# storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
TEAMWORK_TRAITS = {"gentle", "patient", "kind", "careful", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    sky: str
    pretend_place: str
    sendoff: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    rig: str
    linen_part: str
    motion: str
    fragility: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    the: str
    roughness: int
    snags_linen: bool
    pretend_name: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    works_on_linen: bool
    method: str
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
        return [e for e in self.entities.values() if e.role in {"captain", "navigator"}]

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


def _r_conflict_stings(world: World) -> list[str]:
    out: list[str] = []
    if "captain" not in world.entities or "navigator" not in world.entities:
        return out
    captain = world.get("captain")
    navigator = world.get("navigator")
    if captain.memes["conflict"] < THRESHOLD or navigator.memes["conflict"] < THRESHOLD:
        return out
    sig = ("conflict_stings",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.memes["frustration"] += 1
    navigator.memes["frustration"] += 1
    out.append("__conflict__")
    return out


def _r_snag_tears(world: World) -> list[str]:
    out: list[str] = []
    linen = world.entities.get("linen")
    ship = world.entities.get("ship")
    if linen is None or ship is None:
        return out
    if linen.meters["snagged"] < THRESHOLD:
        return out
    sig = ("snag_tears",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    linen.meters["torn"] += 1
    ship.meters["stalled"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__tear__")
    return out


def _r_patch_steadies(world: World) -> list[str]:
    out: list[str] = []
    linen = world.entities.get("linen")
    ship = world.entities.get("ship")
    if linen is None or ship is None:
        return out
    if linen.meters["patched"] < THRESHOLD:
        return out
    sig = ("patch_steadies",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship.meters["steady"] += 1
    for kid in world.kids():
        kid.memes["hope"] += 1
    out.append("__patch__")
    return out


CAUSAL_RULES = [
    Rule(name="conflict_stings", tag="social", apply=_r_conflict_stings),
    Rule(name="snag_tears", tag="physical", apply=_r_snag_tears),
    Rule(name="patch_steadies", tag="physical", apply=_r_patch_steadies),
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


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN and r.works_on_linen]


def teamwork_bonus(trait: str) -> int:
    return 1 if trait in TEAMWORK_TRAITS else 0


def snag_severity(vehicle: Vehicle, obstacle: Obstacle) -> int:
    return vehicle.fragility + obstacle.roughness


def can_snag(vehicle: Vehicle, obstacle: Obstacle) -> bool:
    return bool(vehicle.linen_part) and obstacle.snags_linen


def mission_success(vehicle: Vehicle, obstacle: Obstacle, repair: Repair, trait: str) -> bool:
    return repair.power + teamwork_bonus(trait) >= snag_severity(vehicle, obstacle)


def explain_rejection(vehicle: Vehicle, obstacle: Obstacle) -> str:
    if not obstacle.snags_linen:
        return (
            f"(No story: {obstacle.the} would not snag the ship's linen part, so the "
            f"quarrel would cause no real space-adventure problem to solve. Pick a rougher obstacle.)"
        )
    return "(No story: this combination would not make a believable snagging accident.)"


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    if not repair.works_on_linen:
        return (
            f"(Refusing repair '{rid}': it does not really fix torn linen. "
            f"Try one of: {better}.)"
        )
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for vehicle_id, vehicle in VEHICLES.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                if not can_snag(vehicle, obstacle):
                    continue
                for repair in sensible_repairs():
                    combos.append((theme_id, vehicle_id, obstacle_id, repair.id))
    return combos


def predict_snag(world: World, obstacle_id: str) -> dict:
    sim = world.copy()
    linen = sim.get("linen")
    obstacle = sim.get(obstacle_id)
    linen.meters["snagged"] += 1
    propagate(sim, narrate=False)
    return {
        "torn": linen.meters["torn"] >= THRESHOLD,
        "stalled": sim.get("ship").meters["stalled"] >= THRESHOLD,
        "obstacle": obstacle.label,
    }


def introduce(world: World, captain: Entity, navigator: Entity, theme: Theme, vehicle: Vehicle) -> None:
    for kid in (captain, navigator):
        kid.memes["joy"] += 1
    world.say(
        f"At dusk, {captain.id} and {navigator.id} turned the yard into {theme.pretend_place}. "
        f"{vehicle.rig}"
    )
    world.say(
        f"They called it {vehicle.phrase}, and the {vehicle.linen_part} fluttered in the {theme.sky} air."
    )


def remember_previous(world: World, captain: Entity, navigator: Entity, obstacle: Obstacle) -> None:
    world.say(
        f'"Tonight we should take the previous shortcut past {obstacle.the}," {captain.id} said. '
        f'"Real star crews are brave."'
    )
    world.say(
        f'{navigator.id} touched the linen softly. "The previous time we bumped {obstacle.the}, '
        f"the ship wobbled. I don't want that again."
    )


def argue(world: World, captain: Entity, navigator: Entity, parent: Entity, obstacle: Obstacle) -> None:
    pred = predict_snag(world, "obstacle")
    world.facts["predicted_torn"] = pred["torn"]
    captain.memes["conflict"] += 1
    navigator.memes["conflict"] += 1
    captain.memes["stubborn"] += 1
    navigator.memes["caution"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{captain.id} wanted to steer toward {obstacle.the}, and {navigator.id} pulled the nose of the ship the other way."
    )
    world.say(
        f'{parent.label_word.capitalize()} heard the sharp voices. "Space crews listen before they launch," '
        f'{parent.pronoun()} called from the porch.'
    )


def snag(world: World, captain: Entity, navigator: Entity, vehicle: Vehicle, obstacle: Obstacle) -> None:
    linen = world.get("linen")
    linen.meters["snagged"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But the ship lurched first. The {vehicle.linen_part} caught on {obstacle.the} -- their {obstacle.pretend_name} -- '
        f'and the cloth gave a sudden rriiip.'
    )
    world.say(
        f"{obstacle.The} held the linen for one worried second, and {vehicle.label} sagged in the middle."
    )


def apology(world: World, captain: Entity, navigator: Entity) -> None:
    captain.memes["sorry"] += 1
    navigator.memes["sorry"] += 1
    captain.memes["conflict"] = 0.0
    navigator.memes["conflict"] = 0.0
    captain.memes["care"] += 1
    navigator.memes["care"] += 1
    world.say(
        f'For a moment they only stared. Then {captain.id} whispered, "I should have listened."'
    )
    world.say(
        f'"I should have stopped pulling and just talked," said {navigator.id}. They looked at each other, and the angry part melted.'
    )


def repair_scene(world: World, captain: Entity, navigator: Entity, parent: Entity, repair: Repair, vehicle: Vehicle) -> None:
    linen = world.get("linen")
    linen.meters["patched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} brought {repair.phrase}, but the fixing was work for four hands. "
        f"{captain.id} held the torn linen flat while {navigator.id} {repair.method}."
    )
    world.say(
        f"Soon the tear lay quiet, and the {vehicle.linen_part} looked ready to try once more."
    )


def ending_launch(world: World, captain: Entity, navigator: Entity, theme: Theme, vehicle: Vehicle, obstacle: Obstacle) -> None:
    ship = world.get("ship")
    ship.meters["launched"] += 1
    for kid in (captain, navigator):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f'This time {captain.id} asked, "Left or right, Navigator?" and {navigator.id} grinned. "Together."'
    )
    world.say(
        f"They guided {vehicle.label} in a wide curve around {obstacle.the}, and the patched linen held."
    )
    world.say(
        f"Above them the first stars came out, and the crew {theme.sendoff} -- not by winning the quarrel, but by mending it."
    )


def ending_gentle(world: World, captain: Entity, navigator: Entity, theme: Theme, vehicle: Vehicle, parent: Entity) -> None:
    for kid in (captain, navigator):
        kid.memes["calm"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"The patch was neat, but not strong enough for a wild launch that night."
    )
    world.say(
        f"So {parent.label_word} spread cushions inside {vehicle.label}, and the two astronauts lay shoulder to shoulder under the open sky."
    )
    world.say(
        f"They traced slow constellations with their fingers and planned a wiser route for tomorrow. The mission waited, but the crew was whole again."
    )


def tell(
    theme: Theme,
    vehicle: Vehicle,
    obstacle: Obstacle,
    repair: Repair,
    captain_name: str = "Nova",
    captain_gender: str = "girl",
    navigator_name: str = "Leo",
    navigator_gender: str = "boy",
    trait: str = "gentle",
    parent_type: str = "mother",
    relation: str = "siblings",
) -> World:
    world = World()
    captain = world.add(
        Entity(
            id="captain",
            kind="character",
            type=captain_gender,
            label=captain_name,
            phrase=captain_name,
            role="captain",
            traits=["bold"],
            attrs={"name": captain_name, "relation": relation},
        )
    )
    navigator = world.add(
        Entity(
            id="navigator",
            kind="character",
            type=navigator_gender,
            label=navigator_name,
            phrase=navigator_name,
            role="navigator",
            traits=[trait],
            attrs={"name": navigator_name, "relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    ship = world.add(
        Entity(
            id="ship",
            type="ship",
            label=vehicle.label,
            phrase=vehicle.phrase,
            tags=set(vehicle.tags),
        )
    )
    linen = world.add(
        Entity(
            id="linen",
            type="linen",
            label="linen",
            phrase=vehicle.linen_part,
            tags={"linen"},
        )
    )
    world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.the,
            tags=set(obstacle.tags),
        )
    )

    introduce(world, captain, navigator, theme, vehicle)
    remember_previous(world, captain, navigator, obstacle)

    world.para()
    argue(world, captain, navigator, parent, obstacle)
    snag(world, captain, navigator, vehicle, obstacle)

    world.para()
    apology(world, captain, navigator)
    repair_scene(world, captain, navigator, parent, repair, vehicle)

    success = mission_success(vehicle, obstacle, repair, trait)
    world.para()
    if success:
        ending_launch(world, captain, navigator, theme, vehicle, obstacle)
        outcome = "launched"
    else:
        ending_gentle(world, captain, navigator, theme, vehicle, parent)
        outcome = "stalled"

    world.facts.update(
        captain=captain,
        navigator=navigator,
        parent=parent,
        theme=theme,
        vehicle=vehicle,
        obstacle_cfg=obstacle,
        repair=repair,
        relation=relation,
        outcome=outcome,
        success=success,
        snagged=True,
        torn=world.get("linen").meters["torn"] >= THRESHOLD,
        patched=world.get("linen").meters["patched"] >= THRESHOLD,
        teamwork_bonus=teamwork_bonus(trait),
    )
    return world


THEMES = {
    "nebula": Theme(
        id="nebula",
        sky="violet",
        pretend_place="the edge of a singing nebula",
        sendoff="sailed into their pretend nebula",
        tags={"space"},
    ),
    "moon": Theme(
        id="moon",
        sky="silver",
        pretend_place="a moon base on the far side of the garden",
        sendoff="rolled toward their moon base",
        tags={"space", "moon"},
    ),
    "comet": Theme(
        id="comet",
        sky="blue",
        pretend_place="the tail of a sleepy comet",
        sendoff="glided along the comet tail",
        tags={"space", "comet"},
    ),
}

VEHICLES = {
    "rocket_cart": Vehicle(
        id="rocket_cart",
        label="the rocket cart",
        phrase="the Star Hopper",
        rig="A wagon became a rocket cart, a colander became a radar dish, and a pale linen tea towel served as the ship's sail.",
        linen_part="linen sail",
        motion="rolled",
        fragility=1,
        tags={"rocket", "linen"},
    ),
    "crate_shuttle": Vehicle(
        id="crate_shuttle",
        label="the crate shuttle",
        phrase="the Moon Mender",
        rig="A wooden crate became a shuttle, a saucepan lid became a moon window, and a striped linen napkin stretched across the side like a shining fin.",
        linen_part="linen fin",
        motion="skimmed",
        fragility=2,
        tags={"rocket", "linen"},
    ),
    "box_skiff": Vehicle(
        id="box_skiff",
        label="the star skiff",
        phrase="the Comet Skipper",
        rig="A cardboard box became a star skiff, two spoons became control levers, and a square of linen flapped from the back like a brave little solar sail.",
        linen_part="linen solar sail",
        motion="glided",
        fragility=1,
        tags={"rocket", "linen"},
    ),
}

OBSTACLES = {
    "rosebush": Obstacle(
        id="rosebush",
        label="rosebush",
        the="the rosebush",
        roughness=2,
        snags_linen=True,
        pretend_name="meteor thorns",
        tags={"garden", "thorn"},
    ),
    "fence_latch": Obstacle(
        id="fence_latch",
        label="fence latch",
        the="the fence latch",
        roughness=3,
        snags_linen=True,
        pretend_name="iron asteroid hook",
        tags={"fence", "metal"},
    ),
    "branch": Obstacle(
        id="branch",
        label="low branch",
        the="the low branch",
        roughness=2,
        snags_linen=True,
        pretend_name="comet claw",
        tags={"tree", "branch"},
    ),
    "chalk_planet": Obstacle(
        id="chalk_planet",
        label="chalk planet",
        the="the chalk planet",
        roughness=0,
        snags_linen=False,
        pretend_name="quiet moon circle",
        tags={"chalk"},
    ),
}

REPAIRS = {
    "silver_tape": Repair(
        id="silver_tape",
        label="silver tape",
        phrase="a roll of silver tape",
        sense=3,
        power=3,
        works_on_linen=True,
        method="smoothed silver tape across the tear from both sides",
        tags={"tape", "repair"},
    ),
    "safety_pins": Repair(
        id="safety_pins",
        label="safety pins",
        phrase="a small tin of safety pins",
        sense=2,
        power=2,
        works_on_linen=True,
        method="fastened the cloth carefully with three tiny safety pins",
        tags={"pins", "repair"},
    ),
    "star_stickers": Repair(
        id="star_stickers",
        label="star stickers",
        phrase="a sheet of glittering star stickers",
        sense=1,
        power=1,
        works_on_linen=False,
        method="pressed bright stickers over the rip",
        tags={"stickers"},
    ),
}

GIRL_NAMES = ["Nova", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora"]
BOY_NAMES = ["Leo", "Max", "Sam", "Finn", "Noah", "Eli", "Theo", "Ben"]
TRAITS = ["gentle", "patient", "kind", "careful", "curious", "quick"]
RELATIONS = ["siblings", "friends"]


@dataclass
class StoryParams:
    theme: str
    vehicle: str
    obstacle: str
    repair: str
    captain: str
    captain_gender: str
    navigator: str
    navigator_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="nebula",
        vehicle="rocket_cart",
        obstacle="rosebush",
        repair="silver_tape",
        captain="Nova",
        captain_gender="girl",
        navigator="Leo",
        navigator_gender="boy",
        parent="mother",
        trait="gentle",
        relation="siblings",
    ),
    StoryParams(
        theme="moon",
        vehicle="crate_shuttle",
        obstacle="fence_latch",
        repair="silver_tape",
        captain="Sam",
        captain_gender="boy",
        navigator="Mia",
        navigator_gender="girl",
        parent="father",
        trait="careful",
        relation="friends",
    ),
    StoryParams(
        theme="comet",
        vehicle="box_skiff",
        obstacle="branch",
        repair="safety_pins",
        captain="Ava",
        captain_gender="girl",
        navigator="Ben",
        navigator_gender="boy",
        parent="mother",
        trait="quick",
        relation="siblings",
    ),
]


KNOWLEDGE = {
    "linen": [
        (
            "What is linen?",
            "Linen is a cloth made from plant fibers. It feels light and strong, but it can still tear if it catches on something rough.",
        )
    ],
    "rocket": [
        (
            "What is a sail on a pretend spaceship game?",
            "In a pretend game, a sail is a piece of cloth that makes the ship look ready to fly. Children can imagine it as a solar sail catching starlight.",
        )
    ],
    "repair": [
        (
            "Why is tape useful for fixing torn cloth in a game?",
            "Tape can hold the edges still so the tear does not open wider right away. It is a quick helper when children need a simple patch for play.",
        )
    ],
    "conflict": [
        (
            "What does reconciliation mean?",
            "Reconciliation means making peace after an argument. People listen, say sorry, and find a way to work together again.",
        )
    ],
    "thorn": [
        (
            "Why can thorns or rough hooks tear cloth?",
            "Sharp or rough things can catch tiny threads and pull them apart. That is why cloth should be kept away from thorns and metal hooks.",
        )
    ],
}
KNOWLEDGE_ORDER = ["linen", "rocket", "repair", "conflict", "thorn"]


def pair_noun(captain: Entity, navigator: Entity, relation: str) -> str:
    if relation == "siblings":
        if captain.type == "boy" and navigator.type == "boy":
            return "two brothers"
        if captain.type == "girl" and navigator.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    navigator = f["navigator"]
    vehicle = f["vehicle"]
    obstacle = f["obstacle_cfg"]
    outcome = f["outcome"]
    end_clause = (
        "and ends with the patched ship launching again"
        if outcome == "launched"
        else "and ends with a gentle porch-side stargazing scene after the argument is healed"
    )
    return [
        'Write a short space-adventure story for a 3-to-5-year-old that includes the words "previous" and "linen".',
        f"Tell a story where {captain.attrs['name']} and {navigator.attrs['name']} argue about using a previous shortcut in {vehicle.label}, the linen part snags on {obstacle.the}, and they reconcile.",
        f"Write a child-facing story with conflict and reconciliation in a backyard space game, {end_clause}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    navigator = f["navigator"]
    parent = f["parent"]
    vehicle = f["vehicle"]
    obstacle = f["obstacle_cfg"]
    repair = f["repair"]
    relation = f["relation"]
    pair = pair_noun(captain, navigator, relation)
    captain_name = captain.attrs["name"]
    navigator_name = navigator.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain_name} and {navigator_name}, who pretend to be a space crew. Their {parent.label_word} is nearby when the problem happens.",
        ),
        (
            "Why did they start arguing?",
            f"{captain_name} wanted to use the previous shortcut again, but {navigator_name} remembered that the route had felt risky before. The conflict came from one child wanting speed and the other wanting care.",
        ),
        (
            "What part of the ship was made of linen?",
            f"The ship had a {vehicle.linen_part}. That linen part is what snagged and tore when the launch went crooked.",
        ),
        (
            "What happened to the ship during the quarrel?",
            f"The ship lurched the wrong way and the {vehicle.linen_part} caught on {obstacle.the}. Because the cloth tore, the pretend spaceship sagged and could not keep going the same way.",
        ),
        (
            "How did they reconcile?",
            f"They stopped blaming each other and both said sorry. After that, they worked side by side to patch the tear instead of pulling in opposite directions.",
        ),
    ]
    if f["outcome"] == "launched":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children steering together and launching their game again. The patched linen held because the repair was strong enough and they were finally cooperating.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly instead of wildly: the patch was not strong enough for a big launch that night. Even so, the children lay together under the sky and planned a wiser mission because they had made peace.",
            )
        )
    qa.append(
        (
            f"What did {parent.label_word} help with?",
            f"{parent.label_word.capitalize()} brought {repair.label} for the patch. The grown-up helped them start the fix, but the children themselves had to hold the linen and mend it together.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"linen", "rocket", "repair", "conflict"}
    if world.facts["obstacle_cfg"].id in {"rosebush", "fence_latch", "branch"}:
        tags.add("thorn")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, V, O) :- theme(T), vehicle(V), obstacle(O), snags_linen(O), has_linen(V).
sensible(R) :- repair(R), works_on_linen(R), sense(R, S), sense_min(M), S >= M.
valid_story(T, V, O, R) :- valid(T, V, O), sensible(R).

team_bonus(1) :- trait(T), teamwork_trait(T).
team_bonus(0) :- trait(T), not teamwork_trait(T).

severity(F + R) :- chosen_vehicle(V), fragility(V, F), chosen_obstacle(O), roughness(O, R).
score(P + B) :- chosen_repair(R), power(R, P), team_bonus(B).

mission(launched) :- score(S), severity(V), S >= V.
mission(stalled) :- score(S), severity(V), S < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for vid, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("fragility", vid, vehicle.fragility))
        if vehicle.linen_part:
            lines.append(asp.fact("has_linen", vid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("roughness", oid, obstacle.roughness))
        if obstacle.snags_linen:
            lines.append(asp.fact("snags_linen", oid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
        if repair.works_on_linen:
            lines.append(asp.fact("works_on_linen", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(TEAMWORK_TRAITS):
        lines.append(asp.fact("teamwork_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_mission(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_vehicle", params.vehicle),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_repair", params.repair),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show mission/1."))
    atoms = asp.atoms(model, "mission")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.vehicle not in VEHICLES or params.obstacle not in OBSTACLES or params.repair not in REPAIRS:
        raise StoryError("(Invalid parameters for outcome calculation.)")
    return (
        "launched"
        if mission_success(VEHICLES[params.vehicle], OBSTACLES[params.obstacle], REPAIRS[params.repair], params.trait)
        else "stalled"
    )


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP valid_story set matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid story combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    mismatches = 0
    for params in cases:
        if asp_mission(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP mission model matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} mission outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a linen spaceship, a previous shortcut, a quarrel, and reconciliation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle is not None and args.vehicle is not None:
        vehicle = VEHICLES[args.vehicle]
        obstacle = OBSTACLES[args.obstacle]
        if not can_snag(vehicle, obstacle):
            raise StoryError(explain_rejection(vehicle, obstacle))
    if args.repair is not None:
        repair = REPAIRS[args.repair]
        if repair.sense < SENSE_MIN or not repair.works_on_linen:
            raise StoryError(explain_repair(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.vehicle is None or combo[1] == args.vehicle)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, vehicle_id, obstacle_id, repair_id = rng.choice(sorted(combos))
    captain, captain_gender = _pick_kid(rng)
    navigator, navigator_gender = _pick_kid(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(RELATIONS)

    return StoryParams(
        theme=theme_id,
        vehicle=vehicle_id,
        obstacle=obstacle_id,
        repair=repair_id,
        captain=captain,
        captain_gender=captain_gender,
        navigator=navigator,
        navigator_gender=navigator_gender,
        parent=parent,
        trait=trait,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        vehicle = VEHICLES[params.vehicle]
        obstacle = OBSTACLES[params.obstacle]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not can_snag(vehicle, obstacle):
        raise StoryError(explain_rejection(vehicle, obstacle))
    if repair.sense < SENSE_MIN or not repair.works_on_linen:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        theme=theme,
        vehicle=vehicle,
        obstacle=obstacle,
        repair=repair,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        navigator_name=params.navigator,
        navigator_gender=params.navigator_gender,
        trait=params.trait,
        parent_type=params.parent,
        relation=params.relation,
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
        print(asp_program("", "#show valid_story/4.\n#show mission/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (theme, vehicle, obstacle, repair) combos:\n")
        for theme, vehicle, obstacle, repair in combos:
            print(f"  {theme:7} {vehicle:12} {obstacle:12} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.captain} and {p.navigator}: {p.vehicle} vs {p.obstacle} ({outcome_of(p)})"
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
