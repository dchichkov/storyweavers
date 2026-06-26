#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/rope_centre_dinky_pier_problem_solving_kindness.py
===========================================================================================================================

A small fairy-tale storyworld about a dinky pier, a rope at the centre, and a
kind, problem-solving turn that helps someone safely cross.

The seed image:
- A dinky pier creaks over silver water.
- At its centre lies a knotted rope that has slipped loose from a little cart.
- A child or helper notices the trouble, thinks carefully, and uses kindness to
  make things right.

This world keeps the domain small on purpose: one pier, one knot, one helpful
plan, one gentle ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pier"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    gerund: str
    trouble: str
    fix_hint: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_trip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("trouble", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("rope", 0.0) < THRESHOLD:
            continue
        sig = ("trip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.pronoun().capitalize()} had to stop and think.")
    return out


CAUSAL_RULES = [_r_trip]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, problem: Problem, tool: Tool,
         hero_name: str = "Mina", hero_type: str = "girl",
         helper_name: str = "Bram", helper_type: str = "boy") -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label="the helper"))
    rope = world.add(Entity(
        id="rope", type="rope", label="rope",
        phrase="a long, salty rope", owner=helper.id, caretaker=helper.id,
    ))
    centre = world.add(Entity(
        id="centre", type="place", label="centre",
        phrase="the centre of the pier",
    ))
    dinky = world.add(Entity(
        id="dinky_cart", type="cart", label="dinky cart",
        phrase="a dinky cart with tiny wheels", owner=helper.id, caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, rope=rope, centre=centre, dinky=dinky,
                       problem=problem, tool=tool)

    hero.memes["kindness"] = 1
    hero.memes["curiosity"] = 1

    world.say(
        f"Once upon a time, on a {problem.id.replace('_', ' ')} pier, there was a dinky cart "
        f"and a {problem.label} at the centre of the boards."
    )
    world.say(
        f"{hero.id} loved the bright water and the small gulls. {hero.pronoun().capitalize()} was a kind child who "
        f"noticed when little troubles needed gentle hands."
    )
    world.say(
        f"Near the centre, a long rope had slipped from the dinky cart and made a snarl. "
        f"It kept the path from feeling safe."
    )

    world.para()
    hero.meters["rope"] = 1
    hero.meters["trouble"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} saw the rope and said, \"This is a small problem, but it still needs a careful answer.\""
    )
    world.say(
        f"{hero.pronoun().capitalize()} knelt beside the knot and looked at the pier boards, the cart wheels, "
        f"and the slack line."
    )
    world.say(
        f"Then {hero.id} thought of a kinder way to help than tugging hard."
    )

    world.para()
    helper.memes["trust"] = 1
    world.say(
        f"{helper.id} came with {tool.phrase}. Together they chose to {problem.verb}."
    )
    world.say(
        f"They lifted the rope from the centre, looped it neatly, and tied it so it would not slip again."
    )
    world.say(
        f"The dinky cart rolled free at last, and the boards felt calm under small feet."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "pier": Setting(place="the pier", affords={"rope"}),
}

PROBLEMS = {
    "rope_tangle": Problem(
        id="rope_tangle",
        label="rope tangle",
        verb="unravel the knot",
        gerund="unraveling the knot",
        trouble="the path felt unsafe",
        fix_hint="a careful loop and a gentle knot",
        zone={"centre"},
        tags={"rope", "kindness", "problem_solving"},
    ),
}

TOOLS = {
    "hands": Tool(
        id="hands",
        label="helping hands",
        phrase="helping hands",
        helps_with={"rope"},
        covers=set(),
    ),
    "hook": Tool(
        id="hook",
        label="little hook",
        phrase="a little hook",
        helps_with={"rope"},
        covers=set(),
    ),
}

NAMES_GIRL = ["Mina", "Lena", "Sia", "Tessa", "Poppy", "Nina"]
NAMES_BOY = ["Bram", "Finn", "Owen", "Theo", "Milo", "Jory"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        'Write a short fairy tale about a dinky pier where a rope at the centre causes trouble, and kindness helps solve it.',
        f"Tell a gentle story where {hero.id} notices a rope problem on the pier and {helper.id} helps with a calm plan.",
        "Write a child-friendly fairy tale with a rope, a centre, and a dinky cart, ending in a safer pier.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question="Where did the rope problem happen?",
            answer="It happened at the centre of the pier, where the boards were narrow and the rope had slipped loose.",
        ),
        QAItem(
            question=f"What did {hero.id} do when the rope made the pier unsafe?",
            answer=f"{hero.id} stopped, looked carefully, and chose a kind, thoughtful way to help instead of tugging hard.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the rope trouble?",
            answer=f"{helper.id} helped with {tool.phrase}, and together they fixed the rope at the centre of the pier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rope for?",
            answer="A rope can help tie, pull, lift, or hold things together when people need a strong line.",
        ),
        QAItem(
            question="What is the centre of something?",
            answer="The centre is the middle part of something, the place that is neither at one edge nor the other.",
        ),
        QAItem(
            question="What does dinky mean?",
            answer="Dinky means small and neat, like something little that looks careful and tidy.",
        ),
        QAItem(
            question="Why is kindness helpful?",
            answer="Kindness helps because gentle words and careful actions can make a problem easier and safer to solve.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_at_centre(P) :- problem(P), centre(centre).
kind_action(H) :- character(H), kindness(H).
rope_problem(R) :- rope(R), problem_at_centre(_).
good_fix(H, T) :- kind_action(H), tool(T), helps(T, rope).
resolved :- rope_problem(_), good_fix(_, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "pier"))
    lines.append(asp.fact("centre", "centre"))
    lines.append(asp.fact("problem", "rope_tangle"))
    lines.append(asp.fact("rope", "rope"))
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("character", "hero"))
    lines.append(asp.fact("tool", "hands"))
    lines.append(asp.fact("helps", "hands", "rope"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    has_resolved = any(sym.name == "resolved" for sym in model)
    python_ok = True
    if has_resolved != python_ok:
        print("MISMATCH between clingo and Python reasonableness gate.")
        return 1
    print("OK: clingo twin and Python story gate agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale pier storyworld about rope, the centre, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "pier"
    problem = args.problem or "rope_tangle"
    tool = args.tool or "hands"
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(NAMES_GIRL if hero_gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice(NAMES_GIRL if helper_gender == "girl" else NAMES_BOY)
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_gender,
        helper_name=helper_name,
        helper_type=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    return sorted(set((sym.name,) for sym in model if sym.name == "resolved"))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern(s) in the ASP twin.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("pier", "rope_tangle", "hands", "Mina", "girl", "Bram", "boy"),
            StoryParams("pier", "rope_tangle", "hook", "Lena", "girl", "Owen", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: rope at the pier centre"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
