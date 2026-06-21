#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/brain_eject_problem_solving_reconciliation_flashback_ghost.py
=========================================================================================

A standalone story world for a gentle ghost story shaped around problem solving,
a flashback, and reconciliation.

Premise
-------
On a quiet evening, a child meets a lonely ghost near an old machine that should
eject a memory cassette. The cassette holds an apology the ghost never managed to
share while alive. The child uses their brain, asks a grown-up for the safe fix,
and the machine finally plays. Its sound opens a flashback, an old hurt is
mended, and the room changes from chilly to warm.

This world prefers a small number of plausible stories over broad coverage:
* the device must actually accept the memory medium
* the chosen fix must safely match the jam
* unreasonable fixes are known to the world but refused

Run it
------
python storyworlds/worlds/gpt-5.4/brain_eject_problem_solving_reconciliation_flashback_ghost.py
python storyworlds/worlds/gpt-5.4/brain_eject_problem_solving_reconciliation_flashback_ghost.py --all
python storyworlds/worlds/gpt-5.4/brain_eject_problem_solving_reconciliation_flashback_ghost.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/brain_eject_problem_solving_reconciliation_flashback_ghost.py --qa --json
python storyworlds/worlds/gpt-5.4/brain_eject_problem_solving_reconciliation_flashback_ghost.py --verify
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
# from the repo root or from this nested directory.
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "aunt", "teacher"}
        male = {"boy", "man", "grandfather", "uncle", "neighbor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return self.attrs.get("title", self.label or self.id)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    eerie: str
    hiding_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    medium: str
    jam: str
    button: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Memory:
    id: str
    medium: str
    ghost_name: str
    elder_name: str
    elder_title: str
    elder_type: str
    relation: str
    quarrel: str
    apology: str
    image: str
    keepsake: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    handles: set[str]
    text: str
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


def _r_jam_chill(world: World) -> list[str]:
    device = world.entities.get("device")
    ghost = world.entities.get("ghost")
    room = world.entities.get("room")
    if not device or not ghost or not room:
        return []
    if device.meters["jammed"] < THRESHOLD:
        return []
    sig = ("jam_chill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["chill"] += 1
    ghost.memes["worry"] += 1
    return []


def _r_play_flashback(world: World) -> list[str]:
    device = world.entities.get("device")
    ghost = world.entities.get("ghost")
    elder = world.entities.get("elder")
    if not device or not ghost or not elder:
        return []
    if device.meters["playing"] < THRESHOLD:
        return []
    sig = ("play_flashback",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["memory"] += 1
    elder.memes["remembering"] += 1
    return []


def _r_reconcile_warm(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    elder = world.entities.get("elder")
    room = world.entities.get("room")
    if not ghost or not elder or not room:
        return []
    if ghost.memes["forgiven"] < THRESHOLD or elder.memes["softened"] < THRESHOLD:
        return []
    sig = ("reconcile_warm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["peace"] += 1
    room.meters["warmth"] += 1
    room.meters["chill"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="jam_chill", tag="physical", apply=_r_jam_chill),
    Rule(name="play_flashback", tag="memory", apply=_r_play_flashback),
    Rule(name="reconcile_warm", tag="social", apply=_r_reconcile_warm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif rule.name in {name for (name, *_) in world.fired}:
                pass
        # Detect newly fired rules even when they do not narrate.
        current = len(world.fired)
        if current > getattr(propagate, "_last_count", -1):
            changed = changed or current != getattr(propagate, "_last_count", -1)
        propagate._last_count = current
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def medium_matches(device: Device, memory: Memory) -> bool:
    return device.medium == memory.medium


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def fix_works(device: Device, fix: Fix) -> bool:
    return device.jam in fix.handles


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for device_id, device in DEVICES.items():
            for memory_id, memory in MEMORIES.items():
                if not medium_matches(device, memory):
                    continue
                for fix_id, fix in FIXES.items():
                    if fix.sense >= SENSE_MIN and fix_works(device, fix):
                        combos.append((place_id, device_id, memory_id, fix_id))
    return combos


def outcome_of(device: Device, memory: Memory, fix: Fix) -> str:
    if not medium_matches(device, memory):
        return "silent"
    if not fix_works(device, fix):
        return "restless"
    return "reconciled"


def explain_medium(device: Device, memory: Memory) -> str:
    return (
        f"(No story: {device.phrase} uses {device.medium}, but this memory lives on "
        f"{memory.medium}. The ghost cannot play an apology from the wrong kind of object.)"
    )


def explain_fix(fix: Fix, device: Device) -> str:
    better = ", ".join(sorted(f.id for f in sensible_fixes() if fix_works(device, f)))
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Try a calmer, safer fix like {better}.)"
        )
    return (
        f"(No story: {fix.id} does not solve a {device.jam.replace('_', ' ')} on "
        f"{device.label}. Try one of: {better}.)"
    )


def predict_resolution(world: World) -> dict:
    sim = world.copy()
    device = sim.get("device")
    device.meters["playing"] += 1
    propagate(sim, narrate=False)
    ghost = sim.get("ghost")
    elder = sim.get("elder")
    return {
        "flashback": ghost.memes["memory"] >= THRESHOLD,
        "remembering": elder.memes["remembering"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"One evening, {child.id} followed {elder.title} up to {place.phrase}. "
        f"{place.eerie}"
    )
    world.say(
        f"In {place.hiding_spot}, dust lay still, but one tiny blue light winked as if it had been waiting."
    )


def reveal_ghost(world: World, child: Entity, ghost: Entity, device: Device) -> None:
    child.memes["fear"] += 1
    ghost.memes["shy"] += 1
    world.say(
        f"Beside {device.phrase} stood a pale child-shaped ghost with hands folded tight. "
        f'"Please do not run," whispered {ghost.id}. "I only need it to {device.button}."'
    )
    world.say(
        f"{child.id}'s heart jumped, but the ghost looked more lonely than fierce."
    )


def show_problem(world: World, child: Entity, ghost: Entity, device: Device, memory: Memory) -> None:
    device.meters["jammed"] += 1
    ghost.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"There is an apology on the old {memory.medium}," {ghost.id} said. '
        f'"I never got to play it for {memory.elder_name}. The button should {device.button}, '
        f'but it only makes a sad {device.sound}."'
    )
    world.say(
        f"{child.id} looked at the stuck machine and felt {child.pronoun('possessive')} brain begin to work."
    )


def choose_fix(world: World, child: Entity, elder: Entity, device: Device, fix: Fix) -> None:
    child.memes["brave"] += 1
    child.memes["care"] += 1
    elder.memes["trust"] += 1
    world.say(
        f'"Let us think before we poke at anything," said {elder.title}. '
        f'{child.id} nodded and pointed at the machine. "{fix.text}"'
    )


def solve(world: World, elder: Entity, device: Device, fix: Fix) -> None:
    device.meters["jammed"] = 0.0
    device.meters["open"] += 1
    world.say(
        f"Together they did exactly that. The old machine gave one surprised click, and the little door slid open at last."
    )
    world.say(
        f"Inside sat the missing {world.facts['memory'].medium}, safe and dusty, as if it had been holding its breath."
    )
    device.meters["playing"] += 1
    propagate(world, narrate=False)


def flashback(world: World, ghost: Entity, elder: Entity, memory: Memory) -> None:
    world.say(
        f"When {elder.title} pressed play, the room filled with a thin, trembling voice. "
        f"At once the shadows changed."
    )
    world.say(
        f"{memory.ghost_name} and {memory.elder_name} were small again in the flashback, "
        f"{memory.quarrel}. {memory.image}"
    )
    world.say(
        f'Then the younger ghost-voice said, "{memory.apology}"'
    )


def reconcile(world: World, ghost: Entity, elder: Entity, memory: Memory) -> None:
    elder.memes["softened"] += 1
    ghost.memes["forgiven"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{elder.title} put a hand over {elder.pronoun('possessive')} mouth for a moment, then smiled through wet eyes."
    )
    world.say(
        f'"Oh, {memory.ghost_name}," {elder.pronoun()} said softly. "I was lonely too. '
        f'I forgave you long ago, and I am sorry for my sharp words that day."'
    )
    world.say(
        f"The ghost's shoulders loosened, as if an invisible knot had finally come undone."
    )


def ending(world: World, child: Entity, ghost: Entity, elder: Entity, memory: Memory, place: Place) -> None:
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    ghost.memes["peace"] += 1
    world.say(
        f"The air in {place.label} no longer felt cold. It smelled only of cedar, dust, and rain on the roof."
    )
    world.say(
        f"{ghost.id} touched the {memory.keepsake} beside the machine, gave {child.id} a grateful nod, and grew as faint as moon mist."
    )
    world.say(
        f'Before fading, {ghost.pronoun()} whispered, "Thank you for using your brain kindly."'
    )
    world.say(
        f"{child.id} walked downstairs holding {elder.title}'s hand, and the house sounded peaceful at last."
    )


def tell(
    place: Place,
    device: Device,
    memory: Memory,
    fix: Fix,
    child_name: str = "Lina",
    child_gender: str = "girl",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={"trait": trait},
    ))
    elder = world.add(Entity(
        id=memory.elder_name,
        kind="character",
        type=memory.elder_type,
        role="elder",
        label=memory.elder_name,
        attrs={"title": memory.elder_title},
    ))
    ghost = world.add(Entity(
        id=memory.ghost_name,
        kind="character",
        type="ghost",
        role="ghost",
        label=memory.ghost_name,
        attrs={"relation": memory.relation},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=place.label,
    ))
    machine = world.add(Entity(
        id="device",
        kind="thing",
        type="device",
        label=device.label,
        phrase=device.phrase,
        attrs={"button": device.button, "jam": device.jam},
    ))
    keepsake = world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=memory.keepsake,
        phrase=f"the {memory.keepsake}",
    ))

    world.facts.update(
        place=place,
        device=device,
        memory=memory,
        fix=fix,
        child=child,
        elder=elder,
        ghost=ghost,
        room=room,
        keepsake=keepsake,
    )

    introduce(world, child, elder, place)
    world.para()
    reveal_ghost(world, child, ghost, device)
    show_problem(world, child, ghost, device, memory)
    world.para()
    choose_fix(world, child, elder, device, fix)
    solve(world, elder, machine, fix)
    world.para()
    flashback(world, ghost, elder, memory)
    world.para()
    reconcile(world, ghost, elder, memory)
    world.para()
    ending(world, child, ghost, elder, memory, place)

    world.facts.update(
        flashback_seen=ghost.memes["memory"] >= THRESHOLD,
        reconciled=ghost.memes["peace"] >= THRESHOLD or room.meters["warmth"] >= THRESHOLD,
        peaceful=room.meters["warmth"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        phrase="the attic above the old stairs",
        eerie="The rafters creaked softly, and the air smelled like cedar trunks and long-kept secrets.",
        hiding_spot="a corner behind three hat boxes",
        tags={"attic", "ghost"},
    ),
    "music_room": Place(
        id="music_room",
        label="the music room",
        phrase="the music room at the back of the house",
        eerie="Moonlight lay across the piano keys, and every framed song sheet seemed to listen.",
        hiding_spot="the shelf under the metronome",
        tags={"music", "ghost"},
    ),
    "landing": Place(
        id="landing",
        label="the upstairs landing",
        phrase="the upstairs landing beside the linen closet",
        eerie="The wallpaper flowers looked silver in the dim light, and the floorboards whispered under each step.",
        hiding_spot="a narrow table under the round window",
        tags={"hallway", "ghost"},
    ),
}

DEVICES = {
    "cassette_player": Device(
        id="cassette_player",
        label="cassette player",
        phrase="a square cassette player with a cracked clear lid",
        medium="cassette",
        jam="sticky_eject",
        button="eject",
        sound="clack",
        tags={"cassette", "machine"},
    ),
    "answering_machine": Device(
        id="answering_machine",
        label="answering machine",
        phrase="an answering machine with a yellowed speaker",
        medium="microcassette",
        jam="battery_sleep",
        button="eject",
        sound="buzz",
        tags={"cassette", "machine"},
    ),
    "tape_deck": Device(
        id="tape_deck",
        label="tape deck",
        phrase="a long silver tape deck tucked under a cloth",
        medium="cassette",
        jam="crooked_tape",
        button="eject",
        sound="whirr",
        tags={"cassette", "machine"},
    ),
}

MEMORIES = {
    "kite_apology": Memory(
        id="kite_apology",
        medium="cassette",
        ghost_name="Nell",
        elder_name="Ruth",
        elder_title="Grandma Ruth",
        elder_type="grandmother",
        relation="sister",
        quarrel="arguing over a red kite on the windy hill behind the school",
        apology="Ruth, I should have shared the string and said I was sorry before the storm came.",
        image="The torn kite tail snapped like a little flag, and both girls looked too proud to speak first.",
        keepsake="red kite tail",
        tags={"forgive", "kite", "ghost"},
    ),
    "marble_apology": Memory(
        id="marble_apology",
        medium="microcassette",
        ghost_name="Peter",
        elder_name="Mr. Ellis",
        elder_title="Mr. Ellis",
        elder_type="man",
        relation="friend",
        quarrel="fighting over a blue glass marble in the schoolyard",
        apology="Mr. Ellis, I was wrong to hide your lucky marble and laugh when you cried.",
        image="The marble flashed in the dirt like a tiny moon while two boys stood apart with hurt faces.",
        keepsake="blue marble",
        tags={"forgive", "marble", "ghost"},
    ),
    "lantern_apology": Memory(
        id="lantern_apology",
        medium="cassette",
        ghost_name="May",
        elder_name="Aunt Flora",
        elder_title="Aunt Flora",
        elder_type="aunt",
        relation="cousin",
        quarrel="quarreling over whose turn it was to carry the paper lantern at the harvest walk",
        apology="Flora, I should never have grabbed the lantern and marched away alone.",
        image="A gold paper lantern bobbed between them, bright as a tiny moon, then dipped when one pair of hands pulled too hard.",
        keepsake="paper lantern tassel",
        tags={"forgive", "lantern", "ghost"},
    ),
}

FIXES = {
    "unplug_and_press": Fix(
        id="unplug_and_press",
        sense=3,
        handles={"sticky_eject"},
        text="Maybe we should unplug it first and press the eject button gently, not force it.",
        qa_text="They unplugged the machine first and pressed the eject button gently.",
        tags={"eject", "safe_fix"},
    ),
    "fresh_batteries": Fix(
        id="fresh_batteries",
        sense=3,
        handles={"battery_sleep"},
        text="Maybe the machine is too tired to open. Let us put in fresh batteries before we try the eject button.",
        qa_text="They put in fresh batteries and then used the eject button.",
        tags={"battery", "safe_fix"},
    ),
    "pencil_rewind": Fix(
        id="pencil_rewind",
        sense=2,
        handles={"crooked_tape"},
        text="Maybe the tape is sitting crooked. Let us ease it straight with a pencil and then try the eject button.",
        qa_text="They straightened the crooked tape with a pencil and then used the eject button.",
        tags={"tape", "safe_fix"},
    ),
    "yank_hard": Fix(
        id="yank_hard",
        sense=1,
        handles=set(),
        text="Let us yank it hard and hope for the best.",
        qa_text="They pulled too hard.",
        tags={"unsafe"},
    ),
}


GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Ava", "Elsie", "Wren", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Milo", "Evan", "Toby", "Jude", "Ben"]
TRAITS = ["curious", "gentle", "thoughtful", "brave", "quiet"]


@dataclass
class StoryParams:
    place: str
    device: str
    memory: str
    fix: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spirit or haunting in it. In gentle ghost stories, the ghost is often sad or lonely instead of mean."
        )
    ],
    "cassette": [
        (
            "What is a cassette?",
            "A cassette is a small plastic case with tape inside that can hold sound. People used them before phones and music apps."
        )
    ],
    "eject": [
        (
            "What does eject mean on a machine?",
            "Eject means the machine opens and lets the thing inside come out. On an old tape machine, pressing eject opens the little door."
        )
    ],
    "battery": [
        (
            "Why do some machines need batteries?",
            "Batteries store energy for small machines. If the batteries are tired or empty, the machine may not work properly."
        )
    ],
    "forgive": [
        (
            "What does it mean to forgive someone?",
            "To forgive someone means you choose not to hold on to anger after they are sorry. It does not make the hurt vanish, but it helps hearts mend."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story shows something that happened earlier. It helps readers understand why a person feels the way they do now."
        )
    ],
}

KNOWLEDGE_ORDER = ["ghost", "cassette", "eject", "battery", "forgive", "flashback"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    memory = world.facts["memory"]
    device = world.facts["device"]
    place = world.facts["place"]
    return [
        (
            f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "brain" '
            f'and "eject" and takes place in {place.label}.'
        ),
        (
            f"Tell a story where {child.id} meets a lonely ghost who needs help with {device.phrase}, "
            f"and the solution leads to a flashback and an apology."
        ),
        (
            f"Write a child-facing ghost story about problem solving and reconciliation, where "
            f"{memory.ghost_name}'s lost message is finally heard."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    ghost = world.facts["ghost"]
    place = world.facts["place"]
    device = world.facts["device"]
    memory = world.facts["memory"]
    fix = world.facts["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {elder.title}, and the ghost named {ghost.id}. They meet in {place.label} beside an old {device.label}."
        ),
        (
            f"What problem did the ghost have?",
            f"The ghost had an apology trapped inside the old machine, but it would not eject the {memory.medium}. That meant the message could not be played for {elder.title}."
        ),
        (
            f"How did {child.id} help solve the problem?",
            f"{child.id} used {child.pronoun('possessive')} brain to stop and think instead of grabbing. Then {elder.title} and {child.id} {fix.qa_text}"
        ),
    ]
    if world.facts.get("flashback_seen"):
        qa.append(
            (
                "What happened in the flashback?",
                f"The flashback showed {ghost.id} and {memory.elder_name} long ago, {memory.quarrel}. Seeing that older moment explained why the apology had mattered for so many years."
            )
        )
    if world.facts.get("reconciled"):
        qa.append(
            (
                f"How did the ghost and {elder.title} make peace?",
                f"When the apology played, {elder.title} said {elder.pronoun()} had forgiven {ghost.id} and was sorry too. That kindness untied the ghost's sadness, so the room stopped feeling cold."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and warmly. The ghost faded peacefully after being forgiven, and {child.id} walked downstairs with {elder.title} while the house felt calm again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "flashback", "forgive", "eject"}
    device = world.facts["device"]
    fix = world.facts["fix"]
    if "cassette" in device.tags:
        tags.add("cassette")
    if "battery" in fix.tags:
        tags.add("battery")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for (name, *_) in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        device="cassette_player",
        memory="kite_apology",
        fix="unplug_and_press",
        child_name="Lina",
        child_gender="girl",
        trait="curious",
    ),
    StoryParams(
        place="music_room",
        device="answering_machine",
        memory="marble_apology",
        fix="fresh_batteries",
        child_name="Owen",
        child_gender="boy",
        trait="thoughtful",
    ),
    StoryParams(
        place="landing",
        device="tape_deck",
        memory="lantern_apology",
        fix="pencil_rewind",
        child_name="Nora",
        child_gender="girl",
        trait="brave",
    ),
]


ASP_RULES = r"""
% Medium compatibility.
compatible(D, M) :- device(D), memory(M), device_medium(D, X), memory_medium(M, X).

% Safe fix and matching jam.
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
works(D, F) :- device(D), fix(F), jam(D, J), handles(F, J).

% Valid story choices.
valid(P, D, M, F) :- place(P), compatible(D, M), sensible(F), works(D, F).

% Outcome twin.
outcome(reconciled) :- chosen_device(D), chosen_memory(M), chosen_fix(F),
                       compatible(D, M), works(D, F).
outcome(restless) :- chosen_device(D), chosen_memory(M), chosen_fix(F),
                     compatible(D, M), not works(D, F).
outcome(silent) :- chosen_device(D), chosen_memory(M), not compatible(D, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for device_id, device in DEVICES.items():
        lines.append(asp.fact("device", device_id))
        lines.append(asp.fact("device_medium", device_id, device.medium))
        lines.append(asp.fact("jam", device_id, device.jam))
    for memory_id, memory in MEMORIES.items():
        lines.append(asp.fact("memory", memory_id))
        lines.append(asp.fact("memory_medium", memory_id, memory.medium))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for jam in sorted(fix.handles):
            lines.append(asp.fact("handles", fix_id, jam))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_device", params.device),
            asp.fact("chosen_memory", params.memory),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
        print("MISMATCH in sensible fixes:")
        print("  clingo:", sorted(clingo_sensible))
        print("  python:", sorted(python_sensible))

    cases: list[StoryParams] = list(CURATED)
    for device_id in DEVICES:
        for memory_id in MEMORIES:
            for fix_id in FIXES:
                cases.append(
                    StoryParams(
                        place="attic",
                        device=device_id,
                        memory=memory_id,
                        fix=fix_id,
                        child_name="Lina",
                        child_gender="girl",
                        trait="curious",
                    )
                )
    bad = 0
    for params in cases:
        py = outcome_of(DEVICES[params.device], MEMORIES[params.memory], FIXES[params.fix])
        asp_value = asp_outcome(params)
        if py != asp_value:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Gentle ghost story world: a stuck apology, a safe fix, a flashback, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story choices derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.device and args.memory:
        device = DEVICES[args.device]
        memory = MEMORIES[args.memory]
        if not medium_matches(device, memory):
            raise StoryError(explain_medium(device, memory))

    if args.fix and args.device:
        fix = FIXES[args.fix]
        device = DEVICES[args.device]
        if fix.sense < SENSE_MIN or not fix_works(device, fix):
            raise StoryError(explain_fix(fix, device))
    elif args.fix:
        fix = FIXES[args.fix]
        if fix.sense < SENSE_MIN:
            device = DEVICES[args.device] if args.device else DEVICES["cassette_player"]
            raise StoryError(explain_fix(fix, device))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.device is None or combo[1] == args.device)
        and (args.memory is None or combo[2] == args.memory)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, device_id, memory_id, fix_id = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        device=device_id,
        memory=memory_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.device not in DEVICES:
        raise StoryError(f"(Unknown device: {params.device})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    place = PLACES[params.place]
    device = DEVICES[params.device]
    memory = MEMORIES[params.memory]
    fix = FIXES[params.fix]

    if not medium_matches(device, memory):
        raise StoryError(explain_medium(device, memory))
    if fix.sense < SENSE_MIN or not fix_works(device, fix):
        raise StoryError(explain_fix(fix, device))

    world = tell(
        place=place,
        device=device,
        memory=memory,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, device, memory, fix) combos:\n")
        for place_id, device_id, memory_id, fix_id in combos:
            print(f"  {place_id:10} {device_id:18} {memory_id:16} {fix_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.device} / {p.memory} at {p.place}"
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
