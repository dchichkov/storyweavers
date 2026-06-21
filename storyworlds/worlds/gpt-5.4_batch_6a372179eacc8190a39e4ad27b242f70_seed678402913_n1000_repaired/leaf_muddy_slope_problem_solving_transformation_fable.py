#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/leaf_muddy_slope_problem_solving_transformation_fable.py
===================================================================================

A small storyworld about a leaf on a muddy slope. The leaf begins proud of its
smooth shape, meets a creature in trouble, and solves the problem only after a
physical transformation makes the leaf useful in a new way.

The world is built as a tiny fable:
- premise: a leaf lands on a muddy slope and wants to stay neat and important
- tension: a smaller creature is blocked by mud, a rut, or splashing muck
- turn: the leaf is bent, curled, or stretched by the slope itself
- resolution: the changed shape becomes the very tool that solves the problem

Run it
------
    python storyworlds/worlds/gpt-5.4/leaf_muddy_slope_problem_solving_transformation_fable.py
    python storyworlds/worlds/gpt-5.4/leaf_muddy_slope_problem_solving_transformation_fable.py --creature ant --obstacle rut --form bridge
    python storyworlds/worlds/gpt-5.4/leaf_muddy_slope_problem_solving_transformation_fable.py --obstacle splash --form sled
    python storyworlds/worlds/gpt-5.4/leaf_muddy_slope_problem_solving_transformation_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/leaf_muddy_slope_problem_solving_transformation_fable.py --all
    python storyworlds/worlds/gpt-5.4/leaf_muddy_slope_problem_solving_transformation_fable.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        neutral = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"ant", "beetle", "snail", "leaf", "slope"}:
            return neutral[case]
        return neutral[case]


@dataclass
class CreatureKind:
    id: str
    label: str
    phrase: str
    move: str
    trouble: str
    need: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    opening: str
    danger: str
    ask: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Form:
    id: str
    label: str
    phrase: str
    transform_text: str
    solve_text: str
    solves: set[str] = field(default_factory=set)
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


def _r_stuck(world: World) -> list[str]:
    creature = world.get("creature")
    obstacle = world.facts["obstacle_cfg"]
    if creature.meters["trying"] < THRESHOLD:
        return []
    sig = ("stuck", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["blocked"] += 1
    creature.memes["worry"] += 1
    world.get("leaf").memes["care"] += 1
    return ["__blocked__"]


def _r_helped(world: World) -> list[str]:
    leaf = world.get("leaf")
    creature = world.get("creature")
    if leaf.meters["useful_form"] < THRESHOLD or creature.meters["help_attempt"] < THRESHOLD:
        return []
    sig = ("helped", world.facts["form_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["safe"] += 1
    creature.meters["blocked"] = 0.0
    creature.memes["worry"] = 0.0
    creature.memes["gratitude"] += 1
    leaf.memes["purpose"] += 1
    leaf.memes["pride"] = 0.0
    leaf.memes["wisdom"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="helped", tag="social", apply=_r_helped),
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


CREATURES = {
    "ant": CreatureKind(
        id="ant",
        label="ant",
        phrase="a small ant named Pip",
        move="pick its way",
        trouble="a muddy rut cut across the slope like a ditch",
        need="carry a seed to a dry patch below",
        solves={"rut", "ooze"},
        tags={"ant"},
    ),
    "beetle": CreatureKind(
        id="beetle",
        label="beetle",
        phrase="a round little beetle named Brim",
        move="roll carefully",
        trouble="the mud was so slick that each step sent it sliding",
        need="reach the blackberry root at the bottom of the slope",
        solves={"ooze"},
        tags={"beetle"},
    ),
    "snail": CreatureKind(
        id="snail",
        label="snail",
        phrase="a young snail named Moss",
        move="inch along",
        trouble="fat drops of muddy water kept splashing down the slope",
        need="find a quiet place before the splashes filled its path",
        solves={"splash"},
        tags={"snail"},
    ),
}

OBSTACLES = {
    "rut": Obstacle(
        id="rut",
        label="rut",
        phrase="a muddy rut",
        opening="A narrow rut crossed the path like a brown little river.",
        danger="If the ant stepped down into it, the seed would tumble away.",
        ask='"How can I get across?" the ant asked.',
        solves={"bridge"},
        tags={"rut", "mud"},
    ),
    "ooze": Obstacle(
        id="ooze",
        label="slick ooze",
        phrase="a slick patch of ooze",
        opening="Below them lay a shiny patch of ooze where the slope turned slippery.",
        danger="Anything with small feet could slide straight into a cold puddle at the bottom.",
        ask='"How can I get down without slipping?" the little creature asked.',
        solves={"sled"},
        tags={"mud", "slope"},
    ),
    "splash": Obstacle(
        id="splash",
        label="muddy splash",
        phrase="a curtain of muddy splashes",
        opening="Above them, drops of muddy water kept hopping from stone to stone and splashing down.",
        danger="A slow traveler would be peppered with mud before reaching shelter.",
        ask='"How can I stay safe until the splashing stops?" the snail asked.',
        solves={"hood"},
        tags={"mud", "rain"},
    ),
}

FORMS = {
    "bridge": Form(
        id="bridge",
        label="bridge",
        phrase="a little bridge",
        transform_text="The slope pressed the leaf flat between two pebbles until it stretched wide and steady.",
        solve_text="The leaf laid itself across the rut so the ant could walk over on a dry, trembling road.",
        solves={"rut"},
        tags={"bridge"},
    ),
    "sled": Form(
        id="sled",
        label="sled",
        phrase="a tiny sled",
        transform_text="Mud curled the leaf's edges upward, and all at once it was no longer a flat leaf but a tiny sled.",
        solve_text="The leaf let the creature climb in and slid with it down the ooze in one smooth, safe whisper.",
        solves={"ooze"},
        tags={"sled"},
    ),
    "hood": Form(
        id="hood",
        label="hood",
        phrase="a soft hood",
        transform_text="A wet breeze bent the leaf over itself until it became a soft hood with a clean space beneath.",
        solve_text="The leaf held itself above the snail like a roof and caught the muddy splashes on its own back.",
        solves={"splash"},
        tags={"hood"},
    ),
}


@dataclass
class StoryParams:
    creature: str
    obstacle: str
    form: str
    leaf_name: str
    parent_tree: str
    seed: Optional[int] = None


LEAF_NAMES = ["Amber", "Lilt", "Maple", "Saffy", "Tawny", "Clover"]
TREES = ["oak", "maple", "elm", "beech"]

CURATED = [
    StoryParams(
        creature="ant",
        obstacle="rut",
        form="bridge",
        leaf_name="Amber",
        parent_tree="oak",
    ),
    StoryParams(
        creature="beetle",
        obstacle="ooze",
        form="sled",
        leaf_name="Lilt",
        parent_tree="maple",
    ),
    StoryParams(
        creature="snail",
        obstacle="splash",
        form="hood",
        leaf_name="Tawny",
        parent_tree="beech",
    ),
]


def valid_combo(creature_id: str, obstacle_id: str, form_id: str) -> bool:
    if creature_id not in CREATURES or obstacle_id not in OBSTACLES or form_id not in FORMS:
        return False
    creature = CREATURES[creature_id]
    obstacle = OBSTACLES[obstacle_id]
    form = FORMS[form_id]
    return obstacle_id in creature.solves and form_id in obstacle.solves and obstacle_id in form.solves


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for creature_id in CREATURES:
        for obstacle_id in OBSTACLES:
            for form_id in FORMS:
                if valid_combo(creature_id, obstacle_id, form_id):
                    out.append((creature_id, obstacle_id, form_id))
    return out


def explain_rejection(creature_id: str, obstacle_id: str, form_id: str) -> str:
    if creature_id not in CREATURES:
        return f"(No story: unknown creature '{creature_id}'.)"
    if obstacle_id not in OBSTACLES:
        return f"(No story: unknown obstacle '{obstacle_id}'.)"
    if form_id not in FORMS:
        return f"(No story: unknown form '{form_id}'.)"
    creature = CREATURES[creature_id]
    obstacle = OBSTACLES[obstacle_id]
    form = FORMS[form_id]
    if obstacle_id not in creature.solves:
        return (
            f"(No story: {creature.label} does not face {obstacle.phrase} in this world. "
            f"Pick an obstacle that matches the creature's kind of trouble.)"
        )
    if form_id not in obstacle.solves or obstacle_id not in form.solves:
        return (
            f"(No story: turning into {form.phrase} would not honestly solve {obstacle.phrase}. "
            f"This fable only tells fixes that fit the problem.)"
        )
    return "(No story: that combination is not reasonable.)"


def predict_solution(world: World, form_id: str) -> dict:
    sim = world.copy()
    leaf = sim.get("leaf")
    creature = sim.get("creature")
    if form_id == sim.facts["form_cfg"].id:
        leaf.meters["useful_form"] += 1
        creature.meters["help_attempt"] += 1
        propagate(sim, narrate=False)
    return {
        "safe": creature.meters["safe"] >= THRESHOLD,
        "purpose": leaf.memes["purpose"] >= THRESHOLD,
    }


def introduce(world: World, leaf: Entity, creature: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"On a muddy slope under an old {world.facts['parent_tree']} tree, a leaf named {leaf.id} came twirling down and landed with a soft pat."
    )
    world.say(
        f"{leaf.id} was smooth, bright, and very pleased with itself. It liked lying flat where the light could shine on every edge."
    )
    world.say(
        f"Not far away, {creature.phrase} was trying to {CREATURES[creature.type].move} down the hill, but {creature.attrs['trouble']}."
    )
    world.say(obstacle.opening)


def problem(world: World, leaf: Entity, creature: Entity, obstacle: Obstacle) -> None:
    creature.meters["trying"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{obstacle.danger} {creature.id} stopped, looked at the leaf, and said, {obstacle.ask}"
    )
    leaf.memes["pride"] += 1
    world.say(
        f'{leaf.id} rustled a little. "I am only a leaf," it said, though inside it was thinking more about staying neat than being useful.'
    )


def failed_wish(world: World, leaf: Entity) -> None:
    leaf.meters["muddy"] += 1
    leaf.memes["shame"] += 1
    world.say(
        f"But the slope did not care what {leaf.id} wished. Mud kissed one edge, a pebble caught another, and the leaf was tugged out of its old shape."
    )


def transform(world: World, leaf: Entity, form: Form) -> None:
    if form.id == "bridge":
        leaf.meters["flat"] += 1
    elif form.id == "sled":
        leaf.meters["curled"] += 1
    elif form.id == "hood":
        leaf.meters["bent"] += 1
    leaf.meters["useful_form"] += 1
    leaf.memes["shame"] += 1
    pred = predict_solution(world, form.id)
    world.facts["predicted_safe"] = pred["safe"]
    world.say(form.transform_text)
    world.say(
        f'At first {leaf.id} wanted to sigh. "I do not look the way I did," it whispered.'
    )


def insight(world: World, leaf: Entity, creature: Entity, form: Form) -> None:
    if world.facts.get("predicted_safe"):
        leaf.memes["care"] += 1
        world.say(
            f"Then {leaf.id} saw {creature.id}'s worried face and understood something new: a changed shape can still be a good shape."
        )
    else:
        world.say(
            f"{leaf.id} looked at its new shape and wondered what it was for."
        )


def help_creature(world: World, leaf: Entity, creature: Entity, form: Form) -> None:
    creature.meters["help_attempt"] += 1
    propagate(world, narrate=False)
    world.say(form.solve_text)
    if creature.meters["safe"] >= THRESHOLD:
        world.say(
            f"{creature.id.capitalize()} gave a small, glad sound. The hard part of the slope was no longer the end of the journey."
        )


def ending(world: World, leaf: Entity, creature: Entity, form: Form) -> None:
    creature.meters["journey_done"] += 1
    world.say(
        f'Soon {creature.id} reached safety and turned back. "Thank you," it said. "You were just what I needed."'
    )
    world.say(
        f"{leaf.id} rested on the muddy slope, no longer worried about being perfectly smooth. It had become {form.phrase}, and because of that, it had done a kind thing well."
    )
    world.say(
        "From then on, whenever the slope changed what came tumbling down, the little creatures remembered that losing one shape is not the same as losing one's worth."
    )


def moral(world: World) -> None:
    world.say("So the muddy slope taught its quiet lesson: when trouble changes you, wisdom asks what good your new shape can do.")


def tell(creature_cfg: CreatureKind, obstacle_cfg: Obstacle, form_cfg: Form,
         leaf_name: str, parent_tree: str) -> World:
    world = World()
    leaf = world.add(
        Entity(
            id=leaf_name,
            kind="character",
            type="leaf",
            label="leaf",
            phrase=f"a leaf named {leaf_name}",
            role="hero",
            tags={"leaf"},
        )
    )
    creature_name = creature_cfg.phrase.split(" named ", 1)[1] if " named " in creature_cfg.phrase else creature_cfg.label
    creature = world.add(
        Entity(
            id=creature_name,
            kind="character",
            type=creature_cfg.id,
            label=creature_cfg.label,
            phrase=creature_cfg.phrase,
            role="traveler",
            attrs={"trouble": creature_cfg.trouble, "need": creature_cfg.need},
            tags=set(creature_cfg.tags),
        )
    )
    slope = world.add(
        Entity(
            id="slope",
            kind="thing",
            type="slope",
            label="muddy slope",
            phrase="a muddy slope",
            tags={"mud", "slope"},
        )
    )
    slope.meters["slick"] += 1
    leaf.memes["pride"] += 1

    world.facts.update(
        leaf=leaf,
        creature=creature,
        slope=slope,
        creature_cfg=creature_cfg,
        obstacle_cfg=obstacle_cfg,
        form_cfg=form_cfg,
        parent_tree=parent_tree,
    )

    introduce(world, leaf, creature, obstacle_cfg)
    world.para()
    problem(world, leaf, creature, obstacle_cfg)
    failed_wish(world, leaf)
    world.para()
    transform(world, leaf, form_cfg)
    insight(world, leaf, creature, form_cfg)
    help_creature(world, leaf, creature, form_cfg)
    world.para()
    ending(world, leaf, creature, form_cfg)
    moral(world)

    world.facts.update(
        solved=creature.meters["safe"] >= THRESHOLD,
        transformed=form_cfg.id,
        blocked=True,
    )
    return world


KNOWLEDGE = {
    "leaf": [
        (
            "What is a leaf?",
            "A leaf is the flat green or brown part that grows on a plant or tree. Leaves catch sunlight when they are on the tree, and after they fall they can still be useful in small ways.",
        )
    ],
    "mud": [
        (
            "What is mud?",
            "Mud is wet dirt. It can be soft and slippery, so little feet can sink or slide in it.",
        )
    ],
    "slope": [
        (
            "What is a slope?",
            "A slope is ground that tilts up or down instead of staying flat. Things on a slope can slide because gravity pulls them downhill.",
        )
    ],
    "rut": [
        (
            "What is a rut?",
            "A rut is a narrow track or groove pressed into soft ground. For a tiny creature, even a small rut can feel like a ditch.",
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge lets you cross over a gap or a stream without going down into it. Even a tiny bridge can make a hard path safe.",
        )
    ],
    "sled": [
        (
            "What is a sled?",
            "A sled is something that slides over snow or another slick surface. If it is steady, it can carry someone safely over slippery ground.",
        )
    ],
    "hood": [
        (
            "What does a hood or little roof do?",
            "A hood or roof covers what is underneath. It keeps splashes or rain from landing right on top of you.",
        )
    ],
    "ant": [
        (
            "Why can a tiny ant have trouble on mud?",
            "An ant is small, so a little gap or a sticky patch can feel much bigger to it. Mud can block the ant or make it lose what it is carrying.",
        )
    ],
    "beetle": [
        (
            "Why can a beetle slide on a muddy slope?",
            "Mud can be slick, and a slope tilts downward. If a beetle loses its grip, gravity can make it slide.",
        )
    ],
    "snail": [
        (
            "Why would a snail need shelter from splashes?",
            "A snail moves slowly, so it cannot dart away fast. A cover above it can give it time to stay safe while the splashing passes.",
        )
    ],
    "change": [
        (
            "Can changing shape ever help?",
            "Yes. Something can look different and still become more useful for a new problem. In fables, change often helps a character discover a wiser purpose.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "leaf",
    "mud",
    "slope",
    "rut",
    "bridge",
    "sled",
    "hood",
    "ant",
    "beetle",
    "snail",
    "change",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leaf = f["leaf"]
    creature = f["creature"]
    obstacle = f["obstacle_cfg"]
    form = f["form_cfg"]
    return [
        'Write a short fable for a 3-to-5-year-old set on a muddy slope that includes the word "leaf".',
        f"Tell a gentle fable where a proud leaf changes shape into {form.phrase} and solves {creature.id}'s problem with {obstacle.phrase}.",
        f"Write a story about problem solving and transformation in which a leaf first dislikes being changed, then learns that the new shape can help someone else.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leaf = f["leaf"]
    creature = f["creature"]
    obstacle = f["obstacle_cfg"]
    form = f["form_cfg"]
    out = [
        (
            "Who is the story about?",
            f"It is about a leaf named {leaf.id} and {creature.phrase}. They meet on a muddy slope where the small creature is in trouble.",
        ),
        (
            "What problem happened on the muddy slope?",
            f"The problem was {obstacle.phrase}. It blocked {creature.id} and made the journey feel unsafe. {obstacle.danger}",
        ),
        (
            f"How did the leaf change?",
            f"The slope changed {leaf.id} into {form.phrase}. At first the leaf felt sorry to lose its old shape, but the new shape turned out to be useful.",
        ),
        (
            f"How did {leaf.id} solve the problem?",
            f"{leaf.id} used the new shape to help. {form.solve_text} Because the leaf fit the problem, {creature.id} could go on safely.",
        ),
        (
            "What did the leaf learn?",
            f"{leaf.id} learned that being changed does not mean being ruined. The leaf became helpful precisely because it stopped clinging to its old shape.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"leaf", "mud", "slope", "change"}
    tags |= set(f["creature_cfg"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["form_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supports_creature(C, O) :- creature(C), obstacle(O), creature_solves(C, O).
supports_form(F, O) :- form(F), obstacle(O), form_solves(F, O), obstacle_solves(O, F).
valid(C, O, F) :- creature(C), obstacle(O), form(F), supports_creature(C, O), supports_form(F, O).

chosen_valid :- chosen_creature(C), chosen_obstacle(O), chosen_form(F), valid(C, O, F).
outcome(helped) :- chosen_valid.
outcome(rejected) :- chosen_creature(_), chosen_obstacle(_), chosen_form(_), not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        for obstacle_id in sorted(creature.solves):
            lines.append(asp.fact("creature_solves", creature_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        for form_id in sorted(obstacle.solves):
            lines.append(asp.fact("obstacle_solves", obstacle_id, form_id))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        for obstacle_id in sorted(form.solves):
            lines.append(asp.fact("form_solves", form_id, obstacle_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_creature", params.creature),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_form", params.form),
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        expected = "helped" if valid_combo(params.creature, params.obstacle, params.form) else "rejected"
        got = asp_outcome(params)
        if got != expected:
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={got} python={expected}")

    try:
        sample = generate(
            StoryParams(
                creature=CURATED[0].creature,
                obstacle=CURATED[0].obstacle,
                form=CURATED[0].form,
                leaf_name=CURATED[0].leaf_name,
                parent_tree=CURATED[0].parent_tree,
                seed=0,
            )
        )
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    if rc == 0:
        print("OK: ASP parity and smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a leaf on a muddy slope learns to solve a problem by changing shape."
    )
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--form", choices=sorted(FORMS))
    ap.add_argument("--leaf-name")
    ap.add_argument("--tree", choices=sorted(TREES))
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
    if args.creature and args.obstacle and args.form:
        if not valid_combo(args.creature, args.obstacle, args.form):
            raise StoryError(explain_rejection(args.creature, args.obstacle, args.form))

    combos = [
        combo
        for combo in valid_combos()
        if (args.creature is None or combo[0] == args.creature)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.form is None or combo[2] == args.form)
    ]
    if not combos:
        if args.creature and args.obstacle and args.form:
            raise StoryError(explain_rejection(args.creature, args.obstacle, args.form))
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, obstacle_id, form_id = rng.choice(sorted(combos))
    leaf_name = args.leaf_name or rng.choice(LEAF_NAMES)
    parent_tree = args.tree or rng.choice(TREES)
    return StoryParams(
        creature=creature_id,
        obstacle=obstacle_id,
        form=form_id,
        leaf_name=leaf_name,
        parent_tree=parent_tree,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.creature, params.obstacle, params.form):
        raise StoryError(explain_rejection(params.creature, params.obstacle, params.form))

    if params.creature not in CREATURES or params.obstacle not in OBSTACLES or params.form not in FORMS:
        raise StoryError("(No story: one or more params do not match this world's registries.)")

    world = tell(
        creature_cfg=CREATURES[params.creature],
        obstacle_cfg=OBSTACLES[params.obstacle],
        form_cfg=FORMS[params.form],
        leaf_name=params.leaf_name,
        parent_tree=params.parent_tree,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, obstacle, form) combos:\n")
        for creature_id, obstacle_id, form_id in combos:
            print(f"  {creature_id:7} {obstacle_id:7} {form_id}")
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
            header = f"### {p.leaf_name}: {p.creature} / {p.obstacle} / {p.form}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
