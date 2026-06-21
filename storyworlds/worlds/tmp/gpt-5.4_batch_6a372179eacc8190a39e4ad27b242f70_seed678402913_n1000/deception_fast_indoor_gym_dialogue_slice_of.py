#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deception_fast_indoor_gym_dialogue_slice_of.py
=========================================================================

A standalone story world about a child in an indoor gym who wants another fast
turn so badly that they try a small deception. The world models lines, turn
markers, a speaking-up friend, and a coach who checks what really happened.

The stories aim for a slice-of-life shape:
- ordinary gym-class setup
- a tempting unfair shortcut
- dialogue and a social turn
- an ending image that proves honesty changed the moment
"""

from __future__ import annotations

import argparse
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
URGE_TO_GO_AGAIN = 6


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "coach_f"}
        male = {"boy", "father", "man", "coach_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"coach_f", "coach_m"}:
            return "coach"
        return self.label or self.type


@dataclass
class Game:
    id: str
    label: str
    lane: str
    gear: str
    move: str
    finish: str
    speed_word: str
    line_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lie:
    id: str
    quote: str
    claim: str
    needs_marker: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Marker:
    id: str
    label: str
    phrase: str
    check_text: str
    proof_text: str
    clarity: int
    verifies_order: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    text: str
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


def _r_line_cut(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    friend = world.entities.get("friend")
    if kid is None or friend is None:
        return out
    if kid.meters["extra_turn_taken"] < THRESHOLD:
        return out
    sig = ("line_cut", "extra_turn_taken")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["fairness"] += 1
    friend.memes["upset"] += 1
    kid.memes["guilt"] += 1
    out.append("__line_cut__")
    return out


def _r_checked(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    if kid is None:
        return out
    if world.get("coach").meters["checked"] < THRESHOLD:
        return out
    if kid.memes["guilt"] < THRESHOLD:
        return out
    sig = ("checked", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["confession_pressure"] += 1
    out.append("__checked__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="line_cut", tag="social", apply=_r_line_cut),
    Rule(name="checked", tag="social", apply=_r_checked),
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


def valid_combo(game: Game, lie: Lie, marker: Marker) -> bool:
    return lie.needs_marker and marker.verifies_order and game.id in GAMES


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def friend_voice(trait: str) -> int:
    return {
        "careful": 4,
        "honest": 4,
        "steady": 3,
        "shy": 1,
        "gentle": 2,
        "bold": 3,
    }.get(trait, 2)


def would_stop_before_run(marker: Marker, trait: str) -> bool:
    return marker.clarity + friend_voice(trait) > URGE_TO_GO_AGAIN


def explain_rejection(lie: Lie, marker: Marker) -> str:
    if not marker.verifies_order:
        return (
            f"(No story: {marker.label} does not actually keep track of turns, so "
            f"the {lie.claim} deception cannot be checked in a grounded way. Pick "
            f"a real turn marker like floor spots or lap clips.)"
        )
    return "(No story: this combination does not make a grounded turn-order problem.)"


def explain_response(rid: str) -> str:
    resp = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try a calmer coaching response like "
        f"{better}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for game_id, game in GAMES.items():
        for lie_id, lie in LIES.items():
            for marker_id, marker in MARKERS.items():
                if valid_combo(game, lie, marker):
                    combos.append((game_id, lie_id, marker_id))
    return combos


def predict_stop(marker: Marker, trait: str) -> dict:
    return {
        "stopped_before_run": would_stop_before_run(marker, trait),
        "clarity": marker.clarity,
        "voice": friend_voice(trait),
    }


def introduce(world: World, kid: Entity, friend: Entity, coach: Entity, game: Game, marker: Marker) -> None:
    kid.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After school, {kid.id} and {friend.id} stood in the indoor gym with the rest "
        f"of their class. Cones made {game.lane}, {game.gear} waited by the wall, "
        f"and {marker.phrase} helped everyone remember whose turn came next."
    )
    world.say(
        f'"Today we keep the line moving and our words honest," {coach.label_word} said. '
        f'"When it is your turn, you go {game.speed_word}. When it is not, you wait."'
    )


def first_run(world: World, kid: Entity, game: Game) -> None:
    kid.meters["fair_turns"] += 1
    kid.memes["pride"] += 1
    world.say(
        f"When {kid.id}'s turn came, {kid.pronoun()} {game.move} and reached {game.finish} "
        f"with cheeks bright and breath coming quick."
    )
    world.say(
        f'"That was so {game.speed_word}!" {kid.id} said, still smiling as {kid.pronoun()} '
        f"returned to the end of the {game.line_word}."
    )


def temptation(world: World, kid: Entity, friend: Entity, game: Game) -> None:
    kid.memes["want_more"] += 1
    kid.memes["urge"] = float(URGE_TO_GO_AGAIN)
    world.say(
        f"Watching the next child get ready made {kid.id} want another turn right away. "
        f"The game felt smooth and fast, and waiting suddenly felt very slow."
    )
    world.say(
        f'"I want to go again already," {kid.id} whispered to {friend.id}.'
    )


def lie_step(world: World, kid: Entity, friend: Entity, lie: Lie) -> None:
    kid.memes["deception"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{kid.id} took a small step out of line and tried a bit of deception. "
        f'{kid.pronoun().capitalize()} said, "{lie.quote}"'
    )
    world.say(
        f'{friend.id} blinked. "Are you sure?" {friend.pronoun()} asked.'
    )


def friend_warn(world: World, kid: Entity, friend: Entity, marker: Marker, coach: Entity, trait: str) -> None:
    pred = predict_stop(marker, trait)
    friend.memes["courage"] += pred["voice"]
    world.facts["predicted_stop"] = pred["stopped_before_run"]
    world.facts["predicted_voice"] = pred["voice"]
    world.facts["predicted_clarity"] = pred["clarity"]
    extra = " very softly" if trait == "shy" else ""
    world.say(
        f'{friend.id} looked at {marker.label}{extra} and said, '
        f'"I think we should check first. {marker.proof_text}, and {coach.label_word} said we wait our turn."'
    )


def averted(world: World, kid: Entity, friend: Entity, coach: Entity, response: Response, marker: Marker, game: Game) -> None:
    coach.meters["checked"] += 1
    propagate(world, narrate=False)
    kid.memes["guilt"] += 1
    kid.memes["honesty"] += 1
    world.say(
        f"{coach.label_word.capitalize()} heard the little voices, {response.text.format(marker=marker.label)}, "
        f"and paused the line for one calm breath."
    )
    world.say(
        f'{kid.id} looked at the floor, then said, "It was not really my turn. I just wanted '
        f'to go {game.speed_word} again."'
    )
    world.say(
        f'"Thank you for telling the truth," {coach.label_word} said. "You can be excited and still be fair."'
    )
    kid.memes["relief"] += 1
    friend.memes["relief"] += 1


def unfair_run(world: World, kid: Entity, friend: Entity, game: Game) -> None:
    kid.meters["extra_turn_taken"] += 1
    kid.meters["distance"] += 1
    kid.memes["thrill"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before anyone could stop the mix-up, {kid.id} dashed into {game.lane} and "
        f"{game.move}. For one quick moment, it felt wonderful to go so {game.speed_word} twice."
    )
    world.say(
        f"But when {kid.pronoun()} reached {game.finish}, the fun thinned out. "
        f"{friend.id} was still by the line, holding a quiet, troubled face."
    )


def checked_and_confessed(world: World, kid: Entity, friend: Entity, coach: Entity, response: Response, marker: Marker) -> None:
    coach.meters["checked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{coach.label_word.capitalize()} looked from {kid.id} to {friend.id} and said, '
        f'"Tell me what happened."'
    )
    world.say(
        f"{coach.label_word.capitalize()} {response.text.format(marker=marker.label)}. "
        f"{marker.check_text}"
    )
    world.say(
        f'{kid.id} swallowed and said, "I said it was my turn, but that was not true."'
    )
    kid.memes["honesty"] += 1
    kid.memes["guilt"] += 1
    friend.memes["relief"] += 1


def repair(world: World, kid: Entity, friend: Entity, coach: Entity) -> None:
    kid.memes["care"] += 1
    world.say(
        f'"Thank you for fixing it," {coach.label_word} said. "{friend.id}, thank you for speaking up kindly."'
    )
    world.say(
        f'{kid.id} turned to {friend.id}. "I am sorry. I wanted one more turn so much that I said '
        f"something unfair.""
    )
    world.say(
        f'"I still want to play with you," {friend.id} answered. "Let\'s just do it the right way."'
    )
    kid.memes["relief"] += 1
    friend.memes["trust"] += 1


def honest_end(world: World, kid: Entity, friend: Entity, coach: Entity, game: Game, outcome: str) -> None:
    kid.meters["fair_turns"] += 1
    kid.memes["joy"] += 1
    friend.memes["joy"] += 1
    ending = (
        f"A few turns later, when {kid.id}'s real turn came back around, {kid.pronoun()} "
        f"{game.move} again, just as {game.speed_word} as before, but this time with a light chest "
        f"instead of a tight one."
    )
    world.say(ending)
    if outcome == "averted":
        world.say(
            f"{friend.id} clapped, and even the squeak of sneakers on the gym floor sounded friendly again."
        )
    else:
        world.say(
            f"{friend.id} clapped from the line, and the room felt easier once the truth had caught up."
        )
    world.say(
        f'At the end, {coach.label_word} stacked the gear by the wall and said, "Fast feet are fun. Honest words make the game work."'
    )


def tell(
    game: Game,
    lie: Lie,
    marker: Marker,
    response: Response,
    *,
    kid_name: str,
    kid_gender: str,
    friend_name: str,
    friend_gender: str,
    coach_gender: str,
    friend_trait: str,
) -> World:
    world = World()
    kid = world.add(Entity(id="kid", kind="character", type=kid_gender, label=kid_name, role="kid", traits=["eager"]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=[friend_trait]))
    coach_type = "coach_f" if coach_gender == "female" else "coach_m"
    coach = world.add(Entity(id="coach", kind="character", type=coach_type, label="the coach", role="coach"))
    world.add(Entity(id="marker", kind="thing", type="marker", label=marker.label, tags=set(marker.tags)))

    introduce(world, kid, friend, coach, game, marker)
    first_run(world, kid, game)

    world.para()
    temptation(world, kid, friend, game)
    lie_step(world, kid, friend, lie)
    friend_warn(world, kid, friend, marker, coach, friend_trait)

    stopped = would_stop_before_run(marker, friend_trait)
    world.facts["stopped_before_run"] = stopped

    world.para()
    if stopped:
        averted(world, kid, friend, coach, response, marker, game)
        outcome = "averted"
    else:
        unfair_run(world, kid, friend, game)
        world.para()
        checked_and_confessed(world, kid, friend, coach, response, marker)
        repair(world, kid, friend, coach)
        outcome = "confessed_after_extra_turn"

    world.para()
    honest_end(world, kid, friend, coach, game, outcome)

    world.facts.update(
        kid=kid,
        friend=friend,
        coach=coach,
        game=game,
        lie=lie,
        marker_cfg=marker,
        response=response,
        friend_trait=friend_trait,
        outcome=outcome,
        extra_turn=kid.meters["extra_turn_taken"] >= THRESHOLD,
        confessed=kid.memes["honesty"] >= THRESHOLD,
    )
    return world


GAMES = {
    "cone_dash": Game(
        id="cone_dash",
        label="cone dash",
        lane="a zigzag lane of orange cones",
        gear="soft beanbags",
        move="ran around the cones and back",
        finish="the blue mat",
        speed_word="fast",
        line_word="line",
        tags={"gym", "running"},
    ),
    "scooter_relay": Game(
        id="scooter_relay",
        label="scooter relay",
        lane="two shiny relay lanes",
        gear="scooter boards",
        move="pushed off, coasted past the cones, and steered back",
        finish="the foam wall",
        speed_word="fast",
        line_word="relay line",
        tags={"gym", "scooter"},
    ),
    "hula_hop_dash": Game(
        id="hula_hop_dash",
        label="hula-hoop dash",
        lane="a row of hula hoops like stepping islands",
        gear="bright hoops",
        move="hopped through the hoops and tagged the wall",
        finish="the climbing-rope corner",
        speed_word="fast",
        line_word="line",
        tags={"gym", "hopping"},
    ),
}

LIES = {
    "my_turn": Lie(
        id="my_turn",
        quote="Coach said it was my turn again.",
        claim="claiming an extra turn",
        tags={"deception", "turns"},
    ),
    "already_waited": Lie(
        id="already_waited",
        quote="I already waited longer than everybody else.",
        claim="pretending the waiting order is different",
        tags={"deception", "waiting"},
    ),
    "holding_place": Lie(
        id="holding_place",
        quote="I was just holding this place in line the whole time.",
        claim="pretending to have kept a place in line",
        tags={"deception", "line"},
    ),
}

MARKERS = {
    "floor_spots": Marker(
        id="floor_spots",
        label="the colored floor spots",
        phrase="colored floor spots on the wood floor",
        check_text="The empty spot at the front showed whose turn really came next.",
        proof_text="the front spot is still empty",
        clarity=3,
        verifies_order=True,
        tags={"floor_spots", "turn_order"},
    ),
    "lap_clips": Marker(
        id="lap_clips",
        label="the clip board by the cones",
        phrase="small lap clips hanging on a board by the cones",
        check_text="Only one clip had been moved, so the board showed exactly who had already gone.",
        proof_text="the next clip is still waiting on the board",
        clarity=3,
        verifies_order=True,
        tags={"lap_clips", "turn_order"},
    ),
    "wristbands": Marker(
        id="wristbands",
        label="the turn wristbands",
        phrase="soft turn wristbands in two little baskets",
        check_text="The child with the next wristband had not gone yet, and that made the order clear enough.",
        proof_text="the next wristband is still in the basket",
        clarity=2,
        verifies_order=True,
        tags={"wristbands", "turn_order"},
    ),
    "echo_noise": Marker(
        id="echo_noise",
        label="the noisy gym echoes",
        phrase="only the noisy gym echoes and a lot of guesses",
        check_text="The sound in the room did not show who went next at all.",
        proof_text="noise cannot hold a place in line",
        clarity=0,
        verifies_order=False,
        tags={"noise"},
    ),
}

RESPONSES = {
    "check_marker": Response(
        id="check_marker",
        sense=3,
        text="walked over to {marker} and checked it before deciding anything",
        qa_text="checked the turn marker calmly and used it to reset the line fairly",
        tags={"coach", "fairness"},
    ),
    "pause_and_reset": Response(
        id="pause_and_reset",
        sense=3,
        text="raised one hand, paused the game, and looked at {marker} with the children",
        qa_text="paused the game and reset the line with the children after checking the marker",
        tags={"coach", "fairness"},
    ),
    "public_scold": Response(
        id="public_scold",
        sense=1,
        text="called out the child in front of everyone without checking {marker}",
        qa_text="scolded loudly without checking the turn order first",
        tags={"scold"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Noah", "Finn", "Max", "Eli", "Theo"]
FRIEND_TRAITS = ["careful", "honest", "steady", "shy", "gentle", "bold"]


@dataclass
class StoryParams:
    game: str
    lie: str
    marker: str
    response: str
    kid_name: str
    kid_gender: str
    friend_name: str
    friend_gender: str
    coach_gender: str
    friend_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "gym": [
        (
            "What is an indoor gym?",
            "An indoor gym is a big room for moving games and exercise. It often has mats, cones, and open space for running and jumping.",
        )
    ],
    "running": [
        (
            "Why do classes take turns in running games?",
            "Taking turns keeps a running game fair and safe. It also gives each child room to move without bumping into someone else.",
        )
    ],
    "deception": [
        (
            "What is deception?",
            "Deception means trying to make someone believe something that is not true. It can seem helpful for a moment, but it usually makes trust wobble.",
        )
    ],
    "turn_order": [
        (
            "Why do turn markers help in a game?",
            "Turn markers show whose turn comes next, so children do not have to guess. That makes the game calmer and more fair.",
        )
    ],
    "fairness": [
        (
            "Why is fairness important in a game?",
            "Fairness means everyone follows the same rules and gets a real turn. When a game is fair, people can relax and enjoy playing together.",
        )
    ],
    "coach": [
        (
            "What can a coach do when children disagree about turns?",
            "A coach can slow the moment down, listen, and check what really happened. Calm checking helps children learn without the game turning mean.",
        )
    ],
}
KNOWLEDGE_ORDER = ["gym", "running", "deception", "turn_order", "fairness", "coach"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    friend = f["friend"]
    game = f["game"]
    lie = f["lie"]
    marker = f["marker_cfg"]
    return [
        (
            f'Write a slice-of-life story for a 3-to-5-year-old set in an indoor gym. '
            f'Include dialogue, the words "deception" and "fast", and a small unfair moment about turns.'
        ),
        (
            f"Tell a gentle gym-class story where {kid.label} wants another {game.label} turn so badly "
            f"that {kid.pronoun()} tries {lie.claim}, but {friend.label} notices {marker.label} and helps the truth come out."
        ),
        (
            f"Write a story with spoken lines, a calm coach, and a child learning that being fast is not the same as being fair."
        ),
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    friend = f["friend"]
    coach = f["coach"]
    game = f["game"]
    lie = f["lie"]
    marker = f["marker_cfg"]
    response = f["response"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid.label} and {friend.label} in an indoor gym, with a coach watching the game. "
            f"The story follows one tempting little mistake during {game.label}.",
        ),
        (
            f"Why did {kid.label} try deception?",
            f"{kid.label} had just had a fun turn and wanted to go again right away because moving fast felt exciting. "
            f"That strong wish made waiting feel hard, so {kid.pronoun()} tried a deceptive shortcut instead of standing in line.",
        ),
        (
            f"What was the deception?",
            f"The deception was {lie.claim}: {kid.label} said, \"{lie.quote}\" "
            f"The lie was meant to change the turn order without really earning the next turn.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"How was the problem stopped before anyone lost a turn?",
                f"{friend.label} spoke up kindly and pointed to {marker.label}, which made the class pause and check. "
                f"Because the marker was clear enough, {kid.label} admitted the truth before running again.",
            )
        )
    else:
        qa.append(
            (
                f"Did {kid.label} get an extra turn?",
                f"Yes. {kid.label} slipped into the lane and took one extra turn before the adults fully sorted it out. "
                f"After that, {coach.label_word} {response.qa_text}, and the truth came out anyway.",
            )
        )
    qa.append(
        (
            f"How did the coach handle it?",
            f"{coach.label_word.capitalize()} did not guess or explode. "
            f"{coach.label_word.capitalize()} {response.qa_text}, which turned the argument into a calm, fair fix.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {kid.label} taking a real turn honestly and still moving fast. "
            f"The last image shows that the game felt lighter once fairness and truth were back in place.",
        )
    )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gym", "deception"} | set(f["game"].tags) | set(f["marker_cfg"].tags) | set(f["response"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        game="cone_dash",
        lie="my_turn",
        marker="floor_spots",
        response="check_marker",
        kid_name="Mia",
        kid_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        coach_gender="female",
        friend_trait="careful",
    ),
    StoryParams(
        game="scooter_relay",
        lie="holding_place",
        marker="wristbands",
        response="pause_and_reset",
        kid_name="Leo",
        kid_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        coach_gender="male",
        friend_trait="gentle",
    ),
    StoryParams(
        game="hula_hop_dash",
        lie="already_waited",
        marker="lap_clips",
        response="check_marker",
        kid_name="Ava",
        kid_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        coach_gender="female",
        friend_trait="honest",
    ),
]


def outcome_of(params: StoryParams) -> str:
    marker = MARKERS[params.marker]
    return "averted" if would_stop_before_run(marker, params.friend_trait) else "confessed_after_extra_turn"


ASP_RULES = r"""
valid(G, L, M) :- game(G), lie(L), marker(M), verifies_order(M), needs_marker(L).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.

voice(4) :- trait(careful).
voice(4) :- trait(honest).
voice(3) :- trait(steady).
voice(1) :- trait(shy).
voice(2) :- trait(gentle).
voice(3) :- trait(bold).

stopped_before_run :- chosen_marker(M), clarity(M, C), voice(V), urge(U), C + V > U.
outcome(averted) :- stopped_before_run.
outcome(confessed_after_extra_turn) :- not stopped_before_run.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for game_id in GAMES:
        lines.append(asp.fact("game", game_id))
    for lie_id, lie in LIES.items():
        lines.append(asp.fact("lie", lie_id))
        if lie.needs_marker:
            lines.append(asp.fact("needs_marker", lie_id))
    for marker_id, marker in MARKERS.items():
        lines.append(asp.fact("marker", marker_id))
        lines.append(asp.fact("clarity", marker_id, marker.clarity))
        if marker.verifies_order:
            lines.append(asp.fact("verifies_order", marker_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("urge", URGE_TO_GO_AGAIN))
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

    extra = "\n".join(
        [
            asp.fact("chosen_marker", params.marker),
            asp.fact("trait", params.friend_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a gym-class child tries a small deception to get another fast turn."
    )
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--lie", choices=LIES)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--coach-gender", choices=["female", "male"])
    ap.add_argument("--friend-trait", choices=FRIEND_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.marker and not MARKERS[args.marker].verifies_order:
        lie = LIES[args.lie] if args.lie else next(iter(LIES.values()))
        raise StoryError(explain_rejection(lie, MARKERS[args.marker]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.game is None or combo[0] == args.game)
        and (args.lie is None or combo[1] == args.lie)
        and (args.marker is None or combo[2] == args.marker)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    game_id, lie_id, marker_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    coach_gender = args.coach_gender or rng.choice(["female", "male"])
    kid_name = pick_name(rng, kid_gender)
    friend_name = pick_name(rng, friend_gender, avoid=kid_name)
    friend_trait = args.friend_trait or rng.choice(FRIEND_TRAITS)

    return StoryParams(
        game=game_id,
        lie=lie_id,
        marker=marker_id,
        response=response_id,
        kid_name=kid_name,
        kid_gender=kid_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        coach_gender=coach_gender,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        game = GAMES[params.game]
        lie = LIES[params.lie]
        marker = MARKERS[params.marker]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if not valid_combo(game, lie, marker):
        raise StoryError(explain_rejection(lie, marker))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        game=game,
        lie=lie,
        marker=marker,
        response=response,
        kid_name=params.kid_name,
        kid_gender=params.kid_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        coach_gender=params.coach_gender,
        friend_trait=params.friend_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sensible = {r.id for r in sensible_responses()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible responses match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            ns = build_parser().parse_args([])
            cases.append(resolve_params(ns, random.Random(seed)))
        except StoryError:
            continue

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
            raise StoryError("empty story")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke, trace=False, qa=True, header="SMOKE")
        finally:
            sys.stdout = old_stdout
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


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
        print(f"{len(combos)} compatible (game, lie, marker) combos:\n")
        for game_id, lie_id, marker_id in combos:
            print(f"  {game_id:14} {lie_id:15} {marker_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.kid_name} and {p.friend_name}: {p.game}, {p.lie}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
