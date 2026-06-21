#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/porter_repetition_problem_solving_moral_value_bedtime.py
===================================================================================

A standalone story world about a gentle night porter at a tiny station, rebuilt
as a small simulation rather than a frozen template. The domain is tuned for a
bedtime-story mood and for three seed features:

- Repetition: the porter helps one sleepy passenger, then another, then another.
- Problem Solving: a concrete obstacle blocks the way to the train, and the
  porter must choose the right tool for it.
- Moral Value: patient helping makes the ending possible.

Run it
------
    python storyworlds/worlds/gpt-5.4/porter_repetition_problem_solving_moral_value_bedtime.py
    python storyworlds/worlds/gpt-5.4/porter_repetition_problem_solving_moral_value_bedtime.py --stop forest --obstacle tall_step --tool stool
    python storyworlds/worlds/gpt-5.4/porter_repetition_problem_solving_moral_value_bedtime.py --obstacle windy_path --tool wagon
    python storyworlds/worlds/gpt-5.4/porter_repetition_problem_solving_moral_value_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/porter_repetition_problem_solving_moral_value_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/porter_repetition_problem_solving_moral_value_bedtime.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Stop:
    id: str
    label: str
    opening: str
    image: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    line: str
    fear: str
    fix_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolDef:
    id: str
    label: str
    phrase: str
    action: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class BundleStyle:
    id: str
    label: str
    phrase: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    stop: str
    obstacle: str
    tool: str
    bundle: str
    porter_name: str
    porter_gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, stop: Stop) -> None:
        self.stop = stop
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
        clone = World(self.stop)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def passengers(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "passenger"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_waiting_worry(world: World) -> list[str]:
    out: list[str] = []
    blocked = world.get("path").meters["blocked"] >= THRESHOLD
    for passenger in world.passengers():
        if passenger.meters["aboard"] >= THRESHOLD:
            continue
        if not blocked:
            continue
        sig = ("worry", passenger.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        passenger.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_boarding_relief(world: World) -> list[str]:
    out: list[str] = []
    porter = world.get("porter")
    for passenger in world.passengers():
        if passenger.meters["aboard"] < THRESHOLD:
            continue
        sig = ("relief", passenger.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        passenger.memes["relief"] += 1
        porter.memes["kindness"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="waiting_worry", tag="emotional", apply=_r_waiting_worry),
    Rule(name="boarding_relief", tag="emotional", apply=_r_boarding_relief),
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


STOPS = {
    "meadow": Stop(
        id="meadow",
        label="Meadow Gate",
        opening="where the grass smelled sweet and the lamps glowed like buttercups",
        image="Beyond the platform, the little Dream Train waited with sleepy silver windows.",
        affords={"puddle", "windy_path"},
    ),
    "forest": Stop(
        id="forest",
        label="Forest Nook",
        opening="where soft pine shadows lay across the boards",
        image="Owls blinked from the branches while the Dream Train breathed tiny clouds into the cool air.",
        affords={"tall_step", "windy_path"},
    ),
    "harbor": Stop(
        id="harbor",
        label="Harbor Lantern Stop",
        opening="where the dark water made the lamps shimmer in long gold lines",
        image="The Dream Train waited beside the docks, gentle as a cat settling into a basket.",
        affords={"puddle", "tall_step"},
    ),
}

OBSTACLES = {
    "puddle": Obstacle(
        id="puddle",
        label="puddle",
        line="A wide silver puddle had spread across the platform and made the boards slippery.",
        fear='Each passenger peeped at the shining water and whispered, "I do not want my bedtime things to splash."',
        fix_need="something that could carry the bundles safely past the puddle",
        tags={"puddle", "station"},
    ),
    "tall_step": Obstacle(
        id="tall_step",
        label="step",
        line="The last step into the train looked far too high for sleepy little legs.",
        fear='Each passenger stared at the high step and whispered, "I am too drowsy to climb that."',
        fix_need="something that would make the climb small and steady",
        tags={"step", "station"},
    ),
    "windy_path": Obstacle(
        id="windy_path",
        label="wind",
        line="A fussy wind ran up and down the platform, tugging at scarves and loose pages.",
        fear='Each passenger held tight and whispered, "The wind will snatch my bedtime things away."',
        fix_need="something that could shield the bundles from the gusts",
        tags={"wind", "station"},
    ),
}

TOOLS = {
    "wagon": ToolDef(
        id="wagon",
        label="wagon",
        phrase="a little red wagon",
        action="rolled out a little red wagon and lined it with a dry cloth",
        solves={"puddle"},
        tags={"wagon", "helping"},
    ),
    "stool": ToolDef(
        id="stool",
        label="stool",
        phrase="a sturdy wooden stool",
        action="set down a sturdy wooden stool so the climb became one easy step and then another",
        solves={"tall_step"},
        tags={"stool", "helping"},
    ),
    "umbrella": ToolDef(
        id="umbrella",
        label="umbrella",
        phrase="a wide blue umbrella",
        action="opened a wide blue umbrella and held it low like a calm little roof",
        solves={"windy_path"},
        tags={"umbrella", "helping"},
    ),
}

BUNDLES = {
    "blankets": BundleStyle(
        id="blankets",
        label="blankets",
        phrase="soft rolled blankets",
        plural=True,
        tags={"blanket", "bedtime"},
    ),
    "pillows": BundleStyle(
        id="pillows",
        label="pillows",
        phrase="round moon pillows",
        plural=True,
        tags={"pillow", "bedtime"},
    ),
    "storybooks": BundleStyle(
        id="storybooks",
        label="storybooks",
        phrase="small bedtime storybooks",
        plural=True,
        tags={"storybook", "bedtime"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mina", "Ella", "Ruby", "Cora"]
BOY_NAMES = ["Owen", "Milo", "Toby", "Finn", "Benji", "Theo"]
TRAITS = ["patient", "thoughtful", "rushed"]

PASSENGER_SETS = [
    [("Moss", "rabbit"), ("Pip", "fox"), ("Wren", "duck")],
    [("Daisy", "mouse"), ("Bramble", "rabbit"), ("Nip", "squirrel")],
    [("Juniper", "fox"), ("Poppy", "mouse"), ("Otis", "bear")],
]


def valid_tool_for(obstacle_id: str, tool_id: str) -> bool:
    return obstacle_id in TOOLS[tool_id].solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for stop_id, stop in STOPS.items():
        for obstacle_id in sorted(stop.affords):
            for tool_id in TOOLS:
                if valid_tool_for(obstacle_id, tool_id):
                    combos.append((stop_id, obstacle_id, tool_id))
    return combos


def explain_rejection(stop: Stop, obstacle: Obstacle, tool: ToolDef) -> str:
    if obstacle.id not in stop.affords:
        return (
            f"(No story: {stop.label} does not have a {obstacle.label} problem in this world, "
            f"so {tool.label} would have nothing honest to fix there.)"
        )
    return (
        f"(No story: {tool.phrase} does not sensibly solve the {obstacle.label} problem. "
        f"The obstacle needs {obstacle.fix_need}.)"
    )


def calm_trait(trait: str) -> bool:
    return trait in {"patient", "thoughtful"}


def outcome_of(params: StoryParams) -> str:
    return "calm" if calm_trait(params.trait) else "flustered"


def introduce(world: World, porter: Entity, stop: Stop) -> None:
    world.say(
        f"At {stop.label}, {stop.opening}, {porter.id} was the night's little porter. "
        f"{stop.image}"
    )
    world.say(
        f"{porter.id} liked to keep the platform quiet, the blankets folded, and the sleepy passengers smiling."
    )


def gather_passengers(world: World, porter: Entity, bundle: BundleStyle, passengers: list[Entity]) -> None:
    names = ", ".join(p.id for p in passengers[:-1]) + f", and {passengers[-1].id}"
    for passenger in passengers:
        passenger.memes["sleepy"] += 1
        passenger.meters["waiting"] += 1
    world.say(
        f"That evening, three tiny passengers came padding up the boards: {names}. "
        f"Each one carried {bundle.phrase} for the ride to Dream Hill."
    )
    world.say(
        f'"Porter, porter," they murmured, one after another, "please help us catch the train before our eyes close."'
    )


def show_problem(world: World, obstacle: Obstacle) -> None:
    path = world.get("path")
    path.meters["blocked"] = 1
    propagate(world, narrate=False)
    world.say(obstacle.line)
    world.say(obstacle.fear)


def think_and_choose(world: World, porter: Entity, tool: ToolDef, obstacle: Obstacle, trait: str) -> None:
    porter.memes["thoughtful"] += 1
    if trait == "rushed":
        porter.memes["fluster"] += 1
        world.say(
            f'{porter.id} hurried to one end of the platform, then the other. "Oh dear," {porter.pronoun()} whispered. '
            f'For a moment {porter.pronoun()} almost tried to fix the {obstacle.label} problem too quickly.'
        )
        world.say(
            f"Then {porter.pronoun()} stopped, took one slow breath, and looked carefully again."
        )
    else:
        porter.memes["calm"] += 1
        world.say(
            f'{porter.id} did not rush. "{porter.pronoun("subject").capitalize()} can solve one small problem at a time," '
            f'{porter.pronoun()} told {porter.pronoun("object")}.'
        )
    world.say(
        f"At last {porter.pronoun()} smiled, {tool.action}, and the whole platform seemed to settle."
    )
    world.get("path").meters["blocked"] = 0
    world.get("path").meters["cleared"] = 1
    porter.meters["solved"] += 1


def help_one(world: World, porter: Entity, passenger: Entity, ordinal: str, bundle: BundleStyle, tool: ToolDef) -> None:
    passenger.meters["aboard"] = 1
    passenger.meters["waiting"] = 0
    porter.meters["trips"] += 1
    porter.memes["care"] += 1
    propagate(world, narrate=False)
    carried = {
        "blankets": "blanket roll",
        "pillows": "pillow",
        "storybooks": "storybook satchel",
    }[bundle.id]
    if tool.id == "wagon":
        move = f"set {passenger.id}'s {carried} into the wagon and rolled it around the puddle"
    elif tool.id == "stool":
        move = f"held {passenger.id}'s paw, claw, or wingtip and guided {passenger.pronoun('object')} up by the stool"
    else:
        move = f"tucked {passenger.id}'s {carried} under the umbrella and walked beside {passenger.pronoun('object')} through the gusts"
    world.say(
        f"{ordinal}, {porter.id} {move}. {passenger.id} climbed aboard with a grateful little sigh."
    )


def end_story(world: World, porter: Entity, passengers: list[Entity], trait: str) -> None:
    for passenger in passengers:
        passenger.memes["trust"] += 1
    porter.memes["pride"] += 1
    calm = outcome_of(world.facts["params"]) == "calm"
    if calm:
        world.say(
            f'Soon all three passengers were tucked into their seats. "{porter.id} helped me," one whispered. '
            f'"{porter.id} helped me too," said the next. "And me," said the third.'
        )
    else:
        world.say(
            f'Soon all three passengers were tucked into their seats. "{porter.id} almost hurried," one whispered, '
            f'"but then {porter.pronoun()} remembered to slow down and help carefully."'
        )
    world.say(
        "The Dream Train gave a soft ding and slid away into the dark, carrying blankets, pillows, and stories toward sleep."
    )
    world.say(
        f"{porter.id} watched the last silver window pass and learned something warm and true: "
        f"when you help one small creature, and then another, and then another, kindness can move a whole night along."
    )


def tell(
    stop: Stop,
    obstacle: Obstacle,
    tool: ToolDef,
    bundle: BundleStyle,
    porter_name: str,
    porter_gender: str,
    trait: str,
    passenger_seed: int,
) -> World:
    world = World(stop)
    porter = world.add(
        Entity(
            id=porter_name,
            kind="character",
            type=porter_gender,
            label="the porter",
            role="porter",
            traits=[trait],
        )
    )
    world.add(Entity(id="path", type="path", label="the path to the train"))
    set_choice = PASSENGER_SETS[passenger_seed % len(PASSENGER_SETS)]
    passengers: list[Entity] = []
    for idx, (name, animal) in enumerate(set_choice, 1):
        passengers.append(
            world.add(
                Entity(
                    id=name,
                    kind="character",
                    type=animal,
                    label=animal,
                    role="passenger",
                    attrs={"order": idx},
                )
            )
        )

    introduce(world, porter, stop)
    gather_passengers(world, porter, bundle, passengers)

    world.para()
    show_problem(world, obstacle)

    world.para()
    think_and_choose(world, porter, tool, obstacle, trait)

    world.para()
    help_one(world, porter, passengers[0], "First", bundle, tool)
    help_one(world, porter, passengers[1], "Then", bundle, tool)
    help_one(world, porter, passengers[2], "Last", bundle, tool)

    world.para()
    world.facts["params"] = StoryParams(
        stop=stop.id,
        obstacle=obstacle.id,
        tool=tool.id,
        bundle=bundle.id,
        porter_name=porter_name,
        porter_gender=porter_gender,
        trait=trait,
        seed=passenger_seed,
    )
    end_story(world, porter, passengers, trait)

    world.facts.update(
        porter=porter,
        passengers=passengers,
        stop=stop,
        obstacle=obstacle,
        tool=tool,
        bundle=bundle,
        outcome=outcome_of(world.facts["params"]),
        solved=world.get("path").meters["cleared"] >= THRESHOLD,
        trips=int(porter.meters["trips"]),
        passenger_names=[p.id for p in passengers],
    )
    return world


KNOWLEDGE = {
    "porter": [
        (
            "What is a porter?",
            "A porter is a helper who carries things and helps travelers move from one place to another. At a station, a porter helps people and their bags get where they need to go.",
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon is a little cart with wheels that helps carry things from one place to another. It is useful when the ground is wet or a load is too much to carry in your arms.",
        )
    ],
    "stool": [
        (
            "What does a stool help with?",
            "A stool makes a high place easier to reach because it gives you a smaller step first. That can make climbing safer and steadier.",
        )
    ],
    "umbrella": [
        (
            "What does an umbrella do?",
            "An umbrella makes a little roof over you. It can keep rain or wind from bothering what you are carrying.",
        )
    ],
    "puddle": [
        (
            "Why can a puddle be tricky?",
            "A puddle can make the ground slippery and splashy. Little feet and small bundles can get wet if no one is careful.",
        )
    ],
    "step": [
        (
            "Why can a big step feel hard at bedtime?",
            "When you are sleepy, lifting your legs high can feel harder than usual. A smaller step or a helping hand makes climbing easier.",
        )
    ],
    "wind": [
        (
            "Why is wind hard when you are carrying something light?",
            "Wind can tug, flap, and blow light things out of your hands. Covering them or holding them close helps keep them safe.",
        )
    ],
    "blanket": [
        (
            "Why do blankets feel cozy at bedtime?",
            "Blankets hold in warmth and make your body feel snug. That cozy feeling helps many children and animals settle down for sleep.",
        )
    ],
    "pillow": [
        (
            "What is a pillow for?",
            "A pillow supports your head when you rest. It helps make lying down softer and more comfortable.",
        )
    ],
    "storybook": [
        (
            "Why do people read storybooks before bed?",
            "A bedtime story can quiet the mind and make the evening feel gentle. Listening to a calm story helps many people get ready to sleep.",
        )
    ],
    "helping": [
        (
            "Why is helping others a good thing?",
            "Helping makes hard moments easier for someone else. It also helps a group feel safe, kind, and ready to work together.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "porter",
    "puddle",
    "step",
    "wind",
    "wagon",
    "stool",
    "umbrella",
    "blanket",
    "pillow",
    "storybook",
    "helping",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    porter = f["porter"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    bundle = f["bundle"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "porter" and uses repetition while a kind helper solves a {obstacle.label} problem.',
        f"Tell a gentle station story where a little porter named {porter.id} helps three sleepy passengers with {bundle.phrase} and figures out how to use {tool.phrase}.",
        f"Write a moral bedtime tale in which helping one passenger, then another, then another is the key to getting everyone safely onto the train.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    porter = f["porter"]
    stop = f["stop"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    bundle = f["bundle"]
    names = f["passenger_names"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {porter.id}, the little porter at {stop.label}, and three sleepy passengers named {', '.join(names[:-1])}, and {names[-1]}. The porter spends the whole story helping them reach the Dream Train.",
        ),
        (
            "What problem did the porter have to solve?",
            f"The path to the train was blocked by a {obstacle.label} problem. That mattered because the passengers were tired and worried about carrying their bedtime things safely.",
        ),
        (
            f"How did {porter.id} solve the problem?",
            f"{porter.id} used {tool.phrase} to handle the {obstacle.label}. The tool worked because it matched exactly what the platform needed: {obstacle.fix_need}.",
        ),
        (
            "How does the story use repetition?",
            f"The helping happens again and again: first one passenger is helped, then the next, and then the last. Repeating the same kind act makes the porter seem steady and dependable.",
        ),
    ]
    if outcome == "calm":
        qa.append(
            (
                f"Why did {porter.id} do well as a porter?",
                f"{porter.id} stayed patient and solved one small problem at a time. Because {porter.pronoun()} did not rush, all three passengers could board quietly and safely.",
            )
        )
    else:
        qa.append(
            (
                f"What did {porter.id} learn when things felt hurried?",
                f"{porter.id} almost rushed at first, but then stopped to breathe and think. That pause helped {porter.pronoun('object')} choose the right solution and finish the job kindly.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            "The story teaches that patient helping matters. When someone solves one problem carefully and keeps helping others, the whole group can feel safe and ready for rest.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"porter", "helping"}
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    bundle = world.facts["bundle"]
    tags |= set(obstacle.tags)
    tags |= set(tool.tags)
    tags |= set(bundle.tags)
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, O, T) :- stop(S), obstacle(O), tool(T), affords(S, O), solves(T, O).

calm_outcome :- chosen_trait(T), calm_trait(T).
outcome(calm) :- calm_outcome.
outcome(flustered) :- not calm_outcome.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for stop_id, stop in STOPS.items():
        lines.append(asp.fact("stop", stop_id))
        for obstacle_id in sorted(stop.affords):
            lines.append(asp.fact("affords", stop_id, obstacle_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for obstacle_id in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, obstacle_id))
    for trait in TRAITS:
        if calm_trait(trait):
            lines.append(asp.fact("calm_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_trait", params.trait)
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for case in cases:
        got = asp_outcome(case)
        want = outcome_of(case)
        if got != want:
            rc = 1
            print(f"MISMATCH in outcome for {case}: asp={got} python={want}")

    try:
        sample = generate(CURATED[0])
        if "porter" not in sample.story.lower():
            raise StoryError("smoke test failed: story did not contain 'porter'")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a little porter solves one gentle station problem and helps three sleepy passengers aboard."
    )
    ap.add_argument("--stop", choices=STOPS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--bundle", choices=BUNDLES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stop and args.obstacle and args.tool:
        stop = STOPS[args.stop]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if args.obstacle not in stop.affords or not valid_tool_for(args.obstacle, args.tool):
            raise StoryError(explain_rejection(stop, obstacle, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.stop is None or combo[0] == args.stop)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        if args.stop and args.obstacle and args.tool:
            raise StoryError(explain_rejection(STOPS[args.stop], OBSTACLES[args.obstacle], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    stop_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    bundle_id = args.bundle or rng.choice(sorted(BUNDLES))
    trait = args.trait or rng.choice(TRAITS)
    porter_gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        porter_name = args.name
    else:
        pool = GIRL_NAMES if porter_gender == "girl" else BOY_NAMES
        porter_name = rng.choice(pool)
    return StoryParams(
        stop=stop_id,
        obstacle=obstacle_id,
        tool=tool_id,
        bundle=bundle_id,
        porter_name=porter_name,
        porter_gender=porter_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        stop = STOPS[params.stop]
        obstacle = OBSTACLES[params.obstacle]
        tool = TOOLS[params.tool]
        bundle = BUNDLES[params.bundle]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if params.obstacle not in stop.affords or not valid_tool_for(params.obstacle, params.tool):
        raise StoryError(explain_rejection(stop, obstacle, tool))

    passenger_seed = params.seed if params.seed is not None else 0
    world = tell(
        stop=stop,
        obstacle=obstacle,
        tool=tool,
        bundle=bundle,
        porter_name=params.porter_name,
        porter_gender=params.porter_gender,
        trait=params.trait,
        passenger_seed=passenger_seed,
    )
    world.facts["params"] = params
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


CURATED = [
    StoryParams(
        stop="meadow",
        obstacle="puddle",
        tool="wagon",
        bundle="blankets",
        porter_name="Nora",
        porter_gender="girl",
        trait="patient",
    ),
    StoryParams(
        stop="forest",
        obstacle="tall_step",
        tool="stool",
        bundle="storybooks",
        porter_name="Milo",
        porter_gender="boy",
        trait="thoughtful",
    ),
    StoryParams(
        stop="harbor",
        obstacle="tall_step",
        tool="stool",
        bundle="pillows",
        porter_name="Ella",
        porter_gender="girl",
        trait="rushed",
    ),
    StoryParams(
        stop="forest",
        obstacle="windy_path",
        tool="umbrella",
        bundle="storybooks",
        porter_name="Theo",
        porter_gender="boy",
        trait="patient",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (stop, obstacle, tool) combos:\n")
        for stop_id, obstacle_id, tool_id in combos:
            print(f"  {stop_id:8} {obstacle_id:11} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        seeded_curated: list[StoryParams] = []
        for i, params in enumerate(CURATED):
            seeded_curated.append(
                StoryParams(
                    stop=params.stop,
                    obstacle=params.obstacle,
                    tool=params.tool,
                    bundle=params.bundle,
                    porter_name=params.porter_name,
                    porter_gender=params.porter_gender,
                    trait=params.trait,
                    seed=i,
                )
            )
        samples = [generate(p) for p in seeded_curated]
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
            header = f"### {p.porter_name} at {p.stop}: {p.obstacle} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
