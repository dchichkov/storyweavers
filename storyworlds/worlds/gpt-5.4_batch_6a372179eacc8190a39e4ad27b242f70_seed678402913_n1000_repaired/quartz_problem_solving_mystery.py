#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quartz_problem_solving_mystery.py
===========================================================

A standalone storyworld for a child-facing mystery about a missing shiny object,
a trail of quartz, and a calm bit of problem solving.

The world model prefers a small, sensible mystery:
- a treasured object goes missing while two children are busy,
- a pet has carried it to a nearby hiding spot,
- pale quartz grit or pebbles provide a real clue,
- the children solve the mystery with an appropriate search method,
- the ending image proves that the worry changed into relief.

Run it
------
    python storyworlds/worlds/gpt-5.4/quartz_problem_solving_mystery.py
    python storyworlds/worlds/gpt-5.4/quartz_problem_solving_mystery.py --place porch --item bell --spot boot_tray --method trail
    python storyworlds/worlds/gpt-5.4/quartz_problem_solving_mystery.py --item key --method listen
    python storyworlds/worlds/gpt-5.4/quartz_problem_solving_mystery.py --all
    python storyworlds/worlds/gpt-5.4/quartz_problem_solving_mystery.py --verify
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal_it = {"kitten", "puppy", "cat", "dog", "pet"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal_it:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    quartz_source: str
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    shine: str
    purpose: str
    jingles: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Pet:
    id: str
    type: str
    label: str
    move_verb: str
    motive: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    reveal_by: set[str] = field(default_factory=set)
    dark: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    approach: str
    success_line: str
    reject_line: str
    needs_sound: bool = False
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


def _r_hidden_means_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    if not item or item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("worry", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role in {"detective", "helper"}:
            ent.memes["worry"] += 1
            ent.memes["curiosity"] += 1
    return out


def _r_quartz_clue(world: World) -> list[str]:
    pet = world.entities.get("pet")
    room = world.entities.get("room")
    if not pet or not room:
        return []
    if pet.meters["tracked_quartz"] < THRESHOLD:
        return []
    sig = ("quartz_clue", pet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["quartz_clue"] += 1
    return []


def _r_found_clears_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    if not item or item.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role in {"detective", "helper"}:
            ent.memes["worry"] = 0.0
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_means_worry", tag="emotion", apply=_r_hidden_means_worry),
    Rule(name="quartz_clue", tag="physical", apply=_r_quartz_clue),
    Rule(name="found_clears_worry", tag="emotion", apply=_r_found_clears_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        if not any(rule.apply(world) for rule in []):
            pass
        current_fired = len(world.fired)
        for rule in CAUSAL_RULES:
            pass
        if current_fired != len(world.fired):
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="garden",
        intro="the little garden beside the shed",
        quartz_source="A line of pale quartz pebbles curved around the herb bed",
        spots={"under_bench", "watering_can"},
        tags={"garden", "quartz"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        intro="the front porch with the creaky swing",
        quartz_source="a bowl of milky quartz stones sat beside the fern",
        spots={"boot_tray", "under_chair"},
        tags={"porch", "quartz"},
    ),
    "sunroom": Place(
        id="sunroom",
        label="sunroom",
        intro="the warm sunroom full of leaf shadows",
        quartz_source="a lemon plant stood in a pot topped with tiny white quartz chips",
        spots={"toy_basket", "curtain_fold"},
        tags={"sunroom", "quartz"},
    ),
}

ITEMS = {
    "bell": MissingItem(
        id="bell",
        label="silver bell",
        phrase="a small silver bell",
        shine="flashed whenever the light touched it",
        purpose="for the pretend treasure box",
        jingles=True,
        tags={"bell", "shiny"},
    ),
    "key": MissingItem(
        id="key",
        label="brass key",
        phrase="a little brass key",
        shine="glowed warm and gold",
        purpose="for the old music chest",
        jingles=False,
        tags={"key", "shiny"},
    ),
    "star": MissingItem(
        id="star",
        label="star badge",
        phrase="a tin star badge",
        shine="winked like a tiny moon",
        purpose="for the detective sash",
        jingles=False,
        tags={"badge", "shiny"},
    ),
}

PETS = {
    "kitten": Pet(
        id="kitten",
        type="kitten",
        label="kitten",
        move_verb="batted",
        motive="anything that glittered looked like a toy to it",
        tags={"kitten", "pet"},
    ),
    "puppy": Pet(
        id="puppy",
        type="puppy",
        label="puppy",
        move_verb="carried",
        motive="anything small and bright looked worth trotting off with",
        tags={"puppy", "pet"},
    ),
}

SPOTS = {
    "under_bench": Spot(
        id="under_bench",
        label="under the bench",
        phrase="the dusty shadow under the garden bench",
        reveal_by={"flashlight", "trail"},
        dark=True,
        tags={"bench", "dark_place"},
    ),
    "watering_can": Spot(
        id="watering_can",
        label="inside the watering can",
        phrase="inside the tall green watering can",
        reveal_by={"listen"},
        dark=False,
        tags={"watering_can"},
    ),
    "boot_tray": Spot(
        id="boot_tray",
        label="in the boot tray",
        phrase="in the rubber boot tray by the door",
        reveal_by={"trail"},
        dark=False,
        tags={"boot_tray"},
    ),
    "under_chair": Spot(
        id="under_chair",
        label="under the porch chair",
        phrase="under the striped porch chair",
        reveal_by={"flashlight"},
        dark=True,
        tags={"chair", "dark_place"},
    ),
    "toy_basket": Spot(
        id="toy_basket",
        label="in the toy basket",
        phrase="deep in the toy basket",
        reveal_by={"trail"},
        dark=False,
        tags={"basket"},
    ),
    "curtain_fold": Spot(
        id="curtain_fold",
        label="inside the curtain fold",
        phrase="inside a heavy fold of the curtain",
        reveal_by={"flashlight"},
        dark=True,
        tags={"curtain", "dark_place"},
    ),
}

METHODS = {
    "trail": Method(
        id="trail",
        label="follow the quartz trail",
        approach="got low and followed the pale quartz specks one by one",
        success_line="The little trail led straight to the hiding place",
        reject_line="There was no clear trail to follow there",
        needs_sound=False,
        tags={"trail", "quartz"},
    ),
    "flashlight": Method(
        id="flashlight",
        label="use a flashlight",
        approach="clicked on a flashlight and swept the beam into the dark place",
        success_line="The beam caught a small shine in the shadows",
        reject_line="The flashlight showed plenty of dust, but not the missing thing",
        needs_sound=False,
        tags={"flashlight", "light"},
    ),
    "listen": Method(
        id="listen",
        label="listen for a jingle",
        approach="went very still and listened for the tiniest sound",
        success_line="A soft jingle answered from the hiding place",
        reject_line="Nothing jingled back",
        needs_sound=True,
        tags={"listen", "sound"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Max", "Theo", "Jack", "Finn", "Eli"]
TRAITS = ["careful", "curious", "bright", "patient", "thoughtful", "steady"]


def place_supports_spot(place_id: str, spot_id: str) -> bool:
    return spot_id in PLACES[place_id].spots


def method_fits(item_id: str, spot_id: str, method_id: str) -> bool:
    if method_id not in SPOTS[spot_id].reveal_by:
        return False
    method = METHODS[method_id]
    item = ITEMS[item_id]
    if method.needs_sound and not item.jingles:
        return False
    return True


def valid_combo(place_id: str, item_id: str, spot_id: str, method_id: str) -> bool:
    return place_supports_spot(place_id, spot_id) and method_fits(item_id, spot_id, method_id)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for item_id in sorted(ITEMS):
            for spot_id in sorted(SPOTS):
                for method_id in sorted(METHODS):
                    if valid_combo(place_id, item_id, spot_id, method_id):
                        combos.append((place_id, item_id, spot_id, method_id))
    return combos


def explain_rejection(place_id: str, item_id: str, spot_id: str, method_id: str) -> str:
    if not place_supports_spot(place_id, spot_id):
        return (
            f"(No story: {SPOTS[spot_id].label} does not belong in the {PLACES[place_id].label}, "
            f"so the mystery's hiding place would not make sense there.)"
        )
    if method_id not in SPOTS[spot_id].reveal_by:
        return (
            f"(No story: {METHODS[method_id].label} is not a sensible way to check "
            f"{SPOTS[spot_id].label}. Pick a method that can really reveal that spot.)"
        )
    if METHODS[method_id].needs_sound and not ITEMS[item_id].jingles:
        return (
            f"(No story: {ITEMS[item_id].label} does not jingle, so listening cannot reveal it. "
            f"Choose a bell or choose another method.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


def outcome_of(params: "StoryParams") -> str:
    return "solved" if valid_combo(params.place, params.item, params.spot, params.method) else "stumped"


def predict_solution(world: World, item_id: str, spot_id: str, method_id: str) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["hidden"] = 1
    sim.get("pet").meters["tracked_quartz"] = 1
    propagate(sim, narrate=False)
    solved = method_fits(item_id, spot_id, method_id)
    return {
        "quartz_clue": sim.get("room").meters["quartz_clue"] >= THRESHOLD,
        "solved": solved,
    }


def setup_scene(world: World, detective: Entity, helper: Entity, adult: Entity,
                place: Place, item: MissingItem) -> None:
    world.say(
        f"After lunch, {detective.id} and {helper.id} made a mystery club in {place.intro}. "
        f"On a crate between them sat {item.phrase} {item.purpose}."
    )
    world.say(
        f"{place.quartz_source}, and in the bright part of the day it almost looked as if the stones were awake."
    )
    world.say(
        f'"We will guard every clue," {detective.id} whispered. {helper.id} nodded as if the whole place might have secrets.'
    )
    world.facts["opening_image"] = place.quartz_source


def pet_hides_item(world: World, pet: Entity, item: Entity, spot: Spot, item_cfg: MissingItem, pet_cfg: Pet) -> None:
    item.meters["hidden"] = 1
    pet.meters["tracked_quartz"] = 1
    item.attrs["spot"] = spot.id
    world.facts["hide_action"] = pet_cfg.move_verb
    world.facts["hide_reason"] = pet_cfg.motive
    propagate(world, narrate=False)
    world.say(
        f"Then a soft little rustle came from behind them. When the children turned back, the {item_cfg.label} was gone."
    )
    world.say(
        f"For a second the mystery felt almost spooky. But on the floor there were a few pale grains of quartz where no grains had been before."
    )


def notice_problem(world: World, detective: Entity, helper: Entity, item_cfg: MissingItem) -> None:
    world.para()
    world.say(
        f'{helper.id} stared at the empty crate. "The {item_cfg.label} was right here," {helper.pronoun()} said.'
    )
    if detective.memes["worry"] >= THRESHOLD:
        world.say(
            f"{detective.id}'s tummy gave a small worried flutter, but curiosity was stronger than tears."
        )


def inspect_clue(world: World, detective: Entity, helper: Entity, place: Place,
                 pet: Pet, method: Method, item_cfg: MissingItem, spot: Spot) -> None:
    pred = predict_solution(world, item_cfg.id, spot.id, method.id)
    world.facts["predicted_quartz"] = pred["quartz_clue"]
    world.facts["predicted_solved"] = pred["solved"]
    world.say(
        f"{detective.id} knelt beside the floorboards. The quartz bits were chalky white, just like the stones from {place.quartz_source.lower()}."
    )
    world.say(
        f'"So it was not a ghost," {detective.id} said. "Something with paws crossed the quartz and took it."'
    )
    world.say(
        f"{helper.id} looked toward the {pet.label} and began to think instead of guess."
    )


def solve_mystery(world: World, detective: Entity, helper: Entity, adult: Entity,
                  pet: Entity, item: Entity, item_cfg: MissingItem, pet_cfg: Pet,
                  spot: Spot, method: Method) -> None:
    world.para()
    for kid in (detective, helper):
        kid.memes["focus"] += 1
    world.say(
        f"They did not rush. First they looked at the clue, then at the pet, and then at all the places nearby where a small bright thing could hide."
    )
    world.say(
        f"{detective.id} {method.approach}."
    )
    world.say(
        f"{method.success_line}. There, in {spot.phrase}, lay the {item_cfg.label}; it {item_cfg.shine}."
    )
    item.meters["found"] = 1
    item.meters["hidden"] = 0
    pet.memes["mischief"] += 1
    world.facts["found_at"] = spot.label
    world.facts["method_sentence"] = method.success_line
    propagate(world, narrate=False)
    world.say(
        f'The {pet_cfg.label} blinked up at them as if it had only borrowed the treasure for a moment.'
    )
    world.say(
        f'{adult.label_word.capitalize()} smiled from the doorway. "That was real detective work," {adult.pronoun()} said. "You looked for a clue, made a plan, and checked it."'
    )


def ending(world: World, detective: Entity, helper: Entity, item_cfg: MissingItem) -> None:
    world.para()
    world.say(
        f"{helper.id} set the {item_cfg.label} back on the crate with both hands, much more carefully this time."
    )
    world.say(
        f"The mystery club felt different now: not spooky, only bright and clever."
    )
    world.say(
        f"Soon the quartz by the door was glowing in the late light, and the children were grinning at the clue that had helped them solve the case."
    )


def tell(place: Place, item_cfg: MissingItem, pet_cfg: Pet, spot: Spot, method: Method,
         detective_name: str = "Lily", detective_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         adult_type: str = "mother", trait: str = "curious") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits={trait},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits={"loyal"},
    ))
    adult = world.add(Entity(
        id="Parent",
        kind="character",
        type=adult_type,
        role="adult",
        label="the parent",
    ))
    pet = world.add(Entity(
        id="pet",
        kind="character",
        type=pet_cfg.type,
        role="pet",
        label=pet_cfg.label,
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=detective.id,
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label=place.label,
    ))

    detective.memes["confidence"] += 1
    helper.memes["trust"] += 1

    setup_scene(world, detective, helper, adult, place, item_cfg)
    pet_hides_item(world, pet, item, spot, item_cfg, pet_cfg)
    notice_problem(world, detective, helper, item_cfg)
    inspect_clue(world, detective, helper, place, pet_cfg, method, item_cfg, spot)

    if not method_fits(item_cfg.id, spot.id, method.id):
        world.para()
        world.say(
            f"They tried to be detectives, but {method.reject_line.lower()}. The case had to wait until a grown-up helped them search more slowly."
        )
        world.facts["outcome"] = "stumped"
    else:
        solve_mystery(world, detective, helper, adult, pet, item, item_cfg, pet_cfg, spot, method)
        ending(world, detective, helper, item_cfg)
        world.facts["outcome"] = "solved"

    world.facts.update(
        detective=detective,
        helper=helper,
        adult=adult,
        pet=pet,
        place=place,
        item_cfg=item_cfg,
        spot=spot,
        method=method,
        found=item.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "quartz": [
        (
            "What is quartz?",
            "Quartz is a hard kind of stone. It can look white, clear, or sparkly, and people often notice how it catches the light."
        )
    ],
    "trail": [
        (
            "What is a clue trail?",
            "A clue trail is a line of signs that leads you somewhere. Good detectives follow each sign slowly instead of making a wild guess."
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help in a mystery?",
            "A flashlight helps you see into dark corners and under furniture. It lets you check a hiding place instead of only imagining what might be there."
        )
    ],
    "listen": [
        (
            "When does listening help solve a problem?",
            "Listening helps when something makes a sound, like a bell or a rattle. If the thing is silent, you need a different clue."
        )
    ],
    "kitten": [
        (
            "Why do kittens bat at shiny things?",
            "Kittens like to practice pouncing and batting. A small shiny object can look like a toy to them."
        )
    ],
    "puppy": [
        (
            "Why do puppies carry things away?",
            "Puppies explore with their mouths and like trotting off with interesting objects. That is why grown-ups keep small things out of reach."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery calmly?",
            "First you notice what changed, then you look for real clues, and then you test one careful idea. Solving a mystery works better with thinking than with panicking."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "quartz", "trail", "flashlight", "listen", "kitten", "puppy"]


@dataclass
class StoryParams:
    place: str
    item: str
    pet: str
    spot: str
    method: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    place = f["place"]
    item_cfg = f["item_cfg"]
    method = f["method"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the word "quartz" and ends with a missing object being found.',
        f"Tell a gentle problem-solving mystery where {detective.id} and {helper.id} notice that a {item_cfg.label} has vanished in the {place.label} and use clues instead of panic.",
        f'Write a child-facing detective story where the children solve the case by choosing to {method.label}.',
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    adult = f["adult"]
    place = f["place"]
    item_cfg = f["item_cfg"]
    pet = f["pet"]
    spot = f["spot"]
    method = f["method"]
    pair = pair_noun(detective, helper)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {detective.id} and {helper.id}, who were playing mystery club, plus a pet {pet.label} and {detective.id}'s {adult.label_word}.",
        ),
        (
            f"What was missing?",
            f"The missing thing was {item_cfg.phrase} {item_cfg.purpose}. It disappeared from the crate while the children were busy being detectives.",
        ),
        (
            "What clue did they notice?",
            f"They noticed pale bits of quartz on the floor where there had not been any before. That clue told them something real had carried the object away, so the mystery was not magic at all.",
        ),
        (
            "How did they solve the mystery?",
            f"They slowed down and chose to {method.label}. Then they checked a place where a pet could really hide a small shiny thing instead of guessing wildly.",
        ),
    ]
    if f.get("found"):
        qa.append(
            (
                f"Where did they find the {item_cfg.label}?",
                f"They found it {spot.label}. The clue and the careful search matched each other, which is why the children could solve the case.",
            )
        )
        qa.append(
            (
                f"Why did the {pet.label} take it?",
                f"The {pet.label} took it because {f['hide_reason']}. The object looked bright and interesting, so the pet treated it like a toy instead of a treasure.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely and happily: the {item_cfg.label} went back on the crate, and the children felt clever instead of worried. The glowing quartz at the end showed that the clue had become part of the happy answer.",
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "quartz"}
    tags |= set(f["method"].tags)
    tags |= set(PETS[f["pet"].type].tags) if f["pet"].type in PETS else set()
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        item="star",
        pet="kitten",
        spot="under_bench",
        method="flashlight",
        detective_name="Lily",
        detective_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        adult="mother",
        trait="patient",
    ),
    StoryParams(
        place="porch",
        item="bell",
        pet="puppy",
        spot="boot_tray",
        method="trail",
        detective_name="Mia",
        detective_gender="girl",
        helper_name="Sam",
        helper_gender="boy",
        adult="father",
        trait="curious",
    ),
    StoryParams(
        place="sunroom",
        item="bell",
        pet="kitten",
        spot="curtain_fold",
        method="flashlight",
        detective_name="Theo",
        detective_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        adult="mother",
        trait="thoughtful",
    ),
    StoryParams(
        place="garden",
        item="bell",
        pet="puppy",
        spot="watering_can",
        method="listen",
        detective_name="Ava",
        detective_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        adult="father",
        trait="steady",
    ),
]


ASP_RULES = r"""
supports(P, S) :- place(P), spot(S), place_spot(P, S).
method_ok(I, S, M) :- item(I), spot(S), method(M), reveal_by(S, M), not needs_sound(M).
method_ok(I, S, M) :- item(I), spot(S), method(M), reveal_by(S, M), needs_sound(M), jingles(I).
valid(P, I, S, M) :- supports(P, S), method_ok(I, S, M).

outcome(solved)  :- chosen_place(P), chosen_item(I), chosen_spot(S), chosen_method(M), valid(P, I, S, M).
outcome(stumped) :- chosen_place(P), chosen_item(I), chosen_spot(S), chosen_method(M), not valid(P, I, S, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for spot_id in sorted(place.spots):
            lines.append(asp.fact("place_spot", place_id, spot_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.jingles:
            lines.append(asp.fact("jingles", item_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for method_id in sorted(spot.reveal_by):
            lines.append(asp.fact("reveal_by", spot_id, method_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method.needs_sound:
            lines.append(asp.fact("needs_sound", method_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    checked = 0
    for place_id in sorted(PLACES):
        for item_id in sorted(ITEMS):
            for spot_id in sorted(SPOTS):
                for method_id in sorted(METHODS):
                    params = StoryParams(
                        place=place_id,
                        item=item_id,
                        pet="kitten",
                        spot=spot_id,
                        method=method_id,
                        detective_name="Lily",
                        detective_gender="girl",
                        helper_name="Ben",
                        helper_gender="boy",
                        adult="mother",
                        trait="curious",
                    )
                    if asp_outcome(params) != outcome_of(params):
                        rc = 1
                        print(
                            "MISMATCH in outcome:",
                            (place_id, item_id, spot_id, method_id),
                            asp_outcome(params),
                            outcome_of(params),
                        )
                    checked += 1
    if rc == 0:
        print(f"OK: outcome model matches on {checked} scenarios.")

    try:
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:
        rc = 1
        print(f"Smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld: a missing shiny thing, a quartz clue, and problem solving."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--pet", choices=sorted(PETS))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.spot and args.method:
        if not valid_combo(args.place, args.item, args.spot, args.method):
            raise StoryError(explain_rejection(args.place, args.item, args.spot, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.spot is None or combo[2] == args.spot)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        if args.place and args.item and args.spot and args.method:
            raise StoryError(explain_rejection(args.place, args.item, args.spot, args.method))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, spot_id, method_id = rng.choice(sorted(combos))
    pet_id = args.pet or rng.choice(sorted(PETS))
    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=detective_name)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        item=item_id,
        pet=pet_id,
        spot=spot_id,
        method=method_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.pet not in PETS:
        raise StoryError(f"(Invalid pet: {params.pet})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    if not valid_combo(params.place, params.item, params.spot, params.method):
        raise StoryError(explain_rejection(params.place, params.item, params.spot, params.method))

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        pet_cfg=PETS[params.pet],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        trait=params.trait,
    )
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, spot, method) combos:\n")
        for place_id, item_id, spot_id, method_id in combos:
            print(f"  {place_id:8} {item_id:5} {spot_id:13} {method_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} & {p.helper_name}: {p.item} in {p.place} ({p.method} -> {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
