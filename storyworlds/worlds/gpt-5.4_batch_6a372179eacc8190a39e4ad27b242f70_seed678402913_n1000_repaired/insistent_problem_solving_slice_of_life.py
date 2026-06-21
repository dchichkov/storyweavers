#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py
=====================================================================

A standalone story world for a small slice-of-life problem-solving domain:
a child hears an insistent household noise at bedtime, asks for help, and
works with a grown-up to figure out what is making the sound and how to stop it.

The world model is intentionally small and concrete. Different noise sources
fit different fixes; unreasonable source/fix pairs are rejected. Stories are
state-driven: a calm evening turns into a small worry, the child and parent
investigate together, and the ending image shows the house becoming quiet again.

Run it
------
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py --source branch --fix tie_branch
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py --source faucet --fix tie_branch
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py --trace
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py --json
    python storyworlds/worlds/gpt-5.4/insistent_problem_solving_slice_of_life.py --verify
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

# Make the shared result containers importable when this script is run directly
# from storyworlds/worlds/gpt-5.4/.
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
class BedtimeActivity:
    id: str
    opening: str
    return_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class NoiseSource:
    id: str
    label: str
    phrase: str
    place: str
    sound: str
    beat: str
    cause: str
    clue: str
    result: str
    suitable_fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    quiet_result: str
    suitable_sources: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    activity: str
    source: str
    fix: str
    child_name: str
    child_gender: str
    parent: str
    comfort_item: str = ""
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_noise_spreads(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    child = world.entities.get("child")
    for ent in list(world.entities.values()):
        if ent.role != "source":
            continue
        if ent.meters["making_noise"] < THRESHOLD:
            continue
        sig = ("noise_spreads", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if room is not None:
            room.meters["noise"] += 1
            room.meters["rest"] -= 1
        if child is not None:
            child.memes["worry"] += 1
            child.memes["alert"] += 1
        out.append("__noise__")
    return out


def _r_quiet_returns(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    child = world.entities.get("child")
    source = world.entities.get("source")
    if room is None or child is None or source is None:
        return out
    if source.meters["making_noise"] > 0:
        return out
    if source.meters["quieted"] < THRESHOLD:
        return out
    sig = ("quiet_returns", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["noise"] = 0.0
    room.meters["rest"] += 1
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    out.append("__quiet__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_spreads", tag="physical", apply=_r_noise_spreads),
    Rule(name="quiet_returns", tag="physical", apply=_r_quiet_returns),
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


ACTIVITIES = {
    "reading": BedtimeActivity(
        id="reading",
        opening="After pajamas and a drink of water, {child} climbed into bed with a picture book.",
        return_line="{child} tucked the book under one arm and listened to the new quiet for a moment before turning another page.",
        tags={"bedtime", "book"},
    ),
    "drawing": BedtimeActivity(
        id="drawing",
        opening="After brushing teeth, {child} sat on the rug in pajamas and made one last crayon drawing before bed.",
        return_line="{child} set the crayons back in their box and smiled at how still the room felt now.",
        tags={"bedtime", "drawing"},
    ),
    "blocks": BedtimeActivity(
        id="blocks",
        opening="Before bed, {child} was building a small block house on the bedroom rug.",
        return_line="{child} straightened the tiny block roof and left the little house standing in the soft quiet.",
        tags={"bedtime", "blocks"},
    ),
}

SOURCES = {
    "branch": NoiseSource(
        id="branch",
        label="branch",
        phrase="a thin tree branch outside the bedroom window",
        place="outside the bedroom window",
        sound="an insistent tap at the glass",
        beat="Tap, tap, tap.",
        cause="the wind kept nudging the branch against the window",
        clue="In the porch light, the branch's shadow hopped across the curtain each time it touched the glass.",
        result="The branch bowed away from the window and stopped reaching for the glass.",
        suitable_fixes={"tie_branch"},
        tags={"branch", "window", "wind"},
    ),
    "vent": NoiseSource(
        id="vent",
        label="vent cover",
        phrase="a loose vent cover in the hallway",
        place="in the hallway",
        sound="an insistent rattle from the hall",
        beat="Rattle-rattle.",
        cause="the heater was blowing warm air under one loose corner of the vent cover",
        clue="When they stood in the hallway, they could see one silver corner shiver each time the warm air pushed through.",
        result="The vent cover sat flat again, and the hall stopped trembling with that little rattle.",
        suitable_fixes={"tighten_vent"},
        tags={"vent", "heater", "hallway"},
    ),
    "faucet": NoiseSource(
        id="faucet",
        label="faucet",
        phrase="the bathroom faucet",
        place="in the bathroom",
        sound="an insistent drip from the sink",
        beat="Plink. Plink. Plink.",
        cause="the cold-water handle had not been turned all the way off",
        clue="A bead of water kept swelling at the spout and dropping into the sink all over again.",
        result="The last bead of water let go, and then no new one came.",
        suitable_fixes={"close_faucet"},
        tags={"faucet", "water", "bathroom"},
    ),
    "chime": NoiseSource(
        id="chime",
        label="wind chime",
        phrase="the little wind chime by the porch door",
        place="by the porch door",
        sound="an insistent clink by the door",
        beat="Clink-clink-clink.",
        cause="the night breeze kept nudging the hanging chime against the wall",
        clue="Every time the breeze slipped in under the porch roof, the chime tapped the siding and swayed again.",
        result="Once it was hanging inside, the porch breeze could not reach it anymore.",
        suitable_fixes={"bring_chime_in"},
        tags={"chime", "wind", "porch"},
    ),
}

FIXES = {
    "tie_branch": Fix(
        id="tie_branch",
        label="garden tie",
        phrase="a soft garden tie from the basket by the back door",
        action="used the soft tie to loop the branch gently back toward the tree",
        quiet_result="That gave the branch a new place to rest instead of the window.",
        suitable_sources={"branch"},
        tags={"tie", "garden", "problem_solving"},
    ),
    "tighten_vent": Fix(
        id="tighten_vent",
        label="screwdriver",
        phrase="a small screwdriver from the kitchen drawer",
        action="gave the loose vent screw a careful turn until the metal cover sat snug",
        quiet_result="Once the corner was snug, the warm air could pass through without shaking it.",
        suitable_sources={"vent"},
        tags={"screwdriver", "tool", "problem_solving"},
    ),
    "close_faucet": Fix(
        id="close_faucet",
        label="steady turn",
        phrase="both hands on the cool faucet handle",
        action="turned the handle slowly until it settled all the way closed",
        quiet_result="The grown-up did not force it; they only turned it far enough to stop the drip.",
        suitable_sources={"faucet"},
        tags={"water", "sink", "problem_solving"},
    ),
    "bring_chime_in": Fix(
        id="bring_chime_in",
        label="quiet hook",
        phrase="the empty hook just inside the door",
        action="lifted the wind chime off its porch hook and hung it inside for the night",
        quiet_result="Inside, it could still be pretty in the morning without tapping at bedtime.",
        suitable_sources={"chime"},
        tags={"porch", "hook", "problem_solving"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Noah", "Eli", "Jack", "Finn", "Theo", "Owen"]
COMFORT_ITEMS = ["striped blanket", "plush rabbit", "small pillow", "soft bear", "favorite quilt", ""]

KNOWLEDGE = {
    "bedtime": [
        ("Why does a quiet room help at bedtime?",
         "A quiet room makes it easier for your body to settle down. When sounds stop surprising you, you can rest and feel sleepy.")
    ],
    "book": [
        ("Why do some children read before bed?",
         "Reading before bed can feel calm and cozy. A gentle story helps many children slow down at the end of the day.")
    ],
    "drawing": [
        ("Why can drawing feel relaxing?",
         "Drawing lets you focus on one small thing at a time. That can help your thoughts feel quieter too.")
    ],
    "blocks": [
        ("Why do children like building with blocks?",
         "Blocks let children make something with their hands and ideas. Even a small tower or house can feel satisfying to finish.")
    ],
    "branch": [
        ("Why might a tree branch tap a window at night?",
         "Wind can move a branch back and forth until it reaches the glass. Then it makes a tapping sound each time it touches.")
    ],
    "window": [
        ("Why do sounds seem louder at night?",
         "Nights are often quieter, so small sounds stand out more. A noise you hardly notice in the day can feel much bigger then.")
    ],
    "wind": [
        ("What can wind move around outside a house?",
         "Wind can sway branches, chimes, and other light things. When those things bump into something, they make noise.")
    ],
    "vent": [
        ("What does a vent do in a house?",
         "A vent lets warm or cool air move through the house. If a cover is loose, that moving air can make it rattle.")
    ],
    "heater": [
        ("Why might a heater make another object rattle?",
         "Moving air can push on a loose piece of metal or plastic again and again. That repeated push is what makes a rattle.")
    ],
    "faucet": [
        ("Why does a faucet drip?",
         "A faucet can drip when it is not turned fully off. Then water keeps collecting and falling one drop at a time.")
    ],
    "water": [
        ("Why does a dripping sound repeat over and over?",
         "Each drop forms, falls, and then another one starts to form. That is why the sound keeps coming back in a steady pattern.")
    ],
    "bathroom": [
        ("Why do bathroom sounds echo a little?",
         "Bathrooms often have hard walls, sinks, and floors. Hard surfaces bounce sound back instead of soaking it up.")
    ],
    "chime": [
        ("What is a wind chime?",
         "A wind chime is something that hangs and makes little musical sounds when air moves it. It is meant to ring softly in a breeze.")
    ],
    "porch": [
        ("Why might something hanging on a porch bump the wall?",
         "A porch can still catch a breeze, even at night. If something is hanging there, the breeze can swing it side to side.")
    ],
    "tool": [
        ("Why should a grown-up use a screwdriver carefully?",
         "A screwdriver is a real tool, so it needs steady hands and careful use. Children can watch and help notice the problem, but a grown-up should handle the tool.")
    ],
    "garden": [
        ("Why use a soft tie on a tree branch?",
         "A soft tie can hold the branch gently without hurting it. The branch is moved just enough to keep it off the window.")
    ],
    "sink": [
        ("What is a sink for?",
         "A sink holds water while people wash hands, brush teeth, or clean things. That is why a dripping faucet is easy to hear there.")
    ],
    "hook": [
        ("What does a hook do?",
         "A hook holds something in one place. Moving an object to a better hook can stop it from bumping and making noise.")
    ],
}
KNOWLEDGE_ORDER = [
    "bedtime", "book", "drawing", "blocks", "branch", "window", "wind",
    "vent", "heater", "faucet", "water", "bathroom", "chime", "porch",
    "tool", "garden", "sink", "hook",
]


def valid_combo(source_id: str, fix_id: str) -> bool:
    return source_id in SOURCES and fix_id in FIXES and fix_id in SOURCES[source_id].suitable_fixes


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for source_id in sorted(SOURCES):
        for fix_id in sorted(FIXES):
            if valid_combo(source_id, fix_id):
                combos.append((source_id, fix_id))
    return combos


def explain_rejection(source: NoiseSource, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not sensibly solve {source.phrase}. "
        f"The sound there comes from {source.cause}, so pick a fix that matches that cause.)"
    )


def predict_solution(world: World, source_id: str, fix_id: str) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source_cfg = SOURCES[source_id]
    source.attrs["cfg"] = source_cfg.id
    source.meters["making_noise"] = 1.0
    propagate(sim, narrate=False)
    solved = False
    if valid_combo(source_id, fix_id):
        source.meters["making_noise"] = 0.0
        source.meters["quieted"] = 1.0
        propagate(sim, narrate=False)
        solved = sim.get("room").meters["noise"] == 0.0
    return {
        "noisy": sim.get("room").meters["noise"] >= THRESHOLD,
        "solved": solved,
    }


def settle_in(world: World, child: Entity, parent: Entity, activity: BedtimeActivity) -> None:
    child.memes["calm"] += 1
    parent.memes["patience"] += 1
    world.say(activity.opening.format(child=child.id))
    world.say(
        f"{parent.label_word.capitalize()} was nearby, finishing the last small jobs of the evening while keeping an ear on {child.id}."
    )


def noise_begins(world: World, child: Entity, source_cfg: NoiseSource) -> None:
    source = world.get("source")
    source.meters["making_noise"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {source_cfg.beat} It was {source_cfg.sound}, too steady to ignore.")
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} held still and listened. The sound did not hurry away; it just kept coming back, insistent and small."
        )


def ask_for_help(world: World, child: Entity, parent: Entity, source_cfg: NoiseSource) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}," {child.id} said, "what is that sound?"'
    )
    world.say(
        f'{parent.label_word.capitalize()} paused, listened with {parent.pronoun("possessive")} head tipped a little, and said, '
        f'"Let\'s find out together."'
    )
    world.facts["source_place"] = source_cfg.place


def investigate(world: World, child: Entity, parent: Entity, source_cfg: NoiseSource) -> None:
    child.memes["curiosity"] += 1
    parent.memes["attention"] += 1
    world.say(
        f"They followed the noise to {source_cfg.place}. {source_cfg.clue}"
    )
    world.say(
        f'{parent.label_word.capitalize()} whispered, "I think I know it now. {source_cfg.cause.capitalize()}."'
    )


def solve(world: World, child: Entity, parent: Entity, source_cfg: NoiseSource, fix_cfg: Fix) -> None:
    if not valid_combo(source_cfg.id, fix_cfg.id):
        raise StoryError(explain_rejection(source_cfg, fix_cfg))
    source = world.get("source")
    world.say(
        f"{parent.label_word.capitalize()} took {fix_cfg.phrase} and {fix_cfg.action}. {fix_cfg.quiet_result}"
    )
    source.meters["making_noise"] = 0.0
    source.meters["quieted"] = 1.0
    child.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(source_cfg.result)
    world.say("They both waited for the sound to come again, but the house stayed still.")
    world.facts["solved"] = True


def ending(world: World, child: Entity, parent: Entity, activity: BedtimeActivity, comfort_item: str) -> None:
    if child.memes["relief"] >= THRESHOLD:
        child.memes["calm"] += 1
        world.say(
            f"{child.id} let out a slow breath. The room felt bigger once the noise was gone."
        )
    if comfort_item:
        world.say(f"{child.id} pulled {child.pronoun('possessive')} {comfort_item} close.")
    world.say(activity.return_line.format(child=child.id))
    world.say(
        f'"Much better," {child.id} said, and {parent.label_word} smiled at the quiet house.'
    )


def tell(activity: BedtimeActivity, source_cfg: NoiseSource, fix_cfg: Fix,
         child_name: str = "Lily", child_gender: str = "girl",
         parent_type: str = "mother", comfort_item: str = "") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = world.add(Entity(id="room", type="room", label="bedroom"))
    source = world.add(Entity(
        id="source",
        type="thing",
        label=source_cfg.label,
        phrase=source_cfg.phrase,
        role="source",
        tags=set(source_cfg.tags),
        attrs={"cfg": source_cfg.id},
    ))

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        source=source,
        activity=activity,
        source_cfg=source_cfg,
        fix_cfg=fix_cfg,
        child_name=child_name,
        comfort_item=comfort_item,
        solved=False,
    )

    settle_in(world, child, parent, activity)
    world.para()
    noise_begins(world, child, source_cfg)
    ask_for_help(world, child, parent, source_cfg)
    world.para()
    investigate(world, child, parent, source_cfg)
    solve(world, child, parent, source_cfg, fix_cfg)
    world.para()
    ending(world, child, parent, activity, comfort_item)
    return world


CURATED = [
    StoryParams(
        activity="reading",
        source="branch",
        fix="tie_branch",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        comfort_item="striped blanket",
    ),
    StoryParams(
        activity="drawing",
        source="vent",
        fix="tighten_vent",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        comfort_item="small pillow",
    ),
    StoryParams(
        activity="blocks",
        source="faucet",
        fix="close_faucet",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        comfort_item="soft bear",
    ),
    StoryParams(
        activity="reading",
        source="chime",
        fix="bring_chime_in",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        comfort_item="favorite quilt",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source_cfg = f["source_cfg"]
    activity = f["activity"]
    parent = f["parent"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "insistent" and centers on bedtime problem solving.',
        f"Tell a gentle household story where {child.label}, a little {child.type}, hears {source_cfg.sound} while {activity.id} before bed, and {parent.label_word} helps {child.pronoun('object')} figure it out.",
        f"Write a calm story about a child and parent listening carefully, finding the cause of a repeating noise, and ending with the house quiet again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    source_cfg = f["source_cfg"]
    fix_cfg = f["fix_cfg"]
    activity = f["activity"]
    name = child.label
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a little {child.type}, and {name}'s {pw}. They solve a small bedtime problem together."
        ),
        (
            "What was happening at the start of the story?",
            f"At the start, {name} was {activity.id} quietly before bed. The evening felt ordinary and calm until the sound began."
        ),
        (
            "What was the problem?",
            f"The problem was {source_cfg.sound}. It kept repeating, so {name} could not ignore it and started to worry."
        ),
        (
            f"Why did {name} ask {name}'s {pw} for help?",
            f"{name} asked for help because the noise kept coming back and {name} did not know what was making it. The sound was insistent, so it felt important to figure out."
        ),
        (
            "How did they figure out what the sound was?",
            f"They listened carefully and followed the noise to {source_cfg.place}. Then they noticed a clue: {source_cfg.clue}"
        ),
        (
            "How did they solve the problem?",
            f"They solved it when {pw} {fix_cfg.action}. That worked because {source_cfg.cause}."
        ),
        (
            "How did the story end?",
            f"It ended with the house quiet again and {name} feeling relieved. The quiet itself showed that their idea had worked."
        ),
    ]
    comfort_item = f.get("comfort_item", "")
    if comfort_item:
        qa.append(
            (
                f"What did {name} do once the sound was gone?",
                f"{name} pulled {child.pronoun('possessive')} {comfort_item} close and settled back down. That small bedtime habit showed {name} felt safe again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["activity"].tags) | set(f["source_cfg"].tags) | set(f["fix_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, F) :- source(S), fix(F), solves(F, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in sorted(ACTIVITIES):
        lines.append(asp.fact("activity", aid))
    for sid in sorted(SOURCES):
        lines.append(asp.fact("source", sid))
    for fid in sorted(FIXES):
        lines.append(asp.fact("fix", fid))
    for sid, source in SOURCES.items():
        for fid in sorted(source.suitable_fixes):
            lines.append(asp.fact("solves", fid, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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

    smoke_cases: list[StoryParams] = list(CURATED)
    for seed in range(5):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed unexpectedly on seed {seed}.")
            break

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
            buf = io.StringIO()
            with redirect_stdout(buf):
                emit(sample, trace=False, qa=False, header="")
        except Exception as err:
            rc = 1
            print(f"ERROR: smoke test failed for {params}: {err}")
            break
    else:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an insistent bedtime noise, careful listening, and a small household solution."
    )
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (source, fix) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source is not None and args.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{args.source}').")
    if args.fix is not None and args.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{args.fix}').")
    if args.activity is not None and args.activity not in ACTIVITIES:
        raise StoryError(f"(No story: unknown activity '{args.activity}').")

    if args.source and args.fix:
        source_cfg = SOURCES[args.source]
        fix_cfg = FIXES[args.fix]
        if not valid_combo(args.source, args.fix):
            raise StoryError(explain_rejection(source_cfg, fix_cfg))

    combos = [
        combo for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.fix is None or combo[1] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    source_id, fix_id = rng.choice(sorted(combos))
    activity_id = args.activity or rng.choice(sorted(ACTIVITIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or pick_name(rng, gender)
    parent_type = args.parent or rng.choice(["mother", "father"])
    comfort_item = rng.choice(COMFORT_ITEMS)

    return StoryParams(
        activity=activity_id,
        source=source_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent_type,
        comfort_item=comfort_item,
    )


def generate(params: StoryParams) -> StorySample:
    if params.activity not in ACTIVITIES:
        raise StoryError(f"(No story: unknown activity '{params.activity}').")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}').")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}').")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.child_gender}').")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown parent '{params.parent}').")
    if not valid_combo(params.source, params.fix):
        raise StoryError(explain_rejection(SOURCES[params.source], FIXES[params.fix]))

    world = tell(
        activity=ACTIVITIES[params.activity],
        source_cfg=SOURCES[params.source],
        fix_cfg=FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        comfort_item=params.comfort_item,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (source, fix) pairs:\n")
        for source_id, fix_id in combos:
            print(f"  {source_id:8} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for i, params in enumerate(CURATED):
            p = StoryParams(
                activity=params.activity,
                source=params.source,
                fix=params.fix,
                child_name=params.child_name,
                child_gender=params.child_gender,
                parent=params.parent,
                comfort_item=params.comfort_item,
                seed=(base_seed + i),
            )
            samples.append(generate(p))
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
            header = f"### {p.child_name}: {p.source} -> {p.fix} ({p.activity})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
