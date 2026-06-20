#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jiggle_didey_sound_effects_kindness_happy_ending.py
==============================================================================

A standalone story world for a gentle detective-style mystery: two children hear
a strange little sound -- "jiggle-jiggle... didey-ding!" -- and solve the case
by being observant, patient, and kind.

The world is deliberately small and constraint-checked. A mystery is only valid
when:
- the place can plausibly host it, and
- the chosen response actually matches the obstacle hiding the source, and
- the response passes a simple kindness/common-sense gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/jiggle_didey_sound_effects_kindness_happy_ending.py
    python storyworlds/worlds/gpt-5.4/jiggle_didey_sound_effects_kindness_happy_ending.py --place garden --mystery basket_kitten
    python storyworlds/worlds/gpt-5.4/jiggle_didey_sound_effects_kindness_happy_ending.py --response shake_harder
    python storyworlds/worlds/gpt-5.4/jiggle_didey_sound_effects_kindness_happy_ending.py --all --qa
    python storyworlds/worlds/gpt-5.4/jiggle_didey_sound_effects_kindness_happy_ending.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up.
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
    role: str = ""
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    scene: str
    hide_desc: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    kind: str                   # animal | item
    label: str
    article: str
    hideout: str
    obstacle: str
    sound1: str
    sound2: str
    clue: str
    fear_text: str
    reveal_text: str
    kind_text: str
    owner_kind: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        phrase = f"{self.article} {self.label}"
        return phrase[0].upper() + phrase[1:]


@dataclass
class Response:
    id: str
    sense: int
    handles: set[str]
    action_text: str
    qa_text: str
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

    def characters(self) -> list[Entity]:
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
        clone = World(self.place)
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


def _r_hidden_sound(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    place = world.get("place")
    if source.meters["hidden"] >= THRESHOLD and source.meters["moving"] >= THRESHOLD:
        sig = ("sound", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["clue_sound"] += 1
            for who in ("detective", "partner"):
                world.get(who).memes["curiosity"] += 1
            out.append("__sound__")
    return out


def _r_kind_calm(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    detective = world.get("detective")
    partner = world.get("partner")
    if source.memes["worry"] >= THRESHOLD and detective.memes["kindness"] >= THRESHOLD:
        sig = ("calm", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            source.memes["trust"] += 1
            partner.memes["kindness"] += 1
            out.append("__calm__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["freed"] >= THRESHOLD:
        sig = ("relief", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            source.memes["worry"] = 0.0
            source.memes["relief"] += 1
            world.get("detective").memes["relief"] += 1
            world.get("partner").memes["relief"] += 1
            if "owner" in world.entities:
                world.get("owner").memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("hidden_sound", "physical", _r_hidden_sound),
    Rule("kind_calm", "social", _r_kind_calm),
    Rule("relief", "social", _r_relief),
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
        for s in produced:
            world.say(s)
    return produced


def mystery_supported(place: Place, mystery: Mystery) -> bool:
    return mystery.id in place.supports


def response_matches(response: Response, mystery: Mystery) -> bool:
    return mystery.obstacle in response.handles


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if not mystery_supported(place, mystery):
                continue
            for rid, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and response_matches(response, mystery):
                    combos.append((pid, mid, rid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    mystery = MYSTERIES[params.mystery]
    return "rescued" if mystery.kind == "animal" else "returned"


def predict_case(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["moving"] += 1
    propagate(sim, narrate=False)
    return {
        "heard_sound": sim.get("place").meters["clue_sound"] >= THRESHOLD,
        "kind_help_needed": mystery.kind == "animal" or bool(mystery.owner_kind),
    }


def setup_case(world: World, detective: Entity, partner: Entity, place: Place) -> None:
    detective.memes["play"] += 1
    partner.memes["play"] += 1
    world.say(
        f"After lunch, Detective {detective.id} and Detective {partner.id} opened their tiny casebook at {place.label}. "
        f"{place.scene}"
    )
    world.say(
        f"They were not hunting robbers or jewels. They were looking for little mysteries that needed careful eyes and kind hearts."
    )


def first_clue(world: World, detective: Entity, partner: Entity, mystery: Mystery, place: Place) -> None:
    source = world.get("source")
    source.meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then both detectives froze. From {place.hide_desc} came a soft sound: "
        f'"{mystery.sound1}! {mystery.sound2}!"'
    )
    world.say(
        f'"A clue," whispered {detective.id}. {partner.id} tipped {partner.pronoun("possessive")} head and listened again.'
    )


def inspect_clue(world: World, detective: Entity, partner: Entity, mystery: Mystery) -> None:
    pred = predict_case(world, mystery)
    world.facts["predicted_sound"] = pred["heard_sound"]
    detective.memes["thinking"] += 1
    partner.memes["thinking"] += 1
    world.say(
        f"They followed the sound to {mystery.hideout}. There, {detective.id} spotted {mystery.clue}."
    )
    if pred["kind_help_needed"]:
        world.say(
            f'"This is not a bad-guy case," {detective.id} murmured. "It is a help-someone case."'
        )


def speak_kindly(world: World, detective: Entity, partner: Entity, mystery: Mystery) -> None:
    detective.memes["kindness"] += 1
    partner.memes["kindness"] += 1
    source = world.get("source")
    source.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{partner.id} knelt down and used {partner.pronoun("possessive")} gentlest voice. "{mystery.kind_text}"'
    )
    world.say(mystery.fear_text)


def solve_case(world: World, detective: Entity, partner: Entity, mystery: Mystery, response: Response) -> None:
    source = world.get("source")
    source.meters["hidden"] = 0.0
    source.meters["freed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Very slowly, {detective.id} {response.action_text}, while {partner.id} stayed close and kept talking softly."
    )
    world.say(mystery.reveal_text)


def close_animal_case(world: World, detective: Entity, partner: Entity, mystery: Mystery) -> None:
    source = world.get("source")
    detective.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(
        f"{detective.id} checked that {mystery.article} {mystery.label} was safe, and {partner.id} stroked it once with one careful finger."
    )
    if source.memes["trust"] >= THRESHOLD:
        world.say(
            f"Soon the frightened little sound-maker was not frightened anymore."
        )


def close_item_case(world: World, detective: Entity, partner: Entity, mystery: Mystery, owner: Entity) -> None:
    detective.memes["pride"] += 1
    partner.memes["pride"] += 1
    owner.memes["sad"] += 1
    world.say(
        f"Inside was {mystery.article} {mystery.label}, still making its tiny noise when the charms bumped together."
    )
    world.say(
        f"Just then {owner.id} came hurrying over with worried eyes. {mystery.owner_kind}"
    )
    world.say(
        f'{detective.id} held it out at once. "Case solved," {detective.pronoun()} said, and {owner.id} smiled so hard that the whole mystery turned bright.'
    )


def happy_ending(world: World, detective: Entity, partner: Entity, mystery: Mystery, place: Place) -> None:
    if mystery.kind == "animal":
        world.say(
            f'The detectives wrote in their casebook: "Mystery solved with kindness." Then they heard one last happy little "{mystery.sound2}!" as the afternoon grew warm and peaceful.'
        )
    else:
        world.say(
            f'The detectives wrote in their casebook: "The best clues are the ones that help someone smile again." All around {place.label}, the day felt lighter.'
        )
    world.say(
        f"{detective.id} and {partner.id} walked on, ready for the next tiny case, but pleased that this one had ended with gentle hands and happy hearts."
    )


def tell(
    place: Place,
    mystery: Mystery,
    response: Response,
    detective_name: str = "Lila",
    detective_gender: str = "girl",
    partner_name: str = "Owen",
    partner_gender: str = "boy",
    owner_name: str = "Mina",
    owner_gender: str = "girl",
) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    world.add(Entity(id="place", type="place", label=place.label))
    source = world.add(Entity(id="source", type=mystery.kind, label=mystery.label, role="source"))
    source.meters["hidden"] = 1.0
    if mystery.kind == "animal":
        source.memes["worry"] = 1.0
    if mystery.kind == "item":
        owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
        world.facts["owner"] = owner
    else:
        owner = None

    setup_case(world, detective, partner, place)
    world.para()
    first_clue(world, detective, partner, mystery, place)
    inspect_clue(world, detective, partner, mystery)
    speak_kindly(world, detective, partner, mystery)

    world.para()
    solve_case(world, detective, partner, mystery, response)
    if mystery.kind == "animal":
        close_animal_case(world, detective, partner, mystery)
    else:
        assert owner is not None
        close_item_case(world, detective, partner, mystery, owner)

    world.para()
    happy_ending(world, detective, partner, mystery, place)

    world.facts.update(
        detective=detective,
        partner=partner,
        place_cfg=place,
        mystery=mystery,
        response=response,
        source=source,
        outcome="rescued" if mystery.kind == "animal" else "returned",
        owner=owner,
        kindness_used=detective.memes["kindness"] >= THRESHOLD,
        trust_built=source.memes["trust"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden": Place(
        "garden",
        "the garden",
        "Rows of marigolds glowed by the path, and the old bench stood beside a stack of picnic things.",
        "the bench and the picnic things",
        supports={"basket_kitten"},
    ),
    "library": Place(
        "library",
        "the library corner",
        "Sunlight made gold squares on the rug, and a coat rack stood near the window beside the lost-and-found shelf.",
        "the coat rack",
        supports={"coat_puppy", "lunchbox_bracelet"},
    ),
    "school_hall": Place(
        "school_hall",
        "the school hall",
        "Rain boots lined the wall, lunch boxes sat on a low shelf, and every whisper seemed to bounce around like a clue.",
        "the hooks and lunch-box shelf",
        supports={"coat_puppy", "lunchbox_bracelet"},
    ),
}

MYSTERIES = {
    "basket_kitten": Mystery(
        "basket_kitten",
        "animal",
        "kitten",
        "a",
        "the upside-down picnic basket",
        "basket",
        "jiggle-jiggle",
        "didey-ding",
        "a ribbon of fur and a tiny brass bell peeking through the slats",
        "From under the basket came a worried little mew and another frightened \"jiggle-jiggle.\"",
        "Out stepped a dusty kitten with a bell on its collar, blinking at the light and giving a tiny shake: \"didey-ding!\"",
        "It's all right. We are detectives, and we came to help.",
        tags={"kitten", "bell", "kindness"},
    ),
    "coat_puppy": Mystery(
        "coat_puppy",
        "animal",
        "puppy",
        "a",
        "the blue raincoat hanging too low on the hook",
        "coat",
        "jiggle",
        "didey-ding",
        "a wagging patch under the coat hem and a silver tag flashing once in the light",
        "The coat gave a nervous wiggle, and a muffled whine answered the little sound.",
        "A small puppy poked its nose out of the coat sleeve, its collar tag going \"didey-ding\" as it wriggled free.",
        "Easy now. Nobody is in trouble. We can help you out.",
        tags={"puppy", "tag", "kindness"},
    ),
    "lunchbox_bracelet": Mystery(
        "lunchbox_bracelet",
        "item",
        "bracelet with star charms",
        "a",
        "the red lunch box on the low shelf",
        "lunchbox",
        "jiggle-jiggle",
        "didey",
        "a shining loop caught between the lid and the little latch",
        "Nothing was scared this time, but the tiny charms kept tapping inside as if they wanted to be found.",
        "The latch clicked, and the hidden sound stopped at once, because the little bracelet was finally back in the open air.",
        "We heard your little clue. We will open this carefully.",
        owner_kind='"My grandma gave it to me this morning," said Mina, pressing both hands to her chest.',
        tags={"bracelet", "lost_and_found", "kindness"},
    ),
}

RESPONSES = {
    "lift_basket": Response(
        "lift_basket",
        3,
        {"basket"},
        "lifted the basket just enough to make a safe little doorway",
        "lifted the basket slowly to make a safe doorway",
        tags={"gentle_help", "basket"},
    ),
    "free_sleeve": Response(
        "free_sleeve",
        3,
        {"coat"},
        "eased the coat sleeve off the hook and untangled the cloth from the small body hidden inside",
        "eased the coat free and untangled the cloth",
        tags={"gentle_help", "coat"},
    ),
    "open_lunchbox": Response(
        "open_lunchbox",
        3,
        {"lunchbox"},
        "pressed the latch and opened the lunch box without jerking it",
        "opened the lunch box carefully",
        tags={"gentle_help", "lunchbox"},
    ),
    "shake_harder": Response(
        "shake_harder",
        1,
        {"basket", "coat", "lunchbox"},
        "gave the hiding place a hard shake",
        "shook it hard",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Zoe", "Tess", "Ruby", "Ella"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Max", "Finn", "Sam", "Eli", "Theo"]
OWNER_NAMES = ["Mina", "Ivy", "June", "Noah", "Benji", "Luca"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    response: str
    detective: str
    detective_gender: str
    partner: str
    partner_gender: str
    owner_name: str
    owner_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues, listens carefully, and tries to understand what happened. A good detective also stays calm and fair."
    )],
    "kindness": [(
        "Why can kindness help solve a problem?",
        "Kindness helps scared people and animals feel safer. When someone feels safe, it is easier to help them."
    )],
    "kitten": [(
        "Why should you move gently around a scared kitten?",
        "A scared kitten can hide or wiggle if it feels unsafe. Gentle hands and a quiet voice help it calm down."
    )],
    "puppy": [(
        "Why do puppies wear tags on their collars?",
        "A collar tag can help people know who the puppy belongs to. It can also jingle when the puppy moves."
    )],
    "bracelet": [(
        "What is a bracelet?",
        "A bracelet is jewelry worn around the wrist. Some bracelets have little charms that can bump together and make a tiny sound."
    )],
    "lost_and_found": [(
        "What should you do if you find something that belongs to someone else?",
        "You should return it kindly or take it to a grown-up or a lost-and-found place. Giving something back helps the owner feel better."
    )],
    "bell": [(
        "Why does a bell make a jingly sound?",
        "A bell has a little piece inside that taps the metal when it moves. That is what makes the ringing sound."
    )],
}
KNOWLEDGE_ORDER = ["detective", "kindness", "kitten", "puppy", "bracelet", "lost_and_found", "bell"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    place = f["place_cfg"]
    detective = f["detective"]
    partner = f["partner"]
    return [
        f'Write a short detective-style story for a 3-to-5-year-old that includes the words "jiggle" and "didey" and ends happily.',
        f"Tell a gentle mystery where Detective {detective.id} and Detective {partner.id} hear a strange sound at {place.label} and solve the case with kindness.",
        f'Write a story with sound effects like "{mystery.sound1}" and "{mystery.sound2}" where the detectives discover that the right answer is to help, not to blame.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    partner = f["partner"]
    mystery = f["mystery"]
    place = f["place_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the story's detectives?",
            f"The detectives are {detective.id} and {partner.id}. They are children pretending to solve a case together."
        ),
        (
            "What clue started the mystery?",
            f"The first clue was the sound \"{mystery.sound1}! {mystery.sound2}!\" coming from {place.hide_desc}. That sound told the detectives exactly where to start looking."
        ),
        (
            "Why did the detectives speak softly?",
            f"They spoke softly because this was a kindness case, not a blame case. A gentle voice helped the hidden {mystery.label if mystery.kind == 'animal' else 'thing'} feel safe enough to be helped."
        ),
        (
            "How did they solve the mystery?",
            f"They solved it by noticing the clue at {mystery.hideout} and then {response.qa_text}. The case opened because their method matched the real problem instead of making the noise worse."
        ),
    ]
    if outcome == "rescued":
        qa.append((
            "What did they find at the end?",
            f"They found {mystery.article} {mystery.label} that had been hidden and worried. Once it was free, the mystery changed from a nervous sound into a happy one."
        ))
        qa.append((
            "Why is the ending happy?",
            f"The ending is happy because the little animal was safe and calm at last. The detectives proved that careful clues and kind hands belong together."
        ))
    else:
        owner = f["owner"]
        qa.append((
            "Who was helped by the detectives?",
            f"They helped {owner.id}, whose lost bracelet had been stuck in the lunch box. Returning it made the worried feeling end right away."
        ))
        qa.append((
            "Why is the ending happy?",
            f"The ending is happy because the lost thing was returned to its owner. The detectives turned a tiny worry into a big smile."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "kindness"} | set(world.facts["mystery"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "basket_kitten", "lift_basket", "Lila", "girl", "Owen", "boy", "Mina", "girl"),
    StoryParams("library", "coat_puppy", "free_sleeve", "Ava", "girl", "Ben", "boy", "June", "girl"),
    StoryParams("school_hall", "lunchbox_bracelet", "open_lunchbox", "Theo", "boy", "Ruby", "girl", "Mina", "girl"),
]


def explain_place(place: Place, mystery: Mystery) -> str:
    return (
        f"(No story: {place.label.capitalize()} does not fit the mystery '{mystery.id}'. "
        f"That case belongs in one of these places: "
        f"{', '.join(sorted(p.label for p in PLACES.values() if mystery.id in p.supports))}.)"
    )


def explain_response(response: Response, mystery: Mystery) -> str:
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response.id}': it is too rough for this gentle detective world "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: response '{response.id}' does not match the obstacle '{mystery.obstacle}'. "
        f"A detective story should solve the real problem, not poke at the wrong thing.)"
    )


ASP_RULES = r"""
valid(P, M, R) :- place(P), mystery(M), response(R),
                  supports(P, M), obstacle(M, O), handles(R, O),
                  sense(R, S), sense_min(Min), S >= Min.

outcome(rescued) :- chosen_mystery(M), animal_mystery(M).
outcome(returned) :- chosen_mystery(M), item_mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for mid in sorted(place.supports):
            lines.append(asp.fact("supports", pid, mid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("obstacle", mid, mystery.obstacle))
        if mystery.kind == "animal":
            lines.append(asp.fact("animal_mystery", mid))
        else:
            lines.append(asp.fact("item_mystery", mid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        for handle in sorted(response.handles):
            lines.append(asp.fact("handles", rid, handle))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(
        asp_program(
            f"{asp.fact('chosen_mystery', params.mystery)}",
            "#show outcome/1.",
        )
    )
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

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
            raise RuntimeError("empty story")
        smoke.to_json()
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test for generate()/emit()/to_json() passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle detective story world: a tiny mystery solved with clues, kindness, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
    ap.add_argument("--gender", choices=["girl", "boy"], help="gender for the lead detective")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        if not mystery_supported(PLACES[args.place], MYSTERIES[args.mystery]):
            raise StoryError(explain_place(PLACES[args.place], MYSTERIES[args.mystery]))
    if args.response and args.mystery:
        response = RESPONSES[args.response]
        mystery = MYSTERIES[args.mystery]
        if response.sense < SENSE_MIN or not response_matches(response, mystery):
            raise StoryError(explain_response(response, mystery))
    if args.response and args.response in RESPONSES and RESPONSES[args.response].sense < SENSE_MIN:
        mystery = MYSTERIES[args.mystery] if args.mystery else next(iter(MYSTERIES.values()))
        raise StoryError(explain_response(RESPONSES[args.response], mystery))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery, response = rng.choice(sorted(combos))
    detective_gender = args.gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    detective = args.detective or _pick_name(rng, detective_gender)
    partner = args.partner or _pick_name(rng, partner_gender, avoid=detective)
    owner_gender = rng.choice(["girl", "boy"])
    owner_name = rng.choice([n for n in OWNER_NAMES if n not in {detective, partner}])

    return StoryParams(
        place=place,
        mystery=mystery,
        response=response,
        detective=detective,
        detective_gender=detective_gender,
        partner=partner,
        partner_gender=partner_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MYSTERIES[params.mystery],
        RESPONSES[params.response],
        params.detective,
        params.detective_gender,
        params.partner,
        params.partner_gender,
        params.owner_name,
        params.owner_gender,
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
        print(f"{len(combos)} compatible (place, mystery, response) combos:\n")
        for place, mystery, response in combos:
            print(f"  {place:11} {mystery:18} {response}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.detective} & {p.partner}: {p.mystery} at {p.place} with {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
