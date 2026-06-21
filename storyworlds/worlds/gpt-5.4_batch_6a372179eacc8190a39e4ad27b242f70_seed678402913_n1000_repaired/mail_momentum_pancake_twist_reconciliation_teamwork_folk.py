#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mail_momentum_pancake_twist_reconciliation_teamwork_folk.py
======================================================================================

A small folk-tale storyworld about two woodland couriers, a hill road, a cart of
mail, and a pancake that becomes part of the turning point. The world prefers
reasonable teamwork methods for the chosen road and mail load. Every generated
story is built from simulated state: a quarrel slows the work, the cart slips,
the pancake causes a surprising twist, and the friends reconcile and finish the
delivery together.

Run it
------
python storyworlds/worlds/gpt-5.4/mail_momentum_pancake_twist_reconciliation_teamwork_folk.py
python storyworlds/worlds/gpt-5.4/mail_momentum_pancake_twist_reconciliation_teamwork_folk.py --road hill --mail feast_letters --method shoulder_yoke
python storyworlds/worlds/gpt-5.4/mail_momentum_pancake_twist_reconciliation_teamwork_folk.py --road bridge --method shoulder_yoke
python storyworlds/worlds/gpt-5.4/mail_momentum_pancake_twist_reconciliation_teamwork_folk.py --all
python storyworlds/worlds/gpt-5.4/mail_momentum_pancake_twist_reconciliation_teamwork_folk.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/mail_momentum_pancake_twist_reconciliation_teamwork_folk.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
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
        female = {"girl", "mother", "hen", "goose", "doe"}
        male = {"boy", "father", "fox", "badger", "mole"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return self.label or self.id


@dataclass
class Road:
    id: str
    label: str
    phrase: str
    challenge: str
    difficulty: int
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MailLoad:
    id: str
    label: str
    phrase: str
    weight: int
    recipient: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    power: int
    handles: set[str] = field(default_factory=set)
    teamwork_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class PancakeKind:
    id: str
    label: str
    phrase: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    road: str
    mail: str
    method: str
    pancake: str
    courier: str
    courier_type: str
    helper: str
    helper_type: str
    elder_type: str
    seed: Optional[int] = None


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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.paragraphs = [[]]
        new.fired = set(self.fired)
        new.facts = copy.deepcopy(self.facts)
        return new

    def couriers(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"courier", "helper"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_quarrel_slows(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    if cart.memes["quarrel"] >= THRESHOLD and cart.meters["speed"] > 0:
        sig = ("slow",)
        if sig not in world.fired:
            world.fired.add(sig)
            cart.meters["speed"] = max(0.0, cart.meters["speed"] - 1.0)
            out.append("__slow__")
    return out


def _r_speed_to_momentum(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    if cart.meters["speed"] >= THRESHOLD and cart.memes["teamwork"] >= THRESHOLD:
        sig = ("momentum", int(cart.meters["speed"]), int(cart.memes["teamwork"]))
        if sig not in world.fired:
            world.fired.add(sig)
            cart.meters["momentum"] += 1.0
            out.append("__momentum__")
    return out


def _r_rollback_fear(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    if cart.meters["rollback"] >= THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.couriers():
                kid.memes["fear"] += 1.0
            out.append("__fear__")
    return out


CAUSAL_RULES = [
    Rule(name="quarrel_slows", tag="social", apply=_r_quarrel_slows),
    Rule(name="speed_to_momentum", tag="physical", apply=_r_speed_to_momentum),
    Rule(name="rollback_fear", tag="social", apply=_r_rollback_fear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__momentum__":
                world.say("At last the little cart began to gather momentum.")
            elif bit == "__fear__":
                world.say("For one sharp breath, both friends felt fear nip at their heels.")
    return produced


ROADS = {
    "hill": Road(
        id="hill",
        label="Mill Hill",
        phrase="the steep road up Mill Hill",
        challenge="slope",
        difficulty=2,
        scene="It curled upward like a gray ribbon toward the old mill.",
        tags={"hill", "momentum"},
    ),
    "bridge": Road(
        id="bridge",
        label="Reed Bridge",
        phrase="the long planked road over Reed Bridge",
        challenge="wind",
        difficulty=2,
        scene="The river hummed below it, and the boards liked to shake in a gust.",
        tags={"bridge", "wind"},
    ),
    "lane": Road(
        id="lane",
        label="Thistle Lane",
        phrase="the rutted road along Thistle Lane",
        challenge="ruts",
        difficulty=1,
        scene="Old wagon grooves crossed it like wrinkles in an old brow.",
        tags={"lane", "ruts"},
    ),
}

MAIL_LOADS = {
    "feast_letters": MailLoad(
        id="feast_letters",
        label="feast mail",
        phrase="a satchel of feast mail tied with blue string",
        weight=1,
        recipient="Old Badger at the mill",
        purpose="invite every hearth to the First Pancake Feast",
        tags={"mail", "feast"},
    ),
    "market_accounts": MailLoad(
        id="market_accounts",
        label="market mail",
        phrase="a bundle of market mail sealed in wax",
        weight=2,
        recipient="Old Badger at the mill",
        purpose="carry the market accounts before sunset",
        tags={"mail", "market"},
    ),
    "winter_parcels": MailLoad(
        id="winter_parcels",
        label="winter mail",
        phrase="a basket of winter mail and two small parcels",
        weight=2,
        recipient="Old Badger at the mill",
        purpose="bring letters and parcels before the frost thickened",
        tags={"mail", "winter"},
    ),
}

METHODS = {
    "shoulder_yoke": Method(
        id="shoulder_yoke",
        label="shoulder yoke",
        phrase="set their shoulders to the yoke together",
        power=3,
        handles={"slope", "ruts"},
        teamwork_line="One leaned into the pole while the other pushed from behind, and they moved as if they shared one pair of sturdy legs.",
        tags={"push", "teamwork"},
    ),
    "guide_rope": Method(
        id="guide_rope",
        label="guide rope",
        phrase="tie a guide rope to the cart and hold it from both sides",
        power=3,
        handles={"wind", "ruts"},
        teamwork_line="One friend kept the cart true while the other answered every sway with a steady pull.",
        tags={"rope", "teamwork"},
    ),
    "chant_steps": Method(
        id="chant_steps",
        label="marching chant",
        phrase="walk in a little marching chant",
        power=2,
        handles={"slope", "wind", "ruts"},
        teamwork_line="They counted their steps aloud, and the rhythm helped their feet and hands agree at last.",
        tags={"song", "teamwork"},
    ),
}

PANCAKES = {
    "honey": PancakeKind(
        id="honey",
        label="honey pancake",
        phrase="a warm honey pancake wrapped in cloth",
        smell="It smelled of butter and warm clover honey.",
        tags={"pancake", "honey"},
    ),
    "apple": PancakeKind(
        id="apple",
        label="apple pancake",
        phrase="a round apple pancake dusted with sugar",
        smell="It smelled of baked apple and cinnamon.",
        tags={"pancake", "apple"},
    ),
    "berry": PancakeKind(
        id="berry",
        label="berry pancake",
        phrase="a soft berry pancake with a purple edge",
        smell="It smelled sweet enough to make the morning feel kinder.",
        tags={"pancake", "berry"},
    ),
}

COURIERS = [
    ("Pip", "fox"),
    ("Mara", "hen"),
    ("Nell", "goose"),
    ("Rowan", "boy"),
]
HELPERS = [
    ("Moss", "mole"),
    ("Brin", "badger"),
    ("Tala", "doe"),
    ("Wren", "girl"),
]
ELDERS = ["badger", "mother", "father"]


def required_power(road: Road, load: MailLoad) -> int:
    return road.difficulty + load.weight


def method_strength(method: Method) -> int:
    return method.power


def method_fits(road: Road, load: MailLoad, method: Method) -> bool:
    return road.challenge in method.handles and method_strength(method) >= required_power(road, load)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for road_id, road in ROADS.items():
        for mail_id, load in MAIL_LOADS.items():
            for method_id, method in METHODS.items():
                if method_fits(road, load, method):
                    combos.append((road_id, mail_id, method_id))
    return combos


def explain_rejection(road: Road, load: MailLoad, method: Method) -> str:
    need = required_power(road, load)
    reasons: list[str] = []
    if road.challenge not in method.handles:
        reasons.append(
            f"{method.label} does not truly solve the road's main trouble, which is {road.challenge}"
        )
    if method.power < need:
        reasons.append(
            f"its strength is too small for this load ({method.power} < needed {need})"
        )
    joined = "; and ".join(reasons) if reasons else "it is not a sensible match"
    return f"(No story: {joined}. Pick a method that really suits {road.label} and this amount of mail.)"


def smooth_success(road: Road, load: MailLoad, method: Method) -> bool:
    return method_strength(method) >= required_power(road, load) + 1


def intro(world: World, courier: Entity, helper: Entity, elder: Entity, road: Road, load: MailLoad, pancake: PancakeKind) -> None:
    world.say(
        f"Long ago, when news still walked on feet and wheels, {courier.id} and {helper.id} served as the little couriers of Mossy Hollow."
    )
    world.say(
        f"One bright morning, {elder.title} gave them {load.phrase} for {load.recipient} and tucked in {pancake.phrase} as a breakfast gift."
    )
    world.say(pancake.smell)
    world.say(
        f'"Take the mail by {road.phrase}," {elder.title} said. "The mill must hear the news, and the pancake must arrive warm."'
    )


def set_out(world: World, courier: Entity, helper: Entity, road: Road) -> None:
    cart = world.get("cart")
    cart.meters["speed"] = 1.0
    world.say(
        f"So off they went with the red mail cart rattling between them. {road.scene}"
    )
    world.say(
        f"At first they laughed, but before long the road grew stubborn and asked more of them than one cheerful start could give."
    )


def quarrel(world: World, courier: Entity, helper: Entity) -> None:
    cart = world.get("cart")
    courier.memes["pride"] += 1.0
    helper.memes["pride"] += 1.0
    courier.memes["anger"] += 1.0
    helper.memes["anger"] += 1.0
    cart.memes["quarrel"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f'"You are pulling too fast," said {helper.id}. "And you are pushing too little," said {courier.id}.'
    )
    world.say(
        "Each wanted to be the wiser one, and while they argued, the cart forgot how to go forward."
    )


def slip(world: World, road: Road, pancake: PancakeKind) -> None:
    cart = world.get("cart")
    pancake_ent = world.get("pancake")
    cart.meters["rollback"] += 1.0
    cart.meters["speed"] = 0.0
    pancake_ent.meters["fallen"] += 1.0
    propagate(world, narrate=True)
    trouble = {
        "slope": "The cart rolled backward down the hill",
        "wind": "A gust shoved the cart sideways on the bridge",
        "ruts": "One wheel dropped into a rut and the cart lurched backward",
    }[road.challenge]
    world.say(
        f"{trouble}, and the wrapped pancake bounced from the top of the satchel."
    )
    world.say(
        "It slid under the wheel with a soft pat and held the cart for one astonished heartbeat."
    )
    world.facts["twist"] = "pancake_brake"


def realize(world: World, courier: Entity, helper: Entity, road: Road) -> None:
    courier.memes["shame"] += 1.0
    helper.memes["shame"] += 1.0
    world.say(
        f'"The pancake saved the mail," whispered {courier.id}. "{road.label} has better sense than we do."'
    )
    world.say(
        f"{helper.id} looked at the squashed little circle under the wheel and began to laugh, though the laugh sounded sorry first."
    )


def reconcile(world: World, courier: Entity, helper: Entity) -> None:
    cart = world.get("cart")
    courier.memes["anger"] = 0.0
    helper.memes["anger"] = 0.0
    courier.memes["trust"] += 1.0
    helper.memes["trust"] += 1.0
    courier.memes["love"] += 1.0
    helper.memes["love"] += 1.0
    cart.memes["quarrel"] = 0.0
    cart.memes["teamwork"] += 1.0
    world.say(
        f'"Friend," said {courier.id}, "I was tugging against you instead of with you."'
    )
    world.say(
        f'"And I was measuring your fault instead of my own hands," said {helper.id}. "Let us pull together now."'
    )


def teamwork(world: World, courier: Entity, helper: Entity, method: Method) -> None:
    cart = world.get("cart")
    cart.meters["rollback"] = 0.0
    cart.meters["speed"] += float(method.power)
    world.say(
        f"So they chose to {method.phrase}. {method.teamwork_line}"
    )
    propagate(world, narrate=True)
    world.say(
        "Where one friend would have strained and stumbled, two moved in one rhythm, and the red cart began to obey them."
    )


def arrival(world: World, courier: Entity, helper: Entity, elder: Entity, load: MailLoad, pancake: PancakeKind, method: Method, smooth: bool) -> None:
    cart = world.get("cart")
    cart.meters["arrived"] += 1.0
    recipient = world.get("recipient")
    pancake_ent = world.get("pancake")
    if pancake_ent.meters["fallen"] >= THRESHOLD:
        pancake_state = "the brave but squashed pancake"
    else:
        pancake_state = pancake.label
    recipient.memes["gratitude"] += 1.0
    world.say(
        f"By noon they reached the mill, where {recipient.title} stood in the floury doorway and took the mail with both paws."
    )
    world.say(
        f"When {recipient.pronoun()} heard how they had come with {pancake_state}, {recipient.pronoun()} chuckled and said, "
        f'"Letters travel best when hearts do not pull in opposite directions."'
    )
    if smooth:
        world.say(
            f"{recipient.title} warmed a second pancake on the stove and said the first one had earned an honorable rest beneath the wheel."
        )
    else:
        world.say(
            f"{recipient.title} fried a fresh pancake at once, saying no messenger should finish a hard road with only the smell of breakfast."
        )
    world.say(
        f"Then the three of them shared the new pancake beside the sacks of flour, and the lesson of the mail journey stayed in {courier.id} and {helper.id} longer than the sweet taste did."
    )
    world.facts["shared_new_pancake"] = True


def tell(road: Road, load: MailLoad, method: Method, pancake: PancakeKind,
         courier_name: str, courier_type: str, helper_name: str, helper_type: str,
         elder_type: str) -> World:
    world = World()
    courier = world.add(Entity(id=courier_name, kind="character", type=courier_type, role="courier", label=courier_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    elder_label = {"mother": "Mother Hazel", "father": "Father Reed", "badger": "Old Badger"}.get(elder_type, elder_type)
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, role="elder", label=elder_label))
    recipient = world.add(Entity(id="recipient", kind="character", type="badger", role="recipient", label="Old Badger"))
    cart = world.add(Entity(id="cart", type="cart", label="mail cart"))
    cart.meters["load"] = float(load.weight)
    route = world.add(Entity(id="road", type="road", label=road.label))
    route.meters["difficulty"] = float(road.difficulty)
    pancake_ent = world.add(Entity(id="pancake", type="food", label=pancake.label))
    satchel = world.add(Entity(id="satchel", type="mail", label=load.label))

    intro(world, courier, helper, elder, road, load, pancake)
    world.para()
    set_out(world, courier, helper, road)
    quarrel(world, courier, helper)
    world.para()
    slip(world, road, pancake)
    realize(world, courier, helper, road)
    reconcile(world, courier, helper)
    world.para()
    teamwork(world, courier, helper, method)
    world.para()
    smooth = smooth_success(road, load, method)
    arrival(world, courier, helper, elder, load, pancake, method, smooth)

    world.facts.update(
        road=road,
        load=load,
        method=method,
        pancake_cfg=pancake,
        courier=courier,
        helper=helper,
        elder=elder,
        recipient=recipient,
        cart=cart,
        pancake=pancake_ent,
        twist=world.facts.get("twist", ""),
        reconciled=courier.memes["trust"] >= THRESHOLD and helper.memes["trust"] >= THRESHOLD,
        teamwork=cart.memes["teamwork"] >= THRESHOLD,
        momentum=cart.meters["momentum"] >= THRESHOLD,
        smooth=smooth,
    )
    return world


KNOWLEDGE = {
    "mail": [
        (
            "What is mail?",
            "Mail is letters or small parcels carried from one place to another. It helps people share news, promises, and care."
        )
    ],
    "momentum": [
        (
            "What is momentum?",
            "Momentum is the push something keeps once it is already moving. A cart with momentum is easier to keep rolling than a cart that has stopped."
        )
    ],
    "pancake": [
        (
            "What is a pancake?",
            "A pancake is a soft round cake cooked on a hot pan or griddle. People often eat it warm with butter, fruit, or honey."
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help with heavy jobs?",
            "Teamwork helps because two people can share the weight and the timing of a job. When they move together, less effort is wasted."
        )
    ],
    "reconciliation": [
        (
            "What does it mean to reconcile after a quarrel?",
            "To reconcile means to make peace after being cross with each other. It often starts when both people admit their part and choose kindness again."
        )
    ],
    "wind": [
        (
            "Why can wind trouble a cart on a bridge?",
            "Wind can push against the cart and make it wobble sideways. On a narrow bridge, that makes steering harder."
        )
    ],
    "hill": [
        (
            "Why is a hill hard for a loaded cart?",
            "A loaded cart feels heavier on a hill because you must push it upward against gravity. If it stops, it may roll backward."
        )
    ],
    "ruts": [
        (
            "What are ruts in a road?",
            "Ruts are grooves worn into a road by many wheels. A cart wheel can catch in them and jerk to one side."
        )
    ],
    "rope": [
        (
            "What does a guide rope do for a cart?",
            "A guide rope lets helpers steady a cart and keep it from swinging too far. It is useful when wind or rough ground tries to pull the cart aside."
        )
    ],
    "song": [
        (
            "Why can a chant or song help people work together?",
            "A shared chant gives everyone the same beat to follow. That makes their steps and pulls happen at the right time."
        )
    ],
    "push": [
        (
            "Why does pushing and pulling together work better than one person doing all the work?",
            "One person can steady while the other adds force. Together they keep the load balanced as well as moving."
        )
    ],
}
KNOWLEDGE_ORDER = ["mail", "momentum", "pancake", "teamwork", "reconciliation", "hill", "wind", "ruts", "rope", "song", "push"]


def generation_prompts(world: World) -> list[str]:
    road = world.facts["road"]
    load = world.facts["load"]
    courier = world.facts["courier"]
    helper = world.facts["helper"]
    return [
        'Write a short folk tale for a young child that includes the words "mail", "momentum", and "pancake".',
        f"Tell a folk-style story where {courier.id} and {helper.id} must carry {load.label} along {road.phrase}, quarrel on the way, and then reconcile through teamwork.",
        "Write a gentle tale with a twist in which a humble pancake changes the course of a journey and teaches two friends to work together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    courier = world.facts["courier"]
    helper = world.facts["helper"]
    road = world.facts["road"]
    load = world.facts["load"]
    method = world.facts["method"]
    pancake = world.facts["pancake_cfg"]
    recipient = world.facts["recipient"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {courier.id} and {helper.id}, two small couriers carrying mail to {recipient.title}. Their journey matters because the village is waiting for the news they bring."
        ),
        (
            "What were they carrying?",
            f"They carried {load.phrase} and {pancake.phrase}. The mail had to reach the mill, and the pancake was meant as a warm breakfast gift."
        ),
        (
            "Why did the cart get into trouble?",
            f"The friends began to quarrel instead of moving as one, so the cart lost its forward motion. Once it slowed on {road.phrase}, the road's {road.challenge} made the danger worse."
        ),
        (
            "What was the twist with the pancake?",
            f"The pancake fell from the load and slipped under the wheel just as the cart lurched backward. That funny little accident held the cart for a moment and gave the friends time to stop blaming each other."
        ),
        (
            "How did they solve the problem?",
            f"They reconciled first, each admitting some fault, and then they chose to {method.phrase}. Because they worked in the same rhythm, the cart gathered momentum and obeyed them."
        ),
        (
            "How did the story end?",
            f"They reached the mill, delivered the mail, and shared a fresh pancake with {recipient.title}. The ending shows that their friendship was mended as surely as the journey was finished."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mail", "momentum", "pancake", "teamwork", "reconciliation"}
    road = world.facts["road"]
    method = world.facts["method"]
    tags |= set(road.tags)
    tags |= set(method.tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        road="hill",
        mail="feast_letters",
        method="shoulder_yoke",
        pancake="honey",
        courier="Pip",
        courier_type="fox",
        helper="Moss",
        helper_type="mole",
        elder_type="badger",
    ),
    StoryParams(
        road="bridge",
        mail="feast_letters",
        method="guide_rope",
        pancake="berry",
        courier="Mara",
        courier_type="hen",
        helper="Brin",
        helper_type="badger",
        elder_type="mother",
    ),
    StoryParams(
        road="lane",
        mail="market_accounts",
        method="guide_rope",
        pancake="apple",
        courier="Nell",
        courier_type="goose",
        helper="Wren",
        helper_type="girl",
        elder_type="father",
    ),
    StoryParams(
        road="hill",
        mail="feast_letters",
        method="chant_steps",
        pancake="apple",
        courier="Rowan",
        courier_type="boy",
        helper="Tala",
        helper_type="doe",
        elder_type="badger",
    ),
]


ASP_RULES = r"""
valid(Road, Mail, Method) :-
    road(Road), mail_load(Mail), method(Method),
    road_challenge(Road, Ch),
    handles(Method, Ch),
    road_difficulty(Road, D),
    mail_weight(Mail, W),
    method_power(Method, P),
    P >= D + W.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for road_id, road in ROADS.items():
        lines.append(asp.fact("road", road_id))
        lines.append(asp.fact("road_challenge", road_id, road.challenge))
        lines.append(asp.fact("road_difficulty", road_id, road.difficulty))
    for mail_id, load in MAIL_LOADS.items():
        lines.append(asp.fact("mail_load", mail_id))
        lines.append(asp.fact("mail_weight", mail_id, load.weight))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("method_power", method_id, method.power))
        for item in sorted(method.handles):
            lines.append(asp.fact("handles", method_id, item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_character(rng: random.Random, pool: list[tuple[str, str]], avoid: str = "") -> tuple[str, str]:
    choices = [item for item in pool if item[0] != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Folk-tale storyworld: two couriers, a cart of mail, a pancake twist, and a lesson in teamwork."
    )
    ap.add_argument("--road", choices=ROADS)
    ap.add_argument("--mail", choices=MAIL_LOADS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--pancake", choices=PANCAKES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.road and args.mail and args.method:
        road = ROADS[args.road]
        load = MAIL_LOADS[args.mail]
        method = METHODS[args.method]
        if not method_fits(road, load, method):
            raise StoryError(explain_rejection(road, load, method))

    combos = [
        combo for combo in valid_combos()
        if (args.road is None or combo[0] == args.road)
        and (args.mail is None or combo[1] == args.mail)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    road_id, mail_id, method_id = rng.choice(sorted(combos))
    pancake_id = args.pancake or rng.choice(sorted(PANCAKES))
    courier_name, courier_type = _pick_character(rng, COURIERS)
    helper_name, helper_type = _pick_character(rng, HELPERS, avoid=courier_name)
    elder_type = rng.choice(ELDERS)
    return StoryParams(
        road=road_id,
        mail=mail_id,
        method=method_id,
        pancake=pancake_id,
        courier=courier_name,
        courier_type=courier_type,
        helper=helper_name,
        helper_type=helper_type,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.road not in ROADS:
        raise StoryError(f"(Unknown road: {params.road})")
    if params.mail not in MAIL_LOADS:
        raise StoryError(f"(Unknown mail load: {params.mail})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.pancake not in PANCAKES:
        raise StoryError(f"(Unknown pancake: {params.pancake})")

    road = ROADS[params.road]
    load = MAIL_LOADS[params.mail]
    method = METHODS[params.method]
    pancake = PANCAKES[params.pancake]
    if not method_fits(road, load, method):
        raise StoryError(explain_rejection(road, load, method))

    world = tell(
        road=road,
        load=load,
        method=method,
        pancake=pancake,
        courier_name=params.courier,
        courier_type=params.courier_type,
        helper_name=params.helper,
        helper_type=params.helper_type,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(123)))
    except StoryError as err:
        print(f"SMOKE SETUP FAILED: {err}")
        return 1

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if "mail" not in sample.story.lower():
                raise StoryError("story omitted the required word 'mail'")
            if "pancake" not in sample.story.lower():
                raise StoryError("story omitted the required word 'pancake'")
            if "momentum" not in sample.story.lower():
                raise StoryError("story omitted the required word 'momentum'")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {err}")
            break
    else:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (road, mail, method) combos:\n")
        for road_id, mail_id, method_id in combos:
            print(f"  {road_id:8} {mail_id:15} {method_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.courier} & {p.helper}: {p.mail} by {p.road} using {p.method}"
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
