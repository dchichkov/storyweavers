#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pup_school_library_dialogue_rhyming_story.py
=======================================================================

A small standalone storyworld for a child-facing rhyming story set in a school
library. A reading pup joins a child during library time. Something in the room
startles or tempts the pup into making noise, and the child uses the right quiet
helper to settle the moment.

The world model prefers only plausible problem/fix pairs:
- a sudden clatter needs a reassuring whisper cue
- a fluttering thing that invites chasing needs a settling mat
- a busy little fidget moment needs a page-holding job

Every generated sample is a complete story with dialogue, a turn driven by the
simulated state, and an ending image that proves the library became calm again.

Run it
------
    python storyworlds/worlds/gpt-5.4/pup_school_library_dialogue_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/pup_school_library_dialogue_rhyming_story.py --trigger cart_squeak --helper whisper_cue
    python storyworlds/worlds/gpt-5.4/pup_school_library_dialogue_rhyming_story.py --trigger flutter_bookmark --helper whisper_cue
    python storyworlds/worlds/gpt-5.4/pup_school_library_dialogue_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/pup_school_library_dialogue_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        custom = self.attrs.get("pronouns")
        if isinstance(custom, dict) and case in custom:
            return custom[case]
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class BookTheme:
    id: str
    title: str
    cover: str
    rhyme_line: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    label: str
    cause_text: str
    bark_text: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    supports: set[str] = field(default_factory=set)
    use_text: str = ""
    cue_line: str = ""
    settle_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    book: str
    trigger: str
    helper: str
    child_name: str
    child_gender: str
    pup_name: str
    pup_style: str
    librarian_name: str
    delay: int = 0
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


def _r_noise_worry(world: World) -> list[str]:
    pup = world.get("pup")
    child = world.get("child")
    room = world.get("library")
    out: list[str] = []
    if pup.meters["noise"] >= THRESHOLD and ("noise_worry",) not in world.fired:
        world.fired.add(("noise_worry",))
        room.meters["quiet"] -= 1
        child.memes["worry"] += 1
        out.append("__noise__")
    return out


def _r_librarian_notice(world: World) -> list[str]:
    pup = world.get("pup")
    librarian = world.get("librarian")
    out: list[str] = []
    if pup.meters["noise"] >= 2 * THRESHOLD and ("noticed",) not in world.fired:
        world.fired.add(("noticed",))
        librarian.memes["alert"] += 1
        out.append("__noticed__")
    return out


def _r_calm_restores_quiet(world: World) -> list[str]:
    pup = world.get("pup")
    room = world.get("library")
    out: list[str] = []
    if pup.memes["calm"] >= THRESHOLD and ("quiet_back",) not in world.fired:
        world.fired.add(("quiet_back",))
        room.meters["quiet"] = max(room.meters["quiet"], 1.0)
        out.append("__quiet_back__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_worry", tag="social", apply=_r_noise_worry),
    Rule(name="noticed", tag="social", apply=_r_librarian_notice),
    Rule(name="quiet_back", tag="social", apply=_r_calm_restores_quiet),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


BOOKS = {
    "moon": BookTheme(
        id="moon",
        title="Moon Tune",
        cover="a silver moon on a deep blue cover",
        rhyme_line='"Moon so bright, drift through night."',
        image="the moon sailing over sleepy roofs",
        tags={"book", "moon", "rhyme"},
    ),
    "frog": BookTheme(
        id="frog",
        title="Frog Song",
        cover="a green frog with a scarf and a song sheet",
        rhyme_line='"Frog in the bog, hum on the log."',
        image="a little frog singing by the reeds",
        tags={"book", "frog", "rhyme"},
    ),
    "kite": BookTheme(
        id="kite",
        title="Kite Night",
        cover="a red kite floating over a town at dusk",
        rhyme_line='"Kite in the light, float just right."',
        image="a kite gliding through a purple sky",
        tags={"book", "kite", "rhyme"},
    ),
}

TRIGGERS = {
    "cart_squeak": Trigger(
        id="cart_squeak",
        label="a squeaky cart",
        cause_text="a metal book cart gave a long little squeak by the end shelf",
        bark_text="The sound made the pup pop up with a sharp yip-yip",
        need="reassure",
        tags={"library", "quiet", "cart"},
    ),
    "tile_clack": Trigger(
        id="tile_clack",
        label="a clacking tile box",
        cause_text="a box of letter tiles tipped and clacked against the floor",
        bark_text="The sudden clack made the pup answer with a surprised bark",
        need="reassure",
        tags={"library", "quiet", "letters"},
    ),
    "flutter_bookmark": Trigger(
        id="flutter_bookmark",
        label="a fluttering bookmark",
        cause_text="a ribbon bookmark slipped out and fluttered like a tiny bird",
        bark_text="The flutter made the pup bounce up, ready to chase and yap",
        need="anchor",
        tags={"library", "bookmark", "quiet"},
    ),
    "rolling_pompom": Trigger(
        id="rolling_pompom",
        label="a rolling craft pompom",
        cause_text="a soft pompom from the story basket rolled under the table",
        bark_text="The rolling fluff made the pup scoot forward with a playful woof",
        need="job",
        tags={"library", "craft", "quiet"},
    ),
}

HELPERS = {
    "whisper_cue": Helper(
        id="whisper_cue",
        label="a whisper cue",
        supports={"reassure"},
        use_text='leaned close and used the library whisper cue',
        cue_line='"Hush, little pup, soft as a cup. Listen, don\'t leap. Library keep."',
        settle_text="The gentle rhyme turned the sharp surprise into a slow calm sigh",
        tags={"quiet", "whisper"},
    ),
    "blue_mat": Helper(
        id="blue_mat",
        label="a blue reading mat",
        supports={"anchor"},
        use_text="slid out the blue reading mat and tapped its soft square",
        cue_line='"Mat for your paws, pause for the cause. Sit by me near, nothing to fear."',
        settle_text="With paws on the mat, the urge to pounce melted and the pup stayed put",
        tags={"library", "mat", "quiet"},
    ),
    "page_job": Helper(
        id="page_job",
        label="a page-turn job",
        supports={"job"},
        use_text="gave the pup a cloth page tab to hold between his paws",
        cue_line='"Hold this small tag, don\'t chase or zigzag. Helper pups stay, gentle all day."',
        settle_text="Having a small job to do turned the wiggle into focus and pride",
        tags={"library", "helping", "quiet"},
    ),
}

CHILD_NAMES = {
    "girl": ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Sadie"],
    "boy": ["Ben", "Max", "Noah", "Sam", "Leo", "Eli", "Theo", "Jack"],
}
PUP_NAMES = ["Pip", "Moss", "Tumble", "Biscuit", "Noodle", "Pebble"]
PUP_STYLES = ["golden", "spotty", "floppy-eared", "curly", "small brown", "velvet-eared"]
LIBRARIAN_NAMES = ["Ms. Reed", "Mr. Bell", "Ms. Page", "Mr. Lane"]


def helper_fits(trigger: Trigger, helper: Helper) -> bool:
    return trigger.need in helper.supports


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for book_id in BOOKS:
        for trigger_id, trigger in TRIGGERS.items():
            for helper_id, helper in HELPERS.items():
                if helper_fits(trigger, helper):
                    combos.append((book_id, trigger_id, helper_id))
    return combos


def explain_rejection(trigger: Trigger, helper: Helper) -> str:
    need_to_reason = {
        "reassure": "a sudden noisy scare needs a soft reassuring cue",
        "anchor": "a fluttery chasing moment needs a place to settle still",
        "job": "a playful fidget moment needs a tiny helper job",
    }
    reason = need_to_reason.get(trigger.need, "this trigger needs a different kind of help")
    return (
        f"(No story: {trigger.label} and {helper.label} do not fit. In this world, "
        f"{reason}, so choose a helper that supports '{trigger.need}'.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "child_settles" if params.delay == 0 else "librarian_helps"


def predict_noise(world: World, trigger: Trigger) -> dict:
    sim = world.copy()
    pup = sim.get("pup")
    pup.meters["noise"] += 1
    pup.memes["startle"] += 1
    if trigger.need == "anchor":
        pup.memes["chase"] += 1
    if trigger.need == "job":
        pup.memes["fidget"] += 1
    propagate(sim, narrate=False)
    return {
        "quiet_drop": sim.get("library").meters["quiet"],
        "worry": sim.get("child").memes["worry"],
    }


def introduce(world: World, child: Entity, pup: Entity, librarian: Entity, book: BookTheme) -> None:
    world.say(
        f"In the school library, still as a sigh, {child.id} came in with {pup.id} the pup padding by."
    )
    world.say(
        f"{pup.id} was a {pup.attrs.get('style', 'small')} reading pup with bright listening eyes, "
        f"and {librarian.id} smiled under the lamps and the skies painted on the wall up high."
    )
    world.say(
        f'"Pick your rhyme book and settle in deep," said {librarian.id}. "{book.title} is a treasure to keep."'
    )


def choose_nook(world: World, child: Entity, pup: Entity, book: BookTheme) -> None:
    child.memes["joy"] += 1
    pup.memes["trust"] += 1
    world.say(
        f"{child.id} chose a nook by the low book rack and opened {book.title}, with {book.cover} on the front and back."
    )
    world.say(
        f'"I will read, and you can stay near,' whispered {child.id}. '
        f'"Soft paws, soft ears, and a soft little cheer."'
    )


def foreshadow(world: World, child: Entity, trigger: Trigger) -> None:
    pred = predict_noise(world, trigger)
    world.facts["predicted_quiet_drop"] = pred["quiet_drop"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'For a minute the room felt neat and right, with pages to turn and a warm gold light.'
    )
    if pred["worry"] >= THRESHOLD:
        world.say(
            f'{child.id} remembered the library rule in a hush-hush way: "Quiet words help stories stay."'
        )


def trigger_moment(world: World, pup: Entity, trigger: Trigger) -> None:
    world.say(f"Then {trigger.cause_text}.")
    pup.meters["noise"] += 1
    pup.memes["startle"] += 1
    if trigger.need == "anchor":
        pup.memes["chase"] += 1
    if trigger.need == "job":
        pup.memes["fidget"] += 1
    propagate(world, narrate=False)
    world.say(f"{trigger.bark_text}, and the library hush gave one small skip.")


def second_bark(world: World, pup: Entity, librarian: Entity) -> None:
    pup.meters["noise"] += 1
    pup.memes["embarrassed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Oh, {pup.id}," said {librarian.id} in a voice so mild, "let us help you settle, sweet library child."'
    )


def use_helper(world: World, child: Entity, pup: Entity, helper: Helper) -> None:
    world.say(f"{child.id} {helper.use_text}.")
    world.say(f'{child.id} said, {helper.cue_line}')
    pup.memes["calm"] += 1
    pup.meters["noise"] = 0.0
    pup.memes["startle"] = 0.0
    pup.memes["chase"] = 0.0
    pup.memes["fidget"] = 0.0
    pup.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(f"{helper.settle_text}.")
    if pup.memes["embarrassed"] >= THRESHOLD:
        world.say(f"{pup.id} tucked close to {child.id}'s shoe, glad the room felt kind and new.")


def read_after(world: World, child: Entity, pup: Entity, librarian: Entity, book: BookTheme, outcome: str) -> None:
    child.memes["focus"] += 1
    pup.memes["focus"] += 1
    world.say(
        f'When the hush came back, {child.id} read in a voice as light as a croon: {book.rhyme_line}'
    )
    if outcome == "child_settles":
        world.say(
            f'"Good quiet thinking," said {librarian.id}. "You helped your pup, and now the rhyme can sing."'
        )
    else:
        world.say(
            f'"Good helping, both of you," said {librarian.id}. "A library can bend and still be true."'
        )
    world.say(
        f"{pup.id} laid his chin by the page and watched {book.image}, while the words moved slow and the room grew bright with quiet delight."
    )


def closing_image(world: World, child: Entity, pup: Entity) -> None:
    world.say(
        f"At the end, {child.id} checked out the book, and {pup.id} trotted out slow, "
        f"soft as a rhyme in a neat little row."
    )
    world.say(
        f'"Tomorrow again?" asked {child.id}. {pup.id} gave one tiny tail-thump answer and no bark at all.'
    )


def tell(params: StoryParams) -> World:
    book = BOOKS[params.book]
    trigger = TRIGGERS[params.trigger]
    helper = HELPERS[params.helper]
    if not helper_fits(trigger, helper):
        raise StoryError(explain_rejection(trigger, helper))
    if params.delay not in (0, 1):
        raise StoryError("(No story: delay must be 0 or 1 in this small library world.)")

    world = World()
    child_pronouns = (
        {"subject": "she", "object": "her", "possessive": "her"}
        if params.child_gender == "girl"
        else {"subject": "he", "object": "him", "possessive": "his"}
    )
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=params.child_gender,
            label=params.child_name,
            role="reader",
            attrs={"pronouns": child_pronouns},
        )
    )
    pup = world.add(
        Entity(
            id="pup",
            kind="character",
            type="pup",
            label=params.pup_name,
            role="pup",
            attrs={
                "pronouns": {"subject": "he", "object": "him", "possessive": "his"},
                "style": params.pup_style,
            },
        )
    )
    librarian = world.add(
        Entity(
            id="librarian",
            kind="character",
            type="librarian",
            label=params.librarian_name,
            role="librarian",
            attrs={"pronouns": {"subject": "she", "object": "her", "possessive": "her"}}
            if params.librarian_name.startswith("Ms.")
            else {"pronouns": {"subject": "he", "object": "him", "possessive": "his"}},
        )
    )
    library = world.add(
        Entity(
            id="library",
            kind="thing",
            type="room",
            label="the school library",
            role="setting",
        )
    )
    library.meters["quiet"] = 1.0

    introduce(world, child, pup, librarian, book)
    choose_nook(world, child, pup, book)
    world.para()
    foreshadow(world, child, trigger)
    trigger_moment(world, pup, trigger)

    if params.delay == 1:
        second_bark(world, pup, librarian)
    world.para()
    use_helper(world, child, pup, helper)
    read_after(world, child, pup, librarian, book, outcome_of(params))
    closing_image(world, child, pup)

    world.facts.update(
        child=child,
        pup=pup,
        librarian=librarian,
        library=library,
        book=book,
        trigger=trigger,
        helper=helper,
        outcome=outcome_of(params),
        delay=params.delay,
        barked=True,
        quiet_restored=library.meters["quiet"] >= THRESHOLD and pup.meters["noise"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    pup = world.facts["pup"]
    book = world.facts["book"]
    trigger = world.facts["trigger"]
    helper = world.facts["helper"]
    outcome = world.facts["outcome"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old set in a school library that includes the word "pup" and uses dialogue.',
        f"Tell a gentle story in rhyme where {child.label} reads {book.title} with {pup.label} the pup, but {trigger.label} breaks the hush and {helper.label} helps restore calm.",
        f"Write a dialogue-rich school library story with a reading pup, a small noise problem, and a happy ending where the outcome is {outcome.replace('_', ' ')}.",
    ]


KNOWLEDGE = {
    "library": [
        (
            "Why do people use quiet voices in a library?",
            "People use quiet voices in a library so everyone can read, think, and listen without being distracted. Quiet helps many stories happen at once."
        )
    ],
    "whisper": [
        (
            "What is a whisper?",
            "A whisper is a very soft voice. It lets you speak to someone nearby without filling the whole room with sound."
        )
    ],
    "bookmark": [
        (
            "What is a bookmark for?",
            "A bookmark helps you save your place in a book. It keeps you from losing the page you want to read next."
        )
    ],
    "cart": [
        (
            "What is a library cart used for?",
            "A library cart helps move books from one shelf or room to another. Librarians use it to carry many books at once."
        )
    ],
    "letters": [
        (
            "What are letter tiles?",
            "Letter tiles are little pieces with letters on them. Children can use them to build words and practice reading."
        )
    ],
    "mat": [
        (
            "Why can a reading mat help someone stay still?",
            "A reading mat gives a clear little place to sit or rest. Having a spot can make it easier to keep your body calm."
        )
    ],
    "helping": [
        (
            "Why does a small job sometimes help a busy body calm down?",
            "A small job gives hands or paws one simple thing to do. That can turn restless energy into steady focus."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching ending sounds, like night and light. Rhymes can make a story feel musical and easy to remember."
        )
    ],
}
KNOWLEDGE_ORDER = ["library", "whisper", "bookmark", "cart", "letters", "mat", "helping", "rhyme"]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    pup = world.facts["pup"]
    librarian = world.facts["librarian"]
    book = world.facts["book"]
    trigger = world.facts["trigger"]
    helper = world.facts["helper"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {pup.label} the pup, and {librarian.label} in the school library. They begin with a quiet reading plan together."
        ),
        (
            f"What book did {child.label} choose?",
            f"{child.label} chose {book.title}. The rhyme book set the gentle, sing-song mood of the story."
        ),
        (
            f"What problem happened in the library?",
            f"{trigger.label.capitalize()} broke the hush, and {pup.label} barked because of it. That sudden noise made the reading corner feel less calm."
        ),
        (
            f"How did {child.label} help {pup.label}?",
            f"{child.label} used {helper.label} and spoke in a calm rhyme. The helper fit the kind of trouble the pup was having, so the barking stopped and the quiet came back."
        ),
    ]
    if outcome == "child_settles":
        qa.append(
            (
                "Did the child solve the problem right away?",
                f"Yes. {child.label} used the helper after the first bark, so the moment stayed small and gentle. Because the calm came back quickly, they could return to the book almost at once."
            )
        )
    else:
        qa.append(
            (
                "Did anyone else help after the pup barked again?",
                f"Yes. After a second bark, {librarian.label} joined with a kind reminder. The grown-up help kept the moment warm instead of scary, and then {child.label}'s helper settled the pup."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {child.label} reading softly while {pup.label} rested by the book. The ending image shows that the library became peaceful again."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"library", "rhyme"}
    trigger = world.facts["trigger"]
    helper = world.facts["helper"]
    tags |= set(trigger.tags) | set(helper.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        book="moon",
        trigger="cart_squeak",
        helper="whisper_cue",
        child_name="Lily",
        child_gender="girl",
        pup_name="Pip",
        pup_style="golden",
        librarian_name="Ms. Reed",
        delay=0,
    ),
    StoryParams(
        book="frog",
        trigger="flutter_bookmark",
        helper="blue_mat",
        child_name="Ben",
        child_gender="boy",
        pup_name="Moss",
        pup_style="floppy-eared",
        librarian_name="Mr. Bell",
        delay=1,
    ),
    StoryParams(
        book="kite",
        trigger="rolling_pompom",
        helper="page_job",
        child_name="Nora",
        child_gender="girl",
        pup_name="Pebble",
        pup_style="curly",
        librarian_name="Ms. Page",
        delay=0,
    ),
    StoryParams(
        book="moon",
        trigger="tile_clack",
        helper="whisper_cue",
        child_name="Sam",
        child_gender="boy",
        pup_name="Biscuit",
        pup_style="small brown",
        librarian_name="Mr. Lane",
        delay=1,
    ),
]


ASP_RULES = r"""
valid(B, T, H) :- book(B), trigger(T), helper(H), needs(T, N), supports(H, N).

outcome(child_settles) :- delay(0).
outcome(librarian_helps) :- delay(1).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for book_id in BOOKS:
        lines.append(asp.fact("book", book_id))
    for trigger_id, trigger in TRIGGERS.items():
        lines.append(asp.fact("trigger", trigger_id))
        lines.append(asp.fact("needs", trigger_id, trigger.need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for need in sorted(helper.supports):
            lines.append(asp.fact("supports", helper_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = f"delay({params.delay})."
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    sink = io.StringIO()
    with redirect_stdout(sink):
        emit(sample, trace=True, qa=True, header="### smoke")
    if "school library" not in sink.getvalue():
        raise StoryError("Smoke test failed: emitted output looked wrong.")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(20):
        params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming school-library storyworld with a reading pup and dialogue."
    )
    ap.add_argument("--book", choices=BOOKS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--pup-name")
    ap.add_argument("--librarian-name", choices=LIBRARIAN_NAMES)
    ap.add_argument("--delay", type=int, choices=[0, 1])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trigger and args.helper:
        trigger = TRIGGERS[args.trigger]
        helper = HELPERS[args.helper]
        if not helper_fits(trigger, helper):
            raise StoryError(explain_rejection(trigger, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.book is None or combo[0] == args.book)
        and (args.trigger is None or combo[1] == args.trigger)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    book_id, trigger_id, helper_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES[child_gender])
    pup_name = args.pup_name or rng.choice(PUP_NAMES)
    pup_style = rng.choice(PUP_STYLES)
    librarian_name = args.librarian_name or rng.choice(LIBRARIAN_NAMES)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        book=book_id,
        trigger=trigger_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        pup_name=pup_name,
        pup_style=pup_style,
        librarian_name=librarian_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.book not in BOOKS:
        raise StoryError(f"(No story: unknown book '{params.book}'.)")
    if params.trigger not in TRIGGERS:
        raise StoryError(f"(No story: unknown trigger '{params.trigger}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("(No story: child_gender must be 'girl' or 'boy'.)")
    world = tell(params)
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
        print(f"{len(combos)} compatible (book, trigger, helper) combos:\n")
        for book_id, trigger_id, helper_id in combos:
            print(f"  {book_id:6} {trigger_id:16} {helper_id}")
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
                f"### {p.child_name} & {p.pup_name}: {p.trigger} with {p.helper} "
                f"({p.book}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
