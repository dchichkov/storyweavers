#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/offer_theme_decoy_sound_effects_inner_monologue.py
=============================================================================

A standalone story world about a pirate-themed picnic, a nosy animal, and a
grown-up's safe offer to use a decoy. The stories are small, child-facing, and
state-driven: a pretend pirate theme creates a problem, one child considers a
reckless move, a sensible offer changes the plan, and the ending image proves
that the decoy worked.

Run it
------
    python storyworlds/worlds/gpt-5.4/offer_theme_decoy_sound_effects_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/offer_theme_decoy_sound_effects_inner_monologue.py --theme pirates --pest gull
    python storyworlds/worlds/gpt-5.4/offer_theme_decoy_sound_effects_inner_monologue.py --decoy ribbon_wand
    python storyworlds/worlds/gpt-5.4/offer_theme_decoy_sound_effects_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/offer_theme_decoy_sound_effects_inner_monologue.py --qa --json
    python storyworlds/worlds/gpt-5.4/offer_theme_decoy_sound_effects_inner_monologue.py --verify
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
    visible: bool = False
    noisy: bool = False
    edible: bool = False
    secure: bool = False
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
class Theme:
    id: str
    scene: str
    opening: str
    titles: tuple[str, str]
    mission: str
    crew_word: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pest:
    id: str
    label: str
    cry: str
    verb: str
    wants: set[str] = field(default_factory=set)
    follows_sound: bool = False
    follows_motion: bool = False
    boldness: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    smell: str
    category: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Decoy:
    id: str
    label: str
    phrase: str
    attracts: set[str] = field(default_factory=set)
    lure: int = 1
    sound: str = ""
    motion: str = ""
    sense: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeSpot:
    id: str
    label: str
    phrase: str
    blocks: set[str] = field(default_factory=set)
    secure_level: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    pest: str
    treasure: str
    decoy: str
    safe_spot: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    relation: str = "siblings"
    trust: int = 6
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    pest = world.get("pest")
    treasure = world.get("treasure")
    decoy = world.get("decoy")
    if treasure.visible and treasure.meters["tempting"] >= THRESHOLD:
        sig = ("notice_treasure",)
        if sig not in world.fired:
            world.fired.add(sig)
            pest.meters["interest_treasure"] += 1
            out.append("__pest_near__")
    if decoy.visible:
        match = bool(pest.attrs.get("wants", set()) & decoy.attrs.get("attracts", set()))
        if match:
            sig = ("notice_decoy",)
            if sig not in world.fired:
                world.fired.add(sig)
                pest.meters["interest_decoy"] += decoy.attrs.get("lure", 1)
                out.append("__decoy_seen__")
    return out


def _r_shift(world: World) -> list[str]:
    out: list[str] = []
    pest = world.get("pest")
    if pest.meters["interest_decoy"] >= pest.meters["interest_treasure"] and pest.meters["interest_decoy"] >= THRESHOLD:
        sig = ("shift",)
        if sig not in world.fired:
            world.fired.add(sig)
            pest.meters["distracted"] += 1
            out.append("__shifted__")
    return out


def _r_steal(world: World) -> list[str]:
    out: list[str] = []
    pest = world.get("pest")
    treasure = world.get("treasure")
    safe_spot = world.get("safe_spot")
    if pest.meters["interest_treasure"] < THRESHOLD:
        return out
    if pest.meters["distracted"] >= THRESHOLD:
        return out
    if safe_spot.secure and treasure.attrs.get("hidden_in") == safe_spot.id:
        return out
    sig = ("steal",)
    if sig not in world.fired:
        world.fired.add(sig)
        treasure.meters["taken"] += 1
        for kid in world.kids():
            kid.memes["sad"] += 1
        out.append("__stolen__")
    return out


CAUSAL_RULES = [
    Rule(name="notice", tag="attention", apply=_r_notice),
    Rule(name="shift", tag="attention", apply=_r_shift),
    Rule(name="steal", tag="physical", apply=_r_steal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                changed = True
                produced.extend(result)
    return produced


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a tiny pirate cove",
        opening="The picnic blanket became a pirate deck, the juice box became a compass, and a striped towel became the sail.",
        titles=("Captain", "Lookout"),
        mission="guard their snack treasure from any thief of the shore",
        crew_word="pirates",
        ending="the little pirates munched their treasure in peace",
        tags={"pirate", "theme"},
    ),
    "island": Theme(
        id="island",
        scene="a bright island camp",
        opening="The blanket became an island map, the basket became a treasure chest, and a driftwood stick became a captain's cane.",
        titles=("Skipper", "Scout"),
        mission="keep their beach treasure safe until snack time",
        crew_word="crew",
        ending="the island crew shared their treasure with sandy smiles",
        tags={"island", "theme"},
    ),
    "harbor": Theme(
        id="harbor",
        scene="a busy harbor adventure",
        opening="The cooler became a dockside chest, the napkins became flags, and the shells made a line like little harbor lights.",
        titles=("Captain", "Matey"),
        mission="watch over their picnic prize like true sea guards",
        crew_word="sailors",
        ending="the young sailors ate beside the quiet water",
        tags={"harbor", "theme"},
    ),
}

PESTS = {
    "gull": Pest(
        id="gull",
        label="gull",
        cry="Caw! Caw!",
        verb="swooped low",
        wants={"food", "shine", "noise", "motion"},
        follows_sound=True,
        follows_motion=True,
        boldness=2,
        tags={"gull", "beach_animal"},
    ),
    "crab": Pest(
        id="crab",
        label="crab",
        cry="skritch skritch",
        verb="side-stepped closer",
        wants={"food", "motion"},
        follows_sound=False,
        follows_motion=True,
        boldness=1,
        tags={"crab", "beach_animal"},
    ),
    "raccoon": Pest(
        id="raccoon",
        label="raccoon",
        cry="sniff sniff",
        verb="padded toward the blanket",
        wants={"food", "shine", "noise"},
        follows_sound=True,
        follows_motion=False,
        boldness=2,
        tags={"raccoon", "animal"},
    ),
}

TREASURES = {
    "cookies": Treasure(
        id="cookies",
        label="cookies",
        phrase="a tin of cinnamon cookies",
        smell="smelled sweet and warm",
        category="food",
        tags={"food", "cookies"},
    ),
    "sandwiches": Treasure(
        id="sandwiches",
        label="sandwiches",
        phrase="a stack of little sandwiches",
        smell="smelled buttery and good",
        category="food",
        tags={"food", "sandwiches"},
    ),
    "berries": Treasure(
        id="berries",
        label="berries",
        phrase="a bowl of bright berries",
        smell="smelled fresh and juicy",
        category="food",
        tags={"food", "berries"},
    ),
}

DECOYS = {
    "shell_rattle": Decoy(
        id="shell_rattle",
        label="shell rattle",
        phrase="a shell rattle tied with string",
        attracts={"noise", "motion"},
        lure=3,
        sound="Clack-clack!",
        motion="the shells danced and flashed in the sun",
        sense=3,
        tags={"decoy", "sound", "shells"},
    ),
    "cracker_trail": Decoy(
        id="cracker_trail",
        label="cracker trail",
        phrase="a tiny trail of plain crackers",
        attracts={"food"},
        lure=2,
        sound="tap tap",
        motion="the crumbs led away across the sand",
        sense=3,
        tags={"decoy", "food"},
    ),
    "ribbon_wand": Decoy(
        id="ribbon_wand",
        label="ribbon wand",
        phrase="a fluttery ribbon wand",
        attracts={"motion", "shine"},
        lure=2,
        sound="swish-swish!",
        motion="the ribbons flickered like fish tails",
        sense=2,
        tags={"decoy", "motion"},
    ),
    "gold_coin": Decoy(
        id="gold_coin",
        label="gold coin",
        phrase="a real shiny coin from the grown-up's purse",
        attracts={"shine"},
        lure=1,
        sound="plink",
        motion="the coin winked once in the light",
        sense=1,
        tags={"decoy", "shine"},
    ),
}

SAFE_SPOTS = {
    "lidded_cooler": SafeSpot(
        id="lidded_cooler",
        label="cooler",
        phrase="the lidded cooler",
        blocks={"gull", "crab", "raccoon"},
        secure_level=3,
        tags={"cooler", "safe_spot"},
    ),
    "picnic_basket": SafeSpot(
        id="picnic_basket",
        label="basket",
        phrase="the picnic basket with its flap tucked down",
        blocks={"crab", "raccoon"},
        secure_level=2,
        tags={"basket", "safe_spot"},
    ),
    "high_table": SafeSpot(
        id="high_table",
        label="table",
        phrase="the high snack table",
        blocks={"crab"},
        secure_level=1,
        tags={"table", "safe_spot"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "quick", "gentle", "steady"]

KNOWLEDGE = {
    "gull": [("Why do gulls come near picnics?",
              "Gulls look for easy food. If they see or smell a snack, they may swoop closer very quickly.")],
    "crab": [("How does a crab move?",
              "A crab usually scuttles sideways on its little legs. It can move quickly, even though it looks funny.")],
    "raccoon": [("Why are raccoons good at finding snacks?",
                 "Raccoons have sharp noses and clever paws. They are very good at noticing food people leave out.")],
    "decoy": [("What is a decoy?",
               "A decoy is something that distracts attention away from the thing you want to protect. It is used to lead eyes, ears, or noses somewhere else.")],
    "sound": [("Why can sound attract an animal?",
               "A sound can make an animal turn its head and come closer to check. Rustles, clacks, and swishes can pull attention away from something else.")],
    "cooler": [("What does a cooler do at a picnic?",
                "A cooler keeps food tucked away and covered. A lid also makes it harder for animals to grab the snacks.")],
    "basket": [("Why put food back in a basket?",
                "A basket keeps snacks together and less open. Covered food is harder for a curious animal to snatch.")],
    "theme": [("What is a theme in a game?",
               "A theme is the big idea that makes pretend play feel special. Pirate hats, treasure words, and brave voices can all be part of one theme.")],
}
KNOWLEDGE_ORDER = ["theme", "decoy", "sound", "gull", "crab", "raccoon", "cooler", "basket"]


def decoy_matches(pest: Pest, decoy: Decoy) -> bool:
    return bool(pest.wants & decoy.attracts)


def safe_spot_works(pest: Pest, safe_spot: SafeSpot) -> bool:
    return pest.id in safe_spot.blocks and safe_spot.secure_level >= pest.boldness


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for theme_id in THEMES:
        for pest_id, pest in PESTS.items():
            for treasure_id in TREASURES:
                for decoy_id, decoy in DECOYS.items():
                    for safe_id, safe_spot in SAFE_SPOTS.items():
                        if decoy.sense >= SENSE_MIN and decoy_matches(pest, decoy) and safe_spot_works(pest, safe_spot):
                            combos.append((theme_id, pest_id, treasure_id, decoy_id, safe_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "taken": sim.get("treasure").meters["taken"] >= THRESHOLD,
        "interest": sim.get("pest").meters["interest_treasure"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, treasure: Treasure) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a sunny shore, {a.id} and {b.id} turned their picnic into {theme.scene}. "
        f"{theme.opening}"
    )
    world.say(
        f'"{theme.titles[0]} {a.id} and {theme.titles[1]} {b.id}!" {a.id} cried. '
        f'"Our mission is to {theme.mission}!"'
    )
    world.say(f"Near them sat {treasure.phrase}, and it {treasure.smell}.")


def pest_arrives(world: World, b: Entity, pest: Pest) -> None:
    world.get("treasure").visible = True
    world.get("treasure").meters["tempting"] += 1
    signals = propagate(world, narrate=False)
    b.memes["worry"] += 1
    world.say(
        f"Then {pest.cry} A {pest.label} {pest.verb}. {b.id} saw it first and felt a little pinch inside."
    )
    if "__pest_near__" in signals:
        world.say(
            f'"Oh no," {b.id} whispered. "{b.pronoun("subject").capitalize()} sees the treasure."'
        )


def reckless_idea(world: World, a: Entity, pest: Pest) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} straightened up. "I will scare that {pest.label} away myself!" {a.pronoun().capitalize()} said.'
    )
    world.say(
        f'Inside, {a.id} thought, "Maybe if I rush fast enough, this will look brave."'
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity, pest: Pest, safe_spot: SafeSpot) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_taken"] = pred["taken"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} tugged at {a.id}\'s sleeve. "{parent.label_word.capitalize()} said not to chase wild animals," '
        f'{b.pronoun()} said. "If we run after it, the snacks might still be snatched before we can stop it."'
    )
    world.say(
        f'Inside, {b.id} thought, "We need a calmer plan. We need the treasure in {safe_spot.phrase}."'
    )


def make_offer(world: World, parent: Entity, decoy: Decoy, safe_spot: SafeSpot) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over at once and knelt beside them."
    )
    world.say(
        f'"I have an offer," {parent.pronoun()} said softly. "Let us put the treasure in {safe_spot.phrase} '
        f"and use {decoy.phrase} as a decoy instead."'
    )


def accept_offer(world: World, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
    world.say(
        f'{a.id} blinked, then nodded. Inside, {a.pronoun()} thought, "That is braver than a foolish dash."'
    )
    world.say(f'"A decoy!" {b.id} said. "That fits our pirate theme perfectly."')


def use_plan(world: World, parent: Entity, decoy_cfg: Decoy, safe_cfg: SafeSpot) -> None:
    decoy = world.get("decoy")
    treasure = world.get("treasure")
    safe_spot = world.get("safe_spot")
    treasure.visible = False
    treasure.attrs["hidden_in"] = safe_spot.id
    safe_spot.secure = True
    decoy.visible = True
    decoy.noisy = bool(decoy_cfg.sound)
    decoy.attrs["attracts"] = set(decoy_cfg.attracts)
    decoy.attrs["lure"] = decoy_cfg.lure
    signals = propagate(world, narrate=False)
    world.say(
        f"They tucked the snack treasure into {safe_cfg.phrase}. Then {parent.label_word} lifted {decoy_cfg.phrase}."
    )
    fx = decoy_cfg.sound.strip()
    if fx:
        world.say(f"{fx} {decoy_cfg.motion}.")
    else:
        world.say(decoy_cfg.motion + ".")
    if "__shifted__" in signals:
        world.say(
            f"The {world.get('pest').label} turned at once and followed the decoy the wrong way."
        )


def happy_end(world: World, a: Entity, b: Entity, theme: Theme, pest: Pest, safe_spot: SafeSpot) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Soon the {pest.label} was busy with the trick, and the real treasure stayed safe in {safe_spot.phrase}."
    )
    world.say(
        f'{a.id} laughed. "{theme.crew_word.capitalize()} can win with cleverness too!"'
    )
    world.say(
        f"When snack time came, {theme.ending}, while the sea made a soft hush-hush at the shore."
    )


def sad_end(world: World, a: Entity, b: Entity, pest: Pest) -> None:
    world.say(
        f"But it was too late. The {pest.label} grabbed at the food and left the blanket messy and bare."
    )
    world.say(
        f'{a.id} felt hot in the face. Inside, {a.pronoun()} thought, "I wanted to be bold, but I did not choose the wise way first."'
    )
    world.say(
        f"{b.id} leaned close, and together they helped clean up while {world.get('parent').label_word} reminded them that calm plans work better than wild chasing."
    )


def tell(
    theme: Theme,
    pest_cfg: Pest,
    treasure_cfg: Treasure,
    decoy_cfg: Decoy,
    safe_cfg: SafeSpot,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        attrs={"relation": relation, "trust": trust},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    pest = world.add(Entity(
        id="pest",
        type="animal",
        label=pest_cfg.label,
        attrs={"wants": set(pest_cfg.wants), "boldness": pest_cfg.boldness},
        tags=set(pest_cfg.tags),
    ))
    treasure = world.add(Entity(
        id="treasure",
        type="food",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        edible=True,
        visible=False,
        tags=set(treasure_cfg.tags),
    ))
    safe_spot = world.add(Entity(
        id="safe_spot",
        type="container",
        label=safe_cfg.label,
        phrase=safe_cfg.phrase,
        secure=False,
        attrs={"blocks": set(safe_cfg.blocks), "secure_level": safe_cfg.secure_level},
        tags=set(safe_cfg.tags),
    ))
    decoy = world.add(Entity(
        id="decoy",
        type="tool",
        label=decoy_cfg.label,
        phrase=decoy_cfg.phrase,
        visible=False,
        noisy=bool(decoy_cfg.sound),
        attrs={"attracts": set(decoy_cfg.attracts), "lure": decoy_cfg.lure, "sense": decoy_cfg.sense},
        tags=set(decoy_cfg.tags),
    ))

    play_setup(world, a, b, theme, treasure_cfg)
    world.para()
    pest_arrives(world, b, pest_cfg)
    reckless_idea(world, a, pest_cfg)
    warn(world, b, a, parent, pest_cfg, safe_cfg)
    world.para()

    if delay > 0:
        propagate(world, narrate=False)
        if world.get("treasure").meters["taken"] >= THRESHOLD:
            sad_end(world, a, b, pest_cfg)
            outcome = "taken"
        else:
            make_offer(world, parent, decoy_cfg, safe_cfg)
            accept_offer(world, a, b)
            use_plan(world, parent, decoy_cfg, safe_cfg)
            world.para()
            if world.get("treasure").meters["taken"] >= THRESHOLD:
                sad_end(world, a, b, pest_cfg)
                outcome = "taken"
            else:
                happy_end(world, a, b, theme, pest_cfg, safe_cfg)
                outcome = "safe"
    else:
        make_offer(world, parent, decoy_cfg, safe_cfg)
        accept_offer(world, a, b)
        use_plan(world, parent, decoy_cfg, safe_cfg)
        world.para()
        if world.get("treasure").meters["taken"] >= THRESHOLD:
            sad_end(world, a, b, pest_cfg)
            outcome = "taken"
        else:
            happy_end(world, a, b, theme, pest_cfg, safe_cfg)
            outcome = "safe"

    world.facts.update(
        theme=theme,
        pest_cfg=pest_cfg,
        treasure_cfg=treasure_cfg,
        decoy_cfg=decoy_cfg,
        safe_cfg=safe_cfg,
        instigator=a,
        cautioner=b,
        parent=parent,
        pest=pest,
        treasure=treasure,
        decoy=decoy,
        safe_spot=safe_spot,
        outcome=outcome,
        delay=delay,
        relation=relation,
    )
    return world


def explain_combo(pest: Pest, decoy: Decoy, safe_spot: SafeSpot) -> str:
    if decoy.sense < SENSE_MIN:
        return (
            f"(No story: {decoy.label} is a poor decoy here. A storyworld should prefer a safer, clearer distraction.)"
        )
    if not decoy_matches(pest, decoy):
        return (
            f"(No story: a {pest.label} would not care much about {decoy.label}. The decoy needs to match what the animal notices.)"
        )
    if not safe_spot_works(pest, safe_spot):
        return (
            f"(No story: {safe_spot.label} does not protect the treasure well enough from a {pest.label}. The safe spot must really block the animal.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    if params.delay > 0:
        return "taken"
    return "safe"


ASP_RULES = r"""
match(P, D) :- wants(P, X), attracts(D, X).
good_decoy(D) :- decoy(D), sense(D, S), sense_min(M), S >= M.
good_safe(P, S) :- pest(P), safe_spot(S), blocks(S, P), secure_level(S, L), boldness(P, B), L >= B.
valid(T, P, Tr, D, S) :- theme(T), pest(P), treasure(Tr), good_decoy(D), match(P, D), good_safe(P, S).

outcome(taken) :- delay(D), D > 0.
outcome(safe)  :- delay(0).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for pest_id, pest in PESTS.items():
        lines.append(asp.fact("pest", pest_id))
        lines.append(asp.fact("boldness", pest_id, pest.boldness))
        for want in sorted(pest.wants):
            lines.append(asp.fact("wants", pest_id, want))
    for treasure_id in TREASURES:
        lines.append(asp.fact("treasure", treasure_id))
    for decoy_id, decoy in DECOYS.items():
        lines.append(asp.fact("decoy", decoy_id))
        lines.append(asp.fact("sense", decoy_id, decoy.sense))
        for attr in sorted(decoy.attracts):
            lines.append(asp.fact("attracts", decoy_id, attr))
    for safe_id, safe_spot in SAFE_SPOTS.items():
        lines.append(asp.fact("safe_spot", safe_id))
        lines.append(asp.fact("secure_level", safe_id, safe_spot.secure_level))
        for pest_id in sorted(safe_spot.blocks):
            lines.append(asp.fact("blocks", safe_id, pest_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(
        asp_program(
            f"{asp.fact('delay', params.delay)}",
            "#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    pest = f["pest_cfg"]
    decoy = f["decoy_cfg"]
    return [
        f'Write a short pirate-style story for a 3-to-5-year-old that includes the words "offer", "theme", and "decoy".',
        f"Tell a beach adventure where two children pretend to be {theme.crew_word}, a {pest.label} threatens their snack treasure, and a grown-up makes a calm offer.",
        f'Write a story with sound effects and inner monologue where a clever decoy saves the day and the pretend theme matters to the solution.',
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    pest = f["pest_cfg"]
    treasure = f["treasure_cfg"]
    decoy = f["decoy_cfg"]
    safe_spot = f["safe_cfg"]
    relation = f["relation"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.id} and {b.id}, who were pretending to be {theme.crew_word} at a picnic. Their {parent.label_word} helps them choose a clever plan."
        ),
        (
            "What was the children's pirate game?",
            f"They gave the picnic a pirate theme and treated their snacks like treasure. That pretend game shaped the problem because they wanted to guard the food like a crew on watch."
        ),
        (
            f"Why did {b.id} get worried?",
            f"{b.id} saw the {pest.label} come close to the blanket and knew it had noticed the food. The treasure smelled tempting, so the animal might snatch it if the children only chased and shouted."
        ),
        (
            "What was the grown-up's offer?",
            f"The grown-up's offer was to hide the real snack treasure in {safe_spot.phrase} and use {decoy.phrase} as a decoy. That plan protected the food while pulling the animal's attention somewhere else."
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                "How did the decoy help?",
                f"The decoy gave the {pest.label} something else to notice first. Because it matched what the animal liked, it followed the trick while the real treasure stayed safe."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the snack treasure safe and the children still in their pretend game. They learned that clever, calm teamwork can feel just as brave as charging ahead."
            )
        )
    else:
        qa.append(
            (
                "Why was the treasure taken?",
                f"The children waited too long before using the safe plan, so the {pest.label} reached the food first. A quick, calm choice would have worked better than rushing after trouble."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that bold feelings are not enough by themselves. A wise plan, made early, protects what matters better than a noisy chase."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"theme", "decoy"}
    if f["decoy_cfg"].sound:
        tags.add("sound")
    tags |= set(f["pest_cfg"].tags)
    tags |= set(f["safe_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {}
            for key, value in ent.attrs.items():
                if isinstance(value, set):
                    shown[key] = sorted(value)
                elif value:
                    shown[key] = value
            if shown:
                bits.append(f"attrs={shown}")
        flags = []
        if ent.visible:
            flags.append("visible")
        if ent.noisy:
            flags.append("noisy")
        if ent.secure:
            flags.append("secure")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        pest="gull",
        treasure="cookies",
        decoy="shell_rattle",
        safe_spot="lidded_cooler",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="island",
        pest="crab",
        treasure="berries",
        decoy="ribbon_wand",
        safe_spot="high_table",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        theme="harbor",
        pest="raccoon",
        treasure="sandwiches",
        decoy="cracker_trail",
        safe_spot="lidded_cooler",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        delay=1,
        relation="siblings",
        trust=4,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate-themed picnic, a decoy, and a calm offer."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--pest", choices=PESTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--decoy", choices=DECOYS)
    ap.add_argument("--safe-spot", dest="safe_spot", choices=SAFE_SPOTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = plan in time, 1 = too late")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.decoy is not None and DECOYS[args.decoy].sense < SENSE_MIN:
        raise StoryError(explain_combo(PESTS[args.pest] if args.pest else next(iter(PESTS.values())), DECOYS[args.decoy], SAFE_SPOTS[args.safe_spot] if args.safe_spot else next(iter(SAFE_SPOTS.values()))))
    if args.pest and args.decoy and not decoy_matches(PESTS[args.pest], DECOYS[args.decoy]):
        safe_pick = SAFE_SPOTS[args.safe_spot] if args.safe_spot else next(iter(SAFE_SPOTS.values()))
        raise StoryError(explain_combo(PESTS[args.pest], DECOYS[args.decoy], safe_pick))
    if args.pest and args.safe_spot and not safe_spot_works(PESTS[args.pest], SAFE_SPOTS[args.safe_spot]):
        decoy_pick = DECOYS[args.decoy] if args.decoy else next(iter(DECOYS.values()))
        raise StoryError(explain_combo(PESTS[args.pest], decoy_pick, SAFE_SPOTS[args.safe_spot]))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.pest is None or combo[1] == args.pest)
        and (args.treasure is None or combo[2] == args.treasure)
        and (args.decoy is None or combo[3] == args.decoy)
        and (args.safe_spot is None or combo[4] == args.safe_spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, pest, treasure, decoy, safe_spot = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    return StoryParams(
        theme=theme,
        pest=pest,
        treasure=treasure,
        decoy=decoy,
        safe_spot=safe_spot,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
        delay=args.delay if args.delay is not None else rng.choice([0, 0, 1]),
        relation=rng.choice(["siblings", "friends"]),
        trust=rng.randint(3, 8),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        pest = PESTS[params.pest]
        treasure = TREASURES[params.treasure]
        decoy = DECOYS[params.decoy]
        safe_spot = SAFE_SPOTS[params.safe_spot]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not (decoy.sense >= SENSE_MIN and decoy_matches(pest, decoy) and safe_spot_works(pest, safe_spot)):
        raise StoryError(explain_combo(pest, decoy, safe_spot))

    world = tell(
        theme=theme,
        pest_cfg=pest,
        treasure_cfg=treasure,
        decoy_cfg=decoy,
        safe_cfg=safe_spot,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        relation=params.relation,
        trust=params.trust,
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


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as err:
        print(f"ASP verify failed to run clingo: {err}")
        return 1

    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for _ in range(20):
        params = resolve_params(parser.parse_args([]), rng)
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (theme, pest, treasure, decoy, safe_spot) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:12}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.instigator} & {p.cautioner}: {p.pest}, {p.decoy}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
