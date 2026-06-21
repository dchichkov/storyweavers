#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py
=================================================================================

A standalone story world for a gentle animal story about curiosity leading to
kindness. A small animal notices a frightened little garden creature trembling
near the compost, learns what it needs, and helps it get home in a safe way.

This world models a tiny garden domain with typed entities, physical meters, and
emotional memes. The story is driven by state: a small creature is exposed and
dry, a curious helper investigates, a friend joins in, and together they use a
simple curved shelter or carrier to return the creature to the damp compost that
keeps it safe.

Run it
------
    python storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py
    python storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py --foundling worm
    python storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py --method leaf_sled
    python storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py --foundling butterfly
    python storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tremble_arc_compost_curiosity_kindness_animal_story.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CARE_MIN = 2


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
    can_carry: bool = False
    bends_into_arc: bool = False
    keeps_damp: bool = False
    belongs_in_compost: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "buck", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    opening: str
    compost_phrase: str
    path_phrase: str
    sky_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalKind:
    id: str
    noun: str
    adjective: str
    step: str
    home_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Foundling:
    id: str
    label: str
    phrase: str
    movement: str
    fear_sound: str
    needs_damp: bool
    belongs_in_compost: bool
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    action: str
    makes_arc: bool
    keeps_damp: bool
    power: int
    care: int
    qa_text: str
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


def _r_exposure(world: World) -> list[str]:
    out: list[str] = []
    foundling = world.get("foundling")
    if foundling.meters["exposed"] < THRESHOLD:
        return out
    sig = ("exposure", foundling.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if foundling.meters["damp"] < THRESHOLD:
        foundling.meters["wobble"] += 1
        foundling.memes["fear"] += 1
        out.append("__tremble__")
    for eid in ("helper", "friend"):
        if eid in world.entities:
            world.get(eid).memes["concern"] += 1
    return out


def _r_home(world: World) -> list[str]:
    out: list[str] = []
    foundling = world.get("foundling")
    if foundling.meters["home"] < THRESHOLD:
        return out
    sig = ("home", foundling.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    foundling.meters["exposed"] = 0.0
    foundling.memes["fear"] = 0.0
    foundling.meters["safe"] += 1
    for eid in ("helper", "friend"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["kindness"] += 1
    out.append("__safe__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="exposure", tag="physical", apply=_r_exposure),
    Rule(name="home", tag="physical", apply=_r_home),
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


def hazard_at_risk(foundling: Foundling) -> bool:
    return foundling.belongs_in_compost and foundling.needs_damp


def sensible_methods(foundling: Foundling) -> list[Method]:
    return [
        m for m in METHODS.values()
        if m.care >= CARE_MIN and m.power >= foundling.weight and m.keeps_damp
    ]


def method_works(method: Method, foundling: Foundling) -> bool:
    return method.power >= foundling.weight and method.keeps_damp and method.care >= CARE_MIN


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    foundling = sim.get("foundling")
    foundling.meters["exposed"] += 1
    foundling.meters["damp"] = 0.0
    propagate(sim, narrate=False)
    return {
        "tremble": foundling.meters["wobble"] >= THRESHOLD,
        "fear": foundling.memes["fear"],
    }


def introduce(world: World, helper: Entity, friend: Entity, animal: AnimalKind) -> None:
    helper.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"In {world.place.label}, a {animal.adjective} {animal.noun} named {helper.id} "
        f"liked to notice small things. {world.place.opening}"
    )
    world.say(
        f"{helper.id} and {friend.id} were {animal.step} past {world.place.compost_phrase} "
        f"when something tiny moved beside {world.place.path_phrase}."
    )


def discover(world: World, helper: Entity, friend: Entity, foundling: Entity, cfg: Foundling) -> None:
    foundling.meters["exposed"] += 1
    foundling.meters["damp"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} tipped {helper.pronoun('possessive')} head and came closer. "
        f"There, in a patch of dry crumbs, lay {cfg.phrase}."
    )
    world.say(
        f'"What are you doing all alone?" {helper.id} whispered.'
    )
    if foundling.meters["wobble"] >= THRESHOLD:
        world.say(
            f"The little {cfg.label} gave {cfg.fear_sound}, and {helper.id} saw it tremble."
        )
    world.facts["noticed_tremble"] = foundling.meters["wobble"] >= THRESHOLD


def ask_and_learn(world: World, helper: Entity, friend: Entity, foundling: Entity, cfg: Foundling) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_fear"] = pred["fear"]
    helper.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} peered down too. "
        f'"Maybe it came from the compost," {friend.pronoun()} said.'
    )
    world.say(
        f"{helper.id} sniffed the warm peelings and leaves. "
        f"{helper.pronoun().capitalize()} was curious, but not the poking kind of curious. "
        f"{helper.pronoun().capitalize()} wanted to understand what would help."
    )
    if pred["tremble"]:
        world.say(
            f'"If it stays out here in the dry air, it will only shake more," {helper.id} said softly.'
        )


def offer_method(world: World, helper: Entity, friend: Entity, method: Method) -> None:
    helper.memes["plan"] += 1
    if method.makes_arc:
        world.say(
            f"{friend.id} bent {method.phrase} into a gentle arc above the little creature, "
            f"so the bright patch no longer felt so bare."
        )
    else:
        world.say(
            f"{friend.id} slid {method.phrase} close, making a soft path back toward the dark, crumbly heap."
        )
    world.say(
        f'"Let us be careful," {helper.id} said. "We can {method.action}."'
    )


def rescue(world: World, helper: Entity, friend: Entity, foundling: Entity, cfg: Foundling, method: Method) -> None:
    foundling.meters["damp"] += 1
    foundling.meters["moved"] += 1
    foundling.meters["home"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {method.action}, carrying it only as much as needed. "
        f"Soon the little {cfg.label} reached {world.place.compost_phrase} again."
    )
    world.say(
        f"It {cfg.movement} under an apple peel and a curl of lettuce, where the air was cool and damp."
    )


def gentle_failure(world: World, helper: Entity, friend: Entity, foundling: Entity, cfg: Foundling, method: Method) -> None:
    foundling.meters["damp"] += 0.0
    foundling.meters["moved"] += 1
    foundling.meters["home"] = 0.0
    foundling.memes["fear"] += 1
    helper.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"They tried to {method.action}, but the little {cfg.label} kept slipping and curling into itself."
    )
    world.say(
        f'"This way is not kind enough," {helper.id} said. The dry trip was still too much for such a tiny garden neighbor.'
    )


def ending(world: World, helper: Entity, friend: Entity, animal: AnimalKind, foundling: Foundling, method: Method, worked: bool) -> None:
    if worked:
        helper.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(
            f"{helper.id} and {friend.id} sat back on their haunches and listened. "
            f"Now the compost gave a soft, busy rustle instead of a frightened silence."
        )
        if method.makes_arc:
            world.say(
                f"Over the heap, the curved little shelter still held its arc for a moment before settling flat again."
            )
        world.say(
            f'"I wanted to know what that tiny sound meant," said {helper.id}. '
            f'"Now I know curiosity can turn into kindness."'
        )
    else:
        world.say(
            f"So the two friends hurried to find a softer, damper leaf instead. "
            f"They had learned that being kind meant changing the plan when the first plan was too rough."
        )
    world.facts["ending_image"] = "busy compost rustle" if worked else "friends seeking a softer leaf"


PLACES = {
    "garden": Place(
        id="garden",
        label="the kitchen garden",
        opening="Beans climbed their poles, and the afternoon light made the bean leaves shine.",
        compost_phrase="the old compost mound under the pear tree",
        path_phrase="the dusty stone path",
        sky_phrase="the wide blue sky",
        tags={"garden", "compost"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard edge",
        opening="Wind moved through the grass, and fallen fruit made sweet smells under the trees.",
        compost_phrase="the orchard compost heap behind the crates",
        path_phrase="the warm dirt track",
        sky_phrase="the pale gold sky",
        tags={"orchard", "compost"},
    ),
    "yard": Place(
        id="yard",
        label="the back yard",
        opening="Sun striped the fence, and marigolds nodded by the gate.",
        compost_phrase="the little compost bin by the shed",
        path_phrase="the pebbly garden path",
        sky_phrase="the bright sky",
        tags={"yard", "compost"},
    ),
}

ANIMALS = {
    "rabbit": AnimalKind(
        id="rabbit",
        noun="rabbit",
        adjective="curious",
        step="hopping",
        home_phrase="under the rosemary bush",
        tags={"rabbit"},
    ),
    "mouse": AnimalKind(
        id="mouse",
        noun="mouse",
        adjective="small",
        step="padding",
        home_phrase="beside the brick wall",
        tags={"mouse"},
    ),
    "squirrel": AnimalKind(
        id="squirrel",
        noun="squirrel",
        adjective="quick",
        step="scampering",
        home_phrase="near the plum stump",
        tags={"squirrel"},
    ),
}

FOUNDLINGS = {
    "worm": Foundling(
        id="worm",
        label="worm",
        phrase="a pink earthworm, half-curled and dusty",
        movement="slid",
        fear_sound="the faintest wriggle",
        needs_damp=True,
        belongs_in_compost=True,
        weight=1,
        tags={"worm", "compost"},
    ),
    "pill_bug": Foundling(
        id="pill_bug",
        label="pill bug",
        phrase="a little pill bug rolled almost into a bead",
        movement="tucked itself",
        fear_sound="a tiny scrape",
        needs_damp=True,
        belongs_in_compost=True,
        weight=1,
        tags={"pill_bug", "compost"},
    ),
    "beetle_larva": Foundling(
        id="beetle_larva",
        label="grub",
        phrase="a pale little grub blinking in the light",
        movement="wriggled",
        fear_sound="a soft squirm",
        needs_damp=True,
        belongs_in_compost=True,
        weight=2,
        tags={"grub", "compost"},
    ),
    "butterfly": Foundling(
        id="butterfly",
        label="butterfly",
        phrase="a butterfly with dusty yellow wings",
        movement="fluttered",
        fear_sound="a papery flick",
        needs_damp=False,
        belongs_in_compost=False,
        weight=1,
        tags={"butterfly"},
    ),
}

METHODS = {
    "leaf_sled": Method(
        id="leaf_sled",
        label="leaf sled",
        phrase="a curled dock leaf",
        action="slide the little one home on the cool leaf sled",
        makes_arc=True,
        keeps_damp=True,
        power=2,
        care=3,
        qa_text="They slid it home on a cool curled leaf, which kept the trip soft and damp.",
        tags={"leaf", "kindness"},
    ),
    "moss_cradle": Method(
        id="moss_cradle",
        label="moss cradle",
        phrase="a cushion of moss on a bark chip",
        action="nestle the little one in the moss cradle and carry it back",
        makes_arc=True,
        keeps_damp=True,
        power=3,
        care=3,
        qa_text="They nestled it in moss on a bark chip, so it stayed soft, shaded, and damp.",
        tags={"moss", "kindness"},
    ),
    "twig_nudge": Method(
        id="twig_nudge",
        label="twig nudge",
        phrase="a thin dry twig",
        action="nudge the little one along with the twig",
        makes_arc=False,
        keeps_damp=False,
        power=1,
        care=1,
        qa_text="They only nudged it with a dry twig, which was too rough and too dry to be kind enough.",
        tags={"twig"},
    ),
}

GIRL_NAMES = ["Pip", "Mimi", "Tansy", "Nell", "Daisy", "Poppy"]
BOY_NAMES = ["Moss", "Bramble", "Nico", "Ash", "Rowan", "Juniper"]


@dataclass
class StoryParams:
    place: str
    animal: str
    helper_name: str
    friend_name: str
    foundling: str
    method: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        animal="rabbit",
        helper_name="Pip",
        friend_name="Moss",
        foundling="worm",
        method="leaf_sled",
    ),
    StoryParams(
        place="orchard",
        animal="mouse",
        helper_name="Mimi",
        friend_name="Ash",
        foundling="pill_bug",
        method="moss_cradle",
    ),
    StoryParams(
        place="yard",
        animal="squirrel",
        helper_name="Nell",
        friend_name="Rowan",
        foundling="beetle_larva",
        method="moss_cradle",
    ),
    StoryParams(
        place="garden",
        animal="rabbit",
        helper_name="Daisy",
        friend_name="Juniper",
        foundling="worm",
        method="twig_nudge",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for foundling_id, foundling in FOUNDLINGS.items():
            if not hazard_at_risk(foundling):
                continue
            for method in sensible_methods(foundling):
                combos.append((place_id, foundling_id, method.id))
    return combos


def explain_rejection(foundling: Foundling) -> str:
    if not foundling.belongs_in_compost:
        return (
            f"(No story: a {foundling.label} does not belong in compost here, "
            f"so returning it to the compost would not be a kind or sensible fix.)"
        )
    if not foundling.needs_damp:
        return (
            f"(No story: a {foundling.label} does not need the damp compost conditions "
            f"that drive this story's problem and solution.)"
        )
    return "(No story: this creature does not fit the compost-rescue domain.)"


def explain_method(method: Method, foundling: Foundling) -> str:
    return (
        f"(Refusing method '{method.id}': it is not gentle enough for a {foundling.label}. "
        f"This world prefers a damp, careful rescue like "
        f"{', '.join(sorted(m.id for m in sensible_methods(foundling)))}.)"
    )


def outcome_of(params: StoryParams) -> str:
    foundling = FOUNDLINGS[params.foundling]
    method = METHODS[params.method]
    return "rescued" if method_works(method, foundling) else "retry"


def tell(
    place: Place,
    animal: AnimalKind,
    helper_name: str,
    friend_name: str,
    foundling_cfg: Foundling,
    method: Method,
) -> World:
    world = World(place)
    helper = world.add(Entity(id=helper_name, kind="character", type=animal.noun, role="helper"))
    friend = world.add(Entity(id=friend_name, kind="character", type=animal.noun, role="friend"))
    foundling = world.add(
        Entity(
            id="foundling",
            kind="character",
            type=foundling_cfg.label,
            label=foundling_cfg.label,
            role="foundling",
            belongs_in_compost=foundling_cfg.belongs_in_compost,
            tags=set(foundling_cfg.tags),
        )
    )

    introduce(world, helper, friend, animal)
    discover(world, helper, friend, foundling, foundling_cfg)

    world.para()
    ask_and_learn(world, helper, friend, foundling, foundling_cfg)
    offer_method(world, helper, friend, method)

    worked = method_works(method, foundling_cfg)
    world.para()
    if worked:
        rescue(world, helper, friend, foundling, foundling_cfg, method)
    else:
        gentle_failure(world, helper, friend, foundling, foundling_cfg, method)

    world.para()
    ending(world, helper, friend, animal, foundling_cfg, method, worked)

    world.facts.update(
        place=place,
        animal=animal,
        helper=helper,
        friend=friend,
        foundling=foundling,
        foundling_cfg=foundling_cfg,
        method=method,
        outcome="rescued" if worked else "retry",
        tremble=foundling.meters["wobble"] >= THRESHOLD,
        rescued=foundling.meters["safe"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "compost": [
        (
            "What is compost?",
            "Compost is a soft pile of old peels, leaves, and plant bits that slowly break down. It stays dark and damp, and many tiny garden creatures like living in it.",
        )
    ],
    "worm": [
        (
            "Why do worms like damp places?",
            "Worms do best in damp places because dry air can make their bodies lose moisture. Soft, wet soil or compost helps keep them safe.",
        )
    ],
    "pill_bug": [
        (
            "Why do pill bugs hide in damp places?",
            "Pill bugs like cool, damp places under leaves and in compost. Those places help them stay comfortable and hidden.",
        )
    ],
    "grub": [
        (
            "What is a grub?",
            "A grub is the soft young form of some beetles. It often lives under soil or in rotting plant matter where it is dark and damp.",
        )
    ],
    "leaf": [
        (
            "How can a leaf help a tiny animal?",
            "A broad leaf can make shade and hold a little coolness. That can help carry a tiny creature gently without squeezing it.",
        )
    ],
    "moss": [
        (
            "Why is moss soft and useful?",
            "Moss holds a little water and feels springy. That makes it a gentle place for a very small creature to rest.",
        )
    ],
    "kindness": [
        (
            "What does kindness look like in a garden?",
            "Kindness means noticing what another living thing needs and acting gently. Sometimes it means slowing down and helping even a tiny creature.",
        )
    ],
    "curiosity": [
        (
            "What is good curiosity?",
            "Good curiosity means wanting to understand something carefully. It asks, 'What is happening, and what would help?' instead of grabbing or poking.",
        )
    ],
}
KNOWLEDGE_ORDER = ["compost", "worm", "pill_bug", "grub", "leaf", "moss", "curiosity", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    helper = f["helper"]
    foundling = f["foundling_cfg"]
    return [
        'Write a gentle animal story for a 3-to-5-year-old that includes the words "tremble", "arc", and "compost".',
        f"Tell a story where a curious little animal named {helper.id} finds a trembling {foundling.label} near compost and helps it kindly.",
        "Write a soft garden tale where curiosity leads to kindness, and the ending image proves that a tiny creature is safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    friend = f["friend"]
    foundling = f["foundling_cfg"]
    method = f["method"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id} and {friend.id}, two small animal friends, and a tiny {foundling.label} they found in {place.label}. The story follows how they noticed its trouble and chose to help.",
        ),
        (
            f"Why did the little {foundling.label} tremble?",
            f"It had been left in a dry, open patch instead of the damp compost it needed. That made it frightened and unsteady, so its body began to tremble.",
        ),
        (
            f"What made {helper.id} curious?",
            f"{helper.id} noticed a tiny movement and sound beside the path near the compost. That small clue made {helper.pronoun()} come closer to understand what was wrong.",
        ),
        (
            f"How did {helper.id} and {friend.id} show kindness?",
            f"They did not poke or leave the little {foundling.label} alone. They chose a gentle plan and tried to return it to the cool, damp compost it needed.",
        ),
    ]
    if f["outcome"] == "rescued":
        qa.append(
            (
                "How did they solve the problem?",
                f"{method.qa_text} That worked because the trip stayed soft and damp instead of dry and rough.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                "The tiny creature was safe back in the compost, and the heap sounded busy and alive again. The ending shows that the garden felt peaceful after the kindness was done.",
            )
        )
    else:
        qa.append(
            (
                "Did their first plan work?",
                f"No. {method.qa_text} So they had to stop and look for a softer, kinder way.",
            )
        )
        qa.append(
            (
                "What did they learn?",
                "They learned that kindness is not just helping quickly. It also means changing a plan when it is too rough for someone small and scared.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"curiosity", "kindness", "compost"}
    foundling = world.facts["foundling_cfg"]
    method = world.facts["method"]
    tags |= set(foundling.tags)
    tags |= set(method.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid creature for this world belongs in compost and needs dampness.
hazard(F) :- foundling(F), belongs_in_compost(F), needs_damp(F).

% A sensible method is gentle enough, strong enough, and keeps the foundling damp.
sensible_method(F, M) :- hazard(F), method(M), weight(F, W), power(M, P), P >= W,
                         keeps_damp(M), care(M, C), care_min(CM), C >= CM.

valid(P, F, M) :- place(P), hazard(F), sensible_method(F, M).

works(F, M) :- sensible_method(F, M).
outcome(rescued) :- chosen_foundling(F), chosen_method(M), works(F, M).
outcome(retry) :- chosen_foundling(F), chosen_method(M), not works(F, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for foundling_id, foundling in FOUNDLINGS.items():
        lines.append(asp.fact("foundling", foundling_id))
        if foundling.belongs_in_compost:
            lines.append(asp.fact("belongs_in_compost", foundling_id))
        if foundling.needs_damp:
            lines.append(asp.fact("needs_damp", foundling_id))
        lines.append(asp.fact("weight", foundling_id, foundling.weight))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method.keeps_damp:
            lines.append(asp.fact("keeps_damp", method_id))
        lines.append(asp.fact("power", method_id, method.power))
        lines.append(asp.fact("care", method_id, method.care))
    lines.append(asp.fact("care_min", CARE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_foundling", params.foundling),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: curiosity and kindness around a tiny compost rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--foundling", choices=FOUNDLINGS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_names(rng: random.Random, helper_name: Optional[str], friend_name: Optional[str]) -> tuple[str, str]:
    helper = helper_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    pools = [n for n in GIRL_NAMES + BOY_NAMES if n != helper]
    friend = friend_name or rng.choice(pools)
    return helper, friend


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.foundling:
        foundling = FOUNDLINGS[args.foundling]
        if not hazard_at_risk(foundling):
            raise StoryError(explain_rejection(foundling))
        if args.method:
            method = METHODS[args.method]
            if not method_works(method, foundling):
                raise StoryError(explain_method(method, foundling))
    elif args.method:
        # Explicit method alone is allowed; filtering happens through combos below.
        pass

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.foundling is None or combo[1] == args.foundling)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, foundling_id, method_id = rng.choice(sorted(combos))
    animal_id = args.animal or rng.choice(sorted(ANIMALS))
    helper_name, friend_name = _pick_names(rng, args.helper_name, args.friend_name)
    return StoryParams(
        place=place_id,
        animal=animal_id,
        helper_name=helper_name,
        friend_name=friend_name,
        foundling=foundling_id,
        method=method_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.foundling not in FOUNDLINGS:
        raise StoryError(f"(Unknown foundling: {params.foundling})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    foundling = FOUNDLINGS[params.foundling]
    method = METHODS[params.method]
    if not hazard_at_risk(foundling):
        raise StoryError(explain_rejection(foundling))
    if outcome_of(params) == "retry":
        # Known but refused for ordinary generation.
        raise StoryError(explain_method(method, foundling))

    world = tell(
        place=PLACES[params.place],
        animal=ANIMALS[params.animal],
        helper_name=params.helper_name,
        friend_name=params.friend_name,
        foundling_cfg=foundling,
        method=method,
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
        print(f"{len(combos)} compatible (place, foundling, method) combos:\n")
        for place_id, foundling_id, method_id in combos:
            print(f"  {place_id:8} {foundling_id:12} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            try:
                samples.append(generate(params))
            except StoryError:
                # Keep curated output robust by skipping intentionally weak example entries.
                continue
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
            header = f"### {p.helper_name} and {p.friend_name}: {p.foundling} in {p.place} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
