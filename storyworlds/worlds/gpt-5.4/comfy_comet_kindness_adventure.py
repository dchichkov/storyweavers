#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/comfy_comet_kindness_adventure.py
============================================================

A standalone story world for a gentle adventure about helping a little comet.
The child-facing core is simple: a child finds a fallen comet in trouble,
chooses a kind, comfy way to help it, faces one adventure obstacle on the way
to a high place, and learns that kindness can help lost things shine again.

The world model keeps two linked dimensions:

* physical meters: glow, warmth, comfort, distance, delay
* emotional memes: fear, hope, trust, bravery, gratitude

Reasonableness gate
-------------------
Not every swap makes sense. A valid story needs both:

* a comfort that honestly helps the comet's trouble
* an adventure tool that can honestly handle the obstacle on the route

So this world rejects combinations like using a lantern to cut brambles, or a
lullaby to warm a freezing comet.

Run it
------
    python storyworlds/worlds/gpt-5.4/comfy_comet_kindness_adventure.py
    python storyworlds/worlds/gpt-5.4/comfy_comet_kindness_adventure.py --place meadow --trouble cold --comfort quilt
    python storyworlds/worlds/gpt-5.4/comfy_comet_kindness_adventure.py --obstacle brambles --tool lantern
    python storyworlds/worlds/gpt-5.4/comfy_comet_kindness_adventure.py --all
    python storyworlds/worlds/gpt-5.4/comfy_comet_kindness_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/comfy_comet_kindness_adventure.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    glowing: bool = False
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
    high_place: str
    sky_image: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    symptom: str
    need: str
    severity: int
    opening_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    gives: set[str]
    strength: int
    action: str
    afterglow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    challenge: str
    need: str
    difficulty: int
    risk_line: str
    cross_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str]
    power: int
    use_line: str
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


def _r_comfy_restores_glow(world: World) -> list[str]:
    out: list[str] = []
    comet = world.get("comet")
    if comet.meters["comfort"] < THRESHOLD:
        return out
    sig = ("comfort_glow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    comet.meters["glow"] += 1
    comet.memes["hope"] += 1
    comet.memes["fear"] = 0.0
    out.append("__comfort__")
    return out


def _r_arrival_builds_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    comet = world.get("comet")
    if hero.meters["arrived"] < THRESHOLD:
        return out
    sig = ("arrival",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    comet.memes["trust"] += 1
    out.append("__arrival__")
    return out


CAUSAL_RULES = [
    Rule("comfort_glow", "emotional", _r_comfy_restores_glow),
    Rule("arrival", "social", _r_arrival_builds_bravery),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "meadow": Place(
        "meadow",
        "the moon-bright meadow",
        "silver grass and sleepy daisies",
        "the round hill above the meadow",
        "where the stars looked close enough to whisper to",
        affords={"stream", "brambles"},
    ),
    "cliffs": Place(
        "cliffs",
        "the path below the windy sea cliffs",
        "a sandy path with lighthouse shadows",
        "the lighthouse knoll",
        "where the dark sea and the sky touched in one shining line",
        affords={"wind", "dark_path"},
    ),
    "garden": Place(
        "garden",
        "the sleeping garden behind the cottages",
        "rows of moonlit herbs and quiet bean poles",
        "the old sundial hill",
        "where the flower heads nodded under the stars",
        affords={"brambles", "dark_path"},
    ),
}

TROUBLES = {
    "cold": Trouble(
        "cold",
        "cold",
        "Its little tail gave only a weak silver shiver.",
        "warm",
        2,
        "The comet looked small and cold, as if night dew had soaked the heat right out of it.",
        tags={"cold", "kindness"},
    ),
    "tired": Trouble(
        "tired",
        "tired",
        "Its glow blinked on and off like sleepy eyes.",
        "soft",
        2,
        "The comet looked very tired, as if it had flown too far and fallen right out of the sky.",
        tags={"sleep", "kindness"},
    ),
    "scared": Trouble(
        "scared",
        "scared",
        "It tucked its tail close and trembled whenever the night made a sound.",
        "calm",
        1,
        "The comet looked more frightened than hurt, as if the whole wide world had become too big at once.",
        tags={"feelings", "kindness"},
    ),
}

COMFORTS = {
    "quilt": Comfort(
        "quilt",
        "patchwork quilt",
        "a comfy patchwork quilt",
        {"warm", "soft"},
        2,
        "wrapped the comet in the comfy patchwork quilt and held the corners close",
        "The cloth made a tiny nest, and the comet's silver glow began to breathe more steadily.",
        tags={"warmth", "blanket"},
    ),
    "scarf": Comfort(
        "scarf",
        "wool scarf",
        "a wool scarf",
        {"warm"},
        1,
        "looped the wool scarf around the comet like a little cloud",
        "The scarf kept the night air off, and the comet stopped shivering so hard.",
        tags={"warmth", "clothes"},
    ),
    "pillow": Comfort(
        "pillow",
        "travel pillow",
        "a small travel pillow",
        {"soft"},
        1,
        "settled the comet onto the small pillow so it could rest its bright little head",
        "The soft pillow gave the comet a place to rest, and its tail uncurled a little.",
        tags={"sleep", "soft"},
    ),
    "lullaby": Comfort(
        "lullaby",
        "lullaby",
        "a hush-soft lullaby",
        {"calm"},
        1,
        "sang a hush-soft lullaby until the comet listened instead of trembling",
        "The gentle song smoothed the fear from the air, and the comet peeped out with trust instead of panic.",
        tags={"song", "feelings"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        "stream",
        "stream",
        "a silver stream that chattered over slippery stones",
        "cross",
        2,
        "The stream curled between them and the hill, too quick to splash through with a fragile comet in their arms.",
        "Past the stream, the hill rose toward the stars.",
        tags={"water", "adventure"},
    ),
    "brambles": Obstacle(
        "brambles",
        "brambles",
        "a wall of blackberry brambles with hooked thorns",
        "clear",
        1,
        "The brambles snagged at sleeves and would surely scratch a tiny comet's tail.",
        "Beyond the brambles, the path opened clean and safe.",
        tags={"plants", "adventure"},
    ),
    "wind": Obstacle(
        "wind",
        "wind",
        "a windy bridge where gusts pushed sideways",
        "steady",
        2,
        "The wind shoved hard enough to make even brave feet wobble.",
        "On the far side, the night felt wide and possible again.",
        tags={"weather", "adventure"},
    ),
    "dark_path": Obstacle(
        "dark_path",
        "dark path",
        "a tunnel of pines where the path went dark as a pocket",
        "light",
        1,
        "Without light, one wrong step could send them off the path and away from the hill.",
        "Once the path was bright, every turn seemed to point upward.",
        tags={"dark", "adventure"},
    ),
}

TOOLS = {
    "stepping_stones": Tool(
        "stepping_stones",
        "stepping stones",
        "flat stepping stones",
        {"cross"},
        2,
        "found a line of flat stepping stones and crossed the stream one careful hop at a time",
        tags={"water", "path"},
    ),
    "gloves": Tool(
        "gloves",
        "garden gloves",
        "thick garden gloves",
        {"clear"},
        1,
        "pulled on thick garden gloves and bent the thorny branches aside",
        tags={"plants", "hands"},
    ),
    "rope": Tool(
        "rope",
        "guide rope",
        "a guide rope tied low along the bridge rail",
        {"steady"},
        2,
        "held the guide rope with one hand and leaned into the gusts until the bridge stopped feeling wild",
        tags={"weather", "bridge"},
    ),
    "lantern": Tool(
        "lantern",
        "paper lantern",
        "a paper lantern",
        {"light"},
        1,
        "lit the paper lantern so the pine path shone gold instead of black",
        tags={"light", "night"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["gentle", "brave", "curious", "kind", "steady", "thoughtful"]


def comfort_helps(trouble: Trouble, comfort: Comfort) -> bool:
    return trouble.need in comfort.gives


def tool_handles(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.need in tool.handles and tool.power >= obstacle.difficulty


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for trouble_id, trouble in TROUBLES.items():
            for comfort_id, comfort in COMFORTS.items():
                if not comfort_helps(trouble, comfort):
                    continue
                for obstacle_id in sorted(place.affords):
                    obstacle = OBSTACLES[obstacle_id]
                    for tool_id, tool in TOOLS.items():
                        if tool_handles(obstacle, tool):
                            combos.append((place_id, trouble_id, comfort_id, tool_id))
    return sorted(set(combos))


def outcome_for(trouble: Trouble, comfort: Comfort) -> str:
    return "tonight" if comfort.strength >= trouble.severity else "dawn"


def explain_comfort_rejection(trouble: Trouble, comfort: Comfort) -> str:
    need_map = {"warm": "warmth", "soft": "rest", "calm": "gentleness"}
    gives = ", ".join(sorted(comfort.gives))
    return (
        f"(No story: {comfort.phrase} offers {gives}, but a {trouble.label} comet needs "
        f"{need_map.get(trouble.need, trouble.need)}. Pick a comfort that honestly helps.)"
    )


def explain_tool_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} does not safely handle {obstacle.challenge}. "
        f"This obstacle needs something that can {obstacle.need}.)"
    )


def predict_homecome(world: World, trouble: Trouble, comfort: Comfort) -> dict:
    sim = world.copy()
    comet = sim.get("comet")
    hero = sim.get("hero")
    comet.meters["comfort"] += 1
    propagate(sim, narrate=False)
    hero.meters["arrived"] += 1
    propagate(sim, narrate=False)
    return {
        "glow": comet.meters["glow"],
        "hope": comet.memes["hope"],
        "outcome": outcome_for(trouble, comfort),
    }


def introduce(world: World, hero: Entity, parent: Entity, place: Place) -> None:
    trait = next((t for t in hero.traits if t), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"On a clear night, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} walked through "
        f"{place.opening}. {hero.id} was a {desc} who always looked up when the sky seemed busy."
    )


def discover(world: World, hero: Entity, comet: Entity, trouble: Trouble) -> None:
    hero.memes["wonder"] += 1
    comet.memes["fear"] += 1
    world.say(
        f"Then a streak of silver dipped low, spun once, and landed in the grass with a puff of sparkles. "
        f"It was not a stone at all, but a tiny comet no bigger than a kitten. {trouble.opening_line}"
    )
    world.say(trouble.symptom)
    world.say(
        f'{hero.id} knelt at once. "Don\'t worry," {hero.pronoun()} whispered. '
        f'"We will help you."'
    )


def choose_kindness(world: World, hero: Entity, comet: Entity, comfort: Comfort, trouble: Trouble) -> None:
    pred = predict_homecome(world, trouble, comfort)
    world.facts["predicted_outcome"] = pred["outcome"]
    world.facts["predicted_glow"] = pred["glow"]
    comet.meters["comfort"] += 1
    if trouble.need == "warm":
        comet.meters["warmth"] += comfort.strength
    elif trouble.need == "soft":
        comet.meters["rest"] += comfort.strength
    elif trouble.need == "calm":
        comet.meters["peace"] += comfort.strength
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} {comfort.action}. {comfort.afterglow}"
    )
    if comet.memes["hope"] >= THRESHOLD:
        world.say(
            f"The little comet blinked up at {hero.id} and trusted {hero.pronoun('object')} enough to stop hiding its face."
        )


def decide_journey(world: World, hero: Entity, parent: Entity, place: Place, obstacle: Obstacle) -> None:
    hero.memes["bravery"] += 1
    parent.memes["care"] += 1
    world.say(
        f'"If we can bring it to {place.high_place}," said {hero.id}\'s {parent.label_word}, '
        f'"maybe it can find the sky again."'
    )
    world.say(
        f"They set off together, but the way held {obstacle.challenge}. "
        f"{obstacle.risk_line}"
    )


def solve_obstacle(world: World, hero: Entity, comet: Entity, obstacle: Obstacle, tool: Tool) -> None:
    hero.meters["distance"] += 1
    hero.meters["progress"] += 1
    comet.meters["progress"] += 1
    world.say(
        f"{hero.id} {tool.use_line}. {obstacle.cross_line}"
    )


def arrive(world: World, hero: Entity, comet: Entity, place: Place) -> None:
    hero.meters["arrived"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {place.high_place}, {place.sky_image}. There the little comet lifted its face to the night."
    )


def ending_tonight(world: World, hero: Entity, comet: Entity, place: Place) -> None:
    comet.meters["glow"] += 1
    comet.memes["gratitude"] += 1
    world.say(
        f"The glow inside it swelled from a blink to a brave silver lantern. With one soft bounce, the comet rose from "
        f"{hero.id}'s hands, circled once above {place.high_place}, and shot upward."
    )
    world.say(
        f"It drew a bright ribbon across the dark, like a thank-you written on the sky. A warm spark drifted down into "
        f"{hero.id}'s palm before the comet hurried home."
    )


def ending_dawn(world: World, hero: Entity, parent: Entity, comet: Entity, place: Place, comfort: Comfort) -> None:
    comet.meters["delay"] += 1
    comet.memes["gratitude"] += 1
    world.say(
        f"The comet tried to rise, but its glow was still too sleepy for the long climb. So {hero.id}'s {parent.label_word} "
        f"made a tiny nest from {comfort.phrase}, and they stayed on {place.high_place} together until the world turned pale."
    )
    world.say(
        f"When dawn touched the sky pink and gold, the comet finally gleamed bright enough. It lifted slowly, dipped in a thankful bow, "
        f"and sailed upward, leaving one last silver wink above the hill."
    )


def tell(place: Place, trouble: Trouble, comfort: Comfort, obstacle: Obstacle, tool: Tool,
         hero_name: str = "Lily", hero_type: str = "girl", trait: str = "kind",
         parent_type: str = "mother") -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, role="hero", traits=[trait], label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    comet = world.add(Entity(id="comet", kind="thing", type="comet", role="comet", label="little comet", glowing=True, portable=True))
    hero.attrs["name"] = hero_name
    parent.attrs["title"] = parent.label_word
    comet.meters["glow"] = 1.0

    introduce(world, hero, parent, place)
    discover(world, hero, comet, trouble)

    world.para()
    choose_kindness(world, hero, comet, comfort, trouble)
    decide_journey(world, hero, parent, place, obstacle)

    world.para()
    solve_obstacle(world, hero, comet, obstacle, tool)
    arrive(world, hero, comet, place)

    world.para()
    if outcome_for(trouble, comfort) == "tonight":
        ending_tonight(world, hero, comet, place)
    else:
        ending_dawn(world, hero, parent, comet, place, comfort)

    world.facts.update(
        hero=hero,
        hero_name=hero_name,
        parent=parent,
        comet=comet,
        place=place,
        trouble=trouble,
        comfort=comfort,
        obstacle=obstacle,
        tool=tool,
        outcome=outcome_for(trouble, comfort),
        comfy="comfy" in comfort.phrase or comfort.id == "quilt",
        grateful=comet.memes["gratitude"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "comet": [("What is a comet?",
               "A comet is a small icy body in space that can glow with a bright tail when it travels near the sun.")],
    "kindness": [("What is kindness?",
                  "Kindness is choosing to help, comfort, or care for someone. It can make others feel safer and less alone.")],
    "blanket": [("Why can a blanket feel comfy?",
                 "A blanket can feel comfy because it is soft and warm. It can help a cold or tired body relax.")],
    "song": [("Why can a gentle song help someone feel calm?",
              "A gentle song is soft and steady, so it can make a frightened heart slow down and feel safer.")],
    "lantern": [("What does a lantern do?",
                 "A lantern makes light so people can see where they are going in the dark.")],
    "rope": [("Why is a rope useful on a windy bridge?",
              "A rope gives your hand something steady to hold. That helps you keep your balance when the wind pushes.")],
    "gloves": [("Why do gloves help with thorny plants?",
                "Gloves protect your hands from scratches and prickles when you move thorny branches aside.")],
    "stones": [("Why are stepping stones useful in a stream?",
                "Stepping stones give you dry places to put your feet, so you can cross water more safely.")],
}
KNOWLEDGE_ORDER = ["comet", "kindness", "blanket", "song", "lantern", "rope", "gloves", "stones"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    comfort = f["comfort"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    place = f["place"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "comfy" and "comet" and centers on kindness.',
        f"Tell a gentle night adventure where a {hero.type} finds a {trouble.label} little comet in {place.opening}, helps it with {comfort.phrase}, and keeps going through {obstacle.challenge} using {tool.phrase}.",
        f"Write a child-facing story where kindness changes the ending: the hero comforts a lost comet before trying to bring it to {place.high_place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    hero_name = f["hero_name"]
    trouble = f["trouble"]
    comfort = f["comfort"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {hero_name}, {hero.pronoun('possessive')} {parent.label_word}, and a little comet that had fallen from the sky."),
        ("What problem did the comet have?",
         f"The comet was {trouble.label}. {trouble.symptom}"),
        (f"How did {hero_name} show kindness to the comet?",
         f"{hero_name} helped with {comfort.phrase}. That kindness matched what the comet needed, so it felt safer and began to shine more steadily."),
        ("Why was the trip an adventure?",
         f"They had to carry the comet to {place.high_place} and face {obstacle.challenge} on the way. The obstacle made the journey feel brave instead of easy."),
        (f"How did they get past {obstacle.label}?",
         f"They used {tool.phrase}. That worked because {tool.phrase} could honestly handle the problem of {obstacle.challenge}."),
    ]
    if outcome == "tonight":
        qa.append((
            "How did the story end?",
            f"The comet flew home that same night. It had enough comfort and hope to shine brightly again, so it could climb back into the sky."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The comet rested until dawn and then flew home. Kindness helped it recover, but it still needed a little more time before it was strong enough to rise."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"comet", "kindness"}
    comfort = f["comfort"]
    tool = f["tool"]
    if comfort.id == "quilt":
        tags.add("blanket")
    if comfort.id == "lullaby":
        tags.add("song")
    if tool.id == "lantern":
        tags.add("lantern")
    if tool.id == "rope":
        tags.add("rope")
    if tool.id == "gloves":
        tags.add("gloves")
    if tool.id == "stepping_stones":
        tags.add("stones")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    trouble: str
    comfort: str
    obstacle: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("meadow", "cold", "quilt", "stream", "stepping_stones", "Lily", "girl", "mother", "kind"),
    StoryParams("cliffs", "scared", "lullaby", "wind", "rope", "Ben", "boy", "father", "brave"),
    StoryParams("garden", "tired", "pillow", "dark_path", "lantern", "Mia", "girl", "mother", "gentle"),
    StoryParams("garden", "cold", "scarf", "brambles", "gloves", "Theo", "boy", "father", "thoughtful"),
]


ASP_RULES = r"""
helps(C, T) :- comfort(C), trouble(T), need(T, N), gives(C, N).
handles(Tool, O) :- tool(Tool), obstacle(O), requires(O, N), does(Tool, N), power(Tool, P), difficulty(O, D), P >= D.
valid(Place, T, C, Tool) :- place(Place), affords(Place, O), trouble(T), comfort(C), tool(Tool), helps(C, T), handles(Tool, O).

strong_enough(C, T) :- chosen_comfort(C), chosen_trouble(T), strength(C, S), severity(T, V), S >= V.
outcome(tonight) :- strong_enough(C, T), chosen_comfort(C), chosen_trouble(T).
outcome(dawn) :- chosen_comfort(C), chosen_trouble(T), not strong_enough(C, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for oid in sorted(p.affords):
            lines.append(asp.fact("affords", pid, oid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("need", tid, t.need))
        lines.append(asp.fact("severity", tid, t.severity))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("strength", cid, c.strength))
        for g in sorted(c.gives):
            lines.append(asp.fact("gives", cid, g))
    for oid, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("requires", oid, o.need))
        lines.append(asp.fact("difficulty", oid, o.difficulty))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
        for h in sorted(t.handles):
            lines.append(asp.fact("does", tid, h))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_comfort", params.comfort),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    cases = list(CURATED)
    for p in cases:
        if asp_outcome(p) != outcome_for(TROUBLES[p.trouble], COMFORTS[p.comfort]):
            rc = 1
            print("MISMATCH in outcome:", p)
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated stories.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a comfy comet kindness adventure. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.comfort:
        if not comfort_helps(TROUBLES[args.trouble], COMFORTS[args.comfort]):
            raise StoryError(explain_comfort_rejection(TROUBLES[args.trouble], COMFORTS[args.comfort]))
    if args.obstacle and args.tool:
        if not tool_handles(OBSTACLES[args.obstacle], TOOLS[args.tool]):
            raise StoryError(explain_tool_rejection(OBSTACLES[args.obstacle], TOOLS[args.tool]))
    if args.place and args.obstacle and args.obstacle not in PLACES[args.place].affords:
        raise StoryError(f"(No story: {PLACES[args.place].label} does not include {OBSTACLES[args.obstacle].challenge} on the route.)")

    combos = []
    for place_id, trouble_id, comfort_id, tool_id in valid_combos():
        place = PLACES[place_id]
        if args.place is not None and place_id != args.place:
            continue
        if args.trouble is not None and trouble_id != args.trouble:
            continue
        if args.comfort is not None and comfort_id != args.comfort:
            continue
        if args.tool is not None and tool_id != args.tool:
            continue
        possible_obstacles = [oid for oid in sorted(place.affords)
                              if (args.obstacle is None or oid == args.obstacle)
                              and tool_handles(OBSTACLES[oid], TOOLS[tool_id])]
        for obstacle_id in possible_obstacles:
            combos.append((place_id, trouble_id, comfort_id, obstacle_id, tool_id))

    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, trouble_id, comfort_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place_id, trouble_id, comfort_id, obstacle_id, tool_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TROUBLES[params.trouble],
        COMFORTS[params.comfort],
        OBSTACLES[params.obstacle],
        TOOLS[params.tool],
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.name),
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
        print(f"{len(combos)} compatible (place, trouble, comfort, tool) combos:\n")
        for place, trouble, comfort, tool in combos:
            print(f"  {place:8} {trouble:6} {comfort:8} {tool}")
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
            header = f"### {p.name}: {p.trouble} comet at {p.place} ({p.comfort}, {p.obstacle}, {p.tool}, {outcome_for(TROUBLES[p.trouble], COMFORTS[p.comfort])})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
