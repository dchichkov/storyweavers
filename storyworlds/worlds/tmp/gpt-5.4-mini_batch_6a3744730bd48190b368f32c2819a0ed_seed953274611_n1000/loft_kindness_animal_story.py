#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/loft_kindness_animal_story.py
=============================================================

A small storyworld for a TinyStories-style animal tale set in a loft.

Seed premise
------------
A little animal lives in a loft. Something goes wrong during a small play or
task, and kindness from another animal helps fix it. The ending should show a
real change in the world state: a shared toy, repaired nest, cleaned spill, or a
brighter, calmer loft.

This world keeps the prose concrete and child-facing:
- typed entities with physical meters and emotional memes
- a simple causal engine
- a reasonableness gate
- an inline ASP twin
- story-grounded and world-knowledge Q&A
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
CALM_MIN = 2
KIND_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"dog", "puppy", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    above: str
    cozy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    type: str
    sound: str
    trait: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    action: str
    mess: str
    risk: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindFix:
    id: str
    sense: int
    power: int
    text: str
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
        return self.entities[eid]

    def animals(self) -> list[Entity]:
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.animals():
        if actor.meters["upset"] < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        loft = world.get("loft")
        loft.meters["mess"] += 1
        for other in world.animals():
            if other.id != actor.id:
                other.memes["worry"] += 1
        out.append("")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    if "helper" not in world.entities or "hero" not in world.entities:
        return out
    helper = world.get("helper")
    hero = world.get("hero")
    if helper.memes["kindness"] < KIND_MIN or hero.meters["mess"] < THRESHOLD:
        return out
    sig = ("kind",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] += 1
    hero.meters["mess"] = 0
    world.get("loft").meters["mess"] = 0
    out.append("")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("spill", "physical", _r_spill),
    Rule("kindness", "social", _r_kindness),
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
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(animal: Animal, trouble: Trouble, fix: KindFix) -> bool:
    return trouble.zone in {"loft_floor", "table_edge"} and fix.sense >= SENSE_MIN


def calm_enough(fix: KindFix, trouble: Trouble) -> bool:
    return fix.power >= 1 and trouble.risk in {"small", "medium"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for trouble_id, trouble in TROUBLES.items():
            for fix_id, fix in FIXES.items():
                if reasonableness_gate(ANIMALS["hero"], trouble, fix) and calm_enough(fix, trouble):
                    combos.append((setting_id, trouble_id, fix_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    trouble: str
    fix: str
    seed: Optional[int] = None
    hero_type: str = "cat"
    helper_type: str = "dog"
    helper_trait: str = "kind"
    hero_trait: str = "shy"
    trouble_level: str = "small"


SETTINGS = {
    "loft": Setting(
        id="loft",
        place="a sunny loft",
        above="the big stairs",
        cozy="the soft rug",
        tags={"loft"},
    )
}

ANIMALS = {
    "hero": Animal(id="Mina", type="cat", sound="mew", trait="shy", tags={"cat", "animal"}),
    "helper": Animal(id="Roo", type="dog", sound="woof", trait="kind", tags={"dog", "animal"}),
}

TROUBLES = {
    "spilled_milk": Trouble(
        id="spilled_milk",
        action="knocked over a cup of milk",
        mess="milk",
        risk="small",
        zone="loft_floor",
        tags={"spill", "milk"},
    ),
    "torn_blanket": Trouble(
        id="torn_blanket",
        action="pulled a blanket too hard",
        mess="fray",
        risk="small",
        zone="table_edge",
        tags={"blanket"},
    ),
}

FIXES = {
    "wipe": KindFix(
        id="wipe",
        sense=3,
        power=1,
        text="fetched a cloth and wiped the floor until it shone again",
        qa_text="fetched a cloth and wiped the floor clean",
        tags={"cloth", "clean"},
    ),
    "share_blanket": KindFix(
        id="share_blanket",
        sense=2,
        power=1,
        text="found the torn blanket's other end and tucked it in gently",
        qa_text="helped tuck the blanket in gently",
        tags={"blanket", "gentle"},
    ),
    "snuggle": KindFix(
        id="snuggle",
        sense=2,
        power=1,
        text="sat beside the small animal and shared a warm snuggle",
        qa_text="sat beside the small animal and shared a warm snuggle",
        tags={"warm", "kind"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Pip", "Nia", "Tess"]
BOY_NAMES = ["Pip", "Ollie", "Finn", "Milo", "Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A loft kindness animal storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
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


def explain_rejection(trouble: Trouble, fix: KindFix) -> str:
    return f"(No story: {fix.id} does not quite fit the small loft trouble with kindness.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.fix and not reasonableness_gate(ANIMALS["hero"], TROUBLES[args.trouble], FIXES[args.fix]):
        raise StoryError(explain_rejection(TROUBLES[args.trouble], FIXES[args.fix]))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(f"(Refusing fix '{args.fix}' because it is too weak.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, fix = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(setting=setting, hero=hero, helper=helper, trouble=trouble, fix=fix)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero", attrs={"trait": params.hero_trait}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper", attrs={"trait": params.helper_trait}))
    loft = world.add(Entity(id="loft", type="setting", label="the loft"))
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    hero.memes["shy"] += 1
    helper.memes["kindness"] += 2

    world.say(f"Up in a sunny loft, {hero.id} lived with {helper.id} near the soft rug.")
    world.say(f"One afternoon, {hero.id} {trouble.action}, and the little place became messy.")
    world.para()
    world.say(f"{hero.id} looked down and felt upset. {helper.id} saw the mess and stayed calm.")
    world.say(f'"Let me help," {helper.id} said, and {fix.text}.')
    propagate(world, narrate=False)
    world.para()
    world.say(f"{hero.id} blinked, then smiled. {helper.id}'s kindness made the loft cozy again.")
    world.say(f"In the end, the loft was tidy, the rug was warm, and both animals curled up together.")

    world.facts.update(
        hero=hero,
        helper=helper,
        loft=loft,
        trouble=trouble,
        fix=fix,
        setting=SETTINGS[params.setting],
        outcome="kind",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short animal story set in a loft where kindness helps fix a small mess.",
        f"Tell a gentle story about {f['hero'].id} and {f['helper'].id} in the loft.",
        f"Write a story that includes the word loft and shows {f['helper'].id} being kind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trouble = f["trouble"]
    fix = f["fix"]
    return [
        ("Where does the story happen?", "It happens in a sunny loft above the stairs."),
        (f"What went wrong for {hero.id}?", f"{hero.id} {trouble.action}. That made the loft messy and upset {hero.id}."),
        (f"How did {helper.id} help?", f"{helper.id} was kind and {fix.qa_text}. That helped the loft feel safe and cozy again."),
        ("How did the story end?", "The loft was tidy again, and the two animals curled up together in peace."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a loft?", "A loft is a room or space high up under a roof. It can feel bright and cozy."),
        ("What is kindness?", "Kindness means helping in a gentle, caring way. It makes others feel better."),
        ("Why is sharing helpful?", "Sharing lets two animals use the same thing without fighting. It helps them stay calm and happy."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="loft", hero="Mina", helper="Roo", trouble="spilled_milk", fix="wipe", hero_type="cat", helper_type="dog"),
    StoryParams(setting="loft", hero="Pip", helper="Luna", trouble="torn_blanket", fix="share_blanket", hero_type="kitten", helper_type="cat"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.trouble not in TROUBLES or params.fix not in FIXES:
        raise StoryError("(Invalid parameters for this storyworld.)")
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


ASP_RULES = r"""
valid(S,T,F) :- setting(S), trouble(T), fix(F), kind_fit(T,F).
kind_fit(T,F) :- trouble(T), fix(F), sense(F,SN), sense_min(M), SN >= M.
outcome(kind) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("sense_min", SENSE_MIN)]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("zone", tid, t.zone))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        with redirect_stdout(io.StringIO()):
            sample = generate(CURATED[0])
            emit(sample, trace=False, qa=False)
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx+1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
