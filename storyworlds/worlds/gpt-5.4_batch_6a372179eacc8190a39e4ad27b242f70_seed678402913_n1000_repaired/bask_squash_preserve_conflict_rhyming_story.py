#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bask_squash_preserve_conflict_rhyming_story.py
=========================================================================

A standalone storyworld for a tiny rhyming tale about a sunny harvest, a quarrel,
and the wiser difference between squashing fruit carelessly and squashing it to
preserve it.

Seed requirements:
- words: bask, squash, preserve
- feature: conflict
- style: rhyming story

The world models a child who wants to bask in the sun and squash ripe fruit on
the warm path just for fun, while another child hopes to preserve the fruit with
a grown-up. A reasonableness gate refuses unsafe "tools" such as boots. The
turn comes when the grown-up redirects the same urge to squash into a careful,
food-safe action in a bowl. If too much fruit was wasted before help arrived,
the family can only make a small sweet snack; otherwise they fill a jar of
preserve.

Run it
------
    python storyworlds/worlds/gpt-5.4/bask_squash_preserve_conflict_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/bask_squash_preserve_conflict_rhyming_story.py --fruit plums --place orchard
    python storyworlds/worlds/gpt-5.4/bask_squash_preserve_conflict_rhyming_story.py --tool boots
    python storyworlds/worlds/gpt-5.4/bask_squash_preserve_conflict_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/bask_squash_preserve_conflict_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    bask_spot: str
    fruit_ok: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    color: str
    yield_count: int
    jar_need: int
    loss_per_delay: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    clean: bool
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_spill_loss(world: World) -> list[str]:
    fruit = world.get("fruit")
    if fruit.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill_loss", int(fruit.meters["spilled"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fruit.meters["usable"] = max(0.0, fruit.meters["usable"] - fruit.meters["spilled"])
    fruit.meters["spilled"] = 0.0
    for kid_id in ("starter", "keeper"):
        if kid_id in world.entities:
            world.get(kid_id).memes["worry"] += 1
    return []


def _r_preserve_success(world: World) -> list[str]:
    fruit = world.get("fruit")
    if fruit.meters["mashed_in_bowl"] < THRESHOLD:
        return []
    sig = ("preserve_check", int(fruit.meters["usable"]), int(fruit.meters["mashed_in_bowl"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    need = world.facts["fruit_cfg"].jar_need
    if fruit.meters["usable"] >= need:
        world.get("jar").meters["filled"] = 1.0
        for kid_id in ("starter", "keeper"):
            world.get(kid_id).memes["relief"] += 1
            world.get(kid_id).memes["joy"] += 1
    else:
        world.get("bowl").meters["sweet_snack"] = 1.0
        for kid_id in ("starter", "keeper"):
            world.get(kid_id).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="spill_loss", tag="physical", apply=_r_spill_loss),
    Rule(name="preserve_success", tag="physical", apply=_r_preserve_success),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        bask_spot="the flat stone by the beans",
        fruit_ok={"berries", "plums"},
        tags={"garden"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        bask_spot="the low wall by the trees",
        fruit_ok={"plums", "apricots"},
        tags={"orchard"},
    ),
    "patio": Place(
        id="patio",
        label="the sunny patio",
        bask_spot="the warm step by the kitchen door",
        fruit_ok={"berries", "apricots"},
        tags={"patio"},
    ),
}

FRUITS = {
    "berries": Fruit(
        id="berries",
        label="berries",
        phrase="a basket of berries",
        color="purple",
        yield_count=8,
        jar_need=6,
        loss_per_delay=2,
        tags={"berries", "jam"},
    ),
    "plums": Fruit(
        id="plums",
        label="plums",
        phrase="a basket of plums",
        color="violet",
        yield_count=7,
        jar_need=5,
        loss_per_delay=2,
        tags={"plums", "jam"},
    ),
    "apricots": Fruit(
        id="apricots",
        label="apricots",
        phrase="a bowl of apricots",
        color="gold",
        yield_count=6,
        jar_need=4,
        loss_per_delay=1,
        tags={"apricots", "preserve"},
    ),
}

TOOLS = {
    "wooden_spoon": Tool(
        id="wooden_spoon",
        label="wooden spoon",
        phrase="a wooden spoon",
        sense=3,
        clean=True,
        power=1,
        tags={"spoon", "kitchen"},
    ),
    "masher": Tool(
        id="masher",
        label="potato masher",
        phrase="a potato masher",
        sense=3,
        clean=True,
        power=2,
        tags={"masher", "kitchen"},
    ),
    "boots": Tool(
        id="boots",
        label="rain boots",
        phrase="a pair of muddy rain boots",
        sense=1,
        clean=False,
        power=3,
        tags={"boots"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Poppy", "Tess", "Wren"]
BOY_NAMES = ["Ben", "Eli", "Finn", "Milo", "Owen", "Theo"]
TRAITS = ["hasty", "bouncy", "sunny", "careful", "steady", "patient"]


def valid_place_fruit(place_id: str, fruit_id: str) -> bool:
    return fruit_id in PLACES[place_id].fruit_ok


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN and tool.clean]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for fruit_id in sorted(FRUITS):
            if not valid_place_fruit(place_id, fruit_id):
                continue
            for tool in sensible_tools():
                combos.append((place_id, fruit_id, tool.id))
    return combos


@dataclass
class StoryParams:
    place: str
    fruit: str
    tool: str
    starter_name: str
    starter_gender: str
    keeper_name: str
    keeper_gender: str
    helper_type: str
    starter_trait: str
    keeper_trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        fruit="berries",
        tool="wooden_spoon",
        starter_name="Ben",
        starter_gender="boy",
        keeper_name="Lila",
        keeper_gender="girl",
        helper_type="grandmother",
        starter_trait="bouncy",
        keeper_trait="careful",
        delay=0,
    ),
    StoryParams(
        place="orchard",
        fruit="plums",
        tool="masher",
        starter_name="Mina",
        starter_gender="girl",
        keeper_name="Theo",
        keeper_gender="boy",
        helper_type="father",
        starter_trait="hasty",
        keeper_trait="steady",
        delay=1,
    ),
    StoryParams(
        place="patio",
        fruit="apricots",
        tool="wooden_spoon",
        starter_name="Owen",
        starter_gender="boy",
        keeper_name="Poppy",
        keeper_gender="girl",
        helper_type="mother",
        starter_trait="sunny",
        keeper_trait="patient",
        delay=2,
    ),
]


def enough_to_preserve(fruit: Fruit, delay: int) -> bool:
    remaining = fruit.yield_count - fruit.loss_per_delay * delay
    return remaining >= fruit.jar_need


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    fruit = FRUITS[params.fruit]
    if tool.sense < SENSE_MIN or not tool.clean:
        return "invalid"
    return "preserve" if enough_to_preserve(fruit, params.delay) else "snack"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    return (
        f"(No story: {tool.phrase} is not a sensible way to prepare fruit for food. "
        f"To preserve fruit, the squashing should happen with a clean kitchen tool "
        f"in a bowl, not with {tool.label}.)"
    )


def explain_place_fruit(place_id: str, fruit_id: str) -> str:
    return (
        f"(No story: {FRUITS[fruit_id].label} are not a good fit for {PLACES[place_id].label} "
        f"in this tiny world. Pick a fruit that the setting reasonably grows.)"
    )


def predict_preserve(world: World, delay: int) -> dict:
    sim = world.copy()
    fruit_cfg = sim.facts["fruit_cfg"]
    sim.get("fruit").meters["spilled"] += fruit_cfg.loss_per_delay * delay
    propagate(sim, narrate=False)
    remaining = int(sim.get("fruit").meters["usable"])
    return {
        "remaining": remaining,
        "enough": remaining >= fruit_cfg.jar_need,
    }


def opening(world: World, starter: Entity, keeper: Entity, place: Place, fruit: Fruit) -> None:
    starter.memes["joy"] += 1
    keeper.memes["joy"] += 1
    world.say(
        f"In {place.label}, where gold bees pass, "
        f"{starter.id} and {keeper.id} loved to bask."
    )
    world.say(
        f"They carried {fruit.phrase} through the noon-bright air, "
        f"with sticky little smiles and summer in their hair."
    )


def desire(world: World, starter: Entity, place: Place, fruit: Fruit) -> None:
    starter.memes["impulse"] += 1
    world.say(
        f'"Look!" cried {starter.id}. "By {place.bask_spot}, warm and dark and flush, '
        f'we could sit and laugh and squash, squash, squash!"'
    )


def caution(world: World, keeper: Entity, helper: Entity, fruit: Fruit, delay: int) -> None:
    pred = predict_preserve(world, delay)
    keeper.memes["caution"] += 1
    world.facts["predicted_remaining"] = pred["remaining"]
    if pred["enough"]:
        end = "Then we can preserve the rest in a shining little pot."
    else:
        end = "If too much is lost, there will be no jar to save, only a snack on the spot."
    world.say(
        f'{keeper.id} shook {keeper.pronoun("possessive")} head. '
        f'"Fruit on the path will mix with grit and dust. '
        f'If we keep it clean for {helper.label_word}, that would be wiser, kind, and just. '
        f'{end}"'
    )


def defy(world: World, starter: Entity, fruit: Fruit, delay: int) -> None:
    if delay <= 0:
        return
    starter.memes["defiance"] += 1
    fruit_ent = world.get("fruit")
    lost = fruit.loss_per_delay * delay
    fruit_ent.meters["spilled"] += lost
    fruit_ent.meters["bursts"] += lost
    propagate(world, narrate=False)
    world.say(
        f"But the wish to play came quick as a breeze; "
        f"{starter.id} gave a twirl with teasing ease."
    )
    if delay == 1:
        world.say(
            f"One {fruit.label[:-1] if fruit.label.endswith('s') else fruit.label} slipped and split with a sugary smack, "
            f"and {starter.id} hopped back from the {fruit.color} track."
        )
    else:
        world.say(
            f"A few soft {fruit.label} popped with a spluttery gush, "
            f"and the sunny stones wore a {fruit.color} blush."
        )


def helper_arrives(world: World, helper: Entity, starter: Entity, keeper: Entity) -> None:
    starter.memes["worry"] += 1
    keeper.memes["hope"] += 1
    world.say(
        f"Just then {helper.label_word} came through the door, "
        f"heard the cross little voices, and paused by the floor."
    )
    world.say(
        f'"No boots for food," said {helper.label_word}, calm and clear. '
        f'"If you want to squash, there is a better way right here."'
    )


def redirect(world: World, helper: Entity, tool: Tool, fruit: Fruit) -> None:
    world.get("fruit").meters["mashed_in_bowl"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} fetched a bowl and {tool.phrase} too. "
        f'"We can squash them clean and preserve them, if that is what you want to do."'
    )
    world.say(
        f"The same small hands that reached for the path now worked in a careful curve, "
        f"pressing the fruit with kitchen care to help the sweet jars preserve."
    )


def resolution(world: World, starter: Entity, keeper: Entity, helper: Entity, fruit: Fruit) -> None:
    jar = world.get("jar")
    bowl = world.get("bowl")
    if jar.meters["filled"] >= THRESHOLD:
        world.say(
            f"Soon a jar stood warm on the sill, jewel-bright and round. "
            f'"This is how we preserve," said {helper.label_word}, '
            f'"with patient hands and clean things all around."'
        )
        world.say(
            f"{starter.id} and {keeper.id} clinked spoons with gentler nerve. "
            f"They still could bask in the evening sun, and now they had jam to serve."
        )
        outcome = "preserve"
    elif bowl.meters["sweet_snack"] >= THRESHOLD:
        world.say(
            f"There was not quite enough for a jar to keep till snow, "
            f"but the bowl made a warm sweet topping with a sunset glow."
        )
        world.say(
            f'"Next time we save more first," said {starter.id}, quiet but brave. '
            f'So they shared their fruity snack that day, and learned what it means to save.'
        )
        outcome = "snack"
    else:
        raise StoryError("The story reached no reasonable ending.")
    world.facts["outcome"] = outcome


def tell(
    place: Place,
    fruit: Fruit,
    tool: Tool,
    starter_name: str,
    starter_gender: str,
    keeper_name: str,
    keeper_gender: str,
    helper_type: str,
    starter_trait: str,
    keeper_trait: str,
    delay: int,
) -> World:
    world = World()
    starter = world.add(Entity(
        id=starter_name,
        kind="character",
        type=starter_gender,
        role="starter",
        traits=[starter_trait],
    ))
    keeper = world.add(Entity(
        id=keeper_name,
        kind="character",
        type=keeper_gender,
        role="keeper",
        traits=[keeper_trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    fruit_ent = world.add(Entity(
        id="fruit",
        type="fruit",
        label=fruit.label,
        phrase=fruit.phrase,
        tags=set(fruit.tags),
    ))
    fruit_ent.meters["usable"] = float(fruit.yield_count)
    world.add(Entity(id="jar", type="jar", label="jar"))
    world.add(Entity(id="bowl", type="bowl", label="bowl"))

    world.facts.update(
        place=place,
        fruit_cfg=fruit,
        tool=tool,
        starter=starter,
        keeper=keeper,
        helper=helper,
        delay=delay,
    )

    opening(world, starter, keeper, place, fruit)
    world.para()
    desire(world, starter, place, fruit)
    caution(world, keeper, helper, fruit, delay)
    defy(world, starter, fruit, delay)
    world.para()
    helper_arrives(world, helper, starter, keeper)
    redirect(world, helper, tool, fruit)
    world.para()
    resolution(world, starter, keeper, helper, fruit)

    world.facts["remaining"] = int(world.get("fruit").meters["usable"])
    world.facts["spilled_before_help"] = fruit.yield_count - int(world.get("fruit").meters["usable"])
    return world


KNOWLEDGE = {
    "bask": [
        (
            "What does bask mean?",
            "To bask means to sit or stand in warm sunshine and enjoy the heat. People and animals both bask when the sun feels gentle and nice."
        )
    ],
    "squash": [
        (
            "What does squash mean in cooking?",
            "In cooking, to squash something means to press it until it becomes soft or flat. Fruit can be squashed gently in a bowl when you are making jam or sauce."
        )
    ],
    "preserve": [
        (
            "What does preserve mean for fruit?",
            "To preserve fruit means to prepare it so it can be kept and eaten later. People often cook fruit with sugar and put it into a clean jar."
        )
    ],
    "jam": [
        (
            "Why do people make jam or preserves?",
            "They make preserves so sweet fruit can last longer instead of spoiling quickly. It is a way to save summer fruit for another day."
        )
    ],
    "clean_tools": [
        (
            "Why should food be prepared with clean tools?",
            "Clean tools help keep dirt and germs out of food. That makes the food safer to eat."
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees are grown together. People may pick plums, peaches, or other fruit there."
        )
    ],
    "garden": [
        (
            "What grows in a garden?",
            "A garden can grow flowers, vegetables, and sometimes fruit. It is a place where people care for plants and harvest what is ready."
        )
    ],
    "patio": [
        (
            "What is a patio?",
            "A patio is a flat outdoor space beside a house. Families may sit, talk, or bring bowls of fruit there in sunny weather."
        )
    ],
}
KNOWLEDGE_ORDER = ["bask", "squash", "preserve", "jam", "clean_tools", "orchard", "garden", "patio"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    starter = f["starter"]
    keeper = f["keeper"]
    place = f["place"]
    fruit = f["fruit_cfg"]
    outcome = f.get("outcome")
    tail = "ends with a bright jar on the sill." if outcome == "preserve" else "ends with a shared sweet snack and a lesson."
    return [
        f'Write a rhyming story for a 3-to-5-year-old that uses the words "bask," "squash," and "preserve."',
        f"Tell a gentle conflict story where {starter.id} wants to squash {fruit.label} on the path while {keeper.id} wants to preserve them in {place.label}.",
        f"Write a child-facing rhyming tale about a summer quarrel over fruit that {tail}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    starter = f["starter"]
    keeper = f["keeper"]
    helper = f["helper"]
    fruit = f["fruit_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    remaining = f["remaining"]
    spilled = f["spilled_before_help"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {starter.id} and {keeper.id}, two children in {place.label}, and {helper.label_word} who helps them. The story follows their little quarrel over what to do with the fruit."
        ),
        (
            f"Why did {starter.id} and {keeper.id} argue?",
            f"{starter.id} wanted to bask in the sun and squash the {fruit.label} on the warm path for fun, but {keeper.id} wanted to keep them clean and preserve them. Their conflict was really about play versus saving the fruit carefully."
        ),
        (
            f"What did {helper.label_word} teach them?",
            f"{helper.label_word.capitalize()} taught them that squashing fruit is not always wrong, but it should be done with a clean tool in a bowl if the fruit is for eating. That turned the quarrel into a useful job."
        ),
    ]
    if spilled > 0:
        qa.append(
            (
                f"What happened before {helper.label_word} stepped in?",
                f"Some fruit burst on the path before help arrived, so part of the harvest was lost. Because of that mess, only {remaining} pieces were still clean and usable."
            )
        )
    else:
        qa.append(
            (
                f"What changed when {helper.label_word} arrived?",
                f"The grown-up stopped the children from using the path and offered a clean bowl and kitchen tool instead. That changed squashing from messy play into careful cooking."
            )
        )
    if outcome == "preserve":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a shining jar of preserve on the sill. The ending shows that the children learned how to bask in the sun without wasting the fruit."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a sweet bowl to eat that day instead of a jar to save for later. The ending shows they learned a lesson, even though too much fruit had been wasted to preserve."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bask", "squash", "preserve", "jam", "clean_tools"}
    place = world.facts["place"]
    tags |= set(place.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M, clean(T).
valid(P, F, T) :- place(P), fruit(F), tool(T), grows(P, F), safe_tool(T).

remaining(Y - L * D) :- chosen_fruit(F), yield(F, Y), loss(F, L), delay(D).
enough :- chosen_fruit(F), remaining(R), jar_need(F, N), R >= N.

outcome(preserve) :- chosen_tool(T), safe_tool(T), enough.
outcome(snack) :- chosen_tool(T), safe_tool(T), not enough.
invalid_choice :- chosen_tool(T), not safe_tool(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for fruit_id in sorted(place.fruit_ok):
            lines.append(asp.fact("grows", place_id, fruit_id))
    for fruit_id, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fruit_id))
        lines.append(asp.fact("yield", fruit_id, fruit.yield_count))
        lines.append(asp.fact("jar_need", fruit_id, fruit.jar_need))
        lines.append(asp.fact("loss", fruit_id, fruit.loss_per_delay))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        if tool.clean:
            lines.append(asp.fact("clean", tool_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_safe_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show safe_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "safe_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_fruit", params.fruit),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1.\n#show invalid_choice/0."))
    invalid = asp.atoms(model, "invalid_choice")
    if invalid:
        return "invalid"
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a sunny fruit quarrel about bask, squash, and preserve."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much fruit is lost before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.fruit and not valid_place_fruit(args.place, args.fruit):
        raise StoryError(explain_place_fruit(args.place, args.fruit))
    if args.tool and (TOOLS[args.tool].sense < SENSE_MIN or not TOOLS[args.tool].clean):
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, fruit, tool = rng.choice(sorted(combos))
    starter_name, starter_gender = _pick_child(rng)
    keeper_name, keeper_gender = _pick_child(rng, avoid=starter_name)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    starter_trait = rng.choice(TRAITS[:3])
    keeper_trait = rng.choice(TRAITS[3:])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        fruit=fruit,
        tool=tool,
        starter_name=starter_name,
        starter_gender=starter_gender,
        keeper_name=keeper_name,
        keeper_gender=keeper_gender,
        helper_type=helper_type,
        starter_trait=starter_trait,
        keeper_trait=keeper_trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.fruit not in FRUITS:
        raise StoryError(f"(Unknown fruit: {params.fruit})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")
    if not valid_place_fruit(params.place, params.fruit):
        raise StoryError(explain_place_fruit(params.place, params.fruit))
    if TOOLS[params.tool].sense < SENSE_MIN or not TOOLS[params.tool].clean:
        raise StoryError(explain_tool(params.tool))

    world = tell(
        place=PLACES[params.place],
        fruit=FRUITS[params.fruit],
        tool=TOOLS[params.tool],
        starter_name=params.starter_name,
        starter_gender=params.starter_gender,
        keeper_name=params.keeper_name,
        keeper_gender=params.keeper_gender,
        helper_type=params.helper_type,
        starter_trait=params.starter_trait,
        keeper_trait=params.keeper_trait,
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

    clingo_tools = set(asp_safe_tools())
    python_tools = {tool.id for tool in sensible_tools()}
    if clingo_tools == python_tools:
        print(f"OK: safe tools match ({sorted(clingo_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in safe tools: clingo={sorted(clingo_tools)} python={sorted(python_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke_params = resolve_params(parser.parse_args([]), random.Random(7))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True)
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show safe_tool/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"safe tools: {', '.join(asp_safe_tools())}\n")
        print(f"{len(combos)} compatible (place, fruit, tool) combos:\n")
        for place, fruit, tool in combos:
            print(f"  {place:8} {fruit:9} {tool}")
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
            header = f"### {p.starter_name} & {p.keeper_name}: {p.fruit} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
