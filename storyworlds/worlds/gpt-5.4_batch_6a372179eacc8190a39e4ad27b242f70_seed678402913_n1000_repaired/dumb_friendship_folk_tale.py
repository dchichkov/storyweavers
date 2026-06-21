#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dumb_friendship_folk_tale.py
=======================================================

A small folk-tale story world about friendship, foolish shortcuts, and the kind
of friend who helps without walking away. The seed word "dumb" appears inside
the stories as a child-level line about a bad idea, then the tale turns toward a
gentler lesson: a dumb plan is not the same thing as a dumb friend.

The domain shape:
    two animal friends set out with a gift to share;
    a path is blocked by a small obstacle;
    one friend is tempted by a foolish shortcut;
    the other warns, predicts trouble, and either talks the friend out of it
    or later helps with the proper tool;
    they end with either the original gift or a new shared supper that proves
    the friendship held.

Run it
------
    python storyworlds/worlds/gpt-5.4/dumb_friendship_folk_tale.py
    python storyworlds/worlds/gpt-5.4/dumb_friendship_folk_tale.py --obstacle brook
    python storyworlds/worlds/gpt-5.4/dumb_friendship_folk_tale.py --response jump_harder
    python storyworlds/worlds/gpt-5.4/dumb_friendship_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/dumb_friendship_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/dumb_friendship_folk_tale.py --verify
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
# from this nested directory (storyworlds/worlds/gpt-5.4/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
TRUST_TO_LISTEN = 7
CALMING_TRAITS = {"steady", "gentle", "kind", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "goose", "doe"}
        male = {"boy", "fox", "badger", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    foolish_idea: str
    warning: str
    trouble: str
    severity: int
    damage: str
    proper_tool: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    obstacles: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    gift = world.entities.get("gift")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if gift is None or hero is None or friend is None:
        return out
    if gift.meters["damaged"] < THRESHOLD:
        return out
    sig = ("worry", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sorrow"] += 1
    friend.memes["concern"] += 1
    out.append("__damage__")
    return out


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return out
    if hero.meters["stuck"] < THRESHOLD:
        return out
    sig = ("stuck", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    friend.memes["concern"] += 1
    out.append("__stuck__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="stuck", tag="physical", apply=_r_stuck),
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


GIFTS = {
    "cake": Gift(
        id="cake",
        label="honey cake",
        phrase="a round honey cake wrapped in a blue cloth",
        tags={"cake", "sharing"},
    ),
    "berries": Gift(
        id="berries",
        label="berry basket",
        phrase="a small basket full of blackberries",
        tags={"berries", "sharing"},
    ),
    "garland": Gift(
        id="garland",
        label="flower garland",
        phrase="a flower garland braided from clover and daisies",
        tags={"flowers", "sharing"},
    ),
}

OBSTACLES = {
    "brook": Obstacle(
        id="brook",
        label="brook",
        scene="a bright brook chattering over round stones",
        foolish_idea="jump from one slick stone to the next with the gift tucked under one arm",
        warning="the stones are wet and the current likes to tug at hurried feet",
        trouble="The first stone held, the second stone rolled, and in one blink the gift splashed low and the traveler sat in the cold water with a great surprised gasp.",
        severity=2,
        damage="wet",
        proper_tool="a flat board",
        tags={"brook", "water"},
    ),
    "hedge": Obstacle(
        id="hedge",
        label="thorn hedge",
        scene="a thorn hedge with a little hidden gate buried in green leaves",
        foolish_idea="push straight through the hedge before the thorns can catch",
        warning="thorns are quick, and gifts are slower than pride",
        trouble="The hedge clutched cloth and ribbon at once. Leaves shook, thorns scratched, and the gift came out bent and ragged while the traveler stood red-faced on the wrong side.",
        severity=2,
        damage="torn",
        proper_tool="the hidden gate",
        tags={"hedge", "thorns"},
    ),
    "ditch": Obstacle(
        id="ditch",
        label="muddy ditch",
        scene="a muddy ditch where the earth looked firm but sighed under every step",
        foolish_idea="hop across before the mud can notice",
        warning="mud notices everything, especially quick feet",
        trouble="The bank crumbled with a soft gulp. One leg sank, then the other, and the gift tipped forward into brown splashes while the traveler clung to a tuft of grass.",
        severity=3,
        damage="muddy",
        proper_tool="a wheelbarrow plank",
        tags={"mud", "ditch"},
    ),
}

RESPONSES = {
    "board": Response(
        id="board",
        sense=3,
        power=3,
        obstacles={"brook", "ditch"},
        text="ran back to the willow shed, fetched a flat board, and laid it down so the path turned steady under their feet",
        fail="fetched a flat board, but the mud and water had already made such a mess that the gift could not be kept whole",
        qa_text="brought a flat board and made a steady path",
        tags={"board", "bridge"},
    ),
    "gate": Response(
        id="gate",
        sense=3,
        power=3,
        obstacles={"hedge"},
        text="parted the leaves, found the hidden latch, and opened the little gate that had been there all along",
        fail="found the hidden gate, but by then the thorns had already spoiled the gift beyond mending",
        qa_text="opened the hidden gate in the hedge",
        tags={"gate", "hedge"},
    ),
    "wagon": Response(
        id="wagon",
        sense=2,
        power=2,
        obstacles={"brook", "ditch", "hedge"},
        text="borrowed the miller's little wagon and took the long, careful path around the obstacle",
        fail="borrowed the miller's little wagon, but the delay had already ruined the gift they meant to share",
        qa_text="borrowed a little wagon and took the long careful way around",
        tags={"wagon", "careful"},
    ),
    "jump_harder": Response(
        id="jump_harder",
        sense=1,
        power=1,
        obstacles={"brook", "ditch"},
        text="shouted for a bigger jump",
        fail="called for a bigger jump, which was no help at all",
        qa_text="tried a bigger jump",
        tags={"foolish"},
    ),
}

NAMES = [
    ("Pip", "fox"),
    ("Mara", "hen"),
    ("Tavi", "badger"),
    ("Lina", "goose"),
    ("Oren", "frog"),
    ("Nell", "doe"),
]

TRAITS = ["steady", "gentle", "kind", "patient", "brisk", "proud", "hasty"]
SNACKS = [
    "two warm rolls with butter",
    "half a wheel of cheese and a red apple",
    "a small jar of jam and a loaf of brown bread",
    "three sweet plums from the windowsill",
]

KNOWLEDGE = {
    "brook": [(
        "Why can wet stones be dangerous?",
        "Wet stones can be slippery, so feet slide off them more easily. That is why people cross water slowly and look for a steady path."
    )],
    "water": [(
        "What happens when bread or cake falls in water?",
        "Water soaks into bread or cake and makes it heavy and soggy. That can spoil the treat you wanted to share."
    )],
    "hedge": [(
        "What is a hedge?",
        "A hedge is a row of bushes or shrubs growing close together. Some hedges have thorns, so it is better to use a gate than push through."
    )],
    "thorns": [(
        "Why do thorns tear things?",
        "Thorns are hard, sharp points on some plants. They catch cloth, ribbons, and skin very quickly."
    )],
    "mud": [(
        "Why does mud make walking hard?",
        "Mud is soft, wet earth that can slide and suck at your shoes. That makes quick steps less safe."
    )],
    "ditch": [(
        "What is a ditch?",
        "A ditch is a narrow hollow in the ground, often holding water or mud. It can look easy to cross when it is not."
    )],
    "board": [(
        "How can a board help you cross a small gap?",
        "A flat board can make a little bridge over a gap or muddy place. It works best when it is set down carefully and does not wobble."
    )],
    "gate": [(
        "Why is a gate better than pushing through thorns?",
        "A gate gives you a safe opening to pass through. It keeps you from snagging your clothes or whatever you are carrying."
    )],
    "wagon": [(
        "Why is taking the long way sometimes wise?",
        "The long way can be safer when the short way is risky. Arriving slowly is better than ruining yourself or your things."
    )],
    "sharing": [(
        "Why does sharing food show friendship?",
        "Sharing food says, 'I am glad you are with me.' It turns one small meal into a warm moment between friends."
    )],
}
KNOWLEDGE_ORDER = [
    "brook", "water", "hedge", "thorns", "mud", "ditch", "board", "gate", "wagon", "sharing"
]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_pair(obstacle_id: str, response_id: str) -> bool:
    obstacle = OBSTACLES[obstacle_id]
    response = RESPONSES[response_id]
    return response.sense >= SENSE_MIN and obstacle.id in response.obstacles


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for gift_id in GIFTS:
        for obstacle_id in OBSTACLES:
            for response_id in RESPONSES:
                if valid_pair(obstacle_id, response_id):
                    out.append((gift_id, obstacle_id, response_id))
    return out


@dataclass
class StoryParams:
    gift: str
    obstacle: str
    response: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    trust: int
    delay: int = 0
    shared_snack: str = ""
    seed: Optional[int] = None


def friendship_holds(trust: int, trait: str) -> bool:
    return trust >= TRUST_TO_LISTEN and trait in CALMING_TRAITS


def danger_of(obstacle: Obstacle, delay: int) -> int:
    return obstacle.severity + delay


def is_saved(response: Response, obstacle: Obstacle, delay: int) -> bool:
    return response.power >= danger_of(obstacle, delay)


def outcome_of(params: StoryParams) -> str:
    if friendship_holds(params.trust, params.trait):
        return "averted"
    if is_saved(RESPONSES[params.response], OBSTACLES[params.obstacle], params.delay):
        return "saved"
    return "shared_only"


def predict_trouble(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    attempt_bad_crossing(sim, obstacle, narrate=False)
    hero = sim.get("hero")
    gift = sim.get("gift")
    return {
        "stuck": hero.meters["stuck"] >= THRESHOLD,
        "damaged": gift.meters["damaged"] >= THRESHOLD,
        "damage_kind": obstacle.damage,
    }


def opening(world: World, hero: Entity, friend: Entity, gift: Gift) -> None:
    hero.memes["joy"] += 1
    friend.memes["love"] += 1
    world.say(
        f"Long ago, when even the lanes between cottages seemed to know the names of friends, "
        f"{hero.id} the {hero.type} set out with {gift.phrase} for {friend.id} the {friend.type}."
    )
    world.say(
        f"{hero.id} had said, \"What tastes sweetest is the part we share,\" and so the little gift was meant for two."
    )


def meeting(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"Before the sun leaned west, {hero.id} met {friend.id} by {obstacle.scene}."
    )
    world.say(
        f"They meant to cross together and eat beneath the old fig tree on the far side."
    )


def temptation(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"But when {hero.id} saw the way blocked, {hero.pronoun()} lifted {hero.pronoun('possessive')} chin and said, "
        f"\"I know a quicker way. I can {obstacle.foolish_idea}.\""
    )


def warning(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    pred = predict_trouble(world, obstacle)
    world.facts["predicted"] = pred
    friend.memes["care"] += 1
    extra = " It is a dumb idea, not because you are dumb, but because hurry makes poor plans." \
        if pred["damaged"] or pred["stuck"] else ""
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head. "
        f"\"No, friend. {obstacle.warning}.{extra}\""
    )


def back_down(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, response: Response) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} looked again, this time with cooler eyes. "
        f"\"Then I will not race the path,\" {hero.pronoun()} said."
    )
    if response.id == "board":
        world.say(
            f"Together they found {obstacle.proper_tool}, set it down with both paws, and crossed side by side."
        )
    elif response.id == "gate":
        world.say(
            f"Together they searched the leaves until they found {obstacle.proper_tool}, and through it they passed without a scratch."
        )
    else:
        world.say(
            f"Together they chose the longer road, and before long the troublesome place was behind them."
        )


def attempt_bad_crossing(world: World, obstacle: Obstacle, narrate: bool = True) -> None:
    hero = world.get("hero")
    gift = world.get("gift")
    hero.memes["defiance"] += 1
    if obstacle.id == "brook":
        hero.meters["wet"] += 1
        hero.meters["stuck"] += 1
        gift.meters["wet"] += 1
    elif obstacle.id == "hedge":
        gift.meters["torn"] += 1
    elif obstacle.id == "ditch":
        hero.meters["muddy"] += 1
        hero.meters["stuck"] += 1
        gift.meters["muddy"] += 1
    gift.meters["damaged"] += 1
    propagate(world, narrate=narrate)


def mishap(world: World, hero: Entity, obstacle: Obstacle) -> None:
    attempt_bad_crossing(world, obstacle, narrate=False)
    world.say(
        f"But pride runs faster than wisdom only for a moment. {obstacle.trouble}"
    )
    if hero.meters["stuck"] >= THRESHOLD:
        world.say(
            f"At once {hero.id}'s brave face crumpled, for being bold did not help {hero.pronoun('object')} one bit."
        )


def rescue(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, response: Response) -> None:
    hero.meters["stuck"] = 0.0
    hero.memes["fear"] = 0.0
    gift = world.get("gift")
    world.say(
        f"{friend.id} did not laugh. {friend.pronoun().capitalize()} {response.text}."
    )
    gift.meters["saved"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["love"] += 1
    world.say(
        f"Soon the way was passable again, and {friend.id} helped {hero.id} gather the gift with careful hands."
    )


def rescue_fail(world: World, hero: Entity, friend: Entity, response: Response) -> None:
    hero.meters["stuck"] = 0.0
    hero.memes["fear"] = 0.0
    world.say(
        f"{friend.id} hurried to help and {response.fail}."
    )
    world.say(
        f"They could save {hero.id}, but not the little offering {hero.pronoun()} had meant to bring."
    )


def feast_with_gift(world: World, hero: Entity, friend: Entity, gift: Gift) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Under the fig tree they sat knee to knee and shared the {gift.label} until even the crumbs seemed merry."
    )
    world.say(
        f"From that day on, {hero.id} remembered that a wise friend is worth more than a quick boast."
    )


def feast_without_gift(world: World, hero: Entity, friend: Entity, snack: str) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"Then {friend.id} opened {friend.pronoun('possessive')} satchel and drew out {snack}."
    )
    world.say(
        f"\"A lost gift is sad,\" {friend.pronoun()} said, \"but friendship is not lost so quickly.\""
    )
    world.say(
        f"So they ate what there was together, and the supper tasted better for the kindness in it."
    )


def closing(world: World, hero: Entity, friend: Entity, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"When the village lamps winked on, the two friends walked home slowly, and neither one hurried the other again."
        )
    elif outcome == "saved":
        world.say(
            f"When the evening star came out, {hero.id} was still damp or dusty, but {hero.pronoun()} was smiling, for friendship had carried more than the gift."
        )
    else:
        world.say(
            f"And old people later said that the meal was small, but the friendship at it was large."
        )


def tell(
    gift_cfg: Gift,
    obstacle: Obstacle,
    response: Response,
    hero_name: str,
    hero_type: str,
    friend_name: str,
    friend_type: str,
    trait: str,
    trust: int,
    delay: int,
    shared_snack: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=["hasty"],
        attrs={"display": hero_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_type,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        traits=[trait],
        attrs={"display": friend_name},
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
    ))
    hero.attrs["trust"] = trust
    friend.attrs["trait"] = trait

    opening(world, hero, friend, gift_cfg)
    meeting(world, hero, friend, obstacle)

    world.para()
    temptation(world, hero, obstacle)
    warning(world, hero, friend, obstacle)

    outcome = "averted" if friendship_holds(trust, trait) else ""
    if outcome == "averted":
        back_down(world, hero, friend, obstacle, response)
        world.para()
        feast_with_gift(world, hero, friend, gift_cfg)
    else:
        world.say(
            f"Yet {hero.id} was feeling too proud to listen. \"I can do it,\" {hero.pronoun()} said, and off {hero.pronoun()} went."
        )
        world.para()
        mishap(world, hero, obstacle)
        severity = danger_of(obstacle, delay)
        gift.meters["severity"] = float(severity)
        saved = is_saved(response, obstacle, delay)
        world.para()
        if saved:
            rescue(world, hero, friend, obstacle, response)
            world.para()
            feast_with_gift(world, hero, friend, gift_cfg)
            outcome = "saved"
        else:
            rescue_fail(world, hero, friend, response)
            world.para()
            feast_without_gift(world, hero, friend, shared_snack)
            outcome = "shared_only"

    closing(world, hero, friend, outcome)
    world.facts.update(
        hero=hero,
        friend=friend,
        gift_cfg=gift_cfg,
        obstacle=obstacle,
        response=response,
        trust=trust,
        trait=trait,
        delay=delay,
        snack=shared_snack,
        outcome=outcome,
        gift_damaged=gift.meters["damaged"] >= THRESHOLD,
        gift_saved=gift.meters["saved"] >= THRESHOLD,
    )
    return world


def pair_label(hero: Entity, friend: Entity) -> str:
    return f"{hero.label_word} and {friend.label_word}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    gift = f["gift_cfg"]
    obstacle = f["obstacle"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short folk tale for a young child that includes the word "dumb" and centers friendship.',
            f"Tell a folk tale where {hero.label_word} wants to carry {gift.phrase} across a {obstacle.label}, but {friend.label_word} gently calls the shortcut a dumb idea and the two friends choose the wiser path together.",
            f"Write a simple story in folk-tale style where a hasty friend listens to a patient one, and the ending image shows them sharing food under a tree.",
        ]
    if outcome == "saved":
        return [
            'Write a short folk tale for a young child that includes the word "dumb" and centers friendship.',
            f"Tell a friendship tale where {hero.label_word} ignores a warning, gets into trouble at a {obstacle.label}, and {friend.label_word} helps with the proper tool so the gift can still be shared.",
            f"Write a folk tale in which a foolish shortcut causes a mishap, but a kind friend rescues both the day and the friendship.",
        ]
    return [
        'Write a short folk tale for a young child that includes the word "dumb" and centers friendship.',
        f"Tell a friendship folk tale where {hero.label_word} ruins a gift by taking a foolish shortcut at a {obstacle.label}, but {friend.label_word} shares {friend.pronoun('possessive')} own food instead.",
        f"Write a gentle moral tale in which the gift is lost, yet the friends still end by eating together and valuing friendship over pride.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    gift = f["gift_cfg"]
    obstacle = f["obstacle"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.label_word} and {friend.label_word}. One carried {gift.phrase}, and the other tried to help when the path turned troublesome."
        ),
        (
            f"What were they trying to do?",
            f"They were trying to cross the {obstacle.label} together and share the {gift.label} under the fig tree. The gift mattered because it was meant as a sign of friendship, not just as food."
        ),
        (
            f"Why did {friend.label_word} call the shortcut a dumb idea?",
            f"{friend.label_word} could see that {obstacle.warning}. In the world of the story, the danger was real: the shortcut could leave the gift damaged or leave {hero.label_word} stuck."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What changed {hero.label_word}'s mind?",
            f"{hero.label_word} listened because {friend.label_word} spoke calmly and like a true friend. The warning was about the plan, not an insult, so {hero.pronoun().capitalize()} cooled down and chose the safer way."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with both friends crossing safely and sharing the {gift.label} under the fig tree. The ending shows that listening preserved both the gift and the friendship."
        ))
    elif outcome == "saved":
        qa.append((
            f"How did {friend.label_word} help after the mishap?",
            f"{friend.label_word} {response.qa_text}. That proper help turned a bad moment around before the gift was lost for good."
        ))
        qa.append((
            f"What did {hero.label_word} learn?",
            f"{hero.label_word} learned that quick pride is weaker than good advice. The rescue proved that a wise friend can carry you farther than a boast can."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the friends still sharing the {gift.label}. The final picture is happy because help came in time and the friendship grew stronger."
        ))
    else:
        qa.append((
            f"Was the gift saved?",
            f"No. {friend.label_word} managed to help {hero.label_word}, but the little gift was already spoiled. The loss happened because the foolish shortcut and the delay gave the damage too much time."
        ))
        qa.append((
            f"What did {friend.label_word} do instead?",
            f"{friend.pronoun().capitalize()} shared {f['snack']} from {friend.pronoun('possessive')} own satchel. That second kindness matters because it shows the friendship was worth more than the lost gift."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the friends eating together anyway. Even without the original present, the ending proves that kindness can mend a sad turn."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["gift_cfg"].tags) | set(f["obstacle"].tags) | set(f["response"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        gift="cake",
        obstacle="brook",
        response="board",
        hero_name="Pip",
        hero_type="fox",
        friend_name="Mara",
        friend_type="hen",
        trait="gentle",
        trust=8,
        delay=0,
        shared_snack="two warm rolls with butter",
    ),
    StoryParams(
        gift="berries",
        obstacle="hedge",
        response="gate",
        hero_name="Tavi",
        hero_type="badger",
        friend_name="Lina",
        friend_type="goose",
        trait="kind",
        trust=4,
        delay=0,
        shared_snack="half a wheel of cheese and a red apple",
    ),
    StoryParams(
        gift="garland",
        obstacle="ditch",
        response="wagon",
        hero_name="Nell",
        hero_type="doe",
        friend_name="Oren",
        friend_type="frog",
        trait="patient",
        trust=3,
        delay=2,
        shared_snack="a small jar of jam and a loaf of brown bread",
    ),
    StoryParams(
        gift="cake",
        obstacle="ditch",
        response="board",
        hero_name="Mara",
        hero_type="hen",
        friend_name="Tavi",
        friend_type="badger",
        trait="steady",
        trust=2,
        delay=0,
        shared_snack="three sweet plums from the windowsill",
    ),
]


def explain_pair(obstacle_id: str, response_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try a sensible helper like {better}.)"
        )
    return (
        f"(No story: {response_id} is not a believable fix for a {obstacle.label}. "
        f"Pick a response that actually fits the obstacle.)"
    )


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(G, O, R) :- gift(G), obstacle(O), response(R), sensible(R), helps(R, O).

% --- outcome model ---------------------------------------------------------
calming(T) :- trait(T), calming_trait(T).
friendship_holds :- trust(V), trust_to_listen(M), V >= M, calming(T), trait(T).
severity(S + D) :- chosen_obstacle(O), obstacle_severity(O, S), delay(D).
saved :- chosen_response(R), helps(R, O), chosen_obstacle(O), power(R, P), severity(V), P >= V.

outcome(averted) :- friendship_holds.
outcome(saved) :- not friendship_holds, saved.
outcome(shared_only) :- not friendship_holds, not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_severity", oid, obstacle.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for oid in sorted(response.obstacles):
            lines.append(asp.fact("helps", rid, oid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("trust_to_listen", TRUST_TO_LISTEN))
    for trait in sorted(CALMING_TRAITS):
        lines.append(asp.fact("calming_trait", trait))
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
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("trust", params.trust),
        asp.fact("trait", params.trait),
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: generate() smoke test produced a story.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Friendship folk tale story world: a foolish shortcut, a loyal friend, and a shared meal."
    )
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2],
                    help="how long the proper help takes to arrive; higher makes saving the gift harder")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_two_names(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    first = rng.choice(NAMES)
    second_choices = [pair for pair in NAMES if pair[0] != first[0]]
    second = rng.choice(second_choices)
    return first, second


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.response and not valid_pair(args.obstacle, args.response):
        raise StoryError(explain_pair(args.obstacle, args.response))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_pair(args.obstacle or "brook", args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.gift is None or combo[0] == args.gift)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    gift_id, obstacle_id, response_id = rng.choice(sorted(combos))
    (hero_name, hero_type), (friend_name, friend_type) = pick_two_names(rng)
    trait = args.trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(2, 9)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    snack = rng.choice(SNACKS)
    return StoryParams(
        gift=gift_id,
        obstacle=obstacle_id,
        response=response_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
        trust=trust,
        delay=delay,
        shared_snack=snack,
    )


def generate(params: StoryParams) -> StorySample:
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.response in RESPONSES and not valid_pair(params.obstacle, params.response):
        raise StoryError(explain_pair(params.obstacle, params.response))

    world = tell(
        gift_cfg=GIFTS[params.gift],
        obstacle=OBSTACLES[params.obstacle],
        response=RESPONSES[params.response],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        trait=params.trait,
        trust=params.trust,
        delay=params.delay,
        shared_snack=params.shared_snack,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (gift, obstacle, response) combos:\n")
        for gift, obstacle, response in combos:
            print(f"  {gift:8} {obstacle:8} {response}")
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
            header = (
                f"### {p.hero_name} and {p.friend_name}: {p.gift} at the {p.obstacle} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
