#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/radio_melancholic_twist_bedtime_story.py
===================================================================

A standalone storyworld for a bedtime tale with an old radio, a melancholic
sound, and a gentle twist. A child hears a radio song that seems sad in the
dark and worries that someone inside the radio is lonely. A calm grown-up
investigates, fixes the ordinary cause that made the music sound wrong, and
discovers the twist: the song is a family lullaby recording that was never sad
at all.

The world model tracks simple physical meters (static, dimness, warmth,
sleepiness) and emotional memes (worry, curiosity, relief, comfort). The prose
is driven by simulated state, not by slot-filling alone.

Run it
------
    python storyworlds/worlds/gpt-5.4/radio_melancholic_twist_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/radio_melancholic_twist_bedtime_story.py --cause low_battery --fix new_batteries
    python storyworlds/worlds/gpt-5.4/radio_melancholic_twist_bedtime_story.py --cause bent_antenna --fix wipe_speaker
    python storyworlds/worlds/gpt-5.4/radio_melancholic_twist_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/radio_melancholic_twist_bedtime_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/radio_melancholic_twist_bedtime_story.py --qa --json
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

# Make the shared result containers importable when this script is run directly:
# this file lives in storyworlds/worlds/gpt-5.4/, so go up three levels.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Bedroom:
    id: str
    room_phrase: str
    window_phrase: str
    bed_phrase: str
    night_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Broadcast:
    id: str
    source_name: str
    source_phrase: str
    singer_name: str
    opening_line: str
    memory_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    problem_phrase: str
    symptom_phrase: str
    trace_word: str
    effect_meter: str
    fix_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action_text: str
    result_text: str
    cures: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    discovery_text: str
    twist_text: str
    comfort_text: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_radio_sad(world: World) -> list[str]:
    radio = world.get("radio")
    child = world.get("child")
    out: list[str] = []
    static = radio.meters["static"]
    wobble = radio.meters["wobble"]
    muffled = radio.meters["muffled"]
    if static + wobble + muffled >= THRESHOLD:
        sig = ("radio_sad",)
        if sig not in world.fired:
            world.fired.add(sig)
            radio.memes["melancholic"] += 1
            child.memes["worry"] += 1
            child.memes["curiosity"] += 1
            out.append("__sad_sound__")
    return out


def _r_comfort_sleep(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    if child.memes["relief"] >= THRESHOLD and room.meters["warmth"] >= THRESHOLD:
        sig = ("sleep",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["sleepy"] += 1
            child.memes["peace"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="radio_sad", apply=_r_radio_sad),
    Rule(name="comfort_sleep", apply=_r_comfort_sleep),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__sad_sound__":
                child = world.get("child")
                radio = world.get("radio")
                world.say(
                    f"The little radio gave a soft, melancholic sigh of music. "
                    f"To {child.id}, it sounded as if the song itself had a lump in its throat."
                )
    return produced


BEDROOMS = {
    "window_nook": Bedroom(
        id="window_nook",
        room_phrase="a small room tucked under the roof",
        window_phrase="a round window where moonlight could reach the blanket",
        bed_phrase="a bed with a patchwork quilt",
        night_sound="rain whispering on the panes",
        tags={"bedroom", "night"},
    ),
    "lamp_room": Bedroom(
        id="lamp_room",
        room_phrase="a quiet room at the end of the hall",
        window_phrase="a square window with curtains like folded clouds",
        bed_phrase="a little bed beside a pearly lamp",
        night_sound="the wind brushing the eaves",
        tags={"bedroom", "night"},
    ),
    "attic_room": Bedroom(
        id="attic_room",
        room_phrase="a cozy attic room with sloping walls",
        window_phrase="a skylight full of stars",
        bed_phrase="a low bed with a moon-colored blanket",
        night_sound="tree branches tapping softly outside",
        tags={"bedroom", "night"},
    ),
}

BROADCASTS = {
    "lullaby": Broadcast(
        id="lullaby",
        source_name="Night Nest",
        source_phrase="a sleepy night program called Night Nest",
        singer_name="Grandma June",
        opening_line="a slow tune drifted out after the bedtime weather",
        memory_line="the voice belonged to someone the family already loved",
        ending_image="the song floated over the pillow like a warm hand smoothing the night",
        tags={"radio", "song", "bedtime"},
    ),
    "story_song": Broadcast(
        id="story_song",
        source_name="Moon Window",
        source_phrase="a late show called Moon Window",
        singer_name="Aunt May",
        opening_line="a humming story-song slipped between the crackles",
        memory_line="the voice turned out to be part of the family's own bedtime history",
        ending_image="the room seemed to rock as gently as a cradle",
        tags={"radio", "song", "bedtime"},
    ),
    "star_program": Broadcast(
        id="star_program",
        source_name="Lantern Hour",
        source_phrase="a soft program called Lantern Hour",
        singer_name="Grandpa Eli",
        opening_line="a low tune wandered through the dark like a lantern on a path",
        memory_line="the voice was not a stranger at all",
        ending_image="each note settled softly, as if it knew the way to sleep",
        tags={"radio", "song", "bedtime"},
    ),
}

CAUSES = {
    "low_battery": Cause(
        id="low_battery",
        problem_phrase="the batteries were nearly empty",
        symptom_phrase="the notes drooped and dragged",
        trace_word="wobble",
        effect_meter="wobble",
        fix_ids={"new_batteries"},
        tags={"battery", "radio"},
    ),
    "bent_antenna": Cause(
        id="bent_antenna",
        problem_phrase="the antenna had been knocked crooked",
        symptom_phrase="the song kept rubbing against static",
        trace_word="static",
        effect_meter="static",
        fix_ids={"straighten_antenna"},
        tags={"antenna", "radio"},
    ),
    "dusty_speaker": Cause(
        id="dusty_speaker",
        problem_phrase="a lace of dust lay over the speaker cloth",
        symptom_phrase="the voice came out dull and muffled",
        trace_word="muffled",
        effect_meter="muffled",
        fix_ids={"wipe_speaker"},
        tags={"speaker", "radio"},
    ),
}

FIXES = {
    "new_batteries": Fix(
        id="new_batteries",
        label="new batteries",
        action_text="opened the back, slipped in fresh batteries, and clicked the little door shut",
        result_text="the dragging tune lifted its head at once",
        cures={"low_battery"},
        tags={"battery"},
    ),
    "straighten_antenna": Fix(
        id="straighten_antenna",
        label="the antenna",
        action_text="gently lifted the thin antenna until it stood straight again",
        result_text="the scratchy edge fell away and the music could breathe",
        cures={"bent_antenna"},
        tags={"antenna"},
    ),
    "wipe_speaker": Fix(
        id="wipe_speaker",
        label="the speaker cloth",
        action_text="brushed the speaker cloth with a clean handkerchief until the dust was gone",
        result_text="the hidden voice came through clear and round",
        cures={"dusty_speaker"},
        tags={"speaker"},
    ),
}

KEEPSAKES = {
    "paper_star": Keepsake(
        id="paper_star",
        label="a folded paper star taped inside the battery door",
        discovery_text="Tucked inside was a folded paper star with a tiny note behind it.",
        twist_text='On the note was written, "For sleepy nights, with love from Grandma."',
        comfort_text="It turned the strange song into a family goodnight.",
        tags={"family", "memory"},
    ),
    "label": Keepsake(
        id="label",
        label="a faded label on the bottom of the radio",
        discovery_text="On the bottom was a faded label that someone had written on years ago.",
        twist_text='It said, "Grandpa Eli singing for every child who needs a soft landing."',
        comfort_text="The old radio had not been lonely; it had been remembering.",
        tags={"family", "memory"},
    ),
    "photo": Keepsake(
        id="photo",
        label="a tiny black-and-white photo tucked in the case",
        discovery_text="Behind the back panel was a tiny black-and-white photo, curled at the edges.",
        twist_text='The smiling singer in it was the grown-up\'s own aunt, holding the same radio.',
        comfort_text="The sad mystery changed into a warm secret passed down at bedtime.",
        tags={"family", "memory"},
    ),
}


def valid_combo(cause_id: str, fix_id: str) -> bool:
    if cause_id not in CAUSES or fix_id not in FIXES:
        return False
    return fix_id in CAUSES[cause_id].fix_ids and cause_id in FIXES[fix_id].cures


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for cause_id in sorted(CAUSES):
        for fix_id in sorted(FIXES):
            if valid_combo(cause_id, fix_id):
                combos.append((cause_id, fix_id))
    return combos


def explain_rejection(cause_id: str, fix_id: str) -> str:
    if cause_id not in CAUSES:
        return f"(No story: unknown cause '{cause_id}'.)"
    if fix_id not in FIXES:
        return f"(No story: unknown fix '{fix_id}'.)"
    cause = CAUSES[cause_id]
    fix = FIXES[fix_id]
    return (
        f"(No story: {fix.label} would not fix this radio problem. Here the issue is that "
        f"{cause.problem_phrase}, so choose one of: {', '.join(sorted(cause.fix_ids))}.)"
    )


def predict_child_worry(world: World, cause: Cause) -> dict:
    sim = world.copy()
    radio = sim.get("radio")
    radio.meters[cause.effect_meter] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "worried": child.memes["worry"] >= THRESHOLD,
        "melancholic": radio.memes["melancholic"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, room_cfg: Bedroom, toy: Entity) -> None:
    room = world.get("room")
    room.meters["warmth"] += 1
    child.memes["comfort"] += 1
    world.say(
        f"In {room_cfg.room_phrase}, there was {room_cfg.bed_phrase} and {room_cfg.window_phrase}. "
        f"{child.id} was tucked in with {toy.label}, listening to {room_cfg.night_sound}."
    )


def mention_radio(world: World, child: Entity, grownup: Entity, broadcast: Broadcast) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Down the hall, {grownup.label_word} had left the old radio on low. "
        f"From {broadcast.source_phrase}, {broadcast.opening_line}."
    )


def hear_wrong(world: World, child: Entity, cause: Cause) -> None:
    radio = world.get("radio")
    radio.meters[cause.effect_meter] += 1
    propagate(world, narrate=True)
    world.say(
        f"Because {cause.problem_phrase}, {cause.symptom_phrase}. "
        f"{child.id} pulled the blanket to {child.pronoun('possessive')} chin and whispered, "
        f'"Why does the radio sound so sad tonight?"'
    )


def wonder(world: World, child: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"Is someone inside it lonely?" {child.id} asked. '
        f"The thought made the room feel a little larger and the dark corners a little farther away."
    )


def comfort_first(world: World, grownup: Entity, child: Entity) -> None:
    grownup.memes["care"] += 1
    child.memes["comfort"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} came in, sat on the edge of the bed, and laid a warm hand on the quilt. "
        f'"Let us see what the radio is trying to tell us," {grownup.pronoun()} said softly.'
    )


def inspect(world: World, grownup: Entity, cause: Cause) -> None:
    world.say(
        f"In the hallway, {grownup.pronoun()} listened carefully. "
        f"It was not real sadness at all; it was the sound of {cause.trace_word} in the old set."
    )


def repair(world: World, grownup: Entity, fix: Fix) -> None:
    radio = world.get("radio")
    for meter in ("wobble", "static", "muffled"):
        radio.meters[meter] = 0.0
    world.say(
        f"{grownup.pronoun().capitalize()} {fix.action_text}. "
        f"Then {fix.result_text}."
    )


def reveal_twist(world: World, grownup: Entity, child: Entity, broadcast: Broadcast, keepsake: Keepsake) -> None:
    radio = world.get("radio")
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    child.memes["worry"] = 0.0
    child.memes["comfort"] += 1
    radio.memes["melancholic"] = 0.0
    radio.memes["familiar"] += 1
    world.get("room").meters["warmth"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But that was only the first surprise. {keepsake.discovery_text} {keepsake.twist_text}"
    )
    world.say(
        f'"This is {broadcast.singer_name}," {grownup.label_word} said with a smile. '
        f'"{broadcast.memory_line}. It was saved here to help children fall asleep."'
    )
    world.say(
        f"{child.id} listened again. Now the tune did not sound lonely at all. {keepsake.comfort_text}"
    )


def sleep_end(world: World, child: Entity, toy: Entity, broadcast: Broadcast) -> None:
    child.memes["peace"] += 1
    child.meters["sleepy"] += 1
    world.say(
        f"Soon {broadcast.ending_image}. {child.id} tucked {toy.label} under one arm, "
        f"gave a soft yawn, and let sleep find {child.pronoun('object')}."
    )


def tell(
    room_cfg: Bedroom,
    broadcast: Broadcast,
    cause: Cause,
    fix: Fix,
    keepsake: Keepsake,
    child_name: str = "Mila",
    child_type: str = "girl",
    grownup_type: str = "mother",
    toy_label: str = "a small rabbit doll",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        attrs={"name": child_name},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="grownup",
    ))
    radio = world.add(Entity(
        id="radio",
        type="radio",
        label="the radio",
        phrase="an old wooden radio",
        tags={"radio"},
    ))
    room = world.add(Entity(
        id="room",
        type="bedroom",
        label="the room",
        tags=set(room_cfg.tags),
    ))
    toy = world.add(Entity(
        id="toy",
        type="toy",
        label=toy_label,
    ))

    introduce(world, child, room_cfg, toy)
    mention_radio(world, child, grownup, broadcast)

    world.para()
    hear_wrong(world, child, cause)
    wonder(world, child)
    comfort_first(world, grownup, child)

    world.para()
    inspect(world, grownup, cause)
    repair(world, grownup, fix)
    reveal_twist(world, grownup, child, broadcast, keepsake)

    world.para()
    sleep_end(world, child, toy, broadcast)

    world.facts.update(
        child=child,
        grownup=grownup,
        radio=radio,
        room_cfg=room_cfg,
        broadcast=broadcast,
        cause=cause,
        fix=fix,
        keepsake=keepsake,
        toy=toy,
        melancholic_before=True,
        soothed=child.memes["relief"] >= THRESHOLD,
        sleepy=child.meters["sleepy"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    room: str
    broadcast: str
    cause: str
    fix: str
    keepsake: str
    child_name: str
    child_gender: str
    grownup: str
    toy_label: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mila", "Luna", "Nora", "Ivy", "Rose", "Ella", "Mina", "Ada"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Noah", "Eli", "Theo", "Milo", "Jude"]
TOYS = [
    "a small rabbit doll",
    "a stuffed bear with one shiny ear",
    "a cloth fox",
    "a sleepy lamb toy",
]

CURATED = [
    StoryParams(
        room="window_nook",
        broadcast="lullaby",
        cause="low_battery",
        fix="new_batteries",
        keepsake="paper_star",
        child_name="Mila",
        child_gender="girl",
        grownup="mother",
        toy_label="a small rabbit doll",
    ),
    StoryParams(
        room="lamp_room",
        broadcast="story_song",
        cause="bent_antenna",
        fix="straighten_antenna",
        keepsake="photo",
        child_name="Owen",
        child_gender="boy",
        grownup="father",
        toy_label="a stuffed bear with one shiny ear",
    ),
    StoryParams(
        room="attic_room",
        broadcast="star_program",
        cause="dusty_speaker",
        fix="wipe_speaker",
        keepsake="label",
        child_name="Nora",
        child_gender="girl",
        grownup="mother",
        toy_label="a sleepy lamb toy",
    ),
]


KNOWLEDGE = {
    "radio": [
        (
            "What is a radio?",
            "A radio is a machine that can play music, voices, and shows through a speaker. It turns invisible signals into sounds you can hear."
        )
    ],
    "melancholic": [
        (
            "What does melancholic mean?",
            "Melancholic means quietly sad or wistful. It is the kind of feeling a soft, droopy song can have."
        )
    ],
    "battery": [
        (
            "Why does a machine sound strange when its batteries are low?",
            "When batteries are almost empty, a machine may not get enough power to work properly. That can make its sound weak, slow, or wobbly."
        )
    ],
    "antenna": [
        (
            "What does an antenna do on a radio?",
            "An antenna helps a radio catch signals from far away. If it is bent or in the wrong place, the sound can turn scratchy."
        )
    ],
    "speaker": [
        (
            "What does a speaker do?",
            "A speaker is the part that pushes sound into the air so your ears can hear it. If it is dusty or covered, the sound can come out muffled."
        )
    ],
    "family": [
        (
            "Why can an old song make people think of family?",
            "Songs can hold memories, just like photos and letters. When a family keeps one for a long time, hearing it again can feel like meeting an old hello."
        )
    ],
    "bedtime": [
        (
            "Why do lullabies help at bedtime?",
            "Lullabies are soft and steady, so they help your body slow down and relax. Gentle sounds can make it easier to feel safe and sleepy."
        )
    ],
}
KNOWLEDGE_ORDER = ["radio", "melancholic", "battery", "antenna", "speaker", "family", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    cause = f["cause"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "radio" and "melancholic" and ends with a gentle twist.',
        f"Tell a soft night story where {child.label} hears a radio song that sounds melancholic because {cause.problem_phrase}, and {grownup.label_word} helps explain it.",
        "Write a cozy story in which something that first feels lonely turns out to be loving, familiar, and safe."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    cause = f["cause"]
    fix = f["fix"]
    broadcast = f["broadcast"]
    keepsake = f["keepsake"]
    toy = f["toy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, who was trying to fall asleep, and {child.pronoun('possessive')} {grownup.label_word}, who came to help when the radio sounded strange."
        ),
        (
            "Why did the radio sound melancholic at first?",
            f"It sounded melancholic because {cause.problem_phrase}, so {cause.symptom_phrase}. That made the music feel sad even though the song itself was not really sad."
        ),
        (
            f"What did {child.label} worry about?",
            f"{child.label} worried that someone inside the radio might be lonely. The odd sound made the dark room feel bigger, so the worry felt real for a moment."
        ),
        (
            f"How did {child.label}'s {grownup.label_word} help?",
            f"{grownup.label_word.capitalize()} stayed calm, listened closely, and {fix.action_text}. {fix.result_text}, which showed that the problem was with the old radio and not with a lonely singer."
        ),
        (
            "What was the twist at the end?",
            f"The twist was that the voice belonged to {broadcast.singer_name}, and the song was a family keepsake, not a sad stranger's song. {keepsake.comfort_text}"
        ),
        (
            "How did the story end?",
            f"It ended with the room feeling warm again while the radio played gently. {child.label} held {toy.label} and drifted to sleep."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"radio", "melancholic", "bedtime"} | set(f["cause"].tags) | set(f["keepsake"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
cause_fixed(C, F) :- cause(C), fix(F), cures(F, C).
valid(C, F) :- cause_fixed(C, F).

broken(M) :- chosen_cause(C), effect_meter(C, M).
radio_melancholic :- broken(_).
soothed :- chosen_fix(F), chosen_cause(C), cures(F, C).

outcome(comforted) :- radio_melancholic, soothed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("effect_meter", cid, cause.effect_meter))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for cured in sorted(fix.cures):
            lines.append(asp.fact("cures", fid, cured))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    for params in CURATED:
        expected = "comforted"
        got = asp_outcome(params)
        if got != expected:
            rc = 1
            print(f"MISMATCH in outcome for {params.cause}/{params.fix}: asp={got} python={expected}")

    # Smoke test normal generation and rendering.
    try:
        sample = generate(CURATED[0])
        if not sample.story or "radio" not in sample.story.lower() or "melancholic" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story text missing expected content.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a melancholic radio song at bedtime, and a family twist makes the night gentle again."
    )
    ap.add_argument("--room", choices=BEDROOMS)
    ap.add_argument("--broadcast", choices=BROADCASTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible cause/fix pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.fix and not valid_combo(args.cause, args.fix):
        raise StoryError(explain_rejection(args.cause, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.cause is None or combo[0] == args.cause)
        and (args.fix is None or combo[1] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cause_id, fix_id = rng.choice(sorted(combos))
    room_id = args.room or rng.choice(sorted(BEDROOMS))
    broadcast_id = args.broadcast or rng.choice(sorted(BROADCASTS))
    keepsake_id = args.keepsake or rng.choice(sorted(KEEPSAKES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    grownup = args.grownup or rng.choice(["mother", "father"])
    toy_label = rng.choice(TOYS)
    return StoryParams(
        room=room_id,
        broadcast=broadcast_id,
        cause=cause_id,
        fix=fix_id,
        keepsake=keepsake_id,
        child_name=child_name,
        child_gender=child_gender,
        grownup=grownup,
        toy_label=toy_label,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in BEDROOMS:
        raise StoryError(f"(Invalid room '{params.room}'.)")
    if params.broadcast not in BROADCASTS:
        raise StoryError(f"(Invalid broadcast '{params.broadcast}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause '{params.cause}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix '{params.fix}'.)")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Invalid keepsake '{params.keepsake}'.)")
    if not valid_combo(params.cause, params.fix):
        raise StoryError(explain_rejection(params.cause, params.fix))

    world = tell(
        room_cfg=BEDROOMS[params.room],
        broadcast=BROADCASTS[params.broadcast],
        cause=CAUSES[params.cause],
        fix=FIXES[params.fix],
        keepsake=KEEPSAKES[params.keepsake],
        child_name=params.child_name,
        child_type=params.child_gender,
        grownup_type=params.grownup,
        toy_label=params.toy_label,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cause, fix) pairs:\n")
        for cause_id, fix_id in combos:
            print(f"  {cause_id:14} {fix_id}")
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
            header = f"### {p.child_name}: {p.cause} fixed with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
