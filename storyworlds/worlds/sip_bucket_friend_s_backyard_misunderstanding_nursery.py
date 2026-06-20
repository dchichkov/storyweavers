#!/usr/bin/env python3
"""
storyworlds/worlds/sip_bucket_friend_s_backyard_misunderstanding_nursery.py
============================================================================

Nursery-rhyme storyworld about a small misunderstanding in a friend's backyard.

Internal source tale:
Two children mean to water something gentle in a friend's backyard. One child
is carrying a bucket while the other mentions a sip from a striped cup, but a
backyard sound bends one little word. The bucket sloshes, the task wobbles,
and the children have to slow down, rhyme the words, and finish the job with a
clearer understanding than they had before.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


BUCKET_START = 3
CHILD_TYPES = ("girl", "boy", "child")
VISITOR_NAMES = ["Pip", "Mina", "Toby", "June", "Elsie", "Rowan"]
FRIEND_NAMES = ["Nell", "Kit", "Rosa", "Ben", "Mae", "Owen"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    region: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class BackyardSpot:
    id: str
    phrase: str
    prop_phrase: str
    flatness: int
    shade: int
    hose: int
    echo: int


@dataclass(frozen=True)
class GardenGoal:
    id: str
    phrase: str
    target_phrase: str
    place_phrase: str
    thirst_need: int
    balance_need: int
    ending_image: str


@dataclass(frozen=True)
class Mixup:
    id: str
    cause: str
    heard_word: str
    meant_word: str
    mistake_text: str
    aftermath_text: str
    water_loss: int
    mud_gain: int
    clarity_need: int
    steady_risk: int
    needs_refill: int
    lesson: str


@dataclass(frozen=True)
class Repair:
    id: str
    label: str
    chant: str
    method_text: str
    pointing: int
    echo: int
    steady: int


@dataclass
class World:
    spot: BackyardSpot
    goal: GardenGoal
    mixup: Mixup
    repair: Repair
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    history: list[dict[str, object]] = field(default_factory=list)

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
        return copy.deepcopy(self)

    def event(self, event_id: str, **detail: object) -> None:
        row = {"event": event_id}
        row.update(detail)
        self.history.append(row)


SPOTS: dict[str, BackyardSpot] = {
    "bean_arbor": BackyardSpot(
        "bean_arbor",
        "the bean-arbor corner in a friend's backyard",
        "a twine reel hanging on the fence like a little moon",
        flatness=1,
        shade=1,
        hose=1,
        echo=0,
    ),
    "sandbox_path": BackyardSpot(
        "sandbox_path",
        "the stepping-stone path beside the sandbox in a friend's backyard",
        "a red pinwheel ticking by the fence",
        flatness=2,
        shade=0,
        hose=0,
        echo=1,
    ),
    "plum_stump": BackyardSpot(
        "plum_stump",
        "the plum-stump nook in a friend's backyard",
        "a mossy stump that worked like a tiny table",
        flatness=1,
        shade=2,
        hose=0,
        echo=1,
    ),
    "rabbit_fence": BackyardSpot(
        "rabbit_fence",
        "the rabbit-fence gate in a friend's backyard",
        "a brass spigot shining under the fence rail",
        flatness=0,
        shade=1,
        hose=2,
        echo=0,
    ),
}


GOALS: dict[str, GardenGoal] = {
    "bean_sprouts": GardenGoal(
        "bean_sprouts",
        "wake the bean sprouts before the sun grew hot",
        "the bean bed",
        "by the bean bed",
        thirst_need=3,
        balance_need=1,
        ending_image="the bean leaves held bright drops like green bells",
    ),
    "marigolds": GardenGoal(
        "marigolds",
        "cool the sleepy marigolds by the stepping stones",
        "the marigold patch",
        "by the marigolds",
        thirst_need=2,
        balance_need=0,
        ending_image="the marigolds lifted their orange faces and looked almost awake enough to sing",
    ),
    "strawberries": GardenGoal(
        "strawberries",
        "give the strawberry roots a gentle drink",
        "the strawberry ring",
        "by the strawberry ring",
        thirst_need=3,
        balance_need=1,
        ending_image="the strawberry roots drank deep while one white blossom nodded over the rim",
    ),
    "birdbath": GardenGoal(
        "birdbath",
        "fill the birdbath for the robins",
        "the birdbath",
        "by the birdbath",
        thirst_need=2,
        balance_need=0,
        ending_image="two robins came to the birdbath and splashed silver rings into the air",
    ),
}


MIXUPS: dict[str, Mixup] = {
    "skip_for_sip": Mixup(
        "skip_for_sip",
        "a sparrow chirped right across the sentence",
        "skip",
        "sip",
        "the visiting child skipped three shiny stones with the bucket swinging wide",
        "Water hopped out in silver commas, and the path wore a quick wet grin.",
        water_loss=1,
        mud_gain=1,
        clarity_need=2,
        steady_risk=1,
        needs_refill=0,
        lesson="A tiny sound can bend a tiny word.",
    ),
    "tip_for_set": Mixup(
        "tip_for_set",
        "the gate latch clinked over the middle of the line",
        "tip",
        "set",
        "the visiting child tipped the bucket too early beside the path",
        "Half the water went patter-pat on the dust before the roots could drink.",
        water_loss=2,
        mud_gain=2,
        clarity_need=3,
        steady_risk=0,
        needs_refill=1,
        lesson="A half-heard plan can spill a whole good idea.",
    ),
    "dip_for_sip": Mixup(
        "dip_for_sip",
        "a fat bee buzzed round the mint cup at the wrong little moment",
        "dip",
        "sip",
        "the visiting child dipped the striped cup into the bucket and splashed both hands",
        "Cool dark freckles spread over the dirt, and the children blinked at the same wrong move.",
        water_loss=1,
        mud_gain=2,
        clarity_need=2,
        steady_risk=0,
        needs_refill=0,
        lesson="One changed sound can change what the hands do.",
    ),
}


REPAIRS: dict[str, Repair] = {
    "clap_and_point": Repair(
        "clap_and_point",
        "clap and point",
        '"Sip from cup, bucket low, step by step and off we go."',
        "The friend clapped twice, pointed first to the striped cup, and then pointed to the waiting bucket.",
        pointing=2,
        echo=1,
        steady=1,
    ),
    "slow_step_song": Repair(
        "slow_step_song",
        "a slow-step song",
        '"One small sip, two slow toes, bucket where the bean bed grows."',
        "Both children sang the words slowly and walked them with their feet on the stones.",
        pointing=1,
        echo=2,
        steady=2,
    ),
    "tap_and_show": Repair(
        "tap_and_show",
        "tap and show",
        '"Cup for sip and pail for pour, hear it once and hear it more."',
        "The friend tapped the striped cup, then rang the bucket rim with one neat fingernail tap.",
        pointing=2,
        echo=0,
        steady=1,
    ),
    "shade_repeat": Repair(
        "shade_repeat",
        "a shady repeat",
        '"Sip means drink and set means stay; gentle words can show the way."',
        "They stepped into the shady nook and repeated the line until it sounded round and clear.",
        pointing=1,
        echo=1,
        steady=2,
    ),
}


@dataclass
class StoryParams:
    spot: str
    goal: str
    mixup: str
    repair: str
    visitor: str
    visitor_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("bean_arbor", "marigolds", "skip_for_sip", "clap_and_point", "Pip", "boy", "Nell", "girl", 201),
    StoryParams("plum_stump", "birdbath", "dip_for_sip", "slow_step_song", "June", "girl", "Kit", "boy", 202),
    StoryParams("rabbit_fence", "bean_sprouts", "tip_for_set", "clap_and_point", "Mina", "girl", "Ben", "boy", 203),
    StoryParams("sandbox_path", "marigolds", "skip_for_sip", "tap_and_show", "Toby", "boy", "Rosa", "girl", 204),
    StoryParams("bean_arbor", "birdbath", "dip_for_sip", "shade_repeat", "Elsie", "girl", "Owen", "boy", 205),
]


def reasonableness_report(
    spot: BackyardSpot,
    goal: GardenGoal,
    mixup: Mixup,
    repair: Repair,
) -> tuple[bool, str]:
    clarity = spot.echo + repair.echo + repair.pointing
    if clarity < mixup.clarity_need:
        return False, "the backyard and repair do not make the misheard words clear enough"

    steadiness = spot.flatness + spot.shade + repair.steady
    if steadiness < goal.balance_need + mixup.steady_risk:
        return False, "the children would still wobble too much to carry the bucket carefully"

    if spot.hose < mixup.needs_refill:
        return False, "there is no nearby water source to recover from the spill"

    water_left = BUCKET_START - mixup.water_loss + spot.hose
    if water_left < goal.thirst_need:
        return False, "too much water would be lost before the backyard task could be finished"

    return True, ""


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for spot_id, spot in SPOTS.items():
        for goal_id, goal in GOALS.items():
            for mixup_id, mixup in MIXUPS.items():
                for repair_id, repair in REPAIRS.items():
                    ok, _ = reasonableness_report(spot, goal, mixup, repair)
                    if ok:
                        out.append((spot_id, goal_id, mixup_id, repair_id))
    return out


def explain_rejection(args: argparse.Namespace) -> str:
    if not all([args.spot, args.goal, args.mixup, args.repair]):
        return "(No valid combinations match the requested options.)"
    ok, reason = reasonableness_report(
        SPOTS[args.spot],
        GOALS[args.goal],
        MIXUPS[args.mixup],
        REPAIRS[args.repair],
    )
    if ok:
        return "(No valid combinations match the requested options.)"
    return f"(No story: {reason})"


def introduce(
    world: World,
    visitor: Entity,
    friend: Entity,
    bucket: Entity,
    cup: Entity,
    target: Entity,
) -> None:
    world.say(
        f"In {world.spot.phrase}, {visitor.label} came to play with {friend.label}, and the two of them had a plain small plan."
    )
    world.say(
        f"They carried {bucket.phrase} for the work and {cup.phrase} for one cool sip while they meant to {world.goal.phrase}."
    )
    world.say(
        f"Nearby, {world.spot.prop_phrase} watched over {target.phrase} as if the whole yard had settled down to listen."
    )
    visitor.memes["eagerness"] += 2
    friend.memes["care"] += 2
    world.event("premise", spot=world.spot.id, goal=world.goal.id)


def start_mixup(
    world: World,
    visitor: Entity,
    friend: Entity,
    bucket: Entity,
    ground: Entity,
) -> None:
    line = f'"Take a sip, then set the bucket {world.goal.place_phrase}," {friend.label} said.'
    world.say(line)
    world.say(
        f"But {world.mixup.cause}, and {visitor.label} heard \"{world.mixup.heard_word}\" when {friend.pronoun('subject')} had meant \"{world.mixup.meant_word}.\""
    )
    world.say(
        f"So {world.mixup.mistake_text}. {world.mixup.aftermath_text} It was only a misunderstanding, but it made the little job wobble."
    )
    bucket.meters["water"] = max(0, bucket.meters["water"] - world.mixup.water_loss)
    ground.meters["muddy"] += world.mixup.mud_gain
    visitor.meters["confusion"] += world.mixup.clarity_need
    visitor.memes["embarrassment"] += 1
    friend.memes["concern"] += 1
    world.facts["instruction"] = line
    world.event(
        "mixup",
        heard=world.mixup.heard_word,
        meant=world.mixup.meant_word,
        water_left=bucket.meters["water"],
        mud=ground.meters["muddy"],
    )


def mend_words(
    world: World,
    visitor: Entity,
    friend: Entity,
    bucket: Entity,
    cup: Entity,
    ground: Entity,
    target: Entity,
) -> None:
    world.say(f"{friend.label} did not fuss. {world.repair.method_text}")
    world.say(f'Together they sang, {world.repair.chant}')

    clarity_help = world.spot.echo + world.repair.echo + world.repair.pointing
    visitor.meters["confusion"] = max(0, visitor.meters["confusion"] - clarity_help)
    visitor.memes["trust"] += 2
    friend.memes["patience"] += 2
    bucket.memes["order"] += 1

    top_up = 0
    if bucket.meters["water"] < world.goal.thirst_need and world.spot.hose:
        before = bucket.meters["water"]
        bucket.meters["water"] = min(BUCKET_START, bucket.meters["water"] + world.spot.hose)
        top_up = int(bucket.meters["water"] - before)
        if top_up > 0:
            world.say(
                f"Then they led the bucket to a quick thread of water near {world.spot.prop_phrase}, and the pail filled back with a bright glug-glug."
            )

    ground.meters["muddy"] = max(0, ground.meters["muddy"] - 1)
    target.memes["waited_for_water"] += 1
    world.facts["top_up"] = top_up
    world.facts["clarity_help"] = clarity_help
    world.event("repair", repair=world.repair.id, top_up=top_up, confusion=visitor.meters["confusion"])


def finish_story(
    world: World,
    visitor: Entity,
    friend: Entity,
    bucket: Entity,
    cup: Entity,
    ground: Entity,
    target: Entity,
) -> None:
    if bucket.meters["water"] < world.goal.thirst_need:
        raise StoryError("The bucket no longer holds enough water to finish the backyard task.")

    bucket.meters["water"] -= world.goal.thirst_need
    target.meters["thirst"] = 0
    cup.meters["sips_taken"] += 1
    ground.meters["muddy"] = max(0, ground.meters["muddy"] - 1)
    visitor.memes["relief"] += 2
    friend.memes["joy"] += 2
    target.memes["comfort"] += 2

    world.say(
        f"At last {visitor.label} took the right sip, held the bucket low, and walked with {friend.label} in a gentler little line."
    )
    if world.goal.id == "birdbath":
        world.say(
            f"They poured the water into {target.phrase}, smooth as a song, and soon {world.goal.ending_image}."
        )
    else:
        world.say(
            f"They poured where {target.phrase} waited, smooth as a song, and soon {world.goal.ending_image}."
        )
    world.say(
        f"{world.mixup.lesson} By the end, the misunderstanding had shrunk to a giggle, and the bucket stood still as if it had learned the rhyme as well."
    )
    world.facts["ending_image"] = world.goal.ending_image
    world.facts["resolved"] = True
    world.event("ending", target=world.goal.target_phrase, ending_image=world.goal.ending_image)


def build_story(
    spot: BackyardSpot,
    goal: GardenGoal,
    mixup: Mixup,
    repair: Repair,
    visitor_name: str,
    visitor_type: str,
    friend_name: str,
    friend_type: str,
) -> World:
    ok, reason = reasonableness_report(spot, goal, mixup, repair)
    if not ok:
        raise StoryError(reason)

    world = World(spot=spot, goal=goal, mixup=mixup, repair=repair)
    visitor = world.add(
        Entity(visitor_name, kind="character", type=visitor_type, label=visitor_name, phrase=visitor_name, region=spot.id)
    )
    friend = world.add(
        Entity(friend_name, kind="character", type=friend_type, label=friend_name, phrase=friend_name, region=spot.id)
    )
    bucket = world.add(
        Entity(
            "bucket",
            kind="thing",
            type="bucket",
            label="the blue bucket",
            phrase="the blue bucket",
            owner=friend.id,
            region=spot.id,
        )
    )
    cup = world.add(
        Entity(
            "cup",
            kind="thing",
            type="cup",
            label="the striped cup",
            phrase="the striped cup with mint water",
            owner=friend.id,
            region=spot.id,
        )
    )
    target = world.add(
        Entity(
            "target",
            kind="thing",
            type=goal.id,
            label=goal.target_phrase,
            phrase=goal.target_phrase,
            region=spot.id,
        )
    )
    ground = world.add(
        Entity(
            "ground",
            kind="thing",
            type="ground",
            label="the path",
            phrase="the path",
            region=spot.id,
        )
    )
    yard = world.add(
        Entity(
            "yard",
            kind="thing",
            type="backyard",
            label="the backyard",
            phrase=spot.phrase,
            region=spot.id,
        )
    )

    bucket.meters["water"] = BUCKET_START
    target.meters["thirst"] = goal.thirst_need
    ground.meters["muddy"] = 0
    cup.meters["sips_taken"] = 0
    yard.memes["friendship"] += 1

    world.facts.update(
        visitor=visitor,
        friend=friend,
        bucket=bucket,
        cup=cup,
        target=target,
        ground=ground,
        yard=yard,
    )

    introduce(world, visitor, friend, bucket, cup, target)
    world.para()
    start_mixup(world, visitor, friend, bucket, ground)
    world.para()
    mend_words(world, visitor, friend, bucket, cup, ground, target)
    world.para()
    finish_story(world, visitor, friend, bucket, cup, ground, target)
    return world


def generation_prompts(world: World) -> list[str]:
    visitor: Entity = world.facts["visitor"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        "Write a nursery-rhyme style story that includes the words sip and bucket.",
        f"Set the story in {world.spot.phrase} and build it around a misunderstanding between {visitor.label} and {friend.label}.",
        f"End with a concrete image that proves the children finally managed to {world.goal.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    visitor: Entity = world.facts["visitor"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    target: Entity = world.facts["target"]  # type: ignore[assignment]
    return [
        (
            "Where does the story happen?",
            f"It happens in {world.spot.phrase}. The friend's backyard matters because the children use its path, shade, and nearby water while they solve the mix-up.",
        ),
        (
            "What was the misunderstanding?",
            f"{visitor.label} heard \"{world.mixup.heard_word}\" when {friend.label} really meant \"{world.mixup.meant_word}.\" "
            f"That small sound-change led to the wrong action with the bucket.",
        ),
        (
            "What trouble did the misunderstanding cause?",
            f"The mix-up made water spill before {target.phrase} could get its full drink. "
            f"It also left the path muddier and made the job feel wobbly for a moment.",
        ),
        (
            "How did the children fix the problem?",
            f"They used {world.repair.label} and repeated the words in a little chant. "
            f"The rhyme slowed their bodies down and made the cup and bucket jobs clear again.",
        ),
        (
            "Why could they still finish their task?",
            f"They could still finish because the repair cleared the confusion before the whole plan fell apart. "
            f"{'A nearby water source helped them top the bucket up again.' if world.facts.get('top_up') else 'Enough water stayed in the bucket once they moved more carefully.'}",
        ),
        (
            "What proves the story is resolved at the end?",
            f"The ending image proves it: {world.goal.ending_image}. "
            f"That final picture shows the misunderstanding is over and the backyard task is complete.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        (
            "Why can a nursery-rhyme chant help with a misunderstanding?",
            "A chant slows speech down and repeats the important words. That makes it easier for children to match what they heard with what they should do.",
        ),
        (
            "Why is carrying a bucket harder when someone rushes?",
            "A bucket swings and sloshes when feet move too quickly. Slower steps keep the water where it belongs.",
        ),
        (
            "Why can backyard sounds cause a mix-up?",
            "Backyards are full of chirps, clicks, and buzzing noises. A small sound can cover one syllable and change the meaning of a whole instruction.",
        ),
    ]
    if world.spot.hose:
        out.append(
            (
                "Why does a nearby hose or spigot make a gardening mistake easier to fix?",
                "Nearby water turns one spill into a delay instead of a disaster. The children can refill and try again without leaving the garden behind.",
            )
        )
    else:
        out.append(
            (
                "Why do children need extra care when there is no nearby refill in a garden story?",
                "Without a nearby refill, every splash matters more. That makes calm steps and clear words part of the solution.",
            )
        )
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
        bits = [f"kind={ent.kind}", f"type={ent.type}"]
        if ent.region:
            bits.append(f"region={ent.region}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} {' '.join(bits)}")
    lines.append(f"  top_up: {world.facts.get('top_up')}")
    lines.append(f"  resolved: {world.facts.get('resolved')}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("bucket_start", BUCKET_START))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id, spot.flatness, spot.shade, spot.hose, spot.echo))
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id, goal.thirst_need, goal.balance_need))
    for mixup_id, mixup in MIXUPS.items():
        lines.append(
            asp.fact(
                "mixup",
                mixup_id,
                mixup.water_loss,
                mixup.clarity_need,
                mixup.steady_risk,
                mixup.needs_refill,
            )
        )
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id, repair.pointing, repair.echo, repair.steady))
    return "\n".join(lines) + "\n"


ASP_RULES = r"""
valid(S, G, M, R) :-
    bucket_start(B),
    spot(S, Flat, Shade, Hose, SpotEcho),
    goal(G, Thirst, Balance),
    mixup(M, Loss, ClarityNeed, SteadyRisk, NeedsRefill),
    repair(R, Pointing, RepairEcho, RepairSteady),
    Clarity = SpotEcho + RepairEcho + Pointing,
    Clarity >= ClarityNeed,
    Steady = Flat + Shade + RepairSteady,
    Steady >= Balance + SteadyRisk,
    Hose >= NeedsRefill,
    WaterLeft = B - Loss + Hose,
    WaterLeft >= Thirst.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme misunderstanding story in a friend's backyard.")
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--goal", choices=sorted(GOALS))
    ap.add_argument("--mixup", choices=sorted(MIXUPS))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--visitor")
    ap.add_argument("--visitor-type", choices=list(CHILD_TYPES))
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=list(CHILD_TYPES))
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None, help="base seed for random choices")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible (spot, goal, mixup, repair) combinations")
    ap.add_argument("--verify", action="store_true", help="check Python vs inline ASP gate and sample stories")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        combo
        for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.goal is None or combo[1] == args.goal)
        and (args.mixup is None or combo[2] == args.mixup)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not candidates:
        raise StoryError(explain_rejection(args))

    spot_id, goal_id, mixup_id, repair_id = rng.choice(candidates)
    visitor_type = args.visitor_type or rng.choice(list(CHILD_TYPES))
    friend_type = args.friend_type or rng.choice(list(CHILD_TYPES))
    visitor = args.visitor or rng.choice(VISITOR_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if visitor == friend and not args.friend:
        friend = next(name for name in FRIEND_NAMES if name != visitor)
    return StoryParams(
        spot=spot_id,
        goal=goal_id,
        mixup=mixup_id,
        repair=repair_id,
        visitor=visitor,
        visitor_type=visitor_type,
        friend=friend,
        friend_type=friend_type,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if (params.spot, params.goal, params.mixup, params.repair) not in valid_combos():
        fake_args = argparse.Namespace(spot=params.spot, goal=params.goal, mixup=params.mixup, repair=params.repair)
        raise StoryError(explain_rejection(fake_args))
    world = build_story(
        SPOTS[params.spot],
        GOALS[params.goal],
        MIXUPS[params.mixup],
        REPAIRS[params.repair],
        params.visitor,
        params.visitor_type,
        params.friend,
        params.friend_type,
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
        print("")
        print(dump_trace(sample.world))
    if qa and sample.world is not None:
        print("")
        print(format_qa(sample))


def verify_samples() -> list[str]:
    errors: list[str] = []
    chosen = CURATED + [
        StoryParams(spot, goal, mixup, repair, "Pip", "child", "Nell", "child")
        for spot, goal, mixup, repair in valid_combos()[:8]
    ]
    seen: set[tuple[str, str, str, str, str, str, str, str]] = set()
    for params in chosen:
        key = (
            params.spot,
            params.goal,
            params.mixup,
            params.repair,
            params.visitor,
            params.visitor_type,
            params.friend,
            params.friend_type,
        )
        if key in seen:
            continue
        seen.add(key)
        sample = generate(params)
        story = sample.story.lower()
        if "sip" not in story:
            errors.append(f"story missing sip for {key[:4]}")
        if "bucket" not in story:
            errors.append(f"story missing bucket for {key[:4]}")
        if "friend's backyard" not in story:
            errors.append(f"story missing friend's backyard for {key[:4]}")
        if "misunderstanding" not in story:
            errors.append(f"story missing misunderstanding language for {key[:4]}")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            errors.append(f"missing prompts/qa for {key[:4]}")
        if any(token in sample.story for token in ["{", "}", "None", "meters", "memes", "id="]):
            errors.append(f"debug/template leak in story for {key[:4]}")
        if sample.world is not None and not sample.world.facts.get("resolved"):
            errors.append(f"world not resolved for {key[:4]}")
    return errors


def asp_verify() -> int:
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    status = 0
    if py_set == asp_set:
        print(f"OK: inline ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        status = 1
        print("MISMATCH between Python gate and inline ASP gate:")
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))

    sample_errors = verify_samples()
    if sample_errors:
        status = 1
        print("Sample verification failed:")
        for err in sample_errors:
            print(" ", err)
    else:
        print(f"OK: sampled {len(CURATED) + 8} exercised stories with grounded QA and required seed details.")
    return status


def _samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    limit = max(args.n * 60, 60)
    while len(samples) < args.n and attempts < limit:
        seed = base_seed + attempts
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        attempts += 1
    if len(samples) < args.n:
        raise StoryError(f"Only generated {len(samples)} distinct stories after {attempts} attempts.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, goal, mixup, repair) combinations:")
        for spot, goal, mixup, repair in combos:
            print(f"  {spot:14} {goal:14} {mixup:14} {repair}")
        return 0

    try:
        samples = _samples_from_args(args)
    except StoryError as exc:
        build_parser().error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples, 1):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.visitor} with {p.friend}: {p.mixup}/{p.goal}"
        elif len(samples) > 1:
            header = f"### variant {i} seed={sample.params.seed}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples):
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
