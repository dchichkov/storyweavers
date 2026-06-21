#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whinny_happy_ending_problem_solving_pirate_tale.py
=============================================================================

A standalone storyworld for a tiny pirate-flavored problem-solving tale.

Two children turn an ordinary place into a pirate adventure. A real obstacle
blocks their way to the "treasure." Their pony gives a sharp whinny that helps
them notice the right tool, and together they solve the problem safely. Every
generated sample ends happily, but only for combinations that make practical
sense.

Run it
------
    python storyworlds/worlds/gpt-5.4/whinny_happy_ending_problem_solving_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/whinny_happy_ending_problem_solving_pirate_tale.py --setting cove --obstacle gap
    python storyworlds/worlds/gpt-5.4/whinny_happy_ending_problem_solving_pirate_tale.py --tool rope
    python storyworlds/worlds/gpt-5.4/whinny_happy_ending_problem_solving_pirate_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/whinny_happy_ending_problem_solving_pirate_tale.py --verify
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
        pony = {"pony"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in pony:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    water: str
    treasure_spot: str
    rig: str
    adult_place: str
    tool_hints: dict[str, str] = field(default_factory=dict)
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    problem_line: str
    danger_line: str
    solved_meter: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    action_text: str
    result_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    pony_name: str
    adult: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_blocked_worry(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["blocked"] < THRESHOLD:
        return []
    if ("worry", obstacle.id) in world.fired:
        return []
    world.fired.add(("worry", obstacle.id))
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__worry__"]


def _r_clue_hope(world: World) -> list[str]:
    tool = world.get("tool")
    if tool.meters["noticed"] < THRESHOLD:
        return []
    if ("hope", tool.id) in world.fired:
        return []
    world.fired.add(("hope", tool.id))
    for kid in world.kids():
        kid.memes["hope"] += 1
    return ["__hope__"]


def _r_solution_relief(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["solved"] < THRESHOLD:
        return []
    if ("relief", obstacle.id) in world.fired:
        return []
    world.fired.add(("relief", obstacle.id))
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="blocked_worry", tag="emotion", apply=_r_blocked_worry),
    Rule(name="clue_hope", tag="emotion", apply=_r_clue_hope),
    Rule(name="solution_relief", tag="emotion", apply=_r_solution_relief),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def supports(setting: Setting, obstacle: Obstacle) -> bool:
    return obstacle.id in setting.affords


def tool_fits(tool: ToolCfg, obstacle: Obstacle) -> bool:
    return tool.id in obstacle.needs


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for oid, obstacle in OBSTACLES.items():
            if not supports(setting, obstacle):
                continue
            for tid, tool in TOOLS.items():
                if tool_fits(tool, obstacle):
                    combos.append((sid, oid, tid))
    return combos


def explain_rejection(setting: Setting, obstacle: Obstacle, tool: ToolCfg) -> str:
    if not supports(setting, obstacle):
        return (
            f"(No story: {obstacle.label} does not fit {setting.place}. "
            f"Pick an obstacle that belongs in that setting.)"
        )
    return (
        f"(No story: {tool.label} would not solve {obstacle.label}. "
        f"This world only tells practical problem-solving stories.)"
    )


def predict_solution(world: World, tool_id: str) -> bool:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    tool = sim.get(tool_id)
    if tool.attrs.get("fits_obstacle"):
        obstacle.meters["solved"] += 1
        obstacle.meters["blocked"] = 0.0
        propagate(sim, narrate=False)
    return obstacle.meters["solved"] >= THRESHOLD


def introduce(world: World, captain: Entity, mate: Entity, pony: Entity, adult: Entity) -> None:
    world.say(
        f"On a bright day, {captain.id} and {mate.id} turned {world.setting.place} into a pirate harbor. "
        f"{world.setting.rig}"
    )
    world.say(
        f'Their pony, {pony.id}, wore a rope halter and trotted beside them like the gentlest deck mate. '
        f'{adult.label_word.capitalize()} worked nearby at {world.setting.adult_place}.'
    )


def set_goal(world: World, captain: Entity, mate: Entity, pony: Entity) -> None:
    world.say(
        f'"Captain {captain.id}!" cried {mate.id}. "If we follow {world.setting.water}, '
        f'we can reach {world.setting.treasure_spot} before sunset."'
    )
    world.say(
        f'{captain.id} bowed to {pony.id}. "Come on, First Mate Pony. We are hunting treasure."'
    )


def reveal_problem(world: World, captain: Entity, mate: Entity, obstacle: Obstacle) -> None:
    obstacle.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.problem_line)
    world.say(
        f'{captain.id} stopped short. "{obstacle.danger_line}"'
    )
    if any(kid.memes["worry"] >= THRESHOLD for kid in world.kids()):
        world.say(
            f"For a moment, the game felt wobbly, and both children looked at the trouble instead of the treasure."
        )


def whinny_clue(world: World, pony: Entity, tool: Entity, obstacle: Obstacle) -> None:
    tool.meters["noticed"] += 1
    propagate(world, narrate=False)
    hint = world.setting.tool_hints[obstacle.id]
    world.say(
        f"Then {pony.id} tossed {pony.pronoun('possessive')} head and let out a loud whinny. "
        f"The whinny rang over {world.setting.water} and made the children turn."
    )
    world.say(
        f"Right where {pony.pronoun()} was looking, they saw {tool.phrase} {hint}."
    )


def plan(world: World, captain: Entity, mate: Entity, tool: Entity, obstacle: Obstacle) -> None:
    good = predict_solution(world, "tool")
    if not good:
        raise StoryError("The chosen tool does not actually solve the problem.")
    world.say(
        f'{mate.id} knelt down and thought hard. "We do not need bigger pirates," {mate.pronoun()} said. '
        f'"We need a better plan."'
    )
    world.say(
        f'{captain.id} touched {tool.phrase} and grinned. "This can help with the {obstacle.label}."'
    )


def solve(world: World, captain: Entity, mate: Entity, pony: Entity, tool: Entity, obstacle: Obstacle) -> None:
    obstacle.meters["solved"] += 1
    obstacle.meters["blocked"] = 0.0
    tool.meters["used"] += 1
    tool.meters[obstacle.solved_meter] += 1
    world.facts["solved_by"] = tool.label
    propagate(world, narrate=False)
    world.say(tool.attrs["action_text"])
    world.say(tool.attrs["result_text"])
    world.say(
        f'{pony.id} gave a softer little snort and stepped after them, as if {pony.pronoun()} approved the plan.'
    )


def ending(world: World, captain: Entity, mate: Entity, pony: Entity, adult: Entity) -> None:
    world.say(
        f"Soon the three mates reached {world.setting.treasure_spot}. Inside the treasure box were shiny shells, a red apple, and two oat biscuits for {pony.id}."
    )
    world.say(
        f'{adult.label_word.capitalize()} looked over from {world.setting.adult_place} and smiled. '
        f'"You solved that like careful sailors," {adult.pronoun()} called.'
    )
    world.say(
        f'{captain.id} shared the apple with {mate.id}, and {mate.id} fed the biscuits to {pony.id}. '
        f'With the sun warm on their backs and the path open at last, the little pirates felt brave, clever, and very glad they had stopped to think.'
    )


def tell(
    setting: Setting,
    obstacle_cfg: Obstacle,
    tool_cfg: ToolCfg,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    pony_name: str,
    adult_type: str,
) -> World:
    world = World(setting=setting)
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    pony = world.add(Entity(id=pony_name, kind="character", type="pony", role="pony", label="the pony"))
    adult = world.add(Entity(id="Parent", kind="character", type=adult_type, role="adult", label="the grown-up"))
    obstacle = world.add(Entity(id="obstacle", type="obstacle", label=obstacle_cfg.label, phrase=obstacle_cfg.phrase))
    tool = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            attrs={
                "fits_obstacle": tool_fits(tool_cfg, obstacle_cfg),
                "action_text": tool_cfg.action_text,
                "result_text": tool_cfg.result_text,
            },
        )
    )

    introduce(world, captain, mate, pony, adult)
    set_goal(world, captain, mate, pony)

    world.para()
    reveal_problem(world, captain, mate, obstacle_cfg)
    whinny_clue(world, pony, tool, obstacle_cfg)
    plan(world, captain, mate, tool, obstacle_cfg)

    world.para()
    solve(world, captain, mate, pony, tool, obstacle_cfg)
    ending(world, captain, mate, pony, adult)

    world.facts.update(
        captain=captain,
        mate=mate,
        pony=pony,
        adult=adult,
        obstacle_cfg=obstacle_cfg,
        obstacle=obstacle,
        tool_cfg=tool_cfg,
        tool=tool,
        setting=setting,
        solved=obstacle.meters["solved"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="a little cove behind the dunes",
        water="the glittering tide line",
        treasure_spot="the shell cave",
        rig="A driftwood bench was their ship, a striped towel was their sail, and a biscuit tin was their treasure chest.",
        adult_place="the picnic blanket",
        tool_hints={
            "gap": "beside a stack of nets",
            "stuck_cart": "near the old crab baskets",
            "closed_gate": "hanging from a post by the path",
        },
        affords={"gap", "closed_gate"},
        tags={"beach", "pirate"},
    ),
    "farm": Setting(
        id="farm",
        place="the lane by the hay barn",
        water="the narrow rain ditch",
        treasure_spot="the shade behind the hay bales",
        rig="An upturned crate was their ship, a broom was their mast, and a blue bucket held the pirate gold.",
        adult_place="the barn door",
        tool_hints={
            "gap": "under the fence rail",
            "stuck_cart": "coiled on a peg by the barn",
            "closed_gate": "on a hook beside the latch",
        },
        affords={"gap", "stuck_cart", "closed_gate"},
        tags={"farm", "pirate"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the meadow path by the creek",
        water="the silver creek",
        treasure_spot="the willow shade on the far bank",
        rig="A handcart was their ship, a scarf was their flag, and a small wooden box held the treasure map.",
        adult_place="the garden bench",
        tool_hints={
            "gap": "under the willow tree",
            "stuck_cart": "looped over the bench arm",
            "closed_gate": "tucked in a flowerpot by the gate",
        },
        affords={"gap", "stuck_cart"},
        tags={"meadow", "pirate"},
    ),
}

OBSTACLES = {
    "gap": Obstacle(
        id="gap",
        label="gap in the path",
        phrase="a long wooden plank",
        problem_line="But a strip of water had chewed a gap across the path, so the treasure trail stopped at the edge.",
        danger_line="That jump is too wide for pirate boots. We might slip into the muddy water.",
        solved_meter="bridged",
        needs={"plank"},
        tags={"bridge", "water", "safety"},
    ),
    "stuck_cart": Obstacle(
        id="stuck_cart",
        label="stuck cart wheel",
        phrase="a coil of rope",
        problem_line="Just then the little treasure cart sank with a squelch, and one wheel stuck deep in the mud.",
        danger_line="If we yank with our hands, the cart may tip and spill everything.",
        solved_meter="pulled_free",
        needs={"rope"},
        tags={"cart", "mud", "teamwork"},
    ),
    "closed_gate": Obstacle(
        id="closed_gate",
        label="latched gate",
        phrase="a brass gate key",
        problem_line="At the end of the path stood a short wooden gate, and its latch was tied shut so the children could not squeeze through.",
        danger_line="Climbing over would be a bad pirate trick. We should open it the proper way.",
        solved_meter="unlatched",
        needs={"key"},
        tags={"gate", "safety"},
    ),
}

TOOLS = {
    "plank": ToolCfg(
        id="plank",
        label="plank",
        phrase="a long wooden plank",
        action_text="Working together, they lifted the plank and laid it across the wet gap.",
        result_text="It made a sturdy little bridge, and the children crossed one careful step at a time.",
        tags={"plank", "bridge", "problem_solving"},
    ),
    "rope": ToolCfg(
        id="rope",
        label="rope",
        phrase="a coil of rope",
        action_text="They tied the rope around the cart, and the children leaned back while the pony stepped forward slowly.",
        result_text="With one firm pull, the wheel came free from the mud, and the cart rolled again.",
        tags={"rope", "teamwork", "problem_solving"},
    ),
    "key": ToolCfg(
        id="key",
        label="key",
        phrase="a brass gate key",
        action_text="Mate and captain fitted the key into the latch and turned it together.",
        result_text="The knot loosened, the latch clicked open, and the little gate swung wide.",
        tags={"key", "gate", "problem_solving"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
PONY_NAMES = ["Comet", "Pebble", "Star", "Maple", "Sunny"]


KNOWLEDGE = {
    "pony": [
        (
            "What is a whinny?",
            "A whinny is a horse or pony sound. It can be loud and sharp, so it helps people notice that the animal wants attention."
        )
    ],
    "bridge": [
        (
            "Why is a bridge helpful?",
            "A bridge lets you cross over water or a gap without stepping into it. A sturdy bridge makes crossing safer and easier."
        )
    ],
    "rope": [
        (
            "What can a rope do?",
            "A rope can help pull, tie, or hold things. When people use it carefully together, it can move something heavy."
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key turns inside a lock or latch so it can open the right way. Using the right key is safer than forcing something."
        )
    ],
    "safety": [
        (
            "Why is stopping to think a good idea?",
            "Stopping to think helps you notice danger before someone gets hurt. A calm plan is often better than a fast guess."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job together. Sharing the work often makes a hard problem easier."
        )
    ],
}

KNOWLEDGE_ORDER = ["pony", "safety", "bridge", "rope", "key", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    return [
        'Write a pirate-style story for a 3-to-5-year-old that includes the word "whinny" and ends happily.',
        f"Tell a gentle pirate adventure where {captain.id} and {mate.id} face a {obstacle.label} and solve it by thinking carefully.",
        f"Write a story where a pony's whinny helps children notice {tool.phrase}, and the right tool fixes the problem."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    pony = f["pony"]
    adult = f["adult"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {captain.id} and {mate.id}, who pretended to be pirates, and their pony {pony.id}. A grown-up watched nearby while the children worked the problem out."
        ),
        (
            "What problem stopped the pirates?",
            f"Their adventure was blocked by a {obstacle.label}. That meant they could not reach {setting.treasure_spot} the easy way."
        ),
        (
            f"Why did {captain.id} and {mate.id} not rush ahead?",
            f"They saw that the trouble could be unsafe if they hurried. The children paused because they wanted a proper plan instead of a risky pirate trick."
        ),
        (
            f"What did {pony.id} do?",
            f"{pony.id} gave a loud whinny and looked toward {tool.phrase}. The whinny helped the children notice the useful thing they had missed."
        ),
        (
            "How did they solve the problem?",
            f"They used {tool.phrase} to deal with the {obstacle.label}. It worked because it was the right tool for that exact problem."
        ),
        (
            "How did the story end?",
            f"The children reached {setting.treasure_spot} and shared their treasure snack with {pony.id}. The ending feels happy because the path was open, the problem was solved, and everyone stayed safe."
        ),
        (
            f"What did the grown-up think at the end?",
            f"{adult.label_word.capitalize()} was pleased that the children solved the trouble carefully. The praise matters because it shows clever thinking was part of the adventure."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pony", "safety"}
    obstacle = world.facts["obstacle_cfg"]
    tool = world.facts["tool_cfg"]
    tags |= set(obstacle.tags)
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
    for e in world.entities.values():
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="farm",
        obstacle="stuck_cart",
        tool="rope",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        pony_name="Comet",
        adult="mother",
    ),
    StoryParams(
        setting="cove",
        obstacle="gap",
        tool="plank",
        captain_name="Mia",
        captain_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        pony_name="Star",
        adult="father",
    ),
    StoryParams(
        setting="farm",
        obstacle="closed_gate",
        tool="key",
        captain_name="Sam",
        captain_gender="boy",
        mate_name="Ella",
        mate_gender="girl",
        pony_name="Maple",
        adult="mother",
    ),
    StoryParams(
        setting="meadow",
        obstacle="gap",
        tool="plank",
        captain_name="Nora",
        captain_gender="girl",
        mate_name="Theo",
        mate_gender="boy",
        pony_name="Sunny",
        adult="father",
    ),
]


ASP_RULES = r"""
valid(S,O,T) :- setting(S), obstacle(O), tool(T), supports(S,O), solves(T,O).
outcome(solved) :- chosen_setting(S), chosen_obstacle(O), chosen_tool(T), valid(S,O,T).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for tid in sorted(obstacle.needs):
            lines.append(asp.fact("solves", tid, oid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid, setting in SETTINGS.items():
        for oid in sorted(setting.affords):
            lines.append(asp.fact("supports", sid, oid))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "invalid"


def outcome_of(params: StoryParams) -> str:
    if (
        params.setting in SETTINGS
        and params.obstacle in OBSTACLES
        and params.tool in TOOLS
        and supports(SETTINGS[params.setting], OBSTACLES[params.obstacle])
        and tool_fits(TOOLS[params.tool], OBSTACLES[params.obstacle])
    ):
        return "solved"
    return "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for i in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(i))
        except StoryError:
            continue
        params.seed = i
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-style problem-solving stories with a pony's whinny and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.tool:
        setting = SETTINGS[args.setting]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not (supports(setting, obstacle) and tool_fits(tool, obstacle)):
            raise StoryError(explain_rejection(setting, obstacle, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        if args.setting and args.obstacle and args.tool:
            raise StoryError(
                explain_rejection(SETTINGS[args.setting], OBSTACLES[args.obstacle], TOOLS[args.tool])
            )
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    captain_name, captain_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=captain_name)
    pony_name = rng.choice(PONY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        tool=tool_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        pony_name=pony_name,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not (supports(setting, obstacle) and tool_fits(tool, obstacle)):
        raise StoryError(explain_rejection(setting, obstacle, tool))

    world = tell(
        setting=setting,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        pony_name=params.pony_name,
        adult_type=params.adult,
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
        print(f"{len(combos)} compatible (setting, obstacle, tool) combos:\n")
        for setting, obstacle, tool in combos:
            print(f"  {setting:8} {obstacle:12} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.setting}: {p.obstacle} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
