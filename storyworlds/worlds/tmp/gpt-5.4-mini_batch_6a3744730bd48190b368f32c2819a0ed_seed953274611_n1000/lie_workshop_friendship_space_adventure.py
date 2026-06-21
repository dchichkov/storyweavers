#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lie_workshop_friendship_space_adventure.py
==========================================================================

A small standalone story world about friendship in a workshop, with a space
adventure feel and a lie that causes trouble before the friends tell the truth
and repair things together.

The world is built around a simple TinyStories-style premise:
two friends are making a pretend rocket in a workshop, one tells a lie to avoid
getting blamed, the lie creates a safety problem, and friendship helps them
confess, fix the problem, and finish the rocket in a better way.

It follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven prose
- story-grounded and world-knowledge QA
- Python reasonableness gate plus inline ASP twin
- support for --verify, --asp, --show-asp, --qa, --json, --trace, --all, -n, --seed
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
        return self.label or self.type


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    goal: str
    workshop: str
    send_off: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    warning: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    can_spill: bool = False
    can_scatter: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    tool: str
    problem: str
    fix: str
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    adult: str
    seed: Optional[int] = None
    lie_kind: str = "deny"  # deny | hide | blame


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["spill"] < THRESHOLD and e.meters["scatter"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["messy"] += 1
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["alarm"] += 1
        out.append("__mess__")
    return out


def _r_lie_burden(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character" or e.memes["lie"] < THRESHOLD:
            continue
        sig = ("burden", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"{e.id} felt a little heavier inside.")
    return out


CAUSAL_RULES = [
    Rule("mess", "physical", _r_mess),
    Rule("lie_burden", "social", _r_lie_burden),
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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combo(theme: str, tool: str, problem: str, fix: str) -> bool:
    th = THEMES[theme]
    tl = TOOLS[tool]
    pr = PROBLEMS[problem]
    fx = FIXES[fix]
    return tl.risky and pr.can_spill and fx.sense >= SENSE_MIN and th.id == "workshop"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for theme in THEMES:
        for tool in TOOLS:
            for problem in PROBLEMS:
                for fix in FIXES:
                    if valid_combo(theme, tool, problem, fix):
                        combos.append((theme, tool, problem, fix))
    return combos


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    sim.get(problem_id).meters["spill"] += 1
    propagate(sim, narrate=False)
    return {"messy": sim.get("floor").meters["messy"] >= THRESHOLD}


def setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In a bright workshop, {a.id} and {b.id} turned old boxes and tape "
        f"into {theme.scene}. {theme.rig}"
    )
    world.say(f"They wanted to reach {theme.goal}, and the whole room felt like a tiny starship hangar.")


def need_repair(world: World, b: Entity, problem: Problem) -> None:
    world.say(
        f"But the {problem.label} on the workbench made the ship tricky to finish. "
        f"{b.id} pointed at it and said they should clean it first."
    )


def lie(world: World, a: Entity, b: Entity, tool: Tool, kind: str) -> None:
    a.memes["lie"] += 1
    if kind == "deny":
        world.say(f'"I did not touch the {tool.label}," {a.id} said, even though {a.pronoun("possessive")} hands were dusty.')
    elif kind == "hide":
        world.say(f'{a.id} smiled too fast. "{tool.use},'" 
                  f" {a.pronoun()} said, trying to hide the {tool.label} behind a crate.")
    else:
        world.say(f'"It was {b.id}," {a.id} said, pointing at {b.id} and not meeting {b.pronoun()} eyes.')
    world.say("For a moment, the workshop went quiet like deep space.")


def warn(world: World, b: Entity, a: Entity, problem: Problem) -> None:
    pred = predict(world, "problem")
    b.memes["care"] += 1
    if pred["messy"]:
        world.say(
            f'{b.id} frowned. "That will make a real mess," {b.pronoun()} said. '
            f'"We should tell the grown-up and fix it together."'
        )
    else:
        world.say(f'{b.id} looked worried anyway, because little spills can travel fast on a floor.')


def confess(world: World, a: Entity, b: Entity, adult: Entity) -> None:
    a.memes["truth"] += 1
    a.memes["lie"] = 0.0
    world.say(
        f'{a.id} took a breath and said, "I lied. I bumped the {world.facts["tool"].label}." '
        f'{b.id} nodded right away, and {a.id} felt the air get lighter.'
    )
    world.say(f'Together they called {adult.label_word} from the doorway of the workshop.')


def clean_and_fix(world: World, adult: Entity, fix: Fix, problem: Problem) -> None:
    if fix.power < 1:
        world.say(f"{adult.label_word.capitalize()} tried to help, but the problem kept spreading.")
        return
    world.get("problem").meters["spill"] = 0.0
    world.get("floor").meters["messy"] = 0.0
    adult.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over and {fix.text.replace('{problem}', problem.label)}."
    )
    world.say("The spilled bits stopped sliding around, and the workbench was safe again.")


def ending(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"After that, the two friends worked side by side. "
        f"{a.id} held the tape while {b.id} lined up the last piece of the rocket."
    )
    world.say(
        f"At the end, their little space ship stood straight and shiny on the bench, "
        f"ready for {theme.send_off}."
    )


THEMES = {
    "workshop": Theme(
        id="workshop",
        scene="a cardboard rocket with silver paper wings",
        rig="A stool became a launch ladder, a paint tray became a control panel, and a flashlight became the ship's beacon.",
        goal="the moon map on the back wall",
        workshop="the workshop",
        send_off="its first trip to the moon",
    ),
    "garage": Theme(
        id="garage",
        scene="a tin rocket with painted fins",
        rig="A toolbox became a console, a coil of rope became a tether, and a lantern glowed like a star.",
        goal="the big red planet poster",
        workshop="the garage",
        send_off="its practice launch",
    ),
}

TOOLS = {
    "glue": Tool(
        id="glue",
        label="glue tube",
        phrase="a glue tube",
        use="I was only using glue",
        warning="glue can stick things fast",
        risky=True,
        tags={"tool", "repair"},
    ),
    "paint": Tool(
        id="paint",
        label="paint brush",
        phrase="a paint brush",
        use="I was only painting",
        warning="paint can smear everywhere",
        risky=True,
        tags={"tool", "repair"},
    ),
    "screwdriver": Tool(
        id="screwdriver",
        label="screwdriver",
        phrase="a screwdriver",
        use="I was only fixing the panel",
        warning="a screwdriver can make a dangerous scratch",
        risky=True,
        tags={"tool", "repair"},
    ),
}

PROBLEMS = {
    "spilled_glue": Problem(
        id="problem",
        label="spilled glue",
        phrase="a sticky spill of glue",
        can_spill=True,
        can_scatter=False,
        tags={"spill", "glue"},
    ),
    "paint_drop": Problem(
        id="problem",
        label="paint drop",
        phrase="a bright drop of paint",
        can_spill=True,
        can_scatter=False,
        tags={"spill", "paint"},
    ),
    "tiny_screws": Problem(
        id="problem",
        label="tiny screws",
        phrase="a handful of tiny screws",
        can_spill=False,
        can_scatter=True,
        tags={"scatter", "metal"},
    ),
}

FIXES = {
    "wipe": Fix(
        id="wipe",
        sense=3,
        power=3,
        text="wiped the {problem} away with a cloth",
        fail="wiped at the {problem}, but it was already too sticky",
        qa_text="wiped the {problem} away with a cloth",
        tags={"clean"},
    ),
    "tray": Fix(
        id="tray",
        sense=3,
        power=3,
        text="put the {problem} in a tray and carried it to the sink",
        fail="tried to move the {problem}, but it slipped off the tray",
        qa_text="put the {problem} in a tray and carried it to the sink",
        tags={"clean"},
    ),
    "magnet": Fix(
        id="magnet",
        sense=1,
        power=1,
        text="used a magnet on the {problem}",
        fail="used a magnet, but the {problem} did not move",
        qa_text="used a magnet on the {problem}",
        tags={"weak"},
    ),
}

NAMES_GIRL = ["Lia", "Mira", "Nova", "Tia", "Zoe", "Ava"]
NAMES_BOY = ["Sol", "Kai", "Leo", "Max", "Eli", "Jett"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story set in a workshop where friends make a rocket, include the word "lie".',
        f"Tell a friendship story in a workshop where {f['a'].id} tells a lie about {f['tool'].label}, then tells the truth and fixes the problem.",
        f"Write a child-friendly space story with a workshop, a small lie, and friends working together to finish their rocket.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, adult, tool, problem, fix, theme = f["a"], f["b"], f["adult"], f["tool"], f["problem_cfg"], f["fix"], f["theme"]
    items = [
        QAItem(
            question="Who were the story friends?",
            answer=f"The story was about {a.id} and {b.id}, two friends working together in the workshop. They were building a pretend rocket and trying to make it ready for the stars.",
        ),
        QAItem(
            question="Why did the workshop get tense?",
            answer=f"{a.id} told a lie about {tool.label} instead of admitting what happened. That made {b.id} worried, because the {problem.label} could turn into a bigger mess.",
        ),
        QAItem(
            question="What changed things in the end?",
            answer=f"{a.id} told the truth, and {b.id} stayed kind instead of turning away. Then {adult.label_word} helped them use {fix.id} so the workshop could be cleaned and the rocket could be finished.",
        ),
    ]
    if f.get("resolved"):
        items.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the friends back at work, side by side, and the rocket standing ready for {theme.send_off}. The lie was over, and friendship made the room feel calm again.",
            )
        )
    return items


WORLD_KNOWLEDGE = {
    "lie": [(
        "What is a lie?",
        "A lie is when someone says something that is not true. It can make other people feel confused or hurt, so telling the truth is usually better.",
    )],
    "workshop": [(
        "What is a workshop?",
        "A workshop is a room where people build, fix, or make things. It often has tools, tables, and small parts scattered around.",
    )],
    "friendship": [(
        "What does friendship mean?",
        "Friendship means caring about each other, helping each other, and being kind when something goes wrong.",
    )],
    "rocket": [(
        "What is a rocket?",
        "A rocket is a vehicle that can shoot up into space. People use rockets to travel beyond Earth.",
    )],
    "space": [(
        "Why do people wear special gear in space stories?",
        "Space is dangerous and has no air, so stories about space often use special gear like helmets and suits to keep people safe.",
    )],
    "tool": [(
        "Why should tools be used carefully?",
        "Tools can help build things, but they can also cause accidents if someone is careless. That is why grown-ups and careful kids handle them slowly.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["tool"].tags) | set(world.facts["problem_cfg"].tags) | {"workshop", "friendship", "lie", "rocket", "space"}
    out: list[QAItem] = []
    for key in ["lie", "workshop", "friendship", "rocket", "space", "tool"]:
        if key in tags and key in WORLD_KNOWLEDGE:
            for q, a in WORLD_KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(theme: Theme, tool: Tool, problem: Problem, fix: Fix,
         a_name: str, a_gender: str, b_name: str, b_gender: str, adult_name: str,
         lie_kind: str = "deny") -> World:
    w = World()
    a = w.add(Entity(id=a_name, kind="character", type=a_gender, role="friend"))
    b = w.add(Entity(id=b_name, kind="character", type=b_gender, role="friend"))
    adult = w.add(Entity(id=adult_name, kind="character", type="adult", label="the captain"))
    floor = w.add(Entity(id="floor", type="floor", label="the floor"))
    tool_ent = w.add(Entity(id="tool", type="tool", label=tool.label))
    prob = w.add(Entity(id="problem", type="problem", label=problem.label))
    w.facts.update(a=a, b=b, adult=adult, tool=tool_ent, problem_cfg=problem, fix=fix, theme=theme)

    setup(w, a, b, theme)
    w.para()
    need_repair(w, b, problem)
    lie(w, a, b, tool, lie_kind)
    warn(w, b, a, problem)

    prob.meters["spill"] += 1
    if tool.risky:
        tool_ent.meters["scattered"] += 1
    propagate(w, narrate=True)

    w.para()
    confess(w, a, b, adult)
    clean_and_fix(w, adult, fix, problem)
    ending(w, a, b, theme)

    w.facts["resolved"] = True
    return w


def valid_names(gender: str) -> list[str]:
    return NAMES_GIRL if gender == "girl" else NAMES_BOY


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(f"(Refusing fix '{args.fix}': it is too weak to be a sensible repair.)")
    theme = args.theme or rng.choice(list(THEMES))
    tool = args.tool or rng.choice(list(TOOLS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice([f.id for f in sensible_fixes()])
    if not valid_combo(theme, tool, problem, fix):
        raise StoryError("(No valid combination matches the given options.)")
    h1_gender = args.hero1_gender or rng.choice(["girl", "boy"])
    h2_gender = args.hero2_gender or ("boy" if h1_gender == "girl" else "girl")
    hero1 = args.hero1 or rng.choice(valid_names(h1_gender))
    hero2_pool = [n for n in valid_names(h2_gender) if n != hero1]
    hero2 = args.hero2 or rng.choice(hero2_pool)
    adult = args.adult or rng.choice(["Captain", "Engineer", "Pilot"])
    return StoryParams(theme=theme, tool=tool, problem=problem, fix=fix,
                       hero1=hero1, hero1_gender=h1_gender,
                       hero2=hero2, hero2_gender=h2_gender,
                       adult=adult, lie_kind=args.lie_kind)


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        tool = TOOLS[params.tool]
        problem = PROBLEMS[params.problem]
        fix = FIXES[params.fix]
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc.args[0]}") from exc
    if fix.sense < SENSE_MIN:
        raise StoryError(f"(Refusing fix '{fix.id}': it is too weak to be sensible.)")
    world = tell(theme, tool, problem, fix, params.hero1, params.hero1_gender,
                 params.hero2, params.hero2_gender, params.adult, params.lie_kind)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


ASP_RULES = r"""
risky_tool(T) :- tool(T), risky(T).
messy_problem(P) :- problem(P), can_spill(P).
valid_combo(Th,T,P,F) :- theme(Th), workshop_theme(Th), risky_tool(T), messy_problem(P), fix(F), sense(F,S), sense_min(M), S >= M.
lie_burden(A) :- tells_lie(A).
truth_heals(A) :- confesses(A).
outcome(resolved) :- truth_heals(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
        lines.append(asp.fact("workshop_theme", tid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.risky:
            lines.append(asp.fact("risky", tid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.can_spill:
            lines.append(asp.fact("can_spill", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, tool=None, problem=None, fix=None,
                                                             hero1=None, hero1_gender=None, hero2=None,
                                                             hero2_gender=None, adult=None, lie_kind="deny"),
                                         random.Random(777)))
        if not sample.story:
            raise RuntimeError("empty story")
        _ = sample.story
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: friendship, a lie, and a workshop space adventure.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero1")
    ap.add_argument("--hero1-gender", choices=["girl", "boy"], dest="hero1_gender")
    ap.add_argument("--hero2")
    ap.add_argument("--hero2-gender", choices=["girl", "boy"], dest="hero2_gender")
    ap.add_argument("--adult")
    ap.add_argument("--lie-kind", choices=["deny", "hide", "blame"], default="deny")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(theme="workshop", tool="glue", problem="spilled_glue", fix="wipe",
                hero1="Nova", hero1_gender="girl", hero2="Kai", hero2_gender="boy",
                adult="Captain", lie_kind="deny"),
    StoryParams(theme="workshop", tool="paint", problem="paint_drop", fix="tray",
                hero1="Lia", hero1_gender="girl", hero2="Sol", hero2_gender="boy",
                adult="Engineer", lie_kind="hide"),
    StoryParams(theme="workshop", tool="screwdriver", problem="spilled_glue", fix="wipe",
                hero1="Mira", hero1_gender="girl", hero2="Eli", hero2_gender="boy",
                adult="Pilot", lie_kind="blame"),
]


def resolve_valid_combo(rng: random.Random) -> tuple[str, str, str, str]:
    return rng.choice(valid_combos())


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_combo/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
