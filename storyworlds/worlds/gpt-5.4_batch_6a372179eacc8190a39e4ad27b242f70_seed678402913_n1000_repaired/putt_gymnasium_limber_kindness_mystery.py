#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/putt_gymnasium_limber_kindness_mystery.py
====================================================================

A standalone story world about a small mystery in a gymnasium: during an indoor
putting game, a child's ball goes missing, clues point somewhere strange, and a
kind reveal changes the ending.

The world is built around a few reasonable mystery shapes:
- the ball rolled under folded mats and only a limber helper can reach it
- the ball was tucked into a cone basket during tidy-up by mistake
- a shy younger child borrowed it to practice a putt in secret

The simulation tracks simple physical meters (lost, found, tucked, reached) and
social/emotional memes (worry, curiosity, relief, kindness, trust). Prose comes
from the state and the chosen causal path, not from one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/putt_gymnasium_limber_kindness_mystery.py
    python storyworlds/worlds/gpt-5.4/putt_gymnasium_limber_kindness_mystery.py --cause under_mats
    python storyworlds/worlds/gpt-5.4/putt_gymnasium_limber_kindness_mystery.py --helper custodian
    python storyworlds/worlds/gpt-5.4/putt_gymnasium_limber_kindness_mystery.py --all
    python storyworlds/worlds/gpt-5.4/putt_gymnasium_limber_kindness_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/putt_gymnasium_limber_kindness_mystery.py --verify
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
    limber: bool = False
    kind_hearted: bool = False
    child: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "coach_woman", "custodian_woman"}
        male = {"boy", "man", "father", "coach_man", "custodian_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Ball:
    id: str
    label: str
    phrase: str
    color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    clue: str
    hide_text: str
    reveal_text: str
    question_word: str
    needs_limber: bool = False
    borrowed: bool = False
    suitable_helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperConfig:
    id: str
    type: str
    role: str
    label: str
    kind_hearted: bool = True
    limber: bool = False
    child: bool = False
    suitable_causes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    ball: str
    cause: str
    helper: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    helper_name: str
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


def _r_missing_feels(world: World) -> list[str]:
    out: list[str] = []
    ball = world.entities.get("ball")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not ball or not hero or not friend:
        return out
    if ball.meters["lost"] < THRESHOLD:
        return out
    sig = ("missing_feels", ball.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    out.append("__mystery__")
    return out


def _r_found_relief(world: World) -> list[str]:
    out: list[str] = []
    ball = world.entities.get("ball")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    helper = world.entities.get("helper")
    if not ball or ball.meters["found"] < THRESHOLD:
        return out
    sig = ("found_relief", ball.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in (hero, friend, helper):
        if ent is not None:
            ent.memes["relief"] += 1
            ent.memes["worry"] = 0.0
    out.append("__relief__")
    return out


def _r_kindness_joy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    helper = world.entities.get("helper")
    if not hero or hero.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness_joy", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] += 1
    if friend is not None:
        friend.memes["joy"] += 1
    if helper is not None:
        helper.memes["trust"] += 1
    out.append("__kindness__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_feels", tag="social", apply=_r_missing_feels),
    Rule(name="found_relief", tag="social", apply=_r_found_relief),
    Rule(name="kindness_joy", tag="social", apply=_r_kindness_joy),
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


BALLS = {
    "striped": Ball(
        id="striped",
        label="striped ball",
        phrase="a striped foam golf ball",
        color="striped",
        tags={"golf_ball", "putt"},
    ),
    "gold": Ball(
        id="gold",
        label="gold ball",
        phrase="a little gold practice ball",
        color="gold",
        tags={"golf_ball", "putt"},
    ),
    "star": Ball(
        id="star",
        label="star ball",
        phrase="a soft ball with a blue star on it",
        color="blue-star",
        tags={"golf_ball", "putt"},
    ),
}

CAUSES = {
    "under_mats": Cause(
        id="under_mats",
        clue="A pale line of chalk dust led straight toward the folded mats by the wall.",
        hide_text="The ball had rolled into the narrow shadow under the folded mats.",
        reveal_text="From under the mats came a tiny knock, then the missing ball blinked back into the light.",
        question_word="under",
        needs_limber=True,
        borrowed=False,
        suitable_helpers={"coach", "limber_sibling"},
        tags={"mats", "gymnasium"},
    ),
    "cone_basket": Cause(
        id="cone_basket",
        clue="From the cone basket came a soft thock, as if something round had tapped plastic and gone still.",
        hide_text="During tidy-up, the ball had bounced into the cone basket and disappeared between the orange cones.",
        reveal_text="When the cones were lifted out one by one, the missing ball rolled free with a bright little hop.",
        question_word="inside",
        needs_limber=False,
        borrowed=False,
        suitable_helpers={"coach", "custodian"},
        tags={"cones", "gymnasium"},
    ),
    "borrowed_practice": Cause(
        id="borrowed_practice",
        clue="Behind the long curtain by the stage, someone made the tiniest tap-tap-tap, like a secret putt.",
        hide_text="A shy younger child had borrowed the ball for one quiet practice try and meant to bring it back.",
        reveal_text="Behind the curtain stood a younger child holding the ball in both hands, cheeks pink with worry.",
        question_word="behind",
        needs_limber=False,
        borrowed=True,
        suitable_helpers={"younger_child"},
        tags={"curtain", "practice", "kindness"},
    ),
}

HELPERS = {
    "coach": HelperConfig(
        id="coach",
        type="coach_woman",
        role="coach",
        label="coach",
        kind_hearted=True,
        limber=True,
        child=False,
        suitable_causes={"under_mats", "cone_basket"},
        tags={"coach", "gym"},
    ),
    "custodian": HelperConfig(
        id="custodian",
        type="custodian_man",
        role="custodian",
        label="custodian",
        kind_hearted=True,
        limber=False,
        child=False,
        suitable_causes={"cone_basket"},
        tags={"custodian", "tidy"},
    ),
    "limber_sibling": HelperConfig(
        id="limber_sibling",
        type="girl",
        role="older_sibling",
        label="older sister",
        kind_hearted=True,
        limber=True,
        child=True,
        suitable_causes={"under_mats"},
        tags={"sibling", "limber"},
    ),
    "younger_child": HelperConfig(
        id="younger_child",
        type="boy",
        role="younger_child",
        label="younger child",
        kind_hearted=True,
        limber=False,
        child=True,
        suitable_causes={"borrowed_practice"},
        tags={"child", "practice", "kindness"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Rose", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
ADULT_NAMES = ["Ms. June", "Coach Ana", "Mr. Hale", "Mr. Ben"]
HELPER_CHILD_NAMES = ["Ruby", "Tess", "Owen", "Nico", "Ivy", "Pip"]


def helper_can_solve(cause: Cause, helper: HelperConfig) -> bool:
    if cause.id not in helper.suitable_causes:
        return False
    if cause.needs_limber and not helper.limber:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for ball_id in BALLS:
        for cause_id, cause in CAUSES.items():
            for helper_id, helper in HELPERS.items():
                if helper_can_solve(cause, helper):
                    combos.append((ball_id, cause_id, helper_id))
    return combos


def explain_rejection(cause: Cause, helper: HelperConfig) -> str:
    if cause.id not in helper.suitable_causes:
        return (
            f"(No story: {helper.label} does not fit the clue path for {cause.id}. "
            f"Pick a helper who would reasonably be there for that reveal.)"
        )
    if cause.needs_limber and not helper.limber:
        return (
            f"(No story: {cause.id} hides the ball where only someone limber can reach it. "
            f"Pick a limber helper.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    return "shared_putt" if cause.borrowed else "group_putt"


def introduce(world: World, hero: Entity, friend: Entity, ball_cfg: Ball) -> None:
    world.say(
        f"Rain tapped at the high windows, so the gymnasium had become a tiny putting course. "
        f"{hero.id} and {friend.id} took turns aiming {ball_cfg.phrase} between chalk lines and soft foam blocks."
    )
    world.say(
        f"Each careful putt made a neat tick on the floor, and the empty gymnasium answered with a whispery echo."
    )


def build_tension(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"They were on the very last shot when {hero.id} set the ball down for one more putt toward the cup by the wall."
    )
    world.say(
        f"But when {hero.pronoun()} blinked and reached for it again, the ball was gone."
    )


def mark_missing(world: World, ball: Entity) -> None:
    ball.meters["lost"] += 1
    propagate(world, narrate=False)


def notice_clue(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    world.say(
        f'{hero.id} looked under the score board. {friend.id} checked beside the beanbag bumpers. '
        f'Nobody saw the ball. {cause.clue}'
    )


def helper_enters(world: World, helper: Entity, cause: Cause) -> None:
    if helper.role == "coach":
        world.say(
            f'{helper.id}, the kind {helper.label}, came across the floor with a ring of keys and listened carefully.'
        )
    elif helper.role == "custodian":
        world.say(
            f'{helper.id}, the kind {helper.label}, was stacking chairs nearby and paused when the children told {helper.pronoun("object")} about the mystery.'
        )
    elif helper.role == "older_sibling":
        world.say(
            f'{helper.id}, {world.get("hero").id}\'s limber {helper.label}, had been helping with the foam blocks and came over at once.'
        )
    else:
        world.say(
            f'From behind the curtain, a small figure shifted, still and worried.'
        )
    if cause.needs_limber and helper.limber:
        helper.memes["confidence"] += 1
        world.say(
            f'"Let me try," {helper.id} said. {helper.pronoun().capitalize()} was so limber that {helper.pronoun()} could bend and reach where nobody else could.'
        )


def reveal_hidden(world: World, helper: Entity, cause: Cause, ball: Entity) -> None:
    if cause.id == "under_mats":
        helper.meters["reached"] += 1
        ball.meters["found"] += 1
        ball.attrs["place"] = "under the folded mats"
        world.say(
            f"{helper.pronoun().capitalize()} knelt, slid one arm into the shadow, and felt around until {cause.reveal_text}"
        )
    elif cause.id == "cone_basket":
        helper.meters["sorted"] += 1
        ball.meters["found"] += 1
        ball.attrs["place"] = "inside the cone basket"
        world.say(
            f"{helper.id} tipped the cone basket gently and smiled. {cause.reveal_text}"
        )
    else:
        helper.meters["borrowed"] += 1
        ball.meters["found"] += 1
        ball.attrs["place"] = "behind the curtain"
        world.say(cause.reveal_text)
    propagate(world, narrate=False)


def borrowed_confession(world: World, hero: Entity, helper: Entity, ball_cfg: Ball) -> None:
    helper.memes["worry"] += 1
    helper.memes["shy"] += 1
    world.say(
        f'"I am sorry," {helper.id} whispered. "I only wanted one practice putt. '
        f'My own ball would not roll straight, and yours looked so smooth and brave."'
    )
    world.say(
        f'{hero.id} saw that {helper.id} was not being mean at all. {helper.pronoun().capitalize()} had only been scared to ask.'
    )
    world.facts["confession"] = True
    world.facts["need_help"] = f"{helper.id} wanted practice with a putt"


def physical_reveal(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    world.say(
        f'"So that was the trick," {hero.id} said. The mystery had not been magic after all; it had been a gymnasium hiding place.'
    )
    world.facts["confession"] = False
    world.facts["need_help"] = ""
    if helper.kind_hearted:
        world.say(
            f'{helper.id} laughed softly and made sure the ball was clean before handing it back.'
        )


def kindness_end(world: World, hero: Entity, friend: Entity, helper: Entity, cause: Cause, ball_cfg: Ball) -> None:
    hero.memes["kindness"] += 1
    propagate(world, narrate=False)
    if cause.borrowed:
        world.say(
            f'Instead of snatching the ball, {hero.id} smiled. "{helper.id}, you can take the next putt with us," {hero.pronoun()} said.'
        )
        world.say(
            f'{friend.id} moved the cup a little closer, and together they made an easier lane. Soon the secret tap-tap became happy giggles.'
        )
        world.facts["ending_image"] = (
            f"{hero.id}, {friend.id}, and {helper.id} knelt side by side, sharing the ball for one gentle putt after another"
        )
    else:
        world.say(
            f'"Since we found it, let\'s make this a three-person mystery game," {hero.id} said kindly.'
        )
        if helper.child:
            world.say(
                f'{helper.id} grinned, and {friend.id} drew a new chalk swirl so everyone could have a turn.'
            )
        else:
            world.say(
                f'{helper.id} set one extra cone by the cup, and {friend.id} clapped because the course looked even better than before.'
            )
        world.facts["ending_image"] = (
            f"the missing ball rolling true while everyone in the gymnasium watched it reach the cup together"
        )


def ending(world: World, hero: Entity, friend: Entity, helper: Entity, ball_cfg: Ball) -> None:
    world.say(
        f'The ball clicked into the cup at last. In the big gymnasium, the sound was small, but the kindness around it felt large.'
    )
    world.say(
        f'{world.facts["ending_image"][0].upper()}{world.facts["ending_image"][1:]}.'
    )


def tell(params: StoryParams) -> World:
    if params.ball not in BALLS:
        raise StoryError(f"(Invalid --ball: {params.ball})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid --cause: {params.cause})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid --helper: {params.helper})")

    ball_cfg = BALLS[params.ball]
    cause = CAUSES[params.cause]
    helper_cfg = HELPERS[params.helper]
    if not helper_can_solve(cause, helper_cfg):
        raise StoryError(explain_rejection(cause, helper_cfg))

    world = World()
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        label=params.hero_name,
        role="hero",
        child=True,
        kind_hearted=True,
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_gender,
        label=params.friend_name,
        role="friend",
        child=True,
        kind_hearted=True,
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role=helper_cfg.role,
        child=helper_cfg.child,
        limber=helper_cfg.limber,
        kind_hearted=helper_cfg.kind_hearted,
        tags=set(helper_cfg.tags),
    ))
    ball = world.add(Entity(
        id="ball",
        kind="thing",
        type="ball",
        label=ball_cfg.label,
        phrase=ball_cfg.phrase,
        role="missing_item",
        tags=set(ball_cfg.tags),
        attrs={"place": "by the cup"},
    ))

    introduce(world, hero, friend, ball_cfg)
    build_tension(world, hero, friend)
    mark_missing(world, ball)

    world.para()
    notice_clue(world, hero, friend, cause)
    helper_enters(world, helper, cause)
    reveal_hidden(world, helper, cause, ball)

    world.para()
    if cause.borrowed:
        borrowed_confession(world, hero, helper, ball_cfg)
    else:
        physical_reveal(world, hero, helper, cause)
    kindness_end(world, hero, friend, helper, cause, ball_cfg)

    world.para()
    ending(world, hero, friend, helper, ball_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        ball_cfg=ball_cfg,
        ball=ball,
        cause=cause,
        outcome=outcome_of(params),
        found_place=ball.attrs.get("place", ""),
        setting="gymnasium",
        mystery_started=ball.meters["lost"] >= THRESHOLD,
        kindness_happened=hero.memes["kindness"] >= THRESHOLD,
        helper_was_limber=helper.limber,
        helper_kind=helper.kind_hearted,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    cause = f["cause"]
    ball_cfg = f["ball_cfg"]
    if cause.borrowed:
        return [
            'Write a gentle mystery for a 3-to-5-year-old set in a gymnasium, where a missing ball is part of a kindness lesson. Include the words "putt", "gymnasium", and "limber".',
            f"Tell a child-friendly mystery where {hero.id} loses {ball_cfg.phrase} before a putt, follows a clue in the gymnasium, and discovers that {helper.id} only borrowed it for shy practice.",
            f"Write a warm story with a mystery feeling at first, but end it with kindness when {hero.id} invites someone to join the game instead of getting angry.",
        ]
    return [
        'Write a gentle mystery for a 3-to-5-year-old set in a gymnasium, where a missing ball is found through clues. Include the words "putt", "gymnasium", and "limber".',
        f"Tell a child-friendly mystery where {hero.id} and {friend.id} lose a ball during an indoor putt game, then solve it with help from {helper.id}.",
        f"Write a story that begins with a missing object, keeps a soft mystery mood, and ends with kindness when the children turn the solved puzzle into a shared game.",
    ]


KNOWLEDGE = {
    "putt": [
        (
            "What is a putt?",
            "A putt is a small, gentle hit in golf. You use it to roll the ball carefully toward a hole or cup."
        )
    ],
    "gymnasium": [
        (
            "What is a gymnasium?",
            "A gymnasium is a big indoor room for games, sports, and exercise. Because it is wide and echoey, sounds can bounce around inside it."
        )
    ],
    "limber": [
        (
            "What does limber mean?",
            "Limber means your body can bend and stretch easily. A limber person can often reach places that feel awkward for someone else."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to be gentle and helpful. It can turn a worried moment into a safe and happy one."
        )
    ],
    "mats": [
        (
            "Why do gyms have folded mats?",
            "Folded mats make soft surfaces for exercise and games. Because they are thick and have edges and gaps, small things can sometimes roll under them."
        )
    ],
    "cones": [
        (
            "What are gym cones for?",
            "Gym cones help mark paths, goals, and safe places to move. People also stack them in baskets when they are tidying up."
        )
    ],
    "practice": [
        (
            "Why might someone practice quietly?",
            "Someone might practice quietly because they feel shy and do not want others to see them make mistakes yet. A kind invitation can help them feel brave."
        )
    ],
}
KNOWLEDGE_ORDER = ["putt", "gymnasium", "limber", "kindness", "mats", "cones", "practice"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    cause = f["cause"]
    ball_cfg = f["ball_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} playing an indoor putting game in a gymnasium. {helper.id} also becomes important when the mystery starts to unfold."
        ),
        (
            f"What was the mystery?",
            f"The mystery was that {ball_cfg.phrase} vanished just before {hero.id} tried one last putt. That sudden loss made the gymnasium feel strange and full of clues."
        ),
        (
            "What clue helped them?",
            f"The clue was this: {cause.clue} It gave the children a real direction to search instead of just guessing."
        ),
        (
            f"Where was the missing ball?",
            f"It was {f['found_place']}. That place matched the clue, which is how the mystery was solved."
        ),
    ]
    if cause.borrowed:
        qa.append(
            (
                f"Why did {helper.id} have the ball?",
                f"{helper.id} had borrowed it for one quiet practice putt and meant to bring it back. {helper.pronoun().capitalize()} was shy and worried, not mean, so the real problem was fear rather than trickery."
            )
        )
    else:
        qa.append(
            (
                f"How was the mystery solved?",
                f"{helper.id} helped search the clue's hiding place until the ball came back into sight. The mystery ended because someone looked carefully and kindly instead of giving up."
            )
        )
    qa.append(
        (
            "How did kindness change the ending?",
            f"{hero.id} did not stay upset after the ball was found. Instead, {hero.pronoun()} used kindness to turn the solved mystery into a shared game, so the ending feels brighter than the worried middle."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"putt", "gymnasium", "kindness"}
    if f.get("helper_was_limber"):
        tags.add("limber")
    tags |= set(f["cause"].tags)
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.limber:
            bits.append("limber=True")
        if e.kind_hearted:
            bits.append("kind=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        ball="striped",
        cause="under_mats",
        helper="coach",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper_name="Coach Ana",
    ),
    StoryParams(
        ball="gold",
        cause="cone_basket",
        helper="custodian",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        helper_name="Mr. Hale",
    ),
    StoryParams(
        ball="star",
        cause="under_mats",
        helper="limber_sibling",
        hero_name="Zoe",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        helper_name="Ruby",
    ),
    StoryParams(
        ball="striped",
        cause="borrowed_practice",
        helper="younger_child",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        helper_name="Pip",
    ),
]


ASP_RULES = r"""
needs_limber(under_mats).
borrowed(borrowed_practice).

helper_fits(H, C) :- suitable(H, C), not needs_limber(C).
helper_fits(H, C) :- suitable(H, C), needs_limber(C), limber(H).

valid(B, C, H) :- ball(B), cause(C), helper(H), helper_fits(H, C).

outcome(shared_putt) :- chosen_cause(C), borrowed(C).
outcome(group_putt)  :- chosen_cause(C), not borrowed(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bid in BALLS:
        lines.append(asp.fact("ball", bid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if helper.limber:
            lines.append(asp.fact("limber", hid))
        for cid in sorted(helper.suitable_causes):
            lines.append(asp.fact("suitable", hid, cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("chosen_cause", params.cause)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=False, header="")
    finally:
        sys.stdout = old
    text = buf.getvalue()
    if not text.strip():
        raise StoryError("(Smoke test failed: emit produced no text.)")


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
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: random resolve failed unexpectedly at seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing putting ball in a gymnasium, solved with clues and kindness."
    )
    ap.add_argument("--ball", choices=BALLS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.helper:
        cause = CAUSES[args.cause]
        helper = HELPERS[args.helper]
        if not helper_can_solve(cause, helper):
            raise StoryError(explain_rejection(cause, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.ball is None or combo[0] == args.ball)
        and (args.cause is None or combo[1] == args.cause)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ball_id, cause_id, helper_id = rng.choice(sorted(combos))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)

    helper_cfg = HELPERS[helper_id]
    if args.helper_name:
        helper_name = args.helper_name
    else:
        if helper_cfg.child:
            helper_name = rng.choice([n for n in HELPER_CHILD_NAMES if n not in {hero_name, friend_name}])
        else:
            helper_name = rng.choice(ADULT_NAMES)

    return StoryParams(
        ball=ball_id,
        cause=cause_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ball not in BALLS or params.cause not in CAUSES or params.helper not in HELPERS:
        raise StoryError("(Invalid params: unknown registry key.)")
    cause = CAUSES[params.cause]
    helper = HELPERS[params.helper]
    if not helper_can_solve(cause, helper):
        raise StoryError(explain_rejection(cause, helper))

    world = tell(params)
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
        print(f"{len(combos)} compatible (ball, cause, helper) combos:\n")
        for ball_id, cause_id, helper_id in combos:
            print(f"  {ball_id:8} {cause_id:17} {helper_id}")
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
            header = f"### {p.hero_name}: {p.cause} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
