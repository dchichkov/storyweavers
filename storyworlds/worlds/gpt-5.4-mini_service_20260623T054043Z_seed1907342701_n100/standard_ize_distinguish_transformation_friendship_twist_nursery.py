#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/standard_ize_distinguish_transformation_friendship_twist_nursery.py
=======================================================================================================================

A standalone story world for a tiny nursery-rhyme-like domain: two friends try
to standard-ize a little shared song, then discover they can distinguish each
voice without turning it into the same tune.

Seed tale:
---
A little rhyme began with two friends who liked to sing together. One wanted to
standard-ize the song so every line sounded neat and even. The other wanted to
distinguish the voices so each friend kept a special part. A small twist turned
the tune into a shared transformation: the song became organized, but still had
two different bright voices.

This world keeps that premise as a tiny simulation with meters and memes:
- physical meters: cards, ribbons, bells, page order, tidy stacks
- emotional memes: delight, worry, pride, closeness, frustration, wonder

It includes:
- a reasonableness gate for valid stories,
- a Python causal model,
- an inline ASP twin,
- three QA sets generated from world state,
- `--verify`, `--asp`, `--show-asp`, `--json`, `--qa`, `--trace`, `-n`, `--all`.
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
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

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
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    result: str
    spread: str
    transforms: str
    risk_region: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    tool: str
    action: str
    effect: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place):
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_standardize(world: World) -> list[str]:
    out: list[str] = []
    for speaker in world.characters():
        if speaker.meters["standardize"] < THRESHOLD:
            continue
        sig = ("standardize", speaker.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("song").meters["order"] += 1
        world.get("song").meters["same"] += 1
        out.append("The little song grew neat and even.")
    return out


def _r_distinguish(world: World) -> list[str]:
    out: list[str] = []
    if world.get("song").meters["order"] < THRESHOLD:
        return out
    if world.get("song").meters["same"] < THRESHOLD:
        return out
    for speaker in world.characters():
        if speaker.meters["distinguish"] < THRESHOLD:
            continue
        sig = ("distinguish", speaker.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("song").meters["voice"] += 1
        world.get("song").meters["balance"] += 1
        speaker.memes["pride"] += 1
        out.append("Each bright voice kept its own small sparkle.")
    return out


def _r_twist(world: World) -> list[str]:
    song = world.get("song")
    if song.meters["voice"] < THRESHOLD or song.meters["order"] < THRESHOLD:
        return []
    if ("twist", song.id) in world.fired:
        return []
    world.fired.add(("twist", song.id))
    song.meters["twist"] += 1
    return ["__twist__"]


CAUSAL_RULES = [Rule("standardize", _r_standardize), Rule("distinguish", _r_distinguish), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__twist__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_story(world: World, child_a: Entity, child_b: Entity) -> None:
    child_a.memes["closeness"] += 1
    child_b.memes["closeness"] += 1
    world.say(
        f"In {world.place.label}, {child_a.id} and {child_b.id} sat by a little page of rhyme. "
        f"The room felt {world.place.mood}, like a cozy pocket of morning."
    )
    world.say(
        f"They had a shared song, a bell, and two ribbons. {child_a.id} liked to hum softly, "
        f"and {child_b.id} liked to tap the beat."
    )


def start_premise(world: World, child_a: Entity, child_b: Entity, problem: Problem) -> None:
    world.say(
        f'{child_a.id} said, "Let us standard-ize the song," and began to line up the page marks '
        f"so every verse looked the same."
    )
    child_a.meters["standardize"] += 1
    child_a.memes["worry"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f'{child_b.id} smiled and said, "We can still distinguish each voice." '
        f"{problem.label.capitalize()} seemed gentle at first, but it could flatten the tune."
    )


def tension(world: World, child_a: Entity, child_b: Entity, problem: Problem) -> None:
    child_b.meters["distinguish"] += 1
    child_b.memes["wonder"] += 1
    world.say(
        f"{child_b.id} tied one ribbon to the bell and another to the page edge, so the parts "
        f"would not get mixed up."
    )
    world.say(
        f"That was the twist: the song was becoming tidier, yet the two friends wanted it to stay "
        f"alive and different."
    )
    propagate(world, narrate=True)


def resolve(world: World, child_a: Entity, child_b: Entity, method: Method, twist: Twist) -> None:
    world.para()
    child_a.meters["standardize"] += 1
    child_b.meters["distinguish"] += 1
    world.say(
        f'Together they used {method.label}. {method.action.capitalize()}, and {method.effect}.'
    )
    world.say(
        f"{twist.reveal.capitalize()} The song did not become the same in every little part. "
        f"It became balanced instead, with a neat frame and two bright voices."
    )
    world.say(
        f'By the end, {child_a.id} and {child_b.id} were laughing side by side, and the tidy page '
        f"rested on the sill like a small, shining promise."
    )


def tell(place: Place, problem: Problem, method: Method, twist: Twist,
         child_a_name: str = "Mina", child_b_name: str = "Pip",
         child_a_gender: str = "girl", child_b_gender: str = "boy") -> World:
    world = World(place)
    a = world.add(Entity(id=child_a_name, kind="character", type=child_a_gender, role="friend"))
    b = world.add(Entity(id=child_b_name, kind="character", type=child_b_gender, role="friend"))
    song = world.add(Entity(id="song", type="thing", label="song"))
    bell = world.add(Entity(id="bell", type="thing", label="bell"))
    ribbon1 = world.add(Entity(id="ribbon1", type="thing", label="red ribbon"))
    ribbon2 = world.add(Entity(id="ribbon2", type="thing", label="blue ribbon"))

    world.facts.update(
        child_a=a, child_b=b, song=song, bell=bell, ribbons=(ribbon1, ribbon2),
        place=place, problem=problem, method=method, twist=twist
    )

    setup_story(world, a, b)
    world.para()
    start_premise(world, a, b, problem)
    tension(world, a, b, problem)
    resolve(world, a, b, method, twist)

    song.meters["resolved"] += 1
    a.memes["closeness"] += 1
    b.memes["closeness"] += 1
    world.facts["ending"] = "balanced"

    return world


PLACES = {
    "nursery": Place(id="nursery", label="the nursery", mood="warm", affords={"rhyme", "song"}),
    "windowseat": Place(id="windowseat", label="the window seat", mood="golden", affords={"rhyme", "song"}),
    "gardenbench": Place(id="gardenbench", label="the garden bench", mood="soft", affords={"rhyme", "song"}),
    "playroom": Place(id="playroom", label="the playroom", mood="bright", affords={"rhyme", "song"}),
}

PROBLEMS = {
    "tune": Problem(
        id="tune",
        label="the tune",
        verb="tidy",
        result="neat and even",
        spread="flatten",
        transforms="become organized",
        risk_region="voice",
        tags={"standardize", "rhyme"},
    ),
    "line": Problem(
        id="line",
        label="the line of verse",
        verb="straighten",
        result="in order",
        spread="smooth",
        transforms="become orderly",
        risk_region="page",
        tags={"standardize", "rhyme"},
    ),
    "beat": Problem(
        id="beat",
        label="the beat",
        verb="steady",
        result="regular",
        spread="squash",
        transforms="settle",
        risk_region="sound",
        tags={"standardize", "distinguish"},
    ),
}

METHODS = {
    "marks": Method(
        id="marks",
        label="little page marks",
        tool="marks",
        action="they drew tiny marks to guide each verse",
        effect="the page grew neat without losing its little hops",
        protects={"voice", "page"},
        tags={"standardize"},
    ),
    "ribbons": Method(
        id="ribbons",
        label="the ribbons",
        tool="ribbons",
        action="they tied one ribbon to each voice",
        effect="the parts stayed tidy and easy to tell apart",
        protects={"voice"},
        tags={"distinguish"},
    ),
    "bell": Method(
        id="bell",
        label="the bell",
        tool="bell",
        action="they tapped the bell only on the chorus",
        effect="the song became organized and still had a bright ring",
        protects={"sound"},
        tags={"standardize", "distinguish"},
    ),
}

TWISTS = {
    "swap": Twist(
        id="swap",
        label="a small twist",
        reveal="Then they swapped roles for the last verse, and the rhyme smiled at the change.",
        ending="the ending line wore a new hat",
        tags={"twist"},
    ),
    "echo": Twist(
        id="echo",
        label="a little echo",
        reveal="Then the last word echoed back, as if the room itself wanted to join the song.",
        ending="the last note came home again",
        tags={"twist"},
    ),
    "treat": Twist(
        id="treat",
        label="a sweet surprise",
        reveal="Then a sweet snack appeared on the sill, and the friends sang one extra verse for joy.",
        ending="the page smelled faintly of honey",
        tags={"twist"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nell", "Poppy", "Ruby", "Lucy", "Mabel", "Tess"]
BOY_NAMES = ["Pip", "Finn", "Tom", "Theo", "Ben", "Jasper", "Noah", "Eli"]


@dataclass
class StoryParams:
    place: str
    problem: str
    method: str
    twist: str
    child_a_name: str
    child_a_gender: str
    child_b_name: str
    child_b_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="nursery", problem="tune", method="bell", twist="swap",
                child_a_name="Mina", child_a_gender="girl", child_b_name="Pip", child_b_gender="boy"),
    StoryParams(place="windowseat", problem="line", method="marks", twist="echo",
                child_a_name="Lily", child_a_gender="girl", child_b_name="Finn", child_b_gender="boy"),
    StoryParams(place="gardenbench", problem="beat", method="ribbons", twist="treat",
                child_a_name="Tess", child_a_gender="girl", child_b_name="Tom", child_b_gender="boy"),
    StoryParams(place="playroom", problem="tune", method="ribbons", twist="swap",
                child_a_name="Ruby", child_a_gender="girl", child_b_name="Eli", child_b_gender="boy"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for method in METHODS:
                for twist in TWISTS:
                    if problem == "tune" and method in {"bell", "ribbons", "marks"}:
                        combos.append((place, problem, method, twist))
                    elif problem == "line" and method in {"marks", "bell"}:
                        combos.append((place, problem, method, twist))
                    elif problem == "beat" and method in {"ribbons", "bell"}:
                        combos.append((place, problem, method, twist))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about standard-ize and distinguish.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
              and (args.problem is None or c[1] == args.problem)
              and (args.method is None or c[2] == args.method)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, method, twist = rng.choice(sorted(combos))
    pa = args.gender_a or rng.choice(["girl", "boy"])
    pb = args.gender_b or ("boy" if pa == "girl" else "girl")
    name_a = args.name_a or rng.choice(GIRL_NAMES if pa == "girl" else BOY_NAMES)
    name_b = args.name_b or rng.choice([n for n in (GIRL_NAMES if pb == "girl" else BOY_NAMES) if n != name_a])
    return StoryParams(place=place, problem=problem, method=method, twist=twist,
                       child_a_name=name_a, child_a_gender=pa, child_b_name=name_b,
                       child_b_gender=pb)


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    problem = PROBLEMS.get(params.problem)
    method = METHODS.get(params.method)
    twist = TWISTS.get(params.twist)
    if not all([place, problem, method, twist]):
        raise StoryError("Invalid params.")
    if params.problem == "tune" and params.method not in {"bell", "ribbons", "marks"}:
        raise StoryError("That method does not fit that problem.")
    if params.problem == "line" and params.method not in {"marks", "bell"}:
        raise StoryError("That method does not fit that problem.")
    if params.problem == "beat" and params.method not in {"ribbons", "bell"}:
        raise StoryError("That method does not fit that problem.")
    world = tell(place, problem, method, twist, params.child_a_name, params.child_a_gender,
                 params.child_b_name, params.child_b_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["place"]
    pr = f["problem"]
    m = f["method"]
    t = f["twist"]
    a, b = f["child_a"], f["child_b"]
    return [
        f'Write a nursery-rhyme style story in {p.label} where {a.id} and {b.id} try to standard-ize {pr.label} with {m.label}.',
        f'Write a gentle friendship story where two children distinguish their voices while keeping the song neat, and include the word "standard-ize".',
        f'Write a short story with a twist: a tidy song, two friends, and a way to distinguish each voice without losing the rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["child_a"], f["child_b"]
    place, problem, method, twist = f["place"], f["problem"], f["method"], f["twist"]
    song = f["song"]
    return [
        QAItem(
            question=f"Who are the story's two friends in {place.label}?",
            answer=f"The story follows {a.id} and {b.id}. They sit together in {place.label} and work on a little rhyme as friends.",
        ),
        QAItem(
            question=f"What did {a.id} want to do to {problem.label}?",
            answer=f"{a.id} wanted to standard-ize {problem.label}. That meant making it neat and even, like a small ordered pattern in a nursery song.",
        ),
        QAItem(
            question=f"How did {b.id} help distinguish the song?",
            answer=f"{b.id} used {method.label} and tied the parts together in a careful way. That helped the voices stay different even while the song became tidier.",
        ),
        QAItem(
            question=f"What was the twist in the ending?",
            answer=f"{twist.reveal} The twist changed the last verse without breaking the friendship or the rhyme.",
        ),
        QAItem(
            question=f"What changed in the song by the end?",
            answer=f"The song became balanced and orderly, and it also kept two bright voices. It was transformed from a loose little tune into a neater one that still had its own charm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem("What does standard-ize mean?", "To standard-ize something is to make it follow one neat pattern or rule so it looks or sounds more orderly."),
        QAItem("What does distinguish mean?", "To distinguish means to tell one thing from another because it has a different look, sound, or mark."),
    ]
    if f["twist"].id == "echo":
        out.append(QAItem("What is an echo?", "An echo is a sound that comes back after you make it, as if the room answers you."))
    if f["method"].id == "bell":
        out.append(QAItem("What does a bell do?", "A bell makes a clear ring that can help people keep time or notice a part of a song."))
    if f["method"].id == "ribbons":
        out.append(QAItem("What are ribbons for?", "Ribbons can help show a pattern or mark one part from another, so things are easier to tell apart."))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for pr in PROBLEMS.values():
        lines.append(asp.fact("problem", pr.id))
        lines.append(asp.fact("risk_region", pr.id, pr.risk_region))
    for m in METHODS.values():
        lines.append(asp.fact("method", m.id))
        for t in sorted(m.protects):
            lines.append(asp.fact("protects", m.id, t))
    for t in TWISTS.values():
        lines.append(asp.fact("twist", t.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, M, T) :- place(P), problem(Pr), method(M), twist(T), fits(Pr, M).
fits(tune, bell).
fits(tune, ribbons).
fits(tune, marks).
fits(line, bell).
fits(line, marks).
fits(beat, bell).
fits(beat, ribbons).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: that combination does not fit the small nursery rhyme world.)"


def verify_samples() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = format_qa(sample)
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(verify_samples())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a_name} & {p.child_b_name}: {p.problem} / {p.method} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
