#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/brontosaurus_magic_adventure.py
==============================================================

A standalone storyworld for a tiny adventure tale with a brontosaurus and a bit
of magic. The world follows a child and a brontosaurus on a small quest: they
hear about a lost magic star, cross a windy path, face a problem, use a clever
magical tool, and end with a vivid change in the world.

The script is deliberately self-contained and uses only the standard library,
plus the shared ``storyworlds/results.py`` and optional lazy ASP helpers from
``storyworlds/asp.py``.
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
BRAVERY_INIT = 5.0
MAGIC_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    size: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    path: str
    feature: str = "adventure"
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    glow: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    danger: str
    severity: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["shimmering"] < THRESHOLD:
            continue
        sig = ("magic", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "trail" in world.entities:
            world.get("trail").meters["glow"] += 1
        out.append(f"A soft magic glow spread along the path.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["trapped"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if ent.role in {"child", "brontosaurus"}:
                ent.memes["worry"] += 1
        out.append(f"The adventure felt stuck for a moment.")
    return out


CAUSAL_RULES = [Rule("magic", _r_magic), Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_at_hand(problem: Problem, setting: Setting) -> bool:
    return problem.id in setting.tags or problem.severity >= 2


def sensible_help() -> list[HelpAction]:
    return [h for h in HELP.values() if h.sense >= MAGIC_MIN]


def can_fix(help_action: HelpAction, problem: Problem) -> bool:
    return help_action.power >= problem.severity


def predict_problem(world: World, problem_id: str) -> dict:
    sim = world.copy()
    sim.get(problem_id).meters["trapped"] += 1
    propagate(sim, narrate=False)
    return {
        "trapped": sim.get(problem_id).meters["trapped"] >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.entities.values()),
    }


def intro(world: World, child: Entity, dino: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    dino.memes["wonder"] += 1
    world.say(
        f"On a bright morning, {child.id} and a friendly brontosaurus named {dino.id} "
        f"stood at the edge of {setting.place}. The {setting.sky} sky shimmered over "
        f"{setting.path}."
    )


def call_to_adventure(world: World, child: Entity, dino: Entity, problem: Problem) -> None:
    world.say(
        f"Then they heard about {problem.phrase}. '{problem.label}!' said {child.id}. "
        f"{dino.id} lowered {dino.pronoun('possessive')} long neck and listened."
    )


def grab_tool(world: World, child: Entity, tool: MagicTool) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} found {tool.phrase}. It {tool.glow}, warm as a tiny sunrise."
    )


def approach(world: World, child: Entity, dino: Entity, problem: Problem) -> None:
    dino.meters["stomping"] += 1
    world.say(
        f"Together they followed the path until {problem.danger} blocked the way."
    )


def warn(world: World, child: Entity, dino: Entity, problem: Problem) -> bool:
    pred = predict_problem(world, "problem")
    if not pred["trapped"]:
        return False
    child.memes["care"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{child.id} bit {child.pronoun('possessive')} lip. "
        f'"That looks tricky," {child.id} said. "We need a clever way through."'
    )
    return True


def attempt(world: World, child: Entity, tool: MagicTool, problem: Problem) -> None:
    world.say(
        f"{child.id} raised {child.pronoun('possessive')} hand and let the magic out. "
        f"{tool.glow} {problem.label}."
    )
    world.get("problem").meters["shimmering"] += 1
    propagate(world, narrate=True)


def solve(world: World, help_action: HelpAction, problem: Problem, child: Entity, dino: Entity) -> bool:
    if not can_fix(help_action, problem):
        return False
    problem.meters["trapped"] = 0.0
    child.memes["joy"] += 1
    dino.memes["joy"] += 1
    body = help_action.text.replace("{problem}", problem.label)
    world.say(f"In a flash, they {body}.")
    world.say(
        f"The way opened, and {child.id} and {dino.id} stepped forward together."
    )
    return True


def fail_help(world: World, help_action: HelpAction, problem: Problem, child: Entity, dino: Entity) -> None:
    body = help_action.fail.replace("{problem}", problem.label)
    world.say(f"They tried, but {body}.")
    world.say(
        f"{dino.id} stayed brave, and {child.id} held on tight while the path stayed blocked."
    )


def ending(world: World, child: Entity, dino: Entity, setting: Setting, tool: MagicTool, problem: Problem) -> None:
    world.say(
        f"At last, the {setting.place} looked different: the path was clear, the "
        f"magic glow was soft, and the brontosaurus's shadow stretched long and safe."
    )


def tell(
    setting: Setting,
    problem: Problem,
    tool: MagicTool,
    help_action: HelpAction,
    child_name: str = "Mina",
    child_gender: str = "girl",
    dino_name: str = "Bruno",
    dino_size: str = "huge",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    dino = world.add(Entity(id=dino_name, kind="character", type="brontosaurus", role="brontosaurus", size=dino_size, tags={"brontosaurus"}))
    world.add(Entity(id="problem", kind="thing", type="problem", label=problem.label, role="problem", tags=set(problem.tags)))
    world.add(Entity(id="trail", kind="thing", type="trail", label="the trail"))

    intro(world, child, dino, setting)
    call_to_adventure(world, child, dino, problem)
    world.para()
    grab_tool(world, child, tool)
    approach(world, child, dino, problem)
    warn(world, child, dino, problem)
    world.para()
    attempt(world, child, tool, problem)
    if solve(world, help_action, problem, child, dino):
        world.para()
        ending(world, child, dino, setting, tool, problem)
    else:
        fail_help(world, help_action, problem, child, dino)
        world.para()
        ending(world, child, dino, setting, tool, problem)

    world.facts.update(
        child=child,
        dino=dino,
        problem=problem,
        tool=tool,
        help_action=help_action,
        setting=setting,
        outcome="solved" if problem.meters["trapped"] < THRESHOLD else "stuck",
        warned=bool(world.facts.get("predicted_worry", 0)),
    )
    return world


SETTINGS = {
    "meadow": Setting(id="meadow", place="a sunlit meadow", sky="golden", path="a winding path", tags={"adventure"}),
    "cave": Setting(id="cave", place="a mossy cave", sky="dim", path="a stone tunnel", tags={"adventure"}),
    "ruins": Setting(id="ruins", place="ancient ruins", sky="violet", path="broken steps", tags={"adventure"}),
}

PROBLEMS = {
    "gate": Problem(id="gate", label="a sleepy gate", phrase="a sleepy gate that would not open", danger="a sleepy gate", severity=2, tags={"gate"}),
    "fog": Problem(id="fog", label="a magic fog", phrase="a magic fog that hid the path", danger="thick fog", severity=3, tags={"fog"}),
    "boulder": Problem(id="boulder", label="a giant boulder", phrase="a giant boulder blocking the trail", danger="a giant boulder", severity=4, tags={"boulder"}),
}

TOOLS = {
    "sparkle_map": MagicTool(id="sparkle_map", label="sparkle map", phrase="a sparkle map", glow="glowed with silver lines", power=2, tags={"magic"}),
    "moon_key": MagicTool(id="moon_key", label="moon key", phrase="a moon key", glow="shone like a little moon", power=3, tags={"magic"}),
    "rainbow_wand": MagicTool(id="rainbow_wand", label="rainbow wand", phrase="a rainbow wand", glow="sprinkled rainbow sparks", power=4, tags={"magic"}),
}

HELP = {
    "whisper": HelpAction(id="whisper", sense=3, power=2, text="whispered to the {problem}, and it slid aside", fail="whispered, but the {problem} stayed put", qa_text="whispered to the {problem}, and it slid aside", tags={"magic"}),
    "twirl": HelpAction(id="twirl", sense=3, power=3, text="twirled the magic tool, and the {problem} rolled away", fail="twirled the magic tool, but the {problem} would not budge", qa_text="twirled the magic tool, and the {problem} rolled away", tags={"magic"}),
    "shine": HelpAction(id="shine", sense=2, power=4, text="shined a bright spell on the {problem}, and it melted into dust", fail="shined a bright spell, but the {problem} still stood there", qa_text="shined a bright spell on the {problem}, and it melted into dust", tags={"magic"}),
}

@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    help_action: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    dino_name: str = "Bruno"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(setting="meadow", problem="gate", tool="sparkle_map", help_action="whisper", child_name="Mina", child_gender="girl", dino_name="Bruno"),
    StoryParams(setting="cave", problem="fog", tool="moon_key", help_action="twirl", child_name="Eli", child_gender="boy", dino_name="Bram"),
    StoryParams(setting="ruins", problem="boulder", tool="rainbow_wand", help_action="shine", child_name="Tia", child_gender="girl", dino_name="Bongo"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if not risk_at_hand(problem, setting):
                continue
            for tid in TOOLS:
                out.append((sid, pid, tid))
    return out


KNOWLEDGE = {
    "brontosaurus": [("What is a brontosaurus?", "A brontosaurus is a very big dinosaur with a long neck and a gentle way of moving.")],
    "magic": [("What is magic in stories?", "Magic in stories is a special kind of pretend power that can make unusual things happen.")],
    "adventure": [("What is an adventure?", "An adventure is an exciting journey to a new place with a problem to solve.")],
    "gate": [("What is a gate?", "A gate is a door in a fence or wall that can open and close.")],
    "fog": [("What is fog?", "Fog is a thick cloud near the ground that makes it hard to see.")],
    "boulder": [("What is a boulder?", "A boulder is a very big rock.")],
}

KNOWLEDGE_ORDER = ["brontosaurus", "magic", "adventure", "gate", "fog", "boulder"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story that includes a brontosaurus named {f['dino'].id} and a child named {f['child'].id}.",
        f"Tell a magical adventure where {f['child'].id} and a brontosaurus solve a problem with a magic tool.",
        f"Write a child-friendly story with the word brontosaurus, a magical helper, and a clear ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, dino, problem, tool = f["child"], f["dino"], f["problem"], f["tool"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and a brontosaurus named {dino.id}. They go on a small adventure together."),
        ("What problem did they face?", f"They faced {problem.phrase}. That problem blocked the way and made the journey feel stuck for a moment."),
        ("What magic tool did they use?", f"They used {tool.phrase}. It helped them try a clever magical answer instead of giving up."),
    ]
    if f.get("warned"):
        qa.append((
            "Why did the child pause before trying the magic?",
            f"{child.id} could see that the problem might trap the path. That warning helped them choose a careful way to use the magic."
        ))
    if f["outcome"] == "solved":
        qa.append((
            "How did the story end?",
            f"It ended with the path opening and the adventure moving forward. {child.id} and {dino.id} could walk on together in the bright magic glow."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The path stayed blocked, but {child.id} and {dino.id} stayed together and kept going bravely. The ending still shows them facing the adventure side by side."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["tool"].tags) | {"brontosaurus", "magic", "adventure"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, help_action: HelpAction) -> str:
    return f"(No story: {help_action.id} does not have enough power to solve {problem.label}, so the adventure would not reach a proper turn.)"


def explain_combo() -> str:
    return "(No story: this combination does not fit the adventure's small magical quest.)"


def outcome_of(params: StoryParams) -> str:
    if params.help_action not in HELP:
        return "?"
    problem = PROBLEMS[params.problem]
    action = HELP[params.help_action]
    return "solved" if can_fix(action, problem) else "stuck"


ASP_RULES = r"""
valid(S, P, T) :- setting(S), problem(P), tool(T).
solved(P, H) :- problem(P), help_action(H), power(H, Pw), severity(P, Sv), Pw >= Sv.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, p.severity))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
    for hid, h in HELP.items():
        lines.append(asp.fact("help_action", hid))
        lines.append(asp.fact("power", hid, h.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo sets:")
        print(" only in ASP:", sorted(a - b))
        print(" only in Python:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a brontosaurus, magic, and an adventure quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--help-action", choices=HELP)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--dino-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    help_action = args.help_action or rng.choice(sorted(HELP))
    if help_action not in HELP:
        raise StoryError(explain_combo())
    if not can_fix(HELP[help_action], PROBLEMS[problem]):
        raise StoryError(explain_rejection(PROBLEMS[problem], HELP[help_action]))
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        help_action=help_action,
        child_name=args.child_name or rng.choice(["Mina", "Eli", "Tia", "Bo"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        dino_name=args.dino_name or rng.choice(["Bruno", "Bram", "Bongo", "Bixi"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.help_action not in HELP:
        raise StoryError("(Invalid StoryParams: unknown setting, problem, tool, or help action.)")
    if not can_fix(HELP[params.help_action], PROBLEMS[params.problem]):
        raise StoryError(explain_rejection(PROBLEMS[params.problem], HELP[params.help_action]))
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], HELP[params.help_action], params.child_name, params.child_gender, params.dino_name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, tool) combos:\n")
        for s, p, t in combos:
            print(f"  {s:8} {p:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.child_name} and {p.dino_name}: {p.problem} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
