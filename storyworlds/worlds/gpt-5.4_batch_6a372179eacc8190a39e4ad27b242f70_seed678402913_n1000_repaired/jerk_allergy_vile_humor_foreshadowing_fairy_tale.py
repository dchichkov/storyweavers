#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jerk_allergy_vile_humor_foreshadowing_fairy_tale.py
==============================================================================

A standalone storyworld about a springtime fairy-tale feast, a thoughtless prank,
an allergy danger, and a kinder ending. The world models:

* typed entities with physical meters and emotional memes
* a small reasonableness gate (only real allergy risks become stories)
* foreshadowing via an early warning sign from the same allergen
* a gentle humorous turn
* an inline ASP twin for the compatibility gate and the outcome model

Seed constraints rebuilt as world logic:
    words: jerk, allergy, vile
    features: Humor, Foreshadowing
    style: Fairy Tale

Run it
------
    python storyworlds/worlds/gpt-5.4/jerk_allergy_vile_humor_foreshadowing_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/jerk_allergy_vile_humor_foreshadowing_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/jerk_allergy_vile_humor_foreshadowing_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4/jerk_allergy_vile_humor_foreshadowing_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/jerk_allergy_vile_humor_foreshadowing_fairy_tale.py --verify
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
KIND_MIN = 2


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
    edible: bool = False
    wearable: bool = False
    safe_for_allergy: bool = False
    prankworthy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "witch", "fairy_godmother", "maid"}
        male = {"boy", "prince", "king", "page", "goblin", "baker", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "queen": "queen",
            "king": "king",
            "fairy_godmother": "fairy godmother",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    season_sign: str
    feast: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Allergen:
    id: str
    label: str
    phrase: str
    drift: str
    symptom: str
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    kind: str
    prankworthy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    kind: int = 2
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    allergen: str
    vessel: str
    remedy: str
    hero_name: str
    hero_gender: str
    prankster_name: str
    prankster_gender: str
    royal_type: str
    helper_type: str
    seed: Optional[int] = None


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


def _r_allergy_reaction(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    allergen = world.get("allergen")
    vessel = world.get("vessel")
    if child.attrs.get("allergic_to") != allergen.id:
        return out
    if vessel.attrs.get("dusted_with") != allergen.id:
        return out
    sig = ("reaction", child.id, allergen.id, vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["sneezes"] += 1
    child.meters["reaction"] += 1
    child.memes["alarm"] += 1
    world.get("hall").meters["trouble"] += 1
    out.append("__reaction__")
    return out


def _r_prank_guilt(world: World) -> list[str]:
    out: list[str] = []
    prankster = world.get("prankster")
    if prankster.memes["caught"] < THRESHOLD:
        return out
    sig = ("guilt", prankster.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prankster.memes["shame"] += 1
    prankster.memes["kindness"] += 1
    out.append("__guilt__")
    return out


CAUSAL_RULES = [
    Rule(name="allergy_reaction", tag="physical", apply=_r_allergy_reaction),
    Rule(name="prank_guilt", tag="social", apply=_r_prank_guilt),
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


SETTINGS = {
    "rose_garden": Setting(
        id="rose_garden",
        place="the rose garden behind the castle",
        season_sign="The fountain was tossing bright drops, and the hedges were hung with little gold ribbons.",
        feast="the Feast of First Bloom",
        ending_image="lanternflies bobbed over the fountain while everyone laughed around the long table",
        tags={"garden", "fairy_tale"},
    ),
    "moon_court": Setting(
        id="moon_court",
        place="the moonlit court beside the palace orchard",
        season_sign="Silver bells chimed in the pear trees, and the flagstones shone like clean plates.",
        feast="the Moon-Petal Supper",
        ending_image="the pear trees whispered above the benches while the silver cups shone softly",
        tags={"orchard", "fairy_tale"},
    ),
    "river_green": Setting(
        id="river_green",
        place="the willow green beside the castle river",
        season_sign="The stream skipped over stones, and white ducks drew wiggly lines through the water.",
        feast="the Willow-Day Picnic",
        ending_image="the river gleamed like blue glass while napkins fluttered on the grass",
        tags={"river", "fairy_tale"},
    ),
}

ALLERGENS = {
    "rose_pollen": Allergen(
        id="rose_pollen",
        label="rose pollen",
        phrase="golden rose pollen",
        drift="gold dust from the roses",
        symptom="made her nose prickle at once",
        warning="One sneeze at the wrong blossom was enough to tell the tale.",
        tags={"allergy", "pollen", "rose"},
    ),
    "lily_dust": Allergen(
        id="lily_dust",
        label="lily dust",
        phrase="powdery lily dust",
        drift="pale dust from the lilies",
        symptom="made his eyes water and his nose twitch",
        warning="Whenever the lily carts rolled by, a sneeze was never far behind.",
        tags={"allergy", "pollen", "lily"},
    ),
    "bee_flour": Allergen(
        id="bee_flour",
        label="bee-flour",
        phrase="sparkly bee-flour",
        drift="sweet flour the palace bees had dusted with pollen",
        symptom="made her nose wiggle before the first bite",
        warning="The palace baker always kept it far from the children who could not bear it.",
        tags={"allergy", "flour", "bee"},
    ),
}

VESSELS = {
    "tart": Vessel(
        id="tart",
        label="berry tart",
        phrase="a little berry tart",
        kind="food",
        prankworthy=True,
        tags={"food", "feast"},
    ),
    "crown": Vessel(
        id="crown",
        label="flower crown",
        phrase="a flower crown",
        kind="wearable",
        prankworthy=True,
        tags={"flowers", "feast"},
    ),
    "cup": Vessel(
        id="cup",
        label="mint cup",
        phrase="a silver mint cup",
        kind="drink",
        prankworthy=True,
        tags={"drink", "feast"},
    ),
    "stone_spoon": Vessel(
        id="stone_spoon",
        label="stone spoon",
        phrase="a stone spoon",
        kind="tool",
        prankworthy=False,
        tags={"tool"},
    ),
}

REMEDIES = {
    "swap": Remedy(
        id="swap",
        label="swap",
        phrase="a quick swap",
        covers={"food", "wearable", "drink"},
        kind=3,
        text="lifted the dangerous thing away before it reached the child and set down a safe one instead",
        qa_text="swapped the dangerous item for a safe one before the child touched it",
        tags={"safety", "swap"},
    ),
    "wash": Remedy(
        id="wash",
        label="wash",
        phrase="a hurried rinse",
        covers={"wearable", "drink"},
        kind=2,
        text="caught the trouble in time, rinsed the dust away, and brought back the item clean and safe",
        qa_text="rinsed the allergen away and brought the item back safe",
        tags={"safety", "wash"},
    ),
    "snatch": Remedy(
        id="snatch",
        label="snatch",
        phrase="a clumsy snatch",
        covers={"food"},
        kind=1,
        text="snatched the thing away so fast that jam flew onto three sleeves and a goose-shaped pie",
        qa_text="snatched the dangerous thing away before it could be eaten",
        tags={"humor", "mess"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nella", "Elsa", "Poppy", "Wren", "Ivy"]
BOY_NAMES = ["Oren", "Milo", "Robin", "Theo", "Bram", "Finn", "Hugo", "Ned"]


def hazard_at_risk(allergen: Allergen, vessel: Vessel) -> bool:
    return vessel.prankworthy and allergen.id in {"rose_pollen", "lily_dust", "bee_flour"}


def remedy_works(vessel: Vessel, remedy: Remedy) -> bool:
    return vessel.kind in remedy.covers and remedy.kind >= KIND_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for aid, allergen in ALLERGENS.items():
            for vid, vessel in VESSELS.items():
                if hazard_at_risk(allergen, vessel) and any(remedy_works(vessel, r) for r in REMEDIES.values()):
                    combos.append((sid, aid, vid))
    return combos


def explain_rejection(allergen: Allergen, vessel: Vessel) -> str:
    if not vessel.prankworthy:
        return (
            f"(No story: {vessel.phrase} is not something a feast prank would sensibly target. "
            f"A prank here needs a wearable or edible object that could actually reach the child.)"
        )
    return (
        f"(No story: {allergen.label} and {vessel.label} do not make a sensible allergy danger in this world.)"
    )


def explain_remedy(remedy_id: str, vessel: Vessel) -> str:
    remedy = REMEDIES[remedy_id]
    if remedy.kind < KIND_MIN:
        return (
            f"(Refusing remedy '{remedy_id}': it scores too low on kindness and sense "
            f"(kind={remedy.kind} < {KIND_MIN}). The world prefers calmer, safer fixes.)"
        )
    if vessel.kind not in remedy.covers:
        return (
            f"(Refusing remedy '{remedy_id}': {remedy.phrase} does not sensibly fix a {vessel.label} hazard.)"
        )
    return "(Refusing remedy: not a valid fix.)"


def predict_reaction(world: World) -> dict:
    sim = world.copy()
    vessel = sim.get("vessel")
    allergen = sim.get("allergen")
    vessel.attrs["dusted_with"] = allergen.id
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "reacts": child.meters["reaction"] >= THRESHOLD,
        "sneezes": child.meters["sneezes"],
        "trouble": sim.get("hall").meters["trouble"],
    }


def foreshadow(world: World, setting: Setting, allergen: Allergen, child: Entity, royal: Entity) -> None:
    child.memes["delight"] += 1
    world.say(
        f"In {setting.place}, where everyone had gathered for {setting.feast}, "
        f"{setting.season_sign}"
    )
    world.say(
        f"{child.id} helped {royal.label_word} count napkins, cups, and sugared plums, "
        f"for the child loved neat little jobs and festival secrets."
    )
    world.say(
        f"But when a breeze carried {allergen.drift} across the path, {child.id} gave one bright little sneeze. "
        f"{allergen.warning}"
    )


def introduce_prank(world: World, prankster: Entity, vessel: Vessel, allergen: Allergen) -> None:
    prankster.memes["mischief"] += 1
    world.say(
        f"Behind the pastry table, {prankster.id} saw {vessel.phrase} waiting to be carried out "
        f"and had a thoroughly foolish thought."
    )
    world.say(
        f'"I shall play a joke so clever that everyone laughs," {prankster.id} whispered. '
        f'It was not a clever thought at all. It was a vile little plan.'
    )
    world.say(
        f"He pinched a bit of {allergen.phrase} between finger and thumb and reached toward the {vessel.label}."
    )


def warn(world: World, hero: Entity, prankster: Entity, child: Entity, allergen: Allergen, vessel: Vessel) -> None:
    pred = predict_reaction(world)
    hero.memes["concern"] += 1
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f"{hero.id} remembered the sneeze by the path and saw at once what would happen next."
    )
    world.say(
        f'"Stop!" {hero.id} cried. "That is not a joke. {child.id} has an allergy to {allergen.label}, '
        f'and the {vessel.label} will make {child.pronoun("object")} poorly."'
    )
    world.say(
        f"{prankster.id} blinked, for sometimes a would-be joker only notices the laugh and forgets the hurt."
    )


def prank_continues(world: World, prankster: Entity, vessel: Entity, allergen: Entity) -> None:
    prankster.memes["defiance"] += 1
    vessel.attrs["dusted_with"] = allergen.id
    world.say(
        f'"It is only a pinch," muttered {prankster.id}, being a jerk for one more foolish heartbeat, '
        f"and he dusted the {vessel.label} anyway."
    )


def catch_before_contact(world: World, royal: Entity, helper: Entity, remedy: Remedy) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{royal.label_word.capitalize()} moved faster than a page turning in a windy tower. "
        f"{royal.pronoun().capitalize()} {remedy.text}."
    )


def playful_humor(world: World, prankster: Entity) -> None:
    prankster.meters["jam_on_nose"] += 1
    world.say(
        f"In the bustle, a dab of berry jam landed on {prankster.id}'s nose, and even the geese seemed to snicker."
    )


def reaction_scene(world: World, child: Entity, allergen: Allergen, vessel: Vessel) -> None:
    propagate(world, narrate=False)
    world.say(
        f"But the {vessel.label} came too near, and at once {child.id}'s {allergen.symptom}. "
        f"{child.pronoun().capitalize()} sneezed three times in a row: " + '"hish, hush, HOO!"'
    )
    world.say(
        f"The ribbons shook. The cups rang. One old hound barked as if he too had been surprised by the sneeze."
    )


def calm_aftercare(world: World, helper: Entity, child: Entity, allergen: Allergen) -> None:
    helper.memes["care"] += 1
    child.memes["relief"] += 1
    child.meters["reaction"] = 0.0
    world.get("hall").meters["trouble"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} brought cool water, clean linen, and a safe honey biscuit. "
        f"In a little while, {child.id}'s nose stopped twitching."
    )
    world.say(
        f'"There now," said {helper.label_word}. "Allergy trouble is no laughing matter."'
    )


def apology_and_lesson(world: World, prankster: Entity, child: Entity, vessel: Vessel) -> None:
    prankster.memes["caught"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{prankster.id} looked at the frightened child, at the mess, and at the jam on his own nose."
    )
    world.say(
        f'"I thought I was being funny," he said. "Instead I was a jerk. I am sorry."'
    )
    world.say(
        f"He carried away every unsafe {vessel.label} himself and scrubbed the serving board until it shone."
    )


def feast_ending(world: World, setting: Setting, child: Entity, prankster: Entity, vessel: Vessel) -> None:
    child.memes["joy"] += 1
    prankster.memes["relief"] += 1
    prankster.memes["kindness"] += 1
    safe_item = {
        "berry tart": "pear tart",
        "flower crown": "ribbon crown",
        "mint cup": "apple-mint water",
        "stone spoon": "wooden spoon",
    }.get(vessel.label, "safe treat")
    world.say(
        f"Soon a safe {safe_item} was set before {child.id}, and this time the feast began with no more trouble."
    )
    world.say(
        f"{child.id} even let {prankster.id} sit nearby, once he had promised that jokes must never be cruel."
    )
    world.say(
        f"And as {setting.ending_image}, the kingdom learned that the smallest pinch of meanness can spoil a table, "
        f"while one quick act of care can set it right."
    )


def tell(
    setting: Setting,
    allergen_cfg: Allergen,
    vessel_cfg: Vessel,
    remedy_cfg: Remedy,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    prankster_name: str = "Ned",
    prankster_gender: str = "boy",
    royal_type: str = "queen",
    helper_type: str = "fairy_godmother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    child = world.add(
        Entity(
            id="Pip",
            kind="character",
            type="girl" if hero_gender == "girl" else "boy",
            role="allergic_child",
            label="the little guest",
            attrs={"allergic_to": allergen_cfg.id},
        )
    )
    prankster = world.add(
        Entity(
            id=prankster_name,
            kind="character",
            type=prankster_gender,
            role="prankster",
            label=prankster_name,
        )
    )
    royal = world.add(Entity(id="Royal", kind="character", type=royal_type, role="royal", label="the royal host"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    hall = world.add(Entity(id="hall", kind="thing", type="hall", label="the feast"))
    allergen = world.add(
        Entity(
            id="allergen",
            kind="thing",
            type="allergen",
            label=allergen_cfg.label,
            phrase=allergen_cfg.phrase,
            tags=set(allergen_cfg.tags),
        )
    )
    vessel = world.add(
        Entity(
            id="vessel",
            kind="thing",
            type=vessel_cfg.kind,
            label=vessel_cfg.label,
            phrase=vessel_cfg.phrase,
            prankworthy=vessel_cfg.prankworthy,
            edible=vessel_cfg.kind in {"food", "drink"},
            wearable=vessel_cfg.kind == "wearable",
        )
    )

    foreshadow(world, setting, allergen_cfg, child, royal)
    world.para()
    introduce_prank(world, prankster, vessel_cfg, allergen_cfg)
    warn(world, hero, prankster, child, allergen_cfg, vessel_cfg)

    prank_continues(world, prankster, vessel, allergen)

    world.para()
    caught_in_time = remedy_works(vessel_cfg, remedy_cfg)
    if caught_in_time:
        catch_before_contact(world, royal, helper, remedy_cfg)
        playful_humor(world, prankster)
        world.facts["reaction_happened"] = False
    else:
        reaction_scene(world, child, allergen_cfg, vessel_cfg)
        calm_aftercare(world, helper, child, allergen_cfg)
        world.facts["reaction_happened"] = True

    world.para()
    apology_and_lesson(world, prankster, child, vessel_cfg)
    feast_ending(world, setting, child, prankster, vessel_cfg)

    outcome = "prevented" if caught_in_time else "reaction"
    world.facts.update(
        setting=setting,
        allergen_cfg=allergen_cfg,
        vessel_cfg=vessel_cfg,
        remedy=remedy_cfg,
        hero=hero,
        child=child,
        prankster=prankster,
        royal=royal,
        helper=helper,
        outcome=outcome,
        caught_in_time=caught_in_time,
        dusted=vessel.attrs.get("dusted_with") == allergen.id,
        predicted=world.facts.get("predicted_trouble", 0),
    )
    return world


def outcome_of(params: StoryParams) -> str:
    vessel = VESSELS[params.vessel]
    remedy = REMEDIES[params.remedy]
    return "prevented" if remedy_works(vessel, remedy) else "reaction"


KNOWLEDGE = {
    "allergy": [
        (
            "What is an allergy?",
            "An allergy is when a body reacts badly to something that seems harmless to other people. It can make someone sneeze, itch, cough, or feel unwell."
        )
    ],
    "pollen": [
        (
            "What is pollen?",
            "Pollen is a fine powder made by flowers and plants. It can drift in the air and tickle noses."
        )
    ],
    "rose": [
        (
            "Can flower pollen bother some people?",
            "Yes. Some people are sensitive to certain flowers, and the pollen can make them sneeze or feel poorly."
        )
    ],
    "lily": [
        (
            "Why might lilies make someone sneeze?",
            "Lilies can carry dusty pollen. If a person is sensitive to it, their nose and eyes may react quickly."
        )
    ],
    "flour": [
        (
            "What is flour used for?",
            "Flour is a powder used for baking breads and cakes. Some special flours may also carry things that sensitive people should avoid."
        )
    ],
    "swap": [
        (
            "Why is swapping a dangerous treat for a safe one a good idea?",
            "It removes the problem before anyone gets hurt. A quick safe swap can stop trouble before it starts."
        )
    ],
    "wash": [
        (
            "Why does washing something help remove dust or pollen?",
            "Water can rinse the tiny particles away. Then the object is cleaner and safer to touch or wear."
        )
    ],
    "humor": [
        (
            "What makes a joke kind instead of mean?",
            "A kind joke makes everyone feel included. A mean joke laughs at someone getting hurt or frightened."
        )
    ],
}
KNOWLEDGE_ORDER = ["allergy", "pollen", "rose", "lily", "flour", "swap", "wash", "humor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prankster = f["prankster"]
    allergen = f["allergen_cfg"]
    vessel = f["vessel_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    if outcome == "prevented":
        return [
            f'Write a fairy-tale story for ages 3 to 5 that includes the words "jerk", "allergy", and "vile". Use foreshadowing with an early sneeze and end with a safe feast in {setting.place}.',
            f"Tell a gentle humorous fairy tale where {prankster.id} plans a vile prank with {allergen.label}, but a clever child stops the danger before {child.id} touches the {vessel.label}.",
            f"Write a story in which a prank seems funny at first, then becomes serious because of an allergy, and ends with apology, safety, and a warm feast scene.",
        ]
    return [
        f'Write a fairy-tale story for ages 3 to 5 that includes the words "jerk", "allergy", and "vile". Use foreshadowing and a silly sneeze scene.',
        f"Tell a fairy tale where {prankster.id} ignores a warning about {child.id}'s allergy, and the {vessel.label} causes a sneezy problem before the adults make things right.",
        f"Write a gentle cautionary tale with humor, a foolish prank, and a lesson that cruel jokes are not really funny.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    child = f["child"]
    prankster = f["prankster"]
    royal = f["royal"]
    helper = f["helper"]
    allergen = f["allergen_cfg"]
    vessel = f["vessel_cfg"]
    remedy = f["remedy"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a careful child at a royal feast, {child.id}, who had an allergy, and {prankster.id}, who tried to play a cruel joke. The royal host and {helper.label_word} helped put things right."
        ),
        (
            "What was the early warning in the story?",
            f"The early warning was {child.id}'s small sneeze when {allergen.drift} blew by. That foreshadowed the bigger trouble the same allergen could cause later."
        ),
        (
            f"What vile plan did {prankster.id} make?",
            f"{prankster.id} wanted to dust the {vessel.label} with {allergen.label} as a prank. It was a vile idea because {child.id}'s allergy made it dangerous, not funny."
        ),
    ]
    if outcome == "prevented":
        qa.append(
            (
                f"How was the danger stopped?",
                f"{hero.id} noticed what the prank meant and warned the grown-ups in time. Then the {royal.label_word} {remedy.qa_text}, so {child.id} never had the reaction at all."
            )
        )
        qa.append(
            (
                f"Why did the joke stop being funny?",
                f"The joke stopped being funny as soon as everyone understood it could trigger an allergy. A laugh is not worth it when someone might get sick or frightened."
            )
        )
    else:
        qa.append(
            (
                f"What happened when the {vessel.label} came near {child.id}?",
                f"{child.id}'s allergy flared up and {child.pronoun()} started sneezing right away. The earlier sneeze had warned that the same dust would cause bigger trouble if it came too close."
            )
        )
        qa.append(
            (
                f"How did {helper.label_word} help after the reaction?",
                f"{helper.label_word.capitalize()} brought cool water, clean linen, and a safe treat until {child.id} felt better. That calm care turned a scary moment back into a gentle ending."
            )
        )
    qa.append(
        (
            f"What did {prankster.id} learn at the end?",
            f"{prankster.id} admitted that he had been a jerk and that cruel jokes are not real humor. He apologized and helped clean up, which proved he was trying to change."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["allergen_cfg"].tags)
    remedy = world.facts["remedy"]
    if remedy.id in {"swap", "wash"}:
        tags.add(remedy.id)
    tags.add("humor")
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="rose_garden",
        allergen="rose_pollen",
        vessel="crown",
        remedy="swap",
        hero_name="Lina",
        hero_gender="girl",
        prankster_name="Ned",
        prankster_gender="boy",
        royal_type="queen",
        helper_type="fairy_godmother",
        seed=101,
    ),
    StoryParams(
        setting="moon_court",
        allergen="bee_flour",
        vessel="tart",
        remedy="swap",
        hero_name="Milo",
        hero_gender="boy",
        prankster_name="Bram",
        prankster_gender="boy",
        royal_type="king",
        helper_type="fairy_godmother",
        seed=102,
    ),
    StoryParams(
        setting="river_green",
        allergen="lily_dust",
        vessel="cup",
        remedy="wash",
        hero_name="Ivy",
        hero_gender="girl",
        prankster_name="Hugo",
        prankster_gender="boy",
        royal_type="queen",
        helper_type="fairy_godmother",
        seed=103,
    ),
    StoryParams(
        setting="rose_garden",
        allergen="bee_flour",
        vessel="tart",
        remedy="snatch",
        hero_name="Wren",
        hero_gender="girl",
        prankster_name="Finn",
        prankster_gender="boy",
        royal_type="king",
        helper_type="fairy_godmother",
        seed=104,
    ),
]


ASP_RULES = r"""
hazard(A, V) :- allergen(A), vessel(V), prankworthy(V).
good_remedy(R) :- remedy(R), kind(R, K), kind_min(M), K >= M.
works(V, R) :- vessel_kind(V, K), remedy(R), covers(R, K), good_remedy(R).
valid(S, A, V) :- setting(S), hazard(A, V), works(V, _).

prevented :- chosen_vessel(V), chosen_remedy(R), works(V, R).
reaction :- chosen_vessel(V), chosen_remedy(R), not works(V, R).

outcome(prevented) :- prevented.
outcome(reaction) :- reaction.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ALLERGENS:
        lines.append(asp.fact("allergen", aid))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("vessel_kind", vid, vessel.kind))
        if vessel.prankworthy:
            lines.append(asp.fact("prankworthy", vid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("kind", rid, remedy.kind))
        for cover in sorted(remedy.covers):
            lines.append(asp.fact("covers", rid, cover))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_remedy", params.remedy),
    ])
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

    checked = 0
    for params in CURATED:
        checked += 1
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome for curated params:", params)
    if rc == 0:
        print(f"OK: outcome model matches outcome_of() on {checked} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "allergy" not in sample.story.lower():
            raise StoryError("smoke test story missing expected content")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print("SMOKE TEST FAILED:", err)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale allergy prank storyworld. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--allergen", choices=ALLERGENS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--prankster-name")
    ap.add_argument("--prankster-gender", choices=["girl", "boy"])
    ap.add_argument("--royal-type", choices=["queen", "king"])
    ap.add_argument("--helper-type", choices=["fairy_godmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.allergen and args.vessel:
        allergen = ALLERGENS[args.allergen]
        vessel = VESSELS[args.vessel]
        if not hazard_at_risk(allergen, vessel):
            raise StoryError(explain_rejection(allergen, vessel))
    if args.remedy and args.vessel:
        vessel = VESSELS[args.vessel]
        remedy = REMEDIES[args.remedy]
        if not remedy_works(vessel, remedy):
            raise StoryError(explain_remedy(args.remedy, vessel))
    elif args.remedy and args.remedy in REMEDIES and args.vessel is None:
        if REMEDIES[args.remedy].kind < KIND_MIN:
            raise StoryError(explain_remedy(args.remedy, VESSELS["tart"]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.allergen is None or combo[1] == args.allergen)
        and (args.vessel is None or combo[2] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, allergen, vessel = rng.choice(sorted(combos))

    possible_remedies = [
        rid for rid, remedy in REMEDIES.items()
        if remedy_works(VESSELS[vessel], remedy)
    ]
    if args.remedy:
        if args.remedy not in possible_remedies:
            raise StoryError(explain_remedy(args.remedy, VESSELS[vessel]))
        remedy = args.remedy
    else:
        remedy = rng.choice(sorted(possible_remedies))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    prankster_gender = args.prankster_gender or "boy"
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    prank_pool = GIRL_NAMES if prankster_gender == "girl" else BOY_NAMES
    prank_choices = [name for name in prank_pool if name != hero_name]
    prankster_name = args.prankster_name or rng.choice(prank_choices)
    royal_type = args.royal_type or rng.choice(["queen", "king"])
    helper_type = args.helper_type or "fairy_godmother"

    return StoryParams(
        setting=setting,
        allergen=allergen,
        vessel=vessel,
        remedy=remedy,
        hero_name=hero_name,
        hero_gender=hero_gender,
        prankster_name=prankster_name,
        prankster_gender=prankster_gender,
        royal_type=royal_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.allergen not in ALLERGENS:
        raise StoryError(f"(Unknown allergen: {params.allergen})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")

    setting = SETTINGS[params.setting]
    allergen = ALLERGENS[params.allergen]
    vessel = VESSELS[params.vessel]
    remedy = REMEDIES[params.remedy]

    if not hazard_at_risk(allergen, vessel):
        raise StoryError(explain_rejection(allergen, vessel))

    world = tell(
        setting=setting,
        allergen_cfg=allergen,
        vessel_cfg=vessel,
        remedy_cfg=remedy,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        prankster_name=params.prankster_name,
        prankster_gender=params.prankster_gender,
        royal_type=params.royal_type,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} compatible (setting, allergen, vessel) combos:\n")
        for setting, allergen, vessel in combos:
            print(f"  {setting:12} {allergen:12} {vessel}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.allergen} prank at {p.setting} "
                f"({p.vessel}, {p.remedy}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
