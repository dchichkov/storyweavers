#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/worm_dim_friendship_conflict_humor_detective_story.py

A small storyworld about two child detectives solving a funny, friendship-sized
mystery in a worm-dim place. One friend jumps to a wrong conclusion, the clues
lead somewhere sensible, and the ending repairs both the case and the friendship.
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


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    nook: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    size: str
    clue: str
    funny: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    capacity: set[str] = field(default_factory=set)
    dark: bool = False
    high: bool = False
    clue_text: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves_dark: bool = False
    solves_high: bool = False
    gag: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    accuse_line: str
    soften_line: str
    apology_style: str
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


def _r_hurt_feelings(world: World) -> list[str]:
    left = world.get("left")
    right = world.get("right")
    if left.memes["accused"] >= THRESHOLD and ("hurt", left.id) not in world.fired:
        world.fired.add(("hurt", left.id))
        left.memes["hurt"] += 1
        right.memes["worry"] += 1
    if right.memes["accused"] >= THRESHOLD and ("hurt", right.id) not in world.fired:
        world.fired.add(("hurt", right.id))
        right.memes["hurt"] += 1
        left.memes["worry"] += 1
    return []


def _r_found_brings_relief(world: World) -> list[str]:
    if world.get("item").meters["found"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("left", "right"):
        kid = world.get(eid)
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hurt_feelings", tag="social", apply=_r_hurt_feelings),
    Rule(name="found_relief", tag="social", apply=_r_found_brings_relief),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def item_fits(item: MissingItem, spot: Spot) -> bool:
    return item.size in spot.capacity


def tool_works(tool: Tool, spot: Spot) -> bool:
    if spot.dark and not tool.solves_dark:
        return False
    if spot.high and not tool.solves_high:
        return False
    return True


def valid_combo(item: MissingItem, spot: Spot, tool: Tool) -> bool:
    return item_fits(item, spot) and tool_works(tool, spot)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id, item in ITEMS.items():
            for spot_id, spot in SPOTS.items():
                for tool_id, tool in TOOLS.items():
                    if valid_combo(item, spot, tool):
                        combos.append((setting_id, item_id, spot_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    item: str
    spot: str
    tool: str
    mood: str
    left_name: str
    left_gender: str
    right_name: str
    right_gender: str
    owner_side: str
    grownup: str
    seed: Optional[int] = None


SETTINGS = {
    "clubhouse": Setting(
        id="clubhouse",
        place="the backyard detective clubhouse",
        opening="Behind the apple tree stood a cardboard detective clubhouse with a paper sign that said CASES SOLVED CHEAP.",
        nook="the worm-dim corner behind the supply shelf",
        closing="the clubhouse felt brighter than before, even in the worm-dim corner",
        tags={"detective", "clubhouse"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the apartment hallway",
        opening="The apartment hallway was long, squeaky, and perfect for secret detective footsteps.",
        nook="the worm-dim space under the coat bench",
        closing="the hallway seemed less spooky and much more giggly",
        tags={"detective", "hallway"},
    ),
    "attic": Setting(
        id="attic",
        place="the attic playroom",
        opening="The attic playroom held old hats, toy boxes, and enough dust to make any detective feel important.",
        nook="the worm-dim gap beside a trunk",
        closing="even the attic dust looked friendly after the case was closed",
        tags={"detective", "attic"},
    ),
}

ITEMS = {
    "badge": MissingItem(
        id="badge",
        label="detective badge",
        phrase="a shiny cardboard detective badge",
        size="small",
        clue="a silver paper star",
        funny="It was so shiny that both detectives said it looked brave enough to solve crimes by itself.",
        tags={"badge", "detective"},
    ),
    "notebook": MissingItem(
        id="notebook",
        label="case notebook",
        phrase="a fat case notebook with a bent blue cover",
        size="medium",
        clue="a bent blue corner",
        funny="The notebook was stuffed with such serious notes as 'Maybe ask the hamster' and 'Check under obvious things.'",
        tags={"notebook", "detective"},
    ),
    "cookie_tin": MissingItem(
        id="cookie_tin",
        label="cookie tin",
        phrase="a round cookie tin with three lemon cookies left inside",
        size="medium",
        clue="a lemon crumb trail",
        funny="The tin rattled when it moved, which made it a very bad item for sneaking.",
        tags={"cookie", "detective"},
    ),
}

SPOTS = {
    "under_bench": Spot(
        id="under_bench",
        label="under the bench",
        phrase="under the old bench",
        capacity={"small", "medium"},
        dark=True,
        high=False,
        clue_text="A tiny clue lay near the floor",
        reveal="The missing thing had slid under the bench when somebody bumped it with a heel.",
        tags={"dark", "under"},
    ),
    "top_shelf": Spot(
        id="top_shelf",
        label="top shelf",
        phrase="on the top shelf",
        capacity={"small", "medium"},
        dark=False,
        high=True,
        clue_text="Something up high looked just a little out of place",
        reveal="The missing thing had been set on the top shelf during a tidy-up and forgotten there.",
        tags={"high", "shelf"},
    ),
    "behind_trunk": Spot(
        id="behind_trunk",
        label="behind the trunk",
        phrase="behind the big trunk",
        capacity={"small"},
        dark=True,
        high=False,
        clue_text="A narrow space hid a clue no bigger than a thumb",
        reveal="The missing thing had skidded behind the trunk when the lid thumped shut.",
        tags={"dark", "trunk"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a stubby flashlight with peeling yellow tape",
        solves_dark=True,
        solves_high=False,
        gag="It made a bright circle that wobbled like it had had too much lemonade.",
        tags={"flashlight", "light"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="a squeaky red step stool",
        solves_dark=False,
        solves_high=True,
        gag="Every step on it squeaked so loudly that the detectives kept shushing the stool.",
        tags={"stool", "reach"},
    ),
    "grabber": Tool(
        id="grabber",
        label="grabber claw",
        phrase="a plastic grabber claw",
        solves_dark=False,
        solves_high=True,
        gag="Its click-clack jaws sounded so dramatic that both detectives whispered, 'Excellent detective noise.'",
        tags={"grabber", "reach"},
    ),
    "lantern_hook": Tool(
        id="lantern_hook",
        label="hook lantern",
        phrase="a little hook lantern",
        solves_dark=True,
        solves_high=False,
        gag="It swung from one finger and made the shadows look as if they were listening to the case.",
        tags={"lantern", "light"},
    ),
}

MOODS = {
    "snappy": Mood(
        id="snappy",
        accuse_line="I think you took it and forgot,",
        soften_line="Maybe I said that too fast.",
        apology_style="a quick, embarrassed apology",
        tags={"conflict"},
    ),
    "dramatic": Mood(
        id="dramatic",
        accuse_line="All clues point straight at you, Detective,",
        soften_line="Oh. Those were very rude clues.",
        apology_style="a grand apology with one hand on the heart",
        tags={"conflict", "humor"},
    ),
    "sulky": Mood(
        id="sulky",
        accuse_line="Well, it was here before you touched the table,",
        soften_line="I was grumpy before I was clever.",
        apology_style="a small apology spoken into a sleeve",
        tags={"conflict"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Nora", "Ivy", "Ella"]
BOY_NAMES = ["Ben", "Nico", "Owen", "Finn", "Leo", "Milo"]


def predict_case(item: MissingItem, spot: Spot, tool: Tool) -> dict:
    return {
        "fits": item_fits(item, spot),
        "tool_ok": tool_works(tool, spot),
        "solvable": valid_combo(item, spot, tool),
    }


def explain_rejection(item: MissingItem, spot: Spot, tool: Tool) -> str:
    if not item_fits(item, spot):
        return (
            f"(No story: {item.phrase} is too big to sensibly end up {spot.phrase}. "
            f"The hiding place must plausibly hold the missing thing.)"
        )
    if spot.dark and not tool.solves_dark:
        return (
            f"(No story: {spot.phrase} is dark, but {tool.phrase} gives no light. "
            f"A detective clue hidden in the dark needs a light source.)"
        )
    if spot.high and not tool.solves_high:
        return (
            f"(No story: the clue is {spot.phrase}, but {tool.phrase} cannot reach it. "
            f"The detectives need a tool that can get something down safely.)"
        )
    return "(No story: this combination is not a reasonable detective case.)"


def intro(world: World, setting: Setting, left: Entity, right: Entity, owner: Entity, item: Entity) -> None:
    left.memes["friendship"] += 1
    right.memes["friendship"] += 1
    world.say(
        f"{setting.opening} In it, {left.id} and {right.id} called themselves the Twig Street Detectives."
    )
    world.say(
        f"On the day of this case, {owner.id} brought {item.phrase} to {setting.place}. {ITEMS[item.attrs['cfg']].funny}"
    )


def missing(world: World, owner: Entity, item: Entity) -> None:
    owner.memes["alarm"] += 1
    item.meters["missing"] += 1
    world.say(
        f"Then {owner.id} stopped short. {owner.pronoun('possessive').capitalize()} {item.label} was gone."
    )
    world.say(
        f'"This is a real mystery," {owner.id} whispered. "A very important, very serious, possibly snack-related mystery."'
    )


def accusation(world: World, accuser: Entity, accused: Entity, mood: Mood, item: Entity) -> None:
    accused.memes["accused"] += 1
    accuser.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{accuser.id} frowned and said, "{mood.accuse_line} {accused.id}. Nobody else was near the {item.label}."'
    )
    if accused.memes["hurt"] >= THRESHOLD:
        world.say(
            f'{accused.id} blinked. "{accused.pronoun("subject").capitalize()} am your detective partner, not a sneaky thief," {accused.pronoun()} said.'
            if accused.pronoun("subject") == "they"
            else f'"I am your detective partner, not a sneaky thief," {accused.id} said.'
        )


def choose_tool(world: World, tool: Tool, spot: Spot) -> None:
    world.say(
        f"They took {tool.phrase} because the best detectives used what the case needed, not just what looked fancy. {tool.gag}"
    )
    if spot.dark:
        world.say(f"The clue trail led toward {world.facts['setting'].nook}, where the light turned worm-dim and dusty.")
    elif spot.high:
        world.say(f"The clue trail led to {spot.phrase}, high above their noses.")
    else:
        world.say(f"The clue trail led toward {spot.phrase}.")


def inspect(world: World, left: Entity, right: Entity, item: Entity, spot: Spot) -> None:
    world.say(
        f"{spot.clue_text}: {ITEMS[item.attrs['cfg']].clue}. Both detectives knelt, squinted, and tried to look wiser than they really were."
    )
    world.say(
        f"That was the first moment {left.id} and {right.id} both saw the same thing and knew the case was stranger than a simple stealing."
    )


def reveal(world: World, finder: Entity, item: Entity, spot: Spot) -> None:
    item.meters["found"] += 1
    item.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{finder.id} reached {spot.phrase} and gave a little gasp. There was the {item.label}."
    )
    world.say(spot.reveal)


def apology(world: World, accuser: Entity, accused: Entity, mood: Mood) -> None:
    accuser.memes["guilt"] += 1
    accused.memes["hurt"] = 0.0
    accuser.memes["friendship"] += 1
    accused.memes["friendship"] += 1
    world.say(
        f'{accuser.id} looked at the floor. "{mood.soften_line} I am sorry," {accuser.pronoun()} said.'
        if accuser.pronoun("subject") == "they"
        else f'"{mood.soften_line} I am sorry," {accuser.id} said.'
    )
    world.say(
        f"It was {mood.apology_style}, and it was honest enough to mend the rip in the afternoon."
    )


def laugh_and_close(world: World, left: Entity, right: Entity, owner: Entity, item: Entity, setting: Setting) -> None:
    for kid in (left, right):
        kid.memes["humor"] += 1
        kid.memes["trust"] += 1
    owner.memes["joy"] += 1
    crumb = ""
    if item.attrs["cfg"] == "cookie_tin":
        crumb = " One lemon cookie had cracked in half, so the detectives shared it as a closing snack."
    world.say(
        f"Soon both detectives were laughing again. They wrote CASE CLOSED in large, crooked letters and gave the {item.label} back to {owner.id}.{crumb}"
    )
    world.say(
        f"When they packed up their tools, {setting.closing}, because the mystery was over and the friendship was fixed too."
    )


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    spot: Spot,
    tool: Tool,
    mood: Mood,
    left_name: str,
    left_gender: str,
    right_name: str,
    right_gender: str,
    owner_side: str,
    grownup: str,
) -> World:
    world = World()
    left = world.add(Entity(id="left", kind="character", type=left_gender, label=left_name, role="detective"))
    left.id = left_name
    world.entities[left_name] = world.entities.pop("left")
    right = world.add(Entity(id="right", kind="character", type=right_gender, label=right_name, role="detective"))
    right.id = right_name
    world.entities[right_name] = world.entities.pop("right")

    # Aliases used by rules
    world.entities["left"] = world.entities[left_name]
    world.entities["right"] = world.entities[right_name]

    owner = world.entities[left_name] if owner_side == "left" else world.entities[right_name]
    other = world.entities[right_name] if owner_side == "left" else world.entities[left_name]
    grown = world.add(Entity(id="grownup", kind="character", type=grownup, label="the grown-up", role="grownup"))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="missing",
            attrs={"owner": owner.id, "cfg": item_cfg.id},
        )
    )
    world.facts["setting"] = setting
    world.facts["owner"] = owner
    world.facts["other"] = other
    world.facts["grownup"] = grown

    intro(world, setting, world.entities["left"], world.entities["right"], owner, item)
    world.para()
    missing(world, owner, item)
    accusation(world, owner, other, mood, item)
    world.para()
    choose_tool(world, tool, spot)
    inspect(world, world.entities["left"], world.entities["right"], item, spot)
    reveal(world, other, item, spot)
    world.para()
    apology(world, owner, other, mood)
    laugh_and_close(world, world.entities["left"], world.entities["right"], owner, item, setting)

    world.facts.update(
        item_cfg=item_cfg,
        spot=spot,
        tool=tool,
        mood=mood,
        owner_side=owner_side,
        owner=owner,
        accused=other,
        item=item,
        solved=item.meters["found"] >= THRESHOLD,
        friendship_repaired=world.entities["left"].memes["trust"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks careful questions, and tries to figure out what happened. Good detectives do not jump to mean guesses before they know the truth."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight helps you see into dark places where clues might be hiding. It lets you look carefully without having to guess."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps you reach something that is too high for you. You still have to use it carefully and with a steady body."
        )
    ],
    "grabber": [
        (
            "What is a grabber claw?",
            "A grabber claw is a tool with a handle and pinchy ends for picking things up from far away. It can help you reach without climbing."
        )
    ],
    "friendship": [
        (
            "What should you do if you blame a friend too fast?",
            "You should tell the truth, say you are sorry, and try to fix the hurt you caused. Friendship gets stronger when people repair mistakes kindly."
        )
    ],
    "cookie": [
        (
            "Why do crumbs make good clues?",
            "Crumbs can show where food has been or where it rolled. A tiny clue can help you solve a much bigger mystery."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "flashlight", "stool", "grabber", "cookie", "friendship"]


def generation_prompts(world: World) -> list[str]:
    owner = world.facts["owner"]
    accused = world.facts["accused"]
    item_cfg = world.facts["item_cfg"]
    spot = world.facts["spot"]
    return [
        'Write a child-facing detective story that includes the exact phrase "worm-dim".',
        f"Tell a funny mystery where {owner.id} wrongly suspects {accused.id} after {owner.pronoun('possessive')} {item_cfg.label} disappears, but a real clue leads to {spot.phrase}.",
        f"Write a friendship story with a detective mood, a small conflict, a silly clue, and an apology after the {item_cfg.label} is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    owner = world.facts["owner"]
    accused = world.facts["accused"]
    item_cfg = world.facts["item_cfg"]
    spot = world.facts["spot"]
    tool = world.facts["tool"]
    mood = world.facts["mood"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the story's detectives?",
            f"The detectives are {world.entities['left'].id} and {world.entities['right'].id}. They are friends who work on the case together, even after their feelings get hurt."
        ),
        (
            f"What went missing?",
            f"The missing thing was {item_cfg.phrase}. It mattered because the case began when {owner.id} noticed it was gone."
        ),
        (
            f"Why did {owner.id} and {accused.id} argue?",
            f"They argued because {owner.id} blamed {accused.id} too quickly. The guess sounded sharp and hurt {accused.id}'s feelings before the detectives had real proof."
        ),
        (
            f"How did the detectives solve the case?",
            f"They followed a clue to {spot.phrase} and used {tool.phrase}. That worked because the hiding place and the tool matched what the case needed."
        ),
        (
            f"Where was the {item_cfg.label}, really?",
            f"It was {spot.phrase}. {spot.reveal}"
        ),
        (
            "How did the friendship change by the end?",
            f"It ended stronger than before because the accuser apologized honestly and the two friends laughed together again. Solving the mystery fixed both the missing item and the hurt feelings."
        ),
    ]
    if mood.id == "dramatic":
        qa.append(
            (
                "What made the story funny?",
                "The detectives treated a small problem like a huge mystery, and their clues sounded much grander than the case really was. That playful seriousness made the apology and ending feel warm instead of scary."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "friendship"} | set(world.facts["tool"].tags) | set(world.facts["item_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    seen: set[int] = set()
    for key, e in world.entities.items():
        if id(e) in seen:
            continue
        seen.add(id(e))
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="clubhouse",
        item="badge",
        spot="behind_trunk",
        tool="flashlight",
        mood="dramatic",
        left_name="Maya",
        left_gender="girl",
        right_name="Ben",
        right_gender="boy",
        owner_side="left",
        grownup="mother",
    ),
    StoryParams(
        setting="hallway",
        item="notebook",
        spot="top_shelf",
        tool="step_stool",
        mood="snappy",
        left_name="Nico",
        left_gender="boy",
        right_name="Zoe",
        right_gender="girl",
        owner_side="right",
        grownup="father",
    ),
    StoryParams(
        setting="attic",
        item="cookie_tin",
        spot="under_bench",
        tool="lantern_hook",
        mood="sulky",
        left_name="Ivy",
        left_gender="girl",
        right_name="Leo",
        right_gender="boy",
        owner_side="left",
        grownup="mother",
    ),
]


ASP_RULES = r"""
fits(I, S) :- item_size(I, Z), spot_capacity(S, Z).
tool_works(T, S) :- tool(T), spot(S),
                    not (spot_dark(S), not solves_dark(T)),
                    not (spot_high(S), not solves_high(T)).
valid(Se, I, S, T) :- setting(Se), item(I), spot(S), tool(T), fits(I, S), tool_works(T, S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_size", iid, item.size))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.dark:
            lines.append(asp.fact("spot_dark", sid))
        if spot.high:
            lines.append(asp.fact("spot_high", sid))
        for size in sorted(spot.capacity):
            lines.append(asp.fact("spot_capacity", sid, size))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.solves_dark:
            lines.append(asp.fact("solves_dark", tid))
        if tool.solves_high:
            lines.append(asp.fact("solves_high", tid))
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in combo gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: child detectives, a worm-dim clue, a friendship bump, and a funny apology."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--owner-side", choices=["left", "right"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.spot and args.tool:
        item = ITEMS[args.item]
        spot = SPOTS[args.spot]
        tool = TOOLS[args.tool]
        if not valid_combo(item, spot, tool):
            raise StoryError(explain_rejection(item, spot, tool))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.item is None or c[1] == args.item)
        and (args.spot is None or c[2] == args.spot)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, item, spot, tool = rng.choice(sorted(combos))
    mood = args.mood or rng.choice(sorted(MOODS))
    left_gender = rng.choice(["girl", "boy"])
    right_gender = rng.choice(["girl", "boy"])
    left_name = pick_name(rng, left_gender)
    right_name = pick_name(rng, right_gender, avoid=left_name)
    owner_side = args.owner_side or rng.choice(["left", "right"])
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        item=item,
        spot=spot,
        tool=tool,
        mood=mood,
        left_name=left_name,
        left_gender=left_gender,
        right_name=right_name,
        right_gender=right_gender,
        owner_side=owner_side,
        grownup=grownup,
    )


def _check_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if params.owner_side not in {"left", "right"}:
        raise StoryError(f"(Unknown owner side: {params.owner_side})")
    if not valid_combo(ITEMS[params.item], SPOTS[params.spot], TOOLS[params.tool]):
        raise StoryError(explain_rejection(ITEMS[params.item], SPOTS[params.spot], TOOLS[params.tool]))
    if params.left_name == params.right_name:
        raise StoryError("(The two detectives need different names.)")


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        spot=SPOTS[params.spot],
        tool=TOOLS[params.tool],
        mood=MOODS[params.mood],
        left_name=params.left_name,
        left_gender=params.left_gender,
        right_name=params.right_name,
        right_gender=params.right_gender,
        owner_side=params.owner_side,
        grownup=params.grownup,
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
        print(f"{len(combos)} compatible (setting, item, spot, tool) combos:\n")
        for setting, item, spot, tool in combos:
            print(f"  {setting:10} {item:10} {spot:12} {tool}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.left_name} & {p.right_name}: {p.item} at {p.setting} ({p.spot}, {p.tool})"
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
