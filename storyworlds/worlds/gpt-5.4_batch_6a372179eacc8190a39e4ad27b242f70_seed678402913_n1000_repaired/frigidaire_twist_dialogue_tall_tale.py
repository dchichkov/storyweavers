#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/frigidaire_twist_dialogue_tall_tale.py
=================================================================

A standalone storyworld for a tall-tale heat-wave story built around an old
frigidaire. The tiny domain is:

    a child must carry a wobbly cold treat to town on a blazing day;
    a booming old frigidaire and a practical helper offer a way;
    the child faces a choice of transport and cooling plan;
    the story ends with a twist proving what the frigidaire had really been doing.

This world keeps the logic narrow and concrete:

* A treat has weight, wobble, and melt risk.
* A transport has carrying power and steadiness.
* A cooling plan has chill power.
* Heat plus travel make the trip harder; sensible plans can still succeed.
* The frigidaire itself is part of the world state, and the final twist comes
  from what it had been freezing inside all along.

Run it
------
    python storyworlds/worlds/gpt-5.4/frigidaire_twist_dialogue_tall_tale.py
    python storyworlds/worlds/gpt-5.4/frigidaire_twist_dialogue_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/frigidaire_twist_dialogue_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/frigidaire_twist_dialogue_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/frigidaire_twist_dialogue_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/frigidaire_twist_dialogue_tall_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from storyworlds/worlds/gpt-5.4/.
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandpa": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    melt: int
    weight: int
    wobble: int
    boast: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transport:
    id: str
    label: str
    phrase: str
    carry: int
    steady: int
    sense: int
    motion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CoolingPlan:
    id: str
    label: str
    phrase: str
    chill: int
    sense: int
    line: str
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    treat = world.entities.get("treat")
    if treat is None:
        return out
    if treat.meters["heat_load"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treat.meters["softening"] += 1
    hero = world.entities.get("hero")
    if hero is not None:
        hero.memes["worry"] += 1
    out.append("__soften__")
    return out


def _r_sag(world: World) -> list[str]:
    out: list[str] = []
    treat = world.entities.get("treat")
    if treat is None:
        return out
    if treat.meters["instability"] < THRESHOLD:
        return out
    sig = ("sag",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treat.meters["sagging"] += 1
    hero = world.entities.get("hero")
    if hero is not None:
        hero.memes["alarm"] += 1
    out.append("__sag__")
    return out


CAUSAL_RULES = [
    Rule(name="soften", tag="physical", apply=_r_soften),
    Rule(name="sag", tag="physical", apply=_r_sag),
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
        for sent in produced:
            world.say(sent)
    return produced


TREATS = {
    "icebox_cake": Treat(
        id="icebox_cake",
        label="icebox cake",
        phrase="a sky-high icebox cake",
        melt=2,
        weight=2,
        wobble=2,
        boast="It was stacked so high the top layer nearly shook hands with the weather vane.",
        tags={"cake", "cold_treat"},
    ),
    "cream_pie": Treat(
        id="cream_pie",
        label="cream pie",
        phrase="a mile-high cream pie",
        melt=2,
        weight=1,
        wobble=2,
        boast="Its whipped top looked as tall as a courthouse clock and twice as proud.",
        tags={"pie", "cold_treat"},
    ),
    "butter_swan": Treat(
        id="butter_swan",
        label="butter swan",
        phrase="a butter swan for the fair table",
        melt=3,
        weight=2,
        wobble=1,
        boast="The swan was so glossy folks said even the sun stopped to stare at its feathers.",
        tags={"butter", "cold_treat"},
    },
}

TRANSPORTS = {
    "wagon": Transport(
        id="wagon",
        label="wagon",
        phrase="a red wagon with high sides",
        carry=3,
        steady=2,
        sense=3,
        motion="rolled as gently as a cloud crossing a pond",
        tags={"wagon"},
    ),
    "wheelbarrow": Transport(
        id="wheelbarrow",
        label="wheelbarrow",
        phrase="a shiny wheelbarrow",
        carry=3,
        steady=1,
        sense=2,
        motion="rattled and bobbed over every pebble in the road",
        tags={"wheelbarrow"},
    ),
    "bicycle": Transport(
        id="bicycle",
        label="bicycle",
        phrase="a bicycle with a basket",
        carry=1,
        steady=0,
        sense=1,
        motion="skipped and jittered like a grasshopper with a new idea",
        tags={"bicycle"},
    ),
}

COOLING_PLANS = {
    "ice_bricks": CoolingPlan(
        id="ice_bricks",
        label="ice bricks",
        phrase="three blue ice bricks wrapped in towels",
        chill=3,
        sense=3,
        line="We'll tuck it beside ice bricks cold enough to make July sneeze.",
        tags={"ice", "frigidaire"},
    ),
    "frost_cloth": CoolingPlan(
        id="frost_cloth",
        label="frost cloth",
        phrase="a frosty quilt from the frigidaire shelf",
        chill=2,
        sense=2,
        line="We'll cover it with the frost cloth and keep the sun from licking it.",
        tags={"cloth", "frigidaire"},
    ),
    "none": CoolingPlan(
        id="none",
        label="no cooling plan",
        phrase="nothing but hope",
        chill=0,
        sense=0,
        line="We'll just move fast and pray the sun is feeling lazy.",
        tags={"none"},
    ),
}

HELPERS = {
    "grandpa": {"type": "grandpa", "style": "Grandpa Pike", "boast": "His suspenders snapped louder than fence rails in a gale."},
    "aunt": {"type": "aunt", "style": "Aunt Maybell", "boast": "She could give orders to a thundercloud and make it say thank you."},
    "uncle": {"type": "uncle", "style": "Uncle Rafe", "boast": "He talked so big the porch posts leaned in to listen."},
}

DESTINATIONS = {
    "fair": {
        "label": "county fair",
        "phrase": "the county fair",
        "distance": 1,
        "heat": 2,
        "ending": "the judges' table",
    },
    "picnic": {
        "label": "church picnic",
        "phrase": "the church picnic",
        "distance": 1,
        "heat": 1,
        "ending": "the long picnic table",
    },
    "parade": {
        "label": "Founders Day parade",
        "phrase": "the Founders Day parade",
        "distance": 2,
        "heat": 2,
        "ending": "the bandstand",
    },
}

GIRL_NAMES = ["Lula", "Maisie", "Pearl", "Dottie", "June", "Minnie"]
BOY_NAMES = ["Jasper", "Beau", "Eli", "Otis", "Wade", "Cal"]
TRAITS = ["brave", "hopeful", "stubborn", "cheerful", "quick-thinking", "earnest"]


def trip_difficulty(treat: Treat, destination: str) -> int:
    dest = DESTINATIONS[destination]
    return treat.melt + dest["heat"] + dest["distance"]


def can_carry(treat: Treat, transport: Transport) -> bool:
    return transport.carry >= treat.weight


def can_steady(treat: Treat, transport: Transport) -> bool:
    return transport.steady >= treat.wobble - 1


def sensible_plan(transport: Transport, cooling: CoolingPlan) -> bool:
    return transport.sense >= SENSE_MIN and cooling.sense >= SENSE_MIN


def successful_trip(treat: Treat, destination: str, transport: Transport, cooling: CoolingPlan) -> bool:
    if not can_carry(treat, transport):
        return False
    if not can_steady(treat, transport):
        return False
    return cooling.chill >= trip_difficulty(treat, destination) - transport.steady


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for treat_id, treat in TREATS.items():
        for destination in DESTINATIONS:
            for transport_id, transport in TRANSPORTS.items():
                for cooling_id, cooling in COOLING_PLANS.items():
                    if sensible_plan(transport, cooling) and can_carry(treat, transport) and can_steady(treat, transport):
                        combos.append((treat_id, destination, transport_id, cooling_id))
    return combos


def predict_trip(treat: Treat, destination: str, transport: Transport, cooling: CoolingPlan) -> dict:
    heat_load = max(0, trip_difficulty(treat, destination) - cooling.chill)
    instability = max(0, treat.wobble - transport.steady)
    return {
        "heat_load": heat_load,
        "instability": instability,
        "success": successful_trip(treat, destination, transport, cooling),
    }


def explain_transport_rejection(treat: Treat, transport: Transport) -> str:
    if not can_carry(treat, transport):
        return (
            f"(No story: {transport.phrase} cannot honestly carry {treat.phrase}. "
            f"This tale needs a load the child could plausibly move.)"
        )
    if not can_steady(treat, transport):
        return (
            f"(No story: {transport.phrase} is too shaky for {treat.phrase}. "
            f"A tall treat would tumble before the twist could happen.)"
        )
    return "(No story: that transport does not fit this treat.)"


def explain_cooling_rejection(cooling: CoolingPlan) -> str:
    return (
        f"(Refusing cooling plan '{cooling.id}': it scores too low on common sense "
        f"for a blazing-day trip. The frigidaire needs to help in a real way.)"
    )


def explain_success_rejection(treat: Treat, destination: str, transport: Transport, cooling: CoolingPlan) -> str:
    need = trip_difficulty(treat, destination) - transport.steady
    return (
        f"(No story: {cooling.label} is not cold enough to protect {treat.label} on the way to "
        f"{DESTINATIONS[destination]['phrase']}. This trip needs chill power at least {need}.)"
    )


def introduce(world: World, hero: Entity, helper: Entity, treat: Treat, destination: str) -> None:
    dest = DESTINATIONS[destination]
    world.say(
        f"In a town so hot that crows panted between caws, {hero.id} had promised to carry "
        f"{treat.phrase} to {dest['phrase']}."
    )
    world.say(treat.boast)
    world.say(
        f"{helper.id} stood on the porch beside the old frigidaire. {helper.attrs['boast']}"
    )


def praise_frigidaire(world: World, helper: Entity) -> None:
    world.say(
        f"The frigidaire was painted the color of old cream, and it hummed so deep the spoons in the kitchen "
        f"drawer kept time with it."
    )
    world.say(
        f'"Listen to that song," {helper.id} said. "That box can keep winter folded up on a shelf."'
    )


def worry(world: World, hero: Entity, treat: Treat, destination: str) -> None:
    dest = DESTINATIONS[destination]
    hero.memes["worry"] += 1
    world.say(
        f'"But {dest["phrase"]} is clear across the hot end of town," {hero.id} said. '
        f'"If the sun even blinks at this {treat.label}, it will sigh and slide."'
    )


def propose(world: World, helper: Entity, transport: Transport, cooling: CoolingPlan) -> None:
    helper.memes["confidence"] += 1
    world.say(
        f'{helper.id} slapped {helper.pronoun("possessive")} knee. "{cooling.line} '
        f'And we\'ll set the whole business in {transport.phrase}."'
    )


def prepare_trip(world: World, hero: Entity, helper: Entity, treat: Treat, transport: Transport, cooling: CoolingPlan) -> None:
    treat_ent = world.get("treat")
    transport_ent = world.get("transport")
    fridge = world.get("frigidaire")
    treat_ent.meters["chill"] += cooling.chill
    transport_ent.meters["steady"] += transport.steady
    fridge.meters["stored_cold"] += cooling.chill
    hero.memes["hope"] += 1
    world.say(
        f"They packed the {treat.label} beside {cooling.phrase}, and the cold came off it in little white whispers."
    )
    world.say(
        f'When {hero.id} touched the wagon rail, {hero.pronoun()} yelped and laughed. "That thing is colder than January socks!"'
    )


def travel(world: World, hero: Entity, treat: Treat, destination: str, transport: Transport, cooling: CoolingPlan) -> None:
    pred = predict_trip(treat, destination, transport, cooling)
    treat_ent = world.get("treat")
    treat_ent.meters["heat_load"] += float(pred["heat_load"])
    treat_ent.meters["instability"] += float(pred["instability"])
    propagate(world, narrate=False)
    world.facts["predicted_heat_load"] = pred["heat_load"]
    world.facts["predicted_instability"] = pred["instability"]
    world.say(
        f"Out on the road, the {transport.label} {transport.motion}. The sun laid hot hands on every fence post in sight."
    )
    if pred["heat_load"] >= THRESHOLD:
        world.say(
            f'{hero.id} leaned close and whispered, "Hold together, you proud old {treat.label}. We are not beaten yet."'
        )
    if pred["instability"] >= THRESHOLD:
        world.say(
            f"The top gave one dangerous shimmy, and {hero.id}'s heart bounced clear to {hero.pronoun('possessive')} hat brim."
        )


def arrive_success(world: World, hero: Entity, helper: Entity, treat: Treat, destination: str) -> None:
    dest = DESTINATIONS[destination]
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"They reached {dest['phrase']}, and {treat.phrase} arrived as proud and straight as a courthouse pillar."
    )
    world.say(
        f'"Well, I\'ll be chilled twice," cried the baker at {dest["ending"]}. "It looks better than when it left!"'
    )
    world.say(
        f'{hero.id} grinned. "{helper.id} said the frigidaire could fold up winter. I guess it tucked in the corners too."'
    )


def twist_reveal(world: World, hero: Entity, helper: Entity, destination: str) -> None:
    dest = DESTINATIONS[destination]
    fridge = world.get("frigidaire")
    fridge.meters["revealed"] += 1
    fridge.attrs["secret"] = "ice_statue"
    world.say(
        f"Then came the twist. When {helper.id} opened the frigidaire back in the square, folks saw it had not been guarding one cold treat at all."
    )
    world.say(
        f"Inside stood a shining block of ice shaped like the town rooster, meant for {dest['phrase']} all along."
    )
    world.say(
        f'"You thought that old box was only growling," {helper.id} said. "It was carving tomorrow\'s bragging rights out of summer itself."'
    )
    world.say(
        "The crowd laughed so hard hats tipped back, and the tale of the frigidaire grew three sizes before supper."
    )


def arrive_failure(world: World, hero: Entity, helper: Entity, treat: Treat, destination: str) -> None:
    dest = DESTINATIONS[destination]
    hero.memes["sadness"] += 1
    world.say(
        f"They did make it to {dest['phrase']}, but the {treat.label} had gone soft at the edges and listed like a tired barn in wind."
    )
    world.say(
        f'"Mercy," {hero.id} said, staring at it. "It didn\'t fall, but it surely forgot how to stand proud."'
    )
    world.say(
        f'{helper.id} tipped {helper.pronoun("possessive")} hat. "A smaller boast would have survived. Next time we borrow more winter from the frigidaire."'
    )


def twist_consolation(world: World, helper: Entity) -> None:
    fridge = world.get("frigidaire")
    fridge.meters["revealed"] += 1
    fridge.attrs["secret"] = "ice_lemons"
    world.say(
        f"Still, the old frigidaire saved the day in its own sideways way. When {helper.id} swung the door wide, it was packed with frozen lemons for cold drinks."
    )
    world.say(
        f'"I was cooling the town either way," {helper.id} said. "If the pie sagged, the lemonade would stand up for us."'
    )
    world.say(
        "So the afternoon ended with cold cups in every hand, and nobody could stay gloomy for long."
    )


def tell(
    treat: Treat,
    destination: str,
    transport: Transport,
    cooling: CoolingPlan,
    hero_name: str = "Lula",
    hero_type: str = "girl",
    helper_kind: str = "grandpa",
    trait: str = "brave",
) -> World:
    world = World()
    helper_cfg = HELPERS[helper_kind]
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id=helper_cfg["style"],
        kind="character",
        type=helper_cfg["type"],
        label="the helper",
        role="helper",
        attrs={"boast": helper_cfg["boast"]},
    ))
    fridge = world.add(Entity(
        id="frigidaire",
        kind="thing",
        type="frigidaire",
        label="frigidaire",
        phrase="the old frigidaire",
        role="machine",
        tags={"frigidaire", "cold"},
    ))
    treat_ent = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=treat.label,
        phrase=treat.phrase,
        role="prize",
        tags=set(treat.tags),
    ))
    transport_ent = world.add(Entity(
        id="transport",
        kind="thing",
        type="transport",
        label=transport.label,
        phrase=transport.phrase,
        role="vehicle",
        tags=set(transport.tags),
    ))

    introduce(world, hero, helper, treat, destination)
    praise_frigidaire(world, helper)

    world.para()
    worry(world, hero, treat, destination)
    propose(world, helper, transport, cooling)
    prepare_trip(world, hero, helper, treat, transport, cooling)

    world.para()
    travel(world, hero, treat, destination, transport, cooling)
    success = successful_trip(treat, destination, transport, cooling)
    if success:
        arrive_success(world, hero, helper, treat, destination)
        world.para()
        twist_reveal(world, hero, helper, destination)
        outcome = "success"
    else:
        arrive_failure(world, hero, helper, treat, destination)
        world.para()
        twist_consolation(world, helper)
        outcome = "softened"

    world.facts.update(
        hero=hero,
        helper=helper,
        treat_cfg=treat,
        destination=destination,
        transport_cfg=transport,
        cooling_cfg=cooling,
        outcome=outcome,
        success=success,
        frigidaire=fridge,
    )
    return world


@dataclass
class StoryParams:
    treat: str
    destination: str
    transport: str
    cooling: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        treat="cream_pie",
        destination="fair",
        transport="wagon",
        cooling="ice_bricks",
        helper="grandpa",
        name="Lula",
        gender="girl",
        trait="brave",
    ),
    StoryParams(
        treat="icebox_cake",
        destination="picnic",
        transport="wagon",
        cooling="frost_cloth",
        helper="aunt",
        name="Jasper",
        gender="boy",
        trait="hopeful",
    ),
    StoryParams(
        treat="butter_swan",
        destination="parade",
        transport="wheelbarrow",
        cooling="ice_bricks",
        helper="uncle",
        name="Pearl",
        gender="girl",
        trait="quick-thinking",
    ),
]


KNOWLEDGE = {
    "frigidaire": [
        (
            "What is a frigidaire?",
            "Frigidaire is an old-fashioned word people sometimes use for a refrigerator. A refrigerator keeps food cold so it stays fresh longer."
        )
    ],
    "ice": [
        (
            "Why do ice bricks help on a hot day?",
            "Ice bricks stay very cold for a long time and soak up heat around them. That helps keep food from warming too fast."
        )
    ],
    "wagon": [
        (
            "Why is a wagon good for carrying a wobbly treat?",
            "A wagon has room for a big load and can roll more steadily than carrying something in your hands. That makes it easier to keep a tall treat from tipping."
        )
    ],
    "wheelbarrow": [
        (
            "What is a wheelbarrow for?",
            "A wheelbarrow is a little cart with one wheel that helps people move heavy things. It can carry a lot, but it can bump and wobble on rough ground."
        )
    ],
    "butter": [
        (
            "Why does butter get soft in the heat?",
            "Butter melts when it gets warm because heat changes it from firm to soft. That is why butter shapes need a cool place."
        )
    ],
    "pie": [
        (
            "Why can cream pie droop on a hot day?",
            "Cream pie has a soft filling and topping, so heat can make it slump. Keeping it cold helps it hold its shape."
        )
    ],
    "cake": [
        (
            "What is an icebox cake?",
            "An icebox cake is a chilled cake that is kept cold instead of baked again after it is put together. Because it is cold and creamy, heat can make it soften."
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise turn near the end that makes you see events in a new way. It changes what you thought was happening."
        )
    ],
}
KNOWLEDGE_ORDER = ["frigidaire", "ice", "wagon", "wheelbarrow", "butter", "pie", "cake", "twist"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treat = f["treat_cfg"]
    transport = f["transport_cfg"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "frigidaire" and lots of dialogue.',
        f"Tell a funny exaggerated story where {hero.id} must carry {treat.phrase} on a blazing day, and {helper.id} trusts an old frigidaire to help.",
        f"Write a child-facing story with a twist ending in which {transport.label} carries a cold treat through the heat, and the surprise explains what the frigidaire had really been doing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treat = f["treat_cfg"]
    transport = f["transport_cfg"]
    cooling = f["cooling_cfg"]
    dest = DESTINATIONS[f["destination"]]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who had to carry {treat.phrase}, and {helper.id}, who trusted the old frigidaire to help. They work together on the hottest day in town."
        ),
        (
            f"Why was {hero.id} worried?",
            f"{hero.id} was worried the heat would soften the {treat.label} before it reached {dest['phrase']}. The trip itself was part of the problem because the sun and the road both made the journey harder."
        ),
        (
            f"What plan did {helper.id} make?",
            f"{helper.id} packed the {treat.label} with {cooling.phrase} and set it in {transport.phrase}. That plan mattered because the cold protected the treat while the transport helped carry it steadily."
        ),
    ]
    if f["success"]:
        qa.append(
            (
                "What was the twist at the end?",
                f"The twist was that the frigidaire had been chilling more than the treat. It was also guarding a big ice rooster for the town event, so the noisy old box turned out to be working on two surprises at once."
            )
        )
        qa.append(
            (
                f"How did the trip end?",
                f"The {treat.label} arrived standing tall and proud at {dest['phrase']}. Then the crowd learned the frigidaire had been saving an even bigger cold surprise inside."
            )
        )
    else:
        qa.append(
            (
                "Did the treat make it perfectly?",
                f"No. It reached {dest['phrase']}, but it had softened and lost some of its proud shape. The road did not defeat the whole day, though, because the frigidaire still held frozen lemons for cold drinks."
            )
        )
        qa.append(
            (
                "What was the twist when the trip went wrong?",
                f"The surprise was that the frigidaire had another job ready. It was full of frozen lemons, so even after the treat sagged, the town still got something cold and cheerful."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"frigidaire", "twist"}
    tags |= set(f["treat_cfg"].tags)
    tags |= set(f["transport_cfg"].tags)
    tags |= set(f["cooling_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_carry(T, Tr) :- treat(T), transport(Tr), weight(T, W), carry(Tr, C), C >= W.
can_steady(T, Tr) :- treat(T), transport(Tr), wobble(T, Wb), steady(Tr, S), S >= Wb - 1.
sensible(Tr, C) :- transport(Tr), cooling(C), tsense(Tr, TS), csense(C, CS), sense_min(M), TS >= M, CS >= M.
valid(T, D, Tr, C) :- treat(T), destination(D), transport(Tr), cooling(C), sensible(Tr, C), can_carry(T, Tr), can_steady(T, Tr).

difficulty(T, D, V) :- melt(T, M), dheat(D, H), ddist(D, Ds), V = M + H + Ds.
need_chill(T, D, Tr, N) :- difficulty(T, D, V), steady(Tr, S), N = V - S.
success(T, D, Tr, C) :- valid(T, D, Tr, C), need_chill(T, D, Tr, N), chill(C, Ch), Ch >= N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        lines.append(asp.fact("melt", treat_id, treat.melt))
        lines.append(asp.fact("weight", treat_id, treat.weight))
        lines.append(asp.fact("wobble", treat_id, treat.wobble))
    for dest_id, dest in DESTINATIONS.items():
        lines.append(asp.fact("destination", dest_id))
        lines.append(asp.fact("dheat", dest_id, dest["heat"]))
        lines.append(asp.fact("ddist", dest_id, dest["distance"]))
    for tr_id, tr in TRANSPORTS.items():
        lines.append(asp.fact("transport", tr_id))
        lines.append(asp.fact("carry", tr_id, tr.carry))
        lines.append(asp.fact("steady", tr_id, tr.steady))
        lines.append(asp.fact("tsense", tr_id, tr.sense))
    for c_id, c in COOLING_PLANS.items():
        lines.append(asp.fact("cooling", c_id))
        lines.append(asp.fact("chill", c_id, c.chill))
        lines.append(asp.fact("csense", c_id, c.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_successes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show success/4."))
    return sorted(set(asp.atoms(model, "success")))


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    py_success: set[tuple[str, str, str, str]] = set()
    for treat_id, dest_id, tr_id, c_id in python_valid:
        if successful_trip(TREATS[treat_id], dest_id, TRANSPORTS[tr_id], COOLING_PLANS[c_id]):
            py_success.add((treat_id, dest_id, tr_id, c_id))
    clingo_success = set(asp_successes())
    if clingo_success == py_success:
        print(f"OK: success model matches ({len(clingo_success)} successful combos).")
    else:
        rc = 1
        print("MISMATCH in success combos:")
        if clingo_success - py_success:
            print("  only in clingo:", sorted(clingo_success - py_success))
        if py_success - clingo_success:
            print("  only in python:", sorted(py_success - clingo_success))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "frigidaire" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story missing required content.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive for batch generation
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child, a blazing day, and an old frigidaire with a twist."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--transport", choices=TRANSPORTS)
    ap.add_argument("--cooling", choices=COOLING_PLANS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.treat and args.transport:
        treat = TREATS[args.treat]
        transport = TRANSPORTS[args.transport]
        if not can_carry(treat, transport) or not can_steady(treat, transport):
            raise StoryError(explain_transport_rejection(treat, transport))
    if args.cooling and COOLING_PLANS[args.cooling].sense < SENSE_MIN:
        raise StoryError(explain_cooling_rejection(COOLING_PLANS[args.cooling]))

    combos = [
        combo for combo in valid_combos()
        if (args.treat is None or combo[0] == args.treat)
        and (args.destination is None or combo[1] == args.destination)
        and (args.transport is None or combo[2] == args.transport)
        and (args.cooling is None or combo[3] == args.cooling)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, dest_id, transport_id, cooling_id = rng.choice(sorted(combos))
    treat = TREATS[treat_id]
    transport = TRANSPORTS[transport_id]
    cooling = COOLING_PLANS[cooling_id]
    if not successful_trip(treat, dest_id, transport, cooling):
        raise StoryError(explain_success_rejection(treat, dest_id, transport, cooling))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        treat=treat_id,
        destination=dest_id,
        transport=transport_id,
        cooling=cooling_id,
        helper=helper,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"Unknown treat: {params.treat}")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"Unknown destination: {params.destination}")
    if params.transport not in TRANSPORTS:
        raise StoryError(f"Unknown transport: {params.transport}")
    if params.cooling not in COOLING_PLANS:
        raise StoryError(f"Unknown cooling plan: {params.cooling}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    treat = TREATS[params.treat]
    transport = TRANSPORTS[params.transport]
    cooling = COOLING_PLANS[params.cooling]
    if not sensible_plan(transport, cooling):
        raise StoryError(explain_cooling_rejection(cooling))
    if not can_carry(treat, transport) or not can_steady(treat, transport):
        raise StoryError(explain_transport_rejection(treat, transport))
    if not successful_trip(treat, params.destination, transport, cooling):
        raise StoryError(explain_success_rejection(treat, params.destination, transport, cooling))

    world = tell(
        treat=treat,
        destination=params.destination,
        transport=transport,
        cooling=cooling,
        hero_name=params.name,
        hero_type=params.gender,
        helper_kind=params.helper,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show success/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid = asp_valid_combos()
        success = set(asp_successes())
        print(f"{len(valid)} compatible (treat, destination, transport, cooling) combos:\n")
        for treat_id, dest_id, tr_id, c_id in valid:
            ok = "success" if (treat_id, dest_id, tr_id, c_id) in success else "soften"
            print(f"  {treat_id:12} {dest_id:8} {tr_id:11} {c_id:11} [{ok}]")
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
            header = f"### {p.name}: {p.treat} to {p.destination} ({p.transport}, {p.cooling})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
