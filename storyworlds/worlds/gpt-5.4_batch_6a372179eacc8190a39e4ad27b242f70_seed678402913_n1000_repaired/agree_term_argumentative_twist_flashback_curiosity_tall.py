#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/agree_term_argumentative_twist_flashback_curiosity_tall.py
=====================================================================================

A standalone storyworld for a tall-tale county-fair growing contest where two
children argue over what a contest "term" means. One child is openly
argumentative, the other is curious enough to look closer, and a flashback helps
them understand the rule before a twist at judging time.

The world prefers a small set of plausible variants over broad coverage:
- a fairground only supports crops it can actually host,
- low-common-sense "boosts" are refused,
- outcomes come from world state: steady teamwork can win, a reckless surge can
  topple a stalk, and bickering can also lose in a quieter way.

Run it
------
    python storyworlds/worlds/gpt-5.4/agree_term_argumentative_twist_flashback_curiosity_tall.py
    python storyworlds/worlds/gpt-5.4/agree_term_argumentative_twist_flashback_curiosity_tall.py --all
    python storyworlds/worlds/gpt-5.4/agree_term_argumentative_twist_flashback_curiosity_tall.py --qa --json
    python storyworlds/worlds/gpt-5.4/agree_term_argumentative_twist_flashback_curiosity_tall.py --verify
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
SENSE_MIN = 2
ARGUMENT_BASE = 4
CURIOUS_TRAITS = {"curious", "careful", "thoughtful"}


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


@dataclass
class Fairground:
    id: str
    label: str
    opening: str
    landmark: str
    water_easy: int
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Crop:
    id: str
    label: str
    sprout: str
    giant_image: str
    sturdiness: int
    thirst: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Boost:
    id: str
    label: str
    method: str
    force: int
    sense: int
    strain: int
    moisture_cost: int
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    memory: str
    clue: str
    clarity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, fairground: Fairground) -> None:
        self.fairground = fairground
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
        clone = World(self.fairground)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_topple(world: World) -> list[str]:
    crop = world.get("crop")
    if crop.meters["strain"] < crop.attrs.get("sturdiness", 0) + 1:
        return []
    sig = ("topple", "crop")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["toppled"] += 1
    crop.meters["height"] = max(0.0, crop.meters["height"] - 1.0)
    world.get("argumentative").memes["shock"] += 1
    world.get("curious").memes["worry"] += 1
    return ["__topple__"]


def _r_bloom(world: World) -> list[str]:
    crop = world.get("crop")
    if crop.meters["height"] < 3:
        return []
    if world.get("argumentative").memes["agreed"] < THRESHOLD:
        return []
    if crop.meters["dry"] >= THRESHOLD or crop.meters["toppled"] >= THRESHOLD:
        return []
    sig = ("bloom", "crop")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["bloomed"] += 1
    return ["__bloom__"]


CAUSAL_RULES = [
    Rule(name="topple", tag="physical", apply=_r_topple),
    Rule(name="bloom", tag="physical", apply=_r_bloom),
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
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


FAIRGROUNDS = {
    "riverfair": Fairground(
        id="riverfair",
        label="the Riverfair",
        opening="wagons stood wheel to wheel, and the bunting snapped so high it seemed to tickle the clouds",
        landmark="the silver pump by the melon tent",
        water_easy=3,
        supports={"skybean", "sunflower", "laddercorn"},
        tags={"fair"},
    ),
    "hillfair": Fairground(
        id="hillfair",
        label="the Hilltop Fair",
        opening="the midway climbed the hill like a ribbon trying to tie a bow around the moon",
        landmark="the windmill cistern",
        water_easy=2,
        supports={"skybean", "sunflower"},
        tags={"fair", "windmill"},
    ),
    "barnfair": Fairground(
        id="barnfair",
        label="the Barnstorm Fair",
        opening="red barns loomed so broad that swallows treated their rafters like whole neighborhoods",
        landmark="the rain barrel behind the pie stand",
        water_easy=1,
        supports={"sunflower", "laddercorn"},
        tags={"fair", "barn"},
    ),
}

CROPS = {
    "skybean": Crop(
        id="skybean",
        label="sky-bean",
        sprout="a green hook no taller than a spoon",
        giant_image="its vine could one day loop around the flagpole and wink at passing geese",
        sturdiness=2,
        thirst=2,
        tags={"bean", "plant"},
    ),
    "sunflower": Crop(
        id="sunflower",
        label="sunflower",
        sprout="a fuzzy stem with two brave leaves",
        giant_image="its face could one day look the weather straight in the nose",
        sturdiness=3,
        thirst=1,
        tags={"flower", "plant"},
    ),
    "laddercorn": Crop(
        id="laddercorn",
        label="ladder corn",
        sprout="a striped shoot that already seemed to be measuring the sky",
        giant_image="its stalk could one day stand so straight a squirrel might climb it like stairs",
        sturdiness=2,
        thirst=2,
        tags={"corn", "plant"},
    ),
}

BOOSTS = {
    "thunder_tonic": Boost(
        id="thunder_tonic",
        label="thunder tonic",
        method="splashed a fizzy spoonful of thunder tonic into the soil",
        force=3,
        sense=3,
        strain=3,
        moisture_cost=1,
        qa_text="used thunder tonic for a sudden burst of growth",
        tags={"tonic", "boost"},
    ),
    "echo_song": Boost(
        id="echo_song",
        label="echo song",
        method="sang the old echo song into the leaves",
        force=2,
        sense=2,
        strain=1,
        moisture_cost=0,
        qa_text="sang an echo song to coax the plant upward",
        tags={"song", "boost"},
    ),
    "cannon_breath": Boost(
        id="cannon_breath",
        label="cannon breath",
        method="blew on the sprout through a brass cannon tube",
        force=4,
        sense=1,
        strain=4,
        moisture_cost=2,
        qa_text="blasted the sprout with cannon breath",
        tags={"wind", "boost"},
    ),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        label="Grandma June",
        phrase="Grandma June, who knew every fair rule from the year the carousel had only three horses",
        memory='Last year Grandma June had tapped the sign and said, "The term lasts as long as the fair, not as short as your temper."',
        clue="the old painted word term on the signboard",
        clarity=3,
        tags={"grandma", "memory"},
    ),
    "seedseller": Helper(
        id="seedseller",
        label="Mr. Pebble the seed seller",
        phrase="Mr. Pebble the seed seller, whose pockets always rattled with kernels and advice",
        memory='Once Mr. Pebble had said, "A giant plant listens for steady hands longer than it listens for loud noise."',
        clue="a dog-eared packet note tucked under the seed tray",
        clarity=2,
        tags={"seller", "memory"},
    ),
    "judge": Helper(
        id="judge",
        label="Judge Maple",
        phrase="Judge Maple, who wore a measuring tape like a mayoral sash",
        memory='On opening morning Judge Maple had boomed, "Read the whole card before you chase the ribbon."',
        clue="a brass judging card hanging from the post",
        clarity=1,
        tags={"judge", "memory"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "thoughtful", "careful", "bold", "cheerful", "stubborn"]


@dataclass
class StoryParams:
    fairground: str
    crop: str
    boost: str
    helper: str
    argumentative_name: str
    argumentative_gender: str
    curious_name: str
    curious_gender: str
    parent: str
    curious_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        fairground="riverfair",
        crop="skybean",
        boost="thunder_tonic",
        helper="grandma",
        argumentative_name="Tom",
        argumentative_gender="boy",
        curious_name="Lily",
        curious_gender="girl",
        parent="mother",
        curious_trait="curious",
    ),
    StoryParams(
        fairground="hillfair",
        crop="sunflower",
        boost="echo_song",
        helper="seedseller",
        argumentative_name="Max",
        argumentative_gender="boy",
        curious_name="Mia",
        curious_gender="girl",
        parent="father",
        curious_trait="thoughtful",
    ),
    StoryParams(
        fairground="barnfair",
        crop="laddercorn",
        boost="thunder_tonic",
        helper="judge",
        argumentative_name="Sam",
        argumentative_gender="boy",
        curious_name="Zoe",
        curious_gender="girl",
        parent="mother",
        curious_trait="bold",
    ),
]


def fair_supports_crop(fairground: Fairground, crop: Crop) -> bool:
    return crop.id in fairground.supports


def sensible_boosts() -> list[Boost]:
    return [b for b in BOOSTS.values() if b.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for fair_id, fair in FAIRGROUNDS.items():
        for crop_id, crop in CROPS.items():
            if not fair_supports_crop(fair, crop):
                continue
            for boost_id, boost in BOOSTS.items():
                if boost.sense < SENSE_MIN:
                    continue
                for helper_id in HELPERS:
                    combos.append((fair_id, crop_id, boost_id, helper_id))
    return combos


def curiosity_value(trait: str) -> int:
    return 3 if trait in CURIOUS_TRAITS else 1


def will_agree(params: StoryParams) -> bool:
    return curiosity_value(params.curious_trait) + HELPERS[params.helper].clarity > ARGUMENT_BASE


def will_topple(params: StoryParams) -> bool:
    crop = CROPS[params.crop]
    boost = BOOSTS[params.boost]
    fair = FAIRGROUNDS[params.fairground]
    strain = boost.strain + max(0, crop.thirst - fair.water_easy)
    return boost.force > crop.sturdiness and strain >= crop.sturdiness + 1


def outcome_of(params: StoryParams) -> str:
    if will_agree(params):
        return "agreed"
    if will_topple(params):
        return "toppled"
    return "lost"


def explain_rejection(fairground: Fairground, crop: Crop) -> str:
    return (
        f"(No story: {fairground.label} is not set up for a {crop.label} contest. "
        f"That fair can only host crops it has room and water for.)"
    )


def explain_boost(boost_id: str) -> str:
    boost = BOOSTS[boost_id]
    better = ", ".join(sorted(b.id for b in sensible_boosts()))
    return (
        f"(Refusing boost '{boost_id}': it scores too low on common sense "
        f"(sense={boost.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def _do_care(world: World, amount: int, narrate: bool = True) -> None:
    crop = world.get("crop")
    crop.meters["water"] += amount
    crop.meters["height"] += 1
    world.get("argumentative").memes["hope"] += 1
    world.get("curious").memes["hope"] += 1
    propagate(world, narrate=narrate)


def _do_boost(world: World, boost: Boost, narrate: bool = True) -> None:
    crop = world.get("crop")
    crop.meters["height"] += boost.force
    crop.meters["strain"] += boost.strain
    crop.meters["water"] = max(0.0, crop.meters["water"] - boost.moisture_cost)
    if crop.meters["water"] < crop.attrs.get("thirst", 0):
        crop.meters["dry"] += 1
    world.get("argumentative").memes["pride"] += 1
    propagate(world, narrate=narrate)


def predict_after_boost(world: World, boost: Boost) -> dict:
    sim = world.copy()
    _do_boost(sim, boost, narrate=False)
    crop = sim.get("crop")
    return {
        "height": crop.meters["height"],
        "toppled": crop.meters["toppled"] >= THRESHOLD,
        "dry": crop.meters["dry"] >= THRESHOLD,
    }


def opening_scene(world: World, arguer: Entity, curious: Entity, crop: Crop, fair: Fairground) -> None:
    arguer.memes["argument"] += 1
    curious.memes["curiosity"] += curiosity_value(curious.traits[0])
    world.say(
        f"At {fair.label}, {fair.opening}. In the middle of all that bragging weather, "
        f"{arguer.id} and {curious.id} carried a pot holding {crop.sprout}, because they had entered the giant-growing contest."
    )
    world.say(
        f"The little {crop.label} looked harmless then, though everyone in town swore {crop.giant_image}."
    )


def read_sign(world: World, arguer: Entity, curious: Entity) -> None:
    world.say(
        f"Over the booth hung a sign that said, 'Tallest plant at the end of the fair term.' "
        f"{arguer.id} read the word term, puffed up, and said it plainly meant by sundown."
    )
    world.say(
        f"{curious.id} was not so sure. In one breath the two of them turned thoroughly argumentative, "
        f"and even the pie tins on the next table seemed to rattle at the noise."
    )


def temptation(world: World, arguer: Entity, boost: Boost) -> None:
    pred = predict_after_boost(world, boost)
    world.facts["predicted_topple"] = pred["toppled"]
    world.facts["predicted_dry"] = pred["dry"]
    extra = " before the crows could finish one complaint" if pred["height"] >= 3 else " in a hurry"
    world.say(
        f'"Then we can win fast," said {arguer.id}. {arguer.pronoun("subject").capitalize()} wanted to use {boost.label} and {boost.method}{extra}.'
    )


def curiosity_and_flashback(world: World, curious: Entity, helper: Helper, parent: Entity) -> None:
    curious.memes["curiosity"] += 1
    curious.memes["memory"] += 1
    world.say(
        f"But {curious.id} kept staring at {helper.clue}. Curiosity tugged harder than the ribbon, "
        f"so {curious.pronoun('subject')} stopped arguing long enough to remember {helper.phrase}."
    )
    world.say(
        f"In a flashback, {helper.memory}"
    )
    world.say(
        f"{curious.id} looked from the sign to {parent.label_word} and back again. "
        f'"Maybe the term means the whole fair," {curious.pronoun("subject")} said softly.'
    )


def agree_branch(world: World, arguer: Entity, curious: Entity, crop: Crop, fair: Fairground, helper: Helper) -> None:
    arguer.memes["agreed"] += 1
    curious.memes["agreed"] += 1
    arguer.memes["argument"] = 0.0
    curious.memes["relief"] += 1
    world.say(
        f"{arguer.id} huffed once, twice, then finally nodded. "
        f'"All right," {arguer.pronoun("subject")} said. "I agree. We will grow it the long way, for the whole term."'
    )
    world.say(
        f"They hauled water from {fair.landmark}, loosened the soil with their fingers, and turned the pot a little so each side got the sun."
    )
    _do_care(world, amount=fair.water_easy, narrate=False)
    world.say(
        f"By afternoon the {crop.label} had climbed from a whisper of green into something worth staring at. "
        f"It did not leap; it rose the way a good promise rises, steady and sure."
    )
    _do_care(world, amount=1, narrate=False)
    world.say(
        f"When judging time came, Judge Maple tipped the pot and revealed the twist: the contest used twin-root seeds, "
        f"so no child could win alone. Only partners who could agree and tend both sides for the full term ever saw the hidden bloom."
    )
    if world.get("crop").meters["bloomed"] >= THRESHOLD:
        world.say(
            f"At that very word, the stem opened a gold bloom broad as a supper plate. "
            f"The crowd cheered, because the flower proved what had changed: the children had grown teamwork faster than the plant had grown height."
        )
    world.facts["twist_text"] = "the seed had twin roots and needed two children working together for the full fair term"


def topple_branch(world: World, arguer: Entity, curious: Entity, crop: Crop, boost: Boost) -> None:
    world.say(
        f"{arguer.id} shook {arguer.pronoun('possessive')} head. "
        f'"A ribbon cannot wait all week," {arguer.pronoun("subject")} said, and {boost.method}.'
    )
    _do_boost(world, boost, narrate=False)
    world.say(
        f"For one thrilling blink the {crop.label} shot upward so fast it seemed to be climbing a ladder nobody could see."
    )
    if world.get("crop").meters["toppled"] >= THRESHOLD:
        world.say(
            f"Then came the turn. The stalk bent, gave a long complaining creak, and toppled sideways across three seed catalogs and a bucket of radishes."
        )
    if world.get("crop").meters["dry"] >= THRESHOLD:
        world.say(
            f"The leaves also curled at the edges, because all that hurry had drunk the pot nearly dry."
        )
    world.say(
        f"{curious.id} did not shout 'I told you so.' {curious.pronoun('subject').capitalize()} only steadied the broken pot while {arguer.id} stared at it, small at last beside the mess."
    )
    world.say(
        f"Judge Maple helped them prop the pieces aside and said the fair had room for mistakes, but not for shortcuts that forgot what a living thing could bear."
    )
    world.facts["twist_text"] = "the fastest-looking growth was the weakest, and the giant stalk could not carry its own hurry"


def lost_branch(world: World, arguer: Entity, curious: Entity, crop: Crop, boost: Boost, fair: Fairground) -> None:
    world.say(
        f"{arguer.id} would not listen, and {curious.id} gave up arguing back. They used {boost.label}, and the {crop.label} did grow taller by supper."
    )
    _do_boost(world, boost, narrate=False)
    world.say(
        f"It stood high enough to cast a skinny evening shadow all the way to {fair.landmark}."
    )
    if world.get("crop").meters["dry"] >= THRESHOLD:
        world.say(
            f"But the leaves felt papery, and one side of the pot had gone dry while the children had been busy proving who was right."
        )
    world.say(
        f"At judging time came the twist. Judge Maple lifted the entry card and explained that the fair term was the whole run of the fair, "
        f"and each pot had to be tended morning and evening by both partners."
    )
    world.say(
        f"Another team won the ribbon with a shorter plant and healthier leaves. "
        f"{arguer.id} looked at {curious.id}, and this time the silence between them was wiser than the earlier argument."
    )
    world.say(
        f"The next morning they came back with water, patience, and no need to be argumentative. "
        f"They did not win the ribbon, but their little plant stood straighter, which was proof enough that they had finally learned the long term."
    )
    world.facts["twist_text"] = "height alone did not decide the contest; the full fair term and shared care mattered more"


def tell(
    fairground: Fairground,
    crop_cfg: Crop,
    boost: Boost,
    helper: Helper,
    argumentative_name: str = "Tom",
    argumentative_gender: str = "boy",
    curious_name: str = "Lily",
    curious_gender: str = "girl",
    parent_type: str = "mother",
    curious_trait: str = "curious",
) -> World:
    world = World(fairground)
    arguer = world.add(
        Entity(
            id=argumentative_name,
            kind="character",
            type=argumentative_gender,
            role="argumentative",
            label=argumentative_name,
            traits=["argumentative"],
        )
    )
    curious = world.add(
        Entity(
            id=curious_name,
            kind="character",
            type=curious_gender,
            role="curious",
            label=curious_name,
            traits=[curious_trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    crop = world.add(
        Entity(
            id="crop",
            kind="thing",
            type="plant",
            label=crop_cfg.label,
            phrase=f"the {crop_cfg.label}",
            attrs={"sturdiness": crop_cfg.sturdiness, "thirst": crop_cfg.thirst},
            tags=set(crop_cfg.tags),
        )
    )
    crop.meters["water"] = fairground.water_easy
    crop.meters["height"] = 0.0

    opening_scene(world, arguer, curious, crop_cfg, fairground)
    read_sign(world, arguer, curious)

    world.para()
    temptation(world, arguer, boost)
    curiosity_and_flashback(world, curious, helper, parent)

    world.para()
    if will_agree(
        StoryParams(
            fairground=fairground.id,
            crop=crop_cfg.id,
            boost=boost.id,
            helper=helper.id,
            argumentative_name=argumentative_name,
            argumentative_gender=argumentative_gender,
            curious_name=curious_name,
            curious_gender=curious_gender,
            parent=parent_type,
            curious_trait=curious_trait,
        )
    ):
        agree_branch(world, arguer, curious, crop_cfg, fairground, helper)
        outcome = "agreed"
    elif will_topple(
        StoryParams(
            fairground=fairground.id,
            crop=crop_cfg.id,
            boost=boost.id,
            helper=helper.id,
            argumentative_name=argumentative_name,
            argumentative_gender=argumentative_gender,
            curious_name=curious_name,
            curious_gender=curious_gender,
            parent=parent_type,
            curious_trait=curious_trait,
        )
    ):
        topple_branch(world, arguer, curious, crop_cfg, boost)
        outcome = "toppled"
    else:
        lost_branch(world, arguer, curious, crop_cfg, boost, fairground)
        outcome = "lost"

    world.facts.update(
        fairground=fairground,
        crop_cfg=crop_cfg,
        boost=boost,
        helper=helper,
        argumentative=arguer,
        curious=curious,
        parent=parent,
        crop=crop,
        outcome=outcome,
        agreed=arguer.memes["agreed"] >= THRESHOLD,
        toppled=crop.meters["toppled"] >= THRESHOLD,
        bloomed=crop.meters["bloomed"] >= THRESHOLD,
        dry=crop.meters["dry"] >= THRESHOLD,
        twist=world.facts.get("twist_text", ""),
    )
    return world


KNOWLEDGE = {
    "fair": [
        (
            "What is a fair?",
            "A fair is a big gathering with games, food, booths, and contests. People come to show things they made or grew and to have fun together.",
        )
    ],
    "plant": [
        (
            "Why do plants need steady care?",
            "Plants need water, light, and time over and over again. A plant can grow quickly for a moment, but healthy growth comes from care that lasts.",
        )
    ],
    "bean": [
        (
            "What is a bean vine?",
            "A bean vine is a climbing plant with a thin stem that likes to reach upward. It often needs something to hold onto as it grows.",
        )
    ],
    "flower": [
        (
            "What does a sunflower do?",
            "A sunflower grows a tall stem and a big flower head. It likes bright sun and can turn its face toward the light.",
        )
    ],
    "corn": [
        (
            "What is corn stalk like?",
            "A corn stalk is a tall, straight plant stem. It grows in sections and can stand firm when it has enough water and room.",
        )
    ],
    "tonic": [
        (
            "Why can a quick plant tonic be risky?",
            "A quick tonic might push a plant too fast before the stem is strong enough. When something grows too suddenly, it can bend or break.",
        )
    ],
    "song": [
        (
            "Why do stories sometimes say singing helps plants?",
            "People often sing to plants in stories because songs can show patience, attention, and care. The song itself is magical in the tale, but the real lesson is steady tending.",
        )
    ],
    "memory": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly looks back to something that happened before. It helps a character remember a clue or a lesson.",
        )
    ],
    "grandma": [
        (
            "Why do grandparents often help in stories?",
            "Grandparents in stories often remember old rules, sayings, or lessons. Their memories can help children slow down and think more clearly.",
        )
    ],
}


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two children"
    if a.type == "girl" and b.type == "girl":
        return "two children"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["argumentative"]
    c = f["curious"]
    crop = f["crop_cfg"]
    boost = f["boost"]
    outcome = f["outcome"]
    base = (
        f'Write a Tall Tale for a 3-to-5-year-old that includes the words "agree", "term", and "argumentative". '
        f"Use curiosity, a flashback, and a twist in a county-fair story about a giant {crop.label}."
    )
    if outcome == "agreed":
        return [
            base,
            f"Tell a tall county-fair story where {a.id} and {c.id} argue over what the contest term means, but {c.id}'s curiosity and a flashback help them agree and win together.",
            f"Write a story where a child wants to use {boost.label} for fast growth, yet the ending proves that teamwork over the whole term matters more than rushing.",
        ]
    if outcome == "toppled":
        return [
            base,
            f"Tell a cautionary tall tale where {a.id} refuses to agree, uses {boost.label}, and the giant plant shoots up before toppling over.",
            f"Write a story with a flashback clue and a twist showing that the fastest-looking growth can be the weakest.",
        ]
    return [
        base,
        f"Tell a tall tale where {a.id} stays argumentative, the children misread the contest term, and the twist is that shared care matters more than being tallest for one evening.",
        f"Write a story where curiosity almost saves the day, but the lesson lands after the ribbon is already gone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["argumentative"]
    c = f["curious"]
    crop = f["crop_cfg"]
    boost = f["boost"]
    fair = f["fairground"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, c)}, {a.id} and {c.id}, at {fair.label}. They are trying to grow a giant {crop.label} for the fair contest.",
        ),
        (
            "Why did the children start arguing?",
            f"They argued because the sign used the word term, and {a.id} thought it meant only until sundown. {c.id} suspected it meant the whole fair, so the misunderstanding made them argumentative.",
        ),
        (
            f"What did {c.id}'s curiosity do?",
            f"{c.id}'s curiosity made {c.pronoun('object')} stop and study {helper.clue}. That pause led to a flashback, which gave the children a clue about the real rule.",
        ),
    ]
    if outcome == "agreed":
        qa.append(
            (
                f"How did {a.id} and {c.id} solve the problem?",
                f"They decided to agree and care for the plant patiently instead of chasing one fast trick. Because they watered and tended both sides through the full term, the hidden bloom appeared at judging time.",
            )
        )
        qa.append(
            (
                "What was the twist?",
                f"The twist was that the seed had twin roots and the contest was really about shared care over the full term. The bloom at the end proved the children had changed from arguing partners into working partners.",
            )
        )
    elif outcome == "toppled":
        qa.append(
            (
                f"What happened when {a.id} used {boost.label}?",
                f"The plant leaped upward for a moment, but the sudden growth strained it too much. Then the stalk toppled, which showed that speed was not the same thing as strength.",
            )
        )
        qa.append(
            (
                "What was the lesson?",
                f"The children learned that a living thing cannot carry more hurry than its stem can bear. The flashback had warned them, but the lesson became real only after the plant fell.",
            )
        )
    else:
        qa.append(
            (
                "Did the children win the ribbon?",
                f"No, they did not. Their plant grew taller for one evening, but they had not cared for it the right way over the whole fair term, so another team won.",
            )
        )
        qa.append(
            (
                "What was the twist?",
                f"The twist was that height alone did not decide the contest. The judges wanted shared care over the whole term, so the children lost first and understood the rule only afterward.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["fairground"].tags) | set(f["crop_cfg"].tags) | set(f["boost"].tags) | set(f["helper"].tags)
    out: list[tuple[str, str]] = []
    order = ["fair", "plant", "bean", "flower", "corn", "tonic", "song", "memory", "grandma"]
    for tag in order:
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supports_crop(F, C) :- fairground(F), crop(C), support(F, C).
sensible(B) :- boost(B), sense(B, S), sense_min(M), S >= M.
valid(F, C, B, H) :- fairground(F), crop(C), boost(B), helper(H),
                     supports_crop(F, C), sensible(B).

curiosity_score(3) :- chosen_trait(T), curious_trait(T).
curiosity_score(1) :- chosen_trait(T), not curious_trait(T).

agreed :- chosen_helper(H), clarity(H, Cl), curiosity_score(Cs), argument_base(A), Cs + Cl > A.

extra_strain(0) :- chosen_fair(F), chosen_crop(C), thirst(C, T), water_easy(F, W), T <= W.
extra_strain(T - W) :- chosen_fair(F), chosen_crop(C), thirst(C, T), water_easy(F, W), T > W.

toppled :- chosen_boost(B), chosen_crop(C),
           force(B, F), sturdiness(C, S), F > S,
           strain(B, St), extra_strain(Ex), St + Ex >= S + 1.

outcome(agreed) :- agreed.
outcome(toppled) :- not agreed, toppled.
outcome(lost) :- not agreed, not toppled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fair_id, fair in FAIRGROUNDS.items():
        lines.append(asp.fact("fairground", fair_id))
        lines.append(asp.fact("water_easy", fair_id, fair.water_easy))
        for crop_id in sorted(fair.supports):
            lines.append(asp.fact("support", fair_id, crop_id))
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        lines.append(asp.fact("sturdiness", crop_id, crop.sturdiness))
        lines.append(asp.fact("thirst", crop_id, crop.thirst))
    for boost_id, boost in BOOSTS.items():
        lines.append(asp.fact("boost", boost_id))
        lines.append(asp.fact("force", boost_id, boost.force))
        lines.append(asp.fact("sense", boost_id, boost.sense))
        lines.append(asp.fact("strain", boost_id, boost.strain))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("clarity", helper_id, helper.clarity))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("argument_base", ARGUMENT_BASE))
    for trait in sorted(CURIOUS_TRAITS):
        lines.append(asp.fact("curious_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_fair", params.fairground),
            asp.fact("chosen_crop", params.crop),
            asp.fact("chosen_boost", params.boost),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_trait", params.curious_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _smoke_emit(sample: StorySample) -> None:
    if not sample.story or "{" in sample.story or "}" in sample.story:
        raise StoryError("Story rendering failed smoke check.")


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

    clingo_sens, python_sens = set(asp_sensible()), {b.id for b in sensible_boosts()}
    if clingo_sens == python_sens:
        print(f"OK: sensible boosts match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible boosts: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        _smoke_emit(smoke)
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: two children argue over a fair-term rule, and curiosity may save the day."
    )
    ap.add_argument("--fairground", choices=FAIRGROUNDS)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--boost", choices=BOOSTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.boost and BOOSTS[args.boost].sense < SENSE_MIN:
        raise StoryError(explain_boost(args.boost))
    if args.fairground and args.crop:
        fair = FAIRGROUNDS[args.fairground]
        crop = CROPS[args.crop]
        if not fair_supports_crop(fair, crop):
            raise StoryError(explain_rejection(fair, crop))

    combos = [
        combo
        for combo in valid_combos()
        if (args.fairground is None or combo[0] == args.fairground)
        and (args.crop is None or combo[1] == args.crop)
        and (args.boost is None or combo[2] == args.boost)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    fairground, crop, boost, helper = rng.choice(sorted(combos))
    argumentative_name, argumentative_gender = _pick_child(rng)
    curious_name, curious_gender = _pick_child(rng, avoid=argumentative_name)
    parent = args.parent or rng.choice(["mother", "father"])
    curious_trait = rng.choice(TRAITS)
    return StoryParams(
        fairground=fairground,
        crop=crop,
        boost=boost,
        helper=helper,
        argumentative_name=argumentative_name,
        argumentative_gender=argumentative_gender,
        curious_name=curious_name,
        curious_gender=curious_gender,
        parent=parent,
        curious_trait=curious_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.fairground not in FAIRGROUNDS:
        raise StoryError(f"(Unknown fairground: {params.fairground})")
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.boost not in BOOSTS:
        raise StoryError(f"(Unknown boost: {params.boost})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    fair = FAIRGROUNDS[params.fairground]
    crop = CROPS[params.crop]
    boost = BOOSTS[params.boost]
    helper = HELPERS[params.helper]

    if not fair_supports_crop(fair, crop):
        raise StoryError(explain_rejection(fair, crop))
    if boost.sense < SENSE_MIN:
        raise StoryError(explain_boost(boost.id))

    world = tell(
        fairground=fair,
        crop_cfg=crop,
        boost=boost,
        helper=helper,
        argumentative_name=params.argumentative_name,
        argumentative_gender=params.argumentative_gender,
        curious_name=params.curious_name,
        curious_gender=params.curious_gender,
        parent_type=params.parent,
        curious_trait=params.curious_trait,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible boosts: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (fairground, crop, boost, helper) combos:\n")
        for fair, crop, boost, helper in combos:
            print(f"  {fair:10} {crop:10} {boost:14} {helper}")
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
            header = f"### {p.argumentative_name} & {p.curious_name}: {p.crop} at {p.fairground} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
