#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/xyz_cautionary_rhyming_story.py
===============================================================

A tiny cautionary rhyming storyworld built from the seed word "xyz".

Premise:
- A child wants to do something playful and mildly risky with letters, lights, or
  a pretend machine.
- A helper notices a problem early, warns them, and they choose a safe fix.
- The story ends with a concrete, changed world state: the risky mess is gone,
  the safe tool is used, and the child remembers the lesson.

This world keeps the prose child-facing and rhythmic, while the simulation tracks
physical meters and emotional memes so the story is driven by state rather than
a frozen template.
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    setup: str
    goal: str
    rhyme_open: str
    rhyme_close: str


@dataclass
class RiskyItem:
    id: str
    label: str
    phrase: str
    hazard: str
    risky_word: str
    makes_mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    use: str
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
    risky: str
    tool: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["mess"] += 1
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["worry"] += 0.5
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


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


def risky_at_risk(risky: RiskyItem, theme: Theme) -> bool:
    return True if risky.makes_mess else False


def sensible_fix(fid: str) -> bool:
    return FIXES[fid].sense >= SENSE_MIN


def fixs_fire(fix: Fix, risky: RiskyItem) -> bool:
    return fix.power >= 1


def predict(world: World, risky_id: str) -> dict:
    sim = world.copy()
    _do_risky(sim, sim.get(risky_id), narrate=False)
    return {"mess": sim.get(risky_id).meters["mess"], "worry": sum(e.memes["worry"] for e in sim.entities.values())}


def _do_risky(world: World, risky_ent: Entity, narrate: bool = True) -> None:
    risky_ent.meters["mess"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, child: Entity, helper: Entity, theme: Theme) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(f"{child.id} and {helper.id} began with a grin, in {theme.scene}. {theme.setup}")
    world.say(f'"{theme.rhyme_open}" sang {child.id}, with a hop and a spin.')


def want(world: World, child: Entity, risky: RiskyItem) -> None:
    child.memes["want"] += 1
    world.say(f'{child.id} wanted {risky.phrase}, "for fun in the sun," they said, "just for a din."')


def warn(world: World, helper: Entity, child: Entity, risky: RiskyItem) -> None:
    pred = predict(world, "risky")
    helper.memes["care"] += 1
    world.facts["pred_mess"] = pred["mess"]
    world.say(
        f'{helper.id} gave a soft, quick warning, "Oh no, not {risky.label}! '
        f'It can make a {risky.makes_mess} scene."'
    )
    world.say(
        f'"A small mistake can grow fast," {helper.id} said, "so let us keep our play clean and keen."'
    )


def do_risky(world: World, child: Entity, risky: RiskyItem) -> None:
    child.memes["defiance"] += 1
    world.say(f'"I can do it!" {child.id} declared, and reached in with a gleam.')
    world.say(f"Then {risky.risky_word} happened, and the {risky.hazard} made a streaking stream.")


def safe_fix(world: World, parent: Entity, fix: Fix, risky: RiskyItem, tool: SafeTool) -> None:
    body = fix.text.replace("{risky}", risky.label).replace("{tool}", tool.label)
    world.say(f"{parent.label_word.capitalize()} came calmly and {body}.")
    world.say(f"The mess was gone, and the room felt bright, as neat as a dream.")


def lesson(world: World, parent: Entity, child: Entity, helper: Entity, risky: RiskyItem) -> None:
    for e in (child, helper):
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
        e.memes["worry"] = 0.0
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and said, "
        f'"Next time, call me first. {risky.label.capitalize()} is not a game to try."'
    )
    world.say(f'"We promise," said {child.id} and {helper.id}, their voices small but spry.')


def safe_ending(world: World, child: Entity, helper: Entity, theme: Theme, tool: SafeTool) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last they used {tool.phrase}, and {tool.use}; {theme.rhyme_close}."
    )
    world.say(f"{child.id} laughed, and the safe new plan felt sweet and shy.")


def tell(theme: Theme, risky: RiskyItem, tool: SafeTool, fix: Fix,
         child: str = "Milo", child_gender: str = "boy",
         helper: str = "Nia", helper_gender: str = "girl",
         parent: str = "mother") -> World:
    world = World()
    c = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    p = world.add(Entity(id="Parent", kind="character", type=parent, role="parent"))
    world.add(Entity(id="risky", label=risky.label))
    world.add(Entity(id="floor", label="the floor"))
    world.facts.update(tool=tool, fix=fix, risky=risky, theme=theme, child=c, helper=h, parent=p)

    open_scene(world, c, h, theme)
    world.para()
    want(world, c, risky)
    warn(world, h, c, risky)
    world.para()
    do_risky(world, c, risky)
    world.para()
    safe_fix(world, p, fix, risky, tool)
    lesson(world, p, c, h, risky)
    world.para()
    safe_ending(world, c, h, theme, tool)

    world.facts["outcome"] = "safe"
    return world


THEMES = {
    "xyz": Theme(
        id="xyz",
        scene="a cozy corner with paper stars and bright chalk swirls",
        setup="A little cardboard sign said X, Y, Z, and the whole room hummed with play.",
        goal="spell a zigzag word",
        rhyme_open="X to Y to Z, let's see!",
        rhyme_close="Their tidy little ending was happy as can be.",
    )
}

RISKIES = {
    "xyz": RiskyItem(
        id="xyz",
        label="the xyz sticks",
        phrase="the xyz sticks",
        hazard="messy scatter",
        risky_word="a little clang-and-clatter",
        makes_mess="mess",
        tags={"xyz", "letters"},
    )
}

TOOLS = {
    "tray": SafeTool(
        id="tray",
        label="a tray",
        phrase="a tray",
        use="kept the letters from skidding away",
        tags={"tray"},
    ),
}

FIXES = {
    "scoop": Fix(
        id="scoop",
        sense=3,
        power=3,
        text="scooped up the {risky}, set them on a {tool}, and steadied the game",
        fail="tried to scoop up the {risky}, but the mess kept growing anyway",
        qa_text="scooped up the {risky} and set them on a {tool}",
        tags={"cleanup"},
    ),
}

GIRL_NAMES = ["Nia", "Mia", "Zoe", "Ava", "Luna"]
BOY_NAMES = ["Milo", "Leo", "Noah", "Theo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in THEMES:
        for rid, risky in RISKIES.items():
            for tool in TOOLS:
                if risky_at_risk(risky, THEMES[tid]):
                    combos.append((tid, rid, tool))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary rhyming storyworld with xyz.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--risky", choices=RISKIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.fix and not sensible_fix(args.fix):
        raise StoryError("unsafe fix")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.risky is None or c[1] == args.risky)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, risky, tool = rng.choice(sorted(combos))
    fix = args.fix or "scoop"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme=theme, risky=risky, tool=tool, fix=fix,
                       child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short cautionary rhyming story that includes "xyz".',
        f"Tell a rhyming story where {f['child'].id} and {f['helper'].id} worry about {f['risky'].label} but choose a safe fix.",
        "Make the ending gentle, with a lesson and a safer way to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    risky: RiskyItem = f["risky"]
    fix: Fix = f["fix"]
    tool: SafeTool = f["tool"]
    return [
        QAItem(
            question="What did the child want to do?",
            answer=f"{child.id} wanted to play with {risky.label}. It sounded fun at first, but it could make a mess.",
        ),
        QAItem(
            question="How did the helper keep things safe?",
            answer=f"{helper.id} warned them early, and the grown-up used {tool.phrase} to steady {risky.label}. That kept the story calm and clean.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended safely. The {risky.label} were put on {tool.phrase}, the lesson was learned, and everyone could smile again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tray for?",
            answer="A tray helps hold small things so they do not slide around. It makes a game neater and safer.",
        ),
        QAItem(
            question="Why is it good to listen to warnings?",
            answer="Warnings can keep a small problem from growing into a bigger one. Listening early helps everyone stay safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    return "\n".join(out)


ASP_RULES = r"""
risky_at_risk(R) :- risky(R).
valid(T, R, U) :- theme(T), risky(R), tool(U), risky_at_risk(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for rid in RISKIES:
        lines.append(asp.fact("risky", rid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(THEMES[params.theme], RISKIES[params.risky], TOOLS[params.tool], FIXES[params.fix],
                     params.child, params.child_gender, params.helper, params.helper_gender, params.parent)
    except KeyError as err:
        raise StoryError(f"invalid parameter: {err}") from err
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


CURATED = [
    StoryParams(theme="xyz", risky="xyz", tool="tray", fix="scoop", child="Milo", child_gender="boy",
                helper="Nia", helper_gender="girl", parent="mother"),
    StoryParams(theme="xyz", risky="xyz", tool="tray", fix="scoop", child="Luna", child_gender="girl",
                helper="Theo", helper_gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
