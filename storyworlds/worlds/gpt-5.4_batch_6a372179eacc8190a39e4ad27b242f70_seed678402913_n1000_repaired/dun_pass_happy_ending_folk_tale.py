#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dun_pass_happy_ending_folk_tale.py
=============================================================

A small folk-tale storyworld about a child, a dun pony, and a mountain pass.

The seed asked for the words "dun" and "pass", a happy ending, and a folk-tale
style. This world models a simple causal tale: a village child must carry a
needed gift over a high pass to a lonely cottage. The weather or terrain creates
a real problem, and the chosen aid must honestly solve that problem. If the aid
fits, the child and the dun pony reach the cottage and the ending image proves
the world changed for the better.

Run it
------
    python storyworlds/worlds/gpt-5.4/dun_pass_happy_ending_folk_tale.py
    python storyworlds/worlds/gpt-5.4/dun_pass_happy_ending_folk_tale.py --gift broth --obstacle fog
    python storyworlds/worlds/gpt-5.4/dun_pass_happy_ending_folk_tale.py --helper lantern
    python storyworlds/worlds/gpt-5.4/dun_pass_happy_ending_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/dun_pass_happy_ending_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dun_pass_happy_ending_folk_tale.py --verify
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
_THIS = os.path.abspath(__file__)
_WORLDS_DIR = os.path.dirname(_THIS)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(_WORLDS_DIR))
sys.path.insert(0, _STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Vale:
    id: str
    name: str
    opening: str
    cottage_place: str
    pass_name: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    purpose: str
    comfort_text: str
    tags: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    sign: str
    danger_text: str
    turn_text: str
    tags: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    use_text: str
    solve_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


VALES = {
    "heather": Vale(
        id="heather",
        name="Heather Vale",
        opening="In Heather Vale, the thatched roofs sat low under the morning mist.",
        cottage_place="a stone cottage beyond the high ridge",
        pass_name="the Old Heather Pass",
        ending_image="the windows of the stone cottage glowed like two warm coins in the dusk",
        tags={"village", "mountain"},
    ),
    "pine": Vale(
        id="pine",
        name="Pine Hollow",
        opening="In Pine Hollow, the wind combed the tall dark trees and rang the little chapel bell.",
        cottage_place="a spruce-shadowed cottage beyond the ridge",
        pass_name="the Needle Pass",
        ending_image="the cottage lamp shone under the pines, steady as a star",
        tags={"forest", "mountain"},
    ),
    "brook": Vale(
        id="brook",
        name="Silver Brook",
        opening="In Silver Brook, the stream flashed between stones and the hens scratched in the dust.",
        cottage_place="a whitewashed cottage on the far slope",
        pass_name="the Shepherd's Pass",
        ending_image="the whitewashed cottage stood bright above the brook, with smoke rising straight from its chimney",
        tags={"brook", "mountain"},
    ),
}

GIFTS = {
    "broth": Gift(
        id="broth",
        label="broth",
        phrase="a covered pot of hot broth",
        purpose="to warm Grandmother after a long cold night",
        comfort_text="The steam smelled of parsley and made the air seem kinder.",
        tags={"food", "warmth"},
        needs={"path"},
    ),
    "herbs": Gift(
        id="herbs",
        label="herbs",
        phrase="a packet of healing herbs",
        purpose="to ease Grandmother's cough",
        comfort_text="The packet held the green smell of summer even in the cold air.",
        tags={"medicine"},
        needs={"path"},
    ),
    "seedcakes": Gift(
        id="seedcakes",
        label="seedcakes",
        phrase="a round of honey seedcakes",
        purpose="to cheer Grandmother and fill her cupboard",
        comfort_text="The sweet smell of honey drifted from the cloth.",
        tags={"food", "gift"},
        needs={"path"},
    ),
    "lamp_oil": Gift(
        id="lamp_oil",
        label="lamp oil",
        phrase="a small jug of lamp oil",
        purpose="to give Grandmother light for the evening",
        comfort_text="The little jug clinked softly against the saddle strap.",
        tags={"light", "gift"},
        needs={"path"},
    ),
}

OBSTACLES = {
    "fog": Obstacle(
        id="fog",
        label="fog",
        sign="a thick white fog had folded itself across the pass",
        danger_text="The stones and drop-offs were hard to see, and one wrong step could send pony and child the wrong way.",
        turn_text="Even the dun pony stopped and blew through its nose, unwilling to guess at the path.",
        tags={"fog"},
        needs={"sight"},
    ),
    "wind": Obstacle(
        id="wind",
        label="wind",
        sign="a hard mountain wind came racing through the pass",
        danger_text="It tugged at cloaks and packs and made the narrow path feel twice as small.",
        turn_text="The gusts shoved at the child and worried the dun pony's ears.",
        tags={"wind"},
        needs={"steady"},
    ),
    "snowdrift": Obstacle(
        id="snowdrift",
        label="snowdrift",
        sign="a pale snowdrift had slipped down and buried the track",
        danger_text="The safe way forward was hidden, and the pony could not see where the path bent around the rocks.",
        turn_text="Cold whiteness lay over every footprint, and the ridge looked changed.",
        tags={"snow"},
        needs={"mark"},
    ),
}

HELPERS = {
    "lantern": Helper(
        id="lantern",
        label="lantern",
        phrase="a horn lantern with a bright clear flame inside",
        use_text="The child lifted the lantern high so the path could show itself one careful stone at a time.",
        solve_text="Its yellow light found the edge of the trail and kept them from wandering into the gray.",
        qa_text="The lantern lit the hidden path through the fog and over the buried stones.",
        tags={"light"},
        covers={"sight"},
    ),
    "rope": Helper(
        id="rope",
        label="rope",
        phrase="a coil of stout rope",
        use_text="The child looped the rope across chest and saddle, so pony and rider could lean together against the gusts.",
        solve_text="With the rope holding them steady, the wind could not shove them apart or off balance.",
        qa_text="The rope let the child and the pony brace together and stay steady in the wind.",
        tags={"rope"},
        covers={"steady"},
    ),
    "bell": Helper(
        id="bell",
        label="bell",
        phrase="a brass bell on a red cord",
        use_text="The child tied the bell to the pony's neck and listened to its honest ringing while watching for the old marker posts.",
        solve_text="The ringing kept courage alive, and the known line of marker posts showed where the buried path ran.",
        qa_text="The bell helped them follow the old marker posts and keep to the true way through the snowdrift.",
        tags={"bell"},
        covers={"mark"},
    ),
    "staff": Helper(
        id="staff",
        label="staff",
        phrase="an ash walking staff cut by the miller",
        use_text="The child planted the staff before each step and tapped for firm ground before the pony moved.",
        solve_text="The staff found the solid edge of the path and gave the child balance on the narrow track.",
        qa_text="The staff let the child test the ground and keep balance on the path.",
        tags={"staff"},
        covers={"path", "steady"},
    ),
}

GIRL_NAMES = ["Mara", "Elin", "Tessa", "Nora", "Asha", "Brin"]
BOY_NAMES = ["Ivo", "Tarin", "Milo", "Rowan", "Perrin", "Luka"]
TRAITS = ["gentle", "brave", "patient", "steady", "kind", "careful"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cold_worry(world: World) -> list[str]:
    out: list[str] = []
    traveler = world.entities.get("traveler")
    pony = world.entities.get("pony")
    pass_ent = world.entities.get("pass")
    if not traveler or not pony or not pass_ent:
        return out
    if pass_ent.meters["blocked"] < THRESHOLD:
        return out
    sig = ("cold_worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.memes["fear"] += 1
    traveler.memes["duty"] += 1
    pony.memes["hesitation"] += 1
    out.append("__turn__")
    return out


def _r_success(world: World) -> list[str]:
    out: list[str] = []
    traveler = world.entities.get("traveler")
    pony = world.entities.get("pony")
    pass_ent = world.entities.get("pass")
    gift = world.entities.get("gift")
    grandmother = world.entities.get("grandmother")
    if not all([traveler, pony, pass_ent, gift, grandmother]):
        return out
    if pass_ent.meters["crossable"] < THRESHOLD or gift.meters["delivered"] < THRESHOLD:
        return out
    sig = ("success",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.memes["relief"] += 1
    traveler.memes["joy"] += 1
    pony.memes["calm"] += 1
    grandmother.memes["gratitude"] += 1
    out.append("__arrival__")
    return out


CAUSAL_RULES = [
    Rule(name="cold_worry", tag="emotion", apply=_r_cold_worry),
    Rule(name="success", tag="resolution", apply=_r_success),
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


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def helper_fits(helper: Helper, obstacle: Obstacle, gift: Gift) -> bool:
    needed = set(obstacle.needs) | set(gift.needs)
    return needed.issubset(helper.covers)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for vale_id in VALES:
        for gift_id, gift in GIFTS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                for helper_id, helper in HELPERS.items():
                    if helper_fits(helper, obstacle, gift):
                        combos.append((vale_id, gift_id, obstacle_id, helper_id))
    return combos


def explain_rejection(gift: Gift, obstacle: Obstacle, helper: Helper) -> str:
    need = sorted(set(obstacle.needs) | set(gift.needs))
    have = sorted(helper.covers)
    return (
        f"(No story: {helper.label} does not honestly solve this journey. "
        f"The gift and obstacle need {need}, but {helper.label} covers {have}. "
        f"Pick a helper that can really get the child and the dun pony through the pass.)"
    )


def predict_crossing(world: World, helper: Helper) -> dict:
    sim = world.copy()
    traveler = sim.get("traveler")
    pony = sim.get("pony")
    pass_ent = sim.get("pass")
    aid = sim.get("helper")
    aid.tags = set(helper.covers)
    pass_ent.meters["blocked"] += 1
    propagate(sim, narrate=False)
    if helper_fits(helper, sim.facts["obstacle_cfg"], sim.facts["gift_cfg"]):
        pass_ent.meters["crossable"] += 1
        traveler.meters["progress"] += 1
        pony.meters["progress"] += 1
    return {
        "crossable": pass_ent.meters["crossable"] >= THRESHOLD,
        "fear": traveler.memes["fear"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, vale: Vale, traveler: Entity, pony: Entity, gift: Gift) -> None:
    world.say(vale.opening)
    world.say(
        f"There lived {traveler.id}, a {traveler.attrs.get('trait', 'kind')} child, "
        f"and a small dun pony with wise dark eyes."
    )
    world.say(
        f"One morning the village gathered {gift.phrase} and asked {traveler.id} "
        f"to carry it to Grandmother in {vale.cottage_place}, {gift.purpose}."
    )
    traveler.memes["duty"] += 1
    pony.memes["trust"] += 1


def set_out(world: World, vale: Vale, traveler: Entity, pony: Entity, helper: Helper, gift: Gift) -> None:
    world.say(
        f"So {traveler.id} set out with the dun pony toward {vale.pass_name}, carrying "
        f"{helper.phrase} and guarding {gift.label} as if it were a small promise."
    )
    world.say(gift.comfort_text)


def face_obstacle(world: World, obstacle: Obstacle) -> None:
    pass_ent = world.get("pass")
    pass_ent.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when child and pony came to the narrow pass, {obstacle.sign}. "
        f"{obstacle.danger_text}"
    )
    world.say(obstacle.turn_text)


def elder_warning(world: World, traveler: Entity, helper: Helper, obstacle: Obstacle, gift: Gift) -> None:
    pred = predict_crossing(world, helper)
    world.facts["predicted_crossable"] = pred["crossable"]
    if pred["crossable"]:
        world.say(
            f"Then {traveler.id} remembered the village elder's words: "
            f'"Carry {helper.label} with a clear mind, and no true path will refuse you."'
        )
    else:
        world.say(
            f"Then {traveler.id} remembered the elder's warning that not every fine-looking thing "
            f"can help on a hard road."
        )


def use_helper(world: World, traveler: Entity, pony: Entity, helper: Helper, obstacle: Obstacle, gift: Gift) -> None:
    pass_ent = world.get("pass")
    traveler.memes["courage"] += 1
    pony.memes["trust"] += 1
    world.say(helper.use_text)
    if not helper_fits(helper, obstacle, gift):
        raise StoryError(explain_rejection(gift, obstacle, helper))
    pass_ent.meters["crossable"] += 1
    traveler.meters["progress"] += 1
    pony.meters["progress"] += 1
    world.say(helper.solve_text)


def cross_pass(world: World, vale: Vale, traveler: Entity, pony: Entity) -> None:
    world.say(
        f"Step by step they crossed the pass together, the child speaking softly and the dun pony answering with patient hooves on stone."
    )


def arrive(world: World, vale: Vale, traveler: Entity, gift_ent: Entity, grandmother: Entity, gift: Gift) -> None:
    gift_ent.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached Grandmother's door. She opened it with a start, then smiled so wide that every tired mile seemed to fall away."
    )
    world.say(
        f"{traveler.id} placed {gift.phrase} in her hands, and Grandmother drew child and pony into the warm light."
    )


def blessing(world: World, traveler: Entity, pony: Entity, grandmother: Entity, vale: Vale, gift: Gift) -> None:
    traveler.memes["joy"] += 1
    grandmother.memes["gratitude"] += 1
    world.say(
        f'She said, "A brave heart, a faithful dun pony, and a wise little help can carry goodness through any pass."'
    )
    world.say(
        f"They shared the evening fire, and the gift did what it had been meant to do."
    )
    world.say(
        f"When night came, {vale.ending_image}, and {traveler.id} knew the road home would no longer feel lonely."
    )


def tell(
    vale: Vale,
    gift: Gift,
    obstacle: Obstacle,
    helper: Helper,
    traveler_name: str = "Mara",
    traveler_gender: str = "girl",
    trait: str = "kind",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    traveler = world.add(Entity(
        id="traveler",
        kind="character",
        type=traveler_gender,
        label=traveler_name,
        phrase=traveler_name,
        role="traveler",
        attrs={"trait": trait, "name": traveler_name},
    ))
    pony = world.add(Entity(
        id="pony",
        kind="thing",
        type="pony",
        label="dun pony",
        phrase="the dun pony",
        role="companion",
        tags={"pony", "dun"},
    ))
    pass_ent = world.add(Entity(
        id="pass",
        kind="thing",
        type="pass",
        label=vale.pass_name,
        phrase=vale.pass_name,
        role="path",
        tags={"pass"},
    ))
    gift_ent = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift.label,
        phrase=gift.phrase,
        role="gift",
        tags=set(gift.tags),
    ))
    grandmother = world.add(Entity(
        id="grandmother",
        kind="character",
        type=elder_type,
        label="Grandmother",
        phrase="Grandmother",
        role="recipient",
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="thing",
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        role="helper",
        tags=set(helper.covers),
    ))

    world.facts.update(
        vale=vale,
        gift_cfg=gift,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        traveler_name=traveler_name,
        traveler_gender=traveler_gender,
        trait=trait,
    )

    introduce(world, vale, traveler, pony, gift)
    set_out(world, vale, traveler, pony, helper, gift)

    world.para()
    face_obstacle(world, obstacle)
    elder_warning(world, traveler, helper, obstacle, gift)

    world.para()
    use_helper(world, traveler, pony, helper, obstacle, gift)
    cross_pass(world, vale, traveler, pony)
    arrive(world, vale, traveler, gift_ent, grandmother, gift)

    world.para()
    blessing(world, traveler, pony, grandmother, vale, gift)

    world.facts.update(
        traveler=traveler,
        pony=pony,
        pass_ent=pass_ent,
        gift_ent=gift_ent,
        grandmother=grandmother,
        helper_ent=helper_ent,
        crossed=pass_ent.meters["crossable"] >= THRESHOLD,
        delivered=gift_ent.meters["delivered"] >= THRESHOLD,
        happy=traveler.memes["joy"] >= THRESHOLD and grandmother.memes["gratitude"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    vale: str
    gift: str
    obstacle: str
    helper: str
    traveler_name: str
    traveler_gender: str
    trait: str
    elder_type: str = "grandmother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pony": [
        (
            "What is a pony?",
            "A pony is a small horse. Ponies are strong for their size and can carry people or packs on country roads and mountain paths.",
        )
    ],
    "pass": [
        (
            "What is a mountain pass?",
            "A mountain pass is a way through high hills or mountains. It is often narrow, so travelers have to move carefully there.",
        )
    ],
    "fog": [
        (
            "Why can fog be dangerous on a path?",
            "Fog makes it hard to see where the path goes. When people cannot see edges or stones clearly, they can lose the safe way.",
        )
    ],
    "wind": [
        (
            "Why is strong wind hard on a mountain path?",
            "Strong wind can push at people and animals. On a narrow path, that makes balance much more important.",
        )
    ],
    "snow": [
        (
            "Why can snow hide a path?",
            "Snow can cover footprints, stones, and the edge of a trail. Then travelers must look for other signs to know where the true path is.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives steady light. It helps people see in dark or foggy places without having to guess where to step.",
        )
    ],
    "rope": [
        (
            "What is a rope useful for on a hard journey?",
            "A rope can help people and animals stay together and pull against a force. It is useful when the road is steep or the wind is strong.",
        )
    ],
    "bell": [
        (
            "Why might a bell help on a journey?",
            "A bell can help travelers keep track of one another, and its ringing can guide attention. In old tales, a bell often also gives courage because it sounds clear and familiar.",
        )
    ],
    "staff": [
        (
            "What is a walking staff for?",
            "A walking staff helps with balance and can test the ground ahead. That makes it useful on rough or hidden paths.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pony", "pass", "fog", "wind", "snow", "lantern", "rope", "bell", "staff"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    vale = f["vale"]
    gift = f["gift_cfg"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    name = f["traveler_name"]
    return [
        f'Write a short folk tale for a young child that includes the words "dun" and "pass" and ends happily.',
        f"Tell a folk-tale story where {name} leads a dun pony over {vale.pass_name} with {gift.phrase}, faces {obstacle.label}, and uses {helper.label} wisely.",
        f"Write a warm mountain tale about a child carrying {gift.label} to Grandmother, with a true problem at the pass, a clever turn, and a peaceful ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    traveler = f["traveler"]
    pony = f["pony"]
    vale = f["vale"]
    gift = f["gift_cfg"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    grandmother = f["grandmother"]
    name = traveler.attrs.get("name", traveler.label)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child from {vale.name}, and a faithful dun pony. They travel together to bring {gift.label} to Grandmother.",
        ),
        (
            "Why did the child go over the pass?",
            f"{name} went over the pass to bring {gift.phrase} to Grandmother. The gift mattered because it was meant {gift.purpose}.",
        ),
        (
            "What problem did they meet at the pass?",
            f"They met {obstacle.label} at the pass. {obstacle.danger_text} That is why the crossing became a real problem instead of an easy ride.",
        ),
        (
            f"How did {name} get through the pass?",
            f"{name} used {helper.label}. {helper.qa_text} Because the helper truly matched the danger, the child and the dun pony could keep going safely.",
        ),
        (
            "How do we know the ending is happy?",
            f"The child reached Grandmother's cottage and delivered the gift, and Grandmother welcomed them into the warm light. The final image is peaceful because the hard road ended in comfort, gratitude, and firelight.",
        ),
    ]
    if world.facts.get("happy"):
        qa.append(
            (
                "What changed by the end of the story?",
                f"At first the pass felt dangerous and uncertain, and even the dun pony hesitated. By the end, the gift had reached Grandmother and fear had turned into relief and joy around the evening fire.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"pony", "pass"}
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper_cfg"]
    if obstacle.id == "fog":
        tags.add("fog")
    elif obstacle.id == "wind":
        tags.add("wind")
    elif obstacle.id == "snowdrift":
        tags.add("snow")
    tags.add(helper.id)
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
# Trace
# ---------------------------------------------------------------------------
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:11} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
need(Need, G, O) :- gift(G), gift_need(G, Need), obstacle(O).
need(Need, G, O) :- obstacle(O), obstacle_need(O, Need), gift(G).
covers_all(H, G, O) :- helper(H), not missing_need(H, G, O).
missing_need(H, G, O) :- need(N, G, O), not helper_covers(H, N).

valid(V, G, O, H) :- vale(V), gift(G), obstacle(O), helper(H), covers_all(H, G, O).

outcome(V, G, O, H, happy) :- valid(V, G, O, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for vale_id in VALES:
        lines.append(asp.fact("vale", vale_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for need in sorted(gift.needs):
            lines.append(asp.fact("gift_need", gift_id, need))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        for need in sorted(obstacle.needs):
            lines.append(asp.fact("obstacle_need", obstacle_id, need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for need in sorted(helper.covers):
            lines.append(asp.fact("helper_covers", helper_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_vale", params.vale),
            asp.fact("chosen_gift", params.gift),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_helper", params.helper),
            "selected_outcome(X) :- chosen_vale(V), chosen_gift(G), chosen_obstacle(O), chosen_helper(H), outcome(V,G,O,H,X).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
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

    # Outcome parity on curated and random valid scenarios.
    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    for params in cases:
        expected = "happy"
        got = asp_outcome(params)
        if got != expected:
            rc = 1
            print(
                "MISMATCH in outcome:",
                params,
                "asp=",
                got,
                "python=",
                expected,
            )
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    # Smoke test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        vale="heather",
        gift="broth",
        obstacle="fog",
        helper="lantern",
        traveler_name="Mara",
        traveler_gender="girl",
        trait="gentle",
        elder_type="grandmother",
    ),
    StoryParams(
        vale="pine",
        gift="herbs",
        obstacle="wind",
        helper="rope",
        traveler_name="Ivo",
        traveler_gender="boy",
        trait="steady",
        elder_type="grandmother",
    ),
    StoryParams(
        vale="brook",
        gift="seedcakes",
        obstacle="snowdrift",
        helper="bell",
        traveler_name="Nora",
        traveler_gender="girl",
        trait="brave",
        elder_type="grandmother",
    ),
    StoryParams(
        vale="heather",
        gift="lamp_oil",
        obstacle="wind",
        helper="staff",
        traveler_name="Rowan",
        traveler_gender="boy",
        trait="patient",
        elder_type="grandmother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child, a dun pony, and a hard mountain pass."
    )
    ap.add_argument("--vale", choices=VALES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--traveler-name")
    ap.add_argument("--traveler-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vale and args.gift and args.obstacle and args.helper:
        gift = GIFTS[args.gift]
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if not helper_fits(helper, obstacle, gift):
            raise StoryError(explain_rejection(gift, obstacle, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.vale is None or combo[0] == args.vale)
        and (args.gift is None or combo[1] == args.gift)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    vale_id, gift_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    gender = args.traveler_gender or rng.choice(["girl", "boy"])
    if args.traveler_name:
        traveler_name = args.traveler_name
    else:
        traveler_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    elder_type = args.elder_type or "grandmother"
    return StoryParams(
        vale=vale_id,
        gift=gift_id,
        obstacle=obstacle_id,
        helper=helper_id,
        traveler_name=traveler_name,
        traveler_gender=gender,
        trait=trait,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.vale not in VALES:
        raise StoryError(f"(Unknown vale: {params.vale})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    world = tell(
        vale=VALES[params.vale],
        gift=GIFTS[params.gift],
        obstacle=OBSTACLES[params.obstacle],
        helper=HELPERS[params.helper],
        traveler_name=params.traveler_name,
        traveler_gender=params.traveler_gender,
        trait=params.trait,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (vale, gift, obstacle, helper) combos:\n")
        for vale, gift, obstacle, helper in combos:
            print(f"  {vale:8} {gift:10} {obstacle:10} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.traveler_name}: {p.gift} through {p.obstacle} at {p.vale} with {p.helper}"
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
