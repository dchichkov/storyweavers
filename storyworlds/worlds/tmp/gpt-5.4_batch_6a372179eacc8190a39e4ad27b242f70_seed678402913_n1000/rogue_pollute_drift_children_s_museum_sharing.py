#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rogue_pollute_drift_children_s_museum_sharing.py
============================================================================

A standalone storyworld about a grand shared water exhibit in a children's
museum. One child is tempted by a rogue material that would pollute the water
and spoil everybody's floating boats. Another child uses a remembered rhyme
(a flashback to the museum guide's rule) to warn them. Depending on the social
setup and the chosen cleanup method, the trouble is either averted in time or a
small mess happens and is sensibly repaired before the children learn to share
the safe decorations instead.

Run it
------
    python storyworlds/worlds/gpt-5.4/rogue_pollute_drift_children_s_museum_sharing.py
    python storyworlds/worlds/gpt-5.4/rogue_pollute_drift_children_s_museum_sharing.py --theme harbor --rogue glitter_mud
    python storyworlds/worlds/gpt-5.4/rogue_pollute_drift_children_s_museum_sharing.py --cleanup towel_swipe
    python storyworlds/worlds/gpt-5.4/rogue_pollute_drift_children_s_museum_sharing.py --all
    python storyworlds/worlds/gpt-5.4/rogue_pollute_drift_children_s_museum_sharing.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rogue_pollute_drift_children_s_museum_sharing.py --verify
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
BOLDNESS_INIT = 6.0
MEMORY_STRONG = {"careful", "thoughtful", "remembering", "steady"}


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
    polluting: bool = False
    shareable: bool = False
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "educator"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "educator": "guide"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    museum_place: str
    big_image: str
    water_name: str
    start_line: str
    boat_word: str
    finish_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RogueMaterial:
    id: str
    label: str
    phrase: str
    source: str
    splash_text: str
    dirty_word: str
    spread: int
    polluting: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTrim:
    id: str
    label: str
    phrase: str
    action: str
    image: str
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cleanup:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_pollute(world: World) -> list[str]:
    out: list[str] = []
    canal = world.get("canal")
    if canal.meters["polluted"] < THRESHOLD:
        return out
    sig = ("pollute", "canal")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for boat_id in ("boat_a", "boat_b"):
        if boat_id in world.entities:
            boat = world.get(boat_id)
            boat.meters["stuck"] += 1
            boat.meters["drift_bad"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__polluted__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    stash = world.get("trim")
    if stash.meters["shared"] < THRESHOLD:
        return out
    sig = ("share", "trim")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for boat_id in ("boat_a", "boat_b"):
        if boat_id in world.entities:
            boat = world.get(boat_id)
            boat.meters["pretty"] += 1
            boat.meters["drift_good"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["belonging"] += 1
    out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule(name="pollute", tag="physical", apply=_r_pollute),
    Rule(name="share", tag="social", apply=_r_share),
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


def hazard_at_risk(rogue: RogueMaterial) -> bool:
    return rogue.polluting and rogue.spread > 0


def sensible_cleanups() -> list[Cleanup]:
    return [c for c in CLEANUPS.values() if c.sense >= SENSE_MIN]


def spill_severity(rogue: RogueMaterial, delay: int) -> int:
    return rogue.spread + delay


def is_restored(cleanup: Cleanup, rogue: RogueMaterial, delay: int) -> bool:
    return cleanup.power >= spill_severity(rogue, delay)


def initial_memory(trait: str) -> float:
    return 5.0 if trait in MEMORY_STRONG else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_memory(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > BOLDNESS_INIT


def predict_spill(world: World, rogue: RogueMaterial) -> dict:
    sim = world.copy()
    do_spill(sim, rogue, narrate=False)
    return {
        "polluted": sim.get("canal").meters["polluted"] >= THRESHOLD,
        "boats_stuck": sum(
            1
            for bid in ("boat_a", "boat_b")
            if bid in sim.entities and sim.get(bid).meters["stuck"] >= THRESHOLD
        ),
    }


def introduce(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["wonder"] += 1
    world.say(
        f"At the children's museum, {theme.museum_place} stretched before {a.id} "
        f"and {b.id} so grandly that it looked big enough for giants. {theme.big_image}"
    )
    world.say(theme.start_line.format(a=a.id, b=b.id))


def launch_boats(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f"They set two little {theme.boat_word}s on {theme.water_name}, and the boats began to drift "
        f"past tiny bridges and toy reeds."
    )
    world.say(
        f'Soon {a.id} was cheering so loudly that the paper gulls overhead seemed to flap faster.'
    )


def tempt(world: World, a: Entity, rogue: RogueMaterial) -> None:
    a.memes["boldness"] += 1
    world.say(
        f"Then {a.id} spotted {rogue.phrase} {rogue.source}. It looked like a rogue treasure, "
        f"the sort of sneaky thing a storm king might hide in his pocket."
    )
    world.say(
        f'"If I pour in just a little," {a.id} said, "my boat will leave the wildest trail in the whole museum!"'
    )


def flashback_warn(world: World, b: Entity, a: Entity, rogue: RogueMaterial, guide: Entity) -> None:
    pred = predict_spill(world, rogue)
    b.memes["memory"] += 1
    world.facts["predicted_stuck"] = pred["boats_stuck"]
    rhyme = world.facts["rhyme"]
    world.say(
        f"{b.id} froze for a blink, and then a flashback came fluttering back: earlier that morning, "
        f"{guide.label_word} had tapped the rail and taught them a rhyme."
    )
    world.say(f'"{rhyme}"')
    world.say(
        f'{b.id} grabbed the edge of the basin and whispered, "{a.id}, that would pollute the water. '
        f'If the water turns {rogue.dirty_word}, all the boats can drift wrong, not just ours."'
    )


def back_down(world: World, a: Entity, b: Entity, rogue: RogueMaterial) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at the jar, then at {b.id}, and the giant plan shrank down to the size of a pea."
    )
    world.say(
        f'"You are right," {a.pronoun()} said. "A rogue trick is not worth spoiling the river for everyone." '
        f"So {a.id} set {rogue.label} back where it belonged."
    )


def do_spill(world: World, rogue: RogueMaterial, narrate: bool = True) -> None:
    canal = world.get("canal")
    canal.meters["polluted"] += 1
    canal.meters["murky"] += 1
    canal.meters["severity"] = float(world.facts.get("severity", rogue.spread))
    propagate(world, narrate=narrate)


def spill(world: World, a: Entity, rogue: RogueMaterial, theme: Theme) -> None:
    do_spill(world, rogue, narrate=False)
    world.say(
        f"But the plan rushed ahead too fast. {rogue.splash_text} into {theme.water_name}, and in one swirly breath "
        f"the clear current turned {rogue.dirty_word}."
    )
    world.say(
        f"The boats bobbed, spun, and stopped behaving like boats at all. Instead of gliding, they seemed to drift in grumpy little circles."
    )


def alarm(world: World, b: Entity, guide: Entity) -> None:
    world.say(f'"{guide.label_word.capitalize()}!" {b.id} cried. "The water is cloudy!"')


def cleanup_scene(world: World, guide: Entity, cleanup: Cleanup, theme: Theme) -> None:
    world.say(
        f"{guide.label_word.capitalize()} came quickly, calm as a lighthouse in a thunder tale. "
        f"{guide.pronoun().capitalize()} {cleanup.text}."
    )
    world.say(
        f"Little by little, {theme.water_name} cleared again, and the worried room let out one long breath."
    )


def cleanup_fail_scene(world: World, guide: Entity, cleanup: Cleanup, theme: Theme) -> None:
    world.say(
        f"{guide.label_word.capitalize()} hurried over and {cleanup.fail}."
    )
    world.say(
        f"For the rest of the afternoon, {theme.water_name} stayed too cloudy for proper sailing, and the exhibit had to rest."
    )


def lesson(world: World, guide: Entity, a: Entity, b: Entity, rogue: RogueMaterial) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["alarm"] = 0.0
        kid.memes["care"] += 1
    rhyme = world.facts["rhyme"]
    world.say(
        f"{guide.label_word.capitalize()} knelt beside them. "
        f'"Shared water is for everybody," {guide.pronoun()} said softly. '
        f'"Even a little rogue mess can pollute a big play river."'
    )
    world.say(
        f'Then {guide.pronoun()} smiled and said the rhyme again: "{rhyme}"'
    )
    world.say(
        f"{a.id} nodded hard. {b.id} nodded too. They both knew the rule belonged in their heads now."
    )


def share_trim(world: World, a: Entity, b: Entity, trim: SafeTrim, theme: Theme) -> None:
    stash = world.get("trim")
    stash.meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Instead of reaching for trouble, the children opened {trim.phrase} and shared every bright bit. "
        f"{trim.action}"
    )
    world.say(
        f"Soon one boat wore a sunny tail and the other wore a moon-blue flap, and together they looked finer than a parade."
    )
    world.say(
        f"{trim.image} On the clean current, both boats could drift side by side."
    )
    world.say(theme.finish_line.format(a=a.id, b=b.id))


def tell(
    theme: Theme,
    rogue: RogueMaterial,
    trim: SafeTrim,
    cleanup: Cleanup,
    *,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    guide_type: str = "educator",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 7,
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            traits=["bold"],
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    guide = world.add(
        Entity(
            id="Guide",
            kind="character",
            type=guide_type,
            role="guide",
            label="the museum guide",
        )
    )
    canal = world.add(
        Entity(
            id="canal",
            type="canal",
            label=theme.water_name,
        )
    )
    boat_a = world.add(Entity(id="boat_a", type="boat", label=f"{a.id}'s boat"))
    boat_b = world.add(Entity(id="boat_b", type="boat", label=f"{b.id}'s boat"))
    trim_ent = world.add(
        Entity(
            id="trim",
            type="trim",
            label=trim.label,
            phrase=trim.phrase,
            shareable=True,
        )
    )

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["memory"] = initial_memory(trait)
    rhyme = "Share the stream and keep it clean; let all boats drift bright and keen."

    introduce(world, a, b, theme)
    launch_boats(world, a, b, theme)

    world.para()
    tempt(world, a, rogue)
    flashback_warn(world, b, a, rogue, guide)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    severity = spill_severity(rogue, delay)
    world.facts["severity"] = severity

    if averted:
        back_down(world, a, b, rogue)
        world.para()
        share_trim(world, a, b, trim, theme)
        outcome = "averted"
        restored = True
    else:
        world.say(f'"Maybe just a sparkle," {a.id} said, and tipped the jar.')
        world.para()
        spill(world, a, rogue, theme)
        alarm(world, b, guide)

        restored = is_restored(cleanup, rogue, delay)
        world.para()
        if restored:
            cleanup_scene(world, guide, cleanup, theme)
            lesson(world, guide, a, b, rogue)
            world.para()
            share_trim(world, a, b, trim, theme)
            outcome = "restored"
        else:
            cleanup_fail_scene(world, guide, cleanup, theme)
            lesson(world, guide, a, b, rogue)
            world.say(
                f"That day the boats had to come out of the water and wait on the railing, still as sleepy ducks."
            )
            world.say(
                f"But before they left, {a.id} and {b.id} shared the safe decorations anyway, promising they would return to make the river shine the right way."
            )
            outcome = "clouded"

    world.facts.update(
        theme=theme,
        rogue=rogue,
        trim=trim,
        cleanup=cleanup,
        instigator=a,
        cautioner=b,
        guide=guide,
        canal=canal,
        rhyme=rhyme,
        relation=relation,
        averted=averted,
        restored=restored,
        outcome=outcome,
        severity=severity,
        delay=delay,
        polluted=canal.meters["polluted"] >= THRESHOLD,
    )
    return world


THEMES = {
    "harbor": Theme(
        id="harbor",
        museum_place="the Make-Believe Harbor Hall",
        big_image="A silver canal curved around the room like a river trying to visit every exhibit at once.",
        water_name="the harbor canal",
        start_line='"Today," said {a}, "my boat will sail farther than a parade." "{b} laughed. "Only if mine does not get there first."',
        boat_word="sailboat",
        finish_line="By the end, {a} and {b} were laughing together, and the whole hall seemed pleased that the river belonged to everyone.",
        tags={"water", "museum"},
    ),
    "cloud": Theme(
        id="cloud",
        museum_place="the Cloud Canal Room",
        big_image="The water track looped under cottony arches and around puff-shaped pillars until it looked as if a rainstorm had learned manners.",
        water_name="the cloud canal",
        start_line='"These boats can outrun thunder," {a} bragged. "{b} grinned. "Then let us race the weather."',
        boat_word="cloud-boat",
        finish_line="When they finally stepped back, {a} and {b} watched the little fleet glide under the white arches in peaceful pairs.",
        tags={"water", "museum"},
    ),
    "moon": Theme(
        id="moon",
        museum_place="the Moon River Corner",
        big_image="Blue lights shone on the winding trough so that every ripple looked like a night sky that had decided to flow.",
        water_name="the moon river",
        start_line='"Look," said {a}, "our boats are sailing on a fallen piece of evening." "{b} answered, "Then let us be kind captains."',
        boat_word="moon-boat",
        finish_line="At last the boats drifted beneath the blue lamps as neatly as stars taking turns across the sky.",
        tags={"water", "museum"},
    ),
}

ROGUES = {
    "glitter_mud": RogueMaterial(
        id="glitter_mud",
        label="the glitter-mud jar",
        phrase="a squat jar of glitter-mud",
        source="on a side shelf beside the closed experiment cards",
        splash_text="A ribbon of glittery brown slosh tumbled",
        dirty_word="brown and sparkly in a bad way",
        spread=2,
        polluting=True,
        tags={"pollute", "water", "glitter"},
    ),
    "confetti_slime": RogueMaterial(
        id="confetti_slime",
        label="the confetti-slime cup",
        phrase="a wobbling cup of confetti slime",
        source="near the craft sink where it should have stayed",
        splash_text="A gloppy rope of sticky slime plopped",
        dirty_word="sticky and flecked with paper bits",
        spread=2,
        polluting=True,
        tags={"pollute", "water", "slime"},
    ),
    "sand_paint": RogueMaterial(
        id="sand_paint",
        label="the sand-paint tub",
        phrase="a little tub of sandy paint",
        source="under a sign that belonged to another station",
        splash_text="A creamy streak of sandy paint spilled",
        dirty_word="gritty and cloudy",
        spread=1,
        polluting=True,
        tags={"pollute", "water", "paint"},
    ),
}

TRIMS = {
    "ribbons": SafeTrim(
        id="ribbons",
        label="ribbons",
        phrase="the box of clip-on ribbons",
        action="They clipped colors to both boats so each child had plenty.",
        image="The ribbons fluttered like tiny festival flags.",
        shareable=True,
        tags={"sharing", "ribbon"},
    ),
    "foam_flags": SafeTrim(
        id="foam_flags",
        label="foam flags",
        phrase="the tray of foam flags",
        action="They took turns choosing shapes and passed the rest across with open hands.",
        image="The little flags stood up proudly without touching the water.",
        shareable=True,
        tags={"sharing", "flag"},
    ),
    "star_clips": SafeTrim(
        id="star_clips",
        label="star clips",
        phrase="the tin of star clips",
        action="They snapped bright stars onto both boats until neither one felt left out.",
        image="The stars winked in the museum lights.",
        shareable=True,
        tags={"sharing", "star"},
    ),
}

CLEANUPS = {
    "filter_net": Cleanup(
        id="filter_net",
        sense=3,
        power=3,
        text="lifted the floating filter net, swept the mess into it, and ran clean water through the channel",
        fail="tried the filter net, but the sticky clumps kept breaking apart and drifting away",
        qa_text="used the filter net and fresh water to clear the canal",
        tags={"cleanup", "water"},
    ),
    "drain_refill": Cleanup(
        id="drain_refill",
        sense=3,
        power=4,
        text="opened the little drain gate, rinsed the channel, and sent a fresh clear stream through it again",
        fail="opened the drain gate, but too much gritty muck was already caught in the bends",
        qa_text="drained and refilled the canal",
        tags={"cleanup", "water"},
    ),
    "towel_swipe": Cleanup(
        id="towel_swipe",
        sense=1,
        power=1,
        text="dragged a towel across the top of the water",
        fail="swiped with a towel, but that only chased the mess from one side to the other",
        qa_text="wiped at the water with a towel",
        tags={"cleanup", "water"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Max", "Ben", "Leo", "Sam", "Finn", "Theo", "Eli", "Jack"]
TRAITS = ["careful", "thoughtful", "remembering", "steady", "quick", "curious"]


@dataclass
class StoryParams:
    theme: str
    rogue: str
    trim: str
    cleanup: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    guide_type: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 7
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="harbor",
        rogue="glitter_mud",
        trim="ribbons",
        cleanup="filter_net",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        guide_type="educator",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        delay=0,
    ),
    StoryParams(
        theme="cloud",
        rogue="confetti_slime",
        trim="foam_flags",
        cleanup="drain_refill",
        instigator="Zoe",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        guide_type="educator",
        trait="thoughtful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        delay=0,
    ),
    StoryParams(
        theme="moon",
        rogue="glitter_mud",
        trim="star_clips",
        cleanup="filter_net",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        guide_type="educator",
        trait="quick",
        relation="friends",
        instigator_age=6,
        cautioner_age=5,
        delay=1,
    ),
    StoryParams(
        theme="harbor",
        rogue="confetti_slime",
        trim="ribbons",
        cleanup="drain_refill",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ella",
        cautioner_gender="girl",
        guide_type="educator",
        trait="remembering",
        relation="siblings",
        instigator_age=4,
        cautioner_age=7,
        delay=0,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for rogue_id, rogue in ROGUES.items():
            if not hazard_at_risk(rogue):
                continue
            for trim_id in TRIMS:
                for cleanup_id, cleanup in CLEANUPS.items():
                    if cleanup.sense >= SENSE_MIN:
                        combos.append((theme_id, rogue_id, trim_id, cleanup_id))
    return combos


KNOWLEDGE = {
    "museum": [
        (
            "What is a children's museum?",
            "A children's museum is a place where kids can touch, build, test, and pretend while they learn. The exhibits are made for hands-on play."
        )
    ],
    "water": [
        (
            "Why should shared play water stay clean?",
            "Shared play water should stay clean so everybody can use it safely and so the exhibit works the way it should. When the water gets dirty, it can stop toys from moving well."
        )
    ],
    "pollute": [
        (
            "What does pollute mean?",
            "Pollute means to make water, air, or land dirty in a way that does not belong there. Even a small mess can spread and cause bigger trouble."
        )
    ],
    "sharing": [
        (
            "Why is sharing important at a museum exhibit?",
            "Sharing is important because many children use the same tools and spaces. When children share, everyone gets a turn and the play works better for the whole group."
        )
    ],
    "cleanup": [
        (
            "Why do grown-ups clean a water exhibit carefully?",
            "They clean it carefully so the water can be clear again and the exhibit can work properly. A good cleanup fixes the problem instead of pushing the mess around."
        )
    ],
    "glitter": [
        (
            "Why can glittery mud be a bad thing in water?",
            "Glittery mud can make the water cloudy and gritty. That can clog or slow things that are supposed to float and move."
        )
    ],
    "slime": [
        (
            "Why is slime a bad thing to pour into shared water?",
            "Slime is sticky, so it can cling to the sides and to floating toys. That makes the water harder to use and harder to clean."
        )
    ],
    "paint": [
        (
            "Why should paint stay at the paint station?",
            "Paint belongs at the paint station because it is made for paper and brushes there. In shared water, it can turn the whole area messy."
        )
    ],
    "ribbon": [
        (
            "What can ribbons do on a toy boat?",
            "Ribbons can decorate a toy boat and flutter in the air. They make the boat look special without dirtying the water."
        )
    ],
    "flag": [
        (
            "What is a foam flag?",
            "A foam flag is a soft, light decoration that can stand on a toy or craft. It adds color without dissolving into the water."
        )
    ],
    "star": [
        (
            "What is a star clip?",
            "A star clip is a little clip shaped like a star that can attach to a toy or paper craft. It decorates without making a watery mess."
        )
    ],
}
KNOWLEDGE_ORDER = ["museum", "water", "pollute", "sharing", "cleanup", "glitter", "slime", "paint", "ribbon", "flag", "star"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    rogue = f["rogue"]
    trim = f["trim"]
    theme = f["theme"]
    rhyme = f["rhyme"]
    outcome = f["outcome"]
    base = (
        f'Write a Tall Tale for a 3-to-5-year-old set in a children\'s museum. '
        f'Include the words "rogue", "pollute", and "drift", and use Sharing, Flashback, and Rhyme.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a story where {a.id} is tempted by {rogue.label}, but {b.id} remembers a rhyme and stops the mess before it starts.",
            f'Write a museum boat story with a flashback to a guide\'s rhyme, a sharing ending with {trim.label}, and this line: "{rhyme}"',
        ]
    if outcome == "restored":
        return [
            base,
            f"Tell a story where {a.id} tips {rogue.label} into {theme.water_name}, the water gets messy, and a calm guide helps fix it before the children share safe decorations.",
            f'Write a cautionary Tall Tale where a rogue idea almost ruins a shared exhibit, but a wise cleanup and a remembered rhyme lead to a happy ending.',
        ]
    return [
        base,
        f"Tell a story where {a.id} makes the water too cloudy for proper sailing, and the children still end by sharing safe decorations and promising to do better.",
        f'Write a museum river story where the rhyme "{rhyme}" becomes an important lesson after a bad choice.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    guide = f["guide"]
    theme = f["theme"]
    rogue = f["rogue"]
    trim = f["trim"]
    cleanup = f["cleanup"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, at a children's museum water exhibit, and the guide who helps them. The story follows what happens when one grand idea forgets that the river is shared."
        ),
        (
            "What were they doing at the museum?",
            f"They were floating little boats on {theme.water_name} and pretending the exhibit was enormous. The boats were meant to drift through the channel while the children watched and played together."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} remembered the guide's rhyme from earlier that day, so a flashback helped {b.pronoun()} understand the danger. {b.id} knew {rogue.label} would pollute the shared water and spoil the drifting for everyone."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {a.id}'s mind?",
                f"{a.id} listened when {b.id} repeated the rhyme and explained the problem. Because the warning felt true and caring, {a.pronoun()} put the rogue material back instead of pouring it in."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children sharing {trim.label} and decorating both boats fairly. The river stayed clean, and the boats could drift side by side."
            )
        )
    elif f["outcome"] == "restored":
        qa.append(
            (
                "What happened when the rogue material went into the water?",
                f"The water turned messy, and the boats stopped gliding properly. Because the canal was polluted, the boats began to drift badly and got stuck instead of sailing smoothly."
            )
        )
        qa.append(
            (
                f"How did the guide fix the problem?",
                f"The guide {cleanup.qa_text}. That careful cleanup restored the exhibit, and after that the children used safe decorations they could share."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that shared play water belongs to everyone, so even a small selfish choice can cause a big mess. They also learned that sharing safe materials makes the game better for both children."
            )
        )
    else:
        qa.append(
            (
                "Was the exhibit fully fixed right away?",
                f"No. The cleanup was not strong enough, so the water stayed too cloudy for proper sailing that day. Even so, the children still learned the rule and chose to share the safe decorations."
            )
        )
        qa.append(
            (
                "How did the ending still show a change?",
                f"The children no longer grabbed at the rogue material. Instead, they shared {trim.label} and promised to come back ready to care for the river properly."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"museum", "water", "pollute", "sharing", "cleanup"}
    tags |= set(f["rogue"].tags)
    tags |= set(f["trim"].tags)
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(rogue: RogueMaterial) -> str:
    return (
        f"(No story: {rogue.label} would not make a meaningful water mess here, so there is no honest museum-river problem to solve.)"
    )


def explain_cleanup(cleanup_id: str) -> str:
    cleanup = CLEANUPS[cleanup_id]
    better = ", ".join(sorted(c.id for c in sensible_cleanups()))
    return (
        f"(Refusing cleanup '{cleanup_id}': it scores too low on common sense "
        f"(sense={cleanup.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "restored" if is_restored(CLEANUPS[params.cleanup], ROGUES[params.rogue], params.delay) else "clouded"


ASP_RULES = r"""
hazard(R) :- rogue(R), polluting(R), spread(R, S), S > 0.
sensible(C) :- cleanup(C), sense(C, S), sense_min(M), S >= M.
valid(T, R, Tr, C) :- theme(T), hazard(R), trim(Tr), sensible(C).

cautious_now(T) :- trait(T), strong_memory(T).
init_memory(5) :- trait(T), cautious_now(T).
init_memory(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(M + 1 + B) :- init_memory(M), bonus(B).
averted :- older_sibling, authority(A), boldness_init(BI), A > BI.

severity(S + D) :- chosen_rogue(R), spread(R, S), delay(D).
restored :- chosen_cleanup(C), power(C, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(restored) :- not averted, restored.
outcome(clouded) :- not averted, not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for rogue_id, rogue in ROGUES.items():
        lines.append(asp.fact("rogue", rogue_id))
        if rogue.polluting:
            lines.append(asp.fact("polluting", rogue_id))
        lines.append(asp.fact("spread", rogue_id, rogue.spread))
    for trim_id in TRIMS:
        lines.append(asp.fact("trim", trim_id))
    for cleanup_id, cleanup in CLEANUPS.items():
        lines.append(asp.fact("cleanup", cleanup_id))
        lines.append(asp.fact("sense", cleanup_id, cleanup.sense))
        lines.append(asp.fact("power", cleanup_id, cleanup.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(MEMORY_STRONG):
        lines.append(asp.fact("strong_memory", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_cleanups() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_rogue", params.rogue),
            asp.fact("chosen_cleanup", params.cleanup),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    c_sens = set(asp_sensible_cleanups())
    p_sens = {c.id for c in sensible_cleanups()}
    if c_sens == p_sens:
        print(f"OK: sensible cleanups match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible cleanups: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rogue museum-river mess, a remembered rhyme, and sharing."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--rogue", choices=ROGUES)
    ap.add_argument("--trim", choices=TRIMS)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--guide-type", choices=["educator"], dest="guide_type")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the mess gets before cleanup")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rogue and not hazard_at_risk(ROGUES[args.rogue]):
        raise StoryError(explain_rejection(ROGUES[args.rogue]))
    if args.cleanup and CLEANUPS[args.cleanup].sense < SENSE_MIN:
        raise StoryError(explain_cleanup(args.cleanup))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.rogue is None or combo[1] == args.rogue)
        and (args.trim is None or combo[2] == args.trim)
        and (args.cleanup is None or combo[3] == args.cleanup)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, rogue_id, trim_id, cleanup_id = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trait = rng.choice(TRAITS)
    guide_type = args.guide_type or "educator"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        theme=theme_id,
        rogue=rogue_id,
        trim=trim_id,
        cleanup=cleanup_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        guide_type=guide_type,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.rogue not in ROGUES:
        raise StoryError(f"Unknown rogue material: {params.rogue}")
    if params.trim not in TRIMS:
        raise StoryError(f"Unknown trim: {params.trim}")
    if params.cleanup not in CLEANUPS:
        raise StoryError(f"Unknown cleanup: {params.cleanup}")
    if not hazard_at_risk(ROGUES[params.rogue]):
        raise StoryError(explain_rejection(ROGUES[params.rogue]))
    if CLEANUPS[params.cleanup].sense < SENSE_MIN:
        raise StoryError(explain_cleanup(params.cleanup))

    world = tell(
        THEMES[params.theme],
        ROGUES[params.rogue],
        TRIMS[params.trim],
        CLEANUPS[params.cleanup],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        guide_type=params.guide_type,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        delay=params.delay,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible cleanups: {', '.join(asp_sensible_cleanups())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, rogue, trim, cleanup) combos:\n")
        for theme_id, rogue_id, trim_id, cleanup_id in combos:
            print(f"  {theme_id:8} {rogue_id:14} {trim_id:10} {cleanup_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.rogue} at {p.theme} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
