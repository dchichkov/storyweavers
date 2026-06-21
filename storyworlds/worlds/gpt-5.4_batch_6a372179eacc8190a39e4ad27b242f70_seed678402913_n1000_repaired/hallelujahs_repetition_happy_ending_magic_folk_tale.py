#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hallelujahs_repetition_happy_ending_magic_folk_tale.py
==================================================================================

A small story world for a folk-tale pattern built around magical repetition:
a child must carry three "hallelujahs" to a silent hill, each one won through
a kind act, and the third sung word wakes a sleeping blessing over the valley.

The world model is simple and state-driven:

- the valley has a missing blessing (light, rain, or song)
- the hero meets three helpers in sequence
- each helper asks for a fitting kindness
- every accepted kindness earns one hallelujah
- three hallelujahs sung at the hill wake the sleeping charm
- the valley changes, and the ending image proves the blessing returned

The script follows the Storyweavers storyworld contract:
- standalone stdlib-only Python
- eager import of results.py
- Python reasonableness gate plus inline ASP twin
- generate/emit/main interface with --verify, --asp, --show-asp, etc.
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "woman", "mother", "queen", "grandmother", "hen"}
        male = {"boy", "man", "father", "king", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Blessing:
    id: str
    loss_text: str
    return_text: str
    hill_effect: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    phrase: str
    need: str
    thanks: str
    gift_line: str
    favor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    object_phrase: str
    success_line: str
    impossible_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    magic_line: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_hope_grows(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    valley = world.entities.get("valley")
    if hero is None or valley is None:
        return out
    count = int(hero.meters["hallelujahs"])
    for need in (1, 2, 3):
        sig = ("hope", need)
        if count >= need and sig not in world.fired:
            world.fired.add(sig)
            valley.memes["hope"] += 1
            out.append("__hope__")
    return out


def _r_wake_blessing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    valley = world.entities.get("valley")
    hill = world.entities.get("hill")
    if hero is None or valley is None or hill is None:
        return out
    if hero.meters["hallelujahs"] >= 3 and hill.meters["sung"] >= 3:
        sig = ("blessing", "awake")
        if sig not in world.fired:
            world.fired.add(sig)
            valley.meters["restored"] = 1
            valley.meters["lack"] = 0
            out.append("__restored__")
    return out


CAUSAL_RULES = [
    Rule(name="hope_grows", apply=_r_hope_grows),
    Rule(name="wake_blessing", apply=_r_wake_blessing),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


BLESSINGS = {
    "spring": Blessing(
        id="spring",
        loss_text="For many weeks no green thing had risen in the valley, and even the brook sounded tired.",
        return_text="At once the sleeping spring stirred under the hill.",
        hill_effect="green light ran through the roots under the grass",
        end_image="By evening the orchard wore soft new leaves, and the whole valley looked washed with green.",
        tags={"spring", "magic", "valley"},
    ),
    "rain": Blessing(
        id="rain",
        loss_text="For many weeks the clouds had shut their jars, and the fields lay thirsty and pale.",
        return_text="At once the sleeping rain woke in the clouds above the hill.",
        hill_effect="silver drops began tapping on the stones",
        end_image="By evening the fields drank deeply, and the valley shone with puddles like little mirrors.",
        tags={"rain", "magic", "valley"},
    ),
    "song": Blessing(
        id="song",
        loss_text="For many weeks the valley had been strangely quiet, and even the birds kept their beaks tucked shut.",
        return_text="At once the sleeping song woke in the air above the hill.",
        hill_effect="bright notes fluttered from stone to stone like birds made of sound",
        end_image="By evening every doorway hummed, and the valley rang with fiddles, birds, and laughing voices.",
        tags={"song", "magic", "valley"},
    ),
}

HELPERS = {
    "sparrow": HelperKind(
        id="sparrow",
        label="sparrow",
        phrase="a small gray sparrow",
        need="Its nest had tumbled into the path.",
        thanks='The sparrow shook out its feathers and chirped, "Kind hands earn holy echoes."',
        gift_line='It gave the child the first hallelujah, light as a seed.',
        favor="lifting the fallen nest back into the low hawthorn",
        tags={"bird", "kindness"},
    ),
    "goat": HelperKind(
        id="goat",
        label="goat",
        phrase="an old white goat",
        need="A bramble loop had caught around one of its horns.",
        thanks='The goat stamped once and said, "Kind hands untie more than thorns."',
        gift_line='From its beard came the second hallelujah, warm as milk.',
        favor="freeing the goat from the bramble",
        tags={"animal", "kindness"},
    ),
    "granny": HelperKind(
        id="granny",
        label="granny",
        phrase="an old grandmother in a blue shawl",
        need="Her bundle of sticks had spilled in the dust.",
        thanks='The grandmother smiled and said, "Kind hands carry blessings farther than feet can go."',
        gift_line='She breathed out the third hallelujah, bright as a little bell.',
        favor="gathering the spilled sticks back into the grandmother's bundle",
        tags={"elder", "kindness"},
    ),
    "fish": HelperKind(
        id="fish",
        label="fish",
        phrase="a shining river fish",
        need="It had flipped into the reeds where the water was too shallow.",
        thanks='The fish flashed silver and whispered, "Kind hands remember the way home."',
        gift_line='It splashed up the first hallelujah, cool as river spray.',
        favor="sliding the fish back into the deep water",
        tags={"river", "kindness"},
    ),
    "mole": HelperKind(
        id="mole",
        label="mole",
        phrase="a velvet mole",
        need="A little stone blocked the mouth of its tunnel.",
        thanks='The mole blinked and murmured, "Kind hands open shut places."',
        gift_line='Out of the dark came the second hallelujah, soft as earth.',
        favor="rolling the stone away from the tunnel mouth",
        tags={"earth", "kindness"},
    ),
    "miller": HelperKind(
        id="miller",
        label="miller",
        phrase="a bent old miller",
        need="A sack of grain had split and spilled across the road.",
        thanks='The miller nodded and said, "Kind hands lose nothing that love gathers."',
        gift_line='He sang out the third hallelujah, round as bread from the oven.',
        favor="helping the miller scoop the spilled grain back into the sack",
        tags={"village", "kindness"},
    ),
}

TASKS = {
    "lift": Task(
        id="lift",
        verb="lift",
        object_phrase="the trouble gently",
        success_line="The child knelt and lifted carefully until the small trouble sat right again.",
        impossible_for=set(),
        tags={"help"},
    ),
    "untie": Task(
        id="untie",
        verb="untie",
        object_phrase="the knot slowly",
        success_line="The child worked patiently with small fingers until the snag gave way.",
        impossible_for={"fish"},
        tags={"help"},
    ),
    "carry": Task(
        id="carry",
        verb="carry",
        object_phrase="the burden a little way",
        success_line="The child bent low and carried what was needed until the burden felt light again.",
        impossible_for={"sparrow", "fish", "mole"},
        tags={"help"},
    ),
    "guide": Task(
        id="guide",
        verb="guide",
        object_phrase="the lost thing home",
        success_line="The child moved with care and guided the lost thing back where it belonged.",
        impossible_for={"granny", "miller"},
        tags={"help"},
    ),
}

TOOLS = {
    "reed_flute": Tool(
        id="reed_flute",
        label="reed flute",
        phrase="a reed flute cut from the riverside",
        solves={"song", "rain", "spring"},
        magic_line="When the child breathed into the reed flute, the note did not end at the hilltop. It circled the stones three times like a golden bird.",
        tags={"flute", "magic"},
    ),
    "copper_bell": Tool(
        id="copper_bell",
        label="copper bell",
        phrase="a little copper bell on a red string",
        solves={"song", "spring"},
        magic_line="When the child rang the copper bell, the sound leaped from stone to stone until the hill itself seemed to answer.",
        tags={"bell", "magic"},
    ),
    "silver_spoon": Tool(
        id="silver_spoon",
        label="silver spoon",
        phrase="a silver spoon bright as moonlight",
        solves={"rain", "spring"},
        magic_line="When the child tapped the silver spoon on the oldest stone, the ring went deep under the ground as if the hill had swallowed it and begun to sing.",
        tags={"spoon", "magic"},
    ),
}

VALID_HELPER_SETS = {
    "path": ("sparrow", "goat", "granny"),
    "river": ("fish", "mole", "miller"),
}


def valid_combo(blessing_id: str, path_id: str, task_id: str, tool_id: str) -> bool:
    if blessing_id not in BLESSINGS or path_id not in VALID_HELPER_SETS or task_id not in TASKS or tool_id not in TOOLS:
        return False
    task = TASKS[task_id]
    if blessing_id not in TOOLS[tool_id].solves:
        return False
    for helper_id in VALID_HELPER_SETS[path_id]:
        if helper_id in task.impossible_for:
            return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for blessing_id in sorted(BLESSINGS):
        for path_id in sorted(VALID_HELPER_SETS):
            for task_id in sorted(TASKS):
                for tool_id in sorted(TOOLS):
                    if valid_combo(blessing_id, path_id, task_id, tool_id):
                        combos.append((blessing_id, path_id, task_id, tool_id))
    return combos


@dataclass
class StoryParams:
    blessing: str
    path: str
    task: str
    tool: str
    hero_name: str
    hero_gender: str
    elder_type: str
    home_place: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        blessing="spring",
        path="path",
        task="lift",
        tool="reed_flute",
        hero_name="Mara",
        hero_gender="girl",
        elder_type="grandmother",
        home_place="the little valley of pear trees",
    ),
    StoryParams(
        blessing="rain",
        path="river",
        task="guide",
        tool="silver_spoon",
        hero_name="Ivo",
        hero_gender="boy",
        elder_type="grandfather",
        home_place="the dry valley below the blue hill",
    ),
    StoryParams(
        blessing="song",
        path="path",
        task="lift",
        tool="copper_bell",
        hero_name="Anya",
        hero_gender="girl",
        elder_type="grandmother",
        home_place="the quiet valley under the old hill",
    ),
    StoryParams(
        blessing="spring",
        path="river",
        task="guide",
        tool="silver_spoon",
        hero_name="Toma",
        hero_gender="boy",
        elder_type="grandfather",
        home_place="the valley of stone bridges",
    ),
]

GIRL_NAMES = ["Mara", "Anya", "Lina", "Dara", "Vesa", "Nina", "Olya", "Zora"]
BOY_NAMES = ["Ivo", "Toma", "Milan", "Petar", "Yuri", "Stefan", "Niko", "Borin"]
HOME_PLACES = [
    "the little valley of pear trees",
    "the quiet valley under the old hill",
    "the dry valley below the blue hill",
    "the valley of stone bridges",
    "the green hollow beside the alder wood",
]
ELDERS = ["grandmother", "grandfather"]


def helper_entities(path_id: str) -> list[HelperKind]:
    return [HELPERS[h] for h in VALID_HELPER_SETS[path_id]]


def explain_rejection(blessing_id: str, path_id: str, task_id: str, tool_id: str) -> str:
    if tool_id in TOOLS and blessing_id in BLESSINGS and blessing_id not in TOOLS[tool_id].solves:
        return (
            f"(No story: the {TOOLS[tool_id].label} does not wake the blessing of {blessing_id}. "
            f"Choose a tool that fits that sleeping magic.)"
        )
    if path_id in VALID_HELPER_SETS and task_id in TASKS:
        impossible = [h for h in VALID_HELPER_SETS[path_id] if h in TASKS[task_id].impossible_for]
        if impossible:
            names = ", ".join(impossible)
            return (
                f"(No story: the task '{task_id}' cannot reasonably solve the trouble for {names} on this path. "
                f"Pick a task that works for all three meetings.)"
            )
    return "(No story: this combination does not fit the world rules.)"


def tell(params: StoryParams) -> World:
    blessing = BLESSINGS[params.blessing]
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    helpers = helper_entities(params.path)

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_type, label=params.elder_type, role="elder"))
    valley = world.add(Entity(id="valley", kind="place", type="valley", label="the valley", role="valley"))
    hill = world.add(Entity(id="hill", kind="place", type="hill", label="the hill of seven stones", role="hill"))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase, role="tool"))
    valley.meters["lack"] = 1

    world.facts["helpers_seen"] = []
    world.facts["kind_acts"] = []
    world.facts["hallelujah_lines"] = []

    world.say(
        f"In {params.home_place}, people had almost forgotten how to look up with glad faces. {blessing.loss_text}"
    )
    world.say(
        f"At the edge of the village, {params.hero_name} lived with {hero.pronoun('possessive')} {params.elder_type}, who knew the old sayings and listened to the wind."
    )
    world.say(
        f'One dusk, the {params.elder_type} said, "The hill of seven stones is sleeping. If you carry three hallelujahs there before moonrise, the valley may wake again."'
    )
    world.say(
        f"So {params.hero_name} set out with {tool.phrase} and a brave, quiet heart."
    )

    for idx, helper in enumerate(helpers, 1):
        world.para()
        world.say(f"First on the road" if idx == 1 else ("Second on the road" if idx == 2 else "Third on the road"))
        world.say(f"{params.hero_name} met {helper.phrase}. {helper.need}")
        world.say(
            f"{params.hero_name} did not hurry past. {task.success_line}"
        )
        world.say(f"In that way, {params.hero_name} helped by {helper.favor}.")
        hero.meters["kindness"] += 1
        hero.meters["hallelujahs"] += 1
        world.facts["helpers_seen"].append(helper.label)
        world.facts["kind_acts"].append(helper.favor)
        line = f"The {helper.label} gave {params.hero_name} hallelujah number {idx}."
        world.facts["hallelujah_lines"].append(line)
        world.say(helper.thanks)
        world.say(helper.gift_line)
        if idx == 1:
            world.say('So the child carried one hallelujah.')
        elif idx == 2:
            world.say('So the child carried two hallelujahs.')
        else:
            world.say('So the child carried three hallelujahs.')
        propagate(world)

    world.para()
    world.say(
        f"By moonrise {params.hero_name} climbed to the hill of seven stones, where the grass was silver and the dark seemed to be listening."
    )
    world.say(tool.magic_line)
    for idx in range(1, 4):
        hill.meters["sung"] += 1
        world.say(f'{params.hero_name} sang, "Hallelujah."')
        if idx == 1:
            world.say("The first hallelujah rose like a lamp in a window.")
        elif idx == 2:
            world.say("The second hallelujah went farther, over roof and field and brook.")
        else:
            world.say("The third hallelujah opened what had been sleeping.")
        propagate(world)

    if valley.meters["restored"] < THRESHOLD:
        raise StoryError("(World error: three hallelujahs were sung, but the blessing did not wake.)")

    world.para()
    world.say(blessing.return_text)
    world.say(f"{blessing.hill_effect}.")
    world.say(
        f"When {params.hero_name} walked home, nobody asked whether the old tale had been true any longer."
    )
    world.say(blessing.end_image)
    world.say(
        f"And from that night on, when good things returned after a hard season, the people of {params.home_place} lifted their heads and answered with hallelujahs."
    )

    world.facts.update(
        blessing=blessing,
        task=task,
        tool=tool,
        hero=hero,
        elder=elder,
        valley=valley,
        hill=hill,
        path=params.path,
        restored=valley.meters["restored"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    blessing = f["blessing"]
    tool = f["tool"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "hallelujahs" and uses magical repetition.',
        f"Tell a gentle folk tale where a child named {hero.label} must gather three hallelujahs to wake the sleeping {blessing.id} of a valley.",
        f"Write a magic story with a happy ending where three repeated songs of hallelujah, helped by {tool.label}, bring a blessing back to the land.",
    ]


def pair_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    blessing = f["blessing"]
    elder = f["elder"]
    tool = f["tool"]
    helpers = f["helpers_seen"]
    acts = f["kind_acts"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child from the valley, and {hero.pronoun('possessive')} {elder.label_word} who sends {hero.pronoun('object')} to the hill of seven stones. The tale follows how {hero.label} gathers three hallelujahs to help the whole valley.",
        ),
        (
            "What was wrong in the valley at the start?",
            f"The valley was missing its {blessing.id}. {blessing.loss_text} That is why the journey mattered.",
        ),
        (
            f"Why did {hero.label} go to the hill?",
            f"{elder.label_word.capitalize()} told {hero.label} that the sleeping hill might wake the valley if three hallelujahs were carried there before moonrise. So the trip was not just a walk; it was the only hopeful cure anyone knew.",
        ),
        (
            f"How did {hero.label} get the three hallelujahs?",
            f"{hero.label} earned them by doing three kind acts for {pair_list(helpers)}. Each helper gave one hallelujah after being helped, so kindness itself became the magic.",
        ),
        (
            f"What did {hero.label} do with the {tool.label} on the hill?",
            f"{hero.label} used the {tool.label} and then sang 'Hallelujah' three times. The repeated song is what opened the sleeping blessing after the three acts of kindness were complete.",
        ),
        (
            "How did the story end?",
            f"It ended happily because the valley's {blessing.id} came back. {blessing.end_image} That final picture proves the magic truly changed the world.",
        ),
    ]
    if acts:
        qa.append(
            (
                "What kind things did the child do on the road?",
                f"{hero.label} helped by {pair_list(acts)}. Those acts mattered because every kindness earned one hallelujah.",
            )
        )
    return qa


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a folk tale?",
            "Magic in a folk tale is a wonderful power that changes the world in a way ordinary people cannot. It often wakes when someone is brave, kind, or true."
        )
    ],
    "folk": [
        (
            "What is a folk tale?",
            "A folk tale is an old story that sounds as if people told it again and again by firelight or at bedtime. It often has simple patterns, memorable sayings, and a lesson hidden inside the adventure."
        )
    ],
    "repetition": [
        (
            "Why do folk tales repeat things three times?",
            "Folk tales often repeat things three times because the pattern is easy to hear and remember. The first time begins the magic, the second time grows it, and the third time completes it."
        )
    ],
    "hallelujah": [
        (
            "What does hallelujah mean?",
            "Hallelujah is a joyful word people say or sing when they feel praise, wonder, or glad thanks. In stories, it can sound bright and holy, like happiness rising into the air."
        )
    ],
    "kindness": [
        (
            "Why is kindness powerful in stories?",
            "Kindness is powerful in stories because small good deeds can change more than one heart at a time. Sometimes a gentle help opens the door for an even bigger blessing."
        )
    ],
    "bell": [
        (
            "What does a bell sound like in a story?",
            "A bell can sound bright, clear, and far-reaching in a story. Its ringing often feels like a call that wakes people, animals, or even sleeping magic."
        )
    ],
    "flute": [
        (
            "What does a flute do in a tale?",
            "A flute makes a singing note when someone blows into it. In a tale, that note can seem to float through the air like a bird or a ribbon."
        )
    ],
    "rain": [
        (
            "Why is rain important to a valley?",
            "Rain gives water to grass, fields, trees, and streams. When rain is missing too long, the land grows dry and tired."
        )
    ],
    "spring": [
        (
            "What is springtime?",
            "Springtime is the season when new green leaves, flowers, and fresh growth return after winter. It often stands for hope and beginning again."
        )
    ],
    "song": [
        (
            "Why does song matter to people?",
            "Song can make people feel less alone because it gives sound to joy, sadness, work, and hope. A singing place often feels alive and shared."
        )
    ],
}
KNOWLEDGE_ORDER = ["folk", "magic", "repetition", "hallelujah", "kindness", "bell", "flute", "rain", "spring", "song"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"folk", "magic", "repetition", "hallelujah", "kindness", f["blessing"].id}
    tool = f["tool"]
    if tool.id == "copper_bell":
        tags.add("bell")
    if tool.id == "reed_flute":
        tags.add("flute")
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
        parts = [f"({ent.type})"]
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.label:
            parts.append(f"label={ent.label}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} " + " ".join(parts))
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
task_possible_on_path(T, P) :-
    task(T), path(P),
    not impossible_on_path(T, P).

impossible_on_path(T, P) :-
    path_member(P, H),
    impossible(T, H).

valid(B, P, T, Tool) :-
    blessing(B), path(P), task(T), tool(Tool),
    task_possible_on_path(T, P),
    solves(Tool, B).

restored :-
    chosen_blessing(B),
    chosen_path(P),
    chosen_task(T),
    chosen_tool(Tool),
    valid(B, P, T, Tool),
    helper_count(P, 3),
    hallelujah_count(3),
    sung_count(3).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for blessing_id in sorted(BLESSINGS):
        lines.append(asp.fact("blessing", blessing_id))
    for path_id, helper_ids in sorted(VALID_HELPER_SETS.items()):
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("helper_count", path_id, len(helper_ids)))
        for helper_id in helper_ids:
            lines.append(asp.fact("path_member", path_id, helper_id))
    for task_id, task in sorted(TASKS.items()):
        lines.append(asp.fact("task", task_id))
        for helper_id in sorted(task.impossible_for):
            lines.append(asp.fact("impossible", task_id, helper_id))
    for tool_id, tool in sorted(TOOLS.items()):
        lines.append(asp.fact("tool", tool_id))
        for blessing_id in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, blessing_id))
    lines.append(asp.fact("hallelujah_count", 3))
    lines.append(asp.fact("sung_count", 3))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_restored(params: StoryParams) -> bool:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_blessing", params.blessing),
            asp.fact("chosen_path", params.path),
            asp.fact("chosen_task", params.task),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show restored/0."))
    return bool(asp.atoms(model, "restored"))


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated story was empty.)")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for params in cases:
        expected = valid_combo(params.blessing, params.path, params.task, params.tool)
        got = asp_restored(params)
        if expected != got:
            rc = 1
            print(
                f"MISMATCH restored/parity for {params.blessing}/{params.path}/{params.task}/{params.tool}: "
                f"python={expected} asp={got}"
            )
    try:
        smoke_test()
        print("OK: smoke test generated and emitted a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: three hallelujahs, kindness, and a waking blessing in a folk tale."
    )
    ap.add_argument("--blessing", choices=sorted(BLESSINGS))
    ap.add_argument("--path", choices=sorted(VALID_HELPER_SETS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-type", choices=ELDERS)
    ap.add_argument("--home-place")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.blessing and args.path and args.task and args.tool:
        if not valid_combo(args.blessing, args.path, args.task, args.tool):
            raise StoryError(explain_rejection(args.blessing, args.path, args.task, args.tool))

    combos = [
        c for c in valid_combos()
        if (args.blessing is None or c[0] == args.blessing)
        and (args.path is None or c[1] == args.path)
        and (args.task is None or c[2] == args.task)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        b = args.blessing or next(iter(BLESSINGS))
        p = args.path or next(iter(VALID_HELPER_SETS))
        t = args.task or next(iter(TASKS))
        tool = args.tool or next(iter(TOOLS))
        raise StoryError(explain_rejection(b, p, t, tool))

    blessing_id, path_id, task_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(ELDERS)
    home_place = args.home_place or rng.choice(HOME_PLACES)
    return StoryParams(
        blessing=blessing_id,
        path=path_id,
        task=task_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        home_place=home_place,
    )


def generate(params: StoryParams) -> StorySample:
    if params.blessing not in BLESSINGS:
        raise StoryError(f"(Invalid blessing: {params.blessing})")
    if params.path not in VALID_HELPER_SETS:
        raise StoryError(f"(Invalid path: {params.path})")
    if params.task not in TASKS:
        raise StoryError(f"(Invalid task: {params.task})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if not valid_combo(params.blessing, params.path, params.task, params.tool):
        raise StoryError(explain_rejection(params.blessing, params.path, params.task, params.tool))

    world = tell(params)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (blessing, path, task, tool) combos:\n")
        for blessing_id, path_id, task_id, tool_id in combos:
            print(f"  {blessing_id:8} {path_id:6} {task_id:6} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.hero_name}: {p.blessing} by way of {p.path} ({p.task}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
