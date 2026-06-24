#!/usr/bin/env python3
"""
storyworlds/worlds/caster_sandbox_reconciliation_mystery_to_solve_twist.py
===========================================================================

A standalone story world for a small slice-of-life sandbox tale about a caster
and a tiny mystery that ends in reconciliation with a twist.

Premise:
- In a sandbox, a child named Caster is building a sand road and a little tower.
- A small mystery appears: the tower keeps changing overnight.
- The twist is that a helpful friend has been secretly smoothing the sand to
  keep the road safe for toy wheels.
- After some worry, the children talk, solve the mystery, and make up.

The world models physical meters and emotional memes, so the prose is driven by
state changes rather than a frozen paragraph.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    soft: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    mystery: str = ""
    twist: str = ""

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.mystery = self.mystery
        clone.twist = self.twist
        return clone


SETTINGS = {
    "sandbox": Place(
        id="sandbox",
        label="the sandbox",
        phrase="the sandbox behind the fence",
        soft=True,
        tags={"sandbox", "sand"},
    )
}

TOOLS = {
    "bucket": Tool(
        id="bucket",
        label="a small bucket",
        phrase="a small bucket",
        use="carry water for smoothing",
        tags={"bucket", "water"},
    ),
    "spade": Tool(
        id="spade",
        label="a red spade",
        phrase="a red spade",
        use="shape paths and towers",
        tags={"spade", "sand"},
    ),
    "caster": Tool(
        id="caster",
        label="a toy caster wheel",
        phrase="a toy caster wheel",
        use="roll along the road",
        tags={"caster", "wheel"},
    ),
}

PROBLEMS = {
    "footprints": Problem(
        id="footprints",
        label="footprints",
        phrase="fresh footprints",
        effect="made the path bumpy",
        tags={"footprints", "sand"},
    ),
    "crumbles": Problem(
        id="crumbles",
        label="crumbles",
        phrase="little sand crumbles",
        effect="made the tower lean",
        tags={"crumbles", "sand"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tia", "Zoe"]
BOY_NAMES = ["Caster", "Ben", "Milo", "Theo", "Finn"]
TRAITS = ["quiet", "curious", "gentle", "patient", "careful"]


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
    tool: str
    problem: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for tool in TOOLS:
            for prob in PROBLEMS:
                combos.append((place, tool, prob))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life sandbox mystery with reconciliation and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, problem = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = args.friend_gender or ("girl" if gender == "boy" else "boy")
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero]
    friend = args.friend or rng.choice(friend_pool or (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES))
    if friend == hero:
        raise StoryError("Hero and friend must be different children.")
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, hero=hero, hero_gender=gender, friend=friend,
                       friend_gender=friend_gender, trait=trait, tool=tool, problem=problem)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,Pr) :- place(P), tool(T), problem(Pr).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place=place, mystery="mystery", twist="twist")
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender))
    bucket = world.add(Entity(id="bucket", type="tool", label=TOOLS["bucket"].label, owner=hero.id))
    spade = world.add(Entity(id="spade", type="tool", label=TOOLS["spade"].label, owner=hero.id))
    caster = world.add(Entity(id="caster", type="tool", label=TOOLS["caster"].label, owner=friend.id))
    prob = PROBLEMS[params.problem]

    hero.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(f"{hero.id} liked the sandbox behind the fence because it felt calm and soft. {hero.id} and {friend.id} spent the morning making a little road and a little tower.")
    world.say(f"{hero.id} used {spade.label} to shape the sand, and {friend.id} rolled {caster.label} along the road as if it were a tiny cart.")
    world.para()
    hero.memes["mystery"] += 1
    world.say(f"The next day, {hero.id} noticed a small mystery: {prob.phrase} had appeared near the tower, and {prob.effect}.")
    world.say(f"{hero.id} frowned and asked, \"Who changed our sandbox?\" {friend.id} looked surprised and said {hero.id} did not do it.")
    world.para()
    friend.memes["wish_to_help"] += 1
    world.say(f"{friend.id} knelt down and showed {hero.id} a clue: {bucket.label} had been left by the fence, with a damp ring inside it.")
    world.say(f"That was the twist. {friend.id} had not been trying to be sneaky; {friend.id} had been quietly using water to smooth the road so {caster.label} would not get stuck.")
    world.para()
    hero.memes["worry"] += 1
    world.say(f"{hero.id} stopped frowning. \"I thought someone was messing it up,\" {hero.id} said.")
    world.say(f"{friend.id} said, \"I should have told you first.\" Then {hero.id} laughed a little and said, \"Next time, let's do it together.\"")
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    hero.memes["reconcile"] += 1
    friend.memes["reconcile"] += 1
    world.say(f"So they fixed the road together, packed the damp sand gently around the tower, and made it stronger than before.")
    world.say(f"By the end, {hero.id} was rolling {caster.label} in smooth loops, {friend.id} was smiling beside the tower, and the sandbox looked neat, busy, and peaceful.")
    world.facts.update(hero=hero, friend=friend, tool=caster, bucket=bucket, spade=spade,
                       problem=prob, place=place, params=params, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story for a young child in {f["place"].label} with the word "caster" in it.',
        f"Tell a sandbox story where {f['hero'].id} thinks there is a mystery, but the truth is kind and ordinary.",
        f"Write a story about a small misunderstanding, a twist, and two children making up while playing in a sandbox.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prob = f["problem"]
    return [
        QAItem(
            question=f"What did {hero.id} think was the mystery in the sandbox?",
            answer=f"{hero.id} thought the {prob.label} were a sign that someone had changed the sandbox. Then {hero.id} learned the truth and stopped worrying.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {friend.id} was not ruining the sand at all. {friend.id} was helping by smoothing the road so the toy caster would roll better.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} feel at the end?",
            answer=f"They felt calm and friendly again. After talking, they fixed the sandbox together and made up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sandbox?",
            answer="A sandbox is a place filled with sand where children can dig, build, and play with toys.",
        ),
        QAItem(
            question="What is a caster wheel?",
            answer="A caster wheel is a small wheel that helps something roll and turn smoothly.",
        ),
        QAItem(
            question="Why do children talk when they have a misunderstanding?",
            answer="Talking helps them find out what really happened. It can clear up worry and help people make up.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="sandbox", hero="Caster", hero_gender="boy", friend="Mina", friend_gender="girl", trait="careful", tool="caster", problem="footprints"),
    StoryParams(place="sandbox", hero="Nora", hero_gender="girl", friend="Finn", friend_gender="boy", trait="gentle", tool="caster", problem="crumbles"),
]


def generate(params: StoryParams) -> StorySample:
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
        print(f"{len(asp_valid_combos())} compatible (place, tool, problem) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.hero}: sandbox mystery and reconciliation"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
