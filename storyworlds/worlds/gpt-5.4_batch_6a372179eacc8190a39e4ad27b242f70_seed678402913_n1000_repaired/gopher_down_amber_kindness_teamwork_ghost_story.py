#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gopher_down_amber_kindness_teamwork_ghost_story.py
=============================================================================

A standalone story world for a gentle ghost-story domain: two children notice a
spooky shape in the evening, hear a lonely sound from somewhere down below, and
discover that the "ghost" is only a misunderstanding around a trapped gopher.
The real turn comes from kindness and teamwork: the children stay together,
bring the right helping tool, and get the little animal out safely.

The seed words are built into the state-driven tale:
- gopher
- down
- amber

Run it
------
    python storyworlds/worlds/gpt-5.4/gopher_down_amber_kindness_teamwork_ghost_story.py
    python storyworlds/worlds/gpt-5.4/gopher_down_amber_kindness_teamwork_ghost_story.py --place orchard --trap window_well
    python storyworlds/worlds/gpt-5.4/gopher_down_amber_kindness_teamwork_ghost_story.py --tool blanket
    python storyworlds/worlds/gpt-5.4/gopher_down_amber_kindness_teamwork_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/gopher_down_amber_kindness_teamwork_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gopher_down_amber_kindness_teamwork_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    amber_line: str
    affords_illusions: set[str] = field(default_factory=set)
    affords_traps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Illusion:
    id: str
    shape: str
    motion: str
    source: str
    spookiness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trap:
    id: str
    label: str
    where: str
    need: str
    depth: str
    problem_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    methods: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.attrs.get("role") == "kid"]

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
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    illusion = world.get("illusion")
    if place.meters["twilight"] < THRESHOLD or illusion.meters["visible"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["spooky"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return out


def _r_lonely(world: World) -> list[str]:
    gopher = world.get("gopher")
    if gopher.meters["stuck"] < THRESHOLD:
        return []
    sig = ("lonely",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gopher.memes["lonely"] += 1
    for kid in world.kids():
        kid.memes["concern"] += 1
    return []


def _r_team(world: World) -> list[str]:
    if world.facts.get("teaming") is not True:
        return []
    sig = ("team",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["courage"] += 1
    return []


def _r_rescue(world: World) -> list[str]:
    gopher = world.get("gopher")
    if gopher.meters["helped"] < THRESHOLD:
        return []
    sig = ("rescue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gopher.meters["stuck"] = 0.0
    gopher.meters["safe"] += 1
    gopher.memes["lonely"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["kindness"] += 1
        kid.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="spook", apply=_r_spook),
    Rule(name="lonely", apply=_r_lonely),
    Rule(name="team", apply=_r_team),
    Rule(name="rescue", apply=_r_rescue),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def trap_at_place(place: Place, trap: Trap) -> bool:
    return trap.id in place.affords_traps


def illusion_at_place(place: Place, illusion: Illusion) -> bool:
    return illusion.id in place.affords_illusions


def tool_fits(trap: Trap, tool: Tool) -> bool:
    return trap.need in tool.methods


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for illusion_id, illusion in ILLUSIONS.items():
            if not illusion_at_place(place, illusion):
                continue
            for trap_id, trap in TRAPS.items():
                if not trap_at_place(place, trap):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_fits(trap, tool):
                        combos.append((place_id, illusion_id, trap_id, tool_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    illusion: str
    trap: str
    tool: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(
        id="garden",
        label="the moon garden",
        detail="Bean poles made thin shadows, and the cabbages sat in neat round rows.",
        amber_line="An amber porch light spilled across the stepping stones.",
        affords_illusions={"sheet", "lantern_vine"},
        affords_traps={"window_well", "rain_barrel"},
        tags={"garden"},
    ),
    "orchard": Place(
        id="orchard",
        label="the old orchard",
        detail="Apple leaves whispered over the path, and the grass smelled sweet and cool.",
        amber_line="An amber lantern hung by the gate and painted the trunks honey-gold.",
        affords_illusions={"kite", "sheet"},
        affords_traps={"root_hollow", "window_well"},
        tags={"orchard"},
    ),
    "shedyard": Place(
        id="shedyard",
        label="the shed yard",
        detail="Rakes leaned against the wall, and flowerpots made little towers by the door.",
        amber_line="An amber bulb over the shed door glowed like a sleepy eye.",
        affords_illusions={"lantern_vine", "kite"},
        affords_traps={"rain_barrel", "root_hollow"},
        tags={"yard"},
    ),
}

ILLUSIONS = {
    "sheet": Illusion(
        id="sheet",
        shape="a white sheet on the clothesline",
        motion="it lifted and bowed in the wind",
        source="the sheet kept catching the light and looking almost alive",
        spookiness=2,
        tags={"sheet", "ghost"},
    ),
    "kite": Illusion(
        id="kite",
        shape="a torn white kite in the branches",
        motion="its tail fluttered and tapped the leaves",
        source="the kite flashed pale whenever the light touched it",
        spookiness=2,
        tags={"kite", "ghost"},
    ),
    "lantern_vine": Illusion(
        id="lantern_vine",
        shape="a white bean blossom vine around an old lantern hook",
        motion="the blossoms swayed together like nodding faces",
        source="the vine turned misty in the dim light",
        spookiness=1,
        tags={"vine", "ghost"},
    ),
}

TRAPS = {
    "window_well": Trap(
        id="window_well",
        label="window well",
        where="down in the narrow window well beside the wall",
        need="ramp",
        depth="deep enough that tiny paws could not climb the smooth side",
        problem_line="A little nose kept peeking up and slipping back again.",
        tags={"hole", "rescue"},
    ),
    "rain_barrel": Trap(
        id="rain_barrel",
        label="empty rain barrel",
        where="down in an empty rain barrel that had fallen on its side and rolled against the fence",
        need="lift",
        depth="round and slippery inside",
        problem_line="Each scratchy scramble slid right back to the bottom.",
        tags={"barrel", "rescue"},
    ),
    "root_hollow": Trap(
        id="root_hollow",
        label="root hollow",
        where="down in a root hollow under an old tree",
        need="reach",
        depth="twisty and dark under the roots",
        problem_line="Two bright eyes blinked from the dark, then hid again.",
        tags={"tree", "rescue"},
    ),
}

TOOLS = {
    "plank": Tool(
        id="plank",
        label="a smooth wooden plank",
        methods={"ramp"},
        action="set the smooth wooden plank against the side so it made a little path upward",
        qa_text="made a ramp with a smooth wooden plank",
        tags={"ramp"},
    ),
    "basket": Tool(
        id="basket",
        label="a berry basket on a string",
        methods={"lift"},
        action="lowered the berry basket on a string and kept it steady until the gopher climbed in",
        qa_text="lowered a berry basket on a string and lifted the gopher out",
        tags={"basket"},
    ),
    "blanket": Tool(
        id="blanket",
        label="a soft picnic blanket",
        methods={"reach"},
        action="stretched the soft blanket low and still so the gopher could step onto it, then gently pulled it free",
        qa_text="used a soft blanket to reach in and pull the gopher free gently",
        tags={"blanket"},
    ),
    # Known to the world but refused for rescue parity.
    "broom": Tool(
        id="broom",
        label="a broom",
        methods={"sweep"},
        action="poked with the broom",
        qa_text="tried to poke with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]

KNOWLEDGE = {
    "ghost": [(
        "What makes something look ghostly at night?",
        "Dim light can make ordinary things look strange. A sheet, a kite, or moving leaves can seem spooky when you only see part of them."
    )],
    "gopher": [(
        "What is a gopher?",
        "A gopher is a small burrowing animal with strong front paws. It digs tunnels in the ground and can disappear underground very quickly."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork is when people help each other do one job together. One person can hold, another can guide, and the job becomes easier and safer."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means noticing that someone is scared, hurt, or stuck and choosing to help gently. It can make others feel safe."
    )],
    "ramp": [(
        "What is a ramp?",
        "A ramp is a sloping path that helps something move up or down without a jump. Animals can climb a ramp more easily than a smooth wall."
    )],
    "basket": [(
        "Why would a basket on a string help in a rescue?",
        "A basket on a string can be lowered down and then lifted back up. It gives a small animal a safe place to ride."
    )],
    "blanket": [(
        "How can a blanket help gently?",
        "A soft blanket can make a gentle surface for holding or guiding something without hurting it. Soft things are useful when you must be careful."
    )],
}
KNOWLEDGE_ORDER = ["ghost", "gopher", "kindness", "teamwork", "ramp", "basket", "blanket"]


def predict_need(world: World) -> dict:
    sim = world.copy()
    gopher = sim.get("gopher")
    gopher.meters["stuck"] += 1
    propagate(sim)
    return {
        "lonely": gopher.memes["lonely"] >= THRESHOLD,
        "still_stuck": gopher.meters["stuck"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    place_ent = world.get("place")
    place_ent.meters["twilight"] += 1
    world.say(
        f"One evening, {a.id} and {b.id} walked together into {place.label}. "
        f"{place.detail} {place.amber_line}"
    )


def first_glimpse(world: World, a: Entity, b: Entity, illusion: Illusion) -> None:
    illusion_ent = world.get("illusion")
    illusion_ent.meters["visible"] += 1
    propagate(world)
    world.say(
        f"Near the far end, they saw {illusion.shape}. In the hush of evening, "
        f"{illusion.motion}, and {illusion.source}."
    )
    fear_word = "both children felt a shiver" if all(k.memes["fear"] >= THRESHOLD for k in world.kids()) else f"{a.id} felt a shiver"
    world.say(f"For a moment, {fear_word}. It looked almost like a ghost.")
    world.facts["ghost_seen"] = True


def hear_cry(world: World, trap: Trap) -> None:
    gopher = world.get("gopher")
    gopher.meters["stuck"] += 1
    propagate(world)
    world.say(
        f"Then a thin, scratchy cry floated up from somewhere {trap.where}. "
        f"It was not a moan at all, only a frightened little sound."
    )
    world.say(trap.problem_line)


def choose_kindness(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    need = predict_need(world)
    world.facts["predicted_need"] = need
    world.facts["teaming"] = True
    propagate(world)
    world.say(
        f'{b.id} reached for {a.id}\'s hand. "If something is down there and scared," '
        f'{b.pronoun()} whispered, "we should help it together."'
    )
    world.say(
        f"{a.id} swallowed, nodded, and stayed beside {b.id} instead of running back to the {parent.label_word}. "
        f"Standing shoulder to shoulder made the dark feel smaller."
    )


def discover_gopher(world: World, trap: Trap) -> None:
    gopher = world.get("gopher")
    world.say(
        f"They stepped closer and peered carefully {trap.where}. There, blinking up at them, was a little gopher."
    )
    if gopher.memes["lonely"] >= THRESHOLD:
        world.say(
            "Its whiskers trembled, and its claws kept scraping for a way out. It looked much more lonely than spooky."
        )


def fetch_tool(world: World, a: Entity, b: Entity, tool: Tool, parent: Entity) -> None:
    world.say(
        f"{a.id} held the amber light steady while {b.id} fetched {tool.label} from near the shed. "
        f"They moved slowly so they would not frighten the gopher."
    )
    world.facts["tool_used"] = tool.id
    world.facts["helper_parent"] = parent.label_word


def rescue(world: World, a: Entity, b: Entity, trap: Trap, tool: Tool) -> None:
    gopher = world.get("gopher")
    gopher.meters["helped"] += 1
    propagate(world)
    world.say(
        f"Working as a team, they {tool.action}. {a.id} watched the edge, and {b.id} spoke in a soft voice the whole time."
    )
    if gopher.meters["safe"] >= THRESHOLD:
        world.say(
            "At last the gopher scrambled up, paused with its paws on the grass, and gave one quick blink as if it understood."
        )


def calm_reveal(world: World, illusion: Illusion) -> None:
    world.say(
        f"Now that they were not shaking anymore, the ghostly shape looked ordinary again. It was only {illusion.shape}, and the wind had done the rest."
    )


def ending(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"The gopher hurried into the safe dark under the plants, while {a.id} and {b.id} walked back through {place.label} side by side."
    )
    world.say(
        "The amber light still glowed, but it no longer seemed eerie. It looked warm, and the whole yard felt gentle again."
    )


def tell(
    place: Place,
    illusion: Illusion,
    trap: Trap,
    tool: Tool,
    child1: str = "Lily",
    child1_gender: str = "girl",
    child2: str = "Ben",
    child2_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, attrs={"role": "kid"}))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, attrs={"role": "kid"}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="illusion", type="thing", label=illusion.shape))
    world.add(Entity(id="gopher", type="animal", label="gopher", tags={"gopher"}))

    introduce(world, a, b, place)
    first_glimpse(world, a, b, illusion)

    world.para()
    hear_cry(world, trap)
    choose_kindness(world, a, b, parent)

    world.para()
    discover_gopher(world, trap)
    fetch_tool(world, a, b, tool, parent)
    rescue(world, a, b, trap, tool)

    world.para()
    calm_reveal(world, illusion)
    ending(world, a, b, place)

    world.facts.update(
        child1=a,
        child2=b,
        parent=parent,
        place_cfg=place,
        illusion_cfg=illusion,
        trap_cfg=trap,
        tool_cfg=tool,
        rescued=world.get("gopher").meters["safe"] >= THRESHOLD,
        teamwork=world.facts.get("teaming") is True,
        kindness=all(k.memes["kindness"] >= THRESHOLD for k in world.kids()),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    place = f["place_cfg"]
    trap = f["trap_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "gopher," "down," and "amber."',
        f"Tell a spooky-but-safe story where {a.id} and {b.id} think they see a ghost in {place.label}, then discover a small animal trapped {trap.where} and help it together.",
        "Write a short story about kindness and teamwork where a scary misunderstanding becomes a rescue."
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    parent = f["parent"]
    place = f["place_cfg"]
    illusion = f["illusion_cfg"]
    trap = f["trap_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}. They walked into {place.label} together and faced something spooky side by side."
        ),
        (
            "What made the place seem ghostly at first?",
            f"They saw {illusion.shape} in the evening light, and it moved in a strange way. In the dim amber glow, that ordinary thing looked almost like a ghost."
        ),
        (
            "What was really making the sad sound?",
            f"It was a little gopher trapped {trap.where}. The sound was not a ghostly moan after all, but a frightened animal calling from below."
        ),
        (
            "Why did the children stay instead of running away?",
            f"They realized something might be scared and stuck, so kindness mattered more than fear. Being together gave them courage, and teamwork made the dark feel less scary."
        ),
        (
            "How did they help the gopher?",
            f"They used {tool.label} and worked as a team. One child watched and steadied things while the other guided the rescue, which helped the gopher climb or ride out safely."
        ),
        (
            "How did the story end?",
            f"The gopher got out safely, and the children saw that the 'ghost' was only {illusion.shape}. The amber light that had seemed eerie at first looked warm by the end."
        ),
    ]
    if f.get("predicted_need", {}).get("still_stuck"):
        qa.append((
            f"Why was helping right away a kind choice?",
            f"If they had only run back to the {parent.label_word}, the gopher would have stayed stuck and lonely for longer. Helping gently right away turned a scary moment into a rescue."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "gopher", "kindness", "teamwork"}
    tool = world.facts["tool_cfg"]
    tags |= set(tool.tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        illusion="sheet",
        trap="window_well",
        tool="plank",
        child1="Lily",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="orchard",
        illusion="kite",
        trap="root_hollow",
        tool="blanket",
        child1="Mia",
        child1_gender="girl",
        child2="Sam",
        child2_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="shedyard",
        illusion="lantern_vine",
        trap="rain_barrel",
        tool="basket",
        child1="Zoe",
        child1_gender="girl",
        child2="Max",
        child2_gender="boy",
        parent="mother",
    ),
]


def explain_rejection(place: Place, illusion: Illusion, trap: Trap, tool: Tool) -> str:
    if not illusion_at_place(place, illusion):
        return (
            f"(No story: {illusion.shape} does not belong in {place.label}, so the spooky misunderstanding would feel arbitrary.)"
        )
    if not trap_at_place(place, trap):
        return (
            f"(No story: a {trap.label} is not a plausible problem spot in {place.label}.)"
        )
    if not tool_fits(trap, tool):
        return (
            f"(No story: {tool.label} is not a good way to help from a {trap.label}. "
            f"This rescue needs a method like '{trap.need}', not {sorted(tool.methods)}.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
fits(Tool, Trap) :- method_needed(Trap, M), has_method(Tool, M).
valid(Place, Illusion, Trap, Tool) :- place(Place), illusion(Illusion), trap(Trap), tool(Tool),
                                      affords_illusion(Place, Illusion),
                                      affords_trap(Place, Trap),
                                      fits(Tool, Trap).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for illusion_id in sorted(place.affords_illusions):
            lines.append(asp.fact("affords_illusion", place_id, illusion_id))
        for trap_id in sorted(place.affords_traps):
            lines.append(asp.fact("affords_trap", place_id, trap_id))
    for illusion_id in ILLUSIONS:
        lines.append(asp.fact("illusion", illusion_id))
    for trap_id, trap in TRAPS.items():
        lines.append(asp.fact("trap", trap_id))
        lines.append(asp.fact("method_needed", trap_id, trap.need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for method in sorted(tool.methods):
            lines.append(asp.fact("has_method", tool_id, method))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "gopher" not in sample.story.lower():
            raise StoryError("smoke test story was empty or missing the core animal")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle ghost story about kindness, teamwork, and a trapped gopher."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--illusion", choices=ILLUSIONS)
    ap.add_argument("--trap", choices=TRAPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.illusion and not illusion_at_place(PLACES[args.place], ILLUSIONS[args.illusion]):
        trap = TRAPS[args.trap] if args.trap else next(iter(TRAPS.values()))
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(PLACES[args.place], ILLUSIONS[args.illusion], trap, tool))
    if args.place and args.trap and not trap_at_place(PLACES[args.place], TRAPS[args.trap]):
        illusion = ILLUSIONS[args.illusion] if args.illusion else next(iter(ILLUSIONS.values()))
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(PLACES[args.place], illusion, TRAPS[args.trap], tool))
    if args.trap and args.tool and not tool_fits(TRAPS[args.trap], TOOLS[args.tool]):
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        illusion = ILLUSIONS[args.illusion] if args.illusion else next(iter(ILLUSIONS.values()))
        raise StoryError(explain_rejection(place, illusion, TRAPS[args.trap], TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.illusion is None or combo[1] == args.illusion)
        and (args.trap is None or combo[2] == args.trap)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, illusion_id, trap_id, tool_id = rng.choice(combos)
    child1, child1_gender = _pick_child(rng)
    child2, child2_gender = _pick_child(rng, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        illusion=illusion_id,
        trap=trap_id,
        tool=tool_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.illusion not in ILLUSIONS:
        raise StoryError(f"(Unknown illusion: {params.illusion})")
    if params.trap not in TRAPS:
        raise StoryError(f"(Unknown trap: {params.trap})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    place = PLACES[params.place]
    illusion = ILLUSIONS[params.illusion]
    trap = TRAPS[params.trap]
    tool = TOOLS[params.tool]

    if not (illusion_at_place(place, illusion) and trap_at_place(place, trap) and tool_fits(trap, tool)):
        raise StoryError(explain_rejection(place, illusion, trap, tool))

    world = tell(
        place=place,
        illusion=illusion,
        trap=trap,
        tool=tool,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, illusion, trap, tool) combos:\n")
        for place, illusion, trap, tool in combos:
            print(f"  {place:8} {illusion:12} {trap:12} {tool}")
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
            header = f"### {p.child1} & {p.child2}: {p.place}, {p.illusion}, {p.trap}, {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
