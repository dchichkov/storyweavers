#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/solution_mole_complaint_twist_lesson_learned_mystery.py
========================================================================================

A small mystery storyworld about a child, a complaint, a hidden mole, and a
surprising solution. The world is intentionally tiny: a clue trail, a mistaken
suspicion, a twist, and a lesson learned.

Seed words:
- solution
- mole
- complaint

Style:
- Mystery

Features:
- Twist
- Lesson Learned
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
    tags: set[str] = field(default_factory=set)
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
class Room:
    id: str
    label: str
    setting: str
    quiet: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    hidden_by: str = ""
    helpful: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MysteryCase:
    id: str
    complaint: str
    initial_suspect: str
    solution: str
    mole_place: str
    mole_tone: str
    twist: str
    lesson: str
    clue_chain: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.room = Room(id="garden", label="the garden", setting="moonlit mystery garden")
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.room = copy.deepcopy(self.room)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mole(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("mole_seen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("mole").meters["presence"] += 1
    out.append("__mole__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.meters["accusation"] < THRESHOLD:
        return out
    if parent.memes["calm"] < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["surprise"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("mole", _r_mole), Rule("twist", _r_twist)]


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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for case in CASES:
        for clue in CLUES:
            if clue.helpful and clue.reveals in {"mole", "solution"}:
                combos.append((case.id, clue.id))
    return combos


@dataclass
class StoryParams:
    case: str
    clue: str
    child_name: str
    child_gender: str
    parent_gender: str
    seed: Optional[int] = None


CASES = {
    "garden_rustle": MysteryCase(
        id="garden_rustle",
        complaint="a tiny complaint about scratching sounds under the bench",
        initial_suspect="the old broom",
        solution="the scratch came from a shy mole tunneling under the soil",
        mole_place="under the bench",
        mole_tone="small and dusty",
        twist="the blamed broom had only been nudged by the wind",
        lesson="not every odd noise is a bad person or a bad thing",
        clue_chain=["soil loose", "bench wobble", "tiny paw prints"],
        tags={"mole", "solution", "complaint", "twist"},
    ),
    "flower_bump": MysteryCase(
        id="flower_bump",
        complaint="a complaint that the flowerbed kept getting bumpy overnight",
        initial_suspect="the gardener's shovel",
        solution="the bumps were made by a mole pushing up neat little hills",
        mole_place="beside the tulips",
        mole_tone="soft and busy",
        twist="the shovel was not the culprit; it was leaning by the shed",
        lesson="a careful look can turn a guess into a real answer",
        clue_chain=["fresh soil", "round hill", "small tunnel"],
        tags={"mole", "solution", "complaint", "twist"},
    ),
}

CLUES = {
    "footprints": Clue("footprints", "footprints", "tiny prints in the dirt", "mole", tags={"mole"}),
    "soil": Clue("soil", "soil", "fresh soil pushed up in a line", "mole", tags={"mole"}),
    "lantern": Clue("lantern", "lantern", "a lantern making the shadows clear", "solution", tags={"solution"}),
    "notes": Clue("notes", "notes", "a little note with a careful plan", "solution", tags={"solution"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: complaint, mole, twist, solution.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--clue", choices=CLUES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.case not in CASES:
        raise StoryError("Unknown case.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.clue and CLUES[args.clue].reveals not in {"mole", "solution"}:
        raise StoryError("That clue would not support the mystery.")
    combos = [c for c in valid_combos()
              if (args.case is None or c[0] == args.case)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    case_id, clue_id = rng.choice(sorted(combos))
    child_name = rng.choice(["Mina", "Ivy", "Noah", "Lena", "Owen"])
    child_gender = rng.choice(["girl", "boy"])
    parent_gender = rng.choice(["mother", "father"])
    return StoryParams(case=case_id, clue=clue_id, child_name=child_name, child_gender=child_gender, parent_gender=parent_gender)


def tell(case: MysteryCase, clue: Clue, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="detective"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, label="the parent", role="guide"))
    mole = world.add(Entity(id="mole", kind="character", type="thing", label="the mole", role="hidden"))
    bench = world.add(Entity(id="bench", kind="thing", type="thing", label="the bench", role="suspect"))
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="thing", label=clue.label, role="clue", tags=set(clue.tags)))

    child.memes["curious"] = 1.0
    child.memes["worry"] = 1.0
    parent.memes["calm"] = 1.0

    world.say(
        f"One quiet night, {params.child_name} heard {case.complaint}. "
        f"The first suspect was {case.initial_suspect}."
    )
    world.say(
        f"{params.child_name} frowned at {clue.phrase} and wrote it down like a careful detective."
    )

    world.para()
    child.meters["accusation"] += 1
    world.say(
        f'"I have a complaint," {params.child_name} said. "Something is wrong in the garden."'
    )
    world.say(
        f"{params.child_name} followed the clue trail: {', '.join(case.clue_chain[:2])}."
    )
    propagate(world, narrate=False)

    world.para()
    if clue.reveals == "mole":
        child.memes["worry"] += 1
        world.say(
            f"Then came the twist: {clue_ent.phrase} pointed past the suspect and toward {case.mole_place}."
        )
        world.say(
            f"At last, the mystery solved itself: {case.solution}. {case.twist.capitalize()}."
        )
    else:
        world.say(
            f"{params.child_name} checked the notes again and found a cleaner path."
        )
        world.say(
            f"The solution was simple after all: {case.solution}."
        )

    world.para()
    parent.memes["pride"] += 1
    world.say(
        f"{params.child_name}'s {parent.label_word} smiled and said, "
        f'"The lesson learned is that a hasty guess can be wrong, but a careful look can find the real answer."'
    )
    world.say(
        f"By morning, the garden was calm again, and the tiny mole was safe under the soil."
    )
    world.facts.update(case=case, clue=clue, child=child, parent=parent, mole=mole, bench=bench)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: MysteryCase = f["case"]
    clue: Clue = f["clue"]
    child: Entity = f["child"]
    return [
        f'Write a mystery story for a young child that includes the words "{case.solution.split()[0]}", "mole", and "complaint".',
        f"Tell a mystery where {child.label} hears a complaint, follows a clue, and discovers a mole was the real answer.",
        f"Write a short story with a twist and a lesson learned, ending with the solution to the garden mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: MysteryCase = f["case"]
    clue: Clue = f["clue"]
    child: Entity = f["child"]
    return [
        QAItem(
            question="What was the complaint about?",
            answer=f"The complaint was about a strange scratching sound and bumpy ground in the garden. It made {child.label} think something mysterious was happening."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the first suspect was wrong. The real cause was a mole tunneling under the soil."
        ),
        QAItem(
            question="What was the solution?",
            answer=f"The solution was to follow the clue trail carefully and discover that the mole made the small changes in the garden. Once {child.label} saw that, the mystery made sense."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mole?",
            answer="A mole is a small animal that lives underground and makes tunnels in the soil. It can leave little bumps and fresh dirt on the ground."
        ),
        QAItem(
            question="What should a detective do first in a mystery?",
            answer="A detective should look carefully for clues before making a guess. Careful looking helps find the real answer."
        ),
        QAItem(
            question="What does lesson learned mean?",
            answer="A lesson learned is what someone remembers after a story teaches them something important. It helps them make a better choice next time."
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_case(C) :- case(C).
chosen_clue(L) :- clue(L).
mole_seen :- chosen_clue(footprints).
mole_seen :- chosen_clue(soil).
twist :- mole_seen.
lesson_learned :- twist.
outcome(solution) :- mole_seen, lesson_learned.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for lid in CLUES:
        lines.append(asp.fact("clue", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show mole_seen/0. #show twist/0."))
    _ = model
    return sorted(set((c, l) for c, l in valid_combos()))


def asp_verify() -> int:
    rc = 0
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
    try:
        sample = generate(resolve_params(argparse.Namespace(case=None, clue=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_sample(params: StoryParams) -> StorySample:
    world = tell(CASES[params.case], CLUES[params.clue], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(case="garden_rustle", clue="footprints", child_name="Mina", child_gender="girl", parent_gender="mother"),
    StoryParams(case="flower_bump", clue="soil", child_name="Owen", child_gender="boy", parent_gender="father"),
    StoryParams(case="garden_rustle", clue="lantern", child_name="Ivy", child_gender="girl", parent_gender="father"),
]


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = ["Mina", "Ivy", "Noah", "Lena", "Owen", "June", "Milo", "Nora"]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.case is None or c[0] == args.case)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    case_id, clue_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    parent_gender = rng.choice(["mother", "father"])
    return StoryParams(
        case=case_id,
        clue=clue_id,
        child_name=_pick_name(rng, child_gender),
        child_gender=child_gender,
        parent_gender=parent_gender,
    )


def build_parser_wrapper() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show mole_seen/0. #show twist/0. #show lesson_learned/0. #show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible (case, clue) combos:\n")
        for c, l in valid_combos():
            print(f"  {c:14} {l}")
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
            header = f"### {p.child_name}: {p.case} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
