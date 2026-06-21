#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chariot_retain_reinforce_bus_depot_suspense_bravery.py
=================================================================================

A standalone story world for a folk-tale-style bus depot story about suspense,
bravery, and wise action.

The core tale:
    At a bus depot, a child and an elder wait beside a baggage cart the elder
    fondly calls a little chariot. A gust or a slick slope sets the cart
    rolling toward the bus lane just as a bus arrives. The child must not be
    reckless. The good ending comes from brave, sensible action: retain calm,
    use a proper stopping method, and let a porter reinforce the effort.

This world models:
- physical meters: rolling, danger, stopped, spilled
- emotional memes: fear, bravery, relief, pride, trust
- a reasonableness gate for compatible depot setups and sensible responses
- an ASP twin that mirrors the Python gate and outcome model
- three Q&A sets grounded in world state rather than parsing English text
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle", "porter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        aliases = {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }
        return aliases.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    opening: str
    weather_line: str
    push_line: str
    risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    precious_line: str
    ending_line: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ChariotKind:
    id: str
    label: str
    phrase: str
    weight: int
    brake_ready: bool
    lane_distance: str
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
    scene: str
    cargo: str
    chariot: str
    response: str
    child_name: str
    child_gender: str
    elder_type: str
    porter_name: str
    trait: str
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


def _r_rolling_danger(world: World) -> list[str]:
    cart = world.entities.get("chariot")
    depot = world.entities.get("depot")
    child = world.entities.get("child")
    cargo = world.entities.get("cargo")
    if not cart or cart.meters["rolling"] < THRESHOLD:
        return []
    sig = ("rolling_danger", "chariot")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if depot:
        depot.meters["danger"] += 1
    if child:
        child.memes["fear"] += 1
        child.memes["bravery"] += 1
    if cargo:
        cargo.meters["at_risk"] += 1
    return ["__danger__"]


def _r_spill_loss(world: World) -> list[str]:
    cart = world.entities.get("chariot")
    cargo = world.entities.get("cargo")
    child = world.entities.get("child")
    if not cart or not cargo:
        return []
    if cart.meters["tipped"] < THRESHOLD:
        return []
    sig = ("spill_loss", "cargo")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["spilled"] += 1
    if child:
        child.memes["sadness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="rolling_danger", tag="physical", apply=_r_rolling_danger),
    Rule(name="spill_loss", tag="physical", apply=_r_spill_loss),
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


SCENES = {
    "windy_twilight": Scene(
        id="windy_twilight",
        opening="At the edge of evening, the bus depot stood like a yard of iron giants and whispering lamps.",
        weather_line="A restless wind went between the benches and made paper scraps skitter like pale mice.",
        push_line="Then the wind gave the little depot chariot a sly shove.",
        risk=1,
        tags={"wind", "bus_depot"},
    ),
    "rainy_dawn": Scene(
        id="rainy_dawn",
        opening="At dawn, when the depot lamps still glowed gold, the bus depot smelled of rain and warm engine breath.",
        weather_line="Rain clicked on the roof, and the stone floor held a thin, shining slickness.",
        push_line="Then one wheel slid on the wet stones, and the little depot chariot began to glide.",
        risk=1,
        tags={"rain", "bus_depot"},
    ),
    "foggy_night": Scene(
        id="foggy_night",
        opening="Late at night, the bus depot lay in fog, and each lamp looked like a moon caught low to the ground.",
        weather_line="The lane sloped gently toward the road, quiet enough to hide trouble until it moved.",
        push_line="Then the sloping ground woke the little depot chariot and sent it rolling.",
        risk=2,
        tags={"fog", "bus_depot"},
    ),
}

CARGOES = {
    "medicine_case": Cargo(
        id="medicine_case",
        label="medicine case",
        phrase="a satchel of medicine wrapped in oilcloth",
        precious_line="The satchel held medicine for a sick baker across the river, so every moment mattered.",
        ending_line="The medicine reached the baker before the night was old.",
        fragile=False,
        tags={"medicine", "helping"},
    ),
    "letter_bundle": Cargo(
        id="letter_bundle",
        label="letter bundle",
        phrase="a tied bundle of letters with blue string",
        precious_line="Inside lay letters carrying good news and homesick words, and the elder said hearts were waiting for them.",
        ending_line="Before long, the letters rode out to meet the hands that needed them.",
        fragile=False,
        tags={"letters", "message"},
    ),
    "seed_crate": Cargo(
        id="seed_crate",
        label="seed crate",
        phrase="a crate of spring seeds in little paper packets",
        precious_line="The crate held seeds for the market gardeners, and the elder said next season's green hope slept inside.",
        ending_line="Soon the seed packets were stacked safely for the morning bus.",
        fragile=True,
        tags={"seeds", "garden"},
    ),
}

CHARIOTS = {
    "brake_cart": ChariotKind(
        id="brake_cart",
        label="handcart",
        phrase="an old baggage handcart with a brass brake lever",
        weight=1,
        brake_ready=True,
        lane_distance="near the painted safety line",
        tags={"brake", "cart"},
    ),
    "mail_trolley": ChariotKind(
        id="mail_trolley",
        label="mail trolley",
        phrase="a narrow mail trolley with high wheels and a creaking handle",
        weight=2,
        brake_ready=False,
        lane_distance="halfway between the benches and the lane",
        tags={"trolley", "cart"},
    ),
    "trunk_wagon": ChariotKind(
        id="trunk_wagon",
        label="trunk wagon",
        phrase="a stout trunk wagon with broad wooden sides",
        weight=2,
        brake_ready=False,
        lane_distance="so close to the bus lane that a grown-up had to mind it carefully",
        tags={"wagon", "cart"},
    ),
}

RESPONSES = {
    "brake_lever": Response(
        id="brake_lever",
        sense=3,
        power=3,
        text="caught the brass brake lever with both hands while {porter} ran in to reinforce the pull, and together they dragged the wheels to a squealing halt",
        fail="caught the brass brake lever, but the rolling weight was too strong and the handle jerked free before {porter} could reinforce the pull",
        qa_text="pulled the brake lever and, with the porter reinforcing the effort, stopped the cart",
        tags={"brake", "porter"},
    ),
    "wheel_chock": Response(
        id="wheel_chock",
        sense=3,
        power=2,
        text="snatched the wooden chock from beside the post and jammed it under the wheel as {porter} rushed up to reinforce the block with his boot",
        fail="jammed a wooden chock under the wheel, but the cart thumped over it before {porter} could reinforce the stop",
        qa_text="wedged a wooden chock under the wheel and stopped the cart with the porter's help",
        tags={"chock", "porter"},
    ),
    "hook_pole": Response(
        id="hook_pole",
        sense=2,
        power=2,
        text="hooked the side rail with the long depot pole and held fast until {porter} came to reinforce the strain and turn the chariot aside",
        fail="hooked the side rail with the long depot pole, but the cart lurched past before {porter} could reinforce the hold",
        qa_text="caught the cart with a long hook pole and held it until the porter helped",
        tags={"hook", "porter"},
    ),
    "bare_hands": Response(
        id="bare_hands",
        sense=1,
        power=1,
        text="threw small bare hands against the wheel",
        fail="threw small bare hands against the wheel",
        qa_text="tried to stop the cart with bare hands",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Asha", "Elin", "Suri", "Mara"]
BOY_NAMES = ["Tobin", "Evan", "Rafi", "Milo", "Ilan", "Bram", "Nico", "Sami"]
PORTER_NAMES = ["Hugo", "Arun", "Marek", "Pavel", "Jon", "Oren"]
TRAITS = ["steady", "watchful", "kind", "quick-thinking", "careful", "bright"]

KNOWLEDGE = {
    "bus_depot": [
        (
            "What is a bus depot?",
            "A bus depot is a place where buses arrive, leave, and wait. People and parcels are loaded there, so everyone needs to watch carefully."
        )
    ],
    "wind": [
        (
            "Why can wind move a cart?",
            "A strong wind can push a light or unguarded cart, especially if the wheels can turn easily. Once the cart starts moving, it can roll farther on its own."
        )
    ],
    "rain": [
        (
            "Why are wet stones slippery?",
            "Rain can leave a thin layer of water on stone, and that makes it easier for wheels or shoes to slide. That is why people walk more carefully on wet ground."
        )
    ],
    "fog": [
        (
            "Why does fog make things feel suspenseful?",
            "Fog hides shapes and sounds, so you may notice trouble later than usual. When you cannot see clearly, being calm and careful matters even more."
        )
    ],
    "brake": [
        (
            "What does a brake do?",
            "A brake helps slow or stop a wheel so a cart cannot keep rolling. It is a safe tool because it works on the cart instead of asking a person to stand in danger."
        )
    ],
    "chock": [
        (
            "What is a wheel chock?",
            "A wheel chock is a block placed snugly against a wheel so it cannot roll. It is a simple way to keep a cart still."
        )
    ],
    "hook": [
        (
            "What is a hook pole used for?",
            "A hook pole lets a worker catch or steer something from a safer distance. That way, hands and feet do not have to go too close to moving wheels."
        )
    ],
    "porter": [
        (
            "What does a porter do at a depot?",
            "A porter helps carry bags and move cargo safely. A porter also watches for trouble and helps keep travelers and parcels out of danger."
        )
    ],
    "medicine": [
        (
            "Why is delivering medicine important?",
            "Medicine can help a sick person feel better or stay safe. When medicine is delayed, someone who needs help may have to wait longer."
        )
    ],
    "letters": [
        (
            "Why can letters matter so much?",
            "Letters can carry news, love, and comfort from far away. Even though they are made of paper, they can mean a great deal to the people waiting for them."
        )
    ],
    "seeds": [
        (
            "Why are seeds precious?",
            "Seeds can grow into plants that feed people and fill gardens. A small packet can hold a whole season of hope."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "bus_depot", "wind", "rain", "fog", "brake", "chock", "hook", "porter",
    "medicine", "letters", "seeds",
]


def hazard_at_risk(scene: Scene, chariot: ChariotKind) -> bool:
    return scene.risk >= 1 and chariot.weight >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for cargo_id in CARGOES:
            for chariot_id, chariot in CHARIOTS.items():
                if hazard_at_risk(scene, chariot):
                    combos.append((scene_id, cargo_id, chariot_id))
    return combos


def response_power(response: Response, chariot: ChariotKind) -> int:
    bonus = 1 if response.id == "brake_lever" and chariot.brake_ready else 0
    return response.power + bonus


def severity(scene: Scene, chariot: ChariotKind, delay: int) -> int:
    return scene.risk + chariot.weight + delay


def contains_roll(response: Response, scene: Scene, chariot: ChariotKind, delay: int) -> bool:
    return response_power(response, chariot) >= severity(scene, chariot, delay)


def predict_roll(world: World, response_id: str) -> dict:
    sim = world.copy()
    cart = sim.get("chariot")
    cart.meters["rolling"] += 1
    propagate(sim, narrate=False)
    scene = sim.facts["scene_cfg"]
    chariot = sim.facts["chariot_cfg"]
    response = RESPONSES[response_id]
    return {
        "danger": sim.get("depot").meters["danger"],
        "contained": contains_roll(response, scene, chariot, sim.facts["delay"]),
    }


def introduce(world: World, child: Entity, elder: Entity, porter: Entity,
              scene: Scene, cargo: Cargo, chariot: ChariotKind) -> None:
    child.memes["trust"] += 1
    world.say(scene.opening)
    world.say(
        f"There stood {child.id}, a {next(iter(child.attrs.get('traits', ['steady'])))} child, beside {child.pronoun('possessive')} "
        f"{elder.label_word}, waiting near {chariot.phrase}."
    )
    world.say(
        f'On the cart rested {cargo.phrase}, and {elder.label_word} called the old cart a little chariot because it carried hopes from one road to another.'
    )
    world.say(cargo.precious_line)
    world.say(scene.weather_line)
    world.facts["porter_label"] = porter.id


def warn(world: World, child: Entity, elder: Entity, scene: Scene, chariot: ChariotKind) -> None:
    pred = predict_roll(world, world.facts["response"].id)
    child.memes["fear"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{elder.label_word.capitalize()} glanced at the wheels and said, "Retain your courage, {child.id}, and keep behind the line. Trouble loves quick feet more than wise ones."'
    )
    if chariot.brake_ready:
        world.say(
            f'{elder.pronoun().capitalize()} nodded toward the brass lever. "If the chariot stirs, we stop the wheel, not the child."'
        )
    else:
        world.say(
            f'{elder.pronoun().capitalize()} nodded toward the depot tools. "If the chariot stirs, we use wood or pole before we use hands."'
        )


def trigger(world: World, scene: Scene, chariot_ent: Entity) -> None:
    chariot_ent.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(scene.push_line)
    world.say(
        f"It rolled from its place, {world.facts['chariot_cfg'].lane_distance}, while the great road chariot of the evening bus grumbled toward the platform."
    )


def gasp(world: World, child: Entity, cargo: Cargo) -> None:
    world.say(
        f"{child.id}'s breath caught. The {cargo.label} was on the moving cart, and for one sharp heartbeat the whole depot seemed to listen."
    )


def brave_choice(world: World, child: Entity, elder: Entity, response: Response) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} wanted to dash straight at the wheel, yet {child.pronoun()} remembered the warning and chose the wiser path."
    )
    if response.id == "bare_hands":
        world.say(
            f"But that choice would ask a child to stand where iron and speed could win."
        )
    else:
        world.say(
            f"{child.pronoun().capitalize()} did not forget to retain calm even while fear beat fast in {child.pronoun('possessive')} chest."
        )


def rescue(world: World, child: Entity, elder: Entity, porter: Entity,
           response: Response, chariot_ent: Entity, cargo_ent: Entity) -> None:
    chariot_ent.meters["rolling"] = 0.0
    chariot_ent.meters["stopped"] += 1
    world.get("depot").meters["danger"] = 0.0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    elder.memes["relief"] += 1
    porter.memes["relief"] += 1
    body = response.text.format(porter=porter.id)
    world.say(f"{child.id} {body}.")
    world.say(
        f'The wheel shuddered once, twice, and then stood still. "{child.id}," said {elder.label_word}, "that was true bravery, because you were bold enough to be wise."'
    )
    world.say(
        f"{porter.id} smiled and dusted his hands. He said he had only come to reinforce a brave beginning that had already been chosen well."
    )


def rescue_fail(world: World, child: Entity, elder: Entity, porter: Entity,
                response: Response, chariot_ent: Entity, cargo_ent: Entity) -> None:
    chariot_ent.meters["rolling"] += 1
    chariot_ent.meters["tipped"] += 1
    propagate(world, narrate=False)
    child.memes["fear"] += 1
    elder.memes["fear"] += 1
    body = response.fail.format(porter=porter.id)
    world.say(f"{child.id} {body}.")
    world.say(
        "The cart lurched, kissed the edge of the lane, and tipped with a hard wooden thump."
    )
    if cargo_ent.meters["spilled"] >= THRESHOLD:
        world.say(
            f"The {world.facts['cargo_cfg'].label} spilled across the stones, and everyone jumped back from the wheels."
        )


def lesson(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["love"] += 1
    elder.memes["love"] += 1
    world.say(
        f'{elder.label_word.capitalize()} drew {child.id} close. "A brave heart must retain its sense," {elder.pronoun()} said softly. "That is how it can help the world instead of merely frightening it."'
    )
    world.say(
        f"{child.id} nodded and looked at the {cargo.label}, now safe again, as if seeing courage in a clearer shape."
    )
    world.say(cargo.ending_line)


def sad_lesson(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["love"] += 1
    elder.memes["love"] += 1
    child.memes["relief"] += 1
    world.say(
        f'{elder.label_word.capitalize()} held {child.id} by the shoulders and said, "The brave do not leap into every danger. They learn, and next time they choose better still."'
    )
    world.say(
        f"{child.id} was glad no one had been struck by the wheels, though the {cargo.label} lay in a sad scatter on the stones."
    )
    if cargo.id == "medicine_case":
        world.say("The porter gathered the satchel quickly so another bus could still carry help onward.")
    elif cargo.id == "letter_bundle":
        world.say("The elder and porter gathered every letter and tied the blue string again, slower and more carefully this time.")
    else:
        world.say("The elder and porter saved what seeds they could and promised to reinforce the crate before dawn came again.")


def tell(scene: Scene, cargo: Cargo, chariot: ChariotKind, response: Response,
         child_name: str = "Lina", child_gender: str = "girl", elder_type: str = "grandmother",
         porter_name: str = "Hugo", trait: str = "steady", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        attrs={"traits": [trait]},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    porter = world.add(Entity(
        id=porter_name,
        kind="character",
        type="porter",
        role="porter",
    ))
    depot = world.add(Entity(
        id="depot",
        type="place",
        label="the bus depot",
    ))
    cargo_ent = world.add(Entity(
        id="cargo",
        type="cargo",
        label=cargo.label,
        phrase=cargo.phrase,
    ))
    chariot_ent = world.add(Entity(
        id="chariot",
        type="cart",
        label=chariot.label,
        phrase=chariot.phrase,
    ))

    world.facts.update(
        scene_cfg=scene,
        cargo_cfg=cargo,
        chariot_cfg=chariot,
        response=response,
        delay=delay,
        child=child,
        elder=elder,
        porter=porter,
        cargo=cargo_ent,
        chariot=chariot_ent,
    )

    introduce(world, child, elder, porter, scene, cargo, chariot)
    world.para()
    warn(world, child, elder, scene, chariot)
    trigger(world, scene, chariot_ent)
    gasp(world, child, cargo)
    brave_choice(world, child, elder, response)

    world.para()
    win = contains_roll(response, scene, chariot, delay)
    if win:
        rescue(world, child, elder, porter, response, chariot_ent, cargo_ent)
        lesson(world, child, elder, cargo)
    else:
        rescue_fail(world, child, elder, porter, response, chariot_ent, cargo_ent)
        sad_lesson(world, child, elder, cargo)

    outcome = "saved" if win else "spilled"
    world.facts.update(
        outcome=outcome,
        stopped=chariot_ent.meters["stopped"] >= THRESHOLD,
        spilled=cargo_ent.meters["spilled"] >= THRESHOLD,
        severity=severity(scene, chariot, delay),
        predicted_stop=contains_roll(response, scene, chariot, delay),
    )
    return world


def pair_description(child: Entity, elder: Entity) -> str:
    return f"{child.id} and {child.pronoun('possessive')} {elder.label_word}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    scene = f["scene_cfg"]
    cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a folk-tale-style story for a 3-to-5-year-old set in a bus depot. '
        f'Include the words "chariot", "retain", and "reinforce", and build suspense around a child who chooses wise bravery.'
    )
    if outcome == "saved":
        return [
            base,
            f"Tell a gentle suspense story where {child.id} and {child.pronoun('possessive')} {elder.label_word} watch a rolling baggage cart carrying {cargo.phrase}, and the child helps stop it safely.",
            f"Write a bus depot folk tale in which a child retains calm, a porter comes to reinforce the effort, and the ending proves that brave thinking is better than reckless jumping.",
        ]
    return [
        base,
        f"Tell a cautionary folk tale where {cargo.phrase} rides on a little depot chariot, trouble begins in {scene.id.replace('_', ' ')}, and the child learns that bravery must be guided by sense.",
        f"Write a suspenseful bus depot story where a child tries to help, a cart tips, nobody is hurt, and the ending teaches a wiser kind of courage.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    porter = f["porter"]
    cargo = f["cargo_cfg"]
    chariot = f["chariot_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.label_word}, and {porter.id} at the bus depot. They are all caught in the moment when a little cargo cart begins to roll."
        ),
        (
            "What was on the little chariot?",
            f"The little chariot carried {cargo.phrase}. It mattered because {cargo.precious_line[0].lower() + cargo.precious_line[1:]}"
        ),
        (
            "Why did the moment feel suspenseful?",
            f"The cart began rolling toward the bus lane just as a bus was coming in. That made everyone fear the cargo could be lost and someone could be hurt if the wheels were not stopped quickly."
        ),
        (
            f"What did the elder tell {child.id} to do?",
            f'The elder told {child.id} to retain courage and stay behind the line. The warning mattered because wise bravery uses the right tool instead of running straight into danger.'
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                f"How was the rolling cart stopped?",
                f"{child.id} used {response.qa_text}. The porter came to reinforce the effort, so the wheel stopped before the cart reached the lane."
            )
        )
        qa.append(
            (
                f"Why was {child.id} called brave?",
                f"{child.id} was brave because {child.pronoun()} felt fear and still chose the safer action. The story says true bravery means being bold enough to be wise."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the cargo safe and the danger gone. The final image shows the precious {cargo.label} ready to continue its journey because the child kept calm."
            )
        )
    else:
        qa.append(
            (
                "Did anyone get hurt when the cart tipped?",
                "No, no one was struck by the wheels. The sad part was the spilled cargo, but the people stepped back in time."
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned that bravery must retain its sense. The lesson came from seeing that wanting to help is not enough unless the way of helping is wise."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with everyone safe but the {cargo.label} spilled on the stones. The ending feels sober because the child gains a lesson instead of a perfect rescue."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["scene_cfg"].tags) | set(f["cargo_cfg"].tags) | set(f["response"].tags)
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="windy_twilight",
        cargo="medicine_case",
        chariot="brake_cart",
        response="brake_lever",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
        porter_name="Hugo",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        scene="rainy_dawn",
        cargo="letter_bundle",
        chariot="mail_trolley",
        response="wheel_chock",
        child_name="Rafi",
        child_gender="boy",
        elder_type="grandfather",
        porter_name="Arun",
        trait="watchful",
        delay=0,
    ),
    StoryParams(
        scene="foggy_night",
        cargo="seed_crate",
        chariot="trunk_wagon",
        response="hook_pole",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        porter_name="Marek",
        trait="quick-thinking",
        delay=1,
    ),
]


def explain_rejection(scene: Scene, chariot: ChariotKind) -> str:
    return (
        f"(No story: {scene.id.replace('_', ' ')} with {chariot.label} gives no grounded rolling danger here. "
        f"The world only tells stories where a cart could reasonably roll and make the bus lane unsafe.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Brave stories here prefer safer depot tools. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    scene = SCENES[params.scene]
    chariot = CHARIOTS[params.chariot]
    response = RESPONSES[params.response]
    return "saved" if contains_roll(response, scene, chariot, params.delay) else "spilled"


ASP_RULES = r"""
hazard(S, Ch) :- scene(S), chariot(Ch), risk(S, R), weight(Ch, W), R >= 1, W >= 1.
valid(S, Cg, Ch) :- scene(S), cargo(Cg), chariot(Ch), hazard(S, Ch).

sensible(Rp) :- response(Rp), sense(Rp, S), sense_min(M), S >= M.

bonus(Rp, Ch, 1) :- chosen_response(Rp), chosen_chariot(Ch), brake_ready(Ch), Rp = brake_lever.
bonus(Rp, Ch, 0) :- chosen_response(Rp), chosen_chariot(Ch), not brake_ready(Ch).
bonus(Rp, Ch, 0) :- chosen_response(Rp), chosen_chariot(Ch), Rp != brake_lever.

effective_power(P + B) :- chosen_response(Rp), base_power(Rp, P), chosen_chariot(Ch), bonus(Rp, Ch, B).
need(R + W + D) :- chosen_scene(S), risk(S, R), chosen_chariot(Ch), weight(Ch, W), delay(D).

outcome(saved) :- effective_power(P), need(N), P >= N.
outcome(spilled) :- effective_power(P), need(N), P < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        lines.append(asp.fact("risk", scene_id, scene.risk))
    for cargo_id in CARGOES:
        lines.append(asp.fact("cargo", cargo_id))
    for chariot_id, chariot in CHARIOTS.items():
        lines.append(asp.fact("chariot", chariot_id))
        lines.append(asp.fact("weight", chariot_id, chariot.weight))
        if chariot.brake_ready:
            lines.append(asp.fact("brake_ready", chariot_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("base_power", response_id, response.power))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_scene", params.scene),
        asp.fact("chosen_chariot", params.chariot),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a brave child, a rolling depot chariot, and the wiser way to help."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--chariot", choices=CHARIOTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start the rolling cart gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.chariot:
        scene = SCENES[args.scene]
        chariot = CHARIOTS[args.chariot]
        if not hazard_at_risk(scene, chariot):
            raise StoryError(explain_rejection(scene, chariot))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.chariot is None or combo[2] == args.chariot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, cargo_id, chariot_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_child(rng)
    porter_name = rng.choice(PORTER_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        scene=scene_id,
        cargo=cargo_id,
        chariot=chariot_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        porter_name=porter_name,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        scene = SCENES[params.scene]
        cargo = CARGOES[params.cargo]
        chariot = CHARIOTS[params.chariot]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter value: {exc.args[0]}.)") from exc

    if not hazard_at_risk(scene, chariot):
        raise StoryError(explain_rejection(scene, chariot))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        scene=scene,
        cargo=cargo,
        chariot=chariot,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        porter_name=params.porter_name,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (scene, cargo, chariot) combos:\n")
        for scene_id, cargo_id, chariot_id in combos:
            print(f"  {scene_id:15} {cargo_id:14} {chariot_id}")
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
            header = f"### {p.child_name}: {p.scene} / {p.cargo} / {p.chariot} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
