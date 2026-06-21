#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gloss_flush_underoos_inner_monologue_quest_myth.py
==============================================================================

A standalone story world for a small myth-flavored quest tale: a child hero sets
out to bring a little sacred shine -- the morning gloss -- back to a village in
need. The quest is simple and child-facing, but it is modeled as live state:
the hero carries a vessel through one obstacle, a guide offers a fitting aid,
and the world's constraints decide whether the gloss makes it home safely.

Seed requirements carried into the world
----------------------------------------
* includes the words: "gloss", "flush", "underoos"
* narrative features: inner monologue, quest
* style: myth

World logic
-----------
A village waits for a bright ceremonial gloss gathered from a special place.
The child hero must carry it home in a vessel. One obstacle threatens the trip:

* wind can spill from an open vessel unless a cover is used
* a stream can dump a small carrier unless stepping stones are given
* dark caves can make a child freeze unless a lantern is given

The guide's aid must actually match the obstacle. The Python reasonableness gate
and the ASP twin agree on which combinations are valid.

Run it
------
    python storyworlds/worlds/gpt-5.4/gloss_flush_underoos_inner_monologue_quest_myth.py
    python storyworlds/worlds/gpt-5.4/gloss_flush_underoos_inner_monologue_quest_myth.py --all
    python storyworlds/worlds/gpt-5.4/gloss_flush_underoos_inner_monologue_quest_myth.py --trace
    python storyworlds/worlds/gpt-5.4/gloss_flush_underoos_inner_monologue_quest_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/gloss_flush_underoos_inner_monologue_quest_myth.py --verify
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
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    keeper: str
    gloss_name: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    open_top: bool
    sturdy: bool
    precious: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    risk: str
    danger_line: str
    path_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps_with: str
    use_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    village: str
    need_line: str
    return_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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

    def note(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    hero = world.get("hero")
    vessel = world.get("vessel")
    gloss = world.get("gloss")
    obstacle = world.facts["obstacle_cfg"]
    if gloss.meters["carried"] < THRESHOLD:
        return []
    sig = ("risk", obstacle.id)
    if sig in world.fired:
        return []
    if obstacle.risk == "wind" and vessel.attrs.get("open_top") and not hero.attrs.get("covered"):
        world.fired.add(sig)
        gloss.meters["spilled"] += 1
        hero.memes["sorrow"] += 1
        return ["__spill__"]
    if obstacle.risk == "stream" and not vessel.attrs.get("sturdy") and not hero.attrs.get("crossing_safe"):
        world.fired.add(sig)
        gloss.meters["spilled"] += 1
        hero.memes["sorrow"] += 1
        return ["__spill__"]
    if obstacle.risk == "dark" and not hero.attrs.get("lit_path"):
        world.fired.add(sig)
        hero.memes["fear"] += 1
        hero.meters["halted"] += 1
        return ["__halt__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="risk", tag="physical", apply=_r_spill),
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
    return produced


def matching_aid(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.risk == aid.helps_with


def survives_crossing(vessel: Vessel, obstacle: Obstacle, aid: Aid) -> bool:
    if not matching_aid(obstacle, aid):
        return False
    if obstacle.risk == "wind":
        return (not vessel.open_top) or aid.id == "cover_cloth"
    if obstacle.risk == "stream":
        return vessel.sturdy or aid.id == "stepping_stones"
    if obstacle.risk == "dark":
        return aid.id == "lantern"
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for source_id in SOURCES:
            for vessel_id, vessel in VESSELS.items():
                for obstacle_id, obstacle in OBSTACLES.items():
                    for aid_id, aid in AIDS.items():
                        if survives_crossing(vessel, obstacle, aid):
                            combos.append((setting_id, source_id, vessel_id, obstacle_id, aid_id))
    return combos


def explain_rejection(vessel: Vessel, obstacle: Obstacle, aid: Aid) -> str:
    if not matching_aid(obstacle, aid):
        return (
            f"(No story: {aid.phrase} does not solve {obstacle.phrase}. "
            f"The guide's gift must match the danger on the path.)"
        )
    if obstacle.risk == "wind" and vessel.open_top and aid.id != "cover_cloth":
        return (
            f"(No story: {vessel.phrase} is open at the top, so the wind would blow the gloss out. "
            f"Use the cover cloth or choose a closed vessel.)"
        )
    if obstacle.risk == "stream" and (not vessel.sturdy) and aid.id != "stepping_stones":
        return (
            f"(No story: {vessel.phrase} is too small and tippy for the stream unless the path has "
            f"stepping stones.)"
        )
    if obstacle.risk == "dark" and aid.id != "lantern":
        return (
            f"(No story: a dark cave needs a light. The hero cannot honestly finish the quest "
            f"without a lantern.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_outcome(vessel: Vessel, obstacle: Obstacle, aid: Aid) -> dict[str, bool]:
    return {
        "matched": matching_aid(obstacle, aid),
        "safe": survives_crossing(vessel, obstacle, aid),
    }


def inner_monologue(hero: Entity, obstacle: Obstacle, source: Source) -> str:
    if obstacle.risk == "wind":
        return (
            f'{hero.id} thought, "The sky is kind, but the ridge is wild. '
            f'If I hold steady, I can keep the {source.gloss_name} safe."'
        )
    if obstacle.risk == "stream":
        return (
            f'{hero.id} thought, "The water talks loudly, but I do not have to hurry. '
            f'One good step can be stronger than a hundred splashes."'
        )
    return (
        f'{hero.id} thought, "The cave is dark, and my cheeks flush warm with nerves, '
        f'but brave feet can still walk where kind light leads."'
    )


def quest_setup(world: World, hero: Entity, elder: Entity, source: Source) -> None:
    setting = world.setting
    hero.memes["duty"] += 1
    hero.memes["love"] += 1
    world.say(
        f"In the age when even small villages listened to dawn, {setting.village} waited for a little "
        f"blessing of brightness. {setting.need_line}"
    )
    world.say(
        f"So {hero.id}, the youngest runner of the lane, was given a quest: travel to {source.phrase} "
        f"and bring back {source.gloss_name} for the morning rite."
    )
    world.say(
        f'Under {hero.pronoun("possessive")} travel tunic, {hero.pronoun()} wore {hero.attrs["underoos"]}, '
        f"because a hero, even a small one, likes a secret brave thing close to the heart."
    )
    world.say(
        f'At the gate, {elder.id} the {elder.attrs["title"]} bowed and said, '
        f'"Go gently, little seeker. Bright things love careful hands."'
    )


def gather_gloss(world: World, hero: Entity, source: Source, vessel: Vessel) -> None:
    gloss = world.get("gloss")
    gloss.meters["carried"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"At {source.phrase}, where {source.keeper} was said to wake first each morning, "
        f"{hero.id} cupped {source.gloss_name} into {vessel.phrase}. {source.image}"
    )
    if vessel.precious:
        world.say(f"The little vessel shone with a soft gloss of its own, as if it remembered older stories.")
    world.note("gloss gathered")


def warn_and_gift(world: World, hero: Entity, elder: Entity, obstacle: Obstacle, aid: Aid, vessel: Vessel) -> None:
    pred = predict_outcome(VESSELS[vessel.id], obstacle, aid)
    world.facts["predicted_safe"] = pred["safe"]
    world.say(obstacle.path_line)
    world.say(obstacle.danger_line)
    world.say(inner_monologue(hero, obstacle, world.facts["source_cfg"]))
    world.say(
        f'{elder.id} touched {hero.pronoun("possessive")} shoulder and offered {aid.phrase}. '
        f'"Take this," {elder.pronoun()} said. "{aid.use_line}"'
    )
    world.note("aid offered")


def take_aid(world: World, hero: Entity, aid: Aid) -> None:
    hero.memes["trust"] += 1
    if aid.id == "cover_cloth":
        hero.attrs["covered"] = True
    elif aid.id == "stepping_stones":
        hero.attrs["crossing_safe"] = True
    elif aid.id == "lantern":
        hero.attrs["lit_path"] = True
    world.note(f"aid used:{aid.id}")


def cross_path(world: World, hero: Entity, vessel_ent: Entity, obstacle: Obstacle) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"Then {hero.id} went to meet {obstacle.phrase}."
    )
    markers = propagate(world, narrate=False)
    if "__spill__" in markers:
        vessel_ent.meters["empty"] += 1
        world.say(
            f"But the danger was true. The {world.get('gloss').label} slipped away before {hero.id} could save it, "
            f"and the quest-song in {hero.pronoun('possessive')} chest went quiet."
        )
        world.note("gloss lost")
    elif "__halt__" in markers:
        world.say(
            f"The dark pressed close. {hero.id} stood still, listening to {hero.pronoun('possessive')} own breath, "
            f"and could go no farther."
        )
        world.note("hero halted")
    else:
        world.say(
            f"{hero.id} crossed with patient steps, and the {world.get('gloss').label} stayed bright."
        )
        world.note("crossed safely")


def return_home(world: World, hero: Entity, elder: Entity, source: Source, aid: Aid) -> None:
    setting = world.setting
    gloss = world.get("gloss")
    if gloss.meters["spilled"] >= THRESHOLD or hero.meters["halted"] >= THRESHOLD:
        hero.memes["resolve"] += 1
        world.say(
            f"{hero.id} came back to {setting.village} with empty hands but a truthful voice. "
            f"{elder.id} listened and did not scold."
        )
        world.say(
            f'"A quest is not only for winning," {elder.id} said. "It is also for learning the shape of danger." '
            f'Together they planned a wiser journey for the next dawn.'
        )
        world.say(
            f"That night {hero.id} folded {hero.attrs['underoos']} under the pillow and promised to rise early. "
            f"Even a small heart can begin again."
        )
        world.facts["outcome"] = "failed"
        return
    hero.memes["joy"] += 1
    hero.memes["belonging"] += 1
    gloss.meters["delivered"] += 1
    world.say(
        f"When {hero.id} reached {setting.village}, the people poured the {source.gloss_name} into the waiting bowl. "
        f"{setting.return_line}"
    )
    world.say(
        f"A happy flush rose in the faces around the square, for the dimness had lifted and the village looked young again."
    )
    world.say(
        f"Then {hero.id} laughed, feeling {hero.attrs['underoos']} like a tiny hidden banner of courage, "
        f"while the first light laid a gold gloss over roof, tree, and road."
    )
    world.facts["outcome"] = "delivered"


def tell(
    setting: Setting,
    source: Source,
    vessel: Vessel,
    obstacle: Obstacle,
    aid: Aid,
    hero_name: str = "Nia",
    hero_type: str = "girl",
    elder_type: str = "mother",
    underoos: str = "star underoos",
    trait: str = "careful",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            traits=["small", trait],
            attrs={"underoos": underoos},
            tags={"hero"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="guide",
            label="the elder",
            attrs={"title": "gate-keeper"},
            tags={"guide"},
        )
    )
    vessel_ent = world.add(
        Entity(
            id="vessel",
            type="vessel",
            label=vessel.label,
            phrase=vessel.phrase,
            attrs={"open_top": vessel.open_top, "sturdy": vessel.sturdy},
            tags=set(vessel.tags),
        )
    )
    world.add(
        Entity(
            id="gloss",
            type="gloss",
            label=source.gloss_name,
            phrase=source.gloss_name,
            tags={"gloss"} | set(source.tags),
        )
    )

    quest_setup(world, hero, elder, source)
    world.para()
    gather_gloss(world, hero, source, vessel)
    warn_and_gift(world, hero, elder, obstacle, aid, vessel)
    take_aid(world, hero, aid)
    world.para()
    cross_path(world, hero, vessel_ent, obstacle)
    world.para()
    return_home(world, hero, elder, source, aid)

    world.facts.update(
        hero=hero,
        elder=elder,
        source_cfg=source,
        vessel_cfg=vessel,
        obstacle_cfg=obstacle,
        aid_cfg=aid,
        outcome=world.facts.get("outcome", "failed"),
        used_aid=True,
    )
    return world


SOURCES = {
    "sun_pool": Source(
        id="sun_pool",
        label="Sun Pool",
        phrase="the Sun Pool on the hill",
        keeper="the first bird of morning",
        gloss_name="sun gloss",
        image="The shining drop trembled like a tiny captured sunrise.",
        tags={"gloss", "dawn"},
    ),
    "moon_well": Source(
        id="moon_well",
        label="Moon Well",
        phrase="the Moon Well under the willow",
        keeper="the last silver star",
        gloss_name="moon gloss",
        image="It gleamed pale and calm, like milk stirred with starlight.",
        tags={"gloss", "moon"},
    ),
    "reed_spring": Source(
        id="reed_spring",
        label="Reed Spring",
        phrase="the Reed Spring beside the marsh",
        keeper="the reeds that whispered old names",
        gloss_name="reed gloss",
        image="It shivered green and gold, bright as dragonfly wings.",
        tags={"gloss", "spring"},
    ),
}

VESSELS = {
    "leaf_bowl": Vessel(
        id="leaf_bowl",
        label="leaf bowl",
        phrase="a folded leaf bowl",
        open_top=True,
        sturdy=False,
        precious=False,
        tags={"leaf_bowl"},
    ),
    "shell_cup": Vessel(
        id="shell_cup",
        label="shell cup",
        phrase="a white shell cup",
        open_top=True,
        sturdy=True,
        precious=True,
        tags={"shell_cup"},
    ),
    "lidded_jar": Vessel(
        id="lidded_jar",
        label="lidded jar",
        phrase="a little lidded jar",
        open_top=False,
        sturdy=True,
        precious=False,
        tags={"jar"},
    ),
}

OBSTACLES = {
    "wind_ridge": Obstacle(
        id="wind_ridge",
        label="wind ridge",
        phrase="the Wind Ridge",
        risk="wind",
        danger_line="The ridge was famous for playful gusts that snatched hats, songs, and careless treasures.",
        path_line="Between the hill and home rose the Wind Ridge, all grasses bending one way and then another.",
        tags={"wind"},
    ),
    "stream_ford": Obstacle(
        id="stream_ford",
        label="stream ford",
        phrase="the Singing Ford",
        risk="stream",
        danger_line="The stream was shallow but quick, and little things could be tipped from little hands.",
        path_line="Between the marsh and the village ran the Singing Ford, silver with busy water.",
        tags={"stream"},
    ),
    "echo_cave": Obstacle(
        id="echo_cave",
        label="echo cave",
        phrase="the Echo Cave",
        risk="dark",
        danger_line="Inside, the cave swallowed shape and color until even brave thoughts sounded small.",
        path_line="Between the willow and the village mouth opened the Echo Cave, cool as evening before supper.",
        tags={"dark"},
    ),
}

AIDS = {
    "cover_cloth": Aid(
        id="cover_cloth",
        label="cover cloth",
        phrase="a soft cover cloth",
        helps_with="wind",
        use_line="Lay it over the vessel when the ridge begins to sing.",
        qa_line="covered the vessel so the wind could not snatch the gloss away",
        tags={"cover", "wind"},
    ),
    "stepping_stones": Aid(
        id="stepping_stones",
        label="stepping stones",
        phrase="a string of stepping stones marked with chalk",
        helps_with="stream",
        use_line="Follow the white stones and let the water pass under you instead of around your ankles.",
        qa_line="crossed on stepping stones so the stream could not tip the vessel",
        tags={"stones", "stream"},
    ),
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a firefly lamp",
        helps_with="dark",
        use_line="Hold it low, and the cave will give one step at a time.",
        qa_line="used the lantern to make a safe path through the dark cave",
        tags={"lantern", "light"},
    ),
}

SETTINGS = {
    "dawn_hamlet": Setting(
        id="dawn_hamlet",
        village="Dawn Hamlet",
        need_line="Without the rite, the square felt pale and sleepy, and even the baker's bell sounded soft.",
        return_line="At once the square seemed to wake, as if the houses themselves had opened their eyes.",
        tags={"village"},
    ),
    "reed_village": Setting(
        id="reed_village",
        village="Reed Village",
        need_line="The day's welcome banner hung ready, but it lacked the final bright touch for the festival basin.",
        return_line="At once the festival basin shone, and the reeds beyond the wall answered with a bright hiss.",
        tags={"village"},
    ),
    "hill_gate": Setting(
        id="hill_gate",
        village="Hill Gate",
        need_line="The old stone bowl by the gate was dull, and the morning visitors kept glancing at the gray sky.",
        return_line="At once the old stone bowl blazed gently, and the people at the gate stood straighter in its light.",
        tags={"village"},
    ),
}

GIRL_NAMES = ["Nia", "Tala", "Mira", "Luma", "Suri", "Asha"]
BOY_NAMES = ["Ivo", "Tarin", "Milo", "Kian", "Rami", "Eli"]
TRAITS = ["careful", "steady", "gentle", "thoughtful", "brave"]
UNDEROOS = ["star underoos", "lion underoos", "moon underoos", "striped underoos"]


@dataclass
class StoryParams:
    setting: str
    source: str
    vessel: str
    obstacle: str
    aid: str
    hero_name: str
    hero_type: str
    elder_type: str
    trait: str
    underoos: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "gloss": [
        (
            "What does gloss mean?",
            "Gloss can mean a soft shine on something. In this story it is the bright shining liquid the hero carries home.",
        )
    ],
    "wind": [
        (
            "Why can wind be a problem when you carry something open?",
            "Wind can push, shake, or blow light things away. If a bowl is open, the wind can make the liquid spill out.",
        )
    ],
    "stream": [
        (
            "Why are stepping stones helpful in a stream?",
            "Stepping stones lift your feet above the water. That helps you keep your balance and carry something carefully.",
        )
    ],
    "dark": [
        (
            "Why does a lantern help in a dark place?",
            "A lantern makes a little pool of light. When you can see the ground, it is easier to take calm, safe steps.",
        )
    ],
    "underoos": [
        (
            "What are underoos?",
            "Underoos are underwear. In this story the hero's underoos feel like a secret brave reminder under the travel clothes.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. Someone goes out to find, carry, or fix something important and comes back changed.",
        )
    ],
    "myth": [
        (
            "What is a myth-like story?",
            "A myth-like story sounds old and special, as if the world is full of signs, places with names, and small acts that matter a lot.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp that can be carried by hand. It helps people see in the dark.",
        )
    ],
}
KNOWLEDGE_ORDER = ["gloss", "quest", "myth", "underoos", "wind", "stream", "dark", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    source = f["source_cfg"]
    obstacle = f["obstacle_cfg"]
    return [
        'Write a short myth-like story for a 3-to-5-year-old about a child on a quest. Include the words "gloss", "flush", and "underoos".',
        f"Tell a gentle quest story where {hero.id} must carry {source.gloss_name} home through {obstacle.phrase}, and include one clear line of inner monologue.",
        "Write a child-facing story in an old tale voice where a small hero takes a wise gift, crosses danger carefully, and returns with proof that courage can be quiet.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    source = f["source_cfg"]
    vessel = f["vessel_cfg"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a small child sent on a quest, and {elder.id}, the elder who guides the journey.",
        ),
        (
            f"What was {hero.id}'s quest?",
            f"{hero.id} had to travel to {source.phrase} and bring back {source.gloss_name} to {world.setting.village}. The village needed that bright gloss for its morning rite.",
        ),
        (
            f"Why did {hero.id} wear underoos in the story?",
            f"{hero.id} wore {hero.attrs['underoos']} under the travel tunic as a secret brave thing. They did not give magic power, but they helped {hero.pronoun('object')} feel small and strong at the same time.",
        ),
        (
            f"What danger stood in the way?",
            f"The path led through {obstacle.phrase}. {obstacle.danger_line} That is why the guide had to think about the right kind of help.",
        ),
        (
            f"What aid did {elder.id} give {hero.id}, and why?",
            f"{elder.id} gave {hero.id} {aid.phrase}. {aid.qa_line.capitalize()}, so the danger on the path would not ruin the quest.",
        ),
    ]
    if outcome == "delivered":
        qa.append(
            (
                f"How did {hero.id} succeed?",
                f"{hero.id} listened to good advice, used the gift carefully, and crossed the danger without losing the gloss. Because the aid matched the problem, the quest could end in light instead of loss.",
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"The gloss reached {world.setting.village}, and the whole place seemed to wake up. A happy flush came to the people's faces because the needed brightness had returned.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} finish the quest that day?",
                f"No. The journey failed that morning, but {hero.id} came home honestly and learned what the path required. The elder turned the mistake into a lesson for the next dawn.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"gloss", "quest", "myth", "underoos"}
    obstacle = world.facts["obstacle_cfg"]
    aid = world.facts["aid_cfg"]
    if obstacle.risk == "wind":
        tags.add("wind")
    if obstacle.risk == "stream":
        tags.add("stream")
    if obstacle.risk == "dark":
        tags.add("dark")
    if aid.id == "lantern":
        tags.add("lantern")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    if world.history:
        lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="dawn_hamlet",
        source="sun_pool",
        vessel="leaf_bowl",
        obstacle="wind_ridge",
        aid="cover_cloth",
        hero_name="Nia",
        hero_type="girl",
        elder_type="mother",
        trait="careful",
        underoos="star underoos",
    ),
    StoryParams(
        setting="reed_village",
        source="reed_spring",
        vessel="leaf_bowl",
        obstacle="stream_ford",
        aid="stepping_stones",
        hero_name="Ivo",
        hero_type="boy",
        elder_type="father",
        trait="steady",
        underoos="lion underoos",
    ),
    StoryParams(
        setting="hill_gate",
        source="moon_well",
        vessel="shell_cup",
        obstacle="echo_cave",
        aid="lantern",
        hero_name="Mira",
        hero_type="girl",
        elder_type="mother",
        trait="thoughtful",
        underoos="moon underoos",
    ),
    StoryParams(
        setting="dawn_hamlet",
        source="sun_pool",
        vessel="lidded_jar",
        obstacle="wind_ridge",
        aid="cover_cloth",
        hero_name="Kian",
        hero_type="boy",
        elder_type="father",
        trait="brave",
        underoos="striped underoos",
    ),
]


ASP_RULES = r"""
matches_aid(O, A) :- obstacle(O), aid(A), risk_of(O, R), helps_with(A, R).

safe_vessel_for(wind, V) :- vessel(V), closed(V).
safe_vessel_for(stream, V) :- vessel(V), sturdy(V).
needs_matching_aid(O, A) :- matches_aid(O, A).

survives(V, O, A) :- obstacle(O), aid(A), vessel(V),
                     risk_of(O, wind), closed(V), matches_aid(O, A).
survives(V, O, A) :- obstacle(O), aid(A), vessel(V),
                     risk_of(O, wind), open_top(V), aid(A), aid_id_cover(A), matches_aid(O, A).
survives(V, O, A) :- obstacle(O), aid(A), vessel(V),
                     risk_of(O, stream), sturdy(V), matches_aid(O, A).
survives(V, O, A) :- obstacle(O), aid(A), vessel(V),
                     risk_of(O, stream), not sturdy(V), aid_id_stones(A), matches_aid(O, A).
survives(V, O, A) :- obstacle(O), aid(A), vessel(V),
                     risk_of(O, dark), aid_id_lantern(A), matches_aid(O, A).

valid(S, So, V, O, A) :- setting(S), source(So), survives(V, O, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for source_id in SOURCES:
        lines.append(asp.fact("source", source_id))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        if vessel.open_top:
            lines.append(asp.fact("open_top", vessel_id))
        else:
            lines.append(asp.fact("closed", vessel_id))
        if vessel.sturdy:
            lines.append(asp.fact("sturdy", vessel_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("risk_of", obstacle_id, obstacle.risk))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("helps_with", aid_id, aid.helps_with))
    lines.append(asp.fact("aid_id_cover", "cover_cloth"))
    lines.append(asp.fact("aid_id_stones", "stepping_stones"))
    lines.append(asp.fact("aid_id_lantern", "lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a myth-like child quest for sacred gloss. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["mother", "father"])
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
    if args.obstacle and args.aid and not matching_aid(OBSTACLES[args.obstacle], AIDS[args.aid]):
        raise StoryError(explain_rejection(VESSELS[args.vessel] if args.vessel else VESSELS["leaf_bowl"], OBSTACLES[args.obstacle], AIDS[args.aid]))
    if args.vessel and args.obstacle and args.aid:
        vessel = VESSELS[args.vessel]
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not survives_crossing(vessel, obstacle, aid):
            raise StoryError(explain_rejection(vessel, obstacle, aid))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.source is None or c[1] == args.source)
        and (args.vessel is None or c[2] == args.vessel)
        and (args.obstacle is None or c[3] == args.obstacle)
        and (args.aid is None or c[4] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, vessel_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_type == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    elder_type = args.elder_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    underoos = rng.choice(UNDEROOS)
    return StoryParams(
        setting=setting_id,
        source=source_id,
        vessel=vessel_id,
        obstacle=obstacle_id,
        aid=aid_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        trait=trait,
        underoos=underoos,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        source = SOURCES[params.source]
        vessel = VESSELS[params.vessel]
        obstacle = OBSTACLES[params.obstacle]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})")

    if not survives_crossing(vessel, obstacle, aid):
        raise StoryError(explain_rejection(vessel, obstacle, aid))

    world = tell(
        setting=setting,
        source=source,
        vessel=vessel,
        obstacle=obstacle,
        aid=aid,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
        underoos=params.underoos,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, source, vessel, obstacle, aid) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{part:14}" for part in row))
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
            header = (
                f"### {p.hero_name}: {p.source} in {p.vessel} through {p.obstacle} "
                f"with {p.aid}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
