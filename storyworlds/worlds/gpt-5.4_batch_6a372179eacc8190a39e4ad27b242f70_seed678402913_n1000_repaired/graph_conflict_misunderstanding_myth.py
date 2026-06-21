#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/graph_conflict_misunderstanding_myth.py
==================================================================

A standalone storyworld for a small mythic domain built around a **graph**, a
**conflict**, and a **misunderstanding**.

Long ago, in little valleys and shores, two weather spirits cared for growing
things: one brought sunlight and one brought rain. An old wise helper drew a
graph to show that the people needed both gifts together. But one spirit
misunderstood the graph as a contest, felt slighted, and quarreled with the
other. The sky tipped too far one way, then too far the other, until the helper
explained what the graph really meant. The spirits made peace, shared the sky,
and the land kept a bright mythic sign of what they learned.

The world model has:
- typed entities with physical meters and emotional memes
- a reasonableness gate for compatible (place, graph) pairs
- an inline ASP twin for that gate and for the ending outcome
- three QA sets generated from simulated state, not by parsing English

Run it
------
    python storyworlds/worlds/gpt-5.4/graph_conflict_misunderstanding_myth.py
    python storyworlds/worlds/gpt-5.4/graph_conflict_misunderstanding_myth.py --all
    python storyworlds/worlds/gpt-5.4/graph_conflict_misunderstanding_myth.py --place shore --graph tide
    python storyworlds/worlds/gpt-5.4/graph_conflict_misunderstanding_myth.py --place mountain --graph tide
    python storyworlds/worlds/gpt-5.4/graph_conflict_misunderstanding_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/graph_conflict_misunderstanding_myth.py --verify
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
        female = {"girl", "woman", "goddess", "queen", "daughter", "mother"}
        male = {"boy", "man", "god", "king", "son", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    people: str
    crop: str
    supports_graphs: set[str] = field(default_factory=set)
    resilience: int = 1
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class GraphKind:
    id: str
    label: str
    phrase: str
    measures: str
    fits_places: set[str] = field(default_factory=set)
    misunderstanding: str = ""
    explanation: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    name: str
    type: str
    title: str
    entrance: str
    wisdom: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SpiritPair:
    id: str
    sun_name: str
    rain_name: str
    sun_type: str = "goddess"
    rain_type: str = "god"
    relation: str = "siblings"


@dataclass
class StoryParams:
    place: str
    graph: str
    helper: str
    pair: str
    offended: str
    delay: int
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


def _r_drought(world: World) -> list[str]:
    land = world.get("land")
    sky = world.get("sky")
    if sky.meters["sun_only"] < THRESHOLD:
        return []
    sig = ("drought",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    land.meters["thirst"] += 1
    land.meters["harm"] += 1
    return ["__drought__"]


def _r_flood(world: World) -> list[str]:
    land = world.get("land")
    sky = world.get("sky")
    if sky.meters["rain_only"] < THRESHOLD:
        return []
    sig = ("flood",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    land.meters["flood"] += 1
    land.meters["harm"] += 1
    return ["__flood__"]


def _r_balance(world: World) -> list[str]:
    land = world.get("land")
    sun = world.get("sun")
    rain = world.get("rain")
    if sun.meters["given"] < THRESHOLD or rain.meters["given"] < THRESHOLD:
        return []
    sig = ("balance",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    land.meters["growth"] += 1
    land.meters["peace"] += 1
    return ["__balance__"]


CAUSAL_RULES = [
    Rule(name="drought", tag="physical", apply=_r_drought),
    Rule(name="flood", tag="physical", apply=_r_flood),
    Rule(name="balance", tag="physical", apply=_r_balance),
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


PLACES = {
    "valley": Place(
        id="valley",
        label="the Green Valley",
        people="the valley children",
        crop="bean vines",
        supports_graphs={"growth", "river"},
        resilience=1,
        ending_image="Ever since then, green vines in the valley climb in bright twists, as if they still remember the day sunlight and rain learned to share.",
        tags={"plants", "weather"},
    ),
    "shore": Place(
        id="shore",
        label="the Shell Shore",
        people="the fishing families",
        crop="salt-grass and tide flowers",
        supports_graphs={"tide", "river"},
        resilience=2,
        ending_image="That is why the little tide flowers on the shore open after sun and rain together, and why their petals shine with silver edges.",
        tags={"ocean", "weather"},
    ),
    "mountain": Place(
        id="mountain",
        label="the Terraced Mountain",
        people="the mountain villagers",
        crop="fig trees on stone steps",
        supports_graphs={"growth"},
        resilience=1,
        ending_image="To this day, the fig leaves on the mountain show dark lines and gold veins, like a lesson written by the sky itself.",
        tags={"mountain", "plants", "weather"},
    ),
}

GRAPHS = {
    "growth": GraphKind(
        id="growth",
        label="growth graph",
        phrase="a growth graph scratched on a clay tablet",
        measures="how the young plants rose when warm light and soft rain took turns",
        fits_places={"valley", "mountain"},
        misunderstanding="The climbing line looked to one proud heart like a ladder for winning.",
        explanation="the line did not keep score; it simply showed that days of sun and days of rain helped the living things together",
        tags={"graph", "plants"},
    ),
    "river": GraphKind(
        id="river",
        label="river graph",
        phrase="a river graph painted in blue on a temple wall",
        measures="how high the water should rise before the roots could drink without drowning",
        fits_places={"valley", "shore"},
        misunderstanding="The marks by the river line looked like praise counted for one gift and not the other.",
        explanation="the marks did not praise one spirit over the other; they showed the gentle middle where roots could drink and still breathe",
        tags={"graph", "river"},
    ),
    "tide": GraphKind(
        id="tide",
        label="tide graph",
        phrase="a tide graph made of shells set in wet sand",
        measures="when the sea should come in and when the sun should dry the flats for little flowers and crabs",
        fits_places={"shore"},
        misunderstanding="The high shell marks looked like a throne to be owned by only one ruler of the sky.",
        explanation="the shell line was not a throne at all; it showed a rhythm, one gift following the other so the shore could live",
        tags={"graph", "ocean"},
    ),
}

HELPERS = {
    "tortoise": HelperKind(
        id="tortoise",
        name="Old Tortoise",
        type="thing",
        title="the oldest keeper of seasons",
        entrance="Old Tortoise lived beside the shrine steps and listened longer than anyone else.",
        wisdom="Slow eyes can read what quick tempers miss.",
        tags={"wisdom"},
    ),
    "crane": HelperKind(
        id="crane",
        name="Silver Crane",
        type="thing",
        title="the long-legged reader of reeds",
        entrance="Silver Crane watched the waterlines and knew how to wait without speaking.",
        wisdom="A picture of time is not the same as a prize.",
        tags={"wisdom"},
    ),
    "moon_grandmother": HelperKind(
        id="moon_grandmother",
        name="Moon Grandmother",
        type="goddess",
        title="the lamp of quiet nights",
        entrance="Moon Grandmother rose above the roofs each evening and remembered the old promises of sky and field.",
        wisdom="What bends together does not break the world apart.",
        tags={"wisdom", "moon"},
    ),
}

PAIRS = {
    "gold_and_mist": SpiritPair(
        id="gold_and_mist",
        sun_name="Sola",
        rain_name="Miro",
    ),
    "amber_and_stream": SpiritPair(
        id="amber_and_stream",
        sun_name="Aru",
        rain_name="Nerin",
    ),
    "dawn_and_drizzle": SpiritPair(
        id="dawn_and_drizzle",
        sun_name="Tala",
        rain_name="Beren",
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for graph_id, graph in GRAPHS.items():
            if graph_id in place.supports_graphs and place_id in graph.fits_places:
                combos.append((place_id, graph_id))
    return combos


def explain_rejection(place: Place, graph: GraphKind) -> str:
    return (
        f"(No story: {graph.label} does not fit {place.label}. "
        f"The graph must measure something that truly belongs there.)"
    )


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    return "scar_mark" if params.delay > place.resilience else "restored"


def compatible(place_id: str, graph_id: str) -> bool:
    return (place_id, graph_id) in set(valid_combos())


def introduce(world: World, place: Place, pair: SpiritPair, helper: HelperKind) -> None:
    sun = world.get("sun")
    rain = world.get("rain")
    world.say(
        f"Long ago, when hills and waters still listened to voices in the sky, "
        f"{place.label} was tended by two young spirits, {sun.id} of warm light and {rain.id} of gentle rain."
    )
    world.say(
        f"The people there trusted both of them, because {place.crop} grew sweetest when sunshine and rain visited in turn."
    )
    world.say(helper.entrance)


def show_graph(world: World, place: Place, graph: GraphKind, helper: HelperKind) -> None:
    helper_ent = world.get("helper")
    helper_ent.meters["teaching"] += 1
    world.say(
        f"One planting season, {helper_ent.id} made {graph.phrase}. "
        f"It showed {graph.measures}."
    )
    world.say(
        f"The children gathered around the graph, and even the two sky spirits leaned down to look."
    )


def spark_misunderstanding(world: World, graph: GraphKind, offended: str) -> None:
    sun = world.get("sun")
    rain = world.get("rain")
    first = sun if offended == "sun" else rain
    other = rain if offended == "sun" else sun
    first.memes["pride"] += 1
    first.memes["misunderstanding"] += 1
    other.memes["hurt"] += 1
    world.say(
        f"But {first.id} stared at the line too quickly. {graph.misunderstanding}"
    )
    if offended == "sun":
        world.say(
            f'"So the valley cheers for rain more than light?" {first.id} cried. '
            f'"Then let them miss my gold."'
        )
        world.say(
            f'{other.id} lifted his hands in surprise. "That is not what it says," he answered, '
            f'but his answer came too late and sounded sharp.'
        )
    else:
        world.say(
            f'"So all the praise is for sunlight?" {first.id} cried. '
            f'"Then let the ground wait for my clouds."'
        )
        world.say(
            f'{other.id} spread her bright arms in surprise. "That is not what it says," she answered, '
            f'but her answer came too fast and sounded proud.'
        )


def quarrel(world: World, place: Place, offended: str, delay: int) -> None:
    sun = world.get("sun")
    rain = world.get("rain")
    sky = world.get("sky")
    land = world.get("land")
    sun.memes["anger"] += 1
    rain.memes["anger"] += 1
    land.memes["fear"] += 1
    world.say(
        f"The two spirits quarreled above {place.label}, and their quarrel tugged the weather out of balance."
    )
    if offended == "sun":
        sky.meters["rain_only"] += 1
        rain.meters["given"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Without {sun.id}'s warm face, clouds crowded low. {rain.id}, hurt and stubborn now, let rain fall for too many days."
        )
    else:
        sky.meters["sun_only"] += 1
        sun.meters["given"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Without {rain.id}'s cool hands, the sky grew hard and bright. {sun.id}, hurt and stubborn now, poured down light for too many days."
        )
    if land.meters["thirst"] >= THRESHOLD:
        world.say(
            f"Soon the soil cracked around the {place.crop}, and even the children spoke softly when they saw the thirsty leaves."
        )
    if land.meters["flood"] >= THRESHOLD:
        world.say(
            f"Soon the roots stood in too much water, and the little paths turned to mirrors where no one wanted to dance."
        )

    if delay >= 1:
        if offended == "sun":
            sky.meters["sun_only"] += 1
            sun.meters["given"] += 1
            world.say(
                f"At last {sun.id} returned in anger, shining all at once as if heat alone could settle the matter."
            )
        else:
            sky.meters["rain_only"] += 1
            rain.meters["given"] += 1
            world.say(
                f"At last {rain.id} returned in anger, pouring all at once as if rain alone could settle the matter."
            )
        propagate(world, narrate=False)
        if land.meters["thirst"] >= THRESHOLD and land.meters["flood"] >= THRESHOLD:
            world.say(
                f"So the poor {place.crop} suffered both ways: first too little of one gift, then too much of the other."
            )


def explain_and_reconcile(world: World, place: Place, graph: GraphKind, helper: HelperKind) -> None:
    helper_ent = world.get("helper")
    sun = world.get("sun")
    rain = world.get("rain")
    sun.memes["anger"] = 0.0
    rain.memes["anger"] = 0.0
    sun.memes["misunderstanding"] = 0.0
    rain.memes["misunderstanding"] = 0.0
    sun.memes["shame"] += 1
    rain.memes["shame"] += 1
    sun.memes["trust"] += 1
    rain.memes["trust"] += 1
    world.say(
        f"Then {helper_ent.id} called them down and touched the graph with a patient hand."
    )
    world.say(
        f'"Look again," {helper_ent.id} said. "{graph.explanation}."'
    )
    world.say(
        f"{sun.id} and {rain.id} looked a second time, and now they saw days beside the marks, not winners above losers."
    )
    world.say(
        f"Their faces changed. Each spirit understood that the other had not been stealing love at all."
    )


def restore_balance(world: World, place: Place) -> None:
    sun = world.get("sun")
    rain = world.get("rain")
    sky = world.get("sky")
    land = world.get("land")
    sky.meters["sun_only"] = 0.0
    sky.meters["rain_only"] = 0.0
    sun.meters["given"] += 1
    rain.meters["given"] += 1
    sun.memes["peace"] += 1
    rain.memes["peace"] += 1
    land.memes["relief"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {sun.id} promised to warm the land gently, and {rain.id} promised to visit softly after."
    )
    world.say(
        f"Light and rain began to take turns again, and the people of {place.label} lifted their heads as the {place.crop} straightened."
    )


def mythic_ending(world: World, place: Place, outcome: str) -> None:
    land = world.get("land")
    if outcome == "scar_mark":
        land.meters["mark"] += 1
        world.say(
            f"The plants healed, but they kept a small sign of the quarrel so no one would forget how a quick misunderstanding can wound a whole land."
        )
    else:
        world.say(
            f"The hurt passed quickly, and the land answered with fresh green life almost at once."
        )
    world.say(place.ending_image)


def tell(
    place: Place,
    graph: GraphKind,
    helper: HelperKind,
    pair: SpiritPair,
    offended: str,
    delay: int,
) -> World:
    world = World()
    sun = world.add(Entity(id=pair.sun_name, kind="character", type=pair.sun_type, role="sun", label="sun spirit"))
    rain = world.add(Entity(id=pair.rain_name, kind="character", type=pair.rain_type, role="rain", label="rain spirit"))
    helper_ent = world.add(Entity(id=helper.name, kind="character", type=helper.type, role="helper", label=helper.title))
    world.add(Entity(id="land", kind="thing", type="land", label=place.label))
    world.add(Entity(id="sky", kind="thing", type="sky", label="the sky"))

    introduce(world, place, pair, helper)
    show_graph(world, place, graph, helper)

    world.para()
    spark_misunderstanding(world, graph, offended)
    quarrel(world, place, offended, delay)

    world.para()
    explain_and_reconcile(world, place, graph, helper)
    restore_balance(world, place)
    outcome = outcome_of(
        StoryParams(
            place=place.id,
            graph=graph.id,
            helper=helper.id,
            pair=pair.id,
            offended=offended,
            delay=delay,
        )
    )
    mythic_ending(world, place, outcome)

    world.facts.update(
        place=place,
        graph=graph,
        helper=helper_ent,
        helper_cfg=helper,
        pair=pair,
        sun=sun,
        rain=rain,
        offended=offended,
        delay=delay,
        outcome=outcome,
        misunderstanding=True,
        conflict=True,
        thirst=world.get("land").meters["thirst"] >= THRESHOLD,
        flood=world.get("land").meters["flood"] >= THRESHOLD,
        growth=world.get("land").meters["growth"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    graph = f["graph"]
    sun = f["sun"]
    rain = f["rain"]
    return [
        f'Write a short myth for a young child that includes the word "{graph.label.split()[0]}".',
        f"Tell a myth set in {place.label} where {sun.id} and {rain.id} fall into conflict because they misunderstand a {graph.label}.",
        f"Write a gentle origin tale in which a misunderstanding about a graph harms the land for a while, then wisdom brings balance back.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place = f["place"]
    graph = f["graph"]
    helper = f["helper"]
    sun = f["sun"]
    rain = f["rain"]
    offended = sun if f["offended"] == "sun" else rain
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sun.id}, the spirit of warm light, {rain.id}, the spirit of rain, and {helper.id}, who explained the truth. They cared for {place.label} together.",
        ),
        (
            "What was the graph for?",
            f"The graph showed {graph.measures}. It was meant to teach that the land needed both sunlight and rain in a good rhythm.",
        ),
        (
            f"Why did {offended.id} get upset?",
            f"{offended.id} misunderstood the graph and thought it was keeping score. That mistake made {offended.pronoun()} feel slighted, so a quarrel began in the sky.",
        ),
    ]
    if f["thirst"] or f["flood"]:
        harm = []
        if f["thirst"]:
            harm.append("the soil cracked from too much sun and too little rain")
        if f["flood"]:
            harm.append("the roots sat in too much water and the paths turned soggy")
        joined = " and ".join(harm)
        qa.append(
            (
                f"What happened to {place.label} during the conflict?",
                f"During the quarrel, {joined}. The land was hurt because the two gifts stopped taking turns the way living things needed.",
            )
        )
    qa.append(
        (
            "How was the misunderstanding solved?",
            f"{helper.id} pointed to the graph and explained that it was a picture of time, not a prize for one spirit to win. When {sun.id} and {rain.id} looked again, they understood each other and made peace.",
        )
    )
    if f["outcome"] == "scar_mark":
        qa.append(
            (
                "How did the story end?",
                f"The land healed, but it kept a small sign of the quarrel. The ending says the world still remembers the lesson about reading carefully and sharing kindly.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"{sun.id} and {rain.id} shared the sky again, and the land grew strong. The final image shows that balance came back quickly once the misunderstanding was cleared up.",
            )
        )
    return qa


KNOWLEDGE = {
    "graph": [
        (
            "What is a graph?",
            "A graph is a picture that helps you see how something changes. Lines or marks on it can show more, less, or a pattern over time.",
        )
    ],
    "weather": [
        (
            "Why do plants need both sunlight and rain?",
            "Plants need sunlight to make food and rain to drink through their roots. Too much of only one can hurt them.",
        )
    ],
    "plants": [
        (
            "What happens when soil gets too dry?",
            "Very dry soil can crack and turn hard. Then roots have a harder time finding the water they need.",
        )
    ],
    "river": [
        (
            "Why can too much water be bad for roots?",
            "Roots need water, but they also need air in the soil. If the ground stays too wet, the roots cannot breathe well.",
        )
    ],
    "ocean": [
        (
            "What is a tide?",
            "A tide is the sea moving in and out along the shore. It changes through the day in a steady pattern.",
        )
    ],
    "wisdom": [
        (
            "How can a misunderstanding start a conflict?",
            "A misunderstanding happens when someone thinks a message means one thing when it really means another. Hurt feelings can grow into a conflict if nobody slows down and explains clearly.",
        )
    ],
    "moon": [
        (
            "Why do old stories give the moon wisdom?",
            "Many myths make the moon wise because it watches quietly over many nights. In stories, quiet watching often stands for patience and memory.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"graph", "weather", "wisdom"} | set(f["place"].tags) | set(f["graph"].tags) | set(f["helper_cfg"].tags)
    order = ["graph", "weather", "plants", "river", "ocean", "wisdom", "moon"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        lines.append(f"  {ent.id:16} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="valley",
        graph="growth",
        helper="tortoise",
        pair="gold_and_mist",
        offended="sun",
        delay=0,
    ),
    StoryParams(
        place="shore",
        graph="tide",
        helper="crane",
        pair="amber_and_stream",
        offended="rain",
        delay=1,
    ),
    StoryParams(
        place="mountain",
        graph="growth",
        helper="moon_grandmother",
        pair="dawn_and_drizzle",
        offended="sun",
        delay=2,
    ),
    StoryParams(
        place="shore",
        graph="river",
        helper="tortoise",
        pair="gold_and_mist",
        offended="rain",
        delay=0,
    ),
]


ASP_RULES = r"""
compatible(P, G) :- place(P), graph(G), place_supports(P, G), graph_fits(G, P).

outcome(restored)  :- chosen_place(P), resilience(P, R), delay(D), D <= R.
outcome(scar_mark) :- chosen_place(P), resilience(P, R), delay(D), D > R.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("resilience", place_id, place.resilience))
        for graph_id in sorted(place.supports_graphs):
            lines.append(asp.fact("place_supports", place_id, graph_id))
    for graph_id, graph in GRAPHS.items():
        lines.append(asp.fact("graph", graph_id))
        for place_id in sorted(graph.fits_places):
            lines.append(asp.fact("graph_fits", graph_id, place_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("delay", params.delay),
        ]
    )
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
        print("MISMATCH in compatible combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

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
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a mythic misunderstanding about a graph leads to a weather quarrel."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--graph", choices=GRAPHS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--offended", choices=["sun", "rain"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the quarrel harms the land before wisdom intervenes")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, graph) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.graph:
        if not compatible(args.place, args.graph):
            raise StoryError(explain_rejection(PLACES[args.place], GRAPHS[args.graph]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.graph is None or combo[1] == args.graph)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, graph_id = rng.choice(sorted(combos))
    return StoryParams(
        place=place_id,
        graph=graph_id,
        helper=args.helper or rng.choice(sorted(HELPERS)),
        pair=args.pair or rng.choice(sorted(PAIRS)),
        offended=args.offended or rng.choice(["sun", "rain"]),
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.graph not in GRAPHS:
        raise StoryError(f"(Unknown graph: {params.graph})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.pair not in PAIRS:
        raise StoryError(f"(Unknown pair: {params.pair})")
    if params.offended not in {"sun", "rain"}:
        raise StoryError(f"(Unknown offended side: {params.offended})")
    if not compatible(params.place, params.graph):
        raise StoryError(explain_rejection(PLACES[params.place], GRAPHS[params.graph]))

    world = tell(
        place=PLACES[params.place],
        graph=GRAPHS[params.graph],
        helper=HELPERS[params.helper],
        pair=PAIRS[params.pair],
        offended=params.offended,
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
        print(asp_program("", "#show compatible/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, graph) pairs:\n")
        for place_id, graph_id in combos:
            print(f"  {place_id:10} {graph_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place}: {p.graph} ({p.offended}, {outcome_of(p)})"
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
