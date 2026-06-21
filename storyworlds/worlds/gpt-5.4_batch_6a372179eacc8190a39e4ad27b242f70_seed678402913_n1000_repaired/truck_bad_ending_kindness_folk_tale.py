#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/truck_bad_ending_kindness_folk_tale.py
=================================================================

A small folk-tale storyworld about a village child, a stranded truck, and a
kind attempt to help on a dangerous road. The central tension is simple and
state-driven: a truck carrying goods meets mud, darkness, or a weak bridge; a
child offers practical kindness; sometimes the kindness is enough, and
sometimes the people are saved while the truck and cargo are lost.

The world prefers a narrow set of plausible stories over broad coverage.
Helpers must actually match the road's danger, and obviously foolish responses
are refused. The inline ASP twin mirrors both the compatibility gate and the
outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/truck_bad_ending_kindness_folk_tale.py
    python storyworlds/worlds/gpt-5.4/truck_bad_ending_kindness_folk_tale.py --road river_bridge
    python storyworlds/worlds/gpt-5.4/truck_bad_ending_kindness_folk_tale.py --aid lantern --road muddy_hill
    python storyworlds/worlds/gpt-5.4/truck_bad_ending_kindness_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/truck_bad_ending_kindness_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/truck_bad_ending_kindness_folk_tale.py --verify
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
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "grandmother":
            return "grandmother"
        return self.type


@dataclass
class Road:
    id: str
    label: str
    phrase: str
    danger: str
    need: str
    severity: int
    sight: str
    warning: str
    fail: str
    saved: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    fragility: int
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    act: str = ""
    comfort: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    power: int
    universal: bool = False
    needs_matching_aid: bool = False
    try_line: str = ""
    success_line: str = ""
    fail_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    road: str
    cargo: str
    aid: str
    response: str
    child_name: str
    child_type: str
    driver_name: str
    driver_type: str
    elder_type: str
    weather: int = 1
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


def _r_worry(world: World) -> list[str]:
    truck = world.get("truck")
    child = world.get("child")
    driver = world.get("driver")
    road = world.get("road")
    if truck.meters["risk"] < THRESHOLD:
        return []
    sig = ("worry", truck.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    driver.memes["fear"] += 1
    road.meters["danger"] += 1
    return []


def _r_loss(world: World) -> list[str]:
    truck = world.get("truck")
    cargo = world.get("cargo")
    driver = world.get("driver")
    child = world.get("child")
    if truck.meters["lost"] < THRESHOLD:
        return []
    sig = ("loss", truck.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["lost"] += 1
    driver.memes["grief"] += 1
    child.memes["sorrow"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="loss", tag="physical", apply=_r_loss),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ROADS = {
    "muddy_hill": Road(
        id="muddy_hill",
        label="muddy hill road",
        phrase="a clay hill road above the little fields",
        danger="mud",
        need="rope",
        severity=2,
        sight="The ruts were deep as soup bowls, and each wheel had sunk into the brown clay.",
        warning="the hill road liked to swallow heavy wheels after rain",
        fail="The back wheels spun, the truck slewed sideways, and at last it slid into the ditch with a broken axle.",
        saved="With the rope biting hard and the wheels moving one careful turn at a time, the truck climbed free of the clay.",
        tags={"mud", "road"},
    ),
    "river_bridge": Road(
        id="river_bridge",
        label="river bridge",
        phrase="a narrow wooden bridge over a loud brown river",
        danger="bridge",
        need="villagers",
        severity=3,
        sight="The planks bent and croaked under the truck as if the bridge were talking in its sleep.",
        warning="the old bridge was strong enough for feet and baskets, not for a loaded truck in storm season",
        fail="A plank cracked like a stick in a fire. The truck lurched, the bridge gave way beneath one side, and the load went down into the river.",
        saved="Box by box, the villagers carried the load across first, and only then did the lightened truck creep over the bridge.",
        tags={"bridge", "river"},
    ),
    "dusk_lane": Road(
        id="dusk_lane",
        label="dusk lane",
        phrase="a narrow lane between willow trees and low stone walls",
        danger="dark",
        need="lantern",
        severity=1,
        sight="Evening had folded itself between the trees, and the bends in the lane were no longer easy to read.",
        warning="the lane twisted sharply, and in bad light even a good driver could miss the edge",
        fail="The driver missed the bend, the truck bumped through the stones, and the crates burst open in the nettles below.",
        saved="The lantern shone on each turn, and the truck rolled slowly past the stones without slipping.",
        tags={"dark", "road"},
    ),
}

CARGOES = {
    "pears": Cargo(
        id="pears",
        label="pears",
        phrase="green pears from the upper orchard",
        fragility=1,
        image="A sweet smell of pears drifted from the back whenever the wind moved the tarp.",
        tags={"fruit"},
    ),
    "flour": Cargo(
        id="flour",
        label="flour sacks",
        phrase="white flour sacks for the baker",
        fragility=1,
        image="The sacks were stacked neat and square, pale as sleeping geese.",
        tags={"flour"},
    ),
    "clay_pots": Cargo(
        id="clay_pots",
        label="clay pots",
        phrase="stacked clay pots for market day",
        fragility=2,
        image="Under the tarp, the pots clicked together with a sound as thin as teeth.",
        tags={"pots"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="rope",
        phrase="a coiled hemp rope",
        helps={"mud"},
        act="ran to fetch a rope from the fig shed",
        comfort="She also brought a heel of bread wrapped in a cloth for the weary driver.",
        tags={"rope", "kindness"},
    ),
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a tin lantern with a clean yellow flame behind glass",
        helps={"dark"},
        act="hurried home for the old lantern that hung by the door",
        comfort="She tucked in two warm buns as well, because kind hands seldom carry only one thing.",
        tags={"lantern", "kindness"},
    ),
    "villagers": Aid(
        id="villagers",
        label="villagers",
        phrase="three neighbors with strong backs and patient hands",
        helps={"bridge"},
        act="ran from door to door until three neighbors came with poles and empty baskets",
        comfort="One of them brought tea in a bottle for the driver, and another laid a shawl around his shoulders.",
        tags={"villagers", "kindness"},
    ),
}

RESPONSES = {
    "use_aid": Response(
        id="use_aid",
        label="use the offered help",
        sense=3,
        power=2,
        universal=False,
        needs_matching_aid=True,
        try_line="The driver listened, swallowed his pride, and agreed to use the help the child had brought.",
        success_line="They worked slowly, just as country wisdom says heavy things must be moved.",
        fail_line="They worked with all the help they had, but the road had grown too dangerous before they began.",
        qa_line="used the child's help carefully",
        tags={"help"},
    ),
    "wait_for_morning": Response(
        id="wait_for_morning",
        label="wait for morning",
        sense=3,
        power=2,
        universal=True,
        needs_matching_aid=False,
        try_line="The child begged the driver to wait for clearer light and kinder ground, and this time he agreed.",
        success_line="They sat beside the road, sharing the small food and the thin warmth they had until the world grew safer.",
        fail_line="They waited, but all night the rain thickened and the road worsened faster than patience could mend it.",
        qa_line="waited for safer conditions",
        tags={"patience"},
    ),
    "lighten_load": Response(
        id="lighten_load",
        label="lighten the load",
        sense=3,
        power=3,
        universal=False,
        needs_matching_aid=True,
        try_line="At the child's urging, the driver agreed that a heavy truck should first become a lighter one.",
        success_line="The load was made smaller before the road was asked to bear it.",
        fail_line="They lifted what they could, but the danger was already bigger than tired arms and good intentions.",
        qa_line="lightened the truck before moving it",
        tags={"cargo"},
    ),
    "gun_engine": Response(
        id="gun_engine",
        label="gun the engine",
        sense=1,
        power=1,
        universal=True,
        needs_matching_aid=False,
        try_line="The driver stamped hard on the pedal, trusting noise more than wisdom.",
        success_line="Against good sense, the engine's roar carried the truck through.",
        fail_line="The engine roared, but roaring did not make the road kind.",
        qa_line="tried to force the truck through",
        tags={"reckless"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tala", "Nora", "Iris", "Sela", "Pia"]
BOY_NAMES = ["Tomas", "Milo", "Evan", "Niko", "Ilan", "Rafi", "Bram", "Oren"]


def aid_matches(aid: Aid, road: Road) -> bool:
    return road.danger in aid.helps


def response_allowed(response: Response, aid: Aid, road: Road) -> bool:
    if response.sense < SENSE_MIN:
        return False
    if response.universal:
        return True
    if response.id == "use_aid":
        return aid_matches(aid, road)
    if response.id == "lighten_load":
        return road.danger == "bridge" and aid.id == "villagers"
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for road_id, road in ROADS.items():
        for cargo_id in CARGOES:
            for aid_id, aid in AIDS.items():
                for response_id, response in RESPONSES.items():
                    if response_allowed(response, aid, road):
                        combos.append((road_id, cargo_id, aid_id, response_id))
    return combos


def risk_value(road: Road, cargo: Cargo, weather: int) -> int:
    return road.severity + cargo.fragility + weather


def response_power(response: Response, aid: Aid, road: Road) -> int:
    power = response.power
    if response.needs_matching_aid and aid_matches(aid, road):
        power += 1
    if response.id == "lighten_load" and road.danger == "bridge" and aid.id == "villagers":
        power += 1
    return power


def outcome_of(params: StoryParams) -> str:
    road = ROADS[params.road]
    cargo = CARGOES[params.cargo]
    aid = AIDS[params.aid]
    response = RESPONSES[params.response]
    if not response_allowed(response, aid, road):
        raise StoryError(explain_rejection(road, aid, response))
    return "saved" if response_power(response, aid, road) >= risk_value(road, cargo, params.weather) else "lost"


def explain_rejection(road: Road, aid: Aid, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it is too reckless for this world "
            f"(sense={response.sense} < {SENSE_MIN}). Choose a calmer plan.)"
        )
    if response.id == "use_aid" and not aid_matches(aid, road):
        return (
            f"(No story: {aid.label} does not solve the danger on {road.label}. "
            f"That road needs help for {road.danger}, not {aid.label}.)"
        )
    if response.id == "lighten_load" and not (road.danger == "bridge" and aid.id == "villagers"):
        return (
            "(No story: lightening a load is only a sensible plan here when "
            "neighbors can carry boxes across a weak bridge.)"
        )
    return "(No valid combination matches the given options.)"


def predict(world: World, response: Response, road: Road, cargo: Cargo, aid: Aid, weather: int) -> dict:
    sim = world.copy()
    truck = sim.get("truck")
    truck.meters["risk"] += float(risk_value(road, cargo, weather))
    if response_power(response, aid, road) < risk_value(road, cargo, weather):
        truck.meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "loss": truck.meters["lost"] >= THRESHOLD,
        "danger": risk_value(road, cargo, weather),
    }


def tale_opening(world: World, child: Entity, elder: Entity, road: Road, cargo: Cargo) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In the days when every village knew the sound of every cartwheel, {child.id} lived with "
        f"{child.pronoun('possessive')} {elder.label_word} at the edge of the fields."
    )
    world.say(
        f"One storm-bitten evening, a truck came groaning along {road.phrase}. {road.sight}"
    )
    world.say(cargo.image)


def meet_driver(world: World, child: Entity, driver: Entity, road: Road) -> None:
    driver.memes["weariness"] += 1
    world.say(
        f"At the bend stood {driver.id}, the driver, with rain on {driver.pronoun('possessive')} cap and worry in "
        f"{driver.pronoun('possessive')} face. {child.id} saw at once that {road.warning}."
    )


def feel_kindness(world: World, child: Entity, driver: Entity, aid: Aid) -> None:
    child.memes["kindness"] += 1
    driver.memes["hope"] += 1
    world.say(
        f"{child.id} was small, but {child.pronoun('possessive')} heart was not small. "
        f"{child.pronoun().capitalize()} {aid.act}."
    )
    world.say(aid.comfort)


def warn(world: World, child: Entity, driver: Entity, response: Response, road: Road, cargo: Cargo, aid: Aid, weather: int) -> None:
    pred = predict(world, response, road, cargo, aid, weather)
    world.facts["predicted_loss"] = pred["loss"]
    world.facts["predicted_danger"] = pred["danger"]
    if pred["loss"]:
        world.say(
            f'"Do not hurry," {child.id} said. "This is a hard road for a loaded truck, and tonight it may take more than goods."'
        )
    else:
        world.say(
            f'"If we go slowly and wisely," {child.id} said, "your truck may still see the village lights."'
        )


def attempt(world: World, child: Entity, driver: Entity, truck: Entity, response: Response, road: Road, cargo: Cargo, aid: Aid, weather: int) -> None:
    truck.meters["risk"] += float(risk_value(road, cargo, weather))
    world.say(response.try_line)
    if response.id == "use_aid":
        world.say(f"The {aid.label} was put to work at once.")
    elif response.id == "lighten_load":
        world.say("Hands reached for crates and sacks before anyone touched the steering wheel again.")
    elif response.id == "wait_for_morning":
        world.say("No one called patience easy, but they called it better than foolishness.")
    power = response_power(response, aid, road)
    if power >= risk_value(road, cargo, weather):
        truck.meters["saved"] += 1
        truck.meters["risk"] = 0.0
        world.say(response.success_line)
        world.say(road.saved)
    else:
        truck.meters["lost"] += 1
        propagate(world, narrate=False)
        world.say(response.fail_line)
        world.say(road.fail)


def saved_ending(world: World, child: Entity, driver: Entity, road: Road, cargo: Cargo) -> None:
    child.memes["joy"] += 1
    driver.memes["gratitude"] += 1
    world.say(
        f"When the truck at last rolled toward the village, {driver.id} climbed down and bowed low to {child.id}."
    )
    world.say(
        f'"A strong road is a good thing," {driver.pronoun()} said, "but a kind guide is better." '
        f"And the truck carried {cargo.label} safely on."
    )


def lost_ending(world: World, child: Entity, driver: Entity, truck: Entity, cargo: Entity, elder: Entity) -> None:
    child.memes["sorrow"] += 1
    driver.memes["gratitude"] += 1
    world.say(
        f"The people stepped back in time, but the truck was not so lucky. The goods were lost, and the night grew very still after the last crash."
    )
    world.say(
        f"{elder.label_word.capitalize()} came down the lane with blankets. {child.id} and {driver.id} sat beside the road, "
        f"sharing bread and tea while the ruined truck leaned in the rain."
    )
    world.say(
        f"From that night on, the village told the tale this way: kindness can save a person even when it cannot save a truck."
    )


def tell(
    road: Road,
    cargo_cfg: Cargo,
    aid: Aid,
    response: Response,
    child_name: str,
    child_type: str,
    driver_name: str,
    driver_type: str,
    elder_type: str,
    weather: int,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, phrase=child_name, role="child"))
    driver = world.add(Entity(id="driver", kind="character", type=driver_type, label=driver_name, phrase=driver_name, role="driver"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, phrase=elder_type, role="elder"))
    truck = world.add(Entity(id="truck", kind="thing", type="truck", label="truck", phrase="the truck", role="truck"))
    cargo = world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo_cfg.label, phrase=cargo_cfg.phrase, role="cargo"))
    road_ent = world.add(Entity(id="road", kind="thing", type="road", label=road.label, phrase=road.phrase, role="road"))
    aid_ent = world.add(Entity(id="aid", kind="thing", type="aid", label=aid.label, phrase=aid.phrase, role="aid"))

    tale_opening(world, child, elder, road, cargo_cfg)
    meet_driver(world, child, driver, road)

    world.para()
    feel_kindness(world, child, driver, aid)
    warn(world, child, driver, response, road, cargo_cfg, aid, weather)

    world.para()
    attempt(world, child, driver, truck, response, road, cargo_cfg, aid, weather)

    world.para()
    if truck.meters["saved"] >= THRESHOLD:
        saved_ending(world, child, driver, road, cargo_cfg)
        outcome = "saved"
    else:
        lost_ending(world, child, driver, truck, cargo, elder)
        outcome = "lost"

    world.facts.update(
        road=road,
        cargo_cfg=cargo_cfg,
        aid=aid,
        response=response,
        child=child,
        driver=driver,
        elder=elder,
        truck=truck,
        cargo=cargo,
        aid_ent=aid_ent,
        weather=weather,
        outcome=outcome,
        people_safe=True,
    )
    return world


KNOWLEDGE = {
    "truck": [
        (
            "What is a truck?",
            "A truck is a big road vehicle used to carry heavy things from one place to another. It can haul much more than a small car."
        )
    ],
    "rope": [
        (
            "What can a rope help with?",
            "A strong rope can help pull or hold heavy things. People must still use it carefully and slowly."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful at night?",
            "A lantern gives steady light, so people can see the road and where to put their feet. Good light helps them avoid mistakes."
        )
    ],
    "bridge": [
        (
            "Why can an old bridge be dangerous?",
            "Old bridges can weaken over time, especially in wet weather. Heavy weight can make boards crack or bend too far."
        )
    ],
    "mud": [
        (
            "Why do wheels get stuck in mud?",
            "Mud is soft and slippery, so heavy wheels sink down and lose their grip. Then the vehicle cannot push itself forward easily."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing someone else's trouble and trying to help. Sometimes it is a big help, and sometimes it is a small warm thing like food or light."
        )
    ],
    "patience": [
        (
            "Why can waiting be wise?",
            "Waiting can be wise when a road or a plan is dangerous. A little patience can stop a much bigger loss."
        )
    ],
    "pots": [
        (
            "Why do clay pots break easily?",
            "Clay pots are hard but brittle, so they can crack or shatter when they fall or knock together too roughly."
        )
    ],
    "fruit": [
        (
            "Why can fruit be ruined in a crash?",
            "Fruit bruises and bursts when it is thrown around hard. Even if it still smells sweet, it may no longer be fit to sell."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    road = f["road"]
    aid = f["aid"]
    child = f["child"]
    outcome = f["outcome"]
    if outcome == "lost":
        end = "ends sadly with the goods or truck lost, though kindness still saves the people"
    else:
        end = "ends with careful help saving the truck"
    return [
        f'Write a short folk tale for a young child that includes the word "truck" and {end}.',
        f"Tell a village-road story where {child.label} offers {aid.label} to a troubled driver on {road.label}, and the tale teaches that kindness matters.",
        f"Write a gentle old-fashioned story about a child helping a truck on a dangerous road, with a clear warning, a turning point, and an ending that proves what kindness could or could not save.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    driver = f["driver"]
    road = f["road"]
    cargo_cfg = f["cargo_cfg"]
    aid = f["aid"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a kind village child, and {driver.label}, a truck driver in trouble on the {road.label}. The story follows what happened when the child chose to help."
        ),
        (
            "What problem did the truck have?",
            f"The truck was in danger on the {road.label}. That road was risky because {road.warning}."
        ),
        (
            f"What kind thing did {child.label} do?",
            f"{child.label} brought {aid.phrase} and also thought about the tired driver, not just the truck. The kindness mattered because it gave help and comfort at the same time."
        ),
        (
            "What did the child warn the driver about?",
            f"{child.label} warned that the road was too dangerous for a loaded truck to be treated carelessly. The warning came from seeing the road clearly before the driver did."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How was the truck saved?",
                f"The driver {response.qa_line}, and that matched the danger on the road. Because the plan fit the problem, the truck and its {cargo_cfg.label} got through safely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the truck rolling on toward the village and the driver thanking {child.label}. The ending proves that kindness and patience together can change danger into safety."
            )
        )
    else:
        qa.append(
            (
                "Did the kindness save the truck?",
                f"No. The people were safe, but the truck and its {cargo_cfg.label} were lost. The road had become more dangerous than their help could overcome."
            )
        )
        qa.append(
            (
                "Why is the ending sad but still kind?",
                f"The ending is sad because the truck could not be saved. It is still kind because {child.label}, {f['elder'].label_word}, and the others cared for the driver after the loss instead of leaving him alone."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"truck", "kindness"}
    tags |= set(f["road"].tags)
    tags |= set(f["aid"].tags)
    tags |= set(f["cargo_cfg"].tags)
    tags |= set(f["response"].tags)
    order = ["truck", "kindness", "mud", "bridge", "rope", "lantern", "patience", "pots", "fruit"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        road="muddy_hill",
        cargo="pears",
        aid="rope",
        response="use_aid",
        child_name="Mira",
        child_type="girl",
        driver_name="Tomas",
        driver_type="man",
        elder_type="grandmother",
        weather=1,
    ),
    StoryParams(
        road="river_bridge",
        cargo="clay_pots",
        aid="villagers",
        response="lighten_load",
        child_name="Anya",
        child_type="girl",
        driver_name="Milo",
        driver_type="man",
        elder_type="grandmother",
        weather=2,
    ),
    StoryParams(
        road="dusk_lane",
        cargo="flour",
        aid="lantern",
        response="wait_for_morning",
        child_name="Niko",
        child_type="boy",
        driver_name="Evan",
        driver_type="man",
        elder_type="grandmother",
        weather=1,
    ),
    StoryParams(
        road="river_bridge",
        cargo="flour",
        aid="villagers",
        response="use_aid",
        child_name="Lina",
        child_type="girl",
        driver_name="Bram",
        driver_type="man",
        elder_type="grandmother",
        weather=2,
    ),
    StoryParams(
        road="dusk_lane",
        cargo="clay_pots",
        aid="lantern",
        response="use_aid",
        child_name="Rafi",
        child_type="boy",
        driver_name="Oren",
        driver_type="man",
        elder_type="grandmother",
        weather=2,
    ),
]


ASP_RULES = r"""
matching_aid(A, R) :- aid(A), road(R), helps(A, D), danger(R, D).

allowed(A, R, use_aid) :- matching_aid(A, R).
allowed(A, R, wait_for_morning) :- aid(A), road(R).
allowed(villagers, river_bridge, lighten_load).

valid(R, C, A, Resp) :- road(R), cargo(C), aid(A), response(Resp), sensible(Resp), allowed(A, R, Resp).
sensible(Resp) :- response(Resp), sense(Resp, S), sense_min(M), S >= M.

power_total(use_aid, A, R, P + 1) :- matching_aid(A, R), base_power(use_aid, P).
power_total(use_aid, A, R, P) :- base_power(use_aid, P), not matching_aid(A, R).
power_total(wait_for_morning, A, R, P) :- aid(A), road(R), base_power(wait_for_morning, P).
power_total(lighten_load, villagers, river_bridge, P + 1) :- base_power(lighten_load, P).
power_total(lighten_load, A, R, 0) :- aid(A), road(R), (A != villagers; R != river_bridge).

risk_total(R, C, W, S + F + W) :- severity(R, S), fragility(C, F), weather(W).
saved(R, C, A, Resp, W) :- valid(R, C, A, Resp), power_total(Resp, A, R, P), risk_total(R, C, W, V), P >= V.
lost(R, C, A, Resp, W) :- valid(R, C, A, Resp), power_total(Resp, A, R, P), risk_total(R, C, W, V), P < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for road_id, road in ROADS.items():
        lines.append(asp.fact("road", road_id))
        lines.append(asp.fact("danger", road_id, road.danger))
        lines.append(asp.fact("severity", road_id, road.severity))
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("fragility", cargo_id, cargo.fragility))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for h in sorted(aid.helps):
            lines.append(asp.fact("helps", aid_id, h))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        if response.id != "gun_engine":
            lines.append(asp.fact("base_power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("weather", params.weather),
            asp.fact("chosen", params.road, params.cargo, params.aid, params.response, params.weather),
            f"picked_saved :- chosen(R,C,A,Resp,W), saved(R,C,A,Resp,W).",
            f"picked_lost :- chosen(R,C,A,Resp,W), lost(R,C,A,Resp,W).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_saved/0.\n#show picked_lost/0."))
    atoms_saved = asp.atoms(model, "picked_saved")
    atoms_lost = asp.atoms(model, "picked_lost")
    if atoms_saved:
        return "saved"
    if atoms_lost:
        return "lost"
    return "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a non-empty story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale truck storyworld about kindness on a dangerous road."
    )
    ap.add_argument("--road", choices=ROADS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--weather", type=int, choices=[0, 1, 2], help="0=calm, 2=storm-worse")
    ap.add_argument("--child-name")
    ap.add_argument("--driver-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, child_type: str) -> str:
    return rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.road and args.aid and args.response:
        road = ROADS[args.road]
        aid = AIDS[args.aid]
        response = RESPONSES[args.response]
        if not response_allowed(response, aid, road):
            raise StoryError(explain_rejection(road, aid, response))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing response '{args.response}': it is too reckless for this world.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.road is None or combo[0] == args.road)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.aid is None or combo[2] == args.aid)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    road_id, cargo_id, aid_id, response_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_type)
    driver_name = args.driver_name or rng.choice([n for n in BOY_NAMES if n != child_name] + ["Ivo", "Pavel"])
    weather = args.weather if args.weather is not None else rng.choice([1, 1, 2, 0])

    params = StoryParams(
        road=road_id,
        cargo=cargo_id,
        aid=aid_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        driver_name=driver_name,
        driver_type="man",
        elder_type="grandmother",
        weather=weather,
    )
    outcome_of(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.road not in ROADS:
        raise StoryError(f"(Unknown road: {params.road})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    road = ROADS[params.road]
    cargo = CARGOES[params.cargo]
    aid = AIDS[params.aid]
    response = RESPONSES[params.response]

    if not response_allowed(response, aid, road):
        raise StoryError(explain_rejection(road, aid, response))

    world = tell(
        road=road,
        cargo_cfg=cargo,
        aid=aid,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        driver_name=params.driver_name,
        driver_type=params.driver_type,
        elder_type=params.elder_type,
        weather=params.weather,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (road, cargo, aid, response) combos:\n")
        for road, cargo, aid, response in combos:
            print(f"  {road:13} {cargo:10} {aid:10} {response}")
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
            header = f"### {p.child_name}: {p.road}, {p.cargo}, {p.aid}, {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
