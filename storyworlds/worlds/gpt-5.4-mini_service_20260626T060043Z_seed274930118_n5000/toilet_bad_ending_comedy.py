#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    mounted: bool = False
    broken: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    has_toilet: bool = False
    has_plunger: bool = False
    has_sign: bool = False


@dataclass
class Problem:
    id: str
    verb: str
    mess: str
    splashes: bool
    comedic: str
    urgent: str


@dataclass
class Fix:
    id: str
    label: str
    tool: str
    helps: set[str]
    requires: set[str] = field(default_factory=set)
    success: bool = True


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
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
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


PROBLEMS = {
    "clog": Problem("clog", "try to flush", "clogged", False, "the water made a nervous gurgle", "right away"),
    "overflow": Problem("overflow", "keep flushing", "overflowing", True, "the water grew a silly white beard of bubbles", "fast"),
    "stuck": Problem("stuck", "unstick the handle", "stuck", False, "the handle clicked like a tiny joke drum", "carefully"),
}

FIXES = {
    "plunger": Fix("plunger", "a plunger", "plunger", {"clog", "stuck"}),
    "mop": Fix("mop", "a mop and bucket", "mop", {"overflow"}, requires={"water"}),
    "sign": Fix("sign", "a wet-floor sign", "sign", {"overflow"}),
}

PLACES = {
    "bathroom": Place("bathroom", "the bathroom", "room", has_toilet=True, has_plunger=True, has_sign=True),
    "hallway": Place("hallway", "the hallway", "room", has_toilet=False, has_plunger=False, has_sign=False),
    "school": Place("school", "the school restroom", "room", has_toilet=True, has_plunger=False, has_sign=True),
}

HEROES = [("Milo", "boy"), ("Lena", "girl"), ("Pip", "boy"), ("Nora", "girl")]
PARENTS = {"boy": "father", "girl": "mother"}
TRAITS = ["silly", "curious", "cheerful", "wobbly"]


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    gender: str
    trait: str
    seed: Optional[int] = None


def reason_ok(place: Place, problem: Problem) -> bool:
    return place.has_toilet and (problem.id != "overflow" or place.has_sign)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_toilet:
            lines.append(asp.fact("has_toilet", pid))
        if p.has_plunger:
            lines.append(asp.fact("has_plunger", pid))
        if p.has_sign:
            lines.append(asp.fact("has_sign", pid))
    for pr in PROBLEMS.values():
        lines.append(asp.fact("problem", pr.id))
        if pr.splashes:
            lines.append(asp.fact("splashes", pr.id))
    for fx in FIXES.values():
        lines.append(asp.fact("fix", fx.id))
        for k in sorted(fx.helps):
            lines.append(asp.fact("helps", fx.id, k))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, R) :- place(P), problem(R), has_toilet(P), not bad_combo(P, R).
bad_combo(P, overflow) :- place(P), not has_sign(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for p in PLACES.values():
        for r in PROBLEMS.values():
            if reason_ok(p, r):
                out.append((p.id, r.id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy toilet story world with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    if not reason_ok(PLACES[place], PROBLEMS[problem]):
        raise StoryError("No valid combination matches the given options.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice([n for n, g in HEROES if g == gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, hero=name, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    prob = PROBLEMS[params.problem]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.gender, meters={"urgency": 0}, memes={"embarrass": 0}))
    parent = world.add(Entity(id="parent", kind="character", type=PARENTS[params.gender], label=f"the {PARENTS[params.gender]}"))
    toilet = world.add(Entity(id="toilet", type="toilet", label="the toilet"))
    tool = world.add(Entity(id="tool", type="tool", label="a plunger", caretaker=parent.id))
    world.facts.update(hero=hero, parent=parent, toilet=toilet, tool=tool, place=place, problem=prob, params=params)

    world.say(f"{hero.id} was a {params.trait} {params.gender} who really, really needed {place.label}.")
    world.say(f"In {place.label}, the toilet waited like a very serious chair with a lid.")
    world.para()
    world.say(f"One day, {hero.id} {prob.verb} and heard {prob.comedic}.")
    hero.meters["urgency"] += 1
    if prob.id == "overflow":
        toilet.broken = True
        hero.memes["embarrass"] += 1
    world.say(f"{hero.id} said, \"Uh-oh,\" because the toilet was {prob.mess}.")
    world.para()
    world.say(f"{hero.id}'s {parent.label} came in with {tool.label} and a brave smile.")
    if prob.id == "clog":
        world.say(f"They tried the plunger, but it made a rude little thunk and nothing changed.")
    elif prob.id == "stuck":
        world.say(f"They wiggled the handle, but it only clicked back like it was laughing.")
    else:
        world.say(f"They looked for a mop, but the floor was already pretending to be a lake.")
    world.say(f"That was the bad part: the problem stayed, and {hero.id} had to hop backward in socks.")
    world.para()
    world.say(f"In the end, {hero.id} had to wait outside the door while the toilet kept being dramatic.")
    world.say(f"The bathroom smelled like soap and defeat, and {hero.id} giggled anyway because the toilet had lost the argument.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    prob: Problem = f["problem"]
    place: Place = f["place"]
    return [
        f'Write a short comedic story for a child about "{place.label}" and a troublesome toilet.',
        f"Tell a gentle bad-ending story where {params.hero} needs the toilet, but {prob.comedic}, and the grown-up cannot fix it.",
        f'Write a funny story that includes a toilet, a problem, and an ending where the mess is still there.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    prob: Problem = f["problem"]
    place: Place = f["place"]
    parent: Entity = f["parent"]
    qa = [
        QAItem(question=f"Who was the story about?", answer=f"It was about {p.hero}, a {p.trait} {p.gender} who needed {place.label}."),
        QAItem(question=f"What went wrong with the toilet?", answer=f"The toilet got {prob.mess}, so it caused a funny but annoying problem."),
        QAItem(question=f"Did the grown-up fix it?", answer="No. They tried, but the toilet stayed troublesome, so the ending was a bad one."),
        QAItem(question=f"How did {p.hero} feel at the end?", answer=f"{p.hero} still giggled, even though the bathroom stayed messy and awkward."),
    ]
    if prob.id == "overflow":
        qa.append(QAItem(
            question=f"Why was the problem extra silly in this story?",
            answer=f"It was extra silly because the toilet kept overflowing, so the grown-up had to rush around and the bathroom acted like a tiny, rude river.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a toilet for?", answer="A toilet is a bathroom fixture people use when they need to go to the bathroom."),
        QAItem(question="What does a plunger do?", answer="A plunger helps push clogs out of a toilet or drain so water can move again."),
        QAItem(question="Why is a wet floor slippery?", answer="A wet floor can be slippery because water makes shoes slide more easily."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.broken:
            bits.append("broken=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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


CURATED = [
    StoryParams(place="bathroom", problem="clog", hero="Milo", gender="boy", trait="silly"),
    StoryParams(place="school", problem="stuck", hero="Lena", gender="girl", trait="curious"),
    StoryParams(place="bathroom", problem="overflow", hero="Pip", gender="boy", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem) combos:\n")
        for c in combos:
            print(f"  {c[0]:10} {c[1]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
