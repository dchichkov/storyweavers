#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/interference_molasses_religious_repetition_inner_monologue_pirate.py
================================================================================================

A standalone story world about a small pirate sloop trying to reach a shore-side
religious festival with a delivery of molasses. The children rely on a harbor
signal, but interference scrambles or hides it. A sensible fix lets them slow
down, think clearly, and reach the dock safely.

Seed requirements covered directly in-world:
- the story text includes the words "interference", "molasses", and "religious"
- narration uses repetition
- narration includes inner monologue
- the style stays close to a gentle pirate tale

Run it
------
    python storyworlds/worlds/gpt-5.4/interference_molasses_religious_repetition_inner_monologue_pirate.py
    python storyworlds/worlds/gpt-5.4/interference_molasses_religious_repetition_inner_monologue_pirate.py --signal bells --interference thunder_static --fix wait_and_count
    python storyworlds/worlds/gpt-5.4/interference_molasses_religious_repetition_inner_monologue_pirate.py --signal lantern --interference gull_swarm --fix hush_parrot
    python storyworlds/worlds/gpt-5.4/interference_molasses_religious_repetition_inner_monologue_pirate.py --all
    python storyworlds/worlds/gpt-5.4/interference_molasses_religious_repetition_inner_monologue_pirate.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Destination:
    id: str
    island: str
    harbor: str
    religious_event: str
    building: str
    feast_food: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    channel: str
    line: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Interference:
    id: str
    label: str
    blocks: str
    onset: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    channel: str = ""
    guide_any: bool = False
    act: str = ""
    result: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    container: str
    slosh: str
    feast_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    destination: str
    signal: str
    interference: str
    fix: str
    cargo: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    adult: str
    captain_trait: str
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


def _r_slosh(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.entities.get("cargo")
    ship = world.entities.get("ship")
    if cargo is None or ship is None:
        return out
    if ship.meters["off_course"] < THRESHOLD:
        return out
    sig = ("slosh", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["sloshing"] += 1
    cargo.meters["sticky"] += 1
    out.append("__slosh__")
    return out


def _r_worry(world: World) -> list[str]:
    captain = world.entities.get("captain")
    ship = world.entities.get("ship")
    if captain is None or ship is None:
        return []
    if ship.meters["danger"] < THRESHOLD:
        return []
    sig = ("worry", captain.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="slosh", tag="physical", apply=_r_slosh),
    Rule(name="worry", tag="emotion", apply=_r_worry),
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
                produced.extend(sents)
    if narrate:
        cargo = world.entities.get("cargo")
        if cargo is not None and cargo.meters["sticky"] >= THRESHOLD and not world.facts.get("slosh_narrated"):
            world.facts["slosh_narrated"] = True
            cfg = world.facts["cargo_cfg"]
            world.say(
                f"The boat tipped the wrong way, and {cfg.slosh} slid across the deck. "
                f"The smell of molasses turned the air warm and sweet, but the sticky streak made the danger feel real."
            )
    return produced


DESTINATIONS = {
    "abbey_isle": Destination(
        id="abbey_isle",
        island="Abbey Isle",
        harbor="Bellwater Harbor",
        religious_event="a little religious lantern supper at the abbey",
        building="the white abbey on the hill",
        feast_food="spice buns",
        tags={"religious", "abbey"},
    ),
    "chapel_cove": Destination(
        id="chapel_cove",
        island="Chapel Cove",
        harbor="Candle Dock",
        religious_event="a small religious feast by the chapel",
        building="the blue-stone chapel by the shore",
        feast_food="ginger cakes",
        tags={"religious", "chapel"},
    ),
}

SIGNALS = {
    "bells": Signal(
        id="bells",
        label="prayer bells",
        channel="sound",
        line="The harbor could be found by the prayer bells from shore.",
        clue="the bell pattern",
        tags={"bells", "sound"},
    ),
    "lantern": Signal(
        id="lantern",
        label="the abbey lantern",
        channel="sight",
        line="The harbor could be found by the abbey lantern shining above the dock.",
        clue="the steady lantern glow",
        tags={"lantern", "light"},
    ),
    "hymn_horn": Signal(
        id="hymn_horn",
        label="the harbor horn after the hymn",
        channel="sound",
        line="The harbor could be found by the harbor horn that always sounded after the evening hymn.",
        clue="the horn after the hymn",
        tags={"horn", "sound", "religious"},
    ),
}

INTERFERENCES = {
    "thunder_static": Interference(
        id="thunder_static",
        label="thunder and crackling interference",
        blocks="sound",
        onset="A low storm growled far off, and thunder rolled over the water. The little radio spat with interference until every sound became a jumble.",
        danger="Without a clear sound to follow, the sloop drifted away from the safe channel.",
        tags={"interference", "thunder", "sound"},
    ),
    "gull_swarm": Interference(
        id="gull_swarm",
        label="a gull swarm",
        blocks="sight",
        onset="A whirl of gulls burst up from the rocks and beat their wings in front of the bow, a fluttering wall of interference over the water.",
        danger="With feathers and flapping everywhere, the crew could not see the harbor mark clearly.",
        tags={"interference", "gulls", "sight"},
    ),
    "parrot_chatter": Interference(
        id="parrot_chatter",
        label="the ship parrot's chatter",
        blocks="sound",
        onset="Cracker the parrot hopped onto the rail and began squawking right beside the receiver, turning the careful signal into noisy interference.",
        danger="The crew could hear noise, but not the useful part of the message.",
        tags={"interference", "parrot", "sound"},
    ),
}

FIXES = {
    "wait_and_count": Fix(
        id="wait_and_count",
        label="wait and count",
        handles={"thunder_static"},
        channel="sound",
        guide_any=False,
        act="dropped the sail a little, let the sloop rock gently, and counted the quiet spaces between the thunder",
        result="In one clean gap, the true harbor sound came through at last.",
        qa_text="They slowed down and counted through the thunder until the true harbor sound came through.",
        tags={"patience", "listening"},
    ),
    "climb_mast": Fix(
        id="climb_mast",
        label="climb the mast",
        handles={"gull_swarm"},
        channel="sight",
        guide_any=False,
        act="climbed halfway up the mast, above the worst of the wings, and shaded careful eyes with a hand",
        result="From higher up, the harbor mark showed itself again.",
        qa_text="They climbed high enough to see past the gulls and spot the harbor mark.",
        tags={"mast", "looking"},
    ),
    "hush_parrot": Fix(
        id="hush_parrot",
        label="hush the parrot",
        handles={"parrot_chatter"},
        channel="sound",
        guide_any=False,
        act="offered Cracker a biscuit crumb and gently covered the receiver with a thick cap so the squawks bounced away",
        result="With the chatter softened, the useful sound came back.",
        qa_text="They quieted the parrot and muffled the extra noise so they could hear the real signal.",
        tags={"parrot", "listening"},
    ),
    "rowboat_guide": Fix(
        id="rowboat_guide",
        label="follow a rowboat guide",
        handles={"thunder_static", "gull_swarm", "parrot_chatter"},
        channel="",
        guide_any=True,
        act="waved the striped harbor flag until a monastery rowboat came skipping over the dark water",
        result="A smiling dock guide lifted a lamp and led the little pirate sloop toward the posts.",
        qa_text="They asked for help, and a rowboat guide led them safely into the harbor.",
        tags={"helper", "guide"},
    ),
}

CARGOES = {
    "jar": Cargo(
        id="jar",
        label="jar",
        phrase="a round blue jar of molasses",
        container="jar",
        slosh="a brown ribbon of molasses from the jar",
        feast_use="to sweeten the abbey buns",
        tags={"molasses", "jar"},
    ),
    "crock": Cargo(
        id="crock",
        label="crock",
        phrase="a stout crock of molasses",
        container="crock",
        slosh="a sticky shine of molasses from the crock",
        feast_use="for the chapel cakes",
        tags={"molasses", "crock"},
    ),
    "barrel": Cargo(
        id="barrel",
        label="barrel",
        phrase="a small barrel of molasses",
        container="barrel",
        slosh="a dark drip of molasses from the barrel hoop",
        feast_use="for the harbor pudding",
        tags={"molasses", "barrel"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tess", "Nell", "June", "Rosa", "Ivy", "Mae"]
BOY_NAMES = ["Finn", "Toby", "Jory", "Ned", "Owen", "Pip", "Leo", "Cal"]
TRAITS = ["brave", "careful", "cheerful", "steady", "curious"]


def valid_fix(signal: Signal, interference: Interference, fix: Fix) -> bool:
    if interference.id not in fix.handles:
        return False
    if fix.guide_any:
        return True
    return signal.channel == fix.channel and interference.blocks == signal.channel


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for did in DESTINATIONS:
        for sid, signal in SIGNALS.items():
            for iid, interference in INTERFERENCES.items():
                for fid, fix in FIXES.items():
                    if valid_fix(signal, interference, fix):
                        combos.append((did, sid, iid, fid))
    return combos


def explain_rejection(signal: Signal, interference: Interference, fix: Fix) -> str:
    if interference.id not in fix.handles:
        return (
            f"(No story: {fix.label} does not address {interference.label}, so the interference would still be in the way.)"
        )
    return (
        f"(No story: {fix.label} is not the right kind of fix for {signal.label}. "
        f"The signal uses {signal.channel}, but that fix does not recover a {signal.channel}-based guide.)"
    )


@dataclass
class StoryBeat:
    text: str = ""


def introduce(world: World, captain: Entity, mate: Entity, adult: Entity, destination: Destination, cargo: Cargo) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a gold-blue evening, {captain.id} and {mate.id} sailed the little pirate sloop Pepperfin beside {adult.label_word} {adult.id}. "
        f"In the middle of the deck sat {cargo.phrase}, promised to {destination.religious_event} on {destination.island}."
    )
    world.say(
        f"The sweet cargo was for {cargo.feast_use}, and the children felt grand carrying something important over the shining sea."
    )


def set_course(world: World, captain: Entity, signal: Signal, destination: Destination) -> None:
    world.say(
        f'{captain.id} held the tiller as if it were the wheel of a treasure ship. "{signal.line}"'
    )
    world.say(
        f"{destination.building.capitalize()} waited beyond the mist, and somewhere ahead lay {destination.harbor}."
    )


def interference_strikes(world: World, captain: Entity, mate: Entity, signal: Signal, interference: Interference) -> None:
    ship = world.get("ship")
    ship.meters["danger"] += 1
    ship.meters["off_course"] += 1
    captain.memes["worry"] += 1
    mate.memes["worry"] += 1
    world.say(interference.onset)
    world.say(interference.danger)
    propagate(world, narrate=True)
    world.facts["blocked_clue"] = signal.clue


def inner_monologue(world: World, captain: Entity) -> None:
    captain.memes["thinking"] += 1
    if captain.memes["worry"] >= THRESHOLD:
        world.say(
            f'{captain.id} swallowed and told {captain.pronoun("object")}self, "Steady, steady, steady." '
            f'*Do not guess. Do not guess. Think first,* {captain.pronoun()} thought.'
        )
    else:
        world.say(
            f'*Easy now. Easy now,* {captain.id} thought.'
        )


def mate_warning(world: World, mate: Entity, captain: Entity, signal: Signal) -> None:
    mate.memes["care"] += 1
    world.say(
        f'"If we chase the first noise we hear, we may miss {signal.clue}," {mate.id} said. '
        f'"Slow, slow, slow."'
    )


def apply_fix(world: World, captain: Entity, mate: Entity, adult: Entity, fix: Fix, signal: Signal) -> None:
    ship = world.get("ship")
    captain.memes["courage"] += 1
    mate.memes["courage"] += 1
    world.say(
        f"So the little crew chose the sensible thing. {captain.id} and {mate.id} {fix.act}."
    )
    world.say(fix.result)
    ship.meters["danger"] = 0.0
    ship.meters["off_course"] = 0.0
    ship.meters["guided"] += 1
    world.facts["helper_used"] = fix.guide_any
    world.facts["adult_present"] = adult.id


def arrive(world: World, captain: Entity, mate: Entity, adult: Entity, destination: Destination, signal: Signal, cargo: Cargo, fix: Fix) -> None:
    captain.memes["relief"] += 1
    mate.memes["relief"] += 1
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f'Soon the posts of {destination.harbor} stood up from the water, one by one, and the pirates slipped between them safely.'
    )
    world.say(
        f'On the dock, warm lights glowed, and the people from {destination.building} waved when they saw the {cargo.container} of molasses arrive. '
        f'"You made it!" they called.'
    )
    if fix.guide_any:
        world.say(
            f"The rowboat guide tipped a lamp, and {adult.label_word} {adult.id} thanked the helper with a sailor's bow."
        )
    world.say(
        f"That night the children ate warm {destination.feast_food}, listened to the gentle religious songs from shore, and remembered how the sea had changed when they stopped hurrying and started thinking."
    )


def tell(
    destination: Destination,
    signal: Signal,
    interference: Interference,
    fix: Fix,
    cargo_cfg: Cargo,
    captain_name: str = "Mira",
    captain_gender: str = "girl",
    mate_name: str = "Finn",
    mate_gender: str = "boy",
    adult_type: str = "aunt",
    captain_trait: str = "steady",
) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    adult = world.add(Entity(id="Mara", kind="character", type=adult_type, role="adult", label="the grown-up"))
    ship = world.add(Entity(id="ship", type="sloop", label="Pepperfin"))
    cargo = world.add(Entity(id="cargo", type="cargo", label="molasses"))
    captain.attrs["trait"] = captain_trait

    world.facts.update(
        destination=destination,
        signal=signal,
        interference=interference,
        fix=fix,
        cargo_cfg=cargo_cfg,
        captain=captain,
        mate=mate,
        adult=adult,
    )

    introduce(world, captain, mate, adult, destination, cargo_cfg)
    set_course(world, captain, signal, destination)

    world.para()
    interference_strikes(world, captain, mate, signal, interference)
    inner_monologue(world, captain)
    mate_warning(world, mate, captain, signal)

    world.para()
    apply_fix(world, captain, mate, adult, fix, signal)
    arrive(world, captain, mate, adult, destination, signal, cargo_cfg, fix)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    destination = f["destination"]
    signal = f["signal"]
    interference = f["interference"]
    cargo = f["cargo_cfg"]
    return [
        'Write a short pirate tale for a young child that includes the words "interference", "molasses", and "religious".',
        f"Tell a gentle sea story where {captain.id} and {mate.id} carry {cargo.phrase} to {destination.religious_event}, but {interference.label} gets in the way of {signal.label}.",
        "Write the turning point with repetition and a clear inner monologue, then end with a safe harbor and a warm meal.",
    ]


KNOWLEDGE = {
    "molasses": [
        (
            "What is molasses?",
            "Molasses is a thick, dark, sweet syrup made when sugar is prepared. It pours slowly and feels sticky."
        )
    ],
    "interference": [
        (
            "What does interference mean?",
            "Interference is extra noise or something in the way that makes a message harder to hear or see clearly."
        )
    ],
    "religious": [
        (
            "What does religious mean?",
            "Religious means connected to prayer, worship, or the special beliefs and traditions people share."
        )
    ],
    "bells": [
        (
            "Why can bells help sailors near shore?",
            "A bell can repeat a clear sound through mist or darkness. Sailors can listen for the pattern and use it like a clue."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful at a harbor?",
            "A lantern makes a steady light that can show where the safe dock is. It helps boats steer toward the right place."
        )
    ],
    "parrot": [
        (
            "Why can a noisy parrot be a problem on a boat?",
            "If someone is trying to listen carefully, extra squawking can cover up the useful sounds. That makes it harder to hear an important message."
        )
    ],
    "gulls": [
        (
            "Why can gulls make it hard to see?",
            "A flock of gulls can flap right in front of your eyes. Their wings can hide the mark you are trying to spot."
        )
    ],
    "thunder": [
        (
            "Why is thunder hard to listen through?",
            "Thunder is loud and rumbly. It can cover smaller sounds, so careful listeners have to wait for a quiet gap."
        )
    ],
    "helper": [
        (
            "Why is asking for help brave?",
            "Asking for help is brave because it means you care more about doing something safely than pretending you can do everything alone."
        )
    ],
    "patience": [
        (
            "Why does slowing down help when you are confused?",
            "Slowing down gives your brain time to sort the clues. When you stop rushing, the right answer is easier to notice."
        )
    ],
}
KNOWLEDGE_ORDER = ["molasses", "interference", "religious", "bells", "lantern", "parrot", "gulls", "thunder", "helper", "patience"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    adult = f["adult"]
    destination = f["destination"]
    signal = f["signal"]
    interference = f["interference"]
    fix = f["fix"]
    cargo = f["cargo_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young pirates, {captain.id} and {mate.id}, sailing with {adult.label_word} {adult.id}. They were carrying {cargo.phrase} across the water."
        ),
        (
            "Where were they going with the molasses?",
            f"They were taking it to {destination.religious_event} on {destination.island}. The sweet cargo was meant {cargo.feast_use}."
        ),
        (
            f"What problem did the crew face near {destination.harbor}?",
            f"They depended on {signal.label}, but {interference.label} caused interference and hid the clue. Because of that, the little sloop began to drift away from the safe channel."
        ),
        (
            "What was the captain thinking when things felt scary?",
            f'{captain.id} told {captain.pronoun("object")}self, "Steady, steady, steady." Then {captain.pronoun()} thought that guessing would only make things worse, so the crew needed to think first.'
        ),
        (
            "How did they solve the problem?",
            f"{fix.qa_text} That sensible choice let them find the harbor without rushing."
        ),
        (
            "How did the story end?",
            f"They reached {destination.harbor} safely, delivered the molasses, and shared warm {destination.feast_food}. The ending shows that the crew changed from flustered and hurried to calm and careful."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"molasses", "interference", "religious"}
    signal = f["signal"]
    interference = f["interference"]
    fix = f["fix"]
    if signal.id == "bells":
        tags.add("bells")
    if signal.id == "lantern":
        tags.add("lantern")
    if interference.id == "parrot_chatter":
        tags.add("parrot")
    if interference.id == "gull_swarm":
        tags.add("gulls")
    if interference.id == "thunder_static":
        tags.add("thunder")
    if fix.guide_any:
        tags.add("helper")
    else:
        tags.add("patience")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        destination="abbey_isle",
        signal="bells",
        interference="thunder_static",
        fix="wait_and_count",
        cargo="jar",
        captain="Mira",
        captain_gender="girl",
        mate="Finn",
        mate_gender="boy",
        adult="aunt",
        captain_trait="steady",
    ),
    StoryParams(
        destination="chapel_cove",
        signal="lantern",
        interference="gull_swarm",
        fix="climb_mast",
        cargo="crock",
        captain="Tess",
        captain_gender="girl",
        mate="Pip",
        mate_gender="boy",
        adult="uncle",
        captain_trait="brave",
    ),
    StoryParams(
        destination="abbey_isle",
        signal="hymn_horn",
        interference="parrot_chatter",
        fix="hush_parrot",
        cargo="barrel",
        captain="Ned",
        captain_gender="boy",
        mate="June",
        mate_gender="girl",
        adult="aunt",
        captain_trait="careful",
    ),
    StoryParams(
        destination="chapel_cove",
        signal="bells",
        interference="gull_swarm",
        fix="rowboat_guide",
        cargo="jar",
        captain="Lina",
        captain_gender="girl",
        mate="Cal",
        mate_gender="boy",
        adult="uncle",
        captain_trait="cheerful",
    ),
]


ASP_RULES = r"""
works(F, I, C) :- handles(F, I), guide_any(F).
works(F, I, C) :- handles(F, I), fix_channel(F, C).

valid(D, S, I, F) :- destination(D), signal(S), interference(I), fix(F),
                     signal_channel(S, C), blocks(I, C), works(F, I, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did in DESTINATIONS:
        lines.append(asp.fact("destination", did))
    for sid, signal in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        lines.append(asp.fact("signal_channel", sid, signal.channel))
    for iid, interference in INTERFERENCES.items():
        lines.append(asp.fact("interference", iid))
        lines.append(asp.fact("blocks", iid, interference.blocks))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for handled in sorted(fix.handles):
            lines.append(asp.fact("handles", fid, handled))
        if fix.guide_any:
            lines.append(asp.fact("guide_any", fid))
        elif fix.channel:
            lines.append(asp.fact("fix_channel", fid, fix.channel))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate delivery of molasses, interference at sea, and a calm fix."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--interference", choices=INTERFERENCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--adult", choices=["aunt", "uncle", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.signal and args.interference and args.fix:
        signal = SIGNALS[args.signal]
        interference = INTERFERENCES[args.interference]
        fix = FIXES[args.fix]
        if not valid_fix(signal, interference, fix):
            raise StoryError(explain_rejection(signal, interference, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.signal is None or combo[1] == args.signal)
        and (args.interference is None or combo[2] == args.interference)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, signal, interference, fix = rng.choice(sorted(combos))
    cargo = args.cargo or rng.choice(sorted(CARGOES))
    captain_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if captain_gender == "girl" else "girl"
    captain = _pick_name(rng, captain_gender)
    mate = _pick_name(rng, mate_gender, avoid=captain)
    adult = args.adult or rng.choice(["aunt", "uncle", "mother", "father"])
    captain_trait = rng.choice(TRAITS)
    return StoryParams(
        destination=destination,
        signal=signal,
        interference=interference,
        fix=fix,
        cargo=cargo,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        adult=adult,
        captain_trait=captain_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        destination = DESTINATIONS[params.destination]
        signal = SIGNALS[params.signal]
        interference = INTERFERENCES[params.interference]
        fix = FIXES[params.fix]
        cargo = CARGOES[params.cargo]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]}.)") from None

    if not valid_fix(signal, interference, fix):
        raise StoryError(explain_rejection(signal, interference, fix))

    world = tell(
        destination=destination,
        signal=signal,
        interference=interference,
        fix=fix,
        cargo_cfg=cargo,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        adult_type=params.adult,
        captain_trait=params.captain_trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (destination, signal, interference, fix) combos:\n")
        for destination, signal, interference, fix in combos:
            print(f"  {destination:12} {signal:10} {interference:15} {fix}")
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
            header = (
                f"### {p.captain} & {p.mate}: {p.signal} vs {p.interference} "
                f"({p.destination}, fix: {p.fix})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
