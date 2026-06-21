#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/insist_footed_squiggly_conflict_reconciliation_tall_tale.py
======================================================================================

A standalone storyworld for a child-sized tall tale: two children try to bring
back a runaway fair animal. One child insists on a proud, noisy plan; the other
predicts that chasing will only send the animal farther away. They argue, then
reconcile, and finally solve the problem together with a calm, fitting lure.

The seed asks for the words "insist", "footed", and "squiggly", plus Conflict
and Reconciliation, in a Tall Tale style. This world builds those directly into
its simulated state and prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/insist_footed_squiggly_conflict_reconciliation_tall_tale.py
    python storyworlds/worlds/gpt-5.4/insist_footed_squiggly_conflict_reconciliation_tall_tale.py --beast calf --lure apple_bucket
    python storyworlds/worlds/gpt-5.4/insist_footed_squiggly_conflict_reconciliation_tall_tale.py --beast goat --lure corn_pan
    python storyworlds/worlds/gpt-5.4/insist_footed_squiggly_conflict_reconciliation_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/insist_footed_squiggly_conflict_reconciliation_tall_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so results.py is three
# levels up in storyworlds/.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Beast:
    id: str
    label: str
    phrase: str
    stride: str
    likes: set[str] = field(default_factory=set)
    skittish: int = 1
    voice: str = ""
    trail: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    phrase: str
    smell: str
    calm_line: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"boaster", "peacemaker"}]

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


def _r_chase_spooks(world: World) -> list[str]:
    beast = world.get("beast")
    if beast.meters["chased"] < THRESHOLD:
        return []
    sig = ("chase_spooks", beast.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    skittish = int(beast.attrs.get("skittish", 1))
    beast.meters["spooked"] += 1
    beast.meters["distance"] += float(skittish)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__spook__"]


def _r_conflict(world: World) -> list[str]:
    a = world.get("boaster")
    b = world.get("peacemaker")
    if a.memes["defiance"] < THRESHOLD or b.memes["caution"] < THRESHOLD:
        return []
    sig = ("conflict", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    return ["__conflict__"]


def _r_reconcile(world: World) -> list[str]:
    a = world.get("boaster")
    b = world.get("peacemaker")
    if a.memes["sorry"] < THRESHOLD or b.memes["forgive"] < THRESHOLD:
        return []
    sig = ("reconcile", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    return ["__reconcile__"]


def _r_lure_works(world: World) -> list[str]:
    beast = world.get("beast")
    if beast.meters["lured"] < THRESHOLD or beast.meters["calm"] < THRESHOLD:
        return []
    sig = ("lure_works", beast.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if beast.attrs.get("lure_ok"):
        beast.meters["distance"] = 0.0
        beast.meters["returned"] += 1
        beast.meters["spooked"] = 0.0
        return ["__return__"]
    return []


CAUSAL_RULES = [
    Rule(name="chase_spooks", tag="physical", apply=_r_chase_spooks),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="lure_works", tag="physical", apply=_r_lure_works),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "fairground": Place(
        id="fairground",
        label="the county fairground",
        opening="The county fairground was so big that the wagons on one side looked like toy blocks from the other.",
        allows={"calf", "goat", "piglet"},
        tags={"fair"},
    ),
    "pasture": Place(
        id="pasture",
        label="the windy pasture",
        opening="The windy pasture rolled so wide that a shout could trot for a mile before it sat down.",
        allows={"calf", "goat"},
        tags={"pasture"},
    ),
    "melon_patch": Place(
        id="melon_patch",
        label="the melon patch behind the barn",
        opening="The melon patch behind the barn was so fat with vines that the rows looked like green rivers.",
        allows={"goat", "piglet"},
        tags={"farm"},
    ),
}

BEASTS = {
    "calf": Beast(
        id="calf",
        label="thunder-calf",
        phrase="a squiggly-tailed, four-footed thunder-calf",
        stride="Its hooves could kick up dust in curly ropes.",
        likes={"apple_bucket", "salt_biscuit"},
        skittish=2,
        voice="Moo-ooo!",
        trail="hoofprints that bent in a squiggly line",
        tags={"calf", "animal"},
    ),
    "goat": Beast(
        id="goat",
        label="hill goat",
        phrase="a beardy, four-footed hill goat",
        stride="It sprang as if each hoof had a tiny spring hidden under it.",
        likes={"clover_bundle", "salt_biscuit"},
        skittish=1,
        voice="Maa-aah!",
        trail="little sharp prints that stitched a squiggly path",
        tags={"goat", "animal"},
    ),
    "piglet": Beast(
        id="piglet",
        label="mud piglet",
        phrase="a rosy, four-footed mud piglet",
        stride="It scooted so fast that even the dust seemed late behind it.",
        likes={"corn_pan", "apple_bucket"},
        skittish=2,
        voice="Squee-ee!",
        trail="tiny hoof marks and a squiggly tail-sweep in the dirt",
        tags={"piglet", "animal"},
    ),
}

LURES = {
    "apple_bucket": Lure(
        id="apple_bucket",
        label="bucket of apples",
        phrase="a sloshing bucket of red apples",
        smell="sweet enough to pull a nose around from halfway to tomorrow",
        calm_line='Come easy now. There is plenty to share.',
        tags={"apples", "food"},
    ),
    "salt_biscuit": Lure(
        id="salt_biscuit",
        label="salt biscuit",
        phrase="a big salt biscuit on a flat palm",
        smell="warm and crumbly",
        calm_line='Slow feet, soft voice, and one bite for a brave animal.',
        tags={"biscuit", "food"},
    ),
    "clover_bundle": Lure(
        id="clover_bundle",
        label="bundle of clover",
        phrase="a cool green bundle of clover",
        smell="fresh as morning",
        calm_line='Look here, little jumper. Supper has found you.',
        tags={"clover", "food"},
    ),
    "corn_pan": Lure(
        id="corn_pan",
        label="pan of corn",
        phrase="a round pan rattling with yellow corn",
        smell="toasty and cheerful",
        calm_line='No hurry now. The corn is waiting right here.',
        tags={"corn", "food"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["bold", "careful", "steady", "cheerful", "thoughtful", "patient"]


@dataclass
class StoryParams:
    place: str
    beast: str
    lure: str
    boaster_name: str
    boaster_gender: str
    peacemaker_name: str
    peacemaker_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def place_allows(place: Place, beast: Beast) -> bool:
    return beast.id in place.allows


def lure_fits(beast: Beast, lure: Lure) -> bool:
    return lure.id in beast.likes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for beast_id, beast in BEASTS.items():
            if not place_allows(place, beast):
                continue
            for lure_id, lure in LURES.items():
                if lure_fits(beast, lure):
                    combos.append((place_id, beast_id, lure_id))
    return combos


def explain_rejection(place: Place, beast: Beast, lure: Lure) -> str:
    if not place_allows(place, beast):
        return (
            f"(No story: {beast.label} does not belong in {place.label} in this world. "
            f"Pick a place that plausibly holds that animal.)"
        )
    if not lure_fits(beast, lure):
        likes = ", ".join(sorted(l.label for l in LURES.values() if l.id in beast.likes))
        return (
            f"(No story: a {beast.label} would not calmly follow {lure.label}. "
            f"Use a fitting lure such as {likes}.)"
        )
    return "(No story: that combination does not fit this world.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def predict_chase(world: World) -> dict:
    sim = world.copy()
    beast = sim.get("beast")
    beast.meters["chased"] += 1
    propagate(sim, narrate=False)
    return {
        "distance": beast.meters["distance"],
        "spooked": beast.meters["spooked"],
    }


def introduce(world: World, place: Place, a: Entity, b: Entity, beast: Beast, adult: Entity) -> None:
    world.say(place.opening)
    world.say(
        f"That was the very morning when {a.id} and {b.id} came to help {adult.label_word} Bell at {place.label}, "
        f"and the proudest creature there was {beast.phrase}."
    )
    world.say(
        f"The children swore the beast was so lively that its shadow had to trot to keep up. {beast.stride}"
    )


def runaway(world: World, beast: Beast) -> None:
    animal = world.get("beast")
    animal.meters["distance"] = 1.0
    world.say(
        f"Then the gate clicked, the rope slipped, and away went the {beast.label}. "
        f'It cried "{beast.voice}" and left {beast.trail} all across the dust.'
    )


def boast_and_insist(world: World, a: Entity, beast: Beast) -> None:
    a.memes["pride"] += 1
    a.memes["defiance"] += 1
    world.say(
        f'"I insist we run after that {beast.label} right this instant," said {a.id}. '
        f'"My feet are faster than a tumbleweed on market day."'
    )


def warn(world: World, a: Entity, b: Entity, beast: Beast) -> None:
    b.memes["caution"] += 1
    pred = predict_chase(world)
    world.facts["predicted_distance"] = pred["distance"]
    world.facts["predicted_spooked"] = pred["spooked"]
    farther = "farther" if pred["distance"] > 1 else "no farther"
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "If you thunder after a four-footed creature, '
        f'it will bolt {farther}. We need quiet hands, not flying heels."'
    )


def chase(world: World, a: Entity, b: Entity, beast_cfg: Beast) -> None:
    beast = world.get("beast")
    beast.meters["chased"] += 1
    propagate(world, narrate=False)
    dist = int(beast.meters["distance"])
    a.memes["worry"] += 1
    world.say(
        f"But {a.id} dashed off anyway, boots pounding so hard that the boards of the nearest stall sounded like a drum. "
        f"The {beast_cfg.label} took one look, sprang away, and by the count of {dist} fence posts it was farther than before."
    )
    world.say(
        f"{b.id} hurried after {a.id}, and for a moment the two of them looked cross enough to bend the air."
    )


def conflict(world: World, a: Entity, b: Entity) -> None:
    propagate(world, narrate=False)
    if a.memes["conflict"] >= THRESHOLD or b.memes["conflict"] >= THRESHOLD:
        world.say(
            f'"You never listen when you get excited," said {b.id}. '
            f'"And you always think I am wrong," said {a.id}.'
        )


def realization(world: World, a: Entity, b: Entity, beast_cfg: Beast) -> None:
    world.say(
        f"Just then the children saw the {beast_cfg.label} pause near a trough and glance back with wide, worried eyes. "
        f"It did not look mean. It looked scared."
    )
    a.memes["pride"] = 0.0
    a.memes["sorry"] += 1
    b.memes["forgive"] += 1
    world.say(
        f'{a.id} let out a slow breath. "I made it worse. I was so busy trying to be the biggest helper in the county that I forgot to be a gentle one."'
    )


def reconcile(world: World, a: Entity, b: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f'{b.id} touched {a.id}\'s sleeve. "We can still fix it together," {b.pronoun()} said.'
    )
    world.say(
        f'{a.id} nodded. "All right. No more stomping. We will use your plan, and I will help."'
    )


def lure_plan(world: World, a: Entity, b: Entity, lure: Lure, beast_cfg: Beast) -> None:
    beast = world.get("beast")
    beast.meters["calm"] += 1
    beast.meters["lured"] += 1
    beast.attrs["lure_ok"] = True
    world.say(
        f"So {b.id} lifted {lure.phrase}, which smelled {lure.smell}, while {a.id} walked beside {b.pronoun('object')} as quietly as a cloud in socks."
    )
    world.say(
        f'{b.id} called, "{lure.calm_line}"'
    )
    propagate(world, narrate=False)
    if beast.meters["returned"] >= THRESHOLD:
        world.say(
            f"The {beast_cfg.label} stopped, sniffed, turned around, and came back in a soft zigzag that matched its own squiggly trail."
        )


def return_home(world: World, a: Entity, b: Entity, adult: Entity, beast_cfg: Beast, lure: Lure) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"{a.id} took the rope gently, {b.id} held out the {lure.label}, and together they led the {beast_cfg.label} back to the pen."
    )
    world.say(
        f'{adult.label_word.capitalize()} Bell laughed with relief. "That is how big helpers do big jobs," {adult.pronoun()} said. "Fast feet are fine, but kind feet are better."'
    )


def ending(world: World, a: Entity, b: Entity, beast_cfg: Beast, place: Place) -> None:
    world.say(
        f"After that, whenever the story was told at {place.label}, it grew another inch. Folks said the children had chased down a storm on four feet and talked it back with one calm voice."
    )
    world.say(
        f"But {a.id} and {b.id} knew the truest part: they had quarreled, said sorry, and stood shoulder to shoulder while the {beast_cfg.label} munched peacefully behind them."
    )


def tell(
    place: Place,
    beast_cfg: Beast,
    lure: Lure,
    boaster_name: str = "Tom",
    boaster_gender: str = "boy",
    peacemaker_name: str = "Lily",
    peacemaker_gender: str = "girl",
    adult_type: str = "mother",
    trait: str = "steady",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=boaster_name,
            kind="character",
            type=boaster_gender,
            role="boaster",
            traits=["eager", trait],
        )
    )
    b = world.add(
        Entity(
            id=peacemaker_name,
            kind="character",
            type=peacemaker_gender,
            role="peacemaker",
            traits=["calm", "thoughtful"],
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the fair keeper",
        )
    )
    beast = world.add(
        Entity(
            id="beast",
            kind="thing",
            type=beast_cfg.id,
            label=beast_cfg.label,
            phrase=beast_cfg.phrase,
            tags=set(beast_cfg.tags),
            attrs={"skittish": beast_cfg.skittish, "lure_ok": False},
        )
    )

    introduce(world, place, a, b, beast_cfg, adult)
    world.para()
    runaway(world, beast_cfg)
    boast_and_insist(world, a, beast_cfg)
    warn(world, a, b, beast_cfg)
    chase(world, a, b, beast_cfg)
    conflict(world, a, b)
    world.para()
    realization(world, a, b, beast_cfg)
    reconcile(world, a, b)
    lure_plan(world, a, b, lure, beast_cfg)
    return_home(world, a, b, adult, beast_cfg, lure)
    world.para()
    ending(world, a, b, beast_cfg, place)

    world.facts.update(
        place=place,
        beast_cfg=beast_cfg,
        lure=lure,
        boaster=a,
        peacemaker=b,
        adult=adult,
        beast=beast,
        conflict_happened=True,
        reconciled=(a.memes["conflict"] < THRESHOLD and b.memes["conflict"] < THRESHOLD),
        returned=(beast.meters["returned"] >= THRESHOLD),
    )
    return world


KNOWLEDGE = {
    "animal": [
        (
            "Why should you move slowly around a scared animal?",
            "A scared animal may run farther if people rush at it. Slow feet and soft voices help it feel safe again.",
        )
    ],
    "apples": [
        (
            "Why might apples help lead a calf?",
            "Many calves like sweet food and will follow a smell they know. Food works better than shouting when you want an animal to come calmly.",
        )
    ],
    "clover": [
        (
            "Why would a goat like clover?",
            "Clover is a fresh plant that many goats enjoy nibbling. A familiar snack can help a goat stop jumping and pay attention.",
        )
    ],
    "corn": [
        (
            "Why might a piglet follow corn?",
            "Corn smells tasty to many piglets, so it can persuade them to come closer. A food lure is gentler than a chase.",
        )
    ],
    "biscuit": [
        (
            "What is a salt biscuit in this story world?",
            "It is a sturdy, salty treat used to tempt an animal to come near. The idea is not the biscuit itself, but offering something the animal already likes.",
        )
    ],
    "fair": [
        (
            "What happens at a county fair?",
            "People bring animals, food, and games to one busy place. There can be many sounds and smells, so animals may need careful handling.",
        )
    ],
    "pasture": [
        (
            "What is a pasture?",
            "A pasture is a grassy field where animals can walk and eat. It gives them room, so people often keep hoofed animals there.",
        )
    ],
    "farm": [
        (
            "What grows in a melon patch?",
            "Melons grow on long vines that spread over the ground. A patch can be leafy and twisty, with rows that are easy to hide in.",
        )
    ],
    "sorry": [
        (
            "Why does saying sorry help after an argument?",
            "A real apology shows that someone sees the hurt they caused. It opens the door for both people to work together again.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful when solving a problem?",
            "Two people can combine different strengths, like speed and patience. Working together often solves a problem more safely than one person acting alone.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fair", "pasture", "farm", "animal", "apples", "clover", "corn", "biscuit", "sorry", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    beast_cfg = f["beast_cfg"]
    lure = f["lure"]
    a = f["boaster"]
    b = f["peacemaker"]
    return [
        (
            f'Write a short tall tale for a 3-to-5-year-old that includes the words '
            f'"insist", "footed", and "squiggly", and centers on conflict and reconciliation.'
        ),
        (
            f"Tell a gentle tall tale where {a.id} insists on chasing a runaway {beast_cfg.label} at {place.label}, "
            f"argues with {b.id}, then says sorry and helps bring it back with {lure.phrase}."
        ),
        (
            f"Write a child-facing story in a big, exaggerated voice where two children quarrel over how to catch "
            f"a four-footed animal, then make up and solve the problem together."
        ),
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["boaster"]
    b = f["peacemaker"]
    adult = f["adult"]
    beast_cfg = f["beast_cfg"]
    lure = f["lure"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, and a runaway {beast_cfg.label} at {place.label}. A grown-up fair keeper is nearby, but the children are the ones who must learn how to help.",
        ),
        (
            f"What problem started the story?",
            f"The {beast_cfg.label} slipped away and ran from its pen. That set the whole tall tale in motion, because the children had to decide how to get it back.",
        ),
        (
            f"What did {a.id} insist on doing first?",
            f"{a.id} insisted on running after the animal right away. {a.pronoun('subject').capitalize()} thought fast feet would solve everything, but the chase only frightened the creature more.",
        ),
        (
            f"Why did {b.id} disagree?",
            f"{b.id} believed that pounding after a scared four-footed animal would send it farther away. {b.pronoun('subject').capitalize()} wanted a calm plan that matched what the animal liked.",
        ),
        (
            "How did the conflict turn into reconciliation?",
            f"When the children saw the {beast_cfg.label} looking scared, {a.id} admitted the chase had made things worse. Then {b.id} forgave {a.pronoun('object')}, and they agreed to help together instead of arguing.",
        ),
        (
            f"How did they bring the animal back?",
            f"They used {lure.phrase} and a soft voice to lure the animal home. That worked because the food was familiar, and the children had stopped acting noisy and cross.",
        ),
        (
            "How did the story end?",
            f"It ended with the children side by side, the animal safely back, and their friendship mended. The last image proves the change: the quarrel is over, and the once-runaway beast is munching peacefully behind them.",
        ),
    ]
    if f.get("returned"):
        qa.append(
            (
                f"What did the fair keeper think at the end?",
                f"{adult.label_word.capitalize()} Bell was relieved and proud. {adult.pronoun('subject').capitalize()} praised the children for using kind feet and teamwork instead of noise.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["place"].tags)
    tags |= set(f["beast_cfg"].tags)
    tags |= set(f["lure"].tags)
    tags |= {"sorry", "teamwork"}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fairground",
        beast="calf",
        lure="apple_bucket",
        boaster_name="Tom",
        boaster_gender="boy",
        peacemaker_name="Lily",
        peacemaker_gender="girl",
        adult="mother",
        trait="bold",
    ),
    StoryParams(
        place="pasture",
        beast="goat",
        lure="clover_bundle",
        boaster_name="Mia",
        boaster_gender="girl",
        peacemaker_name="Ben",
        peacemaker_gender="boy",
        adult="father",
        trait="cheerful",
    ),
    StoryParams(
        place="melon_patch",
        beast="piglet",
        lure="corn_pan",
        boaster_name="Sam",
        boaster_gender="boy",
        peacemaker_name="Zoe",
        peacemaker_gender="girl",
        adult="mother",
        trait="steady",
    ),
    StoryParams(
        place="fairground",
        beast="goat",
        lure="salt_biscuit",
        boaster_name="Ava",
        boaster_gender="girl",
        peacemaker_name="Finn",
        peacemaker_gender="boy",
        adult="father",
        trait="thoughtful",
    ),
    StoryParams(
        place="pasture",
        beast="calf",
        lure="salt_biscuit",
        boaster_name="Leo",
        boaster_gender="boy",
        peacemaker_name="Nora",
        peacemaker_gender="girl",
        adult="mother",
        trait="patient",
    ),
]


ASP_RULES = r"""
fits_place(P, B) :- place(P), beast(B), allows(P, B).
fits_lure(B, L)  :- beast(B), lure(L), likes(B, L).
valid(P, B, L)   :- fits_place(P, B), fits_lure(B, L).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for beast_id in sorted(place.allows):
            lines.append(asp.fact("allows", place_id, beast_id))
    for beast_id, beast in BEASTS.items():
        lines.append(asp.fact("beast", beast_id))
        for lure_id in sorted(beast.likes):
            lines.append(asp.fact("likes", beast_id, lure_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        if "insist" not in smoke.story.lower():
            raise StoryError("smoke story missing required seed word 'insist'")
        print("OK: smoke generation succeeded on curated sample.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        parser = build_parser()
        for seed in range(10):
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError(f"empty story for seed {seed}")
        print("OK: random generation smoke-tested on 10 seeds.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"RANDOM SMOKE FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a runaway four-footed fair beast, an argument, and a reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--beast", choices=BEASTS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by ASP")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.beast:
        place = PLACES[args.place]
        beast = BEASTS[args.beast]
        if not place_allows(place, beast):
            lure = LURES[args.lure] if args.lure else next(iter(LURES.values()))
            raise StoryError(explain_rejection(place, beast, lure))
    if args.beast and args.lure:
        beast = BEASTS[args.beast]
        lure = LURES[args.lure]
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        if not lure_fits(beast, lure):
            raise StoryError(explain_rejection(place, beast, lure))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.beast is None or combo[1] == args.beast)
        and (args.lure is None or combo[2] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, beast_id, lure_id = rng.choice(sorted(combos))
    boaster_gender = rng.choice(["girl", "boy"])
    peacemaker_gender = rng.choice(["girl", "boy"])
    boaster_name = _pick_name(rng, boaster_gender)
    peacemaker_name = _pick_name(rng, peacemaker_gender, avoid=boaster_name)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        beast=beast_id,
        lure=lure_id,
        boaster_name=boaster_name,
        boaster_gender=boaster_gender,
        peacemaker_name=peacemaker_name,
        peacemaker_gender=peacemaker_gender,
        adult=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.beast not in BEASTS:
        raise StoryError(f"(Unknown beast: {params.beast})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    place = PLACES[params.place]
    beast = BEASTS[params.beast]
    lure = LURES[params.lure]
    if not place_allows(place, beast) or not lure_fits(beast, lure):
        raise StoryError(explain_rejection(place, beast, lure))

    world = tell(
        place=place,
        beast_cfg=beast,
        lure=lure,
        boaster_name=params.boaster_name,
        boaster_gender=params.boaster_gender,
        peacemaker_name=params.peacemaker_name,
        peacemaker_gender=params.peacemaker_gender,
        adult_type=params.adult,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, beast, lure) combos:\n")
        for place_id, beast_id, lure_id in combos:
            print(f"  {place_id:12} {beast_id:8} {lure_id}")
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
            header = f"### {p.boaster_name} & {p.peacemaker_name}: {p.beast} at {p.place} with {p.lure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
