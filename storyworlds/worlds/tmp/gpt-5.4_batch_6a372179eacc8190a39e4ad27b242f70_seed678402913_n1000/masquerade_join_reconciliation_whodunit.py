#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/masquerade_join_reconciliation_whodunit.py
=====================================================================

A small standalone story world for a child-facing masquerade whodunit with a
reconciliation ending.

Premise
-------
At a masquerade party, one child notices that a special party object has gone
missing just before the music starts. A clue seems to point toward a friend.
The children investigate, discover a kinder truth, and reconcile in time to
join the final dance.

This world is intentionally narrow. The reasonableness gate only allows clues
and causes that produce a plausible tiny mystery:

* the clue must honestly seem to point at the suspected friend
* the true cause must explain why the item disappeared without malice
* the chosen reconciliation move must fit the discovered truth

The script supports random generation, pinned parameters, Q&A, JSON, an inline
ASP twin, verification, and trace output.

Run it
------
    python storyworlds/worlds/gpt-5.4/masquerade_join_reconciliation_whodunit.py
    python storyworlds/worlds/gpt-5.4/masquerade_join_reconciliation_whodunit.py --venue ballroom --item bell --clue glitter
    python storyworlds/worlds/gpt-5.4/masquerade_join_reconciliation_whodunit.py --item fan --cause dropped_under_stage
    python storyworlds/worlds/gpt-5.4/masquerade_join_reconciliation_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/masquerade_join_reconciliation_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/masquerade_join_reconciliation_whodunit.py --verify
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
# File lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
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
        female = {"girl", "mother", "woman", "hostess"}
        male = {"boy", "father", "man", "host"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    place: str
    opening: str
    music: str
    hiding_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PartyItem:
    id: str
    label: str
    phrase: str
    shine: str
    rest_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    mark: str
    found_at: str
    points_to: str
    question: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    action: str
    reveal: str
    location: str
    innocent_reason: str
    needs_host: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Reconcile:
    id: str
    apology: str
    response: str
    join_line: str
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


def _r_suspicion_hurts(world: World) -> list[str]:
    accuser = world.entities.get("hero")
    suspect = world.entities.get("friend")
    if accuser is None or suspect is None:
        return []
    if accuser.memes["suspects"] < THRESHOLD:
        return []
    sig = ("hurt", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    suspect.memes["distance"] += 1
    return ["__hurt__"]


def _r_truth_brings_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if world.facts.get("truth_found") is not True:
        return []
    sig = ("relief", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    return []


def _r_apology_repairs(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if hero.memes["apologized"] < THRESHOLD:
        return []
    sig = ("repair", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] = 0.0
    friend.memes["distance"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    return []


def _r_joining_raises_joy(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if hero.meters["joined_dance"] < THRESHOLD or friend.meters["joined_dance"] < THRESHOLD:
        return []
    sig = ("joy", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="suspicion_hurts", tag="social", apply=_r_suspicion_hurts),
    Rule(name="truth_brings_relief", tag="social", apply=_r_truth_brings_relief),
    Rule(name="apology_repairs", tag="social", apply=_r_apology_repairs),
    Rule(name="joining_raises_joy", tag="social", apply=_r_joining_raises_joy),
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
        for line in produced:
            world.say(line)
    return produced


VENUES = {
    "ballroom": Venue(
        id="ballroom",
        place="the moonlit ballroom",
        opening="Paper stars swung from the ceiling, and every child wore a bright masquerade mask.",
        music="the violin tune for the final circle dance",
        hiding_spot="under the edge of the little stage",
        ending_image="the paper stars turning slowly over the dancers",
        tags={"ballroom", "dance"},
    ),
    "garden": Venue(
        id="garden",
        place="the lantern garden",
        opening="Lanterns glowed in the bushes, and every child looked mysterious behind a masquerade mask.",
        music="the soft drumbeat for the lantern dance",
        hiding_spot="beneath the ribbon bench",
        ending_image="the lanterns glowing over the grass as the children danced",
        tags={"garden", "dance"},
    ),
    "hall": Venue(
        id="hall",
        place="the echoing school hall",
        opening="Silvery streamers rustled overhead, and the children whispered through their masquerade masks.",
        music="the piano song for the joining dance",
        hiding_spot="behind the coat basket by the wall",
        ending_image="the streamers trembling above the laughing line of dancers",
        tags={"hall", "dance"},
    ),
}

ITEMS = {
    "bell": PartyItem(
        id="bell",
        label="silver bell",
        phrase="a little silver bell for the first dance",
        shine="It flashed whenever it caught the light.",
        rest_place="on the host table",
        tags={"bell", "metal"},
    ),
    "fan": PartyItem(
        id="fan",
        label="velvet fan",
        phrase="a velvet fan for the queen costume game",
        shine="Its tiny beads winked like rain.",
        rest_place="beside the punch bowl",
        tags={"fan", "velvet"},
    ),
    "brooch": PartyItem(
        id="brooch",
        label="moon brooch",
        phrase="a moon-shaped brooch for the lead costume",
        shine="Its smooth silver edge looked like a slice of moon.",
        rest_place="on a folded napkin near the cake",
        tags={"brooch", "moon"},
    ),
}

CLUES = {
    "glitter": Clue(
        id="glitter",
        mark="a line of silver glitter",
        found_at="on the floor near the empty spot",
        points_to="the friend's star cloak",
        question="Who else at the party had silver glitter on a costume?",
        tags={"glitter", "cloak"},
    ),
    "blue_ribbon": Clue(
        id="blue_ribbon",
        mark="a loose blue ribbon",
        found_at="curled beside the tray",
        points_to="the friend's blue mask ties",
        question="Whose costume had blue ribbon that looked just like this?",
        tags={"ribbon", "mask"},
    ),
    "icing": Clue(
        id="icing",
        mark="a dot of lemon icing",
        found_at="on the tablecloth",
        points_to="the friend's cake plate",
        question="Who had just been near the cake with icing on a finger?",
        tags={"icing", "cake"},
    ),
}

CAUSES = {
    "dropped_under_stage": Cause(
        id="dropped_under_stage",
        action="while helping carry decorations, someone brushed the item off the table",
        reveal="They followed the trail and found the item tucked in the dust",
        location="under the edge of the little stage",
        innocent_reason="It had slipped out of sight by accident, not because anyone took it",
        tags={"search", "accident"},
    ),
    "host_moved_it": Cause(
        id="host_moved_it",
        action="the host moved the item to keep it safe before the music began",
        reveal="The host opened a small basket and lifted the missing item from a cloth napkin",
        location="inside the host's keeping basket",
        innocent_reason="The item had been protected on purpose, but no one had said so in the rush",
        needs_host=True,
        tags={"host", "safekeeping"},
    ),
    "caught_in_costume": Cause(
        id="caught_in_costume",
        action="the item snagged in a hanging costume sash when children twirled past",
        reveal="They spotted a gleam and found the missing item caught in the sash",
        location="in the fringe of a costume stand",
        innocent_reason="It had been trapped by cloth, so the clue only looked suspicious",
        tags={"sash", "search"},
    ),
}

RECONCILES = {
    "brave_apology": Reconcile(
        id="brave_apology",
        apology='"{friend}, I was wrong," {hero} said. "I saw the clue and hurried to blame you. I am sorry."',
        response='"{hero}, I felt sad when you thought that," {friend} said, "but I know you were trying to help. We found the truth now."',
        join_line='Then {friend} held out a hand. "Come on. Let\'s join the dance together before the music ends."',
        tags={"apology", "forgiveness"},
    ),
    "shared_laugh": Reconcile(
        id="shared_laugh",
        apology='"{friend}, I should have asked instead of accusing," {hero} said. "{cause_line} I am sorry."',
        response='The friend\'s mouth twitched, and then both children let out the same relieved little laugh. "Mysteries are harder in masks," {friend} said.',
        join_line='"No more guessing," {friend} added. "Let\'s join the dance the right way -- side by side."',
        tags={"apology", "laugh"},
    ),
    "host_nudge": Reconcile(
        id="host_nudge",
        apology='The host touched {hero}\'s shoulder. "{friend} deserves kind words," {host_word} said. {hero_cap} took a breath. "I am sorry I blamed you."',
        response='"{hero}, thank you for saying that," {friend} said. "I still wanted to be your partner."',
        join_line='"Then let the mystery end with music," said the host. "Now join the circle."',
        tags={"host", "apology"},
    ),
}

HERO_NAMES = ["Nina", "Ruby", "Ivy", "Clara", "Milo", "Owen", "Theo", "Luca"]
FRIEND_NAMES = ["Ada", "Mina", "Poppy", "Tess", "Finn", "Jude", "Ben", "Max"]
TRAITS = ["careful", "curious", "eager", "thoughtful", "bright"]
MASKS = ["fox", "moon", "peacock", "cat", "owl", "lion"]


@dataclass
class StoryParams:
    venue: str
    item: str
    clue: str
    cause: str
    reconcile: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    host_type: str
    hero_trait: str
    friend_trait: str
    hero_mask: str
    friend_mask: str
    seed: Optional[int] = None


def clue_points_to_friend(clue_id: str) -> bool:
    return clue_id in CLUES


def cause_fits_item(cause_id: str, item_id: str) -> bool:
    if cause_id == "host_moved_it":
        return item_id in {"bell", "brooch"}
    if cause_id == "dropped_under_stage":
        return item_id in {"bell", "fan", "brooch"}
    if cause_id == "caught_in_costume":
        return item_id in {"fan", "brooch"}
    return False


def clue_fits_cause(clue_id: str, cause_id: str) -> bool:
    allowed = {
        "glitter": {"caught_in_costume", "dropped_under_stage"},
        "blue_ribbon": {"caught_in_costume", "host_moved_it"},
        "icing": {"host_moved_it", "dropped_under_stage"},
    }
    return cause_id in allowed.get(clue_id, set())


def reconcile_fits_cause(reconcile_id: str, cause_id: str) -> bool:
    if reconcile_id == "host_nudge":
        return cause_id == "host_moved_it"
    if reconcile_id == "shared_laugh":
        return cause_id in {"caught_in_costume", "dropped_under_stage"}
    if reconcile_id == "brave_apology":
        return cause_id in CAUSES
    return False


def valid_combo(venue_id: str, item_id: str, clue_id: str, cause_id: str, reconcile_id: str) -> bool:
    return (
        venue_id in VENUES
        and item_id in ITEMS
        and clue_points_to_friend(clue_id)
        and cause_fits_item(cause_id, item_id)
        and clue_fits_cause(clue_id, cause_id)
        and reconcile_fits_cause(reconcile_id, cause_id)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for venue_id in VENUES:
        for item_id in ITEMS:
            for clue_id in CLUES:
                for cause_id in CAUSES:
                    for reconcile_id in RECONCILES:
                        if valid_combo(venue_id, item_id, clue_id, cause_id, reconcile_id):
                            out.append((venue_id, item_id, clue_id, cause_id, reconcile_id))
    return out


def explain_rejection(item_id: str, clue_id: str, cause_id: str, reconcile_id: str) -> str:
    item = ITEMS.get(item_id)
    clue = CLUES.get(clue_id)
    cause = CAUSES.get(cause_id)
    if item is None or clue is None or cause is None or reconcile_id not in RECONCILES:
        return "(No story: one of the requested ids is not known to this world.)"
    if not cause_fits_item(cause_id, item_id):
        return (
            f"(No story: {cause.action} is not a good explanation for the {item.label}. "
            f"Pick a cause that could really hide or move that object.)"
        )
    if not clue_fits_cause(clue_id, cause_id):
        return (
            f"(No story: {clue.mark} would not naturally lead into the truth "
            f"that {cause.innocent_reason.lower()}. The clue and answer must match.)"
        )
    if not reconcile_fits_cause(reconcile_id, cause_id):
        return (
            f"(No story: the reconciliation move '{reconcile_id}' does not fit "
            f"the way this mystery is solved.)"
        )
    return "(No story: this combination is not reasonable.)"


def suspect_prediction(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["suspects"] += 1
    propagate(sim, narrate=False)
    friend = sim.get("friend")
    return {
        "hurt": friend.memes["hurt"] >= THRESHOLD,
        "distance": friend.memes["distance"],
    }


def introduce(world: World, venue: Venue, hero: Entity, friend: Entity, host: Entity, item: PartyItem) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {venue.place}, {venue.opening} {hero.id} wore a {hero.attrs['mask']} mask, "
        f"and {friend.id} wore a {friend.attrs['mask']} mask."
    )
    world.say(
        f"The host had set out {item.phrase}. {item.shine} Soon it would be needed for {venue.music}."
    )


def vanish(world: World, item: PartyItem) -> None:
    world.get("missing_item").meters["missing"] += 1
    world.say(
        f"But when {item.label} was needed, the space where it had rested looked suddenly bare."
    )
    world.say(f"{item.label.capitalize()} was gone.")


def notice_clue(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    pred = suspect_prediction(world)
    hero.memes["suspects"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f"{hero.id} spotted {clue.mark} {clue.found_at}. "
        f"{hero.pronoun().capitalize()} remembered {clue.points_to} and whispered, "
        f'"{clue.question}"'
    )
    world.say(
        f"The clue made {hero.id} look at {friend.id} with worried detective eyes."
    )


def accuse(world: World, hero: Entity, friend: Entity, item: PartyItem) -> None:
    world.say(
        f'"{friend.id}, did you take the {item.label}?" {hero.id} asked.'
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s shoulders drooped. "
            f'"No," {friend.pronoun()} said. "I wanted to join the dance with you. Why would I hide it?"'
        )
    else:
        world.say(f'"No," {friend.id} said softly.')


def search(world: World, hero: Entity, friend: Entity, host: Entity, venue: Venue, cause: Cause, item: PartyItem) -> None:
    hero.memes["resolve"] += 1
    friend.memes["resolve"] += 1
    host.memes["attention"] += 1
    world.say(
        f"Instead of arguing, the three of them followed the mystery together. "
        f"They checked the table, the curtain hem, and {venue.hiding_spot}."
    )
    if cause.id == "host_moved_it":
        world.say(
            f"Then the host blinked and remembered something. {host.pronoun().capitalize()} had moved the {item.label} to a safer place before the crowd pressed in."
        )
    else:
        world.say(
            f"As they searched, it became clear that {cause.action}."
        )


def reveal_truth(world: World, hero: Entity, friend: Entity, host: Entity, cause: Cause, item: PartyItem) -> None:
    world.facts["truth_found"] = True
    propagate(world, narrate=False)
    missing = world.get("missing_item")
    missing.meters["missing"] = 0.0
    missing.meters["found"] += 1
    world.facts["truth_found"] = True
    propagate(world, narrate=False)
    if cause.id == "host_moved_it":
        world.say(
            f"{cause.reveal}. {host.pronoun().capitalize()} held it up, and everyone saw at once that no one had stolen anything."
        )
    else:
        world.say(
            f"{cause.reveal} {cause.location}. It was the very same {item.label}, and suddenly the whole mystery looked different."
        )
    world.say(
        f"{cause.innocent_reason}. The clue had only pointed in the wrong direction."
    )


def reconcile_scene(world: World, hero: Entity, friend: Entity, host: Entity, reconcile: Reconcile, cause: Cause) -> None:
    hero.memes["apologized"] += 1
    propagate(world, narrate=False)
    cause_line = "The clue tricked me"
    apology = reconcile.apology.format(
        hero=hero.id,
        hero_cap=hero.id,
        friend=friend.id,
        cause_line=cause_line,
        host_word=host.label_word.capitalize(),
    )
    response = reconcile.response.format(
        hero=hero.id,
        friend=friend.id,
        host_word=host.label_word.capitalize(),
    )
    join_line = reconcile.join_line.format(
        hero=hero.id,
        friend=friend.id,
    )
    world.say(apology)
    world.say(response)
    world.say(join_line)


def join_dance(world: World, hero: Entity, friend: Entity, venue: Venue) -> None:
    hero.meters["joined_dance"] += 1
    friend.meters["joined_dance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So the two children ran to the circle just as the first notes of {venue.music} began."
    )
    world.say(
        f"They joined hands, stepped into the line, and solved the last part of the mystery by dancing together under {venue.ending_image}."
    )


def tell(
    venue: Venue,
    item: PartyItem,
    clue: Clue,
    cause: Cause,
    reconcile: Reconcile,
    hero_name: str = "Nina",
    hero_gender: str = "girl",
    friend_name: str = "Finn",
    friend_gender: str = "boy",
    host_type: str = "mother",
    hero_trait: str = "curious",
    friend_trait: str = "thoughtful",
    hero_mask: str = "fox",
    friend_mask: str = "owl",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="detective",
        traits=[hero_trait],
        attrs={"mask": hero_mask},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[friend_trait],
        attrs={"mask": friend_mask},
    ))
    host = world.add(Entity(
        id="host",
        kind="character",
        type=host_type,
        label="the host",
        role="host",
    ))
    missing_item = world.add(Entity(
        id="missing_item",
        kind="thing",
        type="party_item",
        label=item.label,
        phrase=item.phrase,
    ))

    world.facts.update(
        venue=venue,
        item=item,
        clue=clue,
        cause=cause,
        reconcile=reconcile,
        hero=hero,
        friend=friend,
        host=host,
        truth_found=False,
    )

    introduce(world, venue, hero, friend, host, item)
    world.para()
    vanish(world, item)
    notice_clue(world, hero, friend, clue)
    accuse(world, hero, friend, item)
    world.para()
    search(world, hero, friend, host, venue, cause, item)
    reveal_truth(world, hero, friend, host, cause, item)
    world.para()
    reconcile_scene(world, hero, friend, host, reconcile, cause)
    join_dance(world, hero, friend, venue)

    world.facts.update(
        hero_name=hero_name,
        friend_name=friend_name,
        host_type=host_type,
        missing_resolved=missing_item.meters["found"] >= THRESHOLD,
        reconciled=hero.memes["apologized"] >= THRESHOLD and friend.memes["distance"] < THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "masquerade": [
        (
            "What is a masquerade?",
            "A masquerade is a party where people wear masks and costumes. The masks can make everyone look mysterious and playful."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, a clue points you toward an answer, though sometimes it points the wrong way at first."
        )
    ],
    "apology": [
        (
            "Why is saying sorry important?",
            "Saying sorry helps repair hurt feelings after you make a mistake. It shows that you understand the hurt and want to make things better."
        )
    ],
    "forgiveness": [
        (
            "What does forgiveness mean?",
            "Forgiveness means choosing not to keep holding on to anger after someone truly says sorry and tries to make things right. It helps friends start again."
        )
    ],
    "dance": [
        (
            "What does it mean to join a dance?",
            "To join a dance means to step in and take part with the other dancers. It shows you are together in the same game or celebration."
        )
    ],
    "bell": [
        (
            "What is a bell used for at a party?",
            "A bell can be rung to signal that something is beginning. It helps everyone know it is time to listen or gather."
        )
    ],
    "fan": [
        (
            "What is a fan?",
            "A fan is something you wave in your hand to make a little breeze. Fancy fans can also be used as costume pieces."
        )
    ],
    "brooch": [
        (
            "What is a brooch?",
            "A brooch is a small piece of jewelry that pins onto clothing. It can sparkle and decorate a costume."
        )
    ],
}
KNOWLEDGE_ORDER = ["masquerade", "clue", "bell", "fan", "brooch", "apology", "forgiveness", "dance"]


def generation_prompts(world: World) -> list[str]:
    venue = world.facts["venue"]
    item = world.facts["item"]
    clue = world.facts["clue"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f'Write a child-friendly whodunit set at a masquerade party where a {item.label} goes missing and a clue seems to point to a friend.',
        f"Tell a gentle mystery about {hero.label} and {friend.label} at {venue.place}, where a mistaken accusation is repaired and the children join the dance at the end.",
        f'Write a short reconciliation story in whodunit style using the words "masquerade" and "join", with one misleading clue and a warm ending.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    venue = world.facts["venue"]
    item = world.facts["item"]
    clue = world.facts["clue"]
    cause = world.facts["cause"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    host = world.facts["host"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label} at a masquerade party, with the host helping near the end. The mystery begins when the {item.label} disappears."
        ),
        (
            f"What went missing at the party?",
            f"The missing object was the {item.label}. It had been needed for {venue.music}, so everyone noticed when it was gone."
        ),
        (
            "Why did the mystery seem to point toward the friend?",
            f"{hero.label} found {clue.mark} {clue.found_at}, and that seemed to match {clue.points_to}. The clue looked convincing, so {hero.label} hurried to suspect {friend.label}."
        ),
        (
            "What was the real truth?",
            f"The real truth was that {cause.innocent_reason.lower()}. When they kept searching, they found the {item.label} {cause.location}."
        ),
        (
            "How were the children reconciled?",
            f"{hero.label} apologized for blaming {friend.label} too quickly, and {friend.label} answered kindly. Their friendship changed because the truth replaced suspicion and the apology repaired the hurt."
        ),
        (
            "How did the story end?",
            f"The children hurried back in time to join the dance together. The ending image shows that the mystery is over because they are side by side under {venue.ending_image}."
        ),
    ]
    if world.facts.get("predicted_hurt"):
        qa.append(
            (
                f"Why did {friend.label} feel sad when {hero.label} asked about the {item.label}?",
                f"{friend.label} felt hurt because the question sounded like blame before the truth was known. A missing object and a misleading clue made the accusation feel serious, even though {friend.pronoun()} had done nothing wrong."
            )
        )
    if cause.needs_host:
        qa.append(
            (
                f"How did the host help solve the mystery?",
                f"The host remembered moving the {item.label} to keep it safe. That memory broke the false guess and showed that nobody had stolen anything."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"masquerade", "clue", "apology", "forgiveness", "dance"}
    tags |= set(world.facts["item"].tags)
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
        bits = [f"label={ent.label!r}"] if ent.label else []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="ballroom",
        item="bell",
        clue="glitter",
        cause="dropped_under_stage",
        reconcile="brave_apology",
        hero_name="Nina",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        host_type="mother",
        hero_trait="curious",
        friend_trait="thoughtful",
        hero_mask="fox",
        friend_mask="owl",
    ),
    StoryParams(
        venue="garden",
        item="brooch",
        clue="blue_ribbon",
        cause="host_moved_it",
        reconcile="host_nudge",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Mina",
        friend_gender="girl",
        host_type="father",
        hero_trait="eager",
        friend_trait="bright",
        hero_mask="lion",
        friend_mask="peacock",
    ),
    StoryParams(
        venue="hall",
        item="fan",
        clue="glitter",
        cause="caught_in_costume",
        reconcile="shared_laugh",
        hero_name="Ruby",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        host_type="mother",
        hero_trait="careful",
        friend_trait="eager",
        hero_mask="moon",
        friend_mask="cat",
    ),
    StoryParams(
        venue="ballroom",
        item="brooch",
        clue="icing",
        cause="dropped_under_stage",
        reconcile="brave_apology",
        hero_name="Luca",
        hero_gender="boy",
        friend_name="Poppy",
        friend_gender="girl",
        host_type="father",
        hero_trait="bright",
        friend_trait="thoughtful",
        hero_mask="owl",
        friend_mask="fox",
    ),
]


ASP_RULES = r"""
clue_points_to_friend(C) :- clue(C).

cause_fits_item(host_moved_it, bell).
cause_fits_item(host_moved_it, brooch).
cause_fits_item(dropped_under_stage, bell).
cause_fits_item(dropped_under_stage, fan).
cause_fits_item(dropped_under_stage, brooch).
cause_fits_item(caught_in_costume, fan).
cause_fits_item(caught_in_costume, brooch).

clue_fits_cause(glitter, caught_in_costume).
clue_fits_cause(glitter, dropped_under_stage).
clue_fits_cause(blue_ribbon, caught_in_costume).
clue_fits_cause(blue_ribbon, host_moved_it).
clue_fits_cause(icing, host_moved_it).
clue_fits_cause(icing, dropped_under_stage).

reconcile_fits_cause(host_nudge, host_moved_it).
reconcile_fits_cause(shared_laugh, caught_in_costume).
reconcile_fits_cause(shared_laugh, dropped_under_stage).
reconcile_fits_cause(brave_apology, C) :- cause(C).

valid(V, I, Cl, Ca, R) :-
    venue(V), item(I), clue(Cl), cause(Ca), reconcile(R),
    clue_points_to_friend(Cl),
    cause_fits_item(Ca, I),
    clue_fits_cause(Cl, Ca),
    reconcile_fits_cause(R, Ca).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for reconcile_id in RECONCILES:
        lines.append(asp.fact("reconcile", reconcile_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover - CLI verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        parser = build_parser()
        args = parser.parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolved story was empty")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as exc:  # pragma: no cover - CLI verification path
        rc = 1
        print(f"DEFAULT SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a masquerade whodunit with reconciliation. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--reconcile", choices=RECONCILES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--host-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    female_pool = [n for n in HERO_NAMES + FRIEND_NAMES if n not in {avoid}]
    male_pool = [n for n in HERO_NAMES + FRIEND_NAMES if n not in {avoid}]
    if gender == "girl":
        pool = [n for n in female_pool if n in {"Nina", "Ruby", "Ivy", "Clara", "Ada", "Mina", "Poppy", "Tess"}]
    else:
        pool = [n for n in male_pool if n in {"Milo", "Owen", "Theo", "Luca", "Finn", "Jude", "Ben", "Max"}]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.clue and args.cause and args.reconcile:
        if not valid_combo(args.venue or next(iter(VENUES)), args.item, args.clue, args.cause, args.reconcile):
            raise StoryError(explain_rejection(args.item, args.clue, args.cause, args.reconcile))
    elif args.item and args.clue and args.cause:
        if not (cause_fits_item(args.cause, args.item) and clue_fits_cause(args.clue, args.cause)):
            reconcile_probe = args.reconcile or next(iter(RECONCILES))
            raise StoryError(explain_rejection(args.item, args.clue, args.cause, reconcile_probe))
    elif args.item and args.cause:
        if not cause_fits_item(args.cause, args.item):
            reconcile_probe = args.reconcile or next(iter(RECONCILES))
            clue_probe = args.clue or next(iter(CLUES))
            raise StoryError(explain_rejection(args.item, clue_probe, args.cause, reconcile_probe))
    elif args.clue and args.cause:
        if not clue_fits_cause(args.clue, args.cause):
            reconcile_probe = args.reconcile or next(iter(RECONCILES))
            item_probe = args.item or next(iter(ITEMS))
            raise StoryError(explain_rejection(item_probe, args.clue, args.cause, reconcile_probe))
    if args.reconcile and args.cause and not reconcile_fits_cause(args.reconcile, args.cause):
        item_probe = args.item or next(iter(ITEMS))
        clue_probe = args.clue or next(iter(CLUES))
        raise StoryError(explain_rejection(item_probe, clue_probe, args.cause, args.reconcile))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
        and (args.cause is None or combo[3] == args.cause)
        and (args.reconcile is None or combo[4] == args.reconcile)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, item_id, clue_id, cause_id, reconcile_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = pick_name(rng, hero_gender)
    friend_name = pick_name(rng, friend_gender, avoid=hero_name)
    host_type = args.host_type or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    hero_mask, friend_mask = rng.sample(MASKS, 2)
    return StoryParams(
        venue=venue_id,
        item=item_id,
        clue=clue_id,
        cause=cause_id,
        reconcile=reconcile_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        host_type=host_type,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
        hero_mask=hero_mask,
        friend_mask=friend_mask,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        item = ITEMS[params.item]
        clue = CLUES[params.clue]
        cause = CAUSES[params.cause]
        reconcile = RECONCILES[params.reconcile]
    except KeyError as exc:
        raise StoryError(f"(No story: unknown parameter key {exc!s}.)") from None

    if not valid_combo(params.venue, params.item, params.clue, params.cause, params.reconcile):
        raise StoryError(explain_rejection(params.item, params.clue, params.cause, params.reconcile))

    world = tell(
        venue=venue,
        item=item,
        clue=clue,
        cause=cause,
        reconcile=reconcile,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        host_type=params.host_type,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
        hero_mask=params.hero_mask,
        friend_mask=params.friend_mask,
    )
    story_text = world.render()
    if not story_text.strip():
        raise StoryError("(No story: generation produced empty prose.)")
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, item, clue, cause, reconcile) combos:\n")
        for venue_id, item_id, clue_id, cause_id, reconcile_id in combos:
            print(f"  {venue_id:9} {item_id:7} {clue_id:12} {cause_id:18} {reconcile_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = (
                f"### {p.hero_name} and {p.friend_name}: {p.item} / {p.clue} / "
                f"{p.cause} at {p.venue}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
