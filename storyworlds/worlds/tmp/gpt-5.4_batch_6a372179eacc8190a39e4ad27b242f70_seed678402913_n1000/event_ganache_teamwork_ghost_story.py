#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/event_ganache_teamwork_ghost_story.py
================================================================

A standalone storyworld for a gentle ghost-story-shaped tale about teamwork at a
night event. Two children help prepare a community event with chocolate ganache
in an old hall. Strange signs make them think a ghost is interfering, but a
careful investigation plus teamwork reveals a real cause, and the event is saved.

The world model tracks:
- physical meters: darkness, wobble, spill, missing, draft, found
- emotional memes: worry, courage, trust, relief, joy

The central tension is always practical and child-facing:
a spooky old place + an important dessert for an event + a mysterious problem.
The fix must be a sensible team method, and the inline ASP twin matches the
Python reasonableness gate and ending model.

Run it
------
    python storyworlds/worlds/gpt-5.4/event_ganache_teamwork_ghost_story.py
    python storyworlds/worlds/gpt-5.4/event_ganache_teamwork_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/event_ganache_teamwork_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/event_ganache_teamwork_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/event_ganache_teamwork_ghost_story.py --verify
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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
class Setting:
    id: str
    place: str
    spooky_detail: str
    event_name: str
    hiding_spot: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    ganache_phrase: str
    tray_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    hint: str
    sound: str
    sign: str
    cause: str
    clue: str
    risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    sense: int
    power: int
    team_text: str
    discover_text: str
    qa_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.characters() if e.role in {"leader", "helper"}]

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


def _r_dark_fear(world: World) -> list[str]:
    out: list[str] = []
    hall = world.entities.get("hall")
    if hall is None or hall.meters["darkness"] < THRESHOLD:
        return out
    sig = ("dark_fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_missing_stress(world: World) -> list[str]:
    out: list[str] = []
    tray = world.entities.get("tray")
    if tray is None or tray.meters["missing"] < THRESHOLD:
        return out
    sig = ("missing_stress",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    hall = world.entities.get("hall")
    if hall is not None:
        hall.meters["trouble"] += 1
    out.append("__missing__")
    return out


CAUSAL_RULES = [
    Rule(name="dark_fear", tag="emotional", apply=_r_dark_fear),
    Rule(name="missing_stress", tag="physical", apply=_r_missing_stress),
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


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def best_method() -> Method:
    return max(METHODS.values(), key=lambda m: (m.sense, m.power))


def valid_combo(setting: Setting, mystery: Mystery, method: Method) -> bool:
    return method.sense >= SENSE_MIN and method.power >= mystery.risk


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for meth_id, method in METHODS.items():
                if valid_combo(setting, mystery, method):
                    combos.append((sid, mid, meth_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    mystery = MYSTERIES[params.mystery]
    if params.courage_level + params.trust_level < 6:
        return "flee"
    return "solved" if method.power >= mystery.risk else "spoiled"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A teamwork story should use a calm, "
        f"practical way to investigate. Try: {better}.)"
    )


def explain_combo(mystery: Mystery, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return explain_method(method.id)
    if method.power < mystery.risk:
        return (
            f"(No story: {method.id} is too weak for the {mystery.id} mystery. "
            f"The team needs a method strong enough to handle the problem and save the event.)"
        )
    return "(No valid combination matches the given options.)"


def predict_spook(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    tray = sim.get("tray")
    hall = sim.get("hall")
    tray.meters["missing"] += 1
    hall.meters["darkness"] += 1
    propagate(sim, narrate=False)
    return {
        "missing": tray.meters["missing"] >= THRESHOLD,
        "worry": sum(kid.memes["worry"] for kid in sim.kids()),
        "trouble": hall.meters["trouble"],
    }


def introduce(world: World, a: Entity, b: Entity, parent: Entity,
              setting: Setting, treat: Treat) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On the evening of the {setting.event_name}, {a.id} and {b.id} stayed late with "
        f"{a.id}'s {parent.label_word} in {setting.place}. {setting.spooky_detail}"
    )
    world.say(
        f"They were helping set out {treat.phrase}, and the shiniest tray held "
        f"{treat.ganache_phrase}."
    )


def promise_of_event(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f'"If we finish together," {b.id} whispered, "everyone at the event will see the table glow."'
    )
    world.say(
        f"{a.id} nodded, though {setting.echo} made the old room sound bigger than it was."
    )


def first_sign(world: World, mystery: Mystery, hall: Entity) -> None:
    hall.meters["darkness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {mystery.sound}, and {mystery.sign}. For one shivery moment, the hall felt like a ghost story."
    )


def tray_goes_missing(world: World, treat: Treat, mystery: Mystery) -> None:
    tray = world.get("tray")
    tray.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the children turned back, the tray of {treat.ganache_phrase} was gone from the long table."
    )
    world.say(
        f'"A ghost took it," {a_or_b(world)[0].id} breathed, because {mystery.hint}.'
    )


def a_or_b(world: World) -> tuple[Entity, Entity]:
    kids = world.kids()
    return kids[0], kids[1]


def warning_and_choice(world: World, a: Entity, b: Entity, parent: Entity,
                       mystery: Mystery, setting: Setting) -> None:
    pred = predict_spook(world, mystery)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'{parent.label_word.capitalize()} looked at the dark corners and said, '
        f'"Maybe it feels spooky, but spooky feelings are not the same as proof."'
    )
    world.say(
        f"{b.id} squeezed {a.id}'s hand. They could run from the room, or they could work together and look carefully."
    )


def flee_ending(world: World, a: Entity, b: Entity, parent: Entity,
                setting: Setting, treat: Treat) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
    world.say(
        f"They hurried out into the bright kitchen and stayed there until other grown-ups arrived."
    )
    world.say(
        f"Later, the tray of {treat.ganache_phrase} was found safe enough in another room, so the event still happened."
    )
    world.say(
        f"But {a.id} and {b.id} wished they had been braver together, because the mystery had stayed bigger in their minds than it really was."
    )


def teamwork_search(world: World, a: Entity, b: Entity, method: Method) -> None:
    for kid in (a, b):
        kid.memes["courage"] += 1
        kid.memes["trust"] += 1
    world.say(method.team_text.replace("{A}", a.id).replace("{B}", b.id))


def solve_mystery(world: World, a: Entity, b: Entity, parent: Entity,
                  setting: Setting, treat: Treat, mystery: Mystery, method: Method) -> None:
    hall = world.get("hall")
    tray = world.get("tray")
    hall.meters["darkness"] = 0.0
    tray.meters["missing"] = 0.0
    hall.meters["found"] += 1
    for kid in (a, b):
        kid.memes["worry"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    world.say(method.discover_text
              .replace("{cause}", mystery.cause)
              .replace("{clue}", mystery.clue)
              .replace("{spot}", setting.hiding_spot))
    world.say(
        f'There was no ghost at all. The trouble had come from {mystery.cause}, and the clue was {mystery.clue}.'
    )
    world.say(
        f'Together they carried the tray back, straightened the crooked cloth, and {parent.label_word} smiled. "That is what good helpers do," {parent.pronoun()} said.'
    )
    world.say(
        f"Soon the event began, and the glossy ganache caught the warm light instead of the shadows."
    )


def spoiled_ending(world: World, a: Entity, b: Entity, parent: Entity,
                   treat: Treat, mystery: Mystery, method: Method) -> None:
    tray = world.get("tray")
    tray.meters["spill"] += 1
    for kid in (a, b):
        kid.memes["worry"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"They tried to help, but their plan was too fussy and too slow. While they were busy, {mystery.cause} spoiled the tray."
    )
    world.say(
        f"The {treat.ganache_phrase} could not be served at the event after all."
    )
    world.say(
        f"{parent.label_word.capitalize()} hugged them and said they had meant well, but next time they would need a simpler teamwork plan."
    )


def tell(setting: Setting, treat: Treat, mystery: Mystery, method: Method,
         leader_name: str, leader_gender: str, helper_name: str, helper_gender: str,
         parent_type: str, courage_level: int, trust_level: int, lantern: str) -> World:
    world = World()
    a = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=["eager"],
        attrs={"lantern": lantern},
    ))
    b = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["steady"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    hall = world.add(Entity(
        id="hall",
        type="hall",
        label=setting.place,
        tags=set(setting.tags),
    ))
    tray = world.add(Entity(
        id="tray",
        type="tray",
        label=treat.label,
        phrase=treat.tray_phrase,
        tags=set(treat.tags),
    ))
    a.memes["courage"] = float(courage_level)
    b.memes["trust"] = float(trust_level)

    introduce(world, a, b, parent, setting, treat)
    promise_of_event(world, a, b, setting)

    world.para()
    first_sign(world, mystery, hall)
    tray_goes_missing(world, treat, mystery)
    warning_and_choice(world, a, b, parent, mystery, setting)

    outcome = outcome_of(StoryParams(
        setting=setting.id,
        treat=treat.id,
        mystery=mystery.id,
        method=method.id,
        leader=leader_name,
        leader_gender=leader_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=parent_type,
        courage_level=courage_level,
        trust_level=trust_level,
        lantern=lantern,
        seed=None,
    ))

    world.para()
    if outcome == "flee":
        flee_ending(world, a, b, parent, setting, treat)
    elif outcome == "solved":
        teamwork_search(world, a, b, method)
        solve_mystery(world, a, b, parent, setting, treat, mystery, method)
    else:
        teamwork_search(world, a, b, method)
        spoiled_ending(world, a, b, parent, treat, mystery, method)

    world.facts.update(
        leader=a,
        helper=b,
        parent=parent,
        hall=hall,
        tray=tray,
        setting=setting,
        treat=treat,
        mystery=mystery,
        method=method,
        outcome=outcome,
        courage_total=courage_level + trust_level,
        lantern=lantern,
    )
    return world


SETTINGS = {
    "hall": Setting(
        id="hall",
        place="the old town hall",
        spooky_detail="Dusty picture frames watched from the walls, and the high windows showed a strip of moon",
        event_name="Harvest Night event",
        hiding_spot="behind the velvet curtain by the little stage",
        echo="every whisper bounced back from the rafters",
        tags={"hall", "event"},
    ),
    "manor": Setting(
        id="manor",
        place="the drafty manor foyer",
        spooky_detail="A long staircase curved above them, and candle-shaped lamps made soft puddles of gold",
        event_name="Charity Lantern event",
        hiding_spot="under the side table near the coat stand",
        echo="the floorboards answered with tiny creaks",
        tags={"manor", "event"},
    ),
    "museum": Setting(
        id="museum",
        place="the old village museum",
        spooky_detail="Glass cases gleamed in the dim room, and the giant clock ticked like slow footsteps",
        event_name="Moonlight Stories event",
        hiding_spot="beside the folded display screen",
        echo="the clock made the quiet seem deeper",
        tags={"museum", "event"},
    ),
}

TREATS = {
    "cake": Treat(
        id="cake",
        label="cake tray",
        phrase="small chocolate cakes",
        ganache_phrase="cakes glazed with dark ganache",
        tray_phrase="the tray of ganache cakes",
        tags={"cake", "ganache"},
    ),
    "eclairs": Treat(
        id="eclairs",
        label="éclair tray",
        phrase="little éclairs",
        ganache_phrase="éclairs striped with glossy ganache",
        tray_phrase="the tray of ganache éclairs",
        tags={"eclair", "ganache"},
    ),
    "cookies": Treat(
        id="cookies",
        label="cookie plate",
        phrase="round cookies",
        ganache_phrase="cookies drizzled with ganache",
        tray_phrase="the plate of ganache cookies",
        tags={"cookie", "ganache"},
    ),
}

MYSTERIES = {
    "draft": Mystery(
        id="draft",
        hint="the curtain lifted by itself",
        sound="a cold breath slipped through the room",
        sign="one candle-shaped lamp flickered and the curtain gave a slow wave",
        cause="a hidden draft from a loose side door",
        clue="the cold ribbon of air on their hands",
        risk=2,
        tags={"draft", "ghost"},
    ),
    "cat": Mystery(
        id="cat",
        hint="something brushed past their ankles in the dark",
        sound="a soft thump came from under the table",
        sign="two bright eyes blinked near the floor",
        cause="the caretaker's cat nosing after the smell of chocolate",
        clue="tiny paw prints in the dust",
        risk=2,
        tags={"cat", "ghost"},
    ),
    "cart": Mystery(
        id="cart",
        hint="wheels squeaked somewhere no one could be seen",
        sound="a squeaky roll came from the far end of the room",
        sign="the tablecloth twitched and one tray slowly slid",
        cause="a slanted serving cart bumping the table leg",
        clue="the wobbling wheel that would not stand straight",
        risk=3,
        tags={"cart", "ghost"},
    ),
}

METHODS = {
    "lantern_search": Method(
        id="lantern_search",
        sense=3,
        power=3,
        team_text="{A} held the lantern low while {B} checked under tables and along the wall. Step by step, they named what they saw instead of what they feared.",
        discover_text="At last they reached {spot}, where they found the tray and the true cause: {cause}. The children noticed {clue} first.",
        qa_text="They used a lantern and searched together carefully",
        tags={"lantern", "teamwork"},
    ),
    "follow_clues": Method(
        id="follow_clues",
        sense=3,
        power=2,
        team_text="{A} watched the floor while {B} listened for the sound again. Working as a team, they followed one small clue after another.",
        discover_text="The clues led them to {spot}. There sat the tray, and nearby was the real answer: {cause}. What gave it away was {clue}.",
        qa_text="They followed clues together instead of panicking",
        tags={"clue", "teamwork"},
    ),
    "call_then_check": Method(
        id="call_then_check",
        sense=2,
        power=3,
        team_text="{A} called to the grown-up at the doorway while {B} kept a finger pointed toward the strange sound. Together they stayed calm and checked the room one part at a time.",
        discover_text="With everyone looking carefully, the tray turned up at {spot}, and the mystery became ordinary: {cause}. The best clue was {clue}.",
        qa_text="They called for help and checked the room together",
        tags={"adult_help", "teamwork"},
    ),
    "hide_under_table": Method(
        id="hide_under_table",
        sense=1,
        power=1,
        team_text="{A} and {B} ducked under the table and hoped the problem would stop by itself.",
        discover_text="They peeped out at last and noticed {cause}, with {clue}.",
        qa_text="They hid instead of investigating",
        tags={"hiding"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ivy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
LANTERNS = ["paper lantern", "small flashlight", "glow lantern"]


@dataclass
class StoryParams:
    setting: str
    treat: str
    mystery: str
    method: str
    leader: str
    leader_gender: str
    helper: str
    helper_gender: str
    parent: str
    courage_level: int
    trust_level: int
    lantern: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "event": [
        ("What is an event?",
         "An event is a special planned time when people gather to do something together, like a fair, a show, or a party.")
    ],
    "ganache": [
        ("What is ganache?",
         "Ganache is a smooth chocolate mixture, often made from chocolate and cream. Bakers spread or drizzle it on desserts to make them shiny and rich.")
    ],
    "ghost": [
        ("Why can an old room feel spooky?",
         "Old rooms can feel spooky because they are dim, creaky, and full of strange sounds. Your imagination can make ordinary things seem bigger and scarier.")
    ],
    "draft": [
        ("What is a draft in a room?",
         "A draft is a little stream of moving air that slips through a crack or open door. It can make curtains move and lights flicker.")
    ],
    "cat": [
        ("Why might a cat sneak toward a dessert table?",
         "A cat might creep toward a dessert table because it smells something interesting. Animals often follow smells even when they are not supposed to.")
    ],
    "cart": [
        ("Why can a wobbly cart make trouble?",
         "A wobbly cart can roll or bump into things by accident. That can make objects slide and seem to move on their own.")
    ],
    "teamwork": [
        ("What does teamwork mean?",
         "Teamwork means people help one another and share the job. When one person watches and another checks, they can solve a problem better together.")
    ],
    "lantern": [
        ("Why is a lantern or flashlight helpful in the dark?",
         "A lantern or flashlight helps you see what is really there. Better light makes it easier to notice clues instead of guessing.")
    ],
    "adult_help": [
        ("When should children call a grown-up for help?",
         "Children should call a grown-up when something feels unsafe, confusing, or too big to handle alone. Asking for help is a smart and brave choice.")
    ],
}
KNOWLEDGE_ORDER = ["event", "ganache", "ghost", "draft", "cat", "cart", "teamwork", "lantern", "adult_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    setting = f["setting"]
    treat = f["treat"]
    mystery = f["mystery"]
    outcome = f["outcome"]
    base = (
        f'Write a gentle ghost-story-style story for a 3-to-5-year-old that includes the words '
        f'"event" and "ganache", and centers on teamwork in {setting.place}.'
    )
    if outcome == "flee":
        return [
            base,
            f"Tell a spooky but gentle story where {leader.id} and {helper.id} think a ghost has taken the {treat.tray_phrase}, but they run for the kitchen before solving it.",
            f"Write a story about a scary feeling at an {setting.event_name} where the children learn that being brave together would have helped them understand the mystery.",
        ]
    if outcome == "spoiled":
        return [
            base,
            f"Tell a cautionary mystery where {leader.id} and {helper.id} try to help together but pick a weak plan, and the dessert for the event gets spoiled.",
            f"Write a story where a spooky misunderstanding in an old room teaches children to use simple teamwork and careful checking.",
        ]
    return [
        base,
        f"Tell a ghost-story-style tale where {leader.id} and {helper.id} save a tray of {treat.ganache_phrase} for the event by working together and following clues.",
        f"Write a gentle spooky story where strange sounds seem ghostly at first, but teamwork reveals that the real cause is {mystery.cause}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["helper"]
    parent = f["parent"]
    setting = f["setting"]
    treat = f["treat"]
    mystery = f["mystery"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children helping at the {setting.event_name}, and {a.id}'s {parent.label_word}. They are trying to take care of the dessert table together."
        ),
        (
            "What made the room feel spooky?",
            f"The room was old and dim, and {mystery.sign}. That made the children think the place felt like a ghost story."
        ),
        (
            "What went missing?",
            f"The tray of {treat.ganache_phrase} went missing from the table. That mattered because it was meant for the event."
        ),
    ]
    if outcome == "solved":
        qa.extend([
            (
                "How did the children solve the mystery?",
                f"They worked together instead of panicking. {method.qa_text}, and that helped them notice {mystery.clue} and find the tray at {setting.hiding_spot}."
            ),
            (
                "Was there really a ghost?",
                f"No, there was not a ghost. The problem came from {mystery.cause}, which only seemed spooky before the children checked carefully."
            ),
            (
                "How did the story end?",
                f"It ended warmly, with the dessert table ready and the event beginning. The ganache shone in the light, which showed that the shadows no longer scared them."
            ),
        ])
    elif outcome == "flee":
        qa.extend([
            (
                "Why did the children run away?",
                f"They felt too scared to investigate, because the dark room and the missing tray made the mystery seem huge. They chose the bright kitchen instead of checking the clues together."
            ),
            (
                "How did the story end?",
                f"The event still happened, but the children wished they had been braver. The ending shows that the mystery stayed scary because they never looked closely at it."
            ),
        ])
    else:
        qa.extend([
            (
                "Did their plan work well?",
                f"No. They tried to help together, but their plan was too weak and too slow for the problem. Because of that, the dessert for the event was spoiled."
            ),
            (
                "What lesson did they learn?",
                f"They learned that teamwork works best when the plan is calm and sensible. Looking carefully and asking for help can solve more than hiding or fussing."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"event", "ganache", "ghost", "teamwork"}
    mystery = f["mystery"]
    method = f["method"]
    tags |= set(mystery.tags)
    tags |= set(method.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="hall",
        treat="cake",
        mystery="draft",
        method="lantern_search",
        leader="Lily",
        leader_gender="girl",
        helper="Tom",
        helper_gender="boy",
        parent="mother",
        courage_level=4,
        trust_level=4,
        lantern="paper lantern",
    ),
    StoryParams(
        setting="manor",
        treat="eclairs",
        mystery="cat",
        method="follow_clues",
        leader="Ben",
        leader_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent="father",
        courage_level=3,
        trust_level=4,
        lantern="small flashlight",
    ),
    StoryParams(
        setting="museum",
        treat="cookies",
        mystery="cart",
        method="call_then_check",
        leader="Ava",
        leader_gender="girl",
        helper="Max",
        helper_gender="boy",
        parent="mother",
        courage_level=3,
        trust_level=3,
        lantern="glow lantern",
    ),
    StoryParams(
        setting="hall",
        treat="cake",
        mystery="draft",
        method="lantern_search",
        leader="Sam",
        leader_gender="boy",
        helper="Lucy",
        helper_gender="girl",
        parent="father",
        courage_level=2,
        trust_level=2,
        lantern="small flashlight",
    ),
]


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
strong_enough(My, M) :- mystery(My), method(M), risk(My, R), power(M, P), P >= R.
valid(S, My, M) :- setting(S), mystery(My), method(M), sensible(M), strong_enough(My, M).

flee :- courage(C), trust(T), C + T < 6.
solved :- not flee, chosen_mystery(My), chosen_method(M), strong_enough(My, M).
spoiled :- not flee, chosen_mystery(My), chosen_method(M), not strong_enough(My, M).

outcome(flee) :- flee.
outcome(solved) :- solved.
outcome(spoiled) :- spoiled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("risk", mid, mystery.risk))
    for meth_id, method in METHODS.items():
        lines.append(asp.fact("method", meth_id))
        lines.append(asp.fact("sense", meth_id, method.sense))
        lines.append(asp.fact("power", meth_id, method.power))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_mystery", params.mystery),
        asp.fact("chosen_method", params.method),
        asp.fact("courage", params.courage_level),
        asp.fact("trust", params.trust_level),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story teamwork world: a spooky event, missing ganache, and a careful investigation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))
    if args.mystery and args.method:
        mystery = MYSTERIES[args.mystery]
        method = METHODS[args.method]
        if not valid_combo(SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values())), mystery, method):
            raise StoryError(explain_combo(mystery, method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, method_id = rng.choice(sorted(combos))
    treat_id = args.treat or rng.choice(sorted(TREATS))
    leader, leader_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    courage_level = rng.randint(2, 5)
    trust_level = rng.randint(2, 5)
    lantern = rng.choice(LANTERNS)
    return StoryParams(
        setting=setting_id,
        treat=treat_id,
        mystery=mystery_id,
        method=method_id,
        leader=leader,
        leader_gender=leader_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        courage_level=courage_level,
        trust_level=trust_level,
        lantern=lantern,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        treat = TREATS[params.treat]
        mystery = MYSTERIES[params.mystery]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(method.id))

    world = tell(
        setting=setting,
        treat=treat,
        mystery=mystery,
        method=method,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        courage_level=params.courage_level,
        trust_level=params.trust_level,
        lantern=params.lantern,
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

    c_sens = set(asp_sensible())
    p_sens = {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    scenarios = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            scenarios.append(p)
        except StoryError:
            rc = 1
            print("Random resolve_params unexpectedly failed during verify.")
            break

    bad = sum(1 for p in scenarios if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, method) combos:\n")
        for setting, mystery, method in combos:
            print(f"  {setting:8} {mystery:8} {method}")
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
            header = (
                f"### {p.leader} & {p.helper}: {p.treat} at {p.setting} "
                f"({p.mystery}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
