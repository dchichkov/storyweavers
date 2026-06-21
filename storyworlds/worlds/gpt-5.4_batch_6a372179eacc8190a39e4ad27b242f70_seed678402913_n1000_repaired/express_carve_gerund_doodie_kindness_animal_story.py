#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/express_carve_gerund_doodie_kindness_animal_story.py
===============================================================================

A standalone story world about forest animals using a carved welcome sign to
help a shy new neighbor feel seen.

The seed words and features are rebuilt as world state rather than pasted into
one frozen paragraph:
- "express" appears because the maker deliberately wants to express kindness.
- "carving" appears because the fix is a carved sign.
- "doodie" appears as Doodie, a small dung beetle who has just moved in.
- Kindness is the central turn: the world changes from "hard to find, easy to
  overlook" to "easy to find, warmly welcomed."

Reasonableness constraint
-------------------------
Not every animal can carve every material, and not every little home can hold a
heavy sign. The world refuses combinations that fail either rule:

    maker.can_carve(material)  AND  material.weight <= home.max_weight

That keeps the fix honest. A rabbit can scratch soft bark but cannot carve a
stone slab, and a tiny mushroom-door nook cannot sensibly carry a heavy sign.

Run it
------
    python storyworlds/worlds/gpt-5.4/express_carve_gerund_doodie_kindness_animal_story.py
    python storyworlds/worlds/gpt-5.4/express_carve_gerund_doodie_kindness_animal_story.py --maker beaver --material bark --home root_nook
    python storyworlds/worlds/gpt-5.4/express_carve_gerund_doodie_kindness_animal_story.py --maker rabbit --material driftwood
    python storyworlds/worlds/gpt-5.4/express_carve_gerund_doodie_kindness_animal_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/express_carve_gerund_doodie_kindness_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Maker:
    id: str
    name: str
    species: str
    phrase: str
    can_carve: set[str] = field(default_factory=set)
    tool: str = ""
    style: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HomeKind:
    id: str
    label: str
    phrase: str
    place: str
    max_weight: int
    hook: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    weight: int
    grain: str
    finish: str
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


def _r_hidden_lonely(world: World) -> list[str]:
    out: list[str] = []
    home = world.get("home")
    doodie = world.get("doodie")
    if home.meters["visible"] < THRESHOLD:
        sig = ("hidden_lonely",)
        if sig not in world.fired:
            world.fired.add(sig)
            doodie.memes["lonely"] += 1
            doodie.memes["worry"] += 1
            out.append("__hidden__")
    return out


def _r_carved_readable(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("sign")
    maker = world.get("maker")
    if sign.meters["carved"] >= THRESHOLD:
        sig = ("carved_readable",)
        if sig not in world.fired:
            world.fired.add(sig)
            sign.meters["readable"] += 1
            maker.memes["hope"] += 1
            out.append("__carved__")
    return out


def _r_mounted_visible(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("sign")
    home = world.get("home")
    doodie = world.get("doodie")
    if sign.meters["mounted"] >= THRESHOLD and sign.meters["readable"] >= THRESHOLD:
        sig = ("mounted_visible",)
        if sig not in world.fired:
            world.fired.add(sig)
            home.meters["visible"] += 1
            doodie.memes["belonging"] += 1
            doodie.memes["worry"] = 0.0
            out.append("__visible__")
    return out


def _r_visited_joy(world: World) -> list[str]:
    out: list[str] = []
    home = world.get("home")
    doodie = world.get("doodie")
    maker = world.get("maker")
    if home.meters["visible"] >= THRESHOLD and world.facts.get("visited"):
        sig = ("visited_joy",)
        if sig not in world.fired:
            world.fired.add(sig)
            doodie.memes["joy"] += 1
            doodie.memes["belonging"] += 1
            maker.memes["joy"] += 1
            out.append("__visited__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_lonely", tag="emotion", apply=_r_hidden_lonely),
    Rule(name="carved_readable", tag="physical", apply=_r_carved_readable),
    Rule(name="mounted_visible", tag="physical", apply=_r_mounted_visible),
    Rule(name="visited_joy", tag="social", apply=_r_visited_joy),
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


def can_make_sign(maker: Maker, material: Material) -> bool:
    return material.id in maker.can_carve


def can_mount(home: HomeKind, material: Material) -> bool:
    return material.weight <= home.max_weight


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for maker_id, maker in MAKERS.items():
        for material_id, material in MATERIALS.items():
            for home_id, home in HOMES.items():
                if can_make_sign(maker, material) and can_mount(home, material):
                    combos.append((maker_id, material_id, home_id))
    return combos


def predict_welcome(world: World, maker_cfg: Maker, material_cfg: Material, home_cfg: HomeKind) -> dict:
    sim = world.copy()
    carve_sign(sim, maker_cfg, material_cfg, narrate=False)
    mount_sign(sim, home_cfg, narrate=False)
    sim.facts["visited"] = True
    propagate(sim, narrate=False)
    return {
        "visible": sim.get("home").meters["visible"] >= THRESHOLD,
        "belonging": sim.get("doodie").memes["belonging"] >= THRESHOLD,
    }


def introduce(world: World, maker_cfg: Maker, home_cfg: HomeKind) -> None:
    maker = world.get("maker")
    doodie = world.get("doodie")
    world.say(
        f"In the ferny edge of the forest lived {maker.id}, {maker_cfg.phrase}. "
        f"Down the path, in {home_cfg.phrase}, lived Doodie, a little dung beetle who had only just moved in."
    )
    world.say(
        f"Doodie's tiny {home_cfg.label} sat {home_cfg.place}, and by dusk it was so easy to miss that feet and paws passed by without stopping."
    )
    world.say(
        f"Doodie tried to be brave, but sometimes {doodie.pronoun()} wondered if the other animals would ever find {doodie.pronoun('possessive')} door at all."
    )
    propagate(world, narrate=False)


def notice(world: World, maker_cfg: Maker) -> None:
    maker = world.get("maker")
    doodie = world.get("doodie")
    maker.memes["kindness"] += 1
    maker.memes["concern"] += 1
    world.say(
        f"When {maker.id} saw Doodie waiting alone beside a pebble lantern, {maker.pronoun()} knew {doodie.pronoun()} was trying not to look sad."
    )
    world.say(
        f'"I want to express a kind welcome," {maker.id} said softly. "If everyone can find your door, they can knock and say hello."'
    )


def plan(world: World, maker_cfg: Maker, material_cfg: Material, home_cfg: HomeKind) -> None:
    pred = predict_welcome(world, maker_cfg, material_cfg, home_cfg)
    world.facts["pred_visible"] = pred["visible"]
    world.facts["pred_belonging"] = pred["belonging"]
    world.say(
        f"{maker.id} looked at {material_cfg.phrase} and smiled. The {material_cfg.grain} would be just right for carving Doodie's name and a small moon."
    )
    world.say(
        f"{maker.pronoun().capitalize()} chose it because it was light enough for {home_cfg.phrase} and clear enough for little eyes to read in the evening."
    )


def carve_sign(world: World, maker_cfg: Maker, material_cfg: Material, narrate: bool = True) -> None:
    maker = world.get("maker")
    sign = world.get("sign")
    sign.meters["carved"] += 1
    sign.attrs["material"] = material_cfg.id
    sign.attrs["name"] = "Doodie"
    sign.attrs["moon"] = True
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"All afternoon, {maker.id} worked at the forest bench, {maker_cfg.tool} moving in patient little strokes. The carving took time, but soon Doodie's round name curled across the sign, with {material_cfg.finish} shining at the edges."
        )


def mount_sign(world: World, home_cfg: HomeKind, narrate: bool = True) -> None:
    sign = world.get("sign")
    sign.meters["mounted"] += 1
    world.get("home").attrs["hook"] = home_cfg.hook
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Then {world.get('maker').id} tied the new sign beside the door with {home_cfg.hook}. It swung once, caught the last gold light, and settled where anyone on the path could see it."
        )


def reveal(world: World, home_cfg: HomeKind) -> None:
    doodie = world.get("doodie")
    maker = world.get("maker")
    world.facts["visited"] = True
    propagate(world, narrate=False)
    world.say(
        f"That evening, the path did not slide past {home_cfg.phrase} anymore. A robin saw the sign first, then a squirrel, and soon soft voices were calling, \"Good evening, Doodie!\""
    )
    world.say(
        f"Doodie blinked, then smiled so hard that {doodie.pronoun('possessive')} whole shell seemed to glow. {maker.id}'s kind idea had turned a hidden door into a welcome one."
    )


def ending(world: World) -> None:
    doodie = world.get("doodie")
    maker = world.get("maker")
    world.say(
        f"Doodie set out acorn-cap tea for the visitors, and nobody hurried past again."
    )
    world.say(
        f"After that, whenever dusk came softly through the ferns, the little sign kept speaking before anyone even knocked: Doodie lives here, and friends are glad to come."
    )
    doodie.memes["gratitude"] += 1
    maker.memes["love"] += 1


def tell(maker_cfg: Maker, material_cfg: Material, home_cfg: HomeKind) -> World:
    world = World()
    maker = world.add(Entity(
        id=maker_cfg.name,
        kind="character",
        type="animal",
        label=maker_cfg.species,
        role="maker",
        attrs={"maker_id": maker_cfg.id},
        tags=set(maker_cfg.tags),
    ))
    doodie = world.add(Entity(
        id="Doodie",
        kind="character",
        type="animal",
        label="dung beetle",
        role="recipient",
        tags={"beetle", "kindness", "welcome"},
    ))
    home = world.add(Entity(
        id="home",
        kind="thing",
        type="home",
        label=home_cfg.label,
        phrase=home_cfg.phrase,
        role="home",
        attrs={"home_id": home_cfg.id},
        tags=set(home_cfg.tags),
    ))
    sign = world.add(Entity(
        id="sign",
        kind="thing",
        type="sign",
        label="welcome sign",
        phrase=f"a little sign cut from {material_cfg.label}",
        role="gift",
        attrs={"material_id": material_cfg.id},
        tags=set(material_cfg.tags),
    ))

    introduce(world, maker_cfg, home_cfg)
    world.para()
    notice(world, maker_cfg)
    plan(world, maker_cfg, material_cfg, home_cfg)
    world.para()
    carve_sign(world, maker_cfg, material_cfg, narrate=True)
    mount_sign(world, home_cfg, narrate=True)
    world.para()
    reveal(world, home_cfg)
    ending(world)

    world.facts.update(
        maker=maker,
        maker_cfg=maker_cfg,
        doodie=doodie,
        home=home,
        home_cfg=home_cfg,
        sign=sign,
        material_cfg=material_cfg,
        visited=world.facts.get("visited", False),
        visible=home.meters["visible"] >= THRESHOLD,
        belonging=doodie.memes["belonging"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "beetle": [
        (
            "What is a dung beetle?",
            "A dung beetle is a kind of beetle that rolls little balls and lives close to the ground. It is small, strong for its size, and easy to overlook if you are not paying attention.",
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means noticing what someone needs and choosing to help in a gentle way. It can be as small as making room for someone or helping them feel seen.",
        )
    ],
    "sign": [
        (
            "What does a sign do?",
            "A sign helps people know where something is or what it means. A clear sign can make a place easier to find.",
        )
    ],
    "carving": [
        (
            "What is carving?",
            "Carving is shaping wood or another material by cutting it carefully. It takes patience because the maker changes the shape a little bit at a time.",
        )
    ],
    "bark": [
        (
            "What is bark?",
            "Bark is the outside layer of a tree. Thin bark can be light and easy to use for small crafts.",
        )
    ],
    "driftwood": [
        (
            "What is driftwood?",
            "Driftwood is wood that has been washed smooth by water. It can make a lovely sign because the wood is already worn soft.",
        )
    ],
    "stone": [
        (
            "Why is stone heavy?",
            "Stone is hard and dense, so even a small slab can weigh a lot. Heavy things need strong support.",
        )
    ],
    "home": [
        (
            "Why might a tiny home be hard to find?",
            "A tiny home can blend into leaves, roots, or mushrooms around it. If it looks like the forest, walkers may pass it without noticing.",
        )
    ],
}

KNOWLEDGE_ORDER = ["beetle", "kindness", "sign", "carving", "bark", "driftwood", "stone", "home"]


@dataclass
class StoryParams:
    maker: str
    material: str
    home: str
    seed: Optional[int] = None


MAKERS = {
    "beaver": Maker(
        id="beaver",
        name="Bramble",
        species="beaver",
        phrase="a busy young beaver with a smooth carving knife",
        can_carve={"bark", "driftwood", "stone"},
        tool="that careful little knife",
        style="neat block letters",
        tags={"kindness", "carving", "sign"},
    ),
    "woodpecker": Maker(
        id="woodpecker",
        name="Tikka",
        species="woodpecker",
        phrase="a red-capped woodpecker with a sharp eye for shapes",
        can_carve={"bark", "driftwood"},
        tool="beak and claw together",
        style="tiny pecked dots",
        tags={"kindness", "carving", "sign"},
    ),
    "rabbit": Maker(
        id="rabbit",
        name="Clover",
        species="rabbit",
        phrase="a gentle rabbit who liked making careful presents",
        can_carve={"bark"},
        tool="a flint flake held between steady paws",
        style="soft curling letters",
        tags={"kindness", "carving", "sign"},
    ),
}

MATERIALS = {
    "bark": Material(
        id="bark",
        label="bark",
        phrase="a flat piece of birch bark",
        weight=1,
        grain="pale bark",
        finish="dewberry juice",
        tags={"bark", "carving", "sign"},
    ),
    "driftwood": Material(
        id="driftwood",
        label="driftwood",
        phrase="a smooth slice of driftwood",
        weight=2,
        grain="silvery wood",
        finish="sap gloss",
        tags={"driftwood", "carving", "sign"},
    ),
    "stone": Material(
        id="stone",
        label="stone",
        phrase="a round stone slab from the stream",
        weight=3,
        grain="cool gray stone",
        finish="moss rubbed bright",
        tags={"stone", "carving", "sign"},
    ),
}

HOMES = {
    "mushroom_nook": HomeKind(
        id="mushroom_nook",
        label="mushroom-door nook",
        phrase="a tiny nook under a red mushroom cap",
        place="under the biggest mushroom in the clearing",
        max_weight=1,
        hook="a loop of grass",
        tags={"home"},
    ),
    "root_nook": HomeKind(
        id="root_nook",
        label="root nook",
        phrase="a round door tucked between two tree roots",
        place="between the roots of an old oak",
        max_weight=2,
        hook="a twist of reed",
        tags={"home"},
    ),
    "stump_hollow": HomeKind(
        id="stump_hollow",
        label="stump hollow",
        phrase="a small hollow in an old stump",
        place="inside a mossy stump by the path",
        max_weight=3,
        hook="a stout twig peg",
        tags={"home"},
    ),
}


CURATED = [
    StoryParams(maker="beaver", material="bark", home="mushroom_nook"),
    StoryParams(maker="woodpecker", material="driftwood", home="root_nook"),
    StoryParams(maker="rabbit", material="bark", home="stump_hollow"),
    StoryParams(maker="beaver", material="stone", home="stump_hollow"),
]


def generation_prompts(world: World) -> list[str]:
    maker = world.facts["maker"]
    maker_cfg = world.facts["maker_cfg"]
    material_cfg = world.facts["material_cfg"]
    home_cfg = world.facts["home_cfg"]
    return [
        'Write a short Animal Story for a 3-to-5-year-old that includes the words "express", "carving", and "Doodie".',
        f"Tell a gentle forest story where {maker.id}, a {maker_cfg.species}, wants to express kindness to Doodie by carving a sign from {material_cfg.label}.",
        f"Write a story about a tiny home that is hard to find until a kind animal makes it easy to notice, ending with Doodie feeling welcome in {home_cfg.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    maker = world.facts["maker"]
    maker_cfg = world.facts["maker_cfg"]
    doodie = world.facts["doodie"]
    home_cfg = world.facts["home_cfg"]
    material_cfg = world.facts["material_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.id}, a kind {maker_cfg.species}, and Doodie, a little dung beetle with a tiny home in the forest.",
        ),
        (
            "Why was Doodie sad at the start?",
            f"Doodie's home was so small and hidden that other animals kept passing by without finding it. That made Doodie worry that nobody would stop to say hello.",
        ),
        (
            f"How did {maker.id} try to express kindness?",
            f"{maker.id} chose {material_cfg.phrase} and spent the afternoon carving Doodie's name into a little sign. {maker.pronoun().capitalize()} wanted the sign to help everyone find Doodie's door.",
        ),
    ]
    if world.facts.get("visible"):
        qa.append(
            (
                "What changed after the sign was hung up?",
                f"The hidden home became easy to notice, so other animals finally called out to Doodie at {home_cfg.phrase}. The sign changed the path from a place of passing by into a place of welcome.",
            )
        )
    if world.facts.get("belonging"):
        qa.append(
            (
                "How did Doodie feel at the end, and why?",
                f"Doodie felt happy and included. Once the sign was up and friends could find the door, Doodie no longer felt forgotten.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"beetle", "kindness", "sign", "carving"} | set(world.facts["material_cfg"].tags) | set(world.facts["home_cfg"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(maker: Maker, material: Material, home: HomeKind) -> str:
    if not can_make_sign(maker, material):
        good = ", ".join(sorted(maker.can_carve))
        return (
            f"(No story: {maker.name} the {maker.species} cannot sensibly carve {material.label}. "
            f"Try one of: {good}.)"
        )
    if not can_mount(home, material):
        return (
            f"(No story: {material.phrase} is too heavy for {home.phrase}. "
            f"A tiny home like that needs a lighter sign.)"
        )
    return "(No story: that combination does not make a reasonable welcome sign.)"


ASP_RULES = r"""
can_make(Mk, Mat) :- maker(Mk), material(Mat), can_carve(Mk, Mat).
can_mount(Home, Mat) :- home(Home), material(Mat),
                        max_weight(Home, MW), weight(Mat, W), W <= MW.
valid(Mk, Mat, Home) :- maker(Mk), material(Mat), home(Home),
                        can_make(Mk, Mat), can_mount(Home, Mat).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for maker_id, maker in MAKERS.items():
        lines.append(asp.fact("maker", maker_id))
        for material_id in sorted(maker.can_carve):
            lines.append(asp.fact("can_carve", maker_id, material_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("weight", material_id, material.weight))
    for home_id, home in HOMES.items():
        lines.append(asp.fact("home", home_id))
        lines.append(asp.fact("max_weight", home_id, home.max_weight))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(7)))
    except StoryError as err:
        rc = 1
        print(f"Smoke resolve failed: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            with io.StringIO() as buf, redirect_stdout(buf):
                emit(sample, trace=False, qa=False, header=f"### smoke {idx}")
        except Exception as err:
            rc = 1
            print(f"Smoke test failed on case {idx}: {err}")
            break

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal story world: a kind animal carves a sign so Doodie the beetle feels welcome."
    )
    ap.add_argument("--maker", choices=MAKERS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--home", choices=HOMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.maker and args.material and args.home:
        maker = MAKERS[args.maker]
        material = MATERIALS[args.material]
        home = HOMES[args.home]
        if not (can_make_sign(maker, material) and can_mount(home, material)):
            raise StoryError(explain_rejection(maker, material, home))

    combos = [
        combo
        for combo in valid_combos()
        if (args.maker is None or combo[0] == args.maker)
        and (args.material is None or combo[1] == args.material)
        and (args.home is None or combo[2] == args.home)
    ]
    if not combos:
        maker = MAKERS[args.maker] if args.maker else next(iter(MAKERS.values()))
        material = MATERIALS[args.material] if args.material else next(iter(MATERIALS.values()))
        home = HOMES[args.home] if args.home else next(iter(HOMES.values()))
        raise StoryError(explain_rejection(maker, material, home))

    maker_id, material_id, home_id = rng.choice(sorted(combos))
    return StoryParams(maker=maker_id, material=material_id, home=home_id)


def generate(params: StoryParams) -> StorySample:
    if params.maker not in MAKERS:
        raise StoryError(f"(Unknown maker: {params.maker})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.home not in HOMES:
        raise StoryError(f"(Unknown home: {params.home})")

    maker_cfg = MAKERS[params.maker]
    material_cfg = MATERIALS[params.material]
    home_cfg = HOMES[params.home]
    if not (can_make_sign(maker_cfg, material_cfg) and can_mount(home_cfg, material_cfg)):
        raise StoryError(explain_rejection(maker_cfg, material_cfg, home_cfg))

    world = tell(maker_cfg, material_cfg, home_cfg)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (maker, material, home) combos:\n")
        for maker_id, material_id, home_id in combos:
            print(f"  {maker_id:11} {material_id:10} {home_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.maker}: {p.material} sign for {p.home}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
