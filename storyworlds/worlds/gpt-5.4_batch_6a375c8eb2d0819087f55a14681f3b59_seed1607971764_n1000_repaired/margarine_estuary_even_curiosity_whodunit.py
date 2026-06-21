#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/margarine_estuary_even_curiosity_whodunit.py
========================================================================

A standalone story world about a small estuary mystery: a child notices that a
picnic snack with margarine has gone missing, follows concrete clues, and solves
a gentle whodunit before the sun goes down.

The world is deliberately small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate for which animal culprit fits which snack and place
- a clue-based investigation with elimination and reveal
- an inline ASP twin that mirrors the Python compatibility and culprit logic

The tone stays child-facing and curious rather than scary. The mystery matters
because someone is blamed too quickly, and the ending image proves what changed:
the children slow down, look carefully, and let curiosity lead before blame.

Run it
------
    python storyworlds/worlds/gpt-5.4/margarine_estuary_even_curiosity_whodunit.py
    python storyworlds/worlds/gpt-5.4/margarine_estuary_even_curiosity_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/margarine_estuary_even_curiosity_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/margarine_estuary_even_curiosity_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/margarine_estuary_even_curiosity_whodunit.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    vista: str
    stash_spot: str
    access: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    crumb: str
    smear: str
    scent: str
    foods: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Suspect:
    id: str
    label: str
    kind: str
    print_mark: str
    trace: str
    noise: str
    likes: set[str] = field(default_factory=set)
    access: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class SearchTool:
    id: str
    label: str
    phrase: str
    action: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str
    snack: str
    culprit: str
    tool: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    parent: str
    mood: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def culprit_fits(place: Place, snack: Snack, suspect: Suspect) -> bool:
    return bool((suspect.likes & snack.foods) and (suspect.access & place.access))


def tool_fits(tool: SearchTool, culprit: Suspect) -> bool:
    return culprit.id in tool.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for snack_id, snack in SNACKS.items():
            for culprit_id, suspect in SUSPECTS.items():
                if not culprit_fits(place, snack, suspect):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_fits(tool, suspect):
                        combos.append((place_id, snack_id, culprit_id, tool_id))
    return combos


def predicted_false_blame(friend_name: str, culprit: Suspect) -> str:
    if culprit.kind == "bird":
        return f'{friend_name} whispered, "Maybe it was the wind," but the crumbs looked much too neatly pecked for that.'
    if culprit.kind == "mammal":
        return f'{friend_name} frowned and wondered if a grown-up had moved the food, but the wet trail said someone small had hurried away.'
    return f'{friend_name} squinted at the marks and guessed wildly, but the clue pattern did not match that guess at all.'


def introduce(world: World, detective: Entity, friend: Entity, parent: Entity, snack: Snack) -> None:
    detective.memes["curiosity"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{detective.id} and {friend.id} went with {detective.pronoun('possessive')} "
        f"{parent.label_word} to {world.place.label}."
    )
    world.say(
        f"{world.place.vista} They had brought {snack.phrase} for a small bird-watching picnic."
    )
    world.say(
        f"{detective.id} was in a {world.facts['mood']} mood and wanted to notice every tiny thing."
    )


def discover_loss(world: World, detective: Entity, friend: Entity, snack: Snack) -> None:
    snack_ent = world.get("snack")
    snack_ent.meters["missing"] = 1
    detective.memes["alarm"] += 1
    friend.memes["alarm"] += 1
    world.say(
        f"When it was time to eat, the plate on {world.place.stash_spot} looked wrong."
    )
    world.say(
        f"One {snack.label} was gone, and a shiny line of margarine still gleamed where it had been."
    )
    world.say(
        f'"That is odd," said {detective.id}. "{friend.id}, this is not just a snack problem. '
        f"It is a mystery."
    )


def accuse_too_fast(world: World, friend: Entity) -> None:
    friend.memes["certainty"] += 1
    world.say(
        f'"I know who did it," said {friend.id} too quickly. "It must have been the first creature we heard."'
    )


def leave_clue(world: World, culprit: Suspect) -> None:
    trail = world.get("trail")
    trail.meters["visible"] = 1
    trail.attrs["mark"] = culprit.print_mark
    trail.attrs["trace"] = culprit.trace
    trail.attrs["noise"] = culprit.noise


def notice_clue(world: World, detective: Entity, culprit: Suspect, tool: SearchTool) -> None:
    detective.memes["focus"] += 1
    world.say(predicted_false_blame(world.facts["friend"].id, culprit))
    world.say(
        f"But {detective.id} knelt down and looked carefully. {tool.action.capitalize()}, "
        f"{detective.pronoun()} found {culprit.print_mark} beside {snack.smear}."
    )
    world.say(
        f"There was {culprit.trace} too, so the mystery began to feel even clearer."
    )


def eliminate_wrong_suspects(world: World, detective: Entity, culprit: Suspect) -> None:
    suspects = [s for s in SUSPECTS.values() if s.id != culprit.id]
    lines: list[str] = []
    for suspect in suspects:
        mismatch_food = not bool(suspect.likes & world.facts["snack_cfg"].foods)
        mismatch_access = not bool(suspect.access & world.place.access)
        if mismatch_food and mismatch_access:
            reason = f"{suspect.label} did not like that kind of food and could not reach the picnic place easily"
        elif mismatch_food:
            reason = f"{suspect.label} did not match the food clues"
        else:
            reason = f"{suspect.label} could not have reached {world.place.stash_spot}"
        lines.append(reason)
    detective.memes["logic"] += 1
    world.say(
        f"{detective.id} thought it through. " + "; ".join(lines[:2]) + "."
    )


def follow_trail(world: World, detective: Entity, friend: Entity, culprit: Suspect) -> None:
    detective.meters["steps_taken"] += 1
    friend.meters["steps_taken"] += 1
    world.say(
        f"The two children followed the little trail past the reeds and along the edge of the estuary."
    )
    world.say(
        f"At last they spotted {culprit.label}, busy with the stolen snack."
    )


def reveal(world: World, detective: Entity, friend: Entity, culprit: Suspect, snack: Snack) -> None:
    culprit_ent = world.get("culprit")
    culprit_ent.meters["found"] = 1
    detective.memes["pride"] += 1
    friend.memes["embarrassed"] += 1
    world.say(
        f'"Aha!" said {detective.id}. "The culprit was {culprit.label} all along."'
    )
    if culprit.id == "gull":
        world.say(
            f"The gull gave one bright look, dropped a torn corner of {snack.crumb}, and flapped up to a post."
        )
    elif culprit.id == "otter":
        world.say(
            f"The otter blinked over its whiskers, paws shiny with {snack.smear}, and slipped back toward the water."
        )
    else:
        world.say(
            f"The crab held up one buttery claw as if it had been caught in the middle of supper."
        )
    world.say(
        f'{friend.id} rubbed the back of {friend.pronoun("possessive")} neck. '
        f'"I should not have guessed so fast," {friend.pronoun()} said.'
    )


def repair_and_end(world: World, detective: Entity, friend: Entity, parent: Entity, tool: SearchTool) -> None:
    detective.memes["calm"] += 1
    friend.memes["learning"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled when the whole case was explained."
    )
    world.say(
        f'"You solved it by looking before blaming," {parent.pronoun()} said. '
        f'"That is what good curiosity does."'
    )
    world.say(
        f"Then {parent.pronoun()} moved the picnic basket to a safer spot, and {detective.id} let {friend.id} use {tool.phrase} too."
    )
    world.say(
        f"By the time the tide turned silver, the children were watching the water quietly, and even the ordinary reeds looked full of clues."
    )


def tell(
    place: Place,
    snack: Snack,
    culprit: Suspect,
    tool: SearchTool,
    detective_name: str = "Mina",
    detective_gender: str = "girl",
    friend_name: str = "Leo",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    mood: str = "curious",
) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="snack", type="snack", label=snack.label))
    world.add(Entity(id="trail", type="clue", label="trail", attrs={"mark": "", "trace": "", "noise": ""}))
    world.add(Entity(id="culprit", type=culprit.kind, label=culprit.label))
    world.facts.update(
        place_cfg=place,
        snack_cfg=snack,
        culprit_cfg=culprit,
        tool_cfg=tool,
        detective=detective,
        friend=friend,
        parent=parent,
        mood=mood,
        wrong_guess=False,
    )

    introduce(world, detective, friend, parent, snack)
    world.para()
    discover_loss(world, detective, friend, snack)
    accuse_too_fast(world, friend)
    leave_clue(world, culprit)
    notice_clue(world, detective, culprit, tool)
    eliminate_wrong_suspects(world, detective, culprit)
    world.para()
    follow_trail(world, detective, friend, culprit)
    reveal(world, detective, friend, culprit, snack)
    world.para()
    repair_and_end(world, detective, friend, parent, tool)

    world.facts.update(
        solved=True,
        clue_mark=culprit.print_mark,
        clue_trace=culprit.trace,
        culprit_found=True,
    )
    return world


PLACES = {
    "boardwalk": Place(
        id="boardwalk",
        label="the old boardwalk by the estuary",
        vista="The estuary spread out in silver ribbons, with reeds whispering and small waves tapping the pilings.",
        stash_spot="a low bench beside the rail",
        access={"rail", "bench", "open_ground"},
        tags={"estuary", "shore"},
    ),
    "bird_hide": Place(
        id="bird_hide",
        label="the little bird hide at the estuary",
        vista="The hide smelled of warm wood, and the estuary shone through the long viewing window.",
        stash_spot="the wide window shelf",
        access={"window", "shelf", "open_ground"},
        tags={"estuary", "birds"},
    ),
    "mudflat_path": Place(
        id="mudflat_path",
        label="the shell path near the estuary mudflats",
        vista="Beyond the path, the estuary opened into brown gleaming mud and strips of bright water.",
        stash_spot="a flat driftwood log",
        access={"log", "open_ground", "water_edge"},
        tags={"estuary", "mud"},
    ),
}

SNACKS = {
    "roll": Snack(
        id="roll",
        label="roll",
        phrase="soft rolls spread with margarine",
        crumb="bread crumbs",
        smear="a pale buttery smear",
        scent="warm bread",
        foods={"bread", "fat"},
        tags={"margarine", "bread"},
    ),
    "crackers": Snack(
        id="crackers",
        label="cracker stack",
        phrase="salty crackers with a curl of margarine on top",
        crumb="cracker flakes",
        smear="a shiny yellow streak",
        scent="salty crumbs",
        foods={"grain", "fat"},
        tags={"margarine", "crackers"},
    ),
    "fishcake": Snack(
        id="fishcake",
        label="fishcake",
        phrase="little fishcakes with a dab of margarine",
        crumb="soft fishy crumbs",
        smear="a buttery patch",
        scent="fish and toast",
        foods={"fish", "fat"},
        tags={"margarine", "fish"},
    ),
}

SUSPECTS = {
    "gull": Suspect(
        id="gull",
        label="the bold gull",
        kind="bird",
        print_mark="three-toed bird prints",
        trace="one white feather caught in the margarine",
        noise="a sharp cry from the rail",
        likes={"bread", "grain", "fat"},
        access={"rail", "bench", "window", "shelf", "log", "open_ground"},
        tags={"gull", "bird"},
    ),
    "otter": Suspect(
        id="otter",
        label="the sleek otter",
        kind="mammal",
        print_mark="small wet pawprints",
        trace="a damp sliding streak toward the water",
        noise="a soft splash near the reeds",
        likes={"fish", "fat"},
        access={"log", "water_edge", "open_ground"},
        tags={"otter", "pawprints"},
    ),
    "crab": Suspect(
        id="crab",
        label="the red crab",
        kind="crustacean",
        print_mark="tiny sideways marks",
        trace="a dotted scrape line in the sand",
        noise="a faint tap under the driftwood",
        likes={"fish", "fat"},
        access={"log", "water_edge", "open_ground"},
        tags={"crab", "shell"},
    ),
}

TOOLS = {
    "magnifier": SearchTool(
        id="magnifier",
        label="magnifying glass",
        phrase="the little magnifying glass",
        action="through the little magnifying glass",
        solves={"gull", "crab"},
        tags={"magnifier"},
    ),
    "binoculars": SearchTool(
        id="binoculars",
        label="binoculars",
        phrase="the bird binoculars",
        action="with the bird binoculars hanging against the chest",
        solves={"gull", "otter"},
        tags={"binoculars"},
    ),
    "field_guide": SearchTool(
        id="field_guide",
        label="field guide",
        phrase="the pocket field guide",
        action="after checking the pocket field guide",
        solves={"gull", "crab", "otter"},
        tags={"field_guide"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Ruby", "Nora", "Ivy", "Clara", "June"]
BOY_NAMES = ["Leo", "Ben", "Max", "Owen", "Finn", "Theo", "Sam", "Eli"]
MOODS = ["curious", "bright", "thoughtful", "eager"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    culprit = f["culprit_cfg"]
    snack = f["snack_cfg"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old set at an estuary that includes the word "margarine".',
        f"Tell a gentle mystery where {detective.id} notices a missing picnic {snack.label}, follows physical clues, and discovers that {culprit.label} took it.",
        f'Write a child-facing story where curiosity, not guessing, solves a small case, and use the word "even" in the ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    parent = f["parent"]
    snack = f["snack_cfg"]
    culprit = f["culprit_cfg"]
    tool = f["tool_cfg"]
    place = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id} and {friend.id} at {place.label}. They are with {detective.id}'s {parent.label_word} and get pulled into a small mystery.",
        ),
        (
            "What was the mystery?",
            f"One {snack.label} from the picnic went missing, and a line of margarine was left behind. That made {detective.id} stop and look for clues instead of treating it like an ordinary accident.",
        ),
        (
            f"Why did {detective.id} not trust the first guess?",
            f"{detective.id} saw that the food had been taken neatly and that real clues were still there. Curiosity made {detective.pronoun()} slow down and test the guess against the marks on the ground.",
        ),
        (
            f"What clue helped solve the case?",
            f"The biggest clue was {culprit.print_mark}, along with {culprit.trace}. {detective.id} noticed it by using {tool.phrase}, which turned the mystery into something {detective.pronoun()} could reason through.",
        ),
        (
            "Who took the snack, and how do we know?",
            f"The culprit was {culprit.label}. The prints, the trail, and the animal's food habits all matched better than the other suspects, so the answer came from the world of the story, not a wild guess.",
        ),
        (
            "What did the children learn at the end?",
            f"They learned to look before blaming. The ending matters because {friend.id} admits the quick guess was unfair, and the children keep watching the estuary with calmer, better curiosity.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "estuary": [
        (
            "What is an estuary?",
            "An estuary is a place where river water meets the sea. The water there can be part fresh and part salty, and many birds and animals like to live nearby.",
        )
    ],
    "margarine": [
        (
            "What is margarine?",
            "Margarine is a soft spread people can put on bread or crackers. It is slippery and a little greasy, so it can leave shiny smears behind.",
        )
    ],
    "gull": [
        (
            "Why might a gull take a picnic snack?",
            "Gulls are quick birds that often look for easy food near people. If a snack is left where they can reach it, they may swoop in and grab it.",
        )
    ],
    "otter": [
        (
            "What kind of clues can an otter leave behind?",
            "An otter can leave wet pawprints or a damp slide where its body moved. Clues like that help people tell it was near water recently.",
        )
    ],
    "crab": [
        (
            "How does a crab move?",
            "Many crabs scuttle sideways instead of walking straight ahead. That sideways motion can leave a funny trail that looks different from bird or paw prints.",
        )
    ],
    "binoculars": [
        (
            "What are binoculars for?",
            "Binoculars help you see things that are far away. Bird-watchers use them to notice animals without getting too close.",
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes small things look bigger. That can help you notice tiny marks, crumbs, or scratches more clearly.",
        )
    ],
    "field_guide": [
        (
            "What is a field guide?",
            "A field guide is a little book that helps you identify plants or animals. People use it to compare what they see with careful descriptions and pictures.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to learn more. It helps you ask questions, notice clues, and look carefully instead of guessing too fast.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "estuary",
    "margarine",
    "gull",
    "otter",
    "crab",
    "binoculars",
    "magnifier",
    "field_guide",
    "curiosity",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"estuary", "margarine", "curiosity"}
    tags |= set(world.facts["culprit_cfg"].tags)
    tags |= set(world.facts["tool_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    lines.append(f"  place: {world.place.id}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="boardwalk",
        snack="roll",
        culprit="gull",
        tool="binoculars",
        detective="Mina",
        detective_gender="girl",
        friend="Leo",
        friend_gender="boy",
        parent="mother",
        mood="curious",
    ),
    StoryParams(
        place="mudflat_path",
        snack="fishcake",
        culprit="otter",
        tool="field_guide",
        detective="Theo",
        detective_gender="boy",
        friend="Ruby",
        friend_gender="girl",
        parent="father",
        mood="thoughtful",
    ),
    StoryParams(
        place="mudflat_path",
        snack="fishcake",
        culprit="crab",
        tool="magnifier",
        detective="Nora",
        detective_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="mother",
        mood="eager",
    ),
    StoryParams(
        place="bird_hide",
        snack="crackers",
        culprit="gull",
        tool="field_guide",
        detective="Clara",
        detective_gender="girl",
        friend="Finn",
        friend_gender="boy",
        parent="father",
        mood="bright",
    ),
]


def explain_combo(place: Place, snack: Snack, culprit: Suspect, tool: SearchTool) -> str:
    if not culprit_fits(place, snack, culprit):
        parts = []
        if not (culprit.likes & snack.foods):
            parts.append(f"{culprit.label} does not fit the food clues for {snack.phrase}")
        if not (culprit.access & place.access):
            parts.append(f"{culprit.label} cannot sensibly reach {place.stash_spot}")
        return "(No story: " + " and ".join(parts) + ".)"
    if not tool_fits(tool, culprit):
        return (
            f"(No story: {tool.label} is not a good reveal tool for {culprit.label} in this tiny world. "
            f"Pick a tool that can actually help notice that suspect's clues.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
fits_culprit(P,S,C) :- place(P), snack(S), suspect(C),
                       likes_food(C,F), snack_food(S,F),
                       access(C,A), place_access(P,A).

fits_tool(C,T) :- suspect(C), tool(T), solves(T,C).

valid(P,S,C,T) :- fits_culprit(P,S,C), fits_tool(C,T).

culprit(C) :- chosen_place(P), chosen_snack(S), chosen_culprit(C), fits_culprit(P,S,C).
solvable :- chosen_culprit(C), chosen_tool(T), fits_tool(C,T).
story_ok :- culprit(_), solvable.

#show valid/4.
#show story_ok/0.
#show culprit/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for access in sorted(place.access):
            lines.append(asp.fact("place_access", place_id, access))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        for food in sorted(snack.foods):
            lines.append(asp.fact("snack_food", snack_id, food))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for like in sorted(suspect.likes):
            lines.append(asp.fact("likes_food", suspect_id, like))
        for access in sorted(suspect.access):
            lines.append(asp.fact("access", suspect_id, access))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for solved in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, solved))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ok(params: StoryParams) -> tuple[bool, str]:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra))
    ok = bool(asp.atoms(model, "story_ok"))
    culprits = asp.atoms(model, "culprit")
    culprit = culprits[0][0] if culprits else "?"
    return ok, culprit


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle estuary whodunit about a missing margarine snack. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.snack and args.culprit and args.tool:
        place = PLACES[args.place]
        snack = SNACKS[args.snack]
        culprit = SUSPECTS[args.culprit]
        tool = TOOLS[args.tool]
        if not culprit_fits(place, snack, culprit) or not tool_fits(tool, culprit):
            raise StoryError(explain_combo(place, snack, culprit, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.snack is None or combo[1] == args.snack)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, snack_id, culprit_id, tool_id = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if detective_gender == "girl" else "girl"
    detective = _pick_name(rng, detective_gender)
    friend = _pick_name(rng, friend_gender, avoid=detective)
    parent = args.parent or rng.choice(["mother", "father"])
    mood = rng.choice(MOODS)
    return StoryParams(
        place=place_id,
        snack=snack_id,
        culprit=culprit_id,
        tool=tool_id,
        detective=detective,
        detective_gender=detective_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.snack not in SNACKS:
        raise StoryError(f"(No story: unknown snack '{params.snack}'.)")
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")

    place = PLACES[params.place]
    snack = SNACKS[params.snack]
    culprit = SUSPECTS[params.culprit]
    tool = TOOLS[params.tool]
    if not culprit_fits(place, snack, culprit) or not tool_fits(tool, culprit):
        raise StoryError(explain_combo(place, snack, culprit, tool))

    world = tell(
        place=place,
        snack=snack,
        culprit=culprit,
        tool=tool,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        mood=params.mood,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    mismatch = 0
    for params in cases:
        ok, culprit = asp_story_ok(params)
        if not ok or culprit != params.culprit:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP story check matches chosen culprit on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} ASP scenario checks failed.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, snack, culprit, tool) combos:\n")
        for place, snack, culprit, tool in combos:
            print(f"  {place:12} {snack:10} {culprit:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.detective}: {p.culprit} at {p.place} ({p.snack}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
