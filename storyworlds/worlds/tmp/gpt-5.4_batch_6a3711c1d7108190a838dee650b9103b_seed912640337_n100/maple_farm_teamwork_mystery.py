#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/maple_farm_teamwork_mystery.py
=========================================================

A standalone storyworld for a tiny **maple-farm mystery**: two children notice
that an important small object is missing before a farm event, gather physical
clues, combine their different strengths, and solve the problem together.

The domain is intentionally narrow and constraint-checked. Not every missing
item belongs with every culprit or hiding place:

- a gust of wind can carry only light paper or cloth things
- a puppy is drawn to food smells and drags things to cozy spots
- a goat mouths paper and cloth and leaves hoof clues near the fence

The world model drives the prose: missingness raises worry, clues lower
uncertainty, teamwork raises confidence, and the ending image depends on whether
the recovered item is still neat or has to be mended first.

Run it
------
    python storyworlds/worlds/gpt-5.4/maple_farm_teamwork_mystery.py
    python storyworlds/worlds/gpt-5.4/maple_farm_teamwork_mystery.py --item banner --culprit wind
    python storyworlds/worlds/gpt-5.4/maple_farm_teamwork_mystery.py --item sapling_tag --culprit puppy
    python storyworlds/worlds/gpt-5.4/maple_farm_teamwork_mystery.py --all
    python storyworlds/worlds/gpt-5.4/maple_farm_teamwork_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/maple_farm_teamwork_mystery.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    texture: str
    use: str
    light: bool
    edible_smell: bool = False
    chewable: bool = False
    paper: bool = False
    cloth: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    kind: str
    move_rule: str
    rough: bool
    mark: str
    first_clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    fits: set[str]
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SkillPair:
    id: str
    clue_skill: str
    search_skill: str
    teamwork_line: str


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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("kid1", "kid2"):
        world.get(eid).memes["worry"] += 1
    return []


def _r_clues_confidence(world: World) -> list[str]:
    total = world.get("kid1").meters["clues"] + world.get("kid2").meters["clues"]
    if total < 2:
        return []
    sig = ("confidence",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("kid1", "kid2"):
        world.get(eid).memes["confidence"] += 1
    return []


def _r_teamwork_pride(world: World) -> list[str]:
    if world.get("team").meters["combined"] < THRESHOLD:
        return []
    sig = ("teamwork_pride",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("kid1", "kid2"):
        world.get(eid).memes["pride"] += 1
        world.get(eid).memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule("missing_worry", "emotional", _r_missing_worry),
    Rule("clues_confidence", "emotional", _r_clues_confidence),
    Rule("teamwork_pride", "social", _r_teamwork_pride),
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


def can_carry(culprit: Culprit, item: MissingItem) -> bool:
    if culprit.id == "wind":
        return item.light and (item.paper or item.cloth)
    if culprit.id == "puppy":
        return item.edible_smell or item.cloth
    if culprit.id == "goat":
        return item.chewable or item.paper or item.cloth
    return False


def valid_hiding(culprit: Culprit, place: HidingPlace) -> bool:
    return culprit.id in place.fits


def valid_combo(item: MissingItem, culprit: Culprit, place: HidingPlace) -> bool:
    return can_carry(culprit, item) and valid_hiding(culprit, place)


def recovered_damaged(item: MissingItem, culprit: Culprit) -> bool:
    return culprit.rough and (item.paper or item.cloth or item.chewable)


def damage_note(item: MissingItem, culprit: Culprit) -> str:
    if not recovered_damaged(item, culprit):
        return ""
    if culprit.id == "wind":
        return "Its corner was bent and damp with dew."
    if culprit.id == "puppy":
        return "One edge was rumpled from being dragged."
    return "A corner was nibbled and crinkled."
    

def predict_find(item: MissingItem, culprit: Culprit, place: HidingPlace) -> dict:
    return {
        "valid": valid_combo(item, culprit, place),
        "damaged": recovered_damaged(item, culprit),
    }


def setup_scene(world: World, kid1: Entity, kid2: Entity, grownup: Entity, item: MissingItem) -> None:
    for kid in (kid1, kid2):
        kid.memes["eager"] += 1
    world.say(
        f"Early one bright morning, {kid1.id} and {kid2.id} hurried across the maple farm "
        f"with {grownup.label_word}. Buckets hung by the sugar house, the air smelled sweet, "
        f"and today everyone was getting ready for visitors."
    )
    world.say(
        f"On the long farm table lay {item.phrase}, needed for {item.use}. "
        f"It looked {item.texture} in the pale sun."
    )


def discover_missing(world: World, kid1: Entity, kid2: Entity, item: MissingItem) -> None:
    world.get("item").meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {kid1.id} reached for the {item.label}, it was gone."
    )
    world.say(
        f"{kid2.id} stared at the empty spot. For one quiet second, the maple farm felt less like a busy morning "
        f"and more like a real mystery."
    )


def vow_to_help(world: World, grownup: Entity, kid1: Entity, kid2: Entity) -> None:
    world.say(
        f'"We can look carefully before we worry," said {grownup.label_word}. '
        f'"A farm keeps telling little truths if you notice them."'
    )
    world.say(
        f'{kid1.id} and {kid2.id} nodded. Neither of them knew the answer alone, but both wanted to help.'
    )


def find_first_clue(world: World, kid1: Entity, kid2: Entity, skills: SkillPair, culprit: Culprit) -> None:
    world.get("kid1").meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{kid1.id} used {skills.clue_skill} and found the first clue: {culprit.first_clue}."
    )
    world.say(
        f'"That means this was not just lost," {kid1.id} said. "Something carried it away."'
    )


def find_second_clue(world: World, kid1: Entity, kid2: Entity, skills: SkillPair, culprit: Culprit, place: HidingPlace) -> None:
    world.get("kid2").meters["clues"] += 1
    propagate(world, narrate=False)
    hint = {
        "wind": f"a little flutter of color pointing toward {place.phrase}",
        "puppy": f"a waggy trail of pawprints leading toward {place.phrase}",
        "goat": f"small hoof marks and one caught thread near {place.phrase}",
    }[culprit.id]
    world.say(
        f"{kid2.id} used {skills.search_skill} and found another clue: {hint}."
    )
    world.say(
        f"{skills.teamwork_line} Now the path of the mystery was starting to show."
    )


def deduce(world: World, kid1: Entity, kid2: Entity, culprit: Culprit, place: HidingPlace) -> None:
    team = world.get("team")
    team.meters["combined"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{culprit.mark}," whispered {kid2.id}. "{culprit.label.capitalize()}!"'
    )
    world.say(
        f'{kid1.id} looked from the clue to {place.phrase} and nodded. '
        f'"If we put our clues together, that is where we should search next."'
    )


def recover(world: World, kid1: Entity, kid2: Entity, item: MissingItem, culprit: Culprit, place: HidingPlace) -> None:
    item_ent = world.get("item")
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] += 1
    if recovered_damaged(item, culprit):
        item_ent.meters["damaged"] += 1
    world.say(
        f"They hurried to {place.phrase}. There, {place.finish}, lay the {item.label}."
    )
    note = damage_note(item, culprit)
    if note:
        world.say(note)
    else:
        world.say("It was still neat enough to use right away.")
    if culprit.id == "wind":
        world.say(
            "It had not meant any harm. The morning gust had simply teased it away."
        )
    elif culprit.id == "puppy":
        world.say(
            "The puppy thumped its tail as if the whole thing had been a game."
        )
    else:
        world.say(
            "The goat blinked over the fence as if it had never heard of mysteries at all."
        )


def repair_or_use(world: World, grownup: Entity, kid1: Entity, kid2: Entity, item: MissingItem) -> None:
    item_ent = world.get("item")
    if item_ent.meters["damaged"] >= THRESHOLD:
        world.say(
            f"{grownup.label_word.capitalize()} smoothed the {item.label} while {kid1.id} held one side and {kid2.id} held the other. "
            f"Together they made it ready again."
        )
    else:
        world.say(
            f"{grownup.label_word.capitalize()} laughed softly. "
            f'"So that was our mystery," {grownup.pronoun()} said.'
        )
    world.say(
        f"Soon the {item.label} was back where it belonged, ready for {item.use}."
    )


def ending(world: World, kid1: Entity, kid2: Entity, item: MissingItem) -> None:
    if world.get("item").meters["damaged"] >= THRESHOLD:
        world.say(
            f"When the first visitors came to the maple farm, they saw the {item.label} standing proud again. "
            f"{kid1.id} and {kid2.id} smiled at each other, because they had solved the mystery with four careful hands instead of two."
        )
    else:
        world.say(
            f"When the first visitors came to the maple farm, the {item.label} was waiting in its proper place. "
            f"{kid1.id} and {kid2.id} smiled at each other, because the mystery had been small, but their teamwork had been big."
        )


def tell(
    item: MissingItem,
    culprit: Culprit,
    place: HidingPlace,
    skills: SkillPair,
    kid1_name: str = "Mira",
    kid1_type: str = "girl",
    kid2_name: str = "Owen",
    kid2_type: str = "boy",
    grownup_type: str = "aunt",
) -> World:
    world = World()
    kid1 = world.add(Entity(id="kid1", kind="character", type=kid1_type, label=kid1_name, role="clue_finder"))
    kid1.id = kid1_name
    del world.entities["kid1"]
    world.entities[kid1_name] = kid1

    kid2 = world.add(Entity(id="kid2", kind="character", type=kid2_type, label=kid2_name, role="searcher"))
    kid2.id = kid2_name
    del world.entities["kid2"]
    world.entities[kid2_name] = kid2

    # stable aliases for rules
    world.entities["kid1"] = kid1
    world.entities["kid2"] = kid2

    grownup = world.add(Entity(id="grown", kind="character", type=grownup_type, label="the grown-up", role="grownup"))
    team = world.add(Entity(id="team", type="team", label="the team"))
    item_ent = world.add(Entity(id="item", type="item", label=item.label))
    culprit_ent = world.add(Entity(id="culprit", type=culprit.kind, label=culprit.label))
    place_ent = world.add(Entity(id="place", type="place", label=place.label))
    _ = (culprit_ent, place_ent, item_ent)

    setup_scene(world, kid1, kid2, grownup, item)
    world.para()
    discover_missing(world, kid1, kid2, item)
    vow_to_help(world, grownup, kid1, kid2)
    world.para()
    find_first_clue(world, kid1, kid2, skills, culprit)
    find_second_clue(world, kid1, kid2, skills, culprit, place)
    deduce(world, kid1, kid2, culprit, place)
    world.para()
    recover(world, kid1, kid2, item, culprit, place)
    repair_or_use(world, grownup, kid1, kid2, item)
    world.para()
    ending(world, kid1, kid2, item)

    world.facts.update(
        kid1=kid1,
        kid2=kid2,
        grownup=grownup,
        item_cfg=item,
        culprit_cfg=culprit,
        place_cfg=place,
        skills=skills,
        damaged=world.get("item").meters["damaged"] >= THRESHOLD,
        recovered=world.get("item").meters["found"] >= THRESHOLD,
    )
    return world


ITEMS = {
    "banner": MissingItem(
        "banner",
        "maple banner",
        "a red maple banner",
        "bright and soft",
        "the front welcome table",
        light=True,
        chewable=True,
        cloth=True,
        tags={"banner", "cloth", "maple"},
    ),
    "recipe_card": MissingItem(
        "recipe_card",
        "maple recipe card",
        "a hand-lettered maple recipe card",
        "smooth and tidy",
        "the tasting table",
        light=True,
        chewable=True,
        paper=True,
        edible_smell=True,
        tags={"paper", "recipe", "maple"},
    ),
    "sapling_tag": MissingItem(
        "sapling_tag",
        "maple sapling tag",
        "a paper tag for the youngest maple sapling",
        "small and fluttery",
        "the row of baby maple trees",
        light=True,
        chewable=True,
        paper=True,
        tags={"paper", "tree", "maple"},
    ),
    "scarf": MissingItem(
        "scarf",
        "maple-leaf scarf",
        "a maple-leaf scarf",
        "striped and cozy",
        "the little music stage",
        light=True,
        chewable=True,
        cloth=True,
        tags={"cloth", "scarf", "maple"},
    ),
}

CULPRITS = {
    "wind": Culprit(
        "wind",
        "the wind",
        "weather",
        "light paper or cloth only",
        rough=False,
        "A loose trail does not look like paws or hooves.",
        "a tiny red flap caught on a splinter",
        tags={"wind"},
    ),
    "puppy": Culprit(
        "puppy",
        "the farm puppy",
        "animal",
        "cloth or food-smelling things",
        rough=True,
        "Round pawprints dotted the dust.",
        "two muddy pawprints under the table",
        tags={"puppy", "paws"},
    ),
    "goat": Culprit(
        "goat",
        "the fence goat",
        "animal",
        "paper or cloth things it can mouth",
        rough=True,
        "Tiny hoof marks lined up by the boards.",
        "a chewed paper fleck near the fence gate",
        tags={"goat", "hooves"},
    ),
}

PLACES = {
    "fence_corner": HidingPlace(
        "fence_corner",
        "the fence corner",
        "the fence corner by the clover patch",
        {"goat", "wind"},
        "half tucked under the lowest rail",
        tags={"fence"},
    ),
    "porch_bench": HidingPlace(
        "porch_bench",
        "the porch bench",
        "the porch bench beside the mudroom door",
        {"puppy", "wind"},
        "curled against a boot and a sleepy tail",
        tags={"porch"},
    ),
    "sap_bucket": HidingPlace(
        "sap_bucket",
        "the empty sap bucket",
        "an empty sap bucket near the sugar house wall",
        {"wind"},
        "resting in the bottom like a secret",
        tags={"bucket"},
    ),
    "hay_bale": HidingPlace(
        "hay_bale",
        "the hay bale",
        "the hay bale stack in the little barn",
        {"puppy"},
        "nestled in the straw",
        tags={"hay"},
    ),
}

SKILLS = {
    "careful_fast": SkillPair(
        "careful_fast",
        "quiet eyes that noticed small things",
        "quick feet that followed a trail",
        "One noticed; the other moved first.",
    ),
    "high_low": SkillPair(
        "high_low",
        "the habit of looking up and around",
        "the habit of peeking under benches and rails",
        "They searched in different ways, and that made the clues fit together.",
    ),
    "listen_reach": SkillPair(
        "listen_reach",
        "patient listening to the sounds around the yard",
        "steady hands for checking tight little corners",
        "Because they did not copy each other, they found more than either one would have alone.",
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Tess", "Ruby", "Nell", "Ivy", "Clara", "June"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Cal", "Noah", "Jude", "Milo", "Beck"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for item_id, item in ITEMS.items():
        for culprit_id, culprit in CULPRITS.items():
            for place_id, place in PLACES.items():
                if valid_combo(item, culprit, place):
                    out.append((item_id, culprit_id, place_id))
    return sorted(out)


@dataclass
class StoryParams:
    item: str
    culprit: str
    place: str
    skills: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    grownup: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "maple": [
        (
            "What is maple syrup made from?",
            "Maple syrup is made from sap that comes from maple trees. People boil the sap until it becomes thick and sweet."
        )
    ],
    "farm": [
        (
            "What is a farm?",
            "A farm is a place where people grow plants or care for animals. Different jobs on a farm often need many helping hands."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other and combine different strengths. A problem can become easier when one person notices something and another person acts on it."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle with missing information that must be figured out. Clues help people understand what happened."
        )
    ],
    "wind": [
        (
            "How can wind move things?",
            "Wind can push light things like paper or cloth. A strong gust may carry them to a new place."
        )
    ],
    "puppy": [
        (
            "Why do puppies carry things away?",
            "Puppies often grab things because they are playful or because something smells interesting. They do not mean to be sneaky in a bad way."
        )
    ],
    "goat": [
        (
            "Why do goats nibble things?",
            "Goats explore with their mouths and may nibble paper or cloth. That is why loose things should be kept away from curious goats."
        )
    ],
}
KNOWLEDGE_ORDER = ["maple", "farm", "teamwork", "mystery", "wind", "puppy", "goat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    place = f["place_cfg"]
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the words "maple" and "farm" and shows teamwork.',
        f"Tell a gentle farm mystery where {kid1.id} and {kid2.id} must find a missing {item.label} by following clues together.",
        f"Write a child-facing mystery in which {culprit.label} leads to clues near {place.label}, and the ending shows that working together solves the problem."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1, kid2, grown = f["kid1"], f["kid2"], f["grownup"]
    item, culprit, place = f["item_cfg"], f["culprit_cfg"], f["place_cfg"]
    skills = f["skills"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {kid1.id} and {kid2.id} on a maple farm. They work together to solve a small mystery before visitors arrive."
        ),
        (
            f"What went missing?",
            f"The missing thing was the {item.label}. It was needed for {item.use}, so the children knew they had to find it quickly."
        ),
        (
            "Why did the morning feel like a mystery?",
            f"The {item.label} vanished from its proper spot, and there were clues showing it had been carried away. That turned an ordinary farm chore into a puzzle."
        ),
        (
            f"How did {kid1.id} and {kid2.id} use teamwork?",
            f"{kid1.id} helped by using {skills.clue_skill}, and {kid2.id} helped by using {skills.search_skill}. They solved the mystery because each child found a different part of the answer."
        ),
        (
            f"What clues told them where to look?",
            f"They found {culprit.first_clue}, and then they found a trail leading toward {place.phrase}. Those clues helped them guess who had moved the {item.label} and where it had gone."
        ),
        (
            f"Where did they find the {item.label}?",
            f"They found it at {place.phrase}. The clues matched that place, so their careful search paid off."
        ),
    ]
    if f["damaged"]:
        qa.append(
            (
                f"Was the {item.label} still perfect when they found it?",
                f"No. It was a little damaged, but the children and {grown.label_word} fixed it together. The repair becomes part of the solution, not a new problem."
            )
        )
    else:
        qa.append(
            (
                f"How did the story end?",
                f"The {item.label} was back in its proper place before the visitors came. The ending shows that the mystery is over and the farm is ready again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"maple", "farm", "teamwork", "mystery", world.facts["culprit_cfg"].id}
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
    seen_ids = set()
    for eid, ent in world.entities.items():
        if eid in seen_ids:
            continue
        seen_ids.add(eid)
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("recipe_card", "puppy", "hay_bale", "careful_fast", "Mira", "girl", "Owen", "boy", "aunt"),
    StoryParams("sapling_tag", "wind", "sap_bucket", "high_low", "Ruby", "girl", "Finn", "boy", "uncle"),
    StoryParams("banner", "goat", "fence_corner", "listen_reach", "Ivy", "girl", "Cal", "boy", "aunt"),
    StoryParams("scarf", "puppy", "porch_bench", "high_low", "June", "girl", "Noah", "boy", "father"),
    StoryParams("banner", "wind", "fence_corner", "careful_fast", "Clara", "girl", "Eli", "boy", "mother"),
]


def explain_rejection(item: MissingItem, culprit: Culprit, place: Optional[HidingPlace] = None) -> str:
    if not can_carry(culprit, item):
        return (
            f"(No story: {culprit.label} would not reasonably carry the {item.label}. "
            f"Pick a lighter paper or cloth item for wind, a food-smelling or cloth item for the puppy, "
            f"or a paper/cloth item for the goat.)"
        )
    if place is not None and not valid_hiding(culprit, place):
        return (
            f"(No story: {place.label} is not a plausible place for {culprit.label} in this small mystery. "
            f"Choose a hiding place that fits that culprit's path.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
% capability rules
can_carry(C, I) :- culprit(C), item(I), culprit_is(C, wind), light(I), paper(I).
can_carry(C, I) :- culprit(C), item(I), culprit_is(C, wind), light(I), cloth(I).
can_carry(C, I) :- culprit(C), item(I), culprit_is(C, puppy), edible_smell(I).
can_carry(C, I) :- culprit(C), item(I), culprit_is(C, puppy), cloth(I).
can_carry(C, I) :- culprit(C), item(I), culprit_is(C, goat), chewable(I).
can_carry(C, I) :- culprit(C), item(I), culprit_is(C, goat), paper(I).
can_carry(C, I) :- culprit(C), item(I), culprit_is(C, goat), cloth(I).

valid(I, C, P) :- item(I), culprit(C), place(P), can_carry(C, I), fits(P, C).

chosen_valid :- chosen_item(I), chosen_culprit(C), chosen_place(P), valid(I, C, P).

damaged :- chosen_valid, chosen_culprit(C), rough(C), chosen_item(I), paper(I).
damaged :- chosen_valid, chosen_culprit(C), rough(C), chosen_item(I), cloth(I).
damaged :- chosen_valid, chosen_culprit(C), rough(C), chosen_item(I), chewable(I).

outcome(neat) :- chosen_valid, not damaged.
outcome(mended) :- chosen_valid, damaged.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.light:
            lines.append(asp.fact("light", item_id))
        if item.edible_smell:
            lines.append(asp.fact("edible_smell", item_id))
        if item.chewable:
            lines.append(asp.fact("chewable", item_id))
        if item.paper:
            lines.append(asp.fact("paper", item_id))
        if item.cloth:
            lines.append(asp.fact("cloth", item_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_is", culprit_id, culprit_id))
        if culprit.rough:
            lines.append(asp.fact("rough", culprit_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for fit in sorted(place.fits):
            lines.append(asp.fact("fits", place_id, fit))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    place = PLACES[params.place]
    if not valid_combo(item, culprit, place):
        return "invalid"
    return "mended" if recovered_damaged(item, culprit) else "neat"


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_place", params.place),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a teamwork mystery on a maple farm."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--skills", choices=SKILLS)
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
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
    if args.item and args.culprit:
        item = ITEMS[args.item]
        culprit = CULPRITS[args.culprit]
        if not can_carry(culprit, item):
            raise StoryError(explain_rejection(item, culprit))
    if args.item and args.culprit and args.place:
        item = ITEMS[args.item]
        culprit = CULPRITS[args.culprit]
        place = PLACES[args.place]
        if not valid_combo(item, culprit, place):
            raise StoryError(explain_rejection(item, culprit, place))

    combos = [
        c
        for c in valid_combos()
        if (args.item is None or c[0] == args.item)
        and (args.culprit is None or c[1] == args.culprit)
        and (args.place is None or c[2] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item, culprit, place = rng.choice(combos)
    skills = args.skills or rng.choice(sorted(SKILLS))
    kid1_gender = rng.choice(["girl", "boy"])
    kid2_gender = "boy" if kid1_gender == "girl" else "girl"
    kid1 = _pick_name(rng, kid1_gender)
    kid2 = _pick_name(rng, kid2_gender, avoid=kid1)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(item, culprit, place, skills, kid1, kid1_gender, kid2, kid2_gender, grownup)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ITEMS[params.item],
        CULPRITS[params.culprit],
        PLACES[params.place],
        SKILLS[params.skills],
        params.kid1,
        params.kid1_gender,
        params.kid2,
        params.kid2_gender,
        params.grownup,
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
        print(f"{len(combos)} compatible (item, culprit, place) combos:\n")
        for item, culprit, place in combos:
            print(f"  {item:12} {culprit:8} {place}")
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
            header = f"### {p.kid1} & {p.kid2}: {p.item} / {p.culprit} / {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
