#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/premise_transcription_music_room_misunderstanding_friendship_flashback.py
=====================================================================================================

A standalone story world about a small detective-style misunderstanding in a
music room. Two friends prepare a rehearsal. A paper goes missing, one child
jumps to the wrong conclusion, a clue-driven search follows, and a flashback
helps the detective-child correct the mistake and repair the friendship.

The world model keeps track of:
- physical meters: lost, found, hidden, crumpled
- emotional memes: worry, suspicion, trust, hurt, relief, friendship

The core constraint is simple and concrete:
a missing paper item must have a plausible way to disappear in a music room, and
the chosen clue must actually fit the hiding cause. The declarative ASP twin
mirrors that compatibility gate and the simple outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/premise_transcription_music_room_misunderstanding_friendship_flashback.py
    python storyworlds/worlds/gpt-5.4/premise_transcription_music_room_misunderstanding_friendship_flashback.py --all
    python storyworlds/worlds/gpt-5.4/premise_transcription_music_room_misunderstanding_friendship_flashback.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/premise_transcription_music_room_misunderstanding_friendship_flashback.py --json
    python storyworlds/worlds/gpt-5.4/premise_transcription_music_room_misunderstanding_friendship_flashback.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we need the storyworlds/
# package directory itself on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity representation.
# ---------------------------------------------------------------------------
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
    title: str = ""
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
    owner: str = ""
    location: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


# ---------------------------------------------------------------------------
# Domain configuration.
# ---------------------------------------------------------------------------
@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CauseCfg:
    id: str
    hide_spot: str
    motion: str
    found_text: str
    flashback_text: str
    room_feature: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueCfg:
    id: str
    label: str
    points_to: set[str] = field(default_factory=set)
    notice_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


# ---------------------------------------------------------------------------
# World model and narration.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
def _r_suspicion_hurts(world: World) -> list[str]:
    detective = world.get("detective")
    friend = world.get("friend")
    if detective.memes["suspicion"] < THRESHOLD:
        return []
    sig = ("hurt", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    paper = world.get("paper")
    if paper.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", paper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("detective").memes["relief"] += 1
    world.get("friend").memes["relief"] += 1
    return []


def _r_apology_repairs(world: World) -> list[str]:
    detective = world.get("detective")
    friend = world.get("friend")
    if detective.memes["apology"] < THRESHOLD:
        return []
    sig = ("repair", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    detective.memes["suspicion"] = 0.0
    friend.memes["hurt"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="suspicion_hurts", tag="social", apply=_r_suspicion_hurts),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
    Rule(name="apology_repairs", tag="social", apply=_r_apology_repairs),
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
    if narrate:
        for text in produced:
            world.say(text)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def clue_fits(cause_id: str, clue_id: str) -> bool:
    return cause_id in CLUES[clue_id].points_to


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id in ITEMS:
        for cause_id in CAUSES:
            for clue_id in CLUES:
                if clue_fits(cause_id, clue_id):
                    combos.append((item_id, cause_id, clue_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.spoken_accusation:
        return "spoken"
    return "quiet"


def explain_rejection(cause_id: str, clue_id: str) -> str:
    cause = CAUSES[cause_id]
    clue = CLUES[clue_id]
    return (
        f"(No story: the clue '{clue.label}' does not honestly point to "
        f"'{cause.hide_spot}'. Pick a clue that could help a child find the paper.)"
    )


# ---------------------------------------------------------------------------
# Simulation verbs.
# ---------------------------------------------------------------------------
def introduce(world: World, detective: Entity, friend: Entity, item: ItemCfg,
              lead_instrument: str, friend_instrument: str) -> None:
    detective.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"After school, {detective.id} and {friend.id} met in the music room for duet practice. "
        f"{detective.id} set down {detective.pronoun('possessive')} {lead_instrument}, and "
        f"{friend.id} opened {friend.pronoun('possessive')} {friend_instrument} case."
    )
    world.say(
        f"On the piano bench lay {item.phrase}, the page they needed for {item.use}. "
        f"{detective.id} liked mysteries, so {detective.pronoun()} called the day's little puzzle "
        f'"the premise of the rehearsal case."'
    )


def flashback_setup(world: World, detective: Entity, friend: Entity, item: ItemCfg) -> None:
    world.say(
        f"A quick flashback slid through {detective.id}'s mind: yesterday {friend.id} had bent over "
        f"{item.label} and said, \"I can help if any line is hard to read.\" "
        f"It was a warm memory of friendship, but in the busy room it also made {friend.id} seem close to the page."
    )


def page_goes_missing(world: World, cause: CauseCfg) -> None:
    paper = world.get("paper")
    paper.meters["lost"] += 1
    paper.meters["hidden"] += 1
    paper.location = cause.hide_spot
    world.say(
        f"Then a scrape of chairs, a puff from the old vent, and one rustly moment changed the room. "
        f"When {world.get('detective').id} looked back, the paper was gone from the bench."
    )


def suspect(world: World, detective: Entity, friend: Entity, item: ItemCfg,
            spoken_accusation: bool) -> None:
    detective.memes["worry"] += 1
    detective.memes["suspicion"] += 1
    propagate(world, narrate=False)
    if spoken_accusation:
        world.say(
            f"{detective.id}'s stomach gave a small jump. Because of that flashback, "
            f"{detective.pronoun()} made the wrong guess. "
            f'"{friend.id}, did you take the {item.label}?" {detective.pronoun()} asked.'
        )
        world.say(
            f"{friend.id} blinked and hugged {friend.pronoun('possessive')} instrument case tighter. "
            f'"No," {friend.pronoun()} said softly. "I thought we were looking at it together."'
        )
    else:
        world.say(
            f"{detective.id}'s stomach gave a small jump. Because of that flashback, "
            f"{detective.pronoun()} quietly wondered if {friend.id} had taken the {item.label}. "
            f"But {detective.pronoun()} did not say it aloud."
        )


def investigate(world: World, detective: Entity, friend: Entity, clue: ClueCfg,
                cause: CauseCfg) -> None:
    detective.memes["curiosity"] += 1
    friend.memes["steadiness"] += 1
    world.say(
        f'"A good detective checks the room before blaming anyone," {friend.id} said. '
        f"The words were gentle, not sharp, and they made {detective.id} listen."
    )
    world.say(
        f"Together they searched the music room: under the metronome, beside the drum shelf, "
        f"and around the piano legs. Then {detective.id} noticed {clue.notice_text}"
    )
    world.say(
        f"The clue did not point to a thief at all. It pointed toward {cause.room_feature}."
    )


def find_paper(world: World, cause: CauseCfg, item: ItemCfg) -> None:
    paper = world.get("paper")
    paper.meters["found"] += 1
    paper.meters["hidden"] = 0.0
    paper.meters["lost"] = 0.0
    paper.location = "in their hands"
    if "crumpled" in cause.tags:
        paper.meters["crumpled"] += 1
    propagate(world, narrate=False)
    world.say(cause.found_text.format(item=item.label))


def realize_truth(world: World, detective: Entity, friend: Entity,
                  spoken_accusation: bool) -> None:
    detective.memes["understanding"] += 1
    world.say(causes_line(world))
    if spoken_accusation:
        world.say(
            f"{detective.id}'s cheeks grew warm. The mystery was solved, and the biggest mistake had been "
            f"{detective.pronoun('possessive')} own guess."
        )
    else:
        world.say(
            f"{detective.id} felt a flutter of shame for the silent suspicion. "
            f"The mystery was solved, and the wrong idea melted away."
        )


def causes_line(world: World) -> str:
    cause = world.facts["cause_cfg"]
    return cause.flashback_text


def apologize(world: World, detective: Entity, friend: Entity,
              spoken_accusation: bool) -> None:
    detective.memes["apology"] += 1
    propagate(world, narrate=False)
    if spoken_accusation:
        world.say(
            f'"I am sorry, {friend.id}," {detective.id} said. "I should have followed the clues before I accused you."'
        )
    else:
        world.say(
            f'"I almost blamed you in my head," {detective.id} admitted. '
            f'"I am glad I looked for clues first."'
        )
    world.say(
        f'{friend.id} smiled a little. "That is what partners are for," {friend.pronoun()} said.'
    )


def ending(world: World, detective: Entity, friend: Entity, item: ItemCfg,
           lead_instrument: str, friend_instrument: str) -> None:
    detective.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"They smoothed the {item.label} flat on the piano bench and began again. "
        f"{detective.id}'s {lead_instrument} answered {friend.id}'s {friend_instrument}, "
        f"and the music room no longer felt like a crime scene."
    )
    world.say(
        f"By the end of practice, the best clue was plain: friendship sounded stronger when both friends listened carefully."
    )


# ---------------------------------------------------------------------------
# High-level screenplay.
# ---------------------------------------------------------------------------
def tell(item: ItemCfg, cause: CauseCfg, clue: ClueCfg,
         detective_name: str, detective_gender: str,
         friend_name: str, friend_gender: str,
         lead_instrument: str, friend_instrument: str,
         teacher_type: str, spoken_accusation: bool) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        label="teacher",
        role="teacher",
    ))
    paper = world.add(Entity(
        id="paper",
        kind="thing",
        type="paper",
        label=item.label,
        phrase=item.phrase,
        owner="both",
        location="piano bench",
        tags=set(item.tags),
    ))

    world.facts.update(
        detective=detective,
        friend=friend,
        teacher=teacher,
        paper=paper,
        item_cfg=item,
        cause_cfg=cause,
        clue_cfg=clue,
        lead_instrument=lead_instrument,
        friend_instrument=friend_instrument,
        spoken_accusation=spoken_accusation,
        room="music room",
    )

    introduce(world, detective, friend, item, lead_instrument, friend_instrument)
    flashback_setup(world, detective, friend, item)

    world.para()
    page_goes_missing(world, cause)
    suspect(world, detective, friend, item, spoken_accusation)

    world.para()
    investigate(world, detective, friend, clue, cause)
    find_paper(world, cause, item)
    realize_truth(world, detective, friend, spoken_accusation)

    world.para()
    apologize(world, detective, friend, spoken_accusation)
    ending(world, detective, friend, item, lead_instrument, friend_instrument)

    world.facts["outcome"] = "repaired"
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
ITEMS = {
    "transcription": ItemCfg(
        id="transcription",
        label="transcription",
        phrase="a fresh transcription of their duet",
        use="the tricky middle of their duet",
        tags={"transcription", "sheet_music"},
    ),
    "practice_notes": ItemCfg(
        id="practice_notes",
        label="practice notes",
        phrase="the page of practice notes for their duet",
        use="the quiet ending of their piece",
        tags={"sheet_music"},
    ),
    "rhythm_copy": ItemCfg(
        id="rhythm_copy",
        label="rhythm copy",
        phrase="a neat rhythm copy for their rehearsal",
        use="the clapping part before the song",
        tags={"sheet_music"},
    ),
}

CAUSES = {
    "piano_back": CauseCfg(
        id="piano_back",
        hide_spot="behind the piano",
        motion="the vent blew the page off the bench and behind the piano",
        found_text="There, caught behind the piano, was the {item}. The vent had pushed it into the narrow space.",
        flashback_text="Another flashback answered the case: yesterday the same vent had ruffled three loose pages. It had been the moving air, not a sneaky hand.",
        room_feature="the old vent beside the piano",
        tags={"vent"},
    ),
    "drum_shelf": CauseCfg(
        id="drum_shelf",
        hide_spot="under the drum shelf",
        motion="a passing elbow brushed the page onto the floor and under the drum shelf",
        found_text="Under the drum shelf lay the {item}, folded at one corner but safe. A bump had sent it skimming there.",
        flashback_text="A flashback clicked into place: before practice, a younger class had hurried past the drum shelf with swinging sleeves. The paper must have slid there in the bustle.",
        room_feature="the low drum shelf",
        tags={"bump"},
    ),
    "cello_case": CauseCfg(
        id="cello_case",
        hide_spot="stuck to the outside of the cello case",
        motion="the page clung to a rosin-smudged case and rode away from the bench",
        found_text="The {item} was stuck against the outside of the cello case, held by a dusty rosin smear. No one had hidden it at all.",
        flashback_text="Then came the true flashback: earlier, one corner of the page had brushed a dusty patch on the case when they set up. It had simply clung there and traveled with the case.",
        room_feature="the row of instrument cases",
        tags={"case", "crumpled"},
    ),
}

CLUES = {
    "flutter": ClueCfg(
        id="flutter",
        label="fluttering corner",
        points_to={"piano_back"},
        notice_text="a tiny white corner fluttering when the vent breathed out again.",
        tags={"vent"},
    ),
    "dust_line": ClueCfg(
        id="dust_line",
        label="dust line",
        points_to={"drum_shelf"},
        notice_text="a fresh dust line on the floor, as if a page had slid under something low.",
        tags={"dust"},
    ),
    "rosin_speck": ClueCfg(
        id="rosin_speck",
        label="rosin speck",
        points_to={"cello_case"},
        notice_text="golden rosin specks on the edge of the empty bench and on one waiting instrument case.",
        tags={"rosin"},
    ),
}

INSTRUMENTS = ["violin", "flute", "clarinet", "recorder", "cello"]
GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Ella", "Suri", "Ruby", "Iris"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Milo", "Eli", "Jonah", "Noah", "Finn"]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    item: str
    cause: str
    clue: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    lead_instrument: str
    friend_instrument: str
    teacher: str
    spoken_accusation: bool
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "transcription": [
        (
            "What is a transcription in music?",
            "A transcription is a written version of music. It helps players remember the notes and rhythm."
        )
    ],
    "sheet_music": [
        (
            "Why do musicians use written pages in practice?",
            "Written pages help musicians remember what to play and when to play it. They are useful when a song has tricky parts."
        )
    ],
    "vent": [
        (
            "What can a vent do to a loose paper?",
            "A vent can blow moving air across a room. If a paper is loose, the air can push it away."
        )
    ],
    "dust": [
        (
            "How can dust help someone find something?",
            "Dust can show lines, marks, or clean spots where an object moved. That makes it a good clue."
        )
    ],
    "rosin": [
        (
            "What is rosin?",
            "Rosin is a sticky, dusty material some string players use on a bow. A little bit can cling to other things nearby."
        )
    ],
    "friendship": [
        (
            "What should you do before blaming a friend?",
            "You should stop and check the facts first. A calm question and a careful search can protect a friendship."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps explain what is happening now."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to understand what really happened. A good detective does not guess too fast."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "flashback", "transcription", "sheet_music", "vent", "dust", "rosin", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    return [
        'Write a short detective-style story for a 3-to-5-year-old set in a music room that includes the words "premise" and "transcription".',
        f"Tell a gentle mystery where {detective.id} wrongly suspects {friend.id} after {item.label} goes missing, but a clue about {clue.label} solves the misunderstanding.",
        "Write a friendship story with a flashback, a small misunderstanding, and a happy ending where the children learn to look for clues before blaming each other.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    item = f["item_cfg"]
    cause = f["cause_cfg"]
    clue = f["clue_cfg"]
    spoken = f["spoken_accusation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {detective.id} and {friend.id}, in a music room. They are practicing together when an important paper goes missing."
        ),
        (
            f"What was missing?",
            f"The missing thing was the {item.label}. They needed it for {item.use}, so losing it made practice feel suddenly hard."
        ),
        (
            f"Why did {detective.id} suspect {friend.id}?",
            f"{detective.id} remembered a flashback from the day before, when {friend.id} had leaned over the page to help. That memory was true, but {detective.id} misunderstood it and treated it like proof."
        ),
        (
            f"What clue helped solve the mystery?",
            f"The clue was {clue.label}. It mattered because it pointed toward {cause.room_feature}, not toward a person."
        ),
        (
            "Where was the paper really?",
            f"It was {cause.hide_spot}. The paper had been moved by accident, so no one had stolen it at all."
        ),
    ]
    if spoken:
        qa.append(
            (
                f"How did the misunderstanding hurt the friendship?",
                f"{detective.id} asked {friend.id} if {friend.pronoun()} had taken the page, and that made the moment feel sad and tense. When friends are blamed too quickly, hurt feelings can grow even when they did nothing wrong."
            )
        )
    else:
        qa.append(
            (
                f"How did {detective.id} fix the misunderstanding?",
                f"{detective.id} admitted the silent suspicion and chose honesty instead of hiding it. That helped the friendship because the truth was spoken kindly after the real clue was found."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the friends practicing together again. The music in the room showed that trust had been repaired."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "flashback", "friendship"} | set(f["item_cfg"].tags) | set(f["cause_cfg"].tags) | set(f["clue_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        item="transcription",
        cause="piano_back",
        clue="flutter",
        detective="Nora",
        detective_gender="girl",
        friend="Theo",
        friend_gender="boy",
        lead_instrument="violin",
        friend_instrument="flute",
        teacher="mother",
        spoken_accusation=True,
    ),
    StoryParams(
        item="practice_notes",
        cause="drum_shelf",
        clue="dust_line",
        detective="Ben",
        detective_gender="boy",
        friend="Maya",
        friend_gender="girl",
        lead_instrument="clarinet",
        friend_instrument="recorder",
        teacher="father",
        spoken_accusation=False,
    ),
    StoryParams(
        item="rhythm_copy",
        cause="cello_case",
        clue="rosin_speck",
        detective="Ava",
        detective_gender="girl",
        friend="Milo",
        friend_gender="boy",
        lead_instrument="flute",
        friend_instrument="cello",
        teacher="mother",
        spoken_accusation=True,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(Cause, Clue) :- clue_points(Clue, Cause).
valid(Item, Cause, Clue) :- item(Item), cause(Cause), clue(Clue), fits(Cause, Clue).

outcome(spoken) :- spoken_accusation(true).
outcome(quiet)  :- spoken_accusation(false).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for cause_id in sorted(clue.points_to):
            lines.append(asp.fact("clue_points", clue_id, cause_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("spoken_accusation", "true" if params.spoken_accusation else "false")
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome for:", params)
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    # Smoke test: ordinary story generation must not crash.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a story successfully.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a detective-style misunderstanding in a music room."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--lead-instrument", choices=INSTRUMENTS)
    ap.add_argument("--friend-instrument", choices=INSTRUMENTS)
    ap.add_argument("--teacher", choices=["mother", "father"], help="background adult type")
    ap.add_argument("--spoken-accusation", action="store_true", help="have the detective speak the wrong guess aloud")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.clue and not clue_fits(args.cause, args.clue):
        raise StoryError(explain_rejection(args.cause, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, cause_id, clue_id = rng.choice(sorted(combos))

    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective or _pick_name(rng, detective_gender)
    friend_name = args.friend or _pick_name(rng, friend_gender, avoid=detective_name)

    lead_instrument = args.lead_instrument or rng.choice(INSTRUMENTS)
    friend_instrument_choices = [inst for inst in INSTRUMENTS if inst != lead_instrument] or list(INSTRUMENTS)
    friend_instrument = args.friend_instrument or rng.choice(friend_instrument_choices)
    teacher = args.teacher or rng.choice(["mother", "father"])
    spoken_accusation = bool(args.spoken_accusation or rng.choice([False, True]))

    return StoryParams(
        item=item_id,
        cause=cause_id,
        clue=clue_id,
        detective=detective_name,
        detective_gender=detective_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        lead_instrument=lead_instrument,
        friend_instrument=friend_instrument,
        teacher=teacher,
        spoken_accusation=spoken_accusation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause '{params.cause}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue '{params.clue}'.)")
    if not clue_fits(params.cause, params.clue):
        raise StoryError(explain_rejection(params.cause, params.clue))
    if params.lead_instrument not in INSTRUMENTS or params.friend_instrument not in INSTRUMENTS:
        raise StoryError("(Unknown instrument choice.)")
    if params.teacher not in {"mother", "father"}:
        raise StoryError("(Unknown teacher/parent choice.)")

    world = tell(
        item=ITEMS[params.item],
        cause=CAUSES[params.cause],
        clue=CLUES[params.clue],
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        lead_instrument=params.lead_instrument,
        friend_instrument=params.friend_instrument,
        teacher_type=params.teacher,
        spoken_accusation=params.spoken_accusation,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, cause, clue) combos:\n")
        for item, cause, clue in combos:
            print(f"  {item:14} {cause:12} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.detective} and {p.friend}: {p.item} / {p.cause} / {outcome_of(p)}"
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
