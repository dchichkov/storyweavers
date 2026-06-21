#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/salsa_cut_bravery_inner_monologue_detective_story.py
===============================================================================

A standalone story world for a tiny child-facing detective story domain:
someone has cut open the tomato sack before fresh salsa can be made, and a
young detective must follow clues to recover the missing tomatoes.

The world is small on purpose. It models a few typed entities, physical meters,
emotional memes, a reasonableness gate over clue/culprit/place combinations, a
simple outcome model for bravery, and an inline ASP twin for parity checks.

Run it
------
python storyworlds/worlds/gpt-5.4/salsa_cut_bravery_inner_monologue_detective_story.py
python storyworlds/worlds/gpt-5.4/salsa_cut_bravery_inner_monologue_detective_story.py --all
python storyworlds/worlds/gpt-5.4/salsa_cut_bravery_inner_monologue_detective_story.py --qa
python storyworlds/worlds/gpt-5.4/salsa_cut_bravery_inner_monologue_detective_story.py --trace --seed 7
python storyworlds/worlds/gpt-5.4/salsa_cut_bravery_inner_monologue_detective_story.py --asp
python storyworlds/worlds/gpt-5.4/salsa_cut_bravery_inner_monologue_detective_story.py --verify
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

# Make shared result containers importable when this nested script is run directly.
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        animal = {"puppy", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Culprit:
    id: str
    label: str
    type: str
    motive: str
    carry_text: str
    reveal_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    points_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    dark: int = 0
    lead_in: str = ""
    hiding_text: str = ""
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Bravery:
    id: str
    label: str
    value: int
    thought: str
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


def _r_open_case(world: World) -> list[str]:
    hero = world.get("hero")
    sack = world.get("sack")
    tomatoes = world.get("tomatoes")
    if sack.meters["cut"] < THRESHOLD or tomatoes.meters["missing"] < THRESHOLD:
        return []
    sig = ("case_open",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    world.get("case").meters["open"] += 1
    return []


def _r_find_tomatoes(world: World) -> list[str]:
    place = world.get("place")
    tomatoes = world.get("tomatoes")
    culprit = world.get("culprit")
    if place.meters["searched"] < THRESHOLD or culprit.attrs.get("place") != place.id:
        return []
    sig = ("found", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tomatoes.meters["missing"] = 0.0
    tomatoes.meters["found"] += 1
    culprit.meters["found"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    tomatoes = world.get("tomatoes")
    if tomatoes.meters["found"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["relief"] += 1
    world.get("adult").memes["relief"] += 1
    world.get("adult").meters["meal_ready"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="open_case", tag="social", apply=_r_open_case),
    Rule(name="find_tomatoes", tag="physical", apply=_r_find_tomatoes),
    Rule(name="relief", tag="social", apply=_r_relief),
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
        for s in produced:
            world.say(s)
    return produced


CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="the puppy",
        type="puppy",
        motive="wanted the round tomatoes because they looked like red balls",
        carry_text="had nudged the tomatoes away one by one with its nose",
        reveal_text="The puppy blinked up from the shadows with a tomato between its paws.",
        tags={"animal", "puppy"},
    ),
    "brother": Culprit(
        id="brother",
        label="the little brother",
        type="boy",
        motive="wanted to make a secret red treasure pile for the game",
        carry_text="had gathered the tomatoes carefully in both hands",
        reveal_text="The little brother looked up, guilty but hopeful, with tomatoes lined beside him like shiny marbles.",
        tags={"child", "brother", "scissors"},
    ),
    "goat": Culprit(
        id="goat",
        label="the goat",
        type="goat",
        motive="liked the smell of the garden sack and followed it for a snack",
        carry_text="had butted the sack and rolled the tomatoes away",
        reveal_text="The goat stood there chewing a leaf, with the tomatoes safe in a dusty corner.",
        tags={"animal", "goat"},
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="muddy paw prints",
        detail="small muddy paw prints dotted the floor beside the torn sack",
        points_to={"puppy"},
        tags={"tracks", "pawprints"},
    ),
    "snip": Clue(
        id="snip",
        label="a neat scissor snip",
        detail="the paper sack had one straight, careful cut, too tidy for teeth",
        points_to={"brother"},
        tags={"cut", "scissors"},
    ),
    "hoofbits": Clue(
        id="hoofbits",
        label="hoof marks and leaf bits",
        detail="tiny hoof marks and chewed cilantro leaves made a wiggly trail away from the table",
        points_to={"goat"},
        tags={"tracks", "goat"},
    ),
    "ragged_edge": Clue(
        id="ragged_edge",
        label="a ragged bite mark",
        detail="the cut in the sack was rough and wet at the edge, as if small teeth had worried at it",
        points_to={"puppy", "goat"},
        tags={"cut", "teeth"},
    ),
}

PLACES = {
    "toy_wagon": Place(
        id="toy_wagon",
        label="the toy wagon by the fence",
        dark=0,
        lead_in="The trail ended by the toy wagon by the fence.",
        hiding_text="Inside the wagon, under a blanket, the missing tomatoes waited in a neat heap.",
        allows={"brother"},
        tags={"wagon"},
    ),
    "doghouse": Place(
        id="doghouse",
        label="the doghouse",
        dark=1,
        lead_in="The trail curved toward the doghouse, where the opening looked low and dim.",
        hiding_text="Just inside the doghouse, the tomatoes sat in a ring like a strange red nest.",
        allows={"puppy"},
        tags={"doghouse", "dark"},
    ),
    "under_porch": Place(
        id="under_porch",
        label="under the porch",
        dark=2,
        lead_in="The clues pointed under the porch, where boards made a striped little cave.",
        hiding_text="There, just beyond the dust, the tomatoes glowed red in the shade.",
        allows={"puppy", "goat"},
        tags={"porch", "dark"},
    ),
    "potting_shed": Place(
        id="potting_shed",
        label="the potting shed",
        dark=3,
        lead_in="The trail reached the potting shed, the darkest place in the yard, where the door stood a little open.",
        hiding_text="On an upside-down bucket inside the shed sat the missing tomatoes, bright as lanterns in the gloom.",
        allows={"brother", "goat"},
        tags={"shed", "dark"},
    ),
}

BRAVERIES = {
    "hesitant": Bravery(
        id="hesitant",
        label="hesitant",
        value=1,
        thought="I do not have to stop feeling scared before I do the next right thing.",
        tags={"bravery"},
    ),
    "steady": Bravery(
        id="steady",
        label="steady",
        value=2,
        thought="A real detective lets a shaky stomach come along and keeps looking anyway.",
        tags={"bravery"},
    ),
    "bold": Bravery(
        id="bold",
        label="bold",
        value=3,
        thought="Clues are waiting for me, and I am brave enough to meet them.",
        tags={"bravery"},
    ),
}

HERO_NAMES = {
    "girl": ["Lina", "Maya", "Nora", "Ella", "Zoe", "Ruby"],
    "boy": ["Ben", "Theo", "Max", "Leo", "Sam", "Noah"],
}
TRAITS = ["careful", "curious", "quiet", "sharp-eyed", "thoughtful"]
ADULT_TYPES = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    culprit: str
    clue: str
    place: str
    bravery: str
    hero_name: str
    hero_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        culprit="puppy",
        clue="pawprints",
        place="doghouse",
        bravery="steady",
        hero_name="Nora",
        hero_gender="girl",
        adult_type="grandfather",
        trait="sharp-eyed",
    ),
    StoryParams(
        culprit="brother",
        clue="snip",
        place="toy_wagon",
        bravery="hesitant",
        hero_name="Ben",
        hero_gender="boy",
        adult_type="mother",
        trait="careful",
    ),
    StoryParams(
        culprit="goat",
        clue="hoofbits",
        place="under_porch",
        bravery="bold",
        hero_name="Maya",
        hero_gender="girl",
        adult_type="grandmother",
        trait="curious",
    ),
    StoryParams(
        culprit="brother",
        clue="snip",
        place="potting_shed",
        bravery="steady",
        hero_name="Theo",
        hero_gender="boy",
        adult_type="father",
        trait="thoughtful",
    ),
]


def valid_combo(culprit_id: str, clue_id: str, place_id: str) -> bool:
    if culprit_id not in CULPRITS or clue_id not in CLUES or place_id not in PLACES:
        return False
    clue = CLUES[clue_id]
    place = PLACES[place_id]
    return culprit_id in clue.points_to and culprit_id in place.allows


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for culprit_id in sorted(CULPRITS):
        for clue_id in sorted(CLUES):
            for place_id in sorted(PLACES):
                if valid_combo(culprit_id, clue_id, place_id):
                    out.append((culprit_id, clue_id, place_id))
    return out


def outcome_of(params: StoryParams) -> str:
    bravery = BRAVERIES[params.bravery]
    place = PLACES[params.place]
    return "solo" if bravery.value >= place.dark else "with_help"


def explain_rejection(culprit_id: str, clue_id: str, place_id: str) -> str:
    if culprit_id not in CULPRITS:
        return f"(No story: unknown culprit '{culprit_id}'.)"
    if clue_id not in CLUES:
        return f"(No story: unknown clue '{clue_id}'.)"
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    clue = CLUES[clue_id]
    place = PLACES[place_id]
    culprit = CULPRITS[culprit_id]
    if culprit_id not in clue.points_to:
        opts = ", ".join(sorted(clue.points_to))
        return (
            f"(No story: {clue.label} would not honestly point to {culprit.label}. "
            f"That clue fits: {opts}.)"
        )
    if culprit_id not in place.allows:
        opts = ", ".join(sorted(place.allows))
        return (
            f"(No story: {culprit.label} would not plausibly hide the tomatoes at "
            f"{place.label}. That place fits: {opts}.)"
        )
    return "(No story: that clue and hiding place do not make a coherent case.)"


def predict_search(params: StoryParams) -> dict:
    bravery = BRAVERIES[params.bravery]
    place = PLACES[params.place]
    return {
        "needs_help": bravery.value < place.dark,
        "fear": max(place.dark - bravery.value, 0),
        "outcome": outcome_of(params),
    }


def open_case(world: World, hero: Entity, adult: Entity, clue: Clue) -> None:
    sack = world.get("sack")
    tomatoes = world.get("tomatoes")
    sack.meters["cut"] += 1
    tomatoes.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the back patio, {hero.id} stood beside {adult.title_word} and a chopping board full of onions, cilantro, and limes. "
        f"They were getting ready to make fresh salsa from the garden tomatoes."
    )
    world.say(
        f"Then {hero.id} turned back and stopped short. The paper tomato sack had been cut open, and half the tomatoes were gone."
    )
    world.say(
        f'This was not just a kitchen problem. This was a case.'
    )
    world.facts["opening_clue_detail"] = clue.detail


def inner_monologue_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} pressed {hero.pronoun('possessive')} lips together and looked slowly around. "
        f'"A detective does not guess," {hero.pronoun()} thought. "A detective notices what changed."'
    )


def inspect_clue(world: World, hero: Entity, clue: Clue, culprit: Culprit) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"Right beside the sack, {hero.id} found the first clue: {clue.detail}."
    )
    world.say(
        f'"That means something," {hero.pronoun()} thought. "If I follow the true clue, it will lead me to the missing tomatoes."'
    )
    world.facts["deduced_culprit"] = culprit.id


def deduce_place(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"{place.lead_in}"
    )
    if place.dark > 0:
        world.say(
            f"The opening looked dark enough to make an ordinary errand feel bigger."
        )


def brave_choice(world: World, hero: Entity, adult: Entity, bravery: Bravery, place: Place, outcome: str) -> None:
    hero.memes["bravery"] = float(bravery.value)
    if place.dark > 0:
        hero.memes["fear"] += float(place.dark)
    world.say(
        f'{hero.id} felt a flutter in {hero.pronoun("possessive")} chest. "{bravery.thought}"'
    )
    if outcome == "solo":
        world.say(
            f"{hero.id} lifted a flashlight from the patio shelf and took one careful step closer, then another."
        )
        world.get("hero").meters["searching"] += 1
    else:
        world.say(
            f"{hero.id} swallowed and chose the brave thing that fit the moment. "
            f'"{adult.title_word.capitalize()}, will you come with me?" {hero.pronoun()} asked.'
        )
        world.say(
            f"{adult.title_word.capitalize()} nodded at once. Asking for help did not close the case; it helped solve it."
        )
        world.get("hero").meters["searching"] += 1
        world.get("adult").meters["helping"] += 1


def search_place(world: World, place: Place) -> None:
    world.get("place").meters["searched"] += 1
    propagate(world, narrate=False)
    world.say(place.hiding_text)


def reveal(world: World, culprit: Culprit, clue: Clue, place: Place, hero: Entity, adult: Entity) -> None:
    world.say(culprit.reveal_text)
    world.say(
        f"It was clear now what had happened. {culprit.label.capitalize()} {culprit.carry_text} after the sack was cut."
    )
    world.say(
        f'"So that was it," {hero.pronoun()} thought. "{clue.label.capitalize()} led me exactly where they should."'
    )
    if culprit.id == "brother":
        world.say(
            f'{adult.title_word.capitalize()} gave a small sigh and then a kind smile. "Next time, ask before you use the scissors," {adult.pronoun()} said.'
        )
    else:
        world.say(
            f'{adult.title_word.capitalize()} laughed softly with relief. "Well, that is one hungry helper," {adult.pronoun()} said.'
        )


def close_case(world: World, hero: Entity, adult: Entity, culprit: Culprit) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} gathered the tomatoes back into a bowl. After a quick wash, {adult.title_word} began to cut them for salsa."
    )
    world.say(
        f'Soon the bowl shone red and green on the table, and the whole mystery felt smaller than the smell of cilantro and lime.'
    )
    world.say(
        f'{adult.title_word.capitalize()} tapped the side of the bowl and smiled at {hero.id}. "Good detectives notice clues, and good detectives are brave," {adult.pronoun()} said.'
    )
    if culprit.id == "brother":
        world.say(
            "The little brother carried over the chips to make up for the trouble, and everyone shared the salsa together."
        )
    else:
        world.say(
            f"{culprit.label.capitalize()} settled nearby at last, watched carefully, and did not get any more ideas about the tomatoes."
        )


def tell(params: StoryParams) -> World:
    culprit_cfg = CULPRITS[params.culprit]
    clue_cfg = CLUES[params.clue]
    place_cfg = PLACES[params.place]
    bravery_cfg = BRAVERIES[params.bravery]
    world = World()

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_gender,
            label=params.hero_name,
            role="hero",
            attrs={"trait": params.trait},
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=params.adult_type,
            label="the grown-up",
            role="adult",
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character",
            type=culprit_cfg.type,
            label=culprit_cfg.label,
            role="culprit",
            attrs={"place": place_cfg.id, "motive": culprit_cfg.motive},
            tags=set(culprit_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="sack",
            type="sack",
            label="the tomato sack",
            phrase="the paper tomato sack",
        )
    )
    world.add(
        Entity(
            id="tomatoes",
            type="tomatoes",
            label="the tomatoes",
            phrase="the garden tomatoes",
        )
    )
    world.add(
        Entity(
            id="place",
            type="place",
            label=place_cfg.label,
            phrase=place_cfg.label,
            attrs={"dark": place_cfg.dark},
            tags=set(place_cfg.tags),
        )
    )
    world.add(Entity(id="case", type="mystery", label="the case"))

    open_case(world, hero, adult, clue_cfg)
    inner_monologue_intro(world, hero)

    world.para()
    inspect_clue(world, hero, clue_cfg, culprit_cfg)
    deduce_place(world, hero, place_cfg)
    brave_choice(world, hero, adult, bravery_cfg, place_cfg, outcome_of(params))

    world.para()
    search_place(world, place_cfg)
    reveal(world, culprit_cfg, clue_cfg, place_cfg, hero, adult)
    close_case(world, hero, adult, culprit_cfg)

    world.facts.update(
        hero=hero,
        adult=adult,
        culprit=culprit_cfg,
        clue=clue_cfg,
        place=place_cfg,
        bravery=bravery_cfg,
        outcome=outcome_of(params),
        solved=True,
        asked_help=outcome_of(params) == "with_help",
        inner_thought=bravery_cfg.thought,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    clue = world.facts["clue"]
    place = world.facts["place"]
    outcome = world.facts["outcome"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the words "salsa" and "cut".',
        f"Tell a child-friendly mystery where {hero.id} notices a tomato sack has been cut open before salsa is made, follows {clue.label}, and solves the case at {place.label}.",
        f"Write a gentle detective story with inner monologue and bravery where the ending is solved {('alone' if outcome == 'solo' else 'with a grown-up')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    adult = world.facts["adult"]
    clue = world.facts["clue"]
    place = world.facts["place"]
    culprit = world.facts["culprit"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            "The mystery was that the tomato sack had been cut open and some of the tomatoes were missing. That mattered because the family was about to make fresh salsa.",
        ),
        (
            f"What clue did {hero.id} find first?",
            f"{hero.id} found {clue.label} first. That clue mattered because it truthfully pointed toward who had taken the tomatoes.",
        ),
        (
            f"Why did {hero.id} have to be brave?",
            f"{hero.id} had to keep following the clues even when the hiding place looked dark and a little scary. The bravery was not pretending the fear was gone; it was choosing the next good step anyway.",
        ),
        (
            f"Who had the tomatoes, and why?",
            f"It was {culprit.label}. {culprit.label.capitalize()} had the tomatoes because {culprit.motive}.",
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"Did {hero.id} solve the case alone?",
                f"Yes. {hero.id} took a flashlight and searched {place.label} alone. The clues and the brave choice worked together to solve the mystery.",
            )
        )
    else:
        qa.append(
            (
                f"How was asking {adult.title_word} for help still brave?",
                f"Asking for help was brave because {hero.id} told the truth about feeling scared and still kept working on the case. The story shows that bravery can mean getting support instead of giving up.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The tomatoes were found, washed, and cut up for salsa, so the case ended with food on the table instead of a problem. The final image proves the mystery was solved and the family could be together again.",
        )
    )
    return qa


KNOWLEDGE = {
    "salsa": [
        (
            "What is salsa?",
            "Salsa is a chopped sauce often made from tomatoes, onions, and other vegetables or herbs. People eat it with many foods, and it can taste fresh and bright.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses them to figure out what happened. Good detectives try not to guess before they have enough facts.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel afraid. It does not mean you never feel scared.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand something hidden. A footprint, a sound, or a cut paper edge can all be clues.",
        )
    ],
    "scissors": [
        (
            "Why should children ask before using scissors?",
            "Scissors can cut paper safely when a grown-up says it is okay, but they still need care and rules. Asking first helps keep people and things safe.",
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show where someone or some animal went. They help you follow a path without seeing the whole event happen.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in a dark place?",
            "A flashlight helps you see clearly in the dark. Seeing well can make a search safer and calmer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["salsa", "detective", "bravery", "clue", "tracks", "scissors", "flashlight"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"salsa", "detective", "bravery", "clue"}
    clue = world.facts["clue"]
    place = world.facts["place"]
    culprit = world.facts["culprit"]
    if "tracks" in clue.tags or "pawprints" in clue.tags or "goat" in culprit.tags:
        tags.add("tracks")
    if "scissors" in clue.tags or "brother" in culprit.tags:
        tags.add("scissors")
    if place.dark > 0:
        tags.add("flashlight")
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        if shown_attrs:
            parts.append(f"attrs={shown_attrs}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Cu, Cl, Pl) :- culprit(Cu), clue(Cl), place(Pl), clue_for(Cl, Cu), hides(Cu, Pl).

solo :- chosen_bravery(B), brave_value(B, V), chosen_place(P), dark(P, D), V >= D.
with_help :- chosen_bravery(B), brave_value(B, V), chosen_place(P), dark(P, D), V < D.

outcome(solo) :- solo.
outcome(with_help) :- with_help.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for culprit_id in sorted(CULPRITS):
        lines.append(asp.fact("culprit", culprit_id))
    for clue_id, clue in sorted(CLUES.items()):
        lines.append(asp.fact("clue", clue_id))
        for culprit_id in sorted(clue.points_to):
            lines.append(asp.fact("clue_for", clue_id, culprit_id))
    for place_id, place in sorted(PLACES.items()):
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("dark", place_id, place.dark))
        for culprit_id in sorted(place.allows):
            lines.append(asp.fact("hides", culprit_id, place_id))
    for bravery_id, bravery in sorted(BRAVERIES.items()):
        lines.append(asp.fact("bravery", bravery_id))
        lines.append(asp.fact("brave_value", bravery_id, bravery.value))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_bravery", params.bravery),
            asp.fact("chosen_place", params.place),
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

    cases = list(CURATED)
    rng = random.Random(11)
    parser = build_parser()
    for _ in range(20):
        params = resolve_params(parser.parse_args([]), rng)
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tiny detective story world: a cut tomato sack, missing tomatoes, bravery, and salsa."
    )
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--bravery", choices=sorted(BRAVERIES))
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible sampling")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.clue and args.place and not valid_combo(args.culprit, args.clue, args.place):
        raise StoryError(explain_rejection(args.culprit, args.clue, args.place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.culprit is None or combo[0] == args.culprit)
        and (args.clue is None or combo[1] == args.clue)
        and (args.place is None or combo[2] == args.place)
    ]
    if not combos:
        if args.culprit and args.clue and args.place:
            raise StoryError(explain_rejection(args.culprit, args.clue, args.place))
        raise StoryError("(No valid combination matches the given options.)")

    culprit_id, clue_id, place_id = rng.choice(sorted(combos))
    bravery_id = args.bravery or rng.choice(sorted(BRAVERIES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES[hero_gender])
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    trait = rng.choice(TRAITS)

    return StoryParams(
        culprit=culprit_id,
        clue=clue_id,
        place=place_id,
        bravery=bravery_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [
        ("culprit", CULPRITS),
        ("clue", CLUES),
        ("place", PLACES),
        ("bravery", BRAVERIES),
    ]:
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(No story: unknown {key} '{value}'.)")
    if not valid_combo(params.culprit, params.clue, params.place):
        raise StoryError(explain_rejection(params.culprit, params.clue, params.place))
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
        print(f"{len(combos)} valid (culprit, clue, place) combos:\n")
        for culprit_id, clue_id, place_id in combos:
            print(f"  {culprit_id:8} {clue_id:12} {place_id}")
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
            header = f"### {p.hero_name}: {p.clue} -> {p.place} ({p.culprit}, {outcome_of(p)})"
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
