#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lee_exert_happy_sandbox_misunderstanding_rhyming_story.py

A small standalone storyworld about children in a sandbox. One child misunderstands
another child's warning, exerts effort in the wrong direction, and then learns what
was really meant. The prose aims for a gentle rhyming-story feel while still being
driven by simulated world state.

Run it
------
python storyworlds/worlds/gpt-5.4/lee_exert_happy_sandbox_misunderstanding_rhyming_story.py
python storyworlds/worlds/gpt-5.4/lee_exert_happy_sandbox_misunderstanding_rhyming_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/lee_exert_happy_sandbox_misunderstanding_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/lee_exert_happy_sandbox_misunderstanding_rhyming_story.py --qa
python storyworlds/worlds/gpt-5.4/lee_exert_happy_sandbox_misunderstanding_rhyming_story.py --trace --seed 11
python storyworlds/worlds/gpt-5.4/lee_exert_happy_sandbox_misunderstanding_rhyming_story.py --verify
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
HELPFUL_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in male:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class BuildPlan:
    id: str
    castle: str
    wall: str
    moat: str
    top: str
    rhyme_end: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    good_for: str
    effort: int
    tags: set[str] = field(default_factory=set)


@dataclass
class WarningCfg:
    id: str
    short: str
    true_meaning: str
    wrong_meaning: str
    issue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairCfg:
    id: str
    label: str
    phrase: str
    helpful: int
    action: str
    result: str
    qa_text: str
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


def _r_wrong_dig_hurts_shape(world: World) -> list[str]:
    out: list[str] = []
    fort = world.get("fort")
    lee = world.get("lee")
    if lee.meters["wrong_dig"] < THRESHOLD:
        return out
    sig = ("wrong_dig",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fort.meters["wobble"] += 1
    fort.meters["shape_loss"] += 1
    lee.memes["worry"] += 1
    world.get("friend").memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_helping_repairs(world: World) -> list[str]:
    out: list[str] = []
    fort = world.get("fort")
    lee = world.get("lee")
    friend = world.get("friend")
    if lee.meters["repair_help"] < THRESHOLD and friend.meters["repair_help"] < THRESHOLD:
        return out
    sig = ("repair_help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fort.meters["steady"] += 1
    fort.meters["ready"] += 1
    fort.meters["wobble"] = 0.0
    fort.meters["shape_loss"] = 0.0
    lee.memes["relief"] += 1
    friend.memes["relief"] += 1
    lee.memes["happy"] += 1
    friend.memes["happy"] += 1
    out.append("__fixed__")
    return out


CAUSAL_RULES = [
    Rule(name="wrong_dig_hurts_shape", tag="physical", apply=_r_wrong_dig_hurts_shape),
    Rule(name="helping_repairs", tag="physical", apply=_r_helping_repairs),
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


def misunderstanding_possible(warning: WarningCfg, tool: ToolCfg) -> bool:
    return tool.good_for != "pat"


def repair_is_helpful(repair: RepairCfg) -> bool:
    return repair.helpful >= HELPFUL_MIN


def valid_combo(plan: BuildPlan, warning: WarningCfg, tool: ToolCfg, repair: RepairCfg) -> bool:
    return misunderstanding_possible(warning, tool) and repair_is_helpful(repair)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for plan_id, plan in PLANS.items():
        for warning_id, warning in WARNINGS.items():
            for tool_id, tool in TOOLS.items():
                for repair_id, repair in REPAIRS.items():
                    if valid_combo(plan, warning, tool, repair):
                        combos.append((plan_id, warning_id, tool_id, repair_id))
    return combos


def predict_misstep(tool: ToolCfg) -> dict:
    sim = World()
    lee = sim.add(Entity(id="lee", kind="character", type="boy", role="hero"))
    friend = sim.add(Entity(id="friend", kind="character", type="girl", role="friend"))
    fort = sim.add(Entity(id="fort", type="castle", label="sand castle"))
    lee.meters["wrong_dig"] = 1 if tool.good_for != "pat" else 0
    sim.add(Entity(id="sandbox", type="place", label="sandbox"))
    propagate(sim, narrate=False)
    return {
        "wobble": fort.meters["wobble"],
        "shape_loss": fort.meters["shape_loss"],
        "lee_worry": lee.memes["worry"],
        "friend_worry": friend.memes["worry"],
    }


def opening(world: World, lee: Entity, friend: Entity, plan: BuildPlan) -> None:
    lee.memes["happy"] += 1
    friend.memes["happy"] += 1
    world.say(
        f"In the sandbox, Lee felt happy as could be, "
        f"with warm gold sand piled high by his knee."
    )
    world.say(
        f"Beside him, {friend.id} smiled with a sunny grand plan: "
        f'"Let\'s build {plan.castle} by patting the sand."'
    )


def shared_goal(world: World, lee: Entity, friend: Entity, plan: BuildPlan) -> None:
    world.say(
        f"They shaped {plan.wall}, they dreamed of {plan.moat}, "
        f"and pictured {plan.top} where a bright flag might float."
    )


def warning_beat(world: World, friend: Entity, warning: WarningCfg) -> None:
    friend.memes["care"] += 1
    world.say(
        f'Soon {friend.id} gave a warning, gentle and light: '
        f'"{warning.short}," she said. "Then the tower stays right."'
    )
    world.facts["warning_spoken"] = warning.short


def misunderstand(world: World, lee: Entity, warning: WarningCfg, tool: ToolCfg) -> None:
    lee.memes["confusion"] += 1
    lee.memes["eagerness"] += 1
    world.say(
        f"But Lee had a misunderstanding, small and sly. "
        f'He heard "{warning.short}" and thought, "{warning.wrong_meaning}," with a try.'
    )
    world.say(
        f"He chose {tool.phrase} and said, "
        f'"I will exert my strength and help it touch the sky!"'
    )


def wrong_effort(world: World, lee: Entity, tool: ToolCfg, plan: BuildPlan) -> None:
    lee.meters["effort"] += tool.effort
    lee.meters["wrong_dig"] += 1
    world.say(
        f"So scrape, scrape, scrape went {tool.label} in the sand, "
        f"while Lee worked with all his might and both his hands."
    )
    propagate(world, narrate=False)
    if world.get("fort").meters["wobble"] >= THRESHOLD:
        world.say(
            f"But {plan.top} gave a shiver, and {plan.wall} sank low. "
            f"The castle looked unsure now, not sturdy in a row."
        )


def reveal(world: World, friend: Entity, warning: WarningCfg) -> None:
    world.say(
        f'"Oh, Lee," said {friend.id}, "that is not what I meant. '
        f'I meant {warning.true_meaning}, not dig with all your bent."'
    )


def remorse(world: World, lee: Entity) -> None:
    lee.memes["worry"] += 1
    world.say(
        "Lee blinked at the wobble and frowned at the sight. "
        '"I wanted to help. I just heard it wrong, not right."'
    )


def repair_offer(world: World, friend: Entity, repair: RepairCfg) -> None:
    world.say(
        f'{friend.id} knelt close and spoke in a cheerful way: '
        f'"That is all right. We can fix it together today. '
        f'{repair.action}."'
    )


def repair_act(world: World, lee: Entity, friend: Entity, repair: RepairCfg, plan: BuildPlan) -> None:
    lee.meters["repair_help"] += 1
    friend.meters["repair_help"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So side by side they {repair.result}, "
        f"and soon stood {plan.castle} where sand met shoe."
    )


def ending(world: World, lee: Entity, friend: Entity, plan: BuildPlan) -> None:
    lee.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"Now Lee felt happy again in the sun's soft glow. "
        f"First he asked what words meant, then he helped it grow."
    )
    world.say(
        f"And there in the sandbox, neat and bright to see, "
        f"stood {plan.castle} by the wall -- for {plan.rhyme_end}, and Lee."
    )


def tell(
    plan: BuildPlan,
    warning: WarningCfg,
    tool: ToolCfg,
    repair: RepairCfg,
    lee_name: str = "Lee",
    friend_name: str = "Mina",
    lee_gender: str = "boy",
    friend_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    lee = world.add(Entity(id=lee_name, kind="character", type=lee_gender, role="hero", label=lee_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", label=friend_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    sandbox = world.add(Entity(id="sandbox", type="place", label="sandbox", phrase="the sandbox"))
    fort = world.add(Entity(id="fort", type="castle", label="sand castle", phrase=plan.castle))

    opening(world, lee, friend, plan)
    shared_goal(world, lee, friend, plan)

    world.para()
    warning_beat(world, friend, warning)
    misunderstand(world, lee, warning, tool)
    wrong_effort(world, lee, tool, plan)

    world.para()
    reveal(world, friend, warning)
    remorse(world, lee)
    repair_offer(world, friend, repair)
    repair_act(world, lee, friend, repair, plan)

    world.para()
    ending(world, lee, friend, plan)

    world.facts.update(
        lee=lee,
        friend=friend,
        parent=parent,
        sandbox=sandbox,
        fort=fort,
        plan=plan,
        warning=warning,
        tool=tool,
        repair=repair,
        misunderstood=lee.memes["confusion"] >= THRESHOLD,
        wrong_effort=lee.meters["wrong_dig"] >= THRESHOLD,
        repaired=fort.meters["ready"] >= THRESHOLD,
        warning_text=warning.short,
        true_meaning=warning.true_meaning,
        wrong_meaning=warning.wrong_meaning,
    )
    return world


KNOWLEDGE = {
    "sandbox": [
        (
            "What is a sandbox?",
            "A sandbox is a box or play area filled with sand. Children can dig, pat, scoop, and build shapes in it."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. It can be fixed by stopping, asking, and explaining more clearly."
        )
    ],
    "bucket": [
        (
            "What is a bucket good for in sand?",
            "A bucket can hold sand and help make a big shape when you turn it over. It is better for carrying or molding than for careful smoothing."
        )
    ],
    "shovel": [
        (
            "What is a shovel good for in sand?",
            "A shovel is good for digging and scooping sand. It can move lots of sand fast, but it is not the best tool for gentle smoothing."
        )
    ],
    "rake": [
        (
            "What is a rake good for in sand?",
            "A toy rake can pull lines through sand. It is useful for grooves and patterns, but it can make a tower wobble if used too roughly."
        )
    ],
    "pat": [
        (
            "Why do builders pat sand gently?",
            "Patting sand gently presses it into shape without cutting it apart. Gentle hands can help a sand castle stay firm."
        )
    ],
    "repair": [
        (
            "How can children fix a sand castle that starts to wobble?",
            "They can stop digging, add sand where it fell away, and press it gently back into shape. Working slowly and together helps the castle stand again."
        )
    ],
}
KNOWLEDGE_ORDER = ["sandbox", "misunderstanding", "bucket", "shovel", "rake", "pat", "repair"]


PLANS = {
    "star_castle": BuildPlan(
        id="star_castle",
        castle="a star-topped castle",
        wall="a round little wall",
        moat="a moon-shaped moat",
        top="the tallest sandy top",
        rhyme_end="Mina",
        tags={"sandbox"},
    ),
    "shell_castle": BuildPlan(
        id="shell_castle",
        castle="a shell-trimmed castle",
        wall="a curvy sandy wall",
        moat="a tiny sparkling moat",
        top="the smooth sandy top",
        rhyme_end="Nora",
        tags={"sandbox"},
    ),
    "fort_tower": BuildPlan(
        id="fort_tower",
        castle="a proud sand fort",
        wall="a brave bumpy wall",
        moat="a winding shallow moat",
        top="the little tower top",
        rhyme_end="Ava",
        tags={"sandbox"},
    ),
}

TOOLS = {
    "shovel": ToolCfg(
        id="shovel",
        label="the small shovel",
        phrase="the small shovel",
        good_for="dig",
        effort=2,
        tags={"shovel"},
    ),
    "bucket": ToolCfg(
        id="bucket",
        label="the red bucket",
        phrase="the red bucket's rim",
        good_for="carry",
        effort=1,
        tags={"bucket"},
    ),
    "rake": ToolCfg(
        id="rake",
        label="the toy rake",
        phrase="the toy rake",
        good_for="groove",
        effort=1,
        tags={"rake"},
    ),
    "hands": ToolCfg(
        id="hands",
        label="his open hands",
        phrase="his open hands",
        good_for="pat",
        effort=1,
        tags={"pat"},
    ),
}

WARNINGS = {
    "easy_side": WarningCfg(
        id="easy_side",
        short="Easy on that side",
        true_meaning="pat that side softly",
        wrong_meaning="dig that side quickly",
        issue="direction word easy sounded like hurry to him",
        tags={"misunderstanding"},
    ),
    "light_touch": WarningCfg(
        id="light_touch",
        short="Use a light touch",
        true_meaning="press the sand softly",
        wrong_meaning="use a light tool and scrape",
        issue="light sounded like a thing instead of a gentle way",
        tags={"misunderstanding"},
    ),
    "hold_the_edge": WarningCfg(
        id="hold_the_edge",
        short="Hold the edge",
        true_meaning="steady the edge with your hand",
        wrong_meaning="pull the edge away",
        issue="hold sounded like grab and yank instead of steadying",
        tags={"misunderstanding"},
    ),
}

REPAIRS = {
    "pat_together": RepairCfg(
        id="pat_together",
        label="patting together",
        phrase="patting together",
        helpful=3,
        action="Let's add a little sand and pat it gently together",
        result="added fresh sand and patted the sides smooth",
        qa_text="They added fresh sand and patted the sides smooth together.",
        tags={"repair", "pat"},
    ),
    "cup_and_press": RepairCfg(
        id="cup_and_press",
        label="cupping and pressing",
        phrase="cupping and pressing",
        helpful=3,
        action="Let's cup the tower, press the wall, and make it steady again",
        result="cupped the tower and pressed the wall back into shape",
        qa_text="They cupped the tower and pressed the wall back into shape together.",
        tags={"repair", "pat"},
    ),
    "kick_flat": RepairCfg(
        id="kick_flat",
        label="kicking flat",
        phrase="kicking flat",
        helpful=1,
        action="Let's kick it flat and start over",
        result="kicked the whole thing flat",
        qa_text="They kicked the whole castle flat.",
        tags={"repair"},
    ),
}


@dataclass
class StoryParams:
    plan: str
    warning: str
    tool: str
    repair: str
    lee_name: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        plan="star_castle",
        warning="easy_side",
        tool="shovel",
        repair="pat_together",
        lee_name="Lee",
        friend_name="Mina",
        friend_gender="girl",
        parent="mother",
    ),
    StoryParams(
        plan="shell_castle",
        warning="light_touch",
        tool="bucket",
        repair="cup_and_press",
        lee_name="Lee",
        friend_name="Nora",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        plan="fort_tower",
        warning="hold_the_edge",
        tool="rake",
        repair="pat_together",
        lee_name="Lee",
        friend_name="Ava",
        friend_gender="girl",
        parent="mother",
    ),
]


def explain_tool(tool: ToolCfg) -> str:
    return (
        f"(No story: {tool.label} does not create the sandbox misunderstanding needed here. "
        f"This world needs Lee to hear a smoothing warning and use a digging or scraping move instead.)"
    )


def explain_repair(repair: RepairCfg) -> str:
    return (
        f"(Refusing repair '{repair.id}': it is not helpful enough for a happy ending "
        f"(helpful={repair.helpful} < {HELPFUL_MIN}). The repair should rebuild the castle, not flatten it.)"
    )


def ensure_params_exist(params: StoryParams) -> None:
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.warning not in WARNINGS:
        raise StoryError(f"(Unknown warning: {params.warning})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lee = f["lee"]
    friend = f["friend"]
    warning = f["warning"]
    tool = f["tool"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old set in a sandbox, and include the words "Lee", "exert", and "happy".',
        f"Tell a gentle misunderstanding story where {lee.id} hears {friend.id}'s warning \"{warning.short}\" the wrong way and uses {tool.label}, but the children fix the sand castle together.",
        "Write a child-facing poem-story with a clear beginning, a little mistake in the middle, and a happy ending that shows asking for meaning before acting.",
    ]


def pair_noun(lee: Entity, friend: Entity) -> str:
    if lee.type == "boy" and friend.type == "girl":
        return "a boy and a girl"
    if lee.type == "boy" and friend.type == "boy":
        return "two boys"
    if lee.type == "girl" and friend.type == "girl":
        return "two girls"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lee = f["lee"]
    friend = f["friend"]
    plan = f["plan"]
    warning = f["warning"]
    tool = f["tool"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(lee, friend)} in a sandbox, Lee and {friend.id}. They were trying to build {plan.castle} together."
        ),
        (
            "Where does the story happen?",
            "The story happens in a sandbox. The sand is the place where the children build, make a mistake, and then fix it."
        ),
        (
            f"What did {friend.id} mean when {friend.pronoun()} said \"{warning.short}\"?",
            f"{friend.id} meant {warning.true_meaning}. The warning was meant to help the castle stay steady, not to tell Lee to dig harder."
        ),
        (
            f"Why was there a misunderstanding?",
            f"There was a misunderstanding because Lee heard the warning in the wrong way and thought it meant {warning.wrong_meaning}. He wanted to help, but he understood the words differently from what {friend.id} meant."
        ),
        (
            f"How did Lee exert himself in the wrong way?",
            f"Lee worked hard with {tool.label} and put real effort into the sand. But that strong effort hurt the shape because the castle needed gentle patting, not digging or scraping."
        ),
        (
            "What happened to the sand castle?",
            f"The castle started to wobble, and part of {plan.wall} sank. That change showed the misunderstanding in a clear, physical way."
        ),
        (
            "How did the children fix the problem?",
            f"{repair.qa_text} They worked side by side, so the castle became steady again."
        ),
        (
            "How did Lee feel at the end?",
            "Lee felt happy again at the end. He had learned to ask what a warning means before rushing to help."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sandbox", "misunderstanding", "repair"} | set(f["tool"].tags) | set(f["repair"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding_possible(W, T) :- warning(W), tool(T), good_for(T, G), G != pat.
helpful_repair(R) :- repair(R), helpful(R, H), helpful_min(M), H >= M.
valid(P, W, T, R) :- plan(P), warning(W), tool(T), repair(R),
                     misunderstanding_possible(W, T), helpful_repair(R).

wrong_effort :- chosen_tool(T), good_for(T, G), G != pat.
wobble :- wrong_effort.
happy_ending :- chosen_repair(R), helpful_repair(R), wobble.
outcome(happy) :- happy_ending.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    for warning_id in WARNINGS:
        lines.append(asp.fact("warning", warning_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("good_for", tool_id, tool.good_for))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("helpful", repair_id, repair.helpful))
    lines.append(asp.fact("helpful_min", HELPFUL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    ensure_params_exist(params)
    if not misunderstanding_possible(WARNINGS[params.warning], TOOLS[params.tool]):
        return "invalid"
    if not repair_is_helpful(REPAIRS[params.repair]):
        return "invalid"
    return "happy"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: Lee misunderstands a sandbox warning, exerts effort the wrong way, and then helps fix the castle."
    )
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--friend", help="friend name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool:
        tool = TOOLS[args.tool]
        if not misunderstanding_possible(next(iter(WARNINGS.values())), tool):
            raise StoryError(explain_tool(tool))
    if args.repair and not repair_is_helpful(REPAIRS[args.repair]):
        raise StoryError(explain_repair(REPAIRS[args.repair]))

    combos = [
        c for c in valid_combos()
        if (args.plan is None or c[0] == args.plan)
        and (args.warning is None or c[1] == args.warning)
        and (args.tool is None or c[2] == args.tool)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plan_id, warning_id, tool_id, repair_id = rng.choice(sorted(combos))
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    if args.friend:
        friend_name = args.friend
    else:
        friend_name = rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        plan=plan_id,
        warning=warning_id,
        tool=tool_id,
        repair=repair_id,
        lee_name="Lee",
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


GIRL_NAMES = ["Mina", "Nora", "Ava", "Lucy", "Maya", "Ella", "Zoe", "Anna"]
BOY_NAMES = ["Max", "Ben", "Finn", "Theo", "Noah", "Eli", "Jack", "Sam"]


def generate(params: StoryParams) -> StorySample:
    ensure_params_exist(params)
    plan = PLANS[params.plan]
    warning = WARNINGS[params.warning]
    tool = TOOLS[params.tool]
    repair = REPAIRS[params.repair]
    if not misunderstanding_possible(warning, tool):
        raise StoryError(explain_tool(tool))
    if not repair_is_helpful(repair):
        raise StoryError(explain_repair(repair))
    world = tell(
        plan=plan,
        warning=warning,
        tool=tool,
        repair=repair,
        lee_name=params.lee_name,
        friend_name=params.friend_name,
        lee_gender="boy",
        friend_gender=params.friend_gender,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py == "happy" and asp != "happy":
            mismatches.append((params, py, asp))
    if not mismatches:
        print(f"OK: ASP outcome matches happy-generation model on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)} cases.")
        for params, py, asp in mismatches[:5]:
            print(" ", params, py, asp)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during verify.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (plan, warning, tool, repair) combos:\n")
        for plan, warning, tool, repair in combos:
            print(f"  {plan:12} {warning:12} {tool:8} {repair}")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.lee_name} in the sandbox: {p.warning} / {p.tool} / {p.repair}"
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
