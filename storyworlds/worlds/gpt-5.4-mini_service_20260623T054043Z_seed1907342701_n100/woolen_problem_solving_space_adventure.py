#!/usr/bin/env python3
"""
storyworlds/worlds/woolen_problem_solving_space_adventure.py
=============================================================

A standalone story world for a small space-adventure problem-solving tale:
a child astronaut wants to use a woolen item in a ship, a problem appears,
and the crew solves it by making the woolen thing useful in a safe way.

The world is tiny and classical:
- typed entities with meters and memes
- a forward causal rule or two
- a reasonableness gate for valid combinations
- inline ASP twin rules
- grounded prompts and QA
- complete child-facing stories with a beginning, turn, and ending image
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    danger: str
    fix_hint: str
    at_risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class WoolenItem:
    id: str
    label: str
    phrase: str
    use: str
    safe_use: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    if ship.meters["frost"] < THRESHOLD or ship.meters["leak"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    blanket = world.get("blanket")
    blanket.meters["used"] += 1
    ship.meters["frost"] = 0.0
    ship.meters["leak"] = 0.0
    out.append("The blanket sealed the leak and kept the cold air from spreading.")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["worry"] < THRESHOLD or hero.meters["fix_done"] < THRESHOLD:
        return out
    sig = ("comfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] += 1
    out.append("The cabin felt peaceful again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    events: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_repair, _r_comfort):
            s = rule(world)
            if s:
                changed = True
                events.extend(s)
    if narrate:
        for s in events:
            world.say(s)
    return events


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for prob in PROBLEMS:
            for item in WOOLEN_ITEMS:
                if p.id in prob.tags and item.id in prob.tags and item.id in TOOL_COMPAT:
                    combos.append((p.id, prob.id, item.id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    woolen: str
    tool: str = ""
    hero: str = "Nova"
    hero_type: str = "girl"
    helper: str = "Milo"
    helper_type: str = "boy"
    seed: Optional[int] = None


PLACES = [
    Place("orbital_hub", "the orbital hub", "a bright ring of rooms turning above Earth", {"leak", "frost"}, {"space", "hub"}),
    Place("moon_dock", "the moon dock", "a silver dock with low gravity and narrow rails", {"leak", "frost"}, {"space", "moon"}),
    Place("starship_bay", "the starship bay", "a small ship bay with blinking panels and a round window", {"leak", "frost"}, {"space", "ship"}),
]

PROBLEMS = [
    Problem("cold_leak", "a cold leak", "thin air made the cabin chilly", "seal the crack", "a sleeping panel", {"leak", "cold"}),
    Problem("frost_panel", "frost on a panel", "the screen looked cloudy and hard to read", "wipe it warm", "the navigation screen", {"frost", "cold"}),
    Problem("draft_corner", "a drafty corner", "the air kept slipping through a seam", "block the seam", "a little seam by the wall", {"leak", "draft"}),
]

WOOLEN_ITEMS = [
    WoolenItem("blanket", "a woolen blanket", "a woolen blanket folded in the locker", "covering the crack", "covering the crack and holding warmth in", {"cold_leak", "frost_panel", "draft_corner"}, {"woolen", "soft", "cover"}),
    WoolenItem("mittens", "woolen mittens", "a pair of woolen mittens", "warming hands", "warming hands and gripping tools safely", {"frost_panel", "draft_corner"}, {"woolen", "warm", "grip"}),
    WoolenItem("scarf", "a woolen scarf", "a long woolen scarf", "tucking around edges", "tucking around edges to stop the draft", {"draft_corner", "cold_leak"}, {"woolen", "warm", "wrap"}),
]

TOOL_COMPAT = {
    "blanket": "seal",
    "mittens": "wipe",
    "scarf": "block",
}

TOOLS = [
    Tool("seal_tape", "seal tape", "a roll of seal tape", "sealed the crack", {"leak", "seal"}),
    Tool("warm_cloth", "warm cloth", "a warm cloth", "softened the frost", {"frost", "warm"}),
    Tool("panel_clip", "panel clip", "a clip for the panel edge", "held the seam closed", {"draft", "block"}),
]

GIRL_NAMES = ["Nova", "Iris", "Luna", "Mira", "Zuri", "Ada"]
BOY_NAMES = ["Milo", "Tate", "Theo", "Jett", "Ravi", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure problem-solving storyworld with a woolen object.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--problem", choices=[p.id for p in PROBLEMS])
    ap.add_argument("--woolen", choices=[w.id for w in WOOLEN_ITEMS])
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _lookup(seq, key):
    for x in seq:
        if x.id == key:
            return x
    raise StoryError(f"Unknown choice: {key}")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.problem or args.woolen:
        combos = [c for c in combos
                  if (args.place is None or c[0] == args.place)
                  and (args.problem is None or c[1] == args.problem)
                  and (args.woolen is None or c[2] == args.woolen)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, woolen = rng.choice(sorted(combos))
    tool = args.tool or next(t.id for t in TOOLS if woolen in t.tags or _lookup(WOOLEN_ITEMS, woolen).id in TOOL_COMPAT)
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(place=place, problem=problem, woolen=woolen, tool=tool, hero=hero, helper=helper)


def tell(params: StoryParams) -> World:
    place = _lookup(PLACES, params.place)
    prob = _lookup(PROBLEMS, params.problem)
    wool = _lookup(WOOLEN_ITEMS, params.woolen)
    tool = _lookup(TOOLS, params.tool) if params.tool else TOOLS[0]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type="girl" if params.hero in GIRL_NAMES else "boy", label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type="girl" if params.helper in GIRL_NAMES else "boy", label=params.helper))
    ship = world.add(Entity(id="ship", type="ship", label="the ship"))
    blanket = world.add(Entity(id="blanket", type="item", label=wool.label, phrase=wool.phrase))
    world.facts.update(place=place, problem=prob, woolen=wool, tool=tool, hero=hero, helper=helper, ship=ship, blanket=blanket)
    hero.memes["curious"] += 1
    helper.memes["care"] += 1
    ship.meters["leak"] = 1.0
    ship.meters["frost"] = 1.0
    world.say(f"{params.hero} and {params.helper} drifted through {place.label}, where {place.scene}.")
    world.say(f"They found {wool.phrase}, and {params.hero} liked how {wool.use} felt in the quiet ship.")
    world.para()
    world.say(f"Then {prob.label} made the cabin uneasy: {prob.danger}.")
    hero.memes["worry"] += 1
    helper.memes["problem_solve"] += 1
    world.say(f"{params.helper} pointed at {prob.at_risk} and said they needed to {prob.fix_hint}.")
    if wool.id == "blanket":
        ship.meters["leak"] += 0.5
        world.say(f"{params.hero} spread the woolen blanket over the sleeping panel, and the draft calmed at once.")
    elif wool.id == "mittens":
        ship.meters["frost"] += 0.5
        world.say(f"{params.hero} wore the woolen mittens, warmed the screen, and wiped away the frost in careful circles.")
    else:
        ship.meters["leak"] += 0.5
        world.say(f"{params.hero} wrapped the woolen scarf along the seam, tucking it in until the cold air stopped whispering through.")
    hero.meters["fix_done"] += 1
    propagate(world)
    world.para()
    if ship.meters["leak"] < THRESHOLD and ship.meters["frost"] < THRESHOLD:
        world.say(f"With the problem solved, {params.hero} and {params.helper} watched the window turn blue with Earth below.")
        world.say(f"The woolen item stayed in place, and the little ship felt warm, tidy, and ready for the next star.")
    else:
        world.say("The fix did not fully hold, so they called for help and tried again with steadier hands.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child that includes the word "{f["woolen"].label.split()[0]}".',
        f"Tell a gentle problem-solving story where {f['hero'].label} and {f['helper'].label} use {f['woolen'].label} to help on {f['place'].label}.",
        f"Write a tiny story about fixing {f['problem'].label} with something woolen in a spaceship setting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, place, prob, wool = f["hero"], f["helper"], f["place"], f["problem"], f["woolen"]
    return [
        QAItem(question=f"What problem did {hero.label} and {helper.label} face on {place.label}?", answer=f"They faced {prob.label}. It made the ship feel uneasy, so they had to solve it."),
        QAItem(question=f"What woolen thing did they use to help?", answer=f"They used {wool.phrase}. It was a gentle fix because it could warm, cover, or block the problem area."),
        QAItem(question=f"How did the story show the problem was solved?", answer=f"By the end, the leak or frost was gone or held back, and the ship felt warm and ready again. The final picture is the woolen item sitting neatly where the problem had been."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does woolen mean?", answer="Woolen means made from wool, which is soft and warm."),
        QAItem(question="Why is woolen useful in space stories?", answer="A woolen thing can keep warmth in, soften a chill, or block a small draft. That makes it a good helper when a little ship has a problem."),
        QAItem(question="What is a problem-solving story?", answer="It is a story where characters notice a problem, think about it, try a fix, and then see that the fix worked."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orbital_hub", problem="cold_leak", woolen="blanket", tool="seal_tape", hero="Nova", helper="Milo"),
    StoryParams(place="moon_dock", problem="frost_panel", woolen="mittens", tool="warm_cloth", hero="Iris", helper="Tate"),
    StoryParams(place="starship_bay", problem="draft_corner", woolen="scarf", tool="panel_clip", hero="Luna", helper="Finn"),
    StoryParams(place="orbital_hub", problem="draft_corner", woolen="scarf", tool="panel_clip", hero="Mira", helper="Jett"),
]


def valid_story(params: StoryParams) -> bool:
    return (params.place, params.problem, params.woolen) in valid_combos()


ASP_RULES = r"""
valid(P, R, W) :- place(P), problem(R), woolen(W), fits(W, R), place_affords(P, R).
"""


def asp_facts() -> str:
    import asp
    out: list[str] = []
    for p in PLACES:
        out.append(asp.fact("place", p.id))
        for a in sorted(p.affords):
            out.append(asp.fact("place_affords", p.id, a))
    for p in PROBLEMS:
        out.append(asp.fact("problem", p.id))
        for t in sorted(p.tags):
            out.append(asp.fact("problem_tag", p.id, t))
    for w in WOOLEN_ITEMS:
        out.append(asp.fact("woolen", w.id))
        for t in sorted(w.fits):
            out.append(asp.fact("fits", w.id, t))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("(Invalid parameter combination.)")
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
