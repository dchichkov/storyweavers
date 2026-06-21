#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py
======================================================================

A small standalone storyworld for gentle animal stories with dialogue.

Core premise
------------
A little animal is excited for a forest song circle and wants to bring a basket
of treats to share before singing into a mic. But the chosen basket cannot
properly contain the treats: they either slip through holes or tumble over the
low sides. A friend notices, predicts the spill, and helps fix the basket in a
reasonable way. Then the hero can carry the treats safely and sing.

The world model tracks:
- physical meters: carrying, spilled, lined, covered, contained
- emotional memes: joy, worry, embarrassment, relief, gratitude, confidence

The reasonableness gate prefers only combinations where:
- the basket really is a bad container for the chosen treat
- the chosen fix actually solves that specific containment problem

Run it
------
python storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py
python storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py --basket twig
python storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py --treat pebbles
python storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py --fix napkin_lining
python storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py --all
python storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py --qa --json
python storyworlds/worlds/gpt-5.4/basket_mic_contain_dialogue_animal_story.py --verify
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
        female = {"girl", "mother", "hen", "duck", "goose"}
        male = {"boy", "father", "fox", "bear", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.id


@dataclass
class AnimalCfg:
    id: str
    species: str
    snack: str
    voice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BasketCfg:
    id: str
    label: str
    phrase: str
    flaw: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TreatCfg:
    id: str
    label: str
    phrase: str
    risk: str
    scatter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceCfg:
    id: str
    label: str
    path: str
    stage: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


THE_PLACES = {
    "meadow": PlaceCfg(
        id="meadow",
        label="the clover meadow",
        path="the ferny path to the clover meadow",
        stage="a little stump stage under the willow tree",
        tags={"meadow", "stage"},
    ),
    "pond": PlaceCfg(
        id="pond",
        label="the pond clearing",
        path="the soft path around the pond",
        stage="a flat stone stage near the reeds",
        tags={"pond", "stage"},
    ),
    "oak": PlaceCfg(
        id="oak",
        label="the old oak clearing",
        path="the winding path to the old oak",
        stage="a mossy stump stage beside the oak roots",
        tags={"oak", "stage"},
    ),
}

ANIMALS = {
    "mouse": AnimalCfg(
        id="mouse",
        species="mouse",
        snack="crumbs",
        voice="small but bright",
        tags={"mouse", "forest_animals"},
    ),
    "rabbit": AnimalCfg(
        id="rabbit",
        species="rabbit",
        snack="sweet clover cookies",
        voice="soft and springy",
        tags={"rabbit", "forest_animals"},
    ),
    "squirrel": AnimalCfg(
        id="squirrel",
        species="squirrel",
        snack="toasted seeds",
        voice="quick and happy",
        tags={"squirrel", "forest_animals"},
    ),
    "duck": AnimalCfg(
        id="duck",
        species="duck",
        snack="pond crackers",
        voice="warm and waddly",
        tags={"duck", "forest_animals"},
    ),
}

BASKETS = {
    "twig": BasketCfg(
        id="twig",
        label="twig basket",
        phrase="a small twig basket with wide little gaps",
        flaw="holes",
        detail="The weave had wide little gaps between the twigs.",
        tags={"basket", "holes"},
    ),
    "petal": BasketCfg(
        id="petal",
        label="petal basket",
        phrase="a pretty petal basket with very low sides",
        flaw="low_sides",
        detail="It was pretty, but the sides were so low that round things could roll right out.",
        tags={"basket", "low_sides"},
    ),
    "reed": BasketCfg(
        id="reed",
        label="reed basket",
        phrase="a light reed basket with a crooked rim",
        flaw="low_sides",
        detail="Its rim tilted on one side, so anything round would tip toward the edge.",
        tags={"basket", "low_sides"},
    ),
}

TREATS = {
    "berries": TreatCfg(
        id="berries",
        label="berries",
        phrase="a pile of shiny red berries",
        risk="holes",
        scatter="slipped through the gaps and dotted the path like little red beads",
        tags={"berries", "food", "tiny"},
    ),
    "seeds": TreatCfg(
        id="seeds",
        label="seeds",
        phrase="a scoop of striped sunflower seeds",
        risk="holes",
        scatter="trickled through the weave in a tiny rattly stream",
        tags={"seeds", "food", "tiny"},
    ),
    "plums": TreatCfg(
        id="plums",
        label="plums",
        phrase="three round purple plums",
        risk="low_sides",
        scatter="bumped the rim and rolled into the grass",
        tags={"plums", "food", "round"},
    ),
    "pebbles": TreatCfg(
        id="pebbles",
        label="song pebbles",
        phrase="four smooth song pebbles for tapping a rhythm",
        risk="low_sides",
        scatter="clacked together, tipped over the edge, and rolled apart",
        tags={"pebbles", "music", "round"},
    ),
}

FIXES = {
    "leaf_lining": FixCfg(
        id="leaf_lining",
        label="leaf lining",
        phrase="broad dock leaves tucked neatly inside",
        solves={"holes"},
        action="lined the inside with broad green leaves and pressed them flat against the gaps",
        qa_text="lined the basket with broad leaves so tiny things could not slip through",
        tags={"leaves", "contain", "basket_fix"},
    ),
    "napkin_lining": FixCfg(
        id="napkin_lining",
        label="napkin lining",
        phrase="a clean blue napkin folded into the basket",
        solves={"holes"},
        action="folded a clean blue napkin into the basket and tucked every corner in place",
        qa_text="folded a napkin into the basket to block the gaps",
        tags={"napkin", "contain", "basket_fix"},
    ),
    "cover_cloth": FixCfg(
        id="cover_cloth",
        label="cover cloth",
        phrase="a soft cloth tied over the top",
        solves={"low_sides"},
        action="set a soft cloth over the top and tied it gently so the round things could not bounce out",
        qa_text="tied a cloth over the basket so the round things stayed inside",
        tags={"cloth", "contain", "basket_fix"},
    ),
    "lid_vine": FixCfg(
        id="lid_vine",
        label="vine lid",
        phrase="a flat bark lid held on with a springy vine",
        solves={"low_sides"},
        action="laid a flat bark lid on top and held it snug with a springy vine",
        qa_text="added a bark lid and vine so the round things could not roll out",
        tags={"lid", "contain", "basket_fix"},
    ),
}

GIRL_NAMES = ["Mina", "Pip", "Tansy", "Lulu", "Daisy", "Mabel"]
BOY_NAMES = ["Ollie", "Ned", "Pico", "Bram", "Toby", "Rory"]
HELPER_NAMES = ["Fern", "Moss", "Junie", "Poppy", "Hazel", "Nibbles"]
TRAITS = ["cheerful", "eager", "gentle", "bouncy", "hopeful", "careful"]


def spill_risk(basket: BasketCfg, treat: TreatCfg) -> bool:
    return basket.flaw == treat.risk


def fix_works(basket: BasketCfg, treat: TreatCfg, fix: FixCfg) -> bool:
    return spill_risk(basket, treat) and basket.flaw in fix.solves


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in THE_PLACES:
        for animal_id in ANIMALS:
            for basket_id, basket in BASKETS.items():
                for treat_id, treat in TREATS.items():
                    if not spill_risk(basket, treat):
                        continue
                    for fix_id, fix in FIXES.items():
                        if fix_works(basket, treat, fix):
                            combos.append((place_id, animal_id, basket_id, treat_id, fix_id))
    return combos


@dataclass
class StoryParams:
    place: str
    animal: str
    basket: str
    treat: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="meadow",
        animal="mouse",
        basket="twig",
        treat="berries",
        fix="leaf_lining",
        hero_name="Mina",
        hero_gender="girl",
        helper_name="Fern",
        helper_gender="girl",
        trait="eager",
        seed=1,
    ),
    StoryParams(
        place="pond",
        animal="duck",
        basket="petal",
        treat="plums",
        fix="cover_cloth",
        hero_name="Ollie",
        hero_gender="boy",
        helper_name="Hazel",
        helper_gender="girl",
        trait="cheerful",
        seed=2,
    ),
    StoryParams(
        place="oak",
        animal="squirrel",
        basket="twig",
        treat="seeds",
        fix="napkin_lining",
        hero_name="Pico",
        hero_gender="boy",
        helper_name="Junie",
        helper_gender="girl",
        trait="hopeful",
        seed=3,
    ),
    StoryParams(
        place="meadow",
        animal="rabbit",
        basket="reed",
        treat="pebbles",
        fix="lid_vine",
        hero_name="Tansy",
        hero_gender="girl",
        helper_name="Moss",
        helper_gender="boy",
        trait="gentle",
        seed=4,
    ),
]


def explain_rejection(basket: BasketCfg, treat: TreatCfg, fix: Optional[FixCfg] = None) -> str:
    if not spill_risk(basket, treat):
        return (
            f"(No story: {basket.label} has a {basket.flaw.replace('_', ' ')} problem, "
            f"but {treat.label} do not test that problem. The basket would not honestly fail to contain them.)"
        )
    if fix is not None and not fix_works(basket, treat, fix):
        need = basket.flaw.replace("_", " ")
        return (
            f"(No story: {fix.label} does not solve the basket's {need} problem. "
            f"The repair must really help the basket contain the {treat.label}.)"
        )
    return "(No story: this combination does not make a sensible containment problem.)"


def outcome_of(params: StoryParams) -> str:
    return "mended"


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    if not choices:
        choices = HELPER_NAMES
    return rng.choice(choices)


def pick_helper_name(rng: random.Random, avoid: str = "") -> str:
    choices = [n for n in HELPER_NAMES if n != avoid]
    return rng.choice(choices)


def build_world(params: StoryParams) -> World:
    if params.place not in THE_PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.basket not in BASKETS:
        raise StoryError(f"(Unknown basket: {params.basket})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    place = THE_PLACES[params.place]
    animal = ANIMALS[params.animal]
    basket_cfg = BASKETS[params.basket]
    treat_cfg = TREATS[params.treat]
    fix_cfg = FIXES[params.fix]

    if not spill_risk(basket_cfg, treat_cfg):
        raise StoryError(explain_rejection(basket_cfg, treat_cfg))
    if not fix_works(basket_cfg, treat_cfg, fix_cfg):
        raise StoryError(explain_rejection(basket_cfg, treat_cfg, fix_cfg))

    world = World()
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=animal.species,
            label=params.hero_name,
            role="hero",
            traits=[params.trait],
            tags=set(animal.tags),
        )
    )
    helper_species = "rabbit" if animal.species != "rabbit" else "mouse"
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type=helper_species,
            label=params.helper_name,
            role="helper",
            traits=["thoughtful"],
            tags={"helper"},
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            kind="thing",
            type="basket",
            label=basket_cfg.label,
            phrase=basket_cfg.phrase,
            tags=set(basket_cfg.tags),
            attrs={"flaw": basket_cfg.flaw},
        )
    )
    treat = world.add(
        Entity(
            id="treat",
            kind="thing",
            type="treat",
            label=treat_cfg.label,
            phrase=treat_cfg.phrase,
            tags=set(treat_cfg.tags),
            attrs={"risk": treat_cfg.risk},
        )
    )
    mic = world.add(
        Entity(
            id="mic",
            kind="thing",
            type="mic",
            label="mic",
            phrase="a dewdrop mic made from a silver thistle stem",
            tags={"mic", "music"},
        )
    )

    hero.memes["joy"] += 1
    hero.memes["confidence"] += 1
    basket.meters["carrying"] += 1
    basket.meters["open"] += 1

    world.say(
        f"On a bright morning in {place.label}, {hero.name} the little {animal.species} "
        f"trotted along {place.path} with {basket_cfg.phrase} on one arm."
    )
    world.say(
        f"Inside were {treat_cfg.phrase}, and ahead waited {place.stage} with {mic.phrase}."
    )
    world.say(
        f'{hero.name} hummed in a {animal.voice} voice. "I will share these first," '
        f'{hero.pronoun()} said, "and then I will sing into the mic."'
    )

    world.para()
    world.say(basket_cfg.detail)
    world.say(
        f"When {hero.name} skipped over a root, the {treat_cfg.label} {treat_cfg.scatter}."
    )
    basket.meters["failed_contain"] += 1
    basket.meters["spilled"] += 1
    treat.meters["spilled"] += 1
    hero.memes["worry"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["confidence"] = 0.0

    world.say(
        f'"Oh no," {hero.name} cried. "This basket cannot contain my {treat_cfg.label} at all!"'
    )
    world.say(
        f"{helper.name}, who was carrying a fern flag for the song circle, hurried over."
    )
    world.say(
        f'"Do not worry," {helper.name} said. "Let us look at the basket instead of the problem."'
    )

    world.para()
    if basket_cfg.flaw == "holes":
        world.say(
            f"{helper.name} peered through the weave and tapped one of the gaps. "
            f'"The basket is kind, but the holes are too wide for {treat_cfg.label}," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f"{helper.name} steadied the crooked rim with one paw. "
            f'"The basket is pretty, but the sides are too low to contain round things," {helper.pronoun()} said.'
        )

    world.say(
        f'Then {helper.name} {fix_cfg.action}.'
    )
    basket.meters["mended"] += 1
    basket.meters["contained"] += 1
    if basket_cfg.flaw == "holes":
        basket.meters["lined"] += 1
    else:
        basket.meters["covered"] += 1
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    helper.memes["care"] += 1

    world.say(
        f'The {treat_cfg.label} settled quietly inside. "{fix_cfg.label.capitalize()}!" '
        f'{hero.name} said. "Now the basket can contain them."'
    )

    world.para()
    hero.memes["confidence"] += 1
    hero.memes["joy"] += 1
    basket.meters["spilled"] = 0.0
    treat.meters["spilled"] = 0.0
    world.say(
        f"Together they reached {place.stage}. {hero.name} set the basket down without losing a single thing."
    )
    world.say(
        f'"Thank you, {helper.name}," {hero.name} said. "You helped me save the sharing part and the singing part."'
    )
    world.say(
        f'"Then sing," {helper.name} whispered with a smile.'
    )
    world.say(
        f"{hero.name} stood by the mic, saw the safe basket waiting below, and sang a little song so sweet "
        f"that even the willow leaves seemed to listen."
    )
    world.say(
        f"Afterward, the animals munched {treat_cfg.label} together, and the mended basket rested beside the stage as if it felt proud too."
    )

    world.facts.update(
        place=place,
        animal=animal,
        basket_cfg=basket_cfg,
        treat_cfg=treat_cfg,
        fix_cfg=fix_cfg,
        hero=hero,
        helper=helper,
        basket=basket,
        treat=treat,
        mic=mic,
        outcome="mended",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    animal = world.facts["animal"]
    basket_cfg = world.facts["basket_cfg"]
    treat_cfg = world.facts["treat_cfg"]
    place = world.facts["place"]
    return [
        'Write a gentle Animal Story for a 3-to-5-year-old that includes the words "basket", "mic", and "contain", and uses dialogue.',
        f"Tell a forest story where {hero.name} the {animal.species} is on the way to {place.label} with {basket_cfg.label}, but it cannot contain {treat_cfg.label} until a friend helps.",
        f'Write a simple animal tale with dialogue in which a little creature fixes a basket problem before singing into a mic.',
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    animal = world.facts["animal"]
    basket_cfg = world.facts["basket_cfg"]
    treat_cfg = world.facts["treat_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    place = world.facts["place"]
    basket = world.facts["basket"]

    flaw_text = "holes that were too wide" if basket_cfg.flaw == "holes" else "sides that were too low"
    problem_effect = (
        f"The basket had {flaw_text}, so it could not contain the {treat_cfg.label}. "
        f"That is why they spilled when {hero.name} hurried along the path."
    )
    fix_effect = (
        f"{helper.name} {fix_cfg.qa_text}. "
        f"After that, the {treat_cfg.label} stayed inside, so {hero.name} could reach the stage calmly."
    )

    return [
        (
            "Who is the story about?",
            f"It is about {hero.name}, a little {animal.species}, and {helper.name}, the friend who came to help. "
            f"They were on their way to a forest song circle in {place.label}."
        ),
        (
            f"Why was {hero.name} carrying a basket?",
            f"{hero.name} wanted to bring {treat_cfg.label} to share before singing. "
            f"The basket was meant to carry the treats safely to the stage."
        ),
        (
            f"What went wrong with the basket?",
            problem_effect,
        ),
        (
            f"What did {hero.name} say when the treats spilled?",
            f'{hero.name} said, "This basket cannot contain my {treat_cfg.label} at all!" '
            f"The words came after the spill, when {hero.pronoun()} felt worried and embarrassed."
        ),
        (
            f"How did {helper.name} solve the problem?",
            fix_effect,
        ),
        (
            "Why was the mic important in the story?",
            f"The mic was waiting on the little stage for {hero.name}'s song. "
            f"Once the basket problem was fixed, {hero.pronoun()} could stop worrying and sing."
        ),
        (
            "How did the story end?",
            f"It ended with the basket safely holding the {treat_cfg.label} while {hero.name} sang into the mic. "
            f"After the song, everyone shared the treats together."
        ),
    ]


KNOWLEDGE = {
    "basket": [
        (
            "What does a basket do?",
            "A basket holds things and helps you carry them from one place to another. If it has holes or low sides, little things can fall out."
        )
    ],
    "contain": [
        (
            "What does contain mean?",
            "Contain means to keep something inside instead of letting it spill or escape. A good container holds things safely where they belong."
        )
    ],
    "mic": [
        (
            "What is a mic?",
            "A mic is short for microphone. It helps a voice sound louder so other people can hear a song or speech."
        )
    ],
    "berries": [
        (
            "Why can berries fall through a basket?",
            "Small berries can slip through wide gaps in a basket. Tiny things need a tighter basket or a lining inside."
        )
    ],
    "seeds": [
        (
            "Why do seeds need a tight container?",
            "Seeds are very small, so they can trickle through cracks and holes. That is why they need a container with no gaps."
        )
    ],
    "plums": [
        (
            "Why do round plums roll?",
            "Round things roll when they are tipped or bumped. If a basket has low sides, they can roll right out."
        )
    ],
    "pebbles": [
        (
            "Why can smooth pebbles tumble out of a basket?",
            "Smooth pebbles can slide and roll when a basket tips. A cover or lid helps keep them inside."
        )
    ],
    "leaves": [
        (
            "How can leaves help a basket?",
            "Big flat leaves can line the inside of a basket and block little gaps. That helps tiny things stay inside."
        )
    ],
    "napkin": [
        (
            "How can a napkin help contain small things?",
            "A folded napkin can make a soft lining inside a basket. The lining covers the holes so small things cannot slip through."
        )
    ],
    "cloth": [
        (
            "Why would someone tie a cloth over a basket?",
            "A cloth over the top helps stop things from bouncing or rolling out. It is useful when the basket needs a simple cover."
        )
    ],
    "lid": [
        (
            "What does a lid do?",
            "A lid covers the top of a container and helps keep what is inside from falling out. It can also protect the things inside while you carry them."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "basket",
    "contain",
    "mic",
    "berries",
    "seeds",
    "plums",
    "pebbles",
    "leaves",
    "napkin",
    "cloth",
    "lid",
]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    basket_cfg = world.facts["basket_cfg"]
    treat_cfg = world.facts["treat_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    tags = {"basket", "contain", "mic"} | set(treat_cfg.tags) | set(fix_cfg.tags) | set(basket_cfg.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(B, T) :- basket(B), treat(T), flaw(B, F), needs(T, F).
works(B, T, X) :- risk(B, T), fix(X), flaw(B, F), solves(X, F).
valid(P, A, B, T, X) :- place(P), animal(A), basket(B), treat(T), fix(X), works(B, T, X).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in THE_PLACES:
        lines.append(asp.fact("place", place_id))
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal", animal_id))
    for basket_id, basket in BASKETS.items():
        lines.append(asp.fact("basket", basket_id))
        lines.append(asp.fact("flaw", basket_id, basket.flaw))
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        lines.append(asp.fact("needs", treat_id, treat.risk))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for need in sorted(fix.solves):
            lines.append(asp.fact("solves", fix_id, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
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
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a basket that cannot contain treats until a friend fixes it."
    )
    ap.add_argument("--place", choices=THE_PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--basket", choices=BASKETS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.basket and args.treat:
        basket = BASKETS[args.basket]
        treat = TREATS[args.treat]
        if not spill_risk(basket, treat):
            raise StoryError(explain_rejection(basket, treat))
        if args.fix:
            fix = FIXES[args.fix]
            if not fix_works(basket, treat, fix):
                raise StoryError(explain_rejection(basket, treat, fix))
    elif args.fix and args.basket and not any(
        fix_works(BASKETS[args.basket], treat, FIXES[args.fix]) for treat in TREATS.values()
    ):
        sample_treat = next(iter(TREATS.values()))
        raise StoryError(explain_rejection(BASKETS[args.basket], sample_treat, FIXES[args.fix]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.animal is None or combo[1] == args.animal)
        and (args.basket is None or combo[2] == args.basket)
        and (args.treat is None or combo[3] == args.treat)
        and (args.fix is None or combo[4] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, animal, basket, treat, fix = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    helper_name = args.helper_name or pick_helper_name(rng, avoid=hero_name)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        animal=animal,
        basket=basket,
        treat=treat,
        fix=fix,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(f"{len(combos)} compatible (place, animal, basket, treat, fix) combos:\n")
        for place, animal, basket, treat, fix in combos:
            print(f"  {place:7} {animal:9} {basket:6} {treat:8} {fix}")
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
            header = f"### {p.hero_name}: {p.basket} basket, {p.treat}, {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
