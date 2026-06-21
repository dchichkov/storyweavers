#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/smore_banquet_foreshadowing_sound_effects_rhyme_folk.py
==================================================================================

A standalone story world for a small folk-tale domain built from the seed words
"smore" and "banquet", with deliberate use of foreshadowing, sound effects, and
light rhyme.

Premise
-------
In a little village, a child is chosen to carry a special treat to a moonlit
banquet. The treat may be a smore or another feast food, but the seed words
"smore" and "banquet" always appear in the story. On the road, an elder notices
a sign of trouble -- wind, rain, goats, or crows -- and gives a warning. The
child either hurries ahead and risks disaster, or uses a simple folk-tale tool
that fits the danger. The world model decides whether the food reaches the
banquet safely.

World logic
-----------
This script keeps the schema small and plain:

* one shared Entity dataclass with physical meters and emotional memes
* compact config dataclasses for road, treat, omen, and protection
* one forward-chaining rule engine for spoilage and worry
* one Python reasonableness gate plus an inline ASP twin
* three QA sets derived from the simulated world state

Run it
------
python storyworlds/worlds/gpt-5.4/smore_banquet_foreshadowing_sound_effects_rhyme_folk.py
python storyworlds/worlds/gpt-5.4/smore_banquet_foreshadowing_sound_effects_rhyme_folk.py --all
python storyworlds/worlds/gpt-5.4/smore_banquet_foreshadowing_sound_effects_rhyme_folk.py --trace
python storyworlds/worlds/gpt-5.4/smore_banquet_foreshadowing_sound_effects_rhyme_folk.py --qa --json
python storyworlds/worlds/gpt-5.4/smore_banquet_foreshadowing_sound_effects_rhyme_folk.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Road:
    id: str
    label: str
    place: str
    image: str
    banquet_image: str
    rhyme_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    texture: str
    precious: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    label: str
    risk: str
    sign: str
    sound: str
    danger_line: str
    spoil_line: str
    spread: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Protection:
    id: str
    label: str
    phrase: str
    guards: set[str]
    sense: int
    success_line: str
    fail_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    road: str
    treat: str
    omen: str
    protection: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    delay: int = 0
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


def _r_spoilage(world: World) -> list[str]:
    out: list[str] = []
    treat = world.get("treat")
    if treat.meters["threat"] < THRESHOLD:
        return out
    sig = ("spoilage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if treat.meters["shielded"] >= THRESHOLD:
        treat.meters["saved"] += 1
        return out
    treat.meters["spoiled"] += 1
    child = world.get("child")
    child.memes["sorrow"] += 1
    child.memes["fear"] += 1
    out.append("__spoiled__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    treat = world.get("treat")
    if treat.meters["threat"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="spoilage", tag="physical", apply=_r_spoilage),
    Rule(name="worry", tag="emotional", apply=_r_worry),
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


def treat_at_risk(omen: Omen, treat: Treat) -> bool:
    return omen.risk in {"wet", "jostled", "snatched"}


def protection_fits(omen: Omen, protection: Protection) -> bool:
    return omen.risk in protection.guards and protection.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for road_id in ROADS:
        for treat_id, treat in TREATS.items():
            for omen_id, omen in OMENS.items():
                if not treat_at_risk(omen, treat):
                    continue
                for prot_id, prot in PROTECTIONS.items():
                    if protection_fits(omen, prot):
                        combos.append((road_id, treat_id, omen_id, prot_id))
    return combos


def peril(omen: Omen, delay: int) -> int:
    return omen.spread + delay


def is_saved(omen: Omen, protection: Protection, delay: int) -> bool:
    return protection_fits(omen, protection) and protection.sense >= peril(omen, delay)


def predict_spoilage(world: World, omen: Omen, protection: Optional[Protection]) -> dict:
    sim = world.copy()
    treat = sim.get("treat")
    treat.meters["threat"] += 1
    if protection and omen.risk in protection.guards:
        treat.meters["shielded"] += 1
    propagate(sim, narrate=False)
    return {
        "spoiled": treat.meters["spoiled"] >= THRESHOLD,
        "saved": treat.meters["saved"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, elder: Entity, road: Road, treat: Treat) -> None:
    child.memes["duty"] += 1
    world.say(
        f"In the days when the moon was treated like a silver lamp over the fields, "
        f"{child.id} lived by {road.place}. "
        f"Each year the village laid out a moonlit banquet there, and this year "
        f"{child.id} was trusted to carry {treat.phrase} to the feast."
    )
    world.say(
        f"The {treat.label} was {treat.texture}, {treat.precious}, and so dear to the table "
        f"that even the word smore made the younger children lick their lips."
    )
    world.say(
        f"{road.image} {road.rhyme_line}"
    )
    world.say(
        f'{elder.label_word.capitalize()} said, "Carry it steady, carry it light; '
        f'what starts in the dusk must finish by night."'
    )


def foreshadow(world: World, elder: Entity, omen: Omen, child: Entity, treat: Treat) -> None:
    world.say(
        f"But before {child.id} set out, {elder.label_word} noticed {omen.sign}. "
        f'"{omen.sound}," went the road, and the old one grew still.'
    )
    pred = predict_spoilage(world, omen, None)
    world.facts["predicted_spoil"] = pred["spoiled"]
    world.say(
        f'{elder.label_word.capitalize()} touched the basket rim and whispered, '
        f'"When the world sounds like {omen.sound}, {omen.danger_line}"'
    )
    if pred["spoiled"]:
        world.say(
            f"The warning hung in the air like a little bell. It was a sign that the "
            f"{treat.label} might not reach the banquet whole."
        )


def haste(world: World, child: Entity, road: Road) -> None:
    child.memes["hurry"] += 1
    world.say(
        f"But {child.id}, being {child.attrs.get('trait', 'eager')}, thought the path looked short. "
        f'"Quick feet, sweet treat; quick feet, no defeat," {child.pronoun()} murmured, '
        f'and off {child.pronoun()} went along {road.label}.'
    )


def offer_protection(world: World, elder: Entity, protection: Protection, omen: Omen) -> None:
    world.say(
        f'{elder.label_word.capitalize()} held out {protection.phrase} and said, '
        f'"Take this with you. {protection.label.capitalize()} answers {omen.sound}."'
    )


def choose_protection(world: World, child: Entity, treat_ent: Entity, protection: Protection) -> None:
    child.memes["trust"] += 1
    treat_ent.meters["shielded"] += 1
    world.say(
        f"{child.id} stopped, listened, and took {protection.phrase}. "
        f"{protection.success_line}"
    )


def ignore_protection(world: World, child: Entity, protection: Protection) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'Yet {child.id} shook {child.pronoun("possessive")} head. '
        f'"The banquet waits, and I am late," {child.pronoun()} said, leaving {protection.label} behind.'
    )


def meet_omen(world: World, child: Entity, treat_ent: Entity, road: Road, omen: Omen) -> None:
    treat_ent.meters["threat"] += 1
    world.say(
        f"Halfway down {road.label}, the sign came true. "
        f'"{omen.sound}!" went the world. {omen.danger_line.capitalize()}'
    )
    propagate(world, narrate=False)


def disaster(world: World, child: Entity, treat: Treat, omen: Omen) -> None:
    world.say(
        f"{omen.spoil_line.capitalize()} The poor {treat.label} was no longer fit for a feast."
    )
    world.say(
        f"{child.id} stood still with hot cheeks and heavy eyes. "
        f"The road had kept its warning, and the warning had proved wise."
    )


def rescue(world: World, child: Entity, treat: Treat, protection: Protection, road: Road) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{protection.qa_line.capitalize()}, so the {treat.label} stayed safe all the way down {road.label}."
    )
    world.say(
        f'{child.id} laughed softly. "Shield in the hand, feast in the land," '
        f'{child.pronoun()} said.'
    )


def banquet_ending(world: World, child: Entity, treat: Treat, road: Road, saved: bool) -> None:
    if saved:
        child.memes["joy"] += 1
        world.say(
            f"At the clearing, lanterns glowed in the branches and the village banquet shone like a ring of stars. "
            f"When {child.id} lifted the {treat.label}, everyone clapped."
        )
        world.say(
            f"The first bite was sweet and smoky, and the little ones cried, "
            f'"Share more smore!" until even the fiddler laughed. '
            f"So the feast went bright that night: right was light, and care was might."
        )
    else:
        child.memes["lesson"] += 1
        world.say(
            f"At the clearing, the moonlit banquet was kind even in disappointment. "
            f"The neighbors made room for {child.id}, though the special treat was lost."
        )
        world.say(
            f'{child.id} told the truth and bowed {child.pronoun("possessive")} head. '
            f'Then the old fiddler tapped the table -- tap, tap -- and said, '
            f'"A feast can mend a plate, but not a lesson learned too late."'
        )
        world.say(
            f"After that night, {child.id} never mocked a true warning again."
        )


def tell(
    road: Road,
    treat: Treat,
    omen: Omen,
    protection: Protection,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    child_trait: str = "eager",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"trait": child_trait},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    treat_ent = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=treat.label,
        phrase=treat.phrase,
        role="treat",
        owner=child_name,
        tags=set(treat.tags),
    ))
    road_ent = world.add(Entity(
        id="road",
        kind="thing",
        type="road",
        label=road.label,
        phrase=road.place,
        role="road",
        tags=set(road.tags),
    ))

    opening(world, child, elder, road, treat)
    world.para()
    foreshadow(world, elder, omen, child, treat)
    offer_protection(world, elder, protection, omen)

    saved = is_saved(omen, protection, delay)

    world.para()
    if saved:
        choose_protection(world, child, treat_ent, protection)
    else:
        ignore_protection(world, child, protection)
    haste(world, child, road)
    meet_omen(world, child, treat_ent, road, omen)

    world.para()
    if treat_ent.meters["spoiled"] >= THRESHOLD:
        disaster(world, child, treat, omen)
    else:
        rescue(world, child, treat, protection, road)

    world.para()
    banquet_ending(world, child, treat, road, saved=treat_ent.meters["spoiled"] < THRESHOLD)

    outcome = "saved" if treat_ent.meters["spoiled"] < THRESHOLD else "spoiled"
    world.facts.update(
        child=child,
        elder=elder,
        treat_cfg=treat,
        treat=treat_ent,
        road=road,
        omen=omen,
        protection=protection,
        outcome=outcome,
        saved=outcome == "saved",
        delay=delay,
        peril=peril(omen, delay),
    )
    return world


ROADS = {
    "reed_path": Road(
        id="reed_path",
        label="the reed path",
        place="the marsh edge",
        image="The reeds leaned together like whispering aunties beside the path.",
        banquet_image="a clearing near the marsh",
        rhyme_line="Reed and seed, heed with speed.",
        tags={"marsh", "path"},
    ),
    "stone_bridge": Road(
        id="stone_bridge",
        label="the old stone bridge",
        place="the river bend",
        image="The bridge arched over dark water where minnows flashed like dropped coins.",
        banquet_image="a clearing beyond the river",
        rhyme_line="Stone and bone, cross not alone.",
        tags={"river", "bridge"},
    ),
    "pine_lane": Road(
        id="pine_lane",
        label="the pine lane",
        place="the hill below the pines",
        image="Tall pines clicked their cones together over the lane.",
        banquet_image="a green hollow under the hill",
        rhyme_line="Pine and twine, keep the meal fine.",
        tags={"hill", "pines"},
    ),
}

TREATS = {
    "smore": Treat(
        id="smore",
        label="smore",
        phrase="a round, gooey smore on a willow plate",
        texture="sticky with melted sweetness",
        precious="the special sweet promised for the center of the board",
        tags={"smore", "sweet"},
    ),
    "berry_tart": Treat(
        id="berry_tart",
        label="berry tart",
        phrase="a bright berry tart on a willow plate",
        texture="glossy with red juice",
        precious="the red jewel of the feast table",
        tags={"berries", "tart"},
    ),
    "honey_cake": Treat(
        id="honey_cake",
        label="honey cake",
        phrase="a soft honey cake wrapped in cloth",
        texture="golden and tender",
        precious="the golden pride of the village oven",
        tags={"honey", "cake"},
    ),
}

OMENS = {
    "rain": Omen(
        id="rain",
        label="rain cloud",
        risk="wet",
        sign="a gray seam sewing itself across the sky",
        sound="drip-drop",
        danger_line="a wet road can wet a feast",
        spoil_line="Rain slipped through the wrapping and turned the treat soggy",
        spread=2,
        tags={"rain", "wet"},
    ),
    "wind": Omen(
        id="wind",
        label="wind gust",
        risk="jostled",
        sign="the reeds bowing all one way and then springing back",
        sound="whoosh",
        danger_line="a wild wind can toss a feast",
        spoil_line="The gust jolted the plate and flung the sweet into the dust",
        spread=2,
        tags={"wind"},
    ),
    "goat": Omen(
        id="goat",
        label="goat on the lane",
        risk="snatched",
        sign="small crescent hoofprints on the soft earth",
        sound="clatter-clop",
        danger_line="a hungry goat can steal a feast",
        spoil_line="A nimble goat darted in and snatched a mouthful before the child could pull back",
        spread=3,
        tags={"goat", "animal"},
    ),
    "crows": Omen(
        id="crows",
        label="crows overhead",
        risk="snatched",
        sign="three black feathers spinning in a circle",
        sound="caw-caw",
        danger_line="sharp beaks can peck a feast",
        spoil_line="The crows swooped low and pecked the treat into crumbs",
        spread=2,
        tags={"bird", "animal"},
    ),
}

PROTECTIONS = {
    "wax_cloth": Protection(
        id="wax_cloth",
        label="wax cloth",
        phrase="a square of wax cloth",
        guards={"wet"},
        sense=3,
        success_line="It wrapped snugly around the plate with a soft crinkle.",
        fail_line="A dry cloth was not enough against a hard soaking.",
        qa_line="the wax cloth kept the rain from soaking through",
        tags={"cover", "rain"},
    ),
    "lidded_basket": Protection(
        id="lidded_basket",
        label="lidded basket",
        phrase="a lidded basket",
        guards={"wet", "jostled", "snatched"},
        sense=3,
        success_line="The lid clicked shut with a tidy tuck.",
        fail_line="The basket was left open, and trouble slipped right in.",
        qa_line="the lidded basket kept the treat tucked away",
        tags={"basket", "cover"},
    ),
    "walking_stick": Protection(
        id="walking_stick",
        label="walking stick",
        phrase="a smooth walking stick",
        guards={"jostled", "snatched"},
        sense=2,
        success_line="With it in hand, the child could steady steps and shoo noses and beaks away.",
        fail_line="A stick could not stop rain from seeping in.",
        qa_line="the walking stick helped keep steps steady and greedy animals back",
        tags={"stick", "animal"},
    ),
    "song": Protection(
        id="song",
        label="road song",
        phrase="an old road song",
        guards={"worry"},
        sense=1,
        success_line="The tune was lovely, but it could not cover a plate or block a beak.",
        fail_line="A song may cheer a traveler, but it does not shield supper.",
        qa_line="the song only made the child feel braver",
        tags={"song"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tova", "Nella", "Esme"]
BOY_NAMES = ["Ivo", "Tarin", "Milo", "Bram", "Oren", "Pavel"]
TRAITS = ["eager", "quick", "hopeful", "bright", "restless"]


KNOWLEDGE = {
    "smore": [
        ("What is a smore?",
         "A smore is a sweet treat, usually soft and sticky with melted sweetness. It is a special kind of snack for sharing.")
    ],
    "banquet": [
        ("What is a banquet?",
         "A banquet is a big feast where many people gather to eat together. It feels more special than an ordinary meal.")
    ],
    "foreshadowing": [
        ("What is foreshadowing in a story?",
         "Foreshadowing is when a story gives a small hint about something that will happen later. It helps the later event feel prepared instead of sudden.")
    ],
    "rain": [
        ("Why can rain spoil food?",
         "Rain can soak food and make it soggy or messy. Some foods need covering so they stay dry and clean.")
    ],
    "wind": [
        ("Why is strong wind hard for carrying food?",
         "Strong wind can shake your hands, tip a plate, or blow light things away. That is why people carry food more carefully when it is gusty.")
    ],
    "goat": [
        ("Why might a goat bother a picnic or feast?",
         "Goats are curious and often try to nibble things. If food is low and uncovered, a goat may try to steal it.")
    ],
    "crow": [
        ("Why do crows sometimes peck at food?",
         "Crows are smart birds and look for easy bites. If food is left open, they may swoop down to investigate it.")
    ],
    "basket": [
        ("Why is a basket with a lid useful?",
         "A lidded basket keeps things tucked inside and safer from rain, bumps, and grabbing animals. The lid gives extra protection while you travel.")
    ],
    "wax_cloth": [
        ("What does wax cloth do?",
         "Wax cloth is cloth treated so water slides off more easily. It helps keep things dry.")
    ],
    "walking_stick": [
        ("Why can a walking stick help on a path?",
         "A walking stick can help you keep your balance and feel where the ground is uneven. It can also help shoo an animal away without getting too close.")
    ],
}
KNOWLEDGE_ORDER = [
    "smore", "banquet", "foreshadowing", "rain", "wind", "goat", "crow",
    "basket", "wax_cloth", "walking_stick",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    omen = f["omen"]
    road = f["road"]
    treat = f["treat_cfg"]
    protection = f["protection"]
    if f["saved"]:
        return [
            f'Write a short folk tale for a 3-to-5-year-old that includes the words "smore" and "banquet", uses foreshadowing, and has sound effects like "{omen.sound}".',
            f"Tell a gentle village tale where {child.id} carries a {treat.label} along {road.label}, heeds an elder's warning, and reaches a moonlit banquet safely.",
            f"Write a rhyming folk-style story where a child uses {protection.label} to protect a feast treat after a warning sign hints at trouble.",
        ]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "smore" and "banquet", uses foreshadowing, and has sound effects like "{omen.sound}".',
        f"Tell a cautionary folk tale where {child.id} hurries along {road.label}, ignores an elder's warning about {omen.label}, and learns why careful travel matters.",
        f"Write a simple rhyming tale where a warning comes true and a child arrives at a banquet with a lesson instead of a perfect treat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    treat = f["treat_cfg"]
    road = f["road"]
    omen = f["omen"]
    protection = f["protection"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child carrying {treat.phrase} to a village banquet, and {elder.label_word} who gave the warning. The story follows whether that warning is believed in time."
        ),
        (
            f"What was {child.id} carrying, and where was {child.pronoun()} going?",
            f"{child.id} was carrying {treat.phrase} to a moonlit banquet. The treat mattered because it was meant to be part of the shared feast."
        ),
        (
            "What was the warning sign at the beginning?",
            f"The warning sign was {omen.sign}, and the road sounded like {omen.sound}. That was foreshadowing, because it hinted that the same danger would appear later."
        ),
    ]
    if outcome == "saved":
        qa.append((
            f"How did {child.id} keep the treat safe?",
            f"{child.id} listened to {elder.label_word} and used {protection.phrase}. {protection.qa_line.capitalize()}, so the danger never spoiled the food."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily at the banquet, with the treat arriving safely and the villagers cheering. The final feast image shows that care changed the journey."
        ))
    else:
        qa.append((
            f"Why was the treat spoiled?",
            f"The treat was spoiled because {child.id} hurried on after the warning and did not use a protection that could stop {omen.label}. When the omen came true, {omen.spoil_line.lower()}."
        ))
        qa.append((
            "What did the child learn?",
            f"{child.id} learned that a true warning should be heeded. The banquet was still kind, but the lost treat made the lesson feel real."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"smore", "banquet", "foreshadowing"}
    omen = world.facts["omen"]
    protection = world.facts["protection"]
    if omen.id == "rain":
        tags.add("rain")
    if omen.id == "wind":
        tags.add("wind")
    if omen.id == "goat":
        tags.add("goat")
    if omen.id == "crows":
        tags.add("crow")
    if protection.id == "lidded_basket":
        tags.add("basket")
    if protection.id == "wax_cloth":
        tags.add("wax_cloth")
    if protection.id == "walking_stick":
        tags.add("walking_stick")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        road="reed_path",
        treat="smore",
        omen="rain",
        protection="wax_cloth",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="eager",
        delay=0,
    ),
    StoryParams(
        road="stone_bridge",
        treat="berry_tart",
        omen="wind",
        protection="walking_stick",
        child_name="Ivo",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="quick",
        delay=0,
    ),
    StoryParams(
        road="pine_lane",
        treat="honey_cake",
        omen="goat",
        protection="lidded_basket",
        child_name="Nella",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="bright",
        delay=1,
    ),
    StoryParams(
        road="stone_bridge",
        treat="smore",
        omen="goat",
        protection="walking_stick",
        child_name="Bram",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="restless",
        delay=2,
    ),
    StoryParams(
        road="reed_path",
        treat="berry_tart",
        omen="crows",
        protection="lidded_basket",
        child_name="Esme",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="hopeful",
        delay=0,
    ),
]


def explain_rejection(omen: Omen, protection: Protection) -> str:
    if protection.sense < SENSE_MIN:
        return (
            f"(No story: {protection.label} is known in the world, but it is too weak to solve the problem "
            f"well enough for this domain. Pick a sturdier protection like wax_cloth, lidded_basket, or walking_stick.)"
        )
    return (
        f"(No story: {protection.label} does not reasonably protect against {omen.label}. "
        f"The fix should match the danger, not just sound pretty.)"
    )


def outcome_of(params: StoryParams) -> str:
    omen = OMENS[params.omen]
    protection = PROTECTIONS[params.protection]
    return "saved" if is_saved(omen, protection, params.delay) else "spoiled"


ASP_RULES = r"""
% Reasonableness gate
treat_at_risk(T, O) :- treat(T), omen(O), risk(O, wet).
treat_at_risk(T, O) :- treat(T), omen(O), risk(O, jostled).
treat_at_risk(T, O) :- treat(T), omen(O), risk(O, snatched).

sensible(P) :- protection(P), sense(P, S), sense_min(M), S >= M.
fits(O, P) :- omen(O), protection(P), risk(O, R), guards(P, R), sensible(P).
valid(Rd, T, O, P) :- road(Rd), treat(T), omen(O), protection(P), treat_at_risk(T, O), fits(O, P).

% Outcome model
peril(V) :- chosen_omen(O), spread(O, S), delay(D), V = S + D.
saved :- chosen_omen(O), chosen_protection(P), fits(O, P), sense(P, Pow), peril(V), Pow >= V.
outcome(saved) :- saved.
outcome(spoiled) :- not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROADS:
        lines.append(asp.fact("road", rid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for oid, omen in OMENS.items():
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("risk", oid, omen.risk))
        lines.append(asp.fact("spread", oid, omen.spread))
    for pid, prot in PROTECTIONS.items():
        lines.append(asp.fact("protection", pid))
        lines.append(asp.fact("sense", pid, prot.sense))
        for risk in sorted(prot.guards):
            lines.append(asp.fact("guards", pid, risk))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_omen", params.omen),
        asp.fact("chosen_protection", params.protection),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {pid for pid, prot in PROTECTIONS.items() if prot.sense >= SENSE_MIN}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible protections match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible protections: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "banquet" not in smoke.story or "smore" not in smoke.story:
            raise StoryError("smoke story missing expected story content")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child carries a feast treat to a folk-tale banquet while an omen hints at trouble."
    )
    ap.add_argument("--road", choices=ROADS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--protection", choices=PROTECTIONS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start trouble gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.protection and PROTECTIONS[args.protection].sense < SENSE_MIN:
        raise StoryError(explain_rejection(OMENS[args.omen] if args.omen else next(iter(OMENS.values())), PROTECTIONS[args.protection]))
    if args.omen and args.protection:
        if not protection_fits(OMENS[args.omen], PROTECTIONS[args.protection]):
            raise StoryError(explain_rejection(OMENS[args.omen], PROTECTIONS[args.protection]))

    combos = [
        combo for combo in valid_combos()
        if (args.road is None or combo[0] == args.road)
        and (args.treat is None or combo[1] == args.treat)
        and (args.omen is None or combo[2] == args.omen)
        and (args.protection is None or combo[3] == args.protection)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    road, treat, omen, protection = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    child_name = _pick_name(rng, child_gender)
    child_trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        road=road,
        treat=treat,
        omen=omen,
        protection=protection,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        child_trait=child_trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.road not in ROADS:
        raise StoryError(f"(Unknown road: {params.road})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.omen not in OMENS:
        raise StoryError(f"(Unknown omen: {params.omen})")
    if params.protection not in PROTECTIONS:
        raise StoryError(f"(Unknown protection: {params.protection})")

    world = tell(
        road=ROADS[params.road],
        treat=TREATS[params.treat],
        omen=OMENS[params.omen],
        protection=PROTECTIONS[params.protection],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
        delay=params.delay,
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
        print(f"sensible protections: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (road, treat, omen, protection) combos:\n")
        for road, treat, omen, protection in combos:
            print(f"  {road:12} {treat:10} {omen:8} {protection}")
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
            header = f"### {p.child_name}: {p.treat} on {p.road} ({p.omen}, {p.protection}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
