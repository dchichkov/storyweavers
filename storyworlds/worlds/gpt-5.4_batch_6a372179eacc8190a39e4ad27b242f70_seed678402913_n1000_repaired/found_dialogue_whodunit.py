#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/found_dialogue_whodunit.py
=====================================================

A small storyworld for a child-facing whodunit: a treasured object goes missing,
children ask questions, clues point to one sensible explanation, and the object
is found. The prose is state-driven: worry, suspicion, clue-reading, dialogue,
and relief all come from the simulated world.

Run it
------
    python storyworlds/worlds/gpt-5.4/found_dialogue_whodunit.py
    python storyworlds/worlds/gpt-5.4/found_dialogue_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/found_dialogue_whodunit.py --all --qa
    python storyworlds/worlds/gpt-5.4/found_dialogue_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/found_dialogue_whodunit.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    container: str
    game: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceCfg:
    id: str
    label: str
    phrase: str
    detail: str
    hiding_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectCfg:
    id: str
    name: str
    type: str
    role_word: str
    speech_style: str
    access: set[str] = field(default_factory=set)
    reason_tags: set[str] = field(default_factory=set)
    clue_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ReasonCfg:
    id: str
    label: str
    setup: str
    move_text: str
    confession: str
    location_tags: set[str] = field(default_factory=set)
    clue_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueCfg:
    id: str
    label: str
    text: str
    question: str
    reveal: str
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    owner = world.get("owner")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    for ent in world.children():
        if ent.id != owner.id:
            ent.memes["concern"] += 1
    return []


def _r_clue_focus(world: World) -> list[str]:
    detective = world.get("detective")
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_focus", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    detective.memes["confidence"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.children():
        ent.memes["relief"] += 1
        ent.memes["suspicion"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="clue_focus", tag="emotion", apply=_r_clue_focus),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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
            world.say(line)
    return produced


ITEMS = {
    "badge": ItemCfg(
        id="badge",
        label="star badge",
        phrase="a shiny star badge",
        container="small blue box",
        game="the clubhouse oath",
        tags={"badge", "clubhouse"},
    ),
    "ribbon": ItemCfg(
        id="ribbon",
        label="prize ribbon",
        phrase="a red prize ribbon",
        container="paper folder",
        game="the pretend parade",
        tags={"ribbon", "parade"},
    ),
    "map": ItemCfg(
        id="map",
        label="treasure map",
        phrase="a crinkly treasure map",
        container="green envelope",
        game="the detective treasure hunt",
        tags={"map", "treasure"},
    ),
}

PLACES = {
    "clubhouse": PlaceCfg(
        id="clubhouse",
        label="clubhouse",
        phrase="the little clubhouse at the end of the yard",
        detail="A rug covered the floor, and a shelf of jars and crayons leaned under the window.",
        hiding_spot="behind the stack of paper on the low shelf",
        tags={"clubhouse"},
    ),
    "library_corner": PlaceCfg(
        id="library_corner",
        label="library corner",
        phrase="the library corner in the classroom",
        detail="A beanbag chair sat beside the book cart, and soft afternoon light fell across the carpet.",
        hiding_spot="under the beanbag by the book cart",
        tags={"library", "books"},
    ),
    "porch": PlaceCfg(
        id="porch",
        label="porch",
        phrase="the wide front porch",
        detail="A wicker basket stood by the door, and flowerpots lined the railing.",
        hiding_spot="inside the wicker basket by the door",
        tags={"porch", "garden"},
    ),
}

SUSPECTS = {
    "ben": SuspectCfg(
        id="ben",
        name="Ben",
        type="boy",
        role_word="builder",
        speech_style="quickly",
        access={"clubhouse", "porch"},
        reason_tags={"fix", "safe"},
        clue_tags={"tape", "twine"},
        tags={"friend"},
    ),
    "mia": SuspectCfg(
        id="mia",
        name="Mia",
        type="girl",
        role_word="artist",
        speech_style="softly",
        access={"clubhouse", "library_corner"},
        reason_tags={"decorate", "safe"},
        clue_tags={"glitter", "paper"},
        tags={"friend"},
    ),
    "leo": SuspectCfg(
        id="leo",
        name="Leo",
        type="boy",
        role_word="reader",
        speech_style="carefully",
        access={"library_corner", "porch"},
        reason_tags={"bookmark", "safe"},
        clue_tags={"book", "leaf"},
        tags={"friend"},
    ),
    "zoe": SuspectCfg(
        id="zoe",
        name="Zoe",
        type="girl",
        role_word="helper",
        speech_style="quietly",
        access={"clubhouse", "library_corner", "porch"},
        reason_tags={"safe", "decorate", "fix"},
        clue_tags={"paper", "twine", "glitter"},
        tags={"friend"},
    ),
}

REASONS = {
    "fix": ReasonCfg(
        id="fix",
        label="fix",
        setup="needed something bright while mending the corner of a game sign",
        move_text="picked it up to compare the color, then set it aside and forgot to tell anyone",
        confession="I only borrowed it because I was fixing the sign. I meant to bring it right back.",
        location_tags={"clubhouse", "porch"},
        clue_tags={"tape", "twine"},
        tags={"repair"},
    ),
    "safe": ReasonCfg(
        id="safe",
        label="safe",
        setup="worried it might get bent or stepped on",
        move_text="slid it out of the busy path to keep it safe",
        confession="I moved it so nobody would step on it. Then I hurried off and forgot where I tucked it.",
        location_tags={"clubhouse", "library_corner", "porch"},
        clue_tags={"paper", "leaf"},
        tags={"careful"},
    ),
    "decorate": ReasonCfg(
        id="decorate",
        label="decorate",
        setup="wanted to match colors for a cheerful picture",
        move_text="carried it to the art things, then hid it under a pile so glue would not drip on it",
        confession="I was matching colors for my picture. I hid it from the glue and forgot to say so.",
        location_tags={"clubhouse", "library_corner"},
        clue_tags={"glitter", "paper"},
        tags={"art"},
    ),
    "bookmark": ReasonCfg(
        id="bookmark",
        label="bookmark",
        setup="used it for one minute to hold a page in a big book",
        move_text="tucked it near the books, then got called away before putting it back",
        confession="I used it as a bookmark for one minute. Then I was called away, and I forgot.",
        location_tags={"library_corner", "porch"},
        clue_tags={"book", "leaf"},
        tags={"reading"},
    ),
}

CLUES = {
    "glitter": ClueCfg(
        id="glitter",
        label="glitter",
        text="On the floor nearby, a tiny sprinkle of silver glitter winked in the light.",
        question='"{name}," the detective said, "were you making art here?"',
        reveal="The glitter pointed toward art supplies, not a sneaky thief.",
        tags={"glitter", "art"},
    ),
    "paper": ClueCfg(
        id="paper",
        label="paper",
        text="A bent corner of colored paper peeked out from the shelf.",
        question='"{name}," the detective asked, "did paper have anything to do with this?"',
        reveal="The paper suggested the object had been tucked away, not taken away.",
        tags={"paper"},
    ),
    "tape": ClueCfg(
        id="tape",
        label="tape",
        text="A loop of yellow tape stuck to the table leg like a bright little clue.",
        question='"{name}," the detective said, "were you fixing something with tape?"',
        reveal="The tape hinted at mending, not stealing.",
        tags={"tape", "repair"},
    ),
    "twine": ClueCfg(
        id="twine",
        label="twine",
        text="A short fuzzy piece of twine lay curled beside the chair.",
        question='"{name}," the detective asked, "were you tying something together?"',
        reveal="The twine made the mystery feel less mean and more mix-up than crime.",
        tags={"twine", "repair"},
    ),
    "book": ClueCfg(
        id="book",
        label="book",
        text="A fat storybook lay open with a square-shaped gap between its pages.",
        question='"{name}," the detective said, "did you tuck anything into a book?"',
        reveal="The open book pointed to reading, not plotting.",
        tags={"book", "reading"},
    ),
    "leaf": ClueCfg(
        id="leaf",
        label="leaf",
        text="A dry leaf rested where the wind could only have blown it from the door.",
        question='"{name}," the detective asked, "did you carry it toward the door to keep it safe?"',
        reveal="The leaf led toward the edge of the room where careful hands might stash something.",
        tags={"leaf", "outside"},
    ),
}


def valid_combo(place_id: str, suspect_id: str, reason_id: str, clue_id: str) -> bool:
    place = PLACES[place_id]
    suspect = SUSPECTS[suspect_id]
    reason = REASONS[reason_id]
    clue = CLUES[clue_id]
    return (
        place.id in suspect.access
        and reason.id in suspect.reason_tags
        and place.id in reason.location_tags
        and clue.id in suspect.clue_tags
        and clue.id in reason.clue_tags
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for suspect_id in SUSPECTS:
            for reason_id in REASONS:
                for clue_id in CLUES:
                    if valid_combo(place_id, suspect_id, reason_id, clue_id):
                        combos.append((place_id, suspect_id, reason_id, clue_id))
    return combos


def sensible_clues() -> list[str]:
    return sorted(cid for cid in CLUES if cid and len(cid) >= SENSE_MIN)


@dataclass
class StoryParams:
    item: str
    place: str
    suspect: str
    reason: str
    clue: str
    detective_name: str
    detective_gender: str
    owner_name: str
    owner_gender: str
    adult: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        item="badge",
        place="clubhouse",
        suspect="mia",
        reason="decorate",
        clue="glitter",
        detective_name="Nora",
        detective_gender="girl",
        owner_name="Finn",
        owner_gender="boy",
        adult="mother",
    ),
    StoryParams(
        item="map",
        place="library_corner",
        suspect="leo",
        reason="bookmark",
        clue="book",
        detective_name="Max",
        detective_gender="boy",
        owner_name="Lily",
        owner_gender="girl",
        adult="father",
    ),
    StoryParams(
        item="ribbon",
        place="porch",
        suspect="ben",
        reason="fix",
        clue="twine",
        detective_name="Ava",
        detective_gender="girl",
        owner_name="Theo",
        owner_gender="boy",
        adult="mother",
    ),
    StoryParams(
        item="badge",
        place="library_corner",
        suspect="zoe",
        reason="safe",
        clue="paper",
        detective_name="Eli",
        detective_gender="boy",
        owner_name="Mia",
        owner_gender="girl",
        adult="father",
    ),
]


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def explain_rejection(place_id: str, suspect_id: str, reason_id: str, clue_id: str) -> str:
    bits: list[str] = []
    place = PLACES[place_id]
    suspect = SUSPECTS[suspect_id]
    reason = REASONS[reason_id]
    clue = CLUES[clue_id]
    if place.id not in suspect.access:
        bits.append(f"{suspect.name} has no good reason to be at {place.phrase}")
    if reason.id not in suspect.reason_tags:
        bits.append(f"{suspect.name} would not plausibly move the object for {reason.label}")
    if place.id not in reason.location_tags:
        bits.append(f"the reason '{reason.label}' does not fit {place.label}")
    if clue.id not in suspect.clue_tags or clue.id not in reason.clue_tags:
        bits.append(f"the clue '{clue.label}' does not point honestly to that explanation")
    if not bits:
        return "(No story: this combination is not reasonable.)"
    return "(No story: " + "; ".join(bits) + ".)"


def introduce(world: World, owner: Entity, detective: Entity, item: ItemCfg, place: PlaceCfg) -> None:
    owner.memes["pride"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"After lunch, {owner.id} and {detective.id} hurried to {place.phrase}. {place.detail}"
    )
    world.say(
        f"{owner.id} opened {item.container} to show off {item.phrase}, because the children needed it for {item.game}."
    )


def lose_item(world: World, owner: Entity, item_ent: Entity) -> None:
    item_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But when {owner.id} looked again, the {item_ent.label} was gone. "{item_ent.label.capitalize()}? Where did it go?" {owner.pronoun()} whispered.'
    )
    world.say(
        f"{owner.id}'s cheeks turned pink, and {owner.pronoun()} looked all around the room."
    )


def suspect_talk(world: World, detective: Entity, suspect: Entity, reason: ReasonCfg) -> None:
    owner = world.get("owner")
    suspect.memes["suspicion_on_them"] += 1
    detective.memes["focus"] += 1
    world.say(
        f'"Nobody leave yet," said {detective.id}. "{owner.id}\'s {world.get("item").label} has gone missing, and I want to ask careful questions."'
    )
    world.say(
        f'{suspect.id} blinked {SUSPECTS[world.facts["suspect_cfg"].id].speech_style}. "I did walk by the shelf," {suspect.pronoun()} said, "but I was there because I {reason.setup}."'
    )


def notice_clue(world: World, detective: Entity, clue: ClueCfg) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(clue.text)
    world.say(
        f'{detective.id} knelt down. "{clue.reveal}" {detective.pronoun()} said.'
    )


def follow_dialogue(world: World, detective: Entity, suspect: Entity, clue: ClueCfg) -> None:
    text = clue.question.format(name=suspect.id)
    world.say(text)
    world.say(
        f'"Yes," {suspect.id} answered. "I did not mean to hide anything forever."'
    )


def reveal(world: World, owner: Entity, detective: Entity, suspect: Entity, item_ent: Entity,
           reason: ReasonCfg, place: PlaceCfg) -> None:
    suspect.memes["honesty"] += 1
    owner.memes["hope"] += 1
    item_ent.meters["found"] += 1
    item_ent.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f'{suspect.id} pressed a hand to {suspect.pronoun("possessive")} chest. "{reason.confession}"'
    )
    world.say(
        f"Together they looked {place.hiding_spot}, and there the {item_ent.label} was, safe and a little dusty."
    )
    world.say(
        f'"Found it!" cried {owner.id}. {detective.id} smiled, and even {suspect.id} let out a relieved breath.'
    )


def ending(world: World, owner: Entity, detective: Entity, suspect: Entity, item: ItemCfg) -> None:
    owner.memes["joy"] += 1
    detective.memes["pride"] += 1
    suspect.memes["relief"] += 1
    world.say(
        f'"Next time, please tell us first," said {owner.id}.'
    )
    world.say(
        f'"I will," said {suspect.id}. "{item.label.capitalize()} was never stolen. It was only misplaced by a hurried helper."'
    )
    world.say(
        f"Soon the children were laughing again, and {item.phrase} shone in the middle of the game like proof that a calm question can solve a mystery."
    )


def tell(params: StoryParams) -> World:
    item_cfg = ITEMS[params.item]
    place_cfg = PLACES[params.place]
    suspect_cfg = SUSPECTS[params.suspect]
    reason_cfg = REASONS[params.reason]
    clue_cfg = CLUES[params.clue]

    if not valid_combo(params.place, params.suspect, params.reason, params.clue):
        raise StoryError(explain_rejection(params.place, params.suspect, params.reason, params.clue))

    world = World()
    owner = world.add(Entity(id=params.owner_name, kind="character", type=params.owner_gender, role="owner"))
    detective = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_gender, role="detective"))
    suspect = world.add(
        Entity(
            id=suspect_cfg.name,
            kind="character",
            type=suspect_cfg.type,
            role="suspect",
            traits=[suspect_cfg.role_word],
            tags=set(suspect_cfg.tags),
        )
    )
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult, role="adult", label="the grown-up"))
    item_ent = world.add(Entity(id="item", type="object", label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags)))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue_cfg.label, phrase=clue_cfg.text, tags=set(clue_cfg.tags)))
    place_ent = world.add(Entity(id="place", type="place", label=place_cfg.label, phrase=place_cfg.phrase, tags=set(place_cfg.tags)))

    world.facts.update(
        owner=owner,
        detective=detective,
        suspect=suspect,
        adult=adult,
        item_cfg=item_cfg,
        place_cfg=place_cfg,
        suspect_cfg=suspect_cfg,
        reason_cfg=reason_cfg,
        clue_cfg=clue_cfg,
    )

    introduce(world, owner, detective, item_cfg, place_cfg)
    world.para()
    lose_item(world, owner, item_ent)
    suspect_talk(world, detective, suspect, reason_cfg)
    world.para()
    notice_clue(world, detective, clue_cfg)
    follow_dialogue(world, detective, suspect, clue_cfg)
    world.para()
    reveal(world, owner, detective, suspect, item_ent, reason_cfg, place_cfg)
    ending(world, owner, detective, suspect, item_cfg)

    world.facts.update(
        found=item_ent.meters["found"] >= THRESHOLD,
        missing=item_ent.meters["missing"] >= THRESHOLD,
        place=place_ent,
        item=item_ent,
        clue=clue_ent,
        culprit=suspect,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    detective = f["detective"]
    item = f["item_cfg"]
    place = f["place_cfg"]
    suspect = f["suspect"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "found" and uses dialogue.',
        f"Tell a gentle mystery where {owner.id} loses {item.phrase} at {place.phrase}, and {detective.id} solves it by asking questions.",
        f"Write a child-friendly detective story with dialogue, a clue, and a surprising but kind explanation involving {suspect.id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    detective = f["detective"]
    suspect = f["suspect"]
    item = f["item_cfg"]
    place = f["place_cfg"]
    reason = f["reason_cfg"]
    clue = f["clue_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id}, who lost {item.phrase}, {detective.id}, who asked careful questions, and {suspect.id}, who knew where it had been moved.",
        ),
        (
            f"Why was {owner.id} upset?",
            f"{owner.id} was upset because the {item.label} was missing just when the children needed it for {item.game}. That made the room feel like a real little mystery.",
        ),
        (
            f"What clue did {detective.id} notice?",
            f"{detective.id} noticed {clue.text[0].lower() + clue.text[1:]} The clue mattered because it pointed toward {reason.label} instead of a mean theft.",
        ),
        (
            f"What did {detective.id} ask {suspect.id}?",
            f"{detective.id} asked {suspect.id} direct questions about the clue. The talking solved the mystery because the clue and the answer fit together.",
        ),
    ]
    if f.get("found"):
        qa.append(
            (
                f"Where was the {item.label} found?",
                f"It was found {place.hiding_spot}. The children looked there after {suspect.id} explained why {suspect.pronoun()} had moved it.",
            )
        )
        qa.append(
            (
                f"Did {suspect.id} steal the {item.label}?",
                f"No. {suspect.id} had moved it because {suspect.pronoun()} {reason.setup} and then forgot to tell anyone. The mystery was a mix-up, not a crime.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the {item.label} back in the game and everyone feeling relieved. The ending shows that calm questions and honest answers helped the children put the worry away.",
            )
        )
    return qa


KNOWLEDGE = {
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with hidden facts. You solve it by noticing clues and asking careful questions.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It does not tell the whole answer by itself, but it points in the right direction.",
        )
    ],
    "dialogue": [
        (
            "What is dialogue in a story?",
            "Dialogue is when characters speak out loud in the story. Their words can show feelings, questions, and answers.",
        )
    ],
    "honesty": [
        (
            "Why is it good to tell people when you borrow something?",
            "It helps people know where their things are and keeps worry from growing. Honest words can stop a small mix-up from turning into a big problem.",
        )
    ],
    "library": [
        (
            "What do people do in a library corner?",
            "They sit quietly, look at books, and read stories. It is a cozy place for calm voices and careful hands.",
        )
    ],
    "art": [
        (
            "Why do art tables sometimes have glitter or paper scraps?",
            "Art tables get tiny bits of supplies on them while people make things. Those little bits can also become clues in a story.",
        )
    ],
    "repair": [
        (
            "What does it mean to fix something?",
            "Fixing something means making it work or look right again. People may use tape, string, or careful hands to do it.",
        )
    ],
}

KNOWLEDGE_ORDER = ["mystery", "clue", "dialogue", "honesty", "library", "art", "repair"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "clue", "dialogue", "honesty"}
    if f["place_cfg"].id == "library_corner":
        tags.add("library")
    if f["clue_cfg"].id in {"glitter", "paper"} or f["reason_cfg"].id == "decorate":
        tags.add("art")
    if f["reason_cfg"].id == "fix" or f["clue_cfg"].id in {"tape", "twine"}:
        tags.add("repair")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,R,C) :- place(P), suspect(S), reason(R), clue(C),
                  access(S,P), has_reason(S,R), reason_place(R,P),
                  suspect_clue(S,C), reason_clue(R,C).

outcome(found) :- chosen_valid.
chosen_valid :- chosen_place(P), chosen_suspect(S), chosen_reason(R), chosen_clue(C),
                valid(P,S,R,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for place_id in sorted(suspect.access):
            lines.append(asp.fact("access", suspect_id, place_id))
        for reason_id in sorted(suspect.reason_tags):
            lines.append(asp.fact("has_reason", suspect_id, reason_id))
        for clue_id in sorted(suspect.clue_tags):
            lines.append(asp.fact("suspect_clue", suspect_id, clue_id))
    for reason_id, reason in REASONS.items():
        lines.append(asp.fact("reason", reason_id))
        for place_id in sorted(reason.location_tags):
            lines.append(asp.fact("reason_place", reason_id, place_id))
        for clue_id in sorted(reason.clue_tags):
            lines.append(asp.fact("reason_clue", reason_id, clue_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_suspect", params.suspect),
            asp.fact("chosen_reason", params.reason),
            asp.fact("chosen_clue", params.clue),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    return "found" if valid_combo(params.place, params.suspect, params.reason, params.clue) else "invalid"


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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed unexpectedly at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "found" not in sample.story.lower():
            raise StoryError("Smoke test story did not render a proper found-ending.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child-friendly whodunit with dialogue and a found object."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--reason", choices=REASONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective-name")
    ap.add_argument("--owner-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.suspect and args.reason and args.clue:
        if not valid_combo(args.place, args.suspect, args.reason, args.clue):
            raise StoryError(explain_rejection(args.place, args.suspect, args.reason, args.clue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.suspect is None or combo[1] == args.suspect)
        and (args.reason is None or combo[2] == args.reason)
        and (args.clue is None or combo[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, suspect_id, reason_id, clue_id = rng.choice(sorted(combos))
    item_id = args.item or rng.choice(sorted(ITEMS))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or pick_name(rng, detective_gender)
    owner_name = args.owner_name or pick_name(rng, owner_gender, avoid=detective_name)
    adult = args.adult or rng.choice(["mother", "father"])

    return StoryParams(
        item=item_id,
        place=place_id,
        suspect=suspect_id,
        reason=reason_id,
        clue=clue_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect '{params.suspect}'.)")
    if params.reason not in REASONS:
        raise StoryError(f"(Unknown reason '{params.reason}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue '{params.clue}'.)")
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, suspect, reason, clue) combos:\n")
        for place_id, suspect_id, reason_id, clue_id in combos:
            print(f"  {place_id:14} {suspect_id:6} {reason_id:10} {clue_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.item} at {p.place}: {p.suspect} / {p.reason} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
