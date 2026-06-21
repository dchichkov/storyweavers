#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/startle_slant_mystery_to_solve_suspense_friendship.py
================================================================================

A standalone story world for small child-facing mystery stories with suspense,
friendship, and a solvable surprise. Two friends hear a strange sound in a cozy
place, see a slant of light or shadow, feel a startle of fear, and then either
solve the mystery together or wisely fetch a grown-up for the last step.

Run it
------
    python storyworlds/worlds/gpt-5.4/startle_slant_mystery_to_solve_suspense_friendship.py
    python storyworlds/worlds/gpt-5.4/startle_slant_mystery_to_solve_suspense_friendship.py --place attic --mystery marble_tin
    python storyworlds/worlds/gpt-5.4/startle_slant_mystery_to_solve_suspense_friendship.py --place porch --mystery kitten_crate
    python storyworlds/worlds/gpt-5.4/startle_slant_mystery_to_solve_suspense_friendship.py --all --qa
    python storyworlds/worlds/gpt-5.4/startle_slant_mystery_to_solve_suspense_friendship.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
STEADY_TRAITS = {"steady", "brave", "patient", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    slant_text: str
    hiding_spots: str
    end_image: str
    has_window: bool = False
    has_storage: bool = False
    has_slant_surface: bool = False
    near_tree: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    noise: str
    first_hint: str
    reveal: str
    clue: str
    ending: str
    difficulty: int
    requires_window: bool = False
    requires_storage: bool = False
    requires_slant_surface: bool = False
    requires_tree: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        return [e for e in self.entities.values() if e.role in {"lead", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    source = world.entities.get("mystery")
    if source is None or source.meters["active"] < THRESHOLD:
        return []
    sig = ("fear", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    out: list[str] = []
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["curiosity"] += 1
    return out


def _r_friendship(world: World) -> list[str]:
    a = world.entities.get("lead")
    b = world.entities.get("friend")
    if a is None or b is None:
        return []
    if a.memes["comforted"] < THRESHOLD and b.memes["comforted"] < THRESHOLD:
        return []
    sig = ("friendship", "comfort")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    return []


RULES = [
    Rule(name="fear", apply=_r_fear),
    Rule(name="friendship", apply=_r_friendship),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def compatible(place: Place, mystery: Mystery) -> bool:
    if mystery.requires_window and not place.has_window:
        return False
    if mystery.requires_storage and not place.has_storage:
        return False
    if mystery.requires_slant_surface and not place.has_slant_surface:
        return False
    if mystery.requires_tree and not place.near_tree:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if compatible(place, mystery):
                combos.append((pid, mid))
    return combos


def support_score(trait1: str, trait2: str) -> int:
    score = 1
    if trait1 in STEADY_TRAITS:
        score += 1
    if trait2 in STEADY_TRAITS:
        score += 1
    return score


def outcome_of(params: "StoryParams") -> str:
    mystery = MYSTERIES[params.mystery]
    return "friends_solve" if support_score(params.trait1, params.trait2) >= mystery.difficulty else "adult_helps"


def predict_outcome(world: World, mystery: Mystery) -> str:
    a = world.get("lead")
    b = world.get("friend")
    score = support_score(a.traits[0], b.traits[0])
    return "friends_solve" if score >= mystery.difficulty else "adult_helps"


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After supper, {a.id} and {b.id} slipped into {place.label}, their favorite place for small secrets and quiet games."
    )
    world.say(place.opening)
    world.say(place.slant_text)


def mystery_stirs(world: World, mystery: Mystery) -> None:
    source = world.get("mystery")
    source.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {mystery.noise} sounded from the dim side of the room. It was enough to startle both friends, and they went still."
    )
    world.say(mystery.first_hint)


def comfort(world: World, a: Entity, b: Entity) -> None:
    a.memes["comforted"] += 1
    b.memes["comforted"] += 1
    propagate(world, narrate=False)
    if a.memes["fear"] >= THRESHOLD or b.memes["fear"] >= THRESHOLD:
        world.say(
            f'{b.id} found {a.id}\'s hand in the half-dark. "We do not have to be brave alone," {b.pronoun()} whispered.'
        )
    world.say(
        f"{a.id} took a breath and nodded. Standing close together made the mysterious sound feel smaller and the friendship between them feel bigger."
    )


def inspect(world: World, a: Entity, b: Entity, place: Place, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.memes["courage"] += 1
    world.say(
        f"They listened again, following the sound past {place.hiding_spots}. Each little step felt slow and suspenseful."
    )
    world.say(mystery.clue)


def solve_together(world: World, a: Entity, b: Entity, mystery: Mystery, place: Place) -> None:
    culprit = world.get("mystery")
    culprit.meters["active"] = 0.0
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["fear"] = 0.0
    world.say(mystery.reveal)
    world.say(
        f"{a.id} laughed first, and then {b.id} did too. The terrible mystery had turned into something ordinary the moment they solved it together."
    )
    world.say(
        f"In the end, {place.end_image} {mystery.ending}"
    )


def fetch_grownup(world: World, a: Entity, b: Entity, grownup: Entity, mystery: Mystery, place: Place) -> None:
    culprit = world.get("mystery")
    for kid in (a, b):
        kid.memes["wisdom"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'The sound came once more, and this time {a.id} whispered, "Let\'s ask {grownup.label_word}." Choosing help felt wiser than pretending not to be scared.'
    )
    world.say(
        f"{grownup.label_word.capitalize()} came with a warm flashlight and knelt beside them instead of rushing ahead."
    )
    culprit.meters["active"] = 0.0
    world.say(mystery.reveal)
    world.say(
        f'{grownup.label_word.capitalize()} smiled. "Good detectives know when to stay together and when to ask for help," {grownup.pronoun()} said.'
    )
    world.say(
        f"In the end, {place.end_image} {mystery.ending}"
    )


def tell(
    place: Place,
    mystery: Mystery,
    name1: str,
    gender1: str,
    trait1: str,
    name2: str,
    gender2: str,
    trait2: str,
    grownup_type: str,
) -> World:
    world = World(place)
    a = world.add(Entity(id="lead", kind="character", type=gender1, label=name1, role="lead", traits=[trait1]))
    b = world.add(Entity(id="friend", kind="character", type=gender2, label=name2, role="friend", traits=[trait2]))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up", role="grownup"))
    culprit = world.add(Entity(id="mystery", kind="thing", type="mystery", label=mystery.id, tags=set(mystery.tags)))

    introduce(world, a, b, place)
    world.para()
    mystery_stirs(world, mystery)
    comfort(world, a, b)
    world.para()
    inspect(world, a, b, place, mystery)

    outcome = predict_outcome(world, mystery)
    world.para()
    if outcome == "friends_solve":
        solve_together(world, a, b, mystery, place)
    else:
        fetch_grownup(world, a, b, grownup, mystery, place)

    world.facts.update(
        place=place,
        mystery_cfg=mystery,
        lead=a,
        friend=b,
        grownup=grownup,
        outcome=outcome,
        support=support_score(trait1, trait2),
        solved_by_friends=outcome == "friends_solve",
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic room above the hall",
        opening="Old trunks stood along the wall, and a folded quilt made a little island on the floorboards.",
        slant_text="A slant of evening light came through the round window and laid a golden stripe across the floor.",
        hiding_spots="old trunks and the quilt",
        end_image="the round window still held its slant of light, but now the room felt friendly instead of strange.",
        has_window=True,
        has_storage=True,
        has_slant_surface=True,
        near_tree=False,
        tags={"attic", "window"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        opening="Rakes slept against one wall, flowerpots were stacked in neat towers, and the wooden room smelled like soil and rain.",
        slant_text="A slant of pale light slipped through the dusty side window and made the shadows seem longer than they really were.",
        hiding_spots="flowerpots and seed boxes",
        end_image="the dusty window shone softly, and the shed no longer felt full of whispers.",
        has_window=True,
        has_storage=True,
        has_slant_surface=False,
        near_tree=True,
        tags={"shed", "window", "garden"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        opening="The swing hung still, boots waited by the door, and the steps looked down toward the dark garden.",
        slant_text="A slant of moonlight crossed the porch boards and turned every little shadow into a question.",
        hiding_spots="the boot basket and the swing",
        end_image="the porch boards gleamed under the moon, calm and ordinary again.",
        has_window=False,
        has_storage=False,
        has_slant_surface=False,
        near_tree=True,
        tags={"porch", "moonlight", "tree"},
    ),
}

MYSTERIES = {
    "kite_tail": Mystery(
        id="kite_tail",
        noise="a quick tap-tap-tap",
        first_hint="Something thin flicked across the window and vanished, as if a dark finger had rapped on the glass.",
        reveal="At the window they found the answer: a bright paper kite had blown into the tree, and its ribbon tail kept tapping the pane in the breeze.",
        clue="When they looked up, they saw the shadow move only when the wind breathed through the branches.",
        ending="They waved at the silly kite as if it had been a very polite ghost.",
        difficulty=1,
        requires_window=True,
        requires_tree=True,
        tags={"wind", "kite", "window"},
    ),
    "kitten_crate": Mystery(
        id="kitten_crate",
        noise="a tiny scratch-scratch and one soft thump",
        first_hint="From behind the stacked pots came a pair of bright eyes, then silence, then another worried little sound.",
        reveal="Behind the pots was a wooden crate with its lid tipped sideways. A gray kitten was inside, pawing at the slats until the crate bumped and scratched.",
        clue="The sound was low to the ground, and once they heard a small mew hidden inside it.",
        ending="Soon the kitten was purring between them, and the scary sound became the start of a new story to tell.",
        difficulty=2,
        requires_storage=True,
        tags={"kitten", "animal", "crate"},
    ),
    "marble_tin": Mystery(
        id="marble_tin",
        noise="a nervous click-clack from overhead",
        first_hint="A tiny shine flashed in the dimness, then came the sound again, as if a hard little thing were rolling where no one could see it.",
        reveal="On a shelf they found a tin with its lid half open. Each time the old board leaned, the marbles inside rolled to one side and clicked against the metal.",
        clue="The sound always came after the floor gave the smallest creak, which made the puzzle feel less like magic and more like a clue.",
        ending="They shut the lid, set the tin straight, and grinned at how a room can sound mysterious when it is only untidy.",
        difficulty=1,
        requires_storage=True,
        requires_slant_surface=True,
        tags={"marbles", "tin", "slant"},
    ),
    "acorn_roof": Mystery(
        id="acorn_roof",
        noise="a sudden plunk above their heads",
        first_hint="The roof gave one sharp knock, then another, and the leaves outside shivered in the dark.",
        reveal="They peeked out and discovered the truth at once: acorns were dropping from the old oak and bouncing over the porch roof before tumbling into the yard.",
        clue="Every knock came just after a branch shook, and that rhythm made the fright fade into a pattern they could understand.",
        ending="For a while they listened on purpose, counting the acorns as if the tree were tapping out a sleepy good-night song.",
        difficulty=1,
        requires_tree=True,
        tags={"acorn", "tree", "roof"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "June"]
BOY_NAMES = ["Max", "Ben", "Theo", "Sam", "Leo", "Finn", "Eli", "Jack"]
TRAITS = ["steady", "brave", "patient", "gentle", "curious", "jumpy", "careful", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name1: str
    gender1: str
    trait1: str
    name2: str
    gender2: str
    trait2: str
    grownup: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet. You look for clues until the answer makes sense."
        )
    ],
    "friendship": [
        (
            "How can a friend help when something feels scary?",
            "A friend can stay beside you, listen with you, and help you think clearly. Being together can make a scary moment feel smaller."
        )
    ],
    "window": [
        (
            "Why can shadows by a window look spooky at night?",
            "Light and movement can stretch a shadow and make it look bigger or stranger than it really is. When you look closely, the shape usually has an ordinary cause."
        )
    ],
    "wind": [
        (
            "How can wind make a tapping sound?",
            "Wind can push ribbons, branches, or other loose things against a wall or window. The tapping repeats each time the wind moves them."
        )
    ],
    "kitten": [
        (
            "Why might a kitten make scratching sounds?",
            "A kitten may scratch when it is stuck or trying to get out of a small space. The sound is a clue that the kitten needs help."
        )
    ],
    "marbles": [
        (
            "Why do marbles make noise when they roll?",
            "Marbles are hard and smooth, so they click when they bump into a tin or wooden floor. Even a small tilt can make them roll."
        )
    ],
    "tree": [
        (
            "Why do acorns fall from trees?",
            "Acorns grow on oak trees and fall when they are ready or when the wind shakes the branches. When they hit a roof or the ground, they can sound surprisingly loud."
        )
    ],
    "ask_help": [
        (
            "When should children ask a grown-up for help?",
            "Children should ask a grown-up when something feels too hard, too hidden, or too worrying to handle alone. Asking for help is a smart and safe choice."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "friendship", "window", "wind", "kitten", "marbles", "tree", "ask_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["lead"]
    b = f["friend"]
    place = f["place"]
    mystery = f["mystery_cfg"]
    outcome = f["outcome"]
    if outcome == "friends_solve":
        return [
            'Write a gentle mystery story for a 3-to-5-year-old that includes the words "startle" and "slant".',
            f"Tell a suspenseful but cozy story where two friends, {a.label} and {b.label}, hear {mystery.noise} in {place.label} and solve the mystery together.",
            "Write a friendship mystery where a scary sound turns out to have an ordinary answer once the children follow the clues."
        ]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old that includes the words "startle" and "slant".',
        f"Tell a suspenseful story where two friends hear {mystery.noise} in {place.label}, stay together, and wisely ask a grown-up for the last step.",
        "Write a child-facing mystery about friendship, clues, and knowing when asking for help is part of solving the puzzle."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["lead"]
    b = f["friend"]
    place = f["place"]
    mystery = f["mystery_cfg"]
    grownup = f["grownup"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.label} and {b.label}. They were together in {place.label} when the strange sound began."
        ),
        (
            "What made the story feel mysterious at first?",
            f"The mystery began with {mystery.noise} and a strange hint in the half-light. Those clues made the ordinary room feel full of suspense before the friends understood the cause."
        ),
        (
            "How did friendship help in the story?",
            f"{b.label} reached for {a.label}'s hand, and they stayed close instead of running away. Being together helped them keep looking for clues even after the sound gave them a startle."
        ),
    ]
    if f["outcome"] == "friends_solve":
        qa.append(
            (
                "How did they solve the mystery?",
                f"They listened carefully and followed the clues together until the answer made sense. {mystery.reveal} That changed the fear into relief because they could see the true cause with their own eyes."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly and safely. {mystery.ending} The last image shows that the place felt ordinary again once the mystery was understood."
            )
        )
    else:
        qa.append(
            (
                f"Why did {a.label} and {b.label} ask a grown-up for help?",
                f"The mystery felt a little too hard for them to finish alone, so they chose the safer idea and called {grownup.label_word}. Good detectives do not have to do every part by themselves."
            )
        )
        qa.append(
            (
                "How was the mystery solved in the end?",
                f"{grownup.label_word.capitalize()} came with them, and then the answer became clear. {mystery.reveal} The ending shows that asking for help was part of solving the mystery, not failing at it."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "friendship"}
    place = f["place"]
    mystery = f["mystery_cfg"]
    if place.has_window:
        tags.add("window")
    if "wind" in mystery.tags or "kite" in mystery.tags:
        tags.add("wind")
    if "kitten" in mystery.tags:
        tags.add("kitten")
    if "marbles" in mystery.tags:
        tags.add("marbles")
    if "tree" in mystery.tags or "acorn" in mystery.tags:
        tags.add("tree")
    if f["outcome"] == "adult_helps":
        tags.add("ask_help")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        mystery="marble_tin",
        name1="Lily",
        gender1="girl",
        trait1="curious",
        name2="Max",
        gender2="boy",
        trait2="steady",
        grownup="mother",
    ),
    StoryParams(
        place="shed",
        mystery="kitten_crate",
        name1="Nora",
        gender1="girl",
        trait1="gentle",
        name2="Ben",
        gender2="boy",
        trait2="patient",
        grownup="father",
    ),
    StoryParams(
        place="porch",
        mystery="acorn_roof",
        name1="Ella",
        gender1="girl",
        trait1="jumpy",
        name2="Theo",
        gender2="boy",
        trait2="brave",
        grownup="mother",
    ),
    StoryParams(
        place="shed",
        mystery="kitten_crate",
        name1="Ava",
        gender1="girl",
        trait1="curious",
        name2="Sam",
        gender2="boy",
        trait2="jumpy",
        grownup="father",
    ),
    StoryParams(
        place="attic",
        mystery="kite_tail",
        name1="Leo",
        gender1="boy",
        trait1="careful",
        name2="Ruby",
        gender2="girl",
        trait2="thoughtful",
        grownup="mother",
    ),
]


def explain_rejection(place: Place, mystery: Mystery) -> str:
    needs: list[str] = []
    if mystery.requires_window and not place.has_window:
        needs.append("a window")
    if mystery.requires_storage and not place.has_storage:
        needs.append("storage corners")
    if mystery.requires_slant_surface and not place.has_slant_surface:
        needs.append("a slanted shelf or floor")
    if mystery.requires_tree and not place.near_tree:
        needs.append("a nearby tree")
    need_text = ", ".join(needs)
    return (
        f"(No story: {mystery.id.replace('_', ' ')} does not fit {place.label}. "
        f"This mystery needs {need_text}, and that place does not provide it.)"
    )


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if not compatible(PLACES[params.place], MYSTERIES[params.mystery]):
        raise StoryError(explain_rejection(PLACES[params.place], MYSTERIES[params.mystery]))


ASP_RULES = r"""
compatible(P, M) :- place(P), mystery(M),
                    not need_window(M).
compatible(P, M) :- place(P), mystery(M),
                    need_window(M), has_window(P),
                    not need_storage(M), not need_slant_surface(M), not need_tree(M).
compatible(P, M) :- place(P), mystery(M),
                    need_storage(M), has_storage(P),
                    not need_window(M), not need_slant_surface(M), not need_tree(M).
compatible(P, M) :- place(P), mystery(M),
                    need_slant_surface(M), has_slant_surface(P),
                    not need_window(M), not need_storage(M), not need_tree(M).
compatible(P, M) :- place(P), mystery(M),
                    need_tree(M), near_tree(P),
                    not need_window(M), not need_storage(M), not need_slant_surface(M).
compatible(P, M) :- place(P), mystery(M),
                    need_window(M), has_window(P),
                    need_tree(M), near_tree(P),
                    not need_storage(M), not need_slant_surface(M).
compatible(P, M) :- place(P), mystery(M),
                    need_storage(M), has_storage(P),
                    need_slant_surface(M), has_slant_surface(P),
                    not need_window(M), not need_tree(M).
compatible(P, M) :- place(P), mystery(M),
                    need_window(M), has_window(P),
                    need_storage(M), has_storage(P),
                    not need_slant_surface(M), not need_tree(M).
compatible(P, M) :- place(P), mystery(M),
                    need_window(M), has_window(P),
                    need_storage(M), has_storage(P),
                    need_slant_surface(M), has_slant_surface(P),
                    not need_tree(M).

valid(P, M) :- compatible(P, M).

steady_pair :- trait1(T1), steady(T1).
steady_pair :- trait2(T2), steady(T2).
support(3) :- trait1(T1), steady(T1), trait2(T2), steady(T2).
support(2) :- steady_pair, not support(3).
support(1) :- not steady_pair.

friends_solve :- chosen_mystery(M), difficulty(M, D), support(S), S >= D.
adult_helps :- chosen_mystery(M), difficulty(M, D), support(S), S < D.
outcome(friends_solve) :- friends_solve.
outcome(adult_helps) :- adult_helps.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.has_window:
            lines.append(asp.fact("has_window", pid))
        if place.has_storage:
            lines.append(asp.fact("has_storage", pid))
        if place.has_slant_surface:
            lines.append(asp.fact("has_slant_surface", pid))
        if place.near_tree:
            lines.append(asp.fact("near_tree", pid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("difficulty", mid, mystery.difficulty))
        if mystery.requires_window:
            lines.append(asp.fact("need_window", mid))
        if mystery.requires_storage:
            lines.append(asp.fact("need_storage", mid))
        if mystery.requires_slant_surface:
            lines.append(asp.fact("need_slant_surface", mid))
        if mystery.requires_tree:
            lines.append(asp.fact("need_tree", mid))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_mystery", params.mystery),
            asp.fact("trait1", params.trait1),
            asp.fact("trait2", params.trait2),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed during verify on seed {seed}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle mystery, a startle of suspense, and friendship that helps solve it."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, mystery) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        place = PLACES[args.place]
        mystery = MYSTERIES[args.mystery]
        if not compatible(place, mystery):
            raise StoryError(explain_rejection(place, mystery))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mystery is None or combo[1] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mystery_id = rng.choice(sorted(combos))
    gender1 = rng.choice(["girl", "boy"])
    gender2 = rng.choice(["girl", "boy"])
    name1 = pick_name(rng, gender1)
    name2 = pick_name(rng, gender2, avoid=name1)
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice(TRAITS)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        mystery=mystery_id,
        name1=name1,
        gender1=gender1,
        trait1=trait1,
        name2=name2,
        gender2=gender2,
        trait2=trait2,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        place=PLACES[params.place],
        mystery=MYSTERIES[params.mystery],
        name1=params.name1,
        gender1=params.gender1,
        trait1=params.trait1,
        name2=params.name2,
        gender2=params.gender2,
        trait2=params.trait2,
        grownup_type=params.grownup,
    )
    story = world.render().replace("lead", params.name1).replace("friend", params.name2)
    story = story.replace("grownup", {"mother": "mom", "father": "dad"}[params.grownup])
    story = story.replace(" lead ", f" {params.name1} ")
    story = story.replace(" friend ", f" {params.name2} ")
    story = story.replace("Lead", params.name1).replace("Friend", params.name2)

    # Rendered prose should use visible names, not internal ids.
    story = story.replace("lead's", f"{params.name1}'s").replace("friend's", f"{params.name2}'s")
    story = story.replace("lead", params.name1).replace("friend", params.name2)

    # Q&A uses world state directly, with visible labels from facts.
    world.facts["lead"].label = params.name1
    world.facts["friend"].label = params.name2

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:8} {mystery}")
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
            header = f"### {p.name1} and {p.name2}: {p.mystery} in {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
