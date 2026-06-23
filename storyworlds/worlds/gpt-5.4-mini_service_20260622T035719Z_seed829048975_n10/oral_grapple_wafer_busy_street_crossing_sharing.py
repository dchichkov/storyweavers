#!/usr/bin/env python3
"""
storyworlds/worlds/oral_grapple_wafer_busy_street_crossing_sharing.py
======================================================================

A compact storyworld about a busy street crossing, where a small misunderstanding
about sharing a wafer turns into a comic problem-solving moment.

The seed words are woven into the world model:
- oral: the narrator/QA can mention a spoken reminder or oral warning
- grapple: the children briefly grapple over the snack bag
- wafer: the shared snack that causes the misunderstanding

Story features:
- Sharing
- Problem Solving
- Misunderstanding

Style:
- Comedy
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: __import__("copy").deepcopy(v) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [dict(item) for item in self.history]
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    crossing: str
    snack: str
    conflict: str
    resolver: str
    child1_name: str
    child1_type: str
    child2_name: str
    child2_type: str
    adult_name: str
    adult_type: str
    tone: str = "comedy"
    seed: int | None = None


@dataclass
class Crossing:
    id: str
    place: str
    signal: str
    noise: str
    crowd: str


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    crumbs: str
    shareable: bool = True


@dataclass
class Conflict:
    id: str
    misunderstanding: str
    worry: str
    fix_hint: str


@dataclass
class Resolver:
    id: str
    method: str
    punchline: str


CROSSINGS = {
    "busy_street": Crossing(
        id="busy_street",
        place="the busy street crossing",
        signal="the walk sign blinked like a little blinking box of manners",
        noise="cars hummed, buses sighed, and a bike bell went ding-ding",
        crowd="people hurried by with shopping bags and umbrellas",
    )
}

SNACKS = {
    "wafer": Snack(
        id="wafer",
        label="wafer",
        phrase="a crisp wafer in a blue wrapper",
        crumbs="tiny crumbs",
        shareable=True,
    )
}

CONFLICTS = {
    "sharing": Conflict(
        id="sharing",
        misunderstanding="one child thought the wrapper meant private snack treasure",
        worry="the other child thought the snack had vanished into a pocket",
        fix_hint="sharing the wafer one careful bite at a time",
    )
}

RESOLVERS = {
    "problem_solving": Resolver(
        id="problem_solving",
        method="ask first, then split the wafer down the middle",
        punchline="the wafer became two happy halves instead of one dramatic whole",
    )
}

GIRL_NAMES = ["Mia", "Nora", "Lina", "Zoe", "Ivy", "June"]
BOY_NAMES = ["Leo", "Finn", "Sam", "Theo", "Max", "Owen"]
TRAITS = ["cheerful", "curious", "silly", "careful", "helpful", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("busy_street", "wafer", "sharing")]


def explain_rejection(crossing: Crossing, snack: Snack, conflict: Conflict) -> str:
    return f"(No story: the chosen combo does not fit a comic sharing mishap at {crossing.place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: a busy crossing, a wafer, and a sharing mix-up.")
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--resolver", choices=RESOLVERS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--adult")
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = valid_combos()
    if args.crossing and args.crossing != "busy_street":
        raise StoryError(explain_rejection(CROSSINGS["busy_street"], SNACKS["wafer"], CONFLICTS["sharing"]))
    if args.snack and args.snack != "wafer":
        raise StoryError(explain_rejection(CROSSINGS["busy_street"], SNACKS["wafer"], CONFLICTS["sharing"]))
    if args.conflict and args.conflict != "sharing":
        raise StoryError(explain_rejection(CROSSINGS["busy_street"], SNACKS["wafer"], CONFLICTS["sharing"]))
    if args.resolver and args.resolver != "problem_solving":
        raise StoryError(explain_rejection(CROSSINGS["busy_street"], SNACKS["wafer"], CONFLICTS["sharing"]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    cross_id, snack_id, conflict_id = rng.choice(combos)
    resolver_id = args.resolver or "problem_solving"
    name1 = args.name1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    name2_pool = [n for n in GIRL_NAMES + BOY_NAMES if n != name1]
    name2 = args.name2 or rng.choice(name2_pool)
    adult = args.adult or rng.choice(["Mom", "Dad"])
    child1_type = "girl" if name1 in GIRL_NAMES else "boy"
    child2_type = "girl" if name2 in GIRL_NAMES else "boy"
    return StoryParams(
        crossing=cross_id,
        snack=snack_id,
        conflict=conflict_id,
        resolver=resolver_id,
        child1_name=name1,
        child1_type=child1_type,
        child2_name=name2,
        child2_type=child2_type,
        adult_name=adult,
        adult_type="mother" if adult == "Mom" else "father",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c1 = f["child1"]
    c2 = f["child2"]
    return [
        f'Write a funny story for a young child set at {f["crossing"].place} about {c1.id}, {c2.id}, and a shared wafer.',
        f"Tell a comedy about a misunderstanding over a wafer at {f['crossing'].place} where {c1.id} and {c2.id} have to solve the problem.",
        f'Write a simple story using the words "oral", "grapple", and "wafer" with sharing and a happy fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1 = f["child1"]
    c2 = f["child2"]
    adult = f["adult"]
    snack = f["snack"]
    return [
        QAItem(
            question=f"What were {c1.id} and {c2.id} doing at {f['crossing'].place}?",
            answer=f"They were crossing the street and trying to share {snack.phrase}. The busy crossing made everyone move carefully, which turned the snack into a funny little problem.",
        ),
        QAItem(
            question=f"Why did {c1.id} and {c2.id} start to grapple?",
            answer=f"They both wanted the wafer at the same time because of a misunderstanding. Once {adult.id} spoke up, they realized nobody meant to keep it all to themselves.",
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer=f"They listened to an oral reminder from {adult.id} and split the wafer into two pieces. That made the snack fair and stopped the grappling right away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wafer?",
            answer="A wafer is a thin, crisp snack that can snap into pieces easily. It is small enough to share, which makes it handy for a comedy about polite problems.",
        ),
        QAItem(
            question="What does oral mean in this storyworld?",
            answer="Oral means spoken out loud instead of written down. In this story, the adult gives an oral reminder to help solve the misunderstanding.",
        ),
        QAItem(
            question="What does grapple mean?",
            answer="Grapple means to hold on tightly or struggle over something. Here it is a comic, harmless tug over a snack, not a real fight.",
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


def tell(crossing: Crossing, snack: Snack, conflict: Conflict, resolver: Resolver, params: StoryParams) -> World:
    world = World()
    c1 = world.add(Entity(id=params.child1_name, kind="character", type=params.child1_type, role="child"))
    c2 = world.add(Entity(id=params.child2_name, kind="character", type=params.child2_type, role="child"))
    adult = world.add(Entity(id=params.adult_name, kind="character", type=params.adult_type, role="adult"))
    snack_ent = world.add(Entity(id="wafer", kind="thing", type="snack", label="wafer", phrase="a wafer", owner=c1.id, plural=False))
    c1.memes["want"] += 1
    c2.memes["want"] += 1
    c1.meters["hands"] += 1
    c2.meters["hands"] += 1
    world.say(f"{c1.id} and {c2.id} were at {crossing.place}, and {crossing.signal}.")
    world.say(f"{crossing.noise} while {crossing.crowd} hurried around them.")
    world.say(f"{c1.id} had {snack.phrase}, and {c2.id} thought sharing meant keeping it very, very close.")
    world.para()
    world.say(f"Then came the misunderstanding: {conflict.misunderstanding}.")
    world.say(f"They both reached for the wafer, and soon they had a comic grapple over one tiny snack bag.")
    c1.memes["confused"] += 1
    c2.memes["confused"] += 1
    world.event("grapple", child1=c1.id, child2=c2.id, snack=snack_ent.id)
    world.para()
    world.say(f"{adult.id} gave an oral reminder: 'Pause, breathe, and share the wafer fairly.'")
    world.say(f"{resolver.method.capitalize()}, {adult.id} suggested, and that solved the problem in the silliest way possible.")
    c1.memes["relief"] += 1
    c2.memes["relief"] += 1
    c1.memes["sharing"] += 1
    c2.memes["sharing"] += 1
    snack_ent.meters["shared"] = 1
    world.say(f"{c1.id} took one half, {c2.id} took the other, and the wafer became {resolver.punchline}.")
    world.say("They laughed, the traffic kept humming, and the crossing turned back into an ordinary street instead of a snack courtroom.")
    world.facts.update(
        crossing=crossing,
        snack=snack,
        conflict=conflict,
        resolver=resolver,
        child1=c1,
        child2=c2,
        adult=adult,
        snack_ent=snack_ent,
    )
    return world


ASP_RULES = r"""
shared(X) :- wafer(X).
misunderstanding(C1,C2) :- child(C1), child(C2), C1 != C2.
problem(C1,C2) :- misunderstanding(C1,C2), shared(wafer).
solved :- problem(_, _), oral_reminder, split_wafer.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, cross in CROSSINGS.items():
        lines.append(asp.fact("crossing", cid))
        lines.append(asp.fact("place", cid, cross.place))
    for sid in SNACKS:
        lines.append(asp.fact("wafer", sid))
    for fid in CONFLICTS:
        lines.append(asp.fact("conflict", fid))
    for rid in RESOLVERS:
        lines.append(asp.fact("resolver", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show shared/1.\n#show solved/0."))
        _ = model
    except Exception as err:
        print(f"ASP unavailable or failed: {err}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(CROSSINGS[params.crossing], SNACKS[params.snack], CONFLICTS[params.conflict], RESOLVERS[params.resolver], params)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        crossing="busy_street",
        snack="wafer",
        conflict="sharing",
        resolver="problem_solving",
        child1_name="Mia",
        child1_type="girl",
        child2_name="Leo",
        child2_type="boy",
        adult_name="Mom",
        adult_type="mother",
    )
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shared/1.\n#show solved/0."))
        return
    if args.verify:
        sample = generate(CURATED[0])
        if not sample.story or "wafer" not in sample.story:
            raise SystemExit(1)
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show shared/1.\n#show solved/0."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
