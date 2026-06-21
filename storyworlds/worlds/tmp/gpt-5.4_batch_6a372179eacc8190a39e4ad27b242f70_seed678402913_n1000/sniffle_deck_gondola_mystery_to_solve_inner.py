#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sniffle_deck_gondola_mystery_to_solve_inner.py
==========================================================================

A small storyworld about a funny little mystery at a mountain station:
a child hears a strange sniffle on the deck beside a gondola platform,
follows physical clues, thinks dramatically in private, and discovers that
the "mystery" is really a chilly creature that needs a sensible kind of help.

The world model keeps one foot in comedy and one foot in causality:

- typed entities with physical meters and emotional memes
- a clue-following mystery shape
- inner-monologue narration driven by state
- a Python reasonableness gate plus an inline ASP twin
- a simple outcome model: some mysteries are easy enough to solve alone,
  while trickier ones prompt the child to ask for help

Run it
------
    python storyworlds/worlds/gpt-5.4/sniffle_deck_gondola_mystery_to_solve_inner.py
    python storyworlds/worlds/gpt-5.4/sniffle_deck_gondola_mystery_to_solve_inner.py --culprit puppy --spot gondola_seat
    python storyworlds/worlds/gpt-5.4/sniffle_deck_gondola_mystery_to_solve_inner.py --culprit goat --remedy tissue
    python storyworlds/worlds/gpt-5.4/sniffle_deck_gondola_mystery_to_solve_inner.py --all
    python storyworlds/worlds/gpt-5.4/sniffle_deck_gondola_mystery_to_solve_inner.py --qa --json
    python storyworlds/worlds/gpt-5.4/sniffle_deck_gondola_mystery_to_solve_inner.py --verify
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
COURAGE_INIT = 2


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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    deck_phrase: str
    gondola_phrase: str
    air: str
    allows_spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    sniffle: str
    clue: str
    clue_phrase: str
    hiding_style: str
    need: str
    reveal: str
    comedy: str
    difficulty: int
    allows_spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    search_text: str
    reveal_text: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    use_text: str
    good_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_cold_sniffle(world: World) -> list[str]:
    culprit = world.entities.get("culprit")
    if culprit is None:
        return []
    if culprit.meters["cold"] < THRESHOLD:
        return []
    sig = ("sniffle", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.meters["audible_sniffle"] += 1
    return ["__sniffle__"]


def _r_clue_idea(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None:
        return []
    if child.meters["clues_found"] < THRESHOLD:
        return []
    sig = ("idea", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["suspicion"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="cold_sniffle", tag="physical", apply=_r_cold_sniffle),
    Rule(name="clue_idea", tag="mystery", apply=_r_clue_idea),
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
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


PLACES = {
    "peak_station": Place(
        id="peak_station",
        label="the snowy peak station",
        deck_phrase="the wooden deck above the snow",
        gondola_phrase="the red gondola station",
        air="The air smelled like pine and cold metal.",
        allows_spots={"bench", "gondola_seat", "crate"},
        tags={"mountain", "gondola", "deck"},
    ),
    "lake_station": Place(
        id="lake_station",
        label="the windy lake station",
        deck_phrase="the long deck above the shining water",
        gondola_phrase="the blue gondola station",
        air="The air smelled like wet rope and cold wind.",
        allows_spots={"bench", "gondola_seat"},
        tags={"lake", "gondola", "deck"},
    ),
    "hill_fair": Place(
        id="hill_fair",
        label="the hill fair station",
        deck_phrase="the painted deck beside the ticket booth",
        gondola_phrase="the yellow gondola stop",
        air="The air smelled like popcorn trying to be brave in the cold.",
        allows_spots={"bench", "gondola_seat", "crate"},
        tags={"fair", "gondola", "deck"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        phrase="a fluffy little puppy",
        sniffle="small wet snuffles",
        clue="pawprint",
        clue_phrase="tiny pawprints in the frost",
        hiding_style="curled into a round furry comma",
        need="blanket",
        reveal="The mystery turned out to be a shivering puppy with a red tag.",
        comedy="The puppy looked as if it had accidentally become its own mustache.",
        difficulty=1,
        allows_spots={"bench", "gondola_seat", "crate"},
        tags={"animal", "blanket", "puppy"},
    ),
    "goat": Culprit(
        id="goat",
        label="baby goat",
        phrase="a woolly baby goat",
        sniffle="sniffles that sounded like a toy trumpet trying not to wake anyone",
        clue="wool",
        clue_phrase="a puff of white wool caught on a nail",
        hiding_style="tucked up with its knees folded under it",
        need="scarf",
        reveal="The mystery was a baby goat whose beard was dusted with snow.",
        comedy="It blinked with the serious face of someone who had misplaced an invisible sandwich.",
        difficulty=2,
        allows_spots={"bench", "crate"},
        tags={"animal", "scarf", "goat"},
    ),
    "mime": Culprit(
        id="mime",
        label="young mime",
        phrase="a young mime from the fair show",
        sniffle="one dramatic sniffle after another",
        clue="glitter",
        clue_phrase="a little silver glitter on the boards",
        hiding_style="trying very hard to hide while still being visible in three directions",
        need="tissue",
        reveal="The mystery was a young mime with a white-painted nose and very watery eyes.",
        comedy="Even the sniffle looked theatrical, as if it deserved its own applause.",
        difficulty=3,
        allows_spots={"gondola_seat", "crate"},
        tags={"person", "tissue", "mime"},
    ),
}

SPOTS = {
    "bench": Spot(
        id="bench",
        label="bench",
        phrase="under the long bench on the deck",
        search_text="The clue trail slipped under the long bench at the edge of the deck.",
        reveal_text="There, in the shadow under the bench, something blinked.",
        difficulty=1,
        tags={"bench", "deck"},
    ),
    "gondola_seat": Spot(
        id="gondola_seat",
        label="gondola",
        phrase="inside an empty gondola car",
        search_text="The clue trail led to an empty gondola rocking gently at the platform.",
        reveal_text="Behind the seat, something gave a shy little rustle.",
        difficulty=2,
        tags={"gondola"},
    ),
    "crate": Spot(
        id="crate",
        label="supply crate",
        phrase="behind a stack of cocoa crates",
        search_text="The clue trail dodged behind a stack of cocoa crates beside the rail.",
        reveal_text="From behind the crates came another very embarrassed sniffle.",
        difficulty=2,
        tags={"crate", "cocoa"},
    ),
}

REMEDIES = {
    "blanket": Remedy(
        id="blanket",
        label="blanket",
        phrase="a striped lap blanket",
        use_text="wrapped the little mystery in the warm blanket",
        good_for={"blanket"},
        tags={"blanket", "warmth"},
    ),
    "scarf": Remedy(
        id="scarf",
        label="scarf",
        phrase="a soft green scarf",
        use_text="looped the soft scarf gently around the chilly neck",
        good_for={"scarf"},
        tags={"scarf", "warmth"},
    ),
    "tissue": Remedy(
        id="tissue",
        label="tissue",
        phrase="a crinkly clean tissue",
        use_text="offered the clean tissue with very serious detective manners",
        good_for={"tissue"},
        tags={"tissue", "kindness"},
    ),
}

HELPERS = {
    "grandfather": {"type": "grandfather", "title": "Grandpa", "style": "grandpa"},
    "mother": {"type": "mother", "title": "Mom", "style": "mom"},
    "friend": {"type": "girl", "title": "friend", "style": "friend"},
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "dramatic", "cheerful", "nosy", "thoughtful", "brave"]


@dataclass
class StoryParams:
    place: str
    culprit: str
    spot: str
    remedy: str
    child_name: str
    child_gender: str
    helper: str
    trait: str
    courage: int
    seed: Optional[int] = None


def culprit_fits(culprit: Culprit, spot: Spot, place: Place) -> bool:
    return spot.id in culprit.allows_spots and spot.id in place.allows_spots


def remedy_fits(culprit: Culprit, remedy: Remedy) -> bool:
    return culprit.need in remedy.good_for


def mystery_difficulty(culprit: Culprit, spot: Spot) -> int:
    return max(culprit.difficulty, spot.difficulty)


def needs_helper(courage: int, culprit: Culprit, spot: Spot) -> bool:
    return mystery_difficulty(culprit, spot) > courage


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for culprit_id, culprit in CULPRITS.items():
            for spot_id, spot in SPOTS.items():
                if not culprit_fits(culprit, spot, place):
                    continue
                for remedy_id, remedy in REMEDIES.items():
                    if remedy_fits(culprit, remedy):
                        combos.append((place_id, culprit_id, spot_id, remedy_id))
    return combos


def explain_rejection(place: Place, culprit: Culprit, spot: Spot, remedy: Remedy) -> str:
    if not culprit_fits(culprit, spot, place):
        return (
            f"(No story: {culprit.phrase} does not fit plausibly at {spot.phrase} in "
            f"{place.label}. The mystery needs a hiding place the culprit could really use.)"
        )
    if not remedy_fits(culprit, remedy):
        return (
            f"(No story: {remedy.phrase} would not sensibly help {culprit.phrase}. "
            f"This culprit needs {culprit.need}, so the fix would feel fake.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


def outcome_of(params: StoryParams) -> str:
    culprit = CULPRITS[params.culprit]
    spot = SPOTS[params.spot]
    return "helper" if needs_helper(params.courage, culprit, spot) else "solo"


def inner_line(child: Entity, text: str) -> str:
    return f'{child.id} thought, "{text}"'


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"{child.id} stood on {place.deck_phrase} beside {place.gondola_phrase} with "
        f"{helper.label_word}. {place.air}"
    )
    world.say(
        f"{child.pronoun().capitalize()} had come for the ride, the view, and maybe a hot chocolate "
        f"with too many marshmallows and no regrets."
    )


def hear_sniffle(world: World, child: Entity, culprit: Entity) -> None:
    culprit.meters["cold"] += 1
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a strange sniffle floated across the boards. It was not a loud sniffle. "
        f"It was exactly the kind of sniffle that makes a person's ears lean forward."
    )
    world.say(inner_line(child, "A sniffle? On a deck? Either a mystery is here, or a nose is having a hard day."))


def inspect_clue(world: World, child: Entity, culprit_cfg: Culprit) -> None:
    child.meters["clues_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} knelt and found {culprit_cfg.clue_phrase}."
    )
    world.say(
        inner_line(
            child,
            f"Interesting. I have discovered evidence. I always hoped to say that before lunch."
        )
    )


def decide_search(world: World, child: Entity, spot: Spot) -> None:
    world.say(
        f"{spot.search_text}"
    )
    if child.memes["suspicion"] >= THRESHOLD:
        world.say(
            inner_line(
                child,
                f"If I follow this clue trail and it turns out to be a snow monster, I will be polite first and scream second."
            )
        )


def ask_for_help(world: World, child: Entity, helper: Entity, outcome: str) -> None:
    if outcome != "helper":
        return
    child.memes["prudence"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{child.id} took one brave breath, then another slightly wobblier one, and tugged at "
        f"{helper.label_word}'s sleeve."
    )
    world.say(
        f'"I am still a detective," {child.id} whispered, "but I would like a detective assistant who can reach high latches."'
    )


def search(world: World, child: Entity, helper: Entity, spot: Spot, outcome: str) -> None:
    if outcome == "helper":
        world.say(
            f"{helper.label_word.capitalize()} came along, smiling the calm smile grown-ups use when a mystery is probably small but important anyway."
        )
        world.say(
            f"Together they peered toward {spot.phrase}. {spot.reveal_text}"
        )
    else:
        child.memes["pride"] += 1
        world.say(
            f"{child.id} tiptoed toward {spot.phrase} all alone. {spot.reveal_text}"
        )


def reveal(world: World, child: Entity, culprit_cfg: Culprit) -> None:
    culprit = world.get("culprit")
    culprit.memes["relief"] += 1
    world.say(culprit_cfg.reveal)
    world.say(
        f"It was {culprit_cfg.hiding_style}, making {culprit_cfg.sniffle}. {culprit_cfg.comedy}"
    )
    world.say(
        inner_line(
            child,
            "Oh. Not a monster. Just a small citizen with a problem. That is much better for everybody's schedule."
        )
    )


def comfort(world: World, child: Entity, helper: Entity, remedy: Remedy, culprit_cfg: Culprit, outcome: str) -> None:
    culprit = world.get("culprit")
    child.memes["kindness"] += 1
    child.memes["relief"] += 1
    culprit.meters["cold"] = 0.0
    culprit.meters["audible_sniffle"] = 0.0
    culprit.memes["comfort"] += 1
    if outcome == "helper":
        world.say(
            f"With {helper.label_word}'s help, {child.id} {remedy.use_text}."
        )
    else:
        world.say(
            f"Very carefully, {child.id} {remedy.use_text}."
        )
    world.say(
        f"The sniffle stopped sounding lonely and started sounding sleepy."
    )


def finish(world: World, child: Entity, helper: Entity, place: Place, culprit_cfg: Culprit, spot: Spot, outcome: str) -> None:
    culprit = world.get("culprit")
    if culprit_cfg.id == "puppy":
        end_image = "Soon the puppy was sitting like a tiny captain, wrapped up and staring at the gondola as if it planned to drive."
    elif culprit_cfg.id == "goat":
        end_image = "Soon the baby goat gave one proud little hop, as if the whole mystery had been arranged to improve its scarf."
    else:
        end_image = "Soon the young mime dabbed at its nose, bowed to the deck, and somehow made gratitude look like a silent parade."
    world.say(
        f"{helper.label_word.capitalize()} checked the tag, the fair pass, or the station note nearby, and soon the right grown-up came hurrying over."
    )
    if outcome == "helper":
        world.say(
            f"{child.id} stood a little taller. Asking for help had not ended the mystery. It had solved it."
        )
    else:
        world.say(
            f"{child.id} grinned so hard that even the cold air seemed warmer around {child.pronoun('object')}."
        )
    world.say(
        f"{end_image} Behind them, the gondola doors opened with a cheerful clunk, and {place.deck_phrase} no longer felt mysterious at all."
    )
    world.facts["ending_image"] = end_image
    world.facts["culprit_entity"] = culprit
    world.facts["found_at"] = spot.phrase


def tell(
    place: Place,
    culprit_cfg: Culprit,
    spot: Spot,
    remedy: Remedy,
    child_name: str,
    child_gender: str,
    helper_key: str,
    trait: str,
    courage: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"trait": trait, "courage": courage},
            tags={"child"},
        )
    )
    helper_info = HELPERS[helper_key]
    helper_name = helper_info["title"] if helper_key != "friend" else random.choice([n for n in GIRL_NAMES if n != child_name] + [n for n in BOY_NAMES if n != child_name])
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_info["type"],
            label=helper_name,
            role="helper",
            attrs={"style": helper_info["style"]},
            tags={"helper"},
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character",
            type="creature" if culprit_cfg.id != "mime" else "person",
            label=culprit_cfg.label,
            phrase=culprit_cfg.phrase,
            role="culprit",
            tags=set(culprit_cfg.tags),
        )
    )

    outcome = "helper" if needs_helper(courage, culprit_cfg, spot) else "solo"

    introduce(world, child, helper, place)
    hear_sniffle(world, child, culprit)
    inspect_clue(world, child, culprit_cfg)

    world.para()
    decide_search(world, child, spot)
    ask_for_help(world, child, helper, outcome)
    search(world, child, helper, spot, outcome)

    world.para()
    reveal(world, child, culprit_cfg)
    comfort(world, child, helper, remedy, culprit_cfg, outcome)
    finish(world, child, helper, place, culprit_cfg, spot, outcome)

    world.facts.update(
        place=place,
        culprit_cfg=culprit_cfg,
        spot=spot,
        remedy=remedy,
        child=child,
        helper=helper,
        outcome=outcome,
        clue=culprit_cfg.clue_phrase,
        need=culprit_cfg.need,
        mystery_difficulty=mystery_difficulty(culprit_cfg, spot),
        courage=courage,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    culprit = f["culprit_cfg"]
    place = f["place"]
    spot = f["spot"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    helper_phrase = "asks for help to solve it" if outcome == "helper" else "solves it alone"
    return [
        'Write a funny mystery story for a 3-to-5-year-old that includes the words "sniffle", "deck", and "gondola".',
        f"Tell a comedy about a child named {child.id} who hears a sniffle on a deck beside a gondola and follows clues to {spot.phrase}.",
        f"Write a story with clear inner monologue where the mystery turns out to be {culprit.phrase}, and the child {helper_phrase} by using {remedy.phrase}.",
        f"Set the story at {place.label} and keep the ending gentle, concrete, and funny.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    culprit = f["culprit_cfg"]
    place = f["place"]
    spot = f["spot"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who heard a strange sniffle at {place.label}, and the hidden {culprit.label} that needed help. The mystery matters because {child.id} chooses to investigate instead of just walking away.",
        ),
        (
            "What made the mystery begin?",
            f"The mystery began when {child.id} heard a sniffle on the deck beside the gondola platform. That odd sound made {child.pronoun('object')} curious and worried, so {child.pronoun()} started looking for clues.",
        ),
        (
            f"What clue did {child.id} find?",
            f"{child.id} found {culprit.clue_phrase}. The clue pointed toward {spot.phrase}, which is why {child.pronoun()} decided where to search next.",
        ),
        (
            f"What was the mystery really about?",
            f"It was not a monster at all. The mystery was really about {culprit.phrase} hiding at {spot.phrase} because it was cold and uncomfortable.",
        ),
        (
            f"How was the problem solved?",
            f"{child.id} solved the problem by finding the hidden {culprit.label} and using {remedy.phrase}. {remedy.phrase.capitalize()} made sense because this culprit needed {culprit.need}, not just guessing or giggling.",
        ),
    ]
    if outcome == "helper":
        qa.append(
            (
                f"Why did {child.id} ask {helper.label_word} for help?",
                f"{child.id} asked for help because the hiding place was trickier than {child.pronoun()} felt ready for alone. The mystery was harder than {child.pronoun('possessive')} courage level, so asking a grown-up or friend was part of solving it wisely.",
            )
        )
    else:
        qa.append(
            (
                f"Why could {child.id} solve the mystery alone?",
                f"{child.id} could solve it alone because the hiding place was simple enough to search safely. {child.pronoun().capitalize()} still moved carefully, but the clues were easy to follow and the problem stayed small.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the mystery gone, the hidden {culprit.label} comforted, and the deck feeling cheerful again. The final image shows that what first sounded spooky became funny and kind once someone paid attention.",
        )
    )
    return qa


KNOWLEDGE = {
    "gondola": [
        (
            "What is a gondola?",
            "A gondola is a small cabin that hangs from a cable and carries people up or across a place. It glides through the air instead of driving on the ground.",
        )
    ],
    "deck": [
        (
            "What is a deck?",
            "A deck is a flat platform made of boards, often outside a building. People can stand or walk on it.",
        )
    ],
    "sniffle": [
        (
            "What is a sniffle?",
            "A sniffle is the sound someone makes when their nose is runny or stuffy. It can be small and quiet or easy to hear.",
        )
    ],
    "blanket": [
        (
            "What does a blanket do?",
            "A blanket helps keep a body warm by trapping heat. Warmth can help when someone is chilly.",
        )
    ],
    "scarf": [
        (
            "What is a scarf for?",
            "A scarf wraps around your neck to help keep you warm. It is useful on cold and windy days.",
        )
    ],
    "tissue": [
        (
            "What is a tissue for?",
            "A tissue is soft paper used to wipe or blow your nose. It helps when someone is sniffling.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small piece of information that helps you figure something out. Detectives look for clues when they solve mysteries.",
        )
    ],
    "help": [
        (
            "Why is it good to ask for help sometimes?",
            "Asking for help is smart when a problem is tricky or hard to reach. You can still be brave while getting help from someone you trust.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sniffle", "deck", "gondola", "clue", "blanket", "scarf", "tissue", "help"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sniffle", "deck", "gondola", "clue"}
    tags |= set(f["remedy"].tags)
    if f["outcome"] == "helper":
        tags.add("help")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="peak_station",
        culprit="puppy",
        spot="gondola_seat",
        remedy="blanket",
        child_name="Lily",
        child_gender="girl",
        helper="grandfather",
        trait="curious",
        courage=2,
    ),
    StoryParams(
        place="hill_fair",
        culprit="mime",
        spot="crate",
        remedy="tissue",
        child_name="Ben",
        child_gender="boy",
        helper="mother",
        trait="dramatic",
        courage=1,
    ),
    StoryParams(
        place="peak_station",
        culprit="goat",
        spot="bench",
        remedy="scarf",
        child_name="Maya",
        child_gender="girl",
        helper="friend",
        trait="thoughtful",
        courage=3,
    ),
    StoryParams(
        place="lake_station",
        culprit="puppy",
        spot="bench",
        remedy="blanket",
        child_name="Theo",
        child_gender="boy",
        helper="mother",
        trait="cheerful",
        courage=2,
    ),
]


ASP_RULES = r"""
fits(C, S, P) :- culprit(C), spot(S), place(P), culprit_allows(C, S), place_allows(P, S).
good_fix(C, R) :- culprit(C), remedy(R), needs(C, N), helps(R, N).
valid(P, C, S, R) :- fits(C, S, P), good_fix(C, R).

difficulty(C, S, D) :- culprit_diff(C, DC), spot_diff(S, DS), DC >= DS, D = DC.
difficulty(C, S, D) :- culprit_diff(C, DC), spot_diff(S, DS), DS > DC, D = DS.

needs_helper :- chosen_culprit(C), chosen_spot(S), courage(K), difficulty(C, S, D), D > K.
outcome(helper) :- needs_helper.
outcome(solo) :- not needs_helper.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for spot_id in sorted(place.allows_spots):
            lines.append(asp.fact("place_allows", place_id, spot_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_diff", culprit_id, culprit.difficulty))
        lines.append(asp.fact("needs", culprit_id, culprit.need))
        for spot_id in sorted(culprit.allows_spots):
            lines.append(asp.fact("culprit_allows", culprit_id, spot_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("spot_diff", spot_id, spot.difficulty))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for need in sorted(remedy.good_for):
            lines.append(asp.fact("helps", remedy_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_spot", params.spot),
            asp.fact("courage", params.courage),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke story was empty")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny sniffle mystery on a deck by a gondola."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--courage", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_place = PLACES[args.place] if args.place else None
    explicit_culprit = CULPRITS[args.culprit] if args.culprit else None
    explicit_spot = SPOTS[args.spot] if args.spot else None
    explicit_remedy = REMEDIES[args.remedy] if args.remedy else None

    if explicit_place and explicit_culprit and explicit_spot and explicit_remedy:
        if not culprit_fits(explicit_culprit, explicit_spot, explicit_place) or not remedy_fits(explicit_culprit, explicit_remedy):
            raise StoryError(explain_rejection(explicit_place, explicit_culprit, explicit_spot, explicit_remedy))

    if explicit_place and explicit_culprit and explicit_spot and not culprit_fits(explicit_culprit, explicit_spot, explicit_place):
        remedy = explicit_remedy or next(iter(REMEDIES.values()))
        raise StoryError(explain_rejection(explicit_place, explicit_culprit, explicit_spot, remedy))

    if explicit_culprit and explicit_remedy and not remedy_fits(explicit_culprit, explicit_remedy):
        place = explicit_place or next(iter(PLACES.values()))
        spot_id = next(iter(explicit_culprit.allows_spots))
        spot = SPOTS[spot_id]
        raise StoryError(explain_rejection(place, explicit_culprit, spot, explicit_remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.spot is None or combo[2] == args.spot)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, culprit_id, spot_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        child_name = args.name
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
        child_name = rng.choice(pool)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    courage = args.courage if args.courage is not None else rng.choice([1, 2, 3])

    return StoryParams(
        place=place_id,
        culprit=culprit_id,
        spot=spot_id,
        remedy=remedy_id,
        child_name=child_name,
        child_gender=gender,
        helper=helper,
        trait=trait,
        courage=courage,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Invalid culprit: {params.culprit})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Invalid remedy: {params.remedy})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid gender: {params.child_gender})")

    place = PLACES[params.place]
    culprit = CULPRITS[params.culprit]
    spot = SPOTS[params.spot]
    remedy = REMEDIES[params.remedy]

    if not culprit_fits(culprit, spot, place) or not remedy_fits(culprit, remedy):
        raise StoryError(explain_rejection(place, culprit, spot, remedy))

    world = tell(
        place=place,
        culprit_cfg=culprit,
        spot=spot,
        remedy=remedy,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_key=params.helper,
        trait=params.trait,
        courage=params.courage,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, culprit, spot, remedy) combos:\n")
        for place, culprit, spot, remedy in combos:
            print(f"  {place:12} {culprit:8} {spot:12} {remedy}")
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
                f"### {p.child_name}: {p.culprit} at {p.spot} "
                f"({p.place}, {p.remedy}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
