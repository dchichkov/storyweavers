#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pare_pixie_entry_kindness_lesson_learned_misunderstanding.py
=========================================================================================

A small storyworld for a child-sized detective story about a missing snack, a
pixie misunderstanding, and a kindness that turns the mystery into a lesson.

Seed words and features
-----------------------
Words: pare, pixie, entry
Features: Kindness, Lesson Learned, Misunderstanding
Style: Detective Story

Premise
-------
A grown-up pares fruit for a snack. Some slices go missing near an entryway. A
child detective notices a tiny clue and imagines a pixie thief. The real answer
is kinder: another child quietly shared the fruit with someone who needed help.
The detective learns to ask before blaming.

This script follows the Storyworld contract:
- one standalone stdlib file
- shared QAItem / StoryError / StorySample imports from results.py
- typed entities with physical meters and emotional memes
- state-driven prose
- a Python reasonableness gate plus an inline ASP twin
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
# from inside storyworlds/worlds/gpt-5.4/.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
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
    entry_phrase: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    pare_text: str
    slices_word: str
    softness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Receiver:
    id: str
    label: str
    phrase: str
    need: str
    location_text: str
    kindness_text: str
    reveal_text: str
    requires_soft: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    places: set[str] = field(default_factory=set)
    magic_like: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_pixie_suspicion(world: World) -> list[str]:
    plate = world.entities.get("plate")
    clue_ent = world.entities.get("clue")
    hero = world.entities.get("hero")
    if not plate or not clue_ent or not hero:
        return []
    if plate.meters["missing"] < THRESHOLD or clue_ent.meters["noticed"] < THRESHOLD:
        return []
    sig = ("pixie_suspicion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts.get("clue_magic_like", 0) >= 1:
        hero.memes["suspicion"] += 1
    else:
        hero.memes["curiosity"] += 1
    return []


def _r_kindness_relief(world: World) -> list[str]:
    receiver = world.entities.get("receiver")
    helper = world.entities.get("helper")
    if not receiver or not helper:
        return []
    if receiver.meters["helped"] < THRESHOLD:
        return []
    sig = ("kindness_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    receiver.memes["relief"] += 1
    helper.memes["kindness"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="pixie_suspicion", tag="meme", apply=_r_pixie_suspicion),
    Rule(name="kindness_relief", tag="meme", apply=_r_kindness_relief),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "garden_entry": Place(
        id="garden_entry",
        label="the garden entry",
        entry_phrase="the garden entry by the back door",
        supports={"robin", "grandma"},
        tags={"entry", "garden"},
    ),
    "front_entry": Place(
        id="front_entry",
        label="the front entry",
        entry_phrase="the front entry with the umbrella stand",
        supports={"new_kid", "grandma"},
        tags={"entry", "hall"},
    ),
    "side_entry": Place(
        id="side_entry",
        label="the side entry",
        entry_phrase="the side entry beside the coat hooks",
        supports={"robin", "new_kid"},
        tags={"entry", "hall"},
    ),
}

FRUITS = {
    "pear": Fruit(
        id="pear",
        label="pear",
        phrase="a ripe pear",
        pare_text="began to pare a pear into neat moon-shaped slices",
        slices_word="pear slices",
        softness=3,
        tags={"pear", "fruit", "pare"},
    ),
    "apple": Fruit(
        id="apple",
        label="apple",
        phrase="a bright apple",
        pare_text="used a small knife to pare the peel from an apple and cut it into tidy slices",
        slices_word="apple slices",
        softness=2,
        tags={"apple", "fruit", "pare"},
    ),
    "peach": Fruit(
        id="peach",
        label="peach",
        phrase="a soft peach",
        pare_text="carefully pared a peach and set down its sweet little slices",
        slices_word="peach slices",
        softness=3,
        tags={"peach", "fruit", "pare"},
    ),
}

RECEIVERS = {
    "robin": Receiver(
        id="robin",
        label="robin",
        phrase="a small robin",
        need="hungry",
        location_text="on the mat by the door, head tilted as if asking for help",
        kindness_text="thought the robin looked hungry and carried over two tiny slices",
        reveal_text="The robin pecked the fruit with quick grateful taps.",
        requires_soft=False,
        tags={"bird", "kindness"},
    ),
    "new_kid": Receiver(
        id="new_kid",
        label="new child",
        phrase="the new child from next door",
        need="shy",
        location_text="just inside the doorway, holding a backpack strap with both hands",
        kindness_text="saw the new child looking shy at the entry and offered a few slices first",
        reveal_text="The new child smiled around a bite and stopped twisting the backpack strap.",
        requires_soft=False,
        tags={"neighbor", "kindness"},
    ),
    "grandma": Receiver(
        id="grandma",
        label="grandma",
        phrase="Grandma in the hallway chair",
        need="tired",
        location_text="resting in the hallway chair with a blanket over her knees",
        kindness_text="noticed Grandma looked tired and brought her the softest slices",
        reveal_text="Grandma's tired face softened into a warm, thankful smile.",
        requires_soft=True,
        tags={"family", "kindness"},
    ),
}

CLUES = {
    "glitter": Clue(
        id="glitter",
        label="glitter specks",
        detail="three tiny glitter specks shone beside the baseboard",
        places={"front_entry", "side_entry", "garden_entry"},
        magic_like=2,
        tags={"glitter", "pixie"},
    ),
    "petal": Clue(
        id="petal",
        label="flower petal",
        detail="a curled flower petal rested near the threshold",
        places={"garden_entry", "side_entry"},
        magic_like=1,
        tags={"flower", "pixie"},
    ),
    "silver_thread": Clue(
        id="silver_thread",
        label="silver thread",
        detail="a silver thread clung to the umbrella stand like a tiny ribbon trail",
        places={"front_entry", "side_entry"},
        magic_like=1,
        tags={"thread", "pixie"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ruby", "Ivy", "Lucy", "Anna"]
BOY_NAMES = ["Theo", "Ben", "Max", "Finn", "Leo", "Sam", "Eli", "Noah"]
TRAITS = ["careful", "curious", "steady", "thoughtful", "clever", "bright"]


def receiver_ok_for_fruit(receiver: Receiver, fruit: Fruit) -> bool:
    return (not receiver.requires_soft) or fruit.softness >= 3


def valid_combo(place_id: str, fruit_id: str, receiver_id: str, clue_id: str) -> bool:
    place = PLACES[place_id]
    fruit = FRUITS[fruit_id]
    receiver = RECEIVERS[receiver_id]
    clue = CLUES[clue_id]
    return (
        receiver_id in place.supports
        and place_id in clue.places
        and receiver_ok_for_fruit(receiver, fruit)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for fruit_id in sorted(FRUITS):
            for receiver_id in sorted(RECEIVERS):
                for clue_id in sorted(CLUES):
                    if valid_combo(place_id, fruit_id, receiver_id, clue_id):
                        out.append((place_id, fruit_id, receiver_id, clue_id))
    return out


@dataclass
class StoryParams:
    place: str
    fruit: str
    receiver: str
    clue: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    hasty: bool
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden_entry",
        fruit="pear",
        receiver="robin",
        clue="petal",
        hero_name="Theo",
        hero_gender="boy",
        helper_name="Maya",
        helper_gender="girl",
        parent="mother",
        trait="careful",
        hasty=True,
    ),
    StoryParams(
        place="front_entry",
        fruit="pear",
        receiver="grandma",
        clue="glitter",
        hero_name="Lina",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="father",
        trait="thoughtful",
        hasty=False,
    ),
    StoryParams(
        place="front_entry",
        fruit="apple",
        receiver="new_kid",
        clue="silver_thread",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="mother",
        trait="curious",
        hasty=True,
    ),
    StoryParams(
        place="side_entry",
        fruit="peach",
        receiver="robin",
        clue="glitter",
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Lucy",
        helper_gender="girl",
        parent="father",
        trait="steady",
        hasty=False,
    ),
]


def explain_rejection(place_id: str, fruit_id: str, receiver_id: str, clue_id: str) -> str:
    place = PLACES[place_id]
    fruit = FRUITS[fruit_id]
    receiver = RECEIVERS[receiver_id]
    clue = CLUES[clue_id]
    if receiver_id not in place.supports:
        return (
            f"(No story: {receiver.phrase} would not naturally be at {place.entry_phrase}. "
            f"Pick a receiver the place can honestly support.)"
        )
    if place_id not in clue.places:
        return (
            f"(No story: {clue.label} is not a natural clue at {place.entry_phrase}. "
            f"The clue must fit the entryway where the mystery begins.)"
        )
    if not receiver_ok_for_fruit(receiver, fruit):
        return (
            f"(No story: {receiver.phrase} needs softer fruit, and {fruit.label} is not the best fit. "
            f"Choose a softer fruit like pear or peach.)"
        )
    return "(No story: that combination does not make a reasonable mystery.)"


def outcome_of(params: StoryParams) -> str:
    clue = CLUES[params.clue]
    return "blurted" if params.hasty and clue.magic_like >= 1 else "quiet_note"


def story_title(world: World) -> str:
    return "The Case of the Missing Slices"


def prepare_scene(world: World, hero: Entity, helper: Entity, parent: Entity, fruit: Fruit) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["kindness"] += 0
    world.say(
        f"{hero.id} liked mysteries so much that {hero.pronoun()} kept a little blue notebook for clues."
    )
    world.say(
        f"That afternoon, {hero.id}'s {parent.label_word} stood in the kitchen and {fruit.pare_text}."
    )
    world.say(
        f"The plate was set near {world.place.entry_phrase}, where the light made everything look important."
    )
    world.say(
        f'"No nibbling until I bring the napkins," {parent.label_word} said, smiling at {hero.id} and {helper.id}.'
    )


def kindness_move(world: World, helper: Entity, receiver: Entity, fruit: Fruit, narrate: bool = False) -> None:
    plate = world.get("plate")
    plate.meters["missing"] += 1
    plate.meters["slices_left"] -= 1
    helper.meters["carried_slices"] += 1
    receiver.meters["helped"] += 1
    receiver.meters["need"] = 0.0
    world.facts["kindness_reason"] = receiver.attrs.get("need_word", receiver.label)
    propagate(world, narrate=narrate)


def discover_missing(world: World, hero: Entity, fruit: Fruit) -> None:
    plate = world.get("plate")
    hero.memes["alert"] += 1
    world.say(
        f"When {hero.id} looked back, part of the {fruit.slices_word} was gone."
    )
    if plate.meters["missing"] >= THRESHOLD:
        world.say(
            f"To {hero.pronoun('object')}, that was not snack trouble. It was a case."
        )


def notice_clue(world: World, hero: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    world.facts["clue_magic_like"] = clue.magic_like
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} spotted the first clue: {clue.detail}."
    )


def make_entry(world: World, hero: Entity, clue: Clue) -> None:
    notebook = world.get("notebook")
    notebook.meters["entries"] += 1
    world.say(
        f'{hero.id} opened the notebook and wrote a detective entry: "Missing fruit. Tiny clue. Follow the trail."'
    )
    if clue.magic_like >= 2:
        world.say(
            f'That made one wild idea sparkle in {hero.pronoun("possessive")} head: "Maybe a pixie came in."'
        )
    else:
        world.say(
            f'{hero.id} whispered, "It almost looks like a pixie clue."'
        )


def accuse_or_wonder(world: World, hero: Entity, helper: Entity, params: StoryParams) -> None:
    outcome = outcome_of(params)
    if outcome == "blurted":
        hero.memes["hasty"] += 1
        world.say(
            f'"A pixie took the slices!" {hero.id} announced. {helper.id} blinked but did not answer right away.'
        )
    else:
        hero.memes["care"] += 1
        world.say(
            f"{hero.id} did not say the pixie idea out loud yet. A good detective, {hero.pronoun()} decided, should check one more clue first."
        )


def investigate(world: World, hero: Entity, helper: Entity, receiver: Entity, clue: Clue) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"So {hero.id} padded toward {world.place.entry_phrase}, following the tiny clue."
    )
    world.say(
        f"There, {hero.pronoun()} found {helper.id} with {receiver.location_text}."
    )


def reveal(world: World, hero: Entity, helper: Entity, receiver: Entity, fruit: Fruit) -> None:
    hero.memes["suspicion"] = 0.0
    hero.memes["embarrassment"] += 1
    hero.memes["understanding"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f'"I only took a few {fruit.label} slices," {helper.id} said. "{receiver.kindness_text}."'
    )
    world.say(receiver.reveal_text)
    world.say(
        f"At once, the case changed shape inside {hero.id}'s mind. Nobody had stolen anything after all."
    )


def lesson(world: World, hero: Entity, helper: Entity, parent: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'{hero.id} felt {hero.pronoun("possessive")} cheeks grow warm. "I thought it was a pixie," {hero.pronoun()} admitted.'
    )
    world.say(
        f'{helper.id} gave a small shrug. "{helper.pronoun().capitalize()} did look like a pixie clue," {helper.pronoun()} said, "but I should have told you where I was going."'
    )
    world.say(
        f"{parent.label_word.capitalize()} came over with the napkins and listened to the whole mystery."
    )
    world.say(
        f'"That is how detectives learn," {parent.pronoun()} said. "First notice. Then ask. Kindness is easier to see when you do not hurry to blame."'
    )


def ending(world: World, hero: Entity, helper: Entity, receiver: Entity, fruit: Fruit) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} tore out the old guess in {hero.pronoun('possessive')} mind and made a better one."
    )
    world.say(
        f'{hero.pronoun("possessive").capitalize()} new detective entry was much shorter: "Not a pixie. A kind helper."'
    )
    world.say(
        f"Then {hero.id} carried the rest of the {fruit.slices_word} over to share, and the little mystery ended with everyone gentler than before."
    )


def tell(
    place: Place,
    fruit: Fruit,
    receiver_cfg: Receiver,
    clue: Clue,
    hero_name: str = "Theo",
    hero_gender: str = "boy",
    helper_name: str = "Maya",
    helper_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    hasty: bool = True,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait, "observant"],
        label=hero_name,
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["gentle"],
        label=helper_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    receiver = world.add(Entity(
        id="receiver",
        kind="character",
        type="creature" if receiver_cfg.id == "robin" else "person",
        role="receiver",
        label=receiver_cfg.label,
        phrase=receiver_cfg.phrase,
        attrs={"need_word": receiver_cfg.need},
        tags=set(receiver_cfg.tags),
    ))
    plate = world.add(Entity(
        id="plate",
        kind="thing",
        type="plate",
        label="plate",
        attrs={"fruit": fruit.label},
    ))
    plate.meters["slices_left"] = 4.0
    notebook = world.add(Entity(
        id="notebook",
        kind="thing",
        type="notebook",
        label="notebook",
    ))
    world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        tags=set(clue.tags),
    ))

    # The helper quietly acts before the hero notices, creating the mystery.
    kindness_move(world, helper, receiver, fruit, narrate=False)

    world.facts.update(
        title=story_title(world),
        place=place,
        fruit=fruit,
        receiver_cfg=receiver_cfg,
        clue_cfg=clue,
        clue_magic_like=clue.magic_like,
        hero=hero,
        helper=helper,
        parent=parent,
        receiver=receiver,
        hasty=hasty,
    )

    prepare_scene(world, hero, helper, parent, fruit)

    world.para()
    discover_missing(world, hero, fruit)
    notice_clue(world, hero, clue)
    make_entry(world, hero, clue)
    accuse_or_wonder(
        world,
        hero,
        helper,
        StoryParams(
            place=place.id,
            fruit=fruit.id,
            receiver=receiver_cfg.id,
            clue=clue.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            helper_name=helper_name,
            helper_gender=helper_gender,
            parent=parent_type,
            trait=trait,
            hasty=hasty,
        ),
    )

    world.para()
    investigate(world, hero, helper, receiver, clue)
    reveal(world, hero, helper, receiver, fruit)

    world.para()
    lesson(world, hero, helper, parent)
    ending(world, hero, helper, receiver, fruit)

    world.facts["outcome"] = "blurted" if hasty and clue.magic_like >= 1 else "quiet_note"
    world.facts["shared_kindness"] = True
    world.facts["lesson_learned"] = True
    return world


KNOWLEDGE = {
    "pare": [
        (
            "What does pare mean?",
            "To pare means to cut away the peel or the outside part of a fruit or vegetable. People do it carefully with a knife."
        )
    ],
    "pixie": [
        (
            "What is a pixie in a story?",
            "A pixie is a tiny make-believe creature from fairy stories. Pixies are pretend, so a good detective still checks real clues."
        )
    ],
    "entry": [
        (
            "What is an entryway?",
            "An entryway is the place where you come into a home or room. It is often near a door, a mat, or a place to hang coats."
        )
    ],
    "glitter": [
        (
            "Why can glitter be a tricky clue?",
            "Glitter is bright and easy to notice, but it can travel anywhere on shoes or clothes. That means it is not always a sign of magic."
        )
    ],
    "bird": [
        (
            "Why might someone give tiny fruit pieces to a bird?",
            "A person might think a hungry bird needs a little help. Kindness means helping gently and safely."
        )
    ],
    "neighbor": [
        (
            "How can sharing food help a shy new neighbor?",
            "Sharing a snack can make a new child feel welcome. It shows, 'You are safe here, and I want to be kind to you.'"
        )
    ],
    "family": [
        (
            "Why is it kind to bring soft fruit to a tired grandparent?",
            "Soft fruit is easy to eat and can feel comforting. Bringing it is a small way to notice that someone needs care."
        )
    ],
    "lesson": [
        (
            "What should a detective do before blaming someone?",
            "A detective should look closely, ask questions, and check the facts. Guessing too fast can hurt feelings and miss the true reason."
        )
    ],
}
KNOWLEDGE_ORDER = ["pare", "pixie", "entry", "glitter", "bird", "neighbor", "family", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    fruit = f["fruit"]
    receiver = f["receiver_cfg"]
    place = f["place"]
    return [
        f'Write a detective-style story for a 3-to-5-year-old that includes the words "pare," "pixie," and "entry."',
        f"Tell a gentle mystery where {hero.id} finds missing {fruit.label} slices near {place.entry_phrase}, suspects a pixie, and then learns the truth was an act of kindness.",
        f"Write a small detective story about a misunderstanding: a child sees a clue, guesses too fast, and discovers that someone shared fruit with {receiver.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    fruit = f["fruit"]
    receiver = f["receiver_cfg"]
    clue = f["clue_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who loves detective work, and {helper.id}, who quietly did something kind. {parent.label_word.capitalize()} also helps explain the lesson at the end."
        ),
        (
            f"Why did {hero.id} think a pixie had come in?",
            f"{hero.id} saw that some {fruit.slices_word} were missing and noticed {clue.detail}. Because the clue looked tiny and strange, {hero.pronoun()} jumped to the idea of a pixie."
        ),
        (
            "What was the detective entry in the notebook?",
            'The notebook entry said, "Missing fruit. Tiny clue. Follow the trail." It showed that the snack problem had turned into a little case in the hero\'s mind.'
        ),
        (
            "What was really happening at the entryway?",
            f"{helper.id} had carried a few slices to {receiver.phrase}. It was not stealing at all; it was a quiet act of kindness for someone who seemed {receiver.need}."
        ),
        (
            "What lesson did the hero learn?",
            f"{hero.id} learned to ask questions before blaming anyone. The clue felt magical at first, but the true answer made more sense and was kinder."
        ),
    ]
    if f.get("outcome") == "blurted":
        qa.append(
            (
                f"Did {hero.id} say the pixie idea out loud?",
                f"Yes. {hero.id} announced it before checking every clue, and that is why {hero.pronoun()} felt embarrassed later. The story shows how a quick guess can be wrong even when it sounds exciting."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} shout the pixie idea right away?",
                f"No. {hero.id} kept the idea in the notebook first and went to investigate. That made the misunderstanding quieter, but the lesson was still the same: check before you decide."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pare", "pixie", "entry", "lesson"}
    receiver_cfg = world.facts["receiver_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    if clue_cfg.id == "glitter":
        tags.add("glitter")
    if receiver_cfg.id == "robin":
        tags.add("bird")
    elif receiver_cfg.id == "new_kid":
        tags.add("neighbor")
    elif receiver_cfg.id == "grandma":
        tags.add("family")
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid story building blocks
receiver_ok(R, F) :- receiver(R), fruit(F), not needs_soft(R).
receiver_ok(R, F) :- receiver(R), fruit(F), needs_soft(R), softness(F, S), S >= 3.

valid(P, F, R, C) :- place(P), fruit(F), receiver(R), clue(C),
                     supports(P, R), clue_place(C, P), receiver_ok(R, F).

% simple ending model
outcome(blurted) :- hasty(1), clue_magic(CM), CM >= 1.
outcome(quiet_note) :- not outcome(blurted).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for receiver_id in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, receiver_id))
    for fruit_id, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fruit_id))
        lines.append(asp.fact("softness", fruit_id, fruit.softness))
    for receiver_id, receiver in RECEIVERS.items():
        lines.append(asp.fact("receiver", receiver_id))
        if receiver.requires_soft:
            lines.append(asp.fact("needs_soft", receiver_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("magic_like", clue_id, clue.magic_like))
        for place_id in sorted(clue.places):
            lines.append(asp.fact("clue_place", clue_id, place_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    clue = CLUES[params.clue]
    extra = "\n".join([
        asp.fact("hasty", 1 if params.hasty else 0),
        asp.fact("clue_magic", clue.magic_like),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    rng = random.Random(123)
    parser = build_parser()
    for _ in range(20):
        try:
            p = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small detective storyworld about a missing snack, a pixie misunderstanding, and a kindness lesson."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--fruit", choices=sorted(FRUITS))
    ap.add_argument("--receiver", choices=sorted(RECEIVERS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hasty", action="store_true", help="make the detective blurt the pixie theory")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.fruit and args.receiver and args.clue:
        if not valid_combo(args.place, args.fruit, args.receiver, args.clue):
            raise StoryError(explain_rejection(args.place, args.fruit, args.receiver, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.receiver is None or combo[2] == args.receiver)
        and (args.clue is None or combo[3] == args.clue)
    ]
    if not combos:
        given_place = args.place or sorted(PLACES)[0]
        given_fruit = args.fruit or sorted(FRUITS)[0]
        given_receiver = args.receiver or sorted(RECEIVERS)[0]
        given_clue = args.clue or sorted(CLUES)[0]
        raise StoryError(explain_rejection(given_place, given_fruit, given_receiver, given_clue))

    place_id, fruit_id, receiver_id, clue_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_kid(rng)
    helper_name, helper_gender = _pick_kid(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    hasty = True if args.hasty else rng.choice([True, False])

    return StoryParams(
        place=place_id,
        fruit=fruit_id,
        receiver=receiver_id,
        clue=clue_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        hasty=hasty,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.fruit not in FRUITS or params.receiver not in RECEIVERS or params.clue not in CLUES:
        raise StoryError("Invalid parameters: one or more requested ids are unknown.")
    if not valid_combo(params.place, params.fruit, params.receiver, params.clue):
        raise StoryError(explain_rejection(params.place, params.fruit, params.receiver, params.clue))

    world = tell(
        place=PLACES[params.place],
        fruit=FRUITS[params.fruit],
        receiver_cfg=RECEIVERS[params.receiver],
        clue=CLUES[params.clue],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        hasty=params.hasty,
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
        print(f"{len(combos)} compatible (place, fruit, receiver, clue) combos:\n")
        for place_id, fruit_id, receiver_id, clue_id in combos:
            print(f"  {place_id:13} {fruit_id:6} {receiver_id:8} {clue_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.fruit} at {p.place} ({p.receiver}, {p.clue}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
