#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pup_friendship_misunderstanding_mystery.py
=====================================================================

A small storyworld about a friendship misunderstanding wrapped in a gentle
mystery. Two children are getting ready for something special when one small
belonging goes missing. A clue trail makes one child wrongly suspect the other,
but the real culprit is a playful pup who carried the missing thing to a cozy
spot.

The world model tracks:
- typed entities with physical meters and emotional memes
- a tiny causal engine: carried item -> missing item + worry; accusation ->
  hurt feelings; found clue -> hope; apology -> friendship repaired
- a reasonableness gate over combinations of setting, item, clue, and hiding
  spot
- an inline ASP twin for the same gate and for the happy/sour outcome choice

Run it
------
    python storyworlds/worlds/gpt-5.4/pup_friendship_misunderstanding_mystery.py
    python storyworlds/worlds/gpt-5.4/pup_friendship_misunderstanding_mystery.py --item ribbon --clue pawprints
    python storyworlds/worlds/gpt-5.4/pup_friendship_misunderstanding_mystery.py --spot rainbarrel
    python storyworlds/worlds/gpt-5.4/pup_friendship_misunderstanding_mystery.py --all
    python storyworlds/worlds/gpt-5.4/pup_friendship_misunderstanding_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pup_friendship_misunderstanding_mystery.py --verify
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
    small: bool = False
    soft: bool = False
    wearable: bool = False
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
class Setting:
    id: str
    place: str
    intro: str
    mystery_nook: str
    surface: str
    wet_ground: bool
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    article: str
    use: str
    carryable: bool
    cozy: bool
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Clue:
    id: str
    label: str
    discover: str
    leads_to: str
    requires_wet: bool = False
    requires_soft_item: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    cozy: bool
    sheltered: bool
    fits_small: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class PupType:
    id: str
    label: str
    sound: str
    movement: str
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


def _r_missing(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["carried_by_pup"] < THRESHOLD:
        return out
    sig = ("missing", "item")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["missing"] += 1
    for kid_id in ("friend1", "friend2"):
        world.get(kid_id).memes["worry"] += 1
    out.append("__missing__")
    return out


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("friend1")
    listener = world.get("friend2")
    if speaker.memes["suspects"] < THRESHOLD:
        return out
    sig = ("hurt", "friends")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    listener.memes["hurt"] += 1
    speaker.memes["guilt_seed"] += 1
    speaker.memes["friendship"] -= 1
    listener.memes["friendship"] -= 1
    out.append("__hurt__")
    return out


def _r_hope(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clue").meters["noticed"] < THRESHOLD:
        return out
    sig = ("hope", "clue")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid_id in ("friend1", "friend2"):
        world.get(kid_id).memes["hope"] += 1
    out.append("__hope__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.get("friend1").memes["apology"] < THRESHOLD:
        return out
    sig = ("repair", "friends")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid_id in ("friend1", "friend2"):
        kid = world.get(kid_id)
        kid.memes["friendship"] += 2
        kid.memes["hurt"] = 0.0
        kid.memes["worry"] = 0.0
    out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule("missing", "physical", _r_missing),
    Rule("hurt", "social", _r_hurt),
    Rule("hope", "social", _r_hope),
    Rule("repair", "social", _r_repair),
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


def valid_clue(setting: Setting, item: Item, clue: Clue) -> bool:
    if clue.requires_wet and not setting.wet_ground:
        return False
    if clue.requires_soft_item and not item.cozy:
        return False
    return True


def valid_spot(setting: Setting, item: Item, spot: Spot) -> bool:
    if spot.id not in setting.spots:
        return False
    if not item.carryable:
        return False
    if not spot.fits_small:
        return False
    return True


def valid_combo(setting: Setting, item: Item, clue: Clue, spot: Spot) -> bool:
    return valid_clue(setting, item, clue) and valid_spot(setting, item, spot)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for cid, clue in CLUES.items():
                for pid, spot in SPOTS.items():
                    if valid_combo(setting, item, clue, spot):
                        combos.append((sid, iid, cid, pid))
    return combos


def predict_path(world: World, clue: Clue, spot: Spot) -> dict:
    sim = world.copy()
    sim.get("item").meters["carried_by_pup"] += 1
    propagate(sim, narrate=False)
    return {
        "item_missing": sim.get("item").meters["missing"] >= THRESHOLD,
        "clue_text": clue.discover,
        "spot_text": spot.phrase,
    }


def introduce(world: World, a: Entity, b: Entity, item: Item, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["friendship"] += 2
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} were best friends, and that afternoon they met in {setting.place}. "
        f"{setting.intro}"
    )
    world.say(
        f"They were getting ready for {item.use}, and {a.id} had brought {item.phrase}. "
        f"It felt like exactly the right thing for their special plan."
    )


def add_pup(world: World, pup: Entity, pup_type: PupType) -> None:
    pup.memes["curiosity"] += 1
    world.say(
        f"Near the edge of the place, a {pup_type.label} pup watched them with bright eyes. "
        f"It gave a small {pup_type.sound} and made a quick {pup_type.movement} around their feet."
    )


def set_down_item(world: World, a: Entity, item: Entity, setting: Setting) -> None:
    world.say(
        f'"I will set {item.label} right here for one tiny minute," {a.id} said, '
        f"placing it beside {setting.mystery_nook}."
    )


def pup_takes_item(world: World, pup: Entity, item: Entity, spot: Spot) -> None:
    item.meters["carried_by_pup"] += 1
    pup.attrs["spot"] = spot.id
    propagate(world, narrate=False)


def discover_loss(world: World, a: Entity, b: Entity, item: Item) -> None:
    world.say(
        f"When {a.id} turned back, {item.the} was gone. One blink before, it had been there. "
        f"Now the empty place looked like the start of a tiny mystery."
    )
    world.say(f'"Where did {item.the} go?" {b.id} whispered.')
    if world.get("item").meters["missing"] >= THRESHOLD:
        world.say("Both friends felt a little knot of worry in their chests.")


def suspect_friend(world: World, a: Entity, b: Entity, item: Item) -> None:
    a.memes["suspects"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} remembered that {b.id} had been the closest one to the spot. "
        f'"Did you take {item.the}?" {a.id} asked.'
    )
    world.say(
        f'{b.id} stepped back. "No," {b.pronoun()} said softly. '
        f'"I only turned to look at the flowers."'
    )
    if b.memes["hurt"] >= THRESHOLD:
        world.say(f"The question landed like a pebble between them, and the warm game suddenly felt colder.")


def notice_clue(world: World, b: Entity, clue: Clue, pup_type: PupType) -> None:
    world.get("clue").meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {b.id} pointed to {clue.discover}. "
        f'"Look," {b.pronoun()} said. "That does not look like a person clue. It looks like a pup clue."'
    )
    world.say(
        f"The little mystery changed shape at once. Somewhere nearby, the {pup_type.label} pup had left a trail."
    )


def follow_clue(world: World, a: Entity, b: Entity, clue: Clue, spot: Spot) -> None:
    world.say(
        f"Together they followed {clue.leads_to} until it led them to {spot.phrase}."
    )
    world.say(
        f"They slowed to tiptoe steps, as if a grand detective secret might leap out if they were too loud."
    )


def reveal(world: World, a: Entity, b: Entity, pup: Entity, item: Item, spot: Spot) -> None:
    item_ent = world.get("item")
    item_ent.meters["found"] += 1
    item_ent.meters["missing"] = 0.0
    pup.memes["proud"] += 1
    world.say(
        f"There, inside {spot.phrase}, was the pup, curled around {item.the}. "
        f"It looked up with shining eyes and thumped its tail."
    )
    if ITEMS[item.id].cozy and SPOTS[spot.id].cozy:
        world.say(
            f"The pup had not tried to steal anything meanly. It had carried {item.the} to make its hiding place feel soft and snug."
        )
    else:
        world.say(
            f"The pup had only wanted to play. It had carried {item.the} away and tucked it into its secret spot."
        )


def apology(world: World, a: Entity, b: Entity, item: Item) -> None:
    a.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id}'s cheeks grew warm. "
        f'"I am sorry, {b.id}," {a.pronoun()} said. "I thought you had taken {item.the}, and I was wrong."'
    )
    world.say(
        f'{b.id} nodded. "I was hurt," {b.pronoun()} said, "but I am glad we solved it together."'
    )


def ending(world: World, a: Entity, b: Entity, pup: Entity, item: Item) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"They picked up {item.the}, and this time {a.id} let {b.id} help hold it safely between them."
    )
    world.say(
        f"The pup trotted after the two friends, no longer a suspect-maker but a happy little shadow."
    )
    world.say(
        f"Soon the mystery was over, the friendship felt mended, and the afternoon ended with three companions close together: "
        f"two smiling friends and one drowsy pup at their feet."
    )


def sour_ending(world: World, a: Entity, b: Entity, item: Item) -> None:
    world.say(
        f'"I am sorry," {a.id} said, but the words came late, after the mystery had already made the air heavy.'
    )
    world.say(
        f"{b.id} forgave {a.pronoun('object')}, yet the rest of the afternoon stayed quiet. "
        f"They found {item.the}, but the game never fully turned warm again."
    )


def tell(setting: Setting, item_cfg: Item, clue: Clue, spot: Spot, pup_type: PupType,
         friend1: str = "Lina", friend1_gender: str = "girl",
         friend2: str = "Owen", friend2_gender: str = "boy",
         parent_type: str = "mother", repair: bool = True) -> World:
    world = World()
    a = world.add(Entity(id=friend1, kind="character", type=friend1_gender, role="friend1"))
    b = world.add(Entity(id=friend2, kind="character", type=friend2_gender, role="friend2"))
    pup = world.add(Entity(id="Pip", kind="character", type="dog", label="the pup", role="pup"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item_ent = world.add(Entity(
        id="item", type="item", label=item_cfg.label, small=item_cfg.carryable,
        soft=item_cfg.cozy, wearable=(item_cfg.id in {"ribbon", "mitten"})
    ))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label))
    world.facts["repair"] = repair

    introduce(world, a, b, item_cfg, setting)
    add_pup(world, pup, pup_type)
    set_down_item(world, a, item_ent, setting)

    world.para()
    pup_takes_item(world, pup, item_ent, spot)
    discover_loss(world, a, b, item_cfg)
    suspect_friend(world, a, b, item_cfg)

    world.para()
    pred = predict_path(world, clue, spot)
    world.facts["predicted_item_missing"] = pred["item_missing"]
    notice_clue(world, b, clue, pup_type)
    follow_clue(world, a, b, clue, spot)
    reveal(world, a, b, pup, item_cfg, spot)

    world.para()
    if repair:
        apology(world, a, b, item_cfg)
        ending(world, a, b, pup, item_cfg)
        outcome = "repaired"
    else:
        sour_ending(world, a, b, item_cfg)
        outcome = "sour"

    world.facts.update(
        friend1=a,
        friend2=b,
        pup=pup,
        parent=parent,
        setting=setting,
        item_cfg=item_cfg,
        item=item_ent,
        clue=clue,
        spot=spot,
        pup_type=pup_type,
        outcome=outcome,
        missing=item_ent.meters["found"] >= THRESHOLD,
        hurt=b.memes["hurt"] >= THRESHOLD or a.memes["guilt_seed"] >= THRESHOLD,
        repaired=repair,
    )
    return world


SETTINGS = {
    "garden": Setting(
        "garden",
        "the garden behind the house",
        "Sunlight lay across the stepping stones, and tall flowers nodded as if they knew a secret.",
        "the old watering can",
        "soil",
        wet_ground=False,
        spots={"bench", "flowerpot", "porchbox"},
        tags={"garden"},
    ),
    "yard_after_rain": Setting(
        "yard_after_rain",
        "the yard just after a little rain",
        "The grass still glimmered, and the damp ground kept prints the way a notebook keeps marks.",
        "the back step",
        "mud",
        wet_ground=True,
        spots={"bench", "rainbarrel", "porchbox"},
        tags={"yard", "rain"},
    ),
    "porch": Setting(
        "porch",
        "the front porch in the late afternoon",
        "The boards creaked softly, and shadows under the railing made neat little hiding places.",
        "the striped doormat",
        "wood",
        wet_ground=False,
        spots={"bench", "porchbox"},
        tags={"porch"},
    ),
}

ITEMS = {
    "ribbon": Item(
        "ribbon", "ribbon", "a bright blue ribbon", "a",
        "decorating their secret detective club sign",
        carryable=True, cozy=True, tags={"ribbon", "friendship"},
    ),
    "mitten": Item(
        "mitten", "mitten", "a tiny red mitten", "a",
        "making a puppet friend for their game",
        carryable=True, cozy=True, tags={"mitten", "friendship"},
    ),
    "note": Item(
        "note", "note", "a folded paper note with a silver star", "a",
        "reading the first clue of their pretend mystery game",
        carryable=True, cozy=False, tags={"note", "mystery"},
    ),
}

CLUES = {
    "pawprints": Clue(
        "pawprints",
        "a line of muddy pawprints",
        "the pawprints in a curving little trail",
        requires_wet=True,
        tags={"pawprints", "mystery"},
    ),
    "blue_thread": Clue(
        "blue_thread",
        "a snag of thread caught on a splinter",
        "the tiny thread marks and sniffs",
        requires_soft_item=True,
        tags={"thread", "mystery"},
    ),
    "chewed_corner": Clue(
        "chewed_corner",
        "one small tooth mark and a faint puppy smell",
        "the tooth-mark clue and the tiny snuffling sounds",
        tags={"toothmark", "mystery"},
    ),
}

SPOTS = {
    "bench": Spot("bench", "under the bench", "the shadowy space under the bench", cozy=False, sheltered=True, tags={"bench"}),
    "flowerpot": Spot("flowerpot", "behind the flowerpot", "the big flowerpot by the fence", cozy=False, sheltered=False, tags={"flowerpot"}),
    "porchbox": Spot("porchbox", "inside the porch toy box", "the half-open porch toy box", cozy=True, sheltered=True, tags={"toybox"}),
    "rainbarrel": Spot("rainbarrel", "behind the rain barrel", "the dry nook behind the rain barrel", cozy=True, sheltered=True, tags={"rainbarrel"}),
}

PUPS = {
    "scruffy": PupType("scruffy", "scruffy brown", "woof", "skip"),
    "spotted": PupType("spotted", "spotted white", "yip", "prance"),
    "golden": PupType("golden", "golden", "arf", "bounce"),
}

GIRL_NAMES = ["Lina", "Mia", "Zoe", "Nora", "Ella", "Ruby", "Tess", "Anna"]
BOY_NAMES = ["Owen", "Max", "Leo", "Finn", "Noah", "Ben", "Theo", "Sam"]


@dataclass
class StoryParams:
    setting: str
    item: str
    clue: str
    spot: str
    pup: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    parent: str
    repair: bool = True
    seed: Optional[int] = None


KNOWLEDGE = {
    "pawprints": [(
        "What are pawprints?",
        "Pawprints are little marks an animal's feet leave on soft ground. Mud or dust can make them easier to see."
    )],
    "thread": [(
        "Why might a ribbon leave thread behind?",
        "Soft cloth or ribbon can catch on rough wood and leave a little thread. That can become a useful clue."
    )],
    "toothmark": [(
        "Why do puppies chew things?",
        "Puppies often explore the world with their mouths. They may nibble or chew because they are curious or playful."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is a puzzle about something hidden or unknown. You solve it by noticing clues and thinking carefully."
    )],
    "friendship": [(
        "What helps fix a friendship misunderstanding?",
        "Listening, telling the truth, and saying sorry help. A kind apology can make hurt feelings begin to heal."
    )],
    "garden": [(
        "Why are gardens good places for little mysteries?",
        "Gardens have paths, leaves, pots, and corners where tiny things can hide. That gives children many places to search for clues."
    )],
    "rain": [(
        "Why do muddy prints show up after rain?",
        "Rain softens the ground and makes mud stick to feet and paws. Then each step can leave a mark behind."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "friendship", "garden", "rain", "pawprints", "thread", "toothmark"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    item = f["item_cfg"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "pup" and a friendship misunderstanding.',
        f"Tell a small mystery where {a.id} wrongly thinks {b.id} took {item.the}, but a clue in {setting.place} leads to the real answer.",
        f'Write a child-facing story with friendship, misunderstanding, and a playful pup, using a clue like "{clue.label}" and ending with an apology.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    item = f["item_cfg"]
    clue = f["clue"]
    spot = f["spot"]
    setting = f["setting"]
    pup = f["pup"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, and a little pup named {pup.id}. The story happens in {setting.place}."
        ),
        (
            f"What went missing?",
            f"{item.the.capitalize()} went missing after {a.id} set it down for a moment. That missing item is what began the tiny mystery."
        ),
        (
            f"Why did {a.id} think {b.id} had taken it?",
            f"{a.id} remembered that {b.id} had been standing nearest to the place where {item.the} had been left. Because the item vanished so suddenly, {a.id} guessed too quickly instead of waiting for more clues."
        ),
        (
            "What clue helped solve the mystery?",
            f"The clue was {clue.discover}. It mattered because it pointed toward a pup, not toward {b.id}."
        ),
        (
            f"Where did they find {item.the}?",
            f"They found {item.the} in {spot.phrase} with the pup. The hiding spot proved that the pup had carried it away."
        ),
    ]
    if f["outcome"] == "repaired":
        out.append((
            "How was the friendship fixed?",
            f"{a.id} said sorry for the wrong accusation, and {b.id} admitted the question had hurt. They solved the mystery together, and that shared truth helped their friendship feel warm again."
        ))
    else:
        out.append((
            "Did the apology fix everything right away?",
            f"Not completely. They found the answer, but the misunderstanding had already made the afternoon quiet and heavy."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "friendship"} | set(world.facts["setting"].tags) | set(world.facts["clue"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("yard_after_rain", "ribbon", "pawprints", "rainbarrel", "scruffy", "Lina", "girl", "Owen", "boy", "mother", True),
    StoryParams("garden", "mitten", "blue_thread", "porchbox", "golden", "Mia", "girl", "Finn", "boy", "father", True),
    StoryParams("porch", "note", "chewed_corner", "bench", "spotted", "Nora", "girl", "Sam", "boy", "mother", True),
    StoryParams("porch", "ribbon", "blue_thread", "porchbox", "spotted", "Ruby", "girl", "Leo", "boy", "father", False),
]


def explain_rejection(setting: Setting, item: Item, clue: Clue, spot: Spot) -> str:
    if clue.requires_wet and not setting.wet_ground:
        return (
            f"(No story: {clue.label} needs wet ground, but {setting.place} is not wet enough to hold that kind of clue. "
            f"Try the yard_after_rain setting or choose a different clue.)"
        )
    if clue.requires_soft_item and not item.cozy:
        return (
            f"(No story: {clue.label} only makes sense with a soft cloth-like item, but {item.the} would not leave that clue. "
            f"Try ribbon or mitten.)"
        )
    if spot.id not in setting.spots:
        return (
            f"(No story: {spot.phrase} is not part of {setting.place}, so the clue trail cannot honestly lead there.)"
        )
    if not item.carryable:
        return f"(No story: a small pup could not reasonably carry {item.the}.)"
    return "(No story: this combination does not make a plausible little mystery.)"


def outcome_of(params: StoryParams) -> str:
    return "repaired" if params.repair else "sour"


ASP_RULES = r"""
valid_clue(S, I, C) :- setting(S), item(I), clue(C), not clue_needs_wet(C), not clue_needs_soft(C).
valid_clue(S, I, C) :- setting(S), item(I), clue(C), clue_needs_wet(C), wet_ground(S), not clue_needs_soft(C).
valid_clue(S, I, C) :- setting(S), item(I), clue(C), not clue_needs_wet(C), clue_needs_soft(C), cozy(I).
valid_clue(S, I, C) :- setting(S), item(I), clue(C), clue_needs_wet(C), wet_ground(S), clue_needs_soft(C), cozy(I).

valid_spot(S, I, P) :- setting(S), item(I), spot(P), carryable(I), fits_small(P), has_spot(S, P).

valid(S, I, C, P) :- valid_clue(S, I, C), valid_spot(S, I, P).

outcome(repaired) :- repair(true).
outcome(sour) :- repair(false).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.wet_ground:
            lines.append(asp.fact("wet_ground", sid))
        for spot_id in sorted(s.spots):
            lines.append(asp.fact("has_spot", sid, spot_id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.carryable:
            lines.append(asp.fact("carryable", iid))
        if item.cozy:
            lines.append(asp.fact("cozy", iid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.requires_wet:
            lines.append(asp.fact("clue_needs_wet", cid))
        if clue.requires_soft_item:
            lines.append(asp.fact("clue_needs_soft", cid))
    for pid, spot in SPOTS.items():
        lines.append(asp.fact("spot", pid))
        if spot.fits_small:
            lines.append(asp.fact("fits_small", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("repair", "true" if params.repair else "false")
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            rc = 1
            print(f"MISMATCH in outcome for {case}")
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle mystery storyworld: a missing item, a friendship misunderstanding, and a playful pup."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--pup", choices=PUPS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--repair", choices=["true", "false"],
                    help="whether the apology fully repairs the friendship")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    repair = True if args.repair is None else (args.repair == "true")

    if args.setting and args.item and args.clue and args.spot:
        s, i, c, p = SETTINGS[args.setting], ITEMS[args.item], CLUES[args.clue], SPOTS[args.spot]
        if not valid_combo(s, i, c, p):
            raise StoryError(explain_rejection(s, i, c, p))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, item, clue, spot = rng.choice(sorted(combos))
    pup = args.pup or rng.choice(sorted(PUPS))
    friend1, g1 = _pick_name(rng)
    friend2, g2 = _pick_name(rng, avoid=friend1)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, item, clue, spot, pup, friend1, g1, friend2, g2, parent, repair)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        CLUES[params.clue],
        SPOTS[params.spot],
        PUPS[params.pup],
        params.friend1,
        params.friend1_gender,
        params.friend2,
        params.friend2_gender,
        params.parent,
        params.repair,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, clue, spot) combos:\n")
        for setting, item, clue, spot in combos:
            print(f"  {setting:14} {item:8} {clue:12} {spot}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.friend1} & {p.friend2}: {p.item} in {p.setting} ({p.clue}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
