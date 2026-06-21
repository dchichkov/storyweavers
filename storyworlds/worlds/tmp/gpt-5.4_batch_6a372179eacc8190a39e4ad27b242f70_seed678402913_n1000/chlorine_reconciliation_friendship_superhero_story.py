#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chlorine_reconciliation_friendship_superhero_story.py
================================================================================

A standalone story world for a child-facing superhero-style friendship story
about a chlorinated pool, a hurt feeling, and a real apology.

The core shape is simple and constrained:

- Two friends are playing superheroes at a pool.
- One child does a splashy move too close to the other.
- Chlorine water gets in the other child's eyes and the game breaks.
- A repair attempt can be wise or weak.
- Wise repair leads to reconciliation and a changed ending image.

Run it
------
python storyworlds/worlds/gpt-5.4/chlorine_reconciliation_friendship_superhero_story.py
python storyworlds/worlds/gpt-5.4/chlorine_reconciliation_friendship_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/chlorine_reconciliation_friendship_superhero_story.py --place playground
python storyworlds/worlds/gpt-5.4/chlorine_reconciliation_friendship_superhero_story.py --response shrug
python storyworlds/worlds/gpt-5.4/chlorine_reconciliation_friendship_superhero_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/chlorine_reconciliation_friendship_superhero_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
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
    chlorinated: bool = False
    splashy: bool = False
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
class Place:
    id: str
    label: str
    scene: str
    water_label: str
    chlorinated: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    team_name: str
    opening: str
    goal: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Move:
    id: str
    label: str
    shout: str
    splash_power: int
    close_to_face: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    apology: bool
    wait_kindly: bool
    text: str
    fail_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

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


def _r_sting(world: World) -> list[str]:
    out: list[str] = []
    place = world.entities.get("place")
    target = world.entities.get("friend")
    if place is None or target is None:
        return out
    if place.chlorinated and target.meters["face_splashed"] >= THRESHOLD:
        sig = ("sting", target.id)
        if sig not in world.fired:
            world.fired.add(sig)
            target.meters["eyes_stinging"] += 1
            target.memes["hurt"] += 1
            target.memes["anger"] += 1
            out.append("__sting__")
    return out


def _r_rift(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("instigator")
    b = world.entities.get("friend")
    if a is None or b is None:
        return out
    if b.memes["hurt"] >= THRESHOLD:
        sig = ("rift", a.id, b.id)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["guilt"] += 1
            a.memes["worry"] += 1
            a.meters["friendship_strain"] += 1
            b.meters["friendship_strain"] += 1
            out.append("__rift__")
    return out


CAUSAL_RULES = [
    Rule(name="sting", tag="physical", apply=_r_sting),
    Rule(name="rift", tag="social", apply=_r_rift),
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


def hazard_at_risk(place: Place, move: Move) -> bool:
    return place.chlorinated and move.close_to_face and move.splash_power > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def repair_need(move: Move, trust: int) -> int:
    return move.splash_power + (1 if trust <= 3 else 0)


def is_reconciled(move: Move, response: Response, trust: int) -> bool:
    return response.apology and response.power >= repair_need(move, trust)


def predict_hurt(world: World, move: Move) -> dict:
    sim = world.copy()
    do_mishap(sim, move, narrate=False)
    friend = sim.get("friend")
    return {
        "eyes_stinging": friend.meters["eyes_stinging"],
        "friendship_strain": friend.meters["friendship_strain"],
    }


def introduce(world: World, place: Place, mission: Mission, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"After swim time began, {a.id} and {b.id} hurried to {place.label} and turned the water into {mission.opening}."
    )
    world.say(
        f"They called themselves {mission.team_name}, and their big plan was {mission.goal}."
    )
    world.say(
        f"The water smelled a little like chlorine, but to them it still felt like the shining sea where heroes trained."
    )


def build_game(world: World, a: Entity, b: Entity, mission: Mission) -> None:
    world.say(
        f'{a.id} pointed ahead. "I will lead the charge!"'
    )
    world.say(
        f'{b.id} grinned. "Then I will guard your side, partner."'
    )
    if b.attrs.get("bond") == "best_friends":
        world.say("They moved so easily together that it looked as if they had practiced for a hundred superhero Saturdays.")


def warning(world: World, a: Entity, b: Entity, adult: Entity, move: Move) -> None:
    pred = predict_hurt(world, move)
    world.facts["predicted_strain"] = pred["friendship_strain"]
    world.say(
        f"{adult.label_word.capitalize()} stood nearby with a towel and called, "
        f'"Heroes keep space for each other. Big splashes too close can sting eyes in chlorinated water."'
    )
    if pred["eyes_stinging"] >= THRESHOLD:
        world.say(
            f"{b.id} looked at the choppy water and nodded, because even a game could hurt if someone forgot to be careful."
        )


def choose_move(world: World, a: Entity, move: Move) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'But {a.id} was buzzing with excitement. "{move.shout}" {a.pronoun()} shouted, and {a.pronoun()} launched {a.pronoun("possessive")} {move.label}.'
    )


def do_mishap(world: World, move: Move, narrate: bool = True) -> None:
    friend = world.get("friend")
    friend.meters["face_splashed"] += 1
    friend.meters["wet"] += 1
    world.facts["mishap_move"] = move.id
    propagate(world, narrate=narrate)


def mishap_scene(world: World, a: Entity, b: Entity, place: Place, move: Move) -> None:
    do_mishap(world, move)
    world.say(
        f"A bright sheet of water slapped across {b.id}'s face. {b.id} blinked hard, and the chlorine from {place.water_label} made {b.pronoun('possessive')} eyes sting."
    )
    world.say(
        f'"Ow!" {b.id} cried. "That was too close!"'
    )
    if b.attrs.get("bond") == "best_friends":
        world.say(
            f"What hurt almost as much as the sting was the feeling that {a.id} had forgotten to protect {b.pronoun('object')}."
        )


def rupture(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"{b.id} turned away and hugged {b.pronoun('possessive')} arms. The superhero game fell quiet all at once."
    )
    world.say(
        f"{a.id}'s brave grin disappeared. Seeing {b.id} hurt made {a.pronoun('object')} feel small instead of mighty."
    )


def repair_scene(world: World, a: Entity, b: Entity, adult: Entity, response: Response) -> None:
    if response.apology:
        b.meters["eyes_stinging"] = max(0.0, b.meters["eyes_stinging"] - 1)
        b.memes["anger"] = max(0.0, b.memes["anger"] - 1)
        a.meters["friendship_strain"] = 0.0
        b.meters["friendship_strain"] = 0.0
        b.memes["trust"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        a.memes["friendship"] += 1
        b.memes["friendship"] += 1
        world.say(
            f"{adult.label_word.capitalize()} pointed to the rinse shower, and {a.id} {response.text}"
        )
    else:
        world.say(
            f"{a.id} {response.fail_text}"
        )


def ending_reconciled(world: World, a: Entity, b: Entity, mission: Mission) -> None:
    world.say(
        f'{b.id} looked at {a.id} for a moment, then nodded. "Next time, hero, leave room for your partner."'
    )
    world.say(
        f'"I will," said {a.id}. This time {a.pronoun()} meant it.'
    )
    world.say(
        f"Soon the two friends were side by side again, finishing {mission.ending}. Their splashes were smaller now, and their friendship looked stronger than the pretend powers."
    )


def ending_strained(world: World, a: Entity, b: Entity, mission: Mission) -> None:
    world.say(
        f"{b.id} did rinse {b.pronoun('possessive')} eyes, but the hurt feeling stayed. {a.id} floated on one side of the lane, and {b.id} stayed on the other."
    )
    world.say(
        f"The mission about {mission.goal} never really came back. By the end of swim time, both children knew that a superhero team needs kindness, not just a flashy move."
    )


def tell(
    place: Place,
    mission: Mission,
    move: Move,
    response: Response,
    instigator_name: str = "Kai",
    instigator_gender: str = "boy",
    friend_name: str = "Mina",
    friend_gender: str = "girl",
    adult_type: str = "mother",
    bond: str = "friends",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator_name,
        role="instigator",
        attrs={"bond": bond, "trust": trust},
    ))
    b = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        attrs={"bond": bond, "trust": trust},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        role="adult",
    ))
    pool = world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        chlorinated=place.chlorinated,
        tags=set(place.tags),
    ))

    introduce(world, place, mission, a, b)
    build_game(world, a, b, mission)

    world.para()
    warning(world, a, b, adult, move)
    choose_move(world, a, move)
    mishap_scene(world, a, b, place, move)
    rupture(world, a, b)

    world.para()
    repair_scene(world, a, b, adult, response)
    outcome = "reconciled" if is_reconciled(move, response, trust) else "strained"
    if outcome == "reconciled":
        ending_reconciled(world, a, b, mission)
    else:
        ending_strained(world, a, b, mission)

    world.facts.update(
        place=place,
        mission=mission,
        move=move,
        response=response,
        instigator=a,
        friend=b,
        adult=adult,
        instigator_name=instigator_name,
        friend_name=friend_name,
        trust=trust,
        bond=bond,
        outcome=outcome,
        chlorine=place.chlorinated,
    )
    return world


PLACES = {
    "community_pool": Place(
        id="community_pool",
        label="the community pool",
        scene="blue lanes under a bright roof",
        water_label="the pool water",
        chlorinated=True,
        tags={"pool", "chlorine"},
    ),
    "swim_center": Place(
        id="swim_center",
        label="the swim center",
        scene="a warm indoor pool with echoing walls",
        water_label="the lane water",
        chlorinated=True,
        tags={"pool", "chlorine"},
    ),
    "hotel_pool": Place(
        id="hotel_pool",
        label="the hotel pool",
        scene="a round pool with silver railings",
        water_label="the hotel pool",
        chlorinated=True,
        tags={"pool", "chlorine"},
    ),
    "playground": Place(
        id="playground",
        label="the playground fountain",
        scene="a dry climbing yard",
        water_label="the fountain mist",
        chlorinated=False,
        tags={"playground"},
    ),
}

MISSIONS = {
    "rescue": Mission(
        id="rescue",
        team_name="the Splash Shield League",
        opening="a city of waves and ladders",
        goal="saving a floating ring from the dragon drain",
        ending="their rescue patrol before the whistle blew",
        tags={"superhero", "teamwork"},
    ),
    "meteor": Mission(
        id="meteor",
        team_name="the Comet Capes",
        opening="a secret ocean base",
        goal="blocking a pretend meteor with water-power",
        ending="their meteor defense mission with calm, careful strokes",
        tags={"superhero", "teamwork"},
    ),
    "moon": Mission(
        id="moon",
        team_name="the Moon Current Heroes",
        opening="a moon harbor full of shining waves",
        goal="guarding the silver bridge from sea monsters",
        ending="their moon-harbor watch together",
        tags={"superhero", "teamwork"},
    ),
}

MOVES = {
    "cannonball": Move(
        id="cannonball",
        label="cannonball kick",
        shout="Cannon Splash Blast!",
        splash_power=2,
        close_to_face=True,
        tags={"splash"},
    ),
    "whirlpool": Move(
        id="whirlpool",
        label="whirlpool spin",
        shout="Whirlpool Shield!",
        splash_power=1,
        close_to_face=True,
        tags={"splash"},
    ),
    "tidal_kick": Move(
        id="tidal_kick",
        label="tidal kick",
        shout="Tidal Kick!",
        splash_power=2,
        close_to_face=True,
        tags={"splash"},
    ),
    "pose": Move(
        id="pose",
        label="hero pose",
        shout="Sky Cape Pose!",
        splash_power=0,
        close_to_face=False,
        tags={"pose"},
    ),
}

RESPONSES = {
    "apology_rinse_wait": Response(
        id="apology_rinse_wait",
        sense=3,
        power=3,
        apology=True,
        wait_kindly=True,
        text='hurried over, said, "I am sorry, {friend}. I was showing off," and stayed beside {friend} under the shower until the sting was gone.'.replace("{friend}", "friend"),
        fail_text='mumbled "oops" and looked away, hoping the problem would float off by itself.',
        qa_text="apologized, helped rinse the chlorine away, and waited kindly",
        tags={"apology", "shower", "friendship"},
    ),
    "apology_towel": Response(
        id="apology_towel",
        sense=2,
        power=2,
        apology=True,
        wait_kindly=True,
        text='grabbed a towel, said, "I am sorry, {friend}," and walked {friend} to the rinse shower before trying to play again.'.replace("{friend}", "friend"),
        fail_text='said sorry too quickly and tried to rush straight back to the game.',
        qa_text="said sorry, brought a towel, and helped at the rinse shower",
        tags={"apology", "towel", "friendship"},
    ),
    "adult_help": Response(
        id="adult_help",
        sense=3,
        power=3,
        apology=True,
        wait_kindly=True,
        text='called for help, apologized right away, and listened while the grown-up helped rinse the sore eyes gently.',
        fail_text='called for help without admitting what had happened.',
        qa_text="called for help, apologized, and stayed for the careful rinse",
        tags={"apology", "adult_help", "friendship"},
    ),
    "shrug": Response(
        id="shrug",
        sense=1,
        power=0,
        apology=False,
        wait_kindly=False,
        text='shrugged and said the game mattered more than the sting.',
        fail_text='shrugged and said, "It was just water," even though the chlorine still burned.',
        qa_text="shrugged instead of repairing the hurt",
        tags={"poor_repair"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Kai", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Noah"]


@dataclass
class StoryParams:
    place: str
    mission: str
    move: str
    response: str
    instigator_name: str
    instigator_gender: str
    friend_name: str
    friend_gender: str
    adult: str
    bond: str = "friends"
    trust: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "chlorine": [(
        "What is chlorine in a swimming pool?",
        "Chlorine is a chemical grown-ups use in pool water to help keep the water clean. If it splashes in your eyes, it can sting."
    )],
    "pool": [(
        "Why do pool rules tell swimmers to keep space?",
        "Keeping space helps everyone stay safe and comfortable in the water. Big splashes and kicks are less likely to hit someone by accident."
    )],
    "apology": [(
        "What makes an apology feel real?",
        "A real apology says what went wrong and tries to help fix the hurt. Waiting kindly and changing your behavior shows you mean it."
    )],
    "friendship": [(
        "How can friends get close again after a mistake?",
        "Friends can listen, say sorry, and do something helpful to repair the problem. Trust grows back when kind actions match the words."
    )],
    "shower": [(
        "Why do swimmers rinse after chlorine water stings their eyes?",
        "Clean water can wash the chlorinated pool water away. That helps the sting calm down."
    )],
}
KNOWLEDGE_ORDER = ["chlorine", "pool", "apology", "friendship", "shower"]


CURATED = [
    StoryParams(
        place="community_pool",
        mission="rescue",
        move="cannonball",
        response="apology_rinse_wait",
        instigator_name="Kai",
        instigator_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        adult="mother",
        bond="best_friends",
        trust=7,
    ),
    StoryParams(
        place="swim_center",
        mission="meteor",
        move="whirlpool",
        response="apology_towel",
        instigator_name="Ella",
        instigator_gender="girl",
        friend_name="Noah",
        friend_gender="boy",
        adult="father",
        bond="friends",
        trust=5,
    ),
    StoryParams(
        place="hotel_pool",
        mission="moon",
        move="tidal_kick",
        response="adult_help",
        instigator_name="Ben",
        instigator_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        adult="mother",
        bond="best_friends",
        trust=3,
    ),
    StoryParams(
        place="community_pool",
        mission="rescue",
        move="cannonball",
        response="shrug",
        instigator_name="Leo",
        instigator_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        adult="father",
        bond="friends",
        trust=2,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mission_id in MISSIONS:
            for move_id, move in MOVES.items():
                if hazard_at_risk(place, move):
                    combos.append((place_id, mission_id, move_id))
    return combos


def explain_rejection(place: Place, move: Move) -> str:
    if not place.chlorinated:
        return (
            f"(No story: {place.label} is not a chlorinated pool, so the chlorine sting at the center of this story would make no sense there.)"
        )
    if move.splash_power <= 0 or not move.close_to_face:
        return (
            f"(No story: a {move.label} does not send enough water into a friend's face, so it would not create the hurt-and-repair turn this world needs.)"
        )
    return "(No story: this combination does not create the needed pool mishap.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too weak for a reconciliation story (sense={response.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "reconciled" if is_reconciled(MOVES[params.move], RESPONSES[params.response], params.trust) else "strained"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator_name"]
    b = f["friend_name"]
    mission = f["mission"]
    move = f["move"]
    outcome = f["outcome"]
    if outcome == "reconciled":
        return [
            'Write a short superhero friendship story for a 3-to-5-year-old that includes the word "chlorine".',
            f"Tell a poolside superhero story where {a} hurts {b} by accident with a {move.label}, then truly apologizes and repairs the friendship.",
            f"Write a gentle reconciliation story about two young heroes on {mission.team_name} who learn that careful kindness is stronger than showing off.",
        ]
    return [
        'Write a short superhero friendship story for a 3-to-5-year-old that includes the word "chlorine".',
        f"Tell a poolside story where {a} makes a flashy splash, fails to repair the hurt with {b}, and learns that a team cannot work without kindness.",
        "Write a simple cautionary superhero story where friendship stays hurt because the apology never really happens.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a_name = f["instigator_name"]
    b_name = f["friend_name"]
    mission = f["mission"]
    move = f["move"]
    response = f["response"]
    adult = f["adult"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a_name} and {b_name}, playing superheroes in a pool. A grown-up stayed close enough to help when the game went wrong."
        ),
        (
            "Why did the problem start?",
            f"The problem started when {a_name} did a {move.label} too close to {b_name}. Chlorinated pool water splashed into {b_name}'s eyes, so the game stopped feeling fun."
        ),
        (
            f"Why did {b_name} feel hurt?",
            f"{b_name}'s eyes were stinging from the chlorine, and {b_name} also felt forgotten as a teammate. A superhero game is supposed to protect a partner, not blast them by accident."
        ),
    ]
    if outcome == "reconciled":
        qa.append((
            f"How did {a_name} fix the problem?",
            f"{a_name} {response.qa_text}. That helped with the physical sting and also showed {b_name} that the friendship mattered more than showing off."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the two friends playing together again and being more careful with their splashes. The ending image proves they had reconciled, because the team came back instead of staying apart."
        ))
    else:
        qa.append((
            f"Did {a_name} and {b_name} reconcile?",
            f"No. {a_name} did not make a real repair, so the chlorine sting faded more quickly than the hurt feeling. They finished swim time apart, which showed the friendship was still strained."
        ))
        qa.append((
            "What lesson did the story teach?",
            "The story taught that power and flashy moves are not enough for heroes. Friendship needs apology, listening, and helpful action after a mistake."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"chlorine", "pool", "friendship"}
    response = world.facts["response"]
    if response.apology:
        tags.add("apology")
        tags.add("shower")
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if e.chlorinated:
            bits.append("chlorinated=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, M) :- chlorinated_place(P), splashy_move(M), close_to_face(M).
valid(P, Ms, Mv) :- place(P), mission(Ms), move(Mv), hazard(P, Mv).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
repair_need(N) :- chosen_move(M), splash_power(M, P), trust(T), T <= 3, N = P + 1.
repair_need(N) :- chosen_move(M), splash_power(M, P), trust(T), T > 3, N = P.

reconciled :- chosen_response(R), apology(R), power(R, P), repair_need(N), P >= N.
outcome(reconciled) :- reconciled.
outcome(strained) :- not reconciled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.chlorinated:
            lines.append(asp.fact("chlorinated_place", pid))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for mid, move in MOVES.items():
        lines.append(asp.fact("move", mid))
        if move.splash_power > 0:
            lines.append(asp.fact("splashy_move", mid))
        if move.close_to_face:
            lines.append(asp.fact("close_to_face", mid))
        lines.append(asp.fact("splash_power", mid, move.splash_power))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        if response.apology:
            lines.append(asp.fact("apology", rid))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_move", params.move),
        asp.fact("chosen_response", params.response),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="SMOKE")
        if "chlorine" not in smoke.story.lower():
            raise StoryError("smoke story did not contain required word 'chlorine'")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a superhero pool game, chlorine sting, and friendship repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.move:
        place = PLACES[args.place]
        move = MOVES[args.move]
        if not hazard_at_risk(place, move):
            raise StoryError(explain_rejection(place, move))
    if args.place and not PLACES[args.place].chlorinated:
        move = MOVES[args.move] if args.move else next(v for v in MOVES.values() if v.splash_power > 0)
        raise StoryError(explain_rejection(PLACES[args.place], move))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mission is None or c[1] == args.mission)
        and (args.move is None or c[2] == args.move)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mission, move = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator_name, instigator_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=instigator_name)
    adult = args.adult or rng.choice(["mother", "father"])
    bond = rng.choice(["friends", "best_friends"])
    trust = rng.randint(2, 8)

    return StoryParams(
        place=place,
        mission=mission,
        move=move,
        response=response,
        instigator_name=instigator_name,
        instigator_gender=instigator_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult=adult,
        bond=bond,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.move not in MOVES:
        raise StoryError(f"(Unknown move: {params.move})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = PLACES[params.place]
    move = MOVES[params.move]
    response = RESPONSES[params.response]
    if not hazard_at_risk(place, move):
        raise StoryError(explain_rejection(place, move))

    world = tell(
        place=place,
        mission=MISSIONS[params.mission],
        move=move,
        response=response,
        instigator_name=params.instigator_name,
        instigator_gender=params.instigator_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
        bond=params.bond,
        trust=params.trust,
    )

    return StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator_name).replace("friend", params.friend_name),
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, mission, move) combos:\n")
        for place, mission, move in combos:
            print(f"  {place:15} {mission:8} {move}")
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
            header = f"### {p.instigator_name} & {p.friend_name}: {p.move} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
