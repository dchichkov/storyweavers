#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/marble_hatchet_teamwork_transformation_ghost_story.py
=================================================================================

A standalone storyworld for a gentle ghost-story domain built from the seed
words "marble" and "hatchet" with the features Teamwork and Transformation.

Premise
-------
Two children visit an old place at dusk and hear what sounds like a ghost.
The "ghost" is a lonely garden spirit trapped because moonlight cannot reach a
small marble charm hidden in a statue. The children can only help if they work
together: one holds the light or steadies a stool while the other uses a small
hatchet to clear the right kind of wooden blockage. When the charm is reached,
the pale ghost transforms into a warm, glowing helper and the place feels safe.

Why the coverage constraint exists
----------------------------------
This world refuses weak problem/fix pairs. A hatchet is only a sensible tool for
cutting a *wooden* blockage such as vines on a trellis, a fallen branch, or
boards nailed over a window. It is not a good fit for cloth, stone, or locks.
Likewise, the story depends on a true moonlight path: if nothing blocks the
light, there is no ghostly tension and no transformation to resolve.

The world model tracks:
- physical meters: blocked, cut, lit, open
- emotional memes: fear, trust, courage, relief, belonging
- a cooperative beat: one child helps the other perform the fix
- a transformation beat: the ghost changes from pale/scary to warm/friendly

Run it
------
    python storyworlds/worlds/gpt-5.4/marble_hatchet_teamwork_transformation_ghost_story.py
    python storyworlds/worlds/gpt-5.4/marble_hatchet_teamwork_transformation_ghost_story.py --place greenhouse --blockage boards
    python storyworlds/worlds/gpt-5.4/marble_hatchet_teamwork_transformation_ghost_story.py --blockage curtain
    python storyworlds/worlds/gpt-5.4/marble_hatchet_teamwork_transformation_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/marble_hatchet_teamwork_transformation_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/marble_hatchet_teamwork_transformation_ghost_story.py --verify
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
    material: str = ""
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str = ""
    phrase: str = ""
    ghost_home: str = ""
    moon_path: str = ""
    safe_end: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Blockage:
    id: str
    label: str = ""
    phrase: str = ""
    material: str = ""
    where: str = ""
    sound: str = ""
    method: str = ""
    spread: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostKind:
    id: str
    label: str = ""
    first_look: str = ""
    warm_look: str = ""
    voice: str = ""
    wish: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str = ""
    relation_word: str = ""
    opening: str = ""
    closing: str = ""


@dataclass
class Tool:
    id: str
    label: str = ""
    phrase: str = ""
    safe_use: str = ""
    sense: int = 0
    power_vs: set[str] = field(default_factory=set)
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
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_light_reaches_marble(world: World) -> list[str]:
    opening = world.get("opening")
    marble = world.get("marble")
    ghost = world.get("ghost")
    out: list[str] = []
    if opening.meters["open"] < THRESHOLD:
        return out
    if marble.meters["lit"] >= THRESHOLD:
        return out
    sig = ("light", marble.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    marble.meters["lit"] += 1
    ghost.memes["hope"] += 1
    out.append("__light__")
    return out


def _r_ghost_transforms(world: World) -> list[str]:
    marble = world.get("marble")
    ghost = world.get("ghost")
    out: list[str] = []
    if marble.meters["lit"] < THRESHOLD:
        return out
    if ghost.meters["warm"] >= THRESHOLD:
        return out
    sig = ("transform", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["warm"] += 1
    ghost.meters["scary"] = 0.0
    ghost.memes["belonging"] += 1
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="light_reaches_marble", tag="physical", apply=_r_light_reaches_marble),
    Rule(name="ghost_transforms", tag="magical", apply=_r_ghost_transforms),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def blockage_needs_hatchet(blockage: Blockage) -> bool:
    return blockage.material == "wood"


def sensible_tool(tool: Tool) -> bool:
    return tool.sense >= SENSE_MIN


def tool_works(tool: Tool, blockage: Blockage) -> bool:
    return blockage.id in tool.power_vs


def valid_combo(place: Place, blockage: Blockage, tool: Tool) -> bool:
    return blockage_needs_hatchet(blockage) and sensible_tool(tool) and tool_works(tool, blockage)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for blockage_id, blockage in BLOCKAGES.items():
            for tool_id, tool in TOOLS.items():
                if valid_combo(place, blockage, tool):
                    combos.append((place_id, blockage_id, tool_id))
    return combos


def predict_transformation(world: World) -> dict:
    sim = world.copy()
    sim.get("opening").meters["open"] += 1
    propagate(sim, narrate=False)
    return {
        "marble_lit": sim.get("marble").meters["lit"] >= THRESHOLD,
        "ghost_warm": sim.get("ghost").meters["warm"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, helper: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["trust"] += 1
    world.say(
        f"One evening, {a.id} and {b.id} followed {helper.label_word} along the path to {place.phrase}."
    )
    world.say(
        f"The air smelled of damp leaves, and {place.ghost_home}. "
        f"{helper.attrs['opening']}"
    )


def first_sound(world: World, a: Entity, b: Entity, place: Place, blockage: Blockage, ghost: GhostKind) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"Then a thin sound came from inside: {blockage.sound}. "
        f"In the highest window, {ghost.first_look} shivered for a moment and was gone."
    )
    world.say(
        f'"Did you hear that?" whispered {b.id}. {a.id} held still and listened to the hush around {place.label}.'
    )


def explain_legend(world: World, helper: Entity, ghost: GhostKind) -> None:
    world.say(
        f'{helper.label_word.capitalize()} lowered {helper.pronoun("possessive")} voice. '
        f'"People say {ghost.voice}. It only wants one thing: {ghost.wish}."'
    )


def spot_problem(world: World, a: Entity, b: Entity, place: Place, blockage: Blockage) -> None:
    opening = world.get("opening")
    opening.meters["blocked"] += 1
    world.say(
        f"{a.id} looked up and saw {blockage.phrase} {blockage.where}. "
        f"It had shut off {place.moon_path}."
    )
    world.say(
        f'"If the moon cannot get in," {a.id} said, "then the little marble star inside cannot shine."'
    )


def choose_plan(world: World, a: Entity, b: Entity, helper: Entity, tool: Tool, blockage: Blockage) -> None:
    pred = predict_transformation(world)
    world.facts["predicted_lit"] = pred["marble_lit"]
    world.facts["predicted_warm"] = pred["ghost_warm"]
    for kid in (a, b):
        kid.memes["courage"] += 1
    world.say(
        f'{helper.label_word.capitalize()} fetched {tool.phrase}. "{tool.safe_use}," '
        f'{helper.pronoun()} said.'
    )
    world.say(
        f"{a.id} nodded. {b.id} would steady the stool, and {a.id} would clear {blockage.label}. "
        f"Neither child wanted to do it alone."
    )


def clear_blockage(world: World, a: Entity, b: Entity, blockage: Blockage, tool: Tool) -> None:
    opening = world.get("opening")
    blockage_ent = world.get("blockage")
    blockage_ent.meters["cut"] += 1
    opening.meters["open"] += 1
    a.memes["courage"] += 1
    b.memes["courage"] += 1
    b.memes["helping"] += 1
    world.facts["teamwork"] = True
    world.say(
        f"{b.id} gripped the stool with both hands while {a.id} used the {tool.label} to {blockage.method}. "
        f"Bit by bit, {blockage.spread}, and a clean stripe of moonlight slipped through."
    )
    propagate(world, narrate=False)


def reveal_marble(world: World, ghost: GhostKind) -> None:
    marble = world.get("marble")
    if marble.meters["lit"] >= THRESHOLD:
        world.say(
            f"Deep inside the little statue, a blue marble flashed like a tiny moon. "
            f"At once the cold shape by the window stopped trembling."
        )
    if world.get("ghost").meters["warm"] >= THRESHOLD:
        world.say(
            f"The ghost changed before their eyes. {ghost.warm_look} took the place of the pale blur."
        )


def gratitude(world: World, a: Entity, b: Entity, helper: Entity, place: Place, ghost: GhostKind) -> None:
    ghost_ent = world.get("ghost")
    ghost_ent.memes["gratitude"] += 1
    for kid in (a, b):
        kid.memes["belonging"] += 1
    world.say(
        f'"Thank you," sighed the ghost, and now the voice sounded soft instead of hollow. '
        f'"I was only lonely while the moon was shut away."'
    )
    world.say(
        f"{helper.label_word.capitalize()} smiled instead of shivering. "
        f"{place.safe_end}, and the children could see that the ghost was a keeper, not a threat."
    )


def ending_image(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"When they walked home, {a.id} rolled the glowing marble from palm to palm while {b.id} kept one hand on {a.pronoun('possessive')} sleeve. "
        f"Behind them, {place.label} no longer looked haunted. It looked watched over."
    )


def tell(
    place: Place,
    blockage: Blockage,
    ghost_cfg: GhostKind,
    tool_cfg: Tool,
    helper_cfg: Helper,
    leader_name: str,
    leader_gender: str,
    partner_name: str,
    partner_gender: str,
) -> World:
    world = World()
    a = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader", label=leader_name))
    b = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner", label=partner_name))
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.id,
            role="helper",
            label="the helper",
            attrs={"opening": helper_cfg.opening, "closing": helper_cfg.closing},
        )
    )
    world.add(Entity(id="place", type="place", label=place.label, phrase=place.phrase, tags=set(place.tags)))
    world.add(Entity(id="opening", type="window", label="moon window"))
    world.add(
        Entity(
            id="blockage",
            type="blockage",
            label=blockage.label,
            phrase=blockage.phrase,
            material=blockage.material,
            tags=set(blockage.tags),
        )
    )
    world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, tags=set(tool_cfg.tags)))
    world.add(Entity(id="marble", type="marble", label="marble", phrase="a blue marble", tags={"marble", "moon"}))
    world.add(
        Entity(
            id="ghost",
            type="ghost",
            label=ghost_cfg.label,
            phrase=ghost_cfg.label,
            role="ghost",
            tags=set(ghost_cfg.tags),
        )
    )

    world.get("ghost").meters["scary"] += 1
    world.facts["place"] = place
    world.facts["blockage_cfg"] = blockage
    world.facts["ghost_cfg"] = ghost_cfg
    world.facts["tool_cfg"] = tool_cfg
    world.facts["helper_cfg"] = helper_cfg

    introduce(world, a, b, helper, place)
    first_sound(world, a, b, place, blockage, ghost_cfg)
    explain_legend(world, helper, ghost_cfg)

    world.para()
    spot_problem(world, a, b, place, blockage)
    choose_plan(world, a, b, helper, tool_cfg, blockage)

    world.para()
    clear_blockage(world, a, b, blockage, tool_cfg)
    reveal_marble(world, ghost_cfg)

    world.para()
    gratitude(world, a, b, helper, place, ghost_cfg)
    ending_image(world, a, b, place)

    world.facts.update(
        leader=a,
        partner=b,
        helper=helper,
        teamwork=world.facts.get("teamwork", False),
        transformed=world.get("ghost").meters["warm"] >= THRESHOLD,
        marble_lit=world.get("marble").meters["lit"] >= THRESHOLD,
    )
    return world


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="the greenhouse",
        phrase="the old greenhouse at the edge of the orchard",
        ghost_home="glass panes clicked softly in their frames",
        moon_path="the round top window where moonlight used to pour in",
        safe_end="Warm silver light spread through the greenhouse, touching every leaf",
        tags={"garden", "glass"},
    ),
    "tool_shed": Place(
        id="tool_shed",
        label="the tool shed",
        phrase="the old tool shed behind the plum trees",
        ghost_home="the roof boards creaked like sleepy footsteps",
        moon_path="the narrow loft window that faced the moon",
        safe_end="A friendly glow settled over the rafters and old seed jars",
        tags={"shed", "wood"},
    ),
    "chapel_garden": Place(
        id="chapel_garden",
        label="the chapel garden",
        phrase="the small stone garden behind the chapel",
        ghost_home="ivy whispered against the walls and the birdbath shone darkly",
        moon_path="the carved round opening in the garden wall",
        safe_end="The garden brightened until even the shadows looked kind",
        tags={"garden", "stone"},
    ),
}

BLOCKAGES = {
    "vines": Blockage(
        id="vines",
        label="the thick vines",
        phrase="thick dead vines",
        material="wood",
        where="across the window frame",
        sound="tap... scrape... tap",
        method="chop the dry vines away",
        spread="the brittle vines sprang apart",
        tags={"vines", "wood"},
    ),
    "branch": Blockage(
        id="branch",
        label="the fallen branch",
        phrase="a storm-fallen branch",
        material="wood",
        where="wedged against the opening",
        sound="thump... thump against the wall",
        method="cut the branch into lighter pieces",
        spread="the branch loosened and dropped into the grass",
        tags={"branch", "wood"},
    ),
    "boards": Blockage(
        id="boards",
        label="the nailed boards",
        phrase="two old boards",
        material="wood",
        where="nailed over the little round window",
        sound="clack... clack from the loose nails",
        method="pry and chop the rotten boards free",
        spread="the boards cracked and slid away",
        tags={"boards", "wood"},
    ),
    "curtain": Blockage(
        id="curtain",
        label="the curtain",
        phrase="a heavy velvet curtain",
        material="cloth",
        where="hung across the opening",
        sound="swish... swish in the draft",
        method="cut the curtain",
        spread="the cloth fluttered down",
        tags={"cloth"},
    ),
    "stone": Blockage(
        id="stone",
        label="the stone slab",
        phrase="a heavy stone slab",
        material="stone",
        where="leaning over the gap",
        sound="grrr... scrape from the weight shifting",
        method="chip the stone",
        spread="dust fell from the stone",
        tags={"stone"},
    ),
}

GHOSTS = {
    "gardener": GhostKind(
        id="gardener",
        label="the gardener's ghost",
        first_look="a pale figure shaped like a person in a long coat",
        warm_look="A gentle gardener made of moon-mist and leaf-light",
        voice="a small sad voice comes whenever the moon is blocked",
        wish="for moonlight to find the hidden marble again",
        tags={"ghost", "garden"},
    ),
    "keeper": GhostKind(
        id="keeper",
        label="the keeper's ghost",
        first_look="a thin gray shape with hands folded like a worried watchman",
        warm_look="A bright old keeper with kind eyes and silver edges",
        voice="the old keeper murmurs when the place grows too dark",
        wish="for the moon to wake the marble charm in the wall",
        tags={"ghost", "watch"},
    ),
    "child": GhostKind(
        id="child",
        label="the child ghost",
        first_look="a pale little shadow with shining shoes and a bowed head",
        warm_look="A laughing child spirit, soft as candleglow but cooler than mist",
        voice="a lonely child hums when the moon cannot reach the garden",
        wish="for the moonlit marble to shine so it can find its way home",
        tags={"ghost", "child"},
    ),
}

HELPERS = {
    "grandmother": Helper(
        id="grandmother",
        label="the helper",
        relation_word="grandma",
        opening="Grandma said the old place had never liked to be left in the dark.",
        closing="Grandma locked the gate with a smile.",
    ),
    "grandfather": Helper(
        id="grandfather",
        label="the helper",
        relation_word="grandpa",
        opening="Grandpa said the old place only sounded scary because it had something to say.",
        closing="Grandpa tipped his cap to the bright window.",
    ),
}

TOOLS = {
    "hatchet": Tool(
        id="hatchet",
        label="hatchet",
        phrase="a small hatchet with a smooth wooden handle",
        safe_use="We use this together, with steady hands and no rushing",
        sense=3,
        power_vs={"vines", "branch", "boards"},
        tags={"hatchet", "wood"},
    ),
    "toy_hammer": Tool(
        id="toy_hammer",
        label="toy hammer",
        phrase="a little toy hammer from the play basket",
        safe_use="This will not do real work",
        sense=1,
        power_vs=set(),
        tags={"toy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    place: str
    blockage: str
    ghost: str
    tool: str
    helper: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with something spooky in it, like whispers, shadows, or a spirit. In a gentle ghost story, the scary feeling usually turns into understanding."
        )
    ],
    "marble": [
        (
            "What is a marble?",
            "A marble is a small smooth ball, often made of glass or stone. Children can roll it, collect it, or use it in games."
        )
    ],
    "hatchet": [
        (
            "What is a hatchet?",
            "A hatchet is a small chopping tool with a short handle. It is a real tool, so children should only be near one with careful grown-up help."
        )
    ],
    "moon": [
        (
            "Why does moonlight look special at night?",
            "Moonlight looks soft and silver because it is sunlight bouncing off the moon. At night, that pale light can make ordinary things seem mysterious."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job together. One person may hold, steady, watch, or encourage while another person does a different part."
        )
    ],
    "transformation": [
        (
            "What is a transformation in a story?",
            "A transformation is when something changes in an important way. It might look different, feel different, or become kinder or safer than before."
        )
    ],
    "wood": [
        (
            "Why can a hatchet cut vines, branches, or boards better than stone?",
            "A hatchet is made to chop wood and woody stems. Stone is too hard, and cloth or locks need different tools and safer plans."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "marble", "hatchet", "moon", "teamwork", "transformation", "wood"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["leader"]
    b = f["partner"]
    place = f["place"]
    blockage = f["blockage_cfg"]
    ghost = f["ghost_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "marble" and "hatchet".',
        f"Tell a spooky-but-safe story where {a.id} and {b.id} work together in {place.label} to help {ghost.label}.",
        f"Write a story about teamwork and transformation in which moonlight reaches a hidden marble after children clear {blockage.label}.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["partner"]
    helper = f["helper"]
    place = f["place"]
    blockage = f["blockage_cfg"]
    ghost = f["ghost_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, who visit {place.label} with {helper.label_word}. They meet {ghost.label} and learn it is lonely rather than mean."
        ),
        (
            f"Why did {place.label} seem haunted at first?",
            f"It seemed haunted because strange sounds came from inside and the children saw {ghost.first_look}. The blocked moonlight made the ghost look pale and frightening instead of warm."
        ),
        (
            "What was blocking the moonlight?",
            f"{blockage.phrase.capitalize()} was {blockage.where}, shutting off the moon's path. That kept the hidden marble charm from lighting up."
        ),
        (
            f"How did {a.id} and {b.id} use teamwork?",
            f"{b.id} steadied the stool while {a.id} used the hatchet to {blockage.method}. They needed each other because the job had to be done carefully and without rushing."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                "What changed when the marble caught the moonlight?",
                f"The blue marble flashed, and the ghost transformed from a scary pale shape into {ghost.warm_look.lower()}. The whole place felt safe because the spirit was no longer trapped in the dark."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children walking home while the once-haunted place glowed softly behind them. The ending shows what changed: fear turned into comfort, and the ghost became a friendly keeper."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "marble", "hatchet", "moon", "teamwork", "transformation", "wood"}
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.material:
            parts.append(f"material={ent.material}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="greenhouse",
        blockage="vines",
        ghost="gardener",
        tool="hatchet",
        helper="grandmother",
        leader="Lily",
        leader_gender="girl",
        partner="Tom",
        partner_gender="boy",
    ),
    StoryParams(
        place="tool_shed",
        blockage="branch",
        ghost="keeper",
        tool="hatchet",
        helper="grandfather",
        leader="Ben",
        leader_gender="boy",
        partner="Mia",
        partner_gender="girl",
    ),
    StoryParams(
        place="chapel_garden",
        blockage="boards",
        ghost="child",
        tool="hatchet",
        helper="grandmother",
        leader="Zoe",
        leader_gender="girl",
        partner="Nora",
        partner_gender="girl",
    ),
]


def explain_rejection(blockage: Blockage, tool: Tool) -> str:
    if not blockage_needs_hatchet(blockage):
        return (
            f"(No story: {blockage.label} is {blockage.material}, so a hatchet is not a sensible fix. "
            f"This world only allows wooden blockages that the tool can honestly clear.)"
        )
    if not sensible_tool(tool):
        return (
            f"(No story: {tool.label} is not a sensible real fix here. "
            f"The children need a tool that can truly open the moon path.)"
        )
    if not tool_works(tool, blockage):
        return (
            f"(No story: {tool.label} does not actually work on {blockage.label} in this world.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
needs_hatchet(B) :- material(B, wood).
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
works(T, B)      :- power_vs(T, B).
valid(P, B, T)   :- place(P), blockage(B), tool(T), needs_hatchet(B), sensible_tool(T), works(T, B).

% --- consequence model -----------------------------------------------------
opening_open :- chosen_blockage(B), chosen_tool(T), valid(_, B, T).
marble_lit   :- opening_open.
ghost_warm   :- marble_lit.

outcome(transformed) :- ghost_warm.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for blockage_id, blockage in BLOCKAGES.items():
        lines.append(asp.fact("blockage", blockage_id))
        lines.append(asp.fact("material", blockage_id, blockage.material))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for target in sorted(tool.power_vs):
            lines.append(asp.fact("power_vs", tool_id, target))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_blockage", params.blockage),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit() -> None:
    sample = generate(CURATED[0])
    emit(sample, trace=False, qa=False, header="")


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

    for params in CURATED:
        py = "transformed" if valid_combo(PLACES[params.place], BLOCKAGES[params.blockage], TOOLS[params.tool]) else "?"
        asp_out = asp_outcome(params)
        if py != asp_out:
            rc = 1
            print(f"MISMATCH outcome for curated case {params}: python={py} asp={asp_out}")

    try:
        _smoke_emit()
        print("OK: smoke generate/emit passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost story world: children work together to clear moonlight so a ghost can transform."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.blockage and args.tool:
        blockage = BLOCKAGES[args.blockage]
        tool = TOOLS[args.tool]
        if not valid_combo(PLACES[args.place] if args.place else next(iter(PLACES.values())), blockage, tool):
            raise StoryError(explain_rejection(blockage, tool))
    if args.tool and not sensible_tool(TOOLS[args.tool]):
        raise StoryError(explain_rejection(BLOCKAGES[args.blockage] if args.blockage else BLOCKAGES["vines"], TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.blockage is None or combo[1] == args.blockage)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, blockage_id, tool_id = rng.choice(sorted(combos))
    ghost_id = args.ghost or rng.choice(sorted(GHOSTS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    leader_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    leader = _pick_name(rng, leader_gender)
    partner = _pick_name(rng, partner_gender, avoid=leader)
    return StoryParams(
        place=place_id,
        blockage=blockage_id,
        ghost=ghost_id,
        tool=tool_id,
        helper=helper_id,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        blockage = BLOCKAGES[params.blockage]
        ghost = GHOSTS[params.ghost]
        tool = TOOLS[params.tool]
        helper = HELPERS[params.helper]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from None

    if not valid_combo(place, blockage, tool):
        raise StoryError(explain_rejection(blockage, tool))

    world = tell(
        place=place,
        blockage=blockage,
        ghost_cfg=ghost,
        tool_cfg=tool,
        helper_cfg=helper,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
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
        print(f"{len(combos)} compatible (place, blockage, tool) combos:\n")
        for place, blockage, tool in combos:
            print(f"  {place:14} {blockage:10} {tool}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader} & {p.partner}: {p.blockage} at {p.place} ({p.ghost})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
