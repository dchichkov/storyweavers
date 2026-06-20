#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/violet_conscience_problem_solving_folk_tale.py
===============================================================================

A small standalone story world for a folk-tale style problem-solving story that
uses the seed words "violet" and "conscience".

Premise
-------
Violet lives in a tiny village near a wood, a stream, and a market lane. A little
trouble appears: something important is lost, broken, or blocked. Violet's
conscience nudges her to choose a kind, clever fix instead of a quick selfish
one. The story ends with a concrete solution and a calm village image that shows
what changed.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- a causal world model
- grounded QA sets
- Python reasonableness gate
- inline ASP twin
- --verify smoke test and parity checks
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str


@dataclass
class Trouble:
    id: str
    noun: str
    label: str
    problem: str
    risk: str
    fixed_by: str
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["focus"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solveable(trouble: Trouble, tool: Tool) -> bool:
    return trouble.fixed_by == tool.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TROUBLES:
            for tool in TOOLS:
                if solveable(t, tool):
                    combos.append((s, t.id, tool.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    trouble: str
    tool: str
    name: str
    name_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "village": Setting("village", "the little village", "roofs of straw and stone"),
    "wood": Setting("wood", "the green wood", "birds in the boughs and moss on the stones"),
    "river": Setting("river", "the river lane", "willows leaning over the water"),
}

TROUBLES = {
    "bridge_rope": Trouble(
        "bridge_rope", "rope", "the bridge rope",
        problem="a rope on the little bridge has come loose",
        risk="the bridge may sag and scare the travelers",
        fixed_by="twine_knot",
        severity=1,
        tags={"bridge", "rope"},
    ),
    "goosegate": Trouble(
        "goosegate", "gate", "the goose gate",
        problem="the goose gate will not stay shut",
        risk="the geese wander into the herb patch",
        fixed_by="wooden_wedge",
        severity=1,
        tags={"gate", "goose"},
    ),
    "well_bucket": Trouble(
        "well_bucket", "bucket", "the well bucket",
        problem="the well bucket keeps slipping on its rope",
        risk="the villagers cannot draw water easily",
        fixed_by="brass_hook",
        severity=1,
        tags={"well", "bucket"},
    ),
}

TOOLS = {
    "twine_knot": Tool("twine_knot", "twine and a knot", "some strong twine", "tie the rope tight", tags={"rope", "bridge"}),
    "wooden_wedge": Tool("wooden_wedge", "a wooden wedge", "a small wedge of oak", "hold the gate firm", tags={"gate", "wood"}),
    "brass_hook": Tool("brass_hook", "a brass hook", "a little brass hook", "catch the bucket securely", tags={"well", "bucket"}),
}

GIRL_NAMES = ["Violet", "Mira", "Nell", "Rose", "Poppy", "Hazel"]
BOY_NAMES = ["Tobin", "Eli", "Finn", "Jonah", "Robin"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale problem-solving world with Violet and her conscience."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--name-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def explain_rejection(trouble: Trouble, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not solve {trouble.label}. "
        f"Try a tool that can actually fix the problem.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.tool:
        if not solveable(TROUBLES[args.trouble], TOOLS[args.tool]):
            raise StoryError(explain_rejection(TROUBLES[args.trouble], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, tool = rng.choice(sorted(combos))
    name_gender = args.name_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or ("Violet" if name_gender == "girl" else rng.choice(BOY_NAMES))
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    if helper == name:
        helper = "Mira" if name != "Mira" else "Nell"
    return StoryParams(setting, trouble, tool, name, name_gender, helper, helper_gender)


def tell(setting: Setting, trouble: Trouble, tool: Tool, name: str, name_gender: str,
         helper: str, helper_gender: str) -> World:
    world = World()
    violet = world.add(Entity(id=name, kind="character", type=name_gender, role="hero", traits=["kind", "clever"]))
    helper_e = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper", traits=["wise"]))
    conscience = world.add(Entity(id="conscience", kind="spirit", type="thing", label="conscience", role="inner_voice"))
    place = world.add(Entity(id=setting.id, type="place", label=setting.place))
    tr = world.add(Entity(id=trouble.id, type="trouble", label=trouble.label))
    tl = world.add(Entity(id=tool.id, type="tool", label=tool.label))
    violet.memes["care"] += 1
    helper_e.memes["help"] += 1
    conscience.memes["quiet"] += 1

    world.say(
        f"Long ago, in {setting.place}, lived {name}, a little child with a bright violet cloak and a kind heart. "
        f"{setting.detail}."
    )
    world.say(
        f"{name} had a small conscience that spoke like a whisper in the grass, "
        f"and when trouble came, that whisper never lied."
    )
    world.say(
        f"One morning, {trouble.problem}. {trouble.risk}."
    )
    world.para()
    world.say(
        f"{name} saw the problem and wanted to fix it at once, but {name}'s conscience tugged gently: "
        f'"First look carefully," it seemed to say. "A good fix must fit the harm."'
    )
    world.say(
        f"{helper} came along and agreed. Together they thought of {tool.phrase}."
    )
    world.say(
        f"They did not rush. They watched the broken place, tested the weight, and chose a way that matched it."
    )
    world.para()
    if trouble.id == "bridge_rope":
        world.say(
            f"{name} and {helper} tied the loose rope with {tool.phrase}, then pressed the knot flat so it would not slip. "
            f"The little bridge stood steady again."
        )
    elif trouble.id == "goosegate":
        world.say(
            f"{name} slid {tool.phrase} beneath the gate and held it shut while {helper} checked the latch. "
            f"The geese stayed in their yard, pecking at grass instead of herbs."
        )
    else:
        world.say(
            f"{name} hooked the bucket with {tool.phrase} and lifted it until the rope sat right. "
            f"After that, the well worked as it should."
        )
    world.say(
        f"When the work was done, {name} smiled, and the conscience inside {name}'s chest felt light as a flower in spring. "
        f"The village was safer, and the little problem had been solved by thinking first."
    )
    world.facts.update(
        hero=violet, helper=helper_e, conscience=conscience, setting=setting,
        trouble=trouble, tool=tool, solved=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story for a child named {f["hero"].id} that includes the words "violet" and "conscience".',
        f"Tell a village story where {f['hero'].id} uses {f['tool'].label} to solve a small problem with help from a friend.",
        f"Write a gentle problem-solving tale in which a child's conscience helps choose a careful fix.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, trouble, tool = f["hero"], f["helper"], f["trouble"], f["tool"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, who lives in a small folk-tale village and listens to a conscience inside {hero.id}'s heart."),
        ("What problem needed solving?",
         f"{trouble.problem}. That created a real problem in the village, so the children had to think carefully."),
        ("How did they solve it?",
         f"They used {tool.phrase} and worked together until the trouble was fixed. They chose a fix that matched the problem instead of guessing."),
        ("What did the conscience help Violet do?",
         f"It helped {hero.id} pause, look closely, and choose the right tool. That careful choice made the solution work."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["trouble"].tags) | set(world.facts["tool"].tags) | {"conscience"}
    out = []
    if "bridge" in tags:
        out.append(("What is a bridge for?", "A bridge helps people cross over water or a gap safely."))
    if "rope" in tags:
        out.append(("What is rope used for?", "Rope can tie, hold, lift, or secure things when it is used carefully."))
    if "gate" in tags:
        out.append(("What does a gate do?", "A gate can open and close to keep animals or people in or out."))
    if "well" in tags:
        out.append(("What is a well?", "A well is a deep place where people draw water."))
    out.append(("What is a conscience?", "A conscience is the quiet feeling that helps a person know what is kind, fair, and safe to do."))
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "bridge_rope", "twine_knot", "Violet", "girl", "Mira", "girl"),
    StoryParams("river", "well_bucket", "brass_hook", "Violet", "girl", "Tobin", "boy"),
    StoryParams("wood", "goosegate", "wooden_wedge", "Violet", "girl", "Nell", "girl"),
]


ASP_RULES = r"""
valid(S, T, U) :- setting(S), trouble(T), tool(U), fixes(U, T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TROUBLES.values():
        lines.append(asp.fact("trouble", t.id))
    for u in TOOLS.values():
        lines.append(asp.fact("tool", u.id))
        for tag in sorted(u.tags):
            lines.append(asp.fact("fixes", u.id, next(t.id for t in TROUBLES.values() if t.fixed_by == u.id)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, trouble=None, tool=None, name=None, name_gender=None, helper=None, helper_gender=None), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale problem solving story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--name-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TROUBLES[params.trouble], TOOLS[params.tool],
                 params.name, params.name_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, tool = rng.choice(sorted(combos))
    name_gender = args.name_gender or "girl"
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or "Violet"
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    if helper == name:
        helper = "Mira"
    return StoryParams(setting, trouble, tool, name, name_gender, helper, helper_gender)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
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
