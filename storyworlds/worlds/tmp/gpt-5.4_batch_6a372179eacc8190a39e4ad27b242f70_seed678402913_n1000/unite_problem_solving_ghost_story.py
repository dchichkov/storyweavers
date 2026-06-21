#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/unite_problem_solving_ghost_story.py
===============================================================

A small standalone storyworld for gentle, child-facing ghost stories about
problem solving and bringing things back together. Two children meet a lonely
ghost whose keepsake has come apart. They must notice clues, search the room,
and choose a repair that can truly unite the missing pieces.

The world model prefers a narrow, believable domain over broad coverage:
different keepsakes break in different ways, and only some fixes make sense.
A ribbon can tie a bundle of letters, but it cannot mend cracked china. Glue
can mend a cracked music-box lid, but it does not help a missing key. Thread
can sew cloth, but it does not repair porcelain.

Run it
------
    python storyworlds/worlds/gpt-5.4/unite_problem_solving_ghost_story.py
    python storyworlds/worlds/gpt-5.4/unite_problem_solving_ghost_story.py --place attic --keepsake quilt --fix thread
    python storyworlds/worlds/gpt-5.4/unite_problem_solving_ghost_story.py --keepsake teacup --fix ribbon
    python storyworlds/worlds/gpt-5.4/unite_problem_solving_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/unite_problem_solving_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/unite_problem_solving_ghost_story.py --verify
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
# this file lives under storyworlds/worlds/gpt-5.4/, so go up three levels to
# storyworlds/ and import results from there.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    cloth: bool = False
    tieable: bool = False
    musical: bool = False
    # Shared physical / emotional state.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str = ""
    intro: str = ""
    spooky: str = ""
    hiding_spots: tuple[str, str] = ("", "")
    ending_glow: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str = ""
    phrase: str = ""
    first_part: str = ""
    second_part: str = ""
    clue_sound: str = ""
    clue_image: str = ""
    ghost_memory: str = ""
    repair_story: str = ""
    end_image: str = ""
    needs: str = ""                # "glue" | "thread" | "ribbon"
    tieable: bool = False
    cloth: bool = False
    fragile: bool = False
    musical: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str = ""
    phrase: str = ""
    works_for: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "child"]

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
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lonely_wail(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    keepsake = world.entities.get("keepsake")
    room = world.entities.get("room")
    if ghost is None or keepsake is None or room is None:
        return out
    if keepsake.meters["separated"] < THRESHOLD:
        return out
    sig = ("lonely_wail",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["lonely"] += 1
    room.meters["spooky"] += 1
    for kid in world.kids():
        kid.memes["shiver"] += 1
    out.append("__spooky__")
    return out


def _r_repair_soothes(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    keepsake = world.entities.get("keepsake")
    room = world.entities.get("room")
    if ghost is None or keepsake is None or room is None:
        return out
    if keepsake.meters["whole"] < THRESHOLD:
        return out
    sig = ("repair_soothes",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["lonely"] = 0.0
    ghost.memes["peace"] += 1
    room.meters["spooky"] = 0.0
    room.meters["warmth"] += 1
    for kid in world.kids():
        kid.memes["brave"] += 1
        kid.memes["care"] += 1
    out.append("__peace__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="lonely_wail", tag="emotional", apply=_r_lonely_wail),
    Rule(name="repair_soothes", tag="emotional", apply=_r_repair_soothes),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def repair_possible(keepsake: Keepsake, fix: Fix) -> bool:
    return keepsake.needs in fix.works_for


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for keepsake_id, keepsake in KEEPSAKES.items():
        for fix_id, fix in FIXES.items():
            if repair_possible(keepsake, fix):
                combos.append((keepsake_id, fix_id))
    return combos


def explain_rejection(keepsake: Keepsake, fix: Fix) -> str:
    why = {
        "glue": "something cracked and hard",
        "thread": "something soft that can be sewn",
        "ribbon": "loose pieces that can be tied neatly together",
    }[keepsake.needs]
    return (
        f"(No story: {fix.label.capitalize()} does not make sense for {keepsake.phrase}. "
        f"This keepsake needs a fix for {why}, so it cannot be repaired that way.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_peace(world: World, keepsake_id: str, fix_id: str) -> dict:
    sim = world.copy()
    k = sim.get(keepsake_id)
    chosen_fix = FIXES[fix_id]
    if repair_possible(KEEPSAKES[k.attrs["cfg"]], chosen_fix):
        k.meters["whole"] += 1
        k.meters["separated"] = 0.0
        propagate(sim, narrate=False)
    return {
        "peace": sim.get("ghost").memes["peace"],
        "spooky": sim.get("room").meters["spooky"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def arrive(world: World, child1: Entity, child2: Entity, place: Place) -> None:
    for kid in (child1, child2):
        kid.memes["curious"] += 1
    world.say(
        f"On a windy evening, {child1.id} and {child2.id} climbed into {place.label}. "
        f"{place.intro}"
    )
    world.say(place.spooky)


def discover_clue(world: World, child1: Entity, child2: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"Then they heard {keepsake.clue_sound}, and in the dim light they noticed "
        f"{keepsake.clue_image}."
    )
    world.say(
        f'"Did you see that?" whispered {child1.id}. {child2.id} took a breath and nodded.'
    )


def meet_ghost(world: World, ghost: Entity, keepsake: Keepsake) -> None:
    ghost.memes["hope"] += 1
    world.say(
        f"Out of the shadows drifted a small pale ghost with kind eyes. "
        f'"Please don\'t run," the ghost whispered. "My {keepsake.label} came apart, '
        f"and I have not known how to make it whole again.\""
    )
    world.say(
        f'The ghost pointed to one piece and then another. "If someone could unite '
        f'them, I think my room would stop feeling so cold."'
    )


def search(world: World, child1: Entity, child2: Entity, place: Place, keepsake: Keepsake) -> None:
    child1.memes["focus"] += 1
    child2.memes["focus"] += 1
    spot1, spot2 = place.hiding_spots
    world.say(
        f"{child1.id} looked under {spot1}, and {child2.id} checked behind {spot2}. "
        f"Soon they found {keepsake.first_part} and {keepsake.second_part}."
    )
    world.say(
        f"They set the pieces together on an old trunk and saw exactly what was wrong."
    )


def reason_out(world: World, child1: Entity, child2: Entity, keepsake: Keepsake, fix: Fix) -> None:
    pred = predict_peace(world, "keepsake", fix.id)
    world.facts["predicted_peace"] = pred["peace"]
    world.facts["predicted_spooky"] = pred["spooky"]
    child1.memes["problem_solving"] += 1
    child2.memes["problem_solving"] += 1
    world.say(
        f'"We should think first," said {child2.id}. "A {keepsake.label} needs the right kind of help."'
    )
    world.say(
        f"{child1.id} studied the pieces, then smiled. "
        f'"{fix.phrase.capitalize()} could work here. If we fix it the right way, '
        f"the ghost might finally rest.\""
    )


def mend(world: World, child1: Entity, child2: Entity, keepsake_ent: Entity,
         keepsake: Keepsake, fix: Fix) -> None:
    keepsake_ent.meters["whole"] += 1
    keepsake_ent.meters["separated"] = 0.0
    keepsake_ent.attrs["repaired_with"] = fix.id
    propagate(world, narrate=False)
    world.say(
        f"Very gently, {child1.id} and {child2.id} {fix.action}. They worked slowly, "
        f"holding still whenever the floor creaked under them."
    )
    world.say(keepsake.repair_story)


def calm(world: World, ghost: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"The ghost looked at the whole {keepsake.label} and gave a soft sigh that sounded almost like a song."
    )
    world.say(
        f'"Thank you," the ghost said. "That was what I had lost -- not only the pieces, but the chance to see them together again."'
    )


def ending(world: World, child1: Entity, child2: Entity, place: Place, keepsake: Keepsake) -> None:
    world.say(
        f"{place.ending_glow} {keepsake.end_image}"
    )
    world.say(
        f"{child1.id} and {child2.id} held hands for one moment, listening to the now-quiet room. "
        f"They had come in shivering, but they left smiling, because care and clever thinking had changed the night."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(place: Place, keepsake: Keepsake, fix: Fix,
         child1_name: str = "Nora", child1_gender: str = "girl",
         child2_name: str = "Eli", child2_gender: str = "boy",
         adult_type: str = "grandmother",
         pet: str = "") -> World:
    world = World()
    child1 = world.add(Entity(
        id=child1_name,
        kind="character",
        type=child1_gender,
        role="child",
        traits=["careful"],
    ))
    child2 = world.add(Entity(
        id=child2_name,
        kind="character",
        type=child2_gender,
        role="child",
        traits=["steady"],
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        role="ghost",
        label="the ghost",
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
    ))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        type="keepsake",
        label=keepsake.label,
        phrase=keepsake.phrase,
        fragile=keepsake.fragile,
        cloth=keepsake.cloth,
        tieable=keepsake.tieable,
        musical=keepsake.musical,
        attrs={"cfg": keepsake.id},
    ))

    keepsake_ent.meters["separated"] = 1.0
    propagate(world, narrate=False)

    world.facts["pet"] = pet

    arrive(world, child1, child2, place)
    discover_clue(world, child1, child2, keepsake)

    world.para()
    meet_ghost(world, ghost, keepsake)
    search(world, child1, child2, place, keepsake)
    reason_out(world, child1, child2, keepsake, fix)

    world.para()
    mend(world, child1, child2, keepsake_ent, keepsake, fix)
    calm(world, ghost, keepsake)

    world.para()
    ending(world, child1, child2, place, keepsake)

    outcome = "peaceful" if ghost.memes["peace"] >= THRESHOLD else "uneasy"
    world.facts.update(
        child1=child1,
        child2=child2,
        ghost=ghost,
        adult=adult,
        room=room,
        place=place,
        keepsake_cfg=keepsake,
        keepsake=keepsake_ent,
        fix=fix,
        outcome=outcome,
        united=keepsake_ent.meters["whole"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(
        id="attic",
        label="the old attic",
        intro="Dust floated through the moonbeams, and every hanging coat looked like it might move.",
        spooky="A loose windowpane gave a tiny rattle, and the corners seemed to keep their own secrets.",
        hiding_spots=("a cedar chest", "a stack of trunks"),
        ending_glow="Moonlight spilled wider across the floor, and the attic no longer felt hungry for footsteps.",
        tags={"attic", "ghost"},
    ),
    "hallway": Place(
        id="hallway",
        label="the upstairs hallway",
        intro="Portraits watched from the walls, and the runner rug whispered under each step.",
        spooky="At the far end, a lamp flickered, and a chill brushed past their knees like a quiet cat.",
        hiding_spots=("the umbrella stand", "a tall grandfather clock"),
        ending_glow="The lamp stopped flickering, and the long hallway felt like part of a home again.",
        tags={"hallway", "ghost"},
    ),
    "nursery": Place(
        id="nursery",
        label="the dusty nursery",
        intro="The moon shone through lace curtains, and a wooden rocker moved once and then stood still.",
        spooky="Shadows rocked gently on the wall, though there was no hand there to push them.",
        hiding_spots=("a toy chest", "the little bed"),
        ending_glow="The curtains lifted in a soft breeze, and the nursery felt sleepy instead of sad.",
        tags={"nursery", "ghost"},
    ),
}

KEEPSAKES = {
    "music_box": Keepsake(
        id="music_box",
        label="music box",
        phrase="a silver music box",
        first_part="the cracked lid",
        second_part="the tiny dancing figure",
        clue_sound="a thin, unfinished tune",
        clue_image="a glint of silver under a blanket of dust",
        ghost_memory="The music box used to play at bedtime.",
        repair_story="When the last bit held, the little dancer stood straight, and one clear note trembled out into the dark.",
        end_image="From somewhere inside the box came a sleepy little melody, gentle as a lullaby.",
        needs="glue",
        fragile=True,
        musical=True,
        tags={"music_box", "glue", "ghost"},
    ),
    "quilt": Keepsake(
        id="quilt",
        label="quilt",
        phrase="a patchwork quilt",
        first_part="a loose corner square",
        second_part="the waiting edge of the quilt",
        clue_sound="a soft rustle like cloth being turned over",
        clue_image="a trail of bright thread across the floorboards",
        ghost_memory="The quilt was sewn by loving hands for winter nights.",
        repair_story="Their fingers pulled the thread in and out until the loose square sat snugly where it belonged.",
        end_image="The patchwork squares lay smooth again, and the quilt looked ready to warm somebody's dreams.",
        needs="thread",
        cloth=True,
        tags={"quilt", "thread", "ghost"},
    ),
    "letters": Keepsake(
        id="letters",
        label="letters",
        phrase="a bundle of old letters",
        first_part="the scattered pages",
        second_part="the faded envelope",
        clue_sound="a papery flutter from the dark",
        clue_image="a corner of cream paper peeking from under a stool",
        ghost_memory="The letters carried words the ghost never wanted forgotten.",
        repair_story="They stacked the pages in order, slipped them into the envelope, and tied them carefully so nothing would drift away again.",
        end_image="The letters rested together in one neat bundle, as if the house itself had remembered how to keep a promise.",
        needs="ribbon",
        tieable=True,
        tags={"letters", "ribbon", "ghost"},
    ),
    "teacup": Keepsake(
        id="teacup",
        label="teacup",
        phrase="a blue china teacup",
        first_part="the chipped cup",
        second_part="the little curved handle",
        clue_sound="the faintest clink, like china touching china",
        clue_image="a blue piece shining near the skirting board",
        ghost_memory="The teacup had once sat by a warm window every afternoon.",
        repair_story="They pressed the curved handle back in place and waited until the join held firm.",
        end_image="The blue flowers on the cup made one whole pattern again, small and bright in the moonlight.",
        needs="glue",
        fragile=True,
        tags={"teacup", "glue", "ghost"},
    ),
}

FIXES = {
    "glue": Fix(
        id="glue",
        label="glue",
        phrase="a little bottle of glue",
        works_for={"glue"},
        action="used a little bottle of glue to press the hard pieces back together",
        qa_text="used glue to join the hard broken pieces",
        tags={"glue", "repair"},
    ),
    "thread": Fix(
        id="thread",
        label="thread and needle",
        phrase="thread and a small needle",
        works_for={"thread"},
        action="used thread and a small needle to sew the loose cloth back where it belonged",
        qa_text="sewed the loose cloth back with thread and a needle",
        tags={"thread", "repair"},
    ),
    "ribbon": Fix(
        id="ribbon",
        label="ribbon",
        phrase="a soft blue ribbon",
        works_for={"ribbon"},
        action="wrapped a soft ribbon around the pages and tied them into one careful bundle",
        qa_text="tied the scattered letters together with ribbon",
        tags={"ribbon", "repair"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Rose", "Ava", "Lucy", "Clara", "June"]
BOY_NAMES = ["Eli", "Ben", "Max", "Theo", "Sam", "Finn", "Noah", "Leo"]
PETS = ["the cat", "the little dog", "the old house cat", ""]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    keepsake: str
    fix: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str
    pet: str = ""
    seed: Optional[int] = None


# Curated set
CURATED = [
    StoryParams(
        place="attic",
        keepsake="quilt",
        fix="thread",
        child1="Nora",
        child1_gender="girl",
        child2="Eli",
        child2_gender="boy",
        adult="grandmother",
        pet="the cat",
    ),
    StoryParams(
        place="hallway",
        keepsake="letters",
        fix="ribbon",
        child1="Ben",
        child1_gender="boy",
        child2="Lucy",
        child2_gender="girl",
        adult="grandfather",
        pet="",
    ),
    StoryParams(
        place="nursery",
        keepsake="music_box",
        fix="glue",
        child1="Rose",
        child1_gender="girl",
        child2="Max",
        child2_gender="boy",
        adult="mother",
        pet="the little dog",
    ),
    StoryParams(
        place="hallway",
        keepsake="teacup",
        fix="glue",
        child1="June",
        child1_gender="girl",
        child2="Theo",
        child2_gender="boy",
        adult="father",
        pet="",
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spooky feeling and a ghost in it. In gentle ghost stories, the ghost is often sad or lonely instead of mean."
        )
    ],
    "glue": [
        (
            "What does glue do?",
            "Glue sticks hard pieces together so they can become one whole thing again. You have to let it hold still so the repair stays in place."
        )
    ],
    "thread": [
        (
            "What do thread and a needle do?",
            "Thread and a needle can sew cloth together. They help mend soft things like quilts or clothes."
        )
    ],
    "ribbon": [
        (
            "What can a ribbon do in a repair?",
            "A ribbon can tie loose papers or little bundles together neatly. It helps keep pieces from drifting apart."
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a small box that can play a tune. Some music boxes have tiny moving figures inside."
        )
    ],
    "quilt": [
        (
            "What is a quilt?",
            "A quilt is a warm blanket made from pieces of cloth sewn together. Many quilts have patterns made from different squares."
        )
    ],
    "letters": [
        (
            "Why are letters important?",
            "Letters can carry someone's words across time and distance. People keep them because the words can hold memories and love."
        )
    ],
    "teacup": [
        (
            "Why can a china teacup break easily?",
            "China is hard but fragile, so it can chip or crack if it falls or bumps into something. That is why people handle it gently."
        )
    ],
    "repair": [
        (
            "Why is problem solving helpful?",
            "Problem solving helps you slow down, notice what is wrong, and choose a fix that truly matches the problem. Thinking carefully can turn a scary moment into a hopeful one."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost",
    "repair",
    "glue",
    "thread",
    "ribbon",
    "music_box",
    "quilt",
    "letters",
    "teacup",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    keepsake = f["keepsake_cfg"]
    child1 = f["child1"]
    child2 = f["child2"]
    fix = f["fix"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "unite" and centers on problem solving.',
        f"Tell a spooky-but-safe story where {child1.id} and {child2.id} meet a lonely ghost in {place.label} and must repair {keepsake.phrase}.",
        f"Write a child-facing story in which two children think carefully, choose {fix.label}, and unite the pieces of a ghost's lost keepsake so the room feels peaceful again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child1 = f["child1"]
    child2 = f["child2"]
    ghost = f["ghost"]
    keepsake = f["keepsake_cfg"]
    fix = f["fix"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child1.id} and {child2.id}, who find a lonely ghost in {place.label}. The ghost is sad because {ghost.pronoun('possessive')} {keepsake.label} has come apart."
        ),
        (
            f"What problem did the ghost have?",
            f"The ghost's {keepsake.label} was in separate pieces and could not be enjoyed as it once was. That is why the room felt cold and unsettled."
        ),
        (
            f"How did {child1.id} and {child2.id} solve the problem?",
            f"They searched for the missing pieces, studied what was wrong, and chose the right repair. Then they {fix.qa_text}, which helped unite the keepsake and calm the ghost."
        ),
        (
            "Why did they stop to think before fixing it?",
            f"They knew a careful repair had to match the kind of object in front of them. Their problem solving mattered because the wrong fix would not have made the keepsake whole."
        ),
    ]
    if f.get("united"):
        qa.append(
            (
                "How did the story end?",
                f"The keepsake was whole again, and the ghost became peaceful instead of lonely. The room changed too, because it no longer felt scary after the children helped."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "repair"} | set(f["fix"].tags) | set(f["keepsake_cfg"].tags)
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
# Trace / CLI helpers
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.fragile:
            flags.append("fragile")
        if e.cloth:
            flags.append("cloth")
        if e.tieable:
            flags.append("tieable")
        if e.musical:
            flags.append("musical")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
keepsake_needs(K, N) :- keepsake(K), needs(K, N).
repair_possible(K, F) :- keepsake_needs(K, N), fix(F), works_for(F, N).
valid(K, F) :- repair_possible(K, F).

chosen_valid :- chosen_keepsake(K), chosen_fix(F), repair_possible(K, F).
outcome(peaceful) :- chosen_valid.
:- chosen_keepsake(_), chosen_fix(_), not chosen_valid.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("needs", kid, keepsake.needs))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for need in sorted(fix.works_for):
            lines.append(asp.fact("works_for", fid, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_keepsake", params.keepsake),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        py = "peaceful" if repair_possible(KEEPSAKES[params.keepsake], FIXES[params.fix]) else "?"
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost story world: problem solving helps children unite a ghost's keepsake."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (keepsake, fix) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.keepsake and args.fix:
        keepsake = KEEPSAKES[args.keepsake]
        fix = FIXES[args.fix]
        if not repair_possible(keepsake, fix):
            raise StoryError(explain_rejection(keepsake, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.keepsake is None or combo[0] == args.keepsake)
        and (args.fix is None or combo[1] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    keepsake_id, fix_id = rng.choice(sorted(combos))
    child1, child1_gender = _pick_kid(rng)
    child2, child2_gender = _pick_kid(rng, avoid=child1)
    place = args.place or rng.choice(sorted(PLACES))
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])
    pet = rng.choice(PETS)
    return StoryParams(
        place=place,
        keepsake=keepsake_id,
        fix=fix_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        adult=adult,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    place = PLACES[params.place]
    keepsake = KEEPSAKES[params.keepsake]
    fix = FIXES[params.fix]
    if not repair_possible(keepsake, fix):
        raise StoryError(explain_rejection(keepsake, fix))

    world = tell(
        place=place,
        keepsake=keepsake,
        fix=fix,
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        adult_type=params.adult,
        pet=params.pet,
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
        print(f"{len(combos)} compatible (keepsake, fix) combos:\n")
        for keepsake, fix in combos:
            print(f"  {keepsake:10} {fix}")
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
            header = f"### {p.child1} & {p.child2}: {p.keepsake} in {p.place} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
