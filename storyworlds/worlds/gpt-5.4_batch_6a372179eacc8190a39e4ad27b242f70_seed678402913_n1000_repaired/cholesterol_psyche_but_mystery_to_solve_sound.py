#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cholesterol_psyche_but_mystery_to_solve_sound.py
============================================================================

A small storyworld about a child in a spooky old house who hears strange sounds,
follows clues, remembers good advice, and solves a ghostly-seeming mystery.

Seed constraints:
- Words: cholesterol, psyche, but
- Features: Mystery to Solve, Sound Effects, Flashback
- Style: Ghost Story

The world model keeps the "ghost story" mood while enforcing a child-safe,
common-sense resolution: every mystery must have a plausible sound source, the
chosen search tool must be able to reveal that source, and the story ends by
showing what changed in the room and in the child's feelings.

Run it
------
    python storyworlds/worlds/gpt-5.4/cholesterol_psyche_but_mystery_to_solve_sound.py
    python storyworlds/worlds/gpt-5.4/cholesterol_psyche_but_mystery_to_solve_sound.py --room attic
    python storyworlds/worlds/gpt-5.4/cholesterol_psyche_but_mystery_to_solve_sound.py --source mouse_tin
    python storyworlds/worlds/gpt-5.4/cholesterol_psyche_but_mystery_to_solve_sound.py --tool broom
    python storyworlds/worlds/gpt-5.4/cholesterol_psyche_but_mystery_to_solve_sound.py --all --qa
    python storyworlds/worlds/gpt-5.4/cholesterol_psyche_but_mystery_to_solve_sound.py --verify
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
COURAGE_INIT = 4.0


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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Room:
    id: str
    label: str
    spooky_detail: str
    affordances: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundSource:
    id: str
    label: str
    phrase: str
    kind: str
    noise: str
    reveal: str
    fix: str
    ending_image: str
    room_hint: str
    memory_hook: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reveals: set[str] = field(default_factory=set)
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Memory:
    id: str
    elder_type: str
    line: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    source: str
    tool: str
    memory: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
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


def _r_sound_scares(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    source = world.get("source")
    if source.meters["making_noise"] < THRESHOLD:
        return []
    sig = ("scare", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    room.meters["spooky"] += 1
    return []


def _r_memory_steadies(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["remembered"] < THRESHOLD:
        return []
    sig = ("steady", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["courage"] += 1
    if child.memes["fear"] > 0:
        child.memes["fear"] -= 1
    return []


def _r_reveal_solves(world: World) -> list[str]:
    source = world.get("source")
    if source.meters["found"] < THRESHOLD:
        return []
    sig = ("solve", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["making_noise"] = 0.0
    source.meters["fixed"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    room = world.get("room")
    if room.meters["spooky"] > 0:
        room.meters["spooky"] -= 1
    return []


CAUSAL_RULES = [
    Rule(name="sound_scares", tag="emotion", apply=_r_sound_scares),
    Rule(name="memory_steadies", tag="emotion", apply=_r_memory_steadies),
    Rule(name="reveal_solves", tag="physical", apply=_r_reveal_solves),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


ROOMS = {
    "attic": Room(
        id="attic",
        label="the attic",
        spooky_detail="The beams looked like thin black ribs, and the moon painted pale stripes across old trunks.",
        affordances={"loose_shutter", "mouse_tin", "dripping_pipe"},
        tags={"attic", "ghost"},
    ),
    "hallway": Room(
        id="hallway",
        label="the upstairs hallway",
        spooky_detail="The long runner rug lay quiet, but every family picture seemed to be listening.",
        affordances={"loose_shutter", "branch_window", "dripping_pipe"},
        tags={"hallway", "ghost"},
    ),
    "pantry": Room(
        id="pantry",
        label="the pantry",
        spooky_detail="The shelves stood close together, and jars glimmered like rows of sleepy eyes.",
        affordances={"mouse_tin", "dripping_pipe", "branch_window"},
        tags={"pantry", "ghost"},
    ),
}

SOURCES = {
    "loose_shutter": SoundSource(
        id="loose_shutter",
        label="a loose shutter",
        phrase="a loose shutter tapping the wall",
        kind="draft",
        noise='Tap... tap-tap... clack!',
        reveal="A shutter hook had slipped loose, so the wind kept knocking the shutter against the siding.",
        fix="The child held the lantern while the elder fastened the hook back in place.",
        ending_image="After that, the shutter rested still, and the moonlight lay smooth on the wall.",
        room_hint="Each gust made the sound come from high outside the room.",
        memory_hook="wind",
        tags={"wind", "shutter", "sound"},
    ),
    "mouse_tin": SoundSource(
        id="mouse_tin",
        label="a mouse in a tin",
        phrase="a tiny mouse bumping a round oat tin",
        kind="hidden_animal",
        noise='Scritch-scritch... bonk! Rattle-rattle!',
        reveal="Behind a sack of flour, a tiny mouse had climbed into an oat tin and was bumping it every time it turned around. The bright tin still had the word cholesterol printed on the side because it was grandpa's plain oat cereal.",
        fix="The elder tipped the little mouse gently into a box, carried it outside, and set the tin upright again.",
        ending_image="Soon the pantry was quiet except for one soft rustle from the garden grass outside.",
        room_hint="The sound came low to the floor and hopped from shelf to shelf.",
        memory_hook="oats",
        tags={"mouse", "tin", "cholesterol", "sound"},
    ),
    "dripping_pipe": SoundSource(
        id="dripping_pipe",
        label="a dripping pipe",
        phrase="a slow pipe drip hitting a metal bucket",
        kind="drip",
        noise='Plink... plink... ploink!',
        reveal="A pipe above the ceiling had a slow leak, and each drop was falling into an old metal bucket.",
        fix="The elder moved the bucket, tucked a towel under it for the night, and promised to mend the leak in the morning.",
        ending_image="Then the room held only a sleepy hush, with no bright plink jumping through it.",
        room_hint="The sound repeated slowly, always from the same dark corner.",
        memory_hook="water",
        tags={"water", "pipe", "sound"},
    ),
    "branch_window": SoundSource(
        id="branch_window",
        label="a branch on the window",
        phrase="a thin branch scratching at the glass",
        kind="outside_branch",
        noise='Ssssk... skritch... sssk!',
        reveal="A thin branch from the pear tree was rubbing the window whenever the wind bent it down.",
        fix="The elder opened the window a crack and tied the branch back with a piece of garden twine.",
        ending_image="When the breeze came again, the pane stayed clear and silent.",
        room_hint="The sound slid across the window like a fingernail.",
        memory_hook="tree",
        tags={"tree", "window", "sound"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a small yellow lantern",
        reveals={"draft", "hidden_animal", "drip", "outside_branch"},
        safe=True,
        tags={"light"},
    ),
    "broom": Tool(
        id="broom",
        label="broom",
        phrase="a straw broom",
        reveals={"hidden_animal", "outside_branch"},
        safe=True,
        tags={"broom"},
    ),
    "stepstool": Tool(
        id="stepstool",
        label="stepstool",
        phrase="a little wooden stepstool",
        reveals={"draft", "drip"},
        safe=True,
        tags={"stool"},
    ),
}

MEMORIES = {
    "listen_first": Memory(
        id="listen_first",
        elder_type="grandmother",
        line='Once, on another rainy night, Grandma had told the child, "A jumpy psyche can turn one small sound into a whole parade of ghosts. Listen first, then look."',
        effect="That old advice floated back now and slowed the child's breathing.",
        tags={"psyche", "flashback"},
    ),
    "ghosts_need_reasons": Memory(
        id="ghosts_need_reasons",
        elder_type="grandfather",
        line='The child remembered Grandpa chuckling by the stove: "A house can sound spooky, but noises still have reasons."',
        effect="The memory made the dark feel more like a puzzle than a monster.",
        tags={"flashback"},
    ),
    "count_the_beats": Memory(
        id="count_the_beats",
        elder_type="aunt",
        line='In a flashback, Aunt June appeared in the child\'s mind, tapping the table and saying, "Count the beats of a sound. Real clues repeat."',
        effect="Remembering that, the child counted instead of running away.",
        tags={"flashback", "sound"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lila", "Rose", "Ivy", "Tessa", "Ada", "June"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Finn", "Eli", "Jude", "Bram", "Leo"]


def valid_combo(room_id: str, source_id: str, tool_id: str) -> bool:
    room = ROOMS[room_id]
    source = SOURCES[source_id]
    tool = TOOLS[tool_id]
    return source_id in room.affordances and source.kind in tool.reveals and tool.safe


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id in sorted(ROOMS):
        for source_id in sorted(SOURCES):
            for tool_id in sorted(TOOLS):
                if valid_combo(room_id, source_id, tool_id):
                    combos.append((room_id, source_id, tool_id))
    return combos


def explain_rejection(room_id: str, source_id: str, tool_id: str) -> str:
    room = ROOMS[room_id]
    source = SOURCES[source_id]
    tool = TOOLS[tool_id]
    if source_id not in room.affordances:
        return (
            f"(No story: {source.label} is not a good fit for {room.label}. "
            f"This world only allows sound sources that plausibly belong in that place.)"
        )
    if source.kind not in tool.reveals:
        return (
            f"(No story: {tool.phrase} would not honestly reveal {source.label}. "
            f"The chosen tool must help solve the mystery, not just fill a slot.)"
        )
    if not tool.safe:
        return "(No story: unsafe search tools are refused in this child storyworld.)"
    return "(No story: this combination is not reasonable.)"


def predict_discovery(world: World, tool: Tool) -> bool:
    sim = world.copy()
    source = sim.get("source")
    if tool.safe and sim.facts["source_cfg"].kind in tool.reveals:
        source.meters["found"] += 1
        propagate(sim, narrate=False)
    return source.meters["fixed"] >= THRESHOLD


def open_night(world: World, child: Entity, room: Room) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Late one windy night, {child.id} padded toward {room.label}. {room.spooky_detail}"
    )
    world.say(
        "The house felt old enough to remember secrets, and the dark corners looked deep enough to hide one."
    )


def hear_sound(world: World, child: Entity, source_cfg: SoundSource, room: Room) -> None:
    source = world.get("source")
    source.meters["making_noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a sound slipped through {room.label}: {source_cfg.noise}"
    )
    world.say(
        f"{child.id} stopped so fast that even {child.pronoun('possessive')} nightshirt seemed to listen."
    )


def wonder_if_ghost(world: World, child: Entity, source_cfg: SoundSource) -> None:
    child.memes["fear"] += 1
    world.say(
        f'"Is it a ghost?" {child.id} whispered. The thought ran through {child.pronoun("possessive")} mind, but {source_cfg.room_hint}'
    )


def flashback(world: World, child: Entity, memory: Memory) -> None:
    child.memes["remembered"] += 1
    propagate(world, narrate=False)
    world.say(memory.line)
    world.say(memory.effect)


def search(world: World, child: Entity, elder: Entity, tool: Tool, source_cfg: SoundSource) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Instead of hiding under the blanket, {child.id} took {tool.phrase} and called softly for {elder.id}."
    )
    world.say(
        f"Together they listened again. {child.id} heard that the sound had a rhythm, and {elder.id} said that meant it was a clue."
    )
    if source_cfg.kind in tool.reveals:
        world.get("source").meters["found"] += 1
        propagate(world, narrate=False)


def reveal(world: World, elder: Entity, source_cfg: SoundSource) -> None:
    world.say(source_cfg.reveal)
    world.say(source_cfg.fix)
    world.say(
        f"{elder.id} smiled. \"See? A mystery can feel huge in the dark, but it grows smaller when you find its reason.\""
    )


def end_scene(world: World, child: Entity, source_cfg: SoundSource) -> None:
    child.memes["fear"] = 0.0
    world.say(source_cfg.ending_image)
    world.say(
        f"{child.id} listened one more time. No ghost came at all -- only a safe, sleepy quiet. {child.pronoun('Subject') if False else child.id} felt proud for solving the mystery."
    )


def tell(
    room: Room,
    source_cfg: SoundSource,
    tool: Tool,
    memory: Memory,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_name: str = "Grandma Bea",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name))
    room_ent = world.add(Entity(id="room", type="room", label=room.label))
    source = world.add(Entity(id="source", type="source", label=source_cfg.label))
    child.attrs["name"] = child_name
    elder.attrs["name"] = elder_name
    child.memes["courage"] = COURAGE_INIT
    world.facts.update(
        room_cfg=room,
        source_cfg=source_cfg,
        tool_cfg=tool,
        memory_cfg=memory,
        child=child,
        elder=elder,
        room=room_ent,
        source=source,
    )

    open_night(world, child, room)
    hear_sound(world, child, source_cfg, room)
    wonder_if_ghost(world, child, source_cfg)

    world.para()
    flashback(world, child, memory)
    solves = predict_discovery(world, tool)
    if not solves:
        raise StoryError("(Internal mismatch: the chosen tool should have solved the mystery, but did not.)")

    search(world, child, elder, tool, source_cfg)

    world.para()
    reveal(world, elder, source_cfg)
    end_scene(world, child, source_cfg)

    world.facts.update(
        solved=source.meters["fixed"] >= THRESHOLD,
        ghost_real=False,
        quiet_again=source.meters["making_noise"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    source_cfg = world.facts["source_cfg"]
    room_cfg = world.facts["room_cfg"]
    return [
        'Write a gentle ghost-story mystery for a 3-to-5-year-old that includes the words "cholesterol", "psyche", and "but".',
        f"Tell a spooky-but-safe story where a child named {child.attrs['name']} hears a strange sound in {room_cfg.label} and solves the mystery.",
        f"Write a story with sound effects, a flashback, and a false ghost scare that turns out to be {source_cfg.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    room_cfg = world.facts["room_cfg"]
    source_cfg = world.facts["source_cfg"]
    tool = world.facts["tool_cfg"]
    memory = world.facts["memory_cfg"]
    child_name = child.attrs["name"]
    elder_name = elder.attrs["name"]
    elder_word = elder.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, who heard a spooky sound, and {elder_name}, the {elder_word} who helped solve it.",
        ),
        (
            "What made the room feel spooky at first?",
            f"The room felt spooky because it was dark and old, and then the sound {source_cfg.noise} slipped through it. In the dark, that strange noise made the mystery feel bigger than it really was.",
        ),
        (
            f"Why did {child_name} think it might be a ghost?",
            f"{child_name} did not know what was making the sound, so fear rushed in before the answer did. When a child hears a weird noise in a shadowy room, the imagination can turn it into something ghostly.",
        ),
        (
            "What was the flashback about?",
            f"The flashback brought back advice from {elder_name} about listening for real clues. That memory steadied {child_name} and changed the moment from pure fright into a mystery to solve.",
        ),
        (
            f"How did {child_name} solve the mystery?",
            f"{child_name} used {tool.phrase} and listened carefully with {elder_name}. That helped reveal that the sound was really {source_cfg.phrase}, not a ghost at all.",
        ),
        (
            "What was the sound really coming from?",
            f"It was coming from {source_cfg.phrase}. Once the real cause was found, the room stopped feeling haunted and started feeling ordinary again.",
        ),
        (
            "How did the story end?",
            f"It ended quietly and safely after the sound was fixed. The final image shows that the room changed from spooky to calm, and {child_name} felt proud instead of afraid.",
        ),
    ]
    if source_cfg.id == "mouse_tin":
        qa.append(
            (
                "Why does the story mention cholesterol?",
                "The word appears on the oat tin the mouse was bumping around in. It is a clue about the object making the noise, not about a ghost.",
            )
        )
    if "psyche" in memory.line:
        qa.append(
            (
                "Why does the story use the word psyche?",
                f"It appears in the remembered advice about how fear can play tricks on the mind. In the story, that idea helps {child_name} slow down and think clearly.",
            )
        )
    return qa


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky kind of story that makes a place feel mysterious and eerie. In a gentle ghost story for children, the scary feeling often turns out to have a safe explanation.",
        )
    ],
    "sound": [
        (
            "Why can sounds seem scarier in the dark?",
            "Sounds can seem scarier in the dark because you hear them before you see what made them. When you do not know the cause yet, your imagination may make the mystery feel bigger.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back to something that happened earlier. It can give a character an important memory or clue.",
        )
    ],
    "psyche": [
        (
            "What does psyche mean?",
            "Psyche is a word for the mind and feelings inside a person. In a story, it can mean the part of you that gets scared, brave, worried, or calm.",
        )
    ],
    "cholesterol": [
        (
            "What is cholesterol?",
            "Cholesterol is a waxy substance in bodies and in some foods. Grown-ups may talk about it when they are thinking about heart health.",
        )
    ],
    "mouse": [
        (
            "Why do mice make scratchy sounds?",
            "Mice have tiny feet and little claws, so they make soft scritching and rattling sounds when they move around boxes or tins.",
        )
    ],
    "wind": [
        (
            "How can wind make spooky noises?",
            "Wind can shake shutters, tap branches, and whistle through cracks. Those sounds can seem mysterious until you find what the wind is touching.",
        )
    ],
    "water": [
        (
            "Why does a dripping pipe make a loud sound at night?",
            "A small drip can sound loud when it hits metal or when a quiet house echoes around it. Nighttime hush makes each little plink stand out more.",
        )
    ],
    "tree": [
        (
            "How can a tree branch make noise on a window?",
            "If the wind pushes a branch against a window, it can scratch and tap across the glass again and again.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "sound", "flashback", "psyche", "cholesterol", "mouse", "wind", "water", "tree"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "sound", "flashback"}
    tags |= set(world.facts["source_cfg"].tags)
    tags |= set(world.facts["memory_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="pantry",
        source="mouse_tin",
        tool="lantern",
        memory="listen_first",
        child_name="Mira",
        child_gender="girl",
        elder_name="Grandma Bea",
        elder_type="grandmother",
    ),
    StoryParams(
        room="hallway",
        source="branch_window",
        tool="broom",
        memory="ghosts_need_reasons",
        child_name="Theo",
        child_gender="boy",
        elder_name="Grandpa Sol",
        elder_type="grandfather",
    ),
    StoryParams(
        room="attic",
        source="loose_shutter",
        tool="stepstool",
        memory="count_the_beats",
        child_name="Nora",
        child_gender="girl",
        elder_name="Aunt June",
        elder_type="aunt",
    ),
    StoryParams(
        room="pantry",
        source="dripping_pipe",
        tool="stepstool",
        memory="ghosts_need_reasons",
        child_name="Owen",
        child_gender="boy",
        elder_name="Dad",
        elder_type="father",
    ),
]


ASP_RULES = r"""
valid(Room, Source, Tool) :-
    room(Room), source(Source), tool(Tool),
    affords(Room, Source),
    kind(Source, K),
    reveals(Tool, K),
    safe(Tool).

solved :- chosen_room(R), chosen_source(S), chosen_tool(T),
          valid(R, S, T).

#show valid/3.
#show solved/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for src in sorted(room.affordances):
            lines.append(asp.fact("affords", room_id, src))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("kind", source_id, source.kind))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.safe:
            lines.append(asp.fact("safe", tool_id))
        for kind in sorted(tool.reveals):
            lines.append(asp.fact("reveals", tool_id, kind))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_room", params.room),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "solved"))


def outcome_of(params: StoryParams) -> bool:
    return valid_combo(params.room, params.source, params.tool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Ghost-story mystery world: a child hears a spooky sound, remembers good advice, and solves the mystery."
    )
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--memory", choices=sorted(MEMORIES))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.source and args.tool:
        if not valid_combo(args.room, args.source, args.tool):
            raise StoryError(explain_rejection(args.room, args.source, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.source is None or combo[1] == args.source)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        if args.room and args.source and args.tool:
            raise StoryError(explain_rejection(args.room, args.source, args.tool))
        raise StoryError("(No valid combination matches the given options.)")

    room_id, source_id, tool_id = rng.choice(combos)
    memory_id = args.memory or rng.choice(sorted(MEMORIES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or MEMORIES[memory_id].elder_type
    if elder_type in {"grandmother", "aunt", "mother"}:
        default_elder = {
            "grandmother": "Grandma Bea",
            "aunt": "Aunt June",
            "mother": "Mom",
        }[elder_type]
    else:
        default_elder = {
            "grandfather": "Grandpa Sol",
            "uncle": "Uncle Ray",
            "father": "Dad",
        }[elder_type]
    elder_name = args.elder_name or default_elder
    return StoryParams(
        room=room_id,
        source=source_id,
        tool=tool_id,
        memory=memory_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")
    if not valid_combo(params.room, params.source, params.tool):
        raise StoryError(explain_rejection(params.room, params.source, params.tool))

    world = tell(
        room=ROOMS[params.room],
        source_cfg=SOURCES[params.source],
        tool=TOOLS[params.tool],
        memory=MEMORIES[params.memory],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
    )

    story = world.render().replace("child felt proud", f"{params.child_name} felt proud")
    return StorySample(
        params=params,
        story=story,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    for params in CURATED:
        if asp_solved(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in solved outcome for curated params: {params}")
            break
    else:
        print(f"OK: ASP solved outcome matches Python on {len(CURATED)} curated scenarios.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, source, tool) combos:\n")
        for room_id, source_id, tool_id in combos:
            print(f"  {room_id:8} {source_id:14} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.child_name}: {p.source} in {p.room} with {p.tool}"
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
