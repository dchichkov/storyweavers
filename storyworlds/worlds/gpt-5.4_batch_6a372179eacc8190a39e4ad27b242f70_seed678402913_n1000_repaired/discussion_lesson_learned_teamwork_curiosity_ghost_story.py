#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/discussion_lesson_learned_teamwork_curiosity_ghost_story.py
========================================================================================

A standalone story world for a child-facing ghost-story-shaped tale where two
children hear something spooky, stop for a discussion, and use curiosity plus
teamwork to discover the ordinary cause.

The world enforces one central common-sense constraint: the children must have a
plausible way to investigate the mystery safely. A dark, high, or tangled cause
needs the right tool. The story is not a frozen paragraph with swapped nouns;
the prose is driven by simulated state: fear rises, discussion steadies it,
investigation reveals the cause, and the ending image proves what they learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/discussion_lesson_learned_teamwork_curiosity_ghost_story.py
    python storyworlds/worlds/gpt-5.4/discussion_lesson_learned_teamwork_curiosity_ghost_story.py --place attic --source sheet
    python storyworlds/worlds/gpt-5.4/discussion_lesson_learned_teamwork_curiosity_ghost_story.py --tool basket
    python storyworlds/worlds/gpt-5.4/discussion_lesson_learned_teamwork_curiosity_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/discussion_lesson_learned_teamwork_curiosity_ghost_story.py --qa
    python storyworlds/worlds/gpt-5.4/discussion_lesson_learned_teamwork_curiosity_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ to path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | place
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain vocabulary.
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    phrase: str
    opening: str
    dark_spot: str
    echo: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    sound: str
    look: str
    hiding: str
    needs: set[str] = field(default_factory=set)
    lesson: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    provides: set[str] = field(default_factory=set)
    teamwork_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    opening: str
    hush: str
    closing: str


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return [e for e in self.entities.values() if e.role in {"lead", "friend"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spooky_sound(world: World) -> list[str]:
    source = world.get("source")
    room = world.get("room")
    if source.meters["active"] < THRESHOLD:
        return []
    sig = ("spooky_sound", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["curiosity"] += 1
    return ["__spooky__"]


def _r_discussion_steadies(world: World) -> list[str]:
    if world.get("discussion").meters["happened"] < THRESHOLD:
        return []
    sig = ("discussion_steadies",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        if kid.memes["fear"] > 0:
            kid.memes["fear"] = max(0.0, kid.memes["fear"] - 0.5)
        kid.memes["courage"] += 1
        kid.memes["trust"] += 1
    return []


def _r_reveal_relief(world: World) -> list[str]:
    source = world.get("source")
    room = world.get("room")
    if source.meters["revealed"] < THRESHOLD:
        return []
    sig = ("reveal_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["wonder"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spooky_sound", tag="mystery", apply=_r_spooky_sound),
    Rule(name="discussion_steadies", tag="social", apply=_r_discussion_steadies),
    Rule(name="reveal_relief", tag="resolution", apply=_r_reveal_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Reasonableness helpers.
# ---------------------------------------------------------------------------
def can_happen(place: Place, source: Source) -> bool:
    return source.id in place.supports


def tool_works(source: Source, tool: Tool) -> bool:
    return source.needs.issubset(tool.provides)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if not can_happen(place, source):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_works(source, tool):
                    combos.append((place_id, source_id, tool_id))
    return combos


def explain_rejection(place: Place, source: Source, tool: Tool) -> str:
    if not can_happen(place, source):
        return (
            f"(No story: {source.phrase} is not a good fit for {place.phrase}. "
            f"The mystery should come from something that could really be there.)"
        )
    missing = sorted(source.needs - tool.provides)
    if missing:
        return (
            f"(No story: {tool.phrase} cannot safely solve this mystery. "
            f"It is missing {missing}, which this cause needs for a believable reveal.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Prediction helper.
# ---------------------------------------------------------------------------
def predict_reveal(world: World, source: Source, tool: Tool) -> dict:
    sim = world.copy()
    sim.facts["tool_cfg"] = tool
    if tool_works(source, tool):
        sim.get("source").meters["revealed"] += 1
        propagate(sim, narrate=False)
    return {
        "revealed": sim.get("source").meters["revealed"] >= THRESHOLD,
        "fear_after": sum(k.memes["fear"] for k in sim.kids()),
    }


# ---------------------------------------------------------------------------
# Story actions.
# ---------------------------------------------------------------------------
def opening(world: World, lead: Entity, friend: Entity, place: Place, mood: Mood) -> None:
    for kid in (lead, friend):
        kid.memes["calm"] += 1
    world.say(
        f"After supper, {lead.id} and {friend.id} wandered to {place.phrase}. "
        f"{place.opening} {mood.opening}"
    )
    world.say(
        f"They were supposed to carry back a box of old games, but they kept pausing "
        f"to look into {place.dark_spot}."
    )


def strange_noise(world: World, place: Place, source: Source, mood: Mood) -> None:
    world.get("source").meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {place.echo} made a sound like {source.sound}. In the dimness, "
        f"{source.look} almost seemed to float by itself. {mood.hush}"
    )


def first_reaction(world: World, lead: Entity, friend: Entity) -> None:
    world.say(
        f'{friend.id} grabbed {lead.id}\'s sleeve. "Did you hear that?" '
        f'{friend.pronoun().capitalize()} whispered.'
    )
    world.say(
        f"{lead.id}'s heart gave one big thump. For a moment, both children wondered "
        f"if they had found a real ghost."
    )


def discussion(world: World, lead: Entity, friend: Entity, tool: Tool) -> None:
    world.get("discussion").meters["happened"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But instead of running, they had a quiet discussion right there on the creaky floor."
    )
    world.say(
        f'"Maybe it only sounds spooky because it is dark," {lead.id} said. '
        f'"If we stay together and use {tool.phrase}, we can check."'
    )
    world.say(
        f'{friend.id} took a slow breath and nodded. "We can be scared and still be curious," '
        f'{friend.pronoun()} said.'
    )


def team_up(world: World, lead: Entity, friend: Entity, tool: Tool) -> None:
    lead.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(tool.teamwork_line.format(lead=lead.id, friend=friend.id))
    world.say(
        f"Step by step, they moved closer instead of letting the mystery grow larger in their heads."
    )


def reveal(world: World, lead: Entity, friend: Entity, source: Source) -> None:
    world.get("source").meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last the secret showed itself. It was only {source.phrase}, {source.hiding}."
    )
    world.say(
        f'The strange cry had been {source.sound}, and the pale shape had been {source.look}. '
        f'"So that was our ghost," {friend.id} said, and this time {friend.pronoun()} laughed.'
    )


def lesson(world: World, lead: Entity, friend: Entity, source: Source, place: Place) -> None:
    world.say(
        f"{lead.id} laughed too, though now the room felt small and ordinary again. "
        f'"I am glad we talked first," {lead.pronoun()} said. '
        f'"If we had run away, we would never have learned the truth."'
    )
    world.say(
        f"{friend.id} nodded. {source.lesson} Working together had made them braver than either child felt alone."
    )
    world.say(
        f"When they finally carried the game box back downstairs, {place.label} no longer felt haunted at all. "
        f"It felt like a place where curiosity had turned a ghost story into a lesson."
    )


# ---------------------------------------------------------------------------
# Full screenplay.
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    source: Source,
    tool: Tool,
    mood: Mood,
    lead_name: str = "Nora",
    lead_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", kind="place", type="place", label=place.label, phrase=place.phrase))
    source_ent = world.add(Entity(id="source", kind="thing", type="cause", label=source.label, phrase=source.phrase))
    world.add(Entity(id="discussion", kind="thing", type="moment", label="discussion"))

    opening(world, lead, friend, place, mood)
    world.para()
    strange_noise(world, place, source, mood)
    first_reaction(world, lead, friend)
    world.para()
    discussion(world, lead, friend, tool)
    team_up(world, lead, friend, tool)
    world.para()
    reveal(world, lead, friend, source)
    lesson(world, lead, friend, source, place)

    world.facts.update(
        lead=lead,
        friend=friend,
        parent=parent,
        place_cfg=place,
        source_cfg=source,
        tool_cfg=tool,
        mood_cfg=mood,
        source_revealed=source_ent.meters["revealed"] >= THRESHOLD,
        teamwork=lead.memes["teamwork"] >= THRESHOLD and friend.memes["teamwork"] >= THRESHOLD,
        lesson_learned=lead.memes["lesson"] >= THRESHOLD and friend.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        phrase="the attic above the hall",
        opening="The slanted ceiling held deep shadows between the beams.",
        dark_spot="the far corner under the roof",
        echo="the old rafters",
        supports={"sheet", "window", "mice"},
        tags={"attic", "dark"},
    ),
    "barn": Place(
        id="barn",
        label="the barn loft",
        phrase="the old barn loft behind the house",
        opening="Dusty boards glimmered where moonlight slipped through the cracks.",
        dark_spot="the hay bales at the back",
        echo="the loose wood",
        supports={"sheet", "mice"},
        tags={"barn", "dark"},
    ),
    "hallway": Place(
        id="hallway",
        label="the upstairs hallway",
        phrase="the long upstairs hallway",
        opening="A row of family pictures watched from the wall while the last daylight faded.",
        dark_spot="the bend near the linen closet",
        echo="the narrow walls",
        supports={"window", "mice"},
        tags={"hallway", "dark"},
    ),
}

SOURCES = {
    "sheet": Source(
        id="sheet",
        label="sheet",
        phrase="a white sheet",
        sound="a soft flap and whisper",
        look="a sheet lifting and dipping on a forgotten drying line",
        hiding="caught in a draft from a cracked vent",
        needs={"light", "reach"},
        lesson="They learned that a fluttering thing can look far stranger before you shine a light on it.",
        tags={"sheet", "wind"},
    ),
    "window": Source(
        id="window",
        label="window latch",
        phrase="a loose window latch",
        sound="a thin whistle and click",
        look="moonlight trembling on a half-open window",
        hiding="tapping each time the wind pushed it",
        needs={"light"},
        lesson="They learned that a small noise can sound huge when the house is quiet and nobody has checked it yet.",
        tags={"window", "wind"},
    ),
    "mice": Source(
        id="mice",
        label="mice",
        phrase="two tiny mice",
        sound="little scritches and rustles",
        look="a dusty basket shivering as something moved behind it",
        hiding="nestled under a pile of cloth",
        needs={"light", "move"},
        lesson="They learned that busy little animals can make a room sound much scarier than they really are.",
        tags={"mice", "animal"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        provides={"light"},
        teamwork_line="{lead} held the flashlight with both hands while {friend} stayed shoulder to shoulder beside {lead}.",
        tags={"flashlight"},
    ),
    "stool_light": Tool(
        id="stool_light",
        label="flashlight and step stool",
        phrase="a flashlight and a little step stool",
        provides={"light", "reach"},
        teamwork_line="{friend} carried the step stool while {lead} shone the flashlight, and they promised not to let go of each other's sleeves.",
        tags={"flashlight", "stool"},
    ),
    "lantern_basket": Tool(
        id="lantern_basket",
        label="lantern and basket handle",
        phrase="a lantern and the long basket handle",
        provides={"light", "move"},
        teamwork_line="{lead} lifted the lantern while {friend} used the basket handle to nudge things from a safe distance.",
        tags={"lantern", "handle"},
    ),
    "basket": Tool(
        id="basket",
        label="basket",
        phrase="a basket",
        provides={"move"},
        teamwork_line="{lead} and {friend} carried the basket together, but it did not help them see much at all.",
        tags={"handle"},
    ),
}

MOODS = {
    "moon": Mood(
        id="moon",
        opening="Even the moonlight looked thin and silvery there.",
        hush="The air went so still that even their breathing sounded loud.",
        closing="Outside, the moon looked friendlier than before.",
    ),
    "lamp": Mood(
        id="lamp",
        opening="Only a weak lamp from downstairs touched the steps.",
        hush="The shadows stretched until every box seemed taller than it was.",
        closing="Downstairs, the lamplight felt warm and ordinary.",
    ),
    "rain": Mood(
        id="rain",
        opening="Rain tapped on the roof as if small fingers were drumming overhead.",
        hush="For one heartbeat, the whole house listened with them.",
        closing="The rain still fell, but now it sounded gentle instead of ghostly.",
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Jack", "Noah"]


# ---------------------------------------------------------------------------
# Per-world params.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    source: str
    tool: str
    mood: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


# Curated set.
CURATED = [
    StoryParams(
        place="attic",
        source="sheet",
        tool="stool_light",
        mood="moon",
        lead_name="Nora",
        lead_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="hallway",
        source="window",
        tool="flashlight",
        mood="lamp",
        lead_name="Mia",
        lead_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="barn",
        source="mice",
        tool="lantern_basket",
        mood="rain",
        lead_name="Ruby",
        lead_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
    ),
]


# ---------------------------------------------------------------------------
# QA content.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ghost_story": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky story that makes ordinary things feel mysterious for a while. In many child-safe ghost stories, the scary thing turns out to have a real explanation."
        )
    ],
    "discussion": [
        (
            "What is a discussion?",
            "A discussion is when people stop and talk together about what they think. It can help them make a calmer and smarter plan."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means two or more people help each other to do something. Working together can make a hard or scary job feel easier."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to find out more. It helps you ask questions and look for the truth."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight helps you see what is really there. When you can see clearly, shadows and shapes are less confusing."
        )
    ],
    "wind": [
        (
            "Why can wind make spooky sounds?",
            "Wind can whistle through cracks, flap cloth, and rattle loose things. In a quiet place, those sounds can seem much stranger than they really are."
        )
    ],
    "mice": [
        (
            "Why do tiny animals sometimes sound big in a quiet room?",
            "In a still room, small scratches and rustles echo more than you expect. That can make a tiny animal seem much larger and scarier."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost_story", "discussion", "teamwork", "curiosity", "flashlight", "wind", "mice"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "discussion" and ends with a real explanation instead of a real ghost.',
        f"Tell a spooky-but-safe story where {lead.id} and {friend.id} hear something strange in {place.phrase}, stop for a discussion, and use teamwork plus curiosity to discover it is {source.phrase}.",
        "Write a short story with a haunted feeling, a calm investigation, and a lesson that talking together can be braver than running away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {friend.id}, two children who heard a spooky sound in {place.phrase}. They felt frightened at first, but they stayed together."
        ),
        (
            f"Why did {place.label} seem scary?",
            f"It was dark and full of uncertain sounds, so ordinary things felt mysterious. {source.look.capitalize()} helped make the place seem haunted before the children understood what they were seeing."
        ),
        (
            "What did the children do when they got scared?",
            f"They stopped for a discussion instead of running away. That talk helped them slow down, trust each other, and choose to investigate with {tool.phrase}."
        ),
        (
            "How did teamwork help them?",
            f"They did not investigate alone. By staying side by side and sharing the job, they felt braver and could check the mystery more carefully."
        ),
        (
            "What was the ghost really?",
            f"It was really {source.phrase}. The spooky sound came from {source.sound}, and the children only understood that after they looked closely."
        ),
        (
            "What lesson did they learn?",
            f"They learned that scary things do not always mean danger or magic. When they talked together and checked the facts, curiosity led them to the truth."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost_story", "discussion", "teamwork", "curiosity"}
    tool = f["tool_cfg"]
    source = f["source_cfg"]
    if "light" in tool.provides:
        tags.add("flashlight")
    tags |= set(source.tags)
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:11} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Registry gate.
valid(Place, Source, Tool) :- place(Place), source(Source), tool(Tool),
                              supports(Place, Source),
                              not missing_need(Source, Tool).

missing_need(Source, Tool) :- needs(Source, Need), not provides(Tool, Need).

% Simple outcome model: if the combo is valid, the cause can be revealed.
revealed(Source) :- chosen_place(P), chosen_source(Source), chosen_tool(T),
                    valid(P, Source, T).
outcome(revealed) :- revealed(_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for need in sorted(source.needs):
            lines.append(asp.fact("needs", source_id, need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for provides in sorted(tool.provides):
            lines.append(asp.fact("provides", tool_id, provides))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
        py = "revealed" if (can_happen(PLACES[params.place], SOURCES[params.source]) and tool_works(SOURCES[params.source], TOOLS[params.tool])) else "?"
        asp_out = asp_outcome(params)
        if py != asp_out:
            rc = 1
            print("MISMATCH in outcome:", params, py, asp_out)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: empty story.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a spooky mystery solved by discussion, curiosity, and teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.tool:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        tool = TOOLS[args.tool]
        if not (can_happen(place, source) and tool_works(source, tool)):
            raise StoryError(explain_rejection(place, source, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, tool_id = rng.choice(sorted(combos))
    mood_id = args.mood or rng.choice(sorted(MOODS))
    lead_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    lead_name = _pick_name(rng, lead_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=lead_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        source=source_id,
        tool=tool_id,
        mood=mood_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.source not in SOURCES:
        raise StoryError(f"Unknown source: {params.source}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")

    place = PLACES[params.place]
    source = SOURCES[params.source]
    tool = TOOLS[params.tool]
    mood = MOODS[params.mood]

    if not can_happen(place, source) or not tool_works(source, tool):
        raise StoryError(explain_rejection(place, source, tool))

    world = tell(
        place=place,
        source=source,
        tool=tool,
        mood=mood,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
    )

    # Make sure the world really reached the intended resolution.
    pred = predict_reveal(world, source, tool)
    if not pred["revealed"]:
        raise StoryError("The investigation did not plausibly reveal the cause.")

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
        print(f"{len(combos)} compatible (place, source, tool) combos:\n")
        for place, source, tool in combos:
            print(f"  {place:8} {source:7} {tool}")
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
            header = f"### {p.lead_name} and {p.friend_name}: {p.source} in {p.place} with {p.tool}"
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
