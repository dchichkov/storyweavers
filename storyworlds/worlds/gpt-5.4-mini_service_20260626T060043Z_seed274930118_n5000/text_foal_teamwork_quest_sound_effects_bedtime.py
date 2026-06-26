#!/usr/bin/env python3
"""
A small bedtime story world about a foal, a gentle quest, teamwork, and soft
sound effects in a quiet stable and moonlit meadow.

Premise:
- A young foal wants to fetch something comforting before sleep.
- The quest is only safe and successful if the foal accepts teamwork.
- Sound effects are narrated as part of the world state, not as a frozen script.

This script is a standalone Storyweavers world file.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

try:
    from typing import Literal
except Exception:  # pragma: no cover
    Literal = str


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"foal", "horse", "colt", "stallion"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    bedtime: bool
    quiet: bool = True


@dataclass
class Quest:
    id: str
    goal: str
    route: list[str]
    challenge: str
    reward: str
    sound: str
    teamwork_needed: bool = True


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place, self.quest)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "stable": Place(id="stable", label="the stable", indoors=True, bedtime=True, quiet=True),
    "meadow": Place(id="meadow", label="the moonlit meadow", indoors=False, bedtime=True, quiet=True),
    "barnyard": Place(id="barnyard", label="the barnyard", indoors=False, bedtime=True, quiet=False),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="bring back the little lantern for bedtime",
        route=["the straw pile", "the tack room", "the sleepy door"],
        challenge="the lantern is tucked where the shadows gather",
        reward="a warm glow beside the straw bed",
        sound="clink-clink",
        teamwork_needed=True,
    ),
    "blanket": Quest(
        id="blanket",
        goal="fetch the soft blanket from the peg",
        route=["the tack hook", "the hay corner", "the foal's bed"],
        challenge="the blanket is just out of reach for small legs",
        reward="a cozy nest for sleep",
        sound="fwap-fwap",
        teamwork_needed=True,
    ),
    "bell": Quest(
        id="bell",
        goal="find the tiny bell that sings at bedtime",
        route=["the gate", "the bench", "the moonbeam path"],
        challenge="the bell rolled away with a little jingling skip",
        reward="a gentle bedtime ring",
        sound="ting-ting",
        teamwork_needed=True,
    ),
}

NAMES = ["Pip", "Luna", "Bram", "Milo", "Daisy", "Star"]
HELPERS = ["mother", "father", "older sibling", "kind pony", "grandparent"]
TRAITS = ["sleepy", "brave", "curious", "gentle", "small", "hopeful"]


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        if not place.bedtime:
            continue
        for qid, quest in QUESTS.items():
            if quest.teamwork_needed:
                out.append((pid, qid))
    return out


ASP_RULES = r"""
valid(P,Q) :- place(P), quest(Q), bedtime(P), teamwork_needed(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        if place.bedtime:
            lines.append(asp.fact("bedtime", pid))
        if place.quiet:
            lines.append(asp.fact("quiet", pid))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if quest.teamwork_needed:
            lines.append(asp.fact("teamwork_needed", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def sound_line(sound: str) -> str:
    return {
        "clink-clink": "clink-clink",
        "fwap-fwap": "fwap-fwap",
        "ting-ting": "ting-ting",
    }.get(sound, "soft little sound")


def introduce(world: World, foal: Entity, helper: Entity) -> None:
    world.say(
        f"{foal.id} was a {next((t for t in foal.tags if t != 'foal'), 'small')} foal who "
        f"loved bedtime stories and quiet quests."
    )
    world.say(
        f"{helper.label.capitalize()} stayed nearby, ready to help when the path got tricky."
    )


def begin_quest(world: World, foal: Entity) -> None:
    q = world.quest
    foal.memes["curiosity"] = foal.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"One night, {foal.id} listened to the house settle down and wanted to "
        f"{q.goal}."
    )
    world.say(
        f"Somewhere ahead, {q.challenge}, and the air waited for {sound_line(q.sound)}."
    )


def attempt(world: World, foal: Entity, helper: Entity) -> None:
    q = world.quest
    foal.memes["desire"] = foal.memes.get("desire", 0.0) + 1.0
    foal.meters["effort"] = foal.meters.get("effort", 0.0) + 1.0
    world.say(
        f"{foal.id} trotted to the first turn of the quest, then paused because "
        f"the thing they needed was still too high, too far, or too carefully tucked away."
    )
    world.say(
        f'"{sound_line(q.sound)}," whispered the quiet night, and {foal.id} looked back at {helper.label}.'
    )


def teamwork(world: World, foal: Entity, helper: Entity) -> None:
    q = world.quest
    foal.memes["worry"] = foal.memes.get("worry", 0.0) + 1.0
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1.0
    world.say(
        f"{helper.label.capitalize()} smiled and offered a steadier step. "
        f"Together they chose the safe way through {world.place.label}."
    )
    world.say(
        f"{helper.label.capitalize()} lifted, {foal.id} reached, and the quest answered with a small {sound_line(q.sound)}."
    )
    foal.memes["hope"] = foal.memes.get("hope", 0.0) + 1.0


def resolve(world: World, foal: Entity, helper: Entity) -> None:
    q = world.quest
    foal.memes["joy"] = foal.memes.get("joy", 0.0) + 1.0
    foal.memes["calm"] = foal.memes.get("calm", 0.0) + 1.0
    world.say(
        f"At last, {foal.id} carried home {q.reward}, and the little hero felt proud without feeling loud."
    )
    world.say(
        f"They tucked the reward beside the bed, and the last sound was just {sound_line(q.sound)}, "
        f"as the moon watched over {foal.id} and {helper.label}."
    )


def tell(place: Place, quest: Quest, name: str, helper_kind: str) -> World:
    world = World(place, quest)
    foal = world.add(Entity(id=name, kind="character", type="foal", tags={"foal", "text"}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_kind))
    world.facts.update(foal=foal, helper=helper, place=place, quest=quest)

    introduce(world, foal, helper)
    world.para()
    begin_quest(world, foal)
    attempt(world, foal, helper)
    world.para()
    teamwork(world, foal, helper)
    resolve(world, foal, helper)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    foal: Entity = f["foal"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        f'Write a bedtime story about a foal named {foal.id} who goes on a quiet quest in {place.label}.',
        f"Tell a soft story where {foal.id} needs teamwork to {quest.goal}, and the night makes gentle sound effects.",
        f"Create a child-friendly bedtime tale with a foal, a helper, and a small quest ending in calm sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    foal: Entity = f["foal"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who goes on the quest in {place.label}?",
            answer=f"{foal.id} the foal goes on the quest with help from the {helper.label}.",
        ),
        QAItem(
            question=f"What does {foal.id} want to do at bedtime?",
            answer=f"{foal.id} wants to {quest.goal}, and the story turns soft and careful when that proves tricky.",
        ),
        QAItem(
            question=f"How do {foal.id} and the {helper.label} succeed?",
            answer="They work together, choose the safe way, and use teamwork to finish the quest.",
        ),
        QAItem(
            question=f"What sound is heard during the quest?",
            answer=f"The story includes {sound_line(quest.sound)} as a gentle bedtime sound effect.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help each other do something they could not do as well alone.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone looks for something or tries to finish an important goal.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you imagine noises, like clinks, jingles, or soft footsteps.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: foal, teamwork, quest, and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combos available.")
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(filtered)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, quest=quest, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], params.name, params.helper)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} valid (place, quest) combos:")
        for place, quest in combos:
            print(f"  {place:10} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for pid, qid in valid_combos():
            params = StoryParams(place=pid, quest=qid, name="Pip", helper="mother")
            samples.append(generate(params))
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
