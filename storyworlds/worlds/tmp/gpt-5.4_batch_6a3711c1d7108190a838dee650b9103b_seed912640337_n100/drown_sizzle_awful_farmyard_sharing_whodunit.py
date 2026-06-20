#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drown_sizzle_awful_farmyard_sharing_whodunit.py
============================================================================

A small storyworld for a child-facing farmyard whodunit about a missing hot
snack, a trail of clues, and a gentle lesson about sharing.

Seed constraints:
- must include the words "drown", "sizzle", and "awful"
- set in a farmyard
- feature sharing
- style close to a whodunit

The world model favors only *reasonable* mysteries:
- the chosen culprit must be able to reach the hiding place
- the hiding place must be dry enough for the hot snack
- the detective must be able to read the culprit's clue
- the "late friend" waiting to be included cannot be the culprit

The stories are not frozen templates with swapped nouns. The missing snack,
clue, suspicion, confession, and final sharing scene all come from simulated
state.

Run it
------
    python storyworlds/worlds/gpt-5.4/drown_sizzle_awful_farmyard_sharing_whodunit.py
    python storyworlds/worlds/gpt-5.4/drown_sizzle_awful_farmyard_sharing_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/drown_sizzle_awful_farmyard_sharing_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/drown_sizzle_awful_farmyard_sharing_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/drown_sizzle_awful_farmyard_sharing_whodunit.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hen", "cow", "goose", "duck", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"dog", "pig", "goat", "donkey", "rooster", "lamb"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    plural: str
    sizzle_line: str
    crumb: str
    soggy_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalSpec:
    id: str
    label: str
    type: str
    clue: str
    clue_line: str
    confession_style: str
    reaches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    dry: bool
    near_water: bool
    reachable_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Detective:
    id: str
    label: str
    type: str
    skill_line: str
    reads: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class LateFriend:
    id: str
    label: str
    type: str
    arrival_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hidden_worry(world: World) -> list[str]:
    out: list[str] = []
    if "snack" not in world.entities or "culprit" not in world.entities:
        return out
    snack = world.get("snack")
    culprit = world.get("culprit")
    if snack.meters["hidden"] >= THRESHOLD:
        sig = ("hidden_worry", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            culprit.memes["guilt"] += 1
            for ent in list(world.entities.values()):
                if ent.role == "waiting_friend":
                    ent.memes["hope"] += 1
            out.append("__worry__")
    return out


def _r_detective_finds(world: World) -> list[str]:
    out: list[str] = []
    if "detective" not in world.entities or "culprit" not in world.entities:
        return out
    detective = world.get("detective")
    culprit = world.get("culprit")
    clue = culprit.attrs.get("clue", "")
    if detective.meters["searching"] >= THRESHOLD and clue in detective.attrs.get("reads", set()):
        sig = ("finds", detective.id, culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["certainty"] += 1
            culprit.memes["cornered"] += 1
            out.append("__found__")
    return out


def _r_share_joy(world: World) -> list[str]:
    out: list[str] = []
    if "snack" not in world.entities:
        return out
    snack = world.get("snack")
    if snack.meters["shared"] < THRESHOLD:
        return out
    sig = ("share_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
            ent.meters["hunger"] = 0.0
    out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule("hidden_worry", "social", _r_hidden_worry),
    Rule("detective_finds", "mystery", _r_detective_finds),
    Rule("share_joy", "social", _r_share_joy),
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


TREATS = {
    "corncake": Treat(
        "corncake",
        "corn cake",
        "a pan of corn cakes",
        "corn cakes",
        "The little cakes gave a bright sizzle on the iron griddle.",
        "yellow crumbs",
        "Corn cake would turn awful and soggy if it fell into the trough water.",
        tags={"griddle", "sharing", "food"},
    ),
    "apple_fritter": Treat(
        "apple_fritter",
        "apple fritter",
        "a pan of apple fritters",
        "apple fritters",
        "The apple fritters met the hot pan with a happy sizzle.",
        "sweet crumbs",
        "An apple fritter would go awful and floppy if it tried to drown in the trough.",
        tags={"griddle", "sharing", "food"},
    ),
    "oat_patty": Treat(
        "oat_patty",
        "oat patty",
        "a pan of oat patties",
        "oat patties",
        "The oat patties made a soft sizzle while the farmyard smelled warm and buttery.",
        "oaty crumbs",
        "An oat patty would be awful after a dip in trough water.",
        tags={"griddle", "sharing", "food"},
    ),
}

ANIMALS = {
    "piglet": AnimalSpec(
        "piglet",
        "Pip the piglet",
        "pig",
        "mudprint",
        "There was a neat little mudprint near the empty tray.",
        "snuffled and admitted he had hidden the snack for someone smaller",
        reaches={"hay_nook", "wheelbarrow", "gate_step"},
        tags={"piglet", "mudprint"},
    ),
    "goat_kid": AnimalSpec(
        "goat_kid",
        "Tansy the goat kid",
        "goat",
        "chewed_straw",
        "A twist of straw had been nibbled right beside the missing place on the tray.",
        "blinked and admitted he had tucked the snack away to save it for a friend",
        reaches={"hay_nook", "barrel_lid", "wheelbarrow", "gate_step"},
        tags={"goat", "straw"},
    ),
    "duckling": AnimalSpec(
        "duckling",
        "Dabble the duckling",
        "duck",
        "feather",
        "A soft gray feather rested beside the tray.",
        "ruffled her wings and admitted she had carried the snack off for a late friend",
        reaches={"barrel_lid", "gate_step", "trough_rail"},
        tags={"duckling", "feather"},
    ),
    "calf": AnimalSpec(
        "calf",
        "Moss the calf",
        "cow",
        "broad_hoof",
        "One broad hoof mark pressed into the dust by the table leg.",
        "lowered his head and admitted he had hidden the snack so nobody would be left out",
        reaches={"hay_nook", "wheelbarrow", "gate_step"},
        tags={"calf", "hoofprint"},
    ),
}

HIDEOUTS = {
    "hay_nook": Hideout(
        "hay_nook",
        "hay nook",
        "a dry nook in the hay",
        True,
        False,
        reachable_by={"piglet", "goat_kid", "calf"},
        tags={"hay"},
    ),
    "wheelbarrow": Hideout(
        "wheelbarrow",
        "wheelbarrow",
        "the clean wheelbarrow by the barn wall",
        True,
        False,
        reachable_by={"piglet", "goat_kid", "calf"},
        tags={"wheelbarrow"},
    ),
    "barrel_lid": Hideout(
        "barrel_lid",
        "barrel lid",
        "the sunny lid of the feed barrel",
        True,
        False,
        reachable_by={"goat_kid", "duckling"},
        tags={"barrel"},
    ),
    "gate_step": Hideout(
        "gate_step",
        "gate step",
        "the flat step by the pasture gate",
        True,
        False,
        reachable_by={"piglet", "goat_kid", "duckling", "calf"},
        tags={"gate"},
    ),
    "trough_rail": Hideout(
        "trough_rail",
        "trough rail",
        "the rail above the water trough",
        False,
        True,
        reachable_by={"duckling", "goat_kid"},
        tags={"trough", "water"},
    ),
}

DETECTIVES = {
    "hen": Detective(
        "hen",
        "Hazel the hen",
        "hen",
        "Hazel tipped her head, peered once, and missed nothing.",
        reads={"feather", "chewed_straw", "yellow_crumbs", "sweet_crumbs", "oaty_crumbs"},
        tags={"hen", "clue"},
    ),
    "sheepdog": Detective(
        "sheepdog",
        "Bram the sheepdog",
        "dog",
        "Bram put his nose close to the ground and followed the tiny signs at once.",
        reads={"mudprint", "broad_hoof", "feather"},
        tags={"dog", "clue"},
    ),
    "barn_cat": Detective(
        "barn_cat",
        "Mallow the barn cat",
        "cat",
        "Mallow narrowed her eyes and looked where everyone else forgot to look.",
        reads={"chewed_straw", "feather", "mudprint"},
        tags={"cat", "clue"},
    ),
    "donkey": Detective(
        "donkey",
        "Ned the donkey",
        "donkey",
        "Ned stood very still, then noticed which mark did not belong.",
        reads={"broad_hoof", "mudprint", "chewed_straw"},
        tags={"donkey", "clue"},
    ),
}

LATE_FRIENDS = {
    "chick": LateFriend(
        "chick",
        "Peep the chick",
        "hen",
        "Peep had been helping Farmer June carry napkins and had come late to the snack table.",
        tags={"chick", "sharing"},
    ),
    "lamb": LateFriend(
        "lamb",
        "Woolly the lamb",
        "lamb",
        "Woolly had been untangling himself from a loose ribbon on the fence and reached the table last.",
        tags={"lamb", "sharing"},
    ),
    "gosling": LateFriend(
        "gosling",
        "Mim the gosling",
        "goose",
        "Mim had waddled behind the others and was only just arriving by the barn door.",
        tags={"gosling", "sharing"},
    ),
}

FARMERS = {
    "june": ("Farmer June", "farmer"),
    "sam": ("Farmer Sam", "farmer"),
}


def clue_token_for_treat(treat_id: str) -> str:
    return {
        "corncake": "yellow_crumbs",
        "apple_fritter": "sweet_crumbs",
        "oat_patty": "oaty_crumbs",
    }[treat_id]


def culprit_can_reach(culprit: AnimalSpec, hideout: Hideout) -> bool:
    return hideout.id in culprit.reaches and culprit.id in hideout.reachable_by


def hideout_is_reasonable(treat: Treat, hideout: Hideout) -> bool:
    return hideout.dry and not hideout.near_water


def detective_can_solve(detective: Detective, culprit: AnimalSpec, treat: Treat) -> bool:
    clue = culprit.clue
    crumb = clue_token_for_treat(treat.id)
    reads = detective.reads
    return clue in reads or crumb in reads


def valid_combo(treat: Treat, culprit: AnimalSpec, hideout: Hideout,
                detective: Detective, friend: LateFriend) -> bool:
    if culprit.id == friend.id:
        return False
    if not culprit_can_reach(culprit, hideout):
        return False
    if not hideout_is_reasonable(treat, hideout):
        return False
    if not detective_can_solve(detective, culprit, treat):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for tid, treat in TREATS.items():
        for aid, culprit in ANIMALS.items():
            for hid, hideout in HIDEOUTS.items():
                for did, detective in DETECTIVES.items():
                    for fid, friend in LATE_FRIENDS.items():
                        if valid_combo(treat, culprit, hideout, detective, friend):
                            combos.append((tid, aid, hid, did, fid))
    return combos


def predict_sogginess(treat: Treat, hideout: Hideout) -> dict:
    return {
        "safe": hideout_is_reasonable(treat, hideout),
        "awful": not hideout_is_reasonable(treat, hideout),
        "near_water": hideout.near_water,
    }


def kitchen_setup(world: World, farmer: Entity, treat: Treat,
                  detective: Entity, friend: Entity) -> None:
    world.say(
        f"In the farmyard kitchen, {farmer.id} set out {treat.phrase} for everyone to share."
    )
    world.say(treat.sizzle_line)
    world.say(
        f"{detective.id} was already waiting by the table, and {friend.id} was expected any moment."
    )
    world.facts["opening_count"] = 6


def announce_missing(world: World, farmer: Entity, treat: Treat) -> None:
    world.say(
        f"When {farmer.id} counted the {treat.plural}, one was missing."
    )
    world.say(
        f'"Oh dear," said {farmer.id}. "That is an awful puzzle. We meant to share these fairly."'
    )
    world.say(
        "Every head in the yard turned. It felt, for one tiny moment, like a whodunit."
    )


def inspect_clue(world: World, detective: Entity, culprit: Entity, treat: Treat) -> None:
    detective.meters["searching"] += 1
    world.say(detective.attrs["skill_line"])
    world.say(culprit.attrs["clue_line"])
    if detective.attrs.get("reads_crumb", False):
        crumb = treat.crumb
        world.say(f"A pinch of {crumb} glittered on the floorboards too.")
    propagate(world, narrate=False)


def follow_to_hideout(world: World, detective: Entity, hideout: Hideout) -> None:
    world.say(
        f'Soon {detective.id} led the others to {hideout.phrase}.'
    )


def reveal(world: World, culprit: Entity, friend: Entity, treat: Treat, hideout: Hideout) -> None:
    culprit.memes["honesty"] += 1
    world.say(
        f"There sat the missing {treat.label}, still warm and wrapped in a dock leaf."
    )
    world.say(
        f'{culprit.id} {culprit.attrs["confession_style"]}.'
    )
    if hideout.near_water:
        world.say(
            f'"I did not want it to slip and drown," {culprit.pronoun()} said. '
            f'"That would have been awful."'
        )
    else:
        world.say(
            f'"{friend.id} was late," {culprit.pronoun()} explained. '
            f'"I wanted {friend.pronoun("object")} to have one too, and I did not want a hot cake to tumble into the trough and drown there."'
        )
    world.say(
        f"{treat.soggy_line}"
    )


def lesson_and_share(world: World, farmer: Entity, culprit: Entity,
                     friend: Entity, treat: Treat) -> None:
    snack = world.get("snack")
    snack.meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{farmer.id} knelt by the tray. "Hiding food makes people worry," {farmer.pronoun()} said kindly. '
        f'"But saving a share for someone else is a caring idea. Next time, ask me first."'
    )
    world.say(
        f"Then {farmer.id} cut the missing {treat.label} in two and split the rest of the {treat.plural} as well."
    )
    world.say(
        f"{culprit.id} passed the first piece to {friend.id}, and the second to the nearest waiting neighbor."
    )
    world.say(
        "Soon nobody was guessing anymore. They were chewing, smiling, and making room for one another at the table."
    )


def closing_image(world: World, detective: Entity, friend: Entity) -> None:
    world.say(
        f"{detective.id} looked pleased, {friend.id} licked the last crumb away, and the farmyard felt fair again."
    )


def tell(treat: Treat, culprit_spec: AnimalSpec, hideout: Hideout, detective_spec: Detective,
         friend_spec: LateFriend, farmer_name: str = "Farmer June") -> World:
    world = World()

    farmer = world.add(Entity(id=farmer_name, kind="character", type="farmer", label="the farmer", role="farmer"))
    detective = world.add(Entity(
        id=detective_spec.label, kind="character", type=detective_spec.type,
        role="detective", attrs={"skill_line": detective_spec.skill_line,
                                 "reads": set(detective_spec.reads),
                                 "reads_crumb": clue_token_for_treat(treat.id) in detective_spec.reads}
    ))
    culprit = world.add(Entity(
        id=culprit_spec.label, kind="character", type=culprit_spec.type,
        role="culprit", attrs={"clue": culprit_spec.clue, "clue_line": culprit_spec.clue_line,
                               "confession_style": culprit_spec.confession_style}
    ))
    friend = world.add(Entity(
        id=friend_spec.label, kind="character", type=friend_spec.type,
        role="waiting_friend"
    ))
    snack = world.add(Entity(id="snack", kind="thing", type="treat", label=treat.label))
    place = world.add(Entity(id="place", kind="thing", type="farmyard", label="farmyard"))
    hide = world.add(Entity(id="hideout", kind="thing", type="hideout", label=hideout.label))

    for ent in (detective, culprit, friend):
        ent.meters["hunger"] = 1.0
    culprit.memes["generosity"] = 1.0
    friend.memes["left_out_risk"] = 1.0
    snack.meters["hot"] = 1.0
    snack.meters["hidden"] = 1.0
    hide.meters["dry"] = 1.0 if hideout.dry else 0.0

    kitchen_setup(world, farmer, treat, detective, friend)
    world.para()
    announce_missing(world, farmer, treat)
    inspect_clue(world, detective, culprit, treat)
    follow_to_hideout(world, detective, hideout)
    world.para()
    reveal(world, culprit, friend, treat, hideout)
    world.para()
    lesson_and_share(world, farmer, culprit, friend, treat)
    closing_image(world, detective, friend)

    world.facts.update(
        farmer=farmer,
        detective=detective,
        culprit=culprit,
        friend=friend,
        treat=treat,
        hideout_cfg=hideout,
        detective_cfg=detective_spec,
        culprit_cfg=culprit_spec,
        friend_cfg=friend_spec,
        snack=snack,
        solved=detective.memes["certainty"] >= THRESHOLD,
        shared=snack.meters["shared"] >= THRESHOLD,
        clue=culprit_spec.clue,
        crumb=treat.crumb,
        opening_count=world.facts.get("opening_count", 0),
    )
    return world


@dataclass
class StoryParams:
    treat: str
    culprit: str
    hideout: str
    detective: str
    friend: str
    farmer: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "sharing": [
        ("What does sharing mean?",
         "Sharing means letting other people have some too instead of keeping everything for yourself. It helps a group feel fair and friendly.")
    ],
    "whodunit": [
        ("What is a whodunit story?",
         "A whodunit is a mystery story where everyone wonders who did something. The fun comes from following clues until the answer is found.")
    ],
    "griddle": [
        ("What does sizzle mean?",
         "Sizzle is the sound food makes when it touches a hot pan or griddle. It tells you the pan is hot and the food is cooking.")
    ],
    "trough": [
        ("What is a trough on a farm?",
         "A trough is a long container that holds water or feed for farm animals. Things that fall into the water can get soaked and messy.")
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a small sign that helps you figure something out. Footprints, feathers, and crumbs can all be clues in a mystery.")
    ],
    "mudprint": [
        ("What is a mudprint?",
         "A mudprint is a mark left when muddy feet touch the ground. It can show where someone walked.")
    ],
    "feather": [
        ("Why can a feather be a clue?",
         "A feather can show that a bird was nearby. In a mystery, it helps narrow down who might have been there.")
    ],
    "straw": [
        ("Why might chewed straw be a clue?",
         "Chewed straw can suggest that a goat or another nibbling animal was close by. Little signs like that help solve a puzzle.")
    ],
    "hoofprint": [
        ("What is a hoofprint?",
         "A hoofprint is the mark left by an animal with hooves, like a calf. Its shape can help you tell who passed by.")
    ],
}
KNOWLEDGE_ORDER = ["sharing", "whodunit", "griddle", "trough", "clue",
                   "mudprint", "feather", "straw", "hoofprint"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treat = f["treat"]
    culprit = f["culprit"]
    detective = f["detective"]
    friend = f["friend"]
    return [
        f'Write a gentle farmyard whodunit for a 3-to-5-year-old that includes the words "drown", "sizzle", and "awful". Make the mystery about a missing {treat.label} and end with sharing.',
        f"Tell a small mystery set in a farmyard where {detective.id} follows clues to a missing hot snack and discovers that {culprit.id} hid it for {friend.id}.",
        f'Write a child-facing story where a missing snack causes worry, but the answer turns out to be kindhearted. Use a whodunit feeling, then end with everyone sharing fairly.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    farmer = f["farmer"]
    detective = f["detective"]
    culprit = f["culprit"]
    friend = f["friend"]
    treat = f["treat"]
    hideout = f["hideout_cfg"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {detective.id}, {culprit.id}, {friend.id}, and {farmer.id} in the farmyard. They are all gathered around a hot snack meant to be shared."),
        (f"What was the mystery?",
         f"One {treat.label} was missing from the tray. That made everyone wonder who had taken it and why."),
        (f"How did the detective solve the mystery?",
         f"{detective.id} looked for a clue and followed it to {hideout.phrase}. The clue matched {culprit.id}, so the missing snack was found without guessing wildly."),
        (f"Why did {culprit.id} hide the {treat.label}?",
         f"{culprit.id} was trying to save a share for {friend.id}, who was late to the table. The hiding still worried everyone, but the reason came from wanting nobody to be left out."),
        ("Why does the story use the word 'drown'?",
         f"The animals worried that a hot snack could fall into the trough water and drown there, turning soggy and ruined. That gave the culprit an extra reason to tuck it somewhere dry."),
        ("How did the story end?",
         f"{farmer.id} explained that hiding food is confusing, then helped everyone share fairly. The ending image shows the mystery solved and the whole farmyard eating together."),
    ]
    if f.get("shared"):
        qa.append((
            f"What lesson did {farmer.id} teach?",
            f"{farmer.id} taught that it is kind to think about someone who arrived late, but it is better to ask first than to hide food. Sharing works best when everyone knows the plan."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing", "whodunit", "griddle", "clue"}
    if f["hideout_cfg"].near_water:
        tags.add("trough")
    else:
        tags.add("trough")
    clue = f["clue"]
    if clue == "mudprint":
        tags.add("mudprint")
    elif clue == "feather":
        tags.add("feather")
    elif clue == "chewed_straw":
        tags.add("straw")
    elif clue == "broad_hoof":
        tags.add("hoofprint")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {}
            for k, v in ent.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                else:
                    shown[k] = v
            bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:20} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("corncake", "piglet", "hay_nook", "sheepdog", "chick", "june"),
    StoryParams("apple_fritter", "duckling", "barrel_lid", "hen", "gosling", "sam"),
    StoryParams("oat_patty", "calf", "wheelbarrow", "donkey", "lamb", "june"),
    StoryParams("corncake", "goat_kid", "gate_step", "barn_cat", "chick", "sam"),
]


def explain_reach(culprit: AnimalSpec, hideout: Hideout) -> str:
    return (f"(No story: {culprit.label} cannot reasonably hide food at {hideout.phrase}. "
            f"Pick a hiding place the culprit can actually reach.)")


def explain_hideout(treat: Treat, hideout: Hideout) -> str:
    return (f"(No story: {hideout.phrase} is too wet for a hot {treat.label}. "
            f"{treat.soggy_line} Choose a dry hiding place instead.)")


def explain_detective(detective: Detective, culprit: AnimalSpec, treat: Treat) -> str:
    return (f"(No story: {detective.label} would not know how to read the clue left by "
            f"{culprit.label}. Pick a detective who can plausibly solve this mystery.)")


ASP_RULES = r"""
reachable(A, H) :- can_reach(A, H), hide_access(H, A).
safe_hideout(T, H) :- treat(T), hideout(H), dry(H), not near_water(H).
detective_can_solve(D, A, T) :- clue_of(A, C), reads(D, C).
detective_can_solve(D, A, T) :- treat_crumb(T, Cr), reads(D, Cr).

valid(T, A, H, D, F) :- treat(T), animal(A), hideout(H), detective(D), friend(F),
                        safe_hideout(T, H), reachable(A, H),
                        detective_can_solve(D, A, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("treat_crumb", tid, clue_token_for_treat(tid)))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("clue_of", aid, animal.clue))
        for hid in sorted(animal.reaches):
            lines.append(asp.fact("can_reach", aid, hid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        if hideout.dry:
            lines.append(asp.fact("dry", hid))
        if hideout.near_water:
            lines.append(asp.fact("near_water", hid))
        for aid in sorted(hideout.reachable_by):
            lines.append(asp.fact("hide_access", hid, aid))
    for did, det in DETECTIVES.items():
        lines.append(asp.fact("detective", did))
        for clue in sorted(det.reads):
            lines.append(asp.fact("reads", did, clue))
    for fid in LATE_FRIENDS:
        lines.append(asp.fact("friend", fid))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    # Smoke-test ordinary generation on curated and a few random seeds.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        sample.to_dict()
        print("OK: curated smoke test generated a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED on curated sample: {err}")

    parser = build_parser()
    for seed in range(5):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
            sample.to_dict()
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on random seed {seed}: {err}")
            break
    else:
        print("OK: random smoke tests generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A farmyard whodunit storyworld about a missing hot snack, clues, and sharing."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--culprit", choices=ANIMALS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--friend", choices=LATE_FRIENDS)
    ap.add_argument("--farmer", choices=FARMERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.hideout:
        if not hideout_is_reasonable(TREATS[args.treat], HIDEOUTS[args.hideout]):
            raise StoryError(explain_hideout(TREATS[args.treat], HIDEOUTS[args.hideout]))
    if args.culprit and args.hideout:
        if not culprit_can_reach(ANIMALS[args.culprit], HIDEOUTS[args.hideout]):
            raise StoryError(explain_reach(ANIMALS[args.culprit], HIDEOUTS[args.hideout]))
    if args.treat and args.culprit and args.detective:
        if not detective_can_solve(DETECTIVES[args.detective], ANIMALS[args.culprit], TREATS[args.treat]):
            raise StoryError(explain_detective(DETECTIVES[args.detective], ANIMALS[args.culprit], TREATS[args.treat]))

    combos = [c for c in valid_combos()
              if (args.treat is None or c[0] == args.treat)
              and (args.culprit is None or c[1] == args.culprit)
              and (args.hideout is None or c[2] == args.hideout)
              and (args.detective is None or c[3] == args.detective)
              and (args.friend is None or c[4] == args.friend)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat, culprit, hideout, detective, friend = rng.choice(sorted(combos))
    farmer = args.farmer or rng.choice(sorted(FARMERS))
    return StoryParams(treat, culprit, hideout, detective, friend, farmer)


def generate(params: StoryParams) -> StorySample:
    farmer_name = FARMERS[params.farmer][0]
    world = tell(
        TREATS[params.treat],
        ANIMALS[params.culprit],
        HIDEOUTS[params.hideout],
        DETECTIVES[params.detective],
        LATE_FRIENDS[params.friend],
        farmer_name=farmer_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(combos)} compatible (treat, culprit, hideout, detective, friend) combos:\n")
        for treat, culprit, hideout, detective, friend in combos:
            print(f"  {treat:13} {culprit:10} {hideout:11} {detective:10} {friend}")
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
            header = (f"### {p.treat}: culprit={p.culprit}, hideout={p.hideout}, "
                      f"detective={p.detective}, friend={p.friend}")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
