#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py
=============================================================

A small folk-tale story world about a missing village treasure, a hasty
allegation, and the patient work of reconciliation.

The seed word "allege" is included directly in the rendered story. The domain is
kept narrow on purpose: a child (or cousin/friend) wrongly alleges that another
child took an important object, a wise elder slows the quarrel, the true cause
is discovered in the physical world, and the pair are reconciled.

Run it
------
    python storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py
    python storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py --item bell --cause crow
    python storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py --item jar --cause crow
    python storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py --verify
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

# Make storyworlds/results.py importable when run directly from this nested dir:
#   storyworlds/worlds/gpt-5.4/allege_reconciliation_folk_tale.py
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "aunt"}
        male = {"boy", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    features: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    purpose: str
    trail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CauseCfg:
    id: str
    label: str
    intro: str
    clue: str
    found_text: str
    requires: set[str] = field(default_factory=set)
    place_needs: set[str] = field(default_factory=set)
    method_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MethodCfg:
    id: str
    label: str
    prompt: str
    action: str
    solves: set[str] = field(default_factory=set)
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


def _r_missing_stirs_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for role in ("accuser", "accused"):
        if role in world.entities:
            world.get(role).memes["worry"] += 1
    return []


def _r_accusation_hurts(world: World) -> list[str]:
    accuser = world.entities.get("accuser")
    accused = world.entities.get("accused")
    bond = world.entities.get("bond")
    if accuser is None or accused is None or bond is None:
        return []
    if accuser.memes["accusation"] < THRESHOLD:
        return []
    sig = ("accusation_hurts", accused.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accused.memes["hurt"] += 1
    bond.meters["strain"] += 1
    return []


def _r_truth_softens(world: World) -> list[str]:
    item = world.entities.get("item")
    accuser = world.entities.get("accuser")
    bond = world.entities.get("bond")
    if item is None or accuser is None or bond is None:
        return []
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("truth_softens", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accuser.memes["shame"] += 1
    accuser.memes["understanding"] += 1
    bond.meters["understanding"] += 1
    return []


def _r_apology_reconciles(world: World) -> list[str]:
    accuser = world.entities.get("accuser")
    accused = world.entities.get("accused")
    bond = world.entities.get("bond")
    if accuser is None or accused is None or bond is None:
        return []
    if accuser.memes["apology"] < THRESHOLD or accused.memes["forgiveness"] < THRESHOLD:
        return []
    sig = ("reconcile", "bond")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bond.meters["trust"] += 2
    bond.meters["strain"] = 0.0
    accused.memes["hurt"] = 0.0
    accuser.memes["relief"] += 1
    accused.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_stirs_worry", tag="emotion", apply=_r_missing_stirs_worry),
    Rule(name="accusation_hurts", tag="emotion", apply=_r_accusation_hurts),
    Rule(name="truth_softens", tag="emotion", apply=_r_truth_softens),
    Rule(name="apology_reconciles", tag="emotion", apply=_r_apology_reconciles),
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
            elif rule.name in {name for (name, *_) in world.fired}:
                continue
            else:
                # rule may still have mutated state without narration
                pass
        # continue until no rule adds new fired signatures
        current = len(world.fired)
        out_again = 0
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            _ = rule.apply(world)
            out_again += len(world.fired) - before
        if out_again:
            changed = True
        # avoid narrating second pass; only stability check
        if len(world.fired) == current and out_again == 0:
            break
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "cedar_hollow": Place(
        id="cedar_hollow",
        label="Cedar Hollow",
        opening="In the days when cedar smoke rose in blue threads above the roofs of Cedar Hollow,",
        features={"trees", "wind", "goats"},
    ),
    "reed_bank": Place(
        id="reed_bank",
        label="Reed Bank",
        opening="Long ago, beside the slow river at Reed Bank,",
        features={"river", "reeds", "wind", "crows"},
    ),
    "stone_path": Place(
        id="stone_path",
        label="Stone Path",
        opening="Where the mountain path bent between old prayer stones,",
        features={"wind", "crows", "goats"},
    ),
    "orchard_gate": Place(
        id="orchard_gate",
        label="Orchard Gate",
        opening="At Orchard Gate, where pear trees leaned over the lane,",
        features={"trees", "goats", "crows"},
    ),
}

ITEMS = {
    "bell": ItemCfg(
        id="bell",
        label="bell",
        phrase="the little silver bell from the shrine door",
        purpose="to ring the morning greeting",
        trail="a thin bright chime",
        ending_image="the bell laughed again above the door",
        tags={"shiny", "ringing", "light", "valuable"},
    ),
    "scarf": ItemCfg(
        id="scarf",
        label="scarf",
        phrase="the red festival scarf",
        purpose="to tie over the dance drum",
        trail="a ribbon of red cloth",
        ending_image="the red scarf fluttered from the drum once more",
        tags={"cloth", "light", "bright"},
    ),
    "seed_pouch": ItemCfg(
        id="seed_pouch",
        label="seed pouch",
        phrase="the small pouch of spring seeds",
        purpose="to begin the first planting",
        trail="a few millet seeds on the ground",
        ending_image="the seed pouch rested warm in careful hands",
        tags={"light", "grain", "valuable"},
    ),
    "jar": ItemCfg(
        id="jar",
        label="honey jar",
        phrase="the honey jar for the shared feast",
        purpose="to sweeten the evening cakes",
        trail="a gold smear and a bee or two",
        ending_image="the honey jar stood in the middle of the cloth, golden and safe",
        tags={"sweet", "heavy", "valuable"},
    ),
}

CAUSES = {
    "crow": CauseCfg(
        id="crow",
        label="a thieving crow",
        intro="a crow had seen a bright thing and hopped away with it",
        clue="high in a tree there came a sharp black caw and a glint among twigs",
        found_text="there, in a crow's nest, lay the missing thing",
        requires={"shiny", "light"},
        place_needs={"trees"},
        method_tags={"look_up"},
        tags={"crow", "tree"},
    ),
    "wind": CauseCfg(
        id="wind",
        label="a quick mountain wind",
        intro="a quick wind had lifted what was light enough to travel",
        clue="caught in the reeds or thorns was a familiar bit of color",
        found_text="caught in the reeds, the missing thing waited where the wind had dropped it",
        requires={"cloth", "light"},
        place_needs={"wind"},
        method_tags={"search_edges"},
        tags={"wind"},
    ),
    "goat": CauseCfg(
        id="goat",
        label="a nosy goat",
        intro="a nosy goat had tugged it away with busy teeth",
        clue="on the path were little hoof marks and a teasing trail",
        found_text="behind a wall, a goat stood chewing at the missing thing",
        requires={"grain", "sweet", "cloth"},
        place_needs={"goats"},
        method_tags={"follow_tracks"},
        tags={"goat", "tracks"},
    ),
}

METHODS = {
    "look_up": MethodCfg(
        id="look_up",
        label="look upward and listen",
        prompt="Let our eyes go high before our blame goes far.",
        action="They stood still, listened for wings, and searched the branches overhead.",
        solves={"crow"},
        tags={"listen", "look_up"},
    ),
    "search_edges": MethodCfg(
        id="search_edges",
        label="search the edges",
        prompt="What the wind borrows, it often leaves at the edge of things.",
        action="They walked slowly along reeds, fences, and thorny corners where light things liked to hide.",
        solves={"wind"},
        tags={"search", "edges"},
    ),
    "follow_tracks": MethodCfg(
        id="follow_tracks",
        label="follow the tracks",
        prompt="Small feet and hooves leave honest writing on dust.",
        action="They bent low to the ground and followed the little marks and scraps along the lane.",
        solves={"goat"},
        tags={"tracks"},
    ),
}


def cause_fits_place(cause: CauseCfg, place: Place) -> bool:
    return cause.place_needs.issubset(place.features)


def cause_fits_item(cause: CauseCfg, item: ItemCfg) -> bool:
    return bool(cause.requires & item.tags)


def method_fits_cause(method: MethodCfg, cause: CauseCfg) -> bool:
    return method.id in cause.method_tags or bool(method.tags & cause.method_tags) or cause.id in method.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                if not cause_fits_place(cause, place):
                    continue
                if not cause_fits_item(cause, item):
                    continue
                for method_id, method in METHODS.items():
                    if method_fits_cause(method, cause):
                        combos.append((place_id, item_id, cause_id, method_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    cause: str
    method: str
    accuser: str
    accuser_gender: str
    accused: str
    accused_gender: str
    elder_name: str
    elder_type: str
    relation: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Anu", "Pema", "Lila", "Sona", "Mira", "Tara", "Nima", "Rin"]
BOY_NAMES = ["Tenzin", "Kiran", "Dawa", "Milan", "Noru", "Hari", "Sanjay", "Batu"]
ELDER_NAMES = ["Grandmother Sita", "Grandfather Dorje", "Auntie Meera", "Uncle Puran"]
TRAITS = ["quick-tempered", "proud", "earnest", "hasty", "warm-hearted"]
RELATIONS = ["friends", "cousins"]

CURATED = [
    StoryParams(
        place="cedar_hollow",
        item="bell",
        cause="crow",
        method="look_up",
        accuser="Kiran",
        accuser_gender="boy",
        accused="Pema",
        accused_gender="girl",
        elder_name="Grandmother Sita",
        elder_type="grandmother",
        relation="friends",
        trait="hasty",
    ),
    StoryParams(
        place="reed_bank",
        item="scarf",
        cause="wind",
        method="search_edges",
        accuser="Mira",
        accuser_gender="girl",
        accused="Dawa",
        accused_gender="boy",
        elder_name="Uncle Puran",
        elder_type="uncle",
        relation="cousins",
        trait="proud",
    ),
    StoryParams(
        place="orchard_gate",
        item="jar",
        cause="goat",
        method="follow_tracks",
        accuser="Tara",
        accuser_gender="girl",
        accused="Noru",
        accused_gender="boy",
        elder_name="Auntie Meera",
        elder_type="aunt",
        relation="friends",
        trait="quick-tempered",
    ),
    StoryParams(
        place="stone_path",
        item="seed_pouch",
        cause="goat",
        method="follow_tracks",
        accuser="Sanjay",
        accuser_gender="boy",
        accused="Anu",
        accused_gender="girl",
        elder_name="Grandfather Dorje",
        elder_type="grandfather",
        relation="cousins",
        trait="earnest",
    ),
]


def relation_noun(relation: str) -> str:
    return "cousin" if relation == "cousins" else "friend"


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    place = PLACES[params.place]
    item_cfg = ITEMS[params.item]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    if not cause_fits_place(cause, place):
        raise StoryError(explain_rejection(place=place, item=item_cfg, cause=cause, method=method))
    if not cause_fits_item(cause, item_cfg):
        raise StoryError(explain_rejection(place=place, item=item_cfg, cause=cause, method=method))
    if not method_fits_cause(method, cause):
        raise StoryError(explain_rejection(place=place, item=item_cfg, cause=cause, method=method))

    world = World(place=place)
    accuser = world.add(Entity(
        id="accuser",
        kind="character",
        type=params.accuser_gender,
        label=params.accuser,
        phrase=params.accuser,
        role="accuser",
        traits=[params.trait],
        attrs={"name": params.accuser, "relation": params.relation},
    ))
    accused = world.add(Entity(
        id="accused",
        kind="character",
        type=params.accused_gender,
        label=params.accused,
        phrase=params.accused,
        role="accused",
        traits=["patient"],
        attrs={"name": params.accused, "relation": params.relation},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder_type,
        label=params.elder_name,
        phrase=params.elder_name,
        role="elder",
        traits=["wise", "calm"],
        attrs={"name": params.elder_name},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        tags=set(item_cfg.tags),
        attrs={"purpose": item_cfg.purpose},
    ))
    bond = world.add(Entity(
        id="bond",
        kind="thing",
        type="bond",
        label="friendship",
        phrase="their bond",
    ))
    bond.meters["trust"] = 1.0
    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        cause=cause,
        method=method,
        relation=params.relation,
    )
    return world


def folk_opening(world: World) -> None:
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    accuser = world.get("accuser")
    accused = world.get("accused")
    rel = relation_noun(world.facts["relation"])
    world.say(
        f"{place.opening} two {rel}s, {accuser.label} and {accused.label}, were trusted with {item_cfg.phrase} "
        f"{item_cfg.purpose}."
    )
    world.say(
        f"They carried it together as carefully as two children might carry a cup filled to the brim with moonlight."
    )


def loss(world: World) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    item_cfg = world.facts["item_cfg"]
    accuser = world.get("accuser")
    accused = world.get("accused")
    cause = world.facts["cause"]
    world.say(
        f"But when they reached the square, the {item_cfg.label} was gone. Only an empty place remained, and no child had seen the moment it slipped away."
    )
    if accuser.memes["worry"] >= THRESHOLD and accused.memes["worry"] >= THRESHOLD:
        world.say(
            f"{accuser.label}'s heart beat fast, and {accused.label} went quiet with worry."
        )
    world.facts["actual_cause_intro"] = cause.intro


def allege(world: World) -> None:
    accuser = world.get("accuser")
    accused = world.get("accused")
    item_cfg = world.facts["item_cfg"]
    rel = relation_noun(world.facts["relation"])
    accuser.memes["accusation"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In that hot and foolish moment, {accuser.label} was ready to allege that {accused.label} had taken the {item_cfg.label}."
    )
    world.say(
        f'"You were nearest to it," {accuser.label} said. "{rel.capitalize()} though you are, perhaps you hid it from me."'
    )
    if accused.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{accused.label} lifted {accused.pronoun('possessive')} chin, but the words stung like nettles."
        )


def elder_intervenes(world: World) -> None:
    elder = world.get("elder")
    accuser = world.get("accuser")
    accused = world.get("accused")
    method = world.facts["method"]
    world.para()
    world.say(
        f"Then {elder.label} came from the shade and stood between them, not with anger, but with a face as steady as an old well."
    )
    world.say(
        f'"A torn friendship is harder to mend than a lost object is to find," {elder.pronoun()} said. "{method.prompt}"'
    )
    world.say(
        f"{accuser.label} lowered {accuser.pronoun('possessive')} eyes, and {accused.label} waited without stepping away."
    )


def search(world: World) -> None:
    method = world.facts["method"]
    cause = world.facts["cause"]
    world.say(method.action)
    world.say(
        f"Soon they found a clue: {cause.clue}."
    )


def discover_truth(world: World) -> None:
    item = world.get("item")
    cause = world.facts["cause"]
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"And then they saw the truth plainly: {cause.found_text}."
    )
    world.say(
        "The world had played its own small trick, and no hand among them had stolen anything at all."
    )


def apology(world: World) -> None:
    accuser = world.get("accuser")
    accused = world.get("accused")
    item_cfg = world.facts["item_cfg"]
    accuser.memes["apology"] += 1
    accused.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    shame_bit = "with cheeks gone warm" if accuser.memes["shame"] >= THRESHOLD else "softly"
    world.para()
    world.say(
        f'{accuser.label} turned to {accused.label} {shame_bit}. "I was wrong," {accuser.pronoun()} said. "I let fear speak before truth. Forgive me for blaming you over the {item_cfg.label}."'
    )
    world.say(
        f'"I forgive you," {accused.label} answered. "Next time let us search together before sorrow grows teeth."'
    )


def reconcile(world: World) -> None:
    elder = world.get("elder")
    item_cfg = world.facts["item_cfg"]
    world.say(
        f"{elder.label} smiled the way elders smile when a storm passes without breaking the house."
    )
    world.say(
        f"Together they carried {item_cfg.phrase} back, and by evening {item_cfg.ending_image}."
    )
    if world.get("bond").meters["trust"] >= 2:
        world.say(
            "From that day on, when doubt came knocking, they opened the door to questions first and blame only last."
        )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    folk_opening(world)
    world.para()
    loss(world)
    allege(world)
    elder_intervenes(world)
    world.para()
    search(world)
    discover_truth(world)
    apology(world)
    reconcile(world)
    world.facts.update(
        accuser=world.get("accuser"),
        accused=world.get("accused"),
        elder=world.get("elder"),
        item=world.get("item"),
        bond=world.get("bond"),
        outcome="reconciled" if world.get("bond").meters["trust"] >= 2 else "strained",
        found=world.get("item").meters["found"] >= THRESHOLD,
        apologized=world.get("accuser").memes["apology"] >= THRESHOLD,
        forgave=world.get("accused").memes["forgiveness"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    item_cfg = f["item_cfg"]
    accuser = f["accuser"]
    accused = f["accused"]
    elder = f["elder"]
    cause = f["cause"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "allege" and ends in reconciliation.',
        f"Tell a village tale where {accuser.label} wrongly alleges that {accused.label} took {item_cfg.phrase}, but {elder.label} helps them find the truth and make peace.",
        f"Write a gentle folk tale set in {place.label} where a missing {item_cfg.label}, a mistaken blame, and {cause.label} lead to an apology and a mended friendship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    accuser = f["accuser"]
    accused = f["accused"]
    elder = f["elder"]
    item_cfg = f["item_cfg"]
    cause = f["cause"]
    method = f["method"]
    relation = relation_noun(f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two {relation}s, {accuser.label} and {accused.label}, and {elder.label}, who helps them. The trouble begins when {item_cfg.phrase} goes missing."
        ),
        (
            f"Why did {accuser.label} speak harshly to {accused.label}?",
            f"{accuser.label} grew frightened when the {item_cfg.label} disappeared and spoke before knowing the truth. Fear made {accuser.pronoun('object')} ready to allege that {accused.label} had taken it."
        ),
        (
            f"How did {elder.label} help?",
            f"{elder.label} did not choose a side right away. {elder.pronoun().capitalize()} told the children to slow down and {method.label}, so they could look for clues instead of feeding the quarrel."
        ),
    ]
    if f.get("found"):
        qa.append((
            f"What had really happened to the {item_cfg.label}?",
            f"It had not been stolen at all. {cause.label.capitalize()} had carried or tugged it away, and the children found it by following the clue the world left behind."
        ))
    if f.get("apologized") and f.get("forgave"):
        qa.append((
            "How were they reconciled?",
            f"{accuser.label} admitted being wrong and asked forgiveness, and {accused.label} forgave {accuser.pronoun('object')}. Their peace returned because truth was found and pride was set down."
        ))
    return qa


KNOWLEDGE = {
    "crow": [
        (
            "Why do crows sometimes carry shiny things?",
            "Crows notice bright little objects and may pick them up because they are curious. A shiny thing can catch a crow's eye from far away."
        )
    ],
    "wind": [
        (
            "What can wind do to light things?",
            "Wind can lift and push light things, especially cloth. That is why scarves and scraps can end up caught on bushes or reeds."
        )
    ],
    "goat": [
        (
            "Why might a goat tug at something on the ground?",
            "Goats nibble and pull at many things when they are curious. If something smells sweet or has seeds or cloth, a goat may bother it."
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks are marks left by feet or hooves. They can show where someone or something went."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means making peace after hurt or anger. It often begins when people tell the truth, say sorry, and forgive."
        )
    ],
    "blame": [
        (
            "Why is it better to ask questions before blaming?",
            "Asking questions helps you learn what really happened. Blame spoken too fast can hurt someone who did nothing wrong."
        )
    ],
    "bell": [
        (
            "What is a shrine bell for?",
            "A shrine bell is rung to call people gently or mark an important moment. Its clear sound helps everyone notice the start of something."
        )
    ],
    "scarf": [
        (
            "Why do people use scarves in festivals?",
            "Scarves can add color, warmth, and beauty to a celebration. A bright scarf can make music or dancing feel more festive."
        )
    ],
    "seed_pouch": [
        (
            "Why are seeds important in a village?",
            "Seeds are the beginning of future plants and food. A small pouch of seeds can hold great hope for a season."
        )
    ],
    "jar": [
        (
            "Why must a honey jar be carried carefully?",
            "A honey jar can spill or break if it is handled roughly. Carrying it carefully keeps the sweet food safe for everyone."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "reconciliation",
    "blame",
    "crow",
    "wind",
    "goat",
    "tracks",
    "bell",
    "scarf",
    "seed_pouch",
    "jar",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"reconciliation", "blame"}
    cause = f["cause"]
    item_cfg = f["item_cfg"]
    if cause.id == "goat":
        tags.add("tracks")
    tags.add(cause.id)
    tags.add(item_cfg.id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for (name, *_) in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, item: ItemCfg, cause: CauseCfg, method: MethodCfg) -> str:
    if not cause_fits_place(cause, place):
        needed = ", ".join(sorted(cause.place_needs))
        have = ", ".join(sorted(place.features))
        return (
            f"(No story: {cause.label} does not fit {place.label}. "
            f"It needs place features [{needed}], but this place offers [{have}].)"
        )
    if not cause_fits_item(cause, item):
        need = " / ".join(sorted(cause.requires))
        have = " / ".join(sorted(item.tags))
        return (
            f"(No story: {cause.label} would not plausibly carry or tug {item.phrase}. "
            f"The cause expects item traits like [{need}], but this item has [{have}].)"
        )
    if not method_fits_cause(method, cause):
        return (
            f"(No story: the method '{method.label}' would not reasonably reveal a case caused by {cause.label}. "
            f"Choose a search method matched to the clue.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
compatible_item(C, I) :- cause(C), item(I), requires_trait(C, T), has_trait(I, T).
fits_place(C, P) :- cause(C), place(P), needs_feature(C, F), has_feature(P, F).
solves(M, C) :- method(M), cause(C), method_for(M, C).

valid(P, I, C, M) :- place(P), item(I), cause(C), method(M),
                     compatible_item(C, I), fits_place(C, P), solves(M, C).

outcome(P, I, C, M, reconciled) :- valid(P, I, C, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for feat in sorted(place.features):
            lines.append(asp.fact("has_feature", pid, feat))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("has_trait", iid, tag))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for tag in sorted(cause.requires):
            lines.append(asp.fact("requires_trait", cid, tag))
        for feat in sorted(cause.place_needs):
            lines.append(asp.fact("needs_feature", cid, feat))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for cid in sorted(method.solves):
            lines.append(asp.fact("method_for", mid, cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_method", params.method),
        "chosen_valid :- valid(P, I, C, M), chosen_place(P), chosen_item(I), chosen_cause(C), chosen_method(M).",
        "chosen_outcome(reconciled) :- chosen_valid.",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mistaken allegation, a discovered truth, and reconciliation in folk-tale style."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--relation", choices=sorted(RELATIONS))
    ap.add_argument("--parent", dest="elder_type", choices=["grandmother", "grandfather", "aunt", "uncle"])
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


def _pick_elder(rng: random.Random, elder_type: Optional[str] = None) -> tuple[str, str]:
    if elder_type is not None:
        mapping = {
            "grandmother": "Grandmother Sita",
            "grandfather": "Grandfather Dorje",
            "aunt": "Auntie Meera",
            "uncle": "Uncle Puran",
        }
        return mapping[elder_type], elder_type
    choice = rng.choice([
        ("Grandmother Sita", "grandmother"),
        ("Grandfather Dorje", "grandfather"),
        ("Auntie Meera", "aunt"),
        ("Uncle Puran", "uncle"),
    ])
    return choice


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.cause and args.method:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        cause = CAUSES[args.cause]
        method = METHODS[args.method]
        if not (cause_fits_place(cause, place) and cause_fits_item(cause, item) and method_fits_cause(method, cause)):
            raise StoryError(explain_rejection(place=place, item=item, cause=cause, method=method))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        example_place = PLACES[args.place] if args.place in PLACES else next(iter(PLACES.values()))
        example_item = ITEMS[args.item] if args.item in ITEMS else next(iter(ITEMS.values()))
        example_cause = CAUSES[args.cause] if args.cause in CAUSES else next(iter(CAUSES.values()))
        example_method = METHODS[args.method] if args.method in METHODS else next(iter(METHODS.values()))
        raise StoryError(explain_rejection(place=example_place, item=example_item, cause=example_cause, method=example_method))

    place, item, cause, method = rng.choice(sorted(combos))
    accuser_gender = rng.choice(["girl", "boy"])
    accused_gender = rng.choice(["girl", "boy"])
    accuser = _pick_name(rng, accuser_gender)
    accused = _pick_name(rng, accused_gender, avoid=accuser)
    elder_name, elder_type = _pick_elder(rng, args.elder_type)
    relation = args.relation or rng.choice(RELATIONS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        item=item,
        cause=cause,
        method=method,
        accuser=accuser,
        accuser_gender=accuser_gender,
        accused=accused,
        accused_gender=accused_gender,
        elder_name=elder_name,
        elder_type=elder_type,
        relation=relation,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
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


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    item = ITEMS[params.item]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    if cause_fits_place(cause, place) and cause_fits_item(cause, item) and method_fits_cause(method, cause):
        return "reconciled"
    return "invalid"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure at seed {seed}.")
            break
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, cause, method) combos:\n")
        for place, item, cause, method in combos:
            print(f"  {place:12} {item:10} {cause:8} {method}")
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
            header = f"### {p.accuser} and {p.accused}: {p.item} / {p.cause} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
