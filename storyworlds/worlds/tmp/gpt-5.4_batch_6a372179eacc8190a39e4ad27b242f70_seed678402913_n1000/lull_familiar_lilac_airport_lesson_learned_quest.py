#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lull_familiar_lilac_airport_lesson_learned_quest.py
================================================================================

A small airport storyworld in a nursery-rhyme mood.

Seed features rebuilt as state:
- words: lull, familiar, lilac
- setting: airport
- features: Lesson Learned, Quest, Twist
- style: Nursery Rhyme

Domain:
A child in an airport finds a dropped lilac comfort item during a lull in the
announcements. The child sets off on a small quest to return it before boarding.
The twist is that the item looks familiar enough that the child first thinks it
might be their own. A sensible airport helper and a clue lead either to a direct
reunion or to a careful handoff at the gate desk. The lesson is to check, ask,
and not snatch familiar-looking things in a busy place.
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
        female = {"girl", "mother", "woman", "agent_woman"}
        male = {"boy", "father", "man", "agent_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Zone:
    id: str
    label: str
    verse: str
    difficulty: int = 1
    helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FoundItem:
    id: str
    label: str
    phrase: str
    carrier: str
    fabric: bool = True
    comfort: bool = True
    portable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    line: str
    strength: int = 2
    needs_fabric: bool = False
    needs_comfort: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    role_name: str
    sense: int = 2
    power: int = 2
    action: str = ""
    fail_action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, zone: Zone) -> None:
        self.zone = zone
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
        clone = World(self.zone)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_loss_worry(world: World) -> list[str]:
    item = world.entities.get("found")
    owner = world.entities.get("owner")
    hero = world.entities.get("hero")
    out: list[str] = []
    if item and owner and item.meters["lost"] >= THRESHOLD:
        sig = ("owner_worry", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["worry"] += 1
            out.append("__owner_worry__")
    if item and hero and item.meters["lost"] >= THRESHOLD:
        sig = ("hero_care", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["care"] += 1
            out.append("__hero_care__")
    return out


def _r_reunion_relief(world: World) -> list[str]:
    item = world.entities.get("found")
    owner = world.entities.get("owner")
    hero = world.entities.get("hero")
    guard = world.entities.get("guardian")
    out: list[str] = []
    if item and item.meters["returned"] >= THRESHOLD:
        sig = ("relief", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            if owner:
                owner.memes["relief"] += 1
                owner.memes["calm"] += 1
                owner.memes["worry"] = 0.0
            if hero:
                hero.memes["relief"] += 1
                hero.memes["pride"] += 1
            if guard:
                guard.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="loss_worry", tag="social", apply=_r_loss_worry),
    Rule(name="reunion_relief", tag="social", apply=_r_reunion_relief),
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


def clue_fits(item: FoundItem, clue: Clue) -> bool:
    if clue.needs_fabric and not item.fabric:
        return False
    if clue.needs_comfort and not item.comfort:
        return False
    return True


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def helper_available(zone: Zone, helper_id: str) -> bool:
    return helper_id in zone.helpers


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for zone_id, zone in ZONES.items():
        for item_id, item in ITEMS.items():
            for clue_id, clue in CLUES.items():
                if not clue_fits(item, clue):
                    continue
                for helper_id, helper in HELPERS.items():
                    if helper.sense < SENSE_MIN:
                        continue
                    if helper_available(zone, helper_id):
                        combos.append((zone_id, item_id, clue_id, helper_id))
    return combos


def quest_score(zone: Zone, clue: Clue, helper: Helper, rush: int) -> int:
    return clue.strength + helper.power - zone.difficulty - rush


def outcome_of(params: "StoryParams") -> str:
    score = quest_score(
        ZONES[params.zone],
        CLUES[params.clue],
        HELPERS[params.helper],
        params.rush,
    )
    return "reunited" if score >= 1 else "desk"


def predict_search(zone: Zone, clue: Clue, helper: Helper, rush: int) -> dict:
    score = quest_score(zone, clue, helper, rush)
    return {"score": score, "reunited": score >= 1}


def introduce(world: World, hero: Entity, guardian: Entity, own_item: str) -> None:
    lull_line = world.zone.verse
    world.say(
        f"At the airport, in a silver-bright hall, {hero.id} walked with "
        f"{hero.pronoun('possessive')} {guardian.label_word}, small steps and all."
    )
    world.say(
        f"There came a lull in the rolling speaker song, and the floor lights "
        f"winked as the line moved along. {lull_line}"
    )
    world.say(
        f"In {hero.pronoun('possessive')} hand was {own_item}, a familiar travel thing "
        f"that had ridden beside {hero.pronoun('object')} all morning long."
    )


def discover(world: World, hero: Entity, item: FoundItem) -> None:
    found = world.get("found")
    found.meters["lost"] += 1
    propagate(world, narrate=False)
    hero.memes["curiosity"] += 1
    world.say(
        f"By a row of chairs lay {item.phrase}, quiet and still, lilac and soft "
        f"like a cloud on a windowsill."
    )
    world.say(
        f"{hero.id} bent low. 'Oh my,' {hero.pronoun()} said, 'this looks so familiar, "
        f"I thought it might be mine instead.'"
    )


def twist(world: World, hero: Entity, item: FoundItem) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f"But then {hero.pronoun()} checked {hero.pronoun('possessive')} own things twice, "
        f"and there was the matching one tucked in plain sight."
    )
    world.say(
        f"So that was the twist in the humming airport light: the lilac thing felt "
        f"familiar, yet it belonged to someone else quite right."
    )


def start_quest(world: World, hero: Entity, guardian: Entity, clue: Clue, helper: Helper) -> None:
    hero.memes["purpose"] += 1
    guardian.memes["care"] += 1
    world.say(
        f"'{helper.role_name.capitalize()} might help us,' said {guardian.label_word} with care. "
        f"'{clue.line}' So off went the two through the bright airport air."
    )


def meet_helper(world: World, helper_ent: Entity, helper: Helper, zone: Zone) -> None:
    helper_ent.memes["duty"] += 1
    world.say(
        f"They found {helper.label} near {zone.label}, neat as could be, "
        f"ready to listen beside gate signs and tea."
    )


def use_clue(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["focus"] += 1
    if clue.id == "name_tag":
        world.say(
            f"{hero.id} pointed to the tag and read the careful name, "
            f"soft as a rhyme and clear as a flame."
        )
    elif clue.id == "stitched_initials":
        world.say(
            f"{hero.id} traced the stitched letters with one gentle finger. "
            f"The tiny sewn marks helped the right thought linger."
        )
    else:
        world.say(
            f"Then from farther down the gate came a familiar lull, a sleepy little tune, "
            f"soft and full. {hero.id} listened hard and turned like a spoon to the moon."
        )


def reunion(world: World, hero: Entity, owner: Entity, item: FoundItem, helper: Helper) -> None:
    found = world.get("found")
    found.meters["returned"] += 1
    propagate(world, narrate=False)
    owner.meters["holding"] += 1
    world.say(
        f"Soon they found {owner.id}, whose eyes had grown wet. "
        f"When {owner.pronoun()} saw the lilac {item.label}, {owner.pronoun()} smiled through the fret."
    )
    world.say(
        f"{helper.label.capitalize()} {helper.action}, and into {owner.pronoun('possessive')} arms "
        f"went the soft little treasure at last."
    )
    world.say(
        f"{hero.id} felt light as a paper plane riding the blue, for a kind-hearted quest "
        f"had come kindly true."
    )


def desk_handoff(world: World, hero: Entity, guardian: Entity, helper: Helper, item: FoundItem) -> None:
    hero.memes["patience"] += 1
    helper_ent = world.get("helper")
    helper_ent.meters["custody"] += 1
    world.say(
        f"But the boarding bell fluttered and the line moved fast. "
        f"There was no safe time to search every gate at last."
    )
    world.say(
        f"{helper.label.capitalize()} {helper.fail_action}, setting the lilac {item.label} where lost things are kept "
        f"with care. A calm page floated out through the airport air."
    )
    world.say(
        f"As {hero.id} walked on with {guardian.label_word}, {hero.pronoun()} looked back once more, "
        f"trusting the right grown-up at the desk by the door."
    )


def lesson(world: World, hero: Entity, guardian: Entity, item: FoundItem, direct: bool) -> None:
    hero.memes["lesson"] += 1
    guardian.memes["lesson"] += 1
    world.say(
        f"Then {guardian.label_word} knelt low and said, 'Here is the lesson, bright in your head: "
        f"when a thing looks familiar in a busy, bustling place, do not grab first in a hurry-chase.'"
    )
    if direct:
        world.say(
            f"'Check, ask, and be gentle,' {guardian.pronoun()} said with a grin. "
            f"'That is how kind airport quests begin—and how lost little hearts can settle within.'"
        )
    else:
        world.say(
            f"'Check, ask, and use helpers,' {guardian.pronoun()} said with a grin. "
            f"'That is how careful kindness can still win, even when boarding songs begin.'"
        )


def closing_image(world: World, hero: Entity, own_item: str, direct: bool) -> None:
    if direct:
        world.say(
            f"On the plane, {hero.id} hugged {own_item} close, while clouds outside drifted in lilac rows. "
            f"The airport no longer seemed noisy and wild; it felt like a rhyme remembered by a wiser child."
        )
    else:
        world.say(
            f"On the plane, {hero.id} hugged {own_item} close, while the wing lights blinked in lilac rows. "
            f"{hero.pronoun().capitalize()} had not kept the found thing, yet still had done right, and that made the dark runway seem soft with light."
        )


def tell(
    zone: Zone,
    item: FoundItem,
    clue: Clue,
    helper: Helper,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    guardian_type: str = "mother",
    helper_type: str = "agent_woman",
    owner_name: str = "Pip",
    owner_gender: str = "girl",
    rush: int = 1,
) -> World:
    world = World(zone)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, role="guardian", label="the parent"))
    helper_ent = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label=helper.label))
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
    found = world.add(
        Entity(
            id="found",
            kind="thing",
            type=item.id,
            role="found_item",
            label=item.label,
            phrase=item.phrase,
            tags=set(item.tags),
            attrs={"carrier": item.carrier},
        )
    )

    own_item = f"{hero.pronoun('possessive')} own lilac {item.label}"
    found.attrs["owner_name"] = owner_name

    introduce(world, hero, guardian, own_item)
    world.para()
    discover(world, hero, item)
    twist(world, hero, item)
    world.para()
    start_quest(world, hero, guardian, clue, helper)
    meet_helper(world, helper_ent, helper, zone)
    use_clue(world, hero, clue)
    world.para()

    direct = predict_search(zone, clue, helper, rush)["reunited"]
    if direct:
        reunion(world, hero, owner, item, helper)
    else:
        desk_handoff(world, hero, guardian, helper, item)

    world.para()
    lesson(world, hero, guardian, item, direct)
    closing_image(world, hero, own_item, direct)

    world.facts.update(
        hero=hero,
        guardian=guardian,
        helper=helper_ent,
        owner=owner,
        zone=zone,
        item_cfg=item,
        clue=clue,
        helper_cfg=helper,
        rush=rush,
        own_item=own_item,
        outcome="reunited" if direct else "desk",
        returned=direct,
        twist=True,
    )
    return world


ZONES = {
    "gate": Zone(
        id="gate",
        label="the gate",
        verse="Near the gate, where the silver seats made rows, little suitcases nodded with sleepy bows.",
        difficulty=1,
        helpers={"gate_agent", "cleaner"},
        tags={"gate"},
    ),
    "window": Zone(
        id="window",
        label="the big window",
        verse="By the big window, where tail fins gleamed, the runway shimmered the way a teacup dreamed.",
        difficulty=2,
        helpers={"gate_agent", "cleaner"},
        tags={"airport", "airplane"},
    ),
    "tram": Zone(
        id="tram",
        label="the airport tram stop",
        verse="By the tram stop, where the floor hummed low, bright arrows pointed where small feet should go.",
        difficulty=2,
        helpers={"cleaner"},
        tags={"airport"},
    ),
    "quiet_corner": Zone(
        id="quiet_corner",
        label="the quiet corner",
        verse="In the quiet corner, where the bustle grew thin, there was room for a yawn and a soft little spin.",
        difficulty=1,
        helpers={"gate_agent"},
        tags={"airport"},
    ),
}

ITEMS = {
    "bunny": FoundItem(
        id="bunny",
        label="bunny",
        phrase="a lilac bunny with floppy ears",
        carrier="one small arm",
        fabric=True,
        comfort=True,
        portable=True,
        tags={"toy", "comfort"},
    ),
    "blanket": FoundItem(
        id="blanket",
        label="blanket",
        phrase="a lilac blanket with a satin edge",
        carrier="one warm shoulder",
        fabric=True,
        comfort=True,
        portable=True,
        tags={"blanket", "comfort"},
    ),
    "pillow": FoundItem(
        id="pillow",
        label="neck pillow",
        phrase="a lilac neck pillow shaped like a moon",
        carrier="one drowsy neck",
        fabric=True,
        comfort=True,
        portable=True,
        tags={"pillow", "comfort"},
    ),
}

CLUES = {
    "name_tag": Clue(
        id="name_tag",
        label="name tag",
        line="Look, there is a name tag tied with a tiny bow",
        strength=3,
        needs_fabric=False,
        needs_comfort=False,
        tags={"name_tag"},
    ),
    "stitched_initials": Clue(
        id="stitched_initials",
        label="stitched initials",
        line="See those stitched initials, neat and small",
        strength=2,
        needs_fabric=True,
        needs_comfort=False,
        tags={"sewing"},
    ),
    "sleepy_hum": Clue(
        id="sleepy_hum",
        label="sleepy hum",
        line="Hush now, can you hear that sleepy hum, a familiar lull from farther down",
        strength=2,
        needs_fabric=False,
        needs_comfort=True,
        tags={"lullaby"},
    ),
}

HELPERS = {
    "gate_agent": Helper(
        id="gate_agent",
        label="the gate agent",
        role_name="the gate agent",
        sense=3,
        power=3,
        action="checked the gate list, made one kind page, and led them to the waiting family",
        fail_action="took the item behind the desk, wrote down where it was found, and called for its owner over the speaker",
        qa_text="used the gate desk and the speaker page to help",
        tags={"airport_worker", "gate_agent"},
    ),
    "cleaner": Helper(
        id="cleaner",
        label="the cleaner",
        role_name="the cleaner",
        sense=2,
        power=2,
        action="recognized the family from the nearby seats and waved them over",
        fail_action="carried the item to the gate desk and asked for a careful page",
        qa_text="brought the item to the right airport worker and helped search nearby seats",
        tags={"airport_worker", "cleaner"},
    ),
    "snack_cashier": Helper(
        id="snack_cashier",
        label="the snack cashier",
        role_name="the snack cashier",
        sense=1,
        power=1,
        action="pointed in a vague circle and guessed",
        fail_action="shrugged and went back to the till",
        qa_text="only guessed and was not the right helper",
        tags={"shop"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Poppy", "June", "Tara", "Nora", "Ivy", "Elsie"]
BOY_NAMES = ["Owen", "Milo", "Benji", "Theo", "Arlo", "Finn", "Noah", "Remy"]

OWNER_NAMES_GIRL = ["Pip", "Lulu", "Maisie", "Wren"]
OWNER_NAMES_BOY = ["Toby", "Ned", "Kit", "Hugo"]


@dataclass
class StoryParams:
    zone: str
    item: str
    clue: str
    helper: str
    hero_name: str
    hero_gender: str
    guardian: str
    helper_type: str
    owner_name: str
    owner_gender: str
    rush: int = 1
    seed: Optional[int] = None


KNOWLEDGE = {
    "airport": [
        (
            "What is an airport?",
            "An airport is a place where people go to take airplanes. It has gates, workers, signs, and lots of people moving from one place to another.",
        )
    ],
    "airplane": [
        (
            "Why do people wait at a gate before a flight?",
            "A gate is the place where passengers gather before getting on the airplane. Workers there help people board the right plane safely.",
        )
    ],
    "gate_agent": [
        (
            "What does a gate agent do?",
            "A gate agent helps people at the gate, checks tickets, makes announcements, and helps solve travel problems. That makes a gate agent a good person to ask about a lost item nearby.",
        )
    ],
    "cleaner": [
        (
            "Why might a cleaner know about lost things in an airport?",
            "A cleaner walks through busy places and notices what gets left behind. If a child finds something, a cleaner can help bring it to the right airport worker.",
        )
    ],
    "name_tag": [
        (
            "Why is a name tag helpful on a travel item?",
            "A name tag tells other people who the item belongs to. That makes it much easier to return the item kindly and quickly.",
        )
    ],
    "lullaby": [
        (
            "What is a lull?",
            "A lull is a quiet pause when noise or activity settles down for a little while. In a story, a lull can make a small sound easier to notice.",
        ),
        (
            "What is a lullaby?",
            "A lullaby is a soft song meant to calm someone, often a sleepy child. A familiar lullaby can help people feel safe in a busy place.",
        )
    ],
    "comfort": [
        (
            "Why do children sometimes carry comfort items when they travel?",
            "A comfort item can feel familiar when everything else is new. That familiar feeling can help a child stay calm in a crowded airport.",
        )
    ],
    "blanket": [
        (
            "Why might a blanket matter so much to a child?",
            "A special blanket can help a child rest and feel safe. Losing it in a busy place can make the child worried very quickly.",
        )
    ],
    "toy": [
        (
            "Why should you ask before taking a toy that looks like yours?",
            "Many toys look alike, especially if they are the same color or shape. Checking first helps you avoid taking something that belongs to someone else.",
        )
    ],
    "pillow": [
        (
            "What is a neck pillow for?",
            "A neck pillow helps support your head while you sit and travel. It can make a long wait or a flight feel more comfortable.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "airport",
    "airplane",
    "gate_agent",
    "cleaner",
    "name_tag",
    "lullaby",
    "comfort",
    "blanket",
    "toy",
    "pillow",
]


CURATED = [
    StoryParams(
        zone="gate",
        item="bunny",
        clue="name_tag",
        helper="gate_agent",
        hero_name="Mina",
        hero_gender="girl",
        guardian="mother",
        helper_type="agent_woman",
        owner_name="Pip",
        owner_gender="girl",
        rush=0,
    ),
    StoryParams(
        zone="window",
        item="blanket",
        clue="sleepy_hum",
        helper="cleaner",
        hero_name="Owen",
        hero_gender="boy",
        guardian="father",
        helper_type="agent_man",
        owner_name="Lulu",
        owner_gender="girl",
        rush=1,
    ),
    StoryParams(
        zone="tram",
        item="pillow",
        clue="stitched_initials",
        helper="cleaner",
        hero_name="Lila",
        hero_gender="girl",
        guardian="mother",
        helper_type="agent_woman",
        owner_name="Ned",
        owner_gender="boy",
        rush=2,
    ),
    StoryParams(
        zone="quiet_corner",
        item="blanket",
        clue="name_tag",
        helper="gate_agent",
        hero_name="Theo",
        hero_gender="boy",
        guardian="father",
        helper_type="agent_man",
        owner_name="Maisie",
        owner_gender="girl",
        rush=1,
    ),
]


def explain_rejection(zone: Zone, item: FoundItem, clue: Clue, helper: Helper) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: {helper.label} is not a sensible airport helper for a lost-item quest. "
            f"Ask a gate agent or cleaner instead.)"
        )
    if not helper_available(zone, helper.id):
        return (
            f"(No story: {helper.label} would not be the right helper in {zone.label}. "
            f"Pick a helper who is actually available there.)"
        )
    if not clue_fits(item, clue):
        return (
            f"(No story: the clue '{clue.label}' does not fit {item.phrase}. "
            f"Choose a clue that could really belong to that item.)"
        )
    return "(No story: this airport quest does not make sense with those options.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    clue = f["clue"]
    zone = f["zone"]
    return [
        f'Write a nursery-rhyme style airport story for a 3-to-5-year-old that includes the words "lull", "familiar", and "lilac".',
        f"Tell a gentle quest story where {hero.id} finds {item.phrase} at {zone.label}, mistakes it for something familiar, and learns to ask an airport helper before taking it.",
        f"Write a story with a twist, a lesson learned, and a happy airport mood, using the clue '{clue.label}' to help return a lost item.",
    ]


def pair_answer(hero: Entity, guardian: Entity) -> str:
    return f"It is about {hero.id} and {hero.pronoun('possessive')} {guardian.label_word} at the airport."


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    owner = f["owner"]
    zone = f["zone"]
    item = f["item_cfg"]
    clue = f["clue"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    own_item = f["own_item"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            pair_answer(hero, guardian),
        ),
        (
            f"What did {hero.id} find at the airport?",
            f"{hero.id} found {item.phrase} near {zone.label}. It looked familiar because {hero.pronoun()} was already carrying {own_item}.",
        ),
        (
            "What was the twist?",
            f"The twist was that the lilac {item.label} looked like it might be {hero.id}'s, but it was not. {hero.id} checked carefully and realized someone else had lost it.",
        ),
        (
            f"Why did {hero.id} start a quest?",
            f"{hero.id} wanted to help the child who had lost the lilac {item.label}. The lost item made the unseen owner likely to feel worried, so the quest became a kind thing to do.",
        ),
        (
            f"How did the clue help?",
            f"The clue was {clue.label}. It gave {hero.id} and the helper a real way to search instead of guessing, which is why the quest felt careful rather than grabby.",
        ),
        (
            f"What lesson did {guardian.label_word} teach {hero.id}?",
            f"{guardian.label_word.capitalize()} taught {hero.id} not to snatch a thing just because it looks familiar. In a busy airport, the safe, kind way is to check first and ask a grown-up helper.",
        ),
    ]
    if outcome == "reunited":
        qa.append(
            (
                f"Did they find the owner before boarding?",
                f"Yes. With help from {helper.label}, they found {owner.id} and returned the lilac {item.label}. The owner's worry turned into relief as soon as the item was back.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} hand the item straight to its owner?",
                f"No. Boarding was moving too fast, so {hero.id} gave it to {helper.label} for a careful page and safe keeping. That still helped, because the right airport worker could finish the job properly.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["zone"].tags) | set(f["item_cfg"].tags) | set(f["clue"].tags) | set(f["helper_cfg"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_fits(I, C) :- item(I), clue(C), not needs_fabric(C), not needs_comfort(C).
clue_fits(I, C) :- item(I), clue(C), needs_fabric(C), fabric(I), not needs_comfort(C).
clue_fits(I, C) :- item(I), clue(C), needs_comfort(C), comfort(I), not needs_fabric(C).
clue_fits(I, C) :- item(I), clue(C), needs_fabric(C), fabric(I), needs_comfort(C), comfort(I).

available(Z, H) :- zone(Z), helper(H), serves(Z, H).
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.

valid(Z, I, C, H) :- zone(Z), item(I), clue(C), helper(H),
                     clue_fits(I, C), available(Z, H), sensible(H).

score(V) :- chosen_zone(Z), chosen_clue(C), chosen_helper(H), rush(R),
            difficulty(Z, D), strength(C, S), power(H, P), V = S + P - D - R.

outcome(reunited) :- score(V), V >= 1.
outcome(desk) :- score(V), V < 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for zone_id, zone in ZONES.items():
        lines.append(asp.fact("zone", zone_id))
        lines.append(asp.fact("difficulty", zone_id, zone.difficulty))
        for helper_id in sorted(zone.helpers):
            lines.append(asp.fact("serves", zone_id, helper_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.fabric:
            lines.append(asp.fact("fabric", item_id))
        if item.comfort:
            lines.append(asp.fact("comfort", item_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("strength", clue_id, clue.strength))
        if clue.needs_fabric:
            lines.append(asp.fact("needs_fabric", clue_id))
        if clue.needs_comfort:
            lines.append(asp.fact("needs_comfort", clue_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        lines.append(asp.fact("power", helper_id, helper.power))
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
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_zone", params.zone),
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_helper", params.helper),
            asp.fact("rush", params.rush),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a lilac airport lost-item quest in a nursery-rhyme mood."
    )
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--rush", type=int, choices=[0, 1, 2], help="how close boarding feels")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible airport quest combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _pick_owner(rng: random.Random, gender: str) -> str:
    return rng.choice(OWNER_NAMES_GIRL if gender == "girl" else OWNER_NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.zone and args.item and args.clue and args.helper:
        zone = ZONES[args.zone]
        item = ITEMS[args.item]
        clue = CLUES[args.clue]
        helper = HELPERS[args.helper]
        if not (clue_fits(item, clue) and helper_available(zone, helper.id) and helper.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(zone, item, clue, helper))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        helper = HELPERS[args.helper]
        zone = ZONES[args.zone] if args.zone else next(iter(ZONES.values()))
        item = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        raise StoryError(explain_rejection(zone, item, clue, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.zone is None or combo[0] == args.zone)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    zone_id, item_id, clue_id, helper_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    owner_gender = rng.choice(["girl", "boy"])
    return StoryParams(
        zone=zone_id,
        item=item_id,
        clue=clue_id,
        helper=helper_id,
        hero_name=_pick_name(rng, hero_gender),
        hero_gender=hero_gender,
        guardian=args.guardian or rng.choice(["mother", "father"]),
        helper_type=rng.choice(["agent_woman", "agent_man"]),
        owner_name=_pick_owner(rng, owner_gender),
        owner_gender=owner_gender,
        rush=args.rush if args.rush is not None else rng.randint(0, 2),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        zone = ZONES[params.zone]
        item = ITEMS[params.item]
        clue = CLUES[params.clue]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if helper.sense < SENSE_MIN or not helper_available(zone, helper.id) or not clue_fits(item, clue):
        raise StoryError(explain_rejection(zone, item, clue, helper))

    world = tell(
        zone=zone,
        item=item,
        clue=clue,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guardian_type=params.guardian,
        helper_type=params.helper_type,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        rush=params.rush,
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {h.id for h in sensible_helpers()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible helpers match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible helpers: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (zone, item, clue, helper) combos:\n")
        for zone, item, clue, helper in combos:
            print(f"  {zone:12} {item:8} {clue:16} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.item} at {p.zone} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
