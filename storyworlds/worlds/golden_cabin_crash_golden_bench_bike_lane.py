#!/usr/bin/env python3
"""Nursery-rhyme storyworld about a crash on a bike lane by a golden cabin.

Seed:
    Words: golden cabin, crash, golden bench
    Setting: bike lane
    Features: Kindness, Sharing
    Style: Nursery Rhyme

Internal source tale:
    A child pedals from a golden cabin toward a golden bench on a bike lane.
    A friend crashes in a small but concrete way. The first child shares the
    one spare thing that fits the trouble, and the repaired ride ends with the
    children splitting a bun on the golden bench.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass(frozen=True)
class Lane:
    id: str
    label: str
    phrase: str
    cabin_scene: str
    bench_scene: str
    allows: set[str]
    tags: set[str]


@dataclass(frozen=True)
class CrashKind:
    id: str
    label: str
    sound: str
    cause: str
    result: str
    need: str
    tags: set[str]


@dataclass(frozen=True)
class ShareGift:
    id: str
    label: str
    phrase: str
    covers: set[str]
    action: str
    after: str
    material: str
    tags: set[str]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    region: str = ""
    owner: Optional[str] = None
    shared_with: Optional[str] = None
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return table[case]

    @property
    def phrase_for(self) -> str:
        return self.phrase or self.label


@dataclass
class World:
    params: "StoryParams"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    fired_names: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        text = text.strip()
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        lines = [
            f"lane: {self.params.lane}",
            f"crash: {self.params.crash}",
            f"share: {self.params.share}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for ent in self.entities.values():
            bits = [f"  {ent.id} | {ent.kind} | {ent.label}"]
            if ent.region:
                bits.append(f"region={ent.region}")
            if ent.owner:
                bits.append(f"owner={ent.owner}")
            if ent.shared_with:
                bits.append(f"shared_with={ent.shared_with}")
            lines.append(" | ".join(bits))
            if ent.meters:
                lines.append(f"    meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"    memes={dict(ent.memes)}")
        for key in sorted(self.facts):
            value = self.facts[key]
            if isinstance(value, Entity):
                lines.append(f"fact {key}={value.id}")
            elif hasattr(value, "id"):
                lines.append(f"fact {key}={getattr(value, 'id')}")
            else:
                lines.append(f"fact {key}={value}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_crash_alarm(world: World) -> list[str]:
    if not world.facts.get("crash_happened"):
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    friend_bike = world.get("friend_bike")
    if friend_bike.meters["wobble"] < THRESHOLD:
        return []
    if not _mark(world, "crash_alarm", hero.id, friend.id):
        return []
    hero.memes["concern"] += 1
    friend.memes["upset"] += 1
    return [
        f"{hero.label} hopped down at once, because a little crash can feel very big.",
        f"{friend.label} blinked hard, and even the bike lane seemed to hold its breath.",
    ]


def _r_shared_relief(world: World) -> list[str]:
    if not world.facts.get("help_shared"):
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    bench = world.get("bench")
    gift = SHARES[world.params.share]
    if not _mark(world, "shared_relief", hero.id, friend.id, gift.id):
        return []
    hero.memes["kindness"] += 1
    hero.memes["sharing"] += 1
    friend.memes["relief"] += 1
    friend.memes["trust"] += 1
    bench.memes["welcome"] += 1
    return [
        gift.after,
        f"{friend.label} smiled a little, because shared hands mend more than wheels and straps.",
    ]


def _r_ride_restored(world: World) -> list[str]:
    if world.get("friend_bike").meters["steady"] < THRESHOLD:
        return []
    if not _mark(world, "ride_restored", world.get("friend_bike").id):
        return []
    world.facts["ride_restored"] = True
    world.get("hero_bike").memes["calm"] += 1
    world.get("friend_bike").memes["calm"] += 1
    return ["Soon the rattly moment softened, and the ride found its rhyme again."]


CAUSAL_RULES = [
    Rule("crash_alarm", _r_crash_alarm),
    Rule("shared_relief", _r_shared_relief),
    Rule("ride_restored", _r_ride_restored),
]


def propagate(world: World, *, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


LANES: dict[str, Lane] = {
    "daisy_run": Lane(
        "daisy_run",
        "daisy run",
        "the bike lane from the golden cabin to the golden bench through the daisies",
        "The golden cabin glowed like warm toast at the edge of the lane.",
        "The golden bench waited ahead with bright arms in the sun.",
        {"pebble_skid", "basket_tumble"},
        {"bike_lane", "golden_cabin", "golden_bench", "daisies"},
    ),
    "reed_curve": Lane(
        "reed_curve",
        "reed curve",
        "the bike lane from the golden cabin to the golden bench by the silver reeds",
        "The golden cabin shone beside the reeds, snug as a song box.",
        "The golden bench rested near the turn where the reeds whispered.",
        {"puddle_splash", "basket_tumble"},
        {"bike_lane", "golden_cabin", "golden_bench", "reeds"},
    ),
    "chalk_turn": Lane(
        "chalk_turn",
        "chalk turn",
        "the bike lane from the golden cabin to the golden bench over chalky loops",
        "The golden cabin winked behind chalk stars drawn on the lane.",
        "The golden bench sat at the bend where chalk swirls made a ring.",
        {"pebble_skid", "puddle_splash"},
        {"bike_lane", "golden_cabin", "golden_bench", "chalk"},
    ),
}


CRASHES: dict[str, CrashKind] = {
    "pebble_skid": CrashKind(
        "pebble_skid",
        "pebble skid",
        "Skitter-clack, crash!",
        "A sprinkle of loose pebbles skipped under the front wheel.",
        "{friend}'s knee gave a sharp little sting, and the bike leaned sideways in the bike lane.",
        "knee_wrap",
        {"crash", "pebbles", "knee"},
    ),
    "basket_tumble": CrashKind(
        "basket_tumble",
        "basket tumble",
        "Bumpity-bump, crash!",
        "A jolt popped the basket clasp right at the wavy strip of lane.",
        "The basket flopped low, and two round apples rolled away from {friend}.",
        "basket_tie",
        {"crash", "basket", "apples"},
    ),
    "puddle_splash": CrashKind(
        "puddle_splash",
        "puddle splash",
        "Splish-splash, crash!",
        "A silver puddle slapped the tire, and the little picture map flew into the spray.",
        "Muddy drops dotted {friend}'s face, and the path to the bench blurred all at once.",
        "dry_wipe",
        {"crash", "puddle", "map"},
    ),
}


SHARES: dict[str, ShareGift] = {
    "sunny_scarf": ShareGift(
        "sunny_scarf",
        "sunny scarf",
        "a sunny scarf folded in the basket",
        {"knee_wrap"},
        "wrapped the sunny scarf softly around the sore knee",
        "The sting settled down enough for slow, brave pedals again.",
        "soft cloth",
        {"sharing", "kindness", "knee"},
    ),
    "golden_string": ShareGift(
        "golden_string",
        "golden string",
        "a coil of golden string tucked beside the bun",
        {"basket_tie"},
        "tied the basket snug again with the golden string",
        "The apples stopped rolling, and the basket rode straight once more.",
        "twine",
        {"sharing", "kindness", "basket"},
    ),
    "check_cloth": ShareGift(
        "check_cloth",
        "checkered cloth",
        "a checkered cloth folded under the bun",
        {"dry_wipe"},
        "dabbed the muddy map clear with the checkered cloth",
        "The splashes vanished, and the way to the golden bench showed up again.",
        "dry cloth",
        {"sharing", "kindness", "map"},
    ),
}


HERO_NAMES = ["Pip", "Mina", "Rory", "Tess", "Lulu", "Nico"]
FRIEND_NAMES = ["Jo", "Bea", "Finn", "Ivy", "Moss", "June"]


def valid_combo(lane: Lane, crash: CrashKind, share: ShareGift) -> bool:
    return crash.id in lane.allows and crash.need in share.covers


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lane in LANES.values():
        for crash in CRASHES.values():
            for share in SHARES.values():
                if valid_combo(lane, crash, share):
                    combos.append((lane.id, crash.id, share.id))
    return sorted(combos)


def explain_rejection(lane_id: str, crash_id: str, share_id: str) -> str:
    if lane_id not in LANES:
        return f"Unknown lane {lane_id!r}."
    if crash_id not in CRASHES:
        return f"Unknown crash {crash_id!r}."
    if share_id not in SHARES:
        return f"Unknown share item {share_id!r}."
    lane = LANES[lane_id]
    crash = CRASHES[crash_id]
    share = SHARES[share_id]
    if crash.id not in lane.allows:
        return f"{lane.label} does not plausibly lead to the {crash.label}."
    if crash.need not in share.covers:
        return f"{share.label} cannot honestly fix the trouble caused by the {crash.label}."
    return "The requested golden-cabin bike-lane story is not in the valid set."


def introduce(world: World, lane: Lane, hero: Entity, friend: Entity, gift: ShareGift) -> None:
    cabin = world.get("cabin")
    bench = world.get("bench")
    world.say(f"By the golden cabin rode {hero.label}, ding-ding bright, along {lane.phrase}.")
    world.say(lane.cabin_scene)
    world.say(
        f"In {hero.pronoun('possessive')} basket rested {gift.phrase} and one round pear bun "
        "saved for the golden bench."
    )
    world.say(f"{friend.label} pedaled behind, humming a tiny rhyme to the lane.")
    cabin.memes["homey"] += 1
    bench.memes["promise"] += 1


def crash_scene(world: World, lane: Lane, crash: CrashKind, friend: Entity) -> None:
    friend_bike = world.get("friend_bike")
    basket = world.get("basket")
    picture_map = world.get("map")
    world.para()
    world.say(crash.sound)
    world.say(crash.cause)
    world.say(crash.result.format(friend=friend.label))
    friend_bike.meters["wobble"] += 1
    world.facts["crash_happened"] = True
    if crash.need == "knee_wrap":
        friend.meters["sting"] += 1
    elif crash.need == "basket_tie":
        basket.meters["spill"] += 1
    elif crash.need == "dry_wipe":
        picture_map.meters["muddy"] += 1
    world.facts["problem_need"] = crash.need
    world.facts["lane_after_crash"] = lane.label
    world.say("The golden bench shone ahead, but nobody was ready to sit there yet.")
    propagate(world, narrate=True)


def share_help(world: World, hero: Entity, friend: Entity, crash: CrashKind, gift: ShareGift) -> None:
    if crash.need not in gift.covers:
        raise StoryError(f"{gift.label} cannot help after the {crash.label}.")
    basket = world.get("basket")
    picture_map = world.get("map")
    friend_bike = world.get("friend_bike")
    gift_ent = world.get("gift")
    world.para()
    world.say(f"{hero.label} did not keep the {gift.label} tucked away.")
    world.say(f"{hero.pronoun().capitalize()} shared it at once and {gift.action}.")
    gift_ent.shared_with = friend.id
    gift_ent.meters["given"] += 1
    gift_ent.memes["shared"] += 1
    world.facts["help_shared"] = True
    if crash.need == "knee_wrap":
        friend.meters["sting"] = max(0.0, friend.meters["sting"] - 1.0)
        friend.meters["bandaged"] += 1
    elif crash.need == "basket_tie":
        basket.meters["spill"] = 0.0
        basket.meters["mended"] += 1
    elif crash.need == "dry_wipe":
        picture_map.meters["muddy"] = 0.0
        picture_map.meters["clear"] += 1
    friend_bike.meters["steady"] += 1
    hero.memes["sharing_ready"] += 1
    propagate(world, narrate=True)


def ending(world: World, lane: Lane, hero: Entity, friend: Entity) -> None:
    bun = world.get("bun")
    bench = world.get("bench")
    world.para()
    world.say(f"Carefully they rolled on until the golden bench came under them at last.")
    if world.params.crash == "pebble_skid":
        proof = f"{friend.label}'s knee stayed wrapped, and the pedals turned in a soft little circle."
    elif world.params.crash == "basket_tumble":
        proof = "The apples rode quietly now, snug in the tied basket."
    else:
        proof = "The picture map lay clear again, with the bench drawn in a bright yellow square."
    world.say(proof)
    world.say(f"{hero.label} and {friend.label} split the pear bun in two and shared every crumb.")
    world.say(
        "Behind them the golden cabin glowed, ahead of them the bike lane hummed, "
        '"share and care, share and care."'
    )
    bun.meters["shared"] += 1
    bun.memes["togetherness"] += 1
    bench.meters["occupied"] += 1
    bench.memes["kindness_seen"] += 1
    world.facts["final_image"] = "children_on_golden_bench_sharing_bun"


def build_story(
    lane: Lane,
    crash: CrashKind,
    share: ShareGift,
    hero_name: str,
    friend_name: str,
    seed: Optional[int] = None,
) -> World:
    params = StoryParams(lane.id, crash.id, share.id, hero_name, friend_name, seed)
    world = World(params=params)
    hero = world.add(Entity("hero", "character", hero_name, phrase=hero_name))
    friend = world.add(Entity("friend", "character", friend_name, phrase=friend_name))
    world.add(Entity("cabin", "place", "golden cabin", phrase="the golden cabin", region="start"))
    world.add(Entity("bench", "place", "golden bench", phrase="the golden bench", region="end"))
    world.add(Entity("hero_bike", "thing", f"{hero_name}'s bike", region="lane", owner=hero.id))
    world.add(Entity("friend_bike", "thing", f"{friend_name}'s bike", region="lane", owner=friend.id))
    world.add(Entity("basket", "thing", "basket", region="front rack", owner=friend.id))
    world.add(Entity("gift", "thing", share.label, phrase=share.phrase, region="hero basket", owner=hero.id))
    world.add(Entity("bun", "thing", "pear bun", phrase="a pear bun", region="hero basket", owner=hero.id))
    world.add(Entity("map", "thing", "picture map", phrase="the picture map", region="friend pocket", owner=friend.id))

    world.facts.update(
        lane=lane,
        crash=crash,
        share=share,
        hero=hero,
        friend=friend,
    )

    introduce(world, lane, hero, friend, share)
    crash_scene(world, lane, crash, friend)
    share_help(world, hero, friend, crash, share)
    ending(world, lane, hero, friend)
    return world


@dataclass
class StoryParams:
    lane: str
    crash: str
    share: str
    hero: str
    friend: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("daisy_run", "pebble_skid", "sunny_scarf", "Pip", "Jo", 401),
    StoryParams("reed_curve", "basket_tumble", "golden_string", "Mina", "Bea", 402),
    StoryParams("chalk_turn", "puddle_splash", "check_cloth", "Rory", "Ivy", 403),
    StoryParams("daisy_run", "basket_tumble", "golden_string", "Tess", "Finn", 404),
]


def generation_prompts(world: World) -> list[str]:
    lane = LANES[world.params.lane]
    crash = CRASHES[world.params.crash]
    share = SHARES[world.params.share]
    return [
        'Write a nursery-rhyme story that includes "golden cabin", "crash", and "golden bench".',
        f"Set it on {lane.phrase} and let a {crash.label} interrupt the ride.",
        f"Make kindness concrete by sharing {share.label} before the children rest on the bench.",
    ]


KNOWLEDGE: dict[str, QAItem] = {
    "bike_lane": QAItem(
        "Why do riders slow down after a small crash in a bike lane?",
        "Riders slow down so they can check what is hurt or loose before moving again. A calm restart keeps a small problem from growing bigger.",
    ),
    "golden_bench": QAItem(
        "Why is a bench a good ending place in a child-sized story?",
        "A bench gives bodies a place to rest and lets readers see that the trouble has passed. It makes the change visible in one calm picture.",
    ),
    "golden_cabin": QAItem(
        "What does a cabin often add to a nursery-style story?",
        "A cabin can feel warm, close, and safe. It gives the journey a clear home place to begin from.",
    ),
    "knee_wrap": QAItem(
        "Why can a soft scarf help after a scraped knee?",
        "A soft scarf can protect the sore spot and make the child feel steadier. Gentle care also tells the hurt rider that someone is helping.",
    ),
    "basket_tie": QAItem(
        "Why does tying a basket matter after it comes loose?",
        "A tied basket keeps food and tools from tumbling into the lane again. Fixing the strap also makes the bike easier to steer.",
    ),
    "dry_wipe": QAItem(
        "Why is a dry cloth useful after a puddle splash?",
        "A dry cloth can clear mud and water from a face or a paper map. Seeing clearly again helps riders choose the safe way forward.",
    ),
    "sharing": QAItem(
        "What makes sharing feel kind in this world?",
        "Sharing matters because the useful thing is given at the moment it is needed. The gift changes from private comfort into shared repair.",
    ),
}


def story_qa(world: World) -> list[QAItem]:
    lane = LANES[world.params.lane]
    crash = CRASHES[world.params.crash]
    share = SHARES[world.params.share]
    hero = world.get("hero")
    friend = world.get("friend")
    qa = [
        QAItem(
            "Where did the story happen?",
            f"It happened on {lane.phrase}. The ride began by the golden cabin and finished at the golden bench.",
        ),
        QAItem(
            f"Why did {friend.label} crash?",
            f"{friend.label} crashed because {crash.cause.lower()} The sound '{crash.sound[:-1]}' was the beat that started the trouble.",
        ),
        QAItem(
            f"How did {hero.label} help after the crash?",
            f"{hero.label} shared the {share.label} right away. That gift fit the problem, so the upset moment could turn back into a steady ride.",
        ),
        QAItem(
            "What picture proves the story ends in kindness and sharing?",
            f"The ending picture is both children sitting on the golden bench and splitting one pear bun. That image shows the crash is over and the help became something shared.",
        ),
    ]
    if world.params.crash == "pebble_skid":
        qa.append(
            QAItem(
                "What changed after the scarf was shared?",
                f"{friend.label}'s knee stopped stinging so sharply, and the bike could move slowly again. The kindness changed pain into courage.",
            )
        )
    elif world.params.crash == "basket_tumble":
        qa.append(
            QAItem(
                "What changed after the string was shared?",
                "The basket stopped sagging and the apples stayed put. Fixing the strap made the ride neat and calm again.",
            )
        )
    else:
        qa.append(
            QAItem(
                "What changed after the cloth was shared?",
                "The muddy map became clear enough to read again. Once the path could be seen, the children could pedal forward without guessing.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    crash = CRASHES[world.params.crash]
    need_key = crash.need
    keys = ["bike_lane", "golden_cabin", "golden_bench", "sharing", need_key]
    seen: set[str] = set()
    items: list[QAItem] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        items.append(KNOWLEDGE[key])
    return items


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.friend:
        raise StoryError("Hero and friend must be different children.")
    if params.lane not in LANES or params.crash not in CRASHES or params.share not in SHARES:
        raise StoryError(explain_rejection(params.lane, params.crash, params.share))
    lane = LANES[params.lane]
    crash = CRASHES[params.crash]
    share = SHARES[params.share]
    if not valid_combo(lane, crash, share):
        raise StoryError(explain_rejection(params.lane, params.crash, params.share))
    world = build_story(lane, crash, share, params.hero, params.friend, params.seed)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(L,C,S) :- lane(L), crash(C), share(S), allows(L,C), needs(C,N), covers(S,N).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for lane in LANES.values():
        facts.append(asp.fact("lane", lane.id))
        for crash_id in lane.allows:
            facts.append(asp.fact("allows", lane.id, crash_id))
    for crash in CRASHES.values():
        facts.append(asp.fact("crash", crash.id))
        facts.append(asp.fact("needs", crash.id, crash.need))
    for share in SHARES.values():
        facts.append(asp.fact("share", share.id))
        for need in share.covers:
            facts.append(asp.fact("covers", share.id, need))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    combos: set[tuple[str, str, str]] = set()
    for model in asp.solve(asp_facts() + ASP_RULES):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(x) for x in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1
    for idx, (lane_id, crash_id, share_id) in enumerate(sorted(py), 1):
        params = StoryParams(
            lane=lane_id,
            crash=crash_id,
            share=share_id,
            hero=HERO_NAMES[(idx - 1) % len(HERO_NAMES)],
            friend=FRIEND_NAMES[(idx - 1) % len(FRIEND_NAMES)],
            seed=900 + idx,
        )
        sample = generate(params)
        if not sample.story.strip():
            print("Generated an empty story for", params)
            return 1
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
            print("Generated incomplete QA for", params)
            return 1
    print(f"OK: Python and ASP agree on {len(py)} valid golden-cabin bike-lane stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", choices=sorted(LANES))
    parser.add_argument("--crash", choices=sorted(CRASHES))
    parser.add_argument("--share", choices=sorted(SHARES))
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.lane is None or combo[0] == args.lane)
        and (args.crash is None or combo[1] == args.crash)
        and (args.share is None or combo[2] == args.share)
    ]
    if not choices:
        lane_id = args.lane or sorted(LANES)[0]
        crash_id = args.crash or sorted(CRASHES)[0]
        share_id = args.share or sorted(SHARES)[0]
        raise StoryError(explain_rejection(lane_id, crash_id, share_id))
    lane_id, crash_id, share_id = rng.choice(choices)
    hero = args.hero or rng.choice(HERO_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    if args.friend is not None:
        if args.friend == hero:
            raise StoryError("Hero and friend must be different children.")
        friend = args.friend
    else:
        friend = rng.choice(friend_choices)
    return StoryParams(lane_id, crash_id, share_id, hero, friend, args.seed)


def format_qa(title: str, items: list[QAItem]) -> list[str]:
    lines = [title]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    i = 0
    attempts = 0
    while len(samples) < target and attempts < target * 30:
        seed = base_seed + i
        i += 1
        attempts += 1
        local_args = argparse.Namespace(**vars(args))
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed))
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return 0
    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
        return 2
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0
    for idx, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = (
                "=== golden_cabin_crash_golden_bench_bike_lane "
                f"#{idx} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
