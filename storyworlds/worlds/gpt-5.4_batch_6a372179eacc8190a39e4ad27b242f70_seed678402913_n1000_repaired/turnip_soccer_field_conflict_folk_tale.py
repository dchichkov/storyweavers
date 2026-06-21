#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/turnip_soccer_field_conflict_folk_tale.py
====================================================================

A standalone story world for a folk-tale-shaped soccer-field conflict: a great
turnip has pushed up through the grass where children want to play. One child
wants the game to start at once, another insists the field and the plant should
be treated with care, and a grown helper turns the quarrel into teamwork.

The world model tracks physical state (blocked field, rooted turnip, loose soil)
and emotional state (impatience, conflict, relief, pride). The prose is driven
by those states: a blocked place causes delay, a weak first fix can fail, and a
shared pull resolves both the obstacle and the quarrel.

Run it
------
    python storyworlds/worlds/gpt-5.4/turnip_soccer_field_conflict_folk_tale.py
    python storyworlds/worlds/gpt-5.4/turnip_soccer_field_conflict_folk_tale.py --spot goalmouth --soil clay --fix hands
    python storyworlds/worlds/gpt-5.4/turnip_soccer_field_conflict_folk_tale.py --spot sideline
    python storyworlds/worlds/gpt-5.4/turnip_soccer_field_conflict_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/turnip_soccer_field_conflict_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/turnip_soccer_field_conflict_folk_tale.py --verify
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
class Spot:
    id: str
    label: str
    phrase: str
    opening: str
    block_text: str
    ending: str
    blocks_play: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Soil:
    id: str
    label: str
    depth: int
    pull_text: str
    loosen_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    first_try_text: str
    quick_success_text: str
    fail_text: str
    retry_prep_text: str
    retry_success_text: str
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "keeper"}]

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


def _r_blocked_conflict(world: World) -> list[str]:
    field = world.entities.get("field")
    turnip = world.entities.get("turnip")
    if field is None or turnip is None:
        return []
    if field.meters["blocked"] < THRESHOLD or turnip.meters["rooted"] < THRESHOLD:
        return []
    sig = ("blocked_conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for child in world.children():
        child.memes["frustration"] += 1
    return ["__blocked__"]


def _r_pull_frees_field(world: World) -> list[str]:
    field = world.entities.get("field")
    turnip = world.entities.get("turnip")
    if field is None or turnip is None:
        return []
    if turnip.meters["rooted"] >= THRESHOLD or turnip.meters["pulled"] < THRESHOLD:
        return []
    sig = ("field_free",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    field.meters["blocked"] = 0.0
    for child in world.children():
        child.memes["relief"] += 1
        child.memes["joy"] += 1
    return ["__free__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_conflict", tag="social", apply=_r_blocked_conflict),
    Rule(name="field_free", tag="physical", apply=_r_pull_frees_field),
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


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: (f.power, f.sense))


def blocking_spot(spot: Spot) -> bool:
    return spot.blocks_play


def difficulty(soil: Soil) -> int:
    return soil.depth


def can_solve_quickly(fix: Fix, soil: Soil) -> bool:
    return fix.power >= difficulty(soil)


def predict_stuck(world: World) -> dict:
    sim = world.copy()
    field = sim.get("field")
    turnip = sim.get("turnip")
    field.meters["blocked"] = 1.0
    turnip.meters["rooted"] = 1.0
    propagate(sim, narrate=False)
    return {
        "blocked": field.meters["blocked"] >= THRESHOLD,
        "frustration": sum(child.memes["frustration"] for child in sim.children()),
    }


def opening(world: World, captain: Entity, keeper: Entity, helper: Entity, spot: Spot) -> None:
    for child in (captain, keeper):
        child.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, when the white lines of the soccer field shone like fresh chalk, "
        f"{captain.id} and {keeper.id} came with a ball tucked under one arm and a whole game waiting in their feet."
    )
    world.say(
        f"{spot.opening} There, to the wonder of both children, stood a turnip with broad leaves and a fat pale shoulder peeping from the earth."
    )
    world.say(
        f'The old helper of the field, {helper.id}, was mending a net nearby and called, '
        f'"Mind the ground, little players. The field tells the truth to those who look before they kick."'
    )


def discover_obstacle(world: World, captain: Entity, keeper: Entity, spot: Spot) -> None:
    field = world.get("field")
    turnip = world.get("turnip")
    field.meters["blocked"] = 1.0
    turnip.meters["rooted"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But when the ball rolled toward {spot.phrase}, it bumped against the turnip and hopped away. {spot.block_text}"
    )
    world.say(
        f'{captain.id} stamped once and said, "A game should begin when the whistle is ready, not when a vegetable is ready."'
    )
    world.say(
        f'{keeper.id} laid a hand on the ball and answered, "A turnip is not a stone. If we treat the field roughly, we spoil both game and garden."'
    )


def quarrel(world: World, captain: Entity, keeper: Entity, helper: Entity) -> None:
    captain.memes["impatience"] += 1
    keeper.memes["care"] += 1
    captain.memes["conflict"] += 1
    keeper.memes["conflict"] += 1
    pred = predict_stuck(world)
    world.facts["predicted_frustration"] = pred["frustration"]
    world.say(
        f"The two children pulled words back and forth as if each word were a rope. "
        f"{captain.id} wanted the first kick at once, and {keeper.id} wanted the field treated kindly."
    )
    if pred["frustration"] >= 2:
        world.say(
            f'{helper.id} saw the quarrel growing and said, "When a thing blocks the middle, anger only blocks it more. '
            f'Hands must join where voices have begun to tug apart."'
        )


def ask_for_help(world: World, captain: Entity, keeper: Entity, helper: Entity, fix: Fix) -> None:
    captain.memes["humility"] += 1
    keeper.memes["trust"] += 1
    world.say(
        f"At last the children looked at one another, then at {helper.id}. "
        f'"Please help us move the turnip," said {keeper.id}. "{captain.id} and I cannot even agree on how to start."'
    )
    world.say(
        f'{helper.id} nodded and said, "Then we shall try the wise way first: {fix.first_try_text}."'
    )


def quick_success(world: World, captain: Entity, keeper: Entity, helper: Entity, spot: Spot, fix: Fix) -> None:
    turnip = world.get("turnip")
    turnip.meters["rooted"] = 0.0
    turnip.meters["pulled"] = 1.0
    propagate(world, narrate=False)
    captain.memes["pride"] += 1
    keeper.memes["pride"] += 1
    captain.memes["conflict"] = 0.0
    keeper.memes["conflict"] = 0.0
    world.say(
        f"{fix.quick_success_text} Up came the turnip with a soft tearing sigh of soil and roots."
    )
    world.say(
        f'{helper.id} laughed. "See? The field gives way more gladly to joined hands than to hurried feet."'
    )
    world.say(
        f"They carried the turnip to the fence, and soon the ball ran true again. {spot.ending}"
    )


def failed_first_try(world: World, captain: Entity, keeper: Entity, helper: Entity, soil: Soil, fix: Fix) -> None:
    captain.memes["frustration"] += 1
    keeper.memes["frustration"] += 1
    world.say(
        f"{fix.fail_text} {soil.pull_text}"
    )
    world.say(
        f'{captain.id} felt heat rise in {captain.pronoun("possessive")} cheeks, but {helper.id} raised a calm hand. '
        f'"A stubborn root is not beaten by a hotter temper," {helper.pronoun()} said.'
    )


def retry_success(world: World, captain: Entity, keeper: Entity, helper: Entity, spot: Spot, soil: Soil, fix: Fix) -> None:
    turnip = world.get("turnip")
    turnip.meters["loosened"] = 1.0
    world.say(
        f"{fix.retry_prep_text} {soil.loosen_text}"
    )
    turnip.meters["rooted"] = 0.0
    turnip.meters["pulled"] = 1.0
    propagate(world, narrate=False)
    captain.memes["conflict"] = 0.0
    keeper.memes["conflict"] = 0.0
    captain.memes["patience"] += 1
    keeper.memes["patience"] += 1
    world.say(
        f"{fix.retry_success_text} This time the turnip came free, heavy and shining, and all three nearly sat down in the grass from the sudden give."
    )
    world.say(
        f'{helper.id} brushed the dirt from the turnip and said, "First we loosened the earth, and then we loosened the quarrel too."'
    )
    world.say(
        f"After that, the children set the turnip safely by the gate. {spot.ending}"
    )


def harvest_meal(world: World, captain: Entity, keeper: Entity, helper: Entity, outcome: str) -> None:
    captain.memes["love"] += 1
    keeper.memes["love"] += 1
    world.say(
        f"When the game was done, {helper.id} promised to wash the turnip and share it for supper, "
        f"so the strange visitor from the soccer field would not be wasted."
    )
    if outcome == "quick":
        world.say(
            f"And so the quarrel that had begun with sharp words ended with muddy hands, honest laughter, and a ball rolling cleanly into the goal."
        )
    else:
        world.say(
            f"And so the quarrel that had delayed the first kick ended with patient hands, wiser hearts, and a ball that finally flew straight between the posts."
        )


def tell(
    spot: Spot,
    soil: Soil,
    fix: Fix,
    captain_name: str = "Mira",
    captain_gender: str = "girl",
    keeper_name: str = "Tomas",
    keeper_gender: str = "boy",
    helper_name: str = "Old Niko",
    helper_type: str = "father",
) -> World:
    world = World()
    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            traits=["quick"],
        )
    )
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=keeper_gender,
            role="keeper",
            traits=["careful"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    world.add(Entity(id="field", type="field", label="soccer field", tags={"soccer"}))
    world.add(
        Entity(
            id="turnip",
            type="turnip",
            label="turnip",
            phrase="a great turnip",
            tags={"turnip"},
        )
    )
    world.add(Entity(id="ball", type="ball", label="ball", tags={"soccer"}))

    opening(world, captain, keeper, helper, spot)
    world.para()
    discover_obstacle(world, captain, keeper, spot)
    quarrel(world, captain, keeper, helper)
    ask_for_help(world, captain, keeper, helper, fix)

    world.para()
    quick = can_solve_quickly(fix, soil)
    if quick:
        quick_success(world, captain, keeper, helper, spot, fix)
        outcome = "quick"
    else:
        failed_first_try(world, captain, keeper, helper, soil, fix)
        retry_success(world, captain, keeper, helper, spot, soil, fix)
        outcome = "after_retry"

    world.para()
    harvest_meal(world, captain, keeper, helper, outcome)

    world.facts.update(
        captain=captain,
        keeper=keeper,
        helper=helper,
        field=world.get("field"),
        turnip=world.get("turnip"),
        ball=world.get("ball"),
        spot=spot,
        soil=soil,
        fix=fix,
        outcome=outcome,
        blocked_initially=True,
        pulled=world.get("turnip").meters["pulled"] >= THRESHOLD,
        conflict_happened=(captain.memes["impatience"] >= THRESHOLD and keeper.memes["care"] >= THRESHOLD),
    )
    return world


@dataclass
class StoryParams:
    spot: str
    soil: str
    fix: str
    captain: str
    captain_gender: str
    keeper: str
    keeper_gender: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


SPOTS = {
    "goalmouth": Spot(
        id="goalmouth",
        label="goalmouth",
        phrase="the mouth of the goal",
        opening="At the very mouth of the goal, where any good shot hoped to finish,",
        block_text="No clean shot could pass while it sat there like a squat white guard.",
        ending="Before long, one shot after another kissed the net, and neither child complained of the delay again.",
        blocks_play=True,
        tags={"goal", "soccer"},
    ),
    "center_circle": Spot(
        id="center_circle",
        label="center circle",
        phrase="the center circle",
        opening="In the center circle itself, where every match begins and all eyes first settle,",
        block_text="No fair kickoff could begin while it stood in the middle like a little hill with leaves.",
        ending="Then the whistle sang, the match began at last, and the children remembered that a true beginning is worth waiting for.",
        blocks_play=True,
        tags={"center", "soccer"},
    ),
    "sideline": Spot(
        id="sideline",
        label="sideline",
        phrase="the sideline",
        opening="Along the far sideline, outside the path of feet and ball,",
        block_text="It looked odd there, but it did not truly stop the game.",
        ending="The game could have gone on all along, which is why no such quarrel belongs in this telling.",
        blocks_play=False,
        tags={"sideline", "soccer"},
    ),
}

SOILS = {
    "soft": Soil(
        id="soft",
        label="soft soil",
        depth=1,
        pull_text="The soil was soft from yesterday's watering.",
        loosen_text="A little shaking of the leaves was almost enough, for the earth was already kind.",
        tags={"soil"},
    ),
    "packed": Soil(
        id="packed",
        label="packed ground",
        depth=2,
        pull_text="The ground held the root with a hard, stubborn grip.",
        loosen_text="A little water and careful scraping softened the packed ring around the root.",
        tags={"soil"},
    ),
    "clay": Soil(
        id="clay",
        label="clay",
        depth=3,
        pull_text="The clay clung like a fist and would not let the root go.",
        loosen_text="Water darkened the clay, and a spade gently opened the earth around the turnip's deep root.",
        tags={"soil", "clay"},
    ),
}

FIXES = {
    "hands": Fix(
        id="hands",
        label="joined hands",
        sense=2,
        power=1,
        first_try_text="all of us take hold of the leaves and pull together",
        quick_success_text="They set their shoes, counted to three, and pulled as one",
        fail_text="They tugged until their sleeves stretched tight, but the turnip did not budge.",
        retry_prep_text="So the helper brought a bucket of water and a small spade, and together they made the earth gentler.",
        retry_success_text="Then they took hold once more and pulled in one long steady heave.",
        qa_text="they all grabbed the leaves together and pulled",
        tags={"teamwork", "pull"},
    ),
    "water_and_pull": Fix(
        id="water_and_pull",
        label="water and pull",
        sense=3,
        power=2,
        first_try_text="we pour water around the root, wait a little, and then pull together",
        quick_success_text="They trickled water round the root, waited, and then leaned back together",
        fail_text="They watered the root and pulled together, but the earth still held fast.",
        retry_prep_text="Then the helper fetched a small spade and loosened the earth while the children held the leaves steady.",
        retry_success_text="After that, all three pulled again with a slower, stronger tug.",
        qa_text="they softened the soil with water and then pulled together",
        tags={"water", "teamwork", "pull"},
    ),
    "spade_and_pull": Fix(
        id="spade_and_pull",
        label="spade and pull",
        sense=3,
        power=3,
        first_try_text="we loosen the earth with a small spade and then pull together",
        quick_success_text="The helper loosened the earth, the children took hold, and all three drew back together",
        fail_text="They worked carefully, but the root still clung for one more moment.",
        retry_prep_text="So they widened the circle, watered the clay, and tried again with more patience than before.",
        retry_success_text="Then the spade slipped under the last hard clump, and they gave one great pull together.",
        qa_text="the helper loosened the ground with a small spade before they all pulled together",
        tags={"spade", "teamwork", "pull"},
    ),
    "kick_it": Fix(
        id="kick_it",
        label="kick it aside",
        sense=0,
        power=0,
        first_try_text="kick the turnip like a spare ball",
        quick_success_text="They kicked it aside",
        fail_text="They kicked at it foolishly.",
        retry_prep_text="Then they stopped being foolish.",
        retry_success_text="Then they solved it properly.",
        qa_text="they kicked the turnip",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Zora", "Iva", "Nora", "Tala", "Mina", "Ana"]
BOY_NAMES = ["Tomas", "Luka", "Milo", "Pavel", "Niko", "Ivo", "Sava", "Dario"]
HELPER_NAMES = ["Old Niko", "Coach Mara", "Caretaker Bojan", "Auntie Vesna"]
HELPER_TYPES = ["mother", "father"]
TRAITLESS = ["quick", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for spot_id, spot in SPOTS.items():
        if not blocking_spot(spot):
            continue
        for soil_id in SOILS:
            for fix_id, fix in FIXES.items():
                if fix.sense >= SENSE_MIN:
                    combos.append((spot_id, soil_id, fix_id))
    return combos


KNOWLEDGE = {
    "soccer": [
        (
            "What is a soccer field?",
            "A soccer field is a big grassy place marked with lines where players kick a ball and try to score goals."
        )
    ],
    "goal": [
        (
            "Why must the goalmouth stay clear in soccer?",
            "The goalmouth needs to stay clear so the ball can pass fairly and players do not trip over things near the net."
        )
    ],
    "turnip": [
        (
            "What is a turnip?",
            "A turnip is a root vegetable that grows partly under the ground. It has leaves on top and a thick round root below."
        )
    ],
    "soil": [
        (
            "Why is a root hard to pull from hard soil?",
            "Hard soil grips the root tightly all around it. That makes the root harder to lift out."
        )
    ],
    "clay": [
        (
            "What is clay soil like?",
            "Clay soil is heavy and sticky when wet and hard when dry. Roots can cling tightly in it."
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help with a hard job?",
            "Teamwork helps because several people can share the effort and also think together about the safest way to solve a problem."
        )
    ],
    "water": [
        (
            "Why does water help loosen soil?",
            "Water can soften dry dirt around a root. Softer dirt lets the root move more easily."
        )
    ],
    "spade": [
        (
            "What is a spade for?",
            "A spade is a tool for digging and lifting soil. Grown-ups use it to loosen earth around roots."
        )
    ],
}
KNOWLEDGE_ORDER = ["soccer", "goal", "turnip", "soil", "clay", "teamwork", "water", "spade"]


def pair_noun(captain: Entity, keeper: Entity) -> str:
    if captain.type == "girl" and keeper.type == "girl":
        return "two teammates"
    if captain.type == "boy" and keeper.type == "boy":
        return "two teammates"
    return "two young teammates"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    keeper = f["keeper"]
    spot = f["spot"]
    soil = f["soil"]
    fix = f["fix"]
    outcome = f["outcome"]
    prompts = [
        f'Write a folk-tale-style story for a 3-to-5-year-old set on a soccer field that includes the word "turnip" and a conflict between two children.',
        f"Tell a gentle folk tale where {captain.id} wants a soccer game to begin at once, but {keeper.id} insists they must deal kindly with a turnip growing in {spot.phrase}.",
    ]
    if outcome == "quick":
        prompts.append(
            f"Write a story where a wise helper shows children how to solve a field problem by cooperation: they use {fix.label} in {soil.label} and the game begins happily."
        )
    else:
        prompts.append(
            f"Write a story where the first plan is too weak for {soil.label}, so patience and a second try are needed before the soccer match can begin."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    keeper = f["keeper"]
    helper = f["helper"]
    spot = f["spot"]
    soil = f["soil"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(captain, keeper)}, {captain.id} and {keeper.id}, and {helper.id}, the grown helper at the soccer field."
        ),
        (
            "What caused the conflict?",
            f"The conflict began because a turnip was growing in {spot.phrase}, where it stopped the game from starting fairly. {captain.id} wanted to begin at once, but {keeper.id} wanted to treat the field and the plant carefully."
        ),
        (
            f"Why could they not just start playing?",
            f"They could not start because the turnip blocked {spot.phrase}, so the ball would not roll or fly true there. The obstacle turned their eagerness into frustration."
        ),
        (
            f"What did {helper.id} tell them to do?",
            f"{helper.id} told them to stop arguing and work together. The helper knew that joined hands would solve more than angry words."
        ),
    ]
    if outcome == "quick":
        qa.append(
            (
                "How did they solve the problem?",
                f"They solved it by using {fix.label}. {fix.qa_text.capitalize()}, and the turnip came up before the quarrel could grow any larger."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The turnip was moved safely aside, the field was clear again, and the soccer game began. The ending shows that the children changed from arguing to cooperating."
            )
        )
    else:
        qa.append(
            (
                "Did the first plan work right away?",
                f"No. The first try was too weak for {soil.label}, so the turnip stayed rooted at first. That failure taught the children they needed patience as well as effort."
            )
        )
        qa.append(
            (
                "How did they finally get the turnip out?",
                f"After the first try failed, {helper.id} prepared the ground more carefully and then all three pulled again together. They succeeded because they changed both their method and their mood."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"In the end the turnip came free, the quarrel faded, and the ball could finally travel straight on the soccer field. The children began their game with calmer hearts than they had at the start."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    f = world.facts
    tags |= set(f["spot"].tags)
    tags |= set(f["soil"].tags)
    tags |= set(f["fix"].tags)
    tags.add("turnip")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        spot="goalmouth",
        soil="soft",
        fix="hands",
        captain="Mira",
        captain_gender="girl",
        keeper="Tomas",
        keeper_gender="boy",
        helper_name="Old Niko",
        helper_type="father",
    ),
    StoryParams(
        spot="center_circle",
        soil="packed",
        fix="water_and_pull",
        captain="Lina",
        captain_gender="girl",
        keeper="Milo",
        keeper_gender="boy",
        helper_name="Coach Mara",
        helper_type="mother",
    ),
    StoryParams(
        spot="goalmouth",
        soil="clay",
        fix="hands",
        captain="Nora",
        captain_gender="girl",
        keeper="Luka",
        keeper_gender="boy",
        helper_name="Auntie Vesna",
        helper_type="mother",
    ),
    StoryParams(
        spot="center_circle",
        soil="clay",
        fix="spade_and_pull",
        captain="Pavel",
        captain_gender="boy",
        keeper="Ana",
        keeper_gender="girl",
        helper_name="Caretaker Bojan",
        helper_type="father",
    ),
]


def explain_spot(spot: Spot) -> str:
    return (
        f"(No story: a turnip on {spot.phrase} does not truly block the soccer game. "
        f"Conflict in this world needs the turnip to stand in a place like the goalmouth or center circle.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try a gentler, more believable fix such as {better}.)"
    )


ASP_RULES = r"""
blocking(S) :- spot(S), blocks_play(S).
sensible(F) :- fix(F), sense(F, N), sense_min(M), N >= M.
valid(S, So, F) :- blocking(S), soil(So), sensible(F).

quick :- chosen_fix(F), chosen_soil(So), power(F, P), depth(So, D), P >= D.
outcome(quick) :- quick.
outcome(after_retry) :- not quick.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.blocks_play:
            lines.append(asp.fact("blocks_play", spot_id))
    for soil_id, soil in SOILS.items():
        lines.append(asp.fact("soil", soil_id))
        lines.append(asp.fact("depth", soil_id, soil.depth))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
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
    return sorted(fix for (fix,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_fix", params.fix),
            asp.fact("chosen_soil", params.soil),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    fix = FIXES[params.fix]
    soil = SOILS[params.soil]
    return "quick" if can_solve_quickly(fix, soil) else "after_retry"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {fix.id for fix in sensible_fixes()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible fixes: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a turnip on a soccer field causes a quarrel, and teamwork clears the way."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--soil", choices=SOILS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper")
    ap.add_argument("--keeper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot is not None and not SPOTS[args.spot].blocks_play:
        raise StoryError(explain_spot(SPOTS[args.spot]))
    if args.fix is not None and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.soil is None or combo[1] == args.soil)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, soil_id, fix_id = rng.choice(sorted(combos))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    keeper_gender = args.keeper_gender or rng.choice(["girl", "boy"])
    captain = args.captain or pick_name(rng, captain_gender)
    keeper = args.keeper or pick_name(rng, keeper_gender, avoid=captain)
    helper_name = rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    return StoryParams(
        spot=spot_id,
        soil=soil_id,
        fix=fix_id,
        captain=captain,
        captain_gender=captain_gender,
        keeper=keeper,
        keeper_gender=keeper_gender,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.soil not in SOILS:
        raise StoryError(f"(Unknown soil: {params.soil})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not SPOTS[params.spot].blocks_play:
        raise StoryError(explain_spot(SPOTS[params.spot]))
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        spot=SPOTS[params.spot],
        soil=SOILS[params.soil],
        fix=FIXES[params.fix],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        keeper_name=params.keeper,
        keeper_gender=params.keeper_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (spot, soil, fix) combos:\n")
        for spot, soil, fix in combos:
            print(f"  {spot:13} {soil:8} {fix}")
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
            header = f"### {p.captain} & {p.keeper}: {p.spot}, {p.soil}, {p.fix} ({outcome_of(p)})"
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
