#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ergonomic_creamery_champion_suspense_problem_solving_superhero.py
==============================================================================================

A standalone storyworld about a child who feels like a superhero at a busy
creamery and solves a tense, practical problem with the right ergonomic tool.

The world models a small "save the day" domain:

- a child helper at a creamery wants to deliver something important before a bell
  rings for judging
- the job is risky in a specific, physical way
- a mentor spots the risk, the child imagines the danger, and then uses an
  ergonomic tool that truly fits the problem
- the ending proves the change: the delivery succeeds, the creamery cheers, and
  the child is called a champion

Run it
------
    python storyworlds/worlds/gpt-5.4/ergonomic_creamery_champion_suspense_problem_solving_superhero.py
    python storyworlds/worlds/gpt-5.4/ergonomic_creamery_champion_suspense_problem_solving_superhero.py --challenge giant_tub --gadget ergonomic_cart
    python storyworlds/worlds/gpt-5.4/ergonomic_creamery_champion_suspense_problem_solving_superhero.py --challenge wobble_cones --gadget ergonomic_cart
    python storyworlds/worlds/gpt-5.4/ergonomic_creamery_champion_suspense_problem_solving_superhero.py --all
    python storyworlds/worlds/gpt-5.4/ergonomic_creamery_champion_suspense_problem_solving_superhero.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ergonomic_creamery_champion_suspense_problem_solving_superhero.py --verify
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
        female = {"girl", "mother", "woman"}
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
class Challenge:
    id: str
    item_label: str
    item_phrase: str
    destination: str
    danger: str
    danger_line: str
    suspense_line: str
    solved_line: str
    risk_kind: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    ergonomic: bool
    supports: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    challenge: str
    gadget: str
    name: str
    gender: str
    mentor: str
    mentor_gender: str
    sidekick: str
    style: str
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


def _r_risk_to_suspense(world: World) -> list[str]:
    out: list[str] = []
    load = world.entities.get("load")
    hero = world.entities.get("hero")
    room = world.entities.get("room")
    if load is None or hero is None or room is None:
        return out
    if load.meters["risk"] < THRESHOLD:
        return out
    sig = ("risk_to_suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    room.memes["suspense"] += 1
    out.append("__suspense__")
    return out


def _r_supported_delivery(world: World) -> list[str]:
    out: list[str] = []
    load = world.entities.get("load")
    hero = world.entities.get("hero")
    gadget = world.entities.get("gadget")
    if load is None or hero is None or gadget is None:
        return out
    if load.meters["supported"] < THRESHOLD:
        return out
    sig = ("supported_delivery",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    load.meters["stable"] += 1
    load.meters["risk"] = 0.0
    hero.memes["confidence"] += 1
    out.append("__stable__")
    return out


CAUSAL_RULES = [
    Rule(name="risk_to_suspense", tag="emotional", apply=_r_risk_to_suspense),
    Rule(name="supported_delivery", tag="physical", apply=_r_supported_delivery),
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


CHALLENGES = {
    "giant_tub": Challenge(
        id="giant_tub",
        item_label="ice-cream tub",
        item_phrase="a silver tub of swirled blueberry ice cream",
        destination="the tasting counter",
        danger="it was heavy enough to yank one wrist sideways",
        danger_line="If it slipped, the cold blue swirl would splat across the creamery floor.",
        suspense_line="The tub tugged lower, lower, and for one breath it seemed the whole dessert might crash.",
        solved_line="The tub rolled level and proud, with not one scoop lost.",
        risk_kind="weight",
        need="balanced weight",
        tags={"ice_cream", "heavy", "creamery"},
    ),
    "wobble_cones": Challenge(
        id="wobble_cones",
        item_label="cone tower",
        item_phrase="a tower of six cherry cones stacked for the parade table",
        destination="the parade table",
        danger="the top cones liked to wobble when a hand bumped the tray",
        danger_line="If the tower tipped, pink scoops would tumble like tiny moons.",
        suspense_line="One cone leaned. Then another leaned with it. The tower looked ready to slide apart.",
        solved_line="The cones rode steady in a neat little ring, brave as a superhero team.",
        risk_kind="balance",
        need="steady balance",
        tags={"cones", "balance", "creamery"},
    ),
    "milk_can": Challenge(
        id="milk_can",
        item_label="milk can",
        item_phrase="a polished milk can of fresh cream for the ribbon judge",
        destination="the ribbon table",
        danger="the round handle pinched small fingers and swung the can side to side",
        danger_line="If the cream splashed out, the creamery would lose its finest topping for the final sundae.",
        suspense_line="The can swung toward the edge of the step, shining and dangerous.",
        solved_line="The cream stayed calm inside the can, all the way to the ribbon table.",
        risk_kind="grip",
        need="comfortable grip",
        tags={"milk", "grip", "creamery"},
    ),
}

GADGETS = {
    "ergonomic_cart": Gadget(
        id="ergonomic_cart",
        label="ergonomic cart",
        phrase="an ergonomic cart with soft handles and wide wheels",
        ergonomic=True,
        supports={"weight"},
        action_text="set the load on the ergonomic cart, kept both hands on the soft handle, and pushed in a straight brave line",
        qa_text="used an ergonomic cart with soft handles and wide wheels to move the heavy load safely",
        tags={"ergonomic", "cart", "problem_solving"},
    ),
    "ergonomic_tray": Gadget(
        id="ergonomic_tray",
        label="ergonomic tray",
        phrase="an ergonomic tray with a grippy rim and finger rests",
        ergonomic=True,
        supports={"balance"},
        action_text="slid the cones into the ergonomic tray and held the grippy rim with calm superhero hands",
        qa_text="used an ergonomic tray with a grippy rim to stop the cones from wobbling",
        tags={"ergonomic", "tray", "problem_solving"},
    ),
    "ergonomic_harness": Gadget(
        id="ergonomic_harness",
        label="ergonomic harness",
        phrase="an ergonomic harness with a padded shoulder strap and a hook ring",
        ergonomic=True,
        supports={"grip"},
        action_text="clipped the can to the ergonomic harness so the padded strap carried the swing instead of crushing small fingers",
        qa_text="used an ergonomic harness so the padded strap carried the milk can safely",
        tags={"ergonomic", "harness", "problem_solving"},
    ),
    "ladle": Gadget(
        id="ladle",
        label="ladle",
        phrase="a long ladle from the topping sink",
        ergonomic=False,
        supports=set(),
        action_text="",
        qa_text="",
        tags={"kitchen_tool"},
    ),
}

HERO_STYLES = {
    "comet": {
        "title": "Comet Cape",
        "entry": "felt as if a silver cape were flicking behind",
        "badge": "the Star Spoon badge",
    },
    "thunder": {
        "title": "Thunder Apron",
        "entry": "felt a brave rumble in the chest, as if an apron could be armor",
        "badge": "the Golden Scoop badge",
    },
    "glimmer": {
        "title": "Glimmer Glove",
        "entry": "felt bright as a superhero in a comic panel",
        "badge": "the Moonberry badge",
    },
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Zoe", "Ava", "Ruby", "Elsie", "June"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Theo", "Eli", "Noah"]
MENTOR_NAMES = {
    "mother": ["Mom", "Mama"],
    "father": ["Dad", "Papa"],
    "woman": ["Aunt May", "Chef Rosa", "Captain Bea"],
    "man": ["Uncle Ray", "Chef Tomas", "Captain Drew"],
}
SIDEKICKS = ["Sprinkles", "Cherry", "Pepper", "Waffle", "Button"]


def valid_combo(challenge_id: str, gadget_id: str) -> bool:
    if challenge_id not in CHALLENGES or gadget_id not in GADGETS:
        return False
    return CHALLENGES[challenge_id].risk_kind in GADGETS[gadget_id].supports


def valid_combos() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for challenge_id in CHALLENGES:
        for gadget_id in GADGETS:
            if valid_combo(challenge_id, gadget_id):
                pairs.append((challenge_id, gadget_id))
    return pairs


def explain_rejection(challenge: Challenge, gadget: Gadget) -> str:
    if not gadget.ergonomic:
        return (
            f"(No story: {gadget.label} is known in the creamery, but it is not an ergonomic tool. "
            f"This world only tells problem-solving superhero stories that use a fitting ergonomic fix.)"
        )
    return (
        f"(No story: {gadget.label} does not solve the problem in {challenge.id}. "
        f"That challenge needs {challenge.need}, not {gadget.label}.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    load = sim.get("load")
    load.meters["risk"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": load.meters["risk"],
        "worry": sim.get("hero").memes["worry"],
        "suspense": sim.get("room").memes["suspense"],
    }


def introduce(world: World, hero: Entity, mentor: Entity, style_id: str, challenge: Challenge) -> None:
    style = HERO_STYLES[style_id]
    world.say(
        f"After school, {hero.id} hurried into the bright creamery called Moonbucket Creamery. "
        f"{hero.pronoun().capitalize()} wore a paper apron and {style['entry']}."
    )
    world.say(
        f"Tonight was the Hall of Scoops parade, and {mentor.id} had promised that whoever helped best "
        f"would earn {style['badge']} and be called a champion."
    )
    world.say(
        f"Right then, the creamery needed help with {challenge.item_phrase}."
    )


def assign_mission(world: World, hero: Entity, mentor: Entity, challenge: Challenge, sidekick: str) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'"{hero.id}," said {mentor.id}, "{challenge.item_label.capitalize()} to {challenge.destination}, fast but careful."'
    )
    world.say(
        f"{sidekick}, the tiny creamery cat, twitched its tail beside the mint fridge as if it understood the mission."
    )


def warn(world: World, hero: Entity, mentor: Entity, challenge: Challenge) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_suspense"] = pred["suspense"]
    world.say(
        f"{hero.id} reached for it, but {mentor.id} lifted one finger. "
        f'"Wait. {challenge.danger.capitalize()}."'
    )
    world.say(challenge.danger_line)


def imagine_fall(world: World, hero: Entity, challenge: Challenge) -> None:
    load = world.get("load")
    load.meters["risk"] += 1
    propagate(world, narrate=False)
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} imagined the worst for one quick, shivery second. {challenge.suspense_line}"
    )


def choose_gadget(world: World, hero: Entity, mentor: Entity, gadget: Gadget) -> None:
    world.say(
        f"Then {hero.id}'s eyes found {gadget.phrase} hanging by the workbench."
    )
    world.say(
        f'"That is ergonomic," said {mentor.id}. "It helps your body work with the job instead of fighting it."'
    )
    world.say(
        f"{hero.id} nodded. This was not a guessing moment. It was a problem-solving moment."
    )


def solve(world: World, hero: Entity, gadget_cfg: Gadget, challenge: Challenge) -> None:
    load = world.get("load")
    gadget = world.get("gadget")
    gadget.meters["used"] += 1
    load.meters["supported"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} {gadget_cfg.action_text}."
    )
    world.say(
        challenge.solved_line
    )


def celebrate(world: World, hero: Entity, mentor: Entity, challenge: Challenge, style_id: str) -> None:
    style = HERO_STYLES[style_id]
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"The bell rang just as {hero.id} reached {challenge.destination}. The judges gasped, then smiled."
    )
    world.say(
        f'{mentor.id} laughed and clapped. "Moonbucket Creamery has its champion," {mentor.pronoun()} said. '
        f'"And a superhero knows that smart tools can be brave tools."'
    )
    world.say(
        f"{hero.id} grinned so wide that even the chrome scoops seemed to shine back. "
        f"{hero.pronoun().capitalize()} touched {style['badge']} and felt taller than the freezer doors."
    )


def tell(
    challenge: Challenge,
    gadget_cfg: Gadget,
    *,
    name: str,
    gender: str,
    mentor_name: str,
    mentor_gender: str,
    sidekick: str,
    style: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type=gender, role="hero", label=name))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor", label=mentor_name))
    world.add(Entity(id="room", type="room", label="creamery"))
    load = world.add(Entity(id="load", type="delivery", label=challenge.item_label, phrase=challenge.item_phrase))
    gadget = world.add(Entity(id="gadget", type="tool", label=gadget_cfg.label, phrase=gadget_cfg.phrase))
    world.facts["sidekick"] = sidekick

    introduce(world, hero, mentor, style, challenge)
    assign_mission(world, hero, mentor, challenge, sidekick)

    world.para()
    warn(world, hero, mentor, challenge)
    imagine_fall(world, hero, challenge)

    world.para()
    choose_gadget(world, hero, mentor, gadget_cfg)
    solve(world, hero, gadget_cfg, challenge)

    world.para()
    celebrate(world, hero, mentor, challenge, style)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        load=load,
        gadget=gadget,
        challenge=challenge,
        gadget_cfg=gadget_cfg,
        style=style,
        success=load.meters["stable"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ergonomic": [
        (
            "What does ergonomic mean?",
            "Ergonomic means something is shaped to fit the body well, so it feels safer and easier to use. "
            "A good ergonomic tool helps your hands, arms, or shoulders work in a comfortable way."
        )
    ],
    "creamery": [
        (
            "What is a creamery?",
            "A creamery is a place where milk and cream are used to make things like butter, ice cream, and other dairy foods. "
            "Some creameries are also shops where people serve those treats."
        )
    ],
    "champion": [
        (
            "What is a champion?",
            "A champion is someone who does a job especially well or wins a contest. "
            "In stories, a champion is often brave and also makes smart choices."
        )
    ],
    "balance": [
        (
            "Why do tall cones wobble?",
            "Tall stacks wobble because their weight is high up, so a small bump can make them tip. "
            "A tray with a good grip helps keep them steady."
        )
    ],
    "weight": [
        (
            "Why can a heavy tub be hard to carry?",
            "A heavy tub pulls down on your hands and wrists. "
            "Wheels or wide handles can spread the weight and make the job safer."
        )
    ],
    "grip": [
        (
            "Why can a round handle hurt small fingers?",
            "A thin round handle presses into a small area of your hand, so it can pinch and swing. "
            "A strap or padded support spreads the pull more comfortably."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong, thinking about what tool or plan fits best, and then trying that careful plan. "
            "It is not just rushing; it is thinking first."
        )
    ],
}

KNOWLEDGE_ORDER = ["ergonomic", "creamery", "champion", "weight", "balance", "grip", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    challenge = world.facts["challenge"]
    gadget = world.facts["gadget_cfg"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "ergonomic", "creamery", and "champion".',
        f"Tell a suspenseful story where a child helper at a creamery must move {challenge.item_phrase} and solves the problem with {gadget.phrase}.",
        f"Write a simple problem-solving story about {hero.id}, a brave child who saves the day with an ergonomic tool instead of rushing."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    challenge = world.facts["challenge"]
    gadget = world.facts["gadget_cfg"]
    sidekick = world.facts["sidekick"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child at Moonbucket Creamery who felt like a superhero. "
            f"{mentor.id} gave {hero.pronoun('object')} an important job, and {sidekick} the creamery cat watched the mission."
        ),
        (
            f"What problem did {hero.id} have to solve?",
            f"{hero.id} had to carry {challenge.item_phrase} to {challenge.destination}, but {challenge.danger}. "
            f"That made the moment tense because one mistake could have spoiled the creamery's big event."
        ),
        (
            f"Why did the moment feel suspenseful?",
            f"It felt suspenseful because {hero.id} imagined the load slipping before the bell rang. "
            f"The story shows that {challenge.danger_line[0].lower() + challenge.danger_line[1:]}"
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} {gadget.qa_text}. "
            f"The ergonomic tool matched the real problem, so the load became steady instead of risky."
        ),
        (
            "Why was the hero called a champion at the end?",
            f"{hero.id} was called a champion because {hero.pronoun()} saved the creamery's special delivery without spilling or dropping it. "
            f"The win came from careful problem solving, not from acting wild."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    challenge = world.facts["challenge"]
    gadget = world.facts["gadget_cfg"]
    tags = {"ergonomic", "creamery", "champion", "problem_solving"} | set(challenge.tags) | set(gadget.tags)
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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.phrase:
            bits.append(f"phrase={entity.phrase!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        challenge="giant_tub",
        gadget="ergonomic_cart",
        name="Lila",
        gender="girl",
        mentor="Chef Rosa",
        mentor_gender="woman",
        sidekick="Sprinkles",
        style="comet",
    ),
    StoryParams(
        challenge="wobble_cones",
        gadget="ergonomic_tray",
        name="Leo",
        gender="boy",
        mentor="Captain Bea",
        mentor_gender="woman",
        sidekick="Cherry",
        style="glimmer",
    ),
    StoryParams(
        challenge="milk_can",
        gadget="ergonomic_harness",
        name="Nora",
        gender="girl",
        mentor="Uncle Ray",
        mentor_gender="man",
        sidekick="Waffle",
        style="thunder",
    ),
]


ASP_RULES = r"""
valid(C, G) :- challenge(C), gadget(G), risk_kind(C, R), supports(G, R).
chosen_valid :- chosen_challenge(C), chosen_gadget(G), valid(C, G).
outcome(success) :- chosen_valid.
outcome(invalid) :- not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        lines.append(asp.fact("risk_kind", challenge_id, challenge.risk_kind))
    for gadget_id, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gadget_id))
        if gadget.ergonomic:
            lines.append(asp.fact("ergonomic", gadget_id))
        for support in sorted(gadget.supports):
            lines.append(asp.fact("supports", gadget_id, support))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_challenge", params.challenge),
            asp.fact("chosen_gadget", params.gadget),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    return "success" if valid_combo(params.challenge, params.gadget) else "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for challenge_id in CHALLENGES:
        for gadget_id in GADGETS:
            cases.append(
                StoryParams(
                    challenge=challenge_id,
                    gadget=gadget_id,
                    name="Lila",
                    gender="girl",
                    mentor="Chef Rosa",
                    mentor_gender="woman",
                    sidekick="Sprinkles",
                    style="comet",
                )
            )
    mismatches = [
        (p.challenge, p.gadget, asp_outcome(p), outcome_of(p))
        for p in cases
        if asp_outcome(p) != outcome_of(p)
    ]
    if not mismatches:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for item in mismatches[:10]:
            print(" ", item)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a superhero-style creamery rescue with ergonomic problem solving."
    )
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["mother", "father", "woman", "man"])
    ap.add_argument("--style", choices=sorted(HERO_STYLES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (challenge, gadget) pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.gadget:
        if not valid_combo(args.challenge, args.gadget):
            raise StoryError(explain_rejection(CHALLENGES[args.challenge], GADGETS[args.gadget]))
    if args.gadget and args.gadget in GADGETS and not GADGETS[args.gadget].ergonomic:
        challenge = CHALLENGES[args.challenge] if args.challenge else CHALLENGES["giant_tub"]
        raise StoryError(explain_rejection(challenge, GADGETS[args.gadget]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.challenge is None or combo[0] == args.challenge)
        and (args.gadget is None or combo[1] == args.gadget)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    challenge_id, gadget_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor_gender = args.mentor or rng.choice(["mother", "father", "woman", "man"])
    mentor = rng.choice(MENTOR_NAMES[mentor_gender])
    style = args.style or rng.choice(sorted(HERO_STYLES))
    sidekick = rng.choice(SIDEKICKS)

    return StoryParams(
        challenge=challenge_id,
        gadget=gadget_id,
        name=name,
        gender=gender,
        mentor=mentor,
        mentor_gender=mentor_gender,
        sidekick=sidekick,
        style=style,
    )


def generate(params: StoryParams) -> StorySample:
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Unknown challenge: {params.challenge})")
    if params.gadget not in GADGETS:
        raise StoryError(f"(Unknown gadget: {params.gadget})")
    if not valid_combo(params.challenge, params.gadget):
        raise StoryError(explain_rejection(CHALLENGES[params.challenge], GADGETS[params.gadget]))

    world = tell(
        CHALLENGES[params.challenge],
        GADGETS[params.gadget],
        name=params.name,
        gender=params.gender,
        mentor_name=params.mentor,
        mentor_gender=params.mentor_gender,
        sidekick=params.sidekick,
        style=params.style,
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
        print(f"{len(combos)} compatible (challenge, gadget) combos:\n")
        for challenge_id, gadget_id in combos:
            print(f"  {challenge_id:13} {gadget_id}")
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
            header = f"### {p.name}: {p.challenge} with {p.gadget}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
