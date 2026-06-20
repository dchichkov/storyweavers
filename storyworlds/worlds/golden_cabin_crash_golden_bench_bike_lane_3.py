#!/usr/bin/env python3
"""Nursery-rhyme storyworld about a bike-lane crash near a golden bench.

Seed:
    Words: golden cabin, crash, golden bench
    Setting: bike lane
    Features: Kindness, Sharing
    Style: Nursery Rhyme

Internal source tale:
    Two children ride from a golden cabin along a painted bike lane toward a
    golden bench. A small crash interrupts their easy rhythm when lane trouble
    or glare makes one rider stop short. The other child shares the one useful
    thing that fits the trouble, so the ride can continue and end with both
    children sharing a plum bun on the golden bench.
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


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


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
class ShareTool:
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


def _r_hush_after_crash(world: World) -> list[str]:
    if not world.facts.get("crash_happened"):
        return []
    friend_bike = world.get("friend_bike")
    if friend_bike.meters["shaken"] < THRESHOLD:
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    lane = world.get("lane")
    if not _mark(world, "hush_after_crash", hero.id, friend.id):
        return []
    hero.memes["concern"] += 1.0
    friend.memes["worry"] += 1.0
    lane.memes["quiet"] += 1.0
    world.note(
        "hush_after_crash",
        watcher=hero.label,
        rider=friend.label,
        change="the lane grew quiet enough for help to matter",
    )
    return [
        "The bike lane lost its jingle for a moment, as if the painted line itself had stopped to listen.",
        f"{hero.label} hopped down at once, because a small crash can still feel big to a child on small wheels.",
    ]


def _r_shared_heart(world: World) -> list[str]:
    if not world.facts.get("tool_shared"):
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    bench = world.get("bench")
    tool = TOOLS[world.params.share]
    if not _mark(world, "shared_heart", hero.id, friend.id, tool.id):
        return []
    hero.memes["kindness"] += 1.0
    hero.memes["sharing"] += 1.0
    friend.memes["trust"] += 1.0
    friend.memes["relief"] += 1.0
    bench.memes["welcome"] += 1.0
    world.note(
        "shared_heart",
        sharer=hero.label,
        recipient=friend.label,
        item=tool.label,
        lesson="shared care changed the mood of the ride",
    )
    return [
        tool.effect,
        f"{friend.label} took one slow breath and then another, because help shared kindly can steady more than a wheel.",
    ]


def _r_ride_rebalanced(world: World) -> list[str]:
    friend_bike = world.get("friend_bike")
    if friend_bike.meters["steady"] < THRESHOLD:
        return []
    if not _mark(world, "ride_rebalanced", friend_bike.id):
        return []
    friend_bike.meters["shaken"] = 0.0
    friend_bike.memes["calm"] += 1.0
    world.get("hero_bike").memes["calm"] += 1.0
    world.facts["ride_ready"] = True
    world.note(
        "ride_rebalanced",
        rider=world.get("friend").label,
        proof="the wheels could roll in a soft straight rhythm again",
    )
    return [
        "Soon the spokes found their rhyme again, and the little ride could move in a calm straight song.",
    ]


CAUSAL_RULES = [
    Rule("hush_after_crash", _r_hush_after_crash),
    Rule("shared_heart", _r_shared_heart),
    Rule("ride_rebalanced", _r_ride_rebalanced),
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


def sentence_start(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def article_for(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


ROUTES: dict[str, Route] = {
    "butter_bell": Route(
        id="butter_bell",
        label="butter bell lane",
        phrase="the butter-bell bike lane from the golden cabin to the golden bench",
        cabin_detail="The golden cabin gleamed like warm toast, with one tiny bell hook shining by the door.",
        lane_detail="Yellow loops of paint curved along the bike lane, and buttercup heads bobbed at the edge.",
        bench_detail="The golden bench waited beneath a patch of sun, bright as a spoon dipped in honey.",
        allows=frozenset({"sunflash_swerve", "acorn_clatter"}),
        tags=frozenset({"bike_lane", "golden_cabin", "golden_bench", "buttercups"}),
    ),
    "ribbon_ring": Route(
        id="ribbon_ring",
        label="ribbon ring lane",
        phrase="the ribbon-ring bike lane between the golden cabin and the golden bench",
        cabin_detail="The golden cabin stood behind a ribbon gate that clicked and danced in the breeze.",
        lane_detail="White rings circled the bike lane, and each turn looked neat but narrow for small tires.",
        bench_detail="The golden bench rested by the final curve, ready for knees, crumbs, and a happy pause.",
        allows=frozenset({"acorn_clatter", "puddle_glimmer"}),
        tags=frozenset({"bike_lane", "golden_cabin", "golden_bench", "ribbons"}),
    ),
    "marigold_mark": Route(
        id="marigold_mark",
        label="marigold mark lane",
        phrase="the marigold-mark bike lane that curled from the golden cabin toward the golden bench",
        cabin_detail="The golden cabin blinked beside a fence with marigold paint dots bright as little suns.",
        lane_detail="A pale stripe ran through the bike lane, and marigold shadows dappled the gentle bend.",
        bench_detail="The golden bench shone at the end of the lane, with slats bright enough to catch the late light.",
        allows=frozenset({"sunflash_swerve", "puddle_glimmer"}),
        tags=frozenset({"bike_lane", "golden_cabin", "golden_bench", "marigolds"}),
    ),
}


CRASHES: dict[str, CrashMode] = {
    "sunflash_swerve": CrashMode(
        id="sunflash_swerve",
        label="sunflash swerve",
        sound="Ring-ting, blink-blink, crash!",
        cause="a hard splash of sunshine flashed from a silver lane marker and into {friend}'s eyes",
        result="{friend} gave a surprised squeak, the front wheel kissed the paint lip, and there was a soft little crash.",
        need="shade_fix",
        proof="The bright flash turned gentle, so the lane line was easy to follow all the way to the bench.",
        tags=frozenset({"crash", "glare", "eyes"}),
    ),
    "acorn_clatter": CrashMode(
        id="acorn_clatter",
        label="acorn clatter",
        sound="Clack-clack, bump-bump, crash!",
        cause="two acorns rattled from the hedge and jarred the basket clasp at the bend",
        result="The front basket swung sideways, and {friend} hopped off before the bicycle could tumble into a harder crash.",
        need="basket_fix",
        proof="The basket sat snug and still again, so the handlebars stopped tugging to one side.",
        tags=frozenset({"crash", "acorns", "basket"}),
    ),
    "puddle_glimmer": CrashMode(
        id="puddle_glimmer",
        label="puddle glimmer",
        sound="Splish-spark, slip-slap, crash!",
        cause="a puddle flicked muddy water over the chalk turn arrow beside the painted stripe",
        result="{friend} blinked at the smeared mark, slid one shoe, and made a splashy little crash by the bike lane edge.",
        need="mud_fix",
        proof="The chalk arrow shone clear again, and the safe turn looked simple instead of blurry.",
        tags=frozenset({"crash", "puddle", "chalk"}),
    ),
}


TOOLS: dict[str, ShareTool] = {
    "sky_kerchief": ShareTool(
        id="sky_kerchief",
        label="sky kerchief",
        phrase="a folded sky kerchief",
        handles=frozenset({"shade_fix"}),
        action="looped the sky kerchief over the glaring marker and dabbed away the watery blink",
        reason="a soft kerchief can tame the sharp shine and help a child see the line again",
        effect="The sting of the glare settled, and the bright world looked friendly instead of fierce.",
        material="soft cloth",
        tags=frozenset({"sharing", "kindness", "cloth"}),
    ),
    "honey_twine": ShareTool(
        id="honey_twine",
        label="honey twine",
        phrase="a coil of honey twine",
        handles=frozenset({"basket_fix"}),
        action="threaded the honey twine through the loose clasp and tied a careful bow",
        reason="a firm piece of twine can keep a swinging basket from pulling the bicycle off line",
        effect="The basket stopped flapping, and the handlebar song turned neat and steady again.",
        material="twine",
        tags=frozenset({"sharing", "kindness", "twine"}),
    ),
    "petal_towel": ShareTool(
        id="petal_towel",
        label="petal towel",
        phrase="a dry petal towel",
        handles=frozenset({"mud_fix"}),
        action="wiped the muddy chalk until the turn arrow smiled bright again",
        reason="a dry towel can clear the mark so a rider can see the safe turn instead of guessing",
        effect="The muddy blur disappeared, and the path ahead came back in a clean white curve.",
        material="dry cloth",
        tags=frozenset({"sharing", "kindness", "cloth"}),
    ),
}


HERO_NAMES = ["Mira", "Pip", "Lark", "Nell", "Rory", "Tansy"]
FRIEND_NAMES = ["Bea", "Jun", "Faye", "Otis", "Wren", "Moss"]


def valid_combo(route: Route, crash: CrashMode, share: ShareTool) -> bool:
    return crash.id in route.allows and crash.need in share.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route in ROUTES.values():
        for crash in CRASHES.values():
            for share in TOOLS.values():
                if valid_combo(route, crash, share):
                    combos.append((route.id, crash.id, share.id))
    return sorted(combos)


def explain_rejection(route_id: str, crash_id: str, share_id: str) -> str:
    if route_id not in ROUTES:
        return f"Unknown route {route_id!r}."
    if crash_id not in CRASHES:
        return f"Unknown crash {crash_id!r}."
    if share_id not in TOOLS:
        return f"Unknown share tool {share_id!r}."
    route = ROUTES[route_id]
    crash = CRASHES[crash_id]
    share = TOOLS[share_id]
    if crash.id not in route.allows:
        return f"{route.label} does not plausibly lead to the {crash.label}."
    if crash.need not in share.handles:
        return f"{share.label} cannot honestly solve the trouble caused by the {crash.label}."
    return "The requested nursery-rhyme bike-lane story is outside the valid set."


def introduce(world: World, route: Route, hero: Entity, friend: Entity, tool: ShareTool) -> None:
    cabin = world.get("cabin")
    bench = world.get("bench")
    satchel = world.get("satchel")
    bun = world.get("plum_bun")
    world.say(
        f"Out from the golden cabin rolled {hero.label}, ding-ding bright, along {route.phrase}."
    )
    world.say(route.cabin_detail)
    world.say(route.lane_detail)
    world.say(
        f"In {hero.pronoun('possessive')} satchel rested {tool.phrase} and one sugared plum bun saved for later sharing."
    )
    world.say(
        f"{friend.label} rode beside {hero.label}, and the golden bench glimmered ahead like a tidy little crown."
    )
    satchel.meters["packed"] += 1.0
    bun.meters["whole"] += 1.0
    cabin.memes["home"] += 1.0
    bench.memes["promise"] += 1.0
    hero.memes["joy"] += 0.5
    friend.memes["joy"] += 0.5
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
    chalk_arrow = world.get("chalk_arrow")
    glare_marker = world.get("glare_marker")
    world.para()
    world.say(crash.sound)
    world.say(sentence_start(crash.cause.format(friend=friend.label)) + ".")
    world.say(crash.result.format(friend=friend.label))
    world.say(
        "The golden bench was close enough to see, but not close enough to fix the trouble all by itself."
    )
    world.facts["crash_happened"] = True
    world.facts["problem_need"] = crash.need
    friend_bike.meters["shaken"] += 1.0
    if crash.need == "shade_fix":
        glare_marker.meters["glaring"] += 1.0
        friend.meters["eyes_watery"] += 1.0
    elif crash.need == "basket_fix":
        basket.meters["loose"] += 1.0
    elif crash.need == "mud_fix":
        chalk_arrow.meters["blurred"] += 1.0
    world.note(
        "crash",
        rider=friend.label,
        cause=crash.cause.format(friend=friend.label),
        need=crash.need,
        route=route.label,
    )
    propagate(world, narrate=True)


def share_help(world: World, hero: Entity, friend: Entity, crash: CrashMode, tool: ShareTool) -> None:
    if crash.need not in tool.handles:
        raise StoryError(f"{tool.label} cannot help after the {crash.label}.")
    friend_bike = world.get("friend_bike")
    basket = world.get("friend_basket")
    chalk_arrow = world.get("chalk_arrow")
    glare_marker = world.get("glare_marker")
    shared_tool = world.get("share_tool")
    world.para()
    world.say(f"{hero.label} did not tuck the {tool.label} away.")
    world.say(f"{hero.pronoun().capitalize()} shared it at once and {tool.action}.")
    shared_tool.shared_with = friend.id
    shared_tool.meters["shared"] += 1.0
    shared_tool.memes["used_kindly"] += 1.0
    hero.memes["ready_to_share"] += 1.0
    world.facts["tool_shared"] = True
    if crash.need == "shade_fix":
        glare_marker.meters["glaring"] = 0.0
        glare_marker.meters["shaded"] += 1.0
        friend.meters["eyes_watery"] = 0.0
    elif crash.need == "basket_fix":
        basket.meters["loose"] = 0.0
        basket.meters["secured"] += 1.0
    elif crash.need == "mud_fix":
        chalk_arrow.meters["blurred"] = 0.0
        chalk_arrow.meters["clear"] += 1.0
    friend_bike.meters["steady"] += 1.0
    world.note(
        "share_help",
        sharer=hero.label,
        recipient=friend.label,
        item=tool.label,
        reason=tool.reason,
    )
    propagate(world, narrate=True)


def ending(world: World, route: Route, hero: Entity, friend: Entity) -> None:
    crash = CRASHES[world.params.crash]
    bun = world.get("plum_bun")
    bench = world.get("bench")
    world.para()
    world.say("One careful push, two careful turns, and the riders reached the bench at last.")
    world.say(route.bench_detail)
    world.say(crash.proof)
    world.say(
        f"{hero.label} and {friend.label} sat on the golden bench and broke the plum bun right through the middle."
    )
    world.say(
        '"Share a cloth, share a string, share a bun when troubles sting; kind hands mend, kind hearts sing."'
    )
    bun.meters["whole"] = 0.0
    bun.meters["shared"] += 1.0
    bun.memes["togetherness"] += 1.0
    bench.meters["occupied"] += 1.0
    bench.memes["kindness_seen"] += 1.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    world.facts["ending"] = "bench_shared_bun"
    world.facts["final_image"] = "children_on_golden_bench_sharing_plum_bun"
    world.note(
        "ending",
        image="children on the golden bench sharing a plum bun",
        lesson="kindness traveled farther because it was shared",
    )


def build_story(
    route: Route,
    crash: CrashMode,
    share: ShareTool,
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
    world.add(Entity("share_tool", "thing", share.label, phrase=share.phrase, region="satchel", owner=hero.id))
    world.add(Entity("plum_bun", "food", "plum bun", phrase="the plum bun", region="satchel", owner=hero.id))
    world.add(Entity("friend_basket", "thing", "front basket", phrase="the front basket", region="friend bicycle", owner=friend.id))
    world.add(Entity("chalk_arrow", "thing", "chalk arrow", phrase="the chalk arrow", region="lane turn"))
    world.add(Entity("glare_marker", "thing", "silver lane marker", phrase="the silver lane marker", region="lane stripe"))

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
    share = TOOLS[world.params.share]
    return [
        'Write a Nursery Rhyme style story that includes "golden cabin", "crash", and "golden bench".',
        f"Set it on {route.phrase} and let {article_for(crash.label)} {crash.label} interrupt the ride in a child-sized way.",
        f"Make kindness physical by having one child share the {share.label} so the ending can happen on the bench.",
    ]


KNOWLEDGE: dict[str, QAItem] = {
    "bike_lane": QAItem(
        question="Why is slowing down important after a wobble in a bike lane?",
        answer=(
            "Slowing down gives a child time to notice what went wrong before the problem grows bigger. "
            "It also creates room for a helper to act safely instead of rushing."
        ),
    ),
    "golden_cabin": QAItem(
        question="What does a cabin add to a nursery-sized journey?",
        answer=(
            "A cabin gives the story a warm beginning place that feels close and safe. "
            "That homey start makes the later return to calm easier to feel."
        ),
    ),
    "golden_bench": QAItem(
        question="Why is a bench a strong ending image for a child story?",
        answer=(
            "A bench turns motion into rest, so the child can see that the trouble has truly passed. "
            "It also gives one clear picture where sharing can be seen at the end."
        ),
    ),
    "kindness": QAItem(
        question="How is kindness shown physically in this world?",
        answer=(
            "Kindness is shown by using hands, tools, and time to help another rider. "
            "The caring feeling becomes real because it changes what happens next."
        ),
    ),
    "sharing": QAItem(
        question="What makes sharing meaningful in this storyworld?",
        answer=(
            "Sharing matters because the useful thing is given at the exact moment it is needed. "
            "The shared object stops being private comfort and becomes a bridge back to safety."
        ),
    ),
    "shade_fix": QAItem(
        question="Why can soft cloth help with sharp glare?",
        answer=(
            "Soft cloth can cover the bright source or wipe tears so the eyes can settle. "
            "Seeing clearly again helps the rider move safely instead of guessing."
        ),
    ),
    "basket_fix": QAItem(
        question="Why does tying a loose basket matter on a bicycle?",
        answer=(
            "A loose basket can tug the handlebars and make the ride uneven. "
            "Tying it firmly lets the bicycle track straight again."
        ),
    ),
    "mud_fix": QAItem(
        question="Why is cleaning a muddy lane mark useful?",
        answer=(
            "A muddy mark hides the information that tells the rider where to go. "
            "When the mark is clear again, confusion turns back into safe choice."
        ),
    ),
}


def story_qa(world: World) -> list[QAItem]:
    route = ROUTES[world.params.route]
    crash = CRASHES[world.params.crash]
    share = TOOLS[world.params.share]
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        QAItem(
            question="Where did the story begin and where did it end?",
            answer=(
                f"It began by the golden cabin on {route.phrase}. "
                "It ended at the golden bench after the ride found its calm rhythm again."
            ),
        ),
        QAItem(
            question=f"Why did {friend.label} have a crash?",
            answer=(
                f"{friend.label} had the crash because {crash.cause.format(friend=friend.label)}. "
                "That small hazard broke the easy rhythm of the ride and made help necessary."
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
                f"After the sharing, {share.effect.lower()} "
                "That turned a stopping point into a gentle middle turn instead of the end of the ride."
            ),
        ),
        QAItem(
            question="What final image proves that sharing lasted past the repair?",
            answer=(
                "The final image shows both children on the golden bench breaking the plum bun in two. "
                "That picture proves the story ends in shared comfort, not only in a repaired bicycle."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    crash = CRASHES[world.params.crash]
    keys = ["bike_lane", "golden_cabin", "golden_bench", "kindness", "sharing", crash.need]
    return [KNOWLEDGE[key] for key in keys]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.friend:
        raise StoryError("Hero and friend must be different children.")
    if params.route not in ROUTES or params.crash not in CRASHES or params.share not in TOOLS:
        raise StoryError(explain_rejection(params.route, params.crash, params.share))
    route = ROUTES[params.route]
    crash = CRASHES[params.crash]
    share = TOOLS[params.share]
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
    from storyworlds import asp

    facts: list[str] = []
    for route in ROUTES.values():
        facts.append(asp.fact("route", route.id))
        for crash_id in route.allows:
            facts.append(asp.fact("allows", route.id, crash_id))
    for crash in CRASHES.values():
        facts.append(asp.fact("crash", crash.id))
        facts.append(asp.fact("needs", crash.id, crash.need))
    for share in TOOLS.values():
        facts.append(asp.fact("share", share.id))
        for need in share.handles:
            facts.append(asp.fact("handles", share.id, need))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    combos: set[tuple[str, str, str]] = set()
    for model in asp.solve(asp_facts() + ASP_RULES):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(part) for part in atom))  # type: ignore[arg-type]
    return sorted(combos)


def show_asp_program() -> str:
    return asp_facts() + ASP_RULES


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
        seed = (args.seed if args.seed is not None else 900) + idx
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
        if sample.world is None or sample.world.facts.get("ending") != "bench_shared_bun":
            raise StoryError(f"story for {params} did not reach the bench-sharing ending")
        if sample.world.facts.get("final_image") != "children_on_golden_bench_sharing_plum_bun":
            raise StoryError(f"story for {params} did not record the final image")
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
    parser.add_argument("--share", choices=sorted(TOOLS))
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
        share_id = args.share or sorted(TOOLS)[0]
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
                    "=== golden_cabin_crash_golden_bench_bike_lane_3 "
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
