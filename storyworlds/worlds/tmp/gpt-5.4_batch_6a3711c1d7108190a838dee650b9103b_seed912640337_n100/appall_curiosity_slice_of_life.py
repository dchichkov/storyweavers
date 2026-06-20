#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/appall_curiosity_slice_of_life.py
============================================================

A small standalone story world for a slice-of-life tale about curiosity,
impatience, and learning a gentler way to watch small changes.

Premise
-------
A child is caring for something that changes slowly: a bean in a cup, a bulb in a
pot, or bread dough in a bowl. The child is deeply curious and wants to know
what is happening *right now*. That curiosity can lead to a rough check:
digging up a seed, squeezing a bulb's shoot, or poking dough that should be left
to rise. A calm grown-up notices the risk and offers a safer way to observe:
a ruler, a notebook, or a kitchen timer.

Coverage discipline
-------------------
Not every observation tool fits every kind of slow change. A timer is useful for
dough, but not an honest fix for a bean sprout. A ruler helps with a growing
stem, but not with bread rising under a towel where the child mainly needs to
wait. The world model rejects such weak pairings. The stories prefer fewer,
plausible variants over shallow noun-swapping.

Run it
------
    python storyworlds/worlds/gpt-5.4/appall_curiosity_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/appall_curiosity_slice_of_life.py --subject bean --action dig
    python storyworlds/worlds/gpt-5.4/appall_curiosity_slice_of_life.py --subject dough --tool ruler
    python storyworlds/worlds/gpt-5.4/appall_curiosity_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/appall_curiosity_slice_of_life.py --qa --json
    python storyworlds/worlds/gpt-5.4/appall_curiosity_slice_of_life.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    delicate: bool = False
    alive: bool = False
    # physical + emotional dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type
        )


@dataclass
class Subject:
    id: str
    label: str
    phrase: str
    place: str
    hiding: str
    first_sign: str
    later_sign: str
    cover: str
    protect_word: str
    vulnerable_to: set[str]
    needs_wait: bool
    grows_up: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    body: str
    damage: str
    reassurance: str
    risk_to: set[str]
    impatience: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    lets_child_see: str
    works_for: set[str]
    image: str
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


def _r_stress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    subject = world.get("subject")
    if child.meters["handled_roughly"] < THRESHOLD:
        return out
    sig = ("stress", subject.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    subject.meters["disturbed"] += 1
    child.memes["worry"] += 1
    out.append("__disturbed__")
    return out


def _r_delay(world: World) -> list[str]:
    out: list[str] = []
    subject = world.get("subject")
    if subject.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("delay", subject.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    subject.meters["progress"] -= 1
    out.append("__slowed__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    subject = world.get("subject")
    if child.meters["using_safe_method"] < THRESHOLD:
        return out
    sig = ("repair", subject.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    subject.meters["settled"] += 1
    if subject.meters["progress"] < 1.0:
        subject.meters["progress"] = 1.0
    child.memes["calm"] += 1
    child.memes["wonder"] += 1
    out.append("__settled__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("stress", "physical", _r_stress),
    Rule("delay", "physical", _r_delay),
    Rule("repair", "physical", _r_repair),
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


def action_risks_subject(subject: Subject, action: Action) -> bool:
    return action.id in subject.vulnerable_to and subject.id in action.risk_to


def tool_fits_subject(subject: Subject, tool: Tool) -> bool:
    return subject.id in tool.works_for


def valid_choice(subject: Subject, action: Action, tool: Tool) -> bool:
    return action_risks_subject(subject, action) and tool_fits_subject(subject, tool)


def predict_damage(world: World, action: Action) -> dict:
    sim = world.copy()
    child = sim.get("child")
    _do_action(sim, child, action, narrate=False)
    subject = sim.get("subject")
    return {
        "disturbed": subject.meters["disturbed"] >= THRESHOLD,
        "progress": subject.meters["progress"],
        "worry": child.memes["worry"],
    }


def _do_action(world: World, child: Entity, action: Action, narrate: bool = True) -> None:
    child.memes["curiosity"] += 1
    child.memes["impatience"] += float(action.impatience)
    child.meters["handled_roughly"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, subject: Subject) -> None:
    world.say(
        f"{child.id} had been watching {subject.phrase} {subject.place} every day. "
        f"{child.pronoun().capitalize()} liked small changes and never wanted to miss one."
    )
    world.say(
        f"That morning, {child.pronoun()} noticed {subject.first_sign}, and {child.pronoun('possessive')} "
        f"curiosity began to buzz."
    )


def make_wait_feel_long(world: World, child: Entity, subject: Subject) -> None:
    world.say(
        f"But {subject.hiding} made the change feel slow. "
        f"{child.id} wanted to know what was happening right then, not later."
    )


def tempt(world: World, child: Entity, action: Action) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.pronoun().capitalize()} edged closer and thought about {action.verb}. "
        f"For one small moment, it seemed like the quickest way to learn a secret."
    )


def warn(world: World, adult: Entity, child: Entity, subject: Subject, action: Action) -> None:
    pred = predict_damage(world, action)
    world.facts["predicted_progress"] = pred["progress"]
    child.memes["caution_heard"] += 1
    world.say(
        f'{adult.label_word.capitalize()} saw {child.pronoun("object")} reaching and said, '
        f'"Easy now. If you {action.body}, {action.damage}."'
    )
    if pred["disturbed"]:
        world.say(
            f'"Some things grow best when we watch gently," {adult.pronoun()} added. '
            f'"They do not need bigger hands. They need calmer ones."'
        )


def defy(world: World, child: Entity, action: Action) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'Curiosity tugged harder than patience. "{action.reassurance}" {child.id} said, '
        f"and {child.pronoun()} went ahead."
    )


def regret(world: World, child: Entity, subject: Subject, action: Action) -> None:
    world.say(
        f"As soon as {child.pronoun()} {action.body}, {child.pronoun('possessive')} face changed. "
        f"{subject.later_sign} did not come faster. Instead, everything looked a little troubled."
    )


def comfort_and_redirect(world: World, adult: Entity, child: Entity, subject: Subject, tool: Tool) -> None:
    child.memes["comfort"] += 1
    world.say(
        f"The sight might have appalled someone in a hurry, but it did not appall "
        f"{adult.label_word}. {adult.pronoun().capitalize()} knelt beside {child.id} and kept "
        f"{adult.pronoun('possessive')} voice soft."
    )
    world.say(
        f'"You were curious," {adult.pronoun()} said. "That is not bad. We just need a gentler way to look."'
    )
    world.say(
        f"{adult.label_word.capitalize()} brought {tool.phrase} and showed {child.pronoun('object')} how to "
        f"{tool.method}. That way, {child.id} could {tool.lets_child_see} without bothering {subject.protect_word}."
    )


def settle(world: World, child: Entity, subject: Subject, tool: Tool) -> None:
    child.meters["using_safe_method"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon the room felt quiet again. {child.id} stayed close, used the {tool.label}, and waited."
    )
    world.say(
        f"After a while, {subject.later_sign}. {tool.image}"
    )


def ending(world: World, adult: Entity, child: Entity, tool: Tool) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'{child.id} smiled and leaned against {adult.pronoun("object")}. '
        f'"I can still be curious," {child.pronoun()} said, "just gentle."'
    )
    world.say(
        f"{adult.label_word.capitalize()} nodded. On the windowsill, the small project kept changing at its own pace, "
        f"and this time {child.id} was ready to notice it kindly."
    )


def tell(
    subject: Subject,
    action: Action,
    tool: Tool,
    child_name: str = "Nora",
    child_type: str = "girl",
    adult_type: str = "mother",
    adult_name: str = "Parent",
    child_trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(id=child_name, kind="character", type=child_type, role="child", traits=[child_trait, "eager"])
    )
    adult = world.add(
        Entity(id=adult_name, kind="character", type=adult_type, role="adult", label="the grown-up")
    )
    subject_ent = world.add(
        Entity(id="subject", type="project", label=subject.label, delicate=True, alive=subject.id != "dough")
    )

    subject_ent.meters["progress"] = 2.0
    child.memes["curiosity"] = 3.0
    child.memes["patience"] = 1.0

    introduce(world, child, subject)
    make_wait_feel_long(world, child, subject)

    world.para()
    tempt(world, child, action)
    warn(world, adult, child, subject, action)
    defy(world, child, action)

    world.para()
    _do_action(world, child, action, narrate=False)
    regret(world, child, subject, action)

    world.para()
    comfort_and_redirect(world, adult, child, subject, tool)
    settle(world, child, subject, tool)

    world.para()
    ending(world, adult, child, tool)

    world.facts.update(
        child=child,
        adult=adult,
        subject_cfg=subject,
        action=action,
        tool=tool,
        subject=subject_ent,
        disturbed=subject_ent.meters["disturbed"] >= THRESHOLD,
        recovered=child.meters["using_safe_method"] >= THRESHOLD,
        progress=subject_ent.meters["progress"],
    )
    return world


SUBJECTS = {
    "bean": Subject(
        "bean",
        "bean",
        "a bean seed tucked in a clear cup",
        "on the sunny windowsill",
        "a pale root curling against the side",
        "a green hook of stem peeped up through the soil",
        "the seed and its new root",
        "the tiny bean",
        {"dig"},
        needs_wait=True,
        grows_up=True,
        tags={"bean", "plant", "wait"},
    ),
    "bulb": Subject(
        "bulb",
        "bulb",
        "a flower bulb in a small clay pot",
        "beside the kitchen window",
        "a tight green tip pushing from the dirt",
        "the green tip stood taller and unfolded at the top",
        "the little shoot",
        "the little bulb and shoot",
        {"squeeze"},
        needs_wait=True,
        grows_up=True,
        tags={"bulb", "plant", "wait"},
    ),
    "dough": Subject(
        "dough",
        "dough",
        "bread dough resting in a warm bowl",
        "under a clean towel on the counter",
        "the towel lifting just a little in the middle",
        "the dough had risen high and round",
        "the warm dough",
        "the dough",
        {"poke"},
        needs_wait=True,
        grows_up=False,
        tags={"dough", "kitchen", "wait"},
    ),
}

ACTIONS = {
    "dig": Action(
        "dig",
        "digging the bean up to check it",
        "dug around the cup with one finger",
        "you can break the new root and make it start over",
        "I'll only look for one second.",
        {"bean"},
        impatience=2,
        tags={"dig", "root", "careful"},
    ),
    "squeeze": Action(
        "squeeze",
        "squeezing the new shoot to feel it",
        "gave the green tip a little squeeze",
        "the new shoot can bruise before it has a chance to open",
        "I'm just seeing if it's strong.",
        {"bulb"},
        impatience=2,
        tags={"squeeze", "shoot", "careful"},
    ),
    "poke": Action(
        "poke",
        "poking under the towel again and again",
        "lifted the towel and poked the dough",
        "the warm dough can sink when it keeps getting bothered",
        "I only want to see if it is bigger yet.",
        {"dough"},
        impatience=2,
        tags={"poke", "dough", "careful"},
    ),
}

TOOLS = {
    "ruler": Tool(
        "ruler",
        "a little ruler",
        "a little ruler",
        "measure the height each afternoon and make a pencil mark on the cup",
        "see the change from line to line",
        {"bean", "bulb"},
        "By supper there was a new mark to make, and the ruler showed the change clearly.",
        tags={"ruler", "measure", "wait"},
    ),
    "notebook": Tool(
        "notebook",
        "notebook",
        "a small notebook",
        "draw what was there today and compare it with tomorrow's picture",
        "watch change with pictures instead of fingers",
        {"bean", "bulb", "dough"},
        "Soon one picture did not match the next, and that difference felt like a secret opening slowly.",
        tags={"notebook", "draw", "wait"},
    ),
    "timer": Tool(
        "timer",
        "timer",
        "a round kitchen timer",
        "set the timer and leave the towel alone until the bell rang",
        "know exactly when it was time to check again",
        {"dough"},
        image="When the bell finally rang, waiting had turned into a game instead of a worry.",
        tags={"timer", "kitchen", "wait"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Ava", "Ruby", "Ella", "June", "Sophie"]
BOY_NAMES = ["Owen", "Max", "Leo", "Ben", "Sam", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "eager", "thoughtful", "bright-eyed", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, subject in SUBJECTS.items():
        for aid, action in ACTIONS.items():
            for tid, tool in TOOLS.items():
                if valid_choice(subject, action, tool):
                    combos.append((sid, aid, tid))
    return combos


@dataclass
class StoryParams:
    subject: str
    action: str
    tool: str
    child: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bean": [
        (
            "How does a bean seed start to grow?",
            "A bean seed begins by sending out a tiny root and then a stem. It needs water, warmth, and time more than touching."
        )
    ],
    "bulb": [
        (
            "What is a flower bulb?",
            "A flower bulb is a plant sleeping underground with food tucked inside. When it gets the right care, it sends up a shoot and grows."
        )
    ],
    "dough": [
        (
            "Why does bread dough rise?",
            "Bread dough rises because yeast makes tiny bubbles of gas inside it. Warmth and waiting help the dough puff up."
        )
    ],
    "ruler": [
        (
            "Why use a ruler for a growing plant?",
            "A ruler lets you see how tall a plant is without pulling or squeezing it. That makes it easier to notice change gently."
        )
    ],
    "notebook": [
        (
            "Why is drawing in a notebook a gentle way to observe?",
            "Drawing helps you pay attention with your eyes. You can compare one day to the next without disturbing the thing you are watching."
        )
    ],
    "timer": [
        (
            "What does a timer help with?",
            "A timer helps you wait until a better moment to check something. It turns waiting into a clear job instead of a restless guess."
        )
    ],
    "wait": [
        (
            "Why do some small changes need waiting?",
            "Growing and rising happen little by little. If you keep bothering the process, you can slow it down instead of seeing it sooner."
        )
    ],
    "careful": [
        (
            "Can curiosity be a good thing?",
            "Yes. Curiosity helps you learn, but gentle hands and patient eyes help you learn without causing harm."
        )
    ],
}
KNOWLEDGE_ORDER = ["bean", "bulb", "dough", "ruler", "notebook", "timer", "wait", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, subject, action, tool = f["child"], f["subject_cfg"], f["action"], f["tool"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "appall" and shows a child learning a gentler way to be curious.',
        f"Tell a quiet home story where {child.id} is curious about {subject.phrase} and tries {action.verb}, but a calm grown-up shows {child.pronoun('object')} how to use {tool.phrase} instead.",
        f"Write a simple story about curiosity, patience, and noticing change slowly, ending with {subject.later_sign}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    subject = f["subject_cfg"]
    action = f["action"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a very curious child, and {child.pronoun('possessive')} {adult.label_word}, who helps {child.pronoun('object')} slow down. The story stays in an ordinary home moment and shows how curiosity can be guided kindly."
        ),
        (
            f"What was {child.id} watching?",
            f"{child.pronoun().capitalize()} was watching {subject.phrase} {subject.place}. {child.pronoun('possessive').capitalize()} curiosity grew because a small sign of change had just appeared."
        ),
        (
            f"Why did {child.id} do {action.verb}?",
            f"{child.id} wanted to know what was happening right away. Waiting felt hard, so {child.pronoun()} reached for a quick answer with {action.verb}."
        ),
        (
            f"Why did {adult.label_word} tell {child.id} to be gentle?",
            f"{adult.label_word.capitalize()} knew that if {child.id} {action.body}, {action.damage}. The warning came from the real needs of {subject.protect_word}, not from a wish to spoil the fun."
        ),
    ]
    if f["disturbed"]:
        qa.append(
            (
                f"What happened after {child.id} touched it the rough way?",
                f"{subject.later_sign.capitalize()} did not come faster. Instead, the little project looked disturbed, and {child.id} felt worried because curiosity had turned into fussing."
            )
        )
    qa.append(
        (
            f"How did {adult.label_word} help solve the problem?",
            f"{adult.label_word.capitalize()} did not scold harshly. {adult.pronoun().capitalize()} brought {tool.phrase} and showed {child.id} how to {tool.method}, so curiosity could keep going in a gentler way."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with patience proving useful: {subject.later_sign}, and {child.id} learned that being curious and being gentle can belong together. The ending image shows real change arriving after calm waiting."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["subject_cfg"].tags) | set(f["action"].tags) | set(f["tool"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        flags = [n for n, on in (("delicate", e.delicate), ("alive", e.alive)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bean", "dig", "ruler", "Nora", "girl", "mother", "curious"),
    StoryParams("bulb", "squeeze", "notebook", "Max", "boy", "father", "eager"),
    StoryParams("dough", "poke", "timer", "Lila", "girl", "grandmother", "bright-eyed"),
    StoryParams("bean", "dig", "notebook", "Owen", "boy", "mother", "thoughtful"),
]


def explain_rejection(subject: Subject, action: Action, tool: Tool) -> str:
    if not action_risks_subject(subject, action):
        return (
            f"(No story: {action.verb} does not honestly threaten {subject.label} in this world. "
            f"Pick the action that really risks that subject.)"
        )
    if not tool_fits_subject(subject, tool):
        return (
            f"(No story: {tool.label} is not a good observation fix for {subject.label}. "
            f"The replacement method should suit what the child is trying to notice.)"
        )
    return "(No story: this combination is not supported.)"


ASP_RULES = r"""
% Reasonableness gate: the action must truly risk the subject, and the tool
% must truly fit the kind of slow change the subject has.
valid(S, A, T) :- subject(S), action(A), tool(T), vulnerable(S, A), fits(T, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, subject in SUBJECTS.items():
        lines.append(asp.fact("subject", sid))
        if subject.needs_wait:
            lines.append(asp.fact("needs_wait", sid))
        if subject.grows_up:
            lines.append(asp.fact("grows_up", sid))
        for aid in sorted(subject.vulnerable_to):
            lines.append(asp.fact("vulnerable", sid, aid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for sid in sorted(action.risk_to):
            lines.append(asp.fact("risks", aid, sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for sid in sorted(tool.works_for):
            lines.append(asp.fact("fits", tid, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: curiosity, a too-rough check, and a gentler way to notice change."
    )
    ap.add_argument("--subject", choices=SUBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.subject and args.action and args.tool:
        if not valid_choice(SUBJECTS[args.subject], ACTIONS[args.action], TOOLS[args.tool]):
            raise StoryError(explain_rejection(SUBJECTS[args.subject], ACTIONS[args.action], TOOLS[args.tool]))

    combos = [
        c
        for c in valid_combos()
        if (args.subject is None or c[0] == args.subject)
        and (args.action is None or c[1] == args.action)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    subject, action, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father", "grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(subject, action, tool, name, gender, adult, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SUBJECTS[params.subject],
        ACTIONS[params.action],
        TOOLS[params.tool],
        child_name=params.child,
        child_type=params.gender,
        adult_type=params.adult,
        child_trait=params.trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (subject, action, tool) combos:\n")
        for subject, action, tool in combos:
            print(f"  {subject:7} {action:8} {tool}")
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
            header = f"### {p.child}: {p.subject} / {p.action} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
