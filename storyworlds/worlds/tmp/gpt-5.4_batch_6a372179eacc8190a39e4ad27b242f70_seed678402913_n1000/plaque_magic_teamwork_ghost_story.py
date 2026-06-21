#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/plaque_magic_teamwork_ghost_story.py
===============================================================

A small storyworld about two children, a haunted plaque, and the way teamwork
turns a scary ghost story into a gentle ending. The children find an old plaque
whose faded words keep a lonely ghost restless. Magic stirs the air, but the
solution is practical and kind: the children work together to reveal the words,
read the forgotten name, and help the ghost rest.

Run it
------
python storyworlds/worlds/gpt-5.4/plaque_magic_teamwork_ghost_story.py
python storyworlds/worlds/gpt-5.4/plaque_magic_teamwork_ghost_story.py --place school_hall --ghost caretaker
python storyworlds/worlds/gpt-5.4/plaque_magic_teamwork_ghost_story.py --tool feather_duster
python storyworlds/worlds/gpt-5.4/plaque_magic_teamwork_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/plaque_magic_teamwork_ghost_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/plaque_magic_teamwork_ghost_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "librarian"}
        male = {"boy", "man", "father", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    opening: str
    plaque_spot: str
    night_sound: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    label: str
    type: str
    title: str
    whisper: str
    loss: str
    thanks: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    reveals_letters: bool = False
    sense: int = 2
    sparkle: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Bond:
    id: str
    line: str
    teamwork_gain: int
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "kid"]

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


def _r_whisper(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    room = world.get("room")
    if ghost.meters["restless"] >= THRESHOLD:
        sig = ("whisper", "ghost")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["cold"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__whisper__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    plaque = world.get("plaque")
    tool = world.get("tool")
    if plaque.meters["cleaned"] >= THRESHOLD and tool.attrs.get("reveals_letters"):
        sig = ("reveal", "plaque")
        if sig not in world.fired:
            world.fired.add(sig)
            plaque.meters["readable"] += 1
            out.append("__readable__")
    return out


def _r_name_soothes(world: World) -> list[str]:
    out: list[str] = []
    plaque = world.get("plaque")
    ghost = world.get("ghost")
    if plaque.meters["name_spoken"] >= THRESHOLD and ghost.meters["restless"] >= THRESHOLD:
        sig = ("soothe", "ghost")
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["restless"] = 0.0
            ghost.meters["glowing"] += 1
            room = world.get("room")
            room.meters["cold"] = 0.0
            for kid in world.kids():
                kid.memes["fear"] = 0.0
                kid.memes["relief"] += 1
            out.append("__soothed__")
    return out


CAUSAL_RULES = [
    Rule(name="whisper", tag="magic", apply=_r_whisper),
    Rule(name="reveal", tag="physical", apply=_r_reveal),
    Rule(name="name_soothes", tag="magic", apply=_r_name_soothes),
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


def valid_combo(place: Place, ghost: Ghost, tool: Tool) -> bool:
    return tool.reveals_letters and tool.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for ghost_id, ghost in GHOSTS.items():
            for tool_id, tool in TOOLS.items():
                if valid_combo(place, ghost, tool):
                    combos.append((place_id, ghost_id, tool_id))
    return combos


def teamwork_succeeds(bond: Bond, courage: int) -> bool:
    return bond.teamwork_gain + courage >= 4


def outcome_of(params: "StoryParams") -> str:
    tool = TOOLS[params.tool]
    bond = BONDS[params.bond]
    if not valid_combo(PLACES[params.place], GHOSTS[params.ghost], tool):
        return "invalid"
    return "peaceful" if teamwork_succeeds(bond, params.courage) else "frightened"


def explain_tool(tool: Tool) -> str:
    if not tool.reveals_letters:
        return (
            f"(No story: {tool.phrase} may touch the plaque, but it does not reveal the faded words. "
            "This world needs a tool that can help the children read the plaque together.)"
        )
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). Pick a calmer, more useful tool.)"
        )
    return "(No story: that tool does not fit this world.)"


def predict_with_tool(world: World, tool: Tool) -> dict:
    sim = world.copy()
    sim.get("tool").attrs["reveals_letters"] = tool.reveals_letters
    sim.get("tool").label = tool.label
    sim.get("tool").phrase = tool.phrase
    sim.get("plaque").meters["cleaned"] += 1
    propagate(sim, narrate=False)
    return {
        "readable": sim.get("plaque").meters["readable"] >= THRESHOLD,
        "cold": sim.get("room").meters["cold"],
    }


def setup_scene(world: World, place: Place, kid1: Entity, kid2: Entity) -> None:
    for kid in (kid1, kid2):
        kid.memes["curiosity"] += 1
    world.say(
        f"One dusky evening, {kid1.id} and {kid2.id} stayed a little late in {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"They were meant to walk straight home, but a pale shimmer near {place.plaque_spot} "
        f"made them stop and stare."
    )


def find_plaque(world: World, place: Place) -> None:
    plaque = world.get("plaque")
    plaque.meters["faded"] += 1
    world.say(
        f"On the wall hung an old plaque, green at the edges and fuzzy with dust. "
        f"Most of its words had faded, as if the night had been nibbling at them for years."
    )
    world.say(place.night_sound)


def wake_ghost(world: World, ghost_cfg: Ghost) -> None:
    ghost = world.get("ghost")
    ghost.meters["restless"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a silver shape drifted out of the dark. It was the ghost of {ghost_cfg.title}, "
        f"and {ghost_cfg.whisper}"
    )


def fear_and_hold_close(world: World, kid1: Entity, kid2: Entity, bond: Bond) -> None:
    for kid in (kid1, kid2):
        kid.memes["fear"] += 1
    kid1.memes["teamwork"] += bond.teamwork_gain
    kid2.memes["teamwork"] += bond.teamwork_gain
    world.say(
        f"{kid1.id} felt a cold shiver run up {kid1.pronoun('possessive')} arms. "
        f"{kid2.id} took one small step back."
    )
    world.say(bond.line)


def plan_together(world: World, kid1: Entity, kid2: Entity, tool: Tool) -> None:
    pred = predict_with_tool(world, tool)
    world.facts["predicted_readable"] = pred["readable"]
    world.say(
        f'"Maybe the plaque wants to be read," {kid1.id} whispered. '
        f'"If we use {tool.phrase}, we might see the missing words."'
    )
    world.say(
        f'{kid2.id} nodded. "You hold the light steady. I will {tool.action}."'
    )


def use_tool(world: World, tool: Tool) -> None:
    plaque = world.get("plaque")
    plaque.meters["cleaned"] += 1
    world.say(
        f"Very carefully, the children moved closer. Together they used {tool.phrase} to {tool.action}."
    )
    if tool.sparkle:
        world.say(tool.sparkle)
    propagate(world, narrate=False)
    if plaque.meters["readable"] >= THRESHOLD:
        world.say(
            "Dust lifted away in a soft gray cloud. Little by little, the carved letters brightened "
            "until a hidden name gleamed through."
        )


def read_name(world: World, ghost_cfg: Ghost, kid1: Entity, kid2: Entity) -> None:
    plaque = world.get("plaque")
    plaque.meters["name_spoken"] += 1
    world.say(
        f'"We remember you, {ghost_cfg.title}," {kid1.id} and {kid2.id} said together.'
    )
    world.say(
        f"Under the dust, the plaque finally told the truth: {ghost_cfg.loss}"
    )
    propagate(world, narrate=False)


def peaceful_ending(world: World, place: Place, ghost_cfg: Ghost) -> None:
    ghost = world.get("ghost")
    if ghost.meters["glowing"] >= THRESHOLD:
        world.say(
            f"The ghost's frightened face softened. {ghost_cfg.thanks}"
        )
        world.say(
            f"At once, the room stopped feeling so cold. The silver shape thinned into friendly light "
            f"and floated up beside the plaque like a quiet star."
        )
        world.say(place.ending_image)


def frightened_ending(world: World, place: Place, ghost_cfg: Ghost, kid1: Entity, kid2: Entity) -> None:
    for kid in (kid1, kid2):
        kid.memes["fear"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"But their hands shook too much to finish the job. The plaque stayed half-hidden, "
        f"and the ghost kept whispering, {ghost_cfg.whisper.lower()}"
    )
    world.say(
        f"{kid1.id} and {kid2.id} ran to the door together instead of leaving each other behind. "
        f"Outside, they promised to come back with a grown-up and a steadier plan."
    )
    world.say(
        f"When they looked through the window, the pale ghost was still beside the plaque, waiting "
        f"for the right kind of help."
    )
    world.say(
        f"The night stayed spooky, but the children had learned one brave thing in {place.label}: "
        f"scary magic is easier to face when nobody faces it alone."
    )


def tell(
    place: Place,
    ghost_cfg: Ghost,
    tool: Tool,
    bond: Bond,
    kid1_name: str,
    kid1_type: str,
    kid2_name: str,
    kid2_type: str,
    courage: int,
) -> World:
    world = World()
    kid1 = world.add(Entity(id=kid1_name, kind="character", type=kid1_type, role="kid", label=kid1_name))
    kid2 = world.add(Entity(id=kid2_name, kind="character", type=kid2_type, role="kid", label=kid2_name))
    world.add(Entity(id="room", type="place", label=place.label))
    plaque = world.add(
        Entity(
            id="plaque",
            type="plaque",
            label="plaque",
            phrase="the old plaque",
            tags={"plaque"},
            attrs={"material": "brass"},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type=ghost_cfg.type,
            label=ghost_cfg.label,
            phrase=ghost_cfg.title,
            tags=set(ghost_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            attrs={"reveals_letters": tool.reveals_letters},
            tags=set(tool.tags),
        )
    )
    kid1.memes["courage"] = float(courage)
    kid2.memes["courage"] = float(courage)

    setup_scene(world, place, kid1, kid2)
    find_plaque(world, place)
    world.para()
    wake_ghost(world, ghost_cfg)
    fear_and_hold_close(world, kid1, kid2, bond)
    plan_together(world, kid1, kid2, tool)
    world.para()
    use_tool(world, tool)

    success = world.get("plaque").meters["readable"] >= THRESHOLD and teamwork_succeeds(bond, courage)
    if success:
        read_name(world, ghost_cfg, kid1, kid2)
        world.para()
        peaceful_ending(world, place, ghost_cfg)
        outcome = "peaceful"
    else:
        world.para()
        frightened_ending(world, place, ghost_cfg, kid1, kid2)
        outcome = "frightened"

    world.facts.update(
        place=place,
        ghost_cfg=ghost_cfg,
        tool_cfg=tool,
        bond_cfg=bond,
        kid1=kid1,
        kid2=kid2,
        plaque=plaque,
        ghost=ghost,
        teamwork_score=bond.teamwork_gain + courage,
        outcome=outcome,
        plaque_readable=world.get("plaque").meters["readable"] >= THRESHOLD,
        ghost_helped=world.get("ghost").meters["glowing"] >= THRESHOLD,
        courage=courage,
    )
    return world


PLACES = {
    "school_hall": Place(
        id="school_hall",
        label="the old school hall",
        opening="The long floorboards creaked, and moonlight slipped over the trophy case.",
        plaque_spot="the crooked staircase",
        night_sound="Somewhere above them, a loose window whispered against its frame.",
        ending_image="By morning, the plaque shone in the hall, and no one heard sad whispering there again.",
        tags={"school", "hall"},
    ),
    "library_stair": Place(
        id="library_stair",
        label="the little library stairwell",
        opening="Tall shelves stood like sleepy giants, and the lamps had already been turned low.",
        plaque_spot="the turn of the stairs",
        night_sound="The air smelled like paper, rain, and old wood.",
        ending_image="When the sun came up, the stairwell felt warm again, as if the books themselves had sighed in relief.",
        tags={"library"},
    ),
    "museum_corridor": Place(
        id="museum_corridor",
        label="the museum corridor",
        opening="Glass cases glimmered in the dark, and every shadow looked longer than it had in the daytime.",
        plaque_spot="the end of the stone corridor",
        night_sound="A clock ticked somewhere deep in the building, slow and hollow.",
        ending_image="The corridor no longer felt haunted, only hushed and grand.",
        tags={"museum"},
    ),
}

GHOSTS = {
    "caretaker": Ghost(
        id="caretaker",
        label="caretaker ghost",
        type="caretaker",
        title="Mr. Vale, the old caretaker",
        whisper='"Please... read my name."',
        loss='it belonged to Mr. Vale, the caretaker who had once kept every lamp glowing for the children.',
        thanks='"Thank you," he said, with a smile that looked more tired than scary.',
        tags={"ghost", "memory"},
    ),
    "librarian": Ghost(
        id="librarian",
        label="librarian ghost",
        type="librarian",
        title="Miss Wren, the night librarian",
        whisper='"The words are gone... and so am I."',
        loss='it honored Miss Wren, the librarian who had hidden books for shy children to discover.',
        thanks='"Now I am not forgotten," she murmured, bowing her bright head.',
        tags={"ghost", "books"},
    ),
    "founder": Ghost(
        id="founder",
        label="founder ghost",
        type="woman",
        title="Mrs. Fern, the gentle founder",
        whisper='"Someone must remember this plaque."',
        loss='it marked Mrs. Fern, who had built the place so children would have a safe room full of light and learning.',
        thanks='"You gave my story back to the wall," she said softly.',
        tags={"ghost", "history"},
    ),
}

TOOLS = {
    "chalk_rub": Tool(
        id="chalk_rub",
        label="a piece of white chalk and paper",
        phrase="a piece of white chalk and paper",
        action="make a rubbing over the plaque",
        reveals_letters=True,
        sense=3,
        sparkle="As the chalk moved, faint silver sparks ran along the letters as if the plaque itself were waking up.",
        tags={"chalk", "reading"},
    ),
    "lantern_cloth": Tool(
        id="lantern_cloth",
        label="a lantern and a soft cloth",
        phrase="a lantern and a soft cloth",
        action="wipe the plaque clean while shining warm light across it",
        reveals_letters=True,
        sense=3,
        sparkle="The lantern made the brass glow honey-gold, and the cloth teased hidden lines out of the tarnish.",
        tags={"lantern", "cleaning"},
    ),
    "mirror_beam": Tool(
        id="mirror_beam",
        label="a little mirror and a pocket flashlight",
        phrase="a little mirror and a pocket flashlight",
        action="bounce a narrow beam of light across the carved surface",
        reveals_letters=True,
        sense=2,
        sparkle="The beam slid over the plaque, and each letter flashed up for a breath like moonlight on water.",
        tags={"flashlight", "light"},
    ),
    "feather_duster": Tool(
        id="feather_duster",
        label="a feather duster",
        phrase="a feather duster",
        action="wave the dust around",
        reveals_letters=False,
        sense=1,
        sparkle="",
        tags={"dust"},
    ),
}

BONDS = {
    "siblings": Bond(
        id="siblings",
        line="They squeezed each other's hands the way siblings do when both are scared but neither wants to admit it first.",
        teamwork_gain=2,
        tags={"teamwork", "siblings"},
    ),
    "friends": Bond(
        id="friends",
        line="They leaned shoulder to shoulder like good friends sharing one brave idea.",
        teamwork_gain=2,
        tags={"teamwork", "friends"},
    ),
    "cousins": Bond(
        id="cousins",
        line="They whispered together like cousins who had already solved many backyard mysteries side by side.",
        teamwork_gain=1,
        tags={"teamwork", "cousins"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    place: str
    ghost: str
    tool: str
    bond: str
    kid1_name: str
    kid1_type: str
    kid2_name: str
    kid2_type: str
    courage: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="school_hall",
        ghost="caretaker",
        tool="lantern_cloth",
        bond="siblings",
        kid1_name="Lily",
        kid1_type="girl",
        kid2_name="Tom",
        kid2_type="boy",
        courage=2,
    ),
    StoryParams(
        place="library_stair",
        ghost="librarian",
        tool="chalk_rub",
        bond="friends",
        kid1_name="Mia",
        kid1_type="girl",
        kid2_name="Ben",
        kid2_type="boy",
        courage=2,
    ),
    StoryParams(
        place="museum_corridor",
        ghost="founder",
        tool="mirror_beam",
        bond="cousins",
        kid1_name="Ava",
        kid1_type="girl",
        kid2_name="Noah",
        kid2_type="boy",
        courage=3,
    ),
    StoryParams(
        place="school_hall",
        ghost="caretaker",
        tool="chalk_rub",
        bond="cousins",
        kid1_name="Eli",
        kid1_type="boy",
        kid2_name="Rose",
        kid2_type="girl",
        courage=1,
    ),
]


KNOWLEDGE = {
    "plaque": [
        (
            "What is a plaque?",
            "A plaque is a flat sign, often made of metal or stone, that holds names or words people want to remember."
        )
    ],
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky tale about a spirit or haunting. It can feel scary, but gentle ghost stories often end with understanding instead of harm."
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in the dark?",
            "A lantern spreads warm light so people can see around them. That makes it easier to notice details and feel less frightened."
        )
    ],
    "chalk": [
        (
            "What is a rubbing with chalk?",
            "A rubbing is when you lay paper over something bumpy and move chalk across it so the hidden shapes show through."
        )
    ],
    "flashlight": [
        (
            "Why can a flashlight help you read old letters?",
            "Light from a flashlight can make carved lines stand out. When shadows fall into the grooves, the letters are easier to see."
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help when something feels scary?",
            "Teamwork helps because people can share jobs and share courage. When one person feels shaky, another person can help steady the plan."
        )
    ],
    "memory": [
        (
            "Why is remembering someone's name important?",
            "A name helps keep a person in other people's thoughts. Remembering a name shows care and respect."
        )
    ],
}
KNOWLEDGE_ORDER = ["plaque", "ghost", "lantern", "chalk", "flashlight", "teamwork", "memory"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    tool = f["tool_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "plaque" and ends with kindness instead of harm.',
        f"Tell a spooky story where two children work together in {place.label} to help {ghost_cfg.title} by reading an old plaque.",
        f"Write a magical teamwork story where a haunted plaque, {tool.label}, and two brave children turn a frightening whisper into a peaceful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid1.id} and {kid2.id}, two children who found a haunted plaque in {place.label}. It is also about {ghost_cfg.title}, the lonely ghost tied to that plaque."
        ),
        (
            "What made the place feel spooky at first?",
            f"The children saw an old plaque with faded words, and then a ghost rose near it. The room also turned cold, which made the magic feel real and frightening."
        ),
        (
            "Why did the children move closer to the plaque?",
            f"They guessed the ghost wanted the plaque to be read. That gave them a reason to be brave instead of only running away."
        ),
        (
            "How did teamwork help them?",
            f"They did not try to solve the mystery alone. One child helped steady the plan while the other helped reveal the letters, so their shared courage became stronger than their fear."
        ),
    ]
    if f["plaque_readable"]:
        qa.append(
            (
                "How did they make the plaque readable?",
                f"They used {tool.phrase} to reveal the hidden letters on the plaque. Once the dust and shadows moved the right way, the missing name could finally be seen."
            )
        )
    if outcome == "peaceful":
        qa.append(
            (
                "Why did the ghost become peaceful?",
                f"The children read the plaque and spoke the ghost's name aloud. That helped the ghost feel remembered instead of lost."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the ghost turning gentle and the room losing its icy feeling. The shining plaque showed that something sad had been healed."
            )
        )
    else:
        qa.append(
            (
                "Did they solve the ghost's problem that night?",
                f"No, not yet. They tried together, but they were still too shaky to finish, so they promised to return with better help."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children escaping safely while still caring about the ghost. Even without fixing everything, they learned that staying together was the brave part."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"plaque", "ghost", "teamwork"}
    tool = f["tool_cfg"]
    ghost_cfg = f["ghost_cfg"]
    tags |= set(tool.tags)
    tags |= set(ghost_cfg.tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G, T) :- place(P), ghost(G), tool(T), reveals_letters(T), sense(T, S), sense_min(M), S >= M.

teamwork_score(B + C) :- chosen_bond_score(B), courage(C).
peaceful :- valid(chosen_place, chosen_ghost, chosen_tool), teamwork_score(S), S >= 4.
frightened :- valid(chosen_place, chosen_ghost, chosen_tool), teamwork_score(S), S < 4.

outcome(peaceful) :- peaceful.
outcome(frightened) :- frightened.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for ghost_id in GHOSTS:
        lines.append(asp.fact("ghost", ghost_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.reveals_letters:
            lines.append(asp.fact("reveals_letters", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    for bond_id, bond in BONDS.items():
        lines.append(asp.fact("bond", bond_id))
        lines.append(asp.fact("bond_score", bond_id, bond.teamwork_gain))
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
            asp.fact("chosen_place"),
            asp.fact("chosen_ghost"),
            asp.fact("chosen_tool"),
            asp.fact("courage", params.courage),
            asp.fact("chosen_bond_score", BONDS[params.bond].teamwork_gain),
            f"valid(chosen_place, chosen_ghost, chosen_tool) :- valid({params.place}, {params.ghost}, {params.tool}).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a haunted plaque, a ghost, and teamwork strong enough to make the magic gentle."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--bond", choices=BONDS)
    ap.add_argument("--courage", type=int, choices=[1, 2, 3], help="shared courage level")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool:
        tool = TOOLS[args.tool]
        if not tool.reveals_letters or tool.sense < SENSE_MIN:
            raise StoryError(explain_tool(tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, ghost, tool = rng.choice(sorted(combos))
    bond = args.bond or rng.choice(sorted(BONDS))
    courage = args.courage if args.courage is not None else rng.choice([1, 2, 3])
    kid1_name, kid1_type = pick_name(rng)
    kid2_name, kid2_type = pick_name(rng, avoid=kid1_name)
    return StoryParams(
        place=place,
        ghost=ghost,
        tool=tool,
        bond=bond,
        kid1_name=kid1_name,
        kid1_type=kid1_type,
        kid2_name=kid2_name,
        kid2_type=kid2_type,
        courage=courage,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(Unknown ghost: {params.ghost})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.bond not in BONDS:
        raise StoryError(f"(Unknown bond: {params.bond})")
    tool = TOOLS[params.tool]
    if not valid_combo(PLACES[params.place], GHOSTS[params.ghost], tool):
        raise StoryError(explain_tool(tool))

    world = tell(
        place=PLACES[params.place],
        ghost_cfg=GHOSTS[params.ghost],
        tool=tool,
        bond=BONDS[params.bond],
        kid1_name=params.kid1_name,
        kid1_type=params.kid1_type,
        kid2_name=params.kid2_name,
        kid2_type=params.kid2_type,
        courage=params.courage,
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
        print(f"{len(combos)} compatible (place, ghost, tool) combos:\n")
        for place, ghost, tool in combos:
            print(f"  {place:16} {ghost:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.kid1_name} and {p.kid2_name}: {p.ghost} at {p.place} "
                f"with {p.tool} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
