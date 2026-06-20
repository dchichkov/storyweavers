#!/usr/bin/env python3
"""
storyworlds/worlds/icy_cloud_friend_s_backyard_rhyme_kindness.py
================================================================

Comedy world: an icy cloud interrupts play in a friend's backyard until two
children answer it with rhyme and kindness.

The internal source tale is simple: a visiting child joins a friend in the
backyard for a silly project, a small icy cloud starts making cold trouble for
attention or comfort, the children notice what the cloud needs, and a matching
rhyming kindness act turns the cloud from nuisance into helper.
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


SAFE_SLIP_LIMIT = 2


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
    shelter: int
    open_space: int
    seat: int


@dataclass(frozen=True)
class PlayGoal:
    id: str
    phrase: str
    prop_phrase: str
    needs_open_space: int
    needs_seat: int
    cozy_bonus: int
    stage_bonus: int
    shared_bonus: int
    ending_hint: str


@dataclass(frozen=True)
class CloudTrouble:
    id: str
    intro: str
    comic_effect: str
    need_warmth: int
    need_welcome: int
    need_praise: int
    need_stage: int
    need_beat: int
    ice_risk: int
    resolution_image: str


@dataclass(frozen=True)
class RhymeMove:
    id: str
    label: str
    chant: str
    warmth: int
    welcome: int
    praise: int
    beat: int
    needs_open_space: int


@dataclass(frozen=True)
class KindAct:
    id: str
    label: str
    phrase: str
    warmth: int
    welcome: int
    praise: int
    melt: int
    needs_seat: int
    needs_shelter: int


@dataclass
class World:
    spot: BackyardSpot
    goal: PlayGoal
    cloud_trouble: CloudTrouble
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)

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

    def event(self, event_id: str, detail: str, result: str = "") -> None:
        self.history.append({"event": event_id, "detail": detail, "result": result})


SPOTS: dict[str, BackyardSpot] = {
    "birdbath_circle": BackyardSpot(
        "birdbath_circle",
        "the pebble circle around the birdbath in a friend's backyard",
        "a wobbling pink flamingo stake",
        shelter=0,
        open_space=1,
        seat=0,
    ),
    "apple_tree_nook": BackyardSpot(
        "apple_tree_nook",
        "the apple-tree nook in a friend's backyard",
        "a squeaky green lawn chair",
        shelter=1,
        open_space=1,
        seat=1,
    ),
    "shed_step": BackyardSpot(
        "shed_step",
        "the back step beside the red shed in a friend's backyard",
        "an upside-down bucket that looked like a tiny drum",
        shelter=1,
        open_space=0,
        seat=1,
    ),
    "patio_patch": BackyardSpot(
        "patio_patch",
        "the patchwork patio in a friend's backyard",
        "a striped umbrella table",
        shelter=2,
        open_space=0,
        seat=1,
    ),
}


GOALS: dict[str, PlayGoal] = {
    "bug_parade": PlayGoal(
        "bug_parade",
        "march bottle-cap beetles in a bug parade",
        "a shoebox drum for the parade",
        needs_open_space=0,
        needs_seat=0,
        cozy_bonus=0,
        stage_bonus=1,
        shared_bonus=1,
        ending_hint="the bug parade route glittered like a silver ribbon",
    ),
    "cardboard_castle": PlayGoal(
        "cardboard_castle",
        "build a cardboard castle for a plush dragon",
        "a cereal-box tower with crooked windows",
        needs_open_space=0,
        needs_seat=0,
        cozy_bonus=1,
        stage_bonus=0,
        shared_bonus=1,
        ending_hint="the cardboard castle wore a neat frosting of sparkly trim",
    ),
    "bubble_concert": PlayGoal(
        "bubble_concert",
        "stage a bubble concert with pans and spoons",
        "a saucepan cymbal and a soap tray",
        needs_open_space=1,
        needs_seat=0,
        cozy_bonus=0,
        stage_bonus=1,
        shared_bonus=1,
        ending_hint="the bubbles rose in tidy rows above the backyard concert",
    ),
    "muffin_picnic": PlayGoal(
        "muffin_picnic",
        "set out a muffin picnic on a checked towel",
        "a plate of banana muffins",
        needs_open_space=0,
        needs_seat=1,
        cozy_bonus=1,
        stage_bonus=0,
        shared_bonus=1,
        ending_hint="the picnic towel stayed dry while the muffins smelled warm",
    ),
}


CLOUDS: dict[str, CloudTrouble] = {
    "shivery": CloudTrouble(
        "shivery",
        "A tiny icy cloud trembled over the fence and sneezed bead-sized ice onto everything below.",
        "It made the flamingo look as if it had accidentally put on a frozen mustache.",
        need_warmth=3,
        need_welcome=1,
        need_praise=0,
        need_stage=0,
        need_beat=0,
        ice_risk=3,
        resolution_image="the icy cloud sighed out a soft silver mist instead of sharp ice",
    ),
    "lonely": CloudTrouble(
        "lonely",
        "A small icy cloud drooped low because it hated being left out of the backyard fun.",
        "Whenever the children whispered, it slid closer and dropped chilly confetti on their project.",
        need_warmth=1,
        need_welcome=3,
        need_praise=0,
        need_stage=0,
        need_beat=0,
        ice_risk=2,
        resolution_image="the icy cloud floated beside them like a polite silver balloon",
    ),
    "showoff": CloudTrouble(
        "showoff",
        "A proud icy cloud hovered overhead and kept tossing glittery frost loops whenever anyone looked away.",
        "It clearly wanted applause, even if the audience was only two children and one confused ladybug.",
        need_warmth=0,
        need_welcome=1,
        need_praise=3,
        need_stage=1,
        need_beat=1,
        ice_risk=2,
        resolution_image="the icy cloud twirled neat frost curls on cue instead of pelting the yard",
    ),
}


RHYMES: dict[str, RhymeMove] = {
    "clap_chant": RhymeMove(
        "clap_chant",
        "a clap chant",
        '"Cloud so bright, freeze polite; share our game and float just right!"',
        warmth=0,
        welcome=1,
        praise=1,
        beat=1,
        needs_open_space=0,
    ),
    "bucket_beat": RhymeMove(
        "bucket_beat",
        "a bucket beat rhyme",
        '"Ping on the pail, no icy hail; dance with our joke and wag your tail!"',
        warmth=0,
        welcome=0,
        praise=2,
        beat=1,
        needs_open_space=0,
    ),
    "jumprope_jingle": RhymeMove(
        "jumprope_jingle",
        "a jump-rope jingle",
        '"Skip in, cloud, do not be loud; hop with our yard and make us proud!"',
        warmth=0,
        welcome=2,
        praise=0,
        beat=1,
        needs_open_space=1,
    ),
    "soft_couplet": RhymeMove(
        "soft_couplet",
        "a soft couplet",
        '"Little icy cloud, you look cold but brave; come by our chair and behave."',
        warmth=1,
        welcome=1,
        praise=0,
        beat=0,
        needs_open_space=0,
    ),
}


KINDNESS_ACTS: dict[str, KindAct] = {
    "share_scarf": KindAct(
        "share_scarf",
        "share a scarf",
        "looped a long scarf around the fence like a tiny warm swing for the cloud",
        warmth=2,
        welcome=1,
        praise=0,
        melt=1,
        needs_seat=0,
        needs_shelter=0,
    ),
    "offer_cocoa": KindAct(
        "offer_cocoa",
        "offer cocoa steam",
        "held up a mug so the cocoa steam could kiss the cold air",
        warmth=2,
        welcome=1,
        praise=0,
        melt=2,
        needs_seat=0,
        needs_shelter=1,
    ),
    "save_a_seat": KindAct(
        "save_a_seat",
        "save a seat",
        "pulled out the driest chair and saved a place for the cloud to hover beside them",
        warmth=0,
        welcome=2,
        praise=1,
        melt=0,
        needs_seat=1,
        needs_shelter=0,
    ),
    "cheer_the_cloud": KindAct(
        "cheer_the_cloud",
        "cheer the cloud",
        "told the cloud that its silver swirls looked like a dancer in shiny socks",
        warmth=0,
        welcome=1,
        praise=2,
        melt=0,
        needs_seat=0,
        needs_shelter=0,
    ),
}


VISITOR_NAMES = ["June", "Milo", "Tess", "Rafi", "Sana", "Luca", "Pip", "Nia"]
FRIEND_NAMES = ["Bea", "Otis", "Wren", "Kiki", "Noah", "Ivy", "Jules", "Max"]


@dataclass
class StoryParams:
    spot: str
    goal: str
    cloud: str
    rhyme: str
    kindness: str
    visitor: str
    visitor_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("apple_tree_nook", "cardboard_castle", "shivery", "soft_couplet", "share_scarf", "June", "girl", "Otis", "boy"),
    StoryParams("patio_patch", "muffin_picnic", "lonely", "clap_chant", "save_a_seat", "Nia", "girl", "Bea", "girl"),
    StoryParams("birdbath_circle", "bubble_concert", "showoff", "jumprope_jingle", "cheer_the_cloud", "Milo", "boy", "Ivy", "girl"),
    StoryParams("shed_step", "bug_parade", "showoff", "bucket_beat", "save_a_seat", "Rafi", "boy", "Kiki", "girl"),
]


def support_levels(
    spot: BackyardSpot,
    goal: PlayGoal,
    rhyme: RhymeMove,
    kindness: KindAct,
) -> dict[str, int]:
    return {
        "warmth": spot.shelter + goal.cozy_bonus + rhyme.warmth + kindness.warmth,
        "welcome": goal.shared_bonus + rhyme.welcome + kindness.welcome,
        "praise": goal.stage_bonus + rhyme.praise + kindness.praise,
        "stage": goal.stage_bonus,
        "beat": rhyme.beat,
        "slip": max(0, spot.shelter + kindness.melt),
    }


def reasonableness_report(
    spot: BackyardSpot,
    goal: PlayGoal,
    cloud: CloudTrouble,
    rhyme: RhymeMove,
    kindness: KindAct,
) -> tuple[bool, str]:
    if spot.open_space < goal.needs_open_space:
        return False, f"{goal.phrase.capitalize()} needs more open space than {spot.phrase} offers."
    if spot.open_space < rhyme.needs_open_space:
        return False, f"{rhyme.label.capitalize()} needs room to move, but {spot.phrase} is too cramped."
    if spot.seat < goal.needs_seat:
        return False, f"{goal.phrase.capitalize()} needs a seat or table, and {spot.phrase} does not have one."
    if spot.seat < kindness.needs_seat:
        return False, f"{kindness.label.capitalize()} needs a dry seat, and {spot.phrase} has nowhere suitable."
    if spot.shelter < kindness.needs_shelter:
        return False, f"{kindness.label.capitalize()} works only with some shelter, and {spot.phrase} is too exposed."

    support = support_levels(spot, goal, rhyme, kindness)
    remaining_slip = cloud.ice_risk - support["slip"]
    if support["warmth"] < cloud.need_warmth:
        return False, f"The icy cloud stays too cold for {kindness.label} and {rhyme.label} to calm it."
    if support["welcome"] < cloud.need_welcome:
        return False, "The children do not make the cloud feel included enough."
    if support["praise"] < cloud.need_praise:
        return False, "The cloud wants more applause than this plan provides."
    if support["stage"] < cloud.need_stage:
        return False, f"{cloud.id.capitalize()} cloud trouble needs a showy activity, and {goal.phrase} is too quiet."
    if support["beat"] < cloud.need_beat:
        return False, f"{cloud.id.capitalize()} cloud trouble needs a stronger rhythm to answer its antics."
    if remaining_slip > SAFE_SLIP_LIMIT:
        return False, "Too much icy clutter would stay on the ground, so the backyard scene would not feel safe."
    return True, "ok"


def is_reasonable_story(
    spot: BackyardSpot,
    goal: PlayGoal,
    cloud: CloudTrouble,
    rhyme: RhymeMove,
    kindness: KindAct,
) -> bool:
    ok, _ = reasonableness_report(spot, goal, cloud, rhyme, kindness)
    return ok


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for spot_id, spot in SPOTS.items():
        for goal_id, goal in GOALS.items():
            for cloud_id, cloud in CLOUDS.items():
                for rhyme_id, rhyme in RHYMES.items():
                    for kindness_id, kindness in KINDNESS_ACTS.items():
                        if is_reasonable_story(spot, goal, cloud, rhyme, kindness):
                            combos.append((spot_id, goal_id, cloud_id, rhyme_id, kindness_id))
    return sorted(combos)


def label(word: str) -> str:
    return word.replace("_", " ")


def introduce(world: World, visitor: Entity, friend: Entity, yard: Entity, goal: PlayGoal) -> None:
    world.say(
        f"Once upon a time, {visitor.label} went to {friend.label}'s house to play in a friend's backyard. "
        f"They settled into {world.spot.phrase} with {world.spot.prop_phrase} nearby."
    )
    world.say(
        f"{friend.label} wanted to {goal.phrase}, and {visitor.label} said yes so fast that {visitor.pronoun('possessive')} shoelace bounced."
    )
    world.event("premise", f"{visitor.label} joined {friend.label} in the backyard.", goal.phrase)
    yard.memes["friendship"] += 1


def start_trouble(world: World, visitor: Entity, friend: Entity, cloud: Entity, ground: Entity, goal: PlayGoal) -> None:
    world.say(world.cloud_trouble.intro)
    world.say(world.cloud_trouble.comic_effect)
    world.say(
        f"It kept interrupting while the children tried to {goal.phrase}, and soon tiny ice taps were bouncing off {goal.prop_phrase}."
    )
    world.event("trouble", world.cloud_trouble.id, world.cloud_trouble.comic_effect)
    ground.meters["slip_risk"] += world.cloud_trouble.ice_risk
    cloud.meters["cold"] += world.cloud_trouble.need_warmth + 1
    cloud.memes["belonging_gap"] += world.cloud_trouble.need_welcome
    cloud.memes["attention_gap"] += world.cloud_trouble.need_praise
    visitor.memes["surprise"] += 1
    friend.memes["surprise"] += 1


def notice_need(world: World, visitor: Entity, friend: Entity, cloud: Entity) -> None:
    if world.cloud_trouble.id == "shivery":
        world.say(
            f'"That cloud is not mean," {friend.label} whispered. "It looks as if it is cold all the way to its puffy knees."'
        )
    elif world.cloud_trouble.id == "lonely":
        world.say(
            f'"Maybe it keeps butting in because nobody invited it," {visitor.label} guessed after watching it hover close to them.'
        )
    else:
        world.say(
            f'"It is showing off," {friend.label} said, "but maybe it would stop if we gave it a proper audience."'
        )
    cloud.memes["noticed"] += 1
    world.event("diagnosis", world.cloud_trouble.id, "The children guessed what the cloud needed.")


def perform_turn(
    world: World,
    visitor: Entity,
    friend: Entity,
    cloud: Entity,
    ground: Entity,
    rhyme: RhymeMove,
    kindness: KindAct,
) -> None:
    support = support_levels(world.spot, world.goal, rhyme, kindness)
    world.say(
        f"So {visitor.label} and {friend.label} answered with {rhyme.label}. Together they sang, {rhyme.chant}"
    )
    world.say(
        f"Then {friend.label} and {visitor.label} {kindness.phrase}. The whole moment felt silly, but it also felt gentle."
    )
    visitor.memes["kindness"] += kindness.welcome + kindness.warmth + 1
    friend.memes["kindness"] += kindness.welcome + kindness.warmth + 1
    visitor.memes["joy"] += rhyme.beat + 1
    friend.memes["joy"] += rhyme.beat + 1
    cloud.meters["cold"] = max(0, cloud.meters["cold"] - support["warmth"])
    cloud.memes["belonging_gap"] = max(0, cloud.memes["belonging_gap"] - support["welcome"])
    cloud.memes["attention_gap"] = max(0, cloud.memes["attention_gap"] - support["praise"])
    cloud.memes["rhythm_soothed"] += support["beat"]
    ground.meters["slip_risk"] = max(0, ground.meters["slip_risk"] - support["slip"])
    world.facts["support"] = support
    world.event("turn", rhyme.id, kindness.id)


def settle_cloud(world: World, cloud: Entity, ground: Entity) -> None:
    support = world.facts["support"]
    calmed = (
        cloud.meters["cold"] <= 1
        and cloud.memes["belonging_gap"] <= 0
        and cloud.memes["attention_gap"] <= 0
        and support["beat"] >= world.cloud_trouble.need_beat
    )
    safe = ground.meters["slip_risk"] <= SAFE_SLIP_LIMIT
    world.facts["calmed"] = calmed
    world.facts["safe"] = safe
    if not calmed or not safe:
        raise StoryError("The chosen rhyme and kindness plan failed to calm the icy cloud cleanly.")

    cloud.memes["trust"] += 2
    cloud.memes["joy"] += 2
    ground.memes["comfort"] += 1
    world.say(
        f"After that, {world.cloud_trouble.resolution_image}. The ice stopped coming down in rude little pecks."
    )
    if world.cloud_trouble.id == "shivery":
        world.say("The cloud tucked itself near the warm air and looked proud instead of miserable.")
    elif world.cloud_trouble.id == "lonely":
        world.say("It stayed close, but now it waited for the children's giggles before it moved.")
    else:
        world.say("Now each frosty twirl happened exactly when the children clapped, which made the whole backyard feel like a tiny stage.")
    world.event("resolution_shift", world.cloud_trouble.id, "The cloud switched from nuisance to helper.")


def finish_story(world: World, visitor: Entity, friend: Entity, cloud: Entity, ground: Entity, goal: PlayGoal) -> None:
    visitor.memes["friendship"] += 2
    friend.memes["friendship"] += 2
    cloud.memes["belonging"] += 2
    if goal.id == "cardboard_castle":
        world.say(
            f"Soon {goal.ending_hint}. {friend.label}'s plush dragon got a frosty crown, and even {visitor.label} had to laugh at how royal the box looked."
        )
    elif goal.id == "bubble_concert":
        world.say(
            f"Soon {goal.ending_hint}. Each bubble wobbled past the icy cloud, and the cloud puffed them upward as if it were bowing to the music."
        )
    elif goal.id == "bug_parade":
        world.say(
            f"Soon {goal.ending_hint}. The ladybug in the grass looked like a grand marshal, which made both children snort with laughter."
        )
    else:
        world.say(
            f"Soon {goal.ending_hint}. The icy cloud hovered like a chilly umbrella, and not one muffin received another icy bonk."
        )
    world.say(
        f"By the end, {visitor.label} and {friend.label} knew that the best way to handle a silly problem was to be kind first and clever second."
    )
    world.facts["ending_image"] = goal.ending_hint
    world.event("ending", goal.id, goal.ending_hint)
    ground.memes["peace"] += 1


def build_story(
    spot: BackyardSpot,
    goal: PlayGoal,
    cloud_trouble: CloudTrouble,
    rhyme: RhymeMove,
    kindness: KindAct,
    visitor_name: str,
    visitor_type: str,
    friend_name: str,
    friend_type: str,
) -> World:
    ok, reason = reasonableness_report(spot, goal, cloud_trouble, rhyme, kindness)
    if not ok:
        raise StoryError(reason)

    world = World(spot=spot, goal=goal, cloud_trouble=cloud_trouble)
    visitor = world.add(Entity(visitor_name, kind="character", type=visitor_type, label=visitor_name, phrase=visitor_name))
    friend = world.add(Entity(friend_name, kind="character", type=friend_type, label=friend_name, phrase=friend_name))
    cloud = world.add(Entity("cloud", kind="thing", type="icy_cloud", label="the icy cloud", phrase="the icy cloud", region=spot.id))
    yard = world.add(Entity("yard", kind="thing", type="backyard", label="the backyard", phrase=spot.phrase, region=spot.id))
    ground = world.add(Entity("ground", kind="thing", type="ground", label="the backyard ground", phrase="the backyard ground", region=spot.id))
    prop = world.add(Entity("prop", kind="thing", type="play_prop", label=goal.prop_phrase, phrase=goal.prop_phrase, owner=friend.id, region=spot.id))
    prop.memes["play"] += 1

    world.facts.update(
        visitor=visitor,
        friend=friend,
        cloud=cloud,
        yard=yard,
        ground=ground,
        prop=prop,
        rhyme=rhyme,
        kindness=kindness,
        spot=spot,
        goal=goal,
        cloud_trouble=cloud_trouble,
    )

    introduce(world, visitor, friend, yard, goal)
    world.para()
    start_trouble(world, visitor, friend, cloud, ground, goal)
    notice_need(world, visitor, friend, cloud)
    world.para()
    perform_turn(world, visitor, friend, cloud, ground, rhyme, kindness)
    settle_cloud(world, cloud, ground)
    world.para()
    finish_story(world, visitor, friend, cloud, ground, goal)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly comedy about an icy cloud causing trouble in a friend's backyard.",
        f"Use rhyme and kindness to solve a problem while two children try to {f['goal'].phrase}.",
        f"Keep the ending concrete by showing how the icy cloud changes around {f['spot'].phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    visitor: Entity = f["visitor"]
    friend: Entity = f["friend"]
    goal: PlayGoal = f["goal"]
    spot: BackyardSpot = f["spot"]
    cloud_trouble: CloudTrouble = f["cloud_trouble"]
    rhyme: RhymeMove = f["rhyme"]
    kindness: KindAct = f["kindness"]
    return [
        (
            "Where does the story happen?",
            f"It happens in {spot.phrase}. That backyard setting matters because the children use the things around them to help the cloud.",
        ),
        (
            "What problem did the icy cloud cause?",
            f"The icy cloud kept interrupting while the children tried to {goal.phrase}. "
            f"Because of its {cloud_trouble.id} mood, it dropped cold little bits or frosty tricks onto their project.",
        ),
        (
            "How did the children help the cloud?",
            f"They answered with {rhyme.label} and then chose to {kindness.label}. "
            f"That worked because the rhyme gave the cloud attention and the kind act gave it the warmth or welcome it was missing.",
        ),
        (
            "Why did the plan work?",
            f"The plan worked because it met the cloud's real need instead of only chasing it away. "
            f"The children gave it warmth, welcome, or praise in a way the backyard could support, so the trouble turned into cooperation.",
        ),
        (
            "What changed by the end?",
            f"By the end, the cloud was calm and the ground felt safe enough for play. "
            f"The final image shows that change: {f['ending_image']}, and the children could finish their game together.",
        ),
        (
            "What do the rhyme and kindness reveal about the children?",
            f"They show that {visitor.label} and {friend.label} are playful, observant, and gentle. "
            f"The rhyme kept them working together, and the kind act showed they wanted to help the cloud instead of mocking it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    goal: PlayGoal = f["goal"]
    rhyme: RhymeMove = f["rhyme"]
    kindness: KindAct = f["kindness"]
    cloud_trouble: CloudTrouble = f["cloud_trouble"]
    out = [
        (
            "Why can rhyme calm a silly argument or mix-up in a children's story?",
            "Rhyme gives people a shared rhythm to follow. That can turn scattered feelings into one playful action.",
        ),
        (
            f"What kind of problem does a {cloud_trouble.id} icy cloud usually have in this world?",
            f"A {cloud_trouble.id} icy cloud is not only cold; it is also missing the right kind of care or attention. "
            f"In this world, children solve that by matching the cloud's need instead of scolding it.",
        ),
        (
            f"Why is {kindness.label} a strong choice in a backyard story?",
            f"{kindness.label.capitalize()} uses something immediate and child-sized. "
            f"It changes the mood without making the children stop being kind or imaginative.",
        ),
        (
            f"What does {rhyme.label} add to backyard play?",
            f"{rhyme.label.capitalize()} adds rhythm, memory, and group timing. "
            f"That makes it easier for two children to act together instead of panicking separately.",
        ),
        (
            f"Why is {goal.phrase} funny with an icy cloud nearby?",
            f"It mixes an ordinary backyard plan with a very silly weather guest. "
            f"That contrast creates comedy while still keeping the problem small enough for children to solve.",
        ),
    ]
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
    lines.append(f"  support: {world.facts.get('support')}")
    lines.append(f"  calmed: {world.facts.get('calmed')}")
    lines.append(f"  safe: {world.facts.get('safe')}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id, spot.shelter, spot.open_space, spot.seat))
    for goal_id, goal in GOALS.items():
        lines.append(
            asp.fact(
                "goal",
                goal_id,
                goal.needs_open_space,
                goal.needs_seat,
                goal.cozy_bonus,
                goal.stage_bonus,
                goal.shared_bonus,
            )
        )
    for cloud_id, cloud in CLOUDS.items():
        lines.append(
            asp.fact(
                "cloud",
                cloud_id,
                cloud.need_warmth,
                cloud.need_welcome,
                cloud.need_praise,
                cloud.need_stage,
                cloud.need_beat,
                cloud.ice_risk,
            )
        )
    for rhyme_id, rhyme in RHYMES.items():
        lines.append(
            asp.fact(
                "rhyme",
                rhyme_id,
                rhyme.warmth,
                rhyme.welcome,
                rhyme.praise,
                rhyme.beat,
                rhyme.needs_open_space,
            )
        )
    for kindness_id, kindness in KINDNESS_ACTS.items():
        lines.append(
            asp.fact(
                "kindness",
                kindness_id,
                kindness.warmth,
                kindness.welcome,
                kindness.praise,
                kindness.melt,
                kindness.needs_seat,
                kindness.needs_shelter,
            )
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, C, R, K) :-
    spot(S, Shelter, Open, Seat),
    goal(G, GoalOpen, GoalSeat, Cozy, Stage, Shared),
    cloud(C, NeedWarm, NeedWelcome, NeedPraise, NeedStage, NeedBeat, IceRisk),
    rhyme(R, RWarm, RWelcome, RPraise, Beat, ROpen),
    kindness(K, KWarm, KWelcome, KPraise, Melt, KSeat, KShelter),
    Open >= GoalOpen,
    Open >= ROpen,
    Seat >= GoalSeat,
    Seat >= KSeat,
    Shelter >= KShelter,
    Warmth = Shelter + Cozy + RWarm + KWarm,
    Welcome = Shared + RWelcome + KWelcome,
    Praise = Stage + RPraise + KPraise,
    SlipHelp = Shelter + Melt,
    Warmth >= NeedWarm,
    Welcome >= NeedWelcome,
    Praise >= NeedPraise,
    Stage >= NeedStage,
    Beat >= NeedBeat,
    IceRisk - SlipHelp <= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Kind comedy about an icy cloud in a friend's backyard.")
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--cloud", choices=CLOUDS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--kindness", choices=KINDNESS_ACTS)
    ap.add_argument("--visitor")
    ap.add_argument("--visitor-type", choices=["girl", "boy", "child"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy", "child"])
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None, help="base seed for random choices")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible (spot, goal, cloud, rhyme, kindness) combos")
    ap.add_argument("--verify", action="store_true", help="check Python vs inline ASP gate and sample stories")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap


def explain_rejection(args: argparse.Namespace) -> str:
    if not all([args.spot, args.goal, args.cloud, args.rhyme, args.kindness]):
        return "(No valid combinations match the requested options.)"
    ok, reason = reasonableness_report(
        SPOTS[args.spot],
        GOALS[args.goal],
        CLOUDS[args.cloud],
        RHYMES[args.rhyme],
        KINDNESS_ACTS[args.kindness],
    )
    if ok:
        return "(No valid combinations match the requested options.)"
    return f"(No story: {reason})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        c for c in valid_combos()
        if (args.spot is None or c[0] == args.spot)
        and (args.goal is None or c[1] == args.goal)
        and (args.cloud is None or c[2] == args.cloud)
        and (args.rhyme is None or c[3] == args.rhyme)
        and (args.kindness is None or c[4] == args.kindness)
    ]
    if not candidates:
        raise StoryError(explain_rejection(args))

    spot_id, goal_id, cloud_id, rhyme_id, kindness_id = rng.choice(candidates)
    visitor_type = args.visitor_type or rng.choice(["girl", "boy", "child"])
    friend_type = args.friend_type or rng.choice(["girl", "boy", "child"])
    visitor = args.visitor or rng.choice(VISITOR_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if visitor == friend and not args.friend:
        friend = next(name for name in FRIEND_NAMES if name != visitor)
    return StoryParams(
        spot_id,
        goal_id,
        cloud_id,
        rhyme_id,
        kindness_id,
        visitor,
        visitor_type,
        friend,
        friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(
        SPOTS[params.spot],
        GOALS[params.goal],
        CLOUDS[params.cloud],
        RHYMES[params.rhyme],
        KINDNESS_ACTS[params.kindness],
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
        StoryParams(spot, goal, cloud, rhyme, kindness, "Tess", "girl", "Max", "boy")
        for spot, goal, cloud, rhyme, kindness in valid_combos()[:6]
    ]
    seen: set[tuple[str, str, str, str, str]] = set()
    for params in chosen:
        key = (params.spot, params.goal, params.cloud, params.rhyme, params.kindness)
        if key in seen:
            continue
        seen.add(key)
        sample = generate(params)
        story = sample.story
        if "icy cloud" not in story.lower():
            errors.append(f"story missing icy cloud for {key}")
        if "friend's backyard" not in story.lower():
            errors.append(f"story missing friend's backyard for {key}")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            errors.append(f"missing QA/prompts for {key}")
        if any(token in story for token in ["{", "}", "None", "meters", "memes"]):
            errors.append(f"debug/template leak in story for {key}")
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
        print(f"OK: sampled {len(CURATED) + 6} exercised stories with grounded QA and required seed details.")
    return status


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, goal, cloud, rhyme, kindness) combinations:")
        for spot, goal, cloud, rhyme, kindness in combos:
            print(f"  {spot:16} {goal:18} {cloud:10} {rhyme:16} {kindness}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 60, 60):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.visitor} with {p.friend}: {p.cloud}/{p.goal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
