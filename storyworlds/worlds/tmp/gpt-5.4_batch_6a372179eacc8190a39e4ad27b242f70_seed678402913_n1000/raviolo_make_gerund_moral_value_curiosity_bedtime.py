#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/raviolo_make_gerund_moral_value_curiosity_bedtime.py
================================================================================

A standalone story world for a bedtime tale about curiosity, patience, and
asking a grown-up for help.

Seed constraints rebuilt as a tiny simulation:
- include the words "raviolo" and "make-gerund"
- feature Moral Value and Curiosity
- read like a Bedtime Story

The world models one sleepy child who notices a mysterious kitchen clue at
bedtime and wants to investigate. Curiosity can lead either to a gentle,
safe discovery or to a brief oops moment, depending on how the child acts.
The moral value is not "never be curious"; it is "be curious safely, and ask
for help when you do not understand something."

Run it
------
    python storyworlds/worlds/gpt-5.4/raviolo_make_gerund_moral_value_curiosity_bedtime.py
    python storyworlds/worlds/gpt-5.4/raviolo_make_gerund_moral_value_curiosity_bedtime.py --mystery bowl --approach ask
    python storyworlds/worlds/gpt-5.4/raviolo_make_gerund_moral_value_curiosity_bedtime.py --mystery pot --approach climb
    python storyworlds/worlds/gpt-5.4/raviolo_make_gerund_moral_value_curiosity_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/raviolo_make_gerund_moral_value_curiosity_bedtime.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    hot: bool = False
    high: bool = False
    edible: bool = False
    glowing: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mystery:
    id: str
    clue: str
    source_phrase: str
    sound: str
    hidden_item: str
    hidden_phrase: str
    danger: str
    risk: int
    heat: int
    height: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    sense: int
    solo: bool
    steady: int
    success_text: str
    oops_text: str
    adult_text: str
    resolution_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    phrase: str
    bedtime_line: str
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


def _r_wobble(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["balance_risk"] < THRESHOLD:
        return []
    sig = ("wobble", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    world.get("parent").memes["alarm"] += 1
    world.facts["wobbled"] = True
    return ["__wobble__"]


def _r_burn(world: World) -> list[str]:
    child = world.get("child")
    clue = world.get("clue")
    if clue.meters["heat_risk"] < THRESHOLD:
        return []
    sig = ("burn", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["ouch"] += 1
    child.memes["fear"] += 1
    world.get("parent").memes["alarm"] += 1
    world.facts["ouch"] = True
    return ["__ouch__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="burn", tag="physical", apply=_r_burn),
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
            if bit == "__wobble__":
                world.say("The stool gave a little wobble that made the child's heart jump.")
            elif bit == "__ouch__":
                world.say("The child snatched a hand back with a startled little 'ow.'")
    return produced


MYSTERIES = {
    "bowl": Mystery(
        id="bowl",
        clue="a floury bowl tucked near the lamp",
        source_phrase="a covered mixing bowl on the counter",
        sound="a soft thump of dough being turned",
        hidden_item="raviolo",
        hidden_phrase="one giant raviolo for tomorrow's supper",
        danger="high_counter",
        risk=1,
        heat=0,
        height=1,
        tags={"dough", "counter", "raviolo"},
    ),
    "pot": Mystery(
        id="pot",
        clue="a warm pot with a sleepy lid",
        source_phrase="a small pot on the stove with steam curling up",
        sound="a tiny lid clinking against the pot",
        hidden_item="sauce",
        hidden_phrase="tomato sauce waiting for a giant raviolo tomorrow",
        danger="hot_stove",
        risk=2,
        heat=1,
        height=1,
        tags={"stove", "steam", "raviolo"},
    ),
    "card": Mystery(
        id="card",
        clue="a recipe card with curly letters beside a bowl",
        source_phrase="a recipe card on the table beside a folded cloth",
        sound="paper whispering when the window moved the curtain",
        hidden_item="recipe",
        hidden_phrase='a recipe card with the funny scribble "make-gerund" in the corner',
        danger="none",
        risk=0,
        heat=0,
        height=0,
        tags={"recipe", "make-gerund", "raviolo"},
    ),
}

APPROACHES = {
    "ask": Approach(
        id="ask",
        sense=3,
        solo=False,
        steady=3,
        success_text="asked what the mystery was instead of reaching for it alone",
        oops_text="",
        adult_text="came close, smiled, and answered the question at once",
        resolution_text="Curiosity felt warm and safe when it was shared.",
        tags={"ask_for_help", "safe_choice"},
    ),
    "wait": Approach(
        id="wait",
        sense=2,
        solo=False,
        steady=3,
        success_text="waited under the doorway until the grown-up noticed the wondering eyes",
        oops_text="",
        adult_text="looked up, saw the child waiting, and invited a closer look",
        resolution_text="Waiting turned a lonely puzzle into a quiet lesson.",
        tags={"patience", "safe_choice"},
    ),
    "climb": Approach(
        id="climb",
        sense=2,
        solo=True,
        steady=1,
        success_text="dragged over a stool and climbed up for a peek",
        oops_text="The stool skidded on the floor with a small scrape.",
        adult_text="hurried over before anything worse happened",
        resolution_text="After that, curiosity still mattered, but safety had to come first.",
        tags={"climb", "oopsie"},
    ),
    "reach": Approach(
        id="reach",
        sense=1,
        solo=True,
        steady=2,
        success_text="stretched up on tiptoe and reached before asking",
        oops_text="A warm edge startled the child at once.",
        adult_text="came fast and gently moved the little hand away",
        resolution_text="The child learned that some mysteries should be touched only with help.",
        tags={"reach", "oopsie"},
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        phrase="a moon-soft blanket",
        bedtime_line="Soon the moon-soft blanket was tucked right up under the chin.",
        tags={"blanket"},
    ),
    "rabbit": Comfort(
        id="rabbit",
        phrase="a floppy rabbit toy",
        bedtime_line="Soon the floppy rabbit toy was safe under one small arm.",
        tags={"toy"},
    ),
    "pillow": Comfort(
        id="pillow",
        phrase="a cool, puffy pillow",
        bedtime_line="Soon the cool, puffy pillow held the sleepy head still.",
        tags={"pillow"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ivy", "Tessa", "Rosa"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Nico", "Evan", "Luca"]
TRAITS = ["curious", "gentle", "sleepy", "careful", "bright-eyed"]


def hazard_score(mystery: Mystery, approach: Approach) -> int:
    score = mystery.risk
    if mystery.height:
        score += max(0, 2 - approach.steady)
    if mystery.heat:
        score += 1 if approach.id in {"reach", "climb"} else 0
    return score


def valid_combo(mystery: Mystery, approach: Approach) -> bool:
    if approach.solo and mystery.id == "pot":
        return True
    if approach.solo and mystery.id == "bowl":
        return True
    if approach.solo and mystery.id == "card":
        return False
    if not approach.solo:
        return True
    return False


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for mid, mystery in MYSTERIES.items():
        for aid, approach in APPROACHES.items():
            if valid_combo(mystery, approach):
                out.append((mid, aid))
    return out


@dataclass
class StoryParams:
    mystery: str
    approach: str
    child_name: str
    child_gender: str
    parent: str
    comfort: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mystery="bowl",
        approach="ask",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        comfort="rabbit",
        trait="curious",
    ),
    StoryParams(
        mystery="card",
        approach="wait",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        comfort="blanket",
        trait="sleepy",
    ),
    StoryParams(
        mystery="bowl",
        approach="climb",
        child_name="Milo",
        child_gender="boy",
        parent="mother",
        comfort="pillow",
        trait="bright-eyed",
    ),
    StoryParams(
        mystery="pot",
        approach="reach",
        child_name="Nora",
        child_gender="girl",
        parent="father",
        comfort="blanket",
        trait="curious",
    ),
]


def predict(world: World, mystery: Mystery, approach: Approach) -> dict:
    sim = world.copy()
    child = sim.get("child")
    clue = sim.get("clue")
    if approach.id == "climb":
        child.meters["balance_risk"] += 1
        clue.meters["heat_risk"] += float(mystery.heat)
    elif approach.id == "reach":
        clue.meters["heat_risk"] += float(mystery.heat)
    propagate(sim, narrate=False)
    return {
        "wobble": bool(sim.facts.get("wobbled")),
        "ouch": bool(sim.facts.get("ouch")),
        "hazard": hazard_score(mystery, approach),
    }


def introduce(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    world.say(
        f"It was nearly bedtime when {child.id} padded down the hallway with {comfort.phrase} "
        f"and found a line of warm light under the kitchen door."
    )
    world.say(
        f"{child.id} should have been feeling sleepy, but curiosity was still awake and blinking."
    )
    world.say(
        f"In the kitchen, {child.pronoun('possessive')} {parent.label_word} was humming very softly."
    )


def notice(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"There was {mystery.clue}, and there was {mystery.sound}. "
        f"To {child.id}, it sounded like the room was hiding a secret."
    )


def wonder(world: World, child: Entity, mystery: Mystery) -> None:
    world.say(
        f'"What could it be?" {child.id} whispered. '
        f'The thought of a hidden {mystery.hidden_item} made {child.pronoun("possessive")} eyes grow round.'
    )


def choose(world: World, child: Entity, parent: Entity, mystery: Mystery, approach: Approach) -> None:
    pred = predict(world, mystery, approach)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_ouch"] = pred["ouch"]
    world.facts["predicted_hazard"] = pred["hazard"]
    if approach.id == "ask":
        world.say(
            f"So {child.id} walked to the doorway and {approach.success_text}. "
            f'"{parent.label_word.capitalize()}?" {child.pronoun()} said. "May I know?"'
        )
    elif approach.id == "wait":
        world.say(
            f"So {child.id} {approach.success_text}. "
            f'{child.pronoun().capitalize()} held still, even though the question inside felt bouncy.'
        )
    elif approach.id == "climb":
        child.meters["balance_risk"] += 1
        world.say(
            f"But the question felt too big to carry quietly, so {child.id} {approach.success_text}. "
            f"{approach.oops_text}"
        )
        propagate(world, narrate=True)
    elif approach.id == "reach":
        world.get("clue").meters["heat_risk"] += float(mystery.heat)
        world.say(
            f"But the wondering came out through {child.pronoun('possessive')} hands, and {child.id} "
            f"{approach.success_text}. {approach.oops_text}"
        )
        propagate(world, narrate=True)


def adult_response(world: World, child: Entity, parent: Entity, mystery: Mystery, approach: Approach) -> None:
    if world.facts.get("wobbled") or world.facts.get("ouch"):
        child.memes["relief"] += 1
        parent.memes["care"] += 1
        world.say(
            f"{parent.label_word.capitalize()} {approach.adult_text}. "
            f'"Easy there," {parent.pronoun()} said in a calm voice.'
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} {approach.adult_text}. "
            f'"I can see your wondering face," {parent.pronoun()} said.'
        )


def reveal(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then the secret turned out not to be frightening at all. It was {mystery.hidden_phrase}."
    )
    if mystery.id == "bowl":
        world.say(
            f'"I was folding the edges shut," {parent.label_word} explained. '
            f'"One big raviolo can hold a little pocket of supper inside."'
        )
    elif mystery.id == "pot":
        world.say(
            f'"The sauce only has to whisper tonight," {parent.label_word} explained. '
            f'"Tomorrow it will cuddle up next to the raviolo."'
        )
    else:
        world.say(
            f'"That funny word made you stare, didn\'t it?" {parent.label_word} said. '
            f'"I wrote "make-gerund" there so I would remember to fix the card later."'
        )


def repair(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    if world.facts.get("wobbled"):
        world.say(
            f"{parent.label_word.capitalize()} set the stool straight again and lifted {child.id} down "
            f"to the floor where small feet belonged."
        )
    if world.facts.get("ouch"):
        world.say(
            f"{parent.label_word.capitalize()} cooled the little fingers under gentle water and kissed them once."
        )
    if world.facts.get("wobbled") or world.facts.get("ouch"):
        world.say(
            f"{child.id} hugged {comfort.phrase} close and let the scary feeling grow smaller."
        )


def lesson(world: World, child: Entity, parent: Entity, approach: Approach) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'Then {parent.label_word} sat beside {child.id} and said, '
        f'"It is good to ask questions. Curiosity helps us learn."'
    )
    if approach.solo:
        world.say(
            f'"But when something is high, hot, or unknown, questions should walk to a grown-up first."'
        )
    else:
        world.say(
            f'"And when a mystery feels too big, waiting or asking keeps the wondering safe."'
        )
    world.say(approach.resolution_text)


def bedtime_end(world: World, child: Entity, parent: Entity, comfort: Comfort, mystery: Mystery) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"Soon they went back toward the dark, quiet bedroom together. {comfort.bedtime_line}"
    )
    if mystery.id == "card":
        last = 'The last thing {name} thought about was the funny word "make-gerund" drifting like a paper boat through sleep.'
    elif mystery.id == "pot":
        last = "The last thing {name} smelled was warm tomato and the promise of tomorrow's raviolo."
    else:
        last = "The last thing {name} imagined was a plump raviolo sleeping under its folded blanket of dough."
    world.say(last.format(name=child.id))
    world.say(
        f"And {child.id} fell asleep knowing that good questions shine brightest when they are carried safely."
    )


def tell(
    mystery: Mystery,
    approach: Approach,
    child_name: str = "Lila",
    child_gender: str = "girl",
    parent_type: str = "mother",
    comfort_cfg: Optional[Comfort] = None,
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        label=child_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="kitchen_clue",
        label=mystery.id,
        hot=bool(mystery.heat),
        high=bool(mystery.height),
    ))
    comfort = comfort_cfg or COMFORTS["blanket"]

    introduce(world, child, parent, comfort)
    notice(world, child, mystery)
    wonder(world, child, mystery)

    world.para()
    choose(world, child, parent, mystery, approach)
    adult_response(world, child, parent, mystery, approach)

    world.para()
    reveal(world, child, parent, mystery)
    repair(world, child, parent, comfort)
    lesson(world, child, parent, approach)

    world.para()
    bedtime_end(world, child, parent, comfort, mystery)

    outcome = "safe"
    if world.facts.get("ouch"):
        outcome = "ouch"
    elif world.facts.get("wobbled"):
        outcome = "wobble"

    world.facts.update(
        child=child,
        parent=parent,
        clue=clue,
        mystery=mystery,
        approach=approach,
        comfort=comfort,
        outcome=outcome,
        learned=True,
    )
    return world


KNOWLEDGE = {
    "raviolo": [
        (
            "What is a raviolo?",
            "A raviolo is one large stuffed piece of pasta. It is like one big pocket of dough with filling inside."
        )
    ],
    "ask_for_help": [
        (
            "Why is it smart to ask a grown-up before touching something hot or high?",
            "A grown-up can tell if something is safe and can help you reach it the right way. Asking first keeps curiosity from turning into an accident."
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means waiting calmly instead of grabbing right away. It gives you time to choose a safer and kinder action."
        )
    ],
    "stove": [
        (
            "Why can a stove be dangerous?",
            "A stove can be very hot, even when the flame looks small. Hot metal and steam can hurt skin quickly."
        )
    ],
    "steam": [
        (
            "What is steam?",
            "Steam is hot water floating in the air like a cloud. It can look soft, but it can still burn."
        )
    ],
    "recipe": [
        (
            "What is a recipe card?",
            "A recipe card is a note that tells how to make a food. It helps someone remember the ingredients and steps."
        )
    ],
    "counter": [
        (
            "Why should children be careful around high kitchen counters?",
            "High counters are hard for small children to reach safely. Climbing to see better can make them wobble or fall."
        )
    ],
    "make-gerund": [
        (
            'Why might a funny word like "make-gerund" be written on a note?',
            "Sometimes people scribble a silly reminder to fix later. A strange word on a note does not always mean something important or dangerous."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "raviolo",
    "ask_for_help",
    "patience",
    "stove",
    "steam",
    "recipe",
    "counter",
    "make-gerund",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    approach = f["approach"]
    outcome = f["outcome"]
    prompts = [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "raviolo" and "make-gerund".',
        f"Tell a gentle story about a {child.type} named {child.id} who notices {mystery.source_phrase} and feels very curious.",
    ]
    if approach.solo:
        prompts.append(
            "Write a moral story where curiosity leads to a brief oops moment, but a calm grown-up turns it into a safe lesson before bedtime."
        )
    elif outcome == "safe":
        prompts.append(
            "Write a warm bedtime story where asking or waiting helps a child learn a kitchen secret safely."
        )
    else:
        prompts.append(
            "Write a story about bedtime curiosity, a careful grown-up, and a gentle ending that proves what the child learned."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mystery = f["mystery"]
    approach = f["approach"]
    comfort = f["comfort"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child at bedtime, and {child.pronoun('possessive')} {parent.label_word} in the kitchen."
        ),
        (
            "What made the child curious?",
            f"{child.id} noticed {mystery.clue} and heard {mystery.sound}. Those little clues made the kitchen feel like it was hiding a secret."
        ),
        (
            f"How did {child.id} try to solve the mystery?",
            (
                f"{child.pronoun().capitalize()} {approach.success_text}. "
                f"That choice shaped whether the moment stayed calm or turned into a small scare."
            ),
        ),
    ]
    if outcome == "wobble":
        qa.append(
            (
                "What went wrong before the secret was explained?",
                f"The stool wobbled when {child.id} climbed up alone. That scared {child.pronoun('object')} and showed that being high off the floor was not safe."
            )
        )
    if outcome == "ouch":
        qa.append(
            (
                "What went wrong before the secret was explained?",
                f"{child.id} reached too soon and touched a warm edge. The little 'ow' showed that the kitchen mystery was not safe to touch without help."
            )
        )
    qa.append(
        (
            "What was the secret in the kitchen?",
            f"The secret was {mystery.hidden_phrase}. The mystery felt smaller once a grown-up explained what it really was."
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            (
                "The child learned that curiosity is good, but it should be carried safely. "
                "When something is high, hot, or confusing, asking or waiting for a grown-up is the wiser choice."
            ),
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended quietly in bed with {comfort.phrase} close by. The ending image shows that the child felt safe again and ready to sleep."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["approach"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("hot", e.hot), ("high", e.high), ("edible", e.edible), ("glowing", e.glowing)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} predicted_hazard={world.facts.get('predicted_hazard')}")
    return "\n".join(lines)


def explain_rejection(mystery: Mystery, approach: Approach) -> str:
    if mystery.id == "card" and approach.solo:
        return (
            "(No story: a paper recipe card is low-risk and too easy to inspect alone, "
            "so there is no real safety problem or moral turn. Pick a bowl or pot, or use a gentler approach.)"
        )
    if approach.sense < 1:
        return "(No story: that approach is not supported.)"
    return "(No story: this combination does not form a reasonable bedtime curiosity problem.)"


def outcome_of(params: StoryParams) -> str:
    mystery = MYSTERIES[params.mystery]
    approach = APPROACHES[params.approach]
    score = hazard_score(mystery, approach)
    if approach.id == "climb" and score >= 2:
        return "wobble"
    if approach.id == "reach" and mystery.heat:
        return "ouch"
    return "safe"


ASP_RULES = r"""
valid(M, A) :- mystery(M), approach(A), not forbidden_combo(M, A).

forbidden_combo(card, A) :- solo(A).

hazard(M, A, H) :- risk(M, R), height(M, HT), steady(A, S), H = R + (HT > 0 ? 2 - S : 0) + (heat(M, HE), solo(A), HE > 0 ? 1 : 0).

wobble :- chosen_mystery(M), chosen_approach(climb), risk(M, R), height(M, HT), steady(climb, S), H = R + (HT > 0 ? 2 - S : 0), H >= 2.
ouch :- chosen_mystery(M), chosen_approach(reach), heat(M, HE), HE > 0.

outcome(safe) :- not wobble, not ouch.
outcome(wobble) :- wobble.
outcome(ouch) :- ouch.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("risk", mid, mystery.risk))
        lines.append(asp.fact("heat", mid, mystery.heat))
        lines.append(asp.fact("height", mid, mystery.height))
    for aid, approach in APPROACHES.items():
        lines.append(asp.fact("approach", aid))
        lines.append(asp.fact("sense", aid, approach.sense))
        lines.append(asp.fact("steady", aid, approach.steady))
        if approach.solo:
            lines.append(asp.fact("solo", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_mystery", params.mystery),
        asp.fact("chosen_approach", params.approach),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: curiosity in the kitchen, a gentle mystery, and a safe lesson."
    )
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--approach", choices=sorted(APPROACHES))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (mystery, approach) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    picked_gender = gender or rng.choice(["girl", "boy"])
    if name:
        return name, picked_gender
    pool = GIRL_NAMES if picked_gender == "girl" else BOY_NAMES
    return rng.choice(pool), picked_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.approach:
        mystery = MYSTERIES[args.mystery]
        approach = APPROACHES[args.approach]
        if not valid_combo(mystery, approach):
            raise StoryError(explain_rejection(mystery, approach))

    combos = [
        pair for pair in valid_combos()
        if (args.mystery is None or pair[0] == args.mystery)
        and (args.approach is None or pair[1] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mystery_id, approach_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng, args.child_gender, args.child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        mystery=mystery_id,
        approach=approach_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        comfort=comfort,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery '{params.mystery}'.)")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach '{params.approach}'.)")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort '{params.comfort}'.)")
    mystery = MYSTERIES[params.mystery]
    approach = APPROACHES[params.approach]
    if not valid_combo(mystery, approach):
        raise StoryError(explain_rejection(mystery, approach))

    world = tell(
        mystery=mystery,
        approach=approach,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        comfort_cfg=COMFORTS[params.comfort],
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, approach) combos:\n")
        for mystery, approach in combos:
            print(f"  {mystery:8} {approach}")
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
            header = f"### {p.child_name}: {p.mystery} with {p.approach} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
