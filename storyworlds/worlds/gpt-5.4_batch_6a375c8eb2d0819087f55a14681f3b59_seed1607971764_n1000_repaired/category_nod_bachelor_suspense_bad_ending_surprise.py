#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/category_nod_bachelor_suspense_bad_ending_surprise.py
=================================================================================

A standalone story world for a small detective-style fair mystery.

Seed brief
----------
Words: category, nod, bachelor
Features: Suspense, Bad Ending, Surprise
Style: Detective Story

This world models a child detective at a town fair. A card goes missing from a
display category just before judging. A nearby bachelor may be a helpful witness
or the hidden culprit. The children read clues, follow or distrust a suspicious
nod, and either recover the missing card in time or reach a bad ending where the
judging bell rings too soon.

Run it
------
    python storyworlds/worlds/gpt-5.4/category_nod_bachelor_suspense_bad_ending_surprise.py
    python storyworlds/worlds/gpt-5.4/category_nod_bachelor_suspense_bad_ending_surprise.py --category vegetables
    python storyworlds/worlds/gpt-5.4/category_nod_bachelor_suspense_bad_ending_surprise.py --suspect bachelor --trust trust --delay 1
    python storyworlds/worlds/gpt-5.4/category_nod_bachelor_suspense_bad_ending_surprise.py --all
    python storyworlds/worlds/gpt-5.4/category_nod_bachelor_suspense_bad_ending_surprise.py --qa --json
    python storyworlds/worlds/gpt-5.4/category_nod_bachelor_suspense_bad_ending_surprise.py --verify
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
DEADLINE = 2


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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father", "bachelor"}
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
class CategoryCfg:
    id: str
    label: str
    item: str
    board: str
    scene: str
    rival: str
    clue: str
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
class SpotCfg:
    id: str
    label: str
    phrase: str
    access: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    risk: int = 0
    condition: str = ""
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
class SuspectCfg:
    id: str
    label: str
    type: str
    role_text: str
    motive: str
    access: set[str] = field(default_factory=set)
    deceptive: bool = False
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


def propagate(world: World) -> None:
    card = world.get("card")
    hero = world.get("hero")
    partner = world.get("partner")
    fair = world.get("fair")

    if card.meters["missing"] >= THRESHOLD and ("danger",) not in world.fired:
        world.fired.add(("danger",))
        fair.meters["danger"] += 1
        hero.memes["worry"] += 1
        partner.memes["worry"] += 1

    if fair.meters["ticks"] >= DEADLINE and ("late",) not in world.fired:
        world.fired.add(("late",))
        fair.meters["late"] += 1
        hero.memes["dread"] += 1
        partner.memes["dread"] += 1

    spot_cfg = world.facts["spot_cfg"]
    if (
        card.meters["hidden"] >= THRESHOLD
        and fair.meters["ticks"] + spot_cfg.risk >= 3
        and ("ruined",) not in world.fired
    ):
        world.fired.add(("ruined",))
        card.meters["ruined"] += 1
        hero.memes["sadness"] += 1
        partner.memes["sadness"] += 1


CATEGORIES = {
    "vegetables": CategoryCfg(
        id="vegetables",
        label="vegetable category",
        item="a giant striped pumpkin",
        board="the vegetable category board",
        scene="rows of baskets and crooked prize pumpkins",
        rival="a neat squash display",
        clue="a dusting of dry pumpkin seeds",
        tags={"fair", "category", "pumpkin"},
    ),
    "crafts": CategoryCfg(
        id="crafts",
        label="craft category",
        item="a knitted duck with button eyes",
        board="the craft category table",
        scene="bright yarn, paper rosettes, and neat little models",
        rival="a polished toy boat",
        clue="a tiny strand of blue yarn",
        tags={"fair", "category", "craft"},
    ),
    "pets": CategoryCfg(
        id="pets",
        label="pet category",
        item="a snowy rabbit in a clean pen",
        board="the pet category rail",
        scene="soft straw, brushing combs, and little pens in a row",
        rival="a glossy white pigeon cage",
        clue="a pinch of straw",
        tags={"fair", "category", "rabbit"},
    ),
}

SPOTS = {
    "soup_crate": SpotCfg(
        id="soup_crate",
        label="soup crate",
        phrase="inside a crate under the soup table",
        access={"bachelor"},
        categories={"vegetables"},
        risk=2,
        condition="the paper edges were soft with steam",
        tags={"crate", "steam"},
    ),
    "yarn_box": SpotCfg(
        id="yarn_box",
        label="yarn box",
        phrase="inside a box of spare yarn under the long craft bench",
        access={"bachelor", "clerk"},
        categories={"crafts"},
        risk=1,
        condition="the card was bent but still readable",
        tags={"box", "yarn"},
    ),
    "feed_bin": SpotCfg(
        id="feed_bin",
        label="feed bin",
        phrase="in the feed bin behind the pet rail",
        access={"bachelor"},
        categories={"pets"},
        risk=2,
        condition="one corner was chewed and damp",
        tags={"bin", "straw"},
    ),
    "stamp_drawer": SpotCfg(
        id="stamp_drawer",
        label="stamp drawer",
        phrase="in the little stamp drawer beside the judge's desk",
        access={"clerk"},
        categories={"vegetables", "crafts", "pets"},
        risk=0,
        condition="the card was flat and clean",
        tags={"drawer", "desk"},
    ),
}

SUSPECTS = {
    "bachelor": SuspectCfg(
        id="bachelor",
        label="Mr. Vale",
        type="bachelor",
        role_text="the quiet bachelor from the brick house by the corner",
        motive="wanted his own exhibit to win without competition",
        access={"soup_crate", "yarn_box", "feed_bin"},
        deceptive=True,
        tags={"bachelor", "rival"},
    ),
    "clerk": SuspectCfg(
        id="clerk",
        label="Miss Finch",
        type="woman",
        role_text="the tired fair clerk with an ink-smudged thumb",
        motive="was rushing and hid the card by mistake while sorting papers",
        access={"yarn_box", "stamp_drawer"},
        deceptive=False,
        tags={"clerk", "desk"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Nora", "Ivy", "Lucy", "June", "Ada", "Ruby"]
BOY_NAMES = ["Theo", "Ben", "Max", "Owen", "Finn", "Leo", "Eli", "Sam"]
PARTNER_GIRL_NAMES = ["Tess", "Maya", "Poppy", "Wren", "Zoe", "Ella"]
PARTNER_BOY_NAMES = ["Ned", "Jack", "Milo", "Noah", "Cole", "Hugo"]
TRAITS = ["careful", "sharp-eyed", "steady", "curious", "patient", "brave"]


def valid_combo(category: str, suspect: str, spot: str) -> bool:
    if category not in CATEGORIES or suspect not in SUSPECTS or spot not in SPOTS:
        return False
    return (
        category in SPOTS[spot].categories
        and spot in SUSPECTS[suspect].access
        and suspect in SPOTS[spot].access
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for category in CATEGORIES:
        for suspect in SUSPECTS:
            for spot in SPOTS:
                if valid_combo(category, suspect, spot):
                    out.append((category, suspect, spot))
    return out


def effective_delay(params: "StoryParams") -> int:
    extra = 1 if params.suspect == "bachelor" and params.trust == "trust" else 0
    return params.delay + extra


def outcome_of(params: "StoryParams") -> str:
    if not valid_combo(params.category, params.suspect, params.spot):
        raise StoryError("(No story: that suspect could not reasonably hide the card in that place.)")
    delay_now = effective_delay(params)
    ruined = SPOTS[params.spot].risk + delay_now >= 3
    late = delay_now >= DEADLINE
    return "lost" if ruined or late else "found"


@dataclass
class StoryParams:
    category: str
    suspect: str
    spot: str
    trust: str = "doubt"
    delay: int = 0
    hero: str = "Mira"
    hero_gender: str = "girl"
    partner: str = "Ned"
    partner_gender: str = "boy"
    parent: str = "mother"
    trait: str = "careful"
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


def introduce(world: World, category: CategoryCfg, hero: Entity, partner: Entity, parent: Entity) -> None:
    world.say(
        f"By late afternoon, {hero.id}, {partner.id}, and {hero.pronoun('possessive')} "
        f"{parent.label_word} walked into the town fair hall. The place was full of "
        f"{category.scene}, and every aisle seemed to hide a little mystery."
    )
    world.say(
        f"{hero.id} liked pretending to be a detective, and {partner.id} liked being the one "
        f"who noticed what other people missed."
    )


def setup_case(world: World, category: CategoryCfg, hero: Entity, partner: Entity) -> None:
    card = world.get("card")
    card.meters["missing"] += 1
    propagate(world)
    world.say(
        f"They stopped beside {category.board}, where {category.item} should have had its card pinned neatly in place."
    )
    world.say(
        f"But the line for the {category.label} had a blank gap instead. The category card was gone."
    )
    world.say(
        f'"Judging starts very soon," {partner.id} whispered. At once the case felt real, and the air seemed tighter.'
    )


def meet_bachelor(world: World, hero: Entity, bachelor: Entity, category: CategoryCfg, trust: str, guilty: bool) -> None:
    world.say(
        f"Nearby stood {bachelor.label}, {bachelor.attrs['role_text']}, beside {bachelor.attrs['rival']}."
    )
    if guilty and trust == "trust":
        world.say(
            f'When {hero.id} asked if he had seen the missing card, he gave a quick nod toward the wrong aisle and said, '
            f'"I think I saw someone hurrying past the ribbon stand."'
        )
        world.get("fair").meters["ticks"] += 1
        propagate(world)
        hero.memes["trust"] += 1
        world.facts["false_lead"] = True
    elif guilty:
        world.say(
            f'When {hero.id} asked if he had seen the missing card, he gave a small nod, but it looked too quick and too neat. '
            f'{hero.id} felt a pinch of suspicion instead of comfort.'
        )
        hero.memes["suspicion"] += 1
        world.facts["false_lead"] = False
    else:
        world.say(
            f'When {hero.id} asked if he had seen the missing card, he gave a worried nod toward the judge\'s desk and said, '
            f'"Someone was sorting papers there in a terrible hurry."'
        )
        hero.memes["trust"] += 1
        world.facts["false_lead"] = False


def inspect_clue(world: World, category: CategoryCfg, hero: Entity, partner: Entity, suspect: SuspectCfg) -> None:
    world.say(
        f"Then {partner.id} crouched by the empty pin and found {category.clue}."
    )
    if suspect.id == "bachelor":
        world.say(
            f'That clue did not belong near the desk at all. It pointed back toward {SUSPECTS["bachelor"].label} and his part of the hall.'
        )
    else:
        world.say(
            "That clue looked less like a theft and more like a rushed mistake, the kind a tired worker could make."
        )
    hero.memes["suspicion"] += 1


def search_spot(world: World, spot: SpotCfg, hero: Entity, partner: Entity) -> None:
    world.get("fair").meters["ticks"] += 1
    propagate(world)
    world.say(
        f"The children followed the trail and searched {spot.phrase}."
    )
    card = world.get("card")
    card.meters["hidden"] += 1
    propagate(world)
    if card.meters["ruined"] >= THRESHOLD:
        world.say(
            f"There it was at last, but {spot.condition}."
        )
    else:
        world.say(
            f"There it was at last, and {spot.condition}."
        )


def reveal_found(world: World, hero: Entity, partner: Entity, suspect: SuspectCfg, category: CategoryCfg) -> None:
    card = world.get("card")
    fair = world.get("fair")
    card.meters["missing"] = 0.0
    card.meters["found"] += 1
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f'{hero.id} snatched up the card and ran it to the judge before the last bell. "It belongs with {category.item}," '
        f'{hero.pronoun()} panted.'
    )
    if suspect.id == "bachelor":
        world.say(
            f"{SUSPECTS['bachelor'].label}'s smile slipped for one second. That was surprise enough for any detective."
        )
    else:
        world.say(
            f"{SUSPECTS['clerk'].label} pressed a hand to her cheek and admitted she had tucked it away while hurrying."
        )
    fair.meters["saved"] += 1
    world.say(
        f"Soon the card was back in the right category place, and the hall no longer felt like a trap."
    )


def reveal_lost(world: World, hero: Entity, partner: Entity, suspect: SuspectCfg, category: CategoryCfg) -> None:
    fair = world.get("fair")
    hero.memes["sadness"] += 1
    partner.memes["sadness"] += 1
    fair.meters["lost"] += 1
    if suspect.id == "bachelor":
        world.say(
            f"Before they could fix anything, the judging bell rang. In the biggest surprise of all, the blue ribbon went onto "
            f"{SUSPECTS['bachelor'].label}'s own display."
        )
        world.say(
            f"Only then did the children understand the neat little nod and the wrong direction. The bachelor had hidden the card because he {suspect.motive}."
        )
    else:
        world.say(
            f"Before they could fix anything, the judging bell rang. Then {SUSPECTS['clerk'].label} opened the wrong drawer, gasped, and found the card too late."
        )
        world.say(
            f"The surprise was not a sneaky thief after all, but a foolish mistake that still ruined the day."
        )
    if world.get("card").meters["ruined"] >= THRESHOLD:
        world.say(
            f"The card could not be used anyway, and {category.item} stood in its place with no proper paper beside it."
        )
    else:
        world.say(
            f"The card was still real evidence, but the time for that category had already passed."
        )
    world.say(
        f"{hero.id} and {partner.id} solved the case, yet they still lost it. That was the hard, gloomy ending."
    )


def closing_image(world: World, category: CategoryCfg, hero: Entity) -> None:
    outcome = world.facts["outcome"]
    if outcome == "found":
        world.say(
            f"When they finally stepped outside, {hero.id} felt taller. A detective could be frightened and still keep looking."
        )
    else:
        world.say(
            f"When they finally stepped outside, the fair music sounded far away, and {hero.id} kept thinking about how a mystery can be solved too late."
        )


def tell(
    category: CategoryCfg,
    suspect_cfg: SuspectCfg,
    spot_cfg: SpotCfg,
    trust: str,
    delay: int,
    hero_name: str,
    hero_gender: str,
    partner_name: str,
    partner_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, role="partner", traits=["observant"]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    bachelor = world.add(
        Entity(
            id="bachelor",
            kind="character",
            type="bachelor",
            label=SUSPECTS["bachelor"].label,
            role="bachelor",
            attrs={"role_text": SUSPECTS["bachelor"].role_text, "rival": category.rival},
        )
    )
    clerk = world.add(
        Entity(
            id="clerk",
            kind="character",
            type="woman",
            label=SUSPECTS["clerk"].label,
            role="clerk",
            attrs={"role_text": SUSPECTS["clerk"].role_text},
        )
    )
    world.add(Entity(id="fair", type="fair", label="fair hall"))
    world.add(Entity(id="card", type="card", label="category card"))
    world.facts["spot_cfg"] = spot_cfg
    world.facts["category_cfg"] = category
    world.facts["suspect_cfg"] = suspect_cfg
    world.facts["trust"] = trust
    world.facts["base_delay"] = delay
    world.facts["false_lead"] = False

    for _ in range(delay):
        world.get("fair").meters["ticks"] += 1
    propagate(world)

    introduce(world, category, hero, partner, parent)
    world.para()
    setup_case(world, category, hero, partner)
    meet_bachelor(world, hero, bachelor, category, trust, suspect_cfg.id == "bachelor")
    inspect_clue(world, category, hero, partner, suspect_cfg)

    world.para()
    search_spot(world, spot_cfg, hero, partner)

    params = StoryParams(
        category=category.id,
        suspect=suspect_cfg.id,
        spot=spot_cfg.id,
        trust=trust,
        delay=delay,
        hero=hero_name,
        hero_gender=hero_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        parent=parent_type,
        trait=trait,
    )
    outcome = outcome_of(params)
    world.facts["outcome"] = outcome

    world.para()
    if outcome == "found":
        reveal_found(world, hero, partner, suspect_cfg, category)
    else:
        reveal_lost(world, hero, partner, suspect_cfg, category)

    world.para()
    closing_image(world, category, hero)

    world.facts.update(
        hero=hero,
        partner=partner,
        parent=parent,
        bachelor=bachelor,
        clerk=clerk,
        category=category,
        suspect=suspect_cfg,
        spot=spot_cfg,
        card=world.get("card"),
        bell_late=world.get("fair").meters["late"] >= THRESHOLD,
        ruined=world.get("card").meters["ruined"] >= THRESHOLD,
        effective_delay=effective_delay(params),
    )
    return world


KNOWLEDGE = {
    "fair": [
        (
            "What is a fair category?",
            "A fair category is a group that puts similar entries together, like vegetables, crafts, or pets. Judges compare things fairly when each item is in the right place."
        )
    ],
    "category": [
        (
            "Why does a missing category card matter?",
            "A category card tells the judges what an entry is and where it belongs. Without it, the judges may skip the entry or place it wrong."
        )
    ],
    "bachelor": [
        (
            "What is a bachelor?",
            "A bachelor is a man who is not married. In a story, that word tells you something about who he is, but it does not mean he is kind or mean."
        )
    ],
    "clerk": [
        (
            "What does a clerk do at a fair?",
            "A clerk keeps papers in order, writes names down, and helps the judges. If a clerk rushes, papers can end up in the wrong place."
        )
    ],
    "pumpkin": [
        (
            "Why might a pumpkin be entered at a fair?",
            "People bring big or beautiful pumpkins to show how well they grew them. Judges look at size, shape, and condition."
        )
    ],
    "craft": [
        (
            "What is a craft entry?",
            "A craft entry is something made by hand, like knitting or carving. It is judged for care, skill, and neat work."
        )
    ],
    "rabbit": [
        (
            "Why are rabbits kept in pens at fairs?",
            "A pen keeps a rabbit safe and calm while people look at it. It also stops the rabbit from hopping away."
        )
    ],
    "crate": [
        (
            "Why can steam hurt paper?",
            "Warm steam puts water into paper and makes it limp and soft. Wet paper tears more easily and is harder to read."
        )
    ],
    "desk": [
        (
            "Why are drawers useful for papers?",
            "Drawers keep papers flat and together so they do not blow away. But if someone uses the wrong drawer, papers can be hard to find."
        )
    ],
}
KNOWLEDGE_ORDER = ["fair", "category", "bachelor", "clerk", "pumpkin", "craft", "rabbit", "crate", "desk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    category = f["category"]
    suspect = f["suspect"]
    if f["outcome"] == "lost":
        return [
            f'Write a short detective story for a 3-to-5-year-old that includes the words "category", "nod", and "bachelor".',
            f"Tell a suspenseful fair mystery where {hero.label} notices a missing card in the {category.label}, follows clues, and reaches a bad ending.",
            f"Write a child-friendly detective story with a surprise reveal that {suspect.label.lower() if suspect.id == 'bachelor' else 'the real trouble'} caused the loss."
        ]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "category", "nod", and "bachelor".',
        f"Tell a fair-day mystery where {hero.label} finds a missing card in the {category.label} and solves the case just in time.",
        "Write a child-friendly detective story with suspense, clues, and a last-minute rescue."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    category = f["category"]
    suspect = f["suspect"]
    spot = f["spot"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {partner.label}, two children trying to solve a fair mystery. They act like little detectives when a card disappears from the {category.label}."
        ),
        (
            "What was missing?",
            f"The missing thing was the category card for {category.item}. Without that card, the judges could not properly judge the entry."
        ),
        (
            "Why did the mystery feel urgent?",
            f"It felt urgent because the judging bell was about to ring. If the children did not solve the case fast, that category would be judged without the missing card."
        ),
        (
            f"What clue did {partner.label} find?",
            f"{partner.label} found {category.clue} near the empty pin. That clue showed the children where the card had really gone instead of where they were first pointed."
        ),
    ]
    if f["false_lead"]:
        qa.append(
            (
                f"Why did {hero.label} lose extra time?",
                f"{suspect.label} gave a quick nod toward the wrong aisle, and {hero.label} followed that false lead. Because of that delay, the search took longer and the danger grew."
            )
        )
    else:
        qa.append(
            (
                f"What did the nod mean in this story?",
                f"The nod was a clue about whether someone was honest or hiding something. {hero.label} had to decide if it was meant to help or to fool the detectives."
            )
        )
    if outcome == "found":
        qa.append(
            (
                "How did the story end?",
                f"The children found the card {spot.phrase} and carried it back before the final bell. The ending proves that careful clues and quick thinking can still beat the clock."
            )
        )
    else:
        reason = []
        if f["ruined"]:
            reason.append("the card was already damaged")
        if f["bell_late"]:
            reason.append("the judging bell rang too soon")
        because = " and ".join(reason) if reason else "they were too late"
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly because {because}. Even though the children solved the mystery, the fair did not wait for them, which makes the ending both surprising and bad."
            )
        )
        if suspect.id == "bachelor":
            qa.append(
                (
                    f"Why was the bachelor a surprise culprit?",
                    f"At first {suspect.label} seemed calm and helpful, especially with his neat little nod. The surprise came when the children realized he had hidden the card so his own exhibit could win."
                )
            )
        else:
            qa.append(
                (
                    "What was the surprise in the ending?",
                    f"The surprise was that no grand thief had taken the card after all. {suspect.label} had hidden it by mistake, but the mistake still hurt the children's entry."
                )
            )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["category"].tags) | set(f["suspect"].tags) | set(f["spot"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        label = e.label or e.id
        lines.append(f"  {e.id:8} ({e.type:9}) {label:20} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,S,P) :- category(C), suspect(S), spot(P), suits(P,C), access(S,P), spot_access(P,S).

extra_delay(1) :- chosen_suspect(bachelor), trust(trust).
extra_delay(0) :- not extra_delay(1).

effective_delay(D + E) :- delay(D), extra_delay(E).

ruined :- chosen_spot(P), risk(P,R), effective_delay(D), R + D >= 3.
late   :- effective_delay(D), deadline(L), D >= L.

outcome(found) :- not ruined, not late.
outcome(lost)  :- ruined.
outcome(lost)  :- late.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CATEGORIES:
        lines.append(asp.fact("category", cid))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for spot in sorted(suspect.access):
            lines.append(asp.fact("access", sid, spot))
    for pid, spot in SPOTS.items():
        lines.append(asp.fact("spot", pid))
        lines.append(asp.fact("risk", pid, spot.risk))
        for cat in sorted(spot.categories):
            lines.append(asp.fact("suits", pid, cat))
        for who in sorted(spot.access):
            lines.append(asp.fact("spot_access", pid, who))
    lines.append(asp.fact("deadline", DEADLINE))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    program = "\n".join(
        [
            asp.fact("chosen_suspect", params.suspect),
            asp.fact("chosen_spot", params.spot),
            asp.fact("delay", params.delay),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(program, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a detective-style fair mystery with suspense, a nod, and a bachelor."
    )
    ap.add_argument("--category", choices=CATEGORIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--trust", choices=["trust", "doubt"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much time has already been lost before the search begins")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_names(rng: random.Random, gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        hero = rng.choice(GIRL_NAMES)
        partner_gender = "boy"
        partner_pool = PARTNER_BOY_NAMES
    else:
        hero = rng.choice(BOY_NAMES)
        partner_gender = "girl"
        partner_pool = PARTNER_GIRL_NAMES
    partner = rng.choice([n for n in partner_pool if n != hero])
    return hero, partner, partner_gender


def explain_combo(category: str, suspect: str, spot: str) -> str:
    return (
        f"(No story: the {suspect} option does not fit the spot '{spot}' for the {category} case. "
        f"The hiding place must match both the category and who could reasonably reach it.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.category and args.suspect and args.spot and not valid_combo(args.category, args.suspect, args.spot):
        raise StoryError(explain_combo(args.category, args.suspect, args.spot))

    combos = [
        combo
        for combo in valid_combos()
        if (args.category is None or combo[0] == args.category)
        and (args.suspect is None or combo[1] == args.suspect)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    category, suspect, spot = rng.choice(sorted(combos))
    trust = args.trust or rng.choice(["trust", "doubt"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name, partner_name, partner_gender = _pick_names(rng, gender)
    hero = args.hero or hero_name
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        category=category,
        suspect=suspect,
        spot=spot,
        trust=trust,
        delay=delay,
        hero=hero,
        hero_gender=gender,
        partner=partner_name,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.category not in CATEGORIES:
        raise StoryError(f"(No story: unknown category '{params.category}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(No story: unknown suspect '{params.suspect}'.)")
    if params.spot not in SPOTS:
        raise StoryError(f"(No story: unknown spot '{params.spot}'.)")
    if params.trust not in {"trust", "doubt"}:
        raise StoryError(f"(No story: trust must be 'trust' or 'doubt', not '{params.trust}'.)")
    if not valid_combo(params.category, params.suspect, params.spot):
        raise StoryError(explain_combo(params.category, params.suspect, params.spot))

    world = tell(
        category=CATEGORIES[params.category],
        suspect_cfg=SUSPECTS[params.suspect],
        spot_cfg=SPOTS[params.spot],
        trust=params.trust,
        delay=params.delay,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        trait=params.trait,
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


CURATED = [
    StoryParams(
        category="vegetables",
        suspect="bachelor",
        spot="soup_crate",
        trust="trust",
        delay=1,
        hero="Mira",
        hero_gender="girl",
        partner="Ned",
        partner_gender="boy",
        parent="mother",
        trait="sharp-eyed",
    ),
    StoryParams(
        category="crafts",
        suspect="clerk",
        spot="stamp_drawer",
        trust="doubt",
        delay=0,
        hero="Theo",
        hero_gender="boy",
        partner="Maya",
        partner_gender="girl",
        parent="father",
        trait="patient",
    ),
    StoryParams(
        category="pets",
        suspect="bachelor",
        spot="feed_bin",
        trust="doubt",
        delay=0,
        hero="Ruby",
        hero_gender="girl",
        partner="Cole",
        partner_gender="boy",
        parent="mother",
        trait="steady",
    ),
    StoryParams(
        category="crafts",
        suspect="bachelor",
        spot="yarn_box",
        trust="trust",
        delay=0,
        hero="Ben",
        hero_gender="boy",
        partner="Zoe",
        partner_gender="girl",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        category="vegetables",
        suspect="clerk",
        spot="stamp_drawer",
        trust="trust",
        delay=1,
        hero="Ada",
        hero_gender="girl",
        partner="Hugo",
        partner_gender="boy",
        parent="mother",
        trait="brave",
    ),
]


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome calculations differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for category, suspect, spot in asp_valid_combos():
            print(f"{category:11} {suspect:9} {spot}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero}: {p.category} / suspect={p.suspect} / spot={p.spot} / "
                f"trust={p.trust} / outcome={outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
