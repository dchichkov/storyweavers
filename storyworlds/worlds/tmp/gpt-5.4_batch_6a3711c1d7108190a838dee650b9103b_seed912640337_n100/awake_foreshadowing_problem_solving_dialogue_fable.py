#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/awake_foreshadowing_problem_solving_dialogue_fable.py
================================================================================

A standalone story world for a small fable-like domain built from the seed
word "awake" and the features Foreshadowing, Problem Solving, and Dialogue.

Premise
-------
A young animal wants to stay awake to see a lovely night-time wonder, but also
has an important dawn duty in the village. A wiser elder notices the risk
before it becomes a disaster, a friend helps think through the problem, and the
group chooses a solution that truly fits the duty. The story then proves the
change with an ending image at sunrise.

This world models:
- physical meters like sleepiness, readiness, and done-ness,
- emotional memes like pride, worry, trust, and relief,
- a reasonableness gate over which fixes genuinely fit which duties,
- an inline ASP twin for the same compatibility logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/awake_foreshadowing_problem_solving_dialogue_fable.py
    python storyworlds/worlds/gpt-5.4/awake_foreshadowing_problem_solving_dialogue_fable.py --event moonflower --duty bell
    python storyworlds/worlds/gpt-5.4/awake_foreshadowing_problem_solving_dialogue_fable.py --duty gate --solution bell_string
    python storyworlds/worlds/gpt-5.4/awake_foreshadowing_problem_solving_dialogue_fable.py --all
    python storyworlds/worlds/gpt-5.4/awake_foreshadowing_problem_solving_dialogue_fable.py --verify
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
# from this nested directory: storyworlds/worlds/gpt-5.4/<file>.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # mouse, rabbit, hedgehog, owl, bell, gate...
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def kind_word(self) -> str:
        return self.type


@dataclass
class Place:
    id: str
    label: str
    night_image: str
    dawn_image: str
    travel: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    label: str
    sight: str
    cue: str
    lateness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Duty:
    id: str
    label: str
    need: str                 # sound | presence | carry
    location: str
    act: str
    done_text: str
    value_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    supports: set[str]
    power: int
    offer: str
    method_text: str
    success_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def duty_risk(place: Place, event: Event, duty: Duty) -> int:
    return place.travel + event.lateness


def solution_fits(solution: Solution, duty: Duty, place: Place, event: Event) -> bool:
    return duty.need in solution.supports and solution.power >= duty_risk(place, event, duty)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for event_id, event in EVENTS.items():
            for duty_id, duty in DUTIES.items():
                for sol_id, sol in SOLUTIONS.items():
                    if solution_fits(sol, duty, place, event):
                        combos.append((place_id, event_id, duty_id, sol_id))
    return combos


def predict_problem(world: World, place: Place, event: Event, duty: Duty) -> dict:
    risk = duty_risk(place, event, duty)
    return {
        "risk": risk,
        "too_sleepy": risk >= 3,
        "miss_duty": risk >= 3,
    }


def _r_sleepiness(world: World) -> list[str]:
    hero = world.get("hero")
    duty = world.facts["duty"]
    place = world.facts["place"]
    event = world.facts["event"]
    sig = ("sleepiness", event.id, duty.id, place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    risk = duty_risk(place, event, duty)
    hero.meters["sleepiness"] += float(risk)
    if risk >= 3:
        hero.memes["worry"] += 1
        return ["__heavy_eyes__"]
    hero.memes["hope"] += 1
    return []


def _r_solution_ready(world: World) -> list[str]:
    hero = world.get("hero")
    solution = world.facts.get("solution")
    duty = world.facts.get("duty")
    place = world.facts.get("place")
    event = world.facts.get("event")
    if not solution or not duty or not place or not event:
        return []
    sig = ("solution", solution.id)
    if sig in world.fired:
        return []
    if not solution_fits(solution, duty, place, event):
        return []
    world.fired.add(sig)
    hero.meters["readiness"] += 1
    hero.meters["sleepiness"] = max(0.0, hero.meters["sleepiness"] - float(solution.power))
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule("sleepiness", "physical", _r_sleepiness),
    Rule("solution_ready", "physical", _r_solution_ready),
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


def introduce(world: World, hero: Entity, friend: Entity, place: Place, duty: Duty) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"In {place.label}, a young {hero.type} named {hero.id} liked to be the first pair of eyes to notice what the day needed."
    )
    world.say(
        f"Each morning, {hero.id} had one small but important job: {duty.act} at {duty.location}. {duty.value_text}"
    )
    world.say(
        f"{friend.id}, a steady {friend.type}, often worked nearby and knew how seriously {hero.id} took that duty."
    )


def tempt(world: World, hero: Entity, event: Event, place: Place) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"That evening, {place.night_image}. Word drifted through the grass that {event.cue} and {event.sight}."
    )
    world.say(
        f'"I will stay awake and see it with my own eyes," said {hero.id}. "Then I will still be ready at dawn."'
    )


def foreshadow(world: World, elder: Entity, hero: Entity, event: Event, duty: Duty, place: Place) -> None:
    pred = predict_problem(world, place, event, duty)
    world.facts["predicted_risk"] = pred["risk"]
    elder.memes["care"] += 1
    if pred["too_sleepy"]:
        world.say(
            f'The old {elder.type}, {elder.id}, listened from a branch and said, "A long night can make a short morning. Heavy eyes do not {duty.act.split()[0]} very quickly."'
        )
    else:
        world.say(
            f'The old {elder.type}, {elder.id}, listened from a branch and said, "Even a lovely night should leave room for the work of dawn."'
        )
    world.say(
        f'{hero.id} tried to laugh, but the warning stayed in the air like a small cloud before rain.'
    )


def deepen_night(world: World, hero: Entity, event: Event) -> None:
    propagate(world, narrate=False)
    if hero.meters["sleepiness"] >= 3:
        world.say(
            f"As the night stretched on, {hero.id}'s eyes grew round and sore. {hero.pronoun('possessive').capitalize()} paws slowed, though {hero.pronoun()} kept whispering, \"I am still awake. I am still awake.\""
        )
    else:
        world.say(
            f"The night was not too long, yet it still asked patience of {hero.id}, who sat very still and listened for the first sign of {event.label}."
        )


def consult(world: World, hero: Entity, friend: Entity, duty: Duty) -> None:
    hero.memes["trust"] += 1
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} came with a quiet step and sat beside {hero.id}. "If you spend all your strength on staying awake," {friend.pronoun()} asked, "who will {duty.act} when the sky turns pale?"'
    )
    world.say(
        f'"That is the knot in my thoughts," admitted {hero.id}. "I want both the wonder of night and the work of morning."'
    )


def solve(world: World, hero: Entity, friend: Entity, solution: Solution) -> None:
    world.say(
        f'"Then let us untie the knot," said {friend.id}. "{solution.offer}"'
    )
    world.say(solution.method_text.replace("{hero}", hero.id).replace("{friend}", friend.id))


def witness(world: World, hero: Entity, event: Event) -> None:
    world.say(
        f"Soon {event.sight}, and {hero.id} saw the beauty {hero.pronoun()} had hoped for. Because the plan had eased the danger, wonder no longer felt like a thief stealing from the morning."
    )


def dawn_resolution(world: World, hero: Entity, friend: Entity, duty: Duty, place: Place, solution: Solution) -> None:
    hero.meters["duty_done"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"At dawn, {solution.success_text.replace('{hero}', hero.id).replace('{friend}', friend.id)}"
    )
    world.say(
        f"{hero.id} {duty.done_text}. {place.dawn_image}"
    )
    world.say(
        f'"Now I know," said {hero.id}, "being awake is not the same as being ready."'
    )
    world.say(
        f'"And wisdom," said {friend.id}, "helps both wonder and work arrive on time."'
    )


def moral(world: World) -> None:
    world.say(
        "So the little village remembered: pride may keep your eyes open for a while, but good thinking keeps your promises."
    )


def tell(place: Place, event: Event, duty: Duty, solution: Solution,
         hero_name: str = "Pip", hero_kind: str = "mouse",
         friend_name: str = "Mara", friend_kind: str = "rabbit",
         elder_name: str = "Old Elm", elder_kind: str = "owl") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_kind, role="friend"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_kind, role="elder"))
    world.add(Entity(id="duty", kind="thing", type=duty.id, label=duty.label))
    world.facts.update(place=place, event=event, duty=duty, solution=solution)

    introduce(world, hero, friend, place, duty)

    world.para()
    tempt(world, hero, event, place)
    foreshadow(world, elder, hero, event, duty, place)

    world.para()
    deepen_night(world, hero, event)
    consult(world, hero, friend, duty)
    solve(world, hero, friend, solution)

    world.para()
    propagate(world, narrate=False)
    witness(world, hero, event)
    dawn_resolution(world, hero, friend, duty, place, solution)

    world.para()
    moral(world)

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        risk=duty_risk(place, event, duty),
        solved=solution_fits(solution, duty, place, event),
        saw_event=True,
        did_duty=hero.meters["duty_done"] >= THRESHOLD,
    )
    return world


PLACES = {
    "meadow": Place(
        "meadow",
        "the meadow at the edge of the village",
        "the reeds whispered and the clover smelled cool",
        "The first gold light touched the grass, and every dew bead looked like a tiny bell.",
        travel=1,
        tags={"meadow"},
    ),
    "orchard": Place(
        "orchard",
        "the orchard behind the burrows",
        "apple leaves shivered softly, and the paths under the trees turned silver",
        "Sunshine slipped between the branches and made the apples blush brighter.",
        travel=1,
        tags={"orchard"},
    ),
    "pond": Place(
        "pond",
        "the pond beyond the willow bridge",
        "the water held the moon like a coin, far beyond the willow roots",
        "The pond brightened from gray to blue while rings spread over the water.",
        travel=2,
        tags={"pond"},
    ),
}

EVENTS = {
    "fireflies": Event(
        "fireflies",
        "the firefly dance",
        "a hundred fireflies lifted together like little lamps",
        "the first fireflies would soon rise above the grass",
        lateness=1,
        tags={"fireflies", "night"},
    ),
    "moonflower": Event(
        "moonflower",
        "the moonflower opening",
        "the moonflower slowly opened its white petals to the moon",
        "the moonflower by the hedge would not open until the night grew deep",
        lateness=2,
        tags={"flower", "night"},
    ),
    "startrail": Event(
        "startrail",
        "the star trail",
        "a silver line crossed the sky and seemed to stitch one star to another",
        "a bright wandering star would not pass until nearly morning",
        lateness=2,
        tags={"stars", "night"},
    ),
}

DUTIES = {
    "bell": Duty(
        "bell",
        "the dawn bell",
        "sound",
        "the bell post",
        "ring the dawn bell",
        "rang the dawn bell so the village woke together",
        "The bell told everyone it was time to wake, stretch, and begin the day kindly.",
        tags={"bell", "dawn"},
    ),
    "gate": Duty(
        "gate",
        "the clover gate",
        "presence",
        "the clover gate",
        "open the clover gate",
        "opened the clover gate so the lambs could walk out to breakfast",
        "The gate needed a steady paw at the latch before the little flock could leave safely.",
        tags={"gate", "dawn"},
    ),
    "dew": Duty(
        "dew",
        "the dew bucket",
        "carry",
        "the seed beds",
        "carry the dew bucket to the seed beds",
        "carried the dew bucket to the seed beds before the sun drank the drops away",
        "The seedlings waited for those cool drops before the day turned warm.",
        tags={"garden", "dawn"},
    ),
}

SOLUTIONS = {
    "dew_timer": Solution(
        "dew_timer",
        "a dew timer",
        {"presence", "carry"},
        2,
        "fill a little shell with dew and set it above your nose; when it tips at dawn, it will wake you",
        "{friend} balanced a curled leaf and a shell of dew beside {hero}'s bed, then marked where the first sunbeam would strike.",
        "{hero} woke at the cool drip on {hero}'s whiskers and sprang up in time.",
        "They used a tiny dew timer to wake the hero exactly at dawn.",
        tags={"timer", "dew"},
    ),
    "friend_watch": Solution(
        "friend_watch",
        "a shared watch",
        {"sound", "presence", "carry"},
        4,
        "take turns, and I will watch the last part of the night while you sleep",
        "{friend} promised to keep watch until the wonder arrived, then nudge {hero} before dawn and walk with {hero} to the morning task.",
        "{friend} nudged {hero} at the first pale edge of morning, and together they hurried without confusion.",
        "The friend took the late watch and woke the hero in time to do the duty together.",
        tags={"friend", "watch"},
    ),
    "bell_string": Solution(
        "bell_string",
        "a bell string",
        {"sound"},
        4,
        "tie a long string from your sleeping mat to the bell rope, so one sharp tug will ring it at dawn",
        "{friend} and {hero} tied a clean grass-cord from the sleeping mat to the bell rope and tested one neat pull.",
        "{hero} gave one bright tug from the mat, and the bell answered clear and true.",
        "They tied a string from the sleeping mat to the bell, so the hero could ring it right at dawn.",
        tags={"bell", "string"},
    ),
}

HERO_NAMES = ["Pip", "Nell", "Timo", "Lark", "Bram", "Moss", "Wren", "Jun"]
ANIMAL_KINDS = ["mouse", "rabbit", "hedgehog", "squirrel"]
ELDER_KINDS = ["owl", "tortoise"]


@dataclass
class StoryParams:
    place: str
    event: str
    duty: str
    solution: str
    hero_name: str
    hero_kind: str
    friend_name: str
    friend_kind: str
    elder_name: str
    elder_kind: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "night": [
        ("Why is it harder to stay awake very late at night?",
         "Bodies grow sleepy when the night gets long. Heavy eyes and slow thinking make work harder in the morning.")
    ],
    "dawn": [
        ("What is dawn?",
         "Dawn is the early time when night begins to turn into morning. The sky grows pale before the sun climbs up.")
    ],
    "fireflies": [
        ("What are fireflies?",
         "Fireflies are little insects that can glow in the dark. Their lights make summer nights look dotted with tiny lamps.")
    ],
    "flower": [
        ("What is a moonflower?",
         "A moonflower is a flower that opens when the evening grows dark. Its pale petals can look bright in moonlight.")
    ],
    "stars": [
        ("Why do stars seem brighter at night?",
         "Stars are easier to see at night because the sky is dark then. In daytime, sunlight is so bright that it hides them.")
    ],
    "bell": [
        ("Why would a village ring a bell at dawn?",
         "A bell can tell everyone the day is beginning. It is a simple way to wake many neighbors at once.")
    ],
    "gate": [
        ("Why must a gate be opened carefully?",
         "A gate needs a steady paw or hand so it does not swing the wrong way. Careful opening helps animals pass through safely.")
    ],
    "garden": [
        ("Why do seedlings need water early?",
         "Small seedlings dry out quickly once the day grows warm. Early water helps them stay fresh and strong.")
    ],
    "friend": [
        ("How can a friend help with a hard problem?",
         "A friend can notice what you miss and think with you. Two calm minds often find a better plan than one proud one.")
    ],
    "timer": [
        ("What does a timer do?",
         "A timer helps you notice when a certain time has come. It can remind you to wake up or start a job.")
    ],
    "string": [
        ("What can a string help you do?",
         "A string can pull, tie, or connect two things. That makes it useful for simple clever tools.")
    ],
}
KNOWLEDGE_ORDER = [
    "night", "dawn", "fireflies", "flower", "stars", "bell", "gate", "garden",
    "friend", "timer", "string",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    duty = f["duty"]
    solution = f["solution"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the word "awake" and shows a small animal solving a dawn problem.',
        f"Tell a gentle story where {hero.id} wants to stay awake to see {event.label}, but still must {duty.act}, and a friend helps with a thoughtful plan.",
        f'Write a dialogue-rich fable with foreshadowing, where the warning comes early and the solution is "{solution.label}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    event = f["event"]
    duty = f["duty"]
    solution = f["solution"]
    risk = f["risk"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about a young {hero.type} named {hero.id}, {friend.id} the {friend.type}, and {elder.id} the old {elder.type}. {hero.id} wanted both a night-time wonder and a good morning."),
        (f"Why did {hero.id} want to stay awake?",
         f"{hero.id} wanted to stay awake to see {event.label}. The night wonder felt special enough that {hero.pronoun()} did not want to miss it."),
        (f"What warning did {elder.id} give?",
         f"{elder.id} warned that a long night can make a short morning. That warning foreshadowed the real problem: sleepy eyes might spoil {hero.id}'s dawn duty."),
        (f"What was the problem {hero.id} had to solve?",
         f"{hero.id} wanted to see {event.label} and still {duty.act}. Those two wishes pulled against each other because the night was long and the duty came early."),
        (f"How did {friend.id} help solve it?",
         f"{friend.id} listened to the problem and suggested {solution.label}. The plan worked because it truly fit the job of {duty.label} and took away the danger of oversleeping."),
        (f"Did {hero.id} finish the morning duty?",
         f"Yes. {hero.id} {duty.done_text}. The story proves the solution worked by showing the village morning happen on time."),
    ]
    if risk >= 3:
        qa.append((
            f"Why was the danger real, not just a worry?",
            f"The event happened late and the duty still needed to be done at dawn, so {hero.id} was growing too sleepy. The elder's warning matched the world of the story, where heavy eyes make promises harder to keep."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["event"].tags) | set(f["duty"].tags) | set(f["solution"].tags) | {"night", "dawn", "friend"}
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "fireflies", "bell", "bell_string", "Pip", "mouse", "Mara", "rabbit", "Old Elm", "owl"),
    StoryParams("orchard", "moonflower", "gate", "friend_watch", "Nell", "hedgehog", "Bram", "squirrel", "Mossback", "tortoise"),
    StoryParams("meadow", "fireflies", "dew", "dew_timer", "Wren", "rabbit", "Jun", "mouse", "Old Elm", "owl"),
    StoryParams("pond", "startrail", "bell", "friend_watch", "Timo", "squirrel", "Lark", "rabbit", "Mossback", "tortoise"),
]


def explain_rejection(place: Place, event: Event, duty: Duty, solution: Solution) -> str:
    risk = duty_risk(place, event, duty)
    if duty.need not in solution.supports:
        return (
            f"(No story: {solution.label} does not actually fit {duty.label}. "
            f"That duty needs {duty.need}, but this solution supports {sorted(solution.supports)}.)"
        )
    return (
        f"(No story: {solution.label} is too weak for this night. The risk is {risk}, "
        f"but the solution only handles {solution.power}, so the promise at dawn would not be believable.)"
    )


ASP_RULES = r"""
risk(P,E,D,R) :- travel(P,T), lateness(E,L), R = T + L.

fits(S,P,E,D) :- solution(S), duty(D),
                 supports(S,N), need(D,N),
                 risk(P,E,D,R), power(S,SP), SP >= R.

valid(P,E,D,S) :- place(P), event(E), duty(D), solution(S), fits(S,P,E,D).

chosen_valid :- chosen_place(P), chosen_event(E), chosen_duty(D), chosen_solution(S),
                valid(P,E,D,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("travel", pid, place.travel))
    for eid, event in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("lateness", eid, event.lateness))
    for did, duty in DUTIES.items():
        lines.append(asp.fact("duty", did))
        lines.append(asp.fact("need", did, duty.need))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("power", sid, sol.power))
        for need in sorted(sol.supports):
            lines.append(asp.fact("supports", sid, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_chosen_valid(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_event", params.event),
        asp.fact("chosen_duty", params.duty),
        asp.fact("chosen_solution", params.solution),
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_valid/0."))
    return bool(asp.atoms(model, "chosen_valid"))


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    smoke_cases = list(CURATED)
    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"ERROR: default resolve_params failed during smoke setup: {err}")

    for p in smoke_cases:
        py_ok = solution_fits(SOLUTIONS[p.solution], DUTIES[p.duty], PLACES[p.place], EVENTS[p.event])
        asp_ok = asp_chosen_valid(p)
        if py_ok != asp_ok:
            rc = 1
            print(f"MISMATCH on chosen validity for {p}: python={py_ok} asp={asp_ok}")

    try:
        sample = generate(smoke_cases[0])
        if not sample.story or "awake" not in sample.story.lower():
            raise StoryError("Generated smoke-test story was empty or missed the seed word 'awake'.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"ERROR: smoke test generation failed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-like story world: a small animal tries to stay awake for a night wonder and still keep a dawn promise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--duty", choices=DUTIES)
    ap.add_argument("--solution", choices=SOLUTIONS)
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


def _pick_name(rng: random.Random, avoid: str = "") -> str:
    pool = [n for n in HERO_NAMES if n != avoid]
    return rng.choice(pool)


def _pick_kind(rng: random.Random, avoid: str = "") -> str:
    pool = [k for k in ANIMAL_KINDS if k != avoid] or list(ANIMAL_KINDS)
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.event and args.duty and args.solution:
        place = PLACES[args.place]
        event = EVENTS[args.event]
        duty = DUTIES[args.duty]
        solution = SOLUTIONS[args.solution]
        if not solution_fits(solution, duty, place, event):
            raise StoryError(explain_rejection(place, event, duty, solution))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.event is None or c[1] == args.event)
        and (args.duty is None or c[2] == args.duty)
        and (args.solution is None or c[3] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, event, duty, solution = rng.choice(sorted(combos))
    hero_name = _pick_name(rng)
    hero_kind = _pick_kind(rng)
    friend_name = _pick_name(rng, avoid=hero_name)
    friend_kind = _pick_kind(rng, avoid=hero_kind)
    elder_name = rng.choice(["Old Elm", "Mossback", "Moonfeather", "Quiet Step"])
    elder_kind = rng.choice(ELDER_KINDS)
    return StoryParams(
        place=place,
        event=event,
        duty=duty,
        solution=solution,
        hero_name=hero_name,
        hero_kind=hero_kind,
        friend_name=friend_name,
        friend_kind=friend_kind,
        elder_name=elder_name,
        elder_kind=elder_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        EVENTS[params.event],
        DUTIES[params.duty],
        SOLUTIONS[params.solution],
        params.hero_name,
        params.hero_kind,
        params.friend_name,
        params.friend_kind,
        params.elder_name,
        params.elder_kind,
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
        print(f"{len(combos)} compatible (place, event, duty, solution) combos:\n")
        for place, event, duty, solution in combos:
            print(f"  {place:8} {event:10} {duty:6} {solution}")
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
            header = f"### {p.hero_name}: {p.event} -> {p.duty} with {p.solution} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
