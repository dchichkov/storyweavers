#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/play_wilderness_magic_inner_monologue_pirate_tale.py
==============================================================================

A standalone story world for a tiny, child-facing pirate-style wilderness tale
with magic and inner monologue.

Premise
-------
Two children turn a wild outdoor place into a pirate island. A sparkling magical
shortcut seems to promise treasure faster, but it leads off the safe trail into a
real snag or muddy patch. One child's inner thoughts pull in two directions:
the bold thought says hurry, and the careful thought says slow down. The story
branches among three reasonable outcomes:

* averted    -- the older cautioner talks the other child out of the shortcut
* rescued    -- the shortcut is taken, trouble starts, and a calm grown-up helps
* soaked     -- the trouble grows because help comes too late, though everyone
                still gets home safely

The world model drives the prose: physical meters track mud, snags, distance from
the path, and safety gear; emotional memes track thrill, caution, fear, relief,
trust, and the learned lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/play_wilderness_magic_inner_monologue_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/play_wilderness_magic_inner_monologue_pirate_tale.py --setting woods --hazard brambles
    python storyworlds/worlds/gpt-5.4/play_wilderness_magic_inner_monologue_pirate_tale.py --rescue wagon
    python storyworlds/worlds/gpt-5.4/play_wilderness_magic_inner_monologue_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/play_wilderness_magic_inner_monologue_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/play_wilderness_magic_inner_monologue_pirate_tale.py --qa --json
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

# Make the shared result containers importable when this script is run directly,
# even from a nested directory under storyworlds/worlds/.
_HERE = os.path.abspath(__file__)
_SEARCH = os.path.dirname(_HERE)
for _ in range(6):
    candidate = os.path.join(_SEARCH, "results.py")
    if os.path.exists(candidate):
        sys.path.insert(0, _SEARCH)
        break
    _SEARCH = os.path.dirname(_SEARCH)

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
    treasure: str
    pretend_line: str
    afford_hazards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    warning: str
    snag_text: str
    severity: int
    wet: bool = False
    snare: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class MagicLure:
    id: str
    label: str
    phrase: str
    whisper: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    gift: str
    gift_glow: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "mate"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lost_fear(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    room = world.get("place")
    if leader.meters["offtrail"] >= THRESHOLD:
        sig = ("offtrail",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["danger"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__offtrail__")
    return out


def _r_hazard_hits(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    hazard = world.get("hazard")
    if leader.meters["offtrail"] < THRESHOLD:
        return out
    if hazard.meters["ready"] < THRESHOLD:
        return out
    sig = ("hazard_hits", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.meters["trouble"] += 1
    if hazard.attrs.get("wet"):
        leader.meters["wet"] += 1
        leader.meters["muddy"] += 1
    if hazard.attrs.get("snare"):
        leader.meters["snagged"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__hazard__")
    return out


CAUSAL_RULES = [
    Rule(name="lost_fear", tag="social", apply=_r_lost_fear),
    Rule(name="hazard_hits", tag="physical", apply=_r_hazard_hits),
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


def hazard_at_risk(setting: Setting, hazard: Hazard) -> bool:
    return hazard.id in setting.afford_hazards


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def trouble_severity(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def is_managed(rescue: Rescue, hazard: Hazard, delay: int) -> bool:
    return rescue.power >= trouble_severity(hazard, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, leader_age: int, mate_age: int, trait: str) -> bool:
    mate_older = relation == "siblings" and mate_age > leader_age
    authority = initial_caution(trait) + 1.0 + (3.0 if mate_older else 0.0)
    return mate_older and authority > BRAVERY_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    take_shortcut(sim, narrate=False)
    leader = sim.get("leader")
    place = sim.get("place")
    return {
        "offtrail": leader.meters["offtrail"] >= THRESHOLD,
        "trouble": leader.meters["trouble"] >= THRESHOLD,
        "danger": place.meters["danger"],
    }


def take_shortcut(world: World, narrate: bool = True) -> None:
    leader = world.get("leader")
    leader.meters["offtrail"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, leader: Entity, mate: Entity, setting: Setting) -> None:
    for kid in (leader, mate):
        kid.memes["joy"] += 1
        kid.memes["play"] += 1
    world.say(
        f"On a bright afternoon, {leader.id} and {mate.id} turned {setting.place} into {setting.scene}. "
        f"{setting.pretend_line}"
    )
    world.say(
        f'"Captain {leader.id}!" {mate.id} cheered. "{setting.treasure} is waiting!"'
    )


def dark_need(world: World, mate: Entity, setting: Setting) -> None:
    world.say(
        f"But the path toward {setting.dark_spot} looked twisty and wild, like real wilderness instead of a backyard game."
    )
    world.say(
        f'{mate.id} peered ahead. "It looks exciting," {mate.pronoun()} said, "but we should stay where the path still shows."'
    )


def temptation(world: World, leader: Entity, lure: MagicLure) -> None:
    leader.memes["thrill"] += 1
    world.say(
        f"Then {lure.phrase} shimmered beside the leaves. It {lure.glow}."
    )
    world.say(
        f'{leader.id} heard a tiny thought in {leader.pronoun("possessive")} own head: '
        f'"If I hurry, I can find the treasure first."'
    )
    world.say(
        f'Another thought answered more softly: "{lure.whisper}"'
    )


def warning(world: World, mate: Entity, leader: Entity, hazard: Hazard, parent: Entity) -> None:
    pred = predict_trouble(world)
    mate.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{mate.id} caught {leader.id}\'s sleeve. "{parent.label_word.capitalize()} said side paths can fool you," '
        f'{mate.pronoun()} said. "If you follow the shining shortcut, {hazard.warning}."'
    )


def defy(world: World, leader: Entity, mate: Entity, lure: MagicLure) -> None:
    leader.memes["defiance"] += 1
    world.say(
        f'"Just one quick look," {leader.id} said. The bold little thought in {leader.pronoun("possessive")} head felt louder than the careful one.'
    )
    world.say(
        f"{leader.id} stepped after {lure.label}, and {mate.id} hurried close behind."
    )
    take_shortcut(world, narrate=False)


def back_down(world: World, leader: Entity, mate: Entity, setting: Setting, parent: Entity) -> None:
    leader.memes["relief"] += 1
    mate.memes["relief"] += 1
    leader.memes["defiance"] = 0.0
    rel = "big brother" if mate.type == "boy" else "big sister"
    world.say(
        f'{leader.id} took one step toward the glittering side path, then looked at {mate.id}. '
        f'{mate.id} was {leader.pronoun("possessive")} {rel}, and the careful thought finally won.'
    )
    world.say(
        f'"No secret shortcut," {leader.id} decided. "Real pirates can still play fair." '
        f'They stayed on the path and called for {parent.label_word} to come see the wild place with them.'
    )
    world.facts["inner_winner"] = "careful"


def stumble(world: World, leader: Entity, hazard: Hazard) -> None:
    hazard_ent = world.get("hazard")
    hazard_ent.meters["ready"] += 1
    propagate(world, narrate=False)
    if hazard.wet and hazard.snare:
        world.say(
            f"The shining trail slipped under a tangle of roots. In one blink, {leader.id} splashed knee-deep and got caught in {hazard.the}."
        )
    elif hazard.wet:
        world.say(
            f"The shining trail ended with a soggy plop. {leader.id} stepped into {hazard.the} and muddy water splashed up."
        )
    else:
        world.say(
            f"The shining trail ended in a scratchy rustle. {leader.id} pushed too close and {hazard.snag_text}."
        )
    world.say(
        f'{leader.id}\'s brave thought vanished. "Oh no," {leader.pronoun()} whispered.'
    )
    world.facts["inner_winner"] = "bold"


def alarm(world: World, mate: Entity, leader: Entity, parent: Entity, hazard: Hazard) -> None:
    world.say(
        f'"{parent.label_word.upper()}!" {mate.id} shouted. "{leader.id} is stuck by {hazard.the}!"'
    )


def rescue_success(world: World, parent: Entity, rescue: Rescue, leader: Entity, hazard: Hazard) -> None:
    leader.meters["trouble"] = 0.0
    leader.meters["offtrail"] = 0.0
    world.get("place").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {rescue.text}."
    )
    if leader.meters["snagged"] >= THRESHOLD:
        leader.meters["snagged"] = 0.0
    world.say(
        f"Soon the path felt safe again, though {leader.id}'s knees were shaky and {leader.pronoun('possessive')} boots were a mess."
    )


def rescue_fail(world: World, parent: Entity, rescue: Rescue, leader: Entity, hazard: Hazard) -> None:
    leader.meters["offtrail"] += 1
    world.get("place").meters["danger"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {rescue.fail}."
    )
    world.say(
        f"But the side ground was worse than it had looked, and everyone had to slog the long way back through the wet wilderness edge."
    )


def lesson(world: World, parent: Entity, leader: Entity, mate: Entity, setting: Setting) -> None:
    for kid in (leader, mate):
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say("For a moment, nobody spoke except the leaves.")
    world.say(
        f'Then {parent.label_word.capitalize()} crouched beside them. "Adventures are for play," {parent.pronoun()} said, '
        f'"but real wilderness needs slow feet and listening hearts. Magic is lovely when it helps you notice, not when it pulls you off the path."'
    )
    world.say(
        f'{leader.id} nodded. "{leader.pronoun("subject").capitalize()} heard two thoughts," {mate.id} said softly. '
        f'"Next time we pick the careful one."'
    )


def safe_gift(world: World, parent: Entity, leader: Entity, mate: Entity, rescue: Rescue, setting: Setting) -> None:
    for kid in (leader, mate):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word} brought them {rescue.gift} that {rescue.gift_glow}."
    )
    world.say(
        f'"Now your pirate trail can still feel magic," {parent.pronoun()} smiled, "and it can stay on the safe path too."'
    )
    world.say(
        f'{leader.id} held it high. {mate.id} grinned. Together they marched toward {setting.dark_spot}, still playing pirates, but this time the careful thought walked in front.'
    )


def soaked_ending(world: World, parent: Entity, leader: Entity, mate: Entity, rescue: Rescue, setting: Setting) -> None:
    for kid in (leader, mate):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f"By the time they reached the porch, socks squished, sleeves dripped, and nobody felt like treasure-hunting anymore."
    )
    world.say(
        f'{parent.label_word.capitalize()} wrapped both children in towels. "You are safe, and that matters most," {parent.pronoun()} said. '
        f'"But glittering shortcuts are not always friendly magic."'
    )
    world.say(
        f"After that, whenever their pirate game reached the wilderness edge, {leader.id} stopped to listen for the quieter thought before taking another step."
    )


def tell(
    setting: Setting,
    hazard: Hazard,
    lure: MagicLure,
    rescue: Rescue,
    leader_name: str = "Tom",
    leader_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    leader_age: int = 6,
    mate_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            role="leader",
            traits=["bold"],
            age=leader_age,
            attrs={"relation": relation},
        )
    )
    mate = world.add(
        Entity(
            id=mate_name,
            kind="character",
            type=mate_gender,
            role="mate",
            traits=[trait],
            age=mate_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    place = world.add(
        Entity(
            id="place",
            type="place",
            label=setting.place,
            tags=set(setting.tags),
        )
    )
    hazard_ent = world.add(
        Entity(
            id="hazard",
            type="hazard",
            label=hazard.label,
            tags=set(hazard.tags),
            attrs={"wet": hazard.wet, "snare": hazard.snare},
        )
    )
    world.add(
        Entity(
            id="lure",
            type="magic",
            label=lure.label,
            tags=set(lure.tags),
        )
    )

    leader.memes["bravery"] = BRAVERY_INIT
    mate.memes["caution"] = initial_caution(trait)

    play_setup(world, leader, mate, setting)
    dark_need(world, mate, setting)

    world.para()
    temptation(world, leader, lure)
    warning(world, mate, leader, hazard, parent)

    averted = would_avert(relation, leader_age, mate_age, trait)
    if averted:
        back_down(world, leader, mate, setting, parent)
        world.para()
        safe_gift(world, parent, leader, mate, rescue, setting)
        contained = True
    else:
        defy(world, leader, mate, lure)
        world.para()
        stumble(world, leader, hazard)
        alarm(world, mate, leader, parent, hazard)
        world.para()
        contained = is_managed(rescue, hazard, delay)
        if contained:
            rescue_success(world, parent, rescue, leader, hazard)
            lesson(world, parent, leader, mate, setting)
            world.para()
            safe_gift(world, parent, leader, mate, rescue, setting)
        else:
            rescue_fail(world, parent, rescue, leader, hazard)
            soaked_ending(world, parent, leader, mate, rescue, setting)

    outcome = "averted" if averted else ("rescued" if contained else "soaked")
    world.facts.update(
        setting=setting,
        hazard_cfg=hazard,
        lure=lure,
        rescue=rescue,
        leader=leader,
        mate=mate,
        parent=parent,
        place=place,
        hazard=hazard_ent,
        delay=delay,
        outcome=outcome,
        relation=relation,
        managed=contained,
        trouble=leader.meters["trouble"] >= THRESHOLD or leader.meters["wet"] >= THRESHOLD or leader.meters["snagged"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "woods": Setting(
        id="woods",
        place="the little woods behind the fence",
        scene="a pirate island at the edge of the world",
        dark_spot="the fern arch",
        treasure="The shell chest",
        pretend_line="A fallen branch became their mast, a stick map marked hidden coves, and a flat stone was the captain's deck.",
        afford_hazards={"brambles", "bog"},
        tags={"wilderness", "woods"},
    ),
    "dunes": Setting(
        id="dunes",
        place="the sandy dunes by the path",
        scene="a wind-blown pirate coast",
        dark_spot="the hollow between the dunes",
        treasure="The pearl chest",
        pretend_line="A driftwood plank became their ship, a scarf was their sail, and their bucket held shiny shell coins.",
        afford_hazards={"bog", "roots"},
        tags={"wilderness", "dunes", "sand"},
    ),
    "grove": Setting(
        id="grove",
        place="the willow grove near the garden",
        scene="a secret pirate cove",
        dark_spot="the green tunnel under the branches",
        treasure="The moon chest",
        pretend_line="A garden crate became their ship, a spoon was their silver hook, and a paper map curled like an old sea chart.",
        afford_hazards={"brambles", "roots"},
        tags={"wilderness", "grove"},
    ),
}

HAZARDS = {
    "brambles": Hazard(
        id="brambles",
        label="brambles",
        the="the brambles",
        warning="the thorns can grab your clothes and skin",
        snag_text="the brambles tugged at shirt and sock at once",
        severity=2,
        wet=False,
        snare=True,
        tags={"brambles", "thorns"},
    ),
    "bog": Hazard(
        id="bog",
        label="muddy hollow",
        the="the muddy hollow",
        warning="the ground can swallow your boots in sticky mud",
        snag_text="the mud sucked at one boot",
        severity=3,
        wet=True,
        snare=False,
        tags={"mud", "bog"},
    ),
    "roots": Hazard(
        id="roots",
        label="root tangle",
        the="the root tangle",
        warning="the roots can catch your feet and tip you down",
        snag_text="the root tangle hooked around one ankle",
        severity=2,
        wet=False,
        snare=True,
        tags={"roots", "trip"},
    ),
}

LURES = {
    "fireflies": MagicLure(
        id="fireflies",
        label="the starry fireflies",
        phrase="a string of starry fireflies",
        whisper="Slow captains finish adventures too.",
        glow="winked like little pirate lanterns",
        tags={"magic", "fireflies"},
    ),
    "whisper_shell": MagicLure(
        id="whisper_shell",
        label="the whispering shell",
        phrase="a pale shell on a stump",
        whisper="A true map is safer than a hurried guess.",
        glow="hummed with a silvery shine",
        tags={"magic", "shell"},
    ),
    "moss_arrow": MagicLure(
        id="moss_arrow",
        label="the moss arrow",
        phrase="a mossy arrow shape on a stone",
        whisper="Treasure that matters will wait for kind feet.",
        glow="gleamed as if moonlight had landed on it",
        tags={"magic", "moss"},
    ),
}

RESCUES = {
    "lantern": Rescue(
        id="lantern",
        sense=3,
        power=3,
        text="followed their voices, lifted the leader over the rough spot, and guided both children back with a battery lantern",
        fail="found them and turned on a lantern, but the mud and distance made the walk back much slower than anyone wanted",
        qa_text="guided them back with a battery lantern",
        gift="a little trail lantern",
        gift_glow="shone with a warm golden circle",
        tags={"lantern", "safe_path"},
    ),
    "rope": Rescue(
        id="rope",
        sense=3,
        power=2,
        text="looped a short garden rope around a safe branch and helped the leader step back onto firm ground",
        fail="threw a rope toward them, but the slippery edge meant everyone still had to wade carefully out together",
        qa_text="used a rope to help the child back onto firm ground",
        gift="a striped path rope for pirate games",
        gift_glow="coiled neatly and came with bright ribbon markers",
        tags={"rope", "safe_path"},
    ),
    "wagon": Rescue(
        id="wagon",
        sense=2,
        power=2,
        text="came with the red garden wagon, pulled them away from the rough patch, and rolled them back to the safe path",
        fail="brought the wagon as close as possible, but the ground was so soggy that it stuck and everyone still got soaked",
        qa_text="pulled them back in the garden wagon",
        gift="a red wagon flag that clipped to their pretend ship",
        gift_glow="fluttered bright enough to mark the safe trail",
        tags={"wagon", "safe_path"},
    ),
    "tug_hand": Rescue(
        id="tug_hand",
        sense=1,
        power=1,
        text="just tugged on one hand until the child stumbled back out",
        fail="grabbed for one hand, but the spot was far too awkward for that to work well",
        qa_text="pulled on one hand",
        gift="a plain towel",
        gift_glow="did not glow at all",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "bright"]


@dataclass
class StoryParams:
    setting: str
    hazard: str
    lure: str
    rescue: str
    leader: str
    leader_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    delay: int = 0
    leader_age: int = 6
    mate_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "wilderness": [
        (
            "What does wilderness mean?",
            "Wilderness means a place that feels wild and not carefully built by people. It can have trees, roots, tall grass, or muddy ground that needs careful feet.",
        )
    ],
    "magic": [
        (
            "What kind of magic is safe in a pretend game?",
            "Safe magic in a pretend game is the kind that helps you notice beauty or imagine adventure. It should never tell you to ignore real safety.",
        )
    ],
    "inner_voice": [
        (
            "What is an inner thought?",
            "An inner thought is a voice you hear inside your own mind. Sometimes one thought wants to rush, and another reminds you to slow down and choose carefully.",
        )
    ],
    "brambles": [
        (
            "Why are brambles tricky?",
            "Brambles have thin thorny stems that can scratch skin and catch clothes. That is why it is better to stay on a clear path near them.",
        )
    ],
    "bog": [
        (
            "Why is sticky mud hard to walk in?",
            "Sticky mud grabs at shoes and makes feet sink down. That can make walking slow and wobbly.",
        )
    ],
    "roots": [
        (
            "Why can roots make people trip?",
            "Roots stick up from the ground, so a foot can catch on them if you do not look carefully. Uneven ground needs slow steps.",
        )
    ],
    "lantern": [
        (
            "Why is a battery lantern useful outdoors?",
            "A battery lantern makes light without any flame. It helps people see the path while staying safe.",
        )
    ],
    "rope": [
        (
            "What is a rope useful for on a trail?",
            "A rope can help someone hold steady or pull from a safer place. Grown-ups use it carefully so nobody slips more.",
        )
    ],
    "wagon": [
        (
            "Why can a wagon help after a muddy adventure?",
            "A wagon can carry tired or muddy things back to a dry place. It is helpful when the ground is hard for little legs.",
        )
    ],
    "safe_path": [
        (
            "Why should children stay on the path in wild places?",
            "Paths are usually the safest way to walk because people can see the ground more clearly there. Side places may hide thorns, mud, or roots.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "wilderness",
    "magic",
    "inner_voice",
    "brambles",
    "bog",
    "roots",
    "lantern",
    "rope",
    "wagon",
    "safe_path",
]


def pair_noun(leader: Entity, mate: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and mate.type == "boy":
            return "two brothers"
        if leader.type == "girl" and mate.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    mate = f["mate"]
    setting = f["setting"]
    hazard = f["hazard_cfg"]
    lure = f["lure"]
    rescue = f["rescue"]
    outcome = f["outcome"]
    base = (
        f'Write a short pirate-style story for a 3-to-5-year-old that includes the words "play" and "wilderness", '
        f"uses a magical shortcut and inner monologue, and takes place in {setting.place}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {leader.id} hears a bold thought and a careful thought, and listens to {mate.id} instead of following {lure.label} into {hazard.the}.",
            f"Write a pretend pirate adventure where the children keep their play magical but stay on the safe path, ending with a bright new trail tool.",
        ]
    if outcome == "rescued":
        return [
            base,
            f"Tell a story where {leader.id} follows {lure.label} off the path, gets into trouble with {hazard.the}, and a calm grown-up helps using {rescue.id}.",
            f"Write a child-facing magical wilderness tale with a clear warning, a frightened middle turn, and a safe pirate ending.",
        ]
    return [
        base,
        f"Tell a cautionary pirate adventure where the shortcut looks magical, but {hazard.the} turns the game into a cold muddy mess before the family gets back safely.",
        f"Write a story where an inner brave thought makes a poor choice, then a quieter careful thought becomes the lesson at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    mate = f["mate"]
    parent = f["parent"]
    setting = f["setting"]
    hazard = f["hazard_cfg"]
    lure = f["lure"]
    rescue = f["rescue"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(leader, mate, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {mate.id}, who were playing pirates in {setting.place}. Their {pw} helped them when the game brushed against a real wild place.",
        ),
        (
            "What were they pretending?",
            f"They turned the place into {setting.scene} and hunted for {setting.treasure}. Their pirate play made the ordinary path feel like an adventure.",
        ),
        (
            "What magical thing tempted the leader?",
            f"{lure.phrase.capitalize()} tempted {leader.id} to hurry off the path. It looked helpful at first, but it pulled the adventure toward a real risk.",
        ),
        (
            "What happened inside the leader's mind?",
            f"{leader.id} heard two thoughts: a bold one that wanted to rush and a careful one that wanted to slow down. The story's choice turns on which inner thought wins.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Why did {leader.id} stay on the path?",
                f"{leader.id} trusted {mate.id}'s warning and let the careful inner thought win. Because they stayed on the path, the pirate game could go on without anyone getting hurt or stuck.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely with a new trail tool for their games. The ending shows that the children still got magic and play, but in a wiser way.",
            )
        )
    elif outcome == "rescued":
        qa.append(
            (
                f"What trouble did {leader.id} get into?",
                f"{leader.id} followed the shortcut and ran into {hazard.the}. That changed the game from pretend danger to real trouble, which is why {mate.id} called for help.",
            )
        )
        qa.append(
            (
                f"How did the grown-up help?",
                f"{pw.capitalize()} {rescue.qa_text}. The help mattered because the children were off the safe path and too frightened to fix the problem alone.",
            )
        )
        qa.append(
            (
                "What lesson did they learn?",
                f"They learned that wild places need slow feet, even during play. The magic should help them notice beauty, not trick them into ignoring safety.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the trip back feel so hard?",
                f"The trouble had grown before help reached them, so the ground was wet and awkward all the way home. That is why everyone came back safe but tired, cold, and messy.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended on the porch with towels, wet socks, and a quiet lesson. The children were safe, but the soggy ending proved that glittering shortcuts are not always kind.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"wilderness", "magic", "inner_voice", "safe_path"}
    hazard = f["hazard_cfg"]
    rescue = f["rescue"]
    if hazard.id == "brambles":
        tags.add("brambles")
    elif hazard.id == "bog":
        tags.add("bog")
    elif hazard.id == "roots":
        tags.add("roots")
    if rescue.id in {"lantern", "rope", "wagon"}:
        tags.add(rescue.id)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="woods",
        hazard="brambles",
        lure="fireflies",
        rescue="lantern",
        leader="Tom",
        leader_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        leader_age=6,
        mate_age=4,
        relation="siblings",
    ),
    StoryParams(
        setting="grove",
        hazard="roots",
        lure="whisper_shell",
        rescue="rope",
        leader="Mia",
        leader_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        leader_age=5,
        mate_age=7,
        relation="siblings",
    ),
    StoryParams(
        setting="dunes",
        hazard="bog",
        lure="moss_arrow",
        rescue="wagon",
        leader="Sam",
        leader_gender="boy",
        mate="Zoe",
        mate_gender="girl",
        parent="mother",
        trait="bright",
        delay=1,
        leader_age=6,
        mate_age=5,
        relation="friends",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, setting in SETTINGS.items():
        for hid, hazard in HAZARDS.items():
            if hazard_at_risk(setting, hazard):
                combos.append((sid, hid))
    return combos


def explain_rejection(setting: Setting, hazard: Hazard) -> str:
    return (
        f"(No story: {hazard.the.capitalize()} do not fit {setting.place}. "
        f"This world only tells shortcuts-into-trouble stories when that wild place could really hide the chosen hazard.)"
    )


def explain_rescue(rid: str) -> str:
    rescue = RESCUES[rid]
    better = ", ".join(sorted(r.id for r in sensible_rescues()))
    return (
        f"(Refusing rescue '{rid}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). Try one of these steadier helpers: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.leader_age, params.mate_age, params.trait):
        return "averted"
    contained = is_managed(RESCUES[params.rescue], HAZARDS[params.hazard], params.delay)
    return "rescued" if contained else "soaked"


ASP_RULES = r"""
hazard_at_risk(S, H) :- setting(S), hazard(H), fits(S, H).
sensible(R) :- rescue(R), sense(R, V), sense_min(M), V >= M.
valid(S, H) :- hazard_at_risk(S, H).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

mate_older :- relation(siblings), leader_age(LA), mate_age(MA), MA > LA.
bonus(3) :- mate_older.
bonus(0) :- not mate_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- mate_older, authority(A), bravery_init(BR), A > BR.

severity(SV + D) :- chosen_hazard(H), hazard_severity(H, SV), delay(D).
resc_power(P) :- chosen_rescue(R), power(R, P).
managed :- resc_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(rescued) :- not averted, managed.
outcome(soaked) :- not averted, not managed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.afford_hazards):
            lines.append(asp.fact("fits", sid, hid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_severity", hid, hazard.severity))
    for lid in LURES:
        lines.append(asp.fact("lure", lid))
    for rid, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, rescue.sense))
        lines.append(asp.fact("power", rid, rescue.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_rescue", params.rescue),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("leader_age", params.leader_age),
            asp.fact("mate_age", params.mate_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    py_sensible = {r.id for r in sensible_rescues()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible rescues match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            args = parser.parse_args([])
            p = resolve_params(args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during verify seed {s}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test story was empty.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play, wilderness, safe magic, and an inner choice. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="How long trouble grows before help arrives.")
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hazard:
        if not hazard_at_risk(SETTINGS[args.setting], HAZARDS[args.hazard]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], HAZARDS[args.hazard]))
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(args.rescue))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.hazard is None or c[1] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hazard_id = rng.choice(sorted(combos))
    lure_id = args.lure or rng.choice(sorted(LURES))
    rescue_id = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    leader, leader_gender = _pick_kid(rng)
    mate, mate_gender = _pick_kid(rng, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    leader_age, mate_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        setting=setting_id,
        hazard=hazard_id,
        lure=lure_id,
        rescue=rescue_id,
        leader=leader,
        leader_gender=leader_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        leader_age=leader_age,
        mate_age=mate_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if not hazard_at_risk(SETTINGS[params.setting], HAZARDS[params.hazard]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], HAZARDS[params.hazard]))
    if RESCUES[params.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(params.rescue))

    world = tell(
        setting=SETTINGS[params.setting],
        hazard=HAZARDS[params.hazard],
        lure=LURES[params.lure],
        rescue=RESCUES[params.rescue],
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        leader_age=params.leader_age,
        mate_age=params.mate_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible rescues: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hazard) combos:\n")
        for setting_id, hazard_id in combos:
            print(f"  {setting_id:8} {hazard_id}")
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
            header = f"### {p.leader} & {p.mate}: {p.setting}, {p.hazard}, {p.rescue} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
