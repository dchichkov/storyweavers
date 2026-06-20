#!/usr/bin/env python3
"""Nursery-rhyme storyworld about a bike-lane crash by a golden cabin.

Seed:
    Words: golden cabin, crash, golden bench
    Setting: bike lane
    Features: Kindness, Sharing
    Style: Nursery Rhyme

Internal source tale:
    A child rides from a golden cabin toward a golden bench on a little bike
    lane. A friend has a small crash from a concrete lane hazard. The first
    child shares the one spare thing that truly fits the trouble, and the ride
    ends with both children sharing an oat cake on the golden bench.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass(frozen=True)
class Route:
    id: str
    label: str
    phrase: str
    cabin_detail: str
    lane_detail: str
    bench_detail: str
    allows: frozenset[str]
    tags: frozenset[str]


@dataclass(frozen=True)
class CrashMode:
    id: str
    label: str
    sound: str
    cause: str
    result: str
    need: str
    proof: str
    tags: frozenset[str]


@dataclass(frozen=True)
class ShareItem:
    id: str
    label: str
    phrase: str
    handles: frozenset[str]
    action: str
    reason: str
    effect: str
    material: str
    tags: frozenset[str]


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
class StoryParams:
    route: str
    crash: str
    share: str
    hero: str
    friend: str
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    history: list[dict[str, str]] = field(default_factory=list)
    fired: set[tuple[object, ...]] = field(default_factory=set)
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

    def note(self, event: str, **fields: str) -> None:
        row = {"event": event}
        row.update(fields)
        self.history.append(row)

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

    def trace(self) -> str:
        lines = [
            f"route: {self.params.route}",
            f"crash: {self.params.crash}",
            f"share: {self.params.share}",
            f"hero: {self.params.hero}",
            f"friend: {self.params.friend}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for ent in self.entities.values():
            parts = [f"{ent.id} | {ent.kind} | {ent.label}"]
            if ent.region:
                parts.append(f"region={ent.region}")
            if ent.owner:
                parts.append(f"owner={ent.owner}")
            if ent.shared_with:
                parts.append(f"shared_with={ent.shared_with}")
            lines.append(" | ".join(parts))
            if ent.meters:
                lines.append(f"  meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"  memes={dict(ent.memes)}")
        for item in self.history:
            bits = [f"{key}={value}" for key, value in item.items()]
            lines.append("history: " + ", ".join(bits))
        for key in sorted(self.facts):
            value = self.facts[key]
            if hasattr(value, "id"):
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


def _r_lane_hush(world: World) -> list[str]:
    if not world.facts.get("crash_happened"):
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    friend_bike = world.get("friend_bike")
    lane = world.get("lane")
    if friend_bike.meters["wobble"] < THRESHOLD:
        return []
    if not _mark(world, "lane_hush", hero.id, friend.id):
        return []
    hero.memes["concern"] += 1.0
    friend.memes["worry"] += 1.0
    lane.memes["hush"] += 1.0
    world.note(
        "lane_hush",
        watcher=hero.label,
        rider=friend.label,
        mood="the lane went quiet after the crash",
    )
    return [
        f"{hero.label} hopped off at once, because even a tiny crash can feel loud in a small heart.",
        "The bike lane seemed to hush and listen while the wheels gave one last wobble."
    ]


def _r_shared_comfort(world: World) -> list[str]:
    if not world.facts.get("help_shared"):
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    bench = world.get("bench")
    gift = SHARES[world.params.share]
    if not _mark(world, "shared_comfort", hero.id, friend.id, gift.id):
        return []
    hero.memes["kindness"] += 1.0
    hero.memes["sharing"] += 1.0
    friend.memes["relief"] += 1.0
    friend.memes["trust"] += 1.0
    bench.memes["welcome"] += 1.0
    world.note(
        "shared_comfort",
        sharer=hero.label,
        recipient=friend.label,
        item=gift.label,
        result="sharing turned fright into relief",
    )
    return [
        gift.effect,
        f"{friend.label} breathed more softly, because shared help can steady more than handlebars."
    ]


def _r_ride_restored(world: World) -> list[str]:
    friend_bike = world.get("friend_bike")
    if friend_bike.meters["steady"] < THRESHOLD:
        return []
    if not _mark(world, "ride_restored", friend_bike.id):
        return []
    friend_bike.meters["wobble"] = 0.0
    friend_bike.memes["calm"] += 1.0
    world.get("hero_bike").memes["calm"] += 1.0
    world.facts["ride_restored"] = True
    world.note(
        "ride_restored",
        rider=world.get("friend").label,
        proof="the bicycle could roll in a straight little line again",
    )
    return [
        "Soon the sharp moment softened, and the ride found its nursery beat again."
    ]


CAUSAL_RULES = [
    Rule("lane_hush", _r_lane_hush),
    Rule("shared_comfort", _r_shared_comfort),
    Rule("ride_restored", _r_ride_restored),
]


def propagate(world: World, *, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ROUTES: dict[str, Route] = {
    "buttercup_straight": Route(
        id="buttercup_straight",
        label="buttercup straight",
        phrase="the buttercup bike lane from the golden cabin to the golden bench",
        cabin_detail="The golden cabin shone like butter on warm toast at the start of the lane.",
        lane_detail="Buttercups bobbed by the painted edge, and the bell notes skipped beside them.",
        bench_detail="The golden bench waited ahead with bright slats and a patient little shine.",
        allows=frozenset({"pebble_skip", "basket_tilt"}),
        tags=frozenset({"bike_lane", "golden_cabin", "golden_bench", "buttercups"}),
    ),
    "ribbon_curve": Route(
        id="ribbon_curve",
        label="ribbon curve",
        phrase="the ribboned bike lane that curled from the golden cabin toward the golden bench",
        cabin_detail="The golden cabin blinked behind a gate where ribbons clicked in the breeze.",
        lane_detail="White lane loops curved like ribbon on the ground, smooth but full of little surprises.",
        bench_detail="The golden bench sat by the bend, ready for tired legs and happy crumbs.",
        allows=frozenset({"basket_tilt", "puddle_splatter"}),
        tags=frozenset({"bike_lane", "golden_cabin", "golden_bench", "ribbons"}),
    ),
    "ladybug_bend": Route(
        id="ladybug_bend",
        label="ladybug bend",
        phrase="the ladybug bike lane between the golden cabin and the golden bench",
        cabin_detail="The golden cabin glimmered near a red fence dotted with ladybug paint spots.",
        lane_detail="Tiny red circles winked on the lane, and the turn ahead looked merry and narrow.",
        bench_detail="The golden bench rested under a sun patch where the lane finished its bend.",
        allows=frozenset({"pebble_skip", "puddle_splatter"}),
        tags=frozenset({"bike_lane", "golden_cabin", "golden_bench", "ladybugs"}),
    ),
}


CRASHES: dict[str, CrashMode] = {
    "pebble_skip": CrashMode(
        id="pebble_skip",
        label="pebble skip",
        sound="Tick-tack, skitter-clack, crash!",
        cause="a bead of pebbles skipped under the front tire at the narrow stripe",
        result="{friend}'s elbow kissed the ground, and the bicycle leaned sideways with a startled squeak.",
        need="elbow_wrap",
        proof="The soft wrap stayed snug, and the elbow no longer made {friend} wince.",
        tags=frozenset({"crash", "pebbles", "elbow"}),
    ),
    "basket_tilt": CrashMode(
        id="basket_tilt",
        label="basket tilt",
        sound="Bump-bump, clatter-clap, crash!",
        cause="a crooked crack tapped the wheel and tipped the little front basket",
        result="The basket swung loose, and {friend} had to hop down before the whole bicycle could topple harder.",
        need="basket_loop",
        proof="The basket rode straight again, with its strap sitting neat and quiet.",
        tags=frozenset({"crash", "basket", "strap"}),
    ),
    "puddle_splatter": CrashMode(
        id="puddle_splatter",
        label="puddle splatter",
        sound="Splish-splash, blink-blink, crash!",
        cause="a silver puddle slapped up from the lane and muddied the chalk map at the turn",
        result="{friend} blinked at the blur and bumped to a stop, one shoe sliding in the wet.",
        need="wipe_cloth",
        proof="The chalk map shone clear again, and the next turn was easy to see.",
        tags=frozenset({"crash", "puddle", "map"}),
    ),
}


SHARES: dict[str, ShareItem] = {
    "moon_scarf": ShareItem(
        id="moon_scarf",
        label="moon scarf",
        phrase="a folded moon scarf",
        handles=frozenset({"elbow_wrap"}),
        action="wrapped the moon scarf softly around the sore elbow",
        reason="a soft wrap can cushion a scrape and help a frightened rider feel steady again",
        effect="The little sting settled, and the brave rider could hold the handlebar without flinching.",
        material="soft cloth",
        tags=frozenset({"sharing", "kindness", "cloth"}),
    ),
    "waxed_loop": ShareItem(
        id="waxed_loop",
        label="waxed loop",
        phrase="a waxed loop of string",
        handles=frozenset({"basket_loop"}),
        action="threaded the waxed loop through the loose basket clasp and tied it snug",
        reason="a firm loop can hold a swinging basket still so the rider can steer safely",
        effect="The basket stopped flapping, and the wheel song grew neat instead of noisy.",
        material="string",
        tags=frozenset({"sharing", "kindness", "string"}),
    ),
    "gingham_wipe": ShareItem(
        id="gingham_wipe",
        label="gingham wipe",
        phrase="a gingham wipe",
        handles=frozenset({"wipe_cloth"}),
        action="dabbed the chalk map clear with the gingham wipe until the arrows showed again",
        reason="a dry cloth can lift mud from a map so the rider can see the safe way ahead",
        effect="The muddy blur disappeared, and the lane marks came back in bright little lines.",
        material="dry cloth",
        tags=frozenset({"sharing", "kindness", "cloth"}),
    ),
}


HERO_NAMES = ["Mira", "Pip", "Tansy", "Rory", "Lark", "Nell"]
FRIEND_NAMES = ["Bea", "Jun", "Otis", "Wren", "Faye", "Moss"]


def valid_combo(route: Route, crash: CrashMode, share: ShareItem) -> bool:
    return crash.id in route.allows and crash.need in share.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route in ROUTES.values():
        for crash in CRASHES.values():
            for share in SHARES.values():
                if valid_combo(route, crash, share):
                    combos.append((route.id, crash.id, share.id))
    return sorted(combos)


def explain_rejection(route_id: str, crash_id: str, share_id: str) -> str:
    if route_id not in ROUTES:
        return f"Unknown route {route_id!r}."
    if crash_id not in CRASHES:
        return f"Unknown crash {crash_id!r}."
    if share_id not in SHARES:
        return f"Unknown share item {share_id!r}."
    route = ROUTES[route_id]
    crash = CRASHES[crash_id]
    share = SHARES[share_id]
    if crash.id not in route.allows:
        return f"{route.label} does not plausibly lead to the {crash.label}."
    if crash.need not in share.handles:
        return f"{share.label} cannot honestly fix the trouble caused by the {crash.label}."
    return "The requested bike-lane nursery story is outside the valid set."


def introduce(world: World, route: Route, hero: Entity, friend: Entity, share: ShareItem) -> None:
    cabin = world.get("cabin")
    bench = world.get("bench")
    satchel = world.get("satchel")
    oat_cake = world.get("oat_cake")
    world.say(
        f"From the golden cabin rode {hero.label}, ding-ding bright, along {route.phrase}."
    )
    world.say(route.cabin_detail)
    world.say(route.lane_detail)
    world.say(
        f"In {hero.pronoun('possessive')} satchel rested {share.phrase} and one honey oat cake "
        "saved for later sharing."
    )
    world.say(
        f"{friend.label} pedaled beside {hero.label}, and the golden bench winked ahead like a small prize."
    )
    satchel.meters["packed"] += 1.0
    oat_cake.meters["whole"] += 1.0
    cabin.memes["home"] += 1.0
    bench.memes["promise"] += 1.0
    world.note(
        "premise",
        from_place="golden cabin",
        to_place="golden bench",
        route=route.label,
        riders=f"{hero.label} and {friend.label}",
    )


def crash_scene(world: World, route: Route, crash: CrashMode, friend: Entity) -> None:
    friend_bike = world.get("friend_bike")
    basket = world.get("friend_basket")
    chalk_map = world.get("chalk_map")
    world.para()
    world.say(crash.sound)
    world.say(crash.cause.capitalize() + ".")
    world.say(crash.result.format(friend=friend.label))
    world.say(
        "The golden bench was close enough to see, but not close enough to mend the trouble by itself."
    )
    friend_bike.meters["wobble"] += 1.0
    world.facts["crash_happened"] = True
    world.facts["problem_need"] = crash.need
    if crash.need == "elbow_wrap":
        friend.meters["elbow_sting"] += 1.0
    elif crash.need == "basket_loop":
        basket.meters["loose"] += 1.0
    elif crash.need == "wipe_cloth":
        chalk_map.meters["muddy"] += 1.0
    world.note(
        "crash",
        rider=friend.label,
        cause=crash.cause,
        need=crash.need,
        route=route.label,
    )
    propagate(world, narrate=True)


def share_help(world: World, hero: Entity, friend: Entity, crash: CrashMode, share: ShareItem) -> None:
    if crash.need not in share.handles:
        raise StoryError(f"{share.label} cannot help after the {crash.label}.")
    friend_bike = world.get("friend_bike")
    basket = world.get("friend_basket")
    chalk_map = world.get("chalk_map")
    gift = world.get("share_item")
    world.para()
    world.say(f"{hero.label} did not hide the {share.label} away.")
    world.say(f"{hero.pronoun().capitalize()} shared it at once and {share.action}.")
    gift.shared_with = friend.id
    gift.meters["shared"] += 1.0
    gift.memes["used_kindly"] += 1.0
    world.facts["help_shared"] = True
    if crash.need == "elbow_wrap":
        friend.meters["elbow_sting"] = 0.0
        friend.meters["elbow_wrapped"] += 1.0
    elif crash.need == "basket_loop":
        basket.meters["loose"] = 0.0
        basket.meters["secured"] += 1.0
    elif crash.need == "wipe_cloth":
        chalk_map.meters["muddy"] = 0.0
        chalk_map.meters["clear"] += 1.0
    friend_bike.meters["steady"] += 1.0
    hero.memes["ready_to_share"] += 1.0
    world.note(
        "share_help",
        sharer=hero.label,
        recipient=friend.label,
        item=share.label,
        reason=share.reason,
    )
    propagate(world, narrate=True)


def ending(world: World, route: Route, hero: Entity, friend: Entity) -> None:
    crash = CRASHES[world.params.crash]
    oat_cake = world.get("oat_cake")
    bench = world.get("bench")
    world.para()
    world.say("One careful push, two careful turns, and the children reached the bench at last.")
    world.say(route.bench_detail)
    world.say(crash.proof.format(friend=friend.label))
    world.say(
        f"{hero.label} and {friend.label} sat on the golden bench and broke the honey oat cake right down the middle."
    )
    world.say(
        "Nibble and giggle, crumb and grin, the bike lane hummed, "
        '"kind hands share, and kind hearts win."'
    )
    oat_cake.meters["shared"] += 1.0
    oat_cake.meters["whole"] = 0.0
    oat_cake.memes["togetherness"] += 1.0
    bench.meters["occupied"] += 1.0
    bench.memes["kindness_seen"] += 1.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    world.facts["final_image"] = "children_on_golden_bench_sharing_oat_cake"
    world.facts["ending"] = "shared_rest"
    world.note(
        "ending",
        image="children on the golden bench sharing an oat cake",
        lesson="kindness traveled farther because it was shared",
    )


def build_story(
    route: Route,
    crash: CrashMode,
    share: ShareItem,
    hero_name: str,
    friend_name: str,
    seed: Optional[int] = None,
) -> World:
    params = StoryParams(
        route=route.id,
        crash=crash.id,
        share=share.id,
        hero=hero_name,
        friend=friend_name,
        seed=seed,
    )
    world = World(params=params)
    hero = world.add(Entity("hero", "character", hero_name, phrase=hero_name, region="lane"))
    friend = world.add(Entity("friend", "character", friend_name, phrase=friend_name, region="lane"))
    world.add(Entity("cabin", "place", "golden cabin", phrase="the golden cabin", region="start"))
    world.add(Entity("bench", "place", "golden bench", phrase="the golden bench", region="finish"))
    world.add(Entity("lane", "place", "bike lane", phrase="the bike lane", region="between"))
    world.add(Entity("hero_bike", "thing", f"{hero_name}'s bicycle", region="lane", owner=hero.id))
    world.add(Entity("friend_bike", "thing", f"{friend_name}'s bicycle", region="lane", owner=friend.id))
    world.add(Entity("satchel", "thing", "satchel", region="hero bicycle", owner=hero.id))
    world.add(Entity("share_item", "thing", share.label, phrase=share.phrase, region="satchel", owner=hero.id))
    world.add(Entity("oat_cake", "food", "honey oat cake", phrase="the honey oat cake", region="satchel", owner=hero.id))
    world.add(Entity("friend_basket", "thing", "front basket", phrase="the front basket", region="friend bicycle", owner=friend.id))
    world.add(Entity("chalk_map", "thing", "chalk map", phrase="the chalk map", region="friend pocket", owner=friend.id))

    world.facts.update(
        route=route,
        crash=crash,
        share=share,
        hero=hero,
        friend=friend,
        setting="bike lane",
    )

    introduce(world, route, hero, friend, share)
    crash_scene(world, route, crash, friend)
    share_help(world, hero, friend, crash, share)
    ending(world, route, hero, friend)
    return world


def generation_prompts(world: World) -> list[str]:
    route = ROUTES[world.params.route]
    crash = CRASHES[world.params.crash]
    share = SHARES[world.params.share]
    return [
        'Write a Nursery Rhyme style story that includes "golden cabin", "crash", and "golden bench".',
        f"Set it on {route.phrase} and let a {crash.label} create a child-sized problem.",
        f"Make kindness concrete by having one rider share the {share.label} so the ending can happen on the bench.",
    ]


KNOWLEDGE: dict[str, QAItem] = {
    "bike_lane": QAItem(
        question="Why is slowing down important after a wobble in a bike lane?",
        answer=(
            "Slowing down gives riders time to see what went wrong before the problem grows bigger. "
            "It also makes room for safe help instead of hurried guessing."
        ),
    ),
    "golden_cabin": QAItem(
        question="What does a cabin add to a nursery-sized journey?",
        answer=(
            "A cabin gives the story a warm beginning place that feels close and safe. "
            "That homey start makes the later ride and return to calm feel clearer."
        ),
    ),
    "golden_bench": QAItem(
        question="Why is a bench a strong ending image for a child story?",
        answer=(
            "A bench lets the body rest where the trouble has finally passed. "
            "It turns the ending into one clear picture that shows peace instead of motion."
        ),
    ),
    "sharing": QAItem(
        question="What makes sharing feel meaningful in this world?",
        answer=(
            "Sharing matters because the useful thing is given at the exact moment another rider needs it. "
            "The object stops being private comfort and becomes shared repair."
        ),
    ),
    "kindness": QAItem(
        question="How is kindness different from only feeling sorry for someone?",
        answer=(
            "Kindness does something helpful with the feeling of care. "
            "In this world, the kind child acts with hands, tools, and time."
        ),
    ),
    "elbow_wrap": QAItem(
        question="Why can a soft wrap help after a scraped elbow?",
        answer=(
            "A soft wrap can protect the sore place from rubbing and sudden bumps. "
            "Gentle care also helps the rider feel brave enough to start again."
        ),
    ),
    "basket_loop": QAItem(
        question="Why does tying a loose basket matter on a bicycle?",
        answer=(
            "A tied basket stops swinging into the wheel and pulling the handlebars off line. "
            "When the basket stays quiet, the rider can steer with more confidence."
        ),
    ),
    "wipe_cloth": QAItem(
        question="Why is a dry cloth useful after muddy water hits a map?",
        answer=(
            "A dry cloth can clear the marks so the rider can see the right turn again. "
            "Seeing clearly changes confusion into safe movement."
        ),
    ),
}


def story_qa(world: World) -> list[QAItem]:
    route = ROUTES[world.params.route]
    crash = CRASHES[world.params.crash]
    share = SHARES[world.params.share]
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        QAItem(
            question="Where did the story begin and where did it end?",
            answer=(
                f"It began by the golden cabin on {route.phrase}. "
                f"It ended at the golden bench after the children could ride calmly again."
            ),
        ),
        QAItem(
            question=f"Why did {friend.label} have a crash?",
            answer=(
                f"{friend.label} had the crash because {crash.cause}. "
                "That hazard created a small but real problem that stopped the easy rhythm of the ride."
            ),
        ),
        QAItem(
            question=f"What did {hero.label} share, and why was it the right help?",
            answer=(
                f"{hero.label} shared the {share.label}. "
                f"It was the right help because {share.reason}."
            ),
        ),
        QAItem(
            question="How did kindness change what happened next?",
            answer=(
                f"After the shared help, {share.effect.lower()} "
                "The children could finish the lane gently instead of ending the story in worry."
            ),
        ),
        QAItem(
            question="What final image proves that sharing lasted past the repair?",
            answer=(
                "The final image shows both children on the golden bench breaking the honey oat cake in two. "
                "That picture proves the help was not only a fix but also a shared ending."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    crash = CRASHES[world.params.crash]
    need_key = crash.need
    keys = ["bike_lane", "golden_cabin", "golden_bench", "kindness", "sharing", need_key]
    return [KNOWLEDGE[key] for key in keys]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.friend:
        raise StoryError("Hero and friend must be different children.")
    if params.route not in ROUTES or params.crash not in CRASHES or params.share not in SHARES:
        raise StoryError(explain_rejection(params.route, params.crash, params.share))
    route = ROUTES[params.route]
    crash = CRASHES[params.crash]
    share = SHARES[params.share]
    if not valid_combo(route, crash, share):
        raise StoryError(explain_rejection(params.route, params.crash, params.share))
    world = build_story(route, crash, share, params.hero, params.friend, params.seed)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(R,C,S) :- route(R), crash(C), share(S), allows(R,C), needs(C,N), handles(S,N).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for route in ROUTES.values():
        facts.append(asp.fact("route", route.id))
        for crash_id in route.allows:
            facts.append(asp.fact("allows", route.id, crash_id))
    for crash in CRASHES.values():
        facts.append(asp.fact("crash", crash.id))
        facts.append(asp.fact("needs", crash.id, crash.need))
    for share in SHARES.values():
        facts.append(asp.fact("share", share.id))
        for need in share.handles:
            facts.append(asp.fact("handles", share.id, need))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    combos: set[tuple[str, str, str]] = set()
    for model in asp.solve(asp_facts() + ASP_RULES):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(part) for part in atom))  # type: ignore[arg-type]
    return sorted(combos)


def all_params(args: argparse.Namespace | None = None) -> list[StoryParams]:
    args = args or argparse.Namespace(route=None, crash=None, share=None, hero=None, friend=None, seed=None)
    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.crash is None or combo[1] == args.crash)
        and (args.share is None or combo[2] == args.share)
    ]
    params_list: list[StoryParams] = []
    for idx, (route_id, crash_id, share_id) in enumerate(combos):
        hero = args.hero or HERO_NAMES[idx % len(HERO_NAMES)]
        if args.friend is not None:
            if args.friend == hero:
                raise StoryError("Hero and friend must be different children.")
            friend = args.friend
        else:
            choices = [name for name in FRIEND_NAMES if name != hero]
            friend = choices[idx % len(choices)]
        seed = (args.seed if args.seed is not None else 700) + idx
        params_list.append(StoryParams(route_id, crash_id, share_id, hero, friend, seed))
    return params_list


def verify_asp_parity() -> str:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        only_py = sorted(py - lp)
        only_lp = sorted(lp - py)
        raise StoryError(f"Python/ASP mismatch. only_py={only_py} only_asp={only_lp}")
    return f"OK: Python and ASP agree on {len(py)} valid route/crash/share combinations."


def verify_story_samples() -> str:
    for params in all_params():
        sample = generate(params)
        story_lower = sample.story.lower()
        if "golden cabin" not in story_lower:
            raise StoryError(f"story for {params} is missing 'golden cabin'")
        if "crash" not in story_lower:
            raise StoryError(f"story for {params} is missing 'crash'")
        if "golden bench" not in story_lower:
            raise StoryError(f"story for {params} is missing 'golden bench'")
        if "bike lane" not in story_lower:
            raise StoryError(f"story for {params} is missing 'bike lane'")
        if sample.world is None or sample.world.facts.get("ending") != "shared_rest":
            raise StoryError(f"story for {params} did not reach the shared-rest ending")
        if not sample.prompts or len(sample.story_qa) < 5 or len(sample.world_qa) < 5:
            raise StoryError(f"story for {params} did not populate all QA sets")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"story for {params} leaked template braces")
        if "  " in sample.story:
            raise StoryError(f"story for {params} contains doubled spaces")
    return f"OK: Exercised {len(all_params())} generated stories with grounded QA and complete endings."


def verify() -> str:
    return verify_asp_parity() + "\n" + verify_story_samples()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", choices=sorted(ROUTES))
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
    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.crash is None or combo[1] == args.crash)
        and (args.share is None or combo[2] == args.share)
    ]
    if not combos:
        route_id = args.route or sorted(ROUTES)[0]
        crash_id = args.crash or sorted(CRASHES)[0]
        share_id = args.share or sorted(SHARES)[0]
        raise StoryError(explain_rejection(route_id, crash_id, share_id))
    route_id, crash_id, share_id = rng.choice(combos)
    hero = args.hero or rng.choice(HERO_NAMES)
    if args.friend is not None:
        if args.friend == hero:
            raise StoryError("Hero and friend must be different children.")
        friend = args.friend
    else:
        choices = [name for name in FRIEND_NAMES if name != hero]
        friend = rng.choice(choices)
    return StoryParams(route_id, crash_id, share_id, hero, friend, args.seed)


def format_qa(title: str, items: list[QAItem]) -> list[str]:
    lines = [title]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if args.trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in all_params(args)]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    step = 0
    attempts = 0
    while len(samples) < target and attempts < target * 40:
        attempts += 1
        seed = base_seed + step
        step += 1
        local_args = argparse.Namespace(**vars(args))
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed))
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError(f"Could only generate {len(samples)} unique stories for n={target}.")
    return samples


def show_asp_program() -> str:
    return asp_facts() + ASP_RULES


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.show_asp:
            print(show_asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in asp_valid_combos():
                print(" ".join(combo))
            return 0
        samples = samples_from_args(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0
        for index, sample in enumerate(samples, 1):
            header = None
            if len(samples) > 1:
                header = (
                    "=== golden_cabin_crash_golden_bench_bike_lane_2 "
                    f"#{index} seed={sample.params.seed} ==="
                )
            emit(sample, args, header=header)
            if index != len(samples):
                print()
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
