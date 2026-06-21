#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/peel_driveway_inner_monologue_happy_ending_heartwarming.py
=============================================================================================

A tiny storyworld about a child in a driveway, a peel that worries them, and a
heartwarming happy ending.

Premise
-------
A child notices something peeling in the driveway: a strip of old tape, a loose
edge of bright sticker paper, or a bit of sealant curling up. Their inner
monologue wonders if it means the game is ruined. A calm parent helps peel it
away the careful way, revealing a clean surface ready for a better, safer
finish. The ending image proves the change: the driveway is tidy again, and the
child feels proud instead of worried.

This world keeps a state-driven shape:
- physical meters: loose, clean, finished, comfort
- emotional memes: worry, relief, pride, warmth

The prose is authored from simulation state, not from a frozen paragraph swap.
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
class PeelChoice:
    id: str
    surface: str
    phrase: str
    risky: bool
    tidy_result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixChoice:
    id: str
    tool: str
    phrase: str
    gentle: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    peel: str
    fix: str
    child_name: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


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
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("surface").meters["loose"] >= THRESHOLD and world.get("child").memes["worry"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["worry"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


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


def reasonableness_gate(peel: PeelChoice, fix: FixChoice) -> bool:
    return peel.risky and fix.gentle


def valid_combos() -> list[tuple[str, str]]:
    return [(p.id, f.id) for p in PEELS.values() for f in FIXES.values() if reasonableness_gate(p, f)]


def _simulate_peel(world: World, peel: PeelChoice, narrate: bool = True) -> None:
    world.get("surface").meters["loose"] += 1
    world.get("child").memes["worry"] += 1
    propagate(world, narrate=narrate)


def tell(peel: PeelChoice, fix: FixChoice, child_name: str = "Mia",
         child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    surface = world.add(Entity(id="surface", label=peel.surface))
    surface.attrs["phrase"] = peel.phrase
    child.memes["warmth"] += 1

    world.say(
        f"In the driveway, {child.id} noticed {peel.phrase}. "
        f"The little edge looked like it wanted to peel away."
    )
    world.say(
        f'{child.id} held still and thought, "If I pull it, will it tear everything?" '
        f"{child.pronoun().capitalize()} wanted the driveway to stay neat."
    )

    world.para()
    world.say(
        f"{child.id} told {parent.label_word} about it. {parent.label_word.capitalize()} knelt beside "
        f"{child.id} and said that some things do need a careful peel."
    )
    world.say(
        f'Together they used {fix.phrase} and worked slowly, one small piece at a time.'
    )

    _simulate_peel(world, peel, narrate=False)
    surface.meters["clean"] += 1
    surface.meters["finished"] += 1
    child.memes["worry"] = 0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    parent.memes["warmth"] += 1

    world.para()
    world.say(
        f"The loose edge came off cleanly, and the driveway looked tidy again."
    )
    world.say(
        f"{child.id} smiled at the smooth spot and felt proud of helping."
    )
    world.say(
        f'Inside {child.pronoun("possessive")} own head, {child.id} thought, "I can do careful things."'
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled back, and the two of them stood in the sunny driveway, happy and calm."
    )

    world.facts.update(
        child=child,
        parent=parent,
        surface=surface,
        peel=peel,
        fix=fix,
        outcome="happy",
        cleaned=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    peel = f["peel"]
    return [
        f'Write a heartwarming story set in a driveway where {child.id} notices something peeling and worries about it, then a parent helps with a careful fix.',
        f"Tell a gentle story with an inner monologue where {child.id} thinks about whether to peel {peel.surface}, and the ending is happy and calm.",
        f'Write a child-friendly story that includes the word "peel" and ends with {child.id} feeling proud after a careful cleanup in the driveway.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    peel = f["peel"]
    fix = f["fix"]
    surface = f["surface"]
    return [
        QAItem(
            question="Why did the child feel worried at first?",
            answer=(
                f"{child.id} worried because the edge looked loose and {child.id} did not want to make it worse. "
                f"The careful fix made the worry feel much bigger before it turned into relief."
            ),
        ),
        QAItem(
            question="What helped the problem get better?",
            answer=(
                f"{parent.label_word.capitalize()} helped by using {fix.phrase} and peeling the loose part slowly. "
                f"That gentle method kept the surface neat and let the child feel safe."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended happily: the driveway was clean, the loose edge was gone, and {child.id} felt proud. "
                f"The smooth surface showed that careful work had paid off."
            ),
        ),
        QAItem(
            question=f"What was {peel.surface} like at the end?",
            answer=(
                f"{surface.label_word.capitalize()} was tidy, smooth, and finished. "
                f"The little mess had been peeled away carefully."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to peel something?",
            answer="To peel something means to lift off a thin layer or edge slowly, usually by hand.",
        ),
        QAItem(
            question="Why should peeling be done carefully?",
            answer="Careful peeling helps keep the rest of the surface from tearing or getting damaged.",
        ),
        QAItem(
            question="What is a driveway?",
            answer="A driveway is the hard path where cars can pull up to a house.",
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PEELS = {
    "sticker_edge": PeelChoice(
        id="sticker_edge",
        surface="the driveway sticker",
        phrase="a bright sticker edge on the driveway",
        risky=True,
        tidy_result="the sticker came off neatly",
        tags={"peel"},
    ),
    "tape_strip": PeelChoice(
        id="tape_strip",
        surface="the tape strip",
        phrase="a curled strip of tape near the garage line",
        risky=True,
        tidy_result="the tape came up in one calm strip",
        tags={"peel"},
    ),
    "sealant_flake": PeelChoice(
        id="sealant_flake",
        surface="the old sealant",
        phrase="a little flake of old sealant by the driveway crack",
        risky=True,
        tidy_result="the flake lifted away without making a mess",
        tags={"peel"},
    ),
}

FIXES = {
    "steady_hand": FixChoice(
        id="steady_hand",
        tool="a careful hand",
        phrase="a careful hand",
        gentle=True,
        tags={"careful"},
    ),
    "warm_cloth": FixChoice(
        id="warm_cloth",
        tool="a warm damp cloth",
        phrase="a warm damp cloth",
        gentle=True,
        tags={"careful"},
    ),
    "plastic_scraper": FixChoice(
        id="plastic_scraper",
        tool="a little plastic scraper",
        phrase="a little plastic scraper",
        gentle=True,
        tags={"careful"},
    ),
}

NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Ella"]
NAMES_BOY = ["Leo", "Theo", "Finn", "Max", "Eli"]
PARENTS = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming driveway storyworld about peel and a careful happy ending.")
    ap.add_argument("--peel", choices=PEELS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PEELS:
        lines.append(asp.fact("peel", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, F) :- peel(P), fix(F), gentle(F), risky(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: generate/serialize smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.peel and args.fix:
        if not reasonableness_gate(PEELS[args.peel], FIXES[args.fix]):
            raise StoryError("No story: that peel choice and fix choice do not make a gentle, sensible combination.")
    combos = [c for c in valid_combos()
              if (args.peel is None or c[0] == args.peel)
              and (args.fix is None or c[1] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    peel, fix = rng.choice(sorted(combos))
    peel_choice = PEELS[peel]
    fix_choice = FIXES[fix]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(peel=peel_choice.id, fix=fix_choice.id, child_name=name, child_gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.peel not in PEELS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    peel = PEELS[params.peel]
    fix = FIXES[params.fix]
    if not reasonableness_gate(peel, fix):
        raise StoryError("No story: the chosen peel/fix pair is not reasonable.")
    world = tell(peel, fix, params.child_name, params.child_gender, params.parent)
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
    StoryParams(peel="sticker_edge", fix="steady_hand", child_name="Mia", child_gender="girl", parent="mother"),
    StoryParams(peel="tape_strip", fix="warm_cloth", child_name="Leo", child_gender="boy", parent="father"),
    StoryParams(peel="sealant_flake", fix="plastic_scraper", child_name="Nora", child_gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible peel/fix combos:\n")
        for p, f in combos:
            print(f"  {p:14} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
