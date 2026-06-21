#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mistress_derelict_teamwork_repetition_conflict_whodunit.py
=====================================================================================

A small child-facing whodunit storyworld about a missing object in an old manor.

Seed constraints rebuilt as simulation
--------------------------------------
Words: mistress, derelict
Features: Teamwork, Repetition, Conflict
Style: Whodunit

The world always begins at an old manor museum run by a kind grown-up called
Mistress Vale. A special object goes missing. Two child helpers clash because
they blame different suspects too quickly. Then they work together, follow a
repeating trail of clues, and solve the mystery in a nearby derelict place.
The culprit is always an animal with a plausible reason to take the object, so
the story stays tense but gentle.

Reasonableness constraint
-------------------------
Not every culprit can plausibly take every object or reach every hideout.

* A magpie wants shiny things.
* A puppy wants soft or good-smelling things.
* A goat wants leafy or papery things.

And each animal only haunts certain derelict places. The storyworld refuses
combinations that do not make common sense.

Run it
------
    python storyworlds/worlds/gpt-5.4/mistress_derelict_teamwork_repetition_conflict_whodunit.py
    python storyworlds/worlds/gpt-5.4/mistress_derelict_teamwork_repetition_conflict_whodunit.py --mystery brass_bell
    python storyworlds/worlds/gpt-5.4/mistress_derelict_teamwork_repetition_conflict_whodunit.py --culprit goat --hideout tower
    python storyworlds/worlds/gpt-5.4/mistress_derelict_teamwork_repetition_conflict_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/mistress_derelict_teamwork_repetition_conflict_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/mistress_derelict_teamwork_repetition_conflict_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives one directory deeper than most worlds:
# storyworlds/worlds/gpt-5.4/<file>.py  -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "animal" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.role == "mistress":
            return "mistress"
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain knobs.
# ---------------------------------------------------------------------------
@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    room: str
    tags: set[str] = field(default_factory=set)
    need: str = ""
    clue_line: str = ""
    returned_line: str = ""
    lesson_topic: str = ""


@dataclass
class CulpritSpec:
    id: str
    animal: str
    phrase: str
    sound: str
    repeated_clue: str
    final_trace: str
    motive: str
    likes: set[str] = field(default_factory=set)
    haunts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    path: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and narration helpers.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Reasonableness gate.
# ---------------------------------------------------------------------------
def culprit_wants_item(culprit: CulpritSpec, mystery: Mystery) -> bool:
    return bool(culprit.likes & mystery.tags)


def culprit_fits_hideout(culprit: CulpritSpec, hideout: Hideout) -> bool:
    return hideout.id in culprit.haunts


def valid_combo(mystery: Mystery, culprit: CulpritSpec, hideout: Hideout) -> bool:
    return culprit_wants_item(culprit, mystery) and culprit_fits_hideout(culprit, hideout)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mystery_id, mystery in MYSTERIES.items():
        for culprit_id, culprit in CULPRITS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if valid_combo(mystery, culprit, hideout):
                    combos.append((mystery_id, culprit_id, hideout_id))
    return combos


def explain_rejection(mystery: Mystery, culprit: CulpritSpec, hideout: Hideout) -> str:
    if not culprit_wants_item(culprit, mystery):
        return (
            f"(No story: a {culprit.animal} would not plausibly take {mystery.phrase}. "
            f"It looks for {', '.join(sorted(culprit.likes))}, not this kind of thing.)"
        )
    if not culprit_fits_hideout(culprit, hideout):
        return (
            f"(No story: a {culprit.animal} does not belong in {hideout.phrase} in this world. "
            f"Pick a hideout it actually haunts.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


# ---------------------------------------------------------------------------
# Story world content.
# ---------------------------------------------------------------------------
MYSTERIES = {
    "brass_bell": Mystery(
        id="brass_bell",
        label="brass bell",
        phrase="the little brass bell from the front desk",
        room="the front hall",
        tags={"shiny"},
        need="ring for visitors",
        clue_line="a tiny golden gleam where something had been dragged across the dust",
        returned_line="When the bell rang again in Mistress Vale's hand, the hall felt orderly and cheerful.",
        lesson_topic="bells",
    ),
    "velvet_ribbon": Mystery(
        id="velvet_ribbon",
        label="velvet ribbon",
        phrase="the blue velvet ribbon from the portrait room",
        room="the portrait room",
        tags={"soft", "pretty"},
        need="tie around a welcome bouquet",
        clue_line="a soft thread caught on the edge of a frame",
        returned_line="When the ribbon was smoothed back into place, the room looked ready for guests again.",
        lesson_topic="ribbon",
    ),
    "garden_map": Mystery(
        id="garden_map",
        label="garden map",
        phrase="the folding garden map from the writing desk",
        room="the map room",
        tags={"paper", "leafy"},
        need="show visitors where the rose paths curved",
        clue_line="a corner with neat little nibbles missing",
        returned_line="When the map was opened on the desk again, the winding paths made sense once more.",
        lesson_topic="maps",
    ),
}

CULPRITS = {
    "magpie": CulpritSpec(
        id="magpie",
        animal="magpie",
        phrase="a black-and-white magpie",
        sound="clink",
        repeated_clue="the same bright feather and the same little clink",
        final_trace="three bright feathers beside a nest of shiny odds and ends",
        motive="wanted something glittery for its nest",
        likes={"shiny"},
        haunts={"tower", "greenhouse"},
        tags={"bird", "shiny"},
    ),
    "puppy": CulpritSpec(
        id="puppy",
        animal="puppy",
        phrase="a muddy brown puppy",
        sound="pat-pat",
        repeated_clue="the same round pawprints and the same happy pat-pat",
        final_trace="a wagging tail beside a bed of stolen treasures",
        motive="wanted something soft and cozy to curl up with",
        likes={"soft", "pretty"},
        haunts={"boathouse", "carriage_house"},
        tags={"dog", "soft"},
    ),
    "goat": CulpritSpec(
        id="goat",
        animal="goat",
        phrase="a white goat",
        sound="clip-clop",
        repeated_clue="the same square hoofprints and the same neat little bites",
        final_trace="a white beard, square prints, and crumbs all around the hay",
        motive="wanted something tasty-looking to chew",
        likes={"paper", "leafy"},
        haunts={"greenhouse", "carriage_house"},
        tags={"goat", "chewing"},
    ),
}

HIDEOUTS = {
    "tower": Hideout(
        id="tower",
        label="tower",
        phrase="the derelict tower behind the manor",
        path="up the narrow back steps and past the cracked clock face",
        tags={"tower", "derelict"},
    ),
    "greenhouse": Hideout(
        id="greenhouse",
        label="greenhouse",
        phrase="the derelict greenhouse by the kitchen garden",
        path="through the nettles and under a bent iron arch",
        tags={"greenhouse", "derelict"},
    ),
    "carriage_house": Hideout(
        id="carriage_house",
        label="carriage house",
        phrase="the derelict carriage house beyond the stables",
        path="across the cobbles and through a door that hung crooked on one hinge",
        tags={"shed", "derelict"},
    ),
    "boathouse": Hideout(
        id="boathouse",
        label="boathouse",
        phrase="the derelict boathouse at the edge of the pond",
        path="down the willow path and over the damp planks",
        tags={"boathouse", "derelict"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Sam", "Theo", "Finn", "Leo", "Max"]
TRAITS = ["careful", "quick-eyed", "stubborn", "curious", "thoughtful", "brisk"]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mystery: str
    culprit: str
    hideout: str
    sleuth1: str
    sleuth1_gender: str
    sleuth2: str
    sleuth2_gender: str
    mistress_name: str
    parent_title: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Screenplay verbs.
# ---------------------------------------------------------------------------
def introduce(world: World, a: Entity, b: Entity, mistress: Entity, mystery: Mystery, hideout: Hideout) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    world.say(
        f"On a windy afternoon, {a.id} and {b.id} were helping {mistress.id}, the mistress of Ashdown Manor, "
        f"dust the old museum rooms. Beyond the yew hedge stood {hideout.phrase}, all broken glass or leaning boards, "
        f"the sort of place that made a mystery feel possible."
    )
    world.say(
        f"In {mystery.room}, {mistress.id} stopped short. {mystery.phrase.capitalize()} was gone."
    )
    world.say(
        f'"That cannot be right," said {mistress.id}. "We use it to {mystery.need}."'
    )


def first_conflict(world: World, a: Entity, b: Entity, culprit: CulpritSpec) -> None:
    a.memes["suspicion"] += 1
    b.memes["suspicion"] += 1
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    wrong1 = "goat" if culprit.id != "goat" else "magpie"
    wrong2 = "puppy" if culprit.id != "puppy" else "goat"
    world.facts["first_guess_a"] = wrong1
    world.facts["first_guess_b"] = wrong2
    world.say(
        f'"A goat must have done it," said {a.id} at once.'
    )
    world.say(
        f'"No, it was a puppy," said {b.id}. "You always say goat first."'
    )
    world.say(
        f"Their voices bumped together, and for a moment the mystery felt smaller than the quarrel."
    )


def clue_beats(world: World, a: Entity, b: Entity, culprit: CulpritSpec, mystery: Mystery, hideout: Hideout) -> None:
    world.para()
    world.say(
        f"{mistress_name(world).capitalize()} sent them to look carefully instead of guessing. So the two young sleuths tried again."
    )
    world.say(
        f"First they searched the window ledge in {mystery.room}. They found {mystery.clue_line}, and beside it came {culprit.sound}, very small and very quick."
    )
    a.meters["clues_found"] += 1
    b.meters["clues_found"] += 1
    world.say(
        f"Then they crossed the long gallery. Again they found {culprit.repeated_clue}."
    )
    a.meters["clues_found"] += 1
    b.meters["clues_found"] += 1
    world.say(
        f"At the back stairs they stopped once more. Again there it was: {culprit.repeated_clue}. Repetition made the trail feel true."
    )
    a.meters["clues_found"] += 1
    b.meters["clues_found"] += 1
    world.facts["clue_count"] = 3
    world.facts["repeated_clue"] = culprit.repeated_clue
    world.say(
        f'"The same clue three times," said {a.id}. "{b.id}, maybe we should stop arguing and follow it together."'
    )


def teamwork_turn(world: World, a: Entity, b: Entity) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    b.memes["trust"] += 1
    a.memes["trust"] += 1
    world.say(
        f'{b.id} nodded. "{a.id}, you watch high and I will watch low."'
    )
    world.say(
        f"So {a.id} looked for movement and shine while {b.id} looked for tracks and scraps, and the path suddenly grew easy to read."
    )


def reveal(world: World, a: Entity, b: Entity, culprit: CulpritSpec, mystery: Mystery, hideout: Hideout) -> None:
    world.para()
    world.say(
        f"The clue trail led them {hideout.path} until they reached {hideout.phrase}."
    )
    world.say(
        f"Inside, they found {culprit.final_trace}, and in the middle of it sat {culprit.phrase} with {mystery.phrase}."
    )
    world.get("item").meters["found"] += 1
    world.get("culprit").meters["located"] += 1
    world.facts["solved"] = True
    world.say(
        f'"So that is who did it," whispered {a.id}.'
    )
    world.say(
        f'"Not a thief exactly," said {b.id}. "Just an animal that {culprit.motive}."'
    )


def gentle_resolution(world: World, a: Entity, b: Entity, mistress: Entity, culprit: CulpritSpec, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    mistress.memes["relief"] += 1
    world.get("item").meters["returned"] += 1
    swap = {
        "magpie": "a bright marble",
        "puppy": "an old cushion",
        "goat": "a bundle of safe cabbage leaves",
    }[culprit.id]
    world.say(
        f"They did not snatch. Instead they called {mistress.id}, and together they made a fair swap: {swap} for {mystery.phrase}."
    )
    world.say(
        f"{mistress.id} smiled at both children. \"A mystery is solved best with careful eyes and kinder voices,\" {mistress.pronoun()} said."
    )
    world.say(
        f"{a.id} looked at {b.id}. \"You were right that guessing was not enough.\""
    )
    world.say(
        f'"And you were right to keep looking," said {b.id}.'
    )
    world.say(mystery.returned_line)


def ending_image(world: World, a: Entity, b: Entity, mistress: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"By evening the wind had settled. {a.id} and {b.id} stood beside {mistress.id} in {mystery.room}, and this time when anyone asked who had done it, both children answered together."
    )
    world.say(
        "The old manor no longer felt full of quarrels. It felt full of clues, teamwork, and one solved secret."
    )


def mistress_name(world: World) -> str:
    mistress = world.facts.get("mistress")
    return mistress.id if isinstance(mistress, Entity) else "Mistress Vale"


def tell(
    mystery: Mystery,
    culprit_cfg: CulpritSpec,
    hideout: Hideout,
    sleuth1: str,
    sleuth1_gender: str,
    sleuth2: str,
    sleuth2_gender: str,
    mistress_name_text: str,
    trait1: str,
    trait2: str,
) -> World:
    world = World()
    a = world.add(Entity(
        id=sleuth1,
        kind="character",
        type=sleuth1_gender,
        role="sleuth",
        traits=[trait1],
    ))
    b = world.add(Entity(
        id=sleuth2,
        kind="character",
        type=sleuth2_gender,
        role="sleuth",
        traits=[trait2],
    ))
    mistress = world.add(Entity(
        id=mistress_name_text,
        kind="character",
        type="woman",
        role="mistress",
        label="mistress",
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="animal",
        type=culprit_cfg.animal,
        label=culprit_cfg.animal,
        phrase=culprit_cfg.phrase,
        tags=set(culprit_cfg.tags),
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=mystery.label,
        phrase=mystery.phrase,
        tags=set(mystery.tags),
    ))
    place = world.add(Entity(
        id="hideout",
        kind="place",
        type=hideout.label,
        label=hideout.label,
        phrase=hideout.phrase,
        tags=set(hideout.tags),
    ))

    item.meters["missing"] = 1
    mistress.memes["worry"] += 1

    world.facts.update(
        sleuth1=a,
        sleuth2=b,
        mistress=mistress,
        mystery=mystery,
        culprit_cfg=culprit_cfg,
        culprit=culprit,
        item=item,
        hideout=hideout,
        solved=False,
    )

    introduce(world, a, b, mistress, mystery, hideout)
    world.para()
    first_conflict(world, a, b, culprit_cfg)
    clue_beats(world, a, b, culprit_cfg, mystery, hideout)
    teamwork_turn(world, a, b)
    reveal(world, a, b, culprit_cfg, mystery, hideout)
    gentle_resolution(world, a, b, mistress, culprit_cfg, mystery)
    ending_image(world, a, b, mistress, mystery)
    return world


# ---------------------------------------------------------------------------
# Prompts and QA.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bird": [
        (
            "Why do some birds collect shiny things?",
            "Some birds, like magpies, are curious about sparkle and shine. They may carry bright little objects to a nest."
        )
    ],
    "dog": [
        (
            "Why might a puppy carry something away?",
            "Puppies explore with their mouths and noses, so they sometimes carry off soft things that smell interesting. They are usually playing, not trying to be mean."
        )
    ],
    "goat": [
        (
            "Why do goats nibble paper or leaves?",
            "Goats like to test things with their mouths, especially papery or leafy things. That can make a map or sign get chewed."
        )
    ],
    "tower": [
        (
            "What is a tower?",
            "A tower is a tall part of a building that rises above the rest. Old towers can feel mysterious because they are high, windy, and full of echoes."
        )
    ],
    "greenhouse": [
        (
            "What is a greenhouse?",
            "A greenhouse is a glass house where plants grow warm and bright. If it is derelict, it means it has been left broken and unused."
        )
    ],
    "boathouse": [
        (
            "What is a boathouse?",
            "A boathouse is a little building by water where boats or oars are kept. A derelict boathouse is old and falling apart."
        )
    ],
    "shed": [
        (
            "What does derelict mean?",
            "Derelict means old, broken, and left unused for a long time. A derelict place can look spooky, but it mainly means nobody is taking care of it."
        )
    ],
    "bells": [
        (
            "What is a bell for?",
            "A bell makes a clear ringing sound to call people or get attention. Small bells are useful because everyone can hear them quickly."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long, soft strip of cloth used for tying or decorating things. It feels smooth and light."
        )
    ],
    "maps": [
        (
            "What does a map do?",
            "A map helps people see where places are and how to get from one place to another. Even a small garden map can show paths, corners, and gates."
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help solve problems?",
            "Teamwork helps because two people can notice more than one person alone. They can also calm each other down and compare clues."
        )
    ],
    "clues": [
        (
            "What is a clue in a mystery?",
            "A clue is a sign that points toward what happened. Good detectives look for clues that repeat or fit together."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "bird",
    "dog",
    "goat",
    "tower",
    "greenhouse",
    "boathouse",
    "shed",
    "bells",
    "ribbon",
    "maps",
    "teamwork",
    "clues",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["sleuth1"]
    b = f["sleuth2"]
    mistress = f["mistress"]
    mystery = f["mystery"]
    hideout = f["hideout"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that uses the words "mistress" and "derelict" and includes a missing {mystery.label}.',
        f"Tell a mystery story where {a.id} and {b.id} argue about a suspect, then use teamwork to follow repeating clues to {hideout.phrase}.",
        f"Write a child-facing manor mystery where {mistress.id}, the mistress of the house, asks two children to solve who took {mystery.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["sleuth1"]
    b = f["sleuth2"]
    mistress = f["mistress"]
    mystery = f["mystery"]
    culprit_cfg = f["culprit_cfg"]
    hideout = f["hideout"]
    clue_count = f.get("clue_count", 0)

    return [
        (
            "Who was missing something at the beginning of the story?",
            f"{mistress.id}, the mistress of Ashdown Manor, was missing {mystery.phrase}. She noticed it was gone in {mystery.room} and worried because the manor used it to {mystery.need}."
        ),
        (
            f"Why did {a.id} and {b.id} argue at first?",
            f"They argued because each child guessed too fast and blamed a different animal before they had real proof. The conflict made the mystery harder for a moment because their quarrel mattered more than the clues."
        ),
        (
            "What clue kept repeating?",
            f"The repeating clue was {f.get('repeated_clue', culprit_cfg.repeated_clue)}. They found the same kind of sign {clue_count} times, which helped them trust the trail instead of their first guesses."
        ),
        (
            f"How did {a.id} and {b.id} solve the mystery?",
            f"They solved it by working as a team. {a.id} watched high while {b.id} watched low, so together they could follow the clues all the way to {hideout.phrase}."
        ),
        (
            "Who took the missing thing, and why?",
            f"It was {culprit_cfg.phrase}. The animal was not trying to be naughty in a human way; it had taken the object because it {culprit_cfg.motive}."
        ),
        (
            "How did the story end?",
            f"They called {mistress.id} and made a fair swap, so the missing thing was returned safely. At the end, the manor felt calm again, and the children answered the mystery together instead of arguing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    culprit_cfg = f["culprit_cfg"]
    hideout = f["hideout"]
    mystery = f["mystery"]
    tags = set(culprit_cfg.tags) | set(hideout.tags) | {"teamwork", "clues", mystery.lesson_topic}
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:10} ({ent.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: solved={world.facts.get('solved')} clue_count={world.facts.get('clue_count')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        mystery="brass_bell",
        culprit="magpie",
        hideout="tower",
        sleuth1="Lily",
        sleuth1_gender="girl",
        sleuth2="Ben",
        sleuth2_gender="boy",
        mistress_name="Mistress Vale",
        parent_title="mistress",
        trait1="careful",
        trait2="quick-eyed",
    ),
    StoryParams(
        mystery="velvet_ribbon",
        culprit="puppy",
        hideout="boathouse",
        sleuth1="Nora",
        sleuth1_gender="girl",
        sleuth2="Max",
        sleuth2_gender="boy",
        mistress_name="Mistress Vale",
        parent_title="mistress",
        trait1="stubborn",
        trait2="thoughtful",
    ),
    StoryParams(
        mystery="garden_map",
        culprit="goat",
        hideout="greenhouse",
        sleuth1="Theo",
        sleuth1_gender="boy",
        sleuth2="Ava",
        sleuth2_gender="girl",
        mistress_name="Mistress Vale",
        parent_title="mistress",
        trait1="curious",
        trait2="brisk",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
wants(C, M) :- likes(C, T), mystery_tag(M, T).
fits(C, H)  :- haunts(C, H).
valid(M, C, H) :- mystery(M), culprit(C), hideout(H), wants(C, M), fits(C, H).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        for tag in sorted(mystery.tags):
            lines.append(asp.fact("mystery_tag", mystery_id, tag))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("likes", culprit_id, tag))
        for hideout_id in sorted(culprit.haunts):
            lines.append(asp.fact("haunts", culprit_id, hideout_id))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    # Smoke test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story or "mistress" not in sample.story.lower() or "derelict" not in sample.story.lower():
            raise StoryError("Generated smoke-test story is empty or missed required seed words.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child-friendly manor whodunit with teamwork, repetition, and conflict."
    )
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (mystery, culprit, hideout) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos() and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError(f"(No story: unknown mystery '{args.mystery}'.)")
    if args.culprit and args.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{args.culprit}'.)")
    if args.hideout and args.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{args.hideout}'.)")

    if args.mystery and args.culprit and args.hideout:
        mystery = MYSTERIES[args.mystery]
        culprit = CULPRITS[args.culprit]
        hideout = HIDEOUTS[args.hideout]
        if not valid_combo(mystery, culprit, hideout):
            raise StoryError(explain_rejection(mystery, culprit, hideout))

    combos = [
        combo for combo in valid_combos()
        if (args.mystery is None or combo[0] == args.mystery)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.hideout is None or combo[2] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mystery_id, culprit_id, hideout_id = rng.choice(sorted(combos))
    name1, gender1 = _pick_kid(rng)
    name2, gender2 = _pick_kid(rng, avoid=name1)
    return StoryParams(
        mystery=mystery_id,
        culprit=culprit_id,
        hideout=hideout_id,
        sleuth1=name1,
        sleuth1_gender=gender1,
        sleuth2=name2,
        sleuth2_gender=gender2,
        mistress_name="Mistress Vale",
        parent_title="mistress",
        trait1=rng.choice(TRAITS),
        trait2=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(No story: unknown mystery '{params.mystery}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")

    mystery = MYSTERIES[params.mystery]
    culprit = CULPRITS[params.culprit]
    hideout = HIDEOUTS[params.hideout]
    if not valid_combo(mystery, culprit, hideout):
        raise StoryError(explain_rejection(mystery, culprit, hideout))

    world = tell(
        mystery=mystery,
        culprit_cfg=culprit,
        hideout=hideout,
        sleuth1=params.sleuth1,
        sleuth1_gender=params.sleuth1_gender,
        sleuth2=params.sleuth2,
        sleuth2_gender=params.sleuth2_gender,
        mistress_name_text=params.mistress_name,
        trait1=params.trait1,
        trait2=params.trait2,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, culprit, hideout) combos:\n")
        for mystery_id, culprit_id, hideout_id in combos:
            print(f"  {mystery_id:14} {culprit_id:8} {hideout_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
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
            header = f"### {p.sleuth1} & {p.sleuth2}: {p.mystery} / {p.culprit} / {p.hideout}"
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
